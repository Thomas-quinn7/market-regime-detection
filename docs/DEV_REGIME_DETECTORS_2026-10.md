development data only (S&P 500, 2005-2023), no holdout, not a claim

# Alternative regime detectors in place of the HMM, development data, October 2026

Class of every table in this file: **development data only (S&P 500, 2005-2023), no holdout, not a claim**. Written by `examples/dev_regime_detectors.py` at 0d9b0e7 plus uncommitted files, 2026-10-18 13:31Z, 2,000 bootstrap draws (seed 0). Design: amendment A2 of `docs/ML_REGIME_PROTOCOL_DRAFT.md`, committed before the first fit. Every detector is fitted on the training rows only and applied forward (`regimes.detectors`, causality test in `tests/test_detectors.py`). F1[d] = F0 + detector d's input in place of the HMM probability; F1 = the HMM; F1n = pure noise. Every set at a horizon is fitted on the same rows. Stage S8 (d) of the reopen.

Learner at h = 21: **not yet chosen (the race is not finished)**, the lowest mean QLIKE on F0 at h = 21 over the S8 (b) and (c) forecasts, chosen before any detector fit with it.

## Each regime input against F0 (HAR + VIX inputs only)

Class: development data only (S&P 500, 2005-2023), no holdout, not a claim. Paired circular block bootstrap, block max(63, h); DM = HAC Diebold-Mariano, lag 20. The F1n row is the size of a gain that means nothing.

| h | model | set | days | windows | RMSE | QLIKE | dRMSE 95% | DM p (MSE) | dQLIKE 95% | DM p (QLIKE) |
|---|---|---|---|---|---|---|---|---|---|---|
| 5 | ols | F0 | 3237 | 647 | 0.4859 | 0.4654 |  |  |  |  |
| 5 | ols | F1 | 3237 | 647 | no difference | no difference | -0.001 to +0.006 | 0.294 | -0.009 to +0.004 | 0.491 |
| 5 | ols | F1n | 3237 | 647 | no difference | no difference | -0.000 to +0.001 | 0.383 | -0.002 to +0.001 | 0.795 |
| 5 | ols | F1[kmeans 2] | 3237 | 647 | no difference | no difference | -0.002 to +0.007 | 0.354 | -0.008 to +0.007 | 0.948 |
| 5 | ols | F1[kmeans 3] | 3237 | 647 | no difference | no difference | -0.004 to +0.017 | 0.316 | -0.008 to +0.013 | 0.653 |
| 5 | ols | F1[gmm 2] | 3237 | 647 | no difference | worse | -0.002 to +0.003 | 0.939 | +0.000 to +0.024 | 0.065 |
| 5 | ols | F1[gmm 3] | 3237 | 647 | no difference | no difference | -0.013 to +0.021 | 0.611 | -0.010 to +0.017 | 0.680 |
| 5 | ols | F1[changepoint] | 3237 | 647 | no difference | no difference | -0.001 to +0.006 | 0.316 | -0.001 to +0.018 | 0.111 |
| 5 | ols | F1[spectral 2] | 3237 | 647 | no difference | no difference | -0.002 to +0.008 | 0.222 | -0.011 to +0.004 | 0.405 |
| 21 | ols | F0 | 3205 | 152 | 0.4828 | 0.4365 |  |  |  |  |
| 21 | ols | F1 | 3205 | 152 | no difference | no difference | -0.004 to +0.012 | 0.443 | -0.010 to +0.033 | 0.455 |
| 21 | ols | F1n | 3205 | 152 | no difference | no difference | -0.000 to +0.001 | 0.183 | -0.001 to +0.005 | 0.372 |
| 21 | ols | F1[kmeans 2] | 3205 | 152 | no difference | no difference | -0.001 to +0.002 | 0.339 | -0.001 to +0.011 | 0.183 |
| 21 | ols | F1[kmeans 3] | 3205 | 152 | no difference | no difference | -0.009 to +0.026 | 0.498 | -0.016 to +0.028 | 0.660 |
| 21 | ols | F1[gmm 2] | 3205 | 152 | no difference | worse | -0.001 to +0.002 | 0.426 | +0.002 to +0.015 | 0.016 |
| 21 | ols | F1[gmm 3] | 3205 | 152 | no difference | no difference | -0.013 to +0.025 | 0.736 | -0.014 to +0.030 | 0.623 |
| 21 | ols | F1[changepoint] | 3205 | 152 | no difference | no difference | -0.000 to +0.008 | 0.143 | -0.001 to +0.034 | 0.106 |
| 21 | ols | F1[spectral 2] | 3205 | 152 | no difference | no difference | -0.002 to +0.007 | 0.363 | -0.009 to +0.009 | 0.967 |
| 63 | ols | F0 | 3121 | 49 | 0.5216 | 0.5454 |  |  |  |  |
| 63 | ols | F1 | 3121 | 49 | no difference | no difference | -0.004 to +0.023 | 0.152 | -0.015 to +0.036 | 0.452 |
| 63 | ols | F1n | 3121 | 49 | worse | worse | +0.000 to +0.001 | 0.013 | +0.000 to +0.006 | 0.096 |
| 63 | ols | F1[kmeans 2] | 3121 | 49 | no difference | worse | -0.000 to +0.005 | 0.066 | +0.001 to +0.006 | 0.005 |
| 63 | ols | F1[kmeans 3] | 3121 | 49 | no difference | no difference | -0.006 to +0.045 | 0.105 | -0.035 to +0.036 | 0.956 |
| 63 | ols | F1[gmm 2] | 3121 | 49 | no difference | no difference | -0.005 to +0.007 | 0.502 | -0.004 to +0.058 | 0.064 |
| 63 | ols | F1[gmm 3] | 3121 | 49 | no difference | no difference | -0.014 to +0.026 | 0.680 | -0.037 to +0.025 | 0.688 |
| 63 | ols | F1[changepoint] | 3121 | 49 | no difference | no difference | -0.002 to +0.014 | 0.064 | -0.001 to +0.023 | 0.032 |
| 63 | ols | F1[spectral 2] | 3121 | 49 | worse | no difference | +0.000 to +0.010 | 0.007 | -0.008 to +0.009 | 0.684 |

## Label persistence and agreement with the HMM (h = 21 scored rows)

Class: development data only (S&P 500, 2005-2023), no holdout, not a claim. Persistence = share of days with yesterday's label; *share high* = share of days the detector's input exceeds 0.5 (for the mixture, the posterior of the high-vol component); the adjusted Rand index is against the HMM labels (high-vol probability above 0.5). 3,226 days, 2011-03-08 to 2023-12-29.

| detector | share high | persistence | adjusted Rand vs HMM |
|---|---|---|---|
| HMM (prob > 0.5) | 0.210 | 0.950 | 1.000 |
| kmeans 2 | 0.294 | 0.968 | 0.635 |
| kmeans 3 | 0.085 | 0.933 | 0.287 |
| gmm 2 | 0.326 | 0.930 | 0.503 |
| gmm 3 | 0.060 | 0.909 | 0.205 |
| changepoint | 0.383 | 0.993 | 0.181 |
| spectral 2 | 0.350 | 0.968 | 0.459 |

