# Workflow Token Baseline Execution Report

Plan reference: `.cg-docs/plans/2026-06-22-workflow-token-baseline.md`

Active deviation policy: stored `ask`; runtime override `autonomous` from `/cg-work review:auto deviate:auto`.

## Run: 2026-06-22

Status: completed

### Completed Steps/Phases

- 2026-06-22: Phase 1 complete.
- 2026-06-23: Phases 2-5 reconciled as complete after existing commits, verification review fixes, and current validation rerun.
- Step 1: defined stable workflow telemetry registry in `scripts/cg_audit_context.py`.
- Step 2: added deterministic observability classification for workflow telemetry.
- Steps 3-4: added token artifact renderers and preserved legacy `.cg-docs/cost/` behavior.
- Step 5: updated `/cg-token-audit` prompt/docs for additive `.cg-docs/token/` artifacts.
- Steps 6-7: expanded Python audit schema tests and validated through the canonical safe runner.
- Steps 8-9: generated baseline artifacts and reconciled roadmap linkage/status.

### Deviations

- None yet.

### Accepted Exceptions

- None.

### Evidence Table

| ID | Phase | Evidence Required | Status | Evidence |
|----|-------|-------------------|--------|----------|
| V1 | 1 | All nine requested workflows appear in the audit workflow registry and context map with stable unique IDs. | passed | `python3 -m pytest scripts/tests/test_audit_context.py -q` passed `87 passed`; temp audit `/tmp/cg-work-phase1-token-baseline/context-audit.json` produced 9 workflow telemetry rows and 10 benchmark rows including Knowledge Brain/context lookup. |
| V2 | 2 | Token artifact renderers can generate all five requested files with valid JSON/CSV/Markdown structure in a temporary output directory. | passed | `python3 -m pytest scripts/tests/test_audit_context.py -q` passed `92 passed`; temp audit generated `TOKEN-BUDGET.md`, `token-audit.json`, `context-map.json`, `workflow-costs.csv`, and `large-context-warnings.md`. |
| V3 | 3 | Legacy `.cg-docs/cost/` outputs and `/cg-token-audit` deterministic-command behavior remain compatible. | passed | `python3 scripts/cg_audit_context.py --root . --output-dir /tmp/cg-token-check-cost --token-output-dir /tmp/cg-token-check-token --format both --recommendations` wrote legacy cost reports and token artifacts; `tests/prompt-tools.Tests.ps1` passed through safe runner. |
| V4 | 4 | Python audit/brain/team-brain tests are integrated through the safe runner or skipped when Python is unavailable. | passed | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` passed `2200/2200`, `filteredFiles: null`, with result recorded in `tests/last-run.json`. |
| V5 | final | Committed `.cg-docs/token/` baseline artifacts are generated after validation and do not recursively inflate source-token totals. | passed | Committed artifacts exist under `.cg-docs/token/`; pytest covers scan exclusion for generated `.cg-docs/cost/` and `.cg-docs/token/` outputs. |
| V6 | final | Audit guardrails remain zero-failure and reviewed warning `fix` count is zero or explicitly deferred with rationale. | passed | Temp `token-audit.json` reported `guardrail failures=0` and reviewed warning `fix=0`. |
| V7 | final | No token-saving claim is made without same-probe before/after evidence. | passed | `TOKEN-BUDGET.md` and docs frame Phase 1.1 as baseline evidence, not savings proof; pytest asserts the generated budget says it is not evidence of token savings. |

### Constraints Check

| ID | Constraint | Status | Check |
|----|------------|--------|-------|
| C1 | Extend `scripts/cg_audit_context.py`; do not create a parallel analyzer. | passed | Phase 1 changes are limited to `scripts/cg_audit_context.py` and its tests. |
| C2 | Preserve `.cg-docs/cost/` output compatibility. | passed | Legacy output command still writes `context-audit.json`, `context-audit.md`, and `token-advice.md`; pytest covers `--no-token-artifacts`. |
| C3 | Do not implement excluded Phase 1.2+ features. | passed | Review scope and diff are limited to baseline telemetry/artifacts, docs, scanner warning cleanup, and tests. |
| C4 | Preserve Pester safety. | passed | Safe runner passed; `pester-safety` and `run-tests-runner` suites passed through `Run-Tests.ps1`. |
| C5 | Preserve statistical correctness and review depth. | passed | No analytical/statistical logic or review-routing downgrade was introduced. |
| C6 | Preserve roadmap write discipline. | passed | Roadmap reconciliation followed the local `@cg-roadmap` manager contract: plan exists, feature status set to `done`, milestone status derived as `in-progress`. |
| C7 | Preserve evidence-before-completion behavior. | passed | Phase 1 completion recorded after pytest, py_compile, temp audit, diff check, and full safe runner passed. |
| C8 | Exclude generated `.cg-docs/cost/` and `.cg-docs/token/` outputs from workflow source-token totals by default. | passed | `test_workflow_telemetry_tracks_generated_report_reads_without_scanning_outputs` verifies generated cost/token artifacts are referenced but not scanned as source-token files. |

### Remaining Uncertainty

- The originally planned `tests/python-tests.Tests.ps1` wrapper file is not present. Current validation still covers Python audit behavior through pytest and the canonical Pester suite; no separate Python wrapper evidence exists.
- Token estimates remain heuristic `chars/4` baseline evidence and are not claims of savings.

### Evidence Runs

- Red phase: `python3 -m pytest scripts/tests/test_audit_context.py -q` failed with missing `WORKFLOW_REGISTRY`, telemetry, and observability functions.
- Phase 1 targeted tests: `python3 -m pytest scripts/tests/test_audit_context.py -q` passed `87 passed`.
- Compile check: `python3 -m py_compile scripts/cg_audit_context.py` passed.
- Temp audit: `python3 scripts/cg_audit_context.py --root . --output-dir /tmp/cg-work-phase1-token-baseline --format json` passed.
- Temp audit evidence: 9 workflow telemetry rows, 10 benchmark rows including Knowledge Brain/context lookup, 0 guardrail failures, reviewed warning `fix=0`.
- Full safe runner: `. ./tests/Run-Tests.ps1` via PowerShell passed `2194/2194`, `filteredFiles: null`.
- Current Python audit tests: `python3 -m pytest scripts/tests/test_audit_context.py -q` passed `92 passed`.
- Current temp audit: `python3 scripts/cg_audit_context.py --root . --output-dir /tmp/cg-token-check-cost --token-output-dir /tmp/cg-token-check-token --format both --recommendations` passed and wrote legacy cost plus token artifacts.
- Current temp artifact parse: `token-audit.json` schema version `1`, workflow rows `9`, guardrail failures `0`, reviewed warning fix count `0`.
- Current full safe runner: `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` passed `2200/2200`, `filteredFiles: null`, `gitSha: d10178b`, `ranAt: 2026-06-23T17:11:20Z`.
- `git diff --check` passed.

### Final Status

Completed.
