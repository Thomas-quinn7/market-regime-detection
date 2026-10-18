"""Development data only, no holdout: execution lag, cost drag and a rebalanced 60/40 for the
regime-conditional allocation table.

Re-runs the allocation of ``examples/regime_allocation.py`` (WRITEUP section "Regime-conditional
allocation", development data: SPY, IEF, BIL 2005-2023, walk-forward HMM signal on the S&P 500)
and adds what the desk asked for (desk, trader section 4; desk synthesis finding 4):

1. the published execution rule reproduced (lag 1: the position earning day t is set from the close
   of t-1, i.e. filled at the close that produced the signal);
2. one more day of execution lag for every rule (lag 2: signal at the close of t-2, filled at the
   close of t-1, earning close(t-1) to close(t)), with a paired block-bootstrap interval for the
   Sharpe change the lag causes;
3. the cost drag of every rule from its realised turnover at 5 and 10 basis points per leg, and the
   split of the return given up against 100 percent equity into gross and brokerage;
4. a 60/40 benchmark that drifts and is rebalanced at each month end, paying costs, beside the
   published daily zero-cost one;
5. the trailing-vol threshold grid at both lags.

It then appends the two desk tables on the development forecasts from
``examples/dev_forecast_desk.py`` (Mincer-Zarnowitz, variance-swap sign test) if that script has
been run. Nothing here is a claim; the published table is development data and so is this.

    python examples/allocation_lag.py               # recomputes the walk-forward signal (about a minute)
    python examples/allocation_lag.py --from-cache  # reuse docs/results/allocation_lag/hmm_prob_spy.csv

Writes docs/ALLOCATION_LAG_2026-10.md and the CSV tables under docs/results/allocation_lag/.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from regimes.allocation import (
    backtest,
    block_bootstrap_sharpe,
    performance_stats,
    rebalanced_backtest,
    regime_switch_weights,
    static_weights,
    turnover,
    vol_threshold_signal,
)
from regimes.data import load_index_prices, load_index_returns
from regimes.evaluate import ewma_vol, realised_vol, walk_forward_oos

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "examples"))
OUT = REPO / "docs" / "results" / "allocation_lag"
DOC = REPO / "docs" / "ALLOCATION_LAG_2026-10.md"
START, END = "2005-01-01", "2023-12-31"
CLASS = "development data only (SPY, IEF, BIL 2005-2023; walk-forward HMM signal on the S&P 500), no holdout"
BASE = "Regime switch equity/cash"
RULES = [BASE, "Regime switch equity/bonds", "21d vol > 20% equity/cash", "EWMA vol > 20% equity/cash",
         "EWMA vol target 10%"]
STATICS = ["Static 100% equity", "Static 60/40 equity/bonds"]


def git_head() -> str:
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True,
                              text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True,
                               text=True, check=True).stdout.strip()
        return head + (" plus uncommitted files" if dirty else "")
    except Exception:  # noqa: BLE001
        return "unknown"


def load_assets() -> tuple[pd.DataFrame, pd.Series]:
    eq = load_index_prices("SPY", START, END).pct_change()
    bond = load_index_prices("IEF", START, END).pct_change()
    cash = load_index_prices("BIL", START, END).pct_change()
    assets = pd.DataFrame({"equity": eq, "bonds": bond, "cash": cash}).dropna()
    spy = load_index_returns("SPY", START, END)  # log returns in percent
    return assets, spy


def hmm_signal(spy: pd.Series, *, from_cache: bool) -> tuple[pd.Series, dict]:
    path = OUT / "hmm_prob_spy.csv"
    if from_cache and path.exists():
        prob = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        info = json.loads((OUT / "hmm_signal.json").read_text())
        return prob, info
    t0 = time.perf_counter()
    wf = walk_forward_oos(spy, min_train=756, step=63)
    info = {"n_refits": int(wf.n_refits), "n_skipped": int(wf.n_skipped),
            "seconds": round(time.perf_counter() - t0, 1)}
    conv = getattr(wf, "convergence", None)
    if conv is not None and len(conv):
        info["refits_converged"] = int(pd.DataFrame(conv)["best_converged"].fillna(False).sum())
    prob = wf.high_vol_prob.rename("hmm_high_vol_prob")
    prob.to_csv(path, float_format="%.17g")
    (OUT / "hmm_signal.json").write_text(json.dumps(info, indent=1))
    return prob, info


def schedules(prob: pd.Series, spy: pd.Series, assets: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """The seven weight schedules of examples/regime_allocation.py, by the same names."""
    rv21 = realised_vol(spy, 21) * np.sqrt(252)
    ewma = ewma_vol(spy) * np.sqrt(252)
    eq_w = (10.0 / ewma).clip(upper=1.0).dropna()
    return {
        BASE: regime_switch_weights(prob, risk_on="equity", risk_off="cash"),
        "Regime switch equity/bonds": regime_switch_weights(prob, risk_on="equity", risk_off="bonds"),
        "21d vol > 20% equity/cash": regime_switch_weights(vol_threshold_signal(rv21, 20.0)),
        "EWMA vol > 20% equity/cash": regime_switch_weights(vol_threshold_signal(ewma, 20.0)),
        "EWMA vol target 10%": pd.DataFrame({"equity": eq_w, "cash": 1.0 - eq_w}),
        "Static 100% equity": static_weights(assets.index, {"equity": 1.0}),
        "Static 60/40 equity/bonds": static_weights(assets.index, {"equity": 0.6, "bonds": 0.4}),
    }, rv21, ewma


def run_all(assets, weights, *, lag: int, cost_bps: float) -> dict[str, pd.Series]:
    return {k: backtest(assets, w, cost_bps=cost_bps, execution_lag=lag) for k, w in weights.items()}


def common_index(series: dict[str, pd.Series]) -> pd.Index:
    common = None
    for s in series.values():
        common = s.index if common is None else common.intersection(s.index)
    return common


def stats_row(r: pd.Series, rf: pd.Series) -> dict:
    st = performance_stats(r, rf=rf.reindex(r.index))
    return {"ann ret": st.ann_return, "ann vol": st.ann_vol, "Sharpe": st.sharpe,
            "max DD": st.max_drawdown, "Calmar": st.calmar}


FMT = {"ann ret": ".1%", "ann vol": ".1%", "Sharpe": ".2f", "max DD": ".0%", "Calmar": ".2f"}


def md_table(df: pd.DataFrame, fmt: dict[str, str]) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float) and np.isnan(v):
                cells.append("")
            elif c in fmt:
                cells.append(format(v, fmt[c]))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def main() -> None:
    warnings.simplefilter("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-cache", action="store_true")
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)

    assets, spy = load_assets()
    rf = assets["cash"]
    prob, info = hmm_signal(spy, from_cache=args.from_cache)
    weights, rv21, ewma = schedules(prob, spy, assets)
    lines: list[str] = []
    out = lines.append

    # 1. The published table (lag 1) on the published window.
    lag1 = run_all(assets, weights, lag=1, cost_bps=5.0)
    win1 = common_index(lag1)
    lag1 = {k: v.reindex(win1).dropna() for k, v in lag1.items()}
    pub = pd.DataFrame([{"strategy": k, **stats_row(v, rf)} for k, v in lag1.items()])
    pub.to_csv(OUT / "table_published_lag1.csv", index=False, float_format="%.6g")

    # 2. Lag 1 vs lag 2 on the window common to both (one day shorter at the start).
    lag2 = run_all(assets, weights, lag=2, cost_bps=5.0)
    win = common_index({**lag1, **{k + " L2": v for k, v in lag2.items()}})
    l1 = {k: v.reindex(win).dropna() for k, v in lag1.items()}
    l2 = {k: v.reindex(win).dropna() for k, v in lag2.items()}
    excess = pd.DataFrame({**{k + " | lag 1": v - rf.reindex(v.index) for k, v in l1.items()},
                           **{k + " | lag 2": v - rf.reindex(v.index) for k, v in l2.items()}})
    bench = {}
    for bps in (0.0, 5.0, 10.0):
        res = rebalanced_backtest(assets, {"equity": 0.6, "bonds": 0.4}, freq="ME", cost_bps=bps)
        bench[bps] = (res.net.reindex(win), res.turnover.reindex(win))
        excess[f"60/40 monthly rebalance, {bps:.0f} bps"] = bench[bps][0] - rf.reindex(win)
    draws = block_bootstrap_sharpe(excess, block=63, n_boot=args.n_boot, seed=0)

    def iv(col_a: str, col_b: str | None = None) -> str:
        d = draws[col_a] if col_b is None else draws[col_a] - draws[col_b]
        lo, hi = np.percentile(d, [2.5, 97.5])
        return f"{lo:+.2f} to {hi:+.2f}"

    rows = []
    for k in RULES + STATICS:
        a, b = stats_row(l1[k], rf), stats_row(l2[k], rf)
        rows.append({"strategy": k, "ann ret L1": a["ann ret"], "ann ret L2": b["ann ret"],
                     "Sharpe L1": a["Sharpe"], "Sharpe L2": b["Sharpe"],
                     "Sharpe L2 - L1": b["Sharpe"] - a["Sharpe"],
                     "95% interval of the change": iv(k + " | lag 2", k + " | lag 1"),
                     "max DD L1": a["max DD"], "max DD L2": b["max DD"], "Calmar L2": b["Calmar"]})
    lagtab = pd.DataFrame(rows)
    lagtab.to_csv(OUT / "table_lag1_vs_lag2.csv", index=False, float_format="%.6g")

    # Lag-2 intervals in the shape of the published bootstrap table.
    rows = []
    for k in RULES + STATICS:
        rows.append({"strategy": k, "Sharpe L2": stats_row(l2[k], rf)["Sharpe"],
                     "Sharpe 95% interval (L2)": iv(k + " | lag 2"),
                     f"minus {BASE} (L2)": "" if k == BASE else iv(k + " | lag 2", BASE + " | lag 2"),
                     "minus 60/40 monthly, 5 bps": iv(k + " | lag 2", "60/40 monthly rebalance, 5 bps")})
    boot2 = pd.DataFrame(rows)
    boot2.to_csv(OUT / "table_lag2_bootstrap.csv", index=False)

    # 3. Cost drag from realised turnover.
    years = len(win) / 252.0
    eq_ret = {lag: stats_row(d["Static 100% equity"], rf)["ann ret"] for lag, d in ((1, l1), (2, l2))}
    rows = []
    for k in RULES + STATICS:
        for lag, d in ((1, l1), (2, l2)):
            tv = turnover(weights[k], execution_lag=lag).reindex(win).fillna(0.0)
            ann_tv = tv.sum() / years
            gross = backtest(assets, weights[k], cost_bps=0.0, execution_lag=lag).reindex(win).dropna()
            net10 = backtest(assets, weights[k], cost_bps=10.0, execution_lag=lag).reindex(win).dropna()
            g, n5, n10 = stats_row(gross, rf), stats_row(d[k], rf), stats_row(net10, rf)
            rows.append({"strategy": k, "lag": lag, "turnover / yr": ann_tv,
                         "switch days / yr": float((tv > 1e-12).sum() / years),
                         "drag 5 bps (pp/yr)": 100 * ann_tv * 5e-4, "drag 10 bps (pp/yr)": 100 * ann_tv * 1e-3,
                         "ann ret 0 bps": g["ann ret"], "ann ret 5 bps": n5["ann ret"], "ann ret 10 bps": n10["ann ret"],
                         "Sharpe 10 bps": n10["Sharpe"], "max DD 10 bps": n10["max DD"],
                         "give-up vs equity, 5 bps (pp/yr)": 100 * (eq_ret[lag] - n5["ann ret"]),
                         "of which gross (pp/yr)": 100 * (eq_ret[lag] - g["ann ret"])})
    cost = pd.DataFrame(rows)
    cost.to_csv(OUT / "table_cost_drag.csv", index=False, float_format="%.6g")

    # 4. The 60/40 benchmark: daily zero-cost (published) vs monthly rebalanced with drift.
    rows = [{"benchmark": "Static 60/40, daily rebalance, zero turnover (published)",
             **stats_row(l1["Static 60/40 equity/bonds"], rf), "turnover / yr": 0.0}]
    for bps, (net, tv) in bench.items():
        rows.append({"benchmark": f"60/40 drifting, rebalanced at month end, {bps:.0f} bps",
                     **stats_row(net.dropna(), rf), "turnover / yr": float(tv.fillna(0.0).sum() / years)})
    sixforty = pd.DataFrame(rows)
    sixforty.to_csv(OUT / "table_60_40.csv", index=False, float_format="%.6g")

    # 5. Threshold grid at both lags.
    rows = []
    for vol_name, vol in (("21d vol", rv21), ("EWMA vol", ewma)):
        for thr in (15.0, 20.0, 25.0):
            sig = vol_threshold_signal(vol, thr)
            row = {"rule": f"{vol_name} > {thr:.0f}%", "days in cash": float(sig.reindex(win).mean())}
            for lag in (1, 2):
                r = backtest(assets, regime_switch_weights(sig), cost_bps=5.0, execution_lag=lag).reindex(win).dropna()
                st = stats_row(r, rf)
                row[f"Sharpe L{lag}"] = st["Sharpe"]
                row[f"max DD L{lag}"] = st["max DD"]
            rows.append(row)
    row = {"rule": "HMM prob >= 0.5", "days in cash": float((prob.reindex(win) >= 0.5).mean())}
    for lag, d in ((1, l1), (2, l2)):
        st = stats_row(d[BASE], rf)
        row[f"Sharpe L{lag}"], row[f"max DD L{lag}"] = st["Sharpe"], st["max DD"]
    rows.append(row)
    grid = pd.DataFrame(rows)
    grid.to_csv(OUT / "table_threshold_grid.csv", index=False, float_format="%.6g")

    pd.DataFrame(l1).to_csv(OUT / "strategy_returns_lag1.csv", float_format="%.17g")
    pd.DataFrame(l2).to_csv(OUT / "strategy_returns_lag2.csv", float_format="%.17g")
    pd.DataFrame({f"60/40 monthly {bps:.0f} bps": v[0] for bps, v in bench.items()}).to_csv(
        OUT / "benchmark_60_40_monthly.csv", float_format="%.17g")

    # ---- markdown ----
    out("development data only, no holdout")
    out("")
    out("# Execution lag, cost drag and a rebalanced 60/40 for the allocation table, October 2026")
    out("")
    out(f"Class of every table in this file: **{CLASS}**. Stage S5 of the reopen scope; the published "
        f"allocation table (WRITEUP section \"Regime-conditional allocation\", `examples/regime_allocation.py`) is "
        f"development data and so is everything here; nothing is a claim and no holdout is opened. Written by "
        f"`examples/allocation_lag.py` at {git_head()}, {started.isoformat(timespec='seconds')}; walk-forward "
        f"signal `regimes.evaluate.walk_forward_oos(min_train=756, step=63)` on SPY log returns, "
        f"{info['n_refits']} refits, {info.get('n_skipped', 0)} skipped"
        + (f", {info['refits_converged']} converged" if "refits_converged" in info else "")
        + f", {info.get('seconds', 'cached')} s. Bootstrap: paired circular block bootstrap of annualised Sharpe "
        f"ratios over BIL (`regimes.allocation.block_bootstrap_sharpe`, 63-day blocks, {args.n_boot} draws, seed 0), "
        f"the same blocks for every column, so every difference below is paired. Source of the items: desk, "
        f"trader section 4 (allocation.py:104 execution at the signal close, HIGH; cost drag never stated, "
        f"MEDIUM; 60/40 daily-rebalanced at zero cost, LOW); desk synthesis finding 4.")
    out("")
    out("## 1. What execution lag means here")
    out("")
    out("`regimes.allocation.backtest` now takes `execution_lag` (default 1, the published rule, so every "
        "published number reproduces). With lag 1 the position earning the day-t return is the one the signal "
        "chose at the close of t-1: the backtest is filled at the same close that produced the signal, which a "
        "real book cannot do with a signal computed from closing prices. With lag 2 the signal from the close "
        "of t-2 is filled at the close of t-1 and earns close(t-1) to close(t): one full day later. The gap "
        "between the two is the execution-timing cost; the desk measured it for the trailing-vol rule and asked "
        "for the HMM switch, which needed the walk-forward run.")
    out("")
    out("## 2. The published table reproduced (lag 1, 5 bps per leg)")
    out("")
    out(f"Window {win1.min().date()} to {win1.max().date()} ({len(win1)} days), the window of the WRITEUP table "
        f"(every strategy restricted to the days the walk-forward signal exists). These rows should equal the "
        f"WRITEUP allocation table at its printed precision; `examples/regime_allocation.py` prints the same "
        f"numbers.")
    out("")
    out(md_table(pub, FMT))
    out("")
    out("One rounding note: the WRITEUP and README print the static-equity maximum drawdown as -52 percent; the "
        "script prints -51.5 percent to one decimal and the exact value is "
        f"{stats_row(lag1['Static 100% equity'], rf)['max DD']:.4%}, which rounds to -51 percent. The hand "
        "rounding of a rounded print is the only difference.")
    out("")
    out("## 3. One more day of execution lag, every rule")
    out("")
    out(f"Window {win.min().date()} to {win.max().date()} ({len(win)} days: the published window less its first "
        f"day, so that lag 1 and lag 2 are scored on the same days). L1 = published rule, L2 = one more day. "
        f"The interval is the paired bootstrap 95 percent interval for Sharpe(L2) - Sharpe(L1); the static "
        f"benchmarks hold constant weights, so the lag cannot change them.")
    out("")
    out(md_table(lagtab, {"ann ret L1": ".1%", "ann ret L2": ".1%", "Sharpe L1": ".2f", "Sharpe L2": ".2f",
                          "Sharpe L2 - L1": "+.2f", "max DD L1": ".0%", "max DD L2": ".0%", "Calmar L2": ".2f"}))
    out("")
    out("Sharpe intervals at lag 2, in the shape of the WRITEUP bootstrap table, plus each strategy against "
        "the monthly-rebalanced 60/40 of section 5 (5 bps):")
    out("")
    out(md_table(boot2, {"Sharpe L2": ".2f"}))
    out("")
    out("## 4. Cost drag from realised turnover")
    out("")
    out("Turnover is the sum of absolute weight changes on the day they are traded (a full equity-to-cash switch "
        "is turnover 2.0, so 10 bps at 5 bps per leg). Drag = annual turnover times the per-leg cost. "
        "`give-up vs equity` is the static 100 percent equity annual return less the rule's at 5 bps; `of which "
        "gross` is the same difference at zero cost, so the remainder is brokerage. Same window as section 3; a "
        "rule's turnover can differ by one switch between the lags when a trade falls on the window's first day "
        "at one lag and inside the window at the other. The vol-target rule trades a little every day, so its "
        "switch-day count is the day count.")
    out("")
    out(md_table(cost, {"turnover / yr": ".2f", "switch days / yr": ".1f", "drag 5 bps (pp/yr)": ".2f",
                        "drag 10 bps (pp/yr)": ".2f", "ann ret 0 bps": ".1%", "ann ret 5 bps": ".1%",
                        "ann ret 10 bps": ".1%", "Sharpe 10 bps": ".2f", "max DD 10 bps": ".0%",
                        "give-up vs equity, 5 bps (pp/yr)": "+.2f", "of which gross (pp/yr)": "+.2f"}))
    out("")
    out("## 5. The 60/40 benchmark, charged its rebalance")
    out("")
    out("The published 60/40 holds constant weights every day, which is a daily rebalance that trades nothing "
        "and pays nothing. `regimes.allocation.rebalanced_backtest` lets the weights drift with returns and "
        "resets them to 60/40 at the close of the last trading day of each month, paying the per-leg cost on "
        "the turnover of each reset. Same window as section 3.")
    out("")
    out(md_table(sixforty, {**FMT, "turnover / yr": ".3f"}))
    out("")
    out("## 6. Trailing-vol threshold grid at both lags")
    out("")
    out("The WRITEUP grid (15, 20, 25 percent) with the lag-2 column beside it; the HMM row is the regime switch. "
        "Same window as section 3; `days in cash` is the share of days the rule holds cash.")
    out("")
    out(md_table(grid, {"days in cash": ".0%", "Sharpe L1": ".2f", "max DD L1": ".0%", "Sharpe L2": ".2f",
                        "max DD L2": ".0%"}))
    out("")
    out("## 7. Desk checks on the development forecasts (Mincer-Zarnowitz, variance-swap sign)")
    out("")
    try:
        import dev_forecast_desk
        lines += dev_forecast_desk.sections()
    except FileNotFoundError:
        out("Not available: run `examples/dev_forecast_desk.py` first.")
        out("")
    out("## Files")
    out("")
    out("`docs/results/allocation_lag/`: `hmm_prob_spy.csv` (the walk-forward signal), `strategy_returns_lag1.csv` "
        "and `strategy_returns_lag2.csv` (daily net returns, 5 bps), `benchmark_60_40_monthly.csv`, and one CSV per "
        "table above. `docs/results/dev_vix_forecasts/`: the development forecasts and the desk tables.")
    DOC.write_text("\n".join(lines) + "\n", encoding="ascii")
    print("\n".join(lines))
    print(f"\nwritten: {DOC.relative_to(REPO)}")


if __name__ == "__main__":
    main()
