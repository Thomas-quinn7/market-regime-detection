"""The from-scratch Student-t EM must (a) reduce to the Gaussian model as nu grows, which validates
the implementation against a known-correct reference, and (b) recover fat-tailed regimes.
"""
import numpy as np
import pandas as pd

from regimes.evaluate import regime_agreement
from regimes.model import fit_regimes
from regimes.student_t import fit_regimes_student_t


def _two_regime(seed: int = 0, fat: bool = False) -> pd.Series:
    rng = np.random.default_rng(seed)
    if fat:
        calm = rng.standard_t(4, 500) * 0.5
        storm = rng.standard_t(4, 500) * 3.0
    else:
        calm = rng.normal(0.0, 0.5, 500)
        storm = rng.normal(0.0, 3.0, 500)
    y = np.concatenate([calm, storm])
    return pd.Series(y, index=pd.date_range("2010-01-01", periods=len(y), freq="B"))


def test_probabilities_valid_and_ordered():
    fit = fit_regimes_student_t(_two_regime(), n_regimes=2, nu=5.0)
    assert fit.filtered.to_numpy().min() >= 0.0 and fit.filtered.to_numpy().max() <= 1.0
    assert np.allclose(fit.filtered.sum(axis=1), 1.0)
    assert fit.result["sigma"][0] < fit.result["sigma"][-1]  # canonical ascending scale


def test_recovers_high_vol_in_storm():
    fit = fit_regimes_student_t(_two_regime(fat=True), n_regimes=2, nu=4.0)
    hv = fit.high_vol_filtered()
    assert hv.iloc[500:].mean() > hv.iloc[:500].mean() + 0.3


def test_reduces_to_gaussian_as_nu_grows():
    """The key correctness check: with huge nu the Student-t fit must match the Gaussian model."""
    y = _two_regime()
    t_big = fit_regimes_student_t(y, n_regimes=2, nu=1e6).high_vol_filtered()
    gauss = fit_regimes(y, n_regimes=2).high_vol_filtered()
    ag = regime_agreement(t_big, gauss)
    assert ag.corr > 0.99
    assert ag.label_agreement > 0.99
