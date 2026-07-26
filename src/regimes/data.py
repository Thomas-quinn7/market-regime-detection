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
