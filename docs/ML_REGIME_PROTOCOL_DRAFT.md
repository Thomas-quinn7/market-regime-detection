development data only (S&P 500, 2005-2023), no holdout, not a claim

# Protocol draft: does a flexible learner find regime information that the linear nest misses?

Status: **draft, written 2026-10-18 (stage S8 b) before any learner was fitted.** The runner commits
this file at the end of the run that wrote it; the first fit happens in a later run, at or after that
commit. Any change after the commit is made only by a dated amendment at the bottom, written before
the run it affects, never by editing the text above it. Source: the S8 stage of
`/opt/hmm-agent/HMM_REOPEN_SCOPE.md` (rule 8 amended for S8 only, Thomas, 2026-10-18 13:00 Irish) and
`/opt/hmm-agent/reviews/HMM_S8_PLAN_2026-10-18.md` section 3a.

## What this is and is not

The question: is the paper's claim B ("the regime probability adds nothing once the VIX is in") an
artefact of the linear nest? A tree ensemble or a neural net can use the HMM probability as an
interaction (for example, weight the VIX differently in the high-vol state). If a flexible learner with
the probability is no better than the same learner without it, claim B survives the referee objection
"you only tested a linear nest".

This is development work on the S&P 500 from 2005-01-01 to 2023-12-31 only (scope rule 3; the caches
on disk to 2026-10-13 are not read past 2023-12-31). Nothing here is a holdout or a claim. Nothing from
it enters a claim sentence in README.md or docs/WRITEUP.md; at most one proposal sentence in
`docs/FIXES_FOR_THOMAS_2026-10.md` names the continuation (P19). A holdout for any of it is a January
2027 decision for Thomas.

## Data and target

- S&P 500 daily returns and the VIX, VIX9D, VIX3M and VIX6M closes from the committed caches
  (`regimes.data.load_index_returns`, `load_vol_indices`), 2005-01-01 to 2023-12-31, on the dates where
  the S&P return and the VIX both exist. A download attempt raises.
- Target: log of realised vol over the next h days, `log(regimes.forecast.forward_vol(returns, h))`,
  h in {5, 21, 63} for every learner and also h = 126 for the linear and tree learners (ridge, LASSO,
  random forest, LightGBM). Forecasts are scored in levels: `exp(prediction + s^2 / 2)`, with `s^2` the
  variance of the chosen configuration's residuals on the validation block (below); for the OLS
  benchmark it is the training residual variance, exactly as `regimes.forecast.walk_forward_regression`.

## Feature sets (nested)

- **F0** = log HAR inputs (`har_features`: |r_t|, RMS of the last 5 and 22 returns; clipped at 1e-3
  before the log, as the VIX script does) + log(VIX / sqrt(252)).
- **F1** = F0 + the two-state walk-forward HMM high-vol probability (`regimes.evaluate.walk_forward_oos`,
  min_train 756, step 63, horizon h; filtered, never smoothed), as in S4a.
- **F1n** = F0 + a pure-noise regressor (standard normal, `numpy.random.default_rng(0)`, one value per
  day): the control. A learner that "gains" from F1n over F0 shows the size of a gain that means nothing.
- **F2** = F0 + log |r| at lags 1 to 21 (lag 0 is already in F0) + log RMS of the last 44 and 66 returns
  + log(VIX9D / VIX), log(VIX3M / VIX), log(VIX6M / VIX). A richer set without a regime model, to see
  whether "more information" does what "regime" does not.

Rows. Tables (i) and (ii) use the rows where F1's inputs exist (the HMM probability starts after its
756-row warm-up, about 2008), and every learner and feature set at a horizon is fitted on exactly those
rows, so none trains on more history than another (desk finding 6). Table (iii) uses the rows where F2
exists (VIX9D starts 2011-01-03) and refits F0 on those rows for the comparison.

## Learners (fixed; nothing else in this protocol)

Every learner is fitted to the log target. Scalers (mean and standard deviation per feature) are fitted
on the training rows only and applied forward.

| learner | fixed settings | grid (chosen inside each training window) |
|---|---|---|
| OLS (the benchmark, = HAR + VIX on F0) | `walk_forward_regression`, log target | none |
| ridge | standardised features, intercept | alpha in {0.01, 0.1, 1, 10, 100} |
| LASSO | standardised features, intercept, max_iter 10000 | alpha in {0.0001, 0.001, 0.01, 0.1} |
| random forest | 300 trees, bootstrap, random_state 0, n_jobs 4 for fitting and 1 for prediction (sklearn's threaded prediction adds the trees in a run-dependent order) | max_depth in {4, 8}, min_samples_leaf in {25, 100} |
| LightGBM | learning_rate 0.05, subsample 1.0, colsample_bytree 1.0, deterministic=True, force_row_wise=True, num_threads 4, seed 0 | num_leaves in {7, 15}, n_estimators in {100, 300}, min_child_samples in {25, 100} |
| MLP | two hidden layers (32, 16), ReLU, Adam (learning rate 0.001), batch 64, seed 0, standardised features; early stopping on the validation block (patience 20 epochs, at most 300 epochs) | L2 penalty in {0.0001, 0.01} |

## Walk-forward

As the paper: the first refit after 756 rows, refit every 63 rows, forecasts for the next 63 rows from
each refit, and the training rows embargoed by h (a target is used only once it is fully known: rows
`[: i - h]` at refit position i, as `walk_forward_regression`).

Hyperparameters are chosen only inside the training window, by rolling-origin validation on its last
252 rows: at each refit, each grid point is fitted on the training rows before the validation block
(themselves embargoed by h from it) and scored by mean squared error of the log target on the 252
validation rows; the grid point with the lowest error is refitted on the whole training window and used
for the next 63 rows. Ties go to the first grid point in the order written above. For the MLP the
validation block also sets the number of epochs (the best epoch's count is reused for the refit on the
whole window).

Determinism: fixed seeds as above, fixed thread counts (`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`,
`MKL_NUM_THREADS` and LightGBM's `num_threads` set to 4 in the script before any import), and the run
must reproduce byte for byte on pc-lanes: the script is run twice and the saved forecast files compared
with `cmp`; a difference is reported, not explained away.

## Scoring (all post hoc, development data)

- RMSE on vol and QLIKE on variance (`regimes.forecast.qlike`) on the scored days.
- Paired circular block bootstrap, block max(63, h), 2,000 draws, seed 0 (`regimes.posthoc.paired_interval`),
  read as in the paper: "better" if the interval is wholly below zero, "worse" if wholly above, else
  "no difference".
- HAC Diebold-Mariano, Bartlett lag 20 (`regimes.posthoc.hac_dm`), beside each interval.
- A model confidence set at 10% over all learner-feature pairs per horizon (`regimes.posthoc.mcs`).
- The count of non-overlapping windows (scored days / h) beside every interval.

## Decisive tables, and how they will be read (written first)

1. **Every learner, F1 vs F0, with F1n vs F0 beside it.** If F1 is "better" than F0 for some learner on
   a loss at a horizon while F1n is not, that is a development finding against "claim B is only a
   linear-nest result" for that learner, loss and horizon, and it is reported as such, with the noise
   row beside it and the number of comparisons made (6 learners x 2 losses x 3 or 4 horizons). If F1 is
   "no difference" or "worse" everywhere, claim B survives the objection on development data. Either
   way, nothing becomes a claim.
2. **Every learner on F0 vs OLS on F0 (HAR + VIX).** Does the learner itself beat the linear benchmark?
3. **F2 vs F0 per learner,** on the F2 rows.

No other comparison is decisive. Any further table (for example the MCS) is descriptive.

## Files

`src/regimes/learners.py` (the learners with fixed seeds, the in-window validation and the walk-forward
loop; imported by no frozen script), `examples/dev_ml_regime.py` writing `docs/DEV_ML_REGIME_2026-10.md`
(first line as this file's) and per-day forecasts under `docs/results/dev_ml_regime/`, and
`tests/test_learners.py` (determinism; an embargo perturbation test as in `tests/test_audit.py`: rewriting
every target not yet known at a refit date moves no forecast; F1n within noise of F0 on a synthetic
series). Installs: scikit-learn, lightgbm, torch (CPU wheel, for the S8 c race), ruptures (S8 d) inside
`.venv` only, pinned in `requirements-ml.txt`, installed with `requirements-lock.txt` as a constraint so
that no package the holdouts use changes version; the reproduction identity (vix_early at least) is
rerun after the install.

## Amendments

### A1, 2026-10-18 (before any fit): the best-forecaster race, stage S8 c

Written in the same run as the draft, before any learner was fitted to the S&P 500, and committed with
it. Adds two recurrent learners and the race scoring; nothing above changes.

- **LSTM and GRU** (PyTorch, CPU wheel pinned in `requirements-ml.txt`): one recurrent layer, then a
  linear output; input = the last 66 days of the feature set (standardised on the training rows), output
  = the log target. Adam, learning rate 0.001, batch 64, at most 200 epochs, early stopping with
  patience 20 on the same validation block as the other learners (the last 252 training rows, embargoed
  by h); the best epoch's count is reused for the refit on the whole window. Grid: hidden size in {8, 16}
  x weight decay in {0, 0.0001}. Determinism: `torch.manual_seed(0)`,
  `torch.use_deterministic_algorithms(True)`, `torch.set_num_threads(4)`, a seeded data-loader generator.
  Horizons 5, 21 and 63 (not 126), feature sets F0, F1 and F1n.
- No further learner is added: none was justified from a reference the lane verified, so none is named.
- **Scoring of the race** (`examples/dev_ml_race.py` -> `docs/DEV_ML_RACE_2026-10.md`): every learner and
  feature set of S8 b plus the two recurrent learners, on the F1 rows; RMSE and QLIKE; each against OLS on
  F0 (HAR + VIX) with the paired interval and HAC DM; a model confidence set at 10% over everything, per
  horizon, on each loss (post hoc, descriptive).
- **By volatility tercile:** at each refit the 33rd and 67th percentiles of the VIX over the training
  rows split the next 63 scored days into low, middle and high; losses and the interval against HAR +
  VIX are reported per tercile.
- **Known limit, stated first in the output:** one series, about 3,200 scored days at 21 days (about 150
  non-overlapping windows), so a gain over HAR + VIX is expected to be small and concentrated in the
  high-vol tercile; a race won by a few tenths of a percent of RMSE is a description of this sample.

### A2, 2026-10-18 (before any fit): alternative regime detectors, stage S8 d

Written and committed with the draft, before any detector was fitted to the S&P 500. The code is
`src/regimes/detectors.py` (tests in `tests/test_detectors.py`, synthetic data only).

- **Inputs** (`rolling_features`): log RMS returns over 5 and 22 days and log(VIX / sqrt(252)), causal.
- **Detectors**, each fitted on the training rows only, refit every 63 rows after 756, applied forward
  without smoothing: k-means with k = 2 and 3 (10 initialisations, seed 0); a Gaussian mixture with 2 and
  3 full-covariance components (5 initialisations, seed 0); PELT change-point detection on log 22-day RMS
  returns (`ruptures`, L2 cost, penalty 10, minimum segment 10 days) run on the 252 days ending at each
  day, flagging whether the current segment's mean is above the training median; spectral clustering
  (2 clusters, 15-nearest-neighbour affinity, the last 1,500 training rows, seed 0), with new days
  assigned to the nearest training centroid. Features are standardised on the training rows.
- **Regime input:** for k-means and spectral clustering a 0/1 flag for the cluster with the highest
  mean 22-day RMS return; for the mixture the posterior probability of that component; for PELT the
  0/1 flag. It replaces the HMM probability in F1 (F1[d] = F0 + the detector's input).
- **Models:** OLS at h = 5, 21 and 63, and, at h = 21 only, the learner with the lowest mean QLIKE on F0
  at h = 21 in the S8 b and c tables (chosen from those tables before any detector is fitted, named in
  the output). Each against F0 with the paired interval, beside the HMM's F1 and the noise F1n.
- **Descriptives:** label persistence (share of days with yesterday's label) and the adjusted Rand
  index against the HMM's labels (high-vol probability above 0.5), on the scored days.
- Output: `examples/dev_regime_detectors.py` -> `docs/DEV_REGIME_DETECTORS_2026-10.md`. Causality test:
  a shock at day t moves no detector output before t (`tests/test_detectors.py`).
