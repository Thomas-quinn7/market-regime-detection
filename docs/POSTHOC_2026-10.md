# Post-hoc statistics from the reproduced holdout forecasts, October 2026

Class of every table in this file: **post hoc, computed from the reproduced forecasts; not a registered test**. The registered verdicts are the RMSE verdicts in `docs/results/cross_index_holdout_2026-10-14.txt`, `docs/results/msgarch_credit_holdout_2026-10-14.txt` and the VIX tables in `docs/WRITEUP.md`; nothing here changes them, and no sentence here says a reproduction confirms or re-tests a claim.

Written by `examples/posthoc_stats.py` at 7ee241f plus uncommitted files, 2026-10-17 20:59Z, with 2,000 bootstrap draws (seed 0). Inputs: the scored forecast tables under `docs/results/reproductions/<holdout>/scored/` written by `examples/reproduce_holdout.py` on 2026-10-17 (the exact forecasts and target the frozen scripts scored; the ETF tables are the frozen MS-GARCH, GJR and HMM checkpoints re-scored, which the S1 reproduction showed identical to the committed file), the saved walk-forward implied vols beside them, and the data caches listed in `data/MANIFEST.md`. A laptop draft of tables (a) and (b) from the printed 3-decimal intervals (`QLIKE_EQUIVALENCE_TABLES_DRAFT_2026-10-17.md`, desk review) widened each bound by 0.0005; the bounds here use the unrounded interval ends and are therefore a little tighter.

Desk and panel items this answers: panel item 4 and ranked items 2-4 (HAC DM, MCS, equivalence bounds, block length), desk findings 3, 6, 7 and 9 of `HMM_DESK_REVIEW_2026-10-17.md` (QLIKE beside RMSE, own-row calibration, raw vs recalibrated, what the null is entitled to), and the unregistered HMM-vs-HAR + VIX comparison of desk finding 1.

## Identity check: the registered intervals recomputed from the saved tables

Class: reproduction. Each registered RMSE and QLIKE interval (63-day circular blocks, 2,000 draws, seed 0) recomputed from the scored table and compared, as printed text, with the committed result file (cross-index, ETF) or the reproduction's stdout (VIX, whose intervals match `docs/WRITEUP.md`, see `examples/check_writeup_tables.py`). The last two lines check that the own-row recalibration in (g) reproduces the registered VIX forecasts from the saved HMM outputs.

Result: 79 of 79 identical, 0 differ.

```
Cross-index holdout | Nasdaq-100 | P1 | identical
Cross-index holdout | Nasdaq-100 | P2 | identical
Cross-index holdout | Nasdaq-100 | P3 | identical
Cross-index holdout | Nasdaq-100 | P4 | identical
Cross-index holdout | Nasdaq-100 | P5 | identical
Cross-index holdout | Nasdaq-100 | R1 | identical
Cross-index holdout | Nasdaq-100 | R2 | identical
Cross-index holdout | Nasdaq-100 | R3 | identical
Cross-index holdout | Nasdaq-100 | R4 | identical
Cross-index holdout | Dow Jones Industrial Average | P1 | identical
Cross-index holdout | Dow Jones Industrial Average | P2 | identical
Cross-index holdout | Dow Jones Industrial Average | P3 | identical
Cross-index holdout | Dow Jones Industrial Average | P4 | identical
Cross-index holdout | Dow Jones Industrial Average | P5 | identical
Cross-index holdout | Dow Jones Industrial Average | R1 | identical
Cross-index holdout | Dow Jones Industrial Average | R2 | identical
Cross-index holdout | Dow Jones Industrial Average | R3 | identical
Cross-index holdout | Dow Jones Industrial Average | R4 | identical
Cross-index holdout | Russell 2000 | P1 | identical
Cross-index holdout | Russell 2000 | P2 | identical
Cross-index holdout | Russell 2000 | P3 | identical
Cross-index holdout | Russell 2000 | P4 | identical
Cross-index holdout | Russell 2000 | P5 | identical
Cross-index holdout | Russell 2000 | R1 | identical
Cross-index holdout | Russell 2000 | R2 | identical
Cross-index holdout | Russell 2000 | R3 | identical
Cross-index holdout | Russell 2000 | R4 | identical
MS-GARCH and credit holdout | Crude oil (USO) | M1 | identical
MS-GARCH and credit holdout | Crude oil (USO) | M2 | identical
MS-GARCH and credit holdout | Crude oil (USO) | M3 | identical
MS-GARCH and credit holdout | Crude oil (USO) | M4 | identical
MS-GARCH and credit holdout | Crude oil (USO) | M5 | identical
MS-GARCH and credit holdout | Crude oil (USO) | C1 | identical
MS-GARCH and credit holdout | Crude oil (USO) | C2 | identical
MS-GARCH and credit holdout | Crude oil (USO) | R1 | identical
MS-GARCH and credit holdout | Crude oil (USO) | R2 | identical
MS-GARCH and credit holdout | Gold (GLD) | M1 | identical
MS-GARCH and credit holdout | Gold (GLD) | M2 | identical
MS-GARCH and credit holdout | Gold (GLD) | M3 | identical
MS-GARCH and credit holdout | Gold (GLD) | M4 | identical
MS-GARCH and credit holdout | Gold (GLD) | M5 | identical
MS-GARCH and credit holdout | Gold (GLD) | C1 | identical
MS-GARCH and credit holdout | Gold (GLD) | C2 | identical
MS-GARCH and credit holdout | Gold (GLD) | R1 | identical
MS-GARCH and credit holdout | Gold (GLD) | R2 | identical
MS-GARCH and credit holdout | Emerging markets (EEM) | M1 | identical
MS-GARCH and credit holdout | Emerging markets (EEM) | M2 | identical
MS-GARCH and credit holdout | Emerging markets (EEM) | M3 | identical
MS-GARCH and credit holdout | Emerging markets (EEM) | M4 | identical
MS-GARCH and credit holdout | Emerging markets (EEM) | M5 | identical
MS-GARCH and credit holdout | Emerging markets (EEM) | C1 | identical
MS-GARCH and credit holdout | Emerging markets (EEM) | C2 | identical
MS-GARCH and credit holdout | Emerging markets (EEM) | R1 | identical
MS-GARCH and credit holdout | Emerging markets (EEM) | R2 | identical
MS-GARCH and credit holdout | Brazil (EWZ) | M1 | identical
MS-GARCH and credit holdout | Brazil (EWZ) | M2 | identical
MS-GARCH and credit holdout | Brazil (EWZ) | M3 | identical
MS-GARCH and credit holdout | Brazil (EWZ) | M4 | identical
MS-GARCH and credit holdout | Brazil (EWZ) | M5 | identical
MS-GARCH and credit holdout | Brazil (EWZ) | C1 | identical
MS-GARCH and credit holdout | Brazil (EWZ) | C2 | identical
MS-GARCH and credit holdout | Brazil (EWZ) | R1 | identical
MS-GARCH and credit holdout | Brazil (EWZ) | R2 | identical
S&P 500, 1996-2004 VIX holdout | S&P 500, 1996-2004 | 1 | identical
S&P 500, 1996-2004 VIX holdout | S&P 500, 1996-2004 | 2 | identical
S&P 500, 1996-2004 VIX holdout | S&P 500, 1996-2004 | 3 | identical
S&P 500, 1996-2004 VIX holdout | S&P 500, 1996-2004 | 4 | identical
S&P 500, 1996-2004 VIX holdout | S&P 500, 1996-2004 | 5 | identical
S&P 500, 1996-2004 VIX holdout | S&P 500, 1996-2004 | 6 | identical
S&P 500, 1996-2004 VIX holdout | S&P 500, 1996-2004 | 7 | identical
S&P 500, 2024-2026 VIX holdout | S&P 500, 2024-2026 | 1 | identical
S&P 500, 2024-2026 VIX holdout | S&P 500, 2024-2026 | 2 | identical
S&P 500, 2024-2026 VIX holdout | S&P 500, 2024-2026 | 3 | identical
S&P 500, 2024-2026 VIX holdout | S&P 500, 2024-2026 | 4 | identical
S&P 500, 2024-2026 VIX holdout | S&P 500, 2024-2026 | 5 | identical
S&P 500, 2024-2026 VIX holdout | S&P 500, 2024-2026 | 6 | identical
S&P 500, 2024-2026 VIX holdout | S&P 500, 2024-2026 | 7 | identical
vix_early | own-row recalibration from the saved HMM outputs | identical days, max abs forecast diff 2.00e-15
vix_recent | own-row recalibration from the saved HMM outputs | identical days, max abs forecast diff 4.00e-15
```

## Summary

- Cross-index holdout: claim outcomes that change under QLIKE: R1 (mixed -> rejected).
- MS-GARCH and credit holdout: claim outcomes that change under QLIKE: R1 (confirmed -> mixed).
- S&P 500, 1996-2004: claim outcomes that change under QLIKE: C. regime models' own forecasts lose to HAR (holds -> not shown).
- S&P 500, 2024-2026: claim outcomes that change under QLIKE: A. VIX improves HAR (holds -> not shown).
- (f) HMM implied vol vs HAR + VIX: S&P 500, 1996-2004 +0.044 to +0.133 worse on RMSE, +0.077 to +0.275 worse on QLIKE; S&P 500, 2024-2026 -0.038 to +0.052 no difference on RMSE, -0.136 to +0.033 no difference on QLIKE.

## Cross-index holdout (Nasdaq-100, Dow, Russell 2000; 2026-10-14)

Class: post hoc, computed from the reproduced forecasts; not a registered test. Days scored per asset: Nasdaq-100 3,286, Dow Jones Industrial Average 3,297, Russell 2000 1,513.

### (a), (b) QLIKE beside RMSE, with equivalence bounds

The RMSE verdict column is the registered one (recomputed here to the printed digit, see the identity check at the top). The QLIKE interval was printed by the same frozen run as the registered secondary loss; the QLIKE verdict and every bound are post hoc. Bounds use the unrounded interval ends, in percent of the reference loss on the same days: for a "no difference" row, the largest improvement the interval still allows; for "better" or "worse", the smallest gain or loss it demonstrates.

| claim | forecast vs reference | expected | asset | ref RMSE | dRMSE 95% | RMSE verdict | RMSE bound | ref QLIKE | dQLIKE 95% | QLIKE verdict | QLIKE bound | same? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV vs HAR-RV + IV | better | Nasdaq-100 | 0.342 | -0.000 to +0.000 | no difference | gain excluded above 0.0% | 0.229 | -0.000 to +0.001 | no difference | gain excluded above 0.0% |  |
| P2 | SHAR + IV vs HAR-RV + IV | better | Nasdaq-100 | 0.342 | -0.000 to +0.000 | no difference | gain excluded above 0.1% | 0.229 | -0.001 to +0.000 | no difference | gain excluded above 0.3% |  |
| P3 | HAR-RV + IV + MSM vs HAR-RV + IV | better | Nasdaq-100 | 0.342 | -0.001 to +0.002 | no difference | gain excluded above 0.1% | 0.229 | -0.001 to +0.004 | no difference | gain excluded above 0.5% |  |
| P4 | Combination vs HAR-RV + IV | better | Nasdaq-100 | 0.342 | +0.000 to +0.018 | worse | loss shown of at least 0.1% | 0.229 | -0.000 to +0.046 | no difference | gain excluded above 0.1% | changes |
| P5 | MSM vs Two-state HMM implied vol | better | Nasdaq-100 | 0.377 | -0.026 to +0.014 | no difference | gain excluded above 6.9% | 0.312 | -0.080 to +0.004 | no difference | gain excluded above 25.7% |  |
| R1 | HAR-RV + IV vs HAR-RV | better | Nasdaq-100 | 0.352 | -0.018 to -0.000 | better | gain shown of at least 0.1% | 0.251 | -0.053 to +0.001 | no difference | gain excluded above 21.0% | changes |
| R2 | HAR-RV vs HAR | better | Nasdaq-100 | 0.370 | -0.028 to -0.008 | better | gain shown of at least 2.2% | 0.270 | -0.037 to -0.002 | better | gain shown of at least 0.8% |  |
| R3 | HAR-RV + IV + HMM prob vs HAR-RV + IV | not better | Nasdaq-100 | 0.342 | -0.009 to +0.003 | no difference | gain excluded above 2.7% | 0.229 | -0.012 to +0.001 | no difference | gain excluded above 5.4% |  |
| R4 | GJR-GARCH vs HAR-RV + IV | not better | Nasdaq-100 | 0.342 | +0.002 to +0.032 | worse | loss shown of at least 0.7% | 0.229 | +0.011 to +0.107 | worse | loss shown of at least 4.9% |  |
| P1 | HARQ + IV vs HAR-RV + IV | better | Dow Jones Industrial Average | 0.316 | -0.000 to +0.000 | no difference | gain excluded above 0.2% | 0.316 | -0.001 to +0.001 | no difference | gain excluded above 0.2% |  |
| P2 | SHAR + IV vs HAR-RV + IV | better | Dow Jones Industrial Average | 0.316 | -0.000 to +0.000 | no difference | gain excluded above 0.0% | 0.316 | -0.001 to +0.001 | no difference | gain excluded above 0.2% |  |
| P3 | HAR-RV + IV + MSM vs HAR-RV + IV | better | Dow Jones Industrial Average | 0.316 | -0.000 to +0.003 | no difference | gain excluded above 0.1% | 0.316 | -0.000 to +0.010 | no difference | gain excluded above 0.1% |  |
| P4 | Combination vs HAR-RV + IV | better | Dow Jones Industrial Average | 0.316 | +0.000 to +0.011 | worse | loss shown of at least 0.1% | 0.316 | -0.002 to +0.024 | no difference | gain excluded above 0.6% | changes |
| P5 | MSM vs Two-state HMM implied vol | better | Dow Jones Industrial Average | 0.361 | -0.035 to +0.008 | no difference | gain excluded above 9.8% | 0.435 | -0.171 to +0.007 | no difference | gain excluded above 39.3% |  |
| R1 | HAR-RV + IV vs HAR-RV | better | Dow Jones Industrial Average | 0.322 | -0.014 to +0.001 | no difference | gain excluded above 4.2% | 0.331 | -0.042 to +0.003 | no difference | gain excluded above 12.7% |  |
| R2 | HAR-RV vs HAR | better | Dow Jones Industrial Average | 0.337 | -0.024 to -0.006 | better | gain shown of at least 1.8% | 0.355 | -0.052 to +0.011 | no difference | gain excluded above 14.6% | changes |
| R3 | HAR-RV + IV + HMM prob vs HAR-RV + IV | not better | Dow Jones Industrial Average | 0.316 | -0.000 to +0.003 | no difference | gain excluded above 0.1% | 0.316 | -0.001 to +0.009 | no difference | gain excluded above 0.4% |  |
| R4 | GJR-GARCH vs HAR-RV + IV | not better | Dow Jones Industrial Average | 0.316 | +0.002 to +0.020 | worse | loss shown of at least 0.5% | 0.316 | -0.008 to +0.065 | no difference | gain excluded above 2.5% | changes |
| P1 | HARQ + IV vs HAR-RV + IV | better | Russell 2000 | 0.299 | -0.000 to +0.000 | no difference | gain excluded above 0.1% | 0.113 | -0.000 to +0.001 | no difference | gain excluded above 0.1% |  |
| P2 | SHAR + IV vs HAR-RV + IV | better | Russell 2000 | 0.299 | -0.001 to +0.000 | no difference | gain excluded above 0.3% | 0.113 | -0.000 to +0.000 | no difference | gain excluded above 0.2% |  |
| P3 | HAR-RV + IV + MSM vs HAR-RV + IV | better | Russell 2000 | 0.299 | -0.002 to +0.002 | no difference | gain excluded above 0.7% | 0.113 | -0.001 to +0.003 | no difference | gain excluded above 0.5% |  |
| P4 | Combination vs HAR-RV + IV | better | Russell 2000 | 0.299 | -0.022 to +0.009 | no difference | gain excluded above 7.2% | 0.113 | -0.010 to +0.009 | no difference | gain excluded above 8.5% |  |
| P5 | MSM vs Two-state HMM implied vol | better | Russell 2000 | 0.370 | -0.106 to -0.016 | better | gain shown of at least 4.4% | 0.182 | -0.105 to -0.016 | better | gain shown of at least 8.6% |  |
| R1 | HAR-RV + IV vs HAR-RV | better | Russell 2000 | 0.308 | -0.025 to +0.010 | no difference | gain excluded above 8.1% | 0.115 | -0.013 to +0.010 | no difference | gain excluded above 11.1% |  |
| R2 | HAR-RV vs HAR | better | Russell 2000 | 0.316 | -0.023 to +0.004 | no difference | gain excluded above 7.4% | 0.130 | -0.025 to -0.004 | better | gain shown of at least 3.4% | changes |
| R3 | HAR-RV + IV + HMM prob vs HAR-RV + IV | not better | Russell 2000 | 0.299 | -0.003 to +0.007 | no difference | gain excluded above 0.9% | 0.113 | -0.000 to +0.005 | no difference | gain excluded above 0.4% |  |
| R4 | GJR-GARCH vs HAR-RV + IV | not better | Russell 2000 | 0.299 | -0.007 to +0.052 | no difference | gain excluded above 2.3% | 0.113 | -0.001 to +0.071 | no difference | gain excluded above 1.1% |  |

Per-asset verdicts that change between the two losses: 6 of 27.

### Claim outcomes under each loss and each bootstrap scheme

Columns: the registered scheme (63-day circular blocks), then circular blocks of 21, 42 and 126 days and the stationary bootstrap with mean block 63 (s63), 2,000 draws, seed 0, for each loss. The claim rule is the protocols' (a "better" claim is confirmed if better on at least two counted assets and worse on none, rejected if better on none, mixed otherwise; a "not better" claim holds if better on none).

| claim | forecast vs reference | expected | RMSE (registered, 63) | QLIKE (post hoc, 63) | RMSE c21 | RMSE c42 | RMSE c126 | RMSE s63 | QLIKE c21 | QLIKE c42 | QLIKE c126 | QLIKE s63 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV vs HAR-RV + IV | better | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected |
| P2 | SHAR + IV vs HAR-RV + IV | better | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected |
| P3 | HAR-RV + IV + MSM vs HAR-RV + IV | better | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected |
| P4 | Combination vs HAR-RV + IV | better | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected |
| P5 | MSM vs Two-state HMM implied vol | better | mixed | mixed | mixed | mixed | mixed | mixed | confirmed | mixed | mixed | mixed |
| R1 | HAR-RV + IV vs HAR-RV | better | mixed | rejected | mixed | mixed | mixed | mixed | mixed | rejected | rejected | rejected |
| R2 | HAR-RV vs HAR | better | confirmed | confirmed | confirmed | confirmed | confirmed | confirmed | mixed | confirmed | confirmed | confirmed |
| R3 | HAR-RV + IV + HMM prob vs HAR-RV + IV | not better | holds | holds | holds | holds | holds | holds | holds | holds | holds | holds |
| R4 | GJR-GARCH vs HAR-RV + IV | not better | holds | holds | holds | holds | holds | holds | holds | holds | holds | holds |

### (c) HAC Diebold-Mariano, lag 20

Diebold and Mariano (1995) on the per-day loss difference with a Bartlett-kernel long-run variance truncated at 20 lags (the 21-day targets overlap, so the errors are MA(20) under the null). For RMSE the test is on the squared error (MSE), whose sign agrees with the RMSE difference; two-sided normal p-values. The last column repeats the bootstrap verdicts for comparison: a p below 0.05 and a bootstrap interval off zero should agree in sign.

| claim | asset | forecast vs reference | dMSE mean | DM stat (MSE) | p (MSE) | dQLIKE mean | DM stat (QLIKE) | p (QLIKE) | bootstrap RMSE / QLIKE |
|---|---|---|---|---|---|---|---|---|---|
| P1 | Nasdaq-100 | HARQ + IV vs HAR-RV + IV | +0.0001 | +1.32 | 0.188 | +0.0002 | +1.63 | 0.103 | no difference / no difference |
| P2 | Nasdaq-100 | SHAR + IV vs HAR-RV + IV | +0.0000 | +0.04 | 0.965 | +0.0000 | +0.05 | 0.957 | no difference / no difference |
| P3 | Nasdaq-100 | HAR-RV + IV + MSM vs HAR-RV + IV | +0.0003 | +0.99 | 0.320 | +0.0011 | +1.02 | 0.310 | no difference / no difference |
| P4 | Nasdaq-100 | Combination vs HAR-RV + IV | +0.0068 | +1.71 | 0.086 | +0.0198 | +1.80 | 0.072 | worse / no difference |
| P5 | Nasdaq-100 | MSM vs Two-state HMM implied vol | -0.0052 | -0.79 | 0.430 | -0.0350 | -1.91 | 0.056 | no difference / no difference |
| R1 | Nasdaq-100 | HAR-RV + IV vs HAR-RV | -0.0067 | -1.88 | 0.060 | -0.0216 | -1.80 | 0.071 | better / no difference |
| R2 | Nasdaq-100 | HAR-RV vs HAR | -0.0129 | -2.28 | 0.023 | -0.0196 | -1.73 | 0.084 | better / better |
| R3 | Nasdaq-100 | HAR-RV + IV + HMM prob vs HAR-RV + IV | -0.0027 | -1.16 | 0.245 | -0.0049 | -1.29 | 0.199 | no difference / no difference |
| R4 | Nasdaq-100 | GJR-GARCH vs HAR-RV + IV | +0.0127 | +2.21 | 0.027 | +0.0534 | +2.42 | 0.016 | worse / worse |
| P1 | Dow Jones Industrial Average | HARQ + IV vs HAR-RV + IV | -0.0001 | -1.06 | 0.289 | +0.0001 | +0.28 | 0.781 | no difference / no difference |
| P2 | Dow Jones Industrial Average | SHAR + IV vs HAR-RV + IV | +0.0000 | +0.11 | 0.912 | +0.0001 | +0.52 | 0.605 | no difference / no difference |
| P3 | Dow Jones Industrial Average | HAR-RV + IV + MSM vs HAR-RV + IV | +0.0011 | +1.58 | 0.113 | +0.0038 | +1.62 | 0.105 | no difference / no difference |
| P4 | Dow Jones Industrial Average | Combination vs HAR-RV + IV | +0.0041 | +1.43 | 0.153 | +0.0112 | +1.44 | 0.149 | worse / no difference |
| P5 | Dow Jones Industrial Average | MSM vs Two-state HMM implied vol | -0.0112 | -1.16 | 0.244 | -0.0625 | -1.50 | 0.134 | no difference / no difference |
| R1 | Dow Jones Industrial Average | HAR-RV + IV vs HAR-RV | -0.0044 | -1.23 | 0.220 | -0.0150 | -1.35 | 0.178 | no difference / no difference |
| R2 | Dow Jones Industrial Average | HAR-RV vs HAR | -0.0099 | -2.03 | 0.043 | -0.0236 | -1.34 | 0.180 | better / no difference |
| R3 | Dow Jones Industrial Average | HAR-RV + IV + HMM prob vs HAR-RV + IV | +0.0006 | +1.46 | 0.145 | +0.0034 | +1.45 | 0.146 | no difference / no difference |
| R4 | Dow Jones Industrial Average | GJR-GARCH vs HAR-RV + IV | +0.0050 | +2.08 | 0.037 | +0.0294 | +1.70 | 0.089 | worse / no difference |
| P1 | Russell 2000 | HARQ + IV vs HAR-RV + IV | -0.0000 | -0.22 | 0.827 | +0.0002 | +0.86 | 0.389 | no difference / no difference |
| P2 | Russell 2000 | SHAR + IV vs HAR-RV + IV | -0.0001 | -0.35 | 0.726 | +0.0001 | +0.75 | 0.452 | no difference / no difference |
| P3 | Russell 2000 | HAR-RV + IV + MSM vs HAR-RV + IV | +0.0000 | +0.09 | 0.925 | +0.0009 | +1.25 | 0.211 | no difference / no difference |
| P4 | Russell 2000 | Combination vs HAR-RV + IV | -0.0027 | -0.70 | 0.485 | -0.0006 | -0.11 | 0.915 | no difference / no difference |
| P5 | Russell 2000 | MSM vs Two-state HMM implied vol | -0.0397 | -3.34 | 0.001 | -0.0573 | -3.17 | 0.002 | better / better |
| R1 | Russell 2000 | HAR-RV + IV vs HAR-RV | -0.0050 | -0.89 | 0.373 | -0.0020 | -0.33 | 0.741 | no difference / no difference |
| R2 | Russell 2000 | HAR-RV vs HAR | -0.0051 | -0.94 | 0.348 | -0.0144 | -2.32 | 0.020 | no difference / better |
| R3 | Russell 2000 | HAR-RV + IV + HMM prob vs HAR-RV + IV | +0.0011 | +0.88 | 0.381 | +0.0021 | +1.62 | 0.106 | no difference / no difference |
| R4 | Russell 2000 | GJR-GARCH vs HAR-RV + IV | +0.0114 | +1.37 | 0.171 | +0.0273 | +1.74 | 0.081 | no difference / no difference |

DM at 5% and the bootstrap interval agree on significance in 24 of 27 RMSE rows and 26 of 27 QLIKE rows.

### (d) Block-length sensitivity

Per-asset verdicts under each alternative bootstrap against the registered 63-day circular blocks. c = circular block of that length; s63 = stationary bootstrap (Politis and Romano 1994) with mean block 63.

| loss | scheme | verdicts changed | which |
|---|---|---|---|
| RMSE | c21 | 1 of 27 | P4 Dow Jones Industrial Average (worse -> no difference) |
| RMSE | c42 | 0 of 27 |  |
| RMSE | c126 | 0 of 27 |  |
| RMSE | s63 | 0 of 27 |  |
| QLIKE | c21 | 4 of 27 | P4 Nasdaq-100 (no difference -> worse); P5 Nasdaq-100 (no difference -> better); R1 Nasdaq-100 (no difference -> better); R2 Nasdaq-100 (better -> no difference) |
| QLIKE | c42 | 1 of 27 | P4 Nasdaq-100 (no difference -> worse) |
| QLIKE | c126 | 1 of 27 | P4 Nasdaq-100 (no difference -> worse) |
| QLIKE | s63 | 1 of 27 | P1 Nasdaq-100 (no difference -> worse) |

### (c) Model confidence set per asset, 10%

Hansen, Lunde and Nason (2011) with the T_max statistic and the holdouts' 63-day circular block bootstrap (2,000 draws, seed 0), over every forecast in the scored table. A model is in the set if its MCS p-value is at least 0.10. The set is the group of forecasts that the data cannot separate from the best; it replaces nothing in the registered claim rule.

**Nasdaq-100**, 3,286 days: MSE set has 9 of 11 forecasts, QLIKE set 7 of 11.

| forecast | RMSE | MCS p (MSE) | in set (MSE) | QLIKE | MCS p (QLIKE) | in set (QLIKE) |
|---|---|---|---|---|---|---|
| HAR-RV + IV + HMM prob | 0.338 | 1.000 | yes | 0.224 | 1.000 | yes |
| HAR-RV + IV | 0.342 | 0.238 | yes | 0.229 | 0.176 | yes |
| SHAR + IV | 0.342 | 0.232 | yes | 0.229 | 0.176 | yes |
| HARQ + IV | 0.342 | 0.227 | yes | 0.229 | 0.176 | yes |
| HAR-RV + IV + MSM | 0.342 | 0.181 | yes | 0.230 | 0.176 | yes |
| HAR-RV | 0.352 | 0.123 | yes | 0.251 | 0.152 | yes |
| Combination | 0.352 | 0.181 | yes | 0.249 | 0.140 | yes |
| GJR-GARCH | 0.360 | 0.104 | yes | 0.282 | 0.060 |  |
| HAR | 0.370 | 0.072 |  | 0.270 | 0.060 |  |
| MSM | 0.370 | 0.072 |  | 0.277 | 0.060 |  |
| Two-state HMM implied vol | 0.377 | 0.104 | yes | 0.312 | 0.060 |  |

**Dow Jones Industrial Average**, 3,297 days: MSE set has 9 of 11 forecasts, QLIKE set 10 of 11.

| forecast | RMSE | MCS p (MSE) | in set (MSE) | QLIKE | MCS p (QLIKE) | in set (QLIKE) |
|---|---|---|---|---|---|---|
| HARQ + IV | 0.315 | 1.000 | yes | 0.316 | 0.942 | yes |
| HAR-RV + IV | 0.316 | 0.483 | yes | 0.316 | 1.000 | yes |
| SHAR + IV | 0.316 | 0.483 | yes | 0.316 | 0.942 | yes |
| HAR-RV + IV + HMM prob | 0.317 | 0.483 | yes | 0.320 | 0.547 | yes |
| HAR-RV + IV + MSM | 0.317 | 0.483 | yes | 0.320 | 0.547 | yes |
| Combination | 0.322 | 0.239 | yes | 0.327 | 0.547 | yes |
| HAR-RV | 0.322 | 0.318 | yes | 0.331 | 0.547 | yes |
| GJR-GARCH | 0.323 | 0.239 | yes | 0.345 | 0.370 | yes |
| HAR | 0.337 | 0.091 |  | 0.355 | 0.216 | yes |
| MSM | 0.345 | 0.089 |  | 0.373 | 0.035 |  |
| Two-state HMM implied vol | 0.361 | 0.239 | yes | 0.435 | 0.216 | yes |

**Russell 2000**, 1,513 days: MSE set has 9 of 11 forecasts, QLIKE set 9 of 11.

| forecast | RMSE | MCS p (MSE) | in set (MSE) | QLIKE | MCS p (QLIKE) | in set (QLIKE) |
|---|---|---|---|---|---|---|
| Combination | 0.295 | 1.000 | yes | 0.113 | 1.000 | yes |
| SHAR + IV | 0.299 | 0.520 | yes | 0.113 | 0.898 | yes |
| HARQ + IV | 0.299 | 0.520 | yes | 0.114 | 0.898 | yes |
| HAR-RV + IV | 0.299 | 0.520 | yes | 0.113 | 0.920 | yes |
| HAR-RV + IV + MSM | 0.299 | 0.478 | yes | 0.114 | 0.895 | yes |
| HAR-RV + IV + HMM prob | 0.301 | 0.478 | yes | 0.115 | 0.567 | yes |
| HAR-RV | 0.308 | 0.478 | yes | 0.115 | 0.895 | yes |
| MSM | 0.312 | 0.478 | yes | 0.125 | 0.352 | yes |
| HAR | 0.316 | 0.038 |  | 0.130 | 0.027 |  |
| GJR-GARCH | 0.318 | 0.478 | yes | 0.141 | 0.352 | yes |
| Two-state HMM implied vol | 0.370 | 0.015 |  | 0.182 | 0.015 |  |

## MS-GARCH and credit holdout (USO, GLD, EEM, EWZ; 2026-10-14)

Class: post hoc, computed from the reproduced forecasts; not a registered test. Days scored per asset: Crude oil (USO) 3,604, Gold (GLD) 3,821, Emerging markets (EEM) 3,119, Brazil (EWZ) 3,119.

### (a), (b) QLIKE beside RMSE, with equivalence bounds

The RMSE verdict column is the registered one (recomputed here to the printed digit, see the identity check at the top). The QLIKE interval was printed by the same frozen run as the registered secondary loss; the QLIKE verdict and every bound are post hoc. Bounds use the unrounded interval ends, in percent of the reference loss on the same days: for a "no difference" row, the largest improvement the interval still allows; for "better" or "worse", the smallest gain or loss it demonstrates.

| claim | forecast vs reference | expected | asset | ref RMSE | dRMSE 95% | RMSE verdict | RMSE bound | ref QLIKE | dQLIKE 95% | QLIKE verdict | QLIKE bound | same? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | MS-GARCH vs GJR-GARCH | better | Crude oil (USO) | 0.971 | -0.016 to +0.046 | no difference | gain excluded above 1.6% | 0.352 | -0.022 to +0.007 | no difference | gain excluded above 6.2% |  |
| M2 | HAR + IV + MS-GARCH vs HAR + IV | better | Crude oil (USO) | 0.859 | +0.000 to +0.024 | worse | loss shown of at least 0.0% | 0.247 | +0.001 to +0.010 | worse | loss shown of at least 0.3% |  |
| M3 | MS-GARCH vs Two-state HMM implied vol | better | Crude oil (USO) | 1.081 | -0.277 to +0.122 | no difference | gain excluded above 25.6% | 0.467 | -0.323 to -0.004 | better | gain shown of at least 0.8% | changes |
| M4 | HAR + IV + MS-GARCH prob vs HAR + IV | better | Crude oil (USO) | 0.859 | -0.003 to +0.005 | no difference | gain excluded above 0.3% | 0.247 | -0.002 to +0.003 | no difference | gain excluded above 1.0% |  |
| M5 | MS-GARCH vs HAR + IV | better | Crude oil (USO) | 0.859 | +0.038 to +0.240 | worse | loss shown of at least 4.4% | 0.247 | +0.034 to +0.181 | worse | loss shown of at least 13.6% |  |
| C1 | HAR + IV + credit vs HAR + IV | not better | Crude oil (USO) | 0.859 | -0.008 to +0.042 | no difference | gain excluded above 0.9% | 0.247 | -0.036 to +0.003 | no difference | gain excluded above 14.5% |  |
| C2 | HAR + credit vs HAR | better | Crude oil (USO) | 0.932 | -0.003 to +0.007 | no difference | gain excluded above 0.3% | 0.333 | +0.002 to +0.018 | worse | loss shown of at least 0.5% | changes |
| R1 | HAR + IV vs HAR | better | Crude oil (USO) | 0.932 | -0.127 to -0.010 | better | gain shown of at least 1.1% | 0.333 | -0.148 to -0.038 | better | gain shown of at least 11.4% |  |
| R2 | GJR-GARCH vs HAR + IV | not better | Crude oil (USO) | 0.859 | +0.043 to +0.204 | worse | loss shown of at least 5.0% | 0.247 | +0.044 to +0.185 | worse | loss shown of at least 17.6% |  |
| M1 | MS-GARCH vs GJR-GARCH | better | Gold (GLD) | 0.368 | -0.007 to +0.011 | no difference | gain excluded above 1.8% | 0.251 | -0.013 to +0.015 | no difference | gain excluded above 5.2% |  |
| M2 | HAR + IV + MS-GARCH vs HAR + IV | better | Gold (GLD) | 0.344 | -0.000 to +0.001 | no difference | gain excluded above 0.1% | 0.223 | -0.000 to +0.003 | no difference | gain excluded above 0.1% |  |
| M3 | MS-GARCH vs Two-state HMM implied vol | better | Gold (GLD) | 0.392 | -0.044 to -0.002 | better | gain shown of at least 0.4% | 0.277 | -0.064 to +0.024 | no difference | gain excluded above 23.1% | changes |
| M4 | HAR + IV + MS-GARCH prob vs HAR + IV | better | Gold (GLD) | 0.344 | -0.001 to +0.011 | no difference | gain excluded above 0.2% | 0.223 | -0.001 to +0.018 | no difference | gain excluded above 0.4% |  |
| M5 | MS-GARCH vs HAR + IV | better | Gold (GLD) | 0.344 | +0.013 to +0.038 | worse | loss shown of at least 3.8% | 0.223 | -0.009 to +0.060 | no difference | gain excluded above 3.9% | changes |
| C1 | HAR + IV + credit vs HAR + IV | not better | Gold (GLD) | 0.344 | -0.008 to +0.005 | no difference | gain excluded above 2.3% | 0.223 | -0.009 to +0.027 | no difference | gain excluded above 4.2% |  |
| C2 | HAR + credit vs HAR | better | Gold (GLD) | 0.380 | -0.012 to +0.015 | no difference | gain excluded above 3.1% | 0.258 | -0.007 to +0.047 | no difference | gain excluded above 2.8% |  |
| R1 | HAR + IV vs HAR | better | Gold (GLD) | 0.380 | -0.051 to -0.022 | better | gain shown of at least 5.8% | 0.258 | -0.067 to +0.007 | no difference | gain excluded above 26.1% | changes |
| R2 | GJR-GARCH vs HAR + IV | not better | Gold (GLD) | 0.344 | +0.010 to +0.037 | worse | loss shown of at least 3.0% | 0.223 | -0.006 to +0.056 | no difference | gain excluded above 2.7% | changes |
| M1 | MS-GARCH vs GJR-GARCH | better | Emerging markets (EEM) | 0.504 | -0.029 to +0.006 | no difference | gain excluded above 5.8% | 0.271 | -0.005 to +0.029 | no difference | gain excluded above 2.0% |  |
| M2 | HAR + IV + MS-GARCH vs HAR + IV | better | Emerging markets (EEM) | 0.471 | -0.003 to +0.004 | no difference | gain excluded above 0.6% | 0.253 | -0.008 to +0.009 | no difference | gain excluded above 3.0% |  |
| M3 | MS-GARCH vs Two-state HMM implied vol | better | Emerging markets (EEM) | 0.532 | -0.058 to -0.017 | better | gain shown of at least 3.2% | 0.333 | -0.133 to +0.010 | no difference | gain excluded above 40.1% | changes |
| M4 | HAR + IV + MS-GARCH prob vs HAR + IV | better | Emerging markets (EEM) | 0.471 | -0.003 to +0.006 | no difference | gain excluded above 0.5% | 0.253 | -0.006 to +0.010 | no difference | gain excluded above 2.5% |  |
| M5 | MS-GARCH vs HAR + IV | better | Emerging markets (EEM) | 0.471 | +0.005 to +0.048 | worse | loss shown of at least 1.1% | 0.253 | -0.022 to +0.070 | no difference | gain excluded above 8.6% | changes |
| C1 | HAR + IV + credit vs HAR + IV | not better | Emerging markets (EEM) | 0.471 | -0.001 to +0.013 | no difference | gain excluded above 0.3% | 0.253 | -0.005 to +0.030 | no difference | gain excluded above 1.8% |  |
| C2 | HAR + credit vs HAR | better | Emerging markets (EEM) | 0.498 | -0.011 to +0.019 | no difference | gain excluded above 2.1% | 0.257 | -0.003 to +0.087 | no difference | gain excluded above 1.1% |  |
| R1 | HAR + IV vs HAR | better | Emerging markets (EEM) | 0.498 | -0.049 to -0.009 | better | gain shown of at least 1.8% | 0.257 | -0.040 to +0.052 | no difference | gain excluded above 15.5% | changes |
| R2 | GJR-GARCH vs HAR + IV | not better | Emerging markets (EEM) | 0.471 | +0.009 to +0.061 | worse | loss shown of at least 2.0% | 0.253 | -0.038 to +0.058 | no difference | gain excluded above 14.8% | changes |
| M1 | MS-GARCH vs GJR-GARCH | better | Brazil (EWZ) | 0.917 | -0.061 to +0.063 | no difference | gain excluded above 6.6% | 0.335 | -0.022 to +0.089 | no difference | gain excluded above 6.6% |  |
| M2 | HAR + IV + MS-GARCH vs HAR + IV | better | Brazil (EWZ) | 0.868 | +0.001 to +0.006 | worse | loss shown of at least 0.1% | 0.316 | -0.001 to +0.005 | no difference | gain excluded above 0.2% | changes |
| M3 | MS-GARCH vs Two-state HMM implied vol | better | Brazil (EWZ) | 0.953 | -0.053 to +0.021 | no difference | gain excluded above 5.6% | 0.402 | -0.079 to -0.010 | better | gain shown of at least 2.4% | changes |
| M4 | HAR + IV + MS-GARCH prob vs HAR + IV | better | Brazil (EWZ) | 0.868 | -0.026 to +0.005 | no difference | gain excluded above 3.0% | 0.316 | -0.025 to +0.014 | no difference | gain excluded above 7.8% |  |
| M5 | MS-GARCH vs HAR + IV | better | Brazil (EWZ) | 0.868 | +0.026 to +0.122 | worse | loss shown of at least 3.0% | 0.316 | -0.011 to +0.093 | no difference | gain excluded above 3.6% | changes |
| C1 | HAR + IV + credit vs HAR + IV | not better | Brazil (EWZ) | 0.868 | -0.003 to +0.020 | no difference | gain excluded above 0.4% | 0.316 | -0.019 to +0.005 | no difference | gain excluded above 5.9% |  |
| C2 | HAR + credit vs HAR | better | Brazil (EWZ) | 0.892 | -0.001 to +0.008 | no difference | gain excluded above 0.1% | 0.317 | +0.002 to +0.011 | worse | loss shown of at least 0.7% | changes |
| R1 | HAR + IV vs HAR | better | Brazil (EWZ) | 0.892 | -0.072 to +0.001 | no difference | gain excluded above 8.0% | 0.317 | -0.047 to +0.078 | no difference | gain excluded above 14.8% |  |
| R2 | GJR-GARCH vs HAR + IV | not better | Brazil (EWZ) | 0.868 | -0.006 to +0.157 | no difference | gain excluded above 0.7% | 0.316 | -0.074 to +0.087 | no difference | gain excluded above 23.3% |  |

Per-asset verdicts that change between the two losses: 14 of 36.

### Claim outcomes under each loss and each bootstrap scheme

Columns: the registered scheme (63-day circular blocks), then circular blocks of 21, 42 and 126 days and the stationary bootstrap with mean block 63 (s63), 2,000 draws, seed 0, for each loss. The claim rule is the protocols' (a "better" claim is confirmed if better on at least two counted assets and worse on none, rejected if better on none, mixed otherwise; a "not better" claim holds if better on none).

| claim | forecast vs reference | expected | RMSE (registered, 63) | QLIKE (post hoc, 63) | RMSE c21 | RMSE c42 | RMSE c126 | RMSE s63 | QLIKE c21 | QLIKE c42 | QLIKE c126 | QLIKE s63 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| M1 | MS-GARCH vs GJR-GARCH | better | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected |
| M2 | HAR + IV + MS-GARCH vs HAR + IV | better | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected |
| M3 | MS-GARCH vs Two-state HMM implied vol | better | confirmed | confirmed | confirmed | confirmed | mixed | confirmed | confirmed | confirmed | confirmed | confirmed |
| M4 | HAR + IV + MS-GARCH prob vs HAR + IV | better | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected |
| M5 | MS-GARCH vs HAR + IV | better | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected |
| C1 | HAR + IV + credit vs HAR + IV | not better | holds | holds | holds | holds | holds | holds | holds | holds | holds | holds |
| C2 | HAR + credit vs HAR | better | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected | rejected |
| R1 | HAR + IV vs HAR | better | confirmed | mixed | confirmed | confirmed | confirmed | confirmed | confirmed | mixed | mixed | mixed |
| R2 | GJR-GARCH vs HAR + IV | not better | holds | holds | holds | holds | holds | holds | holds | holds | holds | holds |

### (c) HAC Diebold-Mariano, lag 20

Diebold and Mariano (1995) on the per-day loss difference with a Bartlett-kernel long-run variance truncated at 20 lags (the 21-day targets overlap, so the errors are MA(20) under the null). For RMSE the test is on the squared error (MSE), whose sign agrees with the RMSE difference; two-sided normal p-values. The last column repeats the bootstrap verdicts for comparison: a p below 0.05 and a bootstrap interval off zero should agree in sign.

| claim | asset | forecast vs reference | dMSE mean | DM stat (MSE) | p (MSE) | dQLIKE mean | DM stat (QLIKE) | p (QLIKE) | bootstrap RMSE / QLIKE |
|---|---|---|---|---|---|---|---|---|---|
| M1 | Crude oil (USO) | MS-GARCH vs GJR-GARCH | +0.0319 | +1.29 | 0.197 | -0.0070 | -1.01 | 0.311 | no difference / no difference |
| M2 | Crude oil (USO) | HAR + IV + MS-GARCH vs HAR + IV | +0.0162 | +1.46 | 0.145 | +0.0043 | +1.91 | 0.056 | worse / worse |
| M3 | Crude oil (USO) | MS-GARCH vs Two-state HMM implied vol | -0.1936 | -0.77 | 0.440 | -0.1222 | -1.92 | 0.055 | no difference / better |
| M4 | Crude oil (USO) | HAR + IV + MS-GARCH prob vs HAR + IV | +0.0019 | +0.51 | 0.611 | +0.0003 | +0.23 | 0.819 | no difference / no difference |
| M5 | Crude oil (USO) | MS-GARCH vs HAR + IV | +0.2376 | +2.47 | 0.013 | +0.0976 | +2.97 | 0.003 | worse / worse |
| C1 | Crude oil (USO) | HAR + IV + credit vs HAR + IV | +0.0229 | +0.89 | 0.373 | -0.0113 | -1.22 | 0.222 | no difference / no difference |
| C2 | Crude oil (USO) | HAR + credit vs HAR | +0.0034 | +0.82 | 0.414 | +0.0085 | +2.33 | 0.020 | no difference / worse |
| R1 | Crude oil (USO) | HAR + IV vs HAR | -0.1318 | -1.86 | 0.062 | -0.0858 | -3.44 | 0.001 | better / better |
| R2 | Crude oil (USO) | GJR-GARCH vs HAR + IV | +0.2057 | +2.65 | 0.008 | +0.1045 | +3.22 | 0.001 | worse / worse |
| M1 | Gold (GLD) | MS-GARCH vs GJR-GARCH | +0.0020 | +0.70 | 0.485 | +0.0001 | +0.02 | 0.986 | no difference / no difference |
| M2 | Gold (GLD) | HAR + IV + MS-GARCH vs HAR + IV | +0.0004 | +1.67 | 0.096 | +0.0012 | +1.74 | 0.081 | no difference / no difference |
| M3 | Gold (GLD) | MS-GARCH vs Two-state HMM implied vol | -0.0167 | -2.51 | 0.012 | -0.0258 | -1.32 | 0.187 | better / no difference |
| M4 | Gold (GLD) | HAR + IV + MS-GARCH prob vs HAR + IV | +0.0034 | +1.51 | 0.132 | +0.0074 | +1.79 | 0.073 | no difference / no difference |
| M5 | Gold (GLD) | MS-GARCH vs HAR + IV | +0.0188 | +3.96 | 0.000 | +0.0282 | +1.90 | 0.058 | worse / no difference |
| C1 | Gold (GLD) | HAR + IV + credit vs HAR + IV | -0.0012 | -0.53 | 0.597 | +0.0051 | +0.61 | 0.540 | no difference / no difference |
| C2 | Gold (GLD) | HAR + credit vs HAR | +0.0012 | +0.26 | 0.795 | +0.0173 | +1.50 | 0.134 | no difference / no difference |
| R1 | Gold (GLD) | HAR + IV vs HAR | -0.0258 | -5.62 | 0.000 | -0.0350 | -2.15 | 0.031 | better / no difference |
| R2 | Gold (GLD) | GJR-GARCH vs HAR + IV | +0.0168 | +3.86 | 0.000 | +0.0281 | +2.12 | 0.034 | worse / no difference |
| M1 | Emerging markets (EEM) | MS-GARCH vs GJR-GARCH | -0.0098 | -0.85 | 0.395 | +0.0101 | +1.15 | 0.249 | no difference / no difference |
| M2 | Emerging markets (EEM) | HAR + IV + MS-GARCH vs HAR + IV | +0.0010 | +0.64 | 0.520 | +0.0007 | +0.17 | 0.862 | no difference / no difference |
| M3 | Emerging markets (EEM) | MS-GARCH vs Two-state HMM implied vol | -0.0391 | -2.91 | 0.004 | -0.0521 | -1.56 | 0.119 | better / no difference |
| M4 | Emerging markets (EEM) | HAR + IV + MS-GARCH prob vs HAR + IV | +0.0014 | +0.83 | 0.404 | +0.0017 | +0.42 | 0.678 | no difference / no difference |
| M5 | Emerging markets (EEM) | MS-GARCH vs HAR + IV | +0.0219 | +2.39 | 0.017 | +0.0274 | +1.17 | 0.243 | worse / no difference |
| C1 | Emerging markets (EEM) | HAR + IV + credit vs HAR + IV | +0.0037 | +1.52 | 0.129 | +0.0092 | +1.19 | 0.235 | no difference / no difference |
| C2 | Emerging markets (EEM) | HAR + credit vs HAR | +0.0059 | +0.93 | 0.352 | +0.0367 | +1.80 | 0.072 | no difference / no difference |
| R1 | Emerging markets (EEM) | HAR + IV vs HAR | -0.0259 | -2.48 | 0.013 | -0.0037 | -0.14 | 0.885 | better / no difference |
| R2 | Emerging markets (EEM) | GJR-GARCH vs HAR + IV | +0.0318 | +2.23 | 0.025 | +0.0173 | +0.75 | 0.453 | worse / no difference |
| M1 | Brazil (EWZ) | MS-GARCH vs GJR-GARCH | +0.0259 | +0.48 | 0.632 | +0.0251 | +1.05 | 0.292 | no difference / no difference |
| M2 | Brazil (EWZ) | HAR + IV + MS-GARCH vs HAR + IV | +0.0044 | +2.42 | 0.015 | +0.0022 | +1.48 | 0.139 | worse / no difference |
| M3 | Brazil (EWZ) | MS-GARCH vs Two-state HMM implied vol | -0.0417 | -1.29 | 0.199 | -0.0415 | -2.64 | 0.008 | no difference / better |
| M4 | Brazil (EWZ) | HAR + IV + MS-GARCH prob vs HAR + IV | -0.0127 | -1.09 | 0.278 | -0.0041 | -0.40 | 0.686 | no difference / no difference |
| M5 | Brazil (EWZ) | MS-GARCH vs HAR + IV | +0.1133 | +2.91 | 0.004 | +0.0449 | +1.45 | 0.146 | worse / no difference |
| C1 | Brazil (EWZ) | HAR + IV + credit vs HAR + IV | +0.0075 | +1.22 | 0.221 | -0.0050 | -0.90 | 0.367 | no difference / no difference |
| C2 | Brazil (EWZ) | HAR + credit vs HAR | +0.0050 | +1.71 | 0.088 | +0.0065 | +2.78 | 0.005 | no difference / worse |
| R1 | Brazil (EWZ) | HAR + IV vs HAR | -0.0429 | -1.84 | 0.066 | -0.0009 | -0.03 | 0.980 | no difference / no difference |
| R2 | Brazil (EWZ) | GJR-GARCH vs HAR + IV | +0.0874 | +1.67 | 0.096 | +0.0197 | +0.52 | 0.606 | no difference / no difference |

DM at 5% and the bootstrap interval agree on significance in 34 of 36 RMSE rows and 32 of 36 QLIKE rows.

### (d) Block-length sensitivity

Per-asset verdicts under each alternative bootstrap against the registered 63-day circular blocks. c = circular block of that length; s63 = stationary bootstrap (Politis and Romano 1994) with mean block 63.

| loss | scheme | verdicts changed | which |
|---|---|---|---|
| RMSE | c21 | 3 of 36 | M2 Crude oil (USO) (worse -> no difference); R1 Crude oil (USO) (better -> no difference); R2 Brazil (EWZ) (no difference -> worse) |
| RMSE | c42 | 1 of 36 | M2 Crude oil (USO) (worse -> no difference) |
| RMSE | c126 | 2 of 36 | M2 Crude oil (USO) (worse -> no difference); M3 Gold (GLD) (better -> no difference) |
| RMSE | s63 | 1 of 36 | M2 Crude oil (USO) (worse -> no difference) |
| QLIKE | c21 | 3 of 36 | R1 Gold (GLD) (no difference -> better); R2 Gold (GLD) (no difference -> worse); C2 Emerging markets (EEM) (no difference -> worse) |
| QLIKE | c42 | 1 of 36 | C2 Emerging markets (EEM) (no difference -> worse) |
| QLIKE | c126 | 0 of 36 |  |
| QLIKE | s63 | 0 of 36 |  |

### (c) Model confidence set per asset, 10%

Hansen, Lunde and Nason (2011) with the T_max statistic and the holdouts' 63-day circular block bootstrap (2,000 draws, seed 0), over every forecast in the scored table. A model is in the set if its MCS p-value is at least 0.10. The set is the group of forecasts that the data cannot separate from the best; it replaces nothing in the registered claim rule.

**Crude oil (USO)**, 3,604 days: MSE set has 9 of 9 forecasts, QLIKE set 4 of 9.

| forecast | RMSE | MCS p (MSE) | in set (MSE) | QLIKE | MCS p (QLIKE) | in set (QLIKE) |
|---|---|---|---|---|---|---|
| HAR + IV | 0.859 | 1.000 | yes | 0.247 | 0.262 | yes |
| HAR + IV + MS-GARCH prob | 0.860 | 0.558 | yes | 0.247 | 0.236 | yes |
| HAR + IV + MS-GARCH | 0.868 | 0.323 | yes | 0.251 | 0.156 | yes |
| HAR + IV + credit | 0.872 | 0.364 | yes | 0.236 | 1.000 | yes |
| HAR | 0.932 | 0.323 | yes | 0.333 | 0.085 |  |
| HAR + credit | 0.934 | 0.323 | yes | 0.341 | 0.059 |  |
| GJR-GARCH | 0.971 | 0.323 | yes | 0.352 | 0.065 |  |
| MS-GARCH | 0.988 | 0.323 | yes | 0.345 | 0.085 |  |
| Two-state HMM implied vol | 1.081 | 0.323 | yes | 0.467 | 0.085 |  |

**Gold (GLD)**, 3,821 days: MSE set has 4 of 9 forecasts, QLIKE set 9 of 9.

| forecast | RMSE | MCS p (MSE) | in set (MSE) | QLIKE | MCS p (QLIKE) | in set (QLIKE) |
|---|---|---|---|---|---|---|
| HAR + IV + credit | 0.342 | 1.000 | yes | 0.228 | 0.672 | yes |
| HAR + IV | 0.344 | 0.617 | yes | 0.223 | 1.000 | yes |
| HAR + IV + MS-GARCH | 0.345 | 0.454 | yes | 0.224 | 0.672 | yes |
| HAR + IV + MS-GARCH prob | 0.349 | 0.196 | yes | 0.231 | 0.360 | yes |
| GJR-GARCH | 0.368 | 0.020 |  | 0.251 | 0.326 | yes |
| MS-GARCH | 0.370 | 0.020 |  | 0.251 | 0.360 | yes |
| HAR | 0.380 | 0.001 |  | 0.258 | 0.325 | yes |
| HAR + credit | 0.381 | 0.020 |  | 0.276 | 0.152 | yes |
| Two-state HMM implied vol | 0.392 | 0.020 |  | 0.277 | 0.326 | yes |

**Emerging markets (EEM)**, 3,119 days: MSE set has 4 of 9 forecasts, QLIKE set 8 of 9.

| forecast | RMSE | MCS p (MSE) | in set (MSE) | QLIKE | MCS p (QLIKE) | in set (QLIKE) |
|---|---|---|---|---|---|---|
| HAR + IV | 0.471 | 1.000 | yes | 0.253 | 1.000 | yes |
| HAR + IV + MS-GARCH | 0.472 | 0.726 | yes | 0.254 | 0.981 | yes |
| HAR + IV + MS-GARCH prob | 0.473 | 0.726 | yes | 0.255 | 0.981 | yes |
| HAR + IV + credit | 0.475 | 0.630 | yes | 0.262 | 0.733 | yes |
| MS-GARCH | 0.494 | 0.094 |  | 0.281 | 0.360 | yes |
| HAR | 0.498 | 0.052 |  | 0.257 | 0.981 | yes |
| GJR-GARCH | 0.504 | 0.094 |  | 0.271 | 0.733 | yes |
| HAR + credit | 0.504 | 0.052 |  | 0.294 | 0.192 | yes |
| Two-state HMM implied vol | 0.532 | 0.021 |  | 0.333 | 0.096 |  |

**Brazil (EWZ)**, 3,119 days: MSE set has 6 of 9 forecasts, QLIKE set 7 of 9.

| forecast | RMSE | MCS p (MSE) | in set (MSE) | QLIKE | MCS p (QLIKE) | in set (QLIKE) |
|---|---|---|---|---|---|---|
| HAR + IV + MS-GARCH prob | 0.860 | 1.000 | yes | 0.312 | 0.971 | yes |
| HAR + IV | 0.868 | 0.242 | yes | 0.316 | 0.971 | yes |
| HAR + IV + MS-GARCH | 0.870 | 0.242 | yes | 0.318 | 0.888 | yes |
| HAR + IV + credit | 0.872 | 0.242 | yes | 0.311 | 1.000 | yes |
| HAR | 0.892 | 0.100 | yes | 0.317 | 0.971 | yes |
| HAR + credit | 0.895 | 0.093 |  | 0.323 | 0.864 | yes |
| GJR-GARCH | 0.917 | 0.241 | yes | 0.335 | 0.726 | yes |
| MS-GARCH | 0.931 | 0.089 |  | 0.361 | 0.040 |  |
| Two-state HMM implied vol | 0.953 | 0.093 |  | 0.402 | 0.008 |  |

## S&P 500, 1996-2004 VIX holdout (examples/vol_forecast_vix.py --period early)

Class: post hoc, computed from the reproduced forecasts; not a registered test. Days scored per asset: S&P 500, 1996-2004 2,228.

### (a), (b) QLIKE beside RMSE, with equivalence bounds

The RMSE verdict column is the registered one (recomputed here to the printed digit, see the identity check at the top). The QLIKE interval was printed by the same frozen run as the registered secondary loss; the QLIKE verdict and every bound are post hoc. Bounds use the unrounded interval ends, in percent of the reference loss on the same days: for a "no difference" row, the largest improvement the interval still allows; for "better" or "worse", the smallest gain or loss it demonstrates.

| claim | forecast vs reference | expected | asset | ref RMSE | dRMSE 95% | RMSE verdict | RMSE bound | ref QLIKE | dQLIKE 95% | QLIKE verdict | QLIKE bound | same? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | VIX vs HAR | better | S&P 500, 1996-2004 | 0.387 | -0.054 to -0.003 | better | gain shown of at least 0.9% | 0.261 | -0.103 to -0.018 | better | gain shown of at least 6.9% |  |
| 2 | HAR + VIX vs HAR | better | S&P 500, 1996-2004 | 0.387 | -0.054 to -0.012 | better | gain shown of at least 3.2% | 0.261 | -0.102 to -0.032 | better | gain shown of at least 12.2% |  |
| 3 | HAR + HMM prob vs HAR | not better | S&P 500, 1996-2004 | 0.387 | -0.004 to +0.009 | no difference | gain excluded above 0.9% | 0.261 | +0.001 to +0.039 | worse | loss shown of at least 0.4% | changes |
| 4 | HAR + VIX + HMM prob vs HAR + VIX | not better | S&P 500, 1996-2004 | 0.353 | -0.007 to +0.006 | no difference | gain excluded above 2.0% | 0.196 | -0.008 to +0.015 | no difference | gain excluded above 3.9% |  |
| 5 | HAR + VIX + VIX-HMM prob vs HAR + VIX | not better | S&P 500, 1996-2004 | 0.353 | -0.005 to +0.008 | no difference | gain excluded above 1.4% | 0.196 | -0.006 to +0.017 | no difference | gain excluded above 3.2% |  |
| 6 | HMM implied vol vs HAR | worse | S&P 500, 1996-2004 | 0.387 | +0.016 to +0.094 | worse | loss shown of at least 4.0% | 0.261 | +0.026 to +0.192 | worse | loss shown of at least 9.8% |  |
| 7 | VIX-HMM implied vol vs HAR | worse | S&P 500, 1996-2004 | 0.387 | +0.003 to +0.094 | worse | loss shown of at least 0.9% | 0.261 | -0.014 to +0.168 | no difference | gain excluded above 5.4% | changes |

Per-asset verdicts that change between the two losses: 2 of 7.

### Claim outcomes under each loss and each bootstrap scheme

Columns as above. Claim A holds if HAR + VIX beats HAR; B holds if neither probability model beats HAR + VIX; C holds if both own forecasts are worse than HAR (VIX_HOLDOUT_PROTOCOL.md).

| claim | RMSE (registered, 63) | QLIKE (post hoc, 63) | RMSE c21 | RMSE c42 | RMSE c126 | RMSE s63 | QLIKE c21 | QLIKE c42 | QLIKE c126 | QLIKE s63 |
|---|---|---|---|---|---|---|---|---|---|---|
| A. VIX improves HAR | holds | holds | holds | holds | holds | holds | holds | holds | holds | holds |
| B. regime adds nothing once the VIX is in | holds | holds | holds | holds | holds | holds | holds | holds | holds | holds |
| C. regime models' own forecasts lose to HAR | holds | not shown | holds | holds | holds | holds | not shown | not shown | not shown | not shown |

### (c) HAC Diebold-Mariano, lag 20

Diebold and Mariano (1995) on the per-day loss difference with a Bartlett-kernel long-run variance truncated at 20 lags (the 21-day targets overlap, so the errors are MA(20) under the null). For RMSE the test is on the squared error (MSE), whose sign agrees with the RMSE difference; two-sided normal p-values. The last column repeats the bootstrap verdicts for comparison: a p below 0.05 and a bootstrap interval off zero should agree in sign.

| claim | asset | forecast vs reference | dMSE mean | DM stat (MSE) | p (MSE) | dQLIKE mean | DM stat (QLIKE) | p (QLIKE) | bootstrap RMSE / QLIKE |
|---|---|---|---|---|---|---|---|---|---|
| 1 | S&P 500, 1996-2004 | VIX vs HAR | -0.0228 | -2.58 | 0.010 | -0.0600 | -3.01 | 0.003 | better / better |
| 2 | S&P 500, 1996-2004 | HAR + VIX vs HAR | -0.0253 | -3.24 | 0.001 | -0.0653 | -3.86 | 0.000 | better / better |
| 3 | S&P 500, 1996-2004 | HAR + HMM prob vs HAR | +0.0019 | +0.83 | 0.407 | +0.0187 | +2.24 | 0.025 | no difference / worse |
| 4 | S&P 500, 1996-2004 | HAR + VIX + HMM prob vs HAR + VIX | -0.0008 | -0.41 | 0.682 | +0.0028 | +0.55 | 0.583 | no difference / no difference |
| 5 | S&P 500, 1996-2004 | HAR + VIX + VIX-HMM prob vs HAR + VIX | +0.0011 | +0.47 | 0.642 | +0.0049 | +0.93 | 0.353 | no difference / no difference |
| 6 | S&P 500, 1996-2004 | HMM implied vol vs HAR | +0.0451 | +3.00 | 0.003 | +0.1048 | +2.99 | 0.003 | worse / worse |
| 7 | S&P 500, 1996-2004 | VIX-HMM implied vol vs HAR | +0.0401 | +2.36 | 0.019 | +0.0704 | +1.81 | 0.070 | worse / no difference |

DM at 5% and the bootstrap interval agree on significance in 7 of 7 RMSE rows and 7 of 7 QLIKE rows.

### (d) Block-length sensitivity

Per-asset verdicts under each alternative bootstrap against the registered 63-day circular blocks. c = circular block of that length; s63 = stationary bootstrap (Politis and Romano 1994) with mean block 63.

| loss | scheme | verdicts changed | which |
|---|---|---|---|
| RMSE | c21 | 0 of 7 |  |
| RMSE | c42 | 0 of 7 |  |
| RMSE | c126 | 0 of 7 |  |
| RMSE | s63 | 0 of 7 |  |
| QLIKE | c21 | 0 of 7 |  |
| QLIKE | c42 | 0 of 7 |  |
| QLIKE | c126 | 0 of 7 |  |
| QLIKE | s63 | 1 of 7 | 3 S&P 500, 1996-2004 (worse -> no difference) |

### (c) Model confidence set per asset, 10%

Hansen, Lunde and Nason (2011) with the T_max statistic and the holdouts' 63-day circular block bootstrap (2,000 draws, seed 0), over every forecast in the scored table. A model is in the set if its MCS p-value is at least 0.10. The set is the group of forecasts that the data cannot separate from the best; it replaces nothing in the registered claim rule.

**all forecasts**, 2,228 days: MSE set has 4 of 11 forecasts, QLIKE set 4 of 11.

| forecast | RMSE | MCS p (MSE) | in set (MSE) | QLIKE | MCS p (QLIKE) | in set (QLIKE) |
|---|---|---|---|---|---|---|
| HAR + VIX + HMM prob | 0.352 | 1.000 | yes | 0.199 | 0.920 | yes |
| HAR + VIX | 0.353 | 0.803 | yes | 0.196 | 1.000 | yes |
| HAR + VIX + VIX-HMM prob | 0.354 | 0.803 | yes | 0.201 | 0.920 | yes |
| VIX | 0.356 | 0.803 | yes | 0.201 | 0.920 | yes |
| EWMA vol (0.94) | 0.378 | 0.053 |  | 0.234 | 0.046 |  |
| HAR | 0.387 | 0.045 |  | 0.261 | 0.036 |  |
| HAR + HMM prob | 0.390 | 0.045 |  | 0.280 | 0.009 |  |
| trailing 21-day vol | 0.396 | 0.045 |  | 0.278 | 0.009 |  |
| VIX-HMM implied vol | 0.436 | 0.045 |  | 0.331 | 0.036 |  |
| HMM implied vol | 0.442 | 0.018 |  | 0.366 | 0.009 |  |
| HMM high-vol probability | 0.450 | 0.018 |  | 0.440 | 0.000 |  |

## S&P 500, 2024-2026 VIX holdout (examples/vol_forecast_vix.py --period recent)

Class: post hoc, computed from the reproduced forecasts; not a registered test. Days scored per asset: S&P 500, 2024-2026 676.

### (a), (b) QLIKE beside RMSE, with equivalence bounds

The RMSE verdict column is the registered one (recomputed here to the printed digit, see the identity check at the top). The QLIKE interval was printed by the same frozen run as the registered secondary loss; the QLIKE verdict and every bound are post hoc. Bounds use the unrounded interval ends, in percent of the reference loss on the same days: for a "no difference" row, the largest improvement the interval still allows; for "better" or "worse", the smallest gain or loss it demonstrates.

| claim | forecast vs reference | expected | asset | ref RMSE | dRMSE 95% | RMSE verdict | RMSE bound | ref QLIKE | dQLIKE 95% | QLIKE verdict | QLIKE bound | same? |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | VIX vs HAR | better | S&P 500, 2024-2026 | 0.429 | -0.052 to +0.002 | no difference | gain excluded above 12.2% | 0.315 | -0.062 to +0.061 | no difference | gain excluded above 19.5% |  |
| 2 | HAR + VIX vs HAR | better | S&P 500, 2024-2026 | 0.429 | -0.053 to -0.001 | better | gain shown of at least 0.3% | 0.315 | -0.060 to +0.044 | no difference | gain excluded above 19.0% | changes |
| 3 | HAR + HMM prob vs HAR | not better | S&P 500, 2024-2026 | 0.429 | -0.033 to +0.010 | no difference | gain excluded above 7.6% | 0.315 | -0.071 to -0.004 | better | gain shown of at least 1.3% | changes |
| 4 | HAR + VIX + HMM prob vs HAR + VIX | not better | S&P 500, 2024-2026 | 0.406 | -0.015 to +0.004 | no difference | gain excluded above 3.7% | 0.297 | -0.038 to +0.002 | no difference | gain excluded above 12.8% |  |
| 5 | HAR + VIX + VIX-HMM prob vs HAR + VIX | not better | S&P 500, 2024-2026 | 0.406 | -0.003 to +0.005 | no difference | gain excluded above 0.8% | 0.297 | -0.002 to +0.019 | no difference | gain excluded above 0.8% |  |
| 6 | HMM implied vol vs HAR | worse | S&P 500, 2024-2026 | 0.429 | -0.063 to +0.023 | no difference | gain excluded above 14.7% | 0.315 | -0.100 to -0.013 | better | gain shown of at least 4.1% | changes |
| 7 | VIX-HMM implied vol vs HAR | worse | S&P 500, 2024-2026 | 0.429 | -0.035 to +0.034 | no difference | gain excluded above 8.2% | 0.315 | -0.061 to +0.005 | no difference | gain excluded above 19.4% |  |

Per-asset verdicts that change between the two losses: 3 of 7.

### Claim outcomes under each loss and each bootstrap scheme

Columns as above. Claim A holds if HAR + VIX beats HAR; B holds if neither probability model beats HAR + VIX; C holds if both own forecasts are worse than HAR (VIX_HOLDOUT_PROTOCOL.md).

| claim | RMSE (registered, 63) | QLIKE (post hoc, 63) | RMSE c21 | RMSE c42 | RMSE c126 | RMSE s63 | QLIKE c21 | QLIKE c42 | QLIKE c126 | QLIKE s63 |
|---|---|---|---|---|---|---|---|---|---|---|
| A. VIX improves HAR | holds | not shown | not shown | not shown | holds | holds | not shown | not shown | not shown | not shown |
| B. regime adds nothing once the VIX is in | holds | holds | holds | holds | holds | holds | holds | holds | holds | holds |
| C. regime models' own forecasts lose to HAR | not shown | not shown | not shown | not shown | not shown | not shown | not shown | not shown | not shown | not shown |

### (c) HAC Diebold-Mariano, lag 20

Diebold and Mariano (1995) on the per-day loss difference with a Bartlett-kernel long-run variance truncated at 20 lags (the 21-day targets overlap, so the errors are MA(20) under the null). For RMSE the test is on the squared error (MSE), whose sign agrees with the RMSE difference; two-sided normal p-values. The last column repeats the bootstrap verdicts for comparison: a p below 0.05 and a bootstrap interval off zero should agree in sign.

| claim | asset | forecast vs reference | dMSE mean | DM stat (MSE) | p (MSE) | dQLIKE mean | DM stat (QLIKE) | p (QLIKE) | bootstrap RMSE / QLIKE |
|---|---|---|---|---|---|---|---|---|---|
| 1 | S&P 500, 2024-2026 | VIX vs HAR | -0.0170 | -1.04 | 0.296 | -0.0121 | -0.31 | 0.756 | no difference / no difference |
| 2 | S&P 500, 2024-2026 | HAR + VIX vs HAR | -0.0185 | -1.24 | 0.215 | -0.0176 | -0.52 | 0.602 | better / no difference |
| 3 | S&P 500, 2024-2026 | HAR + HMM prob vs HAR | -0.0124 | -1.23 | 0.218 | -0.0320 | -1.94 | 0.053 | no difference / better |
| 4 | S&P 500, 2024-2026 | HAR + VIX + HMM prob vs HAR + VIX | -0.0061 | -1.19 | 0.234 | -0.0154 | -1.35 | 0.176 | no difference / no difference |
| 5 | S&P 500, 2024-2026 | HAR + VIX + VIX-HMM prob vs HAR + VIX | +0.0015 | +0.78 | 0.438 | +0.0057 | +0.98 | 0.326 | no difference / no difference |
| 6 | S&P 500, 2024-2026 | HMM implied vol vs HAR | -0.0212 | -1.25 | 0.210 | -0.0536 | -2.32 | 0.020 | no difference / better |
| 7 | S&P 500, 2024-2026 | VIX-HMM implied vol vs HAR | -0.0060 | -0.39 | 0.698 | -0.0282 | -1.45 | 0.148 | no difference / no difference |

DM at 5% and the bootstrap interval agree on significance in 6 of 7 RMSE rows and 6 of 7 QLIKE rows.

### (d) Block-length sensitivity

Per-asset verdicts under each alternative bootstrap against the registered 63-day circular blocks. c = circular block of that length; s63 = stationary bootstrap (Politis and Romano 1994) with mean block 63.

| loss | scheme | verdicts changed | which |
|---|---|---|---|
| RMSE | c21 | 1 of 7 | 2 S&P 500, 2024-2026 (better -> no difference) |
| RMSE | c42 | 1 of 7 | 2 S&P 500, 2024-2026 (better -> no difference) |
| RMSE | c126 | 0 of 7 |  |
| RMSE | s63 | 0 of 7 |  |
| QLIKE | c21 | 0 of 7 |  |
| QLIKE | c42 | 0 of 7 |  |
| QLIKE | c126 | 1 of 7 | 7 S&P 500, 2024-2026 (no difference -> better) |
| QLIKE | s63 | 0 of 7 |  |

### (c) Model confidence set per asset, 10%

Hansen, Lunde and Nason (2011) with the T_max statistic and the holdouts' 63-day circular block bootstrap (2,000 draws, seed 0), over every forecast in the scored table. A model is in the set if its MCS p-value is at least 0.10. The set is the group of forecasts that the data cannot separate from the best; it replaces nothing in the registered claim rule.

**all forecasts**, 676 days: MSE set has 11 of 11 forecasts, QLIKE set 10 of 11.

| forecast | RMSE | MCS p (MSE) | in set (MSE) | QLIKE | MCS p (QLIKE) | in set (QLIKE) |
|---|---|---|---|---|---|---|
| HAR + VIX + HMM prob | 0.399 | 1.000 | yes | 0.282 | 0.793 | yes |
| HMM implied vol | 0.403 | 0.947 | yes | 0.261 | 1.000 | yes |
| HAR + VIX | 0.406 | 0.947 | yes | 0.297 | 0.793 | yes |
| HAR + VIX + VIX-HMM prob | 0.408 | 0.947 | yes | 0.303 | 0.752 | yes |
| VIX | 0.408 | 0.947 | yes | 0.303 | 0.733 | yes |
| HMM high-vol probability | 0.410 | 0.947 | yes | 0.265 | 0.793 | yes |
| HAR + HMM prob | 0.414 | 0.683 | yes | 0.283 | 0.793 | yes |
| VIX-HMM implied vol | 0.422 | 0.567 | yes | 0.287 | 0.793 | yes |
| HAR | 0.429 | 0.525 | yes | 0.315 | 0.106 | yes |
| trailing 21-day vol | 0.445 | 0.408 | yes | 0.340 | 0.045 |  |
| EWMA vol (0.94) | 0.454 | 0.567 | yes | 0.349 | 0.106 | yes |

## (e) Raw next to recalibrated own forecasts

Class: post hoc, computed from the reproduced forecasts; not a registered test. Every "own forecast" in the result tables is the model's implied vol pushed through the same log-scale walk-forward regression as the other signals (desk finding 7: that regression is fit by least squares in logs, which is neither RMSE on vol nor QLIKE on variance, so it need not help a model on both losses). Here the raw implied vol is scored on the same days, beside its calibrated version and against the claim's reference. The "raw - calibrated" intervals are paired 63-day block bootstraps; "raw better" means the calibration hurt the model on that loss.

**S&P 500, 1996-2004** (raw table printed by the frozen script, reference HAR as in comparisons 6 and 7)

| model | days | raw RMSE | calibrated RMSE | raw QLIKE | calibrated QLIKE | raw mean / target mean | dRMSE raw - calibrated | dQLIKE raw - calibrated | raw vs HAR, dRMSE | raw vs HAR, dQLIKE |
|---|---|---|---|---|---|---|---|---|---|---|
| HMM implied vol | 2228 | 0.417 | 0.442 | 0.289 | 0.366 | 1.00 / 1.12 | -0.073 to +0.017 (no difference) | -0.165 to +0.005 (no difference) | -0.006 to +0.065 no difference | -0.025 to +0.089 no difference |
| VIX-HMM implied vol | 2228 | 0.420 | 0.436 | 0.289 | 0.331 | 1.01 / 1.12 | -0.055 to +0.019 (no difference) | -0.115 to +0.026 (no difference) | -0.010 to +0.076 no difference | -0.045 to +0.114 no difference |
| EWMA vol (0.94) | 2228 | 0.398 | 0.378 | 0.220 | 0.234 | 1.13 / 1.12 | -0.005 to +0.047 (no difference) | -0.048 to +0.013 (no difference) | -0.014 to +0.039 no difference | -0.082 to -0.008 better |
| trailing 21-day vol | 2228 | 0.438 | 0.396 | 0.284 | 0.278 | 1.12 / 1.12 | +0.007 to +0.076 (raw worse) | -0.038 to +0.043 (no difference) | +0.017 to +0.085 worse | -0.015 to +0.057 no difference |
| VIX | 2228 | 0.465 | 0.356 | 0.230 | 0.201 | 1.43 / 1.12 | +0.032 to +0.186 (raw worse) | -0.060 to +0.106 (no difference) | +0.001 to +0.157 worse | -0.135 to +0.062 no difference |

**S&P 500, 2024-2026** (raw table printed by the frozen script, reference HAR as in comparisons 6 and 7)

| model | days | raw RMSE | calibrated RMSE | raw QLIKE | calibrated QLIKE | raw mean / target mean | dRMSE raw - calibrated | dQLIKE raw - calibrated | raw vs HAR, dRMSE | raw vs HAR, dQLIKE |
|---|---|---|---|---|---|---|---|---|---|---|
| HMM implied vol | 676 | 0.454 | 0.403 | 0.301 | 0.261 | 1.08 / 0.86 | -0.007 to +0.115 (no difference) | -0.060 to +0.109 (no difference) | -0.061 to +0.129 no difference | -0.149 to +0.084 no difference |
| VIX-HMM implied vol | 676 | 0.499 | 0.422 | 0.318 | 0.287 | 1.08 / 0.86 | -0.019 to +0.181 (no difference) | -0.102 to +0.121 (no difference) | -0.044 to +0.209 no difference | -0.153 to +0.118 no difference |
| EWMA vol (0.94) | 676 | 0.505 | 0.454 | 0.414 | 0.349 | 0.89 / 0.86 | +0.002 to +0.107 (raw worse) | +0.018 to +0.122 (raw worse) | -0.011 to +0.167 no difference | +0.019 to +0.193 worse |
| trailing 21-day vol | 676 | 0.529 | 0.445 | 0.509 | 0.340 | 0.86 / 0.86 | +0.004 to +0.173 (raw worse) | +0.055 to +0.316 (raw worse) | +0.009 to +0.204 worse | +0.067 to +0.364 worse |
| VIX | 676 | 0.480 | 0.408 | 0.339 | 0.303 | 1.11 / 0.86 | +0.003 to +0.163 (raw worse) | -0.128 to +0.146 (no difference) | -0.012 to +0.143 no difference | -0.074 to +0.110 no difference |

**Cross-index, Nasdaq-100** (raw implied vols are close-to-close daily vol; the target is the 21-session RMS of 5-minute RV (no overnight), so the raw numbers forecast a different scale and the calibration also does the scale change)

| model | days | raw RMSE | calibrated RMSE | raw QLIKE | calibrated QLIKE | raw mean / target mean | dRMSE raw - calibrated | dQLIKE raw - calibrated | raw vs HAR-RV + IV, dRMSE | raw vs HAR-RV + IV, dQLIKE |
|---|---|---|---|---|---|---|---|---|---|---|
| Two-state HMM implied vol | 3286 | 0.748 | 0.377 | 0.501 | 0.312 | 1.50 / 0.93 | +0.249 to +0.485 (raw worse) | -0.004 to +0.333 (no difference) | +0.297 to +0.518 worse | +0.137 to +0.383 worse |
| GJR-GARCH | 3286 | 0.587 | 0.360 | 0.335 | 0.282 | 1.27 / 0.93 | +0.148 to +0.317 (raw worse) | -0.065 to +0.141 (no difference) | +0.166 to +0.336 worse | +0.023 to +0.175 worse |
| MSM | 3286 | 0.608 | 0.370 | 0.386 | 0.277 | 1.35 / 0.93 | +0.150 to +0.328 (raw worse) | -0.042 to +0.213 (no difference) | +0.183 to +0.355 worse | +0.048 to +0.246 worse |

**Cross-index, Dow Jones Industrial Average** (raw implied vols are close-to-close daily vol; the target is the 21-session RMS of 5-minute RV (no overnight), so the raw numbers forecast a different scale and the calibration also does the scale change)

| model | days | raw RMSE | calibrated RMSE | raw QLIKE | calibrated QLIKE | raw mean / target mean | dRMSE raw - calibrated | dQLIKE raw - calibrated | raw vs HAR-RV + IV, dRMSE | raw vs HAR-RV + IV, dQLIKE |
|---|---|---|---|---|---|---|---|---|---|---|
| Two-state HMM implied vol | 3297 | 0.512 | 0.361 | 0.505 | 0.435 | 1.03 / 0.68 | +0.055 to +0.261 (raw worse) | -0.237 to +0.284 (no difference) | +0.126 to +0.289 worse | +0.002 to +0.340 worse |
| GJR-GARCH | 3297 | 0.509 | 0.323 | 0.364 | 0.345 | 0.94 / 0.68 | +0.088 to +0.298 (raw worse) | -0.137 to +0.134 (no difference) | +0.094 to +0.306 worse | -0.133 to +0.172 no difference |
| MSM | 3297 | 0.484 | 0.345 | 0.442 | 0.373 | 1.00 / 0.68 | +0.047 to +0.245 (raw worse) | -0.154 to +0.229 (no difference) | +0.084 to +0.270 worse | -0.060 to +0.267 no difference |

**Cross-index, Russell 2000** (raw implied vols are close-to-close daily vol; the target is the 21-session RMS of 5-minute RV (no overnight), so the raw numbers forecast a different scale and the calibration also does the scale change)

| model | days | raw RMSE | calibrated RMSE | raw QLIKE | calibrated QLIKE | raw mean / target mean | dRMSE raw - calibrated | dQLIKE raw - calibrated | raw vs HAR-RV + IV, dRMSE | raw vs HAR-RV + IV, dQLIKE |
|---|---|---|---|---|---|---|---|---|---|---|
| Two-state HMM implied vol | 1513 | 0.547 | 0.370 | 0.232 | 0.182 | 1.50 / 1.15 | +0.112 to +0.243 (raw worse) | -0.029 to +0.111 (no difference) | +0.174 to +0.327 worse | +0.065 to +0.159 worse |
| GJR-GARCH | 1513 | 0.408 | 0.318 | 0.158 | 0.141 | 1.35 / 1.15 | +0.045 to +0.143 (raw worse) | -0.030 to +0.057 (no difference) | +0.058 to +0.169 worse | -0.007 to +0.084 no difference |
| MSM | 1513 | 0.540 | 0.312 | 0.249 | 0.125 | 1.57 / 1.15 | +0.162 to +0.300 (raw worse) | +0.055 to +0.176 (raw worse) | +0.172 to +0.319 worse | +0.069 to +0.190 worse |

**ETF, Crude oil (USO)** (raw implied vols from the frozen checkpoints in data/checkpoints/msgarch_credit/)

| model | days | raw RMSE | calibrated RMSE | raw QLIKE | calibrated QLIKE | raw mean / target mean | dRMSE raw - calibrated | dQLIKE raw - calibrated | raw vs HAR + IV, dRMSE | raw vs HAR + IV, dQLIKE |
|---|---|---|---|---|---|---|---|---|---|---|
| Two-state HMM implied vol | 3604 | 1.067 | 1.081 | 0.384 | 0.467 | 2.23 / 2.06 | -0.064 to +0.060 (no difference) | -0.221 to +0.006 (no difference) | +0.086 to +0.339 worse | +0.054 to +0.265 worse |
| GJR-GARCH | 3604 | 1.021 | 0.971 | 0.323 | 0.352 | 2.16 / 2.06 | -0.017 to +0.133 (no difference) | -0.075 to +0.001 (no difference) | +0.046 to +0.319 worse | +0.031 to +0.133 worse |
| MS-GARCH | 3604 | 1.014 | 0.988 | 0.312 | 0.345 | 2.10 / 2.06 | -0.037 to +0.106 (no difference) | -0.070 to -0.007 (raw better) | +0.023 to +0.334 worse | +0.017 to +0.123 worse |

**ETF, Gold (GLD)** (raw implied vols from the frozen checkpoints in data/checkpoints/msgarch_credit/)

| model | days | raw RMSE | calibrated RMSE | raw QLIKE | calibrated QLIKE | raw mean / target mean | dRMSE raw - calibrated | dQLIKE raw - calibrated | raw vs HAR + IV, dRMSE | raw vs HAR + IV, dQLIKE |
|---|---|---|---|---|---|---|---|---|---|---|
| Two-state HMM implied vol | 3821 | 0.406 | 0.392 | 0.265 | 0.277 | 1.11 / 0.98 | -0.007 to +0.037 (no difference) | -0.054 to +0.025 (no difference) | +0.027 to +0.100 worse | -0.049 to +0.106 no difference |
| GJR-GARCH | 3821 | 0.378 | 0.368 | 0.239 | 0.251 | 1.05 / 0.98 | -0.001 to +0.025 (no difference) | -0.034 to +0.006 (no difference) | +0.016 to +0.057 worse | -0.022 to +0.046 no difference |
| MS-GARCH | 3821 | 0.379 | 0.370 | 0.237 | 0.251 | 1.04 / 0.98 | -0.000 to +0.019 (no difference) | -0.036 to +0.003 (no difference) | +0.019 to +0.051 worse | -0.027 to +0.043 no difference |

**ETF, Emerging markets (EEM)** (raw implied vols from the frozen checkpoints in data/checkpoints/msgarch_credit/)

| model | days | raw RMSE | calibrated RMSE | raw QLIKE | calibrated QLIKE | raw mean / target mean | dRMSE raw - calibrated | dQLIKE raw - calibrated | raw vs HAR + IV, dRMSE | raw vs HAR + IV, dQLIKE |
|---|---|---|---|---|---|---|---|---|---|---|
| Two-state HMM implied vol | 3119 | 0.664 | 0.532 | 0.358 | 0.333 | 1.57 / 1.19 | +0.048 to +0.225 (raw worse) | -0.134 to +0.137 (no difference) | +0.108 to +0.290 worse | -0.020 to +0.193 no difference |
| GJR-GARCH | 3119 | 0.537 | 0.504 | 0.245 | 0.271 | 1.34 / 1.19 | +0.005 to +0.066 (raw worse) | -0.084 to +0.020 (no difference) | +0.021 to +0.118 worse | -0.112 to +0.052 no difference |
| MS-GARCH | 3119 | 0.508 | 0.494 | 0.252 | 0.281 | 1.30 / 1.19 | -0.009 to +0.046 (no difference) | -0.086 to +0.014 (no difference) | +0.005 to +0.078 worse | -0.095 to +0.056 no difference |

**ETF, Brazil (EWZ)** (raw implied vols from the frozen checkpoints in data/checkpoints/msgarch_credit/)

| model | days | raw RMSE | calibrated RMSE | raw QLIKE | calibrated QLIKE | raw mean / target mean | dRMSE raw - calibrated | dQLIKE raw - calibrated | raw vs HAR + IV, dRMSE | raw vs HAR + IV, dQLIKE |
|---|---|---|---|---|---|---|---|---|---|---|
| Two-state HMM implied vol | 3119 | 0.979 | 0.953 | 0.314 | 0.402 | 2.31 / 1.97 | -0.057 to +0.154 (no difference) | -0.278 to +0.034 (no difference) | +0.037 to +0.245 worse | -0.186 to +0.107 no difference |
| GJR-GARCH | 3119 | 0.968 | 0.917 | 0.281 | 0.335 | 2.11 / 1.97 | -0.015 to +0.140 (no difference) | -0.130 to -0.004 (raw better) | +0.010 to +0.222 worse | -0.189 to +0.052 no difference |
| MS-GARCH | 3119 | 0.913 | 0.931 | 0.288 | 0.361 | 2.10 / 1.97 | -0.080 to +0.082 (no difference) | -0.193 to +0.004 (no difference) | -0.023 to +0.171 no difference | -0.170 to +0.056 no difference |

## (f) The unregistered comparison: regime models' own forecasts vs HAR + VIX, S&P 500

Class: post hoc, computed from the reproduced forecasts; not a registered test. The registered comparison 6 is HMM implied vol vs HAR without the VIX (VIX_HOLDOUT_PROTOCOL.md); the README's "every holdout but one" sentence reads as if it were against HAR + VIX (desk finding 1). This is that interval, computed the same way.

| period | forecast vs reference | RMSE / ref | dRMSE 95% | RMSE bound | QLIKE / ref | dQLIKE 95% | QLIKE bound | DM p (MSE / QLIKE) |
|---|---|---|---|---|---|---|---|---|
| S&P 500, 1996-2004 | HMM implied vol vs HAR + VIX | 0.442 / 0.353 | +0.044 to +0.133 worse | loss shown of at least 12.4% | 0.366 / 0.196 | +0.077 to +0.275 worse | loss shown of at least 39.5% | 0.000 / 0.000 |
| S&P 500, 1996-2004 | VIX-HMM implied vol vs HAR + VIX | 0.436 / 0.353 | +0.029 to +0.135 worse | loss shown of at least 8.2% | 0.331 / 0.196 | +0.038 to +0.256 worse | loss shown of at least 19.7% | 0.001 / 0.003 |
| S&P 500, 2024-2026 | HMM implied vol vs HAR + VIX | 0.403 / 0.406 | -0.038 to +0.052 no difference | gain excluded above 9.3% | 0.261 / 0.297 | -0.136 to +0.033 no difference | gain excluded above 45.6% | 0.881 / 0.425 |
| S&P 500, 2024-2026 | VIX-HMM implied vol vs HAR + VIX | 0.422 / 0.406 | -0.010 to +0.056 no difference | gain excluded above 2.3% | 0.287 / 0.297 | -0.089 to +0.043 no difference | gain excluded above 29.8% | 0.285 / 0.778 |

## (g) Own-row vs common-row calibration in the VIX script

Class: post hoc, computed from the reproduced forecasts; not a registered test. `examples/vol_forecast_vix.py` fits each feature set's calibration on the rows where that set exists, so HAR and HAR + VIX train on about three more years than the sets that include an HMM probability, and the HMM's own forecast trains on three fewer years than the HAR it is compared with (desk finding 6, sized there on development data only). The other two holdout scripts reindex every set to the common rows. Here every set is recalibrated on the common rows from the saved walk-forward HMM outputs and the cached data, after checking that the own-row recalibration reproduces the registered forecasts.

**S&P 500, 1996-2004**: own-row first forecast dates HAR 1993-03-01, HAR + VIX 1993-03-01, HAR + VIX + HMM prob 1996-01-25; common-row first forecast date 1996-01-25 for every set; first training row on common rows 1992-12-29 (own rows: 1990-02-01 for HAR). Scored days: 2,228 registered, 2,228 common to both calibrations.

| forecast | RMSE own rows | RMSE common rows | dRMSE own - common | QLIKE own rows | QLIKE common rows | dQLIKE own - common |
|---|---|---|---|---|---|---|
| HMM high-vol probability | 0.4501 | 0.4501 | +0.000 to +0.000 no difference | 0.4399 | 0.4399 | +0.000 to +0.000 no difference |
| HMM implied vol | 0.4416 | 0.4416 | +0.000 to +0.000 no difference | 0.3657 | 0.3657 | +0.000 to +0.000 no difference |
| VIX-HMM implied vol | 0.4359 | 0.4359 | +0.000 to +0.000 no difference | 0.3313 | 0.3313 | +0.000 to +0.000 no difference |
| EWMA vol (0.94) | 0.3782 | 0.3822 | -0.010 to +0.002 no difference | 0.2340 | 0.2508 | -0.035 to -0.000 better |
| trailing 21-day vol | 0.3964 | 0.4020 | -0.013 to +0.001 no difference | 0.2780 | 0.3019 | -0.048 to -0.002 better |
| HAR | 0.3871 | 0.3916 | -0.011 to +0.001 no difference | 0.2610 | 0.2808 | -0.041 to -0.001 better |
| VIX | 0.3564 | 0.3534 | -0.007 to +0.012 no difference | 0.2009 | 0.1991 | -0.013 to +0.015 no difference |
| HAR + VIX | 0.3529 | 0.3531 | -0.007 to +0.006 no difference | 0.1957 | 0.1991 | -0.015 to +0.007 no difference |
| HAR + HMM prob | 0.3896 | 0.3896 | +0.000 to +0.000 no difference | 0.2796 | 0.2796 | +0.000 to +0.000 no difference |
| HAR + VIX + HMM prob | 0.3518 | 0.3518 | +0.000 to +0.000 no difference | 0.1985 | 0.1985 | +0.000 to +0.000 no difference |
| HAR + VIX + VIX-HMM prob | 0.3544 | 0.3544 | +0.000 to +0.000 no difference | 0.2006 | 0.2006 | +0.000 to +0.000 no difference |

The seven comparisons under each calibration, on the days common to both:

| forecast vs reference | dRMSE own rows | dRMSE common rows | dQLIKE own rows | dQLIKE common rows | verdict moves |
|---|---|---|---|---|---|
| VIX vs HAR | -0.054 to -0.003 better | -0.064 to -0.009 better | -0.103 to -0.018 better | -0.135 to -0.033 better |  |
| HAR + VIX vs HAR | -0.054 to -0.012 better | -0.060 to -0.015 better | -0.102 to -0.032 better | -0.126 to -0.042 better |  |
| HAR + HMM prob vs HAR | -0.004 to +0.009 no difference | -0.004 to +0.000 no difference | +0.001 to +0.039 worse | -0.006 to +0.004 no difference | yes |
| HAR + VIX + HMM prob vs HAR + VIX | -0.007 to +0.006 no difference | -0.003 to +0.001 no difference | -0.008 to +0.015 no difference | -0.003 to +0.002 no difference |  |
| HAR + VIX + VIX-HMM prob vs HAR + VIX | -0.005 to +0.008 no difference | -0.006 to +0.009 no difference | -0.006 to +0.017 no difference | -0.006 to +0.010 no difference |  |
| HMM implied vol vs HAR | +0.016 to +0.094 worse | +0.014 to +0.088 worse | +0.026 to +0.192 worse | +0.019 to +0.159 worse |  |
| VIX-HMM implied vol vs HAR | +0.003 to +0.094 worse | -0.000 to +0.088 no difference | -0.014 to +0.168 no difference | -0.024 to +0.140 no difference | yes |

RMSE claim outcomes, own rows (registered) vs common rows: A. VIX improves HAR: holds vs holds; B. regime adds nothing once the VIX is in: holds vs holds; C. regime models' own forecasts lose to HAR: holds vs not shown.

**S&P 500, 2024-2026**: own-row first forecast dates HAR 2008-03-07, HAR + VIX 2008-03-07, HAR + VIX + HMM prob 2011-02-04; common-row first forecast date 2011-02-04 for every set; first training row on common rows 2008-01-07 (own rows: 2005-02-03 for HAR). Scored days: 676 registered, 676 common to both calibrations.

| forecast | RMSE own rows | RMSE common rows | dRMSE own - common | QLIKE own rows | QLIKE common rows | dQLIKE own - common |
|---|---|---|---|---|---|---|
| HMM high-vol probability | 0.4104 | 0.4104 | +0.000 to +0.000 no difference | 0.2649 | 0.2649 | +0.000 to +0.000 no difference |
| HMM implied vol | 0.4030 | 0.4030 | +0.000 to +0.000 no difference | 0.2614 | 0.2614 | +0.000 to +0.000 no difference |
| VIX-HMM implied vol | 0.4215 | 0.4215 | +0.000 to +0.000 no difference | 0.2869 | 0.2869 | +0.000 to +0.000 no difference |
| EWMA vol (0.94) | 0.4535 | 0.4554 | -0.006 to +0.001 no difference | 0.3489 | 0.3461 | -0.003 to +0.011 no difference |
| trailing 21-day vol | 0.4453 | 0.4477 | -0.008 to +0.002 no difference | 0.3405 | 0.3363 | -0.005 to +0.016 no difference |
| HAR | 0.4285 | 0.4304 | -0.007 to +0.002 no difference | 0.3150 | 0.3116 | -0.005 to +0.014 no difference |
| VIX | 0.4082 | 0.4086 | -0.001 to +0.001 no difference | 0.3030 | 0.3053 | -0.007 to +0.001 no difference |
| HAR + VIX | 0.4063 | 0.4067 | -0.001 to +0.001 no difference | 0.2974 | 0.2986 | -0.004 to +0.001 no difference |
| HAR + HMM prob | 0.4138 | 0.4138 | +0.000 to +0.000 no difference | 0.2831 | 0.2831 | +0.000 to +0.000 no difference |
| HAR + VIX + HMM prob | 0.3987 | 0.3987 | +0.000 to +0.000 no difference | 0.2821 | 0.2821 | +0.000 to +0.000 no difference |
| HAR + VIX + VIX-HMM prob | 0.4082 | 0.4082 | +0.000 to +0.000 no difference | 0.3032 | 0.3032 | +0.000 to +0.000 no difference |

The seven comparisons under each calibration, on the days common to both:

| forecast vs reference | dRMSE own rows | dRMSE common rows | dQLIKE own rows | dQLIKE common rows | verdict moves |
|---|---|---|---|---|---|
| VIX vs HAR | -0.052 to +0.002 no difference | -0.058 to +0.003 no difference | -0.062 to +0.061 no difference | -0.062 to +0.079 no difference |  |
| HAR + VIX vs HAR | -0.053 to -0.001 better | -0.057 to -0.001 better | -0.060 to +0.044 no difference | -0.060 to +0.058 no difference |  |
| HAR + HMM prob vs HAR | -0.033 to +0.010 no difference | -0.032 to +0.005 no difference | -0.071 to -0.004 better | -0.060 to -0.004 better |  |
| HAR + VIX + HMM prob vs HAR + VIX | -0.015 to +0.004 no difference | -0.015 to +0.003 no difference | -0.038 to +0.002 no difference | -0.040 to -0.000 better | yes |
| HAR + VIX + VIX-HMM prob vs HAR + VIX | -0.003 to +0.005 no difference | -0.003 to +0.004 no difference | -0.002 to +0.019 no difference | -0.003 to +0.017 no difference |  |
| HMM implied vol vs HAR | -0.063 to +0.023 no difference | -0.063 to +0.018 no difference | -0.100 to -0.013 better | -0.090 to -0.015 better |  |
| VIX-HMM implied vol vs HAR | -0.035 to +0.034 no difference | -0.036 to +0.029 no difference | -0.061 to +0.005 no difference | -0.052 to +0.004 no difference |  |

RMSE claim outcomes, own rows (registered) vs common rows: A. VIX improves HAR: holds vs holds; B. regime adds nothing once the VIX is in: holds vs holds; C. regime models' own forecasts lose to HAR: not shown vs not shown.
