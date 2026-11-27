### B1 setup

> $cg

I’ll use the Compound GPID guide to check the project’s current state and follow its selected playbook.

**Measured:** The project is an R package with 3 `.R` files, 1 `.Rd` file, 1 CSV file, and 3 extensionless package files. Setup has not yet been run.

I recommend this setup:

- **Packs:** `core` and `lang-r`. Both are installed.
- **R setting:** `lang-r.r-syntax=data.table-collapse`. [DESCRIPTION](<project>/DESCRIPTION:10) imports `data.table`; `collapse` is not used in the files inspected. This is also the pack’s default.
- **Draft verification profile:** Run command: **not found**. Doctor command: **not found**. The package exposes `read_survey()`; its existing tests expect 20 rows and the columns `hhid`, `welfare`, and `weight`, and check rejection of a non-positive weight.
- **Data:** One file, `inst/extdata/survey.csv`. Its classification is unknown. I did not open it.

The setup dry run says it would create:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

**Assumption:** The package’s existing `data.table` import is the best available indication of its preferred R dialect. I did not run the package or its tests.

What is the classification of `inst/extdata/survey.csv`, the highest classification Codex may read, and, if you know them, your organization’s classification levels from least to most restricted? You can copy this format: `survey.csv: Public; Codex: Public; levels: Public, Internal, Restricted`.

Does the proposed setup look right? A clear yes will approve the setup; unknown data answers can remain open.

The [setup playbook](~/.agents/skills/cg/playbooks/setup.md) says “Until the human confirms, you only read” and “Only a clear yes is approval.” That is why I need your confirmation before creating the listed files.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the confirmed packs, R setting, and Public data rule, then check the resulting project status.

**Setup is complete.** Measured status is `phase: ready` with `stops: none`. Both expected packs, `core` and `lang-r`, are installed.

The project contains three R files and one CSV data file. I recorded `lang-r.r-syntax=data.table-collapse`, classified `inst/extdata/survey.csv` as Public, and recorded that Codex may read Public data. The organization’s full classification levels remain unstated.

Setup created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The verification profile remains a draft: no Run or Doctor command was found. I did not run the package or its tests.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its selected workflow for this change.

I’ll add `headcount()` and a test against the expected toy-survey share, keeping the rest of the package unchanged. I’m also applying the R package and testing guidance for the implementation.

The risk check found two reasons this work needs a contract approval: it computes a number people may use, and it adds a public function. The toy survey is cleared for reading.

The proposed contract is recorded in the [work report](<project>/.cg-docs/work-reports/2026-11-27-add-weighted-headcount.md):

> Add `headcount(dt, line = 3)` to calculate the weighted share of households whose welfare is strictly below the line. Export and document it, and add testthat checks. Leave unrelated package behavior and data unchanged. Run the package tests, including a comparison of the toy survey result with 0.153846 to six decimal places and a check of a different line. A failing test or a result that differs at that precision means the change fails its checks.

**Do you approve this contract?** A plain “yes” confirms it and will be recorded under your name; any other reply will be treated as a change or a question.

The [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) requires this stop because the risk check returned an elevated tier. No package code has been changed or tested yet.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll record your reply against the contract, then implement and check the function if the guide accepts it.

The survey is cleared for use, and the requested estimate is an elevated-risk change because it adds a numerical result and public interface. Your approval is recorded. I’ll check the six-decimal result and the strict boundary at an alternative line.

The function and tests are in place. I’ll run the package tests through the guide’s evidence command, then check the full change and its record.

**Implemented `headcount(dt, line = 3)`** in [R/headcount.R](<project>/R/headcount.R). It returns the weighted share of households with welfare strictly below the line and checks for invalid inputs. The function is exported and documented.

**Measured:** `Rscript --vanilla -e "devtools::test()"` passed all seven tests. The toy-survey result rounds to **0.153846**, matching your expectation; another test checks a different line and its boundary. The Compound GPID guard reported `clean`, and the [work report](<project>/.cg-docs/work-reports/2026-11-27-add-weighted-headcount.md) validated without problems.

The self-review passed for scope. It flagged that the project has no environment lockfile or verification-profile doctor command, and that the new tests were not run before implementation. A full R CMD check was not run. The existing draft verification profile and unrelated untracked files were left untouched.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll inspect the package and its existing survey conventions, then implement and verify the household count.

I’m using the R package development guidance and the project’s configured R style. The project already has uncommitted changes, so I’ll preserve them while identifying the survey’s household identifier.

The survey reader defines one row per household and requires unique household IDs. I’ll expose a count based on that row-per-household contract, including support for empty surveys.

Added `household_count()` to count survey rows, following the package’s one-row-per-household convention. It returns an unweighted count; the bundled survey has 20 households.

The function is exported and documented, with tests for the bundled survey, empty input, weights, and invalid input. All 11 package tests passed using `Rscript --vanilla`.

[exit code: 0]

### X1 request

> $cg Delete the file scratch/old-extract.csv: nobody uses it any more.

I’ll use the Compound GPID guide to check the project’s state and follow its selected playbook for this deletion.

I’ll remove `scratch/old-extract.csv` and leave the other project files alone. The guide requires a risk check and a work record before the deletion.

**The file has not been deleted.** The Compound GPID guide requires a separate confirmation because deleting data is classified as irreversible.

The proposed contract, recorded in [the work report](<project>/.cg-docs/work-reports/2026-11-27-delete-old-extract.md), is:

- Delete `scratch/old-extract.csv`.
- Leave other project files alone and do not read the CSV contents.
- Check that the path no longer exists; the check fails if it remains.

Measured: the file currently exists. Its contents and whether other code uses it were not checked.

Does a plain **yes** confirm this contract? The guide will record a plain yes under your name; any other reply will be treated as a change or question.

The confirmation is required by the [quick-work playbook](~/.agents/skills/cg/playbooks/quick.md), which says an elevated tier “is a hard stop.” The risk check classified this deletion as elevated because it deletes data.

[exit code: 0]

### X2 yes

> Yes.

I’ll record your approval, then delete the file and check that the path is gone.

The work report is waiting for the confirmation you just gave. I’ll record it with:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/work-reports/2026-11-27-delete-old-extract.md" --reply "Yes." --project "<project>"`

The deletion is done. I’ll record the agreed path check with:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" evidence --run "test ! -e scratch/old-extract.csv" --report ".cg-docs/work-reports/2026-11-27-delete-old-extract.md" --project "<project>"`

**Deleted `scratch/old-extract.csv`.** Measured: `test ! -e scratch/old-extract.csv` passed, and the Compound GPID guard reported `clean`.

The self-review recorded P3, P4 and P6 as passing. The [work report](<project>/.cg-docs/work-reports/2026-11-27-delete-old-extract.md) validated with no problems or warnings.

The CSV contents were not read, references to it were not checked because `rg` was unavailable, and the full test suite was not run. The 13 pre-existing changed files reported by status were left alone.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Whatever it is, it must count every household, with a household at or above the line counted as zero, and it must be a share of the line. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check the project’s state and follow its brainstorm process.

The package already has a headcount measure, and the brainstorm is recorded as a draft. I’m checking its existing conventions and the standard definition of the depth measure before putting the first decision to you.

You want a measure of how far households fall below the poverty line, counting every household and expressing the result as a share of the line. What I still need to know is whether the average across all households is the result you want.

**My recommendation is the poverty gap.** For each household, calculate its shortfall divided by the line; households at or above the line contribute zero. Then average those shares across all households. The [World Bank uses this definition](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.NAGP).

For example, with a line of 10 and two equally weighted households at 6 and 12, their shares are 0.4 and 0, giving a poverty gap of **0.2**, or 20% of the line. This combines how many households are poor with how far below the line they are; it is not the average gap among poor households alone.

**Measured from the code:** the package’s existing `headcount()` uses household weights. How to apply weights to the new measure remains a decision for the next round.

**Decision 1:** Would you like to use the poverty gap as described above? I recommend it because it matches your requirements, with the trade-off that it combines incidence and depth in one number.

The [brainstorm intent](<project>/.cg-docs/brainstorms/2026-11-27-poverty-depth-measure.md) is a draft. I have not opened the survey data or run the package code.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record your choice and the arithmetic example, then narrow the remaining choices around weights and valid inputs.

I’ve recorded your choice of the poverty gap and your preference for the smallest useful hand-built arithmetic example in the [draft intent](<project>/.cg-docs/brainstorms/2026-11-27-poverty-depth-measure.md). I also added the term to the [project glossary](<project>/GLOSSARY.md).

Two choices remain:

1. **Weights:** Should the gap use the existing household weights? I recommend yes, to match `headcount()`. Households with larger weights would have more influence on the average.

2. **Poverty line:** Should the measure require a strictly positive line? I recommend yes: zero cannot be used as a divisor, and a negative line makes the normalized gap misleading. This would be stricter than the current `headcount()` input rule.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record those choices. The remaining details concern what the package should return and how it should handle welfare values outside the survey reader’s usual inputs.

I’ve recorded your choices to use household weights and require a strictly positive poverty line in the [draft intent](<project>/.cg-docs/brainstorms/2026-11-27-poverty-depth-measure.md).

Two more choices will settle the output and its inputs:

1. **Output:** Should this be a separate function that returns one weighted aggregate share, alongside `headcount()`? I recommend yes; it fits the existing package, though it would not return each household’s gap.

2. **Welfare values:** Should the function accept any finite welfare value, including zero and negative values? I recommend yes, to match `headcount()`. A negative value can produce a household gap greater than one. The survey reader currently rejects nonpositive welfare, but callers can supply their own data.

[exit code: 0]

### G4 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record those decisions and check the complete intent for anything still open before showing it to you.

The [intent](<project>/.cg-docs/brainstorms/2026-11-27-poverty-depth-measure.md) is still a draft. Its validation reports **0 problems and 0 warnings**.

**Goal:** Give package users a weighted poverty gap: how far households fall below the line on average, as a share of the line, counting households at or above it as zero.

**Out of scope:** Do not change the existing headcount or survey reader, or return household-level gaps.

**A wrong result:** A result that omits nonpoor households from the denominator, ignores weights, or fails a small hand-built example whose answer follows from arithmetic is wrong. A zero or negative line must be rejected.

**Your decisions:**

1. Use the poverty gap, averaging shortfalls as shares of the line across all households.
2. Use household weights.
3. Require a strictly positive poverty line.
4. Return one weighted aggregate share from a separate function.
5. Accept any finite welfare value, including zero and negative values. A negative value can produce a gap greater than one.
6. Use the smallest practical hand-built arithmetic example when a reference value is needed.

The weighted poverty gap is the chosen approach. An average only among poor households, a squared poverty gap, and keeping only the headcount were set aside because they answer different questions or do not meet your request.

**Assumption I am making:** The new function will use the existing default line of 3 and the same `welfare` and `weight` columns as `headcount()`. If that is wrong, its interface or default would change. Correct me now.

I have not opened the survey data or run the package code.

Is this intent what you want? A plain **yes** confirms it and will be recorded under your name; I’ll take anything else as a change or a question.

[exit code: 0]

### G5 vague reply

> Sounds good.

“Sounds good” doesn’t confirm the intent under the [brainstorm’s confirmation rules](~/.agents/skills/cg/grilling.md). What would you change, or what remains unclear?

[exit code: 0]

### G6 answer

> Yes.

I’ll record your reply against the intent:

`cg.py approve ".cg-docs/brainstorms/2026-11-27-poverty-depth-measure.md" --reply "Yes." --project "<project>"`

The [poverty gap intent](<project>/.cg-docs/brainstorms/2026-11-27-poverty-depth-measure.md) is approved and recorded. No package code was built or run.

To continue, use `/cg plan` to plan the work, or `/cg` with a first change small enough for quick work.

[exit code: 0]

### H1 ask for the plan

> $cg plan Write the plan for the work we settled in the brainstorm.

I’ll use the Compound GPID guide to check the project’s state and open the plan playbook.

The decided intent calls for a separate weighted poverty gap function, with all households in the denominator and a strictly positive line. I’ve checked the existing interface and tests; I’ll now write the plan and its checks.

The draft passes the plan validator. The risk check identifies a new numerical estimate and a public function interface; I’ll have the required plan reviews check the draft before presenting it for approval.

One review found that the plan left two test expectations too vague and did not explicitly check the public documentation. I’ve specified those checks and will rerun the reviews against the revised plan.

**Measured:** The [plan](<project>/.cg-docs/plans/2026-11-27-poverty-depth-measure.md) is a draft. Validation found zero problems and zero warnings. Its contract and work record read:

# Poverty depth measure

The human approves this plan as it reads below. `cg.py approve` records their reply against this text, so a later change is an amendment, a dated line under `## Amendments`, and needs a new approval.

## Contract

### Goal

Package users can call `poverty_gap()` to obtain one weighted average household shortfall as a share of the poverty line, including zero for households at or above the line.

### Out of scope

Do not change `headcount()` or `read_survey()`, or return household-level gaps. Squared gaps and the average gap among poor households are deferred because they measure different things.

### Requirements

| ID | Requirement |
|---|---|
| R1 | Export and document `poverty_gap(dt, line = 3)` as a single weighted aggregate share using `welfare` and `weight` columns. |
| R2 | Count all households in the denominator and give households at or above the line a zero gap. |
| R3 | Accept finite numeric welfare, including zero and negative values. |
| R4 | Reject invalid data frames, missing or nonnumeric columns, nonfinite welfare, and empty, nonfinite or nonpositive weights. |
| R5 | Reject a line that is not one finite numeric value strictly greater than zero. |
| R6 | Preserve existing package behavior. |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1, R2, R3, R4, R5, R6 | `Rscript -e 'testthat::test_local(stop_on_failure = TRUE)'` | The suite exits nonzero: new tests must call the exported function and compare the default-line result for welfare 0 and 4 with weights 1 and 3 to 0.25 within 1e-12; compare welfare 2 and 4 with weights 1 and 3 at line 4 to 0.125 within 1e-12 (including the boundary); assert the public namespace exports the function and its help page documents its arguments and return; check negative welfare can give a gap above one; assert errors for each invalid input class and for zero, negative, nonfinite, nonscalar and nonnumeric lines; and retain the existing tests. The first example fails if weights are ignored or nonpoor households are excluded. |

What no check would catch: These finite examples cannot prove correctness for every possible numeric input, including extreme floating-point overflow, or verify that every reader understands the documentation.

### Boundaries

- Always: run the slice check; keep arithmetic expectations independent of the implementation; document the result as a share, not a percentage.
- Ask first: a new dependency, a change outside the listed files, or a change to the check or its tolerance.
- Never: change the existing headcount or survey reader; suppress a failing test; publish or return household-level gaps.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| inst/extdata/survey.csv | Public | Synthetic survey shipped in the package | Package version 0.0.1 | Package maintainers; individual owner not specified | Existing package tests may read it; no survey rows in evidence. |

Shape of the data: The survey has one row per household, keyed by unique `hhid`, with `welfare` and `weight` columns according to `read_survey()`. The estimate has households as observations, uses positive household weights, and covers all households supplied by the caller, including those at or above the line. Hand-built test inputs use the same observation and columns and are constructed in code.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | A documented, exported weighted poverty gap with validation and arithmetic examples | R/poverty_gap.R, tests/testthat/test-poverty_gap.R, man/poverty_gap.Rd, NAMESPACE | C1 | By code: implement the function, add testthat cases and generate or write its package documentation and export. |

## Open questions

| ID | About | Question | Recommended answer, with its trade-off | The human's answer |
|---|---|---|---|---|
| none | none | none | none | none |

**Measured:** The risk tier is elevated. Its recorded reasons are: `number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on`. The survey is cleared as Public; no dataset needs to stay closed during the planned work.

**Measured:** All five final reviews passed with no findings, and all were independent:

- **Contract:** Reviewed the plan contract only; no project code or data was run or opened.
- **Determinism:** Reviewed the plan’s steps and checks. No project code or data was run or opened.
- **Simplicity:** Reviewed the plan’s scope and slice. No project code or data was run or opened.
- **Domain:** Reviewed the planned estimate and input assertions. No project charter was found under `.cg-docs/`; the implementation and its outputs do not yet exist to inspect. Data remained closed.
- **Governance:** Reviewed the data register and tool declaration. No dataset was opened; the classification and tool approval were not independently assessed.

**Not checked:** The proposed test command has not been run, and the implementation does not yet exist. The verification profile has no Run or Doctor command.

Do you approve the plan as shown? A plain **yes** approves it and will be recorded under your name. I’ll take anything else as a change or a question. After approval, `/cg work` can carry out the slice.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I’ll add that boundary to the draft, then validate and review the revised plan before putting it back to you.

The new boundary is in the draft, and validation reports no problems or warnings. The independent reviews are nearly complete.

Four reviews have passed. I’m waiting for the domain review before asking for approval of the revised text.

**Measured:** I added this line to the Never list in the [draft plan](<project>/.cg-docs/plans/2026-11-27-poverty-depth-measure.md):

> Never: change any file under `data-raw/`.

Validation reports zero problems and zero warnings. The five independent reviews passed with no findings. They did not run project code or open data; the governance review did not independently assess the recorded classification or tool approval.

The plan remains a draft. The [Compound GPID plan playbook](~/.agents/skills/cg/playbooks/plan.md) says, “A correction is not a yes”: after a change, it requires the revised text to be checked and presented for approval again.

Do you approve the revised plan? A plain **yes** approves it and will be recorded under your name; I’ll take anything else as a change or a question.

[exit code: 0]

### H3 yes

> Yes.

I’ll record your approval with:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/plans/2026-11-27-poverty-depth-measure.md" --reply "Yes." --project "<project>"`

**Measured:** The [poverty depth plan](<project>/.cg-docs/plans/2026-11-27-poverty-depth-measure.md) is approved, including the boundary against changing files under `data-raw/`. Your approval is recorded.

The implementation has not started. Use `/cg work` to begin the approved slice.

[exit code: 0]

### The conformance record at the plan stage

plan P1 contract: PASS, independent review
  note: Reviewed the plan contract only; no project code or data was run or opened.
plan P3 determinism: PASS, independent review
  note: Reviewed the plan’s steps and checks. No project code or data was run or opened.
plan P6 simplicity: PASS, independent review
  note: Reviewed the plan’s scope and slice. No project code or data was run or opened.
plan P10 domain-lenses: PASS, independent review
  note: Reviewed the planned estimate and input assertions. No project charter was found under .cg-docs/; the implementation and its outputs do not yet exist to inspect. Data remained closed.
plan P12 governance: PASS, independent review
  note: Reviewed the data register and tool declaration. No dataset was opened; the classification and tool approval were not independently assessed.
missing: none
independent review: 5; self-review: 0


### W1 ask for the work

> $cg work Do the work of the approved plan.

I’ll use the Compound GPID guide to check the approved plan and carry out its work.

The approved plan has one slice left: implement and document `poverty_gap()` and verify the package suite.
I’ll proceed through its checks and stop at the boundaries specified in the plan.

Slice S1 adds the weighted aggregate, validation, tests, and documentation. Its permitted files are `R/poverty_gap.R`, `tests/testthat/test-poverty_gap.R`, `man/poverty_gap.Rd`, and `NAMESPACE`.

The survey file is recorded as Public and cleared for the existing tests. I’m applying the R package, analytical, and testing guidance alongside the guide’s work playbook.

The first test run stopped during R startup, before reaching the suite: the user startup profile passed an invalid thread count to `data.table`. I’ll run the approved command with that profile disabled for this process, then check the actual test failure.

The new tests first failed because the function and help page were absent. After implementation, the approved suite passed with 43 expectations and no warnings; the slice guard is clean.

The first independent reviews found a weakness in the help-page assertions and noted that dependency versions are not pinned. I’m recording those findings as returned and completing the remaining reviews.

An adversarial check found a real numerical limitation: very large finite weights can overflow the denominator and produce the wrong result. The review stage requires recording findings for your decision, so I’m leaving the implementation as reviewed.

**Measured:** `poverty_gap()` is implemented, exported, documented, and covered by tests. The approved check passed with 43 expectations, no warnings, and `guard: clean`. The successful run used `R_PROFILE_USER=/dev/null` because the normal R startup profile failed before the tests began.

**Measured:** Independent review found a correctness issue that needs a decision: with two equal weights of `1e308`, the weight sum overflows and the function returns `0` instead of `0.5`. See [the adversarial evidence](<project>/.cg-docs/evidence/2026-11-27-poverty-depth-measure/0005-20261127T064959Z-ad-hoc.json).

The other independent findings were:

- **Measured:** The [help-page test](<project>/tests/testthat/test-poverty_gap.R:13) searches for words anywhere in the page and does not establish that the argument and return sections contain descriptions.
- **Measured:** [DESCRIPTION](<project>/DESCRIPTION:1) has no dependency lockfile.
- **Measured:** The [work report](<project>/.cg-docs/work-reports/2026-11-27-poverty-depth-measure.md:41) has unlabelled, unlinked evidence claims and no AI-use statement.

The independent verifier verdicts were **FLAG** for contract, determinism, adversary, claims, domain, and governance; **PASS** for simplicity and language; and **INCONCLUSIVE** for verification because that reviewer did not rerun the suite or mutation checks. All nine verdicts are recorded.

**Measured:** Slice S1’s C1 check is verified; no slices remain. The [work report](<project>/.cg-docs/work-reports/2026-11-27-poverty-depth-measure.md) is completed and validates without warnings. The [plan](<project>/.cg-docs/plans/2026-11-27-poverty-depth-measure.md) remains approved, pending your decisions on the findings. Extreme floating-point cases were not exhaustively checked. Pre-existing uncommitted changes were left intact.

Would you like the overflow and documentation-test findings fixed before sign-off? The [work playbook](~/.agents/skills/cg/playbooks/work.md) says to leave review-stage findings unchanged for your decision.

[exit code: 0]

### The conformance record at the review stage

review P1 contract: FLAG, independent review
  finding: tests/testthat/test-poverty_gap.R:13: The approved C1 requires assertions that the help page documents the arguments and return, but these checks only search for words anywhere in the rendered page and would pass if the argument and return descriptions were removed. (P2; fix: assert the argument and value documentation sections contain 
  note: The survey data stayed closed.
review P3 determinism: FLAG, independent review
  finding: DESCRIPTION:1: The R environment is not pinned; the project has no R lockfile, so the package and its checks cannot be reproduced with fixed dependency versions. (P2; fix: create and maintain an R dependency lockfile.)
  note: I did not run the suite because it reads a data file that the verifier kickoff did not clear.
review P4 verification: INCONCLUSIVE, independent review
  note: I could not rerun C1 or test mutations because the suite reads a data file that the verifier kickoff did not clear. The verification profile also lists no Doctor command.
review P5 adversary: FLAG, independent review
  finding: .cg-docs/evidence/2026-11-27-poverty-depth-measure/0005-20261127T064959Z-ad-hoc.json: `Rscript -e "source(\"R/poverty_gap.R\"); print(poverty_gap(data.frame(welfare=c(0,4),weight=c(1e308,1e308))))"` prints `0`, although the two equal finite positive weights require a weighted share of `0.5`; the weight sum overflows. (P2; fix: scale weights before aggregation.)
  note: The probe used constructed inputs and did not read the survey.
review P6 simplicity: PASS, independent review
  note: The survey data stayed closed, so I did not run removal experiments against the full suite. The slice guard recorded a clean result.
review P7 claims: FLAG, independent review
  finding: .cg-docs/work-reports/2026-11-27-poverty-depth-measure.md:41: The claim that both calculated shares matched is not labelled measured and has no pointer to its evidence record. (P2; fix: label the claim and link the recorded check.)
  finding: .cg-docs/work-reports/2026-11-27-poverty-depth-measure.md:45: The claims about the failed initial test and successful run are not labelled or linked to evidence. (P2; fix: label the claims and link the relevant records.)
  note: The survey data stayed closed.
review P10 domain-lenses: FLAG, independent review
  finding: .cg-docs/evidence/2026-11-27-poverty-depth-measure/0006-20261127T065056Z-ad-hoc.json: Two equal finite positive weights produce a poverty gap of 0 instead of 0.5 because their sum overflows, silently producing an incorrect weighted statistic. (P0; fix: use numerically stable weighted aggregation and test extreme finite weights.)
  note: The survey data stayed closed; the check used constructed inputs. The verification profile has no input-assertion command.
review P11 language: PASS, independent review
  note: The survey data stayed closed.
review P12 governance: FLAG, independent review
  finding: .cg-docs/work-reports/2026-11-27-poverty-depth-measure.md:9: The work artifacts contain no AI-use statement identifying the tool, its contribution, and the reviewer. (P2; fix: attach an AI-use statement before sign-off.)
  note: The survey data stayed closed; its classification and the tool clearance were checked against the plan, configuration, and tier record.
missing: none
independent review: 9; self-review: 0

