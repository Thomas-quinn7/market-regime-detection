"""Run the frozen stock-bond correlation protocol (docs/HOLDOUT_PROTOCOL.md).

Run from the repo root:

    python examples/stock_bond_holdout.py --period dev       # 2005-2023, already seen, for debugging
    python examples/stock_bond_holdout.py --period holdout   # 1962-2004, run once

Both periods use the same long-sample data (S&P 500 index and the FRED 10-year Treasury proxy), so
the dev run checks the script end to end on data that has already been looked at.
"""
from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd

from regimes.correlation import (
    ewma_corr,
    forward_corr,
    regime_flips,
    score_detection,
    sustained_sign_state,
    trailing_corr,
    walk_forward_corr_regimes,
)
from regimes.data import load_index_returns, load_treasury_10y_returns

PERIODS = {"dev": ("2005-01-01", "2023-12-31"), "holdout": ("1962-01-01", "2004-12-31")}
HORIZON = 63


def _rmse_diff_interval(err: np.ndarray, err_base: np.ndarray, block: int = 63,
                        n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """Paired circular block-bootstrap 95% interval for RMSE(signal) - RMSE(baseline)."""
    rng = np.random.default_rng(seed)
    n = len(err)
    offsets = np.arange(block)
    diffs = np.empty(n_boot)
    for b in range(n_boot):
        idx = ((rng.integers(0, n, -(-n // block))[:, None] + offsets).ravel() % n)[:n]
        diffs[b] = np.sqrt((err[idx] ** 2).mean()) - np.sqrt((err_base[idx] ** 2).mean())
    lo, hi = np.percentile(diffs, [2.5, 97.5])
    return float(lo), float(hi)


def main() -> None:
    warnings.simplefilter("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", choices=sorted(PERIODS), required=True)
    start, end = PERIODS[parser.parse_args().period]

    rets = pd.concat({
        "equity": load_index_returns("^GSPC", "1962-01-01", "2023-12-31").loc[start:end],
        "bonds": load_treasury_10y_returns("1962-01-01", "2023-12-31").loc[start:end],
    }, axis=1, sort=True).dropna()
    print(f"period {start} -> {end}: {len(rets)} common days")

    wf_a = walk_forward_corr_regimes(rets, min_train=756, step=63, horizon=HORIZON)
    wf_b = walk_forward_corr_regimes(rets, min_train=756, step=63, horizon=HORIZON,
                                     tie_variances=True)
    days = wf_a.implied_corr.index
    for label, res in (("A unconstrained", wf_a), ("B tied variances", wf_b)):
        rho = res.state_rho
        print(f"{label}: refits={res.n_refits}, skipped={res.n_skipped}; state correlations "
              f"median {rho.median().round(2).tolist()}, first {rho.iloc[0].round(2).tolist()}, "
              f"last {rho.iloc[-1].round(2).tolist()}")

    target = forward_corr(rets, HORIZON)
    levels = {
        "A implied correlation": wf_a.implied_corr,
        "B implied correlation": wf_b.implied_corr,
        "trailing 63-day correlation": trailing_corr(rets, 63),
        "trailing 252-day correlation": trailing_corr(rets, 252),
        "EWMA correlation (0.97)": ewma_corr(rets, alpha=0.03),
    }
    df = pd.concat({"target": target, **levels}, axis=1, sort=True).loc[days].dropna()
    base = "trailing 63-day correlation"
    print(f"\n1. level forecast of next-quarter correlation, {len(df)} days "
          f"({df.index.min().date()} -> {df.index.max().date()})")
    print(f"{'signal':<30}{'corr':>7}{'RMSE':>7}   RMSE - {base} RMSE, 95% interval")
    e_base = (df[base] - df["target"]).to_numpy()
    for name in levels:
        err = (df[name] - df["target"]).to_numpy()
        line = f"{name:<30}{df[name].corr(df['target']):>7.3f}{np.sqrt((err ** 2).mean()):>7.3f}"
        if name != base:
            lo, hi = _rmse_diff_interval(err, e_base)
            verdict = "beats baseline" if hi < 0 else ("worse" if lo > 0 else "no difference")
            line += f"   [{lo:+.3f}, {hi:+.3f}] {verdict}"
        print(line)

    # 2. Regime detection, scored on the same days.
    flips = regime_flips(df["target"], min_len=126)
    print(f"\n2. regime detection: {len(flips)} lasting flips in the target "
          f"(runs of 126+ days): " + ", ".join(f"{d.date()} to {'+' if s > 0 else '-'}"
                                               for d, s in flips))
    signs = {name: df[name] for name in levels}
    signs["B classifier P(positive) - 0.5"] = (wf_b.prob_high - 0.5).loc[df.index]
    results = {}
    print(f"{'signal':<34}{'median lag':>11}{'misses':>8}{'false alarms':>14}   lags (trading days)")
    for name, sig in signs.items():
        lags, misses, fa = score_detection(sustained_sign_state(sig, run=21), flips, max_lag=252)
        results[name] = (np.median(lags) if lags else np.nan, misses, fa)
        print(f"{name:<34}{results[name][0]:>11.0f}{misses:>8}{fa:>14}   "
              f"{[int(x) for x in lags]}")

    clf, b63 = results["B classifier P(positive) - 0.5"], results[base]
    passed = clf[0] < b63[0] and clf[1] <= b63[1] and clf[2] <= b63[2]
    print(f"\nprotocol verdict, B classifier vs {base}: "
          f"{'ADDS SOMETHING' if passed else 'does not add anything'} "
          f"(median lag {clf[0]:.0f} vs {b63[0]:.0f}, misses {clf[1]} vs {b63[1]}, "
          f"false alarms {clf[2]} vs {b63[2]})")


if __name__ == "__main__":
    main()
