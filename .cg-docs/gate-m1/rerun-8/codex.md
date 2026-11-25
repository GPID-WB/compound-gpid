### B1 setup

> $cg

I’ll use the cg guide to check the project’s state and follow the playbook it selects.

The project is an R package, and both packs it calls for are installed. I’ll check its package files and existing tests to prepare the setup proposal; I won’t open the data file.

**I recommend setting up this project with the `core` and `lang-r` packs.** Both are installed.

The project has three R files, one R documentation file, one CSV file, and three extensionless package files. The R setting I recommend is `lang-r.r-syntax=data.table-collapse`: `DESCRIPTION` imports `data.table`, and [read_survey.R](<project>/R/read_survey.R) uses `fread()`. The setting is also the pack’s default.

The draft verification profile is:

- **Run command:** not found.
- **Doctor command:** not found.
- **Identified output:** `read_survey()` returns a table; the existing tests check its column names and row count and reject a non-positive weight. I did not run the tests.

There is one data file, [survey.csv](<project>/inst/extdata/survey.csv). I did not open it. Its classification remains unknown until you state it.

The setup dry run says it would create:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

I assume this folder is the project root and would record the coding agent as **Codex**. The findings above are measured from the project files; the recommended setting is an inference. No files have been changed.

**Do you approve this setup proposal?** Please also provide the data rules you know. You can copy and complete this example:

> Yes. `inst/extdata/survey.csv`: Public. Codex may read up to: Public. Classification levels, from least to most restricted: Public; Internal; Restricted.

You can leave any unknown data rule open. The setup playbook requires a clear yes before it writes the proposed files.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the survey as Public and Codex as approved to read Public data. The classification-level order remains open.

I’ll run the confirmed setup with `--packs "core,lang-r"`, `--setting "lang-r.r-syntax=data.table-collapse"`, `--data "inst/extdata/survey.csv=Public"`, and `--approved-tool "Codex=Public"`, then fill the verification draft and check status.

Setup is complete. **Measured status:** `phase: ready`, `stops: none`, and no packs are missing. The recorded setting is `lang-r.r-syntax=data.table-collapse`; the survey is classified Public, and Codex is approved to read Public data.

The project contains three R files, one R documentation file, one CSV data file, and three extensionless package files. I found no Run or Doctor command. The verification profile remains a draft, and the organization’s ordered classification levels remain open. I did not run the tests or open the data file.

Setup created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its next step for this change.

The requested function will calculate a weighted household share, and the test will check the toy survey against 0.153846. I’ll inspect the existing survey and package structure to identify the precise scope and checks. I’m also using the R package and testing guidance for this work.

**Approval is needed before implementation.** The requested function computes a number someone will read, so risk line 1 is yes. The other risk lines appear to be no; the toy survey is classified Public.

The proposed change is to add `headcount(dt, line = 3)` and a testthat check, leaving the existing survey reader and data unchanged. I would check that the toy survey returns **0.153846 to six decimal places**, and test that the function uses weights and excludes households exactly on the line. A mismatch would mean the check failed.

Do you approve this contract?

The [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) requires this pause: “Any answer is yes. This is a hard stop.” It says to continue only after a clear yes. No files have been changed.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll proceed with the approved calculation and checks. I’ll first refresh the Compound GPID state, then implement and verify the function.

The survey’s weights give an independent reference of 7 / 45.5, which rounds to 0.153846. R’s normal startup fails on a local thread setting, so I’ll run the checks with `--vanilla`.

The implementation is in place. The first test run exposed that testthat applies the numeric tolerance relatively here; I’m changing the assertion to compare at the six decimal places you specified, while keeping the expected value unchanged.

Implemented `headcount(dt, line = 3)` in [R/headcount.R](<project>/R/headcount.R). It returns the weighted share below the line and checks for invalid inputs. The function is exported and documented.

**Measured:** the toy survey result rounds to **0.153846**, as expected. The test suite passed all 8 checks, including tests for weights and a household exactly on the line. The first comparison used a relative tolerance that was too strict; I changed it to compare at the requested six-decimal precision without changing the expected value.

The self-review found that the project has no lockfile. The Compound GPID `repro` and `guard` commands and the `air` formatter were unavailable; a package-wide `R CMD check` was not run. Details are in the [work report](<project>/.cg-docs/work-reports/2026-11-25-weighted-household-headcount.md).

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I’ll inspect the survey data structures and existing package conventions, then implement and verify the household count. I’m using the R package development guidance for this change.

The survey reader returns one row per household, so the requested count is the unweighted number of rows. I’ll expose that as a separate function and keep the existing weighted poverty headcount intact.

Added `household_count(dt)` to count survey households. It expects one row per household and returns the unweighted row count; `household_count(read_survey())` returns **20**.

The full test suite passed: 12 tests, no failures. Documentation was added and the function exported. `air` was unavailable, so automatic formatting was not run.

[exit code: 0]
