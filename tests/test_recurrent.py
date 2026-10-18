"""Tests for regimes.recurrent (stage S8 c): sequence alignment, determinism, the best-epoch snapshot,
and the embargo. Synthetic data only, with a cut-down grid and epoch cap so the tests run in seconds."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

pytest.importorskip("torch")

from regimes import recurrent as rc  # noqa: E402

H, N, SEQ, STEP, MIN, VAL = 5, 420, 10, 100, 200, 50


@pytest.fixture(autouse=True)
def small(monkeypatch):
    monkeypatch.setattr(rc, "GRID", [{"hidden": 4, "weight_decay": 0.0}])
    monkeypatch.setattr(rc, "MAX_EPOCHS", 6)
    monkeypatch.setattr(rc, "PATIENCE", 3)


def _series(seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2005-01-03", periods=N)
    x1 = pd.Series(rng.normal(0, 0.3, N), index=idx).rolling(10, min_periods=1).mean()
    x2 = pd.Series(rng.normal(0, 1, N), index=idx)
    target = np.exp(0.8 * x1 + 0.1 * x2 + rng.normal(0, 0.1, N))
    return target, pd.DataFrame({"x1": x1, "x2": x2})


def _wf(target, feats, kind="gru"):
    return rc.walk_forward_recurrent(target, feats, kind, horizon=H, step=STEP, min_rows=MIN, val=VAL, seq=SEQ)


def test_windows_end_on_the_row_and_refuse_short_history():
    X = np.arange(20, dtype=float).reshape(10, 2)
    w = rc.windows(X, np.array([3, 9]), seq=4)
    assert w.shape == (2, 4, 2)
    assert np.array_equal(w[0], X[0:4]) and np.array_equal(w[1], X[6:10])
    with pytest.raises(ValueError):
        rc.windows(X, np.array([2]), seq=4)


@pytest.mark.parametrize("kind", ["lstm", "gru"])
def test_walk_forward_is_deterministic(kind):
    target, feats = _series()
    a, b = _wf(target, feats, kind), _wf(target, feats, kind)
    assert a.forecast.equals(b.forecast) and a.chosen.equals(b.chosen)
    assert a.n_refits == len(range(MIN + H, N, STEP))


def test_best_epoch_snapshot_equals_a_retrain_to_that_epoch():
    target, feats = _series()
    X = rc._scaled(feats.to_numpy(), np.arange(SEQ - 1, 300))
    y = np.log(target.to_numpy())
    fit_rows, val_rows = np.arange(SEQ - 1, 250), np.arange(260, 300)
    Xw, Xv = rc.windows(X, fit_rows, SEQ), rc.windows(X, val_rows, SEQ)
    m = rc.RecurrentModel("lstm", 4, 0.0).fit(Xw, y[fit_rows], Xv, y[val_rows])
    again = rc.RecurrentModel("lstm", 4, 0.0, epochs=m.epochs).fit(Xw, y[fit_rows])
    assert m.epochs >= 1
    assert np.array_equal(m.predict(Xv), again.predict(Xv))


def test_targets_unknown_at_a_refit_do_not_move_its_forecasts():
    target, feats = _series()
    base = _wf(target, feats)
    i0 = MIN + H
    first_block = feats.index[i0:i0 + STEP]
    perturbed = target.copy()
    perturbed.iloc[i0 - H:] = perturbed.iloc[i0 - H:] * 5.0 + 1.0
    alt = _wf(perturbed, feats)
    assert np.array_equal(base.forecast.loc[first_block].to_numpy(), alt.forecast.loc[first_block].to_numpy())
    later = feats.index[i0 + STEP:]
    assert not np.allclose(base.forecast.loc[later].to_numpy(), alt.forecast.loc[later].to_numpy())


def test_grid_is_the_protocol_grid():
    import importlib
    fresh = importlib.reload(rc)
    assert fresh.GRID == [{"hidden": 8, "weight_decay": 0.0}, {"hidden": 8, "weight_decay": 0.0001},
                          {"hidden": 16, "weight_decay": 0.0}, {"hidden": 16, "weight_decay": 0.0001}]
    assert (fresh.SEQ, fresh.BATCH, fresh.MAX_EPOCHS, fresh.PATIENCE, fresh.LR) == (66, 64, 200, 20, 0.001)
