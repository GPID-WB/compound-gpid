# scripts/update.ps1
# Updates the global Compound GPID installation.
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
# Version pinning: users can pin to a specific GitHub Release (git tag) or
# return to tracking main at any time. The preference is stored per-user in
# .cg-version inside the global install directory.
#
# Run from anywhere:
#   cg-update               -- use current version preference (default: latest)
#   cg-update v0.2.0        -- pin to a specific release
#   cg-update latest        -- unpin and track main
#   cg-update --list        -- browse available releases
#   cg-update --fix         -- repair a broken installation

param(
    # Optional version argument: a tag (e.g. v0.2.0) or "latest" to unpin.
    # If omitted, the preference stored in .cg-version is used (default: latest).
    [string]$Version,
    # Display available releases and exit without updating.
    [switch]$List,
    # Repair the installation: clean untracked files, discard local changes,
    # and pull the latest code. Use when cg-update fails due to dirty state.
    [switch]$Fix
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve the install location relative to this script's own directory
# (scripts/ -> parent = compound-gpid root). Works with any install path.
$CompoundGpidDir = Split-Path $PSScriptRoot -Parent

# The management marker that identifies a CG-managed copilot-instructions.md
$CopilotInstructionsMarker = "<!-- compound-gpid:managed -->"

# File that stores the user's version preference inside the global install directory.
# Contains "latest" to track main, or a tag name (e.g. v0.2.0) to pin.
$VersionFile = Join-Path $CompoundGpidDir ".cg-version"

# Regex that matches 3-component release tags only (e.g. v0.2.0).
# Dev tags (4-component, e.g. v0.2.0.9000) are intentionally excluded -- they are
# invisible to users and must never appear in --list, the newer-release hint, or error suggestions.
$ReleaseTagPattern = '^v\d+\.\d+\.\d+$'

# Regex that accepts all valid version inputs: release tags, dev tags, and 'latest'.
# Used in the CLI argument guard and the .cg-version format validator.
# Case-sensitive (-cmatch/-cnotmatch): git tag names are case-sensitive; 'V0.2.0' != 'v0.2.0'.
$VersionAcceptPattern = '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$'

# --- Validate install exists ---
if (-not (Test-Path $CompoundGpidDir)) {
    Write-Error @"
Compound GPID installation directory not found at: $CompoundGpidDir

This script expects to run from within a Compound GPID installation.
See docs/installation.md for setup instructions and path guidance.
  # Local machine (OneDrive):  git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"
  # Remote server:             git clone https://github.com/GPID-WB/compound-gpid.git "`$env:USERPROFILE\.compound-gpid"
  # Then run: & "<your-path>\install.ps1"
  # (Adding a new environment? Update this message and the matching one in scripts/link.ps1)
"@
    exit 1
}

# --- Verify git is available ---
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Error "git is not available. Install Git from https://git-scm.com/download/win"
    exit 1
}

# --- Handle --fix: repair a broken installation ---
if ($Fix.IsPresent) {
    Write-Host ""
    Write-Host "Repairing compound-gpid installation..." -ForegroundColor Cyan
    Write-Host "  Install dir: $CompoundGpidDir" -ForegroundColor DarkGray
    Write-Host ""

    Push-Location $CompoundGpidDir
    try {
        # Remove untracked files (e.g. stale .cg-docs left from old project links)
        Write-Host "  Cleaning untracked files..." -ForegroundColor DarkGray
        git clean -fd 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }

        # Discard any local modifications
        Write-Host "  Discarding local changes..." -ForegroundColor DarkGray
        git checkout . 2>&1 | ForEach-Object { Write-Host "    $_" -ForegroundColor DarkGray }

        # Pull the latest code
        Write-Host "  Pulling latest..." -ForegroundColor DarkGray
        git pull --ff-only
        if ($LASTEXITCODE -ne 0) {
            throw "git pull --ff-only failed with exit code $LASTEXITCODE"
        }

        Write-Host ""
        Write-Host "Repair complete." -ForegroundColor Green
        Write-Host "Run cg-update again to verify." -ForegroundColor DarkGray
        Write-Host ""
    } catch {
        Write-Error "Repair failed: $_"
        exit 1
    } finally {
        Pop-Location
    }
    exit 0
}

# --- Trim and validate the $Version argument ---
# Trim whitespace so " v0.2.0 " is treated identically to "v0.2.0".
if ($Version) { $Version = $Version.Trim() }

# Guard against garbage input early with a clear error (after trimming).
# Accepted: empty/null (read from file), "latest" (unpin), a release tag like
# "v0.2.0", or a dev tag like "v0.2.0.9000" (4-component, for maintainer testing).
if ($Version -and $Version -cnotmatch $VersionAcceptPattern) {
    Write-Error "Invalid version: '$Version'. Expected a tag like 'v0.2.0' (or 'v0.2.0.9000' for dev), 'latest', or use --list to browse."
    exit 1
}

# --- Resolve version mode ---
# User-supplied argument takes priority; fall back to .cg-version; default to latest.
# NOTE: The file write (Set-Content) is intentionally deferred to after successful
# tag validation and checkout in the pinned-mode branch -- never written on error.
if ($Version) {
    $versionMode = $Version
} elseif (Test-Path $VersionFile) {
    # Read first non-empty line and trim to guard against manual multi-line edits
    $raw = (Get-Content $VersionFile -Raw -ErrorAction SilentlyContinue)
    $versionMode = (($raw -split "`n" | Where-Object { $_.Trim() -ne "" } | Select-Object -First 1) + "").Trim()
    if ([string]::IsNullOrWhiteSpace($versionMode)) { $versionMode = "latest" }
} else {
    # .cg-version absent -- backward compat with pre-versioning installs
    $versionMode = "latest"
}

# Validate .cg-version content format (guards against manual edits with garbage values).
# CLI argument $Version is validated separately above; this catches the file-only path.
# Case-sensitive (-cnotmatch): git tag names are case-sensitive; 'V0.2.0' would pass git validation
# but fail at checkout with an unhelpful 'pathspec did not match' error.
if (-not $Version -and $versionMode -cnotmatch $VersionAcceptPattern) {
    Write-Error "Malformed .cg-version: '$versionMode'. Expected a tag like 'v0.2.0' or 'latest'. Edit or delete $VersionFile."
    exit 1
}

# Captured inside the pinned-mode branch; used at the end for the "newer release" hint.
$latestTag = $null

Push-Location $CompoundGpidDir

try {
    # --- Handle --list: show available releases and exit ---
    if ($List.IsPresent) {
        Write-Host ""
        Write-Host "Fetching available releases..." -ForegroundColor Cyan
        try { git fetch --tags 2>$null } catch { <# informational stderr -- ignore #> }
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "git fetch --tags failed (exit $LASTEXITCODE) -- showing cached tag data. Check your network connection."
        }

        $tags = @(git tag --list "v*" --sort=-version:refname 2>$null)
        # Only show 3-component release tags to users; dev tags (4-component) are
        # a maintainer-only escape hatch and must never appear in normal output.
        $releaseTags = @($tags | Where-Object { $_ -match $ReleaseTagPattern })

        # Use the already-resolved $versionMode (avoids redundant file read + normalisation)
        $currentPin = $versionMode

        $isDevPin = $currentPin -ne "latest" -and $currentPin -match '^v\d+\.\d+\.\d+\.\d+$'
        if ($currentPin -eq "latest") {
            $modeLabel = "main (latest)"
        } elseif ($isDevPin) {
            $modeLabel = "$currentPin (dev -- not listed above)"
        } else {
            $modeLabel = "$currentPin (pinned)"
        }

        Write-Host ""
        Write-Host "Available releases:" -ForegroundColor Cyan
        if ($releaseTags) {
            foreach ($tag in $releaseTags) {
                if ($tag -eq $currentPin) { $marker = '  <-- current' } else { $marker = '' }
                Write-Host "  $tag$marker"
            }
        } else {
            Write-Host "  No releases found." -ForegroundColor DarkGray
            Write-Host "  See: https://github.com/GPID-WB/compound-gpid/releases" -ForegroundColor DarkGray
        }

        Write-Host ""
        Write-Host "Current: $modeLabel" -ForegroundColor DarkGray
        Write-Host ""
        Write-Host '  cg-update <version>  -- pin to a specific release' -ForegroundColor DarkGray
        Write-Host "  cg-update latest     -- unpin and track main" -ForegroundColor DarkGray
        Write-Host ""
        exit 0
    }

    # --- Show active mode upfront so users know what's happening ---
    if ($versionMode -eq "latest") {
        Write-Host "Mode: tracking main (latest)" -ForegroundColor DarkGray
    } else {
        Write-Host "Mode: pinned ($versionMode)" -ForegroundColor DarkGray
    }

    if ($versionMode -eq "latest") {
        # ---- Latest mode: track main HEAD ----
        # git fetch --tags not needed here; git pull handles all remote sync.
        # Tags stay current after any pinned-mode or --list run that fetched them.

        # Persist the "latest" preference when the user explicitly unpins with
        # 'cg-update latest'. Safe to write before git ops: "latest" is always valid.
        if ($Version -eq "latest") {
            Set-Content -Path $VersionFile -Value "latest" -NoNewline
        }

        # If previously pinned to a tag (detached HEAD), switch back to main first.
        # git rev-parse --abbrev-ref HEAD returns "HEAD" in detached HEAD state.
        $headBranch = (git rev-parse --abbrev-ref HEAD 2>$null)
        if ($LASTEXITCODE -ne 0) {
            throw "Could not determine current branch (git rev-parse failed with exit code $LASTEXITCODE)"
        }
        if ($headBranch -eq "HEAD") {
            Write-Host "Switching from pinned version back to main..." -ForegroundColor DarkGray
            try { git checkout main 2>$null } catch { <# informational stderr -- ignore #> }
            if ($LASTEXITCODE -ne 0) {
                throw "git checkout main failed with exit code $LASTEXITCODE"
            }
        }

        # Capture the commit hash before updating so we can show what changed
        $before = git rev-parse --short HEAD 2>$null

        Write-Host "Checking for updates..." -ForegroundColor Cyan

        # Reset any accidental local changes before pulling.
        # This handles the case where a user inadvertently edited a file through a
        # junction - git checkout discards uncommitted changes in the global clone.
        #
        # PS5.1 with ErrorActionPreference=Stop can promote native stderr to a
        # terminating error even with 2>$null in some host configurations. Wrapping
        # in try/catch makes this bullet-proof: we never want a best-effort cleanup
        # step to abort the update. LASTEXITCODE is still checked for real failures.
        try { git checkout . 2>$null } catch { <# informational stderr -- ignore #> }
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

    } else {
        # ---- Pinned mode: checkout a specific tag (detached HEAD) ----

        Write-Host "Checking out $versionMode..." -ForegroundColor Cyan

        # Fetch tags first so tag metadata is current before validation.
        # Fault-tolerant: network failure just means we work with cached tag data.
        try { git fetch --tags 2>$null } catch { <# informational stderr -- ignore #> }
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "git fetch --tags returned exit code $LASTEXITCODE - continuing with cached tag data"
        }

        # Capture all tags once; derive latestTag, tagExists, and similar from the same list.
        $allTags     = @(git tag --list "v*" --sort=-version:refname 2>$null)
        # Filter to release-only once; reuse for latestTag and similar -- never show dev tags to users.
        $releaseTags = @($allTags | Where-Object { $_ -match $ReleaseTagPattern })
        $latestTag   = $releaseTags | Select-Object -First 1

        # Validate the tag exists before attempting checkout or persisting preference.
        $tagExists = $versionMode -in $allTags
        if (-not $tagExists) {
            # Only show release tags in the suggestion -- never expose dev tags.
            $similar = $releaseTags | Select-Object -First 5
            if ($similar) {
                $hint = "`n`nAvailable releases:`n" + ($similar | ForEach-Object { "  $_" } | Out-String).TrimEnd()
            } else { $hint = "" }
            throw "Release '$versionMode' not found.$hint`n`nRun: cg-update --list   to see all available releases."
        }

        # Checkout the tag. Detached HEAD is expected and normal for pinned mode.
        # Use the PS5.1-safe try/catch + 2>$null pattern to avoid stderr promotion.
        try { git checkout $versionMode 2>$null } catch { <# informational stderr -- ignore #> }
        if ($LASTEXITCODE -ne 0) {
            throw "git checkout $versionMode failed with exit code $LASTEXITCODE"
        }

        # Persist the version preference only after successful checkout.
        # Writing before validation could leave .cg-version permanently corrupted
        # if the tag doesn't exist or checkout fails.
        Set-Content -Path $VersionFile -Value $versionMode -NoNewline

        Write-Host ""
        Write-Host "Pinned to $versionMode." -ForegroundColor Green
        Write-Host ""
        Write-Host "Managed subdirectories (prompts/, skills/, agents/, instructions/) are" -ForegroundColor DarkGray
        Write-Host "updated in all linked projects immediately via junctions." -ForegroundColor DarkGray
        Write-Host ""
        Write-Host "Run: cg-update latest   to return to tracking main." -ForegroundColor DarkGray
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
# --- Structural migration: docs/ -> .cg-docs/ ---
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
                # Simple case: target doesn't exist -- just move
                Move-Item -Path $oldPath -Destination $newPath
                $migrated += $dir
                Write-Host "  Migrated: docs/$dir/ -> .cg-docs/$dir/" -ForegroundColor DarkGray
            } else {
                # Target already exists -- merge file by file, skip conflicts
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
                    Write-Host "  Merged: docs/$dir/ -> .cg-docs/$dir/ ($conflicts files skipped - already exist)" -ForegroundColor Yellow
                } else {
                    Write-Host "  Migrated: docs/$dir/ -> .cg-docs/$dir/" -ForegroundColor DarkGray
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
                # Add field after the last --- in frontmatter.
                # This regex depends on the "# Compound" heading existing
                # immediately after the closing --- in compound-gpid.local.md.
                $localConfig = $localConfig -replace '(---\s*\r?\n# Compound)', "cg-schema-version: `"$currentSchema`"`n---`n# Compound"
            }
            Set-Content -Path $cwdLocalConfig -Value $localConfig -NoNewline
            Write-Host "Schema version stamped: $currentSchema" -ForegroundColor DarkGray
        }
    }

    # --- Migration notice: project charter (compound-gpid.md) ---
    # Introduced in schema version 2026-03-25-project-charter.
    # Inform projects that do not yet have a charter. Do not create it
    # automatically -- the charter requires interactive user input via /cg-setup.
    $cwdCharter = Join-Path $cwdRoot "compound-gpid.md"
    if (-not (Test-Path $cwdCharter)) {
        Write-Host ""
        Write-Host "New feature: project charter." -ForegroundColor Cyan
        Write-Host "  Run /cg-setup in Copilot Chat to create 'compound-gpid.md' for shared project context." -ForegroundColor Cyan
        Write-Host "  The charter gives Copilot awareness of your project's goals, deliverables, and constraints." -ForegroundColor Cyan
    }

    # --- Migration warning: standalone .cg-docs/ in .gitignore ---
    # Projects configured before v0.1.1 (2026-03-23) may have .cg-docs/ as a
    # standalone line added by the pre-v0.1.1 version of Step A5 in
    # .github/prompts/cg-setup.prompt.md (that step was changed in v0.1.1 to
    # stop gitignoring .cg-docs/). The standalone line lives outside the CG
    # managed block, so the
    # remove-then-rewrite logic in link.ps1 does not touch it. Warn the user
    # so they can remove it manually.
    # Intentional: warn on every cg-update run until the user resolves it -- no
    # sentinel needed. A user who misses the first warning will see it again.
    $cwdGitignore = Join-Path $cwdRoot ".gitignore"
    if (Test-Path $cwdGitignore) {
        # -ErrorAction SilentlyContinue: this is a diagnostics-only path.
        # A permission error or race condition must never abort the update run.
        $giLines = Get-Content $cwdGitignore -ErrorAction SilentlyContinue
        # Match either separator (/ or \) -- git on Windows accepts both.
        # Leading/trailing whitespace is also matched: a padded entry like
        # '  .cg-docs/  ' would not be honoured by git, but we warn anyway
        # (harmless over-warning vs silently skipping).
        # Note: this regex detects what /cg-setup wrote as a standalone line --
        # independent of and complementary to link.ps1's block-rewrite pattern.
        $staleCgDocsLines = $giLines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
        if ($staleCgDocsLines) {
            Write-Host ""
            Write-Warning @"
Your .gitignore contains a standalone '.cg-docs/' entry from versions prior to
v0.1.1 (2026-03-23). .cg-docs/ should be committed -- it contains institutional
knowledge (brainstorms, plans, solutions) that must be shared with your team.

To fix:
  1. Remove the '.cg-docs/' line from your .gitignore
  2. Run: git rm -r --cached --ignore-unmatch .cg-docs/
  3. Run: git add .cg-docs/
  4. Commit the change
"@
        }
    }
}

# Remind users running from outside a linked project that per-project notices are skipped
if (-not $env:CG_INTERNAL_CALL -and -not (Test-Path $cwdGithub)) {
    Write-Host ""
    Write-Host "Tip: run cg-update from your project root to apply per-project migration notices." -ForegroundColor DarkGray
}

# --- Version status display ---
# Show the current version state at the end of every successful update run.
Write-Host ""
if ($versionMode -eq "latest") {
    Write-Host "Current version: main (latest)" -ForegroundColor DarkGray
} else {
    # Label dev tags (4-component, e.g. v0.1.0.9000) as 'dev-pinned' to signal
    # pre-release code. Release pins show 'pinned'. Helps users know which context they're in.
    $isDevPin = $versionMode -match '^v\d+\.\d+\.\d+\.\d+$'
    $pinLabel = if ($isDevPin) { "dev-pinned" } else { "pinned" }
    Write-Host "Current version: $versionMode ($pinLabel)" -ForegroundColor DarkGray
    Write-Host "Run: cg-update latest   to unpin and track main." -ForegroundColor DarkGray
    # Hint when a newer release is available (only if we have fresh tag data)
    if ($latestTag -and $latestTag -ne $versionMode) {
        Write-Host ""
        Write-Host "Newer release available: $latestTag" -ForegroundColor Yellow
        Write-Host "Run: cg-update $latestTag" -ForegroundColor Yellow
    }
}

Write-Host ""