"""Markov-switching GARCH and credit spreads as volatility forecasters. Development on the S&P 500.

Run from the repo root:

    python -u examples/msgarch_credit.py                        # the claimed MS-GARCH variant
    python -u examples/msgarch_credit.py --all-variants         # every development variant
    python -u examples/msgarch_credit.py --only hmm             # one walk-forward, cached, no scoring

Each walk-forward (``hmm``, ``garch`` or an MS-GARCH variant's name) is cached to
``data/checkpoints/msgarch_credit/`` once it finishes, so a run killed part-way keeps what it had, and
``--only`` lets separate processes compute them in parallel before one run scores everything.

The cross-index holdout (docs/CROSS_INDEX_HOLDOUT_PROTOCOL.md) found nothing that beats HAR + implied
vol. Two ideas were left over, and both are developed here on S&P 500 data and will be confirmed on a
fresh holdout of other assets with daily data only, so everything below uses daily returns:

- MS-GARCH (``regimes.msgarch``): two regimes, each with its own GJR-GARCH variance, so volatility
  moves continuously inside a regime instead of sitting on two levels as in the two-state HMM;
- credit: Moody's Baa yield minus the 10-year Treasury (FRED ``BAA10Y``), lagged one business day
  because FRED dates the H.15 data by observation and publishes it the next day.

Models, each calibrated by the same embargoed log-scale walk-forward regression on the same rows and
scored against realised vol over the next 21 trading days from daily returns:

- HAR from daily returns, HAR + IV (the asset's implied-vol index), HAR + credit, HAR + IV + credit;
- GJR-GARCH(1,1), the two-state HMM implied vol, and MS-GARCH;
- HAR + IV + MS-GARCH (its forecast as an input) and HAR + IV + MS-GARCH prob (its filtered
  probability of the turbulent regime, the regime as conditioning information).

``evaluate_asset`` is written so the holdout can run it unchanged on each asset.
"""
from __future__ import annotations

import argparse
import re
import warnings
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd

from regimes.data import DATA_DIR, load_fred_series, load_index_returns, load_vix
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
from regimes.garch import walk_forward_gjr
from regimes.msgarch import walk_forward_msgarch

H = 21
RETURNS_FROM = "2000-01-01"
DEV_END = "2023-12-31"
CACHE_DIR = DATA_DIR / "checkpoints" / "msgarch_credit"

# MS-GARCH variants: name -> (innovations, lowest allowed stay probability). ``MSGARCH`` is the one the
# claims refer to, chosen on the S&P 500 development run (docs/MSGARCH_CREDIT_HOLDOUT_PROTOCOL.md):
# Student-t errors, no lower bound on staying in a regime beyond the optimiser's 0.001.
MSGARCH = {"MS-GARCH": ("t", 0.001)}
DEV_VARIANTS = {
    "MS-GARCH": ("t", 0.001),
    "MS-GARCH normal": ("normal", 0.001),
    "MS-GARCH t, stay >= 0.5": ("t", 0.5),
}

# Candidate claims (forecast, reference, expected). ``{m}`` is an MS-GARCH variant's name.
MS_CLAIMS = [
    ("M1", "{m}", "GJR-GARCH", "better"),
    ("M2", "HAR + IV + {m}", "HAR + IV", "better"),
    ("M3", "{m}", "Two-state HMM implied vol", "better"),
    ("M4", "HAR + IV + {m} prob", "HAR + IV", "better"),
    ("M5", "{m}", "HAR + IV", "better"),
]
OTHER_CLAIMS = [
    ("C1", "HAR + IV + credit", "HAR + IV", "not better"),
    ("C2", "HAR + credit", "HAR", "better"),
    ("R1", "HAR + IV", "HAR", "better"),
    ("R2", "GJR-GARCH", "HAR + IV", "not better"),
]


def _verdict(lo: float, hi: float) -> str:
    return "better" if hi < 0 else "worse" if lo > 0 else "no difference"


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")


def _walk_forward(model: str, name: str, end: str, returns: pd.Series, variants: dict,
                  cache_dir: Path | None) -> SimpleNamespace:
    """One walk-forward (``hmm``, ``garch`` or an MS-GARCH variant), loaded from the cache if it is
    there. The cache key is the asset, the model, the end date and the number of return days."""
    path = None
    if cache_dir is not None:
        path = cache_dir / f"{_slug(name)}__{_slug(model)}__{end}__{len(returns)}.csv"
        if path.exists():
            df = pd.read_csv(path, index_col=0, parse_dates=True)
            params_path = path.with_suffix(".params.csv")
            params = pd.read_csv(params_path, index_col=0, parse_dates=True)                 if params_path.exists() else None
            print(f"  {model}: loaded from {path.name}", flush=True)
            return SimpleNamespace(implied_vol=df["implied_vol"], high_vol_prob=df.get("high_vol_prob"),
                                   params=params, n_refits=None if params is None else len(params))
    if model == "hmm":
        wf = walk_forward_oos(returns, min_train=756, step=63, horizon=H)
        out = SimpleNamespace(implied_vol=wf.implied_vol, high_vol_prob=wf.high_vol_prob, params=None,
                              n_refits=wf.n_refits)
    elif model == "garch":
        wf = walk_forward_gjr(returns, min_train=756, step=63, horizon=H)
        out = SimpleNamespace(implied_vol=wf.implied_vol, high_vol_prob=None, params=wf.params,
                              n_refits=wf.n_refits)
    else:
        dist, min_stay = variants[model]
        wf = walk_forward_msgarch(returns, 2, dist, min_train=756, step=63, horizon=H,
                                  min_stay=min_stay)
        out = SimpleNamespace(implied_vol=wf.implied_vol, high_vol_prob=wf.high_vol_prob,
                              params=wf.params, n_refits=wf.n_refits)
        last = wf.params.iloc[-1]
        print(f"  {model}: last fit p00 {last['p00']:.4f}, p11 {last['p11']:.4f}, "
              f"nu {last['nu0']:.1f} / {last['nu1']:.1f}, loglik {last['loglik']:.1f}", flush=True)
    print(f"  {model}: {out.n_refits} refits", flush=True)
    if path is not None:
        path.parent.mkdir(parents=True, exist_ok=True)
        cols = {"implied_vol": out.implied_vol}
        if out.high_vol_prob is not None:
            cols["high_vol_prob"] = out.high_vol_prob
        pd.DataFrame(cols).to_csv(path)
        if out.params is not None:
            out.params.to_csv(path.with_suffix(".params.csv"))
    return out


def evaluate_asset(name: str, returns: pd.Series, iv: pd.Series, credit: pd.Series, *, end: str,
                   variants: dict[str, tuple[str, float]] = MSGARCH,
                   cache_dir: Path | None = CACHE_DIR, only: list[str] | None = None) -> dict | None:
    """Run every model and claim for one asset.

    ``returns`` are daily log returns in percent from ``RETURNS_FROM`` and set the calendar; ``iv`` is
    the asset's implied-vol index (annualised percent) and ``credit`` the ``BAA10Y`` spread, both by
    observation date. IV closes after the asset (CBOE vol indices close at 4:15pm ET), so the day-t
    value is usable at t; credit is lagged one business day.

    ``only`` computes (and caches) just those walk-forwards and returns None without scoring.
    """
    returns = returns.loc[:end]
    days = returns.index
    iv = iv.reindex(days).ffill(limit=5)
    credit = credit.reindex(days).ffill(limit=5).shift(1)
    print(f"\n##### {name}: returns {days.min().date()} -> {days.max().date()} ({len(days)} days); "
          f"IV from {iv.first_valid_index().date()}, credit from {credit.first_valid_index().date()}")

    print("walk-forward: two-state HMM, GJR-GARCH, MS-GARCH ...", flush=True)
    if only is not None:
        for model in only:
            _walk_forward(model, name, end, returns, variants, cache_dir)
        return None
    hmm = _walk_forward("hmm", name, end, returns, variants, cache_dir)
    garch = _walk_forward("garch", name, end, returns, variants, cache_dir)
    ms = {v: _walk_forward(v, name, end, returns, variants, cache_dir) for v in variants}

    target = forward_vol(returns, H)
    log_har = np.log(har_features(returns).clip(lower=1e-3))
    log_iv = np.log(iv / np.sqrt(252)).rename("iv")
    log_credit = np.log(credit).rename("credit")
    signals = {
        "HAR": log_har,
        "HAR + IV": log_har.join(log_iv),
        "HAR + credit": log_har.join(log_credit),
        "HAR + IV + credit": log_har.join(log_iv).join(log_credit),
        "GJR-GARCH": np.log(garch.implied_vol).rename("garch"),
        "Two-state HMM implied vol": np.log(hmm.implied_vol).rename("hmm_iv"),
    }
    for v, wf in ms.items():
        log_ms = np.log(wf.implied_vol).rename("ms")
        signals[v] = log_ms
        signals[f"HAR + IV + {v}"] = log_har.join(log_iv).join(log_ms)
        signals[f"HAR + IV + {v} prob"] = log_har.join(log_iv).join(wf.high_vol_prob.rename("p"))
    common = pd.concat(signals.values(), axis=1).dropna().index
    fc = {k: walk_forward_regression(target, X.reindex(common), horizon=H, step=63, min_rows=756,
                                     log_target=True).forecast for k, X in signals.items()}
    joined = pd.concat({"y": target, **fc}, axis=1, sort=True).dropna()
    print(f"scored days: {len(joined)}, {joined.index.min().date()} -> {joined.index.max().date()}")
    print(forecast_losses({k: joined[k] for k in fc}, joined["y"]).drop(columns="n")
          .round(3).to_string())

    claims = [(c, f.format(m=v), r.format(m=v), e) for v in variants for c, f, r, e in MS_CLAIMS]
    claims += OTHER_CLAIMS
    y = joined["y"].to_numpy()
    rows = []
    for cid, f_name, ref, expected in claims:
        f, b = joined[f_name].to_numpy(), joined[ref].to_numpy()
        r_lo, r_hi = paired_rmse_diff_interval(f - y, b - y)
        q_lo, q_hi = paired_mean_diff_interval(qlike(f, y), qlike(b, y))
        rows.append({"claim": cid, "forecast": f_name, "reference": ref, "expected": expected,
                     "dRMSE 95%": f"{r_lo:+.3f} to {r_hi:+.3f}", "RMSE": _verdict(r_lo, r_hi),
                     "dQLIKE 95%": f"{q_lo:+.3f} to {q_hi:+.3f}", "QLIKE": _verdict(q_lo, q_hi)})
    table = pd.DataFrame(rows)
    print("paired block bootstrap (63-day blocks, 2,000 draws, seed 0):")
    print(table.to_string(index=False))
    return {"n_days": len(joined), "claims": table, "msgarch_params": {v: wf.params for v, wf in ms.items()}}


def main() -> None:
    warnings.simplefilter("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("--all-variants", action="store_true",
                        help="also run the development MS-GARCH variants")
    parser.add_argument("--variant", action="append", choices=sorted(DEV_VARIANTS),
                        help="score these MS-GARCH variants (repeatable)")
    parser.add_argument("--only", action="append", choices=["hmm", "garch", *sorted(DEV_VARIANTS)],
                        help="compute and cache just this walk-forward, no scoring (repeatable)")
    args = parser.parse_args()
    variants = DEV_VARIANTS if args.all_variants else         {v: DEV_VARIANTS[v] for v in args.variant} if args.variant else MSGARCH
    returns = load_index_returns(start=RETURNS_FROM, end=DEV_END)
    vix = load_vix(RETURNS_FROM, DEV_END)
    credit = load_fred_series("BAA10Y").loc[RETURNS_FROM:DEV_END]
    res = evaluate_asset("S&P 500 (development)", returns, vix, credit, end=DEV_END,
                         variants={**variants, **{v: DEV_VARIANTS[v] for v in args.only or []
                                                  if v in DEV_VARIANTS}},
                         only=args.only)
    if res is None:
        return
    for v, params in res["msgarch_params"].items():
        print(f"\n{v}: fitted parameters, every 8th refit")
        print(params.iloc[::8].round(4).to_string())


if __name__ == "__main__":
    main()
