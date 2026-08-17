# scripts/unlink.ps1
# Removes Compound GPID-managed install units from the current project without
# deleting user-owned platform files.

param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [object[]]$RawArgs
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$onWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))
if (-not $onWindows) {
    Write-Error @"
unlink.ps1 is Windows-only (it manages directory junctions).
On macOS/Linux, use unlink.sh instead:
  cg-unlink
(which calls scripts/unlink.sh automatically via the bash wrapper in bin/)
"@
    exit 1
}

$CompoundGpidDir = Split-Path $PSScriptRoot -Parent
$ProjectRoot = (Get-Location).Path
$TargetMappingPath = Join-Path $CompoundGpidDir ".github/shared/target-mapping.json"
$ManifestPath = Join-Path $ProjectRoot ".compound-gpid/managed-files.json"
$gitignorePath = Join-Path $ProjectRoot ".gitignore"
$CopilotInstructionsMarker = "<!-- compound-gpid:managed -->"
$CopiedDirectoryMarkerName = ".compound-gpid-managed-copy.json"

. (Join-Path $PSScriptRoot "helpers.ps1")

function Resolve-CgUnlinkArguments {
    param([object[]]$Arguments)
    # Zero-arg invocation yields $null here via ValueFromRemainingArguments;
    # foreach over $null is a silent no-op, but guard explicitly for symmetry.
    if ($null -eq $Arguments) { $Arguments = @() }
    $force = $false
    foreach ($argObj in $Arguments) {
        $arg = [string]$argObj
        if ($arg -in @("--yes", "-y", "-Force", "--force")) { $force = $true }
        elseif ($arg) { Write-Warning "Unrecognized argument '$arg' - ignoring." }
    }
    return $force
}

function Test-CgOwnedJunction {
    param($Item)
    if (-not $Item) { return $false }
    return ($Item.LinkType -eq "Junction" -and (($Item.Target -join '') -like "*compound-gpid*"))
}

function Remove-CgCopiedDirectoryUnit {
    param([string]$TargetRel)
    $target = Join-Path $ProjectRoot $TargetRel
    $markerPath = Join-Path $target $CopiedDirectoryMarkerName
    if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) { return $false }

    # Only a directory bearing a valid managed-copy marker is Compound-owned.
    # We delete files whose current checksum still equals the recorded one and
    # preserve anything modified by the user (the same safety contract as
    # Remove-CgManagedFile).
    $data = $null
    try {
        $data = Get-Content -LiteralPath $markerPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        Write-Warning "  $TargetRel has an invalid managed-copy marker; leaving it in place."
        return $false
    }
    # Copy properties into a hashtable before any field access. Under
    # Set-StrictMode -Version Latest, reading a missing property on a parsed
    # JSON object (e.g. a `{}` marker) throws PropertyNotFoundException and
    # would abort the whole unlink run instead of skipping the unit.
    $props = @{}
    if ($data -is [System.Management.Automation.PSCustomObject]) {
        foreach ($property in @($data.PSObject.Properties)) { $props[$property.Name] = $property.Value }
    }
    $filesRaw = $props['files']
    if ($props.Count -eq 0 -or $props['schemaVersion'] -ne 1 -or
        -not ($filesRaw -is [System.Management.Automation.PSCustomObject])) {
        Write-Warning "  $TargetRel has an invalid managed-copy marker; leaving it in place."
        return $false
    }

    $targetFull = [System.IO.Path]::GetFullPath($target).TrimEnd([char[]]@('\', '/'))
    $removedAny = $false
    foreach ($property in @($filesRaw.PSObject.Properties)) {
        $relative = [string]$property.Name
        $filePath = Join-Path $target $relative
        # Defensive containment: the marker is a plain editable file, so a
        # traversal key must never be able to delete a file outside the
        # managed directory. Reject rooted/drive/traversal keys (both `/` and
        # `\` separators) and confirm the canonical path stays under $target.
        $escaped = $true
        if (-not ([System.IO.Path]::IsPathRooted($relative) -or $relative -match '^[A-Za-z]:' -or
            $relative -match '(^|[\\/])\.\.([\\/]|$)' -or $relative -match '\.\.$')) {
            $resolved = [System.IO.Path]::GetFullPath($filePath)
            $prefix = $targetFull + [System.IO.Path]::DirectorySeparatorChar
            if ($resolved.StartsWith($prefix, [System.StringComparison]::OrdinalIgnoreCase)) { $escaped = $false }
        }
        if ($escaped) {
            Write-Warning "  $TargetRel/$relative has an unsafe managed-copy path; leaving it in place."
            continue
        }
        if (-not (Test-Path -LiteralPath $resolved -PathType Leaf)) { continue }
        $current = Get-CgFileSha256 -Path $resolved
        if ($current -eq [string]$property.Value) {
            Remove-Item -LiteralPath $resolved -Force
            Write-Host "  $TargetRel/$relative - managed copy removed" -ForegroundColor DarkGray
            $removedAny = $true
        } else {
            Write-Warning "  $TargetRel/$relative was modified by the user; leaving it in place."
        }
    }

    Remove-Item -LiteralPath $markerPath -Force
    Write-Host "  $TargetRel - managed-copy marker removed" -ForegroundColor DarkGray
    $removedAny = $true

    # Prune empty subdirectories bottom-up, never following or removing
    # junctions (a junction is user-owned even when "empty").
    $subdirs = @(Get-ChildItem -LiteralPath $target -Directory -Recurse -Force -ErrorAction SilentlyContinue |
        Sort-Object { $_.FullName.Length } -Descending)
    foreach ($subdir in $subdirs) {
        if ($subdir.LinkType) { continue }
        if (-not (Get-ChildItem -LiteralPath $subdir.FullName -Force -ErrorAction SilentlyContinue)) {
            Remove-Item -LiteralPath $subdir.FullName -Force
        }
    }
    return $removedAny
}

function Remove-CgJunction {
    param([string]$Path)

    $item = Get-Item -LiteralPath $Path -Force -ErrorAction SilentlyContinue
    if (-not $item -or $item.LinkType -ne "Junction") {
        throw "Refusing to remove non-junction path: $Path"
    }

    # Remove-Item prompts for -Recurse on populated junctions in Windows
    # PowerShell 5.1 (and fails in non-interactive mode). Directory.Delete
    # without recursion removes only the reparse point and never traverses
    # into the shared source directory.
    [System.IO.Directory]::Delete($item.FullName)
}

function Remove-CgDirectoryUnit {
    param([string]$TargetRel)
    $target = Join-Path $ProjectRoot $TargetRel
    $item = Get-Item -Path $target -ErrorAction SilentlyContinue
    if (-not $item) { return $false }
    if (Test-CgOwnedJunction $item) {
        Remove-CgJunction -Path $target
        Write-Host "  $TargetRel - junction removed" -ForegroundColor DarkGray
        return $true
    }
    if ($item.LinkType -eq "Junction") {
        Write-Host "  $TargetRel - non-Compound junction, skipping" -ForegroundColor Yellow
        return $false
    }
    if ($item.PSIsContainer) {
        # Real directory: remove only if it is a managed copy-directory
        # (marker present); otherwise treat as user-owned and skip.
        return Remove-CgCopiedDirectoryUnit -TargetRel $TargetRel
    }
    Write-Host "  $TargetRel - user-owned path, skipping" -ForegroundColor Yellow
    return $false
}

function Remove-CgManagedFile {
    param(
        [string]$TargetRel,
        [hashtable]$Manifest
    )
    $target = Join-Path $ProjectRoot $TargetRel

    if ($TargetRel -eq ".github/copilot-instructions.md") {
        if (Test-Path $target) {
            $content = Get-Content $target -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
            if ($content -and $content -match [regex]::Escape($CopilotInstructionsMarker)) {
                Remove-Item -Path $target -Force
                Write-Host "  $TargetRel - removed" -ForegroundColor DarkGray
                return $true
            }
        }
        return $false
    }

    $record = $Manifest.files[$TargetRel]
    if (-not $record) { return $false }
    if (-not (Test-Path $target)) {
        [void]$Manifest.files.Remove($TargetRel)
        return $false
    }

    $current = Get-CgFileSha256 -Path $target
    if ($current -eq $record.checksum) {
        Remove-Item -Path $target -Force
        [void]$Manifest.files.Remove($TargetRel)
        Write-Host "  $TargetRel - managed file removed" -ForegroundColor DarkGray
        return $true
    }

    [void]$Manifest.files.Remove($TargetRel)
    Write-Warning "  $TargetRel was modified by the user; leaving it in place and dropping CG ownership."
    return $false
}

function Remove-CgGitignoreBlock {
    if (-not (Test-Path $gitignorePath)) { return }
    $content = Get-Content $gitignorePath -Raw -ErrorAction SilentlyContinue
    if (-not $content) { return }
    $pattern = "(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.claude/|\.agents/|\.opencode/|\.kilo/|\.compound-gpid/)[^\r\n]*\r?\n)*"
    $updated = ($content -replace $pattern, "").TrimEnd()
    if ($updated -ne $content.TrimEnd()) {
        if ([string]::IsNullOrWhiteSpace($updated)) {
            Remove-Item $gitignorePath -Force
            Write-Host "  .gitignore - removed (empty after CG cleanup)" -ForegroundColor DarkGray
        } else {
            Set-Content -Path $gitignorePath -Value ($updated + "`n") -Encoding UTF8
            Write-Host "  .gitignore - CG entries removed" -ForegroundColor DarkGray
        }
    }
}

function Remove-CgEmptyRoot {
    param([string]$RootName)
    $rootPath = Join-Path $ProjectRoot $RootName
    if ((Test-Path $rootPath) -and (Get-Item $rootPath).PSIsContainer) {
        $remaining = Get-ChildItem -Path $rootPath -Force -ErrorAction SilentlyContinue
        if (($remaining | Measure-Object).Count -eq 0) {
            Remove-Item -Path $rootPath -Force
            Write-Host "  $RootName/ - empty, removed" -ForegroundColor DarkGray
        }
    }
}

# NOTE: The Kilo markdown_source permission in the global kilo.jsonc is keyed on
# the Compound GPID *installation* path, not the project. Multiple projects may
# share one installation, so removing the permission on unlink would break Kilo
# command loading for any other still-linked project. The permission is therefore
# intentionally left in place on unlink; a stale allow entry is harmless.

$Force = Resolve-CgUnlinkArguments -Arguments $RawArgs
$manifest = Read-CgManagedFilesManifest -ManifestPath $ManifestPath

Write-Host ""
Write-Host "Compound GPID - Unlink" -ForegroundColor Cyan
Write-Host "======================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will remove only Compound GPID-managed install units from this project."
Write-Host "The global Compound GPID installation is NOT affected."
if (-not $Force) {
    $answer = Read-Host "Proceed? [y/N]"
    if ($answer -notmatch "^[Yy]$") {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
}

$removedAny = $false
$roots = New-Object System.Collections.ArrayList

# Legacy whole-root junctions from older linkers.
foreach ($rootName in @(".github", ".claude", ".agents", ".opencode", ".kilo")) {
    $rootPath = Join-Path $ProjectRoot $rootName
    $item = Get-Item -Path $rootPath -ErrorAction SilentlyContinue
    if (Test-CgOwnedJunction $item) {
        Remove-CgJunction -Path $rootPath
        Write-Host "  $rootName/ - legacy whole-root junction removed" -ForegroundColor DarkGray
        $removedAny = $true
    }
    [void]$roots.Add($rootName)
}

if (Test-Path $TargetMappingPath) {
    $mapping = Get-Content $TargetMappingPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($target in @($mapping.targets)) {
        foreach ($unit in @($target.installUnits)) {
            $targetRel = ConvertTo-CgSlashPath ([string]$unit.target)
            $rootName = $targetRel.Split("/")[0]
            if (-not $roots.Contains($rootName)) { [void]$roots.Add($rootName) }
            if ([string]$unit.type -eq "directory") {
                if (Remove-CgDirectoryUnit -TargetRel $targetRel) { $removedAny = $true }
            } else {
                if (Remove-CgManagedFile -TargetRel $targetRel -Manifest $manifest) { $removedAny = $true }
            }
        }
    }
}

if ($manifest.files.Count -gt 0) {
    Write-CgManagedFilesManifest -ManifestPath $ManifestPath -Manifest $manifest
} elseif (Test-Path $ManifestPath) {
    Remove-Item -Path $ManifestPath -Force
    Remove-CgEmptyRoot -RootName ".compound-gpid"
}

foreach ($root in @($roots)) { Remove-CgEmptyRoot -RootName $root }
Remove-CgGitignoreBlock

# Remove only checksum-owned manifest projection files; user-modified projected
# files and user roots are preserved.
$projectionOwnership = Join-Path $ProjectRoot ".compound-gpid/projection-ownership.json"
if (Test-Path -LiteralPath $projectionOwnership) {
    try {
        $projectionResult = Invoke-CgProjection -ProjectRoot $ProjectRoot -Mode unlink
        if ($projectionResult.Output -match "UNLINKED (\d+)") {
            if ([int]$Matches[1] -gt 0) { $removedAny = $true }
            Write-Host "  $($projectionResult.Output)" -ForegroundColor DarkGray
        }
    } catch {
        Write-Warning "Could not remove manifest projection files: $_"
    }
}

Write-Host ""
if ($removedAny) {
    Write-Host "Unlinked." -ForegroundColor Green
} else {
    Write-Host "Nothing to unlink - no Compound GPID-managed units found." -ForegroundColor Yellow
}
Write-Host "To re-link at any time, run: cg-link"
Write-Host ""
