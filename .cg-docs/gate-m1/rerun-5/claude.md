### B1 setup

> /cg

I've looked through the project and written nothing. Below is the setup proposal; it needs your yes before I write anything.

## What I found
- **Files (measured):** 8 files. It's an R package called `toypov`: `DESCRIPTION`, `NAMESPACE`, `LICENSE`, one `.R` file, one `.Rd` file, two test `.R` files and one `.csv`. There is no existing `AGENTS.md`, `CLAUDE.md`, `.cg-docs/` or version 1 files.
- **How outputs are made:** no `_targets.R`, `Makefile` or main script. The package's output is the exported function `read_survey()`, and it has testthat tests (edition 3).
- **Data:** one file, `inst/extdata/survey.csv`. I did not open it. `DESCRIPTION` says the data are synthetic, but that is a description, not a classification. Until you classify the file, it counts as restricted data.

## Proposal

**1. Packs:** `core` and `lang-r`. Both are installed (version 1.99.0.9000).

**2. Pack settings:** I recommend `lang-r.r-syntax = data.table-collapse`. The code already uses data.table: `DESCRIPTION` lists `data.table` under Imports, `NAMESPACE:2` has `importFrom(data.table, fread)`, and `R/read_survey.R:8` calls `fread(path)`. It's also the pack's default.

**3. Verification profile (draft):**
- **Run:** not found. The project doesn't state one. The standard command for an R package is `R CMD build .` followed by `R CMD check toypov_0.0.1.tar.gz`, run against a temporary library (inferred). Should I use that?
- **Doctor:** not found.
- **Outputs:**
  - `read_survey()` returns 20 rows with columns `hhid`, `welfare`, `weight`. The proof is `tests/testthat/test-read_survey.R:1-5`.
  - It refuses a weight that is zero or negative. The proof is `tests/testthat/test-read_survey.R:7-11`.
  - No test covers the other three refusals: missing columns, bad welfare values and duplicate `hhid` (inferred from reading the code).

**4. Data rules:** only you can give these. Please answer in one reply, for example:

> `inst/extdata/survey.csv = Public`; Claude Code may read up to `Public`; levels: `Public;Official Use Only;Confidential;Strictly Confidential`

Leave out anything you don't know yet. That item stays open, and the file stays restricted data in the meantime.

**5. Files setup would write** (from `cg.py setup --dry-run`):
- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`, with the pointer block
- `CLAUDE.md`, containing only `@AGENTS.md`
- `.Rbuildignore`, which excludes `.cg-docs`, `AGENTS.md` and `CLAUDE.md`. It's needed because `DESCRIPTION` makes this an R package.

**Assumptions I'm making (correct me now):**
- You want this coding agent recorded as "Claude Code".
- I leave out the optional `--contact` setting.
- I commit nothing.

**Next steps: Waiting on you**
* **Your move:** reply with a clear yes, or with corrections, covering:
  - packs and setting: e.g. `yes to packs and r-syntax`
  - the data rules, in the format of the example in section 4
  - whether to use `R CMD build` + `R CMD check` as the Run command
* **Project:** this is Compound GPID setup for `toypov` (phase: setup, no config yet). Once you confirm, I write the five files and check that status shows `phase: ready`.

[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Setup is done. Status now shows `phase: ready` with no stops.

**What I wrote** (nothing is committed):
- `.cg-docs/config.json` records:
  - the packs `core` and `lang-r`
  - the setting `lang-r.r-syntax = data.table-collapse`
  - `inst/extdata/survey.csv` as Public
  - Claude Code approved to read Public data
- `.cg-docs/verification.md` holds the verification profile. It's still a draft:
  - **Run:** `R CMD build . && R CMD check toypov_0.0.1.tar.gz`, run against a temporary library. I took your "Yes" to cover this command.
  - **Doctor:** not found.
  - **Outputs:** the two tested behaviours of `read_survey()` are listed with their test lines. The three untested refusals say "nothing yet".
- `AGENTS.md` has the Compound GPID pointer block.
- `CLAUDE.md` contains `@AGENTS.md`.
- `.Rbuildignore` excludes `.cg-docs`, `AGENTS.md` and `CLAUDE.md` from the package build.

**Status after setup:**
```
phase: ready
stops: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
packs-missing: none
```

**Still open:**
- **Verification profile:** it stays a draft until the Run command has been run from start to finish. It also has no Doctor command, and three checks in `read_survey()` have no tests.
- **Classification levels:** you didn't give the full list of levels, so it isn't recorded. Only the level Public is in use.
- **Not checked:** I haven't run any command from the profile.

**Next steps: Done**
* **Your move:** type `/cg` followed by the change you want, for example `/cg add tests for read_survey's missing-column and duplicate-hhid checks`. If you want the five new files committed, say `commit the setup files`.
* **Project:** `toypov` is set up for Compound GPID and ready. The next `/cg` opens the quick playbook. You can delete the test folder `<project>` once this trial is over.

[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I've worked out what the change involves, checked the data, and stopped for your approval, as the playbook requires.

## What you asked for

Add `headcount(dt, line = 3)` to toypov. It returns the share of households with welfare strictly below `line`, weighted by `weight`. Add a testthat check that the shipped survey gives 0.153846. I won't touch `read_survey()` or its tests.

## Risk check: one line is yes, so I've stopped here

| # | Answer | Why |
|---|---|---|
| 1 | **yes** | The function computes a poverty headcount, an estimate people will read. |
| 2 | no | The status output lists `inst/extdata/survey.csv` as `Public`, and `config.json` approves Claude Code at `Public`. |
| 3 | no | There's no personal data, no credentials and no access rights involved. |
| 4 | no | Nothing gets deleted, pushed or released. |
| 5 | no | It adds a new export and no new dependency. I'll use base R and data.table (`sum(weight[welfare < line]) / sum(weight)`), not collapse, so `Imports` stays the same. |
| 6 | no | It touches four files: `R/headcount.R`, `tests/testthat/test-headcount.R`, `NAMESPACE` and `man/headcount.Rd`. |
| 7 | no | Checks that would fail if the code were wrong are listed below. |

## Contract

- **Goal:** export `headcount(dt, line = 3)`, which returns `sum(weight[welfare < line]) / sum(weight)`. "Below" means strictly less than: a household at exactly `line` doesn't count as poor. No household in the toy data sits exactly at 3, so this doesn't affect your expected value.
- **It fails loudly when:** `dt` lacks `welfare` or `weight`, either column has an NA, a weight is not positive, or `line` is not a single finite number. Each of these raises an error, never a fallback.
- **Out of scope:** other poverty measures (gap, severity), more than one line at a time, and any change to `read_survey()`.
- **Checks, with what would count as failure:**
  1. `expect_equal(headcount(read_survey()), 0.153846, tolerance = 1e-6)`. Failure: any other value.
  2. I checked your figure by hand against the CSV (measured). Four households fall below 3 (ids 3, 11, 14, 19), with weights totalling 7 out of 45.5, and 7 / 45.5 = 0.1538462. The unweighted share would be 0.20, so the test also catches a function that forgets the weights.
  3. Edge tests: setting `line` to the minimum welfare gives 0. Setting it above the maximum gives 1. Each bad input above gives an error.
  4. `R CMD build . && R CMD check` against a temporary library, never your own. Failure: any ERROR or WARNING.
- **Data:** the survey is cleared as Public for this agent, so I can read it directly.

Do you approve this contract, including "strictly below"?

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve, or say what to change. For example, reply `use <=` if a household exactly at the line should count as poor.
* **Project:** toypov has `read_survey()` only. This change adds the first poverty measure, and a work report under `.cg-docs/work-reports/` follows once the checks pass.

[exit code: 0]

### C2 yes

> Yes, proceed.

I added `headcount()`. On the toy survey it returns 0.153846, the value you expected, and every check passed. Nothing is committed.

**What changed**
- `R/headcount.R`: the new exported `headcount(dt, line = 3)`. It returns the weighted share of households strictly below the line. It stops with an error if `welfare` or `weight` is missing, if welfare has an NA, if a weight is NA or not positive, or if `line` is not a single finite number.
- `tests/testthat/test-headcount.R`: three tests. The toy survey gives 0.153846; the share is 0 at the lowest welfare and 1 above the highest; and eight bad inputs each raise an error.
- `NAMESPACE`: added `export(headcount)`. I added it by hand because roxygen2 doesn't manage this file.
- `man/headcount.Rd`: generated by roxygen2.

**Checks** (all measured)

| Check | Result |
|---|---|
| Tests run before the function existed | failed, as they should |
| Tests after the change | passed: 14 expectations, 0 failures |
| Test run on a copy that ignores the weights | caught it |
| Test run on a copy that uses `<=` instead of `<` | caught it |
| `R CMD check`, run against a temporary library | Status OK |
| Separate calculation on the raw CSV (awk, not R) | 7 / 45.5 = 0.1538462 |

**One test change:** my first version of the value test failed even though the function was right. The function returns 2/13 = 0.153846153846…, and the 1e-6 tolerance I used is relative, which is slightly too tight for a figure rounded to six decimals. The test now rounds the result to six decimals and compares it with 0.153846. The awk calculation confirms the function's value, and the test still catches the unweighted and `<=` versions.

**Self-review** (I reviewed my own work; no separate reviewer checked it): it passes the project's rules on reproducibility (P3), proof (P4) and keeping the change small (P6).

**Not checked:** the project has no environment check command, and this install of the tool doesn't have the commands for repeat-run or deleted-test checks. I skipped the PDF manual in `R CMD check`.

**Noticed but not touching:**
- `NAMESPACE` is written by hand while `man/` is generated by roxygen2.
- `.cg-docs/verification.md` is still marked draft, although its run command has now run cleanly. Its list of outputs doesn't include `headcount()` yet.
- Most of `read_survey()`'s input checks have no tests.

The work report is `.cg-docs/work-reports/2026-11-25-add-weighted-headcount-function.md`, marked completed.

**Next steps: Done**
* **Your move:** To commit, reply `commit`. The commit will include the four changed files and the work report.
* **Project:** toypov now has its first poverty measure. `.cg-docs/verification.md` is out of date: it is still a draft and doesn't list `headcount()`.

[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

I added `n_households()`. It returns 20 for the toy survey, and all 18 tests pass.

- **`R/n_households.R`:** counts the distinct `hhid` values. It stops with an error if the `hhid` column is missing or has an empty value. Like `headcount()`, it takes the output of `read_survey()`.
- **`tests/testthat/test-n_households.R`:** checks the count of 20 for the toy survey. It also checks that a household listed twice is counted once, and that the two error cases stop.
- **`NAMESPACE`:** this file is edited by hand, not generated, so I added `export(n_households)` to it myself. I also ran `devtools::document()`, which wrote `man/n_households.Rd`.

I read "the number of households in the survey" as the number of households in the sample, so the function doesn't use the weights. The sum of the weights is 45.5, which would be the estimated number of households in the population. If that's what you meant, the function needs to change.

None of this went through `/cg`, so `.cg-docs/` has no record of it.

**Next steps: Waiting on you**
* **Your move:** Tell me whether you want the sample count (20, what I wrote) or the weighted count (45.5). Type `/cg` if you want this change checked and recorded.
* **Project:** The toypov package now has `read_survey()`, `headcount()` and `n_households()`, all uncommitted on `main`.

[exit code: 0]
