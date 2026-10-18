"""Post-hoc statistics: HAC Diebold-Mariano, bootstrap intervals, equivalence reading."""
from __future__ import annotations

import math

import numpy as np
import pytest

from regimes.forecast import paired_mean_diff_interval, paired_rmse_diff_interval
from regimes.posthoc import excluded_change_pct, hac_dm, paired_interval, stationary_indices


def test_hac_dm_matches_hand_computation():
    a = np.array([1.0, 2.0, 0.5, 3.0, 1.5, 2.5])
    b = np.zeros(6)
    d = a - a.mean()
    n, lag = 6, 2
    lrv = d @ d / n + 2 * (2 / 3) * (d[1:] @ d[:-1]) / n + 2 * (1 / 3) * (d[2:] @ d[:-2]) / n
    se = math.sqrt(lrv / n)
    res = hac_dm(a, b, lag=lag)
    assert res["se"] == pytest.approx(se)
    assert res["stat"] == pytest.approx(a.mean() / se)
    assert res["p"] == pytest.approx(math.erfc(abs(a.mean() / se) / math.sqrt(2)))


def test_hac_dm_lag0_is_iid_standard_error_and_antisymmetric():
    rng = np.random.default_rng(1)
    a, b = rng.standard_normal(500), rng.standard_normal(500)
    res = hac_dm(a, b, lag=0)
    d = a - b
    assert res["se"] == pytest.approx(d.std() / math.sqrt(500))
    flipped = hac_dm(b, a, lag=20)
    assert flipped["stat"] == pytest.approx(-hac_dm(a, b, lag=20)["stat"])
    assert flipped["p"] == pytest.approx(hac_dm(a, b, lag=20)["p"])


def test_circular_scheme_reproduces_the_holdout_intervals_exactly():
    rng = np.random.default_rng(2)
    e, e0 = rng.standard_normal(700), rng.standard_normal(700) * 1.1
    assert paired_interval(e, e0, statistic="rmse", block=63, n_boot=300) == \
        paired_rmse_diff_interval(e, e0, block=63, n_boot=300)
    q, q0 = e ** 2, e0 ** 2
    assert paired_interval(q, q0, statistic="mean", block=63, n_boot=300) == \
        paired_mean_diff_interval(q, q0, block=63, n_boot=300)


def test_stationary_indices_shape_and_mean_block():
    rng = np.random.default_rng(3)
    idx = stationary_indices(rng, 20000, 42)
    assert idx.shape == (20000,) and idx.min() >= 0 and idx.max() < 20000
    breaks = np.sum(np.diff(idx) != 1) - np.sum(np.diff(idx) == -(20000 - 1))
    assert 20000 / (breaks + 1) == pytest.approx(42, rel=0.15)


def test_bootstrap_deterministic_by_seed():
    rng = np.random.default_rng(4)
    a, b = rng.standard_normal(300), rng.standard_normal(300)
    for scheme in ("circular", "stationary"):
        first = paired_interval(a, b, scheme=scheme, block=21, n_boot=100, seed=7)
        assert first == paired_interval(a, b, scheme=scheme, block=21, n_boot=100, seed=7)
        assert first != paired_interval(a, b, scheme=scheme, block=21, n_boot=100, seed=8)


def test_stationary_interval_coverage_on_ar1_mean():
    """95% intervals for a mean difference of zero cover it in most of 80 AR(1) samples."""
    rng = np.random.default_rng(5)
    hits = 0
    for rep in range(80):
        e = np.empty(400)
        e[0] = rng.standard_normal()
        for t in range(1, 400):
            e[t] = 0.5 * e[t - 1] + rng.standard_normal()
        lo, hi = paired_interval(e, np.zeros(400), statistic="mean", scheme="stationary", block=20,
                                 n_boot=200, seed=rep)
        hits += lo <= 0.0 <= hi
    assert hits >= 68  # 85%: bootstrap intervals under-cover a little at n = 400


def test_excluded_change_pct():
    assert excluded_change_pct(-0.003, 0.006, 0.3) == pytest.approx(
        {"largest_gain_allowed": 1.0, "largest_loss_allowed": 2.0})
    assert excluded_change_pct(0.01, 0.02, 0.5)["largest_gain_allowed"] == 0.0
    with pytest.raises(ValueError):
        paired_interval(np.zeros(5), np.zeros(5), scheme="moving")


def test_mcs_removes_the_dominated_model_and_keeps_equals():
    """A model worse by half a unit every day is always out; two models of equal expected loss are
    both kept in at least 85% of 20 samples (the 10% set drops a true equal about one time in ten)."""
    from regimes.posthoc import mcs
    both_kept = 0
    for rep in range(20):
        rng = np.random.default_rng(rep)
        base = rng.standard_normal(600) ** 2
        losses = np.column_stack([base + 0.02 * rng.standard_normal(600),
                                  base + 0.02 * rng.standard_normal(600),
                                  base + 0.5])
        res = mcs(losses, alpha=0.10, block=21, n_boot=200, seed=0)
        assert res["elimination_rank"][2] == 1 and res["p_value"][2] < 0.05 and not res["in_set"][2]
        assert res["p_value"][res["elimination_rank"].argmax()] == 1.0
        ranked = res["p_value"][np.argsort(res["elimination_rank"])]
        assert np.all(np.diff(ranked) >= 0)  # p-values are non-decreasing in elimination order
        both_kept += bool(res["in_set"][0] and res["in_set"][1])
    assert both_kept >= 17


def test_mcs_deterministic_and_shape():
    from regimes.posthoc import mcs
    rng = np.random.default_rng(7)
    losses = rng.standard_normal((200, 4)) ** 2
    a = mcs(losses, block=21, n_boot=100, seed=3)
    b = mcs(losses, block=21, n_boot=100, seed=3)
    assert np.array_equal(a["p_value"], b["p_value"]) and a["p_value"].shape == (4,)
    assert sorted(a["elimination_rank"]) == [1, 2, 3, 4]


def test_mincer_zarnowitz_recovers_a_known_line_and_hac_se():
    from regimes.posthoc import mincer_zarnowitz

    rng = np.random.default_rng(5)
    f = rng.uniform(0.5, 2.0, 400)
    y = 0.3 + 0.8 * f  # exact line: slope and intercept recovered, R2 = 1, Wald rejects (0, 1)
    mz = mincer_zarnowitz(f, y, lag=20)
    assert abs(mz["slope"] - 0.8) < 1e-10 and abs(mz["intercept"] - 0.3) < 1e-10
    assert abs(mz["r2"] - 1.0) < 1e-10 and mz["n"] == 400
    # With noise the lag-0 HAC standard error is the classical White standard error.
    y2 = y + rng.normal(0, 0.1, 400)
    mz0 = mincer_zarnowitz(f, y2, lag=0)
    x = np.column_stack([np.ones(400), f])
    beta = np.linalg.lstsq(x, y2, rcond=None)[0]
    u = y2 - x @ beta
    xtx_inv = np.linalg.inv(x.T @ x)
    white = xtx_inv @ (x * u[:, None]).T @ (x * u[:, None]) @ xtx_inv
    assert abs(mz0["se_slope"] - math.sqrt(white[1, 1])) < 1e-12
    assert abs(mz0["slope"] - beta[1]) < 1e-12
    # An unbiased forecast (y = f + noise) does not reject a = 0, b = 1.
    y3 = f + rng.normal(0, 0.05, 400)
    assert mincer_zarnowitz(f, y3, lag=20)["p_a0_b1"] > 0.01


def test_variance_swap_sign_test_hand_built():
    from regimes.posthoc import variance_swap_sign_test

    strike = np.array([1.0, 1.0, 1.0, 1.0])          # strike variance 1
    realised = np.array([2.0, 0.5, 1.5, 0.5])        # payoff to long: 3, -0.75, 1.25, -0.75
    forecast = np.array([1.5, 1.5, 0.5, 0.5])        # long, long, short, short
    r = variance_swap_sign_test(forecast, realised, strike)
    assert r["n"] == 4 and abs(r["share_long"] - 0.5) < 1e-12
    # pnl = [3, -0.75, -1.25, 0.75]: mean 0.4375, two of four positive
    assert abs(r["mean_pnl"] - 0.4375) < 1e-12 and abs(r["hit_rate"] - 0.5) < 1e-12
    # always short: pnl = [-3, 0.75, -1.25, 0.75]: mean -0.6875, hit 0.5
    assert abs(r["short_mean_pnl"] + 0.6875) < 1e-12 and abs(r["short_hit_rate"] - 0.5) < 1e-12
    assert abs(r["long_days_mean_payoff"] - 1.125) < 1e-12 and abs(r["long_days_hit_rate"] - 0.5) < 1e-12
    # A forecast that is never long has the always-short P&L exactly and no p-value.
    never = variance_swap_sign_test(np.full(4, 0.5), realised, strike)
    assert never["share_long"] == 0.0 and never["mean_pnl"] == never["short_mean_pnl"]
    assert math.isnan(never["p_vs_short"]) and math.isnan(never["long_days_mean_payoff"])


def test_paired_draws_are_the_draws_behind_paired_interval():
    from regimes.posthoc import paired_draws, paired_interval
    rng = np.random.default_rng(3)
    a, b = rng.normal(size=400), rng.normal(size=400) * 1.1
    for stat, scheme in (("rmse", "circular"), ("mean", "circular"), ("mean", "stationary")):
        draws = paired_draws(a, b, statistic=stat, scheme=scheme, block=21, n_boot=300, seed=5)
        lo, hi = paired_interval(a, b, statistic=stat, scheme=scheme, block=21, n_boot=300, seed=5)
        assert np.allclose(np.percentile(draws, [2.5, 97.5]), [lo, hi], rtol=0, atol=0)


def test_bootstrap_p_value_hand_built_and_consistent_with_the_interval():
    from regimes.posthoc import bootstrap_p_value, paired_draws, paired_interval
    # hand-built draws: 3 of 9 at or below zero -> 2 * (3 + 1) / 10 = 0.8
    assert bootstrap_p_value(np.array([-2, -1, 0, 1, 2, 3, 4, 5, 6.0])) == pytest.approx(0.8)
    assert bootstrap_p_value(np.ones(99)) == pytest.approx(2 / 100)
    # an interval that excludes zero has p at or below about 0.05, one that spans zero above it
    rng = np.random.default_rng(0)
    seen = set()
    for shift in (0.0, 0.05, 0.1, 0.2, 0.4, 0.0, 0.1):
        y = rng.normal(size=600)
        a = y + rng.normal(scale=0.5, size=600) + shift
        b = y + rng.normal(scale=0.5, size=600)
        lo, hi = paired_interval(a - y, b - y, statistic="rmse", block=21, n_boot=1000)
        p = bootstrap_p_value(paired_draws(a - y, b - y, statistic="rmse", block=21, n_boot=1000))
        excl = lo > 0 or hi < 0
        seen.add(excl)
        assert p <= 0.052 if excl else p >= 0.048
    assert seen == {True, False}


def test_holm_matches_the_textbook_example_and_handles_nan():
    from regimes.posthoc import holm
    p = [0.01, 0.04, 0.03, 0.005, np.nan]
    out = holm(p, alpha=0.05)
    # sorted 0.005, 0.01, 0.03, 0.04 times 4, 3, 2, 1 -> 0.02, 0.03, 0.06, 0.04 -> monotone 0.02, 0.03, 0.06, 0.06
    assert np.allclose(out["adjusted"][:4], [0.03, 0.06, 0.06, 0.02])
    assert np.isnan(out["adjusted"][4])
    assert out["reject"].tolist() == [True, False, False, True, False]
    assert holm([0.9, 0.8])["adjusted"].tolist() == [1.0, 1.0]
