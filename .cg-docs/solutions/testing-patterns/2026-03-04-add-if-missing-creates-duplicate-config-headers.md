---
date: 2026-03-04
title: "Add-if-missing config blocks create duplicate headers; use remove-then-rewrite"
category: "testing-patterns"
language: "both"
tags: [powershell, idempotency, gitignore, config-blocks, remove-then-rewrite, deduplication]
root-cause: "Checking for individual entries and appending only missing ones preserves the section header even when it already exists; when new entries are added in a later version the header is written again, producing duplicate blocks"
severity: "P2"
---

# Add-If-Missing Config Blocks Create Duplicate Headers: Use Remove-Then-Rewrite

## Problem

A script managed a named section in a text config file (`.gitignore`, a profile,
an `.ini`) using an "add if missing" strategy:

```powershell
# WRONG - add-if-missing approach for a named block
$header  = "# Compound GPID managed items"
$entries = @(".github/prompts/", ".github/skills/", ".github/agents/")

$content = Get-Content $file -Raw
foreach ($entry in $entries) {
    if ($content -notmatch [regex]::Escape($entry)) {
        # Entry missing - append it
    }
}
# When new entries exist, append a new block:
$entriesToAdd = $entries | Where-Object { $content -notmatch [regex]::Escape($_) }
if ($entriesToAdd) {
    Add-Content $file ("`n$header`n" + ($entriesToAdd -join "`n"))
}
```

After upgrading the tool and adding a new entry (e.g. `.github/instructions/`):

```
# .gitignore - BROKEN result after upgrade
# Compound GPID managed items
.github/prompts/
.github/skills/
.github/agents/

# Compound GPID managed items       <-- DUPLICATE HEADER
.github/instructions/
```

The existing entries are not duplicated, but the *header comment* is written again
for each run that has new entries. Over multiple upgrades the file accumulates
several identical headers, which confuses users and can break tooling that parses
the section.

## Root Cause

The "add if missing" check tests **individual entries** but not the **block
header**. Each time a new entry is added to the managed list, the code finds
"entries to add" and prepends the header comment before them. The header is never
tested for duplication, so it accumulates.

The same bug exists for profile blocks, `.npmrc` sections, hosts-file sections,
or any other keyed block managed by a script.

## Solution

Use the **remove-then-rewrite** pattern: always strip the entire named block first,
then append a complete fresh block. This is idempotent for any set of entries,
handles version upgrades, and never produces duplicates.

```powershell
# CORRECT - remove-then-rewrite
$marker  = "# Compound GPID managed items (junctions + copied file - do not commit)"
$entries = @(
    ".github/prompts/",
    ".github/skills/",
    ".github/agents/",
    ".github/instructions/"
)
$block = $marker + "`n" + ($entries -join "`n") + "`n"

if (Test-Path $file) {
    $existing = Get-Content $file -Raw -ErrorAction SilentlyContinue
    if (-not $existing) { $existing = "" }

    # Strip any existing CG block (regex covers the header + all .github/ lines beneath it)
    $stripped = ($existing -replace "(?m)^# Compound GPID managed items.*\r?\n(\.github/.*\r?\n)*", "").TrimEnd()

    $separator = if ($stripped.Length -gt 0) { "`n`n" } else { "" }
    Set-Content $file -Value ($stripped + $separator + $block)
} else {
    Set-Content $file -Value $block
}
```

The same pattern is used in `install.ps1` for the PowerShell profile `$PROFILE`
block:

```powershell
# From install.ps1 (profile idempotency)
$profileContent = $profileContent -replace "(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?", ""
Set-Content $PROFILE -Value $profileContent.TrimEnd()
Add-Content $PROFILE -Value $newBlock
```

## Prevention

- **Rule**: Never use "add if missing" for a named **block** (header + body).
  Use "add if missing" only for single standalone entries that have no header.
- **Rule**: Any managed block in a config file should have a unique, stable
  marker string (header comment) that the script can reliably find and remove.
- **Pattern**: The remove-then-rewrite cycle:
  1. Strip the old block with a regex that matches `header + all-body-lines`
  2. Trim trailing whitespace
  3. Append a complete fresh block
- **Test this explicitly**: write a test that runs the management function twice
  (or simulates a version upgrade with a new entry) and asserts the header appears
  exactly once.

```powershell
# Pester 3.4 test for idempotency
It "does not add duplicate section headers when run twice with new entries" {
    $file    = Join-Path $TestDrive "config.txt"
    $marker  = "# CG managed"
    $entries = @("entry-a", "entry-b")

    # First run
    $block1 = $marker + "`n" + ($entries -join "`n") + "`n"
    Set-Content $file $block1

    # Second run adds a new entry - remove-then-rewrite
    $all     = $entries + @("entry-c")
    $block2  = $marker + "`n" + ($all -join "`n") + "`n"
    $current = (Get-Content $file -Raw) -replace "(?m)^# CG managed.*\r?\n(entry.*\r?\n)*", ""
    Set-Content $file ($current.TrimEnd() + "`n`n" + $block2)

    $result = Get-Content $file
    ($result | Where-Object { $_ -eq $marker } | Measure-Object).Count | Should Be 1
    ($result | Where-Object { $_ -eq "entry-c" } | Measure-Object).Count | Should Be 1
}
```

## Related

- [PowerShell `$$` is not PID](../build-errors/2026-03-04-powershell-dollar-dollar-is-not-pid.md)
- `install.ps1` profile block management — reference implementation of remove-then-rewrite in this repo
