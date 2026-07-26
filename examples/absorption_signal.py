"""Roadmap P2: the Absorption Ratio spike signal, evaluated honestly.

The Kritzman et al. papers report that essentially all major drawdowns were preceded by an absorption-
ratio spike (a recall statistic). They do not report how often a spike fires with no drawdown
following. This script reports the full confusion matrix, so the false-alarm rate and the lift sit
next to the recall.

Run from the repo root:

    python examples/absorption_signal.py
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from regimes.absorption import (  # noqa: E402
    absorption_ratio,
    dar_signal,
    evaluate_absorption_signal,
)
from regimes.data import load_index_prices, load_sector_returns  # noqa: E402

START, END = "2005-01-01", "2023-12-31"
FIG_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"


def main() -> None:
    warnings.simplefilter("ignore")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    sectors = load_sector_returns(start=START, end=END)
    prices = load_index_prices(start=START, end=END)

    ar = absorption_ratio(sectors, window=500)
    dar = dar_signal(ar)
    alert = (dar >= 1.0)

    print("Absorption-ratio spike as a drawdown warning (S&P 500, 2005-2023)")
    print("alert = dAR >= 1 SD; outcome = drawdown of >= X% within the next 21 trading days\n")
    header = f"{'drawdown':>9} | {'recall':>6} | {'precision':>9} | {'false-alarm':>11} | {'base':>5} | {'lift':>5}"
    print(header)
    print("-" * len(header))
    for dd in (0.05, 0.10):
        ev = evaluate_absorption_signal(sectors, prices, threshold=1.0, horizon=21, drawdown=dd)
        print(f"{int(dd*100):>7}% | {ev.recall:>6.2f} | {ev.precision:>9.2f} | "
              f"{ev.false_alarm_rate:>11.2f} | {ev.base_rate:>5.2f} | {ev.lift:>5.2f}")
    print(f"\nalerts fire on {alert.mean():.0%} of days; recall is the 'preceded by a spike' number the "
          "papers report, precision/false-alarm/lift are what they omit.")

    # Figure: S&P 500 with alert days shaded, so false alarms are visible against actual drawdowns.
    import matplotlib.pyplot as plt

    hi = alert.reindex(prices.index).fillna(False)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(prices.index, prices.values, color="#222222", lw=0.9, label="S&P 500")
    ax.fill_between(prices.index, prices.min(), prices.max(), where=hi.to_numpy(),
                    color="#d1495b", alpha=0.18, step="mid", label="absorption-ratio alert (dAR >= 1 SD)")
    ax.set_ylabel("index level")
    ax.set_title("Absorption-ratio alerts vs the S&P 500 (many alerts, not all followed by a drawdown)")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.margins(x=0)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "absorption_alerts.png", dpi=140)
    print(f"\nfigure written to {FIG_DIR / 'absorption_alerts.png'}")


if __name__ == "__main__":
    main()
