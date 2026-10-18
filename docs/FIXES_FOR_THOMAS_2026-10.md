# Fixes for Thomas, October 2026 reopen

Running list of text changes from the reopen lane. Factual corrections (a wrong number, count, date or
runtime) may be applied on the branch and are listed here with old and new text; claim-wording changes are
proposals only and are never applied. Thomas's pointer of 2026-10-18 00:00 asked for the proposed wording
now, all as proposals, every claim sentence naming its loss (RMSE or QLIKE). The S6 pass adds every
remaining sentence the desk review and the panel flagged.

Classes used below: "reproduction" (a frozen holdout re-run; never a test), "post hoc" (computed from the
reproduced forecasts; not registered), "development data only". Source of each item: "desk, <lane>" is
`/opt/hmm-agent/reviews/`, "fitness" is the joint desk review of 2026-10-18 (fitness-reviewer report),
"panel" is `HMM_PAPER_REVIEW_PANEL_2026-10-17.md`.

## Applied (factual corrections and code)

### A1. Six, not five, S&P trading days in 2014 have no ES bars

- Where: `docs/WRITEUP.md` line 649 and the module docstring of `examples/intraday_rv.py` line 39.
- Old: "the five S&P trading days in 2014 with no bars (Databento flags them as degraded) are left missing"
  (WRITEUP); "the five S&P trading days in 2014 with no ES bars are left missing" (intraday_rv.py).
- New: "the six S&P trading days in 2014 with no bars ..." and "the six S&P trading days in 2014 with no
  ES bars ...".
- Evidence: `data/es_rv_5min.csv` against the S&P 500 calendar in `data/GSPC_2000-01-01_2023-12-31.csv`
  has six trading days from 2010-06-07 with no session RV: 2014-06-12, 2014-06-13, 2014-09-23,
  2014-09-24, 2014-09-25, 2014-12-31 (the same six the frozen cross-index run prints as "6 missing" for
  the Nasdaq-100; `docs/DATA_QUALITY_2026-10.md` section 3, `examples/data_quality.py`). Source of the
  item: desk, data-engineer, F4. Applied 2026-10-17 by the reopen agent.

### A2. Walk-forward checkpoints are now tied to the input values (code, behaviour-preserving)

- Where: `src/regimes/evaluate.py`, `walk_forward_oos` (the checkpoint `settings.json`), new helper
  `series_sha256`; tests in `tests/test_checkpoint_hash.py`.
- What: the checkpoint folder's `settings.json` records a sha256 of the dates and float64 values of the
  input series beside `n`, `first`, `last` and the settings. A rerun whose data has the same span but a
  revised print inside it is refused instead of silently reusing the saved blocks. A `settings.json`
  written before this change (no hash) is accepted once on span and settings, with a warning, and upgraded.
- Why: desk, quant-dev F2 and data-engineer F4 of the joint review (finding 9): "checkpoint validity keyed
  on {n, first, last, settings}, never on data values". Thomas's pointer 2026-10-18 (b): apply only if every
  reproduction stays identical.
- Reproduction identity: no frozen script passes `checkpoint_dir` (only `examples/regime_labels.py`
  does), and the VIX 1996-2004 holdout rerun through `examples/reproduce_holdout.py` after the change is
  identical to the committed reproduction on every shared file (`examples/compare_reproductions.py`,
  22 files; log in `/opt/hmm-agent/out/repro/identity_hash/`). No committed folder under `data/` carries a
  walk-forward `settings.json`, so no committed file changes. Applied 2026-10-18 by the reopen agent.
- Not done: the same change in the VRP repo's vendored copy (`src/vrp/hmm.py`), which is outside this
  lane; the joint review asks the VRP lane for it.

## Proposed (claim wording and additions; not applied)

Each item: where, old text, proposed new text, why, evidence. Thomas's words win; these are drafts.

### P1. README.md lines 13-15: "where the two were level"

- Old (README.md:13-15): "The regime model's own forecast had a higher error than HAR plus implied vol on
  every holdout but one, the short 2024-2026 sample, where the two were level."
- Proposed: "On the two S&P 500 holdouts the registered comparison for the regime model's own forecast was
  against HAR without the VIX: on RMSE it lost on 1996-2004 and was not shown to differ on 2024-2026,
  where it beat HAR on QLIKE. Against HAR plus implied vol the registered comparison was on the four ETFs
  only, where MS-GARCH lost on all four on RMSE and on oil alone on QLIKE. The S&P comparisons against
  HAR plus the VIX are unregistered: on 1996-2004 the HMM's implied vol is worse on both losses; on
  2024-2026 the two are not shown to differ on either (post hoc)."
- Why: the sentence reads an unregistered point estimate (HMM 0.403 vs HAR + VIX 0.406 RMSE,
  WRITEUP.md:552-553) as "level" and drops the one result in the HMM's favour (QLIKE interval -0.100 to
  -0.013, WRITEUP.md:571-572). Desk HIGH 1; fitness F3 (the first two sentences are the fitness
  reviewer's, with the losses named); panel item 2.
- Evidence: WRITEUP.md:547-572 (reproduction: `examples/check_writeup_tables.py`, 52 numbers equal);
  `docs/POSTHOC_2026-10.md` (f) (post hoc): 1996-2004 HMM implied vol vs HAR + VIX +0.044 to +0.133 RMSE,
  +0.077 to +0.275 QLIKE, worse; 2024-2026 -0.038 to +0.052 RMSE, -0.136 to +0.033 QLIKE, no difference.
  ETF per-asset QLIKE for M5: POSTHOC (a) table, MS-GARCH and credit holdout (oil worse +0.034 to +0.181;
  gold, emerging markets and Brazil no difference).

### P2. README.md line 47: the MS-GARCH row names no loss

- Old (README.md:47, inside the row): "MS-GARCH loses to HAR + implied vol on all four and is no better
  than one GJR-GARCH, though it does beat the two-state HMM (confirmed); credit adds nothing"
- Proposed: "MS-GARCH loses to HAR + implied vol on all four on RMSE, the registered loss (on QLIKE, oil
  only; post hoc), is no better than one GJR-GARCH on either loss, and beats the two-state HMM on RMSE
  (confirmed: gold and emerging markets; on QLIKE the two assets are oil and Brazil, post hoc); credit adds
  nothing on either loss"
- Why: every claim sentence should name its loss (desk HIGH 3; fitness F6; pointer (c)). Under QLIKE the
  "all four" becomes one asset and M3 is confirmed on a disjoint pair of assets.
- Evidence: `docs/POSTHOC_2026-10.md`, MS-GARCH and credit holdout, (a) table and "Claim outcomes under
  each loss" (post hoc): M5 rejected on both losses, M3 confirmed on both, M1 rejected, C1 holds, C2
  rejected; R1 confirmed on RMSE and mixed on QLIKE.

### P3. WRITEUP.md line 903: "every RMSE interval wholly above zero"

- Old (WRITEUP.md:903-904): "MS-GARCH lost to HAR plus implied vol on all four assets, with every RMSE
  interval wholly above zero, from +0.005 to +0.048 on emerging markets up to +0.038 to +0.240 on oil."
- Proposed: "MS-GARCH lost to HAR plus implied vol on all four assets on RMSE, the registered loss, with
  every RMSE interval wholly above zero, from +0.005 to +0.048 on emerging markets up to +0.038 to +0.240
  on oil. On QLIKE, computed afterwards from the same forecasts, only oil's interval is above zero
  (+0.034 to +0.181); gold's, emerging markets' and Brazil's span zero."
- Why: desk HIGH 3. The protocol file is frozen and cannot change; the WRITEUP sentence can carry the
  second loss.
- Evidence: POSTHOC (a) table for the ETF holdout (post hoc).

### P4. README.md line 156: the stock-bond caveat

- Old (README.md:155-157): "One caveat: the stock-bond freeze (53b50c6) was pushed in the same push as
  its results, so for that holdout the commit order is local evidence only."
- Proposed: "One caveat: the stock-bond holdout was an out-of-sample check whose rules I wrote before
  running it, not a frozen holdout. Its data files were on disk (14:17-14:18 on 13 Oct) before the protocol
  was written (14:23) and committed (53b50c6, 14:33), the loader that reads them was committed with the
  results, and the freeze and the results went up in one push, so for that holdout the commit order is
  local evidence only."
- Why: desk HIGH 5 (data-engineer, model-validator): the two facts a reader can check from mtimes and git
  are missing. Fitness F7 proposed the first sentence.
- Evidence: file mtimes and `git log` for 53b50c6 (desk, data-engineer report, 2026-10-17); the same facts
  belong at `docs/HOLDOUT_PROTOCOL.md:3` (frozen; cannot change) and WRITEUP.md:463-466.

### P5. WRITEUP.md line 950: "about 1.5 hours" (factual; applied on your word)

- Old (WRITEUP.md:950): "python examples/cross_index_holdout.py # the frozen Nasdaq-100, Dow and Russell
  2000 holdout (about 1.5 hours)"
- Proposed: "python examples/cross_index_holdout.py # the frozen Nasdaq-100, Dow and Russell 2000 holdout
  (about 20 minutes once the 5-minute RV caches exist; freeze 963cb5e 09:31, results 6f4a3d4 09:49 on
  2026-10-14)"
- Why: the commit times give 17.4 minutes between the freeze and the results commit (desk HIGH 2;
  fitness F11); the 1.5 hours was a pre-run estimate. This is a runtime correction that rule 7 lets the
  lane apply; it is left as a proposal because the 2026-10-18 pointer said "all as proposals". One line
  ("apply P5") and it is applied.
- Evidence: `git log --format='%h %ad' 963cb5e 6f4a3d4` (09:31:39 and 09:49:03 +01:00); the pc-lanes
  rerun of the frozen script with the committed RV caches took 4 min 47 s
  (`docs/results/reproductions/REPRODUCTION_2026-10.md`, reproduction).

### P6. README.md lines 37 and 52 (panel D items; LOW)

- Old (README.md:37): "AIC/BIC pick 2 states". Proposed: "two states, the only count whose fits converged
  under default starts (three and four states have lower AIC and BIC but did not converge; see
  docs/DEV_K_STATES_2026-10.md for the restart check, development data only)".
- Old (README.md:52): "regimes differ in variance". Proposed: "regimes differ in variance and intercept".
- Why: panel D (items at HMM_PAPER_REVIEW_PANEL_2026-10-17.md:26-27); fitness LOW. The selection table
  excludes non-converged fits (`src/regimes/selection.py`), so "pick" is an optimiser outcome.
- Evidence: `docs/DEV_K_STATES_2026-10.md` table 1 (`examples/dev_k_states.py`; development data only):
  the Gaussian three- and four-state fits do not converge with the default start or with 20 random starts.

### P7. A reproduction note for the public text (new paragraph, README "Reproducing the numbers")

- Proposed: "In October 2026 the four holdouts were re-run on a second machine from the committed caches
  (`docs/results/reproductions/REPRODUCTION_2026-10.md`). A re-run of a spent holdout is a reproduction,
  not a test: it checks that the committed numbers come out of the committed code and data, and it cannot
  confirm or re-test a claim. The VIX and stock-bond tables reproduced exactly (52 numbers checked). The
  cross-index result file is not byte-identical: every table number is equal, but one printed MSM
  parameter differs in the third decimal on each index. The ETF holdout re-scores its frozen checkpoints
  exactly, but a full refit of the MS-GARCH models does not reproduce them: none of the 20 walk-forward
  files matches, several losses and interval ends move in the third decimal, and no per-asset verdict or
  claim outcome changes. The post-hoc statistics in `docs/POSTHOC_2026-10.md` and the data-quality
  record in `docs/DATA_QUALITY_2026-10.md` are computed from these reproduced forecasts and are not
  registered tests."
- Why: joint review finding 15 (model-validator F5); scope rule 1 (reproduction, never test).
- Evidence: `docs/results/reproductions/REPRODUCTION_2026-10.md` (reproduction;
  `examples/reproduce_holdout.py`, `examples/check_writeup_tables.py`, `examples/etf_refit_audit.py`).

### P8. The VIX source, one sentence per claim (new; README data section and WRITEUP)

- Proposed (README, after the data description): "The development work and the two S&P 500 holdouts
  (claims A, B, C) use Yahoo's ^VIX; the cross-index holdout (P1-P5, R1-R3) uses FRED's VIXCLS as the
  implied vol for all three indices, and the ETF holdout (M1-M5) FRED's OVXCLS, GVZCLS, VXEEMCLS and
  VXEWZCLS. FRED's series equals Cboe's published history; Yahoo's differs from it on 12 of 6,037
  development days by up to 0.98 points (2014-10-15) and has no row on 13 days FRED prints (2004-06-11
  and twelve 2022-2023 US holidays). The stock-bond holdout uses no VIX."
- Why: joint review finding 18 (data-engineer F3): the pair does not use "the same VIX", and the paper
  never names the source per claim.
- Evidence: `examples/vix_source_check.py` (development data only; the committed caches
  `data/VIX_2000-01-01_2023-12-31.csv` and `data/fred_VIXCLS.csv` to 2023-12-31): 12 differing days,
  largest 0.98 on 2014-10-15, 13 FRED-only days, 0 Yahoo-only days; the per-claim sources are read off
  `src/regimes/data.py`, `examples/cross_index_holdout.py:52` and `examples/msgarch_credit_holdout.py:42-48`.
  The desk's count (12 days, 0.98, six missing prints) was on days to 2022-12-30; the seven extra
  FRED-only days here are 2023 holidays.

### P9. An AI-assistance section for the README (new section after "Citing this work")

- Proposed heading: "How this was built".
- Proposed text (the fitness reviewer's draft, for Thomas to rewrite in his own words): "I wrote the
  research questions, chose every claim and holdout, wrote and pushed each protocol before its data was
  opened, and ran each holdout once. Most of the code, and the first drafts of the write-up and docs, were
  written by an AI assistant (Claude, Anthropic) working from my specifications in sessions I directed;
  the October 2026 reproductions, post-hoc tables and development continuations were produced by an
  overnight agent under a fixes-only scope I set, and its commits on the reopen branch are titled 'Agent
  run'. I have checked every number in the README and write-up against the scripts and the committed
  result files, and the interpretation and the mistakes are mine. The paper text I post elsewhere is my
  own rewrite of docs/WRITEUP.md."
- Why: joint review finding 4 (fitness F2): no AI statement in either repo while the branch history says
  "Agent run"; due before the VRP flip and before 30 Nov.
- Evidence: `git log --oneline reopen-2026-10` (commit titles); `/opt/hmm-agent/HMM_REOPEN_SCOPE.md`.

### P10. Claim C on 1996-2004 and claim A on 2024-2026 (loss-naming for the WRITEUP claims table)

- Old (WRITEUP.md:557-558, claims table caption): "The three claims taken to the holdouts, judged on RMSE
  with a paired block-bootstrap 95% interval for the difference:"
- Proposed: keep the table, and add after it: "The registered loss is RMSE. Under QLIKE, computed
  afterwards from the same forecasts, A and B hold on 1996-2004 but C is not shown (the HMM implied vol's
  QLIKE interval against HAR spans zero), and on 2024-2026 B holds but A is not shown; C was not shown on
  RMSE there either. On 1996-2004 C also depends on the calibration and the row choice: the raw HMM
  implied vol is no different from HAR on both losses, and calibrating every model on common rows moves
  the VIX-HMM comparison from worse to no difference."
- Why: pointer (c): every claim sentence names its loss; desk HIGH 3; S2 digest item 1 (your decision on
  whether C's sentence is rewritten; this is the table-side version).
- Evidence: `docs/POSTHOC_2026-10.md`, S&P 500 1996-2004 and 2024-2026 sections, "Claim outcomes under
  each loss" tables, (e) and (g) (post hoc).

### Still to come in S6

Every other sentence the desk synthesis and the panel flagged (allocation section wording after S5,
the "every holdout re-derives" line, DATA_QUALITY paragraph for the partial YM sessions and the 2014 gap,
the panel D items not listed above), each with line, old text, proposed text and whether applied.
