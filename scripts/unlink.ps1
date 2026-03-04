# scripts/unlink.ps1
# Removes the Compound GPID junction from the current project's .github/.
# Does NOT delete any files in the global compound-gpid installation.
#
# Run this from your project root:
#   cg-unlink
#
# If a .github.bak backup exists (created by cg-link), you will be offered
# the option to restore it after unlinking.

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$TargetJunction = Join-Path (Get-Location) ".github"
$BackupPath     = Join-Path (Get-Location) ".github.bak"

# --- Check if .github exists ---
$existing = Get-Item -Path $TargetJunction -ErrorAction SilentlyContinue

if (-not $existing) {
    Write-Host ".github/ does not exist in this project. Nothing to unlink." -ForegroundColor Yellow
    exit 0
}

# --- Verify it is a junction (not a real directory) ---
if ($existing.LinkType -ne "Junction") {
    Write-Warning ".github/ exists but is a regular directory, not a junction."
    Write-Warning "Only junctions created by cg-link are managed by cg-unlink."
    Write-Warning "If you want to remove it manually, run: Remove-Item -Recurse .github"
    exit 1
}

# --- Confirm ---
Write-Host "This will remove the .github junction from this project."
Write-Host "The global Compound GPID installation is NOT affected."
$answer = Read-Host "Proceed? [y/N]"
if ($answer -notmatch "^[Yy]$") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

# --- Remove the junction ---
# Remove-Item on a junction removes the link only, never the target contents
Remove-Item -Path $TargetJunction -Force
Write-Host "Junction removed." -ForegroundColor DarkGray

# --- Offer to restore backup if it exists ---
if (Test-Path $BackupPath) {
    Write-Host ""
    Write-Host "A backup was found at .github.bak (created when you ran cg-link)."
    $restore = Read-Host "Restore .github.bak to .github? [y/N]"
    if ($restore -match "^[Yy]$") {
        Rename-Item -Path $BackupPath -NewName ".github"
        Write-Host "Restored .github.bak to .github/" -ForegroundColor Green
    } else {
        Write-Host ".github.bak left in place." -ForegroundColor DarkGray
    }
}

# --- Success ---
Write-Host ""
Write-Host "Unlinked." -ForegroundColor Green
Write-Host "Compound GPID prompts are no longer available in this project."
Write-Host "To re-link at any time, run: cg-link"
Write-Host ""
