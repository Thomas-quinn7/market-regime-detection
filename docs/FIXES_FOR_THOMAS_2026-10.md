# Fixes for Thomas, October 2026 reopen

Running list of text changes from the reopen lane. Factual corrections (a wrong number, count, date or
runtime) are applied on the branch and listed here with old and new text; claim-wording changes are
proposals only and are never applied. The full list over every sentence the desk review and the panel
flagged is stage S6 and is added at the end of the lane; entries before that are the corrections applied
while earlier stages found them.

## Applied (factual corrections)

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

## Proposed (claim wording; not applied)

To be filled in stage S6.
