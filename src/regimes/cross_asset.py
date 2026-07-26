"""Cross-asset volatility regimes: is the high-vol state systemic or sector-specific?

Rather than fit one multivariate model (statsmodels' switching models are univariate), this takes the
honest, legible route: fit the same 2-state switching-variance model to each sector independently,
then ask whether their high-volatility regimes *coincide*. If a market-wide stress state exists, the
per-sector high-vol probabilities should move together, and market "breadth" (the share of sectors in
their high-vol regime) should spike during known crises.

Every probability used here is the FILTERED (causal) one, consistent with the rest of the project.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .model import fit_regimes


@dataclass
class CrossAssetRegimes:
    """Per-sector high-vol probabilities and their agreement.

    Attributes
    ----------
    high_vol_prob : DataFrame
        Filtered P(high-vol regime) per sector (one column each), on their shared dates.
    breadth : Series
        Mean high-vol probability across sectors per date — a market-wide stress gauge in [0, 1].
    mean_pairwise_corr : float
        Average correlation between sectors' high-vol probabilities. High => the stress state is
        systemic, not idiosyncratic.
    """

    high_vol_prob: pd.DataFrame
    breadth: pd.Series
    mean_pairwise_corr: float


def sector_regime_concordance(returns: pd.DataFrame, n_regimes: int = 2) -> CrossAssetRegimes:
    """Fit per-column regimes and measure how much their high-vol states coincide.

    Parameters
    ----------
    returns : DataFrame
        One column of daily returns per asset (e.g. ``data.load_sector_returns``).
    """
    if returns.shape[1] < 2:
        raise ValueError("need at least two assets to measure concordance")

    probs = {col: fit_regimes(returns[col].dropna(), n_regimes).high_vol_filtered()
             for col in returns.columns}
    hv = pd.DataFrame(probs).dropna(how="any")

    return _package(hv)


def _package(hv: pd.DataFrame) -> "CrossAssetRegimes":
    corr = hv.corr().to_numpy()
    off_diag = corr[~np.eye(corr.shape[0], dtype=bool)]  # exclude the 1.0 diagonal
    return CrossAssetRegimes(
        high_vol_prob=hv,
        breadth=hv.mean(axis=1).rename("breadth"),
        mean_pairwise_corr=float(off_diag.mean()),
    )


def walk_forward_breadth(
    returns: pd.DataFrame,
    *,
    n_regimes: int = 2,
    min_train: int = 756,
    step: int = 63,
    horizon: int = 21,
) -> CrossAssetRegimes:
    """Out-of-sample cross-asset breadth.

    The descriptive ``sector_regime_concordance`` fits each sector on the full sample. This is its
    causal counterpart: each sector's high-vol probability comes from ``evaluate.walk_forward_oos``,
    so every value used only past returns and past-estimated parameters. The resulting breadth is a
    gauge you could actually have computed in real time, not one that peeked at the future.

    Slower than the descriptive version (one walk-forward per asset), so intended for a considered
    run rather than an inner loop.
    """
    from .evaluate import walk_forward_oos

    if returns.shape[1] < 2:
        raise ValueError("need at least two assets to measure concordance")

    probs = {}
    for col in returns.columns:
        wf = walk_forward_oos(returns[col].dropna(), n_regimes=n_regimes,
                              min_train=min_train, step=step, horizon=horizon)
        probs[col] = wf.high_vol_prob
    hv = pd.DataFrame(probs).dropna(how="any")
    return _package(hv)
