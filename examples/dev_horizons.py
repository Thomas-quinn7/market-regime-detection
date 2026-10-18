"""Development-only horizons 5 to 126 trading days (and 252, descriptive) on the S&P 500 to 2023-12-31.

development data only (S&P 500, 2005-2023), no holdout, not a claim.

Writes ``docs/DEV_HORIZONS_2026-10.md``. Stage S8 (a) of the reopen scope. The design is the S4a one
(``examples/dev_continuations.py``): target = realised vol over the next h days; expanding OLS on log
HAR inputs, log target, refit every 63 rows after 756, embargo h; paired circular block bootstrap with
block = max(63, h), 2,000 draws, seed 0; RMSE and QLIKE; a pure-noise regressor (standard normal,
seed 0) beside the HMM probability at every horizon. Two changes from S4a, both stated in the output:

- the implied vol matches the horizon: VIX9D at 5 and 10 days, VIX at 21 and 63, VIX6M at 126, with
  the VIX shown beside it at every horizon;
- every feature set at a horizon is fitted on the same rows (the dates where all its horizon's inputs
  exist), so no set trains on more history than another (desk finding 6, the own-row calibration of
  the frozen VIX script). The 21- and 63-day rows therefore differ slightly from S4a's.

h = 252 is a descriptive line only: losses, no interval and no verdict (no cached one-year implied
vol, about 12 non-overlapping windows). Data from the committed caches (a download attempt raises)::

    python -u examples/dev_horizons.py [--n-boot 2000] [--out docs/DEV_HORIZONS_2026-10.md]
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
import types
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

from regimes.data import load_index_returns, load_vol_indices  # noqa: E402
from regimes.evaluate import walk_forward_oos  # noqa: E402
from regimes.forecast import forward_vol, har_features, qlike, walk_forward_regression  # noqa: E402
from regimes.posthoc import paired_interval  # noqa: E402

from posthoc_stats import git_head, md_table, verdict  # noqa: E402

START, END = "2005-01-01", "2023-12-31"   # development period; rule 3 of the reopen scope
CLASS = "development data only (S&P 500, 2005-2023), no holdout, not a claim"
HORIZONS = (5, 10, 21, 63, 126)
DESCRIPTIVE = (252,)
MATCHING_IV = {5: "VIX9D", 10: "VIX9D", 21: "VIX", 63: "VIX", 126: "VIX6M", 252: "VIX"}


def block_network() -> None:
    def no_network(*a, **k):
        raise RuntimeError("dev_horizons.py reads only the data caches; a download was attempted")
    sys.modules["yfinance"] = types.SimpleNamespace(download=no_network)


def load() -> tuple[pd.Series, pd.DataFrame]:
    returns = load_index_returns(start=START, end=END)
    ivs = load_vol_indices(("VIX", "VIX9D", "VIX6M"), START, END)
    common = returns.index.intersection(ivs.index[ivs["VIX"].notna()])
    return returns.loc[common], ivs.reindex(common)


def feature_sets(returns: pd.Series, ivs: pd.DataFrame, h: int, prob: pd.Series, noise: pd.Series) -> dict[str, pd.DataFrame]:
    """Every feature set at horizon ``h``, each cut to the rows where all of this horizon's inputs exist."""
    iv_name = MATCHING_IV[h]
    log_har = np.log(har_features(returns).clip(lower=1e-3))
    log_iv = np.log(ivs[iv_name] / np.sqrt(252)).rename("iv")
    log_vix = np.log(ivs["VIX"] / np.sqrt(252)).rename("vix")
    sets = {"HAR": log_har,
            f"HAR + {iv_name}": log_har.join(log_iv),
            f"HAR + {iv_name} + HMM prob": log_har.join(log_iv).join(prob),
            f"HAR + {iv_name} + noise": log_har.join(log_iv).join(noise.rename("noise"))}
    if iv_name != "VIX":
        sets["HAR + VIX"] = log_har.join(log_vix)
        sets["HAR + VIX + HMM prob"] = log_har.join(log_vix).join(prob)
    everything = log_har.join(log_iv).join(log_vix).join(prob).dropna()
    return {k: v.loc[everything.index] for k, v in sets.items()}


def comparisons(h: int) -> list[tuple[str, str]]:
    iv = MATCHING_IV[h]
    out = [(f"HAR + {iv}", "HAR"), (f"HAR + {iv} + HMM prob", f"HAR + {iv}"), (f"HAR + {iv} + noise", f"HAR + {iv}")]
    if iv != "VIX":
        out += [("HAR + VIX", "HAR"), ("HAR + VIX + HMM prob", "HAR + VIX"), (f"HAR + {iv}", "HAR + VIX")]
    return out


def scored_table(returns: pd.Series, ivs: pd.DataFrame, h: int, noise: pd.Series) -> pd.DataFrame:
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=h)
    target = forward_vol(returns, h)
    sets = feature_sets(returns, ivs, h, wf.high_vol_prob, noise)
    fc = {name: walk_forward_regression(target, X, horizon=h, step=63, min_rows=756, log_target=True).forecast
          for name, X in sets.items()}
    joined = pd.concat({"target": target, **fc}, axis=1, sort=True).dropna()
    joined.attrs["n_refits"] = wf.n_refits
    joined.attrs["converged"] = None if wf.convergence is None else int(wf.convergence["best_converged"].sum())
    joined.attrs["first_feature_row"] = next(iter(sets.values())).index.min()
    return joined


def compare(df: pd.DataFrame, name: str, ref: str, h: int, n_boot: int) -> dict:
    block = max(63, h)
    y = df["target"].to_numpy()
    e_f, e_b = df[name].to_numpy() - y, df[ref].to_numpy() - y
    q_f, q_b = qlike(df[name].to_numpy(), y), qlike(df[ref].to_numpy(), y)
    r_lo, r_hi = paired_interval(e_f, e_b, statistic="rmse", block=block, n_boot=n_boot)
    q_lo, q_hi = paired_interval(q_f, q_b, statistic="mean", block=block, n_boot=n_boot)
    return {"h": h, "forecast": name, "reference": ref, "block": block, "windows": len(df) // h,
            "dRMSE 95%": f"{r_lo:+.3f} to {r_hi:+.3f}", "RMSE": verdict(r_lo, r_hi),
            "dQLIKE 95%": f"{q_lo:+.3f} to {q_hi:+.3f}", "QLIKE": verdict(q_lo, q_hi),
            "_r": (r_lo, r_hi), "_q": (q_lo, q_hi)}


def losses(df: pd.DataFrame) -> pd.DataFrame:
    y = df["target"].to_numpy()
    return pd.DataFrame([{"model": m, "RMSE": f"{np.sqrt(((df[m] - df['target']) ** 2).mean()):.3f}",
                          "QLIKE": f"{qlike(df[m].to_numpy(), y).mean():.3f}"} for m in df.columns if m != "target"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "docs" / "DEV_HORIZONS_2026-10.md"))
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--horizons", default=",".join(str(h) for h in HORIZONS + DESCRIPTIVE))
    args = parser.parse_args()
    block_network()
    returns, ivs = load()
    horizons = [int(x) for x in args.horizons.split(",")]
    noise = pd.Series(np.random.default_rng(0).standard_normal(len(returns)), index=returns.index)

    out: list[str] = []
    P = out.append
    P(f"{CLASS}\n")
    P("# Development-only horizons 5 to 126 days (and 252, descriptive), October 2026\n")
    P(f"Class of every table in this file: **{CLASS}**. Written by `examples/dev_horizons.py` at {git_head()}, "
      f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}, {args.n_boot:,} bootstrap draws (seed 0). Data: S&P 500 "
      f"returns and the VIX, VIX9D and VIX6M closes {returns.index.min().date()} to {returns.index.max().date()} "
      f"({len(returns)} days) from the committed caches. Stage S8 (a) of the reopen.\n")
    P("Design (S4a's, `examples/dev_continuations.py`): target = realised vol over the next h days; expanding OLS "
      "on log HAR inputs plus the listed regressors, log target, refit every 63 rows after 756, embargo h; paired "
      "circular block bootstrap with block = max(63, h). The HMM is the two-state walk-forward model (min_train "
      "756, step 63), refit for each horizon. Two changes from S4a: the implied vol matches the horizon (VIX9D at "
      "5 and 10 days, VIX at 21 and 63, VIX6M at 126; the VIX is shown beside it), and every feature set at a "
      "horizon is fitted on the same rows, the dates where all of that horizon's inputs exist (desk finding 6), "
      "so the 21- and 63-day numbers differ slightly from S4a's. VIX9D starts 2011-01-03 and VIX6M 2008-01-02, "
      "so the 5-, 10- and 126-day samples are shorter. *windows* = scored days / h, the number of "
      "non-overlapping targets.\n")
    tables, rows = {}, []
    for h in horizons:
        print(f"horizon {h} ...", flush=True)
        df = scored_table(returns, ivs, h, noise)
        tables[h] = df
        conv = df.attrs["converged"]
        P(f"## Horizon {h}" + (" (descriptive only)" if h in DESCRIPTIVE else "") + "\n")
        P(f"Scored days {len(df):,}, {df.index.min().date()} to {df.index.max().date()}; non-overlapping windows "
          f"{len(df) // h}; implied vol {MATCHING_IV[h]}; first feature row {df.attrs['first_feature_row'].date()}; "
          f"HMM refits {df.attrs['n_refits']}" + (f", converged {conv} of {df.attrs['n_refits']}" if conv is not None else "") + ".\n")
        P(md_table(losses(df)) + "\n")
        if h in DESCRIPTIVE:
            P(f"No interval and no verdict at h = {h}: there is no cached one-year implied vol (the VIX, a one-month "
              f"index, stands in), the sample holds {len(df) // h} non-overlapping windows, and a one-year realised-vol "
              "target is mostly mean reversion, a different question from the paper's one-month VIX question.\n")
            continue
        cmp_rows = [compare(df, f, r, h, args.n_boot) for f, r in comparisons(h)]
        rows += cmp_rows
        P(md_table(pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in cmp_rows])) + "\n")

    P("## Summary: the regime-probability question at each horizon\n")
    P(f"Class: {CLASS}. HAR + matching IV + HMM prob against HAR + matching IV, beside the noise row and the "
      "matching IV's own gain over HAR.\n")
    summ = []
    for h in [h for h in horizons if h not in DESCRIPTIVE]:
        iv = MATCHING_IV[h]
        get = {(r["forecast"], r["reference"]): r for r in rows if r["h"] == h}
        p, n, v = get[(f"HAR + {iv} + HMM prob", f"HAR + {iv}")], get[(f"HAR + {iv} + noise", f"HAR + {iv}")], get[(f"HAR + {iv}", "HAR")]
        summ.append({"h": h, "IV": iv, "windows": p["windows"], "HMM prob dRMSE": f"{p['dRMSE 95%']} ({p['RMSE']})",
                     "HMM prob dQLIKE": f"{p['dQLIKE 95%']} ({p['QLIKE']})",
                     "noise dRMSE": f"{n['dRMSE 95%']} ({n['RMSE']})", "noise dQLIKE": f"{n['dQLIKE 95%']} ({n['QLIKE']})",
                     "IV vs HAR dRMSE": f"{v['dRMSE 95%']} ({v['RMSE']})"})
    P(md_table(pd.DataFrame(summ)) + "\n")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="ascii")
    for s in summ:
        print(f"h={s['h']} {s['IV']}: prob {s['HMM prob dRMSE']} | {s['HMM prob dQLIKE']}; noise {s['noise dRMSE']}")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
