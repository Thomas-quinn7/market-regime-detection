# Holdout protocol: better volatility models, on the Nasdaq-100, the Dow and the Russell 2000

**Status, 2026-10-14: frozen, not yet run.** The claims run as written, all at the 21-day horizon.
The open question at the draft stage was whether to add 1-day versions of P1 and P2, since HARQ and
SHAR are built to help most at short horizons. A development check on the S&P 500 (below) found no
difference at 1 or 5 days either, so no 1-day claim was added. **1-day horizons are not tested by this
holdout.**

Written and committed **before** any holdout data was loaded. On 2026-10-13 the futures bars below
were downloaded from Databento and their file listings and job metadata were read; no price in them
has been read. No Nasdaq-100, Dow or Russell 2000 index level and none of their implied-vol indices
(VXN, VXD, RVX) has ever been loaded by this repo. The only related data used before is the nine
sector ETFs for 2005-2023, used to label regimes and never for volatility forecasting.

Each index is run once. Whatever it gives is the result, and a bug found after the run is reported
as a bug, not silently fixed and rerun.

## Why this holdout

Both S&P 500 holdouts in [VIX_HOLDOUT_PROTOCOL.md](VIX_HOLDOUT_PROTOCOL.md) are used. The next round of
work tries models that should forecast volatility better than HAR + VIX, and one regime model built
for the failure found in the write-up ("Why it loses": the two-state HMM's forecast is stuck between
two levels, while volatility moves continuously). All of it is developed on S&P 500 data, so it has
to be confirmed on other markets.

Caveat, stated in advance: these three indices move closely with the S&P 500 and share its crises
(2011, 2015, 2018, 2020, 2022), so this tests whether a result carries over to other US equity
indices. It is not an independent history.

## Two stages

1. **Development, S&P 500 only.** ES futures bars June 2010 to 2023 and S&P 500 daily returns, the
   same data as `examples/intraday_rv.py`. Model details (exact HARQ form, MSM component count, GARCH
   variant) may be tuned here. The S&P 500 2024-2026 data is not used, as it is a spent holdout.
2. **Freeze, then run.** Before any holdout file is opened, one commit adds the holdout script and
   final model code, and this file gets a line recording that commit's hash, which is pushed. The
   claims and comparisons below cannot change at the freeze, only the model details within each
   named model.

## Data

| Index | Intraday futures (session RV) | Daily returns | Implied vol |
|---|---|---|---|
| Nasdaq-100 | NQ.v.0, R2 download, 2010-06-07 to 2026-10-12 | `^NDX`, Yahoo | VXN, FRED `VXNCLS` |
| Dow Jones Industrial Average | YM.v.0, R2 download, 2010-06-07 to 2026-10-12 | `^DJI`, Yahoo | VXD, FRED `VXDCLS` |
| Russell 2000 | RTY.v.0, R4 download, 2017-07-10 to 2026-10-12 | `^RUT`, Yahoo | RVX, FRED `RVXCLS` |

- Session realised vol exactly as for the S&P 500: `regimes.intraday.daily_realised_vol`, 09:30 to
  16:00 New York time, five-minute returns, the session's main instrument by volume. Days Databento
  flags as degraded are kept when they have bars and left missing when they do not.
- The trading calendar is each index's Yahoo daily series. Futures sessions on other days (US
  holidays) are dropped.
- Daily-return models (HAR from daily returns, GARCH, the HMM, MSM) may train on index returns from
  2000-01-01, since a forecaster at the start of the intraday window would have had them.
- An implied-vol value missing for up to 5 days is carried forward; longer gaps are left missing.
  If an index ends up with fewer than 750 scored days, it is reported but left out of the claim
  count below.

## Target and scoring

Target: next-21-day session realised vol, `sqrt(mean(RV^2))` over days t+1 to t+21. Every forecast
is calibrated by `forecast.walk_forward_regression` (`horizon=21`, `step=63`, `min_rows=756`,
`log_target=True`, vol inputs logged), every feature set is restricted to the same rows, and all
forecasts are scored on the same days. Primary metric RMSE, secondary QLIKE. Each comparison gets a
paired circular block-bootstrap 95% interval for the difference (63-day blocks, 2,000 draws, seed
0). A forecast **beats** its reference only if the whole RMSE interval is below zero, and is
**worse** only if it is wholly above zero.

## Models

Fixed now by name; the details are fixed at the freeze commit.

- **HAR**: HAR inputs from daily index returns.
- **HAR-RV**: HAR inputs from session RV (`rv_1d`, 5-day and 22-day RMS).
- **IV**: the index's own implied vol (VXN, VXD or RVX), logged and scaled to daily.
- **HAR-RV + IV**: the reference model, the best on the S&P 500 so far.
- **HARQ + IV** (Bollerslev, Patton and Quaedvlieg 2016): HAR-RV + IV, with the weight on yesterday's
  RV allowed to fall when realised quarticity says it was measured imprecisely.
- **SHAR + IV** (Patton and Sheppard 2015): HAR-RV + IV, with yesterday's RV split into downside and
  upside semivariance.
- **GJR-GARCH**: GJR-GARCH(1,1) on daily index returns, walk-forward, refit every 63 days, its own
  21-day vol forecast as the input.
- **MSM** (Calvet and Fisher 2004): binomial Markov-switching multifractal on daily index returns,
  walk-forward, refit every 63 days, its own 21-day vol forecast as the input. The number of
  components is chosen on the S&P 500 and frozen.
- **Two-state HMM**: `evaluate.walk_forward_oos`, as everywhere in this repo; its implied vol and
  high-vol probability.
- **Combination**: the equal-weight average of the calibrated HAR-RV + IV, GJR-GARCH and MSM
  forecasts.

Nothing else will be tried on the holdout.

## Claims

Per index, each comparison is judged on RMSE as above. A "better" claim is **confirmed** if it is
better on at least two of the three indices and worse on none, **rejected** if it is better on none,
and **mixed** otherwise. A "not better" claim **holds** if it is better on no index.

New models, the point of this round:

| # | Forecast | Reference | Claim |
|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | better |
| P2 | SHAR + IV | HAR-RV + IV | better |
| P3 | HAR-RV + IV + MSM | HAR-RV + IV | better |
| P4 | Combination | HAR-RV + IV | better |
| P5 | MSM | Two-state HMM implied vol | better (the regime-structure claim) |

Replications of what the S&P 500 already showed:

| # | Forecast | Reference | Claim |
|---|---|---|---|
| R1 | HAR-RV + IV | HAR-RV | better (implied vol adds to intraday data) |
| R2 | HAR-RV | HAR | better (intraday data beats daily returns) |
| R3 | HAR-RV + IV + two-state HMM probability | HAR-RV + IV | not better |
| R4 | GJR-GARCH | HAR-RV + IV | not better |

Nine claims on three indices is a lot of comparisons, which is why a "better" claim needs two of three
indices. P1 to P5 are the ones the development work is aimed at, and whichever way they go is the
headline. Development results for every claim will be recorded in this file at the freeze, before
the holdout is run.

## Development results (S&P 500, recorded 2026-10-13, before the freeze)

`examples/better_vol_models.py`, ES session RV and `^GSPC` returns from 2000, VIX as IV. 2,589 scored
days, 2013-08-01 to 2023-11-29. RMSE of next-21-day session RV:

| Forecast | RMSE | QLIKE |
|---|---|---|
| HAR | 0.358 | 0.391 |
| HAR-RV | 0.341 | 0.375 |
| HAR-RV + IV | **0.334** | **0.358** |
| HARQ + IV | 0.334 | 0.358 |
| SHAR + IV | 0.334 | 0.358 |
| GJR-GARCH | 0.343 | 0.381 |
| MSM | 0.365 | 0.432 |
| Two-state HMM implied vol | 0.378 | 0.456 |
| HAR-RV + IV + MSM | 0.335 | 0.358 |
| HAR-RV + IV + HMM prob | 0.334 | 0.359 |
| Combination | 0.341 | 0.372 |

| Claim | RMSE interval | Development verdict |
|---|---|---|
| P1 HARQ + IV vs HAR-RV + IV | -0.000 to +0.000 | no difference |
| P2 SHAR + IV vs HAR-RV + IV | -0.000 to +0.000 | no difference |
| P3 HAR-RV + IV + MSM vs HAR-RV + IV | -0.001 to +0.003 | no difference |
| P4 Combination vs HAR-RV + IV | -0.001 to +0.014 | no difference |
| P5 MSM vs two-state HMM | -0.032 to +0.007 | no difference (point estimate favours MSM) |
| R1 HAR-RV + IV vs HAR-RV | -0.011 to -0.001 | better, as claimed |
| R2 HAR-RV vs HAR | -0.031 to -0.003 | better, as claimed |
| R3 + HMM prob vs HAR-RV + IV | -0.001 to +0.002 | not better, as claimed |
| R4 GJR-GARCH vs HAR-RV + IV | +0.001 to +0.022 | worse, so not better, as claimed |

Notes from development:

- HARQ and SHAR forecasts differ from HAR-RV + IV by about 0.3% on average. The terms are fitted
  and HARQ's has the expected sign (-0.115 on the last refit), but at a 21-day horizon yesterday's RV
  carries a weight of about 0.12 against about 0.54 for IV, so there is little for them to change.
- MSM components: k = 4, the smallest k whose 2000-2009 log-likelihood is within 2 points of the
  best for k = 1 to 8 (k = 4 to 8 all lie within 1.3 points). A single-start Nelder-Mead fit stalled
  (gamma_k stuck at its start, k = 4 short by 28 points), so fits use twelve starts with L-BFGS-B.
- MSM loses to GJR-GARCH here (0.365 against 0.343).
- Short horizons, checked 2026-10-14 (`examples/harq_short_horizon.py`, HAR family only, same
  walk-forward and bootstrap). At 1 day (2,626 days), HARQ + IV has RMSE 0.2618 against 0.2631 for
  HAR-RV + IV, interval -0.0031 to +0.0007; SHAR + IV -0.0005 to +0.0010. At 5 days both intervals
  sit within 0.001 of zero. HARQ's point estimate is about 0.5% better at 1 day, but the interval
  spans zero, so adding 1-day claims would have spent two more comparisons on expected nulls.

## Running it

`examples/cross_index_holdout.py` runs each index through `evaluate_index` from
`examples/better_vol_models.py`, unchanged, then applies the claim rules above. Index returns are
loaded to 2026-10-12, the last day of the futures downloads. `--dry-run` sends the S&P 500
development data (ES bars, `^GSPC`, FRED `VIXCLS`, to 2023) through the same loaders and verdict code,
to test the script without opening a holdout file; it is not a result. Two points the claim rules
leave implicit, fixed here at the freeze: a "not better" claim that is better on any counted index
**fails**, and if an index falls below 750 scored days, "at least two" still means two counted
indices.

## Power

NQ and YM should give about 3,300 scored days each (mid-2013 to September 2026, after the 22-day HAR
window and three years of calibration). RTY starts in July 2017, so it gives about 1,500 (mid-2020
to September 2026), and its intervals will be wider.
