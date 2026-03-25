---
date: 2026-03-14
title: "Dual install paths and restart documentation"
status: completed
brainstorm: ".cg-docs/brainstorms/2026-03-14-dual-install-paths-and-restart-docs.md"
language: "both"
estimated-effort: "small"
tags: [documentation, installation, onedrive, remote-server]
---

# Plan: Dual Install Paths and Restart Documentation

## Objective

Update documentation and script error messages to support two install locations (`C:\WBG\.compound-gpid` for local OneDrive machines, `$env:USERPROFILE\.compound-gpid` for the remote server) and add prominent "restart VS Code / Positron" callouts at every step that requires it.

## Context

The scripts (`install.ps1`, `link.ps1`, `update.ps1`) are already location-agnostic — they resolve paths via `$PSScriptRoot` and `%~dp0`. The only hardcoded `C:\WBG\.compound-gpid` references are in:

- **Documentation**: `docs/installation.md`, `docs/troubleshooting.md`
- **Script error messages**: `scripts/link.ps1` (line 50–51), `scripts/update.ps1` (line 38–39)
- **Script comments**: `install.ps1` (line 5)
- **Tests**: `tests/install.Tests.ps1` (uses `C:\WBG\.compound-gpid\bin` as test data — these are fine as-is, they're testing PATH logic with a concrete example)

The brainstorm chose Approach 1: documentation-only fix (no script logic changes).

## Implementation Steps

### 1. Update `docs/installation.md`

- **Files**: `docs/installation.md`
- **Details**:
  - Add a "Choose your install path" note before Step 1 explaining the two environments:
    - **Local machine (OneDrive)**: use `C:\WBG\.compound-gpid` to avoid Constrained Language Mode issues.
    - **Remote server (no OneDrive)**: use `$env:USERPROFILE\.compound-gpid` (standard user-profile location).
  - Show both clone commands in Step 1, clearly labelled.
  - Update Step 2 to show the install command with a placeholder or both paths.
  - Add a **prominent callout** after Step 2: "Restart VS Code / Positron (not just the terminal) for the PATH change and Copilot to take effect."
  - Add a **prominent callout** after Step 3 (`cg-link`): "Restart VS Code / Positron so Copilot picks up the new `.github/` content."
  - Update the "Upgrading" section's troubleshooting paths to mention both locations.
- **Tests**: Manual review — verify rendered markdown looks correct.
- **Acceptance criteria**: Both install paths are documented; restart callouts appear after Steps 2 and 3.

### 2. Update `docs/troubleshooting.md`

- **Files**: `docs/troubleshooting.md`
- **Details**:
  - In the `cg-update` fails section, replace hardcoded `C:\WBG\.compound-gpid` with a note like "your install directory (e.g. `C:\WBG\.compound-gpid` or `$env:USERPROFILE\.compound-gpid`)".
  - Keep the git commands but use a variable-style placeholder or show both paths.
- **Tests**: Manual review.
- **Acceptance criteria**: No hardcoded path assumptions; reader knows to substitute their path.

### 3. Update script error messages in `scripts/link.ps1`

- **Files**: `scripts/link.ps1`
- **Details**:
  - Line 48–52: Replace the hardcoded `C:\WBG\.compound-gpid` in the `Write-Error` here-string with the dynamic `$CompoundGpidDir` variable (already available) and a generic recommendation.
- **Tests**: Existing `tests/link.Tests.ps1` should still pass (error messages are not tested there).
- **Acceptance criteria**: Error message shows the actual resolved path, not a hardcoded one.

### 4. Update script error messages in `scripts/update.ps1`

- **Files**: `scripts/update.ps1`
- **Details**:
  - Line 35–41: Same treatment — replace hardcoded `C:\WBG\.compound-gpid` in `Write-Error` with dynamic path and generic install instructions.
- **Tests**: Existing `tests/update.Tests.ps1` should still pass.
- **Acceptance criteria**: Error message shows the actual resolved path.

### 5. Update `install.ps1` comment and success message

- **Files**: `install.ps1`
- **Details**:
  - Line 5: Update the comment example to show a generic path or both paths.
  - Lines 160–170: Change "Restart your terminal" to "Restart VS Code / Positron (or your terminal)" in the success output.
- **Tests**: Existing `tests/install.Tests.ps1` should still pass (tests don't test output messages).
- **Acceptance criteria**: Success message mentions restarting the IDE, not just the terminal.

### 6. Update `scripts/link.ps1` success message

- **Files**: `scripts/link.ps1`
- **Details**:
  - After the "Linked!" success block (~line 233), add a callout: "IMPORTANT: Restart VS Code / Positron so Copilot picks up the linked prompts and agents."
- **Tests**: None needed.
- **Acceptance criteria**: User sees restart instruction after linking.

## Testing Strategy

- Run existing Pester tests (`tests/install.Tests.ps1`, `tests/link.Tests.ps1`, `tests/update.Tests.ps1`) to confirm no regressions.
- Manual review of rendered markdown for `docs/installation.md` and `docs/troubleshooting.md`.
- The `tests/install.Tests.ps1` file uses `C:\WBG\.compound-gpid\bin` as test data in PATH logic tests — these are fine as-is (they test the string-matching logic, not the actual install path).

## Documentation Checklist

- [x] Function documentation — N/A (no new functions)
- [ ] README updates — not needed (README links to docs/, no hardcoded paths)
- [ ] `docs/installation.md` — dual paths + restart callouts
- [ ] `docs/troubleshooting.md` — generic paths
- [ ] Inline comments — update `install.ps1` header comment

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|-----------|------------|
| User doesn't read the path-choice section | Medium | Keep it short and prominent (blockquote/callout), placed before Step 1 |
| Existing users confused by new docs | Low | Changes are additive — `C:\WBG\.compound-gpid` is still shown as the recommended local path |

## Out of Scope

- Auto-detection of OneDrive in `install.ps1` (Approach 2 — rejected).
- Config file recording install path (Approach 3 — rejected).
- Changes to script logic — scripts are already correct.
- Shared server install with system-wide PATH (requires admin rights, not available).
