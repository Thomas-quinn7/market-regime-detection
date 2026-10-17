"""The forecast comparison must not leak: calibration is embargoed and the HAR inputs are causal."""
import numpy as np
import pandas as pd
import pytest

from regimes.evaluate import horizon_weights
from regimes.forecast import (
    forward_rv,
    forward_vol,
    har_rv,
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


def test_fred_loader_reads_cache_without_network(tmp_path, monkeypatch):
    import regimes.data as data

    monkeypatch.setattr(data, "DATA_DIR", tmp_path)
    (tmp_path / "fred_BAA10Y.csv").write_text("observation_date,BAA10Y\n2020-01-02,2.1\n2020-01-03,.\n"
                                             "2020-01-06,2.2\n")
    s = data.load_fred_series("BAA10Y")
    assert list(s) == [2.1, 2.2] and s.name == "BAA10Y"


def test_forward_rv_and_har_rv_align_on_a_hand_built_series():
    """forward_rv at t is the RMS of RV over (t, t + horizon]; har_rv at t uses RV up to and including t."""
    idx = pd.bdate_range("2020-01-01", periods=30)
    rv = pd.Series(np.arange(1, 31, dtype=float), index=idx)  # RV_t = t + 1, so everything is checkable by hand
    fwd = forward_rv(rv, horizon=3)
    # at position 0 the next three RVs are 2, 3, 4
    assert fwd.iloc[0] == pytest.approx(np.sqrt((4 + 9 + 16) / 3))
    assert fwd.iloc[26] == pytest.approx(np.sqrt((28 ** 2 + 29 ** 2 + 30 ** 2) / 3))
    assert fwd.iloc[27:].isna().all()  # the last three days have no complete forward window...
    # the shift means a window at the sample end is never produced: exactly 30 - 21 targets exist
    assert forward_rv(rv, horizon=21).notna().sum() == 9
    # the min_periods tolerance applies to missing days INSIDE a window: up to 3 NaNs are averaged over
    gappy = rv.copy()
    gappy.iloc[5:8] = np.nan
    assert forward_rv(gappy, horizon=21).iloc[0] == pytest.approx(np.sqrt(np.nanmean(gappy.iloc[1:22] ** 2)))
    gappy.iloc[8] = np.nan
    assert np.isnan(forward_rv(gappy, horizon=21).iloc[0])  # four missing days: no target
    h = har_rv(rv)
    assert h["rv_1d"].iloc[10] == 11.0
    assert h["rv_5d"].iloc[10] == pytest.approx(np.sqrt(np.mean(np.arange(7, 12) ** 2)))
    assert h["rv_22d"].iloc[25] == pytest.approx(np.sqrt(np.mean(np.arange(5, 27) ** 2)))
    assert np.isnan(h["rv_22d"].iloc[16])  # 17 days < 18 minimum
    assert not np.isnan(h["rv_22d"].iloc[17])  # 18 days are enough
    # the regression target for row t never overlaps its features: features end at t, target starts at t + 1
    rv2 = rv.copy()
    rv2.iloc[11:] = 999.0
    pd.testing.assert_frame_equal(har_rv(rv).iloc[:11], har_rv(rv2).iloc[:11])
    assert forward_rv(rv, 3).iloc[10] != forward_rv(rv2, 3).iloc[10]


def test_qlike_is_pattons_form_up_to_a_per_day_constant():
    """qlike(f, y) = y^2/f^2 - log(y^2/f^2) - 1 equals log(h) + y^2/h with h = f^2, minus the per-day
    constant log(y^2) + 1, so forecast rankings and differences between forecasts are those of Patton (2011)."""
    rng = np.random.default_rng(0)
    y, f, g = rng.uniform(0.5, 2.0, 50), rng.uniform(0.5, 2.0, 50), rng.uniform(0.5, 2.0, 50)
    patton = lambda fc: np.log(fc ** 2) + y ** 2 / fc ** 2  # noqa: E731
    const = np.log(y ** 2) + 1.0
    assert np.allclose(qlike(f, y), patton(f) - const)
    assert np.allclose(qlike(f, y) - qlike(g, y), patton(f) - patton(g))
    # scale-free: scaling forecast and realised together changes nothing
    assert np.allclose(qlike(3 * f, 3 * y), qlike(f, y))
