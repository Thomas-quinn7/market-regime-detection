"""Honest evaluation of inferred regimes.

The claim under test is deliberately narrow and falsifiable: *does the filtered high-volatility
probability carry out-of-sample information about next-period realised volatility?* If it does not,
the regimes are decorative and we say so.

Two levels of rigour live here:
- ``oos_realised_vol_check`` demonstrates the filtered-vs-smoothed distinction on a full-sample fit.
- ``walk_forward_oos`` is the fully rigorous version: it *re-estimates parameters* on each expanding
  train window, so even the emission/transition parameters are free of future data.
"""
from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd

from .model import RegimeFit


def realised_vol(returns: pd.Series, window: int = 21) -> pd.Series:
    """Trailing realised volatility (std of returns over ``window`` days)."""
    return returns.rolling(window).std()


def ewma_vol(returns: pd.Series, alpha: float = 0.06) -> pd.Series:
    """Exponentially weighted volatility, zero-mean (RiskMetrics: ``alpha = 1 - lambda = 0.06``).

    Causal: the value at t uses returns up to and including t only.
    """
    return np.sqrt((returns.astype(float) ** 2).ewm(alpha=alpha, adjust=False).mean())


@dataclass
class Agreement:
    """How closely two high-vol probability series agree, on their shared dates."""

    corr: float           # correlation of the two probability series
    label_agreement: float  # fraction of dates both put on the same side of ``threshold``
    n: int


def regime_agreement(prob_a: pd.Series, prob_b: pd.Series, *, threshold: float = 0.5) -> Agreement:
    """Compare two filtered high-vol probability series (e.g. baseline vs an AR-mean variant).

    Used as a robustness check: if a richer model's regimes agree closely with the baseline's, the
    baseline's regimes were not an artefact of its simpler assumptions.
    """
    joined = pd.concat({"a": prob_a, "b": prob_b}, axis=1, sort=True).dropna()
    hi_a = joined["a"] >= threshold
    hi_b = joined["b"] >= threshold
    return Agreement(
        corr=float(joined["a"].corr(joined["b"])),
        label_agreement=float((hi_a == hi_b).mean()),
        n=len(joined),
    )


@dataclass
class OOSResult:
    """Outcome of the causal predictive check."""

    corr_filtered: float  # corr(high-vol filtered prob at t, realised vol over (t, t+h])
    corr_smoothed: float  # same but with smoothed prob — expected to look better *because* it cheats
    horizon: int
    n: int


def oos_realised_vol_check(returns: pd.Series, fit: RegimeFit, horizon: int = 21,
                           index: pd.Index | None = None) -> OOSResult:
    """Correlate today's high-vol regime probability with *future* realised vol.

    The key comparison is ``corr_filtered`` (causal, honest) vs ``corr_smoothed`` (uses future data).
    If smoothed materially beats filtered, that gap is exactly the look-ahead a naive write-up would
    have banked as "signal".

    NOTE: ``fit`` here is estimated on the full sample, so ``corr_filtered`` still enjoys full-sample
    *parameter* estimation. Use ``walk_forward_oos`` (below) for the version that removes that leak by
    re-estimating parameters on past data only.

    Pass ``index`` (e.g. a walk-forward run's out-of-sample dates) to score on those dates only. The
    walk-forward span starts after its training window, so comparing it against a full-sample score
    would mix two different periods.
    """
    fut_vol = realised_vol(returns, horizon).shift(-horizon)  # realised vol over the NEXT horizon
    hv_filt = fit.high_vol_filtered()
    hv_smooth = fit.smoothed.iloc[:, -1]

    joined = pd.concat(
        {"fut_vol": fut_vol, "filt": hv_filt, "smooth": hv_smooth}, axis=1
    ).dropna()
    if index is not None:
        joined = joined.loc[joined.index.intersection(index)]

    return OOSResult(
        corr_filtered=float(joined["filt"].corr(joined["fut_vol"])),
        corr_smoothed=float(joined["smooth"].corr(joined["fut_vol"])),
        horizon=horizon,
        n=len(joined),
    )


def compare_vol_predictors(predictors: dict[str, pd.Series], returns: pd.Series, *,
                           horizon: int = 21) -> pd.DataFrame:
    """Score several causal predictors of next-``horizon``-day realised vol on their common dates.

    This is the baseline test a regime model has to pass: a high-vol probability is only worth
    having if it tells you more about future vol than trailing vol already does. Every predictor is
    scored on the same dates, with Pearson and Spearman correlation (a probability is bounded and
    realised vol is skewed, so the rank measure is the fairer one for the regime model).
    """
    fut_vol = realised_vol(returns, horizon).shift(-horizon)
    joined = pd.concat({"fut_vol": fut_vol, **predictors}, axis=1, sort=True).dropna()
    rows = {
        name: {
            "pearson": float(joined[name].corr(joined["fut_vol"])),
            "spearman": float(joined[name].corr(joined["fut_vol"], method="spearman")),
        }
        for name in predictors
    }
    out = pd.DataFrame(rows).T
    out["n"] = len(joined)
    return out


def incremental_r2(target: pd.Series, base: pd.Series, extra: pd.Series) -> tuple[float, float]:
    """In-sample R^2 of ``target ~ base`` and of ``target ~ base + extra`` on their common dates.

    A descriptive measure of how much ``extra`` adds once ``base`` is known, not a forecast test.
    """
    joined = pd.concat({"y": target, "b": base, "x": extra}, axis=1, sort=True).dropna()
    y = joined["y"].to_numpy()
    tss = float(((y - y.mean()) ** 2).sum())

    def _r2(cols: list[str]) -> float:
        X = np.column_stack([np.ones(len(joined))] + [joined[c].to_numpy() for c in cols])
        beta = np.linalg.lstsq(X, y, rcond=None)[0]
        return 1.0 - float(((y - X @ beta) ** 2).sum()) / tss

    return _r2(["b"]), _r2(["b", "x"])


def train_test_split_series(returns: pd.Series, train_frac: float = 0.7) -> tuple[pd.Series, pd.Series]:
    """Chronological split — never shuffle a time series."""
    cut = int(len(returns) * train_frac)
    return returns.iloc[:cut], returns.iloc[cut:]


@dataclass
class WalkForwardResult:
    """Outcome of a walk-forward, out-of-sample regime evaluation.

    Attributes
    ----------
    high_vol_prob : Series
        Causal filtered P(high-vol regime) on the out-of-sample span. Each value used only returns up
        to its own date AND parameters estimated only on data strictly before its train window edge.
        This is the honest, leak-free regime signal.
    corr : float
        Correlation between ``high_vol_prob`` and next-``horizon``-day realised volatility, on the OOS
        span only.
    n : int
        Number of OOS observations entering the correlation.
    n_refits : int
        How many times parameters were re-estimated.
    n_skipped : int
        Refit windows whose fit failed and were skipped (leaves a gap; surfaced, never silent).
    implied_vol : Series
        The model's own forecast of daily volatility (percent) over the next ``horizon`` days: the
        filtered state probabilities propagated through the transition matrix, averaged over the
        horizon, weighted against the state variances, then square-rooted. Same dates and same
        causality as ``high_vol_prob``. This is the like-for-like comparison with a vol estimate; the
        raw probability is bounded in [0, 1] and saturates, which handicaps it on a linear measure.
    """

    high_vol_prob: pd.Series
    corr: float
    n: int
    n_refits: int
    n_skipped: int
    implied_vol: pd.Series | None = None
    convergence: pd.DataFrame | None = None  # per refit: best_converged (statsmodels flag), detail


def series_sha256(y: pd.Series) -> str:
    """sha256 of a series' dates and float64 values, so a checkpoint is tied to the data it was made
    from and not only to its span. A revised print inside the span changes the hash."""
    import hashlib
    h = hashlib.sha256()
    h.update("\n".join(str(i) for i in y.index).encode("utf-8"))
    h.update(np.ascontiguousarray(y.to_numpy(dtype=float)).tobytes())
    return h.hexdigest()


def walk_forward_oos(
    returns: pd.Series,
    *,
    n_regimes: int = 2,
    min_train: int = 750,
    step: int = 21,
    horizon: int = 21,
    order_by: str = "variance",
    checkpoint_dir: str | Path | None = None,
) -> WalkForwardResult:
    """Expanding-window walk-forward with frozen-parameter forward filtering.

    This is the version that removes the full-sample-parameter leak that ``oos_realised_vol_check``
    still carries. The protocol, at each refit edge ``i`` (starting at ``min_train``):

    1. Fit the switching-variance model on ``returns[:i]`` only (the train window).
    2. Freeze those parameters and *filter* them forward over ``returns[:i+step]``.
    3. Keep the filtered high-vol probabilities on positions ``[i : i+step]`` — the held-out block.
       The filter is a causal forward recursion, so each of those probabilities used returns only up
       to its own date, and parameters estimated only on data before ``i``.
    4. Advance ``i`` by ``step`` and repeat.

    Regimes are ordered canonically by the *train* fit's variances, so "high-vol" means the same
    thing in every block. Refitting every day would be honest too but wasteful; ``step`` (default:
    monthly) mirrors how a desk actually recalibrates.

    Parameters
    ----------
    min_train : int
        Minimum observations before the first out-of-sample block. Needs enough data to identify two
        variance regimes; the default assumes a few years of daily data.
    step : int
        Refit cadence and OOS block length, in trading days.
    horizon : int
        Forward window (days) for the realised-vol target.
    order_by : {"variance", "mean"}
        Which state counts as "high": the higher-variance one (default, for returns) or the
        higher-mean one, for a level series such as a VIX term-structure slope. ``implied_vol`` only
        means anything for return series.
    checkpoint_dir : path, optional
        Save each refit block to this folder as soon as it is computed, and on a rerun load the
        saved blocks instead of refitting them, so a long run that is stopped resumes where it left
        off. The folder records the settings and data span it was made with, and a rerun with
        different ones is refused rather than silently mixed.
    """
    if order_by not in ("variance", "mean"):
        raise ValueError("order_by must be 'variance' or 'mean'")
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression

    y = returns.astype(float)
    n = len(y)
    if min_train >= n:
        raise ValueError(f"min_train={min_train} leaves no out-of-sample data (n={n})")

    oos_pieces: list[pd.Series] = []
    implied_pieces: list[pd.Series] = []
    conv_rows: list[dict] = []
    conv_idx: list = []
    n_refits = 0
    n_skipped = 0

    ckpt = Path(checkpoint_dir) if checkpoint_dir is not None else None
    if ckpt is not None:
        ckpt.mkdir(parents=True, exist_ok=True)
        settings = {"n": n, "first": str(y.index[0]), "last": str(y.index[-1]),
                    "min_train": min_train, "step": step, "horizon": horizon,
                    "n_regimes": n_regimes, "order_by": order_by,
                    "input_sha256": series_sha256(y)}
        sfile = ckpt / "settings.json"
        if sfile.exists():
            saved = json.loads(sfile.read_text(encoding="utf-8"))
            if "input_sha256" not in saved:
                # Written before the input hash existed (October 2026): checked on span and settings
                # only, as before, then upgraded so the next rerun checks the data values too.
                legacy = {k: v for k, v in settings.items() if k != "input_sha256"}
                if saved != legacy:
                    raise ValueError(f"checkpoint {ckpt} was made with different settings or data")
                warnings.warn(f"checkpoint {ckpt} predates input hashing; matched on span and settings only",
                              RuntimeWarning, stacklevel=2)
            elif saved != settings:
                raise ValueError(f"checkpoint {ckpt} was made with different settings or data "
                                 "(span, settings or the input values themselves)")
        sfile.write_text(json.dumps(settings, indent=1), encoding="utf-8")

    for i in range(min_train, n, step):
        end = min(i + step, n)
        block_file = ckpt / f"block_{i:06d}.csv" if ckpt is not None else None
        if block_file is not None and block_file.exists():
            saved = pd.read_csv(block_file, index_col=0, parse_dates=True)
            if saved.empty:  # this refit failed on the earlier run
                n_skipped += 1
            else:
                n_refits += 1
                oos_pieces.append(saved["hv"].set_axis(y.index[i:end]))
                implied_pieces.append(saved["iv"].set_axis(y.index[i:end]))
                conv_rows.append({"best_converged": None, "detail": "loaded from checkpoint"})
                conv_idx.append(y.index[i])
            continue
        train = y.iloc[:i].reset_index(drop=True)
        try:
            train_res = MarkovRegression(
                train, k_regimes=n_regimes, trend="c", switching_variance=True
            ).fit(disp=False)
        except Exception as exc:  # a single bad window must not sink the whole run
            warnings.warn(f"walk-forward fit failed at i={i}: {exc}", RuntimeWarning, stacklevel=2)
            n_skipped += 1
            if block_file is not None:
                pd.DataFrame(columns=["hv", "iv"]).to_csv(block_file)
            continue
        n_refits += 1
        retvals = getattr(train_res, "mle_retvals", None) or {}
        conv_rows.append({"best_converged": bool(retvals.get("converged", False)),
                          "detail": str(retvals.get("warnflag", ""))})
        conv_idx.append(y.index[i])

        # Canonical order from the TRAIN fit's variances (high-vol regime is last).
        train_var = np.asarray(
            train_res.params[[f"sigma2[{k}]" for k in range(n_regimes)]], dtype=float
        )
        key = train_var if order_by == "variance" else np.asarray(
            train_res.params[[f"const[{k}]" for k in range(n_regimes)]], dtype=float)
        high_idx = int(np.argsort(key)[-1])

        # Freeze train params, filter forward over train+block, read only the held-out block.
        ext = y.iloc[:end].reset_index(drop=True)
        filt = MarkovRegression(
            ext, k_regimes=n_regimes, trend="c", switching_variance=True
        ).filter(train_res.params)
        probs = np.asarray(filt.filtered_marginal_probabilities)[i:end]
        oos_pieces.append(pd.Series(probs[:, high_idx], index=y.index[i:end]))

        # statsmodels stores regime_transition[i, j] = P(S_t = i | S_{t-1} = j); transpose to the
        # row-from convention so A @ ... reads "from" on the rows.
        A = np.asarray(train_res.regime_transition)[:, :, 0].T
        w = probs @ horizon_weights(A, horizon)
        implied_pieces.append(pd.Series(np.sqrt(w @ train_var), index=y.index[i:end]))
        if block_file is not None:
            pd.DataFrame({"hv": oos_pieces[-1], "iv": implied_pieces[-1]}).to_csv(block_file)

    if not oos_pieces:
        raise RuntimeError("no out-of-sample blocks were produced (all fits skipped?)")

    # Clip away sub-1e-14 floating overshoot: statsmodels' filtered marginals sum to 1 but individual
    # entries can round a hair outside [0, 1]. They are probabilities; keep them in range.
    hv_prob = pd.concat(oos_pieces).sort_index().clip(0.0, 1.0)
    hv_prob.name = "high_vol_prob_oos"

    fut_vol = realised_vol(y, horizon).shift(-horizon)
    joined = pd.concat({"hv": hv_prob, "fut_vol": fut_vol}, axis=1, sort=True).dropna()

    return WalkForwardResult(
        high_vol_prob=hv_prob,
        corr=float(joined["hv"].corr(joined["fut_vol"])),
        n=len(joined),
        n_refits=n_refits,
        n_skipped=n_skipped,
        implied_vol=pd.concat(implied_pieces).sort_index().rename("hmm_implied_vol"),
        convergence=pd.DataFrame(conv_rows, index=pd.DatetimeIndex(conv_idx)),
    )


def horizon_weights(A: np.ndarray, horizon: int) -> np.ndarray:
    """Average of A^1 .. A^horizon for a row-stochastic ``A`` (rows = from-state).

    Maps today's filtered state probabilities to the average state probabilities over the next
    ``horizon`` days.
    """
    acc = np.zeros_like(A, dtype=float)
    P = np.eye(len(A))
    for _ in range(horizon):
        P = P @ A
        acc += P
    return acc / horizon
