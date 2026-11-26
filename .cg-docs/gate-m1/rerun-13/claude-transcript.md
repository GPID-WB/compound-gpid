### B1 setup

> /cg

Status says this project is not set up yet (`phase: setup`, no `.cg-docs/config.json`), so I followed the setup playbook. I have only read so far and written nothing; this is the proposal for you to confirm.

## What I found (measured)

- **Files:** 8, forming an R package, `toypov` 0.0.1: 3 `.R`, 1 `.Rd`, 1 `.csv`, plus `DESCRIPTION`, `NAMESPACE` and `LICENSE`.
- **Data files:** 1, `inst/extdata/survey.csv`. I did not open it.
- **Already here:** nothing from Compound GPID. There is no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md` or version 1 file.
- **Stops:** none. Nothing is waiting on you from earlier work.

## Proposal

**1. Packs.** `core` and `lang-r`. Both are installed on this machine, at version 1.99.0.9000. `lang-r` is called for by the `.R` files and `DESCRIPTION`.

**2. Pack setting.** `lang-r.r-syntax = data.table-collapse`. This is also the pack's default. The code shows data.table and no tidyverse:
- `DESCRIPTION:12` imports `data.table`
- `NAMESPACE:2` has `importFrom(data.table, fread)`
- `R/read_survey.R:8` calls `fread(path)`

**3. Verification profile (draft).**
- **Run:** not found. The project has no `Makefile`, `_targets.R` or main script.
- **Doctor:** not found.
- **Outputs map:**

| Output | Where it lives | What proves it right |
|---|---|---|
| Return value of `read_survey()`: a data.table, one row per household | `R/read_survey.R` | Input assertions at `R/read_survey.R:9-21` (columns present, welfare and weight positive, `hhid` unique). Two tests in `tests/testthat/test-read_survey.R`. No reference value yet. |

The package has a test suite, but no file states the command that runs it. If you have one you use, give it to me and I will write it as Run.

**4. Data rules.** Only you can state these. One question, three parts:
- What is the classification of `inst/extdata/survey.csv`? `DESCRIPTION` calls it synthetic, but a description is not a classification.
- What is the highest level your organization lets this coding agent read?
- If you know them: the names of your organization's levels, from public to most restricted.

An example of the form, not a suggested answer: `survey.csv is Public. Claude Code may read up to Official Use Only. Levels: Public; Official Use Only; Confidential; Strictly Confidential.`

Any part you leave unanswered stays open, and until it is answered the file is treated as restricted data.

**5. Files I will write** (from the command's dry run). All five are new; no existing file changes.
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`, with the pointer block
- `CLAUDE.md`, holding the line `@AGENTS.md`
- `.Rbuildignore`, so the package check does not report the three above

The command, with your data answers added as `--data`, `--approved-tool` and `--classification-levels`:

```
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --project "<project>"
```

## Assumptions I am making

1. This coding agent is recorded as `Claude Code`. If it is wrong: the later data check looks for another name, so tell me the name to use.
2. I commit nothing. If it is wrong: say so and I commit the five files after writing them.

Correct me now.

## Not checked

- The contents of `survey.csv`.
- Whether the tests pass, and whether R is installed here. I ran neither R nor the tests.

**Next steps: Waiting on you**
* **Your move:** Reply with your answers to the data question in part 4, and `yes` to write the five files, or tell me what to change. For example: `survey.csv is <level>. Claude Code may read up to <level>. Levels: <level>; <level>. Yes.`
* **Project:** Setup of Compound GPID for `toypov`; the proposal is ready and nothing is written. Once you confirm, I write the files and check that status prints `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

You confirmed the proposal and gave two data rules. You did not name your organization's levels, so I leave that option out. The command:

```
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Claude Code=Public" --project "<project>"
```

Now I fill the verification profile with the draft you confirmed.

Setup is done. Status prints `phase: ready` and `stops: none` (measured).

## What I found

- **Files by language:** an R package, `toypov` 0.0.1, with 3 `.R` files, 1 `.Rd`, `DESCRIPTION`, `NAMESPACE` and `LICENSE`.
- **How outputs are made:** no Run command exists in the project. The one output is the return value of `read_survey()`, protected by input assertions and two tests.
- **Data files:** 1, `inst/extdata/survey.csv`. I still have not opened it.

## What you confirmed

- Packs `core` and `lang-r`, and the setting `lang-r.r-syntax=data.table-collapse`.
- `inst/extdata/survey.csv` is Public.
- This coding agent, recorded as `Claude Code`, may read Public data.
- The draft verification profile and the five files.

## Files written

All five are new, and nothing is committed.

- `.cg-docs/config.json`
- `.cg-docs/verification.md`, filled with the confirmed draft
- `AGENTS.md`, with the pointer block
- `CLAUDE.md`, holding `@AGENTS.md`
- `.Rbuildignore`

## Status lines

```
phase: ready
packs-expected: core; lang-r
packs-missing: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
stops: none
```

No pack is left to add. `cg.py validate` reports 0 problems and 0 warnings.

## What stays open

- **The verification profile is a draft.** Run and Doctor are both "not found". It stays a draft until a Run command exists and has been run from start to finish.
- **Your organization's classification levels are not recorded.** You did not name them, so I left them out. To add them, run `/cg` again with the list, from public to most restricted.

## Not checked

- Whether the tests pass, and whether R is installed here. I ran neither.
- Whether `Claude Code` is the name your organization uses for this tool.

**Next steps: Done**
* **Your move:** Nothing is required. To start work, type `/cg` followed by your request, for example `/cg add a function that computes the poverty headcount`. To keep the setup files in git, reply `commit the setup files`.
* **Project:** Setup of Compound GPID for `toypov` is finished and the project is ready; the next step is your first request through `/cg`, and the verification profile is still a draft.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

**Hard stop: the tier is elevated, so nothing changes until you say yes.**

Status shows the project ready, with no open work, no stops and nothing waiting on you. The tier has one reason:

- **number**: `headcount()` computes a new estimate that someone will read.

The survey file is cleared: it is recorded as Public, and Claude Code is approved for Public. I opened it while looking at the project, before `tier` confirmed that; the status line already showed the rule.

## Contract

**Goal.** Add an exported `headcount(dt, line = 3)` to `toypov`. It returns one number: the sum of `weight` over households with `welfare < line`, divided by the sum of `weight` over all households.

**Files.**
- `R/headcount.R` (new, with roxygen documentation)
- `tests/testthat/test-headcount.R` (new)
- `NAMESPACE` (one line, `export(headcount)`, added directly because the file is not roxygen-generated)
- `man/headcount.Rd` (new, generated by roxygen2)
- `.cg-docs/verification.md` (one row in the outputs map, naming your reference value)

**Out of scope.**
- No change to `read_survey()` or `DESCRIPTION`.
- No other poverty measure.
- No weighting by people.
- No commit.

**Checks, with the tolerance set now.**

| # | Check | It fails when |
|---|---|---|
| C1 | `round(headcount(read_survey()), 6)` equals `0.153846`, your expectation, at the six decimals you gave | the rounded value is anything else |
| C2 | A three-household table built in the test, with one household exactly on the line and unequal weights, gives `0.25` | the code uses `<=` or ignores the weights |
| C3 | `headcount()` raises an error on a missing weight | it returns a number or `NA` |
| C4 | The whole suite passes with `Rscript -e 'devtools::test()'`, including the two existing tests | any test fails |

I will run the new tests before the function exists, to see them fail. I will also break the function in a scratch copy, to show that C1 and C2 catch it.

**Assumptions I am making:**
1. "Below" means strictly below the line. If it is wrong: the comparison becomes `<=`, and C2 expects `0.5`. No household in the toy survey sits exactly at 3, so C1 is the same either way.
2. The share is of households, using `weight` as a household weight. If it is wrong: the function needs a household size column, which the survey does not have.
3. `headcount()` fails loudly on four inputs: a missing `welfare` or `weight` column, a missing value in either, a total weight that is not positive, and a `line` that is not a single number. If it is wrong: those assertions come out, and C3 with them.
4. No new dependency: plain arithmetic and `stop()`, as `read_survey()` does. The project's R setting prefers `collapse` and `rlang`. If it is wrong: `DESCRIPTION` gains imports, which is an interface change and a second reason for the tier.

Correct me now.

**One thing I can already say (inferred, not run by code).** Reading the survey file, the weights below the line sum to 7 and all weights sum to 45.5. That gives 7 / 45.5 = 0.153846, which matches your expectation under assumptions 1 and 2.

Do you approve this contract as written?

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the contract as written, or tell me which file, check or assumption to change.
* **Project:** Quick work to add `headcount()` to `toypov`; the contract is drafted and nothing has been changed; after your yes I write the function and tests, run C1 to C4, and file the work report under `.cg-docs/work-reports/`.

[exit code: 0]

### C2 yes

> Yes, proceed.

Function and tests are in, all four checks pass, and the three break-it mutations are caught. Now updating the outputs map and writing the work report.

`headcount(dt, line = 3)` is added to `toypov`, and for the toy survey it returns 0.153846, equal to your expectation at the six decimals you gave. All four contract checks are verified and the work report validates with no problems; nothing is committed.

## What changed

| File | Change |
|---|---|
| `R/headcount.R` | New: the function, its roxygen documentation and the four input assertions |
| `tests/testthat/test-headcount.R` | New: three tests (C1, C2, C3) |
| `NAMESPACE` | One line added, `export(headcount)` |
| `man/headcount.Rd` | New, generated by roxygen2 |
| `.cg-docs/verification.md` | One row in the outputs map, naming your reference value |

## Checks (all measured)

| Check | Command | Verdict |
|---|---|---|
| New tests fail before the function exists | `Rscript -e 'devtools::test(stop_on_failure = TRUE)'`, exit 1, 3 failures | verified |
| C1: `round(headcount(read_survey()), 6)` equals `0.153846` | `Rscript -e 'devtools::test(filter = "headcount", stop_on_failure = TRUE, reporter = "location")'`, exit 0 | verified |
| C2: the three-household table gives `0.25` | same command | verified |
| C3: error on a missing weight | same command | verified |
| C4: whole suite | `Rscript -e 'devtools::test(stop_on_failure = TRUE)'`, exit 0, 6 passes, 0 failures | verified |
| Installed package, as a user calls it | `R CMD INSTALL` into a temporary library, then `headcount(read_survey())`, exit 0 | verified |
| Break-it runs in scratch copies | `<=` fails C2; an unweighted share fails C1 and C2; removing the missing-weight assertion fails C3 | verified |

No check was changed after it failed.

**Validation.** The function returns 0.1538461538, against your 0.153846. Four of the 20 households are below the line; their weights sum to 7 of 45.5. A second computation with `collapse::fmean()` gives the same value.

## Self-review (P3, P4, P6)

This is a self-review in my own context, not an independent one.

- **P3: FLAG, advisory.** The change itself has no finding. The flag is on the project and was there before: there is no `renv.lock`, and the verification profile names no Run command.
- **P4: PASS.**
- **P6: PASS.** The diff stays in the five contract files.

## Not checked

- `R CMD check` was not run; it was not in the contract.
- The assertions for a missing column, a missing welfare value, a non-positive total weight and a bad `line` have no test in the suite. I ran each once outside it and each raised its error.
- `lintr` and `styler` were not run.
- `headcount()` does not refuse a negative weight when the weights still sum to a positive number. `read_survey()` does refuse it.
- The profile's Run and Doctor commands are "not found", so neither was run.

## Noticed but not touching

- `NAMESPACE` is written directly while the help pages come from roxygen2, and `R/read_survey.R` has no `@importFrom` tag for `fread`.
- The project has no lockfile, and the verification profile is still a draft.
- Both functions use `stop()`; the project's R setting prefers `rlang` or `cli` for errors and `collapse` for weighted statistics, which would add dependencies.
- `.Rbuildignore`, `AGENTS.md`, `CLAUDE.md` and `.cg-docs/` were untracked before this work and still are.

The work report is `.cg-docs/work-reports/2026-11-26-add-headcount.md`. The scratch copies I used are already removed, so there is nothing for you to delete.

**Next steps: Done**
* **Your move:** Nothing required. To commit the change together with its work report, reply `commit the headcount change`.
* **Project:** Quick work to add `headcount()` to `toypov` is complete and recorded; the change is uncommitted on `main`, and status shows no open work.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I'll check where the work stands, then look at the existing code.

I added `n_households(dt)`, which returns the number of households in the survey as an integer; for the toy survey it gives 20. The 13 tests pass and `R CMD check` is clean (0 errors, 0 warnings, 0 notes).

- **What it counts:** the rows of the table, one per household, without weights. This is the sample size, not an estimate of households in the population.
- **What it refuses:** an input that is not a table, a table without `hhid`, a missing `hhid`, or a repeated `hhid`.
- **Errors:** it uses `stop()`, like `read_survey()` and `headcount()`, so the package gains no new dependency.

The function is in `R/n_households.R`, with its tests in `tests/testthat/test-n_households.R`, its help page in `man/n_households.Rd`, and the export added by hand to `NAMESPACE` (roxygen skips that file because it did not generate it). Nothing is committed.

This change was made outside `/cg`, so it has no work report in `.cg-docs/work-reports/`.

**Next steps: Done**
* **Your move:** Nothing. If you wanted the weighted count instead (the sum of `weight`), reply `make n_households weighted`.
* **Project:** `n_households()` is added to the toy package `toypov` and checked; the outputs map in `.cg-docs/verification.md` is now out of date because it does not list the new function.

[exit code: 0]

### G1 idea

> /cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

Still on the look-up step: I have read the package and the record, created the intent file, and I am confirming the field's names for these measures before I ask you anything.

Facts are looked up and written into the intent; here is where we stand and the first round of questions.

**State.** No stops, nothing was waiting on you, no pack missing. The intent is a draft at `.cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md`. Nothing outside `.cg-docs/` was changed, no data file was opened and no project code was run.

**What I think you want:** a second measure in `toypov`, beside `headcount()`, that says how deep poverty is and not only how common. I am missing which question the number must answer, and for whom.

## What the field calls this

Your sentence can mean two different statistics, and they are easy to confuse.

| Term | What it means | Source |
|---|---|---|
| **Poverty gap index** (FGT1) | The average shortfall below the line, as a share of the line, over *all* households. A household at or above the line counts as zero. | World Bank PIP Methodology Handbook, section 4.1 |
| **Income gap ratio** | The average shortfall share among the *poor only*. | One source only: the installed R analytical skill, `welfare-patterns.md:94-98` |
| **Poverty severity**, or squared poverty gap (FGT2) | The poverty gap with each shortfall share squared, so the poorest count for more. | PIP Methodology Handbook, section 4.1 |
| **Watts index** | The average of ln(line / welfare) over the poor, divided by all households. It also weighs the poorest more. | PIP Methodology Handbook, section 4.1 |

- **The two are linked:** poverty gap = headcount × income gap ratio.
- **`headcount()` is already FGT0**, the first member of the family that holds the poverty gap and the squared gap.

**How they differ on a small table** (my arithmetic, not run). Take the table in `tests/testthat/test-headcount.R:9-12`: welfare 1, 3, 5, weights 1, 1, 2, line 3. One household is poor, two thirds below the line.

- Headcount: 0.25
- Poverty gap: 0.167
- Income gap ratio: 0.667

**Where the income gap ratio misleads.** Take four equal households with welfare 1, 2.7, 4 and 5, and line 3. Then the second household rises to 3.3.

| | Before | After |
|---|---|---|
| Poverty gap | 0.192 | 0.167 |
| Income gap ratio | 0.383 | 0.667 |

Nobody is worse off, yet the income gap ratio says poverty got deeper, because the least poor household left the group.

## Round 1

1. **Who will read this number, and what will they do with it?** For example: compare groups or dates, describe the poor, or size a transfer. Only you know this, so I recommend nothing.
2. **D1. Should the number answer "across all households, how large is the shortfall below the line", with non-poor households counted as zero?**
   - I recommend yes. It falls when fewer households are poor and when the poor move closer to the line, and it never rises because a household left poverty.
   - Its cost: it does not describe the typical poor household. A value of 0.05 must not be read as "the poor are 5% below the line".
   - A no means "among the poor only", which is the literal reading of your sentence and has the problem in the table above.
3. **D2. Should each unit of shortfall count the same, however poor the household?**
   - I recommend yes. The number stays easy to explain.
   - Its cost: one household 60% below the line counts the same as two households 30% below it.
   - A no leads to the squared gap or the Watts index.

Still to come, once these are answered: the unit of the number (a share of the line, or welfare units per household), and then the approaches side by side with the one I recommend.

## How I know this

- **Measured:** the facts about the package, read from `R/headcount.R`, `R/read_survey.R` and the work report of 2026-11-26.
- **Inferred:** the arithmetic in the two examples.
- **Read through a fetch agent, not by me:** the PIP handbook page and two Wikipedia pages.
- **Not checked:**
  - The World Bank indicator page refused the request (HTTP 403).
  - I opened no primary reference for the name "income gap ratio".
  - I did not compute any of these measures on the toy survey, because this playbook runs no project code.

**Next steps: Waiting on you**
* **Your move:** Reply with three numbered answers, for example: `1. Analysts comparing regions over time. 2. Yes. 3. Yes.`
* **Project:** This is the brainstorm on a depth-of-poverty measure for `toypov`; the intent is a draft with two decisions and one question open, and the next step is the unit of the number and the choice of approach.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

Your two decisions are recorded in the intent, in your words. Question 1 is still open, because it had no recommended answer for a yes to take.

## Recorded

| | Your answer |
|---|---|
| **D1** | A: the number answers "across all households, how large is the shortfall below the line", with non-poor households counted as zero. |
| **D2** | Each unit of shortfall counts the same, however poor the household. |
| **Size** | "Keep it as small as you can." |

Together, D1 and D2 point to the **poverty gap index** (FGT1) among the four measures. That is my inference, not yet your choice: the approach is put to you as its own decision in the next round.

## The one question still open

**1. Is the reader of this number you, trying Compound GPID on this toy package, with no outside audience and nobody who will size a transfer or publish it?**

- `DESCRIPTION:7-8` says the package is "used to try Compound GPID in each coding agent" and that the data are made up. That suggests this reading, but only you can confirm it.
- A yes takes that reading. If the reader is someone else, tell me who and what they will do with the number.
- It matters for two things: the Goal in the intent names the reader, and the reader's use decides the unit. A share of the line suits comparing groups or dates. Welfare units per household suit sizing a transfer.

## After your answer

One more round, with two decisions:

- the unit of the number;
- the shape of the change, with the smallest approach that works as my recommendation.

Then I restate the intent and ask for your yes to it as the file reads.

## How I know this

- **Measured:** status lists the intent as a draft waiting on you, with no stops.
- **Not done:** no `GLOSSARY.md` was written, because you have not taken up a term yet. No code or data was touched.

**Next steps: Waiting on you**
* **Your move:** Reply `Yes, the reader is me trying the tool.` or name the reader and their use, for example `Analysts comparing regions over time.`
* **Project:** The brainstorm on a depth-of-poverty measure for `toypov` has D1 and D2 decided and the reader still open; next come the unit and the approach.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

Your yes on the reader is recorded, and I have laid out the approaches in the intent. Two decisions are left before I restate it.

**Recorded.** The reader is you, trying Compound GPID on this toy package, with no outside audience. Your reply is in the intent word for word.

## Approaches

Five were considered. Two really differ, and three fall away:

- **A new argument on `headcount()`** makes the name wrong for what the function returns.
- **A function from another package** adds a dependency for one weighted average.
- **Changing nothing** does not meet the request, because the gap cannot be worked out from the headcount value.

| | A. One new function | B. One general function for the family |
|---|---|---|
| What it is | A function beside `headcount()`, same arguments, poverty gap index only | A power argument: 0 gives the headcount, 1 the poverty gap, 2 the squared gap |
| Cost | One R file, one test file, one help page, one `NAMESPACE` line, no dependency | The same, plus a rule and a test per power, and two functions that both give the headcount |
| Risk | Repeats the input checks of `headcount()` | In R, 0^0 is 1, so at power 0 a non-poor household counts as poor unless that case is handled apart |
| Unchecked | Whether a negative welfare should be refused | The same, plus whether anyone wants power 2, which D2 ruled out |

B is the weaker one here. It builds for the squared gap, which you declined in D2, and it goes against "keep it as small as you can".

No experiment is needed: both open choices are about definition, and running code would not settle either.

## Round 2

1. **D3. Should the number be a share of the line, between 0 and 1?**
   - I recommend yes. It is the handbook's definition of the poverty gap index, and it sits on the same scale as `headcount()`.
   - Its cost: it does not say how much welfare is missing. A reader who wants that multiplies by the line.
   - A no means welfare units per household.
2. **D4. Should the change be one new function beside `headcount()`, for the poverty gap index only?**
   - I recommend yes. It is the smallest change that answers the request, and it touches no existing function.
   - Its cost: a later wish for the squared gap means a third function or a rewrite.
   - A no means the general function, B.

## After your answer

I fill in Goal, Out of scope and A wrong result, run the validation, and show you the intent for your yes. One thing I will list there as an assumption, so you can correct it early: you have no expected value for the toy survey yet, so a wrong result would be caught by a hand-worked table and by the rule that the gap can never exceed the headcount of 0.153846.

## How I know this

- **Inferred, not run:** the 0^0 trap, from R's arithmetic rules, and the claim that a household exactly at the line does not move the gap.
- **Not looked up:** any outside package's function for this measure.
- **Not written:** `GLOSSARY.md`. The term "poverty gap index" goes in when you take it up with D4.

**Next steps: Waiting on you**
* **Your move:** Reply with two numbered answers, for example: `1. Yes. 2. Yes.`
* **Project:** The brainstorm on a depth-of-poverty measure for `toypov` has D1, D2 and the reader settled, with D3 and D4 open; next come the restatement and your yes to the intent.

[exit code: 0]

### G4 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

D3 and D4 are recorded, the intent is filled in, and validation prints `problems: 0` and `warnings: 0`. This is the intent as the file reads. It needs your yes before it counts as decided.

**File:** `.cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md` (status `draft`)

## Goal

The package says how far below the line the poor households are, and not only how many of them there are.

It does so with one new function beside `headcount()`, with the same arguments, that returns the **poverty gap index**: the weighted average, over all households, of each household's shortfall below the line as a share of the line. A household at or above the line counts as zero. The number is between 0 and 1.

The reader is you, trying Compound GPID on this toy package. There is no outside audience, and nobody will size a transfer with the number or publish it.

The change is kept as small as it can be. This intent builds nothing: the function is a later piece of work, which you start.

## Out of scope

- The average shortfall among the poor only (the income gap ratio).
- The squared gap, the Watts index, and a general function for the whole family.
- The shortfall in welfare units.
- Any change to `headcount()` or `read_survey()`, and any new dependency.
- A measure of people. The survey has no household size column, so the number describes households.
- Standard errors, and breakdowns by group.
- A commit.

## A wrong result

A wrong number here looks as clean as a right one. On the table in `tests/testthat/test-headcount.R:9-12` (welfare 1, 3, 5; weights 1, 1, 2; line 3), the correct value is 1/6, about 0.1667.

| The error | What it would give |
|---|---|
| Averaged over the poor only | 0.6667 |
| The weights ignored | 0.2222 |
| Not divided by the line | 0.5 |
| The shortfall share squared | 0.1111 |

These five values were worked out by hand and not run. Two more signs of a wrong result:

- A value above the headcount for the same table and line, or outside 0 to 1. For the toy survey at line 3, anything above 0.153846 is wrong.
- A value that differs from a second computation that does not call the new function.

## Decisions

Your reply to each round was: "Yes to each question: I take the answer you recommend."

| ID | Decision | Your answer |
|---|---|---|
| D1 | Which question the number answers | A: across all households, with non-poor households counted as zero |
| D2 | Whether the poorest count for more than their shortfall | No: each unit of shortfall counts the same |
| D3 | The unit of the number | A: a share of the line, between 0 and 1 |
| D4 | The shape of the change | A: one new function beside `headcount()`, for the poverty gap index only |

## Assumptions

```
Assumptions I am making:
1. The function is named `poverty_gap(dt, line = 3)`, with the default line of `headcount()`. If it is wrong: the name or the default changes, and nothing else.
2. The human has no expected value for the toy survey yet. If it is wrong: that value becomes the reference value, stated before any code is run, as 0.153846 was for `headcount()`.
3. The function makes the input checks of `headcount()` and also refuses a negative welfare. If it is wrong: a negative welfare passes, one household's shortfall can be larger than the line, and the number can exceed the headcount.
Correct me now.
```

## Also in the file, not repeated here

- The Facts table, each fact with its source.
- The five approaches considered. One was chosen, one was put to you and declined, and three were set aside.

## One change outside `.cg-docs/`

I wrote `GLOSSARY.md` at the project root, with one term, the poverty gap index, and one flagged ambiguity. The playbook asks for this in the turn a term is taken up, and D4 took it up. Nothing else outside `.cg-docs/` changed. Nothing is committed.

## How I know this

- **Measured:** the validation output, and the facts about the package, read from its files.
- **Inferred:** the hand-worked values, and the bound against the headcount.
- **Read through a fetch agent, not by me:** the PIP handbook page and two Wikipedia pages.
- **Not checked:**
  - No measure was computed on the toy survey.
  - No primary reference was opened for the name "income gap ratio".
  - No outside package was looked up.

**Is this what you want?** Your yes is recorded under your name, word for word, against this text. A correction is welcome in its place: I change the file, show you the part that changed, and ask again.

**Next steps: Waiting on you**
* **Your move:** Reply `Yes, this is what I want.` or tell me what to change, for example `Change assumption 3: do not refuse negative welfare.`
* **Project:** The brainstorm on a depth-of-poverty measure for `toypov` has all four decisions answered and the intent validated; it becomes `decided` on your yes, and building `poverty_gap()` is a separate piece of work after that.

[exit code: 0]

### G5 vague reply

> Sounds good.

"Sounds good." is agreement, but the record needs a plain yes. The playbook has me pass your reply to the tool word for word, so here is the line, and I am running it:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md" --reply "Sounds good." --project "<project>"`

The tool refused "Sounds good." and recorded nothing. The intent is still a `draft`.

The tool's reason: the reply "agrees without deciding". Only a plain yes counts, because it is written under your name against the exact text of the intent.

**Is there anything in the intent you would change, or anything that is unclear?**

The three assumptions are the parts most likely to need a correction, since you have not answered them yet:

1. The function is named `poverty_gap(dt, line = 3)`.
2. You have no expected value for the toy survey yet.
3. The function refuses a negative welfare, on top of the input checks of `headcount()`.

If nothing needs to change, a reply that holds a plain yes settles it. "Sounds good. Yes." would do.

**Next steps: Waiting on you**
* **Your move:** Reply `Yes, this is what I want.` or name the change, for example `Change assumption 1: call it pov_gap.`
* **Project:** The brainstorm on a depth-of-poverty measure for `toypov` is complete except for your yes; the intent stays a draft until then, and nothing is built.

[exit code: 0]

### G6 answer

> Yes, that is what I want.

Recording your reply before anything else. The line:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md" --reply "Yes, that is what I want." --project "<project>"`

The intent is decided, and your yes is on record. The brainstorm ends here: nothing was built and nothing is committed.

**Intent:** `.cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md`, status `decided`.

**Approval record:** `.cg-docs/approvals/2026-11-26-measure-how-far-below-the-line-the-poor-are.15075bd3b07d411a.json`. It holds your reply, "Yes, that is what I want.", under the name git gives for you, against the hash of the intent's text. A change to the intent now needs a new yes.

**Goal:** `toypov` gets one new function beside `headcount()` that returns the poverty gap index, so the package says how far below the line the poor households are and not only how many there are.

## Decisions

| ID | Decision | Your answer |
|---|---|---|
| D1 | Which question the number answers | Across all households, with non-poor households counted as zero |
| D2 | Whether the poorest count for more than their shortfall | No: each unit of shortfall counts the same |
| D3 | The unit of the number | A share of the line, between 0 and 1 |
| D4 | The shape of the change | One new function, for the poverty gap index only |

## Assumptions, confirmed with the intent

1. The function is named `poverty_gap(dt, line = 3)`.
2. You have no expected value for the toy survey yet.
3. The function makes the input checks of `headcount()` and also refuses a negative welfare.

## Approaches

- **Chosen:** one new function beside `headcount()`.
- **Put to you and declined:** one general function for the whole family, with a power argument.
- **Set aside:**
  - a new argument on `headcount()`;
  - a function from another package;
  - changing nothing.

## Still to come

- No experiment and no question for someone else is open.
- If you do have an expected value for the toy survey, state it when you start the work, before any code runs. Without one, the check rests on the hand-worked table (1/6) and on the rule that the gap cannot exceed the headcount of 0.153846.

## How I know this

- **Measured:**
  - The approval tool printed `approved`, and the intent's status line reads `decided`.
  - Status shows no open artifact, nothing waiting on you and no stops.
  - The facts about the package were read from its files.
- **Inferred, not run:**
  - the hand-worked values in "A wrong result";
  - the bound against the headcount;
  - the 0^0 trap of the general function.
- **Read through a fetch agent, not by me:** the PIP handbook page and two Wikipedia pages.
- **Not looked up:**
  - The World Bank indicator page refused the request.
  - No primary reference was opened for the name "income gap ratio".
  - No outside package was looked up.
  - No measure was computed on the toy survey.

**Files this brainstorm added,** all untracked: the intent, the approval record, and `GLOSSARY.md` with the one term.

**Next steps: Done**
* **Your move:** To build it, type `/cg Add poverty_gap(dt, line = 3) as the decided intent in .cg-docs/brainstorms/ describes, with a testthat check.` Add your expected value for the toy survey to that line if you have one.
* **Project:** The brainstorm on a depth-of-poverty measure for `toypov` is finished with a decided intent; the function itself is not built, and building it is the next piece of work, small enough for quick work.

[exit code: 0]
