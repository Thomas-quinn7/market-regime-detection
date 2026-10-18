# Draft protocol: regime overlays on multi-asset benchmarks, 2018 to 2026 (NOT RUN, NOT FROZEN)

Status: a draft for Thomas's decision, written in stage S5 of the October 2026 reopen from
`/opt/hmm-agent/reviews/ALLOCATION_V2_PLAN_2026-10-17.md` and the development results in
`docs/ALLOCATION_V2_DEV_2026-10.md`. Nothing past 2017-12-31 has been downloaded or opened for this study.
The trading plan's 31 January 2027 gate governs whether the holdout half is ever run; this file does not
open it. If it is run, this text is frozen first (committed and pushed before any download whose end date
is after 2017-12-31), with the result section appended afterwards, as the other protocols were.

## 1. Execution rule (first, because the published allocation table did not state one)

Signals are computed from closing prices up to the close of t-1 and filled at the close of t
(`execution_lag=2` in `regimes.allocation.drift_backtest`). Portfolios drift between trades. Static
benchmarks are rebalanced at the close of the last trading day of each month. Costs are charged per leg
of turnover at 5 basis points (primary) and 10 basis points (secondary). No leverage, no shorting, no
intraday data. The first position is established without charge.

## 2. Question

Does a regime overlay improve a modern multi-asset allocation after costs and with the execution rule
above, by more than a plain volatility rule does?

## 3. Data

Yahoo Finance adjusted closes of SPY, EFA, EEM, IEF, TLT, TIP, LQD, HYG, GLD, DBC, VNQ and BIL.
Development: downloads ending 2017-12-31 (`data/<ticker>_2000-01-01_2017-12-31.csv`, in `data/MANIFEST.md`).
Holdout: one download per ticker from 2000-01-01 to the freeze date, made after this file is frozen;
scored from 2018-01-02. The holdout period has already happened and was unseen by the code, not by the
author; the protocol says so wherever the result is reported.

## 4. Benchmarks (five)

1. Static 60/40, SPY/IEF.
2. 1/N over the 11 risky ETFs.
3. Inverse 63-day-vol weights over the 11 risky ETFs, weights summing to one.
4. The 60/40 scaled to a 10 percent EWMA (0.94) volatility target, remainder in BIL, scale read at month ends.
5. A 50/30/20 tilt: SPY 50, IEF 30, GLD, DBC and VNQ 20 in equal parts.

## 5. Overlays (five; the sixth below is a development addition)

Equity action: SPY, EFA and EEM weights move to BIL while the state is on. Bond action: IEF and TLT
weights move half to GLD and half to BIL. Decisions are taken on the first day, at every month end and on
every day the state changes.

1. HMM high-vol probability >= 0.5 from `regimes.evaluate.walk_forward_oos(min_train=756, step=63)` on SPY
   log returns from 2000-01-03 (equity action). The walk-forward is refit every 63 days on an expanding
   window, as in the paper.
2. Trailing 21-day realised vol of SPY >= 20 percent annualised (equity action).
3. EWMA (0.94) vol of SPY >= 20 percent annualised (equity action).
4. Financial turbulence (`regimes.turbulence.financial_turbulence`, causal, 504-day window) on SPY, EFA,
   EEM, IEF, TLT and LQD above the 90th percentile of all its values strictly before t (equity action).
5. Trailing 63-day SPY/IEF correlation above zero (bond action).
6. Development addition, registered here so that it is not a post-hoc choice: the 21-day mean of
   turbulence against the same threshold (equity action). On development data the daily rule changed
   state about 30 times a year and the mean rule 3 times.

## 6. Claims, written before the holdout is opened, with the development reading beside each

Smallest effects of interest, fixed in advance: Sharpe ratio +0.10; maximum drawdown 5 points. Statistic:
paired circular block bootstrap, 63-day blocks, 2,000 draws, seed 0, the same blocks for every strategy
(`regimes.allocation.block_bootstrap_sharpe`, `block_bootstrap_drawdown`); a difference is shown when its
95 percent interval excludes zero. Verdict rule per claim, as the cross-index protocol: "holds" when the
claim's direction is shown on at least two benchmarks and the opposite on none; "not shown" when no
benchmark shows it; "mixed" otherwise.

- C1. An overlay improves the Sharpe ratio of a benchmark after costs and lag. Expected: not shown.
  Development (2007-2017, 5 bps): no overlay's Sharpe interval excludes zero on any benchmark (0 of 5
  better, 0 of 5 worse, every overlay).
- C2. An overlay cuts the maximum drawdown by at least 5 points on every benchmark. Expected: holds on the
  point estimate, not shown on the interval. Development: the HMM, 21-day vol and EWMA overlays cut the
  point drawdown by 5 to 22 points on all five benchmarks; the turbulence rules on three; the correlation
  flag on none; every drawdown-difference interval spans zero.
- C3. The HMM overlay is not better than the trailing-vol overlay on Sharpe or drawdown. Expected: holds.
  Development: HMM minus 21-day vol Sharpe intervals span zero on all five benchmarks (-0.36 to +0.47 at
  the widest); drawdown intervals span zero on all five; the HMM's point drawdown is 2 to 4 points
  shallower with about twice the turnover.
- C4. The correlation flag improves the 60/40 on 2018-2026. Expected: open. Development: the flag was on
  6 percent of days and changed nothing (Sharpe interval -0.05 to +0.04). This is the only claim with a
  "60/40 is dead" story in it and the only one the development data cannot read.

Every claim is scored on the primary cost (5 bps) and reported at 10 bps beside it; a verdict that
changes between the two is reported as such and not averaged.

## 7. What is reported

For every benchmark and overlay at both costs: annual return, annual vol, Sharpe over BIL, maximum
drawdown, Calmar, turnover a year, and the paired intervals against the benchmark. The HMM against the
trailing-vol overlay per benchmark (C3). The signal shares and change counts on the window. Per-day
weights and net returns saved under `docs/results/allocation_v2_holdout/`. Convergence counts of the HMM
walk-forward refits.

## 8. What is not allowed after the freeze

No new benchmark, overlay, threshold, window, cost level or statistic. No change to the execution rule.
No re-run after seeing the result. A bug found after the run is reported with the run, and the fixed
re-run is labelled a reproduction of the protocol, not a second test.

## 9. Honest prior

Regime overlays on multi-asset portfolios behave like vol targeting on development data: drawdown falls,
Sharpe does not move measurably, and the HMM does not beat the trailing-vol control. The development
period (2007-2017) contains 2008 and 2011; the holdout contains 2020 and 2022, the two events overlays
are for, and 2022 is the one year in which the equity-sleeve overlays had no bond sleeve to hide in.
Expect C2 and C3 to hold, C1 not shown, C4 open.
