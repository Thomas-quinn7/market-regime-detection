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
    max_iter: int = 200,
    tol: float = 1e-6,
) -> RegimeFit:
    """Fit a K-state Markov-switching model with Student-t emissions by EM.

    Parameters
    ----------
    nu : float
        Degrees of freedom (fixed). Smaller = heavier tails; nu -> infinity recovers the Gaussian.
        Held fixed rather than estimated because the degrees-of-freedom likelihood is famously flat
        and unstable; the robustness question is whether the regimes hold under fat tails, not what
        the exact tail index is.
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
