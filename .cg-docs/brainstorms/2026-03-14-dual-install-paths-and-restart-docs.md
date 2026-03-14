---
date: 2026-03-14
title: "Dual install paths (local vs. remote server) and restart documentation"
status: decided
chosen-approach: "Documentation-only fix"
tags: [documentation, installation, onedrive, remote-server]
---

# Dual Install Paths and Restart Documentation

## Context

Two issues surfaced during team onboarding:

1. **Restart requirement not documented**: After `install.ps1` (PATH change) and `cg-link` (junction creation), users must restart VS Code / Positron for both the integrated terminal and Copilot to pick up the changes. This was only mentioned as "restart your terminal" and not emphasized enough.

2. **Remote server has no OneDrive**: Team members work on a remote Windows server where OneDrive is absent. The `C:\WBG\.compound-gpid` path was chosen for local machines to avoid OneDrive/CLM issues, but on the server `$env:USERPROFILE\.compound-gpid` works fine. The scripts are already location-agnostic (`$PSScriptRoot` / `%~dp0`), but the documentation and error messages only mention `C:\WBG\.compound-gpid`.

The remote server does not grant admin rights, so each user must clone and run `install.ps1` themselves.

## Requirements

- Documentation must present two install paths: `C:\WBG\.compound-gpid` (local, OneDrive machines) and `$env:USERPROFILE\.compound-gpid` (remote server, no OneDrive).
- Prominent "restart VS Code / Positron" callout after install and after linking.
- Error messages in scripts should not hardcode `C:\WBG\.compound-gpid` — use dynamic paths or neutral phrasing.
- No changes to script logic (already correct).

## Approaches Considered

### Approach 1: Documentation-only fix (CHOSEN)

Update docs (`installation.md`, `troubleshooting.md`, `README.md`) and script error messages to cover both install locations and add restart callouts. No script logic changes.

**Pros**: Minimal change, no risk of breaking existing installs, quick to ship.
**Cons**: Users must read the docs and choose the right path themselves.
**Effort**: Small.

### Approach 2: Smart default with environment detection

Have `install.ps1` auto-detect OneDrive presence and suggest the appropriate clone path.

**Pros**: Smarter UX.
**Cons**: The install path is chosen *before* running `install.ps1` (user already cloned), so detection is only advisory. Adds complexity without real benefit.
**Effort**: Medium.

### Approach 3: Config file recording install location

Write a metadata file during install for better error messages.

**Pros**: Error messages become perfectly accurate.
**Cons**: `$PSScriptRoot` already solves this; a config file adds complexity without addressing a real gap.
**Effort**: Medium.

## Decision

Approach 1 — documentation and error message updates only. The scripts are already location-agnostic; only the docs and error strings need to tell the right story.

## Next Steps

1. Update `docs/installation.md`:
   - Add "Choose your install path" section explaining local vs. server.
   - Add prominent restart VS Code / Positron callout after install and after `cg-link`.
2. Update `docs/troubleshooting.md`: mention both paths where relevant.
3. Update error messages in `install.ps1`, `scripts/link.ps1`, `scripts/update.ps1` to remove hardcoded `C:\WBG\.compound-gpid` references.
4. Update `README.md` quick-start if it mentions a specific path.
5. Update `install.ps1` success message to mention restarting VS Code / Positron (not just terminal).
