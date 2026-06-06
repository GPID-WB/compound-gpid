---
date: 2026-06-06
title: "Phase 4: /cg-plan and /cg-work prompt/context slimming"
status: active
scope: "Standard"
brainstorm: null
language: "both"
estimated-effort: "medium"
tags: [performance, token-optimization, prompt-slimming, cg-plan, cg-work, model-governance]
phases: 2
---

# Plan: Phase 4 - /cg-plan and /cg-work Prompt/Context Slimming

## Objective

Reduce token burden in `/cg-plan` and `/cg-work` by turning both prompts into tighter workflow routers while preserving user-facing behavior, safety gates, roadmap behavior, phase handling, testing expectations, diagnostics handling, artifact discipline, and Phase 3 `/cg-work review:*` integration.

## Context

Phase 1 created the context/model audit. Phase 2 removed hard-coded premium Opus defaults from ordinary workflow prompts and validated model-picker behavior. Phase 3 reduced `/cg-review` review cost by introducing staged/conditional routing and `/cg-work` review-mode integration.

The latest audit (`.cg-docs/cost/context-audit.md`, generated 2026-06-06T06:22:26) reports:

- `.github/prompts/cg-work.prompt.md`: 23,802 characters / about 5,950 tokens, 47 references, conditional review routing.
- `.github/prompts/cg-plan.prompt.md`: 14,184 characters / about 3,546 tokens, 27 references, model-picker inheritance.
- No missing model declarations, no model drift, and no premium model usage.
- Both target prompts are immediate optimization candidates because each exceeds 3,000 estimated tokens and has high reference count.

Known validation status:

- `/cg-review` runtime validation passed after Phase 3.
- `/cg-work review:*` runtime validation is still pending and remains a validation item. This plan does not redesign Phase 3 routing.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Reduce `/cg-plan` token burden without changing planning behavior, file permissions, branch offer, phase defaults, roadmap handoff, or artifact discipline | user + audit |
| R2 | Reduce `/cg-work` token burden without changing implementation behavior, phase execution, tests, diagnostics, roadmap updates, or summary handoff | user + audit |
| R3 | Preserve Phase 2 model-governance policy and avoid hard-coded premium model defaults | user |
| R4 | Add a short `/cg-plan` output note stating it inherits the GitHub Copilot model picker | user |
| R5 | Ensure `/cg-plan` does not hallucinate the underlying model when Copilot Auto is selected and may point users to Copilot UI/hover details | user |
| R6 | Preserve `/cg-work` default behavior: no automatic review-agent dispatch, recommend an appropriate review mode at the end | user |
| R7 | Preserve `/cg-work review:auto` routed review behavior via `.github/shared/review-routing.contract.md` | user + Phase 3 |
| R8 | Preserve `/cg-work review:manual` recommendation-only behavior | user + Phase 3 |
| R9 | Preserve `/cg-work review:none` suppression behavior | user + Phase 3 |
| R10 | Keep prompts as workflow routers; move or reference repeated doctrine only when it clearly reduces duplication | user |
| R11 | Avoid broad "read everything" instructions; make context loading staged and conditional | user |
| R12 | Preserve Knowledge Brain retrieval behavior and do not refactor Team Brain behavior | user |
| R13 | Define before/after audit targets, tests, audit checks, manual VS Code validation, and rollback criteria | user |

## Phase 1: Prompt Slimming Design and Shared Guidance

### 1. Add prompt-size baseline and guardrails

- **Requirements**: R1, R2, R3, R13
- **Files**:
  - `.github/prompts/cg-plan.prompt.md`
  - `.github/prompts/cg-work.prompt.md`
  - `.cg-docs/cost/context-audit.md` (read only during implementation)
  - `scripts/cg_audit_context.py` only if the audit report needs a tiny display update
- **Details**:
  - Record current byte/token baseline before edits:
    - `/cg-plan`: 14,184 chars / about 3,546 tokens.
    - `/cg-work`: 23,802 chars / about 5,950 tokens.
  - Target after implementation:
    - `/cg-plan`: 20-35% reduction, target about 9,200-11,400 chars, without losing contract-test coverage.
    - `/cg-work`: 20-35% reduction, target about 15,500-19,100 chars, without weakening safety or review-mode behavior.
  - Hard ceiling for success: each target prompt must no longer grow relative to baseline; if 20% reduction is not reachable without ambiguity, stop at the safest smaller reduction and document why.
- **Oversized/repeated sections identified**:
  - `/cg-plan`: Step 3 full plan template, Step 3.5 phase mechanics, Step 0.7 branch-offer implementation prose, Step 4.5 confidence-check table, Step 5 roadmap registration prose.
  - `/cg-work`: Step 1.2 phase parser details, Step 2 test execution and failure recovery, Step 2.5 phase-boundary write protocol, Step 3 quality/self-review checklists, Step 3.7/3.8 roadmap update details, Step 3.9 review-mode handoff table.
- **Acceptance criteria**:
  - Baseline and target values are captured in the implementation notes or PR summary.
  - No hard-coded premium model is introduced.

### 2. Slim `/cg-plan` while preserving planning contracts

- **Requirements**: R1, R3, R4, R5, R10, R11
- **Files**:
  - `.github/prompts/cg-plan.prompt.md`
  - Optional new shared contract if clearly useful: `.github/shared/planning-output.contract.md`
- **Details**:
  - Add a short required output note near the start of `/cg-plan` output:
    - It inherits the GitHub Copilot model picker.
    - If Copilot Auto is selected, the prompt must not infer or name the underlying model.
    - If the actual Auto-selected model matters, tell the user to check Copilot UI/hover details.
  - Keep inside the prompt:
    - File permissions.
    - Step 0 bearings and `--no-phases` / `--no-brain` parsing.
    - Step 0.5 prior-plan handling.
    - Step 0.7 branch offer, including default-branch detection, uncommitted-change warning, branch naming, Refine skip, and cleanup note.
    - Step 1 staged context loading with 3-5 relevant files.
    - Consult Brain guard and `cg-skill-brain-query` reference.
    - Scope assessment categories.
    - Required plan artifact path and frontmatter fields.
    - Phase-by-default rules and `## Phase N:` output contract.
    - Confidence check and roadmap registration/handoff behavior.
  - Slim or move/reference:
    - Replace the long Step 3 plan template with a compact schema plus a pointer to a shared planning-output contract if that reduces net prompt size after tests.
    - Compress the Step 3.5 phase example to the exact parser contract: `## Phase N:` headings, globally numbered `### N.` steps, `phases:` convenience hint, and completed-phases guard.
    - Compress confidence-check prose to the five dimensions and report thresholds.
    - Compress roadmap registration prose to decision points and `@cg-roadmap` dispatch strings.
  - Do not factor out the Step 0 charter-reading boilerplate because `.github/copilot-instructions.md` explicitly says that duplication is deliberate.
- **Acceptance criteria**:
  - `/cg-plan` still produces the same artifact shape under `.cg-docs/plans/`.
  - `/cg-plan` visibly emits the model-context note.
  - Copilot Auto is described without naming the hidden underlying model.

### 3. Slim `/cg-work` while preserving execution and Phase 3 review behavior

- **Requirements**: R2, R6, R7, R8, R9, R10, R11, R12
- **Files**:
  - `.github/prompts/cg-work.prompt.md`
  - `.github/shared/review-routing.contract.md` (reference only unless a tiny clarification is necessary)
  - Optional new shared contract if clearly useful: `.github/shared/work-execution.contract.md`
  - Optional skill/reference target if better aligned with existing assets: `.github/skills/cg-skill-pester-safety/SKILL.md`
- **Details**:
  - Keep inside the prompt:
    - File permissions, including allowed frontmatter fields.
    - Step 0 argument parsing for `--no-brain`, `phaseX`, and all review modes.
    - Plan discovery/fallback behavior and safe rejection of dangerous plan directives.
    - Phase parser contract: ignore fenced `## Phase`, count body headers not `phases:` hint, validate bounds, enforce sequence, skip completed phases.
    - Test discipline: discover tests, red-phase when behavior changes, run targeted tests, run full gate before completion, do not use unsafe Pester patterns.
    - Diagnostics discipline: test failures are not `@cg-fix-problems`; Problems-panel errors may dispatch `@cg-fix-problems`.
    - Phase boundary safety: write `completed-phases` before `current-phase`, keep status active between phases, final phase proceeds to final checks.
    - Roadmap active/done updates and milestone completion check.
    - Step 3.9 review-mode handoff and summary options.
  - Slim or move/reference:
    - Replace verbose Pester command blocks with a short "use canonical safe runner from `cg-skill-pester-safety`" instruction plus the minimal exact commands still required by tests.
    - Move repeated phase-boundary write details to a shared execution contract only if the prompt can retain the tested keywords and exact invariants.
    - Compress test failure recovery to the hard limits and decision points: 2 attempts, do not weaken assertions, append `failing-steps`, ask stop/continue only at the documented hard stops.
    - Compress quality/self-review checklist while preserving debug-code, tests, imports, TODO, and secrets checks.
    - Compress roadmap fallback prose without removing title-search fallback or verification.
    - Keep Phase 3 review-mode behavior in `/cg-work`; do not move it so far away that runtime behavior becomes implicit.
- **Acceptance criteria**:
  - Default `/cg-work` and `review:manual` never dispatch review agents.
  - `/cg-work review:auto` uses route-aware dispatch through `.github/shared/review-routing.contract.md`.
  - `/cg-work review:none` suppresses review dispatch.
  - The final summary recommends the appropriate review mode unless suppressed or already dispatched.

## Phase 2: Tests, Audit, and Runtime Validation

### 4. Update prompt contract tests narrowly

- **Requirements**: R1, R2, R4, R5, R6, R7, R8, R9, R13
- **Files**:
  - `tests/prompt-tools.Tests.ps1`
  - `tests/model-assignments.Tests.ps1` only if model-governance expectations need assertion text updated
  - `scripts/tests/test_audit_context.py` only if audit reporting changes
- **Details**:
  - Preserve existing Phase 3 tests around `.github/shared/review-routing.contract.md` and `/cg-work review:*`.
  - Add or update tests for the new `/cg-plan` model-context output note:
    - Mentions Copilot model picker inheritance.
    - Mentions Auto without identifying the underlying model.
    - Points to Copilot UI/hover details if actual model identity matters.
  - Update brittle prompt tests that currently require long prose, but keep tests for behavior-critical phrases:
    - `/cg-plan` Step 0.7 Branch Offer ordering and safety.
    - `/cg-plan` phase output contract.
    - `/cg-work` phase parser and boundary invariants.
    - `/cg-work` red-phase gate and Pester safety.
    - `/cg-work` roadmap active/done updates.
    - `/cg-work` review-mode integration.
- **Acceptance criteria**:
  - Tests guard behavior and contracts, not exact long-form prose.
  - No tests are deleted just to permit weaker prompt behavior.

### 5. Run Codex-side validation and regenerate audit

- **Requirements**: R3, R13
- **Files**:
  - `.cg-docs/cost/context-audit.json`
  - `.cg-docs/cost/context-audit.md`
- **Details**:
  - Run Python audit tests:
    - `python3 -m pytest scripts/tests/test_audit_context.py`
  - Regenerate the audit:
    - `python3 scripts/cg_audit_context.py --format both`
  - Pester validation should use the project-safe pattern, not ad hoc `Invoke-Pester` loops:
    - `. tests\Run-Tests.ps1`
    - Inspect `tests/last-run.json`.
  - If only targeted Pester is needed in VS Code, run the relevant file through the safe runner rather than `Invoke-Pester tests/`.
  - Confirm audit results:
    - No premium model usage.
    - No missing model declarations.
    - No model drift.
    - `/cg-plan` and `/cg-work` character/token counts reduced against baseline.
    - `/cg-work` remains classified as conditional review routing.
- **Acceptance criteria**:
  - Audit report is refreshed and shows the before/after improvement.
  - Any inability to run Pester in Codex is documented; VS Code remains the validation harness for runtime behavior.

### 6. Manual VS Code Copilot validation

- **Requirements**: R4, R5, R6, R7, R8, R9, R13
- **Files**:
  - No code changes in this step; validation only.
- **Details**:
  - `/cg-plan`:
    - Invoke on a small known task.
    - Confirm the first output includes the short model-context note.
    - With Copilot Auto selected, confirm it does not name the underlying model.
    - Confirm it still loads staged context, offers branch creation only when applicable, writes a plan under `.cg-docs/plans/`, phases by default when appropriate, and offers `/cg-work` / `/cg-plan-review` handoff.
  - `/cg-work`:
    - Run against a lightweight plan without a review argument.
    - Confirm it does not dispatch review agents.
    - Confirm it still follows phase/test/roadmap behavior and recommends a review mode at the end.
  - `/cg-work review:auto`:
    - Run against a prompt-only or low-risk plan and a higher-risk fixture if available.
    - Confirm it resolves a route through `.github/shared/review-routing.contract.md` and dispatches only route-appropriate agents.
  - `/cg-work review:manual`:
    - Confirm it does not dispatch agents and emits a structured manual review recommendation with suggested `/cg-review <mode>`.
  - `/cg-work review:none`:
    - Confirm it dispatches nothing and emits only a brief suppression note.
  - Pending carryover:
    - Record that `/cg-work review:*` runtime validation was pending before Phase 4 and must pass before calling Phase 4 fully complete.
- **Acceptance criteria**:
  - Runtime behavior matches Phase 2 and Phase 3 contracts.
  - No validation path depends on hidden model identity.

## Testing Strategy

- Use prompt contract tests for structure and invariants.
- Use model-governance tests to prevent premium-model regression.
- Use Python audit tests for context/model report behavior.
- Use regenerated audit artifacts for before/after token burden comparison.
- Use manual VS Code Copilot validation for actual slash-command runtime behavior.

## Documentation Checklist

- [ ] Update `.cg-docs/cost/context-audit.md` by regenerating it after implementation.
- [ ] Update `docs/model-guide.md` only if `/cg-plan` model-context note reveals a documentation gap.
- [ ] Do not update broad workflow docs unless prompt behavior or command syntax changes.
- [ ] Do not document hidden Copilot Auto model identity.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Prompt slimming makes safety behavior implicit | Keep behavior-critical gates in the prompt and use shared contracts only for reusable mechanics. Roll back if the agent no longer knows when to stop, ask, test, or dispatch. |
| Tests become regex anchors for obsolete prose | Update tests to assert behavior-critical contracts and ordering, not long explanatory paragraphs. |
| `/cg-work review:*` Phase 3 behavior regresses | Preserve existing tests and perform manual VS Code runtime validation for all review modes. |
| Context loading becomes too sparse | Keep staged context loading explicit: charter/local/context first, then 3-5 relevant files, then conditional skills/contracts. |
| Model-governance note overclaims Auto model identity | Explicitly forbid hallucinating the underlying Auto-selected model and point to Copilot UI/hover details instead. |

## Rollback Criteria

Rollback or revise the slimming if any of the following occur:

- `/cg-plan` no longer produces the required plan artifact shape or phase contract.
- `/cg-plan` omits the model-context note or claims to know Copilot Auto's underlying model.
- `/cg-work` defaults to automatic review dispatch.
- `/cg-work review:auto`, `review:manual`, or `review:none` no longer matches Phase 3 behavior.
- Test, diagnostics, phase-boundary, roadmap, or safety gates become weaker, ambiguous, or dependent on external memory.
- Audit shows model-governance drift, premium model regression, or no meaningful prompt-size reduction.

## Out of Scope

- Changing Phase 2 model-governance policy.
- Reintroducing hard-coded premium models.
- Redesigning `/cg-review` routing from Phase 3.
- Changing Knowledge Brain retrieval behavior.
- Refactoring Team Brain behavior.
- Rewriting all skills.
- Targeting `/cg-setup`.
- Targeting `/cg-review-repos`.
- Implementing this plan before approval.
