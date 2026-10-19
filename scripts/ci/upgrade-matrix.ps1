<#
.SYNOPSIS
Test one old-tag upgrade in a disposable profile (hosted runner only).
.EXAMPLE
powershell -NoProfile -File scripts/ci/upgrade-matrix.ps1 -OldTag v1.2.0.9023 -Root E:\t\upgrade-9023 -LocalCheck
.PARAMETER LocalCheck
Skip BOTH installers and migration (they write real HKCU); test link reconciliation only.
#>
param([Parameter(Mandatory)][string]$OldTag, [Parameter(Mandatory)][string]$Root,
    [switch]$LocalCheck)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$source = (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
if (-not $LocalCheck -and $env:GITHUB_ACTIONS -ne 'true') { throw 'Installers require a disposable hosted account; use -LocalCheck.' }
if (Test-Path -LiteralPath $Root) { throw "Fixture already exists: $Root" }
if (-not (Test-Path -LiteralPath (Split-Path $Root -Parent))) { throw 'Fixture parent is missing.' }
foreach ($command in @('git', 'powershell.exe', 'python')) {
    if (-not (Get-Command $command -ErrorAction SilentlyContinue)) { throw "Missing command: $command" }
}
New-Item -ItemType Directory -Path $Root | Out-Null
$Root = (Resolve-Path $Root).Path
$env:HOME = Join-Path $Root 'home'
$env:USERPROFILE = $env:HOME
$env:APPDATA = Join-Path $env:HOME 'AppData\Roaming'
$env:LOCALAPPDATA = Join-Path $env:HOME 'AppData\Local'
$env:XDG_CONFIG_HOME = Join-Path $env:HOME '.config'
$env:TEMP = Join-Path $env:HOME 'temp'
$env:TMP = $env:TEMP
$env:GIT_CONFIG_GLOBAL = Join-Path $env:HOME 'gitconfig'
$env:GIT_CONFIG_NOSYSTEM = '1'
$env:GIT_TERMINAL_PROMPT = '0'
$env:GIT_ALLOW_PROTOCOL = 'file'
$env:PYTHONDONTWRITEBYTECODE = '1'
$env:CG_SKIP_UPDATE = '1'
Set-Variable -Name HOME -Scope Global -Value $env:HOME -Force
$global:PROFILE = Join-Path $env:HOME 'profile.ps1'
$install = Join-Path $env:HOME '.compound-gpid'
$candidate = Join-Path $env:HOME 'candidate'
$stage = 'fixture setup'
$result = 'fail'
$reason = ''

function Invoke-Git([string[]]$Arguments) {
    $output = & git @Arguments
    if ($LASTEXITCODE -ne 0) { throw "git failed: $($Arguments -join ' ')" }
    return $output
}
function Run([string]$Name, [string]$Executable, [string[]]$Arguments, [int[]]$Allowed = @(0)) {
    $log = Join-Path $Root "$Name.log"
    # PS 5.1 wraps redirected native stderr in ErrorRecords; use the exit code.
    $ErrorActionPreference = 'Continue'
    & $Executable @Arguments *> $log
    $code = $LASTEXITCODE
    $ErrorActionPreference = 'Stop'
    if ($code -notin $Allowed) {
        Get-Content -LiteralPath $log
        throw "$Name exited $code; see $log"
    }
    return $code
}
function Snapshot([string]$Path) {
    # Do not traverse junctions or .git; include directory/link identity and bytes.
    foreach ($item in Get-ChildItem -LiteralPath $Path -Force | Sort-Object Name) {
        if ($item.Name -eq '.git') { continue }
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
            "$($item.FullName)|link|$($item.Target)"
        } elseif ($item.PSIsContainer) {
            "$($item.FullName)|directory"
            Snapshot $item.FullName
        } else { "$($item.FullName)|$((Get-FileHash -LiteralPath $item.FullName).Hash)" }
    }
}
function Assert-Same([string]$Left, [string]$Right) {
    if ((Get-FileHash -LiteralPath $Left).Hash -ne (Get-FileHash -LiteralPath $Right).Hash) {
        throw "File bytes differ: $Left != $Right"
    }
}
try {
    foreach ($dir in @($env:APPDATA, $env:LOCALAPPDATA, $env:XDG_CONFIG_HOME, $env:TEMP, "$Root\outside")) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
    Set-Content -LiteralPath "$Root\outside\sentinel.txt" -Value 'outside fixture' -Encoding ASCII
    $outsideBefore = @(Snapshot "$Root\outside")
    $sourceBefore = @(Snapshot $source)
    Invoke-Git -Arguments @('config', '--global', 'user.name', 'Upgrade fixture') | Out-Null
    Invoke-Git -Arguments @('config', '--global', 'user.email', 'upgrade@example.invalid') | Out-Null
    Invoke-Git -Arguments @('config', '--global', 'commit.gpgsign', 'false') | Out-Null
    Invoke-Git -Arguments @('config', '--global', 'maintenance.auto', 'false') | Out-Null
    Invoke-Git -Arguments @('clone', '--no-local', '--branch', $OldTag, '-c', 'core.autocrlf=true', $source, $install) | Out-Null
    $oldHead = Invoke-Git -Arguments @('-C', $install, 'rev-parse', 'HEAD')
    Set-Content -LiteralPath "$install\.cg-version" -Value $OldTag -NoNewline -Encoding ASCII
    $stage = 'old installer'
    if ($LocalCheck) {
        Write-Host 'LOCAL PARTIAL: both installers and migration skipped; they write real HKCU. CI owns migration qualification.'
    } else {
        $null = Run 'old-installer' 'powershell.exe' @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass', '-File', "$install\install.ps1")
    }
    $fixtures = @(@{ Name = 'project'; Platforms = 'copilot,claude-code'; Edited = '.claude/CLAUDE.md';
        Unedited = '.github/prompts/cg-review.prompt.md'; User = '.claude/user-upgrade-sentinel.md' })
    if ($OldTag -ne 'v1.0.4') {
        $fixtures += @{ Name = 'kilo-project'; Platforms = 'kilo'; Edited = '.kilo/commands/cg-plan.md';
            Unedited = '.kilo/commands/cg-review.md'; User = '.kilo/commands/user-upgrade-sentinel.md' }
    }
    foreach ($fixture in $fixtures) {
        $project = Join-Path $env:HOME $fixture.Name
        Invoke-Git -Arguments @('init', $project) | Out-Null
        Set-Content -LiteralPath "$project\fixture.txt" -Value 'small Git project' -Encoding ASCII
        Invoke-Git -Arguments @('-C', $project, 'add', 'fixture.txt') | Out-Null
        Invoke-Git -Arguments @('-C', $project, 'commit', '-m', 'fixture') | Out-Null
        Push-Location $project
        try {
            $stage = "old link ($($fixture.Name))"
            $null = Run "old-link-$($fixture.Name)" 'powershell.exe' @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                '-File', "$install\scripts\link.ps1", '--platforms', $fixture.Platforms, '--yes')
            # Root Claude file is copied even in v1.0.4, which has no copy-directory adapter.
            $edited = Join-Path $project $fixture.Edited
            if ((Get-Item -LiteralPath (Split-Path $edited -Parent)).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Refusing to edit linked fixture: $edited"
            }
            Add-Content -LiteralPath $edited -Value '<!-- upgrade user edit -->' -Encoding UTF8
            Set-Content -LiteralPath (Join-Path $project $fixture.User) -Value 'user-added bytes' -Encoding ASCII
            Copy-Item -LiteralPath (Join-Path $project $fixture.User) -Destination "$Root\$($fixture.Name)-user.before"
            Copy-Item -LiteralPath $edited -Destination "$Root\$($fixture.Name)-edited.before"
            $copilot = Join-Path $project '.github/copilot-instructions.md'
            if (Test-Path -LiteralPath $copilot) {
                Add-Content -LiteralPath $copilot -Value '<!-- upgrade Copilot user edit -->' -Encoding UTF8
                Copy-Item -LiteralPath $copilot -Destination "$Root\copilot.before"
            }
        } finally { Pop-Location }
    }
    $oldBefore = @(Snapshot $install)
    $stage = 'candidate clone and local-only tag'
    $head = Invoke-Git -Arguments @('-C', $source, 'rev-parse', 'HEAD')
    # The local fixture tag must not collide with an inherited published tag.
    Invoke-Git -Arguments @('clone', '--no-local', '--no-tags', '-c', 'core.autocrlf=true', $source, $candidate) | Out-Null
    # Preserve historical release proofs, excluding only the local fixture tag.
    Invoke-Git -Arguments @('-C', $candidate, 'fetch', 'origin', 'refs/tags/*:refs/tags/*', '^refs/tags/v1.2.0.9024') | Out-Null
    Invoke-Git -Arguments @('-C', $candidate, 'checkout', '--detach', $head) | Out-Null
    Invoke-Git -Arguments @('-C', $candidate, 'tag', '-a', 'v1.2.0.9024', '-m', 'LOCAL ONLY upgrade fixture', $head) | Out-Null
    # The unpublished tag is verified through this local fixture remote, never GitHub.
    $candidateUrl = ([Uri]($candidate + '\')).AbsoluteUri.TrimEnd('/')
    Invoke-Git -Arguments @('config', '--global', "url.$candidateUrl.insteadOf", 'https://github.com/GPID-WB/compound-gpid.git') | Out-Null
    $stage = 'candidate migration'
    if ($LocalCheck) {
        Move-Item -LiteralPath $install -Destination "$install.backup-local-check"
        Invoke-Git -Arguments @('clone', '--no-local', '--branch', 'v1.2.0.9024', '-c', 'core.autocrlf=true', $candidate, $install) | Out-Null
        Set-Content -LiteralPath "$install\.cg-version" -Value 'v1.2.0.9024' -NoNewline -Encoding ASCII
    } else {
        $null = Run 'migration' 'powershell.exe' @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
            '-File', "$candidate\scripts\migrate-install.ps1", '-InstallPath', $install)
        $migration = Get-Content -LiteralPath "$Root\migration.log" -Raw
        $registered = (Get-ItemProperty -LiteralPath 'HKCU:\Environment').Path
        if (($registered -split ';') -notcontains "$install\bin" -and $migration -notmatch 'NEW installation kept') {
            throw 'Neither wrapper PATH registration nor PATH warning was observed.'
        }
    }
    if ((Invoke-Git -Arguments @('-C', $install, 'rev-parse', 'HEAD')) -ne $head) { throw 'Candidate HEAD mismatch.' }
    if ((Get-Content -LiteralPath "$install\.cg-version" -Raw) -ne 'v1.2.0.9024') { throw 'Pin mismatch.' }
    $backups = @(Get-ChildItem -LiteralPath $env:HOME -Directory -Force | Where-Object Name -like '.compound-gpid.backup-*')
    if ($backups.Count -ne 1 -or (Invoke-Git -Arguments @('-C', $backups[0].FullName, 'rev-parse', 'HEAD')) -ne $oldHead) { throw 'Old backup missing/wrong.' }
    $backupBytes = @(Snapshot $backups[0].FullName) | ForEach-Object { $_.Replace($backups[0].FullName, $install) }
    if (Compare-Object $oldBefore $backupBytes) { throw 'Old installation bytes were not preserved in backup.' }
    foreach ($wrapper in @('cg-link.cmd', 'cg-update.cmd', 'cg-unlink.cmd')) {
        Assert-Same "$install\bin\$wrapper" "$candidate\bin\$wrapper"
    }
    $protectedBefore = @(Snapshot $candidate) + @(Snapshot $backups[0].FullName) + @(Snapshot $install)
    foreach ($fixture in $fixtures) {
        $project = Join-Path $env:HOME $fixture.Name
        Push-Location $project
        try {
            $stage = "candidate check ($($fixture.Name))"
            $before = @(Snapshot $project)
            $null = Run "check-$($fixture.Name)" 'powershell.exe' @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                '-File', "$install\scripts\link.ps1", '--check', '--platforms', $fixture.Platforms) @(1)
            $checkOutput = (Get-Content -LiteralPath "$Root\check-$($fixture.Name).log" -Raw).Replace('\', '/')
            if (-not $checkOutput.Contains('Manual action required:') -or -not $checkOutput.Contains($fixture.Edited)) {
                throw 'Read-only check did not report the edited file.'
            }
            if (Compare-Object $before @(Snapshot $project)) { throw 'Read-only check changed project.' }
            $stage = "candidate link ($($fixture.Name))"
            $null = Run "link-$($fixture.Name)" 'powershell.exe' @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                '-File', "$install\scripts\link.ps1", '--platforms', $fixture.Platforms, '--yes')
            Assert-Same (Join-Path $project $fixture.Edited) "$Root\$($fixture.Name)-edited.before"
            Assert-Same (Join-Path $project $fixture.Unedited) (Join-Path $candidate $fixture.Unedited)
            $output = (Get-Content -LiteralPath "$Root\link-$($fixture.Name).log" -Raw).Replace('\', '/')
            if ($output -notmatch 'Manual action required: [1-9]' -or -not $output.Contains($fixture.Edited)) { throw 'Missing edited-file manual action.' }
            Assert-Same (Join-Path $project $fixture.User) "$Root\$($fixture.Name)-user.before"
            if ($fixture.Name -eq 'kilo-project' -and $output -notmatch 'user-upgrade-sentinel.md: user file kept') { throw 'Missing informational user-file report.' }
            if ($fixture.Name -eq 'project') {
                Assert-Same "$project\.github\copilot-instructions.md.pre-9024.bak" "$Root\copilot.before"
                if ((Get-Content -LiteralPath "$project\.github\copilot-instructions.md" -Raw) -notmatch '<!-- compound-gpid:managed -->') { throw 'Generated Copilot instructions are missing.' }
                if ((Get-Content -LiteralPath "$project\.github\copilot-instructions.md" -Raw) -match 'upgrade Copilot user edit') { throw 'Copilot transition did not generate new instructions.' }
            }
            $stage = "candidate repeat ($($fixture.Name))"
            $before = @(Snapshot $project)
            $null = Run "repeat-$($fixture.Name)" 'powershell.exe' @('-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
                '-File', "$install\scripts\link.ps1", '--platforms', $fixture.Platforms, '--yes')
            if (Compare-Object $before @(Snapshot $project)) { throw 'Second link changed project.' }
        } finally { Pop-Location }
    }
    $stage = 'outside-write checks'
    if (Compare-Object $protectedBefore (@(Snapshot $candidate) + @(Snapshot $backups[0].FullName) + @(Snapshot $install))) { throw 'Link changed an installation/backup.' }
    if (Compare-Object $outsideBefore @(Snapshot "$Root\outside")) { throw 'Outside sentinel changed.' }
    if (Compare-Object $sourceBefore @(Snapshot $source)) { throw 'Source checkout changed.' }
    $result = 'pass'
    if ($LocalCheck) { $reason = 'LOCAL PARTIAL: link only; installers and migration skipped to avoid real HKCU/PATH writes.' }
} catch {
    $reason = $_.Exception.Message
    # Old exits remain failures until their exact, candidate-independent cause is reviewed.
    Write-Host "${stage}: $reason"
} finally {
    $note = "| windows-latest | $OldTag | $result | $stage | $reason |"
    Set-Content -LiteralPath "$Root\result.md" -Value $note -Encoding UTF8
    if ($env:GITHUB_STEP_SUMMARY) { Add-Content -LiteralPath $env:GITHUB_STEP_SUMMARY -Value $note }
    Write-Host $note
}
if ($result -eq 'fail') { exit 1 }
