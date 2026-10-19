"""Development-only benchmark form check: HAR + VIX with level features vs log features (S&P 500, to 2022-12-30).

development data only (S&P 500, to 2022-12-30), no holdout, not a claim.

Writes ``docs/DEV_BENCHMARK_FORM_2026-10.md``. Stage S9 of the reopen scope. Question: does any MR development
comparison change sign or significance when the HAR + VIX benchmark (and the HMM-augmented model beside it)
uses the log-feature form instead of the level-feature form? Two forms, both with a log target and the
lognormal mean correction of ``regimes.forecast.walk_forward_regression``:

- level form: HAR inputs (|r_t|, RMS 5 and 22 days) and VIX / sqrt(252) in levels;
- log form (Corsi log-HAR): the same inputs in logs. This is the form MR's frozen scripts use
  (``examples/vol_forecast_vix.py`` lines 104-132, ``examples/better_vol_models.py`` lines 93-117,
  ``examples/msgarch_credit.py`` lines 168-186).

The HMM high-vol probability and the noise regressor enter linearly in both forms. Design as S4a/S8a: expanding
OLS, refit every 63 rows after 756, embargo h, every set at a horizon fitted and scored on the same rows; paired
circular block bootstrap with block = max(63, h), 2,000 draws, seed 0; HAC Diebold-Mariano with lag max(20, h - 1)
on the QLIKE and squared-error differences. Horizons 1, 5, 21, 63. Two targets:

- A, MR's target: realised vol from daily S&P 500 returns over the next h days (at h = 1 that is |r_{t+1}|; the
  two zero-return days are dropped, as log(0) is undefined);
- B, the implied-horizon-vol study's target: ES 5-minute realised vol (``data/es_rv_5min.csv``, from
  2010-06-07), HAR inputs built from the same RV (``regimes.forecast.har_rv``).

Every input is clipped to <= 2022-12-30 at load, before any feature or target is built (the VRP equity holdout
starts 2023-01-01; tighter than rule 3). Data from the committed caches (a download attempt raises)::

    python -u examples/dev_benchmark_form.py [--n-boot 2000] [--out docs/DEV_BENCHMARK_FORM_2026-10.md]
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

from regimes.data import DATA_DIR, load_index_returns, load_vix  # noqa: E402
from regimes.evaluate import walk_forward_oos  # noqa: E402
from regimes.forecast import forward_rv, forward_vol, har_features, har_rv, qlike, walk_forward_regression  # noqa: E402
from regimes.posthoc import hac_dm, paired_interval  # noqa: E402

from posthoc_stats import git_head, md_table, verdict  # noqa: E402

START, LOAD_END, CUT = "2005-01-01", "2023-12-31", "2022-12-30"
CLASS = "development data only (S&P 500, to 2022-12-30), no holdout, not a claim"
HORIZONS = (1, 5, 21, 63)
FORMS = ("level", "log")
TARGETS = {"A": "daily-return realised vol (MR's target)", "B": "ES 5-minute realised vol (the IHV study's target)"}


def block_network() -> None:
    def no_network(*a, **k):
        raise RuntimeError("dev_benchmark_form.py reads only the data caches; a download was attempted")
    sys.modules["yfinance"] = types.SimpleNamespace(download=no_network)


def clip(x, cut: str = CUT):
    """Drop every row after ``cut``; called on each input before anything is built from it."""
    return x.loc[x.index <= pd.Timestamp(cut)]


def load() -> tuple[pd.Series, pd.Series, pd.Series]:
    returns = clip(load_index_returns(start=START, end=LOAD_END))
    vix = clip(load_vix(START, LOAD_END))
    common = returns.index.intersection(vix.index)
    es = pd.read_csv(DATA_DIR / "es_rv_5min.csv", index_col=0, parse_dates=True)["rv"]
    return returns.loc[common], vix.loc[common], clip(es)


def return_target(returns: pd.Series, h: int) -> pd.Series:
    """MR's target (``regimes.forecast.forward_vol``, a sample std over the next h days); at h = 1 the std of one
    return is undefined, so it is |r_{t+1}|."""
    return returns.abs().shift(-1) if h == 1 else forward_vol(returns, h)


def es_forward(rv: pd.Series, h: int) -> pd.Series:
    """``regimes.forecast.forward_rv`` (which allows 3 missing days), with every day required when h < 4."""
    if h >= 4:
        return forward_rv(rv, h)
    return np.sqrt((rv.astype(float) ** 2).rolling(h, min_periods=h).mean().shift(-h))


def har_inputs(form: str, har: pd.DataFrame, vix_daily: pd.Series) -> pd.DataFrame:
    """HAR + VIX inputs in the requested form; logs floor at 1e-3 as the frozen scripts do."""
    if form == "log":
        return np.log(har.clip(lower=1e-3)).join(np.log(vix_daily).rename("vix"))
    if form == "level":
        return har.join(vix_daily.rename("vix"))
    raise ValueError(form)


def feature_sets(har: pd.DataFrame, vix_daily: pd.Series, prob: pd.Series, noise: pd.Series) -> dict[str, pd.DataFrame]:
    """Every (form, model) feature set, cut to the rows where all inputs of both forms exist."""
    sets = {}
    for form in FORMS:
        base = har_inputs(form, har, vix_daily)
        hb = base.drop(columns="vix")
        sets[(form, "HAR")] = hb
        sets[(form, "HAR + VIX")] = base
        sets[(form, "HAR + VIX + HMM prob")] = base.join(prob)
        sets[(form, "HAR + VIX + noise")] = base.join(noise.rename("noise"))
    rows = har.join(vix_daily.rename("vix")).join(prob).join(noise.rename("noise")).dropna().index
    return {k: v.loc[rows] for k, v in sets.items()}


def comparisons() -> list[tuple[tuple[str, str], tuple[str, str]]]:
    out = []
    for form in FORMS:
        out += [((form, "HAR + VIX"), (form, "HAR")),
                ((form, "HAR + VIX + HMM prob"), (form, "HAR + VIX")),
                ((form, "HAR + VIX + noise"), (form, "HAR + VIX"))]
    out += [(("log", m), ("level", m)) for m in ("HAR + VIX", "HAR + VIX + HMM prob")]
    return out


def scored_table(target: pd.Series, har: pd.DataFrame, vix_daily: pd.Series, prob: pd.Series,
                 noise: pd.Series, h: int) -> pd.DataFrame:
    target = target.where(target > 0)          # log(0) is undefined: zero-return days at h = 1 drop out
    sets = feature_sets(har, vix_daily, prob, noise)
    fc = {f"{f}: {m}": walk_forward_regression(target, X, horizon=h, step=63, min_rows=756, log_target=True).forecast
          for (f, m), X in sets.items()}
    joined = pd.concat({"target": target, **fc}, axis=1, sort=True).dropna()
    return joined


def compare(df: pd.DataFrame, name: str, ref: str, h: int, n_boot: int) -> dict:
    block, lag = max(63, h), max(20, h - 1)
    y = df["target"].to_numpy()
    e_f, e_b = df[name].to_numpy() - y, df[ref].to_numpy() - y
    q_f, q_b = qlike(df[name].to_numpy(), y), qlike(df[ref].to_numpy(), y)
    r_lo, r_hi = paired_interval(e_f, e_b, statistic="rmse", block=block, n_boot=n_boot)
    q_lo, q_hi = paired_interval(q_f, q_b, statistic="mean", block=block, n_boot=n_boot)
    dm_q, dm_s = hac_dm(q_f, q_b, lag=lag), hac_dm(e_f ** 2, e_b ** 2, lag=lag)
    return {"h": h, "forecast": name, "reference": ref, "windows": len(df) // h,
            "dRMSE 95%": f"{r_lo:+.3f} to {r_hi:+.3f}", "RMSE": verdict(r_lo, r_hi), "DM p (SE)": f"{dm_s['p']:.3f}",
            "dQLIKE 95%": f"{q_lo:+.3f} to {q_hi:+.3f}", "QLIKE": verdict(q_lo, q_hi), "DM p (QLIKE)": f"{dm_q['p']:.3f}",
            "_r": (r_lo, r_hi), "_q": (q_lo, q_hi)}


def losses(df: pd.DataFrame) -> pd.DataFrame:
    y = df["target"].to_numpy()
    return pd.DataFrame([{"model": m, "RMSE": f"{np.sqrt(((df[m] - df['target']) ** 2).mean()):.3f}",
                          "QLIKE": f"{qlike(df[m].to_numpy(), y).mean():.3f}"} for m in df.columns if m != "target"])


# Claim sentences in README.md / docs/WRITEUP.md that rest on HAR + implied vol: where, the script and lines that
# build the benchmark (all log form: np.log of the HAR inputs and of IV / sqrt(252), log_target=True), and the
# development comparison here that is nearest to it (None = S9 refits nothing that speaks to it).
CLAIMS = [
    ("README.md:10-13, WRITEUP.md:551-553", "a regime probability added to HAR + implied vol makes no measurable difference",
     "vol_forecast_vix.py:104-132; better_vol_models.py:93-117; msgarch_credit.py:168-186",
     ("A", 21, "HAR + VIX + HMM prob", "HAR + VIX"), "no difference"),
    ("README.md:48", "adding the VIX cuts forecast error (against HAR-RV)", "vol_forecast_vix.py:104-132",
     ("A", 21, "HAR + VIX", "HAR"), "better"),
    ("README.md:17-19", "unregistered S&P rows: HMM implied vol vs HAR + VIX", "vol_forecast_vix.py:104-132", None, None),
    ("WRITEUP.md:610-614", "term-structure signals and the HMM probability added to HAR + VIX: no difference",
     "term_structure_regimes.py:105-117", ("A", 21, "HAR + VIX + HMM prob", "HAR + VIX"), "no difference"),
    ("WRITEUP.md:655-672", "intraday HAR + VIX: the intraday HMM probability adds nothing", "intraday_rv.py:117-144",
     ("B", 21, "HAR + VIX + HMM prob", "HAR + VIX"), "no difference"),
    ("README.md:50", "cross-index: no model beats HAR-RV + implied vol", "better_vol_models.py:93-117", None, None),
    ("README.md:16-17, 51", "ETFs: MS-GARCH loses to HAR + implied vol", "msgarch_credit.py:168-186", None, None),
]


def claims_table(rows: list[dict]) -> list[dict]:
    out = []
    for where, what, built, key, expected in CLAIMS:
        rec = {"claim (where)": where, "what it says": what, "benchmark built in": built, "form used": "log"}
        if key is None:
            rec.update({"dev check here": "none (S9 refits no such model)", "log form RMSE / QLIKE": "-",
                        "level form RMSE / QLIKE": "-", "log form points the same way": "not checked"})
        else:
            tgt, h, model, ref = key
            get = {r["_pair"]: r for r in rows if r["_target"] == tgt and r["h"] == h}
            lg, lv = get[(("log", model), ("log", ref))], get[(("level", model), ("level", ref))]
            rec.update({"dev check here": f"target {tgt}, h={h}, {model} vs {ref}",
                        "log form RMSE / QLIKE": f"{lg['RMSE']} / {lg['QLIKE']}",
                        "level form RMSE / QLIKE": f"{lv['RMSE']} / {lv['QLIKE']}",
                        "log form points the same way": "yes" if lg["RMSE"] == expected else f"no (claim: {expected} on RMSE)"})
        out.append(rec)
    return out


def form_flips(rows: list[dict]) -> list[dict]:
    """For each (target, h, within-form comparison), whether the verdict differs between the level and log form."""
    out = []
    for r in rows:
        (form, model), (_, ref) = r["_pair"]
        if form != "level" or r["_cross"]:
            continue
        twin = next(x for x in rows if x["_target"] == r["_target"] and x["h"] == r["h"] and not x["_cross"]
                    and x["_pair"] == (("log", model), ("log", ref)))
        out.append({"target": r["_target"], "h": r["h"], "comparison": f"{model} vs {ref}",
                    "RMSE level": r["RMSE"], "RMSE log": twin["RMSE"], "QLIKE level": r["QLIKE"], "QLIKE log": twin["QLIKE"],
                    "moves": "yes" if (r["RMSE"], r["QLIKE"]) != (twin["RMSE"], twin["QLIKE"]) else "no"})
    return out


def answer(rows: list[dict], flips: list[dict]) -> str:
    """The S9 question answered from the computed rows: what moves with the form, and where."""
    moved = [f for f in flips if f["moves"] == "yes"]
    prob_moved = [f for f in moved if "HMM prob" in f["comparison"]]
    at21a = [f for f in moved if f["h"] == 21 and f["target"] == "A"]
    bench = [r for r in rows if r["_cross"] and r["_pair"][0][1] == "HAR + VIX"]
    log_better = [r for r in bench if "better" in (r["RMSE"], r["QLIKE"])]
    level_better = [r for r in bench if "worse" in (r["RMSE"], r["QLIKE"])]

    def desc(f: dict) -> str:
        return (f"target {f['target']} h={f['h']} {f['comparison']} (RMSE {f['RMSE level']} -> {f['RMSE log']}, "
                f"QLIKE {f['QLIKE level']} -> {f['QLIKE log']})")

    lines = [f"### Answer\n\nClass: {CLASS}. Read from the tables above.\n",
             "- Form MR used: the log form, in every script that builds a HAR + implied vol benchmark (table below). "
             "The level form is the alternative, not the paper's.",
             f"- Within-form verdicts that differ between the forms: {len(moved)} of {len(flips)}; at MR's target and "
             f"horizon (A, h = 21): {len(at21a)}.",
             f"- Those involving the HMM probability: {len(prob_moved)}"
             + (": " + "; ".join(desc(f) for f in prob_moved) if prob_moved else "") + ".",
             f"- The HAR + VIX benchmark, log minus level: log has the lower loss (interval below zero on RMSE or "
             f"QLIKE) in {len(log_better)} of {len(bench)} target-horizon cells, the level form in {len(level_better)}.",
             "- No multiplicity correction is applied to any interval in this file; a 'better' that appears in one "
             "form only is a development lead, not a result.\n"]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "docs" / "DEV_BENCHMARK_FORM_2026-10.md"))
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--horizons", default=",".join(str(h) for h in HORIZONS))
    args = parser.parse_args()
    block_network()
    returns, vix, es = load()
    horizons = [int(x) for x in args.horizons.split(",")]
    noise = pd.Series(np.random.default_rng(0).standard_normal(len(returns)), index=returns.index)
    vix_daily = vix / np.sqrt(252)
    es_days = es.index.intersection(returns.index)
    inputs = {"A": (returns, har_features(returns)), "B": (es.loc[es_days], har_rv(es.loc[es_days]))}

    out: list[str] = []
    P = out.append
    P(f"{CLASS}\n")
    P("# Development-only benchmark form check: HAR + VIX in levels vs in logs, October 2026\n")
    P(f"Class of every table in this file: **{CLASS}**. Written by `examples/dev_benchmark_form.py` at {git_head()}, "
      f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, {args.n_boot:,} bootstrap draws (seed 0). Data: S&P 500 "
      f"returns and the VIX {returns.index.min().date()} to {returns.index.max().date()} ({len(returns)} days), ES "
      f"5-minute RV {es.index.min().date()} to {es.index.max().date()} ({len(es)} days), every input clipped to "
      f"<= {CUT} at load. Stage S9 of the reopen.\n")
    P("Forms: *level* = HAR inputs and VIX / sqrt(252) in levels; *log* = the same inputs in logs (Corsi log-HAR; "
      "the form MR's frozen scripts use, `examples/vol_forecast_vix.py` lines 104-132). Both regress the log target "
      "with the lognormal mean correction; the HMM probability and the noise regressor (standard normal, seed 0) "
      "enter linearly. Expanding OLS, refit every 63 rows after 756, embargo h; all eight sets at a horizon fitted "
      "and scored on the same rows. Paired circular block bootstrap, block max(63, h); HAC Diebold-Mariano, lag "
      "max(20, h - 1), on squared errors (SE) and QLIKE. A negative difference favours the forecast. Target A is "
      "MR's (daily-return realised vol; at h = 1 that is |r_{t+1}| and the zero-return days drop out); target B is "
      "the implied-horizon-vol study's (ES 5-minute RV from 2010-06-07, HAR inputs built from the RV). The HMM is "
      "MR's two-state walk-forward model on daily returns (min_train 756, step 63), refit per horizon. *windows* = "
      "scored days / h.\n")
    rows = []
    for h in horizons:
        print(f"horizon {h}: HMM walk-forward ...", flush=True)
        wf = walk_forward_oos(returns, min_train=756, step=63, horizon=h)
        conv = None if wf.convergence is None else int(wf.convergence["best_converged"].sum())
        targets = {"A": return_target(returns, h), "B": es_forward(es.loc[es_days], h)}
        for key in TARGETS:
            series, har = inputs[key]
            df = scored_table(targets[key], har, vix_daily.reindex(series.index), wf.high_vol_prob, noise, h)
            P(f"## Target {key}, horizon {h}\n")
            P(f"Target {TARGETS[key]}. Scored days {len(df):,}, {df.index.min().date()} to {df.index.max().date()}; "
              f"non-overlapping windows {len(df) // h}; HMM refits {wf.n_refits}"
              + (f", converged {conv} of {wf.n_refits}" if conv is not None else "") + ".\n")
            P(md_table(losses(df)) + "\n")
            cmp_rows = []
            for (fa, ma), (fb, mb) in comparisons():
                r = compare(df, f"{fa}: {ma}", f"{fb}: {mb}", h, args.n_boot)
                r.update(_target=key, _pair=((fa, ma), (fb, mb)), _cross=fa != fb)
                cmp_rows.append(r)
            rows += cmp_rows
            P(md_table(pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in cmp_rows])) + "\n")

    flips = form_flips(rows)
    P("## Summary: does any comparison change with the form?\n")
    P(f"Class: {CLASS}. Each within-form comparison at each target and horizon, the 95% interval verdict under the "
      "level form beside the log form. *moves* = the RMSE or QLIKE verdict differs.\n")
    P(md_table(pd.DataFrame(flips)) + "\n")
    n_moves = sum(f["moves"] == "yes" for f in flips)
    P(f"Verdicts that move between forms: {n_moves} of {len(flips)} comparisons (each counted once if either loss "
      "moves).\n")
    P(answer(rows, flips))
    bench = [r for r in rows if r["_cross"]]
    P("## The benchmark itself: log form minus level form\n")
    P(f"Class: {CLASS}. Negative = the log form has the lower loss.\n")
    P(md_table(pd.DataFrame([{"target": r["_target"], "h": r["h"], "model": r["_pair"][0][1], "dRMSE 95%": r["dRMSE 95%"],
                              "RMSE": r["RMSE"], "dQLIKE 95%": r["dQLIKE 95%"], "QLIKE": r["QLIKE"]} for r in bench])) + "\n")
    if 21 in horizons:
        P("## Claim sentences that rest on HAR + implied vol\n")
        P(f"Class: {CLASS}. For each claim sentence, the form its benchmark used (read from the frozen and development "
          "scripts named: every one takes np.log of the HAR inputs and of IV / sqrt(252) and regresses the log target, "
          "so every one is the log form), and the nearest development comparison above. *points the same way* "
          "compares the log-form RMSE verdict with the direction the sentence states (RMSE is the paper's primary "
          "loss); the level form is shown for contrast. The S&P development data cannot speak to the cross-index "
          "and ETF sentences, and S9 refits no HMM implied vol, so those rows say not checked.\n")
        P(md_table(pd.DataFrame(claims_table(rows))) + "\n")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="ascii")
    for f in flips:
        print(f"{f['target']} h={f['h']} {f['comparison']}: RMSE {f['RMSE level']}/{f['RMSE log']} "
              f"QLIKE {f['QLIKE level']}/{f['QLIKE log']} moves={f['moves']}")
    print(f"moves {n_moves} of {len(flips)}; wrote {args.out}")


if __name__ == "__main__":
    main()
