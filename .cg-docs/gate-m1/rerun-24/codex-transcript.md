### B1 setup

> $cg

I’ll use the Compound GPID guide to check the project’s current state and follow the playbook it selects.

The project is an R package, and the R pack is installed. I’ll inspect the package’s code and checks without opening its data file, then prepare the setup proposal.

I recommend setting up Compound GPID with **core** and **lang-r**. Both packs are installed.

- **R setting:** `lang-r.r-syntax=data.table-collapse`. This is the pack default, and the package imports `data.table` and uses `fread()` in [read_survey.R](<project>/R/read_survey.R:7).
- **Draft verification profile:** Run command: not found. Doctor command: not found. The existing tests check that the survey reader returns the expected columns and 20 rows, and rejects a non-positive weight. I did not run them.
- **Files found:** 3 `.R` files, 1 `.Rd` file, 1 `.csv` file, and 3 files without extensions. The one data file is `inst/extdata/survey.csv`; I did not open it.
- **Assumption:** The `data.table` usage supports the default R dialect, although the code does not show use of `collapse`.

The setup dry run says it would create these files:

- [.cg-docs/config.json](<project>/.cg-docs/config.json)
- [.cg-docs/verification.md](<project>/.cg-docs/verification.md)
- [AGENTS.md](<project>/AGENTS.md)
- [CLAUDE.md](<project>/CLAUDE.md)
- [.Rbuildignore](<project>/.Rbuildignore)

Would you approve this setup, and specify the data rules? For example: **“Yes. `inst/extdata/` is Public; Codex may read up to Public; levels are Public, Internal, Restricted.”** You can leave any classification answer open if you don’t know it yet.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the survey as Public and Codex as approved to read Public data. The ordered classification levels remain open.

Compound GPID setup is complete. **Measured:** status reports `phase: ready`, `stops: none`, and no missing packs. The R setting is `lang-r.r-syntax=data.table-collapse`.

I recorded `inst/extdata/survey.csv` as Public and Codex as approved to read Public data. The ordered classification levels remain open.

Setup created [.cg-docs/config.json](<project>/.cg-docs/config.json), [.cg-docs/verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The verification profile remains a draft: no Run or Doctor command was found, and I did not run the existing tests. The project contains three R files and one data file; I did not open the data.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its selected playbook.

I’ll add the weighted headcount and a test against the expected value of 0.153846. I’ll first assess the files and the numerical risk; the project currently has four changed files.

**Measured:** Compound GPID classified the work as elevated risk because it computes a number and adds a public function interface. The survey is cleared for Codex.

The proposed contract is recorded in the [work report](<project>/.cg-docs/work-reports/2026-11-27-add-weighted-headcount.md): add and document `headcount(dt, line = 3)`, then test the toy-survey result against `0.153846` to six decimal places and check boundary and weight behavior.

May I proceed under that contract? A plain **yes** confirms it and will be recorded under your name; any other reply will be treated as a change or question.

The [quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) says **“`tier: elevated`. This is a hard stop”** and requires this confirmation before code changes. No implementation or tests have been run yet.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll record your reply against the contract, then implement and check the function if the guide accepts it.

Your approval was recorded. I’ll use the existing survey columns and check both the strict cutoff and the weighting, including the toy-survey result.

The function and tests are in place. I’ll run the test suite through the guide’s evidence command, then check the recorded change.

**Implemented and verified:** `headcount(dt, line = 3)` returns the weighted share of households whose welfare is strictly below the line. It is exported and documented in [headcount.R](<project>/R/headcount.R).

The toy survey returned **0.153846154**, within the agreed tolerance of your expected `0.153846`. The [testthat checks](<project>/tests/testthat/test-headcount.R) also cover weighting, the cutoff boundary, and invalid observations.

**Measured:** `Rscript --vanilla -e 'testthat::test_local(reporter = "summary")'` passed, and Compound GPID reported `guard: clean`. The work report’s self-review passed P4 and P6 and flagged P3 because the project has no environment lockfile.

A full `R CMD check` and cross-environment reproducibility were not checked. Existing untracked setup files were left alone; the local R startup also fails without `--vanilla`. The completed record is in the [work report](<project>/.cg-docs/work-reports/2026-11-27-add-weighted-headcount.md).

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll inspect the package and its survey data conventions, then add the household count where it fits. I’m using the R package development guidance for the implementation.

The survey reader returns one row per household, so the count can be the number of rows. I’ll expose an unweighted count that accepts that data frame and handles an empty survey.

Added [household_count()](<project>/R/household_count.R), which returns the unweighted number of rows in a survey data frame. For the bundled survey, `household_count(read_survey())` returns 20.

All 13 tests pass. The package check reported no errors or warnings and one note because it could not verify the system clock remotely.

[exit code: 0]

### X1 request

> $cg Delete the file scratch/old-extract.csv: nobody uses it any more.

I’ll use the Compound GPID guide to check the project state and follow the selected playbook for the deletion.

You asked me to delete `scratch/old-extract.csv`. I’ll check the deletion’s risk and leave other project files alone.

**Measured:** The file exists. Compound GPID classified its deletion as elevated risk because it deletes data. I have not opened or deleted it.

The proposed contract, recorded in the [work report](<project>/.cg-docs/work-reports/2026-11-27-delete-old-extract.md), is:

> Delete scratch/old-extract.csv, which irreversibly deletes data. Leave all other project files alone. Check that scratch/old-extract.csv no longer exists; the check fails if the path remains.

Do you approve this contract? A plain **yes** confirms it and will be recorded under your name. I’ll treat anything else as a change or a question.

The [quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) requires this confirmation: “**`tier: elevated`.** This is a hard stop.”

[exit code: 0]

### X2 yes

> Yes.

I’ll record your approval, then delete the file and verify the result.

The work report is waiting for the approval you just gave. I’ll record the reply against that report.

The file has been deleted. I’ll record the existence check and review the work report.

**Measured:** Deleted `scratch/old-extract.csv`. The check `test ! -e scratch/old-extract.csv` passed, and Compound GPID’s guard reported clean. The P3, P4 and P6 self-review passed, and the [work report](<project>/.cg-docs/work-reports/2026-11-27-delete-old-extract.md) validated without warnings.

I did not inspect the file’s contents or verify downstream references; the request stated that it was unused. The project’s pre-existing changes were left alone.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Whatever it is, it must count every household, with a household at or above the line counted as zero, and it must be a share of the line. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check the project’s state and work through the measure with you before anything is built.

The brainstorm is open as a draft. I’ll check the package’s existing poverty calculation and a reference for the measure before asking which outcome you want.

I understand the goal as adding a measure of how far households fall below the line, expressed as a share of the line, with every household included and those at or above the line contributing zero. I’m still missing how you intend to use the result and whether to use the package’s existing weights.

**A promising measure is the poverty gap:** the average shortfall from the poverty line, expressed as a share of that line, with nonpoor households contributing zero. The [World Bank uses this definition](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.NAGP).

For example, with a line of 100 and equally weighted households at 50 and 100, their gaps are 50% and 0%, so the overall gap is **25%**. It combines how many households are poor with how far below the line they are; it does not say that the average *poor household* is 25% below the line.

The package’s existing [headcount](<project>/R/headcount.R) uses household weights. I recommend using those weights for the gap too, so the two measures describe the same weighted household population. The trade-off is that the result depends on what the supplied weights represent.

1. Should the aggregate gap use those household weights?
2. Who will use the result, and what comparison or decision should it support? My starting assumption is that package users will read it alongside the headcount.

The [intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md) is a draft. **Checked:** the existing headcount code and the World Bank definition. **Not checked:** the survey data or package execution. Nothing has been built.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record those choices and use a small hand-calculated example as the reference. Then I’ll put the measure and its trade-offs to you.

The draft now records your choices: use the existing household weights, present the result alongside headcount, and check it against a small hand-built example.

I recommend the **weighted poverty gap**: calculate each household’s shortfall as a share of the line, give households at or above the line a gap of zero, then take the weighted average across all households.

For a small arithmetic check, take a line of 100 and two households:

| Welfare | Weight | Gap |
|---:|---:|---:|
| 50 | 1 | 50% |
| 100 | 3 | 0% |

The weighted gap is `(1 × 50% + 3 × 0%) / 4 = 12.5%`. This is the average across all represented households. It reflects both how many are poor and how far below the line they are.

The alternatives are weaker for your stated goal: averaging only poor households’ gaps leaves the others out of the denominator; squaring the gaps puts more emphasis on the poorest but no longer gives an average shortfall as a share of the line. Keeping headcount alone would leave depth unmeasured.

**Would you like to use the weighted poverty gap?** The choice is still open in the [draft intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md). The example is calculated by hand; the package has not been run or changed.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record the weighted poverty gap as your choice. I’ll also check the remaining boundary decisions that affect what the measure means.

The **weighted poverty gap** is now your chosen measure in the [draft intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md). I’ve also added the term to the project’s [glossary](<project>/GLOSSARY.md).

Three details affect the result:

1. **Negative welfare:** I recommend including finite negative values without capping the gap, consistent with the existing headcount. This means a gap can exceed 100% of the line. Is that what you want?
2. **Output:** I recommend returning a fraction, as headcount does: `0.125` for the 12.5% example. Users could multiply by 100 for display. Is that right?
3. **Poverty line:** I recommend requiring a single, finite, positive line. Zero cannot be a divisor; a negative line would make the shortfall share misleading. This is stricter than the current headcount. Is that right?

The example’s value is derived by hand. Package execution and the survey data remain unchecked.

[exit code: 0]

### G4 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record those decisions, then check the intent for any remaining gaps before showing it to you for confirmation.

The [intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md) is still a draft and passes its completeness check. Here is what it records for your confirmation.

**Goal:** Show package users how far below the line poor households are, as a share of the line, alongside the headcount. Count every household; those at or above the line contribute zero.

**Out of scope:** Change the existing headcount or replace it with a measure averaged only among poor households.

**A wrong result:** Omitting households at or above the line from the denominator, ignoring weights, or returning an unnormalized shortfall. As a hand-calculated check, a line of 100, welfare values of 50 and 100, and weights of 1 and 3 must produce **0.125**.

**Your decisions:**

- Use the existing household weights and present the result alongside headcount.
- Use a small hand-built example when a reference value is needed.
- Use the weighted poverty gap: the weighted average of each household’s shortfall as a share of the line.
- Include finite negative welfare without capping the gap; the result can exceed 1.
- Return a fraction, so `0.125` represents 12.5%.
- Require one finite, positive poverty line.

**Assumptions I am making:**

1. The supplied weights represent the households users want to describe. If that is wrong, the result describes a different population and the weighting choice needs revisiting.

Correct me now.

The alternatives considered were the average gap among poor households only, the squared poverty gap, and keeping headcount alone. Each was set aside because it does not answer the stated goal in the same way.

**Is this intent what you want?** A plain yes confirms the text as written and is recorded under your name. I’ll take anything else as a change or a question.

[exit code: 0]

### G5 vague reply

> Sounds good.

I’ll check that reply against the guide’s confirmation rule.

The [intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md) remains a draft. Is anything unclear, or would you change anything? If it is right as written, please reply **yes**.

The [guide’s confirmation rule](~/.agents/skills/cg/grilling.md) treats “sounds good” as agreement without a decision, so the approval command did not record it.

[exit code: 0]

### G6 answer

> Yes.

I’ll record your confirmation of the intent.

The [intent](<project>/.cg-docs/brainstorms/2026-11-27-household-poverty-depth.md) is approved and recorded.

It calls for a weighted poverty gap across all households, with zero for households at or above the line, returned as a fraction. The reference check will use a small hand-calculated example. No package code has been built or run.

When you’re ready to continue, use `/cg plan` to plan the work, or `/cg` with a small first change.

[exit code: 0]

### H1 ask for the plan

> $cg plan Write the plan for the work we settled in the brainstorm.

I’m using the Compound GPID guide to check the project’s state and follow its planning playbook.

The decided intent specifies a weighted poverty gap and an arithmetic reference value. I’m checking the package interface and the planning template; the survey file itself stays closed during planning.

The draft plan passes the guide’s structural validation. Its risk check identifies a new numerical result and a public function interface; I’m arranging the required plan reviews now.

The [plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) is **draft**, awaiting your approval. Measured: structural validation reported no problems or warnings. The plan reads:

---

# Household poverty depth

The human approves this plan as it reads below. `cg.py approve` records their reply against this text, so a later change is an amendment, a dated line under `## Amendments`, and needs a new approval.

## Contract

### Goal

Package users can call an exported `poverty_gap(dt, line = 3)` to obtain the weighted poverty gap as a fraction across all supplied households, alongside the existing headcount.

### Out of scope

Changing headcount or calculating the mean gap only among poor households. Squared poverty gap is deferred because the goal does not require it.

### Requirements

| ID | Requirement |
|---|---|
| R1 | Return the weighted mean of household shortfalls divided by the positive line, counting all households and assigning zero at or above the line. |
| R2 | Include finite negative welfare without capping the gap. |
| R3 | Reject empty or invalid inputs: missing columns, nonnumeric or nonfinite welfare, nonnumeric, nonfinite or nonpositive weights, and a line that is not one finite positive number. |
| R4 | Export and document the function, its arguments, fraction, denominator, weights and treatment of negative welfare. |
| R5 | Preserve headcount behavior. |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1, R2, R3, R4, R5 | `Rscript --vanilla -e 'testthat::test_local(filter = "poverty-gap", stop_on_failure = TRUE)'` | The package-level tests fail: line 100, welfare 50 and 100, weights 1 and 3 must return 0.125 within 1e-12; all nonpoor return zero; finite negative welfare can yield a gap above 1; invalid inputs raise errors; the function is exported and its help describes the contract; the headcount reference cases remain unchanged. |

The tests must exercise the exported function as a package caller and check the default line, equality and above-line observations, unequal weights, negative welfare, and each invalid-input category. A wrong result omitting nonpoor households, ignoring weights or omitting normalization fails the 0.125 example. The headcount checks pin its arithmetic and acceptance of a finite nonpositive line. What no check would catch: all possible input combinations, numerical instability at extreme magnitudes, whether supplied weights represent the intended population, and errors in prose beyond the checked contract terms.

### Boundaries

- Always: run the slice check, compare against the stated arithmetic reference, and reject missing or invalid observations rather than silently dropping them.
- Ask first: adding a dependency, touching a file outside the slice, or changing a check or tolerance.
- Never: alter headcount, read the survey data for this slice, publish, or weaken a check to make it pass.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| none | none | none | none | none | none |

Shape of the data: No dataset is read or produced. The function accepts one row per household with numeric welfare and weight columns; no key is required. The estimate covers all supplied households, weighted by their positive household weights. Welfare and the line must use the same units. The hand-built values in tests are examples, not a survey dataset. The weights are assumed to represent the population the caller intends to describe.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | The exported, documented weighted poverty gap with input assertions and regression checks. | R/poverty_gap.R, man/poverty_gap.Rd, NAMESPACE, tests/testthat/test-poverty-gap.R | C1 | By code: implement `poverty_gap()` and run the testthat package-level check. |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |

---

Measured: the risk tier is **elevated** because the work computes a number someone will read and changes a public interface. The plan keeps the survey file closed.

All five independent plan reviews passed with no findings: contract, determinism, simplicity, domain correctness, and data governance. The reviewers noted that the implementation and its numerical output do not exist yet; project code and data were not run or inspected for those reviews. The verification profile has no Run command.

Do you approve the plan as written? A plain **yes** approves it and will be recorded under your name. I’ll take anything else as a change or a question.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I’ll add that boundary to the draft, then rerun its validation and required reviews before putting the changed plan back to you for approval.

Added this line to the [draft plan’s Never list](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md):

> Never: change any file under data-raw/.

Measured: validation reported no problems or warnings. All five independent reviews passed with no findings. The implementation and its numerical output do not yet exist, so they were not checked.

Do you approve the plan with this addition? A plain **yes** approves it and will be recorded under your name. I’ll take anything else as a change or a question.

[exit code: 0]

### H3 yes

> Yes.

I’ll record your approval against the plan as it now reads:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/plans/2026-11-27-household-poverty-depth.md" --reply 'Yes.' --project "<project>"`

Measured: the [household poverty depth plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) is **approved**, including the boundary that no file under `data-raw/` is changed. Your approval was recorded.

The plan calls for one slice: add and check an exported weighted poverty gap function. Implementation has not started. Use `/cg work` to begin it.

[exit code: 0]

### The conformance record at the plan stage

plan P1 contract: PASS, independent review
  note: Left the deferred squared poverty gap and the choice of method alone, as directed by the lens.
plan P3 determinism: PASS, independent review
  note: The planned output is a function in source code, so it requires no Run command to write it. I did not run the project or repro.
plan P6 simplicity: PASS, independent review
  note: Left the input assertions and documentation in place because the contract requires them. No implementation was available to inspect.
plan P10 domain-lenses: PASS, independent review
  note: The implementation and its numerical output do not yet exist, so their behavior could not be inspected.
plan P12 governance: PASS, independent review
  note: The plan keeps the survey closed and declares no dataset reads or outputs. I did not inspect data files or run project code.
missing: none
independent review: 5; self-review: 0


### W1 ask for the work

> $cg work Do the work of the approved plan.

I’m using the Compound GPID guide to check the project’s state and follow the work playbook.

S1 is the only slice left. It adds the poverty gap function, documentation, export, and tests in the four files named in the plan.  
I’ll stop at the work playbook’s specified decision points.

The plan’s risk check found no stop. I’m loading the project’s R guidance and checking the slice’s starting state.

**Measured:** S1 has not started. The initial C1 run failed because no `poverty-gap` test file exists, so it did not test the function. No implementation files were changed.

The [work playbook](~/.agents/skills/cg/playbooks/work.md) requires a stop when a pre-change check cannot test the code. The [plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) remains approved, and the [work report](<project>/.cg-docs/work-reports/2026-11-27-household-poverty-depth.md) is in progress. S1 remains to be done.

Would you like `/cg plan` to amend the plan so the tests can be created and run against the missing implementation before S1 proceeds?

[exit code: 0]

### W2 go on

> Go on with the plan as it is approved. I have nothing to add.

I’ll continue with the approved plan. I’ll create the planned tests first and run them against the current package before implementing the function.

The planned tests now fail because `poverty_gap` and its help page do not exist; the headcount reference checks pass. I’ll implement the function and its documentation.

C1 now passes all 38 expectations, including the independent 0.125 reference, and the slice guard is clean. I’m completing the work record and the required reviews.

**Measured:** S1 is implemented. The exported `poverty_gap()` function, help page, and tests are in place. C1 passed 38 expectations, including the 0.125 arithmetic reference; `guard` reported `clean`.

The work is **not yet closed**. The [work report](<project>/.cg-docs/work-reports/2026-11-27-household-poverty-depth.md) remains in progress, and the [plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) remains approved. One review was recorded as a self-review; the remaining required reviews have not run.

That review flagged [the documentation test](<project>/tests/testthat/test-poverty-gap.R:28): it checks for contract terms but could pass if the help text described the denominator or negative welfare incorrectly.

**Measured:** Reproducibility was inconclusive because the verification profile has no Run command. The check also flagged the missing lockfile. Existing unrelated working-tree changes were left alone; extreme numerical cases and all possible inputs were not checked.

[exit code: 0]

### W3 go on

> Go on with the plan as it is approved. I have nothing to add.

I’ll continue the remaining reviews required by the approved plan and record their verdicts.

The review has confirmed the planned test passes and found two areas for the record: the help-text test can miss an incorrect statement, and extreme weights can overflow. I’m completing the remaining independent reviews.

The reviews also found gaps in the work report’s evidence labels and unchecked limitations. The remaining domain review is still running.

The domain review is taking longer than the others. The recorded findings are available in the work record while it finishes.

**Measured:** All planned checks are verified, the slice guard is clean, and the work report validates with no problems. The [work report](<project>/.cg-docs/work-reports/2026-11-27-household-poverty-depth.md) is completed; the [plan](<project>/.cg-docs/plans/2026-11-27-household-poverty-depth.md) remains approved and has not been signed off.

The reviews returned these findings:

- **Measured:** Finite positive weights can overflow the denominator and produce an incorrect result in [poverty_gap.R](<project>/R/poverty_gap.R:26). The plan identified extreme numerical instability as an unchecked limit.
- **Measured:** The [documentation test](<project>/tests/testthat/test-poverty-gap.R:28) passes even if the help page incorrectly says negative welfare is capped.
- **Measured:** The [verification profile](<project>/.cg-docs/verification.md:18) has no Doctor command. It also has no Run command, so reproducibility was inconclusive.
- **Measured:** The work report lacks evidence labels and pointers for several claims and omits two stated limits: whether weights represent the intended population and prose errors beyond the checked terms.

Seven reviews were independent and two were recorded as self-reviews. Determinism, simplicity, language, and data governance passed; contract, verification, adversarial, claims, and domain reviews flagged the findings above. No review findings were changed during review.

The work playbook leaves those findings for your decision. Should the overflow and test gaps be addressed before sign-off?

[exit code: 0]

### The conformance record at the review stage

review P1 contract: FLAG, self-review
  finding: tests/testthat/test-poverty-gap.R:31-34: The documentation check required by C1 in `.cg-docs/plans/2026-11-27-household-poverty-depth.md:37` only searches for isolated terms, so it can pass when the help text states the denominator or treatment of negative welfare incorrectly. (P1; fix: approve an amendment with a check that fails when tho
  note: The claims record has no `not-built` findings; wording preferences, deferred work, and method choices were left alone.
review P3 determinism: PASS, independent review
  note: Set aside `unpinned` because this is an R package declaring dependencies in DESCRIPTION; set aside `no-run` because the sole mapped item is a source function, not an output a run writes. The help page and export are individual edits. I did not rerun repro or the pipeline because they may write outpu
review P4 verification: FLAG, independent review
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0009-20261127T150205Z-ad-hoc.json: C1 still passes when the help page incorrectly says negative welfare is capped. (P1; fix: add a check that fails when the documented treatment of negative welfare is wrong.)
  finding: .cg-docs/verification.md:18: The verification profile has no Doctor command, so the environment has not been checked before trusting the results. (P1; fix: define and run a read-only Doctor command that checks the required environment.)
  note: The declared check was rerun and verified in .cg-docs/evidence/2026-11-27-household-poverty-depth/0008-20261127T150146Z-rerun.json. All possible inputs and extreme numerical instability were not checked.
review P5 adversary: FLAG, independent review, round 1 of 3
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0011-20261127T150228Z-ad-hoc.json: R1 is broken for finite positive weights whose sum overflows at R/poverty_gap.R:26. (P2; fix: normalize weights before calculating their weighted mean.)
  dropped: .cg-docs/evidence/2026-11-27-household-poverty-depth/0012-20261127T150240Z-ad-hoc.json: A probe of negative welfare and unequal weights did not reproduce a fault.
  dropped: .cg-docs/evidence/2026-11-27-household-poverty-depth/0010-20261127T150211Z-ad-hoc.json: The initial probe failed during R startup, before reaching the function.
  note: The successful probe used Rscript --vanilla because the user’s R startup profile prevented Rscript -e from reaching the function. Extreme numerical instability was identified as a limitation in the approved plan. Other possible inputs were not exhaustively probed.
review P6 simplicity: PASS, independent review
  note: Set aside the three `no-caller` entries: `headcount`, `household_count`, and `poverty_gap` are exported package functions. The guard record is clean; other uncommitted files predate this slice. Input assertions and the exported function are required by the contract.
review P7 claims: FLAG, independent review
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:19: The risk claims are written without measured, inferred, or guess labels. (P1; fix: label each claim and give its evidence or reasoning.)
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:41: The numerical validation claim has no evidence label or pointer to the recorded check. (P1; fix: label it measured and point to the check record.)
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:45: The claims about the initial test run and implementation sequence have no evidence labels or pointers. (P1; fix: label the claims and point to their evidence.)
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:45: The not-checked section omits the plan’s stated limits on whether weights represent the intended population and prose errors beyond the checked terms. (P2; fix: include those unchecked limits.)
  finding: .cg-docs/work-reports/2026-11-27-household-poverty-depth.md:49: The claim about the earlier working tree has no evidence label or pointer. (P1; fix: label it and provide evidence or identify it as an inference.)
  note: The claims record has no findings. I left the human’s request, plain descriptions of files, and whether checks passed to their respective scopes.
review P10 domain-lenses: FLAG, self-review
  finding: .cg-docs/evidence/2026-11-27-household-poverty-depth/0011-20261127T150228Z-ad-hoc.json: Finite positive weights can overflow the denominator and silently produce an incorrect weighted poverty gap. (P0; fix: calculate the weighted mean with weights scaled to avoid overflow.)
  note: The general data lens was applied to the function and the recorded synthetic-input probe. No survey data were opened; the verification profile declares no input assertion commands. Other extreme inputs were not exhaustively checked.
review P11 language: PASS, independent review
  note: Compared the contract, introduced names, and reader-facing text with both glossaries. No project data was opened.
review P12 governance: PASS, independent review
  note: The slice uses hand-built examples; its declared check and recorded probes do not read a dataset. The survey-reading tests in the pre-existing working tree were not run or inspected for data content. Sign-off has not yet been offered, so the AI-use statement required before sign-off remains to be pr
missing: none
independent review: 7; self-review: 2

