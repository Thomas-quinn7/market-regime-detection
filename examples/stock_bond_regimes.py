"""Stock-bond correlation regimes: does a hidden Markov model beat a trailing correlation?

Run from the repo root:

    python examples/stock_bond_regimes.py

Fits the correlation HMM (``regimes.correlation``) walk-forward on SPY and IEF in two variants, the
pre-registered unconstrained one and one with variances tied across states (added after the first
showed its states splitting on volatility shocks), then scores each one's implied next-quarter correlation against trailing and EWMA correlations on the same days, checks
which signal turned positive first in the 2021-2022 flip, and writes docs/figures/stock_bond_regimes.png.
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from regimes.correlation import (  # noqa: E402
    ewma_corr,
    forward_corr,
    trailing_corr,
    walk_forward_corr_regimes,
)
from regimes.data import load_index_returns  # noqa: E402

START, END = "2005-01-01", "2023-12-31"
HORIZON = 63  # one quarter: the forecast window and the realised-correlation target
FIG_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"


def _first_sustained_positive(s: pd.Series, after: str, run: int = 21) -> str:
    """First date after ``after`` where ``s`` is above zero and stays there for ``run`` days."""
    s = s.loc[after:]
    pos = (s > 0).astype(int)
    held = pos[::-1].rolling(run).min()[::-1]  # 1 when this and the next run-1 days are all positive
    hits = held[held == 1]
    return str(hits.index[0].date()) if len(hits) else "never"


def _positive_episodes(s: pd.Series, run: int = 21) -> int:
    """Number of separate stretches of at least ``run`` days with ``s`` above zero."""
    pos = (s > 0).to_numpy()
    count = length = 0
    for p in pos:
        length = length + 1 if p else 0
        if length == run:
            count += 1
    return count


def main() -> None:
    warnings.simplefilter("ignore")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    rets = pd.DataFrame({
        "equity": load_index_returns("SPY", START, END),
        "bonds": load_index_returns("IEF", START, END),
    }).dropna()

    wf = walk_forward_corr_regimes(rets, min_train=756, step=63, horizon=HORIZON)
    wf_t = walk_forward_corr_regimes(rets, min_train=756, step=63, horizon=HORIZON, tie_variances=True)
    days = wf.implied_corr.index
    for label, res in (("unconstrained (pre-registered)", wf), ("tied variances", wf_t)):
        print(f"{label}: {days.min().date()} -> {days.max().date()}, refits={res.n_refits}, "
              f"skipped={res.n_skipped}; state correlations, first and last refit:")
        print(res.state_rho.iloc[[0, -1]].round(2).to_string())

    target = forward_corr(rets, HORIZON)
    signals = {
        "HMM implied correlation": wf.implied_corr,
        "HMM, tied variances": wf_t.implied_corr,
        "trailing 63-day correlation": trailing_corr(rets, 63),
        "trailing 252-day correlation": trailing_corr(rets, 252),
        "EWMA correlation (0.97)": ewma_corr(rets, alpha=0.03),
    }
    df = pd.concat({"target": target, **signals}, axis=1).loc[days].dropna()
    print(f"\nforecasting next-quarter stock-bond correlation, same {len(df)} days")
    print(f"{'signal':<30}{'corr':>7}{'RMSE':>7}{'sign right':>12}")
    for name in signals:
        err = df[name] - df["target"]
        print(f"{name:<30}{df[name].corr(df['target']):>7.3f}{np.sqrt((err ** 2).mean()):>7.3f}"
              f"{(np.sign(df[name]) == np.sign(df['target'])).mean():>11.0%}")

    # Paired circular block bootstrap on the squared-error difference against the trailing 63-day
    # correlation. Overlapping quarterly targets make neighbouring days dependent; quarter blocks
    # keep that dependence inside each block.
    rng = np.random.default_rng(0)
    base = "trailing 63-day correlation"
    n, block = len(df), HORIZON
    offsets = np.arange(block)
    print(f"\nRMSE minus {base} RMSE, 95% block-bootstrap interval (negative = better)")
    for name in signals:
        if name == base:
            continue
        e1 = (df[name] - df["target"]).to_numpy() ** 2
        e0 = (df[base] - df["target"]).to_numpy() ** 2
        diffs = []
        for _ in range(2000):
            idx = ((rng.integers(0, n, -(-n // block))[:, None] + offsets).ravel() % n)[:n]
            diffs.append(np.sqrt(e1[idx].mean()) - np.sqrt(e0[idx].mean()))
        lo, hi = np.percentile(diffs, [2.5, 97.5])
        print(f"  {name:<30}[{lo:+.3f}, {hi:+.3f}]")

    print("\nthe 2021-2022 flip: first date each signal is positive and stays so for 21 days")
    print(f"  {'realised next-quarter (hindsight)':<34}{_first_sustained_positive(df['target'], '2021-01-01')}")
    print(f"  {'HMM P(positive state) >= 0.5':<34}"
          f"{_first_sustained_positive(wf.prob_high - 0.5, '2021-01-01')}")
    print(f"  {'tied HMM P(positive state) >= 0.5':<34}"
          f"{_first_sustained_positive(wf_t.prob_high - 0.5, '2021-01-01')}")
    for name in signals:
        print(f"  {name:<34}{_first_sustained_positive(df[name], '2021-01-01')}")
    print("\npositive stretches of 21+ days, 2008-2023 (how often each signal claims a flip)")
    print(f"  {'realised next-quarter (hindsight)':<34}{_positive_episodes(df['target'])}")
    for name in signals:
        print(f"  {name:<34}{_positive_episodes(df[name])}")

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 6.5), sharex=True,
                                   gridspec_kw={"height_ratios": [2.2, 1]})
    ax1.plot(df.index, df["target"], color="#222222", lw=1.0, label="realised next-quarter (target)")
    ax1.plot(df.index, df["HMM, tied variances"], color="#2e7d32", lw=1.3,
             label="HMM implied, tied variances (walk-forward)")
    ax1.plot(df.index, df[base], color="#c77c2a", lw=1.0, alpha=0.9, label=base)
    ax1.axhline(0, color="#888888", lw=0.8)
    ax1.set_ylabel("SPY-IEF correlation")
    ax1.set_title("Stock-bond correlation: HMM vs trailing correlation (walk-forward OOS)")
    ax1.legend(loc="lower left", fontsize=9, framealpha=0.9)
    ax2.fill_between(wf_t.prob_high.index, wf_t.prob_high.values, color="#6c8ebf", alpha=0.6, lw=0)
    ax2.set_ylim(0, 1)
    ax2.set_ylabel("P(positive-corr\nstate)")
    ax2.margins(x=0)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "stock_bond_regimes.png", dpi=140)
    print(f"\nfigure written to {FIG_DIR / 'stock_bond_regimes.png'}")


if __name__ == "__main__":
    main()
