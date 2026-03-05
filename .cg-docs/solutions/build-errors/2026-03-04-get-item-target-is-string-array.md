---
date: 2026-03-04
title: "Get-Item .Target property is string[] in PowerShell 5.1, not a scalar string"
category: "build-errors"
language: "both"
tags: [powershell, junctions, symlinks, get-item, target, string-array, comparison]
root-cause: "Get-Item.Target returns string[] (an array of strings) in PS 5.1 for junctions and symlinks; using -like or -eq directly on an array returns an array of matching elements (truthy if non-empty) rather than a boolean — producing misleading results"
severity: "P2"
---

# `Get-Item .Target` Is `string[]` in PowerShell 5.1, Not a Scalar String

## Problem

Code that checks whether a junction points to a specific directory passed all unit
tests but produced confusing results in edge cases:

```powershell
# WRONG - misleading result for string[] .Target
$item = Get-Item ".github/prompts"
if ($item.Target -like "*compound-gpid*") {
    Write-Host "This is ours"
}
```

The intent is a boolean check. In practice:

- `$item.Target` is `string[]`, not `string`.
- `-like` on an array returns **all matching elements** (a filtered array), not
  `$true`/`$false`.
- An empty array is falsy; a non-empty matching array is truthy — so the `if`
  block *happens* to work for the common case.
- But code reviewers reading `$item.Target -like "pattern"` expect a boolean
  comparison and will misunderstand the code.
- If `.Target` ever contains multiple entries (rare but possible for some link
  types), the behaviour is surprising: `-like` returns the subset that matched,
  not `$true` or `$false`.
- `-eq` on an array is even more dangerous: `$item.Target -eq "exact-string"`
  returns the filtered array, which is truthy even when you expected `$false`.

## Root Cause

In PowerShell 5.1, `[System.IO.FileSystemInfo].Target` (exposed as the `.Target`
property by `Get-Item`) is typed as `string[]` (an array of link targets) because
a single filesystem object can technically have multiple targets (e.g., hardlinks).
For junctions it always contains exactly one element, but the type is still `string[]`.

PowerShell applies `-like` and `-eq` to each element of an array and returns the
**matching elements**, not a boolean — this is [array filtering semantics](https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/everything-about-arrays).

```powershell
PS> (Get-Item ".github/prompts").Target.GetType().FullName
System.String[]

PS> (Get-Item ".github/prompts").Target -like "*compound-gpid*"
C:\Users\user\.compound-gpid\.github\prompts   # an array element, NOT $true
```

## Solution

Join the array to a scalar string before comparing:

```powershell
# CORRECT - explicit scalar comparison
$item = Get-Item ".github/prompts" -ErrorAction SilentlyContinue

if ($item.LinkType -eq "Junction" -and ($item.Target -join '') -like "*compound-gpid*") {
    Write-Host "This is a compound-gpid junction"
}
```

`-join ''` on a single-element array produces the scalar string. On a
multi-element array it concatenates — which is still safe for a contains-check.

For exact equality:

```powershell
# Exact path match
$expectedTarget = "$env:USERPROFILE\.compound-gpid\.github\prompts"
if (($item.Target -join '') -eq $expectedTarget) { ... }
```

## Prevention

- **Rule**: Always use `($item.Target -join '')` before any string comparison on
  `.Target` from `Get-Item`.
- **Pattern**: Check `$item.LinkType` first (it IS a scalar string), then check
  `.Target`.
- **Code review**: flag any `$x.Target -like` or `$x.Target -eq` without
  `-join ''` as a bug.
- This also applies to `.Target` on `[System.IO.FileInfo]` and
  `[System.IO.DirectoryInfo]` objects obtained via `Get-ChildItem`.

```powershell
# Standard pattern for junction ownership check
function Test-IsCGJunction {
    param([System.IO.FileSystemInfo]$Item)
    return $Item.LinkType -eq "Junction" -and
           ($Item.Target -join '') -like "*compound-gpid*"
}
```

## Related

- [PowerShell `$$` is not PID](../build-errors/2026-03-04-powershell-dollar-dollar-is-not-pid.md) — another PS 5.1 surprise
- PowerShell docs: [Everything you wanted to know about arrays](https://learn.microsoft.com/en-us/powershell/scripting/learn/deep-dives/everything-about-arrays)
- PowerShell docs: [about_Comparison_Operators — Array filtering](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_comparison_operators)
