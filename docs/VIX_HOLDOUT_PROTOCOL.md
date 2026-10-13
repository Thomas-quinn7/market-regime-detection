# Holdout protocol: volatility forecasts with the VIX, 1990-2004 and 2024 onward

Written and committed **before** any VIX data for 1990-2004 or 2024 onward was loaded. Everything
below was decided using only the 2005-2023 development period. Each holdout is run once; whatever it
gives is the headline, and any bug found after the run is reported as a bug, not silently fixed and
rerun.

## Why a holdout

The forecast comparison in `examples/vol_forecast_vix.py` was built and adjusted on 2005-2023. One
change was made after seeing a result: the calibration regression was first fit in levels with one
year of history and blew up (the return/VIX HMM probability sat at exactly 1 through 2008-09 and was
collinear with the intercept), so it was moved to log scale with three years of history, for every
signal alike. A result found that way is partly fitted to the period it was found on.

## Data

- Equities: S&P 500 price index (`^GSPC`, yfinance), daily log returns in percent.
- VIX: CBOE VIX close (`^VIX`, yfinance), `regimes.data.load_vix`. Only days present in both series
  are used. Before September 2003 the VIX is CBOE's backfill of the current method, computed from
  historical S&P 500 option prices; it uses only prices available on each day, but it was not a
  published number at the time.
- **Early holdout:** fit and score on 1990-01-01 to 2004-12-31 (`--period early`). No data after 2004
  is used for fitting, filtering, calibration or scoring. The S&P 500 returns for these years were
  used before, in the stock-bond correlation holdout, but never for volatility, and the VIX for these
  years has never been loaded.
- **Recent holdout:** fit on 2005-01-01 to 2026-10-12 and score only days from 2024-01-01
  (`--period recent`). Training on the earlier years is allowed, since a forecaster in 2024 would
  have had them; only the scored days are unseen.

## Models (frozen)

Exactly as in `examples/vol_forecast_vix.py` at the commit that adds this file:

- Return-only HMM: `evaluate.walk_forward_oos`, 2 states, `min_train=756`, `step=63`, `horizon=21`.
  Signals: its filtered high-vol probability, and its implied vol over the next 21 days.
- Joint return/VIX HMM: `vix_regimes.walk_forward_vix_hmm`, observations `[r_t, log VIX_t]`,
  2 states, same walk-forward settings. Signals: high-vol probability and implied vol.
- Baselines: HAR-RV inputs (`|r_t|`, RMS returns over 5 and 22 days), the VIX, EWMA vol (0.94),
  trailing 21-day vol.
- Every forecast comes from `forecast.walk_forward_regression` with `horizon=21`, `step=63`,
  `min_rows=756`, `log_target=True`; vol-unit inputs are logged, probabilities enter linearly.

Nothing else will be tried on either holdout.

## Target and scoring

Target: realised volatility of daily returns over the next 21 trading days, `forecast.forward_vol`.
All forecasts are scored on the same days. Primary metric RMSE, secondary QLIKE. Each comparison
gets a paired circular block-bootstrap 95% interval for the difference (63-day blocks, 2,000 draws,
seed 0). A forecast **beats** its reference only if the whole interval is below zero, and is
**worse** only if the whole interval is above zero.

## The frozen comparisons

| # | Forecast | Reference | Question |
|---|---|---|---|
| 1 | VIX | HAR | does the VIX alone beat a returns-only model? |
| 2 | HAR + VIX | HAR | does adding the VIX improve a returns-only model? |
| 3 | HAR + HMM prob | HAR | does the return-only regime add to HAR? |
| 4 | HAR + VIX + HMM prob | HAR + VIX | does the regime add anything once the VIX is in? |
| 5 | HAR + VIX + VIX-HMM prob | HAR + VIX | same, for the joint return/VIX regime |
| 6 | HMM implied vol | HAR | is the regime model's own forecast competitive? |
| 7 | VIX-HMM implied vol | HAR | same, for the joint model |

## What the development period predicts

On 2005-2023 (3,226 scored days, 2011-02 to 2023-11), on RMSE: 1 and 2 better; 3 and 4 no
difference; 5, 6 and 7 worse. The claims taken to the holdout are:

- **A. The VIX improves accuracy:** comparison 2 is *better* on RMSE.
- **B. The regime model adds nothing once the VIX is available:** neither comparison 4 nor 5 is
  *better* on RMSE. If either is better, the regime adds something, and that is the headline.
- **C. The regime models' own forecasts lose to HAR:** comparisons 6 and 7 are *worse* on RMSE.

Each claim is reported as holding, failing, or (for "better"/"worse" claims) not shown, per period.

## Power

The early holdout should give roughly 2,200 scored days (1996-2004, after the three-year HMM warm-up
and the three-year calibration warm-up). The recent holdout gives about 680 days, roughly eleven
63-day blocks, so its intervals will be wide; a "no difference" there is weak evidence either way.
The early holdout is the main test.
