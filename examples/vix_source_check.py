"""Which VIX each claim used, and how far the two sources on disk differ on development days.

development data only (the comparison); the source table is read off the frozen scripts.

The repo mixes two VIX sources (desk, data-engineer, joint review 2026-10-18 finding 18): the development
scripts and the two S&P 500 holdouts read Yahoo ``^VIX`` through ``regimes.data.load_vix``
(src/regimes/data.py); the cross-index and the MS-GARCH/credit holdouts read FRED ``VIXCLS`` (and the
FRED OVXCLS, GVZCLS, VXEEMCLS, VXEWZCLS series for the ETFs) through ``regimes.data.load_fred_series``
(examples/cross_index_holdout.py, examples/msgarch_credit_holdout.py). FRED's VIXCLS equals Cboe's
published history exactly (desk, data-engineer, re-derived on 8,317 days); Yahoo's does not. This script
compares the committed Yahoo development cache ``data/VIX_2000-01-01_2023-12-31.csv`` with the committed
FRED cache ``data/fred_VIXCLS.csv`` on their common days to 2023-12-31 only (rule 3 of the reopen scope)
and prints the numbers the VIX-source sentence in ``docs/FIXES_FOR_THOMAS_2026-10.md`` quotes.

    python examples/vix_source_check.py
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

DEV_END = "2023-12-31"
YAHOO = ROOT / "data" / "VIX_2000-01-01_2023-12-31.csv"
FRED = ROOT / "data" / "fred_VIXCLS.csv"

# claim or table -> (VIX source, where the loader is called)
SOURCES = [
    ("Development work on the S&P 500 (WRITEUP development tables, examples/*.py except the two FRED holdouts)",
     "Yahoo ^VIX", "regimes.data.load_vix -> load_index_prices('^VIX')"),
    ("VIX holdout claims A, B, C, S&P 500 1996-2004 and 2024-2026 (examples/vol_forecast_vix.py)",
     "Yahoo ^VIX", "regimes.data.load_vix"),
    ("Cross-index holdout claims P1-P5, R1-R3 (examples/cross_index_holdout.py)",
     "FRED VIXCLS (S&P 500 VIX used as the implied vol for all three indices)", "regimes.data.load_fred_series('VIXCLS')"),
    ("MS-GARCH and credit holdout claims M1-M5 (examples/msgarch_credit_holdout.py)",
     "FRED OVXCLS, GVZCLS, VXEEMCLS, VXEWZCLS (one Cboe ETF vol index per asset; VIXCLS in the dry run only)",
     "regimes.data.load_fred_series(<id>)"),
    ("Stock-bond holdout (examples/stock_bond_holdout.py)", "no VIX", "-"),
]


def load_yahoo(path: Path = YAHOO, end: str = DEV_END) -> pd.Series:
    s = pd.read_csv(path, index_col=0, parse_dates=True).iloc[:, 0].astype(float)
    return s.loc[:end].rename("yahoo")


def load_fred(path: Path = FRED, end: str = DEV_END) -> pd.Series:
    """FRED's CSV marks holidays with '.', which become NaN here and are dropped."""
    df = pd.read_csv(path, index_col=0, parse_dates=True, na_values=["."])
    return df.iloc[:, 0].astype(float).loc[:end].dropna().rename("fred")


def compare_sources(yahoo: pd.Series, fred: pd.Series, *, tol: float = 0.005) -> dict:
    """Common days, days whose prints differ by more than ``tol`` points, the largest gap and its date,
    and the days each source has that the other lacks (over the overlap of their spans)."""
    lo = max(yahoo.index.min(), fred.index.min())
    hi = min(yahoo.index.max(), fred.index.max())
    y = yahoo.loc[lo:hi]
    f = fred.loc[lo:hi]
    common = y.index.intersection(f.index)
    diff = (f.loc[common] - y.loc[common])
    big = diff[diff.abs() > tol]
    return {
        "span": f"{lo.date()} to {hi.date()}",
        "common_days": int(len(common)),
        "days_differing": int(len(big)),
        "max_abs_diff": float(diff.abs().max()) if len(common) else float("nan"),
        "max_abs_date": str(diff.abs().idxmax().date()) if len(common) else "",
        "fred_only": [str(d.date()) for d in f.index.difference(y.index)],
        "yahoo_only": [str(d.date()) for d in y.index.difference(f.index)],
        "differing": {str(d.date()): round(float(v), 2) for d, v in big.items()},
    }


def main() -> None:
    yahoo = load_yahoo()
    fred = load_fred()
    r = compare_sources(yahoo, fred)
    print("VIX source per claim (read off the frozen scripts):")
    for what, src, how in SOURCES:
        print(f"  {what}: {src}  [{how}]")
    print(f"\nYahoo ^VIX ({YAHOO.name}) vs FRED VIXCLS ({FRED.name}), development days only, {r['span']}:")
    print(f"  common days {r['common_days']}; days differing by more than 0.005 points: {r['days_differing']}; "
          f"largest gap {r['max_abs_diff']:.2f} points on {r['max_abs_date']}")
    print(f"  FRED prints with no Yahoo row: {len(r['fred_only'])} ({', '.join(r['fred_only'])})")
    print(f"  Yahoo rows with no FRED print: {len(r['yahoo_only'])} ({', '.join(r['yahoo_only'])})")
    print("  differing days (FRED minus Yahoo): " + ", ".join(f"{d} {v:+.2f}" for d, v in r["differing"].items()))
    print("\nOne sentence for the paper (proposal): The development work and the two S&P 500 holdouts use Yahoo's "
          "^VIX; the cross-index holdout uses FRED's VIXCLS and the ETF holdout FRED's OVXCLS, GVZCLS, VXEEMCLS and "
          f"VXEWZCLS. FRED equals Cboe's history; Yahoo differs from it on {r['days_differing']} of "
          f"{r['common_days']} development days by up to {r['max_abs_diff']:.2f} points and lacks "
          f"{len(r['fred_only'])} days FRED prints.")


if __name__ == "__main__":
    main()
