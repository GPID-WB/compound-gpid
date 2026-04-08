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

    It "uses compound finding IDs like [P1.1], [P2.1], [P3.1] in the output template" {
        ($content -match '\*\*\[P[123]\.\d+\]\*\*') | Should Be $true
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
# Skill SKILL.md cross-references - relative links resolve to real files
# ---------------------------------------------------------------------------

Describe "skill SKILL.md - relative markdown links resolve" {
    $skillsDir = Join-Path $repoRoot ".github\skills"
    $skillFiles = Get-ChildItem -Path $skillsDir -Recurse -Filter "SKILL.md"

    foreach ($skill in $skillFiles) {
        $skillName = (Split-Path (Split-Path $skill.FullName -Parent) -Leaf)
        $content = Get-Content $skill.FullName -Raw -Encoding UTF8
        $skillDir = Split-Path $skill.FullName -Parent

        # Extract relative file links (exclude http/https URLs and anchor-only links)
        $links = [regex]::Matches($content, '\]\(([^)#]+)\)') |
            ForEach-Object { $_.Groups[1].Value } |
            Where-Object { $_ -notmatch '^https?://' -and $_ -match '\.' }

        foreach ($link in $links) {
            $resolved = [System.IO.Path]::GetFullPath((Join-Path $skillDir $link))
            It "$($skillName): '$($link)' resolves to an existing file" {
                Test-Path $resolved | Should Be $true
            }
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

    It "SCHEMA_VERSION contains r-syntax-dialect marker" {
        ($content -match 'r-syntax-dialect') | Should Be $true
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
# Run: Invoke-Pester tests/model-assignments.Tests.ps1 -Output Minimal
