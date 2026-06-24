---
date: 2026-06-23
title: "Optional Retrieval Backend Evaluation"
status: completed
completed-date: 2026-06-23
execution-report: .cg-docs/work-reports/2026-06-23-optional-retrieval-backend-evaluation.md
scope: "Standard"
brainstorm: null
language: "JSON/Markdown/Python"
estimated-effort: "medium"
deviation-policy: "autonomous"
tags: [retrieval, evaluation, opt-in, governance, token-efficiency]
phases: 3
completed-phases: [1, 2, 3]
roadmap-features:
  - token-efficiency-portability-expansion/phase-2-2-optional-retrieval-backends
---

# Plan: Optional Retrieval Backend Evaluation

## Objective

Complete Phase 2.2 by adding a deterministic evaluation matrix for optional
retrieval backends without enabling any new backend, dependency, network call,
or external service.

## Context

The current retrieval surface is `cg-index query`, backed by local generated
Brain artifacts. It is stdlib-only, deterministic, budget-aware, and explicitly
does not call external services. Phase 2.2 should evaluate future backend
options behind opt-in gates, not implement them.

Brain findings:

- Phase 1.2 explicitly deferred vector search, embeddings, MCP retrieval
  backends, optional external services, and code-intelligence adapters --
  source:
  `.cg-docs/plans/2026-06-23-knowledge-brain-query-budgeted-retrieval.md`.
- Team Brain patterns need privacy filtering and explicit pull behavior before
  remote knowledge is used -- source:
  `.cg-docs/plans/2026-05-20-team-brain-batch-d.md`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Define candidate retrieval backends and evaluation criteria. | roadmap Phase 2.2 |
| R2 | Keep every non-current backend disabled and opt-in only. | objective hard stop |
| R3 | Include privacy, dependency, offline, token-budget, validation, and rollback gates. | high-stakes workflow constraints |
| R4 | Preserve current local Brain query as the only active backend. | Phase 1.2 |
| R5 | Add tests that fail if an optional backend is marked default-enabled or approved without gates. | project testing pattern |
| R6 | Do not implement external services, vector stores, snapshots, or runtime backend switching. | roadmap sequencing |

## Implementation Steps

## Phase 1: Evaluation Matrix

### 1. Add retrieval backend registry

- **Requirements**: R1, R2, R3, R4, R6
- **Files**:
  - `.github/shared/retrieval-backends.json`
- **Details**:
  - Add a source-of-truth JSON registry for current and candidate backends.
  - Mark `native-brain-query` as current.
  - Mark all future candidates as `evaluate-only`, `default_enabled: false`,
    and `requires_explicit_opt_in: true`.
  - Include required gates and explicit non-goals.
- **Acceptance criteria**: registry is deterministic, local, and does not
  configure any runtime backend.

## Phase 2: Documentation and Tests

### 2. Document evaluation policy and guard it with tests

- **Requirements**: R2, R3, R5
- **Files**:
  - `docs/retrieval-backends.md`
  - `docs/reference.md`
  - `docs/workflow.md`
  - `scripts/tests/test_retrieval_backends.py`
- **Details**:
  - Explain current backend status and candidate gates.
  - Add tests for schema, default-disabled optional candidates, required gates,
    and no approved external/network backend.
- **Acceptance criteria**: docs and tests make evaluation-only status explicit.

## Phase 3: Evidence and Roadmap Closure

### 3. Validate, compound, and close roadmap status

- **Requirements**: R5, R6
- **Files**:
  - `.cg-docs/work-reports/2026-06-23-optional-retrieval-backend-evaluation.md`
  - `.cg-docs/reviews/*optional-retrieval-backend*`
  - `.cg-docs/solutions/testing-patterns/*optional-retrieval-backends*`
  - `roadmap.json`
- **Details**:
  - Run focused retrieval-backend tests, prompt/docs tests, broader Python
    tests, full safe runner, Brain rebuild, audit refresh, and diff check.
  - Mark Phase 2.2 done only after evidence passes.

## Testing Strategy

Use focused Python tests for registry semantics and full safe runner for
repository health. Keep the registry static and stdlib-readable.

## Documentation Checklist

- `docs/retrieval-backends.md` explains current and candidate backends.
- `docs/reference.md` links the registry and policy doc.
- `docs/workflow.md` states that optional retrieval backend work is evaluation
  only until a future roadmap item explicitly implements a backend.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Evaluation is mistaken for implementation | Use `evaluate-only` status and docs/tests that forbid default enablement. |
| External/network backend slips in as approved | Test that network candidates cannot be `approved` or default-enabled. |
| Current local query behavior is destabilized | Do not edit `scripts/brain/query.py` or CLI runtime behavior. |

## Out of Scope

- Runtime backend switching.
- Vector database, embeddings, MCP/code-intelligence retrieval, snapshots, or
  external research modes.
- Installing optional dependencies.

## Completion Contract

### Outcome

Phase 2.2 is complete when the repository has a tested evaluation registry for
optional retrieval backends, docs explain the opt-in gates, current local Brain
query remains the only active backend, and roadmap/evidence artifacts are
committed.

### Verification Surface

| ID | Evidence Required | Command/Artifact | Required |
|----|-------------------|------------------|----------|
| V1 | Retrieval registry tests pass. | `python3 -m pytest scripts/tests/test_retrieval_backends.py -q` | yes |
| V2 | Prompt/docs checks pass. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` | yes |
| V3 | Broader Python tests pass. | `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q` | yes |
| V4 | Full safe runner passes. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |
| V5 | Roadmap feature is done and linked to this plan. | `roadmap.json` | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | No optional backend is default-enabled. | registry tests |
| C2 | No external service, vector DB, snapshot, or runtime switch is implemented. | diff review |
| C3 | Safe Pester runner only. | command evidence |
