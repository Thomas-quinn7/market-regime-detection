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


def test_filtered_prefix_is_identical_under_frozen_parameters_and_smoothed_is_not():
    """Frozen-parameter prefix identity. With the parameters held fixed, the filtered probability at
    t depends on returns up to t only, so filtering the full series and filtering a truncated copy
    give the same numbers on the shared prefix, to machine precision. The smoothed probabilities use
    the whole sample and MUST fail the same check; a leaky implementation that returned smoothed
    probabilities would be caught here (the old correlation check passed for both)."""
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    # A 2-to-1 vol ratio (not the 6-to-1 of _series) so the filter needs a few days to switch and
    # the smoother has something to rewrite; the cut is three days into the storm.
    rng = np.random.default_rng(1)
    y = pd.Series(np.concatenate([rng.normal(0.0, 1.0, 400), rng.normal(0.0, 2.0, 400)]),
                  index=pd.date_range("2012-01-01", periods=800, freq="B"))
    cut = 403
    fit = fit_regimes(y, n_regimes=2)
    params = fit.result.params
    full = MarkovRegression(y.to_numpy(), k_regimes=2, trend="c", switching_variance=True)
    part = MarkovRegression(y.to_numpy()[:cut], k_regimes=2, trend="c", switching_variance=True)
    f_full = np.asarray(full.filter(params).filtered_marginal_probabilities)[:cut]
    f_part = np.asarray(part.filter(params).filtered_marginal_probabilities)
    assert np.allclose(f_full, f_part, atol=1e-12, rtol=0)
    s_full = np.asarray(full.smooth(params).smoothed_marginal_probabilities)[:cut]
    s_part = np.asarray(part.smooth(params).smoothed_marginal_probabilities)
    assert np.abs(s_full - s_part).max() > 0.05  # the smoother rewrites the prefix near the cut
    # and fit_regimes' filtered columns are the filter output, not the smoother's
    assert np.allclose(fit.filtered.to_numpy().max(axis=1), np.asarray(full.filter(params).filtered_marginal_probabilities).max(axis=1), atol=1e-10)


def test_smoothed_and_filtered_differ():
    """Sanity: the two labellings are genuinely different objects (else the thesis is vacuous)."""
    y = _series()
    fit = fit_regimes(y, n_regimes=2)
    diff = (fit.high_vol_filtered() - fit.smoothed.iloc[:, -1]).abs().max()
    assert diff > 1e-6
