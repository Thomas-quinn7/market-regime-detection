# market-regime-detection

[![CI](https://github.com/Thomas-quinn7/market-regime-detection/actions/workflows/ci.yml/badge.svg)](https://github.com/Thomas-quinn7/market-regime-detection/actions/workflows/ci.yml)

Can a regime model forecast volatility better than the simple measures it competes with? This repo
started as a Markov-switching model of S&P 500 volatility regimes, built **without look-ahead bias**,
and grew into a long attempt to answer that question honestly. The main forecasting claims were tested
on data held back for the purpose, under a protocol that was committed and pushed before that data was
opened, and each holdout was run once.

The answer is no. On four holdouts (the S&P 500 in 1996-2004 and 2024-2026, the Nasdaq-100, Dow and
Russell 2000, and oil, gold, emerging-market and Brazil ETFs), adding a regime probability to a simple
HAR forecast with the market's own implied vol never made a measurable difference. That was the
two-state model's probability on the first three and Markov-switching GARCH's on the ETFs. The regime model's own forecast had a higher error than HAR plus implied vol on every
holdout but one, the short 2024-2026 sample, where the two were level. Richer regime models did beat
the two-state one, a multifractal model on the Russell 2000 and Markov-switching GARCH on gold and
emerging markets, however both still had a higher error than HAR plus implied vol on every holdout. The write-up also shows why. The
two-state probability is a squashed version of EWMA volatility, pinned near 0 or 1, so its forecast is
stuck between two levels, and on simulated data it only wins when volatility really does switch
between two levels.

The earlier work is all still here, starting with the look-ahead trap itself (smoothed and Viterbi
labels are computed from the whole series, future included), then a multivariate Financial Turbulence
input, the Kritzman Absorption Ratio with its false-alarm rate measured alongside its recall, a
regime-conditional allocation backtest, point-in-time macro quadrants and stock-bond correlation
regimes. Most of these do not beat their simple benchmarks either, and they are reported that way.

**Start with the full write-up: [docs/WRITEUP.md](docs/WRITEUP.md)**, with the methodology, figures and
caveats for every result below.

## Results at a glance

| Layer | Honest result |
|---|---|
| Volatility-regime baseline | 0.57 correlation with next-month realised vol, walk-forward out-of-sample; letting future data in gives 0.61 on the same days, which is the look-ahead premium |
| Against trailing vol | plain trailing vol forecasts next-month vol **better** (0.66 for 21-day realised vol, 0.68 for EWMA); on ranks the three are level, and the HMM adds little on top (R^2 0.44 to 0.46) |
| Robustness | AIC/BIC pick 2 states; regimes survive an AR(1) mean (99% agreement) and from-scratch Student-t emissions (90%) |
| Cross-asset concordance | stress is systemic: the nine per-sector regimes agree at 0.67 mean pairwise correlation, out-of-sample |
| Multivariate turbulence | a genuinely different signal from single-asset vol (74% label agreement); correlates 0.39 with next-month realised vol vs the single-asset model's 0.55 on its home turf, which is expected since its value is correlation-break detection |
| Absorption Ratio | a real but modest drawdown-warning edge (lift 1.4 to 1.8x), but **76 to 92% of alerts are false**, measured here alongside the recall the literature emphasises |
| Regime allocation | max drawdown -15% vs -52% for equities and -31% for 60/40, but Sharpe 0.66 vs 0.64 for 60/40, and a plain trailing-vol switch or vol targeting does about as well (Sharpe 0.55 to 0.74), and a block bootstrap cannot tell any of the Sharpe ratios apart: loss avoidance, not alpha (out-of-sample, after costs) |
| Macro quadrants | does **not** beat a static 60/40. An honest null result, kept for the point-in-time data discipline it demonstrates |
| Stock-bond correlation regimes | an HMM aimed at a state that is genuinely hidden, tested on a 1962-2004 holdout whose rules were committed first: **worse** than trailing correlation at forecasting it and no better at spotting flips; plain EWMA correlation won on both periods |
| Adding the VIX | every signal scored as a forecast against HAR-RV, with two holdouts committed first (1996-2004, 2024-2026): adding the VIX cuts forecast error on both (about 9% on 1996-2004); a regime probability adds nothing once the VIX is in; the HMM's own forecast loses to HAR on 1996-2004 and draws on 2024-2026 |
| Three more attempts, and why it loses | VIX term structure, recession and Fed-easing labels, and intraday realised vol from S&P futures (development data): the HMM never beats a simple measure built from the same information. Its probability is a squashed EWMA vol, pinned near 0 or 1, with a forecast stuck between two levels; on simulated data it wins only when volatility truly has two states |
| Better vol models, and three more indices | HARQ, SHAR, GJR-GARCH, a multifractal regime model (MSM) and a combination, tested on a Nasdaq-100, Dow and Russell 2000 holdout committed first: none beats HAR-RV + implied vol on any index; MSM beats the two-state HMM on the Russell 2000 only, so the regime claim is mixed |
| Markov-switching GARCH and credit | a regime model where volatility moves inside each regime, plus the Baa credit spread, tested on an oil, gold, emerging-market and Brazil ETF holdout committed first: MS-GARCH loses to HAR + implied vol on all four and is no better than one GJR-GARCH, though it does beat the two-state HMM (confirmed); credit adds nothing |

## The idea

Financial return series switch between persistent states: calm, low-volatility stretches and
turbulent, high-volatility ones. A 2-state **Markov-switching model** (regimes differ in variance)
infers those states from daily S&P 500 log returns.

## The point: filtered vs smoothed (the honest bit)

After you fit the model you can label each day two ways:

- **Smoothed**: P(regime | the *entire* series). Uses future data. Fine for *describing* history,
  **invalid** for any forward-looking or tradeable claim.
- **Filtered**: P(regime | data *up to that day*). Causal, available in real time. This is the one
  any out-of-sample evaluation must use.

Smoothed labels make a much cleaner chart, so it is easy for a regime demo to show them and imply
they were tradeable. They were not. This repo shows the two side by side and only ever makes forward
claims on the **filtered** ones.

## What "correct" means here

Regime detection is **unsupervised**, so there is no ground-truth regime label to check the model
against. The test used here is whether the inferred high-volatility state has measurable,
out-of-sample predictive content for next-period realised volatility, evaluated causally, and how much
it has, including where it fails.

## Results

Full write-up with methodology and figures: **[docs/WRITEUP.md](docs/WRITEUP.md)**.

Headline: on S&P 500 daily returns (2005-2023), the inferred high-volatility state has a correlation
of about **0.57** with next-month realised volatility, and that number survives a strict walk-forward
where parameters are estimated on past data only. A naive evaluation that lets future data in reports
about 0.61 on the same days. The gap is the look-ahead premium, and the honest number is the one
reported. Plain trailing volatility does better at the same test (0.66 to 0.68), so the regime model
is not the better vol forecaster. The later sections of the write-up turn every signal into a
forecast and test it on held-back data, with the outcome in the table above.

![S&P 500 with out-of-sample high-volatility regimes](docs/figures/spx_regimes.png)

## Install and reproduce

```bash
pip install -e .
python examples/spx_regimes.py         # headline vol-regime result + figures
python examples/extensions.py          # state-count, cross-asset concordance, AR + Student-t robustness
python examples/turbulence_regimes.py  # multivariate Financial Turbulence regimes
python examples/absorption_signal.py   # absorption-ratio spike signal, honest confusion matrix
python examples/regime_allocation.py   # regime-conditional cash/bonds/equity allocation, after costs
python examples/macro_quadrants.py     # macro growth/inflation quadrants (runs offline from the committed cache)
python examples/stock_bond_regimes.py  # stock-bond correlation HMM vs trailing correlation
python examples/stock_bond_holdout.py --period holdout  # frozen 1962-2004 holdout (docs/HOLDOUT_PROTOCOL.md)
python examples/vol_forecast_vix.py --period dev      # VIX, HAR-RV and regime forecasts, 2005-2023
python examples/vol_forecast_vix.py --period early    # frozen 1990-2004 VIX holdout (docs/VIX_HOLDOUT_PROTOCOL.md)
python examples/vol_forecast_vix.py --period recent   # frozen 2024-2026 VIX holdout (same protocol)
python examples/term_structure_regimes.py  # HMM on the VIX term structure, 2006-2023
python examples/regime_labels.py      # HMM vs NBER recessions and Fed easing, 1928-2023 (over an hour, resumable)
python examples/why_hmm_loses.py      # why the HMM loses to EWMA vol, plus a simulation (about 40 minutes)
python examples/intraday_rv.py        # intraday realised vol; needs licensed Databento ES bars, not included
python examples/better_vol_models.py  # HARQ, SHAR, GJR-GARCH, MSM vs HAR-RV + VIX (Databento ES bars)
python examples/cross_index_holdout.py  # frozen Nasdaq-100, Dow, Russell 2000 holdout (docs/CROSS_INDEX_HOLDOUT_PROTOCOL.md)
python examples/msgarch_credit.py     # MS-GARCH and credit vs HAR + VIX, S&P 500 development
python examples/msgarch_credit_holdout.py  # frozen oil, gold, EM, Brazil holdout (docs/MSGARCH_CREDIT_HOLDOUT_PROTOCOL.md)
```

Everything runs with no API keys. `macro_quadrants.py` uses FRED/ALFRED data whose small first-release
cache is committed, so it runs offline too; a free `FRED_API_KEY` (`fred.stlouisfed.org` -> My Account
-> API Keys) is needed only to refresh or extend that macro data.

## Layout

```
src/regimes/
  data.py        # cached, deterministic index + sector-ETF daily data
  model.py       # Markov-switching fit (baseline + AR variant); canonical ordering; filtered + smoothed
  student_t.py   # from-scratch Student-t emission model (EM); fat-tail robustness
  turbulence.py  # multivariate Financial Turbulence (Mahalanobis) as the HMM input
  absorption.py  # Absorption Ratio (PCA fragility) + honest signal confusion matrix
  allocation.py  # regime-conditional cash/bonds/equity backtest; performance stats
  macro.py       # point-in-time (ALFRED) macro growth/inflation quadrant regimes
  evaluate.py    # walk-forward OOS validation; regime-agreement metric
  selection.py   # state-count selection by AIC/BIC
  cross_asset.py # per-sector regimes; systemic-stress concordance and breadth (+ OOS)
  plots.py       # every figure tagged smoothed (descriptive) or filtered/OOS (honest)
tests/           # synthetic-regime recovery + an explicit no-look-ahead assertion (55 tests)
notebooks/       # exploration only, not the headline
```

## Limits (stated up front)

- Unsupervised: no ground truth; results are about predictive content, not "true" regimes.
- Daily frequency. The baseline is single-index; the cross-asset turbulence, absorption-ratio,
  allocation and macro layers extend it.
- A Gaussian switching-variance model is a deliberate baseline, not the last word (fat tails,
  autoregressive means, and more states are tested extensions, not silently assumed).

## License

MIT, see [LICENSE](LICENSE).

## Checking the holdout freezes

Every forecasting holdout was run once, under a protocol committed and pushed before the holdout data
was opened. The commits below are the evidence. Each one can be checked on GitHub (its page shows the
commit date and the files it added) or locally with `git show --stat <hash>`. The results commits
came after the freeze commits in every case, and the result files under `docs/results/` have not been
changed since.

| Holdout | Protocol | Freeze commit | Results commit |
|---|---|---|---|
| Stock-bond correlation, 1962-2004 | docs/HOLDOUT_PROTOCOL.md | 53b50c6 (2026-10-13) | see the protocol |
| VIX, S&P 500 1990-2004 and 2024-2026 | docs/VIX_HOLDOUT_PROTOCOL.md | 3fea6a7 (2026-10-13) | see the protocol |
| Nasdaq-100, Dow, Russell 2000 | docs/CROSS_INDEX_HOLDOUT_PROTOCOL.md | 963cb5e (2026-10-14) | 6f4a3d4 (2026-10-14) |
| Oil, gold, EM and Brazil ETFs, MS-GARCH and credit | docs/MSGARCH_CREDIT_HOLDOUT_PROTOCOL.md | da0cf0f (2026-10-14) | 58a351f (2026-10-14) |

A git hash is a local commitment made public by the push, not a third-party registration. The push
times are GitHub's record, not mine.

## Reproducing the numbers

`requirements-lock.txt` holds the exact package versions (Python 3.11.5) the holdouts were run with.
The data pulls are cached and the bootstrap is seeded, so reruns of the development scripts are
deterministic. The holdout scripts can be rerun too, and with the same cached data files they give the same
forecasts (a fresh download can differ where Yahoo revises adjusted prices), however the
holdouts themselves are spent: a rerun is a reproduction, not a new test.

## Citing this work

A `CITATION.cff` file is in the repository root, so GitHub's "Cite this repository" button gives the
reference. Release v1.0.0 is the version the write-up describes.
