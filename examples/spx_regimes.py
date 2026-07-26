"""Reproducible end-to-end analysis behind docs/WRITEUP.md.

Run from the repo root:

    python examples/spx_regimes.py

It (1) fits a 2-state switching-variance regime model to S&P 500 daily returns, (2) runs the honest
walk-forward out-of-sample evaluation, (3) prints the result ladder, and (4) writes two figures to
docs/figures/. Numbers quoted in the write-up come straight from this script — nothing is
hand-transcribed.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # headless: save files, never open a window on import/run
import matplotlib.pyplot as plt  # noqa: E402

from regimes.data import load_index_prices, load_index_returns  # noqa: E402
from regimes.evaluate import oos_realised_vol_check, walk_forward_oos  # noqa: E402
from regimes.model import fit_regimes  # noqa: E402

START, END = "2005-01-01", "2023-12-31"
FIG_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"


def main() -> None:
    warnings.simplefilter("ignore")  # statsmodels chatter; the code paths are covered by tests
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    prices = load_index_prices(start=START, end=END)
    returns = load_index_returns(start=START, end=END)
    print(f"S&P 500 daily returns: {len(returns)} obs, {returns.index.min().date()} -> "
          f"{returns.index.max().date()}")

    # (1) Full-sample fit — used ONLY for the descriptive history figure and the leaky baselines.
    fit = fit_regimes(returns, n_regimes=2)
    print(f"regime variances (ascending): {fit.variances.round(3)}  "
          f"=> vol ratio {(fit.variances[-1] / fit.variances[0]) ** 0.5:.1f}x")

    naive = oos_realised_vol_check(returns, fit, horizon=21)

    # (2) Honest walk-forward: quarterly refit, frozen params filtered forward onto held-out blocks.
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=21)

    # (3) The ladder.
    ladder = [
        ("smoothed (full-sample, peeks at future data)", naive.corr_smoothed),
        ("filtered (full-sample params, causal data)", naive.corr_filtered),
        ("walk-forward (frozen params, fully out-of-sample)", wf.corr),
    ]
    print("\ncorr( high-vol probability , next-month realised vol )")
    print("-" * 62)
    for label, val in ladder:
        print(f"{label:<52}{val:6.3f}")
    print(f"\nwalk-forward: n={wf.n}, refits={wf.n_refits}, skipped={wf.n_skipped}")

    # (4a) Headline figure: price with out-of-sample high-vol regimes shaded.
    from regimes.plots import plot_price_with_regimes

    fig1 = plot_price_with_regimes(
        prices, wf.high_vol_prob,
        title="S&P 500 with walk-forward (out-of-sample) high-volatility regimes",
    )
    fig1.savefig(FIG_DIR / "spx_regimes.png", dpi=140)

    # (4b) Ladder figure: the honest-vs-leaky comparison.
    fig2, ax = plt.subplots(figsize=(8, 3.6))
    labels = ["smoothed\n(peeks at future)", "filtered\n(full-sample params)", "walk-forward\n(fully OOS)"]
    vals = [naive.corr_smoothed, naive.corr_filtered, wf.corr]
    colors = ["#b0b0b0", "#6c8ebf", "#2e7d32"]  # grey -> blue -> green: leaky to honest
    bars = ax.bar(labels, vals, color=colors, width=0.6)
    ax.bar_label(bars, fmt="%.3f", padding=3)
    ax.set_ylabel("corr with next-month\nrealised vol")
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_title("The look-ahead premium: leaky vs honest evaluation")
    fig2.tight_layout()
    fig2.savefig(FIG_DIR / "result_ladder.png", dpi=140)

    print(f"\nfigures written to {FIG_DIR}")


if __name__ == "__main__":
    main()
