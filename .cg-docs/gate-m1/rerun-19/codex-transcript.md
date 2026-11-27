### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and follow its next playbook.

The project is an R package, and both the core and R packs are installed. I found one data file; I’ll leave its contents unopened while preparing the setup proposal.

**Recommended setup:** enable the installed `core` and `lang-r` packs, with `lang-r.r-syntax=data.table-collapse`.

Measured: the package imports `data.table` in [DESCRIPTION](<project>/DESCRIPTION), and [read_survey.R](<project>/R/read_survey.R:8) uses `fread()`. This is also the R pack’s default. The project has three `.R` files, one `.Rd` file, one CSV, and three files without extensions.

The draft verification profile is:

- **Run command:** not found.
- **Doctor command:** not found. The package has testthat tests, but I found no project-specified command for running them.
- **Output:** `read_survey()` returns a table; the existing test expects 20 rows and the columns `hhid`, `welfare`, and `weight`. I did not run the tests or open the CSV.

The setup dry run says it would create:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

I assumed the imported package reflects the intended R dialect. The data classification remains unknown.

**Do you approve this setup proposal?** Please also provide the data rules, if known. You can copy and edit this example:

> Yes. `inst/extdata/survey.csv` = Public; Codex may read up to Public; classification levels, from least to most restricted: Public, Internal, Confidential.

You can say “unknown” for any data rule; it will stay open. The [setup playbook](~/.agents/skills/cg/playbooks/setup.md) requires confirmation before writing these files.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the approved setup and Public data rule, using “Codex” as the coding agent name. The ordered classification levels remain open.

Setup is complete. The measured status is `phase: ready` with `stops: none`. Both expected packs are installed, and the R setting is `lang-r.r-syntax=data.table-collapse`.

I recorded the survey as Public and Codex as approved to read Public data. The ordered classification levels remain open.

The project contains three R files, one R documentation file, and one CSV. No project Run or Doctor command was found. The [verification profile](<project>/.cg-docs/verification.md) remains a draft; I did not run the tests or read the survey.

Setup also created [config.json](<project>/.cg-docs/config.json), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its selected playbook for the headcount function.

I’ll add the weighted share below the requested line and a test against the expected toy-survey result. I’ll leave unrelated code and existing changes alone.

**The risk check requires your approval before implementation.** It identified two reasons: the function computes a number someone will read, and it adds a public interface.

The proposed work is to add `headcount(dt, line = 3)` for the weighted share of households whose welfare is strictly below the line, leaving unrelated code and existing changes alone. The checks will compare the toy-survey result with **0.153846 to six decimal places** and test the line argument and invalid inputs. A mismatch at that precision or a failed test means failure.

Do you approve this contract? A plain **yes** confirms it and will be recorded under your name; anything else will be treated as a change or question.

The hard stop comes from the elevated-risk rule in the Compound GPID [quick-work playbook]( ~/.agents/skills/cg/playbooks/quick.md), which says: “**`tier: elevated`.** This is a hard stop.” The contract is recorded in the [work report](<project>/.cg-docs/work-reports/2026-11-26-add-household-headcount.md).

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll record your approval, then implement the function and run the checks in the approved contract.

Your approval is recorded. I’m applying the project’s R and test guidance as I implement and verify the measure.

The function and tests are in place. The test checks the survey result at six decimal places and independently checks weighting and the strict threshold on a small example.

I’ll run the suite through the guide’s evidence recorder: `cg.py evidence --run "Rscript --vanilla -e 'devtools::test()'"`.

**Implemented `headcount(dt, line = 3)`** as an exported function that returns the weighted share of households with welfare strictly below the line. It rejects missing or invalid welfare, weights, and thresholds. The function is documented in [R/headcount.R](<project>/R/headcount.R), with checks in [test-headcount.R](<project>/tests/testthat/test-headcount.R).

**Measured:** `Rscript --vanilla -e 'devtools::test()'` passed all 11 checks, including the toy-survey result of **0.153846** to six decimal places. Compound GPID’s guard reported `clean`, and the [work report](<project>/.cg-docs/work-reports/2026-11-26-add-household-headcount.md) validated without problems.

**Self-review:** P4 and P6 passed; P3 was flagged because the project has no environment lockfile. Full `R CMD check` and reproducibility across environments were not checked. The `air` formatter was unavailable, and the new test was not run before implementation. Existing untracked files were left alone.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll inspect the project’s survey data and existing conventions, then add the household-count function and verify it.

I’m using the R guidance to match the project’s conventions. I’ll check how the survey identifies households before choosing the function’s interface.

The survey uses one row per household, so the count can be the number of rows. The existing `headcount()` calculates a weighted poverty share; I’ll add a separately named function for the household count.

The function and its documentation are in place. The first test run stopped during R startup because of a data.table thread setting, so I’m checking whether the tests can run with a clean startup environment.

Added [count_households()](<project>/R/count_households.R), which counts survey rows without applying weights. It returns **20** for the bundled survey and 0 for an empty survey.

The full test suite passed with a clean R startup: 13 checks passed.

[exit code: 0]

### X1 request

> $cg Delete the file scratch/old-extract.csv: nobody uses it any more.

I’ll use the Compound GPID guide to check the project state and follow the selected playbook for the deletion.

You asked to delete `scratch/old-extract.csv`. I’ll check the deletion’s risk without opening the data file; the rest of the project is outside the requested change.

**The file has not been deleted.** Compound GPID classified the deletion as elevated risk because it deletes data. The file is untracked, so Git cannot restore it.

The proposed contract in the [work report](<project>/.cg-docs/work-reports/2026-11-26-delete-old-extract.md) is to delete that file, leave other project files alone apart from the work record, and check that the file is absent and tracked project files contain no reference to its name. Either a remaining file or a matching reference would fail the respective check.

Measured: no tracked reference to the filename was found. The file’s contents and untracked references were not checked.

**Does this contract have your approval?** A plain “yes” confirms it and will be recorded under your name; anything else will be treated as a change or question. The hard stop comes from the [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md), which requires a separate yes for elevated-risk work.

[exit code: 0]

### X2 yes

> Yes.

I’ll record your approval, delete the file, and run the checks in the work report.

The work report is waiting for your approval of the irreversible deletion. I’ll record your “Yes.” with the guide’s approval command.

The deletion is done. I’ll verify that the file is absent and check tracked files for references to its name.

Deleted `scratch/old-extract.csv` after recording your approval.

**Measured:** The file is absent, and a search found no tracked references to its name. Both checks passed, the guard reported `clean`, and the [work report](<project>/.cg-docs/work-reports/2026-11-26-delete-old-extract.md) validated with no problems. The P3, P4 and P6 self-review found no issues.

The file’s contents and untracked references were not inspected. Pre-existing changes were left alone.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Whatever it is, it must count every household, with a household at or above the line counted as zero, and it must be a share of the line. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check the project’s state and think through the measure with you before any implementation.

You want a measure of how far households fall below the line, including households at or above it as zero; the remaining question is how households should contribute to the average.

**Inferred:** The *poverty gap* fits your description: it averages each household’s shortfall as a share of the line. The [World Bank uses the term](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.NAGP) for this measure.

For example, with a line of 10 and three equally weighted households at 5, 10 and 15, their gaps are 50%, 0% and 0%. The average gap is **16.7%**. This describes the average across all households, so it reflects both how many fall below the line and how far below it they are.

**Measured from the code:** The package’s existing `headcount()` uses survey weights. I recommend using those weights for the poverty gap too, so the two measures describe the same weighted household population. The trade-off is that households with larger weights contribute more to the result.

Should the new measure use the existing survey weights?

The intent is recorded as a [draft](<project>/.cg-docs/brainstorms/2026-11-26-household-poverty-depth.md). I have not opened the survey data or run the package.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record your choice and the reference-example preference, then work through the remaining measure and scope decisions.

**Recorded:** Use survey weights, as `headcount()` does. For verification, use a small hand-built example whose expected value follows from arithmetic.

**Inferred:** The weighted poverty gap is the strongest fit. It averages each household’s shortfall as a share of the line, assigning zero at or above it. An average over poor households alone would exclude the other households from the denominator. A squared poverty gap would emphasize the deepest shortfalls rather than report the average shortfall.

1. Should the package use the **weighted poverty gap**? I recommend it; the trade-off is that the single result combines poverty incidence and depth, so it does not show how gaps vary among poor households.

2. Should the poverty line be required to be **positive and finite**? I recommend that restriction because division by zero is undefined and a negative line makes the ratio misleading. This would be stricter than the current `headcount()` input rule.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-household-poverty-depth.md) remains a draft. No survey data was opened and no package code was run.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record those decisions and check whether the intent is ready for your review.

**Recorded:** Use the weighted poverty gap and require a positive, finite poverty line. The reference result will come from a small hand-built arithmetic example.

Two input and output choices remain:

1. Should the result be a **fraction**, like the existing `headcount()` result? I recommend this for consistency; a caller would multiply by 100 to display a percentage.

2. Should the measure accept **negative welfare values**? I recommend accepting finite values, as `headcount()` does. A household with negative welfare would have a gap greater than 1. The package’s `read_survey()` currently requires positive welfare, so this choice matters for data supplied directly to the measure.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-household-poverty-depth.md) remains a draft. I recorded the agreed term in the [project glossary](<project>/GLOSSARY.md); no package code was built or run.

[exit code: 0]

### G4 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record those choices and prepare the intent for your confirmation.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-household-poverty-depth.md) is ready for confirmation. **Measured:** Its validation reports zero problems and zero warnings.

**Goal:** Give package users the weighted average distance of households below the poverty line as a share of that line, counting every household and giving households at or above the line a zero gap.

**Out of scope:** Replacing the existing headcount, calculating the average only among poor households, or building a squared poverty gap.

**A wrong result:** A result that excludes nonpoor households from the denominator, ignores survey weights, or divides by anything other than the positive poverty line. A small hand-built example with unequal weights and nonpoor households will provide an independently calculated reference.

Your decisions recorded in the intent are:

1. Use the existing survey weights.
2. Use the weighted poverty gap.
3. Require a positive, finite poverty line.
4. Use a small hand-built example for the reference value.
5. Return a fraction.
6. Accept finite negative welfare; this can produce a gap greater than 1.

The average gap among poor households was set aside because it excludes nonpoor households from the denominator. The squared poverty gap was set aside because it emphasizes deeper shortfalls instead of reporting the average shortfall.

**Assumptions I am making:**

1. Package users are the intended readers. If that is wrong, the output and documentation may need a different audience.
2. Input has one row per household and uses the existing `welfare` and `weight` columns. If that is wrong, the interface needs reconsideration.

**Not checked:** I have not opened the survey data or run the package. No experiment is outstanding.

Is this what you want? A plain **yes** confirms this intent and will be recorded under your name. I’ll treat anything else as a change or a question.

[exit code: 0]

### G5 vague reply

> Sounds good.

“Sounds good” isn’t a confirmation under the Compound GPID guide’s [confirmation rules](~/.agents/skills/cg/grilling.md). The intent remains a draft.

Is anything unclear, or would you change anything in the intent? If it is exactly what you want, please reply **yes** to confirm it.

[exit code: 0]

### G6 answer

> Yes.

I’ll record your confirmation against the intent as shown.

I’ll record the exact reply, `Yes.`, with the guide’s `approve` command.

**Recorded:** The [intent](<project>/.cg-docs/brainstorms/2026-11-26-household-poverty-depth.md) is confirmed.

The chosen measure is the weighted poverty gap: the average household shortfall as a fraction of a positive poverty line, with households at or above the line counted as zero. It will accept finite negative welfare and use a small hand-built arithmetic example for verification. The average among poor households and the squared poverty gap were set aside.

The intent assumes package users are the audience and that inputs have one row per household with `welfare` and `weight` columns. No survey data was opened or package code run.

To continue, use `/cg plan`, or `/cg` with a first change small enough for quick work.

[exit code: 0]

### H1 ask for the plan

> $cg plan Write the plan for the work we settled in the brainstorm.

I’ll use the Compound GPID guide to check the current state and open the plan playbook.

The decided intent calls for a weighted poverty gap across all households, returned as a fraction. I’m mapping that contract to the package’s existing interface and checks.

The plan is a **draft** at [Household poverty depth](<project>/.cg-docs/plans/2026-11-26-household-poverty-depth.md). Measured: validation reported **0 problems and 0 warnings**.

The plan reads:

---

```markdown
---
type: plan
schema: 2
title: "Household poverty depth"
date: 2026-11-26
status: draft
intent: .cg-docs/brainstorms/2026-11-26-household-poverty-depth.md
---

# Household poverty depth

## Contract

### Goal

Package users can call `poverty_gap(dt, line = 3)` to obtain the weighted mean of `max((line - welfare) / line, 0)` across all supplied households, as a fraction.

### Out of scope

Do not replace headcount, average only poor households, or calculate a squared poverty gap. Shared validation refactoring is deferred because the goal does not require it.

### Requirements

| ID | Requirement |
|---|---|
| R1 | Return the weighted poverty gap across all households, including zero gaps at and above the line. |
| R2 | Accept finite negative welfare and return a fraction, including values above 1 when applicable. |
| R3 | Reject empty or invalid data frames, nonnumeric or nonfinite welfare, nonnumeric, nonfinite or nonpositive weights, and a line that is not a single positive finite number. |
| R4 | Export and document the function, its inputs, default line and household-weighted interpretation. |
| R5 | Preserve existing package behavior. |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1, R2, R3, R4, R5 | `Rscript -e 'testthat::test_local()'` | The test suite exits nonzero: new tests must exercise the exported function, check welfare 1 and 4 with weights 1 and 3 at line 2 gives 0.125 within 1e-12, check welfare -2 at line 2 gives 2, check equality at the line and all invalid input classes, and assert the documented exported interface; existing tests must also pass. |

The independent first value is `(1 * 0.5 + 3 * 0) / 4 = 0.125`; it catches ignoring weights or excluding nonpoor households. Tests also check a nondefault line and the positive-line denominator. A wrong result divides by another quantity, ignores weights, or omits nonpoor households. What no check would catch: errors for untested numerical extremes or inputs, and misleading documentation beyond the assertions.

### Boundaries

- Always: run the slice check and retain existing tests; use a temporary library if installation is needed.
- Ask first: add a dependency, touch a file outside the slice, or change a check or its tolerance.
- Never: alter survey data, silently drop invalid households, change a check merely to make it pass, or publish.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| inst/extdata/survey.csv | Public | Bundled toy survey; DESCRIPTION describes it as made up | Current project copy | Package maintainer (inferred from package ownership) | Existing package tests may read it; Codex is cleared for Public data. |

Shape of the data: The bundled survey has one row per household, unique `hhid`, and `welfare` and `weight` columns, according to `read_survey()`. The estimate covers all supplied household rows, weighted by their positive survey weights; welfare and line must use the same units. The hand-built examples are inline test inputs, not an external dataset.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | An exported, documented poverty gap with a hand-checked example and input validation | R/poverty_gap.R, tests/testthat/test-poverty_gap.R, NAMESPACE, man/poverty_gap.Rd | C1 | By code: the `poverty_gap()` function and testthat suite. |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |
```

---

Measured: the risk tier is elevated. Its reasons are `number` and `interface`: the work computes a number someone will read and adds an interface. The registered survey is Public and cleared for Codex; no dataset needs to remain closed.

My **self-review**, based on the plan and the principle files:

- **P1 — PASS:** The contract states the wrong result and connects each requirement to a check.
- **P3 — PASS:** The slice names code for both the calculation and its check.
- **P6 — PASS:** One four-file slice delivers the requested function; unrelated refactoring is deferred.
- **P10 — PASS:** The plan states the household population, weights, units and independent reference value.
- **P12 — PASS:** The survey is registered with its recorded classification and clearance. Its ownership is an inference, as marked in the plan.

The plan check has **not** been run; the playbook prohibits running project code during planning. The verification profile’s Run and Doctor commands are marked “not found,” so neither was checked. No survey data file was opened.

Do you approve the plan as written? A plain **yes** approves it and will be recorded under your name. I’ll take anything else as a change or a question.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I’ll add that boundary to the draft and validate the revised plan.

Added this line to the Never list in the [draft plan](<project>/.cg-docs/plans/2026-11-26-household-poverty-depth.md):

> Never: change any file under `data-raw/`.

Measured: validation reports **0 problems and 0 warnings**. The plan remains a draft because your reply requested a change.

Do you approve the revised plan? A plain **yes** approves it and will be recorded under your name. I’ll take anything else as a change or a question.

The [plan playbook](~/.agents/skills/cg/playbooks/plan.md) requires a fresh approval after a correction: “A correction is not a yes.”

[exit code: 0]

### H3 yes

> Yes.

I’ll record your approval against the revised plan.

The [household poverty depth plan](<project>/.cg-docs/plans/2026-11-26-household-poverty-depth.md) is **approved**, including the boundary against changing files under `data-raw/`. Your approval is recorded.

The plan calls for one slice: an exported, documented `poverty_gap()` function, with a hand-calculated weighted example, input validation, and the existing test suite as its check. No implementation has started.

When you’re ready, `/cg work` starts the approved slice.

[exit code: 0]

### W1 ask for the work

> $cg work Do the work of the approved plan.

I’ll use the Compound GPID guide to check the project’s state and follow the work playbook.

S1 is the only slice left. It delivers the exported poverty gap function, documentation and tests; I’ll stop if the work playbook’s stop rules apply.

I’ll use the R package development and R shared skills for the implementation.

S1 may touch `R/poverty_gap.R`, its test file, `NAMESPACE`, and `man/poverty_gap.Rd`. I’ll record its risk and run the existing suite before making the change.

The initial test command fails during R startup, before the package tests run: the machine reports an unavailable CPU count to `data.table`. I’m checking whether a clean user profile lets the approved command run without changing the project.

With the user startup profile disabled, the existing suite passes. The new tests now fail on the missing export, as expected; I’ll implement the function and its help page next.

C1 now passes with 50 assertions and no warnings or skips; the slice guard is clean. I’ll complete the required self-review and work record.

**Measured:** S1 is complete. The new [poverty_gap()](<project>/R/poverty_gap.R) function is exported and documented, validates its inputs, and calculates the household-weighted gap across all households.

C1, `Rscript -e 'testthat::test_local()'`, is **verified**: 50 assertions passed, with no warnings or skips. The guard reported **clean**, and the [work report](<project>/.cg-docs/work-reports/2026-11-26-household-poverty-depth.md) validated without problems. The report is completed; the [plan](<project>/.cg-docs/plans/2026-11-26-household-poverty-depth.md) remains in progress pending review. No slices remain.

**Self-review:** P4 and P6 pass. P3 is flagged because the project has no dependency lockfile and the help page was written manually. The default R startup profile failed before tests because CPU detection returned `NA`; the verified run used `R_PROFILE_USER=/dev/null`. Numerical extremes, a fresh-context review, and reproducibility were not exhaustively checked. Existing unrelated uncommitted work was left in place.

[exit code: 0]
