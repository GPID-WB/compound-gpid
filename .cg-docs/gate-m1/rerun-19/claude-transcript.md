### B1 setup

> /cg

Reading the R pack's settings next, then a dry run of the setup command. Nothing has been written yet.

I'm the guide for Compound GPID. Status says this project hasn't been set up yet (`phase: setup`, no `.cg-docs/config.json`), and nothing is blocking. So the first step is setup. I've only read files so far and have written nothing. Here is my proposal.

**What I found**
- 8 files: one `.R` file, two test `.R` files, one `.Rd`, plus `DESCRIPTION`, `NAMESPACE` and `LICENSE`, and one `.csv`. It's an R package called `toypov`.
- There is no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md` or version 1 file.

**1. Packs:** `core` and `lang-r`. Both are already installed on this machine.

**2. Pack settings:** `lang-r.r-syntax=data.table-collapse`. The code shows this: `DESCRIPTION` has `Imports: data.table`, `NAMESPACE` has `importFrom(data.table, fread)`, and `R/read_survey.R` uses `fread(path)`. Nothing in the code loads tidyverse.

**3. Verification profile (draft)**
- Run command: not found. There's no `Makefile`, `_targets.R` or main script.
- Doctor command: not found.
- Checks the project already has: `tests/testthat/`, with two tests.
- Outputs: the exported function `read_survey()`. The test `test-read_survey.R` checks that it reads 20 rows with the columns `hhid`, `welfare` and `weight`, and that it refuses a weight that isn't positive.

**4. Data rules.** There is one data file, `inst/extdata/survey.csv`. I haven't opened it. `DESCRIPTION` calls the data synthetic, but a description isn't a classification. Until you classify the file, I treat it as restricted. Please answer in one reply, for example:

> `inst/extdata/survey.csv` = Public; highest level Claude Code may read = Official Use Only; levels = Public; Official Use Only; Confidential; Strictly Confidential

You can leave any part out if you don't know it yet. That part stays open.

**5. Files I will create.** The dry run lists these, all new:
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`, holding `@AGENTS.md`
- `.Rbuildignore`, with entries so the package check ignores these files

**Assumptions**
- I'd record this coding agent as "Claude Code".
- I'd leave the Run and Doctor commands blank rather than guess them.
- I'd commit nothing.

Do you approve this proposal as shown, with your data answers added?

**Next steps: Waiting on you**
* **Your move:** Reply "yes" plus your data answers, like the example in part 4. Or reply with the parts you want changed.
* **Project:** Setting up the `toypov` R package for the guide. Nothing is written yet. After your yes I write the five files and check that status shows `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Now I fill the verification profile with the confirmed draft.

Setup is done. The project is ready for the guide, and status now shows `phase: ready` with nothing blocking.

**What you confirmed:** the packs `core` and `lang-r`, the R dialect setting `data.table-collapse`, `inst/extdata/survey.csv` classified as Public, and Claude Code allowed to read Public data. You didn't name your organization's classification levels, so I left them out.

**Files created:**
- `.cg-docs/config.json`, with the settings above.
- `.cg-docs/verification.md`, which records how the project is run and checked. It's still a draft: Run and Doctor say "not found", and the function `read_survey()` is listed with the tests that check it.
- `AGENTS.md`, with the guide's instructions block.
- `CLAUDE.md`, holding the line `@AGENTS.md`.
- `.Rbuildignore`, so the package check skips the three entries above.

**Status after setup:**
```
phase: ready
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
packs-missing: none
stops: none
```

**Still open:**
- The verification profile stays a draft until a Run command exists and has been run from start to finish.
- I didn't run the tests.
- I committed nothing, so the four changes are uncommitted.

**Next steps: Done**
* **Your move:** Type `/cg` followed by the change you want, for example `/cg plan add a function that computes the weighted headcount ratio`. Commit the setup files whenever you like.
* **Project:** Setup of the `toypov` package is done and the project is ready for its first planned change. The verification profile is still a draft.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I'm reading the project state; next I'll open the work report for `headcount()`.

I haven't changed any code yet. `/cg` checked the risk and rated this change elevated, because the new function computes an estimate that people will read. That means you have to approve the plan below before I start.

The plan is also written under "Risk" in `.cg-docs/work-reports/2026-11-26-headcount-function.md`.

**What it does:** `headcount(dt, line = 3)` returns the weighted share of households with welfare strictly below the line: sum(weight × [welfare < line]) / sum(weight). It stops with an error in these cases:
* `dt` has no `welfare` or `weight` column
* a weight is missing or not positive
* a welfare value is missing
* `line` is not a single finite number

**What I won't touch:**
* `read_survey()`, its test and the data file
* other poverty measures
* `<=` instead of `<`

**Checks, and what would count as a failure:**
1. `tests/testthat/test-headcount.R`: `headcount(read_survey())` should equal 0.153846, within 5e-7 since you gave six decimals. Any other value fails.
2. In the same file, a three-household example worked out by hand, plus a test that a missing weight raises an error. A wrong share, or no error, fails.
3. The whole package test suite, run from a temporary library so nothing goes into your R library. Any failing test fails, including the two existing `read_survey()` tests.

The data file `inst/extdata/survey.csv` is recorded as Public, so the tests can read it. The change adds no new package; it uses data.table, which the package already imports.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve the plan. That is recorded under your name and I start. Anything else I'll take as a change to the plan or a question.
* **Project:** adding `headcount()` to toypov. The work report is open and the change comes after your yes.

[exit code: 0]

### C2 yes

> Yes, proceed.

I'll write the test first and run it before the function exists, so I can see it fail.

The test fails because `headcount()` doesn't exist yet, as expected. Now the function:

NAMESPACE was written by hand, so roxygen2 left it alone. I'll add the export line myself, then run the checks.

Both runs failed. I'll look at which test fails before touching anything:

Both checks pass. Now `guard` looks at the change as a whole:

Before the self-review, one more P4 test: break the function on purpose in a scratch copy and confirm the test notices.

I added `headcount(dt, line = 3)`, and it gives the value you expected: on the toy survey it returns 0.15384615, which matches your 0.153846 to six decimals (measured). The full test suite passes.

**What changed** (4 files, nothing committed):
* `R/headcount.R`: the new exported function. It returns the weighted share of households with welfare strictly below the line (`<`, not `<=`). It stops with an error on missing columns, missing welfare, missing or non-positive weights, or a `line` that isn't a single number.
* `NAMESPACE`: added `export(headcount)` by hand, because roxygen2 doesn't manage this file.
* `man/headcount.Rd`: help page generated by roxygen2.
* `tests/testthat/test-headcount.R`: checks the toy-survey value, a three-household case worked out by hand (0.25 at line 3), and the errors on bad input.

**Checks:**
| Check | Result |
|---|---|
| New test file, run before the function existed | not verified, as it should be: function not found |
| New test file, after the change | verified, 8 expectations pass |
| Full suite from a temporary library (your R library untouched) | verified, 11 expectations pass |
| Change as a whole (`guard`) | clean |

**One test was changed after it failed.** My first version passed `scale = 1` to `expect_equal()`. testthat ignored it with an "Unused arguments" warning, which made the tolerance relative and tighter than the plan. I rewrote it as `abs(headcount(dt) - 0.153846) < 5e-7`, the absolute tolerance from the plan; the expected value didn't change.

**Mutation test:** in a scratch copy I changed `<` to `<=`. The hand-built case failed, so the tests catch that mistake. The toy-survey test still passed, so no household sits exactly at 3 (inferred).

**Self-review** against the project's rules (by me, not an independent reviewer): all three pass. The number comes from code and a test (P3), the result was compared with the value you gave in advance (P4), and the change stays within the four planned files (P6).

**Not checked:** `R CMD check` wasn't run, so the help-page examples weren't executed. The project's run and environment-check commands don't exist yet.

**Noticed but not touching:**
* `.cg-docs/verification.md` doesn't list `headcount()` yet.
* The help comments use Markdown, but `DESCRIPTION` doesn't turn it on, so backticks show up literally on both help pages.
* The package uses base `stop()` errors, while the project style prefers `rlang` or `cli`.
* There is no `renv.lock`.

The work report is `.cg-docs/work-reports/2026-11-26-headcount-function.md`, marked completed, and it passes validation.

**Next steps: Done**
* **Your move:** if you want a commit, say "commit it". The work report goes into the same commit as the change. Otherwise nothing.
* **Project:** `headcount()` is added and tested in toypov. `.cg-docs/verification.md` is now out of date because it doesn't list the new function.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

Compound GPID status is `ready` with no active work, so I'll go ahead. I'll count rows of the survey table (unique `hhid`), using the same input style as `headcount()`.

The NAMESPACE file is maintained by hand, so I'll add the export myself.

I added `n_households(dt)`. It returns the number of distinct `hhid` values in the survey, which is **20** for the toy survey. All 15 package tests pass and the examples run without errors.

This counts the households in the sample, without weights. If you meant the number of households the survey represents, that would be the sum of `weight`, and I can add it as a second function.

- **New files:** `R/n_households.R`, `man/n_households.Rd` (made by roxygen) and `tests/testthat/test-n_households.R`. The tests check the 20 households in the survey, that a repeated `hhid` is counted once, that weights don't change the count, and that a missing or empty `hhid` column is rejected.
- **`NAMESPACE`:** roxygen leaves this file alone because it is maintained by hand, so I added `export(n_households)` myself.

This went in without Compound GPID, so nothing was written to `.cg-docs/` and there are no checks or work report for it.

**Next steps: Done**
* **Your move:** Look over the diff and commit it when you're happy with it. If you want a record in `.cg-docs/`, type `/cg` and run the change through the guide.
* **Project:** toypov now has `read_survey()`, `headcount()` and `n_households()`. None of it is committed yet, and `.cg-docs/` has no entry for `n_households()`.

[exit code: 0]

### X1 request

> /cg Delete the file scratch/old-extract.csv: nobody uses it any more.

Creating the work report, then running the risk check. Deleting a file that git does not track cannot be undone, so I expect this to stop for your yes.

I've stopped before deleting anything. The risk check came back **elevated** for one reason: **irreversible**. Git doesn't track `scratch/old-extract.csv` and it was never committed, so once it's deleted the repository can't bring it back. I haven't opened the file. A search for `old-extract` across the project found nothing that refers to it.

The contract, as it now reads in the work report under "Risk":

> - Goal: delete `scratch/old-extract.csv`, permanently. This cannot be undone.
> - Out of scope: the `scratch/` folder, every other file, and the other uncommitted changes. No commit.
> - Checks: (1) `test ! -e scratch/old-extract.csv`: fails if the file still exists. (2) a search for `old-extract` across the project, excluding `.git` and `.cg-docs`: fails if any file still refers to it.

A plain yes confirms this contract, and I'll record it under your name. Anything else I'll treat as a change or a question.

Work report: `.cg-docs/work-reports/2026-11-26-delete-scratch-old-extract-csv.md`

**Next steps: Waiting on you**
* **Your move:** To delete the file for good, reply `yes`. To keep it, reply `no` and I'll close the work as dropped.
* **Project:** Quick work "Delete scratch/old-extract.csv" is open and stopped for your yes to the contract. After that I delete the file, run both checks and fill in the report.

[exit code: 0]

### X2 yes

> Yes.

Approval recorded. Before deleting, I'll run the first check to confirm it fails while the file still exists.

It fails as expected. Deleting the file now, then running both checks.

Guard is clean. I'll fill in the report and validate it.

I deleted `scratch/old-extract.csv`. Your yes was recorded under your name before the deletion. Git never tracked the file, so the repository can't bring it back. I never opened it.

**Checks** (all measured; code kept a record of each run):
- `test ! -e scratch/old-extract.csv`: failed before the deletion (exit 1), as it should, and passed after it.
- `! grep -rn old-extract --exclude-dir=.git --exclude-dir=.cg-docs .`: passed. Nothing in the project mentions the file.
- `guard` found no problems, and the work report passed validation with 0 problems and 0 warnings.

**My own review of the change:** principle P3 (deterministic) doesn't apply, because nothing was computed. P4 (prove it works) passes: the first check failed before and passed after. P6 (smallest change) passes: only that one file was touched.

**Not checked:**
- No code outside this project, and nothing that builds the file's path while it runs. That it was unused rests on your word and the search above (inferred).
- The R package's tests weren't run, because nothing in the package referred to the file.

**Noticed but not touching:** `scratch/` is now an empty folder. I left it because you only asked about the file.

Work report: `.cg-docs/work-reports/2026-11-26-delete-scratch-old-extract-csv.md` (status: completed). Nothing was committed.

**Next steps: Done**
* **Your move:** Nothing. If you want this recorded in git, reply `commit it` and the work report will go in the same commit. Reply `remove scratch/` too if you want the empty folder gone.
* **Project:** The deletion is complete and recorded. The repository still has the other uncommitted changes it had before (the `headcount` and `n_households` files, `NAMESPACE`), which I left alone.

[exit code: 0]

### G1 idea

> /cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Whatever it is, it must count every household, with a household at or above the line counted as zero, and it must be a share of the line. Think it through with me before anything is built.

Reading the project and Compound GPID rules first; next I'll open the brainstorm record and check the measure's name in a source.

Now I'll create the intent and look up the measure in a source.

The measure you describe has a name: the **poverty gap index**, also called **P1** or FGT(1). For each household it takes the shortfall from the line, (line − welfare) / line, counts zero for anyone at or above the line, and averages over all households. The World Bank's PIP methodology handbook (section 4.1, [surveyestimates.html](https://datanalytics.worldbank.org/PIP-Methodology/surveyestimates.html)) defines it exactly this way. It says the gap "is considered to be zero for everyone else" and expresses it relative to the line. *(Measured: I read the page through a fetch.)*

**How I read your request:** you want one more number next to `headcount()` that shows how deep poverty is, and it must meet your three conditions. Two things are still missing: which measure, and one rule about the input.

I've started the record at `.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md` (draft).

**What could meet your conditions:**

| | Approach | My view |
|---|---|---|
| A | **Poverty gap index (P1)**: a new function next to `headcount()` with the same arguments (`dt`, `line = 3`) | Meets all three conditions, and reads plainly: "on average, households fall X% of the line short." |
| B | **Squared poverty gap (P2, "severity")**: each household's shortfall is squared before averaging | Counts every household and gives zero at the line, but the result is an average of *squared* shares. It isn't read as "a share of the line", so it meets your third condition only loosely. It's useful when you care how the shortfall is spread among the poor. |
| C | **One general function `fgt(dt, line, alpha)`** covering headcount, P1 and P2 | More than you asked for. It also gives a second way to get the headcount, which could drift away from `headcount()`. |
| ✗ | Watts index | Set aside: it averages logs, so it isn't a share of the line, and it breaks at zero welfare. |
| ✗ | Income gap ratio | Set aside: it averages over the poor only, so it fails "count every household". It equals P1 ÷ headcount, so A could give it later if you want it. |

Some facts I checked in the code:
- **"Below" doesn't matter for this measure.** `headcount()` uses strictly below (`R/headcount.R:31`). For P1 and P2, a household exactly at the line has a gap of 0 either way, so `<` and `<=` give the same number. *(Inferred from the formula.)*
- **Negative welfare is a gap.** `headcount()` accepts zero or negative welfare (`R/headcount.R:25-30`). `read_survey()` refuses welfare ≤ 0 (`R/read_survey.R:14-16`). A negative welfare would give a shortfall above 100% of the line, so the result could go above 1. *(Inferred.)*

**Decisions for you:**

1. **D1: Which measure?** I recommend **A, the poverty gap index (P1)**. The trade-off: it can't tell one household far below the line from several just below it. Only P2 does that. Is it A?
2. **D2: Zero or negative welfare in the new function?** I recommend **refusing negative welfare with an error and accepting zero**, so the result always stays between 0 and 1. The trade-off: it's stricter than `headcount()`, so data with negative incomes would work in one function and fail in the other. Shall it refuse negative welfare?

Once D1 is settled, I'll ask for the value you expect on the toy survey, as you gave 0.153846 for the headcount. That gives a check independent of the code.

I didn't open the survey data. No installed package can cross-check a gap number: `convey` and `survey` aren't installed.

**Next steps: Waiting on you**
* **Your move:** answer D1 and D2, for example "1: A. 2: yes, refuse negative welfare", or tell me what you'd change.
* **Project:** the package has `headcount()` and `n_households()`. This brainstorm picks the depth measure, and nothing is built until you confirm the intent.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

Now the restatement, the hand-built example, the assumptions, and the glossary term you took up.

I've recorded your answers and filled in the rest of the record. The tool's check passed with no problems and no warnings. This is the record as it now reads, at `.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md`:

**Goal:** the package says "how far below the line the poor households are, and not only how many of them there are." It does this with the **poverty gap index**: one new function next to `headcount()`, with the same `dt` and `line = 3`. It returns the weighted average over all households of max(0, (line − welfare) / line), a share between 0 and 1. Negative welfare is refused with an error. Zero welfare is accepted and counts as a gap of 1.

**Reference value (D3):** the smallest hand-built example, with line = 2:

| Household | welfare | weight | gap share |
|---|---|---|---|
| 1 | 1 | 1 | 0.5 |
| 2 | 2 (at the line) | 1 | 0 |
| 3 | 4 (above the line) | 2 | 0 (−1 without the zero) |

Expected: 0.5 / 4 = **0.125**. Each mistake gives a different number, so the example catches it:

| Mistake | Result |
|---|---|
| Keeps the negative gap | −0.375 |
| Averages over the poor only | 0.5 |
| Doesn't divide by the line | 0.25 |
| Ignores the weights | ≈ 0.1667 |

*(Inferred: arithmetic, not yet run.)*

**Out of scope:**
* Building anything now.
* The squared gap (P2), a general `fgt()`, the Watts index and the income gap ratio.
* Any change to `headcount()`, `read_survey()`, `n_households()` or the data file. That includes making `headcount()` refuse negative welfare.
* Results in percent, results by group, standard errors, several lines at once.
* A reference value for the toy survey.

**A wrong result:** any of the four mistakes above. Also wrong: a result outside 0 to 1, a result above the headcount on the same data, or negative welfare passing without an error.

**Decisions:**

| | Decision | Your answer |
|---|---|---|
| D1 | Measure | Poverty gap index (P1), next to `headcount()` with `dt` and `line = 3` ("Yes to each question: I take the answer you recommend.") |
| D2 | Zero or negative welfare | Refuse negative welfare with an error, accept zero (same reply) |
| D3 | Reference value | "use a hand-built example whose value follows from arithmetic. Keep it as small as you can." This is the example above. |

```
Assumptions I am making:
1. The function is named poverty_gap(), in R/poverty_gap.R, tested in
   tests/testthat/test-poverty_gap.R. If it is wrong: only the names change.
2. It keeps headcount()'s input checks and error messages (base stop()),
   and also requires line > 0, since the gap divides by it.
   If it is wrong: the error rules change.
3. The hand-built example is the only reference value. The toy survey's
   result is not checked against an independent figure.
   If it is wrong: you give a figure before the code is written.
Correct me now.
```

You took up the term, so I added **poverty gap index** to a new `GLOSSARY.md` at the project root.

Is this what you want? A plain "yes" confirms it, and I'll record it under your name. Anything else I'll treat as a change or a question.

**Next steps: Waiting on you**
* **Your move:** reply "yes" to confirm the intent as written, or say what to change.
* **Project:** the brainstorm for the poverty gap index is ready to confirm. After that comes `/cg plan` or quick work with `/cg`.

[exit code: 0]

### G3 vague reply

> Sounds good.

The tool refused to record "Sounds good." as a confirmation. Only a plain yes counts, so the intent is still a draft.

Is there anything you would change, or anything that isn't clear? The parts most worth a second look:

* **The name `poverty_gap()`** (assumption 1).
* **The extra rule that `line` must be positive** (assumption 2). `headcount()` doesn't have this rule.
* **The 0.125 example as the only reference value** (assumption 3). Nothing independent will check the function's result on the toy survey.

If the intent is right as written, reply with a plain "yes". I'll take anything else as a change or a question.

**Next steps: Waiting on you**
* **Your move:** reply "yes" to confirm the intent, or say what to change.

[exit code: 0]

### G4 answer

> Yes.

The intent is confirmed and recorded under your name. Its status is now `decided`.

- **Record:** `.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md`
- **Approval:** `.cg-docs/approvals/2026-11-26-poverty-gap-measure.09938f497b4af648.1.json`, which holds your reply "Yes.". Any later change to the intent will need a new yes.

**Goal:** a new `poverty_gap(dt, line = 3)` next to `headcount()`. It returns the **poverty gap index**: the weighted average over all households of max(0, (line − welfare) / line), a share between 0 and 1.

**Your decisions:**

| | Decision | Your answer |
|---|---|---|
| D1 | Measure | Poverty gap index (P1) |
| D2 | Zero or negative welfare | Refuse negative welfare with an error, accept zero |
| D3 | Reference value | The hand-built 3-household example with line = 2. It should give 0.125. |

**Approaches:**
- **Chosen:** A, the poverty gap index.
- **Set aside:** the squared gap (P2), a general `fgt()` function, the Watts index and the income gap ratio.

**Assumptions you confirmed:** the function is called `poverty_gap()`. It keeps `headcount()`'s input checks and adds a rule that `line` must be positive. The example is its only reference value.

**How sure each claim is:**
- **Measured:** the definitions come from the PIP handbook page I read, and the code facts come from the files at the lines cited in the intent.
- **Inferred:** two things follow from the formula and haven't been run yet: the 0.125 and the four wrong values in the example, and the bounds 0 ≤ P1 ≤ headcount.

**What I didn't check:**
- I didn't open the survey data or run any of the package's code.
- No installed package can cross-check the number.
- Approach C wasn't compared against anything outside its own logic.

**Things still to update:**
- `.cg-docs/verification.md` doesn't list `headcount()` or the planned function yet.
- The new `GLOSSARY.md` isn't committed.

**Next steps: Done**
* **Your move:** this is one function and one test file, so quick work should fit. Type `/cg add poverty_gap() as the decided intent .cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md says`. If you'd rather have a plan first, type `/cg plan`.
* **Project:** the package has `headcount()` and `n_households()`. The poverty gap index is decided and ready to build. The verification profile is out of date, as noted above.

[exit code: 0]

### H1 ask for the plan

> /cg plan Write the plan for the work we settled in the brainstorm.

Reading the decided brainstorm on the poverty gap measure, then I'll create the plan.

Now creating the plan on the decided intent.

Writing the plan contract and slices now.

I've written the plan. Nothing is approved yet: the file is still a draft and waits on your yes.

The plan is at `.cg-docs/plans/2026-11-26-poverty-gap-index.md`. It is built on the decided intent `.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md`. `cg.py validate` printed `problems: 0`, `warnings: 0` (measured). Here is the plan as the file reads:

---

## Contract

### Goal

The package exports `poverty_gap(dt, line = 3)`, in `R/poverty_gap.R`, beside `headcount()`. It returns the poverty gap index: the weighted mean, over all households, of max(0, (line − welfare) / line), with the `weight` column as the weight. On the hand-built example of the intent (welfare 1, 2, 4; weight 1, 1, 2; line 2) it returns 0.125, within 1e-12. A household with welfare 0 counts as a gap of 1. Negative welfare, and a `line` that is not one finite positive number, stop with an error. The function has a help page with an example that runs for a user of the installed package. `headcount()`, `read_survey()`, `n_households()` and `inst/extdata/survey.csv` are byte for byte as they are today, and every existing test still passes.

### Out of scope

- From the intent: the squared poverty gap (P2), a general `fgt()` function, the Watts index and the income gap ratio. Any change to `headcount()`, `read_survey()`, `n_households()` or `inst/extdata/survey.csv`, including making `headcount()` refuse negative welfare. A result in percent, estimates by group or region, standard errors, and more than one line at a time. A reference value for the shipped toy survey: you gave none (D3).
- Deferred: adding `headcount()`, `n_households()` and `poverty_gap()` to the Outputs map of `.cg-docs/verification.md`.
- Deferred: `Roxygen: list(markdown = TRUE)` in `DESCRIPTION`.
- Deferred: a lockfile (`renv.lock`). The project has none today.
- Deferred: a full `R CMD check`. C7 runs only the new example.

### Requirements

| ID | Requirement |
|---|---|
| R1 | `poverty_gap(dt, line)` returns the weighted mean over all households of max(0, (line − welfare) / line): 0.125 on the hand-built example at line 2. |
| R2 | A household with welfare 0 is accepted and counts as a gap of 1. |
| R3 | Negative welfare stops with the error "welfare must not be negative". |
| R4 | It keeps the input assertions of `headcount()`, with the same messages: required columns `welfare` and `weight`, welfare present, weight present and positive, `line` one finite number. |
| R5 | A `line` that is zero or negative stops with the error "line must be positive". |
| R6 | On the toy survey at the default line, the result lies between 0 and `headcount()` on the same data. |
| R7 | `poverty_gap()` is exported from the installed package. |
| R8 | It has a help page whose example runs without error for a user of the installed package. |
| R9 | Every existing test still passes against the installed package. |
| R10 | `R/headcount.R`, `R/read_survey.R`, `R/n_households.R` and `inst/extdata/survey.csv` stay byte for byte as they are. |

### Checks

C1 to C6 each run one `test_that()` block of `tests/testthat/test-poverty_gap.R`, chosen by its exact description. Each of them fails today, because the file and the function don't exist yet.

| ID | Req. | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `Rscript -e '…test_file(…, desc = "poverty_gap() gives 0.125 on the hand-built example", stop_on_failure = TRUE)'` | The result differs from 0.125 by 1e-12 or more. Each wrong reading gives another number: poor only 0.5, not divided by the line 0.25, unweighted about 0.1667, negative gap kept −0.375. |
| C2 | R2 | same form, desc "poverty_gap() counts zero welfare as a gap of 1" | Welfare 0 and 4, weight 1 and 1, line 2 does not give 0.5, or the call errors. |
| C3 | R3 | same form, desc "poverty_gap() refuses negative welfare" | Welfare −1 returns a number instead of the error. |
| C4 | R4 | same form, desc "poverty_gap() refuses bad input" | A missing column, missing welfare, a missing or zero weight, `line = NA` or `line = c(1, 2)` returns a number, or stops with another message. |
| C5 | R5 | same form, desc "poverty_gap() refuses a line that is not positive" | `line = 0` or `-1` returns a number, `Inf` or `NaN`. |
| C6 | R6 | same form, desc "poverty_gap() on the toy survey is between 0 and the headcount" | The result is below 0, above `headcount()`, or not one finite number. |
| C7 | R7, R8 | installs into a temporary library, checks the export and the help topic, then runs `example("poverty_gap", …)` | The install fails, the function is not exported, it has no help topic, or the example errors. |
| C8 | R9 | the full test suite against the package installed in a temporary library, the same command the headcount work used | Any test fails. This is a regression check: it passes today. |
| C9 | R10 | `stopifnot(identical(md5sum(<the 4 files>), <digests taken today>))` | A digest differs. This is a pin: it passes today. |

The plan file holds each command written out in full.

**What no check would catch:**
- The only independent reference is the hand-built example. The toy survey's index is only bounded, between 0 and the headcount. A formula that is right on three households and wrong on others would pass.
- An error raised by base R before a guard is reached is caught only when its message differs from the planned one.
- C7 proves the help page exists and its example runs, not that its words are right.

### Boundaries

- **Always:**
  - Run each slice's checks through `cg.py evidence`, and see C1 to C6 fail before the code exists.
  - Run C8 and C9 after every slice.
  - Build only in a temporary library.
  - Type the expected values into the tests as plain numbers from the intent.
  - Use base R and `stop()`, with no new dependency.
- **Ask first:**
  - A new dependency or a change to `DESCRIPTION`.
  - Any file outside the slice's list, including another help page that `roxygenise()` would rewrite.
  - Any change to a check, its value or its tolerance.
  - An error message other than the ones named here.
- **Never:**
  - Touch the four pinned files or their tests.
  - Change a check so that it passes.
  - Install into your R library.
  - Print survey rows anywhere.
  - Commit, push or publish unless you ask.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| inst/extdata/survey.csv | Public | Shipped with the package ("synthetic … made up") | MD5 6b2d9769…, as of 2026-11-26 | package author (Gate Kit) | read through `read_survey()` by C6, C7 and C8; not changed |

**Shape of the data:**
- There is one row per household, keyed by a unique `hhid`.
- `welfare` is present and positive.
- `weight` is the number of households a sampled household stands for.
- The index is computed at household level, weighted by `weight`, over every household the survey represents. A household at or above the line counts as zero.
- No dataset is closed. The work produces none.

## Slices

| Slice | What it delivers | Files | Checks | How |
|---|---|---|---|---|
| S1 | The thinnest whole path: the exported `poverty_gap()` gives 0.125, 0.5 for zero welfare, and a bounded value on the toy survey. The body holds only the formula; the guards come in S2. | `R/poverty_gap.R`, `tests/testthat/test-poverty_gap.R`, `NAMESPACE` | C1, C2, C6, C8, C9 | by code |
| S2 | The input guards | `R/poverty_gap.R`, the test file | C3, C4, C5, C8, C9 | by code |
| S3 | The help page, generated by `roxygen2::roxygenise()` | `R/poverty_gap.R`, `man/poverty_gap.Rd` | C7, C8, C9 | by code; the wording by judgement |

`NAMESPACE` is written by hand, so S1 adds `export(poverty_gap)` to it directly.

## Open questions

There are none.

---

**Risk tier (measured):** `tier: elevated`. Its `reasons` line reads "number: it computes a number someone will read, or can change one". The survey file is Public, so this agent may read it.

**Self-review.** I reviewed my own plan; no independent reviewer has checked it.

| Principle | Verdict | Finding |
|---|---|---|
| P1 Specify | PASS | Every requirement has a check, and every check can fail on something you can observe. C1 tells all four wrong readings from the intent apart. |
| P3 Deterministic | FLAG | Every slice is done by code, and the expected values come from arithmetic, not from the code. But the environment is not pinned: the project has no lockfile. That was already true, and it is deferred, not fixed here. |
| P6 Smallest change | PASS | Four files, no new dependency, three slices of at most three files each. |
| P10 Correct in the domain | PASS | The unit, weights and population are stated. The denominator covers all households, negative welfare is refused, and C6 checks the bounds. |
| P12 Governed data | PASS | There is one dataset, classified Public and cleared for this agent. No rows go out. |

**Defaults I chose, for you to see:** the two new error messages ("welfare must not be negative", "line must be positive") and the exact test descriptions.

**Not looked up (inferred):** the plan playbook doesn't let me run project code, so I haven't run C1 to C9. I'm relying on three behaviours I haven't tested:
- `test_file()` stops with an error when no block matches `desc`.
- `help()` returns one entry when the topic exists.
- `example()` passes an error in the example through to the exit code.

If one of these is wrong, that check needs an amendment.

Do you approve this plan? A plain yes approves it and is recorded under your name. I'll take anything else as a change or a question.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve the plan, or tell me what to change.
* **Project:** this is the plan for the poverty gap index, written on the decided intent. Once it's approved, `/cg work` builds it slice by slice, starting with S1.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I added the line to the Never list. The plan is not approved yet: a "yes, but" is a change, so I haven't recorded your reply. The Never list in `.cg-docs/plans/2026-11-26-poverty-gap-index.md` now reads:

> - Never: change `R/headcount.R`, `R/read_survey.R`, `R/n_households.R`, their tests or `inst/extdata/survey.csv`; **change any file under `data-raw/`**; change a check so that it passes; install into the human's R library; print rows of the survey into the work report, the evidence or a commit; commit, push or publish without the human asking.

That is the only change to the plan. `cg.py validate` still prints `problems: 0`, `warnings: 0` (measured).

The project has no `data-raw/` folder today (measured). None of the three slices touches it, and no check reads it. The line keeps the work from creating or changing anything there, and `cg.py guard` already fails a change to a file that a slice didn't declare.

Do you approve the plan as it now reads? A plain yes approves it and is recorded under your name. I'll take anything else as a change or a question.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve the plan, or tell me what else to change.

[exit code: 0]

### H3 yes

> Yes.

The plan is approved, with the `data-raw/` line in its Never list. `cg.py approve` recorded your reply ("Yes.") under your name in `.cg-docs/approvals/2026-11-26-poverty-gap-index.ce68c78e025ed4f1.1.json`. The plan `.cg-docs/plans/2026-11-26-poverty-gap-index.md` now has status `approved` and points to that record (measured).

- **Goal:** the package exports `poverty_gap(dt, line = 3)`, the weighted poverty gap index over all households. It returns 0.125 on the hand-built example, refuses negative welfare and a line that is not positive, and has a help page whose example runs. The four pinned files stay byte for byte as they are.
- **Requirements and checks:**
  - R1 is checked by C1.
  - R2 to R6 are checked by C2 to C6.
  - R7 and R8 are both checked by C7.
  - R9 is checked by C8, the full test suite.
  - R10 is checked by C9, the file digests.
- **Slices, in order:**
  - **S1:** the formula and the export (C1, C2, C6, C8, C9).
  - **S2:** the input guards (C3, C4, C5, C8, C9).
  - **S3:** the help page (C7, C8, C9).
- **Data:** only `inst/extdata/survey.csv`, which is Public and cleared for this agent. No dataset stays closed.
- **Open questions:** none.
- **Deferred:**
  - the Outputs map in `.cg-docs/verification.md`
  - markdown in the help pages
  - a lockfile
  - a full `R CMD check`
- **What no check would catch:** the toy survey's value is only bounded, between 0 and the headcount, and not compared with an outside figure. The wording of the help page isn't checked either.
- **Self-review:** I reviewed my own plan. It passed P1, P6, P10 and P12. P3 is flagged because the project has no lockfile; that was already true, and the plan defers it.
- **Not checked yet (inferred):** the plan playbook doesn't run project code, so none of C1 to C9 has run. If one of them doesn't work as written, the fix is an amendment to the plan.

Nothing is committed. To commit, ask me to add the plan, its intent and their approval records under `.cg-docs/approvals/` in one commit.

**Next steps: Done**
* **Your move:** type `/cg work` to start slice S1.
* **Project:** the poverty gap index plan is approved. The work comes next, slice by slice, from S1.

[exit code: 0]

### W1 ask for the work

> /cg work Do the work of the approved plan.

Reading the approved plan and package files before creating the work report.

Creating the work report, then loading the R pack's lead skill.

`stop: none`, so S1 goes ahead under the plan's approval. Next, the S1 checks run before any code exists, to see C1, C2 and C6 fail.

C1, C2 and C6 fail because the file doesn't exist yet. C8 (15 tests pass) and C9 (pin) pass, as a regression check and a pin should. Writing the S1 code and tests now.

Code and tests written. Running the S1 checks, then guard.

All five S1 checks verified and `guard: clean`. Checking that each check's output shows its tests running, so a desc that matched nothing can't pass as empty.

The records keep only digests. An ad-hoc run of the whole new test file shows the expectation counts.

`stop: none`. Writing the C3–C5 test blocks first, so they can be seen to fail before the guards exist.

All three fail before the guards (1, 6 and 2 failures). Adding the guards to `R/poverty_gap.R`, with `headcount()`'s order and messages plus the two new ones.

Running C7 before the page exists (it should fail), and trying `roxygenise()` on a scratch copy to list what it would change.

All three slices are done and `guard: clean`. Listing the evidence, then reading the Verifier sections of P3, P4 and P6 for the self-review.

The evidence shows every check in every slice `verified`. Before filling in the rest of the report, I'm getting the digests of the new files.

Filling in the remaining sections of the work report and setting it to `completed`, then validating it.

I finished all three slices of the approved poverty gap index plan, and every check of the plan passes. Nothing is committed.

- **Plan:** `.cg-docs/plans/2026-11-26-poverty-gap-index.md`, now `in-progress`. It stays there until someone reviews the work and signs it off.
- **Work report:** `.cg-docs/work-reports/2026-11-26-poverty-gap-index.md`, now `completed`. Validation found 0 problems and the final file check printed `guard: clean`.

| Slice | What it adds | Checks | Before → after (measured) |
|---|---|---|---|
| S1 | `poverty_gap()` with the formula, exported | C1, C2, C6, C8, C9 | C1, C2 and C6 failed before the code existed, then passed. C8 and C9 passed both times. |
| S2 | Input checks with the plan's error messages | C3, C4, C5, C8, C9 | C3, C4 and C5 failed before the checks existed, then passed. C8 now runs 30 tests. |
| S3 | Help page `man/poverty_gap.Rd`, generated by roxygen2 | C7, C8, C9 | C7 failed before the page existed, then passed. |

- **No stops:** nothing needed your approval mid-way, and no file outside the plan's list changed. A trial roxygen2 run on a scratch copy showed it writes only `man/poverty_gap.Rd`.
- **Results (measured):** the hand-built example gives 0.125, as the brainstorm worked out by hand. A copy with the "count households above the line as zero" step removed failed C1, so that check catches the error. On the toy survey at line 3 the index is 0.0810, below the headcount of 0.153846. That is only a bound: there is no outside figure for this survey.
- **Self-review (I wrote the work, so this is not an independent review):**
  - P3 (deterministic by default) is flagged: the R environment is not pinned. The plan put that out of scope.
  - P4 (prove it works) and P6 (smallest change) pass.

**Not checked:**
- The independent reviewers were not run in a fresh context.
- `R CMD check` was not run; the plan put it out of scope.
- I did not judge whether the help page wording is right.
- No test passes a plain data frame instead of a data.table.

**Noticed but not touching:**
- Earlier work is still uncommitted: the `headcount()` and `n_households()` code, tests and help pages, and their `NAMESPACE` lines. A commit now would mix that work with this one.
- I used base R `stop()` as the plan says, not `rlang`/`cli` as the R style guide prefers.
- `headcount()` still accepts negative welfare.
- Help pages show literal backticks.
- `.cg-docs/verification.md` doesn't list the new functions yet.

**Next steps: Done**
* **Your move:** read `man/poverty_gap.Rd`, then tell me how to commit. For example, type: `commit the poverty gap work, and the earlier headcount and n_households work in a separate commit first`.
* **Project:** the poverty gap index is built and proven; it still needs a review and a commit (no review playbook is installed yet).

[exit code: 0]
