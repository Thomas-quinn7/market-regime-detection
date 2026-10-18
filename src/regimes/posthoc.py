"""Post-hoc comparison statistics for saved forecasts (October 2026 reopen, stage S2).

None of these were registered for any holdout. They are computed after the fact from the reproduced
forecasts, to show how the registered verdicts look under other standard tools; they never replace
a registered verdict.

- ``hac_dm``: Diebold-Mariano test of equal mean loss with a Newey-West (Bartlett) long-run variance.
- ``paired_interval``: paired bootstrap 95% interval for an RMSE or mean-loss difference, with either
  the circular block bootstrap used by the holdouts (any block length) or the stationary bootstrap
  of Politis and Romano (1994). With ``scheme="circular"`` and the holdouts' settings it reproduces
  ``regimes.forecast.paired_rmse_diff_interval`` and ``paired_mean_diff_interval`` exactly.
- ``excluded_change_pct``: the equivalence reading of an interval, in percent of the reference loss.
- ``paired_draws`` and ``bootstrap_p_value`` (stage S7): the bootstrap draws behind ``paired_interval``
  (same seed, same draws) and the two-sided p-value got by inverting the percentile interval.
- ``holm``: Holm's (1979) step-down adjustment of a family of p-values.
"""
from __future__ import annotations

import math

import numpy as np


def hac_dm(loss: np.ndarray, loss_base: np.ndarray, *, lag: int = 20) -> dict[str, float]:
    """Diebold-Mariano statistic for mean(loss - loss_base) with a Bartlett-kernel HAC variance.

    Returns the mean difference, its HAC standard error, the statistic and the two-sided normal
    p-value. ``lag`` = 20 suits 21-day overlapping targets (the forecast errors are MA(20) under the
    null of an optimal forecast).
    """
    d = np.asarray(loss, dtype=float) - np.asarray(loss_base, dtype=float)
    n = len(d)
    u = d - d.mean()
    lrv = u @ u / n
    for k in range(1, min(lag, n - 1) + 1):
        lrv += 2.0 * (1.0 - k / (lag + 1)) * (u[k:] @ u[:-k]) / n
    se = math.sqrt(max(lrv, 0.0) / n)
    stat = d.mean() / se if se > 0 else float("nan")
    p = math.erfc(abs(stat) / math.sqrt(2.0)) if se > 0 else float("nan")
    return {"mean_diff": float(d.mean()), "se": se, "stat": float(stat), "p": float(p)}


def _circular_indices(rng: np.random.Generator, n: int, block: int) -> np.ndarray:
    offsets = np.arange(block)
    return ((rng.integers(0, n, -(-n // block))[:, None] + offsets).ravel() % n)[:n]


def stationary_indices(rng: np.random.Generator, n: int, mean_block: float) -> np.ndarray:
    """One stationary-bootstrap resample of 0..n-1: geometric block lengths with mean ``mean_block``,
    wrapping circularly."""
    p = 1.0 / mean_block
    starts = rng.integers(0, n, n)
    new_block = rng.random(n) < p
    new_block[0] = True
    idx = np.empty(n, dtype=np.int64)
    for t in range(n):
        idx[t] = starts[t] if new_block[t] else (idx[t - 1] + 1) % n
    return idx


def paired_interval(a: np.ndarray, b: np.ndarray, *, statistic: str = "rmse", scheme: str = "circular",
                    block: float = 63, n_boot: int = 2000, seed: int = 0) -> tuple[float, float]:
    """Paired bootstrap 95% interval.

    ``statistic="rmse"``: ``a`` and ``b`` are forecast errors and the interval is for
    RMSE(a) - RMSE(b). ``statistic="mean"``: they are per-day losses (e.g. QLIKE) and the interval is
    for mean(a) - mean(b). ``scheme`` is "circular" (fixed blocks of ``block`` days) or "stationary"
    (geometric blocks with mean ``block``).
    """
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    n = len(a)
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot)
    d = a - b
    for i in range(n_boot):
        if scheme == "circular":
            idx = _circular_indices(rng, n, int(block))
        elif scheme == "stationary":
            idx = stationary_indices(rng, n, block)
        else:
            raise ValueError(f"unknown scheme {scheme!r}")
        if statistic == "rmse":
            out[i] = np.sqrt((a[idx] ** 2).mean()) - np.sqrt((b[idx] ** 2).mean())
        elif statistic == "mean":
            out[i] = d[idx].mean()
        else:
            raise ValueError(f"unknown statistic {statistic!r}")
    lo, hi = np.percentile(out, [2.5, 97.5])
    return float(lo), float(hi)


def excluded_change_pct(lo: float, hi: float, reference: float) -> dict[str, float]:
    """Read an interval for (forecast loss - reference loss) as percentages of the reference loss.

    ``largest_gain_allowed``: how much better than the reference the forecast could still be (the
    lower end, as a positive percent; 0 if the interval lies above zero). ``largest_loss_allowed``:
    likewise for being worse. A "no difference" interval with both under x% supports equivalence
    within x%.
    """
    return {"largest_gain_allowed": 100.0 * max(0.0, -lo) / reference,
            "largest_loss_allowed": 100.0 * max(0.0, hi) / reference}


def mcs(losses: np.ndarray, *, alpha: float = 0.10, block: int = 63, n_boot: int = 2000,
        seed: int = 0) -> dict[str, np.ndarray]:
    """Model confidence set (Hansen, Lunde and Nason 2011) with the T_max statistic.

    ``losses`` is an n-by-m array of per-day losses, one column per forecast. Models are eliminated
    one at a time, worst first, until the equal-predictive-ability hypothesis on the survivors is not
    rejected at ``alpha``. The bootstrap is the same circular block bootstrap as the holdouts; the
    draws are fixed once and reused at every step. Returns, per model, the MCS p-value (the largest
    bootstrap p-value at or before the step that removed it, 1.0 for the last survivor), the rank of
    elimination (1 = eliminated first, m = last survivor) and membership at ``alpha``.
    """
    L = np.asarray(losses, dtype=float)
    n, m = L.shape
    rng = np.random.default_rng(seed)
    draws = np.stack([_circular_indices(rng, n, block) for _ in range(n_boot)])  # n_boot x n
    mean_full = L.mean(axis=0)
    boot_full = np.stack([L[idx].mean(axis=0) for idx in draws])  # n_boot x m
    alive = list(range(m))
    p_values = np.ones(m)
    order = np.zeros(m, dtype=int)
    p_running = 0.0
    step = 0
    while len(alive) > 1:
        cols = np.array(alive)
        d = mean_full[cols] - mean_full[cols].mean()
        d_boot = boot_full[:, cols] - boot_full[:, cols].mean(axis=1, keepdims=True)
        var = ((d_boot - d) ** 2).mean(axis=0)
        var = np.where(var > 0, var, np.nan)
        t = d / np.sqrt(var)
        t_boot = (d_boot - d) / np.sqrt(var)
        t_max = np.nanmax(t)
        p = float(np.mean(np.nanmax(t_boot, axis=1) >= t_max))
        p_running = max(p_running, p)
        worst = cols[int(np.nanargmax(t))]
        step += 1
        p_values[worst] = p_running
        order[worst] = step
        alive.remove(int(worst))
    p_values[alive[0]] = 1.0
    order[alive[0]] = m
    return {"p_value": p_values, "elimination_rank": order, "in_set": p_values >= alpha}


def _bartlett_lrv(u: np.ndarray, lag: int) -> float:
    """Long-run variance of a mean-zero series with the Bartlett kernel (Newey-West), per observation."""
    n = len(u)
    lrv = u @ u / n
    for k in range(1, min(lag, n - 1) + 1):
        lrv += 2.0 * (1.0 - k / (lag + 1)) * (u[k:] @ u[:-k]) / n
    return float(max(lrv, 0.0))


def mincer_zarnowitz(forecast: np.ndarray, realised: np.ndarray, *, lag: int = 20) -> dict[str, float]:
    """Mincer-Zarnowitz regression ``realised = a + b * forecast`` by OLS with HAC standard errors.

    Returns the intercept and slope, their Bartlett-kernel HAC standard errors (``lag`` autocovariances,
    20 for 21-day overlapping targets), the R-squared, the Wald statistic for the joint hypothesis
    a = 0, b = 1 (chi-squared with two degrees of freedom under the null) and its p-value. A slope of
    one with a zero intercept means the forecast is unbiased at every level; a slope below one means
    high forecasts overshoot and low ones undershoot.
    """
    f = np.asarray(forecast, dtype=float)
    y = np.asarray(realised, dtype=float)
    n = len(f)
    if n < 3 or len(y) != n:
        raise ValueError("need at least three paired observations")
    x = np.column_stack([np.ones(n), f])
    xtx_inv = np.linalg.inv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    resid = y - x @ beta
    # HAC covariance of beta: (X'X)^-1 S (X'X)^-1 with S the Bartlett long-run covariance of x_t u_t.
    g = x * resid[:, None]
    s = g.T @ g
    for k in range(1, min(lag, n - 1) + 1):
        gamma = g[k:].T @ g[:-k]
        s += (1.0 - k / (lag + 1)) * (gamma + gamma.T)
    cov = xtx_inv @ s @ xtx_inv
    se = np.sqrt(np.clip(np.diag(cov), 0.0, None))
    r2 = 1.0 - resid @ resid / (((y - y.mean()) ** 2).sum() or np.nan)
    d = beta - np.array([0.0, 1.0])
    try:
        wald = float(d @ np.linalg.solve(cov, d))
    except np.linalg.LinAlgError:
        wald = float("nan")
    p = math.exp(-wald / 2.0) if math.isfinite(wald) else float("nan")  # chi2(2) survival function
    return {"intercept": float(beta[0]), "slope": float(beta[1]), "se_intercept": float(se[0]),
            "se_slope": float(se[1]), "r2": float(r2), "wald_a0_b1": wald, "p_a0_b1": float(p), "n": n}


def variance_swap_sign_test(forecast: np.ndarray, realised: np.ndarray, strike_vol: np.ndarray) -> dict[str, float]:
    """A forecast's content as a variance-swap signal, in the units of the inputs (daily percent vol).

    The strike is ``strike_vol ** 2`` (the implied variance, e.g. the raw VIX in daily-percent units),
    the swap pays ``realised ** 2 - strike`` to the long side, and the forecast says long when its own
    variance ``forecast ** 2`` is above the strike, short otherwise. Returns the share of days the
    forecast is long, the mean payoff and hit rate of trading its sign, the same for always-short
    (which the market's variance risk premium rewards on average), the mean payoff and hit rate on the
    long days alone, and the HAC-DM p-value (lag 20) of the forecast's payoff against always-short.
    A forecast that is never long has exactly the always-short P&L and so no content beyond selling
    the premium.
    """
    f = np.asarray(forecast, dtype=float)
    y = np.asarray(realised, dtype=float)
    k = np.asarray(strike_vol, dtype=float) ** 2
    if not (len(f) == len(y) == len(k)):
        raise ValueError("forecast, realised and strike must have the same length")
    payoff = y ** 2 - k
    long = f ** 2 > k
    sign = np.where(long, 1.0, -1.0)
    pnl = sign * payoff
    short_pnl = -payoff
    out = {
        "n": int(len(f)), "share_long": float(long.mean()),
        "mean_pnl": float(pnl.mean()), "hit_rate": float((pnl > 0).mean()),
        "short_mean_pnl": float(short_pnl.mean()), "short_hit_rate": float((short_pnl > 0).mean()),
        "long_days_mean_payoff": float(payoff[long].mean()) if long.any() else float("nan"),
        "long_days_hit_rate": float((payoff[long] > 0).mean()) if long.any() else float("nan"),
    }
    out["p_vs_short"] = hac_dm(-pnl, -short_pnl, lag=20)["p"] if long.any() and not long.all() else float("nan")
    return out


def paired_draws(a: np.ndarray, b: np.ndarray, *, statistic: str = "rmse", scheme: str = "circular",
                 block: float = 63, n_boot: int = 2000, seed: int = 0) -> np.ndarray:
    """The ``n_boot`` bootstrap draws of the difference that ``paired_interval`` takes percentiles of,
    with the same seed and the same resamples, so that ``np.percentile(draws, [2.5, 97.5])`` equals
    ``paired_interval`` with the same arguments."""
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    n = len(a)
    rng = np.random.default_rng(seed)
    out = np.empty(n_boot)
    d = a - b
    for i in range(n_boot):
        if scheme == "circular":
            idx = _circular_indices(rng, n, int(block))
        elif scheme == "stationary":
            idx = stationary_indices(rng, n, block)
        else:
            raise ValueError(f"unknown scheme {scheme!r}")
        if statistic == "rmse":
            out[i] = np.sqrt((a[idx] ** 2).mean()) - np.sqrt((b[idx] ** 2).mean())
        elif statistic == "mean":
            out[i] = d[idx].mean()
        else:
            raise ValueError(f"unknown statistic {statistic!r}")
    return out


def bootstrap_p_value(draws: np.ndarray) -> float:
    """Two-sided p-value for "the difference is zero" from bootstrap draws of the difference, by
    inverting the percentile interval: 2 * min(share of draws <= 0, share >= 0), counted with the
    usual +1 so it is never 0 (smallest value 2 / (n_boot + 1)). A 95% percentile interval that
    excludes zero corresponds to a p-value of about 0.05 or less."""
    draws = np.asarray(draws, dtype=float)
    n = len(draws)
    lo = (np.sum(draws <= 0) + 1) / (n + 1)
    hi = (np.sum(draws >= 0) + 1) / (n + 1)
    return float(min(1.0, 2.0 * min(lo, hi)))


def holm(pvalues, alpha: float = 0.05) -> dict[str, np.ndarray]:
    """Holm's step-down procedure on one family.

    Returns ``adjusted`` (Holm-adjusted p-values, monotone, capped at 1, in the input order) and
    ``reject`` (adjusted < = alpha). NaN p-values are left out of the family and come back as NaN /
    False.
    """
    p = np.asarray(pvalues, dtype=float)
    ok = ~np.isnan(p)
    adjusted = np.full(p.shape, np.nan)
    pv = p[ok]
    m = len(pv)
    if m:
        order = np.argsort(pv, kind="mergesort")
        adj_sorted = np.maximum.accumulate((m - np.arange(m)) * pv[order])
        adj = np.empty(m)
        adj[order] = np.minimum(adj_sorted, 1.0)
        adjusted[ok] = adj
    return {"adjusted": adjusted, "reject": np.where(ok, adjusted <= alpha, False)}
