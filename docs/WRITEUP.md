# Volatility regimes in the S&P 500, without look-ahead

Equity returns switch between calm, low-volatility stretches and turbulent, high-volatility ones.
This note fits a two-state Markov-switching model to daily S&P 500 returns to infer those states, and
then does the part most write-ups skip: it measures whether the inferred states carry real,
out-of-sample information, evaluated causally, with no future data leaking into the answer.

The headline is deliberately modest. The regime signal has a correlation of about **0.57** with
next-month realised volatility, and that number **survives a strict walk-forward** in which
parameters are re-estimated on past data only and applied forward. A naive evaluation that lets
future data in reports about **0.62**. The gap between those two numbers is the look-ahead premium,
and reporting the honest one is the whole point.

## The model

A 2-state Gaussian Markov-switching model where the regimes differ in variance
(`statsmodels` `MarkovRegression(k_regimes=2, switching_variance=True)`), fit on daily S&P 500 log
returns from 2005-01 to 2023-12 (4,780 observations). The two states separate cleanly:

| Regime | Daily volatility | Interpretation |
|---|---|---|
| Calm | ~0.67% | low-variance, trending markets |
| Stressed | ~2.06% | high-variance, crisis-prone markets |

That is roughly a **3.1x** volatility ratio between states.

`statsmodels` was chosen over `hmmlearn` for one specific reason: it exposes both the *filtered* and
the *smoothed* state probabilities directly, and the difference between those two is the crux of an
honest evaluation.

## The trap: smoothed vs filtered

Once the model is fit, each day can be labelled two ways:

- **Smoothed** probability: P(regime | the *entire* series). It uses future returns to decide what
  today's regime was. Fine for describing history. Invalid for any forward-looking or tradeable
  claim.
- **Filtered** probability: P(regime | data *up to and including today*). Causal, and the only one
  available in real time.

A second, subtler leak hides in the *parameters*. Even filtered probabilities are contaminated if the
transition matrix and the per-regime variances were estimated using the full sample, because those
estimates saw the future too. The only way to remove that leak is to re-estimate parameters on past
data alone and apply them forward.

This is the same class of error as normalising a trading signal with the full-sample mean and
standard deviation. It looks like signal. It is hindsight.

## The honest test: walk-forward

The evaluation (`regimes.evaluate.walk_forward_oos`) runs an expanding-window walk-forward:

1. Fit the model on returns up to the current window edge (initial window: ~3 years).
2. Freeze those parameters and filter them forward over the next block (~1 quarter).
3. Keep only the filtered high-volatility probabilities on that held-out block. Each one used
   returns up to its own date and parameters estimated strictly before the block.
4. Advance by a quarter and refit.

Regimes are ordered canonically by the training window's variances, so "high-vol" means the same
thing in every block. Over 2005-2023 this produced 4,003 out-of-sample observations across 64
refits, with no fit failures. The out-of-sample span begins in 2008 because the first three years
are the initial training window.

The test itself is deliberately simple and falsifiable: does today's high-vol probability correlate
with the realised volatility of the *next* 21 trading days? If it does not, the regimes are
decorative.

## Results

![S&P 500 with walk-forward high-volatility regimes](figures/spx_regimes.png)

The shaded periods are the model's out-of-sample high-vol regimes. They line up with the events you
would expect without being told: the 2008 crisis, the 2011 euro-area stress, the 2015-16 and late-2018
selloffs, the 2020 COVID crash, and the 2022 bear market. The calm bull runs of 2013-14, 2017 and
2021 are mostly clean. None of this shading used future data.

![The look-ahead premium](figures/result_ladder.png)

| Evaluation | corr with next-month realised vol | What leaks |
|---|---|---|
| Smoothed (full sample) | **0.622** | future *data* |
| Filtered (full-sample params) | 0.554 | future-estimated *parameters* |
| Walk-forward (frozen params, fully OOS) | **0.568** | nothing |

Two things stand out.

First, the honest walk-forward number (0.568) is essentially equal to the filtered full-sample-params
number (0.554), and slightly higher. So in this case the parameter leak was not doing the work. If
anything, re-estimating each quarter tracks the slowly changing volatility structure a little better
than one static full-sample fit. Almost the entire look-ahead premium lives in the smoothed-versus-
causal gap, not in parameter estimation.

Second, the premium is real but small here: about **0.05** of correlation, roughly a tenth of the
honest signal, would have been banked as edge by a naive write-up. On a noisier target or a shorter
sample it can be much larger. The discipline matters regardless of how big it turns out to be.

## What this shows, and what it does not

This is unsupervised. There is no ground-truth regime label, so the claim is **not** "we recovered the
true regimes." The claim is narrower and testable: the inferred high-volatility state has measurable,
out-of-sample predictive content for future realised volatility, and here is how much, measured
without look-ahead.

What it does not show:

- **Not a trading strategy.** A correlation with future realised vol is not a backtested P&L. Turning
  a regime signal into a position involves costs, capacity, and a sizing rule, none of which are here.
- **Not a claim of the "right" number of regimes.** Two states is a baseline. The extensions below
  test the count by information criterion, and it holds up.
- **Still Gaussian.** Returns have fat tails. The extensions add an autoregressive mean as a
  robustness check, but a Student-t emission is not yet implemented (statsmodels' switching models
  are Gaussian) and remains open.

## Robustness and extensions

Three checks on the baseline. All confirm it rather than overturn it, which is the point of running
them. Reproduce with `python examples/extensions.py`.

### How many regimes?

Fitting the model for two, three and four states on the full S&P 500 sample:

| States | AIC | BIC | Converged |
|---|---|---|---|
| 2 | 13203 | 13242 | yes |
| 3 | 12702 | 12780 | **no** |
| 4 | 12668 | 12798 | **no** |

The three- and four-state fits report lower information criteria, but they **fail to converge**: the
optimiser cannot identify a stable third or fourth state on this data, so those numbers are not
trustworthy. Among the fits that actually converged, both AIC and BIC select **two states**. The
baseline count is the honest choice, not an assumption. (This is exactly why the `converged` flag is
reported and non-converged fits are excluded from the selection rather than silently ranked.)

### Systemic or sector-specific? Cross-asset concordance

Fitting the same two-state model independently to each of the nine SPDR sector ETFs, the high-vol
regimes move together: the mean pairwise correlation of the sectors' high-vol probabilities is
**0.66**. Volatility stress is largely a systemic, market-wide state rather than a sector story.

"Breadth" — the share of the nine sectors in their high-vol regime — makes this visible. It sits near
zero in calm periods and saturates to all nine sectors during 2008-09, 2011, the 2020 COVID crash and
2022.

![Cross-asset breadth](figures/sector_breadth.png)

(This cross-asset view is descriptive: each sector is fit on the full sample, so unlike the headline
S&P 500 result it is not a walk-forward out-of-sample statement.)

### Robust to an autoregressive mean?

The baseline assumes returns are i.i.d. within a regime. Adding an AR(1) mean
(`MarkovAutoregression`) lets the model separate "high variance" from "momentum". The regimes barely
move: the AR and baseline high-vol probabilities correlate at **1.00** and agree on the high-vol
classification on **99.3%** of days. The regimes are a volatility phenomenon, not an artefact of
ignoring autocorrelation.

## Reproduce

```bash
pip install -e .
python examples/spx_regimes.py    # headline result + figures
python examples/extensions.py     # state-count, cross-asset, AR robustness
```

Every number and figure in this note comes straight from those scripts. The raw data pull is cached,
so reruns are deterministic.

## Still open

- A Student-t (fat-tailed) emission as a further robustness check. This needs a custom switching
  model; statsmodels only offers Gaussian emissions.
- A genuinely out-of-sample (walk-forward) version of the cross-asset breadth gauge.
