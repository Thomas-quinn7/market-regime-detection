"""Does extra data make the regime model a better volatility forecaster?

Run from the repo root:

    python examples/vol_forecast_vix.py --period dev      # 2005-2023, the development period
    python examples/vol_forecast_vix.py --period early    # 1990-2004 holdout (docs/VIX_HOLDOUT_PROTOCOL.md)
    python examples/vol_forecast_vix.py --period recent   # 2024 onward holdout (same protocol)

Three outputs, all on the same days:

1. Raw signals. Correlations for everything, and RMSE / QLIKE for the signals already in vol units
   (the two HMM implied vols, EWMA, trailing vol, and the VIX, which is biased upwards by the variance
   risk premium and is shown raw only for reference).
2. Calibrated forecasts. Every signal set goes through the same embargoed walk-forward regression
   (``regimes.forecast``), fit in logs, with vol-unit inputs logged and probabilities left linear.
3. The frozen comparisons: paired block-bootstrap intervals for the RMSE and QLIKE differences.

Design note, made on the development period after a first run: calibration was first fit in levels
with one year of history, and blew up. The return/VIX HMM probability sat at exactly 1 through the
whole 2008-09 calibration year, so it was collinear with the intercept (coefficients near +/-480),
and a crisis-only year also mis-scaled the other HMM inputs. The fix, applied to every signal alike:
log-scale fits and three years of out-of-sample history before the first calibrated forecast.

Signals:
- return-only HMM: its high-vol probability, and its own implied vol forecast;
- joint return/VIX HMM (``regimes.vix_regimes``): implied vol forecast;
- baselines: EWMA vol, trailing 21-day vol, HAR-RV, the VIX, and HAR plus VIX;
- HAR plus VIX plus a regime probability, to ask whether the regime adds anything on top.

Periods. ``dev`` fits and scores 2005-2023, the development period of the rest of the repo. The two
holdouts were frozen in docs/VIX_HOLDOUT_PROTOCOL.md before their data was loaded: ``early`` fits and
scores 1990-2004 with no later data; ``recent`` fits on 2005 onward (training on the past is allowed)
and scores only days from 2024-01-01.
"""
from __future__ import annotations

import argparse
import warnings

import numpy as np
import pandas as pd

from regimes.data import load_index_returns, load_vix
from regimes.evaluate import ewma_vol, realised_vol, walk_forward_oos
from regimes.forecast import (
    forecast_losses,
    forward_vol,
    har_features,
    paired_mean_diff_interval,
    paired_rmse_diff_interval,
    qlike,
    walk_forward_regression,
)
from regimes.vix_regimes import walk_forward_vix_hmm

# period: (fit start, fit end passed to yfinance (exclusive), first scored day or None)
PERIODS = {
    "dev": ("2005-01-01", "2023-12-31", None),
    "early": ("1990-01-01", "2004-12-31", None),
    "recent": ("2005-01-01", "2026-10-13", "2024-01-01"),
}
H = 21

# The frozen comparisons: (forecast, reference). Primary metric RMSE, secondary QLIKE.
COMPARISONS = [
    ("VIX", "HAR"),
    ("HAR + VIX", "HAR"),
    ("HAR + HMM prob", "HAR"),
    ("HAR + VIX + HMM prob", "HAR + VIX"),
    ("HAR + VIX + VIX-HMM prob", "HAR + VIX"),
    ("HMM implied vol", "HAR"),
    ("VIX-HMM implied vol", "HAR"),
]


def _verdict(lo: float, hi: float) -> str:
    return "better" if hi < 0 else "worse" if lo > 0 else "no difference"


def main() -> None:
    warnings.simplefilter("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("--period", choices=sorted(PERIODS), default="dev")
    period = parser.parse_args().period
    start, end, score_from = PERIODS[period]

    returns = load_index_returns(start=start, end=end)
    vix = load_vix(start, end)
    common = returns.index.intersection(vix.index)
    returns, vix = returns.loc[common], vix.loc[common]
    print(f"period {period}: S&P 500 returns with VIX, {len(returns)} days, "
          f"{common.min().date()} -> {common.max().date()}")

    print("walk-forward: return-only HMM ...", flush=True)
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=H)
    print(f"  refits={wf.n_refits}, skipped={wf.n_skipped}")
    print("walk-forward: joint return/VIX HMM ...", flush=True)
    vx = walk_forward_vix_hmm(returns, vix, min_train=756, step=63, horizon=H)
    print(f"  refits={vx.n_refits}, skipped={vx.n_skipped}")
    print("  state vols (daily %), first and last refit:")
    print(vx.state_vol.iloc[[0, -1]].round(2).to_string())

    target = forward_vol(returns, H)
    har = har_features(returns)
    vix_daily = (vix / np.sqrt(252)).rename("vix")
    # Log inputs for the log-scale calibration; |r_t| can be zero, so it gets a small floor.
    log_har = np.log(har.clip(lower=1e-3))
    log_vix = np.log(vix_daily)

    raw = {
        "HMM high-vol probability": wf.high_vol_prob,
        "HMM implied vol": wf.implied_vol,
        "VIX-HMM implied vol": vx.implied_vol,
        "EWMA vol (0.94)": ewma_vol(returns),
        "trailing 21-day vol": realised_vol(returns, 21),
        "VIX": vix_daily,
    }
    feature_sets = {
        "HMM high-vol probability": raw["HMM high-vol probability"],
        "HMM implied vol": np.log(raw["HMM implied vol"]),
        "VIX-HMM implied vol": np.log(raw["VIX-HMM implied vol"]),
        "EWMA vol (0.94)": np.log(raw["EWMA vol (0.94)"]),
        "trailing 21-day vol": np.log(raw["trailing 21-day vol"]),
        "HAR": log_har,
        "VIX": log_vix,
        "HAR + VIX": log_har.join(log_vix),
        "HAR + HMM prob": log_har.join(wf.high_vol_prob),
        "HAR + VIX + HMM prob": log_har.join(log_vix).join(wf.high_vol_prob),
        "HAR + VIX + VIX-HMM prob": log_har.join(log_vix).join(vx.high_vol_prob),
    }
    fc = {name: walk_forward_regression(target, X, horizon=H, step=63, min_rows=756,
                                        log_target=True).forecast
          for name, X in feature_sets.items()}

    joined = pd.concat({"y": target, **fc}, axis=1, sort=True).dropna()
    if score_from is not None:
        joined = joined.loc[score_from:]
    days = joined.index
    print(f"\nscored days (common to every forecast): {len(days)}, "
          f"{days.min().date()} -> {days.max().date()}")

    print("\n1) raw signal vs next-month realised vol (no calibration), same days")
    rank = pd.DataFrame({
        name: {"pearson": s.loc[days].corr(target.loc[days]),
               "spearman": s.loc[days].corr(target.loc[days], method="spearman")}
        for name, s in raw.items()
    }).T
    vol_units = ["HMM implied vol", "VIX-HMM implied vol", "EWMA vol (0.94)", "trailing 21-day vol",
                 "VIX"]
    raw_loss = forecast_losses({k: raw[k].loc[days] for k in vol_units}, target.loc[days])
    rank = rank.join(raw_loss[["rmse", "qlike"]])
    print(rank.round(3).to_string())
    print("(VIX raw is in implied-vol terms, biased upwards by the variance risk premium.)")

    print("\n2) calibrated walk-forward forecasts, same days")
    table = forecast_losses({k: joined[k] for k in fc}, joined["y"])
    print(table.drop(columns="n").round(3).to_string())

    print("\n3) the frozen comparisons (paired block bootstrap, 63-day blocks, 2,000 draws, seed 0)")
    y = joined["y"].to_numpy()
    rows = []
    for name, ref in COMPARISONS:
        f, b = joined[name].to_numpy(), joined[ref].to_numpy()
        r_lo, r_hi = paired_rmse_diff_interval(f - y, b - y)
        q_lo, q_hi = paired_mean_diff_interval(qlike(f, y), qlike(b, y))
        rows.append({
            "forecast": name, "reference": ref,
            "dRMSE 95%": f"{r_lo:+.3f} to {r_hi:+.3f}", "RMSE verdict": _verdict(r_lo, r_hi),
            "dQLIKE 95%": f"{q_lo:+.3f} to {q_hi:+.3f}", "QLIKE verdict": _verdict(q_lo, q_hi),
        })
    print(pd.DataFrame(rows).to_string(index=False))
    print("\nAn interval wholly below zero means the forecast beats its reference; wholly above, worse.")


if __name__ == "__main__":
    main()
