# tests/model-assignments.Tests.ps1
# Validates user-selected execution and advisory-only model guidance.

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
. "$PSScriptRoot/helpers.ps1"

Describe "Canonical prompt execution metadata" {
    $promptFiles = @(Get-ChildItem (Join-Path $repoRoot ".github\prompts") -Filter "*.prompt.md" -File)

    It "contains exactly 25 prompt files - update this sentinel when adding a new prompt" {
        $promptFiles.Count | Should -Be 25
    }

    foreach ($file in $promptFiles) {
        $path = $file.FullName
        $relative = $path.Replace($repoRoot + "\", "")

        It "$relative exists" {
            Test-Path $path | Should -Be $true
        }

        It "$relative does not assign an execution model" {
            $frontmatter = Get-Frontmatter -FilePath $path
            ($frontmatter -cmatch '(?m)^\s*model\s*:') | Should -Be $false
        }
    }
}

Describe "Canonical agent execution metadata" {
    $agentFiles = @(Get-ChildItem (Join-Path $repoRoot ".github\agents") -Filter "*.agent.md" -File)

    It "contains exactly 17 agent files - update this sentinel when adding a new agent" {
        $agentFiles.Count | Should -Be 17
    }

    foreach ($file in $agentFiles) {
        $path = $file.FullName
        $relative = $path.Replace($repoRoot + "\", "")

        It "$relative exists" {
            Test-Path $path | Should -Be $true
        }

        It "$relative does not assign an execution model" {
            $frontmatter = Get-Frontmatter -FilePath $path
            ($frontmatter -cmatch '(?m)^\s*model\s*:') | Should -Be $false
        }
    }
}

Describe "Developer-only release prompt execution metadata" {
    $releasePrompt = Join-Path $repoRoot "cg-release.prompt.md"

    It "exists in the repository" {
        Test-Path $releasePrompt | Should -Be $true
    }

    It "does not assign an execution model" {
        $frontmatter = Get-Frontmatter -FilePath $releasePrompt
        ($frontmatter -cmatch '(?m)^\s*model\s*:') | Should -Be $false
    }
}

Describe "Advisory contract and examples" {
    $contractPath = Join-Path $repoRoot ".github\shared\model-advisory.contract.md"
    $examplesPath = Join-Path $repoRoot ".github\shared\model-advisory-examples.json"
    $mappingPath = Join-Path $repoRoot ".github\shared\target-mapping.json"

    It "provides the shared advisory contract and examples" {
        Test-Path $contractPath | Should -Be $true
        Test-Path $examplesPath | Should -Be $true
    }

    It "defines all stable stages and effort labels" {
        $contract = Get-Content $contractPath -Raw -Encoding UTF8
        $examples = Get-Content $examplesPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $contract | Should -Match "planning"
        $contract | Should -Match "implementation"
        $contract | Should -Match "review"
        $contract | Should -Match "fix-triage"
        $contract | Should -Match "compounding-documentation"
        @($examples.effortLabels) | Should -Contain "low"
        @($examples.effortLabels) | Should -Contain "medium"
        @($examples.effortLabels) | Should -Contain "high"
        @($examples.effortLabels) | Should -Contain "xhigh"
        @($examples.effortLabels) | Should -Contain "max"
    }

    It "requires user control and provenance language" {
        $contract = Get-Content $contractPath -Raw -Encoding UTF8
        $contract | Should -Match "user makes the final selection"
        $contract | Should -Match "availability can differ by platform and date"
        $contract | Should -Match "Runtime catalog introspection is intentionally deferred"
        $contract | Should -Match "must never be translated into prompt or agent frontmatter"
    }

    It "does not retain executable model mapping fields" {
        $mapping = Get-Content $mappingPath -Raw -Encoding UTF8 | ConvertFrom-Json
        foreach ($target in @($mapping.targets)) {
            $target.PSObject.Properties.Name | Should -Not -Contain "modelMappingMode"
            $target.PSObject.Properties.Name | Should -Not -Contain "modelMapping"
            $target.outputPaths.PSObject.Properties.Name | Should -Not -Contain "modelMapping"
        }
        (Get-Content $mappingPath -Raw -Encoding UTF8) | Should -Not -Match "model-mapping"
    }
}

Describe "Model guidance documentation" {
    $guidePath = Join-Path $repoRoot "docs\model-guide.md"
    $guide = Get-Content $guidePath -Raw -Encoding UTF8

    It "is organized around process stages" {
        $guide | Should -Match "Planning"
        $guide | Should -Match "Implementation"
        $guide | Should -Match "Review"
        $guide | Should -Match "Fix triage"
        $guide | Should -Match "Compounding"
    }

    It "includes strong and economical advisory choices" {
        $guide | Should -Match "Strong option"
        $guide | Should -Match "Economical option"
        $guide | Should -Match "successful completion"
    }

    It "states user choice and unknown availability" {
        $guide | Should -Match "user decides"
        $guide | Should -Match "availability"
        $guide | Should -Match "must not infer"
        $guide | Should -Match "unknown"
    }

    It "does not describe enforced assignments or mapping artifacts" {
        $guide | Should -Not -Match "Explicit Model Assignments"
        $guide | Should -Not -Match "model-catalog\.json"
        $guide | Should -Not -Match "model-mapping"
        $guide | Should -Not -Match "OpenAI-first"
    }
}

Describe "Advisory handoff contracts" {
    $handoffs = @{
        "cg-plan.prompt.md" = "planning"
        "cg-work.prompt.md" = "implementation"
        "cg-review.prompt.md" = "review"
        "cg-fix-triage.prompt.md" = "fix-triage"
    }

    foreach ($name in $handoffs.Keys) {
        $path = Join-Path $repoRoot (Join-Path ".github\prompts" $name)
        $content = Get-Content $path -Raw -Encoding UTF8
        $stage = $handoffs[$name]

        It "$name reads the shared advisory contract" {
            $content | Should -Match '\.github/shared/model-advisory\.contract\.md'
        }

        It "$name names the $stage advisory stage" {
            $content | Should -Match $stage
        }

        It "$name preserves user control and availability caveats" {
            $content | Should -Match 'availability can differ by platform\s+and date'
            $content | Should -Match 'user makes the final\s+selection'
            $content | Should -Match 'Do not dispatch,\s*switch,\s*retry,\s*or set'
        }
    }
}

Describe "Cross-document model policy" {
    foreach ($fileName in @("workflow.md", "reference.md", "context-files.md")) {
        $path = Join-Path $repoRoot (Join-Path "docs" $fileName)
        It "docs/$fileName does not require model mapping artifacts" {
            $content = Get-Content $path -Raw -Encoding UTF8
            $content | Should -Not -Match "model-mapping"
            $content | Should -Not -Match "model-catalog\.json"
            $content | Should -Not -Match "OpenAI-first"
        }
    }
}

Describe "Prompt and agent frontmatter delimiters" {
    $allFiles = @()
    $allFiles += Get-ChildItem (Join-Path $repoRoot ".github\prompts") -Filter "*.prompt.md" -File
    $allFiles += Get-ChildItem (Join-Path $repoRoot ".github\agents") -Filter "*.agent.md" -File

    foreach ($file in $allFiles) {
        $relative = $file.FullName.Replace($repoRoot + "\", "")
        It "$relative has both opening and closing frontmatter delimiters" {
            $content = Get-Content $file.FullName -Raw -Encoding UTF8
            ($content -split '\r?\n' | Where-Object { $_ -match '^---\s*$' }).Count |
                Should -BeGreaterThan 1
        }
    }
}
