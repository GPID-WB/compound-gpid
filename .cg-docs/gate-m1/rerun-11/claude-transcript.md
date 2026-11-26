### B1 setup

> /cg

Status says this project is in **setup**: there is no `.cg-docs/config.json` yet. I explored without writing anything, and I did not open the data file or run any R code. Here is the proposal.

## What I found (measured)

- **Files:** 8, making one R package, `toypov`: 3 `.R`, 1 `.Rd`, 1 `.csv`, plus `DESCRIPTION`, `LICENSE` and `NAMESPACE`.
- **Already here:** nothing. There is no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md` or version 1 file.
- **Data files:** 1, `inst/extdata/survey.csv`. It is restricted data until you classify it.

## Proposal

**1. Packs:** `core` and `lang-r`. Both are installed on this machine (version 1.99.0.9000). `lang-r` is called for by the `.R` files and `DESCRIPTION`.

**2. Pack setting:** `lang-r.r-syntax = data.table-collapse`.
- `DESCRIPTION:12` imports `data.table`.
- `NAMESPACE:2` has `importFrom(data.table, fread)`.
- `R/read_survey.R:8` calls `fread()`.
- No tidyverse package is loaded anywhere, and this value is also the pack's default.

**3. Verification profile (draft):**
- **Run:** not found. There is no `_targets.R`, `Makefile` or main script.
- **Doctor:** not found.
- **Outputs map:**

| Output | Where it lives | What proves it right |
|---|---|---|
| Return value of `read_survey()` | `R/read_survey.R` | Input assertions at `R/read_survey.R:9-22` and two tests in `tests/testthat/test-read_survey.R`. No reference value yet. |
| Help page | `man/read_survey.Rd` | Nothing yet. |

The input assertions check required columns, positive welfare and weight, and unique `hhid`. The tests expect 20 rows and three column names, and a refusal of a non-positive weight.

**4. Data rules.** Only you can state these, and anything you leave out stays open:
- the classification of `inst/extdata/survey.csv`, in your organization's words;
- the highest level your organization lets Claude Code read;
- the names of your organization's classification levels, from public to most restricted, if you know them.

`DESCRIPTION` calls the survey synthetic, but that is a description and not a classification. An example answer to copy and correct:

```
survey.csv = Public; Claude Code may read up to Public; levels: Public; Internal; Confidential; Strictly Confidential
```

**5. Files I will write** (from the setup command's dry run, all new):
- `.cg-docs/config.json`
- `.cg-docs/verification.md`, which I then fill with the draft in part 3; its status stays `draft`
- `AGENTS.md`, with the pointer block
- `CLAUDE.md`, holding the line `@AGENTS.md`
- `.Rbuildignore`, so the package check does not report those files

I will commit nothing. The command, with one `--data`, `--approved-tool` and `--classification-levels` option added for each data rule you give:

```
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --project "<project>"
```

## Assumptions

- I will name this coding agent `Claude Code` in the approved-tool rule. Tell me if you want another name.
- The dialect is inferred from `data.table` alone. The code does not use `collapse`.
- `r-syntax` is the only setting the `lang-r` lead skill reads.
- I left Run and Doctor as "not found" and did not guess a command. `tests/testthat.R` is the standard entry for a package check; if you want that as the Run command, say so.
- Not checked: whether the tests pass, and what the data file contains.

Do you approve parts 1, 2, 3 and 5 as shown, and what are your answers for part 4?

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve parts 1, 2, 3 and 5, and add your data rules in the form of the example in part 4. Or reply with corrections.
* **Project:** Setup of Compound GPID for the `toypov` toy package: the proposal is made and nothing is written yet; after your yes I run the setup command, fill the verification profile and confirm that status prints `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Writing what you confirmed. The classification levels stay out, since you did not name them. The command:

```
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Claude Code=Public" --project "<project>"
```

Setup is done, and the project is ready for the guide.

**What I found (measured)**
- 8 files making one R package, `toypov`: 3 `.R`, 1 `.Rd`, 1 `.csv`, plus `DESCRIPTION`, `LICENSE` and `NAMESPACE`.
- No command that makes the outputs: there is no `_targets.R`, `Makefile` or main script. The checks are two tests under `tests/testthat/`.
- 1 data file, `inst/extdata/survey.csv`. I have not opened it.

**What you confirmed**
- Packs `core` and `lang-r`, with `lang-r.r-syntax = data.table-collapse`.
- The draft verification profile, with Run and Doctor as "not found".
- `inst/extdata/survey.csv` is Public, and this coding agent may read Public data. I recorded the agent under the name `Claude Code`.

**Files written (all new, nothing committed)**
- `.cg-docs/config.json`
- `.cg-docs/verification.md`, filled with the confirmed draft
- `AGENTS.md`, with the pointer block
- `CLAUDE.md`, holding `@AGENTS.md`
- `.Rbuildignore`

**Status after setup (measured)**
```
phase: ready
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
packs-missing: none
stops: none
```

**What stays open**
- The verification profile is a draft. It has no Run or Doctor command, and nothing has been run from start to finish.
- The names of your organization's classification levels are not recorded, because you did not state them.
- Not checked: whether the tests pass.

**Next steps: Done**
* **Your move:** Nothing is required. To start work, type `/cg` followed by your request, for example `/cg add a function that computes the poverty headcount`. To keep the setup files, tell me `commit the setup files`.
* **Project:** Setup of Compound GPID for the `toypov` toy package is finished and status prints `phase: ready`; the next step is your first request through `/cg`.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

**Hard stop: this change needs your yes before I write anything.** No file has been changed.

## What you asked

Add `headcount(dt, line = 3)` to the `toypov` package, with a testthat check. It returns the weighted share of households whose welfare is below the line. For the toy survey you expect 0.153846.

## Why it stops

`cg.py tier` gave `tier: elevated`, for one reason:

- **number**: the change computes a number someone will read.

The data file is not a reason. `inst/extdata/survey.csv` is recorded as Public and Claude Code is cleared for Public, so I may read it. I have not opened it or computed anything yet.

## Contract

**Goal.** `headcount(dt, line = 3)` returns `sum(weight[welfare < line]) / sum(weight)`: one number between 0 and 1.

- The unit is the household, the weight is the `weight` column, and the denominator is every household in `dt`.
- "Below" is strict: a household exactly on the line is not counted.
- It fails loudly: an error if `welfare` or `weight` is missing as a column, if either holds a missing value, or if `line` is not a single number.
- It uses base arithmetic only, so no new dependency. The project's dialect setting would suggest `collapse`, but that is not in `Imports` and adding it is a separate decision.

**Files.** New: `R/headcount.R`, `tests/testthat/test-headcount.R`, `man/headcount.Rd`. Changed: `NAMESPACE`, one export line.

**Out of scope.** `read_survey()`, the survey file, `DESCRIPTION`, any other poverty measure, and any commit.

**Checks.** The tolerance is set now, before the first run.

| # | Check | It fails when |
|---|---|---|
| 1 | `headcount(read_survey())` against your 0.153846, to six decimals | the difference is 0.0000005 or more |
| 2 | A three-household table worked out on paper: welfare 1, 3, 5 with weights 1, 1, 2 must give 0.25 | it gives 0.3333 (weights ignored) or 0.5 (the household on the line counted) |
| 3 | A missing weight raises an error | it returns a number |
| 4 | The whole test suite, with the package installed in a temporary library | any test fails, including the two existing `read_survey()` tests |

Checks 1 to 3 are run on the old code first, where they must fail because the function does not exist.

If check 1 fails, I do not touch the expected value. I report the number the code gives and stop.

**Do you approve this contract?**

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the contract as shown, or say what to change (for example `yes, but count households on the line`).
* **Project:** Quick work on `headcount()` in `toypov` is stopped at the risk check with nothing written; after your yes come the change, the four checks and the work report under `.cg-docs/work-reports/`.

[exit code: 0]

### C2 yes

> Yes, proceed.

The function, its tests and the export line are written; the new tests failed on the old code as they should. Now I am generating the help page and running the four checks.

All four checks pass and the headcount matches your expected value. I am now writing the work report and having the tool validate it.

`headcount(dt, line = 3)` is added and returns 0.1538461538 for the toy survey, which matches your 0.153846 to six decimals (difference 1.5e-07, measured). Nothing is committed.

## What changed

| File | Change |
|---|---|
| `R/headcount.R` | New. Returns `sum(weight[welfare < line]) / sum(weight)`. Raises an error if `welfare` or `weight` is missing as a column, if either holds a missing value, or if `line` is not a single number. |
| `tests/testthat/test-headcount.R` | New. Four tests, nine expectations. |
| `NAMESPACE` | One line added: `export(headcount)`. |
| `man/headcount.Rd` | New. Written by roxygen2 from the comments in `R/headcount.R`. |

## Checks

All ran with the package installed in a temporary library, which was removed afterwards. Nothing was installed into your R library. The command, from the project root:

```
LIB=$(mktemp -d) && R CMD INSTALL --library="$LIB" . && Rscript -e '.libPaths(c(Sys.getenv("LIB"), .libPaths())); testthat::test_local(".", load_package = "installed", reporter = "summary", stop_on_failure = TRUE)'; rm -rf "$LIB"
```

| # | Check | Exit code | Verdict |
|---|---|---|---|
| 1 | `headcount(read_survey())` is within 0.0000005 of 0.153846 | 0 | verified |
| 2 | Welfare 1, 3, 5 with weights 1, 1, 2 gives 0.25 | 0 | verified |
| 3 | A missing weight raises an error | 0 | verified |
| 4 | Whole suite: 6 tests, 12 expectations, 0 failed, 0 warnings | 0 | verified |

- **Before the change:** checks 1 to 3 failed on the old code (exit code 1, "could not find function headcount"), and the two `read_survey()` tests passed (measured).
- **Broken on purpose:** I broke the function three ways in scratch copies, and the suite failed each time (measured).
  - Ignoring the weights broke checks 1 and 2.
  - Counting the household on the line (`<=`) broke check 2.
  - Removing the missing-value assertion broke check 3.
- **No check was changed after it failed.**

## Self-review

This is my own review of my own change, not a review in a fresh context.

- **P3 Deterministic by default: PASS.** The number comes from the function and the help page from roxygen2. The only number typed in is your reference value.
- **P4 Prove it works: PASS, with one limit.** In the toy survey no household sits exactly on the line, so check 1 cannot tell `<` from `<=`. Only the three-household table in check 2 proves the strict inequality.
- **P6 Smallest change: PASS.** The four files touched are the four declared. No dependency was added.

## Not checked

- `R CMD check` was not run. The two help-page examples ran once without error.
- There was no fresh-context review and no domain lens; the review playbook is not installed.
- `styler` and `lintr` were not run.
- `headcount()` does not check that weights are positive or that the table has rows. An empty table gives `NaN`, not an error. The contract did not ask for either.
- That your 0.153846 was worked out independently of this code is taken from your message.

## Noticed but not touching

- `.cg-docs/verification.md` has no row for `headcount()` in its outputs map. It is now out of date.
- The `lang-r` pack asks for `rlang` or `cli` errors and `collapse::fmean()` for weighted shares. The project imports none of these, so `headcount()` uses `stop()` and base arithmetic, as `read_survey()` does.
- `NAMESPACE` is kept by hand while the help pages come from roxygen2.
- The project has no `renv.lock`.

The work report is `.cg-docs/work-reports/2026-11-25-add-headcount.md`, with `status: completed`. `cg.py validate` found 0 problems.

**Next steps: Done**
* **Your move:** Nothing is required. To commit the change with its work report, reply `commit the headcount change`.
* **Project:** Quick work on `headcount()` in `toypov` is finished and recorded but uncommitted; `.cg-docs/verification.md` is out of date because its outputs map lacks `headcount()`.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I'll check where the work stands, then look at the existing code.

I added `n_households(dt)`, which returns the number of households in the survey as an integer; `n_households(read_survey())` gives 20. The full test suite passes (17 expectations, 0 failures), run against a temporary install of the package.

- **What it counts:** rows of `dt`, one per household, ignoring the weights. I read "households in the survey" as the households interviewed, not a weighted population estimate (the weights sum to 45.5).
- **Refusals:** it stops with an error if `dt` has no `hhid` column or if `hhid` has duplicates, in the same style as `read_survey()`.
- **Files:** the function is in `R/n_households.R`, its tests in `tests/testthat/test-n_households.R`, the help page in `man/n_households.Rd` (generated by roxygen2), and `NAMESPACE` has one new `export(n_households)` line.

`R CMD check` was not run and nothing is committed. Because this did not go through `/cg`, there is no work report for it in `.cg-docs/`.

**Next steps: Done**
* **Your move:** Nothing. If you wanted the weighted count instead, reply "make n_households weighted".
* **Project:** Added `n_households()` to the `toypov` toy package; `headcount()` and this function are both uncommitted, and `.cg-docs/verification.md` is now out of date because its outputs map lists neither.

[exit code: 0]
