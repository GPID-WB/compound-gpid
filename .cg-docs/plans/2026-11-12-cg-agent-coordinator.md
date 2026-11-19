---
date: 2026-11-12
title: "Developer-Only CG Agent Coordinator"
status: active
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-11-12-cg-agent-coordinator.md"
language: "both"
estimated-effort: "small"
deviation-policy: "ask"
artifact-schema-version: 1
phases: 2
tags: [kilo, coordinator, developer-setup, workflow-reuse]
---

# Plan: Developer-Only CG Agent Coordinator

## Objective

Deliver an explicitly selected Kilo primary agent for Compound GPID developers
that connects existing CG workflows without duplicating them or registering in
consumer projects. Design and Plan-save approval are not implementation approval.

## Context

Expected checkout: `E:/PovcalNet/01.personal/wb384996/GPID-team/compound-gpid/.kilo/worktrees/feat-cg-agent-coordinator-574814e574da0396`,
branch `feat/cg-agent-coordinator`; planning baseline
`598a9e80006266c6d4a291bfc62a61492a875e35` (initially clean).
The decided brainstorm records code evidence: install units exclude developer
sources; generator cleanup deletes only stale owned files; two drift comparisons
need an exact source exception. No mapping, generator, installer, or link-runtime
change is currently needed. Local config enables both suites and thorough review.
Standalone `kilo` is absent from PATH; installed-host live evidence is pending.

## Requirements

| ID | Requirement | Source |
| --- | --- | --- |
| R1 | Explicit primary selection; tracked prompt and minimal opt-in fragment; preserve local settings/credentials, defaults, and model choice. | Approved design |
| R2 | Read and reuse current commands, skills, agents, contracts, gates, and authoritative artifacts; no parallel workflow implementation. | Approved reuse requirements |
| R3 | No consumer installation/registration; preserve source files and unrelated generated-tree correctness. | Discovery/code audit |
| R4 | Verify checkout; label observed/worker-reported/proposed/unknown claims; check prerequisites and overlapping writes; retain human approvals. | Approved behavior |
| R5 | Demonstrate loading, bounded authorized workflow reuse, isolation, and parity with executed evidence and existing review artifacts. | Completion-preview approval |

## Reuse And Ownership

| Capability | Existing owner; coordinator responsibility |
| --- | --- |
| Recovery | `/cg-resume` cross-checks Plans/Reviews/active-state; coordinator selects it, not a new recovery procedure. |
| Design/planning | `/cg-brainstorm`, `/cg-plan`, `/cg-plan-review` own qualification, confirmation, save gates, validation, and read-only critique. |
| Small work | `/cg-light-work <task>` owns hard/size qualification, sequencing, Plan approval, bounded review, and separate compounding consent; never a broad-write lifecycle agent. |
| Approved Plan execution | `/cg-work` owns implementation, Work Reports, permitted Plan status fields, evidence, and active-state writes. |
| Review/correction | `/cg-review`, required review agents, and `/cg-fix-triage` own their modes, fixes, findings, reports, and status updates. Check autofix/verify fallback before routing. |
| Roadmap/knowledge | Only authorized `@cg-roadmap` writes; `/cg-compound` owns verified capture with required consent and disclosed knowledge side effects. |
| Shared behavior | Load current context-loading, active-state, goal-execution, artifact-view, review-routing, and model-advisory contracts when relevant; advice never assigns a model. |

## Implementation Steps

## Phase 1: Source And Parity

### 1. Add The Opt-In Coordinator

- **Requirements**: R1, R2, R4
- **Files**: `.kilo/developer/cg-agent-coordinator.md`, `.kilo/developer/coordinator.config.json`; ignored root `kilo.jsonc` only for approved developer activation.
- **Details**: Plain tracked prompt plus fragment containing only `agent.cg-agent-coordinator` with description, `mode: primary`, and `prompt: "{file:./.kilo/developer/cg-agent-coordinator.md}"`. Merge this entry locally without replacing configuration, copying credentials, or granting wider permissions. The fragment is an input to a manual root merge, not a directly loadable config at its tracked location. Prompt selects routes from the map, reads their current definitions, and inherits their stage limits rather than copying procedures. Selection, worker messages, and saved artifacts never confer authorization. Report checkout mismatches; inspect dependencies/write overlap before parallel work; require explicit authorization for new Agent Manager sessions/worktrees.
- **Test Scenarios**: Opt-in entry loads; unrelated local settings remain; missing source/config conflict is reported without overwrite; planning-only requests cannot enter execution.
- **Tests**: Extend `scripts/tests/test_target_kilo.py` for fragment shape, contained reference, primary mode, and absent model/default/permission overrides; live V1/V2 later.
- **Acceptance criteria**: Only the opted-in developer checkout registers the agent; no workflow/state/reporting duplication.

### 2. Preserve Generated-Tree Checks And Consumer Isolation

- **Requirements**: R3, R5
- **Files**: `scripts/tests/test_target_drift.py`, `test_target_ownership.py`, `test_target_mapping.py`, `test_project_projection.py` in the same directory.
- **Details**: Subtract exactly the two developer paths at the drift exact-set and orphan comparisons; retain the raw inventory and batched ignore checks. Extend existing fixtures, not a new framework: seed both sources, run generator stale-owned cleanup, verify unchanged source bytes and no ownership; exercise selected legacy recursive-copy units and manifest projection/staging/consumer publication without installing into real projects. No generated manifest/config registration.
- **Test Scenarios**: The two sources pass; a third developer file remains unexpected; missing/changed generated output and cache artifacts still fail; neither consumer path contains the sources or registration.
- **Tests**: The five existing test files named in Steps 1-2, using fixture-only output on E:.
- **Acceptance criteria**: V3/V4 pass; generated/runtime sources remain unchanged.

## Phase 2: Live Reuse And Closure

### 3. Demonstrate Fresh-Session Workflow Reuse And Document Setup

- **Requirements**: R1, R2, R4, R5
- **Files**: `CONTRIBUTING.md`; existing workflow-owned Plan/Work Report/active-state artifacts.
- **Details**: After Phase 1 checks, a user-initiated or separately explicitly authorized fresh Kilo session in this same checkout selects the agent. Do not create a session/worktree implicitly. Use `/cg-resume`, cross-check this Plan and its existing Work Report, then explicitly authorize `/cg-work phase2 review:auto` to finish this bounded phase, including the developer-setup paragraph. Preserve existing Work Report evidence; let `/cg-work` append its resume section and update active state. Document Windows/macOS manual merge, explicit selection, removal of only that local entry, and consumer exclusion. No installer. Observe a planning-only/no-publication boundary before execution approval, and retain the stop before compounding without consent.
- **Test Scenarios**: Fresh loading and existing-report reuse succeed; wrong checkout, unsupported reference, or missing authorization stops; no duplicate Plan/ledger/report appears.
- **Tests**: V1/V2 host observations with canonical artifact paths and before/after Git state recorded in the Work Report; static text checks are insufficient.
- **Acceptance criteria**: Both live evidence items pass, unrelated config is unchanged, and setup is repeatable without copying a full local configuration.

### 4. Verify And Review The Complete Change

- **Requirements**: R3, R5
- **Files**: Approved implementation set and workflow-owned reports only.
- **Details**: Run targeted tests, then existing generated-tree parity checks; inspect the intended diff. Execute authorized `review:auto` through current routing at configured thorough depth; use `/cg-fix-triage` for applicable saved findings and finish with `/cg-review mode:verify`, honoring its fallback rules. Record real evidence, not inferred compliance. Do not compound automatically.
- **Test Scenarios**: Full intended change passes; failed/unavailable evidence blocks completion; review correction stays within scope/budget.
- **Tests**: V3/V4 rerun plus V5 canonical Review and Work Report evidence.
- **Acceptance criteria**: All required evidence passes and applicable findings are resolved; no publication or Git mutation beyond approved source edits.

## Testing Strategy

Reuse installed Python/pytest and the installed Kilo host. Before commands,
verify E:-resolved output parents; set process-local `TEMP`, `TMP`, `TMPDIR`,
disable bytecode and pytest cache, and select a new task-specific E: `--basetemp`
(pytest may clear that directory). Run `python -B -m pytest -p no:cacheprovider`
against the five named files with that `--basetemp`. Do not run broad installers,
real-consumer link flows, or Pester for this change. Redirect any agent-started
CLI's XDG data/state/cache and other persistent outputs to E:; no new dependency.
Runtime evidence is separate from static/test-fixture evidence.

## Documentation Checklist

- Update existing `CONTRIBUTING.md` with the opt-in merge/selection/removal steps and live-check prerequisites; no new setup document or command.
- Link canonical evidence through normal workflow reports; no separate reporting schema.

## Risks & Mitigations

| Risk | Minimal response |
| --- | --- |
| Prompt ignores gates or claims worker success as verified. | Observe V2, retain claim labels and original approval/reporting ownership. |
| Shared/generated location leaks registration to consumers. | Keep two developer sources outside install units; exercise both consumer paths. |
| Exception hides unrelated drift. | Exact two-path subtraction only; retain inventory, negative examples, and existing content checks. |
| Local merge loses settings or host cannot load reference. | Small entry-only edit; no full config export; V1 failure blocks completion. |

## Out of Scope

Default-agent/model changes, dependencies, plugins, controllers, installers,
automatic polling, separate slash commands, retired autopilot, duplicated workflow
policies or ledgers, consumer registration, charter/roadmap changes, workflow-policy
cleanup, commits, pushes, merges, publication, and new environments. PIP is reference
only. Later: add sophistication only for a demonstrated need and separate approval.

## Completion Contract

### Outcome

An explicitly selected developer-only coordinator loads through a minimal local
merge, reuses existing CG workflows/artifacts, and leaves consumers unchanged.

### Verification Surface

| ID | Evidence Required | Command/Artifact | Required |
| --- | --- | --- | --- |
| V1 | Fresh-session loading/selection, unchanged default/model/settings. | Installed-host observation and Work Report; same existing checkout. | yes |
| V2 | Bounded authorized execution reuses this Plan, Work Report, and workflow-owned state; unauthorized transitions stop. | `/cg-resume`, then explicitly approved `/cg-work phase2 review:auto`; host observations, artifact paths, Git state in Work Report. | yes |
| V3 | No developer sources/registration reach legacy or manifest consumers. | Existing mapping/Kilo/projection tests extended with recursive-copy and publication fixtures. | yes |
| V4 | Sources survive generation; unrelated drift remains detectable. | Existing ownership/drift tests, third-file/missing/changed/cache examples, generated-tree parity. | yes |
| V5 | Implementation review/correction and final verification complete. | Current review/fix workflows and canonical Review/Work Report evidence. | yes |

### Constraints

| ID | Constraint | Check |
| --- | --- | --- |
| C1 | Preserve local settings/credentials. | Entry-only root merge; never share full config. |
| C2 | Exact source exception only. | Two paths, two comparisons; raw inventory unchanged. |
| C3 | Preserve workflow ownership and approvals. | Read selected command; no parallel planning/review/recovery/state/reporting implementation. |
| C4 | Preserve storage/checkout boundaries. | E:-only outputs; original dev and PIP read-only; mismatches reported without switching. |

### Boundaries

- Allowed after separate implementation authorization: the named sources/tests/docs, local activation, and workflow-owned execution/review artifacts.
- Out of scope: all exclusions above; new sessions require explicit initiation/authorization even for smoke checks. Planning currently writes only new planning artifacts.

### Iteration Policy

1. Execute sequentially after explicit implementation authorization, using installed tools and one working check per change. Minimal First: safeguards only for almost-irreversible failures; otherwise defer under Later.
2. Allow the initial check/review pass and at most two in-scope correction passes; rerun affected checks and preserve all applicable findings until resolved.
3. Use `ask` for material deviations; stop on exhausted budget. Never relabel failed, absent, or worker-reported evidence as passed.

### Blocked-Stop Conditions

- Checkout mismatch, unsafe output path, protected-boundary/scope decision, or unresolved workflow-permission conflict.
- Missing/failed required evidence, unavailable installed-host access, or no explicit fresh-session initiation/authorization; static inspection cannot replace V1/V2.
- Required correction exceeds scope/budget, or durable workflow evidence cannot be saved. No implementation is authorized by this Plan's planning approval.
