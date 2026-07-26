"""A shared stress state across assets should show up as high concordance and a breadth spike."""
import numpy as np
import pandas as pd

from regimes.cross_asset import sector_regime_concordance


def _common_regime_panel(seed: int = 7) -> pd.DataFrame:
    """Three assets sharing a calm->storm volatility regime, each with idiosyncratic noise."""
    rng = np.random.default_rng(seed)
    n_calm, n_storm = 500, 500
    common_vol = np.concatenate([np.full(n_calm, 0.5), np.full(n_storm, 3.0)])
    cols = {}
    for name in ("A", "B", "C"):
        cols[name] = rng.normal(0.0, 1.0, n_calm + n_storm) * common_vol
    idx = pd.date_range("2010-01-01", periods=n_calm + n_storm, freq="B")
    return pd.DataFrame(cols, index=idx)


def test_concordance_high_and_breadth_spikes_in_storm():
    panel = _common_regime_panel()
    res = sector_regime_concordance(panel, n_regimes=2)
    # Shared stress state -> sectors' high-vol probabilities move together.
    assert res.mean_pairwise_corr > 0.5
    # Breadth is a valid [0, 1] gauge and is much higher in the storm half.
    assert res.breadth.between(0.0, 1.0).all()
    storm_start = panel.index[500]
    breadth_storm = res.breadth[res.breadth.index >= storm_start].mean()
    breadth_calm = res.breadth[res.breadth.index < storm_start].mean()
    assert breadth_storm > breadth_calm + 0.3


def test_columns_preserved():
    panel = _common_regime_panel()
    res = sector_regime_concordance(panel, n_regimes=2)
    assert list(res.high_vol_prob.columns) == ["A", "B", "C"]


def test_requires_at_least_two_assets():
    panel = _common_regime_panel()[["A"]]
    try:
        sector_regime_concordance(panel)
    except ValueError:
        return
    raise AssertionError("expected ValueError for a single asset")
