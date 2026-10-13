"""Walk-forward GJR-GARCH: out-of-sample, aligned, and responsive to volatility."""
import numpy as np
import pandas as pd

from regimes.garch import walk_forward_gjr


def _returns(n: int = 1200, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    vol = np.where(np.arange(n) % 300 < 150, 0.6, 1.8)
    return pd.Series(vol * rng.standard_normal(n), index=pd.bdate_range("2001-01-01", periods=n))


def test_forecasts_start_at_min_train_and_ignore_later_returns():
    r = _returns()
    wf = walk_forward_gjr(r, min_train=800, step=200, horizon=5)
    assert wf.implied_vol.index[0] == r.index[800] and wf.n_refits == 2
    r2 = r.copy()
    r2.iloc[900:] *= 4
    wf2 = walk_forward_gjr(r2, min_train=800, step=200, horizon=5)
    # Forecasts made up to day 899 used nothing from day 900 on.
    assert np.allclose(wf.implied_vol.iloc[:100], wf2.implied_vol.iloc[:100])
    assert not np.allclose(wf.implied_vol.iloc[100:200], wf2.implied_vol.iloc[100:200])


def test_forecast_is_higher_in_the_volatile_stretch():
    r = _returns()
    v = walk_forward_gjr(r, min_train=800, step=200, horizon=5).implied_vol
    calm, wild = v.loc[r.index[1040]], v.loc[r.index[1190]]  # 140 days into a calm and a wild stretch
    assert wild > 1.5 * calm
