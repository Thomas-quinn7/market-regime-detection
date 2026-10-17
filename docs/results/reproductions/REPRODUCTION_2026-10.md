# Reproductions of the four spent holdouts, October 2026

Class: reproduction. Every holdout here was run once, under its frozen protocol, in October 2026,
and its verdicts stand as committed. Re-running a frozen script checks that the committed numbers
come out of the committed code and data; it does not test any claim again.

Two sets of runs:

1. **17 Oct 2026, 14:44-14:57Z, pc-lanes**: the frozen scripts run as plain `nohup` jobs, started
   from the laptop, at `17476b5`. Logs copied unchanged to `logs_2026-10-17/` (`CHAIN.log` has the
   start and exit times).
2. **17 Oct 2026, 19:36-20:45Z, pc-lanes**: every holdout again through `examples/reproduce_holdout.py`,
   which imports the frozen script and runs its `main()` unchanged, blocks the network, and saves
   per-day forecasts, the scored forecast tables with their target (`scored/`), per-refit
   parameters, optimiser convergence and the sha256 of every data file read into the folder named
   after the holdout. The VIX, cross-index and ETF folders were written a second time at 20:22-20:45Z
   to add `scored/`; the second runs printed the same output as the first. Repo at `17476b5` plus the new, uncommitted
   wrapper files; the frozen files matched `/opt/hmm-agent/protected.sha256` before and after.

Per-holdout provenance (command, host, packages, wall clock, every input with sha256 and mtime,
convergence counts, the diff) is in `PROVENANCE_2026-10.md`, written by
`examples/reproduction_report.py`. Every cached input is listed in `data/MANIFEST.md`
(`examples/data_manifest.py`).

## Outcome per holdout

| Holdout | Committed reference | 17 Oct chain (frozen script) | Wrapper run | Outcome |
|---|---|---|---|---|
| VIX 1990-2004 | WRITEUP tables (no result file) | exit 0, 22 s | identical to the chain log | all WRITEUP numbers equal |
| VIX 2024-2026 | WRITEUP tables (no result file) | exit 0, 49 s | identical to the chain log | all WRITEUP numbers equal |
| Stock-bond 1962-2004 | WRITEUP tables (no result file) | exit 0, 11 min 18 s | identical to the chain log | all WRITEUP numbers equal |
| Cross-index (NDX, DJI, RUT) | `docs/results/cross_index_holdout_2026-10-14.txt` | **exit 1**: raw bar files absent on pc-lanes | 3 printed lines differ | **not byte-identical**: every table number equal; the printed last-fit MSM parameter `b` differs in the third decimal on each index |
| ETF (USO, GLD, EEM, EWZ) | `docs/results/msgarch_credit_holdout_2026-10-14.txt` | exit 0, 4 s, **re-scored the frozen run's checkpoints**: identical apart from the "loaded from" lines | full refit: 24 printed lines differ | **not reproduced by a refit**: per-asset verdict labels and the claims table unchanged, but 0 of 20 refitted walk-forward files equal the frozen checkpoints and several losses and interval endpoints move in the third decimal |

Wall-clock times: the chain times come from `CHAIN.log`; the wrapper times are in
`PROVENANCE_2026-10.md`. Wrapper runs overlapped each other on the 8-core box, so they are not
benchmarks.

**VIX and stock-bond.** These have no committed result file; their numbers exist only in WRITEUP
tables. `python examples/check_writeup_tables.py` reads those tables and compares each number with the
wrapper's `stdout.txt` at the printed precision: 52 numbers checked, 0 mismatches (the seven RMSEs per
VIX holdout, the scored-day counts, the claim intervals quoted in the claims table and the 2024-2026
QLIKE interval, and every number in the two stock-bond tables). The original runs were on the laptop
on 13 Oct; these reproductions are on pc-lanes, so the match is across machines.

**Cross-index.** The frozen loader (`cross_index_holdout.py`, `load_index`) requires exactly one
licensed Databento bar file per index before reading the derived RV cache in `data/`, and the bar
files are not on pc-lanes, so the 17 Oct chain run stopped before computing anything. The wrapper
points `MARKET_DATA_DIR` at empty placeholder files with the expected names; `cached_daily_rv` then
returns the committed `data/*_rv_5min.csv` cache without opening the placeholder, which is exactly
what the frozen run did once the caches existed (desk, data-engineer and model-validator: the caches
were first written 53 s to 11 min after the freeze commit, during the frozen run).
The frozen script was also run directly with the same placeholder directory
(`/opt/hmm-agent/out/repro/cross_index_box.log`, 4 min 47 s), and its output is identical to the
wrapper's. Against the committed result file, both differ in exactly these lines:

```
-  last MSM fit: m0 1.504, sigma 1.786, b 3.798, gamma_k 0.054
+  last MSM fit: m0 1.504, sigma 1.786, b 3.795, gamma_k 0.054
-  last MSM fit: m0 1.511, sigma 1.929, b 4.558, gamma_k 0.077
+  last MSM fit: m0 1.511, sigma 1.929, b 4.559, gamma_k 0.077
-  last MSM fit: m0 1.424, sigma 2.233, b 3.046, gamma_k 0.032
+  last MSM fit: m0 1.424, sigma 2.233, b 3.047, gamma_k 0.032
```

Every other line, including every loss, every interval, every per-index verdict and the claims
table, is identical. What is known: the MSM fit (`regimes.msm.fit_msm`, L-BFGS-B with
finite-difference gradients from a grid of starts) gives the same answer twice on pc-lanes, and a
slightly different `b` on the laptop where the holdout ran on 14 Oct; What is not known:
whether the cause is the machine (CPU, BLAS, OS) or something else, and how far the MSM forecasts
move on days the table does not show. Settling it needs the same wrapper run on the laptop, which
has the bar files (`python -u examples/reproduce_holdout.py cross_index`), and a comparison of the
saved MSM forecasts. Until then the saved cross-index MSM forecasts in `cross_index/` are pc-lanes
forecasts, not the frozen run's.

**ETF.** The frozen run on 14 Oct (on pc-lanes) wrote every walk-forward to
`data/checkpoints/msgarch_credit/` (mtimes 12:21-12:25Z, between the freeze push at 12:11:58Z and the
results commit at 12:26:15Z; see `data/MANIFEST.md`). A plain rerun loads those files and only
re-scores them, which is what the 17 Oct chain did: its output equals the result file except that
each "N refits" and last-fit line is replaced by "loaded from <checkpoint>". That shows the scoring
and verdicts follow from the frozen forecasts; it does not show the forecasts can be recomputed. The
wrapper run therefore redirects the checkpoint directory to an empty temporary folder, so every HMM,
GJR-GARCH and MS-GARCH walk-forward is refitted from scratch, and then compares the refitted files
with the frozen checkpoints. 

Result of the refit (run on the same host, with the same virtual environment, installed on 14 Oct
at 11:56Z before the frozen run, the same data files with their 14 Oct mtimes, and no change to
`src/` or the two frozen ETF scripts since the freeze, `git diff da0cf0f HEAD -- src examples`):

- The comparison table and every per-asset verdict label are unchanged: 36 claim rows compared, RMSE
  and QLIKE labels equal on all of them (`examples/reproduction_report.py`), and the claims-across-
  assets table is identical, so no registered outcome moves.
- 24 printed lines differ: MS-GARCH and "HAR + IV + MS-GARCH" losses in the third decimal, interval
  endpoints by up to 0.012 (Brazil M1 RMSE, -0.061 to +0.063 committed against -0.058 to +0.051
  reproduced) and the last-fit parameters on EEM and EWZ. The full diff is in `PROVENANCE_2026-10.md`
  and `etf/compare.txt`.
- None of the 20 refitted walk-forward files is byte-identical to its checkpoint
  (`python examples/etf_refit_audit.py`, section 1; its output is saved as
`etf_refit_audit_2026-10-17.txt`). The HMM walk-forwards agree to 4e-11 or better;
  GJR-GARCH to 0.014 (daily percent) on oil and 0.001 or better on the others; MS-GARCH differs by
  up to 0.05 to 0.18 on oil, gold and EEM and by up to 8.7 on Brazil, where 39 of 93 refits end at a
  log-likelihood that differs from the frozen fit by more than 0.01 (from -505.6 to +887.5).

Why, as far as tonight's checks go:

- The fits are sensitive to floating-point details. The GJR-GARCH walk-forward on USO, same code and
  data, gives one answer with one OpenBLAS thread and a different one with two or more, and neither
  equals the checkpoint (`etf_refit_audit.py`, section 3). Each setting is deterministic run to run.
  The 14 Oct run's floating-point environment (thread settings, process history) was not recorded,
  so it cannot be recreated exactly.
- MS-GARCH amplifies this because its likelihood has degenerate optima. In the frozen checkpoints,
  35 of 93 Brazil refits and 4 of 76 gold refits have a regime at a boundary: zero GARCH variance or a
  stay probability below 0.05 (the floor is 0.001) (`etf_refit_audit.py`, section 2; post hoc). The refit has 36 and 7, 32 and 4 of them on
  the same dates. Which degenerate optimum a refit lands on changes with tiny numerical differences,
  which is where the Brazil log-likelihood swings come from.
- The wrapper is not the cause. As a control, the frozen ETF script was run with only the checkpoint
  directory redirected and none of the wrapper's recording patches
  (`/opt/hmm-agent/out/diag/etf_plain_refit.py`, log `/opt/hmm-agent/out/repro/diag_etf_plain_refit.log`):
  its printed output is line for line the wrapper's, and none of its 20 walk-forward files equals the
  frozen checkpoint either.

What this means for the published ETF result. The verdicts are robust to this: every label and
outcome is the same under a refit that differs in its MS-GARCH forecasts. The numbers are not
reproducible to the printed digit, and the MS-GARCH walk-forwards on Brazil and, for a few months,
gold rest partly on boundary fits that the protocol did not anticipate. How much those fits move the
Brazil and gold MS-GARCH rows is a post-hoc question for stage S3 (convergence and data-quality
record) and is not answered here. The committed checkpoints remain the forecasts the registered
verdicts were computed from; the saved refit forecasts in `etf/` are a second, different set.

For the post-hoc statistics the frozen forecasts are the right input, so the wrapper was also run
with `--use-checkpoints` into `etf_frozen_checkpoints/`: it re-scores the frozen walk-forwards and
saves the calibrated forecasts built from them. Its output equals the committed result file except
for the 28 lines where a checkpoint load replaces the "N refits" and last-fit lines (see
`etf_frozen_checkpoints/compare.txt`); every loss, interval and verdict is identical.

## What a reader can check

- `python -u examples/reproduce_holdout.py <holdout>` on any machine with the caches listed in
  `data/MANIFEST.md`; `compare.txt` in the output folder is the diff against the committed reference.
- The frozen files' sha256 are in `/opt/hmm-agent/protected.sha256` on pc-lanes and unchanged.
- Limits: the data caches for the cross-index and VIX holdouts were copied to pc-lanes from the
  laptop on 17 Oct, so their mtimes here are copy times. The laptop mtimes, which date the first
  download relative to each freeze, are tabulated in the desk review (model-validator, Q1) and are
  not re-checked here. Package versions on the laptop at the time of the frozen runs were not
  recorded; `requirements-lock.txt` (added 16 Oct) pins the same numpy, pandas, scipy, statsmodels,
  arch, numba and yfinance versions as used here (a few non-numerical packages differ by a patch
  version).
