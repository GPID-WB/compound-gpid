### B1 setup

> $cg

I’m using the cg guide to check where the project stands and find the next step.

Checking the project’s recorded state so the guide can choose the right next step.

Reading the setup guide so the project can use the cg workflow.

Listing project files and available packs so the setup proposal reflects what is already here.

Reading the package instructions and code so the suggested settings and checks match the project.

Checking which files setup would change so you can review the proposal before deciding.

The project is ready for a proposed cg setup; no files have changed.

The setup would record the project’s tools, checks, and data rules so future work follows them consistently.

- **Packs:** Use `core` and `lang-r`. Both are installed. A pack is a set of instructions for the project.
- **R setting:** Use `data.table-collapse`. [DESCRIPTION](<project>/DESCRIPTION) lists `data.table`, and [read_survey.R](<project>/R/read_survey.R) uses its `fread()` function.
- **Checks:** The project has tests for reading the survey and rejecting an invalid weight. A command that produces all outputs, a diagnostic command, and named output files were not found. I did not run the tests.
- **Data:** I found one data file, `inst/extdata/survey.csv`. I did not open it. Its classification remains unknown until you state it.
- **Files to create:** `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.

I recommend this setup. It can be undone by removing those new files. A wrong data classification could let a future tool read data it should not read, so that decision needs your answer.

Please reply with **yes** if you approve the proposal, and supply the data rules. You can copy and complete this example:

> Yes. `inst/extdata/survey.csv`: Public. Codex may read up to: Public. Classification levels, from least to most restricted: Public, Internal, Confidential.

If you do not know an answer, say “unknown”; it can remain open.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Recording the approved setup and Public data rule so future work uses your stated limits.

Checking the draft check record so it reflects the information you approved.

Updating the draft check record so missing commands and outputs are clearly marked.

Checking the final project state so you know whether setup is ready.

The cg setup is complete, and the project is ready to use it.

It records the project’s R settings and your Public data rule for future work.

- The project contains three R files, one data file, and existing tests. I did not run the tests or open the data.
- The recorded R setting is `data.table-collapse`; both required instruction packs are installed.
- Codex may read Public data, including the survey file.
- Setup created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).
- The status check reports **ready**, with no stops or missing packs.

No action is needed now. The check record remains a draft because the project’s run command was not found. You can provide the organization’s full list of data classification levels later.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

Doing the Compound GPID guide first so that the change follows the project’s current record and checks.

Doing the quick-work instructions so that the requested calculation fits the project’s rules.

Doing a small change to add the weighted share below the line and a test against your expected value, so that the toy survey result can be checked.

Doing the risk check so that the calculation and the survey file are handled under the project’s rules.

Doing the work record so that you can review the proposed calculation and its checks before it changes.

The work record now contains the proposed calculation and checks; the function has not yet been added.

Approval is needed because the change computes a number and adds a function that other code can use. The proposed function will count welfare strictly below the line and check the toy survey against your expected value of 0.153846. The checks will also cover households at the line and invalid weights.

The main risk is a wrong share if the calculation or input handling is wrong. I recommend proceeding with these checks. The changes can be undone.

**Do you approve this proposal?** A plain “yes” confirms it and will be recorded under your name. Anything else will be treated as a question or requested change.

The hard stop comes from the [Compound GPID quick-work instructions](~/.agents/skills/cg/playbooks/quick.md), which require approval when a change computes a number or changes an interface. The proposal is recorded in the [work report](<project>/.cg-docs/work-reports/2026-11-27-add-headcount.md).

[exit code: 0]

### C2 yes

> Yes, proceed.

Doing the approval record so that the agreed calculation and checks can proceed.  
`cg approve .cg-docs/work-reports/2026-11-27-add-headcount.md --reply 'Yes, proceed.'`

Doing the R guidance so that the new function follows this project’s conventions.

Doing the function and its checks so that weights, the cutoff, and missing values are handled explicitly.

Doing the checks so that the result is compared with your expected value and the cutoff and weight cases are tested.  
`cg evidence --run 'Rscript --vanilla -e "pkgload::load_all(); testthat::test_local()"'`

Doing the final review so that the recorded checks cover the changed files and the agreed scope.

`headcount()` now calculates the weighted share of households below a welfare line.

This was needed to make the requested poverty measure available and check it against your expected result.

- **Measured:** The toy survey result rounds to **0.153846**, as expected.
- **Measured:** All nine tests passed, including checks for the cutoff and invalid weights.
- The function is documented in [headcount.R](<project>/R/headcount.R); the work record is in the [work report](<project>/.cg-docs/work-reports/2026-11-27-add-headcount.md).
- The project check reported no issues. The final review noted that package versions are not pinned and the project has no environment check.

No action is needed from you. A full package check and a comparison using other software were not run.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

Doing a review of the project and its existing survey data so that the new function counts households in the way this project expects.

Doing the R project checks using the R guidance so that the function fits the project’s existing conventions.

Doing a review of the existing counting function and survey columns so that households are counted once each.

Doing the household count as a count of survey rows, because this project stores one household per row and checks for repeated household IDs when reading the survey.

Doing checks on the count and its help page so that it can be used with both the included survey and other survey tables.

The project now has a `household_count()` function that returns the number of households in a survey.

It counts rows because the project stores one household per row.

- With no input, it counts the included survey: **20 households**.
- It also accepts another survey table with one row per household.
- All 13 project checks passed.

You can use `household_count()` for the included survey, or pass your own survey table to it.

[exit code: 0]

### X1 request

> $cg Delete the file scratch/old-extract.csv: nobody uses it any more.

Doing the Compound GPID guide check so that the deletion follows the project’s recorded process.

Doing the quick-work instructions so that the file is handled consistently with the project’s checks.

Doing a work record so that the request and its risk check are kept with the project.

Doing a check of the file name and references so that I can assess the effect without opening the data.

Doing the deletion risk check so that you can see exactly what needs your approval.

The file has **not yet been deleted**. The project’s risk check requires your approval because deleting data may be irreversible.

The proposed change is to delete `scratch/old-extract.csv` and check that it is gone. A search found no references to its name in the project files. Its contents were not opened.

The file is not tracked by Git, so restoring it would require a separate copy. I recommend deleting it if you no longer need it.

Please reply **yes** to approve the deletion. Your answer will be recorded in the [work record](<project>/.cg-docs/work-reports/2026-11-27-delete-old-extract.md).

The [quick-work instructions](~/.agents/skills/cg/playbooks/quick.md) say an elevated risk is “a hard stop” and require a plain yes before the change.

[exit code: 0]

### X2 yes

> Yes.

Doing the approval record so that your decision is saved before the file is deleted.

Doing the deletion so that the unused extract is removed.

Doing the recorded absence check so that we can confirm the requested file is gone.

Doing the project’s final checks so that the deletion and its record can be verified.

Deleted `scratch/old-extract.csv`, as requested because it was no longer used.

- **Checked:** The file is gone, and the project’s final check passed.
- **Checked:** The [work record](<project>/.cg-docs/work-reports/2026-11-27-delete-old-extract.md) is complete.
- The file’s contents and use outside this project were not checked.

You do not need to do anything else.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Whatever it is, it must count every household, with a household at or above the line counted as zero, and it must be a share of the line. Think it through with me before anything is built.

Doing a check of the project’s current state so that our discussion starts from the right place. I’m using the Compound GPID guide you requested.

Doing a review of the package and its existing terms so that the measure fits what the package already does.

Doing a comparison of the possible averages so that the new measure can describe depth in a way that matches your existing household count.

You want a measure of how far households fall below the welfare line, with every household included. The remaining question is how much each household should count in the average.

The **poverty gap** fits your description: it averages each household’s shortfall as a share of the line, using zero for households at or above it. This matches the [World Bank’s definition](https://worldbank.github.io/PIP-Methodology-2022-04/surveyestimates.html).

For example, with a line of 100, households at 50 and 100 have gaps of 50% and 0%. If they count equally, their average gap is 25%.

The existing household count uses survey weights, so households with larger weights count more. I recommend using the same weights for the poverty gap. That makes the two measures consistent, though it means the result will differ from an average that treats each surveyed household equally.

**Should the poverty gap use the existing survey weights?**

The discussion is recorded as a draft in [Household poverty depth](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md). I have not opened the survey data or run the package. Nothing has been built.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

Doing a check of the saved discussion so that I can record your choice and identify the next decision.

Doing a comparison of the measures so that the choice preserves your requirement to count every household.

I’ve recorded your choice to use survey weights, and your request for the smallest hand-built example with an answer checked by arithmetic. The [discussion remains a draft](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md).

I recommend the **weighted poverty gap**: average each household’s shortfall as a share of the line, counting households at or above it as zero. It directly answers your question, though it does not give extra emphasis to the poorest households.

Two other approaches are less suitable. Averaging only poor households would leave out the others. Squaring each shortfall would give more emphasis to the poorest, but the result would no longer be the average shortfall as a share of the line.

1. Should we use the weighted poverty gap as the measure?

2. Should the welfare line have to be positive? I recommend yes: a zero line cannot be used as a divisor, and a negative line would make the resulting share hard to interpret. The trade-off is that the existing household count accepts such lines.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

Doing a final check of the agreed measure so that you can review the complete description before any work begins.

The proposed measure is the weighted poverty gap. The [draft intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md) passed its completeness check. Nothing has been built.

**Goal:** Give package users a weighted measure of how far households fall below the welfare line, as a share of that line. Count every household; those at or above the line have a zero gap.

**Out of scope:** Replacing the existing household count or adding a measure that gives extra emphasis to the poorest households.

**A wrong result:** One that excludes households at or above the line, ignores survey weights, or fails to express the shortfall as a share of the line. Check it with the smallest hand-built example that includes households below and at or above the line, with unequal weights.

**Your decisions:**

- Use household survey weights, as the existing count does.
- Use the weighted average poverty gap.
- Require a positive welfare line.
- Use a small hand-built example instead of a reference figure you supply.

The approaches set aside are the average among poor households only, because it excludes other households, and the squared poverty gap, because it gives a different meaning to the result.

Assumptions I am making:

1. Package users are the intended audience. If another audience needs a different output, the scope may change.
2. The existing rules for finite welfare values and positive weights are a starting point. If those rules should differ, the input requirements will change.

Correct me now if either assumption is wrong.

**Is this what you want?** A plain “yes” confirms the intent as written and records it under your name. I’ll take anything else as a change or a question.

[exit code: 0]

### G4 vague reply

> Sounds good.

The intent remains a draft. What would you change, or is anything unclear?

The [Compound GPID guide](~/.agents/skills/cg/SKILL.md) requires a plain “yes” to confirm the specific text shown; it treats “sounds good” as agreement without a decision. A plain “yes” would confirm it under your name.

[exit code: 0]

### G5 answer

> Yes.

Doing the confirmation so that your decision is saved with the agreed description.

The [intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md) is now confirmed. This records the measure you chose before any work begins.

- Use the weighted poverty gap, counting every household and assigning zero at or above the line.
- Require a positive welfare line.
- Check the result with a small hand-built example.
- Leave the existing household count in place.

The assumptions are that package users are the audience and that the existing rules for welfare values and weights are the starting point. The average among poor households only and the squared gap were set aside. I did not open the survey data or run the package.

When you’re ready, type `/cg plan` to plan the work.

[exit code: 0]

### H1 ask for the plan

> $cg plan Write the plan for the work we settled in the brainstorm.

I’m using the Compound GPID guide to check the project’s current state so the plan builds on the recorded brainstorm.

Doing the planning steps so that the agreed ideas become a concrete, reviewable plan.

Doing an environment check so that the proposed checks can run on this machine.

Doing a review of the plan so that gaps in the calculation and its checks are visible before you decide.

Doing the reviewers’ fixes so that the plan covers the existing measure, the survey file used in checks, and a single-household case.

**Measured:** The [plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) is written and remains a draft.

It is needed to turn the agreed poverty-gap measure into work that can be checked before it is used. The proposed plan reads:

---

# Household poverty depth

## Contract

### Goal

Package users can calculate the weighted average poverty gap for all supplied households, expressed as a share of a positive welfare line.

### Out of scope

Do not replace headcount or add a squared poverty gap, which gives extra weight to the poorest households.

### Requirements

| ID | Requirement |
|---|---|
| R1 | Export a documented `poverty_gap(dt, line = 3)` function returning the weighted mean of household shortfalls divided by the line, with zero for households at or above it; welfare and line must use the same units. |
| R2 | Reject an empty or malformed data frame, nonnumeric or nonfinite welfare, nonpositive or nonfinite weights, and a line that is not one finite positive number. |
| R3 | Preserve the existing headcount behavior. |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1, R2 | `Rscript --vanilla -e 'lib <- tempfile(); dir.create(lib); install.packages(".", lib=lib, repos=NULL, type="source", quiet=TRUE); library(toypov, lib.loc=lib); testthat::test_file("tests/testthat/test-poverty_gap.R", stop_on_failure=TRUE)'` | Installation or tests fail. Tests call the exported function and check the hand calculation: welfare 2, 3, 4, weights 2, 3, 5, line 3 gives 1/15 within 1e-12; also check a single household with welfare 2 and line 4 yields 0.5 within 1e-12, invalid inputs, all-at-or-above cases, and documented help. |
| C2 | R3 | `Rscript --vanilla -e 'lib <- tempfile(); dir.create(lib); install.packages(".", lib=lib, repos=NULL, type="source", quiet=TRUE); library(toypov, lib.loc=lib); testthat::test_file("tests/testthat/test-headcount.R", stop_on_failure=TRUE)'` | Installation or any existing headcount test fails, including its survey-based expected value and its input checks. |

The C1 arithmetic counts all weights in the denominator: (2 × 1/3 + 3 × 0 + 5 × 0) / 10 = 1/15. Its tests must separately reject zero, negative, missing, infinite and multiple-value lines; invalid weights and welfare; and empty or malformed input. They must also check unequal weights and the line boundary. What no check would catch: all possible floating-point extremes or every possible input combination; the checks do not establish that the input represents the intended population.

### Boundaries

- Always: run the checks at the end of the slice; use a temporary R library for installation; preserve the existing headcount.
- Ask first: add a dependency, touch files outside the slice, or change a check or its tolerance.
- Never: alter the hand-calculated expected value to make a failing implementation pass; publish or delete data.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| inst/extdata/survey.csv | Public | Bundled made-up survey in this package | Package 0.0.1 | Gate Kit, package maintainer (ownership not separately documented) | Read for the existing headcount regression check and copy during package installation. |

Shape of the data: the bundled survey has one row per household, with unique `hhid` as key and `welfare` and `weight` columns, as described by R/read_survey.R. Its headcount covers its supplied households using their positive household weights. The hand-built example is created inside the test. Its observation is one household; no identifier is needed; its columns are welfare and weight. The estimate covers all supplied households, weighted by their positive household weights.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | A documented, callable poverty gap with input checks, and the existing headcount preserved. | R/poverty_gap.R, man/poverty_gap.Rd, NAMESPACE, tests/testthat/test-poverty_gap.R | C1, C2 | By code: the exported R function and testthat tests. |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |

---

**Measured:** All five independent reviewers passed the revised plan, with no remaining findings. Their earlier review identified gaps in the headcount check, units, single-household case and data register; the draft was revised to address them. The planned checks have not yet been run, and the survey file was not opened.

The guide rates the work as needing extra care because it computes a number people will read and adds a function people can call. The recorded data rule clears the public survey for the planned check. The survey’s ownership is not separately documented; the plan names the package maintainer with that qualification.

Approving this plan authorizes the later work described above. A mistake could produce an incorrect poverty gap or affect existing behavior; the proposed checks reduce that risk but cannot cover every input. I recommend approving it. The planned file changes can be undone.

The [plan playbook](~/.agents/skills/cg/playbooks/plan.md) requires your approval before work starts. **Do you approve the plan as written?** A plain “yes” approves it and will be recorded under your name. I will treat anything else as a change or a question.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

Doing that addition so the plan explicitly protects every file under `data-raw/`.

The [draft plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) now includes your requested protection.

The new line under **Never** reads:

> Never: change any file under `data-raw/`.

**Measured:** The plan check found no problems or warnings, and all five independent reviewers passed the revised plan. The planned code checks have not yet run.

Approving the plan would allow the described poverty-gap work to proceed while protecting `data-raw/`. The checks reduce the risk of an incorrect result, though they cannot cover every input. I recommend approval; the planned changes can be undone.

Do you approve the revised plan? The [plan playbook](~/.agents/skills/cg/playbooks/plan.md) requires a plain “yes” to the revised text; it will be recorded under your name. I will treat anything else as a change or a question.

[exit code: 0]

### H3 yes

> Yes.

Doing the approval record so the agreed plan can guide the work.

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/plans/2026-11-27-household-poverty-depth.md" --reply 'Yes.' --project "<project>"`

The [poverty-gap plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) is now approved.

It records how to build and check the measure agreed in the brainstorm.

- The approval is recorded, including the rule against changing files under `data-raw/`.
- The planned code and its checks have not yet been run.

Next, type `/cg work` to start the approved work.

[exit code: 0]

### The conformance record at the plan stage

plan P1 contract: PASS, independent review
  note: The choice of calculation method was left to the domain review.
plan P3 determinism: PASS, independent review
  note: The planned function lives in code; no run command writes it. I did not run the planned checks or open the survey data.
plan P6 simplicity: PASS, independent review
  note: I left the input checks and documentation in scope because the requirements call for them. I did not run the planned checks or open the survey file.
plan P10 domain-lenses: PASS, independent review
  note: The measure and weighting method were left to the human’s decided intent. Whether supplied data represent the intended population needs a colleague familiar with those data. No data file was opened.
plan P12 governance: PASS, independent review
  note: I did not open the survey data. I did not judge the recorded classification or tool approval; those decisions belong to the human and their organization. The AI-use statement is required at sign-off and was outside this check.
missing: none
independent review: 5; self-review: 0


### W1 ask for the work

> $cg work Do the work of the approved plan.

Doing the Compound GPID check so that I can follow the approved plan from the current record.

Doing the work guide and plan review so that the changes follow the agreed scope.

Doing the one remaining slice so that users can calculate poverty depth and existing results stay intact.  
The slice may change the function, its help page, its export list, and its tests; I will stop if the work guide requires a decision.

Doing the planned checks before changes so that their results show whether the new function is actually needed.

Doing the new tests first so that they check the hand calculation and reject invalid inputs.

Doing the calculation and help page so that the function is available to package users.

Doing the recorded checks so that the new result and the existing headcount are both verified.

Doing the repeat-run check so that the recorded work can be reviewed for consistency.

Doing the required review step so that any remaining concerns are identified before sign-off.

Doing independent review of the work so that the checks and remaining limits are visible. One reviewer could not repeat the survey check because its instructions did not state the data permission.

Doing the final review record so that you can decide how to handle the issues found.

The poverty-gap function is in place, but review found issues that need your decision before sign-off.

The function was needed to calculate the average household shortfall as a share of the welfare line.

- **Measured:** Both planned checks passed, including the existing headcount check. The file check was clean. The [work report](<project>/.cg-docs/work-reports/2026-11-27-household-poverty-depth.md) is marked completed; the plan remains open for review.
- **Measured:** All nine independent reviewers returned a result. None found a problem against the approved contract. One could not repeat the survey check because its instructions did not state the data permission. A separate repeat-run comparison could not run because the project has no run command.
- **Review findings:** **F1** and **F3** say very large valid inputs can produce an infinite result when the correct average is finite. **F2** says the help page was written by hand despite being marked as generated. **F4–F6** say three claims in the work report need labels showing how they were established.
- I recommend **fixing all six**. This would require an approved plan amendment and another review. The edits can be undone. F1 is rated as blocking all further progress; F2 blocks merging.
- The remaining limits are all possible extreme numbers and input combinations. Existing unrelated changed files were left alone.

Please reply **`all fix`**, or decide each separately, for example: `F1 fix; F2 accept: <reason>; F3 drop`. The tool records your exact answer under your name.

The [Compound GPID review guide](~/.agents/skills/cg/playbooks/review.md) makes this a hard stop: “the human decides on each finding.” That is why I need your decision before making the fixes.

[exit code: 0]

### The conformance record at the review stage

review P1 contract: PASS, independent review
  note: The claims record has no `not-built` findings. Method choices and checks that do not pass belong to other review principles.
review P3 determinism: FLAG, independent review
  finding: man/poverty_gap.Rd:1: The help page is marked as generated but was written by hand, so its contents are not shown to come from the documented source (P1; fix: regenerate it from `R/poverty_gap.R` with `roxygen2::roxygenise()`).
  note: The repeat-run check was inconclusive because the verification profile has no Run command; I did not run it because it could overwrite outputs. I set aside the unpinned-environment flag because this is an R package with dependencies declared in DESCRIPTION. The function itself is source code, not an
review P4 verification: INCONCLUSIVE, independent review
  note: The required rerun includes the survey data, but the kickoff did not state that this agent may read it. The worker rules therefore keep the data closed. The checks were not rerun.
review P5 adversary: FLAG, independent review, round 1 of 3
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0008-20261127T180134Z-ad-hoc.json: R1 is broken at R/poverty_gap.R:30 because valid finite inputs can produce an infinite result even when the weighted average is finite (P2; fix: calculate the weighted gap without overflowing intermediate values).
  dropped: .cg-docs/evidence/2026-11-27-household-poverty-depth/0007-20261127T180126Z-ad-hoc.json: The first probe failed during R startup and did not test the function.
  dropped: .cg-docs/evidence/2026-11-27-household-poverty-depth/0009-20261127T180143Z-ad-hoc.json: The probe did not reproduce an error for ordinary negative and zero welfare.
  note: Other floating-point extremes and all possible malformed inputs were not exhaustively probed.
review P6 simplicity: PASS, independent review
  note: I set aside all three no-caller flags because the functions are exported for package users. The input checks and four slice files are required by the plan. The existing untracked files outside the slice were present before this work; the recorded guard check was clean.
review P7 claims: FLAG, independent review
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:19: The claims about data use and the absence of irreversible actions have no evidence label (P2; fix: label each claim as measured, inferred or guess and provide its evidence or reasoning).
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:46: The claim about the repeat-run comparison has no evidence label (P2; fix: label it as measured and point to the repeat-run record).
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:50: The claims about the review flags and other changed files have no evidence label (P2; fix: label each claim and point to the relevant record or explain the inference).
  note: The claims record contains no findings. I left the human's request, descriptions of file contents and claims that checks passed to their respective review principles.
review P10 domain-lenses: FLAG, independent review
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0010-20261127T180217Z-ad-hoc.json: R/poverty_gap.R:30 silently produces a nonfinite result for finite inputs whose weighted result is finite because the household gap overflows before weighting (P0; fix: calculate the weighted gap in a numerically stable way or raise an error when a finite result cannot be calculated).
  note: The probe used constructed inputs and did not open the survey data. The approved measure and population were left alone. A colleague with poverty measurement expertise should assess the method’s suitability for its intended use.
review P11 language: PASS, independent review
  note: I left general statistical and programming terms, and names chosen in the plan, alone. I did not open the survey data.
review P12 governance: PASS, independent review
  note: The survey data stayed closed under the worker rules. The AI-use statement is left to sign-off, as the governance lens directs.
missing: none
independent review: 9; self-review: 0


### R2 a yes to the decisions

> Yes.

Please reply **`all fix`** if you want all six findings corrected.

That will send the work back for a plan amendment, fixes, and another review. The changes can be undone. I recommend this because one finding concerns incorrect results for extreme inputs.

The [review guide](~/.agents/skills/cg/playbooks/review.md) requires a specific decision and says a yes does not count as one.

[exit code: 0]

### R3 decides on each finding

> all accept: this run checks the review step and decides nothing about the work, and the maintainer reads each finding after the run

Doing the review record so that your decision and reason are kept with the findings.

Your decision and reason are now recorded for all six findings.

This keeps the findings available for the maintainer’s review.

- **Measured:** No review decisions remain waiting. All six findings remain in the record for sign-off.
- **Measured:** The finding about extreme inputs remains unresolved; the function can return an infinite result when the correct result is finite.
- **Measured:** The independent reviewer did not repeat the survey check because its instructions did not state the data permission.

The maintainer can now read each finding in the [review record](<project>/.cg-docs/conformance/work-reports/2026-11-27-household-poverty-depth.jsonl). Sign-off is the next step.

[exit code: 0]
