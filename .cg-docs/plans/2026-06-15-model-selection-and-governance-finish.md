---
date: 2026-06-15
title: "Finish Token Optimization and OpenAI-First Model Governance"
status: active
scope: "Deep"
brainstorm: null
language: "Python/PowerShell/Markdown"
estimated-effort: "large"
deviation-policy: "ask"
tags: [model-governance, token-optimization, prompt-slimming, cross-vendor-review, openai, copilot]
phases: 6
completed-phases: [1]
current-phase: 2
execution-report: ".cg-docs/work-reports/2026-06-15-model-selection-and-governance-finish.md"
failing-steps:
  - "Phase 2 is blocked on external VS Code/Copilot validation for exact GPT prompt/agent frontmatter strings."
roadmap-features:
  - token-optimization-model-governance/agent-model-tool-governance
  - token-optimization-model-governance/shrink-always-on-context
  - token-optimization-model-governance/prompt-skill-split
---

# Plan: Finish Token Optimization and OpenAI-First Model Governance

## Objective

Finish the `Token Optimization & Model Governance` milestone by replacing the
current token-first model policy with an explicit performance-aware,
OpenAI-first policy for GitHub Copilot workflows. The plugin should prefer
OpenAI models for coding, review, reasoning, documentation, and analysis when
the prompt does not intentionally inherit the user's Copilot chat-box model.
Anthropic Sonnet should be a targeted fallback or escalation model, and Haiku
should be reserved for extremely cheap mechanical work.

## Context

The roadmap milestone now has eight completed features and three active
features:

- `agent-model-tool-governance`
- `shrink-always-on-context`
- `prompt-skill-split`

Prior token-optimization work added the context/model audit, model-picker
policy, staged context-loading contract, routed review, benchmark guardrails,
and release validation artifacts. That work optimized cost and reduced
accidental premium-model usage, but it left the actual model assignment policy
too Anthropic-heavy and too vague for performance-sensitive coding work.

The available GitHub Copilot model list provided by the user includes:

- Auto
- GPT-5.4
- GPT-5.5
- GPT-5.3-Codex
- GPT-5.4 mini
- GPT-5 mini
- Claude Sonnet 4.6
- Claude Haiku 4.5
- Claude Opus 4.6, 4.7, 4.8
- Gemini 2.5 Pro

GitHub's current model comparison describes GPT-5.3-Codex as a strong model for
agentic software development, including feature implementation, tests,
debugging, refactors, and reviews. The plan should therefore promote
GPT-5.3-Codex for coding/agentic workflows where Copilot frontmatter supports
an explicit model, while keeping user-model-picker prompts inherited.

Plan-review revisions applied:

- Validate exact Copilot frontmatter model strings before broad prompt/agent
  rewrites.
- Add a durable model catalog as the policy source of truth, instead of relying
  only on the screenshot or prose docs.
- Specify concrete generator model/vendor metadata fields for `/cg-work`
  reports and review handoffs.
- Limit prompt/context slimming to measurable targets required for #92-#94.
- Track closure evidence separately for issues #92, #93, and #94.
- Build audit/Pester policy guardrails before broad model frontmatter changes.
- Treat `roadmap.json` as read-only for `/cg-work`; dispatch `@cg-roadmap` for
  all roadmap writes.
- Perform actual roadmap/issue closure only after final validation evidence.
- Specify an executable cross-vendor review mechanism, not just policy prose.
- Keep `.github/shared/review-routing.contract.md` canonical for route depth.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Use OpenAI models as the default preference for coding, debugging, review, documentation, reasoning, and analysis prompts/agents unless the workflow intentionally inherits the user's Copilot model picker. | user |
| R2 | Prefer GPT-5.3-Codex for implementation, code repair, refactoring, test generation, and coding-agent workflows where explicit prompt/agent model selection is supported. | user + GitHub model comparison |
| R3 | Use Sonnet only when it is the best targeted choice or fallback for a specific workflow, not as the broad default. | user |
| R4 | Use Haiku only for extremely simple, cheap, mechanical scans or summaries. | user |
| R5 | Preserve model-picker inheritance for ordinary prompts already designed to inherit the chat-box model. | user + existing policy |
| R6 | Implement cross-vendor review: when generator vendor is known, review should prefer a different vendor; if generator vendor is unknown, ask or record unknown instead of pretending. | user |
| R7 | Keep review routing centralized through `.github/shared/review-routing.contract.md`. | prior token-optimization pattern |
| R8 | Update docs and reference tables so model guidance matches actual prompt/agent frontmatter. | project docs |
| R9 | Extend audit tooling to classify model vendor, model family, model role, stale model names, OpenAI-first policy compliance, and cross-vendor review coverage. | active roadmap features |
| R10 | Extend Python and Pester tests for the new model-governance rules. | active roadmap features |
| R11 | Reduce always-on context and split remaining large prompt doctrine only where it improves maintainability without weakening behavior. | roadmap #93/#94 |
| R12 | Do not mark #92, #93, #94 done or mark the milestone complete until validation evidence exists. | roadmap discipline |
| R13 | Do not claim VS Code/Copilot runtime model-picker or agent dispatch behavior passed from static Codex evidence alone. | prior solution |
| R14 | Establish a durable model catalog with allowed model names, vendor, family, role, status, and source/provenance; use it as the audit/docs source of truth. | plan review |
| R15 | Validate exact Copilot frontmatter model strings in VS Code/Copilot before broad prompt/agent rewrites. | plan review |
| R16 | Keep inherited/model-picker prompts valid exceptions to OpenAI-first policy; do not classify them as failures simply because they are unpinned. | plan review |
| R17 | Define concrete `generator-model`, `generator-vendor`, and `generator-source` metadata fields for `/cg-work` execution reports and review handoff text. | plan review |
| R18 | Close #92, #93, and #94 independently using per-issue evidence; do not require all three to close in the same commit. | plan review |
| R19 | Build model-policy audit/Pester guardrails before broad model frontmatter changes. | Oracle plan review |
| R20 | Treat `roadmap.json` as read-only during `/cg-work`; route all roadmap writes through `@cg-roadmap`. | Oracle plan review |
| R21 | Define an executable cross-vendor review mechanism before claiming cross-vendor review support. | Oracle plan review |
| R22 | Define exact docs/model-guide parser schema for prompt/agent model sync. | Oracle plan review |
| R23 | Keep route-depth dispatch canonical in `.github/shared/review-routing.contract.md` and prevent prompt/contract drift. | Oracle plan review |
| R24 | Update touched Pester file comments so they point to the safe runner, not direct `Invoke-Pester`. | Oracle plan review |

## Implementation Steps

## Phase 1: Model Policy and Assignment Matrix

### 1. Create the model catalog and OpenAI-first governance matrix

- **Requirements**: R1, R2, R3, R4, R5, R14, R16
- **Files**:
  - `.github/shared/model-catalog.json`
  - `docs/model-guide.md`
  - `docs/reference.md`
- **Details**:
  - Create `.github/shared/model-catalog.json` as the source of truth for
    model names and policy metadata. Required fields per model:
    - `id`: exact model string intended for prompt/agent frontmatter.
    - `display-name`: user-facing label.
    - `vendor`: `openai`, `anthropic`, `google`, `github-auto`, or `unknown`.
    - `family`: `gpt-5`, `gpt-5-codex`, `claude`, `gemini`, `auto`, or
      `unknown`.
    - `roles`: one or more of `inherited`, `coding`, `review`, `reasoning`,
      `mechanical`, `fallback`.
    - `status`: `allowed`, `fallback`, `retired`, or `unknown`.
    - `source`: `user-screenshot`, `github-docs`, or both.
  - Add a prompt/agent assignment section keyed by path, either in the same JSON
    file or a sibling `.github/shared/model-assignments.json`. Required fields
    per prompt/agent:
    - `path`
    - `role`
    - `preferred-model`
    - `fallback-model`
    - `inherit-picker` (`true`/`false`)
    - `rationale`
  - Every prompt/agent must map to exactly one role. Unknown or missing roles
    fail the audit.
  - Replace the current cost-focused guidance with a performance-aware model
    matrix generated from, or kept in sync with, the model catalog.
  - Use an exact `docs/model-guide.md` schema that the audit parser can read:
    - `### Prompts`
    - table columns: `File | Model | Role | Rationale`
    - `### Agents`
    - table columns: `File | Model | Role | Rationale`
  - Update `parse_model_guide()` tests against this real guide schema before
    relying on drift detection.
  - Add model roles:
    - `inherited`: prompts intentionally using Copilot chat-box/model-picker.
    - `coding`: GPT-5.3-Codex preferred.
    - `reasoning`: GPT-5.4 or GPT-5.5 preferred for deep architecture/planning.
    - `review`: OpenAI review model preferred unless code was generated by
      OpenAI; then choose cross-vendor review.
    - `mechanical`: Haiku only for extremely simple cheap scans/summaries.
    - `fallback`: Sonnet when GPT models are unavailable, lower-quality, or a
      cross-vendor contrast is explicitly useful.
  - Document that "Auto" is acceptable for inherited prompts but should not be
    treated as a named hidden model.
  - State explicitly that inherited/model-picker prompts satisfy the
    OpenAI-first policy because the user controls the model in the chat box.
- **Test Scenarios**:
  - Happy path: guide documents OpenAI-first defaults and inherited prompt
    exceptions.
  - Edge case: OpenAI model unavailable; fallback path is documented.
  - Error path: guide recommends Sonnet as blanket default; tests fail.
- **Tests**:
  - `tests/model-assignments.Tests.ps1`
  - `python3 -m pytest scripts/tests/test_audit_context.py`
- **Acceptance criteria**:
  - Model catalog exists, includes the user-provided Copilot models, and is
    referenced by the audit and documentation.
  - Every prompt/agent has exactly one role assignment in the catalog or
    assignment map.
  - `docs/model-guide.md` exposes `### Prompts` and `### Agents` tables in the
    schema parsed by `scripts/cg_audit_context.py`.
  - Model guide has a prompt/agent role matrix and explicitly states OpenAI is
    preferred except inherited model-picker prompts and justified fallbacks.

### 2. Build guardrails and validate exact model strings before broad frontmatter edits

- **Requirements**: R1, R2, R5, R8, R14, R15, R19, R22, R24
- **Files**:
  - `.github/shared/model-catalog.json`
  - `.github/shared/model-assignments.json` if split from the catalog
  - `.cg-docs/cost/token-optimization-release-checklist.md`
  - `.github/prompts/*.prompt.md`
  - `.github/agents/*.agent.md`
  - `docs/reference.md`
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
  - `tests/model-assignments.Tests.ps1`
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Add failing or newly enforced audit/Pester checks before broad model
    assignment edits:
    - model vendor/family/role classification;
    - complete prompt/agent role coverage;
    - OpenAI-first coding policy;
    - Haiku mechanical-only policy;
    - Sonnet rationale/fallback policy;
    - docs/model-guide parser schema;
    - cross-vendor policy mechanism presence.
  - Before editing many prompt/agent frontmatter blocks, validate a small
    throwaway or test prompt in VS Code/Copilot with the exact intended model
    strings:
    - `GPT-5.3-Codex`
    - `GPT-5.4`
    - `GPT-5.5`
    - `GPT-5 mini`
    - `GPT-5.4 mini`
    - `Claude Haiku 4.5`
    - `Claude Sonnet 4.6`
    - `Gemini 2.5 Pro`
  - Record the result in the release checklist as one of:
    - `frontmatter-supported`
    - `picker-only`
    - `unsupported`
    - `not-tested`
  - If a model is `picker-only` or `unsupported`, do not write that exact model
    into production prompt/agent frontmatter. Use inherited picker behavior or a
    supported fallback with explicit rationale.
  - Generate a current assignment table from prompt/agent frontmatter.
  - Identify files that are:
    - intentionally inherited;
    - currently Sonnet but should become GPT-5.3-Codex or another OpenAI
      model;
    - currently Haiku and valid as mechanical;
    - missing explicit model metadata but not intentionally inherited.
  - Use the user's available model list as the initial allowlist.
  - Update touched Pester file headers/comments to reference `. tests\Run-Tests.ps1`
    rather than direct ad hoc `Invoke-Pester` commands.
- **Test Scenarios**:
  - Happy path: every prompt/agent is classified.
  - Edge case: unknown model name appears; audit warns or fails by policy.
  - Error path: prompt is missing model metadata but is not inherited.
- **Tests**:
  - `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both`
- **Acceptance criteria**:
  - Audit/Pester policy checks exist before broad model assignment changes.
  - Exact model string support has been recorded before broad prompt/agent
    edits begin.
  - Audit output shows a complete model inventory with no unclassified prompt or
    agent.

## Phase 2: Prompt and Agent Model Updates

### 3. Update coding, fixing, and implementation workflows to prefer OpenAI

- **Requirements**: R1, R2, R3, R5
- **Files**:
  - `.github/prompts/cg-work.prompt.md`
  - `.github/prompts/cg-fixbug.prompt.md`
  - `.github/prompts/cg-fix-problems.prompt.md`
  - `.github/prompts/cg-fix-triage.prompt.md`
  - `.github/prompts/cg-commit-push-pr.prompt.md`
  - `.github/prompts/cg-verify-pr.prompt.md`
  - `.github/agents/cg-fix-problems.agent.md`
  - relevant docs/tests
- **Details**:
  - Apply changes only after Step 2 guardrails exist and exact model string
    validation is recorded.
  - Prefer GPT-5.3-Codex for implementation, bug fixing, diagnostics fixing,
    review-finding application, CI repair, and commit/PR generation if Copilot
    accepts that model string in prompt/agent frontmatter according to Phase 1
    validation.
  - If Copilot frontmatter does not accept `GPT-5.3-Codex`, document the
    runtime model-picker fallback and keep the prompt inherited where safer.
  - Do not leave these workflows on Sonnet by default unless a specific tested
    reason remains.
- **Test Scenarios**:
  - Happy path: coding prompts use GPT-5.3-Codex or explicit OpenAI coding
    guidance.
  - Edge case: prompt must inherit model picker; docs explain why.
  - Error path: Sonnet remains default without rationale; audit fails.
- **Tests**:
  - `tests/model-assignments.Tests.ps1`
  - `scripts/tests/test_audit_context.py`
- **Acceptance criteria**:
  - Coding/fixing surfaces are OpenAI-first and documented.

### 4. Update review agents and prompt routing for executable cross-vendor review

- **Requirements**: R1, R3, R6, R7, R17, R21, R23
- **Files**:
  - `.github/prompts/cg-review.prompt.md`
  - `.github/prompts/cg-work.prompt.md`
  - `.github/shared/review-routing.contract.md`
  - `.github/shared/goal-execution.contract.md`
  - `.github/agents/*.agent.md`
  - `docs/reference.md`
  - `docs/workflow.md`
- **Details**:
  - Add generator model/vendor capture:
    - Add explicit execution-report metadata fields:
      - `generator-model: <model name | unknown>`
      - `generator-vendor: <openai | anthropic | google | github-auto | unknown>`
      - `generator-source: <frontmatter | model-picker | user-supplied | inferred-unavailable | unknown>`
    - If `/cg-work` knows the execution model from frontmatter, record it.
    - If the workflow inherits the model picker, ask the user to provide the
      actual model/vendor when review routing depends on it; otherwise record
      `generator-model: unknown`, `generator-vendor: unknown`, and
      `generator-source: model-picker`.
    - Include the same generator metadata in the review handoff block so
      `/cg-review` can route without re-asking when information is already
      durable.
  - Add cross-vendor review rule:
    - Anthropic-generated code -> OpenAI review preferred.
    - OpenAI-generated code -> Anthropic or Gemini review preferred for
      adversarial contrast when available.
    - Unknown generator -> OpenAI default review, with explicit uncertainty.
  - Implement one executable mechanism, chosen after checking Copilot support:
    - Preferred: make `/cg-review` inherit the chat-box model and emit a
      required model-picker instruction for the chosen vendor before review.
    - Acceptable fallback: keep static frontmatter but emit a manual
      cross-vendor rerun command/handoff that explicitly tells the user which
      model to select and records that runtime validation is manual.
    - Do not claim automated cross-vendor review if the implementation only
      documents a preference and cannot affect runtime model selection.
  - Keep route depth (`light`, `standard`, `data-risk`, `architecture`, `full`)
    independent from vendor choice.
  - Keep `.github/shared/review-routing.contract.md` the only canonical
    mode-to-agent route-depth table. Reduce duplicated route tables in prompts
    or add a test that detects prompt/contract drift.
  - Canonical routing rule: `.github/shared/review-routing.contract.md` is the
    only canonical mode-to-agent route-depth table; prompt copies are summaries
    and must be tested against the contract.
- **Test Scenarios**:
  - Happy path: Anthropic generator routes review to OpenAI.
  - Edge case: OpenAI generator routes adversarial/full review to a
    non-OpenAI reviewer where supported.
  - Error path: prompt claims cross-vendor review but never records generator
    vendor.
- **Tests**:
  - `tests/prompt-tools.Tests.ps1`
  - `scripts/tests/test_audit_context.py`
- **Acceptance criteria**:
  - Review routing contract explicitly separates review depth from model/vendor
    selection.
  - Execution reports and review handoffs have a concrete, testable generator
    metadata schema.
  - Cross-vendor review has an executable runtime mechanism or an explicitly
    manual handoff; audit/Pester fails if policy text exists without one.
  - Route-depth dispatch remains canonical in the shared routing contract.

### 5. Update non-coding prompt and agent assignments

- **Requirements**: R1, R3, R4, R5, R8
- **Files**:
  - `.github/prompts/*.prompt.md`
  - `.github/agents/*.agent.md`
  - `docs/reference.md`
- **Details**:
  - Keep model-picker prompts inherited where the user controls quality/cost:
    `/cg-brainstorm`, `/cg-ideate`, `/cg-plan`, `/cg-plan-review`,
    `/cg-review-repos`, `/cg-strategy`, and any additional prompt explicitly
    moved to inherited mode.
  - Use Haiku only for narrow mechanical workflows such as simple roadmap view,
    dev tag management, release scanning, and issue status if still justified.
  - Use GPT-5.4/GPT-5.5 for deep reasoning/architecture workflows if explicit
    model assignment is appropriate.
  - Use Sonnet only where it remains a justified fallback or cross-vendor
    contrast.
- **Test Scenarios**:
  - Happy path: mechanical prompts are cheap; high-reasoning prompts are not
    underpowered.
  - Edge case: prompt inherits user-selected model and should not be forced.
  - Error path: Haiku assigned to a deep planning/review workflow.
- **Tests**:
  - `tests/model-assignments.Tests.ps1`
- **Acceptance criteria**:
  - Docs and frontmatter agree for every prompt/agent.

## Phase 3: Audit and Regression Guardrails

### 6. Extend context/model audit for vendor and role policy

- **Requirements**: R9, R10, R13, R14, R19, R21, R22, R23
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
  - `.cg-docs/cost/context-audit.md`
  - `.cg-docs/cost/context-audit.json`
- **Details**:
  - Add model parser fields:
    - `vendor`: OpenAI, Anthropic, Google, inherited, unknown.
    - `family`: GPT-5, GPT-5-Codex, Claude, Gemini, Auto, unknown.
    - `role`: inherited, coding, review, reasoning, mechanical, fallback.
  - Add policy checks:
    - Coding workflows must be OpenAI-first.
    - Review workflows must support cross-vendor review.
    - Haiku is allowed only for mechanical workflows.
    - Sonnet requires rationale or fallback/cross-vendor role.
    - Stale model names fail or warn depending on allowlist severity.
    - Every prompt/agent path must map to exactly one catalog role.
    - `docs/model-guide.md` `### Prompts` / `### Agents` tables must parse and
      match frontmatter/catalog assignments.
    - Cross-vendor policy text must have the executable mechanism from Step 4.
    - Prompt-visible route-depth summaries must not drift from
      `.github/shared/review-routing.contract.md`.
  - Keep previous premium/model-picker/context-loading guardrails intact.
- **Test Scenarios**:
  - Happy path: GPT-5.3-Codex classified as OpenAI coding model.
  - Edge case: GPT-5.4 mini classified as OpenAI mechanical/cheap option.
  - Error path: coding prompt defaults to Sonnet without rationale.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_audit_context.py`
- **Acceptance criteria**:
  - Audit report includes vendor/role summary and OpenAI-first compliance.

### 7. Update Pester prompt/model contract tests

- **Requirements**: R10, R13, R19, R24
- **Files**:
  - `tests/model-assignments.Tests.ps1`
  - `tests/prompt-tools.Tests.ps1`
  - `tests/last-run.json` only as generated validation output
- **Details**:
  - Extend current model-assignment tests beyond "has model" vs "inherits
    picker".
  - Add assertions for:
    - OpenAI-first coding workflows.
    - Haiku only for mechanical workflows.
    - Sonnet only with rationale/fallback/cross-vendor purpose.
    - Cross-vendor review text and generator vendor capture.
  - Preserve Pester safety: use `. tests\Run-Tests.ps1` only for full suite;
    do not use ad hoc `Invoke-Pester`.
  - Update header comments in touched Pester files so contributors do not copy
    direct `Invoke-Pester` examples.
- **Test Scenarios**:
  - Happy path: model assignments match policy.
  - Edge case: Pester unavailable in Codex; validation is external and not
    falsely marked passed.
  - Error path: stale model table lets frontmatter drift from docs.
- **Tests**:
  - `. tests\Run-Tests.ps1` in VS Code/PowerShell
- **Acceptance criteria**:
  - Pester tests fail for old Anthropic-default coding assignments.

## Phase 4: Bounded Prompt and Context Slimming Completion

### 8. Finish active prompt/skill split work

- **Requirements**: R11, R12
- **Files**:
  - `.github/prompts/cg-review.prompt.md`
  - `.github/prompts/cg-work.prompt.md`
  - `.github/prompts/cg-fixbug.prompt.md`
  - `.github/prompts/cg-diagnose.prompt.md`
  - `.github/prompts/cg-plan-review.prompt.md`
  - `.github/shared/*.contract.md`
  - relevant `.github/skills/*/SKILL.md`
- **Details**:
  - Bound this phase to prompt/skill split work required for the active
    token-governance milestone features. Do not start a broad prompt rewrite.
  - Eligible targets must satisfy at least one criterion:
    - current audit warning or failure;
    - high-frequency prompt estimated tokens above the current guardrail
      warning threshold;
    - duplicated model-governance or review-routing doctrine that can be moved
      into a shared contract and still loaded explicitly;
    - direct dependency of cross-vendor review or OpenAI-first model policy.
  - Move reusable doctrine into shared contracts or skills only when it reduces
    duplication and keeps command behavior testable.
  - Avoid broad prompt rewrites that weaken explicit safety gates.
- **Test Scenarios**:
  - Happy path: prompt token/reference count decreases or policy clarity
    improves.
  - Edge case: large prompt remains large because shrinking would weaken
    behavior; document rationale.
  - Error path: moved doctrine is no longer loaded by the workflow.
- **Tests**:
  - `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both`
  - Pester prompt tests in VS Code/PowerShell.
- **Acceptance criteria**:
  - Each slimming edit cites the audit warning, token threshold, duplicated
    doctrine, or model-governance dependency that justified it.
  - Remaining active context/prompt-splitting roadmap features have concrete
    validation evidence before closure.

### 9. Reduce always-on context where still measurable

- **Requirements**: R11
- **Files**:
  - `.github/copilot-instructions.md` or template/source equivalent
  - `.github/instructions/*.instructions.md`
  - `docs/context-files.md`
  - `scripts/cg_audit_context.py`
- **Details**:
  - Identify always-on instruction files and their token contribution.
  - Apply only changes that reduce measurable always-on burden or remove
    duplicated doctrine introduced by the model-governance work.
  - Keep routing and safety language, but move deep doctrine behind prompt,
    skill, or shared-contract loading.
  - Keep `AGENTS.md` Codex/Claude adapter separate from GitHub Copilot behavior.
- **Test Scenarios**:
  - Happy path: always-on estimated tokens decrease without losing routing.
  - Edge case: instruction file is intentionally always-on because it is a
    safety contract.
  - Error path: Copilot no longer knows how to route language-specific files.
- **Tests**:
  - `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both`
- **Acceptance criteria**:
  - Audit shows the before/after impact and no new guardrail failures.

## Phase 5: Documentation, Roadmap, and Issue Alignment

### 10. Update user-facing and maintainer docs

- **Requirements**: R8, R12, R13
- **Files**:
  - `docs/model-guide.md`
  - `docs/reference.md`
  - `docs/workflow.md`
  - `.cg-docs/cost/token-optimization-release-checklist.md`
  - `.cg-docs/cost/token-optimization-follow-ups.md`
- **Details**:
  - Document OpenAI-first policy and exact exceptions.
  - Document cross-vendor review and generator vendor capture.
  - Update validation checklist to include new model-policy checks.
  - Keep external VS Code/Copilot runtime checks explicit.
- **Test Scenarios**:
  - Happy path: docs explain how to choose GPT-5.3-Codex and when not to.
  - Edge case: user uses Auto; docs do not infer hidden model.
  - Error path: docs claim runtime dispatch passed from static audit.
- **Tests**:
  - `tests/model-assignments.Tests.ps1`
  - `tests/prompt-tools.Tests.ps1`
- **Acceptance criteria**:
  - Docs match prompt/agent frontmatter and audit policy.

### 11. Prepare remaining roadmap and issue closure evidence

- **Requirements**: R12, R18, R20
- **Files**:
  - `roadmap.json`
  - GitHub issues #92, #93, #94
- **Details**:
  - Keep #92, #93, and #94 open while implementation is active.
  - Treat `roadmap.json` as read-only in `/cg-work`; dispatch `@cg-roadmap` for
    all feature/milestone status writes.
  - Prepare closure evidence for each issue independently:
    - #92 `agent-model-tool-governance`: prompt/agent model matrix, exact model
      string validation, frontmatter/docs sync, and audit policy checks pass.
    - #93 `shrink-always-on-context`: audit before/after shows no new
      guardrail failures and documents any unchanged always-on safety text.
    - #94 `prompt-skill-split`: each split has a cited audit/token/duplication
      reason and prompt-contract tests still pass or remain explicitly external.
  - Do not close issues or mark roadmap features done in this step. Actual
    closure happens only after final validation in Step 13.
  - Closure-after-validation rule: actual roadmap and issue closure happens only after final validation in Step 13.
- **Test Scenarios**:
  - Happy path: roadmap and issue state match implementation state.
  - Edge case: one feature remains partial; milestone stays in-progress.
  - Error path: issue closed before validation.
- **Tests**:
  - Targeted `jq` roadmap status check.
  - `gh issue view` state verification.
- **Acceptance criteria**:
  - Closure evidence is prepared per issue.
  - `roadmap.json` write instructions explicitly use `@cg-roadmap`.

## Phase 6: Final Validation and Knowledge Capture

### 12. Run validation and capture the durable lesson

- **Requirements**: R10, R12, R13
- **Files**:
  - `.cg-docs/solutions/testing-patterns/<new-entry>.md`
  - `.cg-docs/cost/context-audit.md`
  - `.cg-docs/cost/context-audit.json`
  - `.cg-docs/cost/token-optimization-release-checklist.md`
- **Details**:
  - Run available Codex-side validation:
    - Python audit tests.
    - Context/model audit.
    - `git diff --check`.
  - Run VS Code/PowerShell validation where required:
    - `. tests\Run-Tests.ps1`
    - Manual Copilot checks for model-picker and routed dispatch behavior.
  - Capture the model-governance lesson only after available validation has
    run and skipped checks are documented as external requirements.
- **Test Scenarios**:
  - Happy path: all static checks pass and external checks are documented.
  - Edge case: PowerShell unavailable in Codex; checklist requires external
    validation.
  - Error path: solution claims unverified runtime behavior as passed.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_audit_context.py`
  - `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both`
  - `git diff --check`
  - `. tests\Run-Tests.ps1` in VS Code/PowerShell
- **Acceptance criteria**:
  - Release checklist and solution entry clearly separate Codex evidence from
    external VS Code/Copilot evidence.

### 13. Close validated roadmap features and issues

- **Requirements**: R12, R18, R20
- **Files**:
  - `roadmap.json` (read-only verification; writes via `@cg-roadmap`)
  - GitHub issues #92, #93, #94
- **Details**:
  - After Step 12 validation passes or any external requirements are explicitly
    documented, close only the features whose per-issue evidence exists.
  - Dispatch `@cg-roadmap` for each roadmap status update:
    - link this plan to the corresponding feature if needed;
    - mark validated feature(s) done;
    - mark the milestone done only if all features are done.
  - Close the matching GitHub issue(s) with a comment summarizing validation
    evidence.
- **Test Scenarios**:
  - Happy path: all three features validate; all three issues close; milestone
    moves to done through `@cg-roadmap`.
  - Edge case: one feature is still partial; only validated issue(s) close and
    milestone remains in-progress.
  - Error path: roadmap is edited directly instead of via `@cg-roadmap`.
- **Tests**:
  - Targeted `jq` roadmap status read.
  - `gh issue view 92`, `gh issue view 93`, `gh issue view 94`.
- **Acceptance criteria**:
  - Roadmap, issues, and plan status are consistent after final validation.
  - One feature can close without forcing premature closure of the other two.

## Testing Strategy

- Python unit tests validate audit parsing, model classification, vendor/role
  policy, stale model detection, OpenAI-first enforcement, and cross-vendor
  review guardrails.
- Pester prompt tests validate frontmatter, docs/reference sync, prompt-visible
  cross-vendor review text, and model-policy invariants.
- Static audit validates context size, prompt references, model inventory,
  guardrails, benchmark summaries, and before/after deltas.
- Manual VS Code/Copilot validation is required for actual model-picker and
  agent-dispatch behavior.

## Documentation Checklist

- `docs/model-guide.md` explains:
  - OpenAI-first policy.
  - GPT-5.3-Codex preferred coding role.
  - Sonnet as targeted fallback/cross-vendor contrast.
  - Haiku as mechanical-only.
  - inherited model-picker exceptions.
- `docs/reference.md` model columns match prompt and agent frontmatter.
- `docs/workflow.md` explains cross-vendor review and validation limits.
- Release checklist includes the new model-policy gates.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Copilot prompt frontmatter may not accept every displayed model name exactly as shown in the UI. | Model assignment could silently fail or be ignored. | Validate in VS Code/Copilot; if unsupported, use model-picker inheritance with explicit user guidance instead of invalid frontmatter. |
| OpenAI-first policy could overfit to current model availability. | Future model changes make policy stale. | Add allowlist/stale-name checks and document update procedure. |
| Cross-vendor review cannot know the generator model when Auto/model-picker is used. | Review routing may be based on false assumptions. | Record generator model/vendor when known; ask or mark unknown when not known. |
| Prompt slimming could remove safety gates. | Lower correctness or unsafe workflows. | Preserve prompt-contract tests and audit guardrails; only move doctrine where loaded explicitly. |
| Pester unavailable in Codex. | Incomplete validation in this environment. | Keep Pester as VS Code/PowerShell-required external gate; do not mark it passed from static evidence. |
| Too many simultaneous model changes. | Harder review and rollback. | Phase changes by role, keep audit/tests updated before broad edits, and review after each phase. |
| Inherited prompts could be incorrectly treated as OpenAI-first policy failures. | User-controlled model-picker behavior would be weakened. | Model catalog and audit distinguish `inherited` from explicit model assignments; inherited prompts are valid exceptions. |
| Prompt slimming expands beyond the remaining milestone features. | Scope creep delays model-governance completion. | Phase 4 has explicit eligibility criteria and per-edit justification requirements. |
| Guardrails are added after broad model edits. | Drift or invalid model assignments can slip through until late validation. | Step 2 adds/enforces audit and Pester policy checks before Phase 2 frontmatter changes. |
| Cross-vendor review is only documented, not executable. | The plan appears complete but runtime reviews still use a fixed or unchanged model. | Step 4 requires an executable mechanism or explicit manual model-picker handoff, and tests fail policy text without a mechanism. |
| Direct `roadmap.json` writes conflict with `/cg-work` permissions. | Implementation blocks or violates prompt permissions. | `roadmap.json` is read-only for verification; all writes go through `@cg-roadmap`. |

## Out of Scope

- Changing the user's Copilot account or model availability.
- Adding non-Copilot model API calls.
- Processing unrelated `.cg-docs/inbox/` ideas.
- Closing #92, #93, or #94 before implementation evidence exists.
- Claiming hidden Copilot Auto model identity.
- Directly editing `roadmap.json` from `/cg-work`; use `@cg-roadmap` for writes.

## Completion Contract

### Outcome

Compound GPID has an explicit OpenAI-first, performance-aware model governance
system. Coding workflows prefer GPT-5.3-Codex or the best available OpenAI
coding model, review supports cross-vendor validation, Haiku is reserved for
mechanical tasks, Sonnet is a targeted fallback or contrast model, and tests
prevent model-policy drift.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Model guide documents OpenAI-first policy, GPT-5.3-Codex coding role, Sonnet fallback role, Haiku mechanical role, and inherited prompt exceptions. | `docs/model-guide.md` | yes |
| V2 | 1 | Durable model catalog records allowed model names, vendor, family, role, status, provenance, and prompt/agent role assignments. | `.github/shared/model-catalog.json`; optional `.github/shared/model-assignments.json` | yes |
| V3 | 1 | Exact Copilot frontmatter support for target model strings is recorded before broad prompt/agent edits. | `.cg-docs/cost/token-optimization-release-checklist.md` | yes |
| V4 | 2 | Prompt/agent frontmatter and docs/reference agree on model assignments. | `tests/model-assignments.Tests.ps1`; `docs/reference.md` | yes |
| V5 | 2 | Coding/fixing workflows are OpenAI-first or explicitly inherited with rationale. | `.github/prompts/*.prompt.md`; `.github/agents/*.agent.md` | yes |
| V6 | 2 | Cross-vendor review behavior is documented and testable without weakening review depth routing. | `.github/shared/review-routing.contract.md`; `.github/prompts/cg-review.prompt.md`; `.github/prompts/cg-work.prompt.md` | yes |
| V7 | 2 | Generator model/vendor/source metadata schema exists in execution reports and review handoffs. | `.github/shared/goal-execution.contract.md`; `.github/prompts/cg-work.prompt.md`; `.github/prompts/cg-review.prompt.md` | yes |
| V8 | 3 | Audit classifies model vendor/family/role, detects stale or noncompliant assignments, parses model-guide tables, and verifies cross-vendor mechanism presence. | `python3 -m pytest scripts/tests/test_audit_context.py` | yes |
| V9 | 4 | Context/prompt slimming has no new guardrail failures and every slimming edit has an eligibility rationale. | `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both`; implementation notes | yes |
| V10 | 5 | #92 has feature-specific validation evidence prepared before closure. | closure evidence section/checklist | yes |
| V11 | 5 | #93 has feature-specific validation evidence prepared before closure. | closure evidence section/checklist | yes |
| V12 | 5 | #94 has feature-specific validation evidence prepared before closure. | closure evidence section/checklist | yes |
| V13 | final | No whitespace/diff hygiene issues. | `git diff --check` | yes |
| V14 | final | Pester prompt tests pass or are explicitly documented as external VS Code/PowerShell validation if unavailable in Codex. | `. tests\Run-Tests.ps1`; `tests/last-run.json` | yes |
| V15 | final | Manual Copilot validation records model-picker and routed dispatch behavior; static audit does not claim runtime proof. | `.cg-docs/cost/token-optimization-release-checklist.md` | yes |
| V16 | final | Validated roadmap feature updates are dispatched through `@cg-roadmap`, not direct `roadmap.json` edits. | targeted roadmap status read after dispatch | yes |
| V17 | final | Validated GitHub issues close only after final validation, with evidence comments. | `gh issue view 92`; `gh issue view 93`; `gh issue view 94` | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | OpenAI-first applies to explicit model assignments, not prompts intentionally inheriting the user's chat-box model. | model guide + audit |
| C2 | Sonnet must not remain a blanket default for coding/review workflows without rationale. | audit policy |
| C3 | Haiku is allowed only for extremely simple mechanical tasks. | audit policy |
| C4 | Cross-vendor review must not override P0/P1 review depth or data-risk routing. | review-routing tests |
| C5 | Runtime Copilot behavior must be validated in VS Code/Copilot, not inferred from Codex static checks. | release checklist |
| C6 | Existing Pester safety rules remain mandatory. | project instructions |
| C7 | Inherited/model-picker prompts are valid OpenAI-first exceptions and must not be forced to explicit OpenAI frontmatter. | model catalog + audit |
| C8 | Broad prompt/context slimming is limited to measured audit/token/duplication/model-governance needs. | implementation notes + audit |
| C9 | Model-policy guardrails must exist before broad model frontmatter edits. | test/audit ordering |
| C10 | Roadmap writes must go through `@cg-roadmap`; direct `roadmap.json` edits are verification-only. | implementation log |
| C11 | Cross-vendor review cannot be marked complete without an executable mechanism or explicit manual model-picker handoff. | audit/Pester |

### Boundaries

- Allowed: `.github/prompts/`, `.github/agents/`, `.github/shared/`,
  selected `.github/skills/`, `docs/`, `tests/`, `scripts/cg_audit_context.py`,
  `.cg-docs/cost/`, `.cg-docs/solutions/`, and `roadmap.json`.
- Out of scope: account-level model configuration, external API integration,
  unrelated roadmap issues, and unverified runtime claims.

### Iteration Policy

1. Create/update the model catalog and matrix before changing frontmatter.
2. Add or update audit/Pester policy checks before broad model frontmatter
   changes.
3. Validate exact model strings in VS Code/Copilot before broad prompt/agent
   frontmatter edits.
4. Update tests/audit for a policy rule before applying it broadly.
5. Apply model assignment changes by workflow role.
6. Run Python/audit checks after each broad model-assignment pass.
7. Keep Pester and manual Copilot validation explicitly external when not
   runnable in Codex.
8. Prepare roadmap/issue closure evidence before final validation; perform
   actual closure only after final validation.
9. Close roadmap issues only after the relevant feature has implementation and
   validation evidence.

### Blocked-Stop Conditions

- Copilot rejects or ignores the target explicit model names and no valid
  frontmatter syntax can be confirmed.
- A model-policy change would contradict user-controlled model-picker behavior.
- Audit or tests show model-policy drift that cannot be fixed without changing
  scope.
- Cross-vendor review cannot be represented without misleading users about the
  actual generator model.
- Pester or manual Copilot checks are required for final closure and cannot be
  completed or explicitly deferred.
