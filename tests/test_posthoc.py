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
