# tests/create-release.Tests.ps1
# Pester tests for create-release.ps1
#
# Run with: Invoke-Pester tests/create-release.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)
#
# Scope: parameter binding, input validation, and output format logic.
# Real HTTP calls to GitHub are NOT made -- tests cover local logic only.

# ---------------------------------------------------------------------------
# Tag format validation
# ---------------------------------------------------------------------------

Describe "create-release.ps1 - tag format validation" {
    $tagPattern = '^v\d+\.\d+\.\d+(\.\d+)?$'

    Context "valid tag formats" {
        It "accepts v0.0.0 (leading zeros)" {
            ("v0.0.0" -match $tagPattern) | Should -Be $true
        }

        It "accepts v1.2.3 (standard semver)" {
            ("v1.2.3" -match $tagPattern) | Should -Be $true
        }

        It "accepts v10.20.300 (multi-digit components)" {
            ("v10.20.300" -match $tagPattern) | Should -Be $true
        }

        It "accepts v1.2.0.9008 (four-component prerelease)" {
            ("v1.2.0.9008" -match $tagPattern) | Should -Be $true
        }
    }

    Context "invalid tag formats" {
        It "rejects uppercase V prefix" {
            ("V1.2.3" -cmatch $tagPattern) | Should -Be $false
        }
        It "rejects 1.2.3 (missing v prefix)" {
            ("1.2.3" -match $tagPattern) | Should -Be $false
        }

        It "rejects v1.2 (only two components)" {
            ("v1.2" -match $tagPattern) | Should -Be $false
        }

        It "rejects vx.y.z (non-numeric components)" {
            ("vx.y.z" -match $tagPattern) | Should -Be $false
        }

        It "rejects v1.2.3.4.5 (five components)" {
            ("v1.2.3.4.5" -match $tagPattern) | Should -Be $false
        }

        It "rejects empty string" {
            ("" -match $tagPattern) | Should -Be $false
        }

        It "rejects v1.2.3-beta (pre-release suffix)" {
            ("v1.2.3-beta" -match $tagPattern) | Should -Be $false
        }
    }
}

# ---------------------------------------------------------------------------
# NotesFile existence check
# ---------------------------------------------------------------------------

Describe "create-release.ps1 - NotesFile validation" {
    Context "when the file exists" {
        It "reads the file content without error" {
            $notesPath = Join-Path $TestDrive "notes.md"
            Set-Content -Path $notesPath -Value "## What's new`nSome content."

            $exists = Test-Path $notesPath
            $exists | Should -Be $true

            $content = Get-Content -Path $notesPath -Raw
            $content -match "What's new" | Should -Be $true
        }
    }

    Context "when the file does not exist" {
        It "Test-Path returns false for a missing file" {
            $missing = Join-Path $TestDrive "does-not-exist.md"
            Test-Path $missing | Should -Be $false
        }

        It "guard condition correctly detects missing file" {
            $missing = Join-Path $TestDrive "also-missing.md"
            # Simulates the guard in create-release.ps1: -not (Test-Path $NotesFile)
            $shouldAbort = -not (Test-Path $missing)
            $shouldAbort | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Switch parameter semantics
# ---------------------------------------------------------------------------

Describe "create-release.ps1 - switch parameter semantics" {
    # PowerShell switch parameters: when specified, IsPresent = $true; when omitted,
    # PowerShell binds them as [switch]$false (not null). Always test via .IsPresent,
    # never via magic strings -- string-simulated tests pass for the wrong reasons.

    Context "-Draft switch" {
        It "Draft.IsPresent is true when switch is specified" {
            # PowerShell binds -Draft as [switch]$true
            $Draft = [switch]$true
            $Draft.IsPresent | Should -Be $true
        }

        It "Draft.IsPresent is false when switch is omitted" {
            # PowerShell binds unspecified switch as [switch]$false
            $Draft = [switch]$false
            $Draft.IsPresent | Should -Be $false
        }

        It "draft field in payload reflects switch value when true" {
            $Draft = [switch]$true
            $payload = @{ draft = $Draft.IsPresent }
            $payload.draft | Should -Be $true
        }

        It "draft field in payload reflects switch value when false" {
            $Draft = [switch]$false
            $payload = @{ draft = $Draft.IsPresent }
            $payload.draft | Should -Be $false
        }
    }

    Context "-Prerelease switch" {
        It "Prerelease.IsPresent is true when switch is specified" {
            $Prerelease = [switch]$true
            $Prerelease.IsPresent | Should -Be $true
        }

        It "Prerelease.IsPresent is false when switch is omitted" {
            $Prerelease = [switch]$false
            $Prerelease.IsPresent | Should -Be $false
        }

        It "derives prerelease true from a four-component tag" {
            $Tag = "v1.2.0.9008"
            $payload = @{ prerelease = ($Tag -match '^v\d+\.\d+\.\d+\.\d+$') }
            $payload.prerelease | Should -Be $true
        }

        It "derives prerelease false from a three-component tag" {
            $Tag = "v1.2.0"
            $payload = @{ prerelease = ($Tag -match '^v\d+\.\d+\.\d+\.\d+$') }
            $payload.prerelease | Should -Be $false
        }
    }

    Context "-Draft and -Prerelease both specified" {
        It "both flags are independently true" {
            $Draft      = [switch]$true
            $Prerelease = [switch]$true
            $Draft.IsPresent      | Should -Be $true
            $Prerelease.IsPresent | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Payload construction
# ---------------------------------------------------------------------------

Describe "create-release.ps1 - payload construction" {
    Context "all required fields" {
        It "payload contains tag_name, target_commitish, name, body, draft, prerelease" {
            $Tag        = "v0.0.6"
            $HeadCommit = "abc123"
            $Name       = "v0.0.6 - Release automation"
            $Notes      = "## What's new`nRelease automation."
            $Draft      = [switch]$false
            $Prerelease = [switch]$false

            $payload = @{
                tag_name         = $Tag
                target_commitish = $HeadCommit
                name             = $Name
                body             = $Notes
                draft            = $Draft.IsPresent
                prerelease       = $Prerelease.IsPresent
            }

            $payload.tag_name   | Should -Be "v0.0.6"
            $payload.target_commitish | Should -Be "abc123"
            $payload.name       | Should -Be "v0.0.6 - Release automation"
            $payload.body       | Should -Be $Notes
            $payload.draft      | Should -Be $false
            $payload.prerelease | Should -Be $false
        }

        It "notes file content flows into payload body" {
            $notesPath = Join-Path $TestDrive "payload-notes.md"
            $expected  = "## What's new`nSome feature was added."
            Set-Content -Path $notesPath -Value $expected -NoNewline

            $notes   = Get-Content -Path $notesPath -Raw
            $payload = @{ body = $notes }

            $payload.body | Should -Be $expected
        }
    }

    Context "JSON serialization" {
        It "ConvertTo-Json produces valid JSON from payload hashtable" {
            $payload = @{
                tag_name   = "v0.0.6"
                name       = "v0.0.6 - Test"
                body       = "## Notes"
                draft      = $false
                prerelease = $false
            }

            $json = ConvertTo-Json -InputObject $payload -Depth 5
            $json -match '"tag_name"' | Should -Be $true
            $json -match '"v0.0.6"'  | Should -Be $true
            $json -match '"draft"'   | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Output format (release-result.txt)
# ---------------------------------------------------------------------------

Describe "create-release.ps1 - release-result.txt output format" {
    Context "EXISTS path (idempotency)" {
        It "output matches EXISTS|<id>|<url> format" {
            $id  = 123456789
            $url = "https://github.com/GPID-WB/compound-gpid/releases/tag/v0.0.6"

            $result = "EXISTS|$id|$url"
            $result -match '^EXISTS\|\d+\|https://' | Should -Be $true
        }

        It "writes EXISTS result to file" {
            $outPath = Join-Path $TestDrive "release-result.txt"
            $id      = 111
            $url     = "https://github.com/GPID-WB/compound-gpid/releases/tag/v0.0.6"

            "EXISTS|$id|$url" | Set-Content $outPath

            $content = Get-Content $outPath -Raw
            $content -match '^EXISTS\|' | Should -Be $true
        }
    }

    Context "CREATED path" {
        It "output matches CREATED|<id>|<url> format" {
            $id  = 987654321
            $url = "https://github.com/GPID-WB/compound-gpid/releases/tag/v0.0.6"

            $result = "CREATED|$id|$url"
            $result -match '^CREATED\|\d+\|https://' | Should -Be $true
        }

        It "writes CREATED result to file" {
            $outPath = Join-Path $TestDrive "release-result-created.txt"
            $id      = 222
            $url     = "https://github.com/GPID-WB/compound-gpid/releases/tag/v0.0.6"

            "CREATED|$id|$url" | Set-Content $outPath

            $content = Get-Content $outPath -Raw
            $content -match '^CREATED\|' | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Integration: invoke actual script for locally-testable failure cases
# (no HTTP calls -- tests only reach the validation stage)
# ---------------------------------------------------------------------------

Describe "create-release.ps1 - parameter validation (integration)" {
    It "exits with error for invalid tag format" {
        $scriptPath = Join-Path (Join-Path $PSScriptRoot "..") "create-release.ps1"
        { & $scriptPath -Tag "1.2.3" -Name "Test" -NotesFile (Join-Path $TestDrive "notes.md") } | Should -Throw
    }

    It "exits with error when NotesFile does not exist" {
        $scriptPath = Join-Path (Join-Path $PSScriptRoot "..") "create-release.ps1"
        { & $scriptPath -Tag "v1.0.0" -Name "Test" -NotesFile (Join-Path $TestDrive "nonexistent.md") } | Should -Throw
    }
}

Describe "create-release.ps1 - native packaging preflight" {
    BeforeAll {
        $scriptPath = Join-Path (Join-Path $PSScriptRoot "..") "create-release.ps1"
        $scriptContent = Get-Content $scriptPath -Raw -Encoding UTF8
    }

    It "invokes the operational preflight before the first GitHub API call" {
        $preflightIndex = $scriptContent.IndexOf("preflight", [System.StringComparison]::OrdinalIgnoreCase)
        $apiIndex = $scriptContent.IndexOf("Invoke-RestMethod", [System.StringComparison]::Ordinal)
        $preflightIndex | Should -BeGreaterThan -1
        $preflightIndex | Should -BeLessThan $apiIndex
    }

    It "checks preflight failure before credentials or API state transitions" {
        $preflightIndex = $scriptContent.IndexOf("preflight", [System.StringComparison]::OrdinalIgnoreCase)
        $credentialIndex = $scriptContent.IndexOf("git credential fill", [System.StringComparison]::Ordinal)
        $guard = $scriptContent.Substring($preflightIndex, $credentialIndex - $preflightIndex)
        $guard | Should -Match 'LASTEXITCODE'
        $guard | Should -Match '(throw|exit\s+1|Write-Error)'
    }

    It "requires an existing exact local and remote tag at the verified HEAD" {
        $scriptContent | Should -Match 'tag --list \$Tag'
        $scriptContent | Should -Match 'must exist locally before publication'
        $scriptContent | Should -Match 'ls-remote --tags origin'
        $scriptContent | Should -Match 'Remote release tag mismatch'
        $scriptContent | Should -Match 'target_commitish\s*=\s*\$headCommit'
        $scriptContent | Should -Not -Match 'rev-parse[^\r\n]+\|\s*Select-Object'
    }

    It "enforces the stable-main and prerelease-dev branch matrix" {
        $scriptContent | Should -Match '\$isPrereleaseTag\s*=\s*\$Tag -cmatch'
        $scriptContent | Should -Match '\$releaseBranch\s*=\s*"main"'
        $scriptContent | Should -Match 'if \(\$isPrereleaseTag\) \{ \$releaseBranch = "dev" \}'
        $scriptContent | Should -Match 'merge-base --is-ancestor \$headCommit \$remoteBranchCommit'
        $scriptContent | Should -Not -Match 'merge-base --is-ancestor \$remoteMainCommit \$headCommit'
        $scriptContent | Should -Not -Match 'Prerelease branch is stale: origin/main'
        $scriptContent | Should -Match 'prerelease\s*=\s*\$releasePrerelease'
    }

    It "validates payload set and exact Pages deployment before release API creation" {
        $setIndex = $scriptContent.IndexOf('--validate-release-set')
        $buildIndex = $scriptContent.IndexOf('actions/workflows/release-docs.yml/runs')
        $pagesIndex = $scriptContent.IndexOf('actions/workflows/release-pages.yml/runs')
        $releaseIndex = $scriptContent.LastIndexOf('Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases"')
        $setIndex | Should -BeGreaterThan -1
        $buildIndex | Should -BeGreaterThan $setIndex
        $pagesIndex | Should -BeGreaterThan $buildIndex
        $releaseIndex | Should -BeGreaterThan $pagesIndex
        $scriptContent | Should -Match '\$_.head_sha -eq \$headCommit -and \$_.head_branch -eq \$Tag'
        $scriptContent | Should -Match "Protect release tags"
        $scriptContent | Should -Match 'Get-CgRepositoryRuleset'
        $scriptContent | Should -Match '\$RulesetName'
        $scriptContent | Should -Match '\$RulesetTarget'
        $scriptContent | Should -Not -Match 'Get-CgRepositoryRuleset -Name'
        $scriptContent | Should -Match '\$summaryResponse\s*=\s*Invoke-RestMethod'
        $scriptContent | Should -Match '\$summaries\s*=\s*@\(\$summaryResponse\)'
        $scriptContent | Should -Match 'foreach \(\$summary in \$summaries\)'
        $scriptContent | Should -Match 'after 3 attempts'
        $scriptContent | Should -Match 'missing update rule'
        $scriptContent | Should -Match 'ruleTypes -notcontains "update"'
        $scriptContent | Should -Match 'non_fast_forward'
        $scriptContent | Should -Match 'bypassActors\.Count -ne 0'
        $scriptContent | Should -Match 'Restrict release tag creation'
        $scriptContent | Should -Match 'creationRuleTypes -notcontains "creation"'
        $scriptContent | Should -Match 'Protect dev'
        $scriptContent | Should -Match '\$_.name -eq \$controllerRunName'
        $scriptContent | Should -Match '\$publishedReleaseResponse\s*=\s*Invoke-RestMethod'
        $scriptContent | Should -Match '\$publishedReleases\s*=\s*@\(\$publishedReleaseResponse\)'
        $scriptContent | Should -Match 'Assert-CgRemoteReleaseLineage'
        $scriptContent | Should -Match 'has no published GitHub Release'
        $scriptContent | Should -Match 'Method Delete'
        $scriptContent | Should -Match 'Assert-CgRemoteTagCommit[\s\S]*Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases"[\s\S]*Assert-CgRemoteTagCommit'
    }

    It "rejects drafts and verifies the public release body" {
        $scriptContent | Should -Match 'Draft releases are not supported'
        $scriptContent | Should -Match 'ConvertTo-CgNormalizedReleaseText \$existingRelease\.body'
        $scriptContent | Should -Match 'ConvertTo-CgNormalizedReleaseText \$response\.body'
        $scriptContent | Should -Match 'draft\s*=\s*\$false'
    }

    It "tests the exact commit in an isolated LF checkout" {
        $scriptContent | Should -Match 'clone --quiet --no-hardlinks --no-checkout'
        $scriptContent | Should -Match 'core\.autocrlf false'
        $scriptContent | Should -Match 'checkout --detach --quiet \$headCommit'
        $scriptContent | Should -Match 'Remove-Item -LiteralPath \$preflightRoot -Recurse -Force'
    }

    It "writes reviewed post-release skill attestation for existing and new releases" {
        $scriptContent | Should -Match 'scripts/cg_release_attestation\.py'
        $scriptContent | Should -Match '--review-reference "release=\$headCommit"'
        ([regex]::Matches($scriptContent, 'Write-CgReleaseAttestation')).Count | Should -Be 3
        $existingIndex = $scriptContent.IndexOf('if ($null -ne $existingRelease)')
        $createIndex = $scriptContent.IndexOf('# Create the release')
        $existingBlock = $scriptContent.Substring($existingIndex, $createIndex - $existingIndex)
        ($existingBlock -match 'Write-CgReleaseAttestation') | Should -Be $true
        $createBlock = $scriptContent.Substring($createIndex)
        ($createBlock -match 'Write-CgReleaseAttestation') | Should -Be $true
    }

    It "executes a failing preflight without reaching credentials or the API" {
        $notesPath = Join-Path $TestDrive "release-preflight-notes.md"
        Set-Content -Path $notesPath -Value "notes" -Encoding UTF8
        $script:credentialCalled = $false
        $script:apiCalled = $false
        $script:queriedMain = $false
        function global:git {
            $global:LASTEXITCODE = 0
            if (($args -join ' ') -match 'refs/heads/main|origin/main') { $script:queriedMain = $true }
            if ($args[0] -eq "-C" -and $args[2] -eq "rev-parse") { return "abc123" }
            if ($args[0] -eq "-C" -and $args[2] -eq "tag") { return "v1.2.0.9006" }
            if ($args[0] -eq "-C" -and $args[2] -eq "ls-remote" -and $args[3] -eq "--heads") { return "abc123`trefs/heads/dev" }
            if ($args[0] -eq "-C" -and $args[2] -eq "ls-remote" -and $args[3] -eq "--tags") { return "abc123`trefs/tags/v1.2.0.9006" }
            if ($args[0] -eq "-C" -and $args[2] -eq "status") { return }
            if ($args[0] -eq "credential") { $script:credentialCalled = $true; return "password=fake" }
        }
        function global:python3 {
            if ($args[0] -eq "--version") { $global:LASTEXITCODE = 0; return "Python 3.11.0" }
            $global:LASTEXITCODE = 7
        }
        function global:Invoke-RestMethod { $script:apiCalled = $true }
        try {
            { & $scriptPath -Tag "v1.2.0.9006" -Name "v1.2.0.9006 - Manifest-driven skill loading, certified contained launcher, and quarantined skill importing" -NotesFile $notesPath } | Should -Throw
            $script:credentialCalled | Should -Be $false
            $script:apiCalled | Should -Be $false
            $script:queriedMain | Should -Be $false
        } finally {
            Remove-Item Function:\git -Force -ErrorAction SilentlyContinue
            Remove-Item Function:\python3 -Force -ErrorAction SilentlyContinue
            Remove-Item Function:\Invoke-RestMethod -Force -ErrorAction SilentlyContinue
            $global:LASTEXITCODE = 0
        }
    }
}
