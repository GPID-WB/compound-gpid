### B1 setup

> /cg

Reading done; now I'm getting the list of files setup would write, using a dry run.

Setup has to come first: this project has no `.cg-docs/config.json` yet (status: `phase: setup`, `stops: none`). So far I have only read files. I did not open the data file.

## What I found

- **Files (measured):** 8 tracked files. 3 `.R`, 1 `.Rd`, 1 `.csv`, plus `DESCRIPTION`, `NAMESPACE` and `LICENSE`. It is an R package called `toypov` with one exported function, `read_survey()`.
- **How outputs are made:** there is no `_targets.R`, `Makefile` or main script. The package has testthat 3 tests in `tests/testthat/test-read_survey.R`. I read them but did not run them.
- **Data:** 1 file, `inst/extdata/survey.csv`.
- **Already here:** no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md` or version 1 files.

## Proposal

**1. Packs:** `core,lang-r`. Both are installed on this machine (1.99.0.9000). `lang-r` is needed because the project has `.R` files and a `DESCRIPTION`.

**2. Pack settings:** I recommend `lang-r.r-syntax=data.table-collapse`. The code already uses it:
- `DESCRIPTION`: `Imports: data.table`
- `NAMESPACE`: `importFrom(data.table, fread)`
- `R/read_survey.R:8`: `dt <- fread(path)`

This is also the pack's default.

**3. Verification profile (draft):**
- **Run command:** not found. Nothing in the project turns inputs into outputs; it is a library.
- **Doctor command:** inferred, not run: `R CMD check` on the package, using a temporary library. This is based on `DESCRIPTION` plus `tests/testthat.R` calling `test_check("toypov")`. The project does not state any check command itself.
- **Outputs:**
  - `read_survey()`. Proof: the existing tests. One expects the shipped survey to have 20 rows and the columns `hhid`, `welfare`, `weight`. The other expects an error on a weight of zero.
  - Not covered by tests (inferred from reading): the errors for a missing column, a non-positive or missing `welfare`, and a duplicate `hhid`.

**4. Data rules.** Only you can state these. The `DESCRIPTION` says the data are made up, but that doesn't count as a classification. Until you answer, I treat `inst/extdata/survey.csv` as restricted. Please give:
- the classification of `inst/extdata/survey.csv`, or of the folder `inst/extdata`;
- the highest level your organization lets Claude Code read;
- if you know them, your organization's classification levels, from public to most restricted.

For example, you could copy and adjust:
> `inst/extdata=Public`; Claude Code may read up to `Official Use Only`; levels: `Public;Official Use Only;Confidential;Strictly Confidential`

**5. Files I will write**, from the dry run of `cg.py setup` (it wrote nothing):
- create `.cg-docs/config.json`
- create `.cg-docs/verification.md`
- create `AGENTS.md`
- create `CLAUDE.md`
- create `.Rbuildignore` (needed because this is an R package)

**Assumptions:** I name this agent "Claude Code" in `approved-tools`. I commit nothing.

**Next steps: Waiting on you**
* **Your move:** Reply `yes`, adding your data rules in the format above. To change anything, say which part.
* **Project:** This is first-time guide setup for `toypov`. After your yes I write the five files and check that status shows `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Now I'll fill the verification profile with the confirmed draft.

Setup is done, and status now shows the project is ready.

**What I found:** `toypov` is an R package with 3 `.R` files, 1 `.Rd` and 1 data file (`inst/extdata/survey.csv`). There is no pipeline that builds outputs; the only checks are the testthat 3 tests.

**What you confirmed:** packs `core,lang-r`; `r-syntax` set to `data.table-collapse`; `inst/extdata/survey.csv` is Public; Claude Code may read Public data. I used the name "Claude Code" for this agent.

**Files created:**
- `.cg-docs/config.json`
- `.cg-docs/verification.md`, filled with the draft profile
- `AGENTS.md`, holding the pointer block
- `CLAUDE.md`, which holds just `@AGENTS.md`
- `.Rbuildignore`, so the package check skips the three new items

**Status after setup:**
```
phase: ready
stops: none
packs-missing: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
```

**Still open:**
- The verification profile is still a `draft`. It has no Run command, because the package doesn't have one. The Doctor command (`R CMD check` with a temporary library) is my inference and has not been run.
- The tests don't yet cover three of `read_survey()`'s errors: a missing column, a missing or non-positive `welfare`, and a duplicate `hhid`.
- You didn't give your organization's classification levels, so I left them out. You can add them later by running setup again.
- Nothing is committed.

**Next steps: Done**
* **Your move:** Type `/cg` and then the change you want. For example: `/cg add tests for read_survey()'s missing-column, welfare and duplicate-hhid errors`.
* **Project:** Setup is finished for `toypov`, and the next playbook is `quick`, which opens when you give the guide a request.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I'm reading the project state and the quick playbook. Next I check the risk of this change and then write the function.

I stopped before changing anything. The risk check came back **elevated**, so you need to approve the plan below first.

**Why it stopped:** the new function computes a number that people will read. The survey file is fine for me to read: it is recorded as Public.

**One thing I checked first** (measured, on `inst/extdata/survey.csv`): no household has welfare exactly 3. So "below" (`<`) and "at or below" (`<=`) both give 0.1538461538 here, which matches your 0.153846. The unweighted share is 0.2, so the weights do change the result. I plan to use strictly below (`welfare < line`), the usual poverty headcount definition. On other data, a household sitting exactly at the line would not be counted.

**Plan**
- **Goal:** add an exported `headcount(dt, line = 3)` in `R/headcount.R`. It returns `sum(weight[welfare < line]) / sum(weight)`, computed with data.table or base R. It stops with an error if `welfare` or `weight` is missing, if either has an NA, if a weight is not positive, or if `line` is not a single finite positive number. I also add `export(headcount)` to `NAMESPACE`, write `man/headcount.Rd` with roxygen2, and add a row for `headcount()` to the outputs table in `.cg-docs/verification.md`.
- **Out of scope:**
  - No new dependency: collapse is installed but not in `Imports`, so I won't use it.
  - No change to `read_survey()`, the survey data or `DESCRIPTION`.
  - No other poverty measures, no grouping and no commit.
- **Checks**, in `tests/testthat/test-headcount.R`:
  1. `headcount(read_survey())` equals 0.153846 within ±5e-7, which is half a unit in the sixth decimal you gave. Any value outside that range is a failure. I'll run this once before writing the function to see it fail, then again after.
  2. A small made-up case worked out by hand (welfare `c(2, 3, 4)`, weights `c(1, 1, 2)`, line 3, expected result 0.25). It shows that the weights count and that a household exactly at the line is not counted. Any other result is a failure.
  3. Bad input raises an error: a missing `weight` column, an NA weight, and a `line` of length 2.
  4. The whole suite, with `testthat::test_local()`. Any failure, including in the existing `read_survey()` tests, is a failure.

Do you approve this plan, with `<` as the rule? A plain yes starts the work. If you want `<=` instead, say so.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve the plan as written, or `yes, but use <=` to count households at the line.
* **Project:** the toypov package is set up under Compound GPID with nothing open. This `headcount()` change waits on your approval before any file is touched.

[exit code: 0]

### C2 yes

> Yes, proceed.

The approved plan is loaded. I'm writing the test first so I can see it fail before the function exists.

All three tests fail before the change, as expected. Now the function:

The NAMESPACE file is written by hand, so roxygen2 left it alone. I'm adding the export line myself.

Both broken copies fail the tests (measured): `<=` is caught by the hand-worked case, and the unweighted share by both. Now `R CMD check`:

I made a mistake: I ran a `git stash` I hadn't meant to, and it moved `R/headcount.R` out of the working tree. I'm putting it back now.

The file is back and the stash list is empty. I'm rerunning the tests to confirm the restored file is the one that passed.

Now I read the principles for the self-review and update the verification profile.

Next I add `headcount()` to the outputs table in the verification profile and create the work report.

I added `headcount(dt, line = 3)`. On the toy survey it returns **0.1538461538**, which matches your 0.153846 to within the 5e-7 tolerance we set before the first run (measured). All tests pass, and the work report is recorded as completed.

**What changed**
- `R/headcount.R` (new): returns the weighted share of households with welfare strictly below `line`. It stops with an error if `welfare` or `weight` is missing, if a value is NA, if a weight is not positive, if the table is empty, or if `line` is not a single finite positive number.
- `tests/testthat/test-headcount.R` (new): three tests.
- `NAMESPACE`: I added `export(headcount)` by hand. The file isn't generated by roxygen2, so roxygen2 skipped it.
- `man/headcount.Rd` (new): generated by roxygen2.
- `.cg-docs/verification.md`: a new row for `headcount()` in its outputs table.

**Checks** (all measured)

| Check | Verdict |
|---|---|
| The new tests failed before the function existed (3 failures, exit 1) | verified |
| Survey value equals 0.153846 within 5e-7 | verified |
| Hand-worked case gives 0.25: weights count, and a household exactly at the line is not counted | verified |
| A missing `weight` column, an NA weight and a `line` of length 2 each raise an error | verified |
| Full suite, `testthat::test_local(".")`: PASS 8, FAIL 0, exit 0 | verified |
| The tests catch a broken copy that uses `<=`, and one that ignores the weights | verified |
| `R CMD build` and `R CMD check --as-cran` in a scratch folder: exit 0, example and tests OK | verified |

The `R CMD check` NOTE is only the "New submission" notice about the placeholder maintainer address. I changed no check after it failed.

**One slip, now fixed:** I ran a `git stash` by mistake, and it moved `R/headcount.R` out of the working tree. I restored it with `git stash pop`, and the stash list is now empty. The suite passed again afterwards (measured).

**Self-review against P3, P4 and P6:** all pass. One guard goes slightly past the plan: the error on an empty table. Without it, an empty table would silently return NaN. It has no test.

**Not checked:**
- Tests for an empty table, an NA welfare, and a zero or infinite `line`.
- `cg.py repro` and `cg.py guard`: this install doesn't have them.
- A Run or Doctor command: the verification profile has none.
- An independent reviewer: the review above is my own.

**Noticed but not touching:**
- `DESCRIPTION` doesn't turn on roxygen2 markdown, so the backticks in the Rd files show up as literal text.
- `NAMESPACE` is maintained by hand.
- The project uses `stop()` instead of `rlang::abort()` or `cli::cli_abort()`.

Work report: `.cg-docs/work-reports/2026-11-26-add-weighted-headcount-ratio.md` (validated, 0 problems). Nothing is committed.

The build and check output is in `/private/tmp/claude-502/-Users-<user>-temp-cg-gate-rerun-15-toy-r-claude/456098b6-4232-4e5b-a503-ac46083dc8dc/scratchpad/check`, with the log at `/private/tmp/claude-502/-Users-<user>-temp-cg-gate-rerun-15-toy-r-claude/456098b6-4232-4e5b-a503-ac46083dc8dc/scratchpad/check/check.log`. You can delete that folder now.

**Next steps: Done**
* **Your move:** Nothing. If you want to commit, say "commit the headcount change"; the work report goes in the same commit.
* **Project:** toypov now exports `read_survey()` and `headcount()`, and nothing is open. Tests for the remaining input guards are still to write.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I'm counting sample households, which is one per row, identified by `hhid`. This is not the weighted population estimate (`sum(weight)`).

The NAMESPACE file is written by hand, so I'll add the export there myself.

I added `n_households(dt)`. It returns the number of distinct households in the survey: `n_households(read_survey())` gives `20L`. All 12 tests pass, and `R CMD check` finishes with 0 errors, 0 warnings and 0 notes.

- **What it counts:** the households in the sample, one per distinct `hhid`. It is not the weighted population estimate, which would be `sum(weight)`. If you meant the weighted figure, tell me and I'll add an option for it.
- **Bad input:** it stops with an error if `hhid` is missing or has an `NA`, in the same style as `headcount()`.
- **Files:**
  - `R/n_households.R`: the new function.
  - `man/n_households.Rd`: its help page, generated by roxygen.
  - `tests/testthat/test-n_households.R`: tests for the survey count, duplicate `hhid`, and bad input.
  - `NAMESPACE`: I added `export(n_households)` by hand, because roxygen skips this file (it wasn't generated by roxygen).

This didn't go through `/cg`, so `.cg-docs/` has no work report for it. Nothing is committed.

**Next steps: Done**
* **Your move:** Nothing, unless you want a record or a commit. To record and check the change, type `/cg add n_households()`. To commit it, reply "commit".
* **Project:** toypov now has `read_survey()`, `headcount()` and `n_households()`. All changes are still uncommitted on `main`.

[exit code: 0]

### G1 idea

> /cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

Reading the project and the Compound GPID rules before my first question. Next I create the brainstorm record and look up the field's terms.

I started a brainstorm record and read the package before asking you anything. Nothing is built yet.

**The field's word for this.** "How far below the line the poor are" is called the **depth of poverty**. The World Bank's PIP Methodology Handbook (section 4.1, which I opened) measures it with the **poverty gap index**. That is each poor person's shortfall as a share of the line, averaged over the whole population, with zero for everyone not poor. It also gives a stronger version, the **squared poverty gap**, which gives more weight to the poorest.

**What I think you want:** a second measure next to `headcount()` that also moves when poor households fall further below the line. Two things are still missing: who reads the number, and whether it should also count how many are poor.

Here is what I found in the package:
- `headcount()` counts households weighted by `weight`, using strictly below the line (`R/headcount.R:35`).
- The survey has only `hhid`, `welfare` and `weight` (`R/read_survey.R:9`). With no household size column, any measure can only be over households, not persons as PIP does it.
- A household exactly at the line has a gap of zero, so "strictly below" or "at or below" gives the same depth number. This is reasoned from the formula, not run.

**Round 1.** These three are independent:

1. **Who reads the new number, and what do they do with it?** My guess is that it sits next to the headcount to compare surveys or years. If it is instead meant to describe how poor the poor are on their own, a different measure fits better.

2. **What should move the number?** Take two surveys with the same share of poor households. In one the poor sit just below the line; in the other they sit far below. The new number must tell these apart. Should it **also** rise when more households become poor while their depth stays the same?
   - I recommend **yes, both**. That is the poverty gap index, the field's usual choice.
   - The cost: you can't read it as "the average poor household is X% below the line". That reading needs a different measure, which counts the poor only.

3. **What stays out?** I recommend leaving `headcount()`, `read_survey()` and the data as they are, with no standard errors and one survey at a time. The cost is that the new number comes with no measure of uncertainty.

Once these are settled, I'll lay out the measures that could do this (the poverty gap, the squared gap, the gap among the poor only, a shortfall in money terms, one function for the whole family) and put the choice to you.

Record: `<project>/.cg-docs/brainstorms/2026-11-26-how-far-below-the-line-the-poor-are.md` (status `draft`, D1 to D3 open).

**Next steps: Waiting on you**
* **Your move:** Answer questions 1 to 3, for example: "1: compare years next to headcount. 2: yes, both. 3: yes."
* **Project:** This is the brainstorm for a poverty depth measure in `toypov`. Once the goal is settled I'll compare the measures, and nothing gets built until you confirm the intent.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I recorded your three answers in the intent, each with your words. Now the measures.

**Widen.** I found five ways to meet the goal:

- **A. Poverty gap index**, as a new `poverty_gap(dt, line = 3)`. For each household, the gap is (line − welfare) / line when welfare is below the line, and zero otherwise. The function returns the weighted mean of that gap over all households.
- **B. One general function**, `fgt(dt, line = 3, alpha = 1)`. Alpha 0 gives the headcount, 1 the poverty gap and 2 the squared gap.
- **C. Squared poverty gap** alone. This measures severity: it gives more weight to the poorest.
- **D. Average gap among the poor only**, called the income gap ratio.
- **E. Do nothing**, or give the shortfall in money terms.

**Narrow.** Three of these fall away because of your answers:
- **D** doesn't rise when more households become poor, so it fails your answer to question 2. It also has no value when nobody is poor.
- **E**: doing nothing leaves depth unmeasured, and an amount in money can't be compared across lines or years, which fails your answer to question 1.
- **C** answers a question you didn't ask, about inequality among the poor, and is harder to read than A.

That leaves two that really differ:

| | A. `poverty_gap()` | B. `fgt(alpha)` |
|---|---|---|
| Cost | One function, one test file, one export, no new dependency | Same files, plus an `alpha` argument and its checks |
| Risk | Someone reads it as "the average poor household is X% below the line". In fact it is that figure times the headcount. | Two functions then compute the headcount. An unchecked `alpha` gives nonsense. It is more than you asked for. |
| Must be true, not checked | `weight` is the same household weight `headcount()` uses, so the two numbers cover the same population | Same |

**What would show the number is right**, apart from you or me (reasoned from the formula, not run):
- an expected value that you state for the shipped survey before any code exists, as you did for the headcount;
- a small case worked through by hand;
- two properties that always hold: the poverty gap is never above the headcount, and it is zero when nobody is below the line.

This choice is about what the number means. Running code can't settle it, so it needs no experiment.

**D4. Which measure to add?** I recommend **A, `poverty_gap(dt, line = 3)`**: it is the smallest change and matches your answers. The trade-off is that severity isn't covered, so a later squared gap would be a second function, where B would only need a new `alpha`.

Intent updated with D4 open: `<project>/.cg-docs/brainstorms/2026-11-26-how-far-below-the-line-the-poor-are.md`

**Next steps: Waiting on you**
* **Your move:** Answer D4, for example: "A, poverty_gap()" or "B, fgt()".
* **Project:** In the poverty depth brainstorm, the goal and scope are settled. After you choose the measure I'll write the restatement and the assumptions, and ask you to confirm the intent.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I recorded your choice: D4 is A, a single `poverty_gap(dt, line = 3)`. The intent is complete, and `cg.py validate` printed `problems: 0, warnings: 0`. Here it is as the file reads.

**Goal**
Add to `toypov` one measure of how far below the poverty line the poor households are: the poverty gap index, as a new exported function `poverty_gap(dt, line = 3)`. It returns the weighted mean, over all households, of each household's shortfall as a share of the line, with zero for households not below it. It is read next to `headcount()` to compare surveys or years. So it rises both when the poor fall further below the line and when more households become poor. The change is kept as small as possible.

**Out of scope**
- No change to `headcount()`, `read_survey()` or the survey data.
- No squared poverty gap, Watts index, general FGT function or income gap ratio.
- No standard errors or other measure of uncertainty.
- One survey at a time: no grouping by region, year or other unit.
- No measures over persons, because the survey has no household size.
- No new package dependency.

**A wrong result**
- On the shipped survey, a value that differs from the expected value you state before the code is written, beyond a tolerance fixed in advance.
- A value above `headcount()` for the same table and line, below 0, or above 1 when welfare is positive.
- A value other than 0 when no household is below the line.
- A value that ignores the weights, so it equals the unweighted mean of the gaps.
- A value averaged over the poor only. It would equal the poverty gap divided by the headcount, so it would be too large whenever some households are not poor.
- A household exactly at the line with a gap other than 0.
- A different number from a case worked through by hand with unequal weights.

**Decisions** (each answered with your words: "Yes to each question: I take the answer you recommend. Keep it as small as you can.")

| ID | Decision | Your answer |
|---|---|---|
| D1 | Who reads it | Read next to `headcount()` to compare surveys or years |
| D2 | What moves it | Both the depth and the number of poor households |
| D3 | What stays out | `headcount()`, `read_survey()` and the data unchanged; no standard errors; one survey at a time; as small as possible |
| D4 | Which measure | A: `poverty_gap(dt, line = 3)`, the weighted poverty gap index over households |

**Approaches set aside:** B, a general `fgt(alpha)`; C, the squared gap alone; D, the income gap ratio; E, doing nothing or a shortfall in money. The reasons are in the intent's table.

```
Assumptions I am making:
1. `weight` is a household weight, the same one `headcount()` uses. If it is wrong: both measures are weighted wrongly in the same way, and the fix is in the data, not in `poverty_gap()`.
2. `poverty_gap()` makes the same input checks as `headcount()` and adds none. It does not refuse welfare at or below zero, which `read_survey()` already refuses. If it is wrong: a table built by hand with such welfare gives that household a gap of 1 or more, with no error.
3. `line` has the same meaning and default (3, in welfare units) as in `headcount()`. If it is wrong: the two numbers are not read at the same line.
4. A household is poor when welfare is strictly below the line, as in `headcount()`. A household at the line has a gap of 0 either way, so the value does not change.
5. You will state an expected value for the shipped survey before code is written. If not: the only check against the code is a case worked through by hand.
Correct me now.
```

I also created `GLOSSARY.md` at the project root with two terms you took up: **depth of poverty** and **poverty gap index**.

What I didn't check: I opened no data file and ran no code, so every property above is reasoned from the formula, not run. My only outside source is the PIP Methodology Handbook, section 4.1. Its formulas are over persons and leave out weights.

**Is this intent what you want?** A plain "yes" confirms it, and I'll record it under your name. I'll take anything else as a change or a question.

**Next steps: Waiting on you**
* **Your move:** Reply "yes" to confirm the intent, or say what to change, for example: "assumption 2: refuse welfare at or below zero".
* **Project:** The poverty depth brainstorm is fully written and checked, and is waiting for your yes. After that, the first change is `/cg add poverty_gap()` as in the intent.

[exit code: 0]

### G4 vague reply

> Sounds good.

I tried to record your reply with this line:

`cg.py approve ".cg-docs/brainstorms/2026-11-26-how-far-below-the-line-the-poor-are.md" --reply 'Sounds good.'`

The tool refused it, saying that "sounds good" agrees but doesn't decide. Nothing was recorded, and the intent is still a `draft`.

Is there anything in the intent you would change, or anything unclear? The parts most likely to need a second look:

- **Assumption 2:** `poverty_gap()` won't refuse welfare at or below zero. If you'd rather it refused such welfare, that adds one check.
- **Assumption 5:** before any code is written, you state the poverty gap you expect for the shipped survey, as you did for the headcount.

If it reads as you want, reply with a plain "yes".

**Next steps: Waiting on you**
* **Your move:** Reply "yes" to confirm the intent as shown, or name the change, for example: "assumption 2: refuse welfare at or below zero".
* **Project:** The poverty depth brainstorm is still a draft until you give a plain yes.

[exit code: 0]

### G5 answer

> Yes.

I recorded your yes. The intent is now `decided`, and nothing has been built yet.

- **Intent:** `<project>/.cg-docs/brainstorms/2026-11-26-how-far-below-the-line-the-poor-are.md`, status `decided`. The approval record is `.cg-docs/approvals/2026-11-26-how-far-below-the-line-the-poor-are.12e03379f62c4627.json`, under your name.
- **Goal:** add `poverty_gap(dt, line = 3)`. It returns the weighted poverty gap index over households and is read next to `headcount()` to compare surveys or years.
- **Your decisions:**
  - D1: it is read next to the headcount.
  - D2: both how deep and how many move it.
  - D3: `headcount()`, `read_survey()` and the data stay unchanged; no standard errors; one survey at a time; as small as possible.
  - D4: approach A, the single function.
- **Set aside:** a general `fgt(alpha)`, the squared gap alone, the income gap ratio, and doing nothing or a shortfall in money.
- **Assumptions you confirmed:**
  1. `weight` is the household weight.
  2. No new welfare check is added.
  3. `line` means the same as in `headcount()`, with the default 3.
  4. A household is poor when welfare is strictly below the line.
  5. You state an expected value before code is written.
- **Also changed:** a new `GLOSSARY.md` at the project root, with "depth of poverty" and "poverty gap index".

How I know these things:
- **Measured:** the approval and the `decided` status, from the tool's output.
- **Pointed at:** the facts about the package, from the `file:line` sources in the intent.
- **Inferred:** the properties a correct result must have, such as never above the headcount and zero when nobody is poor. They come from the formula and have not been run.
- **Not checked:** I opened no data file, ran no code, and used only one outside source, PIP Handbook section 4.1. Nothing is committed.

The first change is small enough for quick work. Before it starts, work out the poverty gap you expect for the shipped survey, to six decimals.

**Next steps: Done**
* **Your move:** Type `/cg add poverty_gap(dt, line = 3) as in the decided intent; for the shipped survey I expect <your value>`.
* **Project:** The poverty depth brainstorm is decided. The next piece of work is adding `poverty_gap()` through `/cg`.

[exit code: 0]
