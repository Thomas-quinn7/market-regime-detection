"""Macro growth/inflation quadrant regimes (roadmap P4, Tier 1).

Bridgewater's All Weather and Kritzman-Page-Turkington reduce the macro world to two drivers, growth
and inflation, each rising or falling, giving a four-quadrant regime map. Each quadrant has asset
"environmental biases", which is the basis for regime-conditional allocation (reuses P3).

The hard part is not the 2x2 - it is avoiding look-ahead. Macro series are published weeks after their
reference period and are then revised, so a naive pull uses numbers that did not exist at decision
time. This module uses **point-in-time** data from FRED/ALFRED:

- **Tier 1 (implemented here):** first-release values, indexed by their actual PUBLICATION date
  (``realtime_start``) rather than their reference date, then forward-filled onto the daily grid. This
  removes the release-lag look-ahead and uses first prints, not future-revised numbers.
- **Tier 2 (documented, not implemented):** full ALFRED vintage reconstruction via
  ``Fred.get_series_as_of_date(series_id, date)`` at each rebalance date, which also captures later
  revisions as they became known. Use it only if P4 becomes a headline result; it costs one API call
  per vintage date and needs care with the monthly cadence.

Requires a free FRED API key in the ``FRED_API_KEY`` environment variable (never commit it).

Honest limitation, stated loudly: macro regimes turn over slowly, so a 2005-2023 window holds only a
handful of complete cycles. Treat P4 as a descriptive allocation tilt, not a statistically powerful
predictor.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

# Default point-in-time series: CFNAI (monthly activity, "growth vs trend") and core CPI (barely revised).
GROWTH_SERIES = "CFNAI"
INFLATION_SERIES = "CPILFESL"

QUADRANTS = {
    (True, False): "goldilocks",   # growth rising, inflation falling
    (True, True): "overheating",   # growth rising, inflation rising
    (False, True): "stagflation",  # growth falling, inflation rising
    (False, False): "slowdown",    # growth falling, inflation falling
}

# Simple, documented environmental-bias tilt over {equity, bonds, cash}. Not optimised - a transparent
# mapping of each quadrant to the asset that historically likes it.
QUADRANT_WEIGHTS = {
    "goldilocks": {"equity": 1.0},                 # risk-on
    "overheating": {"equity": 0.6, "cash": 0.4},   # growth good but inflation a headwind
    "stagflation": {"cash": 1.0},                  # bad for both stocks and nominal bonds
    "slowdown": {"bonds": 1.0},                    # disinflation + weak growth favours duration
}


def _fred(api_key: str | None):
    from fredapi import Fred  # lazy: the package imports without a network/credential

    key = api_key or os.environ.get("FRED_API_KEY")
    if not key:
        raise RuntimeError("set the FRED_API_KEY environment variable (free key from fred.stlouisfed.org)")
    return Fred(api_key=key)


def load_macro_series(series_id: str, *, api_key: str | None = None, use_cache: bool = True) -> pd.DataFrame:
    """First-release values of a FRED series with their publication dates.

    Returns a DataFrame indexed by observation (reference) date, with columns ``value`` (the first
    release) and ``pub_date`` (when that value was first published, i.e. ALFRED ``realtime_start``).
    Cached to ``data/`` so results are reproducible - first releases do not change, and re-pulling live
    FRED would silently fold in later revisions.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = DATA_DIR / f"macro_{series_id}_firstrelease.csv"
    if use_cache and path.exists():
        df = pd.read_csv(path, parse_dates=["obs_date", "pub_date"])
        return df.set_index("obs_date")

    raw = _fred(api_key).get_series_all_releases(series_id)
    raw = raw.rename(columns={"date": "obs_date", "realtime_start": "pub_date"})
    raw["obs_date"] = pd.to_datetime(raw["obs_date"])
    raw["pub_date"] = pd.to_datetime(raw["pub_date"])
    raw["value"] = pd.to_numeric(raw["value"], errors="coerce")
    raw = raw.dropna(subset=["value"])
    # First release per observation = the row with the earliest publication date.
    first = raw.sort_values("pub_date").groupby("obs_date", as_index=False).first()
    first = first[["obs_date", "value", "pub_date"]].sort_values("obs_date")
    first.to_csv(path, index=False)
    return first.set_index("obs_date")


def to_point_in_time(values_by_obs: pd.Series, pub_dates: pd.Series, daily_index: pd.Index) -> pd.Series:
    """Map an observation-indexed series onto a daily grid by PUBLICATION date, forward-filled.

    Each value appears only on and after the day it was published, so the resulting daily series is
    causal: at any date it reflects only what had actually been released.
    """
    s = pd.Series(np.asarray(values_by_obs, dtype=float),
                  index=pd.DatetimeIndex(pd.to_datetime(pub_dates.to_numpy()))).sort_index()
    s = s[~s.index.duplicated(keep="last")]  # if several obs published the same day, keep the latest
    return s.reindex(daily_index, method="ffill")


def macro_features(
    daily_index: pd.Index,
    *,
    growth_series: str = GROWTH_SERIES,
    inflation_series: str = INFLATION_SERIES,
    api_key: str | None = None,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Point-in-time daily growth and inflation signals on ``daily_index``.

    Growth is the CFNAI activity index (already "growth vs trend"); inflation is the year-over-year
    change of the core-CPI level. Both are computed on the observation-ordered first releases, then
    aligned to the daily grid by publication date.
    """
    g = load_macro_series(growth_series, api_key=api_key, use_cache=use_cache)
    infl = load_macro_series(inflation_series, api_key=api_key, use_cache=use_cache)
    infl_yoy = infl["value"].pct_change(12) * 100.0  # YoY % on the reference-ordered levels

    return pd.DataFrame({
        "growth": to_point_in_time(g["value"], g["pub_date"], daily_index),
        "inflation": to_point_in_time(infl_yoy, infl["pub_date"], daily_index),
    })


def macro_quadrant(features: pd.DataFrame, *, trend_window: int = 252) -> pd.DataFrame:
    """Classify each day into a growth/inflation quadrant.

    "Rising" means above the trailing ``trend_window``-day average of the signal (a causal,
    direction-vs-trend rule). Returns the input plus ``growth_rising``, ``inflation_rising`` and a
    categorical ``quadrant``.
    """
    out = features.copy()
    out["growth_rising"] = out["growth"] > out["growth"].rolling(trend_window).mean()
    out["inflation_rising"] = out["inflation"] > out["inflation"].rolling(trend_window).mean()
    valid = out[["growth", "inflation"]].notna().all(axis=1) & \
        out["growth"].rolling(trend_window).mean().notna() & \
        out["inflation"].rolling(trend_window).mean().notna()
    out["quadrant"] = [
        QUADRANTS[(gr, ir)] if v else None
        for gr, ir, v in zip(out["growth_rising"], out["inflation_rising"], valid)
    ]
    return out


def quadrant_weights(quadrant: pd.Series, *, assets=("equity", "bonds", "cash")) -> pd.DataFrame:
    """Map a quadrant label series to target weights over ``assets`` (rows sum to 1 where defined)."""
    rows = {a: [] for a in assets}
    for q in quadrant:
        w = QUADRANT_WEIGHTS.get(q, {})
        for a in assets:
            rows[a].append(float(w.get(a, 0.0)))
    return pd.DataFrame(rows, index=quadrant.index)
