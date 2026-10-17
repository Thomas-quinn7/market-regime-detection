development data only, no holdout

# Development-only continuations, October 2026

Class of every table in this file: **development data only (S&P 500, 2005-2023), no holdout**. These are continuations of the development work, not claims; no holdout is opened and no registered verdict is touched. Written by `examples/dev_continuations.py` at 8e454ec plus uncommitted files, 2026-10-17 22:16Z, 2,000 bootstrap draws (seed 0). Data: S&P 500 and VIX 2005-01-04 to 2023-12-29 (4780 days) from the committed caches.

## (a) Forecast horizon: 5, 21 and 63 trading days

Same construction as the frozen VIX script at every horizon: target = realised vol over the next h days; expanding OLS on log HAR inputs (and log VIX / sqrt(252), and the walk-forward HMM high-vol probability), log target, refit every 63 days after 756 rows, embargo h; paired circular block bootstrap on the scored days. The HMM is refit walk-forward with the same arguments as in the VIX script (min_train 756, step 63). The 21-day row is the development-period version of the registered comparisons and is here only for scale.

### Horizon 5: scored days 3258, 2011-01-12 -> 2023-12-21; HMM refits 64, converged 64 of 64

| model | RMSE | QLIKE |
|---|---|---|
| HAR | 0.541 | 0.601 |
| HAR + VIX | 0.486 | 0.445 |
| HAR + HMM prob | 0.541 | 0.570 |
| HAR + VIX + HMM prob | 0.487 | 0.464 |

| forecast | reference | block | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|
| HAR + VIX | HAR | 63 | -0.084 to -0.025 | better | -0.216 to -0.108 | better |
| HAR + HMM prob | HAR | 63 | -0.006 to +0.007 | no difference | -0.053 to -0.015 | better |
| HAR + VIX + HMM prob | HAR + VIX | 63 | -0.004 to +0.008 | no difference | +0.006 to +0.034 | worse |

### Horizon 21: scored days 3226, 2011-02-04 -> 2023-11-29; HMM refits 64, converged 64 of 64

| model | RMSE | QLIKE |
|---|---|---|
| HAR | 0.508 | 0.468 |
| HAR + VIX | 0.479 | 0.422 |
| HAR + HMM prob | 0.510 | 0.452 |
| HAR + VIX + HMM prob | 0.484 | 0.441 |
| HAR + VIX + noise | 0.479 | 0.423 |

| forecast | reference | block | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|
| HAR + VIX | HAR | 63 | -0.046 to -0.012 | better | -0.093 to +0.006 | no difference |
| HAR + HMM prob | HAR | 63 | -0.005 to +0.014 | no difference | -0.036 to +0.002 | no difference |
| HAR + VIX + HMM prob | HAR + VIX | 63 | -0.002 to +0.015 | no difference | -0.001 to +0.046 | no difference |

### Horizon 63: scored days 3142, 2011-04-06 -> 2023-09-29; HMM refits 64, converged 64 of 64

| model | RMSE | QLIKE |
|---|---|---|
| HAR | 0.524 | 0.580 |
| HAR + VIX | 0.509 | 0.538 |
| HAR + HMM prob | 0.536 | 0.563 |
| HAR + VIX + HMM prob | 0.526 | 0.553 |

| forecast | reference | block | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|
| HAR + VIX | HAR | 63 | -0.029 to -0.004 | better | -0.086 to -0.010 | better |
| HAR + HMM prob | HAR | 63 | -0.000 to +0.033 | no difference | -0.068 to +0.018 | no difference |
| HAR + VIX + HMM prob | HAR + VIX | 63 | +0.006 to +0.037 | worse | -0.001 to +0.028 | no difference |
| HAR + VIX | HAR | 126 | -0.030 to -0.003 | better | -0.086 to -0.007 | better |
| HAR + HMM prob | HAR | 126 | -0.001 to +0.037 | no difference | -0.070 to +0.023 | no difference |
| HAR + VIX + HMM prob | HAR + VIX | 126 | +0.005 to +0.042 | worse | -0.002 to +0.031 | no difference |

Summary, the regime-probability question at each horizon:

| horizon | HAR + VIX + HMM prob vs HAR + VIX, dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|
| 5 | -0.004 to +0.008 | no difference | +0.006 to +0.034 | worse |
| 21 | -0.002 to +0.015 | no difference | -0.001 to +0.046 | no difference |
| 63 | +0.006 to +0.037 | worse | -0.001 to +0.028 | no difference |

## (c) Nesting-noise check at the 21-day horizon

A standard-normal regressor with no information (seed 0) added to HAR + VIX and scored against HAR + VIX with the same bootstrap, beside the HMM probability's row from (a).

| forecast | reference | block | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|
| HAR + VIX + noise | HAR + VIX | 63 | -0.000 to +0.001 | no difference | -0.001 to +0.004 | no difference |
| HAR + VIX + HMM prob | HAR + VIX | 63 | -0.002 to +0.015 | no difference | -0.001 to +0.046 | no difference |

One line: on development data the pure-noise regressor gives -0.000 to +0.001 (no difference) and the HMM probability -0.002 to +0.015 (no difference); a 'no difference' verdict for a nested regressor is what nesting alone produces when the added regressor carries nothing, so the HMM probability's verdict should be read against this noise row, not against zero.

## (b) K = 3 and 4 Student-t HMMs

Not run yet; separate script.

