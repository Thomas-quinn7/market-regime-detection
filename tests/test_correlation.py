"""The stock-bond correlation HMM must recover correlation regimes and stay causal."""
import numpy as np
import pandas as pd

from regimes.correlation import (
    devolatilise,
    ewma_corr,
    filter_probs,
    fit_corr_hmm,
    forward_corr,
    trailing_corr,
    walk_forward_corr_regimes,
)


def _two_regime_pairs(seed: int = 7, n_each: int = 500) -> pd.DataFrame:
    """Unit-variance pairs: correlation -0.6, then +0.6, then -0.6 again."""
    rng = np.random.default_rng(seed)
    blocks = []
    for rho in (-0.6, 0.6, -0.6):
        cov = np.array([[1.0, rho], [rho, 1.0]])
        blocks.append(rng.multivariate_normal([0.0, 0.0], cov, size=n_each))
    x = np.vstack(blocks)
    idx = pd.date_range("2010-01-01", periods=len(x), freq="B")
    return pd.DataFrame(x, index=idx, columns=["equity", "bonds"])


def test_fit_recovers_both_correlations():
    params, _ = fit_corr_hmm(_two_regime_pairs().to_numpy(), n_regimes=2)
    assert params.rho[0] < -0.45 and params.rho[1] > 0.45  # ordered ascending
    assert np.allclose(params.A.sum(axis=1), 1.0)


def test_filtered_probs_ignore_the_future():
    z = _two_regime_pairs().to_numpy()
    params, _ = fit_corr_hmm(z, n_regimes=2)
    cut = 700
    assert np.allclose(filter_probs(z, params)[:cut], filter_probs(z[:cut], params), atol=1e-12)


def test_filtered_probs_track_the_positive_regime():
    z = _two_regime_pairs().to_numpy()
    params, _ = fit_corr_hmm(z, n_regimes=2)
    p_high = filter_probs(z, params)[:, -1]
    assert p_high[550:1000].mean() > 0.8 and p_high[1050:].mean() < 0.2


def test_devolatilise_is_causal_and_uses_yesterdays_vol():
    x = _two_regime_pairs()
    full = devolatilise(x)
    part = devolatilise(x.iloc[:600])
    assert np.allclose(full.iloc[:599].to_numpy(), part.to_numpy())
    assert full.index[0] == x.index[1]


def test_correlation_helpers():
    x = _two_regime_pairs()
    tc = trailing_corr(x, 63)
    assert tc.iloc[400] < -0.3 and tc.iloc[900] > 0.3
    assert ewma_corr(x).iloc[900] > 0.3
    # the forward target at t is the trailing value at t + horizon
    assert np.isclose(forward_corr(x, 63).iloc[100], tc.iloc[163])


def test_walk_forward_corr_starts_oos_at_min_train():
    x = _two_regime_pairs()
    res = walk_forward_corr_regimes(x, min_train=400, step=200, horizon=21)
    z_index = devolatilise(x).index
    assert res.prob_high.index.min() == z_index[400]
    assert res.n_skipped == 0 and res.n_refits >= 1
    assert res.implied_corr.between(-1.0, 1.0).all()


def test_tied_variances_share_variances_and_keep_correlations():
    x = _two_regime_pairs()
    x.iloc[:, 0] *= np.where(np.arange(len(x)) % 50 < 3, 3.0, 1.0)  # short variance bursts
    params, _ = fit_corr_hmm(x.to_numpy(), n_regimes=2, tie_variances=True)
    var = np.einsum("kii->ki", params.cov)
    assert np.allclose(var[0], var[1])
    assert params.rho[0] < -0.3 and params.rho[1] > 0.3


def test_sustained_sign_state_is_causal_and_needs_a_full_run():
    from regimes.correlation import sustained_sign_state

    idx = pd.date_range("2010-01-01", periods=60, freq="B")
    sig = pd.Series([-1.0] * 30 + [1.0] * 30, index=idx)
    state = sustained_sign_state(sig, run=10)
    assert np.isnan(state.iloc[8]) and state.iloc[9] == -1.0
    assert state.iloc[38] == -1.0 and state.iloc[39] == 1.0  # switch dated on the 10th positive day
    assert np.allclose(sustained_sign_state(sig.iloc[:45], run=10).to_numpy(),
                       state.iloc[:45].to_numpy(), equal_nan=True)


def test_regime_flips_ignore_short_runs_and_scoring():
    from regimes.correlation import regime_flips, score_detection, sustained_sign_state

    idx = pd.date_range("2000-01-01", periods=600, freq="B")
    vals = [-0.5] * 200 + [0.4] * 20 + [-0.5] * 80 + [0.5] * 300  # the 20-day blip is noise
    target = pd.Series(vals, index=idx)
    flips = regime_flips(target, min_len=126)
    assert flips == [(idx[300], 1)]
    # a signal that turns 15 days late, plus one spurious early switch
    sig = pd.Series(vals, index=idx).shift(15).fillna(-0.5)
    sig.iloc[100:130] = 0.3
    lags, misses, false_alarms = score_detection(sustained_sign_state(sig, run=10), flips)
    assert misses == 0 and lags == [24.0]  # 15 days late + 10-day confirmation - 1
    # 4 switches that no lasting flip explains: the spurious one up and back (days 100-130), and
    # following the target's own 20-day blip up and back, which is too short to be a regime.
    assert false_alarms == 4
