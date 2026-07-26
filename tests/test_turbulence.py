"""Financial Turbulence (P1): a multivariate stress measure feeding the HMM.

Tests isolate the two guarantees: (a) turbulence spikes on cross-asset stress and is causal, and
(b) the turbulence HMM separates a normal from an ex-normal regime.
"""
import numpy as np
import pandas as pd

from regimes.turbulence import financial_turbulence, fit_turbulence_regimes


def _panel_with_stress(seed: int = 0) -> pd.DataFrame:
    """Correlated calm markets with a decorrelated, high-volatility stress block in the middle."""
    rng = np.random.default_rng(seed)
    n, T = 5, 1400
    common = rng.normal(0.0, 1.0, (T, 1))
    X = common + rng.normal(0.0, 0.3, (T, n))     # tightly coupled calm
    X[900:1100] = rng.normal(0.0, 4.0, (200, n))  # stress: big moves, broken correlation
    idx = pd.date_range("2010-01-01", periods=T, freq="B")
    return pd.DataFrame(X, columns=list("ABCDE"), index=idx)


def test_turbulence_spikes_on_stress():
    ft = financial_turbulence(_panel_with_stress(), causal=True, window=252, min_periods=252)
    calm = ft.iloc[400:900].mean()
    storm = ft.iloc[900:1100].mean()
    assert storm > 3 * calm


def test_turbulence_is_causal():
    panel = _panel_with_stress()
    ft = financial_turbulence(panel, causal=True, window=252, min_periods=252)
    future_scrambled = panel.copy()
    rng = np.random.default_rng(7)
    future_scrambled.iloc[1200:] = rng.normal(0.0, 7.0, (panel.shape[0] - 1200, panel.shape[1]))
    ft2 = financial_turbulence(future_scrambled, causal=True, window=252, min_periods=252)
    # Turbulence before the scrambled region must be identical: no future leakage.
    assert np.allclose(ft.iloc[:1100], ft2.iloc[:1100], equal_nan=True)


def test_turbulence_requires_multiple_assets():
    panel = _panel_with_stress()[["A"]]
    try:
        financial_turbulence(panel)
    except ValueError:
        return
    raise AssertionError("expected ValueError for a single asset")


def test_fit_turbulence_regimes_separates_normal_from_exnormal():
    panel = _panel_with_stress()
    # Full-sample turbulence isolates the regime-fitting logic from trailing-window dynamics.
    fit = fit_turbulence_regimes(panel, causal=False)
    consts = [float(fit.result.params[f"const[{k}]"]) for k in range(2)]
    assert consts[0] < consts[1]  # ordered by mean: last regime is the high-turbulence one
    hv = fit.high_vol_filtered()
    idx = panel.index
    storm = hv.loc[idx[900]:idx[1099]].mean()
    calm = pd.concat([hv.loc[idx[300]:idx[899]], hv.loc[idx[1100]:]]).mean()
    assert storm > calm + 0.3
