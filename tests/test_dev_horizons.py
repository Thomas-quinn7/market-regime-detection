"""Tests for examples/dev_horizons.py (stage S8 a): matching implied vol and common rows per horizon."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import dev_horizons as dh  # noqa: E402


def _inputs(n=600):
    idx = pd.bdate_range("2008-01-01", periods=n)
    rng = np.random.default_rng(1)
    returns = pd.Series(rng.normal(0, 1, n), index=idx)
    ivs = pd.DataFrame({"VIX": 20 + rng.normal(0, 1, n), "VIX9D": 19 + rng.normal(0, 1, n),
                        "VIX6M": 22 + rng.normal(0, 1, n)}, index=idx)
    ivs.iloc[:100, ivs.columns.get_loc("VIX9D")] = np.nan      # VIX9D starts late
    prob = pd.Series(rng.random(n), index=idx, name="high_vol_prob").where(np.arange(n) >= 50)  # starts after a warm-up
    noise = pd.Series(rng.standard_normal(n), index=idx)
    return returns, ivs, prob, noise


def test_every_feature_set_at_a_horizon_uses_the_same_rows():
    returns, ivs, prob, noise = _inputs()
    for h, iv in ((5, "VIX9D"), (21, "VIX"), (126, "VIX6M")):
        sets = dh.feature_sets(returns, ivs, h, prob, noise)
        idx = [s.index for s in sets.values()]
        assert all(i.equals(idx[0]) for i in idx)
        assert not any(s.isna().any().any() for s in sets.values())
        assert f"HAR + {iv} + HMM prob" in sets and f"HAR + {iv} + noise" in sets
        start = ivs.index[100] if iv == "VIX9D" else ivs.index[50]
        assert idx[0].min() >= start
        assert "HAR + VIX" in sets and len(sets) == (4 if iv == "VIX" else 6)


def test_comparisons_and_block_follow_the_horizon():
    assert dh.MATCHING_IV == {5: "VIX9D", 10: "VIX9D", 21: "VIX", 63: "VIX", 126: "VIX6M", 252: "VIX"}
    assert ("HAR + VIX9D + noise", "HAR + VIX9D") in dh.comparisons(5)
    assert ("HAR + VIX + HMM prob", "HAR + VIX") in dh.comparisons(126)
    assert len(dh.comparisons(21)) == 3
    rng = np.random.default_rng(0)
    y = np.exp(rng.normal(0, 0.3, 400))
    df = pd.DataFrame({"target": y, "a": y * 1.1, "b": y * 1.3})
    assert dh.compare(df, "a", "b", 126, 50)["block"] == 126
    assert dh.compare(df, "a", "b", 5, 50)["block"] == 63
    assert dh.compare(df, "a", "b", 126, 50)["windows"] == 400 // 126
