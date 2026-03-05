---
date: 2026-03-04
title: "Pester $TestDrive cleanup follows junction links, hanging VS Code"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, vscode, junctions, testdrive, freeze, cleanup, ms-vscode.powershell]
root-cause: "Pester 3.4 cleans up $TestDrive with Remove-Item -Recurse -Force, which on Windows follows directory junction links and recursively deletes junction targets — hanging the PowerShell Language Server and freezing VS Code"
severity: "P1"
---

# Pester `$TestDrive` Cleanup Follows Junction Links, Hanging VS Code

## Problem

VS Code froze completely and required a force-quit — reproducibly, every time the
workspace was opened. The freeze happened silently: no error messages, no crash
dialog.

Symptoms:
- VS Code becomes unresponsive within seconds of opening the workspace
- PowerShell terminal and IntelliSense stop responding
- Force-quitting and reopening causes the same freeze immediately
- Only occurs in workspaces that contain `*.Tests.ps1` files that create directory
  junctions

## Root Cause

Two interacting factors:

**Factor 1 — ms-vscode.powershell auto-runs tests on workspace open.**
The PowerShell extension v2024+ integrates with VS Code's native Testing API
(`useLegacyCodeLens: false` by default). This causes it to **automatically
discover and execute `*.Tests.ps1` files every time a workspace opens**, in order
to populate the Testing view sidebar with test results.

**Factor 2 — Pester 3.4 `$TestDrive` cleanup follows junction links.**
Pester uses `$TestDrive` (a temp directory) as a sandbox for file operations.
After each test run, Pester 3.4 cleans up `$TestDrive` with:
```powershell
Remove-Item -Path $TestDrive -Recurse -Force
```
On Windows, `-Recurse` **follows directory junction links** and deletes the
contents of the junction *target* — not just the link itself. When tests create
junctions inside `$TestDrive` pointing to real directories, cleanup recursively
deletes those real directories.

This operation hangs the PowerShell Language Server process (it can take minutes
or forever on deep directory trees), which hangs VS Code's entire PowerShell
integration.

The cycle: open workspace → extension auto-discovers tests → tests run → junctions
created in `$TestDrive` → Pester cleanup follows junctions → Language Server hangs
→ VS Code freezes.

## Solution

**Two fixes required — both are necessary:**

### Fix 1: Disable auto-test-discovery in `.vscode/settings.json`

```json
{
    "powershell.pester.useLegacyCodeLens": true
}
```

This reverts the extension to "legacy CodeLens" mode. Tests still show inline
**▶ Run Tests** / **⚙ Debug Tests** buttons above each `Describe` block, but
they only execute when you click them — never automatically on workspace open.

### Fix 2: Add `AfterAll` junction cleanup blocks to test files

Inside any `Describe` block that creates junctions, add an `AfterAll` that removes
them **before** Pester's `$TestDrive` cleanup fires:

```powershell
Describe "my feature - junction tests" {
    Context "creates junction" {
        It "junction has correct LinkType" {
            $target   = Join-Path $TestDrive "target"
            $junction = Join-Path $TestDrive "link"
            New-Item -ItemType Directory -Path $target  -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should Be "Junction"
        }
    }

    AfterAll {
        # Remove junctions before Pester's $TestDrive cleanup.
        # Scan shallow (1-2 levels) WITHOUT recursing into junctions.
        # If Remove-Item -Recurse hits a junction it will follow the link,
        # deleting target contents and potentially hanging the process.
        $level1 = Get-ChildItem -Path $TestDrive -Force -ErrorAction SilentlyContinue
        $level2 = $level1 |
            Where-Object { $_.PSIsContainer -and $_.LinkType -ne 'Junction' } |
            ForEach-Object { Get-ChildItem -Path $_.FullName -Force -ErrorAction SilentlyContinue }
        @($level1) + @($level2) |
            Where-Object { $_ -and $_.LinkType -eq 'Junction' } |
            ForEach-Object { Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue }
    }
}
```

**Key principle**: always remove a junction with `Remove-Item` *without* `-Recurse`.
`-Recurse` on a junction deletes the target contents. Without `-Recurse`, it
removes only the link.

## Prevention

- **Rule**: Never use `Remove-Item -Recurse -Force` on a path that might be a
  junction or contain junctions. Always check `(Get-Item $path).LinkType` first.
- **Rule**: Any `Describe` block that calls `New-Item -ItemType Junction` must
  have a matching `AfterAll` that removes those junctions by path (not recursively
  via `$TestDrive`).
- **Rule**: All workspaces with junction-creating tests must have
  `"powershell.pester.useLegacyCodeLens": true` in `.vscode/settings.json`.
- Add this to new project checklists: if tests touch the filesystem with junctions,
  add the `.vscode/settings.json` setting before the first VS Code open.

## Related

- [Pester 3.4 vs 5 syntax](2026-03-04-pester-3-vs-5-windows-compatibility.md) — companion Pester entry
- ms-vscode.powershell changelog: Testing API integration added in 2024.x
- PowerShell docs: [Remove-Item and junctions](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/remove-item)
