### B1 setup

> $cg

I’ll use the cg guide to read the project’s current state and follow the playbook it selects.

The project is an R package, and both relevant packs are installed. I’ll inspect its package metadata and checks, without opening the data file, to prepare the setup proposal.

I recommend setting up this project with **core** and **lang-r**. Both packs are installed.

- **R setting:** `lang-r.r-syntax=data.table-collapse`. This is the pack default and fits the existing `data.table` import in [DESCRIPTION](<project>/DESCRIPTION) and `fread()` use in [read_survey.R](<project>/R/read_survey.R).
- **Verification profile, draft:** Run command: not found. Doctor command: not found. The package exposes `read_survey()`; its existing tests check the returned columns and row count and reject a non-positive weight. I did not run them.
- **Data:** One data file, `inst/extdata/survey.csv`. I did not open it. Its classification and Codex’s permitted access level need your decision.
- **Files the setup would create:** `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. The setup dry run reported these paths.

Measured: the repository contains eight files: three `.R`, one `.csv`, one `.Rd`, and three without extensions. I found no existing setup files or project output command. I inferred the proposed R setting from the package dependency; I assumed Codex is the name to use for this coding agent.

**Do you approve this setup proposal, and what data rules should it record?** You can copy and complete this example, using your organization’s terms:

> Yes. `inst/extdata/survey.csv`: Public. Codex may read up to: Public. Classification levels, least to most restricted: Public; Internal; Confidential.

If you do not know an item yet, say “unknown”; it will stay open. I need your approval because the [cg setup playbook](~/.agents/skills/cg/playbooks/setup.md) says, “Until the human confirms, you only read.”

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I’ll record the Public classification and Codex’s Public access, then write the approved setup and draft verification profile.

Setup is complete. The measured status is **ready**, with no stops or missing packs. It records `lang-r.r-syntax=data.table-collapse`, the survey as `Public`, and Codex access to `Public` data.

The setup created [.cg-docs/config.json](<project>/.cg-docs/config.json), [.cg-docs/verification.md](<project>/.cg-docs/verification.md), [AGENTS.md](<project>/AGENTS.md), [CLAUDE.md](<project>/CLAUDE.md), and [.Rbuildignore](<project>/.Rbuildignore).

The project has three R files and one data file. I found no command that produces outputs or checks the environment. The verification profile remains a draft, and the organization’s ordered classification levels remain unstated. I did not run the tests or open the survey.

[exit code: 0]

### C1 request

> $cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll use the Compound GPID guide to check the project state and follow its selected playbook for this change.

I’ll add the weighted household share and a test against your expected value of 0.153846. I’ll first check the existing survey and package structure to identify the smallest set of files involved.

The risk check classified this change as **elevated** for two reasons: it computes a number someone will read, and it adds a function that other code can call. The toy survey is cleared for this agent to read. No files have been changed.

The proposed change is to add and export `headcount(dt, line = 3)`, document it, and add a testthat check. The check will fail if the toy survey’s weighted share differs from **0.153846** at the precision supplied. Existing survey-reading behavior is outside the scope.

May I proceed with that contract?

The [quick-work playbook](~/.agents/skills/cg/playbooks/quick.md) requires a pause at this point: “**`tier: elevated`.** This is a hard stop.” The [Compound GPID guide](~/.agents/skills/cg/SKILL.md) specifies that only a clear yes approves the contract shown.

[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll proceed with the approved change and check the result against the supplied value.

The independent calculation on the toy survey gives 0.1538461538, consistent with your expected value. The normal R startup fails in the existing environment, but R starts with `--vanilla`; I’ll use that for the checks.

The new tests pass, including a boundary case for households exactly on the line. An installed-package check also returns 0.153846154 for the toy survey; I’m completing the work record and reviewing the remaining checks.

Implemented `headcount(dt, line = 3)` in [headcount.R](<project>/R/headcount.R). It returns the weighted share of households below the line and rejects missing or invalid inputs.

**Measured:** The test suite passed all 9 checks. An installed-package check returned **0.153846154** for the toy survey, within the stated tolerance of your expected 0.153846. The new tests also check weights and exclusion of households exactly on the line.

The self-review passed for verification and scope. It flagged the absence of a project environment lockfile. The work report was validated and is available at [weighted household headcount](<project>/.cg-docs/work-reports/2026-11-26-weighted-household-headcount.md).

The project’s Run and Doctor commands are unspecified, and a full `R CMD check` was not run. Normal R startup encountered an existing thread-setting error, so checks used `--vanilla`.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I’ll check the project’s current state and survey data conventions, then add the function where it fits. I’ll use the R package development guidance for the implementation.

The survey reader guarantees one row per household, so the requested count is the number of rows. I’ll add an exported function that accepts a survey data frame and defaults to the bundled survey.

The function and its documentation are in place. The first test run stopped during R startup because of a data.table thread setting; I’m checking whether the suite can run with a valid setting.

Added [count_households()](<project>/R/count_households.R), which returns the unweighted number of survey rows, assuming one row per household. It defaults to the bundled survey, which contains 20 households.

The test suite passed: 13 checks, no failures or warnings. `air` was unavailable, so formatting was not run.

[exit code: 0]

### G1 idea

> $cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I’ll use the Compound GPID guide to check the project’s current state, then work through the choice of measure with you before any implementation.

I understand that you want the package to describe how far below the poverty line poor households are, alongside the existing headcount; I’m still missing the question you want the new number to answer.

**Measured from the code:** `headcount()` reports the weighted share of households below the line. It does not describe their distance below it.

There are two related questions:

- **Among poor households**, how far below the line is the average household? This directly describes the depth of poverty for those who are poor.
- **Across all households**, how large is the average shortfall? This counts nonpoor households as having zero shortfall, so it reflects both the prevalence and depth of poverty. The World Bank calls this the [poverty gap index](https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.GAPS).

I recommend starting with the first question because it matches “how far below the line the poor households are.” Its trade-off is that it does not, on its own, measure the overall burden across all households.

1. Should the main goal be to describe the **average shortfall among poor households**, alongside the existing headcount? If so, who will use or read the result?

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md) is a draft; the decision is open. I have not opened the survey data or run the package code.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record your choice and use a small arithmetic example to compare the measures.

The draft intent now records your choice: describe the average shortfall **among poor households**, alongside the headcount. It also records your request for a small hand-built example checked by arithmetic.

The next choice is how to express that shortfall. Suppose the line is 10 and two equally weighted poor households have welfare of 6 and 8. Their average shortfall is **3 welfare units**, or **30% of the line**.

- **Relative shortfall:** 30% is easier to compare across positive poverty lines, but it does not give a cash amount.
- **Absolute shortfall:** 3 welfare units is directly interpretable in the input’s units, but harder to compare across different lines.
- **Population-wide poverty gap index:** This also includes nonpoor households in the average. It is useful for overall burden, but mixes the number of poor households with their depth of poverty.

I recommend the **weighted average relative shortfall among poor households**, expressed as a share of the line. It answers your chosen question and works alongside the weighted headcount. It would require a positive poverty line; the result when no households are poor remains a decision for a later round.

1. Do you want that relative measure as the main result? Its trade-off is that it does not report the shortfall in welfare units.

2. Who will use or read the result? That will help decide how to describe it.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md) remains a draft. No survey data were opened and no package code was run.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record the relative measure and keep the reference example small. One edge case still needs a decision: what the result means when no households are below the line.

The [draft intent](<project>/.cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md) now records your choice of the weighted average shortfall among poor households, expressed as a share of the poverty line. It also records the small arithmetic example as the reference.

One edge case needs a decision: if **no households are below the line**, there is no average among poor households to calculate. I recommend returning `NA`, meaning the average is undefined. The trade-off is that callers will need to handle a missing result.

1. Should the result be `NA` when no households are poor?

2. Who will use or read the result? I didn’t recommend an audience in my previous question, so I can’t infer one from your answer.

[exit code: 0]

### G4 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll record `NA` for the no-poor-households case and prepare the intent for your review.

Recorded: return `NA` when no households are below the line, because the average among poor households is undefined.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md) remains a draft. Before I restate it for confirmation, who will use or read the result? For example, are they analysts using the R package, or readers of a report?

[exit code: 0]

### G5 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I’ll assume the result is for analysts using the package and make that assumption visible in the intent.

The [intent](<project>/.cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md) is a validated draft. Here is the proposed understanding:

**Goal:** For analysts using the package, describe how far below the line poor households are, alongside the existing headcount.

**Out of scope:** Adding a population-wide poverty gap index or an absolute monetary shortfall. Nothing is built during this brainstorm.

**A wrong result:** Including nonpoor households in the denominator, ignoring weights, or returning zero when no households are poor. As an arithmetic reference, with a line of 10 and two equally weighted poor households at welfare 6 and 8, the average relative shortfall is 0.3.

**Decisions you made:**

1. Describe the average shortfall among poor households alongside headcount.
2. Express it as a weighted share of the poverty line.
3. Return `NA` when no households are poor.

The absolute shortfall and population-wide poverty gap index were considered and set aside.

**Assumptions I am making:**

1. The audience is analysts using the package. If that is wrong, the presentation and documentation may need to change.
2. The line is positive, and households exactly on it are not poor. If that is wrong, the calculation and boundary need reconsideration.
3. A small hand-built arithmetic example is the reference, as you requested.

I have not opened the survey data or run package code.

Is this intent what you want? A plain **yes** confirms this text and is recorded under your name; I’ll take anything else as a change or a question.

[exit code: 0]

### G6 vague reply

> Sounds good.

The intent remains a draft: “sounds good” does not confirm it under the [Compound GPID confirmation rules](~/.agents/skills/cg/grilling.md), which say, “Only a plain yes is a yes.”

Is there anything you would change, or anything that is unclear? If the intent is exactly what you want, reply **yes** to confirm it.

[exit code: 0]

### G7 answer

> Yes.

I’ll record your confirmation against the draft intent.

The confirmation command will record your exact reply:

`cg.py approve ".cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md" --reply "Yes." --project "<project>"`

Your confirmation was recorded. The [poverty-depth intent](<project>/.cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md) is now decided.

It calls for the weighted average shortfall among poor households, expressed as a share of a positive poverty line, alongside the existing headcount. The result will be `NA` when no households are poor. The agreed reference is a small hand-built example checked by arithmetic.

No package changes were made. When you’re ready to proceed, use `/cg plan` to plan the work, or `/cg` with a small first change.

[exit code: 0]

### H1 ask for the plan

> $cg plan Write the plan for the work we settled in the brainstorm.

I’ll use the cg guide to check the project’s state and open the plan playbook.

The recorded intent is decided: it calls for the weighted average relative shortfall among poor households. I’ll check the package interface and verification profile before drafting the plan.

The [plan](<project>/.cg-docs/plans/2026-11-26-measure-poverty-depth.md) is **draft**. Measured: its validation reports zero problems and zero warnings. The plan reads:

---

# Measure poverty depth

## Contract

### Goal

Give analysts an exported `poverty_depth(dt, line = 3)` function that returns the weighted mean of `(line - welfare) / line` among households strictly below a positive line, or `NA_real_` when none are poor.

### Out of scope

Population-wide poverty gap index and absolute monetary shortfall are excluded by the intent. Refactoring headcount is deferred because the new measure does not require it.

### Requirements

| ID | Requirement |
|---|---|
| R1 | Calculate the weighted average relative shortfall among poor households only. |
| R2 | Return `NA_real_` when no household is poor. |
| R3 | Reject invalid inputs and require a single finite positive line. |
| R4 | Export and document the function, its inputs, result and strict threshold. |

### Checks

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `Rscript -e 'pkgload::load_all("."); testthat::test_file("tests/testthat/test-poverty_depth.R")'` | The tests fail, including if equal weights for welfare 6 and 8 at line 10 differ from 0.3 by more than 1e-12, or weights 1 and 3 plus nonpoor welfare 10 and 12 produce a result differing from 0.25 by more than 1e-12. |
| C2 | R2 | `Rscript -e 'pkgload::load_all("."); testthat::test_file("tests/testthat/test-poverty_depth.R")'` | Tests fail, including if a sample with welfare at or above the line does not return a single numeric NA. |
| C3 | R3 | `Rscript -e 'pkgload::load_all("."); testthat::test_file("tests/testthat/test-poverty_depth.R")'` | Tests fail, including if empty or malformed data, nonfinite welfare, nonpositive or nonfinite weights, or a nonpositive, nonfinite or nonscalar line is accepted. |
| C4 | R4 | `Rscript -e 'pkgload::load_all("."); testthat::test_file("tests/testthat/test-poverty_depth.R")'` | Tests fail, including if the function is absent from namespace exports or its installed help lacks its arguments, return value or threshold rule. |

A wrong result includes nonpoor households in the denominator, ignores weights, or returns zero for no poor households. What no check would catch: errors for untested numeric extremes or combinations, and misleading documentation beyond the tested statements.

### Boundaries

- Always: run the slice checks and compare arithmetic against the independent examples; keep units and denominator explicit.
- Ask first: a new dependency, files outside the slice, or changes to checks or tolerances.
- Never: publish, change the existing headcount, or silently discard invalid inputs.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| none | none | none | none | none | none |

Shape of the data: no dataset is read or produced. The estimate takes one row per household, with numeric welfare and positive household weights; no key is required. It covers only households strictly below the specified line and weights their relative shortfalls by household weight. Tests construct their examples in code.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | An exported, documented poverty depth function with arithmetic and input checks. | R/poverty_depth.R, man/poverty_depth.Rd, NAMESPACE, tests/testthat/test-poverty_depth.R | C1, C2, C3, C4 | By code: the function and testthat checks. |

---

**Measured:** the risk tier is elevated. Its reasons are `number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on`. No dataset is planned for reading, so none stays closed.

**Self-review:** P1 PASS—the requirements have checks and the plan names wrong results. P3 PASS—the slice and checks use code. P6 PASS—the plan uses one small slice. P10 PASS—the estimate specifies its population, weights and threshold. P12 PASS—no dataset is read or produced. These are judgments from a self-review, not independent verification. I did not run project code or verify the proposed test command; the verification profile has no run or doctor command.

Planning is at the approval step. Do you approve the plan as written? A plain **yes** approves it and will be recorded under your name; I’ll take anything else as a change or a question.

The hard stop comes from the [cg plan playbook](~/.agents/skills/cg/playbooks/plan.md), which says: “Ask whether they approve the plan” and “Then end your turn.”

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I’ll add that boundary to the draft and validate the revised plan. Your reply requests a change, so the revised text will need its own approval.

I added this line to the Never list in the [draft plan](<project>/.cg-docs/plans/2026-11-26-measure-poverty-depth.md):

> Never: change any file under `data-raw/`.

Measured: validation reports zero problems and zero warnings. The rest of the plan is unchanged.

Do you approve the revised plan? A plain **yes** approves it and will be recorded under your name; I’ll take anything else as a change or a question.

The [cg plan playbook](~/.agents/skills/cg/playbooks/plan.md) requires a new approval after a correction: “show the part that changed, and ask again.”

[exit code: 0]

### H3 yes

> Yes.

I’ll record your approval against the revised plan, then check its status.

The [plan](<project>/.cg-docs/plans/2026-11-26-measure-poverty-depth.md) is approved, including the boundary that no file under `data-raw/` is changed. Your approval was recorded in the [approval record](<project>/.cg-docs/approvals/2026-11-26-measure-poverty-depth.23c31ee6b8be3ead.json).

Planning is complete. To start the implementation, use `/cg` and request the first slice.

[exit code: 0]
