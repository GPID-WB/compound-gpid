# tests/model-assignments.Tests.ps1
# Validates model-governance metadata for prompt and agent files.
# Uses dynamic discovery so new files are automatically included in the sweep.
#
# Design notes:
#   - Count sentinels catch accidental additions or deletions of prompt/agent files.
#     Update the sentinel when intentionally adding a new file.
#   - Test-Path is included for every file to produce clean, isolated failures
#     rather than scope-level exceptions if a file is unexpectedly missing.
#   - Ordinary workflow prompts intentionally omit `model:` so they inherit the
#     user's GitHub Copilot model-picker selection.
#   - Regex is anchored to the YAML `model:` key (not a substring anywhere in
#     frontmatter) and uses -cmatch for case-sensitive matching.
#   - For tier-assignment rationale and override guidance, see docs/model-guide.md.
#
# Run with: Invoke-Pester tests/model-assignments.Tests.ps1 -Quiet

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
. "$PSScriptRoot/helpers.ps1"

# ---------------------------------------------------------------------------
# Model assignments - prompt files
# Discovers all *.prompt.md files in .github/prompts plus the root-level
# cg-release.prompt.md (developer-only, not junctioned into user projects).
# Count sentinel: update to N+1 when adding a new prompt file.
# ---------------------------------------------------------------------------

Describe "Model assignments - prompt files" {
    $promptsDir = Join-Path $repoRoot ".github\prompts"
    $promptFiles = @(Get-ChildItem -Path $promptsDir -Filter "*.prompt.md" -File)
    $ordinaryPromptNames = @(
        "cg-brainstorm.prompt.md",
        "cg-ideate.prompt.md",
        "cg-plan-review.prompt.md",
        "cg-plan.prompt.md",
        "cg-review-repos.prompt.md",
        "cg-strategy.prompt.md"
    )

    # Include root-level cg-release.prompt.md (developer-only)
    $releasePrompt = Join-Path $repoRoot "cg-release.prompt.md"
    if (Test-Path $releasePrompt) {
        $promptFiles += Get-Item $releasePrompt
    }

    It "contains exactly 23 prompt files - update this sentinel when adding a new prompt" {
        $promptFiles.Count | Should -Be 23
    }

    foreach ($file in $promptFiles) {
        $filePath = $file.FullName
        $relPath = $filePath.Replace($repoRoot + "\", "")

        # P1.2 - explicit existence check so a missing file is a clear test failure,
        # not a scope-level exception from Get-Content
        It "$relPath exists" {
            Test-Path $filePath | Should -Be $true
        }

        It "$relPath has the expected model frontmatter governance" {
            $frontmatter = Get-Frontmatter -FilePath $filePath
            if ($ordinaryPromptNames -contains $file.Name) {
                ($frontmatter -cmatch '(?m)^\s*model:') | Should -Be $false
            } else {
                # Anchored to key with non-empty value; -cmatch for case-sensitive matching
                ($frontmatter -cmatch '(?m)^\s*model:\s+\S+') | Should -Be $true
            }
        }
    }
}

Describe "Model governance - ordinary prompts" {
    $ordinaryPrompts = @(
        "cg-brainstorm.prompt.md",
        "cg-ideate.prompt.md",
        "cg-plan-review.prompt.md",
        "cg-plan.prompt.md",
        "cg-review-repos.prompt.md",
        "cg-strategy.prompt.md"
    )

    foreach ($prompt in $ordinaryPrompts) {
        It "$prompt should not hard-code a model" {
            $path = Join-Path $repoRoot ".github\prompts\$prompt"
            $frontmatter = Get-Frontmatter -FilePath $path
            $frontmatter | Should -Not -Match '(?m)^\s*model:'
        }
    }
}

# ---------------------------------------------------------------------------
# Model assignments - agent files
# Discovers all *.agent.md files in .github/agents.
# Count sentinel: update to N+1 when adding a new agent file.
# ---------------------------------------------------------------------------

Describe "Model assignments - agent files" {
    $agentsDir = Join-Path $repoRoot ".github\agents"
    $agentFiles = @(Get-ChildItem -Path $agentsDir -Filter "*.agent.md" -File)

    It "contains exactly 17 agent files - update this sentinel when adding a new agent" {
        $agentFiles.Count | Should -Be 17
    }

    foreach ($file in $agentFiles) {
        $filePath = $file.FullName
        $relPath = $filePath.Replace($repoRoot + "\", "")

        # P1.2 - same rationale as prompt files above
        It "$relPath exists" {
            Test-Path $filePath | Should -Be $true
        }

        It "$relPath has a model: frontmatter key with a non-empty value" {
            $frontmatter = Get-Frontmatter -FilePath $filePath
            # Anchored to key with non-empty value; -cmatch for case-sensitive matching
            ($frontmatter -cmatch '(?m)^\s*model:\s+\S+') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# docs/model-guide.md - governance validation
# Ensures the guide documents model-picker inheritance, escalation guidance,
# recommended model selection, and the governance principle.
# ---------------------------------------------------------------------------

Describe "docs/model-guide.md - structure and sync" {
    $guideFile = Join-Path $repoRoot "docs\model-guide.md"

    It "docs/model-guide.md exists" {
        Test-Path $guideFile | Should -Be $true
    }

    $content = Get-Content $guideFile -Raw -Encoding UTF8

    It "documents ordinary prompts inheriting the user-selected model" {
        $content | Should -Match "Ordinary workflow prompts"
        $content | Should -Match "model picker"
    }

    It "documents recommended model selection" {
        $content | Should -Match "Recommended Model Selection"
        $content | Should -Match "Normal daily use"
        $content | Should -Match "Auto"
    }

    It "documents escalation guidance" {
        $content | Should -Match "Escalation Guidance"
        $content | Should -Match "High-stakes architecture"
        $content | Should -Match "user-initiated"
    }

    It "documents governance principle" {
        $content | Should -Match "Governance Principle"
        $content | Should -Match "does not hard-code expensive premium models"
        $content | Should -Match "explicit budget decision"
    }
}

# ---------------------------------------------------------------------------
# Prompt/agent files - frontmatter delimiters
# Sanity check: every file must have both opening and closing --- delimiters.
# Catches frontmatter that was accidentally truncated or never closed.
# ---------------------------------------------------------------------------

Describe "Prompt/agent files - frontmatter delimiters" {
    $allFiles = @()
    $allFiles += Get-ChildItem (Join-Path $repoRoot ".github\prompts") -Filter "*.prompt.md" -File
    $allFiles += Get-ChildItem (Join-Path $repoRoot ".github\agents") -Filter "*.agent.md" -File

    $releasePrompt = Join-Path $repoRoot "cg-release.prompt.md"
    if (Test-Path $releasePrompt) {
        $allFiles += Get-Item $releasePrompt
    }

    foreach ($file in $allFiles) {
        $relPath = $file.FullName.Replace($repoRoot + "\", "")

        It "$relPath has both opening and closing --- frontmatter delimiters" {
            $content = Get-Content $file.FullName -Raw -Encoding UTF8
            # At least two --- delimiters means both opening and closing are present
            ($content -split '\r?\n' | Where-Object { $_ -match '^---\s*$' }).Count |
                Should -BeGreaterThan 1
        }
    }
}
