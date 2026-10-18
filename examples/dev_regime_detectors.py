"""Alternative regime detectors in place of the HMM probability (stage S8 d).

development data only (S&P 500, 2005-2023), no holdout, not a claim.

Runs amendment A2 of ``docs/ML_REGIME_PROTOCOL_DRAFT.md`` (written and committed before any fit) and writes
``docs/DEV_REGIME_DETECTORS_2026-10.md``. The detectors (``regimes.detectors``: k-means 2 and 3, Gaussian
mixture 2 and 3, PELT change-point, spectral 2) are fitted on the training rows only, refit every 63 rows
after 756, applied forward without smoothing. Each detector's input replaces the HMM probability in F1
(F1[d] = F0 + the detector's input); OLS at h = 5, 21 and 63 and, at h = 21 only, the learner with the lowest
mean QLIKE on F0 at h = 21 in the S8 (b) and (c) caches. Every set at a horizon is fitted on the same rows
(the days where the HMM probability and every detector exist), so F0, F1 and F1n are refitted here on those
rows. Caches under ``docs/results/dev_regime_detectors/``::

    python -u examples/dev_regime_detectors.py --part ols        # detectors + OLS at 5, 21, 63
    python -u examples/dev_regime_detectors.py --part learner    # the S8 (b)/(c) winner at 21 (after the race)
    python -u examples/dev_regime_detectors.py --markdown-only

Data from the committed caches to 2023-12-31; a download attempt raises.
"""
from __future__ import annotations

import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "4")

import argparse  # noqa: E402
import datetime as dt  # noqa: E402
import sys  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from regimes.detectors import DETECTORS, persistence, rand_agreement, rolling_features, walk_forward_detector  # noqa: E402
from regimes.evaluate import walk_forward_oos  # noqa: E402
from regimes.forecast import forward_vol, qlike  # noqa: E402
from regimes.learners import walk_forward_learner  # noqa: E402
from regimes.recurrent import RECURRENT, walk_forward_recurrent  # noqa: E402

import dev_ml_race as race  # noqa: E402
import dev_ml_regime as dm  # noqa: E402
from posthoc_stats import git_head, md_table  # noqa: E402

CLASS = dm.CLASS
HORIZONS = (5, 21, 63)
LEARNER_H = 21
CACHE = ROOT / "docs" / "results" / "dev_regime_detectors"


def set_names() -> list[str]:
    return ["F0", "F1", "F1n"] + [f"F1[{d}]" for d in DETECTORS]


def cache_path(h: int, model: str, fset: str) -> Path:
    tag = fset.replace("[", "_").replace("]", "").replace(" ", "")
    return CACHE / f"h{h:03d}__{model.replace(' ', '_')}__{tag}.csv"


def signals(returns: pd.Series, ivs: pd.DataFrame) -> pd.DataFrame:
    """Every detector's forward signal and label, cached (``signals.csv``)."""
    p = CACHE / "signals.csv"
    if p.exists():
        return pd.read_csv(p, index_col=0, parse_dates=True)
    feats = rolling_features(returns, ivs["VIX"])
    cols = {}
    for d in DETECTORS:
        t = time.time()
        wf = walk_forward_detector(feats, d, min_train=756, step=63)
        cols[f"{d}|signal"], cols[f"{d}|label"] = wf["signal"], wf["label"]
        print(f"detector {d:<12} {len(wf)} days, {time.time() - t:.0f} s", flush=True)
    out = pd.DataFrame(cols)
    CACHE.mkdir(parents=True, exist_ok=True)
    out.to_csv(p, float_format="%.12g")
    return out


def sets_at(returns, ivs, noise, sig: pd.DataFrame, h: int) -> tuple[dict[str, pd.DataFrame], pd.Series]:
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=h)
    base = dm.feature_sets(returns, ivs, wf.high_vol_prob, noise)
    sig_rows = sig[[f"{d}|signal" for d in DETECTORS]].dropna().index
    rows = base["F1"].index.intersection(sig_rows)
    out = {k: base[k].loc[rows] for k in ("F0", "F1", "F1n")}
    for d in DETECTORS:
        out[f"F1[{d}]"] = base["F0"].loc[rows].join(sig[f"{d}|signal"].rename("regime"))
    return out, wf.high_vol_prob


def best_learner() -> str:
    """Lowest mean QLIKE on F0 at h = 21 over the S8 (b) and (c) forecasts, on their common rows."""
    fc = {k: v for k, v in race.all_forecasts(LEARNER_H).items() if k.endswith(" F0") and k != "ols F0"}
    missing = [k for k in RECURRENT if f"{k} F0" not in fc]
    if missing:
        raise RuntimeError(f"the race has no F0 fit at h=21 for {missing}; run dev_ml_race.py first (protocol A2)")
    target = forward_vol(dm.load()[0], LEARNER_H)
    df = pd.concat({"target": target, **fc}, axis=1, sort=True).dropna()
    y = df["target"].to_numpy()
    means = {k: float(qlike(df[k].to_numpy(), y).mean()) for k in fc}
    return min(means, key=means.get)[: -len(" F0")]


def schedule_shift(here: pd.Series, s8b: pd.Series) -> dict:
    """How far an F0 forecast fitted on this script's rows sits from the S8 (b) F0 forecast of the same model on
    their common rows (the detector rows start later, so the refit dates and the tuned penalty can move)."""
    j = pd.concat({"here": here, "s8b": s8b}, axis=1, sort=True).dropna()
    d = (j["here"] - j["s8b"]).abs()
    return {"common days": len(j), "first day here": str(here.index.min().date()),
            "first day S8 (b)": str(s8b.index.min().date()), "median abs diff": f"{d.median():.4f}",
            "99th pct abs diff": f"{d.quantile(0.99):.4f}", "max abs diff": f"{d.max():.4f}",
            "on": str(d.idxmax().date()), "days diff > 0.1": int((d > 0.1).sum())}


def verdicts_two_schedules(here: pd.DataFrame, s8b: pd.DataFrame) -> pd.DataFrame:
    """F1 vs F0 and F1n vs F0 for every (h, model) in both this script's vs_f0 rows and S8 (b) table (i), side by
    side, with whether either verdict differs between the two refit schedules."""
    name = {"F1": "F1 vs F0", "F1n": "F1n vs F0 (noise control)"}
    out = []
    for _, r in here[here["set"].isin(list(name))].iterrows():
        m = s8b[(s8b["h"] == r["h"]) & (s8b["learner"] == r["model"]) & (s8b["comparison"] == name[r["set"]])]
        if m.empty:
            continue
        b = m.iloc[0]
        out.append({"h": r["h"], "model": r["model"], "comparison": name[r["set"]],
                    "dRMSE S8 (b)": b["dRMSE 95%"], "RMSE S8 (b)": b["RMSE"],
                    "dRMSE here": r["dRMSE 95%"], "RMSE here": r["RMSE"],
                    "dQLIKE S8 (b)": b["dQLIKE 95%"], "QLIKE S8 (b)": b["QLIKE"],
                    "dQLIKE here": r["dQLIKE 95%"], "QLIKE here": r["QLIKE"],
                    "verdict moves": "yes" if (b["RMSE"], b["QLIKE"]) != (r["RMSE"], r["QLIKE"]) else "no"})
    return pd.DataFrame(out)


def fit(target, X, model: str, h: int) -> pd.Series:
    if model == "ols":
        return dm.fit_one(target, X, "ols", h)[0]
    if model in RECURRENT:
        return walk_forward_recurrent(target, X, model, horizon=h, step=63, min_rows=756, val=252).forecast
    return walk_forward_learner(target, X, model, horizon=h, step=63, min_rows=756, val=252).forecast


def run(returns, ivs, noise, part: str) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    sig = signals(returns, ivs)
    plan = [(h, "ols") for h in HORIZONS] if part == "ols" else [(LEARNER_H, best_learner())]
    if part == "learner":
        (CACHE / "learner.txt").write_text(plan[0][1] + "\n")
        print(f"learner at h=21 (lowest mean QLIKE on F0 in S8 b/c): {plan[0][1]}", flush=True)
    for h, model in plan:
        todo = [s for s in set_names() if not cache_path(h, model, s).exists()]
        if not todo:
            continue
        sets, _ = sets_at(returns, ivs, noise, sig, h)
        target = forward_vol(returns, h)
        for s in todo:
            t = time.time()
            f = fit(target, sets[s], model, h)
            f.rename("forecast").to_csv(cache_path(h, model, s), float_format="%.12g")
            print(f"h={h} {model:<14} {s:<20} {len(f)} forecasts, {time.time() - t:.0f} s", flush=True)


def markdown(returns, ivs, noise, n_boot: int) -> str:
    sig = signals(returns, ivs)
    learner = (CACHE / "learner.txt").read_text().strip() if (CACHE / "learner.txt").exists() else None
    out = [f"{CLASS}\n", "# Alternative regime detectors in place of the HMM, development data, October 2026\n",
           f"Class of every table in this file: **{CLASS}**. Written by `examples/dev_regime_detectors.py` at "
           f"{git_head()}, {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, {n_boot:,} bootstrap draws (seed 0). "
           "Design: amendment A2 of `docs/ML_REGIME_PROTOCOL_DRAFT.md`, committed before the first fit. Every detector is "
           "fitted on the training rows only and applied forward (`regimes.detectors`, causality test in "
           "`tests/test_detectors.py`). F1[d] = F0 + detector d's input in place of the HMM probability; F1 = the HMM; "
           "F1n = pure noise. Every set at a horizon is fitted on the same rows. Stage S8 (d) of the reopen.\n",
           f"Learner at h = 21: **{learner or 'not yet chosen (the race is not finished)'}**, the lowest mean QLIKE on "
           "F0 at h = 21 over the S8 (b) and (c) forecasts, chosen before any detector fit with it.\n"]
    rows = []
    for h, model in [(h, "ols") for h in HORIZONS] + ([(LEARNER_H, learner)] if learner else []):
        fc = {s: pd.read_csv(cache_path(h, model, s), index_col=0, parse_dates=True)["forecast"]
              for s in set_names() if cache_path(h, model, s).exists()}
        if "F0" not in fc:
            continue
        df = pd.concat({"target": forward_vol(returns, h), **fc}, axis=1, sort=True).dropna()
        y = df["target"].to_numpy()
        for s in fc:
            row = {"h": h, "model": model, "set": s, "days": len(df), "windows": len(df) // h,
                   "RMSE": f"{np.sqrt(((df[s] - df['target']) ** 2).mean()):.4f}",
                   "QLIKE": f"{qlike(df[s].to_numpy(), y).mean():.4f}"}
            if s != "F0":
                row.update(dm.cmp_row(df, s, "F0", h, n_boot))
            rows.append(row)
    out.append("## Each regime input against F0 (HAR + VIX inputs only)\n")
    out.append(f"Class: {CLASS}. Paired circular block bootstrap, block max(63, h); DM = HAC Diebold-Mariano, lag 20. "
               "The F1n row is the size of a gain that means nothing.\n")
    out.append(md_table(pd.DataFrame(rows).fillna("")) + "\n" if rows else "Not run.\n")
    if rows:
        pd.DataFrame(rows).to_csv(CACHE / "vs_f0.csv", index=False)
    shift = []
    for model in ["ols"] + ([learner] if learner and learner != "ols" else []):
        here, s8b = cache_path(LEARNER_H, model, "F0"), dm.cache_path(LEARNER_H, model, "F0")
        if here.exists() and s8b.exists():
            shift.append({"model": model, **schedule_shift(
                pd.read_csv(here, index_col=0, parse_dates=True)["forecast"],
                pd.read_csv(s8b, index_col=0, parse_dates=True)["forecast"])})
    if shift:
        out.append("## Refit-schedule sensitivity: F0 here against F0 in S8 (b), h = 21\n")
        out.append(f"Class: {CLASS}. The detector inputs need warm-up rows, so every set here starts later than in "
                   "S8 (b) and the refit dates move. Comparisons inside the table above are on one schedule and are "
                   "unaffected; this table says how much the F0 forecast itself depends on the schedule. A large "
                   "value means the learner's tuned penalty moved between the two schedules, not an error.\n")
        out.append(md_table(pd.DataFrame(shift)) + "\n")
    s8b_i = dm.CACHE / "decisive_i.csv"
    if rows and s8b_i.exists():
        two = verdicts_two_schedules(pd.DataFrame(rows).fillna(""), pd.read_csv(s8b_i))
        if not two.empty:
            out.append("## Do the HMM and noise verdicts depend on the refit schedule?\n")
            out.append(f"Class: {CLASS}. The same comparison (F1 or F1n against F0, same model, same horizon) on the "
                       "S8 (b) rows (`docs/results/dev_ml_regime/decisive_i.csv`) and on the later-starting detector "
                       "rows here. The two differ in first day, refit dates and, for a tuned learner, the chosen "
                       f"penalty. Verdicts that move: {int((two['verdict moves'] == 'yes').sum())} of {len(two)} rows.\n")
            out.append(md_table(two) + "\n")
    # descriptives on the h = 21 scored rows
    sets, prob = sets_at(returns, ivs, noise, sig, LEARNER_H)
    scored = sets["F0"].index[756 + LEARNER_H:]
    hmm_lab = (prob.reindex(scored) > 0.5).astype(float)
    desc = [{"detector": "HMM (prob > 0.5)", "share high": f"{hmm_lab.mean():.3f}",
             "persistence": f"{persistence(hmm_lab):.3f}", "adjusted Rand vs HMM": "1.000"}]
    for d in DETECTORS:
        lab = sig[f"{d}|label"].reindex(scored)
        hi = sig[f"{d}|signal"].reindex(scored)
        lab = (hi > 0.5).astype(float) if lab.isna().all() else lab   # change-point: its 0/1 flag is the label
        desc.append({"detector": d, "share high": f"{(hi > 0.5).mean():.3f}", "persistence": f"{persistence(lab):.3f}",
                     "adjusted Rand vs HMM": f"{rand_agreement(lab, hmm_lab):.3f}"})
    out.append("## Label persistence and agreement with the HMM (h = 21 scored rows)\n")
    out.append(f"Class: {CLASS}. Persistence = share of days with yesterday's label; *share high* = share of days the "
               "detector's input exceeds 0.5 (for the mixture, the posterior of the high-vol component); the adjusted "
               f"Rand index is against the HMM labels (high-vol probability above 0.5). {len(scored):,} days, "
               f"{scored.min().date()} to {scored.max().date()}.\n")
    out.append(md_table(pd.DataFrame(desc)) + "\n")
    return "\n".join(out) + "\n"


def main() -> None:
    global CACHE
    parser = argparse.ArgumentParser()
    parser.add_argument("--part", choices=("ols", "learner"), default="ols")
    parser.add_argument("--markdown-only", action="store_true")
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--out", default=str(ROOT / "docs" / "DEV_REGIME_DETECTORS_2026-10.md"))
    parser.add_argument("--cache", default=str(CACHE))
    args = parser.parse_args()
    CACHE = Path(args.cache)
    dm.block_network()
    returns, ivs = dm.load()
    noise = pd.Series(np.random.default_rng(0).standard_normal(len(returns)), index=returns.index)
    if not args.markdown_only:
        run(returns, ivs, noise, args.part)
    Path(args.out).write_text(markdown(returns, ivs, noise, args.n_boot), encoding="ascii")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
