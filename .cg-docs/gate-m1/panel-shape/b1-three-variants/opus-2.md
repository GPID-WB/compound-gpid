### B1 opus 2

> [the body of this variant's SKILL.md]


Base directory for this skill: ~/.agents/skills/cg
Relative paths in this skill (e.g., scripts/, references/) are relative to this base directory.

**Measured:** The project is an R package. It has 8 listed files: 6 R files and 1 CSV, plus `DESCRIPTION`. The data file is `inst/extdata/survey.csv`. I did not open it.

**Recommended setup:**
- Packs: `core` and `lang-r`. Both are installed.
- Setting: `lang-r.r-syntax=data.table-collapse`. `DESCRIPTION` lists `data.table` as an import, and `R/read_survey.R` uses `fread()`. This matches the installed default.
- Verification profile: Run command: **not found**. Doctor command: **not found**. I found no command that builds outputs or checks the environment. The package exposes `read_survey()`; its return value is the output. The test file expects 20 rows and three named columns, but I did not run it or inspect the data.
- Files the setup command would write, from its dry run: `.cg-docs/config.json`, `.cg-docs/verification.md`, `AGENTS.md`, `CLAUDE.md`, and `.Rbuildignore`.

**Decision needed:** What classification applies to `inst/extdata/survey.csv`, what is the highest classification this coding agent may read, and what are your organization’s classification levels from public to most restricted? Please also confirm the proposed setup.

Example reply: `survey.csv: Public; agent approved through Public; levels: Public, Internal, Restricted; yes`

Assumptions: I treated the root `DESCRIPTION` as evidence that this is an R package. I inferred the R setting from the code and package imports. I did not inspect the CSV or run package checks. This follows P2 (the human decides) and P12 (governed data).

**Next steps: Waiting on you**
* **Your move:** Reply with the classifications and a clear `yes`, using the example above as a template.
* **Project:** Setup is not written yet. The verification profile has no confirmed Run or Doctor command.

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

✗ Read ~/.agents/skills/cg/principles/P12-data-boundaries.md failed
Error: File not found: ~/.agents/skills/cg/principles/P12-data-boundaries.md
→ Read DESCRIPTION
→ Read ~/.agents/skills/r-shared/SKILL.md
→ Read ~/.agents/skills/cg/principles/README.md
→ Read ~/.agents/skills/cg/principles/P04-prove-it-works.md
→ Read ~/.agents/skills/cg/GLOSSARY.md
→ Read ~/.agents/skills/cg/principles/P02-human-decides.md
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

→ Read tests/testthat.R
→ Read ~/.agents/skills/cg/principles/P12-governed-data.md
→ Read ~/.agents/skills/cg/templates/verification.md
✱ Glob "{AGENTS.md,CLAUDE.md,GLOSSARY.md,.Rbuildignore,_targets.R,Makefile,renv.lock,.cg-docs/**,compound-gpid*,.github/copilot-instructions.md}" in . · 0 matches

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
