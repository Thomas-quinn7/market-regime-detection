"""Summary note for the S8 development continuation (stage S8 e): what ran, the three decisive tables in
counts, and the protocol's findings with a descriptive follow-up.

development data only (S&P 500, 2005-2023), no holdout, not a claim.

Reads the tables the S8 scripts save (``docs/results/dev_ml_regime/decisive_*.csv``,
``docs/results/dev_ml_race/vs_ols.csv``, ``docs/results/dev_regime_detectors/vs_f0.csv``) and the forecast
caches; fits nothing. Writes ``docs/DEV_ML_2026-10.md``. Rerun whenever a part finishes::

    python -u examples/dev_ml_summary.py
"""
from __future__ import annotations

import datetime as dt
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from regimes.forecast import forward_vol  # noqa: E402

import dev_ml_race as race  # noqa: E402
import dev_ml_regime as dm  # noqa: E402
import dev_regime_detectors as drd  # noqa: E402
from posthoc_stats import git_head, md_table  # noqa: E402

CLASS = dm.CLASS
LOSSES = ("RMSE", "QLIKE")


def verdict_counts(df: pd.DataFrame, by: str) -> pd.DataFrame:
    """Per value of ``by``: the number of rows and of 'better', 'no difference', 'worse' per loss."""
    rows = []
    for key, g in df.groupby(by, sort=False):
        row = {by: key, "comparisons": len(g)}
        for loss in LOSSES:
            vc = g[loss].value_counts()
            row[f"{loss} better / no diff. / worse"] = (f"{vc.get('better', 0)} / {vc.get('no difference', 0)} / "
                                                         f"{vc.get('worse', 0)}")
        rows.append(row)
    return pd.DataFrame(rows)


def findings(table_i: pd.DataFrame) -> pd.DataFrame:
    """The protocol's reading of table (i): F1 'better' than F0 for a learner, loss and horizon while the
    noise control F1n is not 'better' for the same learner, loss and horizon."""
    out = []
    f1 = table_i[table_i["comparison"] == "F1 vs F0"]
    f1n = table_i[table_i["comparison"].str.startswith("F1n")].set_index(["h", "learner"])
    for _, r in f1.iterrows():
        for loss in LOSSES:
            noise = f1n.loc[(r["h"], r["learner"]), loss]
            if r[loss] == "better" and noise != "better":
                out.append({"h": r["h"], "learner": r["learner"], "loss": loss,
                            "F1 vs F0": r[f"d{loss} 95%"], "F1n vs F0": f1n.loc[(r["h"], r["learner"]), f"d{loss} 95%"]})
    return pd.DataFrame(out)


def follow_up(returns: pd.Series, h: int, learner: str, n_boot: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Descriptive: the learner's F1 and F0 against OLS on F0, and the RMSE difference F1 - F0 by year."""
    fc = dm.load_forecasts(h, ("ols", learner), ("F0", "F1"))
    df = pd.concat({"target": forward_vol(returns, h), **{f"{k[0]} {k[1]}": v for k, v in fc.items()}},
                   axis=1, sort=True).dropna()
    vs = pd.DataFrame([{"comparison": f"{learner} {s} vs ols F0", **dm.cmp_row(df, f"{learner} {s}", "ols F0", h, n_boot)}
                       for s in ("F0", "F1")] +
                      [{"comparison": f"{learner} F1 vs ols F1", **dm.cmp_row(df, f"{learner} F1", "ols F1", h, n_boot)}])
    rmse = lambda c, g: np.sqrt(((g[c] - g["target"]) ** 2).mean())  # noqa: E731
    years = pd.DataFrame([{"year": y, "days": len(g), f"RMSE {learner} F0": f"{rmse(f'{learner} F0', g):.4f}",
                           f"RMSE {learner} F1": f"{rmse(f'{learner} F1', g):.4f}",
                           "F1 - F0": f"{rmse(f'{learner} F1', g) - rmse(f'{learner} F0', g):+.4f}"}
                          for y, g in df.groupby(df.index.year)])
    return vs, years


def status() -> pd.DataFrame:
    n_b = sum(len(dm.learners_at(h)) * len(dm.SETS) for h in dm.HORIZONS)
    have_b = sum(dm.cache_path(h, lr, fs).exists() for h in dm.HORIZONS for lr in dm.learners_at(h) for fs in dm.SETS)
    n_c = len(race.HORIZONS) * 2 * len(race.SETS)
    have_c = sum(race.cache_path(h, k, fs).exists() for h in race.HORIZONS for k in ("lstm", "gru") for fs in race.SETS)
    sets = drd.set_names()
    have_d = sum(drd.cache_path(h, "ols", s).exists() for h in drd.HORIZONS for s in sets)
    learner_file = drd.CACHE / "learner.txt"
    learner = learner_file.read_text().strip() if learner_file.exists() else None
    have_dl = sum(drd.cache_path(drd.LEARNER_H, learner, s).exists() for s in sets) if learner else 0
    return pd.DataFrame([
        {"part": "(a) horizons, docs/DEV_HORIZONS_2026-10.md", "fits": "-",
         "state": "done" if (ROOT / "docs" / "DEV_HORIZONS_2026-10.md").exists() else "not run"},
        {"part": "(b) learners x feature sets, docs/DEV_ML_REGIME_2026-10.md", "fits": f"{have_b} of {n_b}",
         "state": "done" if have_b == n_b else "partial"},
        {"part": "(c) LSTM and GRU race, docs/DEV_ML_RACE_2026-10.md", "fits": f"{have_c} of {n_c}",
         "state": "done" if have_c == n_c else "partial" if have_c else "not run"},
        {"part": "(d) detectors with OLS, docs/DEV_REGIME_DETECTORS_2026-10.md", "fits": f"{have_d} of {len(sets) * 3}",
         "state": "done" if have_d == len(sets) * 3 else "partial" if have_d else "not run"},
        {"part": f"(d) detectors with the h = 21 learner ({learner or 'not chosen yet'})",
         "fits": f"{have_dl} of {len(sets)}", "state": "done" if have_dl == len(sets) else "not run"},
    ])


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--out", default=str(ROOT / "docs" / "DEV_ML_2026-10.md"))
    args = parser.parse_args()
    dm.block_network()
    returns, _ = dm.load()
    out = [f"{CLASS}\n", "# Horizons and machine learning on the development data: summary, October 2026\n",
           f"Class of every table in this file: **{CLASS}**. Written by `examples/dev_ml_summary.py` at {git_head()}, "
           f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, from the tables the S8 scripts save; it fits nothing. "
           "Design: `docs/ML_REGIME_PROTOCOL_DRAFT.md` and its amendments A1 and A2, committed before the first fit. "
           "Stage S8 (e) of the reopen. Nothing here is a claim or enters a claim sentence.\n"]
    out.append("## What ran\n")
    out.append(md_table(status()) + "\n")
    p = dm.CACHE
    if (p / "decisive_i.csv").exists():
        t1, t2, t3 = (pd.read_csv(p / f"decisive_{k}.csv") for k in ("i", "ii", "iii"))
        out.append("## Decisive table (i) in counts: the regime probability in a flexible learner\n")
        out.append(f"Class: {CLASS}. Verdict counts over learners and horizons (5, 21, 63, 126), from "
                   "`docs/DEV_ML_REGIME_2026-10.md`.\n")
        out.append(md_table(verdict_counts(t1, "comparison")) + "\n")
        fnd = findings(t1)
        n_cmp = 2 * (t1["comparison"] == "F1 vs F0").sum()
        out.append(f"Protocol reading (F1 'better' than F0 while F1n is not, same learner, loss and horizon): "
                   f"{len(fnd)} of {n_cmp} comparisons.\n")
        if len(fnd):
            out.append(md_table(fnd) + "\n")
            for _, r in fnd.iterrows():
                vs, years = follow_up(returns, int(r["h"]), r["learner"], args.n_boot)
                out.append(f"### Follow-up, descriptive: {r['learner']} at h = {int(r['h'])}\n")
                out.append(f"Class: {CLASS}; post hoc, not in the protocol's decisive tables. The same forecasts "
                           "against HAR + VIX (OLS on F0) and against OLS with the HMM probability (OLS on F1), "
                           "and the RMSE difference F1 - F0 by calendar year of the scored day.\n")
                out.append(md_table(vs) + "\n")
                out.append(md_table(years) + "\n")
        out.append("## Decisive table (ii) in counts: each learner on F0 against HAR + VIX\n")
        out.append(f"Class: {CLASS}.\n")
        out.append(md_table(verdict_counts(t2, "learner")) + "\n")
        out.append("## Decisive table (iii) in counts: F2 (more lags, the VIX term structure) against F0\n")
        out.append(f"Class: {CLASS}. On the F2 rows (VIX9D starts 2011-01-03).\n")
        out.append(md_table(verdict_counts(t3, "h")) + "\n")
    rc = race.CACHE / "vs_ols.csv"
    out.append("## The race (c) in counts: every forecast against HAR + VIX\n")
    if rc.exists():
        t = pd.read_csv(rc)
        t["family"] = t["forecast"].str.rsplit(" ", n=1).str[0]
        out.append(f"Class: {CLASS}. From `docs/DEV_ML_RACE_2026-10.md` (the MCS and the tercile split are there).\n")
        out.append(md_table(verdict_counts(t, "family")) + "\n")
    else:
        out.append("Not yet scored (`examples/dev_ml_race.py --markdown-only` writes the table this reads).\n")
    dc = drd.CACHE / "vs_f0.csv"
    out.append("## The detectors (d) in counts: each regime input against F0\n")
    if dc.exists():
        t = pd.read_csv(dc)
        t = t[t["set"] != "F0"]
        out.append(f"Class: {CLASS}. From `docs/DEV_REGIME_DETECTORS_2026-10.md`.\n")
        out.append(md_table(verdict_counts(t, "set")) + "\n")
    else:
        out.append("Not yet scored (`examples/dev_regime_detectors.py --markdown-only` writes the table this reads).\n")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="ascii")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
