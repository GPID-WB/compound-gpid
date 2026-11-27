### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and open the next playbook.

The project is an R package, and the R pack is installed. I’m checking its existing code and checks to prepare the setup proposal; I’ll leave the data file unopened.

**Measured:** The project is an R package with four `.R` files, one `.Rd` file, one `.csv` file, and three files without extensions. The expected packs are `core` and `lang-r`; both are installed.

I recommend the `lang-r.r-syntax=data.table-collapse` setting. [DESCRIPTION](<project>/DESCRIPTION) imports data.table, and [read_survey.R](<project>/R/read_survey.R) uses `fread()`. This is also the pack’s default.

The draft verification profile is:

- **Run command:** not found.
- **Doctor command:** not found. The package has testthat tests, but no project verification command was identified.
- **Output:** `read_survey()` returns a data.table with one row per household. Existing tests check its columns, row count for the bundled survey, and rejection of a non-positive weight. These checks were read, not run.

There is one data file, `inst/extdata/survey.csv`. Its classification is unknown; I did not open it. I assumed the existing data.table usage reflects the intended R dialect.

The setup dry run says it would create:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

Do you approve this setup proposal? Please also state the data rules you know. For example: **“Yes. `inst/extdata/` = Public; Codex may read through Public; levels: Public, Internal, Restricted.”** You may leave any unknown classification or level open.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the approved packs, R setting, and Public data rule, then check the resulting setup status. The organization’s full classification order remains open.

Setup is complete. **Measured status:** `phase: ready`, `stops: none`, with both expected packs installed and `lang-r.r-syntax=data.table-collapse`.

The configuration records `inst/extdata/survey.csv` as Public and Codex as approved to read Public data. The organization’s full classification order remains open.

Created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The verification profile remains a draft: no Run or Doctor command was found, and the existing tests were not run. The project contains four R files and one data file; the data file was not opened.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its next step.

I’ll add `headcount()` and a test of the requested weighted share. I’ll leave unrelated behavior alone.

**Approval is needed before implementation.** The Compound GPID risk check classified the work as elevated because it computes a number and adds a public function interface. It confirmed that the toy survey is cleared for Codex.

The proposed contract is:

> Add `headcount(dt, line = 3)` to compute the weighted share of households whose welfare is strictly below the line, document and export it, and add a testthat check. Leave unrelated behavior and data unchanged. Run the package tests; failure means any test fails, including if the toy survey result differs from 0.153846 by more than 0.0000005. Also run the Compound GPID guard and validate the work report; failure means either reports a FAIL.

Please reply **yes** to approve this contract, or suggest a change or ask a question. A plain yes will be recorded under your name. The contract is in the [work report](<project>/.cg-docs/work-reports/2026-11-26-add-weighted-headcount.md).

The hard stop comes from the [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md), which says an elevated tier “is a hard stop” and requires approval of the contract before changes proceed.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll record your approval and continue with the implementation and checks.

The open report is waiting for your approval of the numeric calculation and public interface. I’ll record your reply against that contract.

I’m applying the R package and testing guidance alongside the project’s configured data.table conventions.

The approval is recorded. I’ve added checks for the requested survey result, the strict cutoff, and invalid input; I’ll run them before adding the function.

The tests now pass, including the toy survey comparison and cutoff check. I’ll finish the recorded verification and review the change against the guide’s principles.

Implemented and exported `headcount(dt, line = 3)`. It returns the weighted share of households with welfare strictly below the line and rejects missing or invalid inputs. The function, documentation, and tests are in [R/headcount.R](<project>/R/headcount.R), [man/headcount.Rd](<project>/man/headcount.Rd), and [test-headcount.R](<project>/tests/testthat/test-headcount.R).

**Measured:** the toy survey result is **0.1538461538**, within the agreed tolerance of your expected 0.153846.

- **Verified:** `Rscript --vanilla -e "testthat::test_local()"` passed all eight expectations. The new tests failed before the function was added.
- **Verified:** Compound GPID guard reported `clean`, and report validation found no problems.
- **Self-review:** P6 passed. P3 and P4 were flagged because the project has no environment lockfile or Doctor command; the review was not independent.

The [work report](<project>/.cg-docs/work-reports/2026-11-26-add-weighted-headcount.md) records the checks. The project’s existing R startup configuration errors without `--vanilla`; I left it unchanged. `air` was unavailable, so formatting was inspected manually.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll inspect the project’s survey data and existing conventions, then add the function and verify its behavior.

I’m using the R package development guidance to match the existing API and documentation. The project has existing changes, so I’ll preserve them while inspecting the survey structure.

The survey uses one row per household, so the function will return an unweighted row count. I’ve added coverage for the bundled survey, an empty survey, and invalid input; I’m checking the package now.

Added [household_count()](<project>/R/household_count.R), which counts rows in a survey data frame, assuming one row per household. The count is unweighted.

The bundled survey returns **20 households**. All 12 package tests pass.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check the project’s state and work through the choice of measure with you before anything is built.

**My understanding:** you want package users to see how far below the line poor households are, alongside how many are below it; I’m still missing the question the new number should answer and who will use it.

Measured from the package code: `headcount()` already returns the weighted share of households below the line. Two related measures answer different questions:

- The **average shortfall among poor households** says how far below the line they are, as a percentage of the line.
- The **poverty gap index** averages that proportional shortfall across all households, counting nonpoor households as zero. It combines how common and how deep poverty is. The [World Bank’s explanation](https://thedocs.worldbank.org/en/doc/775821593194314687-0050022020/original/lecture14final.pdf) distinguishes the two.

For example, if one in four equally weighted households is poor and that household is 40% below the line, the average shortfall among the poor is **40%**, while the poverty gap index is **10%**.

1. I recommend starting with the **average shortfall among poor households**, because it directly answers your question alongside headcount. The trade-off is that it is undefined when no households are poor and does not itself reflect how many are poor. Is that the question you want to answer, or would you prefer the population-wide poverty gap index?
2. Who will use the result? My working assumption is package users interpreting household poverty alongside headcount; a specific audience or reporting requirement could change what the output needs to communicate.

I recorded the open questions in the [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md). I have not opened the survey data or run the package.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record those choices and the arithmetic example requirement, then narrow the remaining measure and scope decisions.

The [poverty depth intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) is **draft and waiting on your decisions**.

You chose the average proportional shortfall among poor households, for package users interpreting it alongside headcount. You also asked for a minimal hand-built example with an answer established by arithmetic. I’ve recorded those choices.

The remaining details are how to average households and what to return when none is poor:

1. I recommend using the existing **household weights**, consistent with `headcount()`. This means the result reflects the supplied weights rather than treating every surveyed household equally. Do you agree?
2. I recommend returning **`NA` when no household is poor**, because an average over an empty group is undefined. Callers would need to handle that result. Do you agree?

**Measured:** the existing headcount uses weights and treats welfare strictly below the line as poor. **Inferred:** matching those conventions will make the two measures easier to interpret together. I have not opened the survey data or run the package.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record the two choices and check the complete draft intent for any remaining gaps before showing it to you for confirmation.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) is **draft and waiting for your confirmation**. Its structure check reports zero problems and zero warnings.

**Goal:** Help package users interpreting household poverty alongside headcount see the average proportional shortfall among poor households.

**Out of scope:** Adding the population-wide poverty gap index or an absolute shortfall measure, or changing the existing headcount.

**A wrong result:** A result that includes nonpoor households in the denominator, ignores household weights, or gives a defined average when no household is poor. For a small arithmetic check, at a line of 4, households with welfare 2 and 3 and weights 1 and 3 have an average shortfall of `(1 × 0.5 + 3 × 0.25) / 4 = 0.3125`.

**Your decisions:**

- Measure the average proportional shortfall among poor households.
- Use it alongside headcount for package users interpreting household poverty.
- Use the existing household weights.
- Return `NA` when no household is poor.
- Use a small hand-built example where a reference value is needed.

The population-wide poverty gap index and average absolute shortfall were considered and set aside: the former combines prevalence and depth; the latter is harder to compare across poverty lines or welfare units.

**Assumptions I am making:**

1. Use the existing headcount convention: welfare strictly below the line is poor, and the default line is 3. If wrong, the cutoff or default must change.
2. Return a proportion, consistent with headcount; multiply by 100 to express it as a percentage. If wrong, the output scale must change.
3. Require a positive poverty line so the proportional shortfall is meaningful. If wrong, the input contract needs reconsideration.

Correct me now. I have not opened the survey data or run the package.

Is this intent what you want? A plain **yes** confirms it and will be recorded under your name; I’ll treat anything else as a change or question.

[exit code: 0]

### G4 vague reply

> Sounds good.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) remains a draft. The [Compound GPID guide](~/.agents/skills/cg/SKILL.md) requires a plain yes to confirm the text; its [confirmation rules](~/.agents/skills/cg/grilling.md) list “sounds good” as agreement that does not record that confirmation.

Would you like to confirm the intent as shown with a plain **yes**, or is there anything you would change?

[exit code: 0]

### G5 answer

> Yes.

I’ll record your “Yes.” against the intent using the guide’s approval command.

Your confirmation is recorded. The [intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) is decided: use the weighted average proportional shortfall among poor households alongside headcount, return `NA` when none are poor, and check a small hand-built example by arithmetic.

The brainstorm is complete; nothing has been built. You can use `/cg plan` to plan the work, or `/cg` with a first small change.

[exit code: 0]

### H1 ask for the plan

> $cg plan Write the plan for the work we settled in the brainstorm.

I’ll use the Compound GPID guide to check the project’s state and follow the planning playbook.

The recorded intent is decided: it specifies a weighted average among poor households and an `NA` result when none are poor. I’ll check the package interface and verification commands before writing the plan.

The plan can use hand-built test inputs, so the planned checks need not open the bundled survey. The risk check identifies a new numerical result and a new public interface.

The draft plan is in [2026-11-26-poverty-depth-measure.md](<project>/.cg-docs/plans/2026-11-26-poverty-depth-measure.md). **Measured:** validation reported zero problems and zero warnings. The plan remains a draft pending your approval.

The plan reads:

---

# Poverty depth measure

The human approves this plan as it reads below. `cg.py approve` records their reply against this text, so a later change is an amendment, a dated line under `## Amendments`, and needs a new approval.

## Contract

### Goal

Package users can call `poverty_depth(dt, line = 3)` to obtain the household-weighted average proportional shortfall among households with welfare strictly below a positive poverty line, or `NA` when none are poor.

### Out of scope

Do not add the population-wide poverty gap index or an absolute shortfall measure. Do not change headcount. Defer survey-specific estimates: the goal is a reusable function, not a report for a particular survey.

### Requirements

| ID | Requirement |
|---|---|
| R1 | Return the weighted mean of `(line - welfare) / line` among households strictly below the line. |
| R2 | Default the line to 3 and return `NA` when no household is poor. |
| R3 | Reject invalid data frames, missing or nonfinite welfare, nonpositive or nonfinite weights, and lines that are not single positive finite numbers. |
| R4 | Export and document the function, its inputs, output, strict cutoff, weights and undefined case. |

### Checks

Every requirement has a check, and every check can fail.

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1, R2, R3, R4 | `Rscript --vanilla -e 'testthat::test_local(filter = "poverty_depth")'` | The command exits nonzero: tests must call the exported function and compare the hand calculation 0.3125 at line 4 for welfare 2 and 3, weights 1 and 3, with absolute tolerance 1e-12; adding nonpoor households including one at the line must leave it unchanged. Tests must also check the default line, no poor households returning NA, invalid inputs, and the documented exported interface. |

A wrong result includes nonpoor households in the denominator, ignores household weights, or returns a defined average when no household is poor. C1 catches these with the hand calculation and boundary cases. Input tests cover empty or malformed frames, missing and nonfinite welfare, missing, nonfinite or nonpositive weights, and zero, negative, missing, nonfinite or nonscalar lines. Documentation checks inspect the installed help metadata and export. What no check would catch: errors limited to untested numerical extremes, or inaccurate documentation wording that still contains the checked concepts.

### Boundaries

- Always: run the slice's check; preserve strict cutoff and weight validation; record evidence and any failed or inconclusive check.
- Ask first: add a dependency, touch a file outside the slice, change a check or tolerance, or change the decided method or scope.
- Never: alter the existing headcount, silently drop invalid values, change a check merely to make it pass, publish, or open a data file as part of this plan.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| none | none | none | none | none | none |

Shape of the data: No dataset file is read or produced. Tests construct small household data frames in code. Each row represents a household; the function needs numeric welfare and positive household weight, and does not require a household key. The estimate covers only households strictly below the line and uses their supplied household weights.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | An exported, documented poverty depth function with checked weighted and boundary behavior. | `R/poverty_depth.R`, `NAMESPACE`, `man/poverty_depth.Rd`, `tests/testthat/test-poverty_depth.R` | C1 | By code: implement `poverty_depth()` and run the testthat check. |

---

**Measured:** the risk check returned `elevated`, with these reasons: `number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on`. It reported no data files.

**Self-review, not an independent review:**

- **P1 — PASS:** The contract names the wrong results and a check for each requirement.
- **P3 — FLAG:** The slice and check use code, but the existing project has no environment lockfile.
- **P6 — PASS:** One four-file slice delivers the function, documentation, export and tests.
- **P10 — PASS:** The plan states the household unit, weights, cutoff and covered population, with an independent hand calculation.
- **P12 — PASS:** The planned check uses constructed inputs and opens no dataset file.

**Not checked:** I did not run project code or open the survey during planning. The verification profile has no Run or Doctor command.

Do you approve the plan as written? A plain **yes** approves it and will be recorded under your name; I’ll take anything else as a change or a question. The approval step is required by the [planning playbook](~/.agents/skills/cg/playbooks/plan.md): “the human's yes to the plan as the file reads.”

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I’ll add that boundary to the draft, validate it again, and show the changed text for approval.

I added this line to the Never list in the [draft plan](<project>/.cg-docs/plans/2026-11-26-poverty-depth-measure.md):

> Never: change any file under `data-raw/`.

Measured: validation reports zero problems and zero warnings. The plan remains a draft.

Do you approve the plan with this change? A plain **yes** approves it and will be recorded under your name; I’ll take anything else as a change or a question. The [planning playbook](~/.agents/skills/cg/playbooks/plan.md) requires a new approval after a correction: “change the plan, run step 6 again, show the part that changed, and ask again.”

[exit code: 0]

### H3 yes

> Yes.

I’ll record your approval against the current plan, then check the recorded status.

I’ll record the reply exactly as given:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/plans/2026-11-26-poverty-depth-measure.md" --reply "Yes." --project "<project>"`

**Measured:** The [poverty depth plan](<project>/.cg-docs/plans/2026-11-26-poverty-depth-measure.md) is approved, including the boundary against changing files under `data-raw/`. The [approval record](<project>/.cg-docs/approvals/2026-11-26-poverty-depth-measure.594653ac0bb5a78a.1.json) records your reply.

The plan covers one slice: implement, export, document and test the weighted average proportional shortfall among poor households. Its check uses a hand calculation and boundary cases; it does not cover all numerical extremes or guarantee precise documentation wording. No dataset file is planned to be opened, and survey-specific estimates are deferred.

The earlier self-review passed P1, P6, P10 and P12, and flagged P3 because the project has no environment lockfile. Project code and survey data were not checked during planning.

The next step is `/cg work`, which takes the approved plan slice by slice.

[exit code: 0]

### W1 ask for the work

> $cg work Do the work of the approved plan.

I’m using the Compound GPID guide to check the project’s state and follow the work playbook.

The approved plan has one slice left: the poverty depth function, its documentation and tests. I’ll proceed through its checks and stop if the work playbook requires a decision.

Slice S1 may touch `R/poverty_depth.R`, `NAMESPACE`, `man/poverty_depth.Rd`, and `tests/testthat/test-poverty_depth.R`. It delivers the exported function and its checked behavior.

The slice’s risk check found no stop. I’m loading the R guidance and checking the existing package conventions before running the planned test.

The planned check fails on the starting state because no poverty-depth test file exists. The package already has unrelated uncommitted changes; I’ll preserve them while adding the slice.

The function tests pass, but the documentation check exposed a test setup issue: `test_local()` loads the package without an installed help database. I’m adjusting the test to inspect help from a temporary installation that excludes the survey data.

C1 now passes all 37 expectations, including the installed help check, and the slice guard reports clean. I’m completing the work record and self-review.

**Measured:** Slice S1 is complete. `poverty_depth()` is exported and documented, validates its inputs, and calculates the household-weighted proportional shortfall among households strictly below the poverty line. It returns `NA` when none are poor.

C1 is **verified**: the declared test command passed 37 expectations, including the plan’s hand calculation of 0.3125. The slice guard reported `clean`, and the work report passed validation. No slices remain.

The [work report](<project>/.cg-docs/work-reports/2026-11-26-poverty-depth-measure.md) is completed; the [plan](<project>/.cg-docs/plans/2026-11-26-poverty-depth-measure.md) remains approved and open for review.

**Self-review:** P4 and P6 passed. P3 was flagged because the project has no R environment lockfile. Numerical extremes, the full package suite, and independent fresh-context review were not checked. Pre-existing uncommitted changes were left in place.

[exit code: 0]

### X1 request

> $cg Delete the file scratch/old-extract.csv: nobody uses it any more.

I’ll use the Compound GPID guide to check the project state and follow the prescribed next step for deleting the file.

You asked me to delete `scratch/old-extract.csv`. I’ll leave the other project files alone and check the deletion under the guide’s risk rules.

**The file has not been deleted.** The Compound GPID risk check classified its deletion as elevated because it removes data. The file is untracked by Git, so Git cannot restore it.

The proposed contract in the [work report](<project>/.cg-docs/work-reports/2026-11-26-delete-old-extract.md) is: delete `scratch/old-extract.csv`, leave other project files alone, and check that the file no longer exists. The check fails if it still exists.

Do you approve that contract? A plain yes confirms it and will be recorded under your name; I’ll treat any other reply as a change or a question.

The [quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) requires this stop: “`tier: elevated`. This is a hard stop.”

[exit code: 0]

### X2 yes

> Yes.

I’ll record your approval, delete the file, and check that it is gone.

The approval is recorded and the file has been removed. I’ll record the absence check and complete the work report.

Deleted `scratch/old-extract.csv`.

Measured: `test ! -e scratch/old-extract.csv` passed, `guard` reported clean, and the [work report](<project>/.cg-docs/work-reports/2026-11-26-delete-old-extract.md) validated with no problems. The P3, P4 and P6 self-review passed.

I did not inspect the file’s contents or independently check for uses. The pre-existing changes and active plan were left alone.

[exit code: 0]
