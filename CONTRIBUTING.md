# Contributing

Version 2 is being built on branch `v2`. Start with `docs/v2/HANDOFF.md`, which lists the state of the build and the working rules.

A change to core has to clear the bar in `SCOPE.md`: an observed failure, and a fit with the principles. Read `.out-of-scope/` before proposing one.

## Checks to run before a commit

```
python3 tools/check_glossary.py packs docs/adr docs/v2 docs/adoption-ledger.md SCOPE.md .out-of-scope spike
python3 tools/sync_version.py --check
```

Read each exit code directly. CI runs the same checks.

## Commits

Conventional commit messages (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`), small and often. A change to what a human types or sees updates the documentation in the same commit.
