### B1 setup

> /cg

**Recommended setup:** use the `core` and `lang-r` packs. Both are installed.

- **Pack setting:** `lang-r.r-syntax=data.table-collapse`. The package imports `data.table` in `DESCRIPTION` and uses `fread()` in `R/read_survey.R`. This matches the installed `lang-r` default.
- **Verification profile draft:** Run command: not found. Doctor command: not found. The package exposes `read_survey()`, which returns a `data.table` with one row per household (`R/read_survey.R`). The existing check expects 20 rows and the columns `hhid`, `welfare`, and `weight` (`tests/testthat/test-read_survey.R`). No project command or independent reference value is defined.
- **Data rules:** The project contains one data file: `inst/extdata/survey.csv`. Its classification is not recorded. Please give its classification, the highest classification this coding agent may read, and your organization’s classification levels from public to most restricted. Example: `survey.csv=Public; agent=Public; levels=Public;Internal;Restricted`. If you do not know an item, say `unknown`; it will remain open.
- **Assumptions:** I recommend `data.table-collapse` because the package uses `data.table`. I did not inspect the data file. The run and doctor commands remain unset because I found no project-defined commands.
- **Files the setup command would create:** `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.

Reply `yes` with the data-rule values to approve this setup. A correction is not approval.

**Next steps: Waiting on you**
* **Your move:** Reply `yes; survey.csv=<classification>; agent=<highest allowed level>; levels=<Public;...>` or provide corrections.
* **Project:** Setup is not written. I will write it only after your approval and data-rule answer.

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

→ Read DESCRIPTION
→ Read tests/testthat.R
→ Read R/read_survey.R
→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read tests/testthat/test-read_survey.R

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --help
usage: cg.py setup [-h] [--packs PACKS] [--setting SETTING]
                   [--classification-levels CLASSIFICATION_LEVELS]
                   [--approved-tool APPROVED_TOOL] [--contact CONTACT]
                   [--data DATA] [--project PROJECT] [--dry-run]

options:
  -h, --help            show this help message and exit
  --packs PACKS
  --setting SETTING
  --classification-levels CLASSIFICATION_LEVELS
  --approved-tool APPROVED_TOOL
  --contact CONTACT
  --data DATA           path=level: the classification the human gave a data
                        file
  --project PROJECT
  --dry-run

→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/templates/verification.md
→ Read inst/extdata/survey.csv [limit=1]

$ git ls-files --cached --others --exclude-standard | awk 'BEGIN { FS="." } { ext=(NF > 1 ? "." $NF : "[no extension]"); count[ext]++ } END { for (ext in count) print ext, count[ext] }'
.csv 1
.R 3
[no extension] 3
.Rd 1

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --project "<project>" --dry-run
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore

→ Read ~/.agents/skills/cg/GLOSSARY.md
→ Read ~/.agents/skills/cg/principles/P12-governed-data.md
→ Read NAMESPACE
→ Read man/read_survey.Rd


[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

The approval sets `survey.csv` to Public and allows Kilo Code to read Public data. I will record Public as the stated classification level and create only the files shown in the dry run.
Setup is complete. The human classified `inst/extdata/survey.csv` as Public and approved Kilo Code to read Public data. The project uses `data.table-collapse`.

The setup created `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. Status reports `phase: ready`, `stops: none`, `settings: lang-r.r-syntax=data.table-collapse`, and `data: inst/extdata/survey.csv=Public`. No packs are missing.

The verification profile is still a draft. I did not run the package check.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** Compound GPID setup is ready. The guide selects `playbooks/quick.md` for the next piece of work.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo Code=Public" --classification-levels "Public" --project "<project>"
created .cg-docs/config.json
created .cg-docs/verification.md
created AGENTS.md
created CLAUDE.md
created .Rbuildignore

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
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md



[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

`/cg` would run this change with checks and a record. I will first read the Compound GPID setup and project status, then check the package conventions before I add the function and test.
`/cg` would run this change with checks and a record.

The smallest change is to add and export `headcount(dt, line = 3)` and test that the toy survey returns `0.153846`. I will leave the survey data and other measures unchanged.

**Risk gate**
- **Yes, line 1:** the function computes a statistic. The playbook requires a hard stop before this change.
- **No, line 2:** status classifies `inst/extdata/survey.csv` as `Public`.
- **No, lines 3–7:** this change does not touch personal data, credentials, irreversible actions, existing dependencies or formats. It needs two files, and a test can fail if the result is wrong.

**Contract**
- Goal: implement and export the weighted household share below the poverty line, then test the expected value.
- Out of scope: changes to the survey data, other statistics, or dependencies.
- Checks: run the focused test and package checks. Failure means the expected value does not match `0.153846`, or a package check fails.

No files have changed. The playbook requires a clear yes before I proceed with a statistic. Reply `yes` to approve this contract.

**Next steps: Waiting on you**
* **Your move:** reply `yes` to approve the contract.
* **Project:** the function and test are not yet implemented; the approval gate is open.

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
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

→ Read ~/.agents/skills/cg/playbooks/quick.md

# Todos
[•] Inspect package source and test conventions for the requested change
[ ] Confirm the risk gate and proceed only after required approval

✱ Glob "R/**/*.R" 1 match
✱ Glob "tests/**/*.R" 2 matches
✱ Glob "DESCRIPTION" 1 match
✱ Glob "NAMESPACE" 1 match
→ Read NAMESPACE
→ Read DESCRIPTION
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R


[exit code: 0]

### C2 yes

> Yes, proceed.

Approval is clear. I will add the exported function and a focused test in the existing source and test files, then run the package checks and record the evidence.
The new test fails because `headcount()` does not exist yet. I will add the function beside `read_survey()` and use the survey’s household-level welfare and positive weights to compute the weighted share below the line.
The first post-change test showed the exact share is `0.1538462`; the requested expectation is rounded to six decimal places. I updated the test to compare at that stated precision. The package check also failed on this test, so I will rerun both checks with the corrected assertion.
Added and exported `headcount(dt, line = 3)`. It returns the weighted share of households with welfare below `line`. The toy survey result is `0.1538461538`, which rounds to the expected `0.153846`.

- Added a test in `tests/testthat/test-read_survey.R`.
- Added function documentation in `man/headcount.Rd`.
- `devtools::test()` passed.
- `devtools::check(document = FALSE, error_on = "warning")` passed with 0 errors, warnings, or notes.
- Recorded the work in `.cg-docs/work-reports/2026-11-25-add-weighted-headcount.md`.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The weighted headcount function and test are implemented, and the package checks pass.

> code · gpt-6-luna

# Todos
[✓] Inspect package source and test conventions for the requested change
[•] Implement and test weighted headcount
[ ] Record checks and self-review in a Compound GPID work report

→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
✗ Read ~/.agents/skills/cg/principles/P06-small-changes.md failed
Error: File not found: ~/.agents/skills/cg/principles/P06-small-changes.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md

$ git status --short
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" --help
usage: cg.py [-h] {doctor,status,new,packs,setup} ...

Compound GPID core tooling.

positional arguments:
  {doctor,status,new,packs,setup}
    doctor              check this machine and write the launcher file
    status              print the state of the work in a project
    new                 create an artifact under .cg-docs/
    packs               list the installed packs
    setup               write what the human confirmed in the setup playbook

options:
  -h, --help            show this help message and exit

→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
% Patch 1 file

$ Rscript -e 'devtools::test(filter = "read_survey")'
Threading set to: 12 cores
ℹ Testing toypov
ERROR: 'test-read_survey.R:14:3' ------------------
Error in `headcount(read_survey())`: could not find function "headcount"
Backtrace:
    ▆
 1. └─testthat::expect_equal(headcount(read_survey()), 0.153846, tolerance = 0.000001) at test-read_survey.R:14:3
 2.   └─testthat::quasi_label(enquo(object), label)
 3.     └─rlang::eval_bare(expr, quo_get_env(quo))

[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

% Patch 1 file

$ Rscript -e 'roxygen2::roxygenise()'
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

✱ Glob "man/*.Rd" 2 matches
→ Read man/headcount.Rd
% Patch 1 file

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
FAILURE: 'test-read_survey.R:14:3' ----------------
Expected `headcount(read_survey())` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

$ Rscript -e 'devtools::check(document = FALSE, error_on = "warning")'
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
* using log directory ‘/private<tmp>/RtmpNYEKgt/file11b032aca457e/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-25 20:29:33 UTC
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
 ERROR
Running the tests in ‘tests/testthat.R’ failed.
Last 13 lines of output:
  Saving _problems/test-read_survey-14.R
  [ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]
  
  ══ Failed tests ════════════════════════════════════════════════════════════════
  ── Failure ('test-read_survey.R:14:3'): headcount() returns the weighted share below the line ──
  Expected `headcount(read_survey())` to equal 0.153846.
  Differences:
    `actual`: 0.1538462
  `expected`: 0.1538460
  
  
  [ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]
  Error:
  ! Test failures.
  Execution halted
* checking for non-standard things in the check directory ... OK
* checking for detritus in the temp directory ... OK
* DONE

Status: 1 ERROR
See
  ‘/private<tmp>/RtmpNYEKgt/file11b032aca457e/toypov.Rcheck/00check.log’
for details.

── R CMD check results ─────────────────────────────────────── toypov 0.0.1 ────
Duration: 13.6s

❯ checking tests ...
  See below...

── Test failures ───────────────────────────────────────────────── testthat ────

> library(testthat)
> library(toypov)
> 
> test_check("toypov")
Saving _problems/test-read_survey-14.R
[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

══ Failed tests ════════════════════════════════════════════════════════════════
── Failure ('test-read_survey.R:14:3'): headcount() returns the weighted share below the line ──
Expected `headcount(read_survey())` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]
Error:
! Test failures.
Execution halted

Error: R CMD check found ERRORs
1 error ✖ | 0 warnings ✔ | 0 notes ✔
Execution halted

% Patch 1 file

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ Rscript -e 'devtools::check(document = FALSE, error_on = "warning")'
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
* using log directory ‘/private<tmp>/RtmpQPNOkH/file11e3327821a97/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-25 20:30:06 UTC
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
Duration: 12.8s

0 errors ✔ | 0 warnings ✔ | 0 notes ✔

# Todos
[✓] Inspect package source and test conventions for the requested change
[✓] Implement and test weighted headcount
[•] Record checks and self-review in a Compound GPID work report

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
index bcde534..212d2cd 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,13 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Calculate the weighted headcount ratio
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line Welfare threshold. Households below this value are counted.
+#' @return The weighted share of households with welfare below `line`.
+#' @export
+headcount <- function(dt, line = 3) {
+  return(sum(dt$weight[dt$welfare < line]) / sum(dt$weight))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..c0d56bb 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -9,3 +9,7 @@ test_that("read_survey() refuses a non-positive weight", {
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("headcount() returns the weighted share below the line", {
+  expect_equal(round(headcount(read_survey()), 6), 0.153846)
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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new --help
usage: cg.py new [-h] [--project PROJECT] [--date DATE]
                 {decision,intent,plan,review,solution,work-report}
                 title [title ...]

positional arguments:
  {decision,intent,plan,review,solution,work-report}
  title

options:
  -h, --help            show this help message and exit
  --project PROJECT
  --date DATE

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report "Add weighted headcount" --project "<project>"
created .cg-docs/work-reports/2026-11-25-add-weighted-headcount.md

→ Read .cg-docs/work-reports/2026-11-25-add-weighted-headcount.md

$ Rscript -e 'library(toypov); cat(sprintf("%.10f\n", headcount(read_survey())))'
Threading set to: 12 cores
Error in library(toypov) : there is no package called ‘toypov’
Execution halted

$ Rscript -e 'devtools::load_all(); cat(sprintf("%.10f\n", headcount(read_survey())))'
Threading set to: 12 cores
ℹ Loading toypov
0.1538461538

$ git rev-parse --short HEAD && git hash-object man/headcount.Rd
ff0a04a
9af36c655d98019edb8e7e02354a6376fe616af0

% Patch 1 file
→ Read .cg-docs/work-reports/2026-11-25-add-weighted-headcount.md

$ git status --short
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

$ git diff --check
(no output)

# Todos
[✓] Inspect package source and test conventions for the requested change
[✓] Implement and test weighted headcount
[✓] Record checks and self-review in a Compound GPID work report



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I will inspect the project status and its survey-data conventions before I add the function.
The survey reader returns one row per unique household ID. The worktree already contains a weighted-headcount change, so I will preserve it and add a separate exported `n_households()` function with a focused test.
Added and exported `n_households(dt = read_survey())`. It returns the number of rows, with one row per household in the survey. Added a test that confirms the default survey has 20 households.

Verification passed: all 5 tests pass, and `R CMD check` reports 0 errors, warnings, or notes. Existing changes in the worktree were preserved.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The household-count function is implemented and checked. The existing weighted-headcount changes remain intact.

> code · gpt-6-luna

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
git: repository
branch: main
changed-files: 8
stops: none
next: the human types /cg to run the work through the guide

# Todos
[•] Inspect project conventions and existing changes
[ ] Implement household-count function and focused test
[ ] Run relevant checks and review the diff

→ Read AGENTS.md
→ Skill "r-shared"
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

→ Read DESCRIPTION
→ Read R/read_survey.R
→ Read .cg-docs/work-reports/2026-11-25-add-weighted-headcount.md
→ Read tests/testthat/test-read_survey.R
→ Read inst/extdata/survey.csv [limit=12]
→ Skill "r-collapse"
→ Skill "r-datatable"
→ Skill "r-testing"
→ Skill "r-analytical"
→ Read NAMESPACE

# Todos
[✓] Inspect project conventions and existing changes
[•] Implement household-count function and focused test
[ ] Run relevant checks and review the diff

% Patch 2 files

$ Rscript -e 'roxygen2::roxygenise()'
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'n_households.Rd'

% Patch 1 file

# Todos
[✓] Inspect project conventions and existing changes
[✓] Implement household-count function and focused test
[•] Run relevant checks and review the diff

$ git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE man/n_households.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..e9c642a 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,4 @@
 export(read_survey)
+export(headcount)
+export(n_households)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..04659cc 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,22 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Calculate the weighted headcount ratio
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line Welfare threshold. Households below this value are counted.
+#' @return The weighted share of households with welfare below `line`.
+#' @export
+headcount <- function(dt, line = 3) {
+  return(sum(dt$weight[dt$welfare < line]) / sum(dt$weight))
+}
+
+#' Count households in a survey
+#'
+#' @param dt A data.table with one row per household. Defaults to the toy survey.
+#' @return The number of households in the survey.
+#' @export
+n_households <- function(dt = read_survey()) {
+  return(nrow(dt))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..70b5d79 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -4,8 +4,16 @@ test_that("read_survey() reads the synthetic survey", {
   expect_named(dt, c("hhid", "welfare", "weight"))
 })
 
+test_that("n_households() returns the number of survey households", {
+  expect_equal(n_households(), 20L)
+})
+
 test_that("read_survey() refuses a non-positive weight", {
   path <- withr::local_tempfile(fileext = ".csv")
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("headcount() returns the weighted share below the line", {
+  expect_equal(round(headcount(read_survey()), 6), 0.153846)
+})

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 5 ]

→ Read man/n_households.Rd

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

$ Rscript -e 'devtools::check(document = FALSE, error_on = "warning")'
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
* using log directory ‘/private<tmp>/RtmpAHClLZ/file125696e8b7765/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-25 20:32:37 UTC
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
Duration: 16.7s

0 errors ✔ | 0 warnings ✔ | 0 notes ✔

# Todos
[✓] Inspect project conventions and existing changes
[✓] Implement household-count function and focused test
[✓] Run relevant checks and review the diff



[exit code: 0]
