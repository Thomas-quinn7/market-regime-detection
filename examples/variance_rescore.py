"""QLIKE scored on a variance forecast instead of the square of a mean-vol forecast (post hoc).

Class: post hoc, computed from the spent holdouts' reproduced forecasts; not a registered test.
Plan: docs/GW_QLIKE_PLAN_2026-11.md, part 1 (committed before this script was run).

Every calibrated forecast in the holdouts is ``exp(fit + s^2/2)`` (``walk_forward_regression`` with
``log_target=True``), the lognormal mean of next-month vol. QLIKE is a loss on variance, so the
forecast it should be given is the lognormal mean of the variance, ``exp(2 fit + 2 s^2)``; squaring the
mean-vol forecast gives ``exp(2 fit + s^2)``, too low by ``exp(s^2)``.

Step 1, capture (one holdout per call; each runs the frozen script unchanged through
examples/reproduce_holdout.py into a scratch folder, so the committed reproductions are untouched):

    python -u examples/variance_rescore.py capture vix_early
    python -u examples/variance_rescore.py capture vix_recent
    python -u examples/variance_rescore.py capture etf          # from the frozen checkpoints
    python -u examples/variance_rescore.py capture cross_index  # about 20 minutes (MSM refits)

Every ``walk_forward_regression`` call is wrapped: a twin repeats the identical fit and returns the
mean-vol forecast (checked equal to the original on every row, else the run stops) and the variance
forecast. The variance forecasts matched to each committed scored table's columns are written to
docs/results/variance_rescore/<holdout>/.

Step 2, score (reads only what step 1 wrote and the committed scored tables):

    python examples/variance_rescore.py score
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

import regimes.forecast as fm  # noqa: E402

REPRO = ROOT / "docs" / "results" / "reproductions"
OUT = ROOT / "docs" / "results" / "variance_rescore"
CLASS = "post hoc, computed from the spent holdouts' reproduced forecasts; not a registered test"
FOLDER = {"vix_early": "vix_early", "vix_recent": "vix_recent", "cross_index": "cross_index",
          "etf": "etf_frozen_checkpoints"}
ORIGINAL = fm.walk_forward_regression
CAPTURED: list[dict] = []
OK = ("exact", "within 1e-9")


def twin(target: pd.Series, features, *, horizon: int = 21, step: int = 63, min_rows: int = 252,
         log_target: bool = False):
    """The same fit as regimes.forecast.walk_forward_regression, line for line, also returning the
    variance forecast and the per-refit residual variance."""
    X_all = features.to_frame() if isinstance(features, pd.Series) else features
    X_all = X_all.dropna()
    y_all = target.reindex(X_all.index)
    X = np.column_stack([np.ones(len(X_all)), X_all.to_numpy(dtype=float)])
    y = y_all.to_numpy(dtype=float)
    if log_target:
        y = np.log(y)
    n = len(X_all)
    means, variances, s2s = [], [], []
    for i in range(min_rows + horizon, n, step):
        end = min(i + step, n)
        tr = slice(0, i - horizon)
        ok = ~np.isnan(y[tr])
        beta = np.linalg.lstsq(X[tr][ok], y[tr][ok], rcond=None)[0]
        pred = X[i:end] @ beta
        resid_var = float(((y[tr][ok] - X[tr][ok] @ beta) ** 2).mean())
        idx = X_all.index[i:end]
        if log_target:
            mean = np.exp(pred + 0.5 * resid_var)
            var = np.exp(2.0 * pred + 2.0 * resid_var)
        else:
            mean = pred
            var = np.maximum(pred, fm._FLOOR) ** 2 + resid_var
        means.append(pd.Series(np.maximum(mean, fm._FLOOR), index=idx))
        variances.append(pd.Series(np.maximum(var, fm._FLOOR ** 2), index=idx))
        s2s.append(resid_var)
    return pd.concat(means), pd.concat(variances), s2s


def wrapper(target, features, *args, **kwargs):
    res = ORIGINAL(target, features, *args, **kwargs)
    if args:
        raise RuntimeError("walk_forward_regression called with extra positional arguments")
    mean, var, s2s = twin(target, features, **kwargs)
    same = mean.index.equals(res.forecast.index) and np.array_equal(mean.to_numpy(), res.forecast.to_numpy())
    if not same:
        raise RuntimeError(f"twin does not reproduce walk_forward_regression (call {len(CAPTURED) + 1})")
    cols = [features.name] if isinstance(features, pd.Series) else list(features.columns)
    CAPTURED.append({"features": cols, "log_target": bool(kwargs.get("log_target", False)),
                     "mean": mean, "var": var, "s2": s2s})
    return res


def install() -> None:
    """Point every loaded name for walk_forward_regression at the wrapper; modules imported later
    (the frozen script) pick it up from regimes.forecast."""
    fm.walk_forward_regression = wrapper
    me = sys.modules[__name__]
    for module in list(sys.modules.values()):
        if module is me:
            continue  # this module's ORIGINAL must keep pointing at the real function
        for attr, value in list(vars(module).items()) if hasattr(module, "__dict__") else []:
            if value is ORIGINAL:
                setattr(module, attr, wrapper)


def load_scored(folder: str) -> list[tuple[str, pd.DataFrame]]:
    index = json.loads((REPRO / folder / "scored" / "index.json").read_text())
    return [(e["block"], pd.read_csv(REPRO / folder / "scored" / e["file"], index_col=0, parse_dates=True))
            for e in index]


def capture(holdout: str) -> None:
    import reproduce_holdout as rh
    install()
    scratch = Path(tempfile.mkdtemp(prefix=f"variance_{holdout}_"))
    argv = ["reproduce_holdout.py", holdout, "--out", str(scratch)]
    if holdout == "etf":
        argv.append("--use-checkpoints")
    saved_argv = sys.argv
    sys.argv = argv
    try:
        rh.main()
    finally:
        sys.argv = saved_argv
    print(f"\ncaptured {len(CAPTURED)} regression calls; every twin forecast equal to the original", flush=True)

    out = OUT / holdout
    out.mkdir(parents=True, exist_ok=True)
    report = {"class": CLASS, "holdout": holdout, "n_calls": len(CAPTURED),
              "level_fits": [c["features"] for c in CAPTURED if not c["log_target"]],
              "scratch_reproduction": str(scratch), "tables": []}
    for t, (block, df) in enumerate(load_scored(FOLDER[holdout]), start=1):
        days = df.index
        var_tab = pd.DataFrame({"target": df["target"]})
        cols = {}
        for col in df.columns.drop("target"):
            hits = [k for k, c in enumerate(CAPTURED)
                    if c["mean"].index.intersection(days).size == days.size
                    and np.array_equal(c["mean"].reindex(days).to_numpy(), df[col].to_numpy())]
            if len(hits) != 1:
                # Fall back to the closest captured forecast, reported with its gap; not used if > 1e-9.
                gaps = [(float(np.nanmax(np.abs(c["mean"].reindex(days).to_numpy() - df[col].to_numpy()))), k)
                        for k, c in enumerate(CAPTURED)]
                gap, k = min(gaps)
                close = sum(g <= 1e-9 for g, _ in gaps)
                cols[col] = {"match": "none exact" if not hits else f"{len(hits)} exact", "closest_gap": gap,
                             "closest_call": k + 1, "features": CAPTURED[k]["features"]}
                if gap <= 1e-9 and close == 1:
                    # Same forecast up to cross-machine floating point (the committed reproductions were
                    # written on another host); a deviation from the plan's "exact", reported as such.
                    c = CAPTURED[k]
                    var_tab[col] = c["var"].reindex(days)
                    cols[col].update({"match": "within 1e-9", "log_target": c["log_target"],
                                      "exp_s2_median": float(np.median(np.exp(c["s2"]))),
                                      "exp_s2_min": float(np.exp(min(c["s2"]))),
                                      "exp_s2_max": float(np.exp(max(c["s2"])))})
                continue
            c = CAPTURED[hits[0]]
            var_tab[col] = c["var"].reindex(days)
            cols[col] = {"match": "exact", "call": hits[0] + 1, "features": c["features"],
                         "log_target": c["log_target"],
                         "exp_s2_median": float(np.median(np.exp(c["s2"]))),
                         "exp_s2_min": float(np.exp(min(c["s2"]))), "exp_s2_max": float(np.exp(max(c["s2"])))}
        name = f"variance_{t:02d}.csv"
        var_tab.to_csv(out / name, float_format="%.12g")
        report["tables"].append({"file": name, "block": block, "n": int(len(df)), "columns": cols})
        n_ok = sum(v["match"] in OK for v in cols.values())
        print(f"table {t} ({block or 'calibrated/raw'}): {n_ok} of {len(cols)} columns matched "
              "(exact or within 1e-9)", flush=True)
    (out / "capture.json").write_text(json.dumps(report, indent=1))
    print(f"written to {out.relative_to(ROOT)}")


# ----------------------------------------------------------------------------------------------
# Step 2

def score(n_boot: int) -> None:
    from cross_index_holdout import claim_verdict
    from posthoc_stats import CROSS_CLAIMS, ETF_CLAIMS, VIX_COMPARISONS, verdict, vix_claim_outcomes
    from regimes.forecast import qlike
    from regimes.posthoc import paired_interval

    def interval(loss_f, loss_b):
        return paired_interval(loss_f, loss_b, statistic="mean", block=63, n_boot=n_boot)

    def rows_for(df: pd.DataFrame, var: pd.DataFrame, name: str, ref: str) -> dict:
        y = df["target"].to_numpy()
        e_f, e_b = df[name].to_numpy() - y, df[ref].to_numpy() - y
        r = {"RMSE": verdict(*paired_interval(e_f, e_b, statistic="rmse", block=63, n_boot=n_boot))}
        lo, hi = interval(qlike(df[name].to_numpy(), y), qlike(df[ref].to_numpy(), y))
        r.update({"Q lo": lo, "Q hi": hi, "QLIKE": verdict(lo, hi)})
        if name in var and ref in var:
            vf, vb = np.sqrt(var[name].to_numpy()), np.sqrt(var[ref].to_numpy())
            lo, hi = interval(qlike(vf, y), qlike(vb, y))
            r.update({"V lo": lo, "V hi": hi, "QLIKE var": verdict(lo, hi),
                      "QLIKE var mean": float(qlike(vf, y).mean()), "QLIKE var ref": float(qlike(vb, y).mean())})
        else:
            r["QLIKE var"] = "not scored (no exact variance match)"
        return r

    lines = ["# QLIKE on variance forecasts: results\n",
             f"Class: **{CLASS}**. Plan: docs/GW_QLIKE_PLAN_2026-11.md part 1. Written by "
             f"`examples/variance_rescore.py score`, {n_boot:,} draws, 63-day circular blocks, seed 0. "
             "'QLIKE' is the convention of docs/POSTHOC_2026-10.md (the squared mean-vol forecast); "
             "'QLIKE var' scores the variance forecast exp(2 fit + 2 s^2).\n"]
    summary = []
    for holdout, claims in (("cross_index", CROSS_CLAIMS), ("etf", ETF_CLAIMS), ("vix_early", None),
                            ("vix_recent", None)):
        cap = json.loads((OUT / holdout / "capture.json").read_text())
        blocks = load_scored(FOLDER[holdout])
        lines.append(f"\n## {holdout}\n")
        lines.append("Size of the bias factor exp(s^2) per forecast (median over refits, first table): " +
                     "; ".join(f"{c} {v['exp_s2_median']:.3f}" for c, v in cap["tables"][-1]["columns"].items()
                               if v.get("match") in OK) + ".\n")
        unmatched = {(t["file"], c): v for t in cap["tables"] for c, v in t["columns"].items() if v.get("match") not in OK}
        if unmatched:
            lines.append("Columns not matched to a captured regression forecast (not variance-scored; in the VIX "
                         "holdouts table 01 is the raw, uncalibrated table, which no claim uses): " +
                         "; ".join(f"{f} {c}: closest gap {v['closest_gap']:.2e}" for (f, c), v in unmatched.items()) + ".\n")
        n_close = sum(v.get("match") == "within 1e-9" for t in cap["tables"] for v in t["columns"].values())
        lines.append(f"Matched columns: {sum(v.get('match') in OK for t in cap['tables'] for v in t['columns'].values())}, "
                     f"of which {n_close} agree with the committed reproduction to within 1e-9 rather than bit for bit "
                     "(the committed reproductions were written on another host; a deviation from the plan's 'exact').\n")
        tab = []
        if claims is not None:
            per = {}
            for (block, df), t in zip(blocks, cap["tables"]):
                var = pd.read_csv(OUT / holdout / t["file"], index_col=0, parse_dates=True)
                for cid, name, ref, expected in claims:
                    r = rows_for(df, var, name, ref)
                    per.setdefault((cid, name, ref, expected), []).append((block, r))
                    tab.append({"claim": cid, "block": block, "forecast vs reference": f"{name} vs {ref}",
                                "RMSE": r["RMSE"], "QLIKE (POSTHOC)": r["QLIKE"],
                                "QLIKE var": r["QLIKE var"],
                                "dQLIKE var 95%": f"{r['V lo']:+.4f} to {r['V hi']:+.4f}" if "V lo" in r else ""})
            out_rows = []
            for (cid, name, ref, expected), rs in per.items():
                o = {k: claim_verdict(expected, [r[k] for _, r in rs]) if all(r[k] in ("better", "worse", "no difference") for _, r in rs)
                     else "not scored" for k in ("RMSE", "QLIKE", "QLIKE var")}
                out_rows.append({"claim": cid, "expected": expected, "RMSE (registered)": o["RMSE"],
                                 "QLIKE (POSTHOC)": o["QLIKE"], "QLIKE var": o["QLIKE var"]})
                if o["QLIKE"] != o["QLIKE var"]:
                    summary.append(f"{holdout} {cid}: {o['QLIKE']} under POSTHOC QLIKE -> {o['QLIKE var']} under QLIKE var")
            lines.append("\n### Claim outcomes\n\n" + pd.DataFrame(out_rows).to_markdown(index=False) + "\n")
        else:
            df = blocks[1][1]
            var = pd.read_csv(OUT / holdout / cap["tables"][1]["file"], index_col=0, parse_dates=True)
            v = {k: {} for k in ("RMSE", "QLIKE", "QLIKE var")}
            for name, ref in VIX_COMPARISONS:
                r = rows_for(df, var, name, ref)
                for k in v:
                    v[k][(name, ref)] = r[k]
                tab.append({"claim": "", "block": holdout, "forecast vs reference": f"{name} vs {ref}",
                            "RMSE": r["RMSE"], "QLIKE (POSTHOC)": r["QLIKE"], "QLIKE var": r["QLIKE var"],
                            "dQLIKE var 95%": f"{r['V lo']:+.4f} to {r['V hi']:+.4f}" if "V lo" in r else ""})
            outs = {k: vix_claim_outcomes(v[k]) for k in v}
            out_rows = [{"claim": c, "RMSE (registered)": outs["RMSE"][c], "QLIKE (POSTHOC)": outs["QLIKE"][c],
                         "QLIKE var": outs["QLIKE var"][c]} for c in outs["RMSE"]]
            for row in out_rows:
                if row["QLIKE (POSTHOC)"] != row["QLIKE var"]:
                    summary.append(f"{holdout} {row['claim']}: {row['QLIKE (POSTHOC)']} -> {row['QLIKE var']}")
            lines.append("\n### Claim outcomes\n\n" + pd.DataFrame(out_rows).to_markdown(index=False) + "\n")
        t = pd.DataFrame(tab)
        changed = t[t["QLIKE (POSTHOC)"] != t["QLIKE var"]]
        lines.append(f"\n### Per-comparison verdicts that differ between the two QLIKE columns ({len(changed)} of {len(t)})\n\n" +
                     (changed.to_markdown(index=False) if len(changed) else "None.") + "\n")
        lines.append("\n### Every comparison\n\n" + t.to_markdown(index=False) + "\n")
    lines.insert(2, "\n## Summary: claim outcomes that change between POSTHOC QLIKE and QLIKE var\n\n" +
                 ("\n".join(f"- {s}" for s in summary) if summary else "- None.") + "\n")
    (OUT / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(summary) if summary else "no claim outcome changes")
    print(f"written to {(OUT / 'RESULTS.md').relative_to(ROOT)}")


def main() -> None:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("capture")
    c.add_argument("holdout", choices=sorted(FOLDER))
    s = sub.add_parser("score")
    s.add_argument("--n-boot", type=int, default=2000)
    a = p.parse_args()
    if a.cmd == "capture":
        capture(a.holdout)
    else:
        score(a.n_boot)


if __name__ == "__main__":
    main()
