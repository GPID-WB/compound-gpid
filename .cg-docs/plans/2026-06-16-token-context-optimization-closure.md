---
date: 2026-06-16
title: "Token Context Optimization Closure"
status: active
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-06-16-token-context-optimization-closure.md"
language: "Python/PowerShell/Markdown"
estimated-effort: "medium"
deviation-policy: "ask"
tags: [token-optimization, context-loading, prompt-splitting, model-governance, audit]
phases: 4
execution-report: ".cg-docs/work-reports/2026-06-16-token-context-optimization-closure.md"
roadmap-features:
  - token-optimization-model-governance/shrink-always-on-context
  - token-optimization-model-governance/prompt-skill-split
---

# Plan: Token Context Optimization Closure

## Objective

Close the remaining Token Optimization & Model Governance work for #93 and #94
with a bounded, evidence-driven implementation: classify current audit warnings,
fix ordinary broad context-loading where measurable, slim or justify `/cg-work`,
and add a small user-facing `/cg-token-audit` command backed by deterministic
Python analysis.

## Context

The current context/model audit reports `failures = 0`, but still has warning
signals:

- `/cg-work` is a high-frequency prompt above the warning threshold at 5360
  estimated tokens.
- The audit reports 31 context-loading risk signals, including broad wording
  around `.cg-docs/`, `roadmap.json`, and `compound-gpid.context.md`.
- The largest token masses are generated or tactical artifacts:
  `.cg-docs/brain-index.json`, `BRAIN-log.md`, `BRAIN-01.md`, `roadmap.json`,
  and `compound-gpid.context.md`.
- Existing prior work already added model-governance audit guardrails,
  benchmark summaries, query-first Knowledge Brain policy, review routing
  contracts, and goal-driven execution contracts.

This plan intentionally avoids a broad prompt rewrite. It focuses on the
warning classes and user-visible diagnostics needed to close #93 and #94.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Classify current audit warnings as `fix`, `accept`, or `docs-only`, or an equivalent reviewed-warning taxonomy. | brainstorm |
| R2 | Fix ordinary broad context-loading instructions where a staged or targeted read preserves behavior. | brainstorm + context-loading contract |
| R3 | Keep maintenance, roadmap, release, setup, and docs-only warning rationale explicit instead of forcing warning count to zero. | brainstorm |
| R4 | Treat `/cg-work` as the primary prompt-slimming target because it is the only high-frequency prompt above 5000 estimated tokens. | audit |
| R5 | Do not move safety-critical behavior into optional skills without an explicit caller load point. | brainstorm |
| R6 | Preserve Pester safety, roadmap write discipline, review routing, protected-artifact rules, and goal-driven execution behavior. | charter + prompt contracts |
| R7 | Add a user-facing `/cg-token-audit` command that runs deterministic tooling and emits compact advisory recommendations. | user |
| R8 | The token audit command must not ask the model to inspect large `.cg-docs/`, BRAIN, roadmap, or context artifacts directly. | user |
| R9 | Prefer extending existing `scripts/cg_audit_context.py` over creating a parallel analyzer. | prior token-audit pattern |
| R10 | Provide cross-platform CLI wrappers so the command can run from linked consumer projects through the installed Compound GPID path. | repo install pattern |
| R11 | Update docs and prompt-entry references so users can discover `/cg-token-audit`. | user-facing command convention |
| R12 | Prepare closure evidence for #93 and #94, but route roadmap writes through `@cg-roadmap` rather than direct edits. | roadmap discipline |
| R13 | Ensure `/cg-token-audit` analyzes the current user project root, not the installed Compound GPID clone. | plan review |
| R14 | Update existing prompt/wrapper tests that encode old command inventories or context-loading assumptions so they validate the new command intentionally. | plan review |

## Implementation Steps

## Phase 1: Audit Triage and Recommendation Foundation

### 1. Extend audit data with warning review classifications

- **Requirements**: R1, R2, R3, R9
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
  - `.cg-docs/cost/context-audit.json`
  - `.cg-docs/cost/context-audit.md`
- **Details**:
  - Add a deterministic classification layer for guardrail warnings and context
    risk rows. At minimum classify warnings as:
    - `fix`: ordinary workflow broad-loading or high-frequency prompt bulk that
      should be reduced.
    - `accept`: intentional maintenance, roadmap, setup, release, or
      knowledge-base behavior that needs broader structured reads.
    - `docs-only`: documentation wording that does not imply runtime prompt
      loading.
  - Include the classification and a short reason in JSON output so downstream
    reporting and `/cg-token-audit` can reuse it.
  - Render a compact reviewed-warning table in Markdown. The release-readiness
    checklist can still report nonzero warnings, but the report must distinguish
    unresolved `fix` warnings from accepted or docs-only warnings.
  - Preserve existing guardrail behavior: real failures still fail; accepted
    warnings must not hide failures.
- **Test Scenarios**:
  - Happy path: docs-only warning is classified as `docs-only`, roadmap agent
    warning as `accept`, and ordinary broad prompt read as `fix`.
  - Edge case: a maintenance workflow with an explicit narrow read remains
    `targeted` or `accept`, not `fix`.
  - Error path: ordinary prompt reads `brain-index.json` wholesale; guardrail
    failure behavior remains intact.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_audit_context.py`
- **Acceptance criteria**:
  - Audit JSON exposes reviewed-warning classifications.
  - Audit Markdown shows classification counts or table.
  - Existing zero-failure state is preserved unless a true regression is found.

### 2. Add token-efficiency recommendation generation

- **Requirements**: R7, R8, R9
- **Files**:
  - `scripts/cg_audit_context.py`
  - `scripts/tests/test_audit_context.py`
- **Details**:
  - Add a report builder that converts audit facts into concise, user-facing
    recommendations.
  - Recommendations should be deterministic and based on structured audit data,
    not model inspection of large files.
  - Recommended categories:
    - largest token contributors;
    - always-on instruction/context burden;
    - high-frequency prompt burden;
    - Knowledge Brain hygiene;
    - review-depth/model-use suggestions;
    - broad context-loading risks;
    - quick wins versus advanced improvements.
  - Recommendations should be advisory. They must never rewrite config, change
    review depth, or change model defaults automatically.
  - Use thresholds that already exist where possible:
    - `THRESHOLD_HIGH_FREQ_PROMPT_WARN`;
    - `THRESHOLD_ALWAYS_ON_WARN`;
    - top-file estimated token ranking;
    - context-loading classification counts.
- **Test Scenarios**:
  - Happy path: oversized `compound-gpid.context.md` produces a context
    slimming recommendation.
  - Edge case: no BRAIN files exist; output says no Knowledge Brain artifact
    burden detected instead of failing.
  - Error path: audit report has failures; recommendation output highlights
    failures before optimization advice.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_audit_context.py`
- **Acceptance criteria**:
  - Recommendation generation is covered by Python unit tests.
  - Recommendations are compact enough for prompt output and do not include raw
    large artifact bodies.

## Phase 2: User-Facing Token Audit Command

### 3. Add a thin `/cg-token-audit` prompt

- **Requirements**: R7, R8, R11, R13, R14
- **Files**:
  - `.github/prompts/cg-token-audit.prompt.md`
  - `.github/copilot-instructions.md`
  - `docs/reference.md`
  - `docs/workflow.md`
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Create `/cg-token-audit` as a thin command that:
    - reads `compound-gpid.md` for bearings if present;
    - loads `.github/shared/context-loading.contract.md`;
    - explicitly avoids opening `.cg-docs/`, BRAIN partitions,
      `brain-index.json`, `roadmap.json`, or `compound-gpid.context.md`
      directly for analysis;
    - runs deterministic tooling through the installed CLI wrapper with
      `--root .` so the analyzed root is the current user project, not the
      installed Compound GPID clone;
    - summarizes the generated recommendation output.
  - The prompt should be advisory only. It may suggest changes such as using a
    lighter review mode for low-risk work or trimming large context files, but
    it must not modify files.
  - Include a fallback if the CLI is not on `PATH`: tell the user to run
    `cg-token-audit --help` or reinstall/update Compound GPID. Do not fall back
    to broad model inspection of files.
  - Decide exact command spelling as `/cg-token-audit` and CLI wrapper
    `cg-token-audit` to keep intent explicit.
  - Add prompt tests that assert the prompt includes `cg-token-audit --root .`
    and does not provide a fallback path that asks the model to inspect large
    artifacts directly.
  - Update any existing prompt-inventory or context-layer tests that assume a
    fixed list of prompts so `/cg-token-audit` is intentionally included or
    explicitly exempted with rationale.
- **Test Scenarios**:
  - Happy path: prompt references `cg-token-audit` and tells the model to use
    deterministic output from `cg-token-audit --root .`.
  - Edge case: CLI unavailable; prompt reports setup issue and stops.
  - Error path: prompt tells the model to read `.cg-docs/` directly; prompt
    tests fail.
  - Error path: prompt invokes the wrapper without `--root .`; prompt tests
    fail because that would audit the installed plugin clone by default.
- **Tests**:
  - Pester prompt-contract tests in `tests/prompt-tools.Tests.ps1`.
- **Acceptance criteria**:
  - New prompt exists with no restrictive `tools:` frontmatter.
  - Workflow entry points and docs mention `/cg-token-audit`.
  - Prompt tests verify no broad model-read fallback is introduced.

### 4. Add cross-platform CLI wrappers for token audit

- **Requirements**: R7, R9, R10, R13, R14
- **Files**:
  - `bin/cg-token-audit`
  - `bin/cg-token-audit.cmd`
  - `install.ps1`
  - `scripts/install.sh`
  - `tests/install.Tests.ps1`
  - `tests/bash-scripts.Tests.ps1`
  - `tests/parity.Tests.ps1`
- **Details**:
  - Add a macOS/Linux bash wrapper that calls `scripts/cg_audit_context.py`
    from the installed Compound GPID directory and forwards all arguments.
  - Add a Windows CMD wrapper using the established Python detection pattern
    from `cg-skill-windows-cmd-python-detection`:
    - `where` pre-checks for `python3`, `python`, and `py`;
    - version verification against `^Python [0-9]`;
    - exact exit-code propagation;
    - all arguments forwarded.
  - Update installation scripts so the wrapper is installed on PATH alongside
    `cg-index`.
  - Add a user-friendly default mode for the CLI, likely by extending
    `cg_audit_context.py` with `--recommendations` or `--summary`, while
    preserving existing `--format json|md|both`.
  - Ensure the command can run from consumer project roots:
    - the wrapper may live in the installed Compound GPID clone;
    - the default script behavior may still resolve paths relative to the
      script for developer use;
    - the user-facing prompt must pass `--root .`;
    - tests must cover that `--root .` causes analysis of the current working
      project instead of the script directory.
  - Update wrapper inventory tests so `bin/cg-token-audit` and
    `bin/cg-token-audit.cmd` are included alongside `cg-index` and
    `cg-brain-init`, including install-script copy/generation assertions.
- **Test Scenarios**:
  - Happy path: wrapper exists and delegates to `cg_audit_context.py`.
  - Happy path: `cg-token-audit --root <temp-project>` analyzes the supplied
    project root, even when the wrapper/script lives elsewhere.
  - Edge case: Python is unavailable on Windows; wrapper emits the established
    Python install message.
  - Error path: wrapper fails to propagate script exit code; tests catch it.
  - Error path: install tests omit the new wrapper from command inventory; tests
    fail until inventories are updated.
- **Tests**:
  - Pester wrapper tests in `tests/install.Tests.ps1`.
  - Bash wrapper tests in `tests/bash-scripts.Tests.ps1`.
  - `python3 -m pytest scripts/tests/test_audit_context.py`.
- **Acceptance criteria**:
  - Wrappers are committed and installation scripts copy or generate them.
  - Windows wrapper follows the safe Python detection pattern.
  - Bash wrapper is executable and delegates self-relatively.

## Phase 3: Targeted Context Loading Fixes and `/cg-work` Slimming

### 5. Apply targeted context-loading fixes to ordinary prompts

- **Requirements**: R1, R2, R3, R5, R6, R14
- **Files**:
  - `.github/prompts/cg-diagnose.prompt.md`
  - `.github/prompts/cg-fixbug.prompt.md`
  - `.github/prompts/cg-fix-problems.prompt.md`
  - `.github/prompts/cg-ideate.prompt.md`
  - `.github/prompts/cg-plan-review.prompt.md`
  - `.github/prompts/cg-wiki.prompt.md`
  - `.github/agents/cg-wiki.agent.md`
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - For ordinary prompts, replace unqualified "read
    `compound-gpid.context.md`" wording with the staged contract:
    load `.github/shared/context-loading.contract.md`, start at Stage 0/1/2,
    and search headings or snippets only when tactical context is needed.
  - For wiki workflows, read only `## Wiki Configuration` or the folder marker
    from `compound-gpid.context.md`; do not imply a full file read.
  - For ideation and plan review, parse roadmap fields only when needed for
    deduplication, status, or side-idea capture; display still goes through
    roadmap view where appropriate.
  - Update legacy context-layer prompt tests that currently assert broad
    `compound-gpid.context.md` references across a fixed prompt set. The new
    assertions should require either:
    - staged/targeted context-loading contract language; or
    - an explicit maintenance/docs-only exception.
  - Do not alter hard stops, expected-behavior gates, Pester safety, roadmap
    write delegation, or review routing.
- **Test Scenarios**:
  - Happy path: broad context risk count decreases or risk rows move to
    targeted/justified.
  - Edge case: setup or maintenance workflows remain accepted because full-file
    semantics are intentional.
  - Error path: ordinary prompt loses the missing-charter warning or context
    skip behavior; prompt tests catch it.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_audit_context.py`
  - Pester prompt-contract tests in `tests/prompt-tools.Tests.ps1`.
- **Acceptance criteria**:
  - Regenerated audit shows classified `fix` warnings reduced or eliminated for
    the touched ordinary prompts.
  - No new guardrail failures.

### 6. Slim `/cg-work` without weakening safety gates

- **Requirements**: R4, R5, R6
- **Files**:
  - `.github/prompts/cg-work.prompt.md`
  - `.github/shared/goal-execution.contract.md`
  - `.github/shared/review-routing.contract.md`
  - `tests/prompt-tools.Tests.ps1`
  - `scripts/tests/test_audit_context.py`
- **Details**:
  - Inspect `/cg-work` for text that is:
    - duplicated from a shared contract already loaded at point of use;
    - non-safety-heavy report formatting;
    - repeated explanatory prose that can be made compact without changing
      behavior.
  - Keep the following inline or explicitly loaded before use:
    - Pester safe-runner discipline;
    - protected artifact rejection;
    - roadmap write delegation;
    - goal-execution contract authority and evidence gate;
    - review-mode dispatch semantics.
  - If a block is moved to a shared contract, update `/cg-work` to load that
    contract before relying on it.
  - Target: get `/cg-work` below 5000 estimated tokens. If that is not possible
    without removing safety-critical text, document the accepted rationale in
    the audit/report notes.
- **Test Scenarios**:
  - Happy path: `/cg-work` token count drops below 5000 and review-mode tests
    still pass.
  - Edge case: token count remains above 5000 because safety-critical text is
    retained; accepted rationale is recorded.
  - Error path: `review:auto`, `review:manual`, or `review:none` semantics
    drift; prompt tests and audit guardrails fail.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_audit_context.py`
  - Pester prompt-contract tests in `tests/prompt-tools.Tests.ps1`.
- **Acceptance criteria**:
  - `/cg-work` benchmark token count is below 5000 or explicitly accepted as
    safety-critical.
  - Review routing and goal evidence gates remain intact.

### 7. Record split/slimming rationale for #94

- **Requirements**: R1, R4, R5, R12
- **Files**:
  - `.cg-docs/cost/context-audit.md`
  - `.cg-docs/cost/token-optimization-release-checklist.md`
  - `.cg-docs/cost/token-optimization-follow-ups.md`
- **Details**:
  - Maintain a short split ledger in the generated audit or cost docs:
    - source prompt;
    - extracted/shared artifact if any;
    - caller load point;
    - audit/token/duplication reason;
    - validation evidence.
  - If no split is performed because all candidates are safety-critical, record
    that as accepted rationale with audit evidence.
  - Keep non-blocking future refactors in `token-optimization-follow-ups.md`.
- **Test Scenarios**:
  - Happy path: each split has a traceable reason and explicit load point.
  - Edge case: no split performed; rationale cites safety-critical behavior.
  - Error path: split exists but caller does not load the new contract; tests or
    plan review flag it.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_audit_context.py`
  - Manual cost-doc review.
- **Acceptance criteria**:
  - #94 closure evidence can point to specific split/slimming decisions, not
    broad claims.

## Phase 4: Validation, Closure Evidence, and Roadmap Handoff

### 8. Regenerate audits and validate regression surface

- **Requirements**: R1, R2, R3, R6, R12
- **Files**:
  - `.cg-docs/cost/context-audit.json`
  - `.cg-docs/cost/context-audit.md`
  - `tests/last-run.json`
- **Details**:
  - Run Python audit tests.
  - Regenerate audit JSON and Markdown with before/after comparison if a
    previous baseline copy is available.
  - Run `git diff --check`.
  - Run the safe Pester runner in VS Code/PowerShell when available:
    `. tests\Run-Tests.ps1`. Read `tests/last-run.json` for the result.
  - If PowerShell is unavailable in Codex, document Pester as external rather
    than claiming it passed.
- **Test Scenarios**:
  - Happy path: Python tests pass, audit failures remain zero, and Pester safe
    runner passes or is documented external.
  - Edge case: warning count remains nonzero but every warning is classified as
    fixed, targeted, accepted, docs-only, or follow-up.
  - Error path: any guardrail failure appears; stop before closure.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_audit_context.py`
  - `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both`
  - `git diff --check`
  - `. tests\Run-Tests.ps1` in VS Code/PowerShell when available.
- **Acceptance criteria**:
  - Required validation evidence is available or explicitly external.
  - No guardrail failures.

### 9. Prepare closure evidence for #93, #94, and milestone handoff

- **Requirements**: R1, R3, R7, R12
- **Files**:
  - `.cg-docs/cost/context-audit.md`
  - `.cg-docs/cost/token-optimization-release-checklist.md`
  - `.cg-docs/cost/token-optimization-follow-ups.md`
  - `roadmap.json` (read-only verification only)
- **Details**:
  - Prepare closure evidence:
    - #93: before/after context warning classification, ordinary broad-read
      reductions, always-on/context rationale, and no guardrail failures.
    - #94: split/slimming ledger, `/cg-work` token result or accepted safety
      rationale, explicit load points for any moved doctrine, and tests.
    - `/cg-token-audit`: command/prompt/tooling/docs evidence as reusable
      ongoing optimization support.
  - Do not edit `roadmap.json` directly. After validation, use `@cg-roadmap` to
    link this plan to the active features and update feature statuses.
  - If all milestone features become done, use `@cg-roadmap` for milestone
    completion as well.
- **Test Scenarios**:
  - Happy path: closure checklist has enough evidence to mark #93/#94 done.
  - Edge case: Pester remains external; checklist records the external
    validation requirement.
  - Error path: roadmap status update would require direct JSON edit; stop and
    dispatch `@cg-roadmap`.
- **Tests**:
  - Targeted read of roadmap feature fields after `@cg-roadmap` dispatch.
- **Acceptance criteria**:
  - Closure evidence is ready before any roadmap status update.
  - Roadmap writes are delegated, not direct.

## Testing Strategy

- Use Python unit tests for deterministic audit and recommendation behavior:
  `python3 -m pytest scripts/tests/test_audit_context.py`.
- Use prompt-contract Pester tests for new prompt behavior and preservation of
  safety/routing text.
- Use install and wrapper tests for CLI wiring:
  `tests/install.Tests.ps1`, `tests/bash-scripts.Tests.ps1`, and
  `tests/parity.Tests.ps1` where relevant.
- Use regenerated audit output as the main acceptance artifact for #93 and #94.
- Use `git diff --check` for whitespace and patch hygiene.
- Use the canonical safe Pester runner only:
  `. tests\Run-Tests.ps1`, then inspect `tests/last-run.json`.

## Documentation Checklist

- Add `/cg-token-audit` to `.github/copilot-instructions.md` Workflow Entry
  Points.
- Add `/cg-token-audit` to `docs/reference.md`.
- Add a short workflow note explaining when to use `/cg-token-audit`.
- Document that the command is advisory and deterministic, and does not modify
  files.
- Update cost/audit documentation to explain reviewed warning classifications.
- Keep Codex/Claude compatibility material in `AGENTS.md`, not in `.github/`
  Copilot assets.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Prompt slimming removes a safety gate. | `/cg-work` may complete unsafe work or bypass evidence. | Keep Pester, roadmap, protected-artifact, review-routing, and evidence-gate rules inline or explicitly loaded before use. |
| Tests pass but prompt behavior changes semantically. | Static validation misses runtime prompt regressions. | Keep edits tied to audit evidence and require manual Copilot/Pester validation where static tests are insufficient. |
| `/cg-token-audit` causes broad model reads. | The diagnostic command worsens token use. | Prompt must run deterministic tooling and stop if CLI is unavailable. |
| CLI wrappers do not work in consumer projects. | Users cannot run the command after install. | Follow existing `cg-index` wrapper and install patterns; add wrapper tests. |
| Warning classification hides real failures. | Milestone appears complete while risk remains. | Keep guardrail failures separate; accepted/docs-only applies only to warnings. |
| Roadmap updates bypass the agent. | Roadmap schema or status discipline regresses. | Treat `roadmap.json` as read-only in implementation and dispatch `@cg-roadmap` for writes. |

## Out of Scope

- Broad prompt rewrite across all large prompts.
- Changing review-depth defaults.
- Changing model-governance policy beyond advice emitted by `/cg-token-audit`.
- Reworking Knowledge Brain indexing or clustering architecture.
- Direct `roadmap.json` edits.
- Moving Codex/Claude compatibility into `.github/` Copilot assets.

## Completion Contract

### Outcome

The Token Optimization & Model Governance milestone has a bounded implementation
path for #93 and #94: audit warnings are classified and acted on, ordinary broad
context reads are reduced, `/cg-work` is slimmed or explicitly justified, and
users get a deterministic `/cg-token-audit` command that reports project
token/context efficiency recommendations without loading large artifacts into
model context.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Audit output includes fix/accept/docs-only classification or equivalent reviewed-warning rationale. | `.cg-docs/cost/context-audit.md` / JSON fields | yes |
| V2 | 1 | Python tests cover recommendation generation and warning classification behavior. | `python3 -m pytest scripts/tests/test_audit_context.py` | yes |
| V3 | 2 | `/cg-token-audit` prompt exists, is thin, advisory, and runs deterministic tooling instead of broad model reads. | `.github/prompts/cg-token-audit.prompt.md`; prompt tests | yes |
| V4 | 2 | Installed CLI wrapper works cross-platform and does not assume consumer projects contain this repo's `scripts/` directory. | `bin/cg-token-audit`, `bin/cg-token-audit.cmd`, install/bash tests | yes |
| V5 | 3 | Ordinary prompt broad reads are converted to staged/targeted reads where classified as `fix`. | regenerated context audit | yes |
| V6 | 3 | `/cg-work` token count decreases below 5000 or remaining size is explicitly justified as safety-critical. | regenerated context audit benchmark row | yes |
| V7 | 3 | Any prompt split has a cited audit/token/duplication reason and explicit caller load point. | implementation notes / audit report | yes |
| V8 | final | Guardrail failures remain zero and warnings are fixed, targeted, accepted, or docs-only. | regenerated `.cg-docs/cost/context-audit.md` | yes |
| V9 | final | Pester safe runner passes, or PowerShell validation is explicitly documented as external if unavailable in Codex. | `. tests\Run-Tests.ps1`; `tests/last-run.json` | yes |
| V10 | final | Roadmap/issue closure evidence for #93/#94 is prepared; actual roadmap writes go through `@cg-roadmap`. | closure evidence section/checklist | yes |
| V11 | final | `/cg-token-audit` prompt and wrapper tests prove the command analyzes `--root .` / supplied project roots rather than the installed plugin root. | prompt, Python, install, and wrapper tests | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | all | Do not weaken Pester safety or add direct unsafe `Invoke-Pester` patterns. | Pester safety tests and prompt review |
| C2 | all | Do not modify `roadmap.json` directly during implementation. | diff review; roadmap writes routed through `@cg-roadmap` |
| C3 | all | Do not move safety-critical behavior into optional skills without explicit Step 0 load. | prompt/contract review |
| C4 | all | Keep review routing canonical in `.github/shared/review-routing.contract.md`. | prompt tools + audit guardrails |
| C5 | all | Keep Codex/Claude compatibility in `AGENTS.md`, not `.github/` Copilot assets. | diff review |
| C6 | 2 | `/cg-token-audit` must be advisory, not auto-fixing or silently changing config. | prompt and script behavior |
| C7 | 2 | `/cg-token-audit` must pass an explicit project root from user workflows; script-directory defaults are not acceptable for the slash command. | prompt and wrapper tests |

### Boundaries

- Allowed: `.github/prompts/`, selected `.github/shared/`, docs, tests,
  `scripts/cg_audit_context.py`, `bin/`, install wrappers, and generated
  `.cg-docs/cost/` audit artifacts.
- Out of scope: broad prompt rewrite.
- Out of scope: direct `roadmap.json` edits.
- Out of scope: changing review depth defaults or safety gates.
- Out of scope: reworking Knowledge Brain architecture beyond audit/advice
  reporting.

### Iteration Policy

1. Fix audit-classified ordinary broad reads before chasing cosmetic token
   reductions.
2. Slim `/cg-work` only where the removed text is duplicated,
   non-safety-heavy, or explicitly loaded elsewhere.
3. Prefer extending existing `cg_audit_context.py` over creating a parallel
   analyzer.
4. If a split would weaken standalone prompt behavior, keep the text inline
   and document the rationale.
5. Closure evidence must distinguish static audit, Python tests, Pester, and
   manual Copilot validation.

### Blocked-Stop Conditions

- A required verification command cannot be run or documented as external.
- `/cg-token-audit` would require broad model loading of `.cg-docs/`, BRAIN
  files, or `compound-gpid.context.md`.
- A proposed split removes a safety gate without an explicit caller load point.
- Guardrail failures become nonzero.
- Roadmap closure would require direct manual edits to `roadmap.json`.
