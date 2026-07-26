"""Multivariate Financial Turbulence regimes vs the single-asset model.

Answers the question the industry research raised: does feeding a multivariate cross-asset turbulence
series into the HMM add anything over the single-asset S&P 500 volatility model?

Run from the repo root:

    python examples/turbulence_regimes.py
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

from regimes.data import load_index_prices, load_index_returns, load_sector_returns  # noqa: E402
from regimes.evaluate import realised_vol, regime_agreement  # noqa: E402
from regimes.model import fit_regimes  # noqa: E402
from regimes.plots import plot_price_with_regimes  # noqa: E402
from regimes.turbulence import fit_turbulence_regimes  # noqa: E402

START, END = "2005-01-01", "2023-12-31"
FIG_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"


def main() -> None:
    warnings.simplefilter("ignore")
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    sectors = load_sector_returns(start=START, end=END)
    spx = load_index_returns(start=START, end=END)
    prices = load_index_prices(start=START, end=END)

    # Multivariate turbulence regime (9 sectors) vs single-asset S&P 500 volatility regime.
    turb = fit_turbulence_regimes(sectors, causal=True).high_vol_filtered()
    single = fit_regimes(spx, n_regimes=2).high_vol_filtered()

    # Does each predict next-month realised vol of the S&P 500?
    fut_vol = realised_vol(spx, 21).shift(-21)
    import pandas as pd

    def corr_with_fut(p):
        j = pd.concat({"p": p, "v": fut_vol}, axis=1, sort=True).dropna()
        return float(j["p"].corr(j["v"])), len(j)

    c_turb, n_turb = corr_with_fut(turb)
    c_single, n_single = corr_with_fut(single)
    ag = regime_agreement(single, turb)

    print("corr( high-stress probability , next-month S&P 500 realised vol )")
    print("-" * 62)
    print(f"{'single-asset S&P 500 volatility regime':<46}{c_single:6.3f}  (n={n_single})")
    print(f"{'multivariate turbulence regime (9 sectors)':<46}{c_turb:6.3f}  (n={n_turb})")
    print(f"\nagreement between the two regime series: corr {ag.corr:.3f}, "
          f"label agreement {ag.label_agreement:.3f} (n={ag.n})")

    fig = plot_price_with_regimes(
        prices, turb,
        title="S&P 500 with multivariate turbulence (cross-asset) high-stress regimes",
    )
    fig.savefig(FIG_DIR / "turbulence_regimes.png", dpi=140)
    print(f"\nfigure written to {FIG_DIR / 'turbulence_regimes.png'}")


if __name__ == "__main__":
    main()
