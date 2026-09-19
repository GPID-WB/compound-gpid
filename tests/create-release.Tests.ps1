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
        { & $scriptPath -LegacyOperation Recovery -Tag "1.2.3" -Name "Test" -NotesFile (Join-Path $TestDrive "notes.md") } | Should -Throw
    }

    It "exits with error when NotesFile does not exist" {
        $scriptPath = Join-Path (Join-Path $PSScriptRoot "..") "create-release.ps1"
        { & $scriptPath -LegacyOperation Recovery -Tag "v1.0.0" -Name "Test" -NotesFile (Join-Path $TestDrive "nonexistent.md") } | Should -Throw
    }
    It "rejects routine legacy publication before any remote operation" {
        $scriptPath = Join-Path (Join-Path $PSScriptRoot "..") "create-release.ps1"
        { & $scriptPath -Tag "v1.0.0" -Name "Test" -NotesFile (Join-Path $TestDrive "notes.md") } | Should -Throw 'Routine publication uses cg-release start'
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

    It "selects an explicit or attached source branch while retaining remote lineage checks" {
        $scriptContent | Should -Match '\$isPrereleaseTag\s*=\s*\$Tag -cmatch'
        $scriptContent | Should -Match '\$releaseBranch\s*=\s*\$SourceBranch'
        $scriptContent | Should -Match 'symbolic-ref --quiet --short HEAD'
        $scriptContent | Should -Match 'detached release checkout requires explicit -SourceBranch'
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

    It "accepts an optional preflight receipt without removing the full gate" {
        $scriptContent | Should -Match '\[string\]\$PreflightReceipt'
        $scriptContent | Should -Match 'Preflight receipt accepted for'
        $scriptContent | Should -Match 'skipping re-run'
        $scriptContent | Should -Match '--phase committed --full-gate --run-native-target'
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
        $authorityHelper = Join-Path $PSScriptRoot '../scripts/release-legacy-authority.ps1'
        if (Test-Path $authorityHelper) {
            New-Item -ItemType Directory -Path (Join-Path $script:fixture 'scripts') -Force | Out-Null
            Copy-Item $authorityHelper (Join-Path $script:fixture 'scripts/release-legacy-authority.ps1')
        }
        $script:state = @{
            Tag = "v1.2.0.9015"; Head = ('a' * 40); Object = ('b' * 40); Tip = ('a' * 40)
            Remote = $false; RemoteObject = ('b' * 40); RemoteCommit = ('a' * 40)
            TagType = "tag"; Release = $null; DraftOnly = $false; Duplicate = $false
            ListExtras = @()
            LookupError = 0; PostMode = "success"; PushMode = "success"; Dirty = @()
            PreflightExit = 0; AttestationExit = 0; CheckExit = 0; NodeExit = 0
            DocsStatus = "success"; PagesStatus = "success"; BadChain = $false
            CredentialExit = 0; Calls = [System.Collections.Generic.List[string]]::new()
            Origin = 'https://github.com/GPID-WB/compound-gpid.git'
            PagesName = 'Deploy docs from 10'; PagesPath = '.github/workflows/release-pages.yml'
            Default = 'production'; PolicyEnabled = $false; CutoverAfterPush = $false
            Protected = $true; Role = 'admin'; RecoveryRecord = $null; BadRuleset = $false
            PagesEvent = 'workflow_run'; ArtifactDigest = ('sha256:' + ('e' * 64))
            PolicySha = ('d' * 40)
            BadDefaultRef = $false; BadDeployJob = $false; BadDeployment = $false; WithdrawAfterArtifact = $false
            MainAncestorExit = 0; WorkflowReadExit = 0
            CurrentBranch = 'dev'; SourceBranchExists = $true; SourceAncestorExit = 0
            ProductionBranches = @('main'); PolicyJson = $null
            RevokeSourceAfterPush = $false
            BuildAttempt = 1; BuildJobs = @(); BuildArtifacts = @()
            Producer = (Get-Content (Join-Path $PSScriptRoot '../.github/workflows/release-docs.yml') -Raw)
            Controller = (Get-Content (Join-Path $PSScriptRoot '../.github/workflows/release-pages.yml') -Raw)
        }
        $script:state.Tree = ('c' * 40)
        $requiredBuildSteps = @('Check out immutable tag commit', 'Set up Node', 'Validate tag, lineage, and durable payload',
            'Build complete documentation tree', 'Validate tagged documentation site', 'Require isolated release metadata',
            'Upload isolated release documentation artifact')
        $stepNumber = 0
        $script:state.BuildJobs = @([pscustomobject]@{ id = 60; name = 'build'; run_id = 10; run_attempt = 1;
            head_sha = $script:state.Head; status = 'completed'; conclusion = 'success';
            started_at = '2026-09-17T00:00:00Z'; completed_at = '2026-09-17T00:02:00Z';
            steps = @($requiredBuildSteps | ForEach-Object { $stepNumber++; [pscustomobject]@{name = $_; number = $stepNumber; status = 'completed'; conclusion = 'success'} }) })
        $script:state.BuildArtifacts = @([pscustomobject]@{ id = 30; name = 'release-docs-site'; expired = $false;
            digest = ('sha256:' + ('e' * 64)); created_at = '2026-09-17T00:01:00Z';
            workflow_run = [pscustomobject]@{id = 10; head_sha = $script:state.Head} })
        $script:state.Python = (Get-Command python -CommandType Application -ErrorAction Stop).Source
        Copy-Item (Join-Path $PSScriptRoot '../scripts/cg_pr_preflight.py') (Join-Path $script:fixture 'scripts/cg_pr_preflight.py')
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
                ' symbolic-ref --quiet --short HEAD$' {
                    if (-not $script:state.CurrentBranch) { $global:LASTEXITCODE = 1; return }
                    return $script:state.CurrentBranch
                }
                ' check-ref-format ' { return }
                ' rev-parse --verify HEAD\^\{tree\}' { return $script:state.Tree }
                ' rev-parse --verify HEAD' { return $script:state.Head }
                ' rev-parse --verify origin/' { return $script:state.Tip }
                ' rev-parse --verify .*\^\{commit\}' { return $script:state.Head }
                ' rev-parse --verify refs/tags/' { return $script:state.Object }
                ' tag --list ' { return $script:state.Tag }
                ' cat-file -t ' { return $script:state.TagType }
                ' ls-remote --heads ' {
                    if (-not $script:state.SourceBranchExists) { return }
                    return "$($script:state.Tip)`t$($args[-1])"
                }
                ' ls-remote --tags ' {
                    if ($script:state.Remote) {
                        return @("$($script:state.RemoteObject)`trefs/tags/$($script:state.Tag)", "$($script:state.RemoteCommit)`trefs/tags/$($script:state.Tag)^{}")
                    }
                    return
                }
                ' status --porcelain ' { return $script:state.Dirty }
                ' merge-base --is-ancestor origin/main ' {
                    $global:LASTEXITCODE = $script:state.MainAncestorExit
                    return
                }
                ' show [0-9a-f]{40}:\.github/workflows/release-docs\.yml$' {
                    $global:LASTEXITCODE = $script:state.WorkflowReadExit
                    return $script:state.Producer
                }
                ' show [0-9a-f]{40}:\.github/workflows/release-pages\.yml$' {
                    $global:LASTEXITCODE = $script:state.WorkflowReadExit
                    return $script:state.Controller
                }
                ' push origin ' {
                    if ($script:state.RevokeSourceAfterPush) { $script:state.ProductionBranches = @() }
                    if ($script:state.CutoverAfterPush) { $script:state.PolicyEnabled = $true; $script:state.PolicySha = ('e' * 40) }
                    if ($script:state.PushMode -ne 'absent') { $script:state.Remote = $true }
                    if ($script:state.PushMode -ne 'success') { $global:LASTEXITCODE = 1; throw "uncertain push" }
                    return
                }
                ' merge-base --is-ancestor ' { $global:LASTEXITCODE = $script:state.SourceAncestorExit; return }
                ' fetch origin | clone --quiet | config core\.| checkout --detach ' { return }
                default { throw "Unmocked git call blocked: $call" }
            }
        }
        function global:python3 {
            $script:state = $global:CgReleaseTestState
            $global:LASTEXITCODE = 0
            if ($args[0] -eq '--version') { return 'Python 3.11.0' }
            $call = $args -join ' '
            $script:state.Calls.Add("python $call")
            if ($call -match 'cg_pr_preflight.py') {
                if ($args -contains '--verify-receipt') {
                    & $script:state.Python @args
                    $global:LASTEXITCODE = $LASTEXITCODE
                    return
                }
                $global:LASTEXITCODE = $script:state.PreflightExit
                return
            }
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
        Mock Start-Sleep { }
        Mock Invoke-RestMethod {
            param($Uri, $Method, $Headers, $Body)
            $script:state = $global:CgReleaseTestState
            $script:expected = $global:CgReleaseTestExpected
            $script:state.Calls.Add("api $Method $Uri")
            if ($Uri -ceq 'https://api.github.com/repos/GPID-WB/compound-gpid') {
                return [pscustomobject]@{ id = 123; full_name = 'GPID-WB/compound-gpid'; default_branch = $script:state.Default; fork = $false }
            }
            if ($Uri -match '/branches/production$') {
                return [pscustomobject]@{ name = 'production'; protected = $script:state.Protected; commit = [pscustomobject]@{ sha = $script:state.PolicySha } }
            }
            if ($Uri -match '/branches/production/protection$') {
                # The classic branch-protection endpoint reports 404 when only
                # repository rulesets protect the default branch and must not
                # be read by the legacy authority gate.
                throw 'classic branch protection endpoint must not be read'
            }
            if ($Uri -ceq "https://api.github.com/repos/GPID-WB/compound-gpid/contents/.release-controller.json?ref=$($script:state.PolicySha)") {
                $json = @{ enabled = $script:state.PolicyEnabled; production_branches = $script:state.ProductionBranches } | ConvertTo-Json -Compress
                if ($null -ne $script:state.PolicyJson) { $json = $script:state.PolicyJson }
                return [pscustomobject]@{ type='file'; encoding='base64'; content=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($json)) }
            }
            if ($Uri -match '/contents/\.github/release-recovery/') { return $script:state.RecoveryRecord }
            if ($Uri -ceq 'https://api.github.com/user') { return [pscustomobject]@{ id=7; login='maintainer' } }
            if ($Uri -match '/collaborators/maintainer/permission$') {
                return [pscustomobject]@{ role_name=$script:state.Role; permission=$(if ($script:state.Role -eq 'admin') {'admin'} else {'write'}); user=@{id=7} }
            }
            if ($Uri -match '/rulesets$') {
                return @(
                    [pscustomobject]@{ id = 1; name = 'Protect release tags'; target = 'tag'; enforcement = 'active' },
                    [pscustomobject]@{ id = 2; name = 'Restrict release tag creation'; target = 'tag'; enforcement = 'active' },
                    [pscustomobject]@{ id = 3; name = 'Protect dev'; target = 'branch'; enforcement = 'active' },
                    [pscustomobject]@{ id = 4; name = 'Protect main'; target = 'branch'; enforcement = 'active' }
                )
            }
            if ($Uri -match '/rulesets/([1234])$') {
                $id = $Matches[1]
                $types = @('update', 'deletion', 'non_fast_forward'); $include = 'refs/tags/v*'; $bypass = @(); $canBypass = 'never'
                if ($id -eq '2') { $types = @('creation'); $bypass = @([pscustomobject]@{ actor_type = 'RepositoryRole'; actor_id = 5; bypass_mode = 'always' }) }
                if ($id -eq '3') { $include = 'refs/heads/dev' }
                if ($id -eq '4') {
                    $types = @('deletion', 'non_fast_forward', 'pull_request', 'required_status_checks')
                    $include = '~DEFAULT_BRANCH'
                    $bypass = @([pscustomobject]@{ actor_type = 'RepositoryRole'; actor_id = 5; bypass_mode = 'always' })
                    $canBypass = 'always'
                    if ($script:state.BadRuleset) { $types = @('deletion', 'non_fast_forward', 'required_status_checks') }
                }
                return [pscustomobject]@{
                    rules = @($types | ForEach-Object { [pscustomobject]@{ type = $_ } })
                    conditions = [pscustomobject]@{ ref_name = [pscustomobject]@{ include = @($include); exclude = @() } }
                    bypass_actors = $bypass; current_user_can_bypass = $canBypass
                }
            }
            if ($Uri -match '/releases\?') {
                # Invoke-RestMethod emits the JSON array as one pipeline object.
                if ($script:state.DraftOnly) { $draft = $script:expected.PSObject.Copy(); $draft.draft = $true; return ,@($draft) }
                if ($script:state.Duplicate) { return ,@($script:expected, $script:expected) }
                if ($null -ne $script:state.Release) { return ,@($script:state.ListExtras + @($script:state.Release)) }
                return ,@($script:state.ListExtras)
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
                $run = [pscustomobject]@{ id = 10; run_attempt = $script:state.BuildAttempt; head_sha = $script:state.Head; head_branch = $script:state.Tag; event = 'push'; path = '.github/workflows/release-docs.yml'; status = 'completed'; conclusion = $script:state.DocsStatus }
                if ($script:state.BadChain) { $run.head_sha = ('c' * 40) }
                if ($Uri -match 'actions/runs/10$') { return $run }
                return [pscustomobject]@{ workflow_runs = @($run) }
            }
            if ($Uri -match 'release-pages.yml/runs|actions/runs/20$') {
                $run = [pscustomobject]@{ id = 20; name = $script:state.PagesName; display_title = $script:state.PagesName; event = $script:state.PagesEvent; path = $script:state.PagesPath; status = 'completed'; conclusion = $script:state.PagesStatus; head_sha = ('d' * 40); head_branch = $(if ($script:state.BadDefaultRef) {'other'} else {'production'}); run_attempt = 1 }
                if ($Uri -match 'actions/runs/20$') { return $run }
                return [pscustomobject]@{ workflow_runs = @($run) }
            }
            if ($Uri -match '/actions/artifacts/30$') {
                if ($script:state.WithdrawAfterArtifact) { $script:state.RecoveryRecord = $null }
                return [pscustomobject]@{ id=30; name='release-docs-site'; workflow_run=@{id=10;head_sha=$script:state.Head}; digest=$script:state.ArtifactDigest; expired=$false }
            }
            if ($Uri -match '/actions/runs/10/attempts/[0-9]+/jobs\?') {
                return [pscustomobject]@{total_count = $script:state.BuildJobs.Count; jobs = $script:state.BuildJobs}
            }
            if ($Uri -match '/actions/runs/10/artifacts\?') {
                return [pscustomobject]@{total_count = $script:state.BuildArtifacts.Count; artifacts = $script:state.BuildArtifacts}
            }
            if ($Uri -match '/actions/runs/20/attempts/1/jobs\?') {
                return [pscustomobject]@{ total_count=1; jobs=@([pscustomobject]@{id=40;run_id=20;run_attempt=1;name='deploy';html_url='https://github.com/GPID-WB/compound-gpid/actions/runs/20/job/40';status='completed';conclusion=$(if ($script:state.BadDeployJob) {'skipped'} else {'success'});steps=@(@{name='Deploy to GitHub Pages';conclusion='success'})}) }
            }
            if ($Uri -match '/deployments\?') { return ,@([pscustomobject]@{id=50;sha=('d'*40);ref='production';environment='github-pages'}) }
            if ($Uri -match '/deployments/50/statuses\?') { return ,@([pscustomobject]@{state=$(if ($script:state.BadDeployment) {'failure'} else {'success'});log_url='https://github.com/GPID-WB/compound-gpid/actions/runs/20/job/40';environment='github-pages'}) }
            throw "Unmocked HTTP call blocked: $Method $Uri"
        }
        function Invoke-FixtureRelease {
            param([string]$Phase = 'Reserve', [switch]$ExactRuns, [switch]$BuildOnly, [switch]$Timing, [string]$Operation = 'Bridge', [string]$PreflightReceipt, [string]$SourceBranch)
            $parameters = @{ Tag = $script:state.Tag; Name = $script:expected.name; NotesFile = (Join-Path $script:fixture 'notes.md'); Phase = $Phase; LegacyOperation = $Operation }
            if ($ExactRuns) { $parameters.BuildRunId = 10; $parameters.PagesRunId = 20 }
            if ($BuildOnly) { $parameters.BuildRunId = 10 }
            if ($Timing) { $parameters.Timing = $true }
            if ($PreflightReceipt) { $parameters.PreflightReceipt = $PreflightReceipt }
            if ($SourceBranch) { $parameters.SourceBranch = $SourceBranch }
            & (Join-Path $script:fixture 'create-release.ps1') @parameters
        }
        function Set-FixtureRecoveryRecord {
            param([string]$SchemaJson = '1')
            $record = @{schema_version=1;repository_id=123;tag=$script:state.Tag;tag_object=$script:state.Object;release_sha=$script:state.Head;actor_ids=@(7);reason='Reviewed offline historical fixture';build_run_id=10;artifact_id=30;artifact_digest=('sha256:' + ('e' * 64))}
            $raw = $record | ConvertTo-Json -Compress
            $raw = $raw -replace '"schema_version":1(?=[,}])', ('"schema_version":' + $SchemaJson)
            $script:state.RecoveryRecord = [pscustomobject]@{type='file';encoding='base64';content=[Convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes($raw))}
        }
        function Set-FixtureStable {
            $script:state.CurrentBranch = 'main'
            Remove-Item (Join-Path $script:fixture 'releases/v1.2.0.9015.json')
            $script:state.Tag = 'v1.2.0'
            $script:expected.tag_name = 'v1.2.0'; $script:expected.name = 'v1.2.0 - Pairing'
            $script:expected.html_url = 'https://github.com/GPID-WB/compound-gpid/releases/tag/v1.2.0'
            $script:expected.prerelease = $false
            @{ tag = $script:state.Tag; name = $script:expected.name; url = $script:expected.html_url; publishedAt = '2026-09-10T00:00:00Z' } |
                ConvertTo-Json | Set-Content (Join-Path $script:fixture 'releases/v1.2.0.json')
        }
        function New-FixtureReceipt {
            param([string]$Case = 'valid')
            $path = Join-Path $TestDrive ('receipt-' + [guid]::NewGuid().ToString('N') + '.json')
            # Use real Python for the cross-language wire format; no gate or network calls.
            $code = @'
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
import cg_pr_preflight as p
commands = p.selected_native_commands(p.full_gate_selection(), Path('.'))
data = dict(schema_version=1, commit_sha='a'*40, tree_sha='c'*40,
            line_ending_provenance={'core.autocrlf':'false','core.eol':'lf'},
            timestamp='2026-09-17T00:00:00+00:00',
            commands=[list(c) for c in commands], exit_codes=[0]*len(commands))
case = sys.argv[3]
if case == 'commit': data['commit_sha'] = 'e'*40
if case == 'tree': data['tree_sha'] = 'e'*40
if case == 'non-lf': data['line_ending_provenance']['core.eol'] = 'crlf'
if case == 'failed-command': data['exit_codes'][0] = 1
if case == 'partial': data['commands'] = data['commands'][:-1]
if case == 'other-python':
    for command in data['commands']:
        if command[0] == sys.executable: command[0] = str(Path(sys.executable).parent / 'another-venv' / 'python.exe')
data['digest'] = hashlib.sha256(json.dumps(data, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode()).hexdigest()
if case == 'digest': data['digest'] = 'f'*64
Path(sys.argv[2]).write_text('{' if case == 'malformed' else json.dumps(data), encoding='utf-8')
'@
            & $script:state.Python -c $code (Join-Path $script:fixture 'scripts') $path $Case
            if ($LASTEXITCODE -ne 0) { throw 'Receipt fixture generation failed.' }
            return $path
        }
    }
    AfterEach {
        @($script:state.Calls | Where-Object { $_ -match '^api (Delete|Patch) ' }).Count | Should -Be 0
        Remove-Item Function:\git, Function:\python3, Function:\Invoke-CgFixtureNode -Force -ErrorAction SilentlyContinue
        Remove-Variable CgReleaseTestState, CgReleaseTestExpected -Scope Global -ErrorAction SilentlyContinue
        $global:LASTEXITCODE = 0
    }

    It 'does not emit timing unless explicitly enabled' {
        $writer = [System.IO.StringWriter]::new()
        $previous = [Console]::Error
        try {
            [Console]::SetError($writer)
            Invoke-FixtureRelease
        } finally { [Console]::SetError($previous) }
        $writer.ToString() | Should -Not -Match '"kind":"timing"'
        $writer.Dispose()
    }
    It 'publishes a prerelease from verified source branch <Branch>' -TestCases @(
        @{ Branch = 'dev' }, @{ Branch = 'feature/release-test' }, @{ Branch = 'production' }
    ) {
        param($Branch)
        Invoke-FixtureRelease -SourceBranch $Branch
        $script:state.Release.prerelease | Should -Be $true
        ($script:state.Calls -join "`n") | Should -Match ([regex]::Escape("ls-remote --heads origin refs/heads/$Branch"))
    }
    It 'publishes stable only from an authorized source branch <Branch>' -TestCases @(
        @{ Branch = 'production' }, @{ Branch = 'deploy/1.x' }
    ) {
        param($Branch)
        Set-FixtureStable
        $script:state.ProductionBranches = @('deploy/1.x')
        Invoke-FixtureRelease -SourceBranch $Branch
        $script:state.Release.prerelease | Should -Be $false
        ($script:state.Calls -join "`n") | Should -Match ([regex]::Escape("ls-remote --heads origin refs/heads/$Branch"))
    }
    It 'rejects stable feature source even when its commit also exists on main' {
        Set-FixtureStable
        { Invoke-FixtureRelease -SourceBranch 'feature/release-test' } | Should -Throw 'Stable release source branch'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rechecks deployment branch authorization before Release POST after tag push' {
        Set-FixtureStable
        $script:state.RevokeSourceAfterPush = $true
        { Invoke-FixtureRelease -SourceBranch 'main' } | Should -Throw 'Stable release source branch'
        $script:state.Remote | Should -Be $true
        ($script:state.Calls -join "`n") | Should -Not -Match 'api Post'
    }
    It 'rejects unsafe source branch <Branch> before remote effects' -TestCases @(
        @{ Branch = '../bad' }, @{ Branch = '--all' }, @{ Branch = 'bad name' },
        @{ Branch = 'branch@{1}' }, @{ Branch = 'branch.lock' }
    ) {
        param($Branch)
        { Invoke-FixtureRelease -SourceBranch $Branch } | Should -Throw 'Invalid release source branch name'
        ($script:state.Calls -join "`n") | Should -Not -Match 'fetch origin|push origin|api Post'
    }
    It 'requires an explicit source branch for a detached release checkout' {
        $script:state.CurrentBranch = $null
        { Invoke-FixtureRelease } | Should -Throw 'SourceBranch'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'accepts an explicit verified source branch in a detached checkout' {
        $script:state.CurrentBranch = $null
        Invoke-FixtureRelease -SourceBranch 'feature/release-test'
        $script:state.Release.id | Should -Be 123
    }
    It 'rejects a source branch absent from the canonical remote' {
        $script:state.SourceBranchExists = $false
        { Invoke-FixtureRelease -SourceBranch 'feature/missing' } | Should -Throw 'remote release branch'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects a new tag not at the exact selected source tip' {
        $script:state.Tip = ('f' * 40)
        { Invoke-FixtureRelease -SourceBranch 'feature/release-test' } | Should -Throw 'exact current origin/feature/release-test'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects resumed prerelease outside selected source lineage' {
        $script:state.Remote = $true; $script:state.Release = $script:expected
        $script:state.SourceAncestorExit = 1
        { Invoke-FixtureRelease -Phase Finalize -BuildOnly -SourceBranch 'feature/release-test' } | Should -Throw 'Release lineage mismatch'
        ($script:state.Calls -join "`n") | Should -Not -Match 'cg_release_attestation.py|push origin|api Post'
    }
    It 'rejects malformed remote production branch policy <Policy>' -TestCases @(
        @{ Policy = '{"enabled":false,"production_branches":"feature/release-test"}' },
        @{ Policy = '{"enabled":false,"production_branches":[null]}' },
        @{ Policy = '{"enabled":false,"production_branches":["../bad"]}' },
        @{ Policy = '{"enabled":false,"production_branches":["main"],"production_branches":["feature/release-test"]}' }
    ) {
        param($Policy)
        Set-FixtureStable
        $script:state.PolicyJson = $Policy
        { Invoke-FixtureRelease -SourceBranch 'feature/release-test' } | Should -Throw 'production_branches'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'checks stable docs layout against exact protected default before the tag push' {
        Set-FixtureStable
        Invoke-FixtureRelease
        $calls = $script:state.Calls -join "`n"
        $calls | Should -Not -Match 'merge-base --is-ancestor origin/main'
        $calls | Should -Match 'show a{40}:\.github/workflows/release-docs.yml'
        $calls | Should -Match 'show d{40}:\.github/workflows/release-pages.yml'
        $calls.IndexOf(':.github/workflows/release-pages.yml') | Should -BeLessThan $calls.IndexOf('push origin')
    }
    It 'halts stable publication when the controller accepts only the old site layout' {
        Set-FixtureStable
        $script:state.Controller = $script:state.Controller.Replace('process.env.ISOLATED_RELEASE === "true" ? "docs" : "site"', '"site"')
        { Invoke-FixtureRelease } | Should -Throw 'sync the protected controller on production first'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects controller contract drift in <Old>' -TestCases @(
        @{ Old = '.docs-build-metadata.json'; New = '.other-metadata.json' },
        @{ Old = 'path: release-artifact'; New = 'path: other-artifact' },
        @{ Old = "ISOLATED_RELEASE: `${{ steps.authority.outputs.dev_artifact_id != '' }}"; New = 'ISOLATED_RELEASE: false' }
    ) {
        param($Old, $New)
        Set-FixtureStable
        $script:state.Controller = $script:state.Controller.Replace($Old, $New)
        { Invoke-FixtureRelease } | Should -Throw 'sync the protected controller on production first'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'does not force configured stable source to contain the protected default tip' {
        Set-FixtureStable
        $script:state.Remote = $true
        $script:state.MainAncestorExit = 1
        Invoke-FixtureRelease
        $script:state.Release.prerelease | Should -Be $false
        ($script:state.Calls -join "`n") | Should -Not -Match 'merge-base --is-ancestor origin/main'
        ($script:state.Calls -join "`n") | Should -Match 'show d{40}:\.github/workflows/release-pages.yml'
    }
    It 'rejects extraction and composition path drift in <Old>' -TestCases @(
        @{ Old = 'path: release-dev-artifact'; New = 'path: other-dev-artifact' },
        @{ Old = 'import-dev current-dev release-dev-artifact'; New = 'import-dev current-dev other-dev-artifact' },
        @{ Old = 'import-docs release-source release-artifact'; New = 'import-docs release-source other-artifact' },
        @{ Old = 'import-docs release-source release-artifact verified-staging/release'; New = 'import-docs release-source release-artifact other-staging/release' },
        @{ Old = 'import-dev current-dev release-dev-artifact verified-staging/dev'; New = 'import-dev current-dev release-dev-artifact other-staging/dev' },
        @{ Old = '--main-build verified-staging/release --dev-build verified-staging/dev'; New = '--main-build verified-staging/dev --dev-build verified-staging/release' },
        @{ Old = ' import-docs release-source release-artifact verified-staging/release'; New = ' import-docs release-source release-artifact' },
        @{ Old = '--out composed-artifact'; New = '--out other-composition' },
        @{ Old = 'mv composed-artifact release-artifact'; New = 'mv composed-artifact other-artifact' },
        @{ Old = 'path: release-artifact/site'; New = 'path: release-artifact/docs' },
        @{ Old = 'path: current-dev'; New = 'path: other-dev' },
        @{ Old = 'path: release-source'; New = 'path: other-source' }
    ) {
        param($Old, $New)
        Set-FixtureStable
        $original = $script:state.Controller
        $script:state.Controller = $original.Replace($Old, $New)
        $script:state.Controller | Should -Not -BeExactly $original
        { Invoke-FixtureRelease } | Should -Throw 'sync the protected controller on production first'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects a sealing step that drops the existing recovery token' {
        Set-FixtureStable
        $pattern = '(?ms)^      - name: Seal durable official snapshot in the Pages artifact\r?\n.*?(?=^      - |\z)'
        $block = [regex]::Match($script:state.Controller, $pattern).Value
        $block.Length | Should -BeGreaterThan 0
        $changed = $block.Replace('steps.recovery-authority.outputs.token || github.token', 'github.token')
        $changed | Should -Not -Be $block
        $script:state.Controller = $script:state.Controller.Replace($block, $changed)
        { Invoke-FixtureRelease } | Should -Throw "step 'Seal durable official snapshot in the Pages artifact'"
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects <Mutation> controller step <Step>' -TestCases @(
        @{ Step = 'Download isolated dev documentation'; Mutation = 'missing' },
        @{ Step = 'Download isolated dev documentation'; Mutation = 'skipped' },
        @{ Step = 'Compose isolated producer artifacts with protected code'; Mutation = 'missing' },
        @{ Step = 'Compose isolated producer artifacts with protected code'; Mutation = 'skipped' },
        @{ Step = 'Seal durable official snapshot in the Pages artifact'; Mutation = 'missing' },
        @{ Step = 'Seal durable official snapshot in the Pages artifact'; Mutation = 'skipped' },
        @{ Step = 'Upload verified release Pages artifact'; Mutation = 'missing' },
        @{ Step = 'Upload verified release Pages artifact'; Mutation = 'skipped' }
    ) {
        param($Step, $Mutation)
        Set-FixtureStable
        $pattern = '(?ms)^      - name: ' + [regex]::Escape($Step) + '\r?\n.*?(?=^      - |\z)'
        $block = [regex]::Match($script:state.Controller, $pattern).Value
        $block | Should -Not -BeNullOrEmpty
        $replacement = ''
        if ($Mutation -eq 'skipped') {
            $replacement = $block.Replace("if: steps.authority.outputs.dev_artifact_id != ''", 'if: false')
            if ($replacement -ceq $block) {
                $replacement = $block.Replace("- name: $Step", "- name: $Step`n        if: false")
            }
        }
        $script:state.Controller = $script:state.Controller.Replace($block, $replacement)
        { Invoke-FixtureRelease } | Should -Throw 'sync the protected controller on production first'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects composition moved before artifact extraction' {
        Set-FixtureStable
        $pattern = '(?ms)^      - name: Compose isolated producer artifacts with protected code\r?\n.*?(?=^      - |\z)'
        $block = [regex]::Match($script:state.Controller, $pattern).Value
        $block | Should -Not -BeNullOrEmpty
        $script:state.Controller = $script:state.Controller.Replace($block, '').Replace(
            '      - name: Download isolated dev documentation', $block + '      - name: Download isolated dev documentation')
        { Invoke-FixtureRelease } | Should -Throw 'out of extraction/composition order'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'fails closed when exact workflow content cannot be read' {
        Set-FixtureStable
        $script:state.WorkflowReadExit = 128
        { Invoke-FixtureRelease } | Should -Throw 'release-docs.yml'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects stable producer metadata or upload layout drift' -TestCases @(
        @{ Old = 'docs/'; New = 'other/' },
        @{ Old = '.docs-build-metadata.json'; New = '.other-metadata.json' },
        @{ Old = 'include-hidden-files: true'; New = 'include-hidden-files: false' }
    ) {
        param($Old, $New)
        Set-FixtureStable
        $script:state.Producer = $script:state.Producer.Replace($Old, $New)
        { Invoke-FixtureRelease } | Should -Throw 'release-docs.yml'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'skips main-tip and docs-contract checks for prereleases' {
        $script:state.MainAncestorExit = 1
        $script:state.WorkflowReadExit = 128
        Invoke-FixtureRelease
        ($script:state.Calls -join "`n") | Should -Not -Match 'merge-base --is-ancestor origin/main| show .*release-(docs|pages)\.yml'
        $script:state.Release.id | Should -Be 123
    }
    It 'falls back to the full gate for a missing receipt' {
        Invoke-FixtureRelease -PreflightReceipt (Join-Path $TestDrive 'missing-receipt.json')
        ($script:state.Calls -join "`n") | Should -Match 'clone --quiet'
        ($script:state.Calls -join "`n") | Should -Match '--phase committed --full-gate --run-native-target'
    }
    It 'reuses exact successful LF receipt evidence in <Phase>' -TestCases @(
        @{ Phase = 'Reserve' }, @{ Phase = 'Finalize' }
    ) {
        param($Phase)
        if ($Phase -eq 'Finalize') { $script:state.Remote = $true; $script:state.Release = $script:expected }
        $receipt = New-FixtureReceipt
        Invoke-FixtureRelease -Phase $Phase -PreflightReceipt $receipt
        ($script:state.Calls -join "`n") | Should -Match '--verify-receipt'
        ($script:state.Calls -join "`n") | Should -Not -Match 'clone --quiet|--run-native-target'
        Get-Content (Join-Path $script:fixture 'release-result.txt') | Should -Match '^(CREATED|FINALIZED)\|'
    }
    It 'runs the full gate for invalid receipt <Case>' -TestCases @(
        @{ Case = 'commit' }, @{ Case = 'tree' }, @{ Case = 'non-lf' },
        @{ Case = 'digest' }, @{ Case = 'malformed' }, @{ Case = 'partial' },
        @{ Case = 'failed-command' }
    ) {
        param($Case)
        $receipt = New-FixtureReceipt -Case $Case
        Invoke-FixtureRelease -PreflightReceipt $receipt
        ($script:state.Calls -join "`n") | Should -Match 'clone --quiet'
        ($script:state.Calls -join "`n") | Should -Match '--phase committed --full-gate --run-native-target'
    }
    It 'keeps the clean checkout guard even with a valid receipt' {
        $receipt = New-FixtureReceipt
        $script:state.Dirty = @(' M create-release.ps1')
        { Invoke-FixtureRelease -PreflightReceipt $receipt } | Should -Throw 'Release checkout must be clean'
        ($script:state.Calls -join "`n") | Should -Not -Match '--verify-receipt|credential fill|push origin|api Post'
    }
    It 'accepts the same logical gate from a different Python executable path' {
        $receipt = New-FixtureReceipt -Case 'other-python'
        Invoke-FixtureRelease -PreflightReceipt $receipt
        ($script:state.Calls -join "`n") | Should -Match '--verify-receipt'
        ($script:state.Calls -join "`n") | Should -Not -Match 'clone --quiet|--run-native-target|another-venv'
    }
    It 'keeps the current remote tip guard even with a valid receipt' {
        $receipt = New-FixtureReceipt
        $script:state.Tip = ('e' * 40)
        { Invoke-FixtureRelease -PreflightReceipt $receipt } | Should -Throw 'exact current origin/dev'
        ($script:state.Calls -join "`n") | Should -Not -Match '--verify-receipt|credential fill|push origin|api Post'
    }
    It 'retains the full gate when no receipt is supplied' {
        Invoke-FixtureRelease
        ($script:state.Calls -join "`n") | Should -Match 'clone --quiet'
        ($script:state.Calls -join "`n") | Should -Match '--phase committed --full-gate --run-native-target'
    }
    It 'does not publish when the missing-receipt fallback gate fails' {
        $script:state.PreflightExit = 7
        { Invoke-FixtureRelease -PreflightReceipt (Join-Path $TestDrive 'missing-receipt.json') } |
            Should -Throw 'preflight failed with exit code 7'
        ($script:state.Calls -join "`n") | Should -Not -Match 'credential fill|push origin|api Post'
    }
    It 'rejects routine new publication through Recovery before any write' {
        { Invoke-FixtureRelease -Operation Recovery } | Should -Throw 'Explicit reviewed historical recovery authority is required; routine new publication is forbidden.'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'reads cutover from the protected remote default, not absent local policy or main' {
        $script:state.PolicyEnabled = $true
        { Invoke-FixtureRelease } | Should -Throw 'Legacy Bridge is disabled after remote controller cutover or with invalid policy.'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
        ($script:state.Calls -join "`n") | Should -Match '/contents/\.release-controller.json\?ref=d{40}'
    }
    It 'rejects an unprotected default before any legacy write' {
        $script:state.Protected = $false
        { Invoke-FixtureRelease } | Should -Throw 'Legacy authority requires the protected remote default branch.'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects a weakened default-branch ruleset before any legacy write' {
        $script:state.BadRuleset = $true
        { Invoke-FixtureRelease } | Should -Throw 'Legacy protected-default review authority is insufficient.'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'never reads the classic branch protection endpoint' {
        Invoke-FixtureRelease
        ($script:state.Calls -join "`n") | Should -Not -Match '/branches/production/protection'
    }
    It 'rechecks cutover after a tag push before Release creation' {
        $script:state.CutoverAfterPush = $true
        { Invoke-FixtureRelease } | Should -Throw 'Legacy Bridge is disabled after remote controller cutover or with invalid policy.'
        $script:state.Remote | Should -Be $true
        ($script:state.Calls -join "`n") | Should -Not -Match 'api Post'
    }
    It 'allows current maintainer recovery of the exact stranded remote tag after cutover' {
        $script:state.Remote = $true; $script:state.PolicyEnabled = $true
        Invoke-FixtureRelease -Operation Recovery
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin'
        $script:state.Release.id | Should -Be 123
    }
    It 'rejects revoked historical recovery authority before Release creation' {
        $script:state.Remote = $true; $script:state.Role = 'read'
        { Invoke-FixtureRelease -Operation Recovery } | Should -Throw 'Current maintainer authority is required for legacy publication.'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'requires the exact reviewed historical record to recover an absent remote tag' {
        Set-FixtureRecoveryRecord
        $script:state.PolicyEnabled = $true
        Invoke-FixtureRelease -Operation Recovery
        $script:state.Remote | Should -Be $true
        $script:state.Release.id | Should -Be 123
    }
    It 'accepts the Int64 schema representation without changing reviewed authority' {
        Set-FixtureRecoveryRecord
        $script:state.PolicyEnabled = $true
        Mock ConvertFrom-Json -ParameterFilter { $InputObject -match '"schema_version":1[,}]' -and $InputObject -match '"tag_object"' } {
            $parser = Get-Command ConvertFrom-Json -CommandType Cmdlet
            $record = & $parser -InputObject $InputObject
            $record.schema_version = [long]1
            return $record
        }
        Invoke-FixtureRelease -Operation Recovery
        Assert-MockCalled ConvertFrom-Json -Times 1 -Scope It
        $script:state.Remote | Should -Be $true
        $script:state.Release.id | Should -Be 123
    }
    It 'rejects invalid historical schema <SchemaJson> before any effect' -TestCases @(
        @{ SchemaJson = 'true' }, @{ SchemaJson = '"1"' }, @{ SchemaJson = '1.0' },
        @{ SchemaJson = '1.5' }, @{ SchemaJson = 'null' }, @{ SchemaJson = '0' },
        @{ SchemaJson = '2' }, @{ SchemaJson = '2147483648' }
    ) {
        param($SchemaJson)
        Set-FixtureRecoveryRecord -SchemaJson $SchemaJson
        $script:state.PolicyEnabled = $true
        { Invoke-FixtureRelease -Operation Recovery } | Should -Throw 'Explicit reviewed historical recovery authority'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post|cg_release_attestation.py'
    }
    It 'finalizes the exact reviewed historical manual deployment after cutover' {
        Set-FixtureStable
        $script:state.Remote=$true; $script:state.Release=$script:expected; $script:state.PolicyEnabled=$true
        $script:state.PagesEvent='workflow_dispatch'
        Set-FixtureRecoveryRecord
        Invoke-FixtureRelease -Operation Recovery -Phase Finalize -ExactRuns
        Get-Content (Join-Path $script:fixture 'release-result.txt') | Should -Match '^FINALIZED\|'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'rejects a substituted historical artifact before attestation effects' {
        Set-FixtureStable
        $script:state.Remote=$true; $script:state.Release=$script:expected; $script:state.PolicyEnabled=$true
        $script:state.PagesEvent='workflow_dispatch'; $script:state.ArtifactDigest=('sha256:' + ('f' * 64))
        Set-FixtureRecoveryRecord
        { Invoke-FixtureRelease -Operation Recovery -Phase Finalize -ExactRuns } | Should -Throw 'Historical recovery deployment does not bind the exact immutable build and artifact.'
        ($script:state.Calls -join "`n") | Should -Not -Match 'cg_release_attestation.py|push origin|api Post'
    }
    It 'rejects withdrawal of the historical grant after artifact validation' {
        Set-FixtureStable
        $script:state.Remote=$true; $script:state.Release=$script:expected; $script:state.PolicyEnabled=$true
        $script:state.PagesEvent='workflow_dispatch'; $script:state.WithdrawAfterArtifact=$true
        Set-FixtureRecoveryRecord
        { Invoke-FixtureRelease -Operation Recovery -Phase Finalize -ExactRuns } | Should -Throw 'historical recovery authority'
        ($script:state.Calls -join "`n") | Should -Not -Match 'cg_release_attestation.py'
    }
    It 'rejects an all-skipped deployment wrapper on another default ref' {
        Set-FixtureStable
        $script:state.Remote=$true; $script:state.Release=$script:expected; $script:state.BadDefaultRef=$true
        { Invoke-FixtureRelease -Phase Finalize -ExactRuns } | Should -Throw 'protected default'
    }
    It 'rejects a successful wrapper with a skipped protected deploy job' {
        Set-FixtureStable
        $script:state.Remote=$true; $script:state.Release=$script:expected; $script:state.BadDeployJob=$true
        { Invoke-FixtureRelease -Phase Finalize -ExactRuns } | Should -Throw 'protected deploy job'
    }
    It 'rejects a successful wrapper without successful deployment evidence' {
        Set-FixtureStable
        $script:state.Remote=$true; $script:state.Release=$script:expected; $script:state.BadDeployment=$true
        { Invoke-FixtureRelease -Phase Finalize -ExactRuns } | Should -Throw 'deployment result'
    }
    It 'emits opt-in gate and publication spans without changing authority order' {
        $writer = [System.IO.StringWriter]::new()
        $previous = [Console]::Error
        try {
            [Console]::SetError($writer)
            Invoke-FixtureRelease -Timing
        } finally { [Console]::SetError($previous) }
        $raw = $writer.ToString()
        $rows = @($raw -split '\r?\n' | Where-Object { $_ -match '^\{' } | ForEach-Object { $_ | ConvertFrom-Json })
        @($rows | Where-Object { $_.stage -eq 'gates' -and $_.outcome -eq 'complete' }).Count | Should -Be 1
        @($rows | Where-Object { $_.stage -eq 'publication' -and $_.outcome -eq 'complete' }).Count | Should -Be 1
        foreach ($row in $rows) {
            ($row.elapsed_seconds -ge 0) | Should -Be $true
            $row.schema_version | Should -Be 1
        }
        $raw | Should -Not -Match 'SECRET-MUST-NOT-LEAK|Authorization|Bearer|notes.md'
        $calls = $script:state.Calls -join "`n"
        $calls.IndexOf('cg_pr_preflight.py') | Should -BeLessThan $calls.IndexOf('credential fill')
        $calls.IndexOf('credential fill') | Should -BeLessThan $calls.IndexOf('push origin')
        $writer.Dispose()
    }
    It 'records interrupted gates without credential access or publication' {
        $script:state.PreflightExit = 7
        $writer = [System.IO.StringWriter]::new()
        $previous = [Console]::Error
        try {
            [Console]::SetError($writer)
            { Invoke-FixtureRelease -Timing } | Should -Throw 'preflight failed with exit code 7'
        } finally { [Console]::SetError($previous) }
        $rows = @($writer.ToString() -split '\r?\n' | Where-Object { $_ -match '^\{' } | ForEach-Object { $_ | ConvertFrom-Json })
        @($rows | Where-Object { $_.stage -eq 'gates' -and $_.outcome -eq 'interrupted' }).Count | Should -Be 1
        ($script:state.Calls -join "`n") | Should -Not -Match 'credential fill|push origin|api Post'
        $writer.Dispose()
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
    It 'accepts multiple records in a non-enumerated REST array' {
        $script:state.ListExtras = @(
            [pscustomobject]@{ tag_name = 'v1.0.0' },
            [pscustomobject]@{ tag_name = 'v1.1.0' }
        )
        Invoke-FixtureRelease
        Get-Content (Join-Path $script:fixture 'release-result.txt') | Should -Match '^CREATED\|123\|'
    }
    It 'rejects a null entry inside a non-enumerated REST array before pushing' {
        $script:state.ListExtras = @($null)
        { Invoke-FixtureRelease } | Should -Throw 'Incomplete GitHub release list'
        ($script:state.Calls -join "`n") | Should -Not -Match 'push origin|api Post'
    }
    It 'reserves a stable release from exact configured source with explicit branch identity' {
        Set-FixtureStable
        $script:state.CurrentBranch = $null
        Invoke-FixtureRelease -SourceBranch 'main'
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
    It 'finalizes a prerelease with only the exact build and no deployment reads' {
        $script:state.Remote = $true; $script:state.Release = $script:expected
        $script:state.PagesStatus = 'failure'
        Invoke-FixtureRelease -Phase Finalize -BuildOnly
        Get-Content (Join-Path $script:fixture 'release-result.txt') | Should -Match '^FINALIZED\|'
        $calls = $script:state.Calls -join "`n"
        $calls | Should -Match '/actions/runs/10'
        $calls | Should -Not -Match 'release-pages.yml/runs|/actions/runs/20|/deployments|push origin|api Post'
        $calls.LastIndexOf('cg_release_attestation.py') | Should -BeGreaterThan $calls.IndexOf('/actions/runs/10')
    }
    It 'rejects a failed exact prerelease build without reading a controller' {
        $script:state.Remote = $true; $script:state.Release = $script:expected
        $script:state.DocsStatus = 'failure'
        { Invoke-FixtureRelease -Phase Finalize -BuildOnly } | Should -Throw 'release-docs.yml'
        ($script:state.Calls -join "`n") | Should -Not -Match 'release-pages.yml/runs|/actions/runs/20|cg_release_attestation.py'
    }
    It 'rejects a green prerelease wrapper with <Failure> release build evidence' -TestCases @(
        @{Failure = 'skipped-job'}, @{Failure = 'missing-job'}, @{Failure = 'wrong-attempt'},
        @{Failure = 'wrong-sha'}, @{Failure = 'missing-step'}, @{Failure = 'skipped-step'},
        @{Failure = 'missing-artifact'}, @{Failure = 'expired-artifact'}, @{Failure = 'wrong-artifact-run'},
        @{Failure = 'wrong-artifact-sha'}, @{Failure = 'old-attempt-artifact'}, @{Failure = 'duplicate-artifact'}
        @{Failure = 'invalid-digest'}, @{Failure = 'step-order'}
    ) {
        param($Failure)
        $script:state.Remote = $true; $script:state.Release = $script:expected
        switch ($Failure) {
            'skipped-job' { $script:state.BuildJobs[0].conclusion = 'skipped' }
            'missing-job' { $script:state.BuildJobs = @([pscustomobject]@{name = 'build-dev'; conclusion = 'success'}) }
            'wrong-attempt' { $script:state.BuildAttempt = 2 }
            'wrong-sha' { $script:state.BuildJobs[0].head_sha = ('f' * 40) }
            'missing-step' { $script:state.BuildJobs[0].steps = @($script:state.BuildJobs[0].steps | Where-Object { $_.number -ne 4 }) }
            'skipped-step' { $script:state.BuildJobs[0].steps[3].conclusion = 'skipped' }
            'missing-artifact' { $script:state.BuildArtifacts = @() }
            'expired-artifact' { $script:state.BuildArtifacts[0].expired = $true }
            'wrong-artifact-run' { $script:state.BuildArtifacts[0].workflow_run.id = 99 }
            'wrong-artifact-sha' { $script:state.BuildArtifacts[0].workflow_run.head_sha = ('f' * 40) }
            'old-attempt-artifact' { $script:state.BuildArtifacts[0].created_at = '2026-09-16T00:01:00Z' }
            'duplicate-artifact' { $script:state.BuildArtifacts = @($script:state.BuildArtifacts[0], $script:state.BuildArtifacts[0]) }
            'invalid-digest' { $script:state.BuildArtifacts[0].digest = 'sha256:bad' }
            'step-order' { $script:state.BuildJobs[0].steps[3].number = 1 }
        }
        { Invoke-FixtureRelease -Phase Finalize -BuildOnly } | Should -Throw 'release-docs'
        ($script:state.Calls -join "`n") | Should -Not -Match 'release-pages.yml/runs|/actions/runs/20|cg_release_attestation.py'
    }
    It 'attests a successful exact retried build attempt without requiring Pages' {
        $script:state.Remote = $true; $script:state.Release = $script:expected
        $script:state.BuildAttempt = 2; $script:state.BuildJobs[0].run_attempt = 2
        Invoke-FixtureRelease -Phase Finalize -BuildOnly
        Get-Content (Join-Path $script:fixture 'release-result.txt') | Should -Match '^FINALIZED\|'
        ($script:state.Calls -join "`n") | Should -Match '/actions/runs/10/attempts/2/jobs'
        ($script:state.Calls -join "`n") | Should -Not -Match 'release-pages.yml/runs|/actions/runs/20'
    }
    It 'requires successful Pages for stable Finalize and leaves the pair intact' {
        Set-FixtureStable
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
        Set-FixtureStable
        $script:state.Remote = $true; $script:state.Release = $script:expected; $script:state[$Field] = $Value
        { Invoke-FixtureRelease -Phase Finalize -ExactRuns } | Should -Throw 'release-pages.yml'
        ($script:state.Calls -join "`n") | Should -Not -Match 'cg_release_attestation.py|push origin|api Post'
    }
    It 'never creates lifecycle attestation for withdrawn 9014' {
        $script:state.Tag = 'v1.2.0.9014'
        { Invoke-FixtureRelease -Phase Finalize } | Should -Throw 'not eligible for lifecycle attestation'
        $script:state.Calls.Count | Should -Be 0
    }
    It 'finalizes the exact stable chain then attests without remote mutations' {
        Set-FixtureStable
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

Describe 'create-release.ps1 - bounded read-only reservation reconciliation' {
    BeforeEach {
        $tokens = $null; $errors = $null
        $ast = [System.Management.Automation.Language.Parser]::ParseFile(
            (Join-Path $PSScriptRoot '../create-release.ps1'), [ref]$tokens, [ref]$errors)
        foreach ($functionName in @('Get-CgReleaseReservation', 'ConvertTo-CgNormalizedReleaseText')) {
            $definition = $ast.Find({ param($node)
                $node -is [System.Management.Automation.Language.FunctionDefinitionAst] -and
                $node.Name -eq $functionName
            }, $true)
            . ([scriptblock]::Create($definition.Extent.Text))
        }
        $Tag = 'v1.2.0.9015'; $Name = 'Pairing'; $headCommit = ('a' * 40)
        $recordedPayload = @{ url = 'https://example.invalid/release' }
        $script:raceRead = 0
        $script:raceMode = 'settles-present'
        $script:raceField = 'id'
        $script:raceRelease = [pscustomobject]@{
            id = 123; html_url = $recordedPayload.url; tag_name = $Tag; name = $Name
            body = 'Exact notes'; target_commitish = $headCommit; prerelease = $true
            draft = $false; published_at = '2026-09-10T00:00:00Z'
        }
        function Invoke-CgReleaseApi { param($Uri, $Method = 'Get', [switch]$AllowNotFound) }
        function Get-CgPublishedReleases { }
        function Assert-CgReleaseMetadata { param($Release, $ExpectedTag, $ExpectedName, $ExpectedCommit, $ExpectedUrl, [switch]$CheckBody) }
        Mock Invoke-CgReleaseApi {
            $script:raceRead++
            if ($script:raceMode -eq 'absent') { return $null }
            if ($script:raceMode -eq 'settles-absent' -and $script:raceRead -ge 2) { return $null }
            return $script:raceRelease
        }
        Mock Get-CgPublishedReleases {
            if ($script:raceMode -eq 'settles-fields' -or $script:raceMode -eq 'persistent-fields') {
                $listedRelease = $script:raceRelease.PSObject.Copy()
                if ($script:raceRead -eq 1 -or $script:raceMode -eq 'persistent-fields') {
                    if ($script:raceField -eq 'id') { $listedRelease.id = 456 }
                    else { $listedRelease.draft = $true }
                }
                return @{ 'v1.2.0.9015' = $listedRelease }
            }
            if ($script:raceMode -eq 'consistent' -or
                ($script:raceMode -eq 'settles-present' -and $script:raceRead -ge 2)) {
                return @{ 'v1.2.0.9015' = $script:raceRelease }
            }
            return @{}
        }
        Mock Assert-CgReleaseMetadata { }
        Mock Start-Sleep { }
    }
    It 'accepts a settled pair after re-reading both surfaces' {
        $result = Get-CgReleaseReservation -RaceAttempts 3 -RaceDelaySeconds 0
        $result.id | Should -Be 123
        Assert-MockCalled Invoke-CgReleaseApi -Times 2 -Exactly -Scope It
        Assert-MockCalled Get-CgPublishedReleases -Times 2 -Exactly -Scope It
        Assert-MockCalled Assert-CgReleaseMetadata -Times 2 -Exactly -Scope It
    }
    It 'accepts a settled absent pair without metadata checks' {
        $script:raceMode = 'settles-absent'
        $result = Get-CgReleaseReservation -RaceAttempts 3 -RaceDelaySeconds 0
        $result | Should -BeNullOrEmpty
        Assert-MockCalled Invoke-CgReleaseApi -Times 2 -Exactly -Scope It
        Assert-MockCalled Get-CgPublishedReleases -Times 2 -Exactly -Scope It
        Assert-MockCalled Assert-CgReleaseMetadata -Times 0 -Exactly -Scope It
    }
    It 'accepts two absent surfaces immediately' {
        $script:raceMode = 'absent'
        Get-CgReleaseReservation -RaceAttempts 3 -RaceDelaySeconds 0 | Should -BeNullOrEmpty
        Assert-MockCalled Invoke-CgReleaseApi -Times 1 -Exactly -Scope It
        Assert-MockCalled Get-CgPublishedReleases -Times 1 -Exactly -Scope It
        Assert-MockCalled Start-Sleep -Times 0 -Exactly -Scope It
    }
    It 'reconciles transient disagreement in <Field> before validating metadata' -TestCases @(
        @{ Field = 'id' }, @{ Field = 'draft' }
    ) {
        param($Field)
        $script:raceMode = 'settles-fields'; $script:raceField = $Field
        (Get-CgReleaseReservation -RaceAttempts 3 -RaceDelaySeconds 0).id | Should -Be 123
        Assert-MockCalled Invoke-CgReleaseApi -Times 2 -Exactly -Scope It
        Assert-MockCalled Get-CgPublishedReleases -Times 2 -Exactly -Scope It
        Assert-MockCalled Assert-CgReleaseMetadata -Times 2 -Exactly -Scope It
    }
    It 'preserves the ID conflict diagnostic after bounded reconciliation' {
        $script:raceMode = 'persistent-fields'
        { Get-CgReleaseReservation -RaceAttempts 2 -RaceDelaySeconds 0 } | Should -Throw 'Conflicting GitHub Release IDs'
        Assert-MockCalled Invoke-CgReleaseApi -Times 2 -Exactly -Scope It
        Assert-MockCalled Get-CgPublishedReleases -Times 2 -Exactly -Scope It
    }
    It 'throws the conflict only after the requested bound without remote writes' {
        $script:raceMode = 'persistent'
        { Get-CgReleaseReservation -RaceAttempts 3 -RaceDelaySeconds 0 } |
            Should -Throw 'Conflicting GitHub Release lookup and list'
        Assert-MockCalled Invoke-CgReleaseApi -Times 3 -Exactly -Scope It
        Assert-MockCalled Get-CgPublishedReleases -Times 3 -Exactly -Scope It
        # Pester records an omitted Method as null rather than the stub's Get default.
        Assert-MockCalled Invoke-CgReleaseApi -Times 0 -Exactly -Scope It -ParameterFilter { $Method -and $Method -ne 'Get' }
        Assert-MockCalled Start-Sleep -Times 0 -Exactly -Scope It
    }
    It 'returns a consistent first pair without sleeping' {
        $script:raceMode = 'consistent'
        (Get-CgReleaseReservation -RaceAttempts 3 -RaceDelaySeconds 0).id | Should -Be 123
        Assert-MockCalled Invoke-CgReleaseApi -Times 1 -Exactly -Scope It
        Assert-MockCalled Start-Sleep -Times 0 -Exactly -Scope It
    }
    It 'distinguishes explicit write methods from an omitted default GET in the mock filter' {
        $null = Invoke-CgReleaseApi -Uri 'https://example.invalid' -Method Post
        Assert-MockCalled Invoke-CgReleaseApi -Times 1 -Exactly -Scope It -ParameterFilter { $Method -and $Method -ne 'Get' }
    }
    It 'gives authorized legacy resume routes without claiming resume is read-only' {
        $script:raceMode = 'persistent'
        $message = ''
        try { Get-CgReleaseReservation -RaceAttempts 1 -RaceDelaySeconds 0 }
        catch { $message = $_.Exception.Message }
        $message | Should -Match '/cg-release --legacy-bridge --resume v1\.2\.0\.9015'
        $message | Should -Match '/cg-release --legacy-recovery --resume v1\.2\.0\.9015'
        $message | Should -Match 'Inspect the tag and Release state read-only first'
        $message | Should -Match 'only with separate authorization'
        $message | Should -Match 'Resume requires confirmation and may run Reserve or Finalize; it is not read-only'
    }
    It 'sleeps only between attempts and never after the final attempt' {
        $script:raceMode = 'persistent'
        { Get-CgReleaseReservation -RaceAttempts 3 -RaceDelaySeconds 15 } |
            Should -Throw 'Conflicting GitHub Release lookup and list'
        Assert-MockCalled Start-Sleep -Times 2 -Exactly -Scope It -ParameterFilter { $Seconds -eq 15 }
    }
    It 'uses the fast one-attempt override without sleeping' {
        $script:raceMode = 'persistent'
        { Get-CgReleaseReservation -RaceAttempts 1 -RaceDelaySeconds 0 } | Should -Throw 'Conflicting GitHub Release lookup and list'
        Assert-MockCalled Invoke-CgReleaseApi -Times 1 -Exactly -Scope It
        Assert-MockCalled Get-CgPublishedReleases -Times 1 -Exactly -Scope It
        Assert-MockCalled Start-Sleep -Times 0 -Exactly -Scope It
    }
}

Describe 'create-release.ps1 - no-fallback and classic-protection audit' {
    It 'keeps the script and prompt free of fallback publication and rollback commands' {
        foreach ($relative in @('../create-release.ps1', '../.github/prompts/cg-release.prompt.md')) {
            $content = Get-Content (Join-Path $PSScriptRoot $relative) -Raw
            $content | Should -Not -Match 'gh\s+release\s+create'
            $content | Should -Not -Match '(?i)(-Method\s+(Delete|Patch)|gh\s+api\s+[^\r\n]*(-X|--method)\s+(DELETE|PATCH))'
            $content | Should -Not -Match '/git/refs'
        }
        $scriptContent = Get-Content (Join-Path $PSScriptRoot '../create-release.ps1') -Raw
        ([regex]::Matches($scriptContent, '-Method Post -Body \$payload')).Count | Should -Be 1
        $scriptContent | Should -Match 'Assert-CgRemoteTagCommit[\s\S]*-Method Post -Body \$payload'
        $scriptContent | Should -Match 'read-only'
        $scriptContent | Should -Match 'Resume Reserve'
        $promptContent = Get-Content (Join-Path $PSScriptRoot '../.github/prompts/cg-release.prompt.md') -Raw
        $promptContent | Should -Match '--resume'
    }
    It 'does not read classic protection endpoints in the script or workflow family' {
        $paths = @((Join-Path $PSScriptRoot '../create-release.ps1'),
            (Join-Path $PSScriptRoot '../scripts/release-legacy-authority.ps1'))
        $workflowPaths = @(Get-ChildItem (Join-Path $PSScriptRoot '../.github/workflows/release-controller*.yml') | ForEach-Object { $_.FullName })
        $workflowPaths.Count | Should -BeGreaterThan 0
        $paths += $workflowPaths
        foreach ($path in $paths) {
            $content = (Get-Content $path | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
            $content | Should -Not -Match '/branches/[^\s]+/protection'
        }
    }
}
