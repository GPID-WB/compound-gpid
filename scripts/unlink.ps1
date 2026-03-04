# scripts/unlink.ps1
# Removes the Compound GPID junctions from the current project's .github/.
# Does NOT delete any files in the global compound-gpid installation.
#
# Handles both the legacy whole-directory junction (old cg-link behaviour)
# and the current per-subdirectory junction approach.
#
# Run this from your project root:
#   cg-unlink

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot     = Get-Location
$TargetGithubDir = Join-Path $ProjectRoot ".github"
$gitignorePath   = Join-Path $ProjectRoot ".gitignore"

# Subdirectories managed by Compound GPID
$ManagedDirs = @("prompts", "skills", "agents", "instructions")

# The management marker used in copilot-instructions.md
$CopilotInstructionsMarker = "<!-- compound-gpid:managed -->"
$CopilotInstructionsDest   = Join-Path $TargetGithubDir "copilot-instructions.md"

# --- Check if .github exists ---
$githubItem = Get-Item -Path $TargetGithubDir -ErrorAction SilentlyContinue

if (-not $githubItem) {
    Write-Host ".github/ does not exist in this project. Nothing to unlink." -ForegroundColor Yellow
    exit 0
}

# --- Handle legacy: .github/ itself is a whole-directory junction ---
if ($githubItem.LinkType -eq "Junction") {
    # .Target is string[] in PS 5.1 - join before comparing
    if (($githubItem.Target -join '') -notlike "*compound-gpid*") {
        Write-Warning ".github/ is a junction but does not point to compound-gpid: $($githubItem.Target)"
        Write-Warning "Only junctions created by cg-link are managed by cg-unlink."
        exit 1
    }

    Write-Host "Found legacy whole-directory junction. Removing..."
    $answer = Read-Host "Remove the .github junction from this project? [y/N]"
    if ($answer -notmatch "^[Yy]$") {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
    # Remove-Item on a junction removes the link only, not the target contents
    Remove-Item -Path $TargetGithubDir -Force
    Write-Host "Legacy junction removed." -ForegroundColor Green
    Write-Host ""
    Write-Host "Unlinked." -ForegroundColor Green
    Write-Host "Run cg-link to re-link using the current per-subdirectory approach."
    exit 0
}

# --- Per-subdirectory unlink ---
Write-Host ""
Write-Host "Compound GPID - Unlink" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will remove Compound GPID junctions from .github/ in this project."
Write-Host "The global Compound GPID installation is NOT affected."
$answer = Read-Host "Proceed? [y/N]"
if ($answer -notmatch "^[Yy]$") {
    Write-Host "Aborted." -ForegroundColor Yellow
    exit 0
}

$removedAny = $false

# Remove per-subdirectory junctions
foreach ($dir in $ManagedDirs) {
    $junctionPath = Join-Path $TargetGithubDir $dir
    $item = Get-Item -Path $junctionPath -ErrorAction SilentlyContinue

    if (-not $item) {
        Write-Host "  $dir/ - not found, skipping" -ForegroundColor DarkGray
        continue
    }

    if ($item.LinkType -eq "Junction") {
        # .Target is string[] in PS 5.1 - join before comparing
        if (($item.Target -join '') -like "*compound-gpid*") {
            Remove-Item -Path $junctionPath -Force
            Write-Host "  $dir/ - junction removed" -ForegroundColor DarkGray
            $removedAny = $true
        } else {
            Write-Host "  $dir/ - junction not from compound-gpid, skipping" -ForegroundColor Yellow
        }
    } else {
        Write-Host "  $dir/ - real directory (not a junction), skipping" -ForegroundColor Yellow
    }
}

# Remove copilot-instructions.md only if it carries the management marker
if (Test-Path $CopilotInstructionsDest) {
    $content = Get-Content $CopilotInstructionsDest -Raw -ErrorAction SilentlyContinue
    if ($content -and $content -match [regex]::Escape($CopilotInstructionsMarker)) {
        Remove-Item -Path $CopilotInstructionsDest -Force
        Write-Host "  copilot-instructions.md - removed (was CG-managed)" -ForegroundColor DarkGray
        $removedAny = $true
    } else {
        Write-Host "  copilot-instructions.md - user-managed (no marker), leaving in place" -ForegroundColor Yellow
    }
} else {
    Write-Host "  copilot-instructions.md - not found, skipping" -ForegroundColor DarkGray
}

# If .github/ is now empty, remove the directory
$remainingItems = Get-ChildItem -Path $TargetGithubDir -Force -ErrorAction SilentlyContinue
if (($remainingItems | Measure-Object).Count -eq 0) {
    Remove-Item -Path $TargetGithubDir -Force
    Write-Host "  .github/ - empty after unlinking, directory removed" -ForegroundColor DarkGray
}

# --- Remove CG-specific .gitignore entries ---
if (Test-Path $gitignorePath) {
    $giContent = Get-Content $gitignorePath -Raw -ErrorAction SilentlyContinue
    if ($giContent) {
        # Remove the CG-managed gitignore block, identified by its header comment
        # Also handles the old-style single ".github" entry added by the legacy linker
        $updated = $giContent -replace "(?m)^# Compound GPID managed items.*\r?\n(\.github/.*\r?\n)*", ""
        $updated = $updated -replace "(?m)^# Compound GPID \(junction \+ backup.*\r?\n(\.github.*\r?\n)*", ""
        if ($updated -ne $giContent) {
            Set-Content -Path $gitignorePath -Value $updated.TrimEnd()
            Write-Host "  .gitignore - CG entries removed" -ForegroundColor DarkGray
        }
    }
}

# --- Done ---
Write-Host ""
if ($removedAny) {
    Write-Host "Unlinked." -ForegroundColor Green
} else {
    Write-Host "Nothing to unlink - no Compound GPID junctions found." -ForegroundColor Yellow
}
Write-Host "Compound GPID prompts are no longer available in this project."
Write-Host "To re-link at any time, run: cg-link"
Write-Host ""
