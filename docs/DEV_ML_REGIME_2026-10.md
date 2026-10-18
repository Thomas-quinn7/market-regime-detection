development data only (S&P 500, 2005-2023), no holdout, not a claim

# Machine learning and the regime probability, development data, October 2026

Class of every table in this file: **development data only (S&P 500, 2005-2023), no holdout, not a claim**. Written by `examples/dev_ml_regime.py` at 0d9b0e7 plus uncommitted files, 2026-10-18 13:05Z, 2,000 bootstrap draws (seed 0). Design, learners, grids and the reading rule: `docs/ML_REGIME_PROTOCOL_DRAFT.md`, committed before the first fit. Forecasts and the per-refit chosen hyperparameters: `docs/results/dev_ml_regime/`. Stage S8 (b) of the reopen.

Intervals: paired circular block bootstrap, block max(63, h); DM = HAC Diebold-Mariano, lag 20, two-sided p. *windows* = scored days / h. Nothing here is a claim.

## Horizon 5

F1 rows: scored days 3,258, 2011-01-12 to 2023-12-21, windows 651; HMM refits 64, converged 64.

| forecast | RMSE | QLIKE |
|---|---|---|
| ols F0 | 0.4850 | 0.4663 |
| ols F1 | 0.4871 | 0.4639 |
| ols F1n | 0.4855 | 0.4663 |
| ridge F0 | 0.4869 | 0.4683 |
| ridge F1 | 0.4897 | 0.4668 |
| ridge F1n | 0.4875 | 0.4680 |
| lasso F0 | 0.4874 | 0.4650 |
| lasso F1 | 0.4895 | 0.4641 |
| lasso F1n | 0.4880 | 0.4643 |
| random forest F0 | 0.5358 | 0.4911 |
| random forest F1 | 0.5346 | 0.4929 |
| random forest F1n | 0.5358 | 0.4902 |
| lightgbm F0 | 0.5011 | 0.4778 |
| lightgbm F1 | 0.5025 | 0.4849 |
| lightgbm F1n | 0.5035 | 0.4781 |
| mlp F0 | 0.4910 | 0.4739 |
| mlp F1 | 0.4968 | 0.4810 |
| mlp F1n | 0.5048 | 0.4815 |

Model confidence set at 10% on QLIKE over the 18 learner-feature pairs (post hoc, descriptive): ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, lightgbm F1n, mlp F0, mlp F1, mlp F1n.

## Horizon 21

F1 rows: scored days 3,226, 2011-02-04 to 2023-11-29, windows 153; HMM refits 64, converged 64.

| forecast | RMSE | QLIKE |
|---|---|---|
| ols F0 | 0.4814 | 0.4333 |
| ols F1 | 0.4838 | 0.4409 |
| ols F1n | 0.4818 | 0.4346 |
| ridge F0 | 0.4888 | 0.4389 |
| ridge F1 | 0.4914 | 0.4460 |
| ridge F1n | 0.4893 | 0.4403 |
| lasso F0 | 0.4909 | 0.4343 |
| lasso F1 | 0.4909 | 0.4433 |
| lasso F1n | 0.4896 | 0.4311 |
| random forest F0 | 0.5089 | 0.4860 |
| random forest F1 | 0.5133 | 0.5179 |
| random forest F1n | 0.5087 | 0.4852 |
| lightgbm F0 | 0.4982 | 0.4744 |
| lightgbm F1 | 0.4984 | 0.5174 |
| lightgbm F1n | 0.4984 | 0.4766 |
| mlp F0 | 0.5122 | 0.4759 |
| mlp F1 | 0.5149 | 0.4880 |
| mlp F1n | 0.5132 | 0.4695 |

Model confidence set at 10% on QLIKE over the 18 learner-feature pairs (post hoc, descriptive): ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, lightgbm F1n, mlp F0, mlp F1, mlp F1n.

## Horizon 63

F1 rows: scored days 3,142, 2011-04-06 to 2023-09-29, windows 49; HMM refits 64, converged 64.

| forecast | RMSE | QLIKE |
|---|---|---|
| ols F0 | 0.5203 | 0.5454 |
| ols F1 | 0.5259 | 0.5525 |
| ols F1n | 0.5208 | 0.5471 |
| ridge F0 | 0.5370 | 0.5709 |
| ridge F1 | 0.5430 | 0.5773 |
| ridge F1n | 0.5374 | 0.5727 |
| lasso F0 | 0.5309 | 0.5386 |
| lasso F1 | 0.5357 | 0.5458 |
| lasso F1n | 0.5309 | 0.5386 |
| random forest F0 | 0.5569 | 0.5967 |
| random forest F1 | 0.5565 | 0.6244 |
| random forest F1n | 0.5567 | 0.5966 |
| lightgbm F0 | 0.5712 | 0.5972 |
| lightgbm F1 | 0.5519 | 0.5958 |
| lightgbm F1n | 0.5680 | 0.5935 |
| mlp F0 | 0.5668 | 0.7111 |
| mlp F1 | 0.5580 | 0.6259 |
| mlp F1n | 0.5565 | 0.5880 |

Model confidence set at 10% on QLIKE over the 18 learner-feature pairs (post hoc, descriptive): ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, lightgbm F1n, mlp F0, mlp F1, mlp F1n.

## Horizon 126

F1 rows: scored days 3,016, 2011-07-07 to 2023-06-30, windows 23; HMM refits 64, converged 64.

| forecast | RMSE | QLIKE |
|---|---|---|
| ols F0 | 0.5499 | 0.5303 |
| ols F1 | 0.5461 | 0.5205 |
| ols F1n | 0.5506 | 0.5304 |
| ridge F0 | 0.5439 | 0.5348 |
| ridge F1 | 0.5452 | 0.5280 |
| ridge F1n | 0.5445 | 0.5348 |
| lasso F0 | 0.5370 | 0.5103 |
| lasso F1 | 0.5393 | 0.5074 |
| lasso F1n | 0.5373 | 0.5104 |
| random forest F0 | 0.5733 | 0.5907 |
| random forest F1 | 0.5635 | 0.5360 |
| random forest F1n | 0.5731 | 0.5907 |
| lightgbm F0 | 0.5892 | 0.6007 |
| lightgbm F1 | 0.5540 | 0.5364 |
| lightgbm F1n | 0.5858 | 0.5914 |

Model confidence set at 10% on QLIKE over the 15 learner-feature pairs (post hoc, descriptive): ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F1, lightgbm F1.

## Decisive table (i): does the regime probability help a flexible learner?

Class: development data only (S&P 500, 2005-2023), no holdout, not a claim. Every learner F1 vs F0, with the noise control F1n vs F0 beside it.

| h | learner | comparison | windows | dRMSE 95% | RMSE | DM p (MSE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 5 | ols | F1 vs F0 | 651 | -0.001 to +0.006 | no difference | 0.297 | -0.009 to +0.004 | no difference | 0.482 |
| 5 | ols | F1n vs F0 (noise control) | 651 | -0.000 to +0.001 | no difference | 0.366 | -0.002 to +0.001 | no difference | 0.993 |
| 5 | ridge | F1 vs F0 | 651 | -0.001 to +0.007 | no difference | 0.201 | -0.008 to +0.005 | no difference | 0.651 |
| 5 | ridge | F1n vs F0 (noise control) | 651 | -0.000 to +0.002 | no difference | 0.322 | -0.002 to +0.001 | no difference | 0.737 |
| 5 | lasso | F1 vs F0 | 651 | -0.001 to +0.005 | no difference | 0.287 | -0.007 to +0.005 | no difference | 0.792 |
| 5 | lasso | F1n vs F0 (noise control) | 651 | -0.000 to +0.002 | no difference | 0.380 | -0.003 to +0.002 | no difference | 0.625 |
| 5 | random forest | F1 vs F0 | 651 | -0.004 to +0.001 | no difference | 0.291 | -0.008 to +0.014 | no difference | 0.718 |
| 5 | random forest | F1n vs F0 (noise control) | 651 | -0.001 to +0.001 | no difference | 0.848 | -0.003 to +0.001 | no difference | 0.469 |
| 5 | lightgbm | F1 vs F0 | 651 | -0.003 to +0.007 | no difference | 0.684 | -0.005 to +0.022 | no difference | 0.257 |
| 5 | lightgbm | F1n vs F0 (noise control) | 651 | -0.000 to +0.006 | no difference | 0.098 | -0.005 to +0.006 | no difference | 0.902 |
| 5 | mlp | F1 vs F0 | 651 | -0.010 to +0.024 | no difference | 0.510 | -0.013 to +0.026 | no difference | 0.429 |
| 5 | mlp | F1n vs F0 (noise control) | 651 | -0.003 to +0.033 | no difference | 0.208 | -0.012 to +0.027 | no difference | 0.448 |
| 21 | ols | F1 vs F0 | 153 | -0.004 to +0.012 | no difference | 0.469 | -0.009 to +0.032 | no difference | 0.449 |
| 21 | ols | F1n vs F0 (noise control) | 153 | -0.000 to +0.001 | no difference | 0.240 | -0.001 to +0.005 | no difference | 0.389 |
| 21 | ridge | F1 vs F0 | 153 | -0.004 to +0.012 | no difference | 0.441 | -0.009 to +0.031 | no difference | 0.471 |
| 21 | ridge | F1n vs F0 (noise control) | 153 | -0.000 to +0.001 | no difference | 0.154 | -0.001 to +0.005 | no difference | 0.369 |
| 21 | lasso | F1 vs F0 | 153 | -0.006 to +0.009 | no difference | 0.996 | -0.007 to +0.031 | no difference | 0.365 |
| 21 | lasso | F1n vs F0 (noise control) | 153 | -0.004 to +0.000 | no difference | 0.090 | -0.010 to +0.001 | no difference | 0.287 |
| 21 | random forest | F1 vs F0 | 153 | -0.005 to +0.018 | no difference | 0.538 | -0.012 to +0.095 | no difference | 0.203 |
| 21 | random forest | F1n vs F0 (noise control) | 153 | -0.000 to +0.000 | no difference | 0.132 | -0.002 to -0.000 | better | 0.021 |
| 21 | lightgbm | F1 vs F0 | 153 | -0.008 to +0.010 | no difference | 0.957 | +0.001 to +0.101 | worse | 0.068 |
| 21 | lightgbm | F1n vs F0 (noise control) | 153 | -0.002 to +0.002 | no difference | 0.825 | -0.004 to +0.011 | no difference | 0.526 |
| 21 | mlp | F1 vs F0 | 153 | -0.018 to +0.020 | no difference | 0.749 | -0.030 to +0.073 | no difference | 0.624 |
| 21 | mlp | F1n vs F0 (noise control) | 153 | -0.017 to +0.019 | no difference | 0.889 | -0.030 to +0.021 | no difference | 0.576 |
| 63 | ols | F1 vs F0 | 49 | -0.005 to +0.021 | no difference | 0.210 | -0.016 to +0.038 | no difference | 0.476 |
| 63 | ols | F1n vs F0 (noise control) | 49 | +0.000 to +0.001 | worse | 0.021 | -0.000 to +0.005 | no difference | 0.105 |
| 63 | ridge | F1 vs F0 | 49 | -0.003 to +0.019 | no difference | 0.117 | -0.013 to +0.032 | no difference | 0.453 |
| 63 | ridge | F1n vs F0 (noise control) | 49 | +0.000 to +0.001 | worse | 0.026 | -0.000 to +0.005 | no difference | 0.107 |
| 63 | lasso | F1 vs F0 | 49 | -0.003 to +0.017 | no difference | 0.151 | -0.012 to +0.034 | no difference | 0.386 |
| 63 | lasso | F1n vs F0 (noise control) | 49 | -0.000 to +0.000 | no difference | 0.535 | -0.000 to +0.000 | no difference | 0.973 |
| 63 | random forest | F1 vs F0 | 49 | -0.015 to +0.011 | no difference | 0.941 | -0.002 to +0.066 | no difference | 0.040 |
| 63 | random forest | F1n vs F0 (noise control) | 49 | -0.001 to +0.000 | no difference | 0.372 | -0.001 to +0.000 | no difference | 0.784 |
| 63 | lightgbm | F1 vs F0 | 49 | -0.046 to +0.001 | no difference | 0.071 | -0.049 to +0.049 | no difference | 0.944 |
| 63 | lightgbm | F1n vs F0 (noise control) | 49 | -0.009 to +0.001 | no difference | 0.163 | -0.009 to +0.000 | no difference | 0.090 |
| 63 | mlp | F1 vs F0 | 49 | -0.047 to +0.019 | no difference | 0.461 | -0.299 to +0.055 | no difference | 0.238 |
| 63 | mlp | F1n vs F0 (noise control) | 49 | -0.046 to +0.015 | no difference | 0.341 | -0.328 to +0.002 | no difference | 0.071 |
| 126 | ols | F1 vs F0 | 23 | -0.021 to +0.015 | no difference | 0.511 | -0.033 to +0.013 | no difference | 0.249 |
| 126 | ols | F1n vs F0 (noise control) | 23 | +0.000 to +0.002 | worse | 0.012 | -0.001 to +0.001 | no difference | 0.942 |
| 126 | ridge | F1 vs F0 | 23 | -0.010 to +0.016 | no difference | 0.804 | -0.031 to +0.017 | no difference | 0.470 |
| 126 | ridge | F1n vs F0 (noise control) | 23 | +0.000 to +0.002 | worse | 0.018 | -0.001 to +0.001 | no difference | 0.952 |
| 126 | lasso | F1 vs F0 | 23 | -0.009 to +0.016 | no difference | 0.593 | -0.024 to +0.017 | no difference | 0.685 |
| 126 | lasso | F1n vs F0 (noise control) | 23 | +0.000 to +0.001 | worse | 0.072 | -0.000 to +0.000 | no difference | 0.340 |
| 126 | random forest | F1 vs F0 | 23 | -0.034 to +0.014 | no difference | 0.389 | -0.170 to +0.016 | no difference | 0.055 |
| 126 | random forest | F1n vs F0 (noise control) | 23 | -0.001 to +0.000 | no difference | 0.192 | -0.001 to +0.001 | no difference | 0.989 |
| 126 | lightgbm | F1 vs F0 | 23 | -0.062 to -0.010 | better | 0.003 | -0.191 to +0.020 | no difference | 0.049 |
| 126 | lightgbm | F1n vs F0 (noise control) | 23 | -0.008 to +0.000 | no difference | 0.072 | -0.020 to -0.001 | better | 0.002 |

## Decisive table (ii): does the learner itself beat HAR + VIX?

Class: development data only (S&P 500, 2005-2023), no holdout, not a claim. Every learner on F0 vs OLS on F0.

| h | learner | comparison | windows | dRMSE 95% | RMSE | DM p (MSE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 5 | ridge | F0 vs OLS F0 (HAR + VIX) | 651 | -0.001 to +0.005 | no difference | 0.252 | -0.005 to +0.009 | no difference | 0.504 |
| 5 | lasso | F0 vs OLS F0 (HAR + VIX) | 651 | -0.001 to +0.005 | no difference | 0.176 | -0.010 to +0.007 | no difference | 0.741 |
| 5 | random forest | F0 vs OLS F0 (HAR + VIX) | 651 | +0.008 to +0.102 | worse | 0.140 | -0.005 to +0.057 | no difference | 0.096 |
| 5 | lightgbm | F0 vs OLS F0 (HAR + VIX) | 651 | +0.001 to +0.032 | worse | 0.131 | -0.011 to +0.033 | no difference | 0.274 |
| 5 | mlp | F0 vs OLS F0 (HAR + VIX) | 651 | -0.002 to +0.015 | no difference | 0.199 | -0.008 to +0.023 | no difference | 0.359 |
| 21 | ridge | F0 vs OLS F0 (HAR + VIX) | 153 | +0.001 to +0.019 | worse | 0.017 | -0.003 to +0.014 | no difference | 0.137 |
| 21 | lasso | F0 vs OLS F0 (HAR + VIX) | 153 | +0.001 to +0.022 | worse | 0.015 | -0.014 to +0.016 | no difference | 0.883 |
| 21 | random forest | F0 vs OLS F0 (HAR + VIX) | 153 | +0.007 to +0.052 | worse | 0.011 | +0.000 to +0.121 | worse | 0.069 |
| 21 | lightgbm | F0 vs OLS F0 (HAR + VIX) | 153 | -0.003 to +0.044 | no difference | 0.151 | +0.001 to +0.096 | worse | 0.070 |
| 21 | mlp | F0 vs OLS F0 (HAR + VIX) | 153 | +0.013 to +0.054 | worse | 0.003 | +0.016 to +0.074 | worse | 0.003 |
| 63 | ridge | F0 vs OLS F0 (HAR + VIX) | 49 | +0.002 to +0.042 | worse | 0.003 | +0.005 to +0.051 | worse | 0.001 |
| 63 | lasso | F0 vs OLS F0 (HAR + VIX) | 49 | -0.002 to +0.027 | no difference | 0.118 | -0.076 to +0.040 | no difference | 0.800 |
| 63 | random forest | F0 vs OLS F0 (HAR + VIX) | 49 | +0.012 to +0.072 | worse | 0.000 | -0.017 to +0.119 | no difference | 0.088 |
| 63 | lightgbm | F0 vs OLS F0 (HAR + VIX) | 49 | +0.020 to +0.099 | worse | 0.000 | -0.021 to +0.121 | no difference | 0.089 |
| 63 | mlp | F0 vs OLS F0 (HAR + VIX) | 49 | +0.019 to +0.086 | worse | 0.000 | +0.027 to +0.370 | worse | 0.021 |
| 126 | ridge | F0 vs OLS F0 (HAR + VIX) | 23 | -0.032 to +0.019 | no difference | 0.274 | -0.024 to +0.033 | no difference | 0.547 |
| 126 | lasso | F0 vs OLS F0 (HAR + VIX) | 23 | -0.031 to +0.007 | no difference | 0.051 | -0.083 to +0.028 | no difference | 0.294 |
| 126 | random forest | F0 vs OLS F0 (HAR + VIX) | 23 | -0.003 to +0.056 | no difference | 0.013 | +0.016 to +0.109 | worse | 0.000 |
| 126 | lightgbm | F0 vs OLS F0 (HAR + VIX) | 23 | +0.007 to +0.084 | worse | 0.001 | +0.021 to +0.129 | worse | 0.000 |

## Decisive table (iii): more information instead of a regime

Class: development data only (S&P 500, 2005-2023), no holdout, not a claim. F2 vs F0 per learner, on the F2 rows (VIX9D starts 2011-01-03).

| h | learner | comparison | windows | dRMSE 95% | RMSE | DM p (MSE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|
| 5 | ols | F2 vs F0 (F2 rows) | 500 | -0.049 to +0.003 | no difference | 0.158 | -0.043 to +0.020 | no difference | 0.409 |
| 5 | ridge | F2 vs F0 (F2 rows) | 500 | -0.058 to -0.002 | better | 0.064 | -0.045 to +0.016 | no difference | 0.380 |
| 5 | lasso | F2 vs F0 (F2 rows) | 500 | -0.057 to -0.003 | better | 0.017 | -0.047 to +0.009 | no difference | 0.207 |
| 5 | random forest | F2 vs F0 (F2 rows) | 500 | -0.065 to -0.002 | better | 0.051 | -0.090 to +0.022 | no difference | 0.343 |
| 5 | lightgbm | F2 vs F0 (F2 rows) | 500 | -0.040 to +0.004 | no difference | 0.088 | -0.032 to +0.053 | no difference | 0.648 |
| 5 | mlp | F2 vs F0 (F2 rows) | 500 | +0.004 to +0.047 | worse | 0.009 | +0.060 to +0.178 | worse | 0.000 |
| 21 | ols | F2 vs F0 (F2 rows) | 117 | -0.011 to +0.015 | no difference | 0.888 | -0.023 to +0.026 | no difference | 0.799 |
| 21 | ridge | F2 vs F0 (F2 rows) | 117 | -0.014 to +0.011 | no difference | 0.513 | -0.024 to +0.020 | no difference | 0.948 |
| 21 | lasso | F2 vs F0 (F2 rows) | 117 | -0.012 to +0.010 | no difference | 0.846 | -0.011 to +0.024 | no difference | 0.420 |
| 21 | random forest | F2 vs F0 (F2 rows) | 117 | -0.018 to +0.013 | no difference | 0.833 | -0.025 to +0.026 | no difference | 0.923 |
| 21 | lightgbm | F2 vs F0 (F2 rows) | 117 | -0.015 to +0.031 | no difference | 0.557 | -0.038 to +0.075 | no difference | 0.516 |
| 21 | mlp | F2 vs F0 (F2 rows) | 117 | -0.002 to +0.048 | no difference | 0.069 | -0.031 to +0.127 | no difference | 0.180 |
| 63 | ols | F2 vs F0 (F2 rows) | 37 | +0.002 to +0.040 | worse | 0.005 | -0.002 to +0.076 | no difference | 0.050 |
| 63 | ridge | F2 vs F0 (F2 rows) | 37 | +0.004 to +0.050 | worse | 0.007 | +0.008 to +0.076 | worse | 0.051 |
| 63 | lasso | F2 vs F0 (F2 rows) | 37 | +0.004 to +0.050 | worse | 0.006 | +0.009 to +0.066 | worse | 0.002 |
| 63 | random forest | F2 vs F0 (F2 rows) | 37 | +0.002 to +0.022 | worse | 0.001 | +0.013 to +0.101 | worse | 0.011 |
| 63 | lightgbm | F2 vs F0 (F2 rows) | 37 | +0.000 to +0.021 | worse | 0.055 | +0.002 to +0.129 | worse | 0.132 |
| 63 | mlp | F2 vs F0 (F2 rows) | 37 | +0.014 to +0.061 | worse | 0.000 | +0.051 to +0.310 | worse | 0.038 |
| 126 | ols | F2 vs F0 (F2 rows) | 17 | +0.007 to +0.055 | worse | 0.001 | +0.008 to +0.100 | worse | 0.126 |
| 126 | ridge | F2 vs F0 (F2 rows) | 17 | +0.006 to +0.051 | worse | 0.001 | +0.016 to +0.079 | worse | 0.102 |
| 126 | lasso | F2 vs F0 (F2 rows) | 17 | -0.001 to +0.016 | no difference | 0.126 | +0.001 to +0.029 | worse | 0.033 |
| 126 | random forest | F2 vs F0 (F2 rows) | 17 | -0.001 to +0.028 | no difference | 0.028 | -0.010 to +0.092 | no difference | 0.109 |
| 126 | lightgbm | F2 vs F0 (F2 rows) | 17 | +0.002 to +0.037 | worse | 0.004 | +0.017 to +0.090 | worse | 0.043 |

