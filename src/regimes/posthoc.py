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
