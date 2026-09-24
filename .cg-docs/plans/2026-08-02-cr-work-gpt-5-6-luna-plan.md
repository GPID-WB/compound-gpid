---
date: 2026-08-02
title: "Use GPT-5.6 Luna for /cr-work"
status: completed
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-08-02-cr-work-gpt-5-6-luna.md"
language: "PowerShell/Python/Markdown"
estimated-effort: "medium"
deviation-policy: "ask"
tags: [compound-research, cr-work, model-governance, native-targets, generator, testing]
phases: 2
completed-phases: [1, 2]
completed-date: 2026-08-03
execution-report: ".cg-docs/work-reports/2026-08-03-cr-work-gpt-5-6-luna-plan.md"
---

# Plan: Use GPT-5.6 Luna for /cr-work

## Objective

Assign `GPT-5.6 Luna` to the Compound Research `/cr-work` command and carry that
assignment through the canonical model catalog, audit tooling, native target
projections, documentation, and focused tests without changing any other agent
or model assignment.

## Context

The canonical `.github/prompts/cr-work.prompt.md` currently selects
`GPT-5.3-Codex`, which is optimized for coding workflows. `/cr-work` is the
research execution workflow used by World Bank researchers, economists, and
developers implementing research plans, and the requested model is intended to
be more research-oriented and token-efficient.

The command currently has no entry in `.github/shared/model-catalog.json`, so
Codex and Claude-native generated command projections do not carry a model.
The existing generator already resolves arbitrary catalog roles through
`.github/shared/target-mapping.json`; however, the audit tool's accepted role
set must be extended for the new command-specific role.

The selected approach is recorded in
`.cg-docs/brainstorms/2026-08-02-cr-work-gpt-5-6-luna.md`. Static Copilot
frontmatter cannot implement a runtime warning-then-fallback engine. The
implementation must therefore keep model support status truthful, emit an
audit/generation warning when Luna is unavailable or unvalidated, and use the
existing Sonnet mapping for Claude-native output.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | The canonical `/cr-work` prompt declares the exact model string `GPT-5.6 Luna`. | User request; brainstorm |
| R2 | The model catalog contains Luna metadata and one explicit `research-execution` assignment for `/cr-work`. | Brainstorm; model-governance convention |
| R3 | The audit tool recognizes `research-execution` as a valid role without weakening existing role checks. | Implementation discovery |
| R4 | Codex maps `research-execution` to Luna, Claude Code maps it to the existing Sonnet tier, and OpenCode remains inherited. | Brainstorm |
| R5 | Native projections and generated model catalogs/mapping manifests are regenerated from canonical sources. | Brainstorm; native packaging convention |
| R6 | `docs/model-guide.md` and `docs/reference.md` accurately describe the new assignment and its support/fallback status. | Existing documentation tests |
| R7 | Focused tests cover the canonical assignment, catalog role, audit role, target mappings, generated commands, and non-regression of other assignments. | Brainstorm; testing requirements |
| R8 | The exact Luna label is validated in Copilot where practical; unavailable or untested support is reported explicitly rather than silently substituted. | Brainstorm; model-governance convention |
| R9 | No other prompt, agent, global default, `/cr-review` behavior, or runtime fallback architecture changes. | User request; brainstorm |

## Implementation Steps

## Phase 1: Canonical Policy, Projections, And Guardrails

### 1. Register the command-specific model policy

- **Requirements**: R1, R2, R3, R8, R9
- **Files**: `.github/prompts/cr-work.prompt.md`, `.github/shared/model-catalog.json`, `scripts/cg_audit_context.py`
- **Details**:
  - Replace only the canonical `/cr-work` `model:` value with `GPT-5.6 Luna`.
  - Add Luna to the catalog's model and frontmatter-support records with its exact vendor/family/role metadata. Keep the support status `not-tested` until the Copilot check passes; if it passes, record `frontmatter-supported` with dated provenance.
  - Add exactly one catalog assignment for `.github/prompts/cr-work.prompt.md` with role `research-execution`, preferred model Luna, explicit frontmatter mode, and a rationale tied to research execution and token efficiency.
  - Add `research-execution` to `MODEL_ROLES` in `scripts/cg_audit_context.py`. Do not change the existing OpenAI-first, Sonnet, Haiku, inherited, or fallback checks.
  - Ensure the audit emits a visible support warning for an untested/unavailable Luna declaration rather than treating another model as the canonical assignment.
- **Test Scenarios**: exact model string is parsed; exactly one catalog assignment exists; the new role is accepted; an untested support status remains visible; existing role-policy checks remain unchanged.
- **Tests**: `scripts/tests/test_audit_context.py`; `tests/model-assignments.Tests.ps1`
- **Acceptance criteria**: The canonical prompt, catalog, and audit tool agree on one explicit `/cr-work` assignment, and the audit reports no invalid catalog role.

### 2. Add target-specific mappings and regenerate native projections

- **Requirements**: R4, R5, R9
- **Files**: `.github/shared/target-mapping.json`; generated `.agents/`, `.claude/`, and `.opencode/` command, shared-catalog, mapping, and manifest files
- **Details**:
  - Add only `research-execution: GPT-5.6 Luna` to the Codex target mapping.
  - Add only `research-execution: sonnet` to the Claude Code target mapping.
  - Leave OpenCode's role-only mapping unchanged so its `/cr-work` command remains model-inherited.
  - Run a dry-run before generation: `python3 scripts/cg_generate_targets.py --root . --all --dry-run`.
  - Regenerate all non-Copilot targets with `python3 scripts/cg_generate_targets.py --root . --all`; do not hand-edit generated files.
  - Verify the expected projections: `.agents/commands/cr-work.md` contains Luna, `.claude/commands/cr-work.md` contains the native Sonnet model value, and `.opencode/commands/cr-work.md` has no forced model.
- **Test Scenarios**: Codex exact mapping; Claude tier mapping; OpenCode inherited behavior; generated outputs are deterministic; unrelated generated commands retain their existing models.
- **Tests**: `scripts/tests/test_cg_generate_targets.py`; `scripts/tests/test_target_mapping.py`; `scripts/tests/test_target_codex.py`; `scripts/tests/test_target_claude.py`; `scripts/tests/test_target_opencode.py`
- **Acceptance criteria**: The generated projections reflect the new role only for `/cr-work`, and the generator diff contains no unrelated model changes.

### 3. Synchronize human-facing model documentation

- **Requirements**: R2, R6, R8, R9
- **Files**: `docs/model-guide.md`, `docs/reference.md`
- **Details**:
  - Add Luna to the model support table with the truthful validation status and provenance date.
  - Add `cr-work.prompt.md` to the explicit prompt assignment table with role `research-execution` and the rationale from the catalog; the table key is the prompt filename, while `/cr-work` wording belongs in `docs/reference.md`.
  - Update the model-guide rollout/validation wording so it does not claim Luna is Copilot-supported until the exact label is checked.
  - Change the CR command reference row from `GPT-5.3-Codex` to `GPT-5.6 Luna` and document the native-target fallback boundary without claiming runtime fallback behavior.
  - Leave all other prompt and agent rows unchanged.
- **Test Scenarios**: docs parse correctly; the canonical model and catalog model agree; the reference table reports Luna; inherited prompts remain documented as model-picker inheritance.
- **Tests**: `tests/model-assignments.Tests.ps1`; `scripts/tests/test_audit_context.py`
- **Acceptance criteria**: Documentation, catalog, and executable frontmatter have no model-guide/reference drift, and fallback language is explicit and platform-accurate.

### 4. Add focused regression guardrails

- **Requirements**: R2, R3, R4, R5, R7, R9
- **Files**: `scripts/tests/test_audit_context.py`, `scripts/tests/test_cg_generate_targets.py`, `scripts/tests/test_target_mapping.py`, `scripts/tests/test_target_codex.py`, `scripts/tests/test_target_claude.py`, `scripts/tests/test_target_opencode.py`, `tests/model-assignments.Tests.ps1`
- **Details**:
  - Extend generator fixtures with the command-specific role and assert that target resolution returns the expected platform values.
  - Add audit coverage proving `research-execution` is valid and does not alter the existing role-policy rules.
  - Assert the generated Codex and Claude command models, and assert that OpenCode remains inherited.
  - Assert the `/cr-work` catalog row, exact frontmatter, model-guide row, and reference row are synchronized.
  - Add a non-regression assertion or scoped inventory comparison showing that no other assignment changed.
- **Test Scenarios**: happy path for Luna; unavailable/untested support warning; malformed or missing assignment; unrelated assignment preservation; generated target drift.
- **Tests**: Focused Python pytest files listed above and the single-file model-assignment Pester test through the project's safe runner conventions.
- **Acceptance criteria**: Focused tests fail if Luna is absent, the role is invalid, native mappings drift, OpenCode becomes pinned, or another assignment changes.
- **Phase 1 exit criterion**: The focused tests and generator dry-run pass before Phase 2 begins, proving the changed catalog role, native projections, documentation references, and no-other-assignment boundary.

## Phase 2: Final Verification

### 5. Execute verification and finalize evidence

- **Requirements**: R1-R9
- **Files**: Generated validation artifacts only; no additional source files unless a failed check requires a scoped repair
- **Details**:
  - Run targeted Python tests for audit, generator, target mapping, Codex, and Claude/OpenCode projections.
  - Run the canonical safe Pester runner `pwsh -ExecutionPolicy Bypass -File tests/Run-Tests.ps1` once after all fixes; use `tests/last-run.json` as the result artifact.
  - Run the documented repository-wide model audit before and after the change, retaining the pre-change model-inventory baseline. Confirm that `.github/prompts/cr-work.prompt.md` is no longer listed in `missing_catalog_assignments`, no new unknown model, invalid role, model-guide drift, or unsupported preferred-model finding appears, and the only remaining missing assignments are the four pre-existing CR prompts outside this plan's scope. A `not-tested` Luna status may remain only with an explicit support warning and native fallback evidence.
  - Perform the practical GitHub Copilot check for the exact `GPT-5.6 Luna` label. Update catalog/docs provenance only to match what the check establishes.
  - Run `git diff --check` and inspect the final changed-path list to confirm the no-other-models boundary.
- **Test Scenarios**: all targeted tests pass; full safe suite passes; audit output is clean or contains only the explicitly documented Luna support warning; generated output is reproducible; diff scope is limited.
- **Tests**: Targeted `pytest`; canonical `tests/Run-Tests.ps1`; model audit; generator dry-run; final diff-scope inspection.
- **Acceptance criteria**: Required verification evidence is present, `tests/last-run.json` records a passing suite, model support status is truthful, and the final diff contains no unrelated assignment changes.

## Testing Strategy

- Use `pytest` for the Python audit and native-target generator/mapping tests.
- Use the existing single-file Pester conventions for focused model-governance assertions, then run the canonical safe full-suite runner once at the end.
- Use the generator dry-run and committed generated artifacts to test canonical-to-native equivalence.
- Use `cg_audit_context.py` to detect unknown models, invalid roles, missing catalog assignments, model-guide drift, and unsupported preferred models. Because the current repository has pre-existing missing assignments for the other CR prompts, compare the before/after `model_inventory` rather than requiring a repository-wide zero-finding report.
- Treat the Copilot picker/frontmatter check as a manual platform validation; do not infer runtime support from static generated output.
- Confirm fixed output with a final scoped diff and `tests/last-run.json` rather than relying on static inspection alone.

## Documentation Checklist

- [ ] `.github/shared/model-catalog.json` contains the exact model, role, rationale, support status, and provenance.
- [ ] `docs/model-guide.md` lists Luna and `/cr-work` consistently with the catalog.
- [ ] `docs/reference.md` reports the new `/cr-work` model.
- [ ] Documentation distinguishes validation-time warnings and native Sonnet mapping from a runtime fallback engine.
- [ ] Generated native catalogs and mapping artifacts are regenerated from canonical sources.
- [ ] No unrelated agent or prompt documentation rows changed.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `GPT-5.6 Luna` is unavailable or its exact frontmatter label is unsupported | `/cr-work` may not select the requested Copilot model | Validate the exact label; retain `not-tested`/warning status when necessary and preserve the explicit Sonnet-native fallback mapping. |
| New `research-execution` role is rejected by audit tooling | Catalog is correct but the governance audit fails | Add the role to the centralized allowed-role set and a regression fixture without changing existing policy checks. |
| Regeneration changes unrelated native commands | Other agents/models could drift silently | Dry-run first, assert only the new role key is added, run target tests, and inspect changed paths. |
| Catalog, model guide, and reference table diverge | Users receive contradictory model guidance | Update all three from the same assignment rationale and run the model audit plus documentation assertions. |
| Repository-wide audit findings are mistaken for regressions | The implementation is blocked by pre-existing missing catalog assignments for other CR prompts | Capture a pre-change audit baseline, require `/cr-work` to disappear from the missing-assignment list, and fail only on new findings or changes outside the approved slice. |
| Static metadata is mistaken for runtime fallback behavior | Unsupported platform claims become institutional documentation | Document validation-time warning and target-specific fallback only; keep runtime fallback infrastructure out of scope. |

## Out of Scope

- Changing `/cr-review` or any other `/cg-*`/`/cr-*` prompt or agent.
- Changing existing global model defaults or existing target-role mappings.
- Adding a runtime model-selection or fallback engine.
- Interactive validation of every native platform.
- Direct edits to `roadmap.json`; roadmap linkage remains a separate workflow action.
- Changes to `/cr-work` body logic, research gates, phase behavior, or active-state behavior.

## Completion Contract

### Outcome

`/cr-work` uses the exact `GPT-5.6 Luna` model declaration in canonical Copilot metadata, with catalog and audit support. Codex-native output uses Luna, Claude-native output uses the existing Sonnet mapping, OpenCode remains inherited, and no other agent or model assignment changes.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Canonical prompt and catalog contain one matching `cr-work` assignment, and the changed prompt is absent from the baseline missing-assignment findings | `.github/prompts/cr-work.prompt.md`, `.github/shared/model-catalog.json`, before/after model audit inventories | yes |
| V2 | 1 | Target mappings and generated projections are correct | `python3 scripts/cg_generate_targets.py --root . --all --dry-run`; generated native commands | yes |
| V3 | 1 | Human-facing model documentation is synchronized | `docs/model-guide.md`, `docs/reference.md` | yes |
| V4 | 2 | Focused model, audit, generator, and target tests pass | Targeted pytest files and `tests/model-assignments.Tests.ps1` | yes |
| V5 | 2 | Full repository test gate passes | `tests/Run-Tests.ps1`, `tests/last-run.json` | yes |
| V6 | final | Luna is validated or explicitly reported unavailable with a truthful warning and native Sonnet fallback | Copilot picker check plus catalog/audit status | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | No existing agent or model assignment changes | Scoped catalog/target diff and regression assertions |
| C2 | No `/cr-review` or global default changes | Final changed-path and content diff |
| C3 | Generated files come only from canonical sources | Generator dry-run, regeneration, and target tests |
| C4 | No runtime fallback engine or unsupported runtime claim | Documentation and audit review |
| C5 | OpenCode remains model-inherited | Generated OpenCode command assertion |
| C6 | Pre-existing missing assignments for other CR prompts are documented and do not expand | Before/after model-inventory comparison |

### Boundaries

- **Allowed**: `/cr-work`, model catalog, target mappings, audit role registry, related docs, generated projections, and focused tests.
- **Out of scope**: other prompts/agents, `/cr-review`, existing global mappings, runtime fallback infrastructure, and interactive validation of every platform.

### Iteration Policy

1. Run the generator dry-run before writing native outputs.
2. Repair only failures in the affected model-routing slice and rerun the same focused check.
3. If Luna is unavailable, preserve the exact warning/status and native Sonnet mapping; do not silently substitute another canonical Copilot model.
4. Ask before any deviation from these boundaries.

### Blocked-Stop Conditions

- The new role is rejected by the model audit or the model name cannot be represented truthfully.
- The after-audit introduces any new finding outside the approved `/cr-work` slice or changes the pre-existing CR assignment baseline unexpectedly.
- Generation changes unrelated assignments or cannot reproduce expected projections.
- Required tests fail after allowed local repair.
- Safe Pester execution or required evidence cannot be obtained.
- Continuing would require changing a protected or out-of-scope surface.
