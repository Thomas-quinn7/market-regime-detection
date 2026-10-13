"""The forecast comparison must not leak: calibration is embargoed and the HAR inputs are causal."""
import numpy as np
import pandas as pd

from regimes.evaluate import horizon_weights
from regimes.forecast import (
    forward_vol,
    har_features,
    qlike,
    walk_forward_regression,
)


def _returns(n: int = 1200, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    vol = np.where((np.arange(n) // 200) % 2 == 0, 0.6, 2.0)
    idx = pd.date_range("2010-01-01", periods=n, freq="B")
    return pd.Series(rng.normal(0.0, vol), index=idx)


def test_horizon_weights_are_row_stochastic():
    A = np.array([[0.98, 0.02], [0.05, 0.95]])
    W = horizon_weights(A, 21)
    assert np.allclose(W.sum(axis=1), 1.0)
    assert np.allclose(horizon_weights(A, 1), A)


def test_har_features_ignore_the_future():
    r = _returns()
    changed = r.copy()
    changed.iloc[700:] *= 5.0
    a, b = har_features(r).iloc[:700], har_features(changed).iloc[:700]
    pd.testing.assert_frame_equal(a, b)


def test_regression_is_embargoed_against_target_overlap():
    """Targets that were not yet known at a refit date must not change that refit's forecasts."""
    r = _returns()
    y = forward_vol(r, 21)
    X = har_features(r)
    base = walk_forward_regression(y, X, horizon=21, step=63, min_rows=252)
    first_edge = base.forecast.index[0]
    pos = X.dropna().index.get_loc(first_edge)
    # Rewrite every target from (edge - horizon) onward: none of those was known at the edge.
    tampered = y.copy()
    tampered.loc[X.dropna().index[pos - 21]:] = 99.0
    again = walk_forward_regression(tampered, X, horizon=21, step=63, min_rows=252)
    block = base.forecast.index[:63]
    pd.testing.assert_series_equal(base.forecast.loc[block], again.forecast.loc[block])
    # ...whereas one row earlier was known, and changing it does move the forecast.
    tampered.loc[X.dropna().index[pos - 22]] = 99.0
    moved = walk_forward_regression(tampered, X, horizon=21, step=63, min_rows=252)
    assert not np.allclose(base.forecast.loc[block], moved.forecast.loc[block])


def test_qlike_is_zero_for_a_perfect_forecast_and_positive_otherwise():
    y = np.array([0.5, 1.0, 2.0])
    assert np.allclose(qlike(y, y), 0.0)
    assert (qlike(y * 1.3, y) > 0).all() and (qlike(y * 0.7, y) > 0).all()
    # QLIKE punishes under-forecasting more than the same-sized over-forecast.
    assert qlike(np.array([0.5]), np.array([1.0]))[0] > qlike(np.array([2.0]), np.array([1.0]))[0]
