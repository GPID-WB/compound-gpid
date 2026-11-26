### B1 setup

> [the text of the installed cg/SKILL.md]

**Recommended setup:** use `core` and `lang-r`. Both packs are installed.

- **R setting:** `lang-r.r-syntax=data.table-collapse`. The package imports `data.table`; `R/read_survey.R` calls `fread()`.
- **Verification draft:** Run command: `not found`. The repository has tests, but it has no command that produces outputs. Doctor command: `not found`. No environment-check command is defined. The package provides `read_survey()`; its test checks for 20 rows and the columns `hhid`, `welfare`, and `weight`. I did not run the tests.
- **Data rule:** I found one data file, `inst/extdata/survey.csv`. I did not open it. Its classification and the highest level Kilo Code may read are not set. I also need your organization’s classification levels, if you know them.

The setup preview lists these files to create or change: `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.

Assumption: because this is an R package with `DESCRIPTION` at its root, `.Rbuildignore` applies.

To continue, confirm or correct the pack, setting, and preview. In the same reply, give the data details in this form: `inst/extdata/survey.csv=Public; Kilo Code may read=Public; classification levels=Public;Internal;Restricted`. Replace those example levels with your organization’s terms.

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

→ Read LICENSE
→ Read DESCRIPTION
→ Read tests/testthat.R
→ Read R/read_survey.R
→ Read tests/testthat/test-read_survey.R
→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read NAMESPACE
→ Read ~/.agents/skills/cg/templates/pointer-block.md
→ Read ~/.agents/skills/cg/templates/verification.md

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

The confirmation sets the survey classification and Kilo Code’s read limit to Public. I will preview the exact setup changes, then write the confirmed configuration.
The preview contains the five expected files. I will run setup with the confirmed pack, setting, data rule, and Kilo Code read limit.
Setup is ready. The survey file is classified as Public, and Kilo Code may read Public data.

- Status: `phase: ready`; `stops: none`; `packs-missing: none`.
- Settings: `lang-r.r-syntax=data.table-collapse`.
- Created: `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.
- The verification profile remains a draft. No Run or Doctor command was found, and I did not run the tests.
- The organization’s full classification-level list was not provided.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** Compound GPID setup is ready. The verification profile is still a draft.

> code · gpt-6-luna

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" setup --packs "core,lang-r" --setting "lang-r.r-syntax=data.table-collapse" --data "inst/extdata/survey.csv=Public" --approved-tool "Kilo Code=Public" --project "<project>" --dry-run
would create .cg-docs/config.json
would create .cg-docs/verification.md
would create AGENTS.md
would create CLAUDE.md
would create .Rbuildignore

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

> [the text of the installed cg/SKILL.md]

Add a function `headcount(dt, line = 3)` that returns the weighted share of households with welfare below the line, with a testthat check. For the toy survey I expect 0.153846.

`/cg` would run this change with checks and a record. I will read the Compound GPID state first, then follow its selected playbook.
The project is ready with no recorded blocker. The selected playbook is `quick.md`; I will read it and the project vocabulary before changing code.
I will add an exported `headcount()` that computes the weighted share using `collapse::fmean`, without changing `read_survey()` or the survey data. The work changes a numeric output and adds a public function; it is reversible, has no unresolved method choice, and has a test with the expected value as the independent reference. I will use the package’s shipped toy survey in that test.
The risk check returned `tier: elevated` because `headcount()` computes a number and adds a public function to the package interface. The survey file is cleared for Kilo Code to read.

**Contract**
- **Goal:** Add an exported `headcount(dt, line = 3)` function and a test that checks the toy survey returns `0.153846`.
- **Out of scope:** No changes to the survey data or to `read_survey()`.
- **Checks:** Run the new test and the package test suite. Failure means the new test does not pass or the package test suite reports an error.

Reply **yes** to approve this contract. I will make no code changes until then.

**Next steps: Waiting on you**
* **Your move:** Reply `yes` to approve the contract.
* **Project:** The change is not started. The risk check requires approval before implementation.

> code · gpt-6-luna

→ Skill "cg"
→ Read ~/.cg/launcher.json

$ git status --short --branch
## main
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md

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

→ Read ~/.agents/skills/cg/GLOSSARY.md
→ Read ~/.agents/skills/cg/playbooks/quick.md
✱ Glob "GLOSSARY.md" in . · 0 matches
→ Read ~/.agents/skills/cg/principles/README.md
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

# Todos
[•] Read R guidance, inspect code and determine change risk
[ ] Implement headcount and its test
[ ] Run checks, self-review, and record the work

→ Read DESCRIPTION
→ Read R/read_survey.R
→ Read .cg-docs/verification.md
→ Read .cg-docs/config.json
→ Skill "r-shared"
→ Read tests/testthat/test-read_survey.R
→ Skill "r-analytical"
→ Skill "r-datatable"
→ Skill "r-collapse"
→ Skill "r-testing"
→ Read ~/.agents/skills/r-analytical/workflows/welfare-patterns.md

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" tier --fact number=yes --fact personal=no --fact irreversible=no --fact interface=yes --fact choice=no --fact no-check=no --touches "R/read_survey.R" --touches "tests/testthat/test-read_survey.R" --touches "NAMESPACE" --touches "man/headcount.Rd" --reads "inst/extdata/survey.csv" --agent "Kilo Code" --project "<project>"
tier: elevated
reasons: number: it computes a number someone will read, or can change one; interface: it adds or upgrades a dependency, or alters something other code or other people rely on
data: inst/extdata/survey.csv=Public: cleared (its level is Public)
files: 4



[exit code: 0]

### C2 yes

> Yes, proceed.

The contract is approved. I will confirm the current Compound GPID state, then implement the function and test, run the checks, and write the required work report.
The survey has one row per household and columns `welfare` and `weight`. At line 3, the below-line weights total 6 and all weights total 39, so the reference share is `6 / 39 = 0.153846...`. I will use base R’s weighted mean to avoid adding a dependency, and reject missing or non-positive welfare and weights instead of silently dropping rows.
The first test run found two errors in my test expectation: the stated decimal needs the survey’s exact weighted fraction, and my second threshold calculation used the wrong total weight. The implementation returned `0.1538462` at line 3. I will correct the test references using the survey weights, then rerun the suite.
The corrected suite passes. I also generated the manual page with roxygen2; it reported that the existing `NAMESPACE` is not roxygen-managed, so I kept the explicit export entry. The function documentation needs a runnable example, so I will add one, regenerate the manual page, and run the checks again.
**Measured:** Added and exported `headcount(dt, line = 3)`. It returns the weighted share of households with welfare strictly below the line. The toy survey returns `0.1538462`, which rounds to your expected `0.153846`.

**Verified:**
- `Rscript -e 'testthat::test_local()'` passed: 6 passes, no failures.
- `Rscript -e 'devtools::run_examples()'` passed.
- `git diff --check` passed.
- The Compound GPID work report validated with no problems or warnings.

The function and test are in `R/headcount.R` and `tests/testthat/test-headcount.R`. The exported function is documented in `man/headcount.Rd`. The report is `.cg-docs/work-reports/2026-11-26-add-weighted-headcount.md`.

**Not checked:** Full `R CMD check` was not run. The project’s verification profile has no Doctor or Run command.

**Self-review:** P3, P4 and P6 pass. Existing untracked files were left unchanged.

**Next steps: Done**
* **Your move:** Nothing.
* **Project:** The weighted headcount function, test and work report are complete; full `R CMD check` remains unrun.

> code · gpt-6-luna

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

# Todos
[✓] Read R guidance, inspect code and determine change risk
[•] Implement headcount and its test
[ ] Run checks, self-review, and record the work

→ Read ~/.agents/skills/cg/principles/P03-deterministic-by-default.md
→ Read NAMESPACE
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/principles/P12-governed-data.md
→ Read ~/.agents/skills/cg/principles/P06-smallest-change.md
→ Read ~/.agents/skills/cg/principles/P10-correct-in-the-domain.md
→ Read ~/.agents/skills/cg/principles/P07-honest-claims.md
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
    approve             record the human's yes to a plan or an intent, or
                        their decision on data
    tier                compute the risk level of a piece of work from
                        declared facts

options:
  -h, --help            show this help message and exit

% Patch 4 files

# Todos
[✓] Read R guidance, inspect code and determine change risk
[✓] Implement headcount and its test
[•] Run checks, self-review, and record the work

$ git diff --check
(no output)

$ git diff -- R/headcount.R tests/testthat/test-headcount.R NAMESPACE man/headcount.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)

$ Rscript -e 'testthat::test_local()'
Threading set to: 12 cores
FAILURE: 'test-headcount.R:4:3' -------------------
Expected `headcount(dt)` to equal 0.153846.
Differences:
  `actual`: 0.1538462
`expected`: 0.1538460


FAILURE: 'test-headcount.R:5:3' -------------------
Expected `headcount(dt, line = 5)` to equal `18/39`.
Differences:
  `actual`: 0.396
`expected`: 0.462


[ FAIL 2 | WARN 0 | SKIP 0 | PASS 4 ]
Error:
! Test failures.
Execution halted

% Patch 1 file

$ git diff --check
(no output)

$ Rscript -e 'testthat::test_local()'
Threading set to: 12 cores
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 6 ]

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
% Patch 1 file

$ git rev-parse --short HEAD
72eb799

$ git status --short
M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? man/headcount.Rd
?? tests/testthat/test-headcount.R

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

$ Rscript -e 'roxygen2::roxygenise()'
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

% Patch 1 file

$ Rscript -e 'roxygen2::roxygenise()'
Threading set to: 12 cores
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
Writing 'headcount.Rd'

$ git diff --check
(no output)

$ Rscript -e 'testthat::test_local()'
Threading set to: 12 cores
[ FAIL 0 | WARN 0 | SKIP 0 | PASS 6 ]

$ Rscript -e 'devtools::run_examples()'
Threading set to: 12 cores
ℹ Updating toypov documentation
ℹ Loading toypov
✖ Skipping NAMESPACE
  (<file://<project>/NAMESPACE>)
ℹ It already exists and was not generated by roxygen2.
── Running 2 example files ─────────────────────────────────────────── toypov ──
ℹ Loading toypov

R> dt <- data.table::data.table(welfare = c(1, 4), weight = c(1, 
...     1))

R> headcount(dt)
[1] 0.5
ℹ Loading toypov

→ Read man/headcount.Rd

$ git hash-object man/headcount.Rd
d987adf4372903323ad362b8b1d96f6a6e6bd18d

$ git diff -- R/headcount.R tests/testthat/test-headcount.R NAMESPACE man/headcount.Rd
diff --git a/NAMESPACE b/NAMESPACE
index f0fd4ca..6419142 100644
--- a/NAMESPACE
+++ b/NAMESPACE
@@ -1,2 +1,3 @@
 export(read_survey)
+export(headcount)
 importFrom(data.table, fread)

→ Read man/read_survey.Rd
% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

% Patch 1 file

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

% Patch 1 file

$ git diff --check
(no output)

$ git status --short
M NAMESPACE
?? .Rbuildignore
?? .cg-docs/
?? AGENTS.md
?? CLAUDE.md
?? R/headcount.R
?? man/headcount.Rd
?? tests/testthat/test-headcount.R

$ "/opt/homebrew/opt/python@3.14/bin/python3.14" "~/.agents/skills/cg/scripts/cg.py" validate ".cg-docs/work-reports/2026-11-26-add-weighted-headcount.md" --project "<project>"
schema-2: 1
version-1: 0 (read as they are)
problems: 0
warnings: 0

# Todos
[✓] Read R guidance, inspect code and determine change risk
[✓] Implement headcount and its test
[✓] Run checks, self-review, and record the work



[exit code: 0]
