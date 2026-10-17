"""Reproduce a spent holdout and save what the frozen script computes but does not keep.

A reproduction, never a test: the holdouts were each run once and their verdicts stand as committed.
This wrapper imports the frozen holdout script and runs its ``main()`` unchanged; nothing in the
frozen file or in ``src/regimes`` is edited. While it runs it records, without altering any value:

- every per-day forecast from ``walk_forward_regression`` (one CSV per call, with its feature names);
- every table the script scores, as passed to ``forecast_losses``: the named forecasts and the
  target on the scored days (``scored/``, with the asset or period block it belongs to);
- every model walk-forward (HMM, joint VIX-HMM, GJR-GARCH, MSM, MS-GARCH, correlation HMM): the
  per-day series and the per-refit parameter tables;
- convergence of every optimiser call: statsmodels ``mle_retvals["converged"]``, arch
  ``convergence_flag`` and scipy ``success``, one row per call, printed as counts at the end;
- every data file read through ``pandas.read_csv`` with its sha256, size and mtime;
- a provenance header: command, host, git hash and dirty flag, Python and package versions, times.

Network access is blocked (``urllib.request.urlopen`` and ``yfinance.download`` raise), so a missing
cache file stops the run instead of silently downloading something new.

Run from the repo root, one holdout per call:

    python -u examples/reproduce_holdout.py vix_early
    python -u examples/reproduce_holdout.py vix_recent
    python -u examples/reproduce_holdout.py stock_bond
    python -u examples/reproduce_holdout.py cross_index
    python -u examples/reproduce_holdout.py etf             # refits every walk-forward from scratch

Output goes to ``docs/results/reproductions/<holdout>/`` (``--out`` to change it): ``stdout.txt`` is
the frozen script's printed output, byte for byte, and ``compare.txt`` its diff against the
committed reference (the result file for cross_index and etf, the 2026-10-17 reproduction log for
the others, which was checked against the WRITEUP tables).

Two holdout-specific notes. ``etf``: the frozen run cached its walk-forwards in
``data/checkpoints/msgarch_credit/``; a plain rerun would only re-score those files, so this wrapper
points the cache at an empty directory under the output folder and every model is refitted (pass
``--use-checkpoints`` to re-score the frozen checkpoints instead). ``cross_index``: the frozen loader
insists that the licensed Databento bar file exists even though it then reads only the derived RV
cache in ``data/``. If the bar files are not on this machine, the wrapper points ``MARKET_DATA_DIR``
at empty placeholder files so the glob passes; the RV still comes from the committed cache, exactly
as in the frozen run, and the placeholder use is written into the provenance header.
"""
from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib
import io
import json
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from dataclasses import fields, is_dataclass
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "examples"))

REPRO_DIR = REPO / "docs" / "results" / "reproductions"
LOG_2026_10_17 = Path("/opt/hmm-agent/out/repro")  # the laptop-started chain of 2026-10-17

# holdout: (frozen module, argv, committed reference, lines of the reference header to skip)
HOLDOUTS = {
    "vix_early": ("vol_forecast_vix", ["--period", "early"], "logs_2026-10-17/vix_early.log", 0),
    "vix_recent": ("vol_forecast_vix", ["--period", "recent"], "logs_2026-10-17/vix_recent.log", 0),
    "stock_bond": ("stock_bond_holdout", ["--period", "holdout"], "logs_2026-10-17/stock_bond.log", 0),
    "cross_index": ("cross_index_holdout", [], "../cross_index_holdout_2026-10-14.txt", None),
    "etf": ("msgarch_credit_holdout", [], "../msgarch_credit_holdout_2026-10-14.txt", None),
}
PACKAGES = ["numpy", "pandas", "scipy", "statsmodels", "arch", "numba", "yfinance", "hmmlearn"]
WALK_FORWARDS = {  # module: function names whose results are saved
    "regimes.evaluate": ["walk_forward_oos"],
    "regimes.vix_regimes": ["walk_forward_vix_hmm"],
    "regimes.garch": ["walk_forward_gjr"],
    "regimes.msm": ["walk_forward_msm"],
    "regimes.msgarch": ["walk_forward_msgarch"],
    "regimes.correlation": ["walk_forward_corr_regimes"],
}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def file_record(path: Path) -> dict:
    st = path.stat()
    return {"path": str(path.resolve().relative_to(REPO)) if path.resolve().is_relative_to(REPO)
            else str(path), "sha256": sha256(path), "bytes": st.st_size,
            "mtime_utc": datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(timespec="seconds")}


def git(*args: str) -> str:
    return subprocess.run(["git", *args], cwd=REPO, capture_output=True, text=True).stdout.strip()


class Recorder:
    """Collects everything the patched functions see; writes it out at the end."""

    def __init__(self, out: Path):
        self.out = out
        self.files: dict[str, dict] = {}
        self.convergence: list[dict] = []
        self.sm_params: list[dict] = []   # statsmodels Markov-switching parameters, one row per fit
        self.context = ""          # name of the walk-forward currently running, for convergence rows
        self.n_regressions = 0
        self.n_walk_forwards = 0
        self.regression_index: list[dict] = []
        self.block = ""            # last "##### <name>" header the frozen script printed
        self.n_scored = 0
        self.scored_index: list[dict] = []
        self.walk_forward_index: list[dict] = []

    # --- data files -----------------------------------------------------------------------------
    def saw_file(self, path) -> None:
        if isinstance(path, (str, os.PathLike)) and Path(path).is_file():
            key = str(Path(path).resolve())
            if key not in self.files:
                self.files[key] = file_record(Path(path))

    def saw_line(self, line: str) -> None:
        if line.startswith("##### "):
            self.block = line[6:].split(":")[0]

    # --- forecasts ------------------------------------------------------------------------------
    def save_regression(self, features, result) -> None:
        self.n_regressions += 1
        cols = [features.name] if isinstance(features, pd.Series) else list(features.columns)
        name = f"regression_{self.n_regressions:03d}.csv"
        result.forecast.rename("forecast").to_csv(self.out / "forecasts" / name, float_format="%.17g")
        self.regression_index.append({"file": name, "features": cols,
                                      "n": int(result.forecast.notna().sum())})

    def save_scored(self, forecasts: dict, target) -> None:
        """The named forecasts and the target exactly as passed to ``forecast_losses``."""
        self.n_scored += 1
        name = f"scored_{self.n_scored:02d}.csv"
        df = pd.concat({"target": target, **forecasts}, axis=1)
        df.to_csv(self.out / "scored" / name, float_format="%.17g")
        self.scored_index.append({"file": name, "block": self.block, "columns": list(forecasts),
                                  "n": int(len(df))})

    def save_walk_forward(self, func: str, result) -> None:
        self.n_walk_forwards += 1
        stem = f"{func}_{self.n_walk_forwards:03d}"
        saved = []
        if is_dataclass(result):
            for f in fields(result):
                value = getattr(result, f.name)
                if isinstance(value, (pd.Series, pd.DataFrame)):
                    value.to_csv(self.out / "walk_forwards" / f"{stem}__{f.name}.csv", float_format="%.17g")
                    saved.append(f.name)
        entry = {"stem": stem, "function": func, "saved": saved,
                 "n_refits": getattr(result, "n_refits", None)}
        if getattr(result, "convergence", None) is not None:
            from regimes.correlation import convergence_counts
            entry["convergence"] = convergence_counts(result.convergence)
        self.walk_forward_index.append(entry)

    def write(self) -> None:
        pd.DataFrame(self.convergence).to_csv(self.out / "convergence.csv", index=False)
        if self.sm_params:
            pd.DataFrame(self.sm_params).to_csv(self.out / "walk_forwards" / "statsmodels_fit_params.csv",
                                                index=False, float_format="%.17g")
        (self.out / "forecasts" / "index.json").write_text(json.dumps(self.regression_index, indent=1))
        (self.out / "scored" / "index.json").write_text(json.dumps(self.scored_index, indent=1))
        (self.out / "walk_forwards" / "index.json").write_text(json.dumps(self.walk_forward_index,
                                                                          indent=1))

    def convergence_counts(self) -> pd.DataFrame:
        if not self.convergence:
            return pd.DataFrame()
        df = pd.DataFrame(self.convergence)
        return (df.groupby(["walk_forward", "optimiser"])["converged"]
                .agg(calls="size", converged="sum").reset_index()
                .assign(not_converged=lambda d: d["calls"] - d["converged"]))


def install_patches(rec: Recorder) -> list[tuple[object, str, object]]:
    """Wrap functions to record their inputs and outputs. Every wrapper returns the original value."""
    undo: list[tuple[object, str, object]] = []

    def patch(owner, attr, wrapper_factory):
        original = getattr(owner, attr)
        setattr(owner, attr, wrapper_factory(original))
        undo.append((owner, attr, original))

    # Data files.
    def read_csv_factory(original):
        def read_csv(path, *a, **k):
            rec.saw_file(path)
            return original(path, *a, **k)
        return read_csv
    patch(pd, "read_csv", read_csv_factory)

    # No network.
    import urllib.request

    def blocked(_original):
        def raise_(*a, **k):
            raise RuntimeError("reproduce_holdout: network access is blocked (a cache file is missing)")
        return raise_
    patch(urllib.request, "urlopen", blocked)
    with contextlib.suppress(ImportError):
        import yfinance
        patch(yfinance, "download", blocked)

    # Convergence: statsmodels Markov switching, arch, scipy.
    from statsmodels.tsa.regime_switching.markov_switching import MarkovSwitching

    def sm_fit_factory(original):
        def fit(self, *a, **k):
            res = original(self, *a, **k)
            retvals = getattr(res, "mle_retvals", None) or {}
            rec.convergence.append({"walk_forward": rec.context, "optimiser": "statsmodels",
                                    "converged": bool(retvals.get("converged", False)),
                                    "detail": str(retvals.get("warnflag", ""))})
            names = getattr(self, "param_names", None) or [f"p{i}" for i in range(len(res.params))]
            rec.sm_params.append({"walk_forward": rec.context, "fit": len(rec.sm_params) + 1,
                                  "nobs": int(getattr(res, "nobs", 0)), "llf": float(res.llf),
                                  **dict(zip(names, map(float, res.params)))})
            return res
        return fit
    patch(MarkovSwitching, "fit", sm_fit_factory)

    from arch.univariate.base import ARCHModel

    def arch_fit_factory(original):
        def fit(self, *a, **k):
            res = original(self, *a, **k)
            flag = getattr(res, "convergence_flag", None)
            rec.convergence.append({"walk_forward": rec.context, "optimiser": "arch",
                                    "converged": flag == 0, "detail": str(flag)})
            return res
        return fit
    patch(ARCHModel, "fit", arch_fit_factory)

    def minimize_factory(original):
        def minimize(*a, **k):
            res = original(*a, **k)
            rec.convergence.append({"walk_forward": rec.context, "optimiser": "scipy",
                                    "converged": bool(res.success), "detail": str(res.message)[:60]})
            return res
        return minimize
    for mod in ("regimes.msm", "regimes.msgarch"):
        patch(importlib.import_module(mod), "minimize", minimize_factory)

    # Walk-forwards and regressions, in every namespace that imported them by name.
    import regimes.forecast as forecast_mod

    def regression_factory(original):
        def walk_forward_regression(target, features, *a, **k):
            res = original(target, features, *a, **k)
            rec.save_regression(features, res)
            return res
        return walk_forward_regression

    def losses_factory(original):
        def forecast_losses(forecasts, target, *a, **k):
            rec.save_scored(forecasts, target)
            return original(forecasts, target, *a, **k)
        return forecast_losses

    targets = [(forecast_mod, "walk_forward_regression", regression_factory),
               (forecast_mod, "forecast_losses", losses_factory)]
    for mod, names in WALK_FORWARDS.items():
        for name in names:
            def wf_factory(original, name=name):
                def wrapped(*a, **k):
                    previous, rec.context = rec.context, name
                    try:
                        res = original(*a, **k)
                    finally:
                        rec.context = previous
                    rec.save_walk_forward(name, res)
                    return res
                return wrapped
            targets.append((importlib.import_module(mod), name, wf_factory))

    originals = {id(getattr(owner, attr)): (attr, factory) for owner, attr, factory in targets}
    wrapped_cache: dict[int, object] = {}
    for module in list(sys.modules.values()):
        name = getattr(module, "__name__", "") or ""
        if not (name.startswith("regimes") or name in {m for m, *_ in HOLDOUTS.values()}
                or name in {"better_vol_models", "msgarch_credit", "cross_index_holdout"}):
            continue
        for attr, value in list(vars(module).items()):
            hit = originals.get(id(value))
            if hit is None or attr != hit[0]:
                continue
            if id(value) not in wrapped_cache:
                wrapped_cache[id(value)] = hit[1](value)
            setattr(module, attr, wrapped_cache[id(value)])
            undo.append((module, attr, value))
    return undo


def placeholder_bars(tmp: Path) -> None:
    """Empty files with the names the cross-index loader globs for (the RV comes from data/)."""
    for rel in ("R2/placeholder/PLACEHOLDER_EMPTY.ohlcv-1m.NQ.v.0.dbn.zst",
                "R2/placeholder/PLACEHOLDER_EMPTY.ohlcv-1m.YM.v.0.dbn.zst",
                "R4/placeholder/PLACEHOLDER_EMPTY.ohlcv-1m.dbn.zst"):
        (tmp / rel).parent.mkdir(parents=True, exist_ok=True)
        (tmp / rel).touch()


def compare_checkpoints(refit_dir: Path) -> dict:
    """Byte and value comparison of refitted walk-forward files with the frozen run's checkpoints."""
    frozen_dir = REPO / "data" / "checkpoints" / "msgarch_credit"
    result = {}
    for path in sorted(refit_dir.glob("*.csv")):
        frozen = frozen_dir / path.name
        if not frozen.exists():
            result[path.name] = "no frozen checkpoint"
            continue
        if sha256(path) == sha256(frozen):
            result[path.name] = "byte-identical"
            continue
        a = pd.read_csv(path, index_col=0)
        b = pd.read_csv(frozen, index_col=0)
        same_shape = a.shape == b.shape and list(a.columns) == list(b.columns)
        gap = float((a - b).abs().max().max()) if same_shape else float("nan")
        result[path.name] = f"differs, max abs difference {gap:.3g}" if same_shape else "differs in shape"
    return result


def reference_lines(holdout: str, out_root: Path) -> list[str] | None:
    module, _, ref, skip = HOLDOUTS[holdout]
    path = (out_root / ref).resolve()
    if not path.exists():
        return None
    lines = path.read_text().splitlines()
    if skip is None:  # result files open with "# ..." provenance lines added by hand
        while lines and lines[0].startswith("#"):
            lines.pop(0)
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("holdout", choices=sorted(HOLDOUTS))
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--use-checkpoints", action="store_true",
                        help="etf only: re-score the frozen run's walk-forward checkpoints")
    args = parser.parse_args()
    module_name, argv, _, _ = HOLDOUTS[args.holdout]
    out = (args.out or REPRO_DIR / args.holdout).resolve()
    for sub in ("forecasts", "walk_forwards", "scored"):
        (out / sub).mkdir(parents=True, exist_ok=True)

    started = datetime.now(timezone.utc)
    header = {
        "class": "reproduction of a spent holdout; not a test",
        "holdout": args.holdout,
        "frozen_script": f"examples/{module_name}.py {' '.join(argv)}".strip(),
        "wrapper": "examples/reproduce_holdout.py " + " ".join(sys.argv[1:]),
        "host": socket.gethostname(), "platform": platform.platform(), "cpus": os.cpu_count(),
        "git_head": git("rev-parse", "HEAD"), "git_dirty_paths": git("status", "--porcelain").splitlines(),
        "python": sys.version.split()[0],
        "packages": {p: _version(p) for p in PACKAGES},
        "started_utc": started.isoformat(timespec="seconds"),
        "notes": [],
    }
    frozen_file = REPO / "examples" / f"{module_name}.py"
    header["frozen_script_sha256"] = sha256(frozen_file)

    tmp = Path(tempfile.mkdtemp(prefix=f"repro_{args.holdout}_"))
    if args.holdout == "cross_index":
        from regimes.intraday import market_data_dir
        if not any(market_data_dir().glob("R2/*/*.ohlcv-1m.NQ.v.0.dbn.zst")):
            placeholder_bars(tmp / "databento")
            os.environ["MARKET_DATA_DIR"] = str(tmp / "databento")
            header["notes"].append("Databento bar files absent on this host: MARKET_DATA_DIR pointed at "
                                   "empty placeholder files; RV read from the committed data/*_rv_5min.csv "
                                   "caches, as cached_daily_rv does whenever the cache exists.")

    module = importlib.import_module(module_name)
    if args.holdout == "etf" and not args.use_checkpoints:
        import msgarch_credit
        msgarch_credit.evaluate_asset.__kwdefaults__["cache_dir"] = tmp / "checkpoints"
        header["notes"].append("walk-forward checkpoints redirected to an empty directory: every HMM, "
                               "GJR-GARCH and MS-GARCH walk-forward refitted from scratch.")

    rec = Recorder(out)
    undo = install_patches(rec)
    buf = io.StringIO()
    t0 = time.perf_counter()
    sys.argv = [str(frozen_file), *argv]
    try:
        with contextlib.redirect_stdout(_Tee(buf, sys.stdout, on_line=rec.saw_line)):
            module.main()
    finally:
        for owner, attr, original in reversed(undo):
            setattr(owner, attr, original)
    header["wall_clock_seconds"] = round(time.perf_counter() - t0, 1)
    header["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    header["data_files"] = sorted(rec.files.values(), key=lambda r: r["path"])
    header["n_regression_forecasts_saved"] = rec.n_regressions
    header["n_walk_forwards_saved"] = rec.n_walk_forwards

    if args.holdout == "etf" and not args.use_checkpoints:
        header["refit_vs_frozen_checkpoints"] = compare_checkpoints(tmp / "checkpoints")
    stdout = buf.getvalue()
    (out / "stdout.txt").write_text(stdout)
    rec.write()
    counts = rec.convergence_counts()
    print("\n##### Convergence (reproduction; counts of optimiser calls)")
    print(counts.to_string(index=False) if len(counts) else "  no optimiser calls recorded")

    ref = reference_lines(args.holdout, out.parent)
    if ref is None:
        verdict = "no reference found"
        diff = []
    else:
        import difflib
        got = stdout.splitlines()
        diff = list(difflib.unified_diff(ref, got, "committed", "reproduction", lineterm="", n=0))
        verdict = "identical" if not diff else f"differs in {sum(l[:1] in '+-' for l in diff[2:])} lines"
    header["compare_verdict"] = verdict
    (out / "compare.txt").write_text(f"{verdict}\n" + "\n".join(diff) + "\n")
    (out / "provenance.json").write_text(json.dumps(header, indent=1))
    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\n##### Comparison with the committed reference: {verdict}")
    print(f"saved to {out.relative_to(REPO) if out.is_relative_to(REPO) else out}")


class _Tee(io.TextIOBase):
    def __init__(self, *streams, on_line=None):
        self.streams = streams
        self.on_line = on_line

    def write(self, s):
        for st in self.streams:
            st.write(s)
        if self.on_line is not None:
            for line in s.splitlines():
                self.on_line(line)
        return len(s)

    def flush(self):
        for st in self.streams:
            st.flush()


def _version(pkg: str) -> str | None:
    try:
        return metadata.version(pkg)
    except metadata.PackageNotFoundError:
        return None


if __name__ == "__main__":
    main()
