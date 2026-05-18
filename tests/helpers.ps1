# tests/helpers.ps1
# Shared helper functions for Pester test files.
#
# Dot-source at the top of any test that needs these helpers:
#   . "$PSScriptRoot/helpers.ps1"

# Helper: extract the YAML frontmatter block from a markdown file
function Get-Frontmatter {
    param([string]$FilePath)
    $raw = Get-Content $FilePath -Raw -Encoding UTF8
    if ($raw -match '(?s)^---\s*\r?\n(.+?)\r?\n---') {
        return $Matches[1]
    }
    return ''
}

# Helper: extract the tools list from a frontmatter string
function Get-ToolsList {
    param([string]$Frontmatter)
    $line = ($Frontmatter -split '\r?\n' | Where-Object { $_ -match '^\s*tools:' } | Select-Object -First 1)
    if (-not $line) { return @() }
    # Match quoted tokens inside the brackets: 'agent', "read", etc.
    $tokens = [regex]::Matches($line, "['""](\w+)['""]") | ForEach-Object { $_.Groups[1].Value }
    return $tokens
}

# ---------------------------------------------------------------------------
# Shared platform detection (for test files that dot-source this helper)
# ---------------------------------------------------------------------------
# Note: No Set-StrictMode in Pester context -- $IsWindows/$IsMacOS return $null
# on PS 5.1 rather than throwing. Safe to use bare form here.
# Production scripts (link.ps1, unlink.ps1) MUST use the Test-Path guarded form.
$script:OnWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")
$script:OnMacOS   = ($IsMacOS   -eq $true)
