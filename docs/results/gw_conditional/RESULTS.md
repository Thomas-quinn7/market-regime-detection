# Giacomini-White conditional test: results

Class: **post hoc, computed from the spent holdouts' reproduced forecasts; not a registered test**. Plan: docs/GW_QLIKE_PLAN_2026-11.md part 2. Written by `examples/gw_conditional.py`. d = loss of the forecast minus loss of the reference (negative favours the forecast); instruments (1, p_t), p_t the walk-forward HMM high-vol probability on the forecast date; HAC long-run covariance with the rectangular kernel, 20 lags (amendment A1; Bartlett 63 if not positive definite); chi-squared(2). The Bartlett 20 p-value (the plan before A1) and a Bartlett 63 p-value are shown as kernel diagnostics only. Holm at 5% across the 36 primary tests (squared error and QLIKE as in POSTHOC); QLIKE on the variance forecast is a secondary family of 18 with its own Holm.

Pairs: G1 = the regime term added to the benchmark (HMM probability; MS-GARCH probability on the ETFs) against the benchmark; G2 = the two-state HMM's own forecast against the benchmark.


## Summary

- Primary tests rejecting at 5% before Holm: 17 of 36; after Holm: 7.
- Leads under the plan's reading rule (Holm rejection and the p = 1 interval wholly below zero): 0.
- Holm rejections where stress favours the reference (p = 1 interval wholly above zero): 4.
- Secondary (QLIKE var): 9 of 18 reject before Holm, 3 after.

- Holm rejections that do not reject at 5% under the Bartlett 63 diagnostic (kernel-fragile): 1: Brazil (EWZ) G1 squared error (Bartlett 63 p = 0.373).
- Blocks where the rectangular covariance was not positive definite and Bartlett 63 was used: 0 rows.
- With the originally planned Bartlett 20-lag covariance (oversized, see the size check; not used for any reading), 17 of 36 primary tests would reject at 5% before Holm.


## Primary family

| block | pair | loss | n | GW stat | p | p, Bartlett 20 (planned, not used) | p, Bartlett 63 (diagnostic) | Holm p | d at p=0 (95%) | d at p=1 (95%) | share p>=0.5 | mean d p>=0.5 / p<0.5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nasdaq-100 | G1 | squared error | 3286 | 1.11 | 0.574 | 0.508 | 0.526 | 1.000 | +0.0006 (-0.0018, +0.0031) | -0.0166 (-0.0476, +0.0144) | 0.19 | -0.0140 / -0.0001 |
| Nasdaq-100 | G1 | QLIKE | 3286 | 2.38 | 0.304 | 0.209 | 0.265 | 1.000 | +0.0046 (-0.0029, +0.0120) | -0.0443 (-0.0967, +0.0080) | 0.19 | -0.0382 / +0.0029 |
| Nasdaq-100 | G2 | squared error | 3286 | 8.62 | 0.013 | 0.002 | 0.013 | 0.309 | +0.0172 (+0.0034, +0.0311) | +0.0598 (-0.0750, +0.1946) | 0.19 | +0.0513 / +0.0194 |
| Nasdaq-100 | G2 | QLIKE | 3286 | 10.30 | 0.006 | 0.002 | 0.004 | 0.145 | +0.0945 (+0.0340, +0.1550) | +0.0346 (-0.1476, +0.2168) | 0.19 | +0.0371 / +0.0937 |
| Dow Jones Industrial Average | G1 | squared error | 3297 | 2.68 | 0.261 | 0.224 | 0.333 | 1.000 | +0.0003 (-0.0003, +0.0008) | +0.0019 (-0.0012, +0.0050) | 0.18 | +0.0017 / +0.0003 |
| Dow Jones Industrial Average | G1 | QLIKE | 3297 | 3.04 | 0.219 | 0.167 | 0.209 | 1.000 | +0.0050 (-0.0008, +0.0109) | -0.0035 (-0.0294, +0.0224) | 0.18 | -0.0024 / +0.0047 |
| Dow Jones Industrial Average | G2 | squared error | 3297 | 11.44 | 0.003 | 0.000 | 0.004 | 0.092 | +0.0019 (-0.0152, +0.0190) | +0.1527 (-0.1351, +0.4405) | 0.18 | +0.1238 / +0.0104 |
| Dow Jones Industrial Average | G2 | QLIKE | 3297 | 7.99 | 0.018 | 0.012 | 0.022 | 0.386 | +0.0591 (+0.0059, +0.1122) | +0.3730 (-0.3868, +1.1328) | 0.18 | +0.3024 / +0.0790 |
| Russell 2000 | G1 | squared error | 1513 | 3.26 | 0.196 | 0.154 | 0.154 | 1.000 | -0.0014 (-0.0050, +0.0022) | +0.0111 (-0.0004, +0.0226) | 0.18 | +0.0105 / -0.0010 |
| Russell 2000 | G1 | QLIKE | 1513 | 3.98 | 0.137 | 0.103 | 0.135 | 1.000 | +0.0009 (-0.0029, +0.0047) | +0.0067 (-0.0012, +0.0147) | 0.18 | +0.0069 / +0.0010 |
| Russell 2000 | G2 | squared error | 1513 | 13.08 | 0.001 | 0.000 | 0.002 | 0.043 | +0.0149 (-0.0122, +0.0420) | +0.1755 (+0.0692, +0.2819) | 0.18 | +0.1545 / +0.0234 |
| Russell 2000 | G2 | QLIKE | 1513 | 16.85 | 0.000 | 0.000 | 0.000 | 0.007 | +0.0616 (+0.0031, +0.1201) | +0.0989 (+0.0324, +0.1654) | 0.18 | +0.1002 / +0.0623 |
| Crude oil (USO) | G1 | squared error | 3604 | 0.22 | 0.896 | 0.873 | 0.836 | 1.000 | +0.0003 (-0.0052, +0.0057) | +0.0070 (-0.0297, +0.0438) | 0.23 | +0.0045 / +0.0011 |
| Crude oil (USO) | G1 | QLIKE | 3604 | 0.48 | 0.786 | 0.721 | 0.727 | 1.000 | +0.0010 (-0.0022, +0.0042) | -0.0019 (-0.0109, +0.0071) | 0.23 | -0.0018 / +0.0010 |
| Crude oil (USO) | G2 | squared error | 3604 | 14.22 | 0.001 | 0.000 | 0.001 | 0.025 | +0.0259 (-0.2151, +0.2669) | +1.7240 (-1.2332, +4.6813) | 0.23 | +1.3657 / +0.1498 |
| Crude oil (USO) | G2 | QLIKE | 3604 | 8.92 | 0.012 | 0.002 | 0.007 | 0.278 | +0.1180 (+0.0040, +0.2319) | +0.5444 (-0.3103, +1.3992) | 0.23 | +0.4388 / +0.1538 |
| Gold (GLD) | G1 | squared error | 3821 | 1.79 | 0.409 | 0.316 | 0.279 | 1.000 | -0.0008 (-0.0037, +0.0021) | +0.0202 (-0.0088, +0.0491) | 0.18 | +0.0165 / +0.0006 |
| Gold (GLD) | G1 | QLIKE | 3821 | 2.61 | 0.271 | 0.146 | 0.243 | 1.000 | +0.0001 (-0.0074, +0.0076) | +0.0364 (-0.0062, +0.0791) | 0.18 | +0.0303 / +0.0025 |
| Gold (GLD) | G2 | squared error | 3821 | 14.87 | 0.001 | 0.000 | 0.001 | 0.019 | +0.0257 (+0.0077, +0.0438) | +0.0750 (-0.0082, +0.1583) | 0.18 | +0.0687 / +0.0285 |
| Gold (GLD) | G2 | QLIKE | 3821 | 3.94 | 0.140 | 0.062 | 0.172 | 1.000 | +0.0496 (-0.0384, +0.1376) | +0.0716 (-0.0306, +0.1737) | 0.18 | +0.0646 / +0.0517 |
| Emerging markets (EEM) | G1 | squared error | 3119 | 0.52 | 0.770 | 0.702 | 0.739 | 1.000 | +0.0014 (-0.0024, +0.0052) | +0.0013 (-0.0155, +0.0180) | 0.05 | +0.0010 / +0.0014 |
| Emerging markets (EEM) | G1 | QLIKE | 3119 | 0.21 | 0.901 | 0.867 | 0.860 | 1.000 | +0.0017 (-0.0077, +0.0111) | +0.0015 (-0.0080, +0.0110) | 0.05 | +0.0001 / +0.0017 |
| Emerging markets (EEM) | G2 | squared error | 3119 | 10.54 | 0.005 | 0.001 | 0.003 | 0.134 | +0.0341 (+0.0089, +0.0593) | +0.4402 (+0.1509, +0.7295) | 0.05 | +0.3511 / +0.0450 |
| Emerging markets (EEM) | G2 | QLIKE | 3119 | 7.70 | 0.021 | 0.020 | 0.016 | 0.425 | +0.0681 (+0.0166, +0.1195) | +0.2407 (+0.0466, +0.4348) | 0.05 | +0.1645 / +0.0748 |
| Brazil (EWZ) | G1 | squared error | 3119 | 21.46 | 0.000 | 0.254 | 0.373 | 0.001 | -0.0110 (-0.0331, +0.0112) | -0.0242 (-0.0956, +0.0473) | 0.11 | -0.0223 / -0.0115 |
| Brazil (EWZ) | G1 | QLIKE | 3119 | 1.12 | 0.570 | 0.536 | 0.598 | 1.000 | -0.0118 (-0.0436, +0.0201) | +0.0473 (-0.0393, +0.1339) | 0.11 | +0.0309 / -0.0082 |
| Brazil (EWZ) | G2 | squared error | 3119 | 12.66 | 0.002 | 0.001 | 0.003 | 0.052 | +0.0464 (-0.0591, +0.1520) | +0.8782 (-0.3643, +2.1207) | 0.11 | +0.6605 / +0.0952 |
| Brazil (EWZ) | G2 | QLIKE | 3119 | 10.76 | 0.005 | 0.038 | 0.006 | 0.124 | +0.0470 (-0.0462, +0.1402) | +0.3485 (-0.1873, +0.8843) | 0.11 | +0.2418 / +0.0679 |
| S&P 500, 1996-2004 | G1 | squared error | 2228 | 3.85 | 0.146 | 0.098 | 0.114 | 1.000 | +0.0046 (-0.0004, +0.0096) | -0.0038 (-0.0113, +0.0037) | 0.67 | -0.0027 / +0.0031 |
| S&P 500, 1996-2004 | G1 | QLIKE | 2228 | 5.30 | 0.071 | 0.044 | 0.053 | 1.000 | +0.0257 (-0.0021, +0.0535) | -0.0102 (-0.0228, +0.0024) | 0.67 | -0.0054 / +0.0199 |
| S&P 500, 1996-2004 | G2 | squared error | 2228 | 27.19 | 0.000 | 0.000 | 0.000 | 0.000 | +0.0235 (+0.0004, +0.0466) | +0.0971 (+0.0250, +0.1691) | 0.67 | +0.0895 / +0.0312 |
| S&P 500, 1996-2004 | G2 | QLIKE | 2228 | 16.09 | 0.000 | 0.000 | 0.000 | 0.011 | +0.1595 (+0.0509, +0.2680) | +0.1760 (+0.0199, +0.3322) | 0.67 | +0.1776 / +0.1545 |
| S&P 500, 2024-2026 | G1 | squared error | 676 | 8.58 | 0.014 | 0.006 | 0.008 | 0.309 | -0.0060 (-0.0137, +0.0016) | -0.0067 (-0.1101, +0.0966) | 0.13 | -0.0066 / -0.0060 |
| S&P 500, 2024-2026 | G1 | QLIKE | 676 | 4.18 | 0.124 | 0.133 | 0.081 | 1.000 | -0.0050 (-0.0207, +0.0107) | -0.0726 (-0.2657, +0.1206) | 0.13 | -0.0677 / -0.0076 |
| S&P 500, 2024-2026 | G2 | squared error | 676 | 0.96 | 0.618 | 0.620 | 0.550 | 1.000 | -0.0074 (-0.0238, +0.0089) | +0.0233 (-0.2714, +0.3180) | 0.13 | +0.0254 / -0.0069 |
| S&P 500, 2024-2026 | G2 | QLIKE | 676 | 0.90 | 0.638 | 0.629 | 0.516 | 1.000 | -0.0174 (-0.0676, +0.0328) | -0.1385 (-0.7013, +0.4242) | 0.13 | -0.1140 / -0.0245 |


## Secondary family: QLIKE on the variance forecast

| block | pair | loss | n | GW stat | p | p, Bartlett 20 (planned, not used) | p, Bartlett 63 (diagnostic) | Holm p | d at p=0 (95%) | d at p=1 (95%) | share p>=0.5 | mean d p>=0.5 / p<0.5 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Nasdaq-100 | G1 | QLIKE var | 3286 | 1.57 | 0.457 | 0.394 | 0.415 | 1.000 | +0.0027 (-0.0045, +0.0098) | -0.0323 (-0.0816, +0.0170) | 0.19 | -0.0275 / +0.0014 |
| Nasdaq-100 | G2 | QLIKE var | 3286 | 8.53 | 0.014 | 0.005 | 0.010 | 0.182 | +0.0747 (+0.0227, +0.1268) | +0.0375 (-0.1227, +0.1978) | 0.19 | +0.0405 / +0.0739 |
| Dow Jones Industrial Average | G1 | QLIKE var | 3297 | 1.90 | 0.386 | 0.319 | 0.375 | 1.000 | +0.0037 (-0.0018, +0.0092) | -0.0016 (-0.0252, +0.0221) | 0.18 | -0.0008 / +0.0034 |
| Dow Jones Industrial Average | G2 | QLIKE var | 3297 | 6.59 | 0.037 | 0.023 | 0.043 | 0.408 | +0.0446 (-0.0024, +0.0916) | +0.3310 (-0.3302, +0.9922) | 0.18 | +0.2707 / +0.0619 |
| Russell 2000 | G1 | QLIKE var | 1513 | 3.43 | 0.180 | 0.136 | 0.136 | 1.000 | -0.0009 (-0.0047, +0.0030) | +0.0087 (-0.0002, +0.0177) | 0.18 | +0.0084 / -0.0006 |
| Russell 2000 | G2 | QLIKE var | 1513 | 18.07 | 0.000 | 0.000 | 0.000 | 0.002 | +0.0347 (-0.0099, +0.0793) | +0.1450 (+0.0720, +0.2180) | 0.18 | +0.1335 / +0.0399 |
| Crude oil (USO) | G1 | QLIKE var | 3604 | 0.19 | 0.911 | 0.882 | 0.878 | 1.000 | +0.0006 (-0.0023, +0.0034) | -0.0009 (-0.0090, +0.0073) | 0.23 | -0.0011 / +0.0006 |
| Crude oil (USO) | G2 | QLIKE var | 3604 | 9.96 | 0.007 | 0.001 | 0.005 | 0.103 | +0.1053 (+0.0091, +0.2015) | +0.4581 (-0.2779, +1.1941) | 0.23 | +0.3750 / +0.1337 |
| Gold (GLD) | G1 | QLIKE var | 3821 | 2.41 | 0.299 | 0.175 | 0.260 | 1.000 | +0.0005 (-0.0067, +0.0078) | +0.0306 (-0.0074, +0.0687) | 0.18 | +0.0257 / +0.0024 |
| Gold (GLD) | G2 | QLIKE var | 3821 | 6.26 | 0.044 | 0.016 | 0.057 | 0.437 | +0.0537 (-0.0303, +0.1377) | +0.0765 (-0.0091, +0.1621) | 0.18 | +0.0733 / +0.0550 |
| Emerging markets (EEM) | G1 | QLIKE var | 3119 | 0.66 | 0.719 | 0.645 | 0.669 | 1.000 | +0.0036 (-0.0052, +0.0125) | +0.0011 (-0.0092, +0.0114) | 0.05 | +0.0005 / +0.0036 |
| Emerging markets (EEM) | G2 | QLIKE var | 3119 | 9.35 | 0.009 | 0.011 | 0.005 | 0.130 | +0.0604 (+0.0168, +0.1039) | +0.2250 (+0.0689, +0.3811) | 0.05 | +0.1665 / +0.0660 |
| Brazil (EWZ) | G1 | QLIKE var | 3119 | 0.90 | 0.638 | 0.498 | 0.592 | 1.000 | -0.0141 (-0.0432, +0.0150) | +0.0362 (-0.0443, +0.1167) | 0.11 | +0.0216 / -0.0110 |
| Brazil (EWZ) | G2 | QLIKE var | 3119 | 7.61 | 0.022 | 0.143 | 0.028 | 0.267 | +0.0234 (-0.0692, +0.1160) | +0.2797 (-0.1414, +0.7008) | 0.11 | +0.2035 / +0.0395 |
| S&P 500, 1996-2004 | G1 | QLIKE var | 2228 | 2.72 | 0.256 | 0.195 | 0.212 | 1.000 | +0.0173 (-0.0076, +0.0422) | -0.0067 (-0.0186, +0.0051) | 0.67 | -0.0035 / +0.0132 |
| S&P 500, 1996-2004 | G2 | QLIKE var | 2228 | 17.13 | 0.000 | 0.000 | 0.000 | 0.003 | +0.1346 (+0.0442, +0.2249) | +0.1650 (+0.0343, +0.2956) | 0.67 | +0.1658 / +0.1294 |
| S&P 500, 2024-2026 | G1 | QLIKE var | 676 | 13.90 | 0.001 | 0.001 | 0.000 | 0.015 | -0.0128 (-0.0259, +0.0004) | -0.0487 (-0.2311, +0.1336) | 0.13 | -0.0464 / -0.0142 |
| S&P 500, 2024-2026 | G2 | QLIKE var | 676 | 0.20 | 0.904 | 0.894 | 0.871 | 1.000 | -0.0081 (-0.0596, +0.0435) | -0.0844 (-0.7076, +0.5388) | 0.13 | -0.0570 / -0.0143 |


## Size check (amendment A1; synthetic data only)

Rejection rate at a nominal 5% under a true null: d a flat MA(20) of Student-t(5) shocks, p a persistent logistic AR(1) independent of d, 500 draws per length, seed 7.

| days | rectangular 20 (used) | Bartlett 20 (planned) |
|---|---|---|
| 676 | 0.074 | 0.166 |
| 2228 | 0.054 | 0.158 |
| 3300 | 0.052 | 0.122 |


## Note on POSTHOC's DM tests (amendment A1 iv; not a change to POSTHOC)

The same Bartlett 20-lag variance is used by the HAC Diebold-Mariano tests in docs/POSTHOC_2026-10.md, so they share the size problem above. Rejections at 5% for the registered-claim pairs, per holdout and loss:

| holdout | loss | reject at 5%, Bartlett 20 (POSTHOC) | reject at 5%, rectangular 20 | pairs |
|---|---|---|---|---|
| cross_index | QLIKE | 3 | 4 | 27 |
| cross_index | squared error | 5 | 3 | 27 |
| etf | QLIKE | 8 | 5 | 36 |
| etf | squared error | 12 | 13 | 36 |
| vix_early | QLIKE | 4 | 3 | 7 |
| vix_early | squared error | 4 | 3 | 7 |
| vix_recent | QLIKE | 1 | 1 | 7 |
| vix_recent | squared error | 0 | 0 | 7 |

8 of 37 Bartlett rejections are not rejections under the rectangular kernel. The bootstrap intervals that decide every registered and POSTHOC verdict are not affected; only the DM column is.
