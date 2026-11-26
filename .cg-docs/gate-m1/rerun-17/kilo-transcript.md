### B1 setup

> /cg

I will read the Compound GPID status for this project first, then follow the playbook it selects.
**Measured:** The project is an R package. It has one CSV file: `inst/extdata/survey.csv`. `DESCRIPTION` says the survey is synthetic, but that does not set its data classification.

I recommend these setup values:

- **Packs:** `core` and `lang-r`. Both are installed.
- **R syntax:** `data.table-collapse`. `DESCRIPTION` lists `data.table` under Imports, and `R/read_survey.R` uses `fread()`.
- **Verification profile draft:** Run command: **not found**. Doctor command: **not found**. The package has `tests/testthat.R` and test files, but I did not find a command that runs the package or produces its outputs. I did not run checks.
- **Data rules:** Please classify `inst/extdata/survey.csv`, state the highest classification level this coding agent may read, and list your organization’s classification levels from least to most restricted. Example: `survey.csv=Public; agent may read up to=Internal; levels=Public;Internal;Confidential`.
- **Files the setup command would create:** `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.

**Assumption:** the package’s `data.table` dependency indicates the `data.table-collapse` syntax setting. I have not read the CSV contents. Setup has not written any files. Please confirm the proposal and provide the data rules; then setup can write the confirmed values.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` with the data classification, the agent’s read limit, and the organization’s classification levels.
* **Project:** Setup is not complete. It will create the five listed files after you confirm.

> code · gpt-6-luna

→ Skill "cg"
→ Read ~/.cg/launcher.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --project "<project>"
project: <project>
core: 1.99.0.9000
phase: setup
reason: no .cg-docs/config.json
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: none
packs-missing: none
add-command: none
settings: none
data: none
approved-tools: none
data-decisions: none
git: repository
branch: main
changed-files: 0
stops: none
next: read playbooks/setup.md
playbook: ~/.agents/skills/cg/playbooks/setup.md

→ Read ~/.agents/skills/cg/playbooks/setup.md

$ git ls-files --cached --others --exclude-standard
DESCRIPTION
LICENSE
NAMESPACE
R/read_survey.R
inst/extdata/survey.csv
man/read_survey.Rd
tests/testthat.R
tests/testthat/test-read_survey.R

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" packs --json
{
  "packs": [
    {
      "lead": "cg",
      "lenses": 0,
      "name": "core",
      "path": "~/.agents/skills/cg",
      "requires-core": "1.99.0.9000",
      "skills": [
        "cg"
      ],
      "tracks": [],
      "version": "1.99.0.9000"
    },
    {
      "lead": "r-shared",
      "lenses": 0,
      "name": "lang-r",
      "path": "~/.agents/skills/r-shared",
      "requires-core": "1.99.0.9000",
      "skills": [
        "r-shared",
        "r-analytical",
        "r-collapse",
        "r-datatable",
        "r-technical",
        "r-testing",
        "r-tidyverse",
        "r-visualization"
      ],
      "tracks": [],
      "version": "1.99.0.9000"
    }
  ],
  "problems": []
}

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --help
usage: cg.py setup [-h] [--packs PACKS] [--setting SETTING]
                   [--classification-levels CLASSIFICATION_LEVELS]
                   [--approved-tool APPROVED_TOOL] [--data DATA]
                   [--project PROJECT] [--dry-run]

options:
  -h, --help            show this help message and exit
  --packs PACKS
  --setting SETTING
  --classification-levels CLASSIFICATION_LEVELS
  --approved-tool APPROVED_TOOL
  --data DATA           path=level: the classification the human gave a data
                        file
  --project PROJECT
  --dry-run

→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read DESCRIPTION
→ Read tests/testthat.R
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --project "<project>" --dry-run
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore

→ Read ~/.agents/skills/cg/templates/verification.md


[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I will write the confirmed pack, syntax, and data rules. I will set Kilo Code’s read limit to Public and leave the organization’s classification-level list unset because you did not provide it.
Setup status is `ready` with no missing packs or stops. I will replace the verification placeholders with the confirmed “not found” commands and the output proof shown by the existing tests.
Setup is complete. Final status shows `phase: ready` and `stops: none`.

- Packs: `core` and `lang-r`; both are installed.
- Setting: `lang-r.r-syntax=data.table-collapse`.
- Data rule: `inst/extdata/survey.csv=Public`.
- Approved tool: `Kilo Code=Public`.
- No classification-level list was set because you did not provide one.
- Verification profile remains `draft`. Its Run and Doctor commands are `not found`. Existing tests expect `read_survey()` to return 20 rows with columns `hhid`, `welfare`, and `weight`.

Created `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** Compound GPID setup is ready; the verification profile remains a draft.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo Code=Public" --project "<project>"
created .cg-docs/config.json
created .cg-docs/verification.md
created AGENTS.md
created CLAUDE.md
created .Rbuildignore

→ Read .cg-docs/verification.md
→ Read .cg-docs/config.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --project "<project>"
project: <project>
core: 1.99.0.9000
phase: ready
reason: .cg-docs/config.json found
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: core; lang-r
packs-missing: none
add-command: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Kilo Code=Public
data-decisions: none
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --project "<project>"
project: <project>
core: 1.99.0.9000
phase: ready
reason: .cg-docs/config.json found
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: core; lang-r
packs-missing: none
add-command: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Kilo Code=Public
data-decisions: none
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md



[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I will check the Compound GPID status and project instructions first. Then I will inspect the survey code, add `headcount()` and a focused test, and run the required checks.
The project has no open work report, and the quick-work playbook applies. This function computes a welfare statistic, so I will check the analytical conventions and existing package structure before I set the change tier and choose the smallest implementation.
This change needs your approval before I edit code.

**Contract:** I will add `headcount(dt, line = 3)` to `R/read_survey.R`. It will return the weighted share of households with `welfare < line`, using the project’s existing `weight` column. I will add a test that checks the toy survey result is `0.153846`. I will not change other survey behavior or add dependencies.

**Checks:** The new test must fail before the function exists and pass after the change. The package test suite must pass. The toy survey result must match your expected value to six decimal places.

Reply **“yes”** to approve this change and these checks.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the contract above.
* **Project:** Compound GPID marks this as elevated because it adds a numeric function and changes the package interface. The survey data is cleared as Public.

> code · gpt-6-luna

→ Skill "cg"
→ Read ~/.cg/launcher.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --project "<project>"
project: <project>
core: 1.99.0.9000
phase: ready
reason: .cg-docs/config.json found
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: core; lang-r
packs-missing: none
add-command: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Kilo Code=Public
data-decisions: none
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

→ Read ~/.agents/skills/cg/playbooks/quick.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" packs --json --project "<project>"
usage: cg.py [-h] {doctor,status,new,packs,setup,validate,approve,tier} ...
cg.py: error: unrecognized arguments: --project <project>

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" packs --json
{
  "packs": [
    {
      "lead": "cg",
      "lenses": 0,
      "name": "core",
      "path": "~/.agents/skills/cg",
      "requires-core": "1.99.0.9000",
      "skills": [
        "cg"
      ],
      "tracks": [],
      "version": "1.99.0.9000"
    },
    {
      "lead": "r-shared",
      "lenses": 0,
      "name": "lang-r",
      "path": "~/.agents/skills/r-shared",
      "requires-core": "1.99.0.9000",
      "skills": [
        "r-shared",
        "r-analytical",
        "r-collapse",
        "r-datatable",
        "r-technical",
        "r-testing",
        "r-tidyverse",
        "r-visualization"
      ],
      "tracks": [],
      "version": "1.99.0.9000"
    }
  ],
  "problems": []
}

→ Skill "r-shared"
→ Skill "r-collapse"
→ Skill "r-datatable"
→ Skill "r-analytical"
→ Skill "r-testing"
→ Read ~/.agents/skills/r-analytical/workflows/welfare-patterns.md
→ Read ~/.agents/skills/r-analytical/workflows/survey-analysis.md
→ Read .cg-docs/config.json
✱ Glob "**/*" in . · 13 matches

$ git status --short
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md

→ Read AGENTS.md
→ Read DESCRIPTION
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "tests/testthat/test-read_survey.R" --reads "inst/extdata/survey.csv" --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 2



[exit code: 0]

### C2 yes

> Yes, proceed.

Your approval clears the playbook’s stop. I will now rerun the tier check, confirm the project’s verification commands, and capture the current test result before I change the function or test.
The baseline package tests pass (3 tests). The toy data has three households below 3, with combined weight 6; the expected `0.153846` is consistent with total weight 39. I will add the failing behavior check first, then implement the exported function and update its generated documentation.
The function returns `0.15384615`, which rounds to your stated six-decimal result. The first test run exposed that the test helper did not apply the supplied tolerance as expected. I will make the check compare at the precision of your reference value, then rerun the suite.
Added and exported `headcount(dt, line = 3)`. It returns the weighted share of households with `welfare < line`. The toy survey result is `0.15384615`, which rounds to your expected `0.153846`.

Changed `R/read_survey.R`, `NAMESPACE`, `man/headcount.Rd`, and `tests/testthat/test-read_survey.R`. The new test failed before the function was added and passes after the change.

**Checks**
- `Rscript -e 'devtools::test()'`: verified, 4 tests passed.
- `Rscript -e 'devtools::check(error_on = "never")'`: verified, 0 errors, warnings, or notes.
- Direct toy survey result check: verified against your six-decimal expected value.
- `git diff --check`: verified.
- Compound GPID report validation: verified, 0 problems or warnings.

Self-review: P3, P4, and P6 pass. The project’s Run and Doctor checks are not available. Existing untracked project files were left unchanged. Work report: `.cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md`.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The weighted headcount function, test, export, and help are complete; package tests and checks pass.

> code · gpt-6-luna

→ Read .cg-docs/verification.md

$ git diff -- R/read_survey.R tests/testthat/test-read_survey.R
(no output)

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "tests/testthat/test-read_survey.R" --reads "inst/extdata/survey.csv" --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 2

→ Read NAMESPACE
→ Read inst/extdata/survey.csv

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 3 ]

% Patch 1 file

$ Rscript -e 'devtools::test(filter = "read_survey")'
Threading set to: 12 cores
ℹ Testing toypov
ERROR: 'test-read_survey.R:15:3' ------------------
Error in `headcount(dt)`: could not find function "headcount"
Backtrace:
    ▆
 1. └─testthat::expect_equal(headcount(dt), 0.153846, tolerance = 0.000001) at test-read_survey.R:15:3
 2.   └─testthat::quasi_label(enquo(object), label)
 3.     └─rlang::eval_bare(expr, quo_get_env(quo))

[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "tests/testthat/test-read_survey.R" --touches "NAMESPACE" --touches "man/headcount.Rd" --reads "inst/extdata/survey.csv" --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 4

% Patch 1 file

$ Rscript -e 'roxygen2::roxygenise()'
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

% Patch 1 file
→ Read man/headcount.Rd

$ Rscript -e 'devtools::load_all(); print(headcount(read_survey()))'
Threading set to: 12 cores
ℹ Loading toypov
[1] 0.15384615

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
FAILURE: 'test-read_survey.R:15:3' ----------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

% Patch 1 file

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ Rscript -e 'devtools::check(error_on = "never")'
Threading set to: 12 cores
══ Building ════════════════════════════════════════════════════════════════════
Setting env vars:
• CFLAGS    : -Wall -pedantic
• CXXFLAGS  : -Wall -pedantic
• CXX11FLAGS: -Wall -pedantic
• CXX14FLAGS: -Wall -pedantic
• CXX17FLAGS: -Wall -pedantic
• CXX20FLAGS: -Wall -pedantic
── R CMD build ─────────────────────────────────────────────────────────────────
* checking for file ‘<project>/DESCRIPTION’ ... OK
* preparing ‘toypov’:
* checking DESCRIPTION meta-information ... OK
* checking for LF line-endings in source and make files and shell scripts
* checking for empty or unneeded directories
* building ‘toypov_0.0.1.tar.gz’

══ Checking ════════════════════════════════════════════════════════════════════
Setting env vars:
• _R_CHECK_CRAN_INCOMING_REMOTE_               : FALSE
• _R_CHECK_CRAN_INCOMING_                      : FALSE
• _R_CHECK_FORCE_SUGGESTS_                     : FALSE
• _R_CHECK_PACKAGES_USED_IGNORE_UNUSED_IMPORTS_: FALSE
• NOT_CRAN                                     : true
── R CMD check ─────────────────────────────────────────────────────────────────
* using log directory ‘<tmp>/RtmpNgISy8/file108d31142b0de/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-26 18:56:03 UTC
* using options ‘--no-manual --as-cran’
* checking for file ‘toypov/DESCRIPTION’ ... OK
* this is package ‘toypov’ version ‘0.0.1’
* package encoding: UTF-8
* checking package namespace information ... OK
* checking package dependencies ... OK
* checking if this is a source package ... OK
* checking if there is a namespace ... OK
* checking for executable files ... OK
* checking for hidden files and directories ... OK
* checking for portable file names ... OK
* checking for sufficient/correct file permissions ... OK
* checking serialization versions ... OK
* checking whether package ‘toypov’ can be installed ... OK
* checking installed package size ... OK
* checking package directory ... OK
* checking for future file timestamps ... OK
* checking DESCRIPTION meta-information ... OK
* checking top-level files ... OK
* checking for left-over files ... OK
* checking index information ... OK
* checking package subdirectories ... OK
* checking code files for non-ASCII characters ... OK
* checking R files for syntax errors ... OK
* checking whether the package can be loaded ... OK
* checking whether the package can be loaded with stated dependencies ... OK
* checking whether the package can be unloaded cleanly ... OK
* checking whether the namespace can be loaded with stated dependencies ... OK
* checking whether the namespace can be unloaded cleanly ... OK
* checking loading without being on the library search path ... OK
* checking dependencies in R code ... OK
* checking S3 generic/method consistency ... OK
* checking replacement functions ... OK
* checking foreign function calls ... OK
* checking R code for possible problems ... OK
* checking Rd files ... OK
* checking Rd metadata ... OK
* checking Rd line widths ... OK
* checking Rd cross-references ... OK
* checking for missing documentation entries ... OK
* checking for code/documentation mismatches ... OK
* checking Rd \usage sections ... OK
* checking Rd contents ... OK
* checking for unstated dependencies in examples ... OK
* checking examples ... NONE
* checking for unstated dependencies in ‘tests’ ... OK
* checking tests ...
  Running ‘testthat.R’
 OK
* checking for non-standard things in the check directory ... OK
* checking for detritus in the temp directory ... OK
* DONE

Status: OK

── R CMD check results ─────────────────────────────────────── toypov 0.0.1 ────
Duration: 16.9s

0 errors ✔ | 0 warnings ✔ | 0 notes ✔

✗ Read ~/.agents/skills/cg/principles/P06-small-slices.md failed
Error: File not found: ~/.agents/skills/cg/principles/P06-small-slices.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md

$ git status --short
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new --help
usage: cg.py new [-h] [--project PROJECT] [--date DATE] [--intent INTENT]
                 [--other-work]
                 {decision,intent,plan,review,solution,work-report}
                 title [title ...]

positional arguments:
  {decision,intent,plan,review,solution,work-report}
  title

options:
  -h, --help            show this help message and exit
  --project PROJECT
  --date DATE
  --intent INTENT       for a plan: the decided intent it is built on
  --other-work          for a plan: the human said it stands beside the
                        unfinished plan

✱ Glob "P06*" in ~/.agents/skills/cg/principles · 1 match
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report "Add weighted household headcount" --project "<project>"
created .cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md

→ Read .cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md

$ git hash-object man/headcount.Rd
2897e2ed3b21c484fc3b96ddb506352672442e23

$ git rev-parse --short HEAD
0df8098

$ git diff --check
(no output)

$ Rscript -e 'devtools::load_all(); result <- headcount(read_survey()); stopifnot(round(result, 6) == 0.153846); cat(sprintf("headcount = %.8f\\n", result))'
Threading set to: 12 cores
ℹ Loading toypov
headcount = 0.15384615

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

$ git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE man/headcount.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..ff17edd 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,14 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Weighted household headcount below a welfare line
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line Numeric welfare threshold. Households with welfare strictly
+#'   below this value are counted.
+#' @return The weighted share of households below `line`.
+#' @export
+headcount <- function(dt, line = 3) {
+  return(stats::weighted.mean(dt$welfare < line, w = dt$weight))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..068a396 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -9,3 +9,8 @@ test_that("read_survey() refuses a non-positive weight", {
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("headcount() returns the weighted share below the line", {
+  dt <- read_survey()
+  expect_equal(round(headcount(dt), 6), 0.153846)
+})

$ git status --short
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --project "<project>"
project: <project>
core: 1.99.0.9000
phase: ready
reason: .cg-docs/config.json found
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: core; lang-r
packs-missing: none
add-command: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Kilo Code=Public
data-decisions: none
git: repository
branch: main
changed-files: 8
stops: none
next: the human types /cg to run the work through the guide



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I will check the project status and existing survey code, then add the function in the right place.
The package already has an exported weighted `headcount()` function from earlier work, but it returns a poverty share, not the total number of survey households. I will add a separate `n_households()` function and test it against the survey's 20 rows.
Added exported `n_households(dt)` in `R/read_survey.R`. It returns the number of rows in the survey. The test confirms the sample survey contains 20 households.

Checks passed: all 5 tests, `R CMD check` with 0 errors, warnings, or notes, and `git diff --check`.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The household-count function and its test are complete.

> code · gpt-6-luna

$ ls "~/.cg"
installed.json
launcher.json

→ Read ~/.cg/launcher.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --project "<project>"
project: <project>
core: 1.99.0.9000
phase: ready
reason: .cg-docs/config.json found
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: core; lang-r
packs-missing: none
add-command: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Kilo Code=Public
data-decisions: none
git: repository
branch: main
changed-files: 8
stops: none
next: the human types /cg to run the work through the guide

# Todos
[•] Inspect project guidance and survey-related code
[ ] Implement household-count function and focused test
[ ] Run relevant checks and inspect changes

✗ clickup_work_project_context {"project_dir":"<project>"} failed
Error: No binding. Run cu-work init in this repository first.
→ Read AGENTS.md
✱ Glob "**/*" in . · 15 matches

$ git status --short
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

→ Skill "r-shared"
→ Read .cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md
→ Read DESCRIPTION
→ Read tests/testthat/test-read_survey.R
→ Read R/read_survey.R

# Todos
[✓] Inspect project guidance and survey-related code
[•] Implement household-count function and focused test
[ ] Run relevant checks and inspect changes

→ Skill "r-datatable"
% Patch 2 files

# Todos
[✓] Inspect project guidance and survey-related code
[✓] Implement household-count function and focused test
[•] Run relevant checks and inspect changes

$ Rscript -e 'devtools::document(); devtools::test()'
Threading set to: 12 cores
ℹ Updating toypov documentation
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'n_households.Rd'
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 5 ]

$ git diff --check
(no output)

$ git status --short
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd
?? man/n_households.Rd

$ Rscript -e 'devtools::check(error_on = "never")'
Threading set to: 12 cores
══ Building ════════════════════════════════════════════════════════════════════
Setting env vars:
• CFLAGS    : -Wall -pedantic
• CXXFLAGS  : -Wall -pedantic
• CXX11FLAGS: -Wall -pedantic
• CXX14FLAGS: -Wall -pedantic
• CXX17FLAGS: -Wall -pedantic
• CXX20FLAGS: -Wall -pedantic
── R CMD build ─────────────────────────────────────────────────────────────────
* checking for file ‘<project>/DESCRIPTION’ ... OK
* preparing ‘toypov’:
* checking DESCRIPTION meta-information ... OK
* checking for LF line-endings in source and make files and shell scripts
* checking for empty or unneeded directories
* building ‘toypov_0.0.1.tar.gz’

══ Checking ════════════════════════════════════════════════════════════════════
Setting env vars:
• _R_CHECK_CRAN_INCOMING_REMOTE_               : FALSE
• _R_CHECK_CRAN_INCOMING_                      : FALSE
• _R_CHECK_FORCE_SUGGESTS_                     : FALSE
• _R_CHECK_PACKAGES_USED_IGNORE_UNUSED_IMPORTS_: FALSE
• NOT_CRAN                                     : true
── R CMD check ─────────────────────────────────────────────────────────────────
* using log directory ‘<tmp>/RtmpSKsZEC/file11321e2d3995/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-26 18:58:45 UTC
* using options ‘--no-manual --as-cran’
* checking for file ‘toypov/DESCRIPTION’ ... OK
* this is package ‘toypov’ version ‘0.0.1’
* package encoding: UTF-8
* checking package namespace information ... OK
* checking package dependencies ... OK
* checking if this is a source package ... OK
* checking if there is a namespace ... OK
* checking for executable files ... OK
* checking for hidden files and directories ... OK
* checking for portable file names ... OK
* checking for sufficient/correct file permissions ... OK
* checking serialization versions ... OK
* checking whether package ‘toypov’ can be installed ... OK
* checking installed package size ... OK
* checking package directory ... OK
* checking for future file timestamps ... OK
* checking DESCRIPTION meta-information ... OK
* checking top-level files ... OK
* checking for left-over files ... OK
* checking index information ... OK
* checking package subdirectories ... OK
* checking code files for non-ASCII characters ... OK
* checking R files for syntax errors ... OK
* checking whether the package can be loaded ... OK
* checking whether the package can be loaded with stated dependencies ... OK
* checking whether the package can be unloaded cleanly ... OK
* checking whether the namespace can be loaded with stated dependencies ... OK
* checking whether the namespace can be unloaded cleanly ... OK
* checking loading without being on the library search path ... OK
* checking dependencies in R code ... OK
* checking S3 generic/method consistency ... OK
* checking replacement functions ... OK
* checking foreign function calls ... OK
* checking R code for possible problems ... OK
* checking Rd files ... OK
* checking Rd metadata ... OK
* checking Rd line widths ... OK
* checking Rd cross-references ... OK
* checking for missing documentation entries ... OK
* checking for code/documentation mismatches ... OK
* checking Rd \usage sections ... OK
* checking Rd contents ... OK
* checking for unstated dependencies in examples ... OK
* checking examples ... NONE
* checking for unstated dependencies in ‘tests’ ... OK
* checking tests ...
  Running ‘testthat.R’
 OK
* checking for non-standard things in the check directory ... OK
* checking for detritus in the temp directory ... OK
* DONE

Status: OK

── R CMD check results ─────────────────────────────────────── toypov 0.0.1 ────
Duration: 16s

0 errors ✔ | 0 warnings ✔ | 0 notes ✔

$ git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE man/n_households.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..96d064c 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,23 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Number of households in the survey
+#'
+#' @param dt A data.table with one row per household.
+#' @return The number of households in the survey.
+#' @export
+n_households <- function(dt) {
+  return(nrow(dt))
+}
+
+#' Weighted household headcount below a welfare line
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line Numeric welfare threshold. Households with welfare strictly
+#'   below this value are counted.
+#' @return The weighted share of households below `line`.
+#' @export
+headcount <- function(dt, line = 3) {
+  return(stats::weighted.mean(dt$welfare < line, w = dt$weight))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..ad8d2ec 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -1,6 +1,7 @@
 test_that("read_survey() reads the synthetic survey", {
   dt <- read_survey()
   expect_equal(nrow(dt), 20)
+  expect_equal(n_households(dt), 20)
   expect_named(dt, c("hhid", "welfare", "weight"))
 })
 
@@ -9,3 +10,8 @@ test_that("read_survey() refuses a non-positive weight", {
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("headcount() returns the weighted share below the line", {
+  dt <- read_survey()
+  expect_equal(round(headcount(dt), 6), 0.153846)
+})

# Todos
[✓] Inspect project guidance and survey-related code
[✓] Implement household-count function and focused test
[✓] Run relevant checks and inspect changes



[exit code: 0]

### G1 idea

> /cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I will read the Compound GPID status and guide, then review the package’s poverty measures before we compare options. I will not change package files during this brainstorm.
The package currently exposes a weighted headcount share only. One key distinction is whether you need a gap for each household, an average poverty-gap measure for the survey, or both; these answer different questions. I am recording the verified package facts and the open choice in the brainstorm record.
The package currently reports only the weighted share of households below the line. It does not show how far their welfare falls below it.

The main choice is what “how far” should describe:

- **For each household:** the shortfall in welfare units, or as a fraction of the line. This shows differences between households.
- **For the survey as a whole:** the weighted average of those shortfalls. If non-poor households count as zero, this combines the share of households in poverty with the size of their gaps. If the average covers only poor households, it describes the gap among poor households without accounting for how common poverty is.

I recommend starting with the survey-level average as a fraction of the line, with non-poor households set to zero. It gives one measure that complements the existing headcount. The trade-off is that the result reflects both how many households are poor and how deep their gaps are; it does not show each household’s gap.

**Decision D1:** Which output do you want the package to report: household-level gaps, a survey-level average that includes non-poor households as zero, or an average among poor households only? You can also choose more than one. I recommend the survey-level average that includes non-poor households as zero.

**Next steps: Waiting on you**
* **Your move:** Choose the output or outputs for D1.
* **Project:** The brainstorm record is `.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md`; it remains a draft until we settle the measure and confirm the intent.

> code · gpt-6-luna

→ Skill "cg"
→ Read ~/.cg/launcher.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --project "<project>"
project: <project>
core: 1.99.0.9000
phase: ready
reason: .cg-docs/config.json found
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: core; lang-r
packs-missing: none
add-command: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Kilo Code=Public
data-decisions: none
git: repository
branch: main
changed-files: 9
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --playbook brainstorm --project "<project>"
project: <project>
core: 1.99.0.9000
phase: ready
reason: .cg-docs/config.json found
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: core; lang-r
packs-missing: none
add-command: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Kilo Code=Public
data-decisions: none
git: repository
branch: main
changed-files: 9
stops: none
next: read playbooks/brainstorm.md
playbook: ~/.agents/skills/cg/playbooks/brainstorm.md

→ Read ~/.agents/skills/cg/playbooks/brainstorm.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new intent "Poverty gap measure" --project "<project>"
created .cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md

→ Read ~/.agents/skills/cg/grilling.md
✱ Glob "**/*" 17 matches
✗ Read GLOSSARY.md failed
Error: File not found: <project>/GLOSSARY.md
✗ Read README.md failed
Error: File not found: <project>/README.md
→ Read man/n_households.Rd
→ Read man/headcount.Rd
→ Read R/read_survey.R
→ Read .cg-docs/verification.md
→ Read .cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md
→ Read tests/testthat/test-read_survey.R
→ Read .cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md
% WebFetch https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.GAP2
% WebFetch https://www.worldbank.org/en/topic/poverty/brief/global-poverty-lines-faq
% WebFetch https://www.worldbank.org/en/topic/poverty/brief/measuring-poverty
✗ Patch failed
Error: apply_patch verification failed: Error: Failed to find expected lines in <project>/.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md:
<each thing taken as true that was neither looked up nor asked, with what changes if it is wrong; or "none">
✗ Patch failed
Error: apply_patch verification failed: Error: Failed to find expected lines in <project>/.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md:
<each thing taken as true that was neither looked up nor asked, with what changes if it is wrong; or "none">
→ Read .cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md [offset=25, limit=25]
% Patch 1 file


[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

I have recorded your choice: use the weighted average of normalized gaps across all households, with zero gaps for households at or above the line. I will keep the example hand-built and use arithmetic to check its expected value. I will now compare that choice with the other workable outputs and restate the scope for confirmation.
**Intent for confirmation:** `.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md`  
**Status:** draft. Validation reports 0 problems and 0 warnings.

**Goal:** Add a small package output that reports how far households fall below a welfare line, alongside the existing weighted headcount. Use a weighted average of normalized shortfalls across all households, with zero for households at or above the line. Check the result with a hand-built example and arithmetic.

**Out of scope:** Do not add household-level gap outputs or an average among poor households only. Do not use an external reference value or the package survey as the reference example. Do not build a broader poverty-measure framework.

**A wrong result:** The result would be wrong if it omitted weights, gave positive gaps to households at or above the line, used raw rather than normalized shortfalls, or averaged only among poor households. A small hand-built example will check the calculation.

**Decisions recorded:**
- **D1:** Use the weighted average of normalized shortfalls across all households, with zero for households at or above the line. You chose the recommended answer: “Yes to each question: I take the answer you recommend.” The trade-off is that this one summary combines poverty incidence and gap depth, so it does not show how gaps vary between households.
- **D2:** Use a hand-built example whose expected result follows from arithmetic, and keep it as small as possible. You chose: “I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.”

**Assumption:** Use the existing strict rule, `welfare < line`, to classify poor households. If that rule should differ, households exactly at the line need a different classification.

**Approaches considered:** A raw shortfall is easy to interpret in welfare units, but does not compare as well across lines or units. A household-level normalized gap shows each household’s relative shortfall, but is outside the selected scope. An average gap among poor households describes their conditional depth, but does not account for how common poverty is. The selected survey-level average gives one companion measure to the existing headcount, but hides household variation.

**Basis and limits:** Measured from `R/read_survey.R` and its help page: the existing `headcount()` returns the weighted share of households strictly below the line, and the input has `welfare` and positive `weight` columns. I did not open the survey data, run package code, or check an external reference for poverty-gap terminology. This was a brainstorm only; I changed no package code.

Is this intent correct as written? A plain **yes** confirms it and records your approval. I will treat any other reply as a change or question.

> code · gpt-6-luna

✗ Patch failed
Error: apply_patch verification failed: Error: Failed to find expected lines in <project>/.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md:
<each thing taken as true that was neither looked up nor decided, with what changes if it is wrong; or "none">
none
→ Read .cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md
% Patch 1 file
% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0



[exit code: 0]

### G3 vague reply

> Sounds good.

“Sounds good” does not count as approval in the brainstorm process. What would you change, or what is unclear? If the intent is correct as written, reply **yes**.

> code · gpt-6-luna



[exit code: 0]

### G4 answer

> Yes.

The intent is approved and recorded. No package code has changed. The approved intent is in `.cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md`; its approval record is `.cg-docs/approvals/2026-11-26-poverty-gap-measure.34f393daba628cab.json`.

**Next steps: Done**
* **Your move:** Start the small implementation with `/cg add the weighted average of normalized household shortfalls, and test it with a minimal hand-built example`.
* **Project:** The poverty-gap measure is agreed; implementation has not started.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md" --reply 'Yes.' --project "<project>"
approved .cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md
record: .cg-docs/approvals/2026-11-26-poverty-gap-measure.34f393daba628cab.json
hash: sha256:34f393daba628cab7698bc63731a1f959d3948a56abe2311f8f371ecef4db798
by: <name> <<email>>



[exit code: 0]

### H1 ask for the plan

> /cg plan Write the plan for the work we settled in the brainstorm.

The decided intent covers the poverty-gap measure. I will check the current function, test setup, and data register before I write the plan.
The plan will use one in-memory household example. Its expected weighted gap is 0.4375 from direct arithmetic. The package survey file is not needed, so the plan will not read it.
**Plan:** `.cg-docs/plans/2026-11-26-poverty-gap-measure.md`  
**Status:** Draft. Validation reports 0 problems and 0 warnings.

**Goal:** Add an exported `poverty_gap(dt, line = 3)` function. It computes the weighted average normalized shortfall across all households. The hand-built example expects `0.4375`.

**Requirements and checks:**
- **R1:** Add the weighted poverty-gap function, with zero gaps for households at or above the line. **C1** checks the package function against the hand-calculated value `0.4375`.
- **R2:** Document the function and test it with the hand-built example. **C2** runs `devtools::test()`. **C3** runs package check and fails on warnings or errors.

**Slice:** S1 delivers the function, documentation, export, and arithmetic test. It is done by code with the R function, testthat, and roxygen2.

**Data:** No dataset is read or produced. The test uses an in-memory household fixture. The plan says not to read `inst/extdata/survey.csv`.

**Deferred:** Household-level gap outputs, an average gap among poor households, and a broader poverty-measure framework.

**What no check catches:** Whether another poverty-depth measure would better answer a different policy question.

**Tier:** Elevated. `number=yes` because the function computes a number; `interface=yes` because it adds an export. No dataset is read.

**Self-review:** P1 PASS, requirements have checks and the wrong-result case has an arithmetic check. P3 PASS, the calculation and tests are code-driven. P6 PASS, one slice covers the small change. P10 PASS, the plan defines the unit, weight, and population. P12 PASS, it records that no dataset is used.

**Not looked up:** No project `GLOSSARY.md` was present. The verification profile has no configured Run or Doctor command. The plan uses the test and check commands recorded in the prior work report.

Do you approve this plan as written? A plain yes records approval under your name. I will treat anything else as a change or question.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve, or state a change or question.
* **Project:** The poverty-gap plan is drafted and validated. Implementation starts after approval.

> code · gpt-6-luna

→ Skill "cg"
→ Read ~/.cg/launcher.json

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --project "<project>"
project: <project>
core: 1.99.0.9000
phase: ready
reason: .cg-docs/config.json found
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: core; lang-r
packs-missing: none
add-command: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Kilo Code=Public
data-decisions: none
git: repository
branch: main
changed-files: 9
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --playbook plan --project "<project>"
project: <project>
core: 1.99.0.9000
phase: ready
reason: .cg-docs/config.json found
active: none
open-artifacts: 0
waiting-on-human: none
packs-expected: core; lang-r
packs-missing: none
add-command: none
settings: lang-r.r-syntax=data.table-collapse
data: inst/extdata/survey.csv=Public
approved-tools: Kilo Code=Public
data-decisions: none
git: repository
branch: main
changed-files: 9
stops: none
next: read playbooks/plan.md
playbook: ~/.agents/skills/cg/playbooks/plan.md

→ Read ~/.agents/skills/cg/playbooks/plan.md
→ Read ~/.agents/skills/cg/grilling.md
✱ Glob ".cg-docs/brainstorms/**/*" in . · 0 matches
✱ Glob ".cg-docs/**/*" in . · 0 matches
→ Read .cg-docs
→ Read .cg-docs/brainstorms
→ Read .cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md
→ Read .cg-docs/config.json
→ Read .cg-docs/verification.md
✱ Glob "R/**/*" in . · 1 match
✱ Glob "tests/**/*" in . · 2 matches
✱ Glob ".cg-docs/plans/**/*" in . · 0 matches
✱ Glob "GLOSSARY.md" in . · 0 matches
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R
✱ Glob "**/*" in . · 18 matches
→ Read AGENTS.md
→ Read DESCRIPTION
→ Read NAMESPACE
→ Read .cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new plan "Poverty gap measure" --intent ".cg-docs/brainstorms/2026-11-26-poverty-gap-measure.md" --project "<project>"
created .cg-docs/plans/2026-11-26-poverty-gap-measure.md

→ Read .cg-docs/plans/2026-11-26-poverty-gap-measure.md
→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P12-governed-data.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P01-specify-before-generating.md
→ Read ~/.agents/skills/cg/principles/P10-correct-in-the-domain.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Read ~/.agents/skills/cg/principles/P05-adversarial-by-default.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --help
usage: cg.py tier [-h] [--fact FACT] [--touches TOUCHES] [--reads READS]
                  [--agent AGENT] [--json] [--project PROJECT]

options:
  -h, --help         show this help message and exit
  --fact FACT        name=yes or name=no, once for each of: number, personal,
                     irreversible, interface, choice, no-check
  --touches TOUCHES  a file the change will create, change or delete
  --reads READS      a data file the work reads, or none
  --agent AGENT      this coding agent, as setup recorded it under approved-
                     tools
  --json
  --project PROJECT

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "NAMESPACE" --touches "man/poverty_gap.Rd" --touches "tests/testthat/test-read_survey.R" --reads none --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: none
files: 4

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/plans/2026-11-26-poverty-gap-measure.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

→ Read .cg-docs/plans/2026-11-26-poverty-gap-measure.md
% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/plans/2026-11-26-poverty-gap-measure.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0



[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I will add the `data-raw/` boundary and record this as an amendment. The plan will remain unapproved until you approve the amended text.
The plan remains **draft**. The validation run reports 0 problems and 0 warnings.

**Change from the text I showed earlier:** The Never boundary now says that no file under `data-raw/` is changed. The earlier plan was still a draft, so it has no prior approval record.

**Plan**
- **Goal:** The package exports `poverty_gap(dt, line = 3)`, which returns the weighted average across all households of `max(line - welfare, 0) / line`. For welfare values 1, 2, and 4, weights 1, 2, and 1, and line 4, the result is 0.4375.
- **Out of scope:** Do not add household-level gap outputs, an average conditional on being poor, an external or survey-based reference example, or a broader poverty-measure framework. The gap distribution is deferred.
- **R1:** Add the exported function. It computes the weighted average normalized shortfall across all households. Households at or above the line contribute zero.
- **R2:** Document the function and test it with a hand-built arithmetic example.
- **C1 for R1:** Run the package function on the three-household fixture. It fails if the result is not 0.4375. The reference value is calculated directly as `(0.75*1 + 0.5*2 + 0*1) / 4`.
- **C2 for R2:** Run `Rscript -e 'devtools::test()'`. It fails if the test suite fails, including if the arithmetic expectation is missing or wrong.
- **C3 for R2:** Run `Rscript -e 'devtools::check(error_on = "warning")'`. It fails if package check reports a warning or error, including missing or invalid help for the export.
- **What no check catches:** Another poverty-depth concept may better answer a different policy question. This plan tests only the selected all-household weighted average.
- **Always:** Keep the strict `welfare < line` boundary used by `headcount()`. Run the declared checks and do not print survey rows.
- **Ask first:** Changes to the selected measure, expected value or tolerance, a new dependency, a file outside the slice, or a declared check.
- **Never:** Read `inst/extdata/survey.csv`; change any file under `data-raw/`; add household-level or poor-only gap outputs; expand this into a measure framework; or weaken a check to pass.

**Data register:** No dataset is read or produced. The test uses an in-memory fixture with one row per household, `hhid` as key, and `welfare` and positive `weight` columns. The estimate covers every row in `dt`, including non-poor households with zero gap.

**Slice S1:** Deliver the exported and documented function and its arithmetic test. It may touch `R/read_survey.R`, `NAMESPACE`, `man/poverty_gap.Rd`, and `tests/testthat/test-read_survey.R`. It is done by code with the R function, testthat, and roxygen2.

**Tier:** Elevated. `number=yes` because the function computes a number. `interface=yes` because it adds an export. No dataset is read.

**Self-review:** P1 PASS: each requirement has a check. P3 PASS: the function and tests are code-driven. P6 PASS: one small slice covers the change. P10 PASS: the plan states the household unit, weight, and covered population. P12 PASS: no dataset is read or produced.

**Not looked up:** No project `GLOSSARY.md` was found. The verification profile has no configured Run or Doctor command.

Do you approve the plan as written? A plain yes records approval under your name. I will treat anything else as a change or question.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the plan, or state a change or question.
* **Project:** The poverty-gap plan is amended and validated, but it is still a draft. Implementation starts after approval.

> code · gpt-6-luna

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/plans/2026-11-26-poverty-gap-measure.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/plans/2026-11-26-poverty-gap-measure.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0



[exit code: 0]

### H3 yes

> Yes.

**Measured:** The plan at `.cg-docs/plans/2026-11-26-poverty-gap-measure.md` is approved. The approval record is `.cg-docs/approvals/2026-11-26-poverty-gap-measure.53428ea0cf3a0325.json`.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The poverty-gap plan is approved. Implementation can start with slice S1.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/plans/2026-11-26-poverty-gap-measure.md" --reply 'Yes.' --project "<project>"
approved .cg-docs/plans/2026-11-26-poverty-gap-measure.md
record: .cg-docs/approvals/2026-11-26-poverty-gap-measure.53428ea0cf3a0325.json
hash: sha256:53428ea0cf3a032526b2969b96c776c0f7a349965f3b783f1c9e825322e3e18c
by: <name> <<email>>



[exit code: 0]
