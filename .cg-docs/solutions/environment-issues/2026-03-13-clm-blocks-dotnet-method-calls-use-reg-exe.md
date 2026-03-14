---
date: 2026-03-13
title: "CLM blocks .NET method calls — use reg.exe for PATH manipulation"
category: "environment-issues"
language: "both"
tags: [powershell, clm, constrained-language-mode, dotnet, environment-variable, PATH, reg-exe, applocker, wdac, enterprise]
root-cause: "Constrained Language Mode (CLM) enforced by AppLocker or WDAC blocks .NET static method calls like [Environment]::GetEnvironmentVariable — use reg.exe (a trusted native binary) instead"
severity: "P1"
---

# CLM Blocks .NET Method Calls — Use `reg.exe` for PATH Manipulation

## Problem

On WBG enterprise machines, calling `[Environment]::GetEnvironmentVariable` or
`[Environment]::SetEnvironmentVariable` in PowerShell throws:

```
Cannot invoke method. Method invocation is supported only on core types in this language mode.
    + CategoryInfo          : InvalidOperation: (:) [], RuntimeException
    + FullyQualifiedErrorId : MethodInvocationNotSupportedInConstrainedLanguage
```

This blocked the documented uninstall procedure (Step 2 — remove old PATH entry) and would also
block `install.ps1`'s PATH registration step.

## Root Cause

Constrained Language Mode (CLM) is enforced by AppLocker or Windows Defender Application Control
(WDAC). CLM restricts PowerShell to a safe subset of operations:

- `.NET` static method calls on non-core types are **blocked**
- `[Environment]::GetEnvironmentVariable` and `[Environment]::SetEnvironmentVariable` are blocked
- Native executables (`reg.exe`, `setx.exe`, `cmd.exe`) are **not blocked** — they run outside
  the PowerShell language engine

The user PATH is stored in the Windows registry at `HKCU\Environment`. Both `reg.exe` and
`setx.exe` can read/write it without going through .NET.

## Solution

### Reading the current user PATH

```powershell
# WRONG under CLM
$path = [Environment]::GetEnvironmentVariable('PATH', 'User')

# CORRECT — parse reg.exe output
$currentPath = (reg query "HKCU\Environment" /v PATH 2>$null |
    Where-Object { $_ -match 'PATH' }) -replace '.*REG_[A-Z_]+\s+', ''
```

### Writing a new user PATH (remove an entry)

```powershell
$oldBin  = "$env:USERPROFILE\.compound-gpid\bin"
$newPath = ($currentPath.Trim() -split ';' |
    Where-Object { $_ -and $_ -ne $oldBin }) -join ';'
reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d $newPath /f
```

### Adding an entry to user PATH

```powershell
$newBin  = "C:\WBG\.compound-gpid\bin"
$newPath = ($currentPath.Trim() -split ';' |
    Where-Object { $_ }) -join ';'
if ($newPath -notlike "*$newBin*") {
    $newPath = "$newPath;$newBin"
    reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d $newPath /f
}
```

### In scripts that must work in both CLM and full language mode

```powershell
# Attempt .NET first (works in full mode); fall back to reg.exe under CLM
try {
    [Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
} catch {
    reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d $newPath /f
}
```

## Prevention

- **Never use `[Environment]::*` for PATH** in scripts intended for enterprise WBG machines
- **Prefer `reg.exe`** for reading/writing `HKCU\Environment` — it is a signed system binary,
  always available, and CLM-safe
- **`setx` is an alternative** but has a 1024-character PATH limit and does not support
  `REG_EXPAND_SZ` — prefer `reg add` for reliability
- Always use `REG_EXPAND_SZ` (not `REG_SZ`) for PATH so that `%USERPROFILE%` and similar
  environment variable references expand correctly

## Related

- [`.cg-docs/solutions/environment-issues/2026-03-13-troubleshooting-doc-structure-readme-vs-manual.md`](./2026-03-13-troubleshooting-doc-structure-readme-vs-manual.md) — documentation structure for CLM-related issues
- [`.cg-docs/brainstorms/2026-03-13-clm-onedrive-install-fix.md`](../../brainstorms/2026-03-13-clm-onedrive-install-fix.md) — broader context of CLM/OneDrive install challenges
- [PowerShell Constrained Language Mode](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_language_modes)
