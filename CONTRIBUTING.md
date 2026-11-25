# Contributing

Version 2 is being built on branch `v2`. Start with `docs/v2/HANDOFF.md`, which lists the state of the build and the working rules.

A change to core has to clear the bar in `SCOPE.md`: an observed failure, and a fit with the principles. Read `.out-of-scope/` before proposing one.

## Checks to run before a commit

```
python3 tools/check_glossary.py packs docs/adr docs/v2 docs/adoption-ledger.md SCOPE.md .out-of-scope spike README.md CONTRIBUTING.md AGENTS.md docs/install-block.md
python3 tools/sync_version.py --check
python3 tools/lint_skills.py packs
python3 tools/validate_pack.py
python3 tools/check_budgets.py
python3 -m pytest -q
```

Read each exit code directly. CI (`.github/workflows/v2.yml`) runs the same checks, and runs the tests on Linux, macOS and Windows.

## Commits

Conventional commit messages (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`), small and often. A change to what a human types or sees updates the documentation in the same commit.
