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

## Identity reruns after the convergence-recording change (stage S3, 17 Oct 2026, 21:10-21:17Z)

Class: reproduction. Stage S3 of the reopen added a per-refit convergence record to every
walk-forward (`regimes.evaluate.walk_forward_oos`, `garch.walk_forward_gjr`, `msm.walk_forward_msm`,
`msgarch.walk_forward_msgarch`, `vix_regimes.walk_forward_vix_hmm`,
`correlation.walk_forward_corr_regimes`): the fitters take an optional `info` dict and the results
gain a `convergence` table; no return value, signature or number changes. The proof is this rerun:
each holdout was reproduced again with `examples/reproduce_holdout.py --out <identity rerun folder>`
on the patched code and compared file by file with the folders above by
`examples/compare_reproductions.py` (output in `identity_2026-10-17_S3.txt`, numbers below from it).

| Holdout | stdout | forecasts | scored | walk-forward series | verdict | convergence recorded |
|---|---|---|---|---|---|---|
| vix_early | identical | 11 of 11 | 2 of 2 | 6 of 6 | identical on every shared file | HMM 49 of 49 refits; VIX-HMM 49 of 49 refits (97 of 97 EM starts) |
| vix_recent | identical | 11 of 11 | 2 of 2 | 6 of 6 | identical on every shared file | HMM 75 of 75 refits; VIX-HMM 75 of 75 refits (149 of 149 EM starts) |
| etf_frozen_checkpoints | identical | 36 of 36 | 4 of 4 | none run (checkpoints loaded) | identical on every shared file | not exercised: the frozen checkpoints are loaded, so GJR and MS-GARCH were not refit |
| cross_index | identical | 30 of 30 | 3 of 3 | 19 of 19 | identical on every shared file | per index: HMM 95 of 95, GJR 95 of 95, MSM 95 of 95 refits (430 of 430 L-BFGS-B starts) |
| stock_bond (run 3, 22:00-22:29Z, two runs of 890 s and 877 s) | identical | none saved | none saved | 2 of 8 identical; 6 series differ by at most 2.2e-16 (see below) | DIFFERS at the last bit; every printed table identical | correlation HMM: 158 of 158 refits per walk-forward (315 of 315 and 274 of 315 EM starts) |

The only files present on one side are the new `walk_forwards/*__convergence.csv` tables, copied
into the folders above. The MS-GARCH refit path is covered by the unit test only
(`tests/test_convergence.py`: the `info` hook returns the same parameters and likelihood), because a
full ETF refit does not reproduce the committed numbers on this host anyway (see the ETF section).
**Stock-bond (rerun in run 3, 17 Oct 22:00-22:29Z; `identity_2026-10-17_S3_stock_bond.txt`,
logs in `logs_2026-10-17/identity_stock_bond_S3*.log`).** The printed output (`stdout.txt`, which
carries every number the WRITEUP's two stock-bond tables use) is identical to the S1 reference. The
six saved walk-forward series are not byte-identical: `implied_corr`, `prob_high` and `state_rho` of
both correlation HMM walk-forwards differ from the S1 files in the last bit, at most 1.1e-16 to
2.2e-16 (one unit in the last place near 1), in 705 to 2116 of 9941 daily entries and 28 to 38 of
316 state-correlation entries; no sign, shape, index or NaN pattern differs. Two runs of the patched
code (22:00Z and 22:14Z, under different machine load) are byte-identical to each other, so the
patched code is deterministic on this host. The patch to `correlation.py` (`git diff 7ee241f 8e454ec`)
adds an `info` dict and an iteration counter and rewrites `max(fits, key=...)[0]` as an index
`max(...)`, which has the same tie-breaking; it changes no arithmetic. A third run with the pre-S3
`regimes` package (`git archive 7ee241f src/regimes`, shadowed via PYTHONPATH, same shell, same data)
was started at 22:32Z to pin whether the last-bit difference follows the code or the environment of
the S1 run (made at 20:00Z while other refits were running); its result (22:32-22:46Z, `logs_2026-10-17/identity_stock_bond_pin_S1.log`): the pre-S3 package
run in tonight's shell is byte-identical to the patched run on all six walk-forward series and the
stdout, and differs from the S1 reference exactly as the patched run does. The last-bit difference
therefore follows the environment of the S1 run (made at 20:00Z beside other refits), not the
convergence patch; the patch is behaviour-preserving for the stock-bond walk-forward as well. The
shadowed package was built from `git archive 7ee241f src/regimes` under `/opt/hmm-agent/out/repro/pin_s1`
with the data folder symlinked. Nothing in `docs/results/` or the WRITEUP moves: the differences are
at the 16th digit of unpublished intermediate series and every printed number is identical.

## Tolerance comparison of the two reproductions that are not identical (stage S7 c, 18 Oct 2026)

Class: reproduction. `examples/compare_forecasts.py` (new in S7) measures how far apart two
reproductions are and whether any verdict moves: in folder mode it compares the saved scored tables
model by model and recomputes every registered comparison on each side (63-day circular blocks, 2,000
draws, seed 0); in text mode it lines up a committed result file with a reproduction's stdout and
compares every printed number. Both runs below were made on pc-lanes on 18 Oct from the folders above;
the full reports are saved beside this file.

**ETF, full refit against the frozen checkpoints** (`compare_forecasts.py folders etf_frozen_checkpoints
etf --holdout etf`, report `compare_forecasts_etf_refit_2026-10-18.txt`). The target is identical on
every asset. The HMM implied vol agrees to 5e-12 or better, GJR-GARCH to 0.005 (oil) and 7e-5 or
better elsewhere. MS-GARCH and the two HAR + IV + MS-GARCH sets differ most: largest single-day
forecast difference 0.419 (MS-GARCH, Brazil; daily percent), 0.025 to 0.048 on oil and gold, 0.005 on
EEM. The largest change in any model's RMSE is 0.0051 (MS-GARCH, Brazil: 0.9308 frozen, 0.9257
refit) and the largest shift of any registered interval end is 0.0124. Per-asset verdicts moved: 0 of
36 on RMSE and 0 of 36 on QLIKE; no claim outcome moves on either loss. The text-mode comparison of
the refit's stdout with the committed result file (`compare_forecasts_etf_refit_text_2026-10-18.txt`)
finds 24 lines with numeric differences, the largest 0.1 (the printed MS-GARCH Student-t `nu`, 14.8
against 14.9), one structural difference (the two-line header added by hand to the committed file),
and no verdict word moved.

**Cross-index, wrapper against the committed result** (`compare_forecasts.py text
docs/results/cross_index_holdout_2026-10-14.txt cross_index/stdout.txt`, report
`compare_forecasts_cross_index_2026-10-18.txt`). 104 lines on each side; 3 lines differ, all the
printed last MSM fit, parameter `b` only, by 0.003 (Nasdaq-100), 0.001 (Dow) and 0.001 (Russell
2000); no structural difference; no verdict word moves. The frozen run saved no forecasts, so a
forecast-level comparison is possible only after a laptop rerun (see `LAPTOP_RERUN.md`).

Reading. Both are "within tolerance, verdicts unchanged". Neither is "identical", and the ETF refit
is not a reproduction of the frozen MS-GARCH fits: it is a second set of fits that lands on the same
verdicts. The tolerance is not one fixed in advance; it is what was measured, stated above.
