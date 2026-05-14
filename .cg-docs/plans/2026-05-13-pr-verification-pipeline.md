---
date: 2026-05-13
title: "PR verification pipeline (E2E smoke tests, parity checks, CONTRIBUTING.md)"
status: completed
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-13-pr-verification-strategy-cross-platform.md"
language: "both"
estimated-effort: "medium"
tags: [ci, testing, pr-review, cross-platform, contributing, github-actions]
---

# Plan: PR Verification Pipeline

## Objective

Add automated cross-platform verification to the CI pipeline so that PRs which
pass unit tests but fail on real machines (like the macOS `cg-link` bug in PR #37)
are caught before merge. Supplement with contributor documentation and a PR
template that encodes the project's seven verification dimensions.

## Context

- Existing CI runs Pester 4.10.1 on `windows-2022` and `macos-14` via
  `.github/workflows/tests.yml`. Link-check runs on markdown changes.
- PR #37 passed CI but `cg-link` failed on a real macOS machine because
  `Join-Path` with a hardcoded backslash works on Windows CI but not macOS.
  The macOS CI only ran `link.sh` (bash tests), not `link.ps1` via `pwsh`.
- The project has dual platform scripts (`link.ps1` / `link.sh`,
  `unlink.ps1` / `unlink.sh`, etc.) that must stay in sync.
- No `CONTRIBUTING.md` or PR template exists today.

## Requirements

| ID  | Requirement                                                       | Source           |
|-----|-------------------------------------------------------------------|------------------|
| R1  | E2E smoke test: run cg-link on a fresh temp project dir           | brainstorm       |
| R2  | E2E smoke test: verify idempotency (run cg-link twice)            | brainstorm       |
| R3  | E2E smoke test: run cg-unlink, verify clean state                 | brainstorm       |
| R4  | E2E smoke test: both platforms (Windows junctions, macOS symlinks) | brainstorm       |
| R5  | Cross-script parity: link.ps1 and link.sh have same managed dirs  | brainstorm       |
| R6  | Cross-script parity: same verification file target                | brainstorm       |
| R7  | Cross-script parity: same gitignore entries                       | brainstorm       |
| R8  | Conventional commits lint on PRs                                  | brainstorm       |
| R9  | Docs staleness warning when scripts change                        | brainstorm       |
| R10 | CONTRIBUTING.md for external contributors                         | brainstorm       |
| R11 | PR template with seven-dimension review checklist                 | brainstorm       |

## Phase 0: Prerequisites

### 0. Add `-Force` flag to unlink scripts (CI non-interactive support)

- **Requirements**: R3 (prerequisite)
- **Files**: `scripts/unlink.ps1`, `scripts/unlink.sh`
- **Details**:
  - `unlink.ps1`: Add a `[switch]$Force` parameter. When present, skip the
    `Read-Host "Proceed? [y/N]"` confirmation and proceed directly.
  - `unlink.sh`: Add a `--yes` / `-y` flag. When present, skip the
    `read -r answer` confirmation.
  - Behavior without the flag is unchanged (interactive confirmation preserved).
  - Update existing `unlink.Tests.ps1` to verify the flag exists in source.
- **Test Scenarios**:
  - ✅ `unlink.ps1 -Force` proceeds without prompting
  - ✅ `unlink.sh --yes` proceeds without prompting
  - ✅ Without flag, interactive confirmation still required
- **Acceptance criteria**: E2E steps (Steps 1-2) can call unlink
  non-interactively in CI.

## Phase 1: E2E Smoke Tests and Parity Checks

### 1. E2E smoke test CI job (Windows)

- **Requirements**: R1, R2, R3, R4
- **Files**: `.github/workflows/tests.yml` (add new job or steps)
- **Details**:
  - After the existing Pester test step on Windows, add an E2E step:
    1. Create a temp directory to simulate a fresh project (`$env:RUNNER_TEMP/e2e-project`).
    2. `cd` into it. Run `pwsh -File $env:GITHUB_WORKSPACE/scripts/link.ps1`.
    3. Assert: `.github/prompts` junction exists, `Test-Path .github/prompts/cg-setup.prompt.md` succeeds.
    4. Run `link.ps1` again — assert no errors (idempotency).
    5. Run `pwsh -File $env:GITHUB_WORKSPACE/scripts/unlink.ps1 -Force`.
    6. Assert: `.github/prompts` junction is gone, `.gitignore` has no CG entries.
  - Use pwsh shell. `link.ps1` derives compound-gpid root from `$PSScriptRoot`
    — invoke it via its absolute path from the checkout directory.
  - **Teardown** (`if: always()`): Explicitly remove any junctions before
    deleting the temp directory. Use the safe 2-level scan pattern from
    `link.Tests.ps1` to prevent `Remove-Item -Recurse` from following
    junction targets into `$GITHUB_WORKSPACE`:
    ```powershell
    Get-ChildItem "$env:RUNNER_TEMP/e2e-project" -Recurse -Force -ErrorAction SilentlyContinue |
      Where-Object { $_.LinkType -eq 'Junction' } |
      ForEach-Object { Remove-Item $_.FullName -Force }
    Remove-Item "$env:RUNNER_TEMP/e2e-project" -Recurse -Force -ErrorAction SilentlyContinue
    ```
- **Test Scenarios**:
  - ✅ Happy path: fresh dir → link → verify → link again → unlink -Force → clean
  - 🛑 Edge case: project dir that already has a `.github/workflows/` folder
  - ❌ Error path: link.ps1 called from a non-existent directory
  - 🛑 Failure mid-run: teardown step removes junctions even on test failure
- **Acceptance criteria**: E2E step passes on `windows-2022`; catches the
  `Join-Path` backslash bug if reintroduced; junctions are always cleaned up.

### 2. E2E smoke test CI job (macOS)

- **Requirements**: R1, R2, R3, R4
- **Files**: `.github/workflows/tests.yml` (add new job or steps)
- **Details**:
  - Same pattern as Step 1 but for macOS:
    1. Create temp project dir.
    2. Run `bash $GITHUB_WORKSPACE/scripts/link.sh`.
    3. Assert: `.github/prompts` is a symlink, `test -f .github/prompts/cg-setup.prompt.md`.
    4. Run `link.sh` again — assert no errors (idempotency).
    5. Run `bash $GITHUB_WORKSPACE/scripts/unlink.sh --yes`.
    6. Assert: symlinks are gone.
  - Use bash shell. `chmod +x` step already exists in CI.
  - **Teardown** (`if: always()`): `rm -rf $RUNNER_TEMP/e2e-project` (safe on
    macOS — symlinks are not followed by `rm -rf`).
- **Test Scenarios**:
  - ✅ Happy path: fresh dir → link → verify → link again → unlink → clean
  - 🛑 Edge case: project with existing `.github/` content (workflows, CODEOWNERS)
  - ❌ Error path: link.sh called when compound-gpid dir doesn't exist
- **Acceptance criteria**: E2E step passes on `macos-14`; catches symlink and
  path separator bugs.

### 3. Cross-script parity test

- **Requirements**: R5, R6, R7
- **Files**: New `tests/parity.Tests.ps1` + register in `tests/Run-Tests.ps1`
- **Details**:
  - Create `tests/parity.Tests.ps1` with Describe blocks:
    - "link.ps1 ↔ link.sh parity": extract `$ManagedDirs` from `link.ps1`
      and `MANAGED_DIRS` from `link.sh` via regex; assert same elements
      (order-independent). Assert both reference same verification file.
      Extract gitignore entries from both and compare.
    - "unlink.ps1 ↔ unlink.sh parity": same for unlink scripts.
  - **Register in `Run-Tests.ps1`**: Add `'parity'` to `$testNames` array,
    positioned before the junction-creating tests (`link`, `unlink`).
    Without this, the test file is silently skipped by the canonical runner.
  - Reuse the regex extraction pattern already proven in `link.Tests.ps1`
    (Describe "compound-gpid.context.md is not gitignored").
- **Test Scenarios**:
  - ✅ Happy path: both scripts list identical dirs
  - 🛑 Edge case: one script adds a new dir without updating the other
  - ❌ Error path: regex extraction fails (file changed format)
- **Tests**: This IS the test — a Pester Describe block.
- **Acceptance criteria**: Test fails if someone changes `link.ps1` managed
  dirs without updating `link.sh` (or vice versa). Test runs in CI via
  `Run-Tests.ps1`.

## Phase 2: CI Lint and Docs Check

### 4. Conventional commits lint

- **Requirements**: R8
- **Files**: `.github/workflows/commit-lint.yml` (new workflow)
- **Details**:
  - Use `amannn/action-semantic-pull-request@v5` — validates PR title against
    conventional commits format. Lightweight JavaScript action; Node is
    pre-installed on GitHub-hosted runners.
  - Configure allowed types: `feat`, `fix`, `docs`, `test`, `refactor`,
    `chore`, `data`, `analysis` (matching project conventions).
  - Run only on `pull_request` events.
- **Test Scenarios**:
  - ✅ `fix(link): replace Read-Host` → passes
  - ❌ `updated link script` → fails with clear message
- **Acceptance criteria**: PRs with non-conventional titles get a clear CI
  failure message explaining the format.

### 5. Docs staleness warning

- **Requirements**: R9
- **Files**: `.github/workflows/tests.yml` (new step) or standalone workflow
- **Details**:
  - Use `git diff --name-only origin/$DEFAULT_BRANCH...HEAD` to find files
    changed in the PR. If any file in `scripts/` is modified but no file in
    `docs/` is modified, emit a warning annotation.
  - This approach works correctly with GitHub Actions' default shallow clone
    (`fetch-depth: 1`) because `git diff --name-only` only needs the merge
    base and HEAD — not full history. Add `fetch-depth: 0` only if the
    diff command fails (future-proofing note in workflow comments).
  - **Non-blocking**: annotation only (`::warning`), not a failure. Reviewers
    see it in the PR checks summary.
  - Skip if only non-behavioral script files changed (e.g., comments only —
    use a heuristic: if the diff in `scripts/` is ≤3 lines and all are
    comments, skip the warning).
- **Test Scenarios**:
  - ✅ Scripts and docs updated together → no warning
  - 🛑 Script changed, docs unchanged → warning annotation
  - ✅ Only docs changed → no warning
- **Acceptance criteria**: Warning appears as a GitHub annotation on the PR
  when scripts have behavioral changes without corresponding docs updates.

## Phase 3: Contributor Documentation

### 6. CONTRIBUTING.md

- **Requirements**: R10
- **Files**: `CONTRIBUTING.md` (project root)
- **Details**: Cover:
  - **Local test setup**: How to run tests on Windows (Pester 4.10.1) and
    macOS (pwsh + Pester 4.10.1). Reference `tests/Run-Tests.ps1`.
  - **CI explanation**: What the automated checks verify (Pester suite,
    link-check, E2E smoke, commit lint, docs staleness).
  - **Platform requirements**: Both `link.ps1` and `link.sh` must be
    updated together when touching cross-platform logic.
  - **Commit conventions**: `type(scope): description` with allowed types.
  - **PR workflow**: Fork → branch → commit → PR → CI passes → review.
  - **When to update docs**: If CLI behavior, flags, or error messages change.
  - **Self-review checklist**: Reference the PR template dimensions.
- **Acceptance criteria**: A new contributor can read this file and
  successfully run the test suite locally on either platform.

### 7. PR template

- **Requirements**: R11
- **Files**: `.github/PULL_REQUEST_TEMPLATE.md`
- **Details**: Seven-dimension checklist, each with guidance:
  ```markdown
  ## PR Checklist

  Please verify each dimension before requesting review:

  - [ ] **E2E verified**: I ran cg-link/cg-unlink on a fresh project dir
        locally on my platform (Windows: junctions created; macOS: symlinks
        created; `cg-setup.prompt.md` accessible through the link).
  - [ ] **Cross-script parity**: Changes to `.ps1` scripts are mirrored in
        `.sh` equivalents (and vice versa). Managed dirs, verification file,
        and gitignore entries match.
  - [ ] **Docs updated**: `docs/installation.md`, `docs/manual.md`, or
        `README.md` reflect any behavioral changes — or N/A if no
        user-facing behavior changed.
  - [ ] **Backward compatible**: Users with existing installs (junctions/
        symlinks from prior versions) can run `cg-update` and then
        `cg-link` without errors.
  - [ ] **Idempotent**: Running the changed command twice in a row produces
        no errors, no duplicate entries, no extra files.
  - [ ] **Commit conventions**: All commits follow `type(scope): description`
        format. Allowed types: feat, fix, docs, test, refactor, chore,
        data, analysis.
  - [ ] **Security reviewed**: Path handling does not introduce traversal
        vulnerabilities or symlink-following attacks. No user-controlled
        input flows into path construction without validation.
  ```
- **Acceptance criteria**: Template auto-populates when opening a PR on GitHub.

## Testing Strategy

- Steps 1-2 are themselves CI tests — they pass/fail in GitHub Actions.
- Step 3 is a Pester test file that runs in the existing suite.
- Step 4 uses a third-party action — test by opening a PR with a bad title.
- Step 5 uses git timestamps — test by checking annotation output.
- Steps 6-7 are documentation — verify by visual inspection.

## Documentation Checklist

- [ ] `CONTRIBUTING.md` (Step 6 — is the documentation)
- [ ] `docs/installation.md` — no changes needed
- [ ] PR template (Step 7 — is the documentation)
- [ ] README.md — add a "Contributing" section linking to `CONTRIBUTING.md`

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| E2E tests are flaky on CI (file system timing) | False failures block PRs | Use retry logic; keep tests simple (no parallel) |
| Junction cleanup missed on failure (Windows) | Corrupts `$GITHUB_WORKSPACE` checkout | `if: always()` teardown step with 2-level junction scan |
| Commit lint rejects valid PRs from unfamiliar contributors | Contributor friction | Clear error message + documented format in CONTRIBUTING.md |
| Parity test is too brittle (breaks on formatting changes) | Maintenance burden | Use robust regex; test the extraction logic itself |
| Docs staleness check has too many false positives | Alert fatigue | Only warn when `scripts/` has behavioral changes without any `docs/` change |
| New test file silently skipped if not registered | False "all pass" | Explicit step to add to `$testNames` in `Run-Tests.ps1` |

## Out of Scope

- `/cg-review` integration for PRs (maintainer-only; document as optional)
- Branch protection rules (requires repo admin; document as recommendation)
- Code coverage enforcement (not needed for this project type)
- Automated PR auto-merge
