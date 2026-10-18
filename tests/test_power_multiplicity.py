"""Tests for the helpers of examples/power_multiplicity.py (stage S7 a, b)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import power_multiplicity as pm  # noqa: E402


def test_interval_p_normal_reads_a_95_interval():
    assert pm.interval_p_normal(-0.1, 0.1) == pytest.approx(1.0)
    assert pm.interval_p_normal(0.0, 0.2) == pytest.approx(0.05, abs=1e-4)
    assert pm.interval_p_normal(-0.2, 0.0) == pytest.approx(0.05, abs=1e-4)
    assert pm.interval_p_normal(0.1, 0.3) < 0.01


def test_half_width_pct():
    assert pm.half_width_pct(-0.01, 0.03, 0.4) == pytest.approx(5.0)


def _row(holdout, family, claim, expected, lo, hi, keep):
    return {"holdout": holdout, "family": family, "claim": claim, "expected": expected, "forecast": claim,
            "reference": "ref", "r_lo": lo, "r_hi": hi, "keep": keep}


def test_outcomes_after_reads_dropped_verdicts_as_no_difference():
    rows = [_row("X", "cross-index per-index verdicts", "P1", "better", -0.3, -0.1, True),
            _row("X", "cross-index per-index verdicts", "P1", "better", -0.3, -0.1, False),
            _row("X", "cross-index per-index verdicts", "P1", "better", -0.1, 0.1, True),
            _row("X", "cross-index per-index verdicts", "R3", "not better", -0.3, -0.1, False)]
    reg = pm.outcomes_after(rows, lambda r: pm.ph.verdict(r["r_lo"], r["r_hi"]))
    assert reg == {("X", "P1"): "confirmed", ("X", "R3"): "fails"}
    after = pm.outcomes_after(rows, lambda r: pm.ph.verdict(r["r_lo"], r["r_hi"]) if r["keep"] else "no difference")
    # a correction can turn "confirmed" into "mixed" and a failing "not better" into "holds", never the reverse
    assert after == {("X", "P1"): "mixed", ("X", "R3"): "holds"}


def test_claim_sentences_one_per_claim_with_the_range():
    rows = [dict(_row("H", "f", "P1", "better", -0.02, 0.02, True), n=1000, **{"ref RMSE": 0.4, "q_lo": np.nan,
                                                                                   "q_hi": np.nan, "ref QLIKE": np.nan}),
            dict(_row("H", "f", "P1", "better", -0.04, 0.04, True), n=2000, **{"ref RMSE": 0.4, "q_lo": np.nan,
                                                                                   "q_hi": np.nan, "ref QLIKE": np.nan})]
    lines = pm.claim_sentences(rows)
    assert len(lines) == 1
    assert "1,000 to 2,000 scored days" in lines[0] and "5.0% to 10.0%" in lines[0]
