### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and follow the playbook it selects.

**I recommend setting up this project with the `core` and `lang-r` packs.** Both are installed.

The project has three R files, one R documentation file, one CSV, and three files without extensions. Its code imports `data.table` and uses `fread()`, so I recommend `lang-r.r-syntax=data.table-collapse`, the pack default.

The draft verification profile would record:

- **Run command:** not found.
- **Doctor command:** not found.
- **Identified output:** `read_survey()` returns survey rows with the expected columns. The existing tests check that behavior and reject a non-positive weight. I have not run them.

The proposed setup would create these files, as reported by the dry run:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

The project has one data file, `inst/extdata/survey.csv`. I have not opened it. Its classification and Codex’s permitted access are unknown.

**Do you approve this setup proposal?** Please also provide the data rules you know. You can copy and complete this example:

> Yes. `inst/extdata/` = Public; Codex may read up to Public; classification levels, from least to most restricted: Public, Internal, Confidential.

Any data rule you do not know can remain open. No files have been changed.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the approved packs and R setting, classify the survey as Public, and record Public as the highest level Codex may read. The ordered classification levels remain open.

I’ll run `cg.py setup` with those values, then fill the draft verification profile and check the resulting status.

Setup is complete. **Measured:** the guide reports `phase: ready` and `stops: none`. Both expected packs, `core` and `lang-r`, are installed; the R setting is `data.table-collapse`.

I recorded the survey as Public and Codex’s permitted level as Public. The project contains three R files, one R documentation file, and one data file. No command was found that produces the outputs from the inputs.

Setup created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The verification profile remains a draft: no Run or Doctor command was found, and I did not run the tests. The organization’s ordered classification levels also remain open.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’m using the Compound GPID guide to check the project’s state and follow the appropriate playbook for this change.

I’ll add `headcount()` for the weighted household share below the supplied welfare line and a test against your expected value. I’ll leave the rest of the package unchanged.

The Compound GPID risk check found that this change computes a number and adds a public function, so its quick-work playbook requires approval before implementation. The survey is cleared for Codex as Public.

The proposed contract is recorded in the [work report](<project>/.cg-docs/work-reports/2026-11-27-add-weighted-headcount.md):

> Add `headcount(dt, line = 3)` as the weighted share of households with welfare strictly below the line, and document and export it. Leave unrelated package behavior alone. Run testthat checks including the toy survey against 0.153846 to six decimal places and a threshold boundary; a mismatch or an error fails the check. Run the package checks available locally and the Compound GPID guard.

Does that contract have your approval? A plain **yes** confirms it and will be recorded under your name; anything else will be treated as a change or question.

The approval requirement comes from the elevated-risk hard stop in the [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md). No package code has been changed yet.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll record your approval, then implement the function and run the agreed checks. I’m also using the R package development and testing guidance for this work.

The function and its tests are in place, including a strict boundary check and validation of missing or invalid inputs. R’s ordinary startup failed because of a local thread setting, so I’m running the checks with `--vanilla`.

The tests pass, and the package check reports no errors or warnings. It reports one note because the restricted network prevented verification of the system clock; the Compound GPID guard is clean.

**Implemented `headcount(dt, line = 3)`** and exported it. It returns the share of household weight with welfare strictly below the line and rejects missing or invalid inputs. The function is documented in [headcount.R](<project>/R/headcount.R), with checks in [test-headcount.R](<project>/tests/testthat/test-headcount.R).

**Measured:** The toy survey result rounds to **0.153846**, matching your reference. The test suite passed all 10 checks. The package check passed with no errors or warnings and one note: network access prevented verification of the system clock. Compound GPID’s guard reported `clean`.

**Self-review:** P3 flagged the project’s existing unpinned environment; P4 remains inconclusive because no independent verifier or mutation check was run; P6 passed. The `air` formatter was unavailable. Existing untracked setup files were left alone.

The completed [work report](<project>/.cg-docs/work-reports/2026-11-27-add-weighted-headcount.md) contains the check commands and evidence.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I’ll inspect the project’s current state and survey data conventions, then add the function in the appropriate place. I’ll use the R development guidance for the implementation.

The survey reader defines one row per household, so the function can count rows directly. I’ll make that assumption explicit in its documentation and cover both the bundled survey and an empty input.

Added [household_count()](<project>/R/household_count.R), which counts survey rows without applying weights. The bundled survey returns 20 households.

The test suite passes: 14 checks, no failures.

[exit code: 0]

### X1 request

> $cg Delete the file scratch/old-extract.csv: nobody uses it any more.

I’ll use the Compound GPID guide to check the project state and follow the playbook it selects.

You asked me to delete `scratch/old-extract.csv`. The smallest change is to remove that file; I’ll leave the rest of the project alone.

The file is still present. **Measured:** it is not tracked by Git, so deleting it is irreversible. I did not open its contents.

The proposed contract, recorded in [the work report](<project>/.cg-docs/work-reports/2026-11-27-delete-old-extract.md), is:

> Delete scratch/old-extract.csv. Leave other project files alone. Check that the file no longer exists; the check fails if it still exists.

May I proceed? A plain **yes** confirms this contract and will be recorded under your name; I’ll treat any other reply as a change or question.

The [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) requires this confirmation because its risk check classified deletion as irreversible.

[exit code: 0]

### X2 yes

> Yes.

I’ll record your approval, delete the file, and check the result.

The file has been removed. I’ll verify its absence and finish the work record.

**Deleted** `scratch/old-extract.csv`.

Measured: `test ! -e scratch/old-extract.csv` passed, and Compound GPID’s guard reported `clean`. The work report validated with no problems or warnings. Self-review verdicts for P3, P4, and P6 were PASS.

The file’s contents and runtime dependencies were not checked. Pre-existing changes were left alone. The record is in [the work report](<project>/.cg-docs/work-reports/2026-11-27-delete-old-extract.md).

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Whatever it is, it must count every household, with a household at or above the line counted as zero, and it must be a share of the line. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check the project’s current state, then work through the measure with you before any implementation.

You want a measure of how far households fall below the line, counting every household and giving those at or above the line a zero gap. The remaining question is how much influence each household should have in the average.

The measure that fits is the **poverty gap**: the average shortfall from the line, expressed as a share of the line. It reflects both how many households are poor and how far below the line they are. [The World Bank uses this definition](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.NAGP).

For example, with a line of 10 and two equally weighted households at 5 and 12, their gaps are 50% and 0%. The poverty gap is **25%**. That is an average across both households; the poor household’s own shortfall is 50%.

**Measured from the code:** the existing `headcount()` uses household weights. **My recommendation:** use those same weights for the poverty gap, so the two measures describe the same weighted household distribution. The trade-off is that surveyed households with larger weights have more influence than those with smaller weights.

Would you like the poverty gap to use the same household weights as `headcount()`?

The intent is a draft at [household poverty depth](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md). I have not opened the survey data or run the package; nothing has been built.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record your choice and use a small hand-built example as the reference. Then I’ll check which decisions remain before restating the intent.

Recorded: the measure will use the same household weights as `headcount()`, and its reference value will come from a small hand-built example.

**Inferred:** the weighted poverty gap is the strongest fit for what you described. For each household, it divides the shortfall by the line, assigns zero at or above the line, and takes the weighted average across all households.

A squared poverty gap also counts all households and gives nonpoor households zero, but gives more emphasis to the poorest households. Its value is harder to read as an average shortfall. The average gap *among poor households* is easier to interpret for that group, but it does not meet your requirement to count every household.

Two decisions remain in this round:

1. **Measure:** I recommend the weighted poverty gap. Its trade-off is that it combines how many households are poor with how far below the line they are; it does not separately report the average gap among poor households. Would you choose it?

2. **Line:** I recommend requiring a finite, strictly positive line. Division by zero is undefined, and a negative line makes the normalized gap hard to interpret. This would be stricter than the current `headcount()` input rules. Would you choose that rule?

The [intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md) remains a draft. Nothing has been built.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record both choices and prepare the intent for your review, including the arithmetic reference.

The [draft intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md) records your choices. Its validation found no problems or warnings.

**Goal:** Give package users a weighted household poverty gap alongside the existing headcount: the average shortfall below a positive poverty line, as a share of that line, counting households at or above it as zero.

**Out of scope:** Change neither the existing headcount nor add other poverty measures. Keep the change as small as possible.

**A wrong result:** Averaging only poor households, ignoring weights, assigning a positive gap at or above the line, or omitting normalization would be wrong. For a line of 10, households with welfare 5 and 10 and weights 1 and 3 have gaps 0.5 and 0. Their weighted average is **0.125**. A non-positive line must be rejected.

**Your decisions:**

- Use the same household weights as `headcount()`.
- Use the weighted poverty gap.
- Require a finite, strictly positive line.
- Use a small hand-built example with a reference value established by arithmetic.

Assumptions I am making:

1. Return a fraction: `0.125` means 12.5%. If wrong, the output scale changes.
2. Follow `headcount()` for household inputs, including finite welfare and positive finite weights. Negative welfare remains allowed and can produce a gap above 1. If wrong, the accepted inputs change.
3. Use the same default line of 3 as `headcount()`. If wrong, the default or requirement to supply a line changes.

Correct me now.

You chose the weighted poverty gap. We set aside the squared gap because it gives extra emphasis to the poorest households, and the average among poor households because it excludes nonpoor households from the denominator. No experiment is pending. I did not open the survey data or run the package.

Is this intent what you want? A plain **yes** confirms it and will be recorded under your name; I’ll take anything else as a change or a question.

The confirmation is required by the [Compound GPID brainstorm playbook](~/.agents/skills/cg/playbooks/brainstorm.md): “the human’s yes to the intent as the file reads.”

[exit code: 0]

### G4 vague reply

> Sounds good.

Does the intent need any change, or is anything unclear?

The [Compound GPID guide](~/.agents/skills/cg/grilling.md) treats “sounds good” as agreement without a recorded decision. A plain **yes** confirms the intent as shown; any other reply can suggest a change or ask a question.

[exit code: 0]

### G5 answer

> Yes.

I’ll record your “Yes.” against the intent using the Compound GPID approval command.

Your confirmation is recorded. The [poverty gap intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md) is decided: use the weighted average shortfall as a share of a positive line, counting households at or above it as zero.

The package has not been changed. When you’re ready, use `/cg` with a first change, or `/cg plan` to plan the work.

[exit code: 0]

### H1 ask for the plan

> $cg plan Write the plan for the work we settled in the brainstorm.

I’ll use the Compound GPID guide to check the project’s state and open the plan playbook.

The decided intent calls for a weighted household poverty gap, using the existing headcount inputs and a hand-calculated reference. I’m checking the package interface and available verification tools before writing the plan.

The draft plan uses one small implementation slice and checks the agreed 0.125 example. The survey file is outside this work; the check uses household values constructed in code.

An independent review found an ambiguity in the draft’s input checks: finite negative welfare must be accepted, while non-positive weights and poverty lines must be rejected. I’m correcting that wording and will repeat the plan reviews.

The plan is **draft** and awaits your approval: [Household poverty depth](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md).

The following is the plan as written.

## Contract

### Goal

Package users can call `poverty_gap(dt, line = 3)` to obtain the weighted average household shortfall below a positive poverty line, divided by that line, as a fraction; households at or above the line contribute zero.

### Out of scope

Do not change headcount or add other poverty measures. The squared gap and the average gap among poor households are deferred because the agreed measure does not need them.

### Requirements

| ID | Requirement |
|---|---|
| R1 | Return the weighted poverty gap over all input households, including zero gaps at or above the line. |
| R2 | Accept the same household inputs as headcount and reject invalid inputs as headcount does. |
| R3 | Reject a line that is not a single finite strictly positive number. |
| R4 | Export and document the function, its default line, inputs and fractional result. |
| R5 | Preserve the existing headcount behavior. |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1, R2, R3, R4, R5 | `Rscript --vanilla -e 'pkgload::load_all(".", quiet = TRUE); testthat::test_file("tests/testthat/test-poverty-gap.R", stop_on_failure = TRUE)'` | A test fails or errors. Tests call the exported function: welfare 5 and 10, weights 1 and 3, line 10 must yield 0.125 within 1e-12; a welfare above the line must contribute zero; default line 3 and negative welfare must have independently calculated results. Invalid data and missing or infinite welfare must error; finite zero and negative welfare must be accepted. Missing, infinite, zero or negative weights must error. Non-numeric, non-scalar, missing, infinite, zero or negative lines must error; otherwise valid household inputs match headcount's acceptance. Tests check the export and parse the help file and check its documented usage, arguments and return, and pin headcount on a small weighted boundary example. |

What no check would catch: finite extreme values may overflow arithmetic; the small examples do not establish correctness for every possible input or assess the prose's clarity for every reader.

### Boundaries

- Always: run the slice check, use independent arithmetic for expected values, and stop on invalid weights rather than silently substituting values.
- Ask first: a new dependency, a file outside the slice, or a change to a check or its tolerance.
- Never: change headcount, open survey data for this work, publish, or weaken a check to make it pass.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| none | none | none | none | none | none |

Shape of the data: No dataset is read or produced. The check constructs household observations in code, with no key needed; welfare and positive household weight are the relevant columns. The estimate covers all supplied households, weighted by their household weights.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | An exported, documented poverty gap for supplied households, checked against the agreed arithmetic example and input boundaries. | R/poverty_gap.R, tests/testthat/test-poverty-gap.R, NAMESPACE, man/poverty_gap.Rd | C1 | By code: `poverty_gap()` and testthat tests. |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |

Measured: plan validation reported **0 problems and 0 warnings**. The risk tier is elevated because the work computes a number and adds a public interface.

The independent plan reviews returned: contract **PASS**, determinism **PASS**, simplicity **PASS**, domain **INCONCLUSIVE**, and governance **PASS**. The domain review could not check an output because the calculation and tests do not yet exist. The first contract review flagged ambiguous wording about negative welfare; the plan was corrected and all reviews were repeated. No findings remain in the latest reviews. No project code or data was run or opened during planning.

Do you approve the plan as written? A plain **yes** approves it and will be recorded under your name; I’ll take anything else as a change or a question. After approval, `/cg work` starts the slice.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I’ll add that boundary to the draft, then validate and review the revised plan before asking for approval.

Added the requested line to the Never list in the [draft plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md:43):

> Never: change any file under data-raw/.

Measured: validation again reported **0 problems and 0 warnings**. Independent reviews returned PASS for contract, determinism, simplicity and governance. The domain review remained INCONCLUSIVE because the calculation and tests do not yet exist. There were no findings.

Do you approve the revised plan? A plain **yes** approves it and will be recorded under your name; I’ll take anything else as a change or a question.

[exit code: 0]

### H3 yes

> Yes.

I’ll record your approval against the revised plan:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/plans/2026-11-27-household-poverty-depth.md" --reply 'Yes.' --project "<project>"`

Your approval is recorded. The [household poverty depth plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) is **approved**, including the boundary that no file under `data-raw/` is changed.

Use `/cg work` to start the planned slice.

[exit code: 0]

### The conformance record at the plan stage

plan P1 contract: PASS, independent review
  note: The planned test file does not yet exist, so its implementation could not be inspected.
plan P3 determinism: PASS, independent review
  note: The slice delivers a function and tests rather than a generated output file; the verification profile has no Run command. No project code or data was run or opened.
plan P6 simplicity: PASS, independent review
  note: The plan and decided intent were inspected; the implementation and its diff do not yet exist.
plan P10 domain-lenses: INCONCLUSIVE, independent review
  note: The plan states the household unit, weights and covered population. The calculation and tests do not yet exist, so no output was available to check against the general data lens.
plan P12 governance: PASS, independent review
  note: The planned test file does not yet exist, so its actual data access could not be inspected. No data file was opened.
missing: none
independent review: 5; self-review: 0


### W1 ask for the work

> $cg work Do the work of the approved plan.

I’m using the Compound GPID guide to check the approved plan and follow the project’s work process.

The approved plan has one slice left: an exported, documented poverty-gap function and its checks. I’ll proceed through that slice and stop if the work playbook’s stop rules apply.

Slice S1 may touch `R/poverty_gap.R`, its test file, `NAMESPACE`, and `man/poverty_gap.Rd`.

I’m also applying the R project guidance for the package and its tests. The existing working tree has uncommitted files, which I’ll preserve.

The planned check currently fails because its test file does not exist yet. I’ll create the planned tests first and run them against the existing package before implementing the function.

The planned check now passes all 37 expectations, and the slice guard is clean. The first run exposed a test path issue; I corrected the path to the help file and kept the planned assertions intact.

Reproducibility could not be checked: the project’s verification profile has no Run command. The required review is underway; its findings will be recorded for your decision.

The reviewers found that extreme but finite inputs can overflow the calculation. The plan identified overflow as a limitation; the review findings remain open for your decision, as the work playbook requires.

**Implemented and checked S1.** The new [poverty_gap()](<project>/R/poverty_gap.R) is exported and documented, with tests for the agreed arithmetic and input boundaries.

**Measured:** Check C1 passed 37 expectations, and the slice guard reported `guard: clean`. The [work report](<project>/.cg-docs/work-reports/2026-11-27-household-poverty-depth.md) is completed and validates without problems. The [plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) remains in progress pending your review; no slices remain.

The nine independent reviewers returned PASS for determinism, simplicity and shared language, and FLAG for the following:

- **Measured:** Extreme finite weights or negative welfare can cause arithmetic overflow and a non-finite or incorrect result. The domain reviewer classified this as P0. See the [weight probe](<project>/.cg-docs/evidence/2026-11-27-household-poverty-depth/0009-20261127T101243Z-ad-hoc.json) and [shortfall probe](<project>/.cg-docs/evidence/2026-11-27-household-poverty-depth/0010-20261127T101249Z-ad-hoc.json).
- **Inferred by the contract reviewer:** The plan needs an explicit wrong-result statement. [Finding](<project>/.cg-docs/evidence/2026-11-27-household-poverty-depth/0006-20261127T101157Z-ad-hoc.json)
- **Measured:** The verification profile lacks a Doctor command; the reviewer says environment fitness is therefore unestablished. It also lacks a Run command, so reproducibility was inconclusive. [Profile](<project>/.cg-docs/verification.md)
- **Inferred by reviewers:** The work report needs claim labels and evidence pointers, plus an AI-use statement before sign-off. [Report](<project>/.cg-docs/work-reports/2026-11-27-household-poverty-depth.md)

**Not checked:** Reproducibility through a project Run command, environment fitness through a Doctor command, and correctness for all possible inputs. Survey data was not opened. Pre-existing uncommitted changes were left in place.

Which findings would you like addressed? The work playbook leaves review findings for your decision before changes are made.

[exit code: 0]

### The conformance record at the review stage

review P1 contract: FLAG, independent review
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0006-20261127T101157Z-ad-hoc.json: The approved plan has no explicit statement of what a wrong result looks like. (P2; fix: add a concrete wrong-result statement through an approved plan amendment.)
  note: The initial search could not run because `rg` was unavailable; the recorded fallback search completed.
review P3 determinism: PASS, independent review
  note: Did not run the pipeline or repro because they write outputs. Left the unpinned environment alone because this is an R package with dependencies declared in DESCRIPTION; left the missing Run command alone because the outputs map names a function rather than a generated output file.
review P4 verification: FLAG, independent review
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0008-20261127T101224Z-ad-hoc.json: The verification profile has no doctor command, so the environment has not been established as fit for the check. (P2; fix: define and pass a read-only doctor check before relying on C1)
  note: C1 was rerun and exited successfully, but its result cannot be trusted under P4 until the doctor passes; behavior outside the contract was not checked.
review P5 adversary: FLAG, independent review
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0009-20261127T101243Z-ad-hoc.json: The calculation breaks R1 for finite positive weights whose sum overflows. (P2; fix: scale weights before computing the weighted average.)
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0010-20261127T101249Z-ad-hoc.json: The calculation breaks R1 for finite negative welfare and a finite positive line when their subtraction overflows. (P2; fix: compute the normalized shortfall without overflowing the intermediate subtraction.)
  note: Two probe rounds were run; no project data files were opened.
review P6 simplicity: PASS, independent review
  note: None.
review P7 claims: FLAG, independent review
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:39: The arithmetic and measurement claims lack claim labels and a pointer to evidence for the measured result. (P2; fix: label each claim and link the measurement to its evidence.)
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:40: The claims about the failed and passing checks lack labels and pointers to the relevant evidence records. (P2; fix: label the claims and link the corresponding records.)
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:48: The claims about pre-existing changes and the reproducibility check lack labels and evidence pointers. (P2; fix: label the claims and cite the supporting records, or identify uncertainty.)
  note: No defend-it brief was present among the listed project records.
review P10 domain-lenses: FLAG, independent review
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0011-20261127T101332Z-ad-hoc.json: Valid finite household weights can cause `poverty_gap()` to return a non-finite result through arithmetic overflow. (P0; fix: scale the weights before aggregation and guard against overflow in the shortfall calculation.)
  note: No survey data was opened.
review P11 language: PASS, independent review
  note: No shared-language conflict found in the inspected work.
review P12 governance: FLAG, independent review
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:46: The work has no AI-use statement identifying the tool, its contribution, and the reviewer. (P2; fix: add the AI-use statement before sign-off.)
  note: Dataset contents were not inspected because the kickoff did not authorize opening them.
missing: none
independent review: 9; self-review: 0

