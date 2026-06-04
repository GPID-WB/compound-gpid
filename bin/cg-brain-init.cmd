@echo off
rem bin/cg-brain-init.cmd -- Team brain initialisation command (Windows)
rem One-time setup for the team brain manager: creates and scaffolds the
rem central GitHub repository for cross-project knowledge sharing.
rem
rem Usage:
rem   cg-brain-init --repo <owner/name> --manager <github-username>
rem
rem Example:
rem   cg-brain-init --repo GPID-WB/team-brain --manager wb384996
rem
rem Resolves Python at invocation time: probes python3 -> python -> py.
rem All three candidates are verified against Windows Store stubs by checking
rem that `--version` output starts with "Python". Store stubs open the Store
rem App instead of running Python.
rem
rem This file is the single source of truth. install.ps1 copies it to bin/
rem rather than generating from an inline string. Edit here, not in install.ps1.

setlocal

for /f "tokens=*" %%V in ('python3 --version 2^>^&1') do (
    echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
    if not errorlevel 1 (
        python3 "%~dp0..\scripts\team_brain\init.py" %*
        exit /b %ERRORLEVEL%
    )
)

for /f "tokens=*" %%V in ('python --version 2^>^&1') do (
    echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
    if not errorlevel 1 (
        python "%~dp0..\scripts\team_brain\init.py" %*
        exit /b %ERRORLEVEL%
    )
)

for /f "tokens=*" %%V in ('py --version 2^>^&1') do (
    echo %%V | findstr /i "^Python [0-9]" >nul 2>&1
    if not errorlevel 1 (
        py "%~dp0..\scripts\team_brain\init.py" %*
        exit /b %ERRORLEVEL%
    )
)

echo ERROR: Python is not available (checked: python3, python, py). >&2
echo Install from: https://www.python.org/downloads/ >&2
echo Or via winget: winget install Python.Python.3.11 >&2
exit /b 1
