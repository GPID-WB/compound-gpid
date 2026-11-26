### B1 setup

> /cg

Still reading only. Next I check what setup would write, with a dry run that writes nothing.

This project hasn't been set up for the guide yet. Status shows `phase: setup`, `stops: none` and nothing waiting on you, so I followed the setup playbook. So far I have only read files. I haven't opened the data file and haven't written anything.

## What I found

- **Files:** an R package called `toypov`, with 3 `.R` files, 1 `.Rd` file, `DESCRIPTION`, `NAMESPACE` and 1 `.csv`. There is no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md` or version 1 file.
- **How outputs are made:** there's no Makefile, `_targets.R` or main script. The only output is the exported function `read_survey()`. It's covered by `tests/testthat/test-read_survey.R`, which has 2 tests.
- **Data:** 1 file, `inst/extdata/survey.csv`. `DESCRIPTION:8` calls it synthetic, but a description isn't a classification (P12). Until you classify it, I treat it as restricted.

## Proposal

**1. Packs:** `core` and `lang-r`. Both are installed (version 1.99.0.9000).

**2. Pack setting:** `lang-r.r-syntax=data.table-collapse`. The code already uses this style: `DESCRIPTION:11-12` imports `data.table`, `NAMESPACE:2` imports `fread`, and `R/read_survey.R:8` calls `fread(path)`. It is also the pack's default.

**3. Verification profile (draft, P4):**
- **Run:** not found in the project. Because this is an R package with testthat tests, I suggest the standard package check: `R CMD build . && R CMD check --no-manual toypov_0.0.1.tar.gz`. This is my inference, not a command the project has. The check installs the package into its own temporary library, not into yours.
- **Doctor:** not found.
- **Outputs:** `read_survey()`, which returns a data.table with one row per household. The proof is the two tests:
  - `test-read_survey.R:1-5` checks that it reads 20 rows with columns `hhid`, `welfare`, `weight`.
  - `test-read_survey.R:7-11` checks that it refuses a weight of 0.
- **Not covered by any test:** the refusals for missing columns, non-positive `welfare` and duplicate `hhid` (`R/read_survey.R:11-22`).

**4. Data rules (P12).** Only you can answer these. You can reply in this form:

> `inst/extdata/survey.csv` = Public. Claude Code may read up to: Official Use Only. Levels: Public; Official Use Only; Confidential; Strictly Confidential.

- What is the classification of `inst/extdata/survey.csv` (or of `inst/extdata/` as a whole)?
- What is the highest level your organization allows Claude Code to read?
- If you know them, what are your organization's classification levels, from public to most restricted?

If you don't know an answer yet, it stays open and the file stays restricted.

**5. Files I would write.** These come from a dry run of `cg.py setup`, which wrote nothing:
- `.cg-docs/config.json` (new)
- `.cg-docs/verification.md` (new, then filled with the draft above, marked `draft`)
- `AGENTS.md` (new, with the guide's pointer block)
- `CLAUDE.md` (new, holding `@AGENTS.md`)
- `.Rbuildignore` (new, excluding `.cg-docs`, `AGENTS.md`, `CLAUDE.md`)

**Assumptions:** I'd record the coding agent as "Claude Code". I won't commit anything unless you ask.

Do you approve items 1, 2, 3 and 5 as written, or with changes? And what are your answers for item 4?

**Next steps: Waiting on you**
* **Your move:** Reply "yes" plus your data answers, for example: `yes. inst/extdata/survey.csv = Public. Claude Code may read up to: Official Use Only. Levels: Public; Official Use Only; Confidential; Strictly Confidential`. To change something, say what.
* **Project:** Setting up the `toypov` package for the guide. Nothing is written yet; once you confirm, I'll write the five files and check that status shows `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Writing the confirmed setup now.

Now filling the verification profile with the confirmed draft.

Setup is finished. Status now reads `phase: ready` and `stops: none`. I didn't open the data file or commit anything.

**What I found:** an R package, `toypov`, with 3 `.R` files and 1 `.Rd` file. There's no build script, so its only checks are the 2 testthat tests. It has 1 data file, `inst/extdata/survey.csv`.

**What you confirmed:**
- Packs `core` and `lang-r`.
- The setting `r-syntax` is `data.table-collapse`.
- The draft verification profile.
- `inst/extdata/survey.csv` is Public.
- Claude Code may read Public data. I recorded the agent under the name "Claude Code".

**Files written (all new, none committed):**
- `.cg-docs/config.json`
- `.cg-docs/verification.md`, filled with the draft profile
- `AGENTS.md`, with the guide's pointer block
- `CLAUDE.md`, holding `@AGENTS.md`
- `.Rbuildignore`, so the package check skips these files

**Status after setup:**
```
phase: ready
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Claude Code=Public
packs-missing: none
stops: none
```

**Still open:**
- The verification profile is still a `draft`. Its Run command, `R CMD build . && R CMD check --no-manual toypov_0.0.1.tar.gz`, is the standard check for an R package rather than one the project names, and it hasn't been run. There is no Doctor command.
- No test covers the refusals for missing columns, non-positive `welfare` or duplicate `hhid`.
- Your organization's classification levels aren't recorded. That's optional: you didn't give them, and nothing depends on them yet.

**Next steps: Done**
* **Your move:** Type `/cg` followed by the change you want, for example `/cg add tests for the missing-column and duplicate-hhid refusals`. To keep the setup files in git, say "commit the setup files".
* **Project:** Setup of `toypov` for the guide is complete and the project is ready for its first change.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I've stopped before changing anything. The risk tier is **elevated** (measured: `cg.py tier`), so I need your yes first.

**Why:** `headcount()` computes a number people will read: a poverty headcount. The survey file is cleared to read (recorded as Public), so the data raises no issue.

**What I'll do**
- **Goal:** add `headcount(dt, line = 3)` in `R/headcount.R`. It returns `sum(weight[welfare < line]) / sum(weight)`. "Below" means strictly less than, so a household exactly at the line counts as not poor.
- **It will fail loudly** (with an error) if `dt` has no `welfare` or `weight` column, if any of those values is NA, if a weight is 0 or less, or if `line` is not a single positive number.
- **Files:** `R/headcount.R` (new), `tests/testthat/test-headcount.R` (new), plus an `export(headcount)` line in `NAMESPACE` and `man/headcount.Rd`.
- **Out of scope:** `read_survey()` and its tests, `DESCRIPTION`, new dependencies (no collapse; data.table and base R only), other poverty measures, and committing.

**Checks, and what would count as failure**
1. **Value check:** `headcount(read_survey())` must equal **0.153846**, the number you gave me before any code ran. The tolerance is ±5e-7, half a unit in the 6th decimal. Anything outside that fails. If it fails, I fix the code and leave your expected value alone, unless an independent source shows it is wrong.
2. **Hand calculation:** I'll compute the same share by hand in base R, outside the package function, on the shipped survey. It must match check 1.
3. **Error tests:** a missing column, an NA weight and a bad `line` must each raise an error.
4. **Before and after:** the new test must fail before the function exists and pass after.
5. **Full package check:** `R CMD build . && R CMD check --no-manual`, the Run command in `.cg-docs/verification.md`. It must finish with no ERROR and no new WARNING. It uses a temporary library, so nothing goes into your R library.

Do you approve this contract, including "below" meaning strictly less than (`<`)?

**Next steps: Waiting on you**
* **Your move:** reply `yes`, or say what to change (for example "use <= for below").
* **Project:** this adds `headcount()` to toypov through the quick playbook. It is stopped at the contract, and the change, checks and work report come after your yes.

[exit code: 0]

### C2 yes

> Yes, proceed.

Contract approved. I've read the lang-r skills. I'm writing the test first so I can watch it fail before the function exists.

Measured: before the change, all 3 tests error with `could not find function "headcount"`. Now the function:

The NAMESPACE file is written by hand, so roxygen left it alone. I'm adding the export line myself.

All tests pass. The hand computation in base R gives 0.15384615, the same as the package. Now the full Run command, built and checked in a temp folder:

R CMD check passed with `Status: OK` (no errors, warnings or notes). Now the self-review against P3, P4 and P6, then the record.

I added `headcount(dt, line = 3)`. On the toy survey it returns **0.15384615**, which matches your 0.153846 within ±5e-7 (measured). It counts a household as poor only when welfare is strictly below the line. The package check ran clean, with `Status: OK`.

**What changed**
- `R/headcount.R` (new): the function and its help page source. It stops with an error on a missing column, a bad `line`, an empty table, an NA welfare, or a weight that is NA or 0 or less.
- `tests/testthat/test-headcount.R` (new): 13 checks.
- `NAMESPACE`: one line, `export(headcount)`. This file is written by hand, so I added the line directly.
- `man/headcount.Rd` (new): generated by roxygen2.

**Checks** (all measured, all verified)
1. **Value check:** the result is within ±5e-7 of 0.153846.
2. **Hand calculation:** a base R loop over the CSV, with no package code, also gives 0.15384615.
3. **Error tests:** each bad input raises an error.
4. **Before and after:** the tests failed before the function existed (3 errors) and pass now. On scratch copies I broke the code three ways: `<=` instead of `<`, weights ignored, and the weight check removed. The tests caught each one.
5. **Full package check:** `R CMD build . && R CMD check --no-manual` passed with `Status: OK`.

**One check changed after it failed.** I first wrote `expect_equal(..., tolerance = 5e-7, scale = 1)`. testthat warned that it ignores `scale`, so the tolerance became relative, about ±7.7e-8, tighter than we agreed. The line now checks the absolute difference instead. Your 0.153846 and the ±5e-7 did not change.

**Self-review** (my own review, not an independent one): P3, P4 and P6 pass. I added one guard beyond the contract, for an empty table. It stops a division by zero and has its own test.

**Not checked**
- No independent reviewer looked at this.
- No cross-check in Stata.
- The Doctor command and `cg.py repro`/`guard`/`evidence` aren't installed.
- No household sits exactly at 3. So on this survey `<` and `<=` give the same value; the hand-built test covers that case.

**Noticed but not touching**
- The R skills ask for `cli_abort()` and `collapse::fmean()`. Neither package is a dependency, so I used `stop()` and base R, as `read_survey()` does.
- `NAMESPACE` is written by hand, not by roxygen.
- The project has no `renv.lock`.
- `.cg-docs/verification.md` still says `draft`, although its Run command has now passed end to end.

Work report: `.cg-docs/work-reports/2026-11-26-add-headcount-poverty-headcount-ratio.md` (validated with 0 problems, `status: completed`). Nothing is committed.

The scratch builds, the temporary R library and the broken copies are in `~/temp/cg-headcount-check`. You can delete that folder now.

**Next steps: Done**
* **Your move:** Nothing. To commit, reply "commit it", and the work report goes in the same commit as the change.
* **Project:** this adds `headcount()` to toypov, and it is finished and uncommitted. `.cg-docs/verification.md` is out of date: its status still says draft.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record.

The NAMESPACE file is maintained by hand, so I'll add the export myself.

That was my bad argument, not the package. I'll check the export without installing anything:

I added `n_households(dt)` in `R/n_households.R`. It returns the number of distinct `hhid` values, and for the toy survey that's **20**. The tests pass (21 checks, 0 failures).

**A choice you should check:** "number of households" could mean two things.
- **What I built:** the unweighted count of households in the sample.
- **The other reading:** the weighted number, meaning how many households the survey stands for. Here that's 45.5, the sum of `weight`.

If you meant the weighted number, it's a one-line change.

**How it behaves:**
- **Repeated households:** it counts distinct `hhid` values, not rows. If a household appears on more than one row, as in person-level data, it is counted once.
- **Bad input:** it stops with an error if `hhid` is missing or has an NA. The error messages follow the style of `headcount()`. They use `stop()`, like the rest of the package, which doesn't depend on `rlang` or `cli`.
- **Tests** are in `tests/testthat/test-n_households.R`. They check the toy survey count, that repeated households and weights aren't counted extra, an empty table, and the two errors.
- **Documentation:** `man/n_households.Rd` was generated by roxygen2.
- **Export:** roxygen skips `NAMESPACE` because that file isn't generated by roxygen, so I added `export(n_households)` by hand. I confirmed the function is exported.

Nothing is committed. Compound GPID status showed no active work, so this change has no record in `.cg-docs/`.

**Next steps: Done**
* **Your move:** Nothing. If you meant the weighted count, reply "make it weighted".
* **Project:** toypov now has `read_survey()`, `headcount()` and `n_households()`, all uncommitted on `main`. Type `/cg` if you want later changes run with checks and a record.

[exit code: 0]
