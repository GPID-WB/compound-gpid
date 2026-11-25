### B1 setup

> /cg

I haven't written anything yet. The project has no Compound GPID setup, so the guide opened the **setup** playbook. I've only read files so far, and a dry run of the setup command confirmed that nothing changed. Here is the proposal for you to confirm.

**What I found** (measured)
- 7 files: 3 `.R`, 1 `.csv`, plus `DESCRIPTION`, `NAMESPACE` and `LICENSE`. This is the R package `toypov`, with one exported function, `read_survey()`.
- The only checks are 2 testthat tests in `tests/testthat/test-read_survey.R`. There is no `_targets.R`, `Makefile`, main script or `renv.lock`.
- 1 data file: `inst/extdata/survey.csv`. I did not open it. Until you classify it, it counts as restricted data (P12).
- There is no `AGENTS.md`, `CLAUDE.md`, `.cg-docs/` or `GLOSSARY.md`, and no files from version 1.

**1. Packs:** `core` and `lang-r`. Both are installed on this machine.

**2. Pack setting:** I recommend `lang-r.r-syntax = data.table-collapse`. The code supports it: `DESCRIPTION` imports `data.table`, `NAMESPACE` has `importFrom(data.table, fread)`, and `R/read_survey.R:8` calls `fread(path)`. It is also the pack's default.

**3. Verification profile (P4), draft:**
- **Run:** not found. This is a package, and no command produces outputs from inputs.
- **Doctor:** not found.
- **Outputs:** `read_survey()` returns a data.table with 20 rows and the columns `hhid`, `welfare` and `weight`, and it refuses a weight that is not positive. Both are proven by `tests/testthat/test-read_survey.R`.
- **Existing check:** the testthat suite. One way to run it is `Rscript -e 'testthat::test_local()'`, but the project doesn't name a command, so you'd be choosing one. Tell me which you want, or leave it as "not found".

**4. Data rules (P12):** only you can answer these. `DESCRIPTION` says the data are made up, but the classification is still your call. Please reply in this form:
> `inst/extdata/survey.csv = Public`; highest level Claude Code may read: `Public`; levels: `Public;Official Use Only;Confidential;Strictly Confidential`

Leave out any part you don't know yet. That item stays open, and the file stays restricted.

**5. Files that will be written** (all new, all in the project root):
- `.cg-docs/config.json`
- `.cg-docs/verification.md` (stays `draft`)
- `AGENTS.md` (the pointer block)
- `CLAUDE.md` (the line `@AGENTS.md`)
- `.Rbuildignore` (because this is an R package)

I'll commit nothing.

**Assumptions:** I named the coding agent "Claude Code", and I treated the testthat suite as the project's only check. Correct either one now if it's wrong.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` plus the data rules in the form above (for example `yes; inst/extdata/survey.csv = Public; Claude Code may read Public; levels Public;Official Use Only;Confidential;Strictly Confidential`). Add a test command if you want one in the profile.
* **Project:** toypov has no Compound GPID setup yet. Once you confirm, I write the five files and check that status shows `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Setup is done. Status now shows `phase: ready` and `stops: none`.

**What you confirmed:** the packs `core` and `lang-r`, with `r-syntax = data.table-collapse`. You classified `inst/extdata/survey.csv` as Public and said Claude Code may read Public data.

**Files written** (all new; nothing committed):
- `.cg-docs/config.json`: the packs, the setting, the data rule and the approved tool.
- `.cg-docs/verification.md`: the draft profile. Run and Doctor say "not found", and the outputs map points `read_survey()` at its two testthat tests.
- `AGENTS.md`: the pointer block.
- `CLAUDE.md`: the line `@AGENTS.md`.
- `.Rbuildignore`: excludes `.cg-docs`, `AGENTS.md` and `CLAUDE.md` from the package build.

**Status lines** (measured, from a rerun after writing):
```
phase: ready
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
packs-missing: none
stops: none
```

**Still open:**
- The verification profile stays a draft. There's no Run command and no Doctor command, and I haven't run the tests.
- You didn't give the names of your classification levels, so they aren't recorded.

**Next steps: Done**
* **Your move:** Type `/cg` followed by the change you want to make to toypov. Status will open the quick playbook for it.
* **Project:** toypov is set up for Compound GPID. The verification profile is still a draft until a Run command is chosen and run.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

`/cg` started the guide. Status: phase `ready`, no open work, no stops. It picked the **quick** playbook.

**Restated request.** Add an exported function `headcount(dt, line = 3)` that returns the weighted share of households whose `welfare` is below `line`, plus a testthat check that the toy survey gives 0.153846. The smallest change is:
- a new `R/headcount.R`
- one `export(headcount)` line in `NAMESPACE`
- a new `tests/testthat/test-headcount.R`
- a new row in the outputs map in `.cg-docs/verification.md`

I won't touch `read_survey()`, `DESCRIPTION` or the data.

**Risk check**

| # | Answer | Why |
|---|---|---|
| 1 | **yes** | New code that computes a poverty headcount, a number people will read. |
| 2 | no | `inst/extdata/survey.csv` is `Public`, and `approved-tools` lists Claude Code at `Public`. |
| 3 | no | The data has no personal details and nothing touches credentials. |
| 4 | no | Nothing is deleted, pushed or published. |
| 5 | no | It adds a new function and changes no existing one. I'll write it with data.table and base R only, so `DESCRIPTION` gets no new dependency such as collapse. |
| 6 | no | Four files, and no open design choice beyond the two points below. |
| 7 | no | The test fails if the result isn't 0.153846. |

Line 1 is yes, so the playbook stops here until you approve.

**Proposed contract**
- **Goal:** `headcount(dt, line = 3)` returns `sum(weight[welfare < line]) / sum(weight)`.
- **Two choices for you to confirm:**
  - "Below" means strictly `<`. A household exactly on the line counts as not poor. No toy household sits exactly at 3, so this doesn't change your 0.153846.
  - The function stops with an error, and never returns a quiet fallback, when:
    - `welfare` or `weight` is missing;
    - either has an NA;
    - a weight is not positive;
    - `line` is not a single positive number.
- **Out of scope:** other FGT measures, grouped headcounts, roxygen-built `man/` pages, and a new run command in the verification profile.
- **Checks:**
  1. `testthat::test_local()` in a temporary library. It fails if `headcount(read_survey())` isn't 0.153846 within tolerance 1e-6, or if any existing test breaks.
  2. One new test that expects an error for an NA weight.
  3. Before I write the function, I'll run the new test to watch it fail.
- **Independent reference:** your 0.153846, which you gave before any code ran.

Do you approve this contract, including strict `<` and the error behaviour? A yes lets me make the change, run the checks and write the work report.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve as written, or say what to change (for example "use `<=`").
* **Project:** quick-playbook work on `toypov`. Nothing has been changed yet. After your yes, I make the change, run the checks and write the work report.

[exit code: 0]

### C2 yes

> Yes, proceed.

I added `headcount(dt, line = 3)`, and it gives **0.1538462** for the toy survey, which matches your 0.153846 to 6 decimals (measured). The full test suite passes. Nothing is committed.

**One departure from what you approved:** the test as written in the contract failed on rounding alone. The 1e-6 tolerance is relative in testthat 3, which is tighter than a figure given to 6 decimals. The test now rounds the result to 6 decimals and compares it exactly with 0.153846. Your expected value is unchanged, and the work report records the change and the reason.

**What changed**
- `R/headcount.R` (new): returns the weighted share of households with welfare strictly below `line`. It stops with an error if a column is missing, welfare or weight has an NA, a weight is zero or negative, or `line` is not a single positive number.
- `NAMESPACE`: adds `export(headcount)`.
- `tests/testthat/test-headcount.R` (new): one test for your 0.153846 and one that expects an error for a missing weight.
- `.cg-docs/verification.md`: two new rows in the outputs map.

**Checks** (all measured, all verified)
- **Before the change:** the 3 existing expectations passed, and both new tests failed because `headcount` didn't exist yet.
- **After the change:** `testthat::test_local(".")` ran 5 expectations with 0 failures, exit code 0.
- **Can the tests catch mistakes?** In a scratch copy I broke the function twice. An unweighted version failed the 0.153846 test, and removing the weight check failed the missing-weight test.
- **Bad `line` values:** `NA`, `-1`, `c(1, 2)` and `"3"` were all rejected. I ran this by hand; it is not in the test suite.
- **Rerun:** the result is identical. The survey file is unchanged.

**My own review** (the agent that wrote the code reviewed it; no independent reviewer ran)
- Reproducibility: flagged, but the problem was there before this change. The project has no `renv.lock`, so package versions aren't pinned.
- Proof: pass.
- Smallest change: pass. Only the four planned files changed and no new package was added.

**Not checked**
- No household sits exactly at 3, so no test tells "below" (`<`) apart from "at or below" (`<=`).
- Missing welfare and missing columns aren't in the tests.
- I didn't run `R CMD check` or `devtools::document()`, so there's no help page for `headcount()`.

**Noticed but not touching:** the package has no `man/` folder, there's no `renv.lock`, and the verification profile is still a draft with no run command.

The work report is at `.cg-docs/work-reports/2026-11-25-add-weighted-headcount-function.md`, with status `completed`.

**Next steps: Done**
* **Your move:** Nothing. If you want it committed, reply `commit it` and the work report goes in the same commit as the change.
* **Project:** `toypov` now has `headcount()` with tests. The verification profile is still a draft with no run command.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

I added `n_households(dt)` in `R/n_households.R`. It returns the number of distinct households (`hhid`) in the survey, which is **20** for the synthetic survey. All 9 tests pass: 3 are new and 6 were already there.

- **What it counts:** households in the sample, without weights. If you meant the estimated number of households in the population, that is the sum of `weight`, which is 45.5 here. I can switch it or add a second function.
- **How it behaves:** a repeated `hhid` is counted once. It stops with an error if the `hhid` column is missing or has empty values.
- **Other files:** the tests are in `tests/testthat/test-n_households.R`, and I added `export(n_households)` to `NAMESPACE` by hand.

This ran outside `/cg`, so nothing was written to `.cg-docs/`.

**Next steps: Done**
* **Your move:** Nothing. If you meant the weighted count, reply "use the weighted count".
* **Project:** `toypov` now has `read_survey`, `headcount` and `n_households`, none of them committed yet. The Compound GPID status is "ready" with no active work.

[exit code: 0]
