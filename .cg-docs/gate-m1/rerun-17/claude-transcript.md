### B1 setup

> /cg

Reading the R pack's settings and running a dry run of the setup command. Nothing gets written.

Setup comes first because this project has no `.cg-docs/config.json` yet. So far I have only read files. Nothing is written until you confirm.

## What I found

- **Files (measured):** 3 `.R` files, 1 `.Rd`, 1 `.csv`, plus `DESCRIPTION`, `NAMESPACE` and `LICENSE`. This is an R package, `toypov` 0.0.1, with one exported function, `read_survey()`.
- **How outputs are made (measured):** there is no `Makefile`, `_targets.R` or main script. The only checks are the testthat tests in `tests/testthat/test-read_survey.R`. I read them and did not run them.
- **Data:** 1 file, `inst/extdata/survey.csv`. I did not open it. Until you classify it, it counts as restricted data.
- **Already here:** nothing. There is no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md` or version 1 file.

## Proposal

**1. Packs:** `core` and `lang-r`. Both are installed on this machine (measured, from `cg.py packs`).

**2. Pack setting:** `lang-r.r-syntax = data.table-collapse`. The code supports it: `DESCRIPTION` has `Imports: data.table`, `NAMESPACE` has `importFrom(data.table, fread)`, and `R/read_survey.R:8` calls `fread(path)`. This is also the pack's default.

**3. Verification profile (draft):**
- **Run:** not found. The project defines no command. An R package is usually checked with `R CMD build . && R CMD check --no-manual toypov_0.0.1.tar.gz`, which installs into a temporary library. That is my inference, not something the project states. Do you want it as the Run command?
- **Doctor:** not found.
- **Outputs:** `read_survey()`, the exported function. The proof is in the tests: it reads 20 rows with columns `hhid`, `welfare`, `weight`, and it stops on a non-positive weight. No check covers missing columns, non-positive welfare or duplicate `hhid`, even though the code (`R/read_survey.R:11-22`) handles all three.

**4. Data rules.** Only you can answer these. `DESCRIPTION` calls the data synthetic, but that is a description, not a classification. Please give:
- the classification of `inst/extdata/survey.csv` (or of the `inst/extdata` folder);
- the highest classification your organization lets Claude Code read;
- if you know them, your organization's classification levels, from public to most restricted.

You can copy and edit this example answer:
`inst/extdata = Public; Claude Code may read up to Official Use Only; levels: Public; Official Use Only; Confidential; Strictly Confidential`

**5. Files that will be written** (from `cg.py setup --dry-run`, measured):
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`, because this is an R package

**Assumptions:**
1. The coding agent is recorded as `Claude Code`. If you want another name, `cg.py tier` will look for that name instead.
2. Nothing will be committed.

Reply with the answers to item 4 and say whether you want the R CMD check line as the Run command. A plain yes to the rest confirms it. Anything else I'll treat as a change or a question.

**Next steps: Waiting on you**
* **Your move:** Reply with the data classifications (item 4) and yes or no on the Run command, for example: `inst/extdata = Public; Claude Code up to Public; Run command: yes; rest: yes`
* **Project:** Compound GPID setup for the `toypov` toy package. The proposal is ready, and nothing is written until you confirm.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Thanks. I'm recording what you confirmed. The survey file is `Public`, and Claude Code may read `Public`. You gave no classification levels, so I'm leaving that option out.

Now I'm filling in the verification profile with the confirmed draft. Run and Doctor stay "not found" for now (see the open question below).

Setup is done. Status now reads `phase: ready` with `stops: none`.

**What I found:** this is an R package with 3 `.R` files, 1 `.Rd` and 1 data file. The project defines no Run command, and its only checks are the testthat tests.

**What you confirmed:**
- packs `core` and `lang-r`
- the setting `r-syntax = data.table-collapse`
- `inst/extdata/survey.csv` is `Public`, and Claude Code may read `Public`

**Files written** (nothing committed):
- `.cg-docs/config.json`
- `.cg-docs/verification.md`: a draft profile that lists `read_survey()` and the tests that check it
- `AGENTS.md`: the Compound GPID pointer block
- `CLAUDE.md`: holds `@AGENTS.md`
- `.Rbuildignore`: keeps the three new files out of the package build

**Status lines (measured):**
```
phase: ready
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
packs-missing: none
stops: none
```

**Still open:**
1. **Run command.** I asked whether you want `R CMD build . && R CMD check --no-manual toypov_0.0.1.tar.gz` as the Run command, and your yes didn't clearly answer that. So the profile says "not found" and lists that line as proposed. Do you want it as the Run command? My recommendation is yes: it is the standard full check for an R package, and it installs only into a temporary library. The cost is that it is slower than running the tests alone.
2. **Doctor command:** none found.
3. **Classification levels:** you didn't give your organization's levels, so they aren't recorded. That's fine while all the data is `Public`.
4. **Missing checks:** no test covers missing columns, bad welfare values or duplicate `hhid`.

The profile stays `draft` until the Run command has been run end to end.

**Next steps: Waiting on you**
* **Your move:** Answer the Run-command question with `yes` or with the command you prefer. Or type `/cg` followed by the change you want to make.
* **Project:** Compound GPID setup for `toypov` is done and ready for work. The verification profile is still a draft until the Run command is confirmed and run.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

Now let me look at the project.

I'm stopping here for your yes before I change anything, because the risk check came back **elevated**.

**Why it stopped:** the new function computes a number people will read. This is the only reason. The survey file is cleared for me to read (it's recorded as Public), the change touches 5 files, and it adds no new dependency.

**What I'll do if you say yes**
- **Goal:** add an exported `headcount(dt, line = 3)` that returns `sum(weight[welfare < line]) / sum(weight)`.
  - "Below" means strictly below, so a household exactly at the line is not counted as poor.
  - It stops with an error if `welfare` or `weight` is missing or `NA`, if a weight is not positive, or if `line` is not one finite number.
- **Files:**
  - new: `R/headcount.R` (with roxygen), `tests/testthat/test-headcount.R`, `man/headcount.Rd`
  - updated: `NAMESPACE` (the export) and the outputs table in `.cg-docs/verification.md`
- **Out of scope:**
  - any change to `read_survey()` or the survey data
  - other poverty measures (gap, severity)
  - a new dependency such as collapse
  - a commit

**Checks, and what would count as a failure**
1. **Toy survey value:** `round(headcount(read_survey()), 6)` must equal **0.153846**, the value you gave. I set the tolerance now, before the first run: your figure has 6 decimals, so I'll compare at 6 decimals. Any other value fails. I'll run this test against the current code first, where it should fail because the function doesn't exist yet.
2. **Small hand-made table:** welfare `c(1, 5)` with weights `c(1, 3)` must give exactly 0.25. A household with welfare exactly at the line must not be counted.
3. **Errors on bad input:** a missing `weight` column, an `NA` weight and a vector `line` must each raise an error.
4. **Full package check:** `R CMD build` then `R CMD check --no-manual`, with the package installed only into a temporary library. It must finish with no errors or warnings, and the existing `read_survey()` tests must still pass.

If I don't get 0.153846, I'll fix the code, not the expected value, unless a source that doesn't depend on my code shows the figure is wrong. Once the checks are done I'll write a work report under `.cg-docs/work-reports/`.

Do you approve this, including "strictly below"?

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve the contract. If a household exactly at the line should count as poor, reply `yes, but use <=` instead.
* **Project:** this adds `headcount()` to the toy package toypov. Only `read_survey()` exists so far, and nothing has been changed yet.

[exit code: 0]

### C2 yes

> Yes, proceed.

Next I'll check the R toolchain. Then I'll write the test first, so I can watch it fail on the current code.

The NAMESPACE file is written by hand, not by roxygen2, so I'll add the export line myself and leave the rest of the file as it is.

Step 4, the proof. First the test suite, then the full package build and check, installed only into a temporary library:

Every check passes and `R CMD check` reports Status OK. Next, the self-review against the Verifier sections of P3, P4 and P6:

Both wrong versions are caught. Next I'll add the new function to the outputs map in the verification profile, then write the work report.

I added `headcount(dt, line = 3)`, and on the toy survey it gives 0.1538461538, which rounds to your 0.153846. Every check in the contract passed, and the full package check (`R CMD check`) finished with Status: OK. Nothing is committed.

**Files changed:**
- `R/headcount.R` (new): returns `sum(weight[welfare < line]) / sum(weight)`. It stops with an error on a missing column, missing or non-positive weights, missing welfare, an empty table, or a `line` that isn't one finite number.
- `tests/testthat/test-headcount.R` (new): 3 tests.
- `NAMESPACE`: added `export(headcount)`. This file is written by hand, so roxygen2 skipped it and I added the line myself.
- `man/headcount.Rd` (new, generated by roxygen2).
- `.cg-docs/verification.md`: added a row for `headcount()`.

**Checks** (all measured):

| Check | Verdict |
|---|---|
| The new tests fail before the change ("could not find function") | verified |
| 1. Toy survey rounds to 0.153846 at 6 decimals | verified |
| 2. Hand-made table: weights work, and a household exactly at the line is not counted | verified |
| 3. Errors on a missing `weight` column, an `NA` weight, a vector `line` and an `NA` line | verified |
| 4. `R CMD build`, then `R CMD check --no-manual` with a temporary library | verified, Status: OK |

- **Second way of computing it:** collapse's weighted mean on the raw CSV gives the same 0.1538461538. I ran it as a one-off outside the package, so collapse is not added as a dependency.
- **Breaking the code on purpose:** in a scratch copy, I switched to `<=` and the hand-made test failed. I switched to an unweighted share and the toy-survey test failed. One limit: the toy-survey test can't tell `<` from `<=`, because no household has welfare exactly 3. The hand-made test is what protects "strictly below". No check was changed after it failed.

**Self-review** (my own, not an independent reviewer's):
- **P3, P4:** PASS.
- **P6:** a minor FLAG. The guards for an empty table and for non-numeric welfare or weight (`R/headcount.R:28-33`) have no test. I kept them on purpose, because an empty table would otherwise quietly return `NaN`.

**Not checked:**
- Those two untested guards.
- The verification profile has no Run or Doctor command yet, so neither was run.

**Noticed but not touching:**
- The R guidance asks for `rlang`/`cli` errors and `collapse::fmean()`. The project uses base `stop()` and has neither package in its dependencies, so I followed the project, as the contract said.
- `NAMESPACE` is maintained by hand, so future exports also need adding by hand.

The work report is `.cg-docs/work-reports/2026-11-26-add-headcount-function.md`, marked completed, and code validation found no problems. The package check ran in `/private/tmp/claude-502/-Users-<user>-temp-cg-gate-rerun-17-toy-r-claude/2cb8b4c2-ada9-4e08-babb-c52991bc8d21/scratchpad/rcheck`. It's throwaway, and you can delete it any time.

**Next steps: Done**
* **Your move:** to commit, reply `commit it`. The work report goes in the same commit as the change.
* **Project:** toypov now has `read_survey()` and `headcount()`, both tested. The verification profile is still a draft until its Run command is confirmed.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

The status is `ready` with no active work. The code uses base R with `stop()` and an explicit `return()`, so I'll match that.

The NAMESPACE file is maintained by hand, so roxygen didn't touch it. I'll add the export myself and rerun the tests.

I added `n_households(dt, weighted = FALSE)` to toypov. By default it counts the households in the sample, one per distinct `hhid`, and the toy survey has 20. Your request could also mean the number of households the survey represents, so `weighted = TRUE` returns the sum of `weight` instead. If you only wanted the plain count, I can take that argument out.

It stops with an error if `hhid` is missing, has gaps or has duplicates, and, when weighted, if a weight is missing or not positive. That matches the checks in `read_survey()` and `headcount()`.

All 22 package tests pass, including the new ones. I did not run `R CMD check`.

Changed files:
- `R/n_households.R`: the function and its roxygen docs.
- `tests/testthat/test-n_households.R`: the toy survey, hand-built cases, and bad inputs.
- `man/n_households.Rd`: generated by roxygen.
- `NAMESPACE`: I added `export(n_households)` by hand, because roxygen skips this file since it didn't write it.

Nothing is committed, and this change has no Compound GPID record in `.cg-docs/`.

**Next steps: Done**
* **Your move:** Nothing. If you want a record of this change, type `/cg`.
* **Project:** toypov now has `read_survey()`, `headcount()` and `n_households()`. The new function is not in `.cg-docs/` and not committed.

[exit code: 0]

### G1 idea

> /cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

Looking up the project's facts before my first question: the existing functions, the docs and the `.cg-docs/` record.

Facts are gathered. I'm writing them into the intent file, then putting the first questions to you.

I'm running this as a brainstorm. Nothing gets built in it. I've started the record at `.cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md` (status `draft`).

**What I think you want:** a number that says how deep poverty is in the survey, to go next to `headcount()`. What's still missing is what that number is for, because the right measure depends on it.

## What I looked up

- **The project** (measured, from the files): the survey has one row per household with `hhid`, `welfare` and `weight`. `read_survey()` stops unless every welfare value is above zero. There is no household size, so any measure is per household, not per person. The unit of welfare isn't written down anywhere. `headcount()` counts a household as poor only when welfare is strictly below the line.
- **The field's names for this** (measured, from the World Bank's poverty methodology handbook, section 4.1, [surveyestimates.html](https://datanalytics.worldbank.org/PIP-Methodology/surveyestimates.html)):
  - **Poverty gap index, FGT(1).** Each poor household's distance below the line, as a share of the line, averaged over *all* households. Households that aren't poor count as zero.
  - **Squared poverty gap (poverty severity), FGT(2).** The same, but each gap is squared first, so the poorest count more. The handbook says it "accounts for inequality among the poor."
  - **Watts index.** The average of ln(line / welfare) over the poor, divided by all households. It also weighs the poorest more, and it needs welfare above zero, which your data guarantees.
- **One more statistic** (from my local analysis guide, not the handbook): averaging the gap over the poor only gives the **income gap ratio**. That's the literal "how far below the line is a poor household on average." It's also a common mistake when someone means FGT(1).

## The choice that matters most

The literal reading of your request is the income gap ratio. It has a catch (inferred, by arithmetic). Take two households with equal weight, welfare 1 and 2.9, and a line of 3. Their gaps are 0.67 and 0.03, so the average gap among the poor is 0.35. Now the 2.9 household rises to 3.1 and leaves poverty. Only the household at 1 is still poor, so the average gap jumps to 0.67. Nobody got poorer, yet depth "doubled." The poverty gap index goes from 0.35 to 0.33, which is the direction you'd expect.

So the question is whether you want a description of the poor or a poverty measure you can compare. Here is the first round. Each has my recommendation, and a yes takes it:

1. **D1. What the number is for.** I recommend a measure for comparing surveys, lines or years: the poverty gap index, FGT(1). The trade-off: it mixes how many are poor with how deep they are, so it reads less directly as "how far below." (The income gap ratio is FGT(1) divided by the headcount, so it could be added later if you want the descriptive reading.) Comparing is what you want?
2. **D2. Unit.** I recommend a share of the line, from 0 to 1, as the handbook defines it. The trade-off: to get "how much below the line in welfare units," you multiply by the line. Share of the line?
3. **D3. Scope.** I recommend one survey and one line, the same as `headcount()`. No groups, no list of lines, no standard errors. Is that the scope?

Once these are answered, I'll set out the approaches, such as one new function or a general FGT function with `headcount()` as the case alpha = 0. Then I'll write what a wrong result would look like.

**Not looked up:** the welfare unit and whether the weights are household or person weights (no file says). I also didn't open the World Bank's `wbpip` code or the original FGT paper.

**Next steps: Waiting on you**
* **Your move:** answer D1–D3. For example, type `1 yes, 2 yes, 3 yes`, or give your own answer to any of them.
* **Project:** the brainstorm on a depth-of-poverty measure is open as a draft intent. After your answers come the approaches, then your yes to the intent, then `/cg plan`.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I recorded all three answers in your words: the **poverty gap index, FGT(1)**, as a **share of the line**, for **one survey and one line**. Your note on the reference value is in the record too: a small hand-built example whose value comes from arithmetic. Record: `.cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md`.

## Ways to build it

I considered five:

- **A. A new `poverty_gap(dt, line = 3)` built like `headcount()`.** Same arguments and input checks, base R only. Each poor household's gap is `(line - welfare) / line`, every other household gets 0, and the result is the weighted mean over all households.
- **B. A general `fgt(dt, line, alpha)`**, with the headcount at alpha = 0 and the gap at alpha = 1.
- **C. A, plus one shared input-check helper** that both functions call.
- **D. A, using `collapse::fmean()`** for the weighted mean.
- **E. Build nothing and document how to compute it by hand.**

Only A and B really differ, so I'm narrowing to those two:

| | Cost | Risk |
|---|---|---|
| **A** | One R file, one test file, one help file, one `NAMESPACE` line. No new dependency. | The input checks are copied, so a later fix to one function could miss the other. |
| **B** | A new interface, plus either rewriting the tested `headcount()` on top of it or keeping two ways to get the headcount. | In R `0^0` is 1, so at alpha = 0 every non-poor household would count as poor unless the code zeroes them separately (inferred, standard R arithmetic). It also builds more than the one-line scope you chose. |

The others drop out for these reasons:
- **C** changes a working, tested function without changing any number.
- **D** adds a dependency for something base R does in one line.
- **E** doesn't meet the goal, and leaves users to make the mistake of averaging over the poor only.

## Reference example

This is the smallest table that fits (all inferred, by arithmetic). It has two households: welfare `c(1, 5)`, weight `c(1, 3)`, line 3.
- The poor household's gap is 2/3, so the **poverty gap is (1 × 2/3) / 4 = 1/6**.
- Each common mistake gives a different number:
  - unweighted mean: 1/3
  - averaged over the poor only: 2/3
  - gap not divided by the line: 1/2
  - non-poor not set to zero: −1/3
- One side effect (inferred): a household exactly on the line has a gap of 0 either way, so the "strictly below" rule from `headcount()` can't change this number.

**D4. Which approach?** I recommend **A**, a new `poverty_gap(dt, line = 3)` next to `headcount()`. The trade-off is the copied input checks. Take A?

**Not looked up:** the weights are still unlabelled as household or person weights. I didn't check how the World Bank's `wbpip` code computes the gap.

**Next steps: Waiting on you**
* **Your move:** answer D4. Type `yes` to take A, or name another approach.
* **Project:** the depth-of-poverty brainstorm is a draft with D1–D3 decided. After D4, I'll write the full intent for your yes, then `/cg plan`.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I took "Yes to each question" as your answer to the one open question, D4. That means approach A: a new `poverty_gap(dt, line = 3)` next to `headcount()`. If you meant something else, say so and I'll change it.

I also started the project's glossary, `GLOSSARY.md`, with four terms you've now taken up: poor household, headcount ratio, poverty gap index and income gap ratio. I filled in the intent and ran the check on it: `problems: 0`, `warnings: 0`.

Here is the intent as the file reads (`.cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md`):

**Goal.** The package says how far below the line the poor households are, not only how many there are. A new exported function `poverty_gap(dt, line = 3)` returns the poverty gap index, FGT(1), for one survey and one line. Each poor household's distance below the line is taken as a share of the line, every other household counts as zero, and these are averaged with the weights over all households. The result is a number from 0 to 1. Whoever uses the package reads it next to `headcount()`, and it can be compared across surveys and lines because it never goes up when a household leaves poverty.

**Out of scope.**
- No income gap ratio (the average over the poor only), squared poverty gap, Watts index or general `fgt(alpha)` function.
- No results by group, no several lines at once, no standard errors.
- No result in welfare units: the result is a share of the line.
- No change to `headcount()`, `n_households()`, `read_survey()`, the survey data or the dependencies (base R only, no collapse).
- No per-person measure, because the survey has no household size.

**A wrong result.** Take the table with welfare `c(1, 5)`, weight `c(1, 3)` and line 3. The correct result is exactly **1/6**. Each common mistake gives a different number:
- weights ignored: 1/3
- averaged over the poor only: 2/3
- gap not divided by the line: 1/2
- the non-poor household's gap not set to zero: −1/3

A result below 0, or above the headcount ratio for the same table and line, is also wrong.

**Decisions.**

| ID | Decision | Your answer |
|---|---|---|
| D1 | What the number is for | A poverty measure that compares: the poverty gap index, FGT(1), over all households ("Yes to each question: I take the answer you recommend.") |
| D2 | Unit | Share of the line, 0 to 1 (same reply) |
| D3 | Scope | One survey and one line, like `headcount()` (same reply) |
| D4 | Approach | A: a new `poverty_gap(dt, line = 3)` next to `headcount()` (same reply) |

The approaches I set aside were B (a general `fgt(alpha)`), C (a shared input-check helper), D (collapse) and E (do nothing). The intent says why for each.

```
Assumptions I am making:
1. poverty_gap() stops when the line is zero or negative, since the gap is divided by the line. headcount() accepts any finite line. If it is wrong: a zero line would give NaN, and a negative line a meaningless value.
2. The only reference value is the hand-built table above. The test on the shipped survey is compared with no figure, because you have none. If it is wrong: your figure would become a second check.
3. The help page calls the result the poverty gap index, FGT(1), and says it is a share of the line averaged over all households. If it is wrong: only the wording of the help page changes.
Correct me now.
```

All the numbers above follow from arithmetic (inferred). None of them came from running anything. I still haven't looked up whether the weights are household or person weights, or how the World Bank's `wbpip` code computes the gap.

**Is this what you want?** A plain yes confirms the intent and is recorded under your name. I'll take anything else as a change or a question.

**Next steps: Waiting on you**
* **Your move:** type `yes` to confirm the intent as shown, or say what to change.
* **Project:** the depth-of-poverty intent is complete and checked but still a draft. After your yes, `/cg plan` builds `poverty_gap()`.

[exit code: 0]

### G4 vague reply

> Sounds good.

I ran the recording step with your reply word for word:

`cg.py approve ".cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md" --reply 'Sounds good.'`

It was **refused**, so nothing is recorded. "Sounds good" says you're happy with the intent, but it doesn't confirm it. The intent is still a `draft`.

Is anything in it you'd change or that isn't clear? These are the parts people most often want to adjust:
- **Assumption 1:** `poverty_gap()` stops on a line of zero or below, even though `headcount()` accepts any finite line.
- **Assumption 2:** the test on the shipped survey is compared with no reference figure. Only the hand-built table gives an exact value.
- **Out of scope:** the income gap ratio, the average gap over the poor only, is left out.

If it's right as it reads, a plain `yes` confirms it and is recorded under your name. I'll take anything else as a change or a question.

**Next steps: Waiting on you**
* **Your move:** type `yes` to confirm the intent as shown, or say what to change.

[exit code: 0]

### G5 answer

> Yes.

Your "Yes." is recorded and the brainstorm is finished. The intent at `.cg-docs/brainstorms/2026-11-26-depth-of-poverty-measure.md` now has status `decided`, and the approval is saved in `.cg-docs/approvals/2026-11-26-depth-of-poverty-measure.0402b034a06b91e9.json`. Nothing has been built yet.

**Goal:** a new `poverty_gap(dt, line = 3)` that returns the poverty gap index, FGT(1). That is the weighted average over all households of each poor household's distance below the line, as a share of the line, with every other household counting as zero.

**Your decisions:**
- **D1, what it's for:** a measure for comparing surveys, lines or years.
- **D2, unit:** a share of the line, from 0 to 1.
- **D3, scope:** one survey and one line, like `headcount()`.
- **D4, how to build it:** approach A, a new function built like `headcount()`, in base R only.
- **Set aside:** a general `fgt(alpha)`, a shared input-check helper, using collapse, and doing nothing.

**Assumptions you confirmed:**
- `poverty_gap()` stops on a line of zero or below.
- The only reference value is the small two-household table, where the answer is exactly 1/6.
- The help page calls the result the poverty gap index, FGT(1).

**Also new:** `GLOSSARY.md` in the project root. It defines poor household, headcount ratio, poverty gap index and income gap ratio.

**Not checked:**
- All the values in the intent come from arithmetic. I ran no code.
- I didn't look up whether the weights are household or person weights.
- I didn't look at how the World Bank's own code computes the gap.

Nothing is committed yet: the intent, the approval record and `GLOSSARY.md` are new, untracked files.

**Next steps: Done**
* **Your move:** type `/cg plan` to plan building `poverty_gap()` from this intent.
* **Project:** the depth-of-poverty brainstorm is decided. Next comes the plan, then the build of `poverty_gap()` with its test against 1/6.

[exit code: 0]

### H1 ask for the plan

> /cg plan Write the plan for the work we settled in the brainstorm.

Reading the decided intent and project files before writing the plan.

Writing the plan file now, from the decided intent and the code.

I've written the plan for `poverty_gap()` from the decided intent. `cg.py validate` printed `problems: 0` and `warnings: 0`. It is waiting for your approval at `.cg-docs/plans/2026-11-26-poverty-gap-index.md`. No code has changed yet. Here is the plan as the file reads:

---

# Poverty gap index

The human approves this plan as it reads below. `cg.py approve` records their reply against this text, so a later change is an amendment, a dated line under `## Amendments`, and needs a new approval.

## Contract

### Goal

The package exports `poverty_gap(dt, line = 3)`. For one survey and one line it returns the poverty gap index, FGT(1): `sum(weight * gap) / sum(weight)`, where `gap = (line - welfare) / line` for a poor household (welfare strictly below the line) and 0 for every other household. On the hand-built table welfare `c(1, 5)`, weight `c(1, 3)`, line 3, it returns 1/6. On the shipped survey at line 3 it returns a number above 0 and below `headcount()` for the same survey and line. It takes the same inputs as `headcount()` and stops on the same bad inputs, and also on a line that is zero or negative. Its help page calls the result the poverty gap index, FGT(1), a share of the line averaged over all households. No other function, the survey data and the dependencies stay as they are.

### Out of scope

- No income gap ratio (the average over the poor only), squared poverty gap, Watts index or general `fgt(alpha)` function. Deferred: a general `fgt(alpha)`, because the intent's scope (D3) asks for one measure, and in R `0^0` is 1, so `fgt(0)` needs care to give the headcount.
- No results by group, no several lines at once, no standard errors.
- No result in welfare units: the result is a share of the line.
- No change to `headcount()`, `n_households()`, `read_survey()`, the survey data or the dependencies (base R only, no collapse).
- No per-person measure: the survey has no household size.
- Deferred: one shared input-check helper for `headcount()` and `poverty_gap()` (approach C of the intent). It would change the tested `headcount.R` and no number.
- Deferred: documenting the unit of `welfare` and of the line. It is undocumented in the package today, and it is no part of this goal.

### Requirements

| ID | Requirement |
|---|---|
| R1 | `poverty_gap(dt, line)` returns the weighted mean over all households of `(line - welfare) / line` for households with `welfare < line`, and of 0 for every other household. |
| R2 | On the shipped survey at line 3, `poverty_gap()` returns a value above 0 and below `headcount()` for the same survey and line. |
| R3 | `poverty_gap()` stops, with the messages `headcount()` uses, on missing `welfare` or `weight` columns, a line that is not a single finite number, an empty table, missing or non-numeric welfare, and missing, non-numeric or non-positive weights. |
| R4 | `poverty_gap()` stops with the message "line must be positive" when the line is zero or negative. |
| R5 | `poverty_gap()` is exported from the package namespace. |
| R6 | The help page `man/poverty_gap.Rd` names the result the poverty gap index, FGT(1), and says it is a share of the line averaged over all households. |
| R7 | `headcount()`, `n_households()`, `read_survey()`, `DESCRIPTION` and `inst/extdata/survey.csv` stay byte for byte as they are, and their tests still pass. |

### Checks

Every requirement has a check, and every check can fail.

The test file is `tests/testthat/test-poverty_gap.R`. Build and check output goes to `~/temp/toypov-poverty-gap-check`, outside the project, with a temporary R library at `~/temp/toypov-poverty-gap-check/lib`.

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `Rscript -e 'devtools::test(filter = "poverty_gap", stop_on_failure = TRUE)'`, with the test `expect_equal(poverty_gap(data.table::data.table(hhid = 1:2, welfare = c(1, 5), weight = c(1, 3)), line = 3), 1 / 6)` (testthat's default tolerance, about 1.5e-8) | the exit code is not 0, because the result is not 1/6: for example 1/3 (weights ignored), 2/3 (averaged over the poor only), 1/2 (gap not divided by the line) or −1/3 (gap of the non-poor not set to zero) |
| C2 | R1 | Before `R/poverty_gap.R` exists, the C1 command; then, in a copy of the project at `~/temp/toypov-poverty-gap-check/mutants/<mistake>`, the C1 command once for each of the four mistakes of C1 written into the formula | the test file passes before the function exists, or passes on any of the four copies with a mistake |
| C3 | R2 | The C1 command, with the test `dt <- read_survey(); pg <- poverty_gap(dt, line = 3); expect_gt(pg, 0); expect_lt(pg, headcount(dt, line = 3))` | the exit code is not 0, because the value on the shipped survey is 0 or less, or equal to or above the headcount ratio 0.153846 |
| C4 | R3 | The C1 command, with one `expect_error()` per bad input, each with the message of `R/headcount.R:21-35`: no `weight` column ("missing columns: weight"), no `welfare` column ("missing columns: welfare"), line `c(1, 2)`, `NA_real_` and `Inf` ("line must be a single finite number"), a table with no rows ("dt has no households"), welfare with an `NA` and welfare as text ("welfare must be numeric and present"), weight with an `NA`, a zero weight and weight as text ("weight must be present and positive") | the exit code is not 0, because one of these inputs returns a value or stops with another message |
| C5 | R4 | The C1 command, with `expect_error(poverty_gap(dt, line = 0), "line must be positive")` and the same for line −1 | the exit code is not 0, because line 0 or −1 returns a value (`NaN`, `Inf` or a negative number) or stops with another message |
| C6 | R5 | `mkdir -p …/toypov-poverty-gap-check/lib && cd …/toypov-poverty-gap-check && R CMD build <project> && R_LIBS=…/lib _R_CHECK_FORCE_SUGGESTS_=true R CMD check --no-manual toypov_0.0.1.tar.gz; grep '^Status:' toypov.Rcheck/00check.log` (the file has the full paths) | the exit code of `R CMD check` is not 0, or the `Status:` line names an ERROR or a WARNING. The help page's example calls `poverty_gap()` on the attached package, so a function that is not exported stops the example with an ERROR, and an exported function with no help page gives the WARNING "Undocumented code objects" |
| C7 | R6 | `grep -q 'FGT(1)' man/poverty_gap.Rd && grep -q 'all households' man/poverty_gap.Rd && grep -q 'share of the line' man/poverty_gap.Rd` | the exit code is not 0: the help page is missing or does not name FGT(1), the share of the line or the average over all households |
| C8 | R7 | `diff` of five `git hash-object` digests (`R/headcount.R`, `R/n_households.R`, `R/read_survey.R`, `DESCRIPTION`, `inst/extdata/survey.csv`) against the values measured today, then `Rscript -e 'devtools::test(stop_on_failure = TRUE)'` (the file has the digests) | `diff` prints a line (one of the five files changed from the digest measured on 2026-11-26 before the work), or the exit code of the full test run is not 0 |

C8 is a pin: it passes today, and its job is to show that these files stay as they are.

What no check would catch:

- The unit of `welfare` and of the line is documented nowhere. A caller who passes a line in another unit than welfare gets a wrong value, and every check passes.
- The input checks are copied from `headcount()`. A later fix to one of the two functions that misses the other is not caught.
- `poverty_gap()` takes the input checks of `headcount()`, as decision D4 asks, and those do not stop on welfare that is zero or negative. `read_survey()` refuses such welfare, but a table built by hand that holds it gives that household a gap of 1 or more, and no check sees it.
- The value on the shipped survey is only bounded by C3, not compared with an independent figure: the human has none. A mistake that gives 1/6 on the two-row table and stays between 0 and the headcount on the survey would pass. I know of no such mistake among the common ones.

### Boundaries

- **Always:**
  - Run the checks a slice ends in, and report each exit code.
  - Write the help text as roxygen in `R/poverty_gap.R`, and generate `man/poverty_gap.Rd` with `roxygen2::roxygenise()`.
  - Add `export(poverty_gap)` to `NAMESPACE` by hand. That file is hand-written, so roxygen2 skips it.
  - Use base R `stop()`, as `headcount()` does.
  - Keep build, check and mutant copies in `~/temp/toypov-poverty-gap-check`.
  - Stop and report when a check fails.
- **Ask first:**
  - Changing any file outside the slice's list. That includes an Rd file other than `man/poverty_gap.Rd` that `roxygenise()` changes, and adding `GLOSSARY.md` to `.Rbuildignore`.
  - Adding a new dependency, or changing `DESCRIPTION` in any way.
  - Changing a check: its expected value, its tolerance or its error message.
  - Changing the default `line = 3`.
- **Never:**
  - Change `R/headcount.R`, `R/n_households.R`, `R/read_survey.R` or `inst/extdata/survey.csv`.
  - Add collapse, rlang or cli.
  - Install a package into your R library.
  - Change a check so that it passes.
  - Build anything that is out of scope.
  - Commit, push or publish without your asking.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| inst/extdata/survey.csv | Public | Synthetic household survey shipped with the package ("The data are made up", `DESCRIPTION`) | git commit 0df8098, blob 1db98caf… | The package maintainer, Gate Kit (`DESCRIPTION`) | Read through `read_survey()` by the tests in C3 and C8; not changed. Public, and cleared for Claude Code |

Shape of the data:
- **The survey file.** One row per household, 20 rows, keyed by `hhid`, which `read_survey()` requires to be unique.
- **Columns that matter.** `welfare` is present and strictly positive in every row, in a unit the package does not document. `weight` is present and strictly positive in every row.
- **The estimate.** The unit of observation is the household and the weight is `weight`. It covers every household the survey represents: the denominator is the total weight of all households. It is per household, not per person.
- **Outputs.** The work produces no dataset.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | `poverty_gap()` exported and documented, giving 1/6 on the hand-built table and a value between 0 and the headcount on the shipped survey; the other files pinned | `R/poverty_gap.R`, `tests/testthat/test-poverty_gap.R`, `NAMESPACE`, `man/poverty_gap.Rd` | C1, C2, C3, C7, C8 | By code: `poverty_gap()`, its testthat file, `roxygenise()`, `devtools::test()`, `git hash-object` |
| S2 | Stops on every bad input of `headcount()` and on a line at or below zero; the package builds and checks clean; the outputs map names the new function | `R/poverty_gap.R`, `tests/testthat/test-poverty_gap.R`, `man/poverty_gap.Rd`, `.cg-docs/verification.md` | C4, C5, C6, C8 | By code: the input checks, their tests, `devtools::test()`, `R CMD build` and `R CMD check` in a temporary library |

---

**Risk (`cg.py tier`, measured):** `tier: elevated`. Reason: "number: it computes a number someone will read, or can change one". The data line says the survey is cleared because its level is Public. No dataset stays closed.

**Self-review.** I wrote the plan and also reviewed it. No independent reviewer has looked at it.

| Principle | Verdict | Finding |
|---|---|---|
| P1 Specify before generating | PASS | Every requirement has a check, and each check names an outcome that means failure. C1 fails on each of the four wrong results the intent names. C8 passes today, but it is a pin, which the rules allow. |
| P3 Deterministic by default | FLAG (minor) | Every slice is done by code, and nothing is sampled. The build and check commands use paths on this machine (`~/temp/...`). This affects only where the scratch output goes, not the project's code or its numbers. |
| P6 Smallest change | PASS | Two slices, five files at most, no new dependency. C2 (the copies with deliberate mistakes) is extra work. I kept it because it shows that C1 can actually fail. |
| P10 Correct in the domain | FLAG | Weights are used, the denominator is every household, and C3 bounds the range. But `poverty_gap()` won't stop on zero or negative welfare, because decision D4 copies the checks of `headcount()`. I listed this under what no check would catch. A guard for it would be a correction from you. |
| P12 Governed data | PASS | One dataset. It is recorded as Public and is cleared for Claude Code. No dataset is produced. |

**What I did not check:**
- Whether `R CMD check` adds a NOTE for `GLOSSARY.md` at the top level (an inference). A NOTE does not fail C6.
- That `devtools::test(..., stop_on_failure = TRUE)` exits non-zero when a test fails. I checked only that it takes that argument.

**Do you approve this plan?** A plain yes approves it, and it is recorded under your name. I'll take any other reply as a change or a question.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the plan. Or tell me what to change, for example "add a check that stops on welfare at or below zero".
* **Project:** Adding a poverty gap index to toypov. The intent is decided and the plan is a draft at the approval step. Slice S1 comes after your yes.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I didn't record your reply as an approval. A "yes, but" asks for a change, so I made it first, and the plan needs a fresh yes on the new text.

I added one item to the Never list in `.cg-docs/plans/2026-11-26-poverty-gap-index.md`. It now reads:

> - Never: change `R/headcount.R`, `R/n_households.R`, `R/read_survey.R` or `inst/extdata/survey.csv`; **change any file under `data-raw/`**; add collapse, rlang or cli; install a package into the human's R library; change a check so that it passes; build what is out of scope; commit, push or publish without the human asking.

Nothing else in the plan changed. `cg.py validate` printed `problems: 0` and `warnings: 0`.

The project has no `data-raw/` folder today, so for now the line protects nothing. No slice touches that path. I read the line as also ruling out creating a file there.

**Do you approve the plan with this change?** A plain yes approves it, and it is recorded under your name. I'll take any other reply as a change or a question.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the amended plan, or tell me what else to change.

[exit code: 0]

### H3 yes

> Yes.

The plan is approved, and the approval is recorded under your name. No code has changed yet.

- **Plan:** `.cg-docs/plans/2026-11-26-poverty-gap-index.md`, now marked `approved`.
- **Record:** `.cg-docs/approvals/2026-11-26-poverty-gap-index.1314cc400bb5b715.json`, which ties your "Yes." to this exact text.

**Goal:** a new exported `poverty_gap(dt, line = 3)` returns the poverty gap index, FGT(1). That is the weighted average gap below the line as a share of the line, with every household that is not poor counted as zero. It gives exactly 1/6 on the two-row example table.

**Requirements and their checks:**

| Requirement | What it says | Checked by |
|---|---|---|
| R1 | The formula is right | C1: 1/6 on the example table. C2: the tests fail before the function exists, and fail on copies with each of the four common mistakes. |
| R2 | On the shipped survey, the result is above 0 and below the headcount | C3 |
| R3 | It stops on the same bad inputs as `headcount()`, with the same messages | C4 |
| R4 | It stops when the line is zero or negative | C5 |
| R5 | It is exported | C6: `R CMD check` shows no ERROR or WARNING |
| R6 | The help page says FGT(1), share of the line, averaged over all households | C7 |
| R7 | Five existing files stay byte for byte as they are | C8: compares their fingerprints with today's |

**Order of work:**
1. **S1:** the function, its help page, its export line, and the tests for its value.
2. **S2:** the checks for bad inputs, a full `R CMD check`, and an update to the project's verification file.

**What stays as it is:**
- **Data:** none of it is off limits. The one dataset, `inst/extdata/survey.csv`, is recorded as Public, and the work only reads it.
- **Deferred:** a general `fgt(alpha)` function, one shared input-check helper for both functions, and documenting what unit welfare is measured in.

**What no check would catch:**
- A line given in a different unit from welfare.
- The input checks of the two functions drifting apart later.
- Zero or negative welfare in a table built by hand.
- The survey result is only checked against bounds, not against an outside figure.

**Self-review:** P1 PASS, P3 FLAG (minor: scratch paths are specific to this machine), P6 PASS, P10 FLAG (zero or negative welfare isn't stopped), P12 PASS. I reviewed my own plan; no independent reviewer looked at it.

**Not looked up:** whether `R CMD check` adds a NOTE about `GLOSSARY.md` (it wouldn't fail C6), and whether `devtools::test()` really exits non-zero when a test fails.

Nothing has been committed. The plan, its intent and the approval records can go into one commit whenever you ask.

**Next steps: Done**
* **Your move:** Type `/cg S1 of the poverty gap index plan` to start the first slice.
* **Project:** Poverty gap index for toypov: the plan is approved, and S1 is next.

[exit code: 0]
