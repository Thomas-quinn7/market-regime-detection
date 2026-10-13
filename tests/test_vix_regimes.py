"""The joint return/VIX HMM separates two synthetic regimes and orders them by return variance."""
import numpy as np
import pandas as pd

from regimes.vix_regimes import fit_vix_hmm, vix_observations, walk_forward_vix_hmm


def _data(seed: int = 2):
    rng = np.random.default_rng(seed)
    state = (np.arange(1200) // 300) % 2           # calm, storm, calm, storm
    ret = rng.normal(0.0, np.where(state == 1, 2.0, 0.6))
    log_vix = np.where(state == 1, np.log(30.0), np.log(14.0)) + rng.normal(0.0, 0.08, 1200)
    idx = pd.date_range("2010-01-01", periods=1200, freq="B")
    return pd.Series(ret, index=idx), pd.Series(np.exp(log_vix), index=idx), state


def test_fit_recovers_state_vols_in_order():
    r, v, _ = _data()
    params, _ = fit_vix_hmm(vix_observations(r, v).to_numpy())
    vols = np.sqrt(params.cov[:, 0, 0])
    assert vols[0] < vols[1]
    assert abs(vols[0] - 0.6) < 0.1 and abs(vols[1] - 2.0) < 0.3


def test_walk_forward_tracks_the_state_out_of_sample():
    r, v, state = _data()
    res = walk_forward_vix_hmm(r, v, min_train=400, step=100, horizon=21)
    assert res.n_skipped == 0
    hv = res.high_vol_prob
    truth = pd.Series(state, index=r.index).loc[hv.index]
    assert ((hv > 0.5) == (truth == 1)).mean() > 0.95
    assert res.implied_vol.min() > 0.5 and res.implied_vol.max() < 2.5
