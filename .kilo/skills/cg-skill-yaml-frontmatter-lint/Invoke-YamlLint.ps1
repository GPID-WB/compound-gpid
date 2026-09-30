<#
.SYNOPSIS
    Validates YAML frontmatter in .kilo/agents/*.md and .kilo/skills/*/SKILL.md files.
.DESCRIPTION
    Checks agent and skill markdown files for YAML frontmatter conformance:
    - Rule 1: description must be double-quoted
    - Rule 2: frontmatter must be ASCII-only (U+0000-U+007F)
    - Rule 3: no UTF-8 BOM
    - Rule 4: required fields present (description, mode for agents; name, description for skills)
    - Rule 5: body content has no mojibake patterns
    - Rule 6: files use LF line endings only
.PARAMETER Path
    Root directory to scan. Defaults to ".kilo"
.PARAMETER Fix
    Reserved for parity with validate_yaml_frontmatter.py. Auto-correction is NOT
    implemented in this PowerShell entry: if -Fix is passed, a notice is printed and
    validation continues. Apply fixes manually, or use the Python validator
    (validate_yaml_frontmatter.py -Fix, or bash Invoke-YamlLint.sh -Fix on macOS/Linux).
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

function Get-DoubleQuotedDescriptionEnd {
    param([string[]]$Lines, [int]$Index)
    $colon = $Lines[$Index].IndexOf(':')
    if ($colon -lt 0) { return -1 }
    $candidate = $Lines[$Index].Substring($colon + 1).Trim()
    if (-not $candidate.StartsWith('"')) { return -1 }
    for ($cursor = $Index; $cursor -lt $Lines.Count; $cursor++) {
        if ($cursor -gt $Index) { $candidate += "`n" + $Lines[$cursor] }
        $folded = $candidate.Replace("`r", '').Replace("`n", ' ')
        if ($folded -match '^"(?:\\.|[^"\\])*"$') { return $cursor }
    }
    return -1
}

function Test-DoubleQuotedDescription {
    param([string[]]$Lines, [int]$Index)
    return (Get-DoubleQuotedDescriptionEnd -Lines $Lines -Index $Index) -ge 0
}

function Test-RootFieldLine {
    param([string]$Line, [string]$Key)
    $prefix = $Key + ':'
    if (-not $Line.StartsWith($prefix)) { return $false }
    if ($Line.Length -eq $prefix.Length) { return $true }
    return [char]::IsWhiteSpace($Line[$prefix.Length])
}

function Get-RootFieldIndices {
    param([string[]]$Lines, [string]$Key, [int]$DescriptionStart = -1, [int]$DescriptionEnd = -1)
    $indices = @()
    for ($index = 0; $index -lt $Lines.Count; $index++) {
        if ($DescriptionStart -ge 0 -and $DescriptionEnd -ge 0 -and $index -gt $DescriptionStart -and $index -le $DescriptionEnd) { continue }
        if (Test-RootFieldLine -Line $Lines[$index] -Key $Key) { $indices += $index }
    }
    return @($indices)
}

function ConvertFrom-CgYamlScalar {
    param([string]$Value)
    $scalar = ($Value -replace '\s+#.*$', '').Trim()
    if ($scalar -match '^"(?:\\.|[^"\\])*"$') {
        try { return [string]($scalar | ConvertFrom-Json) } catch { return $null }
    }
    if ($scalar -match "^'(?:''|[^'])*'$") { return $scalar.Substring(1, $scalar.Length - 2).Replace("''", "'") }
    return $scalar
}

function Test-AgentFile {
    param([string]$FilePath, [switch]$FixIssues, [switch]$RequireMode)
    $relativePath = $FilePath.Replace((Resolve-Path $Path).Path, '').TrimStart('\', '/')
    $content = [System.IO.File]::ReadAllText($FilePath, [System.Text.Encoding]::UTF8)

    # Rule 3: BOM check
    $bytes = [System.IO.File]::ReadAllBytes($FilePath)
    if ($bytes.Length -ge 3 -and $bytes[0] -eq 0xEF -and $bytes[1] -eq 0xBB -and $bytes[2] -eq 0xBF) {
        Add-Violation $relativePath 1 'R3-no-bom' 'File starts with UTF-8 BOM (EF BB BF). Remove the BOM.'
    }
    if ($bytes -contains 13) {
        Add-Violation $relativePath 1 'R6-lf-endings' 'File contains CR or CRLF line endings; use LF only.'
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

    # Rule 1: agent description may be double-quoted or a parse-safe scalar.
    # Line-scoped: a bare 'description:' with no value is reported, and the
    # value never absorbs the next line.
    $descIdx = -1
    $descEndIdx = -1
    for ($di = 0; $di -lt $fmLines.Count; $di++) {
        if (Test-RootFieldLine -Line $fmLines[$di] -Key 'description') { $descIdx = $di; break }
    }
    if ($descIdx -ge 0) {
        $colonIdx = $fmLines[$descIdx].IndexOf(':')
        $descValue = if ($colonIdx -ge 0) { $fmLines[$descIdx].Substring($colonIdx + 1).Trim() } else { '' }
        if ([string]::IsNullOrEmpty($descValue)) {
            Add-Violation $relativePath ($fmStart + $descIdx) 'R1-quoted-description' 'description value is empty (expected a double-quoted or parse-safe scalar).'
        }
        elseif (-not (Test-DoubleQuotedDescription -Lines $fmLines -Index $descIdx)) {
            Add-Violation $relativePath ($fmStart + $descIdx) 'R1-quoted-description' "description value is not double-quoted: $($descValue.Substring(0, [Math]::Min(60, $descValue.Length)))..."
        }
        else {
            $descEndIdx = Get-DoubleQuotedDescriptionEnd -Lines $fmLines -Index $descIdx
        }
    }

    # Rule 4: required fields
    $descIndices = @(Get-RootFieldIndices -Lines $fmLines -Key 'description' -DescriptionStart $descIdx -DescriptionEnd $descEndIdx)
    $modeIndices = @(Get-RootFieldIndices -Lines $fmLines -Key 'mode' -DescriptionStart $descIdx -DescriptionEnd $descEndIdx)
    $modeIdx = if ($modeIndices.Count -gt 0) { $modeIndices[0] } else { -1 }
    if ($descIdx -lt 0) { Add-Violation $relativePath 2 'R4-required-field' 'Missing required field: description' }
    if ($descIndices.Count -gt 1) { Add-Violation $relativePath 2 'R4-required-field' 'Duplicate required field: description' }
    if ($modeIndices.Count -gt 1) { Add-Violation $relativePath 2 'R4-required-field' 'Duplicate required field: mode' }
    $modeIsDescription = $descIdx -ge 0 -and $descEndIdx -ge 0 -and $modeIdx -gt $descIdx -and $modeIdx -le $descEndIdx
    $modeValue = if ($modeIdx -ge 0 -and -not $modeIsDescription) { ConvertFrom-CgYamlScalar -Value ($fmLines[$modeIdx].Substring($fmLines[$modeIdx].IndexOf(':') + 1)) } else { '' }
    if ($RequireMode -and ($modeIdx -lt 0 -or $modeIndices.Count -gt 1 -or $modeIsDescription -or $modeValue -notin @('subagent', 'primary', 'all'))) { Add-Violation $relativePath 2 'R4-required-field' 'Missing required field: mode' }

    # Rule 5: mojibake in body
    $bodyStart = $fmMatch.Index + $fmMatch.Length
    if ($bodyStart -lt $content.Length) {
        $body = $content.Substring($bodyStart)
        $bodyLines = $body -split '\r?\n'
        $mobiJakePattern = '[\u00e2][\u20ac\u2020]|\u00c2[\u0080-\u00FF]'
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
    if ($bytes -contains 13) {
        Add-Violation $relativePath 1 'R6-lf-endings' 'File contains CR or CRLF line endings; use LF only.'
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

    # Rule 1: skill file descriptions must be double-quoted (repo guideline).
    # Line-scoped: a bare 'description:' with no value is reported, and the
    # value never absorbs the next line.
    $descIdx = -1
    $descEndIdx = -1
    for ($di = 0; $di -lt $fmLines.Count; $di++) {
        if (Test-RootFieldLine -Line $fmLines[$di] -Key 'description') { $descIdx = $di; break }
    }
    if ($descIdx -ge 0) {
        $colonIdx = $fmLines[$descIdx].IndexOf(':')
        $descValue = if ($colonIdx -ge 0) { $fmLines[$descIdx].Substring($colonIdx + 1).Trim() } else { '' }
        if ([string]::IsNullOrEmpty($descValue)) {
            Add-Violation $relativePath ($fmStart + $descIdx) 'R1-quoted-description' 'description value is empty (expected a double-quoted string for skill files).'
        }
        elseif (-not (Test-DoubleQuotedDescription -Lines $fmLines -Index $descIdx)) {
            Add-Violation $relativePath ($fmStart + $descIdx) 'R1-quoted-description' "description value is not double-quoted: $($descValue.Substring(0, [Math]::Min(60, $descValue.Length)))..."
        }
        else {
            $descEndIdx = Get-DoubleQuotedDescriptionEnd -Lines $fmLines -Index $descIdx
        }
    }

    # Rule 4: required fields
    $descIndices = @(Get-RootFieldIndices -Lines $fmLines -Key 'description' -DescriptionStart $descIdx -DescriptionEnd $descEndIdx)
    $nameIndices = @(Get-RootFieldIndices -Lines $fmLines -Key 'name' -DescriptionStart $descIdx -DescriptionEnd $descEndIdx)
    $nameIdx = if ($nameIndices.Count -gt 0) { $nameIndices[0] } else { -1 }
    $nameIsDescription = $descIdx -ge 0 -and $descEndIdx -ge 0 -and $nameIdx -gt $descIdx -and $nameIdx -le $descEndIdx
    if ($descIndices.Count -gt 1) { Add-Violation $relativePath 2 'R4-required-field' 'Duplicate required field: description' }
    if ($nameIndices.Count -gt 1) { Add-Violation $relativePath 2 'R4-required-field' 'Duplicate required field: name' }
    if ($nameIdx -lt 0 -or $nameIndices.Count -gt 1 -or $nameIsDescription) { Add-Violation $relativePath 2 'R4-required-field' 'Missing required field: name' }
    if ($descIdx -lt 0) { Add-Violation $relativePath 2 'R4-required-field' 'Missing required field: description' }

    # Rule 5: mojibake in body
    $bodyStart = $fmMatch.Index + $fmMatch.Length
    if ($bodyStart -lt $content.Length) {
        $body = $content.Substring($bodyStart)
        $bodyLines = $body -split '\r?\n'
        $mobiJakePattern = '[\u00e2][\u20ac\u2020]|\u00c2[\u0080-\u00FF]'
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

if ($Fix) {
    Write-Host @"

WARNING: -Fix (auto-fix) is not implemented in the PowerShell entry; this
validator reports violations only. To auto-fix Rule 1/Rule 2, use the Python
validator:  python validate_yaml_frontmatter.py -Path "$Path" -Fix
(or on macOS/Linux: bash Invoke-YamlLint.sh -Path "$Path" -Fix)
"@ -ForegroundColor Yellow
}

$agentFiles = @()
$skillFiles = @()

$agentDir = Join-Path $resolvedPath 'agents'
if (Test-Path $agentDir) {
    $agentFiles = @(Get-ChildItem (Join-Path $agentDir '*.md'))
}

$skillsDir = Join-Path $resolvedPath 'skills'
if (Test-Path $skillsDir) {
    $skillFiles = @(Get-ChildItem (Join-Path $skillsDir '*/SKILL.md') -Recurse)
}

$totalFiles = $agentFiles.Count + $skillFiles.Count
if ($totalFiles -eq 0) {
    Write-Host "No agent or skill files found in $resolvedPath" -ForegroundColor Yellow
    exit 0
}

Write-Host "Checking $totalFiles files ($($agentFiles.Count) agents, $($skillFiles.Count) skills)..." -ForegroundColor Cyan

foreach ($f in $agentFiles) {
    $requireMode = @('.kilo', '.opencode') -contains (Split-Path $resolvedPath -Leaf)
    Test-AgentFile -FilePath $f.FullName -FixIssues:$Fix -RequireMode:$requireMode
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
        'R6' { 'Yellow' }
        default { 'White' }
    }
    Write-Host ("  [{0}] {1}:{2} - {3}" -f $_.Rule, $_.File, $_.Line, $_.Message) -ForegroundColor $color
}

$summary = $script:violations | Group-Object Rule | ForEach-Object { "$($_.Name): $($_.Count)" }
Write-Host ([Environment]::NewLine + "Summary: " + ($summary -join ', ')) -ForegroundColor Cyan

exit 1
