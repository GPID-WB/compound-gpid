### B1 setup

> /cg

This project has no Compound GPID setup yet, so I read the files and have a setup proposal for you. Nothing is written until you say yes.

**What I found** (measured)
- It is an R package called `toypov`, with 8 tracked files. There is one function (`R/read_survey.R`), one test file, and one data file, `inst/extdata/survey.csv`. The README-style text in `DESCRIPTION` calls the data synthetic.
- There is no `_targets.R`, Makefile or main script. The only existing check is `tests/testthat`.
- There is no `AGENTS.md`, `CLAUDE.md` or `.cg-docs/`.

**Proposal**
1. **Packs:** `core` and `lang-r`. Both are installed on this machine. `lang-r` is there because of the `.R` files and `DESCRIPTION`.
2. **Setting:** `lang-r.r-syntax=data.table-collapse`. The code calls `fread` and imports `data.table` (`NAMESPACE`, `R/read_survey.R`). It uses no tidyverse packages. This is also the pack's default.
3. **Verification profile (draft):**
   - Run command: not found.
   - Doctor command: `devtools::test()`, or `R CMD check`. I did not run either.
   - Output to prove: `read_survey()` returns 20 rows with columns `hhid`, `welfare` and `weight`, and rejects bad input. The two tests in `tests/testthat/test-read_survey.R` cover this.
4. **Data rules.** Only you can answer these. Please reply with something like:
   `survey.csv = Public; Claude Code may read up to Public; levels: Public;Official Use Only;Confidential`
   - Which classification does `inst/extdata/survey.csv` have, in your organization's words?
   - What is the highest level this coding agent may read?
   - What are your classification levels, from public to most restricted? You can skip this one.

   Until you answer, the file counts as restricted data, and I will not open it.
5. **Files I would write**, from the dry run:
   - `.cg-docs/config.json`
   - `.cg-docs/verification.md`
   - `AGENTS.md`, with the pointer block
   - `CLAUDE.md`, containing `@AGENTS.md`
   - `.Rbuildignore`, with the entries for `.cg-docs`, `AGENTS.md` and `CLAUDE.md`

   I would name the coding agent "Claude Code" in `approved-tools`. I will commit nothing.

**Assumptions:** the data file is not public until you say so, and no run command exists beyond the tests.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to accept the proposal as written, with the data answers if you have them. For example: `yes; survey.csv = Public; Claude Code may read up to Public`. Or tell me what to change.
* **Project:** Setup of `toypov` is at the proposal stage. After you confirm, I write the files and run status to check that it reads `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Setup is done. Status now prints `phase: ready` and `stops: none`.

**Found** (measured): an R package, `toypov`, with 8 tracked files and 1 data file. There is no run command, only the testthat tests.

**Written** (I ran `cg.py setup` with the options you confirmed):
- `.cg-docs/config.json`: packs `core` and `lang-r`, and the agent named "Claude Code" with access up to Public.
- `.cg-docs/verification.md`
- `AGENTS.md`, with the pointer block
- `CLAUDE.md`, containing `@AGENTS.md`
- `.Rbuildignore`

**Status lines:**
- `settings: lang-r.r-syntax=data.table-collapse`
- `data: inst/extdata/survey.csv=Public`
- `packs-missing: none`

**Verification profile** (I filled it in after the setup command):
- Run command: "not found".
- Doctor command: `Rscript -e 'devtools::test()'`. I did not run it.
- The outputs map lists `read_survey()` with the two tests as proof.
- Status is still `draft`. It stays that way until a Run command has been run from start to finish.

**Still open:**
- The Run command.
- The classification level names. You gave none, so `classification-levels` is not set.

Nothing is committed. `git status` shows 4 changed files, and the other changed file is `.Rbuildignore`.

**Next steps: Done**
* **Your move:** Type `/cg` followed by your first request, for example `/cg add a function that computes the headcount poverty rate`. Nothing is pending.
* **Project:** Setup of `toypov` is finished. The next step is the first piece of work, which the guide will route to the quick playbook.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

Hard stop: step 2 of the quick playbook has one line that is yes.

**What I understand you want:** a new exported `headcount(dt, line = 3)` in `R/headcount.R` that returns the weighted share of households with `welfare < line`. It comes with a testthat test in `tests/testthat/test-headcount.R`. I would leave `read_survey()`, the data file and `DESCRIPTION` alone. `NAMESPACE` and `man/` would change only if I regenerate them with roxygen.

**Risk check**
- **Line 1, yes.** New code that computes a share someone will read counts as a yes, even though no such number existed before.
- **Line 2, no.** `inst/extdata/survey.csv` is listed as `Public` in status, so I may read it.
- **Lines 3, 4, 5, 6, 7, no.**
  - It touches no personal data.
  - It deletes or overwrites nothing and pushes nothing.
  - It adds no dependency and alters no existing function. `data.table` is already imported.
  - It touches about three files.
  - A check exists that fails if the result is wrong.

**Contract**
- **Goal:** `headcount(dt, line = 3)` returns `sum(weight[welfare < line]) / sum(weight)`.
- **Failure handling:** it raises an error on missing columns, `NA` or non-positive weights, or a non-numeric `line`. It does not fall back silently.
- **Out of scope:** any other poverty measure, the `<=` versus `<` question beyond the strict `<` you described, and changes to `read_survey()`.
- **Check 1:** the test on the toy survey expects `0.153846`, compared with `tolerance = 5e-7` (six decimals). It fails if the value differs. I will run it before the function exists, when it should fail, and after, when it should pass.
- **Check 2:** a small hand-built table with a known answer, plus an expectation that the function errors on bad input.
- **Independent reference:** I added the weights by hand from the CSV. Households 3, 11, 14 and 19 are below 3, with total weight 7. The total survey weight is 45.5. 7/45.5 = 0.153846. This matches your number (inferred, not run).
- **Self-review:** I will judge the change against P3, P4 and P6 and record it as my own review. A work report goes in `.cg-docs/`. I will not commit unless you ask.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve this contract, or tell me what to change, such as `<=` instead of `<`.
* **Project:** Quick-work step 2 for `headcount()` in toypov is stopped for your approval. Next are the failing test, the function, the passing test and the work report.

[exit code: 0]

### C2 yes

> Yes, proceed.

`headcount(dt, line = 3)` is added, and on the toy survey it returns 0.15384615, matching your 0.153846. All 10 tests pass (measured).

- **Function:** `R/headcount.R` returns `sum(weight[welfare < line]) / sum(weight)`. It errors on a bad `line`, missing columns, NA welfare, or NA or non-positive weights.
- **Tests:** `tests/testthat/test-headcount.R` checks the toy-survey value, a small weighted case with a strict `<`, and the error cases. They failed before the function existed (3 failures) and pass after.
- **Independent check:** I added the weights by hand from the CSV: 7 / 45.5 = 0.153846 (measured).
- **Other files:** I added `export(headcount)` to `NAMESPACE` by hand, because roxygen skips that file. `man/headcount.Rd` was generated.
- **Check I changed:** my first toy-survey assertion used a relative `tolerance = 5e-7` and failed. I switched it to an absolute difference below 5e-7, which is the tolerance I stated in the contract. The expected value 0.153846 is unchanged.
- **Self-review:** P3, P4 and P6 all pass. This is my own review, not an independent one.
- **Work report:** `.cg-docs/work-reports/2026-11-25-add-headcount.md`, with `status: completed`.
- **Not checked:** `R CMD check`. Tests ran in a temporary library, which I deleted.
- **Noticed but not touching:** nothing.
- **Commit:** nothing is committed.

**Next steps: Done**
* **Your move:** To commit, reply `commit`. I would put the function, the test, `NAMESPACE`, `man/headcount.Rd` and the work report in one commit.
* **Project:** `headcount()` for toypov is finished and recorded. The `.cg-docs/`, `AGENTS.md`, `CLAUDE.md` and `.Rbuildignore` files were already untracked before this change.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

I added `n_households(dt)` in `R/n_households.R`. It returns the number of households as an integer, and it gives 20 on the shipped survey. The test suite passes (14 expectations, 0 failures).

- **What it counts:** The count is of survey rows, not the weighted population. If you meant the weighted total, use `sum(dt$weight)` instead.
- **Checks:** It stops with an error if `hhid` is missing, has NA values, or has duplicates, in the same style as `read_survey()`.
- **Other files:** I added tests in `tests/testthat/test-n_households.R`, generated `man/n_households.Rd`, and added `export(n_households)` to `NAMESPACE` by hand. roxygen2 refused to regenerate that file because it wasn't created by roxygen2.
- **Compound GPID:** I didn't open a playbook or write a work report, since that is the guide's job. `.cg-docs/work-reports/` has no report for this change.

**Next steps: Done**
* **Your move:** Type `/cg` if you want this change recorded and checked through the guide. Otherwise nothing.
* **Project:** `n_households()` joins `headcount()` and `read_survey()` in toypov. None of these changes are committed yet.

[exit code: 0]
