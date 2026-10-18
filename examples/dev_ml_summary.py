"""Summary note for the S8 development continuation (stage S8 e): what ran, the three decisive tables in
counts, and the protocol's findings with a descriptive follow-up, the reading against claim B and what it
would need to become a claim.

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


def n_verdict(df: pd.DataFrame | None, verdict: str) -> tuple[int, int]:
    """(count of ``verdict`` over both losses, number of comparisons over both losses); (0, 0) if absent."""
    if df is None or not len(df):
        return 0, 0
    return int(sum((df[loss] == verdict).sum() for loss in LOSSES)), 2 * len(df)


def weak(t2: pd.DataFrame, r: pd.Series) -> str:
    """Table (ii) verdict of the same learner, horizon and loss on F0 against HAR + VIX ('n/a' if absent)."""
    m = t2[(t2["h"] == r["h"]) & (t2["learner"] == r["learner"])]
    return m.iloc[0][r["loss"]] if len(m) else "n/a"


def reading(t1: pd.DataFrame, t2: pd.DataFrame, t3: pd.DataFrame, race_t: pd.DataFrame | None,
            det_t: pd.DataFrame | None) -> list[str]:
    """The honest reading against the paper's claim B, and what it would need to become a claim. Every
    number is counted from the decisive tables passed in; a part that has not run is said to be missing."""
    f1 = t1[t1["comparison"] == "F1 vs F0"]
    f1n = t1[t1["comparison"].str.startswith("F1n")]
    fnd = findings(t1)
    b1, n1 = n_verdict(f1, "better")
    w1, _ = n_verdict(f1, "worse")
    bn, nn = n_verdict(f1n, "better")
    b2, n2 = n_verdict(t2, "better")
    w2, _ = n_verdict(t2, "worse")
    b3, n3 = n_verdict(t3, "better")
    w3, _ = n_verdict(t3, "worse")
    better_h = ", ".join(str(h) for h in sorted(set(t3.loc[(t3[list(LOSSES)] == "better").any(axis=1), "h"])))
    out = ["## Reading against the paper's claims\n",
           f"Class: {CLASS}. Counts over both losses, from the tables above.\n",
           f"- Claim B (the regime probability adds nothing once the VIX is in) against the objection \"you only "
           f"tested a linear nest\": with the HMM probability, a flexible learner was 'better' than the same learner "
           f"without it in {b1} of {n1} comparisons and 'worse' in {w1}; the pure-noise regressor was 'better' in "
           f"{bn} of {nn}. The protocol reading (F1 better while F1n is not) holds in {len(fnd)} of {n1}"
           + "".join(f"; {r['learner']} at h = {int(r['h'])} ({r['loss']}) on F0 against HAR + VIX is "
                     f"'{weak(t2, r)}'" for _, r in fnd.iterrows()) + ". "
           + ("On development data the objection does not overturn claim B: every protocol finding is in a "
              "learner that is itself worse than HAR + VIX at that horizon and loss.\n"
              if all(weak(t2, r) == "worse" for _, r in fnd.iterrows()) else
              "At least one protocol finding is in a learner that is not worse than HAR + VIX; claim B needs "
              "the closer look in the follow-up.\n"),
           (f"- No learner on F0 beats HAR + VIX: 'better' in {b2} of {n2} comparisons, 'worse' in {w2}.\n"
            if b2 == 0 else
            f"- Learners on F0 against HAR + VIX: 'better' in {b2} of {n2} comparisons, 'worse' in {w2}.\n"),
           f"- More lags and the VIX term structure (F2 vs F0): 'better' in {b3} of {n3}, 'worse' in {w3}; 'better' "
           f"at h = {better_h or 'none'} (table (iii)).\n"]
    rnn = race_t[race_t["forecast"].str.match(r"(lstm|gru) ")] if race_t is not None else None
    if rnn is not None and len(rnn):
        br, nr = n_verdict(rnn, "better")
        wr, _ = n_verdict(rnn, "worse")
        out.append(f"- The race (c): an LSTM or GRU forecast was 'better' than HAR + VIX in {br} of {nr} "
                   f"comparisons and 'worse' in {wr}.\n")
    else:
        out.append("- The race (c): not scored when this file was written; no reading.\n")
    if det_t is not None and len(det_t):
        alt = det_t[~det_t["set"].isin(["F0", "F1", "F1n"])]
        bd, nd = n_verdict(alt, "better")
        wd, _ = n_verdict(alt, "worse")
        out.append(f"- Other regime detectors (d) in place of the HMM probability: 'better' than F0 in {bd} of {nd} "
                   f"comparisons, 'worse' in {wd}." + (" The null is not specific to the HMM." if bd == 0 else "") + "\n")
        sc = drd.CACHE / "schedule_check.csv"
        both = pd.concat([det_t] + ([pd.read_csv(sc)] if sc.exists() else []), ignore_index=True)
        two = drd.verdicts_two_schedules(both, t1) if {"h", "model"} <= set(both.columns) else pd.DataFrame()
        if len(two):
            hmm = two[two["comparison"] == "F1 vs F0"]
            mv = two[two["verdict moves"] == "yes"]
            out.append(f"- Refit schedule: the same F1 and F1n comparisons on the later-starting detector rows move "
                       f"{len(mv)} of {len(two)} verdicts against S8 (b)"
                       + "".join(f"; {r['comparison']}, {r['model']} at h = {int(r['h'])}" for _, r in mv.iterrows())
                       + f". HMM rows that move: {int((hmm['verdict moves'] == 'yes').sum())} of {len(hmm)} "
                       "(`docs/DEV_REGIME_DETECTORS_2026-10.md`, schedule table).\n")
    else:
        out.append("- The detectors (d): not scored when this file was written; no reading.\n")
    out.append("Multiplicity: none of these counts is corrected; at a 2.5% one-sided rate per comparison about "
               f"{0.025 * n1:.1f} 'better' verdicts in {n1} are expected by chance alone, which is what the noise "
               "row shows.\n")
    out.append("## What this would need to become a claim\n")
    out.append("All of the above is one series (the S&P 500), development years the paper already used to choose "
               "its models, and an uncorrected count over many learners, horizons and losses. To become a claim "
               "it would need: (1) a protocol frozen and committed before any new data is opened, naming one "
               "learner, one feature set, one horizon and one loss as primary, with its family of secondary "
               "comparisons and their correction; (2) the January 2027 holdout (Thomas's decision) on data no "
               "S8 fit has seen; (3) the run reproduced byte for byte from the frozen script. Until then it is a "
               "development note: it answers a referee's objection, it adds no evidence of its own.\n")
    return out


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
        wk = race.CACHE / "worse_in_mcs.csv"
        if wk.exists():
            w = pd.read_csv(wk)
            out.append(f"Of the {int(w['worse than HAR + VIX'].sum())} forecast-loss pairs 'worse' than HAR + VIX above, the "
                       f"10% MCS keeps {int(w['of which in the MCS'].sum())} (T_max compares each forecast with the "
                       "average of the set, not with HAR + VIX; table in `docs/DEV_ML_RACE_2026-10.md`). Membership of "
                       "the MCS is not read as parity with HAR + VIX anywhere in this summary.\n")
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
    if (p / "decisive_i.csv").exists():
        out += reading(t1, t2, t3, pd.read_csv(rc) if rc.exists() else None, pd.read_csv(dc) if dc.exists() else None)
    Path(args.out).write_text("\n".join(out) + "\n", encoding="ascii")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
