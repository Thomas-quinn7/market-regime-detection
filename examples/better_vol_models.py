"""Better volatility models than HAR + implied vol? Development on the S&P 500, 2010-2023.

Run from the repo root (needs the Databento ES bars, see src/regimes/intraday.py):

    python examples/better_vol_models.py

The models and claims are the ones fixed in docs/CROSS_INDEX_HOLDOUT_PROTOCOL.md, where the
holdout on the Nasdaq-100, the Dow and the Russell 2000 will run this same ``evaluate_index``:

- HAR from daily returns, HAR-RV from five-minute session RV, and the index's implied vol (IV);
- HARQ + IV: the weight on yesterday's deviation from the monthly level shrinks when realised
  quarticity says yesterday's RV was measured imprecisely (Bollerslev, Patton and Quaedvlieg 2016);
- SHAR + IV: yesterday's RV split into downside and upside semivariance (Patton and Sheppard 2015);
- GJR-GARCH(1,1) and MSM (Calvet and Fisher 2004), walk-forward on daily index returns;
- the two-state HMM, as everywhere in this repo;
- a combination, the equal-weight average of HAR-RV + IV, GJR-GARCH and MSM.

Everything is calibrated by the same embargoed log-scale walk-forward regression, on the same rows,
and scored on the same days against next-21-day session RV.

Development choices, made on S&P 500 data only:
- MSM components: the smallest k whose log-likelihood on S&P 500 returns 2000-2009 (before any scored
  day) is within 2 points of the best for k = 1 to 8. That is k = 4 (k = 4 to 8 all lie within 1.3
  points). All k have the same four parameters.
- MSM fits use twelve starting points with L-BFGS-B, after a single-start Nelder-Mead fit stalled.
- HARQ uses the quarticity ratio ``q = sqrt(RQ) / RV^2`` (about 1 when intraday returns are
  Gaussian) and the term ``(log rv_1d - log rv_22d) * (q - 1)``.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from regimes.data import DATA_DIR, load_index_returns, load_vix
from regimes.evaluate import walk_forward_oos
from regimes.forecast import (
    forecast_losses,
    forward_rv,
    har_features,
    har_rv,
    paired_mean_diff_interval,
    paired_rmse_diff_interval,
    qlike,
    walk_forward_regression,
)
from regimes.garch import walk_forward_gjr
from regimes.intraday import cached_daily_rv, market_data_dir
from regimes.msm import walk_forward_msm

H = 21
MSM_K = 4
RETURNS_FROM = "2000-01-01"

CLAIMS = [
    ("P1", "HARQ + IV", "HAR-RV + IV", "better"),
    ("P2", "SHAR + IV", "HAR-RV + IV", "better"),
    ("P3", "HAR-RV + IV + MSM", "HAR-RV + IV", "better"),
    ("P4", "Combination", "HAR-RV + IV", "better"),
    ("P5", "MSM", "Two-state HMM implied vol", "better"),
    ("R1", "HAR-RV + IV", "HAR-RV", "better"),
    ("R2", "HAR-RV", "HAR", "better"),
    ("R3", "HAR-RV + IV + HMM prob", "HAR-RV + IV", "not better"),
    ("R4", "GJR-GARCH", "HAR-RV + IV", "not better"),
]


def _verdict(lo: float, hi: float) -> str:
    return "better" if hi < 0 else "worse" if lo > 0 else "no difference"


def evaluate_index(name: str, rv: pd.DataFrame, returns: pd.Series, iv: pd.Series, *,
                   end: str) -> dict:
    """Run every model and claim for one index. ``rv`` is the daily session-RV frame
    (``regimes.intraday.daily_realised_vol``), ``returns`` daily index log returns in percent from
    ``RETURNS_FROM``, ``iv`` the implied-vol index in annualised percent."""
    returns = returns.loc[:end]
    days = returns.index
    rv = rv.reindex(days).loc[rv.index.min():end]
    iv = iv.reindex(days).ffill(limit=5)
    print(f"\n##### {name}: returns {days.min().date()} -> {days.max().date()}; session RV "
          f"{rv['rv'].notna().sum()} days from {rv.index.min().date()}, {rv['rv'].isna().sum()} missing")

    print("walk-forward: two-state HMM, GJR-GARCH, MSM ...", flush=True)
    hmm = walk_forward_oos(returns, min_train=756, step=63, horizon=H)
    garch = walk_forward_gjr(returns, min_train=756, step=63, horizon=H)
    msm = walk_forward_msm(returns, MSM_K, min_train=756, step=63, horizon=H)
    print(f"  refits: HMM {hmm.n_refits}, GARCH {garch.n_refits}, MSM {msm.n_refits}")
    print("  last MSM fit: " + ", ".join(f"{k} {v:.3f}" for k, v in msm.params.iloc[-1].items()))

    target = forward_rv(rv["rv"], H)
    log_har = np.log(har_features(returns).clip(lower=1e-3))
    hrv = har_rv(rv["rv"])
    log_hrv = np.log(hrv.clip(lower=1e-3))
    log_iv = np.log(iv / np.sqrt(252)).rename("iv")
    q = (np.sqrt(rv["rq"]) / rv["rv"] ** 2).rename("q")
    harq = log_hrv.join(log_iv).assign(
        q_term=(log_hrv["rv_1d"] - log_hrv["rv_22d"]) * (q - 1))
    shar = log_hrv.drop(columns="rv_1d").join(log_iv).assign(
        rv_neg=np.log(rv["rv_neg"].clip(lower=1e-3)), rv_pos=np.log(rv["rv_pos"].clip(lower=1e-3)))
    log_msm = np.log(msm.implied_vol).rename("msm")
    signals = {
        "HAR": log_har,
        "HAR-RV": log_hrv,
        "HAR-RV + IV": log_hrv.join(log_iv),
        "HARQ + IV": harq,
        "SHAR + IV": shar,
        "GJR-GARCH": np.log(garch.implied_vol).rename("garch"),
        "MSM": log_msm,
        "Two-state HMM implied vol": np.log(hmm.implied_vol).rename("hmm_iv"),
        "HAR-RV + IV + MSM": log_hrv.join(log_iv).join(log_msm),
        "HAR-RV + IV + HMM prob": log_hrv.join(log_iv).join(hmm.high_vol_prob.rename("p")),
    }
    common = pd.concat(signals.values(), axis=1).dropna().index
    fc = {k: walk_forward_regression(target, X.reindex(common), horizon=H, step=63, min_rows=756,
                                     log_target=True).forecast for k, X in signals.items()}
    fc["Combination"] = (fc["HAR-RV + IV"] + fc["GJR-GARCH"] + fc["MSM"]) / 3
    joined = pd.concat({"y": target, **fc}, axis=1, sort=True).dropna()
    print(f"scored days: {len(joined)}, {joined.index.min().date()} -> {joined.index.max().date()}")
    print(forecast_losses({k: joined[k] for k in fc}, joined["y"]).drop(columns="n")
          .round(3).to_string())

    y = joined["y"].to_numpy()
    rows = []
    for cid, f_name, ref, claim in CLAIMS:
        f, b = joined[f_name].to_numpy(), joined[ref].to_numpy()
        r_lo, r_hi = paired_rmse_diff_interval(f - y, b - y)
        q_lo, q_hi = paired_mean_diff_interval(qlike(f, y), qlike(b, y))
        rows.append({"claim": cid, "forecast": f_name, "reference": ref, "expected": claim,
                     "dRMSE 95%": f"{r_lo:+.3f} to {r_hi:+.3f}", "RMSE": _verdict(r_lo, r_hi),
                     "dQLIKE 95%": f"{q_lo:+.3f} to {q_hi:+.3f}", "QLIKE": _verdict(q_lo, q_hi)})
    table = pd.DataFrame(rows)
    print("paired block bootstrap (63-day blocks, 2,000 draws, seed 0):")
    print(table.to_string(index=False))
    return {"n_days": len(joined), "claims": table}


def main() -> None:
    warnings.simplefilter("ignore")
    dbn = next((market_data_dir() / "R1").glob("*/*.ohlcv-1m.dbn.zst"), None)
    rv = cached_daily_rv(dbn, DATA_DIR / "es_rv_5min.csv").loc[:"2023-12-31"]
    returns = load_index_returns(start=RETURNS_FROM, end="2023-12-31")
    vix = load_vix(RETURNS_FROM, "2023-12-31")
    evaluate_index("S&P 500 (development)", rv, returns, vix, end="2023-12-31")


if __name__ == "__main__":
    main()
