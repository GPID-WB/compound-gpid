---
date: 2026-06-23
title: "Handoff Resume and Active-State Compaction"
status: completed
completed-date: 2026-06-23
completed-phases: [1, 2, 3, 4]
scope: "Deep"
brainstorm: null
language: "Markdown/PowerShell/JSON"
estimated-effort: "large"
deviation-policy: "autonomous"
tags: [token-efficiency, resume, handoff, active-state, compaction]
phases: 4
roadmap-features:
  - token-efficiency-core-system/phase-1-5-handoff-resume-compaction
---

# Plan: Handoff Resume and Active-State Compaction

## Objective

Implement Phase 1.5 by adding compact durable active-state handoff records so long workflows can resume from artifact paths, phase/evidence status, unresolved decisions, and exact next commands instead of repeated transcript context.

## Context

Phase 1.1 established measurement, Phase 1.2 added budgeted Brain retrieval, Phase 1.3 added command-output summaries, and Phase 1.4 tightened progressive-disclosure wording. Phase 1.5 should make `/cg-work`, `/cg-resume`, and `/cg-diagnose` use compact state records that reference existing plans, work reports, reviews, issue links, and output artifacts by path.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Store compact active-state records in `.cg-docs/` with artifact paths, current phase, unresolved decisions, evidence status, and exact next command. | roadmap strategy |
| R2 | Make handoff summaries reference existing plans, work reports, reviews, issues, and command-output artifacts by path rather than duplicating content. | roadmap strategy |
| R3 | `/cg-work` should create/update active-state records during long work and completion gates. | roadmap strategy |
| R4 | `/cg-resume` should prefer active-state records for current-state orientation, while verifying referenced files exist and keeping its existing non-mutating behavior. | roadmap strategy |
| R5 | `/cg-diagnose` should use active-state records when present to make crash recovery handoff concise. | roadmap strategy |
| R6 | Add prompt contract tests and docs. | evidence requirements |
| R7 | Do not add external services, cross-agent adapters, optional backends, snapshots, or token-saving claims. | objective hard stop |

## Phase 1: Active-State Contract

### 1. Add shared active-state schema
- **Files**: `.github/shared/active-state.contract.md`, `.cg-docs/active-state/.gitkeep`
- **Details**:
  - Define `.cg-docs/active-state/current.json` as the compact pointer record.
  - Define required fields: schema version, updated timestamp, workflow, status, plan path, execution report path, current phase, evidence status, unresolved decisions, artifact refs, git summary, and exact next command.
  - Require artifact-reference-first content; forbid transcript dumps and raw command output.
- **Tests**:
  - Pester prompt-tool tests assert schema path, exact next command, evidence status, artifact refs, and no transcript dumps.

## Phase 2: Prompt Integration

### 2. Update `/cg-work` to write active-state records
- **Files**: `.github/prompts/cg-work.prompt.md`
- **Details**:
  - Permit writes to `.cg-docs/active-state/`.
  - Load the active-state contract.
  - Write/update `current.json` after execution report creation, phase boundaries, blocked stops, and completion.
  - Store compact references to plans, reports, reviews, wrapper artifacts, and next commands.

### 3. Update `/cg-resume` and templates to read active-state records
- **Files**: `.github/prompts/cg-resume.prompt.md`, `.github/prompts/resume-templates.md`
- **Details**:
  - Read `.cg-docs/active-state/current.json` if present.
  - Validate referenced plan/report/review paths before displaying them.
  - Prefer the active-state exact next command when it is consistent with scanned pending work.
  - Preserve non-mutating behavior.

### 4. Update `/cg-diagnose` handoff
- **Files**: `.github/prompts/cg-diagnose.prompt.md`
- **Details**:
  - Read active-state record if present and include compact recovery handoff pointers.
  - Do not create or modify active-state records from diagnose.

## Phase 3: Docs and Tests

### 5. Add docs and Pester coverage
- **Files**: `docs/reference.md`, `docs/workflow.md`, `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Document active-state records as compact restart aids, not durable knowledge.
  - Add tests for `/cg-work` write behavior, `/cg-resume` read behavior, `/cg-diagnose` read-only handoff behavior, exact next command, and artifact-reference-first wording.

## Phase 4: Evidence, Review, and Compound

### 6. Validate and record evidence
- **Files**: `.cg-docs/work-reports/*`, `.cg-docs/reviews/*`, `.cg-docs/solutions/*`, `roadmap.json`
- **Details**:
  - Run prompt-tool tests, full safe runner, audit/context checks if relevant, review/verify, and compounding.
  - Rebuild Brain after the solution record.

## Testing Strategy

- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"`
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"`
- `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q`
- `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations`
- `git diff --check`

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Active-state records duplicate transcripts and increase context. | Contract forbids transcript dumps and raw command output; records store paths and compact fields only. |
| `/cg-resume` trusts stale state. | Prompt verifies referenced paths and cross-checks scanned pending work before recommending next action. |
| `/cg-diagnose` mutates state unexpectedly. | Diagnose remains read-only and only includes active-state pointers in its handoff. |
| New state files become durable knowledge clutter. | Docs classify active-state as restart aid; durable decisions still belong in plans, reports, reviews, and solutions. |

## Out of Scope

- Automated state-writing scripts.
- External services, GitHub mutation, adapters, optional backends, or snapshots.
- Replacing execution reports or review files.
- Measuring savings; Phase 1.6 owns dashboard/regression checks.

## Completion Contract

### Outcome

Phase 1.5 is complete when `/cg-work`, `/cg-resume`, and `/cg-diagnose` share a compact active-state contract, prompt tests guard the artifact-reference-first handoff behavior, docs explain usage, and validation evidence passes.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Active-state contract defines compact schema and forbids transcript/raw output dumps. | `.github/shared/active-state.contract.md` and prompt tests | yes |
| V2 | 2 | `/cg-work` is authorized and instructed to write/update active-state records. | `tests/prompt-tools.Tests.ps1` | yes |
| V3 | 2 | `/cg-resume` reads active-state records, validates refs, and preserves non-mutating behavior. | `tests/prompt-tools.Tests.ps1` | yes |
| V4 | 2 | `/cg-diagnose` uses active-state handoff pointers without writing state. | `tests/prompt-tools.Tests.ps1` | yes |
| V5 | 3 | Docs explain active-state restart aids without token-saving claims. | docs diff | yes |
| V6 | final | Prompt-tool checks pass. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` | yes |
| V7 | final | Full safe runner passes. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | all | Active-state records reference artifacts by path and do not copy full report/review/test output. | Contract and prompt tests. |
| C2 | all | `/cg-resume` and `/cg-diagnose` remain non-mutating. | Prompt tests. |
| C3 | all | Existing execution report and review semantics remain intact. | Prompt-tools and safe runner. |
| C4 | all | No external services, adapters, backends, snapshots, or GitHub writes. | Diff review. |
| C5 | all | No unmeasured token-saving claim. | Docs/review. |

### Boundaries

- Allowed: shared contract, prompt wording, docs, prompt-tool tests, evidence artifacts.
- Out of scope: runtime state generator scripts, IDE APIs, CI integrations, cross-agent packaging, optional retrieval backends.

### Iteration Policy

1. Prefer compact JSON fields and artifact paths over prose.
2. Verify references before presenting active-state recommendations.
3. Keep active-state records as restart aids; durable decisions stay in canonical project artifacts.

### Blocked-Stop Conditions

- A prompt change would alter non-mutating behavior for `/cg-resume` or `/cg-diagnose`.
- Active-state records would need to store raw terminal output or transcript text.
- Required tests or safe runner fail and cannot be fixed within scope.
