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

. (Join-Path $PSScriptRoot "helpers.ps1")

function Resolve-CgLinkArguments {
    param([object[]]$Args)
    $result = @{ Force = $false; Platforms = $null }
    for ($i = 0; $i -lt $Args.Count; $i++) {
        $arg = [string]$Args[$i]
        if ($arg -in @("--yes", "-y", "-Force", "--force")) {
            $result.Force = $true
        } elseif ($arg -like "--platforms=*") {
            $result.Platforms = $arg.Substring("--platforms=".Length)
        } elseif ($arg -like "-Platforms=*") {
            $result.Platforms = $arg.Substring("-Platforms=".Length)
        } elseif ($arg -in @("--platforms", "-Platforms")) {
            if ($i + 1 -ge $Args.Count) { throw "Missing value after $arg" }
            $i++
            $result.Platforms = [string]$Args[$i]
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
    $supported = @("copilot", "claude-code", "codex", "opencode")
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

function Test-CgOwnedJunction {
    param($Item)
    if (-not $Item) { return $false }
    return ($Item.LinkType -eq "Junction" -and (($Item.Target -join '') -like "*compound-gpid*"))
}

function Ensure-CgRootDirectory {
    param([string]$RootName)
    $rootPath = Join-Path $ProjectRoot $RootName
    $existing = Get-Item -Path $rootPath -ErrorAction SilentlyContinue
    if ($existing -and (Test-CgOwnedJunction $existing)) {
        Write-Host "  $RootName/ - migrating legacy whole-root junction" -ForegroundColor Yellow
        Remove-Item -Path $rootPath -Force
        New-Item -ItemType Directory -Path $rootPath -Force | Out-Null
        return $true
    }
    if ($existing -and $existing.LinkType -eq "Junction" -and -not (Test-CgOwnedJunction $existing)) {
        Write-Warning "  $RootName/ is a non-Compound junction; skipping units under it."
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
        [bool]$Force
    )
    $source = Join-Path $CompoundGpidDir $SourceRel
    $target = Join-Path $ProjectRoot $TargetRel
    $existing = Get-Item -Path $target -ErrorAction SilentlyContinue

    if ($existing) {
        if ($existing.LinkType -eq "Junction") {
            if (Test-CgOwnedJunction $existing) {
                Write-Host "  $TargetRel - already linked" -ForegroundColor DarkGray
                return $true
            }
            Write-Warning "  $TargetRel is a junction pointing to: $($existing.Target)"
            if (-not $Force) {
                $answer = Read-Host "  Relink $TargetRel to Compound GPID instead? [y/N]"
                if ($answer -notmatch "^[Yy]$") {
                    Write-Host "  $TargetRel - skipped" -ForegroundColor Yellow
                    return $false
                }
            }
            Remove-Item -Path $target -Force
        } elseif ($existing.PSIsContainer) {
            Write-Warning "  $TargetRel is a real directory; skipping this unit."
            return $false
        } else {
            Write-Warning "  $TargetRel exists as a file; skipping this unit."
            return $false
        }
    }

    $parent = Split-Path $target -Parent
    if (-not (Test-Path $parent)) { New-Item -ItemType Directory -Path $parent -Force | Out-Null }
    New-Item -ItemType Junction -Path $target -Value $source | Out-Null
    Write-Host "  $TargetRel - linked" -ForegroundColor DarkGray
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
    $pattern = "(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.claude/|\.agents/|\.opencode/|\.compound-gpid/)[^\r\n]*\r?\n)*"

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
    Set-Content -Path $gitignorePath -Value ($cleaned + $separator + $block) -Encoding UTF8
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
            $targetPath = Join-Path $ProjectRoot $targetRel
            if ([string]$unit.type -eq "directory") {
                $item = Get-Item -Path $targetPath -ErrorAction SilentlyContinue
                if (Test-CgOwnedJunction $item) { [void]$entries.Add($targetRel) }
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

if (-not (Test-Path $CompoundGpidDir)) {
    Write-Error "Compound GPID installation directory not found at: $CompoundGpidDir$CG_INSTALL_GUIDANCE"
    exit 1
}
if (-not (Test-Path $TargetMappingPath)) {
    Write-Error "Target mapping not found at: $TargetMappingPath"
    exit 1
}

$argsParsed = Resolve-CgLinkArguments -Args $RawArgs
$Force = [bool]$argsParsed.Force
$selectedPlatforms = Resolve-CgPlatforms -PlatformsValue $argsParsed.Platforms

Write-Host ""
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
$installedEntries = New-Object System.Collections.ArrayList

foreach ($target in $targets) {
    Write-Host "Linking $($target.name)..." -ForegroundColor DarkGray
    foreach ($unit in @($target.installUnits)) {
        $targetRel = ConvertTo-CgSlashPath ([string]$unit.target)
        $rootName = Get-CgTargetRoot -RelativePath $targetRel
        if (-not (Ensure-CgRootDirectory -RootName $rootName)) { continue }

        $installed = $false
        if ([string]$unit.type -eq "directory") {
            $installed = Install-CgDirectoryUnit -SourceRel ([string]$unit.source) -TargetRel $targetRel -Force $Force
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

Update-CgGitignoreBlock -Entries (@($installedEntries) + (Get-CgInstalledGitignoreEntries -Mapping $mapping -Manifest $manifest))

Write-Host ""
Write-Host "Platform availability checks:" -ForegroundColor DarkGray
$checks = @{
    "copilot" = ".github/prompts/cg-setup.prompt.md"
    "claude-code" = ".claude/commands/cg-plan.md"
    "codex" = ".agents/commands/cg-plan.md"
    "opencode" = ".opencode/commands/cg-plan.md"
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
Write-Host "Use --platforms copilot to install only Copilot assets, or --platforms opencode for OpenCode-only assets."
Write-Host ""
Write-Host "IMPORTANT:" -ForegroundColor Yellow
Write-Host "  Managed linked directories and copied files should not be edited directly." -ForegroundColor Yellow
Write-Host "  If a config file was skipped, apply the printed manual snippet if needed." -ForegroundColor Yellow
Write-Host ""
Write-Host "Restart your AI coding tool so it reloads commands, skills, agents, and config." -ForegroundColor Yellow
Write-Host ""
