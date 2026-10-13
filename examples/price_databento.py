"""Price the Databento data for the intraday extensions, without buying anything.

Run from the repo root once DATABENTO_API_KEY is in the environment or in a gitignored .env:

    python examples/price_databento.py

It calls Databento's metadata API (cost and billable size) for each item in docs/DATA_EXTENSION_PLAN.md
and prints an itemised bill. Nothing is downloaded. Buying is a separate, deliberate step
(``regimes.intraday.fetch_bars``) after the bill has been approved.
"""
from __future__ import annotations

from regimes.intraday import databento_quote

END = "2026-10-13"
GLBX_START = "2010-06-06"   # first day of CME Globex history on Databento
RTY_START = "2017-07-10"    # Russell 2000 futures moved to CME in July 2017

# (item, symbol, schema, start, what it is for)
ITEMS = [
    ("D1", "ES.v.0", "ohlcv-1m", GLBX_START, "S&P 500 intraday realised vol (development)"),
    ("D2", "NQ.v.0", "ohlcv-1m", GLBX_START, "Nasdaq-100 intraday realised vol (holdout, unread)"),
    ("D3", "YM.v.0", "ohlcv-1m", GLBX_START, "Dow intraday realised vol (holdout, unread)"),
    ("D4", "RTY.v.0", "ohlcv-1m", RTY_START, "Russell 2000 intraday realised vol (holdout, unread)"),
    ("D5", "ZN.v.0", "ohlcv-1m", GLBX_START, "10y Treasury: intraday stock-bond correlation"),
    ("D1h", "ES.v.0", "ohlcv-1h", GLBX_START, "fallback: hourly ES if 1m is too dear"),
    ("D2h", "NQ.v.0", "ohlcv-1h", GLBX_START, "fallback: hourly NQ"),
]


def main() -> None:
    total = 0.0
    print(f"{'item':5s} {'symbol':8s} {'schema':9s} {'start':10s} {'cost $':>9s} {'size MB':>9s}  purpose")
    for item, sym, schema, start, why in ITEMS:
        q = databento_quote([sym], schema, start, END)
        total += q["cost_usd"] if not item.endswith("h") else 0.0
        print(f"{item:5s} {sym:8s} {schema:9s} {start:10s} {q['cost_usd']:9.2f} "
              f"{q['billable_bytes'] / 1e6:9.1f}  {why}")
    print(f"\ntotal for D1-D5 (one-minute items): ${total:.2f}")


if __name__ == "__main__":
    main()
