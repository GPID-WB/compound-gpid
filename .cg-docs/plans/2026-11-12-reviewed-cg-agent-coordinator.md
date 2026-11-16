---
date: 2026-11-12
title: "Developer-Only CG Agent Coordinator (Reviewed)"
status: completed
completed-date: 2026-11-13
execution-report: ".cg-docs/work-reports/2026-11-13-reviewed-cg-agent-coordinator.md"
completed-phases: [1, 2]
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-11-12-cg-agent-coordinator.md"
supersedes: ".cg-docs/plans/2026-11-12-cg-agent-coordinator.md"
language: "both"
estimated-effort: "small"
deviation-policy: "ask"
artifact-schema-version: 1
phases: 2
tags: [kilo, coordinator, developer-setup, workflow-reuse]
---

# Plan: Developer-Only CG Agent Coordinator (Reviewed)

## Objective

Deliver an explicitly selected developer-only Kilo primary agent that connects
existing CG workflows without duplicating them or registering in consumers.
Planning approval does not authorize implementation.

## Context

Expected checkout: `E:/PovcalNet/01.personal/wb384996/GPID-team/compound-gpid/.kilo/worktrees/feat-cg-agent-coordinator-574814e574da0396`,
branch `feat/cg-agent-coordinator`, initial clean baseline
`598a9e80006266c6d4a291bfc62a61492a875e35`.
The brainstorm records current code evidence: install units exclude developer
sources; generator cleanup preserves unowned files; two drift comparisons need
an exact exception. No generator, mapping, installer, or link-runtime change is
needed. Local config enables both suites and thorough review. Standalone `kilo`
is absent from PATH; installed-host checks remain pending.

Initial plan critique found P2.1 (recursive Phase 2 startup) and P2.2 (Pester
prohibition conflicting with the inherited phase gate). The user approved both
revisions: a one-time handoff and the existing safe full-suite gate. Use this
revision explicitly; the original is preserved, not an execution target.

## Requirements

| ID | Requirement | Source |
| --- | --- | --- |
| R1 | Explicit primary selection; two tracked developer sources; minimal local activation preserving credentials/settings/default/model. | Approved design |
| R2 | Reuse current workflows, contracts, gates, artifacts, and reporting; no duplicate implementation. | Approved reuse requirements |
| R3 | Exclude consumers; preserve sources and unrelated generated-tree checks. | Code audit |
| R4 | Verify checkout, label claim provenance, inspect parallel prerequisites/write overlap, preserve approvals. | Approved behavior |
| R5 | Executed live, isolation, parity, and review evidence. | Approved completion contract |

## Reuse And Ownership

| Need | Existing owner; coordinator responsibility |
| --- | --- |
| Recovery | Select `/cg-resume`; it cross-checks artifacts/state. Never treat `nextCommand` as authorization. |
| Design/planning | `/cg-brainstorm`, `/cg-plan`, `/cg-plan-review` own confirmation, save gates, validation, and read-only critique. |
| Small work | `/cg-light-work <task>` owns actual qualification, sequencing, permissions, Plan approval, bounded review, and compounding consent; no broad-write lifecycle agent. |
| Approved execution | `/cg-work` owns implementation, Work Report, permitted Plan status fields, evidence, and active-state writes. |
| Review/correction | `/cg-review`, required agents, `/cg-fix-triage`; preserve report/status ownership, autofix permissions, and verify fallback rules. |
| Roadmap/knowledge | Authorized `@cg-roadmap` writes; `/cg-compound` owns verified capture with required consent and disclosed side effects. |
| Shared rules | Load applicable context-loading, active-state, goal-execution, artifact-view, review-routing, and model-advisory contracts; advice never assigns models. |

## Implementation Steps

## Phase 1: Source And Parity

### 1. Add The Opt-In Coordinator

- **Requirements**: R1, R2, R4
- **Files**: `.kilo/developer/cg-agent-coordinator.md`, `.kilo/developer/coordinator.config.json`; ignored root `kilo.jsonc` for approved local activation only.
- **Details**: Plain prompt; fragment contains only `agent.cg-agent-coordinator` description, `mode: primary`, and `prompt: "{file:./.kilo/developer/cg-agent-coordinator.md}"`. Manually merge that entry at the root, preserving unrelated configuration/comments/credentials/permissions; do not load the fragment directly at its tracked location. The prompt selects routes, reads their definitions, and obeys their stage limits, without copying procedures. Selection, workers, and artifacts grant no approval. Report checkout mismatches; inspect prerequisites/write overlap before parallelism; new Agent Manager sessions/worktrees require explicit authorization.
- **Test Scenarios**: Valid opt-in; unrelated settings preserved; conflicting entry/missing prompt stops without overwrite; planning-only cannot enter execution.
- **Tests**: Extend `scripts/tests/test_target_kilo.py` for fragment/reference shape, primary mode, and absent model/default/permission overrides; live V1/V2 later.
- **Acceptance criteria**: Only opted-in developers register it; no duplicate workflow/state/reporting implementation.

### 2. Preserve Parity And Consumer Isolation

- **Requirements**: R3, R5
- **Files**: `scripts/tests/test_target_drift.py`, `test_target_ownership.py`, `test_target_mapping.py`, `test_project_projection.py` in that directory.
- **Details**: Subtract exactly the two developer paths at exact-set and orphan comparisons; retain raw inventory and batched Git-ignore checks. Extend existing fixtures: seed both sources, execute stale-owned cleanup, check unchanged bytes/no ownership; exercise legacy recursive-copy install units and manifest staging/publication into fixture consumers. No generated config/manifest registration.
- **Test Scenarios**: Approved sources survive/pass; third developer file, missing/changed output, and cache artifacts remain detectable; neither consumer path contains sources/registration.
- **Tests**: Five existing Python files named in Steps 1-2; inherited safe phase gate below.
- **Acceptance criteria**: V3/V4 checks pass; runtime generator/link/install sources unchanged.

#### One-Time Phase 1-To-2 Handoff

After Phase 1's inherited full-suite gate and completion update, the originating
session saves its normal Work Report/active-state handoff and ends execution.
Only a user-initiated or separately explicitly authorized fresh session in this
same checkout selects `cg-agent-coordinator`. It runs `/cg-resume`, cross-checks
this exact Plan and existing Work Report/state, and demonstrates a planning-only
boundary before receiving explicit authorization for `/cg-work phase2 review:auto`.
The originating session must not continue writing concurrently. No automatic
session/worktree creation. If fresh-session access is unavailable, V1/V2 remain
blocked. This transition occurs once, outside Step 3; the resumed phase must not
invoke itself. Any execution handoff prompt must include the required Target
Project, Target Environment, and Target Agent metadata.

## Phase 2: Live Reuse And Closure

### 3. Complete The Bounded Setup Task In The Fresh Session

- **Requirements**: R1, R2, R4, R5
- **Files**: `CONTRIBUTING.md`; existing workflow-owned execution artifacts.
- **Details**: Start already inside the authorized fresh coordinator session after the one-time handoff. Through the running `/cg-work`, document Windows/macOS root-entry merge, explicit selection, removal of only that local entry, consumer exclusion, and live-check prerequisites. Reuse the same Plan/Work Report; let the workflow append its resume section and update state. Record host observations and before/after Git state. Do not create a second session, Plan, ledger, or report, or invoke `/cg-work phase2` again. Preserve the stop before compounding without consent.
- **Test Scenarios**: Explicit selection and authorized documentation edit succeed; mismatch/missing authority stops; no duplicated artifacts or unrelated config change.
- **Tests**: V1/V2 host observations and artifact identities in the existing Work Report; static text checks do not prove compliance.
- **Acceptance criteria**: V1/V2 pass and setup is reusable without exporting full configuration.

### 4. Verify And Review The Complete Change

- **Requirements**: R3, R5
- **Files**: Approved implementation set and workflow-owned reports only.
- **Details**: Rerun affected Python/parity checks and inherited safe phase gate; inspect intended diff. Use authorized `review:auto` through current routing at configured thorough depth, `/cg-fix-triage` for saved applicable findings, and final `/cg-review mode:verify` with its actual fallback rules. Preserve evidence and consent boundaries.
- **Test Scenarios**: Required checks/review pass; unavailable evidence or exhausted corrections blocks completion.
- **Tests**: V3/V4 plus canonical Review/Work Report evidence for V5.
- **Acceptance criteria**: All required evidence passes, applicable findings resolved, and no unauthorized publication or Git mutation.

## Testing Strategy

Use installed Python/pytest and Kilo. Verify E:-resolved output parents; set
process-local `TEMP`, `TMP`, `TMPDIR`, disable bytecode/pytest cache, and use a
new task-specific E: `--basetemp` (pytest may clear it). Run
`python -B -m pytest -p no:cacheprovider` on the five named files with that base.
Retain `/cg-work`'s existing full-suite phase gate: load `cg-skill-pester-safety`,
use its prescribed isolated execution mechanism and `. tests\Run-Tests.ps1`
without flags/pipelines, then inspect `tests/last-run.json` summary only;
`filteredFiles` means partial, not a passed gate. Verify installed prerequisites
and all child-process outputs first; if safe isolation/E:-only writes cannot be
satisfied, block rather than substitute targeted tests or install dependencies.
Fixture tests may exercise link helpers; never install/link into real consumers.
Redirect any agent-started CLI XDG data/state/cache and persistent outputs to E:.

## Documentation Checklist

- Update existing `CONTRIBUTING.md`; no new setup document/command.
- Record evidence through existing reports, not a new schema.

## Risks & Mitigations

| Risk | Minimal response |
| --- | --- |
| Prompt bypasses gates or overclaims worker evidence. | Live V2 plus claim labels and command-owned approvals/reports. |
| Source location or broad exception leaks/hides content. | Exact paths; consumer fixtures; retained raw inventory and negative cases. |
| Config merge damages settings or host cannot load. | Entry-only edit, no config export; V1 must pass. |

## Out of Scope

Default/model changes, dependencies, plugin/controller/installer, polling,
separate command, retired autopilot, duplicate workflow policies/ledgers,
consumer registration, charter/roadmap changes, workflow-policy cleanup,
commits/pushes/merges/publication, and new environments. PIP is reference only.
Later: add sophistication only for demonstrated need and separate approval.

## Completion Contract

### Outcome

An explicitly selected developer-only coordinator loads through a minimal local
merge, reuses existing workflows/artifacts, and leaves consumers unchanged.

### Verification Surface

| ID | Evidence Required | Command/Artifact | Required |
| --- | --- | --- | --- |
| V1 | Fresh loading/selection; unchanged default/model/settings. | Installed-host observations in Work Report; same checkout. | yes |
| V2 | Bounded authorized execution reuses this Plan/report/state; unauthorized transitions stop. | One-time handoff: `/cg-resume`, approved `/cg-work phase2 review:auto`; host/artifact/Git observations. | yes |
| V3 | No sources/registration in either consumer path. | Existing Kilo/mapping/projection fixtures, including recursive copy and staging/publication. | yes |
| V4 | Sources survive; unrelated drift remains detectable; inherited phase gates pass. | Ownership/drift tests and parity; canonical runner summary, no partial result. | yes |
| V5 | Review/correction and final verification complete. | Current review/fix workflows and canonical Review/Work Report evidence. | yes |

### Constraints

| ID | Constraint | Check |
| --- | --- | --- |
| C1 | Preserve settings/credentials. | Entry-only root merge; no full config sharing. |
| C2 | Exact source exception only. | Two paths/two comparisons; raw inventory unchanged. |
| C3 | Preserve workflow ownership/approvals. | Read selected commands; no parallel workflow/state/report implementation. |
| C4 | Preserve storage/checkout boundaries. | E:-only outputs; original dev/PIP read-only; report mismatches without switching. |

### Boundaries

- Allowed after separate implementation authorization: named sources/tests/docs, local activation, workflow-owned reports/state, and inherited safe checks.
- Out of scope: exclusions above; fresh sessions require explicit initiation/authorization; current planning writes only new planning artifacts.

### Iteration Policy

1. Execute sequentially after explicit implementation authorization; the one-time fresh-session handoff is a real prerequisite, not routine phase approval. Use installed tools and one working check per change. Minimal First: safeguards only for almost-irreversible failures; otherwise defer under Later.
2. Initial check/review pass plus at most two in-scope correction passes; rerun affected checks, resolving all applicable findings.
3. `ask` for material deviations; stop on exhausted budget. Never relabel missing/failed/worker-reported evidence as passed.

### Blocked-Stop Conditions

- Checkout mismatch, unsafe output/runner isolation, missing installed prerequisite, protected boundary/scope decision, or unresolved workflow-permission conflict.
- Missing/failed required evidence or no explicit fresh-session access/authorization; static inspection cannot replace V1/V2.
- Correction exceeds scope/budget or durable evidence cannot be saved. Plan approval never implies implementation authorization.
