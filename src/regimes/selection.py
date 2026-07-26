"""Choosing the number of regimes, honestly.

Two states is a defensible default, but "how many regimes?" should be answered by evidence, not
taste. This module fits the switching-variance model for a range of state counts and reports the
information criteria (AIC, BIC) and log-likelihood for each, plus the BIC-preferred count.

BIC is the primary criterion here: it penalises extra parameters more firmly than AIC, which matters
because each added regime brings a full row of transition probabilities plus its own mean and
variance, and it is easy to "improve" the likelihood by over-fitting noise into a rarely-visited
state.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import pandas as pd


@dataclass
class RegimeCount:
    """Fit quality for one candidate state count."""

    n_regimes: int
    aic: float
    bic: float
    llf: float
    converged: bool


@dataclass
class SelectionResult:
    """State-count comparison across candidates."""

    table: pd.DataFrame  # indexed by n_regimes, columns aic/bic/llf/converged
    best_bic: int
    best_aic: int

    def summary(self) -> str:
        lines = [f"BIC prefers {self.best_bic} regimes; AIC prefers {self.best_aic}.", "", str(self.table)]
        return "\n".join(lines)


def select_n_regimes(returns: pd.Series, candidates=(2, 3, 4)) -> SelectionResult:
    """Fit the model for each candidate state count and rank by information criterion.

    A candidate whose fit fails to converge is recorded (``converged=False``) rather than dropped, so
    the comparison never silently hides an unstable model. Non-converged fits are excluded from the
    "best" selection.
    """
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    y = returns.astype(float).reset_index(drop=True)
    rows = []
    for k in candidates:
        try:
            with warnings.catch_warnings():
                # A non-converging over-specified count is expected and recorded below via the
                # ``converged`` flag; the warning would just be noise on top of that signal.
                warnings.simplefilter("ignore")
                res = MarkovRegression(y, k_regimes=k, trend="c", switching_variance=True).fit(disp=False)
            rows.append(RegimeCount(k, float(res.aic), float(res.bic), float(res.llf),
                                    bool(res.mle_retvals.get("converged", True))))
        except Exception:
            rows.append(RegimeCount(k, float("nan"), float("nan"), float("nan"), False))

    table = pd.DataFrame(
        {"aic": [r.aic for r in rows], "bic": [r.bic for r in rows],
         "llf": [r.llf for r in rows], "converged": [r.converged for r in rows]},
        index=pd.Index([r.n_regimes for r in rows], name="n_regimes"),
    )
    ok = table[table["converged"]]
    if ok.empty:
        raise RuntimeError("no candidate state count converged")

    return SelectionResult(table=table, best_bic=int(ok["bic"].idxmin()), best_aic=int(ok["aic"].idxmin()))
