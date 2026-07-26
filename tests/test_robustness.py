"""AR-mean robustness: regimes should survive adding an autoregressive mean, and the AR and baseline
labellings should largely agree.
"""
import numpy as np
import pandas as pd

from regimes.evaluate import regime_agreement
from regimes.model import fit_regimes, fit_regimes_ar


def _two_regime(seed: int = 9) -> pd.Series:
    rng = np.random.default_rng(seed)
    y = np.concatenate([rng.normal(0.0, 0.5, 500), rng.normal(0.0, 3.0, 500)])
    return pd.Series(y, index=pd.date_range("2010-01-01", periods=len(y), freq="B"))


def test_ar_fit_aligns_and_separates_regimes():
    y = _two_regime()
    fit = fit_regimes_ar(y, n_regimes=2, order=1)
    # AR(1) consumes the first observation.
    assert fit.high_vol_filtered().index[0] == y.index[1]
    assert len(fit.high_vol_filtered()) == len(y) - 1
    hv = fit.high_vol_filtered()
    assert hv.iloc[500:].mean() > hv.iloc[:499].mean() + 0.3


def test_ar_and_baseline_agree():
    y = _two_regime()
    base = fit_regimes(y, n_regimes=2).high_vol_filtered()
    ar = fit_regimes_ar(y, n_regimes=2, order=1).high_vol_filtered()
    ag = regime_agreement(base, ar)
    assert ag.corr > 0.8
    assert ag.label_agreement > 0.8


def test_agreement_identity():
    y = _two_regime()
    p = fit_regimes(y, n_regimes=2).high_vol_filtered()
    ag = regime_agreement(p, p)
    assert ag.corr > 0.999
    assert ag.label_agreement == 1.0
