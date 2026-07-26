# market-regime-detection

Detecting **volatility regimes** in equity index returns with a Markov-switching model — and doing
it **without look-ahead bias**, which is the part most implementations get wrong.

The look-ahead-free baseline then extends toward how systematic funds actually do regime analysis: a
multivariate Financial Turbulence input, the Kritzman Absorption Ratio (with the false-alarm rate the
papers omit), a regime-conditional cross-asset allocation backtest, and point-in-time macro quadrants.
Every result is reproducible, and the honest framing includes the extensions that do **not** beat their
benchmarks. Full write-up: **[docs/WRITEUP.md](docs/WRITEUP.md)**.

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

Most "regime detection" demos quietly report smoothed labels and imply they were tradeable. They are
not. This repo shows the two side by side and only ever makes forward claims on the **filtered** ones.

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
about 0.62. The gap is the look-ahead premium, and the honest number is the one reported.

![S&P 500 with out-of-sample high-volatility regimes](docs/figures/spx_regimes.png)

## Install and reproduce

```bash
pip install -e .
python examples/spx_regimes.py         # headline vol-regime result + figures
python examples/extensions.py          # state-count, cross-asset concordance, AR + Student-t robustness
python examples/turbulence_regimes.py  # multivariate Financial Turbulence regimes
python examples/absorption_signal.py   # absorption-ratio spike signal, honest confusion matrix
python examples/regime_allocation.py   # regime-conditional cash/bonds/equity allocation, after costs
python examples/macro_quadrants.py     # macro growth/inflation quadrants (needs FRED_API_KEY)
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
tests/           # synthetic-regime recovery + an explicit no-look-ahead assertion (39 tests)
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
