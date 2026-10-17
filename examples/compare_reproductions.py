"""Compare two reproduction folders written by examples/reproduce_holdout.py, file by file.

Class: reproduction. Used to show that a behaviour-preserving code change leaves a holdout's
reproduction identical (the rule of the October 2026 reopen): the printed output, every saved
forecast, every scored table and every walk-forward series must match byte for byte. Files present
on one side only (for example a newly recorded diagnostic table) are listed, not counted as a
difference.

    python examples/compare_reproductions.py <reference folder> <candidate folder> [...]

Prints one line per file class and a verdict. Exit status 1 if any shared file differs.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

CLASSES = ("stdout.txt", "forecasts", "scored", "walk_forwards", "convergence.csv")


def compare(reference: Path, candidate: Path) -> dict[str, dict]:
    """{file class: {"identical": n, "differ": [names], "only_reference": [...], "only_candidate": [...]}}"""
    out = {}
    for cls in CLASSES:
        a, b = reference / cls, candidate / cls
        if a.is_dir() or b.is_dir():
            names_a = {p.name for p in a.glob("*.csv")} if a.is_dir() else set()
            names_b = {p.name for p in b.glob("*.csv")} if b.is_dir() else set()
        else:
            names_a = {cls} if a.exists() else set()
            names_b = {cls} if b.exists() else set()
            a, b = reference, candidate
        shared = sorted(names_a & names_b)
        differ = [n for n in shared if (a / n).read_bytes() != (b / n).read_bytes()]
        out[cls] = {"identical": len(shared) - len(differ), "differ": differ,
                    "only_reference": sorted(names_a - names_b), "only_candidate": sorted(names_b - names_a)}
    return out


def report(reference: Path, candidate: Path) -> bool:
    res = compare(reference, candidate)
    print(f"reference {reference}\ncandidate {candidate}")
    ok = True
    for cls, r in res.items():
        extra = ""
        if r["only_candidate"]:
            extra += f"; only in candidate: {', '.join(r['only_candidate'])}"
        if r["only_reference"]:
            extra += f"; only in reference: {', '.join(r['only_reference'])}"
        if r["differ"]:
            ok = False
            print(f"  {cls:16s} {r['identical']} identical, DIFFER: {', '.join(r['differ'])}{extra}")
        else:
            print(f"  {cls:16s} {r['identical']} identical{extra}")
    print("verdict: identical on every shared file" if ok else "verdict: DIFFERS")
    for line in convergence_lines(candidate):
        print("  " + line)
    return ok


def convergence_lines(folder: Path) -> list[str]:
    """One line per walk-forward convergence table saved in ``folder`` (stage S3 of the reopen), as
    printed by ``regimes.correlation.convergence_counts``."""
    import pandas as pd

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from regimes.correlation import convergence_counts

    out = []
    for path in sorted((folder / "walk_forwards").glob("*__convergence.csv")):
        df = pd.read_csv(path, index_col=0)
        if "best_converged" in df and df["best_converged"].dtype == object:
            df["best_converged"] = df["best_converged"].map({"True": True, "False": False}).astype("boolean")
        out.append(f"{path.name.split('__')[0]}: {convergence_counts(df)}")
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("pairs", nargs="+", help="reference and candidate folders, alternating")
    args = parser.parse_args()
    if len(args.pairs) % 2:
        parser.error("give folders in reference/candidate pairs")
    ok = True
    for ref, cand in zip(args.pairs[::2], args.pairs[1::2]):
        ok &= report(Path(ref), Path(cand))
        print()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
