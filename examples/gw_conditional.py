"""Giacomini-White conditional predictive ability test, conditioning on the HMM's filtered probability.

Class: post hoc, computed from the spent holdouts' reproduced forecasts; not a registered test.
Plan: docs/GW_QLIKE_PLAN_2026-11.md, part 2 (pairs, instruments, lag, losses and reading rule fixed
before this script was written or run).

For each pair (a forecast against its reference) and each asset or period, ``d_t`` is the loss of the
forecast minus the loss of the reference for the target over (t, t + 21], and the instruments are
``h_t = (1, p_t)`` with ``p_t`` the walk-forward two-state HMM's filtered high-vol probability on the
forecast date. The statistic ``T * Zbar' Omega^-1 Zbar`` with ``Z_t = h_t d_t`` and ``Omega`` the
Bartlett Newey-West covariance with 20 lags (no small-sample correction, the weights of
regimes.posthoc.hac_dm) is compared with chi-squared(2). The OLS fit of ``d_t`` on ``(1, p_t)``, with
the same HAC covariance, gives the loss difference the data imply at p = 0 and at p = 1.

Inputs, all already on disk: the committed scored tables under docs/results/reproductions/, the
saved walk-forward HMM probabilities (cross-index and VIX reproductions; the frozen ETF checkpoints in
data/checkpoints/msgarch_credit/), and for the secondary loss the variance forecasts written by
examples/variance_rescore.py.

    python examples/gw_conditional.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from regimes.forecast import qlike  # noqa: E402
from regimes.posthoc import holm  # noqa: E402


def md(df: pd.DataFrame) -> str:
    """Markdown table without the optional tabulate dependency (floats to 4 significant figures)."""
    cols = list(df.columns)
    out = ["| " + " | ".join(map(str, cols)) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        out.append("| " + " | ".join(f"{v:.4g}" if isinstance(v, float) else str(v) for v in row) + " |")
    return "\n".join(out)

REPRO = ROOT / "docs" / "results" / "reproductions"
VAR = ROOT / "docs" / "results" / "variance_rescore"
OUT = ROOT / "docs" / "results" / "gw_conditional"
CHECKPOINTS = ROOT / "data" / "checkpoints" / "msgarch_credit"
CLASS = "post hoc, computed from the spent holdouts' reproduced forecasts; not a registered test"
LAG = 20

PAIRS = {
    "cross_index": [("G1", "HAR-RV + IV + HMM prob", "HAR-RV + IV"),
                    ("G2", "Two-state HMM implied vol", "HAR-RV + IV")],
    "etf": [("G1", "HAR + IV + MS-GARCH prob", "HAR + IV"),
            ("G2", "Two-state HMM implied vol", "HAR + IV")],
    "vix": [("G1", "HAR + VIX + HMM prob", "HAR + VIX"),
            ("G2", "HMM implied vol", "HAR + VIX")],
}
ETF_SLUGS = {"Crude oil (USO)": "crude_oil_uso", "Gold (GLD)": "gold_gld",
             "Emerging markets (EEM)": "emerging_markets_eem", "Brazil (EWZ)": "brazil_ewz"}


def nw_cov(Z: np.ndarray, lag: int = LAG, kernel: str = "rectangular") -> np.ndarray:
    """Long-run covariance of the rows of Z (centred). ``kernel="rectangular"``: unit weights up to
    ``lag`` (amendment A1); ``"bartlett"``: weights 1 - k/(lag+1), as regimes.posthoc.hac_dm."""
    U = Z - Z.mean(axis=0)
    n = len(U)
    S = U.T @ U / n
    for k in range(1, min(lag, n - 1) + 1):
        G = U[k:].T @ U[:-k] / n
        w = 1.0 if kernel == "rectangular" else 1.0 - k / (lag + 1)
        S += w * (G + G.T)
    return S


def _pd(M: np.ndarray) -> bool:
    return bool(np.linalg.eigvalsh((M + M.T) / 2).min() > 0)


def hac(Z: np.ndarray) -> tuple[np.ndarray, str]:
    """Amendment A1: rectangular 20 lags; Bartlett 63 if that is not positive definite."""
    S = nw_cov(Z, LAG, "rectangular")
    if _pd(S):
        return S, "rectangular 20"
    return nw_cov(Z, 63, "bartlett"), "bartlett 63 (rectangular not positive definite)"


def gw_stat(d: np.ndarray, H: np.ndarray, omega: np.ndarray) -> float:
    zbar = (H * d[:, None]).mean(axis=0)
    return float(len(d) * zbar @ np.linalg.solve(omega, zbar))


def gw_test(d: np.ndarray, p: np.ndarray) -> dict:
    H = np.column_stack([np.ones_like(p), p])
    Z = H * d[:, None]
    n = len(d)
    omega, kernel = hac(Z)
    stat = gw_stat(d, H, omega)
    stat_planned = gw_stat(d, H, nw_cov(Z, LAG, "bartlett"))
    stat_b63 = gw_stat(d, H, nw_cov(Z, 63, "bartlett"))
    # Direction: OLS of d on (1, p) with HAC covariance (X'X)^-1 S (X'X)^-1 / n.
    XtX = H.T @ H / n
    beta = np.linalg.solve(XtX, H.T @ d / n)
    u = d - H @ beta
    S, _ = hac(H * u[:, None])
    V = np.linalg.solve(XtX, np.linalg.solve(XtX, S).T) / n
    at0, se0 = beta[0], np.sqrt(V[0, 0])
    w = np.array([1.0, 1.0])
    at1, se1 = float(w @ beta), float(np.sqrt(w @ V @ w))
    stressed = p >= 0.5
    return {"n": n, "stat": stat, "p": float(stats.chi2.sf(stat, 2)), "kernel": kernel,
            "p (planned Bartlett 20)": float(stats.chi2.sf(stat_planned, 2)),
            "p (Bartlett 63 diagnostic)": float(stats.chi2.sf(stat_b63, 2)), "mean d": float(d.mean()),
            "d at p=0": float(at0), "lo0": float(at0 - 1.96 * se0), "hi0": float(at0 + 1.96 * se0),
            "d at p=1": at1, "lo1": at1 - 1.96 * se1, "hi1": at1 + 1.96 * se1,
            "share p>=0.5": float(stressed.mean()),
            "mean d, p>=0.5": float(d[stressed].mean()) if stressed.any() else float("nan"),
            "mean d, p<0.5": float(d[~stressed].mean()) if (~stressed).any() else float("nan")}


def size_check(n_draws: int = 500, seed: int = 7) -> pd.DataFrame:
    """Rejection rate at 5% under a true null that mimics the holdouts: d a flat MA(20) of Student-t(5)
    shocks (21-day overlapping targets), p a persistent logistic AR(1) independent of d. Synthetic data
    only (amendment A1)."""
    rng = np.random.default_rng(seed)
    rows = []
    for n in (676, 2228, 3300):
        rej = {"rectangular 20 (used)": 0, "Bartlett 20 (planned)": 0}
        for _ in range(n_draws):
            d = np.convolve(rng.standard_t(5, n + 20), np.ones(21) / np.sqrt(21), "valid")[:n]
            x, u = np.zeros(n), rng.standard_normal(n)
            for t in range(1, n):
                x[t] = 0.99 * x[t - 1] + u[t]
            r = gw_test(d, 1 / (1 + np.exp(-3 * x)))
            rej["rectangular 20 (used)"] += r["p"] < 0.05
            rej["Bartlett 20 (planned)"] += r["p (planned Bartlett 20)"] < 0.05
        rows.append({"days": n, **{k: v / n_draws for k, v in rej.items()}})
    return pd.DataFrame(rows)


def dm_note() -> pd.DataFrame:
    """Amendment A1 (iv): the registered-claim pairs' DM tests (POSTHOC's Bartlett 20) beside the
    rectangular 20-lag version, on squared error and QLIKE as POSTHOC computes them."""
    sys.path.insert(0, str(ROOT / "examples"))
    from posthoc_stats import CROSS_CLAIMS, ETF_CLAIMS, VIX_COMPARISONS

    def dm(d: np.ndarray, kernel: str) -> float:
        lrv = float(nw_cov(d[:, None], LAG, kernel)[0, 0])
        if lrv <= 0:
            lrv = float(nw_cov(d[:, None], 63, "bartlett")[0, 0])
        return float(2 * stats.norm.sf(abs(d.mean()) / np.sqrt(lrv / len(d))))

    rows = []
    sets = [("cross_index", "cross_index", [(c, f, r) for c, f, r, _ in CROSS_CLAIMS]),
            ("etf", "etf_frozen_checkpoints", [(c, f, r) for c, f, r, _ in ETF_CLAIMS]),
            ("vix_early", "vix_early", [(str(i + 1), f, r) for i, (f, r) in enumerate(VIX_COMPARISONS)]),
            ("vix_recent", "vix_recent", [(str(i + 1), f, r) for i, (f, r) in enumerate(VIX_COMPARISONS)])]
    for holdout, folder, pairs in sets:
        index = json.loads((REPRO / folder / "scored" / "index.json").read_text())
        tables = index[1:] if holdout.startswith("vix") else index
        for entry in tables:
            df = read_series_frame(REPRO / folder / "scored" / entry["file"])
            y = df["target"].to_numpy()
            for cid, f, r in pairs:
                for loss, fn in (("squared error", lambda a: (a - y) ** 2), ("QLIKE", lambda a: qlike(a, y))):
                    d = fn(df[f].to_numpy()) - fn(df[r].to_numpy())
                    rows.append({"holdout": holdout, "block": entry["block"] or holdout, "claim": cid, "loss": loss,
                                 "p Bartlett 20 (POSTHOC)": dm(d, "bartlett"), "p rectangular 20": dm(d, "rectangular")})
    return pd.DataFrame(rows)


def read_series(path: Path, col: str | None = None) -> pd.Series:
    df = pd.read_csv(path, index_col=0, parse_dates=True)
    return df[col] if col else df.iloc[:, 0]


def blocks() -> list[dict]:
    """[{holdout, block, scored, prob, variance or None, pairs}] for the nine blocks of the plan."""
    out = []
    ci = json.loads((REPRO / "cross_index" / "scored" / "index.json").read_text())
    ci_prob = ["walk_forward_oos_001", "walk_forward_oos_004", "walk_forward_oos_007"]  # saved in block order
    wf_index = json.loads((REPRO / "cross_index" / "walk_forwards" / "index.json").read_text())
    assert [e["stem"] for e in wf_index if e["function"] == "walk_forward_oos"] == ci_prob
    # The order mapping is checked, not assumed: each index's scored HMM forecast must track its own
    # walk-forward implied vol more closely than the other two indices' (on the common days).
    for entry, stem in zip(ci, ci_prob):
        scored = read_series_frame(REPRO / "cross_index" / "scored" / entry["file"])["Two-state HMM implied vol"]
        corr = {s: scored.corr(np.log(read_series(REPRO / "cross_index" / "walk_forwards" / f"{s}__implied_vol.csv")
                                      .reindex(scored.index))) for s in ci_prob}
        assert max(corr, key=corr.get) == stem, (entry["block"], corr)
    for k, (entry, stem) in enumerate(zip(ci, ci_prob), start=1):
        out.append({"holdout": "cross_index", "block": entry["block"],
                    "scored": read_series_frame(REPRO / "cross_index" / "scored" / entry["file"]),
                    "prob": read_series(REPRO / "cross_index" / "walk_forwards" / f"{stem}__high_vol_prob.csv"),
                    "variance": var_frame("cross_index", k), "pairs": PAIRS["cross_index"]})
    etf = json.loads((REPRO / "etf_frozen_checkpoints" / "scored" / "index.json").read_text())
    for k, entry in enumerate(etf, start=1):
        files = [f for f in CHECKPOINTS.glob(f"{ETF_SLUGS[entry['block']]}__hmm__2026-10-12__*.csv")
                 if not f.name.endswith(".params.csv")]
        assert len(files) == 1, files
        out.append({"holdout": "etf", "block": entry["block"],
                    "scored": read_series_frame(REPRO / "etf_frozen_checkpoints" / "scored" / entry["file"]),
                    "prob": read_series(files[0], "high_vol_prob"),
                    "variance": var_frame("etf", k), "pairs": PAIRS["etf"]})
    for folder, label in (("vix_early", "S&P 500, 1996-2004"), ("vix_recent", "S&P 500, 2024-2026")):
        entry = json.loads((REPRO / folder / "scored" / "index.json").read_text())[1]  # the calibrated table
        out.append({"holdout": folder, "block": label,
                    "scored": read_series_frame(REPRO / folder / "scored" / entry["file"]),
                    "prob": read_series(REPRO / folder / "walk_forwards" / "walk_forward_oos_001__high_vol_prob.csv"),
                    "variance": var_frame(folder, 2), "pairs": PAIRS["vix"]})
    return out


def read_series_frame(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, index_col=0, parse_dates=True)


def var_frame(holdout: str, k: int) -> pd.DataFrame | None:
    path = VAR / holdout / f"variance_{k:02d}.csv"
    return pd.read_csv(path, index_col=0, parse_dates=True) if path.exists() else None


def main() -> None:
    rows = []
    for b in blocks():
        df, var = b["scored"], b["variance"]
        p = b["prob"].reindex(df.index)
        if p.isna().any():
            raise RuntimeError(f"{b['block']}: HMM probability missing on {int(p.isna().sum())} scored days")
        y = df["target"].to_numpy()
        for gid, name, ref in b["pairs"]:
            f, r = df[name].to_numpy(), df[ref].to_numpy()
            losses = {"squared error": ((f - y) ** 2, (r - y) ** 2), "QLIKE": (qlike(f, y), qlike(r, y))}
            if var is not None and name in var and ref in var:
                losses["QLIKE var"] = (qlike(np.sqrt(var[name].to_numpy()), y), qlike(np.sqrt(var[ref].to_numpy()), y))
            for loss, (lf, lr) in losses.items():
                g = gw_test(lf - lr, p.to_numpy())
                rows.append({"holdout": b["holdout"], "block": b["block"], "pair": gid,
                             "forecast": name, "reference": ref, "loss": loss, **g})
    res = pd.DataFrame(rows)
    primary = res["loss"].isin(["squared error", "QLIKE"])
    res["family"] = np.where(primary, "primary", "secondary")
    res["Holm p"] = np.nan
    res["Holm reject"] = False
    h = holm(res.loc[primary, "p"].to_numpy())
    res.loc[primary, "Holm p"] = h["adjusted"]
    res.loc[primary, "Holm reject"] = h["reject"]
    hs = res["loss"] == "QLIKE var"
    if hs.any():
        h2 = holm(res.loc[hs, "p"].to_numpy())
        res.loc[hs, "Holm p"] = h2["adjusted"]
        res.loc[hs, "Holm reject"] = h2["reject"]
    res["lead (reading rule)"] = res["Holm reject"] & (res["hi1"] < 0)
    res["against (stress favours reference)"] = res["Holm reject"] & (res["lo1"] > 0)

    OUT.mkdir(parents=True, exist_ok=True)
    res.to_csv(OUT / "gw_conditional.csv", index=False, float_format="%.6g")

    def fmt(r):
        return {"block": r["block"], "pair": r["pair"], "loss": r["loss"], "n": r["n"],
                "GW stat": f"{r['stat']:.2f}", "p": f"{r['p']:.3f}",
                "p, Bartlett 20 (planned, not used)": f"{r['p (planned Bartlett 20)']:.3f}",
                "p, Bartlett 63 (diagnostic)": f"{r['p (Bartlett 63 diagnostic)']:.3f}",
                "Holm p": "" if np.isnan(r["Holm p"]) else f"{r['Holm p']:.3f}",
                "d at p=0 (95%)": f"{r['d at p=0']:+.4f} ({r['lo0']:+.4f}, {r['hi0']:+.4f})",
                "d at p=1 (95%)": f"{r['d at p=1']:+.4f} ({r['lo1']:+.4f}, {r['hi1']:+.4f})",
                "share p>=0.5": f"{r['share p>=0.5']:.2f}",
                "mean d p>=0.5 / p<0.5": f"{r['mean d, p>=0.5']:+.4f} / {r['mean d, p<0.5']:+.4f}"}

    n_primary = int(primary.sum())
    lines = ["# Giacomini-White conditional test: results\n",
             f"Class: **{CLASS}**. Plan: docs/GW_QLIKE_PLAN_2026-11.md part 2. Written by "
             "`examples/gw_conditional.py`. d = loss of the forecast minus loss of the reference (negative "
             "favours the forecast); instruments (1, p_t), p_t the walk-forward HMM high-vol probability on the "
             f"forecast date; HAC long-run covariance with the rectangular kernel, {LAG} lags (amendment A1; "
             "Bartlett 63 if not positive definite); chi-squared(2). The Bartlett 20 p-value (the plan before "
             "A1) and a Bartlett 63 p-value are shown as kernel diagnostics only. Holm at 5% across the "
             f"{n_primary} primary tests (squared error and QLIKE as in POSTHOC); QLIKE on the variance forecast "
             f"is a secondary family of {int(hs.sum())} with its own Holm.\n",
             "Pairs: G1 = the regime term added to the benchmark (HMM probability; MS-GARCH probability on the "
             "ETFs) against the benchmark; G2 = the two-state HMM's own forecast against the benchmark.\n",
             "\n## Summary\n",
             f"- Primary tests rejecting at 5% before Holm: {int((res.loc[primary, 'p'] < 0.05).sum())} of {n_primary}; "
             f"after Holm: {int(res.loc[primary, 'Holm reject'].sum())}.",
             f"- Leads under the plan's reading rule (Holm rejection and the p = 1 interval wholly below zero): "
             f"{int(res.loc[primary, 'lead (reading rule)'].sum())}.",
             f"- Holm rejections where stress favours the reference (p = 1 interval wholly above zero): "
             f"{int(res.loc[primary, 'against (stress favours reference)'].sum())}.",
             f"- Secondary (QLIKE var): {int((res.loc[hs, 'p'] < 0.05).sum())} of {int(hs.sum())} reject before Holm, "
             f"{int(res.loc[hs, 'Holm reject'].sum())} after.\n"]
    fragile = res[res["Holm reject"] & (res["p (Bartlett 63 diagnostic)"] >= 0.05)]
    lines.append("- Holm rejections that do not reject at 5% under the Bartlett 63 diagnostic (kernel-fragile): "
                 f"{len(fragile)}" + (": " + "; ".join(
                     f"{r['block']} {r['pair']} {r['loss']} (Bartlett 63 p = {r['p (Bartlett 63 diagnostic)']:.3f})"
                     for _, r in fragile.iterrows()) if len(fragile) else "") + ".")
    fallback = res[res["kernel"] != "rectangular 20"]
    lines.append(f"- Blocks where the rectangular covariance was not positive definite and Bartlett 63 was used: "
                 f"{len(fallback)} rows" + (": " + "; ".join(f"{r.block} {r.pair} {r.loss}" for r in fallback.itertuples()) if len(fallback) else "") + ".")
    lines.append(f"- With the originally planned Bartlett 20-lag covariance (oversized, see the size check; not "
                 f"used for any reading), {int((res.loc[primary, 'p (planned Bartlett 20)'] < 0.05).sum())} of "
                 f"{n_primary} primary tests would reject at 5% before Holm.\n")
    for fam, mask in (("Primary family", primary), ("Secondary family: QLIKE on the variance forecast", hs)):
        if mask.any():
            lines.append(f"\n## {fam}\n\n" + md(pd.DataFrame([fmt(r) for _, r in res[mask].iterrows()])) + "\n")

    size = size_check()
    size.to_csv(OUT / "size_check.csv", index=False)
    lines.append("\n## Size check (amendment A1; synthetic data only)\n\nRejection rate at a nominal 5% under a "
                 "true null: d a flat MA(20) of Student-t(5) shocks, p a persistent logistic AR(1) independent "
                 "of d, 500 draws per length, seed 7.\n\n" + md(size) + "\n")

    dmn = dm_note()
    dmn.to_csv(OUT / "dm_kernel_note.csv", index=False, float_format="%.6g")
    tab = (dmn.assign(bart=dmn["p Bartlett 20 (POSTHOC)"] < 0.05, rect=dmn["p rectangular 20"] < 0.05)
           .groupby(["holdout", "loss"])[["bart", "rect"]].sum().astype(int).reset_index()
           .rename(columns={"bart": "reject at 5%, Bartlett 20 (POSTHOC)", "rect": "reject at 5%, rectangular 20"}))
    tab["pairs"] = dmn.groupby(["holdout", "loss"]).size().to_numpy()
    lost = dmn[(dmn["p Bartlett 20 (POSTHOC)"] < 0.05) & (dmn["p rectangular 20"] >= 0.05)]
    lines.append("\n## Note on POSTHOC's DM tests (amendment A1 iv; not a change to POSTHOC)\n\nThe same "
                 "Bartlett 20-lag variance is used by the HAC Diebold-Mariano tests in docs/POSTHOC_2026-10.md, so "
                 "they share the size problem above. Rejections at 5% for the registered-claim pairs, per holdout "
                 "and loss:\n\n" + md(tab) + "\n\n" +
                 f"{len(lost)} of {int((dmn['p Bartlett 20 (POSTHOC)'] < 0.05).sum())} Bartlett rejections are not "
                 "rejections under the rectangular kernel. The bootstrap intervals that decide every registered and "
                 "POSTHOC verdict are not affected; only the DM column is.\n")
    (OUT / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[4:9]))
    print(f"written to {(OUT / 'RESULTS.md').relative_to(ROOT)}")


if __name__ == "__main__":
    main()
