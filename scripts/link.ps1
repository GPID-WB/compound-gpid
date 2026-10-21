# scripts/link.ps1
# Links the current project to Compound GPID using per-install-unit junctions and
# managed copied files. Existing project-owned platform roots are preserved.

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$RawArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$CompoundGpidDir = Split-Path $PSScriptRoot -Parent
$ProjectRoot = (Get-Location).Path
$TargetMappingPath = Join-Path $CompoundGpidDir ".github/shared/target-mapping.json"
$ManifestPath = Join-Path $ProjectRoot ".compound-gpid/managed-files.json"
$CopilotInstructionsMarker = "<!-- compound-gpid:managed -->"
$CopiedDirectoryMarkerName = ".compound-gpid-managed-copy.json"
$KiloCompatMirrorRootRel = ".compound-gpid/kilo-compat-skills"

function Show-CgLinkUsage {
    Write-Host "Usage: cg-link [--check] [--platforms <copilot,claude-code,codex,opencode,kilo|all>] [--yes] [--help]"
    Write-Host "--check reports the current project without update or writes. Exit: 0 nonblocking, 1 manual action or block, 2 usage."
}

function Resolve-CgLinkArguments {
    param([object[]]$Arguments)
    # Zero-arg invocation (e.g. CI E2E: `link.ps1` with no flags) yields
    # $null here via ValueFromRemainingArguments; .Count on $null throws under
    # Set-StrictMode -Version Latest.
    if ($null -eq $Arguments) { $Arguments = @() }
    $result = @{ Force = $false; Platforms = $null; Check = $false; Help = $false }
    for ($i = 0; $i -lt $Arguments.Count; $i++) {
        $arg = [string]$Arguments[$i]
        if ($arg -in @("--yes", "-y", "-Force", "--force")) {
            $result.Force = $true
        } elseif ($arg -eq "--check") {
            $result.Check = $true
        } elseif ($arg -in @("--help", "-h")) {
            $result.Help = $true
        } elseif ($arg -like "--platform=*") {
            $result.Platforms = $arg.Substring("--platform=".Length)
            if ([string]::IsNullOrWhiteSpace($result.Platforms)) { throw "Missing platform value" }
        } elseif ($arg -like "--platforms=*") {
            $result.Platforms = $arg.Substring("--platforms=".Length)
            if ([string]::IsNullOrWhiteSpace($result.Platforms)) { throw "Missing platform value" }
        } elseif ($arg -like "-Platforms=*") {
            $result.Platforms = $arg.Substring("-Platforms=".Length)
            if ([string]::IsNullOrWhiteSpace($result.Platforms)) { throw "Missing platform value" }
        } elseif ($arg -in @("--platform", "--platforms", "-Platforms")) {
            if ($i + 1 -ge $Arguments.Count) { throw "Missing value after $arg" }
            $i++
            $result.Platforms = [string]$Arguments[$i]
            if ([string]::IsNullOrWhiteSpace($result.Platforms) -or $result.Platforms.StartsWith("-")) {
                throw "Missing value after $arg"
            }
        } else {
            throw "Unrecognized argument '$arg'"
        }
    }
    return $result
}

function Resolve-CgPlatforms {
    param([string]$PlatformsValue)
    $supported = @("copilot", "claude-code", "codex", "opencode", "kilo")
    if ([string]::IsNullOrWhiteSpace($PlatformsValue)) { return $supported }

    $selected = New-Object System.Collections.ArrayList
    $unknown = @()
    foreach ($raw in ($PlatformsValue -split ",")) {
        $platform = $raw.Trim().ToLowerInvariant()
        if ([string]::IsNullOrWhiteSpace($platform)) { continue }
        if ($platform -eq "all") {
            foreach ($item in $supported) {
                if (-not $selected.Contains($item)) { [void]$selected.Add($item) }
            }
            continue
        }
        if ($platform -in $supported) {
            if (-not $selected.Contains($platform)) { [void]$selected.Add($platform) }
        } else {
            $unknown += $platform
        }
    }

    if ($unknown.Count -gt 0) { throw "Unknown platform(s): $($unknown -join ', ')" }
    if ($selected.Count -eq 0) {
        throw "No valid platforms selected. Supported platforms: $($supported -join ', ')"
    }
    return @($selected)
}

try {
    $argsParsed = Resolve-CgLinkArguments -Arguments $RawArgs
    $Force = [bool]$argsParsed.Force
    $selectedPlatforms = Resolve-CgPlatforms -PlatformsValue $argsParsed.Platforms
} catch {
    Write-Host "ERROR: $_"
    Show-CgLinkUsage
    exit 2
}
if ($argsParsed.Help) { Show-CgLinkUsage; exit 0 }

$onWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))
if (-not $onWindows) {
    Write-Host "link.ps1 is Windows-only. On macOS/Linux, use scripts/link.sh."
    exit 1
}
. (Join-Path $PSScriptRoot "helpers.ps1")
if ($argsParsed.Check) {
    $checkPython = Resolve-PythonCommand -NoBytecode
    if (-not $checkPython) { Write-Host "ERROR: Python 3.8+ is required for --check."; exit 1 }
    $checkArgs = @("--root", $ProjectRoot, "--source-root", $CompoundGpidDir, "--platforms", ($selectedPlatforms -join ","))
    if ($Force) { $checkArgs += "--force" }
    & $checkPython -B (Join-Path $PSScriptRoot "cg_link_check.py") @checkArgs
    exit $LASTEXITCODE
}

$script:CopyArgs = New-Object System.Collections.ArrayList

function Get-CgTargetRoot {
    param([string]$RelativePath)
    return (ConvertTo-CgSlashPath $RelativePath).Split("/")[0]
}

function Get-CgNormalizedFullPath {
    param([string]$Path)
    # Single canonical normalization used across this file so path-containment
    # decisions never diverge on trailing separators / case.
    return [System.IO.Path]::GetFullPath($Path).TrimEnd([char[]]@('\', '/'))
}

function Test-CgOwnedJunction {
    param(
        $Item,
        [string]$ExpectedTarget
    )
    if (-not $Item -or $Item.LinkType -ne "Junction") { return $false }

    $actualTarget = [string]($Item.Target -join '')
    if (-not [System.IO.Path]::IsPathRooted($actualTarget)) {
        $actualTarget = Join-Path $Item.Parent.FullName $actualTarget
    }
    $actualFull = Get-CgNormalizedFullPath $actualTarget
    $expectedFull = Get-CgNormalizedFullPath $ExpectedTarget
    return $actualFull.Equals($expectedFull, [System.StringComparison]::OrdinalIgnoreCase)
}

function Remove-CgJunction {
    param([string]$Path)

    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if (-not $item -or $item.LinkType -ne "Junction") {
        throw "Refusing to remove non-junction path: $Path"
    }

    # Remove-Item prompts for -Recurse on populated junctions in Windows
    # PowerShell. Directory.Delete without recursion removes only the reparse
    # point and never traverses into the shared source directory.
    [System.IO.Directory]::Delete($item.FullName)
}

function Set-CgJunctionTargetSafely {
    param(
        [string]$Path,
        [string]$Target
    )

    $parent = Split-Path $Path -Parent
    $leaf = Split-Path $Path -Leaf
    $operationId = [System.Guid]::NewGuid().ToString('N')
    $temporary = Join-Path $parent ".$leaf.$operationId.new"
    $backup = Join-Path $parent ".$leaf.$operationId.previous"
    $movedOriginal = $false
    try {
        New-Item -ItemType Junction -Path $temporary -Value $Target | Out-Null
        $temporaryItem = Get-Item -LiteralPath $temporary -Force
        if (-not (Test-CgOwnedJunction -Item $temporaryItem -ExpectedTarget $Target)) {
            throw "Temporary junction did not resolve to the expected target: $temporary"
        }

        [System.IO.Directory]::Move($Path, $backup)
        $movedOriginal = $true
        try {
            [System.IO.Directory]::Move($temporary, $Path)
        } catch {
            if (-not (Test-Path -LiteralPath $Path) -and (Test-Path -LiteralPath $backup)) {
                [System.IO.Directory]::Move($backup, $Path)
                $movedOriginal = $false
            }
            throw
        }
        [System.IO.Directory]::Delete($backup)
        $movedOriginal = $false
    } finally {
        $temporaryItem = Get-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue
        if ($temporaryItem -and $temporaryItem.LinkType -eq "Junction") {
            [System.IO.Directory]::Delete($temporaryItem.FullName)
        }
        if ($movedOriginal -and -not (Test-Path -LiteralPath $Path) -and (Test-Path -LiteralPath $backup)) {
            [System.IO.Directory]::Move($backup, $Path)
        }
    }
}

function Resolve-CgContainedCopyPath {
    param(
        [string]$Base,
        [string]$RelativePath
    )

    # Threat model: the per-directory marker (`.compound-gpid-managed-copy.json`)
    # and manifest-relative paths are attacker-influenceable (the marker is a
    # single plain file that can be hand-edited or tampered). Every path that
    # Sync may write to or delete must be proven to stay inside $Base, or the
    # stale-file removal could delete arbitrary files outside the managed dir.
    $normalized = ConvertTo-CgSlashPath $RelativePath
    if ([string]::IsNullOrWhiteSpace($normalized) -or
        [System.IO.Path]::IsPathRooted($normalized) -or
        $normalized -match '^[A-Za-z]:' -or
        $normalized.IndexOf([char]0) -ge 0) {
        throw "Managed-copy path is not a safe relative path: $RelativePath"
    }
    $parts = @($normalized -split '/')
    if ($parts.Count -eq 0 -or @($parts | Where-Object { $_ -in @('', '.', '..') }).Count -gt 0) {
        throw "Managed-copy path contains an empty or traversal component: $RelativePath"
    }

    $baseFull = Get-CgNormalizedFullPath $Base
    $resolved = [System.IO.Path]::GetFullPath((Join-Path $baseFull $normalized))
    $prefix = $baseFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $resolved.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Managed-copy path escapes its target directory: $RelativePath"
    }
    return $resolved
}

function Assert-CgManagedCopyTargetSafe {
    param([string]$Target)

    $projectFull = Get-CgNormalizedFullPath $ProjectRoot
    $targetFull = Get-CgNormalizedFullPath $Target
    $prefix = $projectFull + [System.IO.Path]::DirectorySeparatorChar
    if (-not $targetFull.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Managed-copy target escapes the project root: $Target"
    }
    $relative = $targetFull.Substring($projectFull.Length).TrimStart([char[]]@('\', '/'))
    $current = $projectFull
    foreach ($part in @($relative -split '[\\/]')) {
        if (-not $part) { continue }
        $current = Join-Path $current $part
        if (-not (Test-Path -LiteralPath $current)) { continue }
        $item = Get-Item -LiteralPath $current -Force
        if ($item.LinkType -in @("SymbolicLink", "Junction")) {
            throw "Managed-copy target crosses a reparse point: $current"
        }
    }
}

function Read-CgCopiedDirectoryManifest {
    param(
        [string]$Target,
        [string]$SourceRel
    )

    # Returns $null => the directory is treated as unmanaged and skipped
    # (callers: Install-CgDirectoryUnit, Get-CgInstalledGitignoreEntries). An invalid, corrupt, or tampered marker
    # must never crash the link run or be silently accepted as valid.
    $markerPath = Resolve-CgContainedCopyPath -Base $Target -RelativePath $CopiedDirectoryMarkerName
    if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) { return $null }
    $markerItem = Get-Item -LiteralPath $markerPath -Force
    if ($markerItem.LinkType -in @("SymbolicLink", "Junction")) {
        Write-Warning "  Managed-copy marker is a reparse point; preserving the directory."
        return $null
    }
    try {
        $data = Get-Content -LiteralPath $markerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Write-Warning "  Invalid managed-copy marker at $markerPath; preserving the directory."
        return $null
    }

    # Defensive root-shape validation. A marker of {}, [], or a scalar would
    # throw PropertyNotFoundException on property access under
    # Set-StrictMode -Version Latest, aborting the whole link. Reject any
    # non-object root as "preserve".
    if ($null -eq $data -or -not ($data -is [System.Management.Automation.PSCustomObject])) {
        Write-Warning "  Managed-copy marker is not a JSON object at $markerPath; preserving the directory."
        return $null
    }
    $props = @{}
    foreach ($property in @($data.PSObject.Properties)) { $props[$property.Name] = $property.Value }
    # `-eq 1` also accepts the string '1' in PowerShell, but we additionally
    # require the recorded source to match the unit we are syncing.
    if ($props['schemaVersion'] -ne 1 -or [string]$props['source'] -ne (ConvertTo-CgSlashPath $SourceRel)) {
        Write-Warning "  Managed-copy marker does not match source $SourceRel; preserving the directory."
        return $null
    }

    $filesRaw = $props['files']
    if ($null -eq $filesRaw -or -not ($filesRaw -is [System.Management.Automation.PSCustomObject])) {
        Write-Warning "  Managed-copy marker has no files object at $markerPath; preserving the directory."
        return $null
    }
    $files = @{}
    foreach ($property in @($filesRaw.PSObject.Properties)) {
        $relative = [string]$property.Name
        if ($relative -eq $CopiedDirectoryMarkerName) {
            Write-Warning "  Managed-copy marker references itself; preserving the directory."
            return $null
        }
        try {
            [void](Resolve-CgContainedCopyPath -Base $Target -RelativePath $relative)
        } catch {
            Write-Warning "  Unsafe managed-copy marker path '$relative'; preserving the directory."
            return $null
        }
        $checksum = [string]$property.Value
        if ($checksum -notmatch '^[0-9a-fA-F]{64}$') {
            Write-Warning "  Managed-copy marker has an invalid checksum for '$relative'; preserving the directory."
            return $null
        }
        $files[$relative] = $checksum
    }
    # An empty files map would silently un-manage previously tracked files
    # (they would read as absent records and be treated as user-owned forever).
    if ($files.Count -eq 0) {
        Write-Warning "  Managed-copy marker lists no managed files at $markerPath; preserving the directory."
        return $null
    }
    return @{ source = (ConvertTo-CgSlashPath $SourceRel); files = $files }
}

function Ensure-CgRootDirectory {
    param([string]$RootName)
    $rootPath = Join-Path $ProjectRoot $RootName
    $expectedRoot = Join-Path $CompoundGpidDir $RootName
    $existing = Get-Item -LiteralPath $rootPath -Force -ErrorAction SilentlyContinue
    if ($existing -and (Test-CgOwnedJunction -Item $existing -ExpectedTarget $expectedRoot)) {
        Write-Host "  $RootName/ - migrating legacy whole-root junction" -ForegroundColor Yellow
        Remove-CgJunction -Path $rootPath
        New-Item -ItemType Directory -Path $rootPath -Force | Out-Null
        return $true
    }
    if ($existing -and $existing.LinkType -in @("SymbolicLink", "Junction")) {
        Write-Warning "  $RootName/ is a non-Compound link; manual action required; skipping units under it."
        return $false
    }
    if ($existing -and -not $existing.PSIsContainer) {
        Write-Warning "  $RootName exists as a file; skipping units under it."
        return $false
    }
    if (-not $existing) {
        New-Item -ItemType Directory -Path $rootPath -Force | Out-Null
        Write-Host "  $RootName/ - created" -ForegroundColor DarkGray
    }
    return $true
}

function Install-CgDirectoryUnit {
    param(
        [string]$SourceRel,
        [string]$TargetRel,
        [string]$Strategy,
        [bool]$Force
    )
    $source = Join-Path $CompoundGpidDir $SourceRel
    $target = Join-Path $ProjectRoot $TargetRel
    $existing = Get-Item -LiteralPath $target -Force -ErrorAction SilentlyContinue

    if ($existing) {
        if ($existing.LinkType -eq "Junction") {
            $compatPlatform = switch ($TargetRel) {
                ".claude/skills" { "claude-code" }
                ".agents/skills" { "codex" }
                ".opencode/skills" { "opencode" }
                default { $null }
            }
            if ($compatPlatform) {
                $mirrorRel = Get-CgKiloCompatSkillMirrorRel -PlatformId $compatPlatform
                $mirrorPath = Join-Path $ProjectRoot $mirrorRel
                if (Test-CgOwnedJunction -Item $existing -ExpectedTarget $mirrorPath) {
                    Write-Host "  $TargetRel - already linked through Kilo compatibility mirror" -ForegroundColor DarkGray
                    return $true
                }
            }
            if (Test-CgOwnedJunction -Item $existing -ExpectedTarget $source) {
                if ($Strategy -eq "copy-directory") {
                    Write-Host "  $TargetRel - migrating legacy junction to copy-directory" -ForegroundColor Yellow
                    Remove-CgJunction -Path $target
                    $existing = $null
                } else {
                    Write-Host "  $TargetRel - already linked" -ForegroundColor DarkGray
                    return $true
                }
            } else {
                Write-Warning "  $TargetRel is a junction pointing to: $($existing.Target); manual action required; preserving it."
                return $false
            }
        } elseif ($existing.LinkType -in @("SymbolicLink", "Junction")) {
            Write-Warning "  $TargetRel is a non-junction link; manual action required; preserving it."
            return $false
        } elseif ($existing.PSIsContainer) {
            if ($Strategy -eq "copy-directory") {
                Write-Host "  $TargetRel - already a real directory (copy queued)" -ForegroundColor DarkGray
            } else {
                Write-Warning "  $TargetRel is a real directory; skipping this unit."
                return $false
            }
        } else {
            Write-Warning "  $TargetRel exists as a file; skipping this unit."
            return $false
        }
    }

    if ($Strategy -eq "copy-directory") {
        foreach ($argument in @("--directory", (ConvertTo-CgSlashPath $SourceRel), (ConvertTo-CgSlashPath $TargetRel))) {
            [void]$script:CopyArgs.Add($argument)
        }
        Write-Host "  $TargetRel - copy queued" -ForegroundColor DarkGray
    } else {
        $parent = Split-Path $target -Parent
        if (-not (Test-Path -LiteralPath $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        New-Item -ItemType Junction -Path $target -Value $source | Out-Null
        Write-Host "  $TargetRel - linked" -ForegroundColor DarkGray
    }
    return $true
}

function Install-CgFileUnit {
    param(
        $Unit,
        [hashtable]$Manifest
    )
    $targetRel = ConvertTo-CgSlashPath ([string]$Unit.target)
    $sourceRel = ConvertTo-CgSlashPath ([string]$Unit.source)
    foreach ($argument in @("--file", $sourceRel, $targetRel, [string]$Unit.strategy)) {
        [void]$script:CopyArgs.Add($argument)
    }
    if ($Unit.PSObject.Properties.Name -contains "manualSnippet") {
        foreach ($argument in @("--manual-snippet", $targetRel, [string]$Unit.manualSnippet)) {
            [void]$script:CopyArgs.Add($argument)
        }
    }
    return $true
}

function Get-CgKiloCompatSkillMirrorRel {
    param([string]$PlatformId)
    return "$KiloCompatMirrorRootRel/$PlatformId"
}

function Protect-CgKiloCompatibilitySkillLinks {
    param($Mapping)

    $kiloSkills = Join-Path $ProjectRoot ".kilo/skills"
    try {
        Assert-CgManagedCopyTargetSafe -Target $kiloSkills
    } catch {
        Write-Warning "  .kilo/skills crosses a link or reparse point; manual action required; compatibility links preserved."
        return @()
    }
    if (-not (Read-CgCopiedDirectoryManifest -Target $kiloSkills -SourceRel ".kilo/skills")) {
        return @()
    }

    $protected = New-Object System.Collections.ArrayList
    foreach ($platformId in @("claude-code", "codex", "opencode")) {
        $target = @($Mapping.targets | Where-Object { $_.id -eq $platformId })[0]
        if (-not $target) { continue }
        $unit = @($target.installUnits | Where-Object {
            [string]$_.type -eq "directory" -and
            (ConvertTo-CgSlashPath ([string]$_.target)) -eq [string]$target.outputPaths.skills
        })[0]
        if (-not $unit) { continue }

        $sourceRel = ConvertTo-CgSlashPath ([string]$unit.source)
        $targetRel = ConvertTo-CgSlashPath ([string]$unit.target)
        $sourcePath = Join-Path $CompoundGpidDir $sourceRel
        $targetPath = Join-Path $ProjectRoot $targetRel
        $mirrorRel = Get-CgKiloCompatSkillMirrorRel -PlatformId $platformId
        $mirrorPath = Join-Path $ProjectRoot $mirrorRel
        $item = Get-Item -LiteralPath $targetPath -Force -ErrorAction SilentlyContinue
        $pointsToSource = Test-CgOwnedJunction -Item $item -ExpectedTarget $sourcePath
        $pointsToMirror = Test-CgOwnedJunction -Item $item -ExpectedTarget $mirrorPath
        if (-not $pointsToSource -and -not $pointsToMirror) { continue }

        try {
            Assert-CgManagedCopyTargetSafe -Target (Split-Path $targetPath -Parent)
            Assert-CgManagedCopyTargetSafe -Target $mirrorPath
        } catch {
            Write-Warning "  $targetRel compatibility path crosses a link or reparse point; manual action required; preserving the link."
            continue
        }
        if (-not (Read-CgCopiedDirectoryManifest -Target $mirrorPath -SourceRel $sourceRel)) {
            Write-Warning "  $targetRel compatibility mirror has no valid receipt; manual action required; preserving the link."
            continue
        }

        if ($pointsToSource) {
            Set-CgJunctionTargetSafely -Path $targetPath -Target $mirrorPath
            Write-Host "  $targetRel - localized for Kilo compatibility discovery" -ForegroundColor DarkGray
        } else {
            Write-Host "  $targetRel - Kilo compatibility mirror updated" -ForegroundColor DarkGray
        }
        [void]$protected.Add($targetRel)
        [void]$protected.Add($mirrorRel)
    }
    return @($protected)
}

function Update-CgGitignoreBlock {
    param([string[]]$Entries)
    $gitignorePath = Join-Path $ProjectRoot ".gitignore"
    $marker = "# Compound GPID managed items (junctions + copied file - do not commit)"
    $pattern = "(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.claude/|\.agents/|\.opencode/|\.kilo/|\.compound-gpid/)[^\r\n]*\r?\n)*"

    $uniqueEntries = @($Entries | Where-Object { $_ } | Sort-Object -Unique)
    if ($uniqueEntries.Count -eq 0) { return }
    $block = $marker + "`n" + ($uniqueEntries -join "`n") + "`n"

    $content = ""
    if (Test-Path $gitignorePath) {
        $content = Get-Content $gitignorePath -Raw -ErrorAction SilentlyContinue
    }
    if ($content -and $content -notmatch '\r?\n$') { $content += "`n" }
    $cleaned = $content -replace $pattern, ""
    $cleaned = $cleaned -replace '(?m)^# Compound GPID knowledge base[^\r\n]*\r?\n\.cg-docs/\r?\n?', ''
    $cleaned = ($cleaned -replace '(?m)^\.cg-docs/\r?\n?', '').TrimEnd()
    $separator = ""
    if ($cleaned.Length -gt 0) { $separator = "`n`n" }
    $utf8NoBom = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
    [System.IO.File]::WriteAllText($gitignorePath, ($cleaned + $separator + $block), $utf8NoBom)
    Write-Host "Updated CG entries in .gitignore" -ForegroundColor DarkGray
}

function Get-CgInstalledGitignoreEntries {
    param(
        $Mapping,
        [hashtable]$Manifest
    )

    $entries = New-Object System.Collections.ArrayList
    foreach ($target in @($Mapping.targets)) {
        foreach ($unit in @($target.installUnits)) {
            $targetRel = ConvertTo-CgSlashPath ([string]$unit.target)
            $sourceRel = ConvertTo-CgSlashPath ([string]$unit.source)
            $targetPath = Join-Path $ProjectRoot $targetRel
            if ([string]$unit.type -eq "directory") {
                $item = Get-Item -Path $targetPath -ErrorAction SilentlyContinue
                $sourcePath = Join-Path $CompoundGpidDir $sourceRel
                if (Test-CgOwnedJunction -Item $item -ExpectedTarget $sourcePath) {
                    [void]$entries.Add($targetRel)
                } elseif ([string]$unit.strategy -eq "copy-directory" -and
                          (Read-CgCopiedDirectoryManifest -Target $targetPath -SourceRel $sourceRel)) {
                    [void]$entries.Add($targetRel)
                }
            } elseif ($targetRel -eq ".github/copilot-instructions.md") {
                if (Test-Path $targetPath) {
                    $content = Get-Content $targetPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
                    if ($content -and $content -match [regex]::Escape($CopilotInstructionsMarker)) {
                        [void]$entries.Add($targetRel)
                    }
                }
            } elseif ($Manifest.files[$targetRel] -and (Test-Path $targetPath)) {
                [void]$entries.Add($targetRel)
            }
        }
    }

    foreach ($platformId in @("claude-code", "codex", "opencode")) {
        $target = @($Mapping.targets | Where-Object { $_.id -eq $platformId })[0]
        if (-not $target) { continue }
        $targetRel = ConvertTo-CgSlashPath ([string]$target.outputPaths.skills)
        $targetPath = Join-Path $ProjectRoot $targetRel
        $mirrorRel = Get-CgKiloCompatSkillMirrorRel -PlatformId $platformId
        $mirrorPath = Join-Path $ProjectRoot $mirrorRel
        $item = Get-Item -LiteralPath $targetPath -Force -ErrorAction SilentlyContinue
        if ((Test-CgOwnedJunction -Item $item -ExpectedTarget $mirrorPath) -and
            (Read-CgCopiedDirectoryManifest -Target $mirrorPath -SourceRel $targetRel)) {
            [void]$entries.Add($targetRel)
            [void]$entries.Add($mirrorRel)
        }
    }

    if ($Manifest.files.Count -gt 0) { [void]$entries.Add(".compound-gpid/managed-files.json") }
    return @($entries | Sort-Object -Unique)
}

function Remove-CgLegacyModelMappingFiles {
    param([hashtable]$Manifest)

    $legacyTargets = @(
        ".claude/model-mapping.claude.json",
        ".agents/model-mapping.codex.json",
        ".opencode/model-mapping.opencode.json",
        ".kilo/model-mapping.kilo.json"
    )

    foreach ($targetRel in $legacyTargets) {
        $record = $Manifest.files[$targetRel]
        if (-not $record) { continue }

        $targetPath = Join-Path $ProjectRoot ($targetRel -replace '/', [System.IO.Path]::DirectorySeparatorChar)
        $item = Get-Item -Path $targetPath -ErrorAction SilentlyContinue
        if ($item -and -not $item.PSIsContainer -and -not $item.LinkType) {
            if ((Get-CgFileSha256 -Path $targetPath) -eq [string]$record.checksum) {
                Remove-Item -Path $targetPath -Force
                Write-Host "  $targetRel - removed legacy model mapping" -ForegroundColor DarkGray
            } else {
                Write-Warning "  $targetRel is user-modified; preserving it and dropping CG ownership."
            }
        }
        [void]$Manifest.files.Remove($targetRel)
    }

    if ($Manifest.files.Count -eq 0 -and (Test-Path $ManifestPath)) {
        Remove-Item -Path $ManifestPath -Force
    }
}

if (-not (Test-Path $CompoundGpidDir)) {
    Write-Error "Compound GPID installation directory not found at: $CompoundGpidDir$CG_INSTALL_GUIDANCE"
    exit 1
}
if (-not (Test-Path $TargetMappingPath)) {
    Write-Error "Target mapping not found at: $TargetMappingPath"
    exit 1
}

Write-Host ""
if ($env:CG_SKIP_UPDATE -eq "1") {
    Write-Host "Skipping Compound GPID update (CG_SKIP_UPDATE=1)." -ForegroundColor DarkGray
} else {
    Write-Host "Updating Compound GPID..." -ForegroundColor Cyan
    $env:CG_INTERNAL_CALL = "1"
    try {
        & "$CompoundGpidDir\scripts\update.ps1"
        if ($LASTEXITCODE -ne 0) {
            throw "cg-update failed with exit code $LASTEXITCODE"
        }
    } catch {
        Write-Error "Could not update and validate Compound GPID; linking is blocked: $_"
        exit 1
    } finally {
        Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
    }
}

$versionFile = Join-Path $CompoundGpidDir ".cg-version"
$activeVersion = "latest"
if (Test-Path $versionFile) { $activeVersion = (Get-Content $versionFile -Raw).Trim() }
if ([string]::IsNullOrWhiteSpace($activeVersion)) { $activeVersion = "latest" }
$versionLabel = "tracking main (latest)"
if ($activeVersion -ne "latest") { $versionLabel = "$activeVersion (pinned)" }

Write-Host "  Version: $versionLabel" -ForegroundColor DarkGray
Write-Host ""
Write-Host "Compound GPID - Link" -ForegroundColor Cyan
Write-Host "====================" -ForegroundColor Cyan
Write-Host "Platforms: $($selectedPlatforms -join ', ')" -ForegroundColor DarkGray
Write-Host ""

$mapping = Get-Content $TargetMappingPath -Raw -Encoding UTF8 | ConvertFrom-Json
$targets = @($mapping.targets | Where-Object { $_.id -in $selectedPlatforms })
$missingSources = @()

foreach ($target in $targets) {
    foreach ($unit in @($target.installUnits)) {
        $sourceRel = [string]$unit.source
        $source = Join-Path $CompoundGpidDir $sourceRel
        if (-not (Test-Path $source)) { $missingSources += "$($target.id): $sourceRel" }
    }
}

if ($missingSources.Count -gt 0) {
    Write-Error "Selected Compound GPID source units are missing:`n  $($missingSources -join "`n  ")"
    exit 1
}

$manifestDriven = Test-Path -LiteralPath (Join-Path $ProjectRoot "compound-gpid.local.md")
$compProjectionStateDir = Join-Path $ProjectRoot ".compound-gpid"
if ($manifestDriven) {
    try {
        $resolvedManifest = Resolve-CgActiveManifest -ProjectRoot $ProjectRoot -SourceRoot $CompoundGpidDir -PlatformIds ($selectedPlatforms -join ",")
        foreach ($line in ($resolvedManifest.Output -split "`r?`n")) {
            if ($line.StartsWith("compound-gpid.local.md has no settings block;")) { Write-Host $line }
        }
        Write-Host "  Active manifest: resolved for $($selectedPlatforms -join ', ')" -ForegroundColor DarkGray
    } catch {
        Write-Error "Linking is blocked by active manifest resolution failure: $_"
        exit 1
    }
}

# Retire proven plugin residue after selection validation, before ownership refresh.
$retirementPython = Resolve-PythonCommand
if (-not $retirementPython) { throw "Python is required for native-evidence residue checks." }
& $retirementPython (Join-Path $PSScriptRoot "cg_retire_native_evidence.py") --root $ProjectRoot
if ($LASTEXITCODE -ne 0) { throw "Linking is blocked by preserved native-evidence residue; review the diagnostics above." }

$manifest = Read-CgManagedFilesManifest -ManifestPath $ManifestPath
$managedFileCountBeforeCleanup = $manifest.files.Count
Remove-CgLegacyModelMappingFiles -Manifest $manifest
$installedEntries = New-Object System.Collections.ArrayList

# Manifest-driven consumers materialize native generated-tree roots as real
# project-local directories through the projection synchronizer. Their legacy
# link-directory/copy-directory install units are therefore skipped: creating a
# junction/copy first would make the no-follow synchronizer reject the root
# (link/reparse destination). Copilot (canonical .github) and legacy
# (non-manifest) consumers keep the legacy junction/copy path.
# Copilot skills are the hybrid exception: target-mapping projectedCategories
# delegates only that category to the Python projection worker, while prompts,
# agents, instructions, and shared keep their existing install topology.

foreach ($target in $targets) {
    Write-Host "Linking $($target.name)..." -ForegroundColor DarkGray
    $nativeProjected = ($null -ne $target.generatedTreePath)
    $projectedCategories = @()
    if ($target.PSObject.Properties.Name -contains "projectedCategories") {
        $projectedCategories = @($target.projectedCategories)
    }
    foreach ($unit in @($target.installUnits)) {
        $targetRel = ConvertTo-CgSlashPath ([string]$unit.target)
        $rootName = Get-CgTargetRoot -RelativePath $targetRel
        if (-not (Ensure-CgRootDirectory -RootName $rootName)) {
            [void]$script:CopyArgs.Add("--manual-path")
            [void]$script:CopyArgs.Add($rootName)
            continue
        }

        if ($manifestDriven -and $nativeProjected -and
            ([string]$unit.type -eq "directory")) {
            Write-Host "  $targetRel - projected by manifest (legacy install skipped)" -ForegroundColor DarkGray
            continue
        }
        if ($manifestDriven -and $targetRel -eq ".github/skills" -and
            "skills" -in $projectedCategories) {
            Write-Host "  $targetRel - Copilot skills projected by manifest" -ForegroundColor DarkGray
            continue
        }

        $installed = $false
        if ([string]$unit.type -eq "directory") {
            $installed = Install-CgDirectoryUnit -SourceRel ([string]$unit.source) -TargetRel $targetRel -Strategy ([string]$unit.strategy) -Force $Force
            if (-not $installed) {
                [void]$script:CopyArgs.Add("--manual-path")
                [void]$script:CopyArgs.Add($targetRel)
            }
        } else {
            # Only refreshed worker receipts identify successfully managed files.
            [void](Install-CgFileUnit -Unit $unit -Manifest $manifest)
        }

        if ($installed) { [void]$installedEntries.Add($targetRel) }
    }
}

# Persist the existing cleanup result before the worker refreshes scalar records.
if ($manifest.files.Count -gt 0 -and $manifest.files.Count -ne $managedFileCountBeforeCleanup) {
    Write-CgManagedFilesManifest -ManifestPath $ManifestPath -Manifest $manifest
}
$copyPython = Resolve-PythonCommand -NoBytecode
if (-not $copyPython) { throw "Python 3.8+ is required for the shared copy worker." }
$copyArguments = @("--source-root", $CompoundGpidDir, "--project-root", $ProjectRoot, "--sync-projection") + @($script:CopyArgs)
$copyErrorAction = $ErrorActionPreference
try {
    $ErrorActionPreference = "Continue"
    $copyOutput = @(& $copyPython -B (Join-Path $PSScriptRoot "cg_kilo_copy.py") @copyArguments 2>&1)
} finally { $ErrorActionPreference = $copyErrorAction }
$copyOutput = @($copyOutput | ForEach-Object { $_.ToString() })
$copyOutput | Out-Host
if ($LASTEXITCODE -ne 0) {
    throw "Shared copy or manifest projection synchronization failed with exit code $LASTEXITCODE; review the diagnostics above."
}
# Do not let the final writer restore the pre-batch scalar ownership records.
$manifest = Read-CgManagedFilesManifest -ManifestPath $ManifestPath

# The batch publishes manifest-driven roots before local Kilo preflight.
# Keep their runtime output in the managed ignore block without syncing again.
if ((Test-Path -LiteralPath $compProjectionStateDir) -and
    (Test-Path -LiteralPath (Join-Path $compProjectionStateDir "active-manifest.json"))) {
    Write-Host "  Project projection: synced and verified" -ForegroundColor DarkGray

    # Generated projection roots are reproducible runtime output. Keep them in
    # the managed gitignore block while leaving active-manifest.json reviewable.
    foreach ($platformId in $selectedPlatforms) {
        $selectedTarget = @($mapping.targets | Where-Object { $_.id -eq $platformId })[0]
        foreach ($managedRoot in @($selectedTarget.projectRoots.managed)) {
            if (-not [string]::IsNullOrWhiteSpace([string]$managedRoot)) {
                [void]$installedEntries.Add((ConvertTo-CgSlashPath ([string]$managedRoot)))
            }
        }
    }
    foreach ($runtimeEntry in @(
        ".compound-gpid/active/",
        ".compound-gpid/generations/",
        ".compound-gpid/projection-ownership.json",
        ".compound-gpid/projection-transaction.json",
        ".compound-gpid/staging/",
        ".compound-gpid/quarantine/",
        ".compound-gpid/retired/",
        ".compound-gpid/*.tmp",
        ".compound-gpid/*.bak"
    )) {
        [void]$installedEntries.Add($runtimeEntry)
    }
}

foreach ($entry in @(Protect-CgKiloCompatibilitySkillLinks -Mapping $mapping)) {
    [void]$installedEntries.Add($entry)
}

if ($manifest.files.Count -gt 0) {
    Write-CgManagedFilesManifest -ManifestPath $ManifestPath -Manifest $manifest
    [void]$installedEntries.Add(".compound-gpid/managed-files.json")
}

# Validate generated Kilo files without discovering or running a Kilo host.
# Existing user-level skill roots are not evidence of a managed projection.
$kiloSelected = "kilo" -in $selectedPlatforms
$compatibilityPresent = (Test-Path -LiteralPath (Join-Path $ProjectRoot ".agents\skills")) -or
    (Test-Path -LiteralPath (Join-Path $ProjectRoot ".claude\skills"))
$kiloRootPresent = Test-Path -LiteralPath (Join-Path $ProjectRoot ".kilo\skills")
$kiloManagedCopy = Test-Path -LiteralPath (Join-Path $ProjectRoot ".kilo/skills/.compound-gpid-managed-copy.json") -PathType Leaf
if ($kiloSelected -or $kiloManagedCopy) {
    $copyHasKiloManual = @($copyOutput | Where-Object { $_ -match '^Kilo validation deferred: [1-9][0-9]*$' }).Count -gt 0
    if ($copyHasKiloManual) {
        Write-Warning "Kilo validation deferred: kept Kilo files need manual action; use cg-link --check after resolving them."
    } else {
        try {
            $kiloPreflight = Invoke-CgKiloPreflight -ProjectRoot $ProjectRoot -LocalOnly
            Write-Host "  Kilo preflight: $($kiloPreflight.status)" -ForegroundColor DarkGray
        } catch {
            $preflightExitCode = 1
            if ($_.Exception.Data.Contains("CgExitCode")) { $preflightExitCode = [int]$_.Exception.Data["CgExitCode"] }
            Write-Error "Linking is blocked by local generated Kilo file validation: $_"
            exit $preflightExitCode
        }
    }
}
if ($kiloRootPresent -and $compatibilityPresent) {
    Write-Host "Note: Kilo and compatibility skills coexist. Use cg-kilo for an optional contained launch." -ForegroundColor Yellow
}

if ("kilo" -in $selectedPlatforms) {
    Update-CgKiloGlobalPermission -CompoundGpidDir $CompoundGpidDir | Out-Null
}

Update-CgGitignoreBlock -Entries (@($installedEntries) + (Get-CgInstalledGitignoreEntries -Mapping $mapping -Manifest $manifest))

Write-Host ""
Write-Host "Platform availability checks:" -ForegroundColor DarkGray
$checks = @{
    "copilot" = ".github/prompts/cg-setup.prompt.md"
    "claude-code" = ".claude/commands/cg-plan.md"
    "codex" = ".agents/commands/cg-plan.md"
    "opencode" = ".opencode/commands/cg-plan.md"
    "kilo" = ".kilo/commands/cg-plan.md"
}
foreach ($platform in $selectedPlatforms) {
    $rel = $checks[$platform]
    if ($rel -and (Test-Path (Join-Path $ProjectRoot $rel))) {
        Write-Host "  $platform - available" -ForegroundColor DarkGray
    } else {
        Write-Warning "  $platform - not fully available; review skipped units above."
    }
}

Write-Host ""
Write-Host "Linked!" -ForegroundColor Green
Write-Host ""
Write-Host "Compound GPID assets are now available for: $($selectedPlatforms -join ', ')."
Write-Host "Use --platforms copilot to install only Copilot assets, or --platforms kilo for Kilo-only assets."
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "  Managed linked directories and copied files should not be edited directly." -ForegroundColor Yellow
Write-Host "  If a config file was skipped, apply the printed manual snippet if needed." -ForegroundColor Yellow
Write-Host ""
Write-Host "Restart your AI coding tool so it reloads commands, skills, agents, and config." -ForegroundColor Yellow
Write-Host ""
