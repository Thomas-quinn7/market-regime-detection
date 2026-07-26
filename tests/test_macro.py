"""Macro quadrant regimes (P4, Tier 1). Tests the pure logic offline (no FRED key / network): the
point-in-time alignment is causal, the quadrant classifier is correct, and the weight map is valid.
The live FRED pull is exercised by examples/macro_quadrants.py.
"""
import numpy as np
import pandas as pd

from regimes.macro import macro_quadrant, quadrant_weights, to_point_in_time


def test_point_in_time_alignment_is_causal():
    obs_values = pd.Series([1.0, 2.0])
    pub_dates = pd.Series(pd.to_datetime(["2020-02-15", "2020-03-15"]))  # published after the reference month
    daily = pd.date_range("2020-01-01", "2020-04-01", freq="D")
    s = to_point_in_time(obs_values, pub_dates, daily)
    assert np.isnan(s.loc["2020-02-14"])          # nothing known before the first publication
    assert s.loc["2020-02-15"] == 1.0             # first value appears on its publication date
    assert s.loc["2020-03-14"] == 1.0             # and holds until the next publication
    assert s.loc["2020-03-15"] == 2.0             # second value only from its publication date


def _monotone_features(growth_dir: int, infl_dir: int, n: int = 300) -> pd.DataFrame:
    t = np.arange(n, dtype=float)
    idx = pd.date_range("2010-01-01", periods=n, freq="B")
    return pd.DataFrame({"growth": growth_dir * t, "inflation": infl_dir * t}, index=idx)


def test_quadrant_classification_all_four_boxes():
    cases = {
        (1, -1): "goldilocks",   # growth rising, inflation falling
        (1, 1): "overheating",   # growth rising, inflation rising
        (-1, 1): "stagflation",  # growth falling, inflation rising
        (-1, -1): "slowdown",    # growth falling, inflation falling
    }
    for (gd, idr), expected in cases.items():
        q = macro_quadrant(_monotone_features(gd, idr), trend_window=20)["quadrant"].dropna()
        assert len(q) > 0
        assert (q == expected).all()


def test_quadrant_weights_valid_and_correct():
    q = pd.Series(["goldilocks", "overheating", "stagflation", "slowdown"],
                  index=pd.date_range("2010-01-01", periods=4, freq="B"))
    w = quadrant_weights(q)
    assert np.allclose(w.sum(axis=1), 1.0)
    assert w.loc[q.index[0], "equity"] == 1.0
    assert w.loc[q.index[1], "equity"] == 0.6 and w.loc[q.index[1], "cash"] == 0.4
    assert w.loc[q.index[2], "cash"] == 1.0
    assert w.loc[q.index[3], "bonds"] == 1.0
