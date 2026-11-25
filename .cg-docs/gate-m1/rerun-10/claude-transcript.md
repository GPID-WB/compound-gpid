### B1 setup

> /cg

Setup has not run in this project yet (`phase: setup`, no `.cg-docs/config.json`), and there are no stops. I have only read so far; nothing is written. Here is the proposal for you to confirm.

## What I found (measured)

- **Files:** 8, in an R package called `toypov`: 3 `.R`, 1 `.Rd`, 1 `.csv`, plus `DESCRIPTION`, `LICENSE` and `NAMESPACE`.
- **Data files:** 1, `inst/extdata/survey.csv`. I did not open it.
- **Already here:** no `AGENTS.md`, `CLAUDE.md`, `GLOSSARY.md`, `.cg-docs/`, `.Rbuildignore` or version 1 files.

## Proposal

**1. Packs:** `core` and `lang-r`. Both are installed on this machine (version 1.99.0.9000). `lang-r` is called for by the `.R` files and `DESCRIPTION`.

**2. Pack setting:** `lang-r.r-syntax = data.table-collapse`.
- The code loads data.table only: `DESCRIPTION:12`, `NAMESPACE:2`, and `fread()` at `R/read_survey.R:8`.
- No tidyverse package and no collapse call appear anywhere.
- This value is also the pack's default.

**3. Verification profile (draft):**

| Part | Draft |
|---|---|
| Run | not found. The package has no pipeline, `Makefile` or main script. |
| Doctor | not found. |
| Output | The return value of `read_survey()`, defined at `R/read_survey.R:7`. |
| What proves it right | Input assertions at `R/read_survey.R:10-22` and two tests in `tests/testthat/test-read_survey.R`. No independent reference value yet. |

The project names no command for running its tests, so I recorded none. If you name the one you use, I will add it.

**4. Data rules: your answers needed.** Only you can state these.
- What is the classification of `inst/extdata/survey.csv`?
- What is the highest level your organization lets Claude Code read?
- If you know them, what are your organization's classification levels, from public to most restricted?

`DESCRIPTION` calls the survey synthetic, but that is a description and not a classification. Until you answer, the file counts as restricted data and I will not open it.

An example answer you can copy and edit:

```
yes. survey.csv = Public. Claude Code may read up to Public. Levels: Public; Official Use Only; Confidential; Strictly Confidential
```

**5. Files I will write** (from the setup command's dry run; all are new):
- `.cg-docs/config.json`
- `.cg-docs/verification.md`, which I then fill with the draft in part 3, status `draft`
- `AGENTS.md`, with the pointer block
- `CLAUDE.md`, holding the line `@AGENTS.md`
- `.Rbuildignore`, with entries for the three items above

## Assumptions

- I name this coding agent "Claude Code" in the approved-tool record.
- I commit nothing.
- What I know about the survey's columns and row count comes from the code and tests, not from the file.

**Next steps: Waiting on you**
* **Your move:** Reply with `yes` plus the three data answers (edit the example above), or tell me what to change. A data answer you do not know can stay open.
* **Project:** This is first-time setup of the guide for `toypov`; the proposal is ready, nothing is written, and the write and the status check come after your yes.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Confirmed: the proposal as shown, `inst/extdata/survey.csv` = Public, and Claude Code may read Public. You gave no list of classification levels, so I leave that option out. The command:

```
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Claude Code=Public" --project "<project>"
```

Setup is done: status now prints `phase: ready` and `stops: none` (measured).

## What I found
- **Files:** 8, in the R package `toypov`: 3 `.R`, 1 `.Rd`, 1 `.csv`, plus `DESCRIPTION`, `LICENSE` and `NAMESPACE`.
- **How outputs are made:** no Run command exists. The package's output is the return value of `read_survey()`, checked by two tests in `tests/testthat/`.
- **Data files:** 1, `inst/extdata/survey.csv`. I still have not opened it.

## What you confirmed
- Packs `core` and `lang-r`, and the setting `lang-r.r-syntax=data.table-collapse`.
- `inst/extdata/survey.csv` is Public.
- Claude Code may read Public data. I used the name "Claude Code" in the record.

## Files written (all new, none committed)
- `.cg-docs/config.json`
- `.cg-docs/verification.md`, filled with the confirmed draft
- `AGENTS.md`, with the pointer block
- `CLAUDE.md`, holding `@AGENTS.md`
- `.Rbuildignore`, so the package check ignores the three items above

## Status lines
```
phase: ready
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
packs-missing: none
stops: none
```

`cg.py validate` also reports 0 problems and 0 warnings.

## What stays open
- **Verification profile:** it is a draft. Run and Doctor are both "not found", and the output has no independent reference value yet.
- **Classification levels:** you did not give your organization's list, so none is recorded.

**Next steps: Done**
* **Your move:** Nothing is required. To start work, type `/cg` followed by your request, for example `/cg add a function that computes the poverty headcount`. To keep the setup files, tell me `commit the setup files`.
* **Project:** This was first-time setup of the guide for `toypov`; the project is ready, the five setup files are uncommitted, and the next step is your first request through `/cg`.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

The work is stopped here for your yes. Status shows the project is set up with nothing open, and the tier came out **elevated**.

**Reason for the stop:** `number` — the change adds code that computes an estimate someone will read. The data file is cleared (`inst/extdata/survey.csv` is recorded as Public, and Claude Code may read Public).

## Contract

**Goal.** Add an exported `headcount(dt, line = 3)` to `toypov`. It returns one number: the sum of `weight` for households with `welfare < line`, divided by the sum of all `weight`.

**Files.**
- New: `R/headcount.R`, `tests/testthat/test-headcount.R`, `man/headcount.Rd`
- Changed: `NAMESPACE` (one `export(headcount)` line)

**Out of scope.**
- `read_survey()`, the survey file and the verification profile stay as they are.
- `DESCRIPTION` stays as it is: I will use base `sum()`, so there is no new dependency.

**Behaviour I will build in.**
- "Below" is strict: a household exactly at the line is not counted. No toy household sits at 3, so this does not move your expected value.
- It raises an error on a missing column, a missing `welfare`, a missing or non-positive `weight`, or a `line` that is not a single finite number.

**Checks, and what would mean failure.**

| Check | Fails when |
|---|---|
| `headcount(read_survey())` against your 0.153846, with tolerance 0.0000005 (six decimals, as you gave it) | the value differs by more than that |
| The new test is run before the function exists, then after | it does not fail before, or does not pass after |
| Edge tests: a household exactly at the line, and each bad input | the household at the line is counted, or a bad input returns a number instead of an error |
| Full test suite with `devtools::test()` (loads the package in place, installs nothing) | any test fails, including the two existing ones |
| `devtools::document()` | it changes anything other than `man/headcount.Rd` and the new `NAMESPACE` line |

**Hand arithmetic (inferred, not yet run in code).** Four households are under 3 (hhid 3, 11, 14, 19), with weights summing to 7. All weights sum to 45.5. 7 / 45.5 = 0.1538462, which agrees with your 0.153846.

**Not done yet.** No file has been changed and no work report exists.

Do you approve this contract?

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the contract as shown, or say what to change (for example, `use <= instead of <`).
* **Project:** Adding `headcount()` to the toy package `toypov`; the risk check is done and the tier is elevated, so the change, the checks and the work report follow your yes.

[exit code: 0]

### C2 yes

> Yes, proceed.

The seven new tests fail as they should, since `headcount()` does not exist yet; the two old ones still pass. Writing the function now.

`headcount(dt, line = 3)` is added and exported, and it returns 0.1538461538 for the toy survey, within 0.0000005 of your 0.153846 (measured). Nothing is committed.

One thing to decide: two inputs outside the contract return a number instead of an error (measured). I left both unguarded because the contract did not list them.
- A data frame with zero rows returns `NaN`.
- A `welfare` column stored as text is compared as text and gives a wrong share.

Neither happens through `read_survey()` on the toy file. I recommend adding both guards.

## What changed

| File | Change |
|---|---|
| `R/headcount.R` | New. Input checks, then `sum(weight[welfare < line]) / sum(weight)`. |
| `tests/testthat/test-headcount.R` | New. Seven tests, 14 expectations. |
| `man/headcount.Rd` | New, written by `devtools::document()`. |
| `NAMESPACE` | One line added by hand: `export(headcount)`. The file is hand-written, so `devtools::document()` skips it. |

To keep `DESCRIPTION` unchanged, errors use `stop()` and the share uses base `sum()`. The lang-r pack would prefer `cli::cli_abort()` and `collapse::fmean()`.

## Checks

All five are measured. No check was changed after it failed.

| Check | Command | Verdict |
|---|---|---|
| Reference value: the result differs from 0.153846 by 1.54e-07, against a tolerance of 5e-07 | first test in `test-headcount.R` | verified |
| New tests fail before the function exists (7 of 7 errored) and pass after | `devtools::test()`, run before and after | verified |
| Edge tests: a household at the line is not counted, and each bad input raises an error | `devtools::test()` | verified |
| Full suite: 9 tests, 17 expectations, 0 failed, 0 warnings | `devtools::test()` | verified |
| `devtools::document()` changes nothing but `man/headcount.Rd` | `devtools::document()`, then `git status --short` | verified |

I also broke the function three ways in a scratch copy: `<=` for `<`, weights dropped, denominator limited to the poor. Each broke at least one test.

Four of the 20 households are below 3, with weight 7 of 45.5. The unweighted share would be 0.2.

## Self-review

This is my own review, not an independent one.

- **P3 Deterministic by default: FLAG, advisory.** The project has no lockfile, which was so before this change. The number itself comes from the function, and two runs gave the same value.
- **P4 Prove it works: PASS.** The reference value came from you, and every check was seen to fail or to be able to fail.
- **P6 Smallest change: PASS.** The diff stays inside the four declared files, and each input check is one the contract listed.

## Not checked

- An independent review.
- `R CMD check`. The help-page examples do run (exit code 0).
- The Run and Doctor commands of the verification profile: both are "not found".
- A formatter or linter: none is set up in the project.

## Noticed but not touching

- `.cg-docs/verification.md` is now out of date: its outputs map does not list `headcount()` or its reference value.
- `R/read_survey.R` has no `@importFrom` tag, so `NAMESPACE` cannot be regenerated from roxygen.
- `DESCRIPTION` does not turn on roxygen markdown, so backticks show as backticks in both help pages.
- `.Rbuildignore`, `AGENTS.md`, `CLAUDE.md` and `.cg-docs/` were untracked before this work and still are.

The work report is at `.cg-docs/work-reports/2026-11-25-add-headcount.md`. It validates with 0 problems, and status shows no open work. I made no temporary folder for you to delete.

**Next steps: Done**
* **Your move:** To add the two guards, type `/cg make headcount() raise an error on zero rows and on a non-numeric welfare or weight column`. To commit as it is, reply `commit the headcount change with its work report`.
* **Project:** `headcount()` is added to `toypov` with its tests and work report, uncommitted; the verification profile `.cg-docs/verification.md` is out of date and the two-guard decision is open.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I added `n_households(dt)`, which returns the number of households in the survey as an integer: 20 for the toy survey. The full test suite passes (25 expectations, 0 failures), and 20 matches the count of data lines in `inst/extdata/survey.csv`.

- **What it counts:** surveyed households, one per row, without using the weights. I read "in the survey" as the sample size, not the population estimate; the sum of the weights would give 45.5 instead.
- **What it refuses:** an input that is not a data frame, a missing `hhid` column, a missing `hhid` value, or a repeated `hhid`. A survey with no rows returns 0.
- **Files:** the function is in `R/n_households.R`, its tests in `tests/testthat/test-n_households.R`, the help page in `man/n_households.Rd`, and `NAMESPACE` gains one hand-written `export(n_households)` line.

This went in without `/cg`, so there is no work report for it in `.cg-docs/`. Nothing is committed, and I did not run `R CMD check`.

**Next steps: Done**
* **Your move:** Nothing, unless you wanted the weighted population count: reply "make it weighted" and I will change it to the sum of `weight`.
* **Project:** Added `n_households()` to `toypov` beside `read_survey()` and `headcount()`; all changes are uncommitted, and `.cg-docs/verification.md` still lists `read_survey()` only, so it is out of date.

[exit code: 0]
