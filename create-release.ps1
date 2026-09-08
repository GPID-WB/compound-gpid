<#
.SYNOPSIS
Creates a GitHub Release for GPID-WB/compound-gpid via the GitHub API.

.DESCRIPTION
Creates a release for the specified git tag after verifying its branch, exact
remote tag, durable payload, native release gate, and Pages deployment.
Retrieves credentials from Git Credential Manager (idempotent -- skips if release exists).
Writes release metadata to release-result.txt next to this script.

.PARAMETER Tag
The git tag in stable or dev-prerelease format
(v<major>.<minor>.<patch>[.<build>]). Required.

.PARAMETER Name
The GitHub Release name/title. Required.

.PARAMETER NotesFile
Path to a Markdown file whose content becomes the release body. Required.

.PARAMETER Draft
If present, creates the release as a draft (not yet published).

.PARAMETER Prerelease
Compatibility switch. Four-component tags are always prereleases and stable
three-component tags cannot be marked as prereleases.

.EXAMPLE
.\create-release.ps1 -Tag v0.0.6 -Name "v0.0.6 - My feature" -NotesFile RELEASE_NOTES.md

.EXAMPLE
.\create-release.ps1 -Tag v0.0.6 -Name "v0.0.6 - Draft" -NotesFile RELEASE_NOTES.md -Draft

.EXAMPLE
.\create-release.ps1 -Tag v1.2.0.9008 -Name "v1.2.0.9008 - Test release" -NotesFile RELEASE_NOTES.md -Prerelease

.NOTES
Output format in release-result.txt (written next to this script):
  EXISTS|<id>|<url>   -- release already existed
  CREATED|<id>|<url>  -- release was created
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Tag,
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][string]$NotesFile,
    [switch]$Draft,
    [switch]$Prerelease
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Enforce semver tag format (v<major>.<minor>.<patch> or v<major>.<minor>.<patch>.<dev>)
# The four-component form (e.g. v0.12.0.9000) follows the R convention for dev prereleases.
if ($Tag -cnotmatch '^v\d+\.\d+\.\d+(\.\d+)?$') {
    Write-Error ('Invalid tag format ''' + $Tag + '''. Expected v<major>.<minor>.<patch> or v<major>.<minor>.<patch>.<dev> (e.g. v0.0.6 or v0.12.0.9000).')
    exit 1
}
$isPrereleaseTag = $Tag -cmatch '^v\d+\.\d+\.\d+\.\d+$'
$releaseBranch = "main"
if ($isPrereleaseTag) { $releaseBranch = "dev" }
if ($Draft.IsPresent) {
    throw "Draft releases are not supported by the durable release publication flow."
}
if ($Prerelease.IsPresent -and -not $isPrereleaseTag) {
    throw "Stable three-component tag '$Tag' cannot be published as a prerelease. Use a four-component tag from dev."
}
$releasePrerelease = $isPrereleaseTag

function Get-CgRemoteTagCommit {
    param([string]$ReleaseTag)

    $lines = @(git -C $PSScriptRoot ls-remote --tags origin "refs/tags/$ReleaseTag" "refs/tags/$ReleaseTag^{}" 2>$null)
    if ($LASTEXITCODE -ne 0 -or $lines.Count -lt 1) {
        throw "Release tag '$ReleaseTag' must exist on origin before API publication."
    }
    $peeled = @($lines | Where-Object { $_ -match '\^\{\}$' } | Select-Object -First 1)
    if ($peeled.Count -eq 0) { $peeled = @($lines[0]) }
    return ([string]$peeled[0] -split '\s+')[0]
}

function Assert-CgRemoteTagCommit {
    param(
        [string]$ReleaseTag,
        [string]$ExpectedCommit
    )

    $actual = Get-CgRemoteTagCommit -ReleaseTag $ReleaseTag
    if ($actual -ne $ExpectedCommit) {
        throw "Remote release tag mismatch: '$ReleaseTag' is $actual but HEAD is $ExpectedCommit."
    }
}

function Assert-CgRemoteReleaseLineage {
    param(
        [string]$ExpectedCommit,
        [string]$Branch
    )

    $branchRef = "+refs/heads/$Branch`:refs/remotes/origin/$Branch"
    git -C $PSScriptRoot fetch origin $branchRef 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Could not refresh origin/$Branch during publication."
    }
    $branchLines = @(git -C $PSScriptRoot ls-remote --heads origin "refs/heads/$Branch" 2>$null)
    if ($LASTEXITCODE -ne 0 -or $branchLines.Count -ne 1) {
        throw "Could not resolve remote release branch origin/$Branch."
    }
    $branchCommit = ([string]$branchLines[0] -split '\s+')[0]
    $fetchedBranchCommit = git -C $PSScriptRoot rev-parse --verify "origin/$Branch^{commit}" 2>$null
    if ($LASTEXITCODE -ne 0 -or $fetchedBranchCommit.Trim() -ne $branchCommit) {
        throw "Remote branch origin/$Branch changed during publication."
    }
    git -C $PSScriptRoot merge-base --is-ancestor $ExpectedCommit $branchCommit 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Release lineage mismatch: $ExpectedCommit is not on origin/$Branch ($branchCommit)."
    }

}

function ConvertTo-CgNormalizedReleaseText {
    param([AllowNull()][string]$Value)

    return ("$Value" -replace "`r`n", "`n" -replace "`r", "`n")
}

function Get-CgRemoteBranchCommit {
    param([string]$Branch)

    $lines = @(git -C $PSScriptRoot ls-remote --heads origin "refs/heads/$Branch" 2>$null)
    if ($LASTEXITCODE -ne 0 -or $lines.Count -ne 1) {
        throw "Could not resolve origin/$Branch."
    }
    return ([string]$lines[0] -split '\s+')[0]
}

if ([string]::IsNullOrWhiteSpace($Name)) {
    Write-Error "Release name cannot be empty."
    exit 1
}

# Validate notes file exists and has content
if (-not (Test-Path $NotesFile)) {
    Write-Error "Notes file not found: $NotesFile"
    exit 1
}
# Read notes and force to a plain string -- Get-Content attaches PS extended type
# metadata (PSPath, PSDrive, etc.) to its output. ConvertTo-Json serializes those
# as object properties, corrupting the JSON body. String interpolation strips them.
# Use -Encoding UTF8 so multi-byte characters aren't misread as Windows-1252.
$notes = "$(Get-Content -Path $NotesFile -Encoding UTF8 -Raw)"
if ([string]::IsNullOrWhiteSpace($notes)) {
    Write-Error "Notes file is empty: $NotesFile"
    exit 1
}

# Operational native-packaging preflight. This runs before credentials are read
# or any GitHub API request can observe or publish release state.
$headCommit = git -C $PSScriptRoot rev-parse --verify "HEAD^{commit}" 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($headCommit)) {
    throw "Could not resolve the current HEAD commit."
}
$headCommit = $headCommit.Trim()
$matchingTags = @(git -C $PSScriptRoot tag --list $Tag 2>$null)
if ($LASTEXITCODE -ne 0) {
    throw "Could not inspect existing release tags."
}
if ($matchingTags -notcontains $Tag) {
    throw "Release tag '$Tag' must exist locally before publication."
}
$tagCommit = git -C $PSScriptRoot rev-parse --verify "$Tag^{commit}" 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($tagCommit)) {
    throw "Release tag '$Tag' does not resolve to a commit."
}
if ($headCommit -ne $tagCommit.Trim()) {
    throw "Release checkout mismatch: tag '$Tag' resolves to $($tagCommit.Trim()) but HEAD is $headCommit. Check out the tag commit before releasing."
}
$branchRef = "+refs/heads/$releaseBranch`:refs/remotes/origin/$releaseBranch"
git -C $PSScriptRoot fetch origin $branchRef --tags 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Could not refresh origin/$releaseBranch before publication."
}
$remoteBranch = @(git -C $PSScriptRoot ls-remote --heads origin "refs/heads/$releaseBranch" 2>$null)
if ($LASTEXITCODE -ne 0 -or $remoteBranch.Count -ne 1) {
    throw "Could not resolve remote release branch origin/$releaseBranch."
}
$remoteBranchCommit = ([string]$remoteBranch[0] -split '\s+')[0]
git -C $PSScriptRoot merge-base --is-ancestor $headCommit $remoteBranchCommit 2>$null
if ($LASTEXITCODE -ne 0) {
    throw "Release lineage mismatch: tag '$Tag' at $headCommit is not on origin/$releaseBranch ($remoteBranchCommit)."
}
Assert-CgRemoteReleaseLineage -ExpectedCommit $headCommit -Branch $releaseBranch
Assert-CgRemoteTagCommit -ReleaseTag $Tag -ExpectedCommit $headCommit
$worktreeChanges = @(git -C $PSScriptRoot status --porcelain --untracked-files=normal 2>$null)
if ($LASTEXITCODE -ne 0) {
    throw "Could not verify that the release checkout is clean."
}
if ($worktreeChanges.Count -gt 0) {
    throw "Release checkout must be clean before testing tag '$Tag'."
}

$nodeCommand = Get-Command node -ErrorAction SilentlyContinue
if (-not $nodeCommand) {
    throw "Release payload validation requires Node.js."
}
$versionedPayload = Join-Path $PSScriptRoot "releases/$Tag.json"
$latestPayload = Join-Path $PSScriptRoot "releases/latest.json"
foreach ($payloadPath in @($versionedPayload, $latestPayload)) {
    & $nodeCommand.Source (Join-Path $PSScriptRoot "scripts/generate-whats-new.js") --root $PSScriptRoot --validate-payload $payloadPath
    if ($LASTEXITCODE -ne 0) {
        throw "Release payload validation failed for $payloadPath."
    }
}
& $nodeCommand.Source (Join-Path $PSScriptRoot "scripts/generate-whats-new.js") --root $PSScriptRoot --validate-release-set
if ($LASTEXITCODE -ne 0) {
    throw "Release payload set validation failed."
}
$recordedPayload = Get-Content -LiteralPath $versionedPayload -Raw -Encoding UTF8 | ConvertFrom-Json
if ([string]$recordedPayload.tag -ne $Tag -or [string]$recordedPayload.name -ne $Name) {
    throw "Release arguments do not match the immutable payload for '$Tag'."
}

$pythonCommand = $null
foreach ($candidate in @("python3", "python", "py")) {
    if (-not (Get-Command $candidate -ErrorAction SilentlyContinue)) { continue }
    try {
        $version = & $candidate --version 2>&1
        if ("$version".Trim() -match '^Python\s+\d') {
            $pythonCommand = $candidate
            break
        }
    } catch { continue }
}
if (-not $pythonCommand) {
    throw "Native packaging preflight requires Python (checked: python3, python, py)."
}

function Write-CgReleaseAttestation {
    & $pythonCommand (Join-Path $PSScriptRoot "scripts/cg_release_attestation.py") `
        --root $PSScriptRoot `
        --tag $Tag `
        --review-reference "release=$headCommit"
    if ($LASTEXITCODE -ne 0) {
        throw "Post-release skill attestation failed with exit code $LASTEXITCODE."
    }
}
$preflightRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("compound-gpid-release-" + [System.Guid]::NewGuid().ToString("N"))
try {
    & git -c core.autocrlf=false clone --quiet --no-hardlinks --no-checkout $PSScriptRoot $preflightRoot
    if ($LASTEXITCODE -ne 0) {
        throw "Could not create the isolated release preflight checkout."
    }
    & git -C $preflightRoot config core.autocrlf false
    & git -C $preflightRoot config core.eol lf
    & git -C $preflightRoot checkout --detach --quiet $headCommit
    if ($LASTEXITCODE -ne 0) {
        throw "Could not check out release commit $headCommit for preflight testing."
    }
    Write-Host "Running native packaging release preflight for $headCommit..." -ForegroundColor Cyan
    & $pythonCommand (Join-Path $preflightRoot "scripts/cg_pr_preflight.py") --root $preflightRoot --phase committed --full-gate --run-native-target
    if ($LASTEXITCODE -ne 0) {
        throw "Native packaging release preflight failed with exit code $LASTEXITCODE. Release publication is blocked."
    }
} finally {
    if (Test-Path -LiteralPath $preflightRoot) {
        Remove-Item -LiteralPath $preflightRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# Get token from Git Credential Manager. Stderr captured for diagnostics.
$credLines = "protocol=https`nhost=github.com`n" | git credential fill 2>&1
$token = ($credLines | Where-Object { $_ -match "^password=" } | Select-Object -First 1) -replace "^password=", ""
if ([string]::IsNullOrEmpty($token)) {
    Write-Error "No GitHub token found. Ensure Git Credential Manager is installed and credentials are stored for github.com.`nRaw GCM output:`n$credLines"
    exit 1
}

$headers = @{
    Authorization = "Bearer $token"
    Accept        = "application/vnd.github+json"
    "User-Agent"  = "ps-cg"
}

function Get-CgRepositoryRuleset {
    param(
        [string]$RulesetName,
        [string]$RulesetTarget
    )

    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $summaryResponse = Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/rulesets" -Headers $headers
        $summaries = @($summaryResponse)
        $match = @()
        foreach ($summary in $summaries) {
            if ($summary.name -eq $RulesetName -and
                $summary.target -eq $RulesetTarget -and
                $summary.enforcement -eq "active") {
                $match += $summary
            }
        }
        if ($match.Count -eq 1) {
            $detail = Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/rulesets/$($match[0].id)" -Headers $headers
            $properties = @($detail.PSObject.Properties.Name)
            if ($properties -contains "rules" -and
                $properties -contains "conditions" -and
                $properties -contains "bypass_actors" -and
                $properties -contains "current_user_can_bypass") {
                return $detail
            }
        }
        if ($attempt -lt 3) { Start-Sleep -Seconds 2 }
    }

    throw "Could not read one complete active '$RulesetName' $RulesetTarget ruleset after 3 attempts."
}

$ruleset = Get-CgRepositoryRuleset -RulesetName "Protect release tags" -RulesetTarget "tag"
$ruleTypes = @($ruleset.rules | ForEach-Object { [string]$_.type })
$includedRefs = @($ruleset.conditions.ref_name.include | ForEach-Object { [string]$_ })
$excludedRefs = @($ruleset.conditions.ref_name.exclude | ForEach-Object { [string]$_ })
$bypassActors = @($ruleset.bypass_actors)
$currentUserCanBypass = [string]$ruleset.current_user_can_bypass
$tagRuleProblems = @()
if ($ruleTypes -notcontains "update") { $tagRuleProblems += "missing update rule" }
if ($ruleTypes -notcontains "deletion") { $tagRuleProblems += "missing deletion rule" }
if ($ruleTypes -notcontains "non_fast_forward") { $tagRuleProblems += "missing non_fast_forward rule" }
if ($includedRefs -notcontains "refs/tags/v*") { $tagRuleProblems += "missing refs/tags/v* include" }
if ($excludedRefs.Count -ne 0) { $tagRuleProblems += "has excluded refs" }
if ($bypassActors.Count -ne 0) { $tagRuleProblems += "has bypass actors" }
if ($currentUserCanBypass -ne "never") { $tagRuleProblems += "current user can bypass ($currentUserCanBypass)" }
if ($tagRuleProblems.Count -ne 0) {
    throw "'Protect release tags' is invalid: $($tagRuleProblems -join '; ')."
}

$creationRuleset = Get-CgRepositoryRuleset -RulesetName "Restrict release tag creation" -RulesetTarget "tag"
$creationRuleTypes = @($creationRuleset.rules | ForEach-Object { [string]$_.type })
$creationIncludes = @($creationRuleset.conditions.ref_name.include | ForEach-Object { [string]$_ })
$creationExcludes = @($creationRuleset.conditions.ref_name.exclude | ForEach-Object { [string]$_ })
$creationBypass = @($creationRuleset.bypass_actors)
if ($creationRuleTypes -notcontains "creation" -or
    $creationIncludes -notcontains "refs/tags/v*" -or
    $creationExcludes.Count -ne 0 -or
    $creationBypass.Count -ne 1 -or
    [string]$creationBypass[0].actor_type -ne "RepositoryRole" -or
    [int]$creationBypass[0].actor_id -ne 5 -or
    [string]$creationBypass[0].bypass_mode -ne "always") {
    throw "'Restrict release tag creation' must limit refs/tags/v* creation to repository administrators."
}

$devRuleset = Get-CgRepositoryRuleset -RulesetName "Protect dev" -RulesetTarget "branch"
$devRuleTypes = @($devRuleset.rules | ForEach-Object { [string]$_.type })
$devIncludes = @($devRuleset.conditions.ref_name.include | ForEach-Object { [string]$_ })
$devExcludes = @($devRuleset.conditions.ref_name.exclude | ForEach-Object { [string]$_ })
$devBypass = @($devRuleset.bypass_actors)
if ($devRuleTypes -notcontains "deletion" -or
    $devRuleTypes -notcontains "non_fast_forward" -or
    $devIncludes -notcontains "refs/heads/dev" -or
    $devExcludes.Count -ne 0 -or
    $devBypass.Count -ne 0 -or
    [string]$devRuleset.current_user_can_bypass -ne "never") {
    throw "'Protect dev' must block deletion and non-fast-forward updates without exclusions or bypass actors."
}

# Output written next to this script so it's always findable regardless of the caller's cwd
$resultFile = Join-Path $PSScriptRoot "release-result.txt"

# The immutable tag-site deployment must succeed before a release API record is
# created. Select both workflow runs by exact tag, commit, and controller run
# name, never by recency alone.
$encodedTag = [uri]::EscapeDataString($Tag)
$buildRunsUri = "https://api.github.com/repos/GPID-WB/compound-gpid/actions/workflows/release-docs.yml/runs?event=push&branch=$encodedTag&per_page=20"
$buildRuns = Invoke-RestMethod -Uri $buildRunsUri -Headers $headers
$matchingBuildRuns = @($buildRuns.workflow_runs | Where-Object {
    $_.head_sha -eq $headCommit -and $_.head_branch -eq $Tag
})
if ($matchingBuildRuns.Count -ne 1 -or
    $matchingBuildRuns[0].status -ne "completed" -or
    $matchingBuildRuns[0].conclusion -ne "success") {
    throw "A successful release-docs.yml push run for exact tag '$Tag' at $headCommit is required before publication."
}
$controllerRunName = "Deploy docs from $($matchingBuildRuns[0].id)"
$pagesRunsUri = "https://api.github.com/repos/GPID-WB/compound-gpid/actions/workflows/release-pages.yml/runs?event=workflow_run&per_page=50"
$pagesRuns = Invoke-RestMethod -Uri $pagesRunsUri -Headers $headers
$matchingPagesRuns = @($pagesRuns.workflow_runs | Where-Object {
    $_.name -eq $controllerRunName -and $_.display_title -eq $controllerRunName
})
if ($matchingPagesRuns.Count -ne 1 -or
    $matchingPagesRuns[0].status -ne "completed" -or
    $matchingPagesRuns[0].conclusion -ne "success") {
    throw "A successful release-pages.yml controller run named '$controllerRunName' is required before publication."
}

# Idempotency check: if this tag already has a release, skip creation
$existingRelease = $null
try {
    $existingRelease = Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases/tags/$Tag" -Headers $headers
} catch {
    # Only a 404 means "release doesn't exist" -- re-throw all other HTTP errors
    # Note: ?. is PS7+ only; use if/else for PS5.1 compatibility
    if ($_.Exception.Response) { $status = $_.Exception.Response.StatusCode.value__ } else { $status = $null }
    if ($null -eq $status -or $status -ne 404) { throw }
}

$immutablePayloads = @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot "releases") -Filter "v*.json" | ForEach-Object {
    Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
} | Sort-Object publishedAt -Descending)
if ($immutablePayloads.Count -lt 1 -or [string]$immutablePayloads[0].tag -ne $Tag) {
    throw "Target tag '$Tag' must be the newest immutable release payload."
}
$publishedReleaseResponse = Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases?per_page=100" -Headers $headers
$publishedReleases = @($publishedReleaseResponse)
$publishedByTag = @{}
foreach ($published in @($publishedReleases)) {
    if (-not [bool]$published.draft) { $publishedByTag[[string]$published.tag_name] = $published }
}
foreach ($record in @($immutablePayloads | Select-Object -Skip 1)) {
    $recordTag = [string]$record.tag
    if (-not $publishedByTag.ContainsKey($recordTag)) {
        throw "Durable release payload '$recordTag' has no published GitHub Release. Repair historical release records before continuing."
    }
    $published = $publishedByTag[$recordTag]
    $recordPrerelease = $recordTag -cmatch '^v\d+\.\d+\.\d+\.\d+$'
    if ([string]$published.name -ne [string]$record.name -or
        [bool]$published.prerelease -ne $recordPrerelease) {
        throw "Published GitHub Release '$recordTag' does not match its durable payload."
    }
}

if ($null -ne $existingRelease) {
    if (-not $existingRelease.id -or -not $existingRelease.html_url) {
        Write-Error "GitHub API response missing expected fields (id, html_url). Raw: $($existingRelease | ConvertTo-Json)"
        exit 1
    }
    if ([string]$existingRelease.tag_name -ne $Tag -or
        [bool]$existingRelease.prerelease -ne $releasePrerelease -or
        [bool]$existingRelease.draft -or
        [string]$existingRelease.name -ne $Name -or
        [string]$existingRelease.target_commitish -ne $headCommit -or
        (ConvertTo-CgNormalizedReleaseText $existingRelease.body) -ne (ConvertTo-CgNormalizedReleaseText $notes)) {
        throw "Existing GitHub Release for '$Tag' does not match the requested immutable release metadata."
    }
    Assert-CgRemoteReleaseLineage -ExpectedCommit $headCommit -Branch $releaseBranch
    Assert-CgRemoteTagCommit -ReleaseTag $Tag -ExpectedCommit $headCommit
    Write-CgReleaseAttestation
    "EXISTS|$($existingRelease.id)|$($existingRelease.html_url)" | Set-Content $resultFile
    exit 0
}

# Create the release
Assert-CgRemoteReleaseLineage -ExpectedCommit $headCommit -Branch $releaseBranch
Assert-CgRemoteTagCommit -ReleaseTag $Tag -ExpectedCommit $headCommit
$releaseBranchSnapshot = Get-CgRemoteBranchCommit -Branch $releaseBranch
$payload = ConvertTo-Json -InputObject @{
    tag_name         = $Tag
    target_commitish = $headCommit
    name             = $Name
    body             = $notes
    draft            = $false
    prerelease       = $releasePrerelease
}

# ConvertTo-Json escapes all non-ASCII as \uXXXX, so $payload is pure ASCII --
# safe to pass as a string directly. The ETS issue is on $notes (fixed above),
# not on the serialized JSON string itself.
$response = $null
try {
    $response = Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases" `
        -Method Post -Headers $headers -Body $payload -ContentType "application/json"
    Assert-CgRemoteTagCommit -ReleaseTag $Tag -ExpectedCommit $headCommit
    if ((Get-CgRemoteBranchCommit -Branch $releaseBranch) -ne $releaseBranchSnapshot) {
        throw "Release branch lineage changed during API publication."
    }
    if (-not $response.id -or -not $response.html_url -or
        [string]$response.tag_name -ne $Tag -or
        [string]$response.target_commitish -ne $headCommit -or
        [bool]$response.prerelease -ne $releasePrerelease -or
        [bool]$response.draft -or
        [string]$response.name -ne $Name -or
        (ConvertTo-CgNormalizedReleaseText $response.body) -ne (ConvertTo-CgNormalizedReleaseText $notes)) {
        throw "GitHub API response does not match the requested immutable release metadata."
    }
    Write-CgReleaseAttestation
} catch {
    if ($response -and $response.id) {
        Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases/$($response.id)" -Method Delete -Headers $headers
    }
    throw
}

"CREATED|$($response.id)|$($response.html_url)" | Set-Content $resultFile
