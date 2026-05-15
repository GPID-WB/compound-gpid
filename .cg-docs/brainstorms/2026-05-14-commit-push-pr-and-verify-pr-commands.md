---
date: 2026-05-14
title: "Commit-push-PR and verify-PR commands"
status: decided
scope: "Standard"
chosen-approach: "Two standalone prompts"
tags: [workflow, git, pr, ci, gh-cli, commit, verification, agents]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Commit-Push-PR and Verify-PR Commands

## Context

When a PR is submitted and CI checks fail, there's no automated way to diagnose
and fix the failures within the plugin workflow. Additionally, the commit→push→PR
flow is manual and doesn't leverage plan files or logical commit splitting.

Two new plugin-level commands to close this gap:
- `/cg-commit-push-pr` — Logical staging, conventional commits, push, open PR.
- `/cg-verify-pr` — Check CI status, auto-fix failures, push fixes.

Both are project-agnostic (distributed to consumer projects, not compound-gpid-internal).

## Requirements

### `/cg-commit-push-pr`
1. Always propose splitting changes into multiple logical commits (code vs tests vs docs).
2. Generate conventional commit messages from the diff.
3. PR description pulled from `.cg-docs/plans/` files added since the branch point.
   - If multiple plans were added, aggregate them into the PR body.
4. `gh` CLI recommended but not required — degrades gracefully (commit + push, then instruct user to open PR manually with install instructions for `gh`).

### `/cg-verify-pr`
5. Default mode: auto-fix (dispatch agents → commit fix → push → re-check).
6. `--propose` flag: observe-only mode (diagnose and present findings, no auto-commit).
7. Classify CI failures by type and dispatch appropriate agents:
   - Lint/type errors → `@cg-fix-problems`
   - Test failures → `@cg-testing` / `@cg-fixbug`
   - Build errors → `@cg-code-quality`
8. Two-round retry cap. After 2 failed fix attempts, surface the problem to the user.
9. Cross-platform awareness: if checks pass on one platform but fail on another, fix what's inferable from CI logs, notify user that the branch is not deployment-ready until both platforms pass.
10. If merge conflicts arise during the fix loop: attempt easy/logical rebases automatically; surface complex conflicts interactively.
11. `gh` CLI required for status checking — graceful degradation with install instructions if missing.

### Out of Scope (v1)
- Auto-merge after checks pass
- Multi-repo support
- PR reviewers/labels assignment
- Integration with `/cg-review` (full review agent suite before opening PR)
- Squash/rebase strategy selection at PR time

## Approaches Considered

### Approach 1: Two Standalone Prompts (CHOSEN)
Both commands as self-contained `.prompt.md` files. `/cg-commit-push-pr` handles
the interactive commit flow. `/cg-verify-pr` handles CI log parsing, failure
classification, agent dispatch, and the fix loop.

- Pros: Simple structure, self-contained, easy to test independently, consistent with existing prompts.
- Cons: `/cg-verify-pr` has complex orchestration logic that may be heavy for a single prompt file.
- Effort: Medium.

### Approach 2: Prompt + Dedicated Agent
Thin `/cg-verify-pr` prompt + `@cg-ci-fixer` agent for the fix logic.

- Pros: Separation of concerns, reusable agent.
- Cons: More files, over-engineering for v1.
- Effort: Medium-large.

### Approach 3: Single Unified Command with Modes
One `/cg-ship` command with flags for different behaviors.

- Pros: Single entry point.
- Cons: Conflates distinct user intents, flag-heavy, harder to document.
- Effort: Medium.

## Decision

Approach 1: Two standalone prompts. Simple, testable, consistent with existing
plugin patterns. Can refactor into prompt + agent later if `/cg-verify-pr` grows
unwieldy.

## Next Steps

1. Design `/cg-commit-push-pr` prompt structure (Step 0 bearings, diff analysis, commit splitting heuristic, plan detection, `gh` integration).
2. Design `/cg-verify-pr` prompt structure (Step 0, `gh pr checks` parsing, failure classification taxonomy, agent dispatch rules, fix loop with 2-round cap, cross-platform notification logic).
3. Define the commit-splitting heuristic (start simple: group by file type — code vs tests vs docs vs config).
4. Define plan-detection logic (find `.cg-docs/plans/` files added since `git merge-base HEAD main`).
5. Add tests for both prompts in `tests/prompt-tools.Tests.ps1` or new dedicated test files.
6. Register both commands in `docs/reference.md`.
