# Data quality of the spent holdouts, October 2026

Every table in this file is headed with its class: **reproduction** (facts read from the committed data caches and the reproduced forecasts), **post hoc, from the reproduced forecasts** (the registered claim intervals recomputed with the affected scored days removed; the forecasts are the frozen ones), or **post hoc what-if, OLS re-estimation** (the OLS-only models re-estimated on the Dow with one input changed). Nothing here is a registered test and nothing changes a registered verdict; the registered verdicts are the RMSE verdicts in `docs/results/cross_index_holdout_2026-10-14.txt` and the VIX tables in `docs/WRITEUP.md`. None of these items was screened before the holdouts ran.

Written by `examples/data_quality.py` at 8e454ec plus uncommitted files, 2026-10-17 22:10Z, with 2,000 bootstrap draws (seed 0). Inputs: `data/*_rv_5min.csv`, `data/fred_*.csv`, the Yahoo price caches named in `data/MANIFEST.md`, and `docs/results/reproductions/cross_index/` and `vix_early/`. Items are the data-engineer desk report's F2 (VXD prints), F3 (partial YM sessions), F4 (2014 no-bar days and short targets), F10 (half days), the back-calculated VIX note and the two-target-definitions note (desk, data-engineer, 2026-10-17). Blast radius means: the published number is recomputed without, or with a corrected version of, the affected days, and the difference is shown.

## 1. Suspect VXD prints (Dow implied vol, FRED VXDCLS)

Class: reproduction (read from the committed data caches and the reproduced forecasts).

| date | VXD | previous | next | log IV jump vs previous | scored day | HAR-RV + IV forecast | HAR-RV forecast | target |
|---|---|---|---|---|---|---|---|---|
| 2021-07-13 | 2.71 | 14.86 | 15.51 | -1.702 | yes | 0.222 | 0.564 | 0.475 |
| 2024-03-21 | 22.91 | 10.81 | 10.91 | +0.751 | yes | 0.706 | 0.561 | 0.610 |
| 2025-10-16 | 36.60 | 18.60 | 17.97 | +0.677 | yes | 1.030 | 0.777 | 0.624 |

VXD 0.1 percent quantile over 2000-2026: 9.39; the series' minimum apart from 2021-07-13 is 7.58. The day-to-day spread of log VXD (median absolute change) is 0.035. No loader screens implied vol for bad prints (`src/regimes/data.py`, `examples/better_vol_models.py`); the prints enter the IV models' regressor on the day and every training set from the next quarterly refit onward.

### 1a. Blast radius, target side

Class: post hoc, from the reproduced forecasts; not a registered test. The three scored days removed from the Dow.

| claim | forecast | reference | registered dRMSE | registered | without the 3 days | verdict | moved |
|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P2 | SHAR + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P3 | HAR-RV + IV + MSM | HAR-RV + IV | -0.000 to +0.003 | no difference | -0.000 to +0.003 | no difference |  |
| P4 | Combination | HAR-RV + IV | +0.000 to +0.011 | worse | +0.000 to +0.011 | worse |  |
| P5 | MSM | Two-state HMM implied vol | -0.035 to +0.008 | no difference | -0.035 to +0.008 | no difference |  |
| R1 | HAR-RV + IV | HAR-RV | -0.014 to +0.001 | no difference | -0.014 to +0.001 | no difference |  |
| R2 | HAR-RV | HAR | -0.024 to -0.006 | better | -0.024 to -0.006 | better |  |
| R3 | HAR-RV + IV + HMM prob | HAR-RV + IV | -0.000 to +0.003 | no difference | -0.000 to +0.003 | no difference |  |
| R4 | GJR-GARCH | HAR-RV + IV | +0.002 to +0.020 | worse | +0.002 to +0.020 | worse |  |

rows kept 3294 of 3297 (3 removed); per-index verdicts moved: 0 of 9; claim outcomes across the three indices: unchanged

### 1b. Blast radius, what-if

Class: post hoc what-if, OLS re-estimation on the frozen data with one change; not a registered test. The three prints are replaced by the previous day's VXD close and the five OLS-only models are re-estimated with the frozen script's regression call (`walk_forward_regression`, horizon 21, step 63, min_rows 756, log target). The HMM, GJR-GARCH and MSM models do not read implied vol and are unchanged; the claims that pair OLS models with them (P3, P4, P5, R3, R4) are covered by 1a.

Replica check (reproduction): maximum absolute difference between the re-estimated frozen-input forecasts and the saved scored columns, HAR 2.2e-16, HAR-RV 4.4e-16, HAR-RV + IV 4.4e-16, HARQ + IV 4.4e-16, SHAR + IV 4.4e-16; target 8.9e-16; common rows 4095.

rows scored: 3297 of the 3297 frozen scored days

| model | RMSE frozen, all scored days | RMSE frozen | RMSE changed | QLIKE frozen | QLIKE changed | max |forecast change| | days changed > 1e-6 |
|---|---|---|---|---|---|---|---|
| HAR | 0.3374 | 0.3374 | 0.3374 | 0.3548 | 0.3548 | 0.0000 | 0 |
| HAR-RV | 0.3224 | 0.3224 | 0.3224 | 0.3311 | 0.3311 | 0.0000 | 0 |
| HAR-RV + IV | 0.3156 | 0.3156 | 0.3156 | 0.3161 | 0.3157 | 0.3449 | 1219 |
| HARQ + IV | 0.3154 | 0.3154 | 0.3154 | 0.3162 | 0.3158 | 0.3407 | 1217 |
| SHAR + IV | 0.3156 | 0.3156 | 0.3156 | 0.3163 | 0.3158 | 0.3470 | 1218 |

| claim | forecast | reference | dRMSE frozen | verdict frozen | dRMSE changed | verdict changed | moved |
|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P2 | SHAR + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| R1 | HAR-RV + IV | HAR-RV | -0.014 to +0.001 | no difference | -0.014 to +0.001 | no difference |  |
| R2 | HAR-RV | HAR | -0.024 to -0.006 | better | -0.024 to -0.006 | better |  |

## 2. Partial YM sessions kept as full-session RV

Class: reproduction (read from the committed data caches and the reproduced forecasts). Index trading days in each scored window whose session has fewer than 75 five-minute returns and is not a half day (a half day has 45-46, a full session 78, the level-1 circuit-breaker halts of March 2020 leave 75-77; futures sessions on index holidays are not index trading days and are dropped by the loader). `daily_realised_vol` sums whatever bars exist and records `n_returns`; nothing reads `n_returns` (`src/regimes/intraday.py`). The cross-index protocol keeps degraded days that have bars.

| index | date | n_returns | rv | rv previous | rv next | index return that day (%) |
|---|---|---|---|---|---|---|
| Dow Jones Industrial Average | 2020-02-27 | 47 | 2.13 | 1.61 | 2.12 | -4.52 |
| Dow Jones Industrial Average | 2020-02-28 | 12 | 2.12 | 2.13 | 2.51 | -1.40 |
| Dow Jones Industrial Average | 2020-06-30 | 9 | 0.35 | 0.96 | 1.06 | +0.84 |

Dow scored days whose 21-day target window contains one of the three sessions: 43; scored days whose 22-day HAR-RV feature window contains one: 45; either: 87.

### 2a. Blast radius, target side

Class: post hoc, from the reproduced forecasts; not a registered test. Dow scored days whose target or HAR-RV feature window contains one of the three sessions removed.

| claim | forecast | reference | registered dRMSE | registered | without affected days | verdict | moved |
|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P2 | SHAR + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | +0.000 to +0.000 | worse | yes |
| P3 | HAR-RV + IV + MSM | HAR-RV + IV | -0.000 to +0.003 | no difference | -0.000 to +0.003 | no difference |  |
| P4 | Combination | HAR-RV + IV | +0.000 to +0.011 | worse | -0.002 to +0.008 | no difference | yes |
| P5 | MSM | Two-state HMM implied vol | -0.035 to +0.008 | no difference | -0.018 to +0.006 | no difference |  |
| R1 | HAR-RV + IV | HAR-RV | -0.014 to +0.001 | no difference | -0.008 to +0.002 | no difference |  |
| R2 | HAR-RV | HAR | -0.024 to -0.006 | better | -0.021 to -0.005 | better |  |
| R3 | HAR-RV + IV + HMM prob | HAR-RV + IV | -0.000 to +0.003 | no difference | -0.000 to +0.003 | no difference |  |
| R4 | GJR-GARCH | HAR-RV + IV | +0.002 to +0.020 | worse | +0.002 to +0.022 | worse |  |

rows kept 3210 of 3297 (87 removed); per-index verdicts moved: 2 of 9; claim outcomes across the three indices: unchanged

### 2b. Blast radius, what-if

Class: post hoc what-if, OLS re-estimation on the frozen data with one change; not a registered test. The three sessions set to missing RV (as the no-bar days are), so the target and the HAR-RV features treat them as gaps; the five OLS-only models re-estimated.

rows scored: 3291 of the 3297 frozen scored days; 6 days lose their forecast because a feature becomes missing: 2020-02-27, 2020-02-28, 2020-03-02, 2020-03-03, 2020-03-04, 2020-06-30. 'RMSE frozen' and the intervals are on the common rows; 'all scored days' is the published row set.

| model | RMSE frozen, all scored days | RMSE frozen | RMSE changed | QLIKE frozen | QLIKE changed | max |forecast change| | days changed > 1e-6 |
|---|---|---|---|---|---|---|---|
| HAR | 0.3374 | 0.3157 | 0.3191 | 0.3380 | 0.3431 | 0.0018 | 1589 |
| HAR-RV | 0.3224 | 0.3021 | 0.3056 | 0.3189 | 0.3250 | 0.0521 | 1613 |
| HAR-RV + IV | 0.3156 | 0.2966 | 0.2998 | 0.3072 | 0.3123 | 0.0802 | 1613 |
| HARQ + IV | 0.3154 | 0.2965 | 0.2997 | 0.3075 | 0.3127 | 0.0774 | 1612 |
| SHAR + IV | 0.3156 | 0.2967 | 0.2998 | 0.3074 | 0.3125 | 0.0716 | 1613 |

| claim | forecast | reference | dRMSE frozen | verdict frozen | dRMSE changed | verdict changed | moved |
|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P2 | SHAR + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| R1 | HAR-RV + IV | HAR-RV | -0.011 to +0.001 | no difference | -0.011 to +0.000 | no difference |  |
| R2 | HAR-RV | HAR | -0.022 to -0.006 | better | -0.022 to -0.006 | better |  |

## 3. Trading days with no bars, and targets on fewer than 21 sessions

Class: reproduction (read from the committed data caches and the reproduced forecasts). Index trading days (Yahoo calendar) inside the RV range with no session RV. `forward_rv` averages the available RV^2 over the next 21 sessions when at least 18 are present (`min_periods = horizon - 3`), and `har_rv` tolerates 4 of 5 and 18 of 22; so a gap inside a window shortens the window rather than dropping the day (`src/regimes/forecast.py`).

| index | RV from | no-bar trading days | dates | scored targets on fewer than 21 sessions | of which 18, 19, 20 | scored targets |
|---|---|---|---|---|---|---|
| Nasdaq-100 | 2010-06-07 | 6 | 2014-06-12, 2014-06-13, 2014-09-23, 2014-09-24, 2014-09-25, 2014-12-31 | 63 | 19, 21, 23 | 3286 |
| Dow Jones Industrial Average | 2010-06-07 | 1 | 2014-10-03 | 21 | 0, 0, 21 | 3297 |
| Russell 2000 | 2017-07-10 | 0 |  | 0 | 0, 0, 0 | 1513 |

Targets at the sample end: the last 21 scored days of each index have 0, 0, 0 short targets respectively. `forward_rv` shifts the rolling window back by the horizon, so a window that runs past the end of the series is never produced; the `min_periods` tolerance acts only on gaps inside a window (`tests/test_forecast.py`, forward_rv alignment test). The scope's phrase '18-20-day targets at sample ends' does not describe the code: the shortened targets are the ones whose window spans a 2014 gap, counted above. The desk report (data-engineer, F4) counted 66 Nasdaq-100 and 21 Dow targets; the count here, on the calendar the frozen loader uses (index trading days, no-bar days as NaN rows), is 63 and 21: the two-gap and three-gap clusters of June and September 2014 share windows, so a per-gap count of 21 overstates them.

### 3a. Blast radius, target side

Class: post hoc, from the reproduced forecasts; not a registered test. Scored days whose target window has fewer than 21 sessions removed, per index; the Russell 2000 has none.

**Nasdaq-100**

| claim | forecast | reference | registered dRMSE | registered | without short targets | verdict | moved |
|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P2 | SHAR + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P3 | HAR-RV + IV + MSM | HAR-RV + IV | -0.001 to +0.002 | no difference | -0.001 to +0.002 | no difference |  |
| P4 | Combination | HAR-RV + IV | +0.000 to +0.018 | worse | +0.001 to +0.019 | worse |  |
| P5 | MSM | Two-state HMM implied vol | -0.026 to +0.014 | no difference | -0.028 to +0.016 | no difference |  |
| R1 | HAR-RV + IV | HAR-RV | -0.018 to -0.000 | better | -0.018 to +0.000 | no difference | yes |
| R2 | HAR-RV | HAR | -0.028 to -0.008 | better | -0.028 to -0.008 | better |  |
| R3 | HAR-RV + IV + HMM prob | HAR-RV + IV | -0.009 to +0.003 | no difference | -0.009 to +0.003 | no difference |  |
| R4 | GJR-GARCH | HAR-RV + IV | +0.002 to +0.032 | worse | +0.002 to +0.032 | worse |  |

rows kept 3223 of 3286 (63 removed); per-index verdicts moved: 1 of 9; claim outcomes across the three indices: R1 mixed -> rejected

**Dow Jones Industrial Average**

| claim | forecast | reference | registered dRMSE | registered | without short targets | verdict | moved |
|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P2 | SHAR + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P3 | HAR-RV + IV + MSM | HAR-RV + IV | -0.000 to +0.003 | no difference | -0.000 to +0.004 | no difference |  |
| P4 | Combination | HAR-RV + IV | +0.000 to +0.011 | worse | +0.001 to +0.011 | worse |  |
| P5 | MSM | Two-state HMM implied vol | -0.035 to +0.008 | no difference | -0.036 to +0.008 | no difference |  |
| R1 | HAR-RV + IV | HAR-RV | -0.014 to +0.001 | no difference | -0.014 to +0.001 | no difference |  |
| R2 | HAR-RV | HAR | -0.024 to -0.006 | better | -0.024 to -0.006 | better |  |
| R3 | HAR-RV + IV + HMM prob | HAR-RV + IV | -0.000 to +0.003 | no difference | -0.000 to +0.003 | no difference |  |
| R4 | GJR-GARCH | HAR-RV + IV | +0.002 to +0.020 | worse | +0.002 to +0.020 | worse |  |

rows kept 3276 of 3297 (21 removed); per-index verdicts moved: 0 of 9; claim outcomes across the three indices: unchanged

Russell 2000: no short targets, table unchanged.

## 4. Half days

Class: reproduction (read from the committed data caches and the reproduced forecasts). Scored-window sessions with 45-46 five-minute returns (NYSE half days, futures RTH close 13:15 ET). Their RV enters the target and the HAR-RV windows unscaled, which is the usual HAR practice.

| index | half days | median RV on half days | median RV, full sessions | scored targets containing one |
|---|---|---|---|---|
| Nasdaq-100 | 28 | 0.324 | 0.737 | 560 |
| Dow Jones Industrial Average | 28 | 0.282 | 0.539 | 565 |
| Russell 2000 | 12 | 0.636 | 0.996 | 243 |

### 4a. Blast radius, target side

Class: post hoc, from the reproduced forecasts; not a registered test. Scored days whose 21-day target window contains a half day removed, per index. This removes many days, so the intervals widen for that reason too.

**Nasdaq-100**

| claim | forecast | reference | registered dRMSE | registered | without half-day windows | verdict | moved |
|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P2 | SHAR + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P3 | HAR-RV + IV + MSM | HAR-RV + IV | -0.001 to +0.002 | no difference | -0.000 to +0.002 | no difference |  |
| P4 | Combination | HAR-RV + IV | +0.000 to +0.018 | worse | +0.003 to +0.021 | worse |  |
| P5 | MSM | Two-state HMM implied vol | -0.026 to +0.014 | no difference | -0.033 to +0.014 | no difference |  |
| R1 | HAR-RV + IV | HAR-RV | -0.018 to -0.000 | better | -0.022 to -0.002 | better |  |
| R2 | HAR-RV | HAR | -0.028 to -0.008 | better | -0.030 to -0.008 | better |  |
| R3 | HAR-RV + IV + HMM prob | HAR-RV + IV | -0.009 to +0.003 | no difference | -0.009 to +0.003 | no difference |  |
| R4 | GJR-GARCH | HAR-RV + IV | +0.002 to +0.032 | worse | +0.005 to +0.039 | worse |  |

rows kept 2726 of 3286 (560 removed); per-index verdicts moved: 0 of 9; claim outcomes across the three indices: unchanged

**Dow Jones Industrial Average**

| claim | forecast | reference | registered dRMSE | registered | without half-day windows | verdict | moved |
|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.001 to +0.000 | no difference |  |
| P2 | SHAR + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P3 | HAR-RV + IV + MSM | HAR-RV + IV | -0.000 to +0.003 | no difference | -0.000 to +0.004 | no difference |  |
| P4 | Combination | HAR-RV + IV | +0.000 to +0.011 | worse | +0.001 to +0.013 | worse |  |
| P5 | MSM | Two-state HMM implied vol | -0.035 to +0.008 | no difference | -0.040 to +0.007 | no difference |  |
| R1 | HAR-RV + IV | HAR-RV | -0.014 to +0.001 | no difference | -0.015 to +0.001 | no difference |  |
| R2 | HAR-RV | HAR | -0.024 to -0.006 | better | -0.025 to -0.004 | better |  |
| R3 | HAR-RV + IV + HMM prob | HAR-RV + IV | -0.000 to +0.003 | no difference | -0.000 to +0.003 | no difference |  |
| R4 | GJR-GARCH | HAR-RV + IV | +0.002 to +0.020 | worse | +0.002 to +0.023 | worse |  |

rows kept 2732 of 3297 (565 removed); per-index verdicts moved: 0 of 9; claim outcomes across the three indices: unchanged

**Russell 2000**

| claim | forecast | reference | registered dRMSE | registered | without half-day windows | verdict | moved |
|---|---|---|---|---|---|---|---|
| P1 | HARQ + IV | HAR-RV + IV | -0.000 to +0.000 | no difference | -0.000 to +0.000 | no difference |  |
| P2 | SHAR + IV | HAR-RV + IV | -0.001 to +0.000 | no difference | -0.000 to +0.001 | no difference |  |
| P3 | HAR-RV + IV + MSM | HAR-RV + IV | -0.002 to +0.002 | no difference | -0.003 to +0.001 | no difference |  |
| P4 | Combination | HAR-RV + IV | -0.022 to +0.009 | no difference | -0.019 to +0.009 | no difference |  |
| P5 | MSM | Two-state HMM implied vol | -0.106 to -0.016 | better | -0.106 to -0.010 | better |  |
| R1 | HAR-RV + IV | HAR-RV | -0.025 to +0.010 | no difference | -0.028 to +0.005 | no difference |  |
| R2 | HAR-RV | HAR | -0.023 to +0.004 | no difference | -0.016 to +0.011 | no difference |  |
| R3 | HAR-RV + IV + HMM prob | HAR-RV + IV | -0.003 to +0.007 | no difference | -0.003 to +0.008 | no difference |  |
| R4 | GJR-GARCH | HAR-RV + IV | -0.007 to +0.052 | no difference | -0.005 to +0.063 | no difference |  |

rows kept 1270 of 1513 (243 removed); per-index verdicts moved: 0 of 9; claim outcomes across the three indices: unchanged

## 5. Implied-vol forward fills

Class: reproduction (read from the committed data caches and the reproduced forecasts). Both holdout scripts reindex the FRED implied-vol series to the asset's calendar and forward-fill up to five days. Counted here on each asset's own calendar and scored window.

| holdout | asset | FRED series | calendar days with no print | filled (within 5 days) | filled days that are scored | scored days |
|---|---|---|---|---|---|---|
| cross-index | Nasdaq-100 | VXNCLS | 275 | 2 | 0 | 3286 |
| cross-index | Dow Jones Industrial Average | VXDCLS | 0 | 0 | 0 | 3297 |
| cross-index | Russell 2000 | RVXCLS | 1005 | 2 | 0 | 1513 |
| MS-GARCH and credit | Crude oil (USO) | OVXCLS | 0 | 0 | 0 | 3604 |
| MS-GARCH and credit | Gold (GLD) | GVZCLS | 0 | 0 | 0 | 3821 |
| MS-GARCH and credit | Emerging markets (EEM) | VXEEMCLS | 0 | 0 | 0 | 3119 |
| MS-GARCH and credit | Brazil (EWZ) | VXEWZCLS | 0 | 0 | 0 | 3119 |

A filled day carries the previous print as that day's implied vol; the count of scored days on a fill is the blast radius (each is one regressor value among thousands; no verdict can move on these counts, and no exclusion table is needed).

## 6. Back-calculated VIX in the 1990-2004 holdout

Class: reproduction (read from the committed data caches and the reproduced forecasts). Cboe's new-methodology VIX is live from 2003-09-22; earlier values in the Yahoo ^VIX series are Cboe's back-calculation (the 1993-12-22 minimum matches Cboe's published record low). `docs/VIX_HOLDOUT_PROTOCOL.md` says so; the WRITEUP does not yet.

VIX file days 3783, back-calculated 3461 (91 percent); scored days 2228, of which 1927 (86 percent) are forecasts made on a back-calculated VIX (note that a forecast made before 2003-09-22 also uses the back-calculated history in its training set).

### 6a. Blast radius

Class: post hoc, from the reproduced forecasts; not a registered test. The seven registered comparisons on the back-calculated days only, and the losses on the live-VIX tail (too short for an interval).

| forecast | reference | registered dRMSE | registered | before 2003-09-22 | verdict | moved | RMSE from 2003-09-22 (n=301) |
|---|---|---|---|---|---|---|---|
| VIX | HAR | -0.054 to -0.003 | better | -0.057 to -0.002 | better |  | 0.145 vs 0.177 |
| HAR + VIX | HAR | -0.054 to -0.012 | better | -0.057 to -0.011 | better |  | 0.146 vs 0.177 |
| HAR + HMM prob | HAR | -0.004 to +0.009 | no difference | -0.004 to +0.011 | no difference |  | 0.171 vs 0.177 |
| HAR + VIX + HMM prob | HAR + VIX | -0.007 to +0.006 | no difference | -0.008 to +0.006 | no difference |  | 0.148 vs 0.146 |
| HAR + VIX + VIX-HMM prob | HAR + VIX | -0.005 to +0.008 | no difference | -0.005 to +0.009 | no difference |  | 0.147 vs 0.146 |
| HMM implied vol | HAR | +0.016 to +0.094 | worse | +0.006 to +0.095 | worse |  | 0.284 vs 0.177 |
| VIX-HMM implied vol | HAR | +0.003 to +0.094 | worse | -0.001 to +0.097 | no difference | yes | 0.251 vs 0.177 |

rows kept 1927 of 2228; verdicts moved: 1 of 7.

## 7. Two target definitions

Class: reproduction (read from the committed data caches and the reproduced forecasts). The cross-index target is sqrt(mean session RV^2) over the next 21 sessions (regular hours only, overnight excluded); the VIX and MS-GARCH holdouts' target is the rolling 21-day standard deviation of close-to-close returns. The implied-vol regressor is the same annualised close-to-close quantity in both (IV / sqrt(252), logged), so on the cross-index its level is about twice the target's and the log-scale intercept absorbs the gap. Computed on each index's scored window:

| index | median IV / sqrt(252) | median session RV | median target (21-day RMS session RV) | session RV^2 / close-to-close r^2 (means) | days |
|---|---|---|---|---|---|
| Nasdaq-100 | 1.25 | 0.74 | 0.79 | 0.58 | 3292 |
| Dow Jones Industrial Average | 0.96 | 0.54 | 0.58 | 0.57 | 3297 |
| Russell 2000 | 1.54 | 1.00 | 1.08 | 0.72 | 1513 |

Blast radius: none on any published number; the two definitions belong to different holdouts and each holdout's claims compare models on its own target. The paper should state both definitions side by side.

## Summary

Class: post hoc, from the reproduced forecasts; not a registered test (counts of per-index RMSE verdicts that move when the affected days are removed).

- VXD prints, 3 Dow scored days removed: 0 of 9 per-index verdicts move
- VXD what-if (prints replaced, OLS refit): replica exact; see 1b for the moved column
- partial YM sessions, 87 Dow days removed: 2 of 9 per-index verdicts move
- short targets, Nasdaq-100: 63 days removed, 1 of 9 per-index verdicts move
- short targets, Dow Jones Industrial Average: 21 days removed, 0 of 9 per-index verdicts move
- half days, Nasdaq-100: 560 days removed, 0 of 9 per-index verdicts move
- half days, Dow Jones Industrial Average: 565 days removed, 0 of 9 per-index verdicts move
- half days, Russell 2000: 243 days removed, 0 of 9 per-index verdicts move
- back-calculated VIX, 1996-2004 comparisons on the back-calculated days only: 1 of 7 verdicts move

