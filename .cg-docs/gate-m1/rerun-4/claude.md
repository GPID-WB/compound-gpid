### B1 setup

> /cg

Setup is not done yet. I've only read files so far, nothing is written, and I need your yes before writing anything. Status shows the project is at `phase: setup` because `.cg-docs/config.json` doesn't exist, so the guide opened the setup playbook.

## What I found

- **Files:** 7 in total. There are 3 `.R` files (`R/read_survey.R`, `tests/testthat.R`, `tests/testthat/test-read_survey.R`), 1 `.csv`, plus `DESCRIPTION`, `NAMESPACE` and `LICENSE`. It's an R package called `toypov`.
- **How outputs are made:** there's no `Makefile`, `_targets.R` or main script. The only output is the exported function `read_survey()`, and two testthat edition 3 tests check it.
- **Data:** 1 file, `inst/extdata/survey.csv`. I haven't opened it. `DESCRIPTION` calls it "synthetic … the data are made up", but only you can classify it. Until you do, it counts as restricted data.
- **Already here:** no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/`, `GLOSSARY.md` or version 1 files.

## Proposal

**1. Packs:** `core` and `lang-r`. Both are installed (version 1.99.0.9000).

**2. Pack setting:** `lang-r.r-syntax = data.table-collapse`. Evidence: `DESCRIPTION:9-10` imports `data.table`, `NAMESPACE:2` has `importFrom(data.table, fread)`, and `R/read_survey.R:8` calls `fread()`. This is also the pack's default.

**3. Verification profile (draft, under P4):**
- **Run:** not found. No file in the project names one. The closest thing is running the tests with `Rscript -e 'testthat::test_local()'`. That's my inference from `tests/testthat.R` and edition 3, not a command the project states, and I haven't run it. Should I record it, or leave Run as "not found"?
- **Doctor:** not found.
- **Outputs map:** `read_survey()` in `R/read_survey.R`. The tests in `tests/testthat/test-read_survey.R` check it: the shipped survey has 20 rows with columns `hhid`, `welfare`, `weight`, and a weight of 0 is rejected. These are input checks only. Nothing yet validates the data against an independent source.

**4. Data rules (under P12):** only you can answer these. Please reply with:
- the classification of `inst/extdata/survey.csv`, in your organization's words;
- the highest level this coding agent (Claude Code) may read;
- if you know them, your organization's classification levels, from public to most restricted.

Example answer you can copy:
`survey.csv = Public; Claude Code may read up to Official Use Only; levels: Public;Official Use Only;Confidential;Strictly Confidential`

**5. Files I would create** (from `cg.py setup --dry-run`):
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md` (holding `@AGENTS.md`)
- `.Rbuildignore` (because this is an R package)

**Assumptions:**
- "Claude Code" is the name you want recorded for this coding agent.
- The setup command will commit nothing.

**Next steps: Waiting on you**
* **Your move:** Reply with a clear yes to items 1–3 and 5. Say whether to record the test command as Run. Give the data answers from item 4, for example: `yes; record test_local as Run; survey.csv = Public; Claude Code may read up to Public; levels: Public;Official Use Only;Confidential;Strictly Confidential`
* **Project:** Setting up Compound GPID in `toypov`. Once you confirm, I'll write the five files and check that status shows `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Setup is finished, and status now shows the project is ready for work.

**What's set up**
- The project uses the `core` and `lang-r` packs, and both are installed.
- R code will follow the `data.table-collapse` style.
- `inst/extdata/survey.csv` is recorded as Public, and Claude Code is approved to read Public data.
- I didn't record your organization's classification levels because you didn't give them. Setup works without them.

**Files created (nothing committed)**
- `.cg-docs/config.json`: the packs, the R setting, the data classification and the approved tool.
- `.cg-docs/verification.md`: the draft verification profile. Run and Doctor are recorded as "not found". The only check listed is the existing tests for `read_survey()`.
- `AGENTS.md`: the Compound GPID instructions for coding agents.
- `CLAUDE.md`: one line, `@AGENTS.md`.
- `.Rbuildignore`: excludes `.cg-docs`, `AGENTS.md` and `CLAUDE.md` from the package build.

**Status check (run after setup)**
```
phase: ready
stops: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
```

**Still open**
- **The verification profile is only a draft.** You didn't say whether the test command `Rscript -e 'testthat::test_local()'` should count as the Run command, so I recorded "not found". The profile stays a draft until a Run command is recorded and has been run from start to finish. I haven't run the tests.
- **Nothing checks the data's results yet.** The tests only confirm the survey file's shape (20 rows, the three columns, a zero weight is refused). Nothing compares the data against an independent source.

**Next steps: Done**
* **Your move:** Type `/cg` followed by the change you want, for example `/cg record testthat::test_local() as the Run command and run it`. To keep the new files, ask me to commit them.
* **Project:** Compound GPID is set up in `toypov` and the project is ready for its first piece of work. The verification profile is still a draft.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

This is a hard stop under the Compound GPID quick playbook, so I haven't changed any files yet.

**What you asked for:** add `headcount(dt, line = 3)` to toypov. It returns the weighted share of households whose welfare is below the line, and comes with a testthat check. The smallest change is one new file `R/headcount.R`, one new test file `tests/testthat/test-headcount.R`, and one `export(headcount)` line in `NAMESPACE`. I won't touch `read_survey()`, the survey data or the verification profile.

**Risk check:** one line is yes, so I need your approval before going on.
- **Line 1: yes.** The function produces a poverty headcount that people will read. New code that computes such a number counts, even though no headcount existed before.
- The other lines are no. The data is cleared as `Public` for Claude Code in `.cg-docs/config.json`. There is no personal data and nothing irreversible. There's no new dependency: I'll use data.table, which the package already imports, and not collapse, which would be a new dependency. I'm adding a new export, not changing one. It's 3 files. Your 0.153846 gives a check that can fail.

**Proposed contract:**
- **Goal:** `headcount(dt, line = 3)` returns `sum(weight[welfare < line]) / sum(weight)`. "Below" means strictly below (`<`), the usual FGT0 definition. Measured: no household in the toy survey has welfare of exactly 3, so `<` and `<=` give the same number here. The choice only matters for other data.
- **Fails loudly:** it stops with an error if `dt` lacks `welfare` or `weight`, if either has missing values, if a weight is ≤ 0, or if `line` is not a single positive number.
- **Out of scope:** other poverty measures, changes to `read_survey()`, and generating roxygen `man/` pages. The package has no `man/` folder and `NAMESPACE` is written by hand, so I'll add roxygen comments and edit `NAMESPACE` by hand.
- **Checks, and what would mean failure:**
  1. `headcount(read_survey())` equals 0.153846 within a tolerance of 1e-6. This is your expected value, stated before anything ran. It fails if the weights are ignored or the line is wrong. A mismatch is reported as "not verified"; I won't change the expected value.
  2. A hand-built 3-row table with one household exactly at the line, worked out by hand. It fails if the code uses `<=` or ignores the weights.
  3. Error tests for a missing column and an NA weight.
  4. The existing `read_survey` tests still pass.

  I'll run the tests in a temporary R library, not your own, and see check 1 fail before the function exists.

Do you approve this contract? And is "strictly below" (`welfare < line`) the definition you want?

**Next steps: Waiting on you**
* **Your move:** reply "yes" to approve as written, or "yes, but use <=" if a household exactly at the line should count as poor.
* **Project:** toypov has only `read_survey()` so far. This adds its first poverty measure, and the work report will be written after the checks run.

[exit code: 0]

### C2 yes

> Yes, proceed.

I added `headcount()` and its tests. All checks pass, and on the toy survey it returns 0.1538461538, which matches your 0.153846 to 6 decimals. Nothing is committed.

One thing to know first: I changed the tolerance in the main test after its first run. I had written it with testthat's `tolerance = 1e-6`, which is a relative tolerance, so it failed by a tiny margin. The contract meant an absolute difference of 1e-6, and you gave the value to 6 decimals. The test now checks `abs(x - 0.153846) < 1e-6`. The expected value itself did not change.

**What changed**
- `R/headcount.R` (new): returns `sum(weight[welfare < line]) / sum(weight)`. It stops with an error on a missing column, a missing or non-positive weight, missing welfare, or a `line` that isn't a single positive number.
- `NAMESPACE`: added `export(headcount)`.
- `tests/testthat/test-headcount.R` (new): three tests.

**Checks** (measured; the package was installed into a temporary library, not your own)

| Check | Verdict |
|---|---|
| Before the function existed: the 3 headcount tests fail, the `read_survey` tests pass | verified |
| `headcount(read_survey())` is within 1e-6 of 0.153846 | verified |
| Hand-worked 3-row case with one household exactly at the line gives 1/6 | verified |
| Errors for a missing `weight` column, a missing weight value, and `line = NA` | verified |
| The existing `read_survey` tests still pass | verified |
| A version that ignores weights fails 2 tests; a version using `<=` fails 1 | verified |

**Where the number comes from** (measured): 4 of 20 households are below 3, with weight 7 out of 45.5. A separate count with awk directly on the CSV gives the same 7 / 45.5. Without weights the share would be 0.20. No household is exactly at 3, so `<` and `<=` give the same number on this data.

**Self-review against the project's principles:**
- **P3 (deterministic):** pass.
- **P4 (prove it works):** pass.
- **P6 (smallest change):** pass, with one note. The errors for missing welfare and for a weight of 0 or below are not tested, so removing them wouldn't break any test. The contract asks for them, so they stay.

**Not checked:**
- `R CMD check`: the project has no run command set up yet.
- Tests for the two error cases above.
- A review by a fresh agent: this was my own self-review only.

**Noticed but not touching:**
- `.cg-docs/verification.md` doesn't list `headcount()` among the outputs yet.
- The package has no `man/` help pages, so the documentation comments aren't turned into help files.

The work report is `.cg-docs/work-reports/2026-11-25-add-headcount-function.md`, marked `completed`.

**Next steps: Done**
* **Your move:** Nothing. To commit, reply "commit it"; the work report will go in the same commit as the change.
* **Project:** toypov now has its first poverty measure. `.cg-docs/verification.md` is out of date: it needs a `headcount()` entry.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

I added `n_households(dt)` in `R/n_households.R`. It returns the number of distinct `hhid` values in the survey, which is 20 for the shipped survey. All 12 package tests pass, including the new ones in `tests/testthat/test-n_households.R`.

- **Weights are not used.** It counts the households that were interviewed, not how many households they stand for. If you wanted the weighted total, that would be `sum(dt$weight)`, which is a different number.
- **Repeated or missing IDs:** a household ID that appears twice is counted once. The function stops with an error if the `hhid` column is missing or has empty values.
- **Export:** I added `export(n_households)` to `NAMESPACE` by hand, the same way `headcount` is already listed there.

This change went through without `/cg`, so `.cg-docs/` has no work report for it.

**Next steps: Done**
* **Your move:** Nothing. If you want this change in the project record, type `/cg` and ask it to record `n_households()`.
* **Project:** `toypov` now has `read_survey()`, `headcount()` and `n_households()`, none committed yet. The outputs map in `.cg-docs/verification.md` still lists only `read_survey()`, so it is out of date.

[exit code: 0]
