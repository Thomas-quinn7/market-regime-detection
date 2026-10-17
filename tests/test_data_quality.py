"""Tests for examples/data_quality.py: window counting helpers, the exclusion re-score, and the Dow OLS
replica against the saved reproduction (the replica must equal the frozen script's forecasts before any
what-if on it means anything)."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "examples"))

import data_quality as dq  # noqa: E402


def _calendar(n: int) -> pd.DatetimeIndex:
    return pd.bdate_range("2015-01-01", periods=n)


def test_short_targets_counts_gaps_inside_the_window_only():
    cal = _calendar(120)
    rv = pd.Series(1.0, index=cal)
    rv.iloc[60] = np.nan                      # one no-bar day
    scored = cal[:80]
    counts = dq.short_targets(rv, scored)
    # the 21 scored days whose forward window (t, t + 21] contains position 60 see 20 sessions
    short = counts[counts < 21]
    assert len(short) == 21
    assert set(short.round().astype(int)) == {20}
    assert short.index.min() == cal[39] and short.index.max() == cal[59]
    # everything else is a full 21-session window; nothing at the start is shortened
    assert (counts.drop(short.index) == 21).all()


def test_windows_containing_marks_the_21_days_before_a_flagged_day():
    cal = _calendar(100)
    hit = dq.windows_containing(cal[[50]], cal)
    assert len(hit) == 21
    assert hit.min() == cal[29] and hit.max() == cal[49]
    two = dq.windows_containing(cal[[50, 52]], cal)
    assert len(two) == 23


def _synthetic_scored(n: int = 300, seed: int = 1) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    cal = _calendar(n)
    y = np.exp(rng.normal(0, 0.3, n))
    df = pd.DataFrame({"target": y}, index=cal)
    for _, f, r, _ in dq.CROSS_CLAIMS:
        for col in (f, r):
            if col not in df:
                df[col] = y * np.exp(rng.normal(0, 0.2, n))
    return df


def test_claim_rows_is_deterministic_and_exclusion_of_nothing_moves_nothing():
    df = _synthetic_scored()
    a = dq.claim_rows(df, n_boot=50)
    b = dq.claim_rows(df, n_boot=50)
    assert [(r["lo"], r["hi"]) for r in a] == [(r["lo"], r["hi"]) for r in b]
    registered = {("blk", r["claim"]): (f"{r['lo']:+.3f} to {r['hi']:+.3f}", r["verdict"], "", "") for r in a}
    table, changed, note = dq.exclusion_table("blk", df, df.index, registered, 50, "same rows")
    assert changed == 0
    assert "0 removed" in note[0]
    assert table.count("| yes |") == 0


def test_exclusion_table_reports_removed_rows():
    df = _synthetic_scored()
    a = dq.claim_rows(df, n_boot=50)
    registered = {("blk", r["claim"]): ("x", r["verdict"], "", "") for r in a}
    keep = df.index[:-30]
    _, _, note = dq.exclusion_table("blk", df, keep, registered, 50, "fewer rows")
    assert "rows kept 270 of 300 (30 removed)" in note[0]


@pytest.mark.skipif(not (dq.REPRO / "cross_index" / "scored" / "index.json").exists(), reason="reproduction not present")
def test_dow_ols_replica_matches_the_saved_reproduction():
    dq.block_network()
    dow = "Dow Jones Industrial Average"
    scored = dict(dq.load_scored("cross_index"))[dow]
    rv, ret, iv = dq.rv_cache(dow), dq.index_returns(dow), dq.index_iv(dow)
    common = dq.common_rows(dow, ret, rv, iv)
    base = dq.dow_ols_forecasts(ret, rv, iv, common)
    for m in ["HAR", "HAR-RV", "HAR-RV + IV", "HARQ + IV", "SHAR + IV"]:
        assert float((base[m].reindex(scored.index) - scored[m]).abs().max()) < 1e-9, m
    assert float((base["target"].reindex(scored.index) - scored["target"]).abs().max()) < 1e-9
