### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and follow its selected playbook.

The project is an R package, and both required packs are installed. I found one data file; I’ll record its name without opening it while I check the package’s existing commands and settings.

I recommend setting up the project with **core** and **lang-r**. Both packs are installed.

- **Setting:** `lang-r.r-syntax=data.table-collapse`. The package imports `data.table` in [DESCRIPTION](<project>/DESCRIPTION), and [read_survey.R](<project>/R/read_survey.R) uses `fread()`. The code does not show use of `collapse`; this is also the pack’s default.
- **Draft verification profile:** Run command: not found. Doctor command: not found. The package has tests for survey columns, row count and invalid weights, but no project command for running them was found. An output-producing command was not found.
- **Files found:** three `.R` files, one `.Rd`, one `.csv`, and three files without extensions. There is one data file: `inst/extdata/survey.csv`. I did not open it or run the package or tests.

The setup dry run says it would create:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

I assumed the existing `data.table` usage is the best guide to the R setting. The data classification is still unknown.

Please provide the data rules and say whether you approve this proposal. You can copy and complete this example:

> `inst/extdata/`: Public  
> Highest level Codex may read: Public  
> Classification levels, from public to most restricted: Public; Internal; Restricted  
> I approve the setup proposal.

You can leave any data answer unknown. The [setup playbook](~/.agents/skills/cg/playbooks/setup.md) requires a clear yes before it writes the proposed files; it says, “Until the human confirms, you only read.”

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the survey as Public and Codex as approved to read Public data. I’ll leave the classification-level order open, since it was not provided. The setup command will use the approved packs and R setting:

```sh
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Codex=Public" --project "<project>"
```

Setup is complete. The final status reports **`phase: ready`** and **`stops: none`**, with both required packs installed.

The configuration records `lang-r.r-syntax=data.table-collapse`, classifies `inst/extdata/survey.csv` as Public, and permits Codex to read Public data. The organization’s full classification-level order remains open.

Created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The verification profile remains a draft: no Run or Doctor command was found, and the tests were not run. The project contains three R files and one survey data file; I did not open the data during setup.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its next step.

I’ll add the weighted headcount function and a test against your expected toy-survey value. I’ll inspect the existing package conventions and leave unrelated work alone.

**The change needs your approval before implementation.** The Compound GPID risk check classified it as elevated because it computes a number and adds a function other code can use. The survey data is cleared for Codex. These are measured results from the project’s risk check.

I propose to add `headcount(dt, line = 3)` and its package documentation and export, plus a testthat check. The function will calculate the sum of weights for households strictly below the line divided by the sum of all household weights. I’ll leave the survey and existing functions alone.

I’ll check that the toy survey returns **0.153846 to six decimal places**, as you specified, and that the test suite passes. A different rounded result or a failing test means the change has not passed.

May I proceed with this contract? The approval stop comes from the [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md), which requires a clear yes for elevated-risk work.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll proceed with the agreed function and checks. I’m rechecking the project state first, then I’ll implement the calculation and record the evidence.

The new tests fail on the unchanged package because `headcount()` does not yet exist. I’ll implement the calculation with checks for missing or invalid inputs, then run the full suite.

The toy survey now returns 0.153846154, which matches your expected value to six decimal places. The full test suite passes; I’m finishing the package check and work record.

**Measured:** Added `headcount(dt, line = 3)` in [R/headcount.R](<project>/R/headcount.R). It returns the share of household weight with welfare strictly below the line and rejects missing or invalid inputs. The toy survey result is **0.153846154**, matching your expected value to six decimal places.

**Checks:**

- `Rscript --vanilla -e 'devtools::test(stop_on_failure = TRUE)'` — verified; all 8 tests passed.
- The direct toy-survey comparison — verified against your prior expectation.
- `devtools::check()` — verified with no errors or warnings; it reported one NOTE because it could not verify the system clock.

**Self-review:** P4 and P6 passed. P3 was flagged because the project has no R lockfile, so its environment is not pinned. The verification profile has no Run or Doctor command; `air`, `cg.py repro`, and `cg.py guard` were unavailable.

The completed [work report](<project>/.cg-docs/work-reports/2026-11-25-weighted-household-headcount.md) passed validation. The missing lockfile and a default R startup error were noticed and left untouched; checks ran with `--vanilla`.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I’ll inspect the project and its existing survey conventions, then add the household count function and verify it. I’m using the R package development guidance for this work.

The survey reader returns one row per household, so the count can use the number of rows. I’ll expose that as a separate function and cover the bundled survey and an empty survey.

Added `household_count(dt)` to count survey rows, assuming one row per household. The bundled survey returns **20**.

The function is exported and documented, with tests for the bundled and empty surveys. All 10 package tests pass.

[exit code: 0]
