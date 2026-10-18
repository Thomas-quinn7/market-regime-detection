development data only (S&P 500, 2005-2023), no holdout, not a claim

# The best-forecaster race, development data, October 2026

**Known limit, first:** one series (the S&P 500), about 3,200 scored days at 21 days (about 150 non-overlapping windows). A gain over HAR + VIX is expected to be small and concentrated in the high-vol tercile; a race won by a few tenths of a percent of RMSE is a description of this sample, not a finding.

Class of every table in this file: **development data only (S&P 500, 2005-2023), no holdout, not a claim**. Written by `examples/dev_ml_race.py` at b0500c8 plus uncommitted files, 2026-10-18 17:24Z, 2,000 bootstrap draws (seed 0). Design: amendment A1 of `docs/ML_REGIME_PROTOCOL_DRAFT.md`, committed before the first fit. The LSTM and GRU forecasts are in `docs/results/dev_ml_race/`; every other forecast is read from the S8 (b) cache `docs/results/dev_ml_regime/` and scored here on the same rows. The recurrent learners need 65 earlier days as input, so their first 65 F1 rows serve only as inputs and each training window is 65 rows shorter than the other learners'; the scored rows are the same. Stage S8 (c) of the reopen.

Every comparison is against OLS on F0 (HAR + VIX): paired circular block bootstrap, block max(63, h), and HAC Diebold-Mariano, lag 20. The model confidence set (Hansen, Lunde and Nason 2011, T_max, 10%) is over every forecast present at the horizon, on squared error (the RMSE loss) and on QLIKE; it is post hoc and descriptive. Nothing here is a claim.

## Horizon 5

Scored days 3,258, 2011-01-12 to 2023-12-21, windows 651.

| forecast | RMSE | QLIKE | MCS p (sq. error) | MCS p (QLIKE) |
|---|---|---|---|---|
| gru F0 | 0.4829 | 0.4542 | 1.000 | 1.000 |
| ols F1 | 0.4871 | 0.4639 | 0.864 | 0.800 |
| lasso F1 | 0.4895 | 0.4641 | 0.864 | 0.800 |
| lasso F1n | 0.4880 | 0.4643 | 0.864 | 0.800 |
| lasso F0 | 0.4874 | 0.4650 | 0.864 | 0.800 |
| ols F1n | 0.4855 | 0.4663 | 0.864 | 0.800 |
| ols F0 | 0.4850 | 0.4663 | 0.867 | 0.800 |
| ridge F1 | 0.4897 | 0.4668 | 0.864 | 0.800 |
| ridge F1n | 0.4875 | 0.4680 | 0.864 | 0.712 |
| ridge F0 | 0.4869 | 0.4683 | 0.864 | 0.712 |
| mlp F0 | 0.4910 | 0.4739 | 0.804 | 0.712 |
| lightgbm F0 | 0.5011 | 0.4778 | 0.667 | 0.712 |
| lightgbm F1n | 0.5035 | 0.4781 | 0.647 | 0.712 |
| mlp F1 | 0.4968 | 0.4810 | 0.804 | 0.712 |
| mlp F1n | 0.5048 | 0.4815 | 0.609 | 0.712 |
| lightgbm F1 | 0.5025 | 0.4849 | 0.667 | 0.712 |
| random forest F1n | 0.5358 | 0.4902 | 0.628 | 0.712 |
| lstm F1n | 0.5044 | 0.4907 | 0.628 | 0.712 |
| random forest F0 | 0.5358 | 0.4911 | 0.628 | 0.712 |
| random forest F1 | 0.5346 | 0.4929 | 0.651 | 0.712 |
| lstm F0 | 0.4956 | 0.5155 | 0.864 | 0.712 |
| gru F1 | 0.5030 | 0.5207 | 0.667 | 0.712 |
| lstm F1 | 0.4930 | 0.5238 | 0.804 | 0.048 |
| gru F1n | 0.5016 | 0.5542 | 0.667 | 0.712 |

In the 10% MCS on squared error: ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, lightgbm F1n, mlp F0, mlp F1, mlp F1n, lstm F0, lstm F1, lstm F1n, gru F0, gru F1, gru F1n. On QLIKE: ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, lightgbm F1n, mlp F0, mlp F1, mlp F1n, lstm F0, lstm F1n, gru F0, gru F1, gru F1n.

## Horizon 21

Scored days 3,226, 2011-02-04 to 2023-11-29, windows 153.

| forecast | RMSE | QLIKE | MCS p (sq. error) | MCS p (QLIKE) |
|---|---|---|---|---|
| lasso F1n | 0.4896 | 0.4311 | 0.742 | 1.000 |
| ols F0 | 0.4814 | 0.4333 | 1.000 | 0.910 |
| lasso F0 | 0.4909 | 0.4343 | 0.742 | 0.910 |
| ols F1n | 0.4818 | 0.4346 | 0.742 | 0.910 |
| ridge F0 | 0.4888 | 0.4389 | 0.742 | 0.707 |
| ridge F1n | 0.4893 | 0.4403 | 0.742 | 0.707 |
| ols F1 | 0.4838 | 0.4409 | 0.742 | 0.813 |
| lasso F1 | 0.4909 | 0.4433 | 0.742 | 0.707 |
| ridge F1 | 0.4914 | 0.4460 | 0.742 | 0.663 |
| mlp F1n | 0.5132 | 0.4695 | 0.664 | 0.663 |
| lightgbm F0 | 0.4982 | 0.4744 | 0.664 | 0.663 |
| mlp F0 | 0.5122 | 0.4759 | 0.664 | 0.663 |
| lightgbm F1n | 0.4984 | 0.4766 | 0.664 | 0.663 |
| random forest F1n | 0.5087 | 0.4852 | 0.664 | 0.663 |
| random forest F0 | 0.5089 | 0.4860 | 0.664 | 0.663 |
| mlp F1 | 0.5149 | 0.4880 | 0.664 | 0.663 |
| gru F0 | 0.5657 | 0.4962 | 0.664 | 0.663 |
| lightgbm F1 | 0.4984 | 0.5174 | 0.742 | 0.663 |
| random forest F1 | 0.5133 | 0.5179 | 0.664 | 0.663 |
| gru F1 | 0.5204 | 0.5881 | 0.664 | 0.629 |
| lstm F0 | 0.5710 | 0.5887 | 0.139 | 0.277 |
| lstm F1 | 0.5284 | 0.6162 | 0.569 | 0.277 |
| lstm F1n | 0.5644 | 0.6399 | 0.142 | 0.098 |
| gru F1n | 0.5458 | 0.7688 | 0.664 | 0.663 |

In the 10% MCS on squared error: ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, lightgbm F1n, mlp F0, mlp F1, mlp F1n, lstm F0, lstm F1, lstm F1n, gru F0, gru F1, gru F1n. On QLIKE: ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, lightgbm F1n, mlp F0, mlp F1, mlp F1n, lstm F0, lstm F1, gru F0, gru F1, gru F1n.

## Horizon 63

Scored days 3,142, 2011-04-06 to 2023-09-29, windows 49; not yet fitted: lstm F0, lstm F1, lstm F1n, gru F0, gru F1, gru F1n.

| forecast | RMSE | QLIKE | MCS p (sq. error) | MCS p (QLIKE) |
|---|---|---|---|---|
| lasso F0 | 0.5309 | 0.5386 | 0.435 | 1.000 |
| lasso F1n | 0.5309 | 0.5386 | 0.435 | 0.966 |
| ols F0 | 0.5203 | 0.5454 | 1.000 | 0.939 |
| lasso F1 | 0.5357 | 0.5458 | 0.435 | 0.939 |
| ols F1n | 0.5208 | 0.5471 | 0.435 | 0.939 |
| ols F1 | 0.5259 | 0.5525 | 0.435 | 0.801 |
| ridge F0 | 0.5370 | 0.5709 | 0.435 | 0.621 |
| ridge F1n | 0.5374 | 0.5727 | 0.435 | 0.621 |
| ridge F1 | 0.5430 | 0.5773 | 0.393 | 0.540 |
| mlp F1n | 0.5565 | 0.5880 | 0.393 | 0.387 |
| lightgbm F1n | 0.5680 | 0.5935 | 0.087 | 0.387 |
| lightgbm F1 | 0.5519 | 0.5958 | 0.393 | 0.621 |
| random forest F1n | 0.5567 | 0.5966 | 0.195 | 0.387 |
| random forest F0 | 0.5569 | 0.5967 | 0.195 | 0.387 |
| lightgbm F0 | 0.5712 | 0.5972 | 0.102 | 0.387 |
| random forest F1 | 0.5565 | 0.6244 | 0.195 | 0.240 |
| mlp F1 | 0.5580 | 0.6259 | 0.344 | 0.387 |
| mlp F0 | 0.5668 | 0.7111 | 0.195 | 0.387 |

In the 10% MCS on squared error: ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, mlp F0, mlp F1, mlp F1n. On QLIKE: ols F0, ols F1, ols F1n, ridge F0, ridge F1, ridge F1n, lasso F0, lasso F1, lasso F1n, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, lightgbm F1n, mlp F0, mlp F1, mlp F1n.

## Every forecast against HAR + VIX (OLS on F0)

Class: development data only (S&P 500, 2005-2023), no holdout, not a claim.

| h | forecast | windows | dRMSE 95% | RMSE | DM p (MSE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|
| 5 | ols F1 | 651 | -0.001 to +0.006 | no difference | 0.297 | -0.009 to +0.004 | no difference | 0.482 |
| 5 | ols F1n | 651 | -0.000 to +0.001 | no difference | 0.366 | -0.002 to +0.001 | no difference | 0.993 |
| 5 | ridge F0 | 651 | -0.001 to +0.005 | no difference | 0.252 | -0.005 to +0.009 | no difference | 0.504 |
| 5 | ridge F1 | 651 | -0.000 to +0.009 | no difference | 0.129 | -0.009 to +0.010 | no difference | 0.913 |
| 5 | ridge F1n | 651 | -0.001 to +0.006 | no difference | 0.219 | -0.006 to +0.009 | no difference | 0.605 |
| 5 | lasso F0 | 651 | -0.001 to +0.005 | no difference | 0.176 | -0.010 to +0.007 | no difference | 0.741 |
| 5 | lasso F1 | 651 | -0.000 to +0.009 | no difference | 0.132 | -0.012 to +0.007 | no difference | 0.645 |
| 5 | lasso F1n | 651 | -0.001 to +0.006 | no difference | 0.170 | -0.011 to +0.007 | no difference | 0.639 |
| 5 | random forest F0 | 651 | +0.008 to +0.102 | worse | 0.140 | -0.005 to +0.057 | no difference | 0.096 |
| 5 | random forest F1 | 651 | +0.006 to +0.102 | worse | 0.152 | -0.006 to +0.062 | no difference | 0.093 |
| 5 | random forest F1n | 651 | +0.008 to +0.102 | worse | 0.140 | -0.006 to +0.056 | no difference | 0.109 |
| 5 | lightgbm F0 | 651 | +0.001 to +0.032 | worse | 0.131 | -0.011 to +0.033 | no difference | 0.274 |
| 5 | lightgbm F1 | 651 | +0.002 to +0.033 | worse | 0.094 | -0.008 to +0.044 | no difference | 0.135 |
| 5 | lightgbm F1n | 651 | +0.002 to +0.035 | worse | 0.089 | -0.008 to +0.032 | no difference | 0.232 |
| 5 | mlp F0 | 651 | -0.002 to +0.015 | no difference | 0.199 | -0.008 to +0.023 | no difference | 0.359 |
| 5 | mlp F1 | 651 | -0.002 to +0.025 | no difference | 0.133 | -0.007 to +0.035 | no difference | 0.137 |
| 5 | mlp F1n | 651 | +0.005 to +0.035 | worse | 0.034 | -0.005 to +0.034 | no difference | 0.125 |
| 5 | lstm F0 | 651 | -0.020 to +0.044 | no difference | 0.447 | -0.004 to +0.109 | no difference | 0.066 |
| 5 | lstm F1 | 651 | -0.008 to +0.026 | no difference | 0.267 | +0.024 to +0.094 | worse | 0.001 |
| 5 | lstm F1n | 651 | +0.005 to +0.033 | worse | 0.019 | -0.008 to +0.055 | no difference | 0.116 |
| 5 | gru F0 | 651 | -0.026 to +0.022 | no difference | 0.850 | -0.040 to +0.013 | no difference | 0.378 |
| 5 | gru F1 | 651 | -0.004 to +0.038 | no difference | 0.108 | +0.001 to +0.137 | worse | 0.055 |
| 5 | gru F1n | 651 | -0.004 to +0.040 | no difference | 0.063 | +0.006 to +0.205 | worse | 0.050 |
| 21 | ols F1 | 153 | -0.004 to +0.012 | no difference | 0.469 | -0.009 to +0.032 | no difference | 0.449 |
| 21 | ols F1n | 153 | -0.000 to +0.001 | no difference | 0.240 | -0.001 to +0.005 | no difference | 0.389 |
| 21 | ridge F0 | 153 | +0.001 to +0.019 | worse | 0.017 | -0.003 to +0.014 | no difference | 0.137 |
| 21 | ridge F1 | 153 | -0.000 to +0.027 | no difference | 0.034 | -0.006 to +0.036 | no difference | 0.177 |
| 21 | ridge F1n | 153 | +0.001 to +0.019 | worse | 0.011 | -0.002 to +0.016 | no difference | 0.073 |
| 21 | lasso F0 | 153 | +0.001 to +0.022 | worse | 0.015 | -0.014 to +0.016 | no difference | 0.883 |
| 21 | lasso F1 | 153 | -0.001 to +0.026 | no difference | 0.043 | -0.008 to +0.031 | no difference | 0.274 |
| 21 | lasso F1n | 153 | +0.000 to +0.020 | worse | 0.026 | -0.022 to +0.015 | no difference | 0.799 |
| 21 | random forest F0 | 153 | +0.007 to +0.052 | worse | 0.011 | +0.000 to +0.121 | worse | 0.069 |
| 21 | random forest F1 | 153 | +0.012 to +0.057 | worse | 0.002 | +0.008 to +0.189 | worse | 0.045 |
| 21 | random forest F1n | 153 | +0.007 to +0.052 | worse | 0.012 | -0.000 to +0.119 | no difference | 0.071 |
| 21 | lightgbm F0 | 153 | -0.003 to +0.044 | no difference | 0.151 | +0.001 to +0.096 | worse | 0.070 |
| 21 | lightgbm F1 | 153 | -0.006 to +0.048 | no difference | 0.181 | +0.007 to +0.185 | worse | 0.044 |
| 21 | lightgbm F1n | 153 | -0.003 to +0.044 | no difference | 0.133 | -0.001 to +0.106 | no difference | 0.083 |
| 21 | mlp F0 | 153 | +0.013 to +0.054 | worse | 0.003 | +0.016 to +0.074 | worse | 0.003 |
| 21 | mlp F1 | 153 | +0.010 to +0.065 | worse | 0.035 | +0.009 to +0.126 | worse | 0.055 |
| 21 | mlp F1n | 153 | +0.010 to +0.064 | worse | 0.038 | +0.011 to +0.065 | worse | 0.007 |
| 21 | lstm F0 | 153 | +0.039 to +0.164 | worse | 0.001 | +0.054 to +0.296 | worse | 0.004 |
| 21 | lstm F1 | 153 | +0.024 to +0.066 | worse | 0.007 | +0.045 to +0.386 | worse | 0.016 |
| 21 | lstm F1n | 153 | +0.049 to +0.132 | worse | 0.000 | +0.068 to +0.397 | worse | 0.006 |
| 21 | gru F0 | 153 | +0.011 to +0.210 | worse | 0.023 | +0.016 to +0.130 | worse | 0.004 |
| 21 | gru F1 | 153 | +0.011 to +0.082 | worse | 0.006 | +0.021 to +0.385 | worse | 0.062 |
| 21 | gru F1n | 153 | +0.021 to +0.104 | worse | 0.035 | +0.030 to +0.923 | worse | 0.179 |
| 63 | ols F1 | 49 | -0.005 to +0.021 | no difference | 0.210 | -0.016 to +0.038 | no difference | 0.476 |
| 63 | ols F1n | 49 | +0.000 to +0.001 | worse | 0.021 | -0.000 to +0.005 | no difference | 0.105 |
| 63 | ridge F0 | 49 | +0.002 to +0.042 | worse | 0.003 | +0.005 to +0.051 | worse | 0.001 |
| 63 | ridge F1 | 49 | +0.005 to +0.054 | worse | 0.002 | +0.004 to +0.065 | worse | 0.006 |
| 63 | ridge F1n | 49 | +0.003 to +0.042 | worse | 0.002 | +0.005 to +0.054 | worse | 0.002 |
| 63 | lasso F0 | 49 | -0.002 to +0.027 | no difference | 0.118 | -0.076 to +0.040 | no difference | 0.800 |
| 63 | lasso F1 | 49 | +0.002 to +0.034 | worse | 0.037 | -0.071 to +0.054 | no difference | 0.989 |
| 63 | lasso F1n | 49 | -0.002 to +0.027 | no difference | 0.116 | -0.076 to +0.040 | no difference | 0.800 |
| 63 | random forest F0 | 49 | +0.012 to +0.072 | worse | 0.000 | -0.017 to +0.119 | no difference | 0.088 |
| 63 | random forest F1 | 49 | +0.013 to +0.070 | worse | 0.001 | +0.014 to +0.158 | worse | 0.014 |
| 63 | random forest F1n | 49 | +0.012 to +0.072 | worse | 0.000 | -0.017 to +0.119 | no difference | 0.088 |
| 63 | lightgbm F0 | 49 | +0.020 to +0.099 | worse | 0.000 | -0.021 to +0.121 | no difference | 0.089 |
| 63 | lightgbm F1 | 49 | +0.004 to +0.073 | worse | 0.005 | -0.062 to +0.158 | no difference | 0.279 |
| 63 | lightgbm F1n | 49 | +0.019 to +0.092 | worse | 0.000 | -0.024 to +0.116 | no difference | 0.114 |
| 63 | mlp F0 | 49 | +0.019 to +0.086 | worse | 0.000 | +0.027 to +0.370 | worse | 0.021 |
| 63 | mlp F1 | 49 | +0.007 to +0.077 | worse | 0.008 | +0.008 to +0.179 | worse | 0.027 |
| 63 | mlp F1n | 49 | +0.008 to +0.074 | worse | 0.009 | -0.017 to +0.103 | no difference | 0.105 |

## Worse than HAR + VIX in the pair, yet in the MCS

Class: development data only (S&P 500, 2005-2023), no holdout, not a claim. The paired interval asks whether one forecast differs from HAR + VIX; the T_max MCS asks whether a forecast is worse than the average of every forecast in the set, against a critical value for the largest of all those statistics. With about 20 forecasts that bar is high, so a forecast can lose to HAR + VIX and still stay in the set. Membership of the MCS is therefore not evidence that a forecast matches HAR + VIX; the paired verdict is the comparison that answers that question.

| h | loss | worse than HAR + VIX | of which in the MCS | forecasts |
|---|---|---|---|---|
| 5 | QLIKE | 3 | 2 | gru F1, gru F1n |
| 5 | RMSE | 8 | 8 | random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, lightgbm F1n, mlp F1n, lstm F1n |
| 21 | QLIKE | 13 | 12 | random forest F0, random forest F1, lightgbm F0, lightgbm F1, mlp F0, mlp F1, mlp F1n, lstm F0, lstm F1, gru F0, gru F1, gru F1n |
| 21 | RMSE | 16 | 16 | ridge F0, ridge F1n, lasso F0, lasso F1n, random forest F0, random forest F1, random forest F1n, mlp F0, mlp F1, mlp F1n, lstm F0, lstm F1, lstm F1n, gru F0, gru F1, gru F1n |
| 63 | QLIKE | 6 | 6 | ridge F0, ridge F1, ridge F1n, random forest F1, mlp F0, mlp F1 |
| 63 | RMSE | 14 | 13 | ols F1n, ridge F0, ridge F1, ridge F1n, lasso F1, random forest F0, random forest F1, random forest F1n, lightgbm F0, lightgbm F1, mlp F0, mlp F1, mlp F1n |

## By tercile of the training-window VIX: each learner on F0 against HAR + VIX

Class: development data only (S&P 500, 2005-2023), no holdout, not a claim. The tercile cut points are the 33rd and 67th percentiles of the VIX over each refit's training rows; the bootstrap runs over the tercile's days joined end to end, so its blocks cross the gaps between them (an approximation, stated). Every forecast and feature set: `docs/results/dev_ml_race/terciles.csv`.

| h | tercile | forecast | days | RMSE of forecast | RMSE HAR + VIX | dRMSE 95% | RMSE | DM p (MSE) | dQLIKE 95% | QLIKE | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 5 | low | ridge F0 | 1728 | 0.2878 | 0.2872 | -0.000 to +0.002 | no difference | 0.321 | -0.006 to +0.005 | no difference | 0.877 |
| 5 | low | lasso F0 | 1728 | 0.2897 | 0.2872 | -0.001 to +0.006 | no difference | 0.193 | -0.017 to +0.008 | no difference | 0.501 |
| 5 | low | random forest F0 | 1728 | 0.2956 | 0.2872 | -0.000 to +0.018 | no difference | 0.032 | -0.039 to +0.039 | no difference | 0.866 |
| 5 | low | lightgbm F0 | 1728 | 0.2990 | 0.2872 | +0.001 to +0.024 | worse | 0.011 | -0.029 to +0.050 | no difference | 0.558 |
| 5 | low | mlp F0 | 1728 | 0.2943 | 0.2872 | +0.002 to +0.012 | worse | 0.011 | -0.012 to +0.033 | no difference | 0.434 |
| 5 | low | lstm F0 | 1728 | 0.3160 | 0.2872 | +0.014 to +0.047 | worse | 0.001 | -0.014 to +0.090 | no difference | 0.192 |
| 5 | low | gru F0 | 1728 | 0.2989 | 0.2872 | +0.002 to +0.022 | worse | 0.019 | -0.044 to +0.022 | no difference | 0.580 |
| 5 | middle | ridge F0 | 793 | 0.4464 | 0.4458 | -0.003 to +0.005 | no difference | 0.815 | -0.012 to +0.025 | no difference | 0.538 |
| 5 | middle | lasso F0 | 793 | 0.4465 | 0.4458 | -0.003 to +0.005 | no difference | 0.744 | -0.012 to +0.014 | no difference | 0.897 |
| 5 | middle | random forest F0 | 793 | 0.4560 | 0.4458 | +0.004 to +0.016 | worse | 0.009 | +0.006 to +0.055 | worse | 0.046 |
| 5 | middle | lightgbm F0 | 793 | 0.4537 | 0.4458 | +0.001 to +0.014 | worse | 0.044 | -0.009 to +0.047 | no difference | 0.159 |
| 5 | middle | mlp F0 | 793 | 0.4493 | 0.4458 | -0.003 to +0.012 | no difference | 0.391 | -0.021 to +0.027 | no difference | 0.732 |
| 5 | middle | lstm F0 | 793 | 0.4692 | 0.4458 | -0.000 to +0.044 | no difference | 0.047 | -0.012 to +0.194 | no difference | 0.086 |
| 5 | middle | gru F0 | 793 | 0.4499 | 0.4458 | -0.011 to +0.021 | no difference | 0.598 | -0.067 to +0.030 | no difference | 0.417 |
| 5 | high | ridge F0 | 737 | 0.7998 | 0.7955 | -0.004 to +0.010 | no difference | 0.287 | -0.004 to +0.012 | no difference | 0.392 |
| 5 | high | lasso F0 | 737 | 0.7994 | 0.7955 | -0.004 to +0.010 | no difference | 0.347 | -0.004 to +0.013 | no difference | 0.357 |
| 5 | high | random forest F0 | 737 | 0.9169 | 0.7955 | +0.009 to +0.237 | worse | 0.172 | -0.003 to +0.193 | no difference | 0.162 |
| 5 | high | lightgbm F0 | 737 | 0.8239 | 0.7955 | -0.018 to +0.068 | no difference | 0.312 | -0.023 to +0.029 | no difference | 0.777 |
| 5 | high | mlp F0 | 737 | 0.8035 | 0.7955 | -0.009 to +0.031 | no difference | 0.498 | -0.017 to +0.027 | no difference | 0.698 |
| 5 | high | lstm F0 | 737 | 0.7841 | 0.7955 | -0.069 to +0.071 | no difference | 0.730 | -0.056 to +0.161 | no difference | 0.437 |
| 5 | high | gru F0 | 737 | 0.7770 | 0.7955 | -0.073 to +0.054 | no difference | 0.531 | -0.070 to +0.039 | no difference | 0.712 |
| 21 | low | ridge F0 | 1698 | 0.3625 | 0.3613 | -0.001 to +0.004 | no difference | 0.248 | -0.007 to +0.016 | no difference | 0.497 |
| 21 | low | lasso F0 | 1698 | 0.3618 | 0.3613 | -0.004 to +0.006 | no difference | 0.824 | -0.036 to +0.010 | no difference | 0.314 |
| 21 | low | random forest F0 | 1698 | 0.3720 | 0.3613 | -0.002 to +0.024 | no difference | 0.082 | -0.023 to +0.141 | no difference | 0.226 |
| 21 | low | lightgbm F0 | 1698 | 0.3799 | 0.3613 | +0.003 to +0.037 | worse | 0.022 | -0.017 to +0.145 | no difference | 0.190 |
| 21 | low | mlp F0 | 1698 | 0.3801 | 0.3613 | +0.008 to +0.033 | worse | 0.000 | +0.004 to +0.096 | worse | 0.035 |
| 21 | low | lstm F0 | 1698 | 0.4548 | 0.3613 | +0.025 to +0.199 | worse | 0.035 | +0.007 to +0.356 | worse | 0.090 |
| 21 | low | gru F0 | 1698 | 0.5289 | 0.3613 | +0.017 to +0.367 | worse | 0.032 | +0.016 to +0.207 | worse | 0.006 |
| 21 | middle | ridge F0 | 794 | 0.5099 | 0.5083 | -0.004 to +0.006 | no difference | 0.520 | -0.010 to +0.012 | no difference | 0.878 |
| 21 | middle | lasso F0 | 794 | 0.5106 | 0.5083 | -0.001 to +0.006 | no difference | 0.244 | -0.022 to +0.010 | no difference | 0.691 |
| 21 | middle | random forest F0 | 794 | 0.5184 | 0.5083 | -0.003 to +0.019 | no difference | 0.123 | +0.003 to +0.198 | worse | 0.146 |
| 21 | middle | lightgbm F0 | 794 | 0.5221 | 0.5083 | +0.003 to +0.028 | worse | 0.022 | +0.018 to +0.081 | worse | 0.004 |
| 21 | middle | mlp F0 | 794 | 0.5258 | 0.5083 | +0.006 to +0.037 | worse | 0.028 | +0.009 to +0.065 | worse | 0.042 |
| 21 | middle | lstm F0 | 794 | 0.5836 | 0.5083 | +0.018 to +0.178 | worse | 0.045 | +0.059 to +0.204 | worse | 0.006 |
| 21 | middle | gru F0 | 794 | 0.5250 | 0.5083 | -0.002 to +0.045 | no difference | 0.139 | -0.003 to +0.134 | no difference | 0.058 |
| 21 | high | ridge F0 | 734 | 0.6819 | 0.6613 | +0.001 to +0.057 | worse | 0.019 | -0.002 to +0.035 | no difference | 0.045 |
| 21 | high | lasso F0 | 734 | 0.6886 | 0.6613 | +0.004 to +0.062 | worse | 0.013 | +0.006 to +0.061 | worse | 0.010 |
| 21 | high | random forest F0 | 734 | 0.7261 | 0.6613 | +0.017 to +0.139 | worse | 0.023 | +0.013 to +0.065 | worse | 0.010 |
| 21 | high | lightgbm F0 | 734 | 0.6798 | 0.6613 | -0.028 to +0.095 | no difference | 0.595 | -0.043 to +0.043 | no difference | 0.747 |
| 21 | high | mlp F0 | 734 | 0.7207 | 0.6613 | +0.017 to +0.127 | worse | 0.048 | -0.002 to +0.103 | no difference | 0.100 |
| 21 | high | lstm F0 | 734 | 0.7655 | 0.6613 | +0.012 to +0.267 | worse | 0.024 | +0.016 to +0.558 | worse | 0.024 |
| 21 | high | gru F0 | 734 | 0.6790 | 0.6613 | -0.036 to +0.086 | no difference | 0.623 | -0.051 to +0.022 | no difference | 0.552 |
| 63 | low | ridge F0 | 1648 | 0.5149 | 0.5166 | -0.010 to +0.003 | no difference | 0.342 | -0.011 to +0.039 | no difference | 0.242 |
| 63 | low | lasso F0 | 1648 | 0.5189 | 0.5166 | -0.010 to +0.021 | no difference | 0.670 | -0.187 to +0.040 | no difference | 0.382 |
| 63 | low | random forest F0 | 1648 | 0.5288 | 0.5166 | -0.006 to +0.044 | no difference | 0.143 | -0.112 to +0.159 | no difference | 0.574 |
| 63 | low | lightgbm F0 | 1648 | 0.5433 | 0.5166 | +0.001 to +0.068 | worse | 0.008 | -0.122 to +0.170 | no difference | 0.567 |
| 63 | low | mlp F0 | 1648 | 0.5545 | 0.5166 | +0.008 to +0.090 | worse | 0.000 | -0.111 to +0.152 | no difference | 0.453 |
| 63 | middle | ridge F0 | 765 | 0.5803 | 0.5720 | -0.008 to +0.022 | no difference | 0.119 | -0.008 to +0.071 | no difference | 0.083 |
| 63 | middle | lasso F0 | 765 | 0.5768 | 0.5720 | -0.010 to +0.021 | no difference | 0.364 | -0.024 to +0.032 | no difference | 0.805 |
| 63 | middle | random forest F0 | 765 | 0.6188 | 0.5720 | +0.011 to +0.111 | worse | 0.008 | +0.023 to +0.161 | worse | 0.013 |
| 63 | middle | lightgbm F0 | 765 | 0.6534 | 0.5720 | +0.020 to +0.194 | worse | 0.030 | +0.028 to +0.171 | worse | 0.009 |
| 63 | middle | mlp F0 | 765 | 0.5766 | 0.5720 | -0.046 to +0.036 | no difference | 0.765 | +0.002 to +0.144 | worse | 0.081 |
| 63 | high | ridge F0 | 729 | 0.5387 | 0.4690 | +0.011 to +0.142 | worse | 0.001 | +0.014 to +0.102 | worse | 0.000 |
| 63 | high | lasso F0 | 729 | 0.5068 | 0.4690 | -0.012 to +0.077 | no difference | 0.171 | +0.006 to +0.135 | worse | 0.044 |
| 63 | high | random forest F0 | 729 | 0.5501 | 0.4690 | +0.020 to +0.139 | worse | 0.011 | +0.018 to +0.104 | worse | 0.001 |
| 63 | high | lightgbm F0 | 729 | 0.5395 | 0.4690 | -0.002 to +0.134 | no difference | 0.037 | +0.004 to +0.091 | worse | 0.005 |
| 63 | high | mlp F0 | 729 | 0.5840 | 0.4690 | +0.041 to +0.197 | worse | 0.007 | +0.098 to +1.354 | worse | 0.039 |

