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
# Structural migrations (folder moves, config field additions) are applied to
# the current working directory when it is a linked project. This enables a
# two-tier update model:
#   - Non-structural: prompt/skill/agent changes propagate instantly via junctions.
#   - Structural: folder-structure changes are migration-gated per project and
#     applied when cg-update is run from that project's root.
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
    git checkout .
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
# --- Structural migration: docs/ → .cg-docs/ ---
# Applies only when run from a linked project. Migrates docs/brainstorms/,
# docs/plans/, docs/solutions/ to .cg-docs/ if they still exist at the old path.
# Idempotent: safe to run multiple times across multiple projects.
if (-not $env:CG_INTERNAL_CALL -and (Test-Path $cwdGithub)) {
    $cwdRoot      = Get-Location
    $cgDocsDir    = Join-Path $cwdRoot ".cg-docs"
    $dirsToMigrate = @("brainstorms", "plans", "solutions")
    $migrated     = @()

    foreach ($dir in $dirsToMigrate) {
        $oldPath = Join-Path $cwdRoot "docs\$dir"
        $newPath = Join-Path $cgDocsDir $dir

        if (Test-Path $oldPath) {
            # Create .cg-docs/ if it doesn't exist yet
            if (-not (Test-Path $cgDocsDir)) {
                New-Item -ItemType Directory -Path $cgDocsDir -Force | Out-Null
            }

            if (-not (Test-Path $newPath)) {
                # Simple case: target doesn't exist — just move
                Move-Item -Path $oldPath -Destination $newPath
                $migrated += $dir
                Write-Host "  Migrated: docs/$dir/ → .cg-docs/$dir/" -ForegroundColor DarkGray
            } else {
                # Target already exists — merge file by file, skip conflicts
                $conflicts = 0
                Get-ChildItem -Path $oldPath -Recurse -File | ForEach-Object {
                    $rel  = $_.FullName.Substring($oldPath.Length + 1)
                    $dest = Join-Path $newPath $rel
                    $destDir = Split-Path $dest -Parent
                    if (-not (Test-Path $destDir)) {
                        New-Item -ItemType Directory -Path $destDir -Force | Out-Null
                    }
                    if (-not (Test-Path $dest)) {
                        Move-Item -Path $_.FullName -Destination $dest
                    } else {
                        $conflicts++
                        Write-Warning "  Skipped (already exists): $rel"
                    }
                }
                # Remove old dir if now empty
                if (-not (Get-ChildItem -Path $oldPath -Recurse -File)) {
                    Remove-Item -Path $oldPath -Recurse -Force
                }
                $migrated += $dir
                if ($conflicts -gt 0) {
                    Write-Host "  Merged: docs/$dir/ → .cg-docs/$dir/ ($conflicts files skipped - already exist)" -ForegroundColor Yellow
                } else {
                    Write-Host "  Migrated: docs/$dir/ → .cg-docs/$dir/" -ForegroundColor DarkGray
                }
            }
        }
    }

    # Clean up empty docs/ directory if all CG subdirs moved and nothing else remains
    $oldDocsDir = Join-Path $cwdRoot "docs"
    if ((Test-Path $oldDocsDir) -and $migrated.Count -gt 0) {
        $remaining = Get-ChildItem -Path $oldDocsDir -ErrorAction SilentlyContinue
        if (-not $remaining) {
            Remove-Item -Path $oldDocsDir -Force
            Write-Host "  Removed empty docs/ directory." -ForegroundColor DarkGray
        }
    }

    if ($migrated.Count -gt 0) {
        Write-Host ""
        Write-Host "Structural migration complete: knowledge base moved to .cg-docs/" -ForegroundColor Green
        Write-Host ""
    }

    # --- Schema version: stamp compound-gpid.local.md ---
    # Read current SCHEMA_VERSION from the global install
    $schemaVersionFile  = Join-Path $CompoundGpidDir "SCHEMA_VERSION"
    $cwdLocalConfig     = Join-Path $cwdRoot "compound-gpid.local.md"

    if ((Test-Path $schemaVersionFile) -and (Test-Path $cwdLocalConfig)) {
        $currentSchema  = (Get-Content $schemaVersionFile -Raw).Trim()
        $localConfig    = Get-Content $cwdLocalConfig -Raw

        if ($localConfig -match 'cg-schema-version:\s*"([^"]*)"') {
            $projectSchema = $Matches[1]
        } else {
            $projectSchema = ""
        }

        if ($projectSchema -ne $currentSchema) {
            if ($localConfig -match 'cg-schema-version:') {
                # Update existing field
                $localConfig = $localConfig -replace 'cg-schema-version:\s*"[^"]*"', "cg-schema-version: `"$currentSchema`""
            } else {
                # Add field after the last --- in frontmatter
                $localConfig = $localConfig -replace '(---\s*\r?\n# Compound)', "cg-schema-version: `"$currentSchema`"`n---`n# Compound"
            }
            Set-Content -Path $cwdLocalConfig -Value $localConfig -NoNewline
            Write-Host "Schema version stamped: $currentSchema" -ForegroundColor DarkGray
        }
    }
}

Write-Host ""