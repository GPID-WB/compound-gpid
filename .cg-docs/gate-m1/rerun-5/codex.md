### B1 setup

> $cg

I’m using the cg guide to check the project’s current state and follow its next playbook.

The project is an R package, and the R pack is installed. I’ll inspect its package files and existing checks to prepare the setup proposal; I’ll leave the survey data unopened.

**I recommend setting up this project with the installed `core` and `lang-r` packs**, using `lang-r.r-syntax=data.table-collapse`. The package imports `data.table` ([DESCRIPTION](<project>/DESCRIPTION:9)); that setting is also the R pack’s default.

**Draft verification profile:**

- **Run command:** not found.
- **Doctor command:** not found.
- **Output:** `read_survey()` returns a table of households. The existing checks expect 20 rows and three named columns for the bundled survey, and an error for a non-positive weight ([tests](<project>/tests/testthat/test-read_survey.R:1)). An independent validation source was not found.
- **Evidence location:** not found; to be established.

**Measured:** the file listing contains three `.R` files, one `.csv`, one `.Rd`, and three files without extensions. There is one data file: `inst/extdata/survey.csv`. The package describes it as synthetic, but its organizational classification still needs your declaration. I did not open it or run the checks.

**Inferred assumption:** the existing `data.table` import is enough to use the pack’s default dialect. The verification profile will remain a draft because no end-to-end Run command was found.

The setup dry run says it would create these files:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

Please give the data rules and say whether you approve this setup proposal. You can copy and edit this example:

> Yes, approve the proposal. `inst/extdata/survey.csv`: Public. Codex may read up to Public. Classification levels, from least to most restricted: Public; Internal; Restricted.

You can leave any data rule unknown; it will remain open and the file will be treated as restricted.

The [setup playbook](~/.agents/skills/cg/playbooks/setup.md) requires confirmation before writing: “Until the human confirms, you only read” and “Only a clear yes is approval.”

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the survey as Public and Codex as approved to read Public data. The organization’s classification levels remain open because they weren’t provided.

I’ll run:

```sh
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Codex=Public" --project "<project>"
```

Setup is complete. **Measured:** the guide reports `phase: ready`, `stops: none`, and `lang-r.r-syntax=data.table-collapse`. Both expected packs are installed.

You confirmed that the synthetic survey is Public and that Codex may read Public data. The organization’s classification levels remain open.

Setup created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The verification profile remains a draft: no Run or Doctor command was found. The existing package checks were identified but not run, and the survey data was not opened.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’m using the Compound GPID guide to check the project’s state and follow its selected playbook.

You asked for a weighted household headcount function and a test against 0.153846. I’ll inspect the existing survey and package code to identify the scope and checks; other calculations will stay untouched.

**Approval is needed before implementation.** The [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) says: “Any answer is yes. This is a hard stop.” Risk line 1 is yes because `headcount()` will calculate a statistic that someone may read.

**Proposed work:** Add `headcount(dt, line = 3)` to calculate the share of household weight with welfare strictly below the line, and add a testthat check. Existing survey-reading behavior and other calculations are out of scope.

**Checks:** Run the package tests and compare the toy-survey result with your independently supplied expectation, 0.153846. A test failure or a result outside the test’s numerical tolerance would mean the change fails verification.

May I proceed with that scope and those checks?

Measured: No files have been changed. The project status reports four existing untracked entries.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll implement the approved calculation and tests, then record the checks and self-review required by the guide. I’m also using the R package development and testing guidance for the package changes.

The function now checks its inputs and counts welfare strictly below the threshold. I’ve added a separate weighted boundary example alongside the toy-survey check; I’ll run the package checks and generate the public documentation.

The package tests pass, and an installation into a temporary library returns 0.153846154 for the bundled survey. The initial assertion exposed a tolerance mismatch with the six-decimal expectation, so the test now compares at the precision you supplied.

Implemented and exported [`headcount(dt, line = 3)`](<project>/R/headcount.R). It returns the weighted share of households whose welfare is strictly below the line and rejects missing or invalid inputs.

**Measured:** The toy survey returns **0.153846154**, matching your expected 0.153846 to six decimal places. `Rscript --vanilla -e 'devtools::test()'` passed all 10 checks. A temporary-library installation also verified the exported function and toy-survey result.

The [work report](<project>/.cg-docs/work-reports/2026-11-25-weighted-household-headcount.md) records the checks and self-review. The review passed P4 and P6; P3 was flagged because the project has no environment lockfile. A full R CMD check and mutation testing were not run. The existing R startup profile caused an error, so verification used a clean R session.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll inspect the project’s survey data structures and existing conventions, then add the household-count function and verify it.

I’m using the R package development guidance to match the project’s conventions. I’ll also check the Compound GPID status before making changes.

The survey reader returns one row per household, so the count can use the row count directly. The bundled survey contains 20 households; I’ll make the function accept a survey data frame and default to the bundled survey.

Added `n_households()`, which counts rows in a survey data frame and defaults to the bundled survey. The bundled survey has **20 households**.

The function is exported and documented. All 14 package tests pass. `air` was unavailable, so I couldn’t run its formatter.

[exit code: 0]
