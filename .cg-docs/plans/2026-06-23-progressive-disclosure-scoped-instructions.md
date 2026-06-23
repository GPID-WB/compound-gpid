---
date: 2026-06-23
title: "Progressive Disclosure Skills and Scoped Instructions"
status: completed
completed-date: 2026-06-23
completed-phases: [1, 2, 3, 4]
scope: "Deep"
brainstorm: null
language: "Markdown/Python/PowerShell"
estimated-effort: "large"
deviation-policy: "autonomous"
tags: [token-efficiency, progressive-disclosure, context-loading, skills, instructions]
phases: 4
roadmap-features:
  - token-efficiency-core-system/phase-1-4-progressive-disclosure-cleanup
---

# Plan: Progressive Disclosure Skills and Scoped Instructions

## Objective

Implement Phase 1.4 by tightening progressive-disclosure boundaries in prompts, agents, skills, and docs so ordinary workflows load minimal context by default and expand only through targeted, justified reads.

## Context

Phase 1.1 established token/context baselines, Phase 1.2 added budgeted Brain retrieval, and Phase 1.3 added compact command-output summaries. The next bottleneck is default instruction wording that can still encourage broad reads of `.cg-docs/`, `compound-gpid.context.md`, `roadmap.json`, or generated Brain artifacts.

Existing guardrails already detect broad context-loading risks in `scripts/cg_audit_context.py` and report them in `.cg-docs/cost/context-audit.*`. Phase 1.4 should improve prompt/skill/instruction shape without reworking roadmap, issue, setup, release, or compound semantics.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Keep ordinary workflows staged and query-first using `.github/shared/context-loading.contract.md`. | context-loading contract |
| R2 | Avoid unqualified whole-file reads of `.cg-docs/`, generated Brain artifacts, `compound-gpid.context.md`, and `roadmap.json` in ordinary/default paths. | roadmap strategy |
| R3 | Preserve maintenance workflows that explicitly require whole-file semantics, but require context-expansion rationale and narrow field/heading selection where practical. | context-loading contract |
| R4 | Keep skill descriptions specific and short; move repeated doctrine to focused references only when used. | roadmap strategy |
| R5 | Add tests or audit checks that prevent regressions in progressive-disclosure wording. | evidence requirements |
| R6 | Do not introduce external services, optional retrieval backends, cross-agent adapters, snapshots, or token-saving claims. | objective hard stop |
| R7 | Preserve Pester safety and existing command semantics. | project instructions |

## Phase 1: Audit and Contract Coverage

### 1. Add progressive-disclosure audit checks
- **Files**: `scripts/cg_audit_context.py`, `scripts/tests/test_audit_context.py`
- **Details**:
  - Add or extend tests around broad context-loading findings so ordinary prompts with unqualified reads fail guardrail expectations.
  - Add explicit classification coverage for justified maintenance wording so allowed full reads must include a context-expansion rationale.
  - Keep findings advisory/guardrail-compatible with the existing token audit output.
- **Tests**:
  - Targeted Python tests for ordinary prompt broad-read detection.
  - Targeted Python tests for justified context-expansion wording.

### 2. Inventory current broad-read wording
- **Files**: `.github/prompts/*.prompt.md`, `.github/agents/*.agent.md`, `.github/skills/**/SKILL.md`, `docs/*.md`
- **Details**:
  - Use the current audit output and `rg` searches to classify each finding as:
    - ordinary workflow wording to fix;
    - maintenance workflow wording to narrow or justify;
    - docs-only wording that should not imply runtime broad loading.
  - Do not edit unrelated prompt behavior.

## Phase 2: Prompt, Agent, and Skill Cleanup

### 3. Rewrite ordinary/default instructions to staged reads
- **Files**: likely `.github/prompts/cg-strategy.prompt.md`, `.github/prompts/cg-compound-refresh.prompt.md`, `.github/prompts/cg-token-audit.prompt.md`, `.github/prompts/cg-work.prompt.md`, targeted docs where needed
- **Details**:
  - Replace broad reads with frontmatter/heading/snippet/structured-field reads where possible.
  - Use `cg-index query` for prior knowledge when prior project knowledge is needed.
  - Add `Context expansion: ...` rationale only where whole-file reads remain required.
- **Tests**:
  - Existing prompt-tool and audit-context tests.

### 4. Justify maintenance-agent full reads without changing semantics
- **Files**: likely `.github/agents/cg-roadmap.agent.md`, `.github/agents/cg-roadmap-view.agent.md`, `.github/agents/cg-release-scanner.agent.md`, `.github/agents/cg-learnings-researcher.agent.md`
- **Details**:
  - Keep roadmap commands allowed to parse `roadmap.json` when required.
  - Prefer structured fields, filenames, manifests, summaries, or selected solution categories over whole-directory scans.
  - Add expansion rationale where full artifact reads are essential.
- **Tests**:
  - Prompt/docs tests that cover key contract phrases if existing tests have suitable hooks.

## Phase 3: Documentation and Evidence

### 5. Document the progressive-disclosure policy
- **Files**: `docs/workflow.md`, `docs/reference.md`, possibly `.github/shared/context-loading.contract.md`
- **Details**:
  - Document Stage 0-4 behavior and the expectation that workflows start minimal, use budgeted Brain query, and summarize command output.
  - Avoid implying all `.cg-docs/` or full context files should be loaded during ordinary work.

### 6. Validate, review, and compound
- **Files**: `.cg-docs/work-reports/*`, `.cg-docs/reviews/*`, `.cg-docs/solutions/*`, `roadmap.json`
- **Details**:
  - Run targeted Python audit tests, token audit, prompt-tool checks, full safe runner, review/verify, and `/cg-compound`.
  - Mark plan and roadmap done only after evidence passes.

## Testing Strategy

- `python3 -m pytest scripts/tests/test_audit_context.py -q`
- `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q`
- `python3 scripts/cg_audit_context.py --root . --output-dir .cg-docs/cost --format both --recommendations`
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"`
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"`
- `git diff --check`

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Over-slimming removes needed context for maintenance workflows. | Keep maintenance full reads when required, but add explicit expansion rationale and field narrowing. |
| Audit false positives cause churn. | Prefer targeted classifier/test improvements and docs-only classifications over broad prompt rewrites. |
| Prompt semantics drift. | Keep edits textual and scoped; rely on prompt-tool and safe-runner validation. |
| Token-saving claims are overstated. | State only bounded/progressive-disclosure behavior unless same-probe measurements exist. |

## Out of Scope

- Cross-agent packaging adapters.
- Optional retrieval backends.
- Snapshot or external-research modes.
- Replacing roadmap, issue, setup, release, or compound semantics.
- Claims of measured savings without a Phase 1.6 regression/dashboard probe.

## Completion Contract

### Outcome

Phase 1.4 is complete when ordinary/default prompt, agent, skill, and documentation paths follow the staged context-loading contract, maintenance broad reads are narrowed or explicitly justified, and tests/audit evidence guard against regression.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Audit tests cover broad-read detection and justified expansion wording. | `scripts/tests/test_audit_context.py` | yes |
| V2 | 2 | Ordinary/default prompt wording no longer encourages unqualified broad context reads. | token audit and diff review | yes |
| V3 | 2 | Maintenance reads preserve command semantics while adding rationale/narrowing. | prompt/docs review | yes |
| V4 | 3 | Docs describe progressive-disclosure policy without implying token-saving measurements. | docs diff | yes |
| V5 | final | Prompt-tool checks pass. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` | yes |
| V6 | final | Full safe runner passes. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | all | No external services, adapters, backends, or snapshot tooling. | Diff review. |
| C2 | all | No unsafe Pester instructions. | Safe runner and grep. |
| C3 | all | No unmeasured token-saving/cost-saving claim. | Docs/review. |
| C4 | all | Existing command semantics remain intact. | Prompt-tool and safe runner checks. |
| C5 | all | Roadmap writes remain scoped and evidence-backed. | Roadmap/status checks. |

### Boundaries

- Allowed: prompt/agent/skill/doc wording, audit tests/classifier refinements, evidence artifacts.
- Out of scope: architecture changes, new retrieval systems, cross-agent packaging, live IDE integrations, GitHub mutations.

### Iteration Policy

1. Fix ordinary-workflow broad reads first.
2. For maintenance workflows, narrow to structured fields/headings where possible.
3. If a full read is necessary, require a context-expansion rationale and keep output summaries compact.

### Blocked-Stop Conditions

- A wording change would alter roadmap/issue/setup/release behavior beyond Phase 1.4 scope.
- Required tests or audit checks fail and cannot be fixed within scope.
- A review finding says the cleanup risks model-governance, Pester safety, or roadmap integrity.
