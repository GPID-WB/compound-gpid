---
type: work-report
title: "Weighted household headcount"
date: 2026-11-25
status: completed
size: quick
---

# Weighted household headcount

## Asked

Add headcount(dt, line = 3), the weighted household share below the line, and a test. Expected toy survey value: 0.153846.

## Risk

Lines 1 and 2: this calculates an estimate and the configuration records no data classification approval. The human approved the stated contract and access to the synthetic survey by saying "Proceed."

## Changed

| File | What changed and why |
|---|---|
| R/headcount.R | Calculate the weighted share and reject invalid inputs. |
| NAMESPACE | Export headcount. |
| man/headcount.Rd | Document the public function. |
| tests/testthat/test-headcount.R | Check survey result, cutoff, weights, and invalid weights. |

## Checks

| Check | Command | Exit code | Verdict |
|---|---|---|---|
| Full test suite | `Rscript -e 'devtools::test(stop_on_failure = TRUE)'` | 0 | verified: 8 passed |
| Installed public function | `Rscript -e 'd <- tempfile(); dir.create(d); status <- system2(file.path(R.home("bin"), "R"), c("CMD", "INSTALL", "-l", shQuote(d), ".")); stopifnot(status == 0); library(toypov, lib.loc=d); stopifnot(round(headcount(read_survey()), 6) == 0.153846); cat("Installed package headcount verified\n")'` | 0 | verified |

## Evidence

- Commit: 1d1ba3f + changes.
- Git blob digests: R/headcount.R d1c465ac635ea8248954f0516cc6e941fffc4ad0; NAMESPACE 1337bbb2130f45064144af057445198631aa555d; man/headcount.Rd 83cec1f9d86c8ccd43f5e28ff6a69fe7479a1675; tests/testthat/test-headcount.R 0f8aa8e9bb0098cd5a3f8f6d0551095893fc5329.
- Validation: survey output 0.15384615 agrees to six decimals with the human's prior expectation 0.153846. Constructed example checks a weighted share of 0.2 and strict exclusion at the threshold.
- An initial test used an unsuitable relative tolerance and failed; the comparison now rounds to the requested six decimals. An initial installation check failed because `--library` was not recognized; it installed the package into the user's default R library before the corrected temporary-library check passed.

## Self-review

| Principle | Verdict | Finding |
|---|---|---|
| P3 Deterministic by default | FLAG | Calculation and tests are deterministic, but the project has no environment lockfile and no reproducibility profile command. |
| P4 Prove it works | PASS | The installed public function and tests were checked against the prior expectation and a constructed example; this is self-review, not independent review. |
| P6 Smallest change | PASS | Changes implement, export, document, and test the requested function. |

review-mode: self-review

## Not checked

Full R CMD check, independent review, and reproduction in a pinned environment were not performed. The verification profile has no run or doctor command. The formatter `air` was unavailable.

## Noticed but not touching

Pre-existing untracked setup files and the draft verification profile were left alone.
