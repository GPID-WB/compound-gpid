---
date: 2026-03-18
title: "Version pinning via cg-update"
status: active
brainstorm: ".cg-docs/brainstorms/2026-03-18-version-pinning-via-cg-update.md"
language: "both"
estimated-effort: "medium"
tags: [versioning, releases, cg-update, git-tags, powershell]
---

# Plan: Version pinning via cg-update

## Objective

Extend `cg-update` to support pinning the global Compound GPID installation to a specific GitHub Release (git tag), so users can choose between stability (a known-good version) and bleeding-edge (latest `main`). The version preference is stored per-user in a `.cg-version` file inside the global install directory.

## Context

Today, `cg-update` does `git pull --ff-only` on `main`. Every linked project immediately gets HEAD. There is no concept of releases or version pinning. The brainstorm decided on Approach 1: extend `cg-update` with an optional version argument and a `.cg-version` file, using GitHub Releases (git tags) as the release mechanism.

Key constraints from existing code:
- `cg-update.cmd` already passes `%*` to `update.ps1`, so CLI arguments flow through.
- `link.ps1` calls `update.ps1` internally with `$env:CG_INTERNAL_CALL = "1"` — pinned-version checkout must work in this context too.
- All scripts target PowerShell 5.1 with `$ErrorActionPreference = "Stop"` — any new `git` calls must use the established `try { ... 2>$null } catch {}` pattern to avoid PS5.1 stderr promotion (see `.cg-docs/solutions/git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md`).
- Tests use Pester 3.4+ (built-in on Windows).

## Implementation Steps

### 1. Add `.cg-version` file support to `install.ps1`

- **Files**: `install.ps1`
- **Details**: After the PATH registration step (Step 3), add a step that creates `.cg-version` with content `latest` if the file does not already exist. If it exists (upgrade path), leave it untouched to preserve the user's choice.
- **Tests**: Add test in `tests/install.Tests.ps1`:
  - `.cg-version` is created with `latest` when absent.
  - `.cg-version` is left untouched when it already exists (idempotency).
- **Acceptance criteria**: After running `install.ps1` on a fresh install, `.cg-version` exists and contains `latest`. Re-running does not overwrite an existing value.

### 2. Refactor `update.ps1` — argument parsing and `.cg-version` read/write

- **Files**: `scripts/update.ps1`
- **Details**:
  - Accept an optional first positional argument: a tag name (e.g., `v0.2.0`), the string `latest`, or the flag `--list`.
  - On startup, read `.cg-version` from `$CompoundGpidDir`. If the file is missing, treat as `latest` (backward compatibility with pre-versioning installs).
  - If the user passes a version argument, write it to `.cg-version` before proceeding.
  - Store the resolved mode in a `$versionMode` variable: either `latest` or the specific tag string.
- **Tests**: Add tests in `tests/update.Tests.ps1`:
  - Argument parsing: no args, `latest`, `v0.1.0`, `--list`.
  - `.cg-version` read: file present with `latest`, file present with `v0.1.0`, file absent (defaults to `latest`).
  - `.cg-version` write: switching from `latest` to `v0.1.0`, from `v0.1.0` to `latest`.
- **Acceptance criteria**: `$versionMode` correctly reflects the resolved version for all input combinations.

### 3. Implement `--list` flag in `update.ps1`

- **Files**: `scripts/update.ps1`
- **Details**:
  - When `--list` is passed, run `git fetch --tags` then `git tag --list "v*" --sort=-version:refname` to list available versions sorted newest-first.
  - Display a formatted table with the tag name and a marker for the currently active version (read from `.cg-version`).
  - Show a hint: `"Run: cg-update <version> to pin, cg-update latest to track main"`.
  - Exit after displaying — do not proceed with update logic.
- **Tests**: Add tests in `tests/update.Tests.ps1`:
  - Simulated tag list formatting and current-version marking.
  - Hint message is present in output.
- **Acceptance criteria**: `cg-update --list` displays available tags with the current one marked, then exits.

### 4. Implement "latest" mode in `update.ps1` (refactor existing logic)

- **Files**: `scripts/update.ps1`
- **Details**:
  - When `$versionMode` is `latest`:
    - If currently in detached HEAD (from a previous pin), run `git checkout main` first.
    - Then proceed with the existing `git checkout .` + `git pull --ff-only` logic (unchanged).
  - Add `git fetch --tags` before the pull so tag metadata stays up to date even in latest mode.
- **Tests**: Add tests in `tests/update.Tests.ps1`:
  - Detached HEAD detection and branch switch simulation.
  - Existing pull-mode tests continue to pass.
- **Acceptance criteria**: `cg-update` with `.cg-version = latest` behaves identically to today's behavior, except it also fetches tags and handles the detached-HEAD-to-main transition.

### 5. Implement "pinned" mode in `update.ps1`

- **Files**: `scripts/update.ps1`
- **Details**:
  - When `$versionMode` is a tag (e.g., `v0.2.0`):
    - Run `git fetch --tags`.
    - Validate the tag exists: `git tag --list $versionMode`. If not found, error with a helpful message listing similar tags.
    - Run `git checkout $versionMode` (detached HEAD). Use the PS5.1-safe `try { git checkout ... 2>$null } catch {}` pattern.
    - Display: `"Pinned to $versionMode. Run cg-update latest to return to tracking main."`.
  - The copilot-instructions.md refresh and structural migration sections remain unchanged — they run regardless of mode.
- **Tests**: Add tests in `tests/update.Tests.ps1`:
  - Tag validation: tag exists vs. tag does not exist.
  - Checkout to tag with PS5.1-safe pattern.
  - Confirmation message displayed.
- **Acceptance criteria**: `cg-update v0.2.0` writes `v0.2.0` to `.cg-version`, fetches tags, checks out the tag, and displays a confirmation. Invalid tags produce a clear error.

### 6. Add version display to `update.ps1` output

- **Files**: `scripts/update.ps1`
- **Details**:
  - At the end of every update run (both modes), display the current state:
    - `"Current version: v0.2.0 (pinned)"` or `"Current version: main (latest)"`.
  - When a newer release exists and the user is pinned, show: `"Newer release available: v0.3.0. Run: cg-update v0.3.0"`.
- **Tests**: Add tests in `tests/update.Tests.ps1`:
  - Status line formatting for pinned vs. latest mode.
  - Newer-version hint when applicable.
- **Acceptance criteria**: Every `cg-update` run ends with a clear status line showing what version is active.

### 7. Update `link.ps1` to respect pinned version

- **Files**: `scripts/link.ps1`
- **Details**:
  - `link.ps1` already calls `update.ps1` with `$env:CG_INTERNAL_CALL = "1"`. No argument changes needed — `update.ps1` will read `.cg-version` and do the right thing (pull latest or checkout the pinned tag).
  - Verify that the internal call path works correctly in both modes. Add a diagnostic line after the update call showing which version was resolved.
- **Tests**: Verify in `tests/link.Tests.ps1` that the update call pattern still works (existing tests should still pass).
- **Acceptance criteria**: `cg-link` on a pinned install checks out the pinned tag, not `main`.

### 8. Update documentation

- **Files**: `docs/installation.md`, `docs/reference.md`, `docs/manual.md`
- **Details**:
  - `installation.md`: Add a "Version Pinning" section after "Updating" explaining `cg-update <version>`, `cg-update latest`, and `cg-update --list`.
  - `reference.md`: Update the `cg-update` row in the PowerShell Commands table to mention optional version argument. Add a new "Version Management" section.
  - `manual.md`: Brief mention in the relevant section.
- **Tests**: None (documentation only).
- **Acceptance criteria**: A new user can discover and use version pinning from the docs alone.

### 9. Add `.cg-version` to `.gitignore`

- **Files**: `.gitignore` (in the compound-gpid repo itself)
- **Details**:
  - Add `.cg-version` to the repo's `.gitignore` so the user's version preference is never accidentally committed.
- **Tests**: None.
- **Acceptance criteria**: `git status` does not show `.cg-version` as an untracked file.

## Testing Strategy

All tests use Pester 3.4+ with `$TestDrive` for isolated file operations. No tests touch the real git repo or the user's actual install directory.

**Test categories:**
- **Argument parsing**: all input combinations (no args, `latest`, tag, `--list`, invalid input).
- **`.cg-version` file I/O**: read, write, missing file, malformed content.
- **Mode logic**: latest-to-pinned transition, pinned-to-latest transition, re-pin to different version.
- **Tag validation**: valid tag, invalid tag, similar-tag suggestion.
- **Output formatting**: status lines, list formatting, upgrade hints.
- **Backward compatibility**: existing behavior unchanged when `.cg-version` is absent or set to `latest`.
- **PS5.1 safety**: all new git calls use the try/catch + 2>$null pattern.

## Documentation Checklist

- [ ] `docs/installation.md` — Version Pinning section
- [ ] `docs/reference.md` — Updated command table + Version Management section
- [ ] `docs/manual.md` — Brief mention
- [ ] Inline comments in `update.ps1` explaining the two modes
- [ ] Help text in `--list` output

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Detached HEAD confuses users who inspect git status | Clear messaging: "Pinned to v0.2.0 (detached HEAD is expected)" |
| PS5.1 stderr promotion on `git checkout <tag>` | Use established try/catch + 2>$null pattern from the PS5.1 solution |
| User runs `cg-update` while pinned and expects to see new changes | Status line always shows current mode; upgrade hint when newer release exists |
| No GitHub Releases exist yet (empty tag list) | `--list` shows "No releases found" with hint to check GitHub |
| `.cg-version` file corrupted or contains invalid value | Validate content; fall back to `latest` with a warning if unrecognized |

## Out of Scope

- **Channel system** (stable/beta/main) — can be layered on later per the brainstorm.
- **Per-project version pinning** — brainstorm decided on per-user only.
- **Automatic upgrade notifications** — only shown during `cg-update` runs, not proactively.
- **Creating the first GitHub Release** — separate task; requires agreeing on a version number and writing release notes.
- **`cg-releases` companion command** — rejected in brainstorm.
