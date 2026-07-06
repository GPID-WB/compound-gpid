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

. (Join-Path $PSScriptRoot "helpers.ps1")

function Resolve-CgUnlinkArguments {
    param([object[]]$Args)
    $force = $false
    foreach ($argObj in $Args) {
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

function Remove-CgDirectoryUnit {
    param([string]$TargetRel)
    $target = Join-Path $ProjectRoot $TargetRel
    $item = Get-Item -Path $target -ErrorAction SilentlyContinue
    if (-not $item) { return $false }
    if (Test-CgOwnedJunction $item) {
        Remove-Item -Path $target -Force
        Write-Host "  $TargetRel - junction removed" -ForegroundColor DarkGray
        return $true
    }
    if ($item.LinkType -eq "Junction") {
        Write-Host "  $TargetRel - non-Compound junction, skipping" -ForegroundColor Yellow
    } else {
        Write-Host "  $TargetRel - user-owned path, skipping" -ForegroundColor Yellow
    }
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
    $pattern = "(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.claude/|\.agents/|\.opencode/|\.compound-gpid/)[^\r\n]*\r?\n)*"
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

$Force = Resolve-CgUnlinkArguments -Args $RawArgs
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
foreach ($rootName in @(".github", ".claude", ".agents", ".opencode")) {
    $rootPath = Join-Path $ProjectRoot $rootName
    $item = Get-Item -Path $rootPath -ErrorAction SilentlyContinue
    if (Test-CgOwnedJunction $item) {
        Remove-Item -Path $rootPath -Force
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

Write-Host ""
if ($removedAny) {
    Write-Host "Unlinked." -ForegroundColor Green
} else {
    Write-Host "Nothing to unlink - no Compound GPID-managed units found." -ForegroundColor Yellow
}
Write-Host "To re-link at any time, run: cg-link"
Write-Host ""
