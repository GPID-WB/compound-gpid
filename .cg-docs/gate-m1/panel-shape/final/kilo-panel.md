### B1 setup

> [the body of SKILL.md at d93dfef6, as Kilo's panel sends it; 68 lines, not repeated here]


Base directory for this skill: ~/.agents/skills/cg
Relative paths in this skill (e.g., scripts/, references/) are relative to this base directory.

**Measured:** The project is an R package. It has four R files, one `.Rd` file, and one CSV file. The CSV is `inst/extdata/survey.csv`. I did not open it. `DESCRIPTION` says the survey data are made up, but that does not set their classification.

**Recommended setup:**
- Packs: `core` and `lang-r`. Both are installed.
- Setting: `lang-r.r-syntax=data.table-collapse`. The R code uses `data.table` (`DESCRIPTION`, lines 11–12; `R/read_survey.R`, line 8). The pack’s default also applies when no setting is declared.
- Verification profile: **not found**. The project has a `testthat` test file, but no Run command, Doctor command, or stated pass condition. I did not run checks.
- Data rules: Please give the classification for `inst/extdata/survey.csv`, the highest classification level this coding agent may read, and the organization’s classification levels from public to most restricted, if known. Example: `survey.csv=Public; agent=Public; levels=Public; Internal; Restricted`.

I assumed this coding agent’s product name is **Kilo**. I did not set a data rule or a classification level for Kilo because only you can declare those.

If you approve this proposal, reply with **yes** and the data rules. The setup command preview shows that setup would create `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`. Nothing has been written.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` with the three data rules, or send corrections to the proposal.
* **Project:** Setup is not complete. The project has no `.cg-docs/config.json`; the next step depends on your approval and data rules.

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
→ Read tests/testthat.R
→ Read tests/testthat/test-read_survey.R
✱ Glob "{AGENTS.md,CLAUDE.md,GLOSSARY.md,.cg-docs/**,Makefile,_targets.R,renv.lock}" in . · 0 matches
→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/GLOSSARY.md

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

$ Rscript -e 'tools::package_dependencies("toypov", which = c("Depends", "Imports", "LinkingTo"))'
Threading set to: 12 cores
$toypov
NULL

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --project "<project>" --dry-run
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore



[exit code: 0]

### B2 yes

> Yes. The survey inst/extdata/survey.csv is synthetic and its classification is Public, and you may read Public data.

The approval sets the survey file to Public and allows Kilo to read Public data. I will check the project state again, then write only the confirmed setup.
Setup is ready, and status shows both packs installed with the approved data rule. I will replace the template placeholders with the verification details found in the package; the profile will stay draft because no project Run or Doctor command was found.
Setup is complete.

- **Measured:** Status reports `phase: ready`, `stops: none`, and `packs-missing: none`.
- **Measured:** Status records `settings: lang-r.r-syntax=data.table-collapse` and `data: inst/extdata/survey.csv=Public`.
- **Recorded:** Kilo may read Public data. No full classification scale was provided, so none was recorded.
- **Created or updated:** `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.
- **Open:** The verification profile is still a draft. No project Run command or Doctor command was found. The existing test checks that `read_survey()` returns 20 rows with the expected column names. No independent reference value or cross-check is defined.
- **Not checked:** I did not run the package tests or a package check.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** Compound GPID setup is complete. The verification profile remains a draft until the project’s Run command is defined and run.

> code · gpt-6-luna

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

→ Read ~/.agents/skills/cg/templates/verification.md
→ Read ~/.agents/skills/cg/templates/pointer-block.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo=Public" --project "<project>" --dry-run
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo=Public" --project "<project>"
created .cg-docs/config.json
created .cg-docs/verification.md
created AGENTS.md
created CLAUDE.md
created .Rbuildignore

→ Read .cg-docs/verification.md

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
git: repository
branch: main
changed-files: 4
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md



[exit code: 0]

### C1 request

> [the body of SKILL.md at d93dfef6, as Kilo's panel sends it; 68 lines, not repeated here]


Base directory for this skill: ~/.agents/skills/cg
Relative paths in this skill (e.g., scripts/, references/) are relative to this base directory.

Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

/cg would run this change with checks and a record. I will read the Compound GPID state first, then follow the playbook that it selects.
The requested change adds `headcount(dt, line = 3)` to calculate a weighted poverty share. I will leave other functions and data unchanged.

The risk check found one hard stop: **yes, this change computes a number someone will read.** The survey file is classified Public and Kilo is approved to read Public data. The other risk checks are no: the change does not involve personal data, credentials, irreversible actions, dependencies, or more than five files. It has a test that can check the result.

**Contract**
- Goal: add and export `headcount(dt, line = 3)` and add a testthat check against your expected toy-survey value, `0.153846`.
- Out of scope: changes to the survey data or other functions.
- Checks: run the relevant testthat tests. Failure means the tests fail or the returned value does not equal `0.153846` at six decimal places.

I have not changed any files. Reply **yes** to approve this contract.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the contract.
* **Project:** The current work is ready; the function, test, verification, and work report are pending approval.

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
[•] Inspect current R source and test files for the requested change
[ ] Report the required approval contract before editing
[ ] Implement, verify, and record the approved change

✱ Glob "R/**" 1 match
✱ Glob "tests/**" 2 matches
✗ Read GLOSSARY.md failed
Error: File not found: <project>/GLOSSARY.md
→ Read tests/testthat/test-read_survey.R
→ Read .cg-docs/config.json
→ Read R/read_survey.R

# Todos
[✓] Inspect current R source and test files for the requested change
[•] Report the required approval contract before editing
[ ] Implement, verify, and record the approved change



[exit code: 0]

### C2 yes

> Yes, proceed.

The contract is approved. I will check the existing worktree, load the R and verification guidance, then add the function and test without changing the survey data.
The package has no project glossary. The domain guidance defines the headcount as the weighted mean of the below-line indicator, using strict `<` and the full household weight total. I will add a documented exported function and a test of the public call; the existing baseline test suite passes.
The new test fails before implementation because `headcount()` is not yet defined. The independent calculation on the Public toy survey returns `0.15384615`, which matches the expected value to six decimal places. I will now add the documented function with checks for missing columns, missing values, and invalid weights, then generate package documentation.
The first implementation run exposed a test precision issue: the exact estimate is `0.15384615`, while the approved expectation is rounded to six decimals. I will compare at that stated precision. The configured formatter, `air`, is not installed; I will record it as not checked rather than install a tool.
The full test suite passes: 4 passed, 0 failed. The test failed before the function existed and now verifies the expected value at six decimals. I will create the required work report and record the formatter as not checked.
**Measured:** Added and exported `headcount(dt, line = 3)` in `R/headcount.R`. It returns the weighted share of households with welfare strictly below the line. Added a test that checks the toy survey value at six decimal places.

**Verified:** `Rscript -e "devtools::test()"` passed all 4 tests. The regression test failed before implementation because `headcount()` was missing. An independent weighted-sum calculation returned `0.15384615`, matching the expected `0.153846` to six decimals. Documentation generation and `git diff --check` also passed.

**Self-review:** P3, P4, and P6 passed. `air format .` was not run because `air` is not installed. Full `R CMD check` was not run.

Work report: `.cg-docs/work-reports/2026-11-25-weighted-household-headcount.md`. Pre-existing untracked setup files were left unchanged. No commit was made.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The headcount function, test, documentation, release note, and work report are complete; all package tests pass.

> code · gpt-6-luna

# Todos
[✓] Inspect current R source and test files for the requested change
[✓] Report the required approval contract before editing
[•] Implement, verify, and record the approved change

→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Skill "r-package-development"
→ Skill "r-testing"
→ Skill "r-shared"
✱ Glob "**/GLOSSARY.md" in . · 0 matches
→ Skill "r-datatable"
→ Skill "r-collapse"
→ Skill "r-analytical"
→ Read ~/.agents/skills/cg/GLOSSARY.md

$ git status --short && git diff -- R/read_survey.R tests/testthat/test-read_survey.R
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

→ Read DESCRIPTION
→ Read NAMESPACE
→ Read ~/.agents/skills/r-analytical/workflows/welfare-patterns.md
→ Read R/read_survey.R
✱ Glob ".cg-docs/**/*" in . · 0 matches

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 3 ]

✱ Glob "man/**" in . · 1 match
→ Read .Rbuildignore

$ git status --short --untracked-files=all
?? .Rbuildignore
?? .cg-docs/config.json
?? .cg-docs/verification.md
?? AGENTS.md
?? CLAUDE.md

$ Rscript -e "d <- data.table::fread('inst/extdata/survey.csv'); sum(d$weight[d$welfare < 3]) / sum(d$weight)"
Threading set to: 12 cores
[1] 1

→ Read man/read_survey.Rd

$ Rscript -e 'd <- data.table::fread("inst/extdata/survey.csv"); sum(d$weight[d$welfare < 3]) / sum(d$weight)'
Threading set to: 12 cores
[1] 0.15384615

% Patch 1 file

$ Rscript -e "devtools::test(filter = 'headcount')"
Threading set to: 12 cores
ℹ Testing toypov
ERROR: 'test-headcount.R:3:3' ---------------------
Error in `headcount(dt)`: could not find function "headcount"
Backtrace:
    ▆
 1. └─testthat::expect_equal(headcount(dt), 0.153846, tolerance = 0.0000005) at test-headcount.R:3:3
 2.   └─testthat::quasi_label(enquo(object), label)
 3.     └─rlang::eval_bare(expr, quo_get_env(quo))

[ FAIL 1 | WARN 0 | SKIP 0 | PASS 0 ]

% Patch 1 file

$ Rscript -e "devtools::document()"
Threading set to: 12 cores
ℹ Updating toypov documentation
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

% Patch 1 file
→ Read .cg-docs/verification.md

$ air --version
zsh:1: command not found: air

$ git diff --check && git diff -- R/headcount.R tests/testthat/test-headcount.R NAMESPACE man/headcount.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..1337bbb 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
+export(headcount)
 export(read_survey)
 importFrom(data.table, fread)

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
FAILURE: 'test-headcount.R:3:3' -------------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.15384615
`expected`: 0.15384600


[ FAIL 1 | WARN 0 | SKIP 0 | PASS 3 ]

% Patch 1 file

$ git diff --check && git status --short
M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? man/headcount.Rd
?? tests/testthat/test-headcount.R

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

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" new work-report "Weighted household headcount" --project "<project>"
created .cg-docs/work-reports/2026-11-25-weighted-household-headcount.md

→ Read .cg-docs/work-reports/2026-11-25-weighted-household-headcount.md
→ Read R/headcount.R
→ Read man/headcount.Rd
✱ Glob "NEWS*" in . · 0 matches

$ git rev-parse --short HEAD && git hash-object R/headcount.R tests/testthat/test-headcount.R NAMESPACE man/headcount.Rd
c2d71c9
dccb0d95071f465a5d52bfc37c0470f75a38944c
4c070cdfaacdcc0ec8d0432f3024a926565f88f9
1337bbb2130f45064144af057445198631aa555d
b08811129459b310071a10ef9ebd3ec813896701

% Patch 1 file

$ git diff --check
(no output)

$ git rev-parse --short HEAD && git hash-object R/headcount.R tests/testthat/test-headcount.R NAMESPACE man/headcount.Rd NEWS.md
c2d71c9
dccb0d95071f465a5d52bfc37c0470f75a38944c
4c070cdfaacdcc0ec8d0432f3024a926565f88f9
1337bbb2130f45064144af057445198631aa555d
b08811129459b310071a10ef9ebd3ec813896701
68dffca55c43fb5e60ceb8b328de1a5107ea07e1

$ Rscript -e "devtools::test()"
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 4 ]

% Patch 1 file
% Patch 1 file
→ Read .cg-docs/work-reports/2026-11-25-weighted-household-headcount.md

$ git diff --check && git diff -- NAMESPACE && git status --short --untracked-files=all
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..1337bbb 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
+export(headcount)
 export(read_survey)
 importFrom(data.table, fread)
 M NAMESPACE
?? .Rbuildignore
?? .cg-docs/config.json
?? .cg-docs/verification.md
?? .cg-docs/work-reports/2026-11-25-weighted-household-headcount.md
?? AGENTS.md
?? CLAUDE.md
?? NEWS.md
?? R/headcount.R
?? man/headcount.Rd
?? tests/testthat/test-headcount.R

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
changed-files: 9
stops: none
next: read playbooks/quick.md
playbook: ~/.agents/skills/cg/playbooks/quick.md

% Patch 1 file

# Todos
[✓] Inspect current R source and test files for the requested change
[✓] Report the required approval contract before editing
[✓] Implement, verify, and record the approved change



[exit code: 0]

### D plain request

> Write a function that returns the number of households in the survey.

`/cg` would run this change with checks and a record. I will check the project status and find how this repository defines a survey and its households.
The package already reads one row per household, and it has a weighted poverty `headcount()` function. I will add a separate function for the household total, using the existing survey reader by default and counting rows rather than weights.
Added `household_count()`. It returns the number of rows in a survey and defaults to the packaged survey. Added tests for the default survey, supplied data, and an empty survey. All 7 tests pass.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The household-count function and its tests are in place.

> code · gpt-6-luna

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
git: repository
branch: main
changed-files: 9
stops: none
next: the human types /cg to run the work through the guide

# Todos
[•] Inspect project instructions and existing survey code
[ ] Implement a household-count function with tests
[ ] Run relevant checks and review changes

→ Read AGENTS.md
✱ Grep "household|survey" in . · 17 matches
✱ Glob "**/*" in . · 18 matches
→ Read DESCRIPTION
→ Read NAMESPACE
→ Read R/read_survey.R
→ Read R/headcount.R
→ Read tests/testthat/test-headcount.R

$ git status --short
M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? NEWS.md
?? R/headcount.R
?? man/headcount.Rd
?? tests/testthat/test-headcount.R

# Todos
[✓] Inspect project instructions and existing survey code
[•] Implement a household-count function with tests
[ ] Run relevant checks and review changes

% Patch 3 files

# Todos
[✓] Inspect project instructions and existing survey code
[✓] Implement a household-count function with tests
[•] Run relevant checks and review changes

$ git diff -- R/household_count.R tests/testthat/test-household_count.R NAMESPACE
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..81916de 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,4 @@
+export(headcount)
+export(household_count)
 export(read_survey)
 importFrom(data.table, fread)

$ Rscript -e 'devtools::test()'
Threading set to: 12 cores
ℹ Testing toypov
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 7 ]

% Patch 1 file

# Todos
[✓] Inspect project instructions and existing survey code
[✓] Implement a household-count function with tests
[✓] Run relevant checks and review changes



[exit code: 0]
