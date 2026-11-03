# QLIKE on variance forecasts: results

Class: **post hoc, computed from the spent holdouts' reproduced forecasts; not a registered test**. Plan: docs/GW_QLIKE_PLAN_2026-11.md part 1. Written by `examples/variance_rescore.py score`, 2,000 draws, 63-day circular blocks, seed 0. 'QLIKE' is the convention of docs/POSTHOC_2026-10.md (the squared mean-vol forecast); 'QLIKE var' scores the variance forecast exp(2 fit + 2 s^2).


## Summary: claim outcomes that change between POSTHOC QLIKE and QLIKE var

- etf R1: mixed under POSTHOC QLIKE -> confirmed under QLIKE var
- vix_recent B. regime adds nothing once the VIX is in: holds -> fails

Not scored under QLIKE var, because a forecast in the claim has no matched regression variance (in the cross-index holdout GJR-GARCH, MSM and the combination are not regression forecasts, and HAR-RV + IV + MSM does not match the committed reproduction because the MSM refits differ across hosts by up to about 5e-4): cross_index P3, cross_index P4, cross_index P5, cross_index R4.


## cross_index

Size of the bias factor exp(s^2) per forecast (median over refits, last table): HAR 1.088; HAR-RV 1.077; HAR-RV + IV 1.070; HARQ + IV 1.070; SHAR + IV 1.070; Two-state HMM implied vol 1.115; HAR-RV + IV + HMM prob 1.070.

Columns not matched to a captured regression forecast (not variance-scored; in the VIX holdouts table 01 is the raw, uncalibrated table, which no claim uses): variance_01.csv GJR-GARCH: closest gap 2.17e-05; variance_01.csv MSM: closest gap 7.71e-05; variance_01.csv HAR-RV + IV + MSM: closest gap 1.52e-05; variance_01.csv Combination: closest gap 3.69e-01; variance_02.csv GJR-GARCH: closest gap 5.69e-05; variance_02.csv MSM: closest gap 4.73e-04; variance_02.csv HAR-RV + IV + MSM: closest gap 6.60e-05; variance_02.csv Combination: closest gap 3.52e-01; variance_03.csv GJR-GARCH: closest gap 9.86e-05; variance_03.csv MSM: closest gap 6.90e-05; variance_03.csv HAR-RV + IV + MSM: closest gap 3.49e-05; variance_03.csv Combination: closest gap 3.13e-01.

Matched columns: 21, of which 21 agree with the committed reproduction to within 1e-9 rather than bit for bit (the committed reproductions were written on another host; a deviation from the plan's 'exact').


### Claim outcomes

| claim | expected | RMSE (registered) | QLIKE (POSTHOC) | QLIKE var |
|---|---|---|---|---|
| P1 | better | rejected | rejected | rejected |
| P2 | better | rejected | rejected | rejected |
| P3 | better | rejected | rejected | not scored |
| P4 | better | rejected | rejected | not scored |
| P5 | better | mixed | mixed | not scored |
| R1 | better | mixed | rejected | rejected |
| R2 | better | confirmed | confirmed | confirmed |
| R3 | not better | holds | holds | holds |
| R4 | not better | holds | holds | not scored |


### Per-comparison verdicts that differ between the two QLIKE columns (12 of 27)

| claim | block | forecast vs reference | RMSE | QLIKE (POSTHOC) | QLIKE var | dQLIKE var 95% |
|---|---|---|---|---|---|---|
| P3 | Nasdaq-100 | HAR-RV + IV + MSM vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |
| P4 | Nasdaq-100 | Combination vs HAR-RV + IV | worse | no difference | not scored (no exact variance match) |  |
| P5 | Nasdaq-100 | MSM vs Two-state HMM implied vol | no difference | no difference | not scored (no exact variance match) |  |
| R4 | Nasdaq-100 | GJR-GARCH vs HAR-RV + IV | worse | worse | not scored (no exact variance match) |  |
| P3 | Dow Jones Industrial Average | HAR-RV + IV + MSM vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |
| P4 | Dow Jones Industrial Average | Combination vs HAR-RV + IV | worse | no difference | not scored (no exact variance match) |  |
| P5 | Dow Jones Industrial Average | MSM vs Two-state HMM implied vol | no difference | no difference | not scored (no exact variance match) |  |
| R4 | Dow Jones Industrial Average | GJR-GARCH vs HAR-RV + IV | worse | no difference | not scored (no exact variance match) |  |
| P3 | Russell 2000 | HAR-RV + IV + MSM vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |
| P4 | Russell 2000 | Combination vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |
| P5 | Russell 2000 | MSM vs Two-state HMM implied vol | better | better | not scored (no exact variance match) |  |
| R4 | Russell 2000 | GJR-GARCH vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |


### Every comparison

| claim | block | forecast vs reference | RMSE | QLIKE (POSTHOC) | QLIKE var | dQLIKE var 95% |
|---|---|---|---|---|---|---|
| P1 | Nasdaq-100 | HARQ + IV vs HAR-RV + IV | no difference | no difference | no difference | -0.0000 to +0.0005 |
| P2 | Nasdaq-100 | SHAR + IV vs HAR-RV + IV | no difference | no difference | no difference | -0.0006 to +0.0004 |
| P3 | Nasdaq-100 | HAR-RV + IV + MSM vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |
| P4 | Nasdaq-100 | Combination vs HAR-RV + IV | worse | no difference | not scored (no exact variance match) |  |
| P5 | Nasdaq-100 | MSM vs Two-state HMM implied vol | no difference | no difference | not scored (no exact variance match) |  |
| R1 | Nasdaq-100 | HAR-RV + IV vs HAR-RV | better | no difference | no difference | -0.0438 to +0.0032 |
| R2 | Nasdaq-100 | HAR-RV vs HAR | better | better | better | -0.0328 to -0.0013 |
| R3 | Nasdaq-100 | HAR-RV + IV + HMM prob vs HAR-RV + IV | no difference | no difference | no difference | -0.0109 to +0.0016 |
| R4 | Nasdaq-100 | GJR-GARCH vs HAR-RV + IV | worse | worse | not scored (no exact variance match) |  |
| P1 | Dow Jones Industrial Average | HARQ + IV vs HAR-RV + IV | no difference | no difference | no difference | -0.0005 to +0.0007 |
| P2 | Dow Jones Industrial Average | SHAR + IV vs HAR-RV + IV | no difference | no difference | no difference | -0.0006 to +0.0005 |
| P3 | Dow Jones Industrial Average | HAR-RV + IV + MSM vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |
| P4 | Dow Jones Industrial Average | Combination vs HAR-RV + IV | worse | no difference | not scored (no exact variance match) |  |
| P5 | Dow Jones Industrial Average | MSM vs Two-state HMM implied vol | no difference | no difference | not scored (no exact variance match) |  |
| R1 | Dow Jones Industrial Average | HAR-RV + IV vs HAR-RV | no difference | no difference | no difference | -0.0373 to +0.0028 |
| R2 | Dow Jones Industrial Average | HAR-RV vs HAR | better | no difference | no difference | -0.0433 to +0.0166 |
| R3 | Dow Jones Industrial Average | HAR-RV + IV + HMM prob vs HAR-RV + IV | no difference | no difference | no difference | -0.0017 to +0.0082 |
| R4 | Dow Jones Industrial Average | GJR-GARCH vs HAR-RV + IV | worse | no difference | not scored (no exact variance match) |  |
| P1 | Russell 2000 | HARQ + IV vs HAR-RV + IV | no difference | no difference | no difference | -0.0002 to +0.0005 |
| P2 | Russell 2000 | SHAR + IV vs HAR-RV + IV | no difference | no difference | no difference | -0.0003 to +0.0003 |
| P3 | Russell 2000 | HAR-RV + IV + MSM vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |
| P4 | Russell 2000 | Combination vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |
| P5 | Russell 2000 | MSM vs Two-state HMM implied vol | better | better | not scored (no exact variance match) |  |
| R1 | Russell 2000 | HAR-RV + IV vs HAR-RV | no difference | no difference | no difference | -0.0099 to +0.0132 |
| R2 | Russell 2000 | HAR-RV vs HAR | no difference | better | better | -0.0258 to -0.0065 |
| R3 | Russell 2000 | HAR-RV + IV + HMM prob vs HAR-RV + IV | no difference | no difference | no difference | -0.0018 to +0.0042 |
| R4 | Russell 2000 | GJR-GARCH vs HAR-RV + IV | no difference | no difference | not scored (no exact variance match) |  |


## etf

Size of the bias factor exp(s^2) per forecast (median over refits, last table): HAR 1.096; HAR + IV 1.079; HAR + credit 1.096; HAR + IV + credit 1.079; GJR-GARCH 1.106; Two-state HMM implied vol 1.126; MS-GARCH 1.114; HAR + IV + MS-GARCH 1.079; HAR + IV + MS-GARCH prob 1.077.

Matched columns: 36, of which 36 agree with the committed reproduction to within 1e-9 rather than bit for bit (the committed reproductions were written on another host; a deviation from the plan's 'exact').


### Claim outcomes

| claim | expected | RMSE (registered) | QLIKE (POSTHOC) | QLIKE var |
|---|---|---|---|---|
| M1 | better | rejected | rejected | rejected |
| M2 | better | rejected | rejected | rejected |
| M3 | better | confirmed | confirmed | confirmed |
| M4 | better | rejected | rejected | rejected |
| M5 | better | rejected | rejected | rejected |
| C1 | not better | holds | holds | holds |
| C2 | better | rejected | rejected | rejected |
| R1 | better | confirmed | mixed | confirmed |
| R2 | not better | holds | holds | holds |


### Per-comparison verdicts that differ between the two QLIKE columns (3 of 36)

| claim | block | forecast vs reference | RMSE | QLIKE (POSTHOC) | QLIKE var | dQLIKE var 95% |
|---|---|---|---|---|---|---|
| C2 | Crude oil (USO) | HAR + credit vs HAR | no difference | worse | no difference | -0.0003 to +0.0145 |
| R1 | Gold (GLD) | HAR + IV vs HAR | better | no difference | better | -0.0720 to -0.0027 |
| R2 | Gold (GLD) | GJR-GARCH vs HAR + IV | worse | no difference | worse | +0.0001 to +0.0580 |


### Every comparison

| claim | block | forecast vs reference | RMSE | QLIKE (POSTHOC) | QLIKE var | dQLIKE var 95% |
|---|---|---|---|---|---|---|
| M1 | Crude oil (USO) | MS-GARCH vs GJR-GARCH | no difference | no difference | no difference | -0.0193 to +0.0068 |
| M2 | Crude oil (USO) | HAR + IV + MS-GARCH vs HAR + IV | worse | worse | worse | +0.0010 to +0.0096 |
| M3 | Crude oil (USO) | MS-GARCH vs Two-state HMM implied vol | no difference | better | better | -0.2673 to -0.0048 |
| M4 | Crude oil (USO) | HAR + IV + MS-GARCH prob vs HAR + IV | no difference | no difference | no difference | -0.0020 to +0.0024 |
| M5 | Crude oil (USO) | MS-GARCH vs HAR + IV | worse | worse | worse | +0.0273 to +0.1570 |
| C1 | Crude oil (USO) | HAR + IV + credit vs HAR + IV | no difference | no difference | no difference | -0.0291 to +0.0064 |
| C2 | Crude oil (USO) | HAR + credit vs HAR | no difference | worse | no difference | -0.0003 to +0.0145 |
| R1 | Crude oil (USO) | HAR + IV vs HAR | better | better | better | -0.1289 to -0.0346 |
| R2 | Crude oil (USO) | GJR-GARCH vs HAR + IV | worse | worse | worse | +0.0359 to +0.1587 |
| M1 | Gold (GLD) | MS-GARCH vs GJR-GARCH | no difference | no difference | no difference | -0.0127 to +0.0125 |
| M2 | Gold (GLD) | HAR + IV + MS-GARCH vs HAR + IV | no difference | no difference | no difference | -0.0001 to +0.0026 |
| M3 | Gold (GLD) | MS-GARCH vs Two-state HMM implied vol | better | no difference | no difference | -0.0629 to +0.0209 |
| M4 | Gold (GLD) | HAR + IV + MS-GARCH prob vs HAR + IV | no difference | no difference | no difference | -0.0013 to +0.0165 |
| M5 | Gold (GLD) | MS-GARCH vs HAR + IV | worse | no difference | no difference | -0.0033 to +0.0607 |
| C1 | Gold (GLD) | HAR + IV + credit vs HAR + IV | no difference | no difference | no difference | -0.0074 to +0.0262 |
| C2 | Gold (GLD) | HAR + credit vs HAR | no difference | no difference | no difference | -0.0172 to +0.0311 |
| R1 | Gold (GLD) | HAR + IV vs HAR | better | no difference | better | -0.0720 to -0.0027 |
| R2 | Gold (GLD) | GJR-GARCH vs HAR + IV | worse | no difference | worse | +0.0001 to +0.0580 |
| M1 | Emerging markets (EEM) | MS-GARCH vs GJR-GARCH | no difference | no difference | no difference | -0.0045 to +0.0245 |
| M2 | Emerging markets (EEM) | HAR + IV + MS-GARCH vs HAR + IV | no difference | no difference | no difference | -0.0058 to +0.0100 |
| M3 | Emerging markets (EEM) | MS-GARCH vs Two-state HMM implied vol | better | no difference | no difference | -0.1197 to +0.0052 |
| M4 | Emerging markets (EEM) | HAR + IV + MS-GARCH prob vs HAR + IV | no difference | no difference | no difference | -0.0041 to +0.0113 |
| M5 | Emerging markets (EEM) | MS-GARCH vs HAR + IV | worse | no difference | no difference | -0.0265 to +0.0627 |
| C1 | Emerging markets (EEM) | HAR + IV + credit vs HAR + IV | no difference | no difference | no difference | -0.0034 to +0.0281 |
| C2 | Emerging markets (EEM) | HAR + credit vs HAR | no difference | no difference | no difference | -0.0106 to +0.0697 |
| R1 | Emerging markets (EEM) | HAR + IV vs HAR | better | no difference | no difference | -0.0427 to +0.0464 |
| R2 | Emerging markets (EEM) | GJR-GARCH vs HAR + IV | worse | no difference | no difference | -0.0388 to +0.0509 |
| M1 | Brazil (EWZ) | MS-GARCH vs GJR-GARCH | no difference | no difference | no difference | -0.0230 to +0.0697 |
| M2 | Brazil (EWZ) | HAR + IV + MS-GARCH vs HAR + IV | worse | no difference | no difference | -0.0004 to +0.0052 |
| M3 | Brazil (EWZ) | MS-GARCH vs Two-state HMM implied vol | no difference | better | better | -0.0629 to -0.0043 |
| M4 | Brazil (EWZ) | HAR + IV + MS-GARCH prob vs HAR + IV | no difference | no difference | no difference | -0.0263 to +0.0088 |
| M5 | Brazil (EWZ) | MS-GARCH vs HAR + IV | worse | no difference | no difference | -0.0352 to +0.0728 |
| C1 | Brazil (EWZ) | HAR + IV + credit vs HAR + IV | no difference | no difference | no difference | -0.0157 to +0.0067 |
| C2 | Brazil (EWZ) | HAR + credit vs HAR | no difference | worse | worse | +0.0007 to +0.0091 |
| R1 | Brazil (EWZ) | HAR + IV vs HAR | no difference | no difference | no difference | -0.0394 to +0.0844 |
| R2 | Brazil (EWZ) | GJR-GARCH vs HAR + IV | no difference | no difference | no difference | -0.0894 to +0.0733 |


## vix_early

Size of the bias factor exp(s^2) per forecast (median over refits, last table): HMM high-vol probability 1.142; HMM implied vol 1.125; VIX-HMM implied vol 1.113; EWMA vol (0.94) 1.087; trailing 21-day vol 1.095; HAR 1.091; VIX 1.076; HAR + VIX 1.074; HAR + HMM prob 1.099; HAR + VIX + HMM prob 1.082; HAR + VIX + VIX-HMM prob 1.082.

Columns not matched to a captured regression forecast (not variance-scored; in the VIX holdouts table 01 is the raw, uncalibrated table, which no claim uses): variance_01.csv HMM implied vol: closest gap 3.32e-01; variance_01.csv VIX-HMM implied vol: closest gap 2.82e-01; variance_01.csv EWMA vol (0.94): closest gap 7.74e-01; variance_01.csv trailing 21-day vol: closest gap 1.14e+00; variance_01.csv VIX: closest gap 1.07e+00.

Matched columns: 11, of which 11 agree with the committed reproduction to within 1e-9 rather than bit for bit (the committed reproductions were written on another host; a deviation from the plan's 'exact').


### Claim outcomes

| claim | RMSE (registered) | QLIKE (POSTHOC) | QLIKE var |
|---|---|---|---|
| A. VIX improves HAR | holds | holds | holds |
| B. regime adds nothing once the VIX is in | holds | holds | holds |
| C. regime models' own forecasts lose to HAR | holds | not shown | not shown |


### Per-comparison verdicts that differ between the two QLIKE columns (1 of 7)

| claim | block | forecast vs reference | RMSE | QLIKE (POSTHOC) | QLIKE var | dQLIKE var 95% |
|---|---|---|---|---|---|---|
|  | vix_early | HAR + HMM prob vs HAR | no difference | worse | no difference | -0.0003 to +0.0319 |


### Every comparison

| claim | block | forecast vs reference | RMSE | QLIKE (POSTHOC) | QLIKE var | dQLIKE var 95% |
|---|---|---|---|---|---|---|
|  | vix_early | VIX vs HAR | better | better | better | -0.0904 to -0.0156 |
|  | vix_early | HAR + VIX vs HAR | better | better | better | -0.0861 to -0.0263 |
|  | vix_early | HAR + HMM prob vs HAR | no difference | worse | no difference | -0.0003 to +0.0319 |
|  | vix_early | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | no difference | -0.0073 to +0.0121 |
|  | vix_early | HAR + VIX + VIX-HMM prob vs HAR + VIX | no difference | no difference | no difference | -0.0059 to +0.0133 |
|  | vix_early | HMM implied vol vs HAR | worse | worse | worse | +0.0326 to +0.1714 |
|  | vix_early | VIX-HMM implied vol vs HAR | worse | no difference | no difference | -0.0038 to +0.1542 |


## vix_recent

Size of the bias factor exp(s^2) per forecast (median over refits, last table): HMM high-vol probability 1.194; HMM implied vol 1.252; VIX-HMM implied vol 1.280; EWMA vol (0.94) 1.142; trailing 21-day vol 1.160; HAR 1.151; VIX 1.117; HAR + VIX 1.117; HAR + HMM prob 1.166; HAR + VIX + HMM prob 1.138; HAR + VIX + VIX-HMM prob 1.141.

Columns not matched to a captured regression forecast (not variance-scored; in the VIX holdouts table 01 is the raw, uncalibrated table, which no claim uses): variance_01.csv HMM implied vol: closest gap 2.29e-01; variance_01.csv VIX-HMM implied vol: closest gap 3.73e-01; variance_01.csv EWMA vol (0.94): closest gap 7.71e-01; variance_01.csv trailing 21-day vol: closest gap 9.87e-01; variance_01.csv VIX: closest gap 3.94e-01.

Matched columns: 11, of which 11 agree with the committed reproduction to within 1e-9 rather than bit for bit (the committed reproductions were written on another host; a deviation from the plan's 'exact').


### Claim outcomes

| claim | RMSE (registered) | QLIKE (POSTHOC) | QLIKE var |
|---|---|---|---|
| A. VIX improves HAR | holds | not shown | not shown |
| B. regime adds nothing once the VIX is in | holds | holds | fails |
| C. regime models' own forecasts lose to HAR | not shown | not shown | not shown |


### Per-comparison verdicts that differ between the two QLIKE columns (2 of 7)

| claim | block | forecast vs reference | RMSE | QLIKE (POSTHOC) | QLIKE var | dQLIKE var 95% |
|---|---|---|---|---|---|---|
|  | vix_recent | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | better | -0.0396 to -0.0027 |
|  | vix_recent | HMM implied vol vs HAR | no difference | better | no difference | -0.0968 to +0.0066 |


### Every comparison

| claim | block | forecast vs reference | RMSE | QLIKE (POSTHOC) | QLIKE var | dQLIKE var 95% |
|---|---|---|---|---|---|---|
|  | vix_recent | VIX vs HAR | no difference | no difference | no difference | -0.0624 to +0.0553 |
|  | vix_recent | HAR + VIX vs HAR | better | no difference | no difference | -0.0610 to +0.0413 |
|  | vix_recent | HAR + HMM prob vs HAR | no difference | better | better | -0.0641 to -0.0070 |
|  | vix_recent | HAR + VIX + HMM prob vs HAR + VIX | no difference | no difference | better | -0.0396 to -0.0027 |
|  | vix_recent | HAR + VIX + VIX-HMM prob vs HAR + VIX | no difference | no difference | no difference | -0.0008 to +0.0139 |
|  | vix_recent | HMM implied vol vs HAR | no difference | better | no difference | -0.0968 to +0.0066 |
|  | vix_recent | VIX-HMM implied vol vs HAR | no difference | no difference | no difference | -0.0639 to +0.0467 |
