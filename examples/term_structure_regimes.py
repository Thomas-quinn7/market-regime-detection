"""VIX term-structure regimes: an HMM on a state that may genuinely be discrete (development period).

Run from the repo root:

    python examples/term_structure_regimes.py

The slope is ``100 * log(VIX / VIX3M)``: negative when the curve slopes up (contango, the normal
state), positive when it inverts (backwardation, stress). Inversion looks closer to a true two-state
phenomenon than the volatility level does, so it is a fairer home for a two-state model.

1. Is it two-state? Information criteria for 1, 2 and 3 states, the two-state means and expected
   durations, and how often the curve is inverted.
2. Walk-forward HMM on the slope (quarterly refits, ordered by mean, so the high state is the
   inverted one), against the plain rule "the curve is inverted today" (slope > 0): how often each
   agrees and how often each flips.
3. Does the state help the volatility forecast? Same embargoed, log-scale walk-forward calibration
   as ``vol_forecast_vix.py``, all on the same days, with HAR + VIX as the reference:
   - F1 adds the slope itself (continuous);
   - F2 adds the inverted indicator, F3 the HMM probability;
   - F4 and F5 also let the regime change how the VIX maps to future vol (interaction with log VIX),
     F4 with the indicator, F5 with the HMM probability.
   The HMM only earns its place if F3 beats F2 or F5 beats F4.

S&P 500 data, 2005-2023, which the repo has used for development throughout; the slope starts when
VIX3M does, July 2006. Nothing here is a holdout.
"""
from __future__ import annotations

import warnings

import numpy as np
import pandas as pd

from regimes.data import load_index_returns, load_vol_indices
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
from regimes.model import fit_regimes

START, END = "2005-01-01", "2023-12-31"
H = 21


def _flips_per_year(on: pd.Series) -> float:
    return float(on.astype(int).diff().abs().sum() / (len(on) / 252))


def _verdict(lo: float, hi: float) -> str:
    return "better" if hi < 0 else "worse" if lo > 0 else "no difference"


def main() -> None:
    warnings.simplefilter("ignore")
    returns = load_index_returns(start=START, end=END)
    vol = load_vol_indices(("VIX", "VIX3M"), START, END)
    slope = (100 * np.log(vol["VIX"] / vol["VIX3M"])).dropna().rename("slope")
    slope = slope.loc[slope.index.intersection(returns.index)]
    print(f"slope = 100 log(VIX/VIX3M): {len(slope)} days, {slope.index.min().date()} -> "
          f"{slope.index.max().date()}; inverted (slope > 0) on {(slope > 0).mean():.1%} of days")

    print("\n1) is the term structure two-state? (full-sample fits, descriptive)")
    n = len(slope)
    ics = {}
    # One state is a single Gaussian: two parameters, closed-form log-likelihood.
    ll_one = -0.5 * n * (np.log(2 * np.pi * slope.var(ddof=0)) + 1)
    ics[1] = {"BIC": -2 * ll_one + 2 * np.log(n), "converged": True}
    fits = {}
    for k in (2, 3):
        f = fit_regimes(slope, n_regimes=k, order_by="mean")
        fits[k] = f
        ics[k] = {"BIC": float(f.result.bic), "converged": bool(f.result.mle_retvals.get("converged", True))}
    print(pd.DataFrame(ics).T.to_string())
    f2 = fits[2].result
    p = np.asarray(f2.regime_transition)[:, :, 0]
    order = fits[2].order
    means = np.asarray(f2.params[[f"const[{k}]" for k in range(2)]])[order]
    sds = np.sqrt(np.asarray(f2.params[[f"sigma2[{k}]" for k in range(2)]])[order])
    stay = np.diag(p)[order]
    print("two-state fit: state means " + ", ".join(f"{m:+.1f}" for m in means)
          + "; sds " + ", ".join(f"{s:.1f}" for s in sds)
          + "; expected durations (days) " + ", ".join(f"{1 / (1 - q):.0f}" for q in stay))

    print("\n2) walk-forward HMM on the slope vs the plain inverted rule", flush=True)
    wf = walk_forward_oos(slope, min_train=756, step=63, horizon=H, order_by="mean")
    p_inv = wf.high_vol_prob.rename("p_inverted")
    ind = (slope > 0).astype(float).rename("inverted")
    days = p_inv.index
    hmm_on = p_inv >= 0.5
    print(f"  out of sample {days.min().date()} -> {days.max().date()}, refits={wf.n_refits}, "
          f"skipped={wf.n_skipped}")
    print(f"  HMM high state on {hmm_on.mean():.1%} of days, inverted rule on {ind.loc[days].mean():.1%}; "
          f"they agree on {(hmm_on == ind.loc[days].astype(bool)).mean():.1%}")
    print(f"  flips per year: HMM {_flips_per_year(hmm_on):.1f}, inverted rule "
          f"{_flips_per_year(ind.loc[days]):.1f}")

    print("\n3) does the state help the volatility forecast?", flush=True)
    target = forward_vol(returns, H)
    log_har = np.log(har_features(returns).clip(lower=1e-3))
    log_vix = np.log(vol["VIX"] / np.sqrt(252)).rename("vix")
    base = log_har.join(log_vix)
    feature_sets = {
        "F0 HAR + VIX": base,
        "F1 + slope": base.join(slope),
        "F2 + inverted": base.join(ind),
        "F3 + HMM P": base.join(p_inv),
        "F4 + inverted x VIX": base.join(ind).assign(ix=lambda d: d["inverted"] * d["vix"]),
        "F5 + HMM P x VIX": base.join(p_inv).assign(px=lambda d: d["p_inverted"] * d["vix"]),
    }
    fc = {k: walk_forward_regression(target, X, horizon=H, step=63, min_rows=756,
                                     log_target=True).forecast for k, X in feature_sets.items()}
    joined = pd.concat({"y": target, **fc}, axis=1, sort=True).dropna()
    print(f"  scored days (common to every forecast): {len(joined)}, "
          f"{joined.index.min().date()} -> {joined.index.max().date()}")
    print(forecast_losses({k: joined[k] for k in fc}, joined["y"]).drop(columns="n").round(3).to_string())

    y = joined["y"].to_numpy()
    rows = []
    for name, ref in [("F1 + slope", "F0 HAR + VIX"), ("F2 + inverted", "F0 HAR + VIX"),
                      ("F3 + HMM P", "F0 HAR + VIX"), ("F4 + inverted x VIX", "F0 HAR + VIX"),
                      ("F5 + HMM P x VIX", "F0 HAR + VIX"), ("F3 + HMM P", "F2 + inverted"),
                      ("F5 + HMM P x VIX", "F4 + inverted x VIX")]:
        f, b = joined[name].to_numpy(), joined[ref].to_numpy()
        r_lo, r_hi = paired_rmse_diff_interval(f - y, b - y)
        q_lo, q_hi = paired_mean_diff_interval(qlike(f, y), qlike(b, y))
        rows.append({"forecast": name, "reference": ref,
                     "dRMSE 95%": f"{r_lo:+.3f} to {r_hi:+.3f}", "RMSE": _verdict(r_lo, r_hi),
                     "dQLIKE 95%": f"{q_lo:+.3f} to {q_hi:+.3f}", "QLIKE": _verdict(q_lo, q_hi)})
    print("\npaired block bootstrap (63-day blocks, 2,000 draws, seed 0):")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
