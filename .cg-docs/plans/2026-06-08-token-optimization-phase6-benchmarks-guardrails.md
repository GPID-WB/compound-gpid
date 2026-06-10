---
date: 2026-06-08
title: "Token Optimization Phase 6 - Benchmarks, Guardrails, and Release Readiness"
status: completed
completed-date: 2026-06-08
scope: "Standard"
brainstorm: null
language: "Python/PowerShell/Markdown"
estimated-effort: "medium"
tags: [token-cost, benchmark, guardrails, audit, release-readiness]
phases: 3
---

# Plan: Token Optimization Phase 6 - Benchmarks, Guardrails, and Release Readiness

## Objective

Create a repeatable benchmark and regression-guardrail system that verifies whether the Phase 2-5 token-optimization work reduced context burden and model-cost risk while preserving workflow behavior.

## Context

Phase 1 created the context/model audit. Phase 2 removed hard-coded premium Opus defaults from ordinary workflow prompts and validated model-picker behavior. Phase 3 reduced `/cg-review` cost with staged/conditional routing and `/cg-work review:*` integration. Phase 4 slimmed `/cg-plan` and `/cg-work`, added model-context behavior, and stabilized workflow contracts. Phase 5 made Knowledge Brain and context loading more selective and query-driven.

Latest audit baseline: `.cg-docs/cost/context-audit.md`, generated `2026-06-08T09:03:18`.

Current audit facts to preserve and benchmark:

| Signal | Current baseline |
|--------|------------------|
| Total estimated context tokens | 371,345 |
| Prompt estimated tokens | 56,044 |
| Always-on instructions estimated tokens | 3,414 |
| Shared contracts estimated tokens | 1,538 |
| `/cg-plan` prompt | 9 refs, 7 load verbs, 22 total refs, model picker |
| `/cg-work` prompt | 18,702 chars / 4,675 tokens, 47 total refs, conditional review routing |
| `/cg-review` prompt | 18,955 chars / 4,738 tokens, 53 total refs, conditional review routing |
| Context loading signals | 28 risk, 9 justified, 74 targeted |
| Model governance | no missing declarations, no model drift, no premium usage |
| Ordinary model-picker prompts | `/cg-brainstorm`, `/cg-ideate`, `/cg-plan`, `/cg-plan-review`, `/cg-review-repos`, `/cg-strategy` have no `model:` key |

Brain findings used:

- Phase 3 and Phase 4 stabilized route precedence and `/cg-work review:*` behavior: explicit `/cg-review` modes win; auto risk routing applies only without explicit mode; `/cg-work` supports `review:auto`, `review:manual`, and `review:none`.
- Phase 5 introduced `.github/shared/context-loading.contract.md` and `scripts/cg_audit_context.py` context-loading risk classification, so Phase 6 should extend existing audit tooling rather than create a new architecture.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Define a small benchmark suite for `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-compound`, `/cg-resume`, and Knowledge Brain/context lookup behavior. | user |
| R2 | Measure prompt estimated tokens, prompt reference counts, premium model usage, missing/drifted model declarations, broad context-loading signals, Knowledge Brain broad-read signals, review-routing burden, and statically measurable review-agent counts by mode. | user |
| R3 | Define thresholds for high-frequency prompt size, always-on instruction size, model governance, broad context loading, Knowledge Brain loading, `/cg-review` routed modes, and `/cg-work review:*` modes. | user |
| R4 | Add regression checks for ordinary premium model reintroduction and model-picker prompts regaining explicit `model:` frontmatter. | user |
| R5 | Add regression checks for broad loading of `.cg-docs`, `BRAIN.md`, `brain-index.json`, `compound-gpid.context.md`, or `roadmap.json` without selective/context-expansion rules. | user |
| R6 | Add regression checks that `/cg-review` preserves explicit route precedence and explicit full review. | user |
| R7 | Add regression checks that `/cg-work` preserves `review:auto`, `review:manual`, and `review:none`. | user |
| R8 | Produce benchmark output with before/after summary, current audit baseline, top remaining candidates, release-readiness checklist, and manual VS Code/Copilot checklist. | user |
| R9 | Prefer extending `scripts/cg_audit_context.py`; create a separate script only if audit becomes too broad. | user |
| R10 | Add or update focused tests without broad prompt slimming or workflow redesign. | user |
| R11 | Document manual VS Code/Copilot validation for model-picker behavior, `/cg-plan`, `/cg-work review:auto`, `/cg-work review:manual`, `/cg-review light`, `/cg-review data-risk`, `/cg-review full`, and Knowledge Brain selective retrieval. | user |
| R12 | Preserve all Phase 2-5 behavior and do not change model-governance policy, Team Brain, Knowledge Brain architecture, `/cg-review` design, or roadmap schema except an optional plan link. | user |

## Benchmark Suite

The benchmark should be lightweight and static-first, with manual runtime validation only where static checks cannot prove behavior.

| Workflow | Static benchmark | Runtime validation |
|----------|------------------|--------------------|
| `/cg-plan` | prompt tokens, reference counts, model-picker status, context-loading risk count, model-context note present | plan creation starts with model-context note and uses targeted Brain/context expansion |
| `/cg-work` | prompt tokens, reference counts, conditional dispatch burden, `review:*` mode contract text, targeted roadmap/context rules | `review:auto` dispatches routed agents; `review:manual` recommends only; `review:none` suppresses |
| `/cg-review` | prompt tokens, reference counts, conditional dispatch burden, route precedence text, route-to-agent counts | `light`, `data-risk`, and `full` resolve expected routes and preserve explicit full |
| `/cg-compound` | prompt tokens, context-loading risk/justified signals, Brain rebuild language preserved | solution capture still rebuilds/query-updates Brain selectively; no broad read unless enrichment requires it |
| `/cg-resume` | prompt tokens, justified roadmap read remains explicit, metadata scan rules present | resume summary computes roadmap health without carrying unrelated records into the summary |
| Knowledge Brain/context lookup | broad-read signal counts for `BRAIN-log.md`, `BRAIN-NN.md`, `brain-index.json`, `.cg-docs/`; `cg-skill-brain-query` query-first rules | Brain query reads `BRAIN.md` index, chooses matched topic(s), and opens only relevant sections |

## Guardrail Thresholds

Use thresholds as audit warnings unless explicitly listed as fail-fast. The goal is preventing regression, not forcing another slimming pass.

| Guardrail | Threshold | Severity |
|-----------|-----------|----------|
| High-frequency prompt size: `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-compound`, `/cg-resume` | Warn above 5,000 estimated tokens; fail if above 6,000 or above the recorded Phase 6 baseline by more than 15% without an inline rationale. | warn/fail |
| Always-on instructions size: `.github/copilot-instructions.md` plus `.github/instructions/*.instructions.md` | Warn above 4,500 total estimated tokens; fail above 6,000. Current baseline is 3,414. | warn/fail |
| Ordinary workflow prompt model picker | No `model:` key in the six Phase 2 ordinary prompts. | fail |
| Premium models | No explicit Opus/premium model assignment unless a future dedicated premium workflow has an escalation rationale and test coverage. | fail |
| Model drift | Frontmatter model assignments must match `docs/model-guide.md` for explicit-model prompts/agents. | fail |
| Broad context loading in ordinary prompts | No unqualified full reads of `.cg-docs`, `BRAIN-log.md`, `BRAIN-NN.md`, `brain-index.json`, `compound-gpid.context.md`, or `roadmap.json` without targeted/context-expansion wording. | fail for ordinary prompts; warn elsewhere |
| Knowledge Brain broad reads | Prompt/skill text must not instruct reading all Brain partitions or `brain-index.json` wholesale by default. `BRAIN.md` meta-index remains allowed. | fail |
| `/cg-review` routing | Must preserve routed modes `light`, `standard`, `data-risk`, `architecture`, `full`; explicit full/thorough remains available; explicit user modes win over auto routing except verify guard behavior. | fail |
| `/cg-work` review modes | Must preserve `review:auto`, `review:manual`, `review:none`, and explicit routed modes; default/manual never dispatch automatically. | fail |
| Review-agent counts by mode | Static contract counts: light = 2; standard = 8; data-risk = 8 with mandatory emphasis; architecture = 8 with mandatory emphasis; full = 10. | fail |

## Phase 1: Extend Audit Benchmark Output

### 1. Add Benchmark Baseline And Workflow Summary

- **Requirements**: R1, R2, R8, R9
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
  - `.cg-docs/cost/context-audit.json` (generated)
  - `.cg-docs/cost/context-audit.md` (generated)
- **Details**:
  - Extend `build_report()` with a `benchmark` object rather than creating a separate script.
  - Add a fixed workflow list for `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-compound`, `/cg-resume`, and Knowledge Brain/context lookup.
  - For prompt workflows, pull from existing `files`, `reference_matrix`, `dispatch_burden`, `model_inventory`, and `context_loading_risks`.
  - For Knowledge Brain/context lookup, aggregate Brain-related broad-read signals from `context_loading_risks` and include whether `cg-skill-brain-query` still contains query-first/matched-topic language.
  - Include current audit baseline values in JSON and Markdown:
    - prompt tokens and chars
    - total references and load verbs
    - model tier / model-picker state
    - context-loading risk counts by workflow
    - dispatch burden and conditional-routing boolean
    - review-agent counts where statically measurable
  - Keep the implementation stdlib-only.
- **Test Scenarios**:
  - Happy path: `build_report()` includes a `benchmark` section with all six workflow rows.
  - Edge case: missing workflow file produces a warning row, not a crash.
  - Error path: missing `cg-skill-brain-query` marks Knowledge Brain benchmark unavailable.
- **Tests**:
  - Add Python tests for benchmark row construction and Markdown section rendering.
  - Update JSON/Markdown output tests to expect the new section.
- **Acceptance criteria**:
  - `context-audit.json` contains a machine-readable benchmark summary.
  - `context-audit.md` contains a human-readable "Benchmark Summary" section.
  - No separate benchmark script exists unless this step proves the audit script becomes hard to maintain.

### 2. Add Before/After Comparison Support

- **Requirements**: R2, R8, R9
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
  - Optional generated file: `.cg-docs/cost/context-audit-baseline.json`
- **Details**:
  - Add an optional CLI flag such as `--baseline <path>` that reads a previous `context-audit.json`.
  - Compare current benchmark rows against baseline rows by workflow/file path.
  - Report deltas for:
    - estimated tokens
    - total references
    - premium usage count
    - ordinary model-picker violations
    - context-loading risk count
    - dispatch burden level and dispatch ref count
  - If no baseline is passed, render "Current audit baseline" only and skip deltas.
  - Do not make baseline comparison required for normal `python scripts/cg_audit_context.py --format both`.
- **Test Scenarios**:
  - Happy path: previous and current prompt token counts render as negative/positive deltas.
  - Edge case: baseline lacks a workflow row; current row still renders.
  - Error path: malformed baseline JSON returns a clear CLI error and nonzero exit code.
- **Tests**:
  - Unit test baseline loading and delta computation with temporary JSON fixtures.
  - CLI test for malformed baseline error handling.
- **Acceptance criteria**:
  - Maintainers can run one command to compare Phase 6 output against a saved baseline.
  - Existing audit behavior remains unchanged when no baseline is provided.

## Phase 2: Add Regression Guardrail Checks

### 3. Add Audit-Level Guardrail Classification

- **Requirements**: R3, R4, R5, R6, R7, R10, R12
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
- **Details**:
  - Add a `guardrails` object to the audit report with `failures` and `warnings`.
  - Use the thresholds in this plan.
  - Fail ordinary prompts that regain explicit `model:` frontmatter.
  - Fail premium model usage unless explicitly allowlisted in a future premium-workflow allowlist with rationale.
  - Fail broad context-loading risks in ordinary prompts for `.cg-docs`, `BRAIN-log.md`, `BRAIN-NN.md`, `brain-index.json`, `compound-gpid.context.md`, or `roadmap.json`.
  - Warn, not fail, for maintenance agents/prompts where broad reads are expected but should still be visible.
  - Fail if `/cg-review` does not contain effective route precedence language:
    - explicit user modes win
    - auto risk-class routing applies only when no explicit mode is requested
    - full/thorough remains available
    - verify mode remains light-only
  - Fail if `/cg-work` does not contain:
    - `review:auto`
    - `review:manual`
    - `review:none`
    - default/manual no automatic dispatch
    - `review:auto` route-aware dispatch through shared contract
  - Fail if `.github/shared/review-routing.contract.md` route-agent counts drift from the expected 2/8/8/8/10 mode counts.
- **Test Scenarios**:
  - Happy path: current repo passes model/routing guardrails and reports remaining broad-load risks as scoped warnings/failures according to file class.
  - Edge case: `/cg-resume` justified full `roadmap.json` read remains justified, not a failure.
  - Error path: fixture ordinary prompt with `model: Claude Opus` creates a failure.
  - Error path: fixture prompt reading `brain-index.json` before planning creates a failure.
  - Error path: removing `review:auto` from a fixture `/cg-work` creates a failure.
- **Tests**:
  - Add Python unit tests for guardrail severity classification.
  - Keep existing Pester model/prompt contract tests; do not delete coverage to satisfy the new audit.
- **Acceptance criteria**:
  - The audit can be used as a pre-merge regression gate.
  - Guardrail failures are specific enough to point maintainers to file and reason.

### 4. Strengthen Pester Prompt Contract Tests

- **Requirements**: R4, R6, R7, R10, R12
- **Files**:
  - `tests/model-assignments.Tests.ps1`
  - `tests/prompt-tools.Tests.ps1`
  - `.github/skills/cg-skill-pester-safety/SKILL.md` (read only unless test instructions need wording alignment)
- **Details**:
  - In `tests/model-assignments.Tests.ps1`, keep the existing ordinary-prompt no-`model:` tests and docs/reference model-picker sync.
  - In `tests/prompt-tools.Tests.ps1`, add narrow tests where current coverage is implicit or brittle:
    - `/cg-review` explicit route precedence is asserted through effective text, not only table order.
    - `/cg-review full` and `thorough` alias remain explicitly requestable.
    - `/cg-work` default and `review:manual` never dispatch review agents.
    - `/cg-work review:auto` references `.github/shared/review-routing.contract.md` and dispatches only route-appropriate agents.
    - `/cg-work review:none` suppresses dispatch and handoff verbosity.
    - `cg-skill-brain-query` warns against wholesale `brain-index.json` reads while allowing tooling query use.
  - Do not run unsafe ad hoc Pester commands. Use the project safe runner for validation.
- **Test Scenarios**:
  - Happy path: current prompt contracts pass.
  - Edge case: route precedence wording changes but effective rule remains; test should allow equivalent wording.
  - Error path: missing `review:none` or explicit full review fails.
- **Tests**:
  - Pester via `. tests\Run-Tests.ps1` and `tests/last-run.json`.
  - If Codex cannot run PowerShell/Pester, document this and leave VS Code validation as the harness.
- **Acceptance criteria**:
  - Prompt contract tests protect Phase 2-5 behavior without forcing exact long-form prose.

## Phase 3: Release-Readiness Documentation And Validation

### 5. Document The Maintainer Validation Workflow

- **Requirements**: R8, R11, R12
- **Files**:
  - `docs/workflow.md`
  - `docs/reference.md`
  - `docs/model-guide.md`
  - Optional: `.cg-docs/cost/README.md` if a short benchmark-run note fits better than expanding public docs
- **Details**:
  - Document the pre-merge/release validation workflow:
    1. Save or identify the baseline audit JSON.
    2. Run `python3 -m pytest scripts/tests/test_audit_context.py`.
    3. Run `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --baseline <baseline-json>` when comparing before/after.
    4. Run `. tests\Run-Tests.ps1` in VS Code/PowerShell and inspect `tests/last-run.json`.
    5. Review the audit's `Benchmark Summary`, `Guardrails`, `Context Loading Risks`, `Review Dispatch Burden`, and `Model Inventory`.
    6. Complete the manual VS Code/Copilot checklist below.
  - Keep docs concise. Link to `context-audit.md` instead of copying large tables.
  - Do not change model-governance policy or command semantics.
- **Release-readiness checklist**:
  - [ ] Audit generated successfully.
  - [ ] Guardrail failures are zero, or any warning is documented as maintenance-intentional.
  - [ ] Ordinary model-picker prompts still omit `model:`.
  - [ ] Premium model usage remains zero.
  - [ ] `/cg-review` and `/cg-work` remain conditional, not broad, dispatch workflows.
  - [ ] Broad Brain/context reads are either targeted, justified, or maintenance-only.
  - [ ] Top remaining optimization candidates are reviewed and either accepted or filed as future work.
  - [ ] Python tests pass.
  - [ ] Pester safe runner passes in VS Code/PowerShell.
  - [ ] Manual VS Code/Copilot runtime checklist is complete.
- **Acceptance criteria**:
  - Maintainers know exactly what to run before merging token-optimization changes.
  - Runtime validation remains assigned to GitHub Copilot / VS Code.

### 6. Define Manual VS Code/Copilot Validation

- **Requirements**: R1, R6, R7, R11, R12
- **Files**:
  - Documentation only; no prompt behavior changes unless implementation discovers a missing documented contract.
- **Details**:
  - Model-picker behavior:
    - Set Copilot model picker to Auto.
    - Run `/cg-plan` on a small task.
    - Confirm the first output says it inherits the GitHub Copilot model picker and does not name the hidden Auto-selected model.
    - Set the picker to a non-premium standard model and confirm ordinary model-picker prompts run without requiring `model:` frontmatter.
  - `/cg-plan`:
    - Confirm it reads charter/local config, loads context-loading contract, checks prior plans, and writes a plan under `.cg-docs/plans/`.
    - Confirm any `compound-gpid.context.md` or `roadmap.json` expansion states a reason first.
  - `/cg-work review:auto`:
    - Run on a low-risk prompt/doc fixture and one data-risk fixture if available.
    - Confirm it resolves a route through `.github/shared/review-routing.contract.md` and dispatches only route-appropriate agents.
  - `/cg-work review:manual`:
    - Confirm no review agents are dispatched.
    - Confirm output recommends a specific `/cg-review <mode>` command.
  - `/cg-work review:none`:
    - Confirm no review agents are dispatched and review handoff is suppressed to a brief note.
  - `/cg-review light`:
    - Run on a small low-risk diff.
    - Confirm only `@cg-code-quality` and `@cg-testing` are dispatched.
  - `/cg-review data-risk`:
    - Run on a data/statistical fixture or simulated changed-file scope.
    - Confirm standard agents are dispatched with mandatory `@cg-data-quality`, `@cg-reproducibility`, and testing emphasis.
  - `/cg-review full`:
    - Confirm full is explicitly requestable and includes `@cg-learnings-researcher` and `@cg-adversarial`.
  - Knowledge Brain selective retrieval:
    - Invoke a workflow with known Brain matches.
    - Confirm it reads `BRAIN.md`, selects matched topic(s), and opens only relevant `BRAIN-NN.md` section(s), with a `Context expansion:` statement.
    - Confirm it does not read `brain-index.json` wholesale by default.
- **Acceptance criteria**:
  - Manual validation proves runtime behavior that static tests cannot observe.
  - Any runtime failure becomes a targeted fix, not a redesign.

## Testing Strategy

- Python:
  - `python3 -m pytest scripts/tests/test_audit_context.py`
  - Add unit tests for benchmark rows, baseline deltas, guardrail classification, route-agent count parsing, and Markdown/JSON output.
- Pester:
  - Use `. tests\Run-Tests.ps1` from VS Code/PowerShell and inspect `tests/last-run.json`.
  - Do not run `Invoke-Pester tests/`, direct `Invoke-Pester` loops, or piped `Invoke-Pester -PassThru` output.
- Static audit:
  - `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both`
  - Optional comparison: `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --baseline .cg-docs/cost/context-audit-baseline.json`
- Manual:
  - Complete the VS Code/Copilot checklist in Step 6 before release.

## Documentation Checklist

- [ ] Update audit documentation or docs to describe benchmark and guardrail output.
- [ ] Keep `docs/model-guide.md` policy unchanged except for references to the new validation workflow if needed.
- [ ] Keep `docs/reference.md` command behavior unchanged except for linking to release validation if needed.
- [ ] Do not copy large benchmark tables into docs; generated `.cg-docs/cost/context-audit.md` is the source of truth.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Guardrails become noisy and block intentional maintenance workflows | Fail ordinary-prompt regressions; warn for maintenance/tooling broad reads unless they violate an explicit no-wholesale rule. |
| Static checks overfit exact prompt prose | Test effective contracts and key phrases, not entire paragraphs. |
| Audit script becomes too broad | Keep benchmark functions small and derived from existing report structures; split only if the script becomes hard to reason about. |
| Baseline comparison creates stale generated artifacts | Make `--baseline` optional and document when to refresh a baseline. |
| Runtime routing differs from static prompt text | Keep manual VS Code/Copilot validation as required release-readiness evidence. |

## Out of Scope

- Another broad prompt-slimming pass.
- Redesigning `/cg-review`.
- Redesigning Knowledge Brain or Team Brain.
- Changing model-governance policy.
- Changing roadmap schema.
- Implementing new runtime agent architecture.
- Making VS Code/Copilot validation fully automated in this phase.

## Acceptance Criteria

- `scripts/cg_audit_context.py` emits benchmark and guardrail sections in both JSON and Markdown.
- The benchmark covers `/cg-plan`, `/cg-work`, `/cg-review`, `/cg-compound`, `/cg-resume`, and Knowledge Brain/context lookup behavior.
- Guardrails fail or warn for the regressions listed in this plan.
- Existing Phase 2-5 behavior is preserved.
- Python audit tests pass.
- Pester prompt/model tests are updated and pass in the VS Code/PowerShell validation harness.
- `.cg-docs/cost/context-audit.md` shows current baseline, optional before/after deltas, top remaining optimization candidates, and release-readiness checklist.
- Maintainer docs describe the pre-merge/release validation workflow.
- Manual VS Code/Copilot validation checklist is completed before release.
