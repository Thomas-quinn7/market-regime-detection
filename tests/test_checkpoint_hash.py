"""The walk-forward checkpoint is tied to the input values, not only to the span (desk, quant-dev F2;
joint desk review 2026-10-18 finding 9)."""
import json

import numpy as np
import pandas as pd
import pytest

from regimes.evaluate import series_sha256, walk_forward_oos


def _series(seed: int = 0, n: int = 320) -> pd.Series:
    rng = np.random.default_rng(seed)
    x = np.where(np.arange(n) % 80 < 40, 0.5, 2.0) * rng.standard_normal(n)
    return pd.Series(x, index=pd.bdate_range("2001-01-01", periods=n))


def test_series_sha256_depends_on_values_and_dates():
    y = _series()
    a = series_sha256(y)
    assert a == series_sha256(y.copy()) and len(a) == 64
    z = y.copy()
    z.iloc[100] += 1e-9
    assert series_sha256(z) != a
    w = pd.Series(y.to_numpy(), index=pd.bdate_range("2001-01-02", periods=len(y)))
    assert series_sha256(w) != a


def test_checkpoint_rejects_changed_values_inside_the_span(tmp_path):
    y = _series()
    r1 = walk_forward_oos(y, min_train=200, step=60, horizon=5, checkpoint_dir=tmp_path)
    saved = json.loads((tmp_path / "settings.json").read_text())
    assert saved["input_sha256"] == series_sha256(y)
    # same n, first and last date; one value revised inside the window
    z = y.copy()
    z.iloc[150] *= 3.0
    with pytest.raises(ValueError, match="different settings or data"):
        walk_forward_oos(z, min_train=200, step=60, horizon=5, checkpoint_dir=tmp_path)
    # the unchanged series loads from the checkpoint and gives the same forecast
    r2 = walk_forward_oos(y, min_train=200, step=60, horizon=5, checkpoint_dir=tmp_path)
    pd.testing.assert_series_equal(r1.implied_vol, r2.implied_vol)
    assert (r2.convergence["detail"] == "loaded from checkpoint").all()


def test_legacy_checkpoint_without_hash_is_accepted_once_with_a_warning(tmp_path):
    y = _series()
    walk_forward_oos(y, min_train=200, step=60, horizon=5, checkpoint_dir=tmp_path)
    sfile = tmp_path / "settings.json"
    legacy = json.loads(sfile.read_text())
    del legacy["input_sha256"]
    sfile.write_text(json.dumps(legacy))
    with pytest.warns(RuntimeWarning, match="predates input hashing"):
        walk_forward_oos(y, min_train=200, step=60, horizon=5, checkpoint_dir=tmp_path)
    assert json.loads(sfile.read_text())["input_sha256"] == series_sha256(y)
    # a legacy file whose span disagrees is still refused
    legacy["n"] += 1
    sfile.write_text(json.dumps(legacy))
    with pytest.raises(ValueError):
        walk_forward_oos(y, min_train=200, step=60, horizon=5, checkpoint_dir=tmp_path)
