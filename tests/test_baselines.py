"""The trailing-vol baselines a regime model is compared against must be causal and scored fairly.

A baseline that peeked at the future would flatter itself and make the regime model look worse than
it is, so the same no-look-ahead guarantee applies here as to the filtered probabilities.
"""
import numpy as np
import pandas as pd

from regimes.allocation import regime_switch_weights, vol_threshold_signal
from regimes.evaluate import (
    compare_vol_predictors,
    ewma_vol,
    incremental_r2,
    oos_realised_vol_check,
    realised_vol,
)
from regimes.model import fit_regimes


def _series(seed: int = 5) -> pd.Series:
    rng = np.random.default_rng(seed)
    calm = rng.normal(0.0, 0.5, size=400)
    storm = rng.normal(0.0, 3.0, size=400)
    y = np.concatenate([calm, storm, calm[:200]])
    idx = pd.date_range("2011-01-01", periods=len(y), freq="B")
    return pd.Series(y, index=idx, name="log_return_pct")


def test_ewma_vol_ignores_the_future():
    y = _series()
    cut = 500
    full = ewma_vol(y)
    truncated = ewma_vol(y.iloc[:cut])
    assert np.allclose(full.iloc[:cut].to_numpy(), truncated.to_numpy(), atol=1e-12)


def test_ewma_vol_tracks_variance_regimes():
    v = ewma_vol(_series())
    assert v.iloc[300:400].mean() < v.iloc[700:800].mean()


def test_compare_vol_predictors_scores_on_common_dates():
    y = _series()
    fut = realised_vol(y, 21).shift(-21)
    noisy = fut + np.random.default_rng(0).normal(0.0, 0.5, len(fut))
    short = realised_vol(y, 21).iloc[100:]  # fewer dates: everything must be scored on these
    out = compare_vol_predictors({"oracle": fut, "noisy": noisy, "rv21": short}, y, horizon=21)
    assert abs(out.loc["oracle", "pearson"] - 1.0) < 1e-12
    assert out.loc["noisy", "pearson"] < out.loc["oracle", "pearson"]
    assert (out["n"] == len(fut.iloc[100:].dropna())).all()


def test_incremental_r2_adds_nothing_for_a_redundant_input():
    y = _series()
    fut = realised_vol(y, 21).shift(-21)
    base = realised_vol(y, 21)
    r2_base, r2_both = incremental_r2(fut, base, base * 2.0)
    assert 0.0 < r2_base < 1.0
    assert abs(r2_both - r2_base) < 1e-9


def test_oos_check_can_be_restricted_to_given_dates():
    y = _series()
    fit = fit_regimes(y, n_regimes=2)
    full = oos_realised_vol_check(y, fit, horizon=21)
    part = oos_realised_vol_check(y, fit, horizon=21, index=y.index[300:])
    assert part.n == full.n - 300


def test_vol_threshold_signal_flags_and_drops_undefined():
    vol = pd.Series([np.nan, 10.0, 25.0, 20.0], index=pd.date_range("2010-01-01", periods=4, freq="B"))
    sig = vol_threshold_signal(vol, 20.0)
    assert list(sig) == [0.0, 1.0, 1.0]
    w = regime_switch_weights(sig)
    assert list(w["equity"]) == [1.0, 0.0, 0.0]
