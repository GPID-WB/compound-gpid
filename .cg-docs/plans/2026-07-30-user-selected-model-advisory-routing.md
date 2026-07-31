---
date: 2026-07-30
title: "Implement User-Selected Models with Advisory Stage Routing"
status: completed
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-07-30-user-selected-model-advisory-routing.md"
language: "Python/PowerShell/Markdown"
estimated-effort: "large"
deviation-policy: "ask"
tags: [model-routing, model-picker, reasoning-effort, cross-platform, documentation, token-efficiency]
phases: 4
current-phase: 4
execution-report: ".cg-docs/work-reports/2026-07-31-user-selected-model-advisory-routing.md"
---

# Plan: Implement User-Selected Models with Advisory Stage Routing

## Objective

Replace Compound GPID's model-assignment execution policy with user-selected
model and reasoning configuration on every supported platform. Preserve useful
model guidance through one centralized advisory contract that recommends
capability profiles, effort levels, and clearly qualified model examples at
workflow transitions without selecting or constraining the user's model.

Rewrite the model guidance documentation around plausible choices for each
stage of the process. The guide must emphasize that examples are advisory,
availability may differ by platform and date, and the user makes the final
selection.

## Context

The decided brainstorm replaces the OpenAI-first execution policy established
by `.cg-docs/plans/2026-06-15-model-selection-and-governance-finish.md`. This is
a follow-up plan rather than a revision because the prior plan has recorded
completed phases and remains useful historical evidence.

Today, 18 canonical prompts and all 17 canonical agents declare explicit
models. `.github/shared/model-catalog.json`, `.github/shared/target-mapping.json`,
and `scripts/cg_generate_targets.py` translate those assignments into generated
Claude Code, Codex, and OpenCode assets and standalone model-mapping artifacts.
The Python context audit, target tests, Pester model-assignment tests, install
ownership, and documentation all enforce or describe that policy.

The replacement keeps capability advice separate from execution. A shared
contract and examples schema will define stage profiles, effort guidance,
availability provenance, local overrides, cross-family review behavior, and
fallback order. Canonical handoffs will consume that contract, generated
targets will inherit the user's platform configuration, and documentation will
explain practical stage-by-stage choices.

Relevant prior learning: inherited execution is represented by an absent
`model:` key, not a placeholder value. Static checks must compare semantic
states and must not claim runtime availability or identify the hidden model
behind Copilot Auto. See
`.cg-docs/solutions/testing-patterns/2026-06-15-inherited-model-picker-drift-equivalence.md`.

No new runtime dependency is expected. Existing Python, pytest, Pester, JSON,
and Markdown patterns are sufficient.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Remove model-specific execution assignments from every canonical command and agent. | brainstorm |
| R2 | Remove generated model injection, platform model mappings, and install/validation rules that require specific models or vendors. | brainstorm |
| R3 | Ensure canonical and generated commands/agents inherit the model and reasoning configuration selected by the user wherever the platform supports inheritance. | brainstorm |
| R4 | Define one shared advisory contract for stage profiles, effort labels, alternatives, provenance, fallback behavior, and conditional cross-family review. | brainstorm |
| R5 | Support layered advisory sources in this order: reliable runtime/platform facts, local user configuration, bundled dated examples labeled with verification status, then capability-only guidance. | brainstorm |
| R6 | Add advisory recommendations at `/cg-plan` to implementation, `/cg-work` to review, `/cg-review` to fix triage, and `/cg-fix-triage` to compounding/documentation transitions. | brainstorm |
| R7 | Recommend task capability and reasoning effort, prioritizing effective completion before token economy and offering a strong default plus an economical alternative when useful. | brainstorm |
| R8 | Never switch models, set effort, infer a hidden Auto-selected model, guess an unknown vendor, or constrain the user's selection. | brainstorm/charter |
| R9 | Rewrite model guidance to suggest plausible models and effort by process stage while emphasizing that selection is the user's decision and examples may be unavailable or unverified. | user |
| R10 | Keep `.github/` canonical and regenerate equivalent advisory behavior across Claude Code, Codex, and OpenCode without stale model-mapping artifacts. | project architecture |
| R11 | Replace assignment-policy audit and test assertions with inheritance, advisory-schema, provenance, handoff, and generated-parity guardrails. | project testing standards |
| R12 | Keep live runtime model-catalog introspection deferred until a supported platform exposes a reliable mechanism. | brainstorm |

## Implementation Steps

## Phase 1: Advisory Foundation

### 1. Establish the Migration Inventory and Red-Phase Contracts

- **Requirements**: R1, R2, R3, R8, R11
- **Files**:
  - `tests/model-assignments.Tests.ps1`
  - `tests/prompt-tools.Tests.ps1`
  - `scripts/tests/test_audit_context.py`
  - `scripts/tests/test_cg_generate_targets.py`
  - `scripts/tests/test_target_claude.py`
  - `scripts/tests/test_target_codex.py`
  - `scripts/tests/test_target_opencode.py`
  - `scripts/tests/test_target_mapping.py`
  - `scripts/tests/test_target_packaging.py`
- **Details**: Inventory all explicit `model:` declarations, catalog consumers,
  target mapping outputs, install/link ownership entries, audit fields, docs
  assertions, and generated manifests. Convert the old assignment expectations
  into failing target-state tests: canonical and generated commands/agents must
  not carry execution model metadata; model-mapping artifacts must not be
  produced or packaged; inherited selections must remain unguessed. Keep count
  sentinels only where they still protect asset discovery rather than policy.
- **Test Scenarios**: Happy path with no model assignment; edge case with a
  stale canonical or generated `model:` key; error path with a stale mapping
  output or old vendor-enforcement rule.
- **Tests**: Focused pytest files above; `tests/model-assignments.Tests.ps1` and
  prompt contract assertions through the canonical Pester runner.
- **Acceptance criteria**: Tests precisely identify every old enforcement
  surface and fail against the current assignment-based implementation for the
  intended reasons.

### 2. Define the Shared Advisory Contract, Examples, and Local Overrides

- **Requirements**: R4, R5, R7, R8, R12
- **Files**:
  - `.github/shared/model-advisory.contract.md` (new)
  - `.github/shared/model-advisory-examples.json` (new)
  - `.github/shared/model-catalog.json` (remove or replace)
  - `.github/prompts/cg-setup.prompt.md`
  - `.github/skills/cg-skill-setup/SKILL.md`
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
- **Details**: Define stable stage identifiers and capability profiles for
  planning, implementation, review, fix triage, and compounding/documentation.
  Specify supported effort labels (`low`, `medium`, `high`, `xhigh`, `max`) as
  advisory platform-dependent values. Require each recommendation to contain a
  task rationale, strong option, optional economical option, and explicit user
  control statement. Define the source fallback order and a small local config
  shape for user-maintained model examples/preferences; absence or malformed
  optional configuration must fall back loudly to the next safe source rather
  than alter execution. Replace the execution-oriented catalog with a smaller
  examples schema containing model name, vendor/family, capability tags,
  platform, observed date, and availability verification status. Runtime
  introspection remains a reserved first layer with no unsupported adapter.
- **Test Scenarios**: Happy path with valid local examples; edge case with no
  local/runtime data and dated bundled examples; edge case with unknown current
  vendor producing conditional review advice; error path with malformed local
  or bundled advisory data; fallback to capability-only advice.
- **Tests**: JSON/schema and audit tests in
  `scripts/tests/test_audit_context.py`; setup prompt contract tests.
- **Acceptance criteria**: One canonical contract describes all routing
  semantics, valid examples pass, invalid provenance/configuration is reported,
  and no advisory field can act as executable model metadata.

## Phase 2: Decouple Execution Policy

### 3. Remove Canonical and Generated Model Assignment Machinery

- **Requirements**: R1, R2, R3, R10
- **Files**:
  - `.github/prompts/*.prompt.md`
  - `.github/agents/*.agent.md`
  - `.github/shared/target-mapping.json`
  - `scripts/schemas/target_mapping_schema.json`
  - `scripts/cg_generate_targets.py`
  - `scripts/link.ps1`, `scripts/link.sh`
  - `scripts/unlink.ps1`, `scripts/unlink.sh`
  - platform target tests under `scripts/tests/`
- **Details**: Remove every canonical `model:` key. Delete role lookup and
  platform model resolution from generation, remove `modelMappingMode`,
  `modelMapping`, and model-mapping output paths from the target contract, and
  stop emitting/owning/installing standalone mapping files. Ensure command and
  agent emitters preserve platform-native inheritance instead of inserting a
  placeholder such as `Auto` or `inherited`. Keep advisory shared resources in
  normal shared-asset generation and packaging.
- **Test Scenarios**: Happy path for each target with no emitted model field;
  edge case for Codex TOML subagents where the model line must be absent rather
  than commented; error path for stale target mapping fields or owned mapping
  artifacts.
- **Tests**: `scripts/tests/test_cg_generate_targets.py`, target mapping,
  ownership, packaging, closure, determinism, and per-platform tests.
- **Acceptance criteria**: Canonical and freshly generated executable assets
  contain no Compound GPID-selected model, and generation/install manifests no
  longer include model-mapping artifacts.

### 4. Replace Assignment Audits with Advisory and Inheritance Guardrails

- **Requirements**: R3, R5, R8, R11
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
  - `tests/model-assignments.Tests.ps1` (rename if useful)
  - `.cg-docs/cost/context-audit.json`
  - `.cg-docs/cost/context-audit.md`
  - `.cg-docs/cost/token-advice.md`
- **Details**: Remove unknown-model, preferred-vendor, tier restriction,
  assignment completeness, and assignment-table drift checks. Add guardrails
  for forbidden executable model metadata, advisory schema validity, missing or
  stale provenance, unsupported availability claims, stage coverage, required
  user-choice language, and conditional cross-family handling. Distinguish
  static consistency evidence from runtime availability. Update generated audit
  output and warning classification so old assignment warnings disappear
  without masking real stale metadata.
- **Test Scenarios**: Happy path with complete advisory data; edge case with an
  unavailable/unverified example that is correctly labeled; error paths for a
  stale `model:` declaration, missing observed date, executable-looking advice,
  or an assertion about the hidden Auto model.
- **Tests**: `scripts/tests/test_audit_context.py`; focused Pester governance
  tests; regenerated context audit artifacts.
- **Acceptance criteria**: Audit failures reflect the new advisory policy,
  detect old execution metadata, and report no assignment-policy false
  positives on the migrated repository.

## Phase 3: Workflow Advice and Documentation

### 5. Add Centralized Advisory Guidance to the Four Handoffs

- **Requirements**: R4, R5, R6, R7, R8
- **Files**:
  - `.github/prompts/cg-plan.prompt.md`
  - `.github/prompts/cg-work.prompt.md`
  - `.github/prompts/cg-review.prompt.md`
  - `.github/prompts/cg-fix-triage.prompt.md`
  - `.github/shared/model-advisory.contract.md`
  - `tests/prompt-tools.Tests.ps1` or a focused advisory Pester test file
- **Details**: Make each handoff read the shared contract and emit a compact
  recommendation for the next stage. Planning-to-implementation should favor
  code execution and repository tool use; work-to-review should favor
  independent critical reasoning and conditionally suggest a different family;
  review-to-fix should scale coding/reasoning effort to finding severity; and
  fix-triage-to-compounding/documentation should favor faithful synthesis with
  an economical option for straightforward documentation. Preserve existing
  handoff choices and review-mode routing. Recommendations inform the next user
  selection only and never dispatch, retry, set effort, or mutate config.
- **Test Scenarios**: Happy path with a strong and economical recommendation;
  edge cases for known same-family review, unknown vendor, Copilot Auto, and a
  platform lacking a named effort level; error path where handoff text implies
  automatic switching or omits user control.
- **Tests**: Behavioral Pester assertions for all four canonical handoffs and
  independent assertions for each required contract phrase.
- **Acceptance criteria**: All four handoffs use the centralized contract,
  provide stage-appropriate capability/effort advice, and clearly leave the
  decision to the user.

### 6. Rewrite Model Guidance Around User Choice and Process Stages

- **Requirements**: R5, R7, R8, R9, R12
- **Files**:
  - `docs/model-guide.md`
  - `docs/workflow.md`
  - `docs/reference.md`
  - `docs/context-files.md`
  - release/validation documentation that references model assignments
  - `tests/model-assignments.Tests.ps1` or replacement documentation tests
- **Details**: Replace the explicit assignment matrix and OpenAI-first
  governance language with a process-stage guide. Cover discovery/strategy,
  planning, implementation, review, fix triage, and
  compounding/documentation. For each stage, document the capability profile,
  plausible reasoning effort, a strong example and economical alternative when
  useful, and platform/date/availability labels. State prominently that these
  are suggestions, the available picker/config is authoritative, and the user
  decides. Explain Auto/unknown behavior, conditional cross-family review,
  local override precedence, capability-only fallback, and why live discovery
  is deferred. Update target architecture docs to remove model-mapping outputs
  and keep reference/workflow links consistent.
- **Test Scenarios**: Happy path with every process stage represented; edge case
  for an unverified example and unsupported effort label; error paths for stale
  assignment tables, vendor mandates, unlabeled availability claims, or wording
  that implies Compound GPID chooses the model.
- **Tests**: Documentation structure and semantic assertions in the focused
  Pester model/advisory tests; docs site/link validation if applicable.
- **Acceptance criteria**: A user can choose a plausible model and effort for
  each process stage while understanding that the choice and availability are
  theirs, and no current documentation describes enforced assignments.

## Phase 4: Generated Parity and Release Evidence

### 7. Regenerate and Verify All Platform Targets

- **Requirements**: R3, R4, R10, R11
- **Files**:
  - `.claude/**`
  - `.agents/**`
  - `.opencode/**`
  - generated manifests under each target tree
  - `scripts/tests/test_target_drift.py`
  - `scripts/tests/test_target_documentation.py`
  - `scripts/tests/test_release_gate_targets.py`
- **Details**: Regenerate all non-Copilot targets from `.github/`. Confirm that
  commands, agents/subagents, shared advisory resources, manifests, and install
  documentation match the new ownership model. Remove generated
  `model-mapping.*.json` and generated copies of the old execution catalog.
  Verify each target's native syntax remains valid and no adapter reintroduces
  model metadata.
- **Test Scenarios**: Happy path deterministic generation for all targets; edge
  case for target-specific frontmatter/TOML formatting; error path for stale
  generated mapping files, manifest ownership, or source/target drift.
- **Tests**: `python3 scripts/cg_generate_targets.py --all`; target drift,
  determinism, documentation, packaging, and release-gate pytest tests.
- **Acceptance criteria**: All generated trees are deterministic and in sync,
  advisory resources are available on each platform, and no mapping artifact
  or executable model assignment remains.

### 8. Run Final Policy, Documentation, and Safety Verification

- **Requirements**: R1, R2, R3, R6, R8, R9, R10, R11
- **Files**:
  - affected files under `scripts/tests/`
  - affected files under `tests/`
  - `.cg-docs/cost/context-audit.json`
  - `.cg-docs/cost/context-audit.md`
  - `tests/last-run.json`
- **Details**: Run focused Python tests first, then the affected target/audit
  pytest suite, regenerate context-audit outputs, and run the unfiltered Pester
  suite through the canonical safe runner. Perform final static scans for
  canonical/generated `model:` metadata, model-mapping artifacts, stale
  OpenAI-first/vendor-mandate language, and duplicated handoff policy. Record
  runtime model inheritance/availability as unverified unless separately
  observed on the actual platform; static checks must not overclaim it.
- **Test Scenarios**: Happy path with all required evidence passing; edge case
  where only runtime behavior remains unobserved and is labeled as such; error
  path for any stale assignment, documentation drift, target drift, or unsafe
  Pester invocation.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_mapping.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py scripts/tests/test_target_packaging.py scripts/tests/test_target_drift.py scripts/tests/test_audit_context.py`
  - `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations`
  - Execution subagent runs `. tests\Run-Tests.ps1`, then reads bounded fields
    from `tests/last-run.json`.
- **Acceptance criteria**: All required automated evidence passes, generated
  artifacts are current, audit output has no policy failures or unreviewed
  `fix` warnings, and any remaining runtime uncertainty is explicit.

## Testing Strategy

- Use pytest fixture repositories to prove model metadata is omitted rather
  than replaced with `Auto`, `inherited`, or a target default.
- Test each generated platform independently because Claude Markdown, Codex
  TOML, and OpenCode frontmatter have different omission paths.
- Validate advisory examples structurally and semantically: required
  provenance, observation date, verification status, known effort vocabulary,
  and no executable routing fields.
- Add behavioral Pester coverage for each of the four handoffs, each process
  stage in documentation, and explicit user-control language. Avoid regex
  alternations that let one phrase mask another missing contract element.
- Test known-vendor, unknown-vendor, Auto, no-local-config, malformed-local-
  config, stale-example, and capability-only fallback cases.
- Use the canonical Pester runner through an execution subagent and inspect
  `tests/last-run.json`; never invoke a directory run or parse raw Pester output.
- Keep runtime inheritance and picker availability as manual/observational
  evidence separate from static test results.

## Documentation Checklist

- [ ] `docs/model-guide.md` is organized by process stage, not assignment table.
- [ ] Every stage lists capability needs and plausible reasoning effort.
- [ ] Concrete model examples include platform, observed date, and verification
      status, or are explicitly labeled availability-unverified.
- [ ] Strong and economical choices prioritize successful completion before
      token savings.
- [ ] User choice is explicit in default behavior, stage guidance, examples,
      local configuration, and handoff explanations.
- [ ] Copilot Auto and unknown-vendor behavior never infer hidden identity.
- [ ] Conditional cross-family review guidance explains what to do when the
      generator family is known and when it is unknown.
- [ ] `docs/workflow.md`, `docs/reference.md`, and `docs/context-files.md` no
      longer describe generated model mappings or enforced assignments.
- [ ] Validation and release guidance distinguishes static evidence from
      runtime observation.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Removing frontmatter exposes platform defaults that do not actually inherit the active user selection. | Commands or agents may run under an unexpected model. | Verify documented platform semantics where reliable, omit placeholders, keep runtime behavior explicitly unverified until observed, and stop if a supported target fundamentally cannot inherit. |
| Concrete examples become stale or unavailable. | Users receive misleading guidance. | Make capability profiles primary; require platform, observation date, verification status, and capability-only fallback. |
| Advisory wording is interpreted as automatic routing. | User autonomy is weakened despite metadata removal. | Prohibit executable routing fields and imperative switching language; test explicit user-control statements at every handoff. |
| Removing mapping outputs breaks link/unlink/update ownership. | Installations retain stale files or fail cleanup. | Update target schema, generator manifests, shell/PowerShell ownership tables, packaging tests, and stale-file deletion behavior in one phase. |
| Generated targets drift because canonical and target-specific edits are mixed. | Platforms behave inconsistently. | Edit only `.github/` and generator sources, regenerate all targets once, then run deterministic drift tests. |
| Old audit metrics disappear without replacement. | Regressions in provenance or vendor guessing become invisible. | Replace each removed assignment check with an explicit inheritance/advisory guardrail and fixture before deleting old logic. |
| Four handoffs duplicate recommendation prose. | Stage behavior drifts over time. | Keep recommendation fields and fallback semantics in one shared contract; handoffs reference stage identifiers and add only local transition context. |
| Pester verification floods or crashes the editor. | Required evidence cannot be collected safely. | Use the canonical `Run-Tests.ps1` execution-subagent pattern and bounded `last-run.json` output. |

## Out of Scope

- Live runtime model-catalog introspection or network-based availability checks.
- Automatic model switching, reasoning-effort changes, retries, or dispatch to a
  different model.
- An external continuously updated model registry or vendor benchmark service.
- Guarantees that bundled model examples exist in a user's current account or
  platform picker.
- Reworking review-mode routing, agent composition, or unrelated workflow
  handoff choices.
- Revising completed phases or unrelated open work in the June model-governance
  plan.
- Updating `compound-gpid.md`; this implementation aligns with the current
  token-efficiency focus and does not change the project objective.

## Completion Contract

### Outcome

All Compound GPID commands and agents inherit the model and reasoning
configuration selected by the user across supported targets. The four workflow
handoffs provide centralized, advisory-only capability and effort guidance,
while `docs/model-guide.md` explains plausible models for each process stage,
labels availability/provenance, and emphasizes that selection remains entirely
the user's decision.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Canonical prompts and agents contain no execution model assignments, and target mapping/generation no longer injects models or emits model-mapping artifacts. | Repository scan; `.github/shared/target-mapping.json`; `scripts/cg_generate_targets.py` | yes |
| V2 | 1 | One centralized advisory contract/schema validates capability profiles, effort labels, options, provenance, local overrides, and capability-only fallback. | Shared advisory artifacts; targeted generator/audit pytest tests | yes |
| V3 | 2 | `/cg-plan`, `/cg-work`, `/cg-review`, and `/cg-fix-triage` emit stage-appropriate advisory guidance without switching or constraining models. | Canonical prompt contract tests in `tests/prompt-tools.Tests.ps1` or a focused model-advisory Pester file | yes |
| V4 | 3 | Documentation gives plausible model and effort suggestions by process stage, labels examples as best-effort/unverified where applicable, and repeatedly states that the user decides. | `docs/model-guide.md`, `docs/workflow.md`, `docs/reference.md`, `docs/context-files.md`; documentation assertions | yes |
| V5 | 4 | Claude Code, Codex, and OpenCode trees are regenerated from canonical sources, preserve inheritance, include shared advisory resources, and contain no stale mapping artifacts. | `python3 scripts/cg_generate_targets.py --all`; target drift/parity pytest tests | yes |
| V6 | final | Generator, target, audit, and advisory Python regressions pass. | `python3 -m pytest` on affected files under `scripts/tests/` | yes |
| V7 | final | Pester prompt/documentation/model-governance regressions pass through the safe runner. | Execution subagent runs `. tests\Run-Tests.ps1`; inspect `tests/last-run.json` | yes |
| V8 | final | Context audit reports no stale assignment-policy failures and validates advisory consistency without claiming runtime availability. | `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Recommendations must never set, switch, or restrict the user's model or reasoning effort. | Static prompt/agent/generated-target scans and tests |
| C2 | 1 | Exact model examples remain secondary to capability profiles and carry platform, observation date, and verification status. | Advisory schema validation |
| C3 | 2 | Unknown current model/vendor produces conditional cross-family guidance, never a guessed identity. | Handoff fixtures for known, unknown, and Auto selections |
| C4 | 3 | Model guidance covers planning, implementation, review, fix triage, and compounding/documentation stages, with effective completion prioritized before token economy. | Documentation matrix assertions |
| C5 | 4 | `.github/` remains canonical; `.claude/`, `.agents/`, and `.opencode/` are regenerated rather than hand-maintained. | Generator manifests and target drift tests |
| C6 | final | Pester execution follows the project's canonical safe-runner contract. | `tests/last-run.json` records an unfiltered passing run |

### Boundaries

- Allowed: canonical prompts/agents, shared advisory contract and examples,
  local configuration template/schema, target generator/mapping/install
  ownership, audit tooling, generated target trees, tests, and model-guidance
  documentation.
- Allowed: removal or replacement of the current execution-oriented model
  catalog and generated mapping artifacts.
- Out of scope: live runtime model discovery, automatic model switching,
  external registries/network calls, vendor ranking guarantees, and changes to
  platform model-picker implementations.
- Out of scope: revising unrelated unfinished phases in the June
  model-governance plan.

### Iteration Policy

1. Establish failing tests for inherited execution and advisory schema behavior
   before removing old policy.
2. Implement canonical shared policy and generator changes before editing
   generated targets.
3. Add the four handoffs through the shared contract, not duplicated free-form
   recommendation logic.
4. Rewrite documentation and its tests together so stage guidance and
   user-control language cannot drift.
5. Regenerate all targets, run focused tests, then run final Python, Pester, and
   context-audit gates.
6. Under `deviation-policy: ask`, pause before changing scope, adding
   dependencies, or retaining any execution model assignment.

### Blocked-Stop Conditions

- A supported target cannot inherit user-selected model/reasoning settings
  without a platform-enforced assignment.
- Advisory examples cannot be represented without being interpreted as
  executable routing.
- Removing mapping artifacts would break install/update ownership without an
  agreed replacement.
- Required Python, Pester, generator-parity, or context-audit evidence remains
  failing after bounded fixes.
- Verification requires unsafe Pester invocation or unsupported runtime claims.
- Continuing would require implementing deferred runtime introspection or
  crossing protected artifact boundaries.
