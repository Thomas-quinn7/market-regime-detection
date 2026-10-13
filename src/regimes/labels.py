"""Scoring a regime signal against outside labels: is the hidden state a real economic regime?

Everywhere else the regime model is scored as a volatility forecaster, which a two-state model is
badly built for. A regime model's own claim is different: that it recovers discrete states. With
no ground truth that cannot be tested directly, but it can be compared against regimes defined
outside the model, such as NBER recessions or Fed easing cycles. These labels are used for scoring
only, never as inputs: NBER announces its dates months after the fact.

All functions work on monthly series (month-start index). Daily signals are averaged per month.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def monthly_mean(daily: pd.Series) -> pd.Series:
    """Average of a daily series per calendar month, indexed by the first day of the month."""
    return daily.groupby(daily.index.to_period("M")).mean().to_timestamp()


def auc(score: pd.Series, label: pd.Series) -> float:
    """Area under the ROC curve of ``score`` for a 0/1 ``label`` (Mann-Whitney, ties count half).

    0.5 is no information; 1.0 ranks every labelled month above every unlabelled one.
    """
    j = pd.concat({"s": score, "y": label}, axis=1).dropna()
    pos, neg = j.loc[j["y"] == 1, "s"].to_numpy(), j.loc[j["y"] == 0, "s"].to_numpy()
    if len(pos) == 0 or len(neg) == 0:
        return float("nan")
    ranks = pd.Series(np.concatenate([pos, neg])).rank().to_numpy()
    return float((ranks[: len(pos)].sum() - len(pos) * (len(pos) + 1) / 2) / (len(pos) * len(neg)))


def lead_lag_auc(score: pd.Series, label: pd.Series, leads=range(-12, 13)) -> pd.Series:
    """AUC of ``score`` at month t against ``label`` at month t + k, for each k in ``leads``.

    A peak at k > 0 means the signal is high *before* the labelled months (it leads); k < 0 means
    it lags them.
    """
    return pd.Series({k: auc(score, label.shift(-k)) for k in leads}, name="auc")


def episodes(flag: pd.Series) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
    """Runs of consecutive 1s in a 0/1 monthly series, as (first month, last month)."""
    f = flag.fillna(0).astype(int)
    starts = f.index[(f == 1) & (f.shift(1, fill_value=0) == 0)]
    ends = f.index[(f == 1) & (f.shift(-1, fill_value=0) == 0)]
    return list(zip(starts, ends))


def threshold_for_rate(score: pd.Series, rate: float) -> float:
    """The threshold at which ``score`` is "on" for a share ``rate`` of months.

    Used to give a baseline signal the same alarm rate as the regime model, so the comparison is
    about where the alarms fall, not how many there are.
    """
    return float(score.dropna().quantile(1.0 - rate))


@dataclass
class DetectionScore:
    lags: dict          # label episode start -> months from that start to the first "on" month
    misses: int         # label episodes with no "on" month in the window
    false_alarms: int   # "on" episodes that overlap no label episode (with ``slack`` months each side)
    on_share: float     # share of months the signal is on


def score_detection(on: pd.Series, label: pd.Series, *, before: int = 6, after: int = 12,
                    slack: int = 6) -> DetectionScore:
    """Detection lag, misses and false alarms of a 0/1 signal against 0/1 label episodes.

    For each label episode starting in month s, the lag is the first month in [s - before,
    s + after] where the signal is on, minus s (negative = early). An "on" episode is a false alarm
    if it does not come within ``slack`` months of any label episode.
    """
    on = on.reindex(label.index).fillna(0).astype(int)
    lab_eps = episodes(label)
    months = list(label.index)
    lags, misses = {}, 0
    for s, _ in lab_eps:
        i = months.index(s)
        window = on.iloc[max(0, i - before): i + after + 1]
        hit = window[window == 1]
        if len(hit):
            lags[s] = months.index(hit.index[0]) - i
        else:
            misses += 1
    false_alarms = 0
    for a, b in episodes(on):
        ia, ib = months.index(a), months.index(b)
        near = any(months.index(s) - slack <= ib and ia <= months.index(e) + slack for s, e in lab_eps)
        false_alarms += 0 if near else 1
    return DetectionScore(lags=lags, misses=misses, false_alarms=false_alarms,
                          on_share=float(on.mean()))
