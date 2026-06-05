---
date: 2026-06-05
title: "cg-index.cmd leaks 'python3 not recognized' error to stderr when python3 absent from PATH"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-index, windows, python, cmd, stderr, powershell]
root-cause: "for /f subshell cannot suppress CMD.EXE's 'not recognized' message before the 2>&1 redirect fires; a where pre-check is required"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
red-phase-confirmed: "yes"
expected-behavior-source: "documentation"
test-gap: "missing-test"
---

# cg-index.cmd leaks 'python3 not recognized' error to stderr when python3 absent from PATH

## Symptom

On Windows machines where Python is available as `python` or `py` but not `python3`,
running `cg-index --brain` raised a PowerShell `NativeCommandError`:

```
cg-index : 'python3' is not recognized as an internal or external command,
operable program or batch file.
```

The tool failed even though a valid Python interpreter was present on the machine.

## Expected Behavior Source

Documentation — the `bin/cg-index.cmd` header comment states: "Resolves Python at
invocation time: probes python3 -> python -> py." When `python3` is absent, the probe
must fall through silently with zero stderr output and find `python` or `py` instead.

## Root Cause

The `for /f ('python3 --version 2^>^&1')` construct runs `python3 --version` in a CMD
subshell. When `python3` does not exist on `PATH`, CMD.EXE emits the "not recognized"
error message **before** the `2>&1` redirect in the subshell takes effect — the message
escapes to the outer process's stderr. PowerShell intercepts this as a
`NativeCommandError`, halting execution before the `python` / `py` fallback blocks are
reached.

`install.ps1` avoids this correctly by calling `Get-Command -ErrorAction SilentlyContinue`
before attempting to invoke each candidate. The `.cmd` wrapper needed the same pattern
via `where <cmd> >nul 2>&1`.

## Reproduction Test

File: `tests/install.Tests.ps1`  
Describe block: `"install.ps1 - cg-index.cmd copy"` → Context `"single source of truth"`

```powershell
It "cg-index.cmd guards each python probe with a 'where' pre-check to prevent stderr leak" {
    $repoRoot = Split-Path $PSScriptRoot -Parent
    $cmdFile  = Join-Path $repoRoot "bin\cg-index.cmd"
    $content  = Get-Content $cmdFile -Raw
    ($content -match 'where python3\s+>nul') | Should -Be $true
    ($content -match 'where python\s+>nul')  | Should -Be $true
    ($content -match 'where py\s+>nul')      | Should -Be $true
}
```

## Test Gap

**missing-test** — The existing test only asserted that `for /f` appeared somewhere in
`cg-index.cmd`. It had no assertion verifying that each candidate was guarded with a
`where` pre-check. The absence of the guard was structurally invisible to the test suite.

## Fix

Added `where <cmd> >nul 2>&1 / if not errorlevel 1 (...)` wrappers around each `for /f`
block in `bin/cg-index.cmd`:

```batch
where python3 >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            python3 "%~dp0..\scripts\cg_index.py" %*
            exit /b %ERRORLEVEL%
        )
    )
)
```

Same pattern applied to `python` and `py` blocks. `where` exits non-zero immediately
when the command is absent, so the `for /f` subshell is never entered and CMD.EXE never
attempts to resolve the missing executable.

## Lessons Learned

**missing-test** gap: structural tests for `.cmd` wrappers should assert both the
presence of fallback logic *and* the guards that make silent fallthrough possible.
Testing only that a pattern (`for /f`) is present does not verify the surrounding
error-suppression structure.

Pattern to follow: when a script probes multiple candidates in sequence, add a test that
asserts the guard mechanism (here: `where >nul 2>&1`) exists for each candidate — not
just that the probe loop is present.

Anti-pattern that caused it: the test was written to verify the feature (Python
resolution) without verifying the error-isolation contract (no stderr leakage when a
candidate is absent).

## Related

None.
