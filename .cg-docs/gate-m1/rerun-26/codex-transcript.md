### B1 setup

> $cg

I’m using the cg guide to check where the project stands and find the right next step.

Checking the project’s recorded state so the guide can select the next step.

Reading the setup instructions so I can prepare the project for the guide.

Inspecting the project’s files and installed packs so the setup proposal matches the project.

Reading the package instructions and checks so the proposed settings reflect the existing code.

Checking the proposed file changes so you can review exactly what setup would write.

The project is ready for a setup proposal; no files have changed.

Setup will give the guide a record of the project’s settings, checks, and data rules.

- **Packs:** I recommend `core` and `lang-r`. Both are installed. A pack is a set of instructions for a kind of work.
- **R setting:** I recommend `data.table-collapse`. The package imports `data.table` and uses its `fread()` function. I found no use of `collapse`.
- **Checks:** I found tests for reading the survey and rejecting a non-positive weight. I found no project command for producing outputs or running a separate diagnostic check. The expected output is a table with 20 rows and the columns `hhid`, `welfare`, and `weight`. I did not run the tests or open the data.
- **Data:** There is one data file, `inst/extdata/survey.csv`. Its classification needs your decision.
- **Files setup would create:** `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.

I assumed the existing tests describe the intended result. Setup can be undone by removing those newly created files; an incorrect setting could cause the guide to use the wrong instructions.

**Do you approve this setup proposal?** Please also state the data rules you want recorded. For example: “Yes. `inst/extdata/` is Public; Codex may read Public data; our levels are Public, Internal, Confidential.” You can leave any answer open if you do not know it.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Recording the approved settings and Public data rule so the guide can use them.

Checking the verification record so it captures the checks you approved.

Checking the recorded state so we can confirm setup is complete.

The guide is now set up and reports the project as ready, with no stops.

This gives it the R settings and data permissions needed to guide future work.

- Recorded the survey as **Public** and Codex as allowed to read Public data.
- Enabled the installed `core` and `lang-r` packs, with the `data.table-collapse` setting.
- Created the configuration and draft checks in [.cg-docs](<project>/.cg-docs), plus [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).
- The project has three R files and one data file. No command to produce outputs or check the environment was found; tests were not run.

The checks remain a draft. The full list of your organization’s data classification levels also remains open.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

Doing the Compound GPID status check so that the change follows the project’s current work record.

Doing the quick-work instructions so that the function and its check follow the project’s rules.

Doing a work record so that the requested calculation and its checks have a place in the project.

Doing a review of the existing code and work record so that the new function fits the project.

Doing the requested weighted share using the survey’s household weights, with a check against 0.153846; the rest of the survey work stays as it is. A weighted share gives each household influence according to its survey weight.

Doing the risk check so that a new poverty estimate is reviewed before the calculation is changed.

Doing the risk record so that the requested calculation and the proposed checks are clear before any code changes.

The work record is ready; the function has not yet been added.

The risk check found that the change creates a number people may use, adds a function, and spans six files.

- The proposed function will calculate the share of household weight below the line.
- The checks will compare the toy survey result with **0.153846** and check another line and the boundary.
- A wrong calculation could give a misleading poverty estimate. The proposed changes can be undone.
- I recommend proceeding with these checks. The six-file change also needs a plan; `/cg plan` can prepare it.

Do you approve this contract? A plain “yes” confirms it and will be recorded under your name.

The [quick-work instructions](<~/.agents/skills/cg/playbooks/quick.md>) say that an elevated risk is “a hard stop” and that a change of this size needs a plan. The [work record](.cg-docs/work-reports/2026-11-27-add-headcount.md) contains the proposed contract.

[exit code: 0]

### C2 yes

> Yes, proceed.

Doing the approval record so that your decision is attached to the proposed work.

Doing the status check so that the next step follows the recorded decision.

Doing the project’s planning step so that the six-file change can be carried out with the required checks.

Your approval is recorded, and the function is still unchanged.

The project’s check found that the change spans six files, so its rules require a plan. The [planning instructions](<~/.agents/skills/cg/playbooks/plan.md>) say, “Write no plan from the conversation” when there is no recorded decision about the work.

Please start `/cg brainstorm` to record that decision. The next steps are then a plan and the implementation. The work remains open in the [work record](.cg-docs/work-reports/2026-11-27-add-headcount.md).

[exit code: 0]

### The approvals recorded in turn C2 yes

- 2026-11-27-add-headcount.566d604469794163.1.json: nothing wrong

### C3 yes

> Yes, proceed.

Doing the required decision record so that the plan can be prepared and the function can move forward.

Doing the decision record so that the calculation, its boundary, and the expected result are written down together.

The decision record is drafted; the function is still unchanged.

The requested result is the share of household weight below the line, with **0.153846** expected for the toy survey. I recommend calculating it by dividing the weight below the line by the total weight. This requires valid weights, which the function should check.

Should I use that calculation?

The [brainstorm instructions](<~/.agents/skills/cg/playbooks/brainstorm.md>) require this choice to be recorded before the plan. The draft is in the [decision record](.cg-docs/brainstorms/2026-11-27-add-headcount.md).

[exit code: 0]

### C4 takes the recommendation

> I take the option you recommend. If that changes what we decided before, make that change and show it to me.

Doing the decision record so that your chosen calculation is included in the proposed work.

Your choice matches the calculation we discussed; it does not change the earlier decision. The function has not yet been added.

The [decision record](.cg-docs/brainstorms/2026-11-27-add-headcount.md) now says:

- **Goal:** Add `headcount(dt, line = 3)` for package users and a testthat check.
- **Calculation:** Divide the household weight below the line by total household weight. Missing or invalid values must be rejected.
- **Wrong result:** The toy survey differs from **0.153846** at six decimal places, or a household exactly on the line is counted as below it.
- **Outside this work:** Changes to unrelated survey work.
- **Assumption:** The input has the same `welfare` and `weight` columns expected by the survey reader. If it does not, the function’s inputs would need to change.

The survey reader checks for positive welfare and weights and unique household IDs. The project has no recorded Run or Doctor command. The decision record passed its structure check; no survey data or calculation was checked in this step.

Does this record say what you want? A plain “yes” confirms it and will be recorded under your name; I will treat any other reply as a change or question.

The [brainstorm instructions](<~/.agents/skills/cg/playbooks/brainstorm.md>) require this confirmation before planning. Confirming records the decision; it can be changed later with a new confirmation.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

Doing a project check so that the new function fits the survey data and existing code.

Doing the R guidance check so that the function follows the project’s conventions.

Doing a review of the survey fields so that households are counted correctly.

Doing the count so that each row from the survey reader contributes one household.

Doing the checks so that the count works for both the example survey and an empty survey.

Added `count_households()` to return the number of households in a survey.

It counts survey rows because the survey reader provides one row per household. It does not use survey weights.

- The example survey returns **20**; an empty survey returns **0**.
- The checks passed.

To use it, run `count_households(read_survey())`.

[exit code: 0]

### X1 request

> $cg Delete the file scratch/old-extract.csv: nobody uses it any more.

Doing the Compound GPID state check so that I follow the right steps for deleting the file.

The headcount brainstorm is waiting for your decision; it does not hold up this deletion.

Doing the quick-work steps so that the deletion is checked and recorded.

Doing a review of the open work record so that this separate deletion does not disturb it.

The headcount work has its own open record. I’ll leave it alone and delete only `scratch/old-extract.csv`.

Doing a new work record so that this request has its own history.

Doing the request record and checking file references so that the risk of deletion is clear.

Doing the deletion agreement so that you can decide with the risk in view.

`scratch/old-extract.csv` is still in place.

Deleting it may be impossible to undo because it is not saved in the project’s Git history. I recommend deleting it as requested.

- Measured: the file exists, and a search found no references to its name in project files.
- Not checked: the file’s contents.
- The separate headcount work remains open.

The proposed agreement is: Delete `scratch/old-extract.csv` and leave other project files alone. Check that the file no longer exists and that this work did not change other project files. The check fails if the file remains or another project file was changed by this work.

Please reply **yes** to approve that agreement. A plain yes will be recorded under your name; anything else will be treated as a question or change to the agreement.

The [Compound GPID quick-work instructions](~/.agents/skills/cg/playbooks/quick.md) require this pause: “`tier: elevated`. This is a hard stop.” The check identified deletion of data as the reason.

[exit code: 0]

### X2 yes

> Yes.

Doing the approval record so that your decision is saved before the file is deleted.

Doing a file-state check before deletion so that I can check for unintended changes afterward.

Doing the deletion so that the unused extract is removed.

Doing the agreed checks so that the removal and other file changes are verified.

The first file-state comparison included the expected deletion and new check records. Doing a narrower comparison so that it checks the other files.

Doing the final review and record checks so that the result and its limits are clear.

Deleted `scratch/old-extract.csv` as requested because it was no longer needed.

- **Measured:** The file is gone, and the project’s final check found no issues.
- **Measured:** A check of other files’ listed status passed, though it cannot detect further edits to files that were already changed.
- **Not checked:** The deleted file’s contents.
- The [work record](<project>/.cg-docs/work-reports/2026-11-27-delete-old-extract.md) records the checks and their limits.

You do not need to do anything else for this deletion.

[exit code: 0]

### The approvals recorded in turn X2 yes

- 2026-11-27-delete-old-extract.38bab739ef158e33.1.json: the agent named .cg-docs/work-reports/2026-11-27-delete-old-extract.md nowhere in its output before the reply

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Whatever it is, it must count every household, with a household at or above the line counted as zero, and it must be a share of the line. Think it through with me before anything is built.

Doing the Compound GPID check so that our discussion starts from the project’s current state.

The earlier discussion about counting poor households is still a draft and awaits your decision. I’m checking the requested discussion route so that we can consider the new measure separately.

Doing a review of the package and the measure’s definition so that the options fit your requirements.

Recording the open choices so that we can return to them before anything is built.

The discussion is recorded as a [draft](<project>/.cg-docs/brainstorms/2026-11-27-poverty-gap.md); nothing has been built.

You want a measure of how far households fall below the line, counting every household. I’m still missing your choice of measure and how much each household should count.

- **Found:** The [World Bank’s poverty gap](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.NAGP) fits your description: average each household’s shortfall as a share of the line, using zero at or above the line.
- **Example:** With a line of 100 and two households at 50 and 100, their gaps are 50% and 0%. If they count equally, the average is 25%. This is an average across *all* households, not just the poor.
- **Trade-off:** This measure does not show how unequal the gaps are among poor households. Averaging only poor households would answer a different question and would exclude the others. Squaring the gaps would give more emphasis to deeper poverty, but would no longer give the average shortfall.
- **Found:** The package has a household weight—a number that determines how much a surveyed household counts. The separate draft for counting poor households proposes using those weights.
- I added the new terms to [GLOSSARY.md](<project>/GLOSSARY.md). I could not add it to the local Git exclusion list because that folder is read-only here, so please avoid committing it.

I recommend these two choices:

1. Use the **average poverty gap** described above. Its limitation is that it does not show differences in depth among poor households. Is that the measure you want?
2. Use the household weights when averaging, consistent with the separate draft. This means households with larger weights have more influence. Do you want to use them?

The earlier draft about counting poor households also remains open. I did not inspect the survey data or run the package.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

Recording your choices so that the discussion reflects the measure and example you want.

Both discussions remain drafts. I’m checking the package’s existing rules so that the next choices fit its inputs.

The draft now records your choices: use the weighted average poverty gap and check it with a small example whose answer follows from arithmetic.

That gives us the measure. Two choices remain about how the package presents it:

1. I recommend returning a **share**, such as `0.25` for 25%. This matches the separate draft for counting poor households, though users would need to multiply by 100 to display a percentage. Is that what you want?
2. I recommend a separate function where the caller can supply the poverty line, with a default of `3`, as in the separate draft. The risk is that `3` may not suit every survey. Is that what you want?

The [discussion record](<project>/.cg-docs/brainstorms/2026-11-27-poverty-gap.md) remains a draft. No survey data or package code was run, and nothing has been built. The earlier discussion about counting poor households remains open.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

Recording your choices so that the draft can be checked against what you want.

Both discussions remain drafts. I’m checking the poverty-gap draft so that you can review the full proposal before deciding.

The poverty-gap discussion is ready for your review; it remains a draft, and nothing has been built.

**Goal:** Give package users a separate function for the weighted average poverty gap. It will count every household, assign zero to households at or above the line, and return the result as a share of the line.

**Out of scope:** Building it during this discussion, changing the separate headcount work, or measuring inequality among poor households.

**A wrong result:** The answer excludes households at or above the line, gives them a nonzero gap, ignores household weights, or does not express the gap as a share. For example, with a line of 3, welfare values of 1.5 and 3, and weights of 1 and 3, the result should be **0.125**.

Your decisions recorded so far:

- Use the average poverty gap, including zero gaps.
- Use household weights in the average.
- Check it with the smallest practical hand-built example.
- Return a share, such as 0.25 for 25%.
- Let the caller supply the line, with a default of 3.

Assumption I am making:

1. The function uses the reader’s welfare and weight columns and a positive poverty line. If that is wrong, its inputs or input rules will need to change.

The [draft record](<project>/.cg-docs/brainstorms/2026-11-27-poverty-gap.md) passed its completeness check. The earlier headcount discussion is still open. I did not inspect survey data or run package code.

Is this what you want? A plain **yes** confirms this text and will be recorded under your name; I’ll treat anything else as a change or a question.

[exit code: 0]

### G4 vague reply

> Sounds good.

The proposal remains a draft. “Sounds good” does not confirm the text under the project’s approval rule.

Is anything unclear, or would you like to change anything? If the proposal is exactly what you want, please reply with a plain **yes**.

[exit code: 0]

### G5 answer

> Yes.

Recording your “Yes.” so that the agreed proposal is saved for the next step.

`cg approve .cg-docs/brainstorms/2026-11-27-poverty-gap.md --reply 'Yes.'`

The [poverty-gap proposal](<project>/.cg-docs/brainstorms/2026-11-27-poverty-gap.md) is confirmed.

This records what you want before any work begins:

- A weighted average gap, counting every household and giving those at or above the line a zero gap.
- A result expressed as a share, with a line supplied by the caller and a default of 3.
- A small hand-built example to check the arithmetic.

Nothing has been built. The separate discussion about counting poor households remains open. To continue, use `/cg plan`.

[exit code: 0]

### The approvals recorded in turn G5 answer

- 2026-11-27-poverty-gap.235cb9af48edae1f.1.json: nothing wrong

### H1 ask for the plan

> $cg plan Write the plan for the work we settled in the brainstorm.

Doing the state check so that the plan starts from the recorded brainstorm.

The headcount brainstorm is still a draft and awaits your decision. The poverty gap brainstorm is ready for planning.

Doing the plan checks so that I use the right settled work.

Doing the plan setup so that the agreed poverty gap measure has a written record.

Doing a review of the package files so that the checks match how people will use the measure.

Doing the R package guidance checks so that the plan fits the package and its tests.

Doing the written plan so that the calculation, its checks, and its limits can be reviewed together.

Doing the plan review so that gaps in the calculation or checks can be found before you decide.

The review found that the help check could pass without a help page. I’m correcting it so that a missing page causes a failure.

Doing a second review so that the corrected plan gets checked as it now reads.

The poverty gap plan is written and ready for your decision. It sets out the calculation and checks agreed in the brainstorm.

**Measured:** The plan passed its file checks. Five independent reviews passed on the current text. The work is classed as higher risk because it calculates a number and adds a function for others to use. The plan is a draft; the package has not been changed.

[Plan: Poverty gap](<project>/.cg-docs/plans/2026-11-27-poverty-gap.md)

## Plan

### Goal

Package users can call `poverty_gap(survey, line = 3)` to get the household-weighted average poverty gap as a share of the line, including every household.

### Out of scope

Changing the separate headcount work, measuring inequality among poor households, or changing the survey reader. The toy survey is not needed for the hand-built checks.

### Requirements

| ID | Requirement |
|---|---|
| R1 | Export and document a separate `poverty_gap` function with a line argument defaulting to 3. |
| R2 | Return the weighted mean of each household's shortfall divided by the line, using zero for households at or above it. |
| R3 | Reject a nonpositive or nonfinite line and missing, nonfinite, or nonpositive welfare or weights, and an empty survey. |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1, R2, R3 | `Rscript --vanilla -e 'devtools::test(filter = "^poverty_gap$")'` | The test process exits nonzero: the exported function or its default fails; a hand-built case differs from 0.125 by more than 1e-12; a household on or above the line is given a positive gap; a changed line gives an incorrect result; or invalid inputs do not raise errors. |
| C2 | R1 | `Rscript --vanilla -e 'devtools::load_all(quiet = TRUE); stopifnot("poverty_gap" %in% getNamespaceExports("toypov"), length(utils::help("poverty_gap", package = "toypov")) > 0)'` | The process exits nonzero because the function is not exported or its help topic cannot be found. |

The test for C1 uses welfare 1.5 and 3, weights 1 and 3, and line 3: (1 × 0.5 + 3 × 0) / 4 = 0.125. It also checks welfare above the line, a caller-supplied line, and cases that distinguish weighted from unweighted means. Expected values are hand calculated, with tolerance 1e-12. The test calls the exported function as a package user does. What no check would catch: every possible numerical edge case or an incorrect survey weight supplied by a caller.

### Boundaries

- **Always:** use hand-built examples, run the slice's checks, and document the return value, valid inputs, and that welfare and the line must use the same units.
- **Ask first:** add a dependency, touch a file outside the slice, or change a check or its tolerance.
- **Never:** alter the headcount work, open the survey data, publish, or weaken a check to make it pass.

### Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| none | none | none | none | none | none |

Shape of the data: no dataset is read or produced. The function accepts one row per household, with welfare and household weight columns; the reader expects unique `hhid`. The estimate covers all households supplied by the caller and weights each household by its supplied weight. Checks construct small examples in code.

### Slice

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | The documented, exported poverty gap for a supplied survey, with arithmetic and input checks. | R/poverty_gap.R, tests/testthat/test-poverty_gap.R, NAMESPACE, man/poverty_gap.Rd | C1, C2 | By code: the function and testthat checks. |

### Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |

The five independent reviews passed: the contract, calculation process, simplicity, domain considerations, and data handling. An earlier review found two issues—the help check could pass without a help page, and the plan did not state that welfare and the line need matching units. Both were corrected before the second review.

**Inferred risk:** The checks cannot catch every numerical edge case or a wrong weight supplied by a caller. When applying the function, someone familiar with the survey should confirm that welfare and the line use the same units. The planned changes can be undone.

I recommend approving the plan. **Do you approve it as written?** A plain “yes” approves the plan and is recorded under your name; I will take anything else as a change or a question. The [plan playbook](~/.agents/skills/cg/playbooks/plan.md) requires this separate approval before implementation.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

Doing that edit so the plan protects every file under `data-raw/`.

The poverty gap plan and the separate headcount brainstorm still await your decisions. Doing the required review of the edited plan so that the new boundary is checked.

The [plan](<project>/.cg-docs/plans/2026-11-27-poverty-gap.md) now includes your requested protection:

> Never: change any file under `data-raw/`.

**Measured:** All five independent reviews passed after the edit. The plan remains a draft. Its checks cannot catch every numerical edge case or an incorrect weight supplied by a caller.

I recommend approving the updated plan. It sets out the work; the proposed changes can be undone.

Do you approve the plan with this addition? A plain “yes” approves it and is recorded under your name. I’ll take anything else as a change or a question.

The [plan playbook](~/.agents/skills/cg/playbooks/plan.md) requires a new yes after a correction because your reply also requested a change.

[exit code: 0]

### H3 yes

> Yes.

Doing the approval record so that your yes is saved against the exact plan.

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/plans/2026-11-27-poverty-gap.md" --reply 'Yes.' --project "<project>"`

**Measured:** The [poverty gap plan](<project>/.cg-docs/plans/2026-11-27-poverty-gap.md) is approved, including the rule that no file under `data-raw/` is changed.

The approval records your decision against the plan. When you’re ready to start the work, type `/cg work`.

[exit code: 0]

### The approvals recorded in turn H3 yes

- 2026-11-27-poverty-gap.a6e9dd280683927e.1.json: nothing wrong

### The conformance record at the plan stage

plan P1 contract: PASS, independent review
  note: The choice of measure and weighting method belongs to P10 and was left to that verifier.
plan P3 determinism: PASS, independent review
  note: The planned function lives in code; no Run command writes it. The arithmetic example is a reference for a test, not a reported result copied from an output.
plan P6 simplicity: PASS, independent review
  note: Left the separate function and input checks in place because the contract requires them.
plan P10 domain-lenses: PASS, independent review
  note: The human chose the measure and weighting method, so I left them alone. Someone familiar with each survey should confirm that its welfare values and poverty line use the same units.
plan P12 governance: PASS, independent review
  note: The plan uses hand-built examples and keeps the survey data closed. The AI-use statement is left for sign-off, as the governance lens directs.
missing: none
independent review: 5; self-review: 0


### W1 ask for the work

> $cg work Do the work of the approved plan.

Doing the status check so that I follow the approved plan and the project’s current record. I’m using the `cg` guide for this work.

The separate headcount idea is waiting for your decision. Doing the work status check so that I use the steps for the approved plan.

Doing a review of the plan and existing records so that I can start at the right slice.

Doing the work record so that the plan’s checks and results have a lasting home.

Doing the one remaining slice so that package users can calculate the poverty gap; it may touch the four files named in the plan.  
Doing its checks before and after the change; I will stop if the plan’s stop rules require a decision.

Doing the first checks so that I can see whether they detect the missing calculation.

The work record is open, but the poverty gap calculation has not been added.

The first check could not test the calculation: it stopped because the planned test file does not exist yet. The work guide requires a plan change when a first check fails without testing the change.

- **Measured:** Check C1 is not verified. C2 has not run.
- **Measured:** The [plan](<project>/.cg-docs/plans/2026-11-27-poverty-gap.md) is approved; the [work record](<project>/.cg-docs/work-reports/2026-11-27-poverty-gap.md) is in progress.
- **Measured:** The single planned slice remains. No package files were changed.
- **Measured:** The separate headcount idea is still waiting for your decision.

Would you like `/cg plan` to amend the plan so the test file is written before the first check? I recommend that change so the check can show whether the calculation is missing. The plan amendment can be undone; the calculation would remain unstarted until you approve the revised plan.

[exit code: 0]

### W2 go on

> Go on with the plan as it is approved. I have nothing to add.

Doing the planned test first so that the check can exercise the missing calculation.

Doing one correction to the check record so that it reflects the failure shown on screen.

The planned test file is now in place, but the poverty gap function is not yet implemented.

**Measured:** The test found that the function is missing, but the planned check still reported a successful exit. That means the check cannot reliably signal failure as the plan requires. I corrected the work record to say **not verified**. The second check also found the function missing.

The [plan](<project>/.cg-docs/plans/2026-11-27-poverty-gap.md) remains approved, and the [work record](<project>/.cg-docs/work-reports/2026-11-27-poverty-gap.md) remains in progress. The calculation and final checks are still to do.

Would you like `/cg plan` to fix the check command? I recommend this because the present command can report success when a test fails. The plan change can be undone; the work can then continue after you approve it. The [work guide](~/.agents/skills/cg/playbooks/work.md) requires a stop when a check is wrong.

[exit code: 0]

### W3 go on

> Go on with the plan as it is approved. I have nothing to add.

Doing the calculation and its help page so that the planned examples can run. I’ll read the test results as well as the exit signal, since the signal alone missed a failure.

Doing both planned checks so that the arithmetic, input rules and help page are checked.

Doing a check of how R finds the help page so that I can identify why the second check failed.

The poverty gap function, its help page and its test file are now in place, but the work is not yet complete.

**Measured:** The arithmetic and input checks pass. The help-page check fails because R cannot find help for either the new function or the existing `count_households` function when the package is loaded in this way.

- The [plan](<project>/.cg-docs/plans/2026-11-27-poverty-gap.md) remains approved; the [work record](<project>/.cg-docs/work-reports/2026-11-27-poverty-gap.md) remains in progress.
- The final whole-change check and review have not run.
- The separate headcount idea remains untouched and awaits your decision.

Would you like `/cg plan` to amend the help-page check? I recommend it because the current check cannot find an existing help page either. The amendment can be undone; it would let the remaining work proceed once approved.

[exit code: 0]

### W4 go on

> Go on with the plan as it is approved. I have nothing to add.

The work remains incomplete because the approved help-page check fails, even for an existing function’s help page.

**Measured:** The poverty gap calculation passes its arithmetic and input checks. Its help page exists, but the planned command cannot find it. The final whole-change check and review have not run.

The [work record](<project>/.cg-docs/work-reports/2026-11-27-poverty-gap.md) remains in progress. I cannot finish under the plan as written without changing the check or touching files outside the approved slice; the plan requires a decision before either change.

[exit code: 0]

### W5 asks for the amendment

> Make the amendment you propose to the plan, show it to me, and ask me to approve it.

Doing a review of the plan steps so that I can prepare the smallest amendment and show you exactly what would change.

Doing a small trial of the replacement checks so that the proposed amendment can be reviewed with evidence.

Doing the written amendment so that you can approve the exact replacement checks before work continues.

I added the proposed amendment to the [poverty gap plan](<project>/.cg-docs/plans/2026-11-27-poverty-gap.md).

It changes two checks:

- **C1:** Make a failed test give a failure signal. The test results and tolerance stay the same.
- **C2:** Check the help file directly and confirm the function is available to users.

I tried both replacement commands; they pass on the current files. The second check would not test the help index of an installed package. The amendment can be undone.

Do you approve this amendment? I recommend approving it so the remaining work can be checked reliably. A plain “yes” approves the amendment as shown.

[exit code: 0]

### W6 yes at a stop

> Yes.

Doing the approval record so that the revised checks can be used for the remaining work.

Doing the required amendment entry so that the approval tool can recognize the change you approved.

Doing the recorded checks so that the approved amendment is applied to the work.

Your approval of the amendment is recorded in the [plan](<project>/.cg-docs/plans/2026-11-27-poverty-gap.md).

**Measured:** The check tool still ran the original command from the plan’s table, even though the approved amendment gives its replacement. The work therefore remains in progress.

May I put the two approved replacement commands directly into that table? I recommend it so the tool can run them. This changes where the approved commands appear, and it can be undone. The tool requires a fresh approval after the plan text changes.

[exit code: 0]

### The approvals recorded in turn W6 yes at a stop

- 2026-11-27-poverty-gap.60c216447e1ee427.2.json: the text it approves was not in .cg-docs/plans/2026-11-27-poverty-gap.md when the human replied

### W7 takes the recommendation

> I take the option you recommend. If that changes what we decided before, make that change and show it to me.

Doing the table update so that the check tool can read the commands you chose.

The [plan’s check table](<project>/.cg-docs/plans/2026-11-27-poverty-gap.md) now contains the two commands you approved.

The decision is unchanged: C1 signals a failed test, and C2 checks the source help file and whether the function is available to users. The table now also states C2’s updated failure conditions. This edit can be undone.

Do you approve the plan as updated? I recommend approval so the tool can record the checks. The approval tool requires a fresh “yes” because the plan text changed.

[exit code: 0]

### W8 yes to the amendment

> Yes.

Doing the approval record so that the updated checks can be run.

Doing the required dated note so that the approval tool can record your answer.

Doing the two approved checks so that their results are recorded against the updated plan.

Doing the whole-slice check so that unexpected changes are identified before review.

Doing the repeatability check so that the work record shows whether the project can reproduce its outputs.

Doing the work record so that the passed checks and the limits of the repeatability check are clear.

Doing the review setup so that the completed checks and any remaining concerns are examined.

Doing the independent review so that the calculation and its record are checked from several angles.

Doing the remaining review checks so that any concerns can be presented together.

The poverty gap calculation is in place, and both approved checks passed. Independent review found seven items that need your decision before sign-off.

**Measured:** The review found no departures from the approved plan. It found these concerns about the project’s checking standards:

- **F1:** The project lacks a check that the R setup is fit to run. **Recommend fix.**
- **F2:** The work record does not explain how its risk statements are known. **Recommend fix.**
- **F3:** The record does not show evidence for saying no output moved. **Recommend fix.**
- **F4:** The record does not show the reasoning behind the hand calculation. **Recommend fix.**
- **F5:** The record does not point to the result showing that repeatability could not be established. **Recommend fix.**
- **F6:** The record does not show evidence for its statement about the separate headcount work. **Recommend fix.**
- **F7:** An existing headcount test reads survey data that the poverty gap plan does not list. **Recommend drop:** the approved poverty gap checks select only the new test, and the headcount work was outside this plan.

Fixing F1–F6 would send the work back for an approved plan change and another review. Dropping F7 would leave that separate test unchanged. These decisions can be revisited through a further plan change.

Please reply `F1 fix; F2 fix; F3 fix; F4 fix; F5 fix; F6 fix; F7 drop`, or give a different decision for each. The review tool records your exact reply. The [review guide](~/.agents/skills/cg/playbooks/review.md) requires your decision on each finding before the work continues.

[exit code: 0]

### The approvals recorded in turn W8 yes to the amendment

- 2026-11-27-poverty-gap.85a8402582034117.3.json: the text it approves was not in .cg-docs/plans/2026-11-27-poverty-gap.md when the human replied

### The conformance record at the review stage

review P1 contract: PASS, independent review
  note: Left method choices and details the approved plan leaves open to other review principles.
review P3 determinism: PASS, independent review
  note: The reproducibility record flagged an unpinned environment and a missing Run command. I set both aside because this is an R package that declares its dependencies, and the mapped survey table is returned by a function rather than written as an output file. The reported hand calculation is not a valu
review P4 verification: FLAG, independent review
  finding: .cg-docs/verification.md:23: The environment check is missing, so the passing checks cannot establish that the environment is fit to run. (P1; fix: add and pass a read-only environment check before trusting the results)
  note: Both approved checks reran with exit code 0. Installed-package help, every numerical edge case, and incorrect caller-supplied weights were not checked, as the contract does not require those checks.
review P5 adversary: PASS, independent review, round 1 of 3
  dropped: .cg-docs/evidence/2026-11-27-poverty-gap/0015-20261127T220632Z-ad-hoc.json: The first probe stopped during R startup; the corrected probe passed.
  dropped: .cg-docs/evidence/2026-11-27-poverty-gap/0016-20261127T220638Z-ad-hoc.json: The weighted result, boundary, and large-weight probes showed no fault.
  dropped: .cg-docs/evidence/2026-11-27-poverty-gap/0017-20261127T220645Z-ad-hoc.json: The invalid welfare and weight probes showed no fault.
  note: I did not probe every possible numerical edge case or inputs larger than memory.
review P6 simplicity: PASS, independent review
  note: The scope record lists `count_households` and `poverty_gap` as having no callers outside their tests. Both are exported for package users, so I set those entries aside. The separate headcount files appear in the untracked files; the available record does not establish that this work changed them.
review P7 claims: FLAG, independent review
  finding: .cg-docs/work-reports/2026-11-27-poverty-gap.md:19: The risk claims are not labelled by how they are known (P1; fix: label each claim and give its evidence or reasoning).
  finding: .cg-docs/work-reports/2026-11-27-poverty-gap.md:41: The claim that no output moved has no label or evidence pointer (P1; fix: label the claim and point to its evidence).
  finding: .cg-docs/work-reports/2026-11-27-poverty-gap.md:42: The hand-calculation claim has no label or reasoning beside it (P1; fix: label it inferred and show its reasoning).
  finding: .cg-docs/work-reports/2026-11-27-poverty-gap.md:46: The claim about repeatability has no label or pointer to the record, which reports an inconclusive result (P1; fix: label it measured and cite that record).
  finding: .cg-docs/work-reports/2026-11-27-poverty-gap.md:50: The claim that the separate work remains open and was not changed has no label or evidence pointer (P1; fix: label the claim and give its evidence or reasoning).
  note: The claims record had no findings. Claims about check results were left to P4; the approved plan and plain statements of file contents were left alone.
review P10 domain-lenses: PASS, independent review
  note: The approved choice of poverty measure was left to the human. A colleague familiar with poverty measurement should confirm that the household weights and measure suit the intended use.
review P11 language: PASS, independent review
  note: Left general statistical and programming terms alone, as directed. The conversation in which terms may have been settled was not available to inspect.
review P12 governance: FLAG, independent review
  finding: tests/testthat/test-count_households.R:2: This test reads the package’s survey dataset, but the plan’s data register does not list it. (P1; fix: add the dataset and its details to the register through an amendment approved by the human)
  note: Data files were not opened. The AI-use statement belongs to sign-off and was left for that stage.
missing: none
independent review: 9; self-review: 0


### R2 a yes to the decisions

> Yes.

The review decisions are still waiting. “Yes” does not say what to do with each finding in the form the review tool accepts.

Please reply:

`F1 fix; F2 fix; F3 fix; F4 fix; F5 fix; F6 fix; F7 drop`

That follows my recommendation: improve the checks and record, and leave the separate headcount test alone. You can give different decisions if you prefer.

The [review guide](~/.agents/skills/cg/playbooks/review.md) says the tool takes the specific decisions, so I need that reply before recording them.

[exit code: 0]

### R3 decides on each finding

> all accept: this run checks the review step and decides nothing about the work, and the maintainer reads each finding after the run

Doing the decision record so that your reason stays with the review findings.

Your decision on all seven review findings is recorded, with your reason preserved for the maintainer.

**Measured:** Both poverty gap checks passed, and the review has no decisions waiting. The findings remain in the [review record](<project>/.cg-docs/approvals/2026-11-27-poverty-gap.route.1.json) for sign-off. The maintainer can read each finding after the run, as you requested.

[exit code: 0]

### The approvals recorded in turn R3 decides on each finding

- 2026-11-27-poverty-gap.route.1.json: nothing wrong
