"""Markov-switching model with Student-t emissions, fit by EM.

statsmodels' switching models are Gaussian-only, so this is implemented from scratch. It is the
fat-tailed robustness check: equity returns have heavier tails than a normal, and a Gaussian model can
manufacture a spurious "high-variance" state simply to accommodate a handful of outliers that a
Student-t would absorb within a single regime. If the regimes survive Student-t emissions, that
failure mode is not driving them.

Method. A K-state hidden Markov model where, in state k, returns are Student-t with location mu_k,
scale sigma_k and a fixed degrees-of-freedom nu (the tail-heaviness hyperparameter). Fitting is
Baum-Welch (EM):

- E-step: a scaled forward-backward pass gives the filtered P(state | data up to t) and the smoothed
  P(state | all data), the transition posteriors, and per-observation tail weights.
- M-step: the Student-t is written as a scale mixture of normals, t(x) = int N(x; mu, sigma^2 / u)
  Gamma(u; nu/2, nu/2) du, whose posterior weight E[u | x] = (nu + 1) / (nu + delta), delta =
  ((x - mu) / sigma)^2, down-weights outliers and yields closed-form, robust mu and sigma updates.

Regimes are ordered canonically by scale (ascending), matching the rest of the project so "high-vol"
means the same thing everywhere. The result is a RegimeFit, so it plugs straight into
`evaluate.regime_agreement` and the plotting helpers.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .model import RegimeFit

_VAR_FLOOR = 1e-8  # keep a scale from collapsing onto a single point


def _update_nu(smoothed: np.ndarray, delta: np.ndarray, nu_old: float,
               nu_min: float, nu_max: float) -> float:
    """EM update for the (shared) degrees of freedom.

    There is no closed form. Given the current responsibilities and squared standardised residuals,
    the ML update for nu solves ``log(nu/2) - digamma(nu/2) + 1 + S = 0``, where S is the
    responsibility-weighted mean of ``E[log u] - E[u]`` under the scale-mixture posterior (Liu &
    Rubin 1995; McLachlan & Peel 2000). ``log(nu/2) - digamma(nu/2)`` is positive and decreases to 0
    as nu grows, so a finite root exists only when ``S < -1``; otherwise the data are effectively
    Gaussian and nu is pinned to ``nu_max``.
    """
    from scipy.optimize import brentq
    from scipy.special import digamma

    u = (nu_old + 1.0) / (nu_old + delta)
    elog_u = digamma((nu_old + 1.0) / 2.0) - np.log((nu_old + delta) / 2.0)
    s = float((smoothed * (elog_u - u)).sum() / smoothed.sum())  # responsibilities sum to T

    def f(nu):
        return np.log(nu / 2.0) - digamma(nu / 2.0) + 1.0 + s

    if f(nu_min) * f(nu_max) > 0:  # no sign change -> no interior root
        return nu_max if f(nu_max) > 0 else nu_min
    return float(brentq(f, nu_min, nu_max))


def _t_logpdf(x: np.ndarray, mu: np.ndarray, sigma: np.ndarray, nu: float) -> np.ndarray:
    """Log Student-t density, shape (T, K) for x:(T,), mu/sigma:(K,)."""
    from scipy.special import gammaln

    z2 = ((x[:, None] - mu[None, :]) / sigma[None, :]) ** 2
    const = gammaln((nu + 1) / 2) - gammaln(nu / 2) - 0.5 * np.log(nu * np.pi)
    return const - np.log(sigma)[None, :] - (nu + 1) / 2 * np.log1p(z2 / nu)


def _forward_backward(logB: np.ndarray, A: np.ndarray, pi: np.ndarray):
    """Scaled forward-backward. Returns (filtered, smoothed, xi_sum, loglik).

    filtered[t] = P(state | x_1..x_t); smoothed[t] = P(state | x_1..x_T); xi_sum = summed transition
    posteriors (K, K) for the M-step.
    """
    T, K = logB.shape
    # Work in normal space per row using a max-shift for stability, then normalise each t.
    B = np.exp(logB - logB.max(axis=1, keepdims=True))

    alpha = np.zeros((T, K))
    scale = np.zeros(T)
    alpha[0] = pi * B[0]
    scale[0] = alpha[0].sum()
    alpha[0] /= scale[0]
    for t in range(1, T):
        alpha[t] = (alpha[t - 1] @ A) * B[t]
        scale[t] = alpha[t].sum()
        alpha[t] /= scale[t]

    beta = np.zeros((T, K))
    beta[-1] = 1.0
    for t in range(T - 2, -1, -1):
        beta[t] = (A @ (B[t + 1] * beta[t + 1])) / scale[t + 1]

    smoothed = alpha * beta
    smoothed /= smoothed.sum(axis=1, keepdims=True)

    xi_sum = np.zeros((K, K))
    for t in range(T - 1):
        xi = (alpha[t][:, None] * A) * (B[t + 1] * beta[t + 1])[None, :]
        xi_sum += xi / xi.sum()

    # The row max-shift cancels in the normalised alpha/beta but not in the likelihood; add it back.
    loglik = float(np.log(scale).sum() + logB.max(axis=1).sum())
    return alpha, smoothed, xi_sum, loglik


def fit_regimes_student_t(
    returns: pd.Series,
    n_regimes: int = 2,
    *,
    nu: float = 5.0,
    estimate_nu: bool = False,
    nu_bounds: tuple[float, float] = (2.1, 200.0),
    max_iter: int = 200,
    tol: float = 1e-6,
) -> RegimeFit:
    """Fit a K-state Markov-switching model with Student-t emissions by EM.

    Parameters
    ----------
    nu : float
        Degrees of freedom. If ``estimate_nu`` is False this is fixed; otherwise it is the starting
        value. Smaller = heavier tails; nu -> infinity recovers the Gaussian.
    estimate_nu : bool
        If True, estimate a single shared degrees-of-freedom by EM alongside the other parameters
        (see ``_update_nu``). Off by default: the nu likelihood is famously flat, so a fixed value is
        the safer robustness default, and the fitted nu is offered for those who want it. The lower
        bound ``nu_bounds[0]`` should stay above 2 so the variance exists.
    """
    x = returns.astype(float).to_numpy()
    T = x.size
    K = n_regimes

    # Deterministic init: scales spread across the empirical spread, means at the sample mean, a
    # sticky transition matrix. Spreading the scales seeds the calm/stressed separation.
    s = float(np.std(x)) or 1.0
    mu = np.full(K, float(np.mean(x)))
    sigma = s * np.linspace(0.5, 2.0, K)
    A = np.full((K, K), 0.05 / max(K - 1, 1))
    np.fill_diagonal(A, 0.95)
    pi = np.full(K, 1.0 / K)

    prev_ll = -np.inf
    filtered = smoothed = None
    for _ in range(max_iter):
        logB = _t_logpdf(x, mu, sigma, nu)
        filtered, smoothed, xi_sum, ll = _forward_backward(logB, A, pi)

        # M-step. Tail weights down-weight outliers (the scale-mixture E[u | x, k]).
        delta = ((x[:, None] - mu[None, :]) / sigma[None, :]) ** 2
        u = (nu + 1.0) / (nu + delta)            # (T, K)
        w = smoothed * u                          # responsibility x tail weight
        gsum = smoothed.sum(axis=0)               # (K,)

        mu = (w * x[:, None]).sum(axis=0) / w.sum(axis=0)
        var = (smoothed * u * (x[:, None] - mu[None, :]) ** 2).sum(axis=0) / gsum
        sigma = np.sqrt(np.maximum(var, _VAR_FLOOR))
        pi = smoothed[0] / smoothed[0].sum()
        A = xi_sum / xi_sum.sum(axis=1, keepdims=True)

        if estimate_nu:
            # Update nu against the just-updated mu/sigma (multicycle ECM), shared across states.
            new_delta = ((x[:, None] - mu[None, :]) / sigma[None, :]) ** 2
            nu = _update_nu(smoothed, new_delta, nu, nu_bounds[0], nu_bounds[1])

        if ll - prev_ll < tol:
            break
        prev_ll = ll

    order = np.argsort(sigma)  # ascending scale -> canonical order (regime 0 calmest)
    cols = [f"regime_{k}" for k in range(K)]
    result = {"mu": mu[order], "sigma": sigma[order], "nu": nu, "A": A[np.ix_(order, order)],
              "loglik": prev_ll}
    return RegimeFit(
        filtered=pd.DataFrame(filtered[:, order], index=returns.index, columns=cols),
        smoothed=pd.DataFrame(smoothed[:, order], index=returns.index, columns=cols),
        variances=(sigma[order] ** 2),
        order=order,
        result=result,
    )
