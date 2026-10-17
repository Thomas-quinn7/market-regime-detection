"""Every walk-forward records optimiser convergence per refit, without changing its forecasts.

The forecasts' identity with the committed holdout outputs is shown by the reproduction runs
(docs/results/reproductions/REPRODUCTION_2026-10.md); here each walk-forward is checked on a small
synthetic series for the shape and content of the record and for the ``info`` hook being optional.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from regimes.correlation import convergence_counts, convergence_row, fit_corr_hmm, walk_forward_corr_regimes
from regimes.evaluate import walk_forward_oos
from regimes.garch import walk_forward_gjr
from regimes.msgarch import fit_msgarch, walk_forward_msgarch
from regimes.msm import fit_msm, simulate_msm, MSMParams, starts_row, walk_forward_msm
from regimes.vix_regimes import walk_forward_vix_hmm


def _returns(n: int = 1000, seed: int = 0) -> pd.Series:
    rng = np.random.default_rng(seed)
    vol = np.where(np.arange(n) % 300 < 150, 0.6, 1.8)
    return pd.Series(vol * rng.standard_normal(n), index=pd.bdate_range("2001-01-01", periods=n))


def test_hmm_walk_forward_records_one_flag_per_refit():
    wf = walk_forward_oos(_returns(), min_train=700, step=100, horizon=21)
    assert list(wf.convergence.columns) == ["best_converged", "detail"]
    assert len(wf.convergence) == wf.n_refits == 3
    assert wf.convergence["best_converged"].all()
    assert convergence_counts(wf.convergence) == "3 of 3 refits converged"


def test_gjr_walk_forward_records_the_arch_flag():
    wf = walk_forward_gjr(_returns(), min_train=700, step=150, horizon=5)
    assert len(wf.convergence) == wf.n_refits == 2
    assert wf.convergence["best_converged"].all() and (wf.convergence["detail"] == "0").all()


def test_msm_and_msgarch_record_starts_and_the_info_hook_is_optional():
    r = pd.Series(simulate_msm(MSMParams(m0=1.4, sigma=1.0, b=3.0, gamma_k=0.5), 3, 600, seed=1),
                  index=pd.bdate_range("2005-01-01", periods=600))
    p_plain, ll_plain = fit_msm(r, 3)
    info: dict = {}
    p_info, ll_info = fit_msm(r, 3, info=info)
    assert p_plain == p_info and ll_plain == ll_info  # the hook changes nothing
    assert len(info["starts"]) >= 2 and 0 <= info["best"] < len(info["starts"])
    row = starts_row(info)
    assert row["starts"] == len(info["starts"]) and 0 <= row["converged"] <= row["starts"]
    wf = walk_forward_msm(r, 3, min_train=400, step=100, horizon=21)
    assert list(wf.convergence.columns) == ["starts", "converged", "best_converged"]
    assert len(wf.convergence) == wf.n_refits == 2 and wf.convergence["starts"].iloc[0] > wf.convergence["starts"].iloc[1]
    assert convergence_counts(wf.convergence).startswith(f"{int(wf.convergence['best_converged'].sum())} of 2 refits converged (")
    info = {}
    p1, ll1 = fit_msgarch(r, 2, "normal")
    p2, ll2 = fit_msgarch(r, 2, "normal", info=info)
    assert ll1 == ll2 and len(info["starts"]) >= 1
    assert all(np.array_equal(np.asarray(a), np.asarray(b)) for a, b in zip(p1.as_dict().values(), p2.as_dict().values()))
    wf2 = walk_forward_msgarch(r, 2, "normal", min_train=400, step=200, horizon=21)
    assert len(wf2.convergence) == wf2.n_refits == 1 and set(wf2.convergence.columns) == {"starts", "converged", "best_converged"}


def test_em_fitters_record_iterations_and_convergence():
    rng = np.random.default_rng(2)
    z = np.column_stack([rng.standard_normal(500), rng.standard_normal(500)])
    z[250:, 1] = 0.8 * z[250:, 0] + 0.6 * z[250:, 1]
    info: dict = {}
    params, ll = fit_corr_hmm(z, 2, info=info)
    params2, ll2 = fit_corr_hmm(z, 2)
    assert ll == ll2 and np.array_equal(params.A, params2.A)
    assert info["converged"] is True and 1 < info["iterations"] <= 200
    assert convergence_row([info], 0) == {"starts": 1, "converged": 1, "best_converged": True,
                                          "iterations": info["iterations"]}
    tight: dict = {}
    fit_corr_hmm(z, 2, max_iter=2, info=tight)
    assert tight == {"iterations": 2, "converged": False}
    frame = pd.DataFrame(z, index=pd.bdate_range("2010-01-01", periods=500), columns=["a", "b"])
    wf = walk_forward_corr_regimes(frame, min_train=300, step=100, horizon=21)
    assert len(wf.convergence) == wf.n_refits and wf.convergence["starts"].iloc[-1] == 2
    assert "iterations" in wf.convergence.columns
    r = _returns(800)
    vix = (10 + 5 * r.abs().rolling(20).mean()).bfill()
    wv = walk_forward_vix_hmm(r, vix, min_train=500, step=150, horizon=21)
    assert len(wv.convergence) == wv.n_refits and set(wv.convergence.columns) >= {"starts", "converged", "best_converged"}
    assert convergence_counts(None) == "no convergence record"
