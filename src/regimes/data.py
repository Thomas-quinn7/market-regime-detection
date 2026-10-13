"""Deterministic, cached daily equity-index data.

Design goals:
- Reproducible: a pull is cached to ``data/`` keyed by ticker and date range, so re-running gives the
  same numbers rather than silently drifting when the upstream source updates.
- Causal-friendly: returns a tidy, date-sorted series of daily log returns with no gaps introduced.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parents[2] / "data"


def _cache_path(ticker: str, start: str, end: str) -> Path:
    safe = ticker.replace("^", "").replace("/", "_")
    return DATA_DIR / f"{safe}_{start}_{end}.csv"


def load_index_prices(
    ticker: str = "^GSPC",
    start: str = "2004-01-01",
    end: str = "2024-12-31",
    *,
    use_cache: bool = True,
) -> pd.Series:
    """Return a date-indexed Series of adjusted close prices, cached to ``data/``.

    Network access happens only on a cache miss. The cache is what makes results reproducible; do not
    remove it in favour of a live pull inside experiments.
    """
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    path = _cache_path(ticker, start, end)
    if use_cache and path.exists():
        df = pd.read_csv(path, index_col=0, parse_dates=True)
        return df["adj_close"].dropna()

    # Imported lazily so the package imports without a network stack present.
    import yfinance as yf

    raw = yf.download(ticker, start=start, end=end, auto_adjust=True, progress=False)
    if raw.empty:
        raise RuntimeError(f"no data returned for {ticker} in [{start}, {end}]")
    close = raw["Close"]
    # Recent yfinance returns MultiIndex columns even for a single ticker, so ``raw["Close"]`` can be
    # a one-column DataFrame; collapse it to a Series before renaming.
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    prices = close.rename("adj_close")
    prices.to_frame().to_csv(path)
    return prices.dropna()


def load_index_returns(
    ticker: str = "^GSPC",
    start: str = "2004-01-01",
    end: str = "2024-12-31",
    *,
    use_cache: bool = True,
) -> pd.Series:
    """Daily log returns (in percent) for ``ticker``, date-sorted, NaNs dropped.

    Percent scaling keeps the switching-variance model numerically comfortable.
    """
    prices = load_index_prices(ticker, start, end, use_cache=use_cache)
    log_ret = np.log(prices).diff().dropna() * 100.0
    log_ret.name = "log_return_pct"
    return log_ret.sort_index()


# The nine classic SPDR sector ETFs (pre-2015 history, so a long window is available).
SECTOR_ETFS = ("XLB", "XLE", "XLF", "XLI", "XLK", "XLP", "XLU", "XLV", "XLY")


def load_sector_returns(
    tickers=SECTOR_ETFS,
    start: str = "2005-01-01",
    end: str = "2023-12-31",
    *,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Daily log returns (percent) for several tickers, aligned on their common trading days.

    Each column is one ticker. Rows with any missing ticker are dropped so every column shares the
    same dates — the cross-asset regime analysis needs them aligned.
    """
    cols = {t: load_index_returns(t, start, end, use_cache=use_cache) for t in tickers}
    return pd.DataFrame(cols).dropna(how="any").sort_index()


TREASURY_10Y_CSV = DATA_DIR / "DGS10_fredgraph.csv"


def load_treasury_10y_returns(start: str = "1962-01-01", end: str = "2023-12-31") -> pd.Series:
    """Approximate daily total returns (percent) of a 10-year par Treasury from the FRED DGS10 yield.

    ETF bond histories start in 2002, so the long sample needs a proxy. The day-t return is carry
    plus the duration effect of the yield change, ``y_{t-1} / 252 - D_{t-1} * (y_t - y_{t-1})``, where
    ``D`` is the modified duration of a 10-year semi-annual par bond at the previous day's yield.
    Convexity and roll-down are ignored, which is small at a daily horizon. The yield file is the
    keyless FRED download (fred.stlouisfed.org/graph/fredgraph.csv?id=DGS10), committed so runs are
    reproducible.
    """
    raw = pd.read_csv(TREASURY_10Y_CSV, index_col=0, parse_dates=True)
    y = pd.to_numeric(raw.iloc[:, 0], errors="coerce").dropna() / 100.0  # decimal yield
    y = y.loc[start:end]
    y_prev = y.shift(1)
    duration = (1.0 - (1.0 + y_prev / 2.0) ** -20) / y_prev
    ret = y_prev / 252.0 - duration * (y - y_prev)
    return (ret * 100.0).dropna().rename("treasury_10y_ret_pct")


def load_vix(start: str = "2005-01-01", end: str = "2023-12-31", *, use_cache: bool = True) -> pd.Series:
    """Daily CBOE VIX close (annualised percent), cached like the index prices.

    VIX is the market's 30-calendar-day implied volatility for the S&P 500, so it carries forward-
    looking information that no function of past returns has. It closes at 4:15pm ET, after the
    4:00pm equity close, and both are known by the end of day t, so using VIX_t to forecast volatility
    over t+1 onward is causal.
    """
    return load_index_prices("^VIX", start, end, use_cache=use_cache).rename("vix")
