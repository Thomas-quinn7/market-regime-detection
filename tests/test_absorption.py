"""Absorption Ratio (P2) and the honest signal evaluation.

The confusion-matrix arithmetic is the load-bearing part (it is the repo's actual contribution over
the source papers), so it is tested exactly against hand-built arrays.
"""
import numpy as np
import pandas as pd

from regimes.absorption import (
    absorption_ratio,
    dar_signal,
    evaluate_absorption_signal,
    signal_confusion,
)


def test_signal_confusion_exact():
    idx = pd.date_range("2020-01-01", periods=4, freq="B")
    alert = pd.Series([True, True, False, False], index=idx)
    outcome = pd.Series([True, False, False, True], index=idx)
    ev = signal_confusion(alert, outcome)
    assert ev.n == 4
    assert ev.precision == 0.5          # TP=1, FP=1
    assert ev.recall == 0.5             # TP=1, FN=1
    assert ev.false_alarm_rate == 0.5   # 1 - precision
    assert ev.fpr == 0.5                # FP=1, TN=1
    assert ev.base_rate == 0.5          # 2 of 4 outcomes true
    assert ev.lift == 1.0               # precision / base_rate
    assert ev.alert_frequency == 0.5


def _panel(seed: int, correlated: bool, T: int = 800, n: int = 5) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    if correlated:
        X = rng.normal(0, 1, (T, 1)) + rng.normal(0, 0.2, (T, n))  # one dominant factor
    else:
        X = rng.normal(0, 1, (T, n))                                # independent
    idx = pd.date_range("2010-01-01", periods=T, freq="B")
    return pd.DataFrame(X, columns=[f"a{i}" for i in range(n)], index=idx)


def test_absorption_ratio_higher_when_coupled():
    ar_corr = absorption_ratio(_panel(0, correlated=True), window=250).dropna()
    ar_indep = absorption_ratio(_panel(1, correlated=False), window=250).dropna()
    assert (ar_corr <= 1.0).all() and (ar_corr >= 0.0).all()
    assert ar_corr.median() > ar_indep.median() + 0.2


def test_absorption_ratio_is_causal():
    panel = _panel(2, correlated=True)
    ar = absorption_ratio(panel, window=250)
    scrambled = panel.copy()
    rng = np.random.default_rng(3)
    scrambled.iloc[600:] = rng.normal(0, 5, (panel.shape[0] - 600, panel.shape[1]))
    ar2 = absorption_ratio(scrambled, window=250)
    assert np.allclose(ar.iloc[:600], ar2.iloc[:600], equal_nan=True)


def test_absorption_ratio_requires_multiple_assets():
    panel = _panel(0, correlated=True)[["a0"]]
    try:
        absorption_ratio(panel)
    except ValueError:
        return
    raise AssertionError("expected ValueError for a single asset")


def test_dar_signal_spikes_on_a_jump():
    idx = pd.date_range("2010-01-01", periods=400, freq="B")
    ar = pd.Series(np.concatenate([np.full(300, 0.5), np.full(100, 0.9)]), index=idx)
    dar = dar_signal(ar, short=15, long=252)
    assert dar.max() > 1.0  # a sustained regime jump produces a >1 SD standardized shift


def test_evaluate_absorption_signal_returns_valid_rates():
    panel = _panel(0, correlated=True, T=900)
    # A synthetic price path just to exercise the pipeline end to end.
    rng = np.random.default_rng(5)
    prices = pd.Series(100 * np.exp(np.cumsum(rng.normal(0, 0.01, 900))), index=panel.index)
    ev = evaluate_absorption_signal(panel, prices, ar_window=250, horizon=21, drawdown=0.05)
    for r in (ev.precision, ev.recall, ev.false_alarm_rate, ev.fpr, ev.base_rate, ev.alert_frequency):
        assert np.isnan(r) or 0.0 <= r <= 1.0
    assert ev.n > 0
