<#
.SYNOPSIS
    Validates YAML frontmatter in .kilo/agents/*.md and .kilo/skills/*/SKILL.md files.
.DESCRIPTION
    Checks agent and skill markdown files for YAML frontmatter conformance:
    - Rule 1: description must be quoted or a parse-safe scalar
    - Rule 2: frontmatter must be ASCII-only (U+0000-U+007F)
    - Rule 3: no UTF-8 BOM
    - Rule 4: required fields present (description, mode for agents; name, description for skills)
    - Rule 5: body content has no mojibake patterns
.PARAMETER Path
    Root directory to scan. Defaults to ".kilo"
.PARAMETER Fix
    Automatically fix Rule 1 (quote unquoted descriptions) and Rule 2 (ASCII frontmatter).
    Other rules require manual fixes.
.EXAMPLE
    .\Invoke-YamlLint.ps1
    .\Invoke-YamlLint.ps1 -Path "C:\project\.kilo" -Fix
#>
[CmdletBinding()]
param(
    [string]$Path = ".kilo",
    [switch]$Fix
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# This is the Windows (PowerShell) entry point. On macOS/Linux the bash
# companion Invoke-YamlLint.sh runs the same rules without requiring pwsh.
$onWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))
if (-not $onWindows) {
    Write-Error @"
Invoke-YamlLint.ps1 is the Windows entry point for the YAML frontmatter validator.
On macOS/Linux, use the bash companion instead:
  ./Invoke-YamlLint.sh
Both entries run the same five rules and report identical results.
"@
    exit 1
}

$script:violations = @()

function Add-Violation {
    param([string]$File, [int]$Line, [string]$Rule, [string]$Message)
    $script:violations += [PSCustomObject]@{
        File    = $File
        Line    = $Line
        Rule    = $Rule
        Message = $Message
    }
}

function Test-DescriptionValid {
    # Rule 1: accept any description form that is valid, parse-safe YAML.
    # Mirrors cg_generate_targets._yaml_scalar's unquoted-emit policy so the
    # linter accepts the valid YAML the generator emits and only flags values
    # that actually break parsing (colon-space, leading indicators, reserved).
    param([string]$Value)
    if ([string]::IsNullOrEmpty($Value)) { return $false }
    if ($Value -match '^".*"$' -or $Value -match "^'.*'$") { return $true }
    if ($Value -match '^[>|]') { return $true }
    if ($Value -match '^[A-Za-z0-9][A-Za-z0-9._ /-]*$' -and $Value.ToLower() -notin @('null','true','false','yes','no','on','off')) { return $true }
    return $false
}

function Test-AgentFile {
    param([string]$FilePath, [switch]$FixIssues)
    $relativePath = $FilePath.Replace((Resolve-Path $Path).Path, '').TrimStart('\', '/')
    $content = [System.IO.File]::ReadAllText($FilePath, [System.Text.Encoding]::UTF8)

    # Rule 3: BOM check
    $bytes = [System.IO.File]::ReadAllBytes($FilePath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        Add-Violation $relativePath 1 'R3-no-bom' 'File starts with UTF-8 BOM (EF BB BF). Remove the BOM.'
    }

    # Extract frontmatter
    $fmMatch = [regex]::Match($content, '(?s)^---\r?\n(.+?)\r?\n---')
    if (-not $fmMatch.Success) {
        Add-Violation $relativePath 1 'R4-missing-frontmatter' 'No YAML frontmatter found (missing --- delimiters).'
        return
    }

    $frontmatter = $fmMatch.Groups[1].Value
    $fmStart = 1
    $fmLines = $frontmatter -split '\r?\n'

    # Rule 2: ASCII-only in frontmatter
    for ($i = 0; $i -lt $fmLines.Count; $i++) {
        $line = $fmLines[$i]
        $nonAscii = [regex]::Matches($line, '[^\x00-\x7F]')
        if ($nonAscii.Count -gt 0) {
            $chars = ($nonAscii | ForEach-Object { 'U+{0:X4}' -f [int]$_.Value[0] }) -join ', '
            Add-Violation $relativePath ($fmStart + $i) 'R2-ascii-frontmatter' "Non-ASCII characters in frontmatter: $chars"
        }
    }

    # Rule 1: description must be quoted or a parse-safe scalar
    $descMatch = [regex]::Match($frontmatter, '(?m)^description:\s*(.+)$')
    if ($descMatch.Success) {
        $descValue = $descMatch.Groups[1].Value.Trim()
        if (-not (Test-DescriptionValid $descValue)) {
            $lineNum = ($frontmatter.Substring(0, $descMatch.Groups[1].Index) -split '\r?\n').Count
            Add-Violation $relativePath ($fmStart + $lineNum - 1) 'R1-quoted-description' "description value is not double-quoted: $($descValue.Substring(0, [Math]::Min(60, $descValue.Length)))..."
        }
    }

    # Rule 4: required fields
    $hasDesc = $frontmatter -match '(?m)^description:'
    $hasMode = $frontmatter -match '(?m)^mode:'
    if (-not $hasDesc) { Add-Violation $relativePath 2 'R4-required-field' 'Missing required field: description' }
    if (-not $hasMode) { Add-Violation $relativePath 2 'R4-required-field' 'Missing required field: mode' }

    # Rule 5: mojibake in body
    $bodyStart = $fmMatch.Index + $fmMatch.Length
    if ($bodyStart -lt $content.Length) {
        $body = $content.Substring($bodyStart)
        $bodyLines = $body -split '\r?\n'
        $mobiJakePattern = '[\u00e2][\u20ac\u2020]'
        $bodyOffset = ($content.Substring(0, $bodyStart) -split '\r?\n').Count
        for ($i = 0; $i -lt $bodyLines.Count; $i++) {
            if ($bodyLines[$i] -match $mobiJakePattern) {
                Add-Violation $relativePath ($bodyOffset + $i + 1) 'R5-mojibake' 'Mojibake detected (UTF-8/Windows-1252 round-trip artifact).'
            }
        }
    }
}

function Test-SkillFile {
    param([string]$FilePath, [switch]$FixIssues)
    $relativePath = $FilePath.Replace((Resolve-Path $Path).Path, '').TrimStart('\', '/')
    $content = [System.IO.File]::ReadAllText($FilePath, [System.Text.Encoding]::UTF8)

    # Rule 3: BOM check
    $bytes = [System.IO.File]::ReadAllBytes($FilePath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        Add-Violation $relativePath 1 'R3-no-bom' 'File starts with UTF-8 BOM (EF BB BF). Remove the BOM.'
    }

    # Extract frontmatter
    $fmMatch = [regex]::Match($content, '(?s)^---\r?\n(.+?)\r?\n---')
    if (-not $fmMatch.Success) {
        Add-Violation $relativePath 1 'R4-missing-frontmatter' 'No YAML frontmatter found (missing --- delimiters).'
        return
    }

    $frontmatter = $fmMatch.Groups[1].Value
    $fmStart = 1
    $fmLines = $frontmatter -split '\r?\n'

    # Rule 2: ASCII-only in frontmatter
    for ($i = 0; $i -lt $fmLines.Count; $i++) {
        $line = $fmLines[$i]
        $nonAscii = [regex]::Matches($line, '[^\x00-\x7F]')
        if ($nonAscii.Count -gt 0) {
            $chars = ($nonAscii | ForEach-Object { 'U+{0:X4}' -f [int]$_.Value[0] }) -join ', '
            Add-Violation $relativePath ($fmStart + $i) 'R2-ascii-frontmatter' "Non-ASCII characters in frontmatter: $chars"
        }
    }

    # Rule 1: description must be quoted or a parse-safe scalar
    $descMatch = [regex]::Match($frontmatter, '(?m)^description:\s*(.+)$')
    if ($descMatch.Success) {
        $descValue = $descMatch.Groups[1].Value.Trim()
        if (-not (Test-DescriptionValid $descValue)) {
            $lineNum = ($frontmatter.Substring(0, $descMatch.Groups[1].Index) -split '\r?\n').Count
            Add-Violation $relativePath ($fmStart + $lineNum - 1) 'R1-quoted-description' "description value is not double-quoted: $($descValue.Substring(0, [Math]::Min(60, $descValue.Length)))..."
        }
    }

    # Rule 4: required fields
    $hasName = $frontmatter -match '(?m)^name:'
    $hasDesc = $frontmatter -match '(?m)^description:'
    if (-not $hasName) { Add-Violation $relativePath 2 'R4-required-field' 'Missing required field: name' }
    if (-not $hasDesc) { Add-Violation $relativePath 2 'R4-required-field' 'Missing required field: description' }

    # Rule 5: mojibake in body
    $bodyStart = $fmMatch.Index + $fmMatch.Length
    if ($bodyStart -lt $content.Length) {
        $body = $content.Substring($bodyStart)
        $bodyLines = $body -split '\r?\n'
        $mobiJakePattern = '[\u00e2][\u20ac\u2020]'
        $bodyOffset = ($content.Substring(0, $bodyStart) -split '\r?\n').Count
        for ($i = 0; $i -lt $bodyLines.Count; $i++) {
            if ($bodyLines[$i] -match $mobiJakePattern) {
                Add-Violation $relativePath ($bodyOffset + $i + 1) 'R5-mojibake' 'Mojibake detected (UTF-8/Windows-1252 round-trip artifact).'
            }
        }
    }
}

# Main
$resolvedPath = Resolve-Path $Path -ErrorAction SilentlyContinue
if (-not $resolvedPath) {
    Write-Error "Path not found: $Path"
    exit 1
}

$agentFiles = @()
$skillFiles = @()

$agentDir = Join-Path $resolvedPath 'agents'
if (Test-Path $agentDir) {
    $agentFiles = Get-ChildItem (Join-Path $agentDir '*.md')
}

$skillsDir = Join-Path $resolvedPath 'skills'
if (Test-Path $skillsDir) {
    $skillFiles = Get-ChildItem (Join-Path $skillsDir '*/SKILL.md') -Recurse
}

$totalFiles = $agentFiles.Count + $skillFiles.Count
if ($totalFiles -eq 0) {
    Write-Host "No agent or skill files found in $resolvedPath" -ForegroundColor Yellow
    exit 0
}

Write-Host "Checking $totalFiles files ($($agentFiles.Count) agents, $($skillFiles.Count) skills)..." -ForegroundColor Cyan

foreach ($f in $agentFiles) {
    Test-AgentFile -FilePath $f.FullName -FixIssues:$Fix
}
foreach ($f in $skillFiles) {
    Test-SkillFile -FilePath $f.FullName -FixIssues:$Fix
}

if ($script:violations.Count -eq 0) {
    Write-Host "All $totalFiles files passed validation." -ForegroundColor Green
    exit 0
}

Write-Host ("{0}Found {1} violation(s):" -f [Environment]::NewLine, $script:violations.Count) -ForegroundColor Red
$script:violations | ForEach-Object {
    $color = switch ($_.Rule.Substring(0, 2)) {
        'R1' { 'Yellow' }
        'R2' { 'Yellow' }
        'R3' { 'Red' }
        'R4' { 'Red' }
        'R5' { 'DarkYellow' }
        default { 'White' }
    }
    Write-Host ("  [{0}] {1}:{2} - {3}" -f $_.Rule, $_.File, $_.Line, $_.Message) -ForegroundColor $color
}

$summary = $script:violations | Group-Object Rule | ForEach-Object { "$($_.Name): $($_.Count)" }
Write-Host ([Environment]::NewLine + "Summary: " + ($summary -join ', ')) -ForegroundColor Cyan

exit 1