---
date: 2026-03-04
title: "$$  is not a process ID in PowerShell"
category: "build-errors"
language: "both"
tags: [powershell, pid, temp-files, unique-names, guid]
root-cause: "In Bash $$ expands to the current PID; in PowerShell $$ expands to the last token of the previous command line, producing collision-prone or empty strings"
severity: "P1"
---

# `$$` Is Not a Process ID in PowerShell

## Problem

A script used `$$` to generate a unique temp directory name, as is idiomatic in
Bash/sh:

```powershell
# WRONG — copied from Bash idiom
$tempTarget   = Join-Path $env:TEMP "cg-gpid-junction-target-$$"
$tempJunction = Join-Path $env:TEMP "cg-gpid-junction-link-$$"
```

The intent was to get the current process ID so temp paths would not collide
across parallel runs. In testing:

- On the first command of a session `$$` expands to an **empty string**.
- On subsequent commands it expands to the **last token typed on the previous
  line** (e.g., `install.ps1`, or `True`).
- Two instances running simultaneously get the same "PID" value.
- The resulting paths are not unique and a duplicate-directory error is thrown.

## Root Cause

PowerShell's `$$` automatic variable contains the **last token of the last input
line**, not the current PID. This is a direct clash with the Unix shell convention
where `$$` is the process ID.

The correct PowerShell variables for process information are:
- `$PID` — current process ID (integer)
- `[System.Diagnostics.Process]::GetCurrentProcess().Id` — .NET equivalent

However, neither PID alone is truly collision-safe across script invocations that
start and finish quickly (PIDs are reused by the OS). A GUID is the safest choice
for temp-path uniqueness.

## Solution

Replace `$$` with a GUID-based name:

```powershell
# CORRECT — collision-proof across all scenarios
$guid         = [System.Guid]::NewGuid().ToString('N')   # 32 lowercase hex chars
$tempTarget   = Join-Path $env:TEMP "cg-gpid-junction-target-$guid"
$tempJunction = Join-Path $env:TEMP "cg-gpid-junction-link-$guid"
```

`ToString('N')` produces a compact 32-character hex string with no hyphens,
safe in directory names on all platforms.

If you genuinely need the PID (e.g., for a lock file keyed to the process):

```powershell
$tempPath = Join-Path $env:TEMP "myscript-$PID"
```

## Prevention

- **Never use `$$` in PowerShell** for unique names. Reserve it only for
  interactive use where its "last token" meaning is handy.
- Prefer `[System.Guid]::NewGuid().ToString('N')` whenever you need a temp path
  that must not collide.
- Code review checklist: flag any `$$` usage in `.ps1` files as a potential bug.

## Related

- [update.ps1 stderr fix](../git-workflows/2026-03-04-git-pull-stderr-redirect-swallows-errors.md) — sibling P1 fix from the same review session
- Microsoft docs: [about_Automatic_Variables](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_automatic_variables)
