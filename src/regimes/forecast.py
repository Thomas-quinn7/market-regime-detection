"""Volatility forecasting baselines and a like-for-like forecast comparison.

The headline test in this repo correlates a regime probability with next-month realised vol. That
says whether a signal ranks future vol well, not whether it forecasts it accurately. This module
turns every signal into an actual forecast in the same units and scores them on the same days:

- ``har_features``: the HAR-RV components (Corsi 2009) built from daily returns: the last day's
  absolute return and the root-mean-square return over the last 5 and 22 days.
- ``walk_forward_regression``: an expanding-window OLS of next-``horizon``-day realised vol on any set
  of causal features, refit every ``step`` days. Training rows are **embargoed**: a row's target
  covers the ``horizon`` days after it, so only rows whose target was fully known before the refit
  date are used. This is the same no-look-ahead rule as the regime walk-forward, applied to the
  calibration step.
- ``forecast_losses``: RMSE on volatility and QLIKE on variance (Patton 2011; robust to noise in the
  realised-vol proxy, and it punishes under-forecasting more than over-forecasting).
- ``paired_rmse_diff_interval`` and ``paired_mean_diff_interval``: paired circular block-bootstrap
  intervals for the RMSE (or mean-loss, e.g. QLIKE) difference between two forecasts on the same days.

Calibrating every signal with the same walk-forward regression puts raw signals on an equal footing:
VIX is biased upwards by the variance risk premium, and a regime probability is not in vol units at
all, so scoring either raw on RMSE would be unfair to it.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .evaluate import realised_vol

_FLOOR = 1e-3  # a volatility forecast must be positive for QLIKE


def har_features(returns: pd.Series) -> pd.DataFrame:
    """HAR-RV inputs from daily returns: |r_t| and RMS returns over the last 5 and 22 days (causal)."""
    sq = returns.astype(float) ** 2
    return pd.DataFrame({
        "rv_1d": np.sqrt(sq),
        "rv_5d": np.sqrt(sq.rolling(5).mean()),
        "rv_22d": np.sqrt(sq.rolling(22).mean()),
    })


def forward_vol(returns: pd.Series, horizon: int = 21) -> pd.Series:
    """Realised vol over the NEXT ``horizon`` days, (t, t + horizon]: the target."""
    return realised_vol(returns, horizon).shift(-horizon)


@dataclass
class RegressionForecast:
    forecast: pd.Series     # out-of-sample forecasts of next-``horizon``-day vol
    coefs: pd.DataFrame     # per-refit coefficients (diagnostic), indexed by refit date
    n_refits: int


def walk_forward_regression(target: pd.Series, features: pd.DataFrame | pd.Series, *,
                            horizon: int = 21, step: int = 63, min_rows: int = 252,
                            log_target: bool = False) -> RegressionForecast:
    """Expanding-window OLS forecast of ``target`` from ``features``, embargoed against overlap.

    Rows are the dates where every feature is present. At refit position ``i`` the model is fit on
    rows ``[: i - horizon]`` (the target at row ``t`` uses returns up to ``t + horizon``, so it is only
    known from row ``t + horizon`` onward) and used to forecast rows ``[i : i + step]``. The first
    refit waits until ``min_rows`` training rows exist.

    ``log_target=True`` regresses ``log(target)`` instead and returns ``exp(fit) * exp(s^2 / 2)``, with
    ``s^2`` the training residual variance (the lognormal mean correction). Log-scale fits cannot go
    negative and extrapolate far more tamely in a volatility spike than a level fit does.
    """
    X_all = features.to_frame() if isinstance(features, pd.Series) else features
    X_all = X_all.dropna()
    y_all = target.reindex(X_all.index)
    X = np.column_stack([np.ones(len(X_all)), X_all.to_numpy(dtype=float)])
    y = y_all.to_numpy(dtype=float)
    if log_target:
        y = np.log(y)
    n = len(X_all)

    pieces, coef_rows, coef_idx = [], [], []
    for i in range(min_rows + horizon, n, step):
        end = min(i + step, n)
        tr = slice(0, i - horizon)
        ok = ~np.isnan(y[tr])
        beta = np.linalg.lstsq(X[tr][ok], y[tr][ok], rcond=None)[0]
        pred = X[i:end] @ beta
        if log_target:
            resid_var = float(((y[tr][ok] - X[tr][ok] @ beta) ** 2).mean())
            pred = np.exp(pred + 0.5 * resid_var)
        pieces.append(pd.Series(np.maximum(pred, _FLOOR), index=X_all.index[i:end]))
        coef_rows.append(beta)
        coef_idx.append(X_all.index[i])
    if not pieces:
        raise ValueError(f"not enough rows ({n}) for min_rows={min_rows} and horizon={horizon}")
    cols = ["const", *X_all.columns]
    return RegressionForecast(
        forecast=pd.concat(pieces),
        coefs=pd.DataFrame(coef_rows, index=pd.DatetimeIndex(coef_idx), columns=cols),
        n_refits=len(pieces),
    )


def qlike(forecast_vol: np.ndarray, realised: np.ndarray) -> np.ndarray:
    """Per-day QLIKE loss on variances: y/f - log(y/f) - 1, zero for a perfect forecast."""
    ratio = (np.asarray(realised) ** 2) / (np.asarray(forecast_vol) ** 2)
    return ratio - np.log(ratio) - 1.0


def forecast_losses(forecasts: dict[str, pd.Series], target: pd.Series) -> pd.DataFrame:
    """RMSE, QLIKE and Pearson correlation for each forecast, all on their common dates."""
    joined = pd.concat({"y": target, **forecasts}, axis=1, sort=True).dropna()
    y = joined["y"].to_numpy()
    rows = {}
    for name in forecasts:
        f = joined[name].to_numpy()
        rows[name] = {
            "rmse": float(np.sqrt(((f - y) ** 2).mean())),
            "qlike": float(qlike(f, y).mean()),
            "pearson": float(np.corrcoef(f, y)[0, 1]),
        }
    out = pd.DataFrame(rows).T
    out["n"] = len(joined)
    return out


def paired_rmse_diff_interval(err: np.ndarray, err_base: np.ndarray, *, block: int = 63,
                              n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """Paired circular block-bootstrap 95% interval for RMSE(err) - RMSE(err_base).

    Same days in every draw for both forecasts, so the interval is about the difference, and blocks of
    ``block`` days keep the overlap and volatility clustering in the errors.
    """
    rng = np.random.default_rng(seed)
    err, err_base = np.asarray(err), np.asarray(err_base)
    n = len(err)
    offsets = np.arange(block)
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        idx = ((rng.integers(0, n, -(-n // block))[:, None] + offsets).ravel() % n)[:n]
        diffs[b] = np.sqrt((err[idx] ** 2).mean()) - np.sqrt((err_base[idx] ** 2).mean())
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(lo), float(hi)


def paired_mean_diff_interval(loss: np.ndarray, loss_base: np.ndarray, *, block: int = 63,
                              n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """Paired circular block-bootstrap 95% interval for mean(loss) - mean(loss_base), e.g. QLIKE."""
    rng = np.random.default_rng(seed)
    d = np.asarray(loss) - np.asarray(loss_base)
    n = len(d)
    offsets = np.arange(block)
    means = np.empty(n_boot)
    for b in range(n_boot):
        idx = ((rng.integers(0, n, -(-n // block))[:, None] + offsets).ravel() % n)[:n]
        means[b] = d[idx].mean()
    lo, hi = np.percentile(means, [2.5, 97.5])
    return float(lo), float(hi)
