"""Post-hoc statistics from the reproduced holdout forecasts (October 2026 reopen, stage S2).

Class of every number printed here: "post hoc, computed from the reproduced forecasts; not a
registered test". The registered verdicts are the RMSE verdicts in docs/results/*.txt and
docs/WRITEUP.md; nothing here changes them. This script reads the scored forecast tables that
examples/reproduce_holdout.py saved under docs/results/reproductions/<holdout>/scored/ (the exact
forecasts and target the frozen scripts scored), checks that it recomputes every registered interval
to the printed digit (the identity check), and then writes docs/POSTHOC_2026-10.md with:

(a) the QLIKE verdict beside the RMSE verdict for every claim, and the claim outcome under each loss;
(b) equivalence bounds per asset, in percent of the reference loss, from the unrounded interval ends;
(c) a HAC Diebold-Mariano test (Bartlett kernel, lag 20) per row and a model confidence set per asset;
(d) block-length sensitivity (21 / 42 / 126-day circular blocks) and a stationary bootstrap (mean 63);
(e) raw next to recalibrated "own forecasts" of the HMM, the MSM, GJR-GARCH and MS-GARCH;
(f) the unregistered HMM-implied-vol vs HAR + VIX interval on both S&P 500 periods;
(g) the VIX script's own-row vs common-row calibration difference on both S&P 500 periods.

Run from the repo root with the network unplugged in spirit: it reads only the data caches.

    python examples/posthoc_stats.py [--out docs/POSTHOC_2026-10.md] [--n-boot 2000]
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

import regimes.data as data_mod  # noqa: E402
from regimes.forecast import forward_vol, har_features, qlike, walk_forward_regression  # noqa: E402
from regimes.posthoc import excluded_change_pct, hac_dm, mcs, paired_interval  # noqa: E402

from better_vol_models import CLAIMS as CROSS_CLAIMS  # noqa: E402
from cross_index_holdout import claim_verdict  # noqa: E402
from msgarch_credit import MS_CLAIMS, OTHER_CLAIMS, _slug  # noqa: E402
from regimes.evaluate import ewma_vol, realised_vol  # noqa: E402
from vol_forecast_vix import COMPARISONS as VIX_COMPARISONS  # noqa: E402
from vol_forecast_vix import PERIODS as VIX_PERIODS  # noqa: E402

REPRO = ROOT / "docs" / "results" / "reproductions"
CHECKPOINTS = ROOT / "data" / "checkpoints" / "msgarch_credit"
CLASS = "post hoc, computed from the reproduced forecasts; not a registered test"
H = 21
BLOCKS = (21, 42, 126)

ETF_CLAIMS = [(c, f.format(m="MS-GARCH"), r.format(m="MS-GARCH"), e) for c, f, r, e in MS_CLAIMS] + OTHER_CLAIMS

# holdout -> (reproduction folder, committed table to check against, claims, per-block scored table)
HOLDOUTS = {
    "cross_index": {
        "dir": "cross_index", "committed": ROOT / "docs/results/cross_index_holdout_2026-10-14.txt",
        "claims": CROSS_CLAIMS, "title": "Cross-index holdout (Nasdaq-100, Dow, Russell 2000; 2026-10-14)",
        "reference_own": "HAR-RV + IV",
    },
    "etf": {
        "dir": "etf_frozen_checkpoints", "committed": ROOT / "docs/results/msgarch_credit_holdout_2026-10-14.txt",
        "claims": ETF_CLAIMS, "title": "MS-GARCH and credit holdout (USO, GLD, EEM, EWZ; 2026-10-14)",
        "reference_own": "HAR + IV",
    },
}
VIX_HOLDOUTS = {"vix_early": "S&P 500, 1996-2004", "vix_recent": "S&P 500, 2024-2026"}


def verdict(lo: float, hi: float) -> str:
    return "better" if hi < 0 else "worse" if lo > 0 else "no difference"


def fmt_iv(lo: float, hi: float) -> str:
    return f"{lo:+.3f} to {hi:+.3f}"


def md_table(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        lines.append("| " + " | ".join(str(row[c]) for c in cols) + " |")
    return "\n".join(lines)


def git_head() -> str:
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True,
                               text=True, check=True).stdout.strip()
        return head + (" plus uncommitted files" if dirty else "")
    except Exception:  # noqa: BLE001
        return "unknown"


# ----------------------------------------------------------------------------------------------
# Inputs

def load_scored(folder: str) -> list[tuple[str, pd.DataFrame]]:
    """[(block name, scored table with 'target' and one column per forecast)] in saved order."""
    index = pd.read_json(REPRO / folder / "scored" / "index.json")
    out = []
    for _, entry in index.iterrows():
        df = pd.read_csv(REPRO / folder / "scored" / entry["file"], index_col=0, parse_dates=True)
        out.append((entry["block"], df))
    return out


def committed_intervals(path: Path, blocks: list[str]) -> dict[tuple[str, str], tuple[str, str, str, str]]:
    """{(block, claim id): (dRMSE text, RMSE verdict, dQLIKE text, QLIKE verdict)} from a committed
    result file (one '#####' section per asset, in the saved order)."""
    text = path.read_text()
    sections = [s for s in text.split("##### ")[1:] if not s.startswith("Claims across")]
    pat = re.compile(r"^\s*([A-Z]\d)\s+.+?\s+(better|not better)\s+([+-]\d\.\d{3} to [+-]\d\.\d{3})\s+"
                     r"(better|worse|no difference)\s+([+-]\d\.\d{3} to [+-]\d\.\d{3})\s+(better|worse|no difference)\s*$",
                     re.M)
    out = {}
    for block, section in zip(blocks, sections):
        assert section.startswith(block.split(" (")[0]), (block, section[:40])
        for m in pat.finditer(section):
            out[(block, m.group(1))] = (m.group(3), m.group(4), m.group(5), m.group(6))
    return out


def committed_vix_intervals(folder: str) -> dict[tuple[str, str], tuple[str, str, str, str]]:
    """The seven comparisons' intervals as printed by the reproduction of vol_forecast_vix.py."""
    text = (REPRO / folder / "stdout.txt").read_text()
    out = {}
    for name, ref in VIX_COMPARISONS:
        pat = re.compile(rf"^\s*{re.escape(name)}\s+{re.escape(ref)}\s+([+-]\d\.\d{{3}} to [+-]\d\.\d{{3}})\s+"
                         r"(better|worse|no difference)\s+([+-]\d\.\d{3} to [+-]\d\.\d{3})\s+(better|worse|no difference)\s*$", re.M)
        m = pat.search(text)
        assert m is not None, (folder, name, ref)
        out[(name, ref)] = m.groups()
    return out


# ----------------------------------------------------------------------------------------------
# One comparison row

def compare(df: pd.DataFrame, name: str, ref: str, n_boot: int) -> dict:
    y = df["target"].to_numpy()
    f, b = df[name].to_numpy(), df[ref].to_numpy()
    e_f, e_b = f - y, b - y
    q_f, q_b = qlike(f, y), qlike(b, y)
    ref_rmse, ref_qlike = float(np.sqrt((e_b ** 2).mean())), float(q_b.mean())
    row = {"n": len(y), "ref RMSE": ref_rmse, "ref QLIKE": ref_qlike,
           "RMSE": float(np.sqrt((e_f ** 2).mean())), "QLIKE": float(q_f.mean())}
    r_lo, r_hi = paired_interval(e_f, e_b, statistic="rmse", block=63, n_boot=n_boot)
    q_lo, q_hi = paired_interval(q_f, q_b, statistic="mean", block=63, n_boot=n_boot)
    row.update({"dRMSE lo": r_lo, "dRMSE hi": r_hi, "dQLIKE lo": q_lo, "dQLIKE hi": q_hi})
    row["RMSE bound"] = excluded_change_pct(r_lo, r_hi, ref_rmse)
    row["QLIKE bound"] = excluded_change_pct(q_lo, q_hi, ref_qlike)
    row["DM MSE"] = hac_dm(e_f ** 2, e_b ** 2, lag=20)
    row["DM QLIKE"] = hac_dm(q_f, q_b, lag=20)
    for blk in BLOCKS:
        row[f"RMSE c{blk}"] = verdict(*paired_interval(e_f, e_b, statistic="rmse", block=blk, n_boot=n_boot))
        row[f"QLIKE c{blk}"] = verdict(*paired_interval(q_f, q_b, statistic="mean", block=blk, n_boot=n_boot))
    row["RMSE s63"] = verdict(*paired_interval(e_f, e_b, statistic="rmse", scheme="stationary", block=63, n_boot=n_boot))
    row["QLIKE s63"] = verdict(*paired_interval(q_f, q_b, statistic="mean", scheme="stationary", block=63, n_boot=n_boot))
    return row


def equivalence(lo: float, hi: float, reference: float) -> str:
    v = verdict(lo, hi)
    if v == "no difference":
        return f"gain excluded above {100 * -lo / reference:.1f}%"
    if v == "better":
        return f"gain shown of at least {100 * -hi / reference:.1f}%"
    return f"loss shown of at least {100 * lo / reference:.1f}%"


def vix_claim_outcomes(v: dict[tuple[str, str], str]) -> dict[str, str]:
    """The three registered VIX claims from the seven comparison verdicts (VIX_HOLDOUT_PROTOCOL.md)."""
    better = {k for k, val in v.items() if val == "better"}
    worse = {k for k, val in v.items() if val == "worse"}
    a = ("HAR + VIX", "HAR") in better
    b = ("HAR + VIX + HMM prob", "HAR + VIX") not in better and ("HAR + VIX + VIX-HMM prob", "HAR + VIX") not in better
    c = ("HMM implied vol", "HAR") in worse and ("VIX-HMM implied vol", "HAR") in worse
    return {"A. VIX improves HAR": "holds" if a else "not shown",
            "B. regime adds nothing once the VIX is in": "holds" if b else "fails",
            "C. regime models' own forecasts lose to HAR": "holds" if c else "not shown"}


# ----------------------------------------------------------------------------------------------
# Sections

def section_claims(out: list[str], title: str, rows: list[dict], claims, blocks: list[str],
                   committed, identity: list[str], multi_asset: bool) -> dict:
    """Tables (a)-(d) for one holdout. ``rows`` has one dict per (block, claim) with the compare()
    result. Returns verdict dicts for the summary."""
    out.append(f"## {title}\n")
    out.append(f"Class: {CLASS}. Days scored per asset: " +
               ", ".join(f"{b} {next(r['n'] for r in rows if r['block'] == b):,}" for b in blocks) + ".\n")
    # (a)+(b): per row
    tab = []
    changes = 0
    for r in rows:
        key = (r["block"], r["id"]) if multi_asset else (r["forecast"], r["reference"])
        c = committed[key]
        r_text, q_text = fmt_iv(r["dRMSE lo"], r["dRMSE hi"]), fmt_iv(r["dQLIKE lo"], r["dQLIKE hi"])
        rv, qv = verdict(r["dRMSE lo"], r["dRMSE hi"]), verdict(r["dQLIKE lo"], r["dQLIKE hi"])
        same = (r_text, rv, q_text, qv) == tuple(c)
        identity.append(f"{title.split(' (')[0]} | {r['block']} | {r['id']} | {'identical' if same else 'DIFFERS: ' + str(c)}")
        changes += rv != qv
        tab.append({"claim": r["id"], "forecast vs reference": f"{r['forecast']} vs {r['reference']}",
                    "expected": r["expected"], "asset": r["block"],
                    "ref RMSE": f"{r['ref RMSE']:.3f}", "dRMSE 95%": r_text, "RMSE verdict": rv,
                    "RMSE bound": equivalence(r["dRMSE lo"], r["dRMSE hi"], r["ref RMSE"]),
                    "ref QLIKE": f"{r['ref QLIKE']:.3f}", "dQLIKE 95%": q_text, "QLIKE verdict": qv,
                    "QLIKE bound": equivalence(r["dQLIKE lo"], r["dQLIKE hi"], r["ref QLIKE"]),
                    "same?": "" if rv == qv else "changes"})
    out.append("### (a), (b) QLIKE beside RMSE, with equivalence bounds\n")
    out.append("The RMSE verdict column is the registered one (recomputed here to the printed digit, see the "
               "identity check at the top). The QLIKE interval was printed by the same frozen run as the "
               "registered secondary loss; the QLIKE verdict and every bound are post hoc. Bounds use the "
               "unrounded interval ends, in percent of the reference loss on the same days: for a \"no "
               "difference\" row, the largest improvement the interval still allows; for \"better\" or "
               "\"worse\", the smallest gain or loss it demonstrates.\n")
    out.append(md_table(pd.DataFrame(tab)) + "\n")
    out.append(f"Per-asset verdicts that change between the two losses: {changes} of {len(rows)}.\n")

    # claim outcomes under each loss and each block length
    verdict_cols = {"RMSE (registered, 63)": lambda r: verdict(r["dRMSE lo"], r["dRMSE hi"]),
                    "QLIKE (post hoc, 63)": lambda r: verdict(r["dQLIKE lo"], r["dQLIKE hi"])}
    for blk in BLOCKS:
        verdict_cols[f"RMSE c{blk}"] = lambda r, b=blk: r[f"RMSE c{b}"]
    verdict_cols["RMSE s63"] = lambda r: r["RMSE s63"]
    for blk in BLOCKS:
        verdict_cols[f"QLIKE c{blk}"] = lambda r, b=blk: r[f"QLIKE c{b}"]
    verdict_cols["QLIKE s63"] = lambda r: r["QLIKE s63"]

    outcomes = {}
    if multi_asset:
        tab = []
        for cid, f_name, ref, expected in claims:
            crow = {"claim": cid, "forecast vs reference": f"{f_name} vs {ref}", "expected": expected}
            for col, fn in verdict_cols.items():
                per = [fn(r) for r in rows if r["id"] == cid]
                crow[col] = claim_verdict(expected, per)
            tab.append(crow)
            outcomes[cid] = crow
    else:
        tab = []
        per_col = {}
        for col, fn in verdict_cols.items():
            per_col[col] = vix_claim_outcomes({(r["forecast"], r["reference"]): fn(r) for r in rows})
        for claim in next(iter(per_col.values())):
            crow = {"claim": claim}
            crow.update({col: per_col[col][claim] for col in verdict_cols})
            tab.append(crow)
            outcomes[claim] = crow
    out.append("### Claim outcomes under each loss and each bootstrap scheme\n")
    out.append("Columns: the registered scheme (63-day circular blocks), then circular blocks of 21, 42 and "
               "126 days and the stationary bootstrap with mean block 63 (s63), 2,000 draws, seed 0, "
               "for each loss. The claim rule is the protocols' (a \"better\" claim is confirmed if better on "
               "at least two counted assets and worse on none, rejected if better on none, mixed otherwise; "
               "a \"not better\" claim holds if better on none).\n" if multi_asset else
               "Columns as above. Claim A holds if HAR + VIX beats HAR; B holds if neither probability model "
               "beats HAR + VIX; C holds if both own forecasts are worse than HAR (VIX_HOLDOUT_PROTOCOL.md).\n")
    out.append(md_table(pd.DataFrame(tab)) + "\n")

    # (c) DM
    tab = []
    for r in rows:
        tab.append({"claim": r["id"], "asset": r["block"], "forecast vs reference": f"{r['forecast']} vs {r['reference']}",
                    "dMSE mean": f"{r['DM MSE']['mean_diff']:+.4f}", "DM stat (MSE)": f"{r['DM MSE']['stat']:+.2f}",
                    "p (MSE)": f"{r['DM MSE']['p']:.3f}",
                    "dQLIKE mean": f"{r['DM QLIKE']['mean_diff']:+.4f}", "DM stat (QLIKE)": f"{r['DM QLIKE']['stat']:+.2f}",
                    "p (QLIKE)": f"{r['DM QLIKE']['p']:.3f}",
                    "bootstrap RMSE / QLIKE": f"{verdict(r['dRMSE lo'], r['dRMSE hi'])} / {verdict(r['dQLIKE lo'], r['dQLIKE hi'])}"})
    out.append("### (c) HAC Diebold-Mariano, lag 20\n")
    out.append("Diebold and Mariano (1995) on the per-day loss difference with a Bartlett-kernel long-run "
               "variance truncated at 20 lags (the 21-day targets overlap, so the errors are MA(20) under "
               "the null). For RMSE the test is on the squared error (MSE), whose sign agrees with the RMSE "
               "difference; two-sided normal p-values. The last column repeats the bootstrap verdicts for "
               "comparison: a p below 0.05 and a bootstrap interval off zero should agree in sign.\n")
    out.append(md_table(pd.DataFrame(tab)) + "\n")
    agree = sum((r["DM MSE"]["p"] < 0.05) == (verdict(r["dRMSE lo"], r["dRMSE hi"]) != "no difference") for r in rows)
    agree_q = sum((r["DM QLIKE"]["p"] < 0.05) == (verdict(r["dQLIKE lo"], r["dQLIKE hi"]) != "no difference") for r in rows)
    out.append(f"DM at 5% and the bootstrap interval agree on significance in {agree} of {len(rows)} RMSE rows "
               f"and {agree_q} of {len(rows)} QLIKE rows.\n")

    # (d) sensitivity counts
    tab = []
    for loss, key in (("RMSE", "dRMSE"), ("QLIKE", "dQLIKE")):
        reg = [verdict(r[f"{key} lo"], r[f"{key} hi"]) for r in rows]
        for scheme in [f"c{b}" for b in BLOCKS] + ["s63"]:
            alt = [r[f"{loss} {scheme}"] for r in rows]
            moved = [f"{r['id']} {r['block']} ({a} -> {b})" for r, a, b in zip(rows, reg, alt) if a != b]
            tab.append({"loss": loss, "scheme": scheme, "verdicts changed": f"{len(moved)} of {len(rows)}",
                        "which": "; ".join(moved) if moved else ""})
    out.append("### (d) Block-length sensitivity\n")
    out.append("Per-asset verdicts under each alternative bootstrap against the registered 63-day circular "
               "blocks. c = circular block of that length; s63 = stationary bootstrap (Politis and Romano "
               "1994) with mean block 63.\n")
    out.append(md_table(pd.DataFrame(tab)) + "\n")
    return outcomes


def losers_kept(rows: list[dict], in_set: dict[str, dict[str, bool]]) -> list[dict]:
    """Decisive registered pairs whose losing forecast the MCS still keeps.

    ``rows`` are comparison rows from ``compare`` (forecast, reference and the unrounded interval ends);
    ``in_set`` maps "RMSE" (the MCS on squared error) and "QLIKE" to {forecast: membership}. A pair is
    decisive under a loss if its 95% interval excludes zero; the loser is the forecast on the worse side.
    The pair tests one forecast against one reference; the T_max MCS tests each forecast against the
    average of the set, so a forecast can lose its pair and stay in the set.
    """
    out = []
    for r in rows:
        for loss, lo, hi in (("RMSE", r["dRMSE lo"], r["dRMSE hi"]), ("QLIKE", r["dQLIKE lo"], r["dQLIKE hi"])):
            v = verdict(lo, hi)
            if v == "no difference":
                continue
            loser = r["forecast"] if v == "worse" else r["reference"]
            out.append({"id": r["id"], "pair": f"{r['forecast']} vs {r['reference']}", "loss": loss,
                        "verdict": v, "loser": loser, "loser in set": bool(in_set[loss][loser])})
    return out


def section_mcs(out: list[str], blocks: list[tuple[str, pd.DataFrame]], n_boot: int, drop: tuple = (),
                pairs: dict[str, list[dict]] | None = None) -> tuple[int, int]:
    out.append("### (c) Model confidence set per asset, 10%\n")
    out.append("Hansen, Lunde and Nason (2011) with the T_max statistic and the holdouts' 63-day circular "
               "block bootstrap (2,000 draws, seed 0), over every forecast in the scored table. A model is "
               "in the set if its MCS p-value is at least 0.10. The set is the group of forecasts that the "
               "data cannot separate from the best; it replaces nothing in the registered claim rule.\n")
    n_dec = n_kept_all = 0
    for block, df in blocks:
        names = [c for c in df.columns if c != "target" and c not in drop]
        y = df["target"].to_numpy()
        F = df[names].to_numpy()
        se = (F - y[:, None]) ** 2
        ql = np.column_stack([qlike(F[:, j], y) for j in range(len(names))])
        r_se, r_ql = mcs(se, alpha=0.10, block=63, n_boot=n_boot), mcs(ql, alpha=0.10, block=63, n_boot=n_boot)
        order = np.argsort(se.mean(axis=0), kind="stable")
        tab = pd.DataFrame({"forecast": [names[j] for j in order],
                            "RMSE": [f"{v:.3f}" for v in np.sqrt(se.mean(axis=0))[order]],
                            "MCS p (MSE)": [f"{v:.3f}" for v in r_se["p_value"][order]],
                            "in set (MSE)": np.where(r_se["in_set"][order], "yes", ""),
                            "QLIKE": [f"{v:.3f}" for v in ql.mean(axis=0)[order]],
                            "MCS p (QLIKE)": [f"{v:.3f}" for v in r_ql["p_value"][order]],
                            "in set (QLIKE)": np.where(r_ql["in_set"][order], "yes", "")})
        label = block if block else "all forecasts"
        out.append(f"**{label}**, {len(y):,} days: MSE set has {int(r_se['in_set'].sum())} of {len(names)} forecasts, "
                   f"QLIKE set {int(r_ql['in_set'].sum())} of {len(names)}.\n")
        out.append(md_table(tab) + "\n")
        if pairs is not None and pairs.get(block):
            kept = losers_kept(pairs[block], {
                "RMSE": dict(zip(names, r_se["in_set"])), "QLIKE": dict(zip(names, r_ql["in_set"]))})
            n_kept = sum(k["loser in set"] for k in kept)
            n_dec += len(kept)
            n_kept_all += n_kept
            out.append(f"Registered pairs on {label} with a 95% interval that excludes zero: {len(kept)}; the "
                       f"losing forecast is still in the 10% MCS in {n_kept} of them. MCS membership is therefore "
                       "not read as parity with the reference.\n")
            if kept:
                out.append(md_table(pd.DataFrame([{**k, "loser in set": "yes" if k["loser in set"] else ""}
                                                  for k in kept])) + "\n")
    return n_dec, n_kept_all


def section_raw_vs_calibrated(out: list[str], label: str, scored: pd.DataFrame, raw: dict[str, pd.Series],
                              reference: str, n_boot: int, note: str = "") -> None:
    """(e): the model's raw implied vol beside its recalibrated forecast, on the scored days."""
    y = scored["target"]
    tab = []
    for name, raw_series in raw.items():
        r = raw_series.reindex(scored.index)
        ok = r.notna()
        yy, rr, cc, bb = y[ok].to_numpy(), r[ok].to_numpy(), scored.loc[ok, name].to_numpy(), scored.loc[ok, reference].to_numpy()
        row = {"model": name, "days": int(ok.sum()),
               "raw RMSE": f"{np.sqrt(((rr - yy) ** 2).mean()):.3f}", "calibrated RMSE": f"{np.sqrt(((cc - yy) ** 2).mean()):.3f}",
               "raw QLIKE": f"{qlike(rr, yy).mean():.3f}", "calibrated QLIKE": f"{qlike(cc, yy).mean():.3f}",
               "raw mean / target mean": f"{rr.mean():.2f} / {yy.mean():.2f}"}
        lo, hi = paired_interval(rr - yy, cc - yy, statistic="rmse", block=63, n_boot=n_boot)
        row["dRMSE raw - calibrated"] = f"{fmt_iv(lo, hi)} ({'raw ' + verdict(lo, hi) if verdict(lo, hi) != 'no difference' else 'no difference'})"
        lo, hi = paired_interval(qlike(rr, yy), qlike(cc, yy), statistic="mean", block=63, n_boot=n_boot)
        row["dQLIKE raw - calibrated"] = f"{fmt_iv(lo, hi)} ({'raw ' + verdict(lo, hi) if verdict(lo, hi) != 'no difference' else 'no difference'})"
        lo, hi = paired_interval(rr - yy, bb - yy, statistic="rmse", block=63, n_boot=n_boot)
        row[f"raw vs {reference}, dRMSE"] = f"{fmt_iv(lo, hi)} {verdict(lo, hi)}"
        lo, hi = paired_interval(qlike(rr, yy), qlike(bb, yy), statistic="mean", block=63, n_boot=n_boot)
        row[f"raw vs {reference}, dQLIKE"] = f"{fmt_iv(lo, hi)} {verdict(lo, hi)}"
        tab.append(row)
    out.append(f"**{label}**" + (f" ({note})" if note else "") + "\n")
    out.append(md_table(pd.DataFrame(tab)) + "\n")


def vix_features(period: str) -> tuple[pd.Series, dict[str, pd.DataFrame | pd.Series], dict[str, pd.Series], str | None]:
    """Rebuild the VIX script's feature sets for one holdout period from the data cache and the saved
    walk-forward HMM outputs, exactly as examples/vol_forecast_vix.py builds them."""
    start, end, score_from = VIX_PERIODS[period]
    returns = data_mod.load_index_returns(start=start, end=end)
    vix = data_mod.load_vix(start, end)
    common = returns.index.intersection(vix.index)
    returns, vix = returns.loc[common], vix.loc[common]
    folder = REPRO / {"early": "vix_early", "recent": "vix_recent"}[period] / "walk_forwards"

    def wf(stem: str, col: str) -> pd.Series:
        s = pd.read_csv(folder / f"{stem}__{col}.csv", index_col=0, parse_dates=True).iloc[:, 0]
        return s.rename(col)

    hmm_prob, hmm_iv = wf("walk_forward_oos_001", "high_vol_prob"), wf("walk_forward_oos_001", "implied_vol")
    vx_prob, vx_iv = wf("walk_forward_vix_hmm_002", "high_vol_prob"), wf("walk_forward_vix_hmm_002", "implied_vol")
    target = forward_vol(returns, H)
    har = har_features(returns)
    vix_daily = (vix / np.sqrt(252)).rename("vix")
    log_har = np.log(har.clip(lower=1e-3))
    log_vix = np.log(vix_daily)
    raw = {"HMM implied vol": hmm_iv, "VIX-HMM implied vol": vx_iv, "EWMA vol (0.94)": ewma_vol(returns),
           "trailing 21-day vol": realised_vol(returns, 21), "VIX": vix_daily}
    feature_sets = {
        "HMM high-vol probability": hmm_prob,
        "HMM implied vol": np.log(hmm_iv),
        "VIX-HMM implied vol": np.log(vx_iv),
        "EWMA vol (0.94)": np.log(raw["EWMA vol (0.94)"]),
        "trailing 21-day vol": np.log(raw["trailing 21-day vol"]),
        "HAR": log_har,
        "VIX": log_vix,
        "HAR + VIX": log_har.join(log_vix),
        "HAR + HMM prob": log_har.join(hmm_prob),
        "HAR + VIX + HMM prob": log_har.join(log_vix).join(hmm_prob),
        "HAR + VIX + VIX-HMM prob": log_har.join(log_vix).join(vx_prob),
    }
    return target, feature_sets, raw, score_from


def section_common_rows(out: list[str], folder: str, period: str, scored: pd.DataFrame, n_boot: int) -> list[str]:
    """(g): recalibrate every VIX feature set on the rows common to all of them, as the other two
    holdout scripts do, and compare with the registered own-row calibration. Returns identity lines."""
    target, feature_sets, _raw, score_from = vix_features(period)
    own = {name: walk_forward_regression(target, X, horizon=H, step=63, min_rows=756, log_target=True).forecast
           for name, X in feature_sets.items()}
    joined_own = pd.concat({"y": target, **own}, axis=1, sort=True).dropna()
    if score_from is not None:
        joined_own = joined_own.loc[score_from:]
    identity = []
    same_days = joined_own.index.equals(scored.index)
    diff = float(np.abs(joined_own[list(own)].to_numpy() - scored[list(own)].to_numpy()).max()) if same_days else float("nan")
    identity.append(f"{folder} | own-row recalibration from the saved HMM outputs | "
                    f"{'identical days, max abs forecast diff ' + format(diff, '.2e') if same_days else 'DIFFERENT scored days'}")
    common = pd.concat(feature_sets.values(), axis=1, sort=True).dropna().index
    comm = {name: walk_forward_regression(target, X.reindex(common), horizon=H, step=63, min_rows=756,
                                          log_target=True).forecast for name, X in feature_sets.items()}
    joined_comm = pd.concat({"y": target, **comm}, axis=1, sort=True).dropna()
    if score_from is not None:
        joined_comm = joined_comm.loc[score_from:]
    days = joined_own.index.intersection(joined_comm.index)
    y = joined_own.loc[days, "y"].to_numpy()
    first_own = {n: own[n].index.min().date() for n in ("HAR", "HAR + VIX", "HAR + VIX + HMM prob")}
    out.append(f"**{VIX_HOLDOUTS[folder]}**: own-row first forecast dates HAR {first_own['HAR']}, HAR + VIX "
               f"{first_own['HAR + VIX']}, HAR + VIX + HMM prob {first_own['HAR + VIX + HMM prob']}; common-row first "
               f"forecast date {comm['HAR'].index.min().date()} for every set; first training row on common rows "
               f"{common.min().date()} (own rows: {feature_sets['HAR'].dropna().index.min().date()} for HAR). "
               f"Scored days: {len(scored):,} registered, {len(days):,} common to both calibrations.\n")
    tab = []
    for name in feature_sets:
        o, c = joined_own.loc[days, name].to_numpy(), joined_comm.loc[days, name].to_numpy()
        lo, hi = paired_interval(o - y, c - y, statistic="rmse", block=63, n_boot=n_boot)
        qlo, qhi = paired_interval(qlike(o, y), qlike(c, y), statistic="mean", block=63, n_boot=n_boot)
        tab.append({"forecast": name, "RMSE own rows": f"{np.sqrt(((o - y) ** 2).mean()):.4f}",
                    "RMSE common rows": f"{np.sqrt(((c - y) ** 2).mean()):.4f}",
                    "dRMSE own - common": f"{fmt_iv(lo, hi)} {verdict(lo, hi)}",
                    "QLIKE own rows": f"{qlike(o, y).mean():.4f}", "QLIKE common rows": f"{qlike(c, y).mean():.4f}",
                    "dQLIKE own - common": f"{fmt_iv(qlo, qhi)} {verdict(qlo, qhi)}"})
    out.append(md_table(pd.DataFrame(tab)) + "\n")
    tab = []
    for name, ref in VIX_COMPARISONS:
        f_o, b_o = joined_own.loc[days, name].to_numpy(), joined_own.loc[days, ref].to_numpy()
        f_c, b_c = joined_comm.loc[days, name].to_numpy(), joined_comm.loc[days, ref].to_numpy()
        ro = paired_interval(f_o - y, b_o - y, statistic="rmse", block=63, n_boot=n_boot)
        rc = paired_interval(f_c - y, b_c - y, statistic="rmse", block=63, n_boot=n_boot)
        qo = paired_interval(qlike(f_o, y), qlike(b_o, y), statistic="mean", block=63, n_boot=n_boot)
        qc = paired_interval(qlike(f_c, y), qlike(b_c, y), statistic="mean", block=63, n_boot=n_boot)
        tab.append({"forecast vs reference": f"{name} vs {ref}",
                    "dRMSE own rows": f"{fmt_iv(*ro)} {verdict(*ro)}", "dRMSE common rows": f"{fmt_iv(*rc)} {verdict(*rc)}",
                    "dQLIKE own rows": f"{fmt_iv(*qo)} {verdict(*qo)}", "dQLIKE common rows": f"{fmt_iv(*qc)} {verdict(*qc)}",
                    "verdict moves": "" if (verdict(*ro), verdict(*qo)) == (verdict(*rc), verdict(*qc)) else "yes"})
    out.append("The seven comparisons under each calibration, on the days common to both:\n")
    out.append(md_table(pd.DataFrame(tab)) + "\n")
    claims_own = vix_claim_outcomes({(n, r): verdict(*paired_interval(joined_own.loc[days, n].to_numpy() - y, joined_own.loc[days, r].to_numpy() - y, statistic="rmse", block=63, n_boot=n_boot)) for n, r in VIX_COMPARISONS})
    claims_comm = vix_claim_outcomes({(n, r): verdict(*paired_interval(joined_comm.loc[days, n].to_numpy() - y, joined_comm.loc[days, r].to_numpy() - y, statistic="rmse", block=63, n_boot=n_boot)) for n, r in VIX_COMPARISONS})
    out.append("RMSE claim outcomes, own rows (registered) vs common rows: " +
               "; ".join(f"{k}: {claims_own[k]} vs {claims_comm[k]}" for k in claims_own) + ".\n")
    return identity


# ----------------------------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "docs" / "POSTHOC_2026-10.md"))
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()
    n_boot = args.n_boot

    def no_network(*a, **k):
        raise RuntimeError("posthoc_stats.py reads only the data caches; a download was attempted")
    import types
    sys.modules["yfinance"] = types.SimpleNamespace(download=no_network)  # data.py imports it lazily

    out: list[str] = []
    identity: list[str] = []
    summary: list[str] = []

    out.append("# Post-hoc statistics from the reproduced holdout forecasts, October 2026\n")
    out.append(f"Class of every table in this file: **{CLASS}**. The registered verdicts are the RMSE verdicts "
               "in `docs/results/cross_index_holdout_2026-10-14.txt`, `docs/results/msgarch_credit_holdout_2026-10-14.txt` "
               "and the VIX tables in `docs/WRITEUP.md`; nothing here changes them, and no sentence here "
               "says a reproduction confirms or re-tests a claim.\n")
    out.append(f"Written by `examples/posthoc_stats.py` at {git_head()}, {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, "
               f"with {n_boot:,} bootstrap draws (seed 0). Inputs: the scored forecast tables under "
               "`docs/results/reproductions/<holdout>/scored/` written by `examples/reproduce_holdout.py` on "
               "2026-10-17 (the exact forecasts and target the frozen scripts scored; the ETF tables are the "
               "frozen MS-GARCH, GJR and HMM checkpoints re-scored, which the S1 reproduction showed identical to "
               "the committed file), the saved walk-forward implied vols beside them, and the data caches "
               "listed in `data/MANIFEST.md`. A laptop draft of tables (a) and (b) from the printed 3-decimal "
               "intervals (`QLIKE_EQUIVALENCE_TABLES_DRAFT_2026-10-17.md`, desk review) widened each bound by "
               "0.0005; the bounds here use the unrounded interval ends and are therefore a little tighter.\n")
    out.append("Desk and panel items this answers: panel item 4 and ranked items 2-4 (HAC DM, MCS, equivalence "
               "bounds, block length), desk findings 3, 6, 7 and 9 of `HMM_DESK_REVIEW_2026-10-17.md` "
               "(QLIKE beside RMSE, own-row calibration, raw vs recalibrated, what the null is entitled to), "
               "and the unregistered HMM-vs-HAR + VIX comparison of desk finding 1.\n")

    body: list[str] = []
    all_rows = {}
    mcs_counts: dict[str, tuple[int, int]] = {}

    # Multi-asset holdouts
    for key, spec in HOLDOUTS.items():
        blocks = load_scored(spec["dir"])
        names = [b for b, _ in blocks]
        committed = committed_intervals(spec["committed"], names)
        rows = []
        for block, df in blocks:
            for cid, f_name, ref, expected in spec["claims"]:
                r = compare(df, f_name, ref, n_boot)
                r.update({"id": cid, "forecast": f_name, "reference": ref, "expected": expected, "block": block})
                rows.append(r)
        all_rows[key] = rows
        outcomes = section_claims(body, spec["title"], rows, spec["claims"], names, committed, identity, True)
        mcs_counts[key] = section_mcs(body, blocks, n_boot,
                                      pairs={blk: [r for r in rows if r["block"] == blk] for blk in names})
        moved = [f"{c} ({o['RMSE (registered, 63)']} -> {o['QLIKE (post hoc, 63)']})" for c, o in outcomes.items()
                 if o["RMSE (registered, 63)"] != o["QLIKE (post hoc, 63)"]]
        summary.append(f"{spec['title'].split(' (')[0]}: claim outcomes that change under QLIKE: "
                       f"{', '.join(moved) if moved else 'none'}.")
        print(f"{key}: {len(rows)} rows; outcomes changed under QLIKE: {moved}", flush=True)

    # VIX holdouts
    vix_rows = {}
    for folder, period in (("vix_early", "early"), ("vix_recent", "recent")):
        blocks = load_scored(folder)
        raw_tab, cal_tab = blocks[0][1], blocks[1][1]
        committed = committed_vix_intervals(folder)
        rows = []
        for name, ref in VIX_COMPARISONS:
            r = compare(cal_tab, name, ref, n_boot)
            r.update({"id": f"{VIX_COMPARISONS.index((name, ref)) + 1}", "forecast": name, "reference": ref,
                      "expected": "better" if ref == "HAR" and name in ("VIX", "HAR + VIX") else "worse" if "implied vol" in name else "not better",
                      "block": VIX_HOLDOUTS[folder]})
            rows.append(r)
        vix_rows[folder] = (rows, raw_tab, cal_tab, committed, period)
        outcomes = section_claims(body, f"{VIX_HOLDOUTS[folder]} VIX holdout (examples/vol_forecast_vix.py --period {period})",
                                  rows, None, [VIX_HOLDOUTS[folder]], committed, identity, False)
        mcs_counts[folder] = section_mcs(body, [("", cal_tab)], n_boot, pairs={"": rows})
        moved = [f"{c} ({o['RMSE (registered, 63)']} -> {o['QLIKE (post hoc, 63)']})" for c, o in outcomes.items()
                 if o["RMSE (registered, 63)"] != o["QLIKE (post hoc, 63)"]]
        summary.append(f"{VIX_HOLDOUTS[folder]}: claim outcomes that change under QLIKE: {', '.join(moved) if moved else 'none'}.")
        print(f"{folder}: outcomes changed under QLIKE: {moved}", flush=True)

    # (e) raw vs calibrated
    body.append("## (e) Raw next to recalibrated own forecasts\n")
    body.append(f"Class: {CLASS}. Every \"own forecast\" in the result tables is the model's implied vol pushed "
                "through the same log-scale walk-forward regression as the other signals (desk finding 7: "
                "that regression is fit by least squares in logs, which is neither RMSE on vol nor QLIKE on "
                "variance, so it need not help a model on both losses). Here the raw implied vol is scored on "
                "the same days, beside its calibrated version and against the claim's reference. The "
                "\"raw - calibrated\" intervals are paired 63-day block bootstraps; \"raw better\" means the "
                "calibration hurt the model on that loss.\n")
    for folder in ("vix_early", "vix_recent"):
        rows, raw_tab, cal_tab, committed, period = vix_rows[folder]
        raw = {c: raw_tab[c] for c in raw_tab.columns if c != "target"}
        section_raw_vs_calibrated(body, VIX_HOLDOUTS[folder], cal_tab, raw, "HAR", n_boot,
                                  note="raw table printed by the frozen script, reference HAR as in comparisons 6 and 7")
    # cross-index: raw walk-forward implied vols, saved beside the scored tables
    ci_blocks = load_scored("cross_index")
    stems = {"Two-state HMM implied vol": "walk_forward_oos_{:03d}", "GJR-GARCH": "walk_forward_gjr_{:03d}",
             "MSM": "walk_forward_msm_{:03d}"}
    for i, (block, df) in enumerate(ci_blocks):
        raw = {}
        for name, stem in stems.items():
            k = 3 * i + {"Two-state HMM implied vol": 1, "GJR-GARCH": 2, "MSM": 3}[name]
            raw[name] = pd.read_csv(REPRO / "cross_index" / "walk_forwards" / (stem.format(k) + "__implied_vol.csv"),
                                    index_col=0, parse_dates=True).iloc[:, 0]
        section_raw_vs_calibrated(body, f"Cross-index, {block}", df, raw, "HAR-RV + IV", n_boot,
                                  note="raw implied vols are close-to-close daily vol; the target is the 21-session RMS of "
                                       "5-minute RV (no overnight), so the raw numbers forecast a different scale and the "
                                       "calibration also does the scale change")
    etf_blocks = load_scored("etf_frozen_checkpoints")
    for block, df in etf_blocks:
        raw = {}
        for name, model in (("Two-state HMM implied vol", "hmm"), ("GJR-GARCH", "garch"), ("MS-GARCH", "ms_garch")):
            path = next(CHECKPOINTS.glob(f"{_slug(block)}__{model}__2026-10-12__*.csv"))
            if path.name.endswith(".params.csv"):
                path = next(p for p in CHECKPOINTS.glob(f"{_slug(block)}__{model}__2026-10-12__*.csv") if not p.name.endswith(".params.csv"))
            raw[name] = pd.read_csv(path, index_col=0, parse_dates=True)["implied_vol"]
        section_raw_vs_calibrated(body, f"ETF, {block}", df, raw, "HAR + IV", n_boot,
                                  note="raw implied vols from the frozen checkpoints in data/checkpoints/msgarch_credit/")

    # (f) HMM implied vol vs HAR + VIX
    body.append("## (f) The unregistered comparison: regime models' own forecasts vs HAR + VIX, S&P 500\n")
    body.append(f"Class: {CLASS}. The registered comparison 6 is HMM implied vol vs HAR without the VIX "
                "(VIX_HOLDOUT_PROTOCOL.md); the README's \"every holdout but one\" sentence reads as if it were "
                "against HAR + VIX (desk finding 1). This is that interval, computed the same way.\n")
    tab = []
    for folder in ("vix_early", "vix_recent"):
        rows, raw_tab, cal_tab, committed, period = vix_rows[folder]
        for name in ("HMM implied vol", "VIX-HMM implied vol"):
            r = compare(cal_tab, name, "HAR + VIX", n_boot)
            tab.append({"period": VIX_HOLDOUTS[folder], "forecast vs reference": f"{name} vs HAR + VIX",
                        "RMSE / ref": f"{r['RMSE']:.3f} / {r['ref RMSE']:.3f}",
                        "dRMSE 95%": f"{fmt_iv(r['dRMSE lo'], r['dRMSE hi'])} {verdict(r['dRMSE lo'], r['dRMSE hi'])}",
                        "RMSE bound": equivalence(r["dRMSE lo"], r["dRMSE hi"], r["ref RMSE"]),
                        "QLIKE / ref": f"{r['QLIKE']:.3f} / {r['ref QLIKE']:.3f}",
                        "dQLIKE 95%": f"{fmt_iv(r['dQLIKE lo'], r['dQLIKE hi'])} {verdict(r['dQLIKE lo'], r['dQLIKE hi'])}",
                        "QLIKE bound": equivalence(r["dQLIKE lo"], r["dQLIKE hi"], r["ref QLIKE"]),
                        "DM p (MSE / QLIKE)": f"{r['DM MSE']['p']:.3f} / {r['DM QLIKE']['p']:.3f}"})
    body.append(md_table(pd.DataFrame(tab)) + "\n")
    n_dec, n_kept = (sum(v[i] for v in mcs_counts.values()) for i in (0, 1))
    summary.append(f"(c) MCS vs the registered pairs: of {n_dec} pair-loss intervals that exclude zero, the losing "
                   f"forecast stays in the 10% MCS in {n_kept} ("
                   + ", ".join(f"{k} {v[1]} of {v[0]}" for k, v in mcs_counts.items())
                   + "); MCS membership is not read as parity.")
    summary.append("(f) HMM implied vol vs HAR + VIX: " + "; ".join(f"{t['period']} {t['dRMSE 95%']} on RMSE, {t['dQLIKE 95%']} on QLIKE" for t in tab if t["forecast vs reference"].startswith("HMM")) + ".")

    # (g) own rows vs common rows
    body.append("## (g) Own-row vs common-row calibration in the VIX script\n")
    body.append(f"Class: {CLASS}. `examples/vol_forecast_vix.py` fits each feature set's calibration on the rows "
                "where that set exists, so HAR and HAR + VIX train on about three more years than the sets that "
                "include an HMM probability, and the HMM's own forecast trains on three fewer years than the HAR "
                "it is compared with (desk finding 6, sized there on development data only). The other two "
                "holdout scripts reindex every set to the common rows. Here every set is recalibrated on the "
                "common rows from the saved walk-forward HMM outputs and the cached data, after checking that the "
                "own-row recalibration reproduces the registered forecasts.\n")
    for folder, period in (("vix_early", "early"), ("vix_recent", "recent")):
        rows, raw_tab, cal_tab, committed, period = vix_rows[folder]
        identity += section_common_rows(body, folder, period, cal_tab, n_boot)
        print(f"{folder}: common-row section done", flush=True)

    # Identity check, placed first
    n_diff = sum("DIFFERS" in line or "DIFFERENT" in line for line in identity)
    out.append("## Identity check: the registered intervals recomputed from the saved tables\n")
    out.append("Class: reproduction. Each registered RMSE and QLIKE interval (63-day circular blocks, 2,000 draws, "
               "seed 0) recomputed from the scored table and compared, as printed text, with the committed "
               "result file (cross-index, ETF) or the reproduction's stdout (VIX, whose intervals match "
               "`docs/WRITEUP.md`, see `examples/check_writeup_tables.py`). The last two lines check that the "
               "own-row recalibration in (g) reproduces the registered VIX forecasts from the saved HMM outputs.\n")
    out.append(f"Result: {len(identity) - n_diff} of {len(identity)} identical, {n_diff} differ.\n")
    out.append("```\n" + "\n".join(identity) + "\n```\n")
    out.append("## Summary\n")
    out.append("\n".join(f"- {s}" for s in summary) + "\n")
    out.extend(body)

    text = "\n".join(out)
    assert text.isascii(), "non-ASCII output"
    Path(args.out).write_text(text)
    print(f"identity: {len(identity) - n_diff} of {len(identity)} identical, {n_diff} differ")
    for s in summary:
        print(s)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
