"""Regime-conditional allocation (P3): the performance primitives and the backtest are causal and
cost-aware, and a regime that flags a crash should avoid it.
"""
import numpy as np
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
