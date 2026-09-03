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
# Run from VS Code/PowerShell with the repository safe runner:
#   . tests\Run-Tests.ps1

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

    It "contains exactly 32 prompt files - update this sentinel when changing prompts" {
        $promptFiles.Count | Should -Be 32
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
            ($frontmatter -cmatch '(?m)^\s*model:') | Should -Be $false
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

    It "contains exactly 28 agent files - update this sentinel when adding a new agent" {
        $agentFiles.Count | Should -Be 28
    }

    foreach ($file in $agentFiles) {
        $filePath = $file.FullName
        $relPath = $filePath.Replace($repoRoot + "\", "")

        # P1.2 - same rationale as prompt files above
        It "$relPath exists" {
            Test-Path $filePath | Should -Be $true
        }

        It "$relPath does not assign an execution model" {
            $frontmatter = Get-Frontmatter -FilePath $filePath
            ($frontmatter -cmatch '(?m)^\s*model:') | Should -Be $false
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

    It "documents workflows inheriting the user-selected model" {
        $content | Should -Match "Decision Belongs To The User"
        $content | Should -Match "model picker"
    }

    It "documents advisory process-stage guidance" {
        $content | Should -Match "Process-Stage Guide"
        $content | Should -Match "Strong option"
        $content | Should -Match "Economical option"
    }

    It "documents advisory source order and user control" {
        $content | Should -Match "Availability And Validation Boundaries"
        $content | Should -Match "user decides"
        $content | Should -Match "availability"
        $content | Should -Match "must not infer"
    }

    It "does not describe executable model assignments" {
        $content | Should -Not -Match "Explicit Model Assignments"
        $content | Should -Not -Match "model-catalog\.json"
        $content | Should -Not -Match "model-mapping"
        $content | Should -Not -Match "OpenAI-first"
    }
}

# ---------------------------------------------------------------------------
# model-catalog CR policy coverage
# ---------------------------------------------------------------------------

Describe "model-catalog.json - CR model policy" {
    $catalogFile = Join-Path $repoRoot ".github\shared\model-catalog.json"

    It "model-catalog file is absent under advisory-only routing" {
        Test-Path $catalogFile | Should -Be $false
    }

    $catalog = if (Test-Path $catalogFile) {
        Get-Content $catalogFile -Raw -Encoding UTF8 | ConvertFrom-Json
    } else {
        $null
    }

    It "does not provide an executable CR assignment catalog" {
        Test-Path $catalogFile | Should -Be $false
    }

    It "does not contain executable assignments for CR agents" {
        Test-Path $catalogFile | Should -Be $false
    }

    It "does not contain an executable /cr-work assignment" {
        Test-Path $catalogFile | Should -Be $false
    }
}

Describe "docs/reference.md - ordinary prompt model picker sync" {
    $referenceFile = Join-Path $repoRoot "docs\reference.md"
    if (-not (Test-Path $referenceFile)) {
        Write-Warning "docs/reference.md not found -- skipping model picker sync tests"
    }
    $content = if (Test-Path $referenceFile) { Get-Content $referenceFile -Raw -Encoding UTF8 } else { "" }
    $ordinaryCommands = @(
        "/cg-brainstorm",
        "/cg-ideate",
        "/cg-plan",
        "/cg-plan-review",
        "/cg-compound-gpid-rd",
        "/cg-strategy"
    )

    foreach ($command in $ordinaryCommands) {
        It "$command documents model-picker inheritance rather than a premium default" {
            $escapedCommand = [regex]::Escape($command)
            ($content -match "\| ``?$escapedCommand") | Should -Be $true
            ($content -match "\| ``?$escapedCommand[^\r\n]*\| Claude Opus") | Should -Be $false
            ($content -match "\| ``?$escapedCommand[^\r\n]*\| Copilot model picker \|") | Should -Be $true
        }
    }
}

Describe "docs/reference.md - CR command model-picker sync" {
    $referenceFile = Join-Path $repoRoot "docs\reference.md"
    $content = if (Test-Path $referenceFile) { Get-Content $referenceFile -Raw -Encoding UTF8 } else { "" }

    It "/cr-brainstorm inherits the model picker" {
        ($content -match '\| `/cr-brainstorm` \| Copilot model picker \|') | Should -Be $true
    }

    It "/cr-plan inherits the model picker" {
        ($content -match '\| `/cr-plan` \| Copilot model picker \|') | Should -Be $true
    }

    It "/cr-work inherits the model picker" {
        ($content -match '\| `/cr-work` \| Copilot model picker \|') | Should -Be $true
    }

    It "/cr-review inherits the model picker" {
        ($content -match '\| `/cr-review` \| Copilot model picker \|') | Should -Be $true
    }

    It "/cr-compound inherits the model picker" {
        ($content -match '\| `/cr-compound` \| Copilot model picker \|') | Should -Be $true
    }
}

Describe "docs/model-guide.md - CR advisory coverage" {
    $guideFile = Join-Path $repoRoot "docs\model-guide.md"
    $content = if (Test-Path $guideFile) { Get-Content $guideFile -Raw -Encoding UTF8 } else { "" }

    It "documents research review as an advisory stage" {
        $content | Should -Match "Review"
        $content | Should -Match "Independent reasoning"
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
