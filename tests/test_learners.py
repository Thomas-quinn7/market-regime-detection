"""Tests for regimes.learners (stage S8 b): determinism, the embargo, and the noise control.

Synthetic data only; no learner is fitted to the S&P 500 here.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("lightgbm")

from regimes.learners import GRIDS, LEARNERS, choose, walk_forward_learner  # noqa: E402

H, N = 5, 1150


def _series(seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2005-01-03", periods=N)
    x1 = pd.Series(rng.normal(0, 0.3, N), index=idx).rolling(10, min_periods=1).mean()
    x2 = pd.Series(rng.normal(0, 1, N), index=idx)
    logvol = 0.8 * x1 + 0.1 * x2 + rng.normal(0, 0.1, N)
    target = np.exp(logvol)
    feats = pd.DataFrame({"x1": x1, "x2": x2})
    noise = pd.Series(np.random.default_rng(99).standard_normal(N), index=idx, name="noise")
    return target, feats, noise


def test_grids_are_the_protocol_grids():
    assert LEARNERS == ("ridge", "lasso", "random forest", "lightgbm", "mlp")
    assert [len(GRIDS[k]) for k in LEARNERS] == [5, 4, 4, 8, 2]


@pytest.mark.parametrize("learner", ["ridge", "lightgbm", "random forest"])
def test_walk_forward_is_deterministic(learner):
    target, feats, _ = _series()
    a = walk_forward_learner(target, feats, learner, horizon=H, step=126, min_rows=756, val=126)
    b = walk_forward_learner(target, feats, learner, horizon=H, step=126, min_rows=756, val=126)
    assert a.forecast.equals(b.forecast)
    assert a.chosen.equals(b.chosen)
    assert a.n_refits == len(range(756 + H, N, 126))


@pytest.mark.parametrize("learner", ["ridge", "lightgbm"])
def test_targets_unknown_at_a_refit_do_not_move_its_forecasts(learner):
    target, feats, _ = _series()
    base = walk_forward_learner(target, feats, learner, horizon=H, step=126, min_rows=756, val=126)
    i0 = 756 + H                              # first refit position
    first_block = feats.index[i0:i0 + 126]
    perturbed = target.copy()
    perturbed.iloc[i0 - H:] = perturbed.iloc[i0 - H:] * 5.0 + 1.0   # every target not yet known at i0
    alt = walk_forward_learner(perturbed, feats, learner, horizon=H, step=126, min_rows=756, val=126)
    assert np.array_equal(base.forecast.loc[first_block].to_numpy(), alt.forecast.loc[first_block].to_numpy())
    later = feats.index[i0 + 126:]
    assert not np.allclose(base.forecast.loc[later].to_numpy(), alt.forecast.loc[later].to_numpy())


def test_a_noise_column_stays_within_noise_of_the_base_set():
    target, feats, noise = _series()
    f0 = walk_forward_learner(target, feats, "ridge", horizon=H, step=126, min_rows=756, val=126).forecast
    f1n = walk_forward_learner(target, feats.join(noise), "ridge", horizon=H, step=126, min_rows=756, val=126).forecast
    y = target.reindex(f0.index)
    rmse = lambda f: float(np.sqrt(((f - y) ** 2).mean()))  # noqa: E731
    assert abs(rmse(f1n) - rmse(f0)) / rmse(f0) < 0.01


def test_choose_validates_on_the_last_rows_and_mlp_returns_epochs():
    target, feats, _ = _series()
    X, y = feats.to_numpy()[:600], np.log(target.to_numpy()[:600])
    best = choose("ridge", X, y, horizon=H, val=100)
    assert best["params"] in GRIDS["ridge"] and best["s2"] > 0 and best["epochs"] is None
    best = choose("mlp", X, y, horizon=H, val=100)
    assert best["params"] in GRIDS["mlp"] and best["epochs"] >= 1
