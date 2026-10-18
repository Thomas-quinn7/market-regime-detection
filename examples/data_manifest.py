"""Write data/MANIFEST.md: sha256, size and mtime of every cached input, and which holdout reads it.

Run from the repo root:

    python examples/data_manifest.py
    python examples/data_manifest.py --check [--holdout etf]   # verify local files against the manifest

Every file under ``data/`` is listed, including the walk-forward checkpoints in
``data/checkpoints/msgarch_credit/``. The holdout column comes from the reproductions: each
``docs/results/reproductions/<holdout>/provenance.json`` lists the files the frozen script read
(recorded by ``examples/reproduce_holdout.py``), and the ETF holdout also reads its checkpoints.
A file no reproduction read is marked "-".

The mtimes are those on the machine that runs this script. Files copied between machines carry the
copy time, not the time they were first downloaded; the manifest says which host it was made on.
"""
from __future__ import annotations

import json
import socket
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "examples"))

from reproduce_holdout import sha256  # noqa: E402

DATA = REPO / "data"
REPRO = REPO / "docs" / "results" / "reproductions"
CHECKPOINTS = "data/checkpoints/msgarch_credit/"
FREEZE = {"stock_bond": "53b50c6", "vix_early": "3fea6a7", "vix_recent": "3fea6a7",
          "cross_index": "963cb5e", "etf": "da0cf0f"}  # freeze commits, from the protocols and WRITEUP


def readers() -> dict[str, list[str]]:
    """Map repo-relative data path -> holdouts whose reproduction read it."""
    out: dict[str, list[str]] = {}
    for prov in sorted(REPRO.glob("*/provenance.json")):
        header = json.loads(prov.read_text())
        for rec in header.get("data_files", []):
            out.setdefault(rec["path"], []).append(header["holdout"])
    return out


def tracked() -> set[str]:
    res = subprocess.run(["git", "ls-files", "data"], cwd=REPO, capture_output=True, text=True)
    return set(res.stdout.split())


def rows() -> list[dict]:
    who = readers()
    in_git = tracked()
    result = []
    for path in sorted(p for p in DATA.rglob("*") if p.is_file() and p.name not in {".gitkeep", "MANIFEST.md"}):
        rel = path.relative_to(REPO).as_posix()
        users = list(who.get(rel, []))
        if rel.startswith(CHECKPOINTS) and "etf" not in users:
            users.append("etf (frozen-run checkpoints)")
        st = path.stat()
        freezes = sorted({FREEZE[u.split()[0]] for u in users})
        result.append({"path": rel, "freeze": ", ".join(freezes) or "-", "sha256": sha256(path), "bytes": st.st_size,
                       "mtime": datetime.fromtimestamp(st.st_mtime, timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ"),
                       "holdouts": ", ".join(sorted(set(users))) or "-",
                       "git": "yes" if rel in in_git else "no"})
    return result


def read_manifest(path: Path) -> list[dict]:
    """The rows of a written MANIFEST.md: path, sha256, bytes, holdouts."""
    out = []
    for line in path.read_text().splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) == 7 and cells[0].startswith("`data/"):
            out.append({"path": cells[0].strip("`"), "sha256": cells[1].strip("`"), "bytes": int(cells[2]),
                        "holdouts": cells[4]})
    return out


def check(manifest: Path, root: Path, holdout: str | None = None) -> dict[str, list[str]]:
    """Compare the files under ``root`` with a manifest. Returns {"ok", "differ", "missing"} lists of
    repo-relative paths; with ``holdout`` only the files that holdout read are checked."""
    res: dict[str, list[str]] = {"ok": [], "differ": [], "missing": []}
    for r in read_manifest(manifest):
        if holdout and holdout not in r["holdouts"]:
            continue
        f = root / r["path"]
        if not f.is_file():
            res["missing"].append(r["path"])
        elif sha256(f) != r["sha256"]:
            res["differ"].append(r["path"])
        else:
            res["ok"].append(r["path"])
    return res


def main() -> None:
    if "--check" in sys.argv:
        holdout = sys.argv[sys.argv.index("--holdout") + 1] if "--holdout" in sys.argv else None
        res = check(DATA / "MANIFEST.md", REPO, holdout)
        for key in ("differ", "missing"):
            for p in res[key]:
                print(f"{key.upper()}: {p}")
        print(f"manifest check{' (' + holdout + ')' if holdout else ''}: {len(res['ok'])} equal, "
              f"{len(res['differ'])} differ, {len(res['missing'])} missing")
        sys.exit(1 if res["differ"] or res["missing"] else 0)
    table = rows()
    head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True,
                          text=True).stdout.strip()
    lines = [
        "# Data manifest",
        "",
        f"Written by `examples/data_manifest.py` on {socket.gethostname()} at "
        f"{datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M')}Z, repo at {head}. "
        f"{len(table)} files.",
        "",
        "Holdout column: the holdouts whose reproduction (`examples/reproduce_holdout.py`) read the file,",
        "from `docs/results/reproductions/*/provenance.json`; \"-\" means no reproduction read it. mtimes are",
        "on this host: files copied here from the laptop on 2026-10-17 carry the copy time, so only files",
        "first written on this host (the ETF caches and checkpoints) date their download or computation.",
        "\"git\" says whether the file is committed; the rest are local caches (see .gitignore).",
        "",
        "| file | sha256 | bytes | mtime (UTC) | holdouts | freeze commit | git |",
        "|---|---|---|---|---|---|---|",
    ]
    lines += [f"| `{r['path']}` | `{r['sha256']}` | {r['bytes']} | {r['mtime']} | {r['holdouts']} | {r['freeze']} | {r['git']} |"
              for r in table]
    (DATA / "MANIFEST.md").write_text("\n".join(lines) + "\n")
    print(f"data/MANIFEST.md: {len(table)} files")


if __name__ == "__main__":
    main()
