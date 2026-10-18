"""K-state Student-t HMMs with random restarts, and a causal walk-forward forecast from them.

Development-only tooling for the October 2026 continuation (b): the paper's two-state model was chosen
on an information-criterion table whose three- and four-state rows did not converge under default
starts (panel, item 10; desk, quant-researcher 11). This module fits a K-state Markov-switching model
with Student-t emissions by EM from ``n_starts`` starting points (one deterministic, the rest random),
reports how many starts converged and how many reached the best likelihood, and runs the same
frozen-parameter walk-forward as :func:`regimes.evaluate.walk_forward_oos`: fit on ``returns[:i]``,
freeze, filter forward over ``returns[:i+step]``, keep the held-out block, advance.

The E-step and the Student-t density are the ones in :mod:`regimes.student_t`; nothing there is
changed. Convergence of one EM run means the log-likelihood gain fell below ``tol`` before
``max_iter`` iterations; a run that stops at ``max_iter`` is recorded as not converged.
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .evaluate import horizon_weights
from .student_t import _VAR_FLOOR, _forward_backward, _t_logpdf, _update_nu

NU_BOUNDS = (2.1, 200.0)


@dataclass
class StudentTParams:
    """One fitted K-state Student-t HMM, states ordered by ascending scale (state 0 calmest)."""

    mu: np.ndarray
    sigma: np.ndarray
    nu: float
    A: np.ndarray          # row-stochastic, rows = from-state
    pi: np.ndarray
    loglik: float
    converged: bool
    n_iter: int

    @property
    def k(self) -> int:
        return len(self.sigma)

    @property
    def n_params(self) -> int:
        k = self.k
        return 2 * k + k * (k - 1) + (k - 1) + 1   # mu, sigma, A off-diagonals, pi, nu

    @property
    def state_variances(self) -> np.ndarray:
        """Variance of the Student-t emission in each state: sigma^2 nu / (nu - 2)."""
        return self.sigma ** 2 * self.nu / (self.nu - 2.0)

    def aic(self, n: int) -> float:
        return 2.0 * self.n_params - 2.0 * self.loglik

    def bic(self, n: int) -> float:
        return self.n_params * float(np.log(n)) - 2.0 * self.loglik


def deterministic_init(x: np.ndarray, k: int) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """The start :func:`regimes.student_t.fit_regimes_student_t` uses."""
    s = float(np.std(x)) or 1.0
    mu = np.full(k, float(np.mean(x)))
    sigma = s * np.linspace(0.5, 2.0, k)
    A = np.full((k, k), 0.05 / max(k - 1, 1))
    np.fill_diagonal(A, 0.95)
    pi = np.full(k, 1.0 / k)
    return mu, sigma, A, pi


def random_init(x: np.ndarray, k: int, rng: np.random.Generator) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """A random start: scales log-uniform in [0.25 s, 4 s] (sorted), means jittered around the sample
    mean, a sticky transition matrix with diagonals in [0.80, 0.99]."""
    s = float(np.std(x)) or 1.0
    mu = float(np.mean(x)) + 0.1 * s * rng.standard_normal(k)
    sigma = np.sort(s * np.exp(rng.uniform(np.log(0.25), np.log(4.0), size=k)))
    diag = rng.uniform(0.80, 0.99, size=k)
    off = rng.dirichlet(np.ones(max(k - 1, 1)), size=k)
    A = np.zeros((k, k))
    for i in range(k):
        others = [j for j in range(k) if j != i]
        A[i, i] = diag[i]
        for j, w in zip(others, off[i][: len(others)]):
            A[i, j] = (1.0 - diag[i]) * w
    pi = rng.dirichlet(np.ones(k))
    return mu, sigma, A, pi


def em_student_t(x: np.ndarray, k: int, init: tuple, *, nu0: float = 8.0, estimate_nu: bool = True,
                 max_iter: int = 200, tol: float = 1e-6) -> StudentTParams:
    """One EM run from ``init = (mu, sigma, A, pi)``. Same updates as ``fit_regimes_student_t``."""
    mu, sigma, A, pi = (np.array(v, dtype=float, copy=True) for v in init)
    nu = float(nu0)
    prev_ll = -np.inf
    converged = False
    n_iter = 0
    for n_iter in range(1, max_iter + 1):
        logB = _t_logpdf(x, mu, sigma, nu)
        _, smoothed, xi_sum, ll = _forward_backward(logB, A, pi)
        delta = ((x[:, None] - mu[None, :]) / sigma[None, :]) ** 2
        u = (nu + 1.0) / (nu + delta)
        w = smoothed * u
        gsum = smoothed.sum(axis=0)
        mu = (w * x[:, None]).sum(axis=0) / w.sum(axis=0)
        var = (smoothed * u * (x[:, None] - mu[None, :]) ** 2).sum(axis=0) / gsum
        sigma = np.sqrt(np.maximum(var, _VAR_FLOOR))
        pi = smoothed[0] / smoothed[0].sum()
        A = xi_sum / xi_sum.sum(axis=1, keepdims=True)
        if estimate_nu:
            new_delta = ((x[:, None] - mu[None, :]) / sigma[None, :]) ** 2
            nu = _update_nu(smoothed, new_delta, nu, NU_BOUNDS[0], NU_BOUNDS[1])
        if ll - prev_ll < tol:
            converged = True
            prev_ll = ll
            break
        prev_ll = ll
    order = np.argsort(sigma)
    return StudentTParams(mu=mu[order], sigma=sigma[order], nu=nu, A=A[np.ix_(order, order)], pi=pi[order],
                          loglik=float(prev_ll), converged=converged, n_iter=n_iter)


@dataclass
class RestartSummary:
    best: StudentTParams
    logliks: list[float]
    converged: list[bool]
    n_at_best: int          # starts whose loglik is within ``at_best_tol`` of the best
    at_best_tol: float = 1e-2
    runs: list[StudentTParams] = field(default_factory=list, repr=False)


def fit_student_t_restarts(x: np.ndarray, k: int, *, n_starts: int = 20, seed: int = 0, nu0: float = 8.0,
                           estimate_nu: bool = True, max_iter: int = 200, tol: float = 1e-6,
                           at_best_tol: float = 1e-2) -> RestartSummary:
    """EM from the deterministic start plus ``n_starts - 1`` random starts; keep the best likelihood.

    The best run is chosen among converged runs when any converged, otherwise among all runs.
    """
    rng = np.random.default_rng(seed)
    inits = [deterministic_init(x, k)] + [random_init(x, k, rng) for _ in range(max(n_starts - 1, 0))]
    runs = [em_student_t(x, k, init, nu0=nu0, estimate_nu=estimate_nu, max_iter=max_iter, tol=tol) for init in inits]
    pool = [r for r in runs if r.converged] or runs
    best = max(pool, key=lambda r: r.loglik)
    lls = [r.loglik for r in runs]
    return RestartSummary(best=best, logliks=lls, converged=[r.converged for r in runs],
                          n_at_best=int(sum(abs(ll - best.loglik) <= at_best_tol for ll in lls)),
                          at_best_tol=at_best_tol, runs=runs)


def filter_student_t(x: np.ndarray, params: StudentTParams) -> np.ndarray:
    """Causal filtered state probabilities P(S_t | x_1..x_t), shape (T, K), under frozen ``params``."""
    logB = _t_logpdf(x, params.mu, params.sigma, params.nu)
    filtered, _, _, _ = _forward_backward(logB, params.A, params.pi)
    return filtered


def implied_vol(filtered: np.ndarray, params: StudentTParams, horizon: int) -> np.ndarray:
    """Model-implied average daily vol over the next ``horizon`` days from today's filtered state
    probabilities: sqrt(E[variance]) with the state variances of the Student-t emissions."""
    w = filtered @ horizon_weights(params.A, horizon)
    return np.sqrt(w @ params.state_variances)


def _refit_block(args: tuple) -> dict:
    """Worker: fit on ``x[:i]`` with restarts, filter ``x[:end]`` with frozen parameters, return the block."""
    x, i, end, k, n_starts, seed, horizon, nu0, estimate_nu, max_iter, tol = args
    summ = fit_student_t_restarts(x[:i], k, n_starts=n_starts, seed=seed, nu0=nu0, estimate_nu=estimate_nu,
                                  max_iter=max_iter, tol=tol)
    p = summ.best
    filt = filter_student_t(x[:end], p)[i:end]
    var = p.state_variances
    return {
        "i": i, "end": end,
        "hv": filt[:, -1],                     # highest-variance state's probability
        "evar": filt @ var,                    # today's expected variance
        "iv": implied_vol(filt, p, horizon),
        "conv": {"n_starts": n_starts, "n_converged": int(sum(summ.converged)), "best_converged": p.converged,
                 "n_at_best": summ.n_at_best, "loglik": p.loglik, "nu": p.nu, "n_iter": p.n_iter,
                 "sigma_min": float(p.sigma[0]), "sigma_max": float(p.sigma[-1]),
                 "min_stay": float(np.diag(p.A).min())},
    }


@dataclass
class KStateWalkForward:
    high_vol_prob: pd.Series     # P(highest-variance state), causal
    expected_var: pd.Series      # sum_k P(k) var_k, causal
    implied_vol: pd.Series       # horizon-average implied daily vol, causal
    convergence: pd.DataFrame    # one row per refit
    n_refits: int


def walk_forward_student_t(returns: pd.Series, k: int, *, min_train: int = 756, step: int = 63, horizon: int = 21,
                           n_starts: int = 20, seed: int = 0, nu0: float = 8.0, estimate_nu: bool = True,
                           max_iter: int = 200, tol: float = 1e-6, n_jobs: int = 1) -> KStateWalkForward:
    """Expanding-window walk-forward for a K-state Student-t HMM, same protocol as ``walk_forward_oos``.

    Refit ``r`` uses seed ``seed + r`` for its random starts, so the run is deterministic for a given
    ``n_jobs``-independent task list. ``n_jobs > 1`` fits refits in separate processes.
    """
    y = returns.astype(float)
    x = y.to_numpy()
    n = len(x)
    if min_train >= n:
        raise ValueError(f"min_train={min_train} leaves no out-of-sample data (n={n})")
    tasks = [(x, i, min(i + step, n), k, n_starts, seed + r, horizon, nu0, estimate_nu, max_iter, tol)
             for r, i in enumerate(range(min_train, n, step))]
    if n_jobs > 1:
        with ProcessPoolExecutor(max_workers=n_jobs) as ex:
            blocks = list(ex.map(_refit_block, tasks))
    else:
        blocks = [_refit_block(t) for t in tasks]
    hv, ev, iv, conv, idx = [], [], [], [], []
    for b in blocks:
        ix = y.index[b["i"]:b["end"]]
        hv.append(pd.Series(b["hv"], index=ix))
        ev.append(pd.Series(b["evar"], index=ix))
        iv.append(pd.Series(b["iv"], index=ix))
        conv.append(b["conv"])
        idx.append(y.index[b["i"]])
    return KStateWalkForward(
        high_vol_prob=pd.concat(hv).clip(0.0, 1.0).rename(f"k{k}_high_vol_prob"),
        expected_var=pd.concat(ev).rename(f"k{k}_expected_var"),
        implied_vol=pd.concat(iv).rename(f"k{k}_implied_vol"),
        convergence=pd.DataFrame(conv, index=pd.Index(idx, name="refit_at")),
        n_refits=len(blocks),
    )
