---
name: cg-skill-windows-cmd-python-detection
description: "Windows CMD launcher pattern for safe Python detection across python3/python/py candidates. Load when writing or reviewing any bin/*.cmd file that invokes a Python script. Covers: the mandatory 'where' pre-check guard, the for /f version-verification pattern, the Windows Store stub rejection logic, the parity rule (fix one cmd → audit all), and required test assertions. Prevents the stderr-leak NativeCommandError that occurs when python3 is absent from PATH."
---

# Windows CMD Python Detection

Use this skill when writing or reviewing any `bin/*.cmd` launcher that probes for Python.

---

## The Problem

CMD batch files that probe Python candidates using bare `for /f` subshells leak
`"'python3' is not recognized"` errors to stderr when `python3` is absent from PATH.
PowerShell intercepts this as a `NativeCommandError`, halting execution before the
`python` / `py` fallback is tried.

**Root cause**: CMD.EXE emits the "not recognized" message *before* the `2>&1` redirect
in the subshell takes effect. The message escapes the subshell to the outer process stderr.

---

## Required Pattern

Every Python candidate probe in a `bin/*.cmd` file must use this exact structure:

```batch
where python3 >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call python3 "%~dp0..\scripts\<entrypoint>.py" %*
            exit /b %ERRORLEVEL%
        )
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call python "%~dp0..\scripts\<entrypoint>.py" %*
            exit /b %ERRORLEVEL%
        )
    )
)

where py >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('py --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call py "%~dp0..\scripts\<entrypoint>.py" %*
            exit /b %ERRORLEVEL%
        )
    )
)

echo ERROR: Python is not available (checked: python3, python, py). >&2
echo Install from: https://www.python.org/downloads/ >&2
echo Or via winget: winget install Python.Python.3.11 >&2
exit /b 1
```

### Layer breakdown

| Layer | Purpose |
|-------|---------|
| `where <cmd> >nul 2>&1` | Pre-check: exits non-zero immediately if command absent — `for /f` never entered |
| `for /f ('cmd --version 2^>^&1')` | Captures version string from the real Python |
| `findstr /i "^Python [0-9]"` | Rejects Windows Store stubs (output: empty or "Python was not found") |
| `call python3 ... %*` | Delegates to executables or batch shims, returns control, and forwards all arguments |
| `exit /b %ERRORLEVEL%` | Propagates Python's exit code exactly |

Use `call` for every version-gate invocation and final interpreter execution.
Without it, a candidate implemented as a `.cmd` shim replaces the caller's batch
context, so fallback probing and child status propagation do not resume in the
launcher. `call` is harmless for real Python executables and required for shims.

---

## Anti-Patterns

```batch
rem ❌ MISSING where guard — leaks stderr to outer process
for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
    ...
)

rem ❌ NO version check — accepts Windows Store stubs
where python3 >nul 2>&1
if not errorlevel 1 (
    python3 "%~dp0..\scripts\foo.py" %*
    exit /b %ERRORLEVEL%
)

rem ❌ exit code not propagated, and a .cmd shim does not return
python3 "%~dp0..\scripts\foo.py" %*
exit /b 0
```

---

## Parity Rule

**When fixing this pattern in one `.cmd` file, immediately check ALL other `.cmd` files
in `bin/` for the same issue.** Parity gaps have repeatedly caused the same bug in sister
launchers after the root fix was applied.

Audit checklist for `bin/`:
- `cg-index.cmd` — ✅ fixed 2026-06-05
- `cg-brain-init.cmd` — ✅ fixed 2026-06-10
- `cg-link.cmd`, `cg-unlink.cmd`, `cg-update.cmd` — check on next touch (these may not invoke Python)

---

## install.ps1 Parity

`install.ps1` detects Python using `Get-Command <cmd> -ErrorAction SilentlyContinue`
before invoking. The `where` pre-check in `.cmd` files mirrors this pattern for CMD context.
Both must apply the same "pre-check before invoke" contract.

The PowerShell probe regex is `'^Python\s+\d'` — the same acceptance criterion as
`findstr /i "^Python [0-9]"` in the CMD launchers.

---

## Required Test Assertions

Every `.cmd` launcher must have a Pester `Describe` block in `tests/install.Tests.ps1`
with these assertions:

```powershell
Describe "install.ps1 - <launcher>.cmd copy" {
    Context "single source of truth" {
        It "<launcher>.cmd exists in the committed bin/ directory" {
            Test-Path (Join-Path $repoRoot "bin\<launcher>.cmd") | Should -Be $true
        }

        It "<launcher>.cmd contains the for /f Python resolution pattern" {
            ($content -match 'for /f') | Should -Be $true
        }

        It "<launcher>.cmd guards each python probe with a 'where' pre-check" {
            ($content -match 'where python3\s+>nul') | Should -Be $true
            ($content -match 'where python\s+>nul')  | Should -Be $true
            ($content -match 'where py\s+>nul')      | Should -Be $true
        }

        It "<launcher>.cmd references <entrypoint>.py" {
            ($content -match '<entrypoint>\.py') | Should -Be $true
        }
    }
}
```

---

## References

- `.cg-docs/solutions/bugs/2026-06-05-cg-index-cmd-python3-stderr-leak.md` — original diagnosis and fix
- `.cg-docs/solutions/bugs/2026-06-10-cg-brain-init-cmd-python3-stderr-leak.md` — parity gap instance
- `.github/instructions/powershell.instructions.md` — project-wide PowerShell and CMD coding standards
