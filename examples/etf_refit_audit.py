"""Audit of the ETF holdout walk-forwards: frozen checkpoints against the reproduction's full refit.

Class: reproduction (sections 1 and 3) and post hoc, from the frozen and reproduced walk-forwards
(section 2). Not a test of any claim; the registered verdicts stand as committed.

    python examples/etf_refit_audit.py

1. Per asset and model, how far the refitted walk-forward (``docs/results/reproductions/etf/``,
   written by ``examples/reproduce_holdout.py etf``) is from the frozen run's checkpoint
   (``data/checkpoints/msgarch_credit/``): largest and median absolute forecast difference, days
   differing by more than 0.01 (daily percent), and for MS-GARCH the refits whose log-likelihood
   differs by more than 0.01.
2. MS-GARCH refits at a boundary, in both: a regime whose GARCH variance collapses to zero
   (omega and beta both below 1e-6) or whose stay probability is below 0.05 (the fit's floor is
   0.001). Such a regime is visited for single days and is a known degenerate optimum of mixture
   likelihoods.
3. Floating-point sensitivity of the GJR-GARCH walk-forward on USO: the same code, data and
   packages run in subprocesses with different OpenBLAS thread counts, against the checkpoint.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "examples"))
REFIT = REPO / "docs" / "results" / "reproductions" / "etf" / "walk_forwards"
FROZEN = REPO / "data" / "checkpoints" / "msgarch_credit"
ASSETS = ["crude_oil_uso", "gold_gld", "emerging_markets_eem", "brazil_ewz"]
FUNCS = {"hmm": "walk_forward_oos", "garch": "walk_forward_gjr", "ms_garch": "walk_forward_msgarch"}


def read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0, parse_dates=True, float_precision="round_trip")


def refit_files() -> dict[tuple[str, str], str]:
    """(asset, model) -> stem of the refitted walk-forward, in the order the holdout ran them."""
    index = json.loads((REFIT / "index.json").read_text())
    out = {}
    for model, func in FUNCS.items():
        stems = [e["stem"] for e in index if e["function"] == func]
        out.update({(a, model): s for a, s in zip(ASSETS, stems)})
    return out


def boundary(p: pd.DataFrame) -> pd.Series:
    bad = pd.Series(False, index=p.index)
    for s in "01":
        bad |= ((p[f"omega{s}"] < 1e-6) & (p[f"beta{s}"] < 1e-6)) | (p[f"p{s}{s}"] < 0.05)
    return bad


def garch_once() -> None:
    """Child process: one GJR-GARCH walk-forward on USO; print its gap to the checkpoint and a hash."""
    warnings.simplefilter("ignore")
    from msgarch_credit_holdout import HOLDOUT_END, load_asset

    from regimes.garch import walk_forward_gjr
    returns, _ = load_asset("USO", "OVXCLS", HOLDOUT_END)
    wf = walk_forward_gjr(returns, min_train=756, step=63, horizon=21)
    frozen = read(next(FROZEN.glob("crude_oil_uso__garch__*[0-9].csv")))["implied_vol"]
    gap = float((wf.implied_vol.reindex(frozen.index) - frozen).abs().max())
    print(f"{gap:.4g} {hashlib.sha256(wf.implied_vol.to_numpy().tobytes()).hexdigest()[:12]}")


def main() -> None:
    if sys.argv[1:] == ["--garch-once"]:
        garch_once()
        return
    stems = refit_files()
    print("1. refit vs frozen checkpoint (reproduction; forecasts in daily percent)")
    rows = []
    for asset in ASSETS:
        for model in FUNCS:
            frozen_path = next(FROZEN.glob(f"{asset}__{model}__*[0-9].csv"))
            frozen = read(frozen_path)["implied_vol"]
            refit = read(REFIT / f"{stems[asset, model]}__implied_vol.csv").iloc[:, 0]
            gap = (refit.reindex(frozen.index) - frozen).abs()
            row = {"asset": asset, "model": model, "days": int(frozen.notna().sum()),
                   "max |diff|": f"{gap.max():.3g}", "median |diff|": f"{gap.median():.2g}",
                   "days > 0.01": int((gap > 0.01).sum()), "refits": "", "loglik moved > 0.01": ""}
            if model == "ms_garch":
                pf = read(frozen_path.with_suffix(".params.csv"))
                pr = read(REFIT / f"{stems[asset, model]}__params.csv")
                dll = pr["loglik"].to_numpy() - pf["loglik"].to_numpy()
                row["refits"] = len(pf)
                row["loglik moved > 0.01"] = (f"{int((np.abs(dll) > 0.01).sum())} "
                                              f"(range {dll.min():+.1f} to {dll.max():+.1f})")
            rows.append(row)
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n2. MS-GARCH refits with a regime at a boundary (post hoc, from the frozen and reproduced "
          "walk-forwards)")
    rows = []
    for asset in ASSETS:
        frozen_path = next(FROZEN.glob(f"{asset}__ms_garch__*[0-9].csv"))
        pf = read(frozen_path.with_suffix(".params.csv"))
        pr = read(REFIT / f"{stems[asset, 'ms_garch']}__params.csv")
        bf, br = boundary(pf), boundary(pr)
        rows.append({"asset": asset, "refits": len(pf), "frozen": int(bf.sum()), "refit": int(br.sum()),
                     "both": int((bf & br).sum()),
                     "frozen, first-last": (f"{bf[bf].index.min().date()} to {bf[bf].index.max().date()}"
                                            if bf.any() else "-")})
    print(pd.DataFrame(rows).to_string(index=False))

    print("\n3. GJR-GARCH on USO, same code and data, by OpenBLAS thread count (reproduction)")
    for threads in ("1", "2", "8"):
        env = {**os.environ, "OPENBLAS_NUM_THREADS": threads}
        res = subprocess.run([sys.executable, __file__, "--garch-once"], cwd=REPO, env=env,
                             capture_output=True, text=True)
        gap, digest = res.stdout.split()
        print(f"  OPENBLAS_NUM_THREADS={threads}: max |diff| vs checkpoint {gap}, forecast hash {digest}")


if __name__ == "__main__":
    main()
