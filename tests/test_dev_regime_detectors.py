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


def test_verdicts_two_schedules_flags_a_moved_verdict():
    here = pd.DataFrame([
        {"h": 21, "model": "ols", "set": "F0", "dRMSE 95%": "", "RMSE": "", "dQLIKE 95%": "", "QLIKE": ""},
        {"h": 21, "model": "ols", "set": "F1", "dRMSE 95%": "a", "RMSE": "no difference", "dQLIKE 95%": "b",
         "QLIKE": "worse"},
        {"h": 21, "model": "ols", "set": "F1n", "dRMSE 95%": "c", "RMSE": "no difference", "dQLIKE 95%": "d",
         "QLIKE": "no difference"},
        {"h": 21, "model": "ols", "set": "F1[gmm 2]", "dRMSE 95%": "e", "RMSE": "worse", "dQLIKE 95%": "f",
         "QLIKE": "worse"},
        {"h": 5, "model": "lasso", "set": "F1", "dRMSE 95%": "g", "RMSE": "no difference", "dQLIKE 95%": "h",
         "QLIKE": "no difference"}])
    s8b = pd.DataFrame([
        {"h": 21, "learner": "ols", "comparison": "F1 vs F0", "dRMSE 95%": "A", "RMSE": "no difference",
         "dQLIKE 95%": "B", "QLIKE": "no difference"},
        {"h": 21, "learner": "ols", "comparison": "F1n vs F0 (noise control)", "dRMSE 95%": "C",
         "RMSE": "no difference", "dQLIKE 95%": "D", "QLIKE": "no difference"}])
    out = drd.verdicts_two_schedules(here, s8b)
    assert list(out["comparison"]) == ["F1 vs F0", "F1n vs F0 (noise control)"]   # detector and unmatched rows dropped
    assert list(out["verdict moves"]) == ["yes", "no"]
    assert out.iloc[0]["dRMSE S8 (b)"] == "A" and out.iloc[0]["dRMSE here"] == "a"


def test_schedule_part_needs_a_chosen_learner(monkeypatch, tmp_path):
    monkeypatch.setattr(drd, "CACHE", tmp_path)
    monkeypatch.setattr(drd, "signals", lambda r, i: pd.DataFrame())
    with pytest.raises(RuntimeError, match="--part learner"):
        drd.run(None, None, None, "schedule")


def test_score_reads_only_the_named_sets_on_common_rows(monkeypatch, tmp_path):
    import numpy as np
    monkeypatch.setattr(drd, "CACHE", tmp_path)
    idx = pd.bdate_range("2015-01-01", periods=400)
    returns = pd.Series(np.random.default_rng(1).normal(0, 0.01, len(idx)), index=idx)
    target = drd.forward_vol(returns, 5)
    rng = np.random.default_rng(2)
    for s, start in (("F0", 0), ("F1", 10), ("F1n", 0), ("F1[gmm 2]", 0)):
        f = (target + rng.normal(0, 0.05, len(target))).iloc[start:]
        f.rename("forecast").to_csv(drd.cache_path(5, "lasso", s))
    rows = drd.score([(5, "lasso"), (63, "lasso")], ["F0", "F1", "F1n"], returns, 50)
    assert [r["set"] for r in rows] == ["F0", "F1", "F1n"]        # no detector set, no h = 63 (no cache)
    assert len({r["days"] for r in rows}) == 1                   # one common row set per horizon
    assert rows[0]["days"] == target.dropna().iloc[10:].shape[0]
    assert "RMSE" in rows[1] and rows[1]["RMSE"] in ("better", "worse", "no difference")


def test_schedule_pairs_are_the_cached_pairs_outside_the_main_tables(monkeypatch, tmp_path):
    monkeypatch.setattr(drd, "CACHE", tmp_path)
    for h, m, s in ((21, "ols", "F0"), (21, "lasso", "F0"), (5, "lasso", "F0"), (21, "random forest", "F0"),
                    (21, "random forest", "F1"), (63, "mlp", "F1")):
        drd.cache_path(h, m, s).write_text("")
    assert drd.schedule_pairs([(21, "ols"), (21, "lasso")]) == [(5, "lasso"), (21, "random forest")]
