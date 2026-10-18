"""examples/vix_source_check.py: the two-source comparison on hand-built series."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))
from vix_source_check import compare_sources, load_fred  # noqa: E402


def test_compare_sources_counts_differences_and_missing_days():
    idx = pd.bdate_range("2020-01-01", periods=10)
    yahoo = pd.Series(range(10), index=idx, dtype=float)
    fred = yahoo.copy()
    fred.iloc[3] += 0.98          # one revised print
    fred.iloc[5] += 0.001         # below the tolerance
    fred = fred.drop(idx[7])      # a day FRED lacks
    fred.loc[pd.Timestamp("2020-01-20")] = 50.0   # a FRED-only day inside the span (a Monday)
    fred = fred.sort_index()
    yahoo = pd.concat([yahoo, pd.Series([1.0], index=[pd.Timestamp("2021-01-04")])])  # outside FRED's span
    r = compare_sources(yahoo, fred)
    assert r["common_days"] == 9
    assert r["days_differing"] == 1 and r["differing"] == {str(idx[3].date()): 0.98}
    assert r["max_abs_diff"] == 0.98 and r["max_abs_date"] == str(idx[3].date())
    assert r["fred_only"] == ["2020-01-20"]
    assert r["yahoo_only"] == [str(idx[7].date())]   # the 2021 row is outside the overlap and not counted


def test_load_fred_drops_dot_holidays(tmp_path):
    p = tmp_path / "fred.csv"
    p.write_text("observation_date,VIXCLS\n2020-01-01,.\n2020-01-02,13.5\n2024-01-02,14.0\n")
    s = load_fred(p, end="2023-12-31")
    assert list(s.index) == [pd.Timestamp("2020-01-02")] and s.iloc[0] == 13.5
