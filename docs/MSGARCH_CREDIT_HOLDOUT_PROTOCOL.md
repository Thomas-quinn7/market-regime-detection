# Holdout protocol: Markov-switching GARCH and credit spreads, on oil, gold and emerging markets

**Status, 2026-10-14: draft, not frozen.** Development on the S&P 500 is running. The claims below are
candidates and become final at the freeze. No holdout data has been loaded.

Written and committed **before** any holdout data was loaded. On 2026-10-14 the first and last dates
of each FRED implied-vol series below were checked to confirm they are still published; no value in
them has been read. No USO, GLD, EEM or EWZ price and none of OVX, GVZ, VXEEM or VXEWZ has ever been
loaded by this repo (checked against the code, the docs and the `data/` cache on 2026-10-14).

Each asset is run once. Whatever it gives is the result, and a bug found after the run is reported as
a bug, not silently fixed and rerun.

## Why this holdout

The cross-index holdout ([CROSS_INDEX_HOLDOUT_PROTOCOL.md](CROSS_INDEX_HOLDOUT_PROTOCOL.md)) is
spent: nothing beat HAR plus implied vol on the Nasdaq-100, the Dow or the Russell 2000. Two ideas
were left over. One is a regime model where volatility moves continuously inside each regime
(Markov-switching GARCH), aimed at the failure in the write-up ("Why it loses": the two-state HMM's
forecast is stuck between two levels). The other is credit spreads as a forward-looking input. Both are
put in this one protocol so the holdout is not spent on one idea.

The holdout assets are ETFs with their own CBOE implied-vol index on FRED. They are not US equity
indices, so unlike the last holdout they do not share every S&P 500 crisis by construction.

Caveats, stated in advance:

- Oil, emerging markets and Brazil all fell together in 2008, 2015 and 2020, and EEM holds Brazil.
  The four assets are not independent of each other.
- Credit is the US Baa corporate spread for every asset. There is less reason for it to forecast gold
  or oil volatility than equity volatility, and the result should be read that way.
- USO changed what it holds in April 2020 (it moved away from the front-month contract after the
  negative oil price) and did a 1-for-8 reverse split. Adjusted prices still give the fund's
  returns, so it is kept as it is, with no exclusion window.
- The target is realised vol from daily returns, which is much noisier than the intraday measure the
  last holdout used, so intervals will be wider.

## Two stages

1. **Development, S&P 500 only.** S&P 500 daily returns from 2000 to 2023, the VIX and `BAA10Y`, with
   `examples/msgarch_credit.py`. MS-GARCH details (innovations, a lower bound on the probability of
   staying in a regime) may be chosen here. The S&P 500 2024-2026 data is not used, as it is a spent
   holdout.
2. **Freeze, then run.** Before any holdout data is loaded, one commit adds the holdout script and
   final model code, and this file gets a line recording that commit's hash, which is pushed. The
   holdout script puts each asset through `evaluate_asset` from `examples/msgarch_credit.py`
   unchanged.

## Data

| Asset | Returns (Yahoo, adjusted close) | Implied vol (FRED) | IV history |
|---|---|---|---|
| Crude oil | USO, from 2006-04 | `OVXCLS` | 2007-05-10 on |
| Gold | GLD, from 2004-11 | `GVZCLS` | 2008-06-03 on |
| Emerging markets | EEM, from 2003-04 | `VXEEMCLS` | 2011-03-16 on |
| Brazil | EWZ, from 2000-07 | `VXEWZCLS` | 2011-03-16 on |

The ETF start months are the funds' launch dates as commonly reported, not checked against Yahoo,
since that would mean loading holdout prices; the run prints the first date of each. The IV start
dates were checked on FRED.

Credit: `BAA10Y` from FRED for every asset, already used in development. Returns start at each ETF's
first day (and no earlier than 2000-01-01); everything ends on **2026-10-12**. The ETFs close at 4:00pm
ET and the vol indices at 4:15pm, so the day-t implied vol is usable at t. `BAA10Y` is lagged one
business day. Implied vol and credit are carried forward for up to 5 days.

Considered and left out: the CBOE vol indices on China (VXFXI), gold miners (VXGDX), energy stocks
(VXXLE) and silver (VXSLV) stopped on 2022-02-11, and the euro index (EVZ) on 2025-03-11.

## Target and scoring

Realised vol over the next 21 trading days from daily returns (`forecast.forward_vol`). Every model is
calibrated by the same embargoed log-scale walk-forward regression (step 63 days, at least 756 rows
before the first forecast) and scored on the days where every model has a forecast. Primary metric
RMSE, secondary QLIKE, compared with a paired circular block bootstrap (63-day blocks, 2,000 draws,
seed 0). A forecast is **better** than its reference only if the whole 95% interval for the RMSE
difference is below zero, and **worse** only if it is wholly above zero.

## Models

- HAR from daily returns; HAR + IV; HAR + credit; HAR + IV + credit.
- GJR-GARCH(1,1), Student-t errors (`regimes.garch`).
- The two-state HMM implied vol (`evaluate.walk_forward_oos`).
- MS-GARCH (`regimes.msgarch`): two regimes, each a GJR-GARCH(1,1), in the Haas, Mittnik and
  Paolella (2004) form. Maximum likelihood, the multi-day forecast computed exactly. The likelihood
  matches the R package MSGARCH 2.51 to 1e-6 on a test series.
- HAR + IV + MS-GARCH, with the MS-GARCH forecast as an input, and HAR + IV + MS-GARCH prob, with its
  filtered probability of the turbulent regime as the input.

All walk-forwards refit every 63 days on an expanding window, with at least 756 days in the first fit.

## Claims (candidates until the freeze)

| Claim | Forecast | Reference | Expected |
|---|---|---|---|
| M1 | MS-GARCH | GJR-GARCH | better |
| M2 | HAR + IV + MS-GARCH | HAR + IV | better |
| M3 | MS-GARCH | Two-state HMM implied vol | better |
| M4 | HAR + IV + MS-GARCH prob | HAR + IV | better |
| C1 | HAR + IV + credit | HAR + IV | better |
| C2 | HAR + credit | HAR | better |
| R1 | HAR + IV | HAR | better |
| R2 | GJR-GARCH | HAR + IV | not better |

Verdict rules, as in the last protocol. A "better" claim is **confirmed** if it is better on at least
two counted assets and worse on none, **rejected** if it is better on none, and **mixed** otherwise.
A "not better" claim **holds** if it is better on no asset and **fails** otherwise. An asset needs at
least 750 scored days to be counted; one with fewer is reported but left out of the count.

## Development results (S&P 500)

Pending.
