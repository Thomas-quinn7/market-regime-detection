"""MS-GARCH and credit holdout: oil, gold, emerging markets and Brazil, from daily data.

Run from the repo root:

    python -u examples/msgarch_credit_holdout.py --dry-run   # S&P 500 development data, same code path
    python -u examples/msgarch_credit_holdout.py             # the holdout, run once

The claims, models, scoring and verdict rules are fixed in docs/MSGARCH_CREDIT_HOLDOUT_PROTOCOL.md,
and each asset goes through ``evaluate_asset`` from examples/msgarch_credit.py unchanged. Per asset:
daily ETF returns from Yahoo (adjusted close), which also set the calendar, the ETF's CBOE implied-vol
index from FRED, and the Baa-Treasury spread ``BAA10Y`` from FRED.

``--dry-run`` puts the S&P 500 development data (``^GSPC``, ``^VIX``, ``BAA10Y``, to the end of 2023)
through the same loaders, ``evaluate_asset`` and verdict code, so the script can be tested without
loading any holdout series. It is not a result.

Verdicts across assets use ``claim_verdict`` from examples/cross_index_holdout.py: a "better" claim is
confirmed if better on at least two assets and worse on none, rejected if better on none, and mixed
otherwise; a "not better" claim holds if better on no asset, and fails otherwise. An asset with fewer
than 750 scored days is reported but left out of the count.
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from cross_index_holdout import claim_verdict  # noqa: E402
from msgarch_credit import DEV_END, RETURNS_FROM, evaluate_asset  # noqa: E402

from regimes.data import load_fred_series, load_index_returns  # noqa: E402

HOLDOUT_END = "2026-10-12"
MIN_SCORED_DAYS = 750

# name: (Yahoo ticker, FRED implied-vol series)
HOLDOUT = {
    "Crude oil (USO)": ("USO", "OVXCLS"),
    "Gold (GLD)": ("GLD", "GVZCLS"),
    "Emerging markets (EEM)": ("EEM", "VXEEMCLS"),
    "Brazil (EWZ)": ("EWZ", "VXEWZCLS"),
}
DEVELOPMENT = {"S&P 500 (dry run, development data)": ("^GSPC", "VIXCLS")}


def load_asset(ticker: str, fred_id: str, end: str) -> tuple[pd.Series, pd.Series]:
    """Daily returns and implied vol for one asset, everything up to ``end``."""
    # yfinance treats the end date as exclusive, so ask for the day after.
    yahoo_end = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    returns = load_index_returns(ticker, start=RETURNS_FROM, end=yahoo_end).loc[:end]
    iv = load_fred_series(fred_id).loc[RETURNS_FROM:end]
    return returns, iv


def main() -> None:
    warnings.simplefilter("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="S&P 500 development data through the same code; not a result")
    args = parser.parse_args()
    assets, end = (DEVELOPMENT, DEV_END) if args.dry_run else (HOLDOUT, HOLDOUT_END)
    credit = load_fred_series("BAA10Y").loc[RETURNS_FROM:end]

    results = {}
    for name, (ticker, fred_id) in assets.items():
        returns, iv = load_asset(ticker, fred_id, end)
        results[name] = evaluate_asset(name, returns, iv, credit, end=end)

    counted = {k: v for k, v in results.items() if v["n_days"] >= MIN_SCORED_DAYS}
    print("\n##### Scored days per asset")
    for name, res in results.items():
        note = "" if name in counted else f"  (fewer than {MIN_SCORED_DAYS}: reported, not counted)"
        print(f"  {name}: {res['n_days']}{note}")

    rows = []
    first = next(iter(results.values()))["claims"]
    for i, claim in first.iterrows():
        per_asset = {name: res["claims"].loc[i, "RMSE"] for name, res in counted.items()}
        rows.append({"claim": claim["claim"], "forecast": claim["forecast"],
                     "reference": claim["reference"], "expected": claim["expected"],
                     **per_asset, "outcome": claim_verdict(claim["expected"], list(per_asset.values()))})
    print("\n##### Claims across assets (RMSE verdict per asset)")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
