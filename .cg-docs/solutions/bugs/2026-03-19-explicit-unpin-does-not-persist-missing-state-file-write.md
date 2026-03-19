---
date: 2026-03-19
title: "Explicit-unpin command does not persist when the target branch does not write back to state file"
category: "bugs"
language: "both"
tags: [powershell, state-management, cg-version, version-pinning, unpin, latest, regression]
root-cause: "The 'latest' (unpin) code path only read from .cg-version — it never wrote 'latest' back, so unpinning with 'cg-update latest' appeared to succeed but the old tag was re-applied on the next bare cg-update call"
severity: "P2"
---

# Explicit-unpin command does not persist when the target branch does not write back to state file

## Problem

After pinning to `v0.2.0` with `cg-update v0.2.0`, running `cg-update latest` appeared to succeed:
- The working tree switched back to `main`.
- `git pull` ran and showed "up to date" or new commits.

But on the next bare `cg-update` call, the output showed:

```
Mode: pinned (v0.2.0)
Checking out v0.2.0...
```

The unpin did not persist. `.cg-version` still contained `v0.2.0`.

## Root Cause

The pinned-mode branch correctly called `Set-Content` (after the fix for the write-before-validate bug). The latest-mode branch was never given an equivalent write.

```powershell
# latest mode — missing write
if ($versionMode -eq "latest") {
    # git pull ran fine here, but nothing wrote "latest" back to .cg-version
}
```

The only way `.cg-version` could contain `latest` was if the user ran install.ps1 fresh (which initialises to `latest`) or if they manually edited the file.

## Solution

In the latest-mode branch, write `"latest"` back to `.cg-version` when the user explicitly passed `latest` as an argument. This covers the explicit-unpin case without overwriting the file on every bare `cg-update` run (which is harmless but unnecessary).

```powershell
if ($versionMode -eq "latest") {
    # Persist the "latest" preference when the user explicitly unpins.
    # Safe to write before git ops: "latest" is always a valid value.
    if ($Version -eq "latest") {
        Set-Content -Path $VersionFile -Value "latest" -NoNewline
    }

    # ... detached HEAD check, git pull, etc. ...
}
```

`$Version` holds the raw user argument (or `$null` if none was supplied), so `$Version -eq "latest"` is only true for the explicit `cg-update latest` call — not for bare `cg-update` runs that resolved `latest` from the file.

## Prevention

When implementing a multi-mode command where modes are stored in a state file:

1. **Every mode that can be entered via a user argument must also write that mode to the state file.** Even if the mode is the default, an explicit argument signals user intent and must be persisted.
2. **Test the entire round-trip**, not just the individual write. A test for "pin → unpin → bare update stays on latest" catches this class of bug:

```powershell
It "re-reads 'latest' after an explicit unpin" {
    $versionFile = Join-Path $TestDrive "cv-roundtrip.txt"
    Set-Content -Path $versionFile -Value "v0.1.0" -NoNewline  # pinned state

    # Simulate: user runs cg-update latest
    $Version = "latest"
    if ($Version -eq "latest") {
        Set-Content -Path $versionFile -Value "latest" -NoNewline
    }

    # Simulate: next bare cg-update reads file
    $versionMode = (Get-Content $versionFile -Raw).Trim()
    $versionMode | Should Be "latest"  # would FAIL without the write
}
```

## Related

- [`.cg-docs/solutions/bugs/2026-03-19-persistent-state-written-before-validation-causes-corruption.md`](./2026-03-19-persistent-state-written-before-validation-causes-corruption.md) — the paired bug: write-before-validate in the pinned branch
