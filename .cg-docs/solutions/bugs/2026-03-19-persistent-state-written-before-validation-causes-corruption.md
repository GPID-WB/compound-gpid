---
date: 2026-03-19
title: "Persistent state file written before validation causes permanent corruption on bad input"
category: "bugs"
language: "both"
tags: [powershell, state-management, file-write, validation, atomicity, cg-version, version-pinning]
root-cause: "Set-Content was called at argument-parse time, before the tag was validated against the remote and before git checkout succeeded — meaning a bad tag name would be permanently written to .cg-version even though no checkout occurred"
severity: "P1"
---

# Persistent state file written before validation causes permanent corruption on bad input

## Problem

`cg-update v9.9.9` (a non-existent tag) would:
1. Write `v9.9.9` to `.cg-version` immediately on argument parse.
2. Fail on tag validation — `git tag --list` returns nothing for that tag.
3. Throw and exit with an error.

After this, every subsequent bare `cg-update` would read `v9.9.9` from `.cg-version` and fail again — permanently — until the user manually deleted or edited the file. The machine was stuck.

**Symptom**: `cg-update` consistently fails with "Release 'v9.9.9' not found" even when run with no arguments, for any user.

## Root Cause

The original code parsed arguments and immediately persisted the new version:

```powershell
# BUG: write at arg-parse time, before any validation
if ($Version -and $Version -ne "--list") {
    Set-Content -Path $VersionFile -Value $Version -NoNewline  # <-- too early
    $versionMode = $Version
}
```

The principle violated: **write persistent state only after the operation that validates it succeeds**.

This is analogous to writing a config file before confirming the connection it configures actually works.

## Solution

Move `Set-Content` to after the `git checkout` succeeds in the pinned-mode branch:

```powershell
# ---- Pinned mode ----

# 1. Fetch and validate first
$allTags   = @(git tag --list "v*" --sort=-version:refname 2>$null)
$tagExists = $versionMode -in $allTags
if (-not $tagExists) {
    throw "Release '$versionMode' not found. ..."
}

# 2. Checkout
try { git checkout $versionMode 2>$null } catch { <# ignore informational stderr #> }
if ($LASTEXITCODE -ne 0) {
    throw "git checkout $versionMode failed with exit code $LASTEXITCODE"
}

# 3. ONLY NOW write the preference — after both validation and checkout succeeded
Set-Content -Path $VersionFile -Value $versionMode -NoNewline
```

For the `latest` (unpin) mode, writing is also deferred until the branch is entered and only when the user explicitly passed `latest` as an argument:

```powershell
if ($versionMode -eq "latest") {
    # Persist only when the user explicitly passed "latest" (not just read from file)
    if ($Version -eq "latest") {
        Set-Content -Path $VersionFile -Value "latest" -NoNewline
    }
    # ... git pull ...
}
```

## Prevention

**Rule**: never write to a persistent preference/config file at argument-parse time. Always follow:

```
parse args → resolve intent → validate → execute → persist on success
```

Apply this pattern to any script that accepts user input and stores it:
- Validate the value is meaningful **in context** (not just syntactically valid).
- Only persist after the action it enables succeeds.
- On failure, leave the existing preference unchanged so the next run is not poisoned.

**Add a test** that verifies the file is NOT written when validation fails:

```powershell
It "does NOT write .cg-version when the tag does not exist" {
    $versionFile = Join-Path $TestDrive "cv-bad-tag.txt"
    Set-Content -Path $versionFile -Value "v0.1.0" -NoNewline   # existing pref

    $versionMode = "v9.9.9"
    $allTags     = @("v0.2.0", "v0.1.0")
    $wrote = $false
    try {
        if ($versionMode -notin $allTags) { throw "Release not found." }
        Set-Content -Path $versionFile -Value $versionMode -NoNewline
        $wrote = $true
    } catch { <# expected #> }

    $wrote                                 | Should Be $false
    (Get-Content $versionFile -Raw).Trim() | Should Be "v0.1.0"  # unchanged
}
```

## Related

- [`.cg-docs/solutions/git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md`](../git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md) — the try/catch + LASTEXITCODE pattern used in the checkout step
- [`.cg-docs/solutions/testing-patterns/2026-03-19-testing-powershell-switch-parameters.md`](../testing-patterns/2026-03-19-testing-powershell-switch-parameters.md) — the related test API fix discovered alongside this bug
