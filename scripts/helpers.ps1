# scripts/helpers.ps1
# Shared constants and helpers dot-sourced by link.ps1 and update.ps1.

# Static guidance shown when the Compound GPID install directory is missing.
# The directory path itself is interpolated by each calling script.
$CG_INSTALL_GUIDANCE = @"

This script expects to run from within a Compound GPID installation.
See docs/installation.md for setup instructions and path guidance.
  # Local machine (OneDrive):  git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"
  # Remote server:             git clone https://github.com/GPID-WB/compound-gpid.git "`$env:USERPROFILE\.compound-gpid"
  # Then run: & "<your-path>\install.ps1"
"@

function Resolve-PythonCommand {
    <#
    .SYNOPSIS
        Finds the first working Python executable on PATH.
    .DESCRIPTION
        Probes python3 -> python -> py in order, rejecting Windows Store stubs
        by verifying that `--version` output starts with "Python". Returns the
        command name (string) that can be invoked, or $null if none found.

        Mirrors the detection logic in install.ps1 (Test-PythonCandidate) and
        the where/for/f/findstr pattern in bin/*.cmd launchers so Python
        resolution is consistent across the plugin.
    .OUTPUTS
        System.String or $null -- the first working Python command name.
    .EXAMPLE
        $py = Resolve-PythonCommand
        if ($py) { & $py scripts/cg_generate_targets.py --all }
    #>
    foreach ($candidate in @("python3", "python", "py")) {
        if (-not (Get-Command $candidate -ErrorAction SilentlyContinue)) { continue }
        try {
            $ver = & $candidate --version 2>&1
            $verStr = "$ver".Trim()
            if ($verStr -match '^Python\s+\d') {
                return $candidate
            }
        } catch {
            continue
        }
    }
    return $null
}

function Get-CgFileSha256 {
    param([Parameter(Mandatory)][string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Read-CgManagedFilesManifest {
    param([Parameter(Mandatory)][string]$ManifestPath)

    $manifest = @{
        schemaVersion = "compound-gpid-managed-files-v1"
        files = @{}
    }

    if (-not (Test-Path $ManifestPath)) { return $manifest }

    try {
        $raw = Get-Content $ManifestPath -Raw -Encoding UTF8 -ErrorAction Stop
        if ([string]::IsNullOrWhiteSpace($raw)) { return $manifest }
        $parsed = $raw | ConvertFrom-Json
        if ($parsed.schemaVersion) { $manifest.schemaVersion = [string]$parsed.schemaVersion }
        if ($parsed.files) {
            foreach ($prop in $parsed.files.PSObject.Properties) {
                $manifest.files[$prop.Name] = @{
                    source = [string]$prop.Value.source
                    checksum = [string]$prop.Value.checksum
                }
            }
        }
    } catch {
        Write-Warning "Could not read Compound GPID managed file manifest: $_"
    }

    return $manifest
}

function Write-CgManagedFilesManifest {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)][hashtable]$Manifest
    )

    $parent = Split-Path $ManifestPath -Parent
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
    }
    $json = $Manifest | ConvertTo-Json -Depth 6
    Set-Content -Path $ManifestPath -Value ($json + "`n") -Encoding UTF8
}

function Resolve-CgContainedPath {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$RelativePath,
        [Parameter(Mandatory)][string]$Label
    )

    if ([System.IO.Path]::IsPathRooted($RelativePath)) {
        throw "$Label path must be relative: $RelativePath"
    }

    $rootFull = [System.IO.Path]::GetFullPath($Root)
    $full = [System.IO.Path]::GetFullPath([System.IO.Path]::Combine($rootFull, $RelativePath))
    $rootPrefix = $rootFull
    if (-not $rootPrefix.EndsWith([System.IO.Path]::DirectorySeparatorChar)) {
        $rootPrefix += [System.IO.Path]::DirectorySeparatorChar
    }

    if ($full -ne $rootFull -and -not $full.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "$Label path escapes its root: $RelativePath"
    }

    return $full
}

function Test-CgReparsePath {
    param([Parameter(Mandatory)][string]$Path)

    $item = Get-Item -Path $Path -Force -ErrorAction SilentlyContinue
    if (-not $item) { return $false }
    return [bool]($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint)
}

function Update-CgManagedPlatformFiles {
    param(
        [Parameter(Mandatory)][string]$ManifestPath,
        [Parameter(Mandatory)][string]$ProjectRoot,
        [Parameter(Mandatory)][string]$CompoundGpidDir
    )

    $result = [pscustomobject]@{
        Refreshed = @()
        SkippedUserModified = @()
        RemovedMissing = @()
        MissingSources = @()
        Invalid = @()
    }

    if (-not (Test-Path $ManifestPath)) { return $result }

    $manifest = Read-CgManagedFilesManifest -ManifestPath $ManifestPath
    $manifestChanged = $false
    foreach ($targetRel in @($manifest.files.Keys)) {
        $record = $manifest.files[$targetRel]
        try {
            $targetPath = Resolve-CgContainedPath -Root $ProjectRoot -RelativePath $targetRel -Label "Managed target"
            $sourcePath = Resolve-CgContainedPath -Root $CompoundGpidDir -RelativePath ([string]$record.source) -Label "Managed source"
        } catch {
            Write-Warning "Invalid managed file manifest entry, skipping refresh: $targetRel ($_)"
            $result.Invalid += $targetRel
            continue
        }

        if (-not (Test-Path $sourcePath)) {
            Write-Warning "Managed source missing, leaving current project file unchanged: $($record.source)"
            $result.MissingSources += $targetRel
            continue
        }
        if (Test-CgReparsePath -Path $sourcePath) {
            Write-Warning "Managed source is a symlink or reparse point, skipping refresh: $($record.source)"
            $result.Invalid += $targetRel
            continue
        }
        if (-not (Test-Path $targetPath)) {
            Write-Warning "Managed file missing in current project, dropping manifest entry: $targetRel"
            [void]$manifest.files.Remove($targetRel)
            $manifestChanged = $true
            $result.RemovedMissing += $targetRel
            continue
        }
        if (Test-CgReparsePath -Path $targetPath) {
            Write-Warning "Managed target is a symlink or reparse point, skipping refresh: $targetRel"
            $result.Invalid += $targetRel
            continue
        }

        $currentChecksum = Get-CgFileSha256 -Path $targetPath
        if ($currentChecksum -ne $record.checksum) {
            Write-Warning "Managed file modified by user, skipping refresh: $targetRel"
            $result.SkippedUserModified += $targetRel
            continue
        }

        Copy-Item -Path $sourcePath -Destination $targetPath -Force
        $manifest.files[$targetRel] = @{
            source = $record.source
            checksum = (Get-CgFileSha256 -Path $targetPath)
        }
        $manifestChanged = $true
        $result.Refreshed += $targetRel
        Write-Host "Refreshed managed platform file: $targetRel" -ForegroundColor DarkGray
    }

    if ($manifestChanged) {
        if ($manifest.files.Count -gt 0) {
            Write-CgManagedFilesManifest -ManifestPath $ManifestPath -Manifest $manifest
        } else {
            Remove-Item -Path $ManifestPath -Force
        }
    }

    return $result
}

function ConvertTo-CgSlashPath {
    param([Parameter(Mandatory)][string]$Path)
    return ($Path -replace '\\', '/')
}

function New-CopilotInstructions {
    <#
    .SYNOPSIS
        Generates a slim, project-specific copilot-instructions.md from the Compound GPID template.
    .DESCRIPTION
        Reads the template from TemplateDir\.github\copilot-instructions.template.md,
        reads project-specific values from compound-gpid.md and compound-gpid.local.md
        in ProjectRoot, fills placeholders, and returns the generated content with
        the management marker prepended.

        Falls back to placeholder values when charter or local config files are absent --
        never fails silently on missing config (only on missing template).
    .PARAMETER TemplateDir
        Path to the Compound GPID installation directory (parent of .github\).
    .PARAMETER ProjectRoot
        Path to the consumer project root directory. When called from update.ps1,
        pass (Get-Location) after Pop-Location -- at that point it resolves to
        the consumer project root, not the compound-gpid install dir.
    .EXAMPLE
        $content = New-CopilotInstructions -TemplateDir "C:\WBG\.compound-gpid" -ProjectRoot (Get-Location)
        Set-Content -Path ".github\copilot-instructions.md" -Value $content
    .OUTPUTS
        System.String
        Generated copilot-instructions.md content with the management marker
        prepended. Write with Set-Content -- do not pipe directly into New-Item.
    #>
    param(
        [Parameter(Mandatory)][string]$TemplateDir,
        [Parameter(Mandatory)][string]$ProjectRoot
    )

    if (-not (Test-Path -Path $ProjectRoot -PathType Container)) {
        throw "ProjectRoot does not exist or is not a directory: '$ProjectRoot'"
    }

    $marker       = "<!-- compound-gpid:managed -->"
    $templatePath = Join-Path $TemplateDir ".github\copilot-instructions.template.md"

    if (-not (Test-Path $templatePath)) {
        throw "Compound GPID template not found at: $templatePath. The installation may be corrupted -- run cg-update --fix."
    }

    $template = Get-Content $templatePath -Raw -Encoding UTF8
    if ([string]::IsNullOrWhiteSpace($template)) {
        throw "Template file is empty: $templatePath. Installation may be corrupted -- run cg-update --fix."
    }

    # --- Read project-name from compound-gpid.md frontmatter ---
    $charterPath = Join-Path $ProjectRoot "compound-gpid.md"
    $projectName = "<project-name>"
    if (Test-Path $charterPath) {
        $charterContent = Get-Content $charterPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        # Match YAML frontmatter block (--- ... ---) and extract project-name
        if ($charterContent -match '(?s)^---[ \t]*\r?\n(.*?)\r?\n---') {
            $fm = $Matches[1]
            if ($fm -match '(?m)^\s*project-name:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$') {
                $val = $Matches[1].Trim()
                if (-not [string]::IsNullOrWhiteSpace($val)) { $projectName = $val }
            }
        }
    }

    # --- Read language, project-type, review-depth, r-syntax from compound-gpid.local.md ---
    $localPath   = Join-Path $ProjectRoot "compound-gpid.local.md"
    $language    = "<not configured>"
    $projectType = "<not configured>"
    $reviewDepth = "<not configured>"
    $rSyntax     = $null
    if (Test-Path $localPath) {
        $localContent = Get-Content $localPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($localContent -match '(?s)^---[ \t]*\r?\n(.*?)\r?\n---') {
            $fm = $Matches[1]
            if ($fm -match '(?m)^\s*language:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')      { $language    = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*project-type:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')  { $projectType = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*review-depth:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')  { $reviewDepth = $Matches[1].Trim() }
            if ($fm -match '(?m)^\s*r-syntax:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')      { $rSyntax     = $Matches[1].Trim() }
        }
    }

    # Build languages string -- append R dialect when configured
    $languages = $language
    if ($null -ne $rSyntax -and $language -match '(?i)\bR\b') {
        $languages = "$language (R dialect: $rSyntax)"
    }

    # --- Fill template placeholders ---
    # Use the .Replace() string method (literal substitution) rather than the
    # -replace operator (which interprets $0, $1 etc. in the replacement as
    # regex backreferences and would silently corrupt values like "R$0 Pipeline").
    # Guard: reject config values that contain placeholder tokens to prevent
    # cross-injection (e.g. a project-name of "{{project-type}}" would corrupt the output).
    foreach ($val in @($projectName, $projectType, $languages, $reviewDepth)) {
        if ($val -match '\{\{') {
            throw "A config value contains a placeholder token ('{{') which would corrupt the generated output. Check compound-gpid.md and compound-gpid.local.md."
        }
    }

    $output = $template
    $output = $output.Replace('{{project-name}}', $projectName)
    $output = $output.Replace('{{project-type}}', $projectType)
    $output = $output.Replace('{{languages}}',    $languages)
    $output = $output.Replace('{{review-depth}}', $reviewDepth)

    # Prepend the managed marker so cg-link/cg-update can identify managed files
    # Match the template's line-ending style to avoid mixed line endings.
    $sep = "`n"
    if ($output -match '\r\n') { $sep = "`r`n" }
    return $marker + $sep + $output
}

function Update-ManagedInstructionsFile {
    <#
    .SYNOPSIS
        Refreshes a CG-managed copilot-instructions.md if content has changed.
    .DESCRIPTION
        Reads the file at Dest. If it contains the management marker, regenerates
        content via New-CopilotInstructions and writes back only if content changed.
        This is the testable core of update.ps1's refresh logic.
    .PARAMETER Dest
        Path to the copilot-instructions.md to refresh.
    .PARAMETER Marker
        The management marker string that identifies a CG-managed file.
    .PARAMETER TemplateDir
        Path to the Compound GPID installation directory (parent of .github\).
    .PARAMETER ProjectRoot
        Path to the consumer project root directory.
    .OUTPUTS
        System.String
        "refreshed"  -- file was regenerated and written.
        "up-to-date" -- content unchanged, no write performed.
        "skipped"    -- file has no management marker; treated as user-managed.
    #>
    param(
        [Parameter(Mandatory)][string]$Dest,
        [Parameter(Mandatory)][string]$Marker,
        [Parameter(Mandatory)][string]$TemplateDir,
        [Parameter(Mandatory)][string]$ProjectRoot
    )
    $existing = Get-Content $Dest -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
    if (-not ($existing -and $existing -match [regex]::Escape($Marker))) {
        return "skipped"
    }
    $generated = New-CopilotInstructions -TemplateDir $TemplateDir -ProjectRoot $ProjectRoot
    if ($generated -ne $existing) {
        Set-Content -Path $Dest -Value $generated -Encoding UTF8
        return "refreshed"
    }
    return "up-to-date"
}
