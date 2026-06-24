---
date: 2026-06-23
title: "Snapshot and External-Research Modes"
status: completed
completed-date: 2026-06-23
execution-report: .cg-docs/work-reports/2026-06-23-snapshot-external-research-modes.md
scope: "Standard"
brainstorm: null
language: "JSON/Markdown/Python"
estimated-effort: "medium"
deviation-policy: "autonomous"
tags: [snapshot, external-research, opt-in, governance, evidence]
phases: 3
completed-phases: [1, 2, 3]
roadmap-features:
  - token-efficiency-portability-expansion/phase-2-3-snapshot-external-research-modes
---

# Plan: Snapshot and External-Research Modes

## Objective

Complete Phase 2.3 by defining tested opt-in governance for future snapshot and
external-research modes without implementing snapshot capture, browser/web
research, network calls, or external integrations.

## Context

Compound GPID already has local command-summary artifacts and Brain/query
artifacts. External research exists only in older strategy/review workflows and
must not become an implicit dependency of ordinary prompts. Phase 2.3 should
define mode semantics, gates, and non-goals.

Brain findings:

- Optional retrieval backend evaluation established the pattern: registry as
  evaluation artifact, not runtime configuration -- source:
  `.cg-docs/plans/2026-06-23-optional-retrieval-backend-evaluation.md`.
- External workflow research needs explicit attribution and mode boundaries --
  source: `.cg-docs/plans/2026-04-21-competitive-repo-review-system.md`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Define snapshot and external-research candidate modes and gates. | roadmap Phase 2.3 |
| R2 | Keep non-local modes disabled and explicit opt-in only. | objective hard stop |
| R3 | Include source attribution, privacy, reproducibility, copyright-safe summarization, token budget, and rollback gates. | external research risk |
| R4 | Preserve ordinary local workflow behavior as the only default. | current workflow |
| R5 | Add tests that fail if snapshot/external modes become default-enabled or approved without gates. | project testing pattern |
| R6 | Do not implement snapshot capture, browser automation, web search, external services, or runtime mode switching. | roadmap sequencing |

## Implementation Steps

## Phase 1: Mode Registry

### 1. Add mode registry

- **Requirements**: R1, R2, R3, R4, R6
- **Files**:
  - `.github/shared/snapshot-research-modes.json`
- **Details**:
  - Add a static registry for current local mode and future candidates.
  - Mark snapshot and external research candidates as `evaluate-only` or
    `deferred`, default-disabled, and explicit opt-in.
  - Include required gates and non-goals.

## Phase 2: Documentation and Tests

### 2. Document and guard mode policy

- **Requirements**: R2, R3, R5
- **Files**:
  - `docs/snapshot-external-research.md`
  - `docs/reference.md`
  - `docs/workflow.md`
  - `scripts/tests/test_snapshot_research_modes.py`
- **Details**:
  - Document current default behavior and future candidate modes.
  - Test that only local workflow mode is default-enabled and that external
    research is deferred and gated.

## Phase 3: Evidence and Roadmap Closure

### 3. Validate, compound, and close roadmap status

- **Requirements**: R5, R6
- **Files**:
  - `.cg-docs/work-reports/2026-06-23-snapshot-external-research-modes.md`
  - `.cg-docs/reviews/*snapshot-external-research*`
  - `.cg-docs/solutions/testing-patterns/*snapshot-external-research*`
  - `roadmap.json`
- **Details**:
  - Run focused tests, prompt/docs tests, broader Python tests, full safe
    runner, Brain rebuild, audit refresh, and diff check.
  - Mark Phase 2.3 done and parent milestone done only after validation passes.

## Testing Strategy

Focused Python tests guard registry semantics. Pester safe runner validates
roadmap/docs health. No external research is performed for this feature.

## Documentation Checklist

- `docs/snapshot-external-research.md` explains mode gates and non-goals.
- `docs/reference.md` links the mode registry.
- `docs/workflow.md` states ordinary workflows remain local by default.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Mode registry is mistaken for implementation | Label it evaluation-only and test default-disabled candidates. |
| External research creates attribution/privacy risk | Require source, privacy, copyright-safe summary, and reproducibility gates. |
| Snapshot mode stores large transcript dumps | Make transcript/raw-output dumps a non-goal and require token-budget review. |

## Out of Scope

- Browser automation, web search, external research execution, or source
  fetching.
- Snapshot capture or replay implementation.
- Runtime mode switching or new command flags.

## Completion Contract

### Outcome

Phase 2.3 is complete when the repository has a tested mode registry and docs
for future snapshot/external-research modes, all non-local modes remain opt-in
and disabled, and roadmap/evidence artifacts are committed.

### Verification Surface

| ID | Evidence Required | Command/Artifact | Required |
|----|-------------------|------------------|----------|
| V1 | Mode registry tests pass. | `python3 -m pytest scripts/tests/test_snapshot_research_modes.py -q` | yes |
| V2 | Prompt/docs checks pass. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` | yes |
| V3 | Broader Python tests pass. | `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q` | yes |
| V4 | Full safe runner passes. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |
| V5 | Roadmap feature and parent milestone are done and linked. | `roadmap.json` | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | No snapshot or external-research candidate is default-enabled. | registry tests |
| C2 | No external search, browser automation, network, or snapshot runtime is implemented. | diff review |
| C3 | Safe Pester runner only. | command evidence |
