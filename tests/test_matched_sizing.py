"""Matched sizing test, tier 1: the calibration tie rule, the expected shortfall and the paired ES-gain
bootstrap behave as the protocol (docs/MATCHED_SIZING_PROTOCOL_2026-10.md) says.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))


def _idx(n):
    return pd.date_range("2010-01-01", periods=n, freq="B")


def test_closest_breaks_ties_to_the_smaller_key():
    import matched_sizing as ms

    assert ms._closest({1: 6.0, 2: 10.0, 3: 12.0}, 8.0) == 1
    assert ms._closest({1: 20.0, 2: 9.0, 3: 7.5}, 8.0) == 3


def test_expected_shortfall_is_the_mean_of_the_worst_one_percent_as_a_loss():
    import matched_sizing as ms

    r = np.concatenate([np.full(198, 0.001), [-0.05, -0.03]])
    assert abs(ms.expected_shortfall(r) - 0.04) < 1e-12  # ceil(0.01 * 200) = 2 worst days


def test_es_gain_is_zero_for_identical_arms_and_positive_when_v_has_the_fatter_tail():
    import matched_sizing as ms

    rng = np.random.default_rng(0)
    h = pd.Series(rng.normal(0, 0.01, 1000), index=_idx(1000))
    p, lo, hi = ms.es_gain_bootstrap(h, h, n_boot=200)
    assert p == 0 and lo == 0 and hi == 0
    p, lo, hi = ms.es_gain_bootstrap(h, 2.0 * h, n_boot=200)
    assert p > 0 and lo > 0
