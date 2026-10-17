"""examples/compare_reproductions.py: byte comparison of two reproduction folders."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import compare_reproductions as cr  # noqa: E402


def _folder(root: Path, stdout: str, forecast: str, extra: bool = False) -> Path:
    root.mkdir()
    (root / "stdout.txt").write_text(stdout)
    for sub in ("forecasts", "scored", "walk_forwards"):
        (root / sub).mkdir()
    (root / "forecasts" / "regression_001.csv").write_text(forecast)
    (root / "scored" / "scored_01.csv").write_text("Date,target\n2020-01-01,1\n")
    (root / "walk_forwards" / "wf_001__implied_vol.csv").write_text("Date,v\n2020-01-01,1\n")
    if extra:
        (root / "walk_forwards" / "wf_001__convergence.csv").write_text("Date,best_converged,detail\n2020-01-01,True,0\n")
    (root / "convergence.csv").write_text("a,b\n1,2\n")
    return root


def test_identical_folders_with_an_extra_candidate_file_pass(tmp_path, capsys):
    a = _folder(tmp_path / "a", "out\n", "Date,forecast\n2020-01-01,0.5\n")
    b = _folder(tmp_path / "b", "out\n", "Date,forecast\n2020-01-01,0.5\n", extra=True)
    assert cr.report(a, b) is True
    res = cr.compare(a, b)
    assert res["walk_forwards"] == {"identical": 1, "differ": [], "only_reference": [],
                                    "only_candidate": ["wf_001__convergence.csv"]}
    text = capsys.readouterr().out
    assert "identical on every shared file" in text
    assert cr.convergence_lines(b) == ["wf_001: 1 of 1 refits converged"] and "wf_001: 1 of 1" in text


def test_a_changed_forecast_fails(tmp_path, capsys):
    a = _folder(tmp_path / "a", "out\n", "Date,forecast\n2020-01-01,0.5\n")
    b = _folder(tmp_path / "b", "out\n", "Date,forecast\n2020-01-01,0.50000001\n")
    assert cr.report(a, b) is False
    assert cr.compare(a, b)["forecasts"]["differ"] == ["regression_001.csv"]
    assert "DIFFERS" in capsys.readouterr().out
