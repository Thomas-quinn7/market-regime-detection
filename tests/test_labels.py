"""Label scoring: AUC, lead/lag direction, detection lags and false alarms on hand-built series."""
import numpy as np
import pandas as pd

from regimes.labels import auc, episodes, lead_lag_auc, monthly_mean, score_detection


def _months(n: int = 60) -> pd.DatetimeIndex:
    return pd.date_range("2000-01-01", periods=n, freq="MS")


def test_auc_perfect_random_and_inverted():
    idx = _months(10)
    y = pd.Series([0, 0, 0, 0, 0, 1, 1, 1, 1, 1], index=idx)
    assert auc(pd.Series(np.arange(10.0), index=idx), y) == 1.0
    assert auc(pd.Series(-np.arange(10.0), index=idx), y) == 0.0
    assert auc(pd.Series(np.ones(10), index=idx), y) == 0.5


def test_lead_lag_peaks_where_the_signal_leads():
    idx = _months(120)
    y = pd.Series(0, index=idx)
    for start in (20, 60, 100):
        y.iloc[start:start + 8] = 1
    lead3 = y.shift(-3).fillna(0)  # signal switches on 3 months before the label
    ll = lead_lag_auc(lead3, y, leads=range(-6, 7))
    assert ll.idxmax() == 3


def test_detection_lags_misses_and_false_alarms():
    idx = _months(60)
    y = pd.Series(0, index=idx)
    y.iloc[10:15] = 1      # episode A
    y.iloc[40:44] = 1      # episode B
    on = pd.Series(0, index=idx)
    on.iloc[12:16] = 1     # catches A two months late
    on.iloc[28:30] = 1     # far from any episode: a false alarm
    sc = score_detection(on, y, before=6, after=12, slack=6)
    assert sc.lags == {idx[10]: 2}
    assert sc.misses == 1  # B is never flagged
    assert sc.false_alarms == 1
    assert len(episodes(on)) == 2


def test_monthly_mean_uses_month_start_index():
    d = pd.Series([1.0, 3.0, 10.0], index=pd.to_datetime(["2001-01-05", "2001-01-20", "2001-02-02"]))
    m = monthly_mean(d)
    assert list(m.index) == list(pd.to_datetime(["2001-01-01", "2001-02-01"]))
    assert list(m) == [2.0, 10.0]
