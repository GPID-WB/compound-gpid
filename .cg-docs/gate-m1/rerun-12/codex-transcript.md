### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and open the selected playbook.

The project is an R package, and the required R pack is installed. I found one CSV file; I’ll use its name only while preparing the setup proposal.

The project is ready for setup. I recommend **core and lang-r**, with `lang-r.r-syntax=data.table-collapse`. Both packs are installed. The setting matches the `data.table` import in [DESCRIPTION](<project>/DESCRIPTION) and its use in [read_survey.R](<project>/R/read_survey.R:7).

The draft verification profile is:

- **Run command:** not found.
- **Doctor command:** not found.
- **Identified behavior:** `read_survey()` returns household records and rejects invalid weights. The existing tests describe those checks; I did not run them.

Measured from the file list: three `.R` files, one `.Rd` file, one `.csv` file, and three files without extensions. There is one data file, [survey.csv](<project>/inst/extdata/survey.csv). I did not open it. Although the package describes it as synthetic, its classification needs your answer.

The setup dry run says it would create:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

I assumed the existing `data.table` dependency reflects the preferred R dialect. The verification profile would remain a draft.

**Do you approve this setup proposal, and what data rules should it record?** You can copy and fill in this example; leave any unknown answer open:

> Yes. `inst/extdata/survey.csv`: Public. Codex may read up to: Public. Classification levels, least to most restricted: Public; Internal; Confidential.

The [setup playbook](~/.agents/skills/cg/playbooks/setup.md) requires confirmation before writing: “Until the human confirms, you only read.”

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll apply the confirmed setup and record the survey as Public, with Codex approved to read Public data. The classification levels remain open.

The setup command is:

```sh
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Codex=Public" --project "<project>"
```

Setup is complete. **Measured status:** `phase: ready`, `stops: none`, with both required packs installed. The R setting is `lang-r.r-syntax=data.table-collapse`.

I recorded the confirmed Public classification for `inst/extdata/survey.csv` and Public read access for Codex. The organization’s ordered classification levels remain open.

Created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The project has three R files, one R documentation file, and one CSV data file. No Run or Doctor command was found. The verification profile remains a draft; the existing tests were not run.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its selected playbook.

I’ll add the weighted household share and a test against your expected value, keeping the rest of the survey workflow unchanged. I’m checking the existing interface and the guide’s risk tier first.

The guide’s risk check returned **elevated** because `headcount()` computes a number and adds a public function. The toy survey is cleared for Codex to read.

I propose to add `headcount(dt, line = 3)` and its documentation, plus a testthat check that the toy survey result rounds to `0.153846` at six decimal places. I’ll also check that welfare equal to the line is excluded and that invalid weights fail. The check fails if any of those expectations is unmet. Existing survey-reading behavior is out of scope.

May I proceed with that contract?

The required pause comes from the [quick-work playbook](~/.agents/skills/cg/playbooks/quick.md), which says: “**`tier: elevated`.** This is a hard stop” and requires a clear yes before continuing. No project files were changed.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll proceed with the agreed change and checks. I’ll first refresh the Compound GPID state, then implement and verify the function.

The function and tests are in place. It uses all household weights in the denominator, treats the line as a strict cutoff, and rejects missing or invalid inputs. I’m running the package tests and checking the work record now.

The toy result is `0.15384615`, which rounds to your expected `0.153846`; the full test suite now passes. The first comparison used testthat’s relative tolerance and failed despite meeting the agreed six-decimal check, so I changed it to compare the rounded result directly.

Added and exported `headcount(dt, line = 3)`. It returns the weighted share of households whose welfare is strictly below the line and rejects invalid weights.

**Measured:** The toy survey result is `0.15384615`, which rounds to your expected `0.153846`. The package tests passed: 7 passes, no failures. They cover the reference value, weighted cutoff behavior, and invalid weights.

The first reference check failed because testthat interpreted its tolerance relatively. I corrected the check to compare at the agreed six decimal places; the expected value did not change.

The work is recorded in [the work report](<project>/.cg-docs/work-reports/2026-11-26-weighted-headcount.md), which passed validation. Self-review passed for verification and scope; determinism is flagged because the project has no lockfile. A full R CMD check and an independent software cross-check were not run.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I’ll inspect the survey data structure and existing package conventions, then add a household count function that fits them. I’ll use the R development guidance for the implementation.

The survey reader returns one row per household, so the count can use the number of rows. I’ll make the function accept a survey data frame and default to the bundled survey.

Added `household_count()` in [R/household_count.R](<project>/R/household_count.R). It counts rows in a survey data frame, assuming one row per household, and defaults to the bundled survey, which has **20 households**.

The package tests passed: 11 assertions, with no failures or warnings.

[exit code: 0]
