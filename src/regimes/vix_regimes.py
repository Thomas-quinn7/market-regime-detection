"""Volatility regimes that also observe the VIX.

The return-only regime model loses to trailing volatility because everything it knows comes from past
returns, which trailing vol already summarises. The VIX is different information: it is the price of
30-day S&P 500 options, so it is the market's own forward-looking vol forecast. This variant gives the
hidden state two observations per day, the return and the log VIX level, so the state is inferred
from both.

The design, fixed before looking at results:

- Observation ``z_t = [r_t, log VIX_t]``, returns in daily percent.
- Model: a 2-state HMM with a full-covariance Gaussian per state, fit by EM (the estimator from
  ``regimes.correlation``). States are ordered by their return variance, so the last state is the
  high-vol one. Log VIX is persistent, which a within-state i.i.d. emission ignores; the model treats
  the VIX level as a noisy reading of the state, not as a process in its own right.
- Walk-forward exactly as for the other models: fit on data up to each refit edge (keeping the better
  of a fresh start and a warm start from the previous fit), freeze, filter forward over the next block,
  keep only that block.
- Forecast: the implied daily vol over the next ``horizon`` days, from the filtered state probabilities
  propagated through the transition matrix and weighted against the state return variances.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .correlation import CorrHMMParams, convergence_row, filter_probs, fit_corr_hmm
from .evaluate import horizon_weights


def vix_observations(returns: pd.Series, vix: pd.Series) -> pd.DataFrame:
    """Aligned ``[return, log VIX]`` observations on the dates both exist."""
    return pd.concat({"ret": returns.astype(float), "log_vix": np.log(vix.astype(float))},
                     axis=1, sort=True).dropna()


def _order_by_return_var(p: CorrHMMParams) -> CorrHMMParams:
    o = np.argsort(p.cov[:, 0, 0])
    return CorrHMMParams(p.pi[o], p.A[np.ix_(o, o)], p.mu[o], p.cov[o])


def _vix_split_init(z: np.ndarray, K: int) -> CorrHMMParams:
    """Deterministic start: split the days into K groups by VIX quantile, sticky transitions."""
    d = z.shape[1]
    edges = np.quantile(z[:, 1], np.linspace(0, 1, K + 1))
    groups = np.clip(np.searchsorted(edges, z[:, 1], side="right") - 1, 0, K - 1)
    mu = np.array([z[groups == k].mean(axis=0) for k in range(K)])
    cov = np.array([np.cov(z[groups == k].T) + 1e-6 * np.eye(d) for k in range(K)])
    A = np.full((K, K), 0.01 / max(K - 1, 1))
    np.fill_diagonal(A, 0.99)
    return CorrHMMParams(np.full(K, 1.0 / K), A, mu, cov)


def fit_vix_hmm(z: np.ndarray, n_regimes: int = 2, *, init: CorrHMMParams | None = None,
                max_iter: int = 200, tol: float = 1e-4, info: dict | None = None) -> tuple[CorrHMMParams, float]:
    """Fit the joint return/VIX HMM. Returns (params ordered by return variance, loglik).
    ``info`` is filled as in ``fit_corr_hmm``."""
    z = np.asarray(z, dtype=float)
    start = init if init is not None else _vix_split_init(z, n_regimes)
    params, ll = fit_corr_hmm(z, n_regimes, init=start, max_iter=max_iter, tol=tol, info=info)
    return _order_by_return_var(params), ll


@dataclass
class VixWalkForwardResult:
    high_vol_prob: pd.Series    # filtered P(high-vol state), out of sample
    implied_vol: pd.Series      # model-implied daily vol (percent) over the next ``horizon`` days
    state_vol: pd.DataFrame     # per-refit state return vols (diagnostic), indexed by refit date
    n_refits: int
    n_skipped: int
    convergence: pd.DataFrame | None = None  # per refit: starts, converged, best_converged, iterations


def walk_forward_vix_hmm(returns: pd.Series, vix: pd.Series, *, n_regimes: int = 2,
                         min_train: int = 756, step: int = 63, horizon: int = 21,
                         warm_start: bool = True) -> VixWalkForwardResult:
    """Expanding-window walk-forward for the joint return/VIX HMM, frozen params filtered forward."""
    obs = vix_observations(returns, vix)
    z = obs.to_numpy()
    n = len(z)
    if min_train >= n:
        raise ValueError(f"min_train={min_train} leaves no out-of-sample data (n={n})")

    probs, implied, vol_rows, vol_idx = [], [], [], []
    conv_rows, conv_idx = [], []
    params = None
    n_refits = n_skipped = 0
    for i in range(min_train, n, step):
        end = min(i + step, n)
        try:
            infos = [{}]
            fits = [fit_vix_hmm(z[:i], n_regimes, info=infos[0])]
            if params is not None and warm_start:
                infos.append({})
                fits.append(fit_vix_hmm(z[:i], n_regimes, init=params, info=infos[-1]))
            best = max(range(len(fits)), key=lambda j: fits[j][1])
            params = fits[best][0]
            conv_rows.append(convergence_row(infos, best))
            conv_idx.append(obs.index[i])
        except (np.linalg.LinAlgError, FloatingPointError, ValueError) as exc:
            warnings.warn(f"VIX HMM fit failed at i={i}: {exc}", RuntimeWarning, stacklevel=2)
            n_skipped += 1
            continue
        n_refits += 1
        filt = filter_probs(z[:end], params)[i:end]
        idx = obs.index[i:end]
        state_var = params.cov[:, 0, 0]
        probs.append(pd.Series(filt[:, -1], index=idx))
        implied.append(pd.Series(np.sqrt(filt @ horizon_weights(params.A, horizon) @ state_var),
                                 index=idx))
        vol_rows.append(np.sqrt(state_var))
        vol_idx.append(obs.index[i])

    if not probs:
        raise RuntimeError("no out-of-sample blocks were produced (all fits skipped?)")
    cols = [f"state_{k}" for k in range(n_regimes)]
    return VixWalkForwardResult(
        high_vol_prob=pd.concat(probs).rename("vix_hmm_high_vol_prob"),
        implied_vol=pd.concat(implied).rename("vix_hmm_implied_vol"),
        state_vol=pd.DataFrame(vol_rows, index=pd.DatetimeIndex(vol_idx), columns=cols),
        n_refits=n_refits,
        n_skipped=n_skipped,
        convergence=pd.DataFrame(conv_rows, index=pd.DatetimeIndex(conv_idx)),
    )
