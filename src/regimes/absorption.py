"""Absorption Ratio (Kritzman, Li, Page & Rigobon 2011) and the honest signal evaluation.

Roadmap item P2 (see ../../MARKET_REGIME_INDUSTRY_ROADMAP.md). The Absorption Ratio (AR) is the
fraction of a cross-section's total return variance absorbed by its first few principal components.
A high AR means risk is concentrated in a few factors, i.e. markets are tightly coupled and fragile;
a low AR means risk is dispersed and markets are resilient. It is definitionally cross-sectional.

The paper's early-warning signal is a standardised shift in the AR:

    dAR = (AR_short - AR_long) / sigma(AR_long)

with a one-standard-deviation spike as the trigger. Every input is a trailing moving average or
standard deviation, so the signal is causal.

The paper reports that essentially all of the worst drawdowns were *preceded by* a spike. That is a
recall statistic, and on its own it is not an edge: it says nothing about how often a spike fires with
NO drawdown following. This module therefore computes the full confusion matrix, so the precision, the
false-positive rate, the base rate and the lift are all reported, not just the flattering recall.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


def absorption_ratio(returns: pd.DataFrame, *, n_eigen: int | None = None, window: int = 500) -> pd.Series:
    """Trailing Absorption Ratio of a cross-asset return panel.

    For each day, PCA is run on the covariance of the trailing ``window`` days (ending that day, so
    the measure is causal), and the AR is the share of total variance in the top ``n_eigen``
    eigenvalues. ``n_eigen`` defaults to ~1/5 of the number of assets, per the paper.
    """
    if returns.shape[1] < 2:
        raise ValueError("the absorption ratio is a cross-asset measure; need at least two assets")
    X = returns.astype(float).to_numpy()
    T, n = X.shape
    k = n_eigen if n_eigen is not None else max(1, round(n / 5))

    ar = np.full(T, np.nan)
    for t in range(window - 1, T):
        past = X[t - window + 1:t + 1]  # trailing window, inclusive of t -> causal
        cov = np.cov(past, rowvar=False)
        eig = np.linalg.eigvalsh(cov)  # ascending
        total = eig.sum()
        if total > 0:
            ar[t] = eig[-k:].sum() / total
    return pd.Series(ar, index=returns.index, name="absorption_ratio")


def dar_signal(ar: pd.Series, *, short: int = 15, long: int = 252) -> pd.Series:
    """Standardised AR shift dAR = (AR_short - AR_long) / sigma(AR_long). All inputs trailing."""
    ar_short = ar.rolling(short).mean()
    ar_long = ar.rolling(long).mean()
    sigma_long = ar.rolling(long).std()
    return ((ar_short - ar_long) / sigma_long).rename("dAR")


def forward_drawdown(prices: pd.Series, horizon: int) -> pd.Series:
    """Worst point-to-start return over the next ``horizon`` days: min_k (P[t+k]/P[t] - 1)."""
    p = prices.astype(float).to_numpy()
    T = len(p)
    fdd = np.full(T, np.nan)
    for t in range(T):
        end = min(t + horizon, T - 1)
        if end > t:
            fdd[t] = p[t + 1:end + 1].min() / p[t] - 1.0
    return pd.Series(fdd, index=prices.index, name="forward_drawdown")


@dataclass
class SignalEval:
    """Confusion-matrix summary of a binary alert against a binary forward outcome."""

    recall: float           # P(alert | drawdown ahead) -- the paper's "preceded by a spike" number
    precision: float        # P(drawdown ahead | alert)
    false_alarm_rate: float # 1 - precision: share of alerts with NO drawdown (the omitted number)
    fpr: float              # P(alert | no drawdown ahead) -- classical false-positive rate
    base_rate: float        # P(drawdown ahead) unconditionally
    lift: float             # precision / base_rate: >1 means the alert beats the base rate
    alert_frequency: float  # P(alert)
    n: int


def signal_confusion(alert: pd.Series, outcome: pd.Series) -> SignalEval:
    """Confusion matrix of a boolean alert vs a boolean outcome, on their shared, non-null dates."""
    j = pd.concat({"a": alert, "o": outcome}, axis=1, sort=True).dropna()
    a = j["a"].to_numpy().astype(bool)
    o = j["o"].to_numpy().astype(bool)
    tp = int((a & o).sum())
    fp = int((a & ~o).sum())
    fn = int((~a & o).sum())
    tn = int((~a & ~o).sum())
    n = len(j)

    def safe(num, den):
        return float(num / den) if den else float("nan")

    precision = safe(tp, tp + fp)
    base_rate = safe(tp + fn, n)
    return SignalEval(
        recall=safe(tp, tp + fn),
        precision=precision,
        false_alarm_rate=(1.0 - precision if not np.isnan(precision) else float("nan")),
        fpr=safe(fp, fp + tn),
        base_rate=base_rate,
        lift=safe(precision, base_rate) if base_rate else float("nan"),
        alert_frequency=safe(tp + fp, n),
        n=n,
    )


def evaluate_absorption_signal(
    returns: pd.DataFrame,
    prices: pd.Series,
    *,
    n_eigen: int | None = None,
    ar_window: int = 500,
    threshold: float = 1.0,
    horizon: int = 21,
    drawdown: float = 0.05,
) -> SignalEval:
    """End-to-end honest evaluation of the AR spike signal as a drawdown warning.

    Alert = dAR >= ``threshold`` (a one-SD spike by default). Outcome = a drawdown of at least
    ``drawdown`` (5% by default) at some point over the next ``horizon`` days. Returns the full
    confusion summary so the false-alarm rate and lift are visible next to the recall.
    """
    ar = absorption_ratio(returns, n_eigen=n_eigen, window=ar_window)
    alert = dar_signal(ar) >= threshold
    outcome = forward_drawdown(prices, horizon) <= -abs(drawdown)
    return signal_confusion(alert, outcome)
