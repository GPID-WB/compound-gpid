---
type: work-report
title: "Add headcount function"
date: 2026-11-25
status: completed
size: quick
---

# Add headcount function

## Asked

"Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846."
Restated: add an exported `headcount()` that returns sum(weight where welfare < line) / sum(weight), with tests. `read_survey()` is left alone.

## Risk

Every line was no. New function, no existing number moves (1); data is the synthetic survey (2, inferred); no personal data (3); nothing deleted (4); no new dependency, one new export (5); 3 files plus NAMESPACE (6); checks named (7).

## Changed

| File | What changed and why |
|---|---|
| R/headcount.R | New `headcount()`. Strictly below the line; stops on missing columns, bad `line`, NA welfare, NA or non-positive weight. |
| tests/testthat/test-headcount.R | Toy-survey value, strict inequality, weighting, error cases. |
| NAMESPACE | `export(headcount)`. |

## Checks

| Check | Command | Exit code | Verdict |
|---|---|---|---|
| Tests fail before the function exists | `Rscript -e 'devtools::test(filter="headcount")'` | 0 (FAIL 4, "could not find function") | verified |
| All tests pass after | `Rscript -e 'devtools::test()'` | 0 (FAIL 0, PASS 11) | verified |
| Toy-survey value independent of R | `awk` over inst/extdata/survey.csv | 0 (7 / 45.5 = 0.153846) | verified |

## Evidence

- Commit the checks ran on: 1d1ba3f+changes
- Digest of each output file the change produced or moved: R/headcount.R e4cd66d84a60e44aaf6a88c09824a943d2f58786; tests/testthat/test-headcount.R 89ea6c7a93a13669cd28ff465189f5c86c586f45 (new files, no baseline)
- Validation, for a number: headcount(read_survey()) = 0.1538462; the human expected 0.153846 before the check ran, and awk gave 7 / 45.5 = 0.153846.

## Self-review

| Principle | Verdict | Finding, with file and line |
|---|---|---|
| P3 Deterministic by default | PASS | The value comes from code (R/headcount.R:25) and the test recomputes it as 7 / 45.5. No sampling. |
| P4 Prove it works | PASS | Test failed first, passes now, and the value matches an independent awk calculation and the human's expectation. One test tolerance of mine was too tight and I fixed the test, not the function. |
| P6 Smallest change | PASS | Two new files and one NAMESPACE line. No new dependency, no edit to read_survey. |

review-mode: self-review

## Not checked

R CMD check and documentation build (no man/ page generated; roxygen was not run). Behaviour on data that is not a data.table, such as a plain data.frame, was not tested. .cg-docs/verification.md is still draft, with Run "not found".

## Noticed but not touching

- verification.md outputs map does not list headcount().
- read_survey() has untested error branches (missing columns, non-positive welfare, duplicate hhid), as verification.md already notes.
