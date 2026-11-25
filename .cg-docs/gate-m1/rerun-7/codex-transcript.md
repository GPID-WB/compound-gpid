### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and follow the playbook it selects.

The project is an R package, and the R pack is installed. I’ll inspect its scripts and existing checks; I’ll identify the data file by name without opening it.

I recommend setting up this project with **core** and **lang-r**. Both packs are installed.

- **R setting:** `lang-r.r-syntax=data.table-collapse`. [DESCRIPTION](<project>/DESCRIPTION) imports `data.table`, and [read_survey.R](<project>/R/read_survey.R:7) uses `fread()`. The code does not show `collapse` use; this is also the pack’s default.
- **Draft verification profile:** Run command: **not found**. Doctor command: **not found**. The package has testthat checks for survey columns, row count, and invalid weights, but I found no documented command for producing an output. I did not run the checks.
- **Files found:** Three `.R` files, one `.Rd` file, one `.csv` file, and three files without extensions. The data file is `inst/extdata/survey.csv`. I identified it by name and did not open it.

The setup dry run says it would create:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

I assumed the R pack’s default dialect fits the existing code. The data rules still need your decision; the package description calls the survey synthetic, but that does not establish its classification.

Please provide the data rules and say **yes** if you approve this setup proposal. You can copy and fill in:

```text
inst/extdata/survey.csv classification: Public
Highest classification Codex may read: Public
Classification levels, least to most restricted: Public; Internal; Confidential
Setup proposal: yes
```

You can leave any classification answer unknown. The [setup playbook](~/.agents/skills/cg/playbooks/setup.md) requires confirmation before it writes: “Until the human confirms, you only read.”

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the approved packs, R setting, and Public data rule. The classification-level order remains open because you haven’t specified it.

Compound GPID setup is complete. The measured status is **ready**, with no stops or missing packs. The R setting is `data.table-collapse`, and `inst/extdata/survey.csv` is recorded as Public. Codex is approved to read Public data.

The project contains three R files and one CSV data file. I found no documented command for producing outputs or checking the environment. The [verification profile](<project>/.cg-docs/verification.md) remains a draft; I did not run the package tests or open the data.

Setup created [config.json](<project>/.cg-docs/config.json), the verification profile, [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore). The organization’s ordered classification levels remain open.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’m using the Compound GPID guide to check the project’s state and follow its next step.

You asked for a weighted household poverty share and a test against the toy survey’s expected value. I’ll inspect the existing code and survey setup to define the change and its checks.

The requested function would calculate a new number that someone can read, so **risk line 1 is yes**. The toy survey is classified Public in the project status. The other risk lines appear to be no, based on the files inspected.

Proposed contract:

- **Goal:** Add `headcount(dt, line = 3)` to calculate the sum of weights for households with welfare strictly below the line, divided by the sum of household weights.
- **Out of scope:** Changes to the survey data or existing `read_survey()` behavior.
- **Checks:** Run a testthat check against `0.153846` with an absolute tolerance of `0.0000005`; a larger difference fails. Also check that welfare equal to the line is excluded and that invalid weights or missing welfare cause an error.

May I proceed with this contract?

The [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) requires this pause: “Any answer is yes. This is a hard stop.” Its instruction says to continue only after a clear yes.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll implement the agreed calculation and checks, then compare the result with your reference value and record the evidence.

The toy survey returns 0.1538462, within the agreed tolerance, and the test suite passes. I’m checking the package-facing installation and completing the work record.

Implemented `headcount(dt, line = 3)` and exported it from the package. It returns the weighted share of households whose welfare is strictly below the line and rejects missing welfare or invalid weights.

**Measured:** The toy survey returns **0.1538462**, within the agreed tolerance of 0.153846. The testthat suite passed, including checks for the boundary, weights, and invalid inputs. Package installation into a temporary library also passed.

The work report is at [weighted household headcount](<project>/.cg-docs/work-reports/2026-11-25-weighted-household-headcount.md). Self-review found the existing project has no R lockfile; the verification review remains inconclusive because the project has no Doctor command and the tests were not run against deliberately broken code. Ordinary R startup also failed in the existing user profile, so checks used vanilla R or disabled that profile.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I’ll inspect the survey data and existing package conventions, then add the function and verify it against the available tests. I’m using the R development guidance for this work.

The survey reader guarantees one row per household, so the requested count is the number of rows. The bundled survey contains 20 households; I’ll expose a small function that also works with other survey data frames.

Added [`household_count()`](<project>/R/household_count.R), which counts survey rows without applying weights. It returns **20** for the bundled survey.

All 14 tests passed. The test run required `Rscript --vanilla` because the local R startup configuration failed while setting data.table threads.

[exit code: 0]
