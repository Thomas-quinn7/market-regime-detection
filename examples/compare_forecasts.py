"""Numeric (tolerance) comparison of two reproductions, for the ones that are not byte-identical.

Class: reproduction. Stage S7 (c) of the October 2026 reopen. ``compare_reproductions.py`` answers
"identical or not"; this answers "how far apart, and does any verdict move". Two modes:

    # two folders written by examples/reproduce_holdout.py (scored/ tables on both sides)
    python examples/compare_forecasts.py folders <reference folder> <candidate folder> --holdout etf
    # a committed result file against a reproduction's stdout, number by number
    python examples/compare_forecasts.py text docs/results/cross_index_holdout_2026-10-14.txt \
        docs/results/reproductions/cross_index/stdout.txt

Folder mode prints, per asset and model, the largest absolute forecast difference and the RMSE and
QLIKE on each side; then every registered comparison's interval and verdict (63-day circular blocks,
2,000 draws, seed 0, the registered scheme) on each side, and the claim outcomes from each side's
verdicts. Text mode lines up the two files line by line, compares every number, and reports the lines
that differ, the largest absolute difference, and whether any verdict word differs. Exit status 0 if no
verdict and no claim outcome moves, 1 otherwise.
"""
from __future__ import annotations

import argparse
import difflib
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from regimes.forecast import qlike  # noqa: E402
from regimes.posthoc import paired_interval  # noqa: E402

NUM = re.compile(r"[+-]?\d+\.\d+|[+-]?\d+")
VERDICT_WORDS = ("better", "worse", "no difference", "confirmed", "rejected", "mixed", "holds", "fails",
                 "not shown", "beats baseline", "does not add anything")


def verdict(lo: float, hi: float) -> str:
    return "better" if hi < 0 else "worse" if lo > 0 else "no difference"


def load_scored(folder: Path) -> list[tuple[str, pd.DataFrame]]:
    index = pd.read_json(folder / "scored" / "index.json")
    return [(e["block"], pd.read_csv(folder / "scored" / e["file"], index_col=0, parse_dates=True))
            for _, e in index.iterrows()]


def claims_for(holdout: str):
    """[(id, forecast, reference, expected)] for the holdout, from the frozen scripts' claim lists."""
    if holdout == "etf":
        from msgarch_credit import MS_CLAIMS, OTHER_CLAIMS
        return [(c, f.format(m="MS-GARCH"), r.format(m="MS-GARCH"), e) for c, f, r, e in MS_CLAIMS] + OTHER_CLAIMS
    if holdout == "cross_index":
        from better_vol_models import CLAIMS
        return CLAIMS
    raise ValueError(f"no claim list for {holdout!r}")


def forecast_table(ref: list[tuple[str, pd.DataFrame]], cand: list[tuple[str, pd.DataFrame]]) -> pd.DataFrame:
    rows = []
    for (block, a), (block_b, b) in zip(ref, cand):
        assert block == block_b, (block, block_b)
        common = a.index.intersection(b.index)
        for col in a.columns:
            if col == "target" or col not in b.columns:
                continue
            x, y = a.loc[common, col].to_numpy(), b.loc[common, col].to_numpy()
            t = a.loc[common, "target"].to_numpy()
            rows.append({"asset": block, "model": col, "days ref": len(a), "days cand": len(b),
                         "max abs diff": float(np.nanmax(np.abs(x - y))),
                         "RMSE ref": float(np.sqrt(np.mean((x - t) ** 2))),
                         "RMSE cand": float(np.sqrt(np.mean((y - t) ** 2))),
                         "QLIKE ref": float(qlike(x, t).mean()), "QLIKE cand": float(qlike(y, t).mean())})
        tgt = float(np.nanmax(np.abs(a.loc[common, "target"].to_numpy() - b.loc[common, "target"].to_numpy())))
        rows.append({"asset": block, "model": "target", "days ref": len(a), "days cand": len(b), "max abs diff": tgt,
                     "RMSE ref": np.nan, "RMSE cand": np.nan, "QLIKE ref": np.nan, "QLIKE cand": np.nan})
    return pd.DataFrame(rows)


def verdict_table(ref, cand, claims, n_boot: int = 2000) -> pd.DataFrame:
    rows = []
    for (block, a), (_, b) in zip(ref, cand):
        for cid, f, r, expected in claims:
            out = {"asset": block, "claim": cid, "expected": expected}
            for side, df in (("ref", a), ("cand", b)):
                y = df["target"].to_numpy()
                ef, eb = df[f].to_numpy() - y, df[r].to_numpy() - y
                lo, hi = paired_interval(ef, eb, statistic="rmse", block=63, n_boot=n_boot)
                qlo, qhi = paired_interval(qlike(df[f].to_numpy(), y), qlike(df[r].to_numpy(), y),
                                           statistic="mean", block=63, n_boot=n_boot)
                out.update({f"dRMSE {side}": f"{lo:+.3f} to {hi:+.3f}", f"RMSE verdict {side}": verdict(lo, hi),
                            f"dQLIKE {side}": f"{qlo:+.3f} to {qhi:+.3f}", f"QLIKE verdict {side}": verdict(qlo, qhi),
                            f"_r {side}": (lo, hi), f"_q {side}": (qlo, qhi)})
            out["RMSE moves"] = out["RMSE verdict ref"] != out["RMSE verdict cand"]
            out["QLIKE moves"] = out["QLIKE verdict ref"] != out["QLIKE verdict cand"]
            out["max end shift"] = max(abs(u - v) for u, v in zip(out["_r ref"] + out["_q ref"], out["_r cand"] + out["_q cand"]))
            rows.append(out)
    return pd.DataFrame(rows)


def claim_outcomes(vt: pd.DataFrame, claims, side: str, loss: str) -> dict[str, str]:
    from cross_index_holdout import claim_verdict
    return {cid: claim_verdict(expected, vt.loc[vt["claim"] == cid, f"{loss} verdict {side}"].tolist())
            for cid, _, _, expected in claims}


def folders_mode(ref_dir: Path, cand_dir: Path, holdout: str, n_boot: int) -> tuple[list[str], bool]:
    ref, cand = load_scored(ref_dir), load_scored(cand_dir)
    claims = claims_for(holdout)
    out = [f"reference: {ref_dir}", f"candidate: {cand_dir}", ""]
    ft = forecast_table(ref, cand)
    out.append("1. forecasts, per asset and model (common days)")
    for _, r in ft.iterrows():
        loss = "" if r["model"] == "target" else (f"  RMSE {r['RMSE ref']:.4f} vs {r['RMSE cand']:.4f}"
                                                  f"  QLIKE {r['QLIKE ref']:.4f} vs {r['QLIKE cand']:.4f}")
        out.append(f"  {r['asset']:<30} {r['model']:<30} max |diff| {r['max abs diff']:.2e}{loss}")
    vt = verdict_table(ref, cand, claims, n_boot)
    out += ["", "2. registered comparisons (63-day circular blocks, seed 0), reference vs candidate"]
    for _, r in vt.iterrows():
        flag = "  MOVES" if r["RMSE moves"] or r["QLIKE moves"] else ""
        out.append(f"  {r['asset']:<26} {r['claim']}  RMSE {r['dRMSE ref']} {r['RMSE verdict ref']:<13} | "
                   f"{r['dRMSE cand']} {r['RMSE verdict cand']:<13}  QLIKE {r['QLIKE verdict ref']} | "
                   f"{r['QLIKE verdict cand']}{flag}")
    claim_moved = False
    out += ["", "3. claim outcomes, reference vs candidate"]
    for loss in ("RMSE", "QLIKE"):
        a, b = claim_outcomes(vt, claims, "ref", loss), claim_outcomes(vt, claims, "cand", loss)
        for cid in a:
            mv = a[cid] != b[cid]
            claim_moved |= mv
            out.append(f"  {loss:<5} {cid}: {a[cid]} | {b[cid]}{'  MOVES' if mv else ''}")
    n_rm, n_qm = int(vt["RMSE moves"].sum()), int(vt["QLIKE moves"].sum())
    moved = claim_moved or bool(n_rm or n_qm)
    models = ft[ft["model"] != "target"]
    worst = models.loc[models["max abs diff"].idxmax()]
    drmse = (models["RMSE cand"] - models["RMSE ref"]).abs()
    out += ["", "summary: "
            f"largest forecast difference {worst['max abs diff']:.2e} ({worst['model']}, {worst['asset']}); "
            f"largest RMSE change {drmse.max():.4f}; largest interval-end shift {vt['max end shift'].max():.4f}; "
            f"per-asset verdicts moved: RMSE {n_rm} of {len(vt)}, QLIKE {n_qm} of {len(vt)}; "
            f"claim outcomes moved: {'yes, see section 3' if claim_moved else 'none'}",
            "verdict: " + ("a verdict or claim outcome MOVES" if moved else
                           "identical forecasts" if ft["max abs diff"].max() == 0 else
                           "within tolerance, no verdict or claim outcome moves")]
    return out, moved


def numbers(line: str) -> list[float]:
    return [float(x) for x in NUM.findall(line)]


def text_mode(ref_path: Path, cand_path: Path) -> tuple[list[str], bool]:
    a, b = ref_path.read_text().splitlines(), cand_path.read_text().splitlines()
    out = [f"reference: {ref_path}", f"candidate: {cand_path}", ""]
    sm = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
    max_diff, n_lines, n_struct, verdict_moves, structural = 0.0, 0, 0, [], []
    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            continue
        if tag != "replace" or (i2 - i1) != (j2 - j1):
            n_struct += 1
            structural.append(f"  {tag} reference {i1 + 1}-{i2}, candidate {j1 + 1}-{j2}")
            for line in a[i1:i2]:
                structural.append(f"    - {line}")
            for line in b[j1:j2]:
                structural.append(f"    + {line}")
            continue
        for k in range(i2 - i1):
            la, lb = a[i1 + k], b[j1 + k]
            n_lines += 1
            na, nb = numbers(la), numbers(lb)
            words_a = [w for w in VERDICT_WORDS if w in la]
            words_b = [w for w in VERDICT_WORDS if w in lb]
            if NUM.sub("#", la) != NUM.sub("#", lb) or len(na) != len(nb):
                n_struct += 1
                structural.append(f"  line {i1 + k + 1}: text differs\n    - {la}\n    + {lb}")
            else:
                d = max((abs(x - y) for x, y in zip(na, nb)), default=0.0)
                max_diff = max(max_diff, d)
                out.append(f"  line {i1 + k + 1}: max |diff| {d:.4g}\n    - {la.strip()}\n    + {lb.strip()}")
            if words_a != words_b:
                verdict_moves.append(f"  line {i1 + k + 1}: {words_a} -> {words_b}")
    moved = bool(verdict_moves)
    out.insert(3, f"lines compared {len(a)} vs {len(b)}; lines with numeric differences {n_lines}; "
                  f"largest absolute difference {max_diff:.4g}; structural differences {n_struct}; "
                  f"verdict words moved {len(verdict_moves)}")
    out += structural + verdict_moves
    out.append(f"verdict: {'a verdict word MOVES' if moved else 'within tolerance, no verdict word moves' if n_lines or structural else 'identical'}")
    return out, moved


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="mode", required=True)
    f = sub.add_parser("folders")
    f.add_argument("reference", type=Path)
    f.add_argument("candidate", type=Path)
    f.add_argument("--holdout", required=True, choices=["etf", "cross_index"])
    f.add_argument("--n-boot", type=int, default=2000)
    t = sub.add_parser("text")
    t.add_argument("reference", type=Path)
    t.add_argument("candidate", type=Path)
    for p in (f, t):
        p.add_argument("--save", type=Path, help="also write the report to this file")
    args = parser.parse_args()
    if args.mode == "folders":
        lines, moved = folders_mode(args.reference, args.candidate, args.holdout, args.n_boot)
    else:
        lines, moved = text_mode(args.reference, args.candidate)
    text = "\n".join(lines) + "\n"
    if args.save:
        args.save.write_text("Class: reproduction (examples/compare_forecasts.py).\n" + text)
    print(text, end="")
    sys.exit(1 if moved else 0)


if __name__ == "__main__":
    main()
