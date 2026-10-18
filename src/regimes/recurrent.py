"""Recurrent learners (LSTM, GRU) for the S8 (c) race (October 2026 reopen). Not used by any holdout.

development data only (S&P 500, 2005-2023), no holdout, not a claim.

The design is fixed by amendment A1 of ``docs/ML_REGIME_PROTOCOL_DRAFT.md`` (written and committed before
any fit): one recurrent layer and a linear output on the last step; input = the last ``SEQ`` days of the
feature set, standardised on the training rows; output = the log target. Adam (learning rate 0.001), batch
64, at most 200 epochs, early stopping with patience 20 on the last ``val`` training rows (embargoed by the
horizon from the rows the candidates are fitted on); the best epoch's count is reused for the refit on the
whole window. Grid: hidden size {8, 16} x weight decay {0, 0.0001}. Seeds: ``torch.manual_seed(0)`` before
every network is built and a seeded generator for the batch order; deterministic algorithms; 4 threads.

The walk-forward is the one of ``regimes.learners.walk_forward_learner`` (and of the paper): first refit
after ``min_rows`` rows, refit every ``step`` rows, training rows ``[: i - horizon]`` with a known target,
forecasts ``exp(pred + s2 / 2)`` with ``s2`` the validation residual variance of the chosen grid point.
This module is imported by no frozen script.
"""
from __future__ import annotations

import copy
import itertools

import numpy as np
import pandas as pd

from regimes.learners import LearnerForecast

SEED = 0
THREADS = 4
SEQ = 66
BATCH = 64
MAX_EPOCHS = 200
PATIENCE = 20
LR = 0.001
_FLOOR = 1e-6

GRID: list[dict] = [{"hidden": h, "weight_decay": w} for h, w in itertools.product((8, 16), (0.0, 0.0001))]
RECURRENT = ("lstm", "gru")


def _torch():
    import torch
    torch.set_num_threads(THREADS)
    torch.use_deterministic_algorithms(True)
    return torch


def windows(X: np.ndarray, rows: np.ndarray, seq: int = SEQ) -> np.ndarray:
    """The input sequence for each row ``j`` in ``rows``: ``X[j - seq + 1 : j + 1]`` (rows ``j >= seq - 1``)."""
    if len(rows) and rows.min() < seq - 1:
        raise ValueError("a row has fewer than seq - 1 earlier rows")
    idx = rows[:, None] + np.arange(-seq + 1, 1)[None, :]
    return X[idx]


def _net(kind: str, n_in: int, hidden: int):
    torch = _torch()
    nn = torch.nn
    torch.manual_seed(SEED)

    class Net(nn.Module):
        def __init__(self):
            super().__init__()
            rnn = nn.LSTM if kind == "lstm" else nn.GRU
            self.rnn = rnn(n_in, hidden, batch_first=True)
            self.out = nn.Linear(hidden, 1)

        def forward(self, x):
            h, _ = self.rnn(x)
            return self.out(h[:, -1, :]).squeeze(-1)

    return Net()


class RecurrentModel:
    """One grid point. ``fit`` with a validation block finds the best epoch count (early stopping) and
    then refits from scratch to that count; without one it trains for ``epochs`` epochs."""

    def __init__(self, kind: str, hidden: int, weight_decay: float, *, epochs: int | None = None):
        self.kind, self.hidden, self.weight_decay, self.epochs = kind, hidden, weight_decay, epochs

    def _train(self, Xw, y, n_epochs, Xv=None, yv=None):
        torch = _torch()
        net = _net(self.kind, Xw.shape[2], self.hidden)
        opt = torch.optim.Adam(net.parameters(), lr=LR, weight_decay=self.weight_decay)
        gen = torch.Generator().manual_seed(SEED)
        xt, yt = torch.as_tensor(Xw, dtype=torch.float32), torch.as_tensor(y, dtype=torch.float32)
        xv = None if Xv is None else torch.as_tensor(Xv, dtype=torch.float32)
        best, best_epoch, since = np.inf, 0, 0
        for epoch in range(1, n_epochs + 1):
            net.train()
            for b in torch.randperm(len(yt), generator=gen).split(BATCH):
                opt.zero_grad()
                loss = torch.mean((net(xt[b]) - yt[b]) ** 2)
                loss.backward()
                opt.step()
            if xv is None:
                continue
            net.eval()
            with torch.no_grad():
                err = float(np.mean((net(xv).numpy() - yv) ** 2))
            if err < best - 1e-12:
                best, best_epoch, since = err, epoch, 0
                best_state = copy.deepcopy(net.state_dict())
            else:
                since += 1
                if since >= PATIENCE:
                    break
        if xv is not None:
            # the weights after the best epoch: the same as retraining from scratch for best_epoch epochs,
            # since the evaluation draws no random numbers (tests/test_recurrent.py checks it)
            net.load_state_dict(best_state)
        return net, best_epoch

    def fit(self, Xw, y, Xv=None, yv=None):
        if Xv is None:
            self.net, _ = self._train(Xw, y, self.epochs or MAX_EPOCHS)
            return self
        self.net, self.epochs = self._train(Xw, y, MAX_EPOCHS, Xv, yv)
        return self

    def predict(self, Xw):
        torch = _torch()
        self.net.eval()
        with torch.no_grad():
            return self.net(torch.as_tensor(Xw, dtype=torch.float32)).numpy().astype(float)


def _scaled(X: np.ndarray, rows: np.ndarray) -> np.ndarray:
    """Standardise every row of X with the mean and sd of ``rows`` (the training rows)."""
    mu, sd = X[rows].mean(axis=0), X[rows].std(axis=0)
    sd[sd == 0] = 1.0
    return (X - mu) / sd


def choose(kind: str, X: np.ndarray, y: np.ndarray, tr: np.ndarray, *, horizon: int, val: int = 252,
           seq: int = SEQ) -> dict:
    """Pick a grid point on the last ``val`` rows of the training rows ``tr`` (candidates fitted on
    ``tr[: len(tr) - val - horizon]``), scaler fitted on the candidates' rows."""
    fit_rows, val_rows = tr[: len(tr) - val - horizon], tr[len(tr) - val:]
    Xs = _scaled(X, fit_rows)
    Xw, Xv = windows(Xs, fit_rows, seq), windows(Xs, val_rows, seq)
    best = None
    for params in GRID:
        m = RecurrentModel(kind, params["hidden"], params["weight_decay"]).fit(Xw, y[fit_rows], Xv, y[val_rows])
        resid = y[val_rows] - m.predict(Xv)
        err = float(np.mean(resid ** 2))
        if best is None or err < best["err"]:
            best = {"params": params, "err": err, "s2": float(np.var(resid)), "epochs": m.epochs}
    return best


def walk_forward_recurrent(target: pd.Series, features: pd.DataFrame | pd.Series, kind: str, *,
                           horizon: int = 21, step: int = 63, min_rows: int = 756, val: int = 252,
                           seq: int = SEQ) -> LearnerForecast:
    """The walk-forward of ``regimes.learners.walk_forward_learner`` with an LSTM or GRU on sequences.

    Rows are the dates where every feature is present; the first ``seq - 1`` rows serve only as inputs.
    At refit position ``i`` the training rows are those in ``[seq - 1, i - horizon)`` with a known target.
    """
    if kind not in RECURRENT:
        raise ValueError(f"unknown recurrent learner {kind!r}")
    X_all = features.to_frame() if isinstance(features, pd.Series) else features
    X_all = X_all.dropna()
    y = np.log(target.reindex(X_all.index).to_numpy(dtype=float))
    X = X_all.to_numpy(dtype=float)
    n = len(X_all)
    pieces, chosen = [], []
    for i in range(min_rows + horizon, n, step):
        end = min(i + step, n)
        tr = np.arange(seq - 1, i - horizon)
        tr = tr[~np.isnan(y[tr])]
        best = choose(kind, X, y, tr, horizon=horizon, val=val, seq=seq)
        Xs = _scaled(X, tr)
        model = RecurrentModel(kind, best["params"]["hidden"], best["params"]["weight_decay"],
                               epochs=best["epochs"]).fit(windows(Xs, tr, seq), y[tr])
        pred = np.exp(model.predict(windows(Xs, np.arange(i, end), seq)) + 0.5 * best["s2"])
        pieces.append(pd.Series(np.maximum(pred, _FLOOR), index=X_all.index[i:end]))
        chosen.append({"date": X_all.index[i], **best["params"], "val_mse": best["err"], "s2": best["s2"],
                       "epochs": best["epochs"]})
    if not pieces:
        raise ValueError(f"not enough rows ({n}) for min_rows={min_rows} and horizon={horizon}")
    return LearnerForecast(forecast=pd.concat(pieces), chosen=pd.DataFrame(chosen), n_refits=len(pieces))
