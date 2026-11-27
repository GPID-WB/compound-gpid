### B1 setup

> /cg

Status says this project isn't set up yet, so I'm running the setup playbook. I'm still only reading: next are the principles it cites and the R pack's settings.

I'm running setup first because this project isn't set up for the guide yet (status shows `phase: setup`, because `.cg-docs/config.json` doesn't exist). So far I have only read files. Nothing has been written, and I have not opened the data file.

## What I found

- **Files:** 8 tracked files. They are 3 `.R` files, 1 `.Rd` file, `DESCRIPTION`, `NAMESPACE`, `LICENSE` and 1 `.csv`. This is an R package called `toypov` with one exported function, `read_survey()`.
- **How outputs are made:** there is no `Makefile`, `_targets.R` or main script. The output is the package itself, and it is checked by `tests/testthat/` (2 tests).
- **Data files:** 1, at `inst/extdata/survey.csv`. I did not open it.
- **Already here:** nothing from the guide. There is no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md` or version 1 file.
- **Environment (measured):** R 4.6.2, with data.table 1.18.6.1, testthat 3.3.2, withr 3.0.3, devtools 2.5.2 and roxygen2 8.0.0 installed.

## Proposal

**1. Packs:** I recommend `core` and `lang-r`. Both are installed on this machine (1.99.0.9000).

**2. Pack setting:** I recommend `lang-r.r-syntax = data.table-collapse`. The code shows it:
- `DESCRIPTION:11-12`: `Imports: data.table`
- `NAMESPACE:2`: `importFrom(data.table, fread)`
- `R/read_survey.R:8`: `dt <- fread(path)`

No tidyverse package is loaded. This value is also the pack's default.

**3. Verification profile (draft):**
- **Run:** `Rscript -e 'devtools::check(".", document = FALSE)'`, run from the project root. This is inferred: the project names no command, and this is the standard check for an R package. It builds and checks in a temporary folder and installs nothing into your R library. `document = FALSE` stops it from rewriting `man/`.
- **Doctor:** `Rscript -e 'for (p in c("data.table","testthat","withr","devtools")) cat(p, as.character(packageVersion(p)), "\n")'`. It only reads, and it fails if a package is missing.
- **Outputs map:**

  | Output | Where it lives | What proves it right |
  |---|---|---|
  | `read_survey()` | `R/read_survey.R` | The tests in `tests/testthat/test-read_survey.R` check for 20 rows, the 3 column names, and an error on a weight of 0. There are no tests for missing columns, bad `welfare` values or a duplicate `hhid`. Nothing independent checks it yet. |
  | Package check | `R CMD check` result | 0 errors and 0 warnings from the Run command (not run yet) |

**4. Data rules.** Only you can give these. `DESCRIPTION` calls the survey synthetic, but that doesn't count as a classification. Until you answer, I treat the file as restricted. Please answer in one reply, like this example:

```
inst/extdata/survey.csv = Public
Claude Code may read up to: Official Use Only
Levels: Public; Official Use Only; Confidential; Strictly Confidential
```

Leave out any line you don't know yet, and that item will stay open.

**5. Files I will write or create** (from the setup dry run):
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md` (with the pointer block)
- `CLAUDE.md` (holding `@AGENTS.md`)
- `.Rbuildignore` (with `^\.cg-docs$`, `^AGENTS\.md$`, `^CLAUDE\.md$`)

**My assumptions** (correct any that are wrong):
- The coding agent is recorded as `Claude Code`.
- The package and its check are the only outputs.
- I commit nothing unless you ask.

Do you approve this proposal as written?

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve as written, or send corrections. Add the data rules in the format of the example above.
- **Project:** setting up the `toypov` toy package for the guide. Once you approve, I write the 5 files, fill in the draft verification profile and check that status shows `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Now I'll fill in the verification profile with the draft you approved.

Setup is done, and status now shows the project as ready for the guide.

**What you confirmed:**
- Packs: `core` and `lang-r`.
- R style setting: `data.table-collapse`.
- `inst/extdata/survey.csv` is classified Public.
- Claude Code may read Public data. I recorded the agent under the name `Claude Code`.

**Files written:**
- `.cg-docs/config.json`: the packs, the setting, the data rule and what Claude Code may read.
- `.cg-docs/verification.md`: how the project is run and checked, filled in with the draft you approved.
- `AGENTS.md`: a short pointer block for coding agents.
- `CLAUDE.md`: holds `@AGENTS.md`.
- `.Rbuildignore`: keeps these new files out of the package build.

**Status check (measured):**
```
phase: ready
stops: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
packs-missing: none
```

**Still open:**
- **The verification profile is a draft.** It stays a draft until the Run command (the full package check) has run once from start to finish. I haven't run it.
- **No classification levels are recorded.** You didn't give your organization's list of levels, so that part of the config is empty. Public is still treated as cleared.
- **Not committed.** Nothing has been committed. The 4 new or changed files (counting `.cg-docs/` as one) are in your working tree.

**Next steps: Done**
* **Your move:** type `/cg` followed by the change you want, or `/cg plan` to plan one.
* **Project:** the `toypov` toy package is now set up for the guide. Running the package check once would take the verification profile out of draft.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I'm reading the project. Next I'll open the work report and check the risk.

The tier is elevated: the function computes a number people will read, so this is a hard stop. I'll write the contract into the work report first.

I'm stopping before I write any code because this change computes a number people will read. That makes the risk tier "elevated", and the contract needs your yes first.

**What I found (measured):** the data file `inst/extdata/survey.csv` is already cleared as Public, so I can read it. No other risk applies: no personal data, nothing that can't be undone, no new dependency, no open choice. My reason for each is in the work report.

**Contract**, as it now reads in `.cg-docs/work-reports/2026-11-26-add-headcount.md`:

- **Goal:** a new exported function `headcount(dt, line = 3)` in `R/headcount.R`. It returns the sum of the weights of households with welfare below the line, divided by the sum of all weights. It stops with an error if `dt` has no `welfare` or `weight` column, or if either column has a missing value.
  - roxygen2 generates its help page `man/headcount.Rd` and the `export(headcount)` line in `NAMESPACE`.
  - The tests go in `tests/testthat/test-headcount.R`.
- **One interpretation to confirm:** I read "below the line" as strictly less than, so a household with welfare exactly 3 is not counted. This is how the standard poverty headcount works.
- **Out of scope:** `read_survey()`, its test, the data file, other poverty measures (gap, severity), and any commit.
- **Checks, and what would count as failure:**
  1. A test that `headcount(read_survey())` equals 0.153846. The allowed difference is fixed now, before any run, at 5e-7, which matches the 6 decimals you gave. It fails if the difference is larger.
  2. A test that `headcount()` stops when the `weight` column is missing. It fails if no error is raised.
  3. The project's full package check, `Rscript -e 'devtools::check(".", document = FALSE)'`. It fails on any error or warning.
  4. `man/read_survey.Rd` is unchanged after roxygen2 runs. It fails if its digest changes.

A plain yes confirms the contract, and the record stores it under your name. I'll take any other reply as a change or a question.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to confirm the contract, or tell me what to change, such as "count welfare equal to the line too".
* **Project:** I've opened the work report for `headcount()` in toypov, and the work is stopped at the contract. Once you say yes, I'll write the function and tests and then run the four checks.

[exit code: 0]

### C2 yes

> Yes, proceed.

I'll record your reply first. The line:

`"/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/work-reports/2026-11-26-add-headcount.md" --reply "Yes, proceed." --project "<project>"`

Recorded. Next I'll load the R pack's lead skill.

Skills are loaded. Next I'll check that the R tools are installed, and take the baseline digests.

I'll write the test first, so I can see it fail before the function exists.

testthat's `tolerance` is relative, not absolute, so I'll state the absolute 5e-7 bound from the contract directly.

Both tests fail before the change, as they should (measured). Now the function:

Now the checks, each recorded through `evidence`. First, the new tests after the change:

The value is 0.1538461538, which is 2/13 (measured). Now the full package check:

The check passed with 0 errors, 0 warnings and 0 notes. Next I'll run `guard` on the whole change.

Before the self-review, I'll break the formula in a few plausible ways and confirm the 0.153846 check catches each one (P4).

The boundary test fails on the `<=` copy, as it should (measured). Now I'll rerun the tests and the package check on the files as they stand, then `guard`:

Now I'll fill in the rest of the work report.

I've added `headcount(dt, line = 3)`, and on the toy survey it returns 0.1538461538 (2/13), within 5e-7 of your 0.153846 (measured). All four contract checks pass. Nothing is committed.

**What changed:**
- `R/headcount.R`: the new exported function. It adds the weights of households with welfare strictly below the line and divides by the total weight. It stops with an error if `dt` has no `welfare` or `weight` column, or if either column has a missing value.
- `tests/testthat/test-headcount.R`: three tests, the third one added beyond the contract:
  - the toy survey value against 0.153846;
  - a household with welfare exactly 3 is not counted. I added this because the survey has no household at exactly 3, so the value test alone couldn't tell `<` from `<=`;
  - an error when the `weight` column is missing.
- `man/headcount.Rd`: the help page, generated by roxygen2.
- `NAMESPACE`: I added `export(headcount)` by hand, which differs from the contract. roxygen2 won't edit this file because it was written by hand. Switching it to roxygen2 would mean editing `R/read_survey.R`, which the contract left out.

**Checks** (each run through `cg.py evidence`, all measured):

| Check | Result |
|---|---|
| The three tests, run before the function existed | not verified (failed, as they should) |
| The same tests after the change | verified, 3 passed |
| `devtools::check(".", document = FALSE, error_on = "warning")` | verified: 0 errors, 0 warnings, 0 notes |
| `man/read_survey.Rd` digest unchanged | verified |

- **Change to a check:** I added `error_on = "warning"` to the project's check command so that a warning fails it.
- **Formula errors I tried:** an unweighted share gives 0.2 and counting above the line gives 0.846. The value test catches both. `<=` in place of `<` is caught only by the boundary test, which failed on a scratch copy as it should.
- **`guard`:** clean. **`validate`:** 0 problems.

**Self-review** (not an independent review):
- **P3, deterministic:** FLAG. The project has no `renv.lock`, so package versions aren't pinned. That was true before this change.
- **P4, prove it works:** PASS.
- **P6, smallest change:** PASS.

**Not checked:**
- No reviewer in a fresh session looked at the change.
- `cg.py repro` isn't installed.
- There are no tests for a missing `welfare` column or missing values; the code raises errors for both. Zero total weight and a non-numeric `line` raise no error at all.

**Noticed but not touching:**
- Both functions use `stop()` rather than `rlang`/`cli`, and base R rather than `collapse`. Switching would add a dependency.
- `NAMESPACE` is hand-written while `man/` comes from roxygen2.
- `.cg-docs/verification.md` is still a draft and doesn't list `headcount()`.

The work report is at `.cg-docs/work-reports/2026-11-26-add-headcount.md`.

**Next steps: Done**
* **Your move:** to commit, reply "commit the headcount change". The work report goes in the same commit. If you'd rather drop the boundary test or count welfare equal to the line, say so.
* **Project:** `headcount()` is added and checked in toypov, and nothing is committed yet. `.cg-docs/verification.md` is out of date: it doesn't list `headcount()`.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

I added `n_households(dt)`. For the toy survey, `n_households(read_survey())` returns **20**. All 10 package tests pass, 4 of them new.

**What it counts:** the distinct `hhid` values in the table, so a household that appears twice counts once. It stops with an error if the table has no `hhid` column or if any `hhid` is missing. The count is not weighted. If you meant the estimated number of households in the population, that is the sum of the weights, which is **45.5** here. Tell me if you want an option for that.

**Files:**
- New: `R/n_households.R`, `tests/testthat/test-n_households.R`, `man/n_households.Rd`
- Changed: `NAMESPACE` now exports `n_households`. I edited it by hand because the file isn't generated by roxygen. I generated only the help page with roxygen.

This ran outside `/cg`, so nothing was recorded in `.cg-docs/`.

**Next steps: Done**
* **Your move:** Nothing. If you want this change checked and recorded, type `/cg` and ask for it to cover `n_households()`.
* **Project:** toypov now has `read_survey()`, `headcount()` and `n_households()`, all uncommitted on `main`.

[exit code: 0]

### G1 idea

> /cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I've read the project state and the code. Next I create the intent file and look up the field's terms for "how far below the line."

I've started the brainstorm. Its record is `.cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md`, a draft for now. I built nothing and changed no code.

**What I think you want:** a second function next to `headcount()` that gives one number for how deep poverty is in the survey. I'm still missing who reads that number and which property you need it to have.

**The terms for what you described.** I checked these in `~/.claude/skills/r-analytical/workflows/welfare-patterns.md:50-113`:
- **Poverty gap index, FGT(1):** each household's shortfall as a share of the line, `(line − welfare) / line`, with 0 for households that aren't poor. It's averaged over *all* households using the weights.
- **Income gap ratio:** the same shortfall, averaged over the poor households only. It's a different statistic.
- **Squared poverty gap (severity), FGT(2):** the average of the squared shortfall. It gives more weight to the households furthest below the line.
- Your `headcount()` is FGT(0) in the same family.

There is one more measure, the Watts index, but I didn't open a source for it, so I'm leaving it out.

**What the code shows:**
- `headcount()` counts a household exactly on the line as not poor (`R/headcount.R:26`).
- `read_survey()` requires welfare above 0 (`R/read_survey.R:14`). That keeps each household's gap between 0 and 1 (I worked this out from the formula; I didn't run anything).
- The survey has no region or sampling-design columns.
- The package doesn't say what unit welfare is in.

**Round 1.** Three questions. They don't depend on each other.

1. **Who reads this number, and what for?** For example: you comparing surveys or lines, or a reader of a report who needs a sentence like "the poor are on average 30% below the line." Only you know this.
2. **D1: average the gap over all households, or over the poor only?** I recommend **all households (FGT(1))**. It uses the same denominator as `headcount()`. It also never goes up when a poor household gets richer. The income gap ratio can go up when a household just under the line climbs out, which makes it misleading for comparisons (I reasoned this out; I didn't test it). The cost: FGT(1) mixes how many households are poor with how far below the line they are. A value of 0.05 doesn't mean "the poor are 5% below the line."
3. **D2: should the measure count the very poorest households more than in proportion?** That would be severity, FGT(2). I recommend **no, start with the plain gap**. It's easier to explain, and severity can be added later. The cost: the gap alone can't tell whether the shortfall falls on a few very poor households or is spread evenly.

A "yes" to 2 or 3 takes my recommendation. After this round I'll lay out the ways to build it, then write down the goal, what's out of scope and what a wrong result would look like, for you to confirm.

**Next steps: Waiting on you**
* **Your move:** Answer the three numbered questions, for example: `1. me, comparing poverty lines; 2. yes; 3. yes`.
* **Project:** toypov has `headcount()`. This brainstorm on a measure of how far below the line the poor are is open, and the next step is your answers to round 1.

[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

You took up "poverty gap index", so it goes into the project's glossary in this turn:

I've written D1 and D2 into the intent with your words. Your two other points are there too, as facts with you as the source: you have no figure of your own, so any reference value comes from a small hand-built example worked out by arithmetic, and the change should be as small as it can be. The term "poverty gap index" is now in a new `GLOSSARY.md` at the project root, the only file outside `.cg-docs/` that the brainstorm changes.

Question 1 is still open. I asked it without a recommended answer, so "I take the answer you recommend" didn't settle it. I'll ask it again, alone, this time with a recommendation.

**1. Who reads the poverty gap index, and what for?**
I recommend: **you, as the package's author, checking the measure on the toy survey and on hand-built examples.** No outside reader. `DESCRIPTION` calls the package a trial whose data are made up. The cost: if a report reader comes later, the help page will need a plain sentence explaining what a value like 0.05 means, because that's the hard part of FGT(1).

Once this is answered, I'll lay out the ways to build it and recommend one.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to take the recommended reader, or name the reader and what they'll use the number for.
* **Project:** Brainstorm on the poverty gap index: D1 and D2 are settled. The reader is the last open question before choosing an approach.

[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I've recorded your answer to question 1: the reader is you, as the package's author, checking the measure. That makes the goal clear enough to compare ways of building it.

**Four ways to build it.** Each is in the intent with its cost and risk.

- **A. A new function `poverty_gap(dt, line = 3)`, built the same way as `headcount()`.** It means one R file, one test file, one help page and one export line, with no new dependency. The only cost is a few lines of input checks repeated from `headcount()`.
- **B. One general function `fgt(dt, line, alpha)` that covers FGT(0), FGT(1) and FGT(2).** I advise against it for now:
  - it builds the severity measure, which D2 left out;
  - it leaves you either with two ways to get the headcount ratio or with a rewrite of `headcount()`, which is already tested;
  - it's bigger than "as small as you can".
- **C. A new argument on `headcount()` that makes it return the gap instead.** This is weak. A function named `headcount` would return something that isn't a headcount, and the term in the new glossary would have two meanings.
- **D. Build nothing, and only document how to compute it with `weighted.mean()`.** This costs least. But no function is tested, and each caller can still make the main mistake: averaging over the poor only.

I didn't check whether an existing R package already does this. Adding one would also bring in a dependency, which "small" argues against.

**Two things that help with checking later** (worked out from the formula; I didn't run anything):
- A household exactly on the line has a gap of 0. So `<` versus `<=` doesn't change the poverty gap index, unlike `headcount()`.
- The poverty gap index can never be above the headcount ratio for the same line. That gives a check that needs no figure from you.

No experiment would settle this choice. It's a question of size and design.

**D3: how should the poverty gap index be added?**
I recommend **A: a new exported `poverty_gap(dt, line = 3)` in its own file.** It would have the same column and missing-value checks as `headcount()`, use base R, and leave `headcount()` untouched. The trade-off is those few lines of input checks living in both functions.

After D3, I'll write the goal, what's out of scope and what a wrong result would look like, including the small hand-built example. Then I'll show you the whole intent to confirm.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to take approach A, or name another approach (B, C, D) or a change to A.
* **Project:** Brainstorm on the poverty gap index: the reader, D1 and D2 are settled. D3, the approach, is the last decision before the full intent comes back to you to confirm.

[exit code: 0]

### G4 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

One fact is out of date: I created `GLOSSARY.md` in this brainstorm. I'll correct that line and check the file again.

All three decisions are now recorded. `cg.py validate` reports 0 problems and 0 warnings. Below is the intent as the file reads, for you to confirm. Only the Facts table is left out of this summary; it's in `.cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md`.

**Goal:** The package says how far below the line the poor households are, and not only how many of them there are. It does this with one new exported function, `poverty_gap(dt, line = 3)`. The function returns the poverty gap index, FGT(1): the weighted mean over all households of `(line − welfare) / line`, with 0 for households that aren't below the line. The change is as small as it can be. The reader is you, as the package's author, checking the measure on the toy survey and on hand-built examples.

**Out of scope:**
- Severity (FGT(2)), the income gap ratio, the Watts index, or a general `fgt()` function.
- Any change to `headcount()`, `read_survey()`, their tests or help pages, or `inst/extdata/survey.csv`.
- Standard errors, results by group, or a gap in welfare units (money) instead of a share of the line.
- A new dependency, and any commit.

**A wrong result:** The reference value is a hand-built example worked out by arithmetic:
- Welfare `c(1, 2, 4)`, weight `c(1, 1, 2)`, line 4.
- The gaps are 0.75, 0.5 and 0. The third household sits exactly on the line.
- The correct value is (0.75 × 1 + 0.5 × 1 + 0 × 2) / 4 = **0.3125**.

Each common mistake gives a different number:

| Mistake | Value |
|---|---|
| Ignoring the weights | 0.4167 |
| Averaging over the poor only | 0.625 |
| Measuring the gap in welfare units instead of as a share of the line | 1.25 |

There is no reference figure for the toy survey. A correct value there is at least 0 and at most `headcount()` for the same line.

**Decisions:**

| | Decision | Your answer |
|---|---|---|
| D1 | Which households the gap is averaged over | All households, the poverty gap index FGT(1) ("Yes to each question: I take the answer you recommend.") |
| D2 | Whether the poorest count more than in proportion | No: the plain gap first, no severity weighting (same reply) |
| D3 | How it's added | A: a new exported `poverty_gap(dt, line = 3)` in its own file, built like `headcount()` (same reply) |

Set aside: B, a general `fgt()`; C, an argument on `headcount()`; D, documentation only.

```
Assumptions I am making:
1. poverty_gap() checks inputs exactly as headcount() does (columns present, no missing
   welfare or weight) and does not itself check that welfare or the line is above 0;
   read_survey() already checks welfare. If it is wrong: data that skip read_survey()
   with welfare at or below 0 give a gap of 1 or more without an error, and a line of 0
   divides by zero, so checks on welfare > 0 and line > 0 would be added.
2. The default line is 3, as in headcount(), in the same unit as welfare.
   If it is wrong: only the default changes.
3. Errors use stop(), as headcount() does, to add no dependency.
   If it is wrong: cli or rlang would be added to Imports.
Correct me now.
```

Assumption 1 is the one I'd look at most closely. Leaving out those checks keeps the change smallest, but a bad input from outside `read_survey()` would give a wrong number without any error.

**Is this what you want?** A plain **yes** confirms the intent, and it gets recorded under your name. I'll take any other reply, such as "yes, but…" or a correction to an assumption, as a change or a question.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to confirm the intent as shown, or say what to change (for example: `add the welfare > 0 and line > 0 checks`).
* **Project:** The brainstorm on the poverty gap index is a draft with every decision answered. Your yes makes it decided; after that, `/cg plan` or `/cg` builds `poverty_gap()`.

[exit code: 0]

### G5 vague reply

> Sounds good.

"Sounds good" isn't a yes, so I've recorded nothing, and the intent stays a draft.

Is there anything you'd change or that's unclear? Assumption 1 is the one I'd look at again: `poverty_gap()` doesn't check that welfare and the line are above 0. That keeps the change smallest, but data that don't come through `read_survey()` could then give a wrong number without an error.

If the intent is right as it stands, reply with a plain **yes**. I'll take anything else as a change or a question.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to confirm the intent as shown, or name the change (for example: `add the welfare > 0 and line > 0 checks`).

[exit code: 0]

### G6 answer

> Yes.

Your yes is recorded and the brainstorm is finished. Nothing has been built yet.

I recorded it with `cg.py approve --reply 'Yes.'`. The intent is now `decided`, and the approval is saved in `.cg-docs/approvals/2026-11-26-measure-how-far-below-the-line-the-poor-are.2257ca6827080470.1.json` under your name. Any later change to the intent needs a new yes.

**Goal:** add one exported function, `poverty_gap(dt, line = 3)`. It returns the poverty gap index: the weighted mean over all households of `(line − welfare) / line`, counting 0 for households not below the line. You are its reader, checking it as the package's author.

**Decisions:**
- **D1:** the gap is averaged over all households. This is the poverty gap index, FGT(1).
- **D2:** it uses the plain gap, with no extra weight on the poorest.
- **D3:** it is a new function in its own file, built like `headcount()`.

**Set aside:** a general `fgt()` function, an extra argument on `headcount()`, and documentation only.

**Assumptions you confirmed:**
- The input checks match `headcount()`'s. Nothing checks that welfare or the line is above 0.
- The default line is 3.
- Errors use `stop()`.

**Reference value:** the small hand-built example, which should give 0.3125. I worked that out by arithmetic and haven't run any code. On the toy survey there's no reference figure, only a range: a correct value is at least 0 and at most `headcount()` for the same line. I reasoned that from the formula.

**Not looked up:** the Watts index, and whether an existing R package already computes the poverty gap index. I didn't open the data file or run any of the project's code.

**Files written** (none committed):
- the intent, `.cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md`
- its approval record
- a new `GLOSSARY.md` with one entry, "poverty gap index"

**Next steps: Done**
* **Your move:** To build it, type `/cg add poverty_gap() as in the decided intent .cg-docs/brainstorms/2026-11-26-measure-how-far-below-the-line-the-poor-are.md`. The change is small enough to run as quick work.
* **Project:** toypov has `headcount()` and now a decided intent for `poverty_gap()`. Building it is next. `.cg-docs/verification.md` is still a draft and doesn't list `headcount()`.

[exit code: 0]

### H1 ask for the plan

> /cg plan Write the plan for the work we settled in the brainstorm.

I'm reading the decided brainstorm and the project files before writing the plan.

Reading the principles the plan is checked against, then I'll write the plan.

Writing the plan file now.

Now I'll test the pin command as it will be written, then a mutation to see it fail. Both run on a scratch copy.

I've written the plan for `poverty_gap()` from the brainstorm you approved. It's waiting for your yes.

The plan file is `.cg-docs/plans/2026-11-26-add-poverty-gap.md`, status `draft`. `cg.py validate` reports problems: 0, warnings: 0 (measured). Here it is as the file reads:

---

# Add poverty_gap()

## Contract

### Goal

The package exports `poverty_gap(dt, line = 3)`, defined in `R/poverty_gap.R`. It returns the poverty gap index, FGT(1): `sum(weight * gap) / sum(weight)` over all households, where a household's gap is `(line - welfare) / line` when `welfare < line` and 0 otherwise. On the hand-built example of the intent (welfare `c(1, 2, 4)`, weight `c(1, 1, 2)`, line 4) it returns 0.3125, with an absolute difference below 1e-12. It stops with an error, as `headcount()` does, when `dt` lacks `welfare` or `weight` or either has a missing value. It has a help page, `man/poverty_gap.Rd`, generated by roxygen2 from `R/poverty_gap.R`, and `devtools::check()` gives 0 errors and 0 warnings. No other file of the package changes, apart from one `export(poverty_gap)` line in `NAMESPACE`.

### Out of scope

- Severity, FGT(2), the income gap ratio, the Watts index, or a general `fgt()` function (decision D2 of the intent). Deferred: severity can follow as a second measure, in its own plan.
- Any change to `headcount()`, `n_households()`, `read_survey()`, their tests or their help pages, or to `inst/extdata/survey.csv`.
- Standard errors, results by group, or a gap in welfare units (money) in place of a share of the line.
- A check in `poverty_gap()` that welfare and the line are above 0 (assumption 1 of the intent). Deferred: it is added only if data that skip `read_survey()` are to be supported.
- A new dependency, a move from `stop()` to `cli` or `rlang`, or the use of `collapse` (assumption 3 of the intent).
- An update of `.cg-docs/verification.md` (its Outputs map does not list `headcount()` or `n_households()` either). Deferred: noted for the human in the work report.
- Any commit or push.

### Requirements

| ID | Requirement |
|---|---|
| R1 | `poverty_gap()` returns the weighted mean over all households of the gap as a share of the line: 0.3125 on the hand-built example of the intent. |
| R2 | A household above the line adds a gap of 0, never a negative one. |
| R3 | `poverty_gap()` stops with an error naming the column when `dt` has no `welfare` column or no `weight` column. |
| R4 | `poverty_gap()` stops with an error when `welfare` or `weight` has a missing value. |
| R5 | On the toy survey, the poverty gap index at line 3 lies above 0 and below the headcount ratio at line 3. |
| R6 | `poverty_gap` is exported from the package namespace. |
| R7 | `poverty_gap()` has a help page that matches its code, with an example that runs. |
| R8 | No file of the package outside the slices' lists changes: the code, tests and help pages of `headcount()`, `n_households()` and `read_survey()`, `DESCRIPTION`, `tests/testthat.R` and `inst/extdata/survey.csv` keep their digests. |

### Checks

| ID | Req. | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `Rscript -e 'devtools::load_all(quiet = TRUE); testthat::test_file("tests/testthat/test-poverty_gap.R", desc = "poverty_gap() gives 0.3125 on the hand-built example", stop_on_failure = TRUE)'` | non-zero exit: the test is missing, or the value differs from 0.3125 by 1e-12 or more. The unweighted mean (0.4167), the mean over the poor only (0.625) and the gap in welfare units (1.25) each fail it. |
| C2 | R2 | same command, `desc = "poverty_gap() gives 0 gap above the line"` | non-zero exit: on welfare `c(1, 6)`, weight `c(1, 1)`, line 4 the value differs from 0.375 by 1e-12 or more. A gap left negative above the line gives 0.125 and fails it. |
| C3 | R3 | same command, `desc = "poverty_gap() refuses a survey without a welfare or weight column"` | non-zero exit: a table without `weight`, or one without `welfare`, gives no error, or an error that does not name the missing column. |
| C4 | R4 | same command, `desc = "poverty_gap() refuses a missing welfare or weight"` | non-zero exit: an `NA` in `welfare`, or one in `weight`, gives no error matching "must be present for every household". |
| C5 | R5 | same command, `desc = "poverty_gap() lies between 0 and the headcount ratio on the toy survey"` | non-zero exit: on `read_survey()` at line 3 the value is 0 or less, or at or above `headcount(read_survey(), line = 3)`. |
| C6 | R6 | `Rscript -e 'devtools::load_all(export_all = FALSE, quiet = TRUE); stopifnot("poverty_gap" %in% getNamespaceExports("toypov"))'` | non-zero exit: `NAMESPACE` does not export `poverty_gap`. |
| C7 | R7 | `Rscript -e 'devtools::check(".", document = FALSE, error_on = "warning")'` | non-zero exit: any error or warning of R CMD check. That includes an exported `poverty_gap` with no help page, a usage section that does not match the code, a failing example, and any failing test in the suite. |
| C8 | R8 | `Rscript -e '…'`: compares the `git hash-object` digests of the twelve files in R8 with the values recorded today | non-zero exit: any of the twelve files differs from its digest when this plan was written. This is a pin: it passes today by design. |

(In the file, C2 to C5 and C8 hold their commands in full. I shortened them here.)

The reference values of C1 and C2 come from arithmetic, not from the code. C1 is the check that fails on each wrong result the intent names. Before the work, C1 to C6 fail, since neither the function nor its test file exists yet.

**What no check would catch:**
- The value on the toy survey itself. There is no reference figure, so C5 checks only its range.
- A welfare or a line at or below 0 passed without `read_survey()`. `poverty_gap()` doesn't check these, so the result is a gap of 1 or more, or a division by zero.
- A total weight of 0, which gives `NaN`.
- A negative weight.
- A `line` that is not a number.
- The unit of `welfare` and of the line, which the package states nowhere.

### Boundaries

- **Always:** run each slice's checks through `cg.py evidence`, and run C8 at the end of every slice. Follow the pattern of `R/headcount.R`: base R, `stop()`, and the same column and missing-value checks. Build and check only in a temporary library. Stop and report when a check fails.
- **Ask first:** any new dependency. A file not in the slice's list. A change to a check, its expected value or its tolerance. A roxygen2 run that would change `NAMESPACE` or any other help page. Updating `.cg-docs/verification.md`.
- **Never:** change `headcount()`, `n_households()`, `read_survey()`, their tests or help pages, `DESCRIPTION` or `inst/extdata/survey.csv`. Print survey rows or values anywhere. Change a check so that it passes. Install into your R library. Commit or push.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| inst/extdata/survey.csv | Public | the synthetic survey shipped with the package; `DESCRIPTION` says "The data are made up" | as committed in 6127d8c, git blob 1db98caf | the package maintainer, Gate Kit (`DESCRIPTION`) | read by tests and checks through `read_survey()`; not changed; the record holds exit codes, counts and digests, never rows |

**Shape of the data:**
- **The survey:** one row per household, 20 rows, keyed by `hhid`, which `read_survey()` asserts is unique.
- **The columns that matter:** `welfare` and `weight`, both asserted present and above 0. The unit of `welfare` is not stated.
- **The estimate:** the unit is the household and the weights are `weight`. It covers every household the survey represents, poor and not poor, so the denominator is the sum of all weights, as in `headcount()`.
- **Output:** the work produces no dataset.

## Slices

| Slice | What it delivers | Files | Checks | How |
|---|---|---|---|---|
| S1 | `poverty_gap()` as a user calls it. It gives 0.3125 on the example, 0.375 with a household above the line, and a value between 0 and the headcount ratio on the toy survey. | `R/poverty_gap.R`, `tests/testthat/test-poverty_gap.R`, `NAMESPACE` | C1, C2, C5, C6, C8 | by code: the function and its testthat file. The `NAMESPACE` line goes in by hand, as for `headcount()`, because roxygen2 doesn't manage this `NAMESPACE`. |
| S2 | It stops on a missing column or a missing value | `R/poverty_gap.R`, `tests/testthat/test-poverty_gap.R` | C3, C4, C8 | by code: the input checks and their tests |
| S3 | The help page, and a package check with 0 errors and 0 warnings | `R/poverty_gap.R`, `man/poverty_gap.Rd` | C7, C8 | by code: `Rscript -e 'roxygen2::roxygenise()'` |

---

**Risk (`tier`, measured):** `tier: elevated`, for one reason: `number: it computes a number someone will read, or can change one`. The data line says `inst/extdata/survey.csv=Public: cleared`, so no dataset stays closed. I didn't open the survey; I only took its git digest.

**Self-review** (by me, not by a separate checker with fresh context):

| Principle | Verdict | Finding |
|---|---|---|
| P1 Specify before generating | PASS | The wrong result is stated. Every requirement has a check that can fail. C1 fails on all three wrong results the intent names. C8 is a pin and passes today by design. |
| P3 Deterministic by default | FLAG | Every slice is done by code. The R environment isn't pinned: there's no `renv.lock`. That was already so and is out of scope. The `NAMESPACE` line is one obvious edit by hand. |
| P6 Smallest change | PASS | Four files, no dependency, nothing existing touched. R2/C2 goes beyond the intent's example, because that example has no household above the line and so can't catch a gap left negative. |
| P10 Correct in the domain | FLAG | Weights are used and the denominator is all households. Not covered: the welfare unit is unstated, and the function doesn't check that welfare and the line are above 0. Both were already so, and your assumption 1 covers the second. |
| P12 Governed data | PASS | There is one dataset, Public, cleared for Claude Code. |

**What I checked and what I didn't:**
- **Tried out (measured):** the C8 command exits 0 on the project and 1 on a scratch copy with one help page changed. `testthat::test_file(desc = …)` exits 1 when no test matches that name.
- **Not checked:** whether `devtools::check()` passes on the project as it is now. I infer it does from the headcount work report, but `n_households()` has no work report.
- **Noticed:** `R/n_households.R` and its test and help page exist with no work report under `.cg-docs/`. I pinned them so this work can't change them.

Do you approve the plan as it reads? A plain "yes" approves it, and I'll record it under your name. I'll take anything else as a change or a question.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve the plan, or say what to change.
* **Project:** the brainstorm for the poverty gap index is decided and its plan is a draft waiting for approval. After that, `/cg work` builds it slice by slice.

[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### H3 yes

> Yes.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### H4 yes

> Yes.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### H5 yes

> Yes.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### H6 yes

> Yes.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### H7 yes

> Yes.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### H8 yes

> Yes.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### W1 ask for the work

> /cg work Do the work of the approved plan.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### W2 go on

> Go on with the plan as it is approved. I have nothing to add.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### W3 go on

> Go on with the plan as it is approved. I have nothing to add.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### W4 go on

> Go on with the plan as it is approved. I have nothing to add.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### W5 go on

> Go on with the plan as it is approved. I have nothing to add.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### W6 go on

> Go on with the plan as it is approved. I have nothing to add.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### W7 go on

> Go on with the plan as it is approved. I have nothing to add.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### W8 go on

> Go on with the plan as it is approved. I have nothing to add.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### X1 request

> /cg Delete the file scratch/old-extract.csv: nobody uses it any more.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### X2 yes

> Yes.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### X3 yes

> Yes.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]

### X4 yes

> Yes.

You've hit your 5-hour limit · resets 5pm (America/New_York) · out of usage credits

[exit code: 1]
