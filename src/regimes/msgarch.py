"""Markov-switching GJR-GARCH volatility, in the form of Haas, Mittnik and Paolella (2004).

The two-state HMM forecasts volatility as a blend of two fixed levels, and MSM as a blend of a few
more (docs/WRITEUP.md, "Why it loses"). MS-GARCH keeps the regimes but lets volatility move
continuously inside each one: every regime ``k`` runs its own GJR-GARCH(1,1) variance on the whole
return history,

    h_{k,t+1} = omega_k + (alpha_k + gamma_k * 1[r_t < 0]) * r_t^2 + beta_k * h_{k,t},

and the regime ``s_t`` follows a Markov chain with transition matrix ``P``. Given ``s_t = k``,
``r_t = sqrt(h_{k,t}) * z_t`` with ``z_t`` standard normal or unit-variance Student-t. Running every
regime's variance on all past returns (rather than only the days spent in that regime) is what makes
the likelihood exact and cheap: no path dependence, so the forward filter is the HMM one.

Returns are treated as zero-mean, as in ``regimes.msm`` and the R ``MSGARCH`` package. The filter
starts from the ergodic regime distribution with each regime's variance at its long-run level, as
``MSGARCH`` does, but scores the first return too, where ``MSGARCH`` uses it only to start the
variance recursions. Under that convention the likelihood matches ``MSGARCH`` 2.51 to 1e-6
(tests/test_msgarch.py, examples/msgarch_r_check.R).

Constraints, as in ``MSGARCH``: ``omega_k > 0``, ``alpha_k, gamma_k, beta_k >= 0`` and
``alpha_k + gamma_k / 2 + beta_k < 1`` in each regime. Regimes are ordered after each fit so that
regime 0 has the lower unconditional variance ``omega / (1 - alpha - gamma / 2 - beta)``.

The h-day forecast is exact, not simulated. With ``G[m, k, j] = E_t[1{s_{t+j} = m} h_{k,t+j}]``,
``G[:, k, 1] = p_1 * h_{k,t+1}`` and

    G[n, k, j + 1] = sum_m P[m, n] * (omega_k * p_j[m] + a_k * G[m, m, j] + beta_k * G[m, k, j]),

where ``p_j`` is the regime distribution ``j`` days ahead and ``a_k = alpha_k + gamma_k / 2`` (the
innovations are symmetric, so a negative return is as likely as a positive one). The expected squared
return on day ``t + j`` is ``sum_m G[m, m, j]``. With one regime this is the usual GJR-GARCH forecast.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import pandas as pd
from numba import njit
from scipy.optimize import minimize

_NORMAL = np.inf  # nu = inf in the kernels means Gaussian innovations


@dataclass(frozen=True)
class MSGarchParams:
    omega: np.ndarray   # (K,) variance intercepts
    alpha: np.ndarray   # (K,) reaction to yesterday's squared return
    gamma: np.ndarray   # (K,) extra reaction when yesterday's return was negative
    beta: np.ndarray    # (K,) persistence of the regime's own variance
    P: np.ndarray       # (K, K) row-stochastic transition matrix, rows = from-regime
    nu: np.ndarray      # (K,) Student-t degrees of freedom, inf for normal innovations

    @property
    def k(self) -> int:
        return len(self.omega)

    def persistence(self) -> np.ndarray:
        return self.alpha + self.gamma / 2 + self.beta

    def unconditional_variance(self) -> np.ndarray:
        """Long-run variance of each regime's own GARCH recursion."""
        return self.omega / (1.0 - self.persistence())

    def as_dict(self) -> dict:
        out = {}
        for i in range(self.k):
            out.update({f"omega{i}": self.omega[i], f"alpha{i}": self.alpha[i],
                        f"gamma{i}": self.gamma[i], f"beta{i}": self.beta[i],
                        f"p{i}{i}": self.P[i, i], f"nu{i}": self.nu[i]})
        return out


def ergodic(P: np.ndarray) -> np.ndarray:
    """Stationary distribution of the regime chain."""
    vals, vecs = np.linalg.eig(P.T)
    v = np.real(vecs[:, np.argmin(np.abs(vals - 1.0))])
    return v / v.sum()


@njit(cache=True)
def _log_density(x, h, nu):
    if not np.isfinite(nu):
        return -0.5 * (math.log(2.0 * math.pi * h) + x * x / h)
    s = (nu - 2.0) * h
    return (math.lgamma(0.5 * (nu + 1.0)) - math.lgamma(0.5 * nu) - 0.5 * math.log(math.pi * s)
            - 0.5 * (nu + 1.0) * math.log1p(x * x / s))


@njit(cache=True)
def _filter_kernel(r, omega, alpha, gamma, beta, P, nu, pi0, h0, store):
    """Forward filter. Returns filtered regime probabilities after each day, each regime's variance
    for the NEXT day (h_{k,t+1}, known at the end of day t), and the log-likelihood."""
    n, K = len(r), len(omega)
    probs = np.empty((n if store else 1, K))
    h_next = np.empty((n if store else 1, K))
    pi = pi0.copy()
    h = h0.copy()
    pred = np.empty(K)
    logf = np.empty(K)
    ll = 0.0
    for t in range(n):
        for j in range(K):
            acc = 0.0
            for i in range(K):
                acc += pi[i] * P[i, j]
            pred[j] = acc
        mx = -np.inf
        for j in range(K):
            if not (h[j] > 1e-12) or not np.isfinite(h[j]):
                return probs, h_next, -1e300
            logf[j] = _log_density(r[t], h[j], nu[j])
            if logf[j] > mx:
                mx = logf[j]
        c = 0.0
        for j in range(K):
            c += pred[j] * math.exp(logf[j] - mx)
        if not (c > 0.0) or not np.isfinite(mx):
            return probs, h_next, -1e300
        ll += mx + math.log(c)
        for j in range(K):
            pi[j] = pred[j] * math.exp(logf[j] - mx) / c
        neg = 1.0 if r[t] < 0.0 else 0.0
        for j in range(K):
            h[j] = omega[j] + (alpha[j] + gamma[j] * neg) * r[t] * r[t] + beta[j] * h[j]
        if store:
            probs[t] = pi
            h_next[t] = h
    return probs, h_next, ll


def msgarch_filter(returns: np.ndarray, p: MSGarchParams, *,
                   store: bool = True) -> tuple[np.ndarray | None, np.ndarray | None, float]:
    """Filtered regime probabilities, next-day regime variances and the log-likelihood.

    The filter starts from the ergodic regime distribution, with each regime's variance at its
    unconditional level. ``store=False`` keeps only the likelihood (for the optimiser).
    """
    r = np.ascontiguousarray(returns, dtype=float)
    probs, h_next, ll = _filter_kernel(r, p.omega, p.alpha, p.gamma, p.beta, p.P, p.nu,
                                       ergodic(p.P), p.unconditional_variance(), store)
    return (probs if store else None), (h_next if store else None), float(ll)


@njit(cache=True)
def _forecast_kernel(probs, h_next, omega, a, beta, P, horizon):
    """Exact mean variance over the next ``horizon`` days from each row (see the module docstring)."""
    n, K = probs.shape
    out = np.empty(n)
    G = np.empty((K, K))
    G2 = np.empty((K, K))
    p = np.empty(K)
    p2 = np.empty(K)
    for t in range(n):
        for m in range(K):
            acc = 0.0
            for i in range(K):
                acc += probs[t, i] * P[i, m]
            p[m] = acc
        for m in range(K):
            for k in range(K):
                G[m, k] = p[m] * h_next[t, k]
        total = 0.0
        for j in range(horizon):
            for m in range(K):
                total += G[m, m]
            if j == horizon - 1:
                break
            for nn in range(K):
                for k in range(K):
                    acc = 0.0
                    for m in range(K):
                        acc += P[m, nn] * (omega[k] * p[m] + a[k] * G[m, m] + beta[k] * G[m, k])
                    G2[nn, k] = acc
            for nn in range(K):
                acc = 0.0
                for m in range(K):
                    acc += p[m] * P[m, nn]
                p2[nn] = acc
            G[:, :] = G2
            p[:] = p2
        out[t] = total / horizon
    return out


def forecast_variance(probs: np.ndarray, h_next: np.ndarray, p: MSGarchParams,
                      horizon: int) -> np.ndarray:
    """Expected mean squared return over the next ``horizon`` days, one value per filtered row."""
    return _forecast_kernel(np.ascontiguousarray(probs), np.ascontiguousarray(h_next), p.omega,
                            p.alpha + p.gamma / 2, p.beta, p.P, horizon)


# --- fitting -----------------------------------------------------------------------------------

def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _unpack(x: np.ndarray, k: int, dist: str, min_stay: float = 0.001) -> MSGarchParams:
    """Unconstrained vector -> parameters. Per regime: log omega, logit persistence and two logits
    that split the persistence between alpha, gamma / 2 and beta (beta's logit fixed at 0)."""
    x = np.clip(x, -30.0, 30.0)  # keeps the optimiser's trial steps from overflowing
    per = x[:4 * k].reshape(k, 4)
    omega = np.exp(per[:, 0])
    s = 0.9999 * _sigmoid(per[:, 1])
    w = np.exp(np.column_stack([per[:, 2], per[:, 3], np.zeros(k)]))
    w /= w.sum(axis=1, keepdims=True)
    alpha, gamma, beta = s * w[:, 0], 2 * s * w[:, 1], s * w[:, 2]
    rest = x[4 * k:]
    if k == 1:
        P = np.ones((1, 1))
    else:
        stay = min_stay + (0.999 - min_stay) * _sigmoid(rest[:k])   # K = 2: P[i, i]
        P = np.array([[stay[0], 1 - stay[0]], [1 - stay[1], stay[1]]])
        rest = rest[k:]
    nu = 2.05 + np.exp(rest[:k]) if dist == "t" else np.full(k, _NORMAL)
    return MSGarchParams(omega, alpha, gamma, beta, P, nu)


def _pack(p: MSGarchParams, dist: str, min_stay: float = 0.001) -> np.ndarray:
    k = p.k
    s = p.persistence()
    rows = []
    for i in range(k):
        w = np.array([p.alpha[i], p.gamma[i] / 2, p.beta[i]]) / s[i]
        w = np.clip(w, 1e-6, None)
        rows.append([np.log(p.omega[i]), np.log((s[i] / 0.9999) / (1 - s[i] / 0.9999)),
                     np.log(w[0] / w[2]), np.log(w[1] / w[2])])
    x = list(np.ravel(rows))
    if k == 2:
        stay = np.clip((np.diag(p.P) - min_stay) / (0.999 - min_stay), 1e-4, 1 - 1e-4)
        x += list(np.log(stay / (1 - stay)))
    if dist == "t":
        x += list(np.log(p.nu - 2.05))
    return np.array(x)


def _ordered(p: MSGarchParams) -> MSGarchParams:
    """Relabel so regime 0 has the lower unconditional variance."""
    order = np.argsort(p.unconditional_variance())
    return MSGarchParams(p.omega[order], p.alpha[order], p.gamma[order], p.beta[order],
                         p.P[np.ix_(order, order)], p.nu[order])


def start_grid(var: float, k: int = 2, dist: str = "t") -> list[MSGarchParams]:
    """Twelve starting points: a calm and a turbulent regime at a few levels of persistence and
    stickiness.

    ``var`` is the sample variance of the training returns."""
    nu = np.full(k, 8.0 if dist == "t" else _NORMAL)
    if k == 1:
        return [MSGarchParams(np.array([var * 0.02]), np.array([0.03]), np.array([0.1]),
                              np.array([0.9]), np.ones((1, 1)), nu)]
    out = []
    # (calm, turbulent) stay probabilities: two sticky regimes, two looser ones, and a turbulent
    # regime that lasts a day or two (a burst), which is where R's MSGARCH lands on S&P 500 returns.
    for scale in (0.4, 0.2):          # calm regime's long-run variance as a share of the sample's
        for stay0, stay1 in ((0.99, 0.99), (0.95, 0.95), (0.98, 0.3)):
            for beta_hi in (0.85, 0.6):
                lo, hi = var * scale, var * 2.5
                alpha = np.array([0.02, 0.05])
                gamma = np.array([0.08, 0.1])
                beta = np.array([0.88, beta_hi])
                s = alpha + gamma / 2 + beta
                omega = np.array([lo, hi]) * (1 - s)
                P = np.array([[stay0, 1 - stay0], [1 - stay1, stay1]])
                out.append(MSGarchParams(omega, alpha, gamma, beta, P, nu))
    return out


def fit_msgarch(returns: pd.Series | np.ndarray, k: int = 2, dist: str = "t", *,
                starts: list[MSGarchParams] | None = None,
                min_stay: float = 0.001) -> tuple[MSGarchParams, float]:
    """Maximum-likelihood fit (L-BFGS-B on transformed parameters), best of every start.

    ``min_stay`` is the lowest allowed probability of staying in a regime. At the default the fit
    may settle on a regime that lasts a single day, which makes the model a fat-tailed mixture
    rather than two persistent regimes (it does on S&P 500 returns 2000-2009 with Student-t errors).
    Returns the parameters, regimes ordered calm first, and the log-likelihood."""
    if dist not in ("normal", "t"):
        raise ValueError("dist must be 'normal' or 't'")
    if k not in (1, 2):
        raise ValueError("only one or two regimes are implemented")
    r = np.ascontiguousarray(returns, dtype=float)

    def nll(x):
        try:
            ll = msgarch_filter(r, _unpack(x, k, dist, min_stay), store=False)[2]
        except (ZeroDivisionError, FloatingPointError, np.linalg.LinAlgError):
            return 1e12
        return -ll if np.isfinite(ll) and ll > -1e299 else 1e12

    best = None
    for s0 in starts or start_grid(float(r.var()), k, dist):
        res = minimize(nll, _pack(s0, dist, min_stay), method="L-BFGS-B")
        if best is None or res.fun < best.fun:
            best = res
    return _ordered(_unpack(best.x, k, dist, min_stay)), float(-best.fun)


# --- walk-forward ------------------------------------------------------------------------------

@dataclass
class MSGarchWalkForward:
    implied_vol: pd.Series      # out-of-sample forecast of next-``horizon``-day vol
    high_vol_prob: pd.Series    # filtered probability of the turbulent regime, same dates
    params: pd.DataFrame        # fitted parameters per refit, indexed by refit date
    n_refits: int


def walk_forward_msgarch(returns: pd.Series, k: int = 2, dist: str = "t", *, min_train: int = 756,
                         step: int = 63, horizon: int = 21,
                         min_stay: float = 0.001) -> MSGarchWalkForward:
    """Expanding-window walk-forward, the same protocol as ``msm.walk_forward_msm``.

    At each refit edge ``i``: fit on ``returns[:i]``, freeze the parameters, filter forward through
    ``returns[:i + step]`` and keep the forecasts for rows ``[i : i + step]``. Each forecast uses
    returns up to its own date only. The first fit and every fourth one after it search the full
    start grid; the others start from the previous fit and from the first grid point.
    """
    r = returns.astype(float)
    vols, probs_out, rows, idx = [], [], [], []
    prev = None
    for n_fit, i in enumerate(range(min_train, len(r), step)):
        end = min(i + step, len(r))
        grid = start_grid(float(r.iloc[:i].var()), k, dist)
        p, ll = fit_msgarch(r.iloc[:i], k, dist, starts=grid if n_fit % 4 == 0 else [prev, grid[0]],
                            min_stay=min_stay)
        prev = p
        probs, h_next, _ = msgarch_filter(r.iloc[:end].to_numpy(), p)
        var = forecast_variance(probs[i:end], h_next[i:end], p, horizon)
        vols.append(pd.Series(np.sqrt(var), index=r.index[i:end]))
        probs_out.append(pd.Series(probs[i:end, -1], index=r.index[i:end]))
        rows.append({**p.as_dict(), "loglik": ll})
        idx.append(r.index[i])
    return MSGarchWalkForward(implied_vol=pd.concat(vols), high_vol_prob=pd.concat(probs_out),
                              params=pd.DataFrame(rows, index=pd.DatetimeIndex(idx)),
                              n_refits=len(vols))


def simulate_msgarch(p: MSGarchParams, n: int, seed: int = 0) -> tuple[np.ndarray, np.ndarray]:
    """Simulated returns and regime path (used by the tests)."""
    rng = np.random.default_rng(seed)
    s = rng.choice(p.k, p=ergodic(p.P))
    h = p.unconditional_variance().copy()
    r, states = np.empty(n), np.empty(n, dtype=int)
    for t in range(n):
        nu = p.nu[s]
        z = rng.standard_normal() if not np.isfinite(nu) else \
            rng.standard_t(nu) * np.sqrt((nu - 2) / nu)
        r[t] = np.sqrt(h[s]) * z
        states[t] = s
        h = p.omega + (p.alpha + p.gamma * (r[t] < 0)) * r[t] ** 2 + p.beta * h
        s = rng.choice(p.k, p=p.P[s])
    return r, states
