"""Is the HMM's high-volatility state an economic regime? Scored against NBER recessions and Fed easing.

Run from the repo root (the 1928-2023 walk-forward takes over an hour):

    python examples/regime_labels.py

Each quarterly refit block is saved to data/checkpoints/ as it is computed, so if the run is stopped,
running it again resumes where it left off instead of starting over.

The return-only two-state HMM is run walk-forward on S&P 500 daily returns from 30 Dec 1927 (the
start of Yahoo's daily history) to 2023, quarterly refits as elsewhere in the repo, and its filtered
high-vol probability is averaged per month. It is then scored as a classifier of two outside labels:

- NBER recession months (FRED ``USREC``), from the first out-of-sample month;
- Fed easing months, defined here as the effective fed funds rate (FRED ``DFF``, monthly average)
  at least 0.5 percentage points below its level six months earlier, from 1955.

Baselines are causal trailing volatility, 21-day and EWMA, averaged the same way. For the detection
counts every baseline is given the same share of "on" months as the HMM (``threshold_for_rate``), so
the comparison is about where alarms fall, not how many there are.

These are descriptive checks on data the repo has largely seen already, and NBER dates are only
known months after the fact, so nothing here is a tradeable or out-of-sample claim. Daily S&P 500
data before 1957 covers a 90-stock index and includes Saturday sessions until 1952.
"""
from __future__ import annotations

import warnings

import pandas as pd

from regimes.data import DATA_DIR, load_fred_series, load_index_returns
from regimes.evaluate import ewma_vol, realised_vol, walk_forward_oos
from regimes.labels import (
    auc,
    lead_lag_auc,
    monthly_mean,
    score_detection,
    threshold_for_rate,
)

START, END = "1927-12-30", "2023-12-31"


def main() -> None:
    warnings.simplefilter("ignore")
    returns = load_index_returns(start=START, end=END)
    print(f"S&P 500 daily returns: {len(returns)} days, {returns.index.min().date()} -> "
          f"{returns.index.max().date()}")
    print("walk-forward HMM, quarterly refits ...", flush=True)
    wf = walk_forward_oos(returns, min_train=756, step=63, horizon=21,
                          checkpoint_dir=DATA_DIR / "checkpoints" / "wf_gspc_1928_2023")
    print(f"  refits={wf.n_refits}, skipped={wf.n_skipped}, out of sample from "
          f"{wf.high_vol_prob.index.min().date()}")

    signals = pd.DataFrame({
        "HMM P(high vol)": monthly_mean(wf.high_vol_prob),
        "trailing 21-day vol": monthly_mean(realised_vol(returns, 21)),
        "EWMA vol (0.94)": monthly_mean(ewma_vol(returns)),
    }).dropna()
    first, last = signals.index.min(), signals.index.max()

    rec = load_fred_series("USREC")
    rec.index = rec.index.to_period("M").to_timestamp()
    rec = rec.loc[first:last].astype(int)
    dff = load_fred_series("DFF")
    dff_m = monthly_mean(dff)
    easing = ((dff_m - dff_m.shift(6)) <= -0.5).astype(int).loc["1955-01-01":last]
    labels = {"NBER recession": rec, "Fed easing": easing}

    for lname, lab in labels.items():
        s = signals.loc[lab.index.min():lab.index.max()]
        print(f"\n=== {lname}: {lab.index.min().date()} -> {lab.index.max().date()}, "
              f"{len(lab)} months, {int(lab.sum())} labelled ({lab.mean():.0%}), "
              f"{len(score_detection(lab, lab).lags)} episodes")
        rows = {}
        for name in s:
            ll = lead_lag_auc(s[name], lab)
            rows[name] = {"AUC same month": auc(s[name], lab), "AUC 3m ahead": ll[3],
                          "AUC 6m ahead": ll[6], "peak AUC": ll.max(), "at lead k": int(ll.idxmax())}
        print(pd.DataFrame(rows).T.round(3).to_string())
        print("(k > 0: the signal is high k months BEFORE the labelled months)")

        hmm_on = (s["HMM P(high vol)"] >= 0.5).astype(int)
        rate = float(hmm_on.mean())
        det = {"HMM P >= 0.5": score_detection(hmm_on, lab)}
        for name in ["trailing 21-day vol", "EWMA vol (0.94)"]:
            thr = threshold_for_rate(s[name], rate)
            det[f"{name} (same on-rate)"] = score_detection((s[name] >= thr).astype(int), lab)
        print(f"\ndetection, every signal on for {rate:.0%} of months "
              f"(lag window 6 months before to 12 after an episode start):")
        summary = pd.DataFrame({
            n: {"median lag (months)": pd.Series(d.lags).median() if d.lags else float("nan"),
                "caught": len(d.lags), "missed": d.misses, "false alarms": d.false_alarms}
            for n, d in det.items()
        }).T
        print(summary.to_string())
        if lname == "NBER recession":
            per = pd.DataFrame({n: pd.Series(d.lags) for n, d in det.items()})
            per.index = [d.strftime("%Y-%m") for d in per.index]
            print("\nlag per recession start (months; negative = flagged early, blank = missed):")
            print(per.to_string())


if __name__ == "__main__":
    main()
