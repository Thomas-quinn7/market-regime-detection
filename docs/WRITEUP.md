# Volatility regimes in the S&P 500, without look-ahead

Equity returns switch between calm, low-volatility stretches and turbulent, high-volatility ones.
This note fits a two-state Markov-switching model to daily S&P 500 returns to infer those states, and
then does the part most write-ups skip: it measures whether the inferred states carry real,
out-of-sample information, evaluated causally, with no future data leaking into the answer.

The headline is deliberately modest, and it has two parts. The regime signal has a correlation of
about **0.57** with next-month realised volatility, and that number **survives a strict walk-forward**
in which parameters are re-estimated on past data only and applied forward. A naive evaluation that
lets future data in reports about **0.61** on the same days. The gap between those two numbers is the
look-ahead premium. The second part is less flattering: plain trailing volatility does better at the
same test (**0.66** for 21-day realised vol, **0.68** for an EWMA), so the regime probability is not
the better volatility forecaster, and in the allocation test a simple trailing-vol switch does about
as well as the regime switch. Reporting both halves is the point.

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

All three rungs are scored on the same 4,003 out-of-sample days (2008-2023). The walk-forward span
starts after its three-year training window, so the leaky rungs are restricted to those days too.
(An earlier version of this note scored the leaky rungs on the full 2005-2023 sample, 0.622 and
0.554, which mixed two different periods.)

| Evaluation | corr with next-month realised vol | What leaks |
|---|---|---|
| Smoothed (full sample) | **0.612** | future *data* |
| Filtered (full-sample params) | 0.545 | future-estimated *parameters* |
| Walk-forward (frozen params, fully OOS) | **0.568** | nothing |

Two things stand out.

First, the honest walk-forward number (0.568) is essentially equal to the filtered full-sample-params
number (0.545), and slightly higher. So in this case the parameter leak was not doing the work. If
anything, re-estimating each quarter tracks the slowly changing volatility structure a little better
than one static full-sample fit. Almost the entire look-ahead premium lives in the smoothed-versus-
causal gap, not in parameter estimation.

Second, the premium is real but small here: about **0.04** of correlation, under a tenth of the
honest signal, would have been banked as edge by a naive write-up. On a noisier target or a shorter
sample it can be much larger. The discipline matters regardless of how big it turns out to be.

## The baseline that matters: trailing volatility

A regime probability that correlates with future volatility is only worth having if it says more
than trailing volatility already does, because volatility clusters and yesterday's vol is the first
forecast anyone would try. So the same test is run on two plain baselines, on the same days and
against the same target (`regimes.evaluate.compare_vol_predictors`): trailing 21-day realised vol and
an exponentially weighted vol with the RiskMetrics decay of 0.94. Both are causal.

| Predictor of next-month realised vol | Pearson | Spearman |
|---|---|---|
| Walk-forward HMM high-vol probability | 0.568 | 0.618 |
| Trailing 21-day realised vol | **0.663** | 0.594 |
| EWMA vol (RiskMetrics 0.94) | **0.680** | **0.623** |

On the linear measure both baselines beat the regime model clearly. On ranks, which is the fairer
measure for a bounded probability against a skewed target, the three are roughly level. Adding the
HMM probability to a regression of next-month vol on trailing 21-day vol lifts the in-sample R^2 from
0.440 to 0.463, so it carries a little information that trailing vol does not, but not much.

The honest reading is that the regime model is **not a better volatility forecaster** than trailing
vol. What it adds is a discrete, persistent state with a probability attached, which is what the
allocation test further down puts to use, and that test includes the trailing-vol baseline too.

## What this shows, and what it does not

This is unsupervised. There is no ground-truth regime label, so the claim is **not** "we recovered the
true regimes." The claim is narrower and testable: the inferred high-volatility state has measurable,
out-of-sample predictive content for future realised volatility, and here is how much, measured
without look-ahead. That content is real but smaller than what trailing volatility alone provides.

What it does not show:

- **The correlation itself is not a P&L.** A correlation with future realised vol is not a backtested
  profit-and-loss. The regime-conditional allocation section further down turns the signal into a
  costed position; this headline result is only a statement about predictive content.
- **Not a claim of the "right" number of regimes.** Two states is a baseline. The extensions below
  test the count by information criterion, and it holds up.
- **Fat tails matter a little.** Returns have fat tails. The extensions add both an autoregressive
  mean and a from-scratch Student-t emission as robustness checks. The regimes survive both, though
  the Student-t moves about 10% of the day-level labels (see below).

## Robustness and extensions

A set of checks and extensions on the baseline. The robustness checks confirm it rather than overturn
it, which is the point of running them. Reproduce with `python examples/extensions.py`.

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

The figure above fits each sector on the full sample, so it is descriptive. Running the same idea
through the walk-forward machinery instead - each sector's high-vol probability comes from
`evaluate.walk_forward_oos`, so it used only past data and past-estimated parameters - gives a breadth
gauge you could have computed in real time. The systemic story survives the stricter test: the
out-of-sample mean pairwise correlation is **0.67**, essentially unchanged from the descriptive 0.66,
and the crisis structure is the same.

![Out-of-sample cross-asset breadth](figures/sector_breadth_oos.png)

### Robust to an autoregressive mean?

The baseline assumes returns are i.i.d. within a regime. Adding an AR(1) mean
(`MarkovAutoregression`) lets the model separate "high variance" from "momentum". The regimes barely
move: the AR and baseline high-vol probabilities correlate at **1.00** and agree on the high-vol
classification on **99.3%** of days. The regimes are a volatility phenomenon, not an artefact of
ignoring autocorrelation.

### Robust to fat tails? Student-t emissions

Equity returns have heavier tails than a normal, and this is the failure mode worth taking seriously:
a Gaussian model can invent a spurious high-variance state just to accommodate a few outliers that a
fat-tailed distribution would absorb within one regime. statsmodels only offers Gaussian switching
models, so this variant (`regimes.student_t.fit_regimes_student_t`) is implemented from scratch: a
Markov-switching model with Student-t emissions, fit by EM using the scale-mixture representation of
the Student-t so outliers are down-weighted in closed form. Its correctness is checked by a test that
confirms it reproduces the statsmodels Gaussian fit as the degrees of freedom grow.

With nu = 5 (heavy tails), the fat-tailed regimes correlate at **0.92** with the Gaussian baseline and
agree on the high-vol classification on **90%** of days. So the regimes are mostly robust to fat
tails, but not entirely: the Student-t reclassifies about one day in ten. That is the expected
direction: some days the Gaussian labelled high-vol were isolated outliers, which the Student-t keeps
in the calm regime rather than treating as a change of state. This is the most informative of the
robustness checks, because it actually moves something, and in the way the theory predicts.

The degrees of freedom can also be estimated rather than fixed (`estimate_nu=True`), via an EM update
that solves the digamma equation for nu each iteration. On the S&P 500 the estimate is **nu = 4.75** —
genuinely heavy tails, and close enough to the nu = 5 used above that the fixed choice was a fair one.
It is offered as an option rather than the default because the nu likelihood is famously flat, so a
fixed, documented value is the more honest robustness setting.

## Multivariate regimes: a Financial Turbulence input

Everything above defines regimes from a single asset's returns. Real systematic funds do not: they use
a multivariate stress measure. The canonical one is **Financial Turbulence** (Kritzman & Li 2010) - the
Mahalanobis distance of the day's cross-asset return vector from its history,
`FT = (r - mu)' Sigma^-1 (r - mu)`, which fires both on uncharacteristically large moves and on breaks
in the cross-asset correlation structure. Feeding that series into the same 2-state HMM ("normal" vs
"ex-normal") is standard practice among systematic managers (Kritzman & Li 2010).

The implementation (`regimes.turbulence`) computes turbulence across the nine SPDR sectors with the
mean and covariance estimated causally from a trailing window, so it inherits the same look-ahead
discipline as the rest of the repo, and fits the HMM ordered by mean turbulence (normal vs ex-normal).

The honest comparison, on the S&P 500 (2005-2023):

| Regime signal | corr with next-month S&P 500 realised vol |
|---|---|
| Single-asset S&P 500 volatility regime | 0.55 |
| Multivariate turbulence regime (9 sectors) | 0.39 |

(Both are computed on a full-sample fit here, for a like-for-like comparison; the single-asset 0.55 is
the filtered full-sample-params number from the ladder above, not the 0.57 walk-forward headline.)

The turbulence regime is a genuinely *different* signal - it agrees with the single-asset labelling on
only 74% of days. And it scores **lower** on predicting the S&P 500's own next-month volatility. That
is expected, not a failure: the single-asset model is almost tautologically tied to S&P 500 vol because
it is built from it, whereas turbulence measures broader cross-asset fragility that a single-asset model
cannot see. Its value is as a systemic-stress gauge and, per the literature, as an input to
regime-conditional *allocation* across assets - not as a sharper predictor of one index's volatility.
Testing it on that narrower task is the fair, unflattering comparison, so that is the one reported here.

![S&P 500 with multivariate turbulence regimes](figures/turbulence_regimes.png)

## The Absorption Ratio, and its false-alarm rate

The Absorption Ratio (Kritzman, Li, Page & Rigobon 2011) is the fraction of a cross-section's total
return variance absorbed by its first few principal components. A high AR means risk is concentrated
in a few factors, i.e. markets are tightly coupled and fragile. The early-warning signal is a
standardised shift `dAR = (AR_short - AR_long) / sigma(AR_long)`, with a one-standard-deviation spike
as the trigger; all inputs are trailing, so it is causal (`regimes.absorption`).

The papers report that essentially all major drawdowns were *preceded by* an AR spike. That is a
**recall** statistic, and on its own it is not an edge: it says nothing about how often a spike fires
with no drawdown following. So the repo measures the full confusion matrix. On the S&P 500
(2005-2023), alert = one-SD dAR spike, outcome = a drawdown of at least X% within the next 21 trading
days:

| Outcome | recall | precision | false-alarm share | base rate | lift |
|---|---|---|---|---|---|
| drawdown >= 5% | 0.32 | 0.24 | **0.76** | 0.18 | **1.37** |
| drawdown >= 10% | 0.43 | 0.08 | **0.92** | 0.05 | **1.82** |

("False-alarm share" here is the fraction of alerts *not* followed by a drawdown, i.e. 1 - precision,
which is the false-discovery rate rather than the classical false-positive rate FP/(FP+TN); the code
reports both.)

The honest reading: the AR spike carries a **real but modest** edge (lift of 1.4 to 1.8 times the base
rate, and it is larger for the more severe drawdowns, which is the right direction), but **76% to 92%
of alerts are false** and alerts fire on ~23% of all days. "Almost every drawdown was preceded by a
spike" and "most spikes are false alarms" are both true at once, and only the first half survives into
the marketing. Reporting the false-alarm rate and the lift is the contribution here.

![Absorption-ratio alerts vs the S&P 500](figures/absorption_alerts.png)

Caveats, stated plainly: this uses the 9 SPDR sectors, so only ~2 principal components (n/5), a much
coarser cross-section than Kritzman's 51 industries with 10 components; the recall here is therefore
far below the paper's near-100%, partly from the smaller universe and a different drawdown definition.
This is not a refutation of the paper. It is the missing half of the picture: even taking the leading-
indicator claim at face value, the signal is a high-false-alarm one with a genuine but small lift.

## Regime-conditional allocation: holding the signal to a P&L standard

Everything so far measures a regime signal against volatility. The literature (Ang & Bekaert 2004) is
clear that the actual value of regime detection shows up somewhere else: not in predicting one index's
volatility, but in switching across assets to avoid losses. So this is the capstone test - turn the
regime probability into a position and score it on profit and loss.

The rules are deliberately strict on look-ahead: the regime probability is the **walk-forward
out-of-sample** one (parameters estimated only on past data), the position for each day is decided from
the prior day's information, and turnover is charged 5 basis points. When the filtered high-vol
probability is below 0.5 the strategy holds equity (SPY); at or above it, the strategy switches to cash
(BIL) or to 7-10y Treasuries (IEF). Benchmarks are static 100% equity, a static 60/40, and the
baseline from earlier: the same equity/cash switch driven by plain trailing vol instead of the regime
model, moving to cash when annualised vol is at or above 20%. The 20% is a round number fixed in
advance, not tuned. A volatility-targeting rule is included as the standard continuous alternative
(Moreira & Muir 2017 style, no leverage): equity weight = 10% / EWMA vol, capped at 1, the rest in
cash. Window: 2008-2023 (where the OOS signal exists).

| Strategy | ann return | ann vol | Sharpe | max drawdown | Calmar |
|---|---|---|---|---|---|
| Regime switch equity / cash | 7.7% | 10.9% | 0.66 | **-15%** | **0.51** |
| Regime switch equity / bonds | 8.5% | 12.0% | 0.67 | -17% | 0.51 |
| 21-day vol > 20%, equity / cash | 9.1% | 11.6% | **0.74** | -18% | **0.51** |
| EWMA vol > 20%, equity / cash | 6.7% | 11.6% | 0.55 | -20% | 0.33 |
| EWMA vol target 10%, equity / cash | 7.0% | 10.0% | 0.65 | -19% | 0.37 |
| Static 100% equity | **10.0%** | 20.4% | 0.53 | -52% | 0.19 |
| Static 60/40 equity / bonds | 7.8% | 11.6% | 0.64 | -31% | 0.25 |

![Regime-conditional allocation vs benchmarks](figures/regime_allocation.png)

The honest reading, and it is exactly what the literature predicts. Regime switching **does not make
more money** than buy-and-hold equity - it earns less (7.7% vs 10.0%), because sitting out flagged
periods means missing some of the rebounds. What it does is earn a similar amount with **half the
volatility and a third of the drawdown**: max drawdown falls from -52% to -15%, and risk-adjusted
return improves clearly (Sharpe 0.66 vs 0.53, Calmar 0.51 vs 0.19). The chart shows where it comes
from: the regime strategies sidestep almost all of 2008 and most of 2020, and give the ground back
slowly during the long bull run. This is loss avoidance, not alpha, and it is the value Ang & Bekaert
attribute to regimes.

Two comparisons take most of the shine off that. Against a static 60/40, which is the fairer
benchmark for a strategy that spends a quarter of its time in cash, the Sharpe gain is 0.02 (0.66 vs
0.64), and what remains is the smaller drawdown (-15% vs -31%). And against the trailing-vol switch,
the regime model is not clearly better: the 21-day rule has a higher Sharpe (0.74) and a slightly
deeper drawdown (-18%), the EWMA rule a lower Sharpe (0.55). The threshold grid printed by the script
shows the trailing-vol rules spread across roughly the same range as the regime switch:

| Trailing-vol rule, equity / cash | 15% | 20% | 25% |
|---|---|---|---|
| 21-day vol: Sharpe / max drawdown / days in cash | 0.63 / -12% / 44% | 0.74 / -18% / 24% | 0.72 / -25% / 14% |
| EWMA vol: Sharpe / max drawdown / days in cash | 0.61 / -15% / 44% | 0.55 / -20% / 24% | 0.67 / -21% / 13% |

(The regime switch spends 28% of days in cash.) Six variants on one path is a small grid, and picking
its best cell would be the same mistake as reporting a smoothed label, so the reading is about the
range: on this sample the regime model does about as well as a plain trailing-vol rule, not better.

**None of these Sharpe ratios can be told apart on this sample.** A paired circular block bootstrap
(`regimes.allocation.block_bootstrap_sharpe`: quarter-long blocks to keep volatility clustering, the
same blocks for every strategy so differences are paired, 2,000 draws) gives:

| Strategy | Sharpe 95% interval | Sharpe minus regime switch (equity/cash), 95% interval |
|---|---|---|
| Regime switch equity / cash | 0.24 to 1.11 | |
| Regime switch equity / bonds | 0.26 to 1.09 | -0.17 to +0.19 |
| 21-day vol > 20% | 0.31 to 1.18 | -0.19 to +0.31 |
| EWMA vol > 20% | 0.09 to 1.03 | -0.40 to +0.17 |
| EWMA vol target 10% | 0.23 to 1.09 | -0.32 to +0.28 |
| Static 100% equity | 0.13 to 1.03 | -0.58 to +0.29 |
| Static 60/40 | 0.22 to 1.15 | -0.51 to +0.42 |

Every difference interval contains zero, including the one against plain buy-and-hold. Sixteen years
of daily data pins a single Sharpe ratio down only to about plus or minus 0.4, while the gaps in the
table are under 0.2, so the Sharpe column above should be read as a description of one path rather
than a ranking. The drawdown reduction is the more robust part of the result, since every switching
and vol-targeting rule cuts the maximum drawdown sharply (-12% to -25%, against -52% for equity),
though as a single-path statistic it has no interval here either.

Caveats, because this is the result most easily oversold. It is a single out-of-sample path on one
market over one 16-year window, and that window is bracketed by two large crashes that flatter a
loss-avoidance strategy; a different sample could look very different (Ang & Bekaert flag the same
sample-specificity about their own numbers). The binary switch is crude, the ~2.3% of annual return
given up is a real cost of the insurance, and none of this is a live trading system. The claim is
narrow: used the way the literature says to use it, the regime signal produces a genuine,
out-of-sample, cost-aware reduction in drawdown, and on this sample a plain trailing-vol switch
achieves about the same.

## Macro growth/inflation quadrants, and the cost of doing it honestly

The last piece follows Bridgewater and Kritzman-Page-Turkington: classify each day by two macro
drivers, growth and inflation, each rising or falling, into a four-quadrant regime (goldilocks,
overheating, stagflation, slowdown), and tilt allocation by each quadrant's asset bias. Growth is the
Chicago Fed CFNAI activity index, inflation is core-CPI year-over-year (`regimes.macro`).

For this repo the interesting part is not the 2x2, it is the data. Macro series are published weeks
after their reference period and then revised, so a naive pull feeds the model numbers that did not
exist at decision time. The implementation therefore uses **point-in-time** data from FRED/ALFRED:
first-release values, indexed by their actual publication date (`realtime_start`) rather than their
reference date, forward-filled onto the daily grid. Nothing enters the series before the day it was
really released.

Doing this honestly has a price that is itself the headline finding. ALFRED's real-time (vintage)
archive for the CFNAI only begins in **May 2011**, even though the index itself runs back to 1967. So
the honest, look-ahead-free macro series only exists from 2011, and after the trailing-trend warmup the
usable backtest starts in **2012**. Using the revised series would buy a longer history at the cost of
look-ahead, which is exactly the trade this repo refuses. Integrity costs years of sample here, and
that is worth stating rather than hiding.

The result, 2012-2023, quadrant tilt across equity/bonds/cash vs static benchmarks, after costs:

| Strategy | ann return | ann vol | Sharpe | max drawdown | Calmar |
|---|---|---|---|---|---|
| Macro-quadrant tilt | 7.5% | 9.4% | 0.72 | -19% | 0.40 |
| Static 100% equity | 13.8% | 16.9% | 0.80 | -34% | 0.41 |
| Static 60/40 equity/bonds | 9.0% | 9.9% | 0.82 | -21% | 0.43 |

This one does **not** work, and the honest thing is to say so. The quadrant tilt trails both benchmarks
on return and on Sharpe (7.5% and 0.72, versus 9.0% and 0.82 for a plain 60/40 and 13.8% and 0.80 for
all-equity). It does cut drawdown versus all-equity, to about the level of a plain 60/40 (-19% vs
-21%), but 60/40 delivers that same risk reduction with clearly higher return and Sharpe, so the tilt
adds nothing a static balanced fund did not. Two reasons, both anticipated when the feature was scoped. First, the usable window (2012-2023) is short and
almost entirely a bull market, so a strategy that sits in cash or bonds for roughly half the days -
every "stagflation" and "slowdown" quadrant - simply misses equity gains. Second, a monthly macro
signal is a slow, coarse overlay, and macro regimes turn over so rarely that a decade contains only a
few independent observations. The macro-quadrant layer is a descriptive allocation tilt on a sample too
small and too one-directional to add value here, and that is a more useful thing to have demonstrated
than another flattering backtest.

![Macro-quadrant tilt vs benchmarks](figures/macro_quadrants.png)

(Tier 2 - full ALFRED vintage reconstruction via `get_series_as_of_date`, and survey-based expectations
- is documented in `regimes/macro.py` as the rigorous upgrade, but it would not change the sample-size
limitation that drives this result.)

## Stock-bond correlation regimes: aiming the HMM at a state that is actually hidden

The volatility results above have a simple explanation. Volatility is close to observable, since a
few large daily moves reveal it within days, so a hidden-state model mostly rebuilds what trailing
volatility already shows, more coarsely. The sign of the stock-bond correlation is a better
candidate for a hidden state: it was positive through the 1970s to 1990s, negative for most of
2000-2021, and positive again from 2022, and daily cross-products are noisy enough that a trailing
correlation needs a long window to settle. So the last experiment points an HMM at it
(`regimes.correlation`).

**Design.** Equity and Treasury returns are each divided by their own EWMA volatility from the
previous day, so that what is left to separate the states is mostly correlation. A two-state HMM
with a full-covariance Gaussian per state is fit by EM, walk-forward with quarterly refits and
frozen parameters filtered forward, exactly as for the volatility model. Its forecast is the
implied correlation over the next quarter. The baselines are trailing 63-day and 252-day
correlation and an EWMA correlation, the target is the realised correlation over the next 63 days,
and everything is scored on the same days.

### Development period, 2005-2023 (SPY and IEF)

The pre-registered model **failed outright**. Maximum likelihood preferred to spend both states on
short volatility shocks that survive the devolatilisation (one state with about 2.5 times the
variance, lasting about two days on average), and the two states ended up with almost the same
correlation (-0.35 and -0.27). A clean correlation split (-0.61 and +0.13) does exist, and plain EM
from a neutral start finds it, but it has a lower likelihood by about 100 log-likelihood units, so
the walk-forward correctly moved past it. Restarting each refit from a fresh start did not change
this. The implied correlation came out *negatively* related to the outcome (-0.31).

A second variant was then added, with the variances tied across states so that they can differ only
in correlation. Its states separate as intended (-0.59 and +0.14), but as a forecast of the
correlation level it still loses to trailing correlation (RMSE 0.286 against 0.272, interval
spanning zero), for the same reason as the volatility model: two discrete levels cannot track a
continuous quantity. Its probability of the positive state did turn positive on 25 Jan 2021, a month
before the trailing 63-day correlation, but that is one flip, and once false alarms were counted it
switched sign 19 times against 10 for the trailing correlation.

![Stock-bond correlation, tied HMM vs trailing correlation](figures/stock_bond_regimes.png)

### Holdout, 1962-2004, run once

Two variants had been chosen after looking at 2005-2023, so a win there would be partly fitted to
it. The rules for a holdout on 1962-2004, which neither model had seen, were therefore written and
committed first ([HOLDOUT_PROTOCOL.md](HOLDOUT_PROTOCOL.md), commit `53b50c6`), and the holdout was
run once. ETF bond data starts in 2002, so the bond leg is a 10-year Treasury return proxy built
from the FRED DGS10 yield (carry plus duration times yield change). On 2005-2023 its quarterly
stock-bond correlation matches the IEF version at 0.990.

Level forecast, 9,878 days (1965-2004):

| Signal | corr with outcome | RMSE | RMSE minus trailing 63-day, 95% interval |
|---|---|---|---|
| HMM, unconstrained | 0.05 | 0.321 | +0.034 to +0.109, **worse** |
| HMM, tied variances | 0.08 | 0.329 | +0.045 to +0.111, **worse** |
| Trailing 63-day correlation | 0.65 | 0.251 | |
| Trailing 252-day correlation | 0.65 | 0.237 | -0.034 to +0.006, no difference |
| EWMA correlation (0.97) | **0.68** | 0.239 | -0.019 to -0.005, **better** |

Regime detection. The frozen definition (runs of one sign lasting at least 126 days) finds only
three lasting flips in 40 years, all between 1998 and 2000; the 1970s-1990s positive regime is one
long run. Each signal's sign call switches only after 21 days of the new sign and is dated on the
day it could have been known:

| Signal | lags in trading days (3 flips) | median | misses | false alarms |
|---|---|---|---|---|
| HMM tied, P(positive state) | 143, 49, 0 | 49 | 0 | 6 |
| Trailing 63-day correlation | 0, 83, 0 | 0 | 0 | 18 |
| Trailing 252-day correlation | 98, 188, 38 | 98 | 0 | 5 |
| EWMA correlation (0.97) | 0, 98, 0 | 0 | 0 | 17 |
| HMM implied correlation (either variant) | 0 | 0 | 2 | 1 to 5 |

A lag of 0 means the signal already showed the new sign on the flip date, which can come from an
earlier switch during a shorter run of the same sign.

**Verdict under the frozen rule: the HMM adds nothing.** Both variants are significantly worse than
trailing correlation at forecasting the level, and the tied classifier is slower than the trailing
63-day correlation (median 49 days against 0) while having fewer false alarms (6 against 18), which
fails the rule that required it to be no worse on all three counts. Outside the rule, and on only
three events, it sits on the speed versus false-alarm trade-off about where a trailing window
between 63 and 252 days would, so even that is not something a simpler signal cannot do.

The one result that held on both periods is a plain one: the EWMA correlation beat the trailing
63-day correlation on level in 2005-2023 and again in the holdout.

What this does and does not show. It shows that this HMM, as specified, has no edge over simple
correlation estimates on this question, on 60 years of data, with the decisive test run once on
unseen data. It does not show that no regime model can help here. A Student-t multivariate
emission, which could absorb shocks without spending a state on them, is the obvious untried next
step, and three flips is still a small number of events. Two variants were tried in total, and both
are reported.

## Reproduce

```bash
pip install -e .
python examples/spx_regimes.py         # headline result + figures
python examples/extensions.py          # state-count, cross-asset, AR + Student-t robustness
python examples/turbulence_regimes.py  # multivariate Financial Turbulence regimes
python examples/absorption_signal.py   # absorption-ratio spike signal, honest confusion matrix
python examples/regime_allocation.py   # regime-conditional cash/bonds/equity allocation, after costs
python examples/macro_quadrants.py     # macro growth/inflation quadrants (runs offline from the committed cache)
python examples/stock_bond_regimes.py  # stock-bond correlation HMM vs trailing correlation, 2005-2023
python examples/stock_bond_holdout.py --period holdout  # the frozen 1962-2004 holdout (about an hour)
```

`macro_quadrants.py` uses FRED/ALFRED data whose small first-release cache is committed, so it runs
with no key; a free `FRED_API_KEY` (`fred.stlouisfed.org` -> My Account -> API Keys) is needed only to
refresh or extend it. Everything else needs no keys.

Every number and figure in this note comes straight from those scripts. The raw data pull is cached,
so reruns are deterministic.

## Possible extensions

The repo spans the full arc: a look-ahead-free baseline, an honest walk-forward, state-count selection,
four robustness and cross-asset angles, a multivariate turbulence input, the absorption-ratio confusion
matrix, a regime-conditional allocation backtest, and point-in-time macro quadrants. Natural directions
from here, none of them started:

- Intraday or higher-frequency data, where regime switches are faster and the filtered-vs-smoothed
  distinction bites harder.
- Asset classes beyond equity/bonds/cash (FX, commodities) and a richer cross-asset risk-on / risk-off
  state.
- Tier 2 point-in-time macro: full ALFRED vintage reconstruction and survey-based expectations (the
  sample-size limitation would remain).
