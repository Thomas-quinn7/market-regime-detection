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

### A3. WRITEUP.md line 950: the cross-index runtime (P5, applied on your word)

- Applied 2026-10-18 on Thomas's pointer of 2026-10-18 11:56 ("apply P5"). Old and new text, why and
  evidence: P5 below.

### A4. "-52%" to "-51%" for the static-equity drawdown, four places (P14, applied on your word)

- Applied 2026-10-18 on Thomas's pointer of 2026-10-18 11:56 ("apply P14") at README.md:41,
  WRITEUP.md:316 (table), :324 and :364. Old and new text, why and evidence: P14 below. The Calmar ratio
  in the same table row (0.19) is unchanged at two decimals (10.0 / 51.48 = 0.194). The rounding note in
  `docs/ALLOCATION_LAG_2026-10.md` section 2 describes the text before this change.

### A5. WRITEUP.md line 701: "Calm 2019" is the last quarter of 2019

- Old: "Calm 2019 sat at about 0.9 in the forecast against 0.4 in reality (panel 4)."
- New: "Calm late 2019 sat at about 0.9 in the forecast against 0.4 in reality (panel 4)."
- Why: a date correction. Panel 4 is drawn by `examples/why_hmm_loses.py` on the window
  `slice("2019-10-01", "2020-12-31")` (line 214), so the calm months it shows are October to December
  2019. Source: desk, quant-researcher (LOW, WRITEUP:701-702): Q4 2019 medians 0.92 vs 0.45, calendar
  2019 means 1.03 vs 0.70 (the desk's figures from its own run, not recomputed by a repo script). Only
  the date word changes; the 0.9 and 0.4 are the published figures.

### A6. README.md lines 153-157: "not edited between freeze and results except to add the freeze hash"

- Old: "the protocol files were not edited between freeze and results except to add the freeze hash, and
  the result files under `docs/results/` have not been changed since."
- New: "the protocol files were not edited between freeze and results except to add the freeze hash (the
  results commits then changed the status line of the cross-index and MS-GARCH protocols and appended a
  results section, 51 and 61 lines; no rule was edited), and the result files under `docs/results/` have
  not been changed since."
- Why: scope rule 7 names this correction ("only the hash line" to the true description). Desk,
  data-engineer, and "Where the desk corrects the academic panel" in the synthesis: the protocols got a
  results section appended (+54 and +64 lines from the freeze, of which 3 each are the hash commit).
- Evidence: `git show --stat b233742 6f4a3d4 324dfe3 58a351f -- docs/*PROTOCOL.md` (+3, +51/-1, +3,
  +61/-1); the only deleted line in each results commit is the "Status, 2026-10-14: frozen, not yet run"
  line (`git diff 963cb5e 6f4a3d4`, `git diff da0cf0f 58a351f`). The VIX and stock-bond protocols have
  no commit after their freeze.

### A7. WRITEUP.md line 538: "before their data was downloaded" to "opened"

- Old: "the rules for two holdouts were committed and pushed before their data was downloaded"
- New: "the rules for two holdouts were committed and pushed before their data was opened"
- Why: scope rule 7 names this correction; the README (lines 9-10, 150-151) says "opened" and the
  other protocols use that word. The cache files the VIX holdout read were written 11 s and 95 s after
  the freeze commit 3fea6a7, but the desk (data-engineer, input table) found an earlier 15:26 pull of the
  2005-2026 VIX on 13 Oct, value-identical to the cache, so "downloaded" is not the defensible word for
  the 2024-2026 holdout; "opened" is the claim the protocol makes.
- Evidence: desk, data-engineer report, table "Inputs" (VIX recent: "0 diffs vs 15:26 pull"); panel,
  "Errors in the draft" item 2.

## Proposed (claim wording and additions; not applied)

Each item: where, old text, proposed new text, why, evidence. Thomas's words win; these are drafts.

### P1. README.md lines 13-15: "where the two were level"

- Status: **APPLIED 2026-10-19 on Thomas's word** ("paste P1 as approved"), the three sentences exactly as
  proposed below, README.md:13-18. Earlier: Thomas's pointer of 2026-10-18 11:56 approved all three
  sentences, including the one naming the unregistered HAR + VIX comparisons on the S&P.

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

- Status: **APPLIED 2026-10-20 on Thomas's word** (README.md line 51), exactly as proposed.

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

### P4. README.md line 158: the stock-bond caveat

- Status: **APPLIED 2026-10-20 on Thomas's word** (README.md lines 169-173), exactly as proposed. Not done here:
  the same facts at WRITEUP.md:463-466 (that is P21, not ruled).

- Old (README.md:157-159 after A6; 155-157 before it): "One caveat: the stock-bond freeze (53b50c6) was pushed in the same push as
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

### P5. WRITEUP.md line 950: "about 1.5 hours" (factual; APPLIED 2026-10-18 on your word, see A3)

- Old (WRITEUP.md:950): "python examples/cross_index_holdout.py # the frozen Nasdaq-100, Dow and Russell
  2000 holdout (about 1.5 hours)"
- Proposed: "python examples/cross_index_holdout.py # the frozen Nasdaq-100, Dow and Russell 2000 holdout
  (about 20 minutes once the 5-minute RV caches exist; freeze 963cb5e 09:31, results 6f4a3d4 09:49 on
  2026-10-14)"
- Why: the commit times give 17.4 minutes between the freeze and the results commit (desk HIGH 2;
  fitness F11); the 1.5 hours was a pre-run estimate. This is a runtime correction that rule 7 lets the
  lane apply; applied 2026-10-18 on Thomas's "apply P5" (pointer 11:56).
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

- Status: **APPLIED 2026-10-20 on Thomas's word** (README.md, after the API-key paragraph), README only; the
  WRITEUP copy is not done. One change: "12 of 6,037 development days" became "12 of 6,037 common days in
  2000-2023", because the compared span includes 2000-2004, which is holdout, not development (re-run of
  `examples/vix_source_check.py` 2026-10-20: same counts, 12 / 6037 / 0.98 / 13 / 0).

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

### P11. WRITEUP.md lines 298-300: the execution assumption and the cost per switch

- Status: **APPLIED 2026-10-24 on Thomas's word** ("approve P16 and P11-P13, apply them"), WRITEUP.md:298-307,
  with two wording changes found when checking against `ALLOCATION_LAG_2026-10.md` sections 3 and 4: "do not
  move" became "barely move (Sharpe 0.56 to 0.59 and 0.66 to 0.64)", and the lag comparison names its window
  ("scored on the same 4,022 days, one fewer than the table below"), because the 21-day rule's lag-1 Sharpe is
  0.75 there against 0.74 in the published table.

- Old (WRITEUP.md:298-300): "The rules are deliberately strict on look-ahead: the regime probability is the
  **walk-forward out-of-sample** one (parameters estimated only on past data), the position for each day
  is decided from the prior day's information, and turnover is charged 5 basis points."
- Proposed: "The rules are deliberately strict on look-ahead: the regime probability is the **walk-forward
  out-of-sample** one (parameters estimated only on past data), the position for each day is decided from
  the prior day's close and filled at that same close, and turnover is charged 5 basis points per leg (a
  full switch is 10 basis points). Filling at the close that produced the signal is the most favourable
  execution a closing-price signal can have. With one more day of lag (signal at the close of t-2, filled
  at the close of t-1) the regime switch goes from Sharpe 0.66 and max drawdown -15% to 0.44 and -26%, and
  the 21-day trailing-vol rule from 0.75 and -18% to 0.58 and -23%; the EWMA rule and vol targeting do
  not move. The regime switch trades about 15 full switches a year, 1.55% a year of brokerage at 5 basis
  points per leg, against about 0.5% for the trailing-vol rules."
- Why: the backtest trades at the print that produced the signal and the text does not say so; the lag
  moves the regime switch by more than its reported edge over 60/40 (desk, trader section 4, HIGH;
  synthesis finding 4; the HMM row is the run the desk could not afford).
- Evidence: `docs/ALLOCATION_LAG_2026-10.md` sections 1, 3 and 4 (development data only), written by
  `examples/allocation_lag.py`; `regimes.allocation.backtest(execution_lag=...)`, default 1 reproduces the
  published table (section 2).

### P12. WRITEUP.md lines 363-365: "The drawdown reduction is the more robust part of the result"

- Status: **APPLIED 2026-10-24 on Thomas's word**, WRITEUP.md:370-374, with one correction: "unchanged at -18%"
  became "barely moves (-19% to -18%)", since `ALLOCATION_LAG_2026-10.md` section 3 has the vol-target rule at
  -19% with the published lag and -18% with one more day.

- Old (WRITEUP.md:363-365): "The drawdown reduction is the more robust part of the result, since every
  switching and vol-targeting rule cuts the maximum drawdown sharply (-12% to -25%, against -52% for
  equity), though as a single-path statistic it has no interval here either."
- Proposed: "Every switching and vol-targeting rule cuts the maximum drawdown on this path (-12% to -25%,
  against -51% for equity), but the drawdown is the statistic most exposed to execution timing: with one
  more day of lag the regime switch's drawdown is -26%, against -31% for the 60/40, while the
  vol-targeting rule's is unchanged at -18%. As a single-path statistic it has no interval here either."
- Why: the sentence a desk would challenge (desk, trader section 4); the lag run measures it.
- Evidence: `docs/ALLOCATION_LAG_2026-10.md` section 3 (development data only).

### P13. WRITEUP.md lines 370-371: "the ~2.3% of annual return given up is a real cost of the insurance"

- Status: **APPLIED 2026-10-24 on Thomas's word**, WRITEUP.md:379-382, reworded because the proposal's split did
  not add up: 1.55 is turnover times cost before compounding, and 1.55 + 0.72 is not 2.40. By section 4's own
  definition (give-up at 5 bps less give-up at zero cost) brokerage is 2.40 - 0.72 = 1.68. Applied text keeps
  the published "~2.3%" (10.0% vs 7.7% in the table) and says about 0.7 points out of the market and about 1.7
  points brokerage.

- Old (WRITEUP.md:370-371): "The binary switch is crude, the ~2.3% of annual return given up is a real cost
  of the insurance, and none of this is a live trading system."
- Proposed: "The binary switch is crude; of the 2.4 percentage points of annual return given up against
  buy-and-hold equity, 1.55 points a year are brokerage at 5 basis points per leg (turnover of 31 a year,
  about 15 full switches) and 0.7 points are the cost of being out of the market (the give-up at zero
  cost); and none of this is a live trading system."
- Why: more than half of the "insurance cost" is whipsaw brokerage and the paper never says so (desk,
  trader section 4, MEDIUM; synthesis finding 4 companion).
- Evidence: `docs/ALLOCATION_LAG_2026-10.md` section 4, regime switch equity/cash, lag 1 (development data
  only): turnover 30.95 a year, drag 1.55 pp at 5 bps, give-up 2.40 pp of which 0.72 gross.

### P14. "-52%" for the static-equity drawdown is -51% (factual; four places; APPLIED 2026-10-18 on your word, see A4)

- Old: "-52%" at README.md:41, WRITEUP.md:316 (table), :324 and :364.
- Proposed: "-51%" in all four.
- Why: the exact maximum drawdown of the static 100% equity line on the published window is -51.48%; the
  script prints -51.5% to one decimal and the hand rounding to whole percent went to -52%. Rule 7 allows
  this as a factual correction; applied 2026-10-18 on Thomas's "apply P14" (pointer 11:56).
- Evidence: `docs/ALLOCATION_LAG_2026-10.md` section 2 note (development data only).

### P15. WRITEUP.md line 302: the 60/40 is rebalanced daily at no cost

- Old (WRITEUP.md:302): "Benchmarks are static 100% equity, a static 60/40, and the baseline from earlier:"
- Proposed: "Benchmarks are static 100% equity, a static 60/40 (constant weights, which is a daily rebalance
  that trades nothing; a 60/40 that drifts and is reset at each month end, paying the same 5 basis points,
  earns 7.6% at Sharpe 0.63 with a -32% drawdown against 7.9%, 0.64 and -31%), and the baseline from
  earlier:"
- Why: desk, trader section 4 (LOW): the benchmark is flattered by a few basis points; negligible, and a
  reviewer will notice.
- Evidence: `docs/ALLOCATION_LAG_2026-10.md` section 5 (development data only);
  `regimes.allocation.rebalanced_backtest`.

### P16. README.md line 41: the allocation row

- Status: **APPLIED 2026-10-24 on Thomas's word** (README.md:45), exactly as proposed.

- Old (README.md:41, end of the row): "... and a block bootstrap cannot tell any of the Sharpe ratios apart:
  loss avoidance, not alpha (out-of-sample, after costs)"
- Proposed: "... and a block bootstrap cannot tell any of the Sharpe ratios apart; with one more day of
  execution lag the regime switch is Sharpe 0.44 with a -26% drawdown: loss avoidance, not alpha
  (out-of-sample, after costs, filled at the signal's close)"
- Why: as P11; the README row is where a reader meets the -15% first.
- Evidence: `docs/ALLOCATION_LAG_2026-10.md` section 3 (development data only).

## S6 pass: every remaining sentence the desk synthesis and the panel flagged

Written 2026-10-18 (stage S6). P17, P18 and P19 are reserved by the scope for S7 (power, multiple
testing) and S8 (the ML continuation), so the S6 items start at P20. Every number below is quoted from a
committed doc and the script that printed it is named; nothing is recomputed in this file. Classes as
at the top. "Desk n" is finding n of `HMM_DESK_REVIEW_2026-10-17.md`; "panel, errors" is the list "Errors
in the draft or repo" in `HMM_PAPER_REVIEW_PANEL_2026-10-17.md`.

### P20. README.md lines 11-13: "never made a measurable difference"

- Old (README.md:11-13): "On four holdouts (...), adding a regime probability to a simple HAR forecast
  with the market's own implied vol never made a measurable difference."
- Proposed: "On four holdouts (...), adding a regime probability to a simple HAR forecast with the
  market's own implied vol left the 21-day RMSE unchanged within a 95% paired block-bootstrap interval on
  every holdout asset; those intervals exclude an improvement larger than 0.1% to 3.7% of the reference
  RMSE, depending on the asset, uncorrected across assets, and the same holds on QLIKE (improvements
  above 0.4% to 12.8% excluded; post hoc). The test was at the one-month horizon only."
- Why: desk 9 (model-validator, quant-researcher: what the null is entitled to say); panel, agreed item 4
  (a null without a bound is not evidence of no difference). Names the loss (pointer 00:00 (c)). The
  "uncorrected across assets" clause is the place S7's family count (P18) will attach.
- Evidence: `docs/POSTHOC_2026-10.md` (a), (b) tables (`examples/posthoc_stats.py`, 7ee241f; post hoc),
  the eleven regime-probability rows: cross-index R3 (Nasdaq-100 2.7%, Dow 0.1%, Russell 2000 0.9% on
  RMSE; 5.4%, 0.4%, 0.4% on QLIKE), ETF M4 (oil 0.3%, gold 0.2%, EM 0.5%, Brazil 3.0%; QLIKE 1.0%, 0.4%,
  2.5%, 7.8%), S&P comparisons 4 and 5 on 1996-2004 (2.0%, 1.4%; QLIKE 3.9%, 3.2%) and 2024-2026
  (3.7%, 0.8%; QLIKE 12.8%, 0.8%). Every one is "no difference" on both losses. The desk's soft spot
  (Nasdaq-100 R3 on QLIKE excludes only gains above 5.4%, where HAR-RV + IV + HMM prob has the best
  point RMSE and QLIKE) is in the same table.

### P21. WRITEUP.md lines 463-466: the stock-bond holdout called "run once" on data "neither model had seen"

- Old (WRITEUP.md:462-465): "The rules for a holdout on 1962-2004, which neither model had seen, were
  therefore written and committed first (HOLDOUT_PROTOCOL.md, commit `53b50c6`), and the holdout was run
  once."
- Proposed: "The rules for a check on 1962-2004, which neither model had been fitted to, were therefore
  written and committed (HOLDOUT_PROTOCOL.md, commit `53b50c6`) before it was run, once. It is an
  out-of-sample check rather than a frozen holdout: the two data files it reads were written to disk at
  14:17-14:18 on 13 October, before the protocol file was created (14:23) and committed (14:33); the
  loader that reads them was committed with the development results; and the freeze was pushed in the
  same push as the results."
- Why: desk 5 (data-engineer HIGH, model-validator MEDIUM); panel, agreed item 7. Companion to P4 (the
  README caveat); `docs/HOLDOUT_PROTOCOL.md:3` carries the same claim and is frozen (rule 2), so the
  disclosure has to live in the WRITEUP and README.
- Evidence: desk, data-engineer input table (file mtimes 14:17:47 and 14:18:00; freeze 14:33:59);
  `git log --format='%h %ad' 53b50c6`. The section heading "Holdout, 1962-2004, run once" at
  WRITEUP.md:461 would read "Out-of-sample check, 1962-2004, run once" under this proposal.

### P22. WRITEUP.md lines 529-530: "the same walk-forward regression" (own-row calibration)

- Old (WRITEUP.md:528-529): "Every signal set is turned into a forecast by the same walk-forward
  regression (`regimes.forecast`), refit quarterly and fitted in logs, ..."
- Proposed: add after the sentence: "Each signal set's regression is fitted on the rows where that set
  exists, so at every refit HAR and HAR + VIX train on about three more years than the sets that contain
  an HMM output, which start after the HMM's own first out-of-sample block. Refitting every set on the
  common rows moves no RMSE verdict on either holdout except claim C's VIX-HMM comparison on 1996-2004
  (worse to no difference). On QLIKE it removes the HAR + HMM probability's 'worse' on 1996-2004, and on
  2024-2026 it turns HAR + VIX + HMM probability against HAR + VIX from no difference to better (-0.040
  to -0.000), the one place in the VIX holdouts where the regime probability's interval excludes zero in
  its favour (post hoc)."
- Why: desk 6 (quant-researcher and quant-dev independently; not in the panel): the regression is the
  same, the rows are not, and the cross-index and ETF scripts reindex to common rows.
- Evidence: `docs/POSTHOC_2026-10.md` (g) (post hoc): 1996-2004 own-row first forecast dates HAR
  1993-03-01, HAR + VIX + HMM prob 1996-01-25; "VIX-HMM implied vol vs HAR +0.003 to +0.094 worse (own
  rows), -0.000 to +0.088 no difference (common rows)"; "HAR + HMM prob vs HAR" QLIKE +0.001 to +0.039
  worse to -0.006 to +0.004 no difference; RMSE claim outcomes A and B unchanged, C holds -> not shown.
  2024-2026 half of (g): "HAR + VIX + HMM prob vs HAR + VIX" QLIKE -0.038 to +0.002 no difference (own
  rows) to -0.040 to -0.000 better (common rows); every RMSE verdict unchanged. This is a post-hoc
  reading on a 676-day sample with the interval end at -0.000, not a claim; it belongs beside P20's
  sentence if Thomas adopts the common-row variant as a disclosure.

### P23. WRITEUP.md lines 534-537: the log-scale recalibration, raw beside calibrated

- Old (WRITEUP.md:534-537): "The calibration was first fitted in levels on one year of history and blew
  up, ..., so it now uses log scale and three years of history."
- Proposed: "..., so it now uses log scale and an expanding window that starts with at least three years
  of history. The calibration is a least-squares fit in logs, which is neither RMSE on volatility nor
  QLIKE on variance, so it is not neutral between the two losses: on 1996-2004 it moves the HMM implied
  vol's RMSE from 0.417 raw to 0.442 calibrated and its QLIKE from 0.289 to 0.366, and against HAR the
  raw HMM implied vol is no different on either loss while the calibrated one is worse on both (post hoc).
  What the comparisons test is the information in each model's output after a log-linear calibration,
  not the model's own forecast as it comes out."
- Why: desk 7 (quant-researcher; answers panel seminar question 1); panel, errors item 3 ("three years of
  history" should be "an expanding window with at least three years": `regimes.forecast` line 102 uses
  `slice(0, i - horizon)`, the module docstring at line 9 says expanding-window OLS). The "three years"
  wording is a method description, so it is proposed, not applied.
- Evidence: `docs/POSTHOC_2026-10.md` (e) (post hoc), S&P 500 1996-2004 table: HMM implied vol raw RMSE
  0.417, calibrated 0.442, raw QLIKE 0.289, calibrated 0.366; raw vs HAR -0.006 to +0.065 (RMSE) and
  -0.025 to +0.089 (QLIKE), no difference on both. The 2024-2026 table follows it in the same section.

### P24. The WRITEUP VIX tables: add the raw VIX row

- Where: WRITEUP.md:544-556 (the RMSE table "RMSE of each forecast of next-month realised vol").
- Proposed: add a row "VIX, uncalibrated (VIX / sqrt(252))" and one sentence: "The benchmark every
  regime model lost to is the calibrated VIX; the raw VIX is biased upward (its mean is 1.43 against a
  realised 1.12 on 1996-2004) and has a higher RMSE than the calibrated one (0.465 against 0.356) but a
  QLIKE of 0.230 (post hoc)."
- Why: desk 8 (trader; confirms and extends panel item 4): the raw VIX row is never tabulated, and on
  development data it has the best QLIKE. The desk's tail statistics (top 5% of days carry 63% of HAR +
  VIX's squared error; every model under-forecast by about 3.4 points for windows starting February
  2020) are the desk's own run and are not printed by a repo script, so they are not proposed here.
- Evidence: `docs/POSTHOC_2026-10.md` (e) (post hoc), the "VIX" rows of the 1996-2004 and 2024-2026
  tables (raw RMSE, calibrated RMSE, raw QLIKE, calibrated QLIKE, raw mean / target mean).

### P25. Convergence of the walk-forward fits (new sentence, WRITEUP methods or each holdout section)

- Proposed: "No published walk-forward checked whether its optimiser converged. The October 2026
  reproductions record it: every refit converged in both VIX holdouts (HMM 49 of 49 and 75 of 75; the
  joint VIX-HMM 97 of 97 and 149 of 149 EM starts) and in the cross-index holdout (per index 95 of 95
  for each of HMM, GJR-GARCH and MSM; 430 of 430 L-BFGS-B starts). The ETF holdout loads its frozen
  checkpoints, so its fits were not re-observed; a full refit on a second machine, which does not
  reproduce the frozen numbers exactly, converged in 1,439 of 1,462 MS-GARCH starts and in every GJR and
  HMM refit (reproduction)."
- Why: desk 10 (quant-dev; confirms the panel modeller's point). Stage S3 of the reopen added the record.
- Evidence: `docs/results/reproductions/REPRODUCTION_2026-10.md`, "Identity reruns after the
  convergence-recording change" table; `docs/results/reproductions/PROVENANCE_2026-10.md`, ETF
  optimiser-call table (walk_forward_msgarch scipy 1462 calls, 1439 converged, 23 not);
  `docs/results/reproductions/etf/convergence.csv` (all reproduction; `examples/reproduce_holdout.py`).

### P26. WRITEUP.md lines 802 and 818-819: two Nasdaq-100 labels rest on an endpoint within 0.0005 of zero

- Old (WRITEUP.md:818-819): "Implied vol adding to intraday data only cleared on the Nasdaq-100."
- Proposed: "Implied vol adding to intraday data only cleared on the Nasdaq-100, and only just: the RMSE
  interval is -0.018 to -0.000, its upper end within 0.0005 of zero. On QLIKE it is -0.053 to +0.001 (no
  difference), and dropping the 63 Nasdaq-100 days whose target averages fewer than 21 sessions makes it
  -0.018 to +0.000 (no difference); either way R1 would be rejected rather than mixed (post hoc)." And
  for the combination row (WRITEUP.md:802): "worse on the Nasdaq-100 and the Dow on RMSE, with both lower
  ends at +0.000; on QLIKE neither is worse (post hoc)."
- Why: desk 11 (quant-dev: print four decimals and call NDX R1 marginal). The verdict file is frozen
  (rule 2) and keeps three decimals; the labels match the rule exactly.
- Evidence: `docs/POSTHOC_2026-10.md` cross-index (a) table (R1 Nasdaq-100 RMSE "gain shown of at least
  0.1%", QLIKE -0.053 to +0.001; P4 Nasdaq-100 and Dow QLIKE no difference) and (c) HAC DM table (R1
  Nasdaq-100 RMSE p 0.060, P4 Nasdaq-100 p 0.086); `docs/DATA_QUALITY_2026-10.md` section 3a
  (`examples/data_quality.py`, 8e454ec; post hoc): "rows kept 3223 of 3286 (63 removed) ... R1 mixed ->
  rejected".

### P27. A data-quality paragraph for the cross-index section (new; WRITEUP after line 796)

- Proposed: "Four data issues sit inside the scored windows and none moves a claim outcome. FRED's VXD
  prints 2.71 on 2021-07-13 between 14.86 and 15.51 (and two suspect prints in 2024 and 2025); removing
  those three Dow days moves no verdict. Two YM sessions in the COVID window are partial (12 of 78
  five-minute bars on 2020-02-28, 9 on 2020-06-30, plus 47 on 2020-02-27) but kept as full-session RV;
  removing the 87 Dow days whose target or features touch them moves two of nine Dow verdicts (SHAR no
  difference -> worse, combination worse -> no difference) and no claim outcome. Six 2014 trading days
  have no bars and are left missing, and because a target needs only 18 of its 21 sessions, 63
  Nasdaq-100 and 21 Dow targets are 18 to 20-session means; dropping the Nasdaq-100 ones turns R1 from
  mixed to rejected (see above). Half days (28 on the Nasdaq-100 and the Dow, 12 on the Russell 2000) are not scaled up; removing every target
  that contains one moves no verdict (post hoc)."
- Why: desk 12 and 17 (data-engineer, model-validator); the `min_periods=horizon-3` rule
  (`regimes.forecast.forward_rv`) is not in the cross-index protocol.
- Evidence: `docs/DATA_QUALITY_2026-10.md` sections 1-4 and the summary (`examples/data_quality.py`,
  8e454ec; reproduction for the facts, post hoc for the blast radii). The 2014 count is A1.

### P28. README.md lines 176-178: "with the same cached data files they give the same forecasts"

- Old (README.md:176-178): "The holdout scripts can be rerun too, and with the same cached data files
  they give the same forecasts (a fresh download can differ where Yahoo revises adjusted prices), however
  the holdouts themselves are spent: a rerun is a reproduction, not a new test."
- Proposed: "The holdout scripts can be rerun too. With the same cached data files the VIX, stock-bond
  and cross-index scripts give the same printed tables on a second machine; the ETF script reproduces
  its result exactly from its saved MS-GARCH checkpoints, but a full refit of the MS-GARCH models on
  another machine moves some losses and interval ends in the third decimal (no verdict moves; see
  docs/results/reproductions/REPRODUCTION_2026-10.md). A fresh download can differ where Yahoo revises
  adjusted prices. The holdouts themselves are spent: a rerun is a reproduction, not a new test."
- Why: desk 13 (data-engineer: the MS-GARCH determinism claim is overstated; the protocol's explanation
  at MSGARCH_CREDIT_HOLDOUT_PROTOCOL.md:193-194, "adjusted closes differ very slightly", is contradicted
  by the two GSPC caches being value-identical over 6,037 rows, and the protocol is frozen). P7 is the
  longer reproduction paragraph; this is the one-sentence fix where the claim is made. S7 (c) will add
  the per-model tolerance comparison and may sharpen the "third decimal" wording.
- Evidence: `docs/results/reproductions/REPRODUCTION_2026-10.md` outcome table and ETF section
  (reproduction; `examples/etf_refit_audit.py`: 0 of 20 refitted walk-forward files byte-identical).

### P29. The back-calculated VIX in the 1990-2004 holdout (new sentence, WRITEUP VIX section)

- Proposed (after WRITEUP.md:540, "fitted and scored with no later data"): "Before 22 September 2003 the
  VIX is Cboe's back-calculation of the current index, not a traded print: 91% of the 1990-2004 VIX file
  and 86% of the scored forecasts rest on it. On the back-calculated days alone, one of the seven
  comparisons moves (VIX-HMM implied vol vs HAR, worse to no difference) (post hoc)."
- Why: desk 17 (data-engineer: the protocol says it at VIX_HOLDOUT_PROTOCOL.md:19-22, the paper does
  not).
- Evidence: `docs/DATA_QUALITY_2026-10.md` section 6 and 6a: "VIX file days 3783, back-calculated 3461
  (91 percent); scored days 2228, of which 1927 (86 percent)"; "verdicts moved: 1 of 7".

### P30. Two target definitions, stated once (new sentence, WRITEUP methods)

- Proposed: "The holdouts score two different targets. The cross-index holdout's is the square root of
  the mean squared 5-minute session RV over the next 21 sessions (regular hours, overnight excluded); the
  VIX and ETF holdouts' is the 21-day standard deviation of close-to-close returns. Each holdout's claims
  compare models on its own target, so no verdict depends on the choice, but levels are not comparable
  across holdouts: session RV carries about 57% to 72% of close-to-close variance."
- Why: desk 17 (data-engineer, quant-researcher).
- Evidence: `docs/DATA_QUALITY_2026-10.md` section 7 (reproduction): session RV^2 / close-to-close r^2
  means 0.58 (Nasdaq-100), 0.57 (Dow), 0.72 (Russell 2000).

### P31. Statements inside frozen files that cannot be edited (disclose in the WRITEUP instead)

Rule 2 freezes these files, so each gets a disclosure sentence where the WRITEUP describes the holdout.
- `docs/results/msgarch_credit_holdout_2026-10-14.txt:1-2`: the two-line `#` header was added by hand
  after the run (desk, model-validator LOW). Proposed for WRITEUP.md near line 900: "The result file is
  the run's output with a two-line header added by hand afterwards; every other line is as printed."
- `docs/MSGARCH_CREDIT_HOLDOUT_PROTOCOL.md:5`, "the claims were chosen from them and approved on
  2026-10-14": no approver is named in a single-author repo (desk, model-validator LOW). Proposed for the
  WRITEUP's MS-GARCH section: "chosen by the author before the freeze", and if the WRITEUP repeats
  "approved", that word replaced. (The WRITEUP does not currently use "approved": `grep -n approv
  docs/WRITEUP.md` finds nothing.)
- `docs/MSGARCH_CREDIT_HOLDOUT_PROTOCOL.md:193-194`, the dry-run difference blamed on adjusted closes:
  see P28.
- `docs/HOLDOUT_PROTOCOL.md:3`, the stock-bond freeze: see P4 and P21.

### P32. WRITEUP.md lines 826-829: the 21-day horizon as a limitation, and the nesting check

- Old (WRITEUP.md:828): "Only the one-month horizon was tested on the holdout."
- Proposed: "Only the one-month horizon was tested on the holdout, by choice: 21 days is the VIX's own
  tenor, the horizon where implied vol is closest to a model-free forecast and so the hardest test for a
  regime term. On development data at 5, 10, 63 and 126 days, with the implied vol matched to the
  horizon (VIX9D, VIX, VIX6M), the HMM probability adds nothing on either loss; that is development
  evidence only (docs/DEV_HORIZONS_2026-10.md)."
  And one sentence where the paper discusses nested comparisons: "A pure-noise regressor added to HAR +
  VIX on development data gives -0.000 to +0.001 (RMSE, no difference), so the nesting penalty that a
  Clark-West adjustment corrects for is two orders of magnitude below the equivalence bounds and would
  move no verdict."
- Why: desk 17 (WRITEUP:829 "lists the 21-day horizon as a limitation rather than a choice"; the nesting
  noise is negligible, quant-researcher, which replaces panel ranked item 3); panel, agreed item 6.
- Evidence: `docs/DEV_CONTINUATIONS_2026-10.md` (a) and (c) (`examples/dev_continuations.py`; development
  data only): HAR + VIX + noise vs HAR + VIX -0.000 to +0.001 RMSE, -0.001 to +0.004 QLIKE.
  `docs/DEV_HORIZONS_2026-10.md` (`examples/dev_horizons.py`, S8 a; development data only, every set fitted
  on common rows): HAR + matching IV + HMM prob vs HAR + matching IV, RMSE: 5 days -0.005 to +0.007, 10
  days -0.004 to +0.010, 21 days -0.004 to +0.012, 63 days -0.005 to +0.021, 126 days -0.033 to +0.009,
  all no difference, and no difference on QLIKE at every horizon. S4a's "worse at 63 days" was an
  own-row fit (the HAR + VIX reference trained on three more years); on common rows it is no
  difference. Caveats: 49 non-overlapping windows at 63 days and 23 at 126; at 126 days the VIX6M makes
  HAR worse (+0.006 to +0.135), so the 126-day row is weak evidence either way.

### P33. README.md line 11 and line 15: "four holdouts" and "Richer regime models did beat the two-state one"

- Old (README.md:11): "On four holdouts (the S&P 500 in 1996-2004 and 2024-2026, ...)".
  Proposed: "On four holdouts, not independent of each other (two are periods of the S&P 500, and the
  Nasdaq-100, Dow and Russell 2000 went through the same crises as the S&P development sample), ...".
- Old (README.md:15-17): "Richer regime models did beat the two-state one, a multifractal model on the
  Russell 2000 and Markov-switching GARCH on gold and emerging markets, ...".
  Proposed: "On RMSE, richer regime models did beat the two-state one, a multifractal model on the
  Russell 2000 (the claim across the three indices was mixed) and Markov-switching GARCH on gold and
  emerging markets (on QLIKE, post hoc, the two assets are oil and Brazil), ...".
- Why: panel, errors item 10 ("four holdouts" reads as four independent tests); panel, errors item 5 and
  desk 3 (MSM is mixed by the paper's own rule; M3 holds on disjoint assets under the two losses); pointer
  00:00 (c) (name the loss).
- Evidence: WRITEUP.md:803 (MSM row "mixed"); `docs/POSTHOC_2026-10.md` MS-GARCH and credit holdout,
  "Claim outcomes under each loss" (M3 confirmed on both losses, on different assets).

### P34. The audit-trail wording (README lines 169-170 and the methods section)

- Old (README.md:169-170): "A git hash is a local commitment made public by the push, not a third-party
  registration. The push times are GitHub's record, not mine."
- Proposed (the model-validator's wording, minus the clause about an archive copy that does not exist
  yet): "Each holdout's protocol and script were committed before its data was opened, on the author's
  clock. For the cross-index and ETF holdouts the freeze commit was public on GitHub 12-14 seconds after it
  was made and 17-18 minutes before the results commit; for the VIX holdout it was public five hours
  before the results. The stock-bond freeze was pushed together with its results, and its data file was
  on disk before the freeze, so that holdout's order rests on local evidence only. The GitHub push and CI
  records that show this are captured in `docs/results/audit/`; they are self-certified prospective
  locking, not third-party registration."
- Why: desk 16 (model-validator Q6); panel item 10. The model-validator's draft also says "and archived
  at the Internet Archive": the lane cannot do that (rule 6, nothing that posts), so the clause stays out
  until Thomas has taken the Wayback snapshots.
- **P34 DECIDED 2026-10-18 by Thomas: (b), no Wayback snapshots.** The archive clause stays out for good; the
  proposed wording above (without it) is the candidate. The README edit itself is Thomas's to make.
- Evidence: `docs/results/audit/README.md` and the two captures beside it (copied in S1); desk,
  model-validator Q6 (push and CI times).

### Flagged items already closed, or not in this repo

- Panel, errors: "worse on none" should be "better on none"; "Nine comparisons per holdout" (the VIX
  holdouts had seven); "MSM and MS-GARCH beat the two-state model" in the abstract. These are in the
  paper draft, which is not in this repo. In the repo: WRITEUP.md:773 "worse on none" is the
  confirmation rule and is correct there; WRITEUP.md:794, :868 and :889 say "nine comparisons" of the
  cross-index and ETF holdouts, which had nine; the README's MSM sentence is P33. Thomas to carry the
  three corrections into the draft.
- Panel, errors: "regimes differ in variance" and "AIC/BIC pick 2 states": P6.
- Panel, errors: README freeze table "see the protocol": fixed by Thomas in 17476b5.
- Panel, errors and desk 16: the GitHub Events and CI captures: committed under `docs/results/audit/`
  in S1. Wayback snapshots, OpenTimestamps and a Zenodo deposit are outside the lane (they post).
- Desk 14 (raw VIX logs) and desk 15 (ETF inputs and checkpoints off pc-lanes, MANIFEST): S1
  (`docs/results/reproductions/logs_2026-10-17/`, `data/MANIFEST.md`); the copy off the box is Thomas's
  `hmm_bundle.ps1`.
- Desk 17: the 60/40 benchmark rebalanced daily at zero cost: P15. The tests nothing covered
  (`forward_rv`, `har_rv`, the QLIKE form, the bootstrap, a prefix-identity test that fails on smoothed
  probabilities): added in S3.
- Desk 4 (allocation execution lag and whipsaw cost): P11-P13, P16.
- Panel seminar question 7 (the 2024-2026 data had already happened when the development period was
  fixed): no sentence in the README or WRITEUP addresses it and no lane number bears on it; left for
  Thomas (a sentence of his own, not a correction).


## S7 pass: power and multiple testing

Written 2026-10-18 (stage S7 a, b). Every number below is printed by `examples/power_multiplicity.py`
(at 2c31339 plus uncommitted files) into `docs/POWER_2026-10.md` and `docs/MULTIPLE_TESTING_2026-10.md`;
class: post hoc, computed from the reproduced forecasts; not a registered test. The script first
recomputes every registered RMSE interval from the saved scored tables: 77 of 77 identical to the
committed text (the four stock-bond intervals are read from its reproduced stdout).

### P17. What each holdout could decide (new; README results paragraph and one line per WRITEUP claims table)

- Proposed (README, after the sentence of P20): "The holdouts were small for the effects in question.
  At one month, an interval as wide as the registered ones shows a difference only when it exceeds about
  0.5% to 2.3% of the reference RMSE for the regime-probability comparisons, and 4% to 18% for the
  comparisons of a regime model's own forecast with HAR + IV, with HAR or with another regime model; smaller effects
  would have read as no difference (post hoc; docs/POWER_2026-10.md)."
- Proposed per claim (paste-ready, for the WRITEUP beside each claims table; "could decide" is the
  interval half-width in percent of the reference loss, a property of the sample and the loss, not of
  the result):
  - Cross-index holdout, P1 (HARQ + IV vs HAR-RV + IV): with 1,513 to 3,297 scored days the registered
    RMSE interval is wide enough that it shows a difference only when the true difference exceeds about
    0.0% to 0.1% of the reference RMSE (0.1% to 0.3% of the reference QLIKE); anything smaller reads as no
    difference.
  - Cross-index holdout, P2 (SHAR + IV vs HAR-RV + IV): with 1,513 to 3,297 scored days the registered
    RMSE interval is wide enough that it shows a difference only when the true difference exceeds about
    0.1% to 0.2% of the reference RMSE (0.2% to 0.3% of the reference QLIKE); anything smaller reads as no
    difference.
  - Cross-index holdout, P3 (HAR-RV + IV + MSM vs HAR-RV + IV): with 1,513 to 3,297 scored days the
    registered RMSE interval is wide enough that it shows a difference only when the true difference
    exceeds about 0.3% to 0.6% of the reference RMSE (1.0% to 1.6% of the reference QLIKE); anything
    smaller reads as no difference.
  - Cross-index holdout, P4 (Combination vs HAR-RV + IV): with 1,513 to 3,297 scored days the registered
    RMSE interval is wide enough that it shows a difference only when the true difference exceeds about
    1.8% to 5.1% of the reference RMSE (4.1% to 10.2% of the reference QLIKE); anything smaller reads as
    no difference.
  - Cross-index holdout, P5 (MSM vs Two-state HMM implied vol): with 1,513 to 3,297 scored days the
    registered RMSE interval is wide enough that it shows a difference only when the true difference
    exceeds about 5.4% to 12.1% of the reference RMSE (13.4% to 24.6% of the reference QLIKE); anything
    smaller reads as no difference.
  - Cross-index holdout, R1 (HAR-RV + IV vs HAR-RV): with 1,513 to 3,297 scored days the registered RMSE
    interval is wide enough that it shows a difference only when the true difference exceeds about 2.2% to
    5.7% of the reference RMSE (6.8% to 10.7% of the reference QLIKE); anything smaller reads as no
    difference.
  - Cross-index holdout, R2 (HAR-RV vs HAR): with 1,513 to 3,297 scored days the registered RMSE interval
    is wide enough that it shows a difference only when the true difference exceeds about 2.6% to 4.3% of
    the reference RMSE (6.5% to 8.8% of the reference QLIKE); anything smaller reads as no difference.
  - Cross-index holdout, R3 (HAR-RV + IV + HMM prob vs HAR-RV + IV): with 1,513 to 3,297 scored days the
    registered RMSE interval is wide enough that it shows a difference only when the true difference
    exceeds about 0.5% to 1.7% of the reference RMSE (1.7% to 3.0% of the reference QLIKE); anything
    smaller reads as no difference.
  - Cross-index holdout, R4 (GJR-GARCH vs HAR-RV + IV): with 1,513 to 3,297 scored days the registered
    RMSE interval is wide enough that it shows a difference only when the true difference exceeds about
    2.8% to 9.9% of the reference RMSE (11.6% to 31.8% of the reference QLIKE); anything smaller reads as
    no difference.
  - MS-GARCH and credit holdout, M1 (MS-GARCH vs GJR-GARCH): with 3,119 to 3,821 scored days the
    registered RMSE interval is wide enough that it shows a difference only when the true difference
    exceeds about 2.4% to 6.8% of the reference RMSE (4.1% to 16.6% of the reference QLIKE); anything
    smaller reads as no difference.
  - MS-GARCH and credit holdout, M2 (HAR + IV + MS-GARCH vs HAR + IV): with 3,119 to 3,821 scored days the
    registered RMSE interval is wide enough that it shows a difference only when the true difference
    exceeds about 0.3% to 1.4% of the reference RMSE (0.6% to 3.4% of the reference QLIKE); anything
    smaller reads as no difference.
  - MS-GARCH and credit holdout, M3 (MS-GARCH vs Two-state HMM implied vol): with 3,119 to 3,821 scored
    days the registered RMSE interval is wide enough that it shows a difference only when the true
    difference exceeds about 3.8% to 18.4% of the reference RMSE (8.7% to 34.2% of the reference QLIKE);
    anything smaller reads as no difference.
  - MS-GARCH and credit holdout, M4 (HAR + IV + MS-GARCH prob vs HAR + IV): with 3,119 to 3,821 scored
    days the registered RMSE interval is wide enough that it shows a difference only when the true
    difference exceeds about 0.5% to 1.8% of the reference RMSE (1.1% to 6.1% of the reference QLIKE);
    anything smaller reads as no difference.
  - MS-GARCH and credit holdout, M5 (MS-GARCH vs HAR + IV): with 3,119 to 3,821 scored days the registered
    RMSE interval is wide enough that it shows a difference only when the true difference exceeds about
    3.7% to 11.7% of the reference RMSE (15.3% to 29.8% of the reference QLIKE); anything smaller reads as
    no difference.
  - MS-GARCH and credit holdout, C1 (HAR + IV + credit vs HAR + IV): with 3,119 to 3,821 scored days the
    registered RMSE interval is wide enough that it shows a difference only when the true difference
    exceeds about 1.3% to 2.9% of the reference RMSE (3.8% to 8.1% of the reference QLIKE); anything
    smaller reads as no difference.
  - MS-GARCH and credit holdout, C2 (HAR + credit vs HAR): with 3,119 to 3,821 scored days the registered
    RMSE interval is wide enough that it shows a difference only when the true difference exceeds about
    0.5% to 3.5% of the reference RMSE (1.5% to 17.5% of the reference QLIKE); anything smaller reads as
    no difference.
  - MS-GARCH and credit holdout, R1 (HAR + IV vs HAR): with 3,119 to 3,821 scored days the registered RMSE
    interval is wide enough that it shows a difference only when the true difference exceeds about 3.8% to
    6.3% of the reference RMSE (14.4% to 19.7% of the reference QLIKE); anything smaller reads as no
    difference.
  - MS-GARCH and credit holdout, R2 (GJR-GARCH vs HAR + IV): with 3,119 to 3,821 scored days the
    registered RMSE interval is wide enough that it shows a difference only when the true difference
    exceeds about 3.9% to 9.4% of the reference RMSE (13.9% to 28.7% of the reference QLIKE); anything
    smaller reads as no difference.
  - S&P 500, 1996-2004, (1) (VIX vs HAR): with 2,228 scored days the registered RMSE interval is wide
    enough that it shows a difference only when the true difference exceeds about 6.5% of the reference
    RMSE (16.3% of the reference QLIKE); anything smaller reads as no difference.
  - S&P 500, 1996-2004, A (HAR + VIX vs HAR): with 2,228 scored days the registered RMSE interval is wide
    enough that it shows a difference only when the true difference exceeds about 5.4% of the reference
    RMSE (13.4% of the reference QLIKE); anything smaller reads as no difference.
  - S&P 500, 1996-2004, (3) (HAR + HMM prob vs HAR): with 2,228 scored days the registered RMSE interval
    is wide enough that it shows a difference only when the true difference exceeds about 1.7% of the
    reference RMSE (7.2% of the reference QLIKE); anything smaller reads as no difference.
  - S&P 500, 1996-2004, B (HAR + VIX + HMM prob vs HAR + VIX; HAR + VIX + VIX-HMM prob vs HAR + VIX): with
    2,228 scored days the registered RMSE interval is wide enough that it shows a difference only when the
    true difference exceeds about 1.8% of the reference RMSE (5.7% to 5.9% of the reference QLIKE);
    anything smaller reads as no difference.
  - S&P 500, 1996-2004, C (HMM implied vol vs HAR; VIX-HMM implied vol vs HAR): with 2,228 scored days the
    registered RMSE interval is wide enough that it shows a difference only when the true difference
    exceeds about 10.1% to 11.7% of the reference RMSE (31.9% to 34.9% of the reference QLIKE); anything
    smaller reads as no difference.
  - S&P 500, 2024-2026, (1) (VIX vs HAR): with 676 scored days the registered RMSE interval is wide enough
    that it shows a difference only when the true difference exceeds about 6.4% of the reference RMSE
    (19.4% of the reference QLIKE); anything smaller reads as no difference.
  - S&P 500, 2024-2026, A (HAR + VIX vs HAR): with 676 scored days the registered RMSE interval is wide
    enough that it shows a difference only when the true difference exceeds about 6.0% of the reference
    RMSE (16.4% of the reference QLIKE); anything smaller reads as no difference.
  - S&P 500, 2024-2026, (3) (HAR + HMM prob vs HAR): with 676 scored days the registered RMSE interval is
    wide enough that it shows a difference only when the true difference exceeds about 5.0% of the
    reference RMSE (10.6% of the reference QLIKE); anything smaller reads as no difference.
  - S&P 500, 2024-2026, B (HAR + VIX + HMM prob vs HAR + VIX; HAR + VIX + VIX-HMM prob vs HAR + VIX): with
    676 scored days the registered RMSE interval is wide enough that it shows a difference only when the
    true difference exceeds about 1.1% to 2.3% of the reference RMSE (3.6% to 6.7% of the reference
    QLIKE); anything smaller reads as no difference.
  - S&P 500, 2024-2026, C (HMM implied vol vs HAR; VIX-HMM implied vol vs HAR): with 676 scored days the
    registered RMSE interval is wide enough that it shows a difference only when the true difference
    exceeds about 8.1% to 10.1% of the reference RMSE (10.5% to 13.8% of the reference QLIKE); anything
    smaller reads as no difference.
  - Stock-bond, 1962-2004, level A (A implied correlation vs trailing 63-day correlation): with 9,878
    scored days the registered RMSE interval is wide enough that it shows a difference only when the true
    difference exceeds about 14.9% of the reference RMSE; anything smaller reads as no difference.
  - Stock-bond, 1962-2004, level B (B implied correlation vs trailing 63-day correlation): with 9,878
    scored days the registered RMSE interval is wide enough that it shows a difference only when the true
    difference exceeds about 13.1% of the reference RMSE; anything smaller reads as no difference.
  - Stock-bond, 1962-2004, level, trailing 252-day (trailing 252-day correlation vs trailing 63-day
    correlation): with 9,878 scored days the registered RMSE interval is wide enough that it shows a
    difference only when the true difference exceeds about 8.0% of the reference RMSE; anything smaller
    reads as no difference.
  - Stock-bond, 1962-2004, level, EWMA (EWMA correlation (0.97) vs trailing 63-day correlation): with
    9,878 scored days the registered RMSE interval is wide enough that it shows a difference only when the
    true difference exceeds about 2.8% of the reference RMSE; anything smaller reads as no difference.
- Why: scope S7 (a); panel ranked item 2 (minimal detectable effect per comparison); desk 9. The
  equivalence bound (POSTHOC (b), repeated in POWER section 2) says what the realised interval excludes;
  this says what an interval of that width could ever have shown.
- Evidence: `docs/POWER_2026-10.md` sections 2 and 3. The README ranges: regime-probability rows
  (cross-index R3 0.5% to 1.7%, ETF M4 0.5% to 1.8%, S&P B 1.1% to 2.3%); own-forecast rows (cross-index
  P5 5.4% to 12.1%, ETF M3 3.8% to 18.4% and M5 3.7% to 11.7%, S&P C 8.1% to 11.7%). The README sentence
  rounds these; Thomas may prefer the exact ranges.

### P18. The family size, and what survives a family-wise correction (new; README and WRITEUP)

- Proposed (README, after P17): "The four forecasting holdouts and the stock-bond check made 81
  registered interval comparisons in five families (27 cross-index, 36 ETF, 7 on each S&P holdout, 4
  stock-bond), each judged by its own 95% interval with no correction for multiplicity. With Holm's
  correction across all 81 (post hoc, RMSE, the registered bootstrap inverted to p-values) 9 of the 30
  'better' or 'worse' verdicts survive. Every 'adds nothing' claim still holds, since a correction can
  only make a null easier to hold; the claims that rest on single marginal verdicts do not survive: the
  VIX improving HAR (claim A) on both S&P holdouts and the regime models' own forecasts losing to HAR
  (claim C) on 1996-2004 become not shown, the cross-index MSM-beats-HMM (P5) and implied-vol (R1)
  claims become rejected, and the ETF MS-GARCH-beats-HMM (M3) and implied-vol (R1) claims become mixed."
- Proposed (WRITEUP limitations): "Multiplicity: the verdicts are per comparison at 95% with no
  correction. docs/MULTIPLE_TESTING_2026-10.md applies Holm within each family and across all 81
  registered comparisons, under both losses, with bootstrap and HAC Diebold-Mariano p-values; the
  registered rule stays the verdict."
- Why: scope S7 (b); joint desk finding 12; desk 9 ("no multiplicity correction anywhere").
- Evidence: `docs/MULTIPLE_TESTING_2026-10.md` sections 1-3: RMSE, bootstrap p-values: 30 non-null
  verdicts, 13 survive Holm within their family, 9 across all (Nasdaq-100 and Dow R2; oil M5 and R2;
  gold M5 and R1; EEM M3; stock-bond A and B); DM p-values: 7 and 3. QLIKE, bootstrap: 18 non-null, 8
  and 4. Claim outcomes that move under Holm (family or all): 7 of 24, listed above; none of R3, M4, B,
  C1, R4, R2 (ETF) moves. Caveats in the doc: the stock-bond p-values are a normal approximation from the
  printed 3-decimal intervals (no stock-bond forecasts were saved), and the DM and bootstrap p-values
  disagree on some rows (2024-2026 A: bootstrap 0.036, DM 0.215), so the DM column is the stricter
  reading.

## S8 pass: the machine-learning continuation

Written 2026-10-18 (stage S8 e). Rule 8 as amended for S8: nothing from S8 enters a claim sentence; this
is the one proposal sentence naming the continuation. Not applied.

### P19. One sentence naming the development-only ML continuation (new; WRITEUP, after P32's sentence at line 829)

- Proposed (WRITEUP, after the sentence P32 adds at line 829): "A development-only continuation
  (docs/DEV_ML_2026-10.md; S&P 500 2005-2023, no holdout, not a claim) asked whether a flexible learner
  finds regime information the linear nest misses: across OLS, ridge, LASSO, random forest and LightGBM
  at 5 to 126 days and an MLP at 5 to 63 days, adding the HMM probability was 'better' in 1 of 46
  comparisons (23 learner-horizon pairs, each on RMSE and QLIKE), in a learner that is itself worse than
  HAR + VIX there, and no learner on HAR + VIX inputs beat HAR + VIX."
- Revised 2026-10-18 17:05Z (run 14): the earlier wording ("ridge, LASSO, random forest, LightGBM and an
  MLP at 5 to 126 days") omitted OLS, which the 46 include, and put the MLP at 126 days, where the
  protocol does not fit it. The coverage now matches the clause `examples/dev_ml_summary.py` prints in
  DEV_ML_2026-10.md, "Reading" (no count changed).
- Why: scope S8 (e); answers the referee objection "you only tested a linear nest" against claim B
  (protocol `docs/ML_REGIME_PROTOCOL_DRAFT.md`, committed before the first fit).
- Evidence (development data only; `examples/dev_ml_summary.py` printing from the tables of
  `examples/dev_ml_regime.py`, 2,000 bootstrap draws): table (i) F1 vs F0: 1 'better' (LightGBM h = 126,
  RMSE, -0.062 to -0.010; noise row -0.008 to +0.000), 1 'worse', 44 no difference; noise row 'better' in 2
  of 46; LightGBM F0 vs HAR + VIX at h = 126 'worse' (RMSE +0.007 to +0.084). Table (ii): 0 'better' of 38,
  18 'worse'. Detectors (`examples/dev_regime_detectors.py`, OLS, h 5/21/63): k-means, GMM, change-point and
  spectral inputs 'better' than HAR + VIX in 0 of 36, 'worse' in 4. Uncorrected counts: about 1.2 'better'
  in 46 are expected by chance at 2.5% one-sided.
- Open: the LSTM/GRU race (S8 c) was running when this was written; if it scores any recurrent forecast
  'better' than HAR + VIX, the sentence's last clause needs that count (DEV_ML_2026-10.md, "Reading").
  Interim (2026-10-18 15:18Z, 8 of 18 race fits scored, `examples/dev_ml_race.py --markdown-only` then
  `examples/dev_ml_summary.py`, development data only): LSTM/GRU 'better' than HAR + VIX in 0 of 16
  comparisons, 'worse' in 13; the clause stands so far. Recheck when the race finishes.
  Interim 2 (2026-10-18 16:06Z, 10 of 18 race fits, same two scripts at e290471 plus uncommitted files,
  development data only): 'better' in 0 of 20, 'worse' in 14. The new fit, GRU F0 at h = 5, has the lowest
  point RMSE and QLIKE at h = 5 (top of both MCS rankings, p = 1.000) but is 'no difference' against HAR + VIX
  (RMSE -0.026 to +0.022, QLIKE -0.040 to +0.013); the clause "no learner ... beat HAR + VIX" stays true.
  Detectors now include the h = 21 learner part (lasso, chosen by the race rule; `examples/dev_regime_detectors.py
  --part learner`, 2026-10-18 15:29Z): 'better' than F0 in 0 of 48, 'worse' in 5 (was 0 of 36, 4 with OLS only).
  Interim 3 (2026-10-18 16:37Z, same 10 race fits, `examples/dev_ml_race.py --markdown-only` then
  `examples/dev_ml_summary.py` at f0e9ce0 plus uncommitted files, development data only): of the 58
  forecast-loss pairs 'worse' than HAR + VIX in the race, the 10% MCS keeps 55, so the MCS here separates
  almost nothing. If the sentence or a footnote mentions the race, cite the paired verdict against HAR + VIX,
  not MCS membership (the 'top of the MCS ranking' remark in Interim 2 is a ranking, not a test result).
  Interim 4 (2026-10-18 16:50Z, 11 of 18 race fits, same two scripts at e6dad63, development data only): 'better'
  than HAR + VIX in 0 of 22, 'worse' in 15 (new: GRU F1 at h = 5, 'worse' on QLIKE +0.001 to +0.137, 'no
  difference' on RMSE). The clause stands.
  Holdout MCS, the same question (post hoc, computed from the reproduced forecasts; not a registered test;
  `examples/posthoc_stats.py` at e6dad63 plus uncommitted files, 2026-10-18, new table under each (c) section of
  docs/POSTHOC_2026-10.md): of 45 registered pair-loss intervals that exclude zero, the losing forecast stays in
  the 10% MCS in 15 (cross-index 5 of 12, ETF 7 of 22, S&P 1996-2004 0 of 8, S&P 2024-2026 3 of 3). The holdout
  MCS separates more than the race's, but not enough to stand for a pairwise result. No claim sentence in
  README.md or docs/WRITEUP.md cites MCS membership (checked with grep); if one is added at merge, it should
  cite the paired interval instead.
  Interim 5 (2026-10-18 17:24Z, 12 of 18 race fits, `examples/dev_ml_race.py --markdown-only` then
  `examples/dev_ml_summary.py` at b0500c8 plus uncommitted files, development data only): 'better' than HAR + VIX
  in 0 of 24, 'worse' in 16 (new: GRU F1n at h = 5, 'worse' on QLIKE +0.006 to +0.205, 'no difference' on RMSE).
  The clause stands. Adding the row changes the h = 5 MCS p-values of other forecasts (the set changed); LSTM F1
  at h = 5 stays outside the 10% MCS (p 0.048, was 0.029).
  Interim 6 (2026-10-18 17:36Z, 14 of 18 race fits, `examples/dev_ml_race.py --markdown-only` then
  `examples/dev_ml_summary.py` at d7660f7 plus uncommitted files, development data only): 'better' than HAR + VIX
  in 0 of 28, 'worse' in 19. New: LSTM F0 at h = 63, 'worse' on RMSE (+0.029 to +0.171) and QLIKE (+0.028 to
  +0.263); LSTM F1 at h = 63, 'worse' on RMSE with a lower bound that prints as +0.000 (knife-edge), 'no
  difference' on QLIKE (-0.028 to +0.188). The clause stands. vs_ols.csv gains those two rows; no earlier row changed.
  Final (2026-10-18 20:50Z, 18 of 18 race fits; `examples/dev_ml_race.py --markdown-only` by s8_chain2.sh at
  18:40Z, `examples/dev_regime_detectors.py --part schedule` and `examples/dev_ml_summary.py` at a14e59a plus
  uncommitted files, development data only): LSTM/GRU 'better' than HAR + VIX in 0 of 36 comparisons, 'worse'
  in 20; the sentence's last clause stands and needs no race count. The h = 21 LSTM rerun reproduced byte for
  byte (6 files, 0 differ, race_rerun.log). The refit-schedule check now covers all six non-recurrent learners
  at h = 21: 5 of 20 verdicts move with a one-month shift of the refit dates. The one HMM row that moves is the
  single 'worse' in table (i) (LightGBM h = 21, QLIKE: worse -> no difference), and the noise row reads 'better'
  on QLIKE under LightGBM and the MLP on the later schedule (and loses its 'better' under the random forest).
  The evidence line's "1 'worse'" is therefore fragile; the proposed sentence does not cite it. If a footnote
  quotes table (i), say that one 'better' and one 'worse' in 46 is within what the noise regressor produces (2 'better' in 46), and
  that both depend on the refit dates (`docs/DEV_ML_2026-10.md`, "Reading", refit-schedule bullet). The race
  clause is closed; nothing under P19 is open.

## S9 pass: the benchmark form check

Written 2026-10-19 (stage S9). The scope asks for this proposal as "P20"; P20 was already used by the S6 pass
(README.md lines 11-13), so it is numbered P35. Proposal only (rule 7), not applied.

**APPLIED 2026-10-20, approved by Thomas the same day** (WRITEUP.md lines 529-533). One change from the
proposed text: "changed no 21-day verdict" is narrowed to "on the daily-return target", because on the ES
5-minute RV target at h = 21 one verdict does differ (HAR + VIX against HAR on QLIKE: 'better' in levels,
'no difference' in logs; `docs/DEV_BENCHMARK_FORM_2026-10.md`, Target B, horizon 21).

### P35. Name the form of the HAR + implied vol benchmark (WRITEUP.md lines 529-530)

- Old (WRITEUP.md lines 529-530): "Every signal set is turned into a forecast by the same walk-forward
  regression (`regimes.forecast`), refit quarterly and fitted in logs, ..."
- Proposed: "Every signal set is turned into a forecast by the same walk-forward regression
  (`regimes.forecast`), refit quarterly and fitted in logs, with every volatility input and the target in
  logs (the log-HAR form of Corsi 2009, used for every HAR + implied vol benchmark in this note); on
  development data to 2022 a version with the inputs in levels was never better on RMSE or QLIKE and changed
  no 21-day verdict, ..."
- Why: the implied-horizon-vol study (laptop, 19 Oct, `/opt/hmm-agent/reviews/IHV_RESULTS_2026-10-19.md`,
  "Reading") says MR's HAR + IV benchmark "used the same level-feature, log-target form". It did not: every
  script that builds the benchmark takes np.log of the HAR inputs and of IV / sqrt(252)
  (`examples/vol_forecast_vix.py` lines 104-132, `examples/better_vol_models.py` lines 93-117,
  `examples/msgarch_credit.py` lines 168-186, `examples/intraday_rv.py` lines 117-144,
  `examples/term_structure_regimes.py` lines 105-117). The paper should say so in one clause, because the
  level form is the one that blows up.
- Evidence (development data only, S&P 500 and ES to 2022-12-30, no holdout, not a claim;
  `examples/dev_benchmark_form.py` at feff299 plus uncommitted files, `docs/DEV_BENCHMARK_FORM_2026-10.md`,
  "Answer" and the claims table): within-form verdicts that differ between the two forms 7 of 24, none at the
  paper's target and horizon (daily-return vol, 21 days); every claim sentence the S&P development data can
  speak to (4 of 7) points the same way under the log form; the log-form benchmark has the lower loss in 3 of
  8 target-horizon cells (h = 1 and 5), the level form in none. On the ES 5-minute target at h = 1 the HMM
  probability reads 'better' than HAR + VIX in the log form only (RMSE -0.002 to -0.000, QLIKE -0.004 to
  -0.001, no multiplicity correction): a short-horizon development lead, outside every claim (all are 21-day)
  and not cited in the proposed sentence.
- Reference check: Corsi, F. (2009), "A Simple Approximate Long-Memory Model of Realized Volatility", Journal
  of Financial Econometrics 7(2), 174-196; WRITEUP.md line 519 already cites Corsi for HAR-RV.

## S9 follow-up pass: the desk re-check of 2026-10-20

Written 2026-10-20 (pointer 2026-10-20 13:20 UTC; joint desk review
`/opt/desk-agent/out/DESK_REVIEW_HMM_VRP_2026-10-18.md`, "Next moves after re-check", bucket 1 item 5, and
its findings N7, N10 and the re-check lines 246-247 and 262). All four are proposals only (rule 7); none is
applied by the lane. Line numbers are README.md at 00ee358. No new number: every figure below is already
printed in a committed file, named beside it. P1b is approved by Thomas in advance and is applied by Claude
on the laptop after checking the evidence.

### P1b. README.md line 48, the "Adding the VIX" table row: "draws on 2024-2026"

- Status: **APPLIED 2026-10-20 on Thomas's word** (approved in advance), exactly as proposed; evidence checked
  against POSTHOC_2026-10.md:534 and :628. The sub-note ("cuts forecast error" -> "cuts the RMSE") is NOT applied: not ruled.

- Old (README.md:48, end of the row): "the HMM's own forecast loses to HAR on 1996-2004 and draws on
  2024-2026 |"
- Proposed: "the HMM's own forecast loses to HAR on RMSE on 1996-2004 and, on 2024-2026, is not shown to
  differ on RMSE and beats it on QLIKE |"
- Why: desk re-check line 246 (fitness D; lead's trace): "draws" hides the QLIKE result that the README's
  opening paragraph (P1, applied at feff299) already reports; pointer 00:00 (c) (name the loss).
- Evidence (reproduction and post hoc, `examples/posthoc_stats.py` at e6dad63, `docs/POSTHOC_2026-10.md`):
  1996-2004, comparison 6 "HMM implied vol vs HAR", RMSE +0.016 to +0.094 worse (POSTHOC:534; the same
  interval is the registered claim C entry, WRITEUP.md:567); 2024-2026, comparison 6, RMSE -0.063 to
  +0.023 no difference and QLIKE -0.100 to -0.013 better (POSTHOC:628; the QLIKE interval is printed by
  the frozen script and quoted at WRITEUP.md:571-572; `examples/check_writeup_tables.py` matched it,
  REPRODUCTION_2026-10.md:39-44). On QLIKE the 1996-2004 comparison is also worse (+0.026 to +0.192,
  POSTHOC:534, post hoc), so "on RMSE" in the first clause is a loss name, not a hedge.
- Not part of P1b, for Thomas to rule separately: the same row's "adding the VIX cuts forecast error on
  both" is RMSE; on QLIKE (post hoc) claim A holds on 1996-2004 and is not shown on 2024-2026
  (POSTHOC:545 and :639). Possible wording: "adding the VIX cuts the RMSE on both (about 9% on 1996-2004)".

### P36. README.md lines 12-13 and 21-22: name the loss in the two headline sentences

- Old (README.md:11-13): "... adding a regime probability to a simple HAR forecast with the market's own
  implied vol never made a measurable difference."
  Proposed: "... adding a regime probability to a simple HAR forecast with the market's own implied vol
  never made a measurable difference on RMSE, the registered loss, nor on QLIKE (post hoc)."
  Evidence: registered RMSE verdicts, WRITEUP.md:566 (claim B, both S&P periods), the cross-index result
  file (R3) and the ETF result file (M4); under QLIKE, post hoc, `docs/POSTHOC_2026-10.md`: S&P claim B
  holds on both periods under every loss and block scheme (POSTHOC:546, :640); cross-index R3 "no
  difference" on all three indices under both losses (POSTHOC:123, :132, :141; claim row :159); ETF M4 "no
  difference" on all four assets under both losses (POSTHOC:305, :314, :323, :332). The S7 Holm pass
  moves no null (`docs/MULTIPLE_TESTING_2026-10.md`).
- Old (README.md:20-22): "... however both still had a higher error than HAR plus implied vol on every
  holdout."
  Proposed: "... however both still had a higher RMSE and a higher QLIKE than HAR plus implied vol on every
  index and ETF they were scored on (for MS-GARCH the registered comparison, worse on RMSE on all four
  ETFs; for the multifractal model not a registered comparison)."
  Evidence (post hoc, POSTHOC model confidence set tables, RMSE / QLIKE): MSM against HAR-RV + IV,
  Nasdaq-100 0.370 / 0.277 vs 0.342 / 0.229 (POSTHOC:222, :230), Dow 0.345 / 0.373 vs 0.316 / 0.316
  (:249, :257), Russell 2000 0.312 / 0.125 vs 0.299 / 0.113 (:275, :279); MS-GARCH against HAR + IV, oil
  0.988 / 0.345 vs 0.859 / 0.247 (:425, :432), gold 0.370 / 0.251 vs 0.344 / 0.223 (:455, :459), EEM
  0.494 / 0.281 vs 0.471 / 0.253 (:477, :481), Brazil 0.931 / 0.361 vs 0.868 / 0.316 (:501, :507).
  Registered M5 (MS-GARCH vs HAR + IV): worse on RMSE on all four; on QLIKE (post hoc) worse on oil only
  (POSTHOC:306, :315, :324, :333).
- Why: desk re-check line 247 (model-validator D: README.md:12-13 and :21-22 name no loss); pointer 00:00 (c).
- Interaction: P33 rewrites the first half of the sentence at line 20 ("On RMSE, richer regime models did
  beat ..."); P36's second change is to its last clause and reads with or without P33.

### P28b. README "Reproducing the numbers" (lines 188-192) and WRITEUP "Reproduce" (lines 965-966): the per-holdout reproduction outcome

Supersedes P28's proposed text (P7 stays the longer optional paragraph). Class of every outcome named:
reproduction, not a new test.

- Old (README.md:189-192): "The data pulls are cached and the bootstrap is seeded, so reruns of the
  development scripts are deterministic. The holdout scripts can be rerun too, and with the same cached
  data files they give the same forecasts (a fresh download can differ where Yahoo revises adjusted
  prices), however the holdouts themselves are spent: a rerun is a reproduction, not a new test."
- Proposed (README): "The data pulls are cached and the bootstrap is seeded, so reruns of the development
  scripts are deterministic. The holdout scripts can be rerun too, however the holdouts themselves are
  spent: a rerun is a reproduction, not a new test. In October 2026 each was rerun on a second machine from
  the cached data files (docs/results/reproductions/REPRODUCTION_2026-10.md). Both VIX holdouts and the
  stock-bond holdout reproduced every number in the write-up's tables. The cross-index holdout, run from
  the committed 5-minute RV caches because the licensed bar files were not on that machine, reproduced
  every table number, but not byte for byte: the printed last-fit MSM parameter b differs in the third
  decimal on each index. The ETF holdout reproduced exactly when re-scored from its frozen MS-GARCH
  checkpoints; a full refit of the MS-GARCH models did not reproduce those checkpoints (none of the 20
  walk-forward files is identical, the largest RMSE change is 0.005), and no per-asset verdict or claim
  outcome moved on RMSE or QLIKE. A fresh download can differ where Yahoo revises adjusted prices."
- Old (WRITEUP.md:965-966): "Every number and figure in this note comes straight from those scripts. The
  raw data pull is cached, so reruns are deterministic."
- Proposed (WRITEUP): "Every number and figure in this note comes straight from those scripts. The raw data
  pull is cached and the bootstrap is seeded, so reruns of the development scripts are deterministic. The
  holdouts are spent, and a rerun of one is a reproduction, not a new test. In October 2026 each holdout
  was rerun on a second machine (docs/results/reproductions/REPRODUCTION_2026-10.md): the two VIX
  holdouts and the stock-bond holdout reproduced every number in the tables above; the cross-index holdout
  reproduced every table number but not byte for byte (one printed MSM parameter differs in the third
  decimal on each index); the ETF holdout reproduced exactly from its frozen MS-GARCH checkpoints, while a
  full MS-GARCH refit did not reproduce them (largest RMSE change 0.005) and moved no verdict on RMSE or
  QLIKE."
- Why: desk re-check N7 and line 262 (model-validator D; lead verified both texts): README:179-182 (now
  188-192) says reruns "give the same forecasts" against REPRODUCTION_2026-10.md:28-34, and the WRITEUP
  does not cite the note. "Reruns are deterministic" in the WRITEUP is the same overstatement for the ETF
  refit.
- Evidence (reproduction): REPRODUCTION_2026-10.md:28-34 (outcome table; the cross-index chain run exit 1
  on absent bar files, the wrapper's 3 differing lines; ETF 0 of 20 files equal), :39-44 (52 VIX and
  stock-bond numbers checked, 0 mismatches, `examples/check_writeup_tables.py`), :203-215 (largest RMSE
  change 0.0051, MS-GARCH Brazil; 0 of 36 verdicts moved on each loss, `examples/compare_forecasts.py`),
  :216-222 (cross-index `b` differs by 0.003, 0.001, 0.001).
- Unsure: "reruns of the development scripts are deterministic" is kept from the current README. The lane
  checked it for its own development scripts on pc-lanes (DEV_* reruns byte-identical), not for
  `examples/msgarch_credit.py` across machines, which refits MS-GARCH like the ETF holdout.

### N10 (no proposal needed): settings.json rewrite in legacy checkpoint directories

Written directly into `docs/results/reproductions/REPRODUCTION_2026-10.md` (a working doc), section "What
a reader can check". No README or WRITEUP change proposed.
