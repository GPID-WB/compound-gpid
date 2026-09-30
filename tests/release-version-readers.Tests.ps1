# Read the actual side-effect-free updater reader region, not a copied parser.
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$source = Get-Content (Join-Path $root 'scripts/update.ps1') -Raw
$region = [regex]::Match($source, '(?s)# BEGIN RELEASE READERS(.*?)# END RELEASE READERS')
if ($region.Success) { . ([scriptblock]::Create($region.Groups[1].Value)) }
$corpus = Get-Content (Join-Path $root 'packages/cg-release/tests/fixtures/versions.json') -Raw | ConvertFrom-Json

Describe 'Actual updater SemVer readers' {
    It 'exposes a side-effect-free reader region' { $region.Success | Should -Be $true }
    It 'accepts all strict corpus versions and legacy pins' {
        foreach ($version in $corpus.valid) { ('v' + $version) -cmatch $VersionAcceptPattern | Should -Be $true }
        'v1.5.0.9000' -cmatch $VersionAcceptPattern | Should -Be $true
        'latest' -cmatch $VersionAcceptPattern | Should -Be $true
    }
    It 'rejects every invalid corpus version' {
        foreach ($version in $corpus.invalid) { ('v' + $version) -cmatch $VersionAcceptPattern | Should -Be $false }
    }
    It 'sorts numeric identifiers and stable promotion by SemVer' {
        $tags = @(Sort-CgReleaseTags @('v1.5.0-rc.2', 'v1.5.0-rc.10', 'v1.5.0'))
        ($tags -join ',') | Should -Be 'v1.5.0,v1.5.0-rc.10,v1.5.0-rc.2'
    }
    It 'ignores build metadata for precedence' {
        foreach ($pair in $corpus.equivalent) { Compare-CgReleaseTags ('v' + $pair[0]) ('v' + $pair[1]) | Should -Be 0 }
    }
    It 'keeps four-part legacy identities in their separate lane' {
        Compare-CgReleaseTags 'v1.5.0.9001' 'v1.5.0.9000' | Should -Be 1
        Compare-CgReleaseTags 'v1.5.0' 'v1.5.0.9001' | Should -Be 1
    }
    It 'handles arbitrarily large numeric identifiers without integer overflow' {
        Compare-CgReleaseTags 'v1.0.0-rc.999999999999999999999' 'v1.0.0-rc.999999999999999999998' | Should -Be 1
    }
}

Describe 'Release controller launcher' {
    It 'uses guarded Python candidates and the argument-preserving entry point' {
        $launcher = Get-Content (Join-Path $root 'bin/cg-release.cmd') -Raw
        $launcher | Should -Match 'for /f'
        foreach ($candidate in @('python3', 'python', 'py')) {
            $launcher | Should -Match ("where " + $candidate + '\s+>nul')
        }
        $launcher | Should -Match 'cg_release_cli\.py.*%\*'
        $launcher | Should -Match 'exit /b %ERRORLEVEL%'
    }
    It 'keeps the writer disabled with unresolved bootstrap authority' {
        $policy = Get-Content (Join-Path $root '.release-controller.json') -Raw | ConvertFrom-Json
        $policy.enabled | Should -Be $false
        $policy.repository_id | Should -BeNullOrEmpty
        $policy.profile.bridge | Should -BeNullOrEmpty
    }
}
