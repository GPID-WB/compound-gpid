# install.ps1
# One-time setup for Compound GPID.
# Run this after cloning the repo. Choose your install path:
#   - Local machine (OneDrive): & "C:\WBG\.compound-gpid\install.ps1"
#   - Remote server (no OneDrive): & "$env:USERPROFILE\.compound-gpid\install.ps1"
#
# What this does:
#   1. Verifies Git is available.
#   1b. Verifies Python is available (python3, python, or py -- required for cg-index).
#   2. Tests that directory junctions can be created on this machine.
#   3. Creates .cmd wrappers in bin\ and adds bin\ to the user PATH
#      so cg-link, cg-unlink, cg-update, cg-index, and cg-token-audit are available from any terminal.
#   4. Initializes .cg-version with "latest" (if not already set).
#
# Python requirement: Python 3.8+ is required (used by cg-index for knowledge indexing).
# The Windows Store installs Python stub launchers that are not real Python -- this
# script detects and skips them. Install from https://www.python.org/downloads/ or
# via winget: winget install Python.Python.3.11
#
# This script is idempotent - running it again updates the wrappers
# and PATH entry without creating duplicates. An existing .cg-version
# preference is preserved on upgrade.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# $PSScriptRoot is always the directory containing this script,
# regardless of where the user runs it from.
$CompoundGpidDir = $PSScriptRoot

. (Join-Path $CompoundGpidDir "scripts\helpers.ps1")

Write-Host ""
Write-Host "Compound GPID - Install" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

# -----------------------------------------------------------------------
# Step 1: Verify Git is available
# -----------------------------------------------------------------------
Write-Host "Checking for Git..." -ForegroundColor DarkGray
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error @"
Git is not available on this system.

Install Git from: https://git-scm.com/download/win
Then re-run this script.
"@
    exit 1
}
$gitVersion = git --version
Write-Host "  Found: $gitVersion" -ForegroundColor DarkGray

# -----------------------------------------------------------------------
# Step 1b: Verify Python is available
# -----------------------------------------------------------------------
# Required for cg-index and cg-token-audit. Probes python3 -> python -> py.
# All three candidates are verified against the Windows Store stub: Store stubs
# register aliases (including python3 on Windows 11) that open the Store App
# instead of running Python. Verification runs `<cmd> --version` and checks
# that the output starts with "Python".
Write-Host "Checking for Python..." -ForegroundColor DarkGray

function Test-PythonCandidate {
    param([string]$Cmd)
    if (-not (Get-Command $Cmd -ErrorAction SilentlyContinue)) { return $false }
    try {
        $ver = & $Cmd --version 2>&1
        # $ver may be a string or ErrorRecord; normalise to string
        $verStr = "$ver".Trim()
        return $verStr -match '^Python\s+\d'
    } catch {
        return $false
    }
}

$pythonFound = $false
foreach ($candidate in @("python3", "python", "py")) {
    if (Test-PythonCandidate $candidate) {
        $pythonVersion = & $candidate --version 2>&1
        Write-Host "  Found: $pythonVersion (via $candidate)" -ForegroundColor DarkGray
        $pythonFound = $true
        break
    }
}

if (-not $pythonFound) {
    Write-Error @"
Python is required but not found (checked: python3, python, py).

Install Python from: https://www.python.org/downloads/
Or via Microsoft Store: search for "Python 3" in the Store.
Or via winget: winget install Python.Python.3.11

Ensure python3, python, or py is on your PATH after installation.
Then re-run this script.
"@
    exit 1
}

# -----------------------------------------------------------------------
# Step 2: Test junction capability
# -----------------------------------------------------------------------
Write-Host "Testing junction capability..." -ForegroundColor DarkGray

# Use a GUID for uniqueness - $$ is not a PID in PowerShell (it's the last token)
$tempTarget   = Join-Path $env:TEMP "cg-gpid-junction-target-$([System.Guid]::NewGuid().ToString('N'))"
$tempJunction = Join-Path $env:TEMP "cg-gpid-junction-test-$([System.Guid]::NewGuid().ToString('N'))"

# Create a temporary target directory to link to
New-Item -ItemType Directory -Path $tempTarget -Force | Out-Null

$junctionOk = $false
try {
    New-Item -ItemType Junction -Path $tempJunction -Value $tempTarget -ErrorAction Stop | Out-Null
    $junctionOk = $true
} catch {
    # Junction creation failed - likely Developer Mode is off
}

# Clean up temp files regardless of outcome.
# Junction must be removed before the target so Windows can release the handle.
try {
    if (Test-Path $tempJunction) { Remove-Item -Path $tempJunction -Force }
} finally {
    if (Test-Path $tempTarget) { Remove-Item -Path $tempTarget -Force -Recurse }
}

if (-not $junctionOk) {
    Write-Warning @"

Directory junction creation failed on this machine.

Compound GPID uses junctions to link managed subdirectories (prompts/, skills/,
agents/, instructions/) inside your project's .github/ to the shared installation.
To enable them, turn on Developer Mode:
  Settings > System > For developers > Developer Mode (set to ON)

Then re-run this script.
"@
    # Don't exit - PATH wrappers do not depend on junction support, so the
    # user can still use the commands after enabling Developer Mode later.
    Write-Host "  Continuing install (PATH wrappers remain available)..." -ForegroundColor Yellow
} else {
    Write-Host "  Junctions supported." -ForegroundColor DarkGray
}

# -----------------------------------------------------------------------
# Step 3: Register cg-* commands via .cmd wrappers on PATH
# -----------------------------------------------------------------------
# Uses batch wrappers instead of PowerShell profile functions to avoid the
# Constrained Language Mode (CLM) dot-source restriction on enterprise machines
# where OneDrive redirects the Documents folder to an untrusted path.
Write-Host "Registering cg-* commands via PATH..." -ForegroundColor DarkGray

# Create bin/ directory inside the installation folder
$binDir = Join-Path $CompoundGpidDir "bin"
if (-not (Test-Path $binDir)) {
    New-Item -ItemType Directory -Path $binDir -Force | Out-Null
}

# Write the three .cmd wrappers (overwrite on upgrade to pick up latest content).
# %~dp0 resolves to the directory containing the .cmd file at call time,
# so the wrappers work regardless of which path the user cloned to.
$scripts = @("link", "unlink", "update")
foreach ($script in $scripts) {
    $cmdPath = Join-Path $binDir "cg-$script.cmd"
    $content  = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0..\scripts\$script.ps1`" %*`r`n"
    Set-Content -Path $cmdPath -Value $content -NoNewline
}
Write-Host "  Created: cg-link, cg-unlink, cg-update in $binDir" -ForegroundColor DarkGray

# Copy cg-index.cmd from the committed file (single source of truth). Unlike
# the simple PS1-calling wrappers above, cg-index.cmd contains non-trivial
# Python resolver logic and is kept as the committed authoritative wrapper in
# this same bin/ directory.
$cgIndexCmdSrc = Join-Path $CompoundGpidDir "bin\cg-index.cmd"
$cgIndexCmdDst = Join-Path $binDir "cg-index.cmd"
if (Test-Path $cgIndexCmdSrc) {
    $cgIndexSrcFull = [System.IO.Path]::GetFullPath($cgIndexCmdSrc)
    $cgIndexDstFull = [System.IO.Path]::GetFullPath($cgIndexCmdDst)
    if ($cgIndexSrcFull -ieq $cgIndexDstFull) {
        Write-Host "  Already present: cg-index in $binDir" -ForegroundColor DarkGray
    } else {
        Copy-Item -Path $cgIndexCmdSrc -Destination $cgIndexCmdDst -Force
        Write-Host "  Copied:  cg-index in $binDir" -ForegroundColor DarkGray
    }
} else {
    Write-Warning "  bin\cg-index.cmd not found in installation -- skipping cg-index wrapper."
}

# Verify cg-brain-init.cmd exists in bin/ (same pattern as cg-index.cmd).
$cgBrainInitCmdSrc = Join-Path $CompoundGpidDir "bin\cg-brain-init.cmd"
$cgBrainInitCmdDst = Join-Path $binDir "cg-brain-init.cmd"
if (Test-Path $cgBrainInitCmdSrc) {
    $cgBrainInitSrcFull = [System.IO.Path]::GetFullPath($cgBrainInitCmdSrc)
    $cgBrainInitDstFull = [System.IO.Path]::GetFullPath($cgBrainInitCmdDst)
    if ($cgBrainInitSrcFull -ieq $cgBrainInitDstFull) {
        Write-Host "  Already present: cg-brain-init in $binDir" -ForegroundColor DarkGray
    } else {
        Copy-Item -Path $cgBrainInitCmdSrc -Destination $cgBrainInitCmdDst -Force
        Write-Host "  Copied:  cg-brain-init in $binDir" -ForegroundColor DarkGray
    }
} else {
    Write-Warning "  bin\cg-brain-init.cmd not found in installation -- skipping cg-brain-init wrapper."
}

# Copy cg-token-audit.cmd from the committed file (same Python resolver pattern
# as cg-index.cmd).
$cgTokenAuditCmdSrc = Join-Path $CompoundGpidDir "bin\cg-token-audit.cmd"
$cgTokenAuditCmdDst = Join-Path $binDir "cg-token-audit.cmd"
if (Test-Path $cgTokenAuditCmdSrc) {
    $cgTokenAuditSrcFull = [System.IO.Path]::GetFullPath($cgTokenAuditCmdSrc)
    $cgTokenAuditDstFull = [System.IO.Path]::GetFullPath($cgTokenAuditCmdDst)
    if ($cgTokenAuditSrcFull -ieq $cgTokenAuditDstFull) {
        Write-Host "  Already present: cg-token-audit in $binDir" -ForegroundColor DarkGray
    } else {
        Copy-Item -Path $cgTokenAuditCmdSrc -Destination $cgTokenAuditCmdDst -Force
        Write-Host "  Copied:  cg-token-audit in $binDir" -ForegroundColor DarkGray
    }
} else {
    Write-Warning "  bin\cg-token-audit.cmd not found in installation -- skipping cg-token-audit wrapper."
}

# Add bin/ to user PATH (persistent across sessions - no dot-sourcing needed)
# Uses reg.exe as primary method (CLM-safe): [Environment]::SetEnvironmentVariable
# is blocked by Constrained Language Mode on enterprise machines.
$pathAdded = $false
try {
    $currentPath = (reg query "HKCU\Environment" /v PATH 2>$null |
        Where-Object { $_ -match 'PATH' }) -replace '.*REG_[A-Z_]+\s+', ''
    if ($currentPath) { $currentPath = $currentPath.Trim() } else { $currentPath = "" }
    if ($currentPath -notlike "*$binDir*") {
        if ($currentPath.Length -gt 0) { $newPath = "$binDir;$currentPath" } else { $newPath = $binDir }
        reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d $newPath /f | Out-Null
        Write-Host "  Added to PATH: $binDir" -ForegroundColor DarkGray
    } else {
        Write-Host "  Already on PATH: $binDir" -ForegroundColor DarkGray
    }
    # Broadcast WM_SETTINGCHANGE unconditionally so Explorer.exe and all running
    # processes (including VS Code terminals) pick up the current PATH immediately.
    # Must run every time install.ps1 is called, not just on first add.
    # setx is CLM-safe and triggers the broadcast as a side effect.
    & "$env:SystemRoot\System32\cmd.exe" /c "setx COMPOUND_GPID_INSTALLED 1 >nul 2>&1" | Out-Null
    $pathAdded = $true
} catch {
    Write-Warning "  Could not update PATH via reg.exe: $_"
    Write-Warning ('  Add manually: reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d "<your-current-path>;' + $binDir + '" /f')
}

# Clean up old profile wrappers from previous installs (upgrade path).
# Attempt cleanup but never fail install if $PROFILE is inaccessible (e.g. CLM).
try {
    $removedLegacyCommands = Remove-LegacyProfileCommands
    if ($null -ne $removedLegacyCommands -and @($removedLegacyCommands).Count -gt 0) {
        [void](Remove-CgLegacyLiveFunctions -CommandNames @($removedLegacyCommands))
    }
} catch {
    Write-Warning "  Could not clean up old profile commands: $_"
    Write-Warning "  You may manually remove the old Compound GPID functions from: $PROFILE"
}

Write-Host "  Registered: cg-link, cg-unlink, cg-update, cg-index, cg-token-audit" -ForegroundColor DarkGray

# -----------------------------------------------------------------------
# Step 4: Initialize .cg-version
# -----------------------------------------------------------------------
# Stores the user's version preference ("latest" or a tag like "v0.2.0").
# Created on first install only -- upgrade runs leave the existing value
# untouched so the user's pinned version is preserved.
Write-Host "Initializing version preference..." -ForegroundColor DarkGray
$versionFile = Join-Path $CompoundGpidDir ".cg-version"
if (-not (Test-Path $versionFile)) {
    Set-Content -Path $versionFile -Value "latest" -NoNewline
    Write-Host "  Created .cg-version: latest" -ForegroundColor DarkGray
} else {
    $existing = (Get-Content $versionFile -Raw).Trim()
    Write-Host "  Existing .cg-version preserved: $existing" -ForegroundColor DarkGray
}

# -----------------------------------------------------------------------
# Success
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "Compound GPID installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Location : $CompoundGpidDir"
Write-Host "  Commands : $binDir"
Write-Host ""
Write-Host "IMPORTANT: Restart VS Code / Positron and your terminal." -ForegroundColor Yellow
Write-Host "  The PATH change only takes effect in new processes." -ForegroundColor Yellow
Write-Host "  Copilot will not pick up changes until VS Code / Positron is restarted." -ForegroundColor Yellow
Write-Host ""
Write-Host "Available commands (after restarting):"
Write-Host "  cg-link    -- Link current project to Compound GPID  (run from project root)"
Write-Host "  cg-unlink  -- Unlink current project                 (run from project root)"
Write-Host "  cg-update  -- Pull latest updates                    (run from anywhere)"
Write-Host '  cg-update <version>  -- Pin to a specific release (e.g. cg-update v0.2.0)'
Write-Host "  cg-update latest     -- Unpin and return to tracking main"
Write-Host "  cg-update --list     -- Browse available releases"
Write-Host "  cg-index        -- Build knowledge index from .cg-docs/   (run from project root)"
Write-Host "  cg-token-audit  -- Analyze token/context usage          (run from project root)"
Write-Host ""
Write-Host "Quick start:"
Write-Host "  1. Restart VS Code / Positron and your terminal"
Write-Host "  2. cd to your project folder"
Write-Host "  3. Run: cg-link"
Write-Host "  4. Restart VS Code / Positron again so Copilot picks up the linked prompts"
Write-Host "  5. Open VS Code / Positron and run in Copilot Chat: /cg-setup"
Write-Host ""
