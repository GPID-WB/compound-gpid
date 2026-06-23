# Cross-Agent Packaging Adapters Execution Report

Plan reference: `.cg-docs/plans/2026-06-23-cross-agent-packaging-adapters.md`

Active deviation policy: stored `autonomous`; runtime override `autonomous` from `/cg-work review:auto deviate:auto`.

## Run: 2026-06-23

Status: completed

### Completed Steps/Phases

- Phase 1: added an opt-in adapter source package under `adapters/` for Codex and Claude Code.
- Phase 2: added Python regression tests for manifest shape, adapter existence, core dispatch contract phrases, and README boundaries; updated docs for discoverability.
- Phase 3: recorded review/evidence, added a solution note, and linked roadmap Phase 2.1 as done.

### Deviations

- Kept the feature source-package only. No `cg-link`, `cg-update`, installer, or `.github/` managed-directory behavior was changed.

### Accepted Exceptions

- Adapter installation remains a manual copy step. Automatic install/link behavior is out of scope for Phase 2.1.

### Evidence Table

| ID | Phase | Evidence Required | Status | Evidence |
|----|-------|-------------------|--------|----------|
| V1 | 1 | Adapter package files exist with required contract sections. | passed | `python3 -m pytest scripts/tests/test_agent_adapters.py -q` -> `5 passed`. |
| V2 | 2 | Prompt/docs checks pass. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` -> `1339 passed, 0 failed`. |
| V3 | final | Broader Python tests pass. | passed | `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q` -> `664 passed, 17 warnings, 5 subtests passed`. |
| V4 | final | Full safe runner passes. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` -> `2210 passed, 0 failed`. |
| V5 | final | Roadmap feature is done and linked to this plan. | passed | `roadmap.json` feature status `done`, plan `.cg-docs/plans/2026-06-23-cross-agent-packaging-adapters.md`. |
| V6 | final | Brain and token audit artifacts are refreshed. | passed | `./bin/cg-index --brain` -> `534 entities, 2 topics, 215 edges`; audit -> `baseline`, failures `0`, warnings `3`, estimated source tokens `440352`. |

### Constraints Check

| ID | Constraint | Status | Check |
|----|------------|--------|-------|
| C1 | Adapters remain opt-in and root-level, not Copilot-managed. | passed | `adapters/README.md`, docs, and diff review; no link/update scripts changed. |
| C2 | No retrieval backend, external research, or snapshot implementation. | passed | Diff is adapter package/docs/tests/evidence only. |
| C3 | Safe Pester runner only. | passed | Pester validation used `tests/Run-Tests.ps1`; no direct unsafe `Invoke-Pester`. |

### Evidence Runs

- `python3 -m pytest scripts/tests/test_agent_adapters.py -q` -> `5 passed`.
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` -> `1339 passed, 0 failed`.
- `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q` -> `664 passed, 17 warnings, 5 subtests passed`.
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` -> `2210 passed, 0 failed`.
- `./bin/cg-index --brain` -> `534 entities, 2 topics, 215 edges`; existing frontmatter/scanner warnings only.
- `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations` -> final regression status `baseline`, failures `0`, warnings `3`, comparison `not_supplied`, source files `90`, estimated source tokens `440352`.

### Remaining Uncertainty

- Consumer repositories must copy adapters intentionally. This phase does not add an installer command or migration that detects desired agent families.

### Final Status

Completed.
