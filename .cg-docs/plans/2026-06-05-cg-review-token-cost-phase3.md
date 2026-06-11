---
date: 2026-06-05
title: "Phase 3: staged /cg-review routing + /cg-work review-mode integration"
status: completed
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-06-04-context-model-audit-infrastructure.md"
language: "both"
estimated-effort: "medium"
tags: [performance, token-optimization, review, routing, safety, model-governance, cg-work]
phases: 2
---

# Plan: Phase 3 - Staged Review Routing and /cg-work Review-Mode Integration

## Objective

Reduce token and model-call cost for review workflows by making `/cg-review` staged and risk-aware by default, and adding explicit review-mode integration in `/cg-work` so post-implementation review behavior is deterministic, cheaper by default, and still safe for high-risk changes.

## Context

Phase 1 created the context/model audit infrastructure and surfaced high-cost hotspots. Phase 2 removed hard-coded premium defaults from ordinary workflow prompts and validated model-governance consistency. The latest audit (`.cg-docs/cost/context-audit.md`) shows no premium model usage drift, no missing model declarations, and no model drift.

The remaining cost driver is review orchestration fan-out. `/cg-review` is large and currently mixes depth selection, escalation triggers, and broad dispatch behavior. `/cg-work` currently ends with a static recommendation to run `/cg-review`, without review-mode-aware integration.

This phase introduces a shared routing contract, updates `/cg-review` to staged dispatch, and integrates `/cg-work` review modes:
- `review:auto`
- `review:manual`
- `review:none`
- optional explicit routed modes: `review:light`, `review:standard`, `review:data-risk`, `review:architecture`, `review:full`

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Identify and reduce concrete `/cg-review` cost drivers | user + audit |
| R2 | Define staged review modes with deterministic dispatch rules | user |
| R3 | Preserve P0/P1 detection strength and safety gates | user |
| R4 | Preserve mandatory data-risk escalation for statistical/survey/poverty/welfare/joins/aggregation/reproducibility-sensitive changes | user |
| R5 | Preserve review report generation and findings/frontmatter flow | user |
| R6 | Preserve explicit user ability to request full review | user |
| R7 | Keep Phase 2 model-governance policy unchanged | user |
| R8 | Avoid broad agent refactors in this phase | user |
| R9 | Add test coverage for routing and integration behavior | user |
| R10 | Define post-implementation audit checks with explicit triggers | user |
| R11 | Define manual VS Code runtime validation steps | user |
| R12 | Define rollback criteria if behavior becomes ambiguous or weaker | user |
| R13 | Add `/cg-work` review-mode argument parsing (`review:auto|manual|none` + optional explicit modes) | user |
| R14 | Default `/cg-work` must not auto-dispatch review agents | user |
| R15 | Default `/cg-work` must recommend a review mode at handoff | user |
| R16 | `/cg-work review:auto` must use the same routing logic as `/cg-review` | user |
| R17 | `/cg-work review:manual` must not dispatch agents and must provide recommendation | user |
| R18 | `/cg-work review:none` must suppress review dispatch and show only a brief note | user |

## Implementation Steps

## Phase 1: Shared Routing Contract and /cg-review Staged Dispatch

### 1. Create a shared review-routing contract artifact
- **Requirements**: R1, R2, R13, R16
- **Files**:
  - `.github/shared/review-routing.contract.md` (new)
  - `.github/prompts/cg-review.prompt.md`
  - `.github/prompts/cg-work.prompt.md`
- **Details**:
  - Add a compact canonical routing contract (mode names, trigger taxonomy, precedence, required escalations, dedup rules).
  - Both `/cg-review` and `/cg-work` reference this contract to avoid prose duplication.
  - Define explicit mode-to-agent dispatch matrix in the shared contract:

    | Mode | Required agents |
    |------|------------------|
    | `light` | `@cg-code-quality`, `@cg-testing` |
    | `standard` | `@cg-code-quality`, `@cg-testing`, `@cg-documentation`, `@cg-version-control`, `@cg-reproducibility`, `@cg-performance`, `@cg-architecture`, `@cg-data-quality` |
    | `data-risk` | all `standard` agents (deduped) with mandatory escalation emphasis on `@cg-data-quality` and `@cg-reproducibility` |
    | `architecture` | all `standard` agents (deduped) with mandatory escalation emphasis on `@cg-architecture` and `@cg-performance` |
    | `full` | `standard` + `@cg-learnings-researcher` + `@cg-adversarial` |

  - Define risk class names as internal-only selectors and map them to user-facing modes:

    | Internal risk class | Resolved mode |
    |---------------------|---------------|
    | `low` | `light` |
    | `normal` | `standard` |
    | `data-risk` | `data-risk` |
    | `architecture-risk` | `architecture` |
    | `security-risk` | `full` |

  - Canonical precedence rule:
    1. explicit user mode
    2. verify/report-only guard behavior
    3. risk-class routing result
    4. line-volume escalation
    5. config default
  - Define additive dedup rule: if multiple rules request the same agent, dispatch once.
- **Test Scenarios**:
  - Happy path: both prompts reference one shared routing source.
  - Edge case: conflicting triggers resolve deterministically.
  - Error path: missing contract reference in either prompt fails tests.
- **Tests (write first, then implement)**:
  - Add contract-presence and prompt-reference assertions in `tests/prompt-tools.Tests.ps1` before prompt edits.
- **Acceptance criteria**:
  - Shared contract exists and is referenced by both `/cg-review` and `/cg-work`.

### 2. Update `/cg-review` parser and mode taxonomy
- **Requirements**: R2, R6
- **Files**:
  - `.github/prompts/cg-review.prompt.md`
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Extend recognized mode/flag parser to include staged modes (`light`, `standard`, `data-risk`, `architecture`, `full`) while keeping existing compatibility (`thorough`, `mode:verify`, `mode:autofix`, `--report-only`, `--no-brain`).
  - Update unrecognized-argument warning text to include new accepted modes.
  - Define mapping for backward compatibility:
    - `thorough` maps to `full` dispatch semantics unless verify/report-only constrains it.
- **Test Scenarios**:
  - Happy path: explicit `data-risk` and `full` are recognized.
  - Edge case: `thorough` still works and maps deterministically.
  - Error path: unrecognized argument warning remains accurate and exhaustive.
- **Tests (write first, then implement)**:
  - Add parser/warning contract assertions in `tests/prompt-tools.Tests.ps1` before prompt edits.
- **Acceptance criteria**:
  - New modes are invocable and not ignored by parser.

### 3. Refactor `/cg-review` preflight and dispatch matrix with explicit Step 1.5 reconciliation
- **Requirements**: R2, R3, R4, R5
- **Files**:
  - `.github/prompts/cg-review.prompt.md`
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Introduce internal risk classes: low, normal, data-risk, architecture-risk, security-risk.
  - Reconcile existing Step 1.5 overrides with staged modes by replacing ad-hoc per-agent adds with mode resolution logic:
    - statistical/reproducibility triggers resolve to `data-risk`
    - architecture/performance-heavy triggers resolve to internal `architecture-risk`, which maps to user mode `architecture`
    - very large/high-risk or explicit request resolves to `full`
  - Keep mandatory data-risk escalation clauses intact.
  - Keep verify mode light-only and exempt from staged broad routing.
  - Line-volume rule interaction is explicit:
    - line-volume can raise `light -> standard`
    - risk-class modes (`data-risk`, `architecture`, `full`) take precedence over line-volume upgrades
- **Test Scenarios**:
  - Happy path: small low-risk changes do not trigger broad fan-out.
  - Edge case: mixed statistical + architecture changes produce deterministic highest-risk route with deduped agents.
  - Error path: missing changed-file scope triggers prompt for scope and no silent broad default dispatch.
- **Tests (write first, then implement)**:
  - Add Step 1.5 reconciliation and precedence assertions in `tests/prompt-tools.Tests.ps1` before prompt edits.
- **Acceptance criteria**:
  - Step 1.5 and staged routing are consistent and non-duplicative.

### 4. Preserve safety and report invariants with narrow scope control
- **Requirements**: R3, R4, R5, R7, R8
- **Files**:
  - `.github/prompts/cg-review.prompt.md`
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Preserve existing P0/P1 strictness language.
  - Preserve data-risk escalation language for specified statistical/data domains.
  - Preserve report generation and findings frontmatter behavior.
  - Scope control for this phase:
    - Do not create new agent files.
    - Do not modify agent model assignments.
    - Do not refactor agent internals.
  - Agent files are read-only unless a single-line clarification is strictly required; if any agent file must change, list exact file and clause in PR before edit.
- **Test Scenarios**:
  - Happy path: report structure unchanged and usable.
  - Edge case: verify mode remains constrained.
  - Error path: regression in severity or report sections is caught by tests.
- **Tests (write first, then implement)**:
  - Add invariant assertions before prompt edits where missing.
- **Acceptance criteria**:
  - No regression in safety/report contracts.

## Phase 2: /cg-work Review-Mode Integration, Validation, and Audit

### 5. Add `/cg-work` review-mode argument parsing and behavior
- **Requirements**: R13, R14, R15, R16, R17, R18
- **Files**:
  - `.github/prompts/cg-work.prompt.md`
  - `.github/prompts/cg-review.prompt.md` (reference alignment only)
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Add three explicit integration injection points in `/cg-work`:
    1. Extend Step 0.4 to parse `review:*` arguments alongside `--no-brain`.
    2. Add new Step 3.9 after Step 3.8 to execute review-mode behavior:
       - `review:auto`: run route-aware agent dispatch using the shared routing contract.
       - `review:manual` or default (no review arg): emit review-mode recommendation only.
       - `review:none`: emit brief suppression note only.
    3. Update Step 4 summary menu to be mode-aware:
       - default and `review:manual`: keep recommendation path to run `/cg-review` with suggested mode.
       - `review:auto`: indicate review already dispatched with resolved mode.
       - `review:none`: suppress automatic review recommendation verbosity and show brief note.

  - Parse optional review argument values in `/cg-work`:
    - `review:auto`
    - `review:manual`
    - `review:none`
    - optional explicit routed values: `review:light`, `review:standard`, `review:data-risk`, `review:architecture`, `review:full`
  - Default behavior when no review argument provided:
    - do not auto-dispatch review agents
    - provide recommended review mode at handoff based on shared routing contract signals
  - `review:auto` behavior:
    - evaluate same routing contract used by `/cg-review`
    - dispatch only the route-appropriate agent set
  - `review:manual` behavior:
    - no agent dispatch
    - show structured recommendation and suggested command
  - `review:none` behavior:
    - suppress dispatch
    - show brief note only
- **Test Scenarios**:
  - Happy path: each mode produces correct dispatch/no-dispatch behavior.
  - Edge case: explicit mode + risky diff still preserves mandatory escalations when dispatching.
  - Error path: invalid `review:<value>` warns and falls back to recommendation mode.
- **Tests (write first, then implement)**:
  - Add `/cg-work` review-mode parser and behavior contract assertions in `tests/prompt-tools.Tests.ps1` before prompt edits.
- **Acceptance criteria**:
  - `/cg-work` review-mode integration works as specified without default auto-dispatch.

### 6. Regression and full-suite testing gates
- **Requirements**: R9
- **Files**:
  - `tests/prompt-tools.Tests.ps1`
  - `tests/model-assignments.Tests.ps1` (regression only)
- **Details**:
  - After each implementation step, run targeted prompt contract tests.
  - Run full suite with canonical runner before completion.
  - Keep model-governance tests unchanged unless docs wording requires test-text update.
- **Tests**:
  - `Invoke-Pester tests/prompt-tools.Tests.ps1 -Quiet`
  - `. tests/Run-Tests.ps1` and verify `tests/last-run.json`
- **Acceptance criteria**:
  - New contracts pass and existing tests remain green.

### 7. Audit and runtime validation with explicit trigger for audit script edits
- **Requirements**: R10, R11
- **Files**:
  - `.cg-docs/cost/context-audit.md` (generated)
  - `scripts/cg_audit_context.py` (only under explicit trigger)
- **Details**:
  - Re-run context/model audit and compare `/cg-review` burden metrics against baseline.
  - Explicit trigger for changing `scripts/cg_audit_context.py`:
    - only modify if current audit output cannot represent dispatch burden change after staged routing (for example: lacks any route-count or dispatch-burden indicator needed to compare before/after).
    - if trigger is not met, keep script unchanged.
  - Manual VS Code validation matrix:
    - `/cg-work` default (no review arg): no dispatch + recommendation
    - `/cg-work review:auto`: route-aware dispatch
    - `/cg-work review:manual`: recommendation only
    - `/cg-work review:none`: brief note only
    - `/cg-review` explicit `data-risk` and `full` modes
- **Tests**:
  - Existing Python tests only if audit script is modified.
- **Acceptance criteria**:
  - Cost/behavior evidence captured with no unnecessary audit tool scope expansion.

## Testing Strategy

- Follow test-first ordering for each step: add/adjust prompt contract tests before editing prompt behavior.
- Maintain regression protection for existing `/cg-review` verify/safety/report features.
- Use full-suite gate before completion.
- If audit script changes, run its targeted Python tests and regenerate audit output.

## Documentation Checklist

- [ ] Update prompt text where behavior changed
- [ ] Keep model-governance policy unchanged
- [ ] Add brief usage examples for `/cg-work review:<mode>` in relevant docs if touched
- [ ] Keep contract language concise and non-duplicative by referencing shared routing contract

## Risks and Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Routing ambiguity between old Step 1.5 and new modes | Wrong dispatch and higher cost | Explicit reconciliation and precedence table in prompt + tests |
| New mode names parsed incorrectly | Modes ignored at runtime | Parser tests and warning-message contract tests |
| `/cg-work` duplicates stale routing logic | Drift and maintenance debt | Shared routing contract referenced by both prompts |
| Over-optimization misses high-risk defects | Safety regression | Preserve mandatory escalations and P0/P1 strictness |
| Scope creep into agent internals | Delays and unstable behavior | Agent files read-only by default in this phase |

## Rollback Criteria

Rollback (full or partial) is required if any occur:
1. P0/P1 findings that were previously detected are no longer surfaced in comparable high-risk scenarios.
2. Data-risk escalation fails for statistical/reproducibility-sensitive changes.
3. `/cg-work` default unexpectedly dispatches agents without explicit review mode.
4. `/cg-work review:auto` does not align with `/cg-review` routing outcomes for equivalent diffs.
5. Review report generation or findings frontmatter contract regresses.

Primary rollback target order:
1. Revert `/cg-work` review-mode integration changes in `.github/prompts/cg-work.prompt.md`.
2. Revert staged dispatch changes in `.github/prompts/cg-review.prompt.md`.
3. Keep unrelated verified safety/report improvements where valid.

## Out of Scope

- Broad refactor of review agent internals.
- Model-governance policy redesign from Phase 2.
- New standalone review commands outside `/cg-review` and `/cg-work` review-mode arguments.
- Audit-tool changes without explicit trigger condition.

## Acceptance Criteria

1. `/cg-review` no longer defaults to broad agent fan-out for small or low-risk changes.
2. High-risk data/statistical/security/architecture changes still escalate correctly.
3. Users can still explicitly request `full` review.
4. `/cg-work` supports `review:auto`, `review:manual`, and `review:none`, with optional explicit route modes.
5. `/cg-work` default does not auto-dispatch review agents and gives a review-mode recommendation.
6. `/cg-work review:auto` uses the same routing contract as `/cg-review` and dispatches only route-appropriate agents.
7. `/cg-work review:manual` dispatches no agents and provides recommendation only.
8. `/cg-work review:none` dispatches no agents and shows brief note only.
9. Existing tests pass and new contract tests for parser/routing behavior pass.
10. Audit/runtime validation shows reduced or better-justified review dispatch burden and preserved review quality.
