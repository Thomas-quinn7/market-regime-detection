"""MSM: transition structure, state layout, filter, forecast and parameter recovery."""
import numpy as np
import pandas as pd

from regimes.msm import (
    MSMParams,
    fit_msm,
    gammas,
    implied_vol,
    msm_filter,
    state_variances,
    transition_matrix,
    walk_forward_msm,
    simulate_msm,
)

P = MSMParams(m0=1.5, sigma=1.0, b=4.0, gamma_k=0.3)


def test_switching_probabilities_rise_to_gamma_k():
    g = gammas(P, 4)
    assert np.all(np.diff(g) > 0)
    assert np.isclose(g[-1], 0.3)


def test_transition_matrix_matches_the_state_layout():
    A = transition_matrix(P, 2)
    assert np.allclose(A.sum(axis=1), 1.0)
    g_slow, g_fast = gammas(P, 2)
    # State 0 = both low, 1 = fast high, 2 = slow high (slowest component is the leading bit).
    assert np.isclose(A[0, 1], (1 - g_slow / 2) * g_fast / 2)
    assert np.isclose(A[0, 2], g_slow / 2 * (1 - g_fast / 2))
    var = state_variances(P, 2)
    assert np.allclose(var, [0.25, 0.75, 0.75, 2.25])


def test_ergodic_forecast_is_the_unconditional_vol():
    k = 3
    uniform = np.full((1, 2 ** k), 1 / 2 ** k)
    assert np.isclose(implied_vol(uniform, P, k, horizon=21)[0], P.sigma)


def test_filter_probabilities_sum_to_one_and_track_volatility():
    k = 3
    r = np.concatenate([np.full(50, 0.3), np.full(50, 3.0)])
    probs, ll = msm_filter(r, P, k)
    assert np.allclose(probs.sum(axis=1), 1.0) and np.isfinite(ll)
    vol = implied_vol(probs, P, k, horizon=1)
    assert vol[-1] > 2 * vol[49]


def test_fit_recovers_parameters_from_simulated_returns():
    k = 3
    truth = MSMParams(m0=1.6, sigma=1.0, b=5.0, gamma_k=0.4)
    r = simulate_msm(truth, k, 4000, seed=1)
    p, _ = fit_msm(r, k)
    assert abs(p.m0 - truth.m0) < 0.1
    assert abs(p.sigma - truth.sigma) / truth.sigma < 0.2


def test_walk_forward_is_out_of_sample():
    k = 2
    r = pd.Series(simulate_msm(P, k, 900, seed=2), index=pd.bdate_range("2001-01-01", periods=900))
    wf = walk_forward_msm(r, k, min_train=600, step=150, horizon=5)
    first = wf.implied_vol.index[0]
    # Changing returns after a forecast's date must not change that forecast.
    r2 = r.copy()
    r2.iloc[700:] *= 5
    wf2 = walk_forward_msm(r2, k, min_train=600, step=150, horizon=5)
    assert first == r.index[600] and wf.n_refits == 2
    assert np.allclose(wf.implied_vol.iloc[:100], wf2.implied_vol.iloc[:100])
