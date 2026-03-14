# install.ps1
# One-time setup for Compound GPID.
# Run this after cloning the repo (recommended path: C:\WBG\.compound-gpid):
#
#   & "C:\WBG\.compound-gpid\install.ps1"
#
# What this does:
#   1. Verifies Git is available.
#   2. Tests that directory junctions can be created on this machine.
#   3. Creates .cmd wrappers in bin\ and adds bin\ to the user PATH
#      so cg-link, cg-unlink, cg-update are available from any terminal.
#
# This script is idempotent - running it again updates the wrappers
# and PATH entry without creating duplicates.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# $PSScriptRoot is always the directory containing this script,
# regardless of where the user runs it from.
$CompoundGpidDir = $PSScriptRoot

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

# Clean up temp files regardless of outcome
if (Test-Path $tempJunction) { Remove-Item -Path $tempJunction -Force }
if (Test-Path $tempTarget)   { Remove-Item -Path $tempTarget -Force -Recurse }

if (-not $junctionOk) {
    Write-Warning @"

Directory junction creation failed on this machine.

Compound GPID uses junctions to link managed subdirectories (prompts/, skills/,
agents/, instructions/) inside your project's .github/ to the shared installation.
To enable them, turn on Developer Mode:
  Settings > System > For developers > Developer Mode (set to ON)

Then re-run this script.
"@
    # Don't exit - profile functions can still be registered so the user
    # is ready to go as soon as they enable Developer Mode.
    Write-Host "  Continuing install (profile functions will be registered)..." -ForegroundColor Yellow
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
    $content  = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File \"%~dp0..\scripts\$script.ps1\" %*`r`n"
    Set-Content -Path $cmdPath -Value $content -NoNewline
}
Write-Host "  Created: cg-link, cg-unlink, cg-update in $binDir" -ForegroundColor DarkGray

# Add bin/ to user PATH (persistent across sessions - no dot-sourcing needed)
$currentPath = [Environment]::GetEnvironmentVariable('PATH', 'User')
if (-not $currentPath) { $currentPath = "" }
if ($currentPath -notlike "*$binDir*") {
    $newPath = if ($currentPath.Length -gt 0) { "$currentPath;$binDir" } else { $binDir }
    [Environment]::SetEnvironmentVariable('PATH', $newPath, 'User')
    Write-Host "  Added to PATH: $binDir" -ForegroundColor DarkGray
} else {
    Write-Host "  Already on PATH: $binDir" -ForegroundColor DarkGray
}

# Clean up old $PROFILE block from previous installs (upgrade path).
# Attempt cleanup but never fail install if $PROFILE is inaccessible (e.g. CLM).
if (Test-Path $PROFILE -ErrorAction SilentlyContinue) {
    try {
        $profileContent = Get-Content -Path $PROFILE -Raw -ErrorAction SilentlyContinue
        if ($profileContent -and $profileContent -match "Compound GPID") {
            $cleaned = ($profileContent -replace "(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?", "").TrimEnd()
            Set-Content -Path $PROFILE -Value $cleaned -ErrorAction Stop
            Write-Host "  Removed old Compound GPID block from PowerShell profile." -ForegroundColor DarkGray
        }
    } catch {
        Write-Warning "  Could not clean up old profile block: $_"
        Write-Warning "  You may manually remove the '# --- Compound GPID' block from: $PROFILE"
    }
}

Write-Host "  Registered: cg-link, cg-unlink, cg-update" -ForegroundColor DarkGray

# -----------------------------------------------------------------------
# Success
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "Compound GPID installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Location : $CompoundGpidDir"
Write-Host "  Commands : $binDir"
Write-Host ""
Write-Host "IMPORTANT: Restart your terminal to pick up the PATH change." -ForegroundColor Yellow
Write-Host ""
Write-Host "Available commands (after restarting terminal):"
Write-Host "  cg-link    -- Link current project to Compound GPID  (run from project root)"
Write-Host "  cg-unlink  -- Unlink current project                 (run from project root)"
Write-Host "  cg-update  -- Pull latest updates                    (run from anywhere)"
Write-Host ""
Write-Host "Quick start:"
Write-Host "  1. Restart your terminal"
Write-Host "  2. cd to your project folder"
Write-Host "  3. Run: cg-link"
Write-Host "  4. Open VS Code and run in Copilot Chat: /cg-setup"
Write-Host ""
