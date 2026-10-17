"""Stock-bond correlation regimes: a hidden Markov model pointed at a state that is actually hidden.

The volatility regime model in this repo turned out to add little over trailing volatility, because
volatility is close to observable: a few large daily moves reveal it within days. The sign of the
stock-bond correlation is a better candidate for a hidden state. It was negative for most of
2000-2021, so bonds hedged equities, and turned positive in 2022, when both fell together. Daily
cross-products are very noisy, so a trailing correlation needs a long window to be stable and is
then slow to notice a change. That is the situation a latent-state model is built for.

The design, fixed before looking at results:

- Inputs: daily log returns of equities and Treasuries, each **devolatilised** by its own EWMA vol
  from the previous day (``devolatilise``). Without this step the states would split on volatility
  again, since equity variance dominates the likelihood; with it, what is left to separate the states
  is mostly correlation.
- Model: a K-state HMM with a full-covariance Gaussian per state, fit by EM (Baum-Welch). States are
  ordered canonically by their correlation, ascending, so the last state is "most positive".
- Walk-forward: fit on data up to each refit edge, freeze the parameters, filter forward over the
  next block, keep only that block. The same protocol as ``evaluate.walk_forward_oos``.
- Forecast: the model-implied correlation over the next ``horizon`` days, averaging the state
  correlations under the filtered state probabilities propagated through the transition matrix.
- Baselines, scored on the same days: trailing 63-day and 252-day correlation and an EWMA
  correlation. Target: the realised correlation of the raw returns over the next ``horizon`` days.
"""
from __future__ import annotations

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd

_RIDGE = 1e-6  # keeps a state covariance positive definite


def devolatilise(returns: pd.DataFrame, alpha: float = 0.06) -> pd.DataFrame:
    """Divide each return by its own EWMA volatility from the *previous* day (causal).

    The first row has no prior volatility and is dropped.
    """
    vol = np.sqrt((returns.astype(float) ** 2).ewm(alpha=alpha, adjust=False).mean())
    return (returns / vol.shift(1)).iloc[1:]


def trailing_corr(returns: pd.DataFrame, window: int) -> pd.Series:
    """Trailing ``window``-day correlation between the two columns of ``returns``."""
    a, b = returns.columns[:2]
    return returns[a].rolling(window).corr(returns[b])


def ewma_corr(returns: pd.DataFrame, alpha: float = 0.03) -> pd.Series:
    """Exponentially weighted correlation between the two columns (zero-mean, causal)."""
    a, b = (returns[c].astype(float) for c in returns.columns[:2])
    cov = (a * b).ewm(alpha=alpha, adjust=False).mean()
    va = (a ** 2).ewm(alpha=alpha, adjust=False).mean()
    vb = (b ** 2).ewm(alpha=alpha, adjust=False).mean()
    return cov / np.sqrt(va * vb)


def forward_corr(returns: pd.DataFrame, horizon: int) -> pd.Series:
    """Realised correlation over the NEXT ``horizon`` days, (t, t + horizon]: the target."""
    return trailing_corr(returns, horizon).shift(-horizon)


@dataclass
class CorrHMMParams:
    pi: np.ndarray    # (K,) initial state distribution
    A: np.ndarray     # (K, K) transition matrix, rows sum to 1
    mu: np.ndarray    # (K, d) state means
    cov: np.ndarray   # (K, d, d) state covariances

    @property
    def rho(self) -> np.ndarray:
        """Correlation between the first two series in each state."""
        c = self.cov
        return c[:, 0, 1] / np.sqrt(c[:, 0, 0] * c[:, 1, 1])

    def ordered(self) -> "CorrHMMParams":
        """The same model with states sorted by correlation, ascending."""
        o = np.argsort(self.rho)
        return CorrHMMParams(self.pi[o], self.A[np.ix_(o, o)], self.mu[o], self.cov[o])


def _gauss_logpdf(z: np.ndarray, mu: np.ndarray, cov: np.ndarray) -> np.ndarray:
    """Log multivariate normal density, shape (T, K) for z:(T, d), mu:(K, d), cov:(K, d, d)."""
    T, d = z.shape
    out = np.empty((T, len(mu)))
    for k in range(len(mu)):
        L = np.linalg.cholesky(cov[k])
        sol = np.linalg.solve(L, (z - mu[k]).T)  # (d, T)
        out[:, k] = (-0.5 * (sol ** 2).sum(axis=0) - np.log(np.diag(L)).sum()
                     - 0.5 * d * np.log(2.0 * np.pi))
    return out


def _forward(B: np.ndarray, A: np.ndarray, pi: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Scaled forward recursion. Returns (alpha, scale): alpha[t] = P(state_t | obs up to t).

    Written over Python floats rather than numpy rows: with two or three states, per-step numpy
    overhead dominates, and this loop runs thousands of times per EM fit.
    """
    T, K = B.shape
    Bl, Al = B.tolist(), A.tolist()
    alpha = [[0.0] * K for _ in range(T)]
    scale = [0.0] * T
    row = [pi[k] * Bl[0][k] for k in range(K)]
    c = sum(row)
    scale[0], alpha[0] = c, [v / c for v in row]
    for t in range(1, T):
        prev, bt = alpha[t - 1], Bl[t]
        row = [sum(prev[i] * Al[i][j] for i in range(K)) * bt[j] for j in range(K)]
        c = sum(row)
        scale[t], alpha[t] = c, [v / c for v in row]
    return np.array(alpha), np.array(scale)


def _backward(B: np.ndarray, A: np.ndarray, scale: np.ndarray) -> np.ndarray:
    """Scaled backward recursion matching ``_forward``'s scaling."""
    T, K = B.shape
    Bl, Al, sl = B.tolist(), A.tolist(), scale.tolist()
    beta = [[1.0] * K for _ in range(T)]
    for t in range(T - 2, -1, -1):
        nxt = [Bl[t + 1][j] * beta[t + 1][j] for j in range(K)]
        c = sl[t + 1]
        beta[t] = [sum(Al[i][j] * nxt[j] for j in range(K)) / c for i in range(K)]
    return np.array(beta)


def _forward_backward(logB: np.ndarray, A: np.ndarray, pi: np.ndarray):
    """Scaled forward-backward: (smoothed probabilities, summed transition posteriors, loglik).

    Same quantities as ``student_t._forward_backward``, with the xi sum vectorised and the
    recursions over Python floats, which matters for the many walk-forward refits here.
    """
    shift = logB.max(axis=1, keepdims=True)
    B = np.exp(logB - shift)
    alpha, scale = _forward(B, A, pi)
    beta = _backward(B, A, scale)
    gamma = alpha * beta
    gamma /= gamma.sum(axis=1, keepdims=True)
    # xi_t(i, j) = alpha_t(i) A(i, j) B_{t+1}(j) beta_{t+1}(j) / scale_{t+1}, each summing to 1.
    xi_sum = A * (alpha[:-1].T @ (B[1:] * beta[1:] / scale[1:, None]))
    loglik = float(np.log(scale).sum() + shift.sum())
    return gamma, xi_sum, loglik


def _default_init(z: np.ndarray, K: int) -> CorrHMMParams:
    """Deterministic start: unit variances, correlations spread from -0.5 to +0.5, sticky A."""
    d = z.shape[1]
    var = z.var(axis=0)
    cov = np.empty((K, d, d))
    for k, r in enumerate(np.linspace(-0.5, 0.5, K)):
        c = np.diag(var)
        c[0, 1] = c[1, 0] = r * np.sqrt(var[0] * var[1])
        cov[k] = c
    A = np.full((K, K), 0.01 / max(K - 1, 1))
    np.fill_diagonal(A, 0.99)
    return CorrHMMParams(np.full(K, 1.0 / K), A, np.tile(z.mean(axis=0), (K, 1)), cov)


def fit_corr_hmm(z: np.ndarray, n_regimes: int = 2, *, init: CorrHMMParams | None = None,
                 max_iter: int = 200, tol: float = 1e-4,
                 tie_variances: bool = False, info: dict | None = None) -> tuple[CorrHMMParams, float]:
    """Fit a full-covariance Gaussian HMM by EM. Returns (params ordered by correlation, loglik).

    ``info``, if given, is filled with ``iterations`` and ``converged`` (True when the loop stopped
    on the tolerance rather than on ``max_iter``); nothing else changes.

    ``tie_variances=True`` forces every state to share the same variances, so the states can differ
    only in correlation (and mean). Unconstrained, maximum likelihood prefers to spend the states on
    volatility shocks that survive devolatilisation, which is the wrong split for this question. The
    tied M-step keeps each state's weighted correlation and replaces its variances with the pooled
    ones. That is an approximate (generalised) EM step rather than the exact constrained maximiser,
    so the loop also stops if the likelihood ever falls.
    """
    z = np.asarray(z, dtype=float)
    K, d = n_regimes, z.shape[1]
    p = init if init is not None else _default_init(z, K)
    pi, A, mu, cov = p.pi.copy(), p.A.copy(), p.mu.copy(), p.cov.copy()

    prev_ll = -np.inf
    converged = False
    iterations = 0
    for _ in range(max_iter):
        iterations += 1
        gamma, xi_sum, ll = _forward_backward(_gauss_logpdf(z, mu, cov), A, pi)
        g = gamma.sum(axis=0)
        mu = (gamma.T @ z) / g[:, None]
        for k in range(K):
            dz = z - mu[k]
            cov[k] = (gamma[:, k, None] * dz).T @ dz / g[k] + _RIDGE * np.eye(d)
        if tie_variances:
            sd_k = np.sqrt(np.einsum("kii->ki", cov))                     # (K, d)
            corr = cov / (sd_k[:, :, None] * sd_k[:, None, :])
            pooled = np.sqrt((g[:, None] * sd_k ** 2).sum(axis=0) / g.sum())
            cov = corr * np.outer(pooled, pooled)[None, :, :]
        pi = gamma[0] / gamma[0].sum()
        A = xi_sum / xi_sum.sum(axis=1, keepdims=True)
        if ll - prev_ll < tol:
            converged = True
            break
        prev_ll = ll
    if info is not None:
        info.update(iterations=iterations, converged=converged)
    return CorrHMMParams(pi, A, mu, cov).ordered(), float(ll)


def filter_probs(z: np.ndarray, params: CorrHMMParams) -> np.ndarray:
    """Causal filtered state probabilities P(state_t | z_1..z_t), shape (T, K)."""
    logB = _gauss_logpdf(np.asarray(z, dtype=float), params.mu, params.cov)
    alpha, _ = _forward(np.exp(logB - logB.max(axis=1, keepdims=True)), params.A, params.pi)
    return alpha


def _horizon_weights(A: np.ndarray, horizon: int) -> np.ndarray:
    """Average of A^1 .. A^horizon: maps today's state probabilities to the mean over the horizon."""
    acc = np.zeros_like(A)
    P = np.eye(len(A))
    for _ in range(horizon):
        P = P @ A
        acc += P
    return acc / horizon


@dataclass
class CorrWalkForwardResult:
    prob_high: pd.Series       # filtered P(most-positive-correlation state), out of sample
    implied_corr: pd.Series    # model-implied correlation over the next ``horizon`` days
    state_rho: pd.DataFrame    # per-refit state correlations (diagnostic), indexed by refit date
    n_refits: int
    n_skipped: int
    convergence: pd.DataFrame | None = None  # per refit: starts, converged, best_converged, iterations


def walk_forward_corr_regimes(returns: pd.DataFrame, *, n_regimes: int = 2, min_train: int = 756,
                              step: int = 63, horizon: int = 63,
                              alpha: float = 0.06, warm_start: bool = True,
                              tie_variances: bool = False) -> CorrWalkForwardResult:
    """Expanding-window walk-forward for the correlation HMM, frozen parameters filtered forward.

    Each refit runs EM from the default start and, if ``warm_start``, also from the previous fit (still
    causal: the previous fit only saw earlier data), and keeps whichever has the higher likelihood.
    """
    z_df = devolatilise(returns, alpha=alpha).dropna()
    z = z_df.to_numpy()
    n = len(z)
    if min_train >= n:
        raise ValueError(f"min_train={min_train} leaves no out-of-sample data (n={n})")

    probs, implied, rho_rows, rho_idx = [], [], [], []
    conv_rows, conv_idx = [], []
    params = None
    n_refits = n_skipped = 0
    for i in range(min_train, n, step):
        end = min(i + step, n)
        try:
            # EM finds a local optimum, so keep the better of a warm start and a fresh start.
            infos = [{}]
            fits = [fit_corr_hmm(z[:i], n_regimes, tie_variances=tie_variances, info=infos[0])]
            if params is not None and warm_start:
                infos.append({})
                fits.append(fit_corr_hmm(z[:i], n_regimes, init=params, tie_variances=tie_variances,
                                         info=infos[-1]))
            best = max(range(len(fits)), key=lambda j: fits[j][1])
            params = fits[best][0]
            conv_rows.append(convergence_row(infos, best))
            conv_idx.append(z_df.index[i])
        except (np.linalg.LinAlgError, FloatingPointError, ValueError) as exc:
            warnings.warn(f"correlation HMM fit failed at i={i}: {exc}", RuntimeWarning, stacklevel=2)
            n_skipped += 1
            continue
        n_refits += 1
        filt = filter_probs(z[:end], params)[i:end]
        idx = z_df.index[i:end]
        probs.append(pd.Series(filt[:, -1], index=idx))
        implied.append(pd.Series(filt @ _horizon_weights(params.A, horizon) @ params.rho, index=idx))
        rho_rows.append(params.rho)
        rho_idx.append(z_df.index[i])

    if not probs:
        raise RuntimeError("no out-of-sample blocks were produced (all fits skipped?)")
    cols = [f"state_{k}" for k in range(n_regimes)]
    return CorrWalkForwardResult(
        prob_high=pd.concat(probs).rename("prob_high_corr"),
        implied_corr=pd.concat(implied).rename("hmm_implied_corr"),
        state_rho=pd.DataFrame(rho_rows, index=pd.DatetimeIndex(rho_idx), columns=cols),
        n_refits=n_refits,
        n_skipped=n_skipped,
        convergence=pd.DataFrame(conv_rows, index=pd.DatetimeIndex(conv_idx)),
    )


def convergence_row(infos: list[dict], best: int) -> dict:
    """One walk-forward refit's convergence record from the per-start ``info`` dicts: how many
    starts were run, how many converged, whether the start that won did, and its iteration count
    (EM) when known."""
    row = {"starts": len(infos), "converged": int(sum(bool(d.get("converged")) for d in infos)),
           "best_converged": bool(infos[best].get("converged"))}
    if "iterations" in infos[best]:
        row["iterations"] = int(infos[best]["iterations"])
    return row


def convergence_counts(convergence: pd.DataFrame | None) -> str:
    """Printable summary of a walk-forward's convergence table, e.g. "95 of 95 refits converged
    (190 of 190 starts)"."""
    if convergence is None or convergence.empty:
        return "no convergence record"
    n = len(convergence)
    text = f"{int(convergence['best_converged'].sum())} of {n} refits converged"
    if "starts" in convergence:
        text += f" ({int(convergence['converged'].sum())} of {int(convergence['starts'].sum())} starts)"
    return text


def sustained_sign_state(signal: pd.Series, run: int = 21) -> pd.Series:
    """Causal sign "call": switches to +1 or -1 only once the signal has held that sign ``run`` days.

    The value at t uses the signal up to t only, so a switch is dated on the day it could have been
    known. Before the first ``run``-day stretch the state is undefined (NaN).
    """
    sign = np.sign(signal.dropna())
    held = sign.rolling(run).apply(lambda w: w[0] if (w == w[0]).all() and w[0] != 0 else 0.0,
                                   raw=True)
    state = held.replace(0.0, np.nan).ffill()
    return state.rename("state")


def regime_flips(target: pd.Series, min_len: int = 126) -> list[tuple[pd.Timestamp, int]]:
    """Sign changes of ``target`` between runs of at least ``min_len`` days: [(start date, new sign)].

    Runs shorter than ``min_len`` are treated as noise and skipped, so a flip is a change from one
    lasting regime to an opposite-signed lasting regime.
    """
    sign = np.sign(target.dropna())
    sign = sign[sign != 0]
    run_id = (sign != sign.shift()).cumsum()
    runs = [(g.index[0], int(g.iloc[0]), len(g)) for _, g in sign.groupby(run_id)]
    kept = [(d, s) for d, s, n in runs if n >= min_len]
    return [(d, s) for (d, s), (_, prev) in zip(kept[1:], kept[:-1]) if s != prev]


def score_detection(state: pd.Series, flips: list[tuple[pd.Timestamp, int]],
                    max_lag: int = 252) -> tuple[list[float], int, int]:
    """Detection lags (trading days) for each flip, misses, and false alarms of a sign ``state``.

    Lag for a flip on day d to sign s: trading days from d to the first day on or after d with
    ``state == s`` (0 if the state already showed s on d). Missed if that takes more than
    ``max_lag`` days. A false alarm is a switch of the state that does not fall within ``max_lag``
    days after a flip to the same sign.
    """
    state = state.dropna()
    pos = {d: i for i, d in enumerate(state.index)}
    lags, misses = [], 0
    for d, s in flips:
        after = state.loc[d:]
        hit = after[after == s]
        if len(hit) and pos[hit.index[0]] - pos[after.index[0]] <= max_lag:
            lags.append(float(pos[hit.index[0]] - pos[after.index[0]]))
        else:
            misses += 1
    switches = state[state != state.shift()].iloc[1:]
    false_alarms = 0
    for d, s in switches.items():
        explained = any(fd <= d and s == fs and pos[d] - pos[state.loc[fd:].index[0]] <= max_lag
                        for fd, fs in flips if fd <= state.index[-1])
        false_alarms += 0 if explained else 1
    return lags, misses, false_alarms
