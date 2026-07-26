"""Regime-conditional allocation across cash, bonds and equity (roadmap P3).

This is the capstone: it turns a regime probability into a position and holds it to a P&L standard,
which is where the literature (Ang & Bekaert 2004) says the value of regime detection actually shows
up - not in predicting one index's volatility, but in switching across assets to avoid losses.

Look-ahead discipline, non-negotiable here:
- The regime probability driving the allocation must be causal. In practice pass the walk-forward
  out-of-sample high-vol probability (``evaluate.walk_forward_oos``), whose parameters were estimated
  only on past data.
- Weights are applied to the NEXT day's return (``weights.shift(1)``): the position for day t is
  decided from information available at the close of t-1.
- Transaction costs are charged on turnover, so a jumpy signal pays for its jumpiness.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def max_drawdown(returns: pd.Series) -> float:
    """Worst peak-to-trough of the cumulative return (a negative number)."""
    curve = (1.0 + returns).cumprod()
    return float((curve / curve.cummax() - 1.0).min())


def annualized_return(returns: pd.Series, periods_per_year: int = 252) -> float:
    n = len(returns)
    if n == 0:
        return float("nan")
    return float((1.0 + returns).prod() ** (periods_per_year / n) - 1.0)


def annualized_vol(returns: pd.Series, periods_per_year: int = 252) -> float:
    return float(returns.std() * np.sqrt(periods_per_year))


def sharpe(returns: pd.Series, rf: pd.Series | float | None = None, periods_per_year: int = 252) -> float:
    """Annualised Sharpe ratio. ``rf`` may be a per-period risk-free return series or a scalar."""
    excess = returns - (rf if rf is not None else 0.0)
    sd = excess.std()
    if not sd:
        return float("nan")
    return float(excess.mean() / sd * np.sqrt(periods_per_year))


@dataclass
class PerfStats:
    ann_return: float
    ann_vol: float
    sharpe: float
    max_drawdown: float
    calmar: float


def performance_stats(returns: pd.Series, *, rf: pd.Series | float | None = None,
                      periods_per_year: int = 252) -> PerfStats:
    returns = returns.dropna()
    ar = annualized_return(returns, periods_per_year)
    md = max_drawdown(returns)
    return PerfStats(
        ann_return=ar,
        ann_vol=annualized_vol(returns, periods_per_year),
        sharpe=sharpe(returns, rf, periods_per_year),
        max_drawdown=md,
        calmar=float(ar / abs(md)) if md < 0 else float("nan"),
    )


def regime_switch_weights(regime_prob: pd.Series, *, threshold: float = 0.5,
                          risk_on: str = "equity", risk_off: str = "cash") -> pd.DataFrame:
    """Binary risk-on / risk-off weights from a regime probability.

    Below ``threshold`` (calm) hold 100% ``risk_on``; at or above it (stressed) hold 100%
    ``risk_off``. Ang & Bekaert's bear-regime switch is exactly this shape.
    """
    on = (regime_prob < threshold).astype(float)
    return pd.DataFrame({risk_on: on, risk_off: 1.0 - on}, index=regime_prob.index)


def backtest(asset_returns: pd.DataFrame, weights: pd.DataFrame, *, cost_bps: float = 0.0) -> pd.Series:
    """Net portfolio returns for a weight schedule, causal and after transaction costs.

    ``asset_returns`` are simple (not log) returns; ``weights`` columns must be a subset of them. The
    position for day t is ``weights`` from day t-1 (so it uses only past information), and turnover is
    charged ``cost_bps`` basis points.
    """
    cols = list(weights.columns)
    ar = asset_returns[cols].reindex(weights.index)
    effective = weights.shift(1)  # decide at t-1, earn the day-t return
    # Rows before the first fully-defined position have no return. (sum(axis=1) skips NaN and would
    # otherwise report a spurious 0 for them, so filter explicitly rather than dropna.)
    valid = effective.notna().all(axis=1)
    gross = (effective * ar).sum(axis=1)
    turnover = effective.diff().abs().sum(axis=1)  # initial establishment is not charged
    net = gross - (cost_bps / 1e4) * turnover
    return net[valid].rename("portfolio")


def static_weights(index: pd.Index, allocation: dict) -> pd.DataFrame:
    """Constant-weight schedule, e.g. ``{'equity': 0.6, 'bonds': 0.4}`` for a 60/40 benchmark."""
    return pd.DataFrame({k: float(v) for k, v in allocation.items()}, index=index)
