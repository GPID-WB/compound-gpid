<#
.SYNOPSIS
Creates a GitHub Release for GPID-WB/compound-gpid via the GitHub API.

.DESCRIPTION
Creates a release for the specified git tag with optional draft/prerelease flags.
Retrieves credentials from Git Credential Manager (idempotent -- skips if release exists).
Writes release metadata to release-result.txt next to this script.

.PARAMETER Tag
The git tag in semver format (v<major>.<minor>.<patch>). Required.

.PARAMETER Name
The GitHub Release name/title. Required.

.PARAMETER NotesFile
Path to a Markdown file whose content becomes the release body. Required.

.PARAMETER Draft
If present, creates the release as a draft (not yet published).

.PARAMETER Prerelease
If present, marks the release as a prerelease.

.EXAMPLE
.\create-release.ps1 -Tag v0.0.6 -Name "v0.0.6 - My feature" -NotesFile RELEASE_NOTES.md

.EXAMPLE
.\create-release.ps1 -Tag v0.0.6 -Name "v0.0.6 - Draft" -NotesFile RELEASE_NOTES.md -Draft

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
if ($Tag -notmatch '^v\d+\.\d+\.\d+(\.\d+)?$') {
    Write-Error ('Invalid tag format ''' + $Tag + '''. Expected v<major>.<minor>.<patch> or v<major>.<minor>.<patch>.<dev> (e.g. v0.0.6 or v0.12.0.9000).')
    exit 1
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
$tagCommit = (git -C $PSScriptRoot rev-parse --verify "$Tag`^{commit}" 2>$null | Select-Object -First 1)
$tagExitCode = (Get-Variable -Name LASTEXITCODE -ValueOnly -ErrorAction SilentlyContinue)
if (($null -ne $tagExitCode -and [int]$tagExitCode -ne 0) -or [string]::IsNullOrWhiteSpace($tagCommit)) {
    throw "Release tag '$Tag' does not resolve to a commit."
}
$headCommit = (git -C $PSScriptRoot rev-parse --verify "HEAD^{commit}" 2>$null | Select-Object -First 1)
$headExitCode = (Get-Variable -Name LASTEXITCODE -ValueOnly -ErrorAction SilentlyContinue)
if (($null -ne $headExitCode -and [int]$headExitCode -ne 0) -or [string]::IsNullOrWhiteSpace($headCommit)) {
    throw "Could not resolve the current HEAD commit."
}
if ($headCommit.Trim() -ne $tagCommit.Trim()) {
    throw "Release checkout mismatch: tag '$Tag' resolves to $($tagCommit.Trim()) but HEAD is $($headCommit.Trim()). Check out the tag commit before releasing."
}
$worktreeChanges = @(git -C $PSScriptRoot status --porcelain --untracked-files=normal 2>$null)
$worktreeExitCode = (Get-Variable -Name LASTEXITCODE -ValueOnly -ErrorAction SilentlyContinue)
if ($null -ne $worktreeExitCode -and [int]$worktreeExitCode -ne 0) {
    throw "Could not verify that the release checkout is clean."
}
if ($worktreeChanges.Count -gt 0) {
    throw "Release checkout must be clean before testing tag '$Tag'."
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
$preflightTests = @(
    "scripts/tests/test_target_mapping.py",
    "scripts/tests/test_cg_generate_targets.py",
    "scripts/tests/test_target_path_safety.py",
    "scripts/tests/test_target_packaging.py",
    "scripts/tests/test_target_ownership.py",
    "scripts/tests/test_target_closure.py",
    "scripts/tests/test_target_determinism.py",
    "scripts/tests/test_target_drift.py",
    "scripts/tests/test_target_claude.py",
    "scripts/tests/test_target_codex.py",
    "scripts/tests/test_target_opencode.py"
) | ForEach-Object { Join-Path $PSScriptRoot $_ }
Write-Host "Running native packaging release preflight..." -ForegroundColor Cyan
$preflightExitCode = 0
& $pythonCommand -m pytest @preflightTests -q
$preflightExitCodeVariable = Get-Variable -Name LASTEXITCODE -ValueOnly -ErrorAction SilentlyContinue
if ($null -ne $preflightExitCodeVariable) {
    $preflightExitCode = [int]$preflightExitCodeVariable
}
if ($preflightExitCode -ne 0) {
    throw "Native packaging release preflight failed with exit code $preflightExitCode. Release publication is blocked."
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

# Output written next to this script so it's always findable regardless of the caller's cwd
$resultFile = Join-Path $PSScriptRoot "release-result.txt"

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

if ($null -ne $existingRelease) {
    if (-not $existingRelease.id -or -not $existingRelease.html_url) {
        Write-Error "GitHub API response missing expected fields (id, html_url). Raw: $($existingRelease | ConvertTo-Json)"
        exit 1
    }
    "EXISTS|$($existingRelease.id)|$($existingRelease.html_url)" | Set-Content $resultFile
    exit 0
}

# Create the release
$payload = ConvertTo-Json -InputObject @{
    tag_name   = $Tag
    name       = $Name
    body       = $notes
    draft      = $Draft.IsPresent
    prerelease = $Prerelease.IsPresent
}

# ConvertTo-Json escapes all non-ASCII as \uXXXX, so $payload is pure ASCII --
# safe to pass as a string directly. The ETS issue is on $notes (fixed above),
# not on the serialized JSON string itself.
$response = Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases" `
    -Method Post -Headers $headers -Body $payload -ContentType "application/json"

if (-not $response.id -or -not $response.html_url) {
    Write-Error "GitHub API response missing expected fields (id, html_url). Raw: $($response | ConvertTo-Json)"
    exit 1
}

"CREATED|$($response.id)|$($response.html_url)" | Set-Content $resultFile
