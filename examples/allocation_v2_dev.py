"""Development data only, no holdout: regime overlays on modern multi-asset benchmarks, 2007-2017.

The development half of /opt/hmm-agent/reviews/ALLOCATION_V2_PLAN_2026-10-17.md (section 2), run on the
free ETF universe with every download ending 2017-12-31 (rule 3 of the reopen scope). The 2018-2026 split
is NOT run here; it is the holdout the draft protocol (docs/ALLOCATION_V2_PROTOCOL_DRAFT.md) describes
and nothing past 2017-12-31 is opened.

Question: does a regime overlay (two-state HMM probability, trailing vol, EWMA vol, multivariate
turbulence, or a stock-bond correlation flag) improve a modern multi-asset allocation after costs and
with realistic execution, by more than a plain volatility rule does?

Execution rule, first: every signal is computed from closing prices up to the close of t-1 and filled
at the close of t (``execution_lag=2`` in ``regimes.allocation.drift_backtest``); portfolios drift between
trades; the static benchmarks are rebalanced at each month end; costs are charged per leg of turnover at
5 and 10 basis points; nothing is levered.

    python examples/allocation_v2_dev.py               # recompute the HMM walk-forward (about a minute)
    python examples/allocation_v2_dev.py --from-cache  # reuse docs/results/allocation_v2_dev/hmm_prob_spy_2017.csv

Writes docs/results/allocation_v2_dev/*.csv and docs/ALLOCATION_V2_DEV_2026-10.md.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from regimes.allocation import (
    block_bootstrap_drawdown,
    block_bootstrap_sharpe,
    drift_backtest,
    performance_stats,
    period_end_decisions,
)
from regimes.data import load_index_prices
from regimes.evaluate import ewma_vol, realised_vol, walk_forward_oos
from regimes.turbulence import financial_turbulence

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / "docs" / "results" / "allocation_v2_dev"
DOC = REPO / "docs" / "ALLOCATION_V2_DEV_2026-10.md"
START, END = "2000-01-01", "2017-12-31"   # downloads end 2017-12-31: the development half only
TICKERS = ["SPY", "EFA", "EEM", "IEF", "TLT", "TIP", "LQD", "HYG", "GLD", "DBC", "VNQ", "BIL"]
RISKY = [t for t in TICKERS if t != "BIL"]
EQUITY = ["SPY", "EFA", "EEM"]
GOVT = ["IEF", "TLT"]
TURBULENCE_PANEL = ["SPY", "EFA", "EEM", "IEF", "TLT", "LQD"]  # the ETFs with history from 2003
LAG = 2
CLASS = ("development data only (ETF universe, downloads ending 2017-12-31; walk-forward HMM on SPY), "
         "no holdout; the 2018-2026 split is not run")


def git_head() -> str:
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True,
                              text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True,
                               text=True, check=True).stdout.strip()
        return head + (" plus uncommitted files" if dirty else "")
    except Exception:  # noqa: BLE001
        return "unknown"


def load() -> tuple[pd.DataFrame, pd.DataFrame]:
    prices = pd.DataFrame({t: load_index_prices(t, START, END) for t in TICKERS})
    returns = prices.pct_change()
    return prices, returns


# ---- signals (all causal; each a 0/1 state series) -------------------------------------------------
def signals(prices: pd.DataFrame, returns: pd.DataFrame, *, from_cache: bool) -> tuple[dict[str, pd.Series], dict]:
    spy_log = (100 * np.log(prices["SPY"]).diff()).dropna().rename("SPY")
    path = OUT / "hmm_prob_spy_2017.csv"
    if from_cache and path.exists():
        prob = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0]
        info = json.loads((OUT / "hmm_signal.json").read_text())
    else:
        t0 = time.perf_counter()
        wf = walk_forward_oos(spy_log, min_train=756, step=63)
        info = {"n_refits": int(wf.n_refits), "n_skipped": int(wf.n_skipped),
                "seconds": round(time.perf_counter() - t0, 1), "first_oos": str(wf.high_vol_prob.index[0].date())}
        conv = getattr(wf, "convergence", None)
        if conv is not None and len(conv):
            info["refits_converged"] = int(pd.DataFrame(conv)["best_converged"].fillna(False).sum())
        prob = wf.high_vol_prob.rename("hmm_high_vol_prob")
        prob.to_csv(path, float_format="%.17g")
        (OUT / "hmm_signal.json").write_text(json.dumps(info, indent=1))
    rv21 = realised_vol(spy_log, 21) * np.sqrt(252)
    ewma = ewma_vol(spy_log) * np.sqrt(252)
    turb = financial_turbulence(returns[TURBULENCE_PANEL].dropna(), causal=True, window=504, min_periods=252)
    # Walk-forward 90th percentile: the quantile of all turbulence values strictly before t.
    thr = turb.expanding(min_periods=252).quantile(0.9).shift(1)
    turb21 = turb.rolling(21).mean()
    corr63 = returns["SPY"].rolling(63).corr(returns["IEF"])
    sig = {
        "HMM prob >= 0.5": (prob >= 0.5).astype(float),
        "21d vol > 20%": (rv21.dropna() >= 20.0).astype(float),
        "EWMA vol > 20%": (ewma.dropna() >= 20.0).astype(float),
        "turbulence > wf p90": (turb > thr).astype(float)[thr.notna()],
        "turbulence 21d mean > wf p90": (turb21 > thr).astype(float)[thr.notna() & turb21.notna()],
        "stock-bond corr63 > 0": (corr63.dropna() > 0).astype(float),
    }
    return sig, info


# ---- benchmark targets (per-day target weights; read at month ends) -------------------------------
def benchmark_targets(returns: pd.DataFrame) -> dict[str, pd.DataFrame]:
    idx = returns.index
    zeros = pd.DataFrame(0.0, index=idx, columns=TICKERS)

    def const(alloc: dict) -> pd.DataFrame:
        df = zeros.copy()
        for k, v in alloc.items():
            df[k] = v
        return df

    b60 = const({"SPY": 0.6, "IEF": 0.4})
    one_n = const({t: 1.0 / len(RISKY) for t in RISKY})
    vol63 = returns[RISKY].rolling(63).std() * np.sqrt(252)
    inv = 1.0 / vol63
    rp = zeros.copy()
    rp[RISKY] = inv.div(inv.sum(axis=1), axis=0)
    # Vol-targeted 60/40 at 10 percent: the 60/40 scaled by min(1, 10% / EWMA vol of the 60/40), rest BIL.
    r6040 = 0.6 * returns["SPY"] + 0.4 * returns["IEF"]
    ew = ewma_vol(100 * r6040.dropna()) * np.sqrt(252)
    scale = (10.0 / ew).clip(upper=1.0).reindex(idx)
    vt = zeros.copy()
    vt["SPY"], vt["IEF"] = 0.6 * scale, 0.4 * scale
    vt["BIL"] = 1.0 - scale
    tilt = const({"SPY": 0.5, "IEF": 0.3, "GLD": 0.2 / 3, "DBC": 0.2 / 3, "VNQ": 0.2 / 3})
    return {"60/40 SPY/IEF": b60, "1/N (11 ETFs)": one_n, "inverse-vol (11 ETFs, 63d)": rp,
            "vol-target 60/40 at 10%": vt, "50/30/20 real-asset tilt": tilt}


def apply_overlay(target: pd.DataFrame, state: pd.Series, kind: str) -> pd.DataFrame:
    """Overlay action on a target schedule: ``equity`` sends the equity sleeve to BIL when the state is
    1; ``bonds`` sends the government-bond sleeve half to GLD and half to BIL."""
    out = target.copy()
    on = state.reindex(out.index).fillna(0.0).to_numpy() > 0.5
    if kind == "equity":
        moved = out[EQUITY].sum(axis=1).to_numpy()
        out.loc[on, EQUITY] = 0.0
        out.loc[on, "BIL"] = out.loc[on, "BIL"].to_numpy() + moved[on]
    elif kind == "bonds":
        moved = out[GOVT].sum(axis=1).to_numpy()
        out.loc[on, GOVT] = 0.0
        out.loc[on, "GLD"] = out.loc[on, "GLD"].to_numpy() + 0.5 * moved[on]
        out.loc[on, "BIL"] = out.loc[on, "BIL"].to_numpy() + 0.5 * moved[on]
    else:
        raise ValueError(kind)
    return out


def decisions(target: pd.DataFrame, state: pd.Series | None, kind: str | None, first: pd.Timestamp) -> pd.DataFrame:
    """Decision rows: the first day, every month end, and (with an overlay) every day the state changes."""
    idx = target.index[target.index >= first]
    tgt = target.loc[idx]
    if state is not None:
        tgt = apply_overlay(tgt, state, kind)
    dec = period_end_decisions(idx, tgt, freq="ME")
    if state is not None:
        st = state.reindex(idx).ffill()
        changed = st.ne(st.shift(1)).to_numpy().copy()
        changed[0] = False
        dec.loc[changed] = tgt.loc[changed].to_numpy()
    return dec


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


OVERLAYS = {"HMM prob >= 0.5": "equity", "21d vol > 20%": "equity", "EWMA vol > 20%": "equity",
            "turbulence > wf p90": "equity", "turbulence 21d mean > wf p90": "equity",
            "stock-bond corr63 > 0": "bonds"}


def main() -> None:
    warnings.simplefilter("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-cache", action="store_true")
    parser.add_argument("--n-boot", type=int, default=2000)
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc)

    prices, returns = load()
    sig, info = signals(prices, returns, from_cache=args.from_cache)
    targets = benchmark_targets(returns)
    full = returns.dropna()  # every ETF has a return (BIL starts 2007-05-30)
    first = max([full.index[0]] + [s.index[0] for s in sig.values()]
                + [t.dropna().index[0] for t in targets.values()])
    first = full.index[full.index >= first][0]
    rf = returns["BIL"]

    nets: dict[tuple[str, str, float], pd.Series] = {}
    tvs: dict[tuple[str, str, float], float] = {}
    for bname, tgt in targets.items():
        for oname in ["none", *OVERLAYS]:
            state = None if oname == "none" else sig[oname]
            kind = None if oname == "none" else OVERLAYS[oname]
            dec = decisions(tgt, state, kind, first)
            for bps in (5.0, 10.0):
                res = drift_backtest(full, dec, cost_bps=bps, execution_lag=LAG)
                nets[(bname, oname, bps)] = res.net
                tvs[(bname, oname, bps)] = float(res.turnover.sum() / (len(res.net) / 252.0))
    common = None
    for s in nets.values():
        common = s.index if common is None else common.intersection(s.index)
    nets = {k: v.reindex(common) for k, v in nets.items()}
    years = len(common) / 252.0

    def row(k) -> dict:
        st = performance_stats(nets[k], rf=rf.reindex(common))
        return {"ann ret": st.ann_return, "ann vol": st.ann_vol, "Sharpe": st.sharpe, "max DD": st.max_drawdown,
                "Calmar": st.calmar, "turnover / yr": tvs[k]}

    # Bootstraps at 5 bps: paired Sharpe and drawdown draws over every (benchmark, overlay) column.
    cols5 = [k for k in nets if k[2] == 5.0]
    excess = pd.DataFrame({f"{b} | {o}": nets[(b, o, 5.0)] - rf.reindex(common) for b, o, _ in cols5})
    plain = pd.DataFrame({f"{b} | {o}": nets[(b, o, 5.0)] for b, o, _ in cols5})
    sh = block_bootstrap_sharpe(excess, block=63, n_boot=args.n_boot, seed=0)
    dd = block_bootstrap_drawdown(plain, block=63, n_boot=args.n_boot, seed=0)

    def iv(draws, a, b) -> tuple[float, float]:
        lo, hi = np.percentile(draws[a] - draws[b], [2.5, 97.5])
        return float(lo), float(hi)

    tables = {}
    for bps in (5.0, 10.0):
        rows = []
        for bname in targets:
            base = row((bname, "none", bps))
            for oname in ["none", *OVERLAYS]:
                r = row((bname, oname, bps))
                entry = {"benchmark": bname, "overlay": oname, **r,
                         "dSharpe vs benchmark": r["Sharpe"] - base["Sharpe"],
                         "dMaxDD vs benchmark (pp)": 100 * (r["max DD"] - base["max DD"])}
                if bps == 5.0 and oname != "none":
                    a, b = f"{bname} | {oname}", f"{bname} | none"
                    lo, hi = iv(sh, a, b)
                    entry["dSharpe 95%"] = f"{lo:+.2f} to {hi:+.2f}"
                    lo, hi = iv(dd, a, b)
                    entry["dMaxDD 95% (pp)"] = f"{100 * lo:+.1f} to {100 * hi:+.1f}"
                rows.append(entry)
        tables[bps] = pd.DataFrame(rows)
        tables[bps].to_csv(OUT / f"table_overlays_{bps:.0f}bps.csv", index=False, float_format="%.6g")

    # HMM overlay against the trailing-vol overlay, per benchmark (claim C3's shape), 5 bps.
    rows = []
    for bname in targets:
        a, b = f"{bname} | HMM prob >= 0.5", f"{bname} | 21d vol > 20%"
        ra, rb = row((bname, "HMM prob >= 0.5", 5.0)), row((bname, "21d vol > 20%", 5.0))
        slo, shi = iv(sh, a, b)
        dlo, dhi = iv(dd, a, b)
        rows.append({"benchmark": bname, "Sharpe HMM": ra["Sharpe"], "Sharpe 21d vol": rb["Sharpe"],
                     "dSharpe 95%": f"{slo:+.2f} to {shi:+.2f}", "max DD HMM": ra["max DD"],
                     "max DD 21d vol": rb["max DD"], "dMaxDD 95% (pp)": f"{100 * dlo:+.1f} to {100 * dhi:+.1f}"})
    hmm_vs_vol = pd.DataFrame(rows)
    hmm_vs_vol.to_csv(OUT / "table_hmm_vs_trailing_vol.csv", index=False, float_format="%.6g")

    # Signal summary on the window.
    rows = []
    for name, s in sig.items():
        st = s.reindex(common).ffill()
        rows.append({"signal": name, "share of days on": float(st.mean()),
                     "changes / yr": float(st.ne(st.shift(1)).sum() / years)})
    sigtab = pd.DataFrame(rows)
    sigtab.to_csv(OUT / "table_signals.csv", index=False, float_format="%.6g")
    pd.DataFrame({f"{b} | {o} | {int(c)} bps": v for (b, o, c), v in nets.items()}).to_csv(
        OUT / "strategy_returns.csv", float_format="%.17g")
    pd.DataFrame({k: v.reindex(common) for k, v in sig.items()}).to_csv(OUT / "signals.csv")

    # Claims C1-C3 of the plan, read on development data (a prior for the protocol, not a verdict).
    def better_count(col: str, draws) -> tuple[int, int]:
        """(benchmarks where the overlay is better with the interval wholly above zero, where it is worse with
        the interval wholly below). For both statistics a positive overlay-minus-benchmark difference is better
        (a higher Sharpe ratio; a less negative maximum drawdown)."""
        better = worse = 0
        for bname in targets:
            lo, hi = iv(draws, f"{bname} | {col}", f"{bname} | none")
            if lo > 0:
                better += 1
            if hi < 0:
                worse += 1
        return better, worse

    claims = []
    for oname in OVERLAYS:
        sb, sw = better_count(oname, sh)
        db, dw = better_count(oname, dd)
        cut5 = sum(100 * (row((b, oname, 5.0))["max DD"] - row((b, "none", 5.0))["max DD"]) >= 5 for b in targets)
        claims.append({"overlay": oname, "C1 Sharpe: better / worse (of 5)": f"{sb} / {sw}",
                       "C2 drawdown cut >= 5 pp (point, of 5)": cut5,
                       "C2 drawdown interval: better / worse (of 5)": f"{db} / {dw}"})
    claimtab = pd.DataFrame(claims)
    claimtab.to_csv(OUT / "table_claims_dev.csv", index=False)

    # ---- markdown ----
    L: list[str] = []
    out = L.append
    out("development data only, no holdout")
    out("")
    out("# Regime overlays on multi-asset benchmarks, development half (2007-2017), October 2026")
    out("")
    out(f"Class of every table in this file: **{CLASS}**. Written by `examples/allocation_v2_dev.py` at "
        f"{git_head()}, {started.isoformat(timespec='seconds')}. This is the development half of the plan in "
        f"`/opt/hmm-agent/reviews/ALLOCATION_V2_PLAN_2026-10-17.md`; the draft protocol for the unopened 2018-2026 "
        f"half is `docs/ALLOCATION_V2_PROTOCOL_DRAFT.md`. Nothing here is a claim; the numbers are the development "
        f"evidence the protocol's expectations rest on. Source: desk, trader section 4 and the editor view that the "
        f"allocation section be demoted or rebuilt as an allocation study; ALLOCATION_V2_PLAN section 2.")
    out("")
    out("## 1. Design")
    out("")
    out(f"- Data: Yahoo adjusted closes of {', '.join(TICKERS)}, downloads 2000-01-01 to 2017-12-31 "
        f"(`data/<ticker>_2000-01-01_2017-12-31.csv`); scored window {common.min().date()} to {common.max().date()} "
        f"({len(common)} days, {years:.1f} years), the first day on which every ETF, every signal and every "
        f"benchmark target exists. BIL (cash, and the Sharpe ratio's risk-free leg) starts 2007-05-30.")
    out(f"- Execution: signals use closes up to t-1 and are filled at the close of t (`execution_lag={LAG}` in "
        f"`regimes.allocation.drift_backtest`); portfolios drift between trades; costs per leg of turnover at 5 and "
        f"10 bps; no leverage. Decisions are taken on the first day, at every month end (benchmark rebalance) and, "
        f"for an overlay, on every day its state changes.")
    out("- Benchmarks: static 60/40 (SPY/IEF); 1/N over the 11 risky ETFs; inverse 63-day-vol weights over the 11 "
        "(no leverage, weights sum to one); the 60/40 scaled to a 10 percent EWMA vol target with the remainder in "
        "BIL (scale read at month ends); a 50/30/20 tilt (SPY 50, IEF 30, GLD/DBC/VNQ equal 20).")
    out(f"- Overlays (equity action: SPY, EFA and EEM weights to BIL while the state is on; bond action: IEF and TLT "
        f"weights half to GLD, half to BIL): HMM high-vol probability >= 0.5 from "
        f"`regimes.evaluate.walk_forward_oos(min_train=756, step=63)` on SPY log returns from 2000 ({info['n_refits']} "
        f"refits, {info.get('n_skipped', 0)} skipped"
        + (f", {info['refits_converged']} converged" if "refits_converged" in info else "")
        + f", first out-of-sample day {info.get('first_oos', 'cached')}); trailing 21-day vol >= 20 percent "
        f"annualised; EWMA (0.94) vol >= 20 percent; financial turbulence (`regimes.turbulence.financial_turbulence`, "
        f"causal 504-day window) on the panel {', '.join(TURBULENCE_PANEL)} above the 90th percentile of all its "
        f"values strictly before t (the plan's rule; and a 21-day mean of turbulence against the same threshold, "
        f"added because the daily rule whipsaws); the stock-bond action when the trailing 63-day SPY/IEF correlation "
        f"is above zero.")
    out("- Statistics: paired circular block bootstrap (63-day blocks, "
        f"{args.n_boot} draws, seed 0, the same blocks for every column) of the annualised Sharpe ratio over BIL "
        "(`block_bootstrap_sharpe`) and of the maximum drawdown of the resampled path (`block_bootstrap_drawdown`; "
        "the drawdown of a reordered path, so a statement about the return distribution and its clustering, not "
        "about the one realised path).")
    out("")
    out("## 2. Signals on the window")
    out("")
    out(md_table(sigtab, {"share of days on": ".1%", "changes / yr": ".1f"}))
    out("")
    out("## 3. Every benchmark with every overlay, 5 bps per leg")
    out("")
    out("`dSharpe` and `dMaxDD` are overlay minus benchmark (a positive `dMaxDD` is a shallower drawdown); the "
        "intervals are the paired bootstrap 95 percent intervals of the same differences.")
    out("")
    fmt = {"ann ret": ".1%", "ann vol": ".1%", "Sharpe": ".2f", "max DD": ".0%", "Calmar": ".2f",
           "turnover / yr": ".2f", "dSharpe vs benchmark": "+.2f", "dMaxDD vs benchmark (pp)": "+.1f"}
    out(md_table(tables[5.0], fmt))
    out("")
    out("## 4. The same at 10 bps per leg")
    out("")
    out(md_table(tables[10.0].drop(columns=[c for c in tables[10.0].columns if "95%" in c]), fmt))
    out("")
    out("## 5. HMM overlay against the trailing-vol overlay (the shape of claim C3), 5 bps")
    out("")
    out(md_table(hmm_vs_vol, {"Sharpe HMM": ".2f", "Sharpe 21d vol": ".2f", "max DD HMM": ".0%", "max DD 21d vol": ".0%"}))
    out("")
    out("## 6. The plan's claims C1-C3 read on development data")
    out("")
    out("A prior for the protocol, not a verdict: C1 (an overlay improves the Sharpe ratio after costs and lag) "
        "counts benchmarks where the Sharpe interval is wholly above zero / wholly below; C2 (an overlay cuts the "
        "maximum drawdown by at least 5 points on every benchmark) counts benchmarks with a 5-point cut in the "
        "point estimate, and benchmarks where the drawdown-difference interval is wholly in the overlay's favour / "
        "against it; C3 is section 5. C4 (the correlation flag on 2018-2026) cannot be read here.")
    out("")
    out(md_table(claimtab, {}))
    out("")
    out("## Files")
    out("")
    out("`docs/results/allocation_v2_dev/`: `hmm_prob_spy_2017.csv` and `hmm_signal.json` (the walk-forward signal), "
        "`signals.csv` (every overlay state on the window), `strategy_returns.csv` (daily net returns of every "
        "benchmark, overlay and cost level), and one CSV per table above.")
    DOC.write_text("\n".join(L) + "\n", encoding="ascii")
    print("\n".join(L))
    print(f"\nwritten: {DOC.relative_to(REPO)}")


if __name__ == "__main__":
    main()
