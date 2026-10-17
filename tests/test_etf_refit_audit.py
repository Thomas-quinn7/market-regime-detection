"""The boundary flag in the ETF refit audit marks a collapsed or never-staying MS-GARCH regime."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "examples"))

from etf_refit_audit import boundary  # noqa: E402


def test_boundary():
    base = {"omega0": 0.02, "beta0": 0.95, "p00": 0.99, "omega1": 0.2, "beta1": 0.9, "p11": 0.98}
    p = pd.DataFrame([base, {**base, "omega0": 0.0, "beta0": 0.0}, {**base, "p11": 0.0011},
                      {**base, "omega1": 0.0}])
    assert boundary(p).tolist() == [False, True, True, False]
