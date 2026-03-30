# tests/prompt-tools.Tests.ps1
# Pester tests to guard the 'tools:' frontmatter in prompt files
#
# Run with: Invoke-Pester tests/prompt-tools.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)
#
# Background: VS Code Copilot prompt files support a 'tools:' YAML key that
# restricts which tools are available when the prompt runs. If 'write' is
# absent, the agent operating under that prompt cannot create or modify files.
# The cg-review.prompt.md was missing 'write', causing all file-creation
# steps (triage fixes, review report output) to silently fail.

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }

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
    $line = ($Frontmatter -split '\r?\n' | Where-Object { $_ -match '^\s*tools:' })
    if (-not $line) { return @() }
    # Match quoted tokens inside the brackets: 'agent', "read", etc.
    $tokens = [regex]::Matches($line, "['""](\w+)['""]") | ForEach-Object { $_.Groups[1].Value }
    return $tokens
}

# ---------------------------------------------------------------------------
# cg-review.prompt.md tools requirements
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - tools frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"

    Context "required tools are declared" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile
        $tools = Get-ToolsList -Frontmatter $frontmatter

        It "has a tools: key in frontmatter" {
            $frontmatter | Should Match 'tools:'
        }

        It "includes 'agent' so review subagents can be dispatched" {
            $tools | Should Contain 'agent'
        }

        It "includes 'read' so agents can read source files" {
            $tools | Should Contain 'read'
        }

        It "includes 'search' so agents can search the codebase" {
            $tools | Should Contain 'search'
        }

        It "includes 'write' so the review report can be saved to .cg-docs/reviews/" {
            $tools | Should Contain 'write'
        }
    }
}

# ---------------------------------------------------------------------------
# cg-review.prompt.md review-output step
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - review file output step" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "contains a step that writes the review report to .cg-docs/reviews/" {
        ($content -match '\.cg-docs[/\\]reviews') | Should Be $true
    }
}
