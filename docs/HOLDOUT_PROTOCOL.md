# Holdout protocol: stock-bond correlation regimes, 1962-2004

Written and committed **before** the 1962-2004 data was looked at. Everything below was decided
using only the 2005-2023 development period. The holdout is run once; whatever it gives is the
headline, and any bug found after the run is reported as a bug, not silently fixed and rerun.

## Why a holdout

Two model variants were tried on 2005-2023 and both were chosen after looking at that period, so a
win there would be partly fitted to it. That period also contains only one lasting flip of the
stock-bond correlation (2021-22). The 1962-2004 period covers the long positive-correlation regime
of the 1970s to 1990s and the turn negative around 1998-2000, and neither model has seen it.

## Data

- Equities: S&P 500 price index (`^GSPC`, yfinance), daily log returns in percent.
- Bonds: a 10-year par Treasury return proxy from FRED DGS10 (`regimes.data.load_treasury_10y_returns`:
  carry plus duration times yield change). Checked on 2005-2023 only: its quarterly stock-bond
  correlation matches the IEF version at 0.990.
- Holdout window: 1962-01-01 to 2004-12-31. No data after 2004 is used for fitting, filtering or
  scoring. The first three years (756 days) are the initial training window.

## Models (frozen)

`regimes.correlation.walk_forward_corr_regimes` with `n_regimes=2`, `min_train=756`, `step=63`,
`horizon=63`, `alpha=0.06`, each refit keeping the better of a fresh and a warm start:

- **A, unconstrained**: the pre-registered design.
- **B, tied variances** (`tie_variances=True`): added on the development period after A split on
  volatility shocks.

Only these two variants have been tried. Nothing else will be tried on the holdout.

## Signals

- A: implied next-quarter correlation. B: implied next-quarter correlation.
- B classifier: P(positive-correlation state) minus 0.5 (sign only, not scored as a level).
- Baselines: trailing 63-day correlation, trailing 252-day correlation, EWMA correlation (alpha 0.03).

## Target

Realised correlation of the raw returns over the next 63 trading days, `forward_corr(returns, 63)`.

## Metrics (frozen)

1. **Level forecast.** Pearson correlation and RMSE against the target, all signals on the same
   days. The RMSE of each signal minus the RMSE of the trailing 63-day correlation gets a paired
   circular block-bootstrap 95% interval (blocks of 63 days, 2,000 draws, seed 0). A signal *beats*
   the baseline only if the whole interval is below zero.
2. **Regime detection.** Lasting regimes are runs of one sign of the target lasting at least 126
   trading days (`regime_flips`, `min_len=126`). Each signal's sign call is
   `sustained_sign_state(signal, run=21)`, which switches only after 21 days of the new sign and is
   dated on the day it could have been known. `score_detection(max_lag=252)` gives each signal's
   lag in trading days for each flip, its misses (no detection within 252 days) and its false alarms
   (switches that no flip to the same sign explains within 252 days).

## What counts as the HMM adding something

Model B's classifier adds something over the trailing 63-day correlation only if, on the holdout,
its median detection lag is shorter **and** it has no more misses **and** no more false alarms. For
the level forecast, the rule in metric 1 applies. All results are reported whether they pass or not.

## Note on the development-period dates

The 2005-2023 output of `examples/stock_bond_regimes.py` dated a flip at the *start* of the 21-day
run, which is only knowable 21 days later. The holdout uses `sustained_sign_state`, which dates it
on the day it is knowable. The shift is the same for every signal, so comparisons between signals
are unaffected; the absolute dates are not comparable between the two scripts.
