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
    model = MarkovRegression(y_fit, k_regimes=n_regimes, trend="c", switching_variance=True)
    res = model.fit(disp=False)

    raw_var = np.asarray(res.params[[f"sigma2[{k}]" for k in range(n_regimes)]], dtype=float)
    order = np.argsort(raw_var)  # ascending variance -> canonical order

    filt = np.asarray(res.filtered_marginal_probabilities)[:, order]
    smooth = np.asarray(res.smoothed_marginal_probabilities)[:, order]
    cols = [f"regime_{k}" for k in range(n_regimes)]

    return RegimeFit(
        filtered=pd.DataFrame(filt, index=y.index, columns=cols),
        smoothed=pd.DataFrame(smooth, index=y.index, columns=cols),
        variances=raw_var[order],
        order=order,
        result=res,
    )
