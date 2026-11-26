### B1 setup

> /cg

Reading the project is done. Next I preview what setup would write, without writing anything yet.

Setup has not been done for this project yet, so the guide opened the **setup** playbook. I have only read files so far. Nothing is written, and I did not open the data file.

## What I found

- **Files (measured):** 8 tracked files. Two `.R` files, one `.R` test script, one `.Rd`, `DESCRIPTION`, `NAMESPACE`, `LICENSE`, and one `.csv`. It is an R package called `toypov`.
- **How outputs are made:** there is no `Makefile`, `_targets.R` or main script. The package exports one function, `read_survey()`, and has testthat tests in `tests/testthat/`.
- **Data (measured, not opened):** 1 file, `inst/extdata/survey.csv`. `DESCRIPTION` calls it synthetic, but that is a description and not a classification. Until you classify it, it counts as restricted data.
- **Already here:** no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md`, and no version 1 files.

## Proposal

1. **Packs:** `core` and `lang-r`. Both are installed on this machine.
2. **Pack setting:** `lang-r.r-syntax = data.table-collapse`. The code supports this: `DESCRIPTION` has `Imports: data.table`, `NAMESPACE` has `importFrom(data.table, fread)`, and `R/read_survey.R` calls `fread(path)`. It is also the pack's default.
3. **Verification profile (draft):**
   - **Run command:** none found in the project. The usual check for an R package is `R CMD build . && R CMD check --no-manual toypov_0.0.1.tar.gz` (inferred). It would run against a temporary library. Do you want that as the Run command, or `testthat` alone?
   - **Doctor command:** not found.
   - **Output:** the value `read_survey()` returns. The tests in `tests/testthat/test-read_survey.R` check it: 20 rows, the columns `hhid, welfare, weight`, and an error when a weight is not positive.
4. **Data rules.** Only you can set these. Answer in one reply, for example:
   > `inst/extdata/survey.csv` = Public. Highest level Claude Code may read: Public. Levels: Public; Official Use Only; Confidential; Strictly Confidential.

   If you don't know an answer yet, that item stays open and the file stays restricted.
5. **Files I will create** (from the `--dry-run` preview): `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md` (which holds only `@AGENTS.md`), and `.Rbuildignore`. The `.Rbuildignore` is needed because this is a package. Nothing gets committed.

**Assumptions:** the coding agent is recorded as `Claude Code`. No other `lang-r` settings are needed, since `r-syntax` is the only one its lead skill reads.

**Next steps: Waiting on you**
* **Your move:** reply with "yes" or with corrections to points 1–5. Include your data rules and your choice of Run command, for example: `yes; survey.csv = Public; Claude Code may read Public; levels Public; Official Use Only; Confidential; Strictly Confidential; Run = R CMD check`.
* **Project:** setting up the `toypov` toy package for Compound GPID. Nothing is configured yet, and once you confirm I'll write the files above.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Now I fill the verification profile with the confirmed draft.

Setup is done, and the project is now ready for the guide.

**What you confirmed and I recorded:**
- Packs `core` and `lang-r`, with the setting `lang-r.r-syntax=data.table-collapse`.
- `inst/extdata/survey.csv` is classified **Public**.
- Claude Code may read data up to **Public**. I recorded the agent under the name `Claude Code`.

**What I wrote** (one `cg.py setup` command, then I filled in one file by hand):
- `.cg-docs/config.json`: packs, setting, data rule and approved tool.
- `.cg-docs/verification.md`: a draft profile, filled in as described under "What stays open".
- `AGENTS.md`: the Compound GPID pointer block.
- `CLAUDE.md`: holds only `@AGENTS.md`.
- `.Rbuildignore`: keeps `.cg-docs`, `AGENTS.md` and `CLAUDE.md` out of the package build.

**Status after setup (measured):**
```
phase: ready
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
packs-missing: none
stops: none
```

**What stays open:**
- **Run command:** your yes didn't pick one, so the verification profile is still `draft` and its Run command reads "not found". I wrote `R CMD build . && R CMD check --no-manual toypov_0.0.1.tar.gz` there as an unconfirmed candidate.
- **Doctor command:** none found.
- **Classification levels:** you didn't list your organization's levels, so they aren't recorded. That doesn't block anything now.

Nothing is committed. Status shows 4 new, uncommitted paths: the `.cg-docs/` folder, `AGENTS.md`, `CLAUDE.md` and `.Rbuildignore`.

**Next steps: Done**
* **Your move:** confirm the Run command, for example reply `Run = R CMD check`, or type `/cg <the change you want>` to start work.
* **Project:** `toypov` is set up for Compound GPID (phase ready). The verification profile stays a draft until a Run command is confirmed and run.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

Status read; the quick playbook is open. Next I'm running the risk check before I change anything.

The risk check came back **elevated**, so I need your yes before I change anything.

**What you asked for:** a new exported function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, plus a testthat check that it gives 0.153846 on the toy survey. I'll leave `read_survey()` and its tests alone.

**Why it's elevated:** the function computes a number someone will read. That's the only reason.
- The data file is fine to read: `inst/extdata/survey.csv` is recorded as Public, and Claude Code is cleared for Public data.
- The file count is fine too (5 files).

**What I'll do:**
- **Formula:** `sum(weight[welfare < line]) / sum(weight)`.
  - "Below" means strictly less than, which is the usual poverty headcount rule.
  - On this survey `<` and `<=` give the same answer, because no household has welfare of exactly 3 (I checked: 20 rows, 0 at exactly 3).
- **Packages:** base R and data.table only. I won't add collapse, so there's no new dependency.
- **Errors instead of silent fallbacks:**
  - it stops if `welfare` or `weight` is missing;
  - it stops on an NA or a weight of zero or less;
  - it stops if `line` isn't a single positive number.
- **Files:**
  - `R/headcount.R` (new)
  - `tests/testthat/test-headcount.R` (new)
  - `NAMESPACE` (add the export)
  - `man/headcount.Rd` (generated by roxygen2 into a temporary copy, not your library)
  - `.cg-docs/verification.md` (add a row to the outputs map)

**Not part of this change:**
- no other poverty measures;
- no handling of grouped data;
- no edits to `read_survey()`;
- no commit unless you ask.

**Checks, and what would count as failure:**
1. **The value on the toy survey:** `expect_equal(headcount(read_survey()), 0.153846, tolerance = 1e-6)`. Your figure has 6 decimals, so the tolerance is set now, before the first run. It fails if the result is more than 1e-6 away from 0.153846. I'll run this test before writing the function (it should fail) and again after (it should pass).
2. **Error cases:** a missing column, an NA weight and a bad `line` each raise an error. It fails if any of them returns a value instead.
3. **The full test suite:** `testthat::test_local()`, with the package installed in a temporary library. It fails on any failing test, including the existing `read_survey` tests.

Shall I go ahead with this contract? A plain yes is enough. If you'd rather "below" mean `<=`, say so with your yes.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to go ahead, or `yes, use <=` for "at or below".
* **Project:** toypov has only `read_survey()` so far. This change adds `headcount()`, and nothing else is open.

[exit code: 0]

### C2 yes

> Yes, proceed.

Writing the test first, so I can watch it fail before the function exists.

Before the change, all 6 new tests fail (no `headcount()` exists yet) and the 2 `read_survey` tests pass. Now writing the function.

The NAMESPACE file is hand-written, so roxygen2 left it alone. I'll add the export by hand.

R CMD check returned `Status: OK`. Next I'm adding the outputs-map row and reading the principles for the self-review.

Self-review against P4 next: a rerun to show the value repeats, and a mutation test (`<` changed to `<=` in a scratch copy) to show the tests catch a wrong inequality.

I've added `headcount(dt, line = 3)`. On the toy survey it returns 0.153846153846, which matches your 0.153846 to six decimals (difference 1.5e-07). All checks pass, but I changed check 1 after it first failed (explained below).

**Changed files:**
- `R/headcount.R` (new): returns the weighted share of households with `welfare < line`. Uses base R only, so no new dependency. It stops with an error on missing columns, missing welfare, a missing or non-positive weight, or a `line` that isn't one positive number.
- `tests/testthat/test-headcount.R` (new): 6 tests. One is a small three-household case with one household exactly at the line, to pin down strictly "below".
- `NAMESPACE`: added `export(headcount)` by hand, because roxygen2 doesn't manage this file.
- `man/headcount.Rd` (new): generated by roxygen2.
- `.cg-docs/verification.md`: a new row for `headcount()`.

**Checks (measured):**

| Check | Command | Verdict |
|---|---|---|
| 1. Value is within 1e-6 of 0.153846: failed before the change, passes after | `testthat::test_dir(..., load_package = "installed")`, with the package installed in a temporary library | verified |
| 2. Each error case raises an error | same | verified |
| 3. Full suite: 8 tests, 14 expectations, 0 failures | `testthat::test_local()` | verified |
| Extra: build and check, including examples | `R CMD build` + `R CMD check --no-manual` | verified (Status: OK) |

**How check 1 changed:** I first wrote it as `expect_equal(..., tolerance = 1e-6)`, and it failed. testthat's documentation (for waldo's `compare()`) says its tolerance follows the `all.equal()` rule, which measures a relative difference: here 1.000001e-06, just over the limit. We had agreed on an absolute difference of at most 1e-6, so I rewrote the test to measure exactly that: `expect_lte(abs(headcount(dt) - 0.153846), 1e-6)`. The expected value and the 1e-6 are unchanged.

**Other evidence (measured):**
- Two runs give the identical value.
- The weights matter: 4 of the 20 households are below 3, which would be 0.20 unweighted, and the check would reject that.
- In a scratch copy, changing `<` to `<=` makes the strict-inequality test fail, so the tests catch that mistake.

**Self-review** (I reviewed my own work; no one else did): P3, P4 and P6 all pass.

**Work report:** `.cg-docs/work-reports/2026-11-26-add-headcount-with-testthat-check.md`, status completed; `cg.py validate` found 0 problems.

**Not checked:**
- The project's verification profile has no Doctor or Run command yet. I ran `R CMD check` as a candidate, but you haven't confirmed it as the Run command.
- No cross-check in other software such as Stata. Your 0.153846 was the independent reference.
- An empty survey isn't tested. It would return NaN (inferred: zero divided by zero).

**Noticed but not touching:**
- The R guidance for this project recommends `collapse::fmean()` and `rlang`/`cli` for errors. Both would add dependencies, so I used base R and `stop()`, as `read_survey()` does.
- `NAMESPACE` is hand-written, so roxygen2 won't keep it up to date.
- The project has no `renv.lock` to pin package versions.

Nothing is committed. The temporary libraries and check output are in `/private/tmp/claude-502/-Users-<user>-temp-cg-gate-rerun-16-toy-r-claude/8b781910-2c2e-48c5-986d-907d40792a59/scratchpad`, which only I used; you can delete it at any time.

**Next steps: Done**
* **Your move:** If you want it committed with its work report, reply `commit it`. Otherwise, nothing.
* **Project:** toypov now has `read_survey()` and `headcount()`, and nothing is open. The verification profile stays a draft until you confirm a Run command.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

The survey has an `hhid` column and the package already has `headcount()` as a style model. I'll add `n_households()`, which counts distinct `hhid` values (the sample count, unweighted).

The NAMESPACE file is maintained by hand, so I'll add the export myself and rerun the tests and the examples.

I added `n_households()`, which returns the number of households in the survey. On the toy survey it returns 20, and all 19 tests pass.

```r
n_households(read_survey())
#> [1] 20
```

- **What it counts:** the number of distinct `hhid` values, so a household that appears on two rows is counted once. This is the sample count, not a weighted estimate of how many households the population has. If you meant the weighted number, it's a one-line change to `sum(dt$weight)`.
- **When it stops with an error:** if the `hhid` column is missing or any `hhid` is missing. The messages match the ones `read_survey()` and `headcount()` already use.
- **Files:**
  - The function is in `R/n_households.R`.
  - Its documentation, `man/n_households.Rd`, was generated by roxygen.
  - The tests are in `tests/testthat/test-n_households.R`.
  - I added `export(n_households)` to `NAMESPACE` by hand, because that file isn't generated by roxygen.
- **Not done:** I didn't commit anything. I made this change outside `/cg`, so `.cg-docs/` has no work report for it.

**Next steps: Done**
* **Your move:** Nothing. To get the checks and a work report in `.cg-docs/`, type `/cg` and ask it to add `n_households()`.
* **Project:** toypov now has `read_survey()`, `headcount()` and `n_households()`; none of the changes are committed yet.

[exit code: 0]

### G1 idea

> /cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

Reading the project's records next, then I'll open the brainstorm record.

Writing the facts and the first questions into the brainstorm record now.

I've opened the brainstorm record and read the package. Here is where we are.

**What I think you want:** a second measure next to `headcount()`, so the package reports both how many households are poor and how deep their poverty goes. What I don't know yet: who reads the number, and in what unit.

**What your field calls this.** "How far below the line" is usually called the **depth of poverty**. There are three common measures (source: the `r-analytical` skill's welfare patterns file, which I opened):

- **Poverty gap index, FGT(1).** For each poor household, take how far welfare falls below the line, as a share of the line. Everyone else gets 0. Then take the weighted average over the **whole** population. It reflects both how many are poor and how poor they are.
- **Income gap ratio.** The same average, but over the **poor only**. This is closest to your wording, "how far below the line the poor are". Swapping it for FGT(1) by mistake is the most common FGT error, and the two numbers can differ by 4 times or more.
- **Squared poverty gap, FGT(2).** Like FGT(1), but each gap is squared, so the poorest count for more. It measures *severity* rather than depth.

I'll compare these properly once the goal is settled. One thing to keep in mind: the income gap ratio has a known weakness. If a household just under the line moves above it, the average among the poor can **go up**, even though nobody got poorer. FGT(1) doesn't have this problem. (Inferred from the definitions; I haven't checked it on your data.)

**Round 1.** The three questions are independent. A "yes" takes my recommendation.

1. **D1: Who reads it?** I recommend the same users as `headcount()`: someone who runs the package on one survey and reports one figure next to the headcount. Trade-off: this doesn't design for reports or dashboards. Is that right, or is there a specific reader or publication in mind?
2. **D2: Unit.** I recommend a share of the line (0 to 1), so the figure means the same thing at any line and in any currency. Trade-off: a reader who wants money has to multiply by the line. Yes, or money units?
3. **D3: Same rules as `headcount()`.** I recommend the same definition of poor (welfare strictly below the line, so a household exactly at the line is not poor), the same default line of 3, the same weights and the same input checks. The new function would also stop when welfare is zero or negative, because that would push a gap to 1 or more. `headcount()` doesn't check this today (`R/headcount.R:25-27`), though `read_survey()` does (`R/read_survey.R:14`). Trade-off: a later change to one function must be made in both. Yes?

I didn't open the survey data, and I didn't look up the original FGT paper (Foster, Greer and Thorbecke, 1984). I'm citing it from memory.

**Next steps: Waiting on you**
* **Your move:** answer D1, D2 and D3, for example "1 yes, 2 yes, 3 yes", or give your own answers.
* **Project:** brainstorm on a depth-of-poverty measure for toypov, recorded in `.cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md` (draft). After round 1 comes the choice of measure, then you confirm the intent.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

Your three answers are recorded, along with "keep it as small as you can." Now the options for the measure itself.

**Widen.** These are the ways to get there that differ in kind:

- **Do nothing.** Fails the goal: the package still couldn't say how deep poverty is.
- **A. One function, `poverty_gap()`, returning FGT(1).** Its help page would explain that the average gap among the poor is `poverty_gap() / headcount()`.
- **B. One function returning the income gap ratio** (the average gap among the poor only).
- **C. A general `fgt(dt, line, alpha)`** covering FGT(0), FGT(1) and FGT(2).
- **D. One function returning FGT(1) and the income gap ratio together.**

**Narrow.** C and D fall away because you asked for the smallest change. C duplicates `headcount()`, and D gives the package a new output shape (a list or two columns). That leaves A and B, which cost the same: one R file, one test file, one help page and one NAMESPACE line, with no new dependency.

- **A (FGT(1))** is the standard companion to the headcount. It never rises when someone leaves poverty, and it is always defined. The risk is that a reader takes it for the average gap among the poor and reads it as too small.
- **B (income gap ratio)** matches your wording best, but it has two weak points:
  - It can **rise** when a poor household climbs above the line.
  - When nobody is poor it is 0/0, so it needs a rule of its own for that case.

  Measured on the toy data, it is a weak choice for the package's only depth figure.

A gives you B for free. With weights, FGT(1) = headcount × income gap ratio exactly, so the help page can show readers how to get B in one line. That identity is reasoned from the definitions, not run.

No experiment decides this. It's a matter of definition, not something a script could settle.

**Round 2.** The two questions are independent. A "yes" takes my recommendation.

4. **D4: Which measure?** I recommend A: one new function, `poverty_gap(dt, line = 3)`, returning FGT(1), with a help page that says the average gap among the poor is `poverty_gap() / headcount()`. Trade-off: the figure isn't literally "how far below the line the poor are". A reader who wants that number has to divide by the headcount.
5. **D5: What shows the number is right?** I recommend doing what was done for `headcount()`:
   - you give me the expected FGT(1) on the toy survey before any check runs;
   - I add a small household case with weights, worked out by hand, including one household exactly at the line.

   Trade-off: you have to compute one figure yourself, for example in Stata or a spreadsheet. Without it, the only check is my own arithmetic.

**Next steps: Waiting on you**
* **Your move:** answer D4 and D5, for example "4 yes, 5 yes", or give your own answers.
* **Project:** brainstorm on a depth-of-poverty measure for toypov (draft intent at `.cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md`). After this round I write the goal, scope and assumptions, and you confirm the intent.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

Both answers are recorded, and the intent now passes `cg.py validate` with 0 problems and 0 warnings (measured). Here it is as the file reads (`.cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md`). Since you took up the new terms, I also started a project `GLOSSARY.md` with three entries: headcount ratio, poverty gap index and income gap ratio.

**Goal.** The package says how deep poverty is, not only how many households are poor. It gets one new exported function, `poverty_gap(dt, line = 3)`, which returns the poverty gap index, FGT(1): the weighted average over all households of how far welfare falls below the line, as a share of the line, with 0 for households that are not poor. It's for the same readers as `headcount()`: one survey, one figure reported next to the headcount. Its help page says that the average gap among the poor alone is `poverty_gap() / headcount()`. The change is as small as it can be.

**Out of scope**
- No change to `headcount()`, `read_survey()` or `n_households()`, or to their tests.
- No income gap ratio function, no FGT(2), no general `fgt()`, and no function that returns several measures at once.
- No estimates by group, and no standard errors.
- No money units.
- No new dependency.

**A wrong result**
- **Gap averaged over the poor only.** On the toy survey the figure would be about 6.5 times too large, since 1 / 0.153846 ≈ 6.5 (inferred). Caught by your expected value and by the hand-built case.
- **Weights ignored.** Caught by the hand-built case, because its weights are unequal.
- **A household exactly at the line counted as poor.** This doesn't change FGT(1), because that household's gap is 0 either way. It would only break the help page's link to `headcount()`, so the hand-built case includes one household exactly at the line and checks that link.
- **Result outside [0, 1], or gap not divided by the line.** Caught by a range check and by a case with a line other than 1.
- **Bad input returns a number instead of an error.** Welfare at or below zero, or a missing weight, must stop with an error, and tests expect it to.

**Decisions** (each answered "Yes to each question: I take the answer you recommend.")
- **D1, readers:** the same users as `headcount()`: one survey, one figure.
- **D2, unit:** a share of the line, between 0 and 1.
- **D3, rules:** the same definition of poor, default line, weights and input checks as `headcount()`, plus an error on welfare at or below zero.
- **D4, measure:** approach A, one function returning FGT(1), with the income gap ratio explained in its help page.
- **D5, proof:** you give the expected FGT(1) on the toy survey before any check runs, plus a hand-built weighted case with one household at the line.

**Set aside:** doing nothing, the income gap ratio alone (B), a general `fgt()` (C), and returning both measures together (D).

```
Assumptions I am making:
1. The function is named poverty_gap(). If it is wrong: only the name changes.
2. On an empty survey it stops with an error, not 0/0. This goes one step beyond
   headcount(), which returns NaN there. If it is wrong: one input check changes.
3. The terms go into a new project GLOSSARY.md, outside .cg-docs/. If it is wrong:
   the file is removed and the terms stay in this intent only.
Correct me now.
```

Two things I didn't check: I didn't open the survey data, and I didn't open the original FGT paper. That FGT(1) equals the headcount times the income gap ratio is reasoned from the definitions, not run.

**Is this what you want?** A plain "yes" confirms it, and I'll record it under your name. Anything else I'll take as a change or a question.

**Next steps: Waiting on you**
* **Your move:** reply "yes" to confirm the intent, or say what to change.
* **Project:** brainstorm on a depth-of-poverty measure for toypov; the intent is a draft until you confirm it. After that, `/cg` with the first change (add `poverty_gap()`) is small enough for quick work.

[exit code: 0]

### G4 vague reply

> Sounds good.

I tried to record your reply with `cg.py approve`, and it refused: "Sounds good." reads as agreement without a decision, so nothing was recorded. The intent is still a draft.

Is there anything in it you would change, or anything that is unclear? The parts most worth a second look:

- **Assumption 2:** on an empty survey, `poverty_gap()` stops with an error. That is stricter than `headcount()`, which returns NaN there.
- **D5:** before any check runs, you give me the FGT(1) value you expect on the toy survey, computed outside the package.
- **Out of scope:** no separate income gap ratio function. The help page only shows how to get it as `poverty_gap() / headcount()`.

A plain "yes" confirms the intent as it reads, and I will record it under your name. I will take anything else as a change or a question.

**Next steps: Waiting on you**
* **Your move:** reply "yes" to confirm the intent, or say what to change.

[exit code: 0]

### G5 answer

> Yes.

I recorded your "Yes." The intent is now **decided**. Nothing was built and nothing was committed.

- **Intent:** `.cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md`, status `decided`.
- **Approval record:** `.cg-docs/approvals/2026-11-26-depth-of-poverty-measure.30119e67e1679718.json`. It holds your reply word for word.

**Goal:** add one function, `poverty_gap(dt, line = 3)`, that returns the poverty gap index, FGT(1), next to `headcount()`. Its help page will explain that the average gap among the poor only is `poverty_gap() / headcount()`.

**Decisions:**
- **D1:** it is for the same readers as `headcount()`.
- **D2:** the result is a share of the line, between 0 and 1.
- **D3:** it follows the same rules as `headcount()`, and also stops on welfare at or below zero.
- **D4:** it reports FGT(1) only.
- **D5:** you give the expected value on the toy survey before any check runs, and the tests add a hand-built weighted case.

**Assumptions you confirmed:** the name `poverty_gap()`, an error on an empty survey, and a project `GLOSSARY.md`.

**Set aside:** the income gap ratio alone, a general `fgt()`, and returning both measures together.

**Still to come:** your expected FGT(1) on the toy survey. The work should ask for it before any check runs.

**What I did not check:**
- I did not open the survey data.
- I cited the original FGT paper from memory.
- The rule that FGT(1) equals the headcount times the income gap ratio is reasoned from the definitions. I have not run it.

**Next steps: Done**
* **Your move:** when you have the expected value, type `/cg add poverty_gap() as in the decided intent .cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md; for the toy survey I expect <your FGT(1) value>`.
* **Project:** the depth-of-poverty brainstorm is decided. Next comes the quick-work change that adds `poverty_gap()`. `GLOSSARY.md` and the intent are new, uncommitted files.

[exit code: 0]

### H1 ask for the plan

> /cg plan Write the plan for the work we settled in the brainstorm.

Reading the decided intent and the project files before I write the plan.

Reading the principles the plan is checked against, then I'll write the plan file.

I've written the plan as a draft, and it needs one number from you before I can finish it. The brainstorm decided (D5) that you give the expected FGT(1) on the toy survey before any check runs. I can't work that out myself: this step doesn't open the data, and the check needs a figure that doesn't come from the code.

**Draft:** `.cg-docs/plans/2026-11-26-add-poverty-gap.md`. The file checker reports 0 problems and 0 warnings (measured). The expected value still appears as `VALUE-PENDING`.

**What I take you to want:** one new function, `poverty_gap(dt, line = 3)`, that returns FGT(1) as a share of the line. It is checked against a figure you give and against a small weighted example I worked out by hand, which comes to exactly 1/6. Nothing else in the package changes.

**The plan so far:**
- **Requirements and checks:** 9 requirements, each with a check. Checks C1 to C7 fail today because the function doesn't exist yet. C8 confirms that the existing files and the survey stay byte for byte the same. C9 confirms that `R CMD check` still passes.
- **Slices:**
  1. The function and its value on the toy survey and the hand-built example.
  2. The input checks.
  3. The help page, with the formula `poverty_gap() / headcount()`.
- **Data:** only `inst/extdata/survey.csv`, which is recorded as Public. Nothing stays closed.

Two questions:

1. **What FGT(1) do you expect from `poverty_gap(read_survey())` at line 3?** Give it to 6 decimals, as you did with 0.153846 for `headcount()`.
2. **What tolerance should that check allow?** I recommend an absolute difference of at most 1e-6, the same as for `headcount()`. The cost is that a figure you give with fewer decimals needs a wider tolerance. A yes takes 1e-6.

Once I have your answers, I'll write them into the plan, work out the risk level, review it against the principles myself, and show you the whole plan for approval.

**Next steps: Waiting on you**
* **Your move:** reply with the number and the tolerance, for example: `0.0xxxxx, and yes to 1e-6`.
* **Project:** the plan for adding `poverty_gap()` is a draft at step 2 of 8. Approval comes after your answer.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I added the line to the Never list, and the plan is still a draft. The file checker reports 0 problems and 0 warnings (measured).

- **Never list:** it now ends with "change any file under `data-raw/`", with your words quoted. There is no `data-raw/` folder in the project today (measured), so the rule also means this work creates none. No slice lists a file there.
- **Tolerance:** I took your "Yes" as accepting an absolute difference of at most 1e-6 for the toy-survey check, and wrote that into the plan with your reply quoted. That's my reading, because your reply gave no number. If the "Yes" meant something else, tell me.

The plan still can't be finished without one figure from you:

**What FGT(1) do you expect from `poverty_gap(read_survey())` at line 3?** Give it to 6 decimals, as you did with 0.153846 for `headcount()`.

Once you send it, I'll write it into the plan, work out the risk level, review the plan against the principles myself, and show you the whole plan for approval.

**Next steps: Waiting on you**
* **Your move:** reply with the expected value, for example `0.0xxxxx`.
* **Project:** the plan for adding `poverty_gap()` is still a draft at step 2 of 8, and the expected value is the only open item before approval.

[exit code: 0]

### H3 yes

> Yes.

I can't use that "Yes." as the figure. I asked for a number, and the plan needs it before the toy-survey check (C1) can be written.

A yes doesn't approve the plan at this point either. I haven't put the plan to you for approval yet. Before I can, the expected value has to be in it, the risk level has to be worked out, and the self-review has to be done.

So the question is still open:

**What FGT(1) do you expect from `poverty_gap(read_survey())` at line 3, to 6 decimals?**

If you'd rather not give a figure, there's another way. The brainstorm decided you would give it (D5), so a change needs your say. C1 could check against the hand-built example only, which comes to exactly 1/6, plus a range check that the toy-survey value lies between 0 and 1. The cost is that the toy-survey number itself is no longer compared with anything outside the code. If you want that, reply "use the hand-built case only".

**Next steps: Waiting on you**
* **Your move:** reply with the expected value (for example `0.0xxxxx`), or with `use the hand-built case only`.

[exit code: 0]

### H4 yes

> Yes.

I still can't use "Yes." here. This is the third time the reply hasn't matched the question, so something in how I'm asking must be unclear. Nothing has changed in the plan, and nothing has been approved.

The open question needs one of two replies:

- **A number,** such as `0.051282`. That is the FGT(1) you expect on the toy survey at line 3, worked out outside the package. I recommend this, because it is what the brainstorm decided (D5).
- **The words `use the hand-built case only`.** Then the toy-survey check only confirms that the value lies between 0 and 1. The number itself is checked against nothing outside the code.

If neither fits, tell me what's missing, for example:
- you don't have the figure yet;
- you want me to compute it;
- you meant the "Yes." as approval of the whole plan.

If you want me to compute it, that value would come from the code, so it couldn't serve as the outside check, and it would reopen D5.

**Next steps: Waiting on you**
* **Your move:** reply with a number (for example `0.051282`), with `use the hand-built case only`, or with what is missing.

[exit code: 0]

### H5 yes

> Yes.

I'm stopping the plan here. Asking again won't help: four replies of "Yes." can't settle a question whose answer is a number, and I won't pick the figure for you or take "Yes." as approval.

**Where it stands:**
- **Plan:** `.cg-docs/plans/2026-11-26-add-poverty-gap.md`, status `draft`. The file checker reports 0 problems and 0 warnings (measured). No approval has been recorded, and no project file outside `.cg-docs/` has been changed.
- **Already written in:** the line about `data-raw/` in the Never list, and the 1e-6 absolute tolerance, quoted from your first reply.
- **Still open:** the expected FGT(1) on the toy survey at line 3, shown in the plan as `VALUE-PENDING`.
- **Not done yet:** the risk level, the self-review against P1, P3, P6, P10 and P12, and the approval stop. These follow once the value is in.

A later session picks up from the file, not from this conversation, so you can come back whenever you have the figure.

**Next steps: Waiting on you**
* **Your move:** when you have the figure, type `/cg plan The expected FGT(1) on the toy survey at line 3 is 0.0xxxxx`. If you'd rather drop the outside reference, type `/cg plan use the hand-built case only`.
* **Project:** the plan for adding `poverty_gap()` is a draft paused at step 2 of 8, and only the expected value is missing before approval.

[exit code: 0]

### H6 yes

> Yes.

Nothing has changed: the plan is still a draft, and nothing has been approved or recorded.

I'll wait until you can give the expected FGT(1) on the toy survey at line 3, or tell me to use the hand-built case only.

**Next steps: Waiting on you**
* **Your move:** type `/cg plan The expected FGT(1) on the toy survey at line 3 is 0.0xxxxx`, or `/cg plan use the hand-built case only`.

[exit code: 0]

### H7 yes

> Yes.

The plan is still a draft, waiting for the expected FGT(1) on the toy survey at line 3. Nothing has changed.

**Next steps: Waiting on you**
* **Your move:** type `/cg plan The expected FGT(1) on the toy survey at line 3 is 0.0xxxxx`, or `/cg plan use the hand-built case only`.

[exit code: 0]

### H8 yes

> Yes.

Nothing has changed. The plan is still a draft and only needs the expected FGT(1) on the toy survey at line 3.

**Next steps: Waiting on you**
* **Your move:** type `/cg plan The expected FGT(1) on the toy survey at line 3 is 0.0xxxxx`, or `/cg plan use the hand-built case only`.

[exit code: 0]
