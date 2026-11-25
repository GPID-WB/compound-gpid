---
type: work-report
title: "weighted household headcount"
date: 2026-11-25
status: in-progress
size: quick
---

# weighted household headcount

## Asked

Add `headcount(dt, line = 3)`, the weighted share of households with welfare below the line, with a testthat check. The human expects 0.153846 for the toy survey. Leave the survey reader unchanged.

## Risk

Line 1: the function produces an estimate. Line 2: the bundled survey's classification and tool approval were initially unknown. The human approved the proposed contract with "approved". The human subsequently stated: "The survey is synthetic and public, made for this test. Posit Assistant may read it."

## Data register

| Dataset | Classification | Source and version | Owner | Permitted use |
|---|---|---|---|---|
| `inst/extdata/survey.csv` | Public, declared by the human | Bundled test survey; git blob `1db98caf5a1e0da55ff9784f0c98cb031f80def7` | Not stated | The human permits Posit Assistant to read it for this test. |

## Changed

| File | What changed and why |
|---|---|
| `R/headcount.R` | Add weighted share and input assertions. |
| `NAMESPACE` | Export the function. |
| `man/headcount.Rd` | Document the function. |
| `tests/testthat/test-headcount.R` | Check weighted share, threshold and invalid inputs with synthetic data. |
| `tests/testthat/test-headcount-survey.R` | Check the human's expectation to six decimal places. |

## Checks

| Check | Command | Exit code | Verdict |
|---|---|---|---|
| Synthetic tests before implementation | `testthat::test_file("tests/testthat/test-headcount.R")` in R console | n/a | Not verified: two failures because the function did not exist, as expected. |
| Synthetic tests after implementation | `pkgload::load_all(".", export_all = FALSE, helpers = FALSE); testthat::test_file("tests/testthat/test-headcount.R", stop_on_failure = TRUE)` in R console | n/a | Verified: seven expectations pass, no warnings. |
| Toy survey expectation | `pkgload::load_all(".", export_all = FALSE, helpers = FALSE); testthat::test_file("tests/testthat/test-headcount-survey.R", stop_on_failure = TRUE)` in R console | n/a | Verified: the output rounds to the human's expected 0.153846. The initial comparison using relative tolerance failed; the explicit six-decimal comparison passed. |
| Existing survey-reader tests | `testthat::test_file("tests/testthat/test-read_survey.R", stop_on_failure = TRUE)` in R console after package load | n/a | Verified: three expectations pass, no warnings. |
| Whitespace | `git diff --check` | 0 | Verified for tracked changes. |
| Guard | `cg.py guard --project <project root>` | 2 | Inconclusive: installed cg has no guard command. |

## Evidence

- Commit the checks ran on: `70f520b+changes`.
- Digests (`git hash-object`): `R/headcount.R` c54f990fa6a957823d2bf739900a15b72e87c22a; `tests/testthat/test-headcount.R` 0cfee1f3214a622e379db225e24256921cc5ed8e; `tests/testthat/test-headcount-survey.R` 04e687e569610d6d1fa763fbe78bd185b591865a; `NAMESPACE` 1337bbb2130f45064144af057445198631aa555d; `man/headcount.Rd` 179c13d066fb304798dc7617334412fd3e14024b.
- Validation: the synthetic test's independently specified weighted share is 0.2; the function matched it. The toy survey output is 0.15384615, matching the human's prior expectation of 0.153846 when rounded to six decimal places.

## Self-review

| Principle | Verdict | Finding, with file and line |
|---|---|---|
| P3 Deterministic by default | FLAG | No environment lockfile or project Run command exists. The new computation has no random component. |
| P4 Prove it works | FLAG | The toy survey comparison passed, but the verification profile has no Doctor command and the guard command is unavailable. |
| P6 Smallest change | PASS | Changes implement, export, document and test the requested function; the work report records the work. |

review-mode: self-review

## Not checked

No independent verifier, package build or full package check was run. The data owner and organization-wide tool approval level remain unspecified. The installed guard command is unavailable, so the report remains in progress.

## Noticed but not touching

The existing survey reader and its tests were left unchanged. No lockfile or Doctor command was added.
