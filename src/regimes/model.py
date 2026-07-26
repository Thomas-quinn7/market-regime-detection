"""Markov-switching volatility-regime model.

Engine choice (see MARKET_REGIMES_DESIGN.md §6): ``statsmodels`` ``MarkovRegression`` with
``switching_variance=True``. Unlike ``hmmlearn`` it exposes BOTH the filtered (causal) and the
smoothed (full-sample) marginal probabilities, which is the entire point of this project.

Two traps handled explicitly here:
- **Label switching.** Regime indices from the fit are arbitrary up to permutation. We impose a
  canonical order: regime 0 = lowest fitted variance (calm), last = highest (stressed).
- **Filtered vs smoothed.** Both are returned, clearly named. Never use ``smoothed`` for a forward
  claim.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class RegimeFit:
    """Result of a Markov-switching fit, with regimes canonically ordered by variance.

    Attributes
    ----------
    filtered : DataFrame
        P(regime = k | data up to and including t). Causal. Use this for forward claims.
    smoothed : DataFrame
        P(regime = k | the entire series). Uses future data. Descriptive only.
    variances : ndarray
        Fitted per-regime variance, ascending (regime 0 is calmest).
    order : ndarray
        The permutation applied to the raw statsmodels regimes to reach canonical order.
    result : object
        The underlying fitted statsmodels results object (for diagnostics / info criteria).
    """

    filtered: pd.DataFrame
    smoothed: pd.DataFrame
    variances: np.ndarray
    order: np.ndarray
    result: object

    @property
    def n_regimes(self) -> int:
        return self.filtered.shape[1]

    def high_vol_filtered(self) -> pd.Series:
        """Filtered probability of the highest-variance (most stressed) regime."""
        return self.filtered.iloc[:, -1]


def _assemble_fit(res, n_regimes: int, index: pd.Index) -> RegimeFit:
    """Order regimes canonically by variance and package filtered + smoothed probabilities.

    ``index`` must match the number of probability rows the fit produced — this is the full return
    index for a plain fit, or the tail of it for an autoregressive fit that consumes the first
    ``order`` observations.
    """
    raw_var = np.asarray(res.params[[f"sigma2[{k}]" for k in range(n_regimes)]], dtype=float)
    order = np.argsort(raw_var)  # ascending variance -> canonical order

    filt = np.asarray(res.filtered_marginal_probabilities)[:, order]
    smooth = np.asarray(res.smoothed_marginal_probabilities)[:, order]
    cols = [f"regime_{k}" for k in range(n_regimes)]

    return RegimeFit(
        filtered=pd.DataFrame(filt, index=index, columns=cols),
        smoothed=pd.DataFrame(smooth, index=index, columns=cols),
        variances=raw_var[order],
        order=order,
        result=res,
    )


def fit_regimes(returns: pd.Series, n_regimes: int = 2) -> RegimeFit:
    """Fit a switching-variance Markov model to a return series.

    Parameters
    ----------
    returns : Series
        Date-indexed daily returns (e.g. from ``data.load_index_returns``).
    n_regimes : int
        Number of latent regimes. Default 2 (calm / stressed). State-count *selection* by
        information criterion is a separate evaluation step, not baked in here.
    """
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    y = returns.astype(float)
    # Fit on a positional index (dates are re-attached to the output below). Passing the DatetimeIndex
    # straight in only earns a "no frequency" warning — irregular trading days have no clean freq and
    # statsmodels ignores it anyway.
    y_fit = y.reset_index(drop=True)
    res = MarkovRegression(y_fit, k_regimes=n_regimes, trend="c", switching_variance=True).fit(disp=False)
    return _assemble_fit(res, n_regimes, y.index)


def fit_regimes_ar(returns: pd.Series, n_regimes: int = 2, order: int = 1) -> RegimeFit:
    """Robustness variant: a Markov-switching **autoregressive** model.

    The baseline ``fit_regimes`` assumes returns are i.i.d. within a regime. This variant adds an
    AR(``order``) mean, so it can tell apart "high variance" from "persistent momentum". If the
    inferred high-vol regime survives this richer mean structure, that is evidence the regimes are a
    volatility phenomenon and not an artefact of ignoring autocorrelation.

    The AR model consumes the first ``order`` observations, so the returned probabilities are aligned
    to ``returns.index[order:]``.
    """
    from statsmodels.tsa.regime_switching.markov_autoregression import MarkovAutoregression

    y = returns.astype(float)
    y_fit = y.reset_index(drop=True)
    res = MarkovAutoregression(
        y_fit, k_regimes=n_regimes, order=order, trend="c", switching_variance=True
    ).fit(disp=False)
    return _assemble_fit(res, n_regimes, y.index[order:])
