"""Write docs/results/reproductions/PROVENANCE_2026-10.md from the reproduction folders.

Class: reproduction. Reads ``docs/results/reproductions/<holdout>/provenance.json``, ``compare.txt``
and ``convergence.csv`` (all written by ``examples/reproduce_holdout.py``) and tabulates, per
holdout: the frozen command, host, git hash, package versions, wall-clock time, comparison verdict
with the diff, convergence counts and every data file read with its sha256 and mtime.

    python examples/reproduction_report.py
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
REPRO = REPO / "docs" / "results" / "reproductions"
ORDER = ["vix_early", "vix_recent", "stock_bond", "cross_index", "etf", "etf_frozen_checkpoints"]


VERDICT = re.compile(r"\b(better|worse|no difference)\b")
CLAIM_ROW = re.compile(r"^\s+([A-Z]\d)\s")


def verdict_labels(text: str) -> list[tuple[str, str, tuple[str, ...]]]:
    """(asset block, claim id, verdict words) for every per-asset claim row in a holdout printout."""
    rows, block = [], ""
    for line in text.splitlines():
        if line.startswith("##### "):
            block = line[6:].split(":")[0]
        m = CLAIM_ROW.match(line)
        if m and "Claims across" not in block:
            rows.append((block, m.group(1), tuple(VERDICT.findall(line))))
    return rows


def label_changes(holdout: str) -> tuple[int, list[str]] | None:
    """Per-asset verdict labels that differ between the committed result file and the reproduction."""
    ref = {"cross_index": "cross_index_holdout_2026-10-14.txt",
           "etf": "msgarch_credit_holdout_2026-10-14.txt"}.get("etf" if holdout.startswith("etf") else holdout)
    stdout = REPRO / holdout / "stdout.txt"
    if ref is None or not stdout.exists():
        return None
    a = verdict_labels((REPRO.parent / ref).read_text())
    b = verdict_labels(stdout.read_text())
    changed = [f"{x[0]} {x[1]}: {x[2]} -> {y[2]}" for x, y in zip(a, b) if x != y]
    if len(a) != len(b):
        changed.append(f"row count {len(a)} -> {len(b)}")
    return len(a), changed


def section(holdout: str) -> list[str]:
    folder = REPRO / holdout
    h = json.loads((folder / "provenance.json").read_text())
    compare = (folder / "compare.txt").read_text().rstrip("\n").splitlines()
    pk = ", ".join(f"{k} {v}" for k, v in h["packages"].items() if v)
    out = [f"## {holdout}", "", "Class: reproduction of a spent holdout; not a test.", "",
           f"- frozen command: `python -u {h['frozen_script']}` (frozen file sha256 `{h['frozen_script_sha256']}`)",
           f"- run as: `python -u {h['wrapper']}`",
           f"- host: {h['host']} ({h['platform']}, {h['cpus']} CPUs); Python {h['python']}; {pk}",
           f"- git: `{h['git_head']}`; uncommitted paths at run time: "
           f"{', '.join('`' + p + '`' for p in h['git_dirty_paths']) or 'none'}",
           f"- started {h['started_utc']}, wall clock {h['wall_clock_seconds']} s",
           f"- forecasts saved: {h['n_regression_forecasts_saved']} regression forecast series, "
           f"{h['n_walk_forwards_saved']} model walk-forwards",
           ]
    for note in h.get("notes", []):
        out.append(f"- note: {note}")
    out += ["", f"Comparison with the committed reference: **{compare[0]}**", ""]
    labels = label_changes(holdout)
    if labels is not None:
        n, changed = labels
        out += [f"Per-asset verdict labels (RMSE and QLIKE, every claim row): {n} rows compared, "
                f"{len(changed)} changed.", ""]
        out += [f"- {c}" for c in changed]
        if changed:
            out.append("")
    if len(compare) > 1:
        out += ["```", *compare[1:], "```", ""]
    conv = folder / "convergence.csv"
    if conv.exists() and conv.stat().st_size > 1:
        df = pd.read_csv(conv)
        counts = (df.groupby(["walk_forward", "optimiser"])["converged"].agg(calls="size", converged="sum")
                  .reset_index())
        counts["not converged"] = counts["calls"] - counts["converged"]
        out += ["Optimiser calls (reproduction):", "", "| walk-forward | optimiser | calls | converged | not converged |",
                "|---|---|---|---|---|"]
        out += [f"| {r.walk_forward} | {r.optimiser} | {r.calls} | {r.converged} | {r['not converged']} |"
                for _, r in counts.iterrows()]
        out.append("")
    else:
        out += ["Optimiser calls: none observable (this holdout's models use the repo's own EM, which "
                "reports no convergence flag).", ""]
    if "refit_vs_frozen_checkpoints" in h:
        res = h["refit_vs_frozen_checkpoints"]
        same = sum(v == "byte-identical" for v in res.values())
        out += [f"Refitted walk-forward files against the frozen run's checkpoints: {same} of {len(res)} "
                f"byte-identical.", ""]
        out += [f"- `{k}`: {v}" for k, v in res.items() if v != "byte-identical"]
        out.append("")
    out += ["Data files read:", "", "| file | sha256 | bytes | mtime on this host (UTC) |", "|---|---|---|---|"]
    out += [f"| `{f['path']}` | `{f['sha256']}` | {f['bytes']} | {f['mtime_utc']} |" for f in h["data_files"]]
    return out + [""]


def main() -> None:
    lines = ["# Reproduction provenance, October 2026", "",
             "Written by `examples/reproduction_report.py` from the folders beside this file. Class: "
             "reproduction. Each spent holdout was re-run once more through `examples/reproduce_holdout.py`, "
             "which runs the frozen script's `main()` unchanged and records what it computes. A reproduction "
             "checks that the committed numbers come out of the committed code and data; it is not a new test "
             "of any claim.", ""]
    for holdout in ORDER:
        if (REPRO / holdout / "provenance.json").exists():
            lines += section(holdout)
        else:
            lines += [f"## {holdout}", "", "Not run yet.", ""]
    (REPRO / "PROVENANCE_2026-10.md").write_text("\n".join(lines))
    print(f"wrote {(REPRO / 'PROVENANCE_2026-10.md').relative_to(REPO)}")


if __name__ == "__main__":
    main()
