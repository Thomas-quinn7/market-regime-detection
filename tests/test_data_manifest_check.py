"""Tests for examples/data_manifest.py --check (stage S7 c, the laptop hand-off)."""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import data_manifest as dm  # noqa: E402


def test_check_finds_equal_changed_and_missing_files(tmp_path):
    (tmp_path / "data").mkdir()
    a, b = tmp_path / "data" / "a.csv", tmp_path / "data" / "b.csv"
    a.write_text("1,2\n")
    b.write_text("3,4\n")
    h = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()  # noqa: E731
    manifest = tmp_path / "MANIFEST.md"
    manifest.write_text("\n".join([
        "| file | sha256 | bytes | mtime (UTC) | holdouts | freeze commit | git |", "|---|---|---|---|---|---|---|",
        f"| `data/a.csv` | `{h(a)}` | 4 | x | etf | da0cf0f | no |",
        f"| `data/b.csv` | `{h(b)}` | 4 | x | cross_index | 963cb5e | no |",
        "| `data/c.csv` | `00` | 4 | x | etf | da0cf0f | no |"]) + "\n")
    b.write_text("3,5\n")
    res = dm.check(manifest, tmp_path)
    assert res == {"ok": ["data/a.csv"], "differ": ["data/b.csv"], "missing": ["data/c.csv"]}
    assert dm.check(manifest, tmp_path, "etf") == {"ok": ["data/a.csv"], "differ": [], "missing": ["data/c.csv"]}
