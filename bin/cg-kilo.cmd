@echo off
set "PYTHON_CMD="

where python3 >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
        echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
            if not errorlevel 1 set "PYTHON_CMD=python3"
        )
    )
)

if not defined PYTHON_CMD (
    where python >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%V in ('python --version 2^>^&1') do (
            echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
            if not errorlevel 1 (
                call python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
                if not errorlevel 1 set "PYTHON_CMD=python"
            )
        )
    )
)

if not defined PYTHON_CMD (
    where py >nul 2>&1
    if not errorlevel 1 (
        for /f "tokens=*" %%V in ('py --version 2^>^&1') do (
            echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
            if not errorlevel 1 (
                call py -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
                if not errorlevel 1 set "PYTHON_CMD=py"
            )
        )
    )
)

if not defined PYTHON_CMD goto no_python

call %PYTHON_CMD% "%~dp0..\scripts\cg_kilo_preflight.py" --launch -- %*
exit /b %ERRORLEVEL%

:no_python
echo ERROR: Python 3.8+ is not available (checked: python3, python, py). >&2
echo Install from: https://www.python.org/downloads/ >&2
exit /b 1
