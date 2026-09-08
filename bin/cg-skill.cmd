@echo off
rem bin/cg-skill.cmd -- Descriptor-driven skill lifecycle command (Windows)
rem
rem Resolves Python at invocation time: probes python3 -> python -> py.
rem Every probe uses a where pre-check and verifies a real Python 3.8+
rem interpreter before dispatch. This rejects Windows Store stubs without
rem leaking missing-command stderr into PowerShell.
rem
rem This file is the single source of truth. install.ps1 keeps it in bin/.

setlocal

where python3 >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
            if not errorlevel 1 (
                set "PYTHON_CMD=python3"
                goto run_python
            )
        )
    )
)

where python >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
            if not errorlevel 1 (
                set "PYTHON_CMD=python"
                goto run_python
            )
        )
    )
)

where py >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('py --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call py -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
            if not errorlevel 1 (
                set "PYTHON_CMD=py"
                goto run_python
            )
        )
    )
)

echo ERROR: Python is not available (checked: python3, python, py). >&2
echo Install from: https://www.python.org/downloads/ >&2
echo Or via winget: winget install Python.Python.3.11 >&2
exit /b 1

:run_python
call %PYTHON_CMD% "%~dp0..\scripts\cg_skill.py" %*
exit /b %ERRORLEVEL%
