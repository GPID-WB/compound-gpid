# tests/create-release.Tests.ps1
# Pester tests for create-release.ps1
#
# Run with: Invoke-Pester tests/create-release.Tests.ps1
# Requires Pester 4.10.1 through tests/Run-Tests.ps1.
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
        $scriptContent | Should -Match 'merge-base --is-ancestor \$ExpectedCommit \$branchCommit'
        $scriptContent | Should -Match 'new remote tag requires HEAD at exact current origin/'
        $scriptContent | Should -Not -Match 'merge-base --is-ancestor \$remoteMainCommit \$headCommit'
        $scriptContent | Should -Not -Match 'Prerelease branch is stale: origin/main'
        $scriptContent | Should -Match 'prerelease\s*=\s*\$releasePrerelease'
    }

    It "reserves the release before querying the exact Pages deployment" {
        $setIndex = $scriptContent.IndexOf('--validate-release-set')
        $buildIndex = $scriptContent.IndexOf('actions/workflows/release-docs.yml/runs')
        $pagesIndex = $scriptContent.IndexOf('actions/workflows/release-pages.yml/runs')
        $releaseIndex = $scriptContent.LastIndexOf('Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases"')
        $setIndex | Should -BeGreaterThan -1
        $buildIndex | Should -BeGreaterThan $setIndex
        $pagesIndex | Should -BeGreaterThan $buildIndex
        $releaseIndex | Should -BeLessThan $buildIndex
        $releaseIndex | Should -BeGreaterThan $setIndex
        $scriptContent | Should -Match '\$_.head_sha -ceq \$headCommit -and \$_.head_branch -ceq \$Tag'
        $scriptContent | Should -Match "Protect release tags"
        $scriptContent | Should -Match 'Get-CgRepositoryRuleset'
        $scriptContent | Should -Match '\$RulesetName'
        $scriptContent | Should -Match '\$RulesetTarget'
        $scriptContent | Should -Not -Match 'Get-CgRepositoryRuleset -Name'
        $scriptContent | Should -Match '\$summaryResponse\s*=\s*Invoke-CgReleaseApi'
        $scriptContent | Should -Match '\$summaries\s*=\s*@\(\$summaryResponse\)'
        $scriptContent | Should -Match 'foreach \(\$summary in \$summaries\)'
        $scriptContent | Should -Match 'after 3 attempts'
        $scriptContent | Should -Match 'missing update rule'
        $scriptContent | Should -Match 'ruleTypes -cnotcontains "update"'
        $scriptContent | Should -Match 'non_fast_forward'
        $scriptContent | Should -Match 'bypassActors\.Count -ne 0'
        $scriptContent | Should -Match 'Restrict release tag creation'
        $scriptContent | Should -Match 'creationRuleTypes -cnotcontains "creation"'
        $scriptContent | Should -Match 'Protect dev'
        $scriptContent | Should -Match '\$_.name -ceq \$controllerRunName'
        $scriptContent | Should -Match 'Get-CgPublishedReleases'
        $scriptContent | Should -Match 'Duplicate GitHub Release entries'
        $scriptContent | Should -Match 'Assert-CgRemoteReleaseLineage'
        $scriptContent | Should -Match 'has no published GitHub Release'
        $scriptContent | Should -Not -Match '-Method (Delete|Patch)'
        $scriptContent | Should -Match 'make_latest\s*=\s*"false"'
        $scriptContent | Should -Not -Match 'push[^\r\n]+--force'
        $scriptContent | Should -Match 'Assert-CgRemoteTagCommit[\s\S]*Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases"[\s\S]*Assert-CgRemoteTagCommit'
    }

    It "rejects drafts and verifies the public release body" {
        $scriptContent | Should -Match 'Draft releases are not supported'
        $scriptContent | Should -Match 'ConvertTo-CgNormalizedReleaseText \$Release\.body'
        $scriptContent | Should -Match '\$Release\.draft -isnot \[bool\]'
        $scriptContent | Should -Match 'draft\s*=\s*\$false'
    }

    It "tests the exact commit in an isolated LF checkout" {
        $scriptContent | Should -Match 'clone --quiet --no-hardlinks --no-checkout'
        $scriptContent | Should -Match 'core\.autocrlf false'
        $scriptContent | Should -Match 'checkout --detach --quiet \$headCommit'
        $scriptContent | Should -Match 'Remove-Item -LiteralPath \$preflightRoot -Recurse -Force'
    }

    It "writes reviewed attestation only in Finalize after reservation returns" {
        $scriptContent | Should -Match 'scripts/cg_release_attestation\.py'
        $scriptContent | Should -Match '--review-reference "release=\$headCommit"'
        ([regex]::Matches($scriptContent, 'Write-CgReleaseAttestation')).Count | Should -Be 2
        $finalizeIndex = $scriptContent.IndexOf('# Finalize is read-only remotely')
        $scriptContent.LastIndexOf('Write-CgReleaseAttestation') | Should -BeGreaterThan $finalizeIndex
        $scriptContent.Substring($finalizeIndex) | Should -Not -Match '-Method Post|push origin'
        $scriptContent | Should -Match 'FINALIZED\|'
        $scriptContent | Should -Match 'Write-Host "RESERVED \(\$reservationStatus\)'
        $scriptContent | Should -Match 'Write-Host "FINALIZED:'
    }

}

Describe "create-release.ps1 - executable two-phase publication with offline mocks" {
    BeforeEach {
        $script:fixture = Join-Path $TestDrive ("release-" + [guid]::NewGuid().ToString('N'))
        New-Item -ItemType Directory -Path (Join-Path $script:fixture "releases") -Force | Out-Null
        Copy-Item (Join-Path $PSScriptRoot "../create-release.ps1") (Join-Path $script:fixture "create-release.ps1") -Force
        $script:state = @{
            Tag = "v1.2.0.9015"; Head = ('a' * 40); Object = ('b' * 40); Tip = ('a' * 40)
            Remote = $false; RemoteObject = ('b' * 40); RemoteCommit = ('a' * 40)
            TagType = "tag"; Release = $null; DraftOnly = $false; Duplicate = $false
            LookupError = 0; PostMode = "success"; PushMode = "success"; Dirty = @()
            PreflightExit = 0; AttestationExit = 0; CheckExit = 0; NodeExit = 0
            DocsStatus = "success"; PagesStatus = "success"; BadChain = $false
            CredentialExit = 0; Calls = [System.Collections.Generic.List[string]]::new()
            Origin = 'https://github.com/GPID-WB/compound-gpid.git'
            PagesName = 'Deploy docs from 10'; PagesPath = '.github/workflows/release-pages.yml'
        }
        $script:expected = [pscustomobject]@{
            id = 123; html_url = "https://github.com/GPID-WB/compound-gpid/releases/tag/v1.2.0.9015"
            tag_name = $script:state.Tag; target_commitish = $script:state.Head
            name = "v1.2.0.9015 - Pairing"; body = "Exact final notes"; draft = $false
            prerelease = $true; published_at = "2026-09-10T00:00:00Z"
        }
        @{ tag = $script:state.Tag; name = $script:expected.name; url = $script:expected.html_url; publishedAt = "2026-09-10T00:00:00Z" } |
            ConvertTo-Json | Set-Content (Join-Path $script:fixture "releases/v1.2.0.9015.json")
        Set-Content (Join-Path $script:fixture "notes.md") $script:expected.body -NoNewline
        Set-Content (Join-Path $script:fixture "release-result.txt") "FINALIZED|stale"
        # Native command substitutes run in the invoked script's scope on PS5.1.
        $global:CgReleaseTestState = $script:state
        $global:CgReleaseTestExpected = $script:expected
        function global:git {
            $script:state = $global:CgReleaseTestState
            $global:LASTEXITCODE = 0
            $call = $args -join ' '
            $script:state.Calls.Add("git $call")
            if ($args[0] -eq 'credential') {
                $global:LASTEXITCODE = $script:state.CredentialExit
                return "password=SECRET-MUST-NOT-LEAK"
            }
            switch -Regex ($call) {
                ' remote get-url ' { return $script:state.Origin }
                ' rev-parse --verify HEAD' { return $script:state.Head }
                ' rev-parse --verify origin/' { return $script:state.Tip }
                ' rev-parse --verify .*\^\{commit\}' { return $script:state.Head }
                ' rev-parse --verify refs/tags/' { return $script:state.Object }
                ' tag --list ' { return $script:state.Tag }
                ' cat-file -t ' { return $script:state.TagType }
                ' ls-remote --heads ' { return "$($script:state.Tip)`t$($args[-1])" }
                ' ls-remote --tags ' {
                    if ($script:state.Remote) {
                        return @("$($script:state.RemoteObject)`trefs/tags/$($script:state.Tag)", "$($script:state.RemoteCommit)`trefs/tags/$($script:state.Tag)^{}")
                    }
                    return
                }
                ' status --porcelain ' { return $script:state.Dirty }
                ' push origin ' {
                    if ($script:state.PushMode -ne 'absent') { $script:state.Remote = $true }
                    if ($script:state.PushMode -ne 'success') { $global:LASTEXITCODE = 1; throw "uncertain push" }
                    return
                }
                ' fetch origin | merge-base --is-ancestor | clone --quiet | config core\.| checkout --detach ' { return }
                default { throw "Unmocked git call blocked: $call" }
            }
        }
        function global:python3 {
            $script:state = $global:CgReleaseTestState
            $global:LASTEXITCODE = 0
            if ($args[0] -eq '--version') { return 'Python 3.11.0' }
            $call = $args -join ' '
            $script:state.Calls.Add("python $call")
            if ($call -match 'cg_pr_preflight.py') { $global:LASTEXITCODE = $script:state.PreflightExit; return }
            if ($call -match 'cg_release_attestation.py') {
                if ($args -contains '--check') { $global:LASTEXITCODE = $script:state.CheckExit }
                else { $global:LASTEXITCODE = $script:state.AttestationExit }
                return
            }
            throw "Unmocked Python call blocked: $call"
        }
        function global:Invoke-CgFixtureNode {
            $script:state = $global:CgReleaseTestState
            $script:state.Calls.Add("node $($args -join ' ')")
            $global:LASTEXITCODE = $script:state.NodeExit
        }
        Mock Get-Command { [pscustomobject]@{ Source = 'Invoke-CgFixtureNode' } } -ParameterFilter { $Name -eq 'node' }
        Mock Invoke-RestMethod {
            param($Uri, $Method, $Headers, $Body)
            $script:state = $global:CgReleaseTestState
            $script:expected = $global:CgReleaseTestExpected
            $script:state.Calls.Add("api $Method $Uri")
            if ($Uri -match '/rulesets$') {
                return @(
                    [pscustomobject]@{ id = 1; name = 'Protect release tags'; target = 'tag'; enforcement = 'active' },
                    [pscustomobject]@{ id = 2; name = 'Restrict release tag creation'; target = 'tag'; enforcement = 'active' },
                    [pscustomobject]@{ id = 3; name = 'Protect dev'; target = 'branch'; enforcement = 'active' }
                )
            }
            if ($Uri -match '/rulesets/([123])$') {
                $id = $Matches[1]
                $types = @('update', 'deletion', 'non_fast_forward'); $include = 'refs/tags/v*'; $bypass = @()
                if ($id -eq '2') { $types = @('creation'); $bypass = @([pscustomobject]@{ actor_type = 'RepositoryRole'; actor_id = 5; bypass_mode = 'always' }) }
                if ($id -eq '3') { $include = 'refs/heads/dev' }
                return [pscustomobject]@{
                    rules = @($types | ForEach-Object { [pscustomobject]@{ type = $_ } })
                    conditions = [pscustomobject]@{ ref_name = [pscustomobject]@{ include = @($include); exclude = @() } }
                    bypass_actors = $bypass; current_user_can_bypass = 'never'
                }
            }
            if ($Uri -match '/releases\?') {
                if ($script:state.DraftOnly) { $draft = $script:expected.PSObject.Copy(); $draft.draft = $true; return $draft }
                if ($script:state.Duplicate) { return @($script:expected, $script:expected) }
                if ($null -ne $script:state.Release) { return $script:state.Release }
                return @()
            }
            if ($Uri -match '/releases/tags/') {
                $code = $script:state.LookupError
                if (-not $code -and $null -eq $script:state.Release) { $code = 404 }
                if ($code) {
                    $errorValue = [System.Exception]::new('SECRET-MUST-NOT-LEAK')
                    $errorValue | Add-Member NoteProperty Response ([pscustomobject]@{ StatusCode = $code })
                    throw $errorValue
                }
                return $script:state.Release
            }
            if ($Uri -match '/releases$' -and $Method -eq 'Post') {
                $posted = [System.Text.Encoding]::UTF8.GetString($Body) | ConvertFrom-Json
                $posted.name | Should -BeExactly $script:expected.name
                $posted.body | Should -BeExactly $script:expected.body
                $posted.target_commitish | Should -BeExactly $script:state.Head
                $posted.draft | Should -Be $false
                ($posted.make_latest -is [string]) | Should -Be $true
                $posted.make_latest | Should -BeExactly 'false'
                if ($script:state.PostMode -ne 'absent') { $script:state.Release = $script:expected.PSObject.Copy() }
                if ($script:state.PostMode -eq 'conflict') { $script:state.Release.name = 'conflict' }
                if ($script:state.PostMode -ne 'success') { throw 'SECRET-MUST-NOT-LEAK' }
                return $script:state.Release
            }
            if ($Uri -match 'release-docs.yml/runs|actions/runs/10$') {
                $run = [pscustomobject]@{ id = 10; head_sha = $script:state.Head; head_branch = $script:state.Tag; event = 'push'; path = '.github/workflows/release-docs.yml'; status = 'completed'; conclusion = $script:state.DocsStatus }
                if ($script:state.BadChain) { $run.head_sha = ('c' * 40) }
                if ($Uri -match 'actions/runs/10$') { return $run }
                return [pscustomobject]@{ workflow_runs = @($run) }
            }
            if ($Uri -match 'release-pages.yml/runs|actions/runs/20$') {
                $run = [pscustomobject]@{ id = 20; name = $script:state.PagesName; display_title = $script:state.PagesName; event = 'workflow_run'; path = $script:state.PagesPath; status = 'completed'; conclusion = $script:state.PagesStatus }
                if ($Uri -match 'actions/runs/20$') { return $run }
                return [pscustomobject]@{ workflow_runs = @($run) }
            }
            throw "Unmocked HTTP call blocked: $Method $Uri"
        }
        function Invoke-FixtureRelease {
            param([string]$Phase = 'Reserve', [switch]$ExactRuns)
            $parameters = @{ Tag = $script:state.Tag; Name = $script:expected.name; NotesFile = (Join-Path $script:fixture 'notes.md'); Phase = $Phase }
            if ($ExactRuns) { $parameters.BuildRunId = 10; $parameters.PagesRunId = 20 }
            & (Join-Path $script:fixture 'create-release.ps1') @parameters
        }
    }
    AfterEach {
        @($script:state.Calls | Where-Object { $_ -match '^api (Delete|Patch) ' }).Count | Should -Be 0
        Remove-Item Function:\git, Function:\python3, Function:\Invoke-CgFixtureNode -Force -ErrorAction SilentlyContinue
        Remove-Variable CgReleaseTestState, CgReleaseTestExpected -Scope Global -ErrorAction SilentlyContinue
        $global:LASTEXITCODE = 0
    }

    It 'reserves final metadata immediately after the exact tag push without docs or attestation' {
        Invoke-FixtureRelease
        Get-Content (Join-Path $script:fixture 'release-result.txt') | Should -Match '^CREATED\|123\|'
        $calls = $script:state.Calls -join "`n"
        $calls | Should -Match ('push origin --no-follow-tags ' + ('b' * 40) + ':refs/tags/v1.2.0.9015')
        $calls | Should -Not -Match 'actions/|cg_release_attestation.py'
        $calls.IndexOf('cg_pr_preflight.py') | Should -BeLessThan $calls.IndexOf('push origin')
        $calls.IndexOf('/releases/tags/') | Should -BeLessThan $calls.IndexOf('push origin')
        $calls.IndexOf('push origin') | Should -BeLessThan $calls.IndexOf('api Post')
    }
    It 'accepts a matching retry on authorized lineage after the branch advances without push or POST' {
        $script:state.Remote = $true; $script:state.Release = $script:expected; $script:state.Tip = ('c' * 40)
        Invoke-FixtureRelease
        Get-Content (Join-Path $script:fixture 'release-result.txt') | Should -Match '^EXISTS\|'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post|actions/'
    }
    It 'reserves a stable release only from exact origin/main without requiring a branch name' {
        Remove-Item (Join-Path $script:fixture 'releases/v1.2.0.9015.json')
        $script:state.Tag = 'v1.2.0'
        $script:expected.tag_name = 'v1.2.0'; $script:expected.name = 'v1.2.0 - Pairing'
        $script:expected.html_url = 'https://github.com/GPID-WB/compound-gpid/releases/tag/v1.2.0'
        $script:expected.prerelease = $false
        @{ tag = $script:state.Tag; name = $script:expected.name; url = $script:expected.html_url; publishedAt = '2026-09-10T00:00:00Z' } |
            ConvertTo-Json | Set-Content (Join-Path $script:fixture 'releases/v1.2.0.json')
        Invoke-FixtureRelease
        $calls = $script:state.Calls -join "`n"
        $calls | Should -Match 'refs/heads/main'
        $calls | Should -Not -Match 'refs/heads/dev|branch --show-current|symbolic-ref'
        $script:state.Release.prerelease | Should -Be $false
    }
    It 'rejects a noncanonical origin before publication without displaying its URL' {
        $script:state.Origin = 'https://SECRET-MUST-NOT-LEAK@github.com/elsewhere/fork.git'
        { Invoke-FixtureRelease } | Should -Throw 'one canonical GPID-WB/compound-gpid'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects missing historical Release pairing before a new tag push' {
        @{ tag = 'v1.2.0.9014'; name = 'prior'; publishedAt = '2026-09-09T00:00:00Z' } |
            ConvertTo-Json | Set-Content (Join-Path $script:fixture 'releases/v1.2.0.9014.json')
        { Invoke-FixtureRelease } | Should -Throw 'has no published GitHub Release'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects invalid local payloads before credentials or tag push' {
        $script:state.NodeExit = 1
        { Invoke-FixtureRelease } | Should -Throw 'payload validation failed'
        ($script:state.Calls -join "`n") | Should -Not -Match 'credential fill|push origin|api Post'
    }
    It 'rejects a case-only payload name mismatch before publication' {
        $script:expected.name = 'v1.2.0.9015 - PAIRING'
        { Invoke-FixtureRelease } | Should -Throw 'arguments do not match the immutable payload'
        ($script:state.Calls -join "`n") | Should -Not -Match 'credential fill|push origin|api Post'
    }
    It 'blocks a new tag at a stale authorized branch commit' {
        $script:state.Tip = ('c' * 40)
        { Invoke-FixtureRelease } | Should -Throw 'exact current origin/dev'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects a lightweight local tag before publication' {
        $script:state.TagType = 'commit'
        { Invoke-FixtureRelease } | Should -Throw 'annotated'
    }
    It 'rejects remote raw object mismatch even when the peeled commit matches' {
        $script:state.Remote = $true; $script:state.RemoteObject = ('c' * 40)
        { Invoke-FixtureRelease } | Should -Throw 'Remote release tag mismatch'
    }
    It 'rejects remote peeled commit mismatch' {
        $script:state.Remote = $true; $script:state.RemoteCommit = ('c' * 40)
        { Invoke-FixtureRelease } | Should -Throw 'Remote release tag mismatch'
    }
    It 'fails preflight before credentials, API calls, or tag push' {
        $script:state.PreflightExit = 7
        { Invoke-FixtureRelease } | Should -Throw 'preflight failed with exit code 7'
        ($script:state.Calls -join "`n") | Should -Not -Match 'credential fill|^api |push origin'
        Test-Path (Join-Path $script:fixture 'release-result.txt') | Should -Be $false
    }
    It 'rejects credential failure without printing helper secrets' {
        $script:state.CredentialExit = 1
        { Invoke-FixtureRelease } | Should -Throw 'credential lookup failed'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'fails closed on non-404 lookup errors without leaking the response' -TestCases @(@{ Code = 401 }, @{ Code = 403 }, @{ Code = 500 }) {
        param($Code)
        $script:state.LookupError = $Code
        { Invoke-FixtureRelease } | Should -Throw 'Remote error details suppressed'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects same-tag drafts hidden from the tag lookup' {
        $script:state.DraftOnly = $true
        { Invoke-FixtureRelease } | Should -Throw 'Conflicting GitHub Release lookup'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects duplicate release list entries' {
        $script:state.Duplicate = $true
        { Invoke-FixtureRelease } | Should -Throw 'Duplicate GitHub Release'
    }
    It 'rejects metadata or publication conflicts' -TestCases @(
        @{ Field = 'name'; Value = 'wrong' }, @{ Field = 'body'; Value = 'wrong' },
        @{ Field = 'name'; Value = 'v1.2.0.9015 - PAIRING' }, @{ Field = 'body'; Value = 'EXACT FINAL NOTES' },
        @{ Field = 'html_url'; Value = 'https://example.invalid' }, @{ Field = 'target_commitish'; Value = 'dev' },
        @{ Field = 'draft'; Value = $true }, @{ Field = 'prerelease'; Value = $false },
        @{ Field = 'draft'; Value = 'false' }, @{ Field = 'published_at'; Value = '' }
    ) {
        param($Field, $Value)
        $script:state.Remote = $true; $script:state.Release = $script:expected.PSObject.Copy()
        $script:state.Release.$Field = $Value
        { Invoke-FixtureRelease } | Should -Throw 'immutable release metadata'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects missing public fields' -TestCases @(@{ Field = 'draft' }, @{ Field = 'published_at' }, @{ Field = 'body' }, @{ Field = 'id' }) {
        param($Field)
        $script:state.Remote = $true; $script:state.Release = $script:expected.PSObject.Copy()
        $script:state.Release.PSObject.Properties.Remove($Field)
        { Invoke-FixtureRelease } | Should -Throw 'missing required field'
    }
    It 'reconciles an uncertain successful push and pairs the tag' {
        $script:state.PushMode = 'uncertain'
        Invoke-FixtureRelease
        $script:state.Release.id | Should -Be 123
    }
    It 'reconciles a failed push read-only and does not POST' {
        $script:state.PushMode = 'absent'
        { Invoke-FixtureRelease } | Should -Throw 'remote tag identity could not be confirmed'
        @($script:state.Calls | Where-Object { $_ -match '/releases/tags/' }).Count | Should -Be 2
        ($script:state.Calls -join "`n") | Should -Not -Match 'api Post'
    }
    It 'reconciles a lost successful POST response without repeating POST' {
        $script:state.PostMode = 'uncertain'
        Invoke-FixtureRelease
        @($script:state.Calls | Where-Object { $_ -match '^api Post ' }).Count | Should -Be 1
        Get-Content (Join-Path $script:fixture 'release-result.txt') | Should -Match '^CREATED\|'
    }
    It 'leaves an unpaired tag and fails explicitly when ambiguous POST has no Release' {
        $script:state.PostMode = 'absent'
        { Invoke-FixtureRelease } | Should -Throw 'Reservation is incomplete'
        $script:state.Remote | Should -Be $true
        @($script:state.Calls | Where-Object { $_ -match '^api Post ' }).Count | Should -Be 1
        Test-Path (Join-Path $script:fixture 'release-result.txt') | Should -Be $false
    }
    It 'rejects conflicting metadata after an ambiguous POST without deleting it' {
        $script:state.PostMode = 'conflict'
        { Invoke-FixtureRelease } | Should -Throw 'immutable release metadata'
        $script:state.Release.name | Should -Be 'conflict'
    }
    It 'leaves the Release intact when docs fail during Finalize' {
        Invoke-FixtureRelease
        $script:state.DocsStatus = 'failure'
        { Invoke-FixtureRelease -Phase Finalize } | Should -Throw 'release-docs.yml'
        $script:state.Release.id | Should -Be 123
        Test-Path (Join-Path $script:fixture 'release-result.txt') | Should -Be $false
    }
    It 'rejects a successful docs run at the wrong SHA' {
        $script:state.Remote = $true; $script:state.Release = $script:expected; $script:state.BadChain = $true
        { Invoke-FixtureRelease -Phase Finalize -ExactRuns } | Should -Throw 'release-docs.yml'
    }
    It 'requires successful Pages and leaves the pair intact' {
        $script:state.Remote = $true; $script:state.Release = $script:expected; $script:state.PagesStatus = 'failure'
        { Invoke-FixtureRelease -Phase Finalize } | Should -Throw 'release-pages.yml'
        $script:state.Release.id | Should -Be 123
    }
    It 'rejects a successful controller from another build or workflow' -TestCases @(
        @{ Field = 'PagesName'; Value = 'Deploy docs from 99' },
        @{ Field = 'PagesName'; Value = 'DEPLOY DOCS FROM 10' },
        @{ Field = 'PagesPath'; Value = '.github/workflows/pages.yml' }
    ) {
        param($Field, $Value)
        $script:state.Remote = $true; $script:state.Release = $script:expected; $script:state[$Field] = $Value
        { Invoke-FixtureRelease -Phase Finalize -ExactRuns } | Should -Throw 'release-pages.yml'
        ($script:state.Calls -join "`n") | Should -Not -Match 'cg_release_attestation.py|push origin|api Post'
    }
    It 'never creates lifecycle attestation for withdrawn 9014' {
        $script:state.Tag = 'v1.2.0.9014'
        { Invoke-FixtureRelease -Phase Finalize } | Should -Throw 'not eligible for lifecycle attestation'
        $script:state.Calls.Count | Should -Be 0
    }
    It 'finalizes the exact successful chain then attests without remote mutations' {
        $script:state.Remote = $true; $script:state.Release = $script:expected
        Invoke-FixtureRelease -Phase Finalize -ExactRuns
        Get-Content (Join-Path $script:fixture 'release-result.txt') | Should -Match '^FINALIZED\|'
        $calls = $script:state.Calls -join "`n"
        $calls | Should -Not -Match 'push origin|api Post'
        $calls.LastIndexOf('cg_release_attestation.py') | Should -BeGreaterThan $calls.IndexOf('/actions/runs/20')
    }
    It 'does not create a Release from Finalize' {
        $script:state.Remote = $true
        { Invoke-FixtureRelease -Phase Finalize } | Should -Throw 'Run Reserve first'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post|actions/'
    }
    It 'leaves the Release intact on attestation failure' {
        $script:state.Remote = $true; $script:state.Release = $script:expected; $script:state.AttestationExit = 9
        { Invoke-FixtureRelease -Phase Finalize } | Should -Throw 'attestation failed'
        $script:state.Release.id | Should -Be 123
        Test-Path (Join-Path $script:fixture 'release-result.txt') | Should -Be $false
    }
    It 'allows an identical canonical untracked attestation retry only after read-only validation' {
        $script:state.Remote = $true; $script:state.Release = $script:expected
        $script:state.Dirty = @('?? .github/shared/skill-management/release-attestations/v1.2.0.9015.json')
        Invoke-FixtureRelease -Phase Finalize
        ($script:state.Calls -join "`n") | Should -Match 'cg_release_attestation.py[^\n]+--check'
    }
    It 'rejects an altered canonical untracked attestation' {
        $script:state.Remote = $true; $script:state.Release = $script:expected; $script:state.CheckExit = 1
        $script:state.Dirty = @('?? .github/shared/skill-management/release-attestations/v1.2.0.9015.json')
        { Invoke-FixtureRelease -Phase Finalize } | Should -Throw 'identical canonical attestation'
    }
    It 'rejects arbitrary dirty files even with a canonical attestation' {
        $script:state.Dirty = @('?? arbitrary.txt', '?? .github/shared/skill-management/release-attestations/v1.2.0.9015.json')
        { Invoke-FixtureRelease } | Should -Throw 'must be clean'
    }
}
