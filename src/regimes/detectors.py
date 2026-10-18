"""Alternative regime detectors for the S8 (d) development continuation (October 2026 reopen).

development data only (S&P 500, 2005-2023), no holdout, not a claim.

Each detector is fitted ONLY on a training window and applied forward causally: the label (or
probability) on day t uses inputs up to day t and a model fitted on rows before the refit date, never a
smoothed or two-sided pass. The design is fixed in ``docs/ML_REGIME_PROTOCOL_DRAFT.md`` (amendment A2);
this module is imported by no frozen script.

- ``rolling_features``: the causal inputs (log RMS returns over 5 and 22 days, log VIX / sqrt(252)).
- ``KMeansDetector``, ``GMMDetector``, ``SpectralDetector``: fit on the training rows' features; the
  regime input is the "high-vol" share: for k-means and spectral clustering a 0/1 flag for the cluster
  with the highest mean 22-day RMS return, for the Gaussian mixture the posterior probability of that
  component.
- ``ChangePointDetector``: PELT (``ruptures``) on log 22-day RMS returns; on day t it segments the last
  ``window`` days up to t and flags whether the current segment's mean is above the training median.
- ``walk_forward_detector``: refit every ``step`` rows after ``min_train``; returns the forward series.
- ``persistence`` and ``rand_agreement``: label persistence and adjusted Rand index against the HMM.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

SEED = 0


def rolling_features(returns: pd.Series, vix: pd.Series) -> pd.DataFrame:
    sq = returns.astype(float) ** 2
    return pd.DataFrame({
        "log_rms5": np.log(np.sqrt(sq.rolling(5).mean()).clip(lower=1e-3)),
        "log_rms22": np.log(np.sqrt(sq.rolling(22).mean()).clip(lower=1e-3)),
        "log_vix": np.log(vix / np.sqrt(252)),
    }).dropna()


class _Scaled:
    def _scale_fit(self, X):
        self.mu, self.sd = X.mean(axis=0), X.std(axis=0)
        self.sd[self.sd == 0] = 1.0
        return (X - self.mu) / self.sd

    def _scale(self, X):
        return (X - self.mu) / self.sd


class KMeansDetector(_Scaled):
    def __init__(self, k: int):
        self.k = k

    def fit(self, X: np.ndarray):
        from sklearn.cluster import KMeans
        Z = self._scale_fit(X)
        self.model = KMeans(n_clusters=self.k, n_init=10, random_state=SEED).fit(Z)
        self.high = int(np.argmax(self.model.cluster_centers_[:, 1]))   # column 1 = log_rms22
        return self

    def labels(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(self._scale(X))

    def signal(self, X: np.ndarray) -> np.ndarray:
        return (self.labels(X) == self.high).astype(float)


class GMMDetector(_Scaled):
    def __init__(self, k: int):
        self.k = k

    def fit(self, X: np.ndarray):
        from sklearn.mixture import GaussianMixture
        Z = self._scale_fit(X)
        self.model = GaussianMixture(n_components=self.k, covariance_type="full", n_init=5, random_state=SEED).fit(Z)
        self.high = int(np.argmax(self.model.means_[:, 1]))
        return self

    def labels(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict(self._scale(X))

    def signal(self, X: np.ndarray) -> np.ndarray:
        return self.model.predict_proba(self._scale(X))[:, self.high]


class SpectralDetector(_Scaled):
    """Spectral clustering has no out-of-sample rule, so new days are assigned to the nearest
    training-cluster centroid (in the scaled feature space). Fitted on at most ``max_rows`` of the most
    recent training rows (the affinity matrix is n by n)."""

    def __init__(self, k: int = 2, max_rows: int = 1500):
        self.k, self.max_rows = k, max_rows

    def fit(self, X: np.ndarray):
        from sklearn.cluster import SpectralClustering
        Z = self._scale_fit(X)[-self.max_rows:]
        lab = SpectralClustering(n_clusters=self.k, affinity="nearest_neighbors", n_neighbors=15,
                                 assign_labels="cluster_qr", random_state=SEED).fit_predict(Z)
        self.centroids = np.vstack([Z[lab == c].mean(axis=0) for c in range(self.k)])
        self.high = int(np.argmax(self.centroids[:, 1]))
        return self

    def labels(self, X: np.ndarray) -> np.ndarray:
        Z = self._scale(X)
        return np.argmin(((Z[:, None, :] - self.centroids[None]) ** 2).sum(axis=2), axis=1)

    def signal(self, X: np.ndarray) -> np.ndarray:
        return (self.labels(X) == self.high).astype(float)


class ChangePointDetector:
    """PELT with an L2 cost on log 22-day RMS returns. ``fit`` stores the training median;
    ``signal_at`` segments the ``window`` values ending at each day and flags the last segment."""

    def __init__(self, window: int = 252, penalty: float = 10.0, min_size: int = 10):
        self.window, self.penalty, self.min_size = window, penalty, min_size

    def fit(self, x: np.ndarray):
        self.median = float(np.median(x))
        return self

    def last_segment_mean(self, x: np.ndarray) -> float:
        import ruptures as rpt
        seg = x[-self.window:]
        bkps = rpt.Pelt(model="l2", min_size=self.min_size, jump=1).fit(seg.reshape(-1, 1)).predict(pen=self.penalty)
        start = bkps[-2] if len(bkps) > 1 else 0
        return float(seg[start:].mean())

    def signal_series(self, x_all: np.ndarray, positions: np.ndarray) -> np.ndarray:
        """Flag at each position p, using x_all[: p + 1] only."""
        return np.array([float(self.last_segment_mean(x_all[: p + 1]) > self.median) for p in positions])


def make_detector(name: str):
    kind, _, k = name.partition(" ")
    if kind == "kmeans":
        return KMeansDetector(int(k))
    if kind == "gmm":
        return GMMDetector(int(k))
    if kind == "spectral":
        return SpectralDetector(int(k) if k else 2)
    if kind == "changepoint":
        return ChangePointDetector()
    raise ValueError(f"unknown detector {name!r}")


DETECTORS = ("kmeans 2", "kmeans 3", "gmm 2", "gmm 3", "changepoint", "spectral 2")


def walk_forward_detector(features: pd.DataFrame, name: str, *, min_train: int = 756, step: int = 63) -> pd.DataFrame:
    """Causal forward series of one detector: refit on rows ``[: i]`` at i = min_train, min_train + step,
    ...; ``signal`` and ``label`` for rows ``[i : i + step]`` from that fit. The change-point detector
    has no label (NaN) and its signal at day t uses rows up to t only."""
    X = features.to_numpy(dtype=float)
    n = len(features)
    pieces = []
    for i in range(min_train, n, step):
        end = min(i + step, n)
        det = make_detector(name)
        if name == "changepoint":
            x = X[:, 1]
            det.fit(x[:i])
            sig = det.signal_series(x, np.arange(i, end))
            lab = np.full(end - i, np.nan)
        else:
            det.fit(X[:i])
            sig, lab = det.signal(X[i:end]), det.labels(X[i:end]).astype(float)
        pieces.append(pd.DataFrame({"signal": sig, "label": lab}, index=features.index[i:end]))
    return pd.concat(pieces)


def persistence(labels: pd.Series) -> float:
    """Share of days whose label equals the previous day's (NaN-free labels)."""
    v = labels.dropna().to_numpy()
    return float(np.mean(v[1:] == v[:-1])) if len(v) > 1 else float("nan")


def rand_agreement(a: pd.Series, b: pd.Series) -> float:
    """Adjusted Rand index of two label series on their common non-missing days."""
    from sklearn.metrics import adjusted_rand_score
    j = pd.concat({"a": a, "b": b}, axis=1).dropna()
    return float(adjusted_rand_score(j["a"].astype(int), j["b"].astype(int)))
