# Plan: QLIKE on variance forecasts, and a Giacomini-White conditional test (November 2026)

Class of everything this plan produces: **post hoc, computed from the spent holdouts' reproduced
forecasts; not a registered test**. No registered verdict changes. No new data is opened: the inputs
are the scored tables and walk-forward outputs under `docs/results/reproductions/`, the frozen ETF
checkpoints in `data/checkpoints/msgarch_credit/`, and the data caches the frozen holdout scripts
already read. This file is committed before either analysis is run; anything decided after a result
is seen is reported as such in the results file.

Asked for by Thomas on 2026-11-02, from the review of WRITEUP.md that day and the 2026-10-25 panel
review (E1.1 for the QLIKE point, E1.3 for the conditional test).

## 1. QLIKE scored on a variance forecast

**Problem.** Every calibrated forecast is `exp(fit + s^2/2)` (`regimes.forecast.walk_forward_regression`,
`log_target=True`), the lognormal mean of next-month vol. QLIKE (`regimes.forecast.qlike`) is a loss on
variance and is consistent for the conditional mean of the squared target, but it is fed the square of
the mean-vol forecast, `exp(2 fit + s^2)`. Under the same lognormal model the mean of the variance is
`exp(2 fit + 2 s^2)`, so every QLIKE forecast is too low by the factor `exp(s^2)`, with `s^2` the
training residual variance of that forecast's own regression. Forecasts with larger residual variance
are pushed further down, so the bias is not the same for every model and can move comparisons.

**Method.** `examples/variance_rescore.py` runs each holdout's frozen script unchanged through
`examples/reproduce_holdout.py` (VIX 1990-2004, VIX 2024-2026, cross-index, and the ETF holdout from
its frozen checkpoints with `--use-checkpoints`), into a scratch output folder so the committed
reproductions are not overwritten. Every call to `walk_forward_regression` is wrapped: a twin repeats
the identical fit (same rows, embargo, refit dates and `lstsq` call) and returns, for `log_target=True`,
the mean-vol forecast and the variance forecast `max(exp(2 fit + 2 s^2), floor^2)`. For a level fit
(`log_target=False`), if any, the variance forecast is `max(pred, floor)^2 + s^2` and the call is
listed.

**Identity checks (the analysis stops if either fails).** (i) The twin's mean-vol forecast equals the
original's forecast exactly on every row of every call. (ii) Each column of each committed scored table
under `docs/results/reproductions/<holdout>/scored/` is matched to exactly one captured regression
forecast that equals it on every scored day; a column with no exact match is reported and left out.

**Scoring.** For each registered claim and each asset or period, QLIKE on the variance forecast,
`y^2/v - log(y^2/v) - 1`, with the same paired circular block bootstrap as `docs/POSTHOC_2026-10.md`
(63-day blocks, 2,000 draws, seed 0, `regimes.posthoc.paired_interval`), the same verdict rule (better
if the interval is wholly below zero, worse if wholly above) and the same claim rules
(`cross_index_holdout.claim_verdict` for the cross-index and ETF claims; the VIX holdout's three claims
as in `posthoc_stats.vix_claim_outcomes`).

**What is reported.** Per claim: the outcome under RMSE (registered), under QLIKE as `POSTHOC` computed
it, and under QLIKE on the variance forecast; every per-asset verdict that changes between the last two;
the size of `exp(s^2)` per forecast (median over refits). Reading rule, fixed now: the variance version
is the correct QLIKE for these forecasts, so where the two QLIKE columns disagree the paper should
quote the variance version and say the earlier POSTHOC QLIKE column was biased. RMSE stays on the
mean-vol forecast, which is the right target for a loss on vol.

## 2. Giacomini-White conditional predictive ability test

**Question.** The unconditional comparisons ask whether a regime-based forecast is better on average.
The conditional test asks whether its relative loss depends on the state the HMM reports, i.e. whether
it does better when the model says "stressed". This is the one test in the repo that could show when
the regime model helps even where it does not help on average.

**Pairs, fixed now (forecast minus reference; a negative loss difference favours the first).**

| Block | G1: regime term added to the benchmark | G2: the regime model's own forecast |
|---|---|---|
| Cross-index, each of Nasdaq-100, Dow, Russell 2000 | HAR-RV + IV + HMM prob vs HAR-RV + IV | Two-state HMM implied vol vs HAR-RV + IV |
| ETF holdout, each of oil, gold, EM, Brazil | HAR + IV + MS-GARCH prob vs HAR + IV | Two-state HMM implied vol vs HAR + IV |
| S&P 500 VIX holdouts, 1996-2004 and 2024-2026 | HAR + VIX + HMM prob vs HAR + VIX | HMM implied vol vs HAR + VIX |

Nine blocks by two pairs: 18 tests per loss.

**Conditioning variable.** `p_t`, the walk-forward two-state HMM's filtered high-vol probability on the
forecast date t (returns up to t, parameters estimated before the block), for the same asset:
`walk_forward_oos` outputs in the reproductions for the cross-index and VIX holdouts, the frozen
`__hmm__` checkpoint's `high_vol_prob` for the ETFs. It is known when the forecast is made. Instruments
`h_t = (1, p_t)`.

**Test.** `d_t` = loss of the first forecast minus loss of the reference for the target over
(t, t + 21]. `Z_t = h_t d_t`; statistic `T * Zbar' Omega^-1 Zbar`, chi-squared with 2 degrees of
freedom, `Omega` the Newey-West covariance of `Z_t` with 20 lags and Bartlett weights (the overlap of
21-day targets; the same lag as POSTHOC's DM tests). Losses: squared error on vol and QLIKE as POSTHOC
computes it are the primary pair (36 tests); QLIKE on the variance forecast from part 1 is a secondary
column. Also reported, to read the direction: the OLS fit of `d_t` on `(1, p_t)` with Newey-West
standard errors, as the fitted loss difference at `p = 0` and at `p = 1` with 95% intervals.

**Multiplicity.** Holm at 5% across the 36 primary tests; raw p-values are printed beside it.

**Reading rule, fixed now.** A test that survives Holm, with a fitted loss difference at `p = 1` whose
interval is wholly below zero, is read as "the regime-based forecast is more accurate when the HMM
reports stress, on this spent holdout". It is a lead, not a claim. It could only become a claim on a
new holdout registered in advance (none can be opened before the 31 January 2027 gate). A rejection
whose direction favours the reference in stress is reported the same way. A test that does not reject is
not read as proof that there is no state dependence; the power is limited, as in POWER_2026-10.md.

**Known limits, stated before the run.** Giacomini and White's asymptotics assume a rolling estimation
window; these forecasts use expanding windows, so the chi-squared reference is approximate. The
conditioning variable is itself a model output from the same returns. The blocks are not independent
(the three indices share crises, as do EM and Brazil).

## Amendment A1 (2026-11-02, before the test was run on any holdout forecast)

A simulation check of the test written above, run on synthetic data only, found it badly oversized:
with losses that overlap over 21 days (a flat MA(20), Student-t(5) shocks) and a persistent
conditioning variable independent of them, the Bartlett 20-lag version rejects 16.6%, 15.8% and 12.2%
of the time at a nominal 5% for 676, 2,228 and 3,300 days (500 draws each). Bartlett weights with a
bandwidth equal to the overlap understate the long-run variance of an MA(20) by about a third. Wider
Bartlett windows (42, 63, 126 lags) did not fix it (8.4% to 19.4%). The truncated (rectangular) kernel
with 20 lags, the usual choice for h-step forecasts, gave 7.4%, 5.4% and 5.2%, and its covariance was
positive definite in every draw.

Changes: (i) the GW statistic and the intervals of the direction regression use the rectangular
kernel with 20 lags; if its covariance is not positive definite for a block, Bartlett with 63 lags is
used there and the block is listed. (ii) The Bartlett 20-lag p-value is still printed beside it, as
the originally planned version, and is not used for any reading. (iii) The simulation is part of the
results. (iv) The same flaw applies to the Bartlett 20-lag DM tests in docs/POSTHOC_2026-10.md; the
results file says so and gives their rectangular-kernel equivalents for the same pairs, as a note, not
as a change to POSTHOC. Everything else in part 2 stands.

## Outputs

`examples/variance_rescore.py` and `examples/gw_conditional.py`; results in
`docs/GW_QLIKE_2026-11.md` with the captured variance forecasts under
`docs/results/variance_rescore/<holdout>/`. Nothing in WRITEUP.md or README.md is edited.
