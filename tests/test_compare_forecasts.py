"""Tests for examples/compare_forecasts.py (stage S7 c): the tolerance comparison of reproductions."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import compare_forecasts as cf  # noqa: E402

CLAIMS = [("X1", "good", "base", "better"), ("X2", "noise", "base", "not better")]


def _folder(root: Path, shift: float) -> Path:
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2010-01-01", periods=800)
    y = np.exp(rng.normal(0, 0.3, 800))
    df = pd.DataFrame({"target": y, "base": y * np.exp(rng.normal(0, 0.4, 800)),
                       "good": y * np.exp(rng.normal(0, 0.1, 800)), "noise": y * np.exp(rng.normal(0, 0.4, 800))},
                      index=idx)
    df["good"] = df["good"] + shift
    (root / "scored").mkdir(parents=True)
    df.to_csv(root / "scored" / "scored_01.csv")
    (root / "scored" / "index.json").write_text(json.dumps([{"file": "scored_01.csv", "block": "A", "n": 800}]))
    return root


def test_identical_folders_show_zero_difference_and_no_move(tmp_path):
    a, b = _folder(tmp_path / "a", 0.0), _folder(tmp_path / "b", 0.0)
    ft = cf.forecast_table(cf.load_scored(a), cf.load_scored(b))
    assert (ft["max abs diff"] == 0).all()
    vt = cf.verdict_table(cf.load_scored(a), cf.load_scored(b), CLAIMS, n_boot=200)
    assert not vt["RMSE moves"].any() and vt["max end shift"].max() == 0
    assert cf.claim_outcomes(vt, CLAIMS, "ref", "RMSE") == cf.claim_outcomes(vt, CLAIMS, "cand", "RMSE")
    assert cf.claim_outcomes(vt, CLAIMS, "ref", "RMSE")["X1"] in ("mixed", "confirmed")


def test_a_large_perturbation_is_measured_and_moves_the_verdict(tmp_path):
    a, b = _folder(tmp_path / "a", 0.0), _folder(tmp_path / "b", 3.0)
    ft = cf.forecast_table(cf.load_scored(a), cf.load_scored(b))
    row = ft[ft["model"] == "good"].iloc[0]
    assert np.isclose(row["max abs diff"], 3.0) and row["RMSE cand"] > row["RMSE ref"]
    vt = cf.verdict_table(cf.load_scored(a), cf.load_scored(b), CLAIMS, n_boot=200)
    x1 = vt[vt["claim"] == "X1"].iloc[0]
    assert x1["RMSE verdict ref"] == "better" and x1["RMSE verdict cand"] == "worse" and x1["RMSE moves"]


def test_text_mode_reports_numeric_differences_and_verdict_words(tmp_path):
    ref = tmp_path / "ref.txt"
    ref.write_text("header\n  P1 x vs y  -0.010 to +0.002 no difference\n  fit b 3.798\n")
    same = tmp_path / "same.txt"
    same.write_text(ref.read_text())
    num = tmp_path / "num.txt"
    num.write_text("header\n  P1 x vs y  -0.010 to +0.002 no difference\n  fit b 3.795\n")
    word = tmp_path / "word.txt"
    word.write_text("header\n  P1 x vs y  -0.010 to -0.002 better\n  fit b 3.798\n")
    lines, moved = cf.text_mode(ref, same)
    assert not moved and lines[-1].endswith("identical")
    lines, moved = cf.text_mode(ref, num)
    assert not moved and "largest absolute difference 0.003" in lines[3]
    lines, moved = cf.text_mode(ref, word)
    assert moved and "MOVES" in lines[-1]
