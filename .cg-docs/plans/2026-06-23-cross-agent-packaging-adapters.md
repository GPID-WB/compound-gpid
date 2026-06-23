---
date: 2026-06-23
title: "Cross-Agent Packaging Adapters"
status: completed
completed-date: 2026-06-23
execution-report: .cg-docs/work-reports/2026-06-23-cross-agent-packaging-adapters.md
scope: "Standard"
brainstorm: null
language: "Markdown/Python/PowerShell"
estimated-effort: "medium"
deviation-policy: "autonomous"
tags: [cross-agent, adapters, codex, claude, packaging, compatibility]
phases: 3
completed-phases: [1, 2, 3]
roadmap-features:
  - token-efficiency-portability-expansion/phase-2-1-cross-agent-packaging-adapters
---

# Plan: Cross-Agent Packaging Adapters

## Objective

Complete Phase 2.1 by packaging the existing Codex / Claude Code compatibility
adapter behavior into reusable, version-controlled adapter files that consumer
projects can opt into without changing GitHub Copilot prompt behavior.

## Context

The repository already has a root `AGENTS.md` compatibility adapter for this
repo, and docs explain that `AGENTS.md` is not part of the GitHub Copilot
context chain. There is no reusable adapter package for consumer projects yet.
Phase 2.1 should fill that gap while keeping `.github/` prompt, skill, agent,
instruction, and shared assets Copilot-oriented.

Brain findings:

- Codex and Claude Code need a root adapter to execute Copilot-oriented
  `/cg-*` prompts; keep compatibility behavior outside `.github/` assets --
  source:
  `.cg-docs/solutions/environment-issues/2026-06-06-codex-claude-code-cg-prompt-dispatch-adapter.md`.
- Compatibility work should preserve existing link/update behavior and avoid
  breaking Copilot managed files -- source:
  `.cg-docs/plans/2026-06-22-workflow-token-baseline.md`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Provide reusable Codex and Claude Code adapter files for projects that want cross-agent support. | roadmap Phase 2.1 |
| R2 | Keep adapters opt-in; do not add them to `cg-link` managed directories or generated Copilot instructions. | docs/context-files.md |
| R3 | Preserve `/cg-*` prompt dispatch, `cg-skill-*` loading, `@cg-*` agent-spec emulation, and tool mapping rules from root `AGENTS.md`. | existing adapter |
| R4 | Document install/copy guidance and the distinction from normal GitHub Copilot installation. | docs |
| R5 | Add regression tests so packaged adapters cannot drift from the core dispatch contract. | project testing pattern |
| R6 | Do not implement optional retrieval backends, external services, or snapshot/external research modes. | roadmap sequencing |

## Implementation Steps

## Phase 1: Adapter Package

### 1. Add reusable adapter files

- **Requirements**: R1, R2, R3, R6
- **Files**:
  - `adapters/README.md`
  - `adapters/codex/AGENTS.md`
  - `adapters/claude/CLAUDE.md`
  - `adapters/manifest.json`
- **Details**:
  - Package Codex and Claude Code root-level adapter files as source assets.
  - State that files are optional, copied into the consumer repo root, and not
    read by GitHub Copilot.
  - Keep dispatch/tool-mapping content aligned with root `AGENTS.md`.
  - Include a manifest with adapter IDs, target filenames, and source version.
- **Test Scenarios**: adapter package exists; both adapter files include prompt,
  skill, agent, tool mapping, and Copilot non-interference rules.
- **Tests**: `python3 -m pytest scripts/tests/test_agent_adapters.py -q`.
- **Acceptance criteria**: source package exists and does not require link/update
  behavior changes.

## Phase 2: Documentation and Tests

### 2. Add discoverability and drift tests

- **Requirements**: R4, R5
- **Files**:
  - `scripts/tests/test_agent_adapters.py`
  - `docs/context-files.md`
  - `docs/installation.md`
  - `docs/reference.md`
- **Details**:
  - Add Python tests that compare required adapter contract phrases across root
    `AGENTS.md`, packaged Codex adapter, and packaged Claude adapter.
  - Document copy guidance and make clear that normal Copilot users do not need
    these adapters.
  - Avoid adding new installer/linker commands in this phase.
- **Acceptance criteria**: docs expose the package without implying automatic
  installation or changing Copilot behavior.

## Phase 3: Evidence and Roadmap Closure

### 3. Validate, review, compound, and close roadmap status

- **Requirements**: R5, R6
- **Files**:
  - `.cg-docs/work-reports/2026-06-23-cross-agent-packaging-adapters.md`
  - `.cg-docs/reviews/*cross-agent-packaging-adapters*`
  - `.cg-docs/solutions/environment-issues/*cross-agent-packaging-adapters*`
  - `roadmap.json`
- **Details**:
  - Run focused adapter tests, prompt/docs tests, and full safe runner.
  - Record implementation and verify review evidence.
  - Add a solution note only after validation passes.
  - Mark Phase 2.1 done and link this plan.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_agent_adapters.py -q`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"`
  - `git diff --check`

## Testing Strategy

Use focused Python tests for adapter file shape and root-package drift. Use the
safe Pester runner for docs/prompt regressions and the full gate before commit.

## Documentation Checklist

- `adapters/README.md` explains when to use the package.
- `docs/context-files.md` documents adapter lifecycle.
- `docs/installation.md` notes optional cross-agent adapter copy steps.
- `docs/reference.md` lists adapter package location.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Users think adapters are required for Copilot | Repeat that GitHub Copilot ignores root agent adapters. |
| Packaged adapters drift from root `AGENTS.md` | Add required-contract tests. |
| Scope expands into installers or external services | Keep this phase source-package only. |

## Out of Scope

- Automatic `cg-link` installation of adapters.
- Optional retrieval backends, vector search, external research, or snapshots.
- Model-provider-specific runtime integrations beyond adapter text.

## Completion Contract

### Outcome

Phase 2.1 is complete when reusable Codex and Claude Code adapter package files
exist, their contract is tested, docs explain opt-in usage, and roadmap/evidence
artifacts are committed.

### Verification Surface

| ID | Evidence Required | Command/Artifact | Required |
|----|-------------------|------------------|----------|
| V1 | Adapter package files exist with required contract sections. | `python3 -m pytest scripts/tests/test_agent_adapters.py -q` | yes |
| V2 | Prompt/docs checks pass. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` | yes |
| V3 | Full safe runner passes. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |
| V4 | Roadmap feature is done and linked to this plan. | `roadmap.json` | yes |

### Constraints

| ID | Constraint | Check |
|----|------------|-------|
| C1 | Adapters remain opt-in and root-level, not Copilot-managed. | docs and diff review |
| C2 | No retrieval backend, external research, or snapshot implementation. | diff review |
| C3 | Safe Pester runner only. | command evidence |

### Blocked-Stop Conditions

- Adapter package would require changing `.github/` prompt semantics for
  Copilot users.
- Full safe runner fails after scoped fixes.
