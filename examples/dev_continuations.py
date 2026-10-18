"""Development-only continuations on the S&P 500 to 2023-12-31. No holdout; nothing here is a claim.

Writes ``docs/DEV_CONTINUATIONS_2026-10.md`` (first line: "development data only, no holdout"). Items from
the reopen scope, stage S4:

(a) horizons 5, 21 and 63 trading days for HAR, HAR + VIX, HAR + HMM prob and HAR + VIX + HMM prob, with
    the frozen VIX script's calibration (expanding OLS on log inputs and log target, refit every 63 days,
    first fit after 756 rows, embargoed by the horizon) and its paired block bootstrap (63-day blocks,
    2,000 draws, seed 0); for the 63-day horizon a 126-day block is shown as well because adjacent
    targets then share 62 of 63 days;
(c) the nesting-noise check: a pure-noise regressor (standard normal, seed 0) added to HAR + VIX, scored
    against HAR + VIX exactly as the HMM probability is. If the noise regressor's interval looks like the
    HMM probability's, the "no difference" verdict for the probability is what nesting alone produces.

Item (b), the K = 3 and 4 Student-t HMMs, is a separate run (examples/dev_k_states.py). Data: S&P 500 and VIX 2005-01-01 to
2023-12-31 from the committed caches (a download attempt raises). Run from the repo root::

    python -u examples/dev_continuations.py [--n-boot 2000] [--out docs/DEV_CONTINUATIONS_2026-10.md]
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from regimes.data import load_index_returns, load_vix  # noqa: E402
from regimes.evaluate import walk_forward_oos  # noqa: E402
from regimes.forecast import forward_vol, har_features, qlike, walk_forward_regression  # noqa: E402
from regimes.posthoc import paired_interval  # noqa: E402

from posthoc_stats import git_head, md_table, verdict  # noqa: E402

START, END = "2005-01-01", "2023-12-31"   # the repo's development period; rule 3 of the reopen scope
HORIZONS = (5, 21, 63)
COMPARISONS = [("HAR + VIX", "HAR"), ("HAR + HMM prob", "HAR"), ("HAR + VIX + HMM prob", "HAR + VIX")]
CLASS = "development data only (S&P 500, 2005-2023), no holdout"


def block_network() -> None:
    def no_network(*a, **k):
        raise RuntimeError("dev_continuations.py reads only the data caches; a download was attempted")
    sys.modules["yfinance"] = types.SimpleNamespace(download=no_network)


def load() -> tuple[pd.Series, pd.Series]:
    returns = load_index_returns(start=START, end=END)
    vix = load_vix(START, END)
    common = returns.index.intersection(vix.index)
    return returns.loc[common], vix.loc[common]


def forecasts_at_horizon(returns: pd.Series, vix: pd.Series, h: int, *, noise: pd.Series | None = None) -> pd.DataFrame:
    """Scored table (target plus one column per model) at horizon ``h``, built as the frozen VIX script
    builds its 21-day one."""
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=h)
    target = forward_vol(returns, h)
    log_har = np.log(har_features(returns).clip(lower=1e-3))
    log_vix = np.log(vix / np.sqrt(252)).rename("vix")
    feature_sets = {
        "HAR": log_har,
        "HAR + VIX": log_har.join(log_vix),
        "HAR + HMM prob": log_har.join(wf.high_vol_prob),
        "HAR + VIX + HMM prob": log_har.join(log_vix).join(wf.high_vol_prob),
    }
    if noise is not None:
        feature_sets["HAR + VIX + noise"] = log_har.join(log_vix).join(noise.rename("noise"))
    fc = {name: walk_forward_regression(target, X, horizon=h, step=63, min_rows=756, log_target=True).forecast
          for name, X in feature_sets.items()}
    joined = pd.concat({"target": target, **fc}, axis=1, sort=True).dropna()
    joined.attrs["n_refits"] = wf.n_refits
    joined.attrs["converged"] = None if wf.convergence is None else int(wf.convergence["best_converged"].sum())
    return joined


def compare(df: pd.DataFrame, name: str, ref: str, n_boot: int, block: int) -> dict:
    y = df["target"].to_numpy()
    e_f, e_b = df[name].to_numpy() - y, df[ref].to_numpy() - y
    q_f, q_b = qlike(df[name].to_numpy(), y), qlike(df[ref].to_numpy(), y)
    r_lo, r_hi = paired_interval(e_f, e_b, statistic="rmse", block=block, n_boot=n_boot)
    q_lo, q_hi = paired_interval(q_f, q_b, statistic="mean", block=block, n_boot=n_boot)
    return {"forecast": name, "reference": ref, "block": block,
            "dRMSE 95%": f"{r_lo:+.3f} to {r_hi:+.3f}", "RMSE": verdict(r_lo, r_hi),
            "dQLIKE 95%": f"{q_lo:+.3f} to {q_hi:+.3f}", "QLIKE": verdict(q_lo, q_hi)}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "docs" / "DEV_CONTINUATIONS_2026-10.md"))
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()
    n_boot = args.n_boot
    block_network()
    returns, vix = load()

    out: list[str] = []
    P = out.append
    P("development data only, no holdout\n")
    P("# Development-only continuations, October 2026\n")
    P(f"Class of every table in this file: **{CLASS}**. These are continuations of the development work, not "
      "claims; no holdout is opened and no registered verdict is touched. Written by "
      f"`examples/dev_continuations.py` at {git_head()}, {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, "
      f"{n_boot:,} bootstrap draws (seed 0). Data: S&P 500 and VIX {returns.index.min().date()} to "
      f"{returns.index.max().date()} ({len(returns)} days) from the committed caches.\n")

    P("## (a) Forecast horizon: 5, 21 and 63 trading days\n")
    P("Same construction as the frozen VIX script at every horizon: target = realised vol over the next h "
      "days; expanding OLS on log HAR inputs (and log VIX / sqrt(252), and the walk-forward HMM high-vol "
      "probability), log target, refit every 63 days after 756 rows, embargo h; paired circular block "
      "bootstrap on the scored days. The HMM is refit walk-forward with the same arguments as in the VIX "
      "script (min_train 756, step 63). The 21-day row is the development-period version of the registered "
      "comparisons and is here only for scale.\n")
    tables = {}
    rng = np.random.default_rng(0)
    noise = pd.Series(rng.standard_normal(len(returns)), index=returns.index)
    for h in HORIZONS:
        print(f"horizon {h} ...", flush=True)
        df = forecasts_at_horizon(returns, vix, h, noise=noise if h == 21 else None)
        tables[h] = df
        y = df["target"].to_numpy()
        losses = [{"model": m, "RMSE": f"{np.sqrt(((df[m] - df['target']) ** 2).mean()):.3f}",
                   "QLIKE": f"{qlike(df[m].to_numpy(), y).mean():.3f}"} for m in df.columns if m != "target"]
        conv = df.attrs["converged"]
        P(f"### Horizon {h}: scored days {len(df)}, {df.index.min().date()} -> {df.index.max().date()}; HMM refits "
          f"{df.attrs['n_refits']}" + (f", converged {conv} of {df.attrs['n_refits']}" if conv is not None else "") + "\n")
        P(md_table(pd.DataFrame(losses)) + "\n")
        rows = [compare(df, f, r, n_boot, 63) for f, r in COMPARISONS]
        if h == 63:
            rows += [compare(df, f, r, n_boot, 126) for f, r in COMPARISONS]
        P(md_table(pd.DataFrame(rows)) + "\n")
    summary = []
    for h in HORIZONS:
        r = compare(tables[h], "HAR + VIX + HMM prob", "HAR + VIX", n_boot, 63)
        summary.append({"horizon": h, "HAR + VIX + HMM prob vs HAR + VIX, dRMSE 95%": r["dRMSE 95%"], "RMSE": r["RMSE"],
                        "dQLIKE 95%": r["dQLIKE 95%"], "QLIKE": r["QLIKE"]})
    P("Summary, the regime-probability question at each horizon:\n")
    P(md_table(pd.DataFrame(summary)) + "\n")

    P("## (c) Nesting-noise check at the 21-day horizon\n")
    P("A standard-normal regressor with no information (seed 0) added to HAR + VIX and scored against HAR + VIX "
      "with the same bootstrap, beside the HMM probability's row from (a).\n")
    df = tables[21]
    rows = [compare(df, "HAR + VIX + noise", "HAR + VIX", n_boot, 63), compare(df, "HAR + VIX + HMM prob", "HAR + VIX", n_boot, 63)]
    P(md_table(pd.DataFrame(rows)) + "\n")
    noise_row, hmm_row = rows
    P(f"One line: on development data the pure-noise regressor gives {noise_row['dRMSE 95%']} ({noise_row['RMSE']}) "
      f"and the HMM probability {hmm_row['dRMSE 95%']} ({hmm_row['RMSE']}); a 'no difference' verdict for a nested "
      "regressor is what nesting alone produces when the added regressor carries nothing, so the HMM probability's "
      "verdict should be read against this noise row, not against zero.\n")
    P("## (b) K = 3 and 4 Student-t HMMs\n\nSeparate run: `examples/dev_k_states.py` writes "
      "`docs/DEV_K_STATES_2026-10.md` (Gaussian and Student-t fits with 20 starts, per-refit convergence, and the "
      "walk-forward forecasts of the three- and four-state models against the two-state model and HAR + VIX, "
      "same class as this file).\n")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="ascii")
    print("\n".join(f"h={s['horizon']}: {s['HAR + VIX + HMM prob vs HAR + VIX, dRMSE 95%']} {s['RMSE']}" for s in summary))
    print(f"noise: {noise_row['dRMSE 95%']} {noise_row['RMSE']}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
