"""HARQ and SHAR at 1-day and 5-day horizons, S&P 500 development data only (2010-2023).

Run from the repo root (needs the Databento ES bars, see src/regimes/intraday.py):

    python examples/harq_short_horizon.py

A development check run on 2026-10-14 before the cross-index holdout was frozen. HARQ and SHAR are
built to help most at short horizons, while the holdout claims (docs/CROSS_INDEX_HOLDOUT_PROTOCOL.md)
are at 21 days, so this asks whether 1-day claims should be added. Same features, walk-forward
regression and paired block bootstrap as examples/better_vol_models.py, with the target replaced by
next-day RV (1 day) or the RMS of the next five days' RV (5 days). Only the HAR family is run.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from regimes.data import DATA_DIR, load_index_returns, load_vix
from regimes.forecast import (
    forecast_losses,
    har_rv,
    paired_mean_diff_interval,
    paired_rmse_diff_interval,
    qlike,
    walk_forward_regression,
)
from regimes.intraday import cached_daily_rv, market_data_dir


def main() -> None:
    warnings.simplefilter("ignore")
    dbn = next((market_data_dir() / "R1").glob("*/*.ohlcv-1m.dbn.zst"), None)
    rv = cached_daily_rv(dbn, DATA_DIR / "es_rv_5min.csv").loc[:"2023-12-31"]
    returns = load_index_returns(start="2000-01-01", end="2023-12-31")
    iv = load_vix("2000-01-01", "2023-12-31").reindex(returns.index).ffill(limit=5)
    rv = rv.reindex(returns.index).loc[rv.index.min():]

    log_hrv = np.log(har_rv(rv["rv"]).clip(lower=1e-3))
    log_iv = np.log(iv / np.sqrt(252)).rename("iv")
    q = (np.sqrt(rv["rq"]) / rv["rv"] ** 2).rename("q")
    signals = {
        "HAR-RV": log_hrv,
        "HAR-RV + IV": log_hrv.join(log_iv),
        "HARQ + IV": log_hrv.join(log_iv).assign(
            q_term=(log_hrv["rv_1d"] - log_hrv["rv_22d"]) * (q - 1)),
        "SHAR + IV": log_hrv.drop(columns="rv_1d").join(log_iv).assign(
            rv_neg=np.log(rv["rv_neg"].clip(lower=1e-3)), rv_pos=np.log(rv["rv_pos"].clip(lower=1e-3))),
    }
    common = pd.concat(signals.values(), axis=1).dropna().index

    for h in (1, 5):
        if h == 1:
            target = rv["rv"].shift(-1)
        else:
            target = np.sqrt((rv["rv"] ** 2).rolling(h, min_periods=h - 1).mean()).shift(-h)
        fc = {k: walk_forward_regression(target, X.reindex(common), horizon=h, step=63, min_rows=756,
                                         log_target=True).forecast for k, X in signals.items()}
        joined = pd.concat({"y": target, **fc}, axis=1, sort=True).dropna()
        print(f"\n##### {h}-day horizon: {len(joined)} scored days, "
              f"{joined.index.min().date()} -> {joined.index.max().date()}")
        print(forecast_losses({k: joined[k] for k in fc}, joined["y"]).drop(columns="n")
              .round(4).to_string())
        y = joined["y"].to_numpy()
        base = joined["HAR-RV + IV"].to_numpy()
        for name in ("HARQ + IV", "SHAR + IV"):
            f = joined[name].to_numpy()
            r_lo, r_hi = paired_rmse_diff_interval(f - y, base - y)
            q_lo, q_hi = paired_mean_diff_interval(qlike(f, y), qlike(base, y))
            print(f"{name} vs HAR-RV + IV: dRMSE {r_lo:+.4f} to {r_hi:+.4f}, "
                  f"dQLIKE {q_lo:+.4f} to {q_hi:+.4f}")


if __name__ == "__main__":
    main()
