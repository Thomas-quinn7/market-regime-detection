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
