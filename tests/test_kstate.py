"""Tests for regimes.kstate: K-state Student-t HMM with restarts and its causal walk-forward."""
import numpy as np
import pandas as pd
import pytest

from regimes.kstate import (StudentTParams, deterministic_init, em_student_t, filter_student_t,
                            fit_student_t_restarts, implied_vol, random_init, walk_forward_student_t)
from regimes.student_t import fit_regimes_student_t


def simulate_three_state(n: int = 3000, seed: int = 1) -> np.ndarray:
    rng = np.random.default_rng(seed)
    sig = np.array([0.4, 1.0, 3.0])
    A = np.array([[0.98, 0.015, 0.005], [0.02, 0.96, 0.02], [0.01, 0.04, 0.95]])
    s = 0
    x = np.empty(n)
    for t in range(n):
        s = rng.choice(3, p=A[s])
        x[t] = sig[s] * rng.standard_t(6)
    return x


def test_deterministic_start_matches_student_t_fitter():
    """From the same start and with the same updates, em_student_t equals fit_regimes_student_t."""
    x = simulate_three_state(800)
    ref = fit_regimes_student_t(pd.Series(x), n_regimes=2, nu=8.0, estimate_nu=True)
    mine = em_student_t(x, 2, deterministic_init(x, 2), nu0=8.0, estimate_nu=True)
    # fit_regimes_student_t returns the log-likelihood of the iteration before the stopping one;
    # em_student_t returns the stopping iteration's, so they differ by less than tol.
    assert mine.loglik == pytest.approx(ref.result["loglik"], abs=1e-5)
    assert np.allclose(mine.sigma, ref.result["sigma"])
    assert mine.nu == pytest.approx(ref.result["nu"])


def test_restarts_recover_three_scales_and_report_convergence():
    x = simulate_three_state()
    summ = fit_student_t_restarts(x, 3, n_starts=6, seed=0, max_iter=300)
    assert len(summ.logliks) == 6 and len(summ.converged) == 6
    assert summ.best.loglik == max(ll for ll, c in zip(summ.logliks, summ.converged) if c)
    assert 1 <= summ.n_at_best <= 6
    assert np.all(np.diff(summ.best.sigma) > 0)                       # ordered by scale
    assert np.allclose(summ.best.sigma, [0.4, 1.0, 3.0], rtol=0.35)   # scales recovered, loosely
    assert summ.best.n_params == 2 * 3 + 6 + 2 + 1


def test_random_init_is_a_valid_start():
    rng = np.random.default_rng(3)
    x = simulate_three_state(500)
    mu, sigma, A, pi = random_init(x, 4, rng)
    assert A.shape == (4, 4) and np.allclose(A.sum(axis=1), 1.0) and (A >= 0).all()
    assert np.all(np.diff(sigma) >= 0) and pi.sum() == pytest.approx(1.0)
    assert mu.shape == (4,)


def test_not_converged_when_max_iter_hit():
    x = simulate_three_state(600)
    p = em_student_t(x, 3, deterministic_init(x, 3), max_iter=2)
    assert p.converged is False and p.n_iter == 2


def test_filter_is_causal_prefix_identity():
    """Filtered probabilities for the first t days do not change when later data is appended."""
    x = simulate_three_state(900)
    p = fit_student_t_restarts(x[:600], 3, n_starts=2, seed=0).best
    short = filter_student_t(x[:700], p)
    long = filter_student_t(x[:900], p)
    assert np.allclose(short, long[:700], atol=1e-12)
    assert np.allclose(short.sum(axis=1), 1.0)


def test_implied_vol_hand_computation():
    A = np.array([[0.9, 0.1], [0.2, 0.8]])
    p = StudentTParams(mu=np.zeros(2), sigma=np.array([1.0, 2.0]), nu=6.0, A=A, pi=np.array([0.5, 0.5]),
                       loglik=0.0, converged=True, n_iter=1)
    var = np.array([1.0, 4.0]) * 6.0 / 4.0
    assert np.allclose(p.state_variances, var)
    filt = np.array([[1.0, 0.0]])
    # horizon 1: next-day state distribution is A[0]
    assert implied_vol(filt, p, 1)[0] == pytest.approx(np.sqrt(A[0] @ var))
    # horizon 2: average of A and A^2 from state 0
    w = (A[0] + (A @ A)[0]) / 2
    assert implied_vol(filt, p, 2)[0] == pytest.approx(np.sqrt(w @ var))


def test_walk_forward_blocks_cover_oos_span_and_are_deterministic():
    x = simulate_three_state(1300, seed=5)
    r = pd.Series(x, index=pd.bdate_range("2000-01-03", periods=len(x)))
    wf1 = walk_forward_student_t(r, 3, min_train=800, step=200, horizon=5, n_starts=2, seed=0)
    wf2 = walk_forward_student_t(r, 3, min_train=800, step=200, horizon=5, n_starts=2, seed=0, n_jobs=2)
    assert wf1.n_refits == 3 and len(wf1.convergence) == 3
    assert wf1.high_vol_prob.index.equals(r.index[800:])
    assert wf1.implied_vol.index.equals(r.index[800:]) and (wf1.implied_vol > 0).all()
    assert ((wf1.high_vol_prob >= 0) & (wf1.high_vol_prob <= 1)).all()
    pd.testing.assert_series_equal(wf1.implied_vol, wf2.implied_vol)   # n_jobs does not change results
    assert set(wf1.convergence.columns) >= {"n_starts", "n_converged", "best_converged", "n_at_best", "loglik", "nu"}


def test_walk_forward_block_uses_only_past_parameters():
    """Changing data after refit edge i leaves block i's forecast unchanged (parameters are frozen
    on x[:i] and the filter is causal), while block i+1 changes."""
    x = simulate_three_state(1100, seed=7)
    idx = pd.bdate_range("2000-01-03", periods=len(x))
    r = pd.Series(x, index=idx)
    r2 = r.copy()
    r2.iloc[1000:] = r2.iloc[1000:] * 3.0
    a = walk_forward_student_t(r, 2, min_train=800, step=200, horizon=5, n_starts=2, seed=0)
    b = walk_forward_student_t(r2, 2, min_train=800, step=200, horizon=5, n_starts=2, seed=0)
    pd.testing.assert_series_equal(a.implied_vol.iloc[:200], b.implied_vol.iloc[:200])
    assert not np.allclose(a.implied_vol.iloc[200:].to_numpy(), b.implied_vol.iloc[200:].to_numpy())
