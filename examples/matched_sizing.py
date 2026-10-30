"""Spent data, exploratory: the matched sizing test, tier 1 (docs/MATCHED_SIZING_PROTOCOL_2026-10.md).

Does the HMM switch control tail risk better than a vol target with a no-trade band once the two are
calibrated to the same turnover and exposure? The protocol was committed (e2cf02a) before this script
was run; this script implements its sections 4 (calibration), 5 (score windows, metrics) and 7
(simulation check) and nothing else.

    python examples/matched_sizing.py                 # all parts (the secondary window downloads data)
    python examples/matched_sizing.py --skip-download  # primary window and simulation only
    python examples/matched_sizing.py --skip-sim       # no simulation (it runs ten walk-forwards)

Writes CSV tables and results.md under docs/results/matched_sizing/.
"""
from __future__ import annotations

import argparse
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

from regimes.allocation import (
    backtest,
    banded_vol_target_weights,
    confirmed_switch_weights,
    max_drawdown,
    regime_switch_weights,
    sharpe,
    static_weights,
    turnover,
    vol_threshold_signal,
)
from regimes.data import load_index_prices, load_index_returns
from regimes.evaluate import ewma_vol, realised_vol, walk_forward_oos

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "examples"))
OUT = REPO / "docs" / "results" / "matched_sizing"
SIGNAL = REPO / "docs" / "results" / "allocation_lag" / "hmm_prob_spy.csv"

LAG = 2
BUDGETS = (4.0, 8.0, 16.0)
K_GRID = range(1, 64)
S_GRID = np.round(np.arange(4.0, 20.0 + 1e-9, 0.25), 2)
B_GRID = np.round(np.arange(0.0, 0.5 + 1e-9, 0.005), 3)
CAL = ("2008-01-07", "2017-12-29")
PRIMARY = ("2018-01-02", "2023-12-29")
SECONDARY_START = "2024-01-02"
SEEDS = (1, 2, 3, 4, 7)


# ---------------------------------------------------------------- data

def load_primary() -> tuple[pd.DataFrame, pd.Series, pd.Series]:
    start, end = "2005-01-01", "2023-12-31"
    return _assets(start, end) + (pd.read_csv(SIGNAL, index_col=0, parse_dates=True).iloc[:, 0],)


def _assets(start: str, end: str) -> tuple[pd.DataFrame, pd.Series]:
    eq = load_index_prices("SPY", start, end).pct_change()
    cash = load_index_prices("BIL", start, end).pct_change()
    assets = pd.DataFrame({"equity": eq, "cash": cash}).dropna()
    spy = load_index_returns("SPY", start, end)  # log returns in percent
    return assets, spy


# ---------------------------------------------------------------- arms and measurements

def eff_equity(w: pd.DataFrame) -> pd.Series:
    return w["equity"].shift(LAG)


def window_turnover(w: pd.DataFrame, lo: str, hi: str) -> float:
    t = turnover(w, execution_lag=LAG).loc[lo:hi]
    return float(t.sum() / (len(t) / 252.0))


def window_exposure(w: pd.DataFrame, lo: str, hi: str) -> float:
    return float(eff_equity(w).loc[lo:hi].mean())


def _closest(values: dict, target: float):
    """Key whose value is closest to target; ties go to the smaller key (dict is in ascending key order)."""
    best, gap = None, math.inf
    for key, v in values.items():
        if abs(v - target) < gap - 1e-12:
            best, gap = key, abs(v - target)
    return best


def calibrate(prob: pd.Series, vol: pd.Series, index: pd.Index, lo: str, hi: str) -> list[dict]:
    """Protocol section 4, on [lo, hi]. ``vol`` is annualised EWMA vol in percent."""
    # Weights are built on the signal's own dates (as in ``run_window``) so the band and confirmation paths
    # are identical in calibration and scoring; only the measurement is restricted to the asset dates.
    vol = vol.dropna()
    h = {k: confirmed_switch_weights(prob, confirm=k).reindex(index).dropna() for k in K_GRID}
    h_turn = {k: window_turnover(w, lo, hi) for k, w in h.items()}
    v_turn, v_exp = {}, {}
    for s in S_GRID:
        for b in B_GRID:
            w = banded_vol_target_weights(vol, float(s), band=float(b)).reindex(index).dropna()
            v_turn[(s, b)] = window_turnover(w, lo, hi)
            v_exp[(s, b)] = window_exposure(w, lo, hi)
    rows = []
    for budget in BUDGETS:
        k = _closest(h_turn, budget)
        e_b = window_exposure(h[k], lo, hi)
        b_of_s = {s: _closest({b: v_turn[(s, b)] for b in B_GRID}, budget) for s in S_GRID}
        s_b = _closest({s: v_exp[(s, b_of_s[s])] for s in S_GRID}, e_b)
        b_b = b_of_s[s_b]
        rows.append({
            "budget": budget, "k": k, "hmm_turnover": h_turn[k], "hmm_exposure": e_b,
            "hmm_budget_reached": abs(h_turn[k] - budget) <= 0.5,
            "s": float(s_b), "band": float(b_b), "vt_turnover": v_turn[(s_b, b_b)],
            "vt_exposure": v_exp[(s_b, b_b)], "vt_budget_reached": abs(v_turn[(s_b, b_b)] - budget) <= 0.5,
        })
    return rows


def expected_shortfall(r: np.ndarray, q: float = 0.01) -> float:
    m = max(1, math.ceil(q * len(r)))
    return float(-np.sort(r)[:m].mean())


def worst_21d(r: pd.Series) -> float:
    return float(((1.0 + r).rolling(21).apply(np.prod, raw=True) - 1.0).min())


def es_gain_bootstrap(h: pd.Series, v: pd.Series, *, block: int = 63, n_boot: int = 2000,
                      seed: int = 0) -> tuple[float, float, float]:
    """ES(V) - ES(H) on the realised days and its paired circular block bootstrap 95% interval."""
    x = pd.concat([h, v], axis=1).dropna().to_numpy()
    n = len(x)
    point = expected_shortfall(x[:, 1]) - expected_shortfall(x[:, 0])
    rng = np.random.default_rng(seed)
    n_blocks = -(-n // block)
    offsets = np.arange(block)
    draws = np.empty(n_boot)
    for i in range(n_boot):
        starts = rng.integers(0, n, size=n_blocks)
        idx = ((starts[:, None] + offsets[None, :]) % n).ravel()[:n]
        s = x[idx]
        draws[i] = expected_shortfall(s[:, 1]) - expected_shortfall(s[:, 0])
    lo, hi = np.percentile(draws, [2.5, 97.5])
    return point, float(lo), float(hi)


def score(name: str, w: pd.DataFrame, assets: pd.DataFrame, lo: str, hi: str) -> tuple[dict, dict]:
    out, nets = {"arm": name}, {}
    for bps in (5.0, 10.0):
        net = backtest(assets, w.reindex(assets.index).dropna(), cost_bps=bps, execution_lag=LAG).loc[lo:hi]
        nets[bps] = net
        tag = f"{bps:g}bps"
        out[f"ES1% {tag}"] = expected_shortfall(net.to_numpy())
        out[f"ann vol {tag}"] = float(net.std() * np.sqrt(252))
        out[f"worst 21d {tag}"] = worst_21d(net)
        out[f"max DD {tag}"] = max_drawdown(net)
        out[f"Sharpe {tag}"] = sharpe(net, rf=assets["cash"].reindex(net.index))
    out["turnover/yr"] = window_turnover(w.reindex(assets.index).dropna(), lo, hi)
    out["exposure"] = window_exposure(w.reindex(assets.index).dropna(), lo, hi)
    out["days"] = len(nets[5.0])
    return out, nets


def run_window(label: str, assets, spy, prob, cal_rows, lo, hi) -> tuple[pd.DataFrame, pd.DataFrame]:
    vol = ewma_vol(spy) * np.sqrt(252)
    rv21 = realised_vol(spy, 21) * np.sqrt(252)
    stats, gains = [], []
    for row in cal_rows:
        hw = confirmed_switch_weights(prob, confirm=row["k"])
        vw = banded_vol_target_weights(vol.dropna(), row["s"], band=row["band"])
        hs, hn = score(f"H(k={row['k']}), budget {row['budget']:g}", hw, assets, lo, hi)
        vs, vn = score(f"V(s={row['s']:g}, b={row['band']:g}), budget {row['budget']:g}", vw, assets, lo, hi)
        stats += [hs, vs]
        for bps in (5.0, 10.0):
            p, l, u = es_gain_bootstrap(hn[bps], vn[bps])
            gains.append({"window": label, "budget": row["budget"], "cost": f"{bps:g}bps",
                          "ES gain (V-H)": p, "95% lo": l, "95% hi": u, "days": len(hn[bps])})
    refs = {
        "ref H(1) published switch": regime_switch_weights(prob),
        "ref V(10, 0) published vol target": banded_vol_target_weights(vol.dropna(), 10.0, band=0.0),
        "ref 21d vol > 20% switch": regime_switch_weights(vol_threshold_signal(rv21, 20.0)),
        "ref static 100% SPY": static_weights(assets.index, {"equity": 1.0, "cash": 0.0}),
    }
    for name, w in refs.items():
        stats.append(score(name, w, assets, lo, hi)[0])
    st = pd.DataFrame(stats)
    st.insert(0, "window", label)
    return st, pd.DataFrame(gains)


# ---------------------------------------------------------------- simulation (protocol section 7)

def simulation() -> pd.DataFrame:
    from why_hmm_loses import _simulate

    global BUDGETS
    keep, BUDGETS = BUDGETS, (8.0,)
    rows = []
    try:
        for kind in ("continuous", "two-state"):
            for seed in SEEDS:
                t0 = time.perf_counter()
                r = _simulate(kind, 5000, seed)
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    prob = walk_forward_oos(r, min_train=756, step=63).high_vol_prob
                assets = pd.DataFrame({"equity": np.expm1(r / 100.0), "cash": 0.0}, index=r.index)
                vol = ewma_vol(r) * np.sqrt(252)
                oos = prob.dropna().index
                mid = oos[len(oos) // 2]
                cal = calibrate(prob, vol, assets.index, str(oos[0].date()), str(oos[len(oos) // 2 - 1].date()))[0]
                hw = confirmed_switch_weights(prob, confirm=cal["k"])
                vw = banded_vol_target_weights(vol.dropna(), cal["s"], band=cal["band"])
                lo, hi = str(mid.date()), str(oos[-1].date())
                hs, hn = score("H", hw, assets, lo, hi)
                vs, vn = score("V", vw, assets, lo, hi)
                p, l, u = es_gain_bootstrap(hn[5.0], vn[5.0])
                rows.append({"market": kind, "seed": seed, "k": cal["k"], "s": cal["s"], "band": cal["band"],
                             "H turnover/yr": hs["turnover/yr"], "V turnover/yr": vs["turnover/yr"],
                             "H exposure": hs["exposure"], "V exposure": vs["exposure"],
                             "ES gain (V-H)": p, "95% lo": l, "95% hi": u})
                print(f"  sim {kind} seed {seed}: gain {p:+.4f} [{l:+.4f}, {u:+.4f}] "
                      f"({time.perf_counter() - t0:.0f}s)", flush=True)
    finally:
        BUDGETS = keep
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-download", action="store_true")
    ap.add_argument("--skip-sim", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)

    assets, spy, prob = load_primary()
    vol = ewma_vol(spy) * np.sqrt(252)
    t0 = time.perf_counter()
    cal = pd.DataFrame(calibrate(prob, vol, assets.index, *CAL))
    cal.to_csv(OUT / "calibration.csv", index=False)
    print(f"calibration ({time.perf_counter() - t0:.0f}s):\n{cal.to_string(index=False)}", flush=True)

    st, gains = run_window("primary 2018-2023", assets, spy, prob, cal.to_dict("records"), *PRIMARY)

    if not args.skip_download:
        try:
            end = pd.Timestamp.today().strftime("%Y-%m-%d")
            a2, s2 = _assets("2005-01-01", end)
            sig = OUT / f"hmm_prob_spy_2005_{end}.csv"
            if sig.exists():
                p2 = pd.read_csv(sig, index_col=0, parse_dates=True).iloc[:, 0]
            else:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    p2 = walk_forward_oos(s2, min_train=756, step=63).high_vol_prob.rename("hmm_high_vol_prob")
                p2.to_csv(sig, float_format="%.17g")
            st2, g2 = run_window(f"secondary {SECONDARY_START} to {a2.index[-1].date()}", a2, s2, p2,
                                 cal.to_dict("records"), SECONDARY_START, str(a2.index[-1].date()))
            st, gains = pd.concat([st, st2]), pd.concat([gains, g2])
        except Exception as exc:  # noqa: BLE001
            print(f"secondary window not run: {exc!r}", flush=True)
            (OUT / "secondary_not_run.txt").write_text(repr(exc))

    st.to_csv(OUT / "scores.csv", index=False, float_format="%.6g")
    gains.to_csv(OUT / "es_gain.csv", index=False, float_format="%.6g")
    print(gains.to_string(index=False), flush=True)

    if not args.skip_sim:
        sim = simulation()
        sim.to_csv(OUT / "simulation.csv", index=False, float_format="%.6g")


if __name__ == "__main__":
    main()
