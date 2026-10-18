"""Flexible learners for the S8 development continuation (October 2026 reopen). Not used by any holdout.

development data only (S&P 500, 2005-2023), no holdout, not a claim.

The learners, grids and walk-forward are fixed by ``docs/ML_REGIME_PROTOCOL_DRAFT.md``; this module is
the code that protocol names, and it is imported by no frozen script.

- ``GRIDS``: the hyperparameter grid of every learner, in the protocol's order (ties go to the first).
- ``make``: one estimator for a learner and a grid point, with fixed seeds and thread counts.
- ``choose``: rolling-origin validation inside a training window (the last ``val`` rows, embargoed by
  the horizon from the rows the candidates are fitted on).
- ``walk_forward_learner``: the paper's walk-forward (first refit after ``min_rows`` rows, refit every
  ``step`` rows, training rows embargoed by ``horizon``), with the learner chosen and refitted at every
  refit, on the log target, returned in levels with the lognormal correction ``exp(pred + s^2 / 2)``,
  ``s^2`` the validation-block residual variance of the chosen grid point.
"""
from __future__ import annotations

import itertools
import warnings
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

SEED = 0
THREADS = 4
_FLOOR = 1e-6

GRIDS: dict[str, list[dict]] = {
    "ridge": [{"alpha": a} for a in (0.01, 0.1, 1.0, 10.0, 100.0)],
    "lasso": [{"alpha": a} for a in (0.0001, 0.001, 0.01, 0.1)],
    "random forest": [{"max_depth": d, "min_samples_leaf": m} for d, m in itertools.product((4, 8), (25, 100))],
    "lightgbm": [{"num_leaves": nl, "n_estimators": ne, "min_child_samples": mc}
                 for nl, ne, mc in itertools.product((7, 15), (100, 300), (25, 100))],
    "mlp": [{"alpha": a} for a in (0.0001, 0.01)],
}
LEARNERS = tuple(GRIDS)


class _Standardised:
    """Fit a scaler on the training rows only, then the model on the scaled rows."""

    def __init__(self, model):
        self.model = model

    def fit(self, X, y):
        self.mu = X.mean(axis=0)
        self.sd = X.std(axis=0)
        self.sd[self.sd == 0] = 1.0
        self.model.fit((X - self.mu) / self.sd, y)
        return self

    def predict(self, X):
        return self.model.predict((X - self.mu) / self.sd)


class _SerialPredict:
    """Fit with ``THREADS`` threads, predict with one: sklearn's threaded forest prediction adds the
    trees' outputs in whatever order the threads finish, which moves the last bit from run to run."""

    def __init__(self, model):
        self.model = model

    def fit(self, X, y):
        self.model.fit(X, y)
        self.model.set_params(n_jobs=1)
        return self

    def predict(self, X):
        return self.model.predict(X)


class _EarlyStoppedMLP:
    """sklearn's MLP trained epoch by epoch; with a validation block, the epoch count with the lowest
    validation error (patience ``patience``) is kept; without one, ``epochs`` epochs are run."""

    def __init__(self, alpha: float, *, epochs: int | None = None, max_epochs: int = 300, patience: int = 20):
        self.alpha, self.epochs, self.max_epochs, self.patience = alpha, epochs, max_epochs, patience

    def _new(self):
        from sklearn.neural_network import MLPRegressor
        return MLPRegressor(hidden_layer_sizes=(32, 16), activation="relu", solver="adam", alpha=self.alpha,
                            learning_rate_init=0.001, batch_size=64, random_state=SEED, shuffle=True)

    def fit(self, X, y, X_val=None, y_val=None):
        self.mu, self.sd = X.mean(axis=0), X.std(axis=0)
        self.sd[self.sd == 0] = 1.0
        Xs = (X - self.mu) / self.sd
        net = self._new()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            if X_val is None:
                for _ in range(self.epochs or self.max_epochs):
                    net.partial_fit(Xs, y)
                self.net = net
                return self
            Xv = (X_val - self.mu) / self.sd
            best, best_epoch, since = np.inf, 0, 0
            for epoch in range(1, self.max_epochs + 1):
                net.partial_fit(Xs, y)
                err = float(np.mean((net.predict(Xv) - y_val) ** 2))
                if err < best - 1e-12:
                    best, best_epoch, since = err, epoch, 0
                else:
                    since += 1
                    if since >= self.patience:
                        break
            self.best_epoch = best_epoch
        # refit from scratch to the best epoch so the returned net is the one validated
        self.epochs = best_epoch
        return self.fit(X, y)

    def predict(self, X):
        return self.net.predict((X - self.mu) / self.sd)


def make(learner: str, params: dict, *, epochs: int | None = None):
    """One unfitted estimator. Seeds and thread counts are fixed here and nowhere else."""
    if learner == "ridge":
        from sklearn.linear_model import Ridge
        return _Standardised(Ridge(alpha=params["alpha"]))
    if learner == "lasso":
        from sklearn.linear_model import Lasso
        return _Standardised(Lasso(alpha=params["alpha"], max_iter=10000))
    if learner == "random forest":
        from sklearn.ensemble import RandomForestRegressor
        return _SerialPredict(RandomForestRegressor(n_estimators=300, bootstrap=True, random_state=SEED,
                                                    n_jobs=THREADS, **params))
    if learner == "lightgbm":
        import lightgbm as lgb
        return lgb.LGBMRegressor(learning_rate=0.05, subsample=1.0, colsample_bytree=1.0, deterministic=True,
                                 force_row_wise=True, num_threads=THREADS, random_state=SEED, verbose=-1, **params)
    if learner == "mlp":
        return _EarlyStoppedMLP(params["alpha"], epochs=epochs)
    raise ValueError(f"unknown learner {learner!r}")


def choose(learner: str, X: np.ndarray, y: np.ndarray, *, horizon: int, val: int = 252) -> dict:
    """Pick a grid point by validation on the last ``val`` rows of a training window.

    Candidates are fitted on rows ``[: n - val - horizon]`` (so no candidate's training target overlaps
    the validation block) and scored by mean squared error on rows ``[n - val :]``. Returns the chosen
    ``params``, its validation residual variance ``s2`` and, for the MLP, its ``epochs``.
    """
    n = len(y)
    fit_rows, val_rows = slice(0, n - val - horizon), slice(n - val, n)
    best = None
    for params in GRIDS[learner]:
        if learner == "mlp":
            m = make(learner, params).fit(X[fit_rows], y[fit_rows], X[val_rows], y[val_rows])
        else:
            m = make(learner, params).fit(X[fit_rows], y[fit_rows])
        resid = y[val_rows] - m.predict(X[val_rows])
        err = float(np.mean(resid ** 2))
        if best is None or err < best["err"]:
            best = {"params": params, "err": err, "s2": float(np.var(resid)),
                    "epochs": getattr(m, "epochs", None)}
    return best


@dataclass
class LearnerForecast:
    forecast: pd.Series                 # out-of-sample forecasts, levels
    chosen: pd.DataFrame = field(repr=False)   # per refit: date, chosen params, validation error, s2
    n_refits: int = 0


def walk_forward_learner(target: pd.Series, features: pd.DataFrame | pd.Series, learner: str, *,
                         horizon: int = 21, step: int = 63, min_rows: int = 756, val: int = 252) -> LearnerForecast:
    """The walk-forward of ``regimes.forecast.walk_forward_regression`` with a learner in place of OLS.

    Rows are the dates where every feature is present. At refit position ``i`` the training rows are
    ``[: i - horizon]`` with a known target; a grid point is chosen on their last ``val`` rows
    (``choose``), refitted on all of them, and used for rows ``[i : i + step]``. Log target; forecasts are
    ``exp(pred + s2 / 2)``.
    """
    X_all = features.to_frame() if isinstance(features, pd.Series) else features
    X_all = X_all.dropna()
    y = np.log(target.reindex(X_all.index).to_numpy(dtype=float))
    X = X_all.to_numpy(dtype=float)
    n = len(X_all)
    pieces, chosen = [], []
    for i in range(min_rows + horizon, n, step):
        end = min(i + step, n)
        tr = np.arange(0, i - horizon)
        tr = tr[~np.isnan(y[tr])]
        best = choose(learner, X[tr], y[tr], horizon=horizon, val=val)
        model = make(learner, best["params"], epochs=best["epochs"]).fit(X[tr], y[tr])
        pred = np.exp(model.predict(X[i:end]) + 0.5 * best["s2"])
        pieces.append(pd.Series(np.maximum(pred, _FLOOR), index=X_all.index[i:end]))
        chosen.append({"date": X_all.index[i], **best["params"], "val_mse": best["err"], "s2": best["s2"],
                       "epochs": best["epochs"]})
    if not pieces:
        raise ValueError(f"not enough rows ({n}) for min_rows={min_rows} and horizon={horizon}")
    return LearnerForecast(forecast=pd.concat(pieces), chosen=pd.DataFrame(chosen), n_refits=len(pieces))
