"""Tests for examples/dev_ml_race.py (stage S8 c): the tercile split uses only each refit's training VIX."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import dev_ml_race as race  # noqa: E402


def test_terciles_cut_on_training_rows_only():
    n, h = 1100, 21
    idx = pd.bdate_range("2008-01-01", periods=n)
    vix = pd.Series(np.r_[np.linspace(10, 40, 777), np.full(n - 777, 25.0)], index=idx)
    lab = race.terciles(idx, idx, vix, h)
    assert lab.iloc[: 756 + h].isna().all()
    # training VIX at the first refit is linspace(10, 40) over 756 rows: cut points 20 and 30
    assert (lab.iloc[756 + h: 756 + h + 63] == "middle").all()
    # a VIX spike after the first block moves no label in the first block
    vix2 = vix.copy()
    vix2.iloc[756 + h + 63:] = 80.0
    lab2 = race.terciles(idx, idx, vix2, h)
    assert lab2.iloc[: 756 + h + 63].equals(lab.iloc[: 756 + h + 63])
    assert (lab2.iloc[756 + h + 63:] == "high").all()


def test_race_cache_names(monkeypatch, tmp_path):
    monkeypatch.setattr(race, "CACHE", tmp_path)
    assert race.cache_path(5, "gru", "F1n") == tmp_path / "h005__gru__F1n.csv"
    assert race.HORIZONS == (5, 21, 63) and race.SETS == ("F0", "F1", "F1n")


def test_worse_in_mcs_counts_only_worse_and_kept():
    vs = pd.DataFrame({"h": [21, 21, 21, 5], "forecast": ["a", "b", "c", "a"],
                       "RMSE": ["worse", "worse", "no difference", "worse"],
                       "QLIKE": ["worse", "better", "worse", "no difference"]})
    in_set = {(21, "RMSE", "a"): True, (21, "RMSE", "b"): False, (21, "RMSE", "c"): True,
              (21, "QLIKE", "a"): False, (21, "QLIKE", "b"): True, (21, "QLIKE", "c"): True,
              (5, "RMSE", "a"): True, (5, "QLIKE", "a"): True}
    out = race.worse_in_mcs(vs, in_set).set_index(["h", "loss"])
    assert out.loc[(21, "RMSE"), "worse than HAR + VIX"] == 2
    assert out.loc[(21, "RMSE"), "of which in the MCS"] == 1
    assert out.loc[(21, "RMSE"), "forecasts"] == "a"
    assert out.loc[(21, "QLIKE"), "of which in the MCS"] == 1  # c only; a is worse but not kept
    assert out.loc[(21, "QLIKE"), "forecasts"] == "c"
    assert out.loc[(5, "QLIKE"), "worse than HAR + VIX"] == 0
    assert out.loc[(5, "QLIKE"), "forecasts"] == "-"
