"""State-count selection should prefer a parsimonious count on genuinely 2-regime data."""
import numpy as np
import pandas as pd

from regimes.selection import select_n_regimes


def _two_regime(seed: int = 5) -> pd.Series:
    rng = np.random.default_rng(seed)
    y = np.concatenate([rng.normal(0.0, 0.5, 500), rng.normal(0.0, 3.0, 500)])
    return pd.Series(y, index=pd.date_range("2010-01-01", periods=len(y), freq="B"))


def test_table_has_all_candidates_and_two_regime_converges():
    res = select_n_regimes(_two_regime(), candidates=(2, 3, 4))
    assert list(res.table.index) == [2, 3, 4]
    # The correct 2-regime model must converge; over-specified counts may not (see next test).
    assert bool(res.table.loc[2, "converged"])


def test_parsimony_wins_on_two_regime_data():
    res = select_n_regimes(_two_regime(), candidates=(2, 3, 4))
    # On a genuine 2-regime process, extra states either lose on BIC or fail to converge outright
    # (statsmodels cannot identify a state that is not there). Either way the selection lands on 2.
    assert res.best_bic == 2
    assert res.best_aic == 2
