"""reproduction_report tabulates a reproduction folder, diff and convergence included."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import reproduction_report as rr  # noqa: E402


def test_section(tmp_path, monkeypatch):
    folder = tmp_path / "cross_index"
    folder.mkdir()
    (folder / "provenance.json").write_text(json.dumps({
        "frozen_script": "examples/x.py", "frozen_script_sha256": "abc", "wrapper": "examples/r.py x",
        "host": "h", "platform": "p", "cpus": 8, "python": "3.12", "packages": {"numpy": "2", "hmmlearn": None},
        "git_head": "deadbeef", "git_dirty_paths": [], "started_utc": "t", "wall_clock_seconds": 1.5,
        "n_regression_forecasts_saved": 3, "n_walk_forwards_saved": 2, "notes": ["placeholder"],
        "data_files": [{"path": "data/a.csv", "sha256": "f00", "bytes": 4, "mtime_utc": "m"}]}))
    (folder / "compare.txt").write_text("differs in 2 lines\n@@ -5 +5 @@\n-a\n+b\n")
    (folder / "convergence.csv").write_text("walk_forward,optimiser,converged,detail\nw,scipy,True,\nw,scipy,False,\n")
    monkeypatch.setattr(rr, "REPRO", tmp_path)
    text = "\n".join(rr.section("cross_index"))
    assert "**differs in 2 lines**" in text and "-a\n+b" in text
    assert "| w | scipy | 2 | 1 | 1 |" in text
    assert "`data/a.csv` | `f00`" in text and "note: placeholder" in text and "hmmlearn" not in text


def test_verdict_labels_and_changes(tmp_path, monkeypatch):
    body = ("\n##### Gold (GLD): returns\n claim forecast\n   M1  A  B     better -0.1 to +0.1 no difference "
            "-0.2 to -0.1        better\n\n##### Claims across assets\n   M1  A  B  better  no difference rejected\n")
    (tmp_path / "msgarch_credit_holdout_2026-10-14.txt").write_text(body)
    (tmp_path / "reproductions" / "etf").mkdir(parents=True)
    (tmp_path / "reproductions" / "etf" / "stdout.txt").write_text(body.replace("better\n\n", "no difference\n\n"))
    monkeypatch.setattr(rr, "REPRO", tmp_path / "reproductions")
    assert rr.verdict_labels(body) == [("Gold (GLD)", "M1", ("better", "no difference", "better"))]
    n, changed = rr.label_changes("etf")
    assert n == 1 and len(changed) == 1 and "Gold (GLD) M1" in changed[0]
