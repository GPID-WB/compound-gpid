---
type: verification-profile
status: draft
---

# Verification profile

How this project is run and checked (principle P4). The status stays `draft` until the Run command has been run from start to finish. Fix this file before using it whenever it no longer matches the project.

## Run

The one command that produces the outputs from the inputs:

```
not found
```

This repository has no build step: the packs are written, not generated.

## Doctor

One command that only reads, and shows the environment is fit to run (package versions, data vintage present, credentials valid):

```
python3 packs/core/cg/scripts/cg.py doctor --project .
```

## Outputs map

| Output | Where it lives | What proves it right |
|---|---|---|
| The core tooling | `packs/core/cg/scripts/cg.py` | `uvx --offline pytest -q tests/core` |
| The installer and the hub tools | `install.py`, `tools/` | `uvx --offline pytest -q tests/hub` |
| The guide and the playbooks | `packs/core/cg/SKILL.md`, `packs/core/cg/playbooks/` | `python3 spike/gate/run_cli_gate.py --kilo-model openai/gpt-6-luna`: each agent passes every step |
| The packs and their skills | `packs/` | `python3 tools/validate_pack.py`, `python3 tools/lint_skills.py packs`, `python3 tools/sync_version.py --check` |
| The wording | every file the glossary covers | `python3 tools/check_glossary.py` |
| The size of the tooling and the tests | `SCOPE.md` | `python3 tools/check_budgets.py` |

The checks are the ones `CONTRIBUTING.md` lists. `uvx --offline` runs pytest from the local cache, since the package index is not always reachable from this machine. CI (`.github/workflows/v2.yml`) runs them on Linux, macOS and Windows.

## Evidence

Evidence is kept in `.cg-docs/work-reports/`. It holds commands, exit codes, digests and counts, and never data.
