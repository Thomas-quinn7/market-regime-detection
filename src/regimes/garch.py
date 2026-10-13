"""Walk-forward GJR-GARCH volatility forecasts, the standard econometric baseline.

GJR-GARCH(1,1) (Glosten, Jagannathan and Runkle 1993) lets a negative return raise tomorrow's
variance more than a positive one of the same size, which is the main asymmetry in equity
volatility. Fitted with the ``arch`` package, constant mean, Student-t errors.

The walk-forward follows the repo's protocol: fit on data up to each refit date, freeze the
parameters, and let the variance recursion run forward through the next ``step`` days, so each
forecast uses returns up to its own date only.
"""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class GarchWalkForward:
    implied_vol: pd.Series   # forecast of vol over the next ``horizon`` days, made at each date
    params: pd.DataFrame     # fitted parameters per refit
    n_refits: int


def walk_forward_gjr(returns: pd.Series, *, min_train: int = 756, step: int = 63,
                     horizon: int = 21, dist: str = "t") -> GarchWalkForward:
    """Expanding-window GJR-GARCH(1,1): forecast of sqrt(mean variance over the next ``horizon`` days)."""
    from arch import arch_model

    r = returns.astype(float)
    pieces, rows, idx = [], [], []
    for i in range(min_train, len(r), step):
        end = min(i + step, len(r))
        # Fit on rows [0, i) only, then filter forward with those parameters frozen.
        res = arch_model(r.iloc[:i], mean="Constant", vol="GARCH", p=1, o=1, q=1,
                         dist=dist).fit(disp="off")
        frozen = arch_model(r.iloc[:end], mean="Constant", vol="GARCH", p=1, o=1, q=1, dist=dist)
        fc = frozen.forecast(params=res.params, horizon=horizon, start=i, reindex=False)
        var = fc.variance.to_numpy()
        pieces.append(pd.Series(np.sqrt(var.mean(axis=1)), index=r.index[i:end]))
        rows.append(res.params.to_dict())
        idx.append(r.index[i])
    return GarchWalkForward(implied_vol=pd.concat(pieces),
                            params=pd.DataFrame(rows, index=pd.DatetimeIndex(idx)),
                            n_refits=len(pieces))
