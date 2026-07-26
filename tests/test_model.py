"""The model must recover a regime structure it was actually shown.

Synthetic two-regime series: a calm stretch (low variance) followed by a turbulent one (high
variance). A correct switching-variance fit should assign high P(high-vol regime) during the
turbulent stretch and low during the calm one, after canonical ordering.
"""
import numpy as np
import pandas as pd

from regimes.model import fit_regimes


def _synthetic_two_regime(seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    calm = rng.normal(0.0, 0.5, size=500)
    storm = rng.normal(0.0, 3.0, size=500)
    y = np.concatenate([calm, storm])
    idx = pd.date_range("2010-01-01", periods=len(y), freq="B")
    return pd.Series(y, index=idx, name="log_return_pct")


def test_canonical_ordering_is_ascending_variance():
    y = _synthetic_two_regime()
    fit = fit_regimes(y, n_regimes=2)
    assert fit.variances[0] < fit.variances[-1]


def test_high_vol_prob_higher_in_storm():
    y = _synthetic_two_regime()
    fit = fit_regimes(y, n_regimes=2)
    hv = fit.high_vol_filtered()
    calm_mean = hv.iloc[:500].mean()
    storm_mean = hv.iloc[500:].mean()
    assert storm_mean > calm_mean + 0.3
