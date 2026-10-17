"""data_manifest maps each cached file to the holdouts whose reproduction read it."""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import data_manifest as dm  # noqa: E402


def test_rows_hash_and_holdout(tmp_path, monkeypatch):
    repo = tmp_path
    data = repo / "data"
    (data / "checkpoints" / "msgarch_credit").mkdir(parents=True)
    (data / "a.csv").write_text("x\n1\n")
    (data / "b.csv").write_text("y\n2\n")
    (data / "checkpoints" / "msgarch_credit" / "c.csv").write_text("z\n")
    repro = repo / "docs" / "results" / "reproductions" / "vix_early"
    repro.mkdir(parents=True)
    (repro / "provenance.json").write_text(json.dumps(
        {"holdout": "vix_early", "data_files": [{"path": "data/a.csv"}]}))
    monkeypatch.setattr(dm, "REPO", repo)
    monkeypatch.setattr(dm, "DATA", data)
    monkeypatch.setattr(dm, "REPRO", repo / "docs" / "results" / "reproductions")
    monkeypatch.setattr(dm, "tracked", lambda: set())
    rows = {r["path"]: r for r in dm.rows()}
    assert rows["data/a.csv"]["holdouts"] == "vix_early" and rows["data/a.csv"]["freeze"] == "3fea6a7"
    assert rows["data/b.csv"]["holdouts"] == "-" and rows["data/b.csv"]["freeze"] == "-"
    ck = rows["data/checkpoints/msgarch_credit/c.csv"]
    assert ck["freeze"] == "da0cf0f" and ck["sha256"] == dm.sha256(data / "checkpoints" / "msgarch_credit" / "c.csv")
