development data only, no holdout

# K = 3 and 4 Student-t HMMs as forecasters, October 2026

Class of every table in this file: **development data only (S&P 500, 2005-2023), no holdout**. Continuation (b) of the reopen scope; no holdout is opened, no registered verdict is touched, nothing here is a claim. Written by `examples/dev_k_states.py` (fits at 45626ea plus uncommitted files, 2026-10-18 00:49Z, 3532 s with 6 processes; markdown at 45626ea plus uncommitted files, 2026-10-18 00:50Z), 2,000 bootstrap draws (seed 0). Data: S&P 500 and VIX 2005-01-04 to 2023-12-29 (4780 days) from the committed caches. Source of the item: panel, item 10 and question 2; desk, quant-researcher 11.

## 1. Gaussian two-, three- and four-state fits: default start vs 20 random starts

statsmodels `MarkovRegression` (switching variance, constant mean), the model behind the paper's selection table (`regimes.selection.select_n_regimes`), on the full development sample. `search_reps=0` is the paper's default start; `search_reps=20` tries 20 random starts before the optimiser (numpy's global seed set to 0 before each fit, so the table is reproducible). AIC and BIC are statsmodels' (Gaussian likelihood), so they are comparable within this table only.

| K | search_reps | AIC | BIC | loglik | converged | sigma (daily %) | seconds |
|---|---|---|---|---|---|---|---|
| 2 | 0 | 13203.2 | 13242.1 | -6595.62 | True | 0.672, 2.058 | 0 |
| 3 | 0 | 12702.2 | 12779.9 | -6339.11 | False | 0.540, 1.281, 3.592 | 5 |
| 4 | 0 | 12668.3 | 12797.8 | -6314.16 | False | 0.518, 0.973, 1.012, 2.961 | 16 |
| 2 | 20 | 13203.2 | 13242.1 | -6595.62 | True | 0.672, 2.057 | 1 |
| 3 | 20 | 12702.2 | 12779.9 | -6339.11 | False | 0.540, 1.282, 3.599 | 5 |
| 4 | 20 | 12667.5 | 12797.0 | -6313.77 | False | 0.517, 0.957, 0.961, 2.895 | 16 |

## 2. Student-t fits with 20 starts, full development sample

EM (`regimes.kstate.em_student_t`, the updates of `regimes.student_t`) from one deterministic start and 19 random starts (seed 0), shared nu estimated, at most 500 iterations, tolerance 0.0001 on the log-likelihood gain per iteration (the robustness fitter in `regimes.student_t` uses 200 and 1e-6; EM converges linearly and the K = 3 and 4 fits creep past 200 iterations at that tolerance, so the cap and tolerance here are looser and are reported with every count). 'Starts at best loglik' counts starts within 0.01 of the best. Parameters: 2K means and scales, K(K-1) transition probabilities, K-1 initial probabilities, nu. AIC and BIC here use the Student-t likelihood and are comparable within this table only.

| K | starts | converged starts | starts at best loglik | best loglik | AIC | BIC | nu | sigma (daily %) | stay prob | best start converged | seconds |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 20 | 20 | 20 | -6443.29 | 12902.6 | 12954.4 | 4.76 | 0.512, 1.387 | 0.989, 0.980 | True | 17 |
| 3 | 20 | 20 | 7 | -6311.29 | 12652.6 | 12749.7 | 9.37 | 0.493, 1.165, 3.179 | 0.979, 0.972, 0.981 | True | 28 |
| 4 | 20 | 20 | 20 | -6257.65 | 12563.3 | 12718.6 | 15.13 | 0.451, 0.875, 1.439, 3.715 | 0.960, 0.947, 0.982, 0.974 | True | 84 |

## 3. Walk-forward convergence

Refit every 63 days after 756 rows (the VIX protocol), 20 starts per refit (seed = refit number), parameters frozen and filtered forward over the next block; per-refit convergence in `docs/results/dev_k_states/convergence_k*.csv`. 'Refits converged' counts refits whose best start met the tolerance within the iteration cap.

| model | refits | refits converged | refits with all starts converged | median starts at best loglik |
|---|---|---|---|---|
| Gaussian K=2 (statsmodels, default start) | 64 | 64 | n/a | n/a |
| Student-t K=2 (20 starts per refit) | 64 | 64 | 64 | 20 |
| Student-t K=3 (20 starts per refit) | 64 | 64 | 62 | 20 |
| Student-t K=4 (20 starts per refit) | 64 | 64 | 53 | 12 |

## 4. 21-day forecasts, 2011-2023, same construction as the frozen VIX script

Scored days 3226, 2011-02-04 to 2023-11-29. Target: realised vol over the next 21 days (daily percent). 'Calibrated' = expanding OLS of the log target on the log implied vol, refit every 63 days after 756 rows, embargo 21, as the VIX script calibrates 'HMM implied vol'; 'raw' = the model's own number. 'K=k prob' is the probability of the highest-variance state; 'expected var' is the log of the filtered expected variance (sum of state probabilities times state variances), which carries the K-state information that a single state probability does not when K > 2.

| forecast | RMSE | QLIKE |
|---|---|---|
| HAR | 0.508 | 0.468 |
| HAR + VIX | 0.479 | 0.422 |
| HAR + VIX + HMM prob (Gaussian K=2) | 0.484 | 0.441 |
| HMM implied vol (Gaussian K=2), calibrated | 0.574 | 0.526 |
| HAR + VIX + K=2 prob | 0.485 | 0.441 |
| HAR + VIX + K=2 expected var | 0.481 | 0.429 |
| K=2 implied vol, calibrated | 0.584 | 0.542 |
| HAR + VIX + K=3 prob | 0.479 | 0.445 |
| HAR + VIX + K=3 expected var | 0.484 | 0.436 |
| K=3 implied vol, calibrated | 0.533 | 0.476 |
| HAR + VIX + K=4 prob | 0.477 | 0.444 |
| HAR + VIX + K=4 expected var | 0.485 | 0.434 |
| K=4 implied vol, calibrated | 0.510 | 0.460 |
| HMM implied vol (Gaussian K=2), raw | 0.589 | 0.487 |
| K=2 implied vol, raw | 0.607 | 0.501 |
| K=3 implied vol, raw | 0.565 | 0.435 |
| K=4 implied vol, raw | 0.526 | 0.435 |

Paired circular block bootstrap, block 63, 95% intervals for forecast minus reference (negative = forecast better):

| forecast | reference | block | dRMSE 95% | RMSE | dQLIKE 95% | QLIKE |
|---|---|---|---|---|---|---|
| K=3 implied vol, calibrated | K=2 implied vol, calibrated | 63 | -0.081 to -0.014 | better | -0.163 to +0.005 | no difference |
| K=4 implied vol, calibrated | K=2 implied vol, calibrated | 63 | -0.109 to -0.032 | better | -0.178 to -0.011 | better |
| K=2 implied vol, calibrated | HMM implied vol (Gaussian K=2), calibrated | 63 | -0.001 to +0.019 | no difference | -0.005 to +0.045 | no difference |
| K=3 implied vol, calibrated | HMM implied vol (Gaussian K=2), calibrated | 63 | -0.068 to -0.009 | better | -0.124 to +0.007 | no difference |
| K=4 implied vol, calibrated | HMM implied vol (Gaussian K=2), calibrated | 63 | -0.096 to -0.027 | better | -0.138 to -0.007 | better |
| K=2 implied vol, calibrated | HAR + VIX | 63 | +0.052 to +0.153 | worse | +0.013 to +0.245 | worse |
| K=3 implied vol, calibrated | HAR + VIX | 63 | +0.025 to +0.083 | worse | -0.005 to +0.103 | no difference |
| K=4 implied vol, calibrated | HAR + VIX | 63 | +0.014 to +0.052 | worse | -0.011 to +0.080 | no difference |
| HAR + VIX + K=2 prob | HAR + VIX | 63 | -0.001 to +0.018 | no difference | -0.001 to +0.048 | no difference |
| HAR + VIX + K=3 prob | HAR + VIX | 63 | -0.013 to +0.017 | no difference | -0.004 to +0.055 | no difference |
| HAR + VIX + K=4 prob | HAR + VIX | 63 | -0.014 to +0.013 | no difference | -0.003 to +0.053 | no difference |
| HAR + VIX + K=2 expected var | HAR + VIX | 63 | -0.004 to +0.008 | no difference | -0.006 to +0.019 | no difference |
| HAR + VIX + K=3 expected var | HAR + VIX | 63 | +0.002 to +0.010 | worse | +0.005 to +0.025 | worse |
| HAR + VIX + K=4 expected var | HAR + VIX | 63 | +0.002 to +0.010 | worse | +0.003 to +0.021 | worse |
| HAR + VIX + HMM prob (Gaussian K=2) | HAR + VIX | 63 | -0.002 to +0.015 | no difference | -0.001 to +0.046 | no difference |
| K=3 implied vol, raw | K=2 implied vol, raw | 63 | -0.093 to +0.022 | no difference | -0.120 to -0.019 | better |
| K=4 implied vol, raw | K=2 implied vol, raw | 63 | -0.126 to -0.027 | better | -0.118 to -0.021 | better |
| K=2 implied vol, raw | HMM implied vol (Gaussian K=2), raw | 63 | +0.001 to +0.038 | worse | -0.010 to +0.042 | no difference |
| K=3 implied vol, raw | HMM implied vol (Gaussian K=2), raw | 63 | -0.075 to +0.047 | no difference | -0.098 to -0.007 | better |
| K=4 implied vol, raw | HMM implied vol (Gaussian K=2), raw | 63 | -0.107 to -0.007 | better | -0.103 to +0.001 | no difference |

## One line

Development data only: against the two-state Student-t forecast the three-state model is better on RMSE (-0.081 to -0.014) and no difference on QLIKE (-0.163 to +0.005); the four-state model is better (-0.109 to -0.032) and better (-0.178 to -0.011). Against HAR + VIX the three-state forecast is worse on RMSE (+0.025 to +0.083) and no difference on QLIKE (-0.005 to +0.103); the four-state worse (+0.014 to +0.052) and no difference (-0.011 to +0.080). Added to HAR + VIX, the four-state probability is no difference on RMSE (-0.014 to +0.013) and its expected variance worse (+0.002 to +0.010). The panel's priors: 'K > 2 beats the two-state model' (80 percent) is met for K = 4; 'reaches HAR + IV' (20 percent) is not met (RMSE worse, QLIKE no difference). The paper's development-period reading, that the regime model's own forecast loses to HAR + VIX and its probability adds nothing to it, does not change with the state count; a four-state Student-t model is a better regime forecaster than the two-state one and still not a better volatility forecaster than HAR + VIX. No holdout is opened on this.

