development data only (S&P 500, 2005-2023), no holdout, not a claim

# Development-only horizons 5 to 126 days (and 252, descriptive), October 2026

Class of every table in this file: **development data only (S&P 500, 2005-2023), no holdout, not a claim**. Written by `examples/dev_horizons.py` at 2c31339 plus uncommitted files, 2026-10-18 11:59Z, 2,000 bootstrap draws (seed 0). Data: S&P 500 returns and the VIX, VIX9D and VIX6M closes 2005-01-04 to 2023-12-29 (4780 days) from the committed caches. Stage S8 (a) of the reopen.

Design (S4a's, `examples/dev_continuations.py`): target = realised vol over the next h days; expanding OLS on log HAR inputs plus the listed regressors, log target, refit every 63 rows after 756, embargo h; paired circular block bootstrap with block = max(63, h). The HMM is the two-state walk-forward model (min_train 756, step 63), refit for each horizon. Two changes from S4a: the implied vol matches the horizon (VIX9D at 5 and 10 days, VIX at 21 and 63, VIX6M at 126; the VIX is shown beside it), and every feature set at a horizon is fitted on the same rows, the dates where all of that horizon's inputs exist (desk finding 6), so the 21- and 63-day numbers differ slightly from S4a's. VIX9D starts 2011-01-03 and VIX6M 2008-01-02, so the 5-, 10- and 126-day samples are shorter. *windows* = scored days / h, the number of non-overlapping targets.

## Horizon 5

Scored days 2,504, 2014-01-13 to 2023-12-21; non-overlapping windows 500; implied vol VIX9D; first feature row 2011-01-03; HMM refits 64, converged 64 of 64.

| model | RMSE | QLIKE |
|---|---|---|
| HAR | 0.574 | 0.624 |
| HAR + VIX9D | 0.475 | 0.443 |
| HAR + VIX9D + HMM prob | 0.476 | 0.440 |
| HAR + VIX9D + noise | 0.475 | 0.443 |
| HAR + VIX | 0.504 | 0.463 |
| HAR + VIX + HMM prob | 0.504 | 0.462 |

| h | forecast | reference | block | windows | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|---|---|
| 5 | HAR + VIX9D | HAR | 63 | 500 | -0.187 to -0.022 | better | -0.271 to -0.109 | better |
| 5 | HAR + VIX9D + HMM prob | HAR + VIX9D | 63 | 500 | -0.005 to +0.007 | no difference | -0.010 to +0.002 | no difference |
| 5 | HAR + VIX9D + noise | HAR + VIX9D | 63 | 500 | -0.000 to +0.000 | no difference | +0.000 to +0.000 | worse |
| 5 | HAR + VIX | HAR | 63 | 500 | -0.151 to +0.009 | no difference | -0.251 to -0.089 | better |
| 5 | HAR + VIX + HMM prob | HAR + VIX | 63 | 500 | -0.006 to +0.006 | no difference | -0.006 to +0.003 | no difference |
| 5 | HAR + VIX9D | HAR + VIX | 63 | 500 | -0.047 to -0.007 | better | -0.042 to +0.000 | no difference |

## Horizon 10

Scored days 2,494, 2014-01-21 to 2023-12-14; non-overlapping windows 249; implied vol VIX9D; first feature row 2011-01-03; HMM refits 64, converged 64 of 64.

| model | RMSE | QLIKE |
|---|---|---|
| HAR | 0.545 | 0.519 |
| HAR + VIX9D | 0.459 | 0.385 |
| HAR + VIX9D + HMM prob | 0.461 | 0.384 |
| HAR + VIX9D + noise | 0.459 | 0.386 |
| HAR + VIX | 0.480 | 0.398 |
| HAR + VIX + HMM prob | 0.481 | 0.397 |

| h | forecast | reference | block | windows | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|---|---|
| 10 | HAR + VIX9D | HAR | 63 | 249 | -0.159 to -0.014 | better | -0.223 to -0.061 | better |
| 10 | HAR + VIX9D + HMM prob | HAR + VIX9D | 63 | 249 | -0.004 to +0.010 | no difference | -0.008 to +0.005 | no difference |
| 10 | HAR + VIX9D + noise | HAR + VIX9D | 63 | 249 | -0.001 to +0.001 | no difference | -0.001 to +0.003 | no difference |
| 10 | HAR + VIX | HAR | 63 | 249 | -0.131 to +0.007 | no difference | -0.218 to -0.039 | better |
| 10 | HAR + VIX + HMM prob | HAR + VIX | 63 | 249 | -0.005 to +0.007 | no difference | -0.007 to +0.004 | no difference |
| 10 | HAR + VIX9D | HAR + VIX | 63 | 249 | -0.037 to -0.003 | better | -0.040 to +0.013 | no difference |

## Horizon 21

Scored days 3,226, 2011-02-04 to 2023-11-29; non-overlapping windows 153; implied vol VIX; first feature row 2008-01-07; HMM refits 64, converged 64 of 64.

| model | RMSE | QLIKE |
|---|---|---|
| HAR | 0.511 | 0.457 |
| HAR + VIX | 0.481 | 0.433 |
| HAR + VIX + HMM prob | 0.484 | 0.441 |
| HAR + VIX + noise | 0.482 | 0.435 |

| h | forecast | reference | block | windows | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|---|---|
| 21 | HAR + VIX | HAR | 63 | 153 | -0.049 to -0.013 | better | -0.079 to +0.041 | no difference |
| 21 | HAR + VIX + HMM prob | HAR + VIX | 63 | 153 | -0.004 to +0.012 | no difference | -0.009 to +0.032 | no difference |
| 21 | HAR + VIX + noise | HAR + VIX | 63 | 153 | -0.000 to +0.001 | no difference | -0.001 to +0.005 | no difference |

## Horizon 63

Scored days 3,142, 2011-04-06 to 2023-09-29; non-overlapping windows 49; implied vol VIX; first feature row 2008-01-07; HMM refits 64, converged 64 of 64.

| model | RMSE | QLIKE |
|---|---|---|
| HAR | 0.532 | 0.563 |
| HAR + VIX | 0.520 | 0.545 |
| HAR + VIX + HMM prob | 0.526 | 0.553 |
| HAR + VIX + noise | 0.521 | 0.547 |

| h | forecast | reference | block | windows | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|---|---|
| 63 | HAR + VIX | HAR | 63 | 49 | -0.025 to -0.002 | better | -0.047 to +0.009 | no difference |
| 63 | HAR + VIX + HMM prob | HAR + VIX | 63 | 49 | -0.005 to +0.021 | no difference | -0.016 to +0.038 | no difference |
| 63 | HAR + VIX + noise | HAR + VIX | 63 | 49 | +0.000 to +0.001 | worse | -0.000 to +0.005 | no difference |

## Horizon 126

Scored days 3,016, 2011-07-07 to 2023-06-30; non-overlapping windows 23; implied vol VIX6M; first feature row 2008-01-07; HMM refits 64, converged 64 of 64.

| model | RMSE | QLIKE |
|---|---|---|
| HAR | 0.538 | 0.532 |
| HAR + VIX6M | 0.599 | 0.578 |
| HAR + VIX6M + HMM prob | 0.586 | 0.559 |
| HAR + VIX6M + noise | 0.599 | 0.578 |
| HAR + VIX | 0.550 | 0.530 |
| HAR + VIX + HMM prob | 0.546 | 0.521 |

| h | forecast | reference | block | windows | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|---|---|
| 126 | HAR + VIX6M | HAR | 126 | 23 | +0.006 to +0.135 | worse | -0.002 to +0.104 | no difference |
| 126 | HAR + VIX6M + HMM prob | HAR + VIX6M | 126 | 23 | -0.033 to +0.009 | no difference | -0.045 to +0.005 | no difference |
| 126 | HAR + VIX6M + noise | HAR + VIX6M | 126 | 23 | +0.000 to +0.001 | worse | -0.000 to +0.001 | no difference |
| 126 | HAR + VIX | HAR | 126 | 23 | -0.008 to +0.037 | no difference | -0.028 to +0.023 | no difference |
| 126 | HAR + VIX + HMM prob | HAR + VIX | 126 | 23 | -0.021 to +0.015 | no difference | -0.033 to +0.013 | no difference |
| 126 | HAR + VIX6M | HAR + VIX | 126 | 23 | +0.004 to +0.111 | worse | +0.007 to +0.094 | worse |

## Horizon 252 (descriptive only)

Scored days 2,764, 2012-01-05 to 2022-12-28; non-overlapping windows 10; implied vol VIX; first feature row 2008-01-07; HMM refits 64, converged 64 of 64.

| model | RMSE | QLIKE |
|---|---|---|
| HAR | 0.535 | 0.469 |
| HAR + VIX | 0.568 | 0.491 |
| HAR + VIX + HMM prob | 0.543 | 0.476 |
| HAR + VIX + noise | 0.570 | 0.492 |

No interval and no verdict at h = 252: there is no cached one-year implied vol (the VIX, a one-month index, stands in), the sample holds 10 non-overlapping windows, and a one-year realised-vol target is mostly mean reversion, a different question from the paper's one-month VIX question.

## Summary: the regime-probability question at each horizon

Class: development data only (S&P 500, 2005-2023), no holdout, not a claim. HAR + matching IV + HMM prob against HAR + matching IV, beside the noise row and the matching IV's own gain over HAR.

| h | IV | windows | HMM prob dRMSE | HMM prob dQLIKE | noise dRMSE | noise dQLIKE | IV vs HAR dRMSE |
|---|---|---|---|---|---|---|---|
| 5 | VIX9D | 500 | -0.005 to +0.007 (no difference) | -0.010 to +0.002 (no difference) | -0.000 to +0.000 (no difference) | +0.000 to +0.000 (worse) | -0.187 to -0.022 (better) |
| 10 | VIX9D | 249 | -0.004 to +0.010 (no difference) | -0.008 to +0.005 (no difference) | -0.001 to +0.001 (no difference) | -0.001 to +0.003 (no difference) | -0.159 to -0.014 (better) |
| 21 | VIX | 153 | -0.004 to +0.012 (no difference) | -0.009 to +0.032 (no difference) | -0.000 to +0.001 (no difference) | -0.001 to +0.005 (no difference) | -0.049 to -0.013 (better) |
| 63 | VIX | 49 | -0.005 to +0.021 (no difference) | -0.016 to +0.038 (no difference) | +0.000 to +0.001 (worse) | -0.000 to +0.005 (no difference) | -0.025 to -0.002 (better) |
| 126 | VIX6M | 23 | -0.033 to +0.009 (no difference) | -0.045 to +0.005 (no difference) | +0.000 to +0.001 (worse) | -0.000 to +0.001 (no difference) | +0.006 to +0.135 (worse) |

