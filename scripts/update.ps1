# scripts/update.ps1
# Updates the global Compound GPID installation by running git pull.
# Because all projects use per-subdirectory junctions to the same shared
# .github/ subdirectories, this single command propagates changes to every
# linked project's prompts/, skills/, agents/, and instructions/ immediately.
#
# For copilot-instructions.md (a copied file, not a junction), this script also
# refreshes the copy in the current working directory if the management marker
# is present. Remove the marker to opt out of auto-refresh.
#
# Run from anywhere:
#   cg-update

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$CompoundGpidDir = Join-Path $env:USERPROFILE ".compound-gpid"

# The management marker that identifies a CG-managed copilot-instructions.md
$CopilotInstructionsMarker = "<!-- compound-gpid:managed -->"

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
    # Capture the commit hash before updating so we can show what changed
    $before = git rev-parse --short HEAD 2>$null

    Write-Host "Checking for updates..." -ForegroundColor Cyan

    # Reset any accidental local changes before pulling.
    # This handles the case where a user inadvertently edited a file through a
    # junction - git checkout discards uncommitted changes in the global clone.
    git checkout . 2>$null
    if ($LASTEXITCODE -ne 0) {
        Write-Warning "git checkout . returned exit code $LASTEXITCODE - continuing anyway"
    }

    # --ff-only ensures we never end up in a merge conflict state.
    # If the remote has diverged (shouldn't happen on main), it fails cleanly.
    # Write directly to terminal so any git messages (auth errors, etc.) are visible.
    git pull --ff-only
    if ($LASTEXITCODE -ne 0) {
        throw "git pull failed with exit code $LASTEXITCODE"
    }

    $after = git rev-parse --short HEAD 2>$null

    if ($before -ne $after) {
        Write-Host ""
        Write-Host "Updated: $before -> $after" -ForegroundColor Green
        Write-Host ""
        Write-Host "Changes:" -ForegroundColor Cyan
        # Show one-line log of new commits
        git log --oneline "$before..$after"
        Write-Host ""
        Write-Host "Managed subdirectories (prompts/, skills/, agents/, instructions/) are" -ForegroundColor DarkGray
        Write-Host "updated in all linked projects immediately via junctions." -ForegroundColor DarkGray
    } else {
        Write-Host "Already up to date." -ForegroundColor Green
    }
} catch {
    Write-Error "Update failed: $_"
    exit 1
} finally {
    # Always return to the original directory, even on error
    Pop-Location
}

# --- Refresh copilot-instructions.md in the current project (if linked) ---
# Junction-linked subdirectories update automatically. The copied
# copilot-instructions.md must be refreshed explicitly.
# We only update it if (a) the current directory looks like a linked project
# and (b) the file carries the management marker.
$cwdGithub      = Join-Path (Get-Location) ".github"
$cwdCopilotDest = Join-Path $cwdGithub "copilot-instructions.md"
$cgCopilotSrc   = Join-Path $CompoundGpidDir ".github\copilot-instructions.md"

# Skip refresh when called internally by cg-link (it handles its own Step 4 refresh)
if (-not $env:CG_INTERNAL_CALL -and
    (Test-Path $cwdGithub) -and (Test-Path $cwdCopilotDest) -and (Test-Path $cgCopilotSrc)) {
    $existing = Get-Content $cwdCopilotDest -Raw -ErrorAction SilentlyContinue
    if ($existing -and $existing -match [regex]::Escape($CopilotInstructionsMarker)) {
        $sourceContent = Get-Content $cgCopilotSrc -Raw
        Set-Content -Path $cwdCopilotDest -Value ($CopilotInstructionsMarker + "`n" + $sourceContent)
        Write-Host "Refreshed copilot-instructions.md in current project." -ForegroundColor DarkGray
    }
}

Write-Host ""
