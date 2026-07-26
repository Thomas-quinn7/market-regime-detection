"""Honest evaluation of inferred regimes.

The claim under test is deliberately narrow and falsifiable: *does the filtered high-volatility
probability carry out-of-sample information about next-period realised volatility?* If it does not,
the regimes are decorative and we say so.

Two levels of rigour live here:
- ``oos_realised_vol_check`` demonstrates the filtered-vs-smoothed distinction on a full-sample fit.
- ``walk_forward_oos`` is the fully rigorous version: it *re-estimates parameters* on each expanding
  train window, so even the emission/transition parameters are free of future data.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

from .model import RegimeFit


def realised_vol(returns: pd.Series, window: int = 21) -> pd.Series:
    """Trailing realised volatility (std of returns over ``window`` days)."""
    return returns.rolling(window).std()


@dataclass
class Agreement:
    """How closely two high-vol probability series agree, on their shared dates."""

    corr: float           # correlation of the two probability series
    label_agreement: float  # fraction of dates both put on the same side of ``threshold``
    n: int


def regime_agreement(prob_a: pd.Series, prob_b: pd.Series, *, threshold: float = 0.5) -> Agreement:
    """Compare two filtered high-vol probability series (e.g. baseline vs an AR-mean variant).

    Used as a robustness check: if a richer model's regimes agree closely with the baseline's, the
    baseline's regimes were not an artefact of its simpler assumptions.
    """
    joined = pd.concat({"a": prob_a, "b": prob_b}, axis=1, sort=True).dropna()
    hi_a = joined["a"] >= threshold
    hi_b = joined["b"] >= threshold
    return Agreement(
        corr=float(joined["a"].corr(joined["b"])),
        label_agreement=float((hi_a == hi_b).mean()),
        n=len(joined),
    )


@dataclass
class OOSResult:
    """Outcome of the causal predictive check."""

    corr_filtered: float  # corr(high-vol filtered prob at t, realised vol over (t, t+h])
    corr_smoothed: float  # same but with smoothed prob — expected to look better *because* it cheats
    horizon: int
    n: int


def oos_realised_vol_check(returns: pd.Series, fit: RegimeFit, horizon: int = 21) -> OOSResult:
    """Correlate today's high-vol regime probability with *future* realised vol.

    The key comparison is ``corr_filtered`` (causal, honest) vs ``corr_smoothed`` (uses future data).
    If smoothed materially beats filtered, that gap is exactly the look-ahead a naive write-up would
    have banked as "signal".

    NOTE: ``fit`` here is estimated on the full sample, so ``corr_filtered`` still enjoys full-sample
    *parameter* estimation. Use ``walk_forward_oos`` (below) for the version that removes that leak by
    re-estimating parameters on past data only.
    """
    fut_vol = realised_vol(returns, horizon).shift(-horizon)  # realised vol over the NEXT horizon
    hv_filt = fit.high_vol_filtered()
    hv_smooth = fit.smoothed.iloc[:, -1]

    joined = pd.concat(
        {"fut_vol": fut_vol, "filt": hv_filt, "smooth": hv_smooth}, axis=1
    ).dropna()

    return OOSResult(
        corr_filtered=float(joined["filt"].corr(joined["fut_vol"])),
        corr_smoothed=float(joined["smooth"].corr(joined["fut_vol"])),
        horizon=horizon,
        n=len(joined),
    )


def train_test_split_series(returns: pd.Series, train_frac: float = 0.7) -> tuple[pd.Series, pd.Series]:
    """Chronological split — never shuffle a time series."""
    cut = int(len(returns) * train_frac)
    return returns.iloc[:cut], returns.iloc[cut:]


@dataclass
class WalkForwardResult:
    """Outcome of a walk-forward, out-of-sample regime evaluation.

    Attributes
    ----------
    high_vol_prob : Series
        Causal filtered P(high-vol regime) on the out-of-sample span. Each value used only returns up
        to its own date AND parameters estimated only on data strictly before its train window edge.
        This is the honest, leak-free regime signal.
    corr : float
        Correlation between ``high_vol_prob`` and next-``horizon``-day realised volatility, on the OOS
        span only.
    n : int
        Number of OOS observations entering the correlation.
    n_refits : int
        How many times parameters were re-estimated.
    n_skipped : int
        Refit windows whose fit failed and were skipped (leaves a gap; surfaced, never silent).
    """

    high_vol_prob: pd.Series
    corr: float
    n: int
    n_refits: int
    n_skipped: int


def walk_forward_oos(
    returns: pd.Series,
    *,
    n_regimes: int = 2,
    min_train: int = 750,
    step: int = 21,
    horizon: int = 21,
) -> WalkForwardResult:
    """Expanding-window walk-forward with frozen-parameter forward filtering.

    This is the version that removes the full-sample-parameter leak that ``oos_realised_vol_check``
    still carries. The protocol, at each refit edge ``i`` (starting at ``min_train``):

    1. Fit the switching-variance model on ``returns[:i]`` only (the train window).
    2. Freeze those parameters and *filter* them forward over ``returns[:i+step]``.
    3. Keep the filtered high-vol probabilities on positions ``[i : i+step]`` — the held-out block.
       The filter is a causal forward recursion, so each of those probabilities used returns only up
       to its own date, and parameters estimated only on data before ``i``.
    4. Advance ``i`` by ``step`` and repeat.

    Regimes are ordered canonically by the *train* fit's variances, so "high-vol" means the same
    thing in every block. Refitting every day would be honest too but wasteful; ``step`` (default:
    monthly) mirrors how a desk actually recalibrates.

    Parameters
    ----------
    min_train : int
        Minimum observations before the first out-of-sample block. Needs enough data to identify two
        variance regimes; the default assumes a few years of daily data.
    step : int
        Refit cadence and OOS block length, in trading days.
    horizon : int
        Forward window (days) for the realised-vol target.
    """
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    y = returns.astype(float)
    n = len(y)
    if min_train >= n:
        raise ValueError(f"min_train={min_train} leaves no out-of-sample data (n={n})")

    oos_pieces: list[pd.Series] = []
    n_refits = 0
    n_skipped = 0

    for i in range(min_train, n, step):
        end = min(i + step, n)
        train = y.iloc[:i].reset_index(drop=True)
        try:
            train_res = MarkovRegression(
                train, k_regimes=n_regimes, trend="c", switching_variance=True
            ).fit(disp=False)
        except Exception as exc:  # a single bad window must not sink the whole run
            warnings.warn(f"walk-forward fit failed at i={i}: {exc}", RuntimeWarning, stacklevel=2)
            n_skipped += 1
            continue
        n_refits += 1

        # Canonical order from the TRAIN fit's variances (high-vol regime is last).
        train_var = np.asarray(
            train_res.params[[f"sigma2[{k}]" for k in range(n_regimes)]], dtype=float
        )
        high_idx = int(np.argsort(train_var)[-1])

        # Freeze train params, filter forward over train+block, read only the held-out block.
        ext = y.iloc[:end].reset_index(drop=True)
        filt = MarkovRegression(
            ext, k_regimes=n_regimes, trend="c", switching_variance=True
        ).filter(train_res.params)
        hv = np.asarray(filt.filtered_marginal_probabilities)[i:end, high_idx]
        oos_pieces.append(pd.Series(hv, index=y.index[i:end]))

    if not oos_pieces:
        raise RuntimeError("no out-of-sample blocks were produced (all fits skipped?)")

    # Clip away sub-1e-14 floating overshoot: statsmodels' filtered marginals sum to 1 but individual
    # entries can round a hair outside [0, 1]. They are probabilities; keep them in range.
    hv_prob = pd.concat(oos_pieces).sort_index().clip(0.0, 1.0)
    hv_prob.name = "high_vol_prob_oos"

    fut_vol = realised_vol(y, horizon).shift(-horizon)
    joined = pd.concat({"hv": hv_prob, "fut_vol": fut_vol}, axis=1, sort=True).dropna()

    return WalkForwardResult(
        high_vol_prob=hv_prob,
        corr=float(joined["hv"].corr(joined["fut_vol"])),
        n=len(joined),
        n_refits=n_refits,
        n_skipped=n_skipped,
    )
