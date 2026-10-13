"""Regime-conditional allocation across cash, bonds and equity.

Turns the walk-forward out-of-sample regime probability into a position and holds it to a P&L
standard, versus static benchmarks, after transaction costs. This is the test the literature says
matters: does knowing the regime let you avoid losses by switching assets?

Everything is causal: the regime probability is walk-forward OOS (past-only parameters), positions
are applied to the next day's return, and turnover is charged.

Run from the repo root:

    python examples/regime_allocation.py
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from regimes.allocation import (  # noqa: E402
    backtest,
    block_bootstrap_sharpe,
    performance_stats,
    regime_switch_weights,
    static_weights,
    vol_threshold_signal,
)
from regimes.data import load_index_prices, load_index_returns  # noqa: E402
from regimes.evaluate import ewma_vol, realised_vol  # noqa: E402
from regimes.evaluate import walk_forward_oos  # noqa: E402

START, END = "2005-01-01", "2023-12-31"
FIG_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"


def main() -> None:
    warnings.simplefilter("ignore")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    # Simple (not log) returns for the tradable assets: equity, 7-10y Treasuries, T-bills as cash.
    eq = load_index_prices("SPY", START, END).pct_change()
    bond = load_index_prices("IEF", START, END).pct_change()
    cash = load_index_prices("BIL", START, END).pct_change()
    assets = pd.DataFrame({"equity": eq, "bonds": bond, "cash": cash}).dropna()

    # Causal, walk-forward OOS regime probability on the S&P 500.
    spy = load_index_returns("SPY", START, END)  # log returns in percent
    prob = walk_forward_oos(spy, min_train=756, step=63).high_vol_prob

    # The baseline the regime model has to beat: switch on plain trailing vol (annualised, percent).
    # The 20% threshold is a round number fixed in advance, not tuned; the grid below shows the spread.
    rv21 = realised_vol(spy, 21) * np.sqrt(252)
    ewma = ewma_vol(spy) * np.sqrt(252)

    rf = assets["cash"]
    # Volatility targeting (Moreira & Muir 2017 style), no leverage: equity weight = 10% / EWMA vol,
    # capped at 1, the rest in cash. The standard continuous alternative to a binary switch.
    eq_w = (10.0 / ewma).clip(upper=1.0).dropna()
    vol_target_weights = pd.DataFrame({"equity": eq_w, "cash": 1.0 - eq_w})

    strategies = {
        "Regime switch equity/cash": backtest(
            assets, regime_switch_weights(prob, risk_on="equity", risk_off="cash"), cost_bps=5.0),
        "Regime switch equity/bonds": backtest(
            assets, regime_switch_weights(prob, risk_on="equity", risk_off="bonds"), cost_bps=5.0),
        "21d vol > 20% equity/cash": backtest(
            assets, regime_switch_weights(vol_threshold_signal(rv21, 20.0)), cost_bps=5.0),
        "EWMA vol > 20% equity/cash": backtest(
            assets, regime_switch_weights(vol_threshold_signal(ewma, 20.0)), cost_bps=5.0),
        "EWMA vol target 10%": backtest(assets, vol_target_weights, cost_bps=5.0),
        "Static 100% equity": backtest(
            assets, static_weights(assets.index, {"equity": 1.0}), cost_bps=5.0),
        "Static 60/40 equity/bonds": backtest(
            assets, static_weights(assets.index, {"equity": 0.6, "bonds": 0.4}), cost_bps=5.0),
    }
    # Compare all strategies over the same window (where the regime signal exists).
    common = None
    for s in strategies.values():
        common = s.index if common is None else common.intersection(s.index)
    strategies = {k: v.reindex(common).dropna() for k, v in strategies.items()}

    print(f"Regime-conditional allocation, {common.min().date()} to {common.max().date()} "
          f"(walk-forward OOS signal, 5 bps costs)\n")
    hdr = f"{'strategy':<30}{'ann ret':>8}{'ann vol':>8}{'Sharpe':>8}{'max DD':>8}{'Calmar':>8}"
    print(hdr)
    print("-" * len(hdr))
    curves = {}
    for name, r in strategies.items():
        st = performance_stats(r, rf=rf.reindex(r.index))
        print(f"{name:<30}{st.ann_return:>7.1%}{st.ann_vol:>8.1%}{st.sharpe:>8.2f}"
              f"{st.max_drawdown:>8.1%}{st.calmar:>8.2f}")
        curves[name] = (1.0 + r).cumprod()

    # Threshold sensitivity for the trailing-vol rules: one window, so read the spread, not the best.
    print("\ntrailing-vol switch (equity/cash), Sharpe / max drawdown / share of days in cash")
    for vol_name, vol in (("21d vol", rv21), ("EWMA vol", ewma)):
        cells = []
        for thr in (15.0, 20.0, 25.0):
            sig = vol_threshold_signal(vol, thr)
            r = backtest(assets, regime_switch_weights(sig), cost_bps=5.0).reindex(common).dropna()
            st = performance_stats(r, rf=rf.reindex(r.index))
            cells.append(f"{thr:.0f}%: {st.sharpe:.2f} / {st.max_drawdown:.0%} / "
                         f"{sig.reindex(common).mean():.0%}")
        print(f"  {vol_name:<9}" + "   ".join(cells))
    print(f"  {'HMM':<9}0.5 prob: share of days in cash {(prob.reindex(common) >= 0.5).mean():.0%}")

    # Can one 16-year path tell these apart? Paired circular block bootstrap (quarter-long blocks).
    excess = pd.DataFrame({k: v - rf.reindex(v.index) for k, v in strategies.items()})
    draws = block_bootstrap_sharpe(excess, block=63, n_boot=2000, seed=0)
    base = "Regime switch equity/cash"
    print(f"\nSharpe 95% interval, and the interval for (strategy - {base}), block bootstrap")
    for name in draws.columns:
        lo, hi = np.percentile(draws[name], [2.5, 97.5])
        line = f"  {name:<30}[{lo:5.2f}, {hi:5.2f}]"
        if name != base:
            dlo, dhi = np.percentile(draws[name] - draws[base], [2.5, 97.5])
            line += f"   diff [{dlo:+.2f}, {dhi:+.2f}]"
        print(line)

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 5.5))
    plotted = ["Regime switch equity/cash", "21d vol > 20% equity/cash",
               "Static 100% equity", "Static 60/40 equity/bonds"]  # four lines stay readable
    for name in plotted:
        c = curves[name]
        ax.plot(c.index, c.values, lw=1.3, label=name)
    ax.set_yscale("log")
    ax.set_ylabel("growth of $1 (log scale)")
    ax.set_title("Regime-conditional allocation vs static benchmarks (walk-forward OOS, after costs)")
    ax.legend(loc="upper left", framealpha=0.9, fontsize=9)
    ax.margins(x=0)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "regime_allocation.png", dpi=140)
    print(f"\nfigure written to {FIG_DIR / 'regime_allocation.png'}")


if __name__ == "__main__":
    main()
