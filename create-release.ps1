<#
.SYNOPSIS
Creates a GitHub Release for GPID-WB/compound-gpid via the GitHub API.

.DESCRIPTION
Creates a release for the specified git tag with optional draft/prerelease flags.
Retrieves credentials from Git Credential Manager (idempotent — skips if release exists).
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
  EXISTS|<id>|<url>   — release already existed
  CREATED|<id>|<url>  — release was created
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)][string]$Tag,
    [Parameter(Mandatory)][string]$Name,
    [Parameter(Mandatory)][string]$NotesFile,
    [switch]$Draft,
    [switch]$Prerelease
)

$ErrorActionPreference = "Stop"

# Enforce semver tag format (v<major>.<minor>.<patch>) for consistency with GitHub Release API
if ($Tag -notmatch '^v\d+\.\d+\.\d+$') {
    Write-Error "Invalid tag format '$Tag'. Expected v<major>.<minor>.<patch> (e.g. v0.0.6)."
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
$notes = Get-Content -Path $NotesFile -Raw
if ([string]::IsNullOrWhiteSpace($notes)) {
    Write-Error "Notes file is empty: $NotesFile"
    exit 1
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
    # Only a 404 means "release doesn't exist" — re-throw all other HTTP errors
    $status = $_.Exception.Response?.StatusCode.value__
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

$response = Invoke-RestMethod -Uri "https://api.github.com/repos/GPID-WB/compound-gpid/releases" `
    -Method Post -Headers $headers -Body $payload -ContentType "application/json"

if (-not $response.id -or -not $response.html_url) {
    Write-Error "GitHub API response missing expected fields (id, html_url). Raw: $($response | ConvertTo-Json)"
    exit 1
}

"CREATED|$($response.id)|$($response.html_url)" | Set-Content $resultFile
