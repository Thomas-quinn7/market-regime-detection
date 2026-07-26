"""Macro growth/inflation quadrant regimes and quadrant-conditional allocation.

Point-in-time macro data (first-release, publication-date-aligned) from FRED/ALFRED defines a
growth x inflation quadrant each day; each quadrant maps to a simple asset tilt, backtested with the
existing causal, cost-aware allocation machinery.

Runs offline from the committed first-release caches in data/. A free FRED API key in the
FRED_API_KEY environment variable is needed only to refresh those caches from ALFRED.

Run from the repo root:

    python examples/macro_quadrants.py
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import pandas as pd  # noqa: E402

from regimes.allocation import backtest, performance_stats, static_weights  # noqa: E402
from regimes.data import load_index_prices  # noqa: E402
from regimes.macro import macro_features, macro_quadrant, quadrant_weights  # noqa: E402

START, END = "2005-01-01", "2023-12-31"
FIG_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"


def main() -> None:
    warnings.simplefilter("ignore")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    eq_px = load_index_prices("SPY", START, END)
    assets = pd.DataFrame({
        "equity": eq_px.pct_change(),
        "bonds": load_index_prices("IEF", START, END).pct_change(),
        "cash": load_index_prices("BIL", START, END).pct_change(),
    }).dropna()

    q = macro_quadrant(macro_features(assets.index))
    labels = q["quadrant"].dropna()
    print("Macro growth/inflation quadrants (point-in-time CFNAI + core CPI), share of days:")
    for name, frac in labels.value_counts(normalize=True).items():
        print(f"  {name:<12}{frac:6.1%}")
    print(f"  most recent quadrant: {labels.iloc[-1]} on {labels.index[-1].date()}\n")

    weights = quadrant_weights(labels)
    strategies = {
        "Macro-quadrant tilt": backtest(assets, weights, cost_bps=5.0),
        "Static 100% equity": backtest(assets, static_weights(assets.index, {"equity": 1.0}), cost_bps=5.0),
        "Static 60/40 equity/bonds": backtest(
            assets, static_weights(assets.index, {"equity": 0.6, "bonds": 0.4}), cost_bps=5.0),
    }
    common = None
    for s in strategies.values():
        common = s.index if common is None else common.intersection(s.index)
    strategies = {k: v.reindex(common).dropna() for k, v in strategies.items()}
    rf = assets["cash"]

    print(f"Quadrant-conditional allocation, {common.min().date()} to {common.max().date()} (5 bps costs)\n")
    hdr = f"{'strategy':<28}{'ann ret':>8}{'ann vol':>8}{'Sharpe':>8}{'max DD':>8}{'Calmar':>8}"
    print(hdr)
    print("-" * len(hdr))
    curves = {}
    for name, r in strategies.items():
        st = performance_stats(r, rf=rf.reindex(r.index))
        print(f"{name:<28}{st.ann_return:>7.1%}{st.ann_vol:>8.1%}{st.sharpe:>8.2f}"
              f"{st.max_drawdown:>8.1%}{st.calmar:>8.2f}")
        curves[name] = (1.0 + r).cumprod()

    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(12, 5.5))
    for name, c in curves.items():
        ax.plot(c.index, c.values, lw=1.3, label=name)
    ax.set_yscale("log")
    ax.set_ylabel("growth of $1 (log scale)")
    ax.set_title("Macro-quadrant tilt vs static benchmarks (point-in-time macro, after costs)")
    ax.legend(loc="upper left", framealpha=0.9, fontsize=9)
    ax.margins(x=0)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "macro_quadrants.png", dpi=140)
    print(f"\nfigure written to {FIG_DIR / 'macro_quadrants.png'}")


if __name__ == "__main__":
    main()
