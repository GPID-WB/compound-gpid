---
applyTo: "**/*.ps1,**/*.cmd,**/bin/*"
---

# PowerShell and CMD Launcher Coding Standards

## General PowerShell

- Always begin scripts with `Set-StrictMode -Version Latest` and `$ErrorActionPreference = "Stop"`.
- Use `$PSScriptRoot` for paths relative to the script location — never rely on `$PWD`.
- Use `Get-Command <cmd> -ErrorAction SilentlyContinue` before invoking external commands; never assume they exist.
- Prefer `Write-Host` for user-facing output. Use `-ForegroundColor` for status messages.
- Never use `Write-Host` for machine-readable output — use `Write-Output` or return values instead.
- Use `$([System.Guid]::NewGuid().ToString('N'))` for unique temp names — `$$` is not a PID in PowerShell.
- Always clean up temp files in a `finally` block or unconditional cleanup section.
- Prefer `Test-Path` before `Get-Content` or `New-Item` to give actionable error messages.

## CMD Launcher Files (`bin/*.cmd`)

CMD wrappers in `bin/` launch Python scripts and must probe multiple Python candidates
(`python3` → `python` → `py`) silently and gracefully.

### Python Probe Pattern — Required Structure

Every Python-probing `.cmd` file **must** use this exact pattern for each candidate:

```batch
where <cmd> >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('<cmd> --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call <cmd> "%~dp0..\scripts\<entrypoint>.py" %*
            exit /b %ERRORLEVEL%
        )
    )
)
```

**Why the `where` pre-check is mandatory**: `for /f ('cmd --version 2^>^&1')` runs in a
CMD subshell. When `cmd` is absent from PATH, CMD.EXE emits the "'cmd' is not recognized"
error *before* the `2>&1` redirect fires — the message escapes to the outer process's
stderr. PowerShell intercepts this as a `NativeCommandError`, halting execution before
the next fallback candidate is tried.

The `where <cmd> >nul 2>&1` guard exits non-zero immediately when the command is absent,
so the `for /f` subshell is never entered.

Use `call` for version gates and final execution outside the `for /f` subshell.
Real Python executables behave normally, while `.cmd` shims return control to the
launcher instead of replacing the current batch context. This keeps fallback
selection and child exit-code propagation testable and correct.

**Anti-pattern — DO NOT USE:**

```batch
rem ❌ Missing where guard — leaks stderr when python3 absent
for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
    ...
)
```

### Parity Rule

When fixing a Python probe bug in one `.cmd` file, **immediately audit all other `.cmd`
files in `bin/`** for the same pattern and apply the fix everywhere at the same time.
Parity gaps have caused repeated bugs (see `.cg-docs/solutions/bugs/`).

Current `.cmd` launchers requiring this pattern:
- `bin/cg-index.cmd` — invokes `scripts/cg_index.py`
- `bin/cg-brain-init.cmd` — invokes `scripts/team_brain/init.py`
- `bin/cg-link.cmd`, `bin/cg-unlink.cmd`, `bin/cg-update.cmd` — check if they invoke Python

### Test Coverage for `.cmd` Launchers

Every `.cmd` launcher must have a corresponding test `Describe` block in `tests/install.Tests.ps1`
(or a dedicated test file) asserting:

1. The file exists in `bin/`.
2. It contains `for /f` (Python resolution pattern).
3. It guards **each** Python candidate with `where <cmd> >nul`.
4. It references the correct entrypoint script.

```powershell
# Required test assertions for each .cmd file
($content -match 'where python3\s+>nul') | Should -Be $true
($content -match 'where python\s+>nul')  | Should -Be $true
($content -match 'where py\s+>nul')      | Should -Be $true
```

## See Also

- `.cg-docs/solutions/bugs/2026-06-05-cg-index-cmd-python3-stderr-leak.md` — original diagnosis
- `.cg-docs/solutions/bugs/2026-06-10-cg-brain-init-cmd-python3-stderr-leak.md` — parity gap instance
- Load `cg-skill-windows-cmd-python-detection` before writing or reviewing any `bin/*.cmd` Python probe block
