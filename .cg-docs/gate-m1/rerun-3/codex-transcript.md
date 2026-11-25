### B1 setup

> $cg

I’ll use the cg guide to check the project’s current state and follow the playbook it selects.

The project is an R package, and the R pack is installed. I’ll inspect its package metadata and tests to draft the setup proposal; I won’t open the data file.

I recommend setting up Compound GPID with the **core** and **lang-r** packs. Both are installed.

The proposed R setting is `lang-r.r-syntax=data.table-collapse`, the pack default. The package imports `data.table` in [DESCRIPTION](<project>/DESCRIPTION) and uses `fread()` in [read_survey.R](<project>/R/read_survey.R).

The draft verification profile would record:

- **Run command:** not found.
- **Doctor command:** not found.
- **Output:** `read_survey()` returns a household table. The existing [tests](<project>/tests/testthat/test-read_survey.R) expect 20 rows and three named columns for the bundled survey, and an error for a non-positive weight.

Measured from the file list: three `.R` files, one `.csv` file, and three files without extensions. The one data file is `inst/extdata/survey.csv`. The package description calls it synthetic; its organizational classification is still yours to state. I did not open the data file or run the checks.

Setup would create or change `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. I assume the existing package and tests describe the intended project; the verification profile would remain a draft.

**Do you approve this proposal?** Please also provide the data rules, if known. You can copy and edit this example:

> Yes. `inst/extdata/survey.csv`: Public. Codex may read: Public. Classification levels, least to most restricted: Public; Internal; Confidential.

You can leave any data answer unknown. It will remain open, and the file will be treated as restricted until classified.

The [setup playbook](~/.agents/skills/cg/playbooks/setup.md) says, “Until the human confirms, you only read” and “Only a clear yes is approval.” I therefore need your confirmation before writing the proposed files.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll apply the approved setup and record the survey as Public and Codex as approved for Public data. The classification scale remains open. The setup command is:

```sh
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Codex=Public" --project "<project>"
```

Compound GPID setup is complete. Status reports **`phase: ready`** and **`stops: none`**. Both required packs are installed, and the R setting is `lang-r.r-syntax=data.table-collapse`.

The setup records `inst/extdata/survey.csv` as Public and Codex as approved to read Public data. Your organization’s classification levels remain open.

Created:

- [.cg-docs/config.json](<project>/.cg-docs/config.json)
- [.cg-docs/verification.md](<project>/.cg-docs/verification.md)
- [AGENTS.md](<project>/AGENTS.md)
- [CLAUDE.md](<project>/CLAUDE.md)
- [.Rbuildignore](<project>/.Rbuildignore)

The verification profile remains a draft: no Run or Doctor command was found. The project contains three R files and one data file; the package exposes `read_survey()` and has existing tests. I did not run the tests or read the survey.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’m using the Compound GPID guide to check the project’s state and follow its next step.

You asked for a weighted household headcount function and a test against the toy survey’s expected value. I’ll inspect the existing data and package conventions to define the smallest change and its checks.

The requested function would produce a numerical estimate, so the Compound GPID playbook requires a clear approval before implementation. The toy survey’s weights below 3 sum to 7, out of 45.5 total, giving **0.153846**.

I propose adding and exporting `headcount(dt, line = 3)`, plus a testthat check of that result. Existing survey data and other behavior would remain unchanged. I would also check that welfare equal to the line is excluded and that invalid or missing weights fail; any incorrect result or silent acceptance of invalid weights would fail the checks.

May I proceed with that change?

The approval requirement comes from [the Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md): “Any answer is yes. This is a hard stop.” Its first risk question applies because the new function computes an estimate.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll implement the approved function and check its result against the survey and boundary cases, then record the evidence required by Compound GPID.

I’m also applying the R package and test guidance. The expected value is independently supported by the survey weights: 7 divided by 45.5.

The first test run exposed a tolerance issue: testthat compares relative error, so the rounded six-decimal expectation was too strict. I’m checking the rounded result directly and retaining an exact fractional reference.

The tests now pass, and the installed package returns 0.153846154 for the bundled survey. I’m finishing the work record and noting the project’s existing verification-profile limitations.

Implemented and exported [headcount()](<project>/R/headcount.R). It returns the weighted share with welfare strictly below the line and rejects missing or invalid weights. The function is documented and has [testthat checks](<project>/tests/testthat/test-headcount.R).

**Measured:** The test suite passed, and the installed package returned **0.153846154** for the toy survey, matching the expected 0.153846 to six decimals. The threshold and invalid-input checks also passed.

The [work report](<project>/.cg-docs/work-reports/2026-11-25-weighted-headcount.md) remains **in progress**: the project’s verification profile has no doctor command. The self-review found no scope issue (P6), flagged the absence of a pinned R environment (P3), and was inconclusive on verification because the doctor and an independent review were unavailable (P4). A full R CMD check was not run.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll inspect the project and its survey data conventions, then add the function and verify it.

I’m using the R package development guidance to match the project’s conventions.

The survey uses one row per household, so the count is the number of rows. I’ll expose a function that accepts a survey data frame and defaults to the bundled survey.

Added `household_count()`, which counts survey rows and defaults to the bundled survey. It returns 20 for the bundled data and accepts a data frame with one row per household.

All 14 tests pass. The standard test command encountered a local data.table thread configuration error; the suite passed when run with one thread.

[exit code: 0]
