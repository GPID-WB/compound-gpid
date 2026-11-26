### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and follow the playbook it selects.

The project is an R package, and the R pack is installed. I’ll inspect the package configuration and checks; I’ll leave the data file unopened.

The project needs setup. I recommend the following proposal:

- **Packs:** `core` and `lang-r`; both are installed.
- **R setting:** `lang-r.r-syntax=data.table-collapse`. This is the pack default and is supported by the `data.table` import in [DESCRIPTION](<project>/DESCRIPTION) and use of `fread()` in [read_survey.R](<project>/R/read_survey.R).
- **Draft verification profile:** Run command: not found. Doctor command: not found. The package’s tests expect `read_survey()` to return 20 rows with three named columns and reject a non-positive weight; the tests have not been run.
- **Data:** One file was found: `inst/extdata/survey.csv`. I did not open it. Its classification is still unknown.
- **Files setup would create:** `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. The dry run reported no existing files to change.

The file listing measured eight project files: three `.R`, one `.csv`, one `.Rd`, and three without extensions. The proposed dialect assumes the existing `data.table` usage reflects the intended style. No build or check command was found in the files inspected.

Please provide the data rules and say whether you approve this setup proposal. You can copy and complete this example:

> `inst/extdata/survey.csv`: Public  
> Highest level Codex may read: Public  
> Classification levels, least to most restricted: Public; Internal; Confidential  
> I approve the setup proposal.

Use your organization’s actual classification names; any unknown answer can remain open. The setup playbook requires a clear yes before writing: “Until the human confirms, you only read.” See [setup.md](~/.agents/skills/cg/playbooks/setup.md).

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the survey as Public and Codex as approved to read Public data. The ordered classification levels remain open because they were not supplied.

I’ll run setup with `core`, `lang-r`, and `lang-r.r-syntax=data.table-collapse`, then record the draft verification profile.

Setup is complete. The measured status is `phase: ready`, `stops: none`, with both required packs installed and `lang-r.r-syntax=data.table-collapse`.

I recorded your classification of `inst/extdata/survey.csv` as Public and Codex’s approval to read Public data. The organization’s ordered classification levels remain open.

Setup created [.cg-docs/config.json](<project>/.cg-docs/config.json), [.cg-docs/verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The project has three R files and one data file. A command that produces outputs was not found. The verification profile remains a draft; its tests and the survey data were not run or inspected.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’m using the Compound GPID guide to check the project’s state and follow its next step.

I’ll add the weighted household share and a test against the supplied toy-survey value. I’ll leave unrelated project changes alone. I’m using the R guidance to inspect the existing package conventions and assess the change.

The risk check found two reasons for approval: the new function computes a number, and it adds a public interface. The toy survey is cleared for this coding agent to read.

I propose adding `headcount(dt, line = 3)` and its documentation, plus a testthat check. The test will fail if the toy survey result differs from **0.153846 by 0.0000005 or more**. I’ll also check that households exactly on the line are excluded and that missing weights cause an error. Unrelated code and data are out of scope.

May I proceed with that contract?

The [Compound GPID quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) says **“`tier: elevated`. This is a hard stop”** and requires a clear yes before making the change. The tier command returned elevated for the number and interface reasons above.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll implement the agreed function and checks, then record the results in the project’s work report.

The required R packages are available. The normal R startup fails on a local thread setting, so I’ll run the checks with `--vanilla` to avoid that startup configuration.

The new tests passed, including the survey reference, the threshold boundary, and missing-weight rejection. They failed before implementation because `headcount()` did not yet exist.

Added and exported `headcount(dt, line = 3)`, with documentation and testthat checks. The function uses household weights, excludes households exactly on the line, and rejects missing weights.

**Measured:** the toy survey result is **0.153846154**, within 0.0000005 of the requested 0.153846. The tests passed with `Rscript --vanilla -e 'testthat::test_local(reporter = "summary")'`; they failed before implementation because the function did not exist. The work report also passed validation.

The self-review passed for verification and scope. It flagged the absence of an environment lockfile, so reproducibility across environments remains unverified. A full package check was not run. Normal R startup also failed on a local thread setting; the tests used `--vanilla`.

The implementation is in [R/headcount.R](<project>/R/headcount.R), and the evidence is in the [work report](<project>/.cg-docs/work-reports/2026-11-26-add-household-headcount.md).

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I’ll inspect the project and its survey data conventions, then add the function and verify its behavior. I’m using the R package development guidance for this change.

The survey reader returns one row per household, so the requested count is the number of rows. The existing `headcount()` calculates a weighted poverty share; I’ll add a separate function for the household count.

Added `household_count(dt)` to count survey households, assuming one row per household. It returns 20 for the bundled survey and 0 for an empty data frame.

The package tests pass: 10 checks, no failures. `air` was unavailable, so automatic formatting was not run.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check where the project stands and start the brainstorm.

The guide found no active work or blockers. I’ve opened a draft intent and am checking the package’s current measures and terminology before putting the first choice to you.

I understand that you want the package to show how far poor households fall below the line; I’m still missing which summary and audience would make the result most useful.

**Measured from the code:** `headcount()` already returns a weighted share of households below the line, with a default line of 3.

The standard **poverty gap** averages each household’s shortfall as a proportion of the line across *all* households, counting nonpoor households as zero. That combines how common poverty is with how deep it is. The [World Bank’s definition](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.NAGP) uses this population-wide average.

For example, if half the households are poor and their average shortfall is 20% of the line, the population-wide poverty gap is 10%, assuming equal weights.

1. **Which question should the main result answer?** I recommend the average shortfall **among poor households**, because it directly answers “how far below the line are they?” Its trade-off is that it is not directly comparable to the standard poverty gap. Would you prefer that, or the population-wide poverty gap?

2. **Who will use or read the result?** I’m assuming package users exploring household poverty. Is that the right audience, or is there a particular report or group you have in mind?

The brainstorm is recorded as a draft in [Poverty depth measure](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md). I have not opened the survey data or run the package.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record your choices and narrow the options for the smallest useful measure.

You’ve chosen to describe the average shortfall **among poor households**, for package users exploring household poverty. I’ll keep the proposed scope small.

Two forms would answer that question:

- **A fraction of the poverty line** makes results easier to compare across lines. I recommend this form, consistent with `headcount()` returning a share. It requires a positive line.
- **Welfare units** shows the average monetary or other welfare-unit shortfall directly, but depends on the units used.

The standard population-wide poverty gap is set aside because you chose an average among poor households. Keeping only the existing headcount would leave the depth question unanswered.

Two decisions remain:

1. **Should the result be a fraction of the line?** For example, `0.2` would mean poor households are, on average, 20% below it.
2. **When no households are poor, should the result be `NA`?** I recommend `NA` because an average over an empty group is undefined; callers would need to handle it.

The [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) records your answers and these open decisions. No package code or survey data was run or changed.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record those choices and check the draft intent before showing it back to you.

The [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) now says:

- **Goal:** Give package users exploring household poverty the weighted average distance below the line among poor households, alongside the existing headcount.
- **Out of scope:** A population-wide poverty gap and other poverty measures.
- **A wrong result:** One that averages over all households, ignores weights, or reports the wrong proportional distance. A small hand-calculated example should distinguish it from the intended result. When no households are poor, the result should be `NA`.

Your decisions are to average among poor households, express the result as a fraction of the line, return `NA` when none are poor, and target package users exploring household poverty. The population-wide gap and welfare-unit shortfall remain alternatives set aside.

Assumptions I am making:

1. The measure uses the existing headcount’s household weights and strict below-line boundary. If that is wrong, the weighting or boundary needs a separate decision.
2. The line must be positive for the proportional result. If other lines must be supported, the definition needs to change.

**Measured:** The intent validation reports zero problems and zero warnings. The survey data and package code have not been run.

Is this what you want? A plain **yes** confirms this intent and is recorded under your name; I’ll take anything else as a change or a question.

[exit code: 0]

### G4 vague reply

> Sounds good.

What would you change in the draft intent, or what is unclear? If it is right as written, please reply **yes** to confirm it.

[exit code: 0]

### G5 answer

> Yes.

I’ll record your confirmation against the draft intent.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) is **decided**; your confirmation was recorded.

The chosen measure is the weighted average shortfall among poor households, expressed as a fraction of the poverty line. It returns `NA` when no households are poor. The intent assumes the existing household weights and strict below-line boundary, and requires a positive line.

The population-wide poverty gap and a shortfall in welfare units were set aside. No package code was built or run, and the survey data was not opened.

To start the small implementation, you can say: `/cg implement the approved poverty depth measure`.

[exit code: 0]
