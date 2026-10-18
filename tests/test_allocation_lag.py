"""Stage S5 scripts: the allocation-lag schedules are the ones of examples/regime_allocation.py and
lag 1 is the published backtest; the desk tables on development forecasts behave on a hand-built
scored folder.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from regimes.allocation import backtest  # noqa: E402


def _idx(n):
    return pd.date_range("2010-01-01", periods=n, freq="B")


def test_schedules_are_the_published_seven_and_lag_one_is_the_default_backtest():
    import allocation_lag as al

    n = 600
    rng = np.random.default_rng(0)
    idx = _idx(n)
    assets = pd.DataFrame({"equity": rng.normal(0.0004, 0.012, n), "bonds": rng.normal(0.0002, 0.004, n),
                           "cash": np.full(n, 0.00005)}, index=idx)
    spy = pd.Series(100 * np.log1p(assets["equity"]), index=idx)  # log returns in percent
    prob = pd.Series(rng.uniform(0, 1, 200), index=idx[400:])
    weights, rv21, ewma = al.schedules(prob, spy, assets)
    assert set(weights) == {al.BASE, "Regime switch equity/bonds", "21d vol > 20% equity/cash",
                            "EWMA vol > 20% equity/cash", "EWMA vol target 10%", "Static 100% equity",
                            "Static 60/40 equity/bonds"}
    assert set(weights) == set(al.RULES) | set(al.STATICS)
    lag1 = al.run_all(assets, weights, lag=1, cost_bps=5.0)
    for k, w in weights.items():
        assert lag1[k].equals(backtest(assets, w, cost_bps=5.0))
    common = al.common_index(lag1)
    assert common.min() > prob.index.min() and common.max() == idx[-1]
    lag2 = al.run_all(assets, weights, lag=2, cost_bps=5.0)
    assert len(al.common_index(lag2)) == len(common) - 1


def test_desk_tables_on_a_hand_built_scored_folder(tmp_path):
    import dev_forecast_desk as dd

    n = 300
    rng = np.random.default_rng(1)
    idx = _idx(n)
    y = rng.uniform(0.5, 2.0, n)
    vix = np.full(n, 5.0)  # strike far above every forecast: HAR + VIX is never long
    har = y + 10.0         # always long, and above the strike
    har_vix = y + rng.normal(0, 0.01, n)   # an almost perfect forecast: slope 1, intercept 0
    raw = pd.DataFrame({"target": y, "HMM implied vol": y * 0.5, "VIX": vix}, index=idx)
    cal = pd.DataFrame({"target": y, "HAR": har, "HAR + VIX": har_vix}, index=idx)
    (tmp_path / "scored").mkdir()
    raw.to_csv(tmp_path / "scored" / "scored_01.csv")
    cal.to_csv(tmp_path / "scored" / "scored_02.csv")
    (tmp_path / "scored" / "index.json").write_text(json.dumps(
        [{"file": "scored_01.csv", "columns": list(raw.columns[1:])},
         {"file": "scored_02.csv", "columns": list(cal.columns[1:])}]))

    r, c = dd.load_scored(tmp_path)
    assert r.index.equals(c.index) and "HAR + VIX" in c.columns and "VIX" in r.columns
    mz = dd.mz_table(r, c).set_index("forecast")
    assert abs(mz.loc["HAR + VIX (calibrated)", "slope"] - 1.0) < 0.05
    assert abs(mz.loc["HAR + VIX (calibrated)", "intercept"]) < 0.05
    assert mz.loc["HAR + VIX (calibrated)", "n"] == n
    assert "VIX (raw)" in mz.index and "HMM implied vol (raw)" in mz.index
    vs = dd.varswap_table(r, c).set_index("forecast")
    assert vs.loc["HAR + VIX (calibrated)", "share_long"] == 0.0
    assert vs.loc["HAR + VIX (calibrated)", "mean_pnl"] == vs.loc["always short", "mean_pnl"]
    assert vs.loc["HAR (calibrated)", "share_long"] == 1.0
    assert abs(vs.loc["HAR (calibrated)", "mean_pnl"] + vs.loc["always short", "mean_pnl"]) < 1e-12
    monthly = dd.varswap_table(r, c, every=21)
    assert monthly["n"].iloc[0] == len(range(0, n, 21))


def test_v2_overlay_moves_sleeves_and_decisions_fire_on_state_changes():
    import allocation_v2_dev as v2

    n = 70
    idx = _idx(n)
    target = pd.DataFrame(0.0, index=idx, columns=v2.TICKERS)
    target["SPY"], target["EFA"], target["IEF"], target["TLT"], target["GLD"] = 0.3, 0.2, 0.2, 0.2, 0.1
    state = pd.Series(0.0, index=idx)
    state.iloc[20:30] = 1.0
    eq = v2.apply_overlay(target, state, "equity")
    assert np.allclose(eq.sum(axis=1), 1.0)
    assert eq["SPY"].iloc[25] == 0.0 and eq["EFA"].iloc[25] == 0.0 and abs(eq["BIL"].iloc[25] - 0.5) < 1e-12
    assert eq.iloc[10].equals(target.iloc[10])
    bd = v2.apply_overlay(target, state, "bonds")
    assert np.allclose(bd.sum(axis=1), 1.0)
    assert bd["IEF"].iloc[25] == 0.0 and abs(bd["GLD"].iloc[25] - 0.3) < 1e-12 and abs(bd["BIL"].iloc[25] - 0.2) < 1e-12
    # Decision rows: first day, month ends, and the two days the state changes; NaN elsewhere.
    dec = v2.decisions(target, state, "equity", idx[0])
    days = dec.dropna().index
    assert idx[0] in days and idx[20] in days and idx[30] in days
    month_ends = v2.period_end_decisions(idx, {"SPY": 1.0}).dropna().index
    assert set(days) == set(month_ends) | {idx[20], idx[30]}
    assert dec.loc[idx[20], "BIL"] == 0.5 and dec.loc[idx[30], "BIL"] == 0.0
    plain = v2.decisions(target, None, None, idx[0])
    assert set(plain.dropna().index) == set(month_ends)
