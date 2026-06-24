---
date: 2026-06-23
title: "Command Output Summarization Wrappers"
status: completed
completed-date: 2026-06-23
completed-phases: [1, 2, 3, 4]
scope: "Deep"
brainstorm: null
language: "Python/Shell/Markdown"
estimated-effort: "large"
deviation-policy: "autonomous"
tags: [token-efficiency, command-output, summaries, validation, git]
phases: 4
roadmap-features:
  - token-efficiency-core-system/phase-1-3-command-output-summaries
---

# Plan: Command Output Summarization Wrappers

## Objective

Implement Phase 1.3 by adding native command-output summarization wrappers that keep raw noisy output on disk and return compact structured summaries for tests, diffs, logs, trees, and diagnostics without changing existing validation semantics.

## Context

Phase 1.1 made command-output and summary-size fields explicit but `not_observed`. Phase 1.2 added bounded Knowledge Brain retrieval. Phase 1.3 adds local wrappers that summarize common noisy command surfaces and store full output under `.cg-docs/token/outputs/` with retention/redaction rules.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Add `cg-test-summary` for Pester/Pytest/R/Stata validation summaries, building on `tests/last-run.json`. | roadmap strategy |
| R2 | Add `cg-diff-summary` for file list, hunks by file, risk tags, and path to full diff. | roadmap strategy |
| R3 | Add `cg-log-summary` for branch-local commits, first-parent counts, and notable files. | roadmap strategy |
| R4 | Add `cg-tree-summary` for bounded repository/file-tree summaries. | roadmap strategy |
| R5 | Add `cg-problems-summary` for diagnostics when a problems/JSON input is available; degrade gracefully otherwise. | roadmap strategy |
| R6 | Store full raw outputs or source references under `.cg-docs/token/outputs/` with redaction and retention notes. | roadmap strategy |
| R7 | Use local stdlib tooling only; no external services or production writes. | objective hard stop |
| R8 | Preserve Pester safety: wrappers may read `tests/last-run.json` but must not run unsafe `Invoke-Pester` commands. | project instructions |
| R9 | Add tests and docs; do not claim token savings without measured same-probe evidence. | objective hard stop |

## Phase 1: Summary Core

### 1. Add a shared summary utility module
- **Files**: `scripts/cg_summary.py`, `scripts/tests/test_cg_summary.py`
- **Details**:
  - Implement subcommands: `test`, `diff`, `log`, `tree`, and `problems`.
  - Write bounded JSON/Markdown summaries to stdout.
  - Write raw output artifacts under `.cg-docs/token/outputs/YYYYMMDD-HHMMSS-<kind>/`.
  - Redact common secret-looking values in captured raw text.
  - Keep functions testable with injected root paths and fixture input files.
- **Tests**:
  - Summary functions produce valid JSON and bounded Markdown.
  - Raw output paths are written under `.cg-docs/token/outputs/`.
  - Redaction removes obvious `TOKEN=...`, `password=...`, and `api_key=...` values.

### 2. Implement test, diff, and log summaries
- **Files**: `scripts/cg_summary.py`, `scripts/tests/test_cg_summary.py`
- **Details**:
  - `test` reads `tests/last-run.json` by default and returns pass/fail counts, filtered files, failure summaries, and raw artifact path.
  - `diff` runs `git diff --stat` and `git diff --name-only`, writes full `git diff` to an artifact, returns changed files and risk tags.
  - `log` uses `git merge-base` and `git log --first-parent` where possible, returns branch-local commits and notable files.
- **Tests**:
  - Fixture `last-run.json` summaries.
  - Temp git repo diff/log summaries.

## Phase 2: Tree, Problems, and Wrappers

### 3. Implement tree and problems summaries
- **Files**: `scripts/cg_summary.py`, `scripts/tests/test_cg_summary.py`
- **Details**:
  - `tree` returns bounded file tree summaries with excludes for `.git`, caches, generated token outputs, and common dependency folders.
  - `problems` reads an optional JSON/text diagnostics file and summarizes severity counts; if no input is given, return `available: false` with setup guidance.
- **Tests**:
  - Tree excludes noisy directories and respects max entries.
  - Problems handles missing, JSON, and text input.

### 4. Add thin bin wrappers
- **Files**: `bin/cg-test-summary`, `bin/cg-diff-summary`, `bin/cg-log-summary`, `bin/cg-tree-summary`, `bin/cg-problems-summary`, optional `.cmd` wrappers if needed.
- **Details**:
  - Shell wrappers call `python3 scripts/cg_summary.py <subcommand> "$@"`.
  - Keep Windows `.cmd` wrappers optional unless existing parity tests require them.
- **Tests**:
  - Static or subprocess tests prove wrappers exist and reference the expected subcommand.

## Phase 3: Docs, Prompt Integration, and Validation

### 5. Document wrapper usage
- **Files**: `docs/reference.md`, `docs/workflow.md`, `.cg-docs/token/outputs/.gitkeep`
- **Details**:
  - Document wrapper purpose, output directory, redaction policy, and that wrappers summarize existing command results rather than replacing validation.
  - Keep `/cg-work` and `/cg-review` semantics unchanged; mention wrappers as preferred bounded-output helpers where command output would otherwise be large.
- **Tests**:
  - Prompt/docs tests assert wrapper names and output directory are documented if practical.

### 6. Validate and record evidence
- **Files**: `.cg-docs/work-reports/*`, `.cg-docs/reviews/*`, `.cg-docs/solutions/*`, `roadmap.json`
- **Details**:
  - Run Python tests, representative wrapper smoke commands, safe runner, review/verify, and `/cg-compound`.
  - Link/mark roadmap through the roadmap manager contract after evidence passes.

## Testing Strategy

- `python3 -m pytest scripts/tests/test_cg_summary.py -q`
- `python3 -m pytest scripts/tests scripts/brain/tests scripts/team_brain/tests -q`
- Representative wrappers:
  - `python3 scripts/cg_summary.py test --root . --format json`
  - `python3 scripts/cg_summary.py diff --root . --format md`
  - `python3 scripts/cg_summary.py log --root . --format json`
  - `python3 scripts/cg_summary.py tree --root . --max-entries 80 --format md`
  - `python3 scripts/cg_summary.py problems --root . --format json`
- `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"`

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Wrapper runs unsafe tests. | `cg-test-summary` reads `tests/last-run.json`; it does not invoke Pester. |
| Raw artifacts leak secrets. | Redact common secret patterns before writing captured raw text. |
| Git summaries fail outside git repos. | Return clear unavailable summaries. |
| Output wrappers become another noisy artifact source. | Keep bounded stdout and store raw files under `.cg-docs/token/outputs/`. |

## Out of Scope

- Replacing `tests/Run-Tests.ps1` or changing validation semantics.
- VS Code API integration for live Problems panels.
- CI/GitHub API calls.
- Token-saving claims without measured before/after comparisons.

## Completion Contract

### Outcome

Phase 1.3 is complete when local wrappers can emit compact summaries for tests, diffs, logs, trees, and optional diagnostics, raw output artifacts are stored under `.cg-docs/token/outputs/`, and validation proves wrappers are bounded, redacted, and compatible with existing workflows.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Summary core writes bounded JSON/Markdown and redacted raw artifacts. | `scripts/tests/test_cg_summary.py` | yes |
| V2 | 1 | Test/diff/log summaries work with fixtures/temp repos. | `scripts/tests/test_cg_summary.py` | yes |
| V3 | 2 | Tree/problems summaries handle bounded and unavailable cases. | `scripts/tests/test_cg_summary.py` | yes |
| V4 | 2 | Bin wrappers exist and call expected subcommands. | wrapper tests/static inspection | yes |
| V5 | final | Representative wrapper smoke commands pass. | command outputs and artifact paths | yes |
| V6 | final | Safe runner passes. | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |
| V7 | final | No unsafe Pester, external service, or token-saving claim is introduced. | diff/review evidence | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | all | `cg-test-summary` reads existing artifacts; it does not run Pester. | Code/tests. |
| C2 | all | Raw artifacts stay under `.cg-docs/token/outputs/`. | Tests and smoke output. |
| C3 | all | Common secret-like values are redacted. | Tests. |
| C4 | all | No external services or GitHub mutation. | Diff review. |
| C5 | all | Existing validation and review semantics are preserved. | Safe runner and docs review. |

### Boundaries

- Allowed: local stdlib summary script, thin wrappers, tests, docs, evidence artifacts.
- Out of scope: live IDE diagnostics APIs, CI APIs, replacing tests, optional retrieval backends.

### Iteration Policy

1. Prefer bounded summaries over full output in stdout.
2. If a summary source is unavailable, return an explicit unavailable status instead of failing noisily.
3. If a raw artifact cannot be written, fail clearly rather than pretending output was captured.

### Blocked-Stop Conditions

- Wrapper needs external services or production/GitHub mutation.
- Wrapper would run unsafe Pester commands.
- Required tests or safe runner fail and cannot be fixed within scope.
