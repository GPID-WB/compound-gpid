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

function Read-CgProfileText {
    <#
    .SYNOPSIS
        Reads a PowerShell profile while preserving its original encoding.
    .DESCRIPTION
        Detects UTF-8, UTF-16, UTF-32, and ANSI profile files from their byte
        order marks and, for files without a mark, validates UTF-8 before
        falling back to the active Windows ANSI code page. The returned
        encoding metadata can be passed to Write-CgProfileText so a cleanup
        does not change a user's encoding or BOM state.
    .PARAMETER Path
        Profile file to read.
    .OUTPUTS
        PSCustomObject with Content, Encoding, EncodingName, HasBom, and Preamble.
    .EXAMPLE
        $profile = Read-CgProfileText -Path $PROFILE
    #>
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return $null }

    if ($ExecutionContext.SessionState.LanguageMode -eq "ConstrainedLanguage") {
        throw "Automatic profile cleanup requires FullLanguage mode to preserve the existing encoding. Run the direct bin\cg-update.cmd wrapper or remove the exact legacy wrapper manually."
    }

    $bytes = [System.IO.File]::ReadAllBytes($Path)
    $offset = 0
    $encoding = $null
    $encodingName = $null
    $hasBom = $false

    # Check four-byte BOMs before the two-byte UTF-16 BOMs because the latter
    # are prefixes of UTF-32 little-endian files.
    if ($bytes.Length -ge 4 -and
        $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE -and
        $bytes[2] -eq 0x00 -and $bytes[3] -eq 0x00) {
        $encoding = New-Object -TypeName System.Text.UTF32Encoding -ArgumentList $false, $false
        $encodingName = "utf-32-le"
        $offset = 4
        $hasBom = $true
    } elseif ($bytes.Length -ge 4 -and
        $bytes[0] -eq 0x00 -and $bytes[1] -eq 0x00 -and
        $bytes[2] -eq 0xFE -and $bytes[3] -eq 0xFF) {
        $encoding = New-Object -TypeName System.Text.UTF32Encoding -ArgumentList $true, $false
        $encodingName = "utf-32-be"
        $offset = 4
        $hasBom = $true
    } elseif ($bytes.Length -ge 3 -and
        $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        $encoding = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false, $true
        $encodingName = "utf-8"
        $offset = 3
        $hasBom = $true
    } elseif ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) {
        $encoding = New-Object -TypeName System.Text.UnicodeEncoding -ArgumentList $false, $false, $true
        $encodingName = "utf-16-le"
        $offset = 2
        $hasBom = $true
    } elseif ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) {
        $encoding = New-Object -TypeName System.Text.UnicodeEncoding -ArgumentList $true, $false, $true
        $encodingName = "utf-16-be"
        $offset = 2
        $hasBom = $true
    } else {
        # A no-BOM file is ambiguous when it contains only ASCII. Prefer UTF-8
        # when the bytes are valid UTF-8; otherwise use the active Windows ANSI
        # code page, which is the only lossless interpretation for legacy profiles.
        $utf8Strict = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false, $true
        try {
            [void]$utf8Strict.GetString($bytes)
            $encoding = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false, $false
            $encodingName = "utf-8"
        } catch {
            # Resolve the active Windows ANSI code page explicitly. Do not use
            # Encoding.Default because it is UTF-8 on common PowerShell 7/.NET
            # runtimes. Hardcoding 1252 would corrupt profiles on other locales.
            $ansiCodePage = [System.Globalization.CultureInfo]::CurrentCulture.TextInfo.ANSICodePage
            if ($ansiCodePage -le 0) {
                throw "Could not determine the active Windows ANSI code page for the profile."
            }
            if ($PSVersionTable.PSEdition -ne "Desktop") {
                [System.Text.Encoding]::RegisterProvider([System.Text.CodePagesEncodingProvider]::Instance)
            }
            $encoding = [System.Text.Encoding]::GetEncoding($ansiCodePage)
            $encodingName = "ansi"
        }
    }

    $content = $encoding.GetString($bytes, $offset, $bytes.Length - $offset)
    $preamble = New-Object -TypeName byte[] -ArgumentList $offset
    if ($offset -gt 0) {
        [System.Array]::Copy($bytes, 0, $preamble, 0, $offset)
    }

    return [pscustomobject]@{
        Content      = $content
        Encoding     = $encoding
        EncodingName = $encodingName
        HasBom       = $hasBom
        Preamble     = $preamble
    }
}

function Write-CgProfileText {
    <#
    .SYNOPSIS
        Writes profile text using encoding metadata returned by Read-CgProfileText.
    .PARAMETER Path
        Profile file to write.
    .PARAMETER Content
        Updated profile content.
    .PARAMETER EncodingInfo
        Encoding metadata returned by Read-CgProfileText.
    .EXAMPLE
        $profile = Read-CgProfileText -Path $PROFILE
        Write-CgProfileText -Path $PROFILE -Content $cleaned -EncodingInfo $profile
    #>
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][AllowEmptyString()][string]$Content,
        [Parameter(Mandatory)][psobject]$EncodingInfo
    )

    $payload = $EncodingInfo.Encoding.GetBytes($Content)
    $preamble = $EncodingInfo.Preamble
    $output = New-Object -TypeName byte[] -ArgumentList ($preamble.Length + $payload.Length)
    if ($preamble.Length -gt 0) {
        [System.Array]::Copy($preamble, 0, $output, 0, $preamble.Length)
    }
    if ($payload.Length -gt 0) {
        [System.Array]::Copy($payload, 0, $output, $preamble.Length, $payload.Length)
    }
    $directory = [System.IO.Path]::GetDirectoryName($Path)
    if ([string]::IsNullOrWhiteSpace($directory)) { $directory = (Get-Location).Path }
    $temporaryPath = Join-Path $directory ("." + [System.IO.Path]::GetFileName($Path) + "." + [guid]::NewGuid().ToString("N") + ".tmp")
    try {
        $profileItem = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
        $isReparsePoint = (($profileItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
        $hasLinkType = ($profileItem.PSObject.Properties.Name -contains "LinkType") -and (-not [string]::IsNullOrWhiteSpace([string]$profileItem.LinkType))
        if ($isReparsePoint -or $hasLinkType) {
            throw "Automatic profile cleanup will not replace a reparse-point profile. Edit the target profile manually or remove the exact legacy wrapper through its target path."
        }
        [System.IO.File]::WriteAllBytes($temporaryPath, $output)
        Move-Item -LiteralPath $temporaryPath -Destination $Path -Force
    } finally {
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force -ErrorAction SilentlyContinue
        }
    }
}

function Get-CgLegacyProfilePatterns {
    <#
    .SYNOPSIS
        Returns exact legacy Compound GPID wrapper patterns.
    .OUTPUTS
        PSCustomObject[] with Name, ProfilePattern, and DefinitionPattern.
    #>
    $legacyPatterns = @(
        @{ Name = "cg-link";   Script = "link" },
        @{ Name = "cg-unlink"; Script = "unlink" },
        @{ Name = "cg-update"; Script = "update" }
    )

    foreach ($legacyPattern in $legacyPatterns) {
        $pathExpression = '(?:"[^"\r\n]*\.compound-gpid(?:\\|/)scripts(?:\\|/)' + $legacyPattern.Script + '\.ps1"|''[^''\r\n]*\.compound-gpid(?:\\|/)scripts(?:\\|/)' + $legacyPattern.Script + '\.ps1'')'
        $bodyPattern = '(?:&[ \t]*|\.[ \t]*)' + $pathExpression + '[ \t]+@args'
        $definitionPattern = '(?im)^[ \t]*' + $bodyPattern + '[ \t]*$'
        $profilePattern = '(?im)^[ \t]*function[ \t]+(?:global:)?' + [regex]::Escape($legacyPattern.Name) + '[ \t]*\{[ \t]*' + $bodyPattern + '[ \t]*\}[ \t]*\r?\n?'
        [pscustomobject]@{
            Name              = $legacyPattern.Name
            ProfilePattern    = $profilePattern
            DefinitionPattern = $definitionPattern
        }
    }
}

function Test-CgLegacyFunctionDefinition {
    <#
    .SYNOPSIS
        Tests whether a live function is an exact legacy wrapper.
    .DESCRIPTION
        The profile cleanup deliberately preserves customized functions. This
        companion check lets callers remove a live function only when its
        loaded definition is the same exact one-statement wrapper, avoiding a
        name-only deletion of a user's custom function.
    .PARAMETER CommandName
        Function command name to inspect.
    .EXAMPLE
        if (Test-CgLegacyFunctionDefinition -CommandName "cg-link") {
            Remove-Item -Path "Function:\cg-link" -Force
        }
    #>
    param([Parameter(Mandatory)][string]$CommandName)

    $command = Get-Command $CommandName -CommandType Function -ErrorAction SilentlyContinue
    if (-not $command) { return $false }

    foreach ($legacyPattern in @(Get-CgLegacyProfilePatterns)) {
        if ($legacyPattern.Name -eq $CommandName) {
            return ([string]$command.Definition -match $legacyPattern.DefinitionPattern)
        }
    }
    return $false
}

function Remove-LegacyProfileCommands {
    <#
    .SYNOPSIS
        Removes exact Compound GPID profile wrappers from a PowerShell profile.
    .DESCRIPTION
        Deletes managed blocks and exact one-statement wrappers emitted by
        pre-wrapper installs. Customized functions are retained and reported.
        Returns the names of commands removed from the profile. The caller is
        responsible for removing matching live functions in its own scope.
    .PARAMETER ProfilePath
        Profile file to clean. Defaults to the current session's $PROFILE.
    .OUTPUTS
        System.String[]
    .EXAMPLE
        $removed = Remove-LegacyProfileCommands -ProfilePath $PROFILE
    #>
    param([string]$ProfilePath)

    if ([string]::IsNullOrWhiteSpace($ProfilePath)) { $ProfilePath = $PROFILE }
    $removedLegacyCommands = @()
    if (-not (Test-Path -LiteralPath $ProfilePath -PathType Leaf -ErrorAction SilentlyContinue)) {
        return $removedLegacyCommands
    }

    $profileFile = Read-CgProfileText -Path $ProfilePath
    if ($null -eq $profileFile) { return $removedLegacyCommands }

    $profileContent = $profileFile.Content
    $managedBlockPattern = '(?ims)^[\t ]*# --- Compound GPID \((?:managed by install\.ps1 (?:-|\u2014) do not edit manually|added by install\.ps1)\) ---[\t ]*\r?\n.*?^[\t ]*# --- End Compound GPID ---[\t ]*\r?\n?'
    $hasManagedBlock = $profileContent -and ($profileContent -match $managedBlockPattern)
    $legacyPatterns = @(Get-CgLegacyProfilePatterns)
    $hasLegacyCgFunctions = $false
    foreach ($legacyPattern in $legacyPatterns) {
        if ($profileContent -match $legacyPattern.ProfilePattern) {
            $hasLegacyCgFunctions = $true
            break
        }
    }
    if (-not ($hasManagedBlock -or $hasLegacyCgFunctions)) { return $removedLegacyCommands }

    $cleaned = $profileContent
    $profileChanged = $false
    if ($hasManagedBlock) {
        $cleaned = [regex]::Replace($cleaned, $managedBlockPattern, "")
        $profileChanged = $true
        $removedLegacyCommands += @("cg-link", "cg-unlink", "cg-update")
    }

    foreach ($legacyPattern in $legacyPatterns) {
        if ($cleaned -match $legacyPattern.ProfilePattern) {
            $removedLegacyCommands += $legacyPattern.Name
            $cleaned = [regex]::Replace($cleaned, $legacyPattern.ProfilePattern, "")
            $profileChanged = $true
        }
    }

    if ($profileChanged) {
        Write-CgProfileText -Path $ProfilePath -Content $cleaned -EncodingInfo $profileFile
        Write-Host "  Removed old Compound GPID commands from PowerShell profile." -ForegroundColor DarkGray
    }

    $remainingLegacy = [regex]::Match($cleaned, '(?im)^\s*function\s+(?:global:)?cg-(link|unlink|update)\b')
    if ($remainingLegacy.Success) {
        Write-Warning "  A customized legacy $($remainingLegacy.Groups[1].Value) function remains in the PowerShell profile and may shadow the PATH wrapper. Remove it manually from: $ProfilePath"
    }

    return @($removedLegacyCommands | Select-Object -Unique)
}

function Remove-CgLegacyLiveFunctions {
    <#
    .SYNOPSIS
        Removes loaded exact legacy wrappers without deleting customized functions.
    .PARAMETER CommandNames
        Names returned by Remove-LegacyProfileCommands.
    .OUTPUTS
        System.String[] with command names removed from the live session.
    #>
    param([Parameter(Mandatory)][string[]]$CommandNames)

    $removed = @()
    foreach ($commandName in $CommandNames) {
        $liveFunction = Get-Command $commandName -CommandType Function -ErrorAction SilentlyContinue
        if (-not $liveFunction) { continue }

        if (Test-CgLegacyFunctionDefinition -CommandName $commandName) {
            try {
                Remove-Item -Path "Function:\$commandName" -Force -ErrorAction Stop
            } catch {
                Write-Warning "  Could not remove live $commandName after profile cleanup: $_"
                continue
            }
            if (-not (Get-Command $commandName -CommandType Function -ErrorAction SilentlyContinue)) {
                $removed += $commandName
            }
        } else {
            Write-Warning "  Preserved live $commandName because its current definition is customized. Restart the shell after removing the profile wrapper."
        }
    }
    return @($removed | Select-Object -Unique)
}

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
    # -LiteralPath (not -Path) so file names containing wildcard characters
    # ([, ], *, ?) hash correctly instead of resolving to nothing.
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant()
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

function ConvertTo-CgHashtable {
    <#
    .SYNOPSIS
        Recursively converts a PSCustomObject graph (from ConvertFrom-Json) into
        nested hashtables. Windows PowerShell 5.1 compatible - does not rely on
        the -AsHashtable switch (PowerShell 6+ only).
    .OUTPUTS
        [hashtable] for objects, [object[]] for arrays, scalar values otherwise.
    #>
    param([Parameter()]$Object)

    if ($null -eq $Object) { return $null }
    if ($Object -is [System.Collections.IList] -and -not ($Object -is [string])) {
        return @($Object | ForEach-Object { ConvertTo-CgHashtable $_ })
    }
    if ($Object -is [System.Management.Automation.PSCustomObject]) {
        $ht = @{}
        foreach ($prop in $Object.PSObject.Properties) {
            $ht[$prop.Name] = ConvertTo-CgHashtable $prop.Value
        }
        return $ht
    }
    return $Object
}

function Update-CgKiloGlobalPermission {
    <#
    .SYNOPSIS
        Adds (or removes) a markdown_source allow entry in the global Kilo config
        so Kilo trusts symlinked .kilo/commands/ command files.
    .DESCRIPTION
        Kilo docs require permission.markdown_source whitelisting when
        .kilo/commands/ is a symlink to an external directory. This function
        preserves all existing config keys and is idempotent. On a parse error
        or a non-object JSON root, it leaves the file unchanged rather than
        destroying user settings.
    .PARAMETER CompoundGpidDir
        Path to the Compound GPID installation (parent of .kilo/).
    .PARAMETER KiloConfigPath
        Optional override for the config file path (used by tests). Defaults
        to ~\.config\kilo\kilo.jsonc.
    .PARAMETER Remove
        Remove the permission entry instead of adding it.
    .OUTPUTS
        [bool] -- $true if the file was written, $false otherwise.
    #>
    param(
        [Parameter(Mandatory)][string]$CompoundGpidDir,
        [string]$KiloConfigPath,
        [switch]$Remove
    )

    if ([string]::IsNullOrWhiteSpace($KiloConfigPath)) {
        $kiloConfigDir = Join-Path $env:USERPROFILE ".config\kilo"
        $KiloConfigPath = Join-Path $kiloConfigDir "kilo.jsonc"
    }
    $kiloConfigDir = Split-Path $KiloConfigPath -Parent

    $commandsSource = ConvertTo-CgSlashPath (Join-Path $CompoundGpidDir ".kilo\commands")
    $permissionKey = "$commandsSource/*"

    if (-not (Test-Path $kiloConfigDir)) {
        New-Item -ItemType Directory -Path $kiloConfigDir -Force | Out-Null
    }

    $config = $null
    if (Test-Path $KiloConfigPath) {
        $raw = Get-Content $KiloConfigPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        if (-not [string]::IsNullOrWhiteSpace($raw)) {
            try {
                $parsed = $raw | ConvertFrom-Json
            } catch {
                Write-Warning "  Could not parse kilo.jsonc; leaving it unchanged. Add the markdown_source permission manually if needed."
                return $false
            }
            $config = ConvertTo-CgHashtable $parsed
            # Reject non-object roots (arrays, scalars) before any mutation.
            if (-not ($config -is [hashtable])) {
                Write-Warning "  kilo.jsonc root is not a JSON object; leaving it unchanged."
                return $false
            }
        }
    }
    if ($null -eq $config) { $config = @{} }

    if (-not $config.ContainsKey("permission")) { $config["permission"] = @{} }
    if (-not ($config["permission"] -is [hashtable])) { $config["permission"] = @{} }
    if (-not $config["permission"].ContainsKey("markdown_source")) { $config["permission"]["markdown_source"] = @{} }
    if (-not ($config["permission"]["markdown_source"] -is [hashtable])) { $config["permission"]["markdown_source"] = @{} }

    if ($Remove) {
        if (-not $config["permission"]["markdown_source"].ContainsKey($permissionKey)) { return $false }
        [void]$config["permission"]["markdown_source"].Remove($permissionKey)
        if ($config["permission"]["markdown_source"].Count -eq 0) { [void]$config["permission"].Remove("markdown_source") }
        if ($config["permission"].Count -eq 0) { [void]$config.Remove("permission") }
        $json = $config | ConvertTo-Json -Depth 6
        Set-Content -Path $KiloConfigPath -Value ($json + "`n") -Encoding UTF8
        Write-Host "  Removed kilo.jsonc markdown_source permission" -ForegroundColor DarkGray
        return $true
    }

    $existing = $config["permission"]["markdown_source"][$permissionKey]
    if ($existing -eq "allow") {
        Write-Host "  kilo.jsonc markdown_source permission already present" -ForegroundColor DarkGray
        return $false
    }

    $config["permission"]["markdown_source"][$permissionKey] = "allow"
    $json = $config | ConvertTo-Json -Depth 6
    Set-Content -Path $KiloConfigPath -Value ($json + "`n") -Encoding UTF8
    Write-Host "  Updated kilo.jsonc markdown_source permission for: $permissionKey" -ForegroundColor DarkGray
    return $true
}
