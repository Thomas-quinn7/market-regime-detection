"""The best-forecaster race: every S8 (b) learner plus an LSTM and a GRU (stage S8 c).

development data only (S&P 500, 2005-2023), no holdout, not a claim.

Runs amendment A1 of ``docs/ML_REGIME_PROTOCOL_DRAFT.md`` (written and committed before any fit) and writes
``docs/DEV_ML_RACE_2026-10.md``. The recurrent fits (``regimes.recurrent``: LSTM and GRU on the last 66 days
of F0, F1 or F1n, horizons 5, 21 and 63) are cached per (horizon, learner, set) under
``docs/results/dev_ml_race/``; the other learners' forecasts are read from the S8 (b) cache
``docs/results/dev_ml_regime/`` (``examples/dev_ml_regime.py``), never refitted here. Every forecast is scored
on the F1 rows against OLS on F0 (HAR + VIX), with a model confidence set over everything and the split by
tercile of the training-window VIX. The fits can be split across processes and resumed::

    python -u examples/dev_ml_race.py --horizons 21,5,63 --kinds lstm
    python -u examples/dev_ml_race.py --markdown-only

``--stop-at HH:MM`` (UTC) starts no new fit after that time, so a job can end before the box's other lanes.
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

from regimes.evaluate import walk_forward_oos  # noqa: E402
from regimes.forecast import forward_vol, qlike  # noqa: E402
from regimes.posthoc import mcs  # noqa: E402
from regimes.recurrent import RECURRENT, walk_forward_recurrent  # noqa: E402

import dev_ml_regime as dm  # noqa: E402
from posthoc_stats import git_head, md_table  # noqa: E402

CLASS = dm.CLASS
HORIZONS = (5, 21, 63)
SETS = ("F0", "F1", "F1n")
CACHE = ROOT / "docs" / "results" / "dev_ml_race"


def cache_path(h: int, kind: str, fset: str) -> Path:
    return CACHE / f"h{h:03d}__{kind}__{fset}.csv"


def run(returns: pd.Series, ivs: pd.DataFrame, noise: pd.Series, h: int, kinds, stop_at: dt.datetime | None) -> bool:
    """Fit every missing (kind, set) at horizon h. Returns False if stopped by ``stop_at``."""
    CACHE.mkdir(parents=True, exist_ok=True)
    todo = [(k, fs) for k in kinds for fs in SETS if not cache_path(h, k, fs).exists()]
    if not todo:
        print(f"h={h}: every recurrent fit cached", flush=True)
        return True
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=h)
    sets = dm.feature_sets(returns, ivs, wf.high_vol_prob, noise)
    target = forward_vol(returns, h)
    for kind, fset in todo:
        if stop_at is not None and dt.datetime.now(dt.timezone.utc) >= stop_at:
            print(f"stop-at {stop_at:%H:%MZ} reached; h={h} {kind} {fset} not started", flush=True)
            return False
        t1 = time.time()
        r = walk_forward_recurrent(target, sets[fset], kind, horizon=h, step=63, min_rows=756, val=252)
        r.forecast.rename("forecast").to_csv(cache_path(h, kind, fset), float_format="%.12g")
        r.chosen.to_csv(cache_path(h, kind, fset).with_suffix(".chosen.csv"), index=False, float_format="%.12g")
        print(f"h={h} {kind:<5} {fset:<4} {len(r.forecast)} forecasts, {r.n_refits} refits, "
              f"{time.time() - t1:.0f} s", flush=True)
    return True


# ----------------------------------------------------------------------------------------------
# Markdown


def all_forecasts(h: int) -> dict[str, pd.Series]:
    out = {}
    for (lr, fs), s in dm.load_forecasts(h, dm.learners_at(h), SETS).items():
        out[f"{lr} {fs}"] = s
    for kind in RECURRENT:
        for fs in SETS:
            p = cache_path(h, kind, fs)
            if p.exists():
                out[f"{kind} {fs}"] = pd.read_csv(p, index_col=0, parse_dates=True)["forecast"]
    return out


def f1_rows(returns: pd.Series, ivs: pd.DataFrame, h: int) -> pd.DatetimeIndex:
    """The F1 rows at horizon h without refitting the HMM: the F0 rows from 756 + h rows before the first
    S8 (b) ridge forecast on F0. Checked against the refit dates in that fit's chosen-parameter file."""
    f0 = dm.feature_sets(returns, ivs, pd.Series(0.5, index=returns.index), pd.Series(0.0, index=returns.index))["F0"]
    first = pd.read_csv(dm.cache_path(h, "ridge", "F0"), index_col=0, parse_dates=True).index[0]
    rows = f0.index[f0.index.get_loc(first) - (756 + h):]
    refits = pd.to_datetime(pd.read_csv(dm.cache_path(h, "ridge", "F0").with_suffix(".chosen.csv"))["date"])
    if not rows[756 + h::63].equals(pd.DatetimeIndex(refits)):
        raise RuntimeError(f"h={h}: reconstructed F1 rows do not give the S8 (b) refit dates")
    return rows


def terciles(index: pd.DatetimeIndex, f1_rows: pd.DatetimeIndex, vix: pd.Series, h: int) -> pd.Series:
    """Low / middle / high by the 33rd and 67th percentiles of the VIX over each refit's training rows
    (the F1 rows before refit position i, embargoed by h), applied to the 63 rows that refit forecasts."""
    lab = pd.Series(index=f1_rows, dtype=object)
    v = vix.reindex(f1_rows).to_numpy()
    for i in range(756 + h, len(f1_rows), 63):
        lo, hi = np.percentile(v[: i - h], [100 / 3, 200 / 3])
        blk = v[i:i + 63]
        lab.iloc[i:i + 63] = np.where(blk <= lo, "low", np.where(blk <= hi, "middle", "high"))
    return lab.reindex(index)


def worse_in_mcs(vs_ols: pd.DataFrame, in_set: dict) -> pd.DataFrame:
    """Per horizon and loss: forecasts 'worse' than HAR + VIX in the paired test that the MCS still keeps.

    ``in_set`` maps (h, loss, forecast) to the MCS membership; ``loss`` is "RMSE" or "QLIKE" (the MCS on
    squared error stands for RMSE). The two tests ask different questions: the pair is one forecast against
    HAR + VIX, the T_max MCS each forecast against the average of the set, with a critical value for the
    largest of all the statistics, so a forecast can lose its pair and survive the set.
    """
    rows = []
    for h, loss in sorted({(k[0], k[1]) for k in in_set}):
        sub = vs_ols[vs_ols["h"] == h]
        worse = [f for f, v in zip(sub["forecast"], sub[loss]) if v == "worse"]
        kept = [f for f in worse if in_set.get((h, loss, f), False)]
        rows.append({"h": h, "loss": loss, "worse than HAR + VIX": len(worse), "of which in the MCS": len(kept),
                     "forecasts": ", ".join(kept) if kept else "-"})
    return pd.DataFrame(rows)


def markdown(returns: pd.Series, ivs: pd.DataFrame, horizons,
             n_boot: int) -> tuple[str, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    out = [f"{CLASS}\n", "# The best-forecaster race, development data, October 2026\n",
           "**Known limit, first:** one series (the S&P 500), about 3,200 scored days at 21 days (about 150 "
           "non-overlapping windows). A gain over HAR + VIX is expected to be small and concentrated in the high-vol "
           "tercile; a race won by a few tenths of a percent of RMSE is a description of this sample, not a finding.\n",
           f"Class of every table in this file: **{CLASS}**. Written by `examples/dev_ml_race.py` at {git_head()}, "
           f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, {n_boot:,} bootstrap draws (seed 0). Design: amendment "
           "A1 of `docs/ML_REGIME_PROTOCOL_DRAFT.md`, committed before the first fit. The LSTM and GRU forecasts are in "
           "`docs/results/dev_ml_race/`; every other forecast is read from the S8 (b) cache `docs/results/dev_ml_regime/` "
           "and scored here on the same rows. The recurrent learners need 65 earlier days as input, so their first 65 F1 "
           "rows serve only as inputs and each training window is 65 rows shorter than the other learners'; the scored "
           "rows are the same. Stage S8 (c) of the reopen.\n",
           "Every comparison is against OLS on F0 (HAR + VIX): paired circular block bootstrap, block max(63, h), and "
           "HAC Diebold-Mariano, lag 20. The model confidence set (Hansen, Lunde and Nason 2011, T_max, 10%) is over "
           "every forecast present at the horizon, on squared error (the RMSE loss) and on QLIKE; it is post hoc and "
           "descriptive. Nothing here is a claim.\n"]
    vs_ols, tert_rows, in_set = [], [], {}
    for h in horizons:
        fc = all_forecasts(h)
        if "ols F0" not in fc:
            out.append(f"## Horizon {h}\n\nNot run (no S8 (b) forecasts at this horizon).\n")
            continue
        target = forward_vol(returns, h)
        df = pd.concat({"target": target, **fc}, axis=1, sort=True).dropna()
        cols = [c for c in df.columns if c != "target"]
        y = df["target"].to_numpy()
        missing = [f"{k} {fs}" for k in RECURRENT for fs in SETS if f"{k} {fs}" not in fc]
        out.append(f"## Horizon {h}\n")
        out.append(f"Scored days {len(df):,}, {df.index.min().date()} to {df.index.max().date()}, windows {len(df) // h}"
                   + (f"; not yet fitted: {', '.join(missing)}" if missing else "") + ".\n")
        se = np.column_stack([(df[c].to_numpy() - y) ** 2 for c in cols])
        ql = np.column_stack([qlike(df[c].to_numpy(), y) for c in cols])
        m_se = mcs(se, alpha=0.10, block=max(63, h), n_boot=n_boot)
        m_ql = mcs(ql, alpha=0.10, block=max(63, h), n_boot=n_boot)
        table = pd.DataFrame({"forecast": cols, "RMSE": [f"{np.sqrt(se[:, k].mean()):.4f}" for k in range(len(cols))],
                              "QLIKE": [f"{ql[:, k].mean():.4f}" for k in range(len(cols))],
                              "MCS p (sq. error)": [f"{p:.3f}" for p in m_se["p_value"]],
                              "MCS p (QLIKE)": [f"{p:.3f}" for p in m_ql["p_value"]]})
        out.append(md_table(table.sort_values("QLIKE", key=lambda s: s.astype(float))) + "\n")
        out.append(f"In the 10% MCS on squared error: {', '.join(c for c, k in zip(cols, m_se['in_set']) if k)}. "
                   f"On QLIKE: {', '.join(c for c, k in zip(cols, m_ql['in_set']) if k)}.\n")
        for c, k_se, k_ql in zip(cols, m_se["in_set"], m_ql["in_set"]):
            in_set[(h, "RMSE", c)], in_set[(h, "QLIKE", c)] = bool(k_se), bool(k_ql)
        for c in cols:
            if c != "ols F0":
                vs_ols.append({"h": h, "forecast": c, "windows": len(df) // h, **dm.cmp_row(df, c, "ols F0", h, n_boot)})
        lab = terciles(df.index, f1_rows(returns, ivs, h), ivs["VIX"], h)
        for t in ("low", "middle", "high"):
            sub = df[lab == t]
            for c in cols:
                if c == "ols F0":
                    continue
                row = {"h": h, "tercile": t, "forecast": c, "days": len(sub),
                       "RMSE of forecast": f"{np.sqrt(((sub[c] - sub['target']) ** 2).mean()):.4f}",
                       "RMSE HAR + VIX": f"{np.sqrt(((sub['ols F0'] - sub['target']) ** 2).mean()):.4f}",
                       **dm.cmp_row(sub, c, "ols F0", h, n_boot)}
                tert_rows.append(row)
    out.append("## Every forecast against HAR + VIX (OLS on F0)\n")
    out.append(f"Class: {CLASS}.\n")
    out.append(md_table(pd.DataFrame(vs_ols)) + "\n" if vs_ols else "Not run.\n")
    kept = worse_in_mcs(pd.DataFrame(vs_ols), in_set) if vs_ols else pd.DataFrame()
    if vs_ols:
        out.append("## Worse than HAR + VIX in the pair, yet in the MCS\n")
        out.append(f"Class: {CLASS}. The paired interval asks whether one forecast differs from HAR + VIX; the T_max "
                   "MCS asks whether a forecast is worse than the average of every forecast in the set, against a "
                   "critical value for the largest of all those statistics. With about 20 forecasts that bar is high, "
                   "so a forecast can lose to HAR + VIX and still stay in the set. Membership of the MCS is therefore "
                   "not evidence that a forecast matches HAR + VIX; the paired verdict is the comparison that answers "
                   "that question.\n")
        out.append(md_table(kept) + "\n")
    tert = pd.DataFrame(tert_rows)
    out.append("## By tercile of the training-window VIX: each learner on F0 against HAR + VIX\n")
    out.append(f"Class: {CLASS}. The tercile cut points are the 33rd and 67th percentiles of the VIX over each refit's "
               "training rows; the bootstrap runs over the tercile's days joined end to end, so its blocks cross the gaps "
               "between them (an approximation, stated). Every forecast and feature set: "
               "`docs/results/dev_ml_race/terciles.csv`.\n")
    if len(tert):
        out.append(md_table(tert[tert["forecast"].str.endswith(" F0")]) + "\n")
    else:
        out.append("Not run.\n")
    return "\n".join(out) + "\n", tert, pd.DataFrame(vs_ols), kept


def main() -> None:
    global CACHE
    parser = argparse.ArgumentParser()
    parser.add_argument("--horizons", default="21,5,63")
    parser.add_argument("--kinds", default=",".join(RECURRENT))
    parser.add_argument("--markdown-only", action="store_true")
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--stop-at", default=None, help="UTC HH:MM today after which no new fit starts")
    parser.add_argument("--out", default=str(ROOT / "docs" / "DEV_ML_RACE_2026-10.md"))
    parser.add_argument("--cache", default=str(CACHE))
    args = parser.parse_args()
    CACHE = Path(args.cache)
    dm.block_network()
    returns, ivs = dm.load()
    noise = pd.Series(np.random.default_rng(0).standard_normal(len(returns)), index=returns.index)
    if not args.markdown_only:
        stop_at = None
        if args.stop_at:
            hh, mm = (int(x) for x in args.stop_at.split(":"))
            stop_at = dt.datetime.now(dt.timezone.utc).replace(hour=hh, minute=mm, second=0, microsecond=0)
        kinds = args.kinds.split(",")
        for h in (int(x) for x in args.horizons.split(",")):
            if not run(returns, ivs, noise, h, kinds, stop_at):
                return
        return
    text, tert, vs_ols, kept = markdown(returns, ivs, HORIZONS, args.n_boot)
    CACHE.mkdir(parents=True, exist_ok=True)
    tert.to_csv(CACHE / "terciles.csv", index=False)
    vs_ols.to_csv(CACHE / "vs_ols.csv", index=False)
    kept.to_csv(CACHE / "worse_in_mcs.csv", index=False)
    Path(args.out).write_text(text, encoding="ascii")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
