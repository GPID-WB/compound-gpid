# scripts/link.ps1
# Links the current project to the global Compound GPID installation by creating
# a directory junction from .github/ to the shared compound-gpid/.github/.
#
# Run this from your project root:
#   cg-link
#
# Requirements:
#   - Compound GPID must be installed at $env:USERPROFILE\.compound-gpid
#   - Developer Mode enabled OR directory junctions available (default on Win10/11)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- Configuration ---
$CompoundGpidDir = Join-Path $env:USERPROFILE ".compound-gpid"
$SourceGithub    = Join-Path $CompoundGpidDir ".github"
$TargetJunction  = Join-Path (Get-Location) ".github"

# --- Validate global install exists ---
if (-not (Test-Path $CompoundGpidDir)) {
    Write-Error @"
Compound GPID is not installed at: $CompoundGpidDir

Run the installer first:
  git clone https://github.com/GPID-WB/compound-gpid.git "$CompoundGpidDir"
  & "$CompoundGpidDir\install.ps1"
"@
    exit 1
}

if (-not (Test-Path $SourceGithub)) {
    Write-Error "Expected .github/ not found inside $CompoundGpidDir. The installation may be corrupted."
    exit 1
}

# --- Check current state of .github in this project ---
$existing = Get-Item -Path $TargetJunction -ErrorAction SilentlyContinue

if ($existing) {
    if ($existing.LinkType -eq "Junction") {
        # Check if it already points to compound-gpid
        if ($existing.Target -like "*compound-gpid*") {
            Write-Host "Already linked to Compound GPID. Nothing to do." -ForegroundColor Green
            exit 0
        } else {
            # Junction points somewhere else — warn and offer to relink
            Write-Warning ".github/ is already a junction pointing to: $($existing.Target)"
            $answer = Read-Host "Relink it to Compound GPID instead? [y/N]"
            if ($answer -notmatch "^[Yy]$") {
                Write-Host "Aborted." -ForegroundColor Yellow
                exit 0
            }
            # Remove the existing junction (does NOT delete the target directory)
            Remove-Item -Path $TargetJunction -Force
        }
    } else {
        # Regular directory — offer to back it up before creating junction
        Write-Warning ".github/ exists as a regular directory in this project."
        Write-Warning "It will be renamed to .github.bak before linking."
        $answer = Read-Host "Back up .github/ to .github.bak and proceed? [y/N]"
        if ($answer -notmatch "^[Yy]$") {
            Write-Host "Aborted. Your .github/ directory is unchanged." -ForegroundColor Yellow
            exit 0
        }
        $backupPath = Join-Path (Get-Location) ".github.bak"
        if (Test-Path $backupPath) {
            Write-Error ".github.bak already exists. Remove or rename it first, then re-run cg-link."
            exit 1
        }
        Rename-Item -Path $TargetJunction -NewName ".github.bak"
        Write-Host "Backed up .github/ to .github.bak" -ForegroundColor Cyan
    }
}

# --- Create the junction ---
# New-Item -ItemType Junction creates a junction without requiring admin rights
# (Developer Mode or standard user junctions on Win10+)
try {
    New-Item -ItemType Junction -Path $TargetJunction -Target $SourceGithub | Out-Null
} catch {
    Write-Error @"
Failed to create junction: $_

If you see an access error, enable Developer Mode:
  Settings > System > For developers > Developer Mode (On)

Then re-run: cg-link
"@
    exit 1
}

# --- Verify the junction works by checking for a known file ---
$checkPath = Join-Path $TargetJunction "prompts\cg-setup.prompt.md"
if (-not (Test-Path $checkPath)) {
    Write-Warning "Junction created, but verification failed — prompts not visible at expected path."
    Write-Warning "Expected: $checkPath"
} else {
    Write-Host "Junction verified." -ForegroundColor DarkGray
}

# --- Add .github and .github.bak to .gitignore ---
# .github  — junction to external repo, must not be committed
# .github.bak — backup created by cg-link, should not be committed either
$gitignorePath = Join-Path (Get-Location) ".gitignore"

if (Test-Path $gitignorePath) {
    $content = Get-Content $gitignorePath -Raw
    # Only add if not already present (check for the entry as a whole line)
    if ($content -notmatch "(?m)^\s*\.github\s*$") {
        Add-Content -Path $gitignorePath -Value "`n# Compound GPID (junction + backup — neither should be committed)`n.github`n.github.bak"
        Write-Host "Added .github and .github.bak to .gitignore" -ForegroundColor DarkGray
    }
} else {
    # Create a minimal .gitignore if none exists
    Set-Content -Path $gitignorePath -Value "# Compound GPID (junction + backup — neither should be committed)`n.github`n.github.bak`n"
    Write-Host "Created .gitignore with .github and .github.bak entries" -ForegroundColor DarkGray
}

# --- Success ---
Write-Host ""
Write-Host "Linked!" -ForegroundColor Green
Write-Host ""
Write-Host "Compound GPID prompts are now available in this project."
Write-Host "Open VS Code and run in Copilot Chat:"
Write-Host "  /cg-setup" -ForegroundColor Cyan
Write-Host ""
