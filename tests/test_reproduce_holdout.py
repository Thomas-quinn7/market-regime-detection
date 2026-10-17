"""The reproduction wrapper records without changing anything, and blocks the network."""
from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

import reproduce_holdout as rh  # noqa: E402

import regimes.forecast as forecast_mod  # noqa: E402
import regimes.garch as garch_mod  # noqa: E402


def _undo(undo):
    for owner, attr, original in reversed(undo):
        setattr(owner, attr, original)


@pytest.fixture
def recorder(tmp_path):
    for sub in ("forecasts", "walk_forwards", "scored"):
        (tmp_path / sub).mkdir()
    return rh.Recorder(tmp_path)


def _series(n=900, seed=0):
    rng = np.random.default_rng(seed)
    idx = pd.bdate_range("2000-01-03", periods=n)
    return pd.Series(rng.standard_normal(n), index=idx)


def test_regression_forecast_unchanged_and_saved(recorder, tmp_path):
    y = _series().abs() + 0.5
    X = pd.DataFrame({"a": _series(seed=1), "b": _series(seed=2)})
    original = forecast_mod.walk_forward_regression
    expected = original(y, X, horizon=5, step=21, min_rows=252).forecast
    undo = rh.install_patches(recorder)
    try:
        got = forecast_mod.walk_forward_regression(y, X, horizon=5, step=21, min_rows=252).forecast
    finally:
        _undo(undo)
    assert forecast_mod.walk_forward_regression is original
    pd.testing.assert_series_equal(got, expected)
    saved = pd.read_csv(tmp_path / "forecasts" / "regression_001.csv", index_col=0, parse_dates=True,
                        float_precision="round_trip")
    np.testing.assert_array_equal(saved["forecast"].to_numpy(), expected.to_numpy())
    assert recorder.regression_index[0]["features"] == ["a", "b"]


def test_convergence_recorded_for_arch(recorder):
    r = _series(n=900, seed=3)
    undo = rh.install_patches(recorder)
    try:
        wf = garch_mod.walk_forward_gjr(r, min_train=756, step=63, horizon=21)
    finally:
        _undo(undo)
    rows = [c for c in recorder.convergence if c["optimiser"] == "arch"]
    assert len(rows) == wf.n_refits
    assert all(c["walk_forward"] == "walk_forward_gjr" for c in rows)
    counts = recorder.convergence_counts()
    assert int(counts["calls"].sum()) == wf.n_refits


def test_network_blocked_then_restored(recorder):
    original = urllib.request.urlopen
    undo = rh.install_patches(recorder)
    try:
        with pytest.raises(RuntimeError, match="network access is blocked"):
            urllib.request.urlopen("https://example.com")
    finally:
        _undo(undo)
    assert urllib.request.urlopen is original


def test_read_csv_records_file(recorder, tmp_path):
    path = tmp_path / "x.csv"
    path.write_text("a\n1\n")
    undo = rh.install_patches(recorder)
    try:
        pd.read_csv(path)
    finally:
        _undo(undo)
    (rec,) = recorder.files.values()
    assert rec["sha256"] == rh.sha256(path) and rec["bytes"] == path.stat().st_size


def test_reference_lines_strip_hand_added_header(tmp_path, monkeypatch):
    (tmp_path / "ref.txt").write_text("# provenance line\n# second\n\n##### body\nrow\n")
    monkeypatch.setitem(rh.HOLDOUTS, "fake", ("m", [], "ref.txt", None))
    assert rh.reference_lines("fake", tmp_path) == ["", "##### body", "row"]


def test_statsmodels_fit_recorded(recorder):
    from regimes.model import fit_regimes
    r = _series(n=600, seed=4)
    undo = rh.install_patches(recorder)
    try:
        fit_regimes(r, 2)
    finally:
        _undo(undo)
    assert [c["optimiser"] for c in recorder.convergence] == ["statsmodels"]
    (row,) = recorder.sm_params
    assert row["nobs"] == 600 and np.isfinite(row["llf"]) and len(row) > 5


def test_scored_table_saved_with_block(recorder, tmp_path):
    y = _series().abs() + 0.5
    fc = {"a": y * 1.1, "b": y * 0.9}
    original = forecast_mod.forecast_losses
    expected = original(fc, y)
    recorder.saw_line("##### Gold (GLD): returns ...")
    undo = rh.install_patches(recorder)
    try:
        got = forecast_mod.forecast_losses(fc, y)
    finally:
        _undo(undo)
    pd.testing.assert_frame_equal(got, expected)
    saved = pd.read_csv(tmp_path / "scored" / "scored_01.csv", index_col=0, float_precision="round_trip")
    assert list(saved.columns) == ["target", "a", "b"]
    np.testing.assert_array_equal(saved["a"].to_numpy(), fc["a"].to_numpy())
    assert recorder.scored_index[0]["block"] == "Gold (GLD)"
