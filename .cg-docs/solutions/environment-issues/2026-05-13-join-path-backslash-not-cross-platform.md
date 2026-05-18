---
date: 2026-05-13
title: "Join-Path with embedded backslash path separator is Windows-only"
category: "environment-issues"
language: "both"
tags: [powershell, cross-platform, join-path, path-separator, macos, linux, platform-guard, scripts]
root-cause: "Join-Path accepts a backslash-separated literal as its second argument but resolves it as a single path component (not a subdirectory chain) on macOS/Linux where \\ is a valid filename character, not a path separator"
severity: "P2"
---

# `Join-Path` with Embedded Backslash Path Separator is Windows-Only

## Problem

On Windows, `Join-Path $base "subdir\file.txt"` works correctly, producing
`$base\subdir\file.txt`. The same call on macOS/Linux resolves to
`$base/subdir\file.txt` — a single path component named `subdir\file.txt`
(a literal backslash in the filename). `Test-Path`, `Get-Content`, and other
cmdlets then fail silently: `Test-Path` returns `$false`, `Get-Content` throws
"file not found", and there is no error at the `Join-Path` call site.

This was the root cause of the `cg-link` macOS verification warning:

```powershell
# link.ps1 Step 6 — broken on macOS
$checkPath = Join-Path $TargetGithubDir "prompts\cg-setup.prompt.md"
# On macOS resolves to: /.../.github/prompts\cg-setup.prompt.md
# Test-Path returns $false even though the symlink is healthy
```

## Root Cause

PowerShell on macOS/Linux uses `/` as `[System.IO.Path]::DirectorySeparatorChar`.
The single-argument form of `Join-Path` does NOT split `"subdir\file.txt"` on `\`
before appending — it treats the entire string as one path component. Only the
multi-argument form `Join-Path $base "subdir" "file.txt"` calls `Combine()`
recursively on each segment, which is platform-safe.

## Solution

Use the **multi-argument form** of `Join-Path` whenever constructing a path with
more than one segment beyond the base:

```powershell
# ❌ Windows-only
$path = Join-Path $base "subdir\file.txt"

# ✅ Cross-platform
$path = Join-Path $base "subdir" "file.txt"
```

For paths with many segments, chain is equivalent to nesting:

```powershell
# ❌ Windows-only
$deep = Join-Path $root "a\b\c\file.txt"

# ✅ Cross-platform
$deep = Join-Path $root "a" "b" "c" "file.txt"
```

Note: the multi-argument form of `Join-Path` requires **PowerShell 3+**
(which is the minimum for this project). It is not available in PS 2.0.

## Prevention

**Rule**: never embed `\` as a path separator inside a `Join-Path` argument. Use one
path segment per argument. Enforce with a source-scan regression test:

```powershell
Describe "scripts do not use backslash path separators in Join-Path" {
    $psFiles = Get-ChildItem -Path (Join-Path $repoRoot "scripts") -Filter "*.ps1" -Recurse
    foreach ($file in $psFiles) {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        It "$($file.Name) has no Join-Path with embedded backslash" {
            # Allow \\server UNC paths and regex backslashes, but flag literal subdir\file patterns
            $content | Should -Not -Match 'Join-Path[^"'']*[''"][^''"\r\n]*\\[^''"\r\n]*[''"]'
        }
    }
}
```

**Companion rule**: any `.ps1` script that uses Windows-only filesystem primitives
(`New-Item -ItemType Junction`, `mklink`, `cmd /c mklink`) must include a platform
guard at the top that exits with a clear error on macOS/Linux:

```powershell
# Note: $IsWindows is PS6+ only. Use Test-Path guard for PS 5.1 Set-StrictMode compatibility.
$onWindows = ((Test-Path variable:IsWindows) -and $IsWindows -or $env:OS -eq "Windows_NT")
if (-not $onWindows) {
    Write-Error "This script is Windows-only. On macOS/Linux, use <equivalent>.sh instead."
    exit 1
}
```

## Related

- `.cg-docs/solutions/bugs/2026-05-13-link-ps1-runs-on-macos-verification-fails.md` — the specific bug where this pattern caused the `cg-link` macOS verification warning
- `.cg-docs/solutions/build-errors/2026-03-13-backslash-quote-in-powershell-string-breaks-percent-operator.md` — different backslash issue: `\"` in PS strings
- `.cg-docs/solutions/build-errors/2026-03-04-powershell-dollar-dollar-is-not-pid.md` — related: cross-platform PS scripting gotcha
