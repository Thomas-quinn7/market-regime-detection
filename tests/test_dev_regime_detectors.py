"""Tests for examples/dev_regime_detectors.py (stage S8 d): set names, cache names, and the rule that the
learner is chosen only once the race has fitted both recurrent learners on F0 at h = 21."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import dev_regime_detectors as drd  # noqa: E402


def test_set_names_and_cache_names(monkeypatch, tmp_path):
    names = drd.set_names()
    assert names[:3] == ["F0", "F1", "F1n"] and "F1[kmeans 2]" in names and "F1[changepoint]" in names
    monkeypatch.setattr(drd, "CACHE", tmp_path)
    assert drd.cache_path(21, "random forest", "F1[gmm 3]") == tmp_path / "h021__random_forest__F1_gmm3.csv"
    assert len({drd.cache_path(21, "ols", s) for s in names}) == len(names)


def test_best_learner_waits_for_the_race(monkeypatch):
    s = pd.Series([1.0], index=pd.to_datetime(["2020-01-02"]))
    monkeypatch.setattr(drd.race, "all_forecasts", lambda h: {"ols F0": s, "ridge F0": s, "lstm F0": s})
    with pytest.raises(RuntimeError, match="gru"):
        drd.best_learner()


def test_schedule_shift_on_common_rows():
    idx = pd.bdate_range("2020-01-01", periods=6)
    here = pd.Series([1.0, 1.0, 1.5, 1.0, 1.0], index=idx[1:])
    s8b = pd.Series([0.9, 1.0, 1.0, 1.0, 1.0, 1.05], index=idx)
    out = drd.schedule_shift(here, s8b)
    assert out["common days"] == 5 and out["first day here"] == "2020-01-02"
    assert out["first day S8 (b)"] == "2020-01-01"
    assert out["max abs diff"] == "0.5000" and out["on"] == "2020-01-06" and out["days diff > 0.1"] == 1
    assert out["median abs diff"] == "0.0000"
