"""Reproducible end-to-end analysis behind docs/WRITEUP.md.

Run from the repo root:

    python examples/spx_regimes.py

It (1) fits a 2-state switching-variance regime model to S&P 500 daily returns, (2) runs the honest
walk-forward out-of-sample evaluation, (3) prints the result ladder on the out-of-sample dates and
sets it against two trailing-vol baselines, and (4) writes two figures to
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
from regimes.evaluate import (  # noqa: E402
    compare_vol_predictors,
    ewma_vol,
    incremental_r2,
    oos_realised_vol_check,
    realised_vol,
    walk_forward_oos,
)
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

    # (2) Honest walk-forward: quarterly refit, frozen params filtered forward onto held-out blocks.
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=21)
    oos_days = wf.high_vol_prob.index

    # The leaky versions are scored on the same out-of-sample dates, so every rung covers one period.
    naive = oos_realised_vol_check(returns, fit, horizon=21, index=oos_days)

    # (3) The ladder, then the question that matters: does the regime model beat trailing vol?
    ladder = [
        ("smoothed (full-sample, peeks at future data)", naive.corr_smoothed),
        ("filtered (full-sample params, causal data)", naive.corr_filtered),
        ("walk-forward (frozen params, fully out-of-sample)", wf.corr),
    ]
    print(f"\ncorr( high-vol probability , next-month realised vol ), "
          f"{oos_days.min().date()} -> {oos_days.max().date()}")
    print("-" * 62)
    for label, val in ladder:
        print(f"{label:<52}{val:6.3f}")
    print(f"\nwalk-forward: n={wf.n}, refits={wf.n_refits}, skipped={wf.n_skipped}")

    rv21 = realised_vol(returns, 21)
    scores = compare_vol_predictors(
        {
            "walk-forward HMM probability": wf.high_vol_prob,
            "trailing 21-day realised vol": rv21.loc[oos_days],
            "EWMA vol (RiskMetrics 0.94)": ewma_vol(returns).loc[oos_days],
        },
        returns, horizon=21,
    )
    print("\nsame dates, same target: the regime model against trailing-vol baselines")
    print(scores.round(3).to_string())
    fut_vol = realised_vol(returns, 21).shift(-21)
    r2_base, r2_both = incremental_r2(fut_vol.loc[oos_days], rv21, wf.high_vol_prob)
    print(f"\nR^2 of next-month vol on trailing 21-day vol: {r2_base:.3f}; "
          f"adding the HMM probability: {r2_both:.3f}")

    # (4a) Headline figure: price with out-of-sample high-vol regimes shaded.
    from regimes.plots import plot_price_with_regimes

    fig1 = plot_price_with_regimes(
        prices, wf.high_vol_prob,
        title="S&P 500 with walk-forward (out-of-sample) high-volatility regimes",
    )
    fig1.savefig(FIG_DIR / "spx_regimes.png", dpi=140)

    # (4b) Ladder figure: leaky vs honest, then the trailing-vol baselines on the same dates.
    fig2, ax = plt.subplots(figsize=(10, 3.9))
    labels = ["smoothed\n(peeks at future)", "filtered\n(full-sample params)", "walk-forward\n(fully OOS)",
              "trailing 21-day\nrealised vol", "EWMA vol\n(RiskMetrics)"]
    vals = [naive.corr_smoothed, naive.corr_filtered, wf.corr,
            scores["pearson"].iloc[1], scores["pearson"].iloc[2]]
    colors = ["#b0b0b0", "#6c8ebf", "#2e7d32", "#c77c2a", "#c77c2a"]  # leaky -> honest, then baselines
    bars = ax.bar(labels, vals, color=colors, width=0.6)
    ax.bar_label(bars, fmt="%.3f", padding=3)
    ax.axvline(2.5, color="#888888", lw=0.8, ls="--")
    ax.set_ylabel("corr with next-month\nrealised vol")
    ax.set_ylim(0, max(vals) * 1.2)
    ax.set_title(f"HMM regime probability vs trailing-vol baselines, same out-of-sample days "
                 f"({oos_days.min().year}-{oos_days.max().year})")
    fig2.tight_layout()
    fig2.savefig(FIG_DIR / "result_ladder.png", dpi=140)

    print(f"\nfigures written to {FIG_DIR}")


if __name__ == "__main__":
    main()
