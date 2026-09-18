<#
.SYNOPSIS
Creates a GitHub Release for GPID-WB/compound-gpid via the GitHub API.

.DESCRIPTION
Reserve pushes the exact local annotated tag and immediately creates its matching
published Release after all preflight checks. Finalize verifies the documentation
run chain and writes the attestation. Neither phase deletes or edits a Release.
All reservations set make_latest to "false", including stable tags. Neither phase
promotes a Release to GitHub's latest stable release.
Retrieves credentials from Git Credential Manager.
Writes release metadata to release-result.txt next to this script.

.PARAMETER Tag
The git tag in stable or dev-prerelease format
(v<major>.<minor>.<patch>[.<build>]). Required.

.PARAMETER Name
The GitHub Release name/title. Required.

.PARAMETER NotesFile
Path to a Markdown file whose content becomes the release body. Required.

.PARAMETER Draft
Compatibility switch. Drafts are rejected because reservation must be published.

.PARAMETER Prerelease
Compatibility switch. Four-component tags are always prereleases and stable
three-component tags cannot be marked as prereleases.

.EXAMPLE
.\create-release.ps1 -Phase Reserve -LegacyOperation Bridge -SourceBranch main -Tag v0.0.6 -Name "v0.0.6 - My feature" -NotesFile RELEASE_NOTES.md

.PARAMETER Phase
Reserve (default) establishes the tag/Release pair, not lifecycle completion.
Finalize requires that pair and a successful exact documentation build.
Stable releases also require the protected documentation deployment chain.

.PARAMETER BuildRunId
Optional exact release-docs run ID for Finalize, useful after workflow retries.

.PARAMETER PagesRunId
Optional exact release-pages controller run ID for stable Finalize.
Four-component prereleases do not require or inspect a Pages deployment.

.PARAMETER SourceBranch
Same-repository source branch, verified against origin. Defaults to the attached
checkout branch; detached checkouts must provide it explicitly. Stable releases
require the protected remote policy's production_branches or remote default.

.PARAMETER LegacyOperation
Required. Bridge permits reviewed legacy publication only before the cutover
recorded on the protected remote default. Recovery requires current maintainer authority and an
existing exact remote tag or a reviewed historical record on that protected ref.
Recovery cannot be used for routine new publication. Tags and published bytes stay
unchanged. Post-cutover stable docs recovery requires the reviewed exact build/artifact
record and an explicit PagesRunId from release-pages.yml manual recovery.

.PARAMETER Timing
Opt in to JSON Lines timing on stderr. Records contain fixed stage names,
monotonic elapsed seconds, and outcome only; no credentials or release inputs.
For example, add -Timing to an otherwise authorized Reserve or Finalize command.
Timing does not authorize a release or change its validation requirements.

.PARAMETER PreflightReceipt
Optional external JSON receipt from cg_pr_preflight.py --emit-receipt. Both phases
reuse only exact commit/tree, complete successful command, digest and LF evidence.
Missing or invalid evidence runs the existing isolated full gate instead.

.EXAMPLE
.\create-release.ps1 -Phase Finalize -LegacyOperation Recovery -SourceBranch dev -Tag v1.2.0.9008 -Name "v1.2.0.9008 - Test release" -NotesFile RELEASE_NOTES.md -Prerelease

.NOTES
Output format in release-result.txt (written next to this script):
  EXISTS|<id>|<url>   -- reservation already existed
  CREATED|<id>|<url>  -- reservation was created
  FINALIZED|<id>|<url> -- required docs evidence and local attestation verified; commit evidence next
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Tag,
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][string]$NotesFile,
    [switch]$Draft,
    [switch]$Prerelease,
    [ValidateSet("Reserve", "Finalize")][string]$Phase = "Reserve",
    [ValidateRange(1, [long]::MaxValue)][long]$BuildRunId,
    [ValidateRange(1, [long]::MaxValue)][long]$PagesRunId,
    [switch]$Timing,
    [string]$PreflightReceipt,
    [string]$SourceBranch,
    [ValidateSet("Bridge", "Recovery")][string]$LegacyOperation
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not $LegacyOperation) {
    throw "Routine publication uses cg-release start. Legacy publication requires explicit -LegacyOperation Bridge or Recovery."
}
. (Join-Path $PSScriptRoot 'scripts/release-legacy-authority.ps1')

function Write-CgReleaseTiming {
    <#
    .SYNOPSIS
    Emit one opt-in monotonic span without operation inputs or error bodies.
    .PARAMETER Stage
    Fixed stage identity; caller text cannot enter timing diagnostics.
    .PARAMETER Clock
    Stopwatch started before the measured span, or null when disabled.
    .PARAMETER Completed
    True only after the span's existing success checks complete.
    .EXAMPLE
    Write-CgReleaseTiming -Stage gates -Clock $gateClock -Completed $gateCompleted
    #>
    param(
        [ValidateSet("preparation", "gates", "subprocess", "publication", "recovery")][string]$Stage,
        [System.Diagnostics.Stopwatch]$Clock,
        [bool]$Completed
    )
    if (-not $Timing -or $null -eq $Clock) { return }
    $Clock.Stop()
    $outcome = "interrupted"
    if ($Completed) { $outcome = "complete" }
    $record = [ordered]@{
        schema_version = 1; kind = "timing"; stage = $Stage
        elapsed_seconds = $Clock.Elapsed.TotalSeconds; outcome = $outcome
    }
    try { [Console]::Error.WriteLine(($record | ConvertTo-Json -Compress)) }
    catch {
        # Telemetry cannot replace the original result after a remote write.
        Write-Warning "Release timing output is unavailable." -WarningAction Continue
    }
}

$preparationClock = $null
if ($Timing) { $preparationClock = [System.Diagnostics.Stopwatch]::StartNew() }
$preparationCompleted = $false
try {
$resultFile = Join-Path $PSScriptRoot "release-result.txt"
if (Test-Path -LiteralPath $resultFile) { Remove-Item -LiteralPath $resultFile -Force }
if ($Phase -eq "Reserve" -and ($BuildRunId -or $PagesRunId)) {
    throw "Documentation run IDs apply only to Finalize."
}

# Enforce semver tag format (v<major>.<minor>.<patch> or v<major>.<minor>.<patch>.<dev>)
# The four-component form (e.g. v0.12.0.9000) follows the R convention for dev prereleases.
if ($Tag -cnotmatch '^v\d+\.\d+\.\d+(\.\d+)?$') {
    Write-Error ('Invalid tag format ''' + $Tag + '''. Expected v<major>.<minor>.<patch> or v<major>.<minor>.<patch>.<dev> (e.g. v0.0.6 or v0.12.0.9000).')
    exit 1
}
$isPrereleaseTag = $Tag -cmatch '^v\d+\.\d+\.\d+\.\d+$'
if ($Draft.IsPresent) {
    throw "Draft releases are not supported by the durable release publication flow."
}
if ($Prerelease.IsPresent -and -not $isPrereleaseTag) {
    throw "Stable three-component tag '$Tag' cannot be published as a prerelease. Use a four-component tag from a verified source branch."
}
$releasePrerelease = $isPrereleaseTag
if ($Phase -eq "Finalize" -and $Tag -ceq "v1.2.0.9014") {
    throw "Withdrawn v1.2.0.9014 is not eligible for lifecycle attestation."
}
$releaseBranch = $SourceBranch
if ([string]::IsNullOrWhiteSpace($releaseBranch)) {
    $releaseBranch = git -C $PSScriptRoot symbolic-ref --quiet --short HEAD 2>$null
    if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($releaseBranch)) {
        throw 'A detached release checkout requires explicit -SourceBranch.'
    }
}
Assert-CgReleaseBranchName -Branch $releaseBranch

function Get-CgRemoteTagIdentity {
    param([string]$ReleaseTag)

    $lines = @(git -C $PSScriptRoot ls-remote --tags origin "refs/tags/$ReleaseTag" "refs/tags/$ReleaseTag^{}" 2>$null)
    if ($LASTEXITCODE -ne 0) {
        throw "Could not read remote release tag '$ReleaseTag'."
    }
    if ($lines.Count -eq 0) { return $null }
    $refs = @{}
    foreach ($line in $lines) {
        $fields = ([string]$line) -split '\s+'
        if ($fields.Count -ne 2 -or $fields[0] -cnotmatch '^[0-9a-f]{40}$' -or
            $fields[1] -cnotin @("refs/tags/$ReleaseTag", "refs/tags/$ReleaseTag^{}") -or
            $refs.ContainsKey($fields[1])) {
            throw "Remote release tag mismatch: malformed or duplicate tag identity."
        }
        $refs[$fields[1]] = $fields[0]
    }
    if ($refs.Count -ne 2) { throw "Remote release tag mismatch: an annotated tag is required." }
    return [pscustomobject]@{ Object = $refs["refs/tags/$ReleaseTag"]; Commit = $refs["refs/tags/$ReleaseTag^{}"] }
}

function Assert-CgRemoteTagCommit {
    param(
        [string]$ReleaseTag,
        [string]$ExpectedCommit
    )

    $actual = Get-CgRemoteTagIdentity -ReleaseTag $ReleaseTag
    if ($null -eq $actual -or $actual.Commit -cne $ExpectedCommit -or $actual.Object -cne $tagObject) {
        throw "Remote release tag mismatch: '$ReleaseTag' must match the local raw tag object and HEAD."
    }
}

function Assert-CgRemoteReleaseLineage {
    param(
        [string]$ExpectedCommit,
        [string]$Branch,
        [switch]$RequireTip
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
    $fields = ([string]$branchLines[0] -split '\s+')
    if ($fields.Count -ne 2 -or $fields[0] -cnotmatch '^[0-9a-f]{40}$' -or $fields[1] -cne "refs/heads/$Branch") {
        throw "Invalid remote release branch identity for origin/$Branch."
    }
    $branchCommit = $fields[0]
    $fetchedBranchCommit = git -C $PSScriptRoot rev-parse --verify "origin/$Branch^{commit}" 2>$null
    if ($LASTEXITCODE -ne 0 -or $fetchedBranchCommit.Trim() -cne $branchCommit) {
        throw "Remote branch origin/$Branch changed during publication."
    }
    if ($RequireTip -and $ExpectedCommit -cne $branchCommit) {
        throw "A new remote tag requires HEAD at exact current origin/$Branch."
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

function Assert-CgStableDocsContract {
    <#
    .SYNOPSIS
    Check stable documentation compatibility from immutable Git objects, without executing workflows.
    .PARAMETER ExpectedCommit
    Exact tag commit whose producer must be supported by the protected default controller.
    .PARAMETER Authority
    Fresh protected remote default branch and exact controller commit.
    .EXAMPLE
    Assert-CgStableDocsContract -ExpectedCommit $headCommit -Authority $authority
    #>
    param([string]$ExpectedCommit, $Authority)

    # Source eligibility and controller location are independent. Read the exact
    # protected controller object without requiring source ancestry from its tip.
    $controllerCommit = $Authority.Commit
    git -C $PSScriptRoot fetch origin $controllerCommit 2>$null
    if ($LASTEXITCODE -ne 0) {
        throw "Cannot fetch protected default controller $($Authority.Branch) at $controllerCommit."
    }
    $remediation = "sync the protected controller on $($Authority.Branch) first"
    $producerLines = @(git -C $PSScriptRoot show "$ExpectedCommit`:.github/workflows/release-docs.yml" 2>$null)
    if ($LASTEXITCODE -ne 0 -or $producerLines.Count -eq 0) {
        throw "Cannot read release-docs.yml at the tag commit; $remediation and verify the producer."
    }
    $controllerLines = @(git -C $PSScriptRoot show "$controllerCommit`:.github/workflows/release-pages.yml" 2>$null)
    if ($LASTEXITCODE -ne 0 -or $controllerLines.Count -eq 0) {
        throw "Cannot read release-pages.yml at protected default commit $controllerCommit; $remediation."
    }
    $producer = ($producerLines -join "`n") -replace "`r`n", "`n"
    $controller = ($controllerLines -join "`n") -replace "`r`n", "`n"

    # Recognize the reviewed upload contract, not arbitrary YAML or workflow code.
    # Unknown layouts fail closed. Both artifacts are needed for ISOLATED_RELEASE=true.
    foreach ($job in @(@{ Id = 'build'; Artifact = 'release-docs-site' }, @{ Id = 'build-dev'; Artifact = 'release-dev-docs' })) {
        $jobs = [regex]::Matches($producer, '(?ms)^  ' + $job.Id + ':\n(?<body>.*?)(?=^  [\w-]+:|\z)')
        if ($jobs.Count -ne 1) {
            throw "release-docs.yml must contain one $($job.Id) job; $remediation and verify the producer."
        }
        if ($jobs[0].Groups['body'].Value -cmatch '(?m)^    if:') {
            throw "release-docs.yml $($job.Id) upload availability is conditional; $remediation and verify the producer."
        }
        $uploads = @([regex]::Split($jobs[0].Groups['body'].Value, '(?m)(?=^      - )') | Where-Object {
            $_ -cmatch ('(?m)^          name: ' + $job.Artifact + '\s*$')
        })
        $uploadContract = '(?s)^      - (?:name: [^\n]+\n        )?uses: actions/upload-artifact@[0-9a-f]{40}[^\n]*\n' +
            '        with:\n          name: ' + $job.Artifact + '\n          path: \|\n' +
            '            docs/\n            \.docs-build-metadata\.json\n' +
            '          retention-days: [1-9][0-9]*\n          include-hidden-files: true\n          if-no-files-found: error\s*$'
        if ($uploads.Count -ne 1 -or $uploads[0] -cnotmatch $uploadContract) {
            throw "release-docs.yml $($job.Id) must upload $($job.Artifact) with docs/ and .docs-build-metadata.json (hidden files enabled); $remediation and verify the producer."
        }
    }
    $deployJobs = [regex]::Matches($controller, '(?ms)^  deploy:\n(?<body>.*?)(?=^  [\w-]+:|\z)')
    if ($deployJobs.Count -ne 1) {
        throw "release-pages.yml must contain one deploy job; $remediation."
    }
    $deploySteps = [regex]::Split($deployJobs[0].Groups['body'].Value, '(?m)(?=^      - )')
    $verifySteps = @($deploySteps | Where-Object {
        $_ -cmatch '(?m)^      - name: Verify release tag, lineage, payload, and artifact$'
    })
    $layoutContract = '(?m)^          const root = "release-artifact";\n' +
        ' +const docs = path\.join\(root, process\.env\.ISOLATED_RELEASE === "true" \? "docs" : "site"\);\n' +
        '          const metadata = JSON\.parse\(fs\.readFileSync\(path\.join\(root, "\.docs-build-metadata\.json"\), "utf8"\)\);'
    if ($verifySteps.Count -ne 1 -or $verifySteps[0] -cnotmatch $layoutContract -or
        $verifySteps[0] -cnotmatch '(?m)^          ISOLATED_RELEASE: \$\{\{ steps\.authority\.outputs\.dev_artifact_id != '''' \}\}$' -or
        $verifySteps[0] -cnotmatch '(?m)^        run: \|$' -or
        $verifySteps[0] -cmatch '(?m)^        if:') {
        throw "release-pages.yml does not verify the isolated docs/ + .docs-build-metadata.json layout from release-docs.yml; $remediation."
    }

    # The isolated docs/ trees must reach composition before Pages receives site/.
    # Match whole steps so skipped steps, changed paths and extra conditions fail closed.
    $compositionContract = @'
      - name: Compose isolated producer artifacts with protected code
        if: steps.authority.outputs.dev_artifact_id != ''
        env:
          RELEASE_TAG: ${{ steps.authority.outputs.release_tag }}
          RELEASE_SHA: ${{ steps.authority.outputs.release_sha }}
        run: |
          node scripts/legacy-pages.js import-docs release-source release-artifact
          node scripts/legacy-pages.js import-dev current-dev release-dev-artifact
          dev_sha="$(git -C current-dev rev-parse HEAD)"
          node scripts/assemble-docs-site.js --main-root release-source --dev-root current-dev --out composed-artifact --main-sha "$RELEASE_SHA" --dev-sha "$dev_sha" --main-branch "$RELEASE_BRANCH" --main-ref "$RELEASE_TAG"
          mv release-artifact release-build-artifact
          mv composed-artifact release-artifact
'@
    $requiredSteps = [ordered]@{
        'Download isolated dev documentation' = '(?s)^      - name: Download isolated dev documentation\n' +
            '        if: steps\.authority\.outputs\.dev_artifact_id != ''''\n' +
            '        uses: actions/download-artifact@[0-9a-f]{40}[^\n]*\n        with:\n' +
            '          artifact-ids: \$\{\{ steps\.authority\.outputs\.dev_artifact_id \}\}\n' +
            '          merge-multiple: true\n          path: release-dev-artifact\n' +
            '          run-id: \$\{\{ inputs\.build_run_id \|\| github\.event\.workflow_run\.id \}\}\n' +
            '          github-token: \$\{\{ github\.token \}\}\s*$'
        'Download exact release documentation artifact' = '(?s)^      - name: Download exact release documentation artifact\n' +
            '        uses: actions/download-artifact@[0-9a-f]{40}[^\n]*\n        with:\n' +
            '          artifact-ids: \$\{\{ steps\.authority\.outputs\.artifact_id \}\}\n' +
            '          merge-multiple: true\n          path: release-artifact\n' +
            '          run-id: \$\{\{ inputs\.build_run_id \|\| github\.event\.workflow_run\.id \}\}\n' +
            '          github-token: \$\{\{ github\.token \}\}\s*$'
        'Verify release tag, lineage, payload, and artifact' = $layoutContract
        'Check out exact release source as data' = '(?s)^      - name: Check out exact release source as data\n' +
            '        uses: actions/checkout@[0-9a-f]{40}[^\n]*\n        with:\n' +
            '          ref: \$\{\{ steps\.authority\.outputs\.release_sha \}\}\n' +
            '          path: release-source\n          fetch-depth: 1\n          persist-credentials: false\s*$'
        'Check out current dev source as data' = '(?s)^      - name: Check out current dev source as data\n' +
            '        uses: actions/checkout@[0-9a-f]{40}[^\n]*\n        with:\n' +
            '          ref: dev\n          path: current-dev\n          fetch-depth: 0\n          persist-credentials: false\s*$'
        'Compose isolated producer artifacts with protected code' = '^' + [regex]::Escape(($compositionContract -replace "`r`n", "`n")) + '\s*$'
        'Seal durable official snapshot in the Pages artifact' = '(?s)^      - name: Seal durable official snapshot in the Pages artifact\n' +
            '        env:\n          GH_TOKEN: \$\{\{ steps\.recovery-authority\.outputs\.token \|\| github\.token \}\}\n' +
            '        run: node scripts/legacy-pages\.js seal-official release-source release-artifact\s*$'
        'Upload verified release Pages artifact' = '(?s)^      - name: Upload verified release Pages artifact\n' +
            '        uses: actions/upload-pages-artifact@[0-9a-f]{40}[^\n]*\n        with:\n' +
            '          path: release-artifact/site\s*$'
    }
    $previousStep = -1
    foreach ($stepName in $requiredSteps.Keys) {
        $stepMatches = @($deploySteps | Where-Object {
            $_ -cmatch ('(?m)^      - name: ' + [regex]::Escape($stepName) + '$')
        })
        if ($stepMatches.Count -ne 1 -or $stepMatches[0] -cnotmatch $requiredSteps[$stepName]) {
            throw "release-pages.yml step '$stepName' has an incompatible extraction/composition contract; $remediation."
        }
        $stepIndex = [array]::IndexOf($deploySteps, $stepMatches[0])
        if ($stepIndex -le $previousStep) {
            throw "release-pages.yml step '$stepName' is out of extraction/composition order; $remediation."
        }
        $previousStep = $stepIndex
    }
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
$preparationCompleted = $true
} finally {
    Write-CgReleaseTiming -Stage preparation -Clock $preparationClock -Completed $preparationCompleted
}

# Operational native-packaging preflight. This runs before credentials are read
# or any GitHub API request can observe or publish release state.
$gateClock = $null
if ($Timing) { $gateClock = [System.Diagnostics.Stopwatch]::StartNew() }
$gateCompleted = $false
try {
$originPattern = '^(https://github\.com/GPID-WB/compound-gpid(?:\.git)?|git@github\.com:GPID-WB/compound-gpid(?:\.git)?|ssh://git@github\.com/GPID-WB/compound-gpid(?:\.git)?)$'
foreach ($direction in @(@("--all"), @("--push", "--all"))) {
    $originUrls = @(git -C $PSScriptRoot remote get-url @direction origin 2>$null)
    if ($LASTEXITCODE -ne 0 -or $originUrls.Count -ne 1 -or $originUrls[0] -cnotmatch $originPattern) {
        throw "Release origin must have one canonical GPID-WB/compound-gpid GitHub fetch and push URL."
    }
}
$headCommit = git -C $PSScriptRoot rev-parse --verify "HEAD^{commit}" 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($headCommit)) {
    throw "Could not resolve the current HEAD commit."
}
$headCommit = $headCommit.Trim()
$matchingTags = @(git -C $PSScriptRoot tag --list $Tag 2>$null)
if ($LASTEXITCODE -ne 0) {
    throw "Could not inspect existing release tags."
}
if ($matchingTags -cnotcontains $Tag) {
    throw "Release tag '$Tag' must exist locally before publication."
}
$tagCommit = git -C $PSScriptRoot rev-parse --verify "refs/tags/$Tag^{commit}" 2>$null
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace($tagCommit)) {
    throw "Release tag '$Tag' does not resolve to a commit."
}
if ($headCommit -cne $tagCommit.Trim()) {
    throw "Release checkout mismatch: tag '$Tag' resolves to $($tagCommit.Trim()) but HEAD is $headCommit. Check out the tag commit before releasing."
}
$tagType = git -C $PSScriptRoot cat-file -t "refs/tags/$Tag" 2>$null
if ($LASTEXITCODE -ne 0 -or $tagType -cne "tag") { throw "Local release tag must be annotated." }
$tagObject = git -C $PSScriptRoot rev-parse --verify "refs/tags/$Tag" 2>$null
if ($LASTEXITCODE -ne 0 -or $tagObject -cnotmatch '^[0-9a-f]{40}$') { throw "Could not resolve local tag object." }
$remoteTag = Get-CgRemoteTagIdentity -ReleaseTag $Tag
if ($null -ne $remoteTag) { Assert-CgRemoteTagCommit -ReleaseTag $Tag -ExpectedCommit $headCommit }
if ($Phase -eq "Finalize" -and $null -eq $remoteTag) { throw "Finalize requires the existing remote tag." }
Assert-CgRemoteReleaseLineage -ExpectedCommit $headCommit -Branch $releaseBranch -RequireTip:($null -eq $remoteTag)
$worktreeChanges = @(git -C $PSScriptRoot status --porcelain --untracked-files=all 2>$null)
if ($LASTEXITCODE -ne 0) {
    throw "Could not verify that the release checkout is clean."
}
$attestationRelative = ".github/shared/skill-management/release-attestations/$Tag.json"
$attestationRetry = $worktreeChanges -ccontains "?? $attestationRelative"
if (@($worktreeChanges | Where-Object { $_ -cne "?? $attestationRelative" }).Count -gt 0) {
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
if ([string]$recordedPayload.tag -cne $Tag -or [string]$recordedPayload.name -cne $Name) {
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
if ($attestationRetry) {
    # Read-only exact-byte validation uses the existing secure attestation service.
    & $pythonCommand (Join-Path $PSScriptRoot "scripts/cg_release_attestation.py") `
        --root $PSScriptRoot --tag $Tag --review-reference "release=$headCommit" --check
    if ($LASTEXITCODE -ne 0) { throw "Release checkout must be clean or contain only the identical canonical attestation." }
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
$receiptAccepted = $false
if ($PreflightReceipt) {
    try {
        $headTree = git -C $PSScriptRoot rev-parse --verify "HEAD^{tree}" 2>$null
        if ($LASTEXITCODE -eq 0 -and "$headTree" -cmatch '^[0-9a-f]{40}$') {
            # Python owns canonical JSON and the authoritative full command list.
            & $pythonCommand (Join-Path $PSScriptRoot "scripts/cg_pr_preflight.py") `
                --verify-receipt $PreflightReceipt --expected-commit $headCommit --expected-tree $headTree
            $receiptAccepted = $LASTEXITCODE -eq 0
        }
    } catch {
        $receiptAccepted = $false
    }
    if ($receiptAccepted) {
        Write-Host "Preflight receipt accepted for $headCommit; skipping re-run." -ForegroundColor Cyan
    } else {
        Write-Warning "Preflight receipt unavailable or invalid; running the full gate."
    }
}
if (-not $receiptAccepted) {
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
    $subprocessClock = $null
    if ($Timing) { $subprocessClock = [System.Diagnostics.Stopwatch]::StartNew() }
    $subprocessCompleted = $false
    try {
        & $pythonCommand (Join-Path $preflightRoot "scripts/cg_pr_preflight.py") --root $preflightRoot --phase committed --full-gate --run-native-target
        if ($LASTEXITCODE -ne 0) {
            throw "Native packaging release preflight failed with exit code $LASTEXITCODE. Release publication is blocked."
        }
        $subprocessCompleted = $true
    } finally {
        Write-CgReleaseTiming -Stage subprocess -Clock $subprocessClock -Completed $subprocessCompleted
    }
} finally {
    if (Test-Path -LiteralPath $preflightRoot) {
        Remove-Item -LiteralPath $preflightRoot -Recurse -Force -ErrorAction SilentlyContinue
    }
}

}

# Never include credential helper output or HTTP response bodies in errors.
try { $credLines = "protocol=https`nhost=github.com`n" | git credential fill 2>$null }
catch { throw "GitHub credential lookup failed." }
if ($LASTEXITCODE -ne 0) { throw "GitHub credential lookup failed." }
$token = ($credLines | Where-Object { $_ -match "^password=" } | Select-Object -First 1) -replace "^password=", ""
if ([string]::IsNullOrEmpty($token)) {
    Write-Error "No GitHub token found. Check Git Credential Manager authentication for github.com."
    exit 1
}

$headers = @{
    Authorization = "Bearer $token"
    Accept        = "application/vnd.github+json"
    "User-Agent"  = "ps-cg"
}

function Invoke-CgReleaseApi {
    <# Make one bounded API request. Never expose remote error bodies or credentials. #>
    param([string]$Uri, [string]$Method = "Get", [string]$Body, [switch]$AllowNotFound)
    $arguments = @{ Uri = $Uri; Method = $Method; Headers = $headers; MaximumRedirection = 0; TimeoutSec = 60 }
    if ($Method -eq "Post") {
        $arguments.Body = [System.Text.Encoding]::UTF8.GetBytes($Body)
        $arguments.ContentType = "application/json; charset=utf-8"
    }
    try { return Invoke-RestMethod @arguments }
    catch {
        $status = $null
        if ($_.Exception.PSObject.Properties["Response"] -and $_.Exception.Response) {
            $status = [int]$_.Exception.Response.StatusCode
        }
        if ($AllowNotFound -and $status -eq 404) { return $null }
        throw "GitHub $Method request failed (HTTP $status). Remote error details suppressed."
    }
}

function Get-CgRepositoryRuleset {
    param(
        [string]$RulesetName,
        [string]$RulesetTarget
    )

    for ($attempt = 1; $attempt -le 3; $attempt++) {
        $summaryResponse = Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/rulesets"
        $summaries = @($summaryResponse)
        $match = @()
        foreach ($summary in $summaries) {
            if ($summary.name -ceq $RulesetName -and
                $summary.target -ceq $RulesetTarget -and
                $summary.enforcement -ceq "active") {
                $match += $summary
            }
        }
        if ($match.Count -eq 1) {
            $detail = Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/rulesets/$($match[0].id)"
            $properties = @($detail.PSObject.Properties.Name)
            if ($properties -ccontains "rules" -and
                $properties -ccontains "conditions" -and
                $properties -ccontains "bypass_actors" -and
                $properties -ccontains "current_user_can_bypass") {
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
if ($ruleTypes -cnotcontains "update") { $tagRuleProblems += "missing update rule" }
if ($ruleTypes -cnotcontains "deletion") { $tagRuleProblems += "missing deletion rule" }
if ($ruleTypes -cnotcontains "non_fast_forward") { $tagRuleProblems += "missing non_fast_forward rule" }
if ($includedRefs -cnotcontains "refs/tags/v*") { $tagRuleProblems += "missing refs/tags/v* include" }
if ($excludedRefs.Count -ne 0) { $tagRuleProblems += "has excluded refs" }
if ($bypassActors.Count -ne 0) { $tagRuleProblems += "has bypass actors" }
if ($currentUserCanBypass -cne "never") { $tagRuleProblems += "current user can bypass ($currentUserCanBypass)" }
if ($tagRuleProblems.Count -ne 0) {
    throw "'Protect release tags' is invalid: $($tagRuleProblems -join '; ')."
}

$creationRuleset = Get-CgRepositoryRuleset -RulesetName "Restrict release tag creation" -RulesetTarget "tag"
$creationRuleTypes = @($creationRuleset.rules | ForEach-Object { [string]$_.type })
$creationIncludes = @($creationRuleset.conditions.ref_name.include | ForEach-Object { [string]$_ })
$creationExcludes = @($creationRuleset.conditions.ref_name.exclude | ForEach-Object { [string]$_ })
$creationBypass = @($creationRuleset.bypass_actors)
if ($creationRuleTypes -cnotcontains "creation" -or
    $creationIncludes -cnotcontains "refs/tags/v*" -or
    $creationExcludes.Count -ne 0 -or
    $creationBypass.Count -ne 1 -or
    [string]$creationBypass[0].actor_type -cne "RepositoryRole" -or
    [int]$creationBypass[0].actor_id -ne 5 -or
    [string]$creationBypass[0].bypass_mode -cne "always") {
    throw "'Restrict release tag creation' must limit refs/tags/v* creation to repository administrators."
}

$devRuleset = Get-CgRepositoryRuleset -RulesetName "Protect dev" -RulesetTarget "branch"
$devRuleTypes = @($devRuleset.rules | ForEach-Object { [string]$_.type })
$devIncludes = @($devRuleset.conditions.ref_name.include | ForEach-Object { [string]$_ })
$devExcludes = @($devRuleset.conditions.ref_name.exclude | ForEach-Object { [string]$_ })
$devBypass = @($devRuleset.bypass_actors)
if ($devRuleTypes -cnotcontains "deletion" -or
    $devRuleTypes -cnotcontains "non_fast_forward" -or
    $devIncludes -cnotcontains "refs/heads/dev" -or
    $devExcludes.Count -ne 0 -or
    $devBypass.Count -ne 0 -or
    [string]$devRuleset.current_user_can_bypass -cne "never") {
    throw "'Protect dev' must block deletion and non-fast-forward updates without exclusions or bypass actors."
}

function Assert-CgReleaseMetadata {
    <# Validate required public fields without boolean coercion or partial responses. #>
    param($Release, [string]$ExpectedTag, [string]$ExpectedName, [string]$ExpectedCommit,
        [string]$ExpectedUrl, [switch]$CheckBody)
    if ($null -eq $Release) { throw "Required GitHub Release is absent." }
    foreach ($field in @("id", "html_url", "tag_name", "name", "body", "target_commitish", "prerelease", "draft", "published_at")) {
        if (-not $Release.PSObject.Properties[$field] -or $null -eq $Release.$field) {
            throw "GitHub Release is missing required field '$field'."
        }
    }
    $publishedAt = [datetimeoffset]::MinValue
    if ([string]$Release.id -notmatch '^[1-9][0-9]*$' -or
        $Release.draft -isnot [bool] -or $Release.draft -or
        $Release.prerelease -isnot [bool] -or
        $Release.prerelease -ne ($ExpectedTag -cmatch '^v\d+\.\d+\.\d+\.\d+$') -or
        -not [datetimeoffset]::TryParse([string]$Release.published_at, [ref]$publishedAt) -or
        [string]$Release.html_url -cne $ExpectedUrl -or
        [string]$Release.tag_name -cne $ExpectedTag -or
        [string]$Release.name -cne $ExpectedName -or
        [string]$Release.target_commitish -cne $ExpectedCommit -or
        ($CheckBody -and (ConvertTo-CgNormalizedReleaseText $Release.body) -cne (ConvertTo-CgNormalizedReleaseText $notes))) {
        throw "GitHub Release for '$ExpectedTag' does not match the requested immutable release metadata."
    }
}

function Get-CgPublishedReleases {
    <# Paginate authenticated releases, including drafts; reject duplicate identities. #>
    $byTag = @{}
    for ($page = 1; $page -le 100; $page++) {
        # Assign first: Invoke-RestMethod emits the JSON array as one pipeline object.
        $pageResponse = Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases?per_page=100&page=$page"
        if ($null -eq $pageResponse) { throw "Incomplete GitHub release list." }
        $items = @($pageResponse)
        foreach ($item in $items) {
            if ($null -eq $item -or -not $item.PSObject.Properties["tag_name"] -or
                [string]::IsNullOrWhiteSpace([string]$item.tag_name)) { throw "Incomplete GitHub release list." }
            $key = [string]$item.tag_name
            if ($byTag.ContainsKey($key)) { throw "Duplicate GitHub Release entries for '$key'." }
            $byTag[$key] = $item
        }
        if ($items.Count -lt 100) { return $byTag }
    }
    throw "GitHub release list exceeded the bounded history scan."
}

function Get-CgReleaseReservation {
    <#
    .SYNOPSIS
    Re-read both Release surfaces within a fixed bound; never write remote state.
    .PARAMETER RaceAttempts
    Maximum reads of each surface. Production uses five attempts.
    .PARAMETER RaceDelaySeconds
    Delay between inconsistent pairs. Tests can use zero without weakening checks.
    .EXAMPLE
    Get-CgReleaseReservation -RaceAttempts 1 -RaceDelaySeconds 0
    #>
    param(
        [ValidateRange(1, 5)][int]$RaceAttempts = 5,
        [ValidateRange(0, 15)][int]$RaceDelaySeconds = 15
    )
    $conflict = ''
    for ($attempt = 1; $attempt -le $RaceAttempts; $attempt++) {
        $conflict = "Conflicting GitHub Release lookup and list for '$Tag'."
        $release = Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases/tags/$Tag" -AllowNotFound
        $listed = Get-CgPublishedReleases
        if ($null -eq $release -and -not $listed.ContainsKey($Tag)) { return $null }
        if ($null -ne $release -and $listed.ContainsKey($Tag)) {
            $consistent = $true
            foreach ($field in @('id', 'html_url', 'tag_name', 'name', 'body', 'target_commitish', 'prerelease', 'draft', 'published_at')) {
                # Malformed responses are not propagation races; preserve strict metadata errors.
                if (-not $release.PSObject.Properties[$field] -or -not $listed[$Tag].PSObject.Properties[$field]) {
                    foreach ($item in @($release, $listed[$Tag])) {
                        Assert-CgReleaseMetadata -Release $item -ExpectedTag $Tag -ExpectedName $Name `
                            -ExpectedCommit $headCommit -ExpectedUrl $recordedPayload.url -CheckBody
                    }
                }
                if ((ConvertTo-CgNormalizedReleaseText $release.$field) -cne
                    (ConvertTo-CgNormalizedReleaseText $listed[$Tag].$field)) { $consistent = $false }
            }
            if ($consistent) {
                foreach ($item in @($release, $listed[$Tag])) {
                    Assert-CgReleaseMetadata -Release $item -ExpectedTag $Tag -ExpectedName $Name `
                        -ExpectedCommit $headCommit -ExpectedUrl $recordedPayload.url -CheckBody
                }
                return $release
            }
            if ($release.id -ne $listed[$Tag].id) { $conflict = "Conflicting GitHub Release IDs for '$Tag'." }
        }
        if ($attempt -lt $RaceAttempts -and $RaceDelaySeconds -gt 0) { Start-Sleep -Seconds $RaceDelaySeconds }
    }
    throw "$conflict Reconciliation stopped after $RaceAttempts attempts; these checks were read-only. Inspect the tag and Release state read-only first. Then, only with separate authorization, use /cg-release --legacy-bridge --resume $Tag before cutover or /cg-release --legacy-recovery --resume $Tag for authorized recovery. Resume requires confirmation and may run Reserve or Finalize; it is not read-only."
}

$immutablePayloads = @(Get-ChildItem -LiteralPath (Join-Path $PSScriptRoot "releases") -Filter "v*.json" | ForEach-Object {
    Get-Content -LiteralPath $_.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
} | Sort-Object publishedAt -Descending)
if ($immutablePayloads.Count -lt 1 -or [string]$immutablePayloads[0].tag -cne $Tag) {
    throw "Target tag '$Tag' must be the newest immutable release payload."
}
$publishedByTag = Get-CgPublishedReleases
foreach ($record in @($immutablePayloads | Select-Object -Skip 1)) {
    $recordTag = [string]$record.tag
    if (-not $publishedByTag.ContainsKey($recordTag)) {
        throw "Durable release payload '$recordTag' has no published GitHub Release. Repair historical release records before continuing."
    }
    $recordCommit = git -C $PSScriptRoot rev-parse --verify "refs/tags/$recordTag^{commit}" 2>$null
    if ($LASTEXITCODE -ne 0) { throw "Cannot resolve historical tag '$recordTag'." }
    Assert-CgReleaseMetadata -Release $publishedByTag[$recordTag] -ExpectedTag $recordTag `
        -ExpectedName $record.name -ExpectedCommit $recordCommit -ExpectedUrl $record.url
}
$existingRelease = Get-CgReleaseReservation
if ($null -ne $existingRelease -and $null -eq $remoteTag) { throw "Existing Release has no matching remote tag." }
$null = Assert-CgLegacyAuthority -Operation $LegacyOperation -ReleaseTag $Tag -Commit $headCommit -Object $tagObject -RemoteTag $remoteTag -SourceBranch $releaseBranch
$gateCompleted = $true
} finally {
    Write-CgReleaseTiming -Stage gates -Clock $gateClock -Completed $gateCompleted
}

if ($Phase -eq "Reserve") {
    $publicationClock = $null
    if ($Timing) { $publicationClock = [System.Diagnostics.Stopwatch]::StartNew() }
    $publicationCompleted = $false
    try {
    $reservationStatus = "EXISTS"
    # Finish every local/payload/API preflight before the first publication operation.
    $payload = ConvertTo-Json -InputObject @{
        tag_name = $Tag; target_commitish = $headCommit; name = $Name
        body = $notes; draft = $false; prerelease = $releasePrerelease
        make_latest = "false"
    }
    Assert-CgRemoteReleaseLineage -ExpectedCommit $headCommit -Branch $releaseBranch -RequireTip:($null -eq $remoteTag)
    $authority = Assert-CgLegacyAuthority -Operation $LegacyOperation -ReleaseTag $Tag -Commit $headCommit -Object $tagObject -RemoteTag $remoteTag -SourceBranch $releaseBranch
    if (-not $isPrereleaseTag) { Assert-CgStableDocsContract -ExpectedCommit $headCommit -Authority $authority }
    $currentAuthority = Assert-CgLegacyAuthority -Operation $LegacyOperation -ReleaseTag $Tag -Commit $headCommit -Object $tagObject -RemoteTag $remoteTag -SourceBranch $releaseBranch
    if ($currentAuthority.Commit -cne $authority.Commit -or $currentAuthority.Branch -cne $authority.Branch) {
        throw 'Protected controller authority changed after docs-contract verification.'
    }
    if ($null -eq $remoteTag) {
        # No distributed atomicity: after an uncertain push, read back exact identity.
        try { git -C $PSScriptRoot push origin --no-follow-tags "$tagObject`:refs/tags/$Tag" 2>$null | Out-Null }
        catch { } # The exact read-back below, not the transport result, decides success.
    }
    try { Assert-CgRemoteTagCommit -ReleaseTag $Tag -ExpectedCommit $headCommit }
    catch {
        # Even an uncertain push that cannot be verified gets a read-only Release lookup.
        $null = Get-CgReleaseReservation
        throw "Reservation stopped: remote tag identity could not be confirmed. No Release mutation was attempted."
    }
    if ($null -eq $existingRelease) {
        Assert-CgRemoteReleaseLineage -ExpectedCommit $headCommit -Branch $releaseBranch
        $null = Assert-CgLegacyAuthority -Operation $LegacyOperation -ReleaseTag $Tag -Commit $headCommit -Object $tagObject -RemoteTag $remoteTag -SourceBranch $releaseBranch
        # One POST only. Reconcile even a lost response before any later invocation retries.
        try {
            $response = Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases" -Method Post -Body $payload
            Assert-CgReleaseMetadata -Release $response -ExpectedTag $Tag -ExpectedName $Name `
                -ExpectedCommit $headCommit -ExpectedUrl $recordedPayload.url -CheckBody
        } catch {
            Assert-CgRemoteTagCommit -ReleaseTag $Tag -ExpectedCommit $headCommit
            $existingRelease = Get-CgReleaseReservation
            if ($null -eq $existingRelease) {
                throw "Reservation is incomplete: exact remote tag exists but no Release was observed. Resume Reserve to reconcile before retry; do not move or delete the tag."
            }
        }
        Assert-CgRemoteTagCommit -ReleaseTag $Tag -ExpectedCommit $headCommit
        $existingRelease = Get-CgReleaseReservation
        if ($null -eq $existingRelease) { throw "Release creation could not be confirmed. Resume Reserve; tag is unchanged." }
        $reservationStatus = "CREATED"
    }
    "$reservationStatus|$($existingRelease.id)|$($existingRelease.html_url)" | Set-Content $resultFile
    Write-Host "RESERVED ($reservationStatus): $Tag. Finalize and evidence commit are still required; no latest promotion was requested."
    $publicationCompleted = $true
    return
    } finally {
        Write-CgReleaseTiming -Stage publication -Clock $publicationClock -Completed $publicationCompleted
    }
}

# Finalize is read-only remotely. Any downstream failure leaves the pair intact.
$recoveryClock = $null
if ($Timing) { $recoveryClock = [System.Diagnostics.Stopwatch]::StartNew() }
$recoveryCompleted = $false
try {
if ($null -eq $existingRelease) { throw "Finalize requires an existing exact matching Release. Run Reserve first." }
$encodedTag = [uri]::EscapeDataString($Tag)
$buildRunsUri = "https://api.github.com/repos/GPID-WB/compound-gpid/actions/workflows/release-docs.yml/runs?event=push&branch=$encodedTag&per_page=100"
if ($BuildRunId) {
    $buildCandidates = @(Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/actions/runs/$BuildRunId")
} else {
    $buildRuns = Invoke-CgReleaseApi -Uri $buildRunsUri
    $buildCandidates = @($buildRuns.workflow_runs)
}
$matchingBuildRuns = @($buildCandidates | Where-Object {
    $_.head_sha -ceq $headCommit -and $_.head_branch -ceq $Tag -and
    $_.event -ceq "push" -and $_.path -ceq ".github/workflows/release-docs.yml"
})
if ($matchingBuildRuns.Count -ne 1 -or $matchingBuildRuns[0].id -le 0 -or
    ($BuildRunId -and $matchingBuildRuns[0].id -ne $BuildRunId) -or
    $matchingBuildRuns[0].status -cne "completed" -or $matchingBuildRuns[0].conclusion -cne "success") {
    throw "A successful release-docs.yml push run for exact tag '$Tag' at $headCommit is required for Finalize."
}
if ($isPrereleaseTag) {
    # A successful wrapper can contain a skipped release build and a green dev job.
    # Bind the actual release build and upload to this exact workflow attempt.
    $buildRun = $matchingBuildRuns[0]
    if ($buildRun.run_attempt -isnot [int] -and $buildRun.run_attempt -isnot [long] -or $buildRun.run_attempt -le 0) {
        throw 'Exact release-docs build run attempt is required.'
    }
    $jobs = Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/actions/runs/$($buildRun.id)/attempts/$($buildRun.run_attempt)/jobs?per_page=100&page=1"
    if ($jobs.total_count -ne @($jobs.jobs).Count -or $jobs.total_count -gt 100) { throw 'Incomplete release-docs build job inventory.' }
    $releaseJobs = @($jobs.jobs | Where-Object { $_.name -ceq 'build' })
    if ($releaseJobs.Count -ne 1 -or $releaseJobs[0].id -le 0 -or
        $releaseJobs[0].run_id -ne $buildRun.id -or $releaseJobs[0].run_attempt -ne $buildRun.run_attempt -or
        $releaseJobs[0].head_sha -cne $headCommit -or $releaseJobs[0].status -cne 'completed' -or
        $releaseJobs[0].conclusion -cne 'success') { throw 'Exact successful release-docs build job is required.' }
    $releaseJob = $releaseJobs[0]
    $previousStep = 0
    foreach ($stepName in @('Check out immutable tag commit', 'Set up Node', 'Validate tag, lineage, and durable payload',
        'Build complete documentation tree', 'Validate tagged documentation site', 'Require isolated release metadata',
        'Upload isolated release documentation artifact')) {
        $steps = @($releaseJob.steps | Where-Object { $_.name -ceq $stepName })
        if ($steps.Count -ne 1 -or $steps[0].status -cne 'completed' -or $steps[0].conclusion -cne 'success' -or
            $steps[0].number -le $previousStep) { throw "Successful release-docs build step '$stepName' is required in order." }
        $previousStep = $steps[0].number
    }
    $inventory = Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/actions/runs/$($buildRun.id)/artifacts?per_page=100&page=1"
    if ($inventory.total_count -ne @($inventory.artifacts).Count -or $inventory.total_count -gt 100) { throw 'Incomplete release-docs artifact inventory.' }
    $artifacts = @($inventory.artifacts | Where-Object { $_.name -ceq 'release-docs-site' })
    if ($artifacts.Count -ne 1 -or $artifacts[0].id -le 0 -or $artifacts[0].expired -ne $false -or
        $artifacts[0].workflow_run.id -ne $buildRun.id -or $artifacts[0].workflow_run.head_sha -cne $headCommit -or
        $artifacts[0].digest -cnotmatch '^sha256:[0-9a-f]{64}$') { throw 'Exact release-docs build artifact is required.' }
    try {
        $started = [DateTimeOffset]::Parse($releaseJob.started_at)
        $completed = [DateTimeOffset]::Parse($releaseJob.completed_at)
        $created = [DateTimeOffset]::Parse($artifacts[0].created_at)
        if ($completed -lt $started -or $created -lt $started -or $created -gt $completed) { throw 'outside attempt' }
    } catch { throw 'Release-docs build artifact must belong to the successful job attempt.' }
}
$historicalDeployment = $false
if (-not $isPrereleaseTag) {
$controllerRunName = "Deploy docs from $($matchingBuildRuns[0].id)"
$pagesRunsUri = "https://api.github.com/repos/GPID-WB/compound-gpid/actions/workflows/release-pages.yml/runs?event=workflow_run&per_page=100"
if ($PagesRunId) {
    $pagesCandidates = @(Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/actions/runs/$PagesRunId")
} else {
    $pagesRuns = Invoke-CgReleaseApi -Uri $pagesRunsUri
    $pagesCandidates = @($pagesRuns.workflow_runs)
}
$matchingPagesRuns = @($pagesCandidates | Where-Object {
    $_.name -ceq $controllerRunName -and $_.display_title -ceq $controllerRunName -and
    ($_.event -ceq "workflow_run" -or ($LegacyOperation -ceq 'Recovery' -and $PagesRunId -and $_.event -ceq 'workflow_dispatch')) -and
    $_.path -ceq ".github/workflows/release-pages.yml"
})
if ($matchingPagesRuns.Count -ne 1 -or $matchingPagesRuns[0].id -le 0 -or
    ($PagesRunId -and $matchingPagesRuns[0].id -ne $PagesRunId) -or
    $matchingPagesRuns[0].status -cne "completed" -or $matchingPagesRuns[0].conclusion -cne "success") {
    throw "A successful release-pages.yml controller run named '$controllerRunName' is required for Finalize."
}
$historicalDeployment = $matchingPagesRuns[0].event -ceq 'workflow_dispatch'
$authority = Assert-CgLegacyAuthority -Operation $LegacyOperation -ReleaseTag $Tag -Commit $headCommit -Object $tagObject -RemoteTag $remoteTag -SourceBranch $releaseBranch -RequireRecoveryRecord:$historicalDeployment
if ($historicalDeployment) {
    $recovery = $authority.Record
    $artifact = Invoke-CgReleaseApi -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/actions/artifacts/$($recovery.artifact_id)"
    if ($recovery.build_run_id -ne $matchingBuildRuns[0].id -or
        $matchingPagesRuns[0].head_sha -cne $authority.Commit -or $matchingPagesRuns[0].run_attempt -ne 1 -or
        $artifact.id -ne $recovery.artifact_id -or $artifact.name -cne 'release-docs-site' -or
        $artifact.workflow_run.id -ne $recovery.build_run_id -or $artifact.workflow_run.head_sha -cne $headCommit -or
        $artifact.digest -cne $recovery.artifact_digest -or $artifact.expired -ne $false) {
        throw 'Historical recovery deployment does not bind the exact immutable build and artifact.'
    }
}
$null = Assert-CgLegacyDeployment -Run $matchingPagesRuns[0] -Authority $authority
} else {
    # Option A: prereleases attest the exact tag build, not a full-site deployment.
    $authority = Assert-CgLegacyAuthority -Operation $LegacyOperation -ReleaseTag $Tag -Commit $headCommit -Object $tagObject -RemoteTag $remoteTag -SourceBranch $releaseBranch
}
Assert-CgRemoteTagCommit -ReleaseTag $Tag -ExpectedCommit $headCommit
$existingRelease = Get-CgReleaseReservation
if ($null -eq $existingRelease) { throw "Release reservation disappeared before finalization." }
Assert-CgRemoteReleaseLineage -ExpectedCommit $headCommit -Branch $releaseBranch
$finalAuthority = Assert-CgLegacyAuthority -Operation $LegacyOperation -ReleaseTag $Tag -Commit $headCommit -Object $tagObject -RemoteTag $remoteTag -SourceBranch $releaseBranch -RequireRecoveryRecord:$historicalDeployment
if ($finalAuthority.Commit -cne $authority.Commit -or $finalAuthority.Branch -cne $authority.Branch -or
    $finalAuthority.Actor -ne $authority.Actor -or
    ($historicalDeployment -and ($finalAuthority.Record | ConvertTo-Json -Depth 20 -Compress) -cne ($authority.Record | ConvertTo-Json -Depth 20 -Compress))) {
    throw 'Protected default or historical recovery authority changed before final attestation.'
}
Write-CgReleaseAttestation
"FINALIZED|$($existingRelease.id)|$($existingRelease.html_url)" | Set-Content $resultFile
Write-Host "FINALIZED: $Tag. Commit canonical and generated evidence before lifecycle completion; latest promotion was not performed."
$recoveryCompleted = $true
} finally {
    Write-CgReleaseTiming -Stage recovery -Clock $recoveryClock -Completed $recoveryCompleted
}
