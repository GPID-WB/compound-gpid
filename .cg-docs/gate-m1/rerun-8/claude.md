### B1 setup

> /cg

**Setup proposal.** I only read files. Nothing has been written.

**What I found**
- This is a small R package, `toypov`. It has one function, `read_survey()`, and one test file.
- There are 7 files in the project. They are `.R`, `.Rd`, `DESCRIPTION`, `NAMESPACE`, `LICENSE`, `.csv` and `tests/testthat.R`.
- There is one data file, `inst/extdata/survey.csv`. Its columns are `hhid`, `welfare` and `weight`.
- The repository has no `_targets.R`, no Makefile and no lockfile.

**1. Packs.** I recommend `core` and `lang-r`. Both are installed on this machine, and `lang-r` is there because of `DESCRIPTION` and the `.R` files.

**2. Settings.** I recommend `lang-r.r-syntax=data.table-collapse`. `DESCRIPTION` imports `data.table`, and `R/read_survey.R` uses `fread`. This is also the default.

**3. Verification profile (draft).**
- **Run command:** not found. The package makes no outputs.
- **Doctor command:** not found. I suggest `devtools::test()` for the test file and `devtools::check()` for the whole package, but I did not find either in the project.
- **Outputs:** `read_survey()` should return a data.table with 20 rows and the columns `hhid`, `welfare` and `weight`. It should refuse a missing column, or a welfare or weight value that is missing or not positive, and a duplicate `hhid`. Only the 20 rows and the zero-weight refusal have tests today.

**4. Data rules.** Only you can answer this, and I need it for `inst/extdata/survey.csv`. The `DESCRIPTION` calls the data synthetic, but that is not a classification.
- Which classification does `survey.csv` have, in your organization's words?
- What is the highest level your organization lets this coding agent read?
- If you know them, which classification levels does your organization use, from public to most restricted?

Example answer you can copy: `survey.csv=Public; Claude Code may read up to Public; levels: Public;Official Use Only;Confidential`

Until you answer, `survey.csv` is treated as restricted data.

**5. Files I would create** (from the `--dry-run`):
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`, holding `@AGENTS.md`
- `.Rbuildignore`, so the package check does not report these files

**Assumptions:** I name the coding agent "Claude Code". I commit nothing.

**Next steps: Waiting on you**
* **Your move:** Reply "yes" to approve packs, setting and files, and give the data answers. For example: `yes; survey.csv=Public; Claude Code may read up to Public; levels: Public;Official Use Only;Confidential`. To leave the data rules open, reply `yes, data rules open`.
* **Project:** Setup of `toypov` is waiting for your approval. After that the guide can start work from `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Setup is done, and status now prints `phase: ready` and `stops: none`.

**What I found:** `toypov` is an R package with 7 files. It has one function, `read_survey()`, one test file, and one data file, `inst/extdata/survey.csv`. There is no `_targets.R`, Makefile or lockfile.

**What you confirmed:** packs `core` and `lang-r`, `lang-r.r-syntax=data.table-collapse`, and `survey.csv=Public`. I named the coding agent "Claude Code" and set it to read up to `Public`.

**Files written:**
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`, holding `@AGENTS.md`
- `.Rbuildignore`

I filled `.cg-docs/verification.md` with the draft. Its Run and Doctor commands are "not found", and the outputs map describes `read_survey()` and its tests. I committed nothing.

**Status lines:**
- `settings: lang-r.r-syntax=data.table-collapse`
- `data: inst/extdata/survey.csv=Public`
- `packs-missing: none`

**Still open:**
- The verification profile stays `draft`. It has no Run or Doctor command yet.
- You did not give the classification level names, so I left `classification-levels` out of the config.
- Only the 20 rows, the column names and the zero-weight refusal have tests. The other refusals have no test.

**Next steps: Done**
* **Your move:** Type `/cg` followed by what you want done, for example `/cg add tests for the missing-column and duplicate hhid refusals`. If you want setup changes committed, tell me.
* **Project:** Setup of `toypov` is finished and the project is ready for work. The next task is whatever you ask the guide to do.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

This is a hard stop under the quick playbook: the change is new code that computes a number someone will read, so I haven't touched any files yet.

**Risk check (step 2)**

| # | Answer | Why |
|---|---|---|
| 1 | **Yes** | `headcount()` is new code that computes a share people will read. |
| 2 | No | `inst/extdata/survey.csv` is listed as `Public` in status. |
| 3 | No | The data are synthetic and hold no personal data, credentials or access rights. |
| 4 | No | Nothing is deleted, overwritten or published. |
| 5 | No | It adds a function and no dependency. `data.table` is already in Imports. |
| 6 | No | About 3 files: `R/headcount.R`, a test file, and `NAMESPACE`/`man` from roxygen. |
| 7 | No | Your 0.153846 is an independent value to check against. |

**Contract**
- **Goal:** add `headcount(dt, line = 3)` in `R/headcount.R`. It returns `sum(weight[welfare < line]) / sum(weight)` as a single number. It is exported and documented with roxygen2, in `data.table`/`collapse` style per the project setting.
- **Fail loudly:** it errors when `welfare` or `weight` is missing, when either has an `NA`, or when a weight is negative or the weights sum to zero. It never falls back silently.
- **Out of scope:** `read_survey()`, the data file, any other poverty measure (gap or severity), and any other weighting scheme.
- **Checks and failure conditions:**
  1. `tests/testthat/test-headcount.R` runs `headcount(read_survey(<toy survey>))`. It expects 0.153846 with `tolerance = 5e-7`, which is six decimals. Failure is any value outside that tolerance.
  2. A small hand-made table with a known answer, plus a check that `line` changes the result.
  3. Error tests for the loud-failure cases above.
  4. Run the full test suite in a temporary library, so nothing goes into your R library.
- **Strictness:** `<` is strict, so a household exactly at the line is not poor. Tell me if you want `<=`.
- **Your 0.153846:** I'll treat it as the independent reference. If the code gives a different value, I fix the code and don't touch the expected value.
- **Record:** a work report in `.cg-docs/`.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to start, or tell me what to change, for example `yes, but use <=`.
* **Project:** Quick work on the `headcount()` request is stopped at the contract. Nothing is edited yet, and the next step is the change, the checks and the work report.

[exit code: 0]

### C2 yes

> Yes, proceed.

`headcount(dt, line = 3)` is added and the full test suite passes (13 passed, 0 failed). On the toy survey it returns 0.1538461538, which is within 5e-7 of your 0.153846 (measured). The work report is written and marked `completed`.

**Changed**
- `R/headcount.R`: the new exported function, computing `sum(weight[welfare < line]) / sum(weight)`. It stops with an error on missing columns, `NA` values, negative or zero-sum weights, or a bad `line`.
- `tests/testthat/test-headcount.R`: your reference value, a small weighted example, the strict-line case, and the error cases.
- `NAMESPACE`: added `export(headcount)`.
- `man/headcount.Rd`: generated by roxygen2 in a scratch copy and copied in. I did not run roxygen on the real tree because it skips the hand-written `NAMESPACE`.

**Checks** (tests run on a copy installed in a temporary library, so nothing went into your R library; all verified)
- Toy survey result against your 0.153846.
- Weighted and strict-line cases.
- Loud failures on bad input.
- Full suite with no regressions.

**One check changed after it failed.** My first test used `expect_equal(tolerance = 5e-7)`. testthat reads that as a relative tolerance, so it rejected 0.15384615 against 0.153846. The contract's tolerance was absolute, at six decimals. The test now checks the absolute difference. The code did not change. The independent source is the arithmetic: the true value is 2/13 = 0.153846153…, which rounds to your 0.153846.

**Self-review:** P3, P4 and P6 all pass. This is a self-review, and the work report says so.

**Not checked:** `R CMD check` was not run, and I did not run the `<` versus `<=` choice past you.

**Noticed but not touching:** `NAMESPACE` is hand-written, so roxygen will not update it.

Work report: `.cg-docs/work-reports/2026-11-25-add-headcount-with-testthat-check.md`. Nothing is committed. Scratch files are in the session scratchpad and need no cleanup.

**Next steps: Done**
* **Your move:** Nothing. If you want it committed, say `commit this`, and the work report goes in the same commit.
* **Project:** The `headcount()` task is finished and the toy package now has `read_survey()` and `headcount()`. Nothing is queued next.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

I added `n_households(dt)`, which returns the number of rows in the survey as an integer. It counts households without weighting, since `read_survey()` already guarantees one row per household with a unique `hhid`. It stops with an error if `dt` isn't a data frame or data.table. The package tests all pass (16 pass, 0 fail).

- **Function:** `R/n_households.R`, with docs in `man/n_households.Rd`.
- **Export:** I added `export(n_households)` to `NAMESPACE` by hand, because roxygen2 skipped that file (it wasn't generated by roxygen2).
- **Tests:** `tests/testthat/test-n_households.R` covers the 20-household synthetic survey, an empty survey (returns 0) and non-data-frame input (errors).

This change did not go through `/cg`, so there is no work report or checks record for it. I did not commit anything.

**Next steps: Done**
* **Your move:** Nothing. To get a checked change with a record next time, start the request with `/cg`.
* **Project:** `toypov` now has `read_survey()`, `headcount()` and `n_households()`. The `headcount` work report exists in `.cg-docs/work-reports/`, and the new function has none.

[exit code: 0]
