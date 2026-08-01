@echo off
rem bin/cg-index.cmd -- Compound GPID knowledge indexer (Windows)
rem
rem Resolves Python at invocation time: probes python3 -> python -> py.
rem All three candidates are verified against Windows Store stubs by checking
rem that `--version` output starts with "Python". Store stubs (including the
rem python3 alias on Windows 11) open the Store App instead of running Python.
rem
rem Each candidate is tested in its own for /f block (parsed independently)
rem so that `%ERRORLEVEL%` on `exit /b` correctly reflects the Python process
rem exit code -- not the pre-expansion value from the enclosing compound line.
rem
rem This file is the single source of truth. install.ps1 copies it to bin/
rem rather than generating from an inline string. Edit here, not in install.ps1.

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
call %PYTHON_CMD% "%~dp0..\scripts\cg_index.py" %*
exit /b %ERRORLEVEL%
