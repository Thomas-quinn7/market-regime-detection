"""Intraday realised volatility from Databento futures bars.

Every volatility number elsewhere in this repo is built from daily closes, which is a noisy measure
of a day's variance: one squared return per day. Summing squared five-minute returns over the trading
session gives a far more precise daily realised variance, both as a forecasting *target* and as a
HAR *input*, and no free source has a long intraday history. Databento's CME feed (``GLBX.MDP3``)
does, from June 2010, for the equity index futures (ES, NQ, YM, and RTY from 2017).

Licensing: Databento data is for internal use. Raw downloads go to ``market_data_dir()``, which sits
outside this public repo (default ``<workspace>/market-data/databento``, override with the
``MARKET_DATA_DIR`` environment variable). Only derived daily statistics are used by the analysis,
and nothing raw is ever committed. The API key is read from ``DATABENTO_API_KEY`` (environment or a
gitignored ``.env``), never passed in code.

Continuous contracts: ``ES.v.0`` is the front contract by volume, re-mapped at most once per day.
Returns are only ever taken *within* one regular session, so a roll between days never shows up as a
price jump. If a session still contains bars from two instruments, the one with more volume is kept.
"""
from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

GLBX = "GLBX.MDP3"
RTH_OPEN, RTH_CLOSE = "09:30", "16:00"   # US equity regular trading hours, New York time
NY = "America/New_York"


def market_data_dir() -> Path:
    """Where raw licensed downloads live: outside the repo, never committed."""
    default = Path(__file__).resolve().parents[3] / "market-data" / "databento"
    path = Path(os.environ.get("MARKET_DATA_DIR", default))
    path.mkdir(parents=True, exist_ok=True)
    return path


def _api_key() -> str:
    key = os.environ.get("DATABENTO_API_KEY")
    if not key:
        env = Path(__file__).resolve().parents[2] / ".env"
        if env.exists():
            for line in env.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("DATABENTO_API_KEY="):
                    key = line.split("=", 1)[1].strip().strip('"').strip("'")
    if not key:
        raise RuntimeError("DATABENTO_API_KEY is not set (environment or market-regime-detection/.env)")
    return key


def databento_quote(symbols: list[str], schema: str, start: str, end: str, *,
                    dataset: str = GLBX, stype_in: str = "continuous") -> dict:
    """Price a request before buying it: cost in USD and billable size, from Databento's metadata API.

    Metadata calls do not download data. Run this and show the bill before any ``fetch_bars`` call.
    """
    import databento as db

    client = db.Historical(_api_key())
    kw = dict(dataset=dataset, symbols=symbols, schema=schema, start=start, end=end, stype_in=stype_in)
    return {
        "cost_usd": float(client.metadata.get_cost(**kw)),
        "billable_bytes": int(client.metadata.get_billable_size(**kw)),
    }


def fetch_bars(symbol: str, schema: str, start: str, end: str, *, dataset: str = GLBX,
               stype_in: str = "continuous") -> Path:
    """Download bars to a DBN file under ``market_data_dir()`` (skipped if the file already exists).

    This spends Databento credit. Quote it first with ``databento_quote``.
    """
    import databento as db

    path = market_data_dir() / f"{dataset}_{symbol}_{schema}_{start}_{end}.dbn.zst"
    if not path.exists():
        db.Historical(_api_key()).timeseries.get_range(
            dataset=dataset, symbols=[symbol], schema=schema, start=start, end=end,
            stype_in=stype_in, path=str(path),
        )
    return path


def load_bars(path: Path) -> pd.DataFrame:
    """Read a downloaded DBN file into a DataFrame indexed by UTC bar-open time."""
    import databento as db

    return db.DBNStore.from_file(str(path)).to_df()


def daily_realised_vol(bars: pd.DataFrame, *, every: str = "5min") -> pd.DataFrame:
    """Regular-session realised volatility per day from one-minute bars, in daily percent.

    For each New York trading day: keep the 09:30-16:00 bars of the session's main instrument,
    sample the close on an ``every`` grid, prepend the first bar's open, and sum the squared log
    returns. Returns ``rv`` (sqrt of the realised variance, percent) and ``n_returns``.

    ``bars`` needs a UTC DatetimeIndex (bar open time) and ``open``, ``close`` and ``volume``
    columns; ``instrument_id`` is used when present.
    """
    df = bars.copy()
    if df.index.tz is None:
        df.index = df.index.tz_localize("UTC")
    df.index = df.index.tz_convert(NY)
    df = df.between_time(RTH_OPEN, RTH_CLOSE, inclusive="left")

    rows = {}
    for day, g in df.groupby(df.index.date):
        if "instrument_id" in g and g["instrument_id"].nunique() > 1:
            main = g.groupby("instrument_id")["volume"].sum().idxmax()
            g = g[g["instrument_id"] == main]
        # Close of each ``every`` interval, labelled at the interval's end.
        closes = g["close"].resample(every, label="right", closed="left").last().dropna()
        prices = np.concatenate([[g["open"].iloc[0]], closes.to_numpy(dtype=float)])
        r = np.diff(np.log(prices)) * 100.0
        rows[pd.Timestamp(day)] = {"rv": float(np.sqrt((r ** 2).sum())), "n_returns": len(r)}
    out = pd.DataFrame.from_dict(rows, orient="index")
    out.index.name = "date"
    return out
