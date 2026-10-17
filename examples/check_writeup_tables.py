"""Check the VIX and stock-bond holdout tables in docs/WRITEUP.md against reproduced output.

A reproduction check, not a test of any claim. These two holdouts have no committed result file;
their numbers live only in WRITEUP tables, so this script reads those tables and compares every
number in them with the matching number in ``docs/results/reproductions/<holdout>/stdout.txt``
(written by ``examples/reproduce_holdout.py``), at the precision the WRITEUP prints.

    python examples/check_writeup_tables.py

Prints one line per number and a count of mismatches; exits 1 if any number differs.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
WRITEUP = REPO / "docs" / "WRITEUP.md"
REPRO = REPO / "docs" / "results" / "reproductions"

# WRITEUP row label -> label in the script's calibrated table (section 2)
VIX_ROWS = {
    "HAR (past returns only)": "HAR",
    "VIX": "VIX",
    "HAR + VIX": "HAR + VIX",
    "HAR + VIX + HMM probability": "HAR + VIX + HMM prob",
    "HAR + VIX + joint-HMM probability": "HAR + VIX + VIX-HMM prob",
    "HMM implied vol": "HMM implied vol",
    "Joint return/VIX HMM implied vol": "VIX-HMM implied vol",
}
# WRITEUP stock-bond level-forecast row label -> label in the script's table 1
SB_ROWS = {
    "HMM, unconstrained": "A implied correlation",
    "HMM, tied variances": "B implied correlation",
    "Trailing 63-day correlation": "trailing 63-day correlation",
    "Trailing 252-day correlation": "trailing 252-day correlation",
    "EWMA correlation (0.97)": "EWMA correlation (0.97)",
}
NUM = r"[-+]?\d+\.\d+"


def table_rows(text: str, header_start: str) -> list[list[str]]:
    lines = text.splitlines()
    i = next(k for k, line in enumerate(lines) if line.startswith(header_start))
    rows = []
    for line in lines[i + 2:]:
        if not line.startswith("|"):
            break
        rows.append([c.strip().strip("*").strip() for c in line.strip("|").split("|")])
    return rows


def stdout_row(stdout: str, label: str, after: str) -> list[str]:
    """Numbers on the first line that starts with ``label`` (after padding) below the line ``after``."""
    body = stdout[stdout.index(after):]
    for line in body.splitlines():
        if line.strip().startswith(label + " ") and re.match(rf"\s*{re.escape(label)}\s+{NUM}", line):
            return re.findall(NUM, line[line.index(label) + len(label):])
    raise KeyError(label)


def main() -> int:
    text = WRITEUP.read_text(encoding="utf-8")
    checks: list[tuple[str, str, str]] = []  # (what, writeup, reproduced)

    # VIX: RMSE table, holdout columns 3 and 4.
    out = {p: (REPRO / f"vix_{p}" / "stdout.txt").read_text() for p in ("early", "recent")}
    for row in table_rows(text, "| Forecast | 2011-2023"):
        label = VIX_ROWS[row[0]]
        for col, period in ((2, "early"), (3, "recent")):
            got = stdout_row(out[period], label, "2) calibrated")[0]
            checks.append((f"VIX {period} RMSE {label}", row[col], got))
    # VIX: claim intervals quoted in the claims table and in the 2024-2026 QLIKE sentence.
    claims_rows = table_rows(text, "| Claim | 1996-2004")
    quoted = re.findall(rf"({NUM}) to ({NUM})", " ".join(" ".join(r[1:]) for r in claims_rows))
    for period in ("early", "recent"):
        frozen = out[period][out[period].index("3) the frozen"):]
        for lo, hi in quoted:
            if f"{lo} to {hi}" in frozen:
                checks.append((f"VIX {period} interval {lo} to {hi}", "quoted", "found"))
    qlike_sentence = re.search(rf"QLIKE\s+\(interval ({NUM}) to ({NUM})\)", text)
    if qlike_sentence:
        lo, hi = qlike_sentence.groups()
        checks.append(("VIX recent HMM implied vol vs HAR dQLIKE", f"{lo} to {hi}",
                       f"{lo} to {hi}" if f"{lo} to {hi}" in out["recent"] else "absent"))
    for lo, hi in quoted:
        if not any(f"{lo} to {hi}" in out[p] for p in out):
            checks.append((f"VIX interval {lo} to {hi}", "quoted", "absent"))
    for period, n in (("early", "2,228"), ("recent", "676")):
        got = re.search(r"scored days \(common to every forecast\): (\d+)", out[period]).group(1)
        checks.append((f"VIX {period} scored days", n.replace(",", ""), got))

    # Stock-bond: level-forecast table.
    sb = (REPRO / "stock_bond" / "stdout.txt").read_text()
    for row in table_rows(text, "| Signal | corr with outcome"):
        label = SB_ROWS[row[0]]
        nums = stdout_row(sb, label, "1. level forecast")
        corr, rmse = nums[0], nums[1]
        checks.append((f"stock-bond corr {label}", row[1], f"{float(corr):.2f}"))
        checks.append((f"stock-bond RMSE {label}", row[2], rmse))
        if len(nums) >= 4:
            checks.append((f"stock-bond interval {label}", re.sub(r",.*", "", row[3]),
                           f"{nums[2]} to {nums[3]}"))
    days = re.search(r"1\. level forecast of next-quarter correlation, (\d+) days", sb).group(1)
    checks.append(("stock-bond scored days", "9878", days))
    # Stock-bond: detection table (lags, median, misses, false alarms) for the four single-signal rows.
    det = {"HMM tied, P(positive state)": "B classifier P(positive) - 0.5",
           "Trailing 63-day correlation": "trailing 63-day correlation",
           "Trailing 252-day correlation": "trailing 252-day correlation",
           "EWMA correlation (0.97)": "EWMA correlation (0.97)"}
    block = sb[sb.index("2. regime detection"):]
    for row in table_rows(text, "| Signal | lags in trading days"):
        if row[0] not in det:
            continue
        line = next(l for l in block.splitlines() if l.startswith(det[row[0]]))
        ints = re.findall(r"\d+", line[len(det[row[0]]):])
        median, misses, alarms, lags = ints[0], ints[1], ints[2], ", ".join(ints[3:])
        for what, w, g in (("lags", row[1], lags), ("median", row[2], median),
                           ("misses", row[3], misses), ("false alarms", row[4], alarms)):
            checks.append((f"stock-bond {what} {det[row[0]]}", w, g))

    bad = 0
    for what, w, g in checks:
        ok = w == g or (w == "quoted" and g == "found")
        bad += not ok
        print(f"{'ok ' if ok else 'BAD'} {what}: WRITEUP {w}, reproduced {g}")
    print(f"\n{len(checks)} numbers checked, {bad} mismatches")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
