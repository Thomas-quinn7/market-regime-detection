"""Tests for examples/dev_continuations.py (development-only horizon and nesting-noise continuations)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

import dev_continuations as dc  # noqa: E402
from regimes.forecast import forward_vol  # noqa: E402


def _synthetic(n: int = 1700, seed: int = 3) -> tuple[pd.Series, pd.Series]:
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2005-01-03", periods=n)
    vol = np.where(rng.random(n) < 0.2, 2.0, 0.8)
    returns = pd.Series(rng.normal(0, vol), index=idx)
    vix = pd.Series(np.clip(vol * np.sqrt(252) * np.exp(rng.normal(0, 0.1, n)), 5, None), index=idx)
    return returns, vix


def test_forecasts_at_horizon_scores_the_right_target_and_adds_noise_only_when_asked():
    returns, vix = _synthetic()
    df = dc.forecasts_at_horizon(returns, vix, 5)
    assert list(df.columns) == ["target", "HAR", "HAR + VIX", "HAR + HMM prob", "HAR + VIX + HMM prob"]
    assert len(df) > 100 and df.notna().all().all()
    expected = forward_vol(returns, 5).reindex(df.index)
    assert np.allclose(df["target"], expected)
    assert df.attrs["n_refits"] > 0 and 0 <= df.attrs["converged"] <= df.attrs["n_refits"]
    noise = pd.Series(np.random.default_rng(0).standard_normal(len(returns)), index=returns.index)
    with_noise = dc.forecasts_at_horizon(returns, vix, 5, noise=noise)
    assert "HAR + VIX + noise" in with_noise.columns
    # the shared columns do not depend on the extra model being present
    assert np.allclose(with_noise["HAR + VIX"], df["HAR + VIX"].reindex(with_noise.index))


def test_compare_row_is_deterministic_and_well_formed():
    rng = np.random.default_rng(0)
    idx = pd.bdate_range("2010-01-01", periods=400)
    y = np.exp(rng.normal(0, 0.3, 400))
    df = pd.DataFrame({"target": y, "A": y * np.exp(rng.normal(0, 0.2, 400)), "B": y * np.exp(rng.normal(0, 0.4, 400))}, index=idx)
    a = dc.compare(df, "A", "B", n_boot=100, block=21)
    b = dc.compare(df, "A", "B", n_boot=100, block=21)
    assert a == b
    assert a["RMSE"] in {"better", "worse", "no difference"} and a["block"] == 21
    assert a["RMSE"] == "better"  # A has the smaller noise, by construction
