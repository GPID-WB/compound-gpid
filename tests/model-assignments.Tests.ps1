# tests/model-assignments.Tests.ps1
# Validates that every prompt and agent file declares a model: frontmatter key.
# Uses dynamic discovery so new files are automatically included in the sweep.
#
# Design notes:
#   - Count sentinels catch accidental additions or deletions of prompt/agent files.
#     Update the sentinel when intentionally adding a new file.
#   - Test-Path is included for every file to produce clean, isolated failures
#     rather than scope-level exceptions if a file is unexpectedly missing.
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

    # Include root-level cg-release.prompt.md (developer-only)
    $releasePrompt = Join-Path $repoRoot "cg-release.prompt.md"
    if (Test-Path $releasePrompt) {
        $promptFiles += Get-Item $releasePrompt
    }

    It "contains exactly 18 prompt files - update this sentinel when adding a new prompt" {
        $promptFiles.Count | Should -Be 18
    }

    foreach ($file in $promptFiles) {
        $filePath = $file.FullName
        $relPath = $filePath.Replace($repoRoot + "\", "")

        # P1.2 - explicit existence check so a missing file is a clear test failure,
        # not a scope-level exception from Get-Content
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
# Model assignments - agent files
# Discovers all *.agent.md files in .github/agents.
# Count sentinel: update to N+1 when adding a new agent file.
# ---------------------------------------------------------------------------

Describe "Model assignments - agent files" {
    $agentsDir = Join-Path $repoRoot ".github\agents"
    $agentFiles = @(Get-ChildItem -Path $agentsDir -Filter "*.agent.md" -File)

    It "contains exactly 15 agent files - update this sentinel when adding a new agent" {
        $agentFiles.Count | Should -Be 15
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
# docs/model-guide.md - structure and sync validation
# Ensures the guide references every prompt and agent file stem so that
# if a file is added or renamed, the guide must also be updated.
# ---------------------------------------------------------------------------

Describe "docs/model-guide.md - structure and sync" {
    $guideFile = Join-Path $repoRoot "docs\model-guide.md"

    It "docs/model-guide.md exists" {
        Test-Path $guideFile | Should -Be $true
    }

    $content = Get-Content $guideFile -Raw -Encoding UTF8

    # All 18 prompt file stems must appear in the guide
    $promptStems = @(
        'cg-strategy', 'cg-brainstorm', 'cg-plan', 'cg-work', 'cg-review',
        'cg-fixbug', 'cg-release', 'cg-compound', 'cg-fix-triage',
        'cg-setup', 'cg-devtag', 'cg-resume',
        'cg-compound-refresh', 'cg-ideate',
        'cg-diagnose', 'cg-fix-problems', 'cg-plan-review',
        'cg-review-repos'
    )
    foreach ($stem in $promptStems) {
        It "guide references prompt stem '$stem'" {
            ($content -match ([regex]::Escape($stem) + '\.prompt\.md')) | Should -Be $true
        }
    }

    # All 15 agent file stems must appear in the guide
    $agentStems = @(
        'cg-architecture', 'cg-performance', 'cg-data-quality', 'cg-code-quality',
        'cg-testing', 'cg-documentation', 'cg-version-control', 'cg-reproducibility',
        'cg-learnings-researcher', 'cg-roadmap',
        'cg-adversarial', 'cg-fix-problems', 'cg-plan-critic',
        'cg-release-scanner', 'cg-project-scanner'
    )
    foreach ($stem in $agentStems) {
        It "guide references agent stem '$stem'" {
            ($content -match ([regex]::Escape($stem) + '\.agent\.md')) | Should -Be $true
        }
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
