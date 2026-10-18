post hoc, computed from the reproduced forecasts; not a registered test

# Multiple testing across the registered holdout comparisons, October 2026

Written by `examples/power_multiplicity.py` at 2c31339 plus uncommitted files, 2026-10-18 11:50Z. p-values: *boot* inverts the registered paired circular block bootstrap (63-day blocks, seed 0, 20,000 draws, the first 2,000 of which are the registered draws), two-sided, `regimes.posthoc.bootstrap_p_value`; *DM* is a HAC Diebold-Mariano test (Bartlett, lag 20) of equal mean squared error (RMSE rows) or equal mean QLIKE. Holm (1979) at 5% family-wise, `regimes.posthoc.holm`. The smallest bootstrap p-value attainable is 2 / (20,000 + 1) = 0.00010; Holm's first threshold across all registered tests is 0.05 / 81 = 0.00062. Stage S7 (b); joint desk finding 12 and desk finding 9 (`HMM_DESK_REVIEW_2026-10-17.md`: no multiplicity correction anywhere).

No verdict changes. The registered rule (a 95% interval per comparison, no correction) stays the verdict; this file only says which registered "better" and "worse" verdicts would survive a family-wise correction. A correction can only turn a "better" or "worse" into "no difference", so it can never break a registered "not better" claim that holds; it can only make it easier to hold.

## 1. The registered families

Class: post hoc, computed from the reproduced forecasts; not a registered test (the counts are read off the protocols and the scored tables).

| family | holdout | comparisons | claims | assets | registered non-null RMSE verdicts |
|---|---|---|---|---|---|
| cross-index per-index verdicts | Cross-index holdout | 27 | 9 | 3 | 8 |
| ETF per-asset verdicts | MS-GARCH and credit holdout | 36 | 9 | 4 | 14 |
| VIX comparisons, S&P 500, 1996-2004 | S&P 500, 1996-2004 | 7 | 5 | 1 | 4 |
| VIX comparisons, S&P 500, 2024-2026 | S&P 500, 2024-2026 | 7 | 5 | 1 | 1 |
| stock-bond level rules | Stock-bond, 1962-2004 | 4 | 4 | 1 | 3 |
| all registered interval tests | all | 81 |  |  | 30 |

Not counted as interval tests: the stock-bond detection rule (B classifier vs trailing 63-day correlation on median lag, misses and false alarms; no p-value exists) and the VIX claims A, B, C, which are read off the seven comparisons. The stock-bond intervals' p-values are a normal approximation from the printed 3-decimal interval (the reproduction saved no stock-bond forecasts), and that family has no QLIKE.

## 2. Which registered verdicts survive

Class: post hoc, computed from the reproduced forecasts; not a registered test. Every comparison whose verdict on that loss is "better" or "worse" (the registered RMSE verdict, or the post-hoc QLIKE verdict from the same interval scheme), with its p-values and whether Holm keeps it within its family and across all registered tests. "yes" = survives.

### RMSE

| family | claim | asset | forecast vs reference | verdict | interval | p boot | p DM | Holm family (boot) | Holm all (boot) | Holm family (DM) | Holm all (DM) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cross-index per-index verdicts | P4 | Nasdaq-100 | Combination vs HAR-RV + IV | worse | +0.000 to +0.018 | 0.0360 | 0.0864 | no | no | no | no |
| cross-index per-index verdicts | R1 | Nasdaq-100 | HAR-RV + IV vs HAR-RV | better | -0.018 to -0.000 | 0.0411 | 0.0599 | no | no | no | no |
| cross-index per-index verdicts | R2 | Nasdaq-100 | HAR-RV vs HAR | better | -0.028 to -0.008 | 0.0001 | 0.0227 | yes | yes | no | no |
| cross-index per-index verdicts | R4 | Nasdaq-100 | GJR-GARCH vs HAR-RV + IV | worse | +0.002 to +0.032 | 0.0248 | 0.0271 | no | no | no | no |
| cross-index per-index verdicts | P4 | Dow Jones Industrial Average | Combination vs HAR-RV + IV | worse | +0.000 to +0.011 | 0.0316 | 0.1532 | no | no | no | no |
| cross-index per-index verdicts | R2 | Dow Jones Industrial Average | HAR-RV vs HAR | better | -0.024 to -0.006 | 0.0004 | 0.0428 | yes | yes | no | no |
| cross-index per-index verdicts | R4 | Dow Jones Industrial Average | GJR-GARCH vs HAR-RV + IV | worse | +0.002 to +0.020 | 0.0124 | 0.0371 | no | no | no | no |
| cross-index per-index verdicts | P5 | Russell 2000 | MSM vs Two-state HMM implied vol | better | -0.106 to -0.016 | 0.0036 | 0.0008 | no | no | yes | no |
| ETF per-asset verdicts | M2 | Crude oil (USO) | HAR + IV + MS-GARCH vs HAR + IV | worse | +0.000 to +0.024 | 0.0487 | 0.1455 | no | no | no | no |
| ETF per-asset verdicts | M5 | Crude oil (USO) | MS-GARCH vs HAR + IV | worse | +0.038 to +0.240 | 0.0005 | 0.0134 | yes | yes | no | no |
| ETF per-asset verdicts | R1 | Crude oil (USO) | HAR + IV vs HAR | better | -0.127 to -0.010 | 0.0286 | 0.0625 | no | no | no | no |
| ETF per-asset verdicts | R2 | Crude oil (USO) | GJR-GARCH vs HAR + IV | worse | +0.043 to +0.204 | 0.0001 | 0.0079 | yes | yes | no | no |
| ETF per-asset verdicts | M3 | Gold (GLD) | MS-GARCH vs Two-state HMM implied vol | better | -0.044 to -0.002 | 0.0424 | 0.0122 | no | no | no | no |
| ETF per-asset verdicts | M5 | Gold (GLD) | MS-GARCH vs HAR + IV | worse | +0.013 to +0.038 | 0.0002 | 0.0001 | yes | yes | yes | yes |
| ETF per-asset verdicts | R1 | Gold (GLD) | HAR + IV vs HAR | better | -0.051 to -0.022 | 0.0001 | 0.0000 | yes | yes | yes | yes |
| ETF per-asset verdicts | R2 | Gold (GLD) | GJR-GARCH vs HAR + IV | worse | +0.010 to +0.037 | 0.0007 | 0.0001 | yes | no | yes | yes |
| ETF per-asset verdicts | M3 | Emerging markets (EEM) | MS-GARCH vs Two-state HMM implied vol | better | -0.058 to -0.017 | 0.0005 | 0.0037 | yes | yes | no | no |
| ETF per-asset verdicts | M5 | Emerging markets (EEM) | MS-GARCH vs HAR + IV | worse | +0.005 to +0.048 | 0.0106 | 0.0166 | no | no | no | no |
| ETF per-asset verdicts | R1 | Emerging markets (EEM) | HAR + IV vs HAR | better | -0.049 to -0.009 | 0.0043 | 0.0131 | no | no | no | no |
| ETF per-asset verdicts | R2 | Emerging markets (EEM) | GJR-GARCH vs HAR + IV | worse | +0.009 to +0.061 | 0.0075 | 0.0254 | no | no | no | no |
| ETF per-asset verdicts | M2 | Brazil (EWZ) | HAR + IV + MS-GARCH vs HAR + IV | worse | +0.001 to +0.006 | 0.0145 | 0.0153 | no | no | no | no |
| ETF per-asset verdicts | M5 | Brazil (EWZ) | MS-GARCH vs HAR + IV | worse | +0.026 to +0.122 | 0.0026 | 0.0036 | no | no | no | no |
| VIX comparisons, S&P 500, 1996-2004 | (1) | S&P 500, 1996-2004 | VIX vs HAR | better | -0.054 to -0.003 | 0.0271 | 0.0097 | no | no | yes | no |
| VIX comparisons, S&P 500, 1996-2004 | A | S&P 500, 1996-2004 | HAR + VIX vs HAR | better | -0.054 to -0.012 | 0.0035 | 0.0012 | yes | no | yes | no |
| VIX comparisons, S&P 500, 1996-2004 | C | S&P 500, 1996-2004 | HMM implied vol vs HAR | worse | +0.016 to +0.094 | 0.0080 | 0.0027 | yes | no | yes | no |
| VIX comparisons, S&P 500, 1996-2004 | C | S&P 500, 1996-2004 | VIX-HMM implied vol vs HAR | worse | +0.003 to +0.094 | 0.0381 | 0.0185 | no | no | no | no |
| VIX comparisons, S&P 500, 2024-2026 | A | S&P 500, 2024-2026 | HAR + VIX vs HAR | better | -0.053 to -0.001 | 0.0363 | 0.2151 | no | no | no | no |
| stock-bond level rules | level A | S&P 500 / 10y | A implied correlation vs trailing 63-day correlation | worse | +0.034 to +0.109 | 0.0002 (approx) | n/a | yes | yes | n/a | n/a |
| stock-bond level rules | level B | S&P 500 / 10y | B implied correlation vs trailing 63-day correlation | worse | +0.045 to +0.111 | 0.0000 (approx) | n/a | yes | yes | n/a | n/a |
| stock-bond level rules | level, EWMA | S&P 500 / 10y | EWMA correlation (0.97) vs trailing 63-day correlation | better | -0.019 to -0.005 | 0.0008 (approx) | n/a | yes | no | n/a | n/a |

RMSE, boot p-values: 30 non-null verdicts; 13 survive Holm within their family, 9 across all registered tests.

RMSE, DM p-values: 30 non-null verdicts; 7 survive Holm within their family, 3 across all registered tests.

### QLIKE

| family | claim | asset | forecast vs reference | verdict | interval | p boot | p DM | Holm family (boot) | Holm all (boot) | Holm family (DM) | Holm all (DM) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| cross-index per-index verdicts | R2 | Nasdaq-100 | HAR-RV vs HAR | better | -0.037 to -0.002 | 0.0265 | 0.0838 | no | no | no | no |
| cross-index per-index verdicts | R4 | Nasdaq-100 | GJR-GARCH vs HAR-RV + IV | worse | +0.011 to +0.107 | 0.0102 | 0.0156 | no | no | no | no |
| cross-index per-index verdicts | P5 | Russell 2000 | MSM vs Two-state HMM implied vol | better | -0.105 to -0.016 | 0.0021 | 0.0015 | no | no | yes | no |
| cross-index per-index verdicts | R2 | Russell 2000 | HAR-RV vs HAR | better | -0.025 to -0.004 | 0.0029 | 0.0202 | no | no | no | no |
| ETF per-asset verdicts | M2 | Crude oil (USO) | HAR + IV + MS-GARCH vs HAR + IV | worse | +0.001 to +0.010 | 0.0137 | 0.0556 | no | no | no | no |
| ETF per-asset verdicts | M3 | Crude oil (USO) | MS-GARCH vs Two-state HMM implied vol | better | -0.323 to -0.004 | 0.0347 | 0.0547 | no | no | no | no |
| ETF per-asset verdicts | M5 | Crude oil (USO) | MS-GARCH vs HAR + IV | worse | +0.034 to +0.181 | 0.0001 | 0.0030 | yes | yes | no | no |
| ETF per-asset verdicts | C2 | Crude oil (USO) | HAR + credit vs HAR | worse | +0.002 to +0.018 | 0.0033 | 0.0200 | no | no | no | no |
| ETF per-asset verdicts | R1 | Crude oil (USO) | HAR + IV vs HAR | better | -0.148 to -0.038 | 0.0001 | 0.0006 | yes | yes | yes | yes |
| ETF per-asset verdicts | R2 | Crude oil (USO) | GJR-GARCH vs HAR + IV | worse | +0.044 to +0.185 | 0.0001 | 0.0013 | yes | yes | yes | no |
| ETF per-asset verdicts | M3 | Brazil (EWZ) | MS-GARCH vs Two-state HMM implied vol | better | -0.079 to -0.010 | 0.0085 | 0.0084 | no | no | no | no |
| ETF per-asset verdicts | C2 | Brazil (EWZ) | HAR + credit vs HAR | worse | +0.002 to +0.011 | 0.0010 | 0.0054 | yes | no | no | no |
| VIX comparisons, S&P 500, 1996-2004 | (1) | S&P 500, 1996-2004 | VIX vs HAR | better | -0.103 to -0.018 | 0.0062 | 0.0026 | yes | no | yes | no |
| VIX comparisons, S&P 500, 1996-2004 | A | S&P 500, 1996-2004 | HAR + VIX vs HAR | better | -0.102 to -0.032 | 0.0003 | 0.0001 | yes | yes | yes | yes |
| VIX comparisons, S&P 500, 1996-2004 | (3) | S&P 500, 1996-2004 | HAR + HMM prob vs HAR | worse | +0.001 to +0.039 | 0.0384 | 0.0249 | no | no | no | no |
| VIX comparisons, S&P 500, 1996-2004 | C | S&P 500, 1996-2004 | HMM implied vol vs HAR | worse | +0.026 to +0.192 | 0.0086 | 0.0028 | yes | no | yes | no |
| VIX comparisons, S&P 500, 2024-2026 | (3) | S&P 500, 2024-2026 | HAR + HMM prob vs HAR | better | -0.071 to -0.004 | 0.0200 | 0.0529 | no | no | no | no |
| VIX comparisons, S&P 500, 2024-2026 | C | S&P 500, 2024-2026 | HMM implied vol vs HAR | better | -0.100 to -0.013 | 0.0056 | 0.0202 | yes | no | no | no |

QLIKE, boot p-values: 18 non-null verdicts; 8 survive Holm within their family, 4 across all registered tests.

QLIKE, DM p-values: 18 non-null verdicts; 6 survive Holm within their family, 2 across all registered tests.

## 3. Claim outcomes when the non-surviving verdicts are read as no difference

Class: post hoc, computed from the reproduced forecasts; not a registered test. The registered rule applied to per-asset verdicts after Holm (bootstrap p-values): a verdict Holm does not keep is read as "no difference". The registered column is the verdict and does not change.

| holdout | claim | RMSE (registered) | RMSE, Holm family | RMSE, Holm all | QLIKE (post hoc) | QLIKE, Holm family | QLIKE, Holm all | moves under Holm |
|---|---|---|---|---|---|---|---|---|
| Cross-index holdout | P1 | rejected | rejected | rejected | rejected | rejected | rejected |  |
| Cross-index holdout | P2 | rejected | rejected | rejected | rejected | rejected | rejected |  |
| Cross-index holdout | P3 | rejected | rejected | rejected | rejected | rejected | rejected |  |
| Cross-index holdout | P4 | rejected | rejected | rejected | rejected | rejected | rejected |  |
| Cross-index holdout | P5 | mixed | rejected | rejected | mixed | rejected | rejected | yes |
| Cross-index holdout | R1 | mixed | rejected | rejected | rejected | rejected | rejected | yes |
| Cross-index holdout | R2 | confirmed | confirmed | confirmed | confirmed | rejected | rejected |  |
| Cross-index holdout | R3 | holds | holds | holds | holds | holds | holds |  |
| Cross-index holdout | R4 | holds | holds | holds | holds | holds | holds |  |
| MS-GARCH and credit holdout | M1 | rejected | rejected | rejected | rejected | rejected | rejected |  |
| MS-GARCH and credit holdout | M2 | rejected | rejected | rejected | rejected | rejected | rejected |  |
| MS-GARCH and credit holdout | M3 | confirmed | mixed | mixed | confirmed | rejected | rejected | yes |
| MS-GARCH and credit holdout | M4 | rejected | rejected | rejected | rejected | rejected | rejected |  |
| MS-GARCH and credit holdout | M5 | rejected | rejected | rejected | rejected | rejected | rejected |  |
| MS-GARCH and credit holdout | C1 | holds | holds | holds | holds | holds | holds |  |
| MS-GARCH and credit holdout | C2 | rejected | rejected | rejected | rejected | rejected | rejected |  |
| MS-GARCH and credit holdout | R1 | confirmed | mixed | mixed | mixed | mixed | mixed | yes |
| MS-GARCH and credit holdout | R2 | holds | holds | holds | holds | holds | holds |  |
| S&P 500, 1996-2004 | A. VIX improves HAR | holds | holds | not shown | holds | holds | holds | yes |
| S&P 500, 1996-2004 | B. regime adds nothing once the VIX is in | holds | holds | holds | holds | holds | holds |  |
| S&P 500, 1996-2004 | C. regime models' own forecasts lose to HAR | holds | not shown | not shown | not shown | not shown | not shown | yes |
| S&P 500, 2024-2026 | A. VIX improves HAR | holds | not shown | not shown | not shown | not shown | not shown | yes |
| S&P 500, 2024-2026 | B. regime adds nothing once the VIX is in | holds | holds | holds | holds | holds | holds |  |
| S&P 500, 2024-2026 | C. regime models' own forecasts lose to HAR | not shown | not shown | not shown | not shown | not shown | not shown |  |

RMSE claim outcomes that move under Holm (family or all): 7 of 24: Cross-index holdout P5 (mixed -> rejected across all); Cross-index holdout R1 (mixed -> rejected across all); MS-GARCH and credit holdout M3 (confirmed -> mixed across all); MS-GARCH and credit holdout R1 (confirmed -> mixed across all); S&P 500, 1996-2004 A. VIX improves HAR (holds -> not shown across all); S&P 500, 1996-2004 C. regime models' own forecasts lose to HAR (holds -> not shown across all); S&P 500, 2024-2026 A. VIX improves HAR (holds -> not shown across all).

