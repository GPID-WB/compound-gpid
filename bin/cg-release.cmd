@echo off
rem Argument-preserving optional GPID wrapper. Never resolves itself through PATH.
setlocal
where python3 >nul 2>&1
if not errorlevel 1 (
    for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
        echo %%V | findstr /i /r /c:"^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call python3 -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
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
        echo %%V | findstr /i /r /c:"^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
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
        echo %%V | findstr /i /r /c:"^Python [0-9]" >nul 2>&1
        if not errorlevel 1 (
            call py -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)" >nul 2>&1
            if not errorlevel 1 (
                set "PYTHON_CMD=py"
                goto run_python
            )
        )
    )
)
echo ERROR: cg-release requires Python 3.11 or later and its locked package installation. >&2
exit /b 1
:run_python
call %PYTHON_CMD% "%~dp0..\scripts\cg_release_cli.py" %*
exit /b %ERRORLEVEL%
