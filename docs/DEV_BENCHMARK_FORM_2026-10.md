development data only (S&P 500, to 2022-12-30), no holdout, not a claim

# Development-only benchmark form check: HAR + VIX in levels vs in logs, October 2026

Class of every table in this file: **development data only (S&P 500, to 2022-12-30), no holdout, not a claim**. Written by `examples/dev_benchmark_form.py` at feff299 plus uncommitted files, 2026-10-19 15:26Z, 2,000 bootstrap draws (seed 0). Data: S&P 500 returns and the VIX 2005-01-04 to 2022-12-30 (4530 days), ES 5-minute RV 2010-06-07 to 2022-12-30 (3227 days), every input clipped to <= 2022-12-30 at load. Stage S9 of the reopen.

Forms: *level* = HAR inputs and VIX / sqrt(252) in levels; *log* = the same inputs in logs (Corsi log-HAR; the form MR's frozen scripts use, `examples/vol_forecast_vix.py` lines 104-132). Both regress the log target with the lognormal mean correction; the HMM probability and the noise regressor (standard normal, seed 0) enter linearly. Expanding OLS, refit every 63 rows after 756, embargo h; all eight sets at a horizon fitted and scored on the same rows. Paired circular block bootstrap, block max(63, h); HAC Diebold-Mariano, lag max(20, h - 1), on squared errors (SE) and QLIKE. A negative difference favours the forecast. Target A is MR's (daily-return realised vol; at h = 1 that is |r_{t+1}| and the zero-return days drop out); target B is the implied-horizon-vol study's (ES 5-minute RV from 2010-06-07, HAR inputs built from the RV). The HMM is MR's two-state walk-forward model on daily returns (min_train 756, step 63), refit per horizon. *windows* = scored days / h.

## Target A, horizon 1

Target daily-return realised vol (MR's target). Scored days 3,015, 2011-01-06 to 2022-12-29; non-overlapping windows 3015; HMM refits 60, converged 60 of 60.

| model | RMSE | QLIKE |
|---|---|---|
| level: HAR | 2.221 | 1.664 |
| level: HAR + VIX | 1.392 | 1.570 |
| level: HAR + VIX + HMM prob | 0.962 | 1.561 |
| level: HAR + VIX + noise | 1.412 | 1.572 |
| log: HAR | 0.768 | 1.647 |
| log: HAR + VIX | 0.724 | 1.536 |
| log: HAR + VIX + HMM prob | 0.724 | 1.537 |
| log: HAR + VIX + noise | 0.727 | 1.540 |

| h | forecast | reference | windows | dRMSE 95% | RMSE | DM p (SE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | level: HAR + VIX | level: HAR | 3015 | -1.528 to -0.027 | better | 0.265 | -0.127 to -0.062 | better | 0.000 |
| 1 | level: HAR + VIX + HMM prob | level: HAR + VIX | 3015 | -0.855 to +0.009 | no difference | 0.303 | -0.026 to +0.004 | no difference | 0.158 |
| 1 | level: HAR + VIX + noise | level: HAR + VIX | 3015 | -0.006 to +0.041 | no difference | 0.344 | -0.005 to +0.008 | no difference | 0.692 |
| 1 | log: HAR + VIX | log: HAR | 3015 | -0.066 to -0.021 | better | 0.000 | -0.158 to -0.062 | better | 0.000 |
| 1 | log: HAR + VIX + HMM prob | log: HAR + VIX | 3015 | -0.001 to +0.002 | no difference | 0.294 | +0.000 to +0.004 | worse | 0.063 |
| 1 | log: HAR + VIX + noise | log: HAR + VIX | 3015 | -0.001 to +0.008 | no difference | 0.200 | -0.003 to +0.012 | no difference | 0.286 |
| 1 | log: HAR + VIX | level: HAR + VIX | 3015 | -1.415 to +0.012 | no difference | 0.304 | -0.073 to +0.004 | no difference | 0.032 |
| 1 | log: HAR + VIX + HMM prob | level: HAR + VIX + HMM prob | 3015 | -0.560 to +0.007 | no difference | 0.308 | -0.053 to +0.009 | no difference | 0.093 |

## Target B, horizon 1

Target ES 5-minute realised vol (the IHV study's target). Scored days 2,385, 2013-07-03 to 2022-12-29; non-overlapping windows 2385; HMM refits 60, converged 60 of 60.

| model | RMSE | QLIKE |
|---|---|---|
| level: HAR | 5.508 | 0.280 |
| level: HAR + VIX | 4.681 | 0.244 |
| level: HAR + VIX + HMM prob | 4.726 | 0.242 |
| level: HAR + VIX + noise | 4.649 | 0.244 |
| log: HAR | 0.285 | 0.219 |
| log: HAR + VIX | 0.270 | 0.196 |
| log: HAR + VIX + HMM prob | 0.269 | 0.193 |
| log: HAR + VIX + noise | 0.271 | 0.196 |

| h | forecast | reference | windows | dRMSE 95% | RMSE | DM p (SE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | level: HAR + VIX | level: HAR | 2385 | -1.438 to -0.016 | better | 0.280 | -0.055 to -0.018 | better | 0.000 |
| 1 | level: HAR + VIX + HMM prob | level: HAR + VIX | 2385 | -0.005 to +0.077 | no difference | 0.294 | -0.009 to +0.004 | no difference | 0.311 |
| 1 | level: HAR + VIX + noise | level: HAR + VIX | 2385 | -0.056 to +0.000 | no difference | 0.296 | -0.001 to +0.000 | no difference | 0.766 |
| 1 | log: HAR + VIX | log: HAR | 2385 | -0.024 to -0.006 | better | 0.046 | -0.034 to -0.015 | better | 0.000 |
| 1 | log: HAR + VIX + HMM prob | log: HAR + VIX | 2385 | -0.002 to -0.000 | better | 0.028 | -0.004 to -0.001 | better | 0.001 |
| 1 | log: HAR + VIX + noise | log: HAR + VIX | 2385 | -0.000 to +0.000 | no difference | 0.273 | -0.000 to +0.000 | no difference | 0.493 |
| 1 | log: HAR + VIX | level: HAR + VIX | 2385 | -7.773 to -0.010 | better | 0.291 | -0.090 to -0.022 | better | 0.007 |
| 1 | log: HAR + VIX + HMM prob | level: HAR + VIX + HMM prob | 2385 | -7.851 to -0.009 | better | 0.291 | -0.091 to -0.021 | better | 0.008 |

## Target A, horizon 5

Target daily-return realised vol (MR's target). Scored days 3,008, 2011-01-12 to 2022-12-22; non-overlapping windows 601; HMM refits 60, converged 60 of 60.

| model | RMSE | QLIKE |
|---|---|---|
| level: HAR | 1.531 | 0.592 |
| level: HAR + VIX | 1.040 | 0.503 |
| level: HAR + VIX + HMM prob | 0.585 | 0.494 |
| level: HAR + VIX + noise | 1.039 | 0.502 |
| log: HAR | 0.555 | 0.622 |
| log: HAR + VIX | 0.500 | 0.487 |
| log: HAR + VIX + HMM prob | 0.502 | 0.483 |
| log: HAR + VIX + noise | 0.500 | 0.486 |

| h | forecast | reference | windows | dRMSE 95% | RMSE | DM p (SE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 5 | level: HAR + VIX | level: HAR | 601 | -0.913 to -0.025 | better | 0.251 | -0.124 to -0.060 | better | 0.000 |
| 5 | level: HAR + VIX + HMM prob | level: HAR + VIX | 601 | -0.906 to +0.007 | no difference | 0.296 | -0.027 to +0.007 | no difference | 0.261 |
| 5 | level: HAR + VIX + noise | level: HAR + VIX | 601 | -0.005 to +0.002 | no difference | 0.710 | -0.002 to +0.001 | no difference | 0.577 |
| 5 | log: HAR + VIX | log: HAR | 601 | -0.086 to -0.027 | better | 0.006 | -0.194 to -0.080 | better | 0.000 |
| 5 | log: HAR + VIX + HMM prob | log: HAR + VIX | 601 | -0.001 to +0.006 | no difference | 0.360 | -0.010 to +0.004 | no difference | 0.371 |
| 5 | log: HAR + VIX + noise | log: HAR + VIX | 601 | -0.000 to +0.001 | no difference | 0.379 | -0.002 to +0.001 | no difference | 0.897 |
| 5 | log: HAR + VIX | level: HAR + VIX | 601 | -1.109 to -0.000 | better | 0.293 | -0.045 to +0.015 | no difference | 0.254 |
| 5 | log: HAR + VIX + HMM prob | level: HAR + VIX + HMM prob | 601 | -0.204 to +0.002 | no difference | 0.285 | -0.033 to +0.013 | no difference | 0.344 |

## Target B, horizon 5

Target ES 5-minute realised vol (the IHV study's target). Scored days 2,377, 2013-07-10 to 2022-12-22; non-overlapping windows 475; HMM refits 60, converged 60 of 60.

| model | RMSE | QLIKE |
|---|---|---|
| level: HAR | 2.521 | 0.280 |
| level: HAR + VIX | 2.055 | 0.246 |
| level: HAR + VIX + HMM prob | 2.063 | 0.245 |
| level: HAR + VIX + noise | 2.047 | 0.246 |
| log: HAR | 0.294 | 0.232 |
| log: HAR + VIX | 0.278 | 0.208 |
| log: HAR + VIX + HMM prob | 0.278 | 0.206 |
| log: HAR + VIX + noise | 0.278 | 0.208 |

| h | forecast | reference | windows | dRMSE 95% | RMSE | DM p (SE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 5 | level: HAR + VIX | level: HAR | 475 | -0.809 to -0.013 | better | 0.277 | -0.057 to -0.014 | better | 0.000 |
| 5 | level: HAR + VIX + HMM prob | level: HAR + VIX | 475 | -0.005 to +0.014 | no difference | 0.282 | -0.007 to +0.006 | no difference | 0.862 |
| 5 | level: HAR + VIX + noise | level: HAR + VIX | 475 | -0.015 to +0.000 | no difference | 0.289 | -0.000 to +0.000 | no difference | 0.781 |
| 5 | log: HAR + VIX | log: HAR | 475 | -0.028 to -0.004 | better | 0.108 | -0.039 to -0.011 | better | 0.001 |
| 5 | log: HAR + VIX + HMM prob | log: HAR + VIX | 475 | -0.002 to +0.001 | no difference | 0.807 | -0.003 to -0.000 | better | 0.065 |
| 5 | log: HAR + VIX + noise | log: HAR + VIX | 475 | -0.000 to +0.000 | no difference | 0.474 | -0.000 to +0.000 | no difference | 0.340 |
| 5 | log: HAR + VIX | level: HAR + VIX | 475 | -3.195 to -0.008 | better | 0.281 | -0.069 to -0.016 | better | 0.006 |
| 5 | log: HAR + VIX + HMM prob | level: HAR + VIX + HMM prob | 475 | -3.208 to -0.009 | better | 0.281 | -0.070 to -0.016 | better | 0.006 |

## Target A, horizon 21

Target daily-return realised vol (MR's target). Scored days 2,976, 2011-02-04 to 2022-11-30; non-overlapping windows 141; HMM refits 60, converged 60 of 60.

| model | RMSE | QLIKE |
|---|---|---|
| level: HAR | 0.908 | 0.487 |
| level: HAR + VIX | 0.691 | 0.461 |
| level: HAR + VIX + HMM prob | 0.531 | 0.466 |
| level: HAR + VIX + noise | 0.690 | 0.462 |
| log: HAR | 0.528 | 0.486 |
| log: HAR + VIX | 0.499 | 0.464 |
| log: HAR + VIX + HMM prob | 0.501 | 0.472 |
| log: HAR + VIX + noise | 0.499 | 0.466 |

| h | forecast | reference | windows | dRMSE 95% | RMSE | DM p (SE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 21 | level: HAR + VIX | level: HAR | 141 | -0.423 to -0.011 | better | 0.207 | -0.057 to +0.009 | no difference | 0.166 |
| 21 | level: HAR + VIX + HMM prob | level: HAR + VIX | 141 | -0.352 to +0.010 | no difference | 0.290 | -0.018 to +0.035 | no difference | 0.710 |
| 21 | level: HAR + VIX + noise | level: HAR + VIX | 141 | -0.002 to +0.001 | no difference | 0.537 | -0.001 to +0.005 | no difference | 0.387 |
| 21 | log: HAR + VIX | log: HAR | 141 | -0.049 to -0.011 | better | 0.009 | -0.080 to +0.049 | no difference | 0.508 |
| 21 | log: HAR + VIX + HMM prob | log: HAR + VIX | 141 | -0.004 to +0.012 | no difference | 0.541 | -0.010 to +0.034 | no difference | 0.457 |
| 21 | log: HAR + VIX + noise | log: HAR + VIX | 141 | -0.000 to +0.001 | no difference | 0.225 | -0.001 to +0.005 | no difference | 0.384 |
| 21 | log: HAR + VIX | level: HAR + VIX | 141 | -0.422 to +0.006 | no difference | 0.284 | -0.030 to +0.044 | no difference | 0.844 |
| 21 | log: HAR + VIX + HMM prob | level: HAR + VIX + HMM prob | 141 | -0.074 to +0.006 | no difference | 0.301 | -0.019 to +0.039 | no difference | 0.632 |

## Target B, horizon 21

Target ES 5-minute realised vol (the IHV study's target). Scored days 2,345, 2013-08-01 to 2022-11-30; non-overlapping windows 111; HMM refits 60, converged 60 of 60.

| model | RMSE | QLIKE |
|---|---|---|
| level: HAR | 0.896 | 0.430 |
| level: HAR + VIX | 0.753 | 0.408 |
| level: HAR + VIX + HMM prob | 0.747 | 0.413 |
| level: HAR + VIX + noise | 0.750 | 0.409 |
| log: HAR | 0.355 | 0.407 |
| log: HAR + VIX | 0.349 | 0.390 |
| log: HAR + VIX + HMM prob | 0.349 | 0.391 |
| log: HAR + VIX + noise | 0.349 | 0.391 |

| h | forecast | reference | windows | dRMSE 95% | RMSE | DM p (SE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 21 | level: HAR + VIX | level: HAR | 111 | -0.259 to -0.004 | better | 0.260 | -0.046 to -0.001 | better | 0.040 |
| 21 | level: HAR + VIX + HMM prob | level: HAR + VIX | 111 | -0.011 to +0.005 | no difference | 0.312 | -0.004 to +0.015 | no difference | 0.252 |
| 21 | level: HAR + VIX + noise | level: HAR + VIX | 111 | -0.005 to +0.000 | no difference | 0.283 | -0.000 to +0.003 | no difference | 0.304 |
| 21 | log: HAR + VIX | log: HAR | 111 | -0.011 to -0.000 | better | 0.101 | -0.043 to +0.006 | no difference | 0.157 |
| 21 | log: HAR + VIX + HMM prob | log: HAR + VIX | 111 | -0.001 to +0.002 | no difference | 0.984 | -0.004 to +0.005 | no difference | 0.748 |
| 21 | log: HAR + VIX + noise | log: HAR + VIX | 111 | -0.000 to +0.000 | no difference | 0.260 | -0.000 to +0.003 | no difference | 0.298 |
| 21 | log: HAR + VIX | level: HAR + VIX | 111 | -0.795 to +0.001 | no difference | 0.259 | -0.049 to +0.010 | no difference | 0.243 |
| 21 | log: HAR + VIX + HMM prob | level: HAR + VIX + HMM prob | 111 | -0.784 to -0.000 | better | 0.258 | -0.053 to +0.006 | no difference | 0.145 |

## Target A, horizon 63

Target daily-return realised vol (MR's target). Scored days 2,892, 2011-04-06 to 2022-09-30; non-overlapping windows 45; HMM refits 60, converged 60 of 60.

| model | RMSE | QLIKE |
|---|---|---|
| level: HAR | 0.691 | 0.564 |
| level: HAR + VIX | 0.605 | 0.555 |
| level: HAR + VIX + HMM prob | 0.555 | 0.569 |
| level: HAR + VIX + noise | 0.606 | 0.556 |
| log: HAR | 0.549 | 0.603 |
| log: HAR + VIX | 0.539 | 0.586 |
| log: HAR + VIX + HMM prob | 0.544 | 0.593 |
| log: HAR + VIX + noise | 0.540 | 0.588 |

| h | forecast | reference | windows | dRMSE 95% | RMSE | DM p (SE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 63 | level: HAR + VIX | level: HAR | 45 | -0.199 to -0.001 | better | 0.258 | -0.028 to +0.012 | no difference | 0.376 |
| 63 | level: HAR + VIX + HMM prob | level: HAR + VIX | 45 | -0.147 to +0.021 | no difference | 0.362 | -0.016 to +0.052 | no difference | 0.411 |
| 63 | level: HAR + VIX + noise | level: HAR + VIX | 45 | -0.000 to +0.001 | no difference | 0.563 | -0.000 to +0.004 | no difference | 0.228 |
| 63 | log: HAR + VIX | log: HAR | 45 | -0.025 to +0.000 | no difference | 0.052 | -0.045 to +0.013 | no difference | 0.275 |
| 63 | log: HAR + VIX + HMM prob | log: HAR + VIX | 45 | -0.005 to +0.022 | no difference | 0.372 | -0.016 to +0.040 | no difference | 0.600 |
| 63 | log: HAR + VIX + noise | log: HAR + VIX | 45 | +0.000 to +0.001 | worse | 0.054 | +0.000 to +0.005 | worse | 0.194 |
| 63 | log: HAR + VIX | level: HAR + VIX | 45 | -0.185 to +0.016 | no difference | 0.330 | -0.025 to +0.106 | no difference | 0.368 |
| 63 | log: HAR + VIX + HMM prob | level: HAR + VIX + HMM prob | 45 | -0.040 to +0.012 | no difference | 0.484 | -0.012 to +0.075 | no difference | 0.281 |

## Target B, horizon 63

Target ES 5-minute realised vol (the IHV study's target). Scored days 2,261, 2013-10-01 to 2022-09-30; non-overlapping windows 35; HMM refits 60, converged 60 of 60.

| model | RMSE | QLIKE |
|---|---|---|
| level: HAR | 0.440 | 0.578 |
| level: HAR + VIX | 0.417 | 0.559 |
| level: HAR + VIX + HMM prob | 0.444 | 0.573 |
| level: HAR + VIX + noise | 0.417 | 0.560 |
| log: HAR | 0.382 | 0.596 |
| log: HAR + VIX | 0.378 | 0.569 |
| log: HAR + VIX + HMM prob | 0.378 | 0.578 |
| log: HAR + VIX + noise | 0.378 | 0.570 |

| h | forecast | reference | windows | dRMSE 95% | RMSE | DM p (SE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 63 | level: HAR + VIX | level: HAR | 35 | -0.053 to -0.001 | better | 0.219 | -0.041 to -0.000 | better | 0.071 |
| 63 | level: HAR + VIX + HMM prob | level: HAR + VIX | 35 | -0.001 to +0.065 | no difference | 0.275 | -0.001 to +0.034 | no difference | 0.105 |
| 63 | level: HAR + VIX + noise | level: HAR + VIX | 35 | -0.000 to +0.000 | no difference | 0.533 | -0.000 to +0.003 | no difference | 0.254 |
| 63 | log: HAR + VIX | log: HAR | 35 | -0.009 to +0.001 | no difference | 0.136 | -0.075 to +0.005 | no difference | 0.188 |
| 63 | log: HAR + VIX + HMM prob | log: HAR + VIX | 35 | -0.001 to +0.004 | no difference | 0.348 | -0.003 to +0.025 | no difference | 0.231 |
| 63 | log: HAR + VIX + noise | log: HAR + VIX | 35 | -0.000 to +0.000 | no difference | 0.314 | -0.000 to +0.002 | no difference | 0.258 |
| 63 | log: HAR + VIX | level: HAR + VIX | 35 | -0.106 to +0.003 | no difference | 0.279 | -0.018 to +0.046 | no difference | 0.531 |
| 63 | log: HAR + VIX + HMM prob | level: HAR + VIX + HMM prob | 35 | -0.169 to +0.002 | no difference | 0.282 | -0.026 to +0.041 | no difference | 0.791 |

## Summary: does any comparison change with the form?

Class: development data only (S&P 500, to 2022-12-30), no holdout, not a claim. Each within-form comparison at each target and horizon, the 95% interval verdict under the level form beside the log form. *moves* = the RMSE or QLIKE verdict differs.

| target | h | comparison | RMSE level | RMSE log | QLIKE level | QLIKE log | moves |
|---|---|---|---|---|---|---|---|
| A | 1 | HAR + VIX vs HAR | better | better | better | better | no |
| A | 1 | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | no difference | worse | yes |
| A | 1 | HAR + VIX + noise vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| B | 1 | HAR + VIX vs HAR | better | better | better | better | no |
| B | 1 | HAR + VIX + HMM prob vs HAR + VIX | no difference | better | no difference | better | yes |
| B | 1 | HAR + VIX + noise vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| A | 5 | HAR + VIX vs HAR | better | better | better | better | no |
| A | 5 | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| A | 5 | HAR + VIX + noise vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| B | 5 | HAR + VIX vs HAR | better | better | better | better | no |
| B | 5 | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | no difference | better | yes |
| B | 5 | HAR + VIX + noise vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| A | 21 | HAR + VIX vs HAR | better | better | no difference | no difference | no |
| A | 21 | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| A | 21 | HAR + VIX + noise vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| B | 21 | HAR + VIX vs HAR | better | better | better | no difference | yes |
| B | 21 | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| B | 21 | HAR + VIX + noise vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| A | 63 | HAR + VIX vs HAR | better | no difference | no difference | no difference | yes |
| A | 63 | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| A | 63 | HAR + VIX + noise vs HAR + VIX | no difference | worse | no difference | worse | yes |
| B | 63 | HAR + VIX vs HAR | better | no difference | better | no difference | yes |
| B | 63 | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | no difference | no difference | no |
| B | 63 | HAR + VIX + noise vs HAR + VIX | no difference | no difference | no difference | no difference | no |

Verdicts that move between forms: 7 of 24 comparisons (each counted once if either loss moves).

### Answer

Class: development data only (S&P 500, to 2022-12-30), no holdout, not a claim. Read from the tables above.

- Form MR used: the log form, in every script that builds a HAR + implied vol benchmark (table below). The level form is the alternative, not the paper's.
- Within-form verdicts that differ between the forms: 7 of 24; at MR's target and horizon (A, h = 21): 0.
- Those involving the HMM probability: 3: target A h=1 HAR + VIX + HMM prob vs HAR + VIX (RMSE no difference -> no difference, QLIKE no difference -> worse); target B h=1 HAR + VIX + HMM prob vs HAR + VIX (RMSE no difference -> better, QLIKE no difference -> better); target B h=5 HAR + VIX + HMM prob vs HAR + VIX (RMSE no difference -> no difference, QLIKE no difference -> better).
- The HAR + VIX benchmark, log minus level: log has the lower loss (interval below zero on RMSE or QLIKE) in 3 of 8 target-horizon cells, the level form in 0.
- No multiplicity correction is applied to any interval in this file; a 'better' that appears in one form only is a development lead, not a result.

## The benchmark itself: log form minus level form

Class: development data only (S&P 500, to 2022-12-30), no holdout, not a claim. Negative = the log form has the lower loss.

| target | h | model | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|
| A | 1 | HAR + VIX | -1.415 to +0.012 | no difference | -0.073 to +0.004 | no difference |
| A | 1 | HAR + VIX + HMM prob | -0.560 to +0.007 | no difference | -0.053 to +0.009 | no difference |
| B | 1 | HAR + VIX | -7.773 to -0.010 | better | -0.090 to -0.022 | better |
| B | 1 | HAR + VIX + HMM prob | -7.851 to -0.009 | better | -0.091 to -0.021 | better |
| A | 5 | HAR + VIX | -1.109 to -0.000 | better | -0.045 to +0.015 | no difference |
| A | 5 | HAR + VIX + HMM prob | -0.204 to +0.002 | no difference | -0.033 to +0.013 | no difference |
| B | 5 | HAR + VIX | -3.195 to -0.008 | better | -0.069 to -0.016 | better |
| B | 5 | HAR + VIX + HMM prob | -3.208 to -0.009 | better | -0.070 to -0.016 | better |
| A | 21 | HAR + VIX | -0.422 to +0.006 | no difference | -0.030 to +0.044 | no difference |
| A | 21 | HAR + VIX + HMM prob | -0.074 to +0.006 | no difference | -0.019 to +0.039 | no difference |
| B | 21 | HAR + VIX | -0.795 to +0.001 | no difference | -0.049 to +0.010 | no difference |
| B | 21 | HAR + VIX + HMM prob | -0.784 to -0.000 | better | -0.053 to +0.006 | no difference |
| A | 63 | HAR + VIX | -0.185 to +0.016 | no difference | -0.025 to +0.106 | no difference |
| A | 63 | HAR + VIX + HMM prob | -0.040 to +0.012 | no difference | -0.012 to +0.075 | no difference |
| B | 63 | HAR + VIX | -0.106 to +0.003 | no difference | -0.018 to +0.046 | no difference |
| B | 63 | HAR + VIX + HMM prob | -0.169 to +0.002 | no difference | -0.026 to +0.041 | no difference |

## Claim sentences that rest on HAR + implied vol

Class: development data only (S&P 500, to 2022-12-30), no holdout, not a claim. For each claim sentence, the form its benchmark used (read from the frozen and development scripts named: every one takes np.log of the HAR inputs and of IV / sqrt(252) and regresses the log target, so every one is the log form), and the nearest development comparison above. *points the same way* compares the log-form RMSE verdict with the direction the sentence states (RMSE is the paper's primary loss); the level form is shown for contrast. The S&P development data cannot speak to the cross-index and ETF sentences, and S9 refits no HMM implied vol, so those rows say not checked.

| claim (where) | what it says | benchmark built in | form used | dev check here | log form RMSE / QLIKE | level form RMSE / QLIKE | log form points the same way |
|---|---|---|---|---|---|---|---|
| README.md:10-13, WRITEUP.md:551-553 | a regime probability added to HAR + implied vol makes no measurable difference | vol_forecast_vix.py:104-132; better_vol_models.py:93-117; msgarch_credit.py:168-186 | log | target A, h=21, HAR + VIX + HMM prob vs HAR + VIX | no difference / no difference | no difference / no difference | yes |
| README.md:48 | adding the VIX cuts forecast error (against HAR-RV) | vol_forecast_vix.py:104-132 | log | target A, h=21, HAR + VIX vs HAR | better / no difference | better / no difference | yes |
| README.md:17-19 | unregistered S&P rows: HMM implied vol vs HAR + VIX | vol_forecast_vix.py:104-132 | log | none (S9 refits no such model) | - | - | not checked |
| WRITEUP.md:610-614 | term-structure signals and the HMM probability added to HAR + VIX: no difference | term_structure_regimes.py:105-117 | log | target A, h=21, HAR + VIX + HMM prob vs HAR + VIX | no difference / no difference | no difference / no difference | yes |
| WRITEUP.md:655-672 | intraday HAR + VIX: the intraday HMM probability adds nothing | intraday_rv.py:117-144 | log | target B, h=21, HAR + VIX + HMM prob vs HAR + VIX | no difference / no difference | no difference / no difference | yes |
| README.md:50 | cross-index: no model beats HAR-RV + implied vol | better_vol_models.py:93-117 | log | none (S9 refits no such model) | - | - | not checked |
| README.md:16-17, 51 | ETFs: MS-GARCH loses to HAR + implied vol | msgarch_credit.py:168-186 | log | none (S9 refits no such model) | - | - | not checked |

