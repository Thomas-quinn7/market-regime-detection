"""examples/posthoc_stats.py: the claim rules, the equivalence reading and the committed-table parser."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import posthoc_stats as ps  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def test_equivalence_reading_uses_the_sign_of_the_interval():
    assert ps.equivalence(-0.006, 0.003, 0.3) == "gain excluded above 2.0%"
    assert ps.equivalence(-0.030, -0.006, 0.3) == "gain shown of at least 2.0%"
    assert ps.equivalence(0.003, 0.030, 0.3) == "loss shown of at least 1.0%"


def test_vix_claim_outcomes_follow_the_protocol():
    base = {k: "no difference" for k in ps.VIX_COMPARISONS}
    out = ps.vix_claim_outcomes(base)
    assert out["A. VIX improves HAR"] == "not shown"
    assert out["B. regime adds nothing once the VIX is in"] == "holds"
    assert out["C. regime models' own forecasts lose to HAR"] == "not shown"
    v = {**base, ("HAR + VIX", "HAR"): "better", ("HMM implied vol", "HAR"): "worse",
         ("VIX-HMM implied vol", "HAR"): "worse"}
    out = ps.vix_claim_outcomes(v)
    assert out["A. VIX improves HAR"] == "holds" and out["C. regime models' own forecasts lose to HAR"] == "holds"
    v[("HAR + VIX + HMM prob", "HAR + VIX")] = "better"
    assert ps.vix_claim_outcomes(v)["B. regime adds nothing once the VIX is in"] == "fails"


def test_committed_tables_parse_every_claim_row():
    cross = ps.committed_intervals(ROOT / "docs/results/cross_index_holdout_2026-10-14.txt",
                                   ["Nasdaq-100", "Dow Jones Industrial Average", "Russell 2000"])
    assert len(cross) == 27
    assert cross[("Nasdaq-100", "R2")] == ("-0.028 to -0.008", "better", "-0.037 to -0.002", "better")
    etf = ps.committed_intervals(ROOT / "docs/results/msgarch_credit_holdout_2026-10-14.txt",
                                 ["Crude oil (USO)", "Gold (GLD)", "Emerging markets (EEM)", "Brazil (EWZ)"])
    assert len(etf) == 36
    assert etf[("Crude oil (USO)", "M5")] == ("+0.038 to +0.240", "worse", "+0.034 to +0.181", "worse")
    vix = ps.committed_vix_intervals("vix_early")
    assert len(vix) == 7 and vix[("HAR + VIX", "HAR")][0] == "-0.054 to -0.012"


def test_compare_reproduces_a_registered_interval_from_the_saved_table():
    """The registered Nasdaq-100 R2 interval comes back from the saved scored table with the
    holdouts' bootstrap settings (63-day blocks, 2,000 draws, seed 0)."""
    block, df = ps.load_scored("cross_index")[0]
    assert block == "Nasdaq-100"
    r = ps.compare(df, "HAR-RV", "HAR", n_boot=2000)
    assert ps.fmt_iv(r["dRMSE lo"], r["dRMSE hi"]) == "-0.028 to -0.008"
    assert ps.fmt_iv(r["dQLIKE lo"], r["dQLIKE hi"]) == "-0.037 to -0.002"
    assert r["n"] == 3286 and r["DM MSE"]["p"] < 0.05


def test_md_table_round_trips_columns():
    df = pd.DataFrame({"a": [1, 2], "b": ["x", "y"]})
    text = ps.md_table(df)
    assert text.splitlines()[0] == "| a | b |" and text.splitlines()[-1] == "| 2 | y |"


def test_vix_features_rebuild_the_registered_forecasts_offline(monkeypatch):
    """The own-row recalibration from the saved HMM outputs equals the registered forecasts."""
    import types
    monkeypatch.setitem(sys.modules, "yfinance", types.SimpleNamespace(
        download=lambda *a, **k: (_ for _ in ()).throw(RuntimeError("network"))))
    target, feature_sets, _raw, score_from = ps.vix_features("recent")
    from regimes.forecast import walk_forward_regression
    fc = walk_forward_regression(target, feature_sets["HAR + VIX + HMM prob"], horizon=21, step=63,
                                 min_rows=756, log_target=True).forecast
    scored = ps.load_scored("vix_recent")[1][1]
    joined = fc.reindex(scored.index)
    assert np.allclose(joined.to_numpy(), scored["HAR + VIX + HMM prob"].to_numpy(), atol=1e-12)


def test_losers_kept_names_the_loser_of_each_decisive_pair():
    rows = [{"id": "A", "forecast": "f", "reference": "r",
             "dRMSE lo": 0.01, "dRMSE hi": 0.03, "dQLIKE lo": -0.02, "dQLIKE hi": -0.01},
            {"id": "B", "forecast": "g", "reference": "r",
             "dRMSE lo": -0.01, "dRMSE hi": 0.01, "dQLIKE lo": -0.01, "dQLIKE hi": 0.02}]
    in_set = {"RMSE": {"f": True, "g": True, "r": True}, "QLIKE": {"f": True, "g": True, "r": False}}
    kept = ps.losers_kept(rows, in_set)
    # B is "no difference" on both losses and is skipped
    assert [(k["id"], k["loss"], k["verdict"], k["loser"], k["loser in set"]) for k in kept] == [
        ("A", "RMSE", "worse", "f", True), ("A", "QLIKE", "better", "r", False)]
