### B1 setup

> /cg

The project has no Compound GPID setup. I will inspect tracked and untracked project files, installed packs, and setup defaults. I will not open data files or write files before you confirm the setup.
**Recommended setup**

- **Packs:** `core` and `lang-r`. Both are installed. The project contains an R package: `DESCRIPTION`, `R/read_survey.R`, and test files.
- **R syntax:** `data.table-collapse`. The source uses `fread()` and returns a `data.table` in `R/read_survey.R:8,23`. This is also the installed `lang-r` default.
- **Verification profile draft:** Run command: `R CMD check .` Doctor command: not found. The package has tests in `tests/testthat/`, but I did not find a project command that runs them or a defined output that proves correctness. I did not run any checks.
- **Data rules:** I found one data file: `inst/extdata/survey.csv`. Its classification, the highest level this coding agent may read, and the organization’s classification levels are not known. I did not open the file. The description says the survey is synthetic, but that does not establish its classification.

What classification applies to `inst/extdata/survey.csv`, what is the highest level this coding agent may read, and what are the organization’s classification levels from public to most restricted? You can answer in this format: `inst/extdata/survey.csv=Public; coding agent=Public; levels=Public;Internal;Restricted`. Change the example to match your policy.

**Assumptions:** I treated the project root as the directory you opened. I recommend the installed `data.table-collapse` default because the source uses `data.table`. The run command is a draft, not a confirmed verification profile.

After you confirm the proposal, setup would create `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. No files have been written.

**Next steps: Waiting on you**
* **Your move:** Confirm the proposed setup and provide the data rules, or state corrections.
* **Project:** The project is in setup; no files have changed.

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

$ git ls-files --cached --others --exclude-standard
DESCRIPTION
LICENSE
NAMESPACE
R/read_survey.R
inst/extdata/survey.csv
man/read_survey.Rd
tests/testthat.R
tests/testthat/test-read_survey.R

→ Read DESCRIPTION
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R
→ Read tests/testthat.R
→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read ~/.agents/skills/cg/principles/README.md

$ find . -type f \( -name '*.dta' -o -name '*.csv' -o -name '*.parquet' -o -name '*.rds' -o -name '*.fst' -o -name '*.xlsx' -o -name '*.xls' \) -not -path './.git/*' -print
./inst/extdata/survey.csv

$ git status --short --branch
## main

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

Your confirmation covers the survey classification and the coding agent’s read level. The organization’s classification-level names remain unknown, so I will leave that unset and write only the confirmed setup values.
Compound GPID setup is complete. Status reports `phase: ready`, `stops: none`, `settings: lang-r.r-syntax=data.table-collapse`, `data: inst/extdata/survey.csv=Public`, and `approved-tools: Kilo=Public`.

Created `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. No verification commands were run. The organization’s classification-level names remain unset.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** Setup is ready. The next guide step is the quick playbook.

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
approved-tools: Kilo=Public
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md



[exit code: 0]

### C1 request

> /cg Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

I’ll check the project record and current package setup first. Then I’ll add `headcount()` and a `testthat` check.
The project uses `data.table` and `collapse`. This function computes a survey statistic, so I’ll check the project rules and inputs before I read the toy survey or edit code.
`/cg` marks this change as **elevated** because `headcount()` computes a number and adds a public function interface. The toy survey is cleared for Kilo to read.

**Contract:** Add `headcount(dt, line = 3)` and a `testthat` check for the toy survey. I will leave other functions and data unchanged. I will run the relevant test and compare its result with your expected value, `0.153846`; a test failure or a result that does not match at six decimal places means failure.

Reply **“yes”** to approve this contract. I will not edit files until you approve it.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the contract.
* **Project:** No files have changed. Work can start after you approve.

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
approved-tools: Kilo=Public
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

→ Read ~/.agents/skills/cg/playbooks/quick.md

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
→ Skill "r-analytical"
→ Skill "r-collapse"
→ Skill "r-datatable"
→ Skill "r-testing"

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/headcount.R" --touches "tests/testthat/test-headcount.R" --reads "inst/extdata/survey.csv" --agent "Kilo" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 2



[exit code: 0]

### C2 yes

> Yes, proceed.

I’ll record the approval and inspect the package layout and survey definition. Then I’ll add the function and test, and run the test against the expected share.
The survey columns are `welfare` and `weight`. The poverty line uses a strict “below” comparison, and the expected result is `6 / 39 = 0.153846…`. Because this package exports documented functions, I’ll also update its export list and generated help page.
The new test fails before the change because `headcount()` does not exist. I’ll implement a weighted share using the existing columns, without adding a dependency or changing the input table.
The full suite passes. A direct check gives weighted poor households `7`, total weight `45.5`, and headcount `0.15384615`, which rounds to your expected `0.153846`. I’m tightening the test to compare at six decimal places, then I’ll write and validate the work record.
Added exported `headcount(dt, line = 3)` with package documentation and a test for the toy survey. The function returns the weighted share with welfare **strictly below** the poverty line. It does not change `dt`.

- **Verified:** `Rscript -e 'devtools::test()'` passed all 4 tests.
- **Verified:** The function returned `0.15384615`, which rounds to the expected `0.153846` at six decimal places.
- **Verified:** `devtools::document()` ran, and the work report passed `cg.py validate` with no problems or warnings.

The work report is `.cg-docs/work-reports/2026-11-25-add-weighted-headcount.md`. Self-review: P3, P4 and P6 passed. I did not run `R CMD check`. Existing untracked setup files remain untouched.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The function, documentation, test and work report are complete.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo=Public" --project "<project>"
nothing to change: the project already holds what setup writes

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/headcount.R" --touches "tests/testthat/test-headcount.R" --reads "inst/extdata/survey.csv" --agent "Kilo" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 2

# Todos
[•] Inspect package structure, conventions, and toy survey columns
[ ] Implement headcount() and a toy-survey test
[ ] Run checks and record verified evidence

→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/r-analytical/workflows/welfare-patterns.md
✱ Grep "welfare|weight|headcount|poverty" in . · 10 matches
✱ Glob "**/*" in . · 13 matches
→ Read AGENTS.md
→ Read DESCRIPTION
→ Read NAMESPACE
→ Read R/read_survey.R
→ Read .cg-docs/verification.md
→ Read tests/testthat/test-read_survey.R
→ Read inst/extdata/survey.csv

$ git status --short
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/headcount.R" --touches "tests/testthat/test-headcount.R" --touches "NAMESPACE" --touches "man/headcount.Rd" --reads "inst/extdata/survey.csv" --agent "Kilo" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 4

→ Skill "r-technical"
% Patch 1 file

$ Rscript -e 'testthat::test_file("tests/testthat/test-headcount.R")'
Threading set to: 12 cores
ERROR: 'test-headcount.R:2:3' ---------------------
Error in `read_survey()`: could not find function "read_survey"

[ FAIL 1 | WARN 0 | SKIP 0 | PASS 0 ]

$ Rscript -e 'devtools::test(filter = "headcount")'
Threading set to: 12 cores
ℹ Testing toypov
ERROR: 'test-headcount.R:4:3' ---------------------
Error in `headcount(dt)`: could not find function "headcount"
Backtrace:
    ▆
 1. └─testthat::expect_equal(headcount(dt), 0.153846, tolerance = 0.000001) at test-headcount.R:4:3
 2.   └─testthat::quasi_label(enquo(object), label)
 3.     └─rlang::eval_bare(expr, quo_get_env(quo))

[ FAIL 1 | WARN 0 | SKIP 0 | PASS 0 ]

# Todos
[✓] Inspect package structure, conventions, and toy survey columns
[•] Implement headcount() and a toy-survey test
[ ] Run checks and record verified evidence

% Patch 3 files

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
FAILURE: 'test-headcount.R:4:3' -------------------
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

# Todos
[✓] Inspect package structure, conventions, and toy survey columns
[✓] Implement headcount() and a toy-survey test
[•] Run checks and record verified evidence

→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md

$ Rscript -e 'devtools::document()'
Threading set to: 12 cores
ℹ Updating toypov documentation
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

$ git diff --stat
NAMESPACE | 1 +
 1 file changed, 1 insertion(+)

$ git status --short
M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? man/headcount.Rd
?? tests/testthat/test-headcount.R

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
    approve             record the human's approval of a plan
    tier                compute the risk level of a piece of work from
                        declared facts

options:
  -h, --help            show this help message and exit

$ Rscript -e 'devtools::load_all(); dt <- read_survey(); cat("weighted poor:", sum(dt$weight[dt$welfare < 3]), "total weight:", sum(dt$weight), "headcount:", headcount(dt), "rounded:", round(headcount(dt), 6), "\n")'
Threading set to: 12 cores
ℹ Loading toypov
weighted poor: 7 total weight: 45.5 headcount: 0.15384615 rounded: 0.153846

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

% Patch 1 file

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

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report "Add weighted headcount" --project "<project>"
created .cg-docs/work-reports/2026-11-25-add-weighted-headcount.md

→ Read .cg-docs/work-reports/2026-11-25-add-weighted-headcount.md
→ Read R/headcount.R
→ Read tests/testthat/test-headcount.R

$ git rev-parse --short HEAD
9e030f8

$ git hash-object R/headcount.R man/headcount.Rd tests/testthat/test-headcount.R NAMESPACE
d5f3311bc4e6cda6a831b898724bdaf2244e40a8
5c769d78c660986a349f428e001634f56fc30926
c2ed443f5f1f650c031b015cbe321aee01e9c93d
1337bbb2130f45064144af057445198631aa555d

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-25-add-weighted-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-25-add-weighted-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

# Todos
[✓] Inspect package structure, conventions, and toy survey columns
[✓] Implement headcount() and a toy-survey test
[✓] Run checks and record verified evidence



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I will check the project status and its R conventions, then add and test the household-count function.
The package already reads one row per household and has a weighted `headcount()` function. I will add a separate function that counts survey rows, with checks for the household ID column and tests for empty and ordinary surveys.
`n_households()` now returns the number of rows in the survey after it checks that `hhid` is present, non-missing, and unique. Tests pass: `Rscript -e 'devtools::test()'` reported 9 passes.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The household-count function and tests are in place; the package test suite passes.

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
approved-tools: Kilo=Public
git: repository
branch: main
changed-files: 8
stops: none
next: the human types /cg to run the work through the guide

→ Skill "r-shared"
→ Skill "r-datatable"
→ Read .cg-docs/config.json
✱ Glob "**/*" 17 matches

$ git status --short
M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? man/headcount.Rd
?? tests/testthat/test-headcount.R

→ Read AGENTS.md
→ Read DESCRIPTION
→ Read R/headcount.R
→ Read R/read_survey.R
→ Read tests/testthat/test-headcount.R
→ Read inst/extdata/survey.csv [limit=8]
→ Read NAMESPACE
→ Read tests/testthat.R
→ Read .cg-docs/verification.md
% Patch 3 files

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 9 ]



[exit code: 0]
