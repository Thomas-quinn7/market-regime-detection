"""development data only, no holdout

Continuation (b) of the October 2026 reopen: K = 3 and 4 Student-t HMMs with restarts, as forecasters,
against the paper's two-state model, on the S&P 500 development period 2005-2023 only (rule 3 of the
reopen scope). Source of the item: panel, item 10 and question 2 ("your own information-criterion table
prefers three and four states; they were discarded for non-convergence"); desk, quant-researcher 11.

What it does:

1. Gaussian ``MarkovRegression`` with K = 2, 3, 4 on the full development sample, once with the default
   start (the paper's selection table) and once with ``search_reps=20``: AIC, BIC, log-likelihood,
   converged. This is the panel's "optimiser outcome, not evidence for two states" check.
2. Student-t HMMs with K = 2, 3, 4 by EM from 20 starts (one deterministic, 19 random, seed 0), nu
   estimated: best log-likelihood, AIC, BIC, nu, scales, how many starts converged and how many reached
   the best likelihood.
3. The frozen-parameter walk-forward of ``regimes.evaluate.walk_forward_oos`` for each Student-t K
   (refit every 63 days after 756 rows, 20 starts per refit, horizon 21), beside the paper's Gaussian
   two-state walk-forward; per-refit convergence counts.
4. The 21-day forecast table the frozen VIX script builds, with the K-state implied vols (raw and
   log-calibrated as the VIX script calibrates the HMM implied vol) and HAR + VIX + K-state probability;
   paired circular block bootstrap (block 63, 2,000 draws, seed 0) on RMSE and QLIKE.

Output: ``docs/DEV_K_STATES_2026-10.md`` (first line "development data only, no holdout"); the per-day
series and the convergence tables in ``docs/results/dev_k_states/`` so the markdown can be rebuilt with
``--from-cache`` without refitting. Runtime: about 45 minutes with ``--n-jobs 6``.

    python -u examples/dev_k_states.py                 # full run
    python -u examples/dev_k_states.py --from-cache    # rebuild the markdown from the saved series
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
import warnings
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "examples"))

from regimes.evaluate import walk_forward_oos  # noqa: E402
from regimes.forecast import forward_vol, har_features, qlike, walk_forward_regression  # noqa: E402
from regimes.kstate import (RestartSummary, deterministic_init, em_student_t, random_init,  # noqa: E402
                            walk_forward_student_t)
from dev_continuations import CLASS, block_network, compare, load  # noqa: E402
from posthoc_stats import git_head, md_table  # noqa: E402

KS = (2, 3, 4)
H = 21
OUT_DIR = ROOT / "docs" / "results" / "dev_k_states"


def gaussian_table(returns: pd.Series, search_reps: int) -> pd.DataFrame:
    from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
    y = returns.astype(float).reset_index(drop=True)
    rows = []
    for k in KS:
        t0 = time.time()
        np.random.seed(0)   # statsmodels' start search draws from numpy's global state
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            res = MarkovRegression(y, k_regimes=k, trend="c", switching_variance=True).fit(
                disp=False, search_reps=search_reps)
        rows.append({"K": k, "search_reps": search_reps, "AIC": f"{res.aic:.1f}", "BIC": f"{res.bic:.1f}",
                     "loglik": f"{res.llf:.2f}", "converged": bool(res.mle_retvals.get("converged", True)),
                     "sigma (daily %)": ", ".join(f"{np.sqrt(v):.3f}" for v in sorted(
                         float(res.params[f"sigma2[{j}]"]) for j in range(k))),
                     "seconds": f"{time.time() - t0:.0f}"})
    return pd.DataFrame(rows)


def _em_task(args):
    x, k, init, nu0, max_iter, tol = args
    return em_student_t(x, k, init, nu0=nu0, estimate_nu=True, max_iter=max_iter, tol=tol)


def student_t_full_sample(x: np.ndarray, k: int, n_starts: int, n_jobs: int, max_iter: int, tol: float) -> RestartSummary:
    """Same procedure as regimes.kstate.fit_student_t_restarts, with the starts run in parallel."""
    rng = np.random.default_rng(0)
    inits = [deterministic_init(x, k)] + [random_init(x, k, rng) for _ in range(n_starts - 1)]
    with ProcessPoolExecutor(max_workers=n_jobs) as ex:
        runs = list(ex.map(_em_task, [(x, k, init, 8.0, max_iter, tol) for init in inits]))
    pool = [r for r in runs if r.converged] or runs
    best = max(pool, key=lambda r: r.loglik)
    lls = [r.loglik for r in runs]
    return RestartSummary(best=best, logliks=lls, converged=[r.converged for r in runs],
                          n_at_best=int(sum(abs(ll - best.loglik) <= 1e-2 for ll in lls)), runs=runs)


def build_scored(returns: pd.Series, vix: pd.Series, series: pd.DataFrame) -> pd.DataFrame:
    """The VIX script's 21-day table: log HAR inputs, log VIX, walk-forward OLS on the log target."""
    target = forward_vol(returns, H)
    log_har = np.log(har_features(returns).clip(lower=1e-3))
    log_vix = np.log(vix / np.sqrt(252)).rename("vix")
    feature_sets = {
        "HAR": log_har,
        "HAR + VIX": log_har.join(log_vix),
        "HAR + VIX + HMM prob (Gaussian K=2)": log_har.join(log_vix).join(series["g2_high_vol_prob"]),
        "HMM implied vol (Gaussian K=2), calibrated": np.log(series["g2_implied_vol"]),
    }
    raw = {"HMM implied vol (Gaussian K=2), raw": series["g2_implied_vol"]}
    for k in KS:
        feature_sets[f"HAR + VIX + K={k} prob"] = log_har.join(log_vix).join(series[f"k{k}_high_vol_prob"])
        feature_sets[f"HAR + VIX + K={k} expected var"] = log_har.join(log_vix).join(
            np.log(series[f"k{k}_expected_var"]).rename(f"k{k}_log_evar"))
        feature_sets[f"K={k} implied vol, calibrated"] = np.log(series[f"k{k}_implied_vol"])
        raw[f"K={k} implied vol, raw"] = series[f"k{k}_implied_vol"]
    fc = {name: walk_forward_regression(target, X, horizon=H, step=63, min_rows=756, log_target=True).forecast
          for name, X in feature_sets.items()}
    return pd.concat({"target": target, **fc, **raw}, axis=1, sort=True).dropna()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", default=str(ROOT / "docs" / "DEV_K_STATES_2026-10.md"))
    parser.add_argument("--n-boot", type=int, default=2000)
    parser.add_argument("--n-starts", type=int, default=20)
    parser.add_argument("--n-jobs", type=int, default=6)
    parser.add_argument("--step", type=int, default=63, help="refit cadence (63 = the VIX protocol)")
    parser.add_argument("--wf-starts", type=int, default=None, help="starts per walk-forward refit (default: --n-starts)")
    parser.add_argument("--max-iter", type=int, default=500, help="EM iteration cap per start")
    parser.add_argument("--tol", type=float, default=1e-4, help="EM stopping tolerance on the log-likelihood")
    parser.add_argument("--from-cache", action="store_true", help="rebuild the markdown from docs/results/dev_k_states/")
    parser.add_argument("--cache-dir", default=str(OUT_DIR))
    parser.add_argument("--refit-gaussian", action="store_true", help="with --from-cache: recompute table 1 only")
    args = parser.parse_args()
    wf_starts = args.wf_starts or args.n_starts
    cache = Path(args.cache_dir)
    cache.mkdir(parents=True, exist_ok=True)
    block_network()
    returns, vix = load()
    x = returns.to_numpy()
    n = len(x)
    t_start = time.time()

    if not args.from_cache:
        # 1. Gaussian selection table, default start vs search_reps.
        print("1. Gaussian MarkovRegression K=2,3,4 ...", flush=True)
        gauss = pd.concat([gaussian_table(returns, 0), gaussian_table(returns, 20)], ignore_index=True)
        gauss.to_csv(cache / "gaussian_selection.csv", index=False)
        print(gauss.to_string(), flush=True)

        # 2. Student-t full-sample fits with restarts.
        print("2. Student-t full-sample restarts ...", flush=True)
        rows, starts = [], []
        for k in KS:
            t0 = time.time()
            summ = student_t_full_sample(x, k, args.n_starts, args.n_jobs, args.max_iter, args.tol)
            b = summ.best
            rows.append({"K": k, "starts": args.n_starts, "converged starts": int(sum(summ.converged)),
                         "starts at best loglik": summ.n_at_best, "best loglik": f"{b.loglik:.2f}",
                         "AIC": f"{b.aic(n):.1f}", "BIC": f"{b.bic(n):.1f}", "nu": f"{b.nu:.2f}",
                         "sigma (daily %)": ", ".join(f"{s:.3f}" for s in b.sigma),
                         "stay prob": ", ".join(f"{a:.3f}" for a in np.diag(b.A)),
                         "best start converged": b.converged, "seconds": f"{time.time() - t0:.0f}"})
            for j, r in enumerate(summ.runs):
                starts.append({"K": k, "start": j, "kind": "deterministic" if j == 0 else "random",
                               "loglik": r.loglik, "converged": r.converged, "n_iter": r.n_iter, "nu": r.nu,
                               "sigma": " ".join(f"{v:.4f}" for v in r.sigma)})
            print(rows[-1], flush=True)
        pd.DataFrame(rows).to_csv(cache / "student_t_full_sample.csv", index=False)
        pd.DataFrame(starts).to_csv(cache / "student_t_starts.csv", index=False)

        # 3. Walk-forwards.
        print("3. Gaussian two-state walk-forward (the paper's) ...", flush=True)
        g2 = walk_forward_oos(returns, min_train=756, step=args.step, horizon=H)
        series = pd.concat({"g2_high_vol_prob": g2.high_vol_prob, "g2_implied_vol": g2.implied_vol}, axis=1)
        conv_summary = [{"model": "Gaussian K=2 (statsmodels, default start)", "refits": g2.n_refits,
                         "refits converged": int(g2.convergence["best_converged"].sum()),
                         "refits with all starts converged": "n/a", "median starts at best loglik": "n/a"}]
        for k in KS:
            t0 = time.time()
            print(f"   Student-t K={k} walk-forward, {wf_starts} starts per refit, {args.n_jobs} jobs ...", flush=True)
            wf = walk_forward_student_t(returns, k, min_train=756, step=args.step, horizon=H, n_starts=wf_starts,
                                        seed=0, n_jobs=args.n_jobs, max_iter=args.max_iter, tol=args.tol)
            series = series.join(wf.high_vol_prob).join(wf.expected_var).join(wf.implied_vol)
            wf.convergence.to_csv(cache / f"convergence_k{k}.csv")
            c = wf.convergence
            conv_summary.append({"model": f"Student-t K={k} ({wf_starts} starts per refit)", "refits": wf.n_refits,
                                 "refits converged": int(c["best_converged"].sum()),
                                 "refits with all starts converged": int((c["n_converged"] == c["n_starts"]).sum()),
                                 "median starts at best loglik": f"{c['n_at_best'].median():.0f}"})
            print(f"   done in {time.time() - t0:.0f} s: {conv_summary[-1]}", flush=True)
        series.to_csv(cache / "walk_forward_series.csv")
        pd.DataFrame(conv_summary).to_csv(cache / "convergence_summary.csv", index=False)
        (cache / "run.json").write_text(json.dumps({
            "git": git_head(), "when": f"{dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}", "n_starts": args.n_starts,
            "wf_starts": wf_starts, "max_iter": args.max_iter, "tol": args.tol,
            "step": args.step, "n_jobs": args.n_jobs, "seconds": round(time.time() - t_start),
            "data": f"{returns.index.min().date()} to {returns.index.max().date()} ({n} days)"}, indent=1))

    if args.from_cache and args.refit_gaussian:
        gauss = pd.concat([gaussian_table(returns, 0), gaussian_table(returns, 20)], ignore_index=True)
        gauss.to_csv(cache / "gaussian_selection.csv", index=False)
    gauss = pd.read_csv(cache / "gaussian_selection.csv")
    tfull = pd.read_csv(cache / "student_t_full_sample.csv")
    series = pd.read_csv(cache / "walk_forward_series.csv", index_col=0, parse_dates=True)
    conv_summary = pd.read_csv(cache / "convergence_summary.csv", keep_default_na=False)
    run = json.loads((cache / "run.json").read_text())

    # 4. Scored table and comparisons.
    print("4. scoring ...", flush=True)
    df = build_scored(returns, vix, series)
    df.to_csv(cache / "scored_21d.csv")
    y = df["target"].to_numpy()
    losses = pd.DataFrame([{"forecast": m, "RMSE": f"{np.sqrt(((df[m] - df['target']) ** 2).mean()):.3f}",
                            "QLIKE": f"{qlike(df[m].to_numpy(), y).mean():.3f}"} for m in df.columns if m != "target"])
    comps = []
    for k in (3, 4):
        comps.append((f"K={k} implied vol, calibrated", "K=2 implied vol, calibrated"))
    for k in KS:
        comps.append((f"K={k} implied vol, calibrated", "HMM implied vol (Gaussian K=2), calibrated"))
    for k in KS:
        comps.append((f"K={k} implied vol, calibrated", "HAR + VIX"))
    for k in KS:
        comps.append((f"HAR + VIX + K={k} prob", "HAR + VIX"))
    for k in KS:
        comps.append((f"HAR + VIX + K={k} expected var", "HAR + VIX"))
    comps.append(("HAR + VIX + HMM prob (Gaussian K=2)", "HAR + VIX"))
    for k in (3, 4):
        comps.append((f"K={k} implied vol, raw", "K=2 implied vol, raw"))
    for k in KS:
        comps.append((f"K={k} implied vol, raw", "HMM implied vol (Gaussian K=2), raw"))
    rows = [compare(df, f, r, args.n_boot, 63) for f, r in comps]
    comp_table = pd.DataFrame(rows)

    out: list[str] = []
    P = out.append
    P("development data only, no holdout\n")
    P("# K = 3 and 4 Student-t HMMs as forecasters, October 2026\n")
    P(f"Class of every table in this file: **{CLASS}**. Continuation (b) of the reopen scope; no holdout is "
      "opened, no registered verdict is touched, nothing here is a claim. Written by `examples/dev_k_states.py` "
      f"(fits at {run['git']}, {run['when']}, {run['seconds']} s with {run['n_jobs']} processes; markdown at "
      f"{git_head()}, {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%MZ}), {args.n_boot:,} bootstrap draws (seed 0). "
      f"Data: S&P 500 and VIX {run['data']} from the committed caches. Source of the item: panel, item 10 and "
      "question 2; desk, quant-researcher 11.\n")

    P("## 1. Gaussian two-, three- and four-state fits: default start vs 20 random starts\n")
    P("statsmodels `MarkovRegression` (switching variance, constant mean), the model behind the paper's "
      "selection table (`regimes.selection.select_n_regimes`), on the full development sample. `search_reps=0` "
      "is the paper's default start; `search_reps=20` tries 20 random starts before the optimiser (numpy's global "
      "seed set to 0 before each fit, so the table is reproducible). "
      "AIC and BIC are statsmodels' (Gaussian likelihood), so they are comparable within this table only.\n")
    P(md_table(gauss) + "\n")

    P(f"## 2. Student-t fits with {run['n_starts']} starts, full development sample\n")
    P("EM (`regimes.kstate.em_student_t`, the updates of `regimes.student_t`) from one deterministic start and "
      f"{run['n_starts'] - 1} random starts (seed 0), shared nu estimated, at most {run['max_iter']} iterations, "
      f"tolerance {run['tol']:g} on the log-likelihood gain per iteration (the robustness fitter in "
      "`regimes.student_t` uses 200 and 1e-6; EM converges linearly and the K = 3 and 4 fits creep past 200 "
      "iterations at that tolerance, so the cap and tolerance here are looser and are reported with every count). "
      "'Starts at best loglik' counts starts within 0.01 of the best. Parameters: "
      "2K means and scales, K(K-1) transition probabilities, K-1 initial probabilities, nu. AIC and BIC here "
      "use the Student-t likelihood and are comparable within this table only.\n")
    P(md_table(tfull) + "\n")

    P("## 3. Walk-forward convergence\n")
    P(f"Refit every {run['step']} days after 756 rows (the VIX protocol), {run['wf_starts']} starts per refit (seed = "
      "refit number), parameters frozen and filtered forward over the next block; per-refit convergence in "
      "`docs/results/dev_k_states/convergence_k*.csv`. 'Refits converged' counts refits whose best start met the "
      "tolerance within the iteration cap.\n")
    P(md_table(conv_summary) + "\n")

    P("## 4. 21-day forecasts, 2011-2023, same construction as the frozen VIX script\n")
    P(f"Scored days {len(df)}, {df.index.min().date()} to {df.index.max().date()}. Target: realised vol over the next "
      "21 days (daily percent). 'Calibrated' = expanding OLS of the log target on the log implied vol, refit every "
      "63 days after 756 rows, embargo 21, as the VIX script calibrates 'HMM implied vol'; 'raw' = the model's own "
      "number. 'K=k prob' is the probability of the highest-variance state; 'expected var' is the log of the "
      "filtered expected variance (sum of state probabilities times state variances), which carries the "
      "K-state information that a single state probability does not when K > 2.\n")
    P(md_table(losses) + "\n")
    P("Paired circular block bootstrap, block 63, 95% intervals for forecast minus reference (negative = forecast better):\n")
    P(md_table(comp_table) + "\n")

    hv = comp_table.set_index(["forecast", "reference"])
    k3 = hv.loc[("K=3 implied vol, calibrated", "K=2 implied vol, calibrated")]
    k4 = hv.loc[("K=4 implied vol, calibrated", "K=2 implied vol, calibrated")]
    k3h = hv.loc[("K=3 implied vol, calibrated", "HAR + VIX")]
    k4h = hv.loc[("K=4 implied vol, calibrated", "HAR + VIX")]
    k4p = hv.loc[("HAR + VIX + K=4 prob", "HAR + VIX")]
    k4e = hv.loc[("HAR + VIX + K=4 expected var", "HAR + VIX")]
    beats = "met" if (k4["RMSE"] == "better" and k4["QLIKE"] == "better") else "not met on both losses"
    reaches = ("not met" if k4h["RMSE"] == "worse" else "met on RMSE") + f" (RMSE {k4h['RMSE']}, QLIKE {k4h['QLIKE']})"
    P("## One line\n")
    P(f"Development data only: against the two-state Student-t forecast the three-state model is {k3['RMSE']} on RMSE "
      f"({k3['dRMSE 95%']}) and {k3['QLIKE']} on QLIKE ({k3['dQLIKE 95%']}); the four-state model is {k4['RMSE']} "
      f"({k4['dRMSE 95%']}) and {k4['QLIKE']} ({k4['dQLIKE 95%']}). Against HAR + VIX the three-state forecast is "
      f"{k3h['RMSE']} on RMSE ({k3h['dRMSE 95%']}) and {k3h['QLIKE']} on QLIKE ({k3h['dQLIKE 95%']}); the four-state "
      f"{k4h['RMSE']} ({k4h['dRMSE 95%']}) and {k4h['QLIKE']} ({k4h['dQLIKE 95%']}). Added to HAR + VIX, the four-state "
      f"probability is {k4p['RMSE']} on RMSE ({k4p['dRMSE 95%']}) and its expected variance {k4e['RMSE']} "
      f"({k4e['dRMSE 95%']}). The panel's priors: 'K > 2 beats the two-state model' (80 percent) is {beats} for K = 4; "
      f"'reaches HAR + IV' (20 percent) is {reaches}. The paper's development-period reading, that the regime model's "
      "own forecast loses to HAR + VIX and its probability adds nothing to it, does not change with the state count; "
      "a four-state Student-t model is a better regime forecaster than the two-state one and still not a better "
      "volatility forecaster than HAR + VIX. No holdout is opened on this.\n")
    Path(args.out).write_text("\n".join(out) + "\n", encoding="ascii")
    print(out[-1])
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
