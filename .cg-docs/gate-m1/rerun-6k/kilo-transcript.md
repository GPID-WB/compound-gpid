### B1 setup

> /cg

The project is in setup. I will inspect its tracked and untracked file names, installed packs, and existing build/check instructions. I will not open data files or write anything before you confirm the setup proposal.
**Recommended setup:** add the `core` and `lang-r` packs. Both are installed.

The project has 8 files: 3 `.R`, 1 `.Rd`, 1 `.csv`, and 3 files with no extension. It is an R package. Its code uses `data.table::fread()` in `R/read_survey.R`, so I recommend the `lang-r.r-syntax=data.table-collapse` setting. This matches the pack’s default.

The package includes `tests/testthat/test-read_survey.R`. It checks the returned data’s row count and column names, and checks that a non-positive weight causes an error. The installed R testing guide lists `devtools::test()` as a way to run the full test suite. The project itself does not declare a Run command or a Doctor command, so both are **not found**. I did not run any checks.

There is 1 data file: `inst/extdata/survey.csv`. I did not open it. The package description says the survey data are synthetic, but only you can set its classification and the access level for Kilo.

The setup preview lists these files to create: `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.

Please confirm the proposed packs and setting. In the same reply, give the data and access rules. You can copy and fill in this example:

```text
Yes. Classifications: inst/extdata/survey.csv=Public.
Kilo may read up to: Public.
Classification levels, from public to most restricted: Public; ...
```

If the data file is not `Public`, replace that value with your organization’s classification. If you do not know an item, leave it unstated; it will stay open. I will make no changes until you confirm.

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

→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/playbooks/setup.md
→ Read ~/.agents/skills/cg/GLOSSARY.md
✱ Glob "**/*" in . · 8 matches
✱ Glob "**/GLOSSARY.md" in . · 0 matches
✱ Glob "**/AGENTS.md" in . · 0 matches

$ git ls-files --cached --others --exclude-standard
DESCRIPTION
LICENSE
NAMESPACE
R/read_survey.R
inst/extdata/survey.csv
man/read_survey.Rd
tests/testthat.R
tests/testthat/test-read_survey.R

$ git status --short --branch
## main

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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" -c 'from collections import Counter; from pathlib import Path; import subprocess; names=subprocess.check_output(["git","ls-files","--cached","--others","--exclude-standard"], text=True).splitlines(); print(Counter(Path(n).suffix or "[no extension]" for n in names))'
Counter({'[no extension]': 3, '.R': 3, '.csv': 1, '.Rd': 1})

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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs core,lang-r --dry-run --project "<project>"
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore

→ Read ~/.agents/skills/r-technical/SKILL.md
→ Read ~/.agents/skills/r-testing/SKILL.md


[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Your reply confirms the packs, the R setting, the CSV classification, and that Kilo may read Public data. I will write that setup now. The verification profile will stay in draft because the project has no declared Run or Doctor command.
Setup is complete. Status shows `phase: ready`, `stops: none`, both expected packs present, `lang-r.r-syntax=data.table-collapse`, and `inst/extdata/survey.csv=Public`.

Created `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. The verification profile remains a draft: no Run or Doctor command is declared by the project. I did not run package checks or open the survey CSV.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo=Public" --project "<project>"
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

I will check the Compound GPID work state and package guidance, then add `headcount()` and a test for the toy survey.
`/cg` would run this change with checks and a record. I will load its guide before editing, as requested by the project workflow.
The requested function will produce a welfare statistic, so the guide marks this as a hard stop under its numerical-output rule. I will confirm the affected code and test paths, then state the bounded change and checks for your approval.
The guide requires approval because `headcount()` will calculate and return a welfare statistic. The survey is marked `Public` in project status, so data access is cleared. The package already checks that welfare and weights are present and positive.

**Change contract**
- **Goal:** Add and export `headcount(dt, line = 3)`, which returns the weighted share of households with welfare below `line`, and test that the toy survey returns `0.153846`.
- **Out of scope:** Changes to the survey data, other poverty measures, and dependencies.
- **Checks:** Run the focused `testthat` test and package tests. A failure to return the expected value or a failed package test means the change is not verified.
- **Risk review:** The numerical-output rule is **yes**, so I stopped before editing. Data access, personal data or credentials, irreversible actions, interface changes, and scope beyond five files or an unresolved design choice are **no**.

Reply with a clear yes to approve this contract.

> code · gpt-6-luna

# Todos
[•] Check Compound GPID status and repository instructions
[ ] Inspect survey helpers and toy test data
[ ] Implement headcount and add testthat coverage
[ ] Run the relevant tests

$ ls -la ~/.cg <project>
~/.cg:
total 16
drwxr-xr-x    4 <user>  staff   128 Nov 25 14:11 .
drwx------+ 121 <user>  staff  3872 Nov 25 14:19 ..
-rw-------    1 <user>  staff  1558 Nov 25 14:11 installed.json
-rw-------    1 <user>  staff   150 Nov 25 09:36 launcher.json

<project>:
total 48
drwxr-xr-x  14 <user>  staff  448 Nov 25 14:28 .
drwxr-xr-x   5 <user>  staff  160 Nov 25 14:27 ..
-rw-------   1 <user>  staff   38 Nov 25 14:28 .Rbuildignore
drwxr-xr-x   4 <user>  staff  128 Nov 25 14:28 .cg-docs
drwxr-xr-x  13 <user>  staff  416 Nov 25 14:28 .git
-rw-------   1 <user>  staff  932 Nov 25 14:28 AGENTS.md
-rw-------   1 <user>  staff   11 Nov 25 14:28 CLAUDE.md
-rw-r--r--   1 <user>  staff  560 Nov 25 14:26 DESCRIPTION
-rw-r--r--   1 <user>  staff   44 Nov 25 00:08 LICENSE
-rw-r--r--   1 <user>  staff   50 Nov 25 00:08 NAMESPACE
drwxr-xr-x   3 <user>  staff   96 Nov 25 00:08 R
drwxr-xr-x   3 <user>  staff   96 Nov 25 00:08 inst
drwxr-xr-x   3 <user>  staff   96 Nov 25 14:10 man
drwxr-xr-x   4 <user>  staff  128 Nov 25 00:08 tests

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
changed-files: 4
stops: none
next: the human types /cg to run the work through the guide

→ Skill "cg"

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
✱ Glob "**/*" in R · 1 match
✱ Glob "**/*" in tests · 2 matches
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R
→ Read DESCRIPTION

# Todos
[✓] Check Compound GPID status and repository instructions
[✓] Inspect survey helpers and toy test data
[ ] Implement headcount and add testthat coverage
[ ] Run the relevant tests



[exit code: 0]

### C2 yes

> Yes, proceed.

I will add the weighted-share function and its test. I will run the same focused test before and after the change to check that it detects the missing function and then passes.
The toy survey has one row per household and includes `welfare` and `weight`. I will define the share as the sum of weights where `welfare < line`, divided by total weight. The user-provided expected value, `0.153846`, will serve as the independent reference.
The focused test now fails for the expected reason: `headcount()` is not defined. I will add the function with checks for required columns and valid welfare and weights, then generate its package documentation.
The implementation returns the expected share to six decimal places. The first test run failed because the test’s tolerance was too strict for the rounded reference value. I will set the tolerance to match the six-decimal reference, then rerun both test commands.
Added and exported `headcount(dt, line = 3)`. The function returns the weighted share of households with welfare below the threshold and checks required columns, welfare, weights, and the threshold. Added a test for the toy survey and generated its help page.

- **Measured:** The toy survey result is `0.153846153846`, which matches the expected `0.153846` to six decimal places.
- **Verified:** The focused test and full testthat suite pass. The focused test failed before implementation because `headcount()` was missing.
- **Verified:** `git diff --check` passes.
- **Not checked:** `R CMD check` and a separate software cross-check.
- **Compound GPID:** Work report is `.cg-docs/work-reports/2026-11-25-weighted-household-headcount.md`. Project status shows no active work or open artifacts.

The pre-existing untracked setup files were left unchanged.

> code · gpt-6-luna

# Todos
[•] Implement headcount and add testthat coverage
[ ] Run the focused test before and after the change, then run package tests
[ ] Create and complete the Compound GPID work report

→ Read ~/.agents/skills/cg/principles/README.md
→ Read NAMESPACE
→ Read inst/extdata/survey.csv
✱ Glob "P0{3,4,6}-*.md" in ~/.agents/skills/cg/principles · 3 matches

$ git status --short && git diff -- R tests man NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md

→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
✱ Glob "man/*" in . · 1 match
% Patch 1 file

$ Rscript -e 'testthat::test_file("tests/testthat/test-read_survey.R")'
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

→ Read man/read_survey.Rd

$ Rscript -e 'testthat::test_local(".", filter = "read_survey")'
Threading set to: 12 cores
ERROR: 'test-read_survey.R:15:3' ------------------
Error in `headcount(dt)`: could not find function "headcount"
Backtrace:
    ▆
 1. └─testthat::expect_equal(headcount(dt), 0.153846, tolerance = 0.000001) at test-read_survey.R:15:3
 2.   └─testthat::quasi_label(enquo(object), label)
 3.     └─rlang::eval_bare(expr, quo_get_env(quo))

[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]
Error:
! Test failures.
Execution halted

% Patch 1 file

$ Rscript -e 'roxygen2::roxygenise()'
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

% Patch 1 file

# Todos
[✓] Implement headcount and add testthat coverage
[•] Run the focused test before and after the change, then run package tests
[ ] Create and complete the Compound GPID work report

$ git diff --check
(no output)

$ Rscript -e 'pkgload::load_all(".", quiet = TRUE); cat(sprintf("headcount = %.6f\n", headcount(read_survey())))'
Threading set to: 12 cores
headcount = 0.153846

$ Rscript -e 'testthat::test_local(".", filter = "read_survey")'
Threading set to: 12 cores
FAILURE: 'test-read_survey.R:15:3' ----------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]
Error:
! Test failures.
Execution halted

$ Rscript -e 'testthat::test_local(".")'
Threading set to: 12 cores
FAILURE: 'test-read_survey.R:15:3' ----------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]
Error:
! Test failures.
Execution halted

$ Rscript -e 'testthat::expect_equal(0.153846153846, 0.153846, tolerance = 1e-6)'
Threading set to: 12 cores

→ Read tests/testthat/test-read_survey.R
% Patch 1 file

$ git diff --check
(no output)

$ Rscript -e 'testthat::test_local(".", filter = "read_survey")'
Threading set to: 12 cores
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ Rscript -e 'testthat::test_local(".")'
Threading set to: 12 cores
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

# Todos
[✓] Implement headcount and add testthat coverage
[✓] Run the focused test before and after the change, then run package tests
[•] Create and complete the Compound GPID work report

$ git status --short && git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE man/headcount.Rd
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..ad5a7d7 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,28 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Calculate the weighted household headcount
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line Welfare threshold. Households below this value are counted.
+#' @return The weighted share of households with welfare below `line`.
+#' @export
+headcount <- function(dt, line = 3) {
+  needed <- c("welfare", "weight")
+  missing_cols <- setdiff(needed, names(dt))
+  if (length(missing_cols) > 0) {
+    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
+  }
+  if (anyNA(dt$welfare) || any(dt$welfare <= 0)) {
+    stop("welfare must be present and positive for every household")
+  }
+  if (anyNA(dt$weight) || any(dt$weight <= 0)) {
+    stop("weight must be present and positive for every household")
+  }
+  if (length(line) != 1 || !is.numeric(line) || is.na(line) || !is.finite(line)) {
+    stop("line must be one finite number")
+  }
+
+  return(sum(dt$weight[dt$welfare < line]) / sum(dt$weight))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..e771fe5 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -9,3 +9,8 @@ test_that("read_survey() refuses a non-positive weight", {
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("headcount() returns the weighted share below the line", {
+  dt <- read_survey()
+  expect_equal(headcount(dt), 0.153846, tolerance = 1e-5)
+})

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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report "Weighted household headcount" --project "<project>"
created .cg-docs/work-reports/2026-11-25-weighted-household-headcount.md

→ Read .cg-docs/work-reports/2026-11-25-weighted-household-headcount.md

$ git rev-parse --short HEAD && git hash-object man/headcount.Rd
3045e85
3182e2803a63b11f73cd5e6e6073fdfaf3041bb1

$ git diff --stat -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE && git diff --check
NAMESPACE                         |  1 +
 R/read_survey.R                   | 25 +++++++++++++++++++++++++
 tests/testthat/test-read_survey.R |  5 +++++
 3 files changed, 31 insertions(+)

$ Rscript -e 'pkgload::load_all(".", quiet = TRUE); cat(sprintf("%.12f\n", headcount(read_survey())))'
Threading set to: 12 cores
0.153846153846

% Patch 1 file
→ Read man/headcount.Rd

$ git status --short && git diff --check
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
git: repository
branch: main
changed-files: 8
stops: none
next: the human types /cg to run the work through the guide

# Todos
[✓] Implement headcount and add testthat coverage
[✓] Run the focused test before and after the change, then run package tests
[✓] Create and complete the Compound GPID work report



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I will first check the project status, glossary, and existing survey functions so the new function fits the package.
The package reader returns one row per household, and the existing uncommitted changes already add `headcount()`. I will add a separate exported `number_households()` function that counts those rows, with a test using the supplied survey.
Added exported `number_households(dt)` in `R/read_survey.R`. It returns the number of rows, since the survey has one row per household. Added a test that checks the supplied survey returns 20.

All package tests pass: 5 passed, 0 failed.

> code · gpt-6-luna

# Todos
[•] Check Compound GPID status and project conventions
[ ] Find survey data model and implement household count function
[ ] Run focused checks for the function

$ ls ~/.cg/launcher.json <project>
~/.cg/launcher.json

<project>:
AGENTS.md
CLAUDE.md
DESCRIPTION
LICENSE
NAMESPACE
R
inst
man
tests

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

$ git status --short
M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

# Todos
[✓] Check Compound GPID status and project conventions
[•] Find survey data model and implement household count function
[ ] Run focused checks for the function

✱ Glob "R/*.R" 1 match
→ Read R/read_survey.R
→ Read DESCRIPTION
→ Read tests/testthat/test-read_survey.R
✱ Glob "man/*.Rd" 2 matches
% Patch 1 file
% Patch 1 file

# Todos
[✓] Check Compound GPID status and project conventions
[✓] Find survey data model and implement household count function
[•] Run focused checks for the function

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 5 ]

# Todos
[✓] Check Compound GPID status and project conventions
[✓] Find survey data model and implement household count function
[✓] Run focused checks for the function



[exit code: 0]
