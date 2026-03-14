---
date: 2026-03-13
title: "Fix CLM/OneDrive profile dot-source error"
status: decided
chosen-approach: "Batch wrappers on PATH + install to C:\\WBG"
tags: [install, clm, onedrive, enterprise, powershell]
---

# Fix CLM/OneDrive Profile Dot-Source Error

## Context

After a OneDrive Documents folder redirection was pushed to World Bank machines,
`$PROFILE` now resolves to an OneDrive-synced path. The organization enforces
Constrained Language Mode (CLM) via AppLocker/WDAC policy. CLM prevents
dot-sourcing scripts from untrusted (OneDrive) locations, which breaks the
current profile-based approach for registering `cg-link`, `cg-unlink`, and
`cg-update` functions.

Error observed:
```
Cannot dot-source this command because it was defined in a different language mode.
```

This affects all World Bank users with the same configuration.

## Requirements

- Commands `cg-link`, `cg-unlink`, `cg-update` must work from any terminal.
- Must not depend on `$PROFILE` or dot-sourcing.
- Must work under Constrained Language Mode.
- Should use a standard path (`C:\WBG\.compound-gpid`) consistent across the team.
- Install script must be idempotent.
- PowerShell-only (no cmd.exe requirement from users).

## Approaches Considered

### Approach 1: Batch wrappers on PATH + install to C:\WBG (Chosen)

Drop the `$PROFILE` approach entirely. Place `.cmd` batch wrapper files in
`C:\WBG\.compound-gpid\bin\` and add that directory to the user's PATH.

- **Pros**: Completely avoids $PROFILE and CLM issues. `.cmd` files are always
  trusted by Windows. Works in any terminal. No dot-sourcing. Simple and robust.
  `C:\WBG` is a known safe directory on all WB machines.
- **Cons**: Each command spawns a new PowerShell process (~0.5s startup).
- **Effort**: Small

### Approach 2: PowerShell module in local path

Package cg-* functions as a PowerShell module and add to PSModulePath via registry.

- **Pros**: Feels native to PowerShell.
- **Cons**: CLM may also block module loading from untrusted user paths. More
  complex. Hard to test across different policy configurations.
- **Effort**: Medium

### Approach 3: Hybrid — profile fallback + batch wrappers

Keep profile block for non-CLM machines, add batch wrappers as primary.

- **Pros**: Works everywhere.
- **Cons**: Two code paths, more maintenance, confusing install output.
- **Effort**: Medium

## Decision

**Approach 1** — Batch wrappers + install to `C:\WBG\.compound-gpid`.

Rationale: Simplest, most robust, avoids CLM entirely. The ~0.5s overhead is
negligible for commands run a few times a day. `C:\WBG` is a standard,
IT-unrestricted path on all World Bank machines, making the install path
consistent across the team.

## Next Steps

1. Create `bin/` directory with `cg-link.cmd`, `cg-unlink.cmd`, `cg-update.cmd` wrappers.
2. Update `install.ps1` to:
   - Use `C:\WBG\.compound-gpid` as the default install location.
   - Create `.cmd` wrappers in `bin/`.
   - Add `bin/` to user PATH (via registry, persistent).
   - Remove the `$PROFILE` manipulation code.
   - Clean up any existing profile blocks from previous installs.
3. Update `README.md` install instructions with new clone path.
4. Update `scripts/update.ps1` if it references the old install path.
5. Update tests to reflect new behavior.
6. Update `scripts/link.ps1` and `scripts/unlink.ps1` if they reference USERPROFILE paths.
