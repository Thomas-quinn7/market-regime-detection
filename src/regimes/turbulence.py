"""Financial Turbulence: a multivariate regime input (Kritzman & Li 2010).

Real systematic funds do not define regimes from a single asset's returns; they use a multivariate
stress measure. Financial Turbulence is the canonical one:

    FT_t = (r_t - mu)' Sigma^-1 (r_t - mu)

the Mahalanobis distance of the day's cross-asset return vector from its historical mean, scaled by
the historical covariance. It fires on two things a single-asset model cannot see: uncharacteristically
large moves AND breaks in the cross-asset correlation structure. Feeding this series into the existing
2-state HMM ("normal" vs "ex-normal") is exactly the First Sentier / Kritzman construction.

Look-ahead discipline (the point of this repo): by default mu and Sigma are estimated CAUSALLY from a
trailing window ending the day before t, so FT_t uses no future information. A full-sample option is
offered for the descriptive Kritzman version, clearly labelled.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .model import RegimeFit, fit_regimes


def financial_turbulence(
    returns: pd.DataFrame,
    *,
    causal: bool = True,
    window: int = 504,
    min_periods: int = 252,
    ridge: float = 1e-6,
) -> pd.Series:
    """Financial Turbulence (Mahalanobis distance) of a cross-asset return panel.

    Parameters
    ----------
    returns : DataFrame
        One column of returns per asset (e.g. ``data.load_sector_returns``).
    causal : bool
        If True (default, look-ahead-free), mu and Sigma for day t are estimated from a trailing
        ``window`` of days strictly before t. If False, they are the full-sample estimates (the
        descriptive Kritzman version; uses future data, so for illustration only).
    window : int
        Trailing window length for the causal estimate (~2 years by default).
    min_periods : int
        Minimum history before a causal value is produced; earlier days are NaN.
    ridge : float
        Small diagonal added to the covariance before inversion, for numerical stability.
    """
    if returns.shape[1] < 2:
        raise ValueError("turbulence is a cross-asset measure; need at least two assets")
    X = returns.astype(float).to_numpy()
    T, n = X.shape
    eye = np.eye(n) * ridge

    if not causal:
        mu = X.mean(axis=0)
        cov = np.cov(X, rowvar=False) + eye
        inv = np.linalg.inv(cov)
        d = X - mu
        ft = np.einsum("ti,ij,tj->t", d, inv, d)
        return pd.Series(ft, index=returns.index, name="turbulence")

    ft = np.full(T, np.nan)
    for t in range(T):
        if t < min_periods:
            continue
        past = X[max(0, t - window):t]  # strictly before t
        mu = past.mean(axis=0)
        cov = np.cov(past, rowvar=False) + eye
        d = X[t] - mu
        ft[t] = float(d @ np.linalg.solve(cov, d))
    return pd.Series(ft, index=returns.index, name="turbulence")


def fit_turbulence_regimes(
    returns: pd.DataFrame,
    *,
    causal: bool = True,
    window: int = 504,
    log: bool = True,
) -> RegimeFit:
    """Compute turbulence on a cross-asset panel and fit a 2-state HMM to it.

    Returns a RegimeFit whose ``high_vol_filtered()`` is P(ex-normal / turbulent regime). Because
    turbulence separates by level rather than by variance, the regimes are ordered by mean, so the
    stressed (high-turbulence) state is last, exactly as for the volatility model.

    ``log`` applies log1p to the turbulence series before fitting; turbulence is right-skewed and a
    Gaussian-emission HMM behaves better on its log.
    """
    ft = financial_turbulence(returns, causal=causal, window=window).dropna()
    series = np.log1p(ft) if log else ft
    series.name = "log_turbulence" if log else "turbulence"
    return fit_regimes(series, n_regimes=2, order_by="mean")
