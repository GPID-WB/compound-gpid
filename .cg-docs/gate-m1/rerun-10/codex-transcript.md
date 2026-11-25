### B1 setup

> $cg

I’ll use the cg guide to check the project’s current state and follow the playbook it selects.

The project is an R package, and both the core and R packs are installed. I’ll inspect its package files and checks; I’ll leave the CSV unopened while its classification is unknown.

**Measured:** The project is in setup because `.cg-docs/config.json` is absent. I recommend the following setup:

1. **Packs:** `core` and `lang-r`. Both are installed.
2. **R setting:** `lang-r.r-syntax=data.table-collapse`. The package imports `data.table`, and [read_survey.R](<project>/R/read_survey.R:9) uses `fread()`. The `r-shared` skill also identifies this as the default.
3. **Draft verification profile:** Run command: **not found**. Doctor command: **not found**. The package has tests: [test-read_survey.R](<project>/tests/testthat/test-read_survey.R:1) expects the survey reader to return 20 rows with three named columns and to reject a non-positive weight. No separate output-producing command was found.
4. **Data:** One CSV exists, `inst/extdata/survey.csv`. Its classification is unknown. I did not open it.
5. **Files the setup command would create:** [.cg-docs/config.json](<project>/.cg-docs/config.json), [.cg-docs/verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The file listing contains three `.R` files, one `.Rd` file, one `.csv` file, and three files without extensions. I assumed the R dialect from the package import; I did not run the package or its tests.

Please provide the data rules, if known. You can copy and edit this example: `inst/extdata/survey.csv=Public; Codex may read up to Public; levels: Public; Internal; Restricted`. Unknown answers can remain open.

Do you approve the proposed setup, including the draft verification profile and file changes?

The [cg setup playbook](~/.agents/skills/cg/playbooks/setup.md) requires confirmation before writing: “Until the human confirms, you only read.”

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the approved setup, classify the survey as Public, and record Public as the highest level Codex may read. The classification-level list remains open.

The setup command is:

```sh
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Codex=Public" --project "<project>"
```

Setup is complete. **Measured:** the guide reports `phase: ready`, `stops: none`, and no missing packs. It records `lang-r.r-syntax=data.table-collapse`, the survey as `Public`, and `Codex=Public`.

The project contains three R files, one R documentation file, and one CSV. No Run or Doctor command was found. The verification profile records the existing survey-reader test expectations and remains a draft; I did not run the tests or open the CSV.

Setup created [.cg-docs/config.json](<project>/.cg-docs/config.json), [.cg-docs/verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The ordered list of organizational classification levels remains open.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its next step for this change.

I’ll add the weighted poverty headcount and a test against the supplied survey estimate. I’ll first inspect the existing package and survey structure to identify the files and checks involved.

**The change needs your approval before implementation.** The project’s risk check classified it as elevated because it computes a number and adds a public function. The survey is cleared for Codex to read.

The proposed change is to add `headcount(dt, line = 3)`, export and document it, and add testthat checks. The checks will fail if the toy survey result differs from **0.153846 by more than 0.0000005**, or if values at the poverty line are counted as below it. Existing survey-reading behavior is out of scope.

May I proceed with that contract?

The [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) says an elevated tier “is a hard stop” and requires a clear yes after showing the contract. The tier and data clearance above are measured from the tool output; implementation and tests have not yet been run.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll proceed with the approved change, starting with the guide’s current status and the R package conventions.

The approved scope is unchanged. I’m applying the R package and testing guidance, including the project’s data.table conventions, and will check the estimate at the agreed precision.

The new tests fail on the existing code because `headcount()` does not yet exist, as expected. I also found that the normal R startup fails in this environment; running R with `--vanilla` avoids that startup issue.

The computed survey share is 0.15384615, which matches your reference at six decimal places. The first comparison exposed testthat’s relative tolerance behavior, so I made the agreed absolute tolerance explicit; the full test suite now passes.

The function also works when installed into a temporary library, including through its exported package interface. I’m recording the checks and the environment limitations now.

**Implemented `headcount(dt, line = 3)`** and exported it with documentation and testthat checks. It returns the weighted share of households whose welfare is strictly below the line.

Measured: the toy survey returns **0.15384615**, within the agreed absolute tolerance of 0.0000005 from your expected 0.153846.

- **Verified:** `Rscript --vanilla -e 'devtools::test(stop_on_failure = TRUE)'` passed all 9 checks, including weighted and boundary cases.
- **Verified:** installation into a temporary library and a call through the exported package interface.
- **Verified:** the [work report](<project>/.cg-docs/work-reports/2026-11-25-add-weighted-headcount.md) passed validation.
- **Self-review:** P4 and P6 passed. P3 was flagged because the project has no pinned environment or declared Run command.

The first reference assertion used testthat’s relative tolerance and failed; I changed it to check the agreed absolute tolerance explicitly, keeping the expected value and tolerance unchanged.

Not checked: the verification profile has no Run or Doctor command, and `air` is unavailable. Measured: normal R startup fails in the existing data.table thread setup; the checks used vanilla startup. That environment issue and existing untracked setup files were left untouched.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I’ll inspect the survey data and existing package conventions, then add the function and verify its behavior. I’m using the R development guidance for this change.

The survey format has one row per household, so the count can be the number of rows. The bundled survey contains 20 households; I’ll also cover an empty survey and a smaller input.

Added [n_households()](<project>/R/n_households.R), which counts rows in a survey with one row per household. For the bundled survey, `n_households(read_survey())` returns **20**.

The function is exported and documented. All 12 tests pass.

[exit code: 0]
