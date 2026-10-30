# Matched sizing test, tier 1: HMM switch against a banded vol target on spent data (written before running)

Status: written and committed on 2026-10-30 before any number in this file's result section was computed.
Class: **spent data, exploratory**. Every window used here has been seen by the author and by earlier code
(the S&P 500 2008-2023 allocation table, the spent 2024-2026 holdout). Nothing here is a holdout result and
nothing here is a claim about untouched data; tier 2 (untouched non-US indices, frozen protocol, run once)
is the only test that can be.

## 1. Why

A comment on the October 2026 post (Julien Riposo, 2026-10-29) pointed out that the allocation table
compares rules at different exposure and turnover. On development data the HMM switch traded about 31
a year against 8 for the EWMA vol target, and the two held different average equity weights, so "the
HMM rule's Sharpe is behind simple vol targeting" is a raw comparison. His proposed test: a vol target
that keeps the position unchanged inside a no-trade band, calibrated with the regime rule to similar
exposure and turnover on training data, then compared on realised vol and tail losses with identical
delayed fills and costs. The question is whether the latent state adds anything beyond a simple
persistence rule.

## 2. Assets, execution, costs

- SPY (equity) and BIL (cash), Yahoo adjusted closes, the cached files `data/SPY_2005-01-01_2023-12-31.csv`
  and `data/BIL_2005-01-01_2023-12-31.csv`. Simple daily returns.
- A signal from the close of t-2 is filled at the close of t-1 and earns the day-t return, one close after
  it could first be computed: `regimes.allocation.backtest(execution_lag=2)`.
- Costs per leg of turnover: 5 bps primary, 10 bps secondary. No leverage, no shorting.
- Weights are held fixed between trades (the `backtest` convention, the same as the published table for
  every arm). This ignores drift between trades for both arms alike.

## 3. Arms

- **H(k), HMM switch with k-day confirmation.** Signal: the cached walk-forward high-vol probability
  `docs/results/allocation_lag/hmm_prob_spy.csv` (`walk_forward_oos(min_train=756, step=63)` on SPY,
  64 refits, the signal of `docs/ALLOCATION_LAG_2026-10.md`). The state moves to the other side only once
  the probability has been on the other side of 0.5 for k consecutive closes. Equity weight 0 in the
  high state, 1 otherwise. k = 1 is the published rule. Grid k = 1, 2, ..., 63.
- **V(s, b), banded vol target.** Target weight w* = min(1, s / sigma), sigma = `ewma_vol` (alpha 0.06) of
  SPY log returns, annualised, in percent. Held weight: the first value is w*; afterwards trade to w* only
  when |w* - held| > b, otherwise keep the held weight. Grid s = 4.00 to 20.00 percent in steps of 0.25,
  b = 0.000 to 0.500 in steps of 0.005.
- **Unmatched references**, reported beside the matched pairs and not used for any reading: H(1), V(10, 0)
  (the published vol target), the 21-day realised vol > 20 percent switch, static 100 percent SPY.

## 4. Calibration rule (2008-01-07 to 2017-12-29, lag 2)

Turnover per year = sum of daily turnover (`regimes.allocation.turnover`, lag 2) divided by the number of
years (days / 252). Exposure = mean effective equity weight. Three turnover budgets B = 4, 8 and 16 a year.
For each B:

1. k_B = the k whose calibration turnover is closest to B (ties: smaller k). E_B = the calibration
   exposure of H(k_B).
2. For every s, b(s) = the b whose calibration turnover of V(s, b) is closest to B (ties: smaller b).
3. s_B = the s whose calibration exposure of V(s, b(s)) is closest to E_B (ties: smaller s).

A budget that an arm cannot reach is recorded as such and the closest value is used. The calibrated knobs
are written to the result section before the score window is computed.

## 5. Score windows and metrics

- **Primary window:** 2018-01-02 to 2023-12-29, the cached data, positions carried over from 2017 (no reset).
- **Secondary window:** the spent holdout, 2024-01-02 to the latest close available on the run date, from a
  fresh download of SPY and BIL from 2005-01-01 with the walk-forward signal recomputed on it (same call).
  Knobs from section 4, not refitted. If the download fails, the window is recorded as not run.
- **Primary metric:** 1 percent daily expected shortfall, ES = minus the mean of the worst ceil(0.01 n) daily
  net returns (a positive loss). The reading is the ES gain of the HMM, ES(V) - ES(H), so positive favours
  the HMM. Paired circular block bootstrap, 63-day blocks, 2,000 draws, seed 0, the same blocks for both
  arms; 95 percent percentile interval.
- **Secondary, reported without reading:** annualised vol, worst 21-day compounded return, max drawdown,
  Sharpe over BIL, realised turnover per year and mean exposure in the score window (to show whether the
  calibration match held out of sample), all at 5 and 10 bps.

## 6. Reading and prediction, fixed now

- The HMM adds something beyond persistence, in this exploratory tier, only if on the primary window at
  two or more of the three budgets the ES gain is positive with its 95 percent interval above zero.
- Otherwise: no evidence on spent data that the latent state adds anything once exposure and turnover are
  matched. Tier 2 then needs a separate decision on whether it is worth spending untouched data on.
- Prediction: no budget shows an interval above zero. Basis: the write-up finds the two-state probability
  behaves like a squashed EWMA vol, pinned near 0 or 1.

## 7. Simulation check (no market data)

The two simulated markets of `examples/why_hmm_loses.py` (continuous AR(1) log vol; true two-state vol),
seeds 1, 2, 3, 4, 7, 5,000 days each, simulated percent log returns as the equity leg, zero-return cash.
The same walk-forward HMM (`min_train=756, step=63`), budget B = 8 only, the section 4 rule calibrated on
the first half of the out-of-sample days and scored on the second half, lag 2, 5 bps. Reported: the ES gain
per seed. Prediction: the gain is not positive in most continuous seeds and is positive in most two-state
seeds. If the HMM does not gain in the two-state market either, a tier 2 run is unlikely to be worth it.

## 8. What would change this file

Nothing in sections 2 to 7 is edited after the first number is computed. A mistake found later is fixed
by an appended note that gives both the original and the corrected result.

## Results

Appended 2026-10-30 after the run, by `examples/matched_sizing.py`. Tables: `docs/results/matched_sizing/`
(`calibration.csv`, `scores.csv`, `es_gain.csv`, `run_log.txt`). Spent data, exploratory, as section 0 says.

### Calibration (2008-01-07 to 2017-12-29)

| budget / yr | HMM k | HMM turnover | HMM exposure | VT s (%) | VT band | VT turnover | VT exposure |
|---|---|---|---|---|---|---|---|
| 4 | 5 | 4.21 | 0.760 | 11.25 | 0.050 | 4.00 | 0.762 |
| 8 | 3 | 7.42 | 0.753 | 10.75 | 0.000 | 7.32 | 0.755 |
| 16 | 2 | 13.04 | 0.749 | 10.50 | 0.000 | 7.62 | 0.745 |

Budget 16 is not reachable for the vol target (with no band it trades about 7.6 a year here), and budget 8
is reached only approximately by both arms (k = 2 gives 13.0 and k = 3 gives 7.4). Exposure matched to
within 0.004 at every budget.

### Primary window, 2018-01-02 to 2023-12-29 (1,509 days, 5 bps; 10 bps within 0.0001 of these)

ES gain = ES(VT) - ES(HMM), daily 1 percent expected shortfall, positive favours the HMM.

| budget | ES HMM | ES VT | ES gain | 95% interval | HMM turnover | VT turnover | HMM exposure | VT exposure |
|---|---|---|---|---|---|---|---|---|
| 4 | 3.40% | 2.69% | -0.71 pp | -1.15 to -0.30 | 12.0 | 5.1 | 0.67 | 0.72 |
| 8 | 3.10% | 2.63% | -0.47 pp | -0.71 to -0.19 | 17.4 | 8.0 | 0.67 | 0.71 |
| 16 | 2.89% | 2.60% | -0.29 pp | -0.55 to -0.08 | 22.0 | 8.1 | 0.67 | 0.70 |

Reading (section 6): the HMM does not add anything here; at all three budgets the interval is below zero,
so on this window the banded vol target had the smaller tail loss. The prediction (no interval above zero)
held, and the result goes further than predicted. Secondary metrics, without reading: max drawdown and
Sharpe favour the vol target at every budget; the worst 21-day loss favours the HMM (for example -9.6
against -13.7 percent at budget 4), which fits a binary rule that is fully out during a long slide and
fully in on the first days of a shock. The calibration match did not hold out of sample: the HMM traded
two to three times its calibrated turnover in 2018-2023 while the vol target stayed near its own, and the
HMM held slightly less equity, so neither a higher exposure nor costs explain its larger tail loss.

### Secondary window, the spent holdout, 2024-01-02 to 2026-10-29 (710 days, 5 bps)

Fresh Yahoo download of SPY and BIL from 2005-01-01 on 2026-10-30 (`data/SPY_2005-01-01_2026-10-30.csv`,
`data/BIL_2005-01-01_2026-10-30.csv`), walk-forward signal recomputed on it, knobs from the calibration above.

| budget | ES gain | 95% interval | HMM turnover | VT turnover | HMM exposure | VT exposure |
|---|---|---|---|---|---|---|
| 4 | +0.10 pp | -0.29 to +0.66 | 7.1 | 5.2 | 0.89 | 0.84 |
| 8 | +0.22 pp | -0.27 to +0.94 | 11.4 | 9.3 | 0.88 | 0.83 |
| 16 | +0.18 pp | -0.30 to +0.89 | 15.6 | 9.8 | 0.87 | 0.81 |

Point estimates lean to the HMM, every interval spans zero. 710 days put only 8 days in the worst 1 percent,
so this window cannot separate the arms.

### Simulation check: incomplete

The run was stopped by Claude Code on 2026-10-30 at about 20:25 because the laptop ran low on memory, after
four of the ten simulated markets. Completed, all continuous (no regimes), budget 8, 5 bps:

| seed | ES gain | 95% interval |
|---|---|---|
| 1 | -1.07 pp | -1.30 to -0.85 |
| 2 | -1.01 pp | -1.29 to -0.70 |
| 3 | -0.68 pp | -0.81 to -0.53 |
| 4 | -0.59 pp | -0.84 to -0.32 |

Continuous seed 7 and all five two-state seeds were not run. The two-state half is the part that says
whether the HMM can win at all when its model is true, so the section 7 reading is not available yet.
The run takes about 4.5 minutes per market; rerun with `python examples/matched_sizing.py --skip-download`
on a machine with free memory (results then replace `run_log.txt`).
