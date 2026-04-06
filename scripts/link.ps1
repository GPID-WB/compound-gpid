# scripts/link.ps1
# Links the current project to the global Compound GPID installation by creating
# per-subdirectory junctions inside .github/ for the managed Compound GPID
# directories (prompts/, skills/, agents/, instructions/) and copying
# copilot-instructions.md with a management marker.
#
# Run this from your project root:
#   cg-link
#
# Key behaviours:
#   - Creates .github/ as a real directory if it does not exist.
#   - Adds junctions only for CG-managed subdirectories, leaving all existing
#     .github/ content (workflows, templates, CODEOWNERS, etc.) untouched.
#   - Copies copilot-instructions.md with a <!-- compound-gpid:managed --> marker.
#     Removes the marker to take ownership of the file and prevent cg-update
#     from overwriting it.
#   - Runs cg-update first to ensure the global clone is up to date.
#   - Gitignores only the CG-managed items, not the entire .github/ folder.
#
# Requirements:
#   - Compound GPID must be installed (default: C:\WBG\.compound-gpid)
#   - Developer Mode enabled OR directory junctions available (default on Win10/11)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# --- Configuration ---
# Resolve the install location relative to this script's own directory
# (scripts/ -> parent = compound-gpid root). Works with any install path.
$CompoundGpidDir  = Split-Path $PSScriptRoot -Parent
$SourceGithub     = Join-Path $CompoundGpidDir ".github"
$ProjectRoot      = Get-Location
$TargetGithubDir  = Join-Path $ProjectRoot ".github"

. (Join-Path $PSScriptRoot "helpers.ps1")

# Subdirectories managed by Compound GPID (each gets its own junction)
$ManagedDirs = @("prompts", "skills", "agents", "instructions")

# The management marker that marks copilot-instructions.md as CG-owned
$CopilotInstructionsMarker  = "<!-- compound-gpid:managed -->"
$CopilotInstructionsSource  = Join-Path $SourceGithub "copilot-instructions.md"
$CopilotInstructionsDest    = Join-Path $TargetGithubDir "copilot-instructions.md"

# --- Validate global install exists ---
if (-not (Test-Path $CompoundGpidDir)) {
    Write-Error "Compound GPID installation directory not found at: $CompoundGpidDir$CG_INSTALL_GUIDANCE"
    exit 1
}

if (-not (Test-Path $SourceGithub)) {
    Write-Error "Expected .github/ not found inside $CompoundGpidDir. The installation may be corrupted."
    exit 1
}

# --- Step 1: Update the global clone before linking ---
# This ensures the user always links against the latest version.
# If offline or the pull fails, we warn and continue with the current version.
Write-Host ""
Write-Host "Updating Compound GPID..." -ForegroundColor Cyan
# Set flag so update.ps1 skips the copilot-instructions.md refresh -
# link.ps1 handles that refresh itself in Step 4 to avoid doing it twice.
$env:CG_INTERNAL_CALL = "1"
try {
    & "$CompoundGpidDir\scripts\update.ps1"
} catch {
    Write-Warning "Could not update Compound GPID (offline?): $_"
    Write-Warning "Continuing with the current version."
} finally {
    Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
}

# Show which version is active after the update so the user knows what they're linking.
$versionFile = Join-Path $CompoundGpidDir ".cg-version"
if (Test-Path $versionFile) { $activeVersion = (Get-Content $versionFile -Raw).Trim() } else { $activeVersion = "latest" }
if ([string]::IsNullOrWhiteSpace($activeVersion)) { $activeVersion = "latest" }
if ($activeVersion -eq "latest") { $versionLabel = "tracking main (latest)" } else { $versionLabel = "$activeVersion (pinned)" }
Write-Host "  Version: $versionLabel" -ForegroundColor DarkGray

Write-Host ""
Write-Host "Compound GPID - Link" -ForegroundColor Cyan
Write-Host "====================" -ForegroundColor Cyan
Write-Host ""

# --- Step 2: Handle .github/ directory in this project ---
$githubItem = Get-Item -Path $TargetGithubDir -ErrorAction SilentlyContinue

if ($githubItem -and $githubItem.LinkType -eq "Junction") {
    # Legacy: .github/ itself is a whole-directory junction (old cg-link behaviour).
    # Remove the junction and replace it with a real directory so we can insert
    # per-subdirectory junctions alongside any existing user content.
    Write-Host ".github/ is a legacy Compound GPID junction - migrating to per-subdirectory junctions..." -ForegroundColor Yellow
    # Remove-Item on a junction removes only the link, not the target contents
    Remove-Item -Path $TargetGithubDir -Force
    New-Item -ItemType Directory -Path $TargetGithubDir -Force | Out-Null
    Write-Host "  Migrated: .github/ is now a real directory." -ForegroundColor DarkGray
} elseif (-not $githubItem) {
    # .github/ does not exist - create it as a real directory
    New-Item -ItemType Directory -Path $TargetGithubDir -Force | Out-Null
    Write-Host "Created .github/ directory." -ForegroundColor DarkGray
}
# If .github/ already exists as a real directory, leave it untouched.

# --- Step 3: Create per-subdirectory junctions ---
Write-Host "Linking managed directories..." -ForegroundColor DarkGray

foreach ($dir in $ManagedDirs) {
    $junctionPath = Join-Path $TargetGithubDir $dir
    $junctionTarget = Join-Path $SourceGithub $dir

    # Verify the source exists
    if (-not (Test-Path $junctionTarget)) {
        Write-Warning "  Source not found, skipping: $junctionTarget"
        continue
    }

    $existing = Get-Item -Path $junctionPath -ErrorAction SilentlyContinue

    if ($existing) {
        if ($existing.LinkType -eq "Junction") {
            # Already a junction - check if it points to this compound-gpid install
            # .Target is string[] in PS 5.1 - join before comparing
            if (($existing.Target -join '') -like "*compound-gpid*") {
                Write-Host "  $dir/ - already linked" -ForegroundColor DarkGray
                continue
            } else {
                # Junction points somewhere unexpected - ask to relink
                Write-Warning "  $dir/ is a junction pointing to: $($existing.Target)"
                $answer = Read-Host "  Relink $dir/ to Compound GPID instead? [y/N]"
                if ($answer -notmatch "^[Yy]$") {
                    Write-Host "  Skipping $dir/" -ForegroundColor Yellow
                    continue
                }
                Remove-Item -Path $junctionPath -Force
            }
        } else {
            # Real directory exists with the same name - cannot create junction
            Write-Error @"
A real directory .github/$dir/ already exists in this project.
Compound GPID cannot create a junction here without risking data loss.

To resolve: rename or remove .github/$dir/ manually, then re-run cg-link.
"@
            exit 1
        }
    }

    # Create the junction
    try {
        New-Item -ItemType Junction -Path $junctionPath -Value $junctionTarget | Out-Null
        Write-Host "  $dir/ - linked" -ForegroundColor DarkGray
    } catch {
        Write-Error @"
Failed to create junction for $dir/: $_

If you see an access error, enable Developer Mode:
  Settings > System > For developers > Developer Mode (On)

Then re-run: cg-link
"@
        exit 1
    }
}

# --- Step 4: Copy copilot-instructions.md with management marker ---
Write-Host "Linking copilot-instructions.md..." -ForegroundColor DarkGray

if (Test-Path $CopilotInstructionsDest) {
    $existingContent = Get-Content $CopilotInstructionsDest -Raw -ErrorAction SilentlyContinue
    if ($existingContent -and $existingContent -match [regex]::Escape($CopilotInstructionsMarker)) {
        # Marker present - this is a CG-managed copy, overwrite with latest
        $sourceContent = Get-Content $CopilotInstructionsSource -Raw
        Set-Content -Path $CopilotInstructionsDest -Value ($CopilotInstructionsMarker + "`n" + $sourceContent)
        Write-Host "  copilot-instructions.md - updated" -ForegroundColor DarkGray
    } else {
        # No marker - user has taken ownership of this file, leave it alone
        Write-Host "  copilot-instructions.md - user-managed (marker absent), skipping" -ForegroundColor Yellow
        Write-Host "  To restore CG management, delete the file and re-run cg-link." -ForegroundColor DarkGray
    }
} else {
    # File does not exist - copy with marker
    $sourceContent = Get-Content $CopilotInstructionsSource -Raw
    Set-Content -Path $CopilotInstructionsDest -Value ($CopilotInstructionsMarker + "`n" + $sourceContent)
    Write-Host "  copilot-instructions.md - copied" -ForegroundColor DarkGray
}

# --- Step 5: Update .gitignore with CG-specific entries only ---
# We gitignore only the CG-managed items so the user's own .github/ content
# (workflows, templates, CODEOWNERS, etc.) remains tracked by git.
#
# Strategy: idempotent remove-then-rewrite of the CG block (same pattern as
# install.ps1 profile block) so repeated cg-link runs and version upgrades
# never produce duplicate section headers.
$gitignorePath = Join-Path $ProjectRoot ".gitignore"

$cgGitignoreMarker  = "# Compound GPID managed items (junctions + copied file - do not commit)"
$cgGitignoreEntries = @(
    ".github/prompts/",
    ".github/skills/",
    ".github/agents/",
    ".github/instructions/",
    ".github/copilot-instructions.md"
)
$cgGitignoreBlock = $cgGitignoreMarker + "`n" + ($cgGitignoreEntries -join "`n") + "`n"

if (Test-Path $gitignorePath) {
    $giContent = Get-Content $gitignorePath -Raw -ErrorAction SilentlyContinue
    if (-not $giContent) { $giContent = "" }

    # Normalize: ensure content ends with a newline so the remove-then-rewrite regex
    # correctly consumes the last block entry even if the file was manually edited to
    # remove the trailing newline (e.g. by a text editor that strips trailing newlines).
    if ($giContent -and $giContent -notmatch '\r?\n$') { $giContent = $giContent + "`n" }

    # Remove any existing CG block before rewriting - handles version upgrades cleanly.
    # Pattern matches .github/ and .cg-docs/ prefixed body lines (covers current entries
    # and legacy .cg-docs/ from older versions) so user content that immediately follows
    # the CG block without a blank-line separator is not consumed.
    $giUpdated = ($giContent -replace "(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.cg-docs/)[^\r\n]*\r?\n)*", "").TrimEnd()
    if ($giUpdated.Length -gt 0) { $separator = "`n`n" } else { $separator = "" }
    Set-Content -Path $gitignorePath -Value ($giUpdated + $separator + $cgGitignoreBlock)
    Write-Host "Updated CG entries in .gitignore" -ForegroundColor DarkGray
} else {
    Set-Content -Path $gitignorePath -Value $cgGitignoreBlock
    Write-Host "Created .gitignore with CG entries" -ForegroundColor DarkGray
}

# --- Step 5b: Remove stale .cg-docs/ gitignore entry from older setups ---
# Older versions of cg-link added .cg-docs/ to .gitignore under a "knowledge base"
# comment. Since 2026-03-23 .cg-docs/ must be committed (institutional memory).
# Remove both the comment line and the entry if they exist.
if (Test-Path $gitignorePath) {
    $giAfterCg = Get-Content $gitignorePath -Raw -ErrorAction SilentlyContinue
    if ($giAfterCg -and ($giAfterCg -match '(?i)# Compound GPID knowledge base')) {
        $giCleaned = $giAfterCg -replace '(?m)^# Compound GPID knowledge base[^\r\n]*\r?\n\.cg-docs/\r?\n?', ''
        $giCleaned = $giCleaned.TrimEnd()
        if ([string]::IsNullOrWhiteSpace($giCleaned)) {
            Remove-Item $gitignorePath -Force
            Write-Host "  Removed stale .cg-docs/ entry from .gitignore (file now empty, deleted)" -ForegroundColor DarkGray
        } else {
            Set-Content -Path $gitignorePath -Value ($giCleaned + "`n")
            Write-Host "  Removed stale .cg-docs/ entry from .gitignore" -ForegroundColor DarkGray
        }
    }
}

# --- Step 6: Verify a known file is accessible ---
$checkPath = Join-Path $TargetGithubDir "prompts\cg-setup.prompt.md"
if (-not (Test-Path $checkPath)) {
    Write-Warning "Verification failed - prompts not visible at expected path: $checkPath"
} else {
    Write-Host "Junctions verified." -ForegroundColor DarkGray
}

# --- Success ---
Write-Host ""
Write-Host "Linked!" -ForegroundColor Green
Write-Host ""
Write-Host "Compound GPID prompts are now available in this project."
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "  The following directories are managed by Compound GPID." -ForegroundColor Yellow
Write-Host "  Do not edit files inside them - changes will be lost on cg-update." -ForegroundColor Yellow
Write-Host "  Managed: .github/prompts/  .github/skills/  .github/agents/  .github/instructions/" -ForegroundColor Yellow
Write-Host ""
Write-Host "IMPORTANT: Restart VS Code / Positron now." -ForegroundColor Yellow
Write-Host "  Copilot must re-index the workspace to see the linked prompts and agents." -ForegroundColor Yellow
Write-Host "  Without a restart, /cg-setup and other prompts will not be available." -ForegroundColor Yellow
Write-Host ""
Write-Host "Run in VS Code / Positron Copilot Chat:"
Write-Host "  /cg-setup" -ForegroundColor Cyan
Write-Host ""
