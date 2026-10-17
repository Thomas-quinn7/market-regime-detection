# Reproduction provenance, October 2026

Written by `examples/reproduction_report.py` from the folders beside this file. Class: reproduction. Each spent holdout was re-run once more through `examples/reproduce_holdout.py`, which runs the frozen script's `main()` unchanged and records what it computes. A reproduction checks that the committed numbers come out of the committed code and data; it is not a new test of any claim.

## vix_early

Class: reproduction of a spent holdout; not a test.

- frozen command: `python -u examples/vol_forecast_vix.py --period early` (frozen file sha256 `75f6c84c05e4ea0ab6c67e446046198e8ae476fb9a202383fa2d05ad64956fea`)
- run as: `python -u examples/reproduce_holdout.py vix_early`
- host: pc-lanes (Linux-6.8.0-146-generic-x86_64-with-glibc2.39, 8 CPUs); Python 3.12.3; numpy 2.4.6, pandas 3.0.5, scipy 1.17.1, statsmodels 0.14.6, arch 8.0.0, numba 0.68.0, yfinance 1.5.2
- git: `17476b5aad4be615b1d491de5e4c42716c12ef33`; uncommitted paths at run time: `?? data/MANIFEST.md`, `?? docs/results/audit/`, `?? docs/results/reproductions/`, `?? examples/check_writeup_tables.py`, `?? examples/data_manifest.py`, `?? examples/etf_refit_audit.py`, `?? examples/reproduce_holdout.py`, `?? examples/reproduction_report.py`, `?? tests/test_data_manifest.py`, `?? tests/test_etf_refit_audit.py`, `?? tests/test_reproduce_holdout.py`, `?? tests/test_reproduction_report.py`
- started 2026-10-17T20:21:38+00:00, wall clock 23.3 s
- forecasts saved: 11 regression forecast series, 2 model walk-forwards

Comparison with the committed reference: **identical**

Optimiser calls (reproduction):

| walk-forward | optimiser | calls | converged | not converged |
|---|---|---|---|---|
| walk_forward_oos | statsmodels | 49 | 49 | 0 |

Data files read:

| file | sha256 | bytes | mtime on this host (UTC) |
|---|---|---|---|
| `data/GSPC_1990-01-01_2004-12-31.csv` | `db18ed2cf1125907f9251e1074aa3a4d61c31c7dd45b7c9247b83f08ce7b7978` | 112089 | 2026-10-17T14:44:42+00:00 |
| `data/VIX_1990-01-01_2004-12-31.csv` | `e29461289a03b336d4c414f5fd0e247ec3a167f1cae2196139bf0beffc30a126` | 113620 | 2026-10-17T14:44:42+00:00 |

## vix_recent

Class: reproduction of a spent holdout; not a test.

- frozen command: `python -u examples/vol_forecast_vix.py --period recent` (frozen file sha256 `75f6c84c05e4ea0ab6c67e446046198e8ae476fb9a202383fa2d05ad64956fea`)
- run as: `python -u examples/reproduce_holdout.py vix_recent`
- host: pc-lanes (Linux-6.8.0-146-generic-x86_64-with-glibc2.39, 8 CPUs); Python 3.12.3; numpy 2.4.6, pandas 3.0.5, scipy 1.17.1, statsmodels 0.14.6, arch 8.0.0, numba 0.68.0, yfinance 1.5.2
- git: `17476b5aad4be615b1d491de5e4c42716c12ef33`; uncommitted paths at run time: `?? data/MANIFEST.md`, `?? docs/results/audit/`, `?? docs/results/reproductions/`, `?? examples/check_writeup_tables.py`, `?? examples/data_manifest.py`, `?? examples/etf_refit_audit.py`, `?? examples/reproduce_holdout.py`, `?? examples/reproduction_report.py`, `?? tests/test_data_manifest.py`, `?? tests/test_etf_refit_audit.py`, `?? tests/test_reproduce_holdout.py`, `?? tests/test_reproduction_report.py`
- started 2026-10-17T20:22:02+00:00, wall clock 119.4 s
- forecasts saved: 11 regression forecast series, 2 model walk-forwards

Comparison with the committed reference: **identical**

Optimiser calls (reproduction):

| walk-forward | optimiser | calls | converged | not converged |
|---|---|---|---|---|
| walk_forward_oos | statsmodels | 75 | 75 | 0 |

Data files read:

| file | sha256 | bytes | mtime on this host (UTC) |
|---|---|---|---|
| `data/GSPC_2005-01-01_2026-10-13.csv` | `bf19a9cb5734947ae78bd12c6aa204b2bd9ce52b9dcb363629999e26963ff4c4` | 158945 | 2026-10-17T14:44:42+00:00 |
| `data/VIX_2005-01-01_2026-10-13.csv` | `a48f07522f2f4902663db917d6af3849ba1d7ac615a501305e1e6f9b10dda20d` | 165346 | 2026-10-17T14:44:42+00:00 |

## stock_bond

Class: reproduction of a spent holdout; not a test.

- frozen command: `python -u examples/stock_bond_holdout.py --period holdout` (frozen file sha256 `20878fbecaad3667225fc5d72d7db0359707da621c7fb27876be8742537f2534`)
- run as: `python -u examples/reproduce_holdout.py stock_bond`
- host: pc-lanes (Linux-6.8.0-146-generic-x86_64-with-glibc2.39, 8 CPUs); Python 3.12.3; numpy 2.4.6, pandas 3.0.5, scipy 1.17.1, statsmodels 0.14.6, arch 8.0.0, numba 0.68.0, yfinance 1.5.2
- git: `17476b5aad4be615b1d491de5e4c42716c12ef33`; uncommitted paths at run time: `?? docs/results/reproductions/`, `?? examples/reproduce_holdout.py`
- started 2026-10-17T19:40:55+00:00, wall clock 1165.5 s
- forecasts saved: 0 regression forecast series, 2 model walk-forwards

Comparison with the committed reference: **identical**

Optimiser calls: none observable (this holdout's models use the repo's own EM, which reports no convergence flag).

Data files read:

| file | sha256 | bytes | mtime on this host (UTC) |
|---|---|---|---|
| `data/DGS10_fredgraph.csv` | `624f2a18b0c5642c72dbf8c58cf54b9dcee50d7d8cb3b7809b9416dabd09dd55` | 268999 | 2026-10-14T11:55:45+00:00 |
| `data/GSPC_1962-01-01_2023-12-31.csv` | `7e3273e9bef1c9d1e2bf4428591f3e9a120b66f8b9d613579a52ec40067b0c23` | 461637 | 2026-10-17T14:44:42+00:00 |

## cross_index

Class: reproduction of a spent holdout; not a test.

- frozen command: `python -u examples/cross_index_holdout.py` (frozen file sha256 `edcb9665e537cf5b7311a8c1f55ea48e8465fb84728b994a20d6f4bfc2c7e0e7`)
- run as: `python -u examples/reproduce_holdout.py cross_index`
- host: pc-lanes (Linux-6.8.0-146-generic-x86_64-with-glibc2.39, 8 CPUs); Python 3.12.3; numpy 2.4.6, pandas 3.0.5, scipy 1.17.1, statsmodels 0.14.6, arch 8.0.0, numba 0.68.0, yfinance 1.5.2
- git: `17476b5aad4be615b1d491de5e4c42716c12ef33`; uncommitted paths at run time: `?? data/MANIFEST.md`, `?? docs/results/audit/`, `?? docs/results/reproductions/`, `?? examples/check_writeup_tables.py`, `?? examples/data_manifest.py`, `?? examples/etf_refit_audit.py`, `?? examples/reproduce_holdout.py`, `?? examples/reproduction_report.py`, `?? tests/test_data_manifest.py`, `?? tests/test_etf_refit_audit.py`, `?? tests/test_reproduce_holdout.py`, `?? tests/test_reproduction_report.py`
- started 2026-10-17T20:21:38+00:00, wall clock 478.9 s
- forecasts saved: 30 regression forecast series, 9 model walk-forwards
- note: Databento bar files absent on this host: MARKET_DATA_DIR pointed at empty placeholder files; RV read from the committed data/*_rv_5min.csv caches, as cached_daily_rv does whenever the cache exists.

Comparison with the committed reference: **differs in 6 lines**

Per-asset verdict labels (RMSE and QLIKE, every claim row): 27 rows compared, 0 changed.

```
--- committed
+++ reproduction
@@ -5 +5 @@
-  last MSM fit: m0 1.504, sigma 1.786, b 3.798, gamma_k 0.054
+  last MSM fit: m0 1.504, sigma 1.786, b 3.795, gamma_k 0.054
@@ -34 +34 @@
-  last MSM fit: m0 1.511, sigma 1.929, b 4.558, gamma_k 0.077
+  last MSM fit: m0 1.511, sigma 1.929, b 4.559, gamma_k 0.077
@@ -63 +63 @@
-  last MSM fit: m0 1.424, sigma 2.233, b 3.046, gamma_k 0.032
+  last MSM fit: m0 1.424, sigma 2.233, b 3.047, gamma_k 0.032
```

Optimiser calls (reproduction):

| walk-forward | optimiser | calls | converged | not converged |
|---|---|---|---|---|
| walk_forward_gjr | arch | 285 | 285 | 0 |
| walk_forward_msm | scipy | 1290 | 1290 | 0 |
| walk_forward_oos | statsmodels | 285 | 285 | 0 |

Data files read:

| file | sha256 | bytes | mtime on this host (UTC) |
|---|---|---|---|
| `data/DJI_2000-01-01_2026-10-13.csv` | `de065b250814b446da7417ddf9c16815f62361d4cd8d45395c7618e6fb3f63dc` | 183050 | 2026-10-17T14:44:42+00:00 |
| `data/NDX_2000-01-01_2026-10-13.csv` | `5eb8b56f209a42d3ec4d99ab5ec6b7524e275a24cd928a55eb9a774d94eabaf6` | 192622 | 2026-10-17T14:44:42+00:00 |
| `data/RUT_2000-01-01_2026-10-13.csv` | `f3912a01475da2a3b79a897f31467c5e96001b5ab6b8b3be62587f3b42a3ff11` | 197946 | 2026-10-17T14:44:42+00:00 |
| `data/fred_RVXCLS.csv` | `35478830566fbec403c62aa349737b077b40e9054931ecf08549c7de0cd139b4` | 99968 | 2026-10-17T14:44:42+00:00 |
| `data/fred_VXDCLS.csv` | `f9e3939a6e4920077de198bcdee152b1eb0a8a3ba598c7eb43207f9cd52f01b9` | 127305 | 2026-10-17T14:44:42+00:00 |
| `data/fred_VXNCLS.csv` | `76f11fac54b408e8e7a86627126183f380bd852755527ebfd808c337a9398223` | 112765 | 2026-10-17T14:44:42+00:00 |
| `data/nq_rv_5min.csv` | `75ee2efd8b4860914ac5c09c18384a490bf1cfd184865c5038cf870fd686f270` | 384575 | 2026-10-17T14:44:42+00:00 |
| `data/rty_rv_5min.csv` | `125e87d69132a47cccaaac13cee52d7cf938c7af912fa29e83c03a56d3e4fdf9` | 216872 | 2026-10-17T14:44:42+00:00 |
| `data/ym_rv_5min.csv` | `4f59dc3f5812fd09f886f8b16e84da1c99f1059eaa6ea4d472170eec1d5cc7ed` | 388897 | 2026-10-17T14:44:42+00:00 |

## etf

Class: reproduction of a spent holdout; not a test.

- frozen command: `python -u examples/msgarch_credit_holdout.py` (frozen file sha256 `cc9b71de94de880c9a6372fe833f2cc042f64af88b3e4d4159099b34f2f0363d`)
- run as: `python -u examples/reproduce_holdout.py etf`
- host: pc-lanes (Linux-6.8.0-146-generic-x86_64-with-glibc2.39, 8 CPUs); Python 3.12.3; numpy 2.4.6, pandas 3.0.5, scipy 1.17.1, statsmodels 0.14.6, arch 8.0.0, numba 0.68.0, yfinance 1.5.2
- git: `17476b5aad4be615b1d491de5e4c42716c12ef33`; uncommitted paths at run time: `?? data/MANIFEST.md`, `?? docs/results/audit/`, `?? docs/results/reproductions/`, `?? examples/check_writeup_tables.py`, `?? examples/data_manifest.py`, `?? examples/etf_refit_audit.py`, `?? examples/reproduce_holdout.py`, `?? examples/reproduction_report.py`, `?? tests/test_data_manifest.py`, `?? tests/test_etf_refit_audit.py`, `?? tests/test_reproduce_holdout.py`, `?? tests/test_reproduction_report.py`
- started 2026-10-17T20:21:38+00:00, wall clock 970.9 s
- forecasts saved: 36 regression forecast series, 12 model walk-forwards
- note: walk-forward checkpoints redirected to an empty directory: every HMM, GJR-GARCH and MS-GARCH walk-forward refitted from scratch.

Comparison with the committed reference: **differs in 48 lines**

Per-asset verdict labels (RMSE and QLIKE, every claim row): 36 rows compared, 0 changed.

```
--- committed
+++ reproduction
@@ -16,2 +16,2 @@
-MS-GARCH                   0.988  0.345    0.575
-HAR + IV + MS-GARCH        0.868  0.251    0.682
+MS-GARCH                   0.988  0.346    0.574
+HAR + IV + MS-GARCH        0.868  0.251    0.683
@@ -21,3 +21,3 @@
-   M1                 MS-GARCH                 GJR-GARCH     better -0.016 to +0.046 no difference -0.022 to +0.007 no difference
-   M2      HAR + IV + MS-GARCH                  HAR + IV     better +0.000 to +0.024         worse +0.001 to +0.010         worse
-   M3                 MS-GARCH Two-state HMM implied vol     better -0.277 to +0.122 no difference -0.323 to -0.004        better
+   M1                 MS-GARCH                 GJR-GARCH     better -0.015 to +0.047 no difference -0.021 to +0.008 no difference
+   M2      HAR + IV + MS-GARCH                  HAR + IV     better +0.000 to +0.022         worse +0.001 to +0.009         worse
+   M3                 MS-GARCH Two-state HMM implied vol     better -0.277 to +0.123 no difference -0.322 to -0.003        better
@@ -25 +25 @@
-   M5                 MS-GARCH                  HAR + IV     better +0.038 to +0.240         worse +0.034 to +0.181         worse
+   M5                 MS-GARCH                  HAR + IV     better +0.039 to +0.240         worse +0.034 to +0.182         worse
@@ -45,3 +45,3 @@
-MS-GARCH                   0.370  0.251    0.540
-HAR + IV + MS-GARCH        0.345  0.224    0.623
-HAR + IV + MS-GARCH prob   0.349  0.231    0.614
+MS-GARCH                   0.371  0.251    0.540
+HAR + IV + MS-GARCH        0.345  0.225    0.624
+HAR + IV + MS-GARCH prob   0.349  0.230    0.615
@@ -50,5 +50,5 @@
-   M1                 MS-GARCH                 GJR-GARCH     better -0.007 to +0.011 no difference -0.013 to +0.015 no difference
-   M2      HAR + IV + MS-GARCH                  HAR + IV     better -0.000 to +0.001 no difference -0.000 to +0.003 no difference
-   M3                 MS-GARCH Two-state HMM implied vol     better -0.044 to -0.002        better -0.064 to +0.024 no difference
-   M4 HAR + IV + MS-GARCH prob                  HAR + IV     better -0.001 to +0.011 no difference -0.001 to +0.018 no difference
-   M5                 MS-GARCH                  HAR + IV     better +0.013 to +0.038         worse -0.009 to +0.060 no difference
+   M1                 MS-GARCH                 GJR-GARCH     better -0.006 to +0.011 no difference -0.014 to +0.013 no difference
+   M2      HAR + IV + MS-GARCH                  HAR + IV     better -0.001 to +0.002 no difference -0.001 to +0.003 no difference
+   M3                 MS-GARCH Two-state HMM implied vol     better -0.043 to -0.002        better -0.064 to +0.021 no difference
+   M4 HAR + IV + MS-GARCH prob                  HAR + IV     better -0.001 to +0.010 no difference -0.001 to +0.018 no difference
+   M5                 MS-GARCH                  HAR + IV     better +0.013 to +0.039         worse -0.011 to +0.059 no difference
@@ -64 +64 @@
-  MS-GARCH: last fit p00 0.9950, p11 0.9964, nu 14.8 / 9.8, loglik -9939.0
+  MS-GARCH: last fit p00 0.9950, p11 0.9964, nu 14.9 / 9.8, loglik -9939.0
@@ -79 +79 @@
-   M1                 MS-GARCH                 GJR-GARCH     better -0.029 to +0.006 no difference -0.005 to +0.029 no difference
+   M1                 MS-GARCH                 GJR-GARCH     better -0.029 to +0.006 no difference -0.006 to +0.029 no difference
@@ -93 +93 @@
-  MS-GARCH: last fit p00 0.9933, p11 0.9877, nu 28.3 / 6.1, loglik -13834.5
+  MS-GARCH: last fit p00 0.9932, p11 0.9876, nu 28.3 / 6.1, loglik -13834.5
@@ -103,2 +103,2 @@
-MS-GARCH                   0.931  0.361    0.348
-HAR + IV + MS-GARCH        0.870  0.318    0.481
+MS-GARCH                   0.926  0.365    0.366
+HAR + IV + MS-GARCH        0.875  0.320    0.477
@@ -108,5 +108,5 @@
-   M1                 MS-GARCH                 GJR-GARCH     better -0.061 to +0.063 no difference -0.022 to +0.089 no difference
-   M2      HAR + IV + MS-GARCH                  HAR + IV     better +0.001 to +0.006         worse -0.001 to +0.005 no difference
-   M3                 MS-GARCH Two-state HMM implied vol     better -0.053 to +0.021 no difference -0.079 to -0.010        better
-   M4 HAR + IV + MS-GARCH prob                  HAR + IV     better -0.026 to +0.005 no difference -0.025 to +0.014 no difference
-   M5                 MS-GARCH                  HAR + IV     better +0.026 to +0.122         worse -0.011 to +0.093 no difference
+   M1                 MS-GARCH                 GJR-GARCH     better -0.058 to +0.051 no difference -0.015 to +0.093 no difference
+   M2      HAR + IV + MS-GARCH                  HAR + IV     better +0.003 to +0.015         worse -0.002 to +0.011 no difference
+   M3                 MS-GARCH Two-state HMM implied vol     better -0.063 to +0.019 no difference -0.074 to -0.003        better
+   M4 HAR + IV + MS-GARCH prob                  HAR + IV     better -0.028 to +0.005 no difference -0.023 to +0.014 no difference
+   M5                 MS-GARCH                  HAR + IV     better +0.023 to +0.116         worse -0.003 to +0.094 no difference
```

Optimiser calls (reproduction):

| walk-forward | optimiser | calls | converged | not converged |
|---|---|---|---|---|
| walk_forward_gjr | arch | 321 | 321 | 0 |
| walk_forward_msgarch | scipy | 1462 | 1439 | 23 |
| walk_forward_oos | statsmodels | 321 | 321 | 0 |

Refitted walk-forward files against the frozen run's checkpoints: 0 of 20 byte-identical.

- `brazil_ewz__garch__2026-10-12__6599.csv`: differs, max abs difference 9.35e-05
- `brazil_ewz__garch__2026-10-12__6599.params.csv`: differs, max abs difference 0.0015
- `brazil_ewz__hmm__2026-10-12__6599.csv`: differs, max abs difference 4.36e-11
- `brazil_ewz__ms_garch__2026-10-12__6599.csv`: differs, max abs difference 8.68
- `brazil_ewz__ms_garch__2026-10-12__6599.params.csv`: differs, max abs difference 6.6e+08
- `crude_oil_uso__garch__2026-10-12__5158.csv`: differs, max abs difference 0.0141
- `crude_oil_uso__garch__2026-10-12__5158.params.csv`: differs, max abs difference 66.9
- `crude_oil_uso__hmm__2026-10-12__5158.csv`: differs, max abs difference 6.14e-12
- `crude_oil_uso__ms_garch__2026-10-12__5158.csv`: differs, max abs difference 0.0512
- `crude_oil_uso__ms_garch__2026-10-12__5158.params.csv`: differs, max abs difference 5.25e+03
- `emerging_markets_eem__garch__2026-10-12__5911.csv`: differs, max abs difference 0.000972
- `emerging_markets_eem__garch__2026-10-12__5911.params.csv`: differs, max abs difference 0.238
- `emerging_markets_eem__hmm__2026-10-12__5911.csv`: differs, max abs difference 6.19e-13
- `emerging_markets_eem__ms_garch__2026-10-12__5911.csv`: differs, max abs difference 0.148
- `emerging_markets_eem__ms_garch__2026-10-12__5911.params.csv`: differs, max abs difference 1.01e+04
- `gold_gld__garch__2026-10-12__5507.csv`: differs, max abs difference 8.87e-05
- `gold_gld__garch__2026-10-12__5507.params.csv`: differs, max abs difference 0.00174
- `gold_gld__hmm__2026-10-12__5507.csv`: differs, max abs difference 8.82e-13
- `gold_gld__ms_garch__2026-10-12__5507.csv`: differs, max abs difference 0.408
- `gold_gld__ms_garch__2026-10-12__5507.params.csv`: differs, max abs difference 9.92e+04

Data files read:

| file | sha256 | bytes | mtime on this host (UTC) |
|---|---|---|---|
| `data/EEM_2000-01-01_2026-10-13.csv` | `2ee15313ec37a6161cc8861273aeb0502e20fba8c8a70f21b565729ba22f6030` | 173694 | 2026-10-14T12:17:28+00:00 |
| `data/EWZ_2000-01-01_2026-10-13.csv` | `aa788cdbac3e32c079defba9f1466945ad2d379112c3b2d5ac796cbf08ce7f7d` | 194403 | 2026-10-14T12:20:50+00:00 |
| `data/GLD_2000-01-01_2026-10-13.csv` | `0e8f882dd0ab9792900c284471f0b9ca456aef706428ce5ca45894fb82f6544c` | 159554 | 2026-10-14T12:14:55+00:00 |
| `data/USO_2000-01-01_2026-10-13.csv` | `53a31cae66a44c0bef0d813bef58cc0c72372e0dbde1dfcf20212d5cc9a3049f` | 147406 | 2026-10-14T12:12:16+00:00 |
| `data/fred_BAA10Y.csv` | `d68146535f8f2951a29f2854a1bd5eeac1bc67c4d92f4a471eaa9ba8dff68aed` | 168428 | 2026-10-14T11:55:54+00:00 |
| `data/fred_GVZCLS.csv` | `4ad6cbd527c52ec9881592d4f68382831e8fdad16d69d4b313a89b9d5440538e` | 80549 | 2026-10-14T12:14:55+00:00 |
| `data/fred_OVXCLS.csv` | `a15a52e6cc3f73f1b3dd1677f496b8eb9ce0d2f1ff795dca2d36de315c3129f5` | 85333 | 2026-10-14T12:12:16+00:00 |
| `data/fred_VXEEMCLS.csv` | `c21653450ca481d45cacd0c36cba5ab98d4441091f210b50d8133e1ec09ef9dc` | 68379 | 2026-10-14T12:17:29+00:00 |
| `data/fred_VXEWZCLS.csv` | `6977c3b5b6eda7db61f115ccfd7e31f9ef208b46a5cf94451b9294f1d19cad86` | 68389 | 2026-10-14T12:20:50+00:00 |

## etf_frozen_checkpoints

Class: reproduction of a spent holdout; not a test.

- frozen command: `python -u examples/msgarch_credit_holdout.py` (frozen file sha256 `cc9b71de94de880c9a6372fe833f2cc042f64af88b3e4d4159099b34f2f0363d`)
- run as: `python -u examples/reproduce_holdout.py etf --use-checkpoints --out docs/results/reproductions/etf_frozen_checkpoints`
- host: pc-lanes (Linux-6.8.0-146-generic-x86_64-with-glibc2.39, 8 CPUs); Python 3.12.3; numpy 2.4.6, pandas 3.0.5, scipy 1.17.1, statsmodels 0.14.6, arch 8.0.0, numba 0.68.0, yfinance 1.5.2
- git: `17476b5aad4be615b1d491de5e4c42716c12ef33`; uncommitted paths at run time: `?? data/MANIFEST.md`, `?? docs/results/audit/`, `?? docs/results/reproductions/`, `?? examples/check_writeup_tables.py`, `?? examples/data_manifest.py`, `?? examples/etf_refit_audit.py`, `?? examples/reproduce_holdout.py`, `?? examples/reproduction_report.py`, `?? tests/test_data_manifest.py`, `?? tests/test_etf_refit_audit.py`, `?? tests/test_reproduce_holdout.py`, `?? tests/test_reproduction_report.py`
- started 2026-10-17T20:29:52+00:00, wall clock 4.6 s
- forecasts saved: 36 regression forecast series, 0 model walk-forwards

Comparison with the committed reference: **differs in 28 lines**

Per-asset verdict labels (RMSE and QLIKE, every claim row): 36 rows compared, 0 changed.

```
--- committed
+++ reproduction
@@ -4,4 +4,3 @@
-  hmm: 70 refits
-  garch: 70 refits
-  MS-GARCH: last fit p00 0.9975, p11 0.9965, nu 21.2 / 5.9, loglik -10673.2
-  MS-GARCH: 70 refits
+  hmm: loaded from crude_oil_uso__hmm__2026-10-12__5158.csv
+  garch: loaded from crude_oil_uso__garch__2026-10-12__5158.csv
+  MS-GARCH: loaded from crude_oil_uso__ms_garch__2026-10-12__5158.csv
@@ -33,4 +32,3 @@
-  hmm: 76 refits
-  garch: 76 refits
-  MS-GARCH: last fit p00 0.9948, p11 0.9902, nu 5.4 / 7.1, loglik -7770.0
-  MS-GARCH: 76 refits
+  hmm: loaded from gold_gld__hmm__2026-10-12__5507.csv
+  garch: loaded from gold_gld__garch__2026-10-12__5507.csv
+  MS-GARCH: loaded from gold_gld__ms_garch__2026-10-12__5507.csv
@@ -62,4 +60,3 @@
-  hmm: 82 refits
-  garch: 82 refits
-  MS-GARCH: last fit p00 0.9950, p11 0.9964, nu 14.8 / 9.8, loglik -9939.0
-  MS-GARCH: 82 refits
+  hmm: loaded from emerging_markets_eem__hmm__2026-10-12__5911.csv
+  garch: loaded from emerging_markets_eem__garch__2026-10-12__5911.csv
+  MS-GARCH: loaded from emerging_markets_eem__ms_garch__2026-10-12__5911.csv
@@ -91,4 +88,3 @@
-  hmm: 93 refits
-  garch: 93 refits
-  MS-GARCH: last fit p00 0.9933, p11 0.9877, nu 28.3 / 6.1, loglik -13834.5
-  MS-GARCH: 93 refits
+  hmm: loaded from brazil_ewz__hmm__2026-10-12__6599.csv
+  garch: loaded from brazil_ewz__garch__2026-10-12__6599.csv
+  MS-GARCH: loaded from brazil_ewz__ms_garch__2026-10-12__6599.csv
```

Optimiser calls: none observable (this holdout's models use the repo's own EM, which reports no convergence flag).

Data files read:

| file | sha256 | bytes | mtime on this host (UTC) |
|---|---|---|---|
| `data/EEM_2000-01-01_2026-10-13.csv` | `2ee15313ec37a6161cc8861273aeb0502e20fba8c8a70f21b565729ba22f6030` | 173694 | 2026-10-14T12:17:28+00:00 |
| `data/EWZ_2000-01-01_2026-10-13.csv` | `aa788cdbac3e32c079defba9f1466945ad2d379112c3b2d5ac796cbf08ce7f7d` | 194403 | 2026-10-14T12:20:50+00:00 |
| `data/GLD_2000-01-01_2026-10-13.csv` | `0e8f882dd0ab9792900c284471f0b9ca456aef706428ce5ca45894fb82f6544c` | 159554 | 2026-10-14T12:14:55+00:00 |
| `data/USO_2000-01-01_2026-10-13.csv` | `53a31cae66a44c0bef0d813bef58cc0c72372e0dbde1dfcf20212d5cc9a3049f` | 147406 | 2026-10-14T12:12:16+00:00 |
| `data/checkpoints/msgarch_credit/brazil_ewz__garch__2026-10-12__6599.csv` | `9c4ac2c4139005d194b05e4390f58024d84f5f4a895b1147bf718bd9dba38107` | 173060 | 2026-10-14T12:21:37+00:00 |
| `data/checkpoints/msgarch_credit/brazil_ewz__garch__2026-10-12__6599.params.csv` | `b6b8039668d77771b16314bc97e506b4d9bb832aaa154c3fed995b22b136a82c` | 11918 | 2026-10-14T12:21:37+00:00 |
| `data/checkpoints/msgarch_credit/brazil_ewz__hmm__2026-10-12__6599.csv` | `e0cf445372602c724647e29a052f0f65bc3482dec239dca1ce98985ffa958593` | 290821 | 2026-10-14T12:21:35+00:00 |
| `data/checkpoints/msgarch_credit/brazil_ewz__ms_garch__2026-10-12__6599.csv` | `c876f13a85d292929d00b22fee8c0cc6f961e2f13d3a3b68614cf83f67418f12` | 273528 | 2026-10-14T12:25:00+00:00 |
| `data/checkpoints/msgarch_credit/brazil_ewz__ms_garch__2026-10-12__6599.params.csv` | `f4b414aaf4858eb0c4cc32ab31d13717882a1d2a3885a669e03fab62b08b4bfb` | 25124 | 2026-10-14T12:25:00+00:00 |
| `data/checkpoints/msgarch_credit/crude_oil_uso__garch__2026-10-12__5158.csv` | `a6e31883483e267328dbf20e60120372fecad9b6a6086b40226e757bd644cb8b` | 130442 | 2026-10-14T12:12:45+00:00 |
| `data/checkpoints/msgarch_credit/crude_oil_uso__garch__2026-10-12__5158.params.csv` | `4155ca2a79a75981c559026808f22454d3ab4ed93d73c0b806a3de3504e19dd7` | 9153 | 2026-10-14T12:12:45+00:00 |
| `data/checkpoints/msgarch_credit/crude_oil_uso__hmm__2026-10-12__5158.csv` | `7980601324921e848dd33b774ac98918c22cedde8d13679a487d8678769fa0f9` | 219603 | 2026-10-14T12:12:44+00:00 |
| `data/checkpoints/msgarch_credit/crude_oil_uso__ms_garch__2026-10-12__5158.csv` | `b19c2d9af3cb44fbf8c8935ed2575df0fbc7c589eed5c571b5d5429b047b9f3f` | 217200 | 2026-10-14T12:14:54+00:00 |
| `data/checkpoints/msgarch_credit/crude_oil_uso__ms_garch__2026-10-12__5158.params.csv` | `f726525618d3f5471474daf340c3fc17e6d2f46ab40de5c26bd11dcbab78d468` | 18623 | 2026-10-14T12:14:54+00:00 |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__garch__2026-10-12__5911.csv` | `9d79feb19c454dc4d565997342c9bdbfd5f4f68de7b88f3206edcb1511bae70a` | 153209 | 2026-10-14T12:18:03+00:00 |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__garch__2026-10-12__5911.params.csv` | `2b49d8c461173ebf2a14c39d35ab220760db9597e6d7b75ff6222bc8adf322de` | 10551 | 2026-10-14T12:18:03+00:00 |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__hmm__2026-10-12__5911.csv` | `f4c22ab6235f8393fca4fb7124e387a8f06854abce80ea2e9453ddf0340abf1f` | 259107 | 2026-10-14T12:18:02+00:00 |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__ms_garch__2026-10-12__5911.csv` | `009c040ef43ed11362866d3014d8406f6e60bbcb87eef37dcfa73fc123d513b9` | 253177 | 2026-10-14T12:20:49+00:00 |
| `data/checkpoints/msgarch_credit/emerging_markets_eem__ms_garch__2026-10-12__5911.params.csv` | `36fc120b77ecd24bf1d00cef0927e08022f8ea00ae95b68ed07f3b7713cae0c3` | 21794 | 2026-10-14T12:20:49+00:00 |
| `data/checkpoints/msgarch_credit/gold_gld__garch__2026-10-12__5507.csv` | `762bf544f2cdd73e3d7d6403e785047bbf786a3b2857b369f56c25d5ae6fc7a5` | 141574 | 2026-10-14T12:15:26+00:00 |
| `data/checkpoints/msgarch_credit/gold_gld__garch__2026-10-12__5507.params.csv` | `08830838488f70be9375e6209218ca0ee3565c68b587d1e70bf3ba8914613695` | 9942 | 2026-10-14T12:15:26+00:00 |
| `data/checkpoints/msgarch_credit/gold_gld__hmm__2026-10-12__5507.csv` | `4b9a2b3ed1d30329862e908c985be94da97ed5f3c7381ab061c9929f23c0fcf3` | 236767 | 2026-10-14T12:15:24+00:00 |
| `data/checkpoints/msgarch_credit/gold_gld__ms_garch__2026-10-12__5507.csv` | `5963c8b1e8def805a714489e091ef95c4e081ebf2061300ad9d28c242c76585b` | 234801 | 2026-10-14T12:17:27+00:00 |
| `data/checkpoints/msgarch_credit/gold_gld__ms_garch__2026-10-12__5507.params.csv` | `91df92b34d490db2e5178f736e542e047cdd0c9652670ac9f9832c2d0e8903c6` | 20486 | 2026-10-14T12:17:27+00:00 |
| `data/fred_BAA10Y.csv` | `d68146535f8f2951a29f2854a1bd5eeac1bc67c4d92f4a471eaa9ba8dff68aed` | 168428 | 2026-10-14T11:55:54+00:00 |
| `data/fred_GVZCLS.csv` | `4ad6cbd527c52ec9881592d4f68382831e8fdad16d69d4b313a89b9d5440538e` | 80549 | 2026-10-14T12:14:55+00:00 |
| `data/fred_OVXCLS.csv` | `a15a52e6cc3f73f1b3dd1677f496b8eb9ce0d2f1ff795dca2d36de315c3129f5` | 85333 | 2026-10-14T12:12:16+00:00 |
| `data/fred_VXEEMCLS.csv` | `c21653450ca481d45cacd0c36cba5ab98d4441091f210b50d8133e1ec09ef9dc` | 68379 | 2026-10-14T12:17:29+00:00 |
| `data/fred_VXEWZCLS.csv` | `6977c3b5b6eda7db61f115ccfd7e31f9ef208b46a5cf94451b9294f1d19cad86` | 68389 | 2026-10-14T12:20:50+00:00 |
