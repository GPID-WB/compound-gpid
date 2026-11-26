### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and follow the playbook it selects.

The project is ready for a setup proposal. **My recommendation is to enable the installed `core` and `lang-r` packs**, with `lang-r.r-syntax=data.table-collapse`.

Measured from the project files: `DESCRIPTION` imports `data.table`, and `R/read_survey.R` uses `fread()` and a data.table. The proposed setting is also the pack default; the code does not establish a `collapse` preference.

The draft verification profile is:

- **Run command:** not found.
- **Doctor command:** not found.
- **Output:** `read_survey()` returns a table. The existing tests expect 20 rows with `hhid`, `welfare`, and `weight`, and check that a non-positive weight is rejected. These checks have not been run.

I found eight files: three `.R`, one `.csv`, one `.Rd`, and three files without extensions. There is one data file, `inst/extdata/survey.csv`. I did not open it. Its classification remains unknown, regardless of the description in `DESCRIPTION`.

The setup command’s dry run says it would create:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

**Do you approve this setup proposal?** Please also state the data rules. You can copy and complete this example, leaving unknown items open:

> Approve: yes  
> `inst/extdata/survey.csv`: Public  
> Highest classification Codex may read: Public  
> Classification levels, from least to most restricted: Public; Internal; Confidential

This proposal assumes the existing tests describe the intended output; if they do not, the verification draft needs correction. Setup requires your explicit confirmation before it writes these files, as stated in the [setup playbook](~/.agents/skills/cg/playbooks/setup.md).

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the approved packs, R setting, and Public access rule for Codex. The classification scale remains open. I’ll run the setup command with those values, then write the confirmed verification draft and check the resulting status.

Compound GPID setup is complete. **Status reports `phase: ready` and `stops: none`.** Both expected packs, `core` and `lang-r`, are installed. The recorded setting is `lang-r.r-syntax=data.table-collapse`.

The setup records `inst/extdata/survey.csv` as Public and Codex as approved to read Public data. The ordered classification levels remain open.

The command created [.cg-docs/config.json](<project>/.cg-docs/config.json), [.cg-docs/verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The verification profile remains a draft: no Run or Doctor command was found, and the existing tests were not run. I found three R files and one data file; I did not open the data.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project’s state and follow its selected playbook.

I’ll add the weighted household share below the requested line and a test against the supplied reference value. I’ll first inspect the package interface and assess the change’s risk.

The risk check returned **elevated** because the function will compute a number and add a public interface. The survey file is cleared for Codex to read.

I propose adding `headcount(dt, line = 3)`, its documentation and a testthat check. The check will fail if the toy survey’s result differs from **0.153846** by more than 0.0000005. I’ll also check that welfare equal to the line is excluded. Existing survey-reading behavior is outside the change.

May I proceed with that contract?

The [quick work playbook](~/.agents/skills/cg/playbooks/quick.md) states that an elevated tier is “a hard stop” and requires a clear yes before continuing.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll proceed with the agreed change and checks. I’ll refresh the project state first, then follow the R pack’s guidance.

The survey is classified as public for this project. I’m using the R package and testing guidance to implement and verify the exported function.

The new checks fail on the current package because `headcount()` does not yet exist, as expected. I’m adding the function with explicit input checks and the strict “below the line” comparison.

The full test suite now passes. One test initially reused an invalid weight when checking the line argument; I corrected its setup and reran the suite.

The installed package also returns the expected value. The first installation attempt exposed a local R startup configuration error; rerunning with user startup files disabled succeeded.

Added `headcount(dt, line = 3)` and exported it from the package. It returns the weighted share of households whose welfare is strictly below the line.

**Measured:** the toy survey result is **0.153846154**, within the agreed tolerance of your expected 0.153846. The full testthat suite passed with 11 checks, including the threshold boundary; the installed package interface also passed.

**Self-review:** P4 and P6 passed. P3 was flagged because the existing project has no lockfile or declared reproducible run command. A full R CMD check was not run.

The [work report](<project>/.cg-docs/work-reports/2026-11-26-weighted-household-headcount.md) records the checks and was validated without errors.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll inspect the project’s survey data conventions and add a function that fits the existing code.

I’m using the R package development guidance to match the project’s conventions.

The survey reader guarantees one row per household, so the count can use the number of rows. I’ll expose that as a small function that also accepts a survey already in memory.

Added `household_count(dt)` to count survey rows, with one row per household. It returns an unweighted count; for the bundled survey, it returns 20.

The test suite passes: 15 tests, with no failures or warnings.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check the project’s current state, then work through the choice of measure with you before any implementation.

I understand that you want the package to describe how far poor households fall below the poverty line, alongside the existing headcount; I’m missing who will use the result and what decision or comparison it should support.

One related measure is the **poverty gap index**: it averages shortfalls across all households, counting nonpoor households as having no shortfall, and expresses the result relative to the poverty line. That differs from averaging the shortfall only among poor households. [World Bank definition](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.NAGP)

The existing `headcount()` reports the weighted share of households below the line. I’ve started a [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md); no package code was run or changed.

Who will use the new result, and what should it help them understand? I suggest starting with the average shortfall **among poor households**, for someone interpreting a survey: it matches your description directly, though it does not by itself show how widespread poverty is. Does that fit your purpose?

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record your choice and compare the measures that could answer it, keeping the scope small.

Your [brainstorm intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) remains open. I’ve recorded your choice to focus on the average shortfall among poor households and to keep the work small.

Three measures could use the package’s existing household welfare and weights:

- **Average shortfall as a share of the line:** for example, 20% means poor households are, on average, one-fifth of the line below it. This is easier to compare across positive poverty lines.
- **Average shortfall in welfare units:** for example, 2 units below a line of 10. This is direct, but harder to compare across lines or units.
- **Poverty gap index:** averages across all households, assigning zero shortfall to the nonpoor. It combines how common and how deep poverty is, so it answers a different question.

I recommend the first: a **weighted average shortfall among poor households, as a fraction of the line**. Its trade-off is that it does not directly report the shortfall in welfare units. If there are no poor households, the average among them is undefined; we’ll need to decide how the package should report that.

Would you choose this measure?

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record that choice and settle the boundary cases needed to make the measure unambiguous.

The chosen measure is the weighted average shortfall among poor households, expressed as a fraction of the poverty line. The [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) records that choice.

Two boundary decisions remain:

1. **No poor households:** I recommend returning `NA`, because there is no average over an empty group. Callers would need to handle that result. Do you agree?
2. **Poverty line:** I recommend requiring a finite, strictly positive line, so the fraction is defined and meaningful. Unlike the existing headcount, this measure would reject zero or negative lines. Do you agree?

[exit code: 0]

### G4 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I’ll record both boundary decisions and prepare the full intent for your review.

The [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) is ready for your review. Its validation reports no problems or warnings.

**Goal:** Add a small measure that tells someone interpreting a survey how far poor households are below the line, alongside the existing headcount.

**Out of scope:** Changing the headcount, adding a population-wide poverty gap index, or reporting shortfall in welfare units. This brainstorm builds nothing.

**A wrong result:** The measure must not average over all households, ignore weights, or count a household at the line as poor. For welfare values 2 and 4, weights 1 and 3, and a line of 5, the correct weighted mean relative shortfall is 0.3. With no household below the line, the result is `NA`.

**Your decisions:**

1. Focus on the average shortfall among poor households for someone interpreting a survey, and keep the work as small as possible.
2. Express that weighted average shortfall as a fraction of the poverty line.
3. Return `NA_real_` when there are no poor households.
4. Require a finite, strictly positive poverty line.

The alternatives considered were the average shortfall in welfare units, the population-wide poverty gap index, and keeping only the existing headcount. The first is harder to compare across lines; the second combines prevalence and depth; the last does not answer your question.

Assumptions I am making:

1. The measure follows the existing headcount’s input conventions: one row per household, finite numeric welfare, positive finite weights, a strict below-line threshold, and a default line of 3. If this is wrong, the interface or validation needs another decision.
2. It returns a fraction, such as `0.2` for 20%, consistent with the headcount’s share. If this is wrong, the output scale needs another decision.

Correct me now. Is this intent what you want? Your clear yes will be recorded under your name against this text.

[exit code: 0]

### G5 vague reply

> Sounds good.

Is there anything you would change or anything unclear in the intent? If it is exactly what you want, please reply **yes**.

The [Compound GPID grilling instructions](~/.agents/skills/cg/grilling.md) classify “sounds good” as “agreement without a decision” and require a plain yes to confirm the intent as shown.

[exit code: 0]

### G6 answer

> Yes, that is what I want.

I’ll record your confirmation against the reviewed intent.

Your confirmation is recorded, and the [poverty depth intent](<project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md) is approved.

The agreed measure is the weighted average shortfall among poor households, expressed as a fraction of a positive poverty line. It returns `NA` when no households are poor. The package has not been changed.

When you’re ready to build it, you can start with `/cg` and request the new measure.

[exit code: 0]
