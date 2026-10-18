"""Tests for regimes.detectors (stage S8 d): causality and the summary helpers. Synthetic data only."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("sklearn")
pytest.importorskip("ruptures")

from regimes.detectors import DETECTORS, persistence, rand_agreement, rolling_features, walk_forward_detector  # noqa: E402

N, MIN_TRAIN, STEP = 520, 300, 100


def _inputs(shock_at=None):
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2008-01-01", periods=N)
    vol = np.where((np.arange(N) // 80) % 2 == 0, 0.8, 2.0)
    r = pd.Series(rng.normal(0, 1, N) * vol, index=idx)
    vix = pd.Series(16 * vol + rng.normal(0, 1, N), index=idx)
    if shock_at is not None:
        r.iloc[shock_at] = 15.0
        vix.iloc[shock_at] = 80.0
    return rolling_features(r, vix)


@pytest.mark.parametrize("name", DETECTORS)
def test_a_shock_at_day_t_moves_nothing_before_t(name):
    t = 410
    base = walk_forward_detector(_inputs(), name, min_train=MIN_TRAIN, step=STEP)
    shocked = walk_forward_detector(_inputs(shock_at=t), name, min_train=MIN_TRAIN, step=STEP)
    t_date = pd.bdate_range("2008-01-01", periods=N)[t]
    before = base.index[base.index < t_date]
    assert len(before) > 50
    pd.testing.assert_frame_equal(base.loc[before], shocked.loc[before])


@pytest.mark.parametrize("name", ["kmeans 2", "gmm 2", "changepoint"])
def test_detectors_find_the_high_vol_blocks(name):
    out = walk_forward_detector(_inputs(), name, min_train=MIN_TRAIN, step=STEP)
    idx = pd.bdate_range("2008-01-01", periods=N)
    high = pd.Series(((np.arange(N) // 80) % 2 == 1).astype(float), index=idx).reindex(out.index)
    # skip the first 22 days of each block, where the 22-day features are still catching up
    pos = np.arange(N)[np.isin(idx, out.index)]
    settled = (pos % 80) >= 22
    agree = (out["signal"].round() == high).to_numpy()[settled].mean()
    assert agree > 0.8


def test_persistence_and_rand():
    a = pd.Series([0, 0, 0, 1, 1, 1, 0, 0], dtype=float)
    assert persistence(a) == pytest.approx(5 / 7)
    assert rand_agreement(a, 1 - a) == pytest.approx(1.0)
    assert rand_agreement(a, pd.Series([0, 1, 0, 1, 0, 1, 0, 1], dtype=float)) < 0.2
