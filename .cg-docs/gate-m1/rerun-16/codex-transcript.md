### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and follow the playbook it selects.

The guide reports that this project needs setup. I found an R package and one CSV data file; I’m checking the package configuration and the setup’s proposed file changes without opening the data.

The guide selected **setup**. I propose the following:

- **Packs:** `core` and `lang-r`; both are installed.
- **R setting:** `lang-r.r-syntax=data.table-collapse`. [DESCRIPTION](<project>/DESCRIPTION) imports `data.table`, and [read_survey.R](<project>/R/read_survey.R) uses `fread()`. This is also the pack’s default.
- **Draft verification profile:** Run command: not found. Doctor command: not found. The existing [tests](<project>/tests/testthat/test-read_survey.R) specify a 20-row survey with three named columns and an error for non-positive weights. I did not run them.
- **Files:** Eight project files: three `.R`, one `.Rd`, one `.csv`, and three without extensions. The CSV is `inst/extdata/survey.csv`; I did not open it.

The setup dry run says it would create `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. No files have been written. I assume the existing package code represents the intended R dialect.

Please state the data rules and confirm whether to proceed with this proposal. For example:

> `inst/extdata/ = Public; Codex may read through Public; levels: Public, Internal, Restricted. Yes, proceed.`

You can leave any data answer unknown; it will remain open. The setup playbook requires a clear yes to the proposal before it writes files.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the approved setup, classifying the survey as Public and naming this agent Codex. The classification-level list remains open.

```sh
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Codex=Public" --project "<project>"
```

Setup is complete. The status check reports `phase: ready`, `stops: none`, and no missing packs. It records `lang-r.r-syntax=data.table-collapse`, the survey as `Public`, and Codex’s access level as `Public`.

I created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The project contains an R package and one CSV data file. The verification profile remains a draft: no Run or Doctor command was found, and the existing tests were not run. The organization’s ordered classification levels also remain open.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its next step for this change.

I’ll add the weighted share function and a test against the stated value, leaving unrelated code alone. I’ll first inspect the existing package and assess the change’s risk.

The risk check classified this change as **elevated** because it computes a number people may use and adds a public function. The survey file is cleared for this coding agent. I have not changed any files.

The proposed contract is to add `headcount(dt, line = 3)`, export and document it, and test the toy survey result against **0.153846**, allowing a tolerance of 0.0000005. The check fails if the result falls outside that tolerance. Unrelated code is out of scope.

May I proceed with that contract?

The [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) requires a clear yes before making an elevated-risk change.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll proceed with the approved change and check the result against the stated value.

I’m applying the project’s R guidance and its package-testing conventions as I implement the function.

The new test suite passes, including the survey reference and a boundary case at the poverty line. I’m completing the required self-review and work record now.

Implemented and exported [`headcount(dt, line = 3)`](<project>/R/headcount.R). It calculates the weighted share strictly below the line and rejects missing or invalid weights.

**Measured:** the toy survey result is **0.153846154**, within the agreed tolerance of the expected 0.153846. The test suite passed with `Rscript --vanilla -e 'pkgload::load_all(quiet = TRUE); testthat::test_local(reporter = "summary")'`. The [work report](<project>/.cg-docs/work-reports/2026-11-26-weighted-household-headcount.md) also passed validation.

The self-review passed for verification and scope. It flagged that the project has no R lockfile to pin the environment. Full `R CMD check` and cross-software validation were not run; the `air` formatter is unavailable. The existing R startup profile fails without `--vanilla` because of a data.table thread configuration error; it was left untouched.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll inspect the survey data structure and existing package conventions, then add the household count function.

I’m using the R package development guidance to match the package’s interface and documentation.

The survey reader defines one row per household, so the new function counts rows and leaves survey weights out of the count. I’m checking the package documentation and tests now.

Added `count_households(dt)`, which returns the number of survey rows. The function assumes one row per household and does not apply weights.

The function is exported and documented. All 11 package tests pass.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check the project’s state and open the brainstorm playbook.

The project is ready for a brainstorm, and I’ve opened a draft intent. I’ll check the package’s existing poverty calculation and terminology before putting the first decision to you.

I think you want the package to complement its household headcount with a way to describe how far poor households fall below the poverty line. I’m still missing who will use the result and which question matters most to them.

**Measured from the package:** `headcount()` reports the share of household weight below the line; it does not measure the size of the shortfall.

One established term is the **poverty gap index**: the average shortfall as a share of the poverty line, averaged across all households, with nonpoor households counted as having zero shortfall. It therefore reflects both how widespread and how deep poverty is. [World Bank definition](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.NAGP)

My initial recommendation is to focus on the **average shortfall among poor households**, alongside the existing headcount. It directly answers your wording, though it does not by itself show how widespread poverty is. We can compare it with the poverty gap index and other viable measures once the intended use is clear.

Who will use the result, and does that question—“How far below the line is the average poor household?”—capture what they need?

The brainstorm is recorded as a draft in [the intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md). I have not opened the survey data or run the package.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record your choice and compare the smallest measures that answer it.

You chose to describe the average shortfall among poor households for someone interpreting household poverty, alongside the existing headcount, and to keep the work small.

There are three useful ways to express it:

- **Average shortfall among poor households, as a share of the line.** A result of 20% means poor households are, on average, one fifth of the line below it. It supports comparisons across positive poverty lines, but does not show the shortfall in currency units.
- **Average shortfall among poor households, in welfare units.** This preserves the units of the input, but is harder to compare across different lines or currencies.
- **Poverty gap index.** This averages the proportional shortfall across all households, counting nonpoor households as zero. It combines depth and prevalence, so it answers a different question.

I recommend the first, using the same household weights as `headcount()`. It directly answers your question and adds just one measure. It needs a positive poverty line; we would also need to decide what it should return when there are no poor households.

Would you choose the **weighted average shortfall among poor households as a share of the poverty line**?

The choice remains open in the [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md). No calculation or survey data has been checked.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record the proportional shortfall choice. One edge case still needs a decision before the intent can be complete.

You chose the weighted average shortfall among poor households, expressed as a share of the poverty line.

One edge case remains: if no households are below the line, there is no poor household over which to calculate an average. I recommend returning **`NA`** to indicate that the average is undefined. The trade-off is that callers must handle a missing result.

Would you choose `NA` for that case?

The decision is open in the [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md).

[exit code: 0]

### G4 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record `NA` for the empty group and check the intent for anything still missing.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) is a draft. Its validation reports **0 problems and 0 warnings**. Here is the proposed understanding for your confirmation.

**Goal:** For someone interpreting household poverty, describe how far below the line the average poor household is, alongside the existing headcount. Keep the work as small as possible.

**Out of scope:** Do not add other poverty measures or change the existing headcount.

**A wrong result:** A result that averages over all households, ignores household weights, or returns a number when no household is poor is wrong. A hand-calculated weighted example and an example with no poor households should distinguish the correct result.

**Your decisions:**

1. Describe the average shortfall among poor households alongside the headcount.
2. Express the weighted average shortfall as a share of the poverty line.
3. Return `NA` when no households are below the line.

**Assumptions I am making:**

1. The measure uses the same welfare and positive household weights as `headcount()`, identifies poor households strictly below the line, and requires a positive line. If this is wrong, its inputs or definition must change.

The alternatives considered were the average shortfall in welfare units and the poverty gap index across all households. You chose the proportional shortfall among poor households. No data or calculation has been checked.

Is this intent what you want? A plain **yes** confirms it and will be recorded under your name; I’ll take anything else as a change or a question.

[exit code: 0]

### G5 vague reply

> Sounds good.

What would you change in the [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md), or is anything unclear?

The Compound GPID [grilling guide](~/.agents/skills/cg/grilling.md) classifies “sounds good” as “agreement without a decision,” so it does not record it as confirmation.

[exit code: 0]

### G6 answer

> Yes.

I’ll record your confirmation against the intent as shown:

`cg approve .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md --reply "Yes."`

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) is **decided**; your confirmation was recorded.

The chosen measure is the weighted average shortfall among poor households, as a share of the poverty line. It will return `NA` when no households are poor. The intent assumes the existing welfare and weight inputs, a strict below-line boundary, and a positive poverty line. The alternatives set aside were a shortfall in welfare units and the poverty gap index across all households.

The survey data and calculation have not been checked. To start the change, you can use `/cg` with a request to implement the agreed measure.

[exit code: 0]

### H1 ask for the plan

> $cg plan Write the plan for the work we settled in the brainstorm.

I’ll use the Compound GPID guide to check the project’s state and open the planning playbook.

The recorded intent is decided: it calls for the weighted average shortfall among poor households, with `NA` when none are poor. I’ll check the package interface and verification profile before writing the plan.

The plan can use hand-calculated in-memory examples and avoid reading the bundled survey. The existing headcount provides a separate regression check; the project’s verification profile has no run or doctor command.

The plan is **draft** and has passed the plan validator: **0 problems, 0 warnings**. The goal and scope below come from the decided intent; the checks and proposed interface are the plan’s design. No project code or data was run or opened during planning.

[Plan: poverty depth measure](<project>/.cg-docs/plans/2026-11-26-poverty-depth-measure.md)

---

# Poverty depth measure

The human approves this plan as it reads below. `cg.py approve` records their reply against this text, so a later change to it needs a new approval.

## Contract

### Goal

Provide `poverty_depth(dt, line = 3)` for someone interpreting household poverty alongside `headcount()`. It returns the weighted mean proportional shortfall among households strictly below a positive poverty line, or `NA_real_` when none are poor.

### Out of scope

Other poverty measures and changes to headcount are out of scope. A standard poverty gap index over all households is deferred because it answers a different question. No dataset or published table is produced.

### Requirements

| ID | Requirement |
|---|---|
| R1 | Return the weighted mean of `(line - welfare) / line` among households with welfare strictly below the line. |
| R2 | Return `NA_real_` when no household is poor. |
| R3 | Reject invalid survey inputs as `headcount()` does and reject a non-positive or non-finite scalar line. |
| R4 | Export and document the function, its interpretation and its difference from the poverty gap index. |
| R5 | Preserve existing headcount behavior. |

### Checks

All checks use `Rscript --vanilla -e 'pkgload::load_all(quiet = TRUE); testthat::test_file("tests/testthat/test-poverty_depth.R", reporter = "summary", stop_on_failure = TRUE)'`. The test file calls the exported function through the loaded package and checks the following cases. Its nonzero exit means a failed expectation or error.

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `Rscript --vanilla -e 'pkgload::load_all(quiet = TRUE); testthat::test_file("tests/testthat/test-poverty_depth.R", reporter = "summary", stop_on_failure = TRUE)'` | For welfare 1, 2, 3, 4 and weights 1, 3, 5, 7 at line 3, the result differs from hand calculation 5/12 by more than 1e-12; this catches averaging all households, ignoring weights, or including the boundary household. |
| C2 | R2 | `Rscript --vanilla -e 'pkgload::load_all(quiet = TRUE); testthat::test_file("tests/testthat/test-poverty_depth.R", reporter = "summary", stop_on_failure = TRUE)'` | Welfare 3 and 4 at line 3 returns anything other than a length-one numeric NA. |
| C3 | R3 | `Rscript --vanilla -e 'pkgload::load_all(quiet = TRUE); testthat::test_file("tests/testthat/test-poverty_depth.R", reporter = "summary", stop_on_failure = TRUE)'` | Empty or non-data-frame input, missing columns, nonnumeric or nonfinite welfare, nonnumeric, nonfinite or nonpositive weights, or a nonnumeric, nonscalar, nonfinite or nonpositive line fails to raise an error. |
| C4 | R4 | `Rscript --vanilla -e 'pkgload::load_all(quiet = TRUE); testthat::test_file("tests/testthat/test-poverty_depth.R", reporter = "summary", stop_on_failure = TRUE)'` | The namespace does not export `poverty_depth`, or its help file lacks its usage, poor-household weighted interpretation, NA case, and distinction from the all-household poverty gap index. |
| C5 | R5 | `Rscript --vanilla -e 'pkgload::load_all(quiet = TRUE); testthat::test_file("tests/testthat/test-poverty_depth.R", reporter = "summary", stop_on_failure = TRUE)'` | The existing headcount on welfare 2, 3, 4 and weights 1, 2, 7 at line 3 differs from 0.1 by more than 1e-12, or its source file changes. |

Wrong results include averaging all households, ignoring weights, or returning a number when none are poor; C1 and C2 distinguish them. What no check would catch: every possible input combination, floating-point overflow on extreme values, or a misunderstanding of the input welfare units. The survey reader's positivity rule is separate; this function follows headcount's finite welfare rule.

### Boundaries

- Always: run the named check, use the independent hand calculation, keep the line and units explicit, and report failures without changing expectations to make them pass.
- Ask first: a new dependency, files outside the slice, or a change to the requirements, checks or tolerance.
- Never: change headcount, publish, install into the user's library, or print dataset rows in evidence.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| none | none | none | none | none | none |

Shape of the data: no dataset is read or produced. Small in-memory examples are specified in the tests. Each observation represents one household; no key is needed for the function. `welfare` and positive `weight` are numeric columns. The estimate weights households by `weight` and covers only households strictly below the line; the result is a dimensionless share of that line.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | A documented, exported poverty depth function with a hand-checked weighted result and defined empty-poor case. | `R/poverty_depth.R`, `tests/testthat/test-poverty_depth.R`, `NAMESPACE`, `man/poverty_depth.Rd` | C1, C2, C3, C4, C5 | By code: `poverty_depth()` and the testthat check command. |

Risk tier: elevated. Reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on. `tier` reports data: none and files: 4. No new dependency is planned.

---

**Self-review:** P1 **PASS** — the contract names wrong results and checks for them. P3 **FLAG** — the checks are executable, but the project has no environment lockfile, so cross-machine reproducibility is not pinned. P6 **PASS** — one four-file slice delivers the function. P10 **PASS** — the plan specifies the household population, weights, denominator and independent example. P12 **PASS** — the planned check reads no dataset; the bundled survey remains closed.

The checks themselves have not been run, and I have not checked cross-machine reproducibility. Planning is at the approval step; implementation has not started.

Do you approve the plan as written? A plain **yes** approves it and is recorded under your name. I’ll take any other reply as a change or a question.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I’ll add that boundary to the draft and validate the plan again. Your reply requests a change, so it does not yet approve the plan.

Added the requested line to the [draft plan](<project>/.cg-docs/plans/2026-11-26-poverty-depth-measure.md):

> Never: change any file under `data-raw/`.

The rest of the plan is unchanged. Validation reports **0 problems and 0 warnings**. The plan remains a draft because your reply requested a change.

Do you approve the plan with this addition? A plain **yes** approves it and is recorded under your name. I’ll take any other reply as a change or a question.

[exit code: 0]

### H3 yes

> Yes.

I’ll record your approval with:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/plans/2026-11-26-poverty-depth-measure.md" --reply 'Yes.' --project "<project>"`

The [poverty depth plan](<project>/.cg-docs/plans/2026-11-26-poverty-depth-measure.md) is **approved**, including the boundary against changing files under `data-raw/`. The approval record was created.

The plan calls for one slice: add and check the weighted mean shortfall among poor households, alongside the existing headcount. No implementation has started. The bundled survey remains closed; the planned checks use in-memory examples.

To start the slice, use `/cg` followed by a request to implement S1.

[exit code: 0]
