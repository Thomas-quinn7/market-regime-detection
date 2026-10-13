"""Regime-conditional allocation across cash, bonds and equity.

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


def vol_threshold_signal(vol: pd.Series, threshold: float) -> pd.Series:
    """Stress flag from a trailing volatility series: 1.0 at or above ``threshold``, else 0.0.

    The simple baseline a regime model has to beat for allocation. It is shaped like a regime
    probability so it drops straight into ``regime_switch_weights``. ``vol`` must be causal (for
    example ``evaluate.realised_vol`` or ``evaluate.ewma_vol``, annualised to match ``threshold``);
    dates where it is undefined are dropped rather than treated as calm.
    """
    vol = vol.dropna()
    return (vol >= threshold).astype(float).rename("vol_stress")


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


def block_bootstrap_sharpe(excess: pd.DataFrame, *, block: int = 63, n_boot: int = 2000,
                           seed: int = 0, periods_per_year: int = 252) -> pd.DataFrame:
    """Bootstrap distribution of annualised Sharpe ratios, one column per strategy.

    Circular block bootstrap on daily *excess* returns: blocks of ``block`` consecutive days keep
    the volatility clustering a plain i.i.d. resample would destroy. The same blocks are drawn for
    every column, so the draws are paired and ``draws[a] - draws[b]`` is a valid distribution for
    the Sharpe difference between two strategies run over the same days.
    """
    x = excess.dropna().to_numpy()
    n = len(x)
    if n < 2 * block:
        raise ValueError(f"need at least {2 * block} rows for block={block}, got {n}")
    rng = np.random.default_rng(seed)
    n_blocks = -(-n // block)  # ceil
    offsets = np.arange(block)
    draws = np.empty((n_boot, x.shape[1]))
    for b in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        idx = ((starts[:, None] + offsets[None, :]) % n).ravel()[:n]
        s = x[idx]
        draws[b] = s.mean(axis=0) / s.std(axis=0, ddof=1) * np.sqrt(periods_per_year)
    return pd.DataFrame(draws, columns=excess.columns)


def static_weights(index: pd.Index, allocation: dict) -> pd.DataFrame:
    """Constant-weight schedule, e.g. ``{'equity': 0.6, 'bonds': 0.4}`` for a 60/40 benchmark."""
    return pd.DataFrame({k: float(v) for k, v in allocation.items()}, index=index)
