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
