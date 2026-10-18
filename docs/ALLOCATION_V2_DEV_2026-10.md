development data only, no holdout

# Regime overlays on multi-asset benchmarks, development half (2007-2017), October 2026

Class of every table in this file: **development data only (ETF universe, downloads ending 2017-12-31; walk-forward HMM on SPY), no holdout; the 2018-2026 split is not run**. Written by `examples/allocation_v2_dev.py` at a53cbf5 plus uncommitted files, 2026-10-18T06:28:19+00:00. This is the development half of the plan in `/opt/hmm-agent/reviews/ALLOCATION_V2_PLAN_2026-10-17.md`; the draft protocol for the unopened 2018-2026 half is `docs/ALLOCATION_V2_PROTOCOL_DRAFT.md`. Nothing here is a claim; the numbers are the development evidence the protocol's expectations rest on. Source: desk, trader section 4 and the editor view that the allocation section be demoted or rebuilt as an allocation study; ALLOCATION_V2_PLAN section 2.

## 1. Design

- Data: Yahoo adjusted closes of SPY, EFA, EEM, IEF, TLT, TIP, LQD, HYG, GLD, DBC, VNQ, BIL, downloads 2000-01-01 to 2017-12-31 (`data/<ticker>_2000-01-01_2017-12-31.csv`); scored window 2007-07-13 to 2017-12-29 (2637 days, 10.5 years), the first day on which every ETF, every signal and every benchmark target exists. BIL (cash, and the Sharpe ratio's risk-free leg) starts 2007-05-30.
- Execution: signals use closes up to t-1 and are filled at the close of t (`execution_lag=2` in `regimes.allocation.drift_backtest`); portfolios drift between trades; costs per leg of turnover at 5 and 10 bps; no leverage. Decisions are taken on the first day, at every month end (benchmark rebalance) and, for an overlay, on every day its state changes.
- Benchmarks: static 60/40 (SPY/IEF); 1/N over the 11 risky ETFs; inverse 63-day-vol weights over the 11 (no leverage, weights sum to one); the 60/40 scaled to a 10 percent EWMA vol target with the remainder in BIL (scale read at month ends); a 50/30/20 tilt (SPY 50, IEF 30, GLD/DBC/VNQ equal 20).
- Overlays (equity action: SPY, EFA and EEM weights to BIL while the state is on; bond action: IEF and TLT weights half to GLD, half to BIL): HMM high-vol probability >= 0.5 from `regimes.evaluate.walk_forward_oos(min_train=756, step=63)` on SPY log returns from 2000 (60 refits, 0 skipped, 60 converged, first out-of-sample day 2003-01-09); trailing 21-day vol >= 20 percent annualised; EWMA (0.94) vol >= 20 percent; financial turbulence (`regimes.turbulence.financial_turbulence`, causal 504-day window) on the panel SPY, EFA, EEM, IEF, TLT, LQD above the 90th percentile of all its values strictly before t (the plan's rule; and a 21-day mean of turbulence against the same threshold, added because the daily rule whipsaws); the stock-bond action when the trailing 63-day SPY/IEF correlation is above zero.
- Statistics: paired circular block bootstrap (63-day blocks, 2000 draws, seed 0, the same blocks for every column) of the annualised Sharpe ratio over BIL (`block_bootstrap_sharpe`) and of the maximum drawdown of the resampled path (`block_bootstrap_drawdown`; the drawdown of a reordered path, so a statement about the return distribution and its clustering, not about the one realised path).

## 2. Signals on the window

| signal | share of days on | changes / yr |
|---|---|---|
| HMM prob >= 0.5 | 28.3% | 10.6 |
| 21d vol > 20% | 22.8% | 4.9 |
| EWMA vol > 20% | 22.5% | 4.3 |
| turbulence > wf p90 | 9.8% | 29.7 |
| turbulence 21d mean > wf p90 | 8.2% | 3.0 |
| stock-bond corr63 > 0 | 6.3% | 1.5 |

## 3. Every benchmark with every overlay, 5 bps per leg

`dSharpe` and `dMaxDD` are overlay minus benchmark (a positive `dMaxDD` is a shallower drawdown); the intervals are the paired bootstrap 95 percent intervals of the same differences.

| benchmark | overlay | ann ret | ann vol | Sharpe | max DD | Calmar | turnover / yr | dSharpe vs benchmark | dMaxDD vs benchmark (pp) | dSharpe 95% | dMaxDD 95% (pp) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 60/40 SPY/IEF | none | 7.2% | 10.9% | 0.65 | -32% | 0.23 | 0.26 | +0.00 | +0.0 |  |  |
| 60/40 SPY/IEF | HMM prob >= 0.5 | 5.5% | 6.1% | 0.84 | -11% | 0.48 | 12.78 | +0.19 | +20.9 | -0.51 to +0.84 | -3.0 to +28.1 |
| 60/40 SPY/IEF | 21d vol > 20% | 5.8% | 6.6% | 0.83 | -14% | 0.43 | 5.91 | +0.18 | +18.6 | -0.39 to +0.70 | -2.1 to +27.4 |
| 60/40 SPY/IEF | EWMA vol > 20% | 5.8% | 6.6% | 0.84 | -13% | 0.45 | 5.22 | +0.18 | +19.2 | -0.38 to +0.71 | -2.4 to +27.8 |
| 60/40 SPY/IEF | turbulence > wf p90 | 6.1% | 9.0% | 0.65 | -25% | 0.24 | 36.03 | -0.00 | +7.0 | -0.38 to +0.27 | -4.7 to +15.0 |
| 60/40 SPY/IEF | turbulence 21d mean > wf p90 | 7.5% | 8.7% | 0.82 | -25% | 0.30 | 3.67 | +0.17 | +7.3 | -0.20 to +0.58 | -5.2 to +20.6 |
| 60/40 SPY/IEF | stock-bond corr63 > 0 | 7.2% | 10.9% | 0.65 | -32% | 0.22 | 1.41 | -0.00 | -0.0 | -0.05 to +0.04 | -0.5 to +0.9 |
| 1/N (11 ETFs) | none | 5.4% | 10.8% | 0.50 | -33% | 0.17 | 0.35 | +0.00 | +0.0 |  |  |
| 1/N (11 ETFs) | HMM prob >= 0.5 | 4.7% | 7.3% | 0.61 | -18% | 0.26 | 6.07 | +0.11 | +14.8 | -0.21 to +0.35 | -0.5 to +20.3 |
| 1/N (11 ETFs) | 21d vol > 20% | 4.7% | 7.5% | 0.58 | -22% | 0.21 | 2.94 | +0.08 | +11.0 | -0.16 to +0.28 | -0.5 to +17.4 |
| 1/N (11 ETFs) | EWMA vol > 20% | 4.8% | 7.6% | 0.60 | -21% | 0.22 | 2.62 | +0.10 | +11.5 | -0.14 to +0.29 | -0.4 to +17.8 |
| 1/N (11 ETFs) | turbulence > wf p90 | 5.2% | 9.5% | 0.53 | -27% | 0.19 | 16.75 | +0.03 | +5.8 | -0.15 to +0.16 | -1.7 to +8.2 |
| 1/N (11 ETFs) | turbulence 21d mean > wf p90 | 5.4% | 9.2% | 0.57 | -27% | 0.20 | 1.92 | +0.07 | +5.4 | -0.11 to +0.23 | -2.1 to +13.3 |
| 1/N (11 ETFs) | stock-bond corr63 > 0 | 5.5% | 10.8% | 0.51 | -33% | 0.17 | 0.87 | +0.01 | -0.0 | -0.01 to +0.04 | -0.3 to +1.2 |
| inverse-vol (11 ETFs, 63d) | none | 5.5% | 6.5% | 0.78 | -20% | 0.27 | 0.97 | +0.00 | +0.0 |  |  |
| inverse-vol (11 ETFs, 63d) | HMM prob >= 0.5 | 5.1% | 5.5% | 0.85 | -13% | 0.40 | 4.06 | +0.07 | +7.7 | -0.19 to +0.28 | -1.0 to +10.4 |
| inverse-vol (11 ETFs, 63d) | 21d vol > 20% | 5.1% | 5.6% | 0.84 | -15% | 0.34 | 2.34 | +0.06 | +5.4 | -0.14 to +0.23 | -0.7 to +8.6 |
| inverse-vol (11 ETFs, 63d) | EWMA vol > 20% | 5.2% | 5.6% | 0.85 | -15% | 0.35 | 2.22 | +0.07 | +5.7 | -0.13 to +0.23 | -0.7 to +8.9 |
| inverse-vol (11 ETFs, 63d) | turbulence > wf p90 | 5.3% | 6.0% | 0.81 | -16% | 0.33 | 10.32 | +0.03 | +4.2 | -0.14 to +0.16 | -1.0 to +5.1 |
| inverse-vol (11 ETFs, 63d) | turbulence 21d mean > wf p90 | 5.5% | 6.0% | 0.84 | -17% | 0.33 | 1.80 | +0.06 | +3.8 | -0.09 to +0.21 | -0.9 to +6.2 |
| inverse-vol (11 ETFs, 63d) | stock-bond corr63 > 0 | 5.6% | 6.5% | 0.79 | -20% | 0.27 | 1.56 | +0.01 | +0.0 | -0.03 to +0.06 | -0.3 to +1.3 |
| vol-target 60/40 at 10% | none | 7.2% | 8.1% | 0.84 | -20% | 0.36 | 1.26 | +0.00 | +0.0 |  |  |
| vol-target 60/40 at 10% | HMM prob >= 0.5 | 5.2% | 5.9% | 0.83 | -11% | 0.46 | 12.60 | -0.00 | +8.7 | -0.53 to +0.53 | -5.3 to +13.7 |
| vol-target 60/40 at 10% | 21d vol > 20% | 5.3% | 6.4% | 0.78 | -14% | 0.37 | 6.15 | -0.06 | +5.6 | -0.42 to +0.31 | -4.9 to +10.6 |
| vol-target 60/40 at 10% | EWMA vol > 20% | 5.4% | 6.4% | 0.79 | -13% | 0.42 | 5.60 | -0.04 | +7.4 | -0.40 to +0.32 | -5.2 to +11.2 |
| vol-target 60/40 at 10% | turbulence > wf p90 | 5.4% | 7.0% | 0.73 | -18% | 0.30 | 31.57 | -0.11 | +1.7 | -0.44 to +0.18 | -6.1 to +7.2 |
| vol-target 60/40 at 10% | turbulence 21d mean > wf p90 | 6.5% | 7.4% | 0.83 | -19% | 0.34 | 4.07 | -0.01 | +0.8 | -0.24 to +0.24 | -6.3 to +7.4 |
| vol-target 60/40 at 10% | stock-bond corr63 > 0 | 7.2% | 8.1% | 0.83 | -20% | 0.36 | 2.40 | -0.00 | +0.0 | -0.07 to +0.05 | -0.5 to +1.1 |
| 50/30/20 real-asset tilt | none | 6.7% | 11.8% | 0.57 | -35% | 0.20 | 0.30 | +0.00 | +0.0 |  |  |
| 50/30/20 real-asset tilt | HMM prob >= 0.5 | 5.4% | 6.7% | 0.76 | -12% | 0.45 | 10.78 | +0.18 | +22.4 | -0.32 to +0.59 | -0.6 to +30.2 |
| 50/30/20 real-asset tilt | 21d vol > 20% | 5.7% | 7.2% | 0.75 | -16% | 0.36 | 5.04 | +0.18 | +18.6 | -0.23 to +0.51 | -1.0 to +27.8 |
| 50/30/20 real-asset tilt | EWMA vol > 20% | 5.7% | 7.2% | 0.75 | -15% | 0.38 | 4.47 | +0.18 | +19.3 | -0.22 to +0.51 | -0.9 to +28.0 |
| 50/30/20 real-asset tilt | turbulence > wf p90 | 5.8% | 9.9% | 0.57 | -26% | 0.22 | 30.19 | -0.00 | +8.4 | -0.29 to +0.19 | -3.5 to +12.6 |
| 50/30/20 real-asset tilt | turbulence 21d mean > wf p90 | 7.0% | 9.6% | 0.71 | -26% | 0.27 | 3.16 | +0.14 | +8.2 | -0.14 to +0.42 | -4.0 to +21.7 |
| 50/30/20 real-asset tilt | stock-bond corr63 > 0 | 6.7% | 11.9% | 0.57 | -35% | 0.19 | 1.17 | -0.00 | +0.0 | -0.04 to +0.03 | -0.5 to +0.7 |

## 4. The same at 10 bps per leg

| benchmark | overlay | ann ret | ann vol | Sharpe | max DD | Calmar | turnover / yr | dSharpe vs benchmark | dMaxDD vs benchmark (pp) |
|---|---|---|---|---|---|---|---|---|---|
| 60/40 SPY/IEF | none | 7.2% | 10.9% | 0.65 | -32% | 0.22 | 0.26 | +0.00 | +0.0 |
| 60/40 SPY/IEF | HMM prob >= 0.5 | 4.8% | 6.1% | 0.74 | -12% | 0.40 | 12.78 | +0.08 | +20.3 |
| 60/40 SPY/IEF | 21d vol > 20% | 5.5% | 6.6% | 0.79 | -14% | 0.38 | 5.91 | +0.13 | +17.9 |
| 60/40 SPY/IEF | EWMA vol > 20% | 5.6% | 6.6% | 0.80 | -14% | 0.41 | 5.22 | +0.15 | +18.6 |
| 60/40 SPY/IEF | turbulence > wf p90 | 4.2% | 9.0% | 0.45 | -31% | 0.13 | 36.03 | -0.20 | +1.1 |
| 60/40 SPY/IEF | turbulence 21d mean > wf p90 | 7.3% | 8.7% | 0.80 | -26% | 0.28 | 3.67 | +0.15 | +6.4 |
| 60/40 SPY/IEF | stock-bond corr63 > 0 | 7.1% | 10.9% | 0.64 | -32% | 0.22 | 1.41 | -0.01 | -0.0 |
| 1/N (11 ETFs) | none | 5.4% | 10.8% | 0.50 | -33% | 0.16 | 0.35 | +0.00 | +0.0 |
| 1/N (11 ETFs) | HMM prob >= 0.5 | 4.4% | 7.3% | 0.56 | -18% | 0.24 | 6.07 | +0.07 | +14.7 |
| 1/N (11 ETFs) | 21d vol > 20% | 4.5% | 7.5% | 0.56 | -22% | 0.21 | 2.94 | +0.07 | +10.8 |
| 1/N (11 ETFs) | EWMA vol > 20% | 4.6% | 7.6% | 0.58 | -21% | 0.22 | 2.62 | +0.08 | +11.4 |
| 1/N (11 ETFs) | turbulence > wf p90 | 4.3% | 9.5% | 0.44 | -28% | 0.16 | 16.75 | -0.05 | +5.1 |
| 1/N (11 ETFs) | turbulence 21d mean > wf p90 | 5.3% | 9.2% | 0.56 | -27% | 0.19 | 1.92 | +0.07 | +5.4 |
| 1/N (11 ETFs) | stock-bond corr63 > 0 | 5.5% | 10.8% | 0.51 | -33% | 0.17 | 0.87 | +0.01 | -0.0 |
| inverse-vol (11 ETFs, 63d) | none | 5.5% | 6.5% | 0.77 | -20% | 0.27 | 0.97 | +0.00 | +0.0 |
| inverse-vol (11 ETFs, 63d) | HMM prob >= 0.5 | 4.9% | 5.5% | 0.81 | -13% | 0.38 | 4.06 | +0.04 | +7.7 |
| inverse-vol (11 ETFs, 63d) | 21d vol > 20% | 5.0% | 5.6% | 0.82 | -15% | 0.33 | 2.34 | +0.05 | +5.3 |
| inverse-vol (11 ETFs, 63d) | EWMA vol > 20% | 5.0% | 5.6% | 0.83 | -15% | 0.34 | 2.22 | +0.06 | +5.6 |
| inverse-vol (11 ETFs, 63d) | turbulence > wf p90 | 4.8% | 6.0% | 0.73 | -17% | 0.28 | 10.32 | -0.04 | +3.8 |
| inverse-vol (11 ETFs, 63d) | turbulence 21d mean > wf p90 | 5.4% | 6.0% | 0.83 | -17% | 0.32 | 1.80 | +0.05 | +3.8 |
| inverse-vol (11 ETFs, 63d) | stock-bond corr63 > 0 | 5.5% | 6.5% | 0.78 | -20% | 0.27 | 1.56 | +0.01 | +0.0 |
| vol-target 60/40 at 10% | none | 7.1% | 8.1% | 0.83 | -20% | 0.35 | 1.26 | +0.00 | +0.0 |
| vol-target 60/40 at 10% | HMM prob >= 0.5 | 4.6% | 5.9% | 0.73 | -12% | 0.38 | 12.60 | -0.10 | +8.4 |
| vol-target 60/40 at 10% | 21d vol > 20% | 5.0% | 6.4% | 0.73 | -15% | 0.32 | 6.15 | -0.10 | +4.8 |
| vol-target 60/40 at 10% | EWMA vol > 20% | 5.1% | 6.4% | 0.75 | -13% | 0.38 | 5.60 | -0.08 | +6.9 |
| vol-target 60/40 at 10% | turbulence > wf p90 | 3.8% | 7.0% | 0.50 | -24% | 0.16 | 31.57 | -0.33 | -3.4 |
| vol-target 60/40 at 10% | turbulence 21d mean > wf p90 | 6.3% | 7.4% | 0.80 | -20% | 0.31 | 4.07 | -0.03 | -0.2 |
| vol-target 60/40 at 10% | stock-bond corr63 > 0 | 7.0% | 8.1% | 0.82 | -20% | 0.35 | 2.40 | -0.01 | +0.0 |
| 50/30/20 real-asset tilt | none | 6.7% | 11.8% | 0.57 | -35% | 0.19 | 0.30 | +0.00 | +0.0 |
| 50/30/20 real-asset tilt | HMM prob >= 0.5 | 4.8% | 6.7% | 0.68 | -13% | 0.38 | 10.78 | +0.10 | +21.9 |
| 50/30/20 real-asset tilt | 21d vol > 20% | 5.4% | 7.2% | 0.71 | -17% | 0.33 | 5.04 | +0.14 | +18.0 |
| 50/30/20 real-asset tilt | EWMA vol > 20% | 5.5% | 7.2% | 0.72 | -16% | 0.34 | 4.47 | +0.15 | +18.5 |
| 50/30/20 real-asset tilt | turbulence > wf p90 | 4.2% | 10.0% | 0.42 | -31% | 0.14 | 30.19 | -0.15 | +3.5 |
| 50/30/20 real-asset tilt | turbulence 21d mean > wf p90 | 6.9% | 9.6% | 0.70 | -27% | 0.26 | 3.16 | +0.12 | +7.7 |
| 50/30/20 real-asset tilt | stock-bond corr63 > 0 | 6.7% | 11.9% | 0.57 | -35% | 0.19 | 1.17 | -0.01 | -0.0 |

## 5. HMM overlay against the trailing-vol overlay (the shape of claim C3), 5 bps

| benchmark | Sharpe HMM | Sharpe 21d vol | dSharpe 95% | max DD HMM | max DD 21d vol | dMaxDD 95% (pp) |
|---|---|---|---|---|---|---|
| 60/40 SPY/IEF | 0.84 | 0.83 | -0.36 to +0.43 | -11% | -14% | -5.4 to +7.3 |
| 1/N (11 ETFs) | 0.61 | 0.58 | -0.15 to +0.22 | -18% | -22% | -2.1 to +6.1 |
| inverse-vol (11 ETFs, 63d) | 0.85 | 0.84 | -0.12 to +0.14 | -13% | -15% | -1.0 to +3.0 |
| vol-target 60/40 at 10% | 0.83 | 0.78 | -0.32 to +0.47 | -11% | -14% | -4.4 to +8.2 |
| 50/30/20 real-asset tilt | 0.76 | 0.75 | -0.27 to +0.32 | -12% | -16% | -3.3 to +7.8 |

## 6. The plan's claims C1-C3 read on development data

A prior for the protocol, not a verdict: C1 (an overlay improves the Sharpe ratio after costs and lag) counts benchmarks where the Sharpe interval is wholly above zero / wholly below; C2 (an overlay cuts the maximum drawdown by at least 5 points on every benchmark) counts benchmarks with a 5-point cut in the point estimate, and benchmarks where the drawdown-difference interval is wholly in the overlay's favour / against it; C3 is section 5. C4 (the correlation flag on 2018-2026) cannot be read here.

| overlay | C1 Sharpe: better / worse (of 5) | C2 drawdown cut >= 5 pp (point, of 5) | C2 drawdown interval: better / worse (of 5) |
|---|---|---|---|
| HMM prob >= 0.5 | 0 / 0 | 5 | 0 / 0 |
| 21d vol > 20% | 0 / 0 | 5 | 0 / 0 |
| EWMA vol > 20% | 0 / 0 | 5 | 0 / 0 |
| turbulence > wf p90 | 0 / 0 | 3 | 0 / 0 |
| turbulence 21d mean > wf p90 | 0 / 0 | 3 | 0 / 0 |
| stock-bond corr63 > 0 | 0 / 0 | 0 | 0 / 0 |

## Files

`docs/results/allocation_v2_dev/`: `hmm_prob_spy_2017.csv` and `hmm_signal.json` (the walk-forward signal), `signals.csv` (every overlay state on the window), `strategy_returns.csv` (daily net returns of every benchmark, overlay and cost level), and one CSV per table above.
