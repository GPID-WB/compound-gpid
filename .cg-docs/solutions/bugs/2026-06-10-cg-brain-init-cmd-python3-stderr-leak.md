---
date: 2026-06-10
title: "cg-brain-init.cmd leaks 'python3 not recognized' error to stderr when python3 absent from PATH"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-brain-init, windows, python, cmd, stderr, powershell, parity]
root-cause: "cg-brain-init.cmd used bare for /f subshell without where pre-check, unlike cg-index.cmd which was fixed earlier"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# cg-brain-init.cmd leaks 'python3 not recognized' error to stderr when python3 absent from PATH

## Problem

On Windows machines where Python is available as `python` or `py` but not `python3`,
running `cg-brain-init` leaked a CMD.EXE "not recognized" error to stderr:

```
'python3' is not recognized as an internal or external command,
operable program or batch file.
```

The tool failed silently or raised a PowerShell `NativeCommandError` even though
a valid Python interpreter was present on the machine.

## Root Cause

`cg-brain-init.cmd` used bare `for /f ('python3 --version 2^>^&1')` subshell blocks
without a `where python3 >nul 2>&1` pre-check. When `python3` is absent from PATH,
CMD.EXE emits its "not recognized" error **before** the `2>&1` redirect takes effect,
so the message escapes to the outer process's stderr.

This is a **parity gap**: `cg-index.cmd` had already been fixed with `where` pre-checks
(see `2026-06-05-cg-index-cmd-python3-stderr-leak.md`), but `cg-brain-init.cmd` was
not updated at the same time, leaving the same bug in both launchers.

## Solution

Added `where <cmd> >nul 2>&1` guards before each `for /f` block in `cg-brain-init.cmd`,
matching the pattern established in `cg-index.cmd`:

```batch
where python3 >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            python3 "%~dp0..\scripts\team_brain\init.py" %*
            exit /b %ERRORLEVEL%
        )
    )
)
```

Applied the same pattern for `python` and `py` candidates.

## Prevention

When a bug is fixed in one `.cmd` launcher, immediately check all other `.cmd`
launchers in `bin/` for the same pattern. The `where` pre-check rule must be
applied uniformly across all Python-probing `.cmd` files.

A parity test suite (`Describe "install.ps1 - cg-brain-init.cmd copy"`) was added
to `tests/install.Tests.ps1` to enforce the invariant going forward:

```powershell
($content -match 'where python3\s+>nul') | Should -Be $true
($content -match 'where python\s+>nul')  | Should -Be $true
($content -match 'where py\s+>nul')      | Should -Be $true
```

## Related

- [2026-06-05-cg-index-cmd-python3-stderr-leak.md](./2026-06-05-cg-index-cmd-python3-stderr-leak.md) — root fix; same bug in `cg-index.cmd`, diagnosed in detail there
