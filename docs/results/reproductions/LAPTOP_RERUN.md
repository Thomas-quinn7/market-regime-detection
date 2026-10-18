# Laptop rerun of the two reproductions that are not identical

Class: reproduction. A rerun of a spent holdout is a reproduction, never a test (scope rule 1).
Written 2026-10-18 by the reopen agent (stage S7 c) for Thomas to run on the laptop after the
`reopen-2026-10` branch is merged there. Nothing here needs pc-lanes, which is destroyed around 24 Oct.

Why these two. On pc-lanes the VIX and stock-bond holdouts reproduced every published number, and the
ETF holdout re-scored its frozen checkpoints exactly. Two things did not reproduce exactly
(`REPRODUCTION_2026-10.md`, "Tolerance comparison"): the cross-index result file differs in the third
decimal of one printed MSM parameter on each index (the frozen run was on the laptop), and a full refit
of the ETF MS-GARCH models lands on different fits (largest RMSE change 0.0051, no verdict moves). The
laptop run says whether the cross-index difference is the machine, and gives the ETF refit a second
machine.

## Before you start

- 8 GB RAM: run one holdout at a time with nothing else open (no browser, no IDE indexing). Do not run
  the two holdouts in parallel.
- PowerShell, from the repo root, on the merged branch. `$py = ".venv\Scripts\python.exe"`.
- Check the data caches against the manifest written on pc-lanes. Every line must say 0 differ, 0
  missing; if not, stop and do not run (a different cache makes it a different computation):

```powershell
& $py examples\data_manifest.py --check --holdout cross_index
& $py examples\data_manifest.py --check --holdout etf
```

  The ETF check needs the ETF caches (USO, GLD, EEM, EWZ, the four FRED Cboe indices, BAA10Y) and
  `data\checkpoints\msgarch_credit\` copied off pc-lanes; they are gitignored, so they come over only if
  you copied `data\` (desk, data-engineer, finding 15). On pc-lanes on 18 Oct the checks gave 9 of 9
  (cross_index) and 43 of 43 (etf) files equal, and 101 of 101 in all.
- Cross-index only: the frozen loader wants one Databento bar file per index under
  `MARKET_DATA_DIR`, as on 14 Oct. With the laptop's bar folder in place it reads the committed
  `data\*_rv_5min.csv` caches and does not open the bars; if the bars are not there the wrapper uses
  empty placeholder files and says so in `provenance.json`.

## 1. Cross-index (expected wall clock: 10 to 25 minutes)

pc-lanes took 479 s through the wrapper with other runs beside it, and 4 min 47 s for the frozen
script alone (`PROVENANCE_2026-10.md`); the 14 Oct laptop run took 17.4 minutes from freeze to results
commit, including writing the RV caches.

```powershell
& $py -u examples\reproduce_holdout.py cross_index --out docs\results\reproductions\laptop_cross_index *> laptop_cross_index.log
& $py examples\compare_forecasts.py text docs\results\cross_index_holdout_2026-10-14.txt docs\results\reproductions\laptop_cross_index\stdout.txt --save docs\results\reproductions\laptop_cross_index\vs_committed.txt
& $py examples\compare_forecasts.py folders docs\results\reproductions\cross_index docs\results\reproductions\laptop_cross_index --holdout cross_index --save docs\results\reproductions\laptop_cross_index\vs_pc_lanes.txt
& $py examples\compare_reproductions.py docs\results\reproductions\cross_index docs\results\reproductions\laptop_cross_index
```

## 2. ETF full refit (expected wall clock: 20 to 45 minutes)

pc-lanes took 971 s (8 cores, other runs beside it). The wrapper redirects the walk-forward
checkpoints to a temporary folder, so `data\checkpoints\msgarch_credit\` is never written.

```powershell
& $py -u examples\reproduce_holdout.py etf --out docs\results\reproductions\laptop_etf *> laptop_etf.log
& $py examples\compare_forecasts.py folders docs\results\reproductions\etf_frozen_checkpoints docs\results\reproductions\laptop_etf --holdout etf --save docs\results\reproductions\laptop_etf\vs_frozen.txt
& $py examples\compare_forecasts.py folders docs\results\reproductions\etf docs\results\reproductions\laptop_etf --holdout etf --save docs\results\reproductions\laptop_etf\vs_pc_lanes_refit.txt
```

## What to keep

Commit the two folders `docs\results\reproductions\laptop_cross_index\` and `laptop_etf\` (stdout,
forecasts, scored tables, walk-forwards, `provenance.json`, the `vs_*.txt` reports) and the two logs
(move them into the folders). Nothing else changes: the committed result files under `docs\results\`
are frozen. Each `compare_forecasts.py` call ends with a `verdict:` line and exits 0 if no verdict
and no claim outcome moves, 1 if one does.

## The sentence the paper may use, by outcome

- **Cross-index identical** (text report "identical", or the three MSM lines now equal): "The
  cross-index holdout reproduces byte for byte on the machine it was run on; on a second machine one
  printed MSM parameter differs in the third decimal and every table number is equal."
- **Within tolerance, verdicts unchanged** (the `verdict:` lines say "within tolerance"; the expected
  outcome for the ETF refit): "A full refit of the MS-GARCH models on a second machine, and on a third,
  does not reproduce the frozen fits exactly: the largest change in any model's RMSE is <x> and no
  per-asset verdict or claim outcome moves. The published result is the frozen run's, whose saved
  walk-forward files re-score exactly." Take <x> from the summary line of `vs_frozen.txt` (0.0051 on
  pc-lanes).
- **A verdict moves** (a `MOVES` line, exit status 1): report it as the most important result of the
  rerun. The published verdict stays the frozen run's (it is what was registered and run once), and the
  paper says: "On a refit on a second machine the <claim> verdict on <asset> moves from <a> to <b>;
  the MS-GARCH fits are not numerically stable enough for that verdict to be called robust." Then
  P7 and P28 in `docs/FIXES_FOR_THOMAS_2026-10.md` need that sentence instead of "no verdict moves".
