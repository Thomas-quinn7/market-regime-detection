"""Development data only, no holdout: desk checks on the VIX script's development-period forecasts.

Two desk statistics the trader lane asked for (desk, trader section 2, items [A2] and [A4]) on the
paper's own development forecasts (S&P 500, 2005-2023, the ``dev`` period of
``examples/vol_forecast_vix.py``):

1. Mincer-Zarnowitz: realised 21-day vol regressed on each forecast, HAC (lag 20) standard errors,
   the joint test of intercept 0 and slope 1, and the slope on the top-decile forecast days.
2. Variance-swap sign test: strike = raw VIX squared in daily-percent units, payoff = realised^2 -
   strike, trade = sign(forecast^2 - strike); share of days long, P&L and hit rate against
   always-short, on every scored day and on non-overlapping 21-day windows.

Step 1 runs the frozen script's ``--period dev`` under the recorder of ``examples/reproduce_holdout.py``
(network blocked, every regression forecast, walk-forward and scored table saved) into
``docs/results/dev_vix_forecasts/``. That folder is development data only: not a holdout and not a
reproduction of one. Step 2 computes the tables from the saved ``scored/`` files, writes them as CSV
beside them and prints them as markdown. ``examples/allocation_lag.py`` includes the same tables in
``docs/ALLOCATION_LAG_2026-10.md``.

    python examples/dev_forecast_desk.py            # reuse the saved forecasts if present
    python examples/dev_forecast_desk.py --rerun    # re-run the frozen script first
"""
from __future__ import annotations

import argparse
import contextlib
import importlib
import io
import json
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "examples"))
OUT = REPO / "docs" / "results" / "dev_vix_forecasts"
H = 21
CLASS = "development data only (S&P 500 2005-2023, the VIX script's dev period); not a holdout, not a reproduction"

MZ_MODELS = ["HAR", "VIX", "HAR + VIX", "HAR + HMM prob", "HAR + VIX + HMM prob", "HAR + VIX + VIX-HMM prob",
             "HMM implied vol", "VIX-HMM implied vol", "EWMA vol (0.94)", "trailing 21-day vol",
             "HMM high-vol probability"]
RAW_MODELS = ["VIX", "HMM implied vol", "VIX-HMM implied vol", "EWMA vol (0.94)", "trailing 21-day vol"]


def git_head() -> str:
    try:
        head = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=REPO, capture_output=True,
                              text=True, check=True).stdout.strip()
        dirty = subprocess.run(["git", "status", "--porcelain"], cwd=REPO, capture_output=True,
                               text=True, check=True).stdout.strip()
        return head + (" plus uncommitted files" if dirty else "")
    except Exception:  # noqa: BLE001
        return "unknown"


def dump_dev_forecasts(out: Path = OUT) -> None:
    """Run ``vol_forecast_vix.py --period dev`` under the reproduction recorder and save everything."""
    import reproduce_holdout as rh

    for sub in ("forecasts", "walk_forwards", "scored"):
        (out / sub).mkdir(parents=True, exist_ok=True)
    frozen = REPO / "examples" / "vol_forecast_vix.py"
    header = {
        "class": CLASS,
        "frozen_script": "examples/vol_forecast_vix.py --period dev",
        "wrapper": "examples/dev_forecast_desk.py " + " ".join(sys.argv[1:]),
        "frozen_script_sha256": rh.sha256(frozen),
        "host": socket.gethostname(), "cpus": __import__("os").cpu_count(),
        "git_head": rh.git("rev-parse", "HEAD"), "git_dirty_paths": rh.git("status", "--porcelain").splitlines(),
        "python": sys.version.split()[0],
        "packages": {p: rh._version(p) for p in rh.PACKAGES},
        "started_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    module = importlib.import_module("vol_forecast_vix")
    rec = rh.Recorder(out)
    undo = rh.install_patches(rec)
    buf = io.StringIO()
    t0 = time.perf_counter()
    argv = sys.argv
    sys.argv = [str(frozen), "--period", "dev"]
    try:
        with contextlib.redirect_stdout(rh._Tee(buf, sys.stdout, on_line=rec.saw_line)):
            module.main()
    finally:
        sys.argv = argv
        for owner, attr, original in reversed(undo):
            setattr(owner, attr, original)
    header["wall_clock_seconds"] = round(time.perf_counter() - t0, 1)
    header["finished_utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    header["data_files"] = sorted(rec.files.values(), key=lambda r: r["path"])
    (out / "stdout.txt").write_text(buf.getvalue())
    rec.write()
    counts = rec.convergence_counts()
    header["convergence"] = counts.to_dict("records") if len(counts) else []
    (out / "provenance.json").write_text(json.dumps(header, indent=1))


def load_scored(out: Path = OUT) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(raw signals in vol units with the target, calibrated forecasts with the target), same days."""
    index = json.loads((out / "scored" / "index.json").read_text())
    frames = {entry["file"]: pd.read_csv(out / "scored" / entry["file"], index_col=0, parse_dates=True)
              for entry in index}
    raw = next(df for df in frames.values() if "VIX" in df.columns and "HAR" not in df.columns)
    cal = next(df for df in frames.values() if "HAR + VIX" in df.columns)
    if not raw.index.equals(cal.index):
        raise ValueError("raw and calibrated scored tables are on different days")
    return raw, cal


def mz_table(raw: pd.DataFrame, cal: pd.DataFrame) -> pd.DataFrame:
    from regimes.posthoc import mincer_zarnowitz

    y = cal["target"].to_numpy()
    rows = []
    series = [(f"{m} (calibrated)", cal[m]) for m in MZ_MODELS if m in cal.columns]
    series += [(f"{m} (raw)", raw[m]) for m in RAW_MODELS if m in raw.columns]
    for name, s in series:
        f = s.to_numpy()
        mz = mincer_zarnowitz(f, y, lag=20)
        top = f >= np.quantile(f, 0.9)
        mz_top = mincer_zarnowitz(f[top], y[top], lag=20)
        rows.append({"forecast": name, "n": mz["n"], "intercept": mz["intercept"], "slope": mz["slope"],
                     "HAC se (slope)": mz["se_slope"], "R2": mz["r2"], "p (a=0, b=1)": mz["p_a0_b1"],
                     "top-decile slope": mz_top["slope"], "top-decile mean forecast": float(f[top].mean()),
                     "top-decile mean realised": float(y[top].mean())})
    return pd.DataFrame(rows)


def varswap_table(raw: pd.DataFrame, cal: pd.DataFrame, *, every: int = 1) -> pd.DataFrame:
    from regimes.posthoc import variance_swap_sign_test

    sub = slice(None, None, every)
    y = cal["target"].to_numpy()[sub]
    strike = raw["VIX"].to_numpy()[sub]
    rows = []
    series = [(f"{m} (calibrated)", cal[m]) for m in MZ_MODELS if m in cal.columns
              and m != "HMM high-vol probability"]
    series += [(f"{m} (raw)", raw[m]) for m in RAW_MODELS if m in raw.columns and m != "VIX"]
    for name, s in series:
        r = variance_swap_sign_test(s.to_numpy()[sub], y, strike)
        rows.append({"forecast": name, **r})
    base = rows[0]
    rows.append({"forecast": "always short", "n": base["n"], "share_long": 0.0,
                 "mean_pnl": base["short_mean_pnl"], "hit_rate": base["short_hit_rate"],
                 "short_mean_pnl": base["short_mean_pnl"], "short_hit_rate": base["short_hit_rate"],
                 "long_days_mean_payoff": float("nan"), "long_days_hit_rate": float("nan"),
                 "p_vs_short": float("nan")})
    return pd.DataFrame(rows)


def md_table(df: pd.DataFrame, fmt: dict[str, str]) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, row in df.iterrows():
        cells = []
        for c in cols:
            v = row[c]
            if isinstance(v, float) and np.isnan(v):
                cells.append("")
            elif c in fmt:
                cells.append(format(v, fmt[c]))
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def sections(out: Path = OUT) -> list[str]:
    """Markdown sections (class-headed) for the two desk tables, computed from the saved forecasts."""
    raw, cal = load_scored(out)
    prov = json.loads((out / "provenance.json").read_text())
    days = cal.index
    lines = [f"Class of every table in this section: **{CLASS}**. Forecasts saved by "
             f"`examples/dev_forecast_desk.py` (git {prov['git_head'][:7]}, {prov['finished_utc']}, "
             f"{prov['wall_clock_seconds']} s), which runs the frozen `examples/vol_forecast_vix.py --period dev` "
             f"unchanged; tables computed by the same script at {git_head()}. Scored days: {len(days)}, "
             f"{days.min().date()} to {days.max().date()} (the days every forecast exists on, as in the "
             f"WRITEUP development column). Source of the items: desk, trader section 2 ([A2], [A4]) and "
             f"section 4.", ""]
    mz = mz_table(raw, cal)
    mz.to_csv(out / "desk_mincer_zarnowitz.csv", index=False, float_format="%.6g")
    lines += ["### Mincer-Zarnowitz: realised 21-day vol on each forecast (daily percent)", "",
              "OLS `realised = a + b * forecast` on the scored days; HAC (Bartlett, lag 20) standard error "
              "of the slope; `p (a=0, b=1)` is the joint Wald test. The top-decile columns refit the line on "
              "the 10 percent of days with the highest forecast. Calibrated rows are the walk-forward "
              "log-linear forecasts the paper scores; raw rows are the signals before calibration (the raw "
              "VIX carries the variance risk premium).", "",
              md_table(mz, {"intercept": ".3f", "slope": ".3f", "HAC se (slope)": ".3f", "R2": ".3f",
                            "p (a=0, b=1)": ".3f", "top-decile slope": ".2f", "top-decile mean forecast": ".2f",
                            "top-decile mean realised": ".2f"}), ""]
    vs_all = varswap_table(raw, cal, every=1)
    vs_month = varswap_table(raw, cal, every=H)
    vs_all.to_csv(out / "desk_variance_swap_daily.csv", index=False, float_format="%.6g")
    vs_month.to_csv(out / "desk_variance_swap_21d.csv", index=False, float_format="%.6g")
    fmt = {"share_long": ".3f", "mean_pnl": "+.4f", "hit_rate": ".3f", "short_mean_pnl": "+.4f",
           "short_hit_rate": ".3f", "long_days_mean_payoff": "+.3f", "long_days_hit_rate": ".3f",
           "p_vs_short": ".3f"}
    lines += ["### Variance-swap sign test against the raw VIX strike", "",
              "Strike = raw VIX squared in daily-percent units; payoff to the long side = realised^2 - strike; "
              "the forecast is long when its own variance is above the strike. `mean_pnl` and `hit_rate` are "
              "for trading the forecast's sign; `short_*` for always-short (the variance risk premium); "
              "`long_days_*` describe the payoff to the long side on the days the forecast is long; "
              "`p_vs_short` is the HAC-DM (lag 20) p-value of the forecast's P&L against always-short, blank "
              "when the forecast is never long (its P&L is then always-short's exactly). Units are daily "
              "variance (percent squared).", "",
              f"All {vs_all['n'].iloc[0]} scored days (overlapping 21-day targets):", "",
              md_table(vs_all, fmt), "",
              f"Every 21st scored day ({vs_month['n'].iloc[0]} non-overlapping windows):", "",
              md_table(vs_month, fmt), ""]
    return lines


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--rerun", action="store_true", help="re-run the frozen script even if forecasts exist")
    args = parser.parse_args()
    if args.rerun or not (OUT / "scored" / "index.json").exists():
        print(f"running examples/vol_forecast_vix.py --period dev under the recorder -> {OUT.relative_to(REPO)}")
        dump_dev_forecasts(OUT)
    print("\n".join(sections(OUT)))


if __name__ == "__main__":
    main()
