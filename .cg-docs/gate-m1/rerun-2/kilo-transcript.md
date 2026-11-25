### B1 setup

> /cg

The project is in setup. Status reports `phase: setup`, `stops: none`, and `waiting-on-human: none`.

**Proposal**
- **Packs:** `core` and `lang-r`. Both are installed.
- **R setting:** `lang-r.r-syntax=data.table-collapse`, the default. `DESCRIPTION` imports `data.table`, and `R/read_survey.R` uses `fread()`.
- **Verification profile draft:** Run command: not found. Doctor command: not found. The package has `tests/testthat/`, but no project command or pipeline identifies how to run it. The documented output is the `read_survey()` function in `R/read_survey.R`; its correctness has no independent reference value yet.
- **Data rules:** `inst/extdata/survey.csv` is the only data file. `DESCRIPTION` says it contains synthetic data, but I will treat its classification as unknown until you state it. I did not open it.
- **Files to write after confirmation:** `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, and `CLAUDE.md`.

Assumptions: the coding agent is named **Kilo Code**. No classification levels or data access approvals are set yet.

Please confirm or correct the proposal. Include the classification for `inst/extdata/survey.csv`, the highest classification Kilo Code may read, and your organization’s classification levels if you know them. For example: `Yes. survey.csv=Public; Kilo Code may read=Public; levels=Public; Internal; Confidential.`

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
✱ Glob "**/*" in . · 7 matches

$ git ls-files --cached --others --exclude-standard
DESCRIPTION
LICENSE
NAMESPACE
R/read_survey.R
inst/extdata/survey.csv
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
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/GLOSSARY.md
→ Read DESCRIPTION
→ Read ~/.agents/skills/cg/principles/P02-human-decides.md
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R
→ Read .
→ Read ~/.agents/skills/cg/templates/verification.md


[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

Setup is complete. Status reports `phase: ready` and `stops: none`.

The project has 5 R-related files and one data file: `inst/extdata/survey.csv`. `DESCRIPTION` identifies the survey as synthetic. The setup records its classification as `Public` and permits Kilo Code to read Public data.

The setup wrote `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. Status reports `settings: lang-r.r-syntax=data.table-collapse` and `packs-missing: none`.

The verification profile is still a draft. A Run command, a Doctor command, and an independent reference for the output were not found. No project checks were run.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo Code=Public" --project "<project>"
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

I will first check the Compound GPID work state and project instructions, then implement the function and test.
This change adds a statistical measure, so the playbook requires a hard stop. Status clears the survey file as `Public`, but rule 1 still applies because the function creates a number. The goal is to add `headcount()` and a test for the expected `0.153846`; I will not change the survey, dependencies, or unrelated code. I will check the calculation and test it after approval.
This change computes a statistical measure, so Compound GPID requires your approval before I edit code. The goal is to add `headcount(dt, line = 3)` and a `testthat` check for the expected toy-survey value `0.153846`. I will leave the data and dependencies unchanged. I will run the package tests; a failure or a result that differs from your expected value will mean the check fails.

Reply **yes** to approve.

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
[•] Inspect project files and identify the headcount inputs and test pattern
[ ] Implement headcount() and add a testthat check
[ ] Run checks, self-review, and create the Compound GPID work report

✱ Glob "**/*" 12 matches
→ Read R/read_survey.R
→ Read DESCRIPTION
→ Read .cg-docs/config.json
→ Read .cg-docs/verification.md
→ Read tests/testthat/test-read_survey.R

$ git status --short
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md



[exit code: 0]

### C2 yes

> Yes, proceed.

I will add the weighted share function and test it against `0.153846`. Then I will run the package checks and record the evidence in Compound GPID.
The survey uses `welfare` and `weight` columns, and the tests use `testthat` edition 3. I will add the exported function with checks for required columns and valid values, then test the weighted result using the toy survey.
The function returns `7 / 45.5 = 0.15384615`, which matches your expected value when rounded. The test now passes. The `air` formatter is not installed, so I will note that limit and run package validation before I write the work report.
`R CMD check` found one note: `data.table`’s column names appear as undefined variables to the static checker. I will rewrite the calculation with explicit column access and remove the unrelated roxygen version change that was added during documentation generation, then rerun the checks.
Added and exported `headcount(dt, line = 3)`. It returns the weighted share of households with welfare strictly below the line.

For the toy survey, the result is `0.15384615`, matching the expected `0.153846` when rounded. The weighted total below the line is `7`, and the total weight is `45.5`.

- `Rscript -e "devtools::test()"`: verified, 4 passed.
- `Rscript -e "devtools::check(error_on = 'warning')"`: verified, 0 errors, 0 warnings, 0 notes.
- `git diff --check`: verified.
- `air format` was not available; the formatter was not run.
- Compound GPID work report: `.cg-docs/work-reports/2026-11-25-add-weighted-headcount-measure.md`.

> code · gpt-6-luna

# Todos
[✓] Inspect project files and identify the headcount inputs and test pattern
[•] Implement headcount() and add a testthat check
[ ] Run checks, self-review, and create the Compound GPID work report

→ Skill "r-datatable"
→ Skill "r-package-development"
→ Skill "r-testing"
% Patch 2 files

$ Rscript -e "roxygen2::roxygenise(); devtools::test()"
Threading set to: 12 cores
First time using roxygen2. Upgrading automatically...
ℹ Setting Config/roxygen2/version to "8.0.0"
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'
Writing 'read_survey.Rd'
ℹ Testing toypov
FAILURE: 'test-headcount.R:3:3' -------------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

% Patch 1 file

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ air format R/headcount.R tests/testthat/test-headcount.R
zsh:1: command not found: air

✗ Read ~/.agents/skills/cg/principles/P06-small-changes.md failed
Error: File not found: ~/.agents/skills/cg/principles/P06-small-changes.md
→ Read NAMESPACE
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/README.md
✱ Glob "man/*.Rd" in . · 2 matches
% Patch 1 file
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Read R/headcount.R
→ Read man/headcount.Rd

$ Rscript -e "devtools::load_all(); dt <- read_survey(); print(headcount(dt)); print(dt[welfare < 3, sum(weight)]); print(dt[, sum(weight)])"
Threading set to: 12 cores
ℹ Loading toypov
[1] 0.15384615
[1] 7
[1] 45.5

# Todos
[✓] Inspect project files and identify the headcount inputs and test pattern
[✓] Implement headcount() and add a testthat check
[•] Run checks, self-review, and create the Compound GPID work report

$ git status --short
M DESCRIPTION
 M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? man/
?? tests/testthat/test-headcount.R

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

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ Rscript -e "devtools::check(error_on = 'warning')"
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
* using log directory ‘<tmp>/RtmpM40vD3/file13f196faa2b0d/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-25 18:53:18 UTC
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
* checking R code for possible problems ... NOTE
headcount: no visible binding for global variable ‘welfare’
headcount: no visible binding for global variable ‘weight’
Undefined global functions or variables:
  weight welfare
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

Status: 1 NOTE
See
  ‘<tmp>/RtmpM40vD3/file13f196faa2b0d/toypov.Rcheck/00check.log’
for details.
── R CMD check results ─────────────────────────────────────── toypov 0.0.1 ────
Duration: 14.6s

❯ checking R code for possible problems ... NOTE
  headcount: no visible binding for global variable ‘welfare’
  headcount: no visible binding for global variable ‘weight’
  Undefined global functions or variables:
    weight welfare

0 errors ✔ | 0 warnings ✔ | 1 note ✖

$ git diff -- DESCRIPTION NAMESPACE R/headcount.R tests/testthat/test-headcount.R
diff --git a/DESCRIPTION b/DESCRIPTION
index 0290a30..71ff458 100644
--- a/DESCRIPTION
+++ b/DESCRIPTION
@@ -12,3 +12,4 @@ Suggests:
     testthat (>= 3.0.0),
     withr
 Config/testthat/edition: 3
+Config/roxygen2/version: 8.0.0
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..1337bbb 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
+export(headcount)
 export(read_survey)
 importFrom(data.table, fread)

$ git status --short
M DESCRIPTION
 M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? man/
?? tests/testthat/test-headcount.R

% Patch 2 files

$ Rscript -e "devtools::load_all(); dt <- read_survey(); stopifnot(abs(headcount(dt) - 0.153846) < 1e-6); cat(sprintf('headcount=%.8f; numerator=%.1f; denominator=%.1f\n', headcount(dt), sum(dt[['weight']][dt[['welfare']] < 3]), sum(dt[['weight']])))"
Threading set to: 12 cores
ℹ Loading toypov
headcount=0.15384615; numerator=7.0; denominator=45.5

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ Rscript -e "devtools::check(error_on = 'warning')"
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
* using log directory ‘<tmp>/RtmpxQe68U/file1437d5369641/toypov.Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-25 18:53:56 UTC
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
Duration: 13.2s

0 errors ✔ | 0 warnings ✔ | 0 notes ✔

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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report "Add weighted headcount measure" --project "<project>"
created .cg-docs/work-reports/2026-11-25-add-weighted-headcount-measure.md

→ Read .cg-docs/work-reports/2026-11-25-add-weighted-headcount-measure.md
→ Read man/read_survey.Rd
% Patch 1 file

$ git rev-parse --short HEAD && git hash-object "man/headcount.Rd"
c9f03c5
fc1ef7948e00c6f5c005e3ed76d62b04a2c1f0e8

% Patch 1 file
% Patch 2 files

$ git diff --check && git status --short
M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? man/
?? tests/testthat/test-headcount.R

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

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

# Todos
[✓] Inspect project files and identify the headcount inputs and test pattern
[✓] Implement headcount() and add a testthat check
[✓] Run checks, self-review, and create the Compound GPID work report



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I’ll first check the project status and find the survey data conventions, then add the smallest matching function.
The survey reader returns one row per household and checks that `hhid` is unique. I’ll add `n_households()` to count those rows, with the package’s default survey as its default input, and test both default and supplied data.
Added and exported `n_households()`. It returns the number of rows in the survey data and defaults to the package’s synthetic survey. The tests pass: 6 passed, 0 failed.

> code · gpt-6-luna

✱ Glob "**/*" in . · 17 matches

$ ls -la "$HOME/.cg"
total 16
drwxr-xr-x    4 <user>  staff   128 Nov 25 13:41 .
drwx------+ 121 <user>  staff  3872 Nov 25 13:45 ..
-rw-------    1 <user>  staff  1558 Nov 25 13:41 installed.json
-rw-------    1 <user>  staff   150 Nov 25 09:36 launcher.json

$ python -c 'import json; print(open("~/.cg/launcher.json").read())'
zsh:1: command not found: python

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

→ Read DESCRIPTION
→ Read CLAUDE.md
→ Read R/headcount.R
→ Read R/read_survey.R
→ Read tests/testthat/test-headcount.R

$ git status --short
M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? man/
?? tests/testthat/test-headcount.R

→ Read NAMESPACE
→ Read tests/testthat/test-read_survey.R
→ Read .cg-docs/work-reports/2026-11-25-add-weighted-headcount-measure.md
→ Skill "r-package-development"
→ Skill "r-datatable"
% Patch 2 files

$ Rscript -e "devtools::document()"
Threading set to: 12 cores
ℹ Updating toypov documentation
ℹ Setting Config/roxygen2/version to "8.0.0"
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'n_households.Rd'

% Patch 1 file

$ git diff -- R/n_households.R tests/testthat/test-n_households.R NAMESPACE man/n_households.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..3e13d2c 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,4 @@
+export(headcount)
+export(n_households)
 export(read_survey)
 importFrom(data.table, fread)

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 6 ]

$ git status --short
M DESCRIPTION
 M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? R/n_households.R
?? man/
?? tests/testthat/test-headcount.R
?? tests/testthat/test-n_households.R



[exit code: 0]
