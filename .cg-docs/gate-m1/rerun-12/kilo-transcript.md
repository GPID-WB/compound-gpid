### B1 setup

> /cg

Setup is still at **Explore**. No files have changed.

**Proposal**

- **Packs:** `core` and `lang-r`. Both are installed.
- **R syntax:** `data.table-collapse`. The package imports `data.table` (`DESCRIPTION:11–12`), and `R/read_survey.R:8` uses `fread()`. This is the recommended setting.
- **Verification profile draft:**
  - **Run:** not found. The project has a `testthat` test file, but no command that produces the package outputs was identified.
  - **Doctor:** not found.
  - **Output:** `read_survey()` returns a `data.table`. The test checks for 20 rows and the columns `hhid`, `welfare`, and `weight` (`tests/testthat/test-read_survey.R:1–5`). I did not open the survey data.
- **Data:** one data file found: `inst/extdata/survey.csv`. Its classification and the highest classification this coding agent may read need your decision.

**Files the setup command would create or change**

This list comes from the setup dry run:

- `.cg-docs/config.json`
- `.cg-docs/verification.md`
- `AGENTS.md`
- `CLAUDE.md`
- `.Rbuildignore`

**Decision needed**

State the classification for `inst/extdata/survey.csv`, the highest classification this coding agent may read, and the organization’s classification levels in order, from public to most restricted. Example format:

```text
inst/extdata/survey.csv=Public; coding agent may read up to=Public; levels=Public;Internal;Restricted
```

Assumption: “synthetic” in the package description does not establish the data classification. I have not inspected the data file. The only choices proposed so far are the `core` and `lang-r` packs and the `data.table-collapse` setting. No setup files will be written until you confirm the proposal.

**Next steps: Waiting on you**
* **Your move:** Reply with the data rules and a clear yes to the proposal, or state any corrections.
* **Project:** Setup has not written files. It will proceed after you confirm the proposal and provide the data rules.

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

✱ Glob "playbooks/setup.md" in ~/.agents/skills/cg · 1 match
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
→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R

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
    approve             record the human's approval of a plan, or their
                        decision on data
    tier                compute the risk level of a piece of work from
                        declared facts

options:
  -h, --help            show this help message and exit

→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P02-human-decides.md
✱ Glob "{AGENTS.md,CLAUDE.md,GLOSSARY.md,.cg-docs/**,compound-gpid*,.Rbuildignore,_targets.R,Makefile,renv.lock}" in . · 0 matches

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --project "<project>" --dry-run
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore



[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

I will write the confirmed setup: `core` and `lang-r`, the `data.table-collapse` setting, and the Public data rule. I will record Kilo Code as approved to read Public data; no classification-level list was provided.
Setup is complete. The project uses the `core` and `lang-r` packs, with `lang-r.r-syntax=data.table-collapse`. The survey file is classified as Public, and Kilo Code may read Public data.

The setup created `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. The verification profile remains a draft: Run and Doctor commands were not found, and independent validation is not recorded.

Status reports `phase: ready`, `stops: none`, no missing packs, and `data: inst/extdata/survey.csv=Public`. No classification-level list was provided.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** Setup is ready; the verification profile remains a draft.

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

I will check the Compound GPID status and project instructions first, then find the welfare and weight fields in the toy survey.
The request adds a numeric result and a new public function, so the change needs an elevated tier review. The survey is classified as Public and Kilo Code is approved for Public data; I will check the required contract before I read it or edit files.
The request is to add and document `headcount(dt, line = 3)` and test that the toy survey returns `0.153846`. I will leave other functions and survey data unchanged.

The risk check returned `tier: elevated` because this change computes a number and adds a public function. The survey file is cleared for Kilo Code to read, but I must stop before reading it or changing files until you approve the contract.

**Contract**
- **Goal:** Return the weighted share of households whose welfare is below `line`.
- **Out of scope:** Changes to the survey data, other measures, and dependencies.
- **Checks:** Run the testthat tests and check the result against your expected `0.153846`. A failed test or a different result means the change is not verified.

Reply **“Yes, I approve this contract.”** to proceed.

**Next steps: Waiting on you**
* **Your move:** Reply `Yes, I approve this contract.`
* **Project:** The implementation has not started. I will proceed only after your approval.

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

# Todos
[•] Inspect project files and determine the change tier
[ ] Implement headcount and its test
[ ] Run checks and create a validated work report

✱ Glob "**/*" in . · 13 matches

$ git status --short
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md

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

→ Read AGENTS.md
→ Read NAMESPACE
→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read ~/.agents/skills/cg/principles/README.md
→ Read DESCRIPTION
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "tests/testthat/test-read_survey.R" --touches "NAMESPACE" --touches "man/headcount.Rd" --reads "inst/extdata/survey.csv" --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 4



[exit code: 0]

### C2 yes

> Yes, proceed.

I will implement the weighted headcount measure, add a test for the expected value, and record the approval in the work report. Then I will run the package checks and validate the report.
The survey has total weight 39, and households below 3 have total weight 6, so the expected share is `6 / 39 = 2 / 13`, which rounds to `0.153846`. I will use that result as the independent reference. I will use base R for the calculation so the function does not add a dependency.
The new test failed first because `headcount()` was not yet defined. After implementation, a tolerance argument did not behave as expected with this test setup, so I changed the check to compare the result with the expected value at the precision given. The full test suite now passes. I will run package checks next.
The full test and package check pass, and the function returns `0.15384615`. I found an arithmetic error in my earlier explanation: the correct reference is poor-household weight `7` divided by total weight `45.5`, not `6 / 39`. The corrected calculation matches your expected value.
Added and documented `headcount(dt, line = 3)` in `R/read_survey.R`. It returns the weighted share of households with welfare below the line. Added a test, exported the function, and added its help page.

The toy survey returns `0.15384615`, which rounds to the expected `0.153846`. The testthat suite and `R CMD check` passed. `R CMD check` reported two NOTES for checking an unbuilt source tree that contains `.git` and `.cg-docs`. The work report is complete and validated at `.cg-docs/work-reports/2026-11-26-add-weighted-headcount.md`.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The weighted headcount function, test and documentation are complete. The work report is validated.

> code · gpt-6-luna

→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Skill "r-datatable"
→ Skill "r-analytical"
→ Skill "r-testing"
→ Skill "r-technical"
→ Skill "r-collapse"

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "tests/testthat/test-read_survey.R" --touches "NAMESPACE" --touches "man/headcount.Rd" --reads "inst/extdata/survey.csv" --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 4

→ Read ~/.agents/skills/r-analytical/workflows/welfare-patterns.md
→ Read ~/.agents/skills/r-analytical/workflows/survey-analysis.md
→ Read .cg-docs/verification.md
→ Read inst/extdata/survey.csv

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
    approve             record the human's approval of a plan, or their
                        decision on data
    tier                compute the risk level of a piece of work from
                        declared facts

options:
  -h, --help            show this help message and exit

$ Rscript -e 'library(testthat); test_file("tests/testthat/test-read_survey.R")'
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

[ FAIL 2 | WARN 0 | SKIP 0 | PASS 0 ]

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 3 ]

% Patch 1 file

$ Rscript -e 'devtools::test()'
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
% Patch 1 file
% Patch 1 file

# Todos
[✓] Inspect project files and determine the change tier
[✓] Implement headcount and its test
[•] Run checks and create a validated work report

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
FAILURE: 'test-read_survey.R:15:3' ----------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

→ Read tests/testthat/test-read_survey.R

$ Rscript -e 'print(all.equal(2 / 13, 0.153846, tolerance = 1e-6)); print(testthat::expect_equal(2 / 13, 0.153846, tolerance = 1e-6))'
Threading set to: 12 cores
[1] TRUE
Error: Expected `2/13` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460
Execution halted

% Patch 1 file

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ R CMD check --no-manual --no-build-vignettes --output=<tmp>/kilo .
Threading set to: 12 cores
* using log directory ‘<tmp>/kilo/..Rcheck’
* using R version 4.6.2 (2026-10-29)
* using platform: aarch64-apple-darwin23
* R was compiled by
    Apple clang version 17.0.0 (clang-1700.3.19.1)
    GNU Fortran (GCC) 14.2.0
* running under: macOS Tahoe 26.7.3
* using session charset: UTF-8
* current time: 2026-11-26 13:25:10 UTC
* using options ‘--no-manual --no-build-vignettes’
* checking for file ‘./DESCRIPTION’ ... OK
* this is package ‘toypov’ version ‘0.0.1’
* package encoding: UTF-8
* checking package namespace information ... OK
* checking package dependencies ... OK
* checking if this is a source package ... OK
* checking if there is a namespace ... OK
* checking for executable files ... OK
* checking for hidden files and directories ... NOTE
Found the following hidden files and directories:
  .cg-docs
  .git
These were most likely included in error. See section ‘Package
structure’ in the ‘Writing R Extensions’ manual.
* checking for portable file names ... OK
* checking for sufficient/correct file permissions ... OK
* checking whether package ‘toypov’ can be installed ... OK
* checking installed package size ... OK
* checking package directory ... OK
* checking DESCRIPTION meta-information ... NOTE
Checking should be performed on sources prepared by ‘R CMD build’.
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
* DONE
Status: 2 NOTEs

See
  ‘<tmp>/kilo/..Rcheck/00check.log’
for details.

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
created .cg-docs/work-reports/2026-11-26-add-weighted-headcount.md

→ Read .cg-docs/work-reports/2026-11-26-add-weighted-headcount.md

$ git rev-parse --short HEAD
6a80491

$ git diff --check && git diff --stat && git status --short
NAMESPACE                         |  1 +
 R/read_survey.R                   | 28 ++++++++++++++++++++++++++++
 tests/testthat/test-read_survey.R |  5 +++++
 3 files changed, 34 insertions(+)
 M NAMESPACE
 M R/read_survey.R
 M tests/testthat/test-read_survey.R
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? man/headcount.Rd

$ Rscript -e 'devtools::load_all(); dt <- read_survey(); print(headcount(dt)); print(sum(dt$weight[dt$welfare < 3])); print(sum(dt$weight))'
Threading set to: 12 cores
ℹ Loading toypov
[1] 0.15384615
[1] 7
[1] 45.5

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

→ Read .cg-docs/work-reports/2026-11-26-add-weighted-headcount.md
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

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

# Todos
[✓] Inspect project files and determine the change tier
[✓] Implement headcount and its test
[✓] Run checks and create a validated work report



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

/cg` would run this change with checks and a record. I will first check the project status and find the survey data conventions, then add the function with a focused test.
The package has `read_survey()` with one row per household. I will add `n_households()` with a default survey input, export it, document it, and test both the default survey and a supplied table.
Added and exported `n_households()`. It returns the row count of a supplied survey table, or the package’s survey when called without an argument. Added documentation and tests; all 6 tests pass, and `git diff --check` reports no issues.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The household-count function is implemented in `R/read_survey.R` and verified with the package tests.

> code · gpt-6-luna

# Todos
[•] Check Compound GPID status and project conventions
[ ] Implement household-count function and test
[ ] Run focused verification

→ Read ~/.cg/launcher.json

$ ls "~/.cg" "<project>"
~/.cg:
installed.json
launcher.json

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

✱ Glob "**/*" 15 matches

$ git status --short --branch
## main
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
→ Read tests/testthat/test-read_survey.R
→ Read .cg-docs/work-reports/2026-11-26-add-weighted-headcount.md

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

→ Read NAMESPACE
→ Read .cg-docs/verification.md
→ Read .cg-docs/config.json
→ Read man/read_survey.Rd
→ Read inst/extdata/survey.csv
→ Skill "r-shared"
→ Skill "r-datatable"
→ Skill "r-collapse"
→ Skill "r-technical"
→ Skill "r-testing"

# Todos
[✓] Check Compound GPID status and project conventions
[•] Implement household-count function and test
[ ] Run focused verification

% Patch 2 files

# Todos
[✓] Check Compound GPID status and project conventions
[✓] Implement household-count function and test
[•] Run focused verification

$ Rscript -e 'devtools::document()'
Threading set to: 12 cores
ℹ Updating toypov documentation
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'n_households.Rd'
Writing 'headcount.Rd'

→ Read NAMESPACE

$ git diff -- R/read_survey.R tests/testthat/test-read_survey.R NAMESPACE man/headcount.Rd man/n_households.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)
diff --git a/R/read_survey.R b/R/read_survey.R
index bcde534..31e2e2c 100644
--- a/R/read_survey.R
+++ b/R/read_survey.R
@@ -22,3 +22,43 @@ read_survey <- function(path = system.file("extdata", "survey.csv", package = "t
   }
   return(dt)
 }
+
+#' Count households in a survey
+#'
+#' @param dt A data.table with one row per household. Defaults to the synthetic
+#'   survey shipped with the package.
+#' @return The number of households in the survey.
+#' @examples
+#' n_households()
+#' @export
+n_households <- function(dt = read_survey()) {
+  return(nrow(dt))
+}
+
+#' Calculate the weighted headcount ratio
+#'
+#' @param dt A data.table with `welfare` and `weight` columns.
+#' @param line A positive welfare threshold. Households with welfare below
+#'   this value are counted as poor.
+#' @return The weighted share of households with welfare below `line`.
+#' @examples
+#' dt <- read_survey()
+#' headcount(dt)
+#' @export
+headcount <- function(dt, line = 3) {
+  needed <- c("welfare", "weight")
+  missing_cols <- setdiff(needed, names(dt))
+  if (length(missing_cols) > 0) {
+    stop("survey is missing columns: ", paste(missing_cols, collapse = ", "))
+  }
+  if (length(line) != 1 || !is.numeric(line) || !is.finite(line) || line <= 0) {
+    stop("line must be a single positive finite number")
+  }
+  if (anyNA(dt$welfare) || anyNA(dt$weight) ||
+      any(dt$welfare <= 0) || any(dt$weight <= 0)) {
+    stop("welfare and weight must be present and positive for every household")
+  }
+
+  poor <- dt$welfare < line
+  return(sum(dt$weight[poor]) / sum(dt$weight))
+}
diff --git a/tests/testthat/test-read_survey.R b/tests/testthat/test-read_survey.R
index 7eedc79..73bfce0 100644
--- a/tests/testthat/test-read_survey.R
+++ b/tests/testthat/test-read_survey.R
@@ -9,3 +9,13 @@ test_that("read_survey() refuses a non-positive weight", {
   writeLines(c("hhid,welfare,weight", "1,2.5,0"), path)
   expect_error(read_survey(path), "weight must be present and positive")
 })
+
+test_that("n_households() counts rows in the survey", {
+  expect_equal(n_households(), 20L)
+  expect_equal(n_households(data.table::data.table(hhid = 1:3)), 3L)
+})
+
+test_that("headcount() returns the weighted share below the line", {
+  dt <- read_survey()
+  expect_true(abs(headcount(dt) - 0.153846) < 5e-7)
+})

% Patch 1 file

$ git diff --check
(no output)

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 6 ]

# Todos
[✓] Check Compound GPID status and project conventions
[✓] Implement household-count function and test
[✓] Run focused verification



[exit code: 0]
