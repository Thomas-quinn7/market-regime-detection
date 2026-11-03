# Paper roadmap: what would strengthen WRITEUP.md (as of 3 November 2026)

This is a working list for turning `docs/WRITEUP.md` from a write-up into a paper. Each item has its
status, who does it, and where the evidence is, so the work can be picked up again at any time.
Line numbers refer to `docs/WRITEUP.md` as of commit 18d714a. Check them before editing, because
they move once text changes.

- Prose and claim wording: Thomas writes or approves every change.
- Analyses: run only on development data or the spent holdouts, and labelled post hoc. No new
  holdout opens before 31 January 2027.

Sources for this list:

- Critical review of WRITEUP.md at a8e5a29 (2 November 2026). Overall 3 of 5: the research is
  about a 4, the write-up as a paper about a 2. `examples/check_writeup_tables.py` matched 52 of
  52 numbers.
- Panel reviews of 17 and 25 October: their Part B fix list, related-work list and contribution
  sentence.
- `docs/GW_QLIKE_2026-11.md`, the post hoc results of 3 November.

## Status at a glance

| # | Item | Owner | Status |
|---|---|---|---|
| 1 | Narrow the headline claim (h = 21, which models; MS-HAR untested) | Thomas | open, most important |
| 2 | Decide and report the loss each verdict rests on (RMSE / QLIKE var) | Thomas | open, needs decision |
| 3 | Bring POWER, POSTHOC, MULTIPLE_TESTING and GW_QLIKE into the text | Thomas | open |
| 4 | Restructure into a paper (abstract, related work, conclusion, appendix) | Thomas | open |
| 5 | Part B fixes B2, B4, B5, B6 | Thomas | open (B1 and B3 done on main, 18d714a) |
| 6 | Line-level fixes in WRITEUP.md | Thomas | open |
| 7 | Simulated-DGP direct test | Claude, on Thomas's yes | not started |
| 8 | Intervals on the correlation ladder, or cut it | Claude / Thomas | not started |
| 9 | Verify the development-determinism sentence | Claude, on Thomas's yes | not started |
| 10 | Pointer note in POSTHOC_2026-10.md | Claude, on Thomas's yes | not started |
| 11 | MS-HAR + IV competitor | decided: not built, stated as a limitation | closed (option a) |
| 12 | Giacomini-White and QLIKE on variance forecasts | Claude | done, `docs/GW_QLIKE_2026-11.md` |

## 1. Narrow the headline claim (most important)

The paper says regime models add nothing. But every holdout tested only the 21-day horizon, and
none included a coefficient-switching MS-HAR, where the HAR coefficients change by regime.

- Kilic (Fed FEDS 2025-061r1) finds MSHAR best at h = 1 on the S&P 500, even with log VIX among the
  predictors.
- Ding et al. (2025) find regime-switching HAR beats linear HAR at weekly and monthly horizons.

Details are in the workspace literature check, `deep-research-vol/litcheck-2026-11-01/LITCHECK.md`.

The claim the evidence supports: at a one-month horizon, with implied vol already in a HAR
benchmark, a two-state HMM probability, MSM and MS-GARCH add no measurable accuracy across four
holdouts whose protocols were pushed before the data was opened.

Then state as a limitation that coefficient-switching MS-HAR was not tested, and that Kilic and
Ding find gains at short horizons.

Since 3 November there is also the VIX 2024-2026 exception (item 2), which has to appear next to
this claim.

## 2. Which loss each verdict rests on (needs Thomas's decision)

RMSE on the vol level is the registered loss, but it is not robust to a noisy proxy (Patton 2011).
QLIKE was added post hoc in `docs/POSTHOC_2026-10.md`. That version fed QLIKE a squared mean-vol
forecast, which is biased low by exp(s^2), a factor of 1.06 to 1.28. `docs/GW_QLIKE_2026-11.md`
re-scores QLIKE on the correct variance forecast ("QLIKE var"). Its plan's reading rule says that
where the two QLIKE versions disagree, the paper quotes QLIKE var. If adopted:

| Claim | RMSE (registered) | QLIKE (POSTHOC) | QLIKE var |
|---|---|---|---|
| Cross-index R1 | mixed | rejected | rejected |
| ETF R1 | confirmed | mixed | confirmed |
| VIX 1996-2004 C | holds | not shown | not shown |
| VIX 2024-2026 A | holds | not shown | not shown |
| VIX 2024-2026 B (regime adds nothing once the VIX is in) | holds | holds | **fails** |

VIX 2024-2026 claim B under QLIKE var: HAR + VIX + HMM prob beats HAR + VIX, dQLIKE -0.0396 to
-0.0027. It is weak evidence:

- RMSE shows no difference;
- the sample is 676 days, about 32 non-overlapping months;
- it is post hoc;
- the GW test shows a similar gain on calm and stressed days, so it is not a regime-timing effect.

It still has to be reported, not left out. Wording guidance is in `docs/GW_QLIKE_2026-11.md`, "For
Thomas to decide".

Cross-index P3, P4, P5 and R4 cannot be scored under QLIKE var (see that file). Say so wherever
QLIKE var is quoted for the cross-index holdout.

## 3. Bring existing results into the text

The October and November analyses are not in WRITEUP.md, which has no mention of Holm, equivalence
bounds, DM tests or model confidence sets.

- **Bounds on the main null** (`docs/POWER_2026-10.md` section 3). R3, "the HMM probability adds
  nothing", rules out RMSE gains above 0.5 to 1.7% (QLIKE 1.7 to 3.0%). That turns "no
  difference" into "at most about 1%".
- **QLIKE beside RMSE** in every claims table, using the loss chosen in item 2.
- **Holm families** (`docs/MULTIPLE_TESTING_2026-10.md`, 81 comparisons). Name the family for each
  claim and lead with the within-family result.
- **DM and MCS** from POSTHOC. Note that POSTHOC's DM p-values use a Bartlett 20-lag variance,
  which is oversized for 21-day overlapping losses: 8 of 37 rejections go away under the
  rectangular kernel (`docs/GW_QLIKE_2026-11.md`). The bootstrap verdicts are unaffected.
- **Giacomini-White.** No state-dependent gain from any regime model: 7 Holm rejections of 36, 0
  leads. Where the test can tell, the HMM's own forecast loses more when the HMM says high vol.
  This answers the obvious referee question, "maybe it wins in spikes".

## 4. Make it a paper

- Add a declarative title, an abstract with the headline numbers, one contribution sentence (the
  17 October panel's section 5 sentence is still the right one), a related-work section (the panel
  list in `HMM_PAPER_REVIEW_PANEL_2026-10-17.md`), and a conclusion.
  - The paper currently ends on "Possible extensions" (line 987). That section is out of date: its
    "full arc" stops at macro quadrants and leaves out the VIX, the four holdouts, MSM and
    MS-GARCH.
- Keep one question in the body: does a filtered two-state HMM beat HAR + implied vol out of
  sample?
  - The body is the four holdouts plus the diagnosis ("Three more attempts... and why it loses",
    line 604).
  - Keep stock-bond (line 435) as a short section. It supports the argument: even where the state
    really is hidden, the HMM loses.
- Move these to an appendix or cut them: allocation (line 292), the Absorption Ratio (line 255),
  turbulence (line 222) and macro quadrants (line 388).
- Literature: "IV helps HAR" is a known replication (Blair, Poon and Taylor 2001), so present it
  as a replication, not as new. Citations are inline only at the moment, with no reference list,
  and the 17 October panel flagged some to check by hand.

## 5. Part B fixes still open (25 October panel review)

The details are in `VRP_HMM_PANEL_REVIEW_2026-10-25.md` at the workspace root.

- **B2:** citation abstract and a v1.0.0 tag.
- **B4:** name the loss and the Holm family for each claim. This overlaps items 2 and 3.
- **B5:** the README landing page.
- **B6:** the WRITEUP contradictions in item 6.

B1 (VIX source per index) and B3 (reproducibility wording) were applied and merged to main in
18d714a.

## 6. Line-level fixes in WRITEUP.md

- **Lines 143 and 166 contradict each other** on the state count: "it holds up" versus "the
  criteria favour more states". `docs/DEV_K_STATES_2026-10.md` supports line 166.
- **Line 534** calls the VIX "the market's own view" of the next 30 days. It is the price of
  30-day variance and includes the variance risk premium.
- **Line 417, the macro verdict**, "This one does not work", rests on Sharpe 0.72 versus 0.82. But
  lines 368 to 370 say a Sharpe on 16 years is pinned only to about plus or minus 0.4, and the
  macro sample is 12 years. A negative verdict needs the same interval standard as a positive one.
  This is moot if macro moves to an appendix with that caveat.
- **Absorption Ratio lifts of 1.37 and 1.82** (lines 271 and 272) have no intervals. Alerts firing
  on 23% of days are autocorrelated, so the lifts are weaker than they read. This is moot if the
  section is cut.
- **The look-ahead ladder** (lines 11, 89 and 98). The smoothed probability sees the very window it
  forecasts, yet lifts the correlation only from 0.57 to 0.61. That shows the correlation measure
  is insensitive, not that look-ahead is harmless. Cut it to one paragraph, or see item 8.
- **The simulation's two-level arm** draws from the HMM's own model class, so winning there only
  shows the estimator works. "The S&P is closer to the drift market" is an inference from which
  model wins, not a test. See item 7.
- **Line 742 onward** ("never added anything... each reason follows from two states") claims more
  than RMSE-only tables show. Rewrite it after items 1 and 2.
- **Naming.** Call the HMM's output "HMM model vol" so it is not confused with option-implied vol.
  Say that the VIX-holdout "HAR" uses absolute daily returns and is not Corsi's HAR-RV.
- **"Honest"** appears 15 times in WRITEUP.md. Use it once at most.
- **FIXES P29:** the back-filled VIX in the 1990-2004 holdout is still not disclosed.
- **README:** the sentence saying development-script reruns are deterministic has not been
  verified. `msgarch_credit.py` refits MS-GARCH, and the ETF refit did not reproduce across
  machines. Narrow the sentence, or see item 9.
- **`examples/msgarch_credit_holdout.py`** names `^VIX` in its docstring while the code uses
  `VIXCLS`. The script is frozen, so leave it unedited and mention the mismatch in a footnote if it
  matters.

## 7 to 10. Analyses Claude can run on Thomas's yes

Each runs post hoc, on development or spent data, with results in a new `docs/` file and no edits
to the paper text.

7. **Simulated-DGP direct test** (about an hour, development data only). Using the existing sim
   code, compare three real-data statistics against each simulated market's distribution of them:
   the switch rate (13.3 a year), the episode lengths (59% last 5 days or less) and how often the
   probability is pinned. This makes "the S&P is closer to the drift market" a test. The laptop is
   RAM-limited (8 GB), so use fewer seeds or the desktop.
8. **Block-bootstrap intervals on the correlation ladder** (about 30 minutes), or cut the ladder
   to one paragraph, which is preferred.
9. **Development-determinism check:** rerun `examples/msgarch_credit.py` and compare with the
   committed output. This is a long MS-GARCH refit, so wait until RAM is free or use the desktop.
10. **Pointer note in `docs/POSTHOC_2026-10.md`** directing readers to `docs/GW_QLIKE_2026-11.md`
    for the exp(s^2) bias in its QLIKE column and the DM kernel. Only a pointer would be added;
    POSTHOC's results stay as they are.

## 11. MS-HAR (closed: option a)

Thomas chose on 2 November to state MS-HAR as a limitation (item 1) and not to build it. The
regime-horizon pilot that was meant to be the MS-HAR + IV competitor stopped on 1 November, when
its simulation gate failed. Reopen it only if the paper later targets a journal. That would need
decisions on the pilot's open protocol choices and several days of work.

## Not worth doing

- **More estimators.** K = 3 to 4 Student-t, MSM, MS-GARCH, the H1 tail pilot and the MS-TVTP
  horizon pilot have all failed or been stopped. Presenting the existing results better will change
  the paper more than another model would.

## Suggested order when resuming

1. Item 2 decision, then item 1, since everything else hangs off the claim.
2. Item 3, then item 4 (structure), then items 5 and 6.
3. Items 7 to 10 can run in parallel with the writing on Thomas's yes.
4. Re-run `examples/check_writeup_tables.py` after every text change that touches a number.
