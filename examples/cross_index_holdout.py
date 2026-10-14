"""Cross-index holdout: the better-volatility-model claims on the Nasdaq-100, the Dow and the Russell 2000.

Run from the repo root (needs the Databento R1, R2 and R4 bar downloads, see src/regimes/intraday.py):

    python -u examples/cross_index_holdout.py --dry-run   # S&P 500 development data, same code path
    python -u examples/cross_index_holdout.py             # the holdout, run once

The claims, models, scoring and verdict rules are fixed in docs/CROSS_INDEX_HOLDOUT_PROTOCOL.md, and
each index goes through ``evaluate_index`` from examples/better_vol_models.py unchanged. Per index:

- session RV from that index's E-mini futures bars (NQ, YM, RTY), as for ES;
- daily index returns from Yahoo (``^NDX``, ``^DJI``, ``^RUT``) from 2000, which also set the calendar;
- the index's own implied vol from FRED (VXN, VXD, RVX), carried forward for up to 5 days.

``--dry-run`` puts the S&P 500 development data (ES bars, ``^GSPC``, FRED ``VIXCLS``, to the end of
2023) through the same loaders, ``evaluate_index`` and verdict code, so the script can be tested
without opening any holdout file. It is not a result.

Verdicts across indices, from the protocol: a "better" claim is confirmed if it is better on at least
two indices and worse on none, rejected if it is better on none, and mixed otherwise; a "not better"
claim holds if it is better on no index, and fails otherwise. An index with fewer than 750 scored days
is reported but left out of the count.
"""
from __future__ import annotations

import argparse
import sys
import warnings
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from better_vol_models import RETURNS_FROM, evaluate_index  # noqa: E402

from regimes.data import DATA_DIR, load_fred_series, load_index_returns  # noqa: E402
from regimes.intraday import cached_daily_rv, market_data_dir  # noqa: E402

HOLDOUT_END = "2026-10-12"  # last day of the Databento downloads
MIN_SCORED_DAYS = 750

# name: (Databento job folder, bar-file glob, RV cache, Yahoo ticker, FRED implied-vol series)
HOLDOUT = {
    "Nasdaq-100": ("R2", "*/*.ohlcv-1m.NQ.v.0.dbn.zst", "nq_rv_5min.csv", "^NDX", "VXNCLS"),
    "Dow Jones Industrial Average": ("R2", "*/*.ohlcv-1m.YM.v.0.dbn.zst", "ym_rv_5min.csv", "^DJI",
                                     "VXDCLS"),
    "Russell 2000": ("R4", "*/*.ohlcv-1m.dbn.zst", "rty_rv_5min.csv", "^RUT", "RVXCLS"),
}
DEVELOPMENT = {
    "S&P 500 (dry run, development data)": ("R1", "*/*.ohlcv-1m.dbn.zst", "es_rv_5min.csv", "^GSPC",
                                            "VIXCLS"),
}


def load_index(job: str, glob: str, rv_cache: str, ticker: str, fred_id: str, end: str):
    """Session RV, daily returns and implied vol for one index, everything up to ``end``."""
    files = sorted((market_data_dir() / job).glob(glob))
    if len(files) != 1:
        raise FileNotFoundError(f"expected one bar file for {job}/{glob}, found {len(files)}")
    rv = cached_daily_rv(files[0], DATA_DIR / rv_cache).loc[:end]
    # yfinance treats the end date as exclusive, so ask for the day after.
    yahoo_end = (pd.Timestamp(end) + pd.Timedelta(days=1)).strftime("%Y-%m-%d")
    returns = load_index_returns(ticker, start=RETURNS_FROM, end=yahoo_end).loc[:end]
    iv = load_fred_series(fred_id).loc[RETURNS_FROM:end]
    return rv, returns, iv


def claim_verdict(expected: str, per_index: list[str]) -> str:
    """Combine per-index RMSE verdicts ("better", "worse", "no difference") into the claim outcome."""
    n_better = per_index.count("better")
    if expected == "not better":
        return "holds" if n_better == 0 else "fails"
    if n_better >= 2 and "worse" not in per_index:
        return "confirmed"
    return "rejected" if n_better == 0 else "mixed"


def main() -> None:
    warnings.simplefilter("ignore")
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true",
                        help="S&P 500 development data through the same code; not a result")
    args = parser.parse_args()
    indices, end = (DEVELOPMENT, "2023-12-31") if args.dry_run else (HOLDOUT, HOLDOUT_END)

    results = {}
    for name, spec in indices.items():
        rv, returns, iv = load_index(*spec, end=end)
        results[name] = evaluate_index(name, rv, returns, iv, end=end)

    counted = {k: v for k, v in results.items() if v["n_days"] >= MIN_SCORED_DAYS}
    print("\n##### Scored days per index")
    for name, res in results.items():
        note = "" if name in counted else f"  (fewer than {MIN_SCORED_DAYS}: reported, not counted)"
        print(f"  {name}: {res['n_days']}{note}")

    rows = []
    first = next(iter(results.values()))["claims"]
    for i, claim in first.iterrows():
        per_index = {name: res["claims"].loc[i, "RMSE"] for name, res in counted.items()}
        rows.append({"claim": claim["claim"], "forecast": claim["forecast"],
                     "reference": claim["reference"], "expected": claim["expected"],
                     **per_index, "outcome": claim_verdict(claim["expected"], list(per_index.values()))})
    print("\n##### Claims across indices (RMSE verdict per index)")
    print(pd.DataFrame(rows).to_string(index=False))


if __name__ == "__main__":
    main()
