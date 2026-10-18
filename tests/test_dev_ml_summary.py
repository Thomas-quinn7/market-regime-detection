"""Tests for examples/dev_ml_summary.py (stage S8 e): the protocol's reading of table (i) and the counts."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import dev_ml_summary as s  # noqa: E402


def _table():
    rows = []
    for h, lr, f1r, f1q, nr, nq in [(21, "ridge", "no difference", "no difference", "no difference", "better"),
                                    (126, "lightgbm", "better", "no difference", "no difference", "better"),
                                    (63, "mlp", "better", "better", "better", "no difference")]:
        rows.append({"h": h, "learner": lr, "comparison": "F1 vs F0", "RMSE": f1r, "QLIKE": f1q,
                     "dRMSE 95%": "a", "dQLIKE 95%": "b"})
        rows.append({"h": h, "learner": lr, "comparison": "F1n vs F0 (noise control)", "RMSE": nr, "QLIKE": nq,
                     "dRMSE 95%": "c", "dQLIKE 95%": "d"})
    return pd.DataFrame(rows)


def test_findings_need_f1_better_and_the_noise_row_not_better():
    f = s.findings(_table())
    assert list(zip(f["h"], f["learner"], f["loss"])) == [(126, "lightgbm", "RMSE"), (63, "mlp", "QLIKE")]
    assert f.iloc[0]["F1n vs F0"] == "c"


def test_verdict_counts():
    c = s.verdict_counts(_table(), "comparison").set_index("comparison")
    assert c.loc["F1 vs F0", "comparisons"] == 3
    assert c.loc["F1 vs F0", "RMSE better / no diff. / worse"] == "2 / 1 / 0"
    assert c.loc["F1n vs F0 (noise control)", "QLIKE better / no diff. / worse"] == "2 / 1 / 0"
