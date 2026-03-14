---
date: 2026-03-13
title: "Fix CLM/OneDrive profile dot-source error — batch wrappers + C:\\WBG install"
status: active
brainstorm: ".cg-docs/brainstorms/2026-03-13-clm-onedrive-install-fix.md"
language: "PowerShell"
estimated-effort: "medium"
tags: [install, clm, onedrive, enterprise, powershell, batch-wrappers]
---

# Plan: Fix CLM/OneDrive Install — Batch Wrappers + C:\WBG

## Objective

Replace the broken `$PROFILE`-based command registration with `.cmd` batch
wrappers on PATH, and change the default install location from
`$env:USERPROFILE\.compound-gpid` to `C:\WBG\.compound-gpid`. This fixes the
Constrained Language Mode (CLM) dot-source error caused by OneDrive Documents
folder redirection on enterprise-managed Windows machines.

## Context

- **Current state**: `install.ps1` appends PowerShell functions to `$PROFILE`.
  On World Bank machines, `$PROFILE` now resolves to an OneDrive-synced path.
  CLM blocks dot-sourcing files from that path — both `. $PROFILE` and
  automatic profile loading on terminal startup fail.
- **Brainstorm decision**: Approach 1 — `.cmd` batch wrappers in
  `C:\WBG\.compound-gpid\bin\`, added to user PATH via registry.
- **Constraints**: Must work under Constrained Language Mode. Must be
  idempotent. Must clean up old `$PROFILE` blocks from previous installs.
  All WB machines have `C:\WBG` as a standard unrestricted directory.

## Implementation Steps

### 1. Create batch wrappers in `bin/`

- **Files**: Create `bin/cg-link.cmd`, `bin/cg-unlink.cmd`, `bin/cg-update.cmd`
- **Details**: Each `.cmd` file is a thin wrapper that calls the corresponding
  `.ps1` script with `-NoProfile -ExecutionPolicy Bypass`. Use `%~dp0` to
  resolve the script path relative to the `.cmd` file's own location (so the
  wrappers work regardless of where compound-gpid is installed).

  Template:
  ```cmd
  @echo off
  powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0..\scripts\<name>.ps1" %*
  ```

- **Tests**: Verify each `.cmd` file exists and contains the expected content.
- **Acceptance criteria**: Running `cg-link` from any terminal invokes
  `scripts/link.ps1` via the `.cmd` wrapper.

### 2. Rewrite `install.ps1`

- **Files**: Modify `install.ps1`
- **Details**:
  1. **Keep** Steps 1 (Git check) and 2 (junction capability test) unchanged.
  2. **Replace** Step 3 (profile manipulation) with:
     - **Create `bin/` directory** if it doesn't exist (inside `$CompoundGpidDir`).
     - **Write the three `.cmd` wrappers** to `bin/` (idempotent — overwrite if
       they already exist to handle upgrades).
     - **Add `$CompoundGpidDir\bin` to the user's PATH** via
       `[Environment]::SetEnvironmentVariable('PATH', ..., 'User')` if not
       already present.
     - **Clean up old `$PROFILE` block**: If `$PROFILE` exists and contains the
       `# --- Compound GPID` block, remove it. This handles upgrades from the
       old installation method. Do NOT create or touch `$PROFILE` if it doesn't
       exist.
  3. **Update success output**: Remove `. $PROFILE` instruction. Instead tell
     the user to restart their terminal (PATH changes require a new session).
  4. The install location should be determined by `$PSScriptRoot` (i.e., wherever
     the repo was cloned to — we don't hardcode `C:\WBG` in the script, just
     in the README instructions). This keeps the script flexible.

- **Tests**: Update `tests/install.Tests.ps1`:
  - Remove all profile-related tests (the `Profile idempotency` describe blocks).
  - Add tests for: `.cmd` wrapper content generation, PATH manipulation logic
    (adding to PATH, idempotency when already present), old profile block cleanup.
- **Acceptance criteria**: After running `install.ps1`, the `bin/` directory
  contains three `.cmd` files and `bin/` is on the user PATH.

### 3. Update `scripts/link.ps1` — install path resolution

- **Files**: Modify `scripts/link.ps1`
- **Details**: Change `$CompoundGpidDir` from
  `Join-Path $env:USERPROFILE ".compound-gpid"` to use `$PSScriptRoot` parent:
  ```powershell
  $CompoundGpidDir = Split-Path $PSScriptRoot -Parent
  ```
  This resolves the install location relative to the script itself, making it
  work regardless of whether the user cloned to `C:\WBG\.compound-gpid` or
  `$env:USERPROFILE\.compound-gpid`. Update the error message to remove the
  hardcoded path.

- **Tests**: No changes needed to `tests/link.Tests.ps1` — existing junction
  tests are path-independent.
- **Acceptance criteria**: `link.ps1` works when cloned to any location.

### 4. Update `scripts/unlink.ps1` — no changes needed

- **Files**: `scripts/unlink.ps1`
- **Details**: This script does not reference `$CompoundGpidDir` or
  `$env:USERPROFILE\.compound-gpid`. It only works with the current project
  directory. **No changes required.**
- **Acceptance criteria**: Existing tests pass unchanged.

### 5. Update `scripts/update.ps1` — install path resolution

- **Files**: Modify `scripts/update.ps1`
- **Details**: Change `$CompoundGpidDir` from
  `Join-Path $env:USERPROFILE ".compound-gpid"` to:
  ```powershell
  $CompoundGpidDir = Split-Path $PSScriptRoot -Parent
  ```
  Update the error message to remove the hardcoded USERPROFILE path.

- **Tests**: No changes needed to `tests/update.Tests.ps1` — existing tests
  are path-independent.
- **Acceptance criteria**: `update.ps1` works when cloned to any location.

### 6. Update `README.md`

- **Files**: Modify `README.md`
- **Details**:
  1. **Step 1 (Clone)**: Change path from `"$env:USERPROFILE\.compound-gpid"`
     to `"C:\WBG\.compound-gpid"`.
  2. **Step 2 (Install)**: Change path to `"C:\WBG\.compound-gpid\install.ps1"`.
     Remove the `. $PROFILE` instruction. Replace with "restart your terminal".
  3. **Execution policy note**: Update the bypass command path.
  4. **Directory structure**: Change junction target paths from
     `%USERPROFILE%\.compound-gpid` to `C:\WBG\.compound-gpid`.
  5. **Troubleshooting**: Update the manual git pull path.
  6. Add a **new troubleshooting section** for the CLM/OneDrive error, pointing
     users to the new install approach if they hit the old error.

- **Tests**: None (documentation only).
- **Acceptance criteria**: README accurately describes the new install workflow.

### 7. Update `docs/manual.md`

- **Files**: Modify `docs/manual.md`
- **Details**: Update the reference to `%USERPROFILE%\.compound-gpid` and the
  mention of "registers in your PowerShell profile" in the Getting Started
  section.
- **Acceptance criteria**: Manual reflects the new install mechanism.

### 8. Update skill/prompt references (informational paths only)

- **Files**: `.github/skills/cg-skill-setup/SKILL.md`,
  `.github/prompts/cg-resume.prompt.md`
- **Details**: These files contain informational references to
  `%USERPROFILE%\.compound-gpid`. Update them to `C:\WBG\.compound-gpid` (or
  use a generic phrasing like "the Compound GPID installation directory").
  Since the scripts now use `$PSScriptRoot`, these are purely documentation
  references.
- **Acceptance criteria**: No stale path references remain in user-facing docs.

### 9. Run all tests

- **Files**: All `tests/*.Tests.ps1`
- **Details**: Run `Invoke-Pester tests/` and verify all tests pass.
- **Acceptance criteria**: Zero failures.

## Testing Strategy

- **Unit tests** (Pester 3.4+):
  - `.cmd` wrapper content: verify each file contains the correct PowerShell
    invocation line.
  - PATH manipulation: test adding to PATH, idempotency when already present.
  - Profile cleanup: test removing the old `# --- Compound GPID` block from a
    profile file.
  - Existing junction/link/unlink/update tests remain — they are
    path-independent.
- **Manual smoke test**: Clone to `C:\WBG\.compound-gpid`, run `install.ps1`,
  restart terminal, verify `cg-link`, `cg-unlink`, `cg-update` are available
  and work.

## Documentation Checklist

- [ ] README.md updated with new install path and instructions
- [ ] docs/manual.md updated
- [ ] Skill/prompt path references updated
- [ ] install.ps1 header comments updated

## Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| `C:\WBG` doesn't exist on some machines | `install.ps1` uses `$PSScriptRoot` — works with any clone location. README just recommends `C:\WBG`. |
| Old `$PROFILE` block left behind after upgrade | `install.ps1` explicitly cleans up old profile blocks. |
| `[Environment]::SetEnvironmentVariable` blocked by CLM | Fall back to `setx` command which works in all language modes. |
| User has existing `$env:USERPROFILE\.compound-gpid` clone | README can mention migration: re-clone to `C:\WBG`, run install. Old profile block is cleaned up automatically. |

## Out of Scope

- Removal of the old `$env:USERPROFILE\.compound-gpid` clone (user can do this
  manually after verifying the new install works).
- Linux/macOS support (not applicable — all WB machines are Windows).
- Changing how junction-based linking works (unchanged by this plan).
- Changing the `SCHEMA_VERSION` mechanism (unchanged).
