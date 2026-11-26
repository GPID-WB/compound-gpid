### B1 setup

> [the text of the installed cg/SKILL.md]

The project is an R package, and the R pack is installed. I am checking its package files and setup templates now. I will not open the CSV data file.
**Measured:** The project has seven tracked files: one `.R` source file, two `.R` test files, one `.csv` data file, one `.Rd` help file, and two files without extensions. It is an R package. `R/read_survey.R` reads the packaged CSV. I did not open the CSV.

**Recommended setup:** Use the `core` and `lang-r` packs. Both are installed. The R source uses `data.table::fread()` (`R/read_survey.R:8`), so I recommend the `data.table-collapse` syntax setting. That is also the pack default.

**Verification profile draft:** No single command that produces the package’s output was found. The output is a `data.table` returned by `read_survey()`. Existing tests check its row count and column names, and check that a non-positive weight is rejected (`tests/testthat/test-read_survey.R:1–10`). No separate read-only environment check or independent reference for the output was found.

**One decision is needed:** What classification does your organization assign to `inst/extdata/survey.csv`, what is the highest classification Kilo Code may read, and what are the organization’s classification levels from public to most restricted? The project description calls the data synthetic, but that does not set its classification.

You can reply in this form:

```text
inst/extdata/survey.csv: <classification>
Kilo Code may read up to: <classification>
Levels, public to most restricted: <level>; <level>; <level>
```

**Measured:** The setup preview would create `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. The preview wrote no files. I recommend recording the tool name as `Kilo Code`.

**Assumptions:** I treated the opened project folder as the project root. The setup is not complete until you provide the data decisions above.

**Next steps: Waiting on you**
* **Your move:** Reply with the three data decisions in the format above.
* **Project:** Setup remains in the proposal stage; no project files have changed.

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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" --help
usage: cg.py [-h] {doctor,status,new,packs,setup,validate,approve,tier} ...

Compound GPID core tooling.

positional arguments:
  {doctor,status,new,packs,setup,validate,approve,tier}
    doctor              check this machine and write the launcher file
    status              print the state of the work in a project
    new                 create an artifact under .cg-docs/
    packs               list the installed packs
    setup               write what the human confirmed in the setup playbook
    validate            check the artifacts under .cg-docs/ against the schema
    approve             record the human's yes to a plan or an intent, or
                        their decision on data
    tier                compute the risk level of a piece of work from
                        declared facts

options:
  -h, --help            show this help message and exit

→ Read DESCRIPTION
→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read tests/testthat.R
→ Read R/read_survey.R
✱ Glob "**/GLOSSARY.md" in . · 0 matches
→ Read ~/.agents/skills/cg/templates/verification.md
→ Read tests/testthat/test-read_survey.R
✱ Glob "AGENTS.md" in . · 0 matches
→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/GLOSSARY.md
→ Read ~/.agents/skills/cg/principles/P02-human-decides.md
✱ Glob "principles/P12*" in ~/.agents/skills/cg · 1 match
→ Read ~/.agents/skills/cg/principles/P12-governed-data.md
→ Read LICENSE
→ Read NAMESPACE
→ Read man/read_survey.Rd

$ ls -la
total 24
drwxr-xr-x  10 <user>  staff  320 Nov 26 14:06 .
drwxr-xr-x   6 <user>  staff  192 Nov 26 14:06 ..
drwxr-xr-x  13 <user>  staff  416 Nov 26 14:07 .git
-rw-r--r--   1 <user>  staff  560 Nov 25 14:26 DESCRIPTION
-rw-r--r--   1 <user>  staff   44 Nov 25 00:08 LICENSE
-rw-r--r--   1 <user>  staff   50 Nov 25 00:08 NAMESPACE
drwxr-xr-x   3 <user>  staff   96 Nov 25 00:08 R
drwxr-xr-x   3 <user>  staff   96 Nov 25 00:08 inst
drwxr-xr-x   3 <user>  staff   96 Nov 25 14:10 man
drwxr-xr-x   4 <user>  staff  128 Nov 25 00:08 tests

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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --project "<project>" --dry-run
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore



[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

The reply confirms the proposed packs and syntax setting, and it sets the survey classification and Kilo Code clearance to Public. I will write those confirmed choices. I will leave the organization’s classification-level names unset because they were not provided.
**Setup is complete.**

**Measured:** Status reports `phase: ready`, `stops: none`, and no missing packs. The settings line is `lang-r.r-syntax=data.table-collapse`. Status records `inst/extdata/survey.csv=Public` and `Kilo Code=Public`.

The setup command created `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. The verification profile is still a draft. It records Run and Doctor as “not found” and describes the `read_survey()` output and current checks. I did not run package checks.

The organization’s classification-level names remain unspecified. No classification levels were added to the configuration.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** Setup is ready. The verification profile remains a draft, and classification-level names are not recorded.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo Code=Public" --project "<project>"
created .cg-docs/config.json
created .cg-docs/verification.md
created AGENTS.md
created CLAUDE.md
created .Rbuildignore

→ Read .cg-docs/config.json
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
data-decisions: none
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

`/cg` would run this change with checks and a record. I will read the Compound GPID state first, then follow its selected playbook.
The requested function computes a numeric share and adds a public function interface, so the change needs the elevated tier check. I will check the target files and the project’s R pack instructions before I change code.
`/cg` would run this change with checks and a record. The tier check returned `elevated` because `headcount()` computes a number and adds a public function interface. The survey file is cleared as `Public`.

**Proposed contract:** Add and export `headcount(dt, line = 3)` to return the weighted share of households with `welfare < line`. Add a testthat check for the toy survey’s expected value, `0.153846`. Leave other measures and files unchanged. I will run the package tests and check that the returned share matches your expected value to six decimal places. A test failure or a different value will count as failure.

Reply **yes** to approve this contract.

> code · gpt-6-luna

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

# Todos
[•] Inspect target files and check change tier
[ ] Implement headcount and its test
[ ] Run checks, self-review, and record work

✱ Glob "R/**;tests/**;DESCRIPTION;NAMESPACE;GLOSSARY.md;.cg-docs/config.json" 0 matches
✱ Glob "**/*" 13 matches
→ Read AGENTS.md
→ Read DESCRIPTION
→ Read R/read_survey.R
→ Read NAMESPACE
→ Read .cg-docs/config.json
→ Read tests/testthat/test-read_survey.R
→ Read inst/extdata/survey.csv

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "tests/testthat/test-read_survey.R" --reads "inst/extdata/survey.csv" --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 2



[exit code: 0]

### C2 yes

> Yes, proceed.

The contract is approved. I will load the R pack guidance, then implement the function and test without changing other files.
The welfare guidance defines the headcount ratio as the weighted mean of the below-line indicator. I will use that definition and include checks for missing welfare or invalid weights, so the function cannot silently drop households. The test will compare the toy survey value with your stated expectation.
The first package test run showed the estimate is `0.1538461538`, which rounds to your six-decimal expectation. The test’s tolerance was slightly too tight under testthat’s relative comparison, so I will compare at the approved six-decimal precision instead.
**Measured:** Added and exported `headcount(dt, line = 3)`. It returns the weighted share of households with welfare below the line. The toy survey output rounds to `0.153846` at six decimal places.

The function and test are in `R/read_survey.R` and `tests/testthat/test-read_survey.R`. Package export and help are in `NAMESPACE` and `man/headcount.Rd`.

**Checks:** `devtools::test()` passed, and `devtools::check()` passed with 0 errors, 0 warnings, and 0 notes. The work report passed validation: `.cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md`.

**Self-review:** P3, P4, and P6 passed. No independent software cross-check was run. Existing unrelated worktree changes were left untouched.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** `headcount()` and its test are implemented, checks pass, and the work report is complete.

> code · gpt-6-luna

# Todos
[✓] Inspect target files and check change tier
[•] Implement headcount and its test
[ ] Run checks, self-review, and record work

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
→ Skill "r-technical"
→ Read ~/.agents/skills/r-analytical/workflows/welfare-patterns.md
✱ Glob "GLOSSARY.md;principles/README.md;principles/P3*;principles/P4*;principles/P6*" 0 matches
✱ Glob "**/principles/**" 0 matches
→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/GLOSSARY.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Read ~/.agents/skills/r-technical/workflows/package-development.md
% Patch 1 file
⚙ stata-mcp_stata_run_selection {"selection":"testthat::test_file('tests/testthat/test-read_survey.R')","working_dir":"<project>"}

$ Rscript -e "testthat::test_file('tests/testthat/test-read_survey.R')"
Threading set to: 12 cores
ERROR: 'test-read_survey.R:2:3' -------------------
Error in `read_survey()`: could not find function "read_survey"

ERROR: 'test-read_survey.R:10:3' ------------------
Error in `read_survey(path)`: could not find function "read_survey"
Backtrace:
    ▆
 1. └─testthat::expect_error(read_survey(path), "weight must be present and positive") at test-read_survey.R:10:3
 2.   └─testthat:::expect_condition_matching_(...)
 3.     └─testthat:::quasi_capture(...)
 4.       ├─testthat (local) .capture(...)
 5.       │ └─base::withCallingHandlers(...)
 6.       └─rlang::eval_bare(quo_get_expr(.quo), quo_get_env(.quo))

ERROR: 'test-read_survey.R:14:3' ------------------
Error in `read_survey()`: could not find function "read_survey"

[ FAIL 3 | WARN 0 | SKIP 0 | PASS 0 ]

% Patch 1 file
% Patch 1 file

# Todos
[✓] Inspect target files and check change tier
[✓] Implement headcount and its test
[•] Run checks, self-review, and record work

→ Read .cg-docs/verification.md

$ git status --short && git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..fa27a12 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,33 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Compute the weighted household headcount ratio
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line Numeric poverty line. Households with welfare below this value
+#'   are counted as poor.
+#' @return The weighted share of households with welfare below `line`.
+#' @export
+#' @examples
+#' headcount(read_survey())
+headcount <- function(dt, line = 3) {
+  needed <- c("welfare", "weight")
+  missing_cols <- setdiff(needed, names(dt))
+  if (length(missing_cols) > 0) {
+    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
+  }
+  if (length(line) != 1 || is.na(line) || !is.finite(line)) {
+    stop("line must be a single finite number")
+  }
+  if (anyNA(dt$welfare)) {
+    stop("welfare must be present for every household")
+  }
+  if (anyNA(dt$weight) || any(dt$weight <= 0)) {
+    stop("weight must be present and positive for every household")
+  }
+  if (nrow(dt) == 0) {
+    stop("survey must contain at least one household")
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

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
FAILURE: 'test-read_survey.R:15:3' ----------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

% Patch 1 file

$ Rscript -e "roxygen2::roxygenise()"
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ Rscript -e "devtools::check()"
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
* using log directory ‘<tmp>/RtmpBoJH7F/file13156594d6291/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-26 19:11:43 UTC
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
Duration: 17.6s

0 errors ✔ | 0 warnings ✔ | 0 notes ✔

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report --help
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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report "Add weighted household headcount" --project "<project>"
created .cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md

→ Read .cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md
→ Read man/headcount.Rd

$ git rev-parse --short HEAD && git status --short
44626f5
 M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

$ git hash-object man/headcount.Rd && git diff --check
f0071ebd3efe3e703d1c20e156d285ce31866dcb

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

% Patch 1 file

$ git diff --check && git diff --stat && git status --short
NAMESPACE                         |  1 +
 R/read_survey.R                   | 30 ++++++++++++++++++++++++++++++
 tests/testthat/test-read_survey.R |  5 +++++
 3 files changed, 36 insertions(+)
 M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

# Todos
[✓] Inspect target files and check change tier
[✓] Implement headcount and its test
[✓] Run checks, self-review, and record work



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll first check the project status and its R conventions, then add the function in the right place.
The survey reader returns one row per household, so the count should use the row count. I’ll add a documented `household_count()` function that reads the bundled survey by default and accepts an existing survey table.
Added and exported `household_count()`. It returns the number of rows in a survey table, or counts the bundled survey when called without an argument. Added an example and tests for both uses.

`R CMD check` passed with 0 errors, warnings, or notes.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The household-count function is implemented and verified in `R/read_survey.R`.

> code · gpt-6-luna

→ Skill "r-shared"

$ ls -la ~/.cg <project>
~/.cg:
total 16
drwxr-xr-x    4 <user>  staff   128 Nov 26 13:52 .
drwx------+ 123 <user>  staff  3936 Nov 26 14:05 ..
-rw-------    1 <user>  staff  1558 Nov 26 13:52 installed.json
-rw-------    1 <user>  staff   150 Nov 25 09:36 launcher.json

<project>:
total 48
drwxr-xr-x  14 <user>  staff   448 Nov 26 14:08 .
drwxr-xr-x   6 <user>  staff   192 Nov 26 14:06 ..
-rw-------   1 <user>  staff    38 Nov 26 14:08 .Rbuildignore
drwxr-xr-x   5 <user>  staff   160 Nov 26 14:12 .cg-docs
drwxr-xr-x  13 <user>  staff   416 Nov 26 14:13 .git
-rw-------   1 <user>  staff  1000 Nov 26 14:08 AGENTS.md
-rw-------   1 <user>  staff    11 Nov 26 14:08 CLAUDE.md
-rw-r--r--   1 <user>  staff   560 Nov 25 14:26 DESCRIPTION
-rw-r--r--   1 <user>  staff    44 Nov 25 00:08 LICENSE
-rw-r--r--   1 <user>  staff    68 Nov 26 14:11 NAMESPACE
drwxr-xr-x   3 <user>  staff    96 Nov 25 00:08 R
drwxr-xr-x   3 <user>  staff    96 Nov 25 00:08 inst
drwxr-xr-x   4 <user>  staff   128 Nov 26 14:11 man
drwxr-xr-x   4 <user>  staff   128 Nov 25 00:08 tests

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

→ Skill "r-datatable"
→ Skill "r-collapse"
→ Read DESCRIPTION
→ Read inst/extdata/survey.csv [limit=8]
✱ Glob "R/**" 1 match

$ git status --short
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

→ Read NAMESPACE
→ Read R/read_survey.R
→ Read man/headcount.Rd
→ Read tests/testthat/test-read_survey.R
% Patch 2 files

$ Rscript -e 'roxygen2::roxygenise()' && Rscript -e 'testthat::test_local()'
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'household_count.Rd'
Threading set to: 12 cores
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 6 ]

→ Read NAMESPACE
% Patch 1 file

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
* using log directory ‘<tmp>/Rtmpz74GxR/file1383f19fae19b/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-26 19:14:26 UTC
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
Duration: 16.9s

0 errors ✔ | 0 warnings ✔ | 0 notes ✔



[exit code: 0]

### G1 idea

> [the text of the installed cg/SKILL.md]

brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

`/cg` would run this change with checks and a record. I will read the project status first, then follow the selected brainstorm playbook.
The project status has no open decisions, and the brainstorm intent is created. I will inspect the package API and its verification record; I will not open the survey data or run package code.
The package has a weighted headcount, but no measure of poverty depth. The field term for the standard companion measure is the **poverty gap index**: the average shortfall from the poverty line across all households, with non-poor households counted as having zero shortfall. The World Bank indicator metadata uses this definition and says it reflects both poverty depth and incidence. I will record these facts and ask which interpretation the new measure should use.
The intent is recorded at `.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md` with status **draft**. I have not built or changed package code.

**Measured:** `headcount()` returns the weighted share of households below the poverty line. The World Bank defines the **poverty gap index** as the average shortfall from the line across all households, with non-poor households counted as zero. This measure reflects both poverty depth and incidence.

**Inferred:** This is the closest standard match for a measure alongside the package’s existing headcount. It does not isolate how far below the line poor households are on average; for that, the alternative is the mean shortfall among poor households only.

**Decision D1 is open:** Should the package report the poverty gap index, or the average shortfall among poor households only? I recommend the poverty gap index. Its trade-off is that it can fall when poverty becomes less common, even if poor households’ average shortfall does not change.

**Assumption:** The new measure should use the household weights already used by `headcount()`.

I did not check the survey data or run package code. Should I use the poverty gap index? A plain **yes** confirms that choice. Anything else will be treated as a change or question.

**Next steps: Waiting on you**
* **Your move:** Reply with your choice of measure.
* **Project:** The measure choice is open in the draft intent; after your answer, the brainstorm will continue.

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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --project "<project>" --playbook brainstorm
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
→ Read ~/.agents/skills/cg/grilling.md

# Todos
[•] Create brainstorm intent and inspect package terms, code, and prior records
[ ] Write grounded facts and ask the first decision round

✱ Glob "**/*" in . · 16 matches

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new intent "Poverty depth measure" --project "<project>"
created .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md

→ Read DESCRIPTION
→ Read CLAUDE.md
→ Read R/read_survey.R
→ Read .cg-docs/verification.md
✱ Glob "GLOSSARY.md" in . · 0 matches
→ Read .cg-docs/work-reports/2026-11-26-add-weighted-household-headcount.md
→ Read tests/testthat/test-read_survey.R
✱ Glob ".cg-docs/{brainstorms,plans,decisions}/**/*" in . · 0 matches
% WebFetch https://www.worldbank.org/en/topic/poverty/brief/global-poverty-monitoring-technical-note
→ Read .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md
✗ WebFetch https://data.worldbank.org/indicator/SI.POV.GAP2 failed
Error: StatusCode: non 2xx status code (403 GET https://data.worldbank.org/indicator/SI.POV.GAP2)
% WebFetch https://api.worldbank.org/v2/indicator/SI.POV.GAP2?format=json
% Patch 1 file

# Todos
[✓] Create brainstorm intent and inspect package terms, code, and prior records
[✓] Write grounded facts and ask the first decision round



[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

Your reply selects the recommended poverty gap index and sets two constraints: use a hand-built arithmetic example for reference values, and keep the change small. I will record these answers. One output choice remains: whether the index should be returned as a fraction or a percentage.
I recorded your choice of the poverty gap index and your request for a small arithmetic example in `.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md`. I added its definition to `GLOSSARY.md`.

**Decision D2 is open:** Should the index be returned as a **fraction**, like `headcount()` (recommended for consistency), or as a **percentage** (as in the World Bank indicator metadata)? A fraction is less familiar to readers who expect percentages; they can multiply it by 100.

Reply with **fraction** or **percentage**. A plain **yes** selects the recommended fraction. Anything else will be treated as a change or question.

**Next steps: Waiting on you**
* **Your move:** Choose a fraction or percentage scale.
* **Project:** The brainstorm stays in draft until the remaining decisions are settled.

> code · gpt-6-luna

→ Read .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md
✗ Patch failed
Error: apply_patch verification failed: Error: Failed to find expected lines in <project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md:
| D1 | Should the package report the poverty gap index (shortfall relative to the line averaged over all households, including zero shortfall for non-poor households), or the average shortfall among poor households only? | Recommend the poverty gap index as the standard complement to the existing headcount and because authoritative World Bank metadata defines it as reflecting both incidence and depth. Cost: it will be lower when poverty is less prevalent, even if the poor households' average shortfall is unchanged. The poor-only mean isolates depth but does not describe the population-wide burden. | open |
✗ Patch failed
Error: apply_patch verification failed: Error: Failed to find expected lines in <project>/.cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md:
| D1 | Should the package report the poverty gap index (shortfall relative to the line averaged over all households, including zero shortfall for non-poor households), or the average shortfall among poor households only? | Recommend the poverty gap index as the standard complement to the existing headcount and because authoritative World Bank metadata defines it as reflecting both incidence and depth. Cost: it will be lower when poverty is less prevalent, even if the poor households' average shortfall is unchanged. The poor-only mean isolates depth but does not describe the population-wide burden. | open |
→ Read .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md [offset=40, limit=10]
% Patch 1 file
% Patch 1 file


[exit code: 0]

### G3 answer

> Yes to each question: I take the answer you recommend. I have no figure of my own to give: where a reference value is needed, use a hand-built example whose value follows from arithmetic. Keep it as small as you can.

Your reply selects the recommended fraction scale. The measure and scale are now set. I will state a narrow implementation intent that matches the existing `headcount()` interface, then validate the intent before asking you to confirm it.
The intent is valid: **0 problems, 0 warnings**. It remains **draft** until you confirm it.

**Goal:** Add a weighted poverty gap index next to the household headcount. Return a fraction. Use a small arithmetic test example and keep the change small.

**Out of scope:** Do not add the poor-only mean or other measures. Do not change the headcount or survey reader.

**A wrong result:** The calculation uses only poor households in the denominator, does not divide each shortfall by the poverty line, ignores weights, or fails the example. With a line of 10, welfare values 5 and 10, and equal weights, the result is 0.25.

**Decisions recorded:** The measure is the poverty gap index, not the average shortfall among poor households only. The result is a fraction, not a percentage.

**Approaches:** The poverty gap index is selected because it measures the population-wide shortfall. The poor-only mean is set aside because it does not include incidence. Percentage output is set aside to match `headcount()`.

**Assumptions I am making:**
1. Name the function `poverty_gap()` and give it the same `dt` and `line = 3` interface as `headcount()`. If wrong, the public API will differ.
2. Use the existing household weights. If wrong, the measure’s meaning and result will change.
3. Use a two-household example as the reference. If more examples are needed to define correct behavior, the scope will grow.

**Inferred:** This is a minimal extension of the current API. I did not open the survey data or run package code.

Is this intent correct as written? A plain **yes** confirms it and is recorded. Anything else will be treated as a change or question.

**Next steps: Waiting on you**
* **Your move:** Reply **yes** to confirm, or state what to change.
* **Project:** The intent is validated and ready for your confirmation; no package code has been built.

> code · gpt-6-luna

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0



[exit code: 0]

### G4 vague reply

> Sounds good.

“Sounds good” does not confirm the intent. Reply with a plain **yes** to confirm it, or tell me what to change.

> code · gpt-6-luna



[exit code: 0]

### G5 answer

> Yes.

The brainstorm is **decided**. Your “Yes.” was recorded in `.cg-docs/approvals/2026-11-26-poverty-depth-measure.6934337c8a2ac38e.json`.

**Measured:** The intent specifies a weighted poverty gap index returned as a fraction, with a small hand-built arithmetic example. The approval record is present.

**Inferred:** A small extension to `headcount()` is the chosen approach. The average shortfall among poor households only and percentage output are set aside. The intent assumes a `poverty_gap(dt, line = 3)` function that uses household weights.

I did not open the survey data or run package code.

**Next steps: Done**
* **Your move:** To start implementation, type `/cg Add weighted poverty_gap(dt, line = 3) using the approved intent in .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md`.
* **Project:** The approved intent is ready; package implementation has not started.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md" --reply 'Yes.' --project "<project>"
approved .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md
record: .cg-docs/approvals/2026-11-26-poverty-depth-measure.6934337c8a2ac38e.json
hash: sha256:6934337c8a2ac38e92cd71463ae27506e6452d69f1d202a5fe3a3a298eee43f8
by: <name> <<email>>

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
changed-files: 10
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md



[exit code: 0]

### H1 ask for the plan

> [the text of the installed cg/SKILL.md]

plan Write the plan for the work we settled in the brainstorm.

`/cg` would run this change with checks and a record. I will read the Compound GPID status first, then follow the playbook it selects for the plan.
The selected plan playbook requires a decided intent before it can create a plan. I will check the recorded brainstorms and any unfinished plans, then proceed only from the matching record.
The decided intent sets a narrow contract: add a weighted poverty gap function that returns a fraction and prove the stated `0.25` example. The standard package check also runs existing tests that read the bundled survey, so I will list that already-classified `Public` input in the register; the new arithmetic example itself will use hand-built data.
**Plan:** `.cg-docs/plans/2026-11-26-poverty-gap-index.md`  
**Status:** draft. Validation is measured: `cg.py validate` reports 0 problems and 0 warnings. The tier is elevated because the change computes a number and adds a public function interface. `inst/extdata/survey.csv` is Public and cleared.

**Self-review:** P1 PASS: each requirement has a check and the plan defines a wrong-result test. P3 PASS: the implementation and tests are code-driven. P6 PASS: one slice covers the smallest complete change. P10 PASS: the plan names the unit, weights and population. P12 PASS: the dataset and result classification are recorded. These are self-review findings, not independent verifier results.

**Not checked:** I did not run the R commands or check whether `roxygen2` is installed. The verification profile has no Run or Doctor command.

The plan reads:

```markdown
---
type: plan
schema: 2
title: "Poverty gap index"
date: 2026-11-26
status: draft
intent: .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md
---

# Poverty gap index

The human approves this plan as it reads below. `cg.py approve` records their reply against this text, so a later change is an amendment, a dated line under `## Amendments`, and needs a new approval.

## Contract

### Goal

The package exports `poverty_gap(dt, line = 3)`, which returns the household-weighted average of `max(0, (line - welfare) / line)` as a fraction. On the decided two-household example with line 10, welfare 5 and 10, and equal weights, it returns 0.25.

### Out of scope

Do not add a poor-only mean, other poverty measures, or output formats; those are outside this measure. Do not change `headcount()` or `read_survey()`; they are existing behavior and do not need a change for this addition.

### Requirements

| ID | Requirement |
|---|---|
| R1 | `poverty_gap()` returns the weighted poverty gap index as a fraction, with non-poor households contributing zero. |
| R2 | `poverty_gap()` rejects missing required columns, missing welfare or weights, non-positive weights, an empty survey, and a line that is not a single positive finite number. |

### Checks

Every requirement has a check, and every check can fail.

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `Rscript -e 'roxygen2::roxygenise()' && R CMD check --no-manual .` | The command exits non-zero, or the test for the hand-built example does not report 0.25 (within `testthat::expect_equal()`'s default tolerance). |
| C2 | R2 | `Rscript -e 'roxygen2::roxygenise()' && R CMD check --no-manual .` | The command exits non-zero, or any hand-built invalid-input case is accepted instead of raising an error. |

What no check would catch: behavior on survey populations or poverty lines not represented by the deterministic tests may still be wrong.

### Boundaries

- Always: Keep the change small, add a hand-built arithmetic test, and run the declared package check.
- Ask first: Any change to the chosen measure, fraction scale, scope, check command, or check tolerance.
- Never: Read or print survey rows for this change; change `headcount()` or `read_survey()`; add a poor-only mean, another poverty measure, or an output format.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| `inst/extdata/survey.csv` | Public | Bundled synthetic survey, described in `DESCRIPTION` | Package version 0.0.1 | Gate Kit, package maintainer | Read by the existing package tests during `R CMD check`; do not print or include rows in evidence. |

Shape of the data: `inst/extdata/survey.csv` has one row per household, with `hhid` as its unique key and `welfare` and `weight` as the columns used by the measures. `poverty_gap()` returns a Public numeric fraction derived from the supplied household rows, using `weight` to average normalized shortfalls over all households in the input survey; non-poor households have zero shortfall. The new arithmetic test uses two in-memory household rows with welfare and weight columns and does not read a separate dataset.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | Add and export the documented `poverty_gap()` function, plus hand-built arithmetic and invalid-input tests. | `R/read_survey.R`, `tests/testthat/test-read_survey.R`, `NAMESPACE`, `man/poverty_gap.Rd` | C1, C2 | By code, using `roxygen2::roxygenise()` to generate documentation and namespace, then `R CMD check --no-manual .` to run package checks and tests. |
```

Do you approve this plan? A plain yes records approval under your name. I will treat any other reply as a change or a question.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the plan as written.
* **Project:** The poverty gap plan is drafted and validated; work starts after approval.

> code · gpt-6-luna

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
changed-files: 10
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" status --guide --project "<project>" --playbook plan
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
changed-files: 10
stops: none
next: read playbooks/plan.md
playbook: ~/.agents/skills/cg/playbooks/plan.md

→ Read ~/.agents/skills/cg/playbooks/plan.md
→ Read ~/.agents/skills/cg/grilling.md
✱ Glob ".cg-docs/plans/**/*" in . · 0 matches
✱ Glob "GLOSSARY.md" in . · 1 match
✱ Glob ".cg-docs/brainstorms/**/*" in . · 0 matches
✱ Glob ".cg-docs/verification.md" in . · 0 matches
→ Read .cg-docs
→ Read .cg-docs/brainstorms
→ Read .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md
→ Read GLOSSARY.md
→ Read .cg-docs/verification.md
✱ Glob "R/*.R" in . · 1 match
✱ Glob "tests/testthat/*.R" in . · 1 match
✱ Glob ".cg-docs/plans/*" in . · 0 matches
✱ Glob "DESCRIPTION" in . · 1 match
→ Read NAMESPACE
→ Read DESCRIPTION
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R
✱ Glob "man/*.Rd" in . · 3 matches
→ Read ~/.agents/skills/cg/playbooks/quick.md
✱ Glob "principles/P1*" in ~/.agents/skills/cg · 3 matches
✱ Glob "principles/P3*" in ~/.agents/skills/cg · 0 matches
✱ Glob "principles/P12*" in ~/.agents/skills/cg · 1 match
✱ Glob "principles/P6*" in ~/.agents/skills/cg · 0 matches

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" --help
usage: cg.py [-h] {doctor,status,new,packs,setup,validate,approve,tier} ...

Compound GPID core tooling.

positional arguments:
  {doctor,status,new,packs,setup,validate,approve,tier}
    doctor              check this machine and write the launcher file
    status              print the state of the work in a project
    new                 create an artifact under .cg-docs/
    packs               list the installed packs
    setup               write what the human confirmed in the setup playbook
    validate            check the artifacts under .cg-docs/ against the schema
    approve             record the human's yes to a plan or an intent, or
                        their decision on data
    tier                compute the risk level of a piece of work from
                        declared facts

options:
  -h, --help            show this help message and exit

→ Read ~/.agents/skills/cg/principles
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P12-governed-data.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Read ~/.agents/skills/cg/principles/P01-specify-before-generating.md
✗ Read .cg-docs/plans failed
Error: File not found: <project>/.cg-docs/plans

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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new plan "Poverty gap index" --intent ".cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md" --project "<project>"
created .cg-docs/plans/2026-11-26-poverty-gap-index.md

→ Read .cg-docs/plans/2026-11-26-poverty-gap-index.md
✱ Glob "tests/testthat.R" in . · 1 match
→ Read tests/testthat.R
% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "tests/testthat/test-read_survey.R" --touches "NAMESPACE" --touches "man/poverty_gap.Rd" --reads "inst/extdata/survey.csv" --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 4

→ Read ~/.agents/skills/cg/principles/P10-correct-in-the-domain.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/plans/2026-11-26-poverty-gap-index.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

→ Read .cg-docs/plans/2026-11-26-poverty-gap-index.md
% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/plans/2026-11-26-poverty-gap-index.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/plans/2026-11-26-poverty-gap-index.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

→ Read .cg-docs/plans/2026-11-26-poverty-gap-index.md
% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/plans/2026-11-26-poverty-gap-index.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0



[exit code: 0]

### H2 a yes that goes on

> Yes, but add one line to the Never list first: no file under data-raw/ is changed.

I will add the requested `data-raw/` boundary as a dated amendment, keep the original plan text, and validate the revised plan before asking for approval again.
**Plan:** `.cg-docs/plans/2026-11-26-poverty-gap-index.md`  
**Status:** draft. Validation is measured: 0 problems and 0 warnings. The requested boundary is now in the Never list. The amendment is dated 2026-11-26.

**Amendment:** “Add the boundary that no file under `data-raw/` is changed, as requested by the human.” No other plan text changed.

**Plan**
```markdown
---
type: plan
schema: 2
title: "Poverty gap index"
date: 2026-11-26
status: draft
intent: .cg-docs/brainstorms/2026-11-26-poverty-depth-measure.md
---

# Poverty gap index

The human approves this plan as it reads below. `cg.py approve` records their reply against this text, so a later change is an amendment, a dated line under `## Amendments`, and needs a new approval.

## Contract

### Goal

The package exports `poverty_gap(dt, line = 3)`, which returns the household-weighted average of `max(0, (line - welfare) / line)` as a fraction. On the decided two-household example with line 10, welfare 5 and 10, and equal weights, it returns 0.25.

### Out of scope

Do not add a poor-only mean, other poverty measures, or output formats; those are outside this measure. Do not change `headcount()` or `read_survey()`; they are existing behavior and do not need a change for this addition.

### Requirements

| ID | Requirement |
|---|---|
| R1 | `poverty_gap()` returns the weighted poverty gap index as a fraction, with non-poor households contributing zero. |
| R2 | `poverty_gap()` rejects missing required columns, missing welfare or weights, non-positive weights, an empty survey, and a line that is not a single positive finite number. |

### Checks

Every requirement has a check, and every check can fail.

| ID | Requirement | Command | Fails when |
|---|---|---|---|
| C1 | R1 | `Rscript -e 'roxygen2::roxygenise()' && R CMD check --no-manual .` | The command exits non-zero, or the test for the hand-built example does not report 0.25 (within `testthat::expect_equal()`'s default tolerance). |
| C2 | R2 | `Rscript -e 'roxygen2::roxygenise()' && R CMD check --no-manual .` | The command exits non-zero, or any hand-built invalid-input case is accepted instead of raising an error. |

What no check would catch: behavior on survey populations or poverty lines not represented by the deterministic tests may still be wrong.

### Boundaries

- Always: Keep the change small, add a hand-built arithmetic test, and run the declared package check.
- Ask first: Any change to the chosen measure, fraction scale, scope, check command, or check tolerance.
- Never: Read or print survey rows for this change; change `headcount()` or `read_survey()`; add a poor-only mean, another poverty measure, or an output format.
- Never: Change any file under `data-raw/`.

## Data register

| Dataset | Classification | Source | Version | Owner | Permitted use |
|---|---|---|---|---|---|
| `inst/extdata/survey.csv` | Public | Bundled synthetic survey, described in `DESCRIPTION` | Package version 0.0.1 | Gate Kit, package maintainer | Read by the existing package tests during `R CMD check`; do not print or include rows in evidence. |

Shape of the data: `inst/extdata/survey.csv` has one row per household, with `hhid` as its unique key and `welfare` and `weight` as the columns used by the measures. `poverty_gap()` returns a Public numeric fraction derived from the supplied household rows, using `weight` to average normalized shortfalls over all households in the input survey; non-poor households have zero shortfall. The new arithmetic test uses two in-memory household rows with welfare and weight columns and does not read a separate dataset.

## Slices

| Slice | What it delivers | Files | Checks | By code or by judgement |
|---|---|---|---|---|
| S1 | Add and export the documented `poverty_gap()` function, plus hand-built arithmetic and invalid-input tests. | `R/read_survey.R`, `tests/testthat/test-read_survey.R`, `NAMESPACE`, `man/poverty_gap.Rd` | C1, C2 | By code, using `roxygen2::roxygenise()` to generate documentation and namespace, then `R CMD check --no-manual .` to run package checks and tests. |

## Amendments

- 2026-11-26: Add the boundary that no file under `data-raw/` is changed, as requested by the human.
```

**Self-review:** P1 PASS, P3 PASS, P6 PASS, P10 PASS, P12 PASS. This is a self-review, not an independent verifier result. The data register lists the cleared Public survey read by the package tests. What no check would catch is stated in the plan.

Do you approve the plan as it now reads? A plain yes records approval under your name. I will treat any other reply as a change or a question.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the amended plan.
* **Project:** The poverty gap plan is amended and validated; work starts after approval.

> code · gpt-6-luna

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/plans/2026-11-26-poverty-gap-index.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0



[exit code: 0]

### H3 yes

> Yes.

The amended plan is approved. `cg.py approve` recorded the approval at `.cg-docs/approvals/2026-11-26-poverty-gap-index.a97ab20ccfe4ba87.json`. The plan status is now approved; no implementation work was started.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The poverty gap plan is approved; its first slice is ready for a later work session.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/plans/2026-11-26-poverty-gap-index.md" --reply "Yes" --project "<project>"
approved .cg-docs/plans/2026-11-26-poverty-gap-index.md
record: .cg-docs/approvals/2026-11-26-poverty-gap-index.a97ab20ccfe4ba87.json
hash: sha256:a97ab20ccfe4ba87fe0b3bf73e69c9afa000e3c7b63ab56c9b3b0f872ba95b38
by: <name> <<email>>



[exit code: 0]
