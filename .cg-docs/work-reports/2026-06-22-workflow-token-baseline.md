# Workflow Token Baseline Execution Report

Plan reference: `.cg-docs/plans/2026-06-22-workflow-token-baseline.md`

Active deviation policy: stored `ask`; runtime override `autonomous` from `/cg-work review:auto deviate:auto`.

## Run: 2026-06-22

Status: in progress

### Completed Steps/Phases

- 2026-06-22: Phase 1 complete.
- Step 1: defined stable workflow telemetry registry in `scripts/cg_audit_context.py`.
- Step 2: added deterministic observability classification for workflow telemetry.

### Deviations

- None yet.

### Accepted Exceptions

- None.

### Evidence Table

| ID | Phase | Evidence Required | Status | Evidence |
|----|-------|-------------------|--------|----------|
| V1 | 1 | All nine requested workflows appear in the audit workflow registry and context map with stable unique IDs. | passed | `python3 -m pytest scripts/tests/test_audit_context.py -q` passed `87 passed`; temp audit `/tmp/cg-work-phase1-token-baseline/context-audit.json` produced 9 workflow telemetry rows and 10 benchmark rows including Knowledge Brain/context lookup. |
| V2 | 2 | Token artifact renderers can generate all five requested files with valid JSON/CSV/Markdown structure in a temporary output directory. | pending | `scripts/tests/test_audit_context.py` temp artifact assertions |
| V3 | 3 | Legacy `.cg-docs/cost/` outputs and `/cg-token-audit` deterministic-command behavior remain compatible. | pending | `.cg-docs/cost/context-audit.*`, `tests/prompt-tools.Tests.ps1` |
| V4 | 4 | Python audit/brain/team-brain tests are integrated through the safe runner or skipped when Python is unavailable. | pending | `tests/Run-Tests.ps1`, `tests/python-tests.Tests.ps1`, `tests/last-run.json` |
| V5 | final | Committed `.cg-docs/token/` baseline artifacts are generated after validation and do not recursively inflate source-token totals. | pending | `.cg-docs/token/*` |
| V6 | final | Audit guardrails remain zero-failure and reviewed warning `fix` count is zero or explicitly deferred with rationale. | pending | generated audit JSON/Markdown |
| V7 | final | No token-saving claim is made without same-probe before/after evidence. | pending | `.cg-docs/token/TOKEN-BUDGET.md` and docs |

### Constraints Check

| ID | Constraint | Status | Check |
|----|------------|--------|-------|
| C1 | Extend `scripts/cg_audit_context.py`; do not create a parallel analyzer. | passed | Phase 1 changes are limited to `scripts/cg_audit_context.py` and its tests. |
| C2 | Preserve `.cg-docs/cost/` output compatibility. | pending | Legacy output tests |
| C3 | Do not implement excluded Phase 1.2+ features. | pending | Diff review |
| C4 | Preserve Pester safety. | pending | Safe runner / static tests |
| C5 | Preserve statistical correctness and review depth. | pending | Diff review |
| C6 | Preserve roadmap write discipline. | pending | No direct implementation-agent roadmap edits |
| C7 | Preserve evidence-before-completion behavior. | passed | Phase 1 completion recorded after pytest, py_compile, temp audit, diff check, and full safe runner passed. |
| C8 | Exclude generated `.cg-docs/cost/` and `.cg-docs/token/` outputs from workflow source-token totals by default. | pending | Audit schema/tests in Phase 2. |

### Remaining Uncertainty

- PowerShell/Pester is available in this Codex environment. Full safe runner passed through `Run-Tests.ps1`.
- Phase 2 still needs token artifact renderers and self-scan exclusion tests.

### Evidence Runs

- Red phase: `python3 -m pytest scripts/tests/test_audit_context.py -q` failed with missing `WORKFLOW_REGISTRY`, telemetry, and observability functions.
- Phase 1 targeted tests: `python3 -m pytest scripts/tests/test_audit_context.py -q` passed `87 passed`.
- Compile check: `python3 -m py_compile scripts/cg_audit_context.py` passed.
- Temp audit: `python3 scripts/cg_audit_context.py --root . --output-dir /tmp/cg-work-phase1-token-baseline --format json` passed.
- Temp audit evidence: 9 workflow telemetry rows, 10 benchmark rows including Knowledge Brain/context lookup, 0 guardrail failures, reviewed warning `fix=0`.
- Full safe runner: `. ./tests/Run-Tests.ps1` via PowerShell passed `2194/2194`, `filteredFiles: null`.

### Final Status

Phase 1 complete; paused before Phase 2.
