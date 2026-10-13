"""Walk-forward OOS must (a) stay causal and (b) still separate regimes out of sample.

Synthetic series: calm (low variance) then storm (high variance). Even under strict walk-forward with
frozen parameters, the out-of-sample high-vol probability should be clearly higher during the storm
portion than during the (out-of-sample) calm portion.
"""
import numpy as np
import pandas as pd

from regimes.evaluate import walk_forward_oos


def _series(seed: int = 3) -> pd.Series:
    rng = np.random.default_rng(seed)
    calm = rng.normal(0.0, 0.5, size=500)
    storm = rng.normal(0.0, 3.0, size=500)
    y = np.concatenate([calm, storm])
    idx = pd.date_range("2010-01-01", periods=len(y), freq="B")
    return pd.Series(y, index=idx, name="log_return_pct")


def test_walk_forward_produces_oos_span_and_refits():
    y = _series()
    res = walk_forward_oos(y, min_train=300, step=100, horizon=21)
    # OOS span begins exactly at min_train, never before.
    assert res.high_vol_prob.index.min() == y.index[300]
    assert res.n_refits >= 1
    assert res.n_skipped == 0


def test_walk_forward_high_vol_prob_higher_in_storm():
    y = _series()
    res = walk_forward_oos(y, min_train=300, step=100, horizon=21)
    hv = res.high_vol_prob
    storm_start = y.index[500]
    calm_oos = hv[hv.index < storm_start].mean()   # OOS calm tail (dates 300..500)
    storm_oos = hv[hv.index >= storm_start].mean()  # OOS storm (dates 500..1000)
    assert storm_oos > calm_oos + 0.3


def test_walk_forward_probs_are_valid_probabilities():
    y = _series()
    res = walk_forward_oos(y, min_train=300, step=100, horizon=21)
    assert res.high_vol_prob.between(0.0, 1.0).all()


def test_walk_forward_implied_vol_is_between_the_state_vols():
    y = _series()
    res = walk_forward_oos(y, min_train=300, step=100, horizon=21)
    iv = res.implied_vol
    assert iv.index.equals(res.high_vol_prob.index)
    # A mixture of the two state vols: above the calm one, below the storm one.
    assert iv.min() > 0.3 and iv.max() < 3.5
    assert iv[iv.index >= y.index[500]].mean() > iv[iv.index < y.index[500]].mean() + 1.0
