"""Data-quality record for the spent holdouts, with the blast radius of every item on the published numbers.

Writes ``docs/DATA_QUALITY_2026-10.md``. Three classes of number appear and every table is headed with
its class:

* **reproduction**: facts read from the committed data caches (``data/*.csv``) and the reproduced
  forecasts under ``docs/results/reproductions/``: the suspect VXD prints, the partial YM sessions, the
  2014 no-bar days, the half days, the back-calculated VIX share, the two target definitions and the
  implied-vol forward fills.
* **post hoc, from the reproduced forecasts**: the registered claim intervals recomputed on the scored
  days with the affected days removed (same 63-day block bootstrap, 2,000 draws, seed 0). This is the
  target-side blast radius: the forecasts are the frozen ones, nothing is refit.
* **post hoc what-if, OLS re-estimation**: for the Dow, the OLS-only models (HAR, HAR-RV, HAR-RV + IV,
  HARQ + IV, SHAR + IV) re-estimated with the suspect VXD prints replaced by the previous print, and
  with the three partial YM sessions treated as missing. The regression code and arguments are the
  frozen script's; the replica is checked against the saved forecasts first, and the check is printed.

Nothing here is a test of a claim and nothing changes a registered verdict. The items come from the
desk review of 2026-10-17 (data-engineer lane, F2 to F4, F10 and the two-target-definitions note).

Run from the repo root (reads only the caches; a download attempt raises)::

    python -u examples/data_quality.py [--n-boot 2000] [--out docs/DATA_QUALITY_2026-10.md]
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

from regimes.data import DATA_DIR, load_fred_series, load_index_returns  # noqa: E402
from regimes.forecast import forward_rv, har_features, har_rv, qlike, walk_forward_regression  # noqa: E402
from regimes.posthoc import paired_interval  # noqa: E402

from better_vol_models import CLAIMS as CROSS_CLAIMS  # noqa: E402
from better_vol_models import H, RETURNS_FROM  # noqa: E402
from cross_index_holdout import HOLDOUT as CROSS_HOLDOUT  # noqa: E402
from cross_index_holdout import HOLDOUT_END, claim_verdict  # noqa: E402
from msgarch_credit_holdout import HOLDOUT as ETF_HOLDOUT  # noqa: E402
from posthoc_stats import committed_intervals, committed_vix_intervals, git_head, load_scored, md_table, verdict  # noqa: E402
from vol_forecast_vix import COMPARISONS as VIX_COMPARISONS  # noqa: E402

REPRO = ROOT / "docs" / "results" / "reproductions"
CROSS_COMMITTED = ROOT / "docs" / "results" / "cross_index_holdout_2026-10-14.txt"
FULL_SESSION = 78          # five-minute returns in a 09:30-16:00 session
HALF_DAY = (45, 46)        # futures RTH close 13:15 on NYSE half days
PARTIAL_BELOW = 75         # fewer returns than this, and not a half day: a partial session (the March 2020 halts leave 75-77)
VXD_SUSPECTS = ["2021-07-13", "2024-03-21", "2025-10-16"]
YM_PARTIAL = ["2020-02-27", "2020-02-28", "2020-06-30"]
NEW_VIX_FROM = "2003-09-22"  # Cboe's new-methodology VIX is live from this date; earlier values are back-calculated
STEMS = {"Nasdaq-100": ("001", "002", "003"), "Dow Jones Industrial Average": ("004", "005", "006"),
         "Russell 2000": ("007", "008", "009")}
CLASS_REPRO = "reproduction (read from the committed data caches and the reproduced forecasts)"
CLASS_POSTHOC = "post hoc, from the reproduced forecasts; not a registered test"
CLASS_WHATIF = "post hoc what-if, OLS re-estimation on the frozen data with one change; not a registered test"


def block_network() -> None:
    def no_network(*a, **k):
        raise RuntimeError("data_quality.py reads only the data caches; a download was attempted")
    sys.modules["yfinance"] = types.SimpleNamespace(download=no_network)


def rv_cache(name: str) -> pd.DataFrame:
    """The committed session-RV cache for one cross-index asset, exactly as the frozen loader reads it."""
    _, _, cache, _, _ = CROSS_HOLDOUT[name]
    return pd.read_csv(DATA_DIR / cache, index_col=0, parse_dates=True).loc[:HOLDOUT_END]


def index_returns(name: str) -> pd.Series:
    _, _, _, ticker, _ = CROSS_HOLDOUT[name]
    yahoo_end = (pd.Timestamp(HOLDOUT_END) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    return load_index_returns(ticker, start=RETURNS_FROM, end=yahoo_end).loc[:HOLDOUT_END]


def index_iv(name: str) -> pd.Series:
    _, _, _, _, fred_id = CROSS_HOLDOUT[name]
    return load_fred_series(fred_id).loc[RETURNS_FROM:HOLDOUT_END]


def short_targets(rv: pd.Series, scored_days: pd.DatetimeIndex, horizon: int = H) -> pd.Series:
    """Number of RV observations inside each scored day's forward window (t, t + horizon]."""
    counts = rv.notna().astype(int).rolling(horizon, min_periods=1).sum().shift(-horizon)
    return counts.reindex(scored_days)


def windows_containing(flag_days: pd.DatetimeIndex, calendar: pd.DatetimeIndex, horizon: int = H) -> pd.DatetimeIndex:
    """Scored days whose forward window (t, t + horizon] on ``calendar`` contains a flagged day."""
    flag = pd.Series(calendar.isin(flag_days).astype(int), index=calendar)
    hit = flag.rolling(horizon, min_periods=1).sum().shift(-horizon)
    return hit.index[hit.fillna(0) > 0]


def claim_rows(df: pd.DataFrame, n_boot: int) -> list[dict]:
    y = df["target"].to_numpy()
    rows = []
    for cid, f_name, ref, expected in CROSS_CLAIMS:
        e_f, e_b = df[f_name].to_numpy() - y, df[ref].to_numpy() - y
        lo, hi = paired_interval(e_f, e_b, statistic="rmse", block=63, n_boot=n_boot)
        rows.append({"claim": cid, "forecast": f_name, "reference": ref, "expected": expected,
                     "lo": lo, "hi": hi, "verdict": verdict(lo, hi)})
    return rows


def exclusion_table(block: str, df: pd.DataFrame, keep: pd.Index, registered: dict, n_boot: int,
                    label: str, blocks: list[str] | None = None) -> tuple[str, int, list[str]]:
    """Registered interval beside the interval on the kept rows; returns (table, n changed, notes).

    With ``blocks`` given, the note also states the claim outcome across indices (the frozen script's
    ``claim_verdict`` rule) with this index's recomputed verdicts and the other indices' registered ones."""
    sub = df.loc[df.index.isin(keep)]
    rows = claim_rows(sub, n_boot)
    out, changed = [], 0
    for r in rows:
        reg_iv, reg_v, _, _ = registered[(block, r["claim"])]
        moved = r["verdict"] != reg_v
        changed += moved
        out.append({"claim": r["claim"], "forecast": r["forecast"], "reference": r["reference"],
                    "registered dRMSE": reg_iv, "registered": reg_v,
                    label: f"{r['lo']:+.3f} to {r['hi']:+.3f}", "verdict": r["verdict"],
                    "moved": "yes" if moved else ""})
    note = [f"rows kept {len(sub)} of {len(df)} ({len(df) - len(sub)} removed); per-index verdicts moved: {changed} of {len(rows)}"]
    if blocks is not None:
        new_v = {r["claim"]: r["verdict"] for r in rows}
        outcome_changes = []
        for cid, _, _, expected in CROSS_CLAIMS:
            reg_out = claim_verdict(expected, [registered[(b, cid)][1] for b in blocks])
            alt_out = claim_verdict(expected, [new_v[cid] if b == block else registered[(b, cid)][1] for b in blocks])
            if reg_out != alt_out:
                outcome_changes.append(f"{cid} {reg_out} -> {alt_out}")
        note.append("claim outcomes across the three indices: " + ("unchanged" if not outcome_changes else "; ".join(outcome_changes)))
    return md_table(pd.DataFrame(out)), changed, note


def claim_outcomes(blocks: list[str], per_block: dict[str, list[dict]]) -> dict[str, str]:
    out = {}
    for cid, _, _, expected in CROSS_CLAIMS:
        out[cid] = claim_verdict(expected, [next(r["verdict"] for r in per_block[b] if r["claim"] == cid) for b in blocks])
    return out


# ----------------------------------------------------------------------------------------------
# OLS what-if on the Dow

def dow_ols_forecasts(returns: pd.Series, rv: pd.DataFrame, iv: pd.Series, common: pd.DatetimeIndex) -> dict[str, pd.Series]:
    """The five OLS-only models of ``better_vol_models.evaluate_index`` with its exact arguments."""
    days = returns.index
    rv = rv.reindex(days).loc[rv.index.min():HOLDOUT_END]
    iv = iv.reindex(days).ffill(limit=5)
    target = forward_rv(rv["rv"], H)
    log_har = np.log(har_features(returns).clip(lower=1e-3))
    hrv = har_rv(rv["rv"])
    log_hrv = np.log(hrv.clip(lower=1e-3))
    log_iv = np.log(iv / np.sqrt(252)).rename("iv")
    q = (np.sqrt(rv["rq"]) / rv["rv"] ** 2).rename("q")
    harq = log_hrv.join(log_iv).assign(q_term=(log_hrv["rv_1d"] - log_hrv["rv_22d"]) * (q - 1))
    shar = log_hrv.drop(columns="rv_1d").join(log_iv).assign(
        rv_neg=np.log(rv["rv_neg"].clip(lower=1e-3)), rv_pos=np.log(rv["rv_pos"].clip(lower=1e-3)))
    signals = {"HAR": log_har, "HAR-RV": log_hrv, "HAR-RV + IV": log_hrv.join(log_iv), "HARQ + IV": harq,
               "SHAR + IV": shar}
    fc = {k: walk_forward_regression(target, X.reindex(common), horizon=H, step=63, min_rows=756,
                                     log_target=True).forecast for k, X in signals.items()}
    fc["target"] = target
    return fc


def common_rows(name: str, returns: pd.Series, rv: pd.DataFrame, iv: pd.Series) -> pd.DatetimeIndex:
    """The frozen script's ``common`` index: rows where every signal (including the saved HMM, GJR and
    MSM implied vols) is present."""
    oos, gjr, msm = STEMS[name]
    wf = REPRO / "cross_index" / "walk_forwards"
    saved = [pd.read_csv(wf / f"walk_forward_{k}_{s}__implied_vol.csv", index_col=0, parse_dates=True).iloc[:, 0]
             for k, s in (("oos", oos), ("gjr", gjr), ("msm", msm))]
    saved.append(pd.read_csv(wf / f"walk_forward_oos_{oos}__high_vol_prob.csv", index_col=0, parse_dates=True).iloc[:, 0])
    days = returns.index
    rv = rv.reindex(days).loc[rv.index.min():HOLDOUT_END]
    iv = iv.reindex(days).ffill(limit=5)
    log_hrv = np.log(har_rv(rv["rv"]).clip(lower=1e-3))
    q = (np.sqrt(rv["rq"]) / rv["rv"] ** 2).rename("q")
    pieces = [np.log(har_features(returns).clip(lower=1e-3)), log_hrv, np.log(iv / np.sqrt(252)).rename("iv"),
              q, np.log(rv["rv_neg"].clip(lower=1e-3)).rename("neg"), np.log(rv["rv_pos"].clip(lower=1e-3)).rename("pos"),
              *[np.log(s).rename(f"s{i}") if i < 3 else s.rename("p") for i, s in enumerate(saved)]]
    return pd.concat(pieces, axis=1).dropna().index


def whatif_table(base: dict[str, pd.Series], alt: dict[str, pd.Series], scored: pd.DataFrame, n_boot: int,
                 claims: tuple[str, ...]) -> tuple[str, str]:
    """Losses and OLS-only claim intervals for the frozen inputs beside the changed inputs."""
    models = ["HAR", "HAR-RV", "HAR-RV + IV", "HARQ + IV", "SHAR + IV"]
    b = pd.concat({**{k: base[k] for k in models}, "target": base["target"]}, axis=1, sort=False).reindex(scored.index)
    a = pd.concat({**{k: alt[k] for k in models}, "target": alt["target"]}, axis=1, sort=False).reindex(scored.index)
    keep = a.dropna().index.intersection(b.dropna().index)
    dropped = scored.index.difference(keep)
    full = b.dropna()
    b, a = b.loc[keep], a.loc[keep]
    loss_rows = []
    for m in models:
        loss_rows.append({"model": m,
                          "RMSE frozen, all scored days": f"{np.sqrt(((full[m] - full['target']) ** 2).mean()):.4f}",
                          "RMSE frozen": f"{np.sqrt(((b[m] - b['target']) ** 2).mean()):.4f}",
                          "RMSE changed": f"{np.sqrt(((a[m] - a['target']) ** 2).mean()):.4f}",
                          "QLIKE frozen": f"{qlike(b[m].to_numpy(), b['target'].to_numpy()).mean():.4f}",
                          "QLIKE changed": f"{qlike(a[m].to_numpy(), a['target'].to_numpy()).mean():.4f}",
                          "max |forecast change|": f"{(a[m] - b[m]).abs().max():.4f}",
                          "days changed > 1e-6": int(((a[m] - b[m]).abs() > 1e-6).sum())})
    claim_out = []
    for cid, f_name, ref, expected in CROSS_CLAIMS:
        if cid not in claims:
            continue
        rows = {}
        for tag, d in (("frozen", b), ("changed", a)):
            y = d["target"].to_numpy()
            lo, hi = paired_interval(d[f_name].to_numpy() - y, d[ref].to_numpy() - y, statistic="rmse", block=63, n_boot=n_boot)
            rows[tag] = (f"{lo:+.3f} to {hi:+.3f}", verdict(lo, hi))
        claim_out.append({"claim": cid, "forecast": f_name, "reference": ref, "dRMSE frozen": rows["frozen"][0],
                          "verdict frozen": rows["frozen"][1], "dRMSE changed": rows["changed"][0],
                          "verdict changed": rows["changed"][1],
                          "moved": "yes" if rows["frozen"][1] != rows["changed"][1] else ""})
    head = f"rows scored: {len(keep)} of the {len(scored)} frozen scored days"
    if len(dropped):
        head += (f"; {len(dropped)} days lose their forecast because a feature becomes missing: "
                 + ", ".join(d.strftime("%Y-%m-%d") for d in dropped) + ". 'RMSE frozen' and the intervals are on the "
                 "common rows; 'all scored days' is the published row set.")
    return head + "\n\n" + md_table(pd.DataFrame(loss_rows)), md_table(pd.DataFrame(claim_out))


# ----------------------------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "docs" / "DATA_QUALITY_2026-10.md"))
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()
    n_boot = args.n_boot
    block_network()

    blocks = list(CROSS_HOLDOUT)
    scored = dict(load_scored("cross_index"))
    registered = committed_intervals(CROSS_COMMITTED, blocks)
    rv = {b: rv_cache(b) for b in blocks}
    ret = {b: index_returns(b) for b in blocks}
    iv = {b: index_iv(b) for b in blocks}
    # The frozen loader reindexes the RV cache to the index calendar: holiday futures sessions (no index
    # close) drop out and no-bar trading days become NaN rows. Every count below uses that calendar.
    rv_cal = {b: rv[b].reindex(ret[b].index).loc[rv[b].index.min():] for b in blocks}
    short = {b: short_targets(rv_cal[b]["rv"], scored[b].index) for b in blocks}

    out: list[str] = []
    summary: list[str] = []
    P = out.append
    P("# Data quality of the spent holdouts, October 2026\n")
    P("Every table in this file is headed with its class: **reproduction** (facts read from the committed "
      "data caches and the reproduced forecasts), **post hoc, from the reproduced forecasts** (the registered "
      "claim intervals recomputed with the affected scored days removed; the forecasts are the frozen ones), or "
      "**post hoc what-if, OLS re-estimation** (the OLS-only models re-estimated on the Dow with one input "
      "changed). Nothing here is a registered test and nothing changes a registered verdict; the registered "
      "verdicts are the RMSE verdicts in `docs/results/cross_index_holdout_2026-10-14.txt` and the VIX tables in "
      "`docs/WRITEUP.md`. None of these items was screened before the holdouts ran.\n")
    P(f"Written by `examples/data_quality.py` at {git_head()}, {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, "
      f"with {n_boot:,} bootstrap draws (seed 0). Inputs: `data/*_rv_5min.csv`, `data/fred_*.csv`, the Yahoo "
      "price caches named in `data/MANIFEST.md`, and `docs/results/reproductions/cross_index/` and "
      "`vix_early/`. Items are the data-engineer desk report's F2 (VXD prints), F3 (partial YM sessions), "
      "F4 (2014 no-bar days and short targets), F10 (half days), the back-calculated VIX note and the "
      "two-target-definitions note (desk, data-engineer, 2026-10-17). Blast radius means: the published "
      "number is recomputed without, or with a corrected version of, the affected days, and the difference is shown.\n")

    # ---- 1. VXD prints -------------------------------------------------------------------------
    P("## 1. Suspect VXD prints (Dow implied vol, FRED VXDCLS)\n")
    P(f"Class: {CLASS_REPRO}.\n")
    dow = "Dow Jones Industrial Average"
    vxd = iv[dow]
    q001 = float(vxd.quantile(0.001))
    rows = []
    for d in VXD_SUSPECTS:
        t = pd.Timestamp(d)
        pos = vxd.index.get_loc(t)
        prev, nxt = float(vxd.iloc[pos - 1]), float(vxd.iloc[pos + 1])
        on_calendar = t in scored[dow].index
        f_iv, f_rv = (float(scored[dow].loc[t, "HAR-RV + IV"]), float(scored[dow].loc[t, "HAR-RV"])) if on_calendar else (np.nan, np.nan)
        tgt = float(scored[dow].loc[t, "target"]) if on_calendar else np.nan
        rows.append({"date": d, "VXD": f"{vxd.loc[t]:.2f}", "previous": f"{prev:.2f}", "next": f"{nxt:.2f}",
                     "log IV jump vs previous": f"{np.log(vxd.loc[t] / prev):+.3f}",
                     "scored day": "yes" if on_calendar else "no",
                     "HAR-RV + IV forecast": f"{f_iv:.3f}", "HAR-RV forecast": f"{f_rv:.3f}", "target": f"{tgt:.3f}"})
    P(md_table(pd.DataFrame(rows)))
    P(f"\nVXD 0.1 percent quantile over {RETURNS_FROM[:4]}-{HOLDOUT_END[:4]}: {q001:.2f}; the series' minimum apart from "
      f"2021-07-13 is {vxd.drop(pd.Timestamp('2021-07-13')).min():.2f}. The day-to-day spread of log VXD "
      f"(median absolute change) is {np.log(vxd).diff().abs().median():.3f}. No loader screens implied vol for bad "
      "prints (`src/regimes/data.py`, `examples/better_vol_models.py`); the prints enter the IV models' "
      "regressor on the day and every training set from the next quarterly refit onward.\n")
    P(f"### 1a. Blast radius, target side\n\nClass: {CLASS_POSTHOC}. The three scored days removed from the Dow.\n")
    keep = scored[dow].index.difference(pd.DatetimeIndex(VXD_SUSPECTS))
    tbl, ch, note = exclusion_table(dow, scored[dow], keep, registered, n_boot, "without the 3 days", blocks)
    P(tbl + "\n\n" + "; ".join(note) + "\n")
    summary.append(f"VXD prints, 3 Dow scored days removed: {ch} of 9 per-index verdicts move")

    P(f"### 1b. Blast radius, what-if\n\nClass: {CLASS_WHATIF}. The three prints are replaced by the previous day's "
      "VXD close and the five OLS-only models are re-estimated with the frozen script's regression call "
      "(`walk_forward_regression`, horizon 21, step 63, min_rows 756, log target). The HMM, GJR-GARCH and MSM "
      "models do not read implied vol and are unchanged; the claims that pair OLS models with them (P3, P4, P5, "
      "R3, R4) are covered by 1a.\n")
    common = common_rows(dow, ret[dow], rv[dow], iv[dow])
    base = dow_ols_forecasts(ret[dow], rv[dow], iv[dow], common)
    diffs = {m: float((base[m].reindex(scored[dow].index) - scored[dow][m]).abs().max()) for m in
             ["HAR", "HAR-RV", "HAR-RV + IV", "HARQ + IV", "SHAR + IV"]}
    tdiff = float((base["target"].reindex(scored[dow].index) - scored[dow]["target"]).abs().max())
    P("Replica check (reproduction): maximum absolute difference between the re-estimated frozen-input "
      "forecasts and the saved scored columns, " + ", ".join(f"{m} {v:.1e}" for m, v in diffs.items()) +
      f"; target {tdiff:.1e}; common rows {len(common)}.\n")
    iv_fixed = iv[dow].copy()
    for d in VXD_SUSPECTS:
        pos = iv_fixed.index.get_loc(pd.Timestamp(d))
        iv_fixed.iloc[pos] = iv_fixed.iloc[pos - 1]
    alt = dow_ols_forecasts(ret[dow], rv[dow], iv_fixed, common)
    losses, claims = whatif_table(base, alt, scored[dow], n_boot, ("P1", "P2", "R1", "R2"))
    P(losses + "\n")
    P(claims + "\n")
    replica_ok = max(diffs.values()) < 1e-9 and tdiff < 1e-9
    summary.append(f"VXD what-if (prints replaced, OLS refit): replica {'exact' if replica_ok else 'NOT exact'}; see 1b for the moved column")

    # ---- 2. Partial YM sessions ------------------------------------------------------------------
    P("## 2. Partial YM sessions kept as full-session RV\n")
    P(f"Class: {CLASS_REPRO}. Index trading days in each scored window whose session has fewer than {PARTIAL_BELOW} five-minute "
      f"returns and is not a half day (a half day has {HALF_DAY[0]}-{HALF_DAY[1]}, a full session {FULL_SESSION}, the "
      "level-1 circuit-breaker halts of March 2020 leave 75-77; futures sessions on index "
      "holidays are not index trading days and are dropped by the loader). `daily_realised_vol` "
      "sums whatever bars exist and records `n_returns`; nothing reads `n_returns` "
      "(`src/regimes/intraday.py`). The cross-index protocol keeps degraded days that have bars.\n")
    rows = []
    for b in blocks:
        r = rv_cal[b]
        win = r.loc[scored[b].index.min():scored[b].index.max() + pd.Timedelta(days=40)]
        part = win[(win["n_returns"] < PARTIAL_BELOW) & ~win["n_returns"].between(*HALF_DAY)]
        for d, row in part.iterrows():
            pos = r.index.get_loc(d)
            rows.append({"index": b, "date": d.date(), "n_returns": int(row["n_returns"]), "rv": f"{row['rv']:.2f}",
                         "rv previous": f"{r['rv'].iloc[pos - 1]:.2f}", "rv next": f"{r['rv'].iloc[pos + 1]:.2f}",
                         "index return that day (%)": f"{ret[b].get(d, np.nan):+.2f}"})
    P(md_table(pd.DataFrame(rows)) if rows else "none")
    ym = pd.DatetimeIndex(YM_PARTIAL)
    hit_targets = windows_containing(ym, ret[dow].index).intersection(scored[dow].index)
    feat_flag = pd.Series(ret[dow].index.isin(ym).astype(int), index=ret[dow].index)
    hit_feats = feat_flag.rolling(22, min_periods=1).sum()
    hit_feats = hit_feats.index[hit_feats > 0].intersection(scored[dow].index)
    P(f"\nDow scored days whose 21-day target window contains one of the three sessions: {len(hit_targets)}; scored "
      f"days whose 22-day HAR-RV feature window contains one: {len(hit_feats)}; either: "
      f"{len(hit_targets.union(hit_feats))}.\n")
    P(f"### 2a. Blast radius, target side\n\nClass: {CLASS_POSTHOC}. Dow scored days whose target or HAR-RV feature "
      "window contains one of the three sessions removed.\n")
    keep = scored[dow].index.difference(hit_targets.union(hit_feats))
    tbl, ch, note = exclusion_table(dow, scored[dow], keep, registered, n_boot, "without affected days", blocks)
    P(tbl + "\n\n" + "; ".join(note) + "\n")
    summary.append(f"partial YM sessions, {len(scored[dow]) - len(keep)} Dow days removed: {ch} of 9 per-index verdicts move")
    P(f"### 2b. Blast radius, what-if\n\nClass: {CLASS_WHATIF}. The three sessions set to missing RV (as the no-bar days "
      "are), so the target and the HAR-RV features treat them as gaps; the five OLS-only models re-estimated.\n")
    rv_fixed = rv[dow].copy()
    rv_fixed.loc[rv_fixed.index.isin(ym), ["rv", "rv_neg", "rv_pos", "rq"]] = np.nan
    alt = dow_ols_forecasts(ret[dow], rv_fixed, iv[dow], common)
    losses, claims = whatif_table(base, alt, scored[dow], n_boot, ("P1", "P2", "R1", "R2"))
    P(losses + "\n")
    P(claims + "\n")

    # ---- 3. No-bar days and short targets --------------------------------------------------------
    P("## 3. Trading days with no bars, and targets on fewer than 21 sessions\n")
    P(f"Class: {CLASS_REPRO}. Index trading days (Yahoo calendar) inside the RV range with no session RV. "
      "`forward_rv` averages the available RV^2 over the next 21 sessions when at least 18 are present "
      "(`min_periods = horizon - 3`), and `har_rv` tolerates 4 of 5 and 18 of 22; so a gap inside a window "
      "shortens the window rather than dropping the day (`src/regimes/forecast.py`).\n")
    rows, short_counts = [], {}
    for b in blocks:
        r = rv_cal[b]["rv"]
        missing = r.index[r.isna()]
        sc = short[b]
        short_counts[b] = int((sc < H).sum())
        rows.append({"index": b, "RV from": rv[b].index.min().date(), "no-bar trading days": len(missing),
                     "dates": ", ".join(d.strftime("%Y-%m-%d") for d in missing),
                     "scored targets on fewer than 21 sessions": short_counts[b],
                     "of which 18, 19, 20": ", ".join(str(int((sc == k).sum())) for k in (18, 19, 20)),
                     "scored targets": len(sc)})
    P(md_table(pd.DataFrame(rows)))
    tail_short = {b: int((short[b].iloc[-H:] < H).sum()) for b in blocks}
    P(f"\nTargets at the sample end: the last 21 scored days of each index have "
      + ", ".join(f"{tail_short[b]}" for b in blocks) +
      " short targets respectively. `forward_rv` shifts the rolling window back by the horizon, so a window that runs "
      "past the end of the series is never produced; the `min_periods` tolerance acts only on gaps inside a window "
      "(`tests/test_forecast.py`, forward_rv alignment test). The scope's phrase '18-20-day targets at sample ends' "
      "does not describe the code: the shortened targets are the ones whose window spans a 2014 gap, counted above. "
      "The desk report (data-engineer, F4) counted 66 Nasdaq-100 and 21 Dow targets; the count here, on the calendar "
      "the frozen loader uses (index trading days, no-bar days as NaN rows), is 63 and 21: the two-gap and three-gap "
      "clusters of June and September 2014 share windows, so a per-gap count of 21 overstates them.\n")
    P(f"### 3a. Blast radius, target side\n\nClass: {CLASS_POSTHOC}. Scored days whose target window has fewer than 21 "
      "sessions removed, per index; the Russell 2000 has none.\n")
    for b in blocks:
        keep = short[b].index[short[b] >= H]
        if len(keep) == len(scored[b]):
            P(f"{b}: no short targets, table unchanged.\n")
            continue
        tbl, ch, note = exclusion_table(b, scored[b], keep, registered, n_boot, "without short targets", blocks)
        P(f"**{b}**\n\n" + tbl + "\n\n" + "; ".join(note) + "\n")
        summary.append(f"short targets, {b}: {len(scored[b]) - len(keep)} days removed, {ch} of 9 per-index verdicts move")

    # ---- 4. Half days ----------------------------------------------------------------------------
    P("## 4. Half days\n")
    P(f"Class: {CLASS_REPRO}. Scored-window sessions with {HALF_DAY[0]}-{HALF_DAY[1]} five-minute returns (NYSE half "
      "days, futures RTH close 13:15 ET). Their RV enters the target and the HAR-RV windows unscaled, which is the "
      "usual HAR practice.\n")
    rows, half_days = [], {}
    for b in blocks:
        r = rv_cal[b]
        win = r.loc[scored[b].index.min():scored[b].index.max() + pd.Timedelta(days=40)]
        hd = win.index[win["n_returns"].between(*HALF_DAY)]
        half_days[b] = hd
        hit = windows_containing(hd, ret[b].index).intersection(scored[b].index)
        rows.append({"index": b, "half days": len(hd), "median RV on half days": f"{win.loc[hd, 'rv'].median():.3f}",
                     "median RV, full sessions": f"{win.loc[win['n_returns'] == FULL_SESSION, 'rv'].median():.3f}",
                     "scored targets containing one": len(hit)})
    P(md_table(pd.DataFrame(rows)))
    P(f"\n### 4a. Blast radius, target side\n\nClass: {CLASS_POSTHOC}. Scored days whose 21-day target window contains "
      "a half day removed, per index. This removes many days, so the intervals widen for that reason too.\n")
    for b in blocks:
        hit = windows_containing(half_days[b], ret[b].index).intersection(scored[b].index)
        keep = scored[b].index.difference(hit)
        tbl, ch, note = exclusion_table(b, scored[b], keep, registered, n_boot, "without half-day windows", blocks)
        P(f"**{b}**\n\n" + tbl + "\n\n" + "; ".join(note) + "\n")
        summary.append(f"half days, {b}: {len(hit)} days removed, {ch} of 9 per-index verdicts move")

    # ---- 5. Implied-vol forward fills ---------------------------------------------------------------
    P("## 5. Implied-vol forward fills\n")
    P(f"Class: {CLASS_REPRO}. Both holdout scripts reindex the FRED implied-vol series to the asset's calendar and "
      "forward-fill up to five days. Counted here on each asset's own calendar and scored window.\n")
    rows = []
    for b in blocks:
        s = iv[b].reindex(ret[b].index)
        filled = s.isna() & s.ffill(limit=5).notna()
        win = scored[b].index
        rows.append({"holdout": "cross-index", "asset": b, "FRED series": CROSS_HOLDOUT[b][4],
                     "calendar days with no print": int(s.isna().sum()),
                     "filled (within 5 days)": int(filled.sum()),
                     "filled days that are scored": int(filled.reindex(win).fillna(False).sum()),
                     "scored days": len(win)})
    etf_scored = dict(load_scored("etf_frozen_checkpoints"))
    for name, (ticker, fred_id) in ETF_HOLDOUT.items():
        yahoo_end = (pd.Timestamp(HOLDOUT_END) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
        r = load_index_returns(ticker, start=RETURNS_FROM, end=yahoo_end).loc[:HOLDOUT_END]
        s = load_fred_series(fred_id).loc[RETURNS_FROM:HOLDOUT_END].reindex(r.index)
        s = s.loc[s.first_valid_index():]
        filled = s.isna() & s.ffill(limit=5).notna()
        win = next((df.index for blk, df in etf_scored.items() if blk.startswith(name.split(" (")[0])), None)
        rows.append({"holdout": "MS-GARCH and credit", "asset": name, "FRED series": fred_id,
                     "calendar days with no print": int(s.isna().sum()),
                     "filled (within 5 days)": int(filled.sum()),
                     "filled days that are scored": int(filled.reindex(win).fillna(False).sum()) if win is not None else "n/a",
                     "scored days": len(win) if win is not None else "n/a"})
    P(md_table(pd.DataFrame(rows)))
    P("\nA filled day carries the previous print as that day's implied vol; the count of scored days on a fill is the "
      "blast radius (each is one regressor value among thousands; no verdict can move on these counts, and no "
      "exclusion table is needed).\n")

    # ---- 6. Back-calculated VIX ----------------------------------------------------------------------
    P("## 6. Back-calculated VIX in the 1990-2004 holdout\n")
    P(f"Class: {CLASS_REPRO}. Cboe's new-methodology VIX is live from {NEW_VIX_FROM}; earlier values in the "
      "Yahoo ^VIX series are Cboe's back-calculation (the 1993-12-22 minimum matches Cboe's published record low). "
      "`docs/VIX_HOLDOUT_PROTOCOL.md` says so; the WRITEUP does not yet.\n")
    vix_early = pd.read_csv(DATA_DIR / "VIX_1990-01-01_2004-12-31.csv", index_col=0, parse_dates=True)
    n_all, n_back = len(vix_early), int((vix_early.index < NEW_VIX_FROM).sum())
    ve = dict(load_scored("vix_early"))
    cal = next(df for blk, df in ve.items() if "HAR + VIX" in df.columns)
    n_sc, n_sc_back = len(cal), int((cal.index < NEW_VIX_FROM).sum())
    P(f"VIX file days {n_all}, back-calculated {n_back} ({100 * n_back / n_all:.0f} percent); scored days "
      f"{n_sc}, of which {n_sc_back} ({100 * n_sc_back / n_sc:.0f} percent) are forecasts made on a back-calculated "
      f"VIX (note that a forecast made before {NEW_VIX_FROM} also uses the back-calculated history in its training set).\n")
    P(f"### 6a. Blast radius\n\nClass: {CLASS_POSTHOC}. The seven registered comparisons on the back-calculated days "
      "only, and the losses on the live-VIX tail (too short for an interval).\n")
    pre, post = cal.loc[cal.index < NEW_VIX_FROM], cal.loc[cal.index >= NEW_VIX_FROM]
    rows = []
    reg = committed_vix_intervals("vix_early")
    for name, ref in VIX_COMPARISONS:
        y = pre["target"].to_numpy()
        lo, hi = paired_interval(pre[name].to_numpy() - y, pre[ref].to_numpy() - y, statistic="rmse", block=63, n_boot=n_boot)
        r_iv, r_v = reg[(name, ref)][0], reg[(name, ref)][1]
        rows.append({"forecast": name, "reference": ref, "registered dRMSE": r_iv, "registered": r_v,
                     f"before {NEW_VIX_FROM}": f"{lo:+.3f} to {hi:+.3f}", "verdict": verdict(lo, hi),
                     "moved": "yes" if verdict(lo, hi) != r_v else "",
                     f"RMSE from {NEW_VIX_FROM} (n={len(post)})": f"{np.sqrt(((post[name] - post['target']) ** 2).mean()):.3f} vs {np.sqrt(((post[ref] - post['target']) ** 2).mean()):.3f}"})
    P(md_table(pd.DataFrame(rows)))
    moved = sum(r["moved"] == "yes" for r in rows)
    P(f"\nrows kept {len(pre)} of {len(cal)}; verdicts moved: {moved} of {len(rows)}.\n")
    summary.append(f"back-calculated VIX, 1996-2004 comparisons on the back-calculated days only: {moved} of 7 verdicts move")

    # ---- 7. Two target definitions -------------------------------------------------------------------
    P("## 7. Two target definitions\n")
    P(f"Class: {CLASS_REPRO}. The cross-index target is sqrt(mean session RV^2) over the next 21 sessions "
      "(regular hours only, overnight excluded); the VIX and MS-GARCH holdouts' target is the rolling 21-day "
      "standard deviation of close-to-close returns. The implied-vol regressor is the same annualised "
      "close-to-close quantity in both (IV / sqrt(252), logged), so on the cross-index its level is about twice the "
      "target's and the log-scale intercept absorbs the gap. Computed on each index's scored window:\n")
    rows = []
    for b in blocks:
        win = scored[b].index
        r_sq = (ret[b].reindex(ret[b].index) ** 2)
        rv_sq = rv[b]["rv"].reindex(ret[b].index) ** 2
        both = pd.concat([r_sq, rv_sq], axis=1).dropna().loc[win.min():win.max()]
        share = float(both.iloc[:, 1].mean() / both.iloc[:, 0].mean())
        ivd = (iv[b].reindex(ret[b].index).ffill(limit=5) / np.sqrt(252)).loc[win]
        rows.append({"index": b, "median IV / sqrt(252)": f"{ivd.median():.2f}",
                     "median session RV": f"{rv[b]['rv'].reindex(win).median():.2f}",
                     "median target (21-day RMS session RV)": f"{scored[b]['target'].median():.2f}",
                     "session RV^2 / close-to-close r^2 (means)": f"{share:.2f}",
                     "days": len(both)})
    P(md_table(pd.DataFrame(rows)))
    P("\nBlast radius: none on any published number; the two definitions belong to different holdouts and each "
      "holdout's claims compare models on its own target. The paper should state both definitions side by side.\n")

    # ---- Summary -----------------------------------------------------------------------------------
    P("## Summary\n")
    P(f"Class: {CLASS_POSTHOC} (counts of per-index RMSE verdicts that move when the affected days are removed).\n")
    for s in summary:
        P(f"- {s}")
    P("")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="ascii")
    print("\n".join(summary))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
