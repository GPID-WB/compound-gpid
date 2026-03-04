# scripts/update.ps1
# Updates the global Compound GPID installation by running git pull.
# Because all projects use a junction to the same shared .github/ folder,
# this single command propagates changes to every linked project immediately.
#
# Run from anywhere:
#   cg-update

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$CompoundGpidDir = Join-Path $env:USERPROFILE ".compound-gpid"

# --- Validate install exists ---
if (-not (Test-Path $CompoundGpidDir)) {
    Write-Error @"
Compound GPID is not installed at: $CompoundGpidDir

Run the installer first:
  git clone https://github.com/GPID-WB/compound-gpid.git "$CompoundGpidDir"
  & "$CompoundGpidDir\install.ps1"
"@
    exit 1
}

# --- Verify git is available ---
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git is not available. Install Git from https://git-scm.com/download/win"
    exit 1
}

Push-Location $CompoundGpidDir

try {
    # Capture the commit hash before pulling so we can show what changed
    $before = git rev-parse --short HEAD 2>$null

    Write-Host "Checking for updates..." -ForegroundColor Cyan

    # --ff-only ensures we never end up in a merge conflict state
    # If the remote has diverged (shouldn't happen on main), it fails cleanly
    $pullOutput = git pull --ff-only 2>&1

    $after = git rev-parse --short HEAD 2>$null

    if ($before -ne $after) {
        Write-Host ""
        Write-Host "Updated: $before -> $after" -ForegroundColor Green
        Write-Host ""
        Write-Host "Changes:" -ForegroundColor Cyan
        # Show one-line log of new commits
        git log --oneline "$before..$after"
        Write-Host ""
        Write-Host "All linked projects see the changes immediately." -ForegroundColor DarkGray
    } else {
        Write-Host "Already up to date." -ForegroundColor Green
    }
} catch {
    Write-Error "git pull failed: $_"
    exit 1
} finally {
    # Always return to the original directory, even on error
    Pop-Location
}
