# market-regime-detection

[![CI](https://github.com/Thomas-quinn7/market-regime-detection/actions/workflows/ci.yml/badge.svg)](https://github.com/Thomas-quinn7/market-regime-detection/actions/workflows/ci.yml)

Detecting **volatility regimes** in equity index returns with a Markov-switching model, and doing
it **without look-ahead bias**, which is easy to get wrong because the standard smoothed and Viterbi
labels are both computed from the whole series, future included.

The look-ahead-free baseline then extends toward the regime methods in the academic and practitioner
literature: a multivariate Financial Turbulence input, the Kritzman Absorption Ratio (with its
false-alarm rate measured alongside its recall), a regime-conditional cross-asset allocation backtest,
and point-in-time macro quadrants. It is also tested against plain trailing volatility, which turns
out to be a hard baseline to beat.
Every result is reproducible, and the honest framing includes the extensions that do **not** beat their
benchmarks.

**Start with the full write-up: [docs/WRITEUP.md](docs/WRITEUP.md)** — methodology, figures, and
caveats for every result below.

## Results at a glance

| Layer | Honest result |
|---|---|
| Volatility-regime baseline | 0.57 correlation with next-month realised vol, walk-forward out-of-sample; letting future data in gives 0.61 on the same days, which is the look-ahead premium |
| Against trailing vol | plain trailing vol forecasts next-month vol **better** (0.66 for 21-day realised vol, 0.68 for EWMA); on ranks the three are level, and the HMM adds little on top (R^2 0.44 to 0.46) |
| Robustness | AIC/BIC pick 2 states; regimes survive an AR(1) mean (99% agreement) and from-scratch Student-t emissions (90%) |
| Cross-asset concordance | stress is systemic: the nine per-sector regimes agree at 0.67 mean pairwise correlation, out-of-sample |
| Multivariate turbulence | a genuinely different signal from single-asset vol (74% label agreement); correlates 0.39 with next-month realised vol vs the single-asset model's 0.55 on its home turf — expected, its value is correlation-break detection |
| Absorption Ratio | a real but modest drawdown-warning edge (lift 1.4–1.8x) — but **76–92% of alerts are false**, measured here alongside the recall the literature emphasises |
| Regime allocation | max drawdown -15% vs -52% for equities and -31% for 60/40, but Sharpe 0.66 vs 0.64 for 60/40, and a plain trailing-vol switch or vol targeting does about as well (Sharpe 0.55 to 0.74), and a block bootstrap cannot tell any of the Sharpe ratios apart: loss avoidance, not alpha (out-of-sample, after costs) |
| Macro quadrants | does **not** beat a static 60/40 — an honest null result, kept for the point-in-time data discipline it demonstrates |
| Stock-bond correlation regimes | an HMM aimed at a state that is genuinely hidden, tested on a 1962-2004 holdout whose rules were committed first: **worse** than trailing correlation at forecasting it and no better at spotting flips; plain EWMA correlation won on both periods |

## The idea

Financial return series switch between persistent states — calm, low-volatility stretches and
turbulent, high-volatility ones. A 2-state **Markov-switching model** (regimes differ in variance)
infers those states from daily S&P 500 log returns.

## The point: filtered vs smoothed (the honest bit)

After you fit the model you can label each day two ways:

- **Smoothed** — P(regime | the *entire* series). Uses future data. Fine for *describing* history,
  **invalid** for any forward-looking or tradeable claim.
- **Filtered** — P(regime | data *up to that day*). Causal, available in real time. This is the one
  any out-of-sample evaluation must use.

Smoothed labels make a much cleaner chart, so it is easy for a regime demo to show them and imply
they were tradeable. They were not. This repo shows the two side by side and only ever makes forward
claims on the **filtered** ones.

## What "correct" means here

Regime detection is **unsupervised** — there is no ground-truth regime label. So the deliverable is
*not* "we recovered the true regimes." It is: *the inferred high-volatility state has measurable,
out-of-sample predictive content for next-period realised volatility, evaluated causally* — and here
is how much. Framed honestly, including where it fails.

## Results

Full write-up with methodology and figures: **[docs/WRITEUP.md](docs/WRITEUP.md)**.

Headline: on S&P 500 daily returns (2005-2023), the inferred high-volatility state has a correlation
of about **0.57** with next-month realised volatility, and that number survives a strict walk-forward
where parameters are estimated on past data only. A naive evaluation that lets future data in reports
about 0.61 on the same days. The gap is the look-ahead premium, and the honest number is the one
reported. Plain trailing volatility does better at the same test (0.66 to 0.68), so the regime model
is not the better vol forecaster; the write-up shows where it does and does not add anything.

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
notebooks/       # exploration only — not the headline
```

## Limits (stated up front)

- Unsupervised: no ground truth; results are about predictive content, not "true" regimes.
- Daily frequency. The baseline is single-index; the cross-asset turbulence, absorption-ratio,
  allocation and macro layers extend it.
- A Gaussian switching-variance model is a deliberate baseline, not the last word (fat tails,
  autoregressive means, and more states are tested extensions, not silently assumed).

## License

MIT — see [LICENSE](LICENSE).
