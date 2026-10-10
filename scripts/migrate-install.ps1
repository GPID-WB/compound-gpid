<#
.SYNOPSIS
Replace a Windows installation from a clean clone of the NEW release tag.
.PARAMETER InstallPath
Old standalone clone root. Required when discovery finds multiple installs.
.PARAMETER Rollback
Backup path printed by migration. Requires InstallPath; keeps current target aside.
.EXAMPLE
& 'C:\new-clone\scripts\migrate-install.ps1' -InstallPath 'C:\WBG\.compound-gpid'
.EXAMPLE
& 'C:\new-clone\scripts\migrate-install.ps1' -InstallPath 'C:\WBG\.compound-gpid' -Rollback 'C:\WBG\.compound-gpid.backup-v1.2.0.9023-20261010-120000-000'
#>
[CmdletBinding()]
param([string]$InstallPath, [string]$Rollback)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$official = 'https://github.com/GPID-WB/compound-gpid.git'
$source = [IO.Path]::GetFullPath((Split-Path $PSScriptRoot -Parent)).TrimEnd('\')
$shell = Join-Path $PSHOME 'powershell.exe'
$originalPath = $env:PATH
$originalEncoding = [Console]::OutputEncoding
$originalOutputEncoding = $OutputEncoding

function Get-NormalPath([string]$Path) {
    # Normalize without following links, e.g. a custom install path with spaces.
    return [IO.Path]::GetFullPath($Path).TrimEnd('\', '/')
}

function Assert-PlainPath([string]$Path) {
    # Reject reparse points in the path AND its parents before a rename/delete.
    for ($part = $Path; $part; $part = Split-Path $part -Parent) {
        if (Test-Path -LiteralPath $part) {
            if ((Get-Item -LiteralPath $part -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Link/junction paths are not supported: $part"
            }
        }
    }
}

function Invoke-MigrationGit([string]$Root, [string[]]$Arguments) {
    $output = & git -C $Root @Arguments
    if ($LASTEXITCODE -ne 0) { throw "Git failed in ${Root}: $($Arguments -join ' ')" }
    return $output
}

function Assert-Clone([string]$Path) {
    # A .git file denotes a worktree or separate gitdir, not a movable clone.
    Assert-PlainPath $Path
    $gitDir = Join-Path $Path '.git'
    Assert-PlainPath $gitDir
    if (-not (Test-Path -LiteralPath $gitDir -PathType Container)) {
        throw "Not a standalone Git clone root (.git files/worktrees refused): $Path"
    }
    if ((Get-NormalPath (Invoke-MigrationGit $Path @('rev-parse', '--show-toplevel'))) -ine $Path) {
        throw "Not a Git clone root: $Path"
    }
    if (Test-Path -LiteralPath (Join-Path $gitDir 'worktrees')) {
        throw "Clone has registered worktrees; manual action required: $Path"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $Path 'install.ps1') -PathType Leaf)) {
        throw "Compound GPID install.ps1 is missing: $Path"
    }
    if (-not (Test-Path -LiteralPath (Join-Path $Path 'bin\cg-update.cmd') -PathType Leaf)) {
        throw "Compound GPID wrapper is missing: $Path"
    }
}

function Assert-Separate([string]$Path) {
    if ($Path -ieq $source -or $Path.StartsWith("$source\", [StringComparison]::OrdinalIgnoreCase) -or
        $source.StartsWith("$Path\", [StringComparison]::OrdinalIgnoreCase)) {
        throw "NEW clone and target overlap: $Path"
    }
}

function Get-Backups([string]$Path) {
    $parent = Split-Path $Path -Parent
    if (Test-Path -LiteralPath $parent) {
        return @(Get-ChildItem -LiteralPath $parent -Force | Where-Object {
            $_.PSIsContainer -and $_.Name.StartsWith("$(Split-Path $Path -Leaf).backup-", [StringComparison]::OrdinalIgnoreCase)
        })
    }
}

try {
    if ($env:OS -ne 'Windows_NT') { throw 'This migration script requires Windows.' }
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw 'Install Git first.' }
    if ($Rollback -and -not $InstallPath) { throw '-Rollback requires -InstallPath with the exact original target.' }
    # PowerShell 5.1 decodes native Git output with the console output encoding.
    [Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
    $OutputEncoding = [Console]::OutputEncoding
    Assert-Clone $source
    $newHead = Invoke-MigrationGit $source @('rev-parse', 'HEAD')
    $newTag = Invoke-MigrationGit $source @('describe', '--tags', '--exact-match', 'HEAD')
    if ($newTag -notmatch '^v\d+\.\d+\.\d+(?:\.\d+)?$' -or
        @(Invoke-MigrationGit $source @('status', '--porcelain', '--untracked-files=all')).Count) {
        throw 'Run from a clean fresh clone at an exact release tag.'
    }
    $stamp = Get-Date -Format 'yyyyMMdd-HHmmss-fff'
    if ($Rollback) {
        $target = Get-NormalPath $InstallPath
        $backup = Get-NormalPath $Rollback
        if ($backup -notmatch ('^' + [regex]::Escape("$target.backup-") + '[A-Za-z0-9._-]+-\d{8}-\d{6}-\d{3}$')) {
            throw 'Use the exact target and sibling .backup- path printed by migration.'
        }
        Assert-Separate $target
        Assert-Separate $backup
        Assert-Clone $backup
        Assert-PlainPath $target
        $aside = "$target.rollback-$stamp"
        if (Test-Path -LiteralPath $aside) { throw "Already exists: $aside" }
        $moved = $false
        try {
            if (Test-Path -LiteralPath $target) {
                Move-Item -LiteralPath $target -Destination $aside
                $moved = $true
            }
            Move-Item -LiteralPath $backup -Destination $target
        } catch {
            if ($moved -and -not (Test-Path -LiteralPath $target)) {
                Move-Item -LiteralPath $aside -Destination $target
            }
            throw
        }
        Write-Host "Restored backup to: $target"
        if ($moved) { Write-Host "Current installation preserved at: $aside" }
        Write-Warning 'Review PATH/profile and project copies manually. Open a new terminal; no old code was run.'
        return
    }

    if ($InstallPath) {
        $target = Get-NormalPath $InstallPath
    } else {
        $candidates = @(Join-Path $env:USERPROFILE '.compound-gpid') + @('C:\WBG\.compound-gpid')
        $registration = Get-ItemProperty -LiteralPath 'HKCU:\Environment' -ErrorAction SilentlyContinue
        $userPath = if ($registration -and $registration.PSObject.Properties['Path']) { $registration.Path } else { '' }
        # Raw bin entries still identify custom targets after wrappers disappear.
        foreach ($entry in ("$env:PATH;$userPath" -split ';')) {
            if (-not $entry.Trim()) { continue }
            $bin = Get-NormalPath ([Environment]::ExpandEnvironmentVariables($entry.Trim().Trim('"')))
            if ((Split-Path $bin -Leaf) -ine 'bin') { continue }
            $root = Split-Path $bin -Parent
            if (@(Get-Backups $root).Count -or (Test-Path -LiteralPath (Join-Path $bin 'cg-update.cmd')) -or
                (Test-Path -LiteralPath (Join-Path $bin 'cg-link.cmd'))) { $candidates += $root }
        }
        foreach ($command in @(Get-Command cg-update, cg-link -All -CommandType Application -ErrorAction SilentlyContinue)) {
            $bin = Split-Path $command.Path -Parent
            if ((Split-Path $bin -Leaf) -ine 'bin') { throw "Unknown PATH wrapper; use -InstallPath: $($command.Path)" }
            $candidates += Split-Path $bin -Parent
        }
        $found = @($candidates | ForEach-Object { Get-NormalPath $_ } | Sort-Object -Unique | Where-Object {
            (Test-Path -LiteralPath $_) -or @(Get-Backups $_).Count
        })
        if ($found.Count -eq 0) { throw 'No installation found. Run the normal NEW install.ps1 instead.' }
        if ($found.Count -gt 1) { throw "Multiple installations found. Use -InstallPath: $($found -join '; ')" }
        $target = $found[0]
    }
    Assert-Separate $target
    Assert-PlainPath $target
    $existing = @(Get-Backups $target)
    if ($existing.Count) {
        Write-Host 'Stop lifecycle activity. Inspect the target and backups; choose one backup to restore.'
        foreach ($item in $existing) {
            Write-Host "  & '$($PSCommandPath.Replace("'", "''"))' -InstallPath '$($target.Replace("'", "''"))' -Rollback '$($item.FullName.Replace("'", "''"))'"
        }
        Write-Host 'To resume: roll back first, then run this exact command:'
        Write-Host "  & '$($PSCommandPath.Replace("'", "''"))' -InstallPath '$($target.Replace("'", "''"))'"
        throw "Existing backup found: $($existing.FullName -join '; '). Nothing was changed."
    }
    Assert-Clone $target
    $oldHead = Invoke-MigrationGit $target @('rev-parse', 'HEAD')
    $oldVersion = Invoke-MigrationGit $target @('describe', '--tags', '--always', '--dirty')
    $pinPath = Join-Path $target '.cg-version'
    $oldPin = if (Test-Path -LiteralPath $pinPath) { Get-Content -LiteralPath $pinPath -Raw } else { '(absent)' }
    Write-Host "Old HEAD: $oldHead"
    Write-Host "Old describe: $oldVersion"
    Write-Host "Old .cg-version: $oldPin"
    $safeVersion = ($oldVersion -replace '[^A-Za-z0-9._-]', '_' -replace '(?i)backup', 'old')
    $backup = "$target.backup-$safeVersion-$stamp"
    if (Test-Path -LiteralPath $backup) { throw "Already exists: $backup" }
    Write-Host "Backup: $backup"
    Write-Warning 'Stop other install/update/link activity. Installer PATH/profile writes are not snapshotted.'
    Move-Item -LiteralPath $target -Destination $backup
    $created = $false
    try {
        New-Item -ItemType Directory -Path $target | Out-Null
        $created = $true
        # --no-local avoids hardlinks/alternates and leaves the running clone untouched.
        Invoke-MigrationGit $source @('clone', '--no-local', '--branch', $newTag, '--', $source, $target) | Out-Null
        Invoke-MigrationGit $target @('remote', 'set-url', 'origin', $official) | Out-Null
        Invoke-MigrationGit $target @('fetch', '--tags', 'origin', "refs/tags/$newTag") | Out-Null
        if ((Invoke-MigrationGit $target @('rev-parse', 'FETCH_HEAD^{commit}')) -ne $newHead -or
            (Invoke-MigrationGit $target @('rev-parse', 'HEAD')) -ne $newHead) {
            throw 'Official tag does not match the running NEW clone.'
        }
        Set-Content -LiteralPath (Join-Path $target '.cg-version') -Value $newTag -NoNewline -Encoding ASCII
        & $shell -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $target 'install.ps1')
        if ($LASTEXITCODE -ne 0) { throw "NEW installer failed (exit $LASTEXITCODE)." }
        if ((Invoke-MigrationGit $target @('rev-parse', 'HEAD')) -ne $newHead -or
            (Invoke-MigrationGit $target @('describe', '--tags', '--exact-match', 'HEAD')) -ne $newTag -or
            (Get-Content -LiteralPath (Join-Path $target '.cg-version') -Raw) -ne $newTag -or
            @(Invoke-MigrationGit $target @('status', '--porcelain', '--untracked-files=all')).Count) {
            throw 'NEW checkout/tag/pin/clean-status verification failed.'
        }
        foreach ($name in @('cg-link.cmd', 'cg-unlink.cmd', 'cg-update.cmd')) {
            if (-not (Test-Path -LiteralPath (Join-Path $target "bin\$name") -PathType Leaf)) {
                throw "Missing NEW wrapper: $name"
            }
        }
        $user = Get-ItemProperty -LiteralPath 'HKCU:\Environment' -ErrorAction Stop
        $machine = Get-ItemProperty -LiteralPath 'HKLM:\SYSTEM\CurrentControlSet\Control\Session Manager\Environment' -ErrorAction Stop
        $env:PATH = [Environment]::ExpandEnvironmentVariables("$($machine.Path);$($user.Path)")
        $resolved = & $shell -NoProfile -NonInteractive -Command '[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false); (Get-Command cg-update -CommandType Application -ErrorAction Stop).Path'
        if ($LASTEXITCODE -ne 0 -or (Get-NormalPath $resolved) -ine (Join-Path $target 'bin\cg-update.cmd')) {
            throw 'Fresh-process cg-update does not resolve to the target. Review PATH shadowing.'
        }
    } catch {
        $failure = $_
        try {
            if ($created -and (Test-Path -LiteralPath $target)) {
                Assert-PlainPath $target
                Remove-Item -LiteralPath $target -Recurse -Force
            }
            if (Test-Path -LiteralPath $target) { throw 'Target is occupied; preserve both folders and inspect manually.' }
            Move-Item -LiteralPath $backup -Destination $target
        } catch {
            Write-Host "  & '$($PSCommandPath.Replace("'", "''"))' -InstallPath '$($target.Replace("'", "''"))' -Rollback '$($backup.Replace("'", "''"))'"
            throw "Migration failed: $failure. Automatic restore failed: $_. Keep backup '$backup'; roll back after manual inspection."
        }
        throw "Migration failed: $failure. Old folder restored to '$target'. Review any installer PATH/profile writes manually."
    }
    Write-Host "Migrated: $oldVersion -> $newTag (pinned)"
    Write-Host "Backup preserved: $backup"
    Write-Host 'Open a new terminal. Run cg-link once per project. Unresolved project conflicts: manual action required; preserve files.'
    Write-Host 'Returning to latest is a separate user action. No project reconciliation was run.'
    Write-Host 'Rollback (stop other lifecycle activity first):'
    Write-Host "  & '$($PSCommandPath.Replace("'", "''"))' -InstallPath '$($target.Replace("'", "''"))' -Rollback '$($backup.Replace("'", "''"))'"
} catch {
    # Write before finally restores encoding; PowerShell error formatting wraps paths.
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
} finally {
    $env:PATH = $originalPath
    [Console]::OutputEncoding = $originalEncoding
    $OutputEncoding = $originalOutputEncoding
}
