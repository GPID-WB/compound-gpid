# tests/prompt-tools.Tests.ps1
# Pester tests to guard prompt file structure and tool configuration
#
# Run with: Invoke-Pester tests/prompt-tools.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)
#
# Background: VS Code Copilot prompt files support a 'tools:' YAML key that
# RESTRICTS which tools are available to the agent running that prompt.
# Omitting 'tools:' gives the agent all available tools (the safe default).
#
# Lesson learned: cg-review.prompt.md had tools:['agent','read','search','write'].
# This whitelist stripped file-write access from the orchestrating agent mid-session
# because the tool categories did not map reliably to the underlying tool functions.
# Fix: remove 'tools:' from orchestrating prompts entirely. Only agent definition
# files (.agent.md) should declare a 'tools:' restriction, since they are
# intentionally read-only reviewers.

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
. "$PSScriptRoot/helpers.ps1"

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
# cg-review.prompt.md must NOT have a tools: restriction
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (a tools: whitelist strips write access from the orchestrating agent)" {
            ($frontmatter -notmatch 'tools:') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# cg-review.prompt.md review-output step
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - review file output step" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "writes the review report to .cg-docs/reviews/ directory in Step 3.5" {
        ($content -match '\.cg-docs[/\\]reviews') | Should Be $true
    }

    It "uses compound finding IDs like [P0.1], [P1.1], [P2.1], [P3.1] in the output template" {
        ($content -match '\*\*\[P[0123]\.\d+\]\*\*') | Should Be $true
    }

    It "includes /cg-fix-triage usage instruction with a compound ID example" {
        ($content -match '/cg-fix-triage.*P\d\.\d') | Should Be $true
    }

    It "mentions /cg-fix-triage so users know how to apply findings" {
        ($content -match '/cg-fix-triage') | Should Be $true
    }

    It "explicitly instructs DO NOT delegate the Step 3.5 file write" {
        ($content -match 'Do NOT delegate') | Should Be $true
    }

    It "documents 'no issues found' as valid output when an agent finds nothing" {
        ($content -match 'no issues found') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-fix-triage.prompt.md existence and content
# ---------------------------------------------------------------------------

Describe "cg-fix-triage.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }
}

Describe "cg-fix-triage.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"

    Context "required frontmatter fields" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "has a description in frontmatter" {
            $frontmatter | Should Match 'description:'
        }

        It "has a model in frontmatter" {
            $frontmatter | Should Match 'model:'
        }
    }
}

Describe "cg-fix-triage.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (a tools: whitelist strips write access from the orchestrating agent)" {
            ($frontmatter -notmatch 'tools:') | Should Be $true
        }
    }
}

Describe "cg-fix-triage.prompt.md - review reports location" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references .cg-docs/reviews/ directory to load saved review reports" {
        ($content -match '\.cg-docs[/\\]reviews') | Should Be $true
    }
}


# ---------------------------------------------------------------------------
# cg-strategy.prompt.md existence, frontmatter, and no tool restriction
# ---------------------------------------------------------------------------

Describe "cg-strategy.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-strategy.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }
}

Describe "cg-strategy.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-strategy.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should Match 'description:'
        }

        It "has a model in frontmatter" {
            $frontmatter | Should Match 'model:'
        }
    }
}

Describe "cg-strategy.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-strategy.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (restrictions are prose-only per convention)" {
            ($frontmatter -notmatch 'tools:') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# copilot-instructions.md Workflow Entry Points table
# ---------------------------------------------------------------------------

Describe "copilot-instructions.md - Workflow Entry Points" {
    $instructionsFile = Join-Path $repoRoot ".github\copilot-instructions.md"
    $rawContent = Get-Content $instructionsFile -Raw -Encoding UTF8
    $section = if ($rawContent -match '(?s)(## Workflow Entry Points.*?)(\r?\n## |\z)') { $Matches[1] } else { "" }

    It "references /cg-strategy in Workflow Entry Points" {
        ($section -match '/cg-strategy') | Should Be $true
    }

    It "references /cg-brainstorm in Workflow Entry Points" {
        ($section -match '/cg-brainstorm') | Should Be $true
    }

    It "references /cg-plan in Workflow Entry Points" {
        ($section -match '/cg-plan') | Should Be $true
    }

    It "references @cg-roadmap in Workflow Entry Points" {
        ($section -match '@cg-roadmap') | Should Be $true
    }

    It "references /cg-resume in Workflow Entry Points" {
        ($section -match '/cg-resume') | Should Be $true
    }

    It "references /cg-work in Workflow Entry Points" {
        ($section -match '/cg-work') | Should Be $true
    }

    It "references /cg-review in Workflow Entry Points" {
        ($section -match '/cg-review') | Should Be $true
    }

    It "references /cg-fix-triage in Workflow Entry Points" {
        ($section -match '/cg-fix-triage') | Should Be $true
    }

    It "references /cg-compound in Workflow Entry Points" {
        ($section -match '/cg-compound') | Should Be $true
    }

    It "references /cg-compound-refresh in Workflow Entry Points" {
        ($section -match '/cg-compound-refresh') | Should Be $true
    }

    It "references /cg-ideate in Workflow Entry Points" {
        ($section -match '/cg-ideate') | Should Be $true
    }

    It "references /cg-fix-problems in Workflow Entry Points" {
        ($section -match '/cg-fix-problems') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-review.prompt.md - review findings frontmatter
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - review findings frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references the findings: frontmatter key in Step 3.5" {
        ($content -match 'findings:') | Should Be $true
    }

    It "sets new findings to status: open in Step 3.5" {
        ($content -match '\bopen\b') | Should Be $true
    }

    It "mentions status: fixed as a valid finding status" {
        ($content -match '\bfixed\b') | Should Be $true
    }

    It "mentions status: skipped as a valid finding status" {
        ($content -match '\bskipped\b') | Should Be $true
    }

    It "includes a plan: key in the frontmatter template" {
        ($content -match '(?s)plan:.*findings:|(?s)findings:.*plan:') | Should Be $true
    }

    It "documents the finding ID parsing patterns in Step 3.5" {
        ($content -match [regex]::Escape('**[P0.')) -and
        ($content -match [regex]::Escape('**[P1.')) -and
        ($content -match [regex]::Escape('**[P2.')) -and
        ($content -match [regex]::Escape('**[P3.')) | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-fix-triage.prompt.md - per-finding status tracking
# ---------------------------------------------------------------------------

Describe "cg-fix-triage.prompt.md - per-finding status tracking" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references the findings: frontmatter key" {
        ($content -match 'findings:') | Should Be $true
    }

    It "instructs updating finding status to fixed in frontmatter after applying a fix" {
        ($content -match 'fixed') -and ($content -match 'frontmatter') | Should Be $true
    }

    It "instructs updating finding status to skipped in frontmatter when user declines" {
        ($content -match 'skipped') | Should Be $true
    }

    It "references --migrate mode" {
        ($content -match '\-\-migrate') | Should Be $true
    }

    It "describes the companion-plan heuristic in --migrate mode" {
        ($content -match 'companion[- ]plan|companion plan') | Should Be $true
    }

    It "reports Previously resolved count in summary template" {
        ($content -match 'Previously resolved') | Should Be $true
    }

    It "Step 3 apply order lists P0 first before P1" {
        ($content -match 'P0 first') | Should Be $true
    }

    It "warns the user when there are more than 15 open findings (large report guard)" {
        ($content -match '15 open|more than 15') | Should Be $true
    }

    It "recommends priority batches (P0 P1, P2, P3) in the large report warning" {
        ($content -match 'P0 P1.*P2.*P3|priority batch') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-resume.prompt.md - findings frontmatter and migration nudge
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - findings frontmatter and migration nudge" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references the findings: frontmatter key in Step 2e" {
        ($content -match 'findings:') | Should Be $true
    }

    It "instructs skipping fully-resolved review files (zero open findings)" {
        ($content -match 'zero|fully resolved|skip it') | Should Be $true
    }

    It "references --migrate nudge for legacy review files without frontmatter" {
        ($content -match '\-\-migrate') | Should Be $true
    }

    It "adds migration nudge to Maintenance Nudges section" {
        ($content -match 'Review migration needed') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# SKILL.md files - required frontmatter
# ---------------------------------------------------------------------------

Describe "SKILL.md files - required frontmatter" {
    $skillsDir = Join-Path $repoRoot ".github\skills"
    $skillFiles = Get-ChildItem -Path $skillsDir -Recurse -Filter "SKILL.md"

    It "finds at least one SKILL.md file" {
        $skillFiles.Count | Should BeGreaterThan 0
    }

    foreach ($skill in $skillFiles) {
        $skillName = (Split-Path (Split-Path $skill.FullName -Parent) -Leaf)
        $frontmatter = Get-Frontmatter -FilePath $skill.FullName

        It "$skillName SKILL.md has a name: field" {
            $frontmatter | Should Match '(?m)^\s*name:'
        }

        It "$skillName SKILL.md has a description: field" {
            $frontmatter | Should Match '(?m)^\s*description:'
        }
    }
}

# ---------------------------------------------------------------------------
# cg-skill-r-testing - all 6 skill files exist
# ---------------------------------------------------------------------------

Describe "cg-skill-r-testing - skill file structure" {
    $skillRoot = Join-Path $repoRoot ".github\skills\cg-skill-r-testing"
    $expectedFiles = @(
        "SKILL.md",
        "references\bdd.md",
        "references\mocking.md",
        "references\fixtures.md",
        "references\snapshots.md",
        "references\advanced.md"
    )

    foreach ($file in $expectedFiles) {
        It "file '$file' exists" {
            Test-Path (Join-Path $skillRoot $file) | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Skill file cross-link validation
# ---------------------------------------------------------------------------

Describe "skill file cross-links resolve" {
    $skillsRoot = Join-Path $repoRoot ".github\skills"
    $skillFiles = Get-ChildItem $skillsRoot -Recurse -Filter "*.md" -ErrorAction SilentlyContinue |
                  Where-Object { $_.Name -ne ".gitkeep" }

    foreach ($skillFile in $skillFiles) {
        $content = Get-Content $skillFile.FullName -Raw -Encoding UTF8
        # Extract markdown links: [text](path) — skip anchors and external URLs
        $links = [regex]::Matches($content, '\[[^\]]*\]\(([^)#]+\.md)\)')
        foreach ($link in $links) {
            $target = $link.Groups[1].Value
            if ($target -match '^https?://') { continue }
            $resolved = [System.IO.Path]::GetFullPath(
                [System.IO.Path]::Combine($skillFile.DirectoryName, $target)
            )
            $relSource = $skillFile.FullName.Replace($repoRoot + "\", "")
            It "$relSource -> $target" {
                Test-Path $resolved | Should Be $true
            }
        }
    }
}

# ---------------------------------------------------------------------------
# cg-review.prompt.md - Step 2.5 subagent quality check guidance
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - subagent output quality check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes a Step 2.5 subagent output quality check" {
        ($content -match 'Subagent Output Quality Check') | Should Be $true
    }

    It "mentions the Incomplete Reviews warning section for failed agents" {
        ($content -match 'Incomplete Reviews') | Should Be $true
    }

    It "instructs NOT to retry the agent automatically" {
        ($content -match 'NOT retry') | Should Be $true
    }

    It "lists empty or garbled output as quality failure criteria" {
        ($content -match 'empty.*garbled|garbled.*empty') | Should Be $true
    }

    It "includes the warning template with @agent-name placeholder" {
        ($content -match '@<agent-name>') | Should Be $true
    }

    It "documents the Presence criterion by name" {
        ($content -match '\bPresence\b') | Should Be $true
    }

    It "documents the Context criterion by name" {
        ($content -match '\bContext\b') | Should Be $true
    }

    It "documents the Volume criterion by name" {
        ($content -match '\bVolume\b') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-compound-refresh.prompt.md - file existence, frontmatter, and no tool restriction
# (Orchestrating prompts must not have a tools: whitelist -- it strips write access)
# ---------------------------------------------------------------------------

Describe "cg-compound-refresh.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound-refresh.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }
}

Describe "cg-compound-refresh.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound-refresh.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should Match 'description:'
        }

        It "has a model in frontmatter" {
            $frontmatter | Should Match 'model:'
        }
    }
}

Describe "cg-compound-refresh.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound-refresh.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (a tools: whitelist strips write access from the orchestrating prompt)" {
            ($frontmatter -notmatch '(?m)^\s*tools:') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# cg-ideate.prompt.md - file existence, frontmatter, and no tool restriction
# (Orchestrating prompts must not have a tools: whitelist -- it strips write access)
# ---------------------------------------------------------------------------

Describe "cg-ideate.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-ideate.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }
}

Describe "cg-ideate.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-ideate.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should Match 'description:'
        }

        It "has a model in frontmatter" {
            $frontmatter | Should Match 'model:'
        }
    }
}

Describe "cg-ideate.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-ideate.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (a tools: whitelist strips write access from the orchestrating prompt)" {
            ($frontmatter -notmatch '(?m)^\s*tools:') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# R dialect routing — r.instructions.md validation
# ---------------------------------------------------------------------------

Describe "r.instructions.md - dialect router" {
    $routerFile = Join-Path $repoRoot ".github\instructions\r.instructions.md"

    It "router file exists" {
        Test-Path $routerFile | Should Be $true
    }

    $content = if (Test-Path $routerFile) { Get-Content $routerFile -Raw -Encoding UTF8 } else { "" }

    It "documents data.table-collapse dialect" {
        ($content -match 'data\.table-collapse') | Should Be $true
    }

    It "routes to cg-skill-r-collapse for data.table-collapse" {
        ($content -match 'cg-skill-r-collapse') | Should Be $true
    }

    It "routes to cg-skill-r-datatable for data.table-collapse" {
        ($content -match 'cg-skill-r-datatable') | Should Be $true
    }

    It "documents tidyverse dialect" {
        ($content -match 'tidyverse') | Should Be $true
    }

    It "routes to cg-skill-r-tidyverse for tidyverse" {
        ($content -match 'cg-skill-r-tidyverse') | Should Be $true
    }

    It "mentions cg-skill-r-visualization" {
        ($content -match 'cg-skill-r-visualization') | Should Be $true
    }

    It "documents fallback for invalid r-syntax values" {
        ($content -match 'Any other value|unrecognized') | Should Be $true
    }

    # P2.4: applyTo field presence — if this field is missing/wrong, dialect routing
    # silently stops working for ALL .R files with no error.
    It "has applyTo frontmatter field (required for auto-apply to .R files)" {
        ($content -match '(?m)^applyTo:') | Should Be $true
    }

    It "applyTo covers .R files" {
        ($content -match 'applyTo.*\*\*/\*\.R') | Should Be $true
    }

    It "applyTo covers .r files (lowercase)" {
        ($content -match 'applyTo.*\*\*/\*\.r') | Should Be $true
    }

    It "applyTo covers .Rmd files" {
        ($content -match 'applyTo.*\*\*/\*\.Rmd') | Should Be $true
    }
}

Describe "R dialect skills - skill directories exist" {
    $dialectSkills = @(
        'cg-skill-r-collapse',
        'cg-skill-r-datatable',
        'cg-skill-r-tidyverse',
        'cg-skill-r-visualization'
    )

    foreach ($skill in $dialectSkills) {
        It "dialect skill '$skill' has SKILL.md" {
            $path = Join-Path $repoRoot ".github\skills\$skill\SKILL.md"
            Test-Path $path | Should Be $true
        }
    }
}

Describe "cg-skill-setup - r-syntax field documentation" {
    $setupFile = Join-Path $repoRoot ".github\skills\cg-skill-setup\SKILL.md"
    $content = if (Test-Path $setupFile) { Get-Content $setupFile -Raw -Encoding UTF8 } else { "" }

    It "documents r-syntax field" {
        ($content -match 'r-syntax') | Should Be $true
    }

    It "documents data.table-collapse as default dialect" {
        ($content -match 'data\.table-collapse') | Should Be $true
    }

    It "documents tidyverse as alternative dialect" {
        ($content -match 'tidyverse') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.1 — SCHEMA_VERSION dialect marker validation
# ---------------------------------------------------------------------------

Describe "SCHEMA_VERSION - dialect marker" {
    $schemaFile = Join-Path $repoRoot "SCHEMA_VERSION"
    $content = if (Test-Path $schemaFile) { (Get-Content $schemaFile -Raw -Encoding UTF8).Trim() } else { "" }

    It "SCHEMA_VERSION file exists" {
        Test-Path $schemaFile | Should Be $true
    }

    It "SCHEMA_VERSION contains scope-fields marker" {
        ($content -match 'scope-fields') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.2 — r.instructions.md router covers all 8 unconditional skill references
# ---------------------------------------------------------------------------

Describe "r.instructions.md - unconditional skill routing" {
    $routerFile = Join-Path $repoRoot ".github\instructions\r.instructions.md"
    $content = if (Test-Path $routerFile) { Get-Content $routerFile -Raw -Encoding UTF8 } else { "" }

    It "routes to cg-skill-r-analytical (unconditional)" {
        ($content -match 'cg-skill-r-analytical') | Should Be $true
    }

    It "routes to cg-skill-r-technical (unconditional)" {
        ($content -match 'cg-skill-r-technical') | Should Be $true
    }

    It "routes to cg-skill-r-testing (unconditional)" {
        ($content -match 'cg-skill-r-testing') | Should Be $true
    }

    It "routes to cg-skill-r-shared (unconditional)" {
        ($content -match 'cg-skill-r-shared') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.3 — docs/reference.md lists all 8 R skills and r-syntax config field
# ---------------------------------------------------------------------------

Describe "docs/reference.md - R skills and r-syntax config" {
    $refFile = Join-Path $repoRoot "docs\reference.md"
    $content = if (Test-Path $refFile) { Get-Content $refFile -Raw -Encoding UTF8 } else { "" }

    It "docs/reference.md exists" {
        Test-Path $refFile | Should Be $true
    }

    $allRSkills = @(
        'cg-skill-r-collapse',
        'cg-skill-r-datatable',
        'cg-skill-r-tidyverse',
        'cg-skill-r-visualization',
        'cg-skill-r-analytical',
        'cg-skill-r-technical',
        'cg-skill-r-shared',
        'cg-skill-r-testing'
    )

    foreach ($skill in $allRSkills) {
        It "reference.md lists $skill" {
            ($content -match [regex]::Escape($skill)) | Should Be $true
        }
    }

    It "documents r-syntax configuration field" {
        ($content -match 'r-syntax') | Should Be $true
    }

    It "documents data.table-collapse dialect in config table" {
        ($content -match 'data\.table-collapse') | Should Be $true
    }

    It "contains Priority Levels table with P0 BLOCKING entry" {
        ($content -match 'P0.*BLOCKING') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.4 — dialect-aware agents document r-syntax and both dialects
# ---------------------------------------------------------------------------

Describe "R-dialect-aware agents - r-syntax handling" {
    $dialectAwareAgents = @('cg-code-quality', 'cg-data-quality', 'cg-performance')

    foreach ($agent in $dialectAwareAgents) {
        $agentFile = Join-Path $repoRoot ".github\agents\$agent.agent.md"
        $agentContent = if (Test-Path $agentFile) { Get-Content $agentFile -Raw -Encoding UTF8 } else { "" }

        It "$agent mentions r-syntax" {
            ($agentContent -match 'r-syntax') | Should Be $true
        }

        It "$agent documents data.table-collapse dialect" {
            ($agentContent -match 'data\.table-collapse') | Should Be $true
        }

        It "$agent documents tidyverse dialect" {
            ($agentContent -match 'tidyverse') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# P3.1 — dialect skill reference files exist by name
# ---------------------------------------------------------------------------

Describe "R dialect skills - reference files exist" {
    $expectedRefFiles = @{
        'cg-skill-r-collapse'      = @('collapse-reference.md', 'collapse-anti-patterns.md')
        'cg-skill-r-datatable'     = @('datatable-reference.md', 'datatable-anti-patterns.md')
        'cg-skill-r-tidyverse'     = @('tidyverse-reference.md', 'tidyverse-anti-patterns.md',
                                        'tidyverse-style.md', 'tidyverse-migration.md')
        'cg-skill-r-visualization' = @('ggplot2-reference.md')
    }

    foreach ($skill in $expectedRefFiles.Keys) {
        foreach ($refFile in $expectedRefFiles[$skill]) {
            It "$skill/references/$refFile exists" {
                $path = Join-Path $repoRoot ".github\skills\$skill\references\$refFile"
                Test-Path $path | Should Be $true
            }
        }
    }
}

# Model assignment tests have been extracted to tests/model-assignments.Tests.ps1.
# Run: Invoke-Pester tests/model-assignments.Tests.ps1 -Quiet

# ---------------------------------------------------------------------------
# P1.2 — agent files must declare a tools: restriction (read-only enforcement)
# cg-roadmap uses ['read','write']; all others must NOT include 'write'.
# ---------------------------------------------------------------------------

Describe "Agent files - tools restriction enforcement" {
    $agentsDir = Join-Path $repoRoot ".github\agents"
    $agentFiles = @(Get-ChildItem -Path $agentsDir -Filter "*.agent.md" -File)

    foreach ($file in $agentFiles) {
        $filePath  = $file.FullName
        $relPath   = $file.Name
        $fm        = Get-Frontmatter -FilePath $filePath

        It "$relPath has a tools: key in frontmatter" {
            ($fm -match 'tools:') | Should Be $true
        }
    }

    # Review-only agents must not include the 'write' tool
    # cg-roadmap.agent.md uses write for roadmap updates; cg-fix-problems.agent.md uses editFiles (not write)
    $reviewAgents = $agentFiles | Where-Object { $_.Name -ne 'cg-roadmap.agent.md' -and $_.Name -ne 'cg-fix-problems.agent.md' }

    foreach ($file in $reviewAgents) {
        $filePath = $file.FullName
        $relPath  = $file.Name
        $fm       = Get-Frontmatter -FilePath $filePath
        $tools    = Get-ToolsList -Frontmatter $fm

        It "$relPath does not include 'write' in its tools list (read-only reviewer)" {
            ($tools -contains 'write') | Should Be $false
        }
    }
}

# ---------------------------------------------------------------------------
# P2.2 — cg-compound.prompt.md structural tests
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }
}

Describe "cg-compound.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should Match 'description:'
        }

        It "has a model in frontmatter" {
            $frontmatter | Should Match 'model:'
        }
    }
}

Describe "cg-compound.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "orchestrator must have unrestricted tools" {
        It "does not have a tools: key (write access required for saving solution files)" {
            ($frontmatter -notmatch 'tools:') | Should Be $true
        }
    }
}

Describe "cg-compound.prompt.md - severity field includes P0" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "severity field template includes P0 option" {
        ($content -match '<P0\|P1\|P2\|P3>') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.3 — orchestrating prompts must not have tools: restrictions
# cg-work, cg-brainstorm, cg-plan
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (orchestrating prompts need unrestricted access)" {
            ($frontmatter -notmatch 'tools:') | Should Be $true
        }
    }
}

Describe "cg-brainstorm.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (orchestrating prompts need unrestricted access)" {
            ($frontmatter -notmatch 'tools:') | Should Be $true
        }
    }
}

Describe "cg-plan.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (orchestrating prompts need unrestricted access)" {
            ($frontmatter -notmatch 'tools:') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# P2.4 — agent files must have substantive body content (not just frontmatter)
# ---------------------------------------------------------------------------

Describe "Agent files - non-trivial body content" {
    $agentsDir = Join-Path $repoRoot ".github\agents"
    $agentFiles = @(Get-ChildItem -Path $agentsDir -Filter "*.agent.md" -File)

    foreach ($file in $agentFiles) {
        $filePath = $file.FullName
        $relPath  = $file.Name
        $raw      = Get-Content $filePath -Raw -Encoding UTF8

        # Strip frontmatter (everything between the first two --- delimiters)
        $body = $raw -replace '(?s)^---.*?---\s*', ''

        It "$relPath has substantive body content (body > 100 chars)" {
            $body.Trim().Length | Should BeGreaterThan 100
        }
    }
}

# ---------------------------------------------------------------------------
# P3.2 — Get-Frontmatter helper negative-case tests
# ---------------------------------------------------------------------------

Describe "Get-Frontmatter helper - edge cases" {
    # Create temp files in the system temp directory for isolation
    $tmpNoFm   = [System.IO.Path]::GetTempFileName() + ".md"
    $tmpPartFm = [System.IO.Path]::GetTempFileName() + ".md"

    # File with no frontmatter at all
    "# Just a heading`n`nSome content." | Set-Content $tmpNoFm -Encoding UTF8

    # File with an opening --- but no closing ---
    "---`ndescription: orphan`n# Heading" | Set-Content $tmpPartFm -Encoding UTF8

    It "returns empty string when the file has no frontmatter" {
        $result = Get-Frontmatter -FilePath $tmpNoFm
        $result | Should BeNullOrEmpty
    }

    It "returns empty string when the frontmatter is unclosed (missing closing ---)" {
        $result = Get-Frontmatter -FilePath $tmpPartFm
        $result | Should BeNullOrEmpty
    }

    # Clean up temp files
    Remove-Item $tmpNoFm  -ErrorAction SilentlyContinue
    Remove-Item $tmpPartFm -ErrorAction SilentlyContinue
}

# ---------------------------------------------------------------------------
# P1.18 — cg-brainstorm Step 0.5 prior work scan
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 0.5 prior work scan" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "scans .cg-docs/brainstorms/ for prior work" {
        ($content -match '\.cg-docs[/\\]brainstorms') | Should Be $true
    }

    It "presents Continue option" {
        ($content -match '\*\*Continue\*\*') | Should Be $true
    }

    It "presents Start fresh option" {
        ($content -match 'Start fresh') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.19 — cg-brainstorm Step 1.1 Task Classification / Thinking Partner Mode
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 1.1 Task Classification" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 1.1 Task Classification" {
        ($content -match 'Step 1\.1.*Task Classification') | Should Be $true
    }

    It "defines Thinking Partner Mode" {
        ($content -match 'Thinking Partner Mode') | Should Be $true
    }

    It "skips roadmap registration for non-software tasks" {
        ($content -match '[Ss]kip roadmap') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.20 — cg-brainstorm Step 1.5 scope assessment
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 1.5 Scope Assessment" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 1.5 Scope Assessment" {
        ($content -match 'Step 1\.5.*Scope Assessment') | Should Be $true
    }

    It "defines Lightweight scope tier" {
        ($content -match '\*\*Lightweight\*\*') | Should Be $true
    }

    It "defines Standard scope tier" {
        ($content -match '\*\*Standard\*\*') | Should Be $true
    }

    It "defines Deep scope tier" {
        ($content -match '\*\*Deep\*\*') | Should Be $true
    }

    It "includes Scope assessment output line" {
        ($content -match 'Scope assessment:') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.21 — cg-plan Step 0.5 prior work scan
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Step 0.5 prior work scan" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "scans .cg-docs/plans/ for prior work" {
        ($content -match '\.cg-docs[/\\]plans') | Should Be $true
    }

    It "presents Refine option" {
        ($content -match '\*\*Refine\*\*') | Should Be $true
    }

    It "presents Follow-up option" {
        ($content -match '\*\*Follow-up\*\*') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.22 — cg-plan Step 1.5 scope assessment
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Step 1.5 Scope Assessment" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 1.5 Scope Assessment" {
        ($content -match 'Step 1\.5.*Scope Assessment') | Should Be $true
    }

    It "includes Lightweight criteria (1-3 steps)" {
        ($content -match '1.3 steps') | Should Be $true
    }

    It "includes Standard criteria (3-8 steps)" {
        ($content -match '3.8 steps') | Should Be $true
    }

    It "includes Deep criteria (8+ steps)" {
        ($content -match '8\+ steps') | Should Be $true
    }

    It "includes Scope assessment output line" {
        ($content -match 'Scope assessment:') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.23 — cg-plan Step 4.5 confidence check
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Step 4.5 Confidence Check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 4.5 Confidence Check" {
        ($content -match 'Step 4\.5.*Confidence Check') | Should Be $true
    }

    It "checks Completeness dimension" {
        ($content -match '\*\*Completeness\*\*') | Should Be $true
    }

    It "checks Testability dimension" {
        ($content -match '\*\*Testability\*\*') | Should Be $true
    }

    It "checks Dependencies dimension" {
        ($content -match '\*\*Dependencies\*\*') | Should Be $true
    }

    It "checks Risk coverage dimension" {
        ($content -match '\*\*Risk coverage\*\*') | Should Be $true
    }

    It "checks Scope clarity dimension" {
        ($content -match '\*\*Scope clarity\*\*') | Should Be $true
    }

    It "defines High / Medium / Low confidence levels" {
        ($content -match '\*\*High\*\*' -and $content -match '\*\*Medium\*\*' -and $content -match '\*\*Low\*\*') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.24 — cg-plan Test Scenarios template (checkmark/warning/cross)
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Test Scenarios template" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Test Scenarios field in step template" {
        ($content -match '\*\*Test Scenarios\*\*:') | Should Be $true
    }

    It "includes happy path marker" {
        ($content -match '[Hh]appy path') | Should Be $true
    }

    It "includes edge case marker" {
        ($content -match '[Ee]dge case') | Should Be $true
    }

    It "includes error path marker" {
        ($content -match '[Ee]rror path') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.25 — cg-review Step 1.5 content-based depth overrides
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - Step 1.5 depth overrides" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 1.5 Content-Based Depth Overrides" {
        ($content -match 'Step 1\.5.*Content-Based Depth Overrides') | Should Be $true
    }

    It "includes pipeline/scripts trigger adding @cg-data-quality" {
        ($content -match 'pipeline.*@cg-data-quality|scripts.*@cg-data-quality') | Should Be $true
    }

    It "includes >= 50 non-test lines escalation trigger" {
        ($content -match '50 non-test lines') | Should Be $true
    }

    It "includes authentication/secrets trigger adding @cg-version-control" {
        ($content -match 'authentication.*secrets|secrets.*credentials') | Should Be $true
    }

    It "includes statistical functions trigger adding @cg-data-quality" {
        ($content -match 'statistical functions|fmean') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.26 — cg-review @cg-adversarial in thorough depth list
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - @cg-adversarial in thorough depth" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes @cg-adversarial in Thorough section" {
        ($content -match '(?s)Thorough.*?@cg-adversarial') | Should Be $true
    }

    It "@cg-adversarial is NOT in Light section" {
        $lightSection = if ($content -match '(?s)\*\*Light\*\*.*?\*\*Standard\*\*') { $Matches[0] } else { '' }
        ($lightSection -match '@cg-adversarial') | Should Be $false
    }
}

# ---------------------------------------------------------------------------
# P1.27 — cg-review protected artifacts guard
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - protected artifacts guard" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "mentions Protected artifacts section" {
        ($content -match 'Protected artifacts') | Should Be $true
    }

    It "lists .cg-docs subdirectories as protected" {
        ($content -match '\.cg-docs') | Should Be $true
    }

    It "lists compound-gpid.md as a protected file" {
        ($content -match 'compound-gpid\.md') | Should Be $true
    }

    It "lists roadmap.json as a protected file" {
        ($content -match 'roadmap\.json') | Should Be $true
    }

    It "guard instructs discarding delete/replace/rename/move findings" {
        ($content -match 'Discard any finding.*delet') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.28 — cg-review mode:autofix argument parsing
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - mode:autofix argument" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents mode:autofix argument" {
        ($content -match 'mode:autofix') | Should Be $true
    }

    It "defines safe_auto and advisory tags" {
        ($content -match '(?s)Step 4.*safe_auto.*advisory') | Should Be $true
    }

    It "includes Autofix complete report template" {
        ($content -match 'Autofix complete:.*safe fixes') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.29 — cg-review P0 BLOCKING section in report template
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - P0 BLOCKING in report template" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes ### P0 BLOCKING section in report template" {
        ($content -match '### P0.*BLOCKING') | Should Be $true
    }

    It "P0 BLOCKING appears before P1 CRITICAL in report" {
        ($content -match '(?s)P0.*BLOCKING.*P1.*CRITICAL') | Should Be $true
    }

    It "P0 section includes immediate remediation language" {
        ($content -match '(?s)P0.*immediate') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.30 — cg-work inline plan fallback
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - inline plan fallback" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "describes lightweight inline plan fallback when no plan found" {
        ($content -match 'lightweight inline plan') | Should Be $true
    }

    It "inline plan is described as 3-5 steps" {
        ($content -match '3.5 steps') | Should Be $true
    }

    It "offers Proceed with this or run /cg-plan option" {
        ($content -match 'Proceed with this.*cg-plan') | Should Be $true
    }

    It "skips roadmap linking Step 1.5 when using inline plan" {
        ($content -match 'Skip Step 1\.5') | Should Be $true
    }

    It "saves inline plan to .cg-docs/plans/ before implementing" {
        ($content -match '\.cg-docs[/\\]plans.*YYYY-MM-DD') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.31 — cg-work Discover existing tests sub-step
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Discover existing tests sub-step" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Discover existing tests sub-step" {
        ($content -match 'Discover existing tests') | Should Be $true
    }

    It "instructs searching for test files before implementing" {
        ($content -match '[Bb]efore implementing.*scan|[Ss]earch for test files') | Should Be $true
    }

    It "references .Tests.ps1 test file pattern" {
        ($content -match '\.Tests\.ps1') | Should Be $true
    }

    It "instructs running both existing and new tests" {
        ($content -match 'existing tests AND the new tests|discovered.*tests AND.*new tests') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.32 — cg-work Step 3.2 self-review
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 3.2 Self-Review" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 3.2 Self-Review section" {
        ($content -match 'Step 3\.2.*Self-Review') | Should Be $true
    }

    It "scans for print( debug code pattern" {
        ($content -match 'print\(') | Should Be $true
    }

    It "checks for missing tests on new public functions" {
        ($content -match 'new public function') | Should Be $true
    }

    It "scans for TODO FIXME HACK XXX markers" {
        ($content -match 'TODO.*FIXME.*HACK') | Should Be $true
    }

    It "emits a self-review complete summary line" {
        ($content -match '[Ss]elf-review complete:') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P3.13 — cg-review depth override arguments documented
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - depth override arguments" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents light, standard, and thorough as Override arguments" {
        ($content -match '(?i)light.*standard.*thorough') | Should Be $true
    }

    It "references review depth from compound-gpid.local.md for default" {
        ($content -match 'compound-gpid\.local') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.33 — cg-fix-problems.prompt.md existence, frontmatter, no tool restriction
# ---------------------------------------------------------------------------

Describe "cg-fix-problems.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-problems.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }
}

Describe "cg-fix-problems.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-problems.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should Match 'description:'
        }

        It "has a model in frontmatter" {
            $frontmatter | Should Match 'model:'
        }
    }
}

Describe "cg-fix-problems.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-problems.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "orchestrator must have unrestricted tools" {
        It "does not have a tools: key (write access required for orchestrating prompts)" {
            ($frontmatter -notmatch '(?m)^\s*tools:') | Should Be $true
        }
    }
}

Describe "cg-fix-problems.prompt.md - dispatches agent and scans diagnostics" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-problems.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "dispatches @cg-fix-problems agent" {
        ($content -match '@cg-fix-problems') | Should Be $true
    }

    It "references get_errors for diagnostics scanning" {
        ($content -match 'get_errors') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.34 — cg-fix-problems.agent.md existence, user-invocable false, auto mode protocol
# ---------------------------------------------------------------------------

Describe "cg-fix-problems.agent.md - user-invocable false" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-fix-problems.agent.md"
    $frontmatter = Get-Frontmatter -FilePath $agentFile

    It "exists in the repository" {
        Test-Path $agentFile | Should Be $true
    }

    It "has user-invocable: false in frontmatter" {
        ($frontmatter -match 'user-invocable:\s*false') | Should Be $true
    }

    It "has editFiles in its tools list (required to apply code fixes)" {
        ($frontmatter -match 'editFiles') | Should Be $true
    }
}

Describe "cg-fix-problems.agent.md - auto mode protocol" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-fix-problems.agent.md"
    $content = Get-Content $agentFile -Raw -Encoding UTF8

    It "documents 2-round retry budget" {
        ($content -match '2[ \-]round|two[ \-]round|Round 2') | Should Be $true
    }

    It "documents errors-only filter for auto mode" {
        ($content -match '(?i)errors only') | Should Be $true
    }

    It "references get_errors diagnostics tool" {
        ($content -match 'get_errors') | Should Be $true
    }

    It "documents hard stop after round 2" {
        ($content -match '[Hh]ard [Ss]top|Hard stop') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.35 — cg-work auto-dispatch @cg-fix-problems
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - auto-dispatch @cg-fix-problems" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references @cg-fix-problems agent" {
        ($content -match '@cg-fix-problems') | Should Be $true
    }

    It "documents 2-round retry budget" {
        ($content -match '2[ \-]round|two[ \-]round|2 rounds') | Should Be $true
    }

    It "documents errors-only scope for auto mode" {
        ($content -match '(?i)errors only') | Should Be $true
    }

    It "explicitly suppresses auto-dispatch when no errors are present (warnings-only guard)" {
        ($content -match 'Suppress this step.*no errors|no errors are present|when.*get_errors.*returns no errors') | Should Be $true
    }

    It "passes mode: auto to the agent dispatch (not interactive)" {
        ($content -match 'mode:\s*auto') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.36 — cg-work roadmap status update must happen before summary wait
# Bug: Step 5 (Update Roadmap Status) was placed after Step 4 (Summary).
# Step 4 ends with "Wait for the user's response before proceeding."
# In practice the user picks a next action (/cg-review etc.) and the
# cg-work session ends — Step 5 never executes, causing roadmap drift.
# Fix: move roadmap update to before the summary / user-wait.
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - roadmap done update before summary wait" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "'to status done.' dispatch phrase is present in the prompt" {
        $content.IndexOf("to status done.") | Should BeGreaterThan -1
    }

    It "'Wait for the user's response before proceeding' phrase is present in the prompt" {
        $content.IndexOf("Wait for the user's response before proceeding") | Should BeGreaterThan -1
    }

    It "dispatches roadmap 'to status done.' update BEFORE the 'Wait for the user' pause (prevents roadmap drift)" {
        $waitPos = $content.IndexOf("Wait for the user's response before proceeding")
        $donePos = $content.IndexOf("to status done.")
        # The roadmap update must precede the user-wait pause
        $donePos | Should BeLessThan $waitPos
    }

    It "Step 3.7 appears between Step 3.5 and Step 4 in the file" {
        $step35Pos = $content.IndexOf("### Step 3.5:")
        $step37Pos = $content.IndexOf("### Step 3.7:")
        $step4Pos  = $content.IndexOf("### Step 4:")
        $step35Pos | Should BeGreaterThan -1
        $step37Pos | Should BeGreaterThan -1
        $step4Pos  | Should BeGreaterThan -1
        $step37Pos | Should BeGreaterThan $step35Pos
        $step37Pos | Should BeLessThan $step4Pos
    }
}
