"""Power and multiple testing for every registered holdout comparison (October 2026 reopen, stage S7).

Post hoc, computed from the reproduced forecasts; not a registered test. Writes two files:

- ``docs/POWER_2026-10.md`` (S7 a): for every registered per-asset comparison (both S&P VIX holdouts,
  the cross-index and ETF holdouts, the stock-bond level rules) the registered interval, the
  equivalence bound in percent of the reference loss under RMSE and QLIKE, the scored-day count and
  the count of non-overlapping target windows, and "what this holdout could decide": the half-width of
  the interval in percent of the reference loss, i.e. the smallest true difference that an interval of
  this width, centred on it, would have shown. One sentence per registered claim.
- ``docs/MULTIPLE_TESTING_2026-10.md`` (S7 b): the registered families counted by name, a two-sided
  p-value per comparison (the registered bootstrap inverted, and a HAC Diebold-Mariano test), Holm
  within each family and across all registered tests, under both losses, and the claim outcomes when
  every verdict that does not survive Holm is read as "no difference". No verdict changes: the
  registered rule stays the verdict.

Inputs are the scored tables under ``docs/results/reproductions/<holdout>/scored/`` (the exact forecasts
the frozen scripts scored; ETF = the frozen checkpoints re-scored) and, for the stock-bond holdout, which
saved no forecasts, the four intervals printed in its reproduced stdout. The registered interval is
recomputed from the scored tables and checked against the committed text before anything else is
printed. Nothing here downloads data.

    python examples/power_multiplicity.py               # about 5 minutes
    python examples/power_multiplicity.py --n-boot-p 2000   # a quick smoke
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

import posthoc_stats as ph  # noqa: E402
from cross_index_holdout import claim_verdict  # noqa: E402
from regimes.forecast import qlike  # noqa: E402
from regimes.posthoc import bootstrap_p_value, hac_dm, holm, paired_draws, paired_interval  # noqa: E402
from vol_forecast_vix import COMPARISONS as VIX_COMPARISONS  # noqa: E402

CLASS = ph.CLASS
ALPHA = 0.05
H = 21

VIX_CLAIM_OF = {("HAR + VIX", "HAR"): "A", ("HAR + VIX + HMM prob", "HAR + VIX"): "B",
                ("HAR + VIX + VIX-HMM prob", "HAR + VIX"): "B", ("HMM implied vol", "HAR"): "C",
                ("VIX-HMM implied vol", "HAR"): "C"}
VIX_EXPECTED = {("VIX", "HAR"): "better", ("HAR + VIX", "HAR"): "better", ("HAR + HMM prob", "HAR"): "not better",
                ("HAR + VIX + HMM prob", "HAR + VIX"): "not better",
                ("HAR + VIX + VIX-HMM prob", "HAR + VIX"): "not better",
                ("HMM implied vol", "HAR"): "worse", ("VIX-HMM implied vol", "HAR"): "worse"}


def interval_p_normal(lo: float, hi: float) -> float:
    """Two-sided p-value read off a printed 95% interval by a normal approximation (used only for the
    stock-bond rules, whose forecasts were not saved)."""
    import math
    se = (hi - lo) / (2 * 1.959964)
    z = (lo + hi) / 2 / se
    return math.erfc(abs(z) / math.sqrt(2.0))


def half_width_pct(lo: float, hi: float, ref: float) -> float:
    return 100.0 * (hi - lo) / 2.0 / ref


def row_stats(df: pd.DataFrame, name: str, ref: str, n_boot: int, n_boot_p: int) -> dict:
    y = df["target"].to_numpy()
    e_f, e_b = df[name].to_numpy() - y, df[ref].to_numpy() - y
    q_f, q_b = qlike(df[name].to_numpy(), y), qlike(df[ref].to_numpy(), y)
    r = {"n": len(y), "ref RMSE": float(np.sqrt((e_b ** 2).mean())), "ref QLIKE": float(q_b.mean())}
    r["r_lo"], r["r_hi"] = paired_interval(e_f, e_b, statistic="rmse", block=63, n_boot=n_boot)
    r["q_lo"], r["q_hi"] = paired_interval(q_f, q_b, statistic="mean", block=63, n_boot=n_boot)
    r["p boot RMSE"] = bootstrap_p_value(paired_draws(e_f, e_b, statistic="rmse", block=63, n_boot=n_boot_p))
    r["p boot QLIKE"] = bootstrap_p_value(paired_draws(q_f, q_b, statistic="mean", block=63, n_boot=n_boot_p))
    r["p DM RMSE"] = hac_dm(e_f ** 2, e_b ** 2, lag=20)["p"]
    r["p DM QLIKE"] = hac_dm(q_f, q_b, lag=20)["p"]
    return r


def collect(n_boot: int, n_boot_p: int) -> tuple[list[dict], list[str]]:
    rows: list[dict] = []
    identity: list[str] = []
    for key, spec in ph.HOLDOUTS.items():
        blocks = ph.load_scored(spec["dir"])
        committed = ph.committed_intervals(spec["committed"], [b for b, _ in blocks])
        family = "cross-index per-index verdicts" if key == "cross_index" else "ETF per-asset verdicts"
        for block, df in blocks:
            for cid, f_name, ref, expected in spec["claims"]:
                r = row_stats(df, f_name, ref, n_boot, n_boot_p)
                r.update({"holdout": spec["title"].split(" (")[0], "family": family, "claim": cid, "asset": block,
                          "forecast": f_name, "reference": ref, "expected": expected, "h": H})
                c = committed[(block, cid)]
                ok = (ph.fmt_iv(r["r_lo"], r["r_hi"]), ph.verdict(r["r_lo"], r["r_hi"])) == (c[0], c[1])
                identity.append(f"{family} | {block} | {cid} | {'identical' if ok else 'DIFFERS ' + str(c)}")
                rows.append(r)
        print(f"{key}: {sum(1 for r in rows if r['family'] == family)} comparisons", flush=True)
    for folder, label in ph.VIX_HOLDOUTS.items():
        scored = ph.load_scored(folder)[1][1]
        committed = ph.committed_vix_intervals(folder)
        for i, (name, ref) in enumerate(VIX_COMPARISONS, start=1):
            r = row_stats(scored, name, ref, n_boot, n_boot_p)
            r.update({"holdout": label, "family": f"VIX comparisons, {label}", "claim": VIX_CLAIM_OF.get((name, ref), f"({i})"),
                      "asset": label, "forecast": name, "reference": ref, "expected": VIX_EXPECTED[(name, ref)], "h": H,
                      "comparison": i})
            c = committed[(name, ref)]
            ok = (ph.fmt_iv(r["r_lo"], r["r_hi"]), ph.verdict(r["r_lo"], r["r_hi"])) == (c[0], c[1])
            identity.append(f"VIX {label} | {name} vs {ref} | {'identical' if ok else 'DIFFERS ' + str(c)}")
            rows.append(r)
        print(f"{folder}: 7 comparisons", flush=True)
    # stock-bond: no saved forecasts; the four printed level-forecast intervals
    text = (ph.REPRO / "stock_bond" / "stdout.txt").read_text()
    n = int(re.search(r"level forecast of next-quarter correlation, (\d+) days", text).group(1))
    ref_rmse = float(re.search(r"^trailing 63-day correlation\s+[\d.]+\s+([\d.]+)\s*$", text, re.M).group(1))
    pat = re.compile(r"^(.+?)\s+([-\d.]+)\s+([\d.]+)\s+\[([+-]\d\.\d{3}), ([+-]\d\.\d{3})\] (worse|no difference|beats baseline)\s*$", re.M)
    for m in pat.finditer(text):
        lo, hi = float(m.group(4)), float(m.group(5))
        label = m.group(1).strip()
        short = {"A implied correlation": "level A", "B implied correlation": "level B"}.get(label, "level, " + label.split(" correlation")[0])
        rows.append({"holdout": "Stock-bond, 1962-2004", "family": "stock-bond level rules", "claim": short,
                     "asset": "S&P 500 / 10y", "forecast": label, "reference": "trailing 63-day correlation",
                     "expected": "beats baseline?", "h": 63, "n": n, "ref RMSE": ref_rmse, "ref QLIKE": float("nan"),
                     "r_lo": lo, "r_hi": hi, "q_lo": float("nan"), "q_hi": float("nan"),
                     "p boot RMSE": interval_p_normal(lo, hi), "p boot QLIKE": float("nan"),
                     "p DM RMSE": float("nan"), "p DM QLIKE": float("nan"), "approx": True})
    print(f"stock_bond: {sum(1 for r in rows if r['family'] == 'stock-bond level rules')} printed intervals", flush=True)
    return rows, identity


# ----------------------------------------------------------------------------------------------
# POWER


def power_doc(rows: list[dict], identity: list[str], head: str, n_boot: int) -> str:
    out = [f"{CLASS}\n",
           "# Power of the registered holdout comparisons, October 2026\n",
           f"Written by `examples/power_multiplicity.py` at {head}, {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, "
           f"{n_boot:,} bootstrap draws (63-day circular blocks, seed 0, the registered scheme). Inputs: the scored "
           "tables under `docs/results/reproductions/<holdout>/scored/` (stage S1; ETF = the frozen checkpoints "
           "re-scored) and, for the stock-bond holdout, which saved no forecasts, the intervals printed in "
           "`docs/results/reproductions/stock_bond/stdout.txt`. Stage S7 (a) of the reopen; panel ranked item 2 "
           "and desk finding 9 (`HMM_DESK_REVIEW_2026-10-17.md`).\n",
           "How to read the columns. *Bound* is the equivalence reading of the registered interval (as in "
           "`docs/POSTHOC_2026-10.md` (b)): for a \"no difference\" row the largest improvement the interval still "
           "allows; for \"better\" or \"worse\" the smallest gain or loss it demonstrates. *Could decide* is the "
           "interval's half-width in percent of the reference loss: a true difference smaller than that would, "
           "with an interval of the same width centred on it, still have read \"no difference\". It is a "
           "property of the sample and the loss, not of the result. *Windows* is the scored days divided by the "
           "target length (21 days; 63 for stock-bond), the number of non-overlapping targets the sample holds.\n",
           "## 1. Identity check\n",
           "Class: reproduction. The registered RMSE interval and verdict recomputed from the scored tables "
           "against the committed text (cross-index and ETF result files; the VIX reproductions' stdout).\n"]
    n_ok = sum(1 for s in identity if s.endswith("identical"))
    out.append(f"Result: {n_ok} of {len(identity)} identical.\n")
    if n_ok != len(identity):
        out.append("```\n" + "\n".join(s for s in identity if not s.endswith("identical")) + "\n```\n")
    out.append("## 2. Per comparison\n")
    out.append(f"Class: {CLASS}.\n")
    for fam in dict.fromkeys(r["family"] for r in rows):
        sub = [r for r in rows if r["family"] == fam]
        out.append(f"### {fam}\n")
        tab = []
        for r in sub:
            t = {"claim": r["claim"], "asset": r["asset"], "forecast vs reference": f"{r['forecast']} vs {r['reference']}",
                 "expected": r["expected"], "days": f"{r['n']:,}", "windows": r["n"] // r["h"],
                 "dRMSE 95% (registered)": ph.fmt_iv(r["r_lo"], r["r_hi"]), "verdict": ph.verdict(r["r_lo"], r["r_hi"]),
                 "RMSE bound": ph.equivalence(r["r_lo"], r["r_hi"], r["ref RMSE"]),
                 "RMSE could decide": f"{half_width_pct(r['r_lo'], r['r_hi'], r['ref RMSE']):.1f}%"}
            if np.isnan(r["q_lo"]):
                t.update({"dQLIKE 95%": "n/a", "QLIKE bound": "n/a", "QLIKE could decide": "n/a"})
            else:
                t.update({"dQLIKE 95%": ph.fmt_iv(r["q_lo"], r["q_hi"]),
                          "QLIKE bound": ph.equivalence(r["q_lo"], r["q_hi"], r["ref QLIKE"]),
                          "QLIKE could decide": f"{half_width_pct(r['q_lo'], r['q_hi'], r['ref QLIKE']):.1f}%"})
            tab.append(t)
        out.append(ph.md_table(pd.DataFrame(tab)) + "\n")
    out.append("The stock-bond rows are correlation forecasts (RMSE of correlation, reference RMSE "
               f"{next(r['ref RMSE'] for r in rows if r['family'] == 'stock-bond level rules'):.3f}); QLIKE does not "
               "apply to a correlation, and the bound uses the printed 3-decimal interval. The stock-bond "
               "detection rule (median lag, misses, false alarms on 3 lasting flips) has no interval and no power "
               "statement beyond its count: three flips.\n")
    out.append("## 3. What each holdout could decide, one sentence per registered claim\n")
    out.append(f"Class: {CLASS}. Paste-ready; the range is over the assets the claim is judged on.\n")
    for line in claim_sentences(rows):
        out.append(f"- {line}")
    out.append("")
    return "\n".join(out) + "\n"


def claim_sentences(rows: list[dict]) -> list[str]:
    lines = []
    groups: dict[tuple[str, str], list[dict]] = {}
    for r in rows:
        groups.setdefault((r["holdout"], r["claim"]), []).append(r)
    for (hold, cid), sub in groups.items():
        rmse = [half_width_pct(r["r_lo"], r["r_hi"], r["ref RMSE"]) for r in sub]
        qs = [half_width_pct(r["q_lo"], r["q_hi"], r["ref QLIKE"]) for r in sub if not np.isnan(r["q_lo"])]
        days = sorted({r["n"] for r in sub})
        what = "; ".join(dict.fromkeys(f"{r['forecast']} vs {r['reference']}" for r in sub))
        rng = (lambda v: f"{min(v):.1f}%" if len(v) == 1 or round(min(v), 1) == round(max(v), 1)
               else f"{min(v):.1f}% to {max(v):.1f}%")
        day_txt = f"{days[0]:,}" if len(days) == 1 else f"{days[0]:,} to {days[-1]:,}"
        s = (f"{hold}, {cid} ({what}): with {day_txt} scored days the registered RMSE interval is wide enough "
             f"that it shows a difference only when the true difference exceeds about {rng(rmse)} of the "
             f"reference RMSE")
        if qs:
            s += f" ({rng(qs)} of the reference QLIKE)"
        s += "; anything smaller reads as no difference."
        lines.append(s)
    return lines


# ----------------------------------------------------------------------------------------------
# MULTIPLE TESTING


def outcomes_after(rows: list[dict], verdict_of) -> dict[tuple[str, str], str]:
    """Claim outcomes from per-asset verdicts given by ``verdict_of(row)``."""
    res = {}
    for hold in dict.fromkeys(r["holdout"] for r in rows):
        sub = [r for r in rows if r["holdout"] == hold]
        if sub[0]["family"].startswith("VIX"):
            v = {(r["forecast"], r["reference"]): verdict_of(r) for r in sub}
            for k, o in ph.vix_claim_outcomes(v).items():
                res[(hold, k)] = o
        elif sub[0]["family"].startswith("stock-bond"):
            continue
        else:
            for cid in dict.fromkeys(r["claim"] for r in sub):
                cr = [r for r in sub if r["claim"] == cid]
                res[(hold, cid)] = claim_verdict(cr[0]["expected"], [verdict_of(r) for r in cr])
    return res


def multiplicity_doc(rows: list[dict], head: str, n_boot: int, n_boot_p: int) -> str:
    fams = list(dict.fromkeys(r["family"] for r in rows))
    out = [f"{CLASS}\n",
           "# Multiple testing across the registered holdout comparisons, October 2026\n",
           f"Written by `examples/power_multiplicity.py` at {head}, {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}. "
           f"p-values: *boot* inverts the registered paired circular block bootstrap (63-day blocks, seed 0, "
           f"{n_boot_p:,} draws, the first {n_boot:,} of which are the registered draws), two-sided, "
           "`regimes.posthoc.bootstrap_p_value`; *DM* is a HAC Diebold-Mariano test (Bartlett, lag 20) of equal "
           "mean squared error (RMSE rows) or equal mean QLIKE. Holm (1979) at 5% family-wise, "
           "`regimes.posthoc.holm`. The smallest bootstrap p-value attainable is "
           f"2 / ({n_boot_p:,} + 1) = {2 / (n_boot_p + 1):.5f}; Holm's first threshold across all registered tests is "
           f"0.05 / {len(rows)} = {0.05 / len(rows):.5f}. Stage S7 (b); joint desk finding 12 and desk finding 9 "
           "(`HMM_DESK_REVIEW_2026-10-17.md`: no multiplicity correction anywhere).\n",
           "No verdict changes. The registered rule (a 95% interval per comparison, no correction) stays the "
           "verdict; this file only says which registered \"better\" and \"worse\" verdicts would survive a "
           "family-wise correction. A correction can only turn a \"better\" or \"worse\" into \"no difference\", "
           "so it can never break a registered \"not better\" claim that holds; it can only make it easier to "
           "hold.\n",
           "## 1. The registered families\n",
           f"Class: {CLASS} (the counts are read off the protocols and the scored tables).\n"]
    tab = []
    for f in fams:
        sub = [r for r in rows if r["family"] == f]
        tab.append({"family": f, "holdout": sub[0]["holdout"], "comparisons": len(sub),
                    "claims": len(dict.fromkeys(r["claim"] for r in sub)),
                    "assets": len(dict.fromkeys(r["asset"] for r in sub)),
                    "registered non-null RMSE verdicts": sum(ph.verdict(r["r_lo"], r["r_hi"]) != "no difference" for r in sub)})
    tab.append({"family": "all registered interval tests", "holdout": "all", "comparisons": len(rows), "claims": "",
                "assets": "", "registered non-null RMSE verdicts": sum(ph.verdict(r["r_lo"], r["r_hi"]) != "no difference" for r in rows)})
    out.append(ph.md_table(pd.DataFrame(tab)) + "\n")
    out.append("Not counted as interval tests: the stock-bond detection rule (B classifier vs trailing 63-day "
               "correlation on median lag, misses and false alarms; no p-value exists) and the VIX claims A, B, C, "
               "which are read off the seven comparisons. The stock-bond intervals' p-values are a normal "
               "approximation from the printed 3-decimal interval (the reproduction saved no stock-bond forecasts), "
               "and that family has no QLIKE.\n")
    # Holm within and across
    for loss in ("RMSE", "QLIKE"):
        for kind in ("boot", "DM"):
            col = f"p {kind} {loss}"
            p_all = np.array([r[col] for r in rows])
            across = holm(p_all, ALPHA)
            for i, r in enumerate(rows):
                r[f"holm all {kind} {loss}"] = bool(across["reject"][i])
                r[f"adj all {kind} {loss}"] = across["adjusted"][i]
            for f in fams:
                idx = [i for i, r in enumerate(rows) if r["family"] == f]
                w = holm(p_all[idx], ALPHA)
                for j, i in enumerate(idx):
                    rows[i][f"holm fam {kind} {loss}"] = bool(w["reject"][j])
                    rows[i][f"adj fam {kind} {loss}"] = w["adjusted"][j]
    out.append("## 2. Which registered verdicts survive\n")
    out.append(f"Class: {CLASS}. Every comparison whose verdict on that loss is \"better\" or \"worse\" (the "
               "registered RMSE verdict, or the post-hoc QLIKE verdict from the same interval scheme), with its p-values and "
               "whether Holm keeps it within its family and across all registered tests. \"yes\" = survives.\n")
    for loss, lo_k, hi_k in (("RMSE", "r_lo", "r_hi"), ("QLIKE", "q_lo", "q_hi")):
        out.append(f"### {loss}\n")
        tab = []
        for r in rows:
            if np.isnan(r[lo_k]):
                continue
            v = ph.verdict(r[lo_k], r[hi_k])
            if v == "no difference":
                continue
            yn = lambda b: "yes" if b else "no"  # noqa: E731
            tab.append({"family": r["family"], "claim": r["claim"], "asset": r["asset"],
                        "forecast vs reference": f"{r['forecast']} vs {r['reference']}", "verdict": v,
                        "interval": ph.fmt_iv(r[lo_k], r[hi_k]),
                        "p boot": f"{r[f'p boot {loss}']:.4f}" + (" (approx)" if r.get("approx") else ""),
                        "p DM": "n/a" if np.isnan(r[f"p DM {loss}"]) else f"{r[f'p DM {loss}']:.4f}",
                        "Holm family (boot)": yn(r[f"holm fam boot {loss}"]),
                        "Holm all (boot)": yn(r[f"holm all boot {loss}"]),
                        "Holm family (DM)": "n/a" if np.isnan(r[f"p DM {loss}"]) else yn(r[f"holm fam DM {loss}"]),
                        "Holm all (DM)": "n/a" if np.isnan(r[f"p DM {loss}"]) else yn(r[f"holm all DM {loss}"])})
        out.append(ph.md_table(pd.DataFrame(tab)) + "\n")
        n_v = len(tab)
        for kind in ("boot", "DM"):
            fam_k = sum(1 for t in tab if t[f"Holm family ({kind})"] == "yes")
            all_k = sum(1 for t in tab if t[f"Holm all ({kind})"] == "yes")
            out.append(f"{loss}, {kind} p-values: {n_v} non-null verdicts; {fam_k} survive Holm within their family, "
                       f"{all_k} across all registered tests.\n")
    out.append("## 3. Claim outcomes when the non-surviving verdicts are read as no difference\n")
    out.append(f"Class: {CLASS}. The registered rule applied to per-asset verdicts after Holm (bootstrap "
               "p-values): a verdict Holm does not keep is read as \"no difference\". The registered column is "
               "the verdict and does not change.\n")
    base_r = outcomes_after(rows, lambda r: ph.verdict(r["r_lo"], r["r_hi"]))
    base_q = outcomes_after(rows, lambda r: ph.verdict(r["q_lo"], r["q_hi"]))

    def keep(lo_k, hi_k, col):
        return lambda r: ph.verdict(r[lo_k], r[hi_k]) if r[col] else "no difference"
    variants = {"RMSE, Holm family": outcomes_after(rows, keep("r_lo", "r_hi", "holm fam boot RMSE")),
                "RMSE, Holm all": outcomes_after(rows, keep("r_lo", "r_hi", "holm all boot RMSE")),
                "QLIKE, Holm family": outcomes_after(rows, keep("q_lo", "q_hi", "holm fam boot QLIKE")),
                "QLIKE, Holm all": outcomes_after(rows, keep("q_lo", "q_hi", "holm all boot QLIKE"))}
    tab = []
    for k in base_r:
        t = {"holdout": k[0], "claim": k[1], "RMSE (registered)": base_r[k],
             "RMSE, Holm family": variants["RMSE, Holm family"][k], "RMSE, Holm all": variants["RMSE, Holm all"][k],
             "QLIKE (post hoc)": base_q[k], "QLIKE, Holm family": variants["QLIKE, Holm family"][k],
             "QLIKE, Holm all": variants["QLIKE, Holm all"][k]}
        t["moves under Holm"] = "yes" if len({t["RMSE (registered)"], t["RMSE, Holm family"], t["RMSE, Holm all"]}) > 1 else ""
        tab.append(t)
    out.append(ph.md_table(pd.DataFrame(tab)) + "\n")
    moved = [f"{t['holdout']} {t['claim']} ({t['RMSE (registered)']} -> {t['RMSE, Holm all']} across all)"
             for t in tab if t["moves under Holm"]]
    out.append(f"RMSE claim outcomes that move under Holm (family or all): {len(moved)} of {len(tab)}"
               + (": " + "; ".join(moved) if moved else "") + ".\n")
    return "\n".join(out) + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-boot", type=int, default=2000, help="draws for the registered intervals")
    parser.add_argument("--n-boot-p", type=int, default=20000, help="draws for the bootstrap p-values")
    parser.add_argument("--power-out", default=str(ROOT / "docs" / "POWER_2026-10.md"))
    parser.add_argument("--mt-out", default=str(ROOT / "docs" / "MULTIPLE_TESTING_2026-10.md"))
    args = parser.parse_args()

    def no_network(*a, **k):
        raise RuntimeError("power_multiplicity.py reads only the saved tables; a download was attempted")
    sys.modules["yfinance"] = types.SimpleNamespace(download=no_network)

    head = ph.git_head()
    rows, identity = collect(args.n_boot, args.n_boot_p)
    Path(args.power_out).write_text(power_doc(rows, identity, head, args.n_boot))
    Path(args.mt_out).write_text(multiplicity_doc(rows, head, args.n_boot, args.n_boot_p))
    n_ok = sum(1 for s in identity if s.endswith("identical"))
    print(f"identity {n_ok} of {len(identity)}; wrote {args.power_out} and {args.mt_out}")


if __name__ == "__main__":
    main()
