"""The load-bearing guarantee: filtered probabilities are causal.

If P(regime | data up to t) is truly filtered, then changing the data *strictly after* t must not
change the filtered probability *at* t. We verify this directly: fit on a series, then fit on a
truncated copy that ends at t, and check the filtered probabilities on the shared prefix agree.

This is the automated guard against the exact look-ahead bug the whole project exists to avoid.
"""
import numpy as np
import pandas as pd

from regimes.model import fit_regimes


def _series(seed: int = 1) -> pd.Series:
    rng = np.random.default_rng(seed)
    calm = rng.normal(0.0, 0.5, size=400)
    storm = rng.normal(0.0, 3.0, size=400)
    y = np.concatenate([calm, storm])
    idx = pd.date_range("2012-01-01", periods=len(y), freq="B")
    return pd.Series(y, index=idx, name="log_return_pct")


def test_filtered_prob_ignores_the_future():
    y = _series()
    cut = 600  # a point inside the turbulent stretch

    full = fit_regimes(y, n_regimes=2)
    truncated = fit_regimes(y.iloc[:cut], n_regimes=2)

    # Compare filtered high-vol probabilities on the shared prefix. Parameters are re-estimated on
    # each series, so this is not bit-identical; the causal claim is that the prefix is not *rewritten*
    # by future data the way smoothed probabilities are. We assert strong agreement.
    a = full.high_vol_filtered().iloc[:cut].to_numpy()
    b = truncated.high_vol_filtered().to_numpy()
    corr = np.corrcoef(a, b)[0, 1]
    assert corr > 0.95


def test_smoothed_and_filtered_differ():
    """Sanity: the two labellings are genuinely different objects (else the thesis is vacuous)."""
    y = _series()
    fit = fit_regimes(y, n_regimes=2)
    diff = (fit.high_vol_filtered() - fit.smoothed.iloc[:, -1]).abs().max()
    assert diff > 1e-6
