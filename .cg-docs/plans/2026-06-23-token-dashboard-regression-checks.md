---
date: 2026-06-23
title: "Token Dashboard and Regression Checks"
status: completed
completed-date: 2026-06-23
execution-report: .cg-docs/work-reports/2026-06-23-token-dashboard-regression-checks.md
scope: "Standard"
brainstorm: null
language: "Python/PowerShell/Markdown"
estimated-effort: "medium"
deviation-policy: "autonomous"
tags: [token-efficiency, dashboard, regression, audit, validation]
phases: 3
completed-phases: [1, 2, 3]
roadmap-features:
  - token-efficiency-core-system/phase-1-6-token-dashboard-regression
---

# Plan: Token Dashboard and Regression Checks

## Objective

Complete Phase 1.6 by turning the existing workflow token baseline into a
maintainer-facing dashboard and deterministic regression check surface. The
work must make token pressure visible and comparable without claiming savings
unless measured by comparable repository probes.

## Context

Phase 1.1 already added `.cg-docs/token/` baseline artifacts and the audit
script already supports `--baseline` comparison. Phase 1.6 should build on that
same deterministic audit layer rather than introduce a second analyzer. The
current gap is that maintainers have machine-readable baseline files, but no
single dashboard artifact or explicit pass/fail regression summary that can be
used during future token-efficiency work.

Brain findings:

- Extend `scripts/cg_audit_context.py` for token/context measurement rather
  than creating a parallel analyzer -- source:
  `.cg-docs/plans/2026-06-16-token-context-optimization-closure.md`.
- Keep token estimates as `chars/4` heuristic and label any savings claims as
  hypotheses until comparable probes exist -- source:
  `.cg-docs/plans/2026-06-22-workflow-token-baseline.md`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Add a human-readable token dashboard artifact under `.cg-docs/token/`. | roadmap Phase 1.6 |
| R2 | Add a machine-readable regression summary that reports guardrail and workflow-budget status. | roadmap Phase 1.6 |
| R3 | Reuse the existing audit report and `--baseline` comparison flow; do not create a parallel analyzer. | prior token-audit pattern |
| R4 | Keep all regression thresholds deterministic and based on current audit data. | evidence requirements |
| R5 | Preserve the no-savings-claim policy and measurement disclaimers. | objective |
| R6 | Keep `.cg-docs/cost/` compatibility and existing token baseline artifacts stable. | Phase 1.1 |
| R7 | Add tests that fail if dashboard/regression artifacts disappear or misreport status. | project testing pattern |
| R8 | Update discoverability docs and `/cg-token-audit` wording for the new artifacts. | user-facing command convention |
| R9 | Mark the roadmap feature complete only after validation and evidence artifacts exist. | goal workflow |

## Implementation Steps

## Phase 1: Artifact Model

### 1. Define dashboard and regression payloads

- **Requirements**: R1, R2, R3, R4, R5, R6
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
- **Details**:
  - Add `TOKEN-DASHBOARD.md` and `regression-check.json` to the token artifact
    family.
  - Render dashboard sections for source scope, regression status, highest
    workflow budgets, context-risk summary, reviewed warning counts, and
    observability boundaries.
  - Build a JSON regression summary with stable fields for `status`,
    `failures`, `warnings`, `workflow_budget`, `comparison`, and
    `measurement_policy`.
  - Treat absent baseline comparison as `status: "baseline"` rather than pass
    or fail.
  - Fail regression status only for deterministic guardrail failures already
    produced by `build_guardrails`, including the existing high-frequency and
    always-on token thresholds.
- **Test Scenarios**: current baseline, guardrail failure, workflow over budget,
  baseline comparison present.
- **Tests**: `python3 -m pytest scripts/tests/test_audit_context.py -q`.
- **Acceptance criteria**: both artifacts are written by default and existing
  artifacts keep their schema.

## Phase 2: User-Facing Surface

### 2. Update prompt and documentation references

- **Requirements**: R5, R8
- **Files**:
  - `.github/prompts/cg-token-audit.prompt.md`
  - `docs/reference.md`
  - `docs/workflow.md`
- **Details**:
  - Mention that `/cg-token-audit` now writes the dashboard and regression
    check in addition to baseline artifacts.
  - Document how to interpret `baseline`, `pass`, and `fail` without implying
    savings.
  - Keep context-loading wording targeted; do not ask agents to read all
    generated artifacts by default.
- **Tests**: existing prompt/docs tests plus focused text assertions if needed.
- **Acceptance criteria**: users can discover the dashboard and regression
  check from command reference and workflow docs.

## Phase 3: Evidence and Roadmap Closure

### 3. Validate, regenerate, review, and close roadmap status

- **Requirements**: R7, R9
- **Files**:
  - `.cg-docs/token/*`
  - `.cg-docs/cost/*`
  - `.cg-docs/work-reports/2026-06-23-token-dashboard-regression-checks.md`
  - `.cg-docs/reviews/*token-dashboard-regression*`
  - `.cg-docs/solutions/testing-patterns/*token-dashboard-regression*`
  - `roadmap.json`
- **Details**:
  - Regenerate audit artifacts with the repository-local audit script.
  - Record implementation and verify review evidence.
  - Add a focused solution note only after validation passes.
  - Update the roadmap feature to `done` with this plan path.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_audit_context.py -q`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"`
  - `git diff --check`
- **Acceptance criteria**: tests pass, artifacts are internally consistent, and
  feature-scoped changes are committed.

## Testing Strategy

Use focused Python tests while shaping the artifact contract, then the safe
Pester runner for prompt/docs coverage and the full regression gate before
commit. Any token-regression claim must cite `regression-check.json` or an
explicit baseline comparison produced by the audit script.

## Documentation Checklist

- `docs/reference.md` lists all token artifacts.
- `docs/workflow.md` explains the dashboard/regression interpretation.
- `/cg-token-audit` prompt points to compact outputs only.
- Evidence files record commands and outcomes.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Dashboard reads as a token-savings claim | Repeat the measurement policy and baseline-only wording. |
| Regression status becomes subjective | Use only deterministic guardrail failures and documented workflow thresholds. |
| Generated artifacts inflate future scans | Preserve the existing generated-artifact exclusion policy. |
| Baseline comparison is absent on normal runs | Represent it explicitly as `baseline`, not `pass`. |

## Out of Scope

- External services, optional retrieval backends, vector stores, or snapshots.
- Cross-agent packaging adapters.
- Runtime transcript instrumentation beyond existing command summary artifacts.
- Prompt slimming or skill rewrites unrelated to dashboard/regression output.

## Completion Contract

### Outcome

Phase 1.6 is complete when `/cg-token-audit` writes a dashboard and regression
summary, tests protect their schema/status semantics, documentation explains
their interpretation, and roadmap evidence is committed.

### Verification Surface

| ID | Evidence Required | Command/Artifact | Required |
|----|-------------------|------------------|----------|
| V1 | Focused Python artifact tests pass | `python3 -m pytest scripts/tests/test_audit_context.py -q` | yes |
| V2 | Prompt/docs checks pass | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` | yes |
| V3 | Full safe regression gate passes | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |
| V4 | Generated artifacts include dashboard and regression summary | `.cg-docs/token/TOKEN-DASHBOARD.md`, `.cg-docs/token/regression-check.json` | yes |
| V5 | Roadmap feature is done and linked to this plan | `roadmap.json` | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | No token-saving claim without comparable measurements | docs/artifact review |
| C2 | No external backend, adapter, or snapshot work | git diff review |
| C3 | Safe Pester runner only | command history and evidence |

### Blocked-Stop Conditions

- New statistical/model-governance guardrail failure that cannot be resolved in
  this feature scope.
- Regression status requires subjective model interpretation.
- Full safe runner fails after focused fixes.
