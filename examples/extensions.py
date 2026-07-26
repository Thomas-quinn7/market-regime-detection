"""Reproducible results for the three extensions in docs/WRITEUP.md:

  1. State-count selection (AIC/BIC).
  2. Cross-asset concordance across the nine SPDR sector ETFs (systemic vs sector-specific stress).
  3. AR-mean robustness check.

Run from the repo root:

    python examples/extensions.py
"""
from __future__ import annotations

import warnings
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from regimes.cross_asset import sector_regime_concordance  # noqa: E402
from regimes.data import load_index_returns, load_sector_returns  # noqa: E402
from regimes.evaluate import regime_agreement  # noqa: E402
from regimes.model import fit_regimes, fit_regimes_ar  # noqa: E402
from regimes.selection import select_n_regimes  # noqa: E402
from regimes.student_t import fit_regimes_student_t  # noqa: E402

START, END = "2005-01-01", "2023-12-31"
FIG_DIR = Path(__file__).resolve().parents[1] / "docs" / "figures"


def main() -> None:
    warnings.simplefilter("ignore")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    spx = load_index_returns(start=START, end=END)

    print("== 1. State-count selection (S&P 500) ==")
    sel = select_n_regimes(spx, candidates=(2, 3, 4))
    print(sel.table.round(1))
    print(f"BIC picks {sel.best_bic}, AIC picks {sel.best_aic}\n")

    print("== 2. Cross-asset concordance (9 SPDR sectors) ==")
    sectors = load_sector_returns(start=START, end=END)
    ca = sector_regime_concordance(sectors, n_regimes=2)
    print(f"mean pairwise corr of sector high-vol probabilities: {ca.mean_pairwise_corr:.3f}")
    print(f"breadth (share of sectors in high-vol) mean {ca.breadth.mean():.2f}, "
          f"max {ca.breadth.max():.2f}\n")

    print("== 3. AR-mean robustness (S&P 500) ==")
    base = fit_regimes(spx, n_regimes=2).high_vol_filtered()
    ar = fit_regimes_ar(spx, n_regimes=2, order=1).high_vol_filtered()
    ag = regime_agreement(base, ar)
    print(f"baseline vs AR(1): corr {ag.corr:.3f}, label agreement {ag.label_agreement:.3f} (n={ag.n})\n")

    print("== 4. Student-t (fat-tail) robustness (S&P 500) ==")
    tfit = fit_regimes_student_t(spx, n_regimes=2, nu=5.0)
    agt = regime_agreement(base, tfit.high_vol_filtered())
    print(f"baseline vs Student-t(nu=5): corr {agt.corr:.3f}, "
          f"label agreement {agt.label_agreement:.3f} (n={agt.n})")

    # Figure: cross-asset breadth over time — a systemic-stress gauge.
    fig, ax = plt.subplots(figsize=(12, 3.6))
    ax.fill_between(ca.breadth.index, 0, ca.breadth.values, color="#d1495b", alpha=0.5)
    ax.set_ylim(0, 1)
    ax.set_ylabel("share of sectors\nin high-vol regime")
    ax.set_title("Cross-asset breadth: fraction of the 9 sectors in their high-volatility regime")
    ax.margins(x=0)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "sector_breadth.png", dpi=140)
    print(f"\nfigure written to {FIG_DIR / 'sector_breadth.png'}")


if __name__ == "__main__":
    main()
