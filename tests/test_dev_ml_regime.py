"""Tests for examples/dev_ml_regime.py (stage S8 b): feature sets and rows, on synthetic data only."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import dev_ml_regime as dm  # noqa: E402


def test_feature_sets_rows_and_columns():
    n = 500
    idx = pd.bdate_range("2008-01-01", periods=n)
    rng = np.random.default_rng(0)
    returns = pd.Series(rng.normal(0, 1, n), index=idx)
    ivs = pd.DataFrame({k: 20 + rng.normal(0, 1, n) for k in ("VIX", "VIX9D", "VIX3M", "VIX6M")}, index=idx)
    ivs.iloc[:150, ivs.columns.get_loc("VIX9D")] = np.nan
    prob = pd.Series(rng.random(n), index=idx).where(np.arange(n) >= 40)
    noise = pd.Series(rng.standard_normal(n), index=idx)
    s = dm.feature_sets(returns, ivs, prob, noise)
    assert s["F0"].index.equals(s["F1"].index) and s["F1"].index.equals(s["F1n"].index)
    assert s["F0@F2"].index.equals(s["F2"].index)
    assert s["F1"].index.min() == idx[40]
    assert s["F2"].index.min() >= idx[150]
    assert list(s["F1"].columns) == ["rv_1d", "rv_5d", "rv_22d", "vix", "hmm_prob"]
    assert s["F2"].shape[1] == 4 + 21 + 2 + 3
    assert not any(v.isna().any().any() for v in s.values())
    # F2's lags are lags: column absr_lag1 on day t is log|r| of day t-1
    t = s["F2"].index[5]
    prev = returns.index[returns.index.get_loc(t) - 1]
    assert np.isclose(s["F2"].loc[t, "absr_lag1"], np.log(max(abs(returns.loc[prev]), 1e-3)))


def test_learners_by_horizon_follow_the_protocol():
    assert dm.learners_at(126) == ("ols", "ridge", "lasso", "random forest", "lightgbm")
    assert dm.learners_at(21)[-1] == "mlp"


def test_cache_path_follows_the_cache_folder(monkeypatch, tmp_path):
    monkeypatch.setattr(dm, "CACHE", tmp_path)
    assert dm.cache_path(21, "random forest", "F0@F2") == tmp_path / "h021__random_forest__F0_at_F2.csv"
