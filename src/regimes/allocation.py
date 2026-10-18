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


def turnover(weights: pd.DataFrame, *, execution_lag: int = 1) -> pd.Series:
    """Daily turnover a weight schedule trades: the sum of absolute weight changes on the day they
    are executed, i.e. after ``execution_lag`` days (see ``backtest``). The initial establishment is
    not counted. Rows before the first fully-defined position are dropped.
    """
    if execution_lag < 1:
        raise ValueError("execution_lag must be at least 1 (a position cannot earn the return that set it)")
    effective = weights.shift(execution_lag)
    valid = effective.notna().all(axis=1)
    return effective.diff().abs().sum(axis=1)[valid].rename("turnover")


def backtest(asset_returns: pd.DataFrame, weights: pd.DataFrame, *, cost_bps: float = 0.0,
             execution_lag: int = 1) -> pd.Series:
    """Net portfolio returns for a weight schedule, causal and after transaction costs.

    ``asset_returns`` are simple (not log) returns; ``weights`` columns must be a subset of them. The
    position earning the day-t return is ``weights`` from day ``t - execution_lag``, and turnover is
    charged ``cost_bps`` basis points.

    ``execution_lag=1`` (the default, and what the published table uses) decides the position at the
    close of t-1 and earns close(t-1) to close(t): the trade is filled at the same close that produced
    the signal. ``execution_lag=2`` fills one close later (signal at t-2, traded at the close of t-1,
    earning close(t-1) to close(t)), which is the realistic rule for a signal computed from closing
    prices; the gap between the two is the execution-timing cost of the strategy.
    """
    cols = list(weights.columns)
    ar = asset_returns[cols].reindex(weights.index)
    if execution_lag < 1:
        raise ValueError("execution_lag must be at least 1 (a position cannot earn the return that set it)")
    effective = weights.shift(execution_lag)  # decide at t-lag, earn the day-t return
    # Rows before the first fully-defined position have no return. (sum(axis=1) skips NaN and would
    # otherwise report a spurious 0 for them, so filter explicitly rather than dropna.)
    valid = effective.notna().all(axis=1)
    gross = (effective * ar).sum(axis=1)
    traded = effective.diff().abs().sum(axis=1)  # initial establishment is not charged
    net = gross - (cost_bps / 1e4) * traded
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


@dataclass
class RebalancedResult:
    net: pd.Series        # daily net return of the drifting portfolio
    turnover: pd.Series   # turnover traded on each day (zero on days with no new position)
    weights: pd.DataFrame  # weights held during each day (after drift, and after that day's trade)


def drift_backtest(asset_returns: pd.DataFrame, decided: pd.DataFrame, *, cost_bps: float = 0.0,
                   execution_lag: int = 1) -> RebalancedResult:
    """A portfolio that drifts with returns between decisions and trades only when a new decision arrives.

    ``decided`` has one row per day and the same columns as the assets traded. A row of NaN means "no new
    decision": the weights carried into that day drift on. A full row is a target weight vector (summing
    to one) decided at the close of that day with information up to it; it is held from
    ``execution_lag`` days later (``execution_lag=1``: the position earning day t+1 was decided at the
    close of t and filled at that close; ``2``: filled at the close of t+1, one day later), the same
    convention as ``backtest``. Turnover is the absolute weight change from the drifted weights to the
    target on the day the new position first earns, charged ``cost_bps`` basis points; the first position
    is established without charge. ``asset_returns`` are simple returns; days with a missing asset return
    are dropped.
    """
    if execution_lag < 1:
        raise ValueError("execution_lag must be at least 1 (a position cannot earn the return that set it)")
    cols = list(decided.columns)
    ar = asset_returns[cols].dropna()
    dec = decided.reindex(ar.index)
    partial = dec.notna().any(axis=1) & ~dec.notna().all(axis=1)
    if partial.any():
        raise ValueError("a decision row must be fully defined or all NaN")
    sums = dec.dropna().sum(axis=1)
    if len(sums) and (sums - 1.0).abs().max() > 1e-9:
        raise ValueError("decided weights must sum to one on every decision day")
    eff = dec.shift(execution_lag)
    has = eff.notna().all(axis=1).to_numpy()
    if not has.any():
        raise ValueError("no decision becomes effective inside the data")
    first = int(np.argmax(has))
    r = ar.to_numpy()[first:]
    e = eff.to_numpy()[first:]
    h = has[first:]
    n = len(r)
    held = np.empty((n, len(cols)))
    net = np.empty(n)
    traded = np.zeros(n)
    cost = cost_bps / 1e4
    w = e[0].copy()
    for t in range(n):
        if t > 0 and h[t]:
            traded[t] = float(np.abs(e[t] - w).sum())
            w = e[t].copy()
        held[t] = w
        rp = float(w @ r[t])
        net[t] = rp - cost * traded[t]
        w = w * (1.0 + r[t]) / (1.0 + rp)
    idx = ar.index[first:]
    return RebalancedResult(net=pd.Series(net, index=idx, name="portfolio"),
                            turnover=pd.Series(traded, index=idx, name="turnover"),
                            weights=pd.DataFrame(held, index=idx, columns=cols))


def period_end_decisions(index: pd.Index, targets: pd.DataFrame | dict, *, freq: str = "ME") -> pd.DataFrame:
    """A decision schedule for ``drift_backtest``: the target weights on the first day and on the last
    trading day of every period (``freq``, pandas offset alias; "ME" is month end), NaN elsewhere.
    ``targets`` is a constant allocation (dict) or a DataFrame of per-day targets to be read on those days.
    The sample's last day counts as a period end; a decision there never becomes effective.
    """
    period = pd.Series(index.to_period("M" if freq in ("ME", "M") else freq), index=index)
    last = (period != period.shift(-1)).to_numpy().copy()
    last[0] = True
    if isinstance(targets, dict):
        targets = pd.DataFrame({k: float(v) for k, v in targets.items()}, index=index)
    out = targets.reindex(index).astype(float).copy()
    out.loc[~last] = np.nan
    return out


def rebalanced_backtest(asset_returns: pd.DataFrame, allocation: dict, *, freq: str = "ME",
                        cost_bps: float = 0.0) -> RebalancedResult:
    """A static-target portfolio that drifts with returns and is reset to target at the close of the
    last trading day of each period (``freq``; "ME" is month end), paying ``cost_bps`` basis points on
    the turnover of each reset: ``drift_backtest`` on ``period_end_decisions`` with lag 1.

    ``static_weights`` + ``backtest`` holds the target weights every day, which is a daily rebalance
    at zero cost (constant weights trade nothing). This is the benchmark a desk would run instead.
    """
    target = np.array([float(allocation[c]) for c in allocation])
    if abs(target.sum() - 1.0) > 1e-12:
        raise ValueError("allocation weights must sum to one")
    ar = asset_returns[list(allocation)].dropna()
    return drift_backtest(ar, period_end_decisions(ar.index, allocation, freq=freq), cost_bps=cost_bps,
                          execution_lag=1)


def block_bootstrap_drawdown(returns: pd.DataFrame, *, block: int = 63, n_boot: int = 2000,
                             seed: int = 0) -> pd.DataFrame:
    """Bootstrap distribution of the maximum drawdown of resampled paths, one column per strategy, with
    the same circular blocks for every column as ``block_bootstrap_sharpe`` (so differences are paired).
    A resampled path is a hypothetical reordering of the same daily returns; its drawdown describes what
    the strategy's return distribution and clustering imply, not the one realised path.
    """
    x = returns.dropna().to_numpy()
    n = len(x)
    if n < 2 * block:
        raise ValueError(f"need at least {2 * block} rows for block={block}, got {n}")
    rng = np.random.default_rng(seed)
    n_blocks = -(-n // block)
    offsets = np.arange(block)
    draws = np.empty((n_boot, x.shape[1]))
    for b in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        idx = ((starts[:, None] + offsets[None, :]) % n).ravel()[:n]
        curve = np.cumprod(1.0 + x[idx], axis=0)
        draws[b] = (curve / np.maximum.accumulate(curve, axis=0) - 1.0).min(axis=0)
    return pd.DataFrame(draws, columns=returns.columns)
