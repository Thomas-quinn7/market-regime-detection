# Data extension plan

Started 2026-10-13. The VIX result (docs/WRITEUP.md, "Adding the VIX") showed that forward-looking
data improves the volatility forecast and the regime model adds nothing on top. Both S&P 500 holdouts
(1990-2004 and 2024-2026) are now used, so every new idea below is developed on S&P 500 data and has
to be confirmed somewhere else. This file records what data exists, what was checked, and which data
is held back unread for that confirmation.

## What is available, checked 2026-10-13

| Series | Source | History | Status | Use |
|---|---|---|---|---|
| VIX9D, VIX3M, VIX6M | Yahoo (`load_vol_indices`) | 2011-01, 2006-07, 2008-01 to now | cached for 2005-2023 | VIX term structure |
| VVIX | Yahoo | 2007-01 to now | cached for 2005-2023 | uncertainty about vol itself |
| SKEW | Yahoo | 1990 to now | cached for 2005-2023 | priced tail risk |
| Moody's Baa minus 10y (`BAA10Y`) | FRED (`load_fred_series`) | 1986 to now | cached | credit stress, lagged one business day |
| VXN with Nasdaq-100 | Yahoo / FRED `VXNCLS` | 2001-02 to now | **held back, not downloaded** | holdout |
| VXD with the Dow | FRED `VXDCLS` (Yahoo from 2005-11) | 1997-10 to now | **held back, not downloaded** | holdout |
| RVX with Russell 2000 | FRED `RVXCLS` (not on Yahoo) | 2004-01 to now | **held back, not downloaded** | holdout |
| Intraday futures bars, ES / NQ / YM / RTY / ZN | Databento `GLBX.MDP3` | 2010-06 (RTY 2017-07) | needs an API key and pricing | intraday realised vol |

Checked and rejected:

- **ICE BofA high-yield and investment-grade spreads** (`BAMLH0A0HYM2`, `BAMLC0A0CM`): FRED now only
  serves them from 2023-10-16, three years of history. `BAA10Y` is the usable credit series.
- **NFCI and STLFSI4** (financial conditions indices): weekly and revised after release, so the
  current vintage leaks. They would need ALFRED vintages, as the macro section does.
- **European implied vol** (VSTOXX, VDAX): not on Yahoo or FRED. Not pursued.
- **Free intraday history**: Yahoo keeps one-minute bars for about 30 days and hourly bars for about
  two years. Nothing free covers the 2008 or 2020 crises intraday, hence Databento.

## Investigations

All developed on the S&P 500, 2005-2023, with the existing walk-forward forecast comparison
(`examples/vol_forecast_vix.py`), HAR + VIX as the bar to beat.

1. **VIX term structure and tails.** Does the slope (VIX9D or VIX against VIX3M), VVIX or SKEW add to
   HAR + VIX? The slope is the market's view of how quickly vol will mean-revert, which is the one
   thing a single 30-day VIX cannot say.
2. **Credit.** Does `BAA10Y`, lagged one business day, add to HAR + VIX?
3. **Regimes as conditioning rather than as a level.** The HMM loses as a level forecast because two
   states cannot track a continuous quantity. A regime-switching HAR, where the HAR coefficients
   differ by regime (interaction terms with the filtered probability), keeps the forecast
   continuous and uses the regime only for how fast vol mean-reverts. The regime can also be inferred
   from forward-looking inputs (log VIX, the VIX slope, credit) rather than from returns.
4. **Intraday realised vol (Databento).** Five-minute realised vol from ES futures as both the target
   and the HAR input, which is HAR-RV as Corsi specified it. The same data gives an intraday
   stock-bond correlation (ES against ZN) for the stock-bond regime question, where daily returns
   needed a long window to settle.

## Holdout

The confirmation is on other US indices, each with its own implied-vol index: Nasdaq-100 with VXN,
the Dow with VXD, and the Russell 2000 with RVX, plus their intraday futures (NQ, YM, RTY) for
investigation 4. None of this has been downloaded. A frozen protocol, in the style of
docs/VIX_HOLDOUT_PROTOCOL.md, will be committed before any of it is loaded.

Caveat, stated in advance: these indices move closely with the S&P 500 and share its crises, so this
tests whether a result generalises across US indices rather than giving an independent history. If
Databento holdout data has to be bought before the protocol is written (the credit expires on
2026-10-25), the files will be downloaded but not opened, and the protocol will record the download
date and that they were unread.

## Databento

- Credit: $125, expiring 2026-10-25, shared with other projects' wish lists.
- Run `python examples/price_databento.py` (metadata only, buys nothing) for an itemised bill of the
  items above. Nothing is bought until the bill is approved.
- Raw files go to `<workspace>/market-data/databento` (outside this repo, `MARKET_DATA_DIR`
  overrides). Databento data is licensed for internal use, so only derived daily statistics are ever
  used here, and nothing raw is committed.
