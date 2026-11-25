### B1 setup

> $cg

I’ll use the cg guide to check the project’s current state and follow the playbook it selects.

The project is in setup: it has no cg configuration yet. I’ll inspect its files and installed packs, then present the setup for your approval.

I recommend setting up **core** and **lang-r**. Both are installed.

The project contains three R files, one CSV file, and three files without extensions. The R package imports `data.table`, so I recommend `lang-r.r-syntax=data.table-collapse`, the pack’s default. That setting is supported by [DESCRIPTION](<project>/DESCRIPTION) and the use of `fread()` in [read_survey.R](<project>/R/read_survey.R).

The draft verification profile is:

- **Run command:** not found.
- **Doctor command:** not found.
- **Outputs:** `read_survey()` returns a table; the existing tests check its expected columns and 20 rows, and that it rejects a non-positive weight. I did not run the tests or inspect the CSV.

One data file exists: `inst/extdata/survey.csv`. The package description calls it synthetic, but its classification and this agent’s read access need your decision.

The setup dry run says it would create:

- [.cg-docs/config.json](<project>/.cg-docs/config.json)
- [.cg-docs/verification.md](<project>/.cg-docs/verification.md)
- [AGENTS.md](<project>/AGENTS.md)
- [CLAUDE.md](<project>/CLAUDE.md)
- [.Rbuildignore](<project>/.Rbuildignore)

I inferred the R dialect from the package dependency and assumed the existing tests belong in the draft profile. No files have been changed.

**Do you approve this setup?** Please also provide the data rules, if known. You can copy and edit: `survey.csv: Public; Codex may read: Public; levels: Public, Internal, Restricted`. Unknown items can remain open.

The [setup playbook](~/.agents/skills/cg/playbooks/setup.md) requires the proposal to be confirmed before it writes: “Until the human confirms, you only read.”

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll apply the approved setup with the survey classified as Public and Codex approved to read Public data. The classification levels will remain open.

I’ll run `cg.py setup` with `core,lang-r`, the `data.table-collapse` setting, and those two data rules.

**Setup is complete.** Measured status is `phase: ready`, `stops: none`, with `lang-r.r-syntax=data.table-collapse` and `inst/extdata/survey.csv=Public`. Both expected packs are installed.

The project contains three R files and one CSV. The package has tests for the survey reader, but I found no Run or Doctor command and did not run the tests. The verification profile remains a draft.

Your confirmed data rules classify the survey as Public and allow Codex to read Public data. The organization’s full list of classification levels remains open.

Setup created [.cg-docs/config.json](<project>/.cg-docs/config.json), [.cg-docs/verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its selected playbook for this change.

You asked for a weighted household headcount function and a test against the toy survey’s expected value. I’ll inspect the survey and existing package code to define the checks and scope.

**Approval is needed before implementation.** The Compound GPID risk check has one “yes”: the new function will calculate a number that someone may use as an estimate.

The proposed scope is to add `headcount(dt, line = 3)` and a testthat check, leaving the survey reader and data unchanged. I’ll check that the toy survey returns approximately `0.153846`; a different result will fail the check. I’ll also check the strict “below the line” boundary and invalid weights.

May I proceed with that scope and those checks?

The hard stop comes from the selected [quick-work playbook](~/.agents/skills/cg/playbooks/quick.md), which says, “Any answer is yes. This is a hard stop” and requires a clear yes before continuing. The [cg skill](~/.agents/skills/cg/SKILL.md) directs me to follow that playbook.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll implement the function and its tests, then run the package checks and record the results. I’m using the R package development and testing guidance for the change.

The survey has the required welfare and weight columns. The function will validate its inputs before calculating the share, including rejecting missing or non-positive weights as agreed.

The first test run exposed a tolerance issue: testthat compared the rounded expectation using a relative tolerance. I’ve changed the test to compare the result at the six decimal places you supplied, and I’ll rerun the suite.

The test suite now passes, including the toy survey, boundary, and invalid-weight checks. I’ll check the package as an installed artifact and finish the work record.

**Implemented `headcount(dt, line = 3)`** and exported it. It returns the weighted share of households whose welfare is strictly below the line and rejects invalid weights.

Measured: the testthat suite passed all 8 checks, including the toy survey result of **0.153846** at six decimal places, the line boundary, and invalid weights. The package built successfully. `R CMD check --no-manual` completed with one warning: the existing `read_survey` function lacks package documentation.

The [work report](<project>/.cg-docs/work-reports/2026-11-25-weighted-headcount.md) remains **in progress** because of that warning. The self-review found the project environment is not pinned; an independent review was not performed. The verification profile has no Run or Doctor command, and the installed Compound GPID tool has no repro or guard command.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll inspect the survey data and existing package conventions, then implement the household count.

I’m using the R package development guidance to match the project’s conventions and document the function.

The survey reader returns one row per household, so the count can be the number of rows. I’ll expose that as an unweighted count and allow an empty survey to return zero.

Added `household_count(dt)`, which returns the unweighted number of rows in a survey with one row per household. It returns `0` for an empty data frame.

The bundled survey has 20 households. All 12 package tests pass.

[exit code: 0]
