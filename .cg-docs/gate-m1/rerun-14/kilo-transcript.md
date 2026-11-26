### B1 setup

> /cg

I will read the CG launcher and run the project status command.
**Measured:** The project is an R package. It has three `.R` files, one `.Rd` file, one `.csv` file, one `DESCRIPTION`, one `LICENSE`, and one `NAMESPACE`. The `lang-r` pack is installed.

**Proposed setup**
- Packs: `core` and `lang-r`.
- Setting: `lang-r.r-syntax=data.table-collapse`. `DESCRIPTION` lists `data.table` as an import, and `R/read_survey.R` uses `fread()`. The package has no other setting to propose.
- Verification draft: Run command: **not found**. Doctor command: **not found**. The existing tests check that `read_survey()` returns 20 rows with the expected columns and rejects a non-positive weight. I did not run them.
- Data: I found one data file, `inst/extdata/survey.csv`. I did not open it. I need your organization’s classification for this file, the highest classification level this coding agent may read, and the classification levels in order from public to most restricted, if you know them.
- Dry-run preview: setup would create `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.

To approve this setup, reply with a clear **yes** and the data details. You can use this format:

```text
Yes.
inst/extdata/survey.csv=Public
Coding agent may read up to=Public
Classification levels=Public;Internal;Restricted
```

Replace the example levels with your organization’s terms. If you do not know an answer, write `unknown`. Setup will not write files until you confirm.

**Next steps: Waiting on you**
* **Your move:** Reply with `Yes` and the data details in the format above.
* **Project:** Setup is not written; the project remains in the `setup` phase.

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

→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read NAMESPACE
→ Read DESCRIPTION
→ Read R/read_survey.R
→ Read tests/testthat.R
→ Read tests/testthat/test-read_survey.R
→ Read ~/.agents/skills/cg/templates/verification.md
✱ Glob "{Makefile,_targets.R,renv.lock,*.Rproj,.Rbuildignore}" in . · 0 matches
✱ Glob "{AGENTS.md,CLAUDE.md,GLOSSARY.md,.cg-docs/**,compound-gpid*}" in . · 0 matches

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

✱ Grep "setting|r-syntax" in ~/.agents/skills/cg · 11 matches

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --project "<project>" --dry-run
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore



[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I will write the confirmed setup, then check the project status. The classification order was not provided, so I will leave it unset.
**Measured:** Setup is complete. Status shows `phase: ready`, `stops: none`, and no missing packs.

The project has three R files, one Rd file, and one CSV file. The package function `read_survey()` reads the survey. Existing tests check its row count, column names, and handling of a non-positive weight. I did not run the tests.

Setup records `lang-r.r-syntax=data.table-collapse`, `inst/extdata/survey.csv=Public`, and `Kilo Code=Public`. The classification order remains unset.

Created or updated: `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. The verification profile is still a draft. Its Run and Doctor commands are `not found`.

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

I’ll check the project’s GPID status and package guidance, then add `headcount()` and a focused test. `/cg` would run this change with checks and a record.
The risk check is elevated because `headcount()` calculates a number and adds a package function to the public interface. The survey file is cleared as Public.

**Contract:** Add `headcount(dt, line = 3)` to `R/read_survey.R`, with a testthat check that the toy survey returns `0.153846`. I will leave other measures and files unchanged. I will run the focused test and the package test suite; a failure to return the expected share or a failing test means the change is not verified.

Reply **yes** to approve this contract.

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
→ Read ~/.agents/skills/cg/principles/README.md
→ Read .cg-docs/config.json
✱ Glob "**/*" in . · 13 matches

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

✱ Glob "**/GLOSSARY.md" in . · 0 matches
→ Read AGENTS.md
→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read DESCRIPTION
→ Read .cg-docs/verification.md
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

I’ll implement the weighted share as total survey weight below the line divided by total survey weight. I’ll use the toy survey’s expected value as the independent check and keep the change to the function and its test.
The package does not import `collapse`, so I will avoid adding a dependency. I’ll compute the weighted share directly from the welfare and weight columns, with explicit input checks to prevent missing values or invalid weights from silently changing the result.
The new test fails before implementation because `headcount()` is not defined. I’ll now add the exported function with documented arguments and return value, then generate the package namespace and help file.
The first post-change test shows the computed share is `0.1538462`; the contract gives `0.153846` to six decimal places. I’ll compare at that stated precision, then rerun the focused and full test suites.
Implemented and exported `headcount(dt, line = 3)`. It returns the share of total survey weight for households with `welfare < line`; it checks required columns, numeric welfare and weights, and positive, complete weights.

- The toy survey returns `0.1538461538`, which rounds to the expected `0.153846`.
- Focused and full testthat suites passed.
- `git diff --check` passed.
- The Compound GPID work report is validated at `.cg-docs/work-reports/2026-11-26-add-weighted-headcount.md`.
- `R CMD check` was not run. Pre-existing untracked files were left unchanged.

Self-review: P3, P4, and P6 passed.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The weighted headcount function and test are complete; the work report is validated.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Skill "r-datatable"
→ Skill "r-analytical"
→ Skill "r-technical"
→ Skill "r-testing"
→ Skill "r-collapse"
→ Read ~/.agents/skills/r-analytical/workflows/welfare-patterns.md
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

% Patch 1 file

$ Rscript -e 'roxygen2::roxygenise()'
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

→ Read NAMESPACE
% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "tests/testthat/test-read_survey.R" --touches "NAMESPACE" --touches "man/headcount.Rd" --reads "inst/extdata/survey.csv" --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 4

$ git status --short && git diff --check && git diff
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
index bcde534..b0d2945 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,28 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Weighted household headcount below a welfare line
+#'
+#' @param dt A data frame or data.table with `welfare` and `weight` columns.
+#' @param line Poverty line. Households with welfare strictly below this value
+#'   are counted as poor.
+#' @return The weighted share of households with welfare below `line`.
+#' @export
+headcount <- function(dt, line = 3) {
+  needed <- c("welfare", "weight")
+  missing_cols <- setdiff(needed, names(dt))
+  if (length(missing_cols) > 0) {
+    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
+  }
+  if (!is.numeric(dt$welfare) || anyNA(dt$welfare)) {
+    stop("welfare must be numeric and present for every household")
+  }
+  if (!is.numeric(dt$weight) || anyNA(dt$weight) || any(dt$weight <= 0)) {
+    stop("weight must be numeric, present, and positive for every household")
+  }
+  if (!is.numeric(line) || length(line) != 1 || is.na(line) || !is.finite(line)) {
+    stop("line must be a single finite number")
+  }
+  return(sum((dt$welfare < line) * dt$weight) / sum(dt$weight))
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

$ Rscript -e 'devtools::test(filter = "read_survey")'
Threading set to: 12 cores
ℹ Testing toypov
FAILURE: 'test-read_survey.R:15:3' ----------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

% Patch 1 file
→ Read man/headcount.Rd

$ git diff --check
(no output)

$ Rscript -e 'devtools::test(filter = "read_survey")'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report --help
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
created .cg-docs/work-reports/2026-11-26-add-weighted-headcount.md

→ Read .cg-docs/work-reports/2026-11-26-add-weighted-headcount.md

$ Rscript -e 'devtools::load_all(); print(headcount(read_survey()), digits = 10)'
Threading set to: 12 cores
ℹ Loading toypov
[1] 0.1538461538

$ git rev-parse --short HEAD && git hash-object man/headcount.Rd && git status --short
2f5c7b2
ac8d89804df0680f8922d566d2e268e7a7a5d0a8
 M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-headcount.md" --project "<project>" && git diff --check && git status --short
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0
 M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I will check the project work status, then find the survey data interface and add the function in its established style.
The package already has `read_survey()` and a separate weighted poverty-rate function. I will add `n_households()`, which returns the survey row count and reads the bundled survey by default. Existing uncommitted edits are present; I will leave them intact.
`n_households()` now returns the number of rows in a survey. It uses the bundled survey by default and accepts a survey data frame or data.table as input.

The package tests pass: 6 passed, with no failures or warnings. Roxygen generated `man/n_households.Rd`; it skipped `NAMESPACE` because that file is not managed by roxygen2.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** Added and tested the household-count function. Existing uncommitted changes remain untouched.

> code · gpt-6-luna

$ ls -a
.
..
.Rbuildignore
.cg-docs
.git
AGENTS.md
CLAUDE.md
DESCRIPTION
LICENSE
NAMESPACE
R
inst
man
tests

$ ls ~/.cg ~/.config/kilo
~/.cg:
installed.json
launcher.json

~/.config/kilo:
AGENTS.md
awesome-copilot
github-mcp-token
kilo.jsonc
kilo.jsonc.clickup-skills-backup-34389cd4bae9
kilo.jsonc.clickup-skills-backup-89d408ac33b3
kilo.jsonc.clickup-skills-backup-ad8e36fe491d
kilo.jsonc.clickup-skills-backup-dd38ea4875d7
kilo.jsonc.pr26-readiness-backup-20261104
node_modules
package-lock.json
package.json
skills

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
[•] Inspect package conventions and survey data structure
[ ] Implement household-count function and documentation/tests
[ ] Run relevant package checks

→ Read DESCRIPTION
✱ Glob "tests/testthat/*" 1 match
✱ Glob "R/*" 1 match
✱ Glob "GLOSSARY.md" 0 matches

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
→ Read tests/testthat/test-read_survey.R

$ git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..b0d2945 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,28 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Weighted household headcount below a welfare line
+#'
+#' @param dt A data frame or data.table with `welfare` and `weight` columns.
+#' @param line Poverty line. Households with welfare strictly below this value
+#'   are counted as poor.
+#' @return The weighted share of households with welfare below `line`.
+#' @export
+headcount <- function(dt, line = 3) {
+  needed <- c("welfare", "weight")
+  missing_cols <- setdiff(needed, names(dt))
+  if (length(missing_cols) > 0) {
+    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
+  }
+  if (!is.numeric(dt$welfare) || anyNA(dt$welfare)) {
+    stop("welfare must be numeric and present for every household")
+  }
+  if (!is.numeric(dt$weight) || anyNA(dt$weight) || any(dt$weight <= 0)) {
+    stop("weight must be numeric, present, and positive for every household")
+  }
+  if (!is.numeric(line) || length(line) != 1 || is.na(line) || !is.finite(line)) {
+    stop("line must be a single finite number")
+  }
+  return(sum((dt$welfare < line) * dt$weight) / sum(dt$weight))
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

→ Read .cg-docs/config.json
→ Read man/headcount.Rd
✱ Glob "man/*.Rd" 2 matches
→ Skill "r-shared"
→ Skill "r-datatable"
→ Skill "r-collapse"
→ Skill "r-testing"
→ Skill "r-technical"

# Todos
[✓] Inspect package conventions and survey data structure
[•] Implement household-count function and documentation/tests
[ ] Run relevant package checks

% Patch 3 files

# Todos
[✓] Inspect package conventions and survey data structure
[✓] Implement household-count function and documentation/tests
[•] Run relevant package checks

$ Rscript -e 'roxygen2::roxygenise(); testthat::test_local()'
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'n_households.Rd'
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 6 ]

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

$ git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE man/n_households.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..4f7e16f 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,4 @@
 export(read_survey)
+export(n_households)
+export(headcount)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..e0073bf 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,40 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Count households in a survey
+#'
+#' @param dt A data frame or data.table with one row per household. Defaults to
+#'   the synthetic survey shipped with the package.
+#' @return The number of households in the survey.
+#' @export
+#' @examples
+#' n_households()
+n_households <- function(dt = read_survey()) {
+  return(nrow(dt))
+}
+
+#' Weighted household headcount below a welfare line
+#'
+#' @param dt A data frame or data.table with `welfare` and `weight` columns.
+#' @param line Poverty line. Households with welfare strictly below this value
+#'   are counted as poor.
+#' @return The weighted share of households with welfare below `line`.
+#' @export
+headcount <- function(dt, line = 3) {
+  needed <- c("welfare", "weight")
+  missing_cols <- setdiff(needed, names(dt))
+  if (length(missing_cols) > 0) {
+    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
+  }
+  if (!is.numeric(dt$welfare) || anyNA(dt$welfare)) {
+    stop("welfare must be numeric and present for every household")
+  }
+  if (!is.numeric(dt$weight) || anyNA(dt$weight) || any(dt$weight <= 0)) {
+    stop("weight must be numeric, present, and positive for every household")
+  }
+  if (!is.numeric(line) || length(line) != 1 || is.na(line) || !is.finite(line)) {
+    stop("line must be a single finite number")
+  }
+  return(sum((dt$welfare < line) * dt$weight) / sum(dt$weight))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..d9d558a 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -9,3 +9,14 @@ test_that("read_survey() refuses a non-positive weight", {
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("n_households() counts survey rows", {
+  dt <- read_survey()
+  expect_equal(n_households(dt), 20L)
+  expect_equal(n_households(), 20L)
+})
+
+test_that("headcount() returns the weighted share below the line", {
+  dt <- read_survey()
+  expect_equal(round(headcount(dt), 6), 0.153846)
+})

# Todos
[✓] Inspect package conventions and survey data structure
[✓] Implement household-count function and documentation/tests
[✓] Run relevant package checks



[exit code: 0]

### G1 idea

> /cg brainstorm I want the package to say how far below the line the poor households are, and not only how many of them there are. I am not sure which measure to use. Think it through with me before anything is built.

I will read the Compound GPID state first, then follow its brainstorm playbook.
The package currently has only a weighted headcount share, and its poverty rule is welfare strictly below the line. I will record that scope and the measure choice in the brainstorm intent before I ask you to choose.
**Measured (E2):** `headcount()` returns the weighted share of households with welfare below the poverty line. It does not measure how far below the line they are. The current test checks only that share.

**Measured (E2):** The World Bank calls one common measure the *poverty gap*: the average shortfall from the line across all households, with nonpoor households counted as zero. It expresses the result as a share of the line. This measure reflects both how many households are poor and how far below the line they are. [World Bank indicator metadata](https://api.worldbank.org/v2/indicator/SI.POV.GAP2?format=json)

**Inferred (E3):** You want a measure of the size of the shortfalls, not another count of poor households. The choice still open is whether to average those shortfalls across all households or only across poor households.

1. Should the package report the poverty gap across **all households**, with nonpoor households counted as zero? I recommend this standard measure. It reflects both poverty incidence and depth, but it is lower than the average shortfall among poor households.
2. Or should it report the **average shortfall among poor households only**? This answers more directly how far poor households fall below the line, but it does not show how common poverty is and needs a rule for when no households are poor.

The intent is recorded at `.cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md`, status `draft`. No code or data was run or changed. **Assumption:** the existing welfare, weight, and poverty-line inputs remain the basis for this measure. If not, the scope changes.

Which measure do you choose? You can also state a different measure.

**Next steps: Waiting on you**
* **Your move:** choose option 1, option 2, or name another measure.
* **Project:** The measure choice is open; no implementation has started.

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
→ Read ~/.agents/skills/cg/grilling.md
✱ Glob "GLOSSARY.md" 0 matches
✱ Glob "README*" 0 matches
✱ Glob "R/**/*" 1 match
✱ Glob "**/*pover*" 0 matches
✱ Glob ".cg-docs/**/*" 0 matches
✱ Glob "man/**/*" 3 matches
→ Read .
→ Read .cg-docs
→ Read ~/.agents/skills/cg/principles/P11-shared-language.md
→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P07-honest-claims.md
→ Read ~/.agents/skills/cg/principles/P02-human-decides.md
→ Read DESCRIPTION
→ Read man/headcount.Rd
→ Read R/read_survey.R
→ Read man/n_households.Rd
→ Read .cg-docs/verification.md
✱ Glob ".cg-docs/brainstorms/**/*" 0 matches
→ Read R
→ Read .cg-docs/work-reports
→ Read tests/testthat
% WebFetch https://www.worldbank.org/en/topic/poverty/brief/global-poverty-lines-faq

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new intent "Measure poverty depth" --project "<project>"
created .cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md

→ Read .cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md
→ Read tests/testthat/test-read_survey.R
→ Read .cg-docs/work-reports/2026-11-26-add-weighted-headcount.md
✱ Grep "poverty gap|headcount ratio|FGT|Foster|Greer|Thorbecke" in . · 0 matches
% WebFetch https://databank.worldbank.org/metadataglossary/world-development-indicators/series/SI.POV.GAP2
% WebFetch https://www.worldbank.org/en/topic/poverty/brief/global-poverty-lines
% WebFetch https://api.worldbank.org/v2/indicator/SI.POV.GAP2?format=json
% Patch 1 file


[exit code: 0]

### G2 answer

> Yes to each question: I take the answer you recommend. Keep it as small as you can.

Your reply selects the recommended poverty gap index and asks for the smallest change. I will record that choice, then check whether the narrow implementation scope matches what you want before asking for approval of the full intent.
**Intent:** `.cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md`, status `draft`. Validation passed with **0 problems and 0 warnings**.

**Measured (E2):** The package has a weighted headcount measure. It counts households below the line but does not measure their shortfalls.

**Inferred (E3):** The goal is to add a small measure of how far welfare falls below the poverty line, while keeping the existing headcount measure.

**Goal:** Add one small package measure of how far poor households fall below the line, for package users working with a survey and poverty line.

**Out of scope:** Do not change the existing headcount measure. Do not add household-level gaps or extra summaries.

**A wrong result:** An output that only counts poor households, averages shortfalls only among poor households, or does not weight and normalize shortfalls as the poverty gap index does. A test with known welfare values, weights, and line can distinguish these results.

**Decisions**
- **D1, measure:** You answered, “Yes to each question: I take the answer you recommend. Keep it as small as you can.” The intent records the weighted poverty gap index: normalized shortfalls averaged across all households, with nonpoor households counted as zero. The trade-off is that this reflects both poverty depth and incidence, but is lower than the average shortfall among poor households alone.
- **D2, scope:** You answered, “Keep it as small as you can.” The intent records one additional measure and no extra summaries. The trade-off is that it will not provide household-level shortfalls.

**Approaches set aside:** The intent sets aside the average shortfall among poor households only, which hides how common poverty is, and household-level gap values, which add output beyond the requested summary.

**Assumption:** The existing welfare, weight, and line inputs are suitable for this measure. If they are not, the input contract must change.

**Not checked:** I did not open the survey data or run package code. The measure and scope are not implemented.

Is this intent what you want? A plain **“Yes”** will record approval under your name. Any correction will keep the intent open.

**Next steps: Waiting on you**
* **Your move:** Reply **“Yes”** to approve this intent, or state the correction.
* **Project:** The poverty-gap measure is selected and scoped in a validated draft intent; implementation has not started.

> code · gpt-6-luna

% Patch 1 file
% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0



[exit code: 0]

### G3 vague reply

> Sounds good.

“Sounds good” does not record approval. The intent remains open. What would you change, or what is still unclear?

**Next steps: Waiting on you**
* **Your move:** Reply **“Yes”** to approve the intent, or state what you want changed.
* **Project:** The validated draft intent is ready for approval; implementation has not started.

> code · gpt-6-luna



[exit code: 0]

### G4 answer

> Yes, that is what I want.

The brainstorm is complete. The approved intent is `.cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md`, status `decided`. The approval record is `.cg-docs/approvals/2026-11-26-measure-poverty-depth.0744282aebf19266.json`.

**Inferred (E3):** The goal is to add one small poverty measure that shows the weighted shortfall from the poverty line, while keeping the existing headcount measure unchanged.

**Decisions**
- Use the weighted poverty gap index: normalize each household's shortfall by the poverty line, then average across all households, counting nonpoor households as zero.
- Add only this measure. Do not add household-level gaps or other summaries.

**Assumption:** The existing welfare, weight, and poverty-line inputs are suitable. If they are not, the input contract will need to change.

**Approaches set aside:** The average shortfall among poor households only, because it does not reflect how common poverty is; household-level shortfalls, because they add more output than requested.

**Measured (E2):** The intent passed validation with zero problems and warnings. No code or survey data was run or changed. No further experiment or outside answer is pending.

**Next steps: Done**
* **Your move:** Nothing. To start implementation later, type `/cg add the approved weighted poverty gap index as one small function; keep headcount unchanged`.
* **Project:** The poverty-gap measure is approved and recorded; implementation has not started.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" approve ".cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md" --reply "Yes, that is what I want." --project "<project>"
approved .cg-docs/brainstorms/2026-11-26-measure-poverty-depth.md
record: .cg-docs/approvals/2026-11-26-measure-poverty-depth.0744282aebf19266.json
hash: sha256:0744282aebf1926676dbbd94aed45435939b34025ee8724c86d93f572c96e704
by: <name> <<email>>



[exit code: 0]
