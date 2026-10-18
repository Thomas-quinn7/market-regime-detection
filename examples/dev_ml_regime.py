"""Does a flexible learner find regime information the linear nest misses? (stage S8 b)

development data only (S&P 500, 2005-2023), no holdout, not a claim.

Runs the design fixed in ``docs/ML_REGIME_PROTOCOL_DRAFT.md`` (committed before the first fit) and writes
``docs/DEV_ML_REGIME_2026-10.md``, with per-day forecasts and the per-refit chosen hyperparameters under
``docs/results/dev_ml_regime/``. Learners and grids: ``regimes.learners``. Feature sets: F0 = log HAR +
log VIX; F1 = F0 + walk-forward HMM high-vol probability; F1n = F0 + pure noise (seed 0); F2 = F0 +
log |r| lags 1-21 + log RMS 44 and 66 + log VIX9D/VIX, VIX3M/VIX, VIX6M/VIX. Horizons 5, 21, 63 (every
learner) and 126 (linear and tree learners). Every fit is cached by (horizon, learner, set), so the run
can be split across processes and resumed::

    python -u examples/dev_ml_regime.py --horizons 5,126        # one process
    python -u examples/dev_ml_regime.py --horizons 21,63        # another
    python -u examples/dev_ml_regime.py --markdown-only         # rebuild the markdown from the caches

Data from the committed caches to 2023-12-31; a download attempt raises.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "4")

import argparse  # noqa: E402
import datetime as dt  # noqa: E402
import json  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
import types  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from regimes.data import load_index_returns, load_vol_indices  # noqa: E402
from regimes.evaluate import walk_forward_oos  # noqa: E402
from regimes.forecast import forward_vol, har_features, qlike, walk_forward_regression  # noqa: E402
from regimes.learners import LEARNERS, walk_forward_learner  # noqa: E402
from regimes.posthoc import hac_dm, mcs, paired_interval  # noqa: E402

from posthoc_stats import git_head, md_table, verdict  # noqa: E402

START, END = "2005-01-01", "2023-12-31"
CLASS = "development data only (S&P 500, 2005-2023), no holdout, not a claim"
HORIZONS = (5, 21, 63, 126)
LONG_LEARNERS = ("ridge", "lasso", "random forest", "lightgbm")   # h = 126: linear and tree learners only
CACHE = ROOT / "docs" / "results" / "dev_ml_regime"
SETS = ("F0", "F1", "F1n", "F0@F2", "F2")


def block_network() -> None:
    def no_network(*a, **k):
        raise RuntimeError("dev_ml_regime.py reads only the data caches; a download was attempted")
    sys.modules["yfinance"] = types.SimpleNamespace(download=no_network)


def load() -> tuple[pd.Series, pd.DataFrame]:
    returns = load_index_returns(start=START, end=END)
    ivs = load_vol_indices(("VIX", "VIX9D", "VIX3M", "VIX6M"), START, END)
    common = returns.index.intersection(ivs.index[ivs["VIX"].notna()])
    return returns.loc[common], ivs.reindex(common)


def feature_sets(returns: pd.Series, ivs: pd.DataFrame, prob: pd.Series, noise: pd.Series) -> dict[str, pd.DataFrame]:
    """F0, F1, F1n on the F1 rows; F0@F2 and F2 on the F2 rows (protocol, "Rows")."""
    log_har = np.log(har_features(returns).clip(lower=1e-3))
    log_vix = np.log(ivs["VIX"] / np.sqrt(252)).rename("vix")
    f0 = log_har.join(log_vix)
    f1 = f0.join(prob.rename("hmm_prob"))
    rows1 = f1.dropna().index
    absr = np.log(returns.abs().clip(lower=1e-3))
    extra = pd.DataFrame({f"absr_lag{k}": absr.shift(k) for k in range(1, 22)})
    sq = returns.astype(float) ** 2
    extra["rms_44"] = np.log(np.sqrt(sq.rolling(44).mean()).clip(lower=1e-3))
    extra["rms_66"] = np.log(np.sqrt(sq.rolling(66).mean()).clip(lower=1e-3))
    for name in ("VIX9D", "VIX3M", "VIX6M"):
        extra[f"slope_{name}"] = np.log(ivs[name] / ivs["VIX"])
    f2 = f0.join(extra)
    rows2 = f2.dropna().index
    return {"F0": f0.loc[rows1], "F1": f1.loc[rows1], "F1n": f0.join(noise.rename("noise")).loc[rows1],
            "F0@F2": f0.loc[rows2], "F2": f2.loc[rows2]}


def learners_at(h: int) -> tuple[str, ...]:
    return ("ols",) + (LONG_LEARNERS if h == 126 else LEARNERS)


def cache_path(h: int, learner: str, fset: str) -> Path:
    return CACHE / f"h{h:03d}__{learner.replace(' ', '_')}__{fset.replace('@', '_at_')}.csv"


def fit_one(target: pd.Series, X: pd.DataFrame, learner: str, h: int) -> tuple[pd.Series, pd.DataFrame]:
    if learner == "ols":
        r = walk_forward_regression(target, X, horizon=h, step=63, min_rows=756, log_target=True)
        return r.forecast, r.coefs.reset_index(names="date")
    r = walk_forward_learner(target, X, learner, horizon=h, step=63, min_rows=756, val=252)
    return r.forecast, r.chosen


def run_horizon(returns: pd.Series, ivs: pd.DataFrame, noise: pd.Series, h: int) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [(lr, fs) for lr in learners_at(h) for fs in SETS if not cache_path(h, lr, fs).exists()]
    if not todo:
        print(f"h={h}: every fit cached", flush=True)
        return
    t0 = time.time()
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=h)
    conv = None if wf.convergence is None else int(wf.convergence["best_converged"].sum())
    (CACHE / f"h{h:03d}__hmm.json").write_text(json.dumps({"n_refits": wf.n_refits, "converged": conv}))
    target = forward_vol(returns, h)
    sets = feature_sets(returns, ivs, wf.high_vol_prob, noise)
    print(f"h={h}: HMM {time.time() - t0:.0f} s, refits {wf.n_refits}, converged {conv}", flush=True)
    for learner, fset in todo:
        t1 = time.time()
        fc, chosen = fit_one(target, sets[fset], learner, h)
        fc.rename("forecast").to_csv(cache_path(h, learner, fset), float_format="%.12g")
        chosen.to_csv(cache_path(h, learner, fset).with_suffix(".chosen.csv"), index=False, float_format="%.12g")
        print(f"h={h} {learner:<14} {fset:<6} {len(fc)} forecasts, {time.time() - t1:.0f} s", flush=True)


# ----------------------------------------------------------------------------------------------
# Markdown


def load_forecasts(h: int, learners, fsets) -> dict[tuple[str, str], pd.Series]:
    out = {}
    for lr in learners:
        for fs in fsets:
            p = cache_path(h, lr, fs)
            if p.exists():
                out[(lr, fs)] = pd.read_csv(p, index_col=0, parse_dates=True)["forecast"]
    return out


def cmp_row(df: pd.DataFrame, a: str, b: str, h: int, n_boot: int) -> dict:
    y = df["target"].to_numpy()
    ea, eb = df[a].to_numpy() - y, df[b].to_numpy() - y
    qa, qb = qlike(df[a].to_numpy(), y), qlike(df[b].to_numpy(), y)
    blk = max(63, h)
    r_lo, r_hi = paired_interval(ea, eb, statistic="rmse", block=blk, n_boot=n_boot)
    q_lo, q_hi = paired_interval(qa, qb, statistic="mean", block=blk, n_boot=n_boot)
    return {"dRMSE 95%": f"{r_lo:+.3f} to {r_hi:+.3f}", "RMSE": verdict(r_lo, r_hi),
            "DM p (MSE)": f"{hac_dm(ea ** 2, eb ** 2, lag=20)['p']:.3f}",
            "dQLIKE 95%": f"{q_lo:+.3f} to {q_hi:+.3f}", "QLIKE": verdict(q_lo, q_hi),
            "DM p (QLIKE)": f"{hac_dm(qa, qb, lag=20)['p']:.3f}"}


def markdown(returns: pd.Series, horizons, n_boot: int) -> str:
    out = [f"{CLASS}\n", "# Machine learning and the regime probability, development data, October 2026\n",
           f"Class of every table in this file: **{CLASS}**. Written by `examples/dev_ml_regime.py` at {git_head()}, "
           f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, {n_boot:,} bootstrap draws (seed 0). Design, learners, "
           "grids and the reading rule: `docs/ML_REGIME_PROTOCOL_DRAFT.md`, committed before the first fit. Forecasts "
           "and the per-refit chosen hyperparameters: `docs/results/dev_ml_regime/`. Stage S8 (b) of the reopen.\n",
           "Intervals: paired circular block bootstrap, block max(63, h); DM = HAC Diebold-Mariano, lag 20, two-sided "
           "p. *windows* = scored days / h. Nothing here is a claim.\n"]
    decisive = {"i": [], "ii": [], "iii": []}
    for h in horizons:
        lrs = learners_at(h)
        fc = load_forecasts(h, lrs, SETS)
        if not fc:
            out.append(f"## Horizon {h}\n\nNot run.\n")
            continue
        target = forward_vol(returns, h)
        meta = json.loads((CACHE / f"h{h:03d}__hmm.json").read_text())
        main = {f"{lr} {fs}": fc[(lr, fs)] for lr in lrs for fs in ("F0", "F1", "F1n") if (lr, fs) in fc}
        df = pd.concat({"target": target, **main}, axis=1, sort=True).dropna()
        out.append(f"## Horizon {h}\n")
        out.append(f"F1 rows: scored days {len(df):,}, {df.index.min().date()} to {df.index.max().date()}, windows "
                   f"{len(df) // h}; HMM refits {meta['n_refits']}, converged {meta['converged']}.\n")
        y = df["target"].to_numpy()
        out.append(md_table(pd.DataFrame([{"forecast": c, "RMSE": f"{np.sqrt(((df[c] - df['target']) ** 2).mean()):.4f}",
                                           "QLIKE": f"{qlike(df[c].to_numpy(), y).mean():.4f}"}
                                          for c in df.columns if c != "target"])) + "\n")
        for lr in lrs:
            if f"{lr} F1" in df and f"{lr} F0" in df:
                decisive["i"].append({"h": h, "learner": lr, "comparison": "F1 vs F0", "windows": len(df) // h,
                                      **cmp_row(df, f"{lr} F1", f"{lr} F0", h, n_boot)})
                decisive["i"].append({"h": h, "learner": lr, "comparison": "F1n vs F0 (noise control)",
                                      "windows": len(df) // h, **cmp_row(df, f"{lr} F1n", f"{lr} F0", h, n_boot)})
            if lr != "ols" and f"{lr} F0" in df:
                decisive["ii"].append({"h": h, "learner": lr, "comparison": "F0 vs OLS F0 (HAR + VIX)",
                                       "windows": len(df) // h, **cmp_row(df, f"{lr} F0", "ols F0", h, n_boot)})
        # MCS over every learner-feature pair on the F1 rows (post hoc, descriptive)
        cols = [c for c in df.columns if c != "target"]
        res = mcs(np.column_stack([qlike(df[c].to_numpy(), y) for c in cols]), alpha=0.10, block=max(63, h),
                  n_boot=n_boot)
        keep = [cols[k] for k in np.flatnonzero(res["in_set"])]
        out.append(f"Model confidence set at 10% on QLIKE over the {len(cols)} learner-feature pairs (post hoc, "
                   f"descriptive): {', '.join(keep)}.\n")
        f2 = {f"{lr} {fs}": fc[(lr, fs)] for lr in lrs for fs in ("F0@F2", "F2") if (lr, fs) in fc}
        if f2:
            d2 = pd.concat({"target": target, **f2}, axis=1, sort=True).dropna()
            for lr in lrs:
                if f"{lr} F2" in d2 and f"{lr} F0@F2" in d2:
                    decisive["iii"].append({"h": h, "learner": lr, "comparison": "F2 vs F0 (F2 rows)",
                                            "windows": len(d2) // h, **cmp_row(d2, f"{lr} F2", f"{lr} F0@F2", h, n_boot)})
    out.append("## Decisive table (i): does the regime probability help a flexible learner?\n")
    out.append(f"Class: {CLASS}. Every learner F1 vs F0, with the noise control F1n vs F0 beside it.\n")
    out.append(md_table(pd.DataFrame(decisive["i"])) + "\n" if decisive["i"] else "Not run.\n")
    out.append("## Decisive table (ii): does the learner itself beat HAR + VIX?\n")
    out.append(f"Class: {CLASS}. Every learner on F0 vs OLS on F0.\n")
    out.append(md_table(pd.DataFrame(decisive["ii"])) + "\n" if decisive["ii"] else "Not run.\n")
    out.append("## Decisive table (iii): more information instead of a regime\n")
    out.append(f"Class: {CLASS}. F2 vs F0 per learner, on the F2 rows (VIX9D starts 2011-01-03).\n")
    out.append(md_table(pd.DataFrame(decisive["iii"])) + "\n" if decisive["iii"] else "Not run.\n")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizons", default=",".join(str(h) for h in HORIZONS))
    parser.add_argument("--markdown-only", action="store_true")
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--out", default=str(ROOT / "docs" / "DEV_ML_REGIME_2026-10.md"))
    args = parser.parse_args()
    block_network()
    returns, ivs = load()
    noise = pd.Series(np.random.default_rng(0).standard_normal(len(returns)), index=returns.index)
    horizons = [int(x) for x in args.horizons.split(",")]
    if not args.markdown_only:
        for h in horizons:
            run_horizon(returns, ivs, noise, h)
    Path(args.out).write_text(markdown(returns, HORIZONS if args.markdown_only else horizons, args.n_boot),
                              encoding="ascii")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
