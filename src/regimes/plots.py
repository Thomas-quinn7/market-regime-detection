"""Plotting helpers. Every figure is explicitly tagged filtered (causal) or smoothed (descriptive) so
a reader can never mistake a look-ahead label for a tradeable one.
"""
from __future__ import annotations

import pandas as pd

from .model import RegimeFit


def plot_regime_probabilities(returns: pd.Series, fit: RegimeFit, *, kind: str = "filtered"):
    """Plot the high-volatility regime probability over price/returns.

    Parameters
    ----------
    kind : {"filtered", "smoothed"}
        ``filtered`` is causal and the only one valid for forward claims; ``smoothed`` is descriptive
        and uses future data. The chosen kind is written into the title so it is unmistakable.
    """
    import matplotlib.pyplot as plt

    if kind not in {"filtered", "smoothed"}:
        raise ValueError("kind must be 'filtered' or 'smoothed'")
    prob = (fit.high_vol_filtered() if kind == "filtered" else fit.smoothed.iloc[:, -1])

    fig, (ax_r, ax_p) = plt.subplots(2, 1, sharex=True, figsize=(11, 6))
    ax_r.plot(returns.index, returns.values, lw=0.6, color="0.4")
    ax_r.set_ylabel("daily log return (%)")
    ax_p.fill_between(prob.index, 0, prob.values, color="crimson", alpha=0.6)
    ax_p.set_ylabel(f"P(high-vol regime)\n[{kind.upper()}]")
    ax_p.set_ylim(0, 1)
    fig.suptitle(f"Volatility regimes — {kind} probabilities"
                 + ("  (CAUSAL)" if kind == "filtered" else "  (uses future data — descriptive only)"))
    fig.tight_layout()
    return fig


def plot_price_with_regimes(prices: pd.Series, high_vol_prob: pd.Series, *, threshold: float = 0.5,
                            title: str = "S&P 500 with inferred high-volatility regimes"):
    """Plot the index level with high-volatility stretches shaded.

    ``high_vol_prob`` should be a CAUSAL (filtered / out-of-sample) probability — shading is only
    honest if the label at each date used no future information. Days with prob >= ``threshold`` are
    shaded.
    """
    import matplotlib.pyplot as plt

    hv = high_vol_prob.reindex(prices.index).ffill()
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(prices.index, prices.values, color="#222222", lw=0.9, label="S&P 500")
    ax.fill_between(prices.index, prices.min(), prices.max(),
                    where=(hv >= threshold).to_numpy(), color="#d1495b", alpha=0.18,
                    label=f"high-vol regime (P >= {threshold:g})", step="mid")
    ax.set_ylabel("index level")
    ax.set_title(title)
    ax.legend(loc="upper left", framealpha=0.9)
    ax.margins(x=0)
    fig.tight_layout()
    return fig
