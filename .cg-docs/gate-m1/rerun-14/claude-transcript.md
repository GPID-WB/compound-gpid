### B1 setup

> /cg

Reading the project and the setup rules. Nothing has been written yet. Next I check the principles that setup cites and do a dry run of the setup command.

I've looked through the project and written nothing yet. Before setup writes any files, I need your yes on the plan below and your answers on the data.

**What I found** (measured, from `git ls-files`): an R package, `toypov`, with 8 files: 3 `.R`, 1 `.Rd`, 1 `.csv`, plus `DESCRIPTION`, `NAMESPACE` and `LICENSE`. It has no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md` or files from version 1. Nothing old needs to be kept or converted.

## Proposal

**1. Packs: `core` and `lang-r`.** Both are installed on this machine. `lang-r` is here because of the `.R` files and `DESCRIPTION`. No Stata or Python files were found.

**2. Pack setting: `lang-r.r-syntax = data.table-collapse`.** The code shows data.table, and this value is also the pack's default:
- `DESCRIPTION:12`: `Imports: data.table`
- `NAMESPACE:2`: `importFrom(data.table, fread)`
- `R/read_survey.R:8`: `dt <- fread(path)`

The code doesn't use collapse yet, so that half of the setting is the default rather than something the code shows.

**3. Verification profile (draft):**
- **Run:** not found. There's no `_targets.R`, Makefile or main script, so nothing builds outputs from inputs. The package's output is what `read_survey()` returns.
- **Check:** `testthat::test_local()` on `tests/testthat/`. This is inferred from `Config/testthat/edition: 3` and the `tests/` folder. I haven't run it. When I do, I'll install the package into a temporary library, not your own.
- **Doctor:** not found.
- **Outputs map:**
  - `read_survey()` with its default path returns 20 rows with the columns `hhid`, `welfare` and `weight`. The proof is `tests/testthat/test-read_survey.R:1-5`.
  - The function's own checks are the input assertions in `R/read_survey.R:10-21`: the required columns are present, `welfare` and `weight` are present and positive, and `hhid` is unique.

**4. Data rules.** One data file was found: `inst/extdata/survey.csv`. I haven't opened it. `DESCRIPTION` calls it synthetic, but that description is not a classification. Until you give it one, it counts as restricted data. Please answer in this form:

```
inst/extdata=Public; Claude Code may read up to: Official Use Only; levels: Public; Official Use Only; Confidential; Strictly Confidential
```

That is:
- the folder's or file's classification;
- the highest level your organization lets Claude Code read;
- if you know them, your organization's classification levels, from public to most restricted.

**5. Files setup will write** (from the `--dry-run`; none exist yet):
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md` (holds only `@AGENTS.md`)
- `.Rbuildignore`, holding `^\.cg-docs$`, `^AGENTS\.md$` and `^CLAUDE\.md$`

**Assumptions I'm making:**
1. The coding agent is recorded as "Claude Code". If you use a different name, `cg.py tier` won't find this agent's approval.
2. There's no pipeline, so the profile stays a draft with Run marked "not found". If a script elsewhere builds outputs, tell me where it is.

Correct me now.

**Next steps: Waiting on you**
* **Your move:** Reply "yes" to items 1–3 and 5, or say what to change. Also give your data answers in the format above.
* **Project:** Setting up `toypov` for Compound GPID. After your answers, setup writes these 5 files and checks that status shows `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

The setup command writes what you confirmed. I'm leaving out `--classification-levels` because you didn't give the levels:

Now I'll fill the verification profile with the draft you confirmed.

Setup is done, and status now shows `phase: ready`.

**What you confirmed and what was written:**
- **Packs:** `core` and `lang-r`, both installed.
- **R style:** `lang-r.r-syntax=data.table-collapse`.
- **Data:** `inst/extdata/survey.csv` is Public, and Claude Code may read Public data. I used the name "Claude Code"; it's what the tool that checks read permission looks for.
- **Files created:**
  - `.cg-docs/config.json`
  - `.cg-docs/verification.md`, filled with the confirmed draft
  - `AGENTS.md`, with the Compound GPID block
  - `CLAUDE.md`, which only points to `AGENTS.md`
  - `.Rbuildignore`, so the R package check skips these new files

Nothing is committed.

**Status after setup:**
```
phase: ready
packs-missing: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
stops: none
```

**Still open:**
- **Verification profile is a draft.** It has no command that builds outputs or checks the environment. The proposed test command, `testthat::test_local()`, hasn't been run.
- **Classification levels not recorded.** You didn't give your organization's list of levels. Setup can be run again to add them whenever you like.

**Next steps: Done**
* **Your move:** Type `/cg` followed by the change you want, for example `/cg add a headcount poverty function`. To record your organization's classification levels, give them in a reply.
* **Project:** `toypov` is set up for Compound GPID and ready for its first piece of work.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I've checked the risk, and this change needs your yes before I write any code.

**Why it needs your yes:** the tier is **elevated** for one reason. The function computes a number that someone will read (a poverty headcount). The survey file is cleared for me to read (recorded as Public), so data is not an issue here.

**What I'll do if you agree:**
- **Goal:** add `headcount(dt, line = 3)` in a new file `R/headcount.R`.
  - It returns `sum(weight[welfare < line]) / sum(weight)`.
  - "Below" means strictly less than: a household exactly at the line is not counted as poor. That is the usual headcount convention.
  - It uses base R and `data.table` only, so the package gains no dependency.
  - It stops with an error if `welfare` or `weight` is missing, if either has an NA value, or if `line` is not a single finite number.
  - It gets roxygen docs and an export. That changes `man/headcount.Rd` and `NAMESPACE`.
- **Tests:** a new file `tests/testthat/test-headcount.R`.
- **Out of scope:** any change to `read_survey()`, the data, `DESCRIPTION`, the verification profile or other poverty measures. No commit unless you ask.

**Checks, and what would count as failure:**

| # | Check | Fails if |
|---|---|---|
| 1 | `headcount(read_survey())` against your expected 0.153846, with the tolerance fixed now at ±5e-7 (half a unit in the sixth decimal) | the result is off by more than 5e-7 |
| 2 | Error tests: missing column, NA weight, `line` of the wrong type | any of them returns a number instead of an error |
| 3 | Edge test: with welfare exactly equal to the line, the household is not counted | it is counted |
| 4 | The full test suite (`testthat::test_local()`), with the package installed in a temporary library and not in your R library | any test fails |

If check 1 fails, I won't change 0.153846 to match the code. I'll stop and show you the number the code gives.

Do you approve this contract, including the strict `<` definition of "below the line"?

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve the contract as written, or say what to change (for example, `use <= instead of <`).
* **Project:** `toypov` has only `read_survey()` so far. This adds its first poverty measure, and work begins once you say yes.

[exit code: 0]

### C2 yes

> Yes, proceed.

Before I write `headcount()`, I'm recording a baseline: the existing test suite run against the unchanged package, with the package installed into a temporary library in the scratchpad.

Baseline: 2 tests, 3 expectations, all passing. Next I write the test first, so I can see it fail before the function exists.

The test fails as it should: all three tests error because `headcount` doesn't exist yet. Now I write the function.

Next I generate the docs and the `NAMESPACE` export with roxygen2. Then I check that only the expected files changed.

`NAMESPACE` is written by hand in this package, and roxygen2 left it alone, so I add the export line by hand.

Now I install the changed package into a fresh temporary library and run the full suite. I also cross-check the number with a separate method (`collapse::fmean`, reading the CSV directly).

All 15 expectations pass, and the data file and `read_survey.R` have the same digests as before. Next I do the self-review against principles P3, P4 and P6.

Principle P4 asks me to show the tests fail when the behaviour is wrong. I'll break the function two ways in a scratch copy: `<=` in place of `<`, and dropping the weights.

Both broken copies fail the tests. The `<=` version is caught only by the edge test, which suggests no household in the toy survey sits exactly at 3. Now the record.

I've added `headcount(dt, line = 3)` and its tests, and on the toy survey it gives 0.153846, as you expected. All 15 tests pass (4 contract checks). The work is recorded as completed and passes `cg.py validate`. Nothing is committed.

**What changed:**
- `R/headcount.R` (new): returns `sum(weight[welfare < line]) / sum(weight)`. A household exactly at the line is not counted. It stops with an error when a column is missing, `dt` has no rows, `welfare` or `weight` has NA values, a weight is zero or negative, or `line` is not a single finite number.
- `tests/testthat/test-headcount.R` (new): checks your expected value, a small hand-built case including a household at the line, and seven bad-input cases.
- `NAMESPACE`: added `export(headcount)`. I added this by hand because the package maintains `NAMESPACE` by hand and roxygen2 skipped it.
- `man/headcount.Rd` (new): generated by roxygen2.

**Checks** (all measured, run with the package installed in a temporary library, not your R library):

| Check | Verdict |
|---|---|
| The existing tests passed before the change | verified |
| The new tests failed before the function existed | verified |
| 1. Toy survey: result is 0.1538461538, which is 1.5e-7 from 0.153846, inside ±5e-7 | verified |
| 2. Bad input stops with an error (7 cases) | verified |
| 3. A household exactly at the line is not counted | verified |
| 4. Full suite: 5 tests, 15 expectations, none failed | verified |
| The tests fail on two broken versions (`<=` instead of `<`, weights dropped) | verified |

A separate calculation with `collapse::fmean` on the CSV gives the same 0.1538461538.

**One check failed at first and I fixed the test, not the code.** I had written check 1 with `expect_equal(tolerance = 5e-7)`. The waldo documentation shows that this tolerance is relative, not absolute. So it rejected a gap of 1.5e-7, which is inside the ±5e-7 we agreed. I rewrote the test as an absolute check. The expected value and the 5e-7 limit are unchanged.

**Beyond the contract:** I added an error for an empty `dt`. Without it, 0/0 would quietly return `NaN`.

**Self-review** (checked against principles P3, P4 and P6): all three pass.

**Not checked:** a full `R CMD check`, style tools such as `lintr`, and other surveys. Two `cg.py` checks, `repro` and `guard`, are not part of this install.

**Noticed but not touching:**
- The package uses base `stop()` rather than `cli::cli_abort()`.
- Roxygen markdown is off, so backticks show up literally in the help pages.
- `DESCRIPTION` has both `Authors@R` and `Author`/`Maintainer` fields.
- The verification profile is still a draft and doesn't list `headcount()`.

The work report is at `.cg-docs/work-reports/2026-11-26-add-headcount-function.md`. The temporary libraries and test copies are in the session scratchpad, which clears itself, so you don't need to delete anything.

**Next steps: Done**
* **Your move:** to commit the change together with its work report, reply `commit it`. Otherwise, nothing.
* **Project:** `toypov` now has its first poverty measure, `headcount()`. The verification profile `.cg-docs/verification.md` doesn't list it yet and is still a draft.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I added `n_households(dt)`, which returns the number of households in the survey. On the toy survey it returns **20**. All tests pass: 20 checks across the three test files.

- **What it counts:** distinct `hhid` values, so a household listed twice counts once. It doesn't use `weight`, so it's the number of households in the sample, not an estimate of how many there are in the population. If you meant the weighted count (`sum(weight)`), say so and I'll add it as an option.
- **Bad input:** it stops with an error if `dt` has no `hhid` column or if any `hhid` is missing. An empty table returns 0.
- **Style:** it takes `dt` the same way `headcount()` does, and uses `stop()` like the rest of the package rather than adding `rlang` as a dependency.

Files:
- New: `R/n_households.R`, `man/n_households.Rd` and `tests/testthat/test-n_households.R`.
- Changed: I added `export(n_households)` to `NAMESPACE` by hand. I didn't regenerate that file with roxygen, because `read_survey.R` has no `@importFrom` tag and roxygen would delete the `importFrom(data.table, fread)` line.

I didn't run this through `/cg`, so `.cg-docs/` has no work report for it, and `verification.md` doesn't list `n_households()` or `headcount()` in its outputs map.

**Next steps: Done**
* **Your move:** Nothing. If you want this change on record with checks, type `/cg`.
* **Project:** toypov now has `read_survey()`, `headcount()` and `n_households()`, all with passing tests; nothing is committed yet and `.cg-docs/verification.md` is out of date.

[exit code: 0]

### G1 idea

> /cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I'm reading the project to gather the facts before I ask you anything. Next: the record files and the headcount work report.

I've started the brainstorm. Nothing is built, and nothing outside `.cg-docs/` has changed. The record is in `.cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md` (status `draft`). The state check found nothing blocking and no other open decisions.

**What I think you want:** a second number next to `headcount()` that says how deep poverty is, not only how widespread. I'm missing three things: who reads the number, whether the poorest should count more, and what unit the number should be in.

**The usual measures for "how far below the line".** All of them fit the package as it is: weighted, by household.

- **Poverty gap index, FGT(1):** each poor household's shortfall as a share of the line, averaged over *everyone*, with the non-poor counted as zero. It's the natural partner to `headcount()`, which is FGT(0) of the same family. Its weakness: it ignores inequality among the poor. Moving money from a very poor household to a less poor one doesn't change it. *(Source: Wikipedia, "Poverty gap index" and "Foster–Greer–Thorbecke indices", read today.)*
- **Squared poverty gap, FGT(2), also called "severity":** the same, but each gap is squared, so the poorest count more. It's harder to explain in a sentence.
- **Watts index:** the average of ln(line / welfare) over the poor. It also weighs the poorest more. It needs welfare above 0, which `read_survey()` already enforces (`R/read_survey.R:16`).
- **Income gap ratio:** the average shortfall among the poor only. It's intuitive, but it can *rise* when poverty falls (when a household just below the line climbs out). Computing it by mistake when FGT(1) was meant is a known error *(source: `~/.claude/skills/r-analytical/workflows/welfare-patterns.md:94`)*.

**One thing you don't need to decide (inferred):** for the gap measures, a household exactly at the line has a gap of zero. So `<` and `<=` give the same number, and what `headcount()` does at the line carries over.

**Round 1.** A plain yes takes my recommendation.

1. **Who reads it, and what question does it answer?** I recommend an analyst who reads it next to `headcount()` to compare surveys, groups or lines. The question would be: "On average, how far below the line is the population, as a share of the line?" Trade-off: it doesn't directly give the money a programme would need.
2. **Should the poorest count more?** I recommend no for the first measure. Trade-off: two very different situations among the poor can get the same number. A severity measure can come later.
3. **What unit?** I recommend a share of the line, from 0 to 1, like `headcount()`. Trade-off: to get an amount, someone multiplies by the line and the population. The package doesn't document the unit of `welfare` or what the default line of 3 means, so I'd have to ask you for those before a money figure could mean anything.

These three answers decide the measure: 1 yes, 2 no, 3 share → FGT(1). 2 yes → FGT(2) or Watts. 3 money → the total poverty gap. Once you've answered, I'll lay out the approaches side by side and ask you to choose one.

I haven't looked at what's in the survey data. The brainstorm doesn't open data files.

**Next steps: Waiting on you**
* **Your move:** Answer 1, 2 and 3, for example: `1 yes, 2 no, 3 yes`, or correct any of them in your own words.
* **Project:** You're choosing a poverty-depth measure for `toypov`. After your answers I'll compare the approaches, and then you confirm the written intent.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I've recorded your three yeses in the intent, in your words. "Poverty gap index" is now in a new project `GLOSSARY.md`, since that's the measure your answers lead to: FGT(1), the shortfall as a share of the line, averaged over all households.

**Round 2: which approach**

| | Approach | Verdict |
|---|---|---|
| **A** | A new `poverty_gap(dt, line = 3)` next to `headcount()`, with the same input checks | **Recommended.** It's the smallest option: one R file, one test file, one `NAMESPACE` line, one help page, and no new dependency. |
| B | A general `fgt(dt, line, alpha)` | It builds the severity measure and other variants that you didn't ask for. It's bigger than A for no gain now. |
| C | A `measure =` argument added to `headcount()` | Weak. A function called `headcount` would return something that isn't a headcount, and it changes code that's already tested. |
| D | No code, only a note on how to compute it by hand | Not tested, and it invites the known error of averaging over the poor only. It doesn't meet your answer to D1. |

4. **Build it with approach A?** Trade-off: if you later want a severity measure, it becomes a third separate function rather than one `alpha` argument.

After you answer, I'll write the goal, what's out of scope and what a wrong result looks like. I'll also list my assumptions, including that `poverty_gap()` should stop when welfare is 0 or below, as `read_survey()` does. Then I'll show you the whole intent for your yes.

**Next steps: Waiting on you**
* **Your move:** Reply `4 yes` to take approach A, or name another approach.
* **Project:** You're choosing a poverty-depth measure for `toypov`. The measure is settled as the poverty gap index, and only the approach is open before you confirm the intent.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

I've recorded your yes to approach A, filled in the rest of the intent, and checked it with code: no problems, no warnings. Here's what it says now. File: `.cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md`, status `draft`.

**Goal:** `toypov` says how far below the poverty line the poor households are, not only how many there are. A new exported function, `poverty_gap(dt, line = 3)`, returns the **poverty gap index** (FGT(1)). That's the weighted average, over all households, of each household's shortfall below the line as a share of the line; households at or above the line count as zero. The reader is an analyst who reads it next to `headcount()` to compare surveys, groups or lines. It stays as small as possible: one function next to `headcount()`, with tests.

**Out of scope:**
- The squared poverty gap (FGT(2)), the Watts index, the income gap ratio, and a general `fgt(alpha)` function.
- Any amount in money, such as the total poverty gap.
- Changes to `headcount()`, `n_households()`, `read_survey()`, the data or `DESCRIPTION`, and any new dependency.
- Standard errors, groups or regions, and documenting the unit of `welfare` or what the default line means.

**A wrong result looks like any of these:**
- A value above `headcount()` for the same data and line, or outside 0 to 1.
- A value that equals the average shortfall among the poor only.
- A value that ignores `weight`.
- A value that differs from the figure you compute by hand before the code runs.

A correct result is between 0 and `headcount()`, is 0 when no household is below the line, and matches a weighted case built by hand.

**Decisions, all yours:**
| | Decision | Your answer |
|---|---|---|
| D1 | Reader and question: an analyst, "how far below the line, as a share of the line" | Yes |
| D2 | Should the poorest count more? No, not in this measure | Yes |
| D3 | Unit: a share of the line, not money | Yes |
| D4 | Approach A: a new `poverty_gap(dt, line = 3)` | Yes |

```
Assumptions I am making:
1. poverty_gap() stops when welfare is 0 or below, as read_survey() does, and otherwise has headcount()'s input checks. If it is wrong: a household with welfare 0 would count with a gap of 1, and a negative one with a gap above 1.
2. The function is named poverty_gap, after the glossary term. If it is wrong: only the name changes.
3. The default line is 3, as in headcount(). If it is wrong: only the default changes.
4. Errors use base stop(), as headcount() does. If it is wrong: they move to cli::cli_abort(), which adds a dependency.
Correct me now.
```

Is this intent what you want? Your reply will be recorded word for word under your name, and it sets the intent to `decided`. After that, any change to it needs a new yes. A correction instead of a yes is fine: I'll change the text and show it to you again.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to confirm the intent as written, or say what to change, for example: `change assumption 1: allow welfare 0`.
* **Project:** You're choosing a poverty-depth measure for `toypov`. Everything is decided and written down; once you confirm, building `poverty_gap()` starts as a separate `/cg` task.

[exit code: 0]

### G4 vague reply

> Sounds good.

I tried to record your reply as approval with this command:

`cg.py approve .cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md --reply "Sounds good." --project .`

It refused, so nothing was recorded. "Sounds good" agrees without deciding, and only a plain yes can confirm the intent. The intent is still `draft`, exactly as I showed it to you.

Is anything in it unclear, or is there something you'd change? These are the parts most worth a second look:
- **Assumption 1:** `poverty_gap()` stops on welfare of 0 or below, instead of counting a zero-welfare household with a gap of 1.
- **Out of scope:** no money amount and no severity measure in this step.

If it reads right as it is, reply `yes`.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to confirm the intent as written, or name what to change, for example: `change assumption 1: allow welfare 0`.

[exit code: 0]

### G5 answer

> Yes, that is what I want.

Your intent is approved and is now `decided`. The approval was recorded under your name with your reply word for word: `.cg-docs/approvals/2026-11-26-measure-how-far-below-the-line-the-poor-are.7c17543b316b3f81.json`. If the intent changes, it needs a new yes.

- **Intent:** `.cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md`, status `decided` (measured: the file header and the approve output).
- **Goal:** a new `poverty_gap(dt, line = 3)` returns the poverty gap index, FGT(1): each household's shortfall below the line as a share of the line, weighted and averaged over all households. It's meant to be read next to `headcount()`.
- **Decisions:**
  - D1: the reader is an analyst asking "how far below the line, as a share of the line." Your answer: yes.
  - D2: the poorest don't count more. Your answer: yes.
  - D3: the result is a share of the line, not money. Your answer: yes.
  - D4: approach A. Your answer: yes.
- **Assumptions you confirmed:**
  - It stops on welfare of 0 or below.
  - It's named `poverty_gap`.
  - The default line is 3.
  - Errors use base `stop()`.
- **Set aside:**
  - B, a general `fgt(alpha)`: it's bigger than needed.
  - C, a `measure =` argument on `headcount()`: the name would no longer describe what it returns.
  - D, a note on computing it by hand: it wouldn't be tested.
- **No experiment needed:** your answers settled the choice, and running something couldn't have.
- **New file:** `GLOSSARY.md` at the project root, with the entry "Poverty gap index." It isn't committed, and neither is anything else.
- **Not looked up:**
  - The survey data itself; the brainstorm doesn't open data files.
  - The unit of `welfare` and what the default line of 3 means. These aren't documented in the package.
  - Any primary source beyond the two Wikipedia pages and the team's R welfare-patterns guide. I didn't open Foster, Greer and Thorbecke (1984).

Before you start the build, compute the toy survey's FGT(1) at line 3 by hand and keep the figure ready. That gives the test a number fixed in advance, as you did for `headcount()`. An inferred check also applies: the result must come out at or below 0.153846, the toy survey's headcount at line 3.

**Next steps: Done**
* **Your move:** Type `/cg Build poverty_gap(dt, line = 3) as the decided intent .cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md says. For the toy survey I expect <your hand-computed figure>.`
* **Project:** The brainstorm for `toypov`'s poverty-depth measure is finished and approved. Next is building `poverty_gap()` with its tests, as a `/cg` task of its own.

[exit code: 0]
