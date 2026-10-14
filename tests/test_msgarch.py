"""MS-GARCH: exact forecast, filter, parameter recovery and the out-of-sample walk-forward."""
import numpy as np
import pandas as pd

from regimes.msgarch import (
    MSGarchParams,
    _pack,
    _unpack,
    ergodic,
    fit_msgarch,
    forecast_variance,
    msgarch_filter,
    simulate_msgarch,
    walk_forward_msgarch,
)

INF = np.inf
P2 = MSGarchParams(omega=np.array([0.02, 0.3]), alpha=np.array([0.03, 0.08]),
                   gamma=np.array([0.06, 0.1]), beta=np.array([0.9, 0.7]),
                   P=np.array([[0.98, 0.02], [0.05, 0.95]]), nu=np.array([INF, INF]))


def test_one_regime_forecast_is_the_gjr_closed_form():
    p = MSGarchParams(np.array([0.05]), np.array([0.05]), np.array([0.1]), np.array([0.85]),
                      np.ones((1, 1)), np.array([INF]))
    lr, s = p.unconditional_variance()[0], p.persistence()[0]
    h1 = 3.0
    expected = np.mean([lr + s ** j * (h1 - lr) for j in range(10)])
    got = forecast_variance(np.ones((1, 1)), np.array([[h1]]), p, horizon=10)[0]
    assert np.isclose(got, expected)


def test_two_regime_forecast_matches_monte_carlo():
    rng = np.random.default_rng(0)
    pi, h1, horizon, n = np.array([0.3, 0.7]), np.array([0.5, 4.0]), 10, 400_000
    exact = forecast_variance(pi[None, :], h1[None, :], P2, horizon)[0]
    # Simulate forward from the filtered state: regime drawn from pi, then the chain and every
    # regime's variance recursion run on the simulated returns.
    s = (rng.random(n) < pi[1]).astype(int)
    h = np.tile(h1, (n, 1))
    sq = np.zeros(n)
    for _ in range(horizon):
        s = np.where(rng.random(n) < P2.P[s, 1], 1, 0)
        r = np.sqrt(h[np.arange(n), s]) * rng.standard_normal(n)
        sq += r ** 2
        h = P2.omega + (P2.alpha + P2.gamma * (r < 0)[:, None]) * (r ** 2)[:, None] + P2.beta * h
    assert abs(sq.mean() / horizon / exact - 1) < 0.01


def test_long_horizon_forecast_converges_to_the_process_variance():
    # Far ahead the forecast forgets today's state, so two very different starting points agree.
    a = forecast_variance(np.array([[1.0, 0.0]]), np.array([[0.2, 1.0]]), P2, horizon=5000)[0]
    b = forecast_variance(np.array([[0.0, 1.0]]), np.array([[3.0, 9.0]]), P2, horizon=5000)[0]
    assert abs(a / b - 1) < 0.02


def test_pack_unpack_round_trip():
    for dist, nu in (("normal", INF), ("t", 6.0)):
        p = MSGarchParams(P2.omega, P2.alpha, P2.gamma, P2.beta, P2.P, np.full(2, nu))
        q = _unpack(_pack(p, dist), 2, dist)
        for f in ("omega", "alpha", "gamma", "beta", "P", "nu"):
            assert np.allclose(getattr(p, f), getattr(q, f))


def test_filter_tracks_the_true_regime():
    r, states = simulate_msgarch(P2, 3000, seed=1)
    probs, h_next, ll = msgarch_filter(r, P2)
    assert np.allclose(probs.sum(axis=1), 1.0) and np.isfinite(ll)
    # The regimes' long-run variances (0.5 and 1.8) overlap, so the separation is real but partial.
    assert probs[states == 1, 1].mean() > probs[states == 0, 1].mean() + 0.15
    assert np.allclose(ergodic(P2.P) @ P2.P, ergodic(P2.P))


def test_fit_recovers_the_regimes_from_simulated_returns():
    r, _ = simulate_msgarch(P2, 6000, seed=2)
    p, ll = fit_msgarch(r, 2, "normal")
    assert ll >= msgarch_filter(r, P2, store=False)[2] - 1.0   # at least as good as the truth
    uv_true, uv = P2.unconditional_variance(), p.unconditional_variance()
    assert np.all(np.abs(uv / uv_true - 1) < 0.5)
    assert abs(p.P[0, 0] - 0.98) < 0.03


def test_walk_forward_is_out_of_sample():
    r = pd.Series(simulate_msgarch(P2, 1000, seed=3)[0],
                  index=pd.bdate_range("2001-01-01", periods=1000))
    wf = walk_forward_msgarch(r, 2, "normal", min_train=700, step=150, horizon=5)
    r2 = r.copy()
    r2.iloc[800:] *= 5
    wf2 = walk_forward_msgarch(r2, 2, "normal", min_train=700, step=150, horizon=5)
    assert wf.implied_vol.index[0] == r.index[700] and wf.n_refits == 2
    # Forecasts made up to day 799 used nothing from day 800 on.
    assert np.allclose(wf.implied_vol.iloc[:100], wf2.implied_vol.iloc[:100])
    assert np.allclose(wf.high_vol_prob.iloc[:100], wf2.high_vol_prob.iloc[:100])
    assert not np.allclose(wf.implied_vol.iloc[100:150], wf2.implied_vol.iloc[100:150])


# R MSGARCH 2.51 fits of tests/data/msgarch_sim.csv (examples/msgarch_r_check.R), full precision.
# Order per regime: omega, alpha, gamma, beta; then P[0, 0], P[1, 0]; then nu per regime.
R_FITS = {
    "normal": (-2010.414061, [0.0253117822149, 1.79343043493e-05, 0.0935897184047, 0.890814091928],
               [0.598879439601, 7.19464722108e-06, 0.104950856188, 0.68066248657],
               0.973185054034, 0.064543322712, [INF, INF]),
    "t": (-2000.655626, [0.0310257359024, 2.85079004479e-05, 0.120919299018, 0.869825679033],
          [0.460150305696, 8.75467413209e-05, 0.176069132492, 0.669683681698],
          0.97773789721, 0.0359312253904, [8.16318985034, 10.1522364924]),
}


def _r_params(dist):
    ll, g0, g1, p00, p10, nu = R_FITS[dist]
    g = np.array([g0, g1])
    P = np.array([[p00, 1 - p00], [p10, 1 - p10]])
    return ll, MSGarchParams(g[:, 0], g[:, 1], g[:, 2], g[:, 3], P, np.array(nu))


def _sim_returns():
    from pathlib import Path
    return pd.read_csv(Path(__file__).parent / "data" / "msgarch_sim.csv")["r"].to_numpy()


def test_likelihood_matches_r_msgarch():
    from regimes.msgarch import _filter_kernel
    r = _sim_returns()
    for dist in R_FITS:
        ll_r, p = _r_params(dist)
        # MSGARCH's convention: day 1 only starts the variance recursions.
        h2 = p.omega + (p.alpha + p.gamma * (r[0] < 0)) * r[0] ** 2 + p.beta * p.unconditional_variance()
        ll = _filter_kernel(np.ascontiguousarray(r[1:]), p.omega, p.alpha, p.gamma, p.beta, p.P, p.nu,
                            ergodic(p.P), h2, False)[2]
        assert abs(ll - ll_r) < 1e-4, (dist, ll, ll_r)


def test_fit_is_at_least_as_good_as_r_msgarch():
    r = _sim_returns()
    for dist in R_FITS:
        _, p_r = _r_params(dist)
        _, ll = fit_msgarch(r, 2, dist)
        assert ll >= msgarch_filter(r, p_r, store=False)[2] - 0.05, dist
