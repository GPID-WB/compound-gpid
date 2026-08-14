# scripts/link.ps1
# Links the current project to Compound GPID using per-install-unit junctions and
# managed copied files. Existing project-owned platform roots are preserved.

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$RawArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$onWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))
if (-not $onWindows) {
    Write-Error @"
link.ps1 is Windows-only (it uses directory junctions).
On macOS/Linux, use link.sh instead:
  cg-link
(which calls scripts/link.sh automatically via the bash wrapper in bin/)
"@
    exit 1
}

$CompoundGpidDir = Split-Path $PSScriptRoot -Parent
$ProjectRoot = (Get-Location).Path
$TargetMappingPath = Join-Path $CompoundGpidDir ".github/shared/target-mapping.json"
$ManifestPath = Join-Path $ProjectRoot ".compound-gpid/managed-files.json"
$CopilotInstructionsMarker = "<!-- compound-gpid:managed -->"
$CopiedDirectoryMarkerName = ".compound-gpid-managed-copy.json"

. (Join-Path $PSScriptRoot "helpers.ps1")

function Resolve-CgLinkArguments {
    param([object[]]$Arguments)
    # Zero-arg invocation (e.g. CI E2E: `link.ps1` with no flags) yields
    # $null here via ValueFromRemainingArguments; .Count on $null throws under
    # Set-StrictMode -Version Latest.
    if ($null -eq $Arguments) { $Arguments = @() }
    $result = @{ Force = $false; Platforms = $null }
    for ($i = 0; $i -lt $Arguments.Count; $i++) {
        $arg = [string]$Arguments[$i]
        if ($arg -in @("--yes", "-y", "-Force", "--force")) {
            $result.Force = $true
        } elseif ($arg -like "--platforms=*") {
            $result.Platforms = $arg.Substring("--platforms=".Length)
        } elseif ($arg -like "-Platforms=*") {
            $result.Platforms = $arg.Substring("-Platforms=".Length)
        } elseif ($arg -in @("--platforms", "-Platforms")) {
            if ($i + 1 -ge $Arguments.Count) { throw "Missing value after $arg" }
            $i++
            $result.Platforms = [string]$Arguments[$i]
        } elseif ($arg -eq "") {
            continue
        } else {
            Write-Warning "Unrecognized argument '$arg' - ignoring."
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

    foreach ($item in $unknown) { Write-Warning "Unknown platform '$item' - skipping." }
    if ($selected.Count -eq 0) {
        throw "No valid platforms selected. Supported platforms: $($supported -join ', ')"
    }
    return @($selected)
}

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

function Test-CgCopyPathHasReparsePoint {
    param(
        [string]$Base,
        [string]$ResolvedPath
    )

    # A reparse point in ANY ancestor (not just the leaf) could redirect a
    # managed write or stale-file removal outside $Base (e.g. a `..`-backed
    # marker key could turn a delete into an escape). Missing intermediate
    # components are skipped so pre-materialization checks stay correct.
    $baseFull = Get-CgNormalizedFullPath $Base
    $relative = $ResolvedPath.Substring($baseFull.Length).TrimStart([char[]]@('\', '/'))
    $current = $baseFull
    foreach ($part in @($relative -split '[\\/]')) {
        if (-not $part) { continue }
        $current = Join-Path $current $part
        if (-not (Test-Path -LiteralPath $current)) { continue }
        $item = Get-Item -LiteralPath $current -Force
        if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            return $true
        }
    }
    return $false
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
    if (($markerItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
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

function Write-CgCopiedDirectoryManifest {
    param(
        [string]$Target,
        [string]$SourceRel,
        [hashtable]$Files
    )

    $markerPath = Resolve-CgContainedCopyPath -Base $Target -RelativePath $CopiedDirectoryMarkerName
    if (Test-Path -LiteralPath $markerPath) {
        $markerItem = Get-Item -LiteralPath $markerPath -Force
        if (($markerItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing to write a managed-copy marker through a reparse point: $markerPath"
        }
    }
    $data = [ordered]@{
        schemaVersion = 1
        source = (ConvertTo-CgSlashPath $SourceRel)
        files = $Files
    }
    $json = ($data | ConvertTo-Json -Depth 4) + "`n"
    $utf8NoBom = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
    $writeId = [System.Guid]::NewGuid().ToString('N')
    $temporaryPath = "$markerPath.tmp-$writeId"
    $backupPath = "$markerPath.bak-$writeId"
    try {
        # Write to a sibling temp file on the same volume, then atomically
        # replace so a crash mid-write can never leave a half-written marker.
        [System.IO.File]::WriteAllText($temporaryPath, $json, $utf8NoBom)
        if (Test-Path -LiteralPath $markerPath) {
            [System.IO.File]::Replace($temporaryPath, $markerPath, $backupPath)
        } else {
            [System.IO.File]::Move($temporaryPath, $markerPath)
        }
    } finally {
        if (Test-Path -LiteralPath $temporaryPath) {
            Remove-Item -LiteralPath $temporaryPath -Force
        }
        if (Test-Path -LiteralPath $backupPath) {
            Remove-Item -LiteralPath $backupPath -Force
        }
    }
}

function Sync-CgCopiedDirectory {
    param(
        [string]$Source,
        [string]$SourceRel,
        [string]$Target,
        [string]$TargetRel,
        [hashtable]$PreviousManifest
    )

    # Write policy: a destination is overwritten only when it is absent,
    # byte-identical to the source, or byte-identical to the previous managed
    # checksum (a revert to the last managed state). Anything else is treated
    # as user-owned and preserved with a warning. Files recorded in the
    # previous manifest but absent from the source are removed STALE only when
    # their current bytes still match the previously recorded checksum.
    #
    # copy-directory semantics: Windows preserves user edits and removes stale
    # managed files via this checksum manifest; the POSIX link.sh uses a
    # wholesale overwrite (see link.sh copy-directory branch). This divergence
    # is intentional and asserted in tests/parity.Tests.ps1.
    if (-not (Test-Path -LiteralPath $Target)) {
        New-Item -ItemType Directory -Path $Target -Force | Out-Null
    }
    $sourceRoot = Get-CgNormalizedFullPath $Source
    $sourcePaths = @{}
    $nextFiles = @{}
    foreach ($sourceFile in @(Get-ChildItem -LiteralPath $Source -File -Recurse -Force)) {
        $relative = ConvertTo-CgSlashPath ($sourceFile.FullName.Substring($sourceRoot.Length).TrimStart([char[]]@('\', '/')))
        if ($relative -eq $CopiedDirectoryMarkerName) { continue }
        $sourcePaths[$relative] = $true
        $destination = Resolve-CgContainedCopyPath -Base $Target -RelativePath $relative

        # Cheap guards first: a reparse point anywhere along the destination
        # path or a directory/link collision must reject the file before any
        # hashing or copy happens.
        if (Test-CgCopyPathHasReparsePoint -Base $Target -ResolvedPath $destination) {
            Write-Warning "  $TargetRel/$relative crosses a reparse point; preserving it."
            continue
        }
        $canWrite = -not (Test-Path -LiteralPath $destination)
        if (-not $canWrite) {
            $destinationItem = Get-Item -LiteralPath $destination -Force
            if ($destinationItem.PSIsContainer -or $destinationItem.LinkType) {
                Write-Warning "  $TargetRel/$relative conflicts with a directory or link; preserving it."
                continue
            }
        }

        $sourceChecksum = Get-CgFileSha256 -Path $sourceFile.FullName
        $previousChecksum = $null
        if ($PreviousManifest -and $PreviousManifest.files.ContainsKey($relative)) {
            $previousChecksum = [string]$PreviousManifest.files[$relative]
        }

        if (-not $canWrite) {
            $currentChecksum = Get-CgFileSha256 -Path $destination
            if ($currentChecksum -eq $sourceChecksum) {
                $nextFiles[$relative] = $sourceChecksum
                continue
            }
            if ($previousChecksum -and $currentChecksum -eq $previousChecksum) {
                $canWrite = $true
            } else {
                Write-Warning "  $TargetRel/$relative was modified or is user-owned; preserving it."
                # Keep recording the last-known managed checksum so the file
                # stays tracked for later reconciliation/cleanup; dropping it
                # would make the user's edit silently deletable later when the
                # source path disappears.
                if ($previousChecksum) { $nextFiles[$relative] = $previousChecksum }
                continue
            }
        }

        if ($canWrite) {
            $destinationParent = Split-Path $destination -Parent
            if (-not (Test-Path -LiteralPath $destinationParent)) {
                New-Item -ItemType Directory -Path $destinationParent -Force | Out-Null
            }
            Copy-Item -LiteralPath $sourceFile.FullName -Destination $destination -Force
            $nextFiles[$relative] = $sourceChecksum
        }
    }

    if ($PreviousManifest) {
        foreach ($relative in @($PreviousManifest.files.Keys)) {
            if ($sourcePaths.ContainsKey($relative)) { continue }
            $destination = Resolve-CgContainedCopyPath -Base $Target -RelativePath $relative
            if (Test-CgCopyPathHasReparsePoint -Base $Target -ResolvedPath $destination) {
                Write-Warning "  $TargetRel/$relative crosses a reparse point; preserving it."
                continue
            }
            if (-not (Test-Path -LiteralPath $destination -PathType Leaf)) { continue }
            $currentChecksum = Get-CgFileSha256 -Path $destination
            if ($currentChecksum -eq [string]$PreviousManifest.files[$relative]) {
                Remove-Item -LiteralPath $destination -Force
                Write-Host "  $TargetRel/$relative - removed stale managed file" -ForegroundColor DarkGray
            } else {
                Write-Warning "  $TargetRel/$relative is stale but user-modified; preserving it."
            }
        }
    }

    Write-CgCopiedDirectoryManifest -Target $Target -SourceRel $SourceRel -Files $nextFiles
}

function Ensure-CgRootDirectory {
    param([string]$RootName)
    $rootPath = Join-Path $ProjectRoot $RootName
    $expectedRoot = Join-Path $CompoundGpidDir $RootName
    $existing = Get-Item -Path $rootPath -ErrorAction SilentlyContinue
    if ($existing -and (Test-CgOwnedJunction -Item $existing -ExpectedTarget $expectedRoot)) {
        Write-Host "  $RootName/ - migrating legacy whole-root junction" -ForegroundColor Yellow
        Remove-CgJunction -Path $rootPath
        New-Item -ItemType Directory -Path $rootPath -Force | Out-Null
        return $true
    }
    if ($existing -and $existing.LinkType) {
        Write-Warning "  $RootName/ is a non-Compound link; skipping units under it."
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
    $existing = Get-Item -Path $target -ErrorAction SilentlyContinue
    $copyManifest = $null

    if ($existing) {
        if ($existing.LinkType -eq "Junction") {
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
                Write-Warning "  $TargetRel is a junction pointing to: $($existing.Target)"
                if (-not $Force) {
                    $answer = Read-Host "  Relink $TargetRel to Compound GPID instead? [y/N]"
                    if ($answer -notmatch "^[Yy]$") {
                        Write-Host "  $TargetRel - skipped" -ForegroundColor Yellow
                        return $false
                    }
                }
                Remove-CgJunction -Path $target
                $existing = $null
            }
        } elseif ($existing.LinkType) {
            Write-Warning "  $TargetRel is a non-junction link; skipping this unit."
            return $false
        } elseif ($existing.PSIsContainer) {
            if ($Strategy -eq "copy-directory") {
                # A real directory at a copy-directory target is almost always
                # a prior CG copy, an empty/partial tree from an aborted run, or
                # a directory whose marker was lost/corrupted. Rather than
                # skipping and silently losing the install (P2.6/P2.10), sync
                # from baseline: absent files are copied, user-modified, dir-,
                # and link-conflicted files are preserved with a warning, and a
                # fresh marker is written. With no previous manifest the
                # stale-file removal is disabled, so a baseline sync can never
                # delete unrecorded user files.
                $copyManifest = Read-CgCopiedDirectoryManifest -Target $target -SourceRel $SourceRel
                if ($copyManifest) {
                    Write-Host "  $TargetRel - already a managed real directory (will update)" -ForegroundColor DarkGray
                } else {
                    Write-Warning "  $TargetRel is a real directory without a valid managed-copy marker; performing a baseline sync (user files preserved)."
                    $copyManifest = $null
                }
            } else {
                Write-Warning "  $TargetRel is a real directory; skipping this unit."
                return $false
            }
        } else {
            Write-Warning "  $TargetRel exists as a file; skipping this unit."
            return $false
        }
    }

    $parent = Split-Path $target -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    if ($Strategy -eq "copy-directory") {
        $python = Resolve-PythonCommand
        if (-not $python) {
            throw "Python 3.8+ is required for the shared Kilo copy worker."
        }
        $worker = Join-Path $PSScriptRoot "cg_kilo_copy.py"
        & $python $worker --source $source --target $target --source-relative (ConvertTo-CgSlashPath $SourceRel)
        if ($LASTEXITCODE -ne 0) {
            throw "Shared Kilo copy worker failed for $TargetRel with exit code $LASTEXITCODE"
        }
        $copied = Get-Item -LiteralPath $target -Force
        if ($copied.LinkType) {
            throw "copy-directory invariant failed for $TargetRel`: target is still a $($copied.LinkType)."
        }
        Write-Host "  $TargetRel - copied" -ForegroundColor DarkGray
    } else {
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
    $target = Join-Path $ProjectRoot $targetRel

    if ([string]$Unit.strategy -eq "generated-copy") {
        $generated = New-CopilotInstructions -TemplateDir $CompoundGpidDir -ProjectRoot $ProjectRoot
        $existing = $null
        if (Test-Path $target) {
            $existing = Get-Content $target -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        }
        $userManaged = $existing -and ($existing -notmatch [regex]::Escape($CopilotInstructionsMarker))
        if ($userManaged) {
            Write-Host "  $targetRel - user-managed (marker absent), skipping" -ForegroundColor Yellow
            return $false
        }
        $parent = Split-Path $target -Parent
        if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
        if ($generated -ne $existing) { Set-Content -Path $target -Value $generated -Encoding UTF8 }
        Write-Host "  $targetRel - generated" -ForegroundColor DarkGray
        return $true
    }

    $source = Join-Path $CompoundGpidDir $sourceRel
    $currentChecksum = Get-CgFileSha256 -Path $target
    $record = $Manifest.files[$targetRel]
    $canWrite = -not (Test-Path $target)
    if (-not $canWrite -and $record -and $currentChecksum -eq $record.checksum) {
        $canWrite = $true
    }

    if (-not $canWrite) {
        Write-Warning "  $targetRel exists and is not manifest-managed; skipping."
        if ($Unit.PSObject.Properties.Name -contains "manualSnippet") {
            Write-Host "  Manual config snippet: $($Unit.manualSnippet)" -ForegroundColor Yellow
        }
        return $false
    }

    $parent = Split-Path $target -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    Copy-Item -Path $source -Destination $target -Force
    $Manifest.files[$targetRel] = @{
        source = $sourceRel
        checksum = (Get-CgFileSha256 -Path $target)
    }
    Write-Host "  $targetRel - copied" -ForegroundColor DarkGray
    return $true
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

$argsParsed = Resolve-CgLinkArguments -Arguments $RawArgs
$Force = [bool]$argsParsed.Force
$selectedPlatforms = Resolve-CgPlatforms -PlatformsValue $argsParsed.Platforms

# Check host containment before any update, copy, manifest, or global Kilo
# permission mutation. The post-copy validation below remains necessary for
# local projection/content ownership checks.
$preflightKiloSelected = "kilo" -in $selectedPlatforms
$preflightCompatibilitySelected = ("codex" -in $selectedPlatforms) -or ("claude-code" -in $selectedPlatforms)
$preflightCompatibilityPresent = (Test-Path -LiteralPath (Join-Path $ProjectRoot ".agents\skills")) -or
    (Test-Path -LiteralPath (Join-Path $ProjectRoot ".claude\skills"))
if ($preflightKiloSelected -and ($preflightCompatibilitySelected -or $preflightCompatibilityPresent)) {
    try {
        [void](Invoke-CgKiloPreflight -ProjectRoot $ProjectRoot -RequireCoexistence -HostOnly)
    } catch {
        $preflightExitCode = 1
        if ($_.Exception.Data.Contains("CgExitCode")) { $preflightExitCode = [int]$_.Exception.Data["CgExitCode"] }
        Write-Error "Linking is blocked by Kilo host preflight: $_"
        exit $preflightExitCode
    }
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

$manifest = Read-CgManagedFilesManifest -ManifestPath $ManifestPath
Remove-CgLegacyModelMappingFiles -Manifest $manifest
$installedEntries = New-Object System.Collections.ArrayList

foreach ($target in $targets) {
    Write-Host "Linking $($target.name)..." -ForegroundColor DarkGray
    foreach ($unit in @($target.installUnits)) {
        $targetRel = ConvertTo-CgSlashPath ([string]$unit.target)
        $rootName = Get-CgTargetRoot -RelativePath $targetRel
        if (-not (Ensure-CgRootDirectory -RootName $rootName)) { continue }

        $installed = $false
        if ([string]$unit.type -eq "directory") {
            $installed = Install-CgDirectoryUnit -SourceRel ([string]$unit.source) -TargetRel $targetRel -Strategy ([string]$unit.strategy) -Force $Force
        } else {
            $installed = Install-CgFileUnit -Unit $unit -Manifest $manifest
        }

        if ($installed) { [void]$installedEntries.Add($targetRel) }
    }
}

if ($manifest.files.Count -gt 0) {
    Write-CgManagedFilesManifest -ManifestPath $ManifestPath -Manifest $manifest
    [void]$installedEntries.Add(".compound-gpid/managed-files.json")
}

if ("kilo" -in $selectedPlatforms) {
    Update-CgKiloGlobalPermission -CompoundGpidDir $CompoundGpidDir | Out-Null
}

# Kilo can discover Codex/Claude skill roots from the same project. A combined
# selection is supported only through the certified child-process launcher; a
# Kilo-only project needs only local projection validation at link time.
$kiloSelected = "kilo" -in $selectedPlatforms
$compatibilitySelected = ("codex" -in $selectedPlatforms) -or ("claude-code" -in $selectedPlatforms)
$compatibilityPresent = (Test-Path -LiteralPath (Join-Path $ProjectRoot ".agents\skills")) -or
    (Test-Path -LiteralPath (Join-Path $ProjectRoot ".claude\skills"))
$kiloRootPresent = Test-Path -LiteralPath (Join-Path $ProjectRoot ".kilo\skills")
if ($kiloSelected -or ($compatibilityPresent -and $kiloRootPresent)) {
    try {
        if ($compatibilitySelected -or $compatibilityPresent) {
            $kiloPreflight = Invoke-CgKiloPreflight -ProjectRoot $ProjectRoot -RequireCoexistence
        } else {
            $kiloPreflight = Invoke-CgKiloPreflight -ProjectRoot $ProjectRoot -LocalOnly
        }
        Write-Host "  Kilo preflight: $($kiloPreflight.status)" -ForegroundColor DarkGray
        if ($kiloPreflight.certified_launch_required) {
            Write-Host "  Certified launch required: cg-kilo (direct Kilo launches unsupported with compatibility roots)." -ForegroundColor Yellow
        }
    } catch {
        $preflightExitCode = 1
        if ($_.Exception.Data.Contains("CgExitCode")) { $preflightExitCode = [int]$_.Exception.Data["CgExitCode"] }
        Write-Error "Linking is blocked by Kilo coexistence preflight: $_"
        exit $preflightExitCode
    }
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
