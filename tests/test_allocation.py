"""Regime-conditional allocation (P3): the performance primitives and the backtest are causal and
cost-aware, and a regime that flags a crash should avoid it.
"""
import numpy as np
import pytest
import pandas as pd

from regimes.allocation import (
    backtest,
    max_drawdown,
    performance_stats,
    regime_switch_weights,
)


def _idx(n):
    return pd.date_range("2010-01-01", periods=n, freq="B")


def test_max_drawdown_exact():
    r = pd.Series([0.0, -0.5, 1.0], index=_idx(3))
    assert abs(max_drawdown(r) - (-0.5)) < 1e-12


def test_regime_switch_weights():
    prob = pd.Series([0.1, 0.9, 0.4, 0.6], index=_idx(4))
    w = regime_switch_weights(prob, threshold=0.5)
    assert list(w["equity"]) == [1.0, 0.0, 1.0, 0.0]
    assert list(w["cash"]) == [0.0, 1.0, 0.0, 1.0]


def test_backtest_all_equity_reproduces_equity_returns():
    n = 50
    rng = np.random.default_rng(0)
    eq = rng.normal(0.0005, 0.01, n)
    ar = pd.DataFrame({"equity": eq, "cash": np.full(n, 0.0001)}, index=_idx(n))
    w = pd.DataFrame({"equity": 1.0, "cash": 0.0}, index=ar.index)
    net = backtest(ar, w, cost_bps=0.0)
    # position for day t is set at t-1, so net starts one day in and equals the equity return.
    assert np.allclose(net.to_numpy(), eq[1:], atol=1e-12)


def test_backtest_charges_turnover_cost():
    idx = _idx(5)
    ar = pd.DataFrame({"equity": [0.0] * 5, "cash": [0.0] * 5}, index=idx)
    # Switch equity->cash after day 1: turnover of 2 (|1-0| + |0-1|) on the day the position changes.
    w = pd.DataFrame({"equity": [1, 1, 0, 0, 0], "cash": [0, 0, 1, 1, 1]}, index=idx, dtype=float)
    net = backtest(ar, w, cost_bps=10.0)
    # All asset returns are zero, so any negative return is pure cost. 10 bps * turnover(2) = 20 bps.
    assert abs(net.min() - (-20e-4)) < 1e-9
    assert (net.drop(net.idxmin()) == 0).all()


def test_regime_strategy_avoids_a_flagged_crash():
    n = 500
    eq = np.full(n, 0.0004)
    eq[300:340] = -0.03            # a crash
    cash = np.full(n, 0.00005)
    prob = np.zeros(n)
    prob[298:345] = 1.0            # regime flags the crash (from just before)
    idx = _idx(n)
    ar = pd.DataFrame({"equity": eq, "cash": cash}, index=idx)

    strat = backtest(ar, regime_switch_weights(pd.Series(prob, index=idx)), cost_bps=1.0)
    static_eq = backtest(ar, pd.DataFrame({"equity": 1.0, "cash": 0.0}, index=idx))

    # The regime strategy sidesteps the crash, so its drawdown is far shallower.
    assert max_drawdown(strat) > max_drawdown(static_eq) + 0.3
    assert performance_stats(strat).ann_return > performance_stats(static_eq).ann_return


def test_block_bootstrap_sharpe_is_paired_and_centred():
    from regimes.allocation import block_bootstrap_sharpe

    n = 2520
    rng = np.random.default_rng(1)
    a = rng.normal(0.0004, 0.01, n)
    ex = pd.DataFrame({"a": a, "a_copy": a, "b": rng.normal(0.0, 0.01, n)}, index=_idx(n))
    draws = block_bootstrap_sharpe(ex, block=63, n_boot=300, seed=0)
    assert draws.shape == (300, 3)
    # identical columns get identical draws: the resample is shared, so differences are paired.
    assert np.allclose(draws["a"], draws["a_copy"])
    full = ex["a"].mean() / ex["a"].std() * np.sqrt(252)
    assert abs(draws["a"].median() - full) < 0.25


def test_execution_lag_default_is_shift_one_and_lag_two_is_shift_two():
    from regimes.allocation import turnover

    n = 60
    rng = np.random.default_rng(3)
    ar = pd.DataFrame({"equity": rng.normal(0, 0.01, n), "cash": np.full(n, 0.0001)}, index=_idx(n))
    sig = pd.Series(rng.uniform(0, 1, n), index=ar.index)
    w = regime_switch_weights(sig)
    net1 = backtest(ar, w, cost_bps=5.0)
    net1_explicit = backtest(ar, w, cost_bps=5.0, execution_lag=1)
    net2 = backtest(ar, w, cost_bps=5.0, execution_lag=2)
    assert net1.equals(net1_explicit)
    # Lag 2 on the schedule equals lag 1 on the schedule shifted by one day.
    net2_by_shift = backtest(ar, w.shift(1).dropna(), cost_bps=5.0, execution_lag=1)
    assert np.allclose(net2.to_numpy(), net2_by_shift.to_numpy(), atol=1e-15)
    assert len(net2) == len(net1) - 1
    # The cost charged is exactly cost_bps times the turnover helper on the same days.
    gross2 = backtest(ar, w, cost_bps=0.0, execution_lag=2)
    tv = turnover(w, execution_lag=2)
    assert tv.index.equals(net2.index)
    assert np.allclose((gross2 - net2).to_numpy(), 5e-4 * tv.to_numpy(), atol=1e-15)
    with pytest.raises(ValueError):
        backtest(ar, w, execution_lag=0)


def test_rebalanced_backtest_drifts_then_resets_at_month_end():
    from regimes.allocation import rebalanced_backtest, static_weights

    idx = pd.date_range("2010-01-25", periods=8, freq="B")  # crosses the Jan/Feb month end (01-29 is a Friday)
    ar = pd.DataFrame({"equity": [0.0, 0.10, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                       "bonds": [0.0] * 8}, index=idx)
    res = rebalanced_backtest(ar, {"equity": 0.6, "bonds": 0.4}, cost_bps=10.0)
    # Established at the close of day 0, so the first return is day 1: equity +10%, portfolio +6%;
    # the weights then drift to 0.66 / 0.34 and stay there until the reset.
    assert res.net.index[0] == idx[1]
    assert abs(res.net.iloc[0] - 0.06) < 1e-12
    assert np.allclose(res.weights.loc[idx[2]].to_numpy(), [0.66 / 1.06, 0.4 / 1.06])
    # The reset decided at the last January close (01-29) is held from 02-01: turnover 2 * (0.66/1.06 - 0.6)
    # charged that day, weights back to 60/40.
    expected_turnover = 2 * (0.66 / 1.06 - 0.6)
    feb1 = pd.Timestamp("2010-02-01")
    assert abs(res.turnover.loc[feb1] - expected_turnover) < 1e-12
    assert abs(res.net.loc[feb1] - (0.0 - 10e-4 * expected_turnover)) < 1e-12
    assert (res.turnover.drop(feb1) == 0).all()
    assert np.allclose(res.weights.loc[feb1].to_numpy(), [0.6, 0.4])
    # With no drift (every asset returns the same), the result equals the daily-rebalanced static
    # portfolio and nothing is traded.
    flat = pd.DataFrame({"equity": np.full(8, 0.01), "bonds": np.full(8, 0.01)}, index=idx)
    res_flat = rebalanced_backtest(flat, {"equity": 0.6, "bonds": 0.4}, cost_bps=10.0)
    assert (res_flat.turnover == 0).all()
    static = backtest(flat, static_weights(idx, {"equity": 0.6, "bonds": 0.4}))
    assert res_flat.net.index.equals(static.index)
    assert np.allclose(res_flat.net.to_numpy(), static.to_numpy())
    with pytest.raises(ValueError):
        rebalanced_backtest(flat, {"equity": 0.6, "bonds": 0.3})


def test_drift_backtest_lag_and_decision_rows():
    from regimes.allocation import drift_backtest, period_end_decisions

    idx = _idx(6)
    ar = pd.DataFrame({"a": [0.01, 0.02, -0.01, 0.03, 0.0, 0.01], "b": [0.0] * 6}, index=idx)
    dec = pd.DataFrame(np.nan, index=idx, columns=["a", "b"])
    dec.iloc[0] = [1.0, 0.0]
    dec.iloc[2] = [0.0, 1.0]   # decided at the close of day 2
    lag1 = drift_backtest(ar, dec, cost_bps=100.0, execution_lag=1)
    lag2 = drift_backtest(ar, dec, cost_bps=100.0, execution_lag=2)
    # Lag 1: all in 'a' on days 1-2, switched to 'b' from day 3 (cost 1% * turnover 2 on day 3).
    assert np.allclose(lag1.net.to_numpy(), [0.02, -0.01, 0.0 - 0.02, 0.0, 0.0])
    # Lag 2: established one day later (first return day 2) and the switch earns from day 4, where
    # its cost is charged.
    assert lag2.net.index[0] == idx[2]
    assert np.allclose(lag2.net.to_numpy(), [-0.01, 0.03, 0.0 - 0.02, 0.0])
    assert abs(lag1.turnover.sum() - 2.0) < 1e-12 and abs(lag2.turnover.sum() - 2.0) < 1e-12
    # A partial decision row or weights not summing to one are refused.
    bad = dec.copy()
    bad.iloc[4] = [0.5, np.nan]
    with pytest.raises(ValueError):
        drift_backtest(ar, bad)
    bad = dec.copy()
    bad.iloc[4] = [0.5, 0.6]
    with pytest.raises(ValueError):
        drift_backtest(ar, bad)
    # period_end_decisions: first day and the last day of each month, NaN elsewhere.
    long = pd.date_range("2010-01-20", periods=20, freq="B")
    sched = period_end_decisions(long, {"a": 0.5, "b": 0.5})
    days = sched.dropna().index
    assert days[0] == long[0] and pd.Timestamp("2010-01-29") in days
    # The sample's last day counts as a period end (a decision there never becomes effective).
    assert list(days) == [long[0], pd.Timestamp("2010-01-29"), long[-1]]


def test_block_bootstrap_drawdown_is_paired_and_deterministic():
    from regimes.allocation import block_bootstrap_drawdown

    n = 1000
    rng = np.random.default_rng(2)
    a = rng.normal(0.0003, 0.01, n)
    df = pd.DataFrame({"a": a, "a_copy": a, "b": rng.normal(0.0003, 0.02, n)}, index=_idx(n))
    d1 = block_bootstrap_drawdown(df, block=63, n_boot=100, seed=0)
    d2 = block_bootstrap_drawdown(df, block=63, n_boot=100, seed=0)
    assert d1.shape == (100, 3) and np.allclose(d1, d2)
    assert np.allclose(d1["a"], d1["a_copy"])
    assert (d1 <= 0).all().all() and d1["b"].median() < d1["a"].median()
