### B1 setup

> [the text of the installed cg/SKILL.md]

I will inspect the project files and installed packs. I will not open data files or write changes before you approve the setup proposal.
**Measured:** Status reports `phase: setup`, `waiting-on-human: none`, `packs-missing: none`, and `stops: none`. The project has three R files, one `DESCRIPTION`, one `.Rd` file, and one CSV data file: `inst/extdata/survey.csv`. The CSV was not opened.

**Proposal**
- **Packs:** `core` and `lang-r`. Both are installed.
- **R setting:** `lang-r.r-syntax=data.table-collapse`. This is the pack default. The package imports `data.table` in `DESCRIPTION:11-13` and `NAMESPACE:2`.
- **Verification profile draft:** Run command: not found. Doctor command: not found. The package exports `read_survey()`, which returns a `data.table` (`R/read_survey.R:7-23`). Existing tests check the row count and column names, and reject a non-positive weight (`tests/testthat/test-read_survey.R:1-11`). I found no independent reference value or cross-check. I did not run the tests.
- **Data rules:** I need your organization’s classification for `inst/extdata/survey.csv`, the highest classification allowed for **Kilo Code**, and the names of your classification levels from public to most restricted. The project description calls the survey synthetic, but that does not establish its classification.
- **Files the setup command would write:** `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. The dry run listed these paths.

**Assumptions:** I recommend the `data.table-collapse` default because the package imports `data.table`. I have not inferred a data classification or Kilo Code approval.

Please confirm the proposal and provide the data rules. For example: `inst/extdata/survey.csv=Public; Kilo Code approved up to Public; levels: Public, Internal, Confidential`. This example is not a classification recommendation.

**Next steps: Waiting on you**
* **Your move:** Reply with a clear yes and the data rules, or correct the proposal.
* **Project:** Setup is still in the read-only proposal stage. No files were changed.

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

→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read DESCRIPTION
→ Read tests/testthat.R
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R
✱ Glob "**/*" in . · 8 matches
✗ Read ~/.agents/skills/cg/principles/P12-data-classification.md failed
Error: File not found: ~/.agents/skills/cg/principles/P12-data-classification.md
✱ Glob "**/GLOSSARY.md" in . · 0 matches
→ Read ~/.agents/skills/r-testing/SKILL.md
→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/r-technical/SKILL.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/GLOSSARY.md
→ Read ~/.agents/skills/cg/principles/P02-human-decides.md
→ Read ~/.agents/skills/cg/templates/verification.md
→ Read ~/.agents/skills/cg/principles/P12-governed-data.md
→ Read man/read_survey.Rd
→ Read NAMESPACE

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

✱ Glob ".*" in . · 0 matches
✱ Glob "**/.*" in . · 0 matches
✱ Glob "Makefile|_targets.R|renv.lock|*.Rproj|AGENTS.md|CLAUDE.md|GLOSSARY.md|compound-gpid*.md|.cg-docs/**" in . · 0 matches

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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --project "<project>" --dry-run
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore



[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Your reply confirms the packs, R setting, Public classification for the survey, and Public as the highest level Kilo Code may read. You did not provide the full classification-level scheme, so I will leave that field out. I will run setup, then add the verification draft we proposed.
Setup created the five previewed files. I will now replace the verification template placeholders with the draft findings: no project Run or Doctor command found, and `read_survey()` as the documented output.
Setup is complete. Status reports `phase: ready`, `stops: none`, and no missing packs. It records `lang-r.r-syntax=data.table-collapse`, `inst/extdata/survey.csv=Public`, and `Kilo Code=Public`.

Setup created `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. I filled the verification profile with the draft we discussed. Its Run and Doctor commands remain `not found`, so the profile remains a draft. The full classification-level scheme was not provided and is not recorded. I did not run the package tests.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** Setup is ready. The guide points to `playbooks/quick.md` for the next work step.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo Code=Public" --project "<project>"
created .cg-docs/config.json
created .cg-docs/verification.md
created AGENTS.md
created CLAUDE.md
created .Rbuildignore

→ Read .cg-docs/verification.md
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
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md



[exit code: 0]

### C1 request

> [the text of the installed cg/SKILL.md]

Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

/cg` would run this change with checks and a record. I will read the Compound GPID launcher and project status first.
This change adds `headcount(dt, line = 3)` and a testthat check for the expected weighted share, `0.153846`. I will leave other functions and survey data unchanged.

**Hard stop: line 1 is yes.** The function computes a share that someone will read. The playbook requires your approval before I make this change.

**Contract:** I will add the function and one testthat check. I will not change the survey data or other behavior. I will run the new test and compare its result with your expected value, `0.153846`; a mismatch will mean failure.

Reply **“yes”** to approve this contract.

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
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

→ Read ~/.agents/skills/cg/playbooks/quick.md


[exit code: 0]

### C2 yes

> Yes, proceed.

Approval is recorded for the stated change and checks. I will inspect the R function and test layout, the required Compound GPID principles, and the current worktree before editing.
The package stores one row per household with `welfare` and positive `weight`; its synthetic survey is classified Public. The expected share is consistent with the input: households below 3 have total weight 7 of 45.5. I will add the function beside `read_survey()` and test it on the package survey.
The new test fails before the implementation because `headcount()` is not defined. I will now add the exported function with basic checks for required columns, missing values, and valid positive weights.
The first post-change test showed that testthat treats `tolerance` as a relative tolerance, so `1e-6` was just below the rounding difference from the six-decimal expectation. I adjusted it to `3.3e-6`, which allows rounding to six decimal places without changing the expected value. The `air` formatter is not installed, so I will report formatting as not checked.
Added and exported `headcount(dt, line = 3)` in `R/read_survey.R`. It returns the sum of household weights below the line divided by the total weight. Added a testthat check, the namespace export, and generated help documentation.

**Measured checks**
- `Rscript -e 'devtools::test()'`: verified; 4 passed.
- `Rscript -e 'devtools::check()'`: verified; 0 errors, 0 warnings, 0 notes.
- The function returned `0.153846153846`, which rounds to the expected `0.153846`. The independent arithmetic from the survey weights is `7 / 45.5`.
- `git diff --check`: verified.

**Self-review:** P3, P4, and P6 passed. The `air` formatter was not checked because it is not installed. The project verification profile has no Run or Doctor command and remains a draft.

The Compound GPID work report is `.cg-docs/work-reports/2026-11-25-add-weighted-headcount.md`. Pre-existing untracked setup files were left unchanged. No commit was made.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The weighted headcount function and its checks are complete; the work report records the evidence.

> code · gpt-6-luna

# Todos
[•] Inspect project status, function and test files, and required principles
[ ] Add weighted headcount and a focused testthat check
[ ] Run checks and compare with expected value
[ ] Write the Compound GPID work report and review evidence

→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
✱ Glob "**/test*" 2 matches
✱ Glob "GLOSSARY.md" 0 matches
✱ Glob "**/*.R" 3 matches
→ Read ~/.agents/skills/cg/GLOSSARY.md
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R
→ Read .cg-docs/config.json

$ git status --short && git diff -- R/read_survey.R tests/testthat/test-read_survey.R && git diff --cached -- R/read_survey.R tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md

→ Read NAMESPACE
→ Read DESCRIPTION
→ Read inst/extdata/survey.csv
✱ Glob "**/GLOSSARY.md" in . · 0 matches

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

→ Skill "r-shared"
→ Skill "r-datatable"
→ Skill "r-collapse"
→ Skill "r-analytical"
→ Skill "r-testing"
→ Skill "r-package-development"

# Todos
[✓] Inspect project status, function and test files, and required principles
[•] Add weighted headcount and a focused testthat check
[ ] Run checks and compare with expected value
[ ] Write the Compound GPID work report and review evidence

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

✗ Read NEWS.md failed
Error: File not found: <project>/NEWS.md
% Patch 2 files

# Todos
[✓] Inspect project status, function and test files, and required principles
[✓] Add weighted headcount and a focused testthat check
[•] Run checks and compare with expected value
[ ] Write the Compound GPID work report and review evidence

$ air format --check .
zsh:1: command not found: air

$ Rscript -e 'devtools::document()'
Threading set to: 12 cores
ℹ Updating toypov documentation
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

$ Rscript -e 'devtools::test(filter = "read_survey")'
Threading set to: 12 cores
ℹ Testing toypov
FAILURE: 'test-read_survey.R:15:3' ----------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

→ Read tests/testthat/test-read_survey.R
→ Read man/headcount.Rd

$ git status --short && git diff --stat && git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE man/headcount.Rd
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd
 NAMESPACE                         |  1 +
 R/read_survey.R                   | 25 +++++++++++++++++++++++++
 tests/testthat/test-read_survey.R |  5 +++++
 3 files changed, 31 insertions(+)
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..6d0427d 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,28 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Calculate the weighted share of households below a welfare line
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line Welfare threshold. Households with welfare below this value
+#'   are counted.
+#' @return A numeric value between zero and one.
+#' @export
+#' @examples
+#' dt <- read_survey()
+#' headcount(dt)
+headcount <- function(dt, line = 3) {
+  needed <- c("welfare", "weight")
+  missing_cols <- setdiff(needed, names(dt))
+  if (length(missing_cols) > 0) {
+    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
+  }
+  if (anyNA(dt$welfare)) {
+    stop("welfare must be present for every household")
+  }
+  if (anyNA(dt$weight) || any(dt$weight <= 0)) {
+    stop("weight must be present and positive for every household")
+  }
+  return(sum(dt$weight[dt$welfare < line]) / sum(dt$weight))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..bcadbf0 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -9,3 +9,8 @@ test_that("read_survey() refuses a non-positive weight", {
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("headcount() returns the weighted share below the line", {
+  dt <- read_survey()
+  expect_equal(headcount(dt), 0.153846, tolerance = 1e-6)
+})

$ Rscript -e 'devtools::load_all(); dt <- read_survey(); print(headcount(dt), digits = 12); print(7 / 45.5, digits = 12); print(all.equal(headcount(dt), 0.153846, tolerance = 1e-6))'
Threading set to: 12 cores
ℹ Loading toypov
[1] 0.153846153846
[1] 0.153846153846
[1] TRUE

$ Rscript -e 'devtools::test(filter = "read_survey")'
Threading set to: 12 cores
ℹ Testing toypov
FAILURE: 'test-read_survey.R:15:3' ----------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

✱ Grep "tolerance|expect_equal" in . · 2 matches

$ Rscript -e 'testthat::expect_equal(7 / 45.5, 0.153846, tolerance = 1e-6); cat("pass\n")'
Threading set to: 12 cores
Error: Expected `7/45.5` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460
Execution halted

% Patch 1 file
% Patch 1 file

$ Rscript -e 'devtools::load_all(); dt <- read_survey(); value <- headcount(dt); cat(sprintf("weighted share: %.12f\n", value)); stopifnot(round(value, 6) == 0.153846)'
Threading set to: 12 cores
ℹ Loading toypov
weighted share: 0.153846153846

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ Rscript -e 'devtools::check()'
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
* using log directory ‘/private<tmp>/Rtmp2yKMhe/file749d5bb4e88/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-25 22:23:36 UTC
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
* checking examples ... OK
* checking for unstated dependencies in ‘tests’ ... OK
* checking tests ...
  Running ‘testthat.R’
 OK
* checking for non-standard things in the check directory ... OK
* checking for detritus in the temp directory ... OK
* DONE

Status: OK

── R CMD check results ─────────────────────────────────────── toypov 0.0.1 ────
Duration: 13.5s

0 errors ✔ | 0 warnings ✔ | 0 notes ✔

# Todos
[✓] Inspect project status, function and test files, and required principles
[✓] Add weighted headcount and a focused testthat check
[✓] Run checks and compare with expected value
[•] Write the Compound GPID work report and review evidence

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

$ git status --short && git diff --check && git diff --stat && git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE man/headcount.Rd
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd
 NAMESPACE                         |  1 +
 R/read_survey.R                   | 25 +++++++++++++++++++++++++
 tests/testthat/test-read_survey.R |  5 +++++
 3 files changed, 31 insertions(+)
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..6d0427d 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,28 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Calculate the weighted share of households below a welfare line
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line Welfare threshold. Households with welfare below this value
+#'   are counted.
+#' @return A numeric value between zero and one.
+#' @export
+#' @examples
+#' dt <- read_survey()
+#' headcount(dt)
+headcount <- function(dt, line = 3) {
+  needed <- c("welfare", "weight")
+  missing_cols <- setdiff(needed, names(dt))
+  if (length(missing_cols) > 0) {
+    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
+  }
+  if (anyNA(dt$welfare)) {
+    stop("welfare must be present for every household")
+  }
+  if (anyNA(dt$weight) || any(dt$weight <= 0)) {
+    stop("weight must be present and positive for every household")
+  }
+  return(sum(dt$weight[dt$welfare < line]) / sum(dt$weight))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..2b52fb0 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -9,3 +9,8 @@ test_that("read_survey() refuses a non-positive weight", {
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("headcount() returns the weighted share below the line", {
+  dt <- read_survey()
+  expect_equal(headcount(dt), 0.153846, tolerance = 3.3e-6)
+})

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report "Add weighted headcount" --project "<project>"
created .cg-docs/work-reports/2026-11-25-add-weighted-headcount.md

→ Read .cg-docs/work-reports/2026-11-25-add-weighted-headcount.md
→ Read .cg-docs
→ Read .cg-docs/verification.md

$ git diff --check
(no output)

$ git rev-parse --short HEAD && git hash-object R/read_survey.R && git hash-object tests/testthat/test-read_survey.R && git hash-object NAMESPACE && git hash-object man/headcount.Rd
d7ec8c9
6d0427d21398713bc9d8646d4d38691dbb6beec3
2b52fb0a5f96e116aa18aed3ad73c2379c3811bb
6419142bf523ab71c37a3d42deece98d0614ce26
e82f5fd22046b041bb25a5790e84bb5a791faf1f

% Patch 1 file

$ git diff --check && git status --short
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

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
git: repository
branch: main
changed-files: 8
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

# Todos
[✓] Inspect project status, function and test files, and required principles
[✓] Add weighted headcount and a focused testthat check
[✓] Run checks and compare with expected value
[✓] Write the Compound GPID work report and review evidence



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

/cg` would run this change with checks and a record. I will inspect the project state and its R conventions, then add and test a small function.
The package already reads one row per household, so the new function can count rows in that survey table. I will add an exported `household_count()` function with a default call to `read_survey()`, and test both default and supplied data.
The tests pass. The package does not have the `air` formatter installed, and its `NAMESPACE` is maintained by hand, so I will add the export there and rerun the tests.
Added exported `household_count()`. It returns the number of rows in the supplied survey table, or reads the packaged survey by default. Added tests for both uses and generated `man/household_count.Rd`.

All package tests pass: 6 passed, 0 failed. `air format .` could not run because `air` is not installed.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The household-count function and tests are in place; the package test suite passes.

> code · gpt-6-luna

$ ls
AGENTS.md
CLAUDE.md
DESCRIPTION
LICENSE
NAMESPACE
R
inst
man
tests

$ python3 -c 'import json,pathlib; p=pathlib.Path.home()/".cg/launcher.json"; print(p.read_text() if p.exists() else "MISSING")'
{
  "cg": "~/.agents/skills/cg/scripts/cg.py",
  "core": "1.99.0.9000",
  "python": "/opt/homebrew/opt/python@3.14/bin/python3.14"
}

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
git: repository
branch: main
changed-files: 8
stops: none
next: the human types /cg to run the work through the guide

→ Skill "r-shared"
→ Skill "r-datatable"
→ Skill "r-package-development"
→ Read DESCRIPTION
✱ Glob "R/**/*.R" 1 match
✱ Glob "tests/testthat/**/*.R" 1 match

$ git status --short
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R
✱ Glob "inst/extdata/*" 1 match
✱ Grep "household|headcount" in . · 11 matches
% Patch 2 files

$ Rscript -e 'devtools::document()'
Threading set to: 12 cores
ℹ Updating toypov documentation
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'household_count.Rd'

→ Read NAMESPACE

$ air format .
zsh:1: command not found: air

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 6 ]

% Patch 1 file
→ Read man/household_count.Rd

$ git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE man/household_count.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..ab4fb13 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,4 @@
 export(read_survey)
+export(headcount)
+export(household_count)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..d134a17 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,40 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Count households in a survey
+#'
+#' @param dt A data.table with one row per household. Defaults to the packaged
+#'   survey.
+#' @return The number of households in the survey.
+#' @export
+#' @examples
+#' household_count()
+household_count <- function(dt = read_survey()) {
+  return(nrow(dt))
+}
+
+#' Calculate the weighted share of households below a welfare line
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line Welfare threshold. Households with welfare below this value
+#'   are counted.
+#' @return A numeric value between zero and one.
+#' @export
+#' @examples
+#' dt <- read_survey()
+#' headcount(dt)
+headcount <- function(dt, line = 3) {
+  needed <- c("welfare", "weight")
+  missing_cols <- setdiff(needed, names(dt))
+  if (length(missing_cols) > 0) {
+    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
+  }
+  if (anyNA(dt$welfare)) {
+    stop("welfare must be present for every household")
+  }
+  if (anyNA(dt$weight) || any(dt$weight <= 0)) {
+    stop("weight must be present and positive for every household")
+  }
+  return(sum(dt$weight[dt$welfare < line]) / sum(dt$weight))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..bdb905e 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -9,3 +9,13 @@ test_that("read_survey() refuses a non-positive weight", {
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("household_count() counts households in the survey", {
+  expect_equal(household_count(), 20)
+  expect_equal(household_count(read_survey()[1:3]), 3)
+})
+
+test_that("headcount() returns the weighted share below the line", {
+  dt <- read_survey()
+  expect_equal(headcount(dt), 0.153846, tolerance = 3.3e-6)
+})

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 6 ]



[exit code: 0]
