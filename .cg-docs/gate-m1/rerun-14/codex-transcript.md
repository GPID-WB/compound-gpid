### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and follow the playbook it selects.

The project is an R package, and both the core and R packs are installed. I’ll inspect its package files and the setup command’s proposed changes; I won’t open the CSV.

I recommend setting up Compound GPID with the **core** and **lang-r** packs. Both are installed.

The proposed R setting is `lang-r.r-syntax=data.table-collapse`. The package imports `data.table` in [DESCRIPTION](<project>/DESCRIPTION), and [read_survey.R](<project>/R/read_survey.R) uses `fread()`. The setting is also the R pack’s default.

The proposed verification profile is a draft:

- **Run command:** not found.
- **Doctor command:** not found.
- **Identified output:** `read_survey()` returns a table with household ID, welfare and weight columns. The existing tests check its dimensions and column names, and that it rejects a non-positive weight.

I found three R files, one CSV, one Rd file and three files without extensions. I did not run the package or its tests, or open the CSV. The package describes the survey as synthetic, but its data classification needs your decision.

The setup dry run reports that it would create:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

I assumed the existing package tests belong in the verification profile and that Codex is the name to use for this coding agent.

Please confirm the proposal and provide the data rules. You can copy and complete this:

> Yes, approve the setup. Classify `inst/extdata/survey.csv` as **[level]**. Codex may read up to **[level]**. Our classification levels, from public to most restricted, are **[levels, or unknown]**.

The [setup playbook](~/.agents/skills/cg/playbooks/setup.md) requires confirmation before it writes these files; it says setup must “explore, propose, confirm, then write.”

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll apply the approved setup, recording the survey as Public and Codex as approved to read Public data. The classification-level list remains open.

```sh
"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Codex=Public" --project "<project>"
```

Compound GPID setup is complete. Status reports **`phase: ready`**, `stops: none`, and no missing packs.

The project has three R files, one CSV, one Rd file and three files without extensions. I found no Run or Doctor command. The verification profile remains a draft; I did not run the package or its tests.

You confirmed the `core` and `lang-r` packs, the `data.table-collapse` setting, the survey’s Public classification, and Codex access to Public data. The organization’s ordered classification levels remain open.

Setup created [config.json](<project>/.cg-docs/config.json), [verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its selected playbook for this change.

The request is to add a weighted household headcount and check the toy survey against 0.153846. I’ll inspect the existing survey and package conventions to identify the smallest change and its risk.

The Compound GPID risk check returned **elevated** because this change computes a number and adds a public function.

The proposed change is to add `headcount(dt, line = 3)`, export and document it, and add a testthat check. I would leave the existing survey reader and data unchanged.

I would check that the toy survey result rounds to **0.153846** at six decimal places, and test that welfare equal to the line is excluded. Either check failing would mean the change is not verified.

May I proceed with that contract?

The [quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) requires this approval: “**`tier: elevated`.** This is a hard stop.”

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll proceed with the approved change and checks. I’ll first refresh the project state, then implement and verify the function.

The new check fails on the current code because `headcount()` does not exist, as expected. The survey is cleared for this agent, and I’ll now add the calculation and input checks.

The full test suite now passes, including the expected survey value and the strict boundary at the line. I’m recording the evidence and checking the final package changes.

Added and exported [headcount()](<project>/R/headcount.R), with documentation and [testthat checks](<project>/tests/testthat/test-headcount.R). It calculates the weighted share with welfare strictly below the line and rejects missing or invalid inputs.

**Measured:** the toy survey returns `0.1538461538`, which rounds to the requested `0.153846`. The test suite passed all nine expectations, including the threshold boundary. The work report also passed validation.

**Self-review:** P4 and P6 passed. P3 was flagged because the project has no lockfile to pin its environment. A full R CMD check was not run; the verification profile has no Run or Doctor command, and `air`, `cg.py repro`, and `cg.py guard` were unavailable.

The [work report](<project>/.cg-docs/work-reports/2026-11-26-weighted-headcount.md) records the commands and evidence. Pre-existing untracked setup files and the failing default R startup profile were left alone; checks used `--vanilla`.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I’ll inspect the package and its survey data conventions, then add the function and verify its behavior. I’m using the R package development guidance for this change.

The survey reader returns one row per household, so the function can report the unweighted number of rows. The bundled survey contains 20 households.

Added `household_count(dt)`, which returns the unweighted number of survey rows, assuming one row per household. It returns **20** for the bundled survey.

The package tests passed (11 assertions). The `air` formatter was unavailable.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check the project’s state and work through the choice of measure with you before any implementation.

The project is ready for a brainstorm, and I’ve created a draft intent to record the decisions. I’m checking the existing headcount definition and a reference for the measures so the first choice is grounded in the package’s current behavior.

I understand that you want a measure of how far poor households fall below the line; the main question is what you want that measure to describe.

**Measured from the code:** the package’s existing `headcount()` returns the weighted share of households strictly below the line.

There are two useful ways to summarize the shortfall:

- **Average among poor households:** If the result is 20%, poor households are, on average, 20% of the line below it. This directly describes their depth of poverty, but it is undefined when no households are poor.
- **Poverty gap index:** Average the shortfall across *all* households, treating nonpoor households as having zero shortfall. This combines depth with the share who are poor. That is the [World Bank’s definition](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.GAPS).

For example, if half of households are poor and their average shortfall is 20% of the line, the poverty gap index is 10%.

I recommend starting with the **average among poor households**, because it most directly answers your question; the existing headcount can show how widespread poverty is alongside it. Would you like that to be the primary question the new measure answers, or would you prefer the poverty gap index across all households?

The [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) records this as an open decision. I have not inspected the survey data or run the package.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record your choice and keep the proposed scope small. I’ll compare the remaining plausible measures against that choice before asking about the intended output.

Your choice is recorded: the primary measure should describe the **weighted average shortfall among poor households**, expressed as a share of the line.

Compared with that choice, the poverty gap index also reflects how many households are poor, while an absolute shortfall depends on the welfare units. Keeping only the existing headcount would leave depth unanswered.

Two decisions would keep the first version small:

1. **Scope:** Return one summary alongside the existing headcount, with no breakdowns or additional poverty measures. I recommend this; it won’t show how shortfalls vary among poor households.
2. **No poor households:** Return `NA` when no household is below the line, because there is no poor-household average to calculate. I recommend this over zero, which could suggest an observed average shortfall of zero.

Do you agree with those two choices? The [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) remains open, and nothing has been built.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record both choices and check the draft intent for any remaining gaps before showing it to you for confirmation.

The [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) now records these choices:

- **Goal:** Let package users see how far below the line poor households are, alongside how many are poor.
- **Measure:** The weighted average shortfall among poor households, expressed as a share of the line.
- **Scope:** One summary alongside the existing headcount; no breakdowns or additional poverty measures.
- **No poor households:** Return `NA`, because there is no poor-household average.
- **A wrong result:** Including nonpoor households in that average, ignoring weights, or returning zero when there are no poor households. Hand-calculated weighted examples can distinguish these cases.

The alternatives recorded are the poverty gap index across all households, the average absolute shortfall among poor households, and keeping the headcount alone.

Assumptions I am making:

1. The result is intended for package users. If a specific audience or format is needed, the output may need to change.
2. The poverty line is positive, so the proportional shortfall has the intended interpretation. If zero or negative lines must be supported, the measure or its contract needs reconsideration.

Correct me now if either assumption is wrong. The intent passed its structural validation with no warnings; the survey data and package code were not run.

Is this intent what you want? Your yes will be recorded under your name.

[exit code: 0]

### G4 vague reply

> Sounds good.

What would you change in the intent, or is anything unclear?

The [Compound GPID guide](~/.agents/skills/cg/SKILL.md) requires a clear yes to the displayed intent; its [grilling instructions](~/.agents/skills/cg/grilling.md) explicitly say that “sounds good” alone is not a yes. The intent remains a draft.

[exit code: 0]

### G5 answer

> Yes, that is what I want.

Your approval is recorded, and the [poverty depth intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) is decided.

The chosen measure is the weighted average shortfall among poor households as a share of a positive poverty line. It will return `NA` when no households are poor. The intent keeps the scope to one summary alongside the existing headcount.

The alternatives set aside are the poverty gap index across all households, an average in welfare units, and keeping the headcount alone. The recorded assumptions are that package users are the audience and that the line is positive. No survey data were inspected or package code run.

To start the small implementation as a separate step, you can say: `/cg add the approved poverty depth measure`.

[exit code: 0]
