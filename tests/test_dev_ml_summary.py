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


def test_reading_counts_and_missing_parts():
    t1 = _table()
    t2 = pd.DataFrame({"h": [126, 63], "learner": ["lightgbm", "mlp"], "RMSE": ["worse", "no difference"], "QLIKE": ["no difference"] * 2})
    t3 = pd.DataFrame({"h": [5], "RMSE": ["better"], "QLIKE": ["worse"]})
    race_t = pd.DataFrame({"forecast": ["lstm F0", "gru F1", "ridge F0"], "RMSE": ["better", "worse", "better"],
                           "QLIKE": ["no difference"] * 3})
    det_t = pd.DataFrame({"set": ["F0", "F1", "F1n", "F1[kmeans 2]"], "RMSE": ["x", "better", "better", "worse"],
                          "QLIKE": ["x", "no difference", "no difference", "no difference"]})
    text = "\n".join(s.reading(t1, t2, t3, race_t, det_t))
    assert "'better' than the same learner without it in 3 of 6 comparisons" in text
    assert "The protocol reading (F1 better while F1n is not) holds in 2 of 6" in text
    assert "'better' in 0 of 4 comparisons, 'worse' in 1" in text
    assert "lightgbm at h = 126 (RMSE) on F0 against HAR + VIX is 'worse'" in text
    assert "mlp at h = 63 (QLIKE) on F0 against HAR + VIX is 'no difference'" in text
    assert "'better' than HAR + VIX in 1 of 4 comparisons and 'worse' in 1" in text  # ridge row not counted
    assert "'better' than F0 in 0 of 2 comparisons, 'worse' in 1" in text  # F0, F1, F1n not counted
    missing = "\n".join(s.reading(t1, t2, t3, None, None))
    assert "The race (c): not scored" in missing and "The detectors (d): not scored" in missing
    assert "'better' at h = 5 (table (iii))" in text
    assert "claim B needs the closer look" in text  # mlp finding is not in a worse learner
    assert text.isascii()


def test_reading_counts_schedule_moves(monkeypatch, tmp_path):
    monkeypatch.setattr(s.drd, "CACHE", tmp_path)  # keep the real schedule_check.csv out of the synthetic count
    t1 = _table()
    t2 = pd.DataFrame({"h": [126, 63], "learner": ["lightgbm", "mlp"], "RMSE": ["worse"] * 2, "QLIKE": ["worse"] * 2})
    t3 = pd.DataFrame({"h": [5], "RMSE": ["no difference"], "QLIKE": ["no difference"]})
    det_t = pd.DataFrame({"h": [21, 21, 63], "model": ["ridge", "ridge", "mlp"], "set": ["F1", "F1n", "F1"],
                          "dRMSE 95%": ["e"] * 3, "RMSE": ["no difference", "worse", "better"],
                          "dQLIKE 95%": ["f"] * 3, "QLIKE": ["no difference", "better", "better"]})
    text = "\n".join(s.reading(t1, t2, t3, None, det_t))
    assert ("move 1 of 3 verdicts against S8 (b); F1n vs F0 (noise control), ridge at h = 21 "
            "(RMSE no difference -> worse)." in text)  # QLIKE is 'better' on both schedules, so it does not move
    assert "HMM rows that move: 0 of 2; noise rows that read 'better' on either schedule: 1 of 1." in text


def test_coverage_groups_learners_by_horizons():
    df = pd.DataFrame({"h": [5, 21, 126, 5, 21, 126, 5, 21], "learner": ["ols"] * 3 + ["lasso"] * 3 + ["mlp"] * 2})
    assert s.coverage(df) == "lasso and ols at h = 5, 21, 126; mlp at h = 5, 21"
    text = "\n".join(s.reading(_table(), pd.DataFrame({"h": [], "learner": [], "RMSE": [], "QLIKE": []}),
                               pd.DataFrame({"h": [], "RMSE": [], "QLIKE": []}), None, None))
    assert "(3 learner-horizon pairs, each on both losses: ridge at h = 21; mlp at h = 63; lightgbm at h = 126)" in text
