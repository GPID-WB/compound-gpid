---
date: 2026-05-14
title: "Two new workflow commands: /cg-commit-push-pr and /cg-verify-pr"
status: completed
completed-date: 2026-05-14
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-14-commit-push-pr-and-verify-pr-commands.md"
language: "both"
estimated-effort: "medium"
tags: [workflow, git, pr, ci, gh-cli, commit, verification, agents, prompt]
phases: 3
completed-phases: [1, 2, 3]
---

# Plan: /cg-commit-push-pr and /cg-verify-pr Commands

## Objective

Create two new plugin-level `.prompt.md` commands distributed to all consumer projects:
1. `/cg-commit-push-pr` — Analyze changes, propose logical commit splits, generate conventional commit messages, push, and open a PR with plan-driven description.
2. `/cg-verify-pr` — Check CI status on the current branch's PR, classify failures, auto-dispatch agents to fix, and push fixes (2-round cap).

## Context

The brainstorm decided on Approach 1 (two standalone prompts). Both commands are
project-agnostic — they must work in any consumer project, not just compound-gpid.
The `gh` CLI is recommended but not required; commands degrade gracefully. The PR
verification pipeline (CI infrastructure with E2E smoke tests) is already done —
these commands sit on top of that infrastructure.

## Requirements

| ID  | Requirement                                                              | Source     |
|-----|--------------------------------------------------------------------------|------------|
| R1  | Always propose splitting changes into multiple logical commits           | brainstorm |
| R2  | Generate conventional commit messages from the diff                      | brainstorm |
| R3  | PR description pulled from `.cg-docs/plans/` added since branch point   | brainstorm |
| R4  | Graceful degradation when `gh` CLI is missing (with install instructions)| brainstorm |
| R5  | Default auto-fix mode for `/cg-verify-pr`                               | brainstorm |
| R6  | `--propose` flag for observe-only mode                                   | brainstorm |
| R7  | Classify CI failures by type and dispatch appropriate agents             | brainstorm |
| R8  | Two-round retry cap                                                      | brainstorm |
| R9  | Cross-platform awareness (notify if one platform fails)                  | brainstorm |
| R10 | Attempt easy rebases; surface complex conflicts interactively            | brainstorm |
| R11 | Project-agnostic — no compound-gpid internals                            | brainstorm |

## Implementation Steps

## Phase 1: `/cg-commit-push-pr` prompt

### 1. Create `cg-commit-push-pr.prompt.md`

- **Requirements**: R1, R2, R3, R4, R11
- **Files**: `.github/prompts/cg-commit-push-pr.prompt.md`
- **Details**:

  **Frontmatter**:
  ```yaml
  ---
  description: "Stage changes into logical commits, push, and open a PR with plan-driven description."
  model: Claude Sonnet 4.6 (copilot)
  ---
  ```

  **File Permissions**:
  - **READ**: Any file in the workspace.
  - **EXECUTE**: `git add`, `git commit`, `git push`, `gh pr create`.
  - **NEVER**: Modify `.cg-docs/` files, plan files, or `roadmap.json` directly.

  **Prompt structure**:

  - **Step 0: Get Bearings** — Standard pattern (read charter, local config, context).

  - **Step 1: Pre-flight Checks**
    - Run `git status` to inventory staged/unstaged/untracked changes.
    - If no changes: "Nothing to commit. Working tree is clean." — halt.
    - Run `git branch --show-current` to get current branch.
    - Detect the default branch (`git symbolic-ref refs/remotes/origin/HEAD --short 2>$null`; fallback to `main`/`master`).
    - If on the default branch: warn "You're on the default branch. Create a feature branch first (`git checkout -b feat/<name>`) or continue anyway?"
    - Check `gh` availability: `Get-Command gh -ErrorAction SilentlyContinue` (PowerShell) / `command -v gh` (bash context). If missing:
      > "`gh` CLI not found. Install it for full PR creation support:
      > - Windows: `winget install GitHub.cli`
      > - macOS: `brew install gh`
      > - Linux: see https://cli.github.com/
      >
      > Continuing without PR creation — will commit and push only."

  - **Step 2: Analyze Changes and Propose Commits**
    - Run `git status --short` to inventory all changed files (staged, unstaged, and untracked). Use `git diff HEAD --stat` for the combined staged+unstaged view relative to HEAD.
    - Classify files into groups using heuristics:
      - **Code**: `*.R`, `*.py`, `*.do`, `*.ado`, `*.ps1`, `*.sh`, `*.ts`, `*.js` (excluding test dirs)
      - **Tests**: files in `tests/`, `test/`, `**/test_*`, `**/*.Tests.*`, `**/test-*`
      - **Docs**: `*.md`, `docs/`, `README*`, `CONTRIBUTING*`, `*.Rd`
      - **Config**: `*.json`, `*.yaml`, `*.yml`, `*.toml`, `renv.lock`, `poetry.lock`, `uv.lock`, `.github/workflows/`
      - **Plans/Knowledge**: `.cg-docs/`
    - Present proposed commit groups:
      > "I see changes in N files. Here's my proposed commit structure:
      >
      > 1. **feat(core): <description>** — `file1.R`, `file2.R` (code changes)
      > 2. **test(core): <description>** — `tests/test-foo.R` (test additions)
      > 3. **docs: <description>** — `README.md`, `docs/reference.md`
      >
      > Adjust grouping? Or accept and I'll generate full commit messages."
    - Wait for user confirmation or adjustments.

  - **Step 3: Generate Commit Messages**
    - For each group, read the actual diff (`git diff <files>`) and generate a conventional commit message:
      - Format: `type(scope): description` (max 72 chars for subject)
      - Body: bullet list of key changes (if diff is non-trivial)
    - Present all messages for review before committing.
    - Read `compound-gpid.md` to infer commit-type taxonomy if documented.

  - **Step 4: Execute Commits**
    - For each confirmed group:
      1. `git add <files>`
      2. `git commit -m "<message>"` (with body if provided)
    - If any commit fails, report error and halt.

  - **Step 5: Push**
    - Run `git push origin <branch>` (with `--set-upstream` if needed).
    - If push fails (rejected/non-fast-forward): report and suggest `git pull --rebase` or `git push --force-with-lease` (ask user, never force-push without consent).

  - **Step 6: Open PR** (skip if `gh` unavailable)
    - Detect plans added since branch point:
      ```
      git merge-base HEAD <default-branch>
      git diff --name-only <merge-base>..HEAD -- .cg-docs/plans/
      ```
    - If plan(s) found: read their `## Objective` and `## Requirements` sections to compose PR body.
    - If multiple plans: aggregate under sections.
    - If no plans: generate PR body from commit messages.
    - PR title: derive from the branch name or primary commit subject.
    - Run `gh pr create --title "<title>" --body "<body>"`.
    - Report PR URL on success.
    - If `gh pr create` fails: show the error and provide the manual command.

  - **Step 7: Handoff**
    > "PR opened: <URL>
    >
    > **Next steps:**
    > 1. `/cg-verify-pr` — Check CI status and auto-fix failures
    > 2. Done for now — wait for review"

- **Test Scenarios**:
  - ✅ Happy path: multiple files across code/tests/docs → 3 logical commits → push → PR
  - ✅ Single-group: all changes are code → 1 commit proposed
  - 🛑 No `gh`: commits and pushes, provides manual PR instructions
  - 🛑 On default branch: warns user
  - 🛑 No changes: halts immediately
  - ❌ Push rejected: reports and suggests resolution
  - ❌ `gh pr create` fails: shows error and manual command
- **Acceptance criteria**: Prompt file exists, follows standard structure, handles all branches. Includes inline commit-splitting heuristic covering R, Python, Stata, PowerShell, bash, JS/TS file types with deterministic path-based grouping and interactive override.

## Phase 2: `/cg-verify-pr` prompt

### 2. Create `cg-verify-pr.prompt.md`

- **Requirements**: R5, R6, R7, R8, R9, R10, R4, R11
- **Files**: `.github/prompts/cg-verify-pr.prompt.md`
- **Details**:

  **Frontmatter**:
  ```yaml
  ---
  description: "Check CI status on current PR, classify failures, and auto-fix with review agents. Use --propose for observe-only mode."
  model: Claude Sonnet 4.6 (copilot)
  ---
  ```

  **File Permissions**:
  - **READ**: Any file in the workspace.
  - **MODIFY**: Source and test files related to CI fix (auto-fix mode only).
  - **NEVER**: Modify `.cg-docs/` files, plan files, or `roadmap.json` directly.
  - **`--propose` mode**: READ-only. No file creation, modification, git commits, or pushes.

  **Prompt structure**:

  - **Step 0: Get Bearings** — Standard pattern.

  - **Step 0.6: Parse Invocation Flags** (no prior-work scan — this command is stateless)
    - Check user input for `--propose` flag.
    - Default mode: auto-fix.
    - `--propose` mode: diagnose and report only, no commits or pushes.

  - **Step 1: Pre-flight Checks**
    - Check `gh` availability. If missing:
      > "`gh` CLI is required for `/cg-verify-pr`. Install it:
      > - Windows: `winget install GitHub.cli`
      > - macOS: `brew install gh`
      > - Linux: see https://cli.github.com/
      >
      > Cannot proceed without `gh`."
      Halt.
    - Check `gh auth status` — if not authenticated, instruct user and halt.
    - Run `git branch --show-current` to get current branch.
    - Run `gh pr view --json number,title,state,statusCheckRollup` to find the PR for this branch.
    - If no PR exists: "No open PR found for branch `<branch>`. Run `/cg-commit-push-pr` first." — halt.

  - **Step 2: Check CI Status**
    - Parse `statusCheckRollup` from the PR view JSON.
    - Classify overall status:
      - **All passing**: "All CI checks are passing. Nothing to fix." — halt with success message.
      - **Pending**: "CI checks are still running. Try again in a few minutes." — halt.
      - **Failing**: Proceed to Step 3.
    - List failing checks with their names and conclusions.

  - **Step 3: Fetch and Classify Failure Logs**
    - Extract run IDs: for each failing check name from `statusCheckRollup`, run `gh run list --branch <branch> --workflow <workflow-name> --limit 1 --json databaseId` to resolve the integer run-id.
    - For each failing run, fetch logs: `gh run view <run-id> --log-failed`.
    - Classify each failure into categories:
      - **Lint/Type errors**: Pattern matches for linting tools, type-check output (eslint, mypy, lintr, pylint, styler)
      - **Test failures**: Pattern matches for test runner output (pytest, testthat, Pester, Stata assert)
      - **Build errors**: Compilation failures, missing dependencies, import errors
      - **Platform-specific**: Failure on one OS but not another
      - **Unknown**: Cannot classify
    - Present classification:
      > "CI failures classified:
      > - 🧪 Test failures (2): `tests/test-foo.R`, `tests/bar.Tests.ps1`
      > - 🔧 Lint errors (1): `src/module.py`
      > - 🖥️ Platform-specific (1): macOS only — `scripts/link.sh`
      >
      > [Auto-fix mode / Propose mode]: <action description>"

  - **Step 4: Fix Round** (auto-fix mode only; in `--propose` mode, skip to Step 7)

    This step is a **one-shot fix round**, not a blocking loop. The prompt cannot wait for CI to re-run (GitHub Actions takes minutes; Copilot Chat completes a single invocation). Each invocation of `/cg-verify-pr` performs one fix round. State is tracked via `fix(ci):` commit messages on the branch.

    **Do NOT use `gh pr checks --watch`** — it blocks the terminal indefinitely and crashes the agent session.

    - **Round detection**: Count `fix(ci):` commits since the branch point (`git log --oneline --grep="fix(ci):" <merge-base>..HEAD | Measure-Object`). If ≥ 2:
      > "**2 fix rounds already attempted.** Remaining CI failures require manual intervention.
      > Review the logs: `gh run view <run-id> --log-failed`"
      Halt.

    - **Pre-push rebase check** (R10):
      1. `git fetch origin <default-branch>`
      2. Check if main has diverged: `git merge-base --is-ancestor origin/<default-branch> HEAD`
      3. If diverged, attempt `git rebase origin/<default-branch>`.
         - Clean rebase: proceed.
         - Simple conflicts (single file, < 10 lines): attempt resolution, show user, ask for confirmation.
         - Complex conflicts: halt with conflict details for interactive resolution.

    - **Apply fixes**:
      1. For lint/type errors: dispatch `@cg-fix-problems` with the relevant files and diagnostics.
      2. For test failures: read the failure output, identify root cause, apply targeted fix. If unclear, dispatch `@cg-testing` for analysis.
      3. For build errors: dispatch `@cg-code-quality` for dependency/import resolution.
      4. Commit fixes: `git add <fixed-files>; git commit -m "fix(ci): <description>"`
      5. Push: `git push origin <branch>` (use `--force-with-lease` only if a rebase was done; never `--force`).

    - **Post-push notification**:
      > "Fixes pushed (round N/2). CI will re-run.
      > Re-invoke `/cg-verify-pr` after checks complete to verify or apply a second fix round."

  - **Step 5: Cross-Platform Notification**
    - After any fix round, if failures are platform-specific:
      > "⚠️ **Platform-specific failure**: Checks pass on <platform-A> but fail on <platform-B>.
      > The fix applied is based on CI log inference — cannot test locally on <platform-B>.
      > **This branch is NOT deployment-ready** until both platforms pass.
      >
      > Suggested: ask a team member with <platform-B> access to verify, or wait for next CI run."

  - **Step 6: Summary and Handoff**
    - **Auto-fix mode**:
      > "✅ CI verification complete.
      > - Rounds used: N/2
      > - Fixes applied: N commits
      > - Status: [all passing / partial — see above]
      >
      > PR: <URL>"
    - **Propose mode**:
      > "CI diagnosis complete. Findings:
      > - <classified failures with suggested fixes>
      >
      > Run `/cg-verify-pr` (without `--propose`) to auto-fix, or apply manually."

- **Test Scenarios**:
  - ✅ Happy path: checks failing → fix round 1 resolves → all green
  - ✅ Two rounds needed: first fix introduces new issue → second fix resolves
  - ✅ Already passing: immediate success message
  - ✅ Propose mode: diagnoses without modifying anything
  - 🛑 No `gh`: halts with install instructions
  - 🛑 No PR: halts with guidance to `/cg-commit-push-pr`
  - 🛑 Pending checks: halts with retry suggestion
  - 🛑 Platform-specific: applies fix + warning about deployment readiness
  - ❌ 2 rounds exhausted: surfaces remaining failures
  - ❌ Merge conflict (complex): halts for interactive resolution
- **Acceptance criteria**: Prompt handles all modes and branches; `--propose` never modifies files.

## Phase 3: Tests and registration

### 3. Add Pester tests for both prompts

- **Requirements**: R1–R11 (structural coverage)
- **Files**: `tests/prompt-tools.Tests.ps1` (append new Describe blocks), `tests/model-assignments.Tests.ps1` (update sentinel)
- **Details**:
  - Test `cg-commit-push-pr.prompt.md` exists and has correct frontmatter.
  - Test it contains key structural elements: Step 0 bearings, File Permissions block, commit-splitting heuristic, `gh` degradation logic, plan-detection logic, conventional commit format.
  - Test `cg-verify-pr.prompt.md` exists and has correct frontmatter.
  - Test it contains: File Permissions block, `--propose` flag parsing, failure classification taxonomy, agent dispatch rules, 2-round cap logic, cross-platform notification, rebase handling, explicit `--watch` prohibition.
  - R11 project-agnostic assertion: assert neither prompt contains internal install paths like `$env:USERPROFILE\.compound-gpid` or `.compound-gpid/` (the global install directory). Note: `compound-gpid.md` references in Step 0 are expected and NOT flagged.
  - Update `tests/model-assignments.Tests.ps1` sentinel from 19 to 21 prompt files. Add model-tier comments for both new prompts in the same file (matching existing comment style).
- **Test Scenarios**:
  - ✅ Frontmatter model is Sonnet 4.6
  - ✅ Both prompts contain Step 0 bearings
  - ✅ Both prompts contain File Permissions block
  - ✅ `/cg-commit-push-pr` mentions logical commit splitting
  - ✅ `/cg-verify-pr` mentions `--propose` flag
  - ✅ `/cg-verify-pr` mentions 2-round cap
  - ✅ `/cg-verify-pr` does NOT mention `--watch`
  - ✅ Neither prompt contains internal install directory paths
  - ✅ `model-assignments.Tests.ps1` sentinel updated to 21
- **Acceptance criteria**: All new tests pass; model-assignments sentinel passes.

### 4. Register commands in `docs/reference.md`

- **Requirements**: R11
- **Files**: `docs/reference.md`
- **Details**:
  - Add both commands to the "Copilot Chat Prompts" table.
  - `/cg-commit-push-pr`: model Sonnet 4.6, purpose "Stage changes into logical commits, push, and open a PR with plan-driven description. Proposes commit groups by file type. Requires `gh` CLI for PR creation (graceful degradation without it)."
  - `/cg-verify-pr`: model Sonnet 4.6, purpose "Check CI status on current PR and auto-fix failures. Classifies failures (lint, test, build, platform-specific) and dispatches review agents. 2-round retry cap. Use `--propose` for observe-only diagnosis."
- **Test Scenarios**:
  - ✅ Both entries appear in `docs/reference.md`
- **Acceptance criteria**: Reference doc updated, no broken table formatting.

### 5. Update `copilot-instructions.md` workflow entry points table

- **Requirements**: R11
- **Files**: `.github/copilot-instructions.md`
- **Details**:
  - Add to the Workflow Entry Points table:
    - `/cg-commit-push-pr` — "Ready to commit, push, and open PR"
    - `/cg-verify-pr` — "CI checks failing on PR"
- **Acceptance criteria**: Table entries present, formatting correct.

## Testing Strategy

- **Structural tests** (Pester): Verify prompt files exist, have correct frontmatter, contain required structural elements (Step 0 pattern, key logic blocks, flag handling).
- **Project-agnostic assertion** (R11): Assert neither prompt contains internal install directory paths (e.g., `$env:USERPROFILE\.compound-gpid`, `.compound-gpid/`). Step 0 references to `compound-gpid.md` are expected and excluded.
- **No behavioral tests**: These prompts orchestrate via Copilot Chat — actual behavior is not testable in Pester. Structural coverage ensures the prompts are well-formed.

## Documentation Checklist

- [ ] Prompt files have `description:` in frontmatter (serves as inline docs)
- [ ] `docs/reference.md` updated with both commands
- [ ] `copilot-instructions.md` workflow entry points updated

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| `gh pr checks` output format changes across versions | Fix loop breaks silently | Parse JSON output (`--json`) rather than text; test with current `gh` version |
| CI logs too large to fit in context window | Agent cannot diagnose | Truncate to last 100 lines per failing check; focus on error summary lines |
| Auto-fix introduces new failures (cascading) | Infinite loop risk | Hard 2-round cap; after round 2, always stop and report |
| `git push --force-with-lease` rejected | Rebase cycle | Report to user; never escalate to `--force` |
| Consumer projects without CI | `/cg-verify-pr` has nothing to check | Detect empty `statusCheckRollup`; report "No CI checks configured for this repo" |

## Out of Scope

- Auto-merge after checks pass
- Multi-repo support
- PR reviewers/labels assignment
- Integration with `/cg-review` (full review agent suite before opening PR)
- Squash/rebase strategy selection at PR time
- Custom commit-splitting rules (beyond file-type heuristic)
