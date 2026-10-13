"""Markov-switching multifractal (MSM) volatility, Calvet and Fisher (2004).

The two-state HMM forecasts volatility badly because its forecast is a blend of two fixed levels
(docs/WRITEUP.md, "Why it loses"). MSM keeps the regime-switching machinery but builds volatility
from ``k`` independent two-level components, each switching at its own speed:

    sigma_t = sigma * sqrt(M_1t * M_2t * ... * M_kt),   M_jt in {m0, 2 - m0}, equally likely

Component ``j`` is redrawn each day with probability
``gamma_j = 1 - (1 - gamma_k) ** (b ** (j - k))``, so the first components change rarely (persistent,
low-frequency volatility) and the last change often. With ``k`` components there are ``2 ** k`` states,
which lets volatility take almost any level and gives the long memory that HAR captures, from only
four parameters: ``m0``, ``sigma``, ``b`` and ``gamma_k``.

Everything here is exact: the likelihood comes from the forward filter over all ``2 ** k`` states,
and the h-day forecast pushes the filtered probabilities through the transition matrix, as
``evaluate.walk_forward_oos`` does for the two-state model.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from numba import njit
from scipy.optimize import minimize

from .evaluate import horizon_weights


@dataclass(frozen=True)
class MSMParams:
    m0: float       # value of a component in its high state, in (1, 2); the low state is 2 - m0
    sigma: float    # unconditional daily volatility, in the units of the returns
    b: float        # growth rate of switching frequencies across components, > 1
    gamma_k: float  # switching probability of the fastest component, in (0, 1)


def gammas(p: MSMParams, k: int) -> np.ndarray:
    """Daily switching probability of each component, slowest first."""
    j = np.arange(1, k + 1)
    return 1.0 - (1.0 - p.gamma_k) ** (p.b ** (j - k))


def _bits(k: int) -> np.ndarray:
    """(2**k, k) matrix: column j is 1 where component j is in its high state."""
    return (np.arange(2 ** k)[:, None] >> np.arange(k)[None, ::-1]) & 1


def state_variances(p: MSMParams, k: int) -> np.ndarray:
    """Daily variance in each of the ``2**k`` states."""
    m = np.where(_bits(k) == 1, p.m0, 2.0 - p.m0)
    return p.sigma ** 2 * m.prod(axis=1)


def transition_matrix(p: MSMParams, k: int) -> np.ndarray:
    """Row-stochastic ``2**k`` transition matrix (rows = from-state).

    A component that switches is redrawn from {m0, 2 - m0} with equal odds, so it keeps its value
    with probability ``1 - gamma / 2``. Components move independently, so the full matrix is the
    Kronecker product of the per-component 2x2 matrices, slowest component as the leading bit.
    """
    A = np.ones((1, 1))
    for g in gammas(p, k):
        A = np.kron(A, np.array([[1 - g / 2, g / 2], [g / 2, 1 - g / 2]]))
    return A


@njit(cache=True)
def _filter_kernel(r, var, g, k, store):
    """Forward filter, compiled. The prediction step uses the Kronecker structure: component ``j``
    keeps its value with probability ``1 - g[j] / 2``, so each step costs ``k * 2**k`` operations
    instead of a dense ``4**k`` matrix product."""
    n, S = len(r), len(var)
    norm = 1.0 / np.sqrt(2.0 * np.pi * var)
    half_prec = 0.5 / var
    probs = np.empty((n if store else 1, S))
    pi = np.full(S, 1.0 / S)
    x = np.empty(S)
    y = np.empty(S)
    f = np.empty(S)
    ll = 0.0
    for t in range(n):
        x[:] = pi
        for j in range(k):
            bit = 1 << (k - 1 - j)
            stay, move = 1.0 - g[j] / 2.0, g[j] / 2.0
            for s in range(S):
                y[s] = stay * x[s] + move * x[s ^ bit]
            x[:] = y
        c = 0.0
        for s in range(S):
            f[s] = x[s] * norm[s] * np.exp(-half_prec[s] * r[t] * r[t])
            c += f[s]
        if not (c > 0.0) or not np.isfinite(c):   # impossible under every state: keep the prior
            f[:] = x
            c = 1e-300
        ll += np.log(c)
        pi = f / f.sum()
        if store:
            probs[t] = pi
    return probs, ll


def msm_filter(returns: np.ndarray, p: MSMParams, k: int, *,
               store: bool = True) -> tuple[np.ndarray | None, float]:
    """Filtered state probabilities after each day's return, and the log-likelihood.

    Returns are treated as zero-mean Gaussian given the state. The filter starts from the ergodic
    distribution, which is uniform because every component is equally likely to be high or low.
    ``store=False`` skips keeping the probabilities (for the likelihood inside the optimiser).
    """
    r = np.ascontiguousarray(returns, dtype=float)
    probs, ll = _filter_kernel(r, state_variances(p, k), gammas(p, k), k, store)
    return (probs if store else None), float(ll)


def _unpack(x: np.ndarray) -> MSMParams:
    s = 1.0 / (1.0 + np.exp(-x))
    return MSMParams(m0=1.0 + 0.999 * s[0], sigma=float(np.exp(x[1])), b=1.0 + float(np.exp(x[2])),
                     gamma_k=0.001 + 0.998 * s[3])


def _pack(p: MSMParams) -> np.ndarray:
    def logit(v):
        return np.log(v / (1 - v))
    return np.array([logit((p.m0 - 1.0) / 0.999), np.log(p.sigma), np.log(p.b - 1.0),
                     logit((p.gamma_k - 0.001) / 0.998)])


def start_grid(sd: float) -> list[MSMParams]:
    """Twelve starting points. The likelihood has several local maxima, and on S&P 500 data a single
    start left ``gamma_k`` stuck at its starting value and the fit 28 log-likelihood points short."""
    return [MSMParams(m0=m, sigma=sd, b=b, gamma_k=g)
            for m in (1.3, 1.5, 1.7) for b in (2.0, 6.0) for g in (0.05, 0.5)]


def fit_msm(returns: pd.Series | np.ndarray, k: int, *,
            starts: list[MSMParams] | None = None) -> tuple[MSMParams, float]:
    """Maximum-likelihood fit (L-BFGS-B on transformed parameters). Returns params and log-lik.

    Every start in ``starts`` (default: ``start_grid``) is optimised and the best fit is kept.
    """
    r = np.asarray(returns, dtype=float)
    best = None
    for s0 in starts or start_grid(float(r.std())):
        res = minimize(lambda x: -msm_filter(r, _unpack(x), k, store=False)[1], _pack(s0),
                       method="L-BFGS-B")
        if best is None or res.fun < best.fun:
            best = res
    return _unpack(best.x), float(-best.fun)


def implied_vol(probs: np.ndarray, p: MSMParams, k: int, horizon: int) -> np.ndarray:
    """Forecast of volatility over the next ``horizon`` days from each row of filtered probabilities:
    sqrt of the expected average variance."""
    w = probs @ horizon_weights(transition_matrix(p, k), horizon)
    return np.sqrt(w @ state_variances(p, k))


@dataclass
class MSMWalkForward:
    implied_vol: pd.Series   # out-of-sample forecast of next-``horizon``-day vol
    params: pd.DataFrame     # fitted parameters per refit, indexed by refit date
    n_refits: int


def walk_forward_msm(returns: pd.Series, k: int, *, min_train: int = 756, step: int = 63,
                     horizon: int = 21) -> MSMWalkForward:
    """Expanding-window walk-forward, the same protocol as ``evaluate.walk_forward_oos``.

    At each refit edge ``i``: fit on ``returns[:i]``, freeze the parameters, filter forward through
    ``returns[:i + step]`` and keep the forecasts for rows ``[i : i + step]``. Each forecast uses
    returns up to its own date only. The first fit and every fourth one after it search the full
    start grid; the others start from the previous fit and from one fixed grid point.
    """
    r = returns.astype(float)
    pieces, rows, idx = [], [], []
    prev = None
    for n_fit, i in enumerate(range(min_train, len(r), step)):
        end = min(i + step, len(r))
        grid = start_grid(float(r.iloc[:i].std()))
        p, _ = fit_msm(r.iloc[:i], k, starts=grid if n_fit % 4 == 0 else [prev, grid[1]])
        prev = p
        probs, _ = msm_filter(r.iloc[:end].to_numpy(), p, k)
        pieces.append(pd.Series(implied_vol(probs[i:end], p, k, horizon), index=r.index[i:end]))
        rows.append(vars(p))
        idx.append(r.index[i])
    return MSMWalkForward(implied_vol=pd.concat(pieces),
                          params=pd.DataFrame(rows, index=pd.DatetimeIndex(idx)),
                          n_refits=len(pieces))


def simulate_msm(p: MSMParams, k: int, n: int, seed: int = 0) -> np.ndarray:
    """Simulated returns from an MSM process (used by the tests)."""
    rng = np.random.default_rng(seed)
    g = gammas(p, k)
    m = rng.choice([p.m0, 2.0 - p.m0], size=k)
    out = np.empty(n)
    for t in range(n):
        switch = rng.random(k) < g
        m = np.where(switch, rng.choice([p.m0, 2.0 - p.m0], size=k), m)
        out[t] = p.sigma * np.sqrt(m.prod()) * rng.standard_normal()
    return out
