# install.ps1
# One-time setup for Compound GPID.
# Run this after cloning the repo:
#
#   & "$env:USERPROFILE\.compound-gpid\install.ps1"
#
# What this does:
#   1. Verifies Git is available.
#   2. Tests that directory junctions can be created on this machine.
#   3. Registers cg-link, cg-unlink, cg-update as functions in your
#      PowerShell profile so they are available from any terminal.
#
# This script is idempotent — running it again updates the profile block
# without creating duplicates.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# $PSScriptRoot is always the directory containing this script,
# regardless of where the user runs it from.
$CompoundGpidDir = $PSScriptRoot

Write-Host ""
Write-Host "Compound GPID — Install" -ForegroundColor Cyan
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

# Use a GUID for uniqueness — $$ is not a PID in PowerShell (it's the last token)
$tempTarget   = Join-Path $env:TEMP "cg-gpid-junction-target-$([System.Guid]::NewGuid().ToString('N'))"
$tempJunction = Join-Path $env:TEMP "cg-gpid-junction-test-$([System.Guid]::NewGuid().ToString('N'))"

# Create a temporary target directory to link to
New-Item -ItemType Directory -Path $tempTarget -Force | Out-Null

$junctionOk = $false
try {
    New-Item -ItemType Junction -Path $tempJunction -Target $tempTarget -ErrorAction Stop | Out-Null
    $junctionOk = $true
} catch {
    # Junction creation failed — likely Developer Mode is off
}

# Clean up temp files regardless of outcome
if (Test-Path $tempJunction) { Remove-Item -Path $tempJunction -Force }
if (Test-Path $tempTarget)   { Remove-Item -Path $tempTarget -Force -Recurse }

if (-not $junctionOk) {
    Write-Warning @"

Directory junction creation failed on this machine.

Compound GPID uses junctions to link projects to the shared .github/ folder.
To enable them, turn on Developer Mode:
  Settings > System > For developers > Developer Mode (set to ON)

Then re-run this script.
"@
    # Don't exit — profile functions can still be registered so the user
    # is ready to go as soon as they enable Developer Mode.
    Write-Host "  Continuing install (profile functions will be registered)..." -ForegroundColor Yellow
} else {
    Write-Host "  Junctions supported." -ForegroundColor DarkGray
}

# -----------------------------------------------------------------------
# Step 3: Register cg-* functions in the PowerShell profile
# -----------------------------------------------------------------------
Write-Host "Registering cg-* commands in PowerShell profile..." -ForegroundColor DarkGray

# Ensure the profile file and its parent directory exist
if (-not (Test-Path $PROFILE)) {
    New-Item -Path $PROFILE -ItemType File -Force | Out-Null
    Write-Host "  Created PowerShell profile at: $PROFILE" -ForegroundColor DarkGray
}

# Read existing profile content (empty string if file is empty)
$profileContent = Get-Content -Path $PROFILE -Raw -ErrorAction SilentlyContinue
if (-not $profileContent) { $profileContent = "" }

# Idempotency: only add the block if it isn't already there
if ($profileContent -match "Compound GPID") {
    Write-Host "  Profile already contains Compound GPID functions — updating..." -ForegroundColor DarkGray

    # Remove the existing block so we can replace it with the latest version.
    # This handles the case where the block content changes between versions.
    $profileContent = $profileContent -replace "(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?", ""

    Set-Content -Path $PROFILE -Value $profileContent.TrimEnd()
}

# The profile functions use $env:USERPROFILE which is resolved at call time,
# not at write time — so the path stays correct across machines and user renames.
# Single-quote here-string prevents variable expansion during the write.
$profileBlock = @'

# --- Compound GPID (managed by install.ps1 — do not edit manually) ---
function cg-link   { & "$env:USERPROFILE\.compound-gpid\scripts\link.ps1"   @args }
function cg-unlink { & "$env:USERPROFILE\.compound-gpid\scripts\unlink.ps1" @args }
function cg-update { & "$env:USERPROFILE\.compound-gpid\scripts\update.ps1" @args }
# --- End Compound GPID ---
'@

Add-Content -Path $PROFILE -Value $profileBlock
Write-Host "  Registered: cg-link, cg-unlink, cg-update" -ForegroundColor DarkGray

# -----------------------------------------------------------------------
# Success
# -----------------------------------------------------------------------
Write-Host ""
Write-Host "Compound GPID installed successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "  Location : $CompoundGpidDir"
Write-Host "  Profile  : $PROFILE"
Write-Host ""
Write-Host "IMPORTANT: Restart your terminal, or run:" -ForegroundColor Yellow
Write-Host "  . `$PROFILE" -ForegroundColor Yellow
Write-Host ""
Write-Host "Available commands (after restarting terminal):"
Write-Host "  cg-link    -- Link current project to Compound GPID  (run from project root)"
Write-Host "  cg-unlink  -- Unlink current project                 (run from project root)"
Write-Host "  cg-update  -- Pull latest updates                    (run from anywhere)"
Write-Host ""
Write-Host "Quick start:"
Write-Host "  1. Restart your terminal (or run: . `$PROFILE)"
Write-Host "  2. cd to your project folder"
Write-Host "  3. Run: cg-link"
Write-Host "  4. Open VS Code and run in Copilot Chat: /cg-setup"
Write-Host ""
