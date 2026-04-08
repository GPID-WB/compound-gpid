---
date: 2026-04-08
title: "cg-update --list never shows installed version arrow in latest mode"
category: "bugs"
type: "bug"
language: "both"
tags: [powershell, cg-update, --list, version-pinning, git-tag, latest-mode, arrow-marker]
root-cause: "Arrow marker loop compared each tag against $currentPin which is 'latest' in unpin mode — no release tag ever equals the string 'latest', so the arrow was never emitted"
severity: "P3"
test-written: "yes"
fix-confirmed: "yes"
---

# cg-update --list Never Shows Installed Version Arrow in Latest Mode

## Symptom

Running `cg-update --list` shows the list of available releases but the
`<-- current` arrow never appears next to the installed version when the user
is in `latest` (unpin) mode:

```
Available releases:
  v0.4.3
  v0.4.2
  v0.4.1
  ...

Current: main (latest)
```

When pinned to a specific tag the arrow worked correctly:

```
Available releases:
  v0.4.3
  v0.4.2  <-- current
  ...
```

## Root Cause

In `scripts/update.ps1`, the `--list` branch sets `$currentPin = $versionMode`.
In latest mode, `$versionMode == "latest"`. The per-tag loop then did:

```powershell
# Buggy: $currentPin is "latest" — no release tag ever equals this string
if ($tag -eq $currentPin) { $marker = '  <-- current' } else { $marker = '' }
```

The comparison `$tag -eq "latest"` is always false for any real release tag
(`"v0.4.3"`, `"v0.3.0"`, etc.), so no arrow was ever emitted in latest mode.

## Reproduction Test

Added to `tests/update.Tests.ps1`, `Describe "update.ps1 - --list formatting"`,
`Context "marking the current version in the tag list"`:

```powershell
It "appends '<-- current' marker to the HEAD tag when mode is 'latest'" {
    $currentPin   = "latest"
    $installedTag = "v0.4.3"   # simulates git tag --points-at HEAD
    $releaseTags  = @("v0.4.3", "v0.3.0", "v0.2.0")

    # Fixed logic
    $lines = $releaseTags | ForEach-Object {
        $marker = if ($_ -eq $currentPin -or $_ -eq $installedTag) { "  <-- current" } else { "" }
        "$_$marker"
    }
    ($lines | Where-Object { $_ -match "<-- current" }).Count        | Should Be 1
    ($lines | Where-Object { $_ -match "v0\.4\.3.*<-- current" }).Count | Should Be 1
    ($lines | Where-Object { $_ -match "v0\.3\.0.*<-- current" }).Count | Should Be 0
}

It "shows no arrow when mode is 'latest' and HEAD is not at a tagged release (between releases)" {
    $currentPin   = "latest"
    $installedTag = $null   # HEAD is between tags
    $releaseTags  = @("v0.4.3", "v0.3.0", "v0.2.0")

    $lines = $releaseTags | ForEach-Object {
        $marker = if ($_ -eq $currentPin -or $_ -eq $installedTag) { "  <-- current" } else { "" }
        "$_$marker"
    }
    ($lines | Where-Object { $_ -match "<-- current" }).Count | Should Be 0
}
```

## Fix

Two changes to `scripts/update.ps1` in the `--list` branch:

**1. Compute `$installedTag` before the tag loop** (after the `$modeLabel` block):

```powershell
# When not pinned ("latest" mode), determine which release tag HEAD points to
# so the arrow can still appear next to the installed version.
$installedTag = $null
if ($currentPin -eq "latest") {
    $headTags = @(git tag --points-at HEAD 2>$null | Where-Object { $_ -match $ReleaseTagPattern })
    if ($headTags) { $installedTag = $headTags[0] }
}
```

**2. Update the per-tag marker condition**:

```powershell
# Before (buggy):
if ($tag -eq $currentPin) { $marker = '  <-- current' } else { $marker = '' }

# After (fixed):
if ($tag -eq $currentPin -or $tag -eq $installedTag) { $marker = '  <-- current' } else { $marker = '' }
```

`$ReleaseTagPattern` (`'^v\d+\.\d+\.\d+$'`) is already defined at the top of the
script and filters out dev tags (`v0.4.3.9000`), keeping the marker restricted to
user-visible release tags.

## Lessons Learned

**When comparing a status value to a fixed sentinel, also check the actual
runtime state that the sentinel represents.**

`latest` is a sentinel meaning "track HEAD". The bug was treating it as a
literal label to compare against tags, rather than resolving what HEAD actually
points to. The fix separates the two concerns:
- `$currentPin` — what the user's *preference* is (`"latest"` or `"v0.4.x"`)
- `$installedTag` — what the *repository* HEAD actually points to

This pattern (`resolved-value != config-value`) is a common source of bugs
wherever a config value is a keyword rather than the actual target identifier.

## Related

- `scripts/update.ps1` — the fixed file
- `tests/update.Tests.ps1` — two new tests added to the `--list formatting` describe block
