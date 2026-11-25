### B1 setup

> /cg

I'll start by reading the launcher file.

Now the R pack's lead skill (for settings) and the project's own files.

Nothing is written yet. Setup has not run, so the project has no `.cg-docs/` folder. Here is the proposal for you to confirm.

## What I found (measured)
- **Files:** 3 `.R` files (`R/read_survey.R`, `tests/testthat.R`, `tests/testthat/test-read_survey.R`). There is also a `DESCRIPTION`, a `NAMESPACE`, 1 `.Rd` file, a `LICENSE` and 1 `.csv`.
- **How outputs are made:** I found no `_targets.R`, `Makefile`, main script or lockfile. The only check is the testthat suite in `tests/`.
- **Already here:** no `AGENTS.md`, `CLAUDE.md`, `GLOSSARY.md`, `.cg-docs/` or version 1 files.
- **Data:** 1 file, `inst/extdata/survey.csv`. I did not open it. I ran a line count (21 lines) to see its size, which is a step past "name and count only". I read nothing else from it.

## 1. Packs
- `core` is installed.
- `lang-r` is installed. The `.R` files, `DESCRIPTION` and `NAMESPACE` call for it.
- I did not add `lang-stata` or `lang-python`, because there are no `.do`, `.ado`, `.py` or `.ipynb` files.

## 2. Pack settings
- **`lang-r.r-syntax` = `data.table-collapse`.** This is the pack's default. The code supports it: `DESCRIPTION` has `Imports: data.table`, `NAMESPACE` has `importFrom(data.table, fread)`, and `R/read_survey.R:12` calls `fread(path)`. No tidyverse package is loaded anywhere.

## 3. Verification profile (draft)
- **Run:** not found. A package has no single command that produces outputs, and I did not guess one.
- **Doctor:** not found.
- **Outputs map:**

| Output | Where it lives | What proves it right |
|---|---|---|
| `read_survey()` | `R/read_survey.R` | `tests/testthat/test-read_survey.R`: 20 rows, columns `hhid`, `welfare`, `weight`, and an error on a weight of 0 |

If you want a Run or Doctor command in the profile, name it and I will use it as you give it.

## 4. Data rules (only you can state these)
`DESCRIPTION` says the data are synthetic. That is a description, not a classification, so `survey.csv` stays restricted data until you answer. I need three things:
- the classification of `inst/extdata/survey.csv`, in your organization's words;
- the highest level your organization lets this coding agent read;
- the names of your classification levels, from public to most restricted, if you know them.

Example answer you can copy and correct: `survey.csv = Public; Claude Code may read up to Public; levels: Public;Official Use Only;Confidential;Strictly Confidential`.

## 5. Files I will write
This list comes from the setup command run with `--dry-run`:
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`, because `DESCRIPTION` is in the root. It will hold `^\.cg-docs$`, `^AGENTS\.md$` and `^CLAUDE\.md$`.

I will commit nothing.

## Assumptions
- I name this coding agent **Claude Code** in `approved-tools`. Tell me if you want another name.
- I leave open any data answer you do not give. That file stays restricted until you give it.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to confirm packs, setting, verification draft and file list, and add your three data answers in the same message. For example: `yes. survey.csv = Public; Claude Code may read up to Public; levels: Public;Official Use Only;Confidential;Strictly Confidential`.
* **Project:** this is setup of `toypov`, an R package with no Compound GPID state yet. After you confirm, I run setup, check that status shows `phase: ready`, and fill the verification profile.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Confirmed. Classification levels were not given, so I leave that option out. Here is the command, then I run it.

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Claude Code=Public" --project "<project>"`

Setup wrote the five files. Next I fill the verification profile with the confirmed draft and check status.

Setup is done. The project is ready for the guide.

## What I found
- **Files by language:** 3 `.R` files, plus `DESCRIPTION`, `NAMESPACE`, 1 `.Rd` file, a `LICENSE` and 1 `.csv`.
- **How outputs are made:** no single command. The only check is the testthat suite in `tests/`.
- **Data files:** 1.

## What you confirmed
- **Packs:** `core` and `lang-r`, both installed.
- **Setting:** `lang-r.r-syntax=data.table-collapse`.
- **Data rule:** `inst/extdata/survey.csv` is `Public`.
- **Approved tool:** I named this coding agent `Claude Code`, with the level `Public`. Quick work looks for that name.

## Files written
- `.cg-docs/config.json`
- `.cg-docs/verification.md`, filled with the confirmed draft
- `AGENTS.md`, with the pointer block
- `CLAUDE.md`, holding `@AGENTS.md`
- `.Rbuildignore`

I committed nothing. All four paths show as untracked in `git status`: `.cg-docs/`, `AGENTS.md`, `CLAUDE.md` and `.Rbuildignore`.

## Status after setup (measured)
```
phase: ready
stops: none
packs-missing: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
```

## Still open
- **Verification profile:** its status is `draft`. Run and Doctor say "not found", and the profile stays a draft until a Run command exists and has been run from start to finish.
- **Classification levels:** you did not give the names, so `classification-levels` is not in the config. Quick work reads it for its risk line 2. I can add it when you tell me the names.

**Next steps: Done**
* **Your move:** type `/cg` followed by the change you want, for example `/cg add a function that computes the weighted headcount poverty rate`. Or tell me the classification level names so I can add them to the config.
* **Project:** setup of `toypov` is finished and status shows `phase: ready`. The next task is the first change to the package, which the guide opens in the quick playbook once you ask for it.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I'll start by reading the launcher file and the project status.

I've read the project and checked the risk. One line is a yes, so this is a hard stop and I haven't changed anything.

## Risk check

| # | Answer | Why |
|---|---|---|
| 1 | **Yes** | `headcount()` is new code that computes a share someone will read. The playbook counts that as a yes even though no number existed before. |
| 2 | No | The only data file is `inst/extdata/survey.csv`. Status lists it as `Public`, so Claude Code may read it (measured). |
| 3 | No | No personal data, credentials or access rights. |
| 4 | No | Nothing is deleted, overwritten, pushed or published. |
| 5 | No, with a condition | I add one function and keep `read_survey()` as it is. I use base `sum()` and add no dependency. Using `collapse::fmean()` instead would add a dependency and turn this line into a yes. |
| 6 | No | It touches 4 files: `R/headcount.R`, `tests/testthat/test-headcount.R`, `NAMESPACE`, `man/headcount.Rd`. |
| 7 | No | You gave an expected value, and I can also write a hand-computed test. |

## Contract

**Goal.** Export `headcount(dt, line = 3)`. It returns `sum(weight[welfare < line]) / sum(weight)`, a single number between 0 and 1. It takes a table like the one `read_survey()` returns.

**Out of scope.** `read_survey()`, the survey file, `DESCRIPTION`, other poverty measures, groups, and unit conversion.

**Assumptions I will use unless you say otherwise.**
- "Below" is strictly less than, so welfare equal to the line is not counted.
- The line is in the same unit as the `welfare` column.
- The result is a share, not a percentage.
- The function stops with an error when `welfare` or `weight` is missing, has an `NA`, or has a non-positive weight, or when `line` is not a single number. There is no silent fallback.

**Checks and what would mean failure.**
1. `headcount(read_survey())` gives 0.153846 within 5e-7 (half a unit in the sixth decimal). Your number is the independent reference. It equals 2/13 (inferred). Failure: any difference above 5e-7.
2. A small table I compute by hand, with a household exactly at the line and unequal weights. Failure: the unweighted share, or a count of the household at the line, comes out instead.
3. Error tests for a missing column and an `NA` weight. Failure: no error.
4. The existing `read_survey()` tests still pass. I run them with `devtools::test()` from source, so nothing is installed into your R library.
5. Checks 1 to 3 must fail before I write the function and pass after.

I generate `NAMESPACE` and `man/` with roxygen2. `DESCRIPTION` says roxygen2 8.0.0. If the installed version differs, I will tell you and not edit `DESCRIPTION`.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve this contract with the assumptions above and no new dependency. Reply `yes, use collapse` if you want `collapse::fmean()` instead, which adds `collapse` to `Imports`. Or tell me what to change.
* **Project:** The toy package `toypov` only has `read_survey()` so far. This task adds `headcount()` as quick work, and the work report comes after the checks pass.

[exit code: 0]

### C2 yes

> Yes, proceed.

Starting step 3. I'll run the existing tests first as a baseline, because the change touches no existing output.

Baseline: 3 tests pass, and roxygen2 is 8.0.0, so it matches `DESCRIPTION`. I'm writing the tests first so I can watch them fail.

Now I'll run the new tests against the unchanged code, where they should fail.

All seven new tests fail because `headcount()` doesn't exist yet, which is what I wanted. Now the function.

All four wrong versions fail the tests. Now the self-review, so I'm reading the principle files for P3, P4 and P6.

Before the record, one more check. I'll recompute the share from the CSV with awk, which doesn't use R, and print only counts and sums.

The awk route gives 7 / 45.5 = 0.1538461538, the same as the R function, from a second method. Now the work report.

I'm fixing two line references in the work report. Then I'll give the summary.

`headcount(dt, line = 3)` is added and gives 0.1538461538 for the toy survey. That is 1.5e-07 from your 0.153846, inside the 5e-7 tolerance I set before the first run. The full suite passes (19 tests), and `devtools::check()` reports 0 errors, 0 warnings and 0 notes.

## What changed (all measured)
- **`R/headcount.R`** is new. It returns `sum(weight[welfare < line]) / sum(weight)`, with "below" strictly less than, and adds no dependency.
- **`tests/testthat/test-headcount.R`** is new, with 7 tests. They cover the toy survey against 0.153846, a hand-computed table with a household exactly at the line, and the error cases.
- **`man/headcount.Rd`** is new, generated by roxygen2 8.0.0.
- **`NAMESPACE`** has one line added by hand, `export(headcount)`. Roxygen refuses to touch this file because it is hand-written. Regenerating it would also drop the `importFrom(data.table, fread)` line.

## Checks
- **Before the function existed:** all 7 new tests failed with `could not find function "headcount"`.
- **Toy survey:** 0.1538461538 against your 0.153846.
- **Second route:** `awk` over the CSV, without R, gives 7 / 45.5 = 0.1538461538, which is 2/13.
- **Wrong versions caught:** `<=`, unweighted, wrong denominator and ignored `line` each failed 3 to 6 tests in a scratch copy under the session scratchpad.

## Self-review (by me, not independent)
- **P3 and P4:** pass.
- **P6:** pass with one disclosure. I added two guards you didn't list: non-numeric columns and a zero-row table. Without them, text welfare would compare as text and an empty table would return `NaN` silently. Each has a test. Say so if you want them removed.

## Not checked
- The verification profile has no Run or Doctor command, so neither ran.
- I didn't run `styler` or `lintr`.
- Errors use `stop()`, like `read_survey()`, because `rlang` isn't in `Imports`.
- Only the 20-row toy survey was tried.

## Noticed but not touching
- Roxygen can't regenerate `NAMESPACE` until `R/read_survey.R` gets an `@importFrom data.table fread` tag. Until then, each new export needs a hand edit.
- The existing `read_survey()` help page shows literal backticks, because roxygen markdown isn't enabled.

Nothing is committed. The work report is `.cg-docs/work-reports/2026-11-25-add-headcount-with-testthat-checks.md`, with `status: completed` because every named check is verified.

**Next steps: Done**
* **Your move:** To commit, reply `commit this`. I'll put the report in the same commit as the change. Otherwise nothing.
* **Project:** `toypov` now has `read_survey()` and `headcount()` with tests; the next measure (poverty gap or severity) would be a new `/cg` request.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I'll check where the work stands first, as the project instructions ask.

The project has a finished, uncommitted `headcount()` and no active CG work. I'll add the new function next to it and follow the same conventions. The test goes first so I can watch it fail.

The five new tests fail because the function doesn't exist yet, and the 19 existing ones still pass. Now the function itself.

I added `n_households(dt)`. It returns the number of rows in `dt` as an integer, so `n_households(read_survey())` gives `20L`. The full test suite passes (25 tests, 0 failures). `R CMD check` gave 0 errors, 0 warnings and 0 notes. A separate `awk` row count of `survey.csv` also gave 20.

- **Counting rule:** it counts surveyed households (rows) and ignores the weights. If you meant the households the sample represents, that would be the sum of the weights, which is 45.5 here. Say so and I'll change it.
- **Empty table:** a table with no rows returns `0L`.
- **Wrong input:** anything that isn't a data.frame stops with an error.
- **Checks:** I wrote the tests first and saw the five new ones fail before the function existed.
- **Files:**
  - `R/n_households.R`
  - `tests/testthat/test-n_households.R`
  - `man/n_households.Rd`, generated by roxygen
  - `NAMESPACE`, with `export(n_households)` added by hand because roxygen skips it, as it did for `headcount`

I did not commit anything. I also wrote no work report, since you didn't start this with `/cg`.

**Next steps: Done**
* **Your move:** Nothing. To have this change recorded with checks, type `/cg` in a new message.
* **Project:** `n_households()` is added next to `headcount()`; both are uncommitted, and only `headcount()` has a work report in `.cg-docs/work-reports/`.

[exit code: 0]
