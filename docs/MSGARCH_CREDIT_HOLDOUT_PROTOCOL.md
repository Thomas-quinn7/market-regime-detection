# Holdout protocol: Markov-switching GARCH and credit spreads, on oil, gold and emerging markets

**Status, 2026-10-14: frozen, not yet run.** The development results are below, with the full log in
[results/msgarch_credit_development_2026-10-14.txt](results/msgarch_credit_development_2026-10-14.txt).
The MS-GARCH variant and the claims were chosen from them and approved on 2026-10-14. No holdout data
has been loaded.

**Freeze commit: `da0cf0f`** (2026-10-14). The holdout runs `examples/msgarch_credit_holdout.py` and
the model code as of that commit.

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
  Paolella (2004) form, with Student-t errors and no lower bound on the probability of staying in a
  regime (beyond the optimiser's 0.001). Maximum likelihood from twelve starting points at the first
  refit and every fourth one after it, and the multi-day forecast computed exactly. The likelihood
  matches the R package MSGARCH 2.51 to 1e-6 on a test series, once R's handling of the first day
  is copied (R uses it only to start the variances and does not score it).
- HAR + IV + MS-GARCH, with the MS-GARCH forecast as an input, and HAR + IV + MS-GARCH prob, with its
  filtered probability of the turbulent regime as the input.

All walk-forwards refit every 63 days on an expanding window, with at least 756 days in the first fit.

## Claims

| Claim | Forecast | Reference | Expected |
|---|---|---|---|
| M1 | MS-GARCH | GJR-GARCH | better |
| M2 | HAR + IV + MS-GARCH | HAR + IV | better |
| M3 | MS-GARCH | Two-state HMM implied vol | better |
| M4 | HAR + IV + MS-GARCH prob | HAR + IV | better |
| M5 | MS-GARCH | HAR + IV | better |
| C1 | HAR + IV + credit | HAR + IV | not better |
| C2 | HAR + credit | HAR | better |
| R1 | HAR + IV | HAR | better |
| R2 | GJR-GARCH | HAR + IV | not better |

M1, M2, M3 and M5 are the questions MS-GARCH was built to answer, so they stay as "better" claims
even though only M3 was better on RMSE in development. M5 was added after the development run, since
MS-GARCH had the lowest RMSE of any model there. C1 was drafted as "better" and turned into "not
better" after development, where adding credit to HAR + IV made the forecast worse on both metrics.

Verdict rules, as in the last protocol. A "better" claim is **confirmed** if it is better on at least
two counted assets and worse on none, **rejected** if it is better on none, and **mixed** otherwise.
A "not better" claim **holds** if it is better on no asset and **fails** otherwise. An asset needs at
least 750 scored days to be counted; one with fewer is reported but left out of the count.

## Development results (S&P 500, recorded 2026-10-14, before the freeze)

S&P 500 daily returns 2000-01-04 to 2023-12-29 (6,036 days), the VIX and `BAA10Y`. Every walk-forward
had 84 refits. Scored days, common to every forecast: **4,482, from 2006-02-09 to 2023-11-29.** The
walk-forwards ran on a Linux server with the same package versions as the laptop, and the repo's
MS-GARCH and GARCH tests pass there.

| Model | RMSE | QLIKE | Pearson |
|---|---|---|---|
| HAR | 0.548 | 0.455 | 0.666 |
| HAR + IV | 0.528 | 0.417 | 0.695 |
| HAR + credit | 0.555 | 0.473 | 0.655 |
| HAR + IV + credit | 0.533 | 0.424 | 0.688 |
| GJR-GARCH | 0.531 | 0.449 | 0.697 |
| Two-state HMM implied vol | 0.661 | 0.632 | 0.450 |
| MS-GARCH | 0.518 | 0.417 | 0.716 |
| HAR + IV + MS-GARCH | 0.530 | 0.412 | 0.696 |
| HAR + IV + MS-GARCH prob | 0.523 | 0.401 | 0.700 |

| Claim | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|
| M1 MS-GARCH vs GJR-GARCH | -0.028 to +0.006 | no difference | -0.059 to -0.005 | better |
| M2 HAR + IV + MS-GARCH vs HAR + IV | -0.021 to +0.044 | no difference | -0.028 to +0.018 | no difference |
| M3 MS-GARCH vs two-state HMM | -0.253 to -0.041 | better | -0.481 to -0.023 | better |
| M4 HAR + IV + MS-GARCH prob vs HAR + IV | -0.009 to +0.002 | no difference | -0.041 to +0.002 | no difference |
| M5 MS-GARCH vs HAR + IV | -0.057 to +0.044 | no difference | -0.067 to +0.055 | no difference |
| C1 HAR + IV + credit vs HAR + IV | +0.001 to +0.011 | worse | +0.001 to +0.015 | worse |
| C2 HAR + credit vs HAR | -0.007 to +0.021 | no difference | -0.022 to +0.070 | no difference |
| R1 HAR + IV vs HAR | -0.037 to -0.005 | better | -0.078 to +0.004 | no difference |
| R2 GJR-GARCH vs HAR + IV | -0.031 to +0.042 | no difference | -0.020 to +0.079 | no difference |

**Choice of MS-GARCH variant.** Three were run on the same days:

| Variant | RMSE | QLIKE | M4 (its probability added to HAR + IV) |
|---|---|---|---|
| Student-t, no bound on staying | 0.518 | 0.417 | no difference |
| Normal, no bound on staying | 0.534 | 0.431 | no difference |
| Student-t, stay probability at least 0.5 | 0.524 | 0.425 | worse on both metrics |

The bound was tried because a fit on 2000-2009 settled on a "regime" that lasts a single day, which
makes the model a fat-tailed mixture rather than two persistent regimes. The bound did not fix that:
in 57 of the 84 refits both stay probabilities sit on an edge of the allowed range (0.5 or 0.999),
and in 81 at least one does, and it forecast worse. The Student-t variant with no bound was chosen, as the best on both metrics.

**What the fitted model is.** Without the bound the regime parameters move a long way from one refit
to the next: stay probabilities over the whole allowed range from 0.001 to 0.999, Student-t degrees
of freedom from 2.05 (the lower limit) to about two million (which is a normal distribution), and in
some refits the regimes swap roles. On S&P 500 returns MS-GARCH works as a flexible
mix of two GARCH variances, not as two stable market regimes. So the holdout tests it as a
forecaster, and M4 is a weak test of the regime idea, because the probability it uses does not mean
the same thing from one refit to the next.

**Power.** The target is realised vol from daily returns, so the intervals are wide. M5's RMSE
interval runs from -0.057 to +0.044 around an RMSE of about 0.52, so only differences of roughly 10%
would show. M3 is the only claim whose development effect is that large. A "no difference" in the
holdout will mostly mean the test could not tell, and the write-up has to say so.

## Running it

The holdout runs `examples/msgarch_credit_holdout.py` once, with no flag, at the freeze commit, on the
same Linux server as development (the laptop does not have the memory for it). Its walk-forwards are
cached as they finish (`data/checkpoints/msgarch_credit/`, local only), so if the run is killed before
any metric prints it is restarted and picks up the cached walk-forwards; that would be recorded here.
A bug found after results print is reported, not fixed and rerun.

Dry run, 2026-10-14: `--dry-run` puts the S&P 500 development data through the same loaders,
`evaluate_asset` and verdict code (with the VIX from FRED `VIXCLS` rather than Yahoo). It gave the
same 4,482 scored days and the same RMSE, QLIKE and intervals as the development table above, to the
printed precision. The last MS-GARCH fit differed in the third or fourth decimal (stay probability
0.3090 against 0.3096), most likely because the dry run reads a separately downloaded copy of the
S&P 500 prices, whose adjusted closes differ very slightly.
