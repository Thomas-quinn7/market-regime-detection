"""Intraday realised volatility: does a cleaner measurement of volatility rescue the regime model?

Run from the repo root (needs the Databento ES file, see src/regimes/intraday.py):

    python examples/intraday_rv.py

Every earlier result in this repo measured a day's volatility from one close-to-close return, which
is a very noisy reading. Here the S&P 500 day is measured instead by five-minute realised vol from
ES futures (09:30-16:00 New York, ``regimes.intraday``), which is what HAR-RV (Corsi 2009) was built
on. Two questions:

1. Does intraday data improve the volatility forecast itself (HAR-RV against the daily-return HAR)?
2. Does the regime model do better when it sees the cleaner data? A two-state HMM is fit walk-forward
   on log daily RV (``HMM-RV``, ordered by mean, so the high state is high RV), and its filtered
   probability is scored the same way as the return HMM's.

Two targets, both next-21-day volatility in daily percent: ``rv`` (the regular-session RV, the
cleaner target and the primary one) and ``cc`` (close-to-close, the target of every earlier script).
Regular-session RV leaves out the overnight move, about 40% of close-to-close variance in 2010-2023.

Every forecast is calibrated with the same embargoed log-scale walk-forward regression as
``vol_forecast_vix.py`` and every feature set is restricted to the same rows, so all forecasts train
on identical days and are scored on identical days.

The comparisons, fixed before the first run (forecast against reference; RMSE primary, QLIKE
secondary; paired block bootstrap):

    C1 HAR-RV                          vs HAR                  does intraday data help at all?
    C2 HAR-RV + VIX                    vs HAR + VIX            ... and with the VIX?
    C3 HMM-RV prob                     vs HMM prob             does the regime improve on clean data?
    C4 HMM-RV prob                     vs trailing 22-day RV   is the regime better than trailing RV?
    C5 HMM-RV prob                     vs HAR-RV               is the regime a usable level forecast?
    C6 HAR-RV + VIX + HMM-RV prob      vs HAR-RV + VIX         does it add to the best baseline?
    C7 HAR-RV + VIX + HMM prob         vs HAR-RV + VIX         does the return HMM add to it?
    C8 regime-switching HAR-RV + VIX   vs HAR-RV + VIX         HMM-RV prob times each HAR-RV term

Data: S&P 500 (Yahoo) and VIX 2005-2023, ES from June 2010. This is the repo's development period;
nothing here is a holdout. The confirmation is on NQ, YM and RTY (downloaded, unopened) under a
protocol still to be written. Databento flags 32 dates as degraded; the five S&P trading days in
2014 with no ES bars are left missing, and degraded days that do have bars are kept.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from regimes.data import DATA_DIR, load_index_returns, load_vix
from regimes.evaluate import walk_forward_oos
from regimes.forecast import (
    forecast_losses,
    forward_vol,
    har_features,
    paired_mean_diff_interval,
    paired_rmse_diff_interval,
    qlike,
    walk_forward_regression,
)
from regimes.intraday import daily_realised_vol, load_session_bars, market_data_dir

START, END = "2005-01-01", "2023-12-31"
H = 21
RV_CACHE = DATA_DIR / "es_rv_5min.csv"

COMPARISONS = [
    ("HAR-RV", "HAR"),
    ("HAR-RV + VIX", "HAR + VIX"),
    ("HMM-RV prob", "HMM prob"),
    ("HMM-RV prob", "trailing 22-day RV"),
    ("HMM-RV prob", "HAR-RV"),
    ("HAR-RV + VIX + HMM-RV prob", "HAR-RV + VIX"),
    ("HAR-RV + VIX + HMM prob", "HAR-RV + VIX"),
    ("regime-switching HAR-RV + VIX", "HAR-RV + VIX"),
]


def es_daily_rv() -> pd.DataFrame:
    """Daily ES five-minute RV, built once from the R1 download and cached as a derived daily file."""
    if not RV_CACHE.exists():
        path = next((market_data_dir() / "R1").glob("*/*.ohlcv-1m.dbn.zst"))
        daily_realised_vol(load_session_bars(path)).to_csv(RV_CACHE)
    return pd.read_csv(RV_CACHE, index_col=0, parse_dates=True)


def har_rv(rv: pd.Series) -> pd.DataFrame:
    """HAR-RV inputs from daily RV, tolerating the odd missing day inside the 5- and 22-day windows."""
    v = rv ** 2
    return pd.DataFrame({
        "rv_1d": rv,
        "rv_5d": np.sqrt(v.rolling(5, min_periods=4).mean()),
        "rv_22d": np.sqrt(v.rolling(22, min_periods=18).mean()),
    })


def _verdict(lo: float, hi: float) -> str:
    return "better" if hi < 0 else "worse" if lo > 0 else "no difference"


def main() -> None:
    warnings.simplefilter("ignore")
    returns = load_index_returns(start=START, end=END)
    vix = load_vix(START, END)
    days = returns.index.intersection(vix.index)
    returns, vix = returns.loc[days], vix.loc[days]
    rv = es_daily_rv()["rv"].reindex(days).loc["2010-06-07":]
    print(f"S&P 500 with VIX: {len(days)} days; ES regular-session RV: {rv.notna().sum()} days, "
          f"{rv.index.min().date()} -> {rv.index.max().date()}, {rv.isna().sum()} missing")

    print("walk-forward: return HMM (from 2005) ...", flush=True)
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=H)
    print("walk-forward: HMM on log RV (from 2010-06) ...", flush=True)
    log_rv = np.log(rv.dropna()).rename("log_rv")
    wf_rv = walk_forward_oos(log_rv, min_train=756, step=63, horizon=H, order_by="mean")
    p_rv = wf_rv.high_vol_prob.rename("p_rv")
    print(f"  return HMM refits={wf.n_refits}; HMM-RV refits={wf_rv.n_refits}, "
          f"skipped={wf_rv.n_skipped}, out of sample from {p_rv.index.min().date()}")

    on = p_rv >= 0.5
    flips = on.astype(int).diff().abs().sum() / (len(on) / 252)
    high_rv, low_rv = rv.reindex(on.index)[on], rv.reindex(on.index)[~on]
    print(f"  HMM-RV high state on {on.mean():.1%} of days, {flips:.1f} flips a year; median RV "
          f"{high_rv.median():.2f} in the high state, {low_rv.median():.2f} in the low (daily %)")

    targets = {"rv": np.sqrt((rv ** 2).rolling(H, min_periods=18).mean().shift(-H)),
               "cc": forward_vol(returns, H)}
    log_har = np.log(har_features(returns).clip(lower=1e-3))
    log_hrv = np.log(har_rv(rv).clip(lower=1e-3))
    log_vix = np.log(vix / np.sqrt(252)).rename("vix")
    p = wf.high_vol_prob.rename("p_ret")
    rs = log_hrv.join(log_vix).join(p_rv)
    for c in log_hrv:
        rs[f"p_x_{c}"] = rs["p_rv"] * rs[c]
    feature_sets = {
        "HAR": log_har,
        "HAR + VIX": log_har.join(log_vix),
        "trailing 22-day RV": log_hrv[["rv_22d"]],
        "HAR-RV": log_hrv,
        "HAR-RV + VIX": log_hrv.join(log_vix),
        "HMM prob": p,
        "HMM implied vol": np.log(wf.implied_vol).rename("hmm_iv"),
        "HMM-RV prob": p_rv,
        "HAR-RV + VIX + HMM-RV prob": log_hrv.join(log_vix).join(p_rv),
        "HAR-RV + VIX + HMM prob": log_hrv.join(log_vix).join(p),
        "regime-switching HAR-RV + VIX": rs,
    }
    # One set of rows for every forecast: the days on which every input exists.
    common = pd.concat(feature_sets.values(), axis=1).dropna().index
    print(f"calibration rows common to every feature set: {len(common)}, "
          f"{common.min().date()} -> {common.max().date()}")

    for tname, target in targets.items():
        fc = {name: walk_forward_regression(target, X.reindex(common), horizon=H, step=63,
                                            min_rows=756, log_target=True).forecast
              for name, X in feature_sets.items()}
        joined = pd.concat({"y": target, **fc}, axis=1, sort=True).dropna()
        print(f"\n=== target: next-{H}-day {'regular-session RV' if tname == 'rv' else 'close-to-close vol'}"
              f", {len(joined)} scored days, {joined.index.min().date()} -> {joined.index.max().date()}")
        print(forecast_losses({k: joined[k] for k in fc}, joined["y"]).drop(columns="n")
              .round(3).to_string())
        y = joined["y"].to_numpy()
        rows = []
        for i, (name, ref) in enumerate(COMPARISONS, 1):
            f, b = joined[name].to_numpy(), joined[ref].to_numpy()
            r_lo, r_hi = paired_rmse_diff_interval(f - y, b - y)
            q_lo, q_hi = paired_mean_diff_interval(qlike(f, y), qlike(b, y))
            rows.append({"": f"C{i}", "forecast": name, "reference": ref,
                         "dRMSE 95%": f"{r_lo:+.3f} to {r_hi:+.3f}", "RMSE": _verdict(r_lo, r_hi),
                         "dQLIKE 95%": f"{q_lo:+.3f} to {q_hi:+.3f}", "QLIKE": _verdict(q_lo, q_hi)})
        print("paired block bootstrap (63-day blocks, 2,000 draws, seed 0):")
        print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
