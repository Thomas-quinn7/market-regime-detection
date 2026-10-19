"""Tests for examples/dev_benchmark_form.py (stage S9): the two forms, the 2022-12-30 cut and the h = 1 targets."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import dev_benchmark_form as bf  # noqa: E402
from regimes.forecast import har_features  # noqa: E402


def _inputs(n=1200):
    idx = pd.bdate_range("2015-01-01", periods=n)
    rng = np.random.default_rng(2)
    returns = pd.Series(rng.normal(0, 1, n), index=idx)
    vix_daily = pd.Series(1.2 + 0.1 * rng.standard_normal(n), index=idx)
    prob = pd.Series(rng.random(n), index=idx, name="high_vol_prob").where(np.arange(n) >= 40)
    noise = pd.Series(rng.standard_normal(n), index=idx)
    return returns, vix_daily, prob, noise


def test_clip_drops_every_row_after_the_cut():
    s = pd.Series(1.0, index=pd.bdate_range("2022-12-26", "2023-01-06"))
    out = bf.clip(s)
    assert out.index.max() == pd.Timestamp("2022-12-30")
    assert (out.index <= pd.Timestamp(bf.CUT)).all()


def test_log_form_is_the_log_of_the_level_form():
    returns, vix_daily, _, _ = _inputs()
    har = har_features(returns)
    lev, log = bf.har_inputs("level", har, vix_daily), bf.har_inputs("log", har, vix_daily)
    assert list(lev.columns) == list(log.columns) == ["rv_1d", "rv_5d", "rv_22d", "vix"]
    ok = lev.dropna().index
    np.testing.assert_allclose(log.loc[ok].to_numpy(), np.log(lev.loc[ok].clip(lower=1e-3)).to_numpy())


def test_prob_and_noise_enter_linearly_and_all_sets_share_rows():
    returns, vix_daily, prob, noise = _inputs()
    sets = bf.feature_sets(har_features(returns), vix_daily, prob, noise)
    assert len(sets) == 8
    rows = {tuple(v.index) for v in sets.values()}
    assert len(rows) == 1
    for form in bf.FORMS:
        X = sets[(form, "HAR + VIX + HMM prob")]
        np.testing.assert_array_equal(X["high_vol_prob"].to_numpy(), prob.loc[X.index].to_numpy())
        np.testing.assert_array_equal(sets[(form, "HAR + VIX + noise")]["noise"].to_numpy(), noise.loc[X.index].to_numpy())
    assert next(iter(rows))[0] >= prob.dropna().index[0]


def test_h1_targets_are_the_next_day():
    returns, _, _, _ = _inputs(50)
    np.testing.assert_array_equal(bf.return_target(returns, 1).to_numpy()[:-1], returns.abs().to_numpy()[1:])
    rv = returns.abs() + 0.1
    np.testing.assert_allclose(bf.es_forward(rv, 1).to_numpy()[:-1], rv.to_numpy()[1:])
    assert bf.return_target(returns, 1).iloc[-1] != bf.return_target(returns, 1).iloc[-1]   # NaN at the end
    np.testing.assert_allclose(bf.es_forward(rv, 2).iloc[0], np.sqrt((rv.iloc[1] ** 2 + rv.iloc[2] ** 2) / 2))


def test_scored_table_is_deterministic_and_drops_zero_targets():
    returns, vix_daily, prob, noise = _inputs()
    target = bf.return_target(returns, 1)
    target.iloc[1000] = 0.0
    har = har_features(returns)
    a = bf.scored_table(target, har, vix_daily, prob, noise, 1)
    b = bf.scored_table(target, har, vix_daily, prob, noise, 1)
    pd.testing.assert_frame_equal(a, b)
    assert target.index[1000] not in a.index
    assert a.shape[1] == 9 and (a.drop(columns="target") > 0).all().all()


def test_form_flips_pairs_level_with_log():
    rows = []
    for form, rmse in (("level", "no difference"), ("log", "better")):
        rows.append({"_target": "A", "h": 5, "_cross": False, "RMSE": rmse, "QLIKE": "no difference",
                     "_pair": ((form, "HAR + VIX + HMM prob"), (form, "HAR + VIX"))})
    rows.append({"_target": "A", "h": 5, "_cross": True, "RMSE": "better", "QLIKE": "better",
                 "_pair": (("log", "HAR + VIX"), ("level", "HAR + VIX"))})
    out = bf.form_flips(rows)
    assert len(out) == 1
    assert out[0]["moves"] == "yes" and out[0]["RMSE level"] == "no difference" and out[0]["RMSE log"] == "better"


def test_claims_table_reads_the_log_form_rmse_verdict():
    rows = []
    for tgt in ("A", "B"):
        for form in bf.FORMS:
            for model, ref in (("HAR + VIX + HMM prob", "HAR + VIX"), ("HAR + VIX", "HAR")):
                rmse = "better" if (form == "log" and model == "HAR + VIX") else "no difference"
                rows.append({"_target": tgt, "h": 21, "_cross": False, "RMSE": rmse, "QLIKE": "no difference",
                             "_pair": ((form, model), (form, ref))})
    out = bf.claims_table(rows)
    assert len(out) == len(bf.CLAIMS)
    assert all(r["form used"] == "log" for r in out)
    assert [r["log form points the same way"] for r in out].count("not checked") == 3
    assert all(r["log form points the same way"] in ("yes", "not checked") for r in out)


def test_answer_counts_moves_and_names_hmm_rows():
    flips = [{"target": "B", "h": 1, "comparison": "HAR + VIX + HMM prob vs HAR + VIX", "RMSE level": "no difference",
              "RMSE log": "better", "QLIKE level": "no difference", "QLIKE log": "better", "moves": "yes"},
             {"target": "A", "h": 21, "comparison": "HAR + VIX vs HAR", "RMSE level": "better", "RMSE log": "better",
              "QLIKE level": "no difference", "QLIKE log": "no difference", "moves": "no"}]
    rows = [{"_cross": True, "_pair": (("log", "HAR + VIX"), ("level", "HAR + VIX")), "RMSE": "better", "QLIKE": "no difference"}]
    text = bf.answer(rows, flips)
    assert "1 of 2" in text and "(A, h = 21): 0" in text
    assert "target B h=1 HAR + VIX + HMM prob" in text
    assert "in 1 of 1 target-horizon cells, the level form in 0" in text
