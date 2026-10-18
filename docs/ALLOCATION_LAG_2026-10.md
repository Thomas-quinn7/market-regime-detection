development data only, no holdout

# Execution lag, cost drag and a rebalanced 60/40 for the allocation table, October 2026

Class of every table in this file: **development data only (SPY, IEF, BIL 2005-2023; walk-forward HMM signal on the S&P 500), no holdout**. Stage S5 of the reopen scope; the published allocation table (WRITEUP section "Regime-conditional allocation", `examples/regime_allocation.py`) is development data and so is everything here; nothing is a claim and no holdout is opened. Written by `examples/allocation_lag.py` at a53cbf5 plus uncommitted files, 2026-10-18T06:23:46+00:00; walk-forward signal `regimes.evaluate.walk_forward_oos(min_train=756, step=63)` on SPY log returns, 64 refits, 0 skipped, 64 converged, 19.7 s. Bootstrap: paired circular block bootstrap of annualised Sharpe ratios over BIL (`regimes.allocation.block_bootstrap_sharpe`, 63-day blocks, 2000 draws, seed 0), the same blocks for every column, so every difference below is paired. Source of the items: desk, trader section 4 (allocation.py:104 execution at the signal close, HIGH; cost drag never stated, MEDIUM; 60/40 daily-rebalanced at zero cost, LOW); desk synthesis finding 4.

## 1. What execution lag means here

`regimes.allocation.backtest` now takes `execution_lag` (default 1, the published rule, so every published number reproduces). With lag 1 the position earning the day-t return is the one the signal chose at the close of t-1: the backtest is filled at the same close that produced the signal, which a real book cannot do with a signal computed from closing prices. With lag 2 the signal from the close of t-2 is filled at the close of t-1 and earns close(t-1) to close(t): one full day later. The gap between the two is the execution-timing cost; the desk measured it for the trailing-vol rule and asked for the HMM switch, which needed the walk-forward run.

## 2. The published table reproduced (lag 1, 5 bps per leg)

Window 2008-01-08 to 2023-12-29 (4023 days), the window of the WRITEUP table (every strategy restricted to the days the walk-forward signal exists). These rows should equal the WRITEUP allocation table at its printed precision; `examples/regime_allocation.py` prints the same numbers.

| strategy | ann ret | ann vol | Sharpe | max DD | Calmar |
|---|---|---|---|---|---|
| Regime switch equity/cash | 7.7% | 10.9% | 0.66 | -15% | 0.51 |
| Regime switch equity/bonds | 8.5% | 12.0% | 0.67 | -17% | 0.51 |
| 21d vol > 20% equity/cash | 9.1% | 11.6% | 0.74 | -18% | 0.51 |
| EWMA vol > 20% equity/cash | 6.7% | 11.6% | 0.55 | -20% | 0.33 |
| EWMA vol target 10% | 7.0% | 10.0% | 0.65 | -19% | 0.37 |
| Static 100% equity | 10.0% | 20.4% | 0.53 | -51% | 0.19 |
| Static 60/40 equity/bonds | 7.8% | 11.6% | 0.64 | -31% | 0.25 |

One rounding note: the WRITEUP and README print the static-equity maximum drawdown as -52 percent; the script prints -51.5 percent to one decimal and the exact value is -51.4814%, which rounds to -51 percent. The hand rounding of a rounded print is the only difference.

## 3. One more day of execution lag, every rule

Window 2008-01-09 to 2023-12-29 (4022 days: the published window less its first day, so that lag 1 and lag 2 are scored on the same days). L1 = published rule, L2 = one more day. The interval is the paired bootstrap 95 percent interval for Sharpe(L2) - Sharpe(L1); the static benchmarks hold constant weights, so the lag cannot change them.

| strategy | ann ret L1 | ann ret L2 | Sharpe L1 | Sharpe L2 | Sharpe L2 - L1 | 95% interval of the change | max DD L1 | max DD L2 | Calmar L2 |
|---|---|---|---|---|---|---|---|---|---|
| Regime switch equity/cash | 7.7% | 5.1% | 0.66 | 0.44 | -0.23 | -0.49 to +0.03 | -15% | -26% | 0.20 |
| Regime switch equity/bonds | 8.5% | 5.9% | 0.67 | 0.48 | -0.20 | -0.48 to +0.09 | -17% | -27% | 0.22 |
| 21d vol > 20% equity/cash | 9.2% | 7.1% | 0.75 | 0.58 | -0.17 | -0.27 to -0.08 | -18% | -23% | 0.30 |
| EWMA vol > 20% equity/cash | 6.8% | 7.1% | 0.56 | 0.59 | +0.02 | -0.06 to +0.12 | -20% | -19% | 0.37 |
| EWMA vol target 10% | 7.1% | 7.0% | 0.66 | 0.64 | -0.02 | -0.05 to +0.01 | -19% | -18% | 0.38 |
| Static 100% equity | 10.1% | 10.1% | 0.54 | 0.54 | +0.00 | +0.00 to +0.00 | -51% | -51% | 0.20 |
| Static 60/40 equity/bonds | 7.9% | 7.9% | 0.64 | 0.64 | +0.00 | +0.00 to +0.00 | -31% | -31% | 0.26 |

Sharpe intervals at lag 2, in the shape of the WRITEUP bootstrap table, plus each strategy against the monthly-rebalanced 60/40 of section 5 (5 bps):

| strategy | Sharpe L2 | Sharpe 95% interval (L2) | minus Regime switch equity/cash (L2) | minus 60/40 monthly, 5 bps |
|---|---|---|---|---|
| Regime switch equity/cash | 0.44 | -0.06 to +0.94 |  | -0.67 to +0.27 |
| Regime switch equity/bonds | 0.48 | -0.02 to +0.98 | -0.13 to +0.23 | -0.69 to +0.40 |
| 21d vol > 20% equity/cash | 0.58 | +0.12 to +1.04 | -0.14 to +0.41 | -0.49 to +0.36 |
| EWMA vol > 20% equity/cash | 0.59 | +0.13 to +1.07 | -0.14 to +0.43 | -0.45 to +0.37 |
| EWMA vol target 10% | 0.64 | +0.22 to +1.07 | -0.12 to +0.50 | -0.28 to +0.27 |
| Static 100% equity | 0.54 | +0.13 to +1.04 | -0.36 to +0.56 | -0.22 to +0.04 |
| Static 60/40 equity/bonds | 0.64 | +0.23 to +1.17 | -0.25 to +0.68 | +0.00 to +0.03 |

## 4. Cost drag from realised turnover

Turnover is the sum of absolute weight changes on the day they are traded (a full equity-to-cash switch is turnover 2.0, so 10 bps at 5 bps per leg). Drag = annual turnover times the per-leg cost. `give-up vs equity` is the static 100 percent equity annual return less the rule's at 5 bps; `of which gross` is the same difference at zero cost, so the remainder is brokerage. Same window as section 3; a rule's turnover can differ by one switch between the lags when a trade falls on the window's first day at one lag and inside the window at the other. The vol-target rule trades a little every day, so its switch-day count is the day count.

| strategy | lag | turnover / yr | switch days / yr | drag 5 bps (pp/yr) | drag 10 bps (pp/yr) | ann ret 0 bps | ann ret 5 bps | ann ret 10 bps | Sharpe 10 bps | max DD 10 bps | give-up vs equity, 5 bps (pp/yr) | of which gross (pp/yr) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Regime switch equity/cash | 1 | 30.95 | 15.5 | 1.55 | 3.10 | 9.4% | 7.7% | 6.1% | 0.52 | -16% | +2.40 | +0.72 |
| Regime switch equity/cash | 2 | 30.95 | 15.5 | 1.55 | 3.10 | 6.7% | 5.1% | 3.4% | 0.29 | -30% | +5.06 | +3.42 |
| Regime switch equity/bonds | 1 | 30.95 | 15.5 | 1.55 | 3.10 | 10.1% | 8.5% | 6.8% | 0.54 | -21% | +1.67 | -0.02 |
| Regime switch equity/bonds | 2 | 30.95 | 15.5 | 1.55 | 3.10 | 7.6% | 5.9% | 4.3% | 0.35 | -31% | +4.21 | +2.56 |
| 21d vol > 20% equity/cash | 1 | 10.53 | 5.3 | 0.53 | 1.05 | 9.8% | 9.2% | 8.6% | 0.70 | -19% | +0.94 | +0.36 |
| 21d vol > 20% equity/cash | 2 | 10.53 | 5.3 | 0.53 | 1.05 | 7.6% | 7.1% | 6.5% | 0.53 | -25% | +3.06 | +2.49 |
| EWMA vol > 20% equity/cash | 1 | 9.77 | 4.9 | 0.49 | 0.98 | 7.4% | 6.8% | 6.3% | 0.52 | -21% | +3.28 | +2.76 |
| EWMA vol > 20% equity/cash | 2 | 9.90 | 4.9 | 0.49 | 0.99 | 7.7% | 7.1% | 6.6% | 0.54 | -20% | +3.00 | +2.47 |
| EWMA vol target 10% | 1 | 8.15 | 204.6 | 0.41 | 0.81 | 7.5% | 7.1% | 6.6% | 0.61 | -19% | +3.04 | +2.61 |
| EWMA vol target 10% | 2 | 8.15 | 204.6 | 0.41 | 0.81 | 7.4% | 7.0% | 6.5% | 0.60 | -19% | +3.17 | +2.73 |
| Static 100% equity | 1 | 0.00 | 0.0 | 0.00 | 0.00 | 10.1% | 10.1% | 10.1% | 0.54 | -51% | +0.00 | +0.00 |
| Static 100% equity | 2 | 0.00 | 0.0 | 0.00 | 0.00 | 10.1% | 10.1% | 10.1% | 0.54 | -51% | +0.00 | +0.00 |
| Static 60/40 equity/bonds | 1 | 0.00 | 0.0 | 0.00 | 0.00 | 7.9% | 7.9% | 7.9% | 0.64 | -31% | +2.26 | +2.26 |
| Static 60/40 equity/bonds | 2 | 0.00 | 0.0 | 0.00 | 0.00 | 7.9% | 7.9% | 7.9% | 0.64 | -31% | +2.26 | +2.26 |

## 5. The 60/40 benchmark, charged its rebalance

The published 60/40 holds constant weights every day, which is a daily rebalance that trades nothing and pays nothing. `regimes.allocation.rebalanced_backtest` lets the weights drift with returns and resets them to 60/40 at the close of the last trading day of each month, paying the per-leg cost on the turnover of each reset. Same window as section 3.

| benchmark | ann ret | ann vol | Sharpe | max DD | Calmar | turnover / yr |
|---|---|---|---|---|---|---|
| Static 60/40, daily rebalance, zero turnover (published) | 7.9% | 11.6% | 0.64 | -31% | 0.26 | 0.000 |
| 60/40 drifting, rebalanced at month end, 0 bps | 7.6% | 11.3% | 0.63 | -32% | 0.24 | 0.229 |
| 60/40 drifting, rebalanced at month end, 5 bps | 7.6% | 11.3% | 0.63 | -32% | 0.24 | 0.229 |
| 60/40 drifting, rebalanced at month end, 10 bps | 7.6% | 11.3% | 0.63 | -32% | 0.24 | 0.229 |

## 6. Trailing-vol threshold grid at both lags

The WRITEUP grid (15, 20, 25 percent) with the lag-2 column beside it; the HMM row is the regime switch. Same window as section 3; `days in cash` is the share of days the rule holds cash.

| rule | days in cash | Sharpe L1 | max DD L1 | Sharpe L2 | max DD L2 |
|---|---|---|---|---|---|
| 21d vol > 15% | 44% | 0.63 | -12% | 0.58 | -22% |
| 21d vol > 20% | 24% | 0.75 | -18% | 0.58 | -23% |
| 21d vol > 25% | 14% | 0.72 | -25% | 0.76 | -24% |
| EWMA vol > 15% | 44% | 0.61 | -15% | 0.57 | -21% |
| EWMA vol > 20% | 24% | 0.56 | -20% | 0.59 | -19% |
| EWMA vol > 25% | 13% | 0.68 | -21% | 0.75 | -23% |
| HMM prob >= 0.5 | 28% | 0.66 | -15% | 0.44 | -26% |

## 7. Desk checks on the development forecasts (Mincer-Zarnowitz, variance-swap sign)

Class of every table in this section: **development data only (S&P 500 2005-2023, the VIX script's dev period); not a holdout, not a reproduction**. Forecasts saved by `examples/dev_forecast_desk.py` (git a53cbf5, 2026-10-18T06:14:15+00:00, 40.0 s), which runs the frozen `examples/vol_forecast_vix.py --period dev` unchanged; tables computed by the same script at a53cbf5 plus uncommitted files. Scored days: 3226, 2011-02-04 to 2023-11-29 (the days every forecast exists on, as in the WRITEUP development column). Source of the items: desk, trader section 2 ([A2], [A4]) and section 4.

### Mincer-Zarnowitz: realised 21-day vol on each forecast (daily percent)

OLS `realised = a + b * forecast` on the scored days; HAC (Bartlett, lag 20) standard error of the slope; `p (a=0, b=1)` is the joint Wald test. The top-decile columns refit the line on the 10 percent of days with the highest forecast. Calibrated rows are the walk-forward log-linear forecasts the paper scores; raw rows are the signals before calibration (the raw VIX carries the variance risk premium).

| forecast | n | intercept | slope | HAC se (slope) | R2 | p (a=0, b=1) | top-decile slope | top-decile mean forecast | top-decile mean realised |
|---|---|---|---|---|---|---|---|---|---|
| HAR (calibrated) | 3226 | 0.092 | 0.883 | 0.119 | 0.316 | 0.615 | 0.94 | 1.80 | 1.75 |
| VIX (calibrated) | 3226 | 0.039 | 0.941 | 0.104 | 0.385 | 0.823 | 0.97 | 1.85 | 1.80 |
| HAR + VIX (calibrated) | 3226 | 0.050 | 0.929 | 0.101 | 0.389 | 0.772 | 1.00 | 1.86 | 1.80 |
| HAR + HMM prob (calibrated) | 3226 | 0.097 | 0.849 | 0.122 | 0.319 | 0.278 | 1.23 | 1.91 | 1.76 |
| HAR + VIX + HMM prob (calibrated) | 3226 | 0.101 | 0.879 | 0.109 | 0.381 | 0.529 | 1.11 | 1.94 | 1.79 |
| HAR + VIX + VIX-HMM prob (calibrated) | 3226 | 0.083 | 0.893 | 0.097 | 0.383 | 0.547 | 0.93 | 1.90 | 1.79 |
| HMM implied vol (calibrated) | 3226 | 0.058 | 0.819 | 0.112 | 0.175 | 0.003 | 1.23 | 1.72 | 1.38 |
| VIX-HMM implied vol (calibrated) | 3226 | 0.271 | 0.601 | 0.141 | 0.074 | 0.000 | -0.79 | 1.60 | 1.15 |
| EWMA vol (0.94) (calibrated) | 3226 | 0.139 | 0.835 | 0.116 | 0.298 | 0.352 | 0.72 | 1.85 | 1.76 |
| trailing 21-day vol (calibrated) | 3226 | 0.128 | 0.843 | 0.119 | 0.271 | 0.411 | 0.86 | 1.78 | 1.66 |
| HMM high-vol probability (calibrated) | 3226 | 0.136 | 0.781 | 0.125 | 0.242 | 0.053 | -0.47 | 1.91 | 1.70 |
| VIX (raw) | 3226 | -0.039 | 0.843 | 0.095 | 0.389 | 0.000 | 0.92 | 2.16 | 1.80 |
| HMM implied vol (raw) | 3226 | -0.060 | 0.855 | 0.115 | 0.218 | 0.000 | 1.08 | 1.89 | 1.42 |
| VIX-HMM implied vol (raw) | 3226 | 0.183 | 0.647 | 0.088 | 0.180 | 0.000 | 0.83 | 1.80 | 1.28 |
| EWMA vol (0.94) (raw) | 3226 | 0.370 | 0.590 | 0.091 | 0.299 | 0.000 | 0.42 | 2.21 | 1.76 |
| trailing 21-day vol (raw) | 3226 | 0.445 | 0.523 | 0.089 | 0.273 | 0.000 | 0.37 | 2.23 | 1.68 |

### Variance-swap sign test against the raw VIX strike

Strike = raw VIX squared in daily-percent units; payoff to the long side = realised^2 - strike; the forecast is long when its own variance is above the strike. `mean_pnl` and `hit_rate` are for trading the forecast's sign; `short_*` for always-short (the variance risk premium); `long_days_*` describe the payoff to the long side on the days the forecast is long; `p_vs_short` is the HAC-DM (lag 20) p-value of the forecast's P&L against always-short, blank when the forecast is never long (its P&L is then always-short's exactly). Units are daily variance (percent squared).

All 3226 scored days (overlapping 21-day targets):

| forecast | n | share_long | mean_pnl | hit_rate | short_mean_pnl | short_hit_rate | long_days_mean_payoff | long_days_hit_rate | p_vs_short |
|---|---|---|---|---|---|---|---|---|---|
| HAR (calibrated) | 3226 | 0.146 | +0.1787 | 0.730 | +0.2901 | 0.830 | -0.381 | 0.159 | 0.000 |
| VIX (calibrated) | 3226 | 0.000 | +0.2901 | 0.830 | +0.2901 | 0.830 |  |  |  |
| HAR + VIX (calibrated) | 3226 | 0.000 | +0.2901 | 0.830 | +0.2901 | 0.830 |  |  |  |
| HAR + HMM prob (calibrated) | 3226 | 0.170 | +0.1855 | 0.734 | +0.2901 | 0.830 | -0.309 | 0.218 | 0.006 |
| HAR + VIX + HMM prob (calibrated) | 3226 | 0.007 | +0.2800 | 0.825 | +0.2901 | 0.830 | -0.680 | 0.167 | 0.091 |
| HAR + VIX + VIX-HMM prob (calibrated) | 3226 | 0.013 | +0.2799 | 0.821 | +0.2901 | 0.830 | -0.403 | 0.122 | 0.188 |
| HMM implied vol (calibrated) | 3226 | 0.444 | +0.0551 | 0.526 | +0.2901 | 0.830 | -0.265 | 0.157 | 0.000 |
| VIX-HMM implied vol (calibrated) | 3226 | 0.475 | +0.0614 | 0.501 | +0.2901 | 0.830 | -0.241 | 0.154 | 0.001 |
| EWMA vol (0.94) (calibrated) | 3226 | 0.131 | +0.1452 | 0.732 | +0.2901 | 0.830 | -0.551 | 0.125 | 0.002 |
| trailing 21-day vol (calibrated) | 3226 | 0.172 | +0.1957 | 0.703 | +0.2901 | 0.830 | -0.274 | 0.131 | 0.076 |
| HMM implied vol (raw) | 3226 | 0.587 | +0.0779 | 0.468 | +0.2901 | 0.830 | -0.181 | 0.192 | 0.052 |
| VIX-HMM implied vol (raw) | 3226 | 0.502 | -0.0243 | 0.519 | +0.2901 | 0.830 | -0.313 | 0.190 | 0.000 |
| EWMA vol (0.94) (raw) | 3226 | 0.148 | +0.1014 | 0.741 | +0.2901 | 0.830 | -0.638 | 0.197 | 0.014 |
| trailing 21-day vol (raw) | 3226 | 0.159 | +0.0877 | 0.728 | +0.2901 | 0.830 | -0.637 | 0.179 | 0.008 |
| always short | 3226 | 0.000 | +0.2901 | 0.830 | +0.2901 | 0.830 |  |  |  |

Every 21st scored day (154 non-overlapping windows):

| forecast | n | share_long | mean_pnl | hit_rate | short_mean_pnl | short_hit_rate | long_days_mean_payoff | long_days_hit_rate | p_vs_short |
|---|---|---|---|---|---|---|---|---|---|
| HAR (calibrated) | 154 | 0.149 | +0.2994 | 0.740 | +0.3747 | 0.825 | -0.252 | 0.217 | 0.180 |
| VIX (calibrated) | 154 | 0.000 | +0.3747 | 0.825 | +0.3747 | 0.825 |  |  |  |
| HAR + VIX (calibrated) | 154 | 0.000 | +0.3747 | 0.825 | +0.3747 | 0.825 |  |  |  |
| HAR + HMM prob (calibrated) | 154 | 0.195 | +0.2559 | 0.721 | +0.3747 | 0.825 | -0.305 | 0.233 | 0.053 |
| HAR + VIX + HMM prob (calibrated) | 154 | 0.006 | +0.3648 | 0.818 | +0.3747 | 0.825 | -0.760 | 0.000 | 0.282 |
| HAR + VIX + VIX-HMM prob (calibrated) | 154 | 0.013 | +0.3836 | 0.825 | +0.3747 | 0.825 | +0.343 | 0.500 | 0.429 |
| HMM implied vol (calibrated) | 154 | 0.442 | +0.1347 | 0.526 | +0.3747 | 0.825 | -0.272 | 0.162 | 0.012 |
| VIX-HMM implied vol (calibrated) | 154 | 0.461 | +0.1164 | 0.506 | +0.3747 | 0.825 | -0.280 | 0.155 | 0.011 |
| EWMA vol (0.94) (calibrated) | 154 | 0.130 | +0.2351 | 0.734 | +0.3747 | 0.825 | -0.537 | 0.150 | 0.005 |
| trailing 21-day vol (calibrated) | 154 | 0.162 | +0.2557 | 0.714 | +0.3747 | 0.825 | -0.367 | 0.160 | 0.011 |
| HMM implied vol (raw) | 154 | 0.610 | +0.0162 | 0.448 | +0.3747 | 0.825 | -0.294 | 0.191 | 0.000 |
| VIX-HMM implied vol (raw) | 154 | 0.487 | +0.0464 | 0.519 | +0.3747 | 0.825 | -0.337 | 0.187 | 0.001 |
| EWMA vol (0.94) (raw) | 154 | 0.149 | +0.1956 | 0.727 | +0.3747 | 0.825 | -0.600 | 0.174 | 0.001 |
| trailing 21-day vol (raw) | 154 | 0.143 | +0.1865 | 0.708 | +0.3747 | 0.825 | -0.659 | 0.091 | 0.000 |
| always short | 154 | 0.000 | +0.3747 | 0.825 | +0.3747 | 0.825 |  |  |  |

## Files

`docs/results/allocation_lag/`: `hmm_prob_spy.csv` (the walk-forward signal), `strategy_returns_lag1.csv` and `strategy_returns_lag2.csv` (daily net returns, 5 bps), `benchmark_60_40_monthly.csv`, and one CSV per table above. `docs/results/dev_vix_forecasts/`: the development forecasts and the desk tables.
