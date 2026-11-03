# QLIKE on variance forecasts and the Giacomini-White conditional test (post hoc)

Class: **post hoc**. Everything here is computed from the four spent holdouts' reproduced forecasts.
None of it is a registered test, and no holdout was opened or re-run on new data. The plan,
`docs/GW_QLIKE_PLAN_2026-11.md`, was committed before any real-data run (b953395, wording fix
4e9e408). Amendment A1 (HAC kernel) was committed after the synthetic size check and before any
real-data GW run (a04554d).

Detailed outputs:

- `docs/results/variance_rescore/RESULTS.md`, written by `examples/variance_rescore.py score`
- `docs/results/gw_conditional/RESULTS.md`, plus `gw_conditional.csv`, `size_check.csv` and
  `dm_kernel_note.csv`, written by `examples/gw_conditional.py`

To reproduce:

```
python -u examples/variance_rescore.py capture vix_early     # also vix_recent, etf, cross_index (about 20 min, MSM refits)
python examples/variance_rescore.py score
python examples/gw_conditional.py
```

## Short version

1. **The POSTHOC QLIKE scores used variance forecasts that were biased low by 6 to 28%.**
   `walk_forward_regression(log_target=True)` returns the lognormal mean of vol, `exp(fit + s^2/2)`.
   Squaring that for QLIKE gives a variance forecast too low by the factor `exp(s^2)`. The median
   factor per forecast is 1.06 to 1.14 in the cross-index, ETF and VIX 1996-2004 holdouts, and 1.12
   to 1.28 in VIX 2024-2026. QLIKE punishes under-forecasts, so the bias was not neutral.
2. **Two claim outcomes change when QLIKE is scored on the correct variance forecast,
   `exp(2 fit + 2 s^2)`.**
   - ETF R1 (implied vol improves HAR): mixed under POSTHOC QLIKE becomes confirmed, the same as
     the registered RMSE outcome. Gold moves from no difference to better (dQLIKE -0.0720 to
     -0.0027).
   - VIX 2024-2026 claim B (the regime adds nothing once the VIX is in): holds becomes **fails**.
     HAR + VIX + HMM prob beats HAR + VIX, dQLIKE -0.0396 to -0.0027. Under RMSE and under POSTHOC
     QLIKE this comparison is no difference.

   Every other scored claim keeps its POSTHOC QLIKE outcome. In particular, cross-index R1 stays
   rejected.
3. **The Giacomini-White test finds no state-dependent gain from any regime model in the primary
   family.** There are 36 primary tests (squared error and POSTHOC QLIKE). Seven reject after Holm.
   None is a lead under the plan's reading rule (Holm rejection and the gain at p = 1 wholly below
   zero). In four of the seven, the stress end of the instrument favours the *reference*: the HMM's
   own forecast loses more when the HMM says high vol (Russell 2000 and S&P 500 1996-2004, both
   losses). One of the seven (Brazil G1, squared error) depends on the kernel and does not survive
   a Bartlett 63 covariance (p = 0.373).
4. **The VIX 2024-2026 G1 result from point 2 shows up again in the secondary family** (QLIKE var,
   Holm p = 0.015). Its shape is not "the regime helps in stress". The estimated gain is negative at
   both ends of p and neither interval excludes zero. The share of days with p >= 0.5 is 13%, and
   the sample is 676 days, the length at which the size check shows the test running at 7.4%
   rather than 5%.

## Part 1: QLIKE on variance forecasts

### What changed in the scoring

For each regression forecast, a twin of `walk_forward_regression` refits the same OLS on the same
embargoed rows and also returns the variance forecast:

- log target: `exp(2 fit + 2 s^2)`, the lognormal second moment;
- level target: `fit^2 + s^2`.

The twin's mean forecast equalled the original exactly on every call:

| Holdout | Regression calls |
|---|---|
| VIX 1996-2004 | 11 |
| VIX 2024-2026 | 11 |
| ETF | 36 |
| Cross-index | 30 |

Each committed scored column was then matched to one captured forecast. The scoring (paired
circular block bootstrap, 63-day blocks, 2,000 draws, seed 0) and the claim rules are the ones
POSTHOC uses.

### Median bias factor exp(s^2) per forecast

| Holdout | Range over forecasts |
|---|---|
| Cross-index | 1.064 to 1.115 |
| ETF | 1.069 to 1.136 |
| VIX 1996-2004 | 1.074 to 1.142 |
| VIX 2024-2026 | 1.117 to 1.280 |

The regime-model forecasts carry the largest factors (Two-state HMM implied vol 1.115 to 1.126 on
cross-index and ETF; HMM implied vol 1.252 and VIX-HMM implied vol 1.280 in VIX 2024-2026). So the
POSTHOC convention penalised them most.

### Claim outcomes (RMSE is the registered measure; both QLIKE columns are post hoc)

| Holdout | Claim | RMSE (registered) | QLIKE (POSTHOC) | QLIKE var |
|---|---|---|---|---|
| Cross-index | P1, P2 | rejected | rejected | rejected |
| Cross-index | P3, P4 | rejected | rejected | not scored |
| Cross-index | P5 | mixed | mixed | not scored |
| Cross-index | R1 | mixed | rejected | rejected |
| Cross-index | R2 | confirmed | confirmed | confirmed |
| Cross-index | R3 | holds | holds | holds |
| Cross-index | R4 | holds | holds | not scored |
| ETF | M1, M2, M4, M5, C2 | rejected | rejected | rejected |
| ETF | M3 | confirmed | confirmed | confirmed |
| ETF | C1, R2 | holds | holds | holds |
| ETF | R1 | confirmed | mixed | **confirmed** |
| VIX 1996-2004 | A, B | holds | holds | holds |
| VIX 1996-2004 | C | holds | not shown | not shown |
| VIX 2024-2026 | A | holds | not shown | not shown |
| VIX 2024-2026 | B | holds | holds | **fails** |
| VIX 2024-2026 | C | not shown | not shown | not shown |

Under the plan's reading rule, where the two QLIKE versions disagree the paper should quote QLIKE
var.

### Deviations from the plan, and coverage

- **Matching tolerance.** The plan says each column must match a captured forecast exactly. No
  column matched bit for bit, because the committed reproductions were written on another host
  (pc-lanes). Every matched column instead agrees with exactly one captured forecast to within 1e-9.
  The largest gaps are:

  | Holdout | Largest gap |
  |---|---|
  | Cross-index | 2.5e-11 |
  | ETF | 2.8e-14 |
  | VIX 1996-2004 | 8.0e-12 |
  | VIX 2024-2026 | 4.8e-12 |

  The match is labelled "within 1e-9" in every `capture.json`.
- **Not scored.** In the cross-index holdout, GJR-GARCH, MSM and the combination are not regression
  forecasts, so they have no regression variance to score. HAR-RV + IV + MSM is a regression, but
  it does not match the committed reproduction: the MSM refits differ across hosts by up to about
  5e-4, giving a closest gap of 1.5e-5 to 6.6e-5. Under the plan these are reported and left out,
  so P3, P4, P5 and R4 are not scored under QLIKE var. In the VIX holdouts, scored table 1 is the
  raw, uncalibrated table and no claim uses it. Everything in table 2 matched.

## Part 2: Giacomini-White conditional test

The test is on d_t = loss(forecast) - loss(reference), with instruments h_t = (1, p_t). Here p_t is
the walk-forward HMM's filtered high-vol probability on the forecast date. The statistic is
`T Zbar' Omega^-1 Zbar` against chi-squared(2). The pairs:

- **G1:** the regime term added to the benchmark against the benchmark. This is the HMM probability
  on cross-index and VIX, and the MS-GARCH probability on the ETFs.
- **G2:** the two-state HMM's own forecast against the benchmark.

That gives 9 blocks x 2 pairs x 2 losses = 36 primary tests with Holm at 5%. QLIKE var is a
secondary family of 18 tests with its own Holm.

### Kernel (amendment A1)

The plan's Bartlett 20-lag covariance was oversized on synthetic nulls built like the holdouts
(MA(20) Student-t losses and a persistent probability). The rectangular 20-lag kernel holds size
much better:

| Days | Rectangular 20 (used) | Bartlett 20 (planned) |
|---|---|---|
| 676 | 0.074 | 0.166 |
| 2,228 | 0.054 | 0.158 |
| 3,300 | 0.052 | 0.122 |

The rectangular covariance was positive definite in every real block, so the Bartlett 63 fallback
was never used. Bartlett 20 and Bartlett 63 p-values are printed as kernel diagnostics only.

### Primary family: 7 Holm rejections, 0 leads

| Block | Pair | Loss | Holm p | d at p=0 (95%) | d at p=1 (95%) | Reading |
|---|---|---|---|---|---|---|
| S&P 500 1996-2004 | G2 | squared error | 0.000 | +0.0235 (+0.0004, +0.0466) | +0.0971 (+0.0250, +0.1691) | against: HMM forecast loses, more in stress |
| Russell 2000 | G2 | QLIKE | 0.007 | +0.0616 (+0.0031, +0.1201) | +0.0989 (+0.0324, +0.1654) | against |
| S&P 500 1996-2004 | G2 | QLIKE | 0.011 | +0.1595 (+0.0509, +0.2680) | +0.1760 (+0.0199, +0.3322) | against |
| Russell 2000 | G2 | squared error | 0.043 | +0.0149 (-0.0122, +0.0420) | +0.1755 (+0.0692, +0.2819) | against |
| Gold (GLD) | G2 | squared error | 0.019 | +0.0257 (+0.0077, +0.0438) | +0.0750 (-0.0082, +0.1583) | HMM forecast loses in calm states |
| Crude oil (USO) | G2 | squared error | 0.025 | +0.0259 (-0.2151, +0.2669) | +1.7240 (-1.2332, +4.6813) | no direction resolved |
| Brazil (EWZ) | G1 | squared error | 0.001 | -0.0110 (-0.0331, +0.0112) | -0.0242 (-0.0956, +0.0473) | kernel-fragile (Bartlett 63 p = 0.373); not read |

Across 18 primary G1 tests, the only Holm rejection is the kernel-fragile Brazil row. So adding a
regime term to HAR + implied vol never shows a conditional gain in the primary family, in any state.
Every G2 rejection points the same way as the unconditional results: the HMM's own vol forecast is
worse than HAR + implied vol, and where the test can tell, it is worse when the HMM says high vol.

### Secondary family (QLIKE var): 3 Holm rejections

| Block | Pair | Holm p | d at p=0 (95%) | d at p=1 (95%) | Reading |
|---|---|---|---|---|---|
| Russell 2000 | G2 | 0.002 | +0.0347 (-0.0099, +0.0793) | +0.1450 (+0.0720, +0.2180) | against |
| S&P 500 1996-2004 | G2 | 0.003 | +0.1346 (+0.0442, +0.2249) | +0.1650 (+0.0343, +0.2956) | against |
| S&P 500 2024-2026 | G1 | 0.015 | -0.0128 (-0.0259, +0.0004) | -0.0487 (-0.2311, +0.1336) | gain at both ends, neither interval excludes zero; not a lead |

The 2024-2026 G1 row is the same comparison that flips claim B in Part 1. Two things limit it.
First, the mean gain is similar on calm days (-0.0142, p < 0.5) and stressed days (-0.0464, p >=
0.5, 13% of days), so this is not evidence of a regime-timing effect. Second, it rests on 676
overlapping days, about 32 non-overlapping months, where the size check puts the test at 7.4%.
The rejection does not depend on the kernel (rectangular 20, Bartlett 20 and Bartlett 63:
squared error p = 0.006 to 0.014, QLIKE var p = 0.000 to 0.001). But under squared error the Holm-adjusted p is 0.309, and RMSE, the registered measure,
shows no difference.

### Note on POSTHOC's DM tests (amendment A1 iv)

POSTHOC's HAC Diebold-Mariano tests use the same Bartlett 20-lag variance, so they share the size
problem above. On the registered-claim pairs, 8 of 37 Bartlett rejections at 5% are not rejections
under the rectangular kernel, and the rectangular kernel adds a few of its own. The full table is
in `docs/results/gw_conditional/RESULTS.md`. Every registered and POSTHOC verdict comes from the
bootstrap intervals, not the DM p-values, so no verdict changes. Only POSTHOC's DM column is
affected.

## Known limits

- All of this is post hoc on spent holdouts. Nothing here can be confirmed until a new holdout
  opens, and none can open before the 31 January 2027 gate.
- The windows expand, the instrument p_t is a model output, and blocks are dependent: the three
  indices share dates, and so do the four ETFs. Holm controls the family-wise error but does not
  model that dependence.
- The QLIKE var forecast assumes lognormal residuals. That is the same assumption the mean
  correction already makes.
- Coefficient-switching MS-HAR is not tested here or anywhere in the paper. Kilic (FEDS 2025-061r1)
  and Ding et al. (2025) find gains from it, so the paper's negative result covers the HMM
  probability, MSM and MS-GARCH at h = 21 only.

## For Thomas to decide (claim wording needs your approval)

- Whether the paper quotes QLIKE var in place of the POSTHOC QLIKE column. That is the plan's
  reading rule, and it brings ETF R1 back to confirmed and makes VIX 2024-2026 claim B fail.
- How to word the VIX 2024-2026 exception. The evidence supports "under the variance-correct
  QLIKE, in a short recent sample, the HMM probability adds a small gain to HAR + VIX; RMSE shows
  none". It does not support a regime-timing story.
- Whether to add a note to POSTHOC_2026-10.md pointing here for the bias in its QLIKE column and the
  DM kernel. POSTHOC itself is not edited.
