# tests/prompt-tools.Tests.ps1
# Pester tests to guard prompt file structure and tool configuration
#
# Run with: . tests\Run-Tests.ps1 -File prompt-tools
# Project requirement: Pester 4.10.1. Do not rely on the Windows built-in 3.4 runner.
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
if ($env:CG_TEST_ROOT -and -not (Test-Path $env:CG_TEST_ROOT)) { throw "CG_TEST_ROOT '$env:CG_TEST_ROOT' does not exist" }
. "$PSScriptRoot/helpers.ps1"

# Note: Get-ToolsList is defined in helpers.ps1 (shared helper, moved here to avoid duplication across test files)

# ---------------------------------------------------------------------------
# cg-review.prompt.md must NOT have a tools: restriction
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (a tools: whitelist strips write access from the orchestrating agent)" {
            ($frontmatter -notmatch 'tools:') | Should -Be $true
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
        ($content -match '\.cg-docs[/\\]reviews') | Should -Be $true
    }

    It "uses compound finding IDs like [P0.1], [P1.1], [P2.1], [P3.1] in the output template" {
        ($content -match '\*\*\[P[0123]\.\d+\]\*\*') | Should -Be $true
    }

    It "includes /cg-fix-triage usage instruction with a compound ID example" {
        ($content -match '/cg-fix-triage.*P\d\.\d') | Should -Be $true
    }

    It "mentions /cg-fix-triage so users know how to apply findings" {
        ($content -match '/cg-fix-triage') | Should -Be $true
    }

    It "explicitly instructs DO NOT delegate the Step 3.5 file write" {
        ($content -match 'Do NOT delegate') | Should -Be $true
    }

    It "documents 'no issues found' as valid output when an agent finds nothing" {
        ($content -match 'no issues found') | Should -Be $true
    }

    It "includes R package .Rbuildignore check for .cg-docs/" {
        ($content -match '\.Rbuildignore') | Should -Be $true
    }

    It "Step 3.5 falls back to last-write time when date: is absent" {
        ($content -match 'last.write|absent.*fall back') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-fix-triage.prompt.md existence and content
# ---------------------------------------------------------------------------

Describe "cg-fix-triage.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-fix-triage.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"

    Context "required frontmatter fields" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "has a description in frontmatter" {
            $frontmatter | Should -Match 'description:'
        }

        It "inherits the selected model without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }
}

Describe "cg-fix-triage.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (a tools: whitelist strips write access from the orchestrating agent)" {
            ($frontmatter -notmatch 'tools:') | Should -Be $true
        }
    }
}

Describe "cg-fix-triage.prompt.md - review reports location" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references .cg-docs/reviews/ directory to load saved review reports" {
        ($content -match '\.cg-docs[/\\]reviews') | Should -Be $true
    }
}


# ---------------------------------------------------------------------------
# cg-strategy.prompt.md existence, frontmatter, and no tool restriction
# ---------------------------------------------------------------------------

Describe "cg-strategy.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-strategy.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-strategy.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-strategy.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should -Match 'description:'
        }

        It "inherits the Copilot model picker without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }
}

Describe "cg-strategy.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-strategy.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (restrictions are prose-only per convention)" {
            ($frontmatter -notmatch 'tools:') | Should -Be $true
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
        ($section -match '/cg-strategy') | Should -Be $true
    }

    It "references /cg-brainstorm in Workflow Entry Points" {
        ($section -match '/cg-brainstorm') | Should -Be $true
    }

    It "references /cg-plan in Workflow Entry Points" {
        ($section -match '/cg-plan') | Should -Be $true
    }

    It "references @cg-roadmap in Workflow Entry Points" {
        ($section -match '@cg-roadmap') | Should -Be $true
    }

    It "references /cg-resume in Workflow Entry Points" {
        ($section -match '/cg-resume') | Should -Be $true
    }

    It "references /cg-work in Workflow Entry Points" {
        ($section -match '/cg-work') | Should -Be $true
    }

    It "references /cg-review in Workflow Entry Points" {
        ($section -match '/cg-review') | Should -Be $true
    }

    It "references /cg-fix-triage in Workflow Entry Points" {
        ($section -match '/cg-fix-triage') | Should -Be $true
    }

    It "references /cg-compound in Workflow Entry Points" {
        ($section -match '/cg-compound') | Should -Be $true
    }

    It "references /cg-compound-refresh in Workflow Entry Points" {
        ($section -match '/cg-compound-refresh') | Should -Be $true
    }

    It "references /cg-ideate in Workflow Entry Points" {
        ($section -match '/cg-ideate') | Should -Be $true
    }

    It "references /cg-fix-problems in Workflow Entry Points" {
        ($section -match '/cg-fix-problems') | Should -Be $true
    }

    It "references /cg-plan-review in Workflow Entry Points" {
        ($section -match '/cg-plan-review') | Should -Be $true
    }

    It "documents /cg-work phaseX for implementing a specific phase (P3.6)" {
        ($section -match '/cg-work phaseX|cg-work phase') | Should -Be $true
    }

    # P2.1 â€” /cg-roadmap-view in Workflow Entry Points
    It "references /cg-roadmap-view in Workflow Entry Points" {
        ($section -match '/cg-roadmap-view') | Should -Be $true
    }

    It "references /cg-commit-push-pr in Workflow Entry Points" {
        ($section -match '/cg-commit-push-pr') | Should -Be $true
    }

    It "references /cg-verify-pr in Workflow Entry Points" {
        ($section -match '/cg-verify-pr') | Should -Be $true
    }

    # P2.6 â€” /cg-wiki added to Workflow Entry Points
    It "references /cg-wiki in Workflow Entry Points" {
        ($section -match '/cg-wiki') | Should -Be $true
    }

    # P2.7 -- /cg-issues added to Workflow Entry Points
    It "references /cg-issues in Workflow Entry Points" {
        ($section -match '/cg-issues') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-review.prompt.md - review findings frontmatter
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - review findings frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references the findings: frontmatter key in Step 3.5" {
        ($content -match 'findings:') | Should -Be $true
    }

    It "sets new findings to status: open in Step 3.5" {
        ($content -match '\bopen\b') | Should -Be $true
    }

    It "mentions status: fixed as a valid finding status" {
        ($content -match '\bfixed\b') | Should -Be $true
    }

    It "mentions status: skipped as a valid finding status" {
        ($content -match '\bskipped\b') | Should -Be $true
    }

    It "includes a plan: key in the frontmatter template" {
        ($content -match '(?s)plan:.*findings:|(?s)findings:.*plan:') | Should -Be $true
    }

    It "includes date, depth, and standard type in the normal review frontmatter template" {
        ($content -match 'date:\s*YYYY-MM-DD') | Should -Be $true
        ($content -match 'depth:\s*<light\|standard\|data-risk\|architecture\|full>') | Should -Be $true
        ($content -match 'type:\s*standard') | Should -Be $true
    }

    It "documents P0 finding ID pattern in Step 3.5" {
        ($content -match [regex]::Escape('**[P0.')) | Should -Be $true
    }

    It "documents P1 finding ID pattern in Step 3.5" {
        ($content -match [regex]::Escape('**[P1.')) | Should -Be $true
    }

    It "documents P2 finding ID pattern in Step 3.5" {
        ($content -match [regex]::Escape('**[P2.')) | Should -Be $true
    }

    It "documents P3 finding ID pattern in Step 3.5" {
        ($content -match [regex]::Escape('**[P3.')) | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-fix-triage.prompt.md - per-finding status tracking
# ---------------------------------------------------------------------------

Describe "cg-fix-triage.prompt.md - per-finding status tracking" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references the findings: frontmatter key" {
        ($content -match 'findings:') | Should -Be $true
    }

    It "instructs updating finding status to fixed in frontmatter after applying a fix" {
        ($content -match 'fixed') -and ($content -match 'frontmatter') | Should -Be $true
    }

    It "instructs updating finding status to skipped in frontmatter when user declines" {
        ($content -match 'skipped') | Should -Be $true
    }

    It "references --migrate mode" {
        ($content -match '\-\-migrate') | Should -Be $true
    }

    It "describes the companion-plan heuristic in --migrate mode" {
        ($content -match 'companion[- ]plan|companion plan') | Should -Be $true
    }

    It "reports Previously resolved count in summary template" {
        ($content -match 'Previously resolved') | Should -Be $true
    }

    It "Step 3 apply order lists P0 first before P1" {
        ($content -match 'P0 first') | Should -Be $true
    }

    It "warns the user when there are more than 15 open findings (large report guard)" {
        ($content -match '15 open|more than 15') | Should -Be $true
    }

    It "recommends priority batches (P0 P1, P2, P3) in the large report warning" {
        ($content -match 'P0 P1.*P2.*P3|priority batch') | Should -Be $true
    }

    It "instructs DO NOT delegate frontmatter status update to a subagent" {
        ($content -match 'Do NOT delegate') | Should -Be $true
    }

    It "loads cg-skill-fix-triage-migrate for --migrate mode by name" {
        ($content -match 'cg-skill-fix-triage-migrate') | Should -Be $true
    }

    It "Step 0.5 instructs skipping skill load when invoked as --migrate" {
        ($content -match 'Skip this step if invoked as.*--migrate') | Should -Be $true
    }

    It "warns on unrecognized arguments with recognized options list" {
        ($content -match 'Unrecognized argument') -and ($content -match '\-\-migrate') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-skill-fix-triage-migrate SKILL.md - behavioral rules
# ---------------------------------------------------------------------------

Describe "cg-skill-fix-triage-migrate SKILL.md - behavioral rules" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-fix-triage-migrate\SKILL.md"
    $content = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }

    It "documents all-open default for findings" {
        ($content -match 'Set all findings to.*open|defaulted to.*open|all findings.*open') | Should -Be $true
    }

    It "instructs do NOT delegate to subagent for file writes" {
        ($content -match 'do NOT delegate|NOT delegate') | Should -Be $true
    }

    It "has 'No legacy review files found' response for empty scan result" {
        ($content -match 'No legacy review files found') | Should -Be $true
    }

    It "instructs prepending full frontmatter block when no frontmatter exists" {
        ($content -match 'prepend full block') | Should -Be $true
    }

    It "uses generic <id> placeholder in frontmatter template (not hardcoded P1.1)" {
        ($content -match '<id>:') | Should -Be $true
    }

    It "documents that <id> should be replaced with actual parsed IDs" {
        ($content -match 'replace <id> with actual IDs|actual IDs.*e\.g\.') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-resume.prompt.md - findings frontmatter and migration nudge
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - findings frontmatter and migration nudge" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references the findings: frontmatter key in Step 2e" {
        ($content -match 'findings:') | Should -Be $true
    }

    It "instructs skipping fully-resolved review files (zero open findings)" {
        ($content -match 'zero|fully resolved|skip it') | Should -Be $true
    }

    It "references --migrate nudge for legacy review files without frontmatter" {
        ($content -match '\-\-migrate') | Should -Be $true
    }

    It "adds migration nudge to Maintenance Nudges section" {
        ($content -match 'Review migration needed') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# SKILL.md files - required frontmatter
# ---------------------------------------------------------------------------

Describe "SKILL.md files - required frontmatter" {
    $skillsDir = Join-Path $repoRoot ".github\skills"
    $skillFiles = Get-ChildItem -Path $skillsDir -Recurse -Filter "SKILL.md"

    It "finds at least one SKILL.md file" {
        $skillFiles.Count | Should -BeGreaterThan 0
    }

    foreach ($skill in $skillFiles) {
        $skillName = (Split-Path (Split-Path $skill.FullName -Parent) -Leaf)
        $frontmatter = Get-Frontmatter -FilePath $skill.FullName

        It "$skillName SKILL.md has a name: field" {
            $frontmatter | Should -Match '(?m)^\s*name:'
        }

        It "$skillName SKILL.md has a description: field" {
            $frontmatter | Should -Match '(?m)^\s*description:'
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
            Test-Path (Join-Path $skillRoot $file) | Should -Be $true
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
        # Strip inline code spans before extracting links (backtick content = examples, not real cross-links)
        $contentForLinks = $content -replace '`[^`\r\n]+`', ''
        # Extract markdown links: [text](path) â€” skip anchors and external URLs
        $links = [regex]::Matches($contentForLinks, '\[[^\]]*\]\(([^)#]+\.md)\)')
        foreach ($link in $links) {
            $target = $link.Groups[1].Value
            if ($target -match '^https?://') { continue }
            $resolved = [System.IO.Path]::GetFullPath(
                [System.IO.Path]::Combine($skillFile.DirectoryName, $target)
            )
            $relSource = $skillFile.FullName.Replace($repoRoot + "\", "")
            It "$relSource -> $target" {
                Test-Path $resolved | Should -Be $true
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
        ($content -match 'Subagent Output Quality Check') | Should -Be $true
    }

    It "mentions the Incomplete Reviews warning section for failed agents" {
        ($content -match 'Incomplete Reviews') | Should -Be $true
    }

    It "instructs NOT to retry the agent automatically" {
        ($content -match 'NOT retry') | Should -Be $true
    }

    It "lists empty or garbled output as quality failure criteria" {
        ($content -match 'empty.*garbled|garbled.*empty') | Should -Be $true
    }

    It "includes the warning template with @agent-name placeholder" {
        ($content -match '@<agent-name>') | Should -Be $true
    }

    It "documents the Presence criterion by name" {
        ($content -match '\bPresence\b') | Should -Be $true
    }

    It "documents the Context criterion by name" {
        ($content -match '\bContext\b') | Should -Be $true
    }

    It "documents the Volume criterion by name" {
        ($content -match '\bVolume\b') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-compound-refresh.prompt.md - file existence, frontmatter, and no tool restriction
# (Orchestrating prompts must not have a tools: whitelist -- it strips write access)
# ---------------------------------------------------------------------------

Describe "cg-compound-refresh.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound-refresh.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-compound-refresh.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound-refresh.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should -Match 'description:'
        }

        It "inherits the selected model without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }
}

Describe "cg-compound-refresh.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound-refresh.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (a tools: whitelist strips write access from the orchestrating prompt)" {
            ($frontmatter -notmatch '(?m)^\s*tools:') | Should -Be $true
        }
    }
}

Describe "cg-compound-refresh.prompt.md - Step 7 brain index count reporting" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound-refresh.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 7 instructs parsing entity/topic/edge counts from cg-index output" {
        ($content -match 'entity.*topic.*edge|entities.*topics.*edges') | Should -Be $true
    }

    It "Step 7 references the [cg-index] Brain index written to stdout pattern" {
        ($content -match '\[cg-index\] Brain index written to') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-ideate.prompt.md - file existence, frontmatter, and no tool restriction
# (Orchestrating prompts must not have a tools: whitelist -- it strips write access)
# ---------------------------------------------------------------------------

Describe "cg-ideate.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-ideate.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-ideate.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-ideate.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should -Match 'description:'
        }

        It "inherits the Copilot model picker without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }
}

Describe "cg-ideate.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-ideate.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (a tools: whitelist strips write access from the orchestrating prompt)" {
            ($frontmatter -notmatch '(?m)^\s*tools:') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# R dialect routing â€” r.instructions.md validation
# ---------------------------------------------------------------------------

Describe "r.instructions.md - dialect router" {
    $routerFile = Join-Path $repoRoot ".github\instructions\r.instructions.md"

    It "router file exists" {
        Test-Path $routerFile | Should -Be $true
    }

    $content = if (Test-Path $routerFile) { Get-Content $routerFile -Raw -Encoding UTF8 } else { "" }

    It "documents data.table-collapse dialect" {
        ($content -match 'data\.table-collapse') | Should -Be $true
    }

    It "routes to cg-skill-r-collapse for data.table-collapse" {
        ($content -match 'cg-skill-r-collapse') | Should -Be $true
    }

    It "routes to cg-skill-r-datatable for data.table-collapse" {
        ($content -match 'cg-skill-r-datatable') | Should -Be $true
    }

    It "documents tidyverse dialect" {
        ($content -match 'tidyverse') | Should -Be $true
    }

    It "routes to cg-skill-r-tidyverse for tidyverse" {
        ($content -match 'cg-skill-r-tidyverse') | Should -Be $true
    }

    It "mentions cg-skill-r-visualization" {
        ($content -match 'cg-skill-r-visualization') | Should -Be $true
    }

    It "documents fallback for invalid r-syntax values" {
        ($content -match 'Any other value|unrecognized') | Should -Be $true
    }

    # P2.4: applyTo field presence â€” if this field is missing/wrong, dialect routing
    # silently stops working for ALL .R files with no error.
    It "has applyTo frontmatter field (required for auto-apply to .R files)" {
        ($content -match '(?m)^applyTo:') | Should -Be $true
    }

    It "applyTo covers .R files" {
        ($content -match 'applyTo.*\*\*/\*\.R') | Should -Be $true
    }

    It "applyTo covers .r files (lowercase)" {
        ($content -match 'applyTo.*\*\*/\*\.r') | Should -Be $true
    }

    It "applyTo covers .Rmd files" {
        ($content -match 'applyTo.*\*\*/\*\.Rmd') | Should -Be $true
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
            Test-Path $path | Should -Be $true
        }
    }
}

Describe "cg-skill-setup - r-syntax field documentation" {
    $setupFile = Join-Path $repoRoot ".github\skills\cg-skill-setup\SKILL.md"
    $content = if (Test-Path $setupFile) { Get-Content $setupFile -Raw -Encoding UTF8 } else { "" }

    It "documents r-syntax field" {
        ($content -match 'r-syntax') | Should -Be $true
    }

    It "documents data.table-collapse as default dialect" {
        ($content -match 'data\.table-collapse') | Should -Be $true
    }

    It "documents tidyverse as alternative dialect" {
        ($content -match 'tidyverse') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.1 â€” SCHEMA_VERSION dialect marker validation
# ---------------------------------------------------------------------------

Describe "SCHEMA_VERSION - dialect marker" {
    $schemaFile = Join-Path $repoRoot "SCHEMA_VERSION"
    $content = if (Test-Path $schemaFile) { (Get-Content $schemaFile -Raw -Encoding UTF8).Trim() } else { "" }

    It "SCHEMA_VERSION file exists" {
        Test-Path $schemaFile | Should -Be $true
    }

    It "SCHEMA_VERSION contains a descriptive slug (date-prefixed, non-empty)" {
        ($content -match '^\d{4}-\d{2}-\d{2}-.+') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.2 â€” r.instructions.md router covers all 8 unconditional skill references
# ---------------------------------------------------------------------------

Describe "r.instructions.md - unconditional skill routing" {
    $routerFile = Join-Path $repoRoot ".github\instructions\r.instructions.md"
    $content = if (Test-Path $routerFile) { Get-Content $routerFile -Raw -Encoding UTF8 } else { "" }

    It "routes to cg-skill-r-analytical (unconditional)" {
        ($content -match 'cg-skill-r-analytical') | Should -Be $true
    }

    It "routes to cg-skill-r-technical (unconditional)" {
        ($content -match 'cg-skill-r-technical') | Should -Be $true
    }

    It "routes to cg-skill-r-testing (unconditional)" {
        ($content -match 'cg-skill-r-testing') | Should -Be $true
    }

    It "routes to cg-skill-r-shared (unconditional)" {
        ($content -match 'cg-skill-r-shared') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.3 â€” docs/reference.md lists all 8 R skills and r-syntax config field
# ---------------------------------------------------------------------------

Describe "docs/reference.md - R skills and r-syntax config" {
    $refFile = Join-Path $repoRoot "docs\reference.md"
    $content = if (Test-Path $refFile) { Get-Content $refFile -Raw -Encoding UTF8 } else { "" }

    It "docs/reference.md exists" {
        Test-Path $refFile | Should -Be $true
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
            ($content -match [regex]::Escape($skill)) | Should -Be $true
        }
    }

    It "documents r-syntax configuration field" {
        ($content -match 'r-syntax') | Should -Be $true
    }

    It "documents data.table-collapse dialect in config table" {
        ($content -match 'data\.table-collapse') | Should -Be $true
    }

    It "contains Priority Levels table with P0 BLOCKING entry" {
        ($content -match 'P0.*BLOCKING') | Should -Be $true
    }

    It "reference.md documents @cg-release-scanner agent" {
        ($content -match 'cg-release-scanner') | Should -Be $true
    }

    It "reference.md documents @cg-project-scanner agent" {
        ($content -match 'cg-project-scanner') | Should -Be $true
    }

    It "column header uses User-invocable (not User-invokable)" {
        ($content -match 'User-invocable') | Should -Be $true
    }

    It "/cg-compound description states user applies .github/ changes manually" {
        ($content -match 'offers to suggest.*user applies.*manually|user applies.*manually') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.4 â€” dialect-aware agents document r-syntax and both dialects
# ---------------------------------------------------------------------------

Describe "R-dialect-aware agents - r-syntax handling" {
    $dialectAwareAgents = @('cg-code-quality', 'cg-data-quality', 'cg-performance')

    foreach ($agent in $dialectAwareAgents) {
        $agentFile = Join-Path $repoRoot ".github\agents\$agent.agent.md"
        $agentContent = if (Test-Path $agentFile) { Get-Content $agentFile -Raw -Encoding UTF8 } else { "" }

        It "$agent mentions r-syntax" {
            ($agentContent -match 'r-syntax') | Should -Be $true
        }

        It "$agent documents data.table-collapse dialect" {
            ($agentContent -match 'data\.table-collapse') | Should -Be $true
        }

        It "$agent documents tidyverse dialect" {
            ($agentContent -match 'tidyverse') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# P3.1 â€” dialect skill reference files exist by name
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
                Test-Path $path | Should -Be $true
            }
        }
    }
}

# Model assignment tests have been extracted to tests/model-assignments.Tests.ps1.
# Run: Invoke-Pester tests/model-assignments.Tests.ps1 -Quiet

# ---------------------------------------------------------------------------
# P1.2 â€” agent files must declare a tools: restriction (read-only enforcement)
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
            ($fm -match 'tools:') | Should -Be $true
        }
    }

    # Review-only agents must not include the 'write' tool
    # cg-roadmap.agent.md uses write for roadmap updates; cg-fix-problems.agent.md uses editFiles (not write)
    # cg-wiki.agent.md uses write for wiki page creation and updates
    $reviewAgents = $agentFiles | Where-Object { $_.Name -ne 'cg-roadmap.agent.md' -and $_.Name -ne 'cg-fix-problems.agent.md' -and $_.Name -ne 'cg-wiki.agent.md' }

    foreach ($file in $reviewAgents) {
        $filePath = $file.FullName
        $relPath  = $file.Name
        $fm       = Get-Frontmatter -FilePath $filePath
        $tools    = Get-ToolsList -Frontmatter $fm

        It "$relPath does not include 'write' in its tools list (read-only reviewer)" {
            ($tools -contains 'write') | Should -Be $false
        }
    }
}

# ---------------------------------------------------------------------------
# P2.2 â€” cg-compound.prompt.md structural tests
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-compound.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should -Match 'description:'
        }

        It "inherits the selected model without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }
}

Describe "cg-compound.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "orchestrator must have unrestricted tools" {
        It "does not have a tools: key (write access required for saving solution files)" {
            ($frontmatter -notmatch 'tools:') | Should -Be $true
        }
    }
}

Describe "cg-compound.prompt.md - severity field includes P0" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "severity field template includes P0 option" {
        ($content -match '<P0\|P1\|P2\|P3>') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.3 â€” orchestrating prompts must not have tools: restrictions
# cg-work, cg-brainstorm, cg-plan
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (orchestrating prompts need unrestricted access)" {
            ($frontmatter -notmatch 'tools:') | Should -Be $true
        }
    }
}

Describe "cg-brainstorm.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (orchestrating prompts need unrestricted access)" {
            ($frontmatter -notmatch 'tools:') | Should -Be $true
        }
    }
}

Describe "cg-plan.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (orchestrating prompts need unrestricted access)" {
            ($frontmatter -notmatch 'tools:') | Should -Be $true
        }
    }
}

Describe "cg-plan.prompt.md - platform-neutral model-context note" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents active-platform model picker inheritance" {
        ($content -match 'inherits the model picker or runtime configuration selected on the active platform') | Should -Be $true
    }

    It "does not infer an Auto or unknown hidden model" {
        ($content -match 'platform reports Auto or an unknown selection') | Should -Be $true
        ($content -match 'will not infer or name a hidden underlying model') | Should -Be $true
    }

    It "points users to the active platform UI or configuration" {
        ($content -match "inspect the active platform's UI or configuration") | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.4 â€” agent files must have substantive body content (not just frontmatter)
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
            $body.Trim().Length | Should -BeGreaterThan 100
        }
    }
}

# ---------------------------------------------------------------------------
# P3.2 â€” Get-Frontmatter helper negative-case tests
# ---------------------------------------------------------------------------

Describe "Get-Frontmatter helper - edge cases" {
    # Create temp files in the system temp directory for isolation
    $tmpNoFm   = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.IO.Path]::GetRandomFileName() + ".md")
    $tmpPartFm = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.IO.Path]::GetRandomFileName() + ".md")

    # File with no frontmatter at all
    "# Just a heading`n`nSome content." | Set-Content $tmpNoFm -Encoding UTF8

    # File with an opening --- but no closing ---
    "---`ndescription: orphan`n# Heading" | Set-Content $tmpPartFm -Encoding UTF8

    It "returns empty string when the file has no frontmatter" {
        $result = Get-Frontmatter -FilePath $tmpNoFm
        $result | Should -BeNullOrEmpty
    }

    It "returns empty string when the frontmatter is unclosed (missing closing ---)" {
        $result = Get-Frontmatter -FilePath $tmpPartFm
        $result | Should -BeNullOrEmpty
    }

    # Clean up temp files
    Remove-Item $tmpNoFm  -ErrorAction SilentlyContinue
    Remove-Item $tmpPartFm -ErrorAction SilentlyContinue
}

# ---------------------------------------------------------------------------
# P1.18 â€” cg-brainstorm Step 0.5 prior work scan
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 0.5 prior work scan" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "scans .cg-docs/brainstorms/ for prior work" {
        ($content -match '\.cg-docs[/\\]brainstorms') | Should -Be $true
    }

    It "presents Continue option" {
        ($content -match '\*\*Continue\*\*') | Should -Be $true
    }

    It "presents Start fresh option" {
        ($content -match 'Start fresh') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.19 â€” cg-brainstorm Step 1.1 Task Classification / Thinking Partner Mode
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 1.1 Task Classification" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 1.1 Task Classification" {
        ($content -match 'Step 1\.1.*Task Classification') | Should -Be $true
    }

    It "defines Thinking Partner Mode" {
        ($content -match 'Thinking Partner Mode') | Should -Be $true
    }

    It "skips roadmap registration for non-software tasks" {
        ($content -match '[Ss]kip roadmap') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.20 â€” cg-brainstorm Step 1.5 scope assessment
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 1.5 Scope Assessment" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 1.5 Scope Assessment" {
        ($content -match 'Step 1\.5.*Scope Assessment') | Should -Be $true
    }

    It "defines Lightweight scope tier" {
        ($content -match '\*\*Lightweight\*\*') | Should -Be $true
    }

    It "defines Standard scope tier" {
        ($content -match '\*\*Standard\*\*') | Should -Be $true
    }

    It "defines Deep scope tier" {
        ($content -match '\*\*Deep\*\*') | Should -Be $true
    }

    It "includes Scope assessment output line" {
        ($content -match 'Scope assessment:') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.21 â€” cg-plan Step 0.5 prior work scan
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Step 0.5 prior work scan" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "scans .cg-docs/plans/ for prior work" {
        ($content -match '\.cg-docs[/\\]plans') | Should -Be $true
    }

    It "presents Refine option" {
        ($content -match '\*\*Refine\*\*') | Should -Be $true
    }

    It "uses 3+ matching keywords threshold (synced with cg-brainstorm)" {
        ($content -match '3\+?\s*matching keywords') | Should -Be $true
    }

    It "presents Follow-up option" {
        ($content -match '\*\*Follow-up\*\*') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.22 â€” cg-plan Step 1.5 scope assessment
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Step 1.5 Scope Assessment" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 1.5 Scope Assessment" {
        ($content -match 'Step 1\.5.*Scope Assessment') | Should -Be $true
    }

    It "includes Lightweight criteria (1-3 steps)" {
        ($content -match '1.3 steps') | Should -Be $true
    }

    It "includes Standard criteria (3-8 steps)" {
        ($content -match '3.8 steps') | Should -Be $true
    }

    It "includes Deep criteria (8+ steps)" {
        ($content -match '8\+ steps') | Should -Be $true
    }

    It "includes Scope assessment output line" {
        ($content -match 'Scope assessment:') | Should -Be $true
    }

    It "blocks Focused/Extended/Strategic scope as plan input (Thinking Partner guard)" {
        ($content -match 'Thinking Partner.*not valid') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.23 â€” cg-plan Step 4.5 confidence check
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Step 4.5 Confidence Check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 4.5 Confidence Check" {
        ($content -match 'Step 4\.5.*Confidence Check') | Should -Be $true
    }

    It "checks Completeness dimension" {
        ($content -match '\*\*Completeness\*\*') | Should -Be $true
    }

    It "checks Testability dimension" {
        ($content -match '\*\*Testability\*\*') | Should -Be $true
    }

    It "checks Dependencies dimension" {
        ($content -match '\*\*Dependencies\*\*') | Should -Be $true
    }

    It "checks Risk coverage dimension" {
        ($content -match '\*\*Risk coverage\*\*') | Should -Be $true
    }

    It "checks Scope clarity dimension" {
        ($content -match '\*\*Scope clarity\*\*') | Should -Be $true
    }

    It "defines High / Medium / Low confidence levels" {
        ($content -match '\*\*High\*\*' -and $content -match '\*\*Medium\*\*' -and $content -match '\*\*Low\*\*') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.24 â€” cg-plan Test Scenarios template (checkmark/warning/cross)
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Test Scenarios template" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Test Scenarios field in step template" {
        ($content -match '\*\*Test Scenarios\*\*:') | Should -Be $true
    }

    It "includes happy path marker" {
        ($content -match '[Hh]appy path') | Should -Be $true
    }

    It "includes edge case marker" {
        ($content -match '[Ee]dge case') | Should -Be $true
    }

    It "includes error path marker" {
        ($content -match '[Ee]rror path') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.25 â€” cg-review Step 1.5 staged preflight routing
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - Step 1.5 staged routing" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 1.5 Deterministic Preflight Risk-Class Routing" {
        ($content -match 'Step 1\.5.*Deterministic Preflight Risk-Class Routing') | Should -Be $true
    }

    It "includes pipeline/scripts trigger routing to data-risk" {
        ($content -match 'pipeline.*data-risk|scripts.*data-risk') | Should -Be $true
    }

    It "includes >= 50 non-test lines escalation trigger from light to standard" {
        ($content -match '50 non-test lines') | Should -Be $true
        ($content -match 'light\s*->\s*standard') | Should -Be $true
    }

    It "includes authentication/secrets trigger routing to full" {
        ($content -match 'Auth.*secrets.*credentials|secrets.*credentials.*security-risk') | Should -Be $true
        ($content -match 'security-risk.*full') | Should -Be $true
    }

    It "includes statistical functions trigger routing to data-risk" {
        ($content -match 'statistical functions|fmean') | Should -Be $true
        ($content -match 'data-risk') | Should -Be $true
    }

    It "includes >= 200 non-test lines suggestion trigger" {
        ($content -match '200 non-test lines') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.26 â€” cg-review @cg-adversarial in full route list
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - @cg-adversarial in full route" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes @cg-adversarial in Full section" {
        ($content -match '(?s)Full.*?@cg-adversarial') | Should -Be $true
    }

    It "@cg-adversarial is NOT in Light section" {
        $lightSection = if ($content -match '(?s)\*\*Light\*\*.*?\*\*Standard\*\*') { $Matches[0] } else { '' }
        ($lightSection -match '@cg-adversarial') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# P1.27 â€” cg-review protected artifacts guard
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - protected artifacts guard" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "mentions Protected artifacts section" {
        ($content -match 'Protected artifacts') | Should -Be $true
    }

    It "lists .cg-docs subdirectories as protected" {
        ($content -match '\.cg-docs') | Should -Be $true
    }

    It "lists compound-gpid.md as a protected file" {
        ($content -match 'compound-gpid\.md') | Should -Be $true
    }

    It "lists roadmap.json as a protected file" {
        ($content -match 'roadmap\.json') | Should -Be $true
    }

    It "guard instructs discarding delete/replace/rename/move findings" {
        ($content -match 'Discard any finding.*delet') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.28 â€” cg-review mode:autofix backward compatibility
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - mode:autofix backward compatibility" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents mode:autofix argument" {
        ($content -match 'mode:autofix') | Should -Be $true
    }

    It "defines safe_auto and advisory tags" {
        ($content -match '(?s)Step 4.*safe_auto.*advisory') | Should -Be $true
    }

    It "includes Autofix complete report template" {
        ($content -match 'Autofix complete:.*safe fixes') | Should -Be $true
    }

    It "prohibits safe_auto for statistical functions (escalate to manual)" {
        ($content -match '(?s)Never.*safe_auto.*statistical|statistical.*escalate.*manual') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.29 â€” cg-review P0 BLOCKING section in report template
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - P0 BLOCKING in report template" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes ### P0 BLOCKING section in report template" {
        ($content -match '### P0.*BLOCKING') | Should -Be $true
    }

    It "P0 BLOCKING appears before P1 CRITICAL in report" {
        ($content -match '(?s)P0.*BLOCKING.*P1.*CRITICAL') | Should -Be $true
    }

    It "P0 section includes immediate remediation language" {
        ($content -match '(?s)P0.*immediate') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.30 â€” cg-work inline plan fallback
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - inline plan fallback" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "describes lightweight inline plan fallback when no plan found" {
        ($content -match 'lightweight inline plan') | Should -Be $true
    }

    It "inline plan is described as 3-5 steps" {
        ($content -match '3.5 steps') | Should -Be $true
    }

    It "offers Proceed with this or run /cg-plan option" {
        ($content -match 'Proceed with this.*cg-plan') | Should -Be $true
    }

    It "skips roadmap linking Step 1.5 when using inline plan" {
        ($content -match 'Skip Step 1\.5') | Should -Be $true
    }

    It "saves inline plan to .cg-docs/plans/ before implementing" {
        ($content -match '\.cg-docs[/\\]plans.*YYYY-MM-DD') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.31 â€” cg-work Discover existing tests sub-step
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Discover existing tests sub-step" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Discover existing tests sub-step" {
        ($content -match 'Discover existing tests') | Should -Be $true
    }

    It "instructs searching for test files before implementing" {
        ($content -match '[Bb]efore implementing.*scan|[Ss]earch for test files') | Should -Be $true
    }

    It "references .Tests.ps1 test file pattern" {
        ($content -match '\.Tests\.ps1') | Should -Be $true
    }

    It "instructs running both existing and new tests" {
        # Original check: text "existing tests AND the new tests" was replaced with
        # a literal execution_subagent block (Phase 2 prompt hardening). The
        # new approach uses execution_subagent + Run-Tests.ps1 + last-run.json.
        # (?s) flag makes . match newlines so the pattern spans multiple lines.
        ($content -match '(?s)existing tests AND the new tests|(?s)execution_subagent.*Run-Tests|Run-Tests.*execution_subagent') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.32 â€” cg-work Step 3.2 self-review
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 3.2 Self-Review" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 3.2 Self-Review section" {
        ($content -match 'Step 3\.2.*Self-Review') | Should -Be $true
    }

    It "scans for print( debug code pattern" {
        ($content -match 'print\(') | Should -Be $true
    }

    It "checks for missing tests on new public functions" {
        ($content -match 'new public function') | Should -Be $true
    }

    It "scans for TODO FIXME HACK XXX markers" {
        ($content -match 'TODO.*FIXME.*HACK') | Should -Be $true
    }

    It "emits a self-review complete summary line" {
        ($content -match '[Ss]elf-review complete:') | Should -Be $true
    }
}

# P3.3â€“P3.12 are advisory-only findings; no regression tests required.

# ---------------------------------------------------------------------------
# P3.13 â€” cg-review routed mode arguments documented
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - routed mode arguments" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents light, standard, data-risk, architecture, and full as routed modes" {
        ($content -match '(?i)light.*standard.*data-risk.*architecture.*full') | Should -Be $true
    }

    It "documents thorough as a backward-compatible alias" {
        ($content -match '(?i)thorough.*backward-compatible|thorough.*alias') | Should -Be $true
    }

    It "references review depth from compound-gpid.local.md for default" {
        ($content -match 'compound-gpid\.local') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.33 â€” cg-fix-problems.prompt.md existence, frontmatter, no tool restriction
# ---------------------------------------------------------------------------

Describe "cg-fix-problems.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-problems.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-fix-problems.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-problems.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should -Match 'description:'
        }

        It "inherits the selected model without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }
}

Describe "cg-fix-problems.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-problems.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    Context "orchestrator must have unrestricted tools" {
        It "does not have a tools: key (write access required for orchestrating prompts)" {
            ($frontmatter -notmatch '(?m)^\s*tools:') | Should -Be $true
        }
    }
}

Describe "cg-fix-problems.prompt.md - dispatches agent and scans diagnostics" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-problems.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "dispatches @cg-fix-problems agent" {
        ($content -match '@cg-fix-problems') | Should -Be $true
    }

    It "references get_errors for diagnostics scanning" {
        ($content -match 'get_errors') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.34 â€” cg-fix-problems.agent.md existence, user-invocable false, auto mode protocol
# ---------------------------------------------------------------------------

Describe "cg-fix-problems.agent.md - user-invocable false" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-fix-problems.agent.md"
    $frontmatter = Get-Frontmatter -FilePath $agentFile

    It "exists in the repository" {
        Test-Path $agentFile | Should -Be $true
    }

    It "has user-invocable: false in frontmatter" {
        ($frontmatter -match 'user-invocable:\s*false') | Should -Be $true
    }

    It "has editFiles in its tools list (required to apply code fixes)" {
        ($frontmatter -match 'editFiles') | Should -Be $true
    }
}

Describe "cg-fix-problems.agent.md - auto mode protocol" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-fix-problems.agent.md"
    $content = Get-Content $agentFile -Raw -Encoding UTF8

    It "documents 2-round retry budget" {
        ($content -match '2[ \-]round|two[ \-]round|Round 2') | Should -Be $true
    }

    It "documents errors-only filter for auto mode" {
        ($content -match '(?i)errors only') | Should -Be $true
    }

    It "references get_errors diagnostics tool" {
        ($content -match 'get_errors') | Should -Be $true
    }

    It "documents hard stop after round 2" {
        ($content -match '[Hh]ard [Ss]top|Hard stop') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.35 â€” cg-work auto-dispatch @cg-fix-problems
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - auto-dispatch @cg-fix-problems" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references @cg-fix-problems agent" {
        ($content -match '@cg-fix-problems') | Should -Be $true
    }

    It "documents 2-round retry budget" {
        ($content -match '2[ \-]round|two[ \-]round|2 rounds') | Should -Be $true
    }

    It "documents errors-only scope for auto mode" {
        ($content -match '(?i)errors only') | Should -Be $true
    }

    It "explicitly suppresses auto-dispatch when no errors are present (warnings-only guard)" {
        ($content -match 'Suppress this step.*no errors|no errors are present|when.*get_errors.*returns no errors') | Should -Be $true
    }

    It "passes mode: auto to the agent dispatch (not interactive)" {
        ($content -match 'mode:\s*auto') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.36 â€” cg-work roadmap status update must happen before summary wait
# Bug: Step 5 (Update Roadmap Status) was placed after Step 4 (Summary).
# Step 4 ends with "Wait for the user's response before proceeding."
# In practice the user picks a next action (/cg-review etc.) and the
# cg-work session ends â€” Step 5 never executes, causing roadmap drift.
# Fix: move roadmap update to before the summary / user-wait.
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - roadmap done update before summary wait" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "'to status done.' dispatch phrase is present in the prompt" {
        $content.IndexOf("to status done.") | Should -BeGreaterThan -1
    }

    It "'Wait for the user's response before proceeding' phrase is present in the prompt" {
        $content.IndexOf("Wait for the user's response before proceeding") | Should -BeGreaterThan -1
    }

    It "dispatches roadmap 'to status done.' update BEFORE the 'Wait for the user' pause (prevents roadmap drift)" {
        $waitPos = $content.IndexOf("Wait for the user's response before proceeding")
        $donePos = $content.IndexOf("to status done.")
        # The roadmap update must precede the user-wait pause
        $donePos | Should -BeLessThan $waitPos
    }

    It "Step 3.7 appears between Step 3.5 and Step 4 in the file" {
        $step35Pos = $content.IndexOf("### Step 3.5:")
        $step37Pos = $content.IndexOf("### Step 3.7:")
        $step4Pos  = $content.IndexOf("### Step 4:")
        $step35Pos | Should -BeGreaterThan -1
        $step37Pos | Should -BeGreaterThan -1
        $step4Pos  | Should -BeGreaterThan -1
        $step37Pos | Should -BeGreaterThan $step35Pos
        $step37Pos | Should -BeLessThan $step4Pos
    }
}

# ---------------------------------------------------------------------------
# P1.38 â€” cg-brainstorm Step 3.5 Devil's Advocate
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 3.5 Devil's Advocate" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 3.5 Devil's Advocate section" {
        ($content -match "Step 3\.5.*Devil") | Should -Be $true
    }

    It "checks problem validation (is problem real)" {
        ($content -match 'Problem validation|problem real') | Should -Be $true
    }

    It "checks simplicity (simpler solution exists)" {
        ($content -match '[Ss]implicity check|simpler solution') | Should -Be $true
    }

    It "checks effort-value proportionality" {
        ($content -match '[Ee]ffort-value|80% of the benefit') | Should -Be $true
    }

    It "checks charter alignment" {
        ($content -match '[Cc]harter alignment') | Should -Be $true
    }

    It "includes side-idea capture instruction during pushback" {
        ($content -match 'adjacent idea|separate idea worth tracking') | Should -Be $true
    }

    It "Step 3.5 is always-on and unconditional for all scopes" {
        ($content -match 'always-on and unconditional') | Should -Be $true
    }

    It "Thinking Partner mode uses decision reversibility check" {
        ($content -match 'decision reversibility') | Should -Be $true
    }

    It "Thinking Partner mode uses stakeholder impact check" {
        ($content -match 'stakeholder impact') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.39 â€” cg-brainstorm Step 5c Side-Idea Capture
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 5c Side-Idea Capture" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 5c Side-Idea Capture section" {
        ($content -match '5c\..*Side-Idea Capture') | Should -Be $true
    }

    It "has 'no adjacent ideas' variant for sessions without pushback" {
        ($content -match 'No adjacent ideas surfaced') | Should -Be $true
    }

    It "has context-aware variant referencing the pushback discussion" {
        ($content -match 'pushback discussion') | Should -Be $true
    }

    It "renames previous 5c to 5d (Handoff moved to 5d)" {
        ($content -match '5d\. Handoff') | Should -Be $true
    }

    It "Step 5c dispatches @cg-roadmap for captured ideas" {
        ($content -match '@cg-roadmap') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.17 â€” cg-brainstorm step ordering: Step 3.5 before Step 4, Step 5c before 5d
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - step ordering: Step 3.5 and Step 5c" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 3.5 appears before Step 4 in the file" {
        $step35Idx = $content.IndexOf("### Step 3.5:")
        $step4Idx  = $content.IndexOf("### Step 4:")
        $step35Idx | Should -BeGreaterThan -1
        $step4Idx  | Should -BeGreaterThan -1
        $step35Idx | Should -BeLessThan $step4Idx
    }

    It "Step 5c Side-Idea Capture appears before Step 5d Handoff" {
        $step5cIdx = $content.IndexOf("5c. Side-Idea Capture")
        $step5dIdx = $content.IndexOf("5d. Handoff")
        $step5cIdx | Should -BeGreaterThan -1
        $step5dIdx | Should -BeGreaterThan -1
        $step5cIdx | Should -BeLessThan $step5dIdx
    }
}
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 1.7 Branch Offer ordering" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 1.7 Branch Offer appears after Step 1.5 Scope Assessment" {
        $step15Idx  = $content.IndexOf('### Step 1.5:')
        $step17Idx  = $content.IndexOf('### Step 1.7:')
        $step15Idx  | Should -BeGreaterThan -1
        $step17Idx  | Should -BeGreaterThan $step15Idx
    }

    It "Step 2 Clarifying Questions appears after Step 1.7 Branch Offer" {
        $step17Idx  = $content.IndexOf('### Step 1.7:')
        $step2Idx   = $content.IndexOf('### Step 2:')
        $step17Idx  | Should -BeGreaterThan -1
        $step2Idx   | Should -BeGreaterThan $step17Idx
    }
}

# ---------------------------------------------------------------------------
# P1.40 â€” cg-plan-critic.agent.md existence and structure
# ---------------------------------------------------------------------------

Describe "cg-plan-critic.agent.md - existence and structure" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-plan-critic.agent.md"

    It "exists in the repository" {
        Test-Path $agentFile | Should -Be $true
    }

    Context "required frontmatter fields" {
        $frontmatter = if (Test-Path $agentFile) { Get-Frontmatter -FilePath $agentFile } else { "" }

        It "has tools: restricted to read and search (not write)" {
            ($frontmatter -match "tools:.*'read'") -and ($frontmatter -match "tools:.*'search'") | Should -Be $true
        }

        It "is NOT user-invocable" {
            ($frontmatter -match 'user-invocable:\s*false') | Should -Be $true
        }

        It "inherits the selected model without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# P1.41 â€” cg-plan-review.prompt.md existence and structure
# ---------------------------------------------------------------------------

Describe "cg-plan-review.prompt.md - existence and structure" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan-review.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (orchestrating prompt needs unrestricted access)" {
            ($frontmatter -notmatch 'tools:') | Should -Be $true
        }
    }

    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "dispatches @cg-plan-critic" {
        ($content -match '@cg-plan-critic') | Should -Be $true
    }

    It "can locate a plan without user specifying a path (scans .cg-docs/plans/)" {
        ($content -match '\.cg-docs[/\\]plans') | Should -Be $true
    }

    It "includes side-idea capture in Step 4" {
        ($content -match 'Step 4.*Side-Idea Capture') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.42 â€” cg-plan.prompt.md Step 6 plan-review handoff and side-idea capture
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Step 6 plan-review handoff" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 6 suggests /cg-plan-review as an option" {
        ($content -match '/cg-plan-review') | Should -Be $true
    }

    It "Step 6a includes side-idea capture section" {
        ($content -match '6a\. Side-Idea Capture') | Should -Be $true
    }

    It "Step 6b contains the handoff options" {
        ($content -match '6b\. Handoff') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.43 â€” cg-resume.prompt.md schema bypass guard for compound-gpid workspace
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - schema bypass guard" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "contains workspace-root SCHEMA_VERSION self-check before schema comparison" {
        ($content -match 'SCHEMA_VERSION') -and ($content -match 'workspace root') | Should -Be $true
    }

    It "instructs to skip schema comparison when workspace root has SCHEMA_VERSION" {
        ($content -match '[Ss]kip this entire step|[Ss]kip.*proceed.*Step 2') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-work.prompt.md - test failure recovery (per-step test enforcement)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - test failure recovery" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "exists" {
        Test-Path $promptFile | Should -Be $true
    }

    It "documents 2 fix attempts hard cap" {
        ($content -match '\d+\.\s+If tests are still failing after 2 fix attempts') | Should -Be $true
    }

    It "notification is rendered as a blockquote" {
        ($content -match '>\s+"?\*\*N test\(s\)|>\s+\*\*N test\(s\)') | Should -Be $true
    }

    It "notification template includes 'Review before merging'" {
        ($content -match 'Review before merging') | Should -Be $true
    }

    It "notification template shows per-test enumeration format" {
        ($content -match '<test-file>::<test-name>') | Should -Be $true
    }

    It "explicitly separates test failures from @cg-fix-problems dispatch" {
        ($content -match '(?s)Do NOT dispatch.*@cg-fix-problems.*test fail') | Should -Be $true
    }

    It "includes anti-weakening guard ('not weaken')" {
        ($content -match 'not\s+weaken|weaken or remove') | Should -Be $true  # \s+ intentionally spans the CRLF line break between 'not' and 'weaken' in the prompt
    }

    It "permits test updates when function interface explicitly changed" {
        ($content -match 'changed signature or return type|Inference about interface change') | Should -Be $true
    }

    It "notification template uses variable count placeholder (N test(s))" {
        ($content -match 'N test\(s\)') | Should -Be $true
    }

    It "describes sequential two-attempt structure ('one more targeted fix attempt')" {
        ($content -match 'one more targeted fix') | Should -Be $true
    }

    It "requires full-suite re-run after targeted fixes resolve to catch regressions" {
        ($content -match '(?s)full test suite.*catch regressions|regressions introduced by the fix') | Should -Be $true
    }

    It "instructs continuing to Auto-Fix Diagnostics when full suite passes (continue path)" {
        ($content -match '(?s)full suite passes.*continue normally|continue.*Auto-Fix Diagnostics') | Should -Be $true
    }

    It "notification template includes last error message placeholder" {
        ($content -match '<last error message>') | Should -Be $true
    }

    It "on new regressions emits step-4 format notification and continues to Auto-Fix Diagnostics" {
        ($content -match 'emit the standard failure notification.*sub-step 4|format from sub-step 4') | Should -Be $true
    }

    It "includes double-notification skip-guard in Auto-Fix Diagnostics sub-item 5" {
        ($content -match '(?s)Test Failure Recovery step 4.*skip emitting') | Should -Be $true
    }

    It "scopes Test Failure Recovery to functional tests only" {
        ($content -match 'Test Failure Recovery.*functional tests only|get_errors.*handled separately') | Should -Be $true
    }

    It "full-suite re-run step appears before the user-wait pause" {
        $rrunIdx = $content.IndexOf('full test suite')
        $waitIdx = $content.IndexOf('Wait for the user')
        $rrunIdx | Should -BeGreaterThan -1
        $rrunIdx | Should -BeLessThan $waitIdx
    }
}

# ---------------------------------------------------------------------------
# P1.37 â€” cg-work Step 3.7 must have title-search fallback for unlinked features
# Bug: When a plan implements features whose roadmap entry still has plan: null,
# Step 3.7 skips them with only a soft warning and never updates their status.
# Fix: add a fallback that searches feature titles in the plan content and
# prompts the user to confirm which features were completed.
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 3.7 title-search fallback for plan:null features" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 3.7 searches feature titles in the plan content when no path match found" {
        ($content -match 'title.*plan content|feature.*title.*appear|scan.*plan.*title|title.*match.*plan') | Should -Be $true
    }

    It "Step 3.7 prompts the user to confirm which unlinked features were completed" {
        ($content -match 'confirm.*which features|which.*features.*complet|ask.*user.*confirm') | Should -Be $true
    }

    It "Step 3.7 still dispatches @cg-roadmap for confirmed matches from the fallback" {
        # The fallback must dispatch @cg-roadmap, not just warn
        $step37Start = $content.IndexOf("### Step 3.7:")
        $step4Start  = $content.IndexOf("### Step 4:")
        $step37Block = $content.Substring($step37Start, $step4Start - $step37Start)
        ($step37Block -match '@cg-roadmap') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.4 â€” cg-work.prompt.md - Step 1.5 Mark Work Started
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 1.5 Mark Work Started" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "dispatches @cg-roadmap to mark feature status active at work start" {
        ($content -match 'to status active') | Should -Be $true
    }

    It "Step 1.5 is conditioned on feature status being planned" {
        ($content -match 'status is.*planned') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.5 â€” cg-work.prompt.md - Step 3.5 Mark Plan Complete
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 3.5 Mark Plan Complete" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 3.5 writes completed-date with today's date" {
        ($content -match 'completed-date') | Should -Be $true
    }

    It "Step 3.5 changes status to completed in plan frontmatter" {
        $step35Start = $content.IndexOf("### Step 3.5:")
        $step37Start = $content.IndexOf("### Step 3.7:")
        $step35Start | Should -BeGreaterThan -1
        $step37Start | Should -BeGreaterThan $step35Start
        $step35Block = $content.Substring($step35Start, $step37Start - $step35Start)
        ($step35Block -match 'status.*completed|status: completed') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Context Layer â€” compound-gpid.context.md referenced in all 17 prompts
# ---------------------------------------------------------------------------

Describe "context layer - all 17 prompts reference compound-gpid.context.md" {
    $prompts = @(
        "cg-brainstorm",
        "cg-commit-push-pr",
        "cg-compound",
        "cg-compound-refresh",
        "cg-diagnose",
        "cg-fix-problems",
        "cg-fix-triage",
        "cg-fixbug",
        "cg-ideate",
        "cg-plan",
        "cg-plan-review",
        "cg-resume",
        "cg-review",
        "cg-review-repos",
        "cg-strategy",
        "cg-verify-pr",
        "cg-work"
    )

    foreach ($name in $prompts) {
        $promptFile = Join-Path $repoRoot ".github\prompts\$name.prompt.md"
        $content    = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

        It "$name.prompt.md references compound-gpid.context.md" {
            ($content -match 'compound-gpid\.context\.md') | Should -Be $true
        }

        It "$name.prompt.md instructs to skip silently when context.md is absent" {
            ($content -match 'skip silently|skip.*silently|proceed without project context') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Context Layer -- cg-issues is an intentional exception (reads roadmap.json directly)
# ---------------------------------------------------------------------------

Describe "context layer - cg-issues intentionally omits Get Bearings (reads roadmap.json directly)" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-issues.prompt.md") -Raw -Encoding UTF8

    It "cg-issues reads roadmap.json rather than charter files" {
        ($content -match 'roadmap\.json') | Should -Be $true
    }

    It "cg-issues does NOT reference compound-gpid.context.md (by design)" {
        ($content -match 'compound-gpid\.context\.md') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# Context Layer â€” renumbering survival: 'warn' item retains 'warn' text
# after context.md item was inserted before it
# ---------------------------------------------------------------------------

Describe "context layer - warn text survives renumbering in standard prompts" {
    $standardPrompts = @(
        "cg-compound",
        "cg-diagnose",
        "cg-fix-problems",
        "cg-fix-triage",
        "cg-fixbug",
        "cg-review",
        "cg-work"
    )

    foreach ($name in $standardPrompts) {
        $promptFile = Join-Path $repoRoot ".github\prompts\$name.prompt.md"
        $content    = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

        It "$name.prompt.md retains 'warn the user' instruction after context.md item inserted" {
            ($content -match 'warn the user') | Should -Be $true
        }

        It "$name.prompt.md retains 'No project charter found' message text" {
            ($content -match 'No project charter found') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Context Layer â€” cg-compound Step 5 context enrichment before Step 6 confirm
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - context enrichment step ordering" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 5 Context Enrichment section" {
        ($content -match 'Step 5.*Context Enrichment') | Should -Be $true
    }

    It "includes Step 6 Confirm section" {
        ($content -match 'Step 6.*Confirm') | Should -Be $true
    }

    It "Step 5 (Context Enrichment) comes before Step 6 (Confirm)" {
        $step5Pos = $content.IndexOf("### Step 5: Context Enrichment")
        $step6Pos = $content.IndexOf("### Step 6: Confirm")
        $step5Pos | Should -BeGreaterThan -1
        $step6Pos | Should -BeGreaterThan -1
        $step5Pos | Should -BeLessThan $step6Pos
    }

    It "proposes adding to compound-gpid.context.md when domain knowledge is discovered" {
        ($content -match 'compound-gpid\.context\.md') | Should -Be $true
    }

    It "offers to create context.md if it does not exist" {
        ($content -match 'does not exist.*suggest creating|Would you like me to create it') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Context Layer â€” cg-work Step 3.8 milestone completion check
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 3.8 milestone completion check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 3.8 Milestone Completion Check section" {
        ($content -match 'Step 3\.8.*Milestone Completion Check') | Should -Be $true
    }

    It "Step 3.8 appears between Step 3.7 and Step 4 in the file" {
        $step37Pos = $content.IndexOf("### Step 3.7:")
        $step38Pos = $content.IndexOf("### Step 3.8:")
        $step4Pos  = $content.IndexOf("### Step 4:")
        $step37Pos | Should -BeGreaterThan -1
        $step38Pos | Should -BeGreaterThan -1
        $step4Pos  | Should -BeGreaterThan -1
        $step38Pos | Should -BeGreaterThan $step37Pos
        $step38Pos | Should -BeLessThan $step4Pos
    }

    It "counts non-done features in the milestone after marking done" {
        ($content -match 'all features.*done|not.*done.*idea.*planned.*active') | Should -Be $true
    }

    It "dispatches @cg-roadmap when milestone is fully complete" {
        $step38Start = $content.IndexOf("### Step 3.8:")
        $step4Start  = $content.IndexOf("### Step 4:")
        $step38Block = $content.Substring($step38Start, $step4Start - $step38Start)
        ($step38Block -match '@cg-roadmap') | Should -Be $true
    }

    It "warns user that Current Focus may be stale when milestone completes" {
        ($content -match '[Ss]tale.*Current Focus|Current Focus.*stale') | Should -Be $true
    }

    It "suggests /cg-strategy to update direction after milestone completes" {
        ($content -match '/cg-strategy') | Should -Be $true
    }

    It "does NOT auto-modify compound-gpid.md charter (redirects to /cg-strategy)" {
        $step38Start = $content.IndexOf("### Step 3.8:")
        $step4Start  = $content.IndexOf("### Step 4:")
        $step38Block = $content.Substring($step38Start, $step4Start - $step38Start)
        # Charter direction is deferred to /cg-strategy, not handled inline in cg-work
        ($step38Block -match '/cg-strategy') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Context Layer â€” cg-resume Step 2f.5 Current Focus staleness check
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - Step 2f.5 Current Focus staleness" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 2f.5 Current Focus staleness check" {
        ($content -match '2f\.5.*[Cc]urrent [Ff]ocus') | Should -Be $true
    }

    It "checks if Current Focus references a completed milestone" {
        ($content -match 'status.*done|done.*status') | Should -Be $true
    }

    It "surfaces a nudge when Current Focus references a completed milestone" {
        ($content -match 'Stale Current Focus') | Should -Be $true
    }

    It "does NOT auto-modify the charter (read-only nudge only)" {
        $step2f5Start = $content.IndexOf("#### 2f.5.")
        $step3Start   = $content.IndexOf("### Step 3:")
        if ($step2f5Start -ge 0 -and $step3Start -ge 0) {
            $block = $content.Substring($step2f5Start, $step3Start - $step2f5Start)
            ($block -match 'Set-Content|Write-Content|update.*compound-gpid\.md') | Should -Be $false
        } else {
            $true | Should -Be $true  # guard: skip if section not found
        }
    }

    It "suggests /cg-strategy to update direction" {
        ($content -match '/cg-strategy') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Context Layer â€” .gitignore must NOT contain compound-gpid.context.md
# (it is institutional knowledge and must be committed)
# ---------------------------------------------------------------------------

Describe "context layer - compound-gpid.context.md is NOT gitignored" {
    # The link.ps1 and unlink.ps1 scripts manage a CG block in .gitignore.
    # compound-gpid.context.md must never appear in that block (or anywhere
    # in the produced .gitignore content).
    $gitignoreFile = Join-Path $repoRoot ".gitignore"
    $content = if (Test-Path $gitignoreFile) {
        Get-Content $gitignoreFile -Raw -Encoding UTF8
    } else { "" }

    It "compound-gpid.context.md is not listed in the project .gitignore" {
        # Only check non-comment lines â€” a comment documenting that the file is intentionally
        # NOT gitignored is permitted; an uncommented entry would actually ignore the file.
        $nonCommentLines = ($content -split '\r?\n' | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
        ($nonCommentLines -match 'compound-gpid\.context\.md') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# cg-compound.prompt.md - context enrichment step (Step 5)
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - context enrichment step" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references compound-gpid.context.md in Step 5" {
        ($content -match 'compound-gpid\.context\.md') | Should -Be $true
    }

    It "auto-writes to compound-gpid.context.md when a finding is relevant (no prompt)" {
        # Step 5 now writes directly and reports the addition (no 'Should I add it?' ask)
        ($content -match 'insert the finding directly|Context enriched:') | Should -Be $true
    }

    It "includes an offer to create compound-gpid.context.md when it does not exist" {
        ($content -match 'does not exist.*create it|create it.*does not exist|Would you like me to create it') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-resume.prompt.md - Current Focus staleness check (Step 2f.5)
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - Current Focus staleness check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 2f.5 Current Focus staleness check" {
        ($content -match '2f\.5') | Should -Be $true
    }

    It "cross-references milestone status done in staleness logic" {
        ($content -match "status.*done|status.*`"done`"") | Should -Be $true
    }

    It "emits a Stale Current Focus nudge when a completed milestone is referenced" {
        ($content -match 'Stale Current Focus') | Should -Be $true
    }

    It "does not auto-modify the charter (nudge only)" {
        ($content -match 'Do NOT auto-modify|only surface the nudge') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-work.prompt.md - milestone completion check (Step 3.8)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - milestone completion check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 3.8 milestone completion check" {
        ($content -match '3\.8') | Should -Be $true
    }

    It "dispatches @cg-roadmap when all features in a milestone are done" {
        ($content -match '@cg-roadmap.*milestone|milestone.*@cg-roadmap') | Should -Be $true
    }

    It "warns the user when a milestone is fully complete" {
        ($content -match 'Milestone.*is now complete|is now complete') | Should -Be $true
    }

    It "offers to update Current Focus when a milestone completes" {
        ($content -match 'Current Focus') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Pester crash prevention - literal execution_subagent blocks in test-running prompts
#
# These tests verify that cg-work, cg-fix-triage, and cg-diagnose each contain
# a literal execution_subagent block for running tests, an Invoke-Pester
# prohibition, and a last-run.json artifact reference. If someone removes these
# blocks, a Pester crash becomes likely again.
#
# Tests use co-presence checks rather than exact phrasing to avoid brittleness.
# ---------------------------------------------------------------------------

Describe "Pester crash prevention - execution_subagent blocks in cg-work" {
    $cgWorkFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $cgWorkContent = if (Test-Path $cgWorkFile) { Get-Content $cgWorkFile -Raw -Encoding UTF8 } else { "" }

    It "cg-work.prompt.md exists" {
        (Test-Path $cgWorkFile) | Should -Be $true
    }

    It "cg-work.prompt.md contains execution_subagent instruction" {
        ($cgWorkContent -match 'execution_subagent') | Should -Be $true
    }

    It "cg-work.prompt.md references Run-Tests.ps1 in test block" {
        ($cgWorkContent -match 'Run-Tests\.ps1') | Should -Be $true
    }

    It "cg-work.prompt.md references last-run.json artifact" {
        ($cgWorkContent -match 'last-run\.json') | Should -Be $true
    }

    It "cg-work.prompt.md contains Invoke-Pester prohibition alongside execution_subagent" {
        # Co-presence check: both must exist (prohibition intent confirmed).
        # Does not test exact phrasing - rewording the prohibition still passes.
        ($cgWorkContent -match 'execution_subagent') -and ($cgWorkContent -match 'Invoke-Pester') |
            Should -Be $true
    }

    It "cg-work.prompt.md does not include a direct Invoke-Pester file inspection recipe" {
        ($cgWorkContent -match 'Invoke-Pester\s+<file>') | Should -Be $false
        ($cgWorkContent -match '\$r\s*=\s*Invoke-Pester') | Should -Be $false
    }

    It "warns filteredFiles non-null means partial run (commit gate guard)" {
        ($cgWorkContent -match 'filteredFiles') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P3.10 â€” cg-work full-suite commit gate guard (dedicated describe)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - full-suite commit gate guard" {
    $cgWorkFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $cgWorkContent = if (Test-Path $cgWorkFile) { Get-Content $cgWorkFile -Raw -Encoding UTF8 } else { "" }

    It "full-suite gate query includes filteredFiles field" {
        ($cgWorkContent -match 'filteredFiles') | Should -Be $true
    }

    It "partial run guard: non-null filteredFiles blocks commit gate" {
        ($cgWorkContent -match 'filteredFiles.*partial run|partial run.*filteredFiles') | Should -Be $true
    }
}

Describe "Pester crash prevention - execution_subagent blocks in cg-fix-triage" {
    $cgFixTriageFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    $cgFixTriageContent = if (Test-Path $cgFixTriageFile) { Get-Content $cgFixTriageFile -Raw -Encoding UTF8 } else { "" }

    It "cg-fix-triage.prompt.md exists" {
        (Test-Path $cgFixTriageFile) | Should -Be $true
    }

    It "cg-fix-triage.prompt.md contains execution_subagent instruction" {
        ($cgFixTriageContent -match 'execution_subagent') | Should -Be $true
    }

    It "cg-fix-triage.prompt.md references Run-Tests.ps1 in test block" {
        ($cgFixTriageContent -match 'Run-Tests\.ps1') | Should -Be $true
    }

    It "cg-fix-triage.prompt.md references last-run.json artifact" {
        ($cgFixTriageContent -match 'last-run\.json') | Should -Be $true
    }

    It "cg-fix-triage.prompt.md contains Invoke-Pester prohibition alongside execution_subagent" {
        ($cgFixTriageContent -match 'execution_subagent') -and ($cgFixTriageContent -match 'Invoke-Pester') |
            Should -Be $true
    }

    It "full-suite gate includes filteredFiles field" {
        ($cgFixTriageContent -match 'filteredFiles') | Should -Be $true
    }

    It "full-suite gate includes Test-Path guard for missing last-run.json" {
        ($cgFixTriageContent -match 'Test-Path tests\\last-run\.json') | Should -Be $true
    }

    It "full-suite gate emits 'last-run.json not found' message when file is missing" {
        ($cgFixTriageContent -match 'last-run\.json not found') | Should -Be $true
    }
}

Describe "Pester crash prevention - execution_subagent blocks in cg-diagnose" {
    $cgDiagnoseFile = Join-Path $repoRoot ".github\prompts\cg-diagnose.prompt.md"
    $cgDiagnoseContent = if (Test-Path $cgDiagnoseFile) { Get-Content $cgDiagnoseFile -Raw -Encoding UTF8 } else { "" }

    It "cg-diagnose.prompt.md exists" {
        (Test-Path $cgDiagnoseFile) | Should -Be $true
    }

    It "cg-diagnose.prompt.md contains execution_subagent instruction" {
        ($cgDiagnoseContent -match 'execution_subagent') | Should -Be $true
    }

    It "cg-diagnose.prompt.md references Run-Tests.ps1 in test block" {
        ($cgDiagnoseContent -match 'Run-Tests\.ps1') | Should -Be $true
    }

    It "cg-diagnose.prompt.md references last-run.json artifact" {
        ($cgDiagnoseContent -match 'last-run\.json') | Should -Be $true
    }

    It "cg-diagnose.prompt.md contains Invoke-Pester prohibition alongside execution_subagent" {
        ($cgDiagnoseContent -match 'execution_subagent') -and ($cgDiagnoseContent -match 'Invoke-Pester') |
            Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.5 â€” cg-skill-pester-safety SKILL.md Agent Workflow regression tests
# If the Agent Workflow section is removed, no agent will know to use
# execution_subagent, and the canonical Run-Tests.ps1 pattern is lost.
# ---------------------------------------------------------------------------

Describe "cg-skill-pester-safety - Agent Workflow section present" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-pester-safety\SKILL.md"
    $skillContent = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }

    It "SKILL.md contains 'execution_subagent' in Agent Workflow section" {
        ($skillContent -match 'execution_subagent') | Should -Be $true
    }

    It "SKILL.md references Run-Tests.ps1 in Agent Workflow section" {
        ($skillContent -match 'Run-Tests\.ps1') | Should -Be $true
    }

    It "SKILL.md references last-run.json artifact in Agent Workflow section" {
        ($skillContent -match 'last-run\.json') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.5 â€” copilot-instructions.md Rule 9 regression tests
# Rule 9 is the system-level mandate that makes the execution_subagent
# pattern binding on all agents. If removed, no agent-level test fails.
# ---------------------------------------------------------------------------

Describe "copilot-instructions.md - Rule 9 Agent test workflow" {
    $instructionsFile = Join-Path $repoRoot ".github\copilot-instructions.md"
    $instructionsContent = if (Test-Path $instructionsFile) { Get-Content $instructionsFile -Raw -Encoding UTF8 } else { "" }

    It "copilot-instructions.md contains 'Agent test workflow' rule" {
        ($instructionsContent -match 'Agent test workflow') | Should -Be $true
    }

    It "copilot-instructions.md references execution_subagent in Rule 9" {
        ($instructionsContent -match 'execution_subagent') | Should -Be $true
    }

    It "copilot-instructions.md references last-run.json in Rule 9" {
        ($instructionsContent -match 'last-run\.json') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.19 â€” cg-setup.prompt.md structural tests (zero coverage previously)
# ---------------------------------------------------------------------------

Describe "cg-setup.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-setup.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    It "has a description in frontmatter" {
        $frontmatter | Should -Match 'description:'
    }

    It "inherits the selected model without model frontmatter" {
        ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
    }

    It "does not have a tools: key (orchestrating prompt needs unrestricted access)" {
        ($frontmatter -notmatch 'tools:') | Should -Be $true
    }
}

Describe "cg-setup.prompt.md - mode detection and overwrite guard" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references compound-gpid.local.md for mode detection (Mode A vs Mode B)" {
        ($content -match 'compound-gpid\.local\.md') | Should -Be $true
    }

    It "has a project-name overwrite guard before recreating compound-gpid.md" {
        ($content -match 'already exists|overwrite') | Should -Be $true
    }

    It "references setup-templates.md for templates" {
        ($content -match 'setup-templates\.md') | Should -Be $true
    }

    It "creates roadmap.json during new project setup" {
        ($content -match 'roadmap\.json') | Should -Be $true
    }

    It "updates .gitignore to exclude compound-gpid.local.md" {
        ($content -match '\.gitignore') | Should -Be $true
    }

    It "does NOT create compound-gpid.md if user skips Question 4 (project name)" {
        ($content -match 'do NOT create|skips.*Q4|skips before Question 4') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.26 â€” cg-setup.prompt.md Mode B returning project coverage
# ---------------------------------------------------------------------------

Describe "cg-setup.prompt.md - Mode B returning project" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Mode B section for returning projects" {
        ($content -match 'Mode B') | Should -Be $true
    }

    It "checks for deprecated charter sections (B1.1.5)" {
        ($content -match 'Architecture Notes|deprecated') | Should -Be $true
    }

    It "performs schema version check (B1.3)" {
        ($content -match 'cg-schema-version') | Should -Be $true
    }

    It "checks for roadmap.json and notifies if missing (B1.2.5)" {
        ($content -match 'roadmap\.json') | Should -Be $true
    }

    It "checks for compound-gpid.context.md and offers to create it (B1.1.3)" {
        ($content -match 'compound-gpid\.context\.md') | Should -Be $true
    }

    It "explicitly instructs not to add context.md to .gitignore" {
        ($content -match '(?i)do NOT add.*\.gitignore|institutional knowledge') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# setup-templates.md - Charter Quality Gate section (Phase 2)
# ---------------------------------------------------------------------------

Describe "setup-templates.md - charter quality gate section" {
    $templateFile = Join-Path $repoRoot ".github\prompts\setup-templates.md"
    $content = Get-Content $templateFile -Raw -Encoding UTF8

    It "contains the Charter Quality Gate section heading" {
        ($content -match '## Charter Quality Gate') | Should -Be $true
    }

    It "lists project-name as a blocker" {
        ($content -match 'project-name') | Should -Be $true
    }

    It "lists <!-- TODO placeholder as a blocker" {
        ($content -match '<!-- TODO') | Should -Be $true
    }

    It "lists empty Objective as a blocker" {
        ($content -match '## Objective') | Should -Be $true
    }

    It "lists last-reviewed as a warning" {
        ($content -match 'last-reviewed') | Should -Be $true
    }

    It "includes deferred-output instruction for Mode B" {
        ($content -match 'Store results internally|Do NOT output') | Should -Be $true
    }

    It "Charter Quality Gate specifies exact TODO blocker strings" {
        ($content -match '<!-- TODO: Describe') | Should -Be $true
        ($content -match '<!-- TODO: List') | Should -Be $true
        ($content -match '<!-- TODO: Add') | Should -Be $true
        ($content -match '<!-- TODO: What') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# setup-templates.md - Charter from Scanner Results section (Phase 2)
# ---------------------------------------------------------------------------

Describe "setup-templates.md - scanner charter template section" {
    $templateFile = Join-Path $repoRoot ".github\prompts\setup-templates.md"
    $content = Get-Content $templateFile -Raw -Encoding UTF8

    It "contains the Charter from Scanner Results section heading" {
        ($content -match '## Charter from Scanner Results') | Should -Be $true
    }

    It "references @cg-project-scanner or scanner" {
        ($content -match '@cg-project-scanner|cg-project-scanner') | Should -Be $true
    }

    It "contains hybrid approve option: Approve as-is" {
        ($content -match 'Approve as-is') | Should -Be $true
    }

    It "contains hybrid approve option: Walk through section by section" {
        ($content -match 'Walk through') | Should -Be $true
    }

    It "contains hybrid approve option: Start from scratch" {
        ($content -match 'Start from scratch') | Should -Be $true
    }

    It "contains confidence-action mapping table with high/skip" {
        ($content -match '\| high') | Should -Be $true
        ($content -match '\| skip') | Should -Be $true
    }

    It "contains confidence-action mapping table with confirm and ask" {
        ($content -match '\| confirm') | Should -Be $true
        ($content -match '\| ask') | Should -Be $true
    }

    It "field mapping table notes Current Focus as not scannable" {
        ($content -match 'Current Focus.*not scannable|not scannable.*Current Focus') | Should -Be $true
    }

    It "setup-templates.md includes YAML quoting rule for project-name" {
        ($content -match 'single-quoted YAML|single quotes instead') | Should -Be $true
    }

    It "setup-templates.md includes JSON string escaping rule" {
        ($content -match 'JSON string escaping') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# setup-templates.md - Pre-flight Health Check section (Phase 2)
# ---------------------------------------------------------------------------

Describe "setup-templates.md - pre-flight health check section" {
    $templateFile = Join-Path $repoRoot ".github\prompts\setup-templates.md"
    $content = Get-Content $templateFile -Raw -Encoding UTF8

    It "contains the Pre-flight Health Check section heading" {
        ($content -match '## Pre-flight Health Check') | Should -Be $true
    }

    It "checks .github/prompts/ directory" {
        ($content -match '\.github/prompts/') | Should -Be $true
    }

    It "checks .github/skills/ directory" {
        ($content -match '\.github/skills/') | Should -Be $true
    }

    It "checks .github/agents/ directory" {
        ($content -match '\.github/agents/') | Should -Be $true
    }

    It "checks .github/instructions/ directory" {
        ($content -match '\.github/instructions/') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# setup-templates.md - Roadmap Bootstrap from Charter section (Phase 2)
# ---------------------------------------------------------------------------

Describe "setup-templates.md - roadmap bootstrap section" {
    $templateFile = Join-Path $repoRoot ".github\prompts\setup-templates.md"
    $content = Get-Content $templateFile -Raw -Encoding UTF8

    It "contains the Roadmap Bootstrap from Charter section heading" {
        ($content -match '## Roadmap Bootstrap from Charter') | Should -Be $true
    }

    It "mentions roadmap.json" {
        ($content -match 'roadmap\.json') | Should -Be $true
    }

    It "mentions Current Focus as the seed source" {
        ($content -match 'Current Focus') | Should -Be $true
    }

    It "specifies the empty skeleton fallback when charter was not written" {
        ($content -match 'charter was NOT written|charter was skipped') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-setup.prompt.md - Mode A scanner integration (Phase 2)
# ---------------------------------------------------------------------------

Describe "cg-setup.prompt.md - Mode A scanner integration" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "dispatches @cg-project-scanner in Mode A" {
        ($content -match '@cg-project-scanner') | Should -Be $true
    }

    It "contains named Fallback: Manual Questions block" {
        ($content -match 'Fallback: Manual Questions') | Should -Be $true
    }

    It "references Charter Quality Gate template" {
        ($content -match 'Charter Quality Gate') | Should -Be $true
    }

    It "references Pre-flight Health Check template" {
        ($content -match 'Pre-flight Health Check') | Should -Be $true
    }

    It "references Roadmap Bootstrap from Charter template" {
        ($content -match 'Roadmap Bootstrap from Charter') | Should -Be $true
    }

    It "contains scanner failure fallback text" {
        ($content -match 'Scanner could not analyze') | Should -Be $true
    }

    It "contains hybrid approve as-is option text" {
        ($content -match 'Approve as-is') | Should -Be $true
    }

    It "contains overwrite guard for existing charter" {
        ($content -match 'already exists.*overwrite|overwrite.*already exists') | Should -Be $true
    }

    It "mentions .Rbuildignore update step" {
        ($content -match '\.Rbuildignore') | Should -Be $true
    }

    It "contains scanner output sanitization instruction" {
        ($content -match 'untrusted user data|SYSTEM:.*prefix|Sanitization') | Should -Be $true
    }

    It "names specific injection trigger words (Ignore, Override, Forget)" {
        ($content -match '(?i)\bIgnore\b') | Should -Be $true
        ($content -match '(?i)\bOverride\b') | Should -Be $true
        ($content -match '(?i)\bForget\b') | Should -Be $true
    }

    It "has roadmap.json existence guard (skip if already exists)" {
        ($content -match 'roadmap\.json.*already exists.*skip|already exists.*roadmap') | Should -Be $true
    }

    It "falls back to ask when Setup Recommendations table is absent" {
        ($content -match 'absent from the scanner report|Setup Recommendations.*absent') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-setup.prompt.md - Mode B quality gate (Phase 2)
# ---------------------------------------------------------------------------

Describe "cg-setup.prompt.md - Mode B quality gate" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Mode B contains B1.1.1 charter quality check step" {
        ($content -match 'B1\.1\.1') | Should -Be $true
    }

    It "Mode B contains deferred-output instruction" {
        ($content -match 'Store results internally|Do NOT output') | Should -Be $true
    }

    It "Mode B references the Charter Quality Gate template" {
        ($content -match 'Charter Quality Gate') | Should -Be $true
    }

    It "Mode B preserves B1 read config step" {
        ($content -match 'B1\. Read existing config') | Should -Be $true
    }

    It "Mode B preserves B3 context summary step" {
        ($content -match 'B3\. Present context summary') | Should -Be $true
    }

    It "Mode B B3 step includes instruction to append quality gate findings" {
        ($content -match 'B3.*quality gate|quality gate.*B3|append.*quality gate|quality gate.*B1\.1\.1') | Should -Be $true
    }

    It "Mode B preserves B4.7 workspace folders step" {
        ($content -match 'B4\.7') | Should -Be $true
    }

    It "Mode B has B0.5 pre-load templates step" {
        ($content -match 'B0\.5') | Should -Be $true
    }

    It "Mode B B4 instructs carrying forward cg-schema-version on rewrite" {
        ($content -match 'carry forward.*cg-schema-version|cg-schema-version.*unchanged') | Should -Be $true
    }

    It "Mode B B3 instructs skipping B4.5 when blockers were fixed in B3" {
        ($content -match 'skip.*B4\.5|charter was just updated') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# link.ps1 - success message guidance
# ---------------------------------------------------------------------------

Describe "link.ps1 - success message guidance" {
    $linkScript = Join-Path $repoRoot "scripts\link.ps1"
    $content = Get-Content $linkScript -Raw -Encoding UTF8

    It "describes default multi-platform asset availability" {
        ($content -match 'Compound GPID assets are now available for') | Should -Be $true
    }

    It "warns not to edit managed linked directories and copied files directly" {
        ($content -match 'Managed linked directories and copied files should not be edited directly') | Should -Be $true
    }

    It "tells users how to limit platforms on future links" {
        ($content -match '--platforms copilot') | Should -Be $true
        ($content -match '--platforms opencode') | Should -Be $true
    }

    It "instructs users to restart their AI coding tool" {
        ($content -match 'Restart your AI coding tool') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-review-repos.prompt.md - file existence, frontmatter, guardrail, and content
# (Developer-only prompt for competitive repo analysis)
# ---------------------------------------------------------------------------

Describe "cg-review-repos.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-review-repos.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
    $frontmatter = if (Test-Path $promptFile) { Get-Frontmatter -FilePath $promptFile } else { "" }

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should -Match 'description:'
        }

        It "inherits the Copilot model picker without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }
}

Describe "cg-review-repos.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = if (Test-Path $promptFile) { Get-Frontmatter -FilePath $promptFile } else { "" }

        It "does not have a tools: key" {
            ($frontmatter -notmatch '(?m)^\s*tools:') | Should -Be $true
        }
    }
}

Describe "cg-review-repos.prompt.md - dev-repo guardrail" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "checks compound-gpid.md for project-name" {
        ($content -match 'project-name') | Should -Be $true
    }

    It "contains consumer-project warning message" {
        ($content -match 'compound-gpid development only') | Should -Be $true
    }

    # P1.1: guardrail must check the exact case-sensitive value, not just key presence
    It "guardrail checks exact case-sensitive value 'Compound GPID'" {
        ($content -match '"Compound GPID"') | Should -Be $true
    }
}

Describe "cg-review-repos.prompt.md - content structure" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "references --full flag for initial assessment mode" {
        ($content -match '--full') | Should -Be $true
    }

    # P3.5: case-insensitive --full flag matching must be documented
    It "specifies case-insensitive --full flag matching" {
        ($content -match 'case-insensitive') | Should -Be $true
    }

    It "references repos.json registry file" {
        ($content -match 'repos\.json') | Should -Be $true
    }

    It "feature card template includes Compatibility field" {
        ($content -match 'Compatibility:') | Should -Be $true
    }

    It "feature card template includes How we'd adapt it field" {
        ($content -match "How we'd adapt it") | Should -Be $true
    }

    It "mentions concept mapping table" {
        ($content -match 'Concept Mapping') | Should -Be $true
    }

    It "references assessment file path format" {
        ($content -match 'competitive-reviews/.*-full-review\.md|competitive-reviews\\.*-full-review\.md') | Should -Be $true
    }

    It "references delta report file path format" {
        ($content -match 'delta-review\.md') | Should -Be $true
    }

    It "warns about null-baseline repos for delta mode" {
        ($content -match 'lastReviewedRelease') | Should -Be $true
    }

    It "instructs to run --full to recover null-baseline repos" {
        ($content -match '--full.*first|Run.*--full') | Should -Be $true
    }

    It "stops when registry file is missing" {
        ($content -match 'Stop if the registry is missing') | Should -Be $true
    }

    # P1.2: injection guard for fetch_webpage content
    It "contains injection guard for fetch_webpage content" {
        ($content -match 'untrusted data') | Should -Be $true
    }

    # P1.3: URL validation â€” only https://github.com/ permitted
    It "requires https://github.com/ URLs only" {
        ($content -match 'https://github\.com/') | Should -Be $true
    }

    # P1.4: repo ID validation â€” alphanumeric + hyphens only
    It "validates repo IDs are alphanumeric with hyphens only" {
        ($content -match 'alphanumeric.*hyphens|hyphens only') | Should -Be $true
    }

    # P1.5: feature card limit per repo in full mode
    It "limits feature cards to 25 per repo in full mode" {
        ($content -match '25 most significant') | Should -Be $true
    }

    # P1.6a: registry write strategy â€” per-repo immediately
    It "instructs updating registry per-repo immediately (not at end)" {
        ($content -match 'per-repo immediately') | Should -Be $true
    }

    # P1.6b: registry write strategy â€” replace entire file
    It "instructs replacing the entire repos.json file on each write" {
        ($content -match 'entire file') | Should -Be $true
    }

    # P2.4: lastFullReviewNote behavior on partial failure
    It "specifies lastFullReviewNote behavior on partial failure" {
        ($content -match 'lastFullReviewNote') | Should -Be $true
    }

    # P3.2: lastFullReviewNote must be removed on successful full review
    It "specifies lastFullReviewNote is removed on successful full review" {
        ($content -match 'remove.*lastFullReviewNote|lastFullReviewNote.*removed') | Should -Be $true
    }

    # P2.12: branch-specific tests for new validation paths
    It "validates releasesUrl ends with /releases" {
        ($content -match 'ends with.*releases|/releases') | Should -Be $true
    }

    It "validates date formats as YYYY-MM-DD" {
        ($content -match 'YYYY-MM-DD') | Should -Be $true
    }

    It "validates shortName uniqueness" {
        ($content -match 'shortName.*unique|unique.*shortName|Duplicate shortName') | Should -Be $true
    }

    It "specifies collision policy for same-day re-runs" {
        ($content -match 'same-day re-run|-2.*-3|-3.*-2') | Should -Be $true
    }

    It "validates root-level lastFullReview date separately from per-repo dates" {
        ($content -match 'root-level|registry root') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# competitive-reviews/repos.json - registry file validation
# ---------------------------------------------------------------------------

Describe "competitive-reviews/repos.json - registry" {
    $registryFile = Join-Path $repoRoot ".cg-docs\competitive-reviews\repos.json"

    It "exists in the repository" {
        Test-Path $registryFile | Should -Be $true
    }

    It "is valid JSON" {
        { Get-Content $registryFile -Raw -Encoding UTF8 | ConvertFrom-Json } | Should -Not -Throw
    }

    $json = if (Test-Path $registryFile) {
        try { Get-Content $registryFile -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $null }
    } else { $null }

    It "has schemaVersion field" {
        $json.schemaVersion | Should -Not -BeNullOrEmpty
    }

    # P2.3: value must match the constant expected by the prompt (case-sensitive)
    It "schemaVersion equals expected constant" {
        $json.schemaVersion.Trim() | Should -BeExactly 'compound-gpid-competitive-reviews-v1'
    }

    # P2.5: schemaVersion must not have leading/trailing whitespace (invisible in failure messages)
    It "schemaVersion has no leading or trailing whitespace" {
        $json.schemaVersion | Should -Be $json.schemaVersion.Trim()
    }

    # P2.2: count sentinel â€” update when adding a new repo to repos.json
    It "has repos array with exactly 3 entries" {
        $json.repos.Count | Should -Be 3
    }

    foreach ($repoEntry in @(if ($null -ne $json) { $json.repos } else { @() })) {
        It "repo '$($repoEntry.id)' has required fields" {
            $repoEntry.id | Should -Not -BeNullOrEmpty
            $repoEntry.url | Should -Not -BeNullOrEmpty
            $repoEntry.releasesUrl | Should -Not -BeNullOrEmpty
            $repoEntry.shortName | Should -Not -BeNullOrEmpty
        }
    }
}

# ---------------------------------------------------------------------------
# Review convergence â€” cg-review mode:verify argument
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - mode:verify argument" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents mode:verify argument" {
        ($content -match 'mode:verify') | Should -Be $true
    }

    It "includes Step 1.7 for verification context" {
        ($content -match 'Step 1\.7') | Should -Be $true
    }

    It "suppression policy never suppresses P0/P1" {
        ($content -match '(?s)P0/P1.*[Nn]ever suppress') | Should -Be $true
    }

    It "suppression policy suppresses P2/P3 on fixed-finding scope" {
        ($content -match '(?s)P2/P3.*fixed-finding scope|P2/P3.*fix-consequence') | Should -Be $true
    }

    It "suppression policy always reports cross-file breakage" {
        ($content -match '(?s)[Cc]ross-file breakage.*[Aa]lways report') | Should -Be $true
    }

    It "forces light depth in verify mode" {
        ($content -match '(?si)Force depth to.*light|light.*forced') | Should -Be $true
    }

    It "verify review filename pattern documented" {
        ($content -match 'verify-review\.md') | Should -Be $true
    }

    It "instructs to skip Step 1.5 overrides in verify mode" {
        ($content -match '(?si)Step 1\.5.*[Ss]kip.*mode:verify|[Ss]kip this step if.*mode:verify') | Should -Be $true
    }

    It "documents parent-review frontmatter for verify reviews" {
        ($content -match 'parent-review') | Should -Be $true
    }

    It "documents type: verification frontmatter field" {
        ($content -match 'type: verification') | Should -Be $true
    }

    It "unrecognized-argument warning lists mode:verify" {
        ($content -match 'Recognized:.*mode:verify') | Should -Be $true
    }

    It "documents mutual exclusion of mode:autofix and mode:verify" {
        ($content -match '(?s)mode:autofix.*mode:verify.*mutually exclusive|Cannot combine.*mode:autofix.*mode:verify') | Should -Be $true
    }

    It "mutual exclusion resolves in favour of mode:verify" {
        ($content -match 'using.*mode:verify|ignore.*mode:autofix') | Should -Be $true
    }

    It "warns when no prior review with fixed findings found" {
        ($content -match '[Nn]o prior review with fixed findings found') | Should -Be $true
    }

    It "verify mode dispatches only cg-code-quality and cg-testing" {
        ($content -match '(?s)[Vv]erify mode.*cg-code-quality.*cg-testing|cg-code-quality.*cg-testing.*light.*forced') | Should -Be $true
    }

    It "excludes -verify-review.md files from prior review scan" {
        ($content -match '-review\.md.*NOT.*-verify-review\.md|verify-review\.md.*[Ss]kip|[Ss]kip.*verify-review\.md') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 3 — staged /cg-review routing and /cg-work review-mode integration
# ---------------------------------------------------------------------------

Describe "Phase 3 review routing contract" {
    $contractFile = Join-Path $repoRoot ".github\shared\review-routing.contract.md"
    $reviewFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $workFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $contract = if (Test-Path $contractFile) { Get-Content $contractFile -Raw -Encoding UTF8 } else { "" }
    $reviewContent = Get-Content $reviewFile -Raw -Encoding UTF8
    $workContent = Get-Content $workFile -Raw -Encoding UTF8

    It "shared review-routing contract exists" {
        Test-Path $contractFile | Should -Be $true
    }

    It "shared contract defines all staged modes" {
        foreach ($mode in @("light", "standard", "data-risk", "architecture", "full")) {
            ($contract -match [regex]::Escape($mode)) | Should -Be $true
        }
    }

    It "shared contract maps risk classes to resolved modes" {
        foreach ($riskClass in @("low", "normal", "data-risk", "architecture-risk", "security-risk")) {
            ($contract -match [regex]::Escape($riskClass)) | Should -Be $true
        }
    }

    It "shared contract documents precedence and additive dedup" {
        ($contract -match '(?s)Resolve exactly one route.*explicit user mode.*auto risk-class routing result.*line-volume escalation.*config default') | Should -Be $true
        ($contract -match 'additive dedup|dispatch once') | Should -Be $true
    }

    It "shared contract makes explicit user modes win over auto routing" {
        ($contract -match '(?s)Explicit user modes win.*Auto risk-class routing applies only.*no explicit mode') | Should -Be $true
        ($contract -match '(?s)cg-review light.*high-risk diff.*light') | Should -Be $true
        ($contract -match '(?s)cg-review full.*low-risk.*full') | Should -Be $true
    }

    It "shared contract routes linking and schema changes as security-risk" {
        ($contract -match '(?s)linking/unlinking paths.*schema changes.*security-risk') | Should -Be $true
    }

    It "cg-review references the shared routing contract" {
        ($reviewContent -match 'review-routing\.contract\.md') | Should -Be $true
    }

    It "cg-work references the shared routing contract" {
        ($workContent -match 'review-routing\.contract\.md') | Should -Be $true
    }
}

Describe "cg-review.prompt.md - staged routing modes" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "parser accepts staged review modes" {
        foreach ($mode in @("data-risk", "architecture", "full")) {
            ($content -match "Recognized:.*$mode") | Should -Be $true
        }
    }

    It "maps thorough to full for backward compatibility" {
        ($content -match '(?s)thorough.*maps to.*full|thorough.*full dispatch') | Should -Be $true
    }

    It "contains a deterministic preflight routing step before dispatch" {
        $preflight = $content.IndexOf("### Step 1.5:")
        $dispatch = $content.IndexOf("### Step 2:")
        ($preflight -ge 0) | Should -Be $true
        ($dispatch -gt $preflight) | Should -Be $true
        ($content -match 'deterministic preflight|risk-class routing') | Should -Be $true
    }

    It "routes statistical and reproducibility-sensitive triggers to data-risk" {
        ($content -match '(?s)statistical.*reproducibility.*data-risk|survey.*poverty.*welfare.*data-risk') | Should -Be $true
    }

    It "routes architecture and performance-heavy triggers to architecture" {
        ($content -match '(?s)architecture.*performance.*architecture-risk|architecture-risk.*architecture') | Should -Be $true
    }

    It "routes security-risk changes to full" {
        ($content -match '(?s)security-risk.*full|auth.*secret.*credential.*full') | Should -Be $true
    }

    It "makes explicit user modes win and reserves auto routing for no explicit mode" {
        ($content -match '(?s)explicit user mode wins.*auto risk-class routing') | Should -Be $true
        ($content -match '(?s)Auto risk-class routing applies only.*no explicit mode') | Should -Be $true
        ($content -match '(?s)requests `full`.*low-risk diff.*keep `full`') | Should -Be $true
    }

    It "routes linking and schema changes to full" {
        ($content -match '(?s)linking/unlinking paths.*schema changes.*security-risk.*full|linking-risk.*schema-risk') | Should -Be $true
    }

    It "keeps verify mode light-only and exempt from staged broad routing" {
        ($content -match '(?s)mode:verify.*light-only|verify mode.*exempt.*staged') | Should -Be $true
    }

    It "reruns normal routing if verify mode falls back" {
        ($content -match '(?s)Step 1\.7 disables verify mode.*continue normal routing|Falling back to normal review.*disable verify mode') | Should -Be $true
    }

    It "documents line-volume can only raise light to standard" {
        ($content -match 'light\s*->\s*standard|light.*standard') | Should -Be $true
        ($content -match 'Explicit user modes take precedence over line-volume upgrades|explicit user mode wins.*line-volume') | Should -Be $true
    }

    It "missing changed-file scope asks for scope and does not silently broad dispatch" {
        ($content -match '(?s)no changed files|missing changed-file scope') | Should -Be $true
        ($content -match '(?s)ask.*scope|prompt.*scope') | Should -Be $true
        ($content -match 'no silent broad default dispatch|do not silently.*broad') | Should -Be $true
    }

    It "full review remains explicitly requestable" {
        ($content -match 'full') | Should -Be $true
        ($content -match 'explicit user.*full|Users can.*request.*full') | Should -Be $true
    }
}

Describe "cg-work.prompt.md - review mode integration" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "parses review mode arguments in Step 0" {
        ($content -match '(?s)Step 0:.*review:\*|Parse flags.*review:') | Should -Be $true
        foreach ($mode in @("review:auto", "review:manual", "review:none")) {
            ($content -match [regex]::Escape($mode)) | Should -Be $true
        }
    }

    It "accepts explicit routed review values" {
        foreach ($mode in @("review:light", "review:standard", "review:data-risk", "review:architecture", "review:full")) {
            ($content -match [regex]::Escape($mode)) | Should -Be $true
        }
    }

    It "adds Step 3.9 after Step 3.8 for review-mode behavior" {
        $step38 = $content.IndexOf("### Step 3.8:")
        $step39 = $content.IndexOf("### Step 3.9:")
        $step4 = $content.IndexOf("### Step 4:")
        ($step38 -ge 0) | Should -Be $true
        ($step39 -gt $step38) | Should -Be $true
        ($step4 -gt $step39) | Should -Be $true
    }

    It "default and review:manual do not dispatch review agents and recommend a mode" {
        ($content -match '(?s)default.*review:manual.*no agent dispatch|no review arg.*no agent dispatch') | Should -Be $true
        ($content -match '(?s)recommend.*review mode|suggested command.*cg-review') | Should -Be $true
    }

    It "review:auto dispatches route-appropriate agents through the shared contract" {
        ($content -match '(?s)review:auto.*shared routing contract.*dispatch only the route-appropriate agent set|review:auto.*route-aware agent dispatch') | Should -Be $true
    }

    It "review:none suppresses dispatch and shows only a brief note" {
        ($content -match '(?s)review:none.*suppress.*dispatch.*brief note|review:none.*brief suppression note') | Should -Be $true
    }

    It "invalid review values warn and fall back to recommendation mode" {
        ($content -match '(?s)invalid `review:<value>`|Invalid review value|unrecognized review') | Should -Be $true
        ($content -match '(?s)fall back.*recommendation mode|fallback.*recommendation') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 6 — token benchmark and regression guardrails
# ---------------------------------------------------------------------------

Describe "Phase 6 review routing guardrails" {
    $contractFile = Join-Path $repoRoot ".github\shared\review-routing.contract.md"
    $reviewFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $workFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $contract = Get-Content $contractFile -Raw -Encoding UTF8
    $reviewContent = Get-Content $reviewFile -Raw -Encoding UTF8
    $workContent = Get-Content $workFile -Raw -Encoding UTF8

    It "preserves expected static review-agent counts by routed mode" {
        $contract | Should -Match '\| `light` \| `@cg-code-quality`, `@cg-testing` \|'
        $contract | Should -Match '\| `standard` \| `@cg-code-quality`, `@cg-testing`, `@cg-documentation`, `@cg-version-control`, `@cg-reproducibility`, `@cg-performance`, `@cg-architecture`, `@cg-data-quality` \|'
        $contract | Should -Match '\| `data-risk` \| all `standard` agents'
        $contract | Should -Match '\| `architecture` \| all `standard` agents'
        $contract | Should -Match '\| `full` \| all `standard` agents plus `@cg-learnings-researcher` and `@cg-adversarial` \|'
    }

    It "asserts effective /cg-review route precedence independent of table ordering" {
        ($contract -match '(?s)Explicit user modes win.*Auto risk-class routing applies only.*no explicit mode') | Should -Be $true
        ($reviewContent -match '(?s)explicit user mode wins.*Auto risk-class routing applies only.*no explicit mode') | Should -Be $true
        ($reviewContent -match '(?s)mode:verify.*light-only|verify mode.*light-only') | Should -Be $true
    }

    It "preserves explicit full review and thorough alias" {
        ($reviewContent -match '(?s)Users can explicitly request `full` review|explicitly request.*full') | Should -Be $true
        ($reviewContent -match '(?s)`thorough`.*maps to `full`|thorough.*full dispatch') | Should -Be $true
    }

    It "preserves /cg-work default/manual/auto/none dispatch semantics" {
        ($workContent -match '(?s)No review arg defaults to `review:manual`.*no agent dispatch') | Should -Be $true
        ($workContent -match '(?s)Default and `review:manual` must never dispatch review agents automatically') | Should -Be $true
        ($workContent -match '(?s)`review:auto`.*route-aware agent dispatch') | Should -Be $true
        ($workContent -match '(?s)`review:none`.*Suppress review dispatch') | Should -Be $true
    }
}

Describe "Phase 6 Knowledge Brain broad-read guardrails" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-brain-query\SKILL.md"
    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "uses query-first retrieval through BRAIN.md and matched topics" {
        ($content -match 'BRAIN\.md') | Should -Be $true
        ($content -match '(?s)Match Topics.*Open Sub-files|matched topic') | Should -Be $true
        ($content -match 'Do NOT read all BRAIN-NN\.md sub-files|read all BRAIN-NN\.md sub-files blindly') | Should -Be $true
    }

    It "prefers budgeted cg-index query with intent, budget, and BRAIN.md fallback" {
        ($content -match 'cg-index query') | Should -Be $true
        ($content -match '--intent <brainstorm\|plan\|work\|review\|compound\|resume>') | Should -Be $true
        ($content -match '--budget <tokens>') | Should -Be $true
        ($content -match '(?s)If `cg-index query` is unavailable.*fall back to.*BRAIN\.md') | Should -Be $true
    }

    It "does not tell agents to read brain-index.json wholesale while allowing tooling query use" {
        ($content -match 'brain-index\.json') | Should -Be $true
        ($content -match '(?s)agents must not read it wholesale|prompt agents must not read it wholesale') | Should -Be $true
        ($content -match '(?s)tooling.*query|Python tooling may query') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Review convergence â€” cg-fix-triage mode:verify handoff
# ---------------------------------------------------------------------------

Describe "cg-fix-triage.prompt.md - mode:verify handoff" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "suggests mode:verify instead of review light in Step 5" {
        ($content -match '(?s)Step 5.*mode:verify') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.7/P2.8 â€” cg-release-scanner.agent.md existence and dispatch reference
# ---------------------------------------------------------------------------

Describe "cg-release-scanner.agent.md - existence and structure" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-release-scanner.agent.md"

    It "exists in the repository" {
        Test-Path $agentFile | Should -Be $true
    }

    Context "required frontmatter fields" {
        $frontmatter = Get-Frontmatter -FilePath $agentFile

        It "has user-invocable: false in frontmatter" {
            ($frontmatter -match 'user-invocable:\s*false') | Should -Be $true
        }

        It "has tools: restricted to read and search (not write)" {
            ($frontmatter -match "tools:.*'read'") -and ($frontmatter -match "tools:.*'search'") | Should -Be $true
        }

        It "inherits the selected model without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }

    $agentContent = Get-Content $agentFile -Raw -Encoding UTF8

    It "documents Highest impact: none for empty commit log" {
        ($agentContent -match 'Highest impact: none') | Should -Be $true
    }

    It "uses window-days (hyphen, not underscore) in window-start description" {
        ($agentContent -match 'window-days') | Should -Be $true
    }
    It "uses tag-date (hyphen, not underscore) in window-start description" {
        ($agentContent -match 'tag-date') | Should -Be $true
    }
}

Describe "cg-release.prompt.md - dispatches cg-release-scanner" {
    $promptFile = Join-Path $repoRoot "cg-release.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "cg-release.prompt.md references @cg-release-scanner" {
        ($content -match '@cg-release-scanner') | Should -Be $true
    }

    It "warns when window-start is on or after today (zero-doc-context guard)" {
        ($content -match 'window-start.*today|All.*cg-docs.*entries will be excluded') | Should -Be $true
    }

    It "warns and falls back when --since ISO date is in the future" {
        ($content -match 'after today.*fall back|parsed.*after today') | Should -Be $true
    }

    It "warns when commit log exceeds 500 lines" {
        ($content -match '500 lines|exceeds 500') | Should -Be $true
    }

    It "warns on shallow clone and falls back to window-days formula" {
        ($content -match 'shallow clone') | Should -Be $true
    }

    It "catch-all when release-result.txt is absent or unrecognized" {
        ($content -match 'may have failed|release-result\.txt.*absent|neither.*CREATED') | Should -Be $true
    }

    It "documents halt condition when scanner returns no output" {
        ($content -match 'no output|does not contain.*Scan Summary|Scanner returned no output') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-skill-project-scanner - existence and structure
# ---------------------------------------------------------------------------

Describe "cg-skill-project-scanner - existence and structure" {
    $skillDir  = Join-Path $repoRoot ".github\skills\cg-skill-project-scanner"
    $skillFile = Join-Path $skillDir "SKILL.md"

    It "skill directory exists" {
        Test-Path $skillDir | Should -Be $true
    }

    It "SKILL.md exists" {
        Test-Path $skillFile | Should -Be $true
    }

    Context "frontmatter fields" {
        $frontmatter = if (Test-Path $skillFile) { Get-Frontmatter -FilePath $skillFile } else { "" }

        It "has a name: field in frontmatter" {
            ($frontmatter -match 'name:') | Should -Be $true
        }

        It "has a description: field in frontmatter" {
            ($frontmatter -match 'description:') | Should -Be $true
        }

        It "has a schema-version: field in frontmatter" {
            ($frontmatter -match 'schema-version:') | Should -Be $true
        }
    }

    $skillContent = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }

    It "contains Tier 1 heading (Language and Framework Detection)" {
        ($skillContent -match 'Tier 1') | Should -Be $true
    }

    It "contains Tier 2 heading (Project Type and Convention)" {
        ($skillContent -match 'Tier 2') | Should -Be $true
    }

    It "contains Tier 3 heading (Charter-Relevant Content)" {
        ($skillContent -match 'Tier 3') | Should -Be $true
    }

    It "contains Tier 4 heading (Out of Scope)" {
        ($skillContent -match 'Tier 4') | Should -Be $true
    }

    It "contains confidence threshold table with high/medium/low rows" {
        ($skillContent -match '(?i)\|\s*(high|medium|low)\s*\|') | Should -Be $true
    }

    It "contains output schema section" {
        ($skillContent -match 'Output Schema') | Should -Be $true
    }

    It "contains prompt injection safety rule" {
        ($skillContent -match 'data, not instructions|prompt injection') | Should -Be $true
    }

    It "signal catalog is non-empty (Tier 1 has at least one row)" {
        # After the Tier 1 heading there should be at least one table row with a pipe character
        ($skillContent -match 'Tier 1[\s\S]+?\|[^\n]+\|') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-project-scanner.agent.md - existence and structure
# Note: No dispatch test â€” the calling prompt (/cg-setup) is not modified
# until Phase 2. Limit tests to agent existence, frontmatter, and content.
# ---------------------------------------------------------------------------

Describe "cg-project-scanner.agent.md - existence and structure" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-project-scanner.agent.md"

    It "exists in the repository" {
        Test-Path $agentFile | Should -Be $true
    }

    Context "required frontmatter fields" {
        $frontmatter = if (Test-Path $agentFile) { Get-Frontmatter -FilePath $agentFile } else { "" }

        It "has user-invocable: false in frontmatter" {
            ($frontmatter -match 'user-invocable:\s*false') | Should -Be $true
        }

        It "has tools: restricted to read and search (not write)" {
            $tools = Get-ToolsList $frontmatter
            ($tools -contains 'read') -and ($tools -contains 'search') -and (-not ($tools -contains 'write')) | Should -Be $true
        }

        It "inherits the selected model without model frontmatter" {
            ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
        }
    }

    $agentContent = if (Test-Path $agentFile) { Get-Content $agentFile -Raw -Encoding UTF8 } else { "" }

    It "references cg-skill-project-scanner (loads the signal catalog)" {
        ($agentContent -match 'cg-skill-project-scanner') | Should -Be $true
    }

    It "contains prompt injection guard (data not instructions)" {
        ($agentContent -match 'data, not instructions|prompt injection') | Should -Be $true
    }

    It "output schema includes Scan Summary section" {
        ($agentContent -match 'Scan Summary') | Should -Be $true
    }

    It "output schema includes Language Detection section" {
        ($agentContent -match 'Language Detection') | Should -Be $true
    }

    It "output schema includes Project Type section" {
        ($agentContent -match 'Project Type') | Should -Be $true
    }

    It "output schema includes Framework and Tooling section" {
        ($agentContent -match 'Framework.*Tooling|Tooling.*Framework') | Should -Be $true
    }

    It "output schema includes Charter Draft Content section" {
        ($agentContent -match 'Charter Draft Content') | Should -Be $true
    }

    It "output schema includes Setup Recommendations section" {
        ($agentContent -match 'Setup Recommendations') | Should -Be $true
    }

    It "does not reference write or terminal tools" {
        ($agentContent -match 'editFiles|runInTerminal|createFile') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# P1.44 â€” cg-brainstorm Branch Offer must appear before Step 2 questions
# The branch offer is the very first question asked of the user, so the
# model cannot bias itself toward an existing branch mid-brainstorm.
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Branch Offer appears before Step 2" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has a Branch Offer step between Step 1.5 and Step 2 (Step 1.7)" {
        $branchOfferIdx = $content.IndexOf('### Step 1.7:')
        $branchOfferIdx | Should -BeGreaterThan -1
    }

    It "Branch Offer (Step 1.7) appears before Step 2 Clarifying Questions" {
        $branchOfferIdx = $content.IndexOf('### Step 1.7:')
        $step2Idx       = $content.IndexOf('### Step 2:')
        $branchOfferIdx | Should -BeGreaterThan -1
        $step2Idx       | Should -BeGreaterThan $branchOfferIdx
    }
}

# ---------------------------------------------------------------------------
# cg-skill-stata-testing - all 8 skill files exist
# ---------------------------------------------------------------------------

Describe "cg-skill-stata-testing - skill file structure" {
    $skillRoot = Join-Path $repoRoot ".github\skills\cg-skill-stata-testing"
    $skillFile = Join-Path $skillRoot "SKILL.md"
    $skillContent = Get-Content $skillFile -Raw -Encoding UTF8
    $skillFm = Get-Frontmatter -FilePath $skillFile
    $skillLineCount = (Get-Content $skillFile).Count
    $expectedFiles = @(
        "SKILL.md",
        "references\assertions-and-error-handling.md",
        "references\data-validation.md",
        "references\result-verification.md",
        "references\reproducibility-reprun.md",
        "references\test-scaffolding.md",
        "references\anti-patterns.md",
        "references\workflow-examples.md"
    )

    foreach ($file in $expectedFiles) {
        It "file '$file' exists" {
            Test-Path (Join-Path $skillRoot $file) | Should -Be $true
        }
    }

    It "SKILL.md has a description: field" {
        ($skillFm -match 'description:') | Should -Be $true
    }

    It "SKILL.md description is non-empty" {
        ($skillContent -match 'description:\s*[>|]?\s*\S') | Should -Be $true
    }

    It "SKILL.md is 100 lines or fewer (thin routing table)" {
        $skillLineCount | Should -BeLessThan 101
    }

    It "SKILL.md references cg-skill-stata-best-practices (cross-reference)" {
        ($skillContent -match 'cg-skill-stata-best-practices') | Should -Be $true
    }

    It "SKILL.md has user-invokable: false (P2.3)" {
        ($skillFm -match 'user-invokable:\s*false') | Should -Be $true
    }

    It "SKILL.md description trigger mentions assertion blocks (P2.4)" {
        ($skillFm -match 'assertion blocks') | Should -Be $true
    }

    It "anti-patterns.md references coding-principles (cross-reference)" {
        $antiFile = Join-Path $skillRoot "references\anti-patterns.md"
        $content = if (Test-Path $antiFile) { Get-Content $antiFile -Raw -Encoding UTF8 } else { "" }
        ($content -match 'coding-principles') | Should -Be $true
    }

    It "data-validation.md uses r(balanced) not e(balanced) (P0.2 guard)" {
        $dv = Get-Content (Join-Path $skillRoot "references\data-validation.md") -Raw -Encoding UTF8
        ($dv -match 'e\(balanced\)') | Should -Be $false
        ($dv -match 'r\(balanced\)') | Should -Be $true
    }

    It "data-validation.md has no assert with inline string message (P0.1 guard)" {
        $dv = Get-Content (Join-Path $skillRoot "references\data-validation.md") -Raw -Encoding UTF8
        # assert[^()\r\n]+,\s*" matches assert without parens before the comma (excludes inlist(), inrange() etc.)
        ($dv -match 'assert\b[^()\r\n]+,\s*"') | Should -Be $false
    }

    It "result-verification.md stores spec coefficient before reldif (P0.3 guard)" {
        $rv = Get-Content (Join-Path $skillRoot "references\result-verification.md") -Raw -Encoding UTF8
        ($rv -match 'local\s+b\d\s*=\s*_b\[') | Should -Be $true
    }

    It "SKILL.md routing table lists 9 anti-patterns (P2.1 guard)" {
        ($skillContent -match '9 testing-specific anti-patterns') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-skill-stata-testing - stata.instructions.md routing
# ---------------------------------------------------------------------------

Describe "stata.instructions.md - skill routing" {
    $instrFile = Join-Path $repoRoot ".github\instructions\stata.instructions.md"
    $content = if (Test-Path $instrFile) { Get-Content $instrFile -Raw -Encoding UTF8 } else { "" }

    It "stata.instructions.md exists" {
        Test-Path $instrFile | Should -Be $true
    }

    It "has applyTo covering .do files" {
        $fm = Get-Frontmatter -FilePath $instrFile
        ($fm -match '\.do') | Should -Be $true
    }

    It "has applyTo covering .ado files" {
        $fm = Get-Frontmatter -FilePath $instrFile
        ($fm -match '\.ado') | Should -Be $true
    }

    It "routes to cg-skill-stata-best-practices" {
        ($content -match 'cg-skill-stata-best-practices') | Should -Be $true
    }

    It "routes to cg-skill-stata-testing" {
        ($content -match 'cg-skill-stata-testing') | Should -Be $true
    }

    It "uses conditional trigger language for stata-testing" {
        ($content -match 'cg-skill-stata-testing.*when writing|when writing.*cg-skill-stata-testing') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-skill-stata-testing - docs/reference.md registration
# ---------------------------------------------------------------------------

Describe "docs/reference.md - cg-skill-stata-testing registration" {
    $refFile = Join-Path $repoRoot "docs\reference.md"
    $content = if (Test-Path $refFile) { Get-Content $refFile -Raw -Encoding UTF8 } else { "" }

    It "docs/reference.md lists cg-skill-stata-testing" {
        ($content -match 'cg-skill-stata-testing') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# docs/reference.md - phased plan (P1.6 + P1.7)
# ---------------------------------------------------------------------------

Describe "docs/reference.md - phased plan documentation" {
    $refFile = Join-Path $repoRoot "docs\reference.md"
    $content = if (Test-Path $refFile) { Get-Content $refFile -Raw -Encoding UTF8 } else { "" }

    It "/cg-work entry documents phaseX argument syntax" {
        ($content -match '/cg-work \[phaseX\]|cg-work phase') | Should Be $true
    }

    It "documents phases: frontmatter field as a convenience hint" {
        ($content -match 'phases.*hint|hint.*phases') | Should Be $true
    }

    It "documents completed-phases as the authoritative completion record" {
        ($content -match 'completed-phases') | Should Be $true
    }

    It "documents current-phase frontmatter field" {
        ($content -match 'current-phase') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# copilot-instructions.md - cg-skill-stata-testing registration (P2.2)
# ---------------------------------------------------------------------------

Describe "copilot-instructions.md - cg-skill-stata-testing registration" {
    $instrFile = Join-Path $repoRoot ".github\copilot-instructions.md"
    $content = if (Test-Path $instrFile) { Get-Content $instrFile -Raw -Encoding UTF8 } else { "" }

    It "copilot-instructions.md registers cg-skill-stata-testing" {
        ($content -match 'cg-skill-stata-testing') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-plan.prompt.md - Step 0.7 Branch Offer ordering
# Feature: branch-creation-from-plan (Workflow Maturity milestone)
# Verifies the branch offer step exists between Step 0.5 and Step 1.
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Step 0.7 Branch Offer ordering" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 0.7 Branch Offer exists in the prompt" {
        ($content -match '### Step 0\.7:.*Branch Offer') | Should -Be $true
    }

    It "File Permissions references branch creation at Step 0.7" {
        ($content -match 'create a git branch.*Step 0\.7') | Should -Be $true
    }

    It "Step 0.7 Branch Offer appears after Step 0.5" {
        $step05Idx  = $content.IndexOf('### Step 0.5:')
        $step07Idx  = $content.IndexOf('### Step 0.7:')
        $step05Idx  | Should -BeGreaterThan -1
        $step07Idx  | Should -BeGreaterThan -1
        $step07Idx  | Should -BeGreaterThan $step05Idx
    }

    It "Step 1 Gather Context appears after Step 0.7 Branch Offer" {
        $step07Idx = $content.IndexOf('### Step 0.7:')
        $step1Idx  = $content.IndexOf('### Step 1:')
        $step07Idx | Should -BeGreaterThan -1
        $step1Idx  | Should -BeGreaterThan -1
        $step1Idx  | Should -BeGreaterThan $step07Idx
    }

    It "Branch Offer skips silently when already on a feature branch" {
        ($content -match 'already on a.*branch.*skip silently') | Should -Be $true
    }

    It "Branch Offer warns on uncommitted changes" {
        ($content -match 'uncommitted changes') | Should -Be $true
    }

    # P1.1 â€” type derivation rule must appear before the offer block
    It "Branch type derivation rule appears before the offer block" {
        $derivationIdx = $content.IndexOf('Derive the branch name')
        $offerIdx      = $content.IndexOf('Suggested name:')
        $derivationIdx | Should -BeGreaterThan -1
        $offerIdx      | Should -BeGreaterThan -1
        $derivationIdx | Should -BeLessThan $offerIdx
    }

    # P1.2 â€” uncommitted-changes check must appear before the offer block
    It "Uncommitted-changes check appears before the offer block" {
        $uncommittedIdx = $content.IndexOf('uncommitted changes')
        $offerIdx       = $content.IndexOf('Suggested name:')
        $uncommittedIdx | Should -BeGreaterThan -1
        $offerIdx       | Should -BeGreaterThan -1
        $uncommittedIdx | Should -BeLessThan $offerIdx
    }

    # P1.3 â€” error handling when branch already exists
    It "Handles git checkout -b failure when branch already exists" {
        ($content -match 'already exists.*switch to it') | Should -Be $true
    }

    # P1.4 â€” cleanup path for orphaned branches
    It "Provides cleanup instruction for orphaned branch when planning abandoned" {
        ($content -match 'git branch -d') | Should -Be $true
    }

    # P1.5 â€” extended type taxonomy covers all conventional-commit types
    It "Branch type taxonomy includes extended types (test, docs, chore, data, analysis)" {
        ($content -match 'test/.*testing work') | Should -Be $true
        ($content -match 'analysis/.*analysis work') | Should -Be $true
        ($content -match 'chore/.*maintenance') | Should -Be $true
        ($content -match 'docs/.*documentation') | Should -Be $true
        ($content -match 'data/.*data work')      | Should -Be $true
    }

    # P2.3 â€” dynamic default branch detection via git symbolic-ref
    It "Uses git symbolic-ref for dynamic default branch detection" {
        ($content -match 'git symbolic-ref refs/remotes/origin/HEAD') | Should -Be $true
    }

    # P2.4 â€” non-git workspace guard
    It "Skips silently when git command fails or returns empty (non-git workspace)" {
        ($content -match 'fails or returns empty.*non-git|non-git workspace.*skip') | Should -Be $true
    }

    # P2.5 â€” branch name sanitization
    It "Branch name normalization rule is present" {
        ($content -match 'Normalize the branch name') | Should -Be $true
        ($content -match 'truncate to 60') | Should -Be $true
    }

    # P2.6 â€” Refine path skips branch offer
    It "Refine decision at Step 0.5 skips the branch offer" {
        ($content -match 'Refine.*decision.*skip|Refine.*skip.*branch') | Should -Be $true
    }

    # P3.1 â€” placeholder matches cg-brainstorm style with 'from-your-request'
    It "Offer placeholder uses 'from-your-request' suffix to match cg-brainstorm style" {
        ($content -match 'short-description-from-your-request') | Should -Be $true
    }

    # P3.2 â€” user-facing language matches cg-brainstorm 'If the user accepts/declines'
    It "Uses 'If the user accepts' and 'If the user declines' phrasing" {
        ($content -match 'If the user accepts') | Should -Be $true
        ($content -match 'If the user declines') | Should -Be $true
    }

    # P3.6 â€” branch name convention and creation command are tested
    It "Branch type convention covers feat, fix, refactor" {
        ($content -match '(?s)feat/.*fix/.*refactor/') | Should -Be $true
    }

    It "Branch creation uses git checkout -b" {
        ($content -match 'git checkout -b') | Should -Be $true
    }

    # P2.2 â€” "other errors â†’ report verbatim" path is tested
    It "Reports git error verbatim and skips branching on other checkout failures" {
        ($content -match 'other errors.*verbatim|report the git error verbatim') | Should -Be $true
    }

    # P2.3 â€” "empty after normalization â†’ ask user" fallback is tested
    It "Asks user for branch name when normalization yields empty string" {
        ($content -match 'empty after normalization.*ask the user') | Should -Be $true
    }
}


# ---------------------------------------------------------------------------
# Phased plan structure â€” cg-plan.prompt.md Step 3.5
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - phase structure support" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "contains Step 3.5 Phase Structure section" {
        ($content -match 'Phase Structure') | Should Be $true
    }

    It "documents phases: frontmatter field in phased template" {
        ($content -match 'phases:') | Should Be $true
    }

    It "shows ## Phase header format in the phased template example" {
        ($content -match '## Phase') | Should Be $true
    }

    It "phases by default applies to Deep scope plans" {
        ($content -match '(?s)Step 3\.5.*organized into phases by default') | Should Be $true
    }

    It "phases by default for all scopes (no optional offer for Standard scope)" {
        # Phases are automatic now -- the old 'Would you like to organize' offer is gone
        ($content -match 'organized into phases by default') | Should Be $true
    }

    It "silently skips phase offer for Lightweight scope" {
        ($content -match '(?i)Lightweight.*skip silently|skip silently') | Should Be $true
    }

    It "Step 3.5 appears before Step 4 in the file" {
        $step35Pos = $content.IndexOf("### Step 3.5:")
        $step4Pos  = $content.IndexOf("### Step 4:")
        $step35Pos | Should BeGreaterThan -1
        $step4Pos  | Should BeGreaterThan -1
        $step35Pos | Should BeLessThan $step4Pos
    }

    It "Step 3.5 checks for non-empty completed-phases before restructuring phases (pre-flight guard)" {
        ($content -match 'completed phases recorded|invalidate the completion history') | Should Be $true
    }

    It "phases: example includes hint comment noting the field may be stale (P3.10)" {
        ($content -match 'phases:.*convenience hint|may be stale.*recount') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Phased execution â€” cg-work.prompt.md Steps 1.2 and 2.5
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - phase argument parsing (Step 1.2)" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "contains Step 1.2 Parse Phase Argument section" {
        ($content -match 'Step 1\.2|Parse Phase Argument') | Should Be $true
    }

    It "documents completed-phases frontmatter field" {
        ($content -match 'completed-phases') | Should Be $true
    }

    It "documents current-phase frontmatter field" {
        ($content -match 'current-phase') | Should Be $true
    }

    It "documents out-of-bounds error message" {
        ($content -match 'Phase N does not exist') | Should Be $true
    }

    It "documents sequential enforcement error message (Phase X cannot start)" {
        ($content -match 'Phase X cannot start') | Should Be $true
    }

    It "Step 1.2 appears before Step 1.5 in the file" {
        $step12Pos = $content.IndexOf("### Step 1.2:")
        $step15Pos = $content.IndexOf("### Step 1.5:")
        $step12Pos | Should BeGreaterThan -1
        $step15Pos | Should BeGreaterThan -1
        $step12Pos | Should BeLessThan $step15Pos
    }

    It "Step 1.2 phase detection ignores ## Phase inside fenced code blocks" {
        ($content -match 'fenced code block|ignore.*code block|code block.*ignore') | Should Be $true
    }

    It "Step 1.2 no-arg phased path skips completed phases" {
        ($content -match 'skip.*completed|already.*completed-phases') | Should Be $true
    }

    It "Step 1.2 accepts case-insensitive phase argument forms" {
        ($content -match 'case.insensitive') | Should Be $true
    }

    It "Step 1.2 warns when phase arg given on non-phased plan" {
        ($content -match 'This plan has no phases|no phases.*Executing') | Should Be $true
    }

    It "Step 1.2 sequential enforcement exempts phase 1" {
        ($content -match 'phase 1 is always allowed|exception.*phase 1') | Should Be $true
    }

    It "Step 1.2 treats absent completed-phases as empty list" {
        ($content -match 'absent.*treat.*\[\]|absent.*empty list') | Should Be $true
    }

    It "Step 1.2 validates no-arg phased run has positive integers in [1, M]" {
        ($content -match 'positive integers in.*1.*M|entries.*out of range') | Should Be $true
    }

    It "Step 1.2 all-phases-complete path halts with clear message" {
        ($content -match 'All.*phases.*already complete|phases are already complete') | Should Be $true
    }

    It "Step 1.2 all-phases-complete halt message uses M (not N) for phase count (P3.v1)" {
        ($content -match 'All M phases are already complete') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase argument validation â€” cg-work.prompt.md Step 1.2 (P1.3, P2.17, P2.18)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - phase argument validation" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 1.2 validates lower-bound (phase0 is not valid)" {
        ($content -match 'phase.*must be.*1|phase0.*not valid|N < 1') | Should Be $true
    }

    It "Step 1.2 re-validates phase argument after plan-loading fallback" {
        ($content -match 're-count.*recovered|re-validate.*fallback|After any plan-file fallback') | Should Be $true
    }

    It "Step 1.2 preamble headings excluded from phase membership scan" {
        ($content -match 'preamble.*NOT steps|before the first.*Phase.*preamble') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase boundary â€” cg-work.prompt.md Step 2.5 (P0.1, P0.2, P1.1, P2.11, P2.12)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - phase boundary (Step 2.5)" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "contains Step 2.5 Phase Boundary section" {
        ($content -match 'Step 2\.5|Phase Boundary') | Should Be $true
    }

    It "documents phase-terminal commit suppression" {
        ($content -match 'phase-terminal|sub-step 6') | Should Be $true
    }

    It "Step 2.5 appears before Step 3 in the file" {
        $step25Pos = $content.IndexOf("### Step 2.5:")
        $step3Pos  = $content.IndexOf("### Step 3:")
        $step25Pos | Should BeGreaterThan -1
        $step3Pos  | Should BeGreaterThan -1
        $step25Pos | Should BeLessThan $step3Pos
    }

    It "instructs keeping status: active when user stops at phase boundary" {
        ($content -match 'paused between phases') | Should Be $true
    }

    It "Step 2.5 mandates completed-phases written before current-phase (crash-safe write order)" {
        ($content -match 'exact order|crash.safe|authoritative completion record') | Should Be $true
    }

    It "Step 2.5 mandates YAML flow sequence with unquoted integers for completed-phases" {
        ($content -match 'unquoted integer|Never use quoted') | Should Be $true
    }

    It "Step 2.5 does not mark a phase complete when tests or failing-steps remain" {
        ($content -match '(?s)full-suite gate fails.*do not append `N` to `completed-phases`') | Should Be $true
        ($content -match '(?s)failing-steps.*do not append `N` to `completed-phases`') | Should Be $true
        ($content -match '(?s)fixed, skipped, deferred, or accepted with rationale') | Should Be $true
    }

    It "Step 2.5 handles final phase (N = M) by proceeding to Step 3 without continue/stop offer" {
        ($content -match 'final phase.*N = M|N = M.*final phase') | Should Be $true
    }

    It "Step 2.5 removes current-phase frontmatter after final phase" {
        ($content -match 'remove.*current-phase|current-phase.*final') | Should Be $true
    }

    It "Step 2.5 documents current-phase as informational only with no consumer" {
        ($content -match 'informational only|no prompt reads') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# File permissions â€” cg-work.prompt.md phase fields (P2 additions)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - file permissions include phase fields" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    # Extract the File Permissions section (between ## File Permissions and ## Process)
    $permStart = $content.IndexOf("## File Permissions")
    $permEnd   = $content.IndexOf("## Process")
    $permBlock = if ($permStart -ge 0 -and $permEnd -gt $permStart) {
        $content.Substring($permStart, $permEnd - $permStart)
    } else { "" }

    It "File Permissions section start anchor found (IndexOf guard)" {
        $permStart | Should BeGreaterThan -1
    }

    It "Process section start anchor found - end of perm block (IndexOf guard)" {
        $permEnd | Should BeGreaterThan $permStart
    }

    It "File Permissions section exists" {
        $permBlock | Should Not BeNullOrEmpty
    }

    It "File Permissions section mentions completed-phases" {
        ($permBlock -match 'completed-phases') | Should Be $true
    }

    It "File Permissions section mentions current-phase" {
        ($permBlock -match 'current-phase') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Phased execution â€” cg-resume.prompt.md phase progress display
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - phase progress display in Step 2a" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    # Extract Step 2a section only (from "#### 2a." to "#### 2b.") â€” P3.4 scope fix
    $step2aStart = $content.IndexOf("#### 2a.")
    $step2bStart = $content.IndexOf("#### 2b.")
    $step2aBlock = if ($step2aStart -ge 0 -and $step2bStart -gt $step2aStart) {
        $content.Substring($step2aStart, $step2bStart - $step2aStart)
    } else { "" }

    It "Step 2a section start anchor found (IndexOf guard)" {
        $step2aStart | Should BeGreaterThan -1
    }

    It "Step 2b section start is after Step 2a (IndexOf guard)" {
        $step2bStart | Should BeGreaterThan $step2aStart
    }

    It "Step 2a section exists" {
        $step2aBlock | Should Not BeNullOrEmpty
    }

    It "references completed-phases frontmatter field in Step 2a" {
        ($step2aBlock -match 'completed-phases') | Should Be $true
    }

    It "documents phase progress display format" {
        ($step2aBlock -match 'Phase progress:') | Should Be $true
    }

    It "documents next phase suggestion with /cg-work phase command" {
        ($step2aBlock -match '/cg-work phase') | Should Be $true
    }

    It "sanitizes malformed completed-phases before computing next phase (discards non-integer entries)" {
        ($step2aBlock -match 'discard.*not positive integer|deduplicate') | Should Be $true
    }

    It "uses smallest integer >= 1 (lower-bound) for next phase computation" {
        ($step2aBlock -match 'smallest integer.*1|integer.*1.*not in') | Should Be $true
    }

    It "reads plan body to count ## Phase headers (not phases: hint) for M" {
        ($step2aBlock -match 'read the plan body|authoritative header count|do not use the.*phases.*hint') | Should Be $true
    }

    It "displays absent completed-phases as no phase info (three-branch display: absent)" {
        ($step2aBlock -match 'completed-phases.*absent.*no phase|absent.*display no phase') | Should Be $true
    }

    It "displays completed-phases: [] as 0/M phases (three-branch display: empty)" {
        ($step2aBlock -match 'present but empty|\[\].*0/M|0/M.*phase1') | Should Be $true
    }

    It "displays all-phases-complete state without a /cg-work phaseX suggestion" {
        ($step2aBlock -match 'All.*phases completed|all phases complete') | Should Be $true
    }

    It "all-phases-complete message does not suggest bare /cg-work (P2.v1: broken suggestion fixed)" {
        ($step2aBlock -match 'Run `/cg-work` to proceed') | Should Be $false
    }

    It "all-phases-complete message references final quality checks (P2.v1)" {
        ($step2aBlock -match 'Final quality checks ran|re-run the final phase') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Phased plan critic â€” cg-plan-critic.agent.md Phase Structure dimension (P2.15)
# ---------------------------------------------------------------------------

Describe "cg-plan-critic.agent.md - phase structure review dimension" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-plan-critic.agent.md"
    $content = if (Test-Path $agentFile) { Get-Content $agentFile -Raw -Encoding UTF8 } else { "" }

    It "contains a Phase Structure review dimension" {
        ($content -match 'Phase Structure') | Should Be $true
    }

    It "Phase Structure dimension checks phase ordering and completion criteria" {
        ($content -match 'completion criterion|logical.*order|independently testable') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-work.prompt.md description â€” no [plan_file] arg (P2.20)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - description does not advertise plan_file argument" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "description does not advertise [plan_file] (unimplemented argument)" {
        ($content -match '\[plan_file\]') | Should Be $false
    }

    It "description: frontmatter advertises phaseX argument support (P3.14)" {
        ($content -match '\[phaseX\]|Supports.*phaseX') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Pipeline contract tests (P2.25): cg-plan -> cg-work -> cg-resume
# ---------------------------------------------------------------------------

Describe "phased plan pipeline contract: cg-plan emits format cg-work parses" {
    $planPromptFile  = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $workPromptFile  = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $resumePromptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $planContent   = if (Test-Path $planPromptFile)   { Get-Content $planPromptFile   -Raw -Encoding UTF8 } else { "" }
    $workContent   = if (Test-Path $workPromptFile)   { Get-Content $workPromptFile   -Raw -Encoding UTF8 } else { "" }
    $resumeContent = if (Test-Path $resumePromptFile) { Get-Content $resumePromptFile -Raw -Encoding UTF8 } else { "" }

    It "cg-plan phased template uses '## Phase N:' format (matches cg-work parser)" {
        ($planContent -match '## Phase \d+:') | Should Be $true
    }

    It "cg-work parser scans for '## Phase' headers (matches cg-plan output format)" {
        ($workContent -match '## Phase') | Should Be $true
    }

    It "cg-resume /cg-work suggestion uses phase argument format matching cg-work parser" {
        ($resumeContent -match '/cg-work phase\d|/cg-work phase') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-roadmap-view.agent.md â€” existence, frontmatter, read-only enforcement
# ---------------------------------------------------------------------------

Describe "cg-roadmap-view.agent.md - existence" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-roadmap-view.agent.md"

    It "exists in the repository" {
        Test-Path $agentFile | Should Be $true
    }
}

Describe "cg-roadmap-view.agent.md - frontmatter" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-roadmap-view.agent.md"
    $frontmatter = if (Test-Path $agentFile) { Get-Frontmatter -FilePath $agentFile } else { "" }

    It "has user-invocable: false (hidden agent)" {
        ($frontmatter -match 'user-invocable:\s*false') | Should Be $true
    }

    It "has tools: restricted to read only (no write)" {
        ($frontmatter -match "tools:.*'read'") | Should Be $true
    }

    It "does not include write in tools list" {
        $tools = Get-ToolsList -Frontmatter $frontmatter
        ($tools -contains 'write') | Should Be $false
    }

    It "inherits the selected model for fast rendering" {
        ($frontmatter -notmatch '(?m)^\s*model:') | Should Be $true
    }

    It "has a description in frontmatter" {
        ($frontmatter -match 'description:') | Should Be $true
    }
}

Describe "cg-roadmap-view.agent.md - view mode templates" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-roadmap-view.agent.md"
    $content = if (Test-Path $agentFile) { Get-Content $agentFile -Raw -Encoding UTF8 } else { "" }

    It "documents summary view" {
        ($content -match '`summary`') | Should Be $true
    }

    It "documents milestone view" {
        ($content -match '`milestone`') | Should Be $true
    }

    It "documents tasks view" {
        ($content -match '`tasks`') | Should Be $true
    }

    It "documents detail view" {
        ($content -match '`detail`') | Should Be $true
    }

    It "documents status view" {
        ($content -match '`status`') | Should Be $true
    }

    It "documents wip view" {
        ($content -match '`wip`') | Should Be $true
    }

    # P3.1 â€” tasks-milestone view coverage
    It "documents tasks-milestone view" {
        ($content -match '`tasks-milestone`') | Should Be $true
    }

    It "tasks-milestone view includes a concrete markdown template" {
        ($content -match '(?s)### `tasks-milestone`.*```.*\| Feature \| Status \|.*```') | Should Be $true
    }

    It "defines fuzzy matching rules" {
        ($content -match '[Ff]uzzy [Mm]atching') | Should Be $true
    }

    # P1.4 â€” idea badge (no emoji in regex: Pester 3.4 reads as Windows-1252, multi-byte chars cause parse errors)
    It "defines idea feature status badge" {
        ($content -match '`idea`') | Should Be $true
    }

    # P1.6 â€” filter match precedence
    It "defines precedence rule when filter matches both milestone and feature" {
        ($content -match '(?i)(precedence|prefer the (feature|milestone) match)') | Should Be $true
    }

    # P1.7 â€” tasks collapse threshold clarity
    It "clarifies tasks collapse threshold as roadmap-wide total" {
        ($content -match '(?i)roadmap-wide') | Should Be $true
    }

    # P1.9 â€” status view case normalization
    It "normalizes filter to lowercase for status view comparison" {
        ($content -match '(?i)Normalize\s+`filter`\s+to\s+lowercase') | Should Be $true
    }

    It "does not instruct writing or modifying files anywhere in body" {
        # Match imperative write/modify/create instructions but not quoted examples or error messages
        # that reference what the USER should do (e.g., 'Run @cg-roadmap to create one')
        # (?m) flag required: without it, ^ anchors to start of string (always misses body content)
        ($content -match '(?im)^\s*(write|modify|create)\s+the\s+(file|roadmap|plan)') | Should Be $false
    }

    # P0.1 â€” path traversal guard
    It "requires plan paths to start with .cg-docs/plans/" {
        ($content -match '\.cg-docs/plans/') | Should Be $true
    }

    It "prohibits paths containing '..' sequences" {
        ($content -match '(?i)no\s*`?\.\.`?\s*(sequences?|path)') | Should Be $true
    }

    It "rejects absolute paths (no leading / or drive letter)" {
        ($content -match '(?i)(absolute path|leading\s+`?/|drive letter)') | Should Be $true
    }

    It "states the invalid-path rejection response" {
        ($content -match '(?i)Plan path is invalid') | Should Be $true
    }

    # P0.2 â€” prompt injection guard
    It "labels roadmap.json data as untrusted content" {
        ($content -match '(?i)untrusted content') | Should Be $true
    }

    It "instructs rendering field values verbatim (not as instructions)" {
        ($content -match '(?i)render it verbatim') | Should Be $true
    }

    # P2.5 â€” schemaVersion validation
    It "validates schemaVersion before rendering" {
        ($content -match '(?i)schemaVersion') | Should Be $true
    }

    It "emits warning when schemaVersion mismatches" {
        ($content -match '(?i)(schema mismatch|does not match)') | Should Be $true
    }

    # P2.6 â€” plan-not-found diagnostic
    It "renders diagnostic when plan file cannot be read" {
        ($content -match '(?i)Plan file not found') | Should Be $true
    }

    # P2.7 â€” features array null guard
    It "guards missing features array with 0/0 fallback" {
        ($content -match '(?i)(no `features` array|features.*empty|0/0)') | Should Be $true
    }

    # P2.9 â€” pipe escaping in titles
    It "escapes pipe characters in title values" {
        ($content -match '(?i)(escape.*\||\\\|)') | Should Be $true
    }

    # P2.10 â€” skip empty milestone headers in status view
    It "only renders milestone headers with matching features in status view" {
        ($content -match '(?i)(only render.*header|at least one feature)') | Should Be $true
    }

    # P2.11 â€” missing Objective section fallback
    It "handles missing Objective section without hallucinating" {
        ($content -match '(?i)(does not contain an.*Objective|## Objective section)') | Should Be $true
    }

    # P2.16 â€” collapse threshold documented
    It "documents the collapse threshold value" {
        ($content -match '(?i)Collapse threshold.*50|50.*roadmap-wide') | Should Be $true
    }

    # P3.5 â€” description field in detail view
    It "renders description field in detail view template" {
        ($content -match '(?i)\*\*Description\*\*') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-roadmap-view.prompt.md â€” existence, no tool restriction, flag documentation
# ---------------------------------------------------------------------------

Describe "cg-roadmap-view.prompt.md - existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-roadmap-view.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }
}

Describe "cg-roadmap-view.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-roadmap-view.prompt.md"
    $frontmatter = if (Test-Path $promptFile) { Get-Frontmatter -FilePath $promptFile } else { "" }

    It "does not have a tools: key (orchestrating prompts need unrestricted access)" {
        ($frontmatter -notmatch 'tools:') | Should Be $true
    }

    It "has a description in frontmatter" {
        ($frontmatter -match 'description:') | Should Be $true
    }
}

Describe "cg-roadmap-view.prompt.md - dispatches agent and documents flags" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-roadmap-view.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "dispatches @cg-roadmap-view agent" {
        ($content -match '@cg-roadmap-view') | Should Be $true
    }

    It "documents --milestone flag" {
        ($content -match '\-\-milestone') | Should Be $true
    }

    It "documents --tasks flag" {
        ($content -match '\-\-tasks') | Should Be $true
    }

    It "documents --detail flag" {
        ($content -match '\-\-detail') | Should Be $true
    }

    It "documents --plan flag" {
        ($content -match '\-\-plan') | Should Be $true
    }

    It "documents --status flag" {
        ($content -match '\-\-status') | Should Be $true
    }

    It "documents --wip flag" {
        ($content -match '\-\-wip') | Should Be $true
    }

    It "documents --help flag" {
        ($content -match '\-\-help') | Should Be $true
    }

    # P3.2 â€” --help stop behavior
    It "instructs stop after --help (do not dispatch agent)" {
        ($content -match '(?i)(stop|do not proceed)') | Should Be $true
    }

    # P1.8 â€” --plan guard
    It "guards --plan used without --detail with an error message" {
        ($content -match '(?i)`--plan`\s+requires\s+`--detail`') | Should Be $true
    }

    # P2.8 â€” --detail guard
    It "guards --detail used without a name with an error message" {
        ($content -match '(?i)`--detail`\s+requires\s+a\s+feature\s+name') | Should Be $true
    }

    # P3.4 â€” --status schema note
    It "notes that --status values mirror roadmap.json schema" {
        ($content -match '(?i)mirror.*schema|status.*field.*features') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Integration: cg-resume, cg-brainstorm, cg-plan, cg-strategy dispatch agent
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - renders wip context inline (no agent dispatch)" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    # P1.5: resume renders WIP inline from Step 2d data â€” no @cg-roadmap-view dispatch
    It "does NOT dispatch @cg-roadmap-view for wip in Step 3" {
        # Checks that no @cg-roadmap-view dispatch with view:wip was re-added
        # after P1.5 removal.
        ($content -match '@cg-roadmap-view\s+with\s+`?view:\s*wip') | Should Be $false
    }

    It "instructs inline rendering for in-progress milestones" {
        ($content -match '(?i)(render|inline).*(in-progress|wip)|(in-progress|wip).*(render|inline)') | Should Be $true
    }

    It "references compact WIP table format" {
        ($content -match '(?i)(compact|Work In Progress|WIP)') | Should Be $true
    }
}

Describe "cg-brainstorm.prompt.md - dispatches @cg-roadmap-view in Step 5b" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "references @cg-roadmap-view in Step 5b roadmap registration" {
        ($content -match '@cg-roadmap-view') | Should Be $true
    }

    # P3.7 â€” Step 5c also dispatches @cg-roadmap-view for milestone display (consistent with 5b)
    It "dispatches @cg-roadmap-view in Step 5c for side-idea milestone display" {
        # Step 5c now dispatches @cg-roadmap-view view: summary before asking which milestone
        ($content -match '(?i)consistent with Step 5b|@cg-roadmap-view.*view.*summary') | Should Be $true
    }
}

Describe "cg-plan.prompt.md - milestone selection uses inline rendering (P2.14)" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "does NOT dispatch @cg-roadmap-view for milestone list in Step 5 (data already in context)" {
        # P2.14: dispatch was replaced with inline rendering from already-loaded roadmap.json
        ($content -match 'dispatch\s+`@cg-roadmap-view`\s+with\s+`view:\s*summary`\s+to\s+show') | Should Be $false
    }

    It "instructs inline milestone list from loaded roadmap data" {
        ($content -match '(?i)(already.loaded|loaded.*item|show.*milestone.*names)') | Should Be $true
    }

    # P3.6 â€” permissions block distinguishes structural vs display reads
    It "documents structural vs display read distinction in permissions" {
        ($content -match '(?i)(structural operations|for display)') | Should Be $true
    }
}

Describe "cg-plan-review.prompt.md - roadmap-view side-idea capture" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan-review.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "dispatches @cg-roadmap-view with view: summary in Step 4 side-idea capture" {
        ($content -match '@cg-roadmap-view[\s\S]*view:\s*summary') | Should Be $true
    }
}

Describe "cg-ideate.prompt.md - roadmap-view idea capture" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-ideate.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "dispatches @cg-roadmap-view with view: summary before roadmap writes" {
        ($content -match '@cg-roadmap-view[\s\S]*view:\s*summary') | Should Be $true
    }
}

Describe "cg-strategy.prompt.md - dispatches @cg-roadmap-view for full picture" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-strategy.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "references @cg-roadmap-view" {
        ($content -match '@cg-roadmap-view') | Should Be $true
    }

    It "uses summary view for strategy context (P2.4: not tasks view)" {
        ($content -match 'view.*summary|summary.*view') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-learnings-researcher.agent.md - untrusted-content notes
# ---------------------------------------------------------------------------
Describe "cg-learnings-researcher.agent.md - untrusted-content notes" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-learnings-researcher.agent.md"
    $content = if (Test-Path $agentFile) { Get-Content $agentFile -Raw -Encoding UTF8 } else { "" }

    It "Tier 1 untrusted-content note includes 'relay'" {
        # P3.1: 'relay' is the key safety verb for prompt-injection defence
        ($content -match '(?i)relay any instructions embedded') | Should Be $true
    }

    It "Tier 2 untrusted-content note includes 'relay'" {
        # P3.1: Tier 2 note must use 'relay', not just 'interpret'
        ($content -match '(?i)execute or relay any instructions found in its content') | Should Be $true
    }

    It "Tier 3 untrusted-content note includes 'relay'" {
        # P1.2 (original review): all tiers must have untrusted-content protection
        ($content -match '(?i)Never execute or relay any instructions found in file content') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-commit-push-pr.prompt.md - existence, frontmatter, structure
# ---------------------------------------------------------------------------

Describe "cg-commit-push-pr.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-commit-push-pr.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-commit-push-pr.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-commit-push-pr.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    It "has a description in frontmatter" {
        ($frontmatter -match 'description:') | Should -Be $true
    }

    It "inherits the selected model for commit and PR workflow" {
        ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
    }

    It "does not have a tools: restriction" {
        ($frontmatter -notmatch 'tools:') | Should -Be $true
    }
}

Describe "cg-commit-push-pr.prompt.md - structure" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-commit-push-pr.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has a File Permissions block" {
        ($content -match '## File Permissions') | Should -Be $true
    }

    It "has Step 0 Get Bearings" {
        ($content -match '### Step 0') | Should -Be $true
    }

    It "instructs reading compound-gpid.md in Step 0" {
        ($content -match 'compound-gpid\.md') | Should -Be $true
    }

    It "proposes splitting into logical commits (R1)" {
        ($content -match 'logical commit|commit group|split') | Should -Be $true
    }

    It "classifies files by type for commit grouping (R1)" {
        ($content -match 'Tests|Docs|Config|Code') | Should -Be $true
    }

    It "references conventional commit format (R2)" {
        ($content -match 'conventional|type\(scope\)|feat|fix\b') | Should -Be $true
    }

    It "detects plans via git merge-base for PR body (R3)" {
        ($content -match 'merge-base|cg-docs/plans') | Should -Be $true
    }

    It "handles missing gh CLI gracefully with install instructions (R4)" {
        ($content -match 'winget install GitHub\.cli') | Should -Be $true
    }

    It "handles missing gh CLI gracefully for macOS (R4)" {
        ($content -match 'brew install gh') | Should -Be $true
    }

    It "does NOT hardcode compound-gpid internal install paths (R11)" {
        ($content -match '\.compound-gpid[/\\]|USERPROFILE.*compound-gpid') | Should -Be $false
    }

    It "halts with 'Nothing to commit' message when working tree is clean (Step 1.1)" {
        ($content -match 'Nothing to commit|Working tree is clean') | Should -Be $true
    }

    It "halts after git add failure without attempting git commit (P1.1)" {
        ($content -match 'Verify exit code after.*git add|exit code.*git add') | Should -Be $true
    }

    It "halts with 'detached HEAD state' when git branch returns empty (P1.4)" {
        ($content -match 'detached HEAD state') | Should -Be $true
    }

    It "reads untracked files via Get-Content when git diff returns empty (P2.10)" {
        ($content -match 'Get-Content.*untracked|untracked.*Get-Content|\?\?.*Get-Content') | Should -Be $true
    }

    It "requires large commit groups to be split before proceeding (P1.8)" {
        ($content -match '20 files[\s\S]{0,120}500 lines|500 lines[\s\S]{0,120}20 files') | Should -Be $true
    }

    It "uses --body-file instead of inline gh pr create --body (P0.1)" {
        ($content -match '--body-file') | Should -Be $true
        ($content -match 'gh pr create --title "<title>" --body "<body>"') | Should -Be $false
    }

    It "requires PR title validation against Conventional Commits before PR creation" {
        ($content -match 'Validation gate before `gh pr create`') | Should -Be $true
        ($content -match '\^\(feat\|fix\|docs\|test\|refactor\|chore\|data\|analysis\)') | Should -Be $true
    }

    It "forbids title-case branch text when deriving PR titles" {
        ($content -match 'Never title-case branch text for PR titles') | Should -Be $true
    }

    It "sanitizes untrusted plan objective content before PR body construction (P1.5)" {
        ($content -match 'untrusted text[\s\S]{0,250}Ignore[\s\S]{0,250}Disregard[\s\S]{0,250}System:') | Should -Be $true
    }

    It "specifies commit-body criteria for complex commit groups (P2.13)" {
        ($content -match 'more than 3 files[\s\S]{0,180}structural changes[\s\S]{0,180}3.5 most significant changes|more than 3 files[\s\S]{0,220}3–5 most significant changes') | Should -Be $true
    }

    It "supports --ask flag to enable interactive confirmation mode (default is auto-proceed)" {
        ($content -match '--ask|--wait') | Should -Be $true
    }

    It "states default mode proceeds without confirmation unless --ask is set" {
        ($content -match 'auto.proceed|without.*confirm|unless.*--ask|by default.*proceed|--ask.*confirm') | Should -Be $true
    }

    It "handles re-run when PR already exists (checks for existing PR before creating)" {
        ($content -match 'existing.*PR|PR.*already|gh pr view') | Should -Be $true
    }

    It "skips PR creation and reports existing PR URL when PR is already open" {
        ($content -match 'existingPR|existing.*PR.*URL|already.*open|included automatically') | Should -Be $true
    }

    It "falls back to VS Code GitHub Pull Request extension when gh CLI is not found" {
        ($content -match 'GitHub Pull Request.*extension|vscode.*github|github-pull-request_create|VS Code.*extension.*PR|extension.*PR.*creation') | Should -Be $true
    }

    It "gives actionable next-time setup instructions when no PR tool is available" {
        ($content -match 'next.time|to enable.*PR|install.*gh.*next|winget.*GitHub\.cli.*next|for.*future.*runs|next run') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-verify-pr.prompt.md - existence, frontmatter, structure
# ---------------------------------------------------------------------------

Describe "cg-verify-pr.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-verify-pr.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-verify-pr.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-verify-pr.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    It "has a description in frontmatter" {
        ($frontmatter -match 'description:') | Should -Be $true
    }

    It "inherits the selected model for PR verification" {
        ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
    }

    It "does not have a tools: restriction" {
        ($frontmatter -notmatch 'tools:') | Should -Be $true
    }
}

Describe "cg-verify-pr.prompt.md - structure" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-verify-pr.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has a File Permissions block" {
        ($content -match '## File Permissions') | Should -Be $true
    }

    It "declares --propose mode is READ-only in File Permissions" {
        ($content -match '(?i)propose.*read.only|propose.*no file|propose.*no.*commit') | Should -Be $true
    }

    It "has Step 0 Get Bearings" {
        ($content -match '### Step 0') | Should -Be $true
    }

    It "has Step 0.6 for flag parsing (not Step 0.5 which is reserved for prior-work scan)" {
        ($content -match '### Step 0\.6') | Should -Be $true
    }

    It "documents --propose flag (R6)" {
        ($content -match '\-\-propose') | Should -Be $true
    }

    It "defaults to auto-fix mode (R5)" {
        ($content -match 'auto-fix') | Should -Be $true
    }

    It "classifies lint/type errors as a failure category (R7)" {
        ($content -match 'Lint') | Should -Be $true
    }

    It "classifies test failures (R7)" {
        ($content -match 'Test failure') | Should -Be $true
    }

    It "dispatches @cg-fix-problems for lint/type errors (R7)" {
        ($content -match '@cg-fix-problems') | Should -Be $true
    }

    It "dispatches @cg-testing for test failures (R7)" {
        ($content -match '@cg-testing') | Should -Be $true
    }

    It "dispatches @cg-code-quality for build errors (R7)" {
        ($content -match '@cg-code-quality') | Should -Be $true
    }

    It "enforces 2-round cap via fix(ci): commit count (R8)" {
        ($content -match 'fix\(ci\)') | Should -Be $true
    }

    It "mentions 2 fix rounds as the cap (R8)" {
        ($content -match '2 fix round|2-round|two.round|2 round') | Should -Be $true
    }

    It "mentions --watch flag in the prohibition context (R8/safety)" {
        ($content -match '\-\-watch') | Should -Be $true
    }

    It "explicitly prohibits using --watch to prevent agent session crash (R8/safety)" {
        ($content -match 'Do NOT use.*--watch|NOT.*--watch') | Should -Be $true
    }

    It "warns branch is NOT deployment-ready on platform-specific failure (R9)" {
        ($content -match 'NOT deployment-ready|not deployment') | Should -Be $true
    }

    It "includes run-id extraction via gh run list before gh run view (R7/P2.1)" {
        ($content -match 'gh run list') | Should -Be $true
    }

    It "handles rebase for diverged branches (R10)" {
        ($content -match 'rebase') | Should -Be $true
    }

    It "instructs using force-with-lease not plain --force (R10/safety)" {
        ($content -match 'force-with-lease') | Should -Be $true
    }

    It "enumerates modified files before staging CI fixes and forbids git add dot (P1.9)" {
        ($content -match 'git diff --stat HEAD') | Should -Be $true
        ($content -match 'Do not use `git add \.`|Do NOT use `git add \.`') | Should -Be $true
    }

    It "performs a non-blocking CI status poll after pushing fixes (P1.10)" {
        ($content -match 'non-blocking CI status poll|gh pr checks|statusCheckRollup') | Should -Be $true
    }

    It "does NOT hardcode compound-gpid internal install paths (R11)" {
        ($content -match '\.compound-gpid[/\\]|USERPROFILE.*compound-gpid') | Should -Be $false
    }

    It "halts with 'No open PR found' and suggests /cg-commit-push-pr (Step 1.4)" {
        ($content -match 'No open PR found|Run.*cg-commit-push-pr') | Should -Be $true
    }

    It "halts with 'No CI checks have run yet' when statusCheckRollup is null or empty (P1.3)" {
        ($content -match 'No CI checks have run yet') | Should -Be $true
    }

    It "halts with 'detached HEAD state' when git branch returns empty (P1.4)" {
        ($content -match 'detached HEAD state') | Should -Be $true
    }

    It "skips log fetching with 'No run found' message when gh run list returns empty (P1.6)" {
        ($content -match 'No run found for workflow') | Should -Be $true
    }

    It "treats SKIPPED conclusion as passing (P1.7)" {
        ($content -match 'SKIPPED') | Should -Be $true
    }

    It "treats CANCELLED as non-blocking (P1.7)" {
        ($content -match 'CANCELLED') | Should -Be $true
    }

    It "halts on ACTION_REQUIRED conclusion (P1.7)" {
        ($content -match 'ACTION_REQUIRED') | Should -Be $true
    }

    It "halts on STALE conclusion (P1.7)" {
        ($content -match 'STALE') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Command default behaviors â€” cg-brainstorm.prompt.md
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - auto-branch default" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 1.7 is named 'Branch Setup' (not 'Branch Offer')" {
        ($content -match 'Step 1\.7: Branch Setup') | Should -Be $true
    }

    It "auto-creates branch on default branch without prompting" {
        ($content -match 'automatically create and switch to the feature branch') | Should -Be $true
    }

    It "does NOT show a Yes/No offer on the default branch" {
        ($content -match '1\. \*\*Yes\*\*.*I.ll create the branch now') | Should -Be $false
    }

    It "prompts stay/new when already on a feature branch" {
        ($content -match 'Stay here.*create a new branch|stay.*new.*default.*stay') | Should -Be $true
    }

    It "offers git init when workspace is not a git repo" {
        ($content -match 'git init') | Should -Be $true
    }

    It "documents --no-branch flag to skip branching" {
        ($content -match '\-\-no-branch') | Should -Be $true
    }

    It "determines default branch via git symbolic-ref" {
        ($content -match 'symbolic-ref') | Should -Be $true
    }

    It "File Permissions mention auto-branch (not explicit acceptance)" {
        ($content -match 'automatically create a git branch') | Should -Be $true
    }

    It "Step 1.7 uses git rev-parse --git-dir to detect non-git workspace" {
        ($content -match 'git rev-parse.*--git-dir') | Should -Be $true
    }

    It "Step 1.7 handles detached HEAD state (empty git branch --show-current output)" {
        ($content -match 'detached HEAD') | Should -Be $true
    }

    It "Step 1.7 normalizes branch names (strips special chars, truncates to 60)" {
        ($content -match 'truncate to 60 characters|remove characters in.*~\^') | Should -Be $true
    }

    It "File Permissions include git init carve-out for non-git workspaces" {
        ($content -match 'run.*git init.*Step 1\.7|git init.*non-git workspace') | Should -Be $true
    }

    It "branch-enabled variable is set from --no-branch flag at Step 0" {
        ($content -match 'branch-enabled\s*=\s*false') | Should -Be $true
    }

    It "uncommitted-changes warning fires before auto-create action" {
        $uncommittedPos = $content.IndexOf('uncommitted changes exist: warn first')
        $autoCreatePos  = $content.IndexOf('Automatically create and switch')
        $uncommittedPos | Should BeGreaterThan -1
        $autoCreatePos  | Should BeGreaterThan -1
        $uncommittedPos | Should BeLessThan $autoCreatePos
    }

    It "Thinking Partner mode skip is silently applied in Step 1.7 pre-flight" {
        ($content -match 'Thinking Partner mode.*skip this step silently') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Command default behaviors â€” cg-plan.prompt.md
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - always-phase default" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 0 parses --no-phases flag" {
        ($content -match '\-\-no-phases') | Should -Be $true
    }

    It "Step 3.5 states phases are organized by default (no prompt)" {
        ($content -match 'organized into phases by default') | Should -Be $true
    }

    It "Step 3.5 does NOT contain a Would you like to organize offer" {
        ($content -match 'Would you like to organize this plan into phases') | Should -Be $false
    }

    It "Step 3.5 does NOT contain Deep/Standard/Lightweight scope gating for phases" {
        ($content -match 'Deep.*scope.*I recommend organizing|Standard.*scope.*Would you like') | Should -Be $false
    }

    It "Step 3.5 skips automatically for plans with 2 or fewer steps" {
        ($content -match '2 implementation steps|\u2264 2') | Should -Be $true
    }

    It "phases-default variable is set from --no-phases flag in Step 0" {
        ($content -match '--no-phases.*phases-default|phases-default.*false') | Should -Be $true
    }

    It "Step 3.5 includes a phase-splitting heuristic" {
        ($content -match 'Phase-splitting heuristic|50/50 by count|grouping by concern') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Command default behaviors â€” cg-review.prompt.md
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - autofix default" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents --report-only flag" {
        ($content -match '\-\-report-only') | Should -Be $true
    }

    It "states autofix is ON by default" {
        ($content -match 'autofix is ON|Default.*autofix') | Should -Be $true
    }

    It "tagging instructions are always included (not gated by mode:autofix)" {
        ($content -match 'Always include tagging instructions') | Should -Be $true
    }

    It "notes mode:autofix is now a no-op (backward compatibility)" {
        ($content -match 'No-op.*autofix is now the default|autofix.*No-op') | Should -Be $true
    }

    It "statistical guardrail preserved: never safe_auto stats/welfare/weight" {
        ($content -match 'statistical functions.*welfare.*weight|welfare.*income.*weight') | Should -Be $true
    }

    It "Step 4 default path is autofix (not report-only)" {
        ($content -match 'Default \(autofix mode\)') | Should -Be $true
    }

    It "--report-only path presents findings one at a time" {
        ($content -match 'report-only.*present findings one at a time|If.*report-only.*present findings') | Should -Be $true
    }

    It "--report-only is listed in the recognized arguments warning" {
        ($content -match 'Recognized:.*--report-only') | Should -Be $true
    }

    It "mutual exclusion: --report-only + mode:verify resolves to mode:verify" {
        ($content -match 'ignore.*--report-only') | Should -Be $true
    }

    It "mode flags are parsed at Step 0 before any file reads" {
        ($content -match '(?s)Step 0:.*Parse mode flags') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Command default behaviors â€” cg-compound.prompt.md
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - auto-enrich default" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 0.5 parses --no-enrich flag" {
        ($content -match '\-\-no-enrich') | Should -Be $true
    }

    It "Step 3c wiki dispatch is gated by enrich flag" {
        ($content -match 'enrich = false.*skip this step') | Should -Be $true
    }

    It "enrich variable is set in Step 0.5" {
        ($content -match 'enrich\s*=\s*(true|false)') | Should -Be $true
    }

    It "Step 5 skips entirely when --no-enrich is passed" {
        ($content -match 'enrich = false.*skip this step') | Should -Be $true
    }

    It "enrich defaults to true when --no-enrich is absent" {
        ($content -match 'enrich\s*=\s*true') | Should -Be $true
    }

    It "Step 5 no longer asks Should I add it before enriching context.md" {
        ($content -match 'Should I add it\?') | Should -Be $false
    }

    It "Step 5 writes to context.md directly and reports the addition" {
        ($content -match 'Context enriched:|Append to the bottom') | Should -Be $true
    }

    It "Step 5 uses append-only insertion (never inserts within existing lines)" {
        ($content -match 'never insert within existing lines|Append to the bottom.*matching section') | Should -Be $true
    }

    It "File Permissions reflect auto-enrichment without user approval" {
        ($content -match 'auto-enrichment') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Batch B â€” cg-brain-rebuild.prompt.md
# ---------------------------------------------------------------------------

Describe "cg-brain-rebuild.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brain-rebuild.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-brain-rebuild.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brain-rebuild.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    It "has a description in frontmatter" {
        $frontmatter | Should -Match 'description:'
    }

    It "inherits the selected model without model frontmatter" {
        ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
    }
}

Describe "cg-brain-rebuild.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brain-rebuild.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    It "does not have a tools: key (orchestrating prompt needs unrestricted access)" {
        ($frontmatter -notmatch 'tools:') | Should -Be $true
    }
}

Describe "cg-brain-rebuild.prompt.md - content" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brain-rebuild.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has Step 0 Get Bearings" {
        ($content -match '### Step 0') | Should -Be $true
    }

    It "references cg-index --brain command" {
        ($content -match 'cg-index --brain') | Should -Be $true
    }

    It "references BRAIN.md as an output to verify" {
        ($content -match 'BRAIN\.md') | Should -Be $true
    }

    It "documents the secondary stdout success pattern" {
        ($content -match '\[cg-index\] Brain index written to') | Should -Be $true
    }

    It "uses exit code as primary success signal (not file existence)" {
        ($content -match 'exit code|non-zero') | Should -Be $true
    }

    It "has a When to Use section" {
        ($content -match 'When to Use') | Should -Be $true
    }

    It "includes action when BRAIN.md absent despite successful exit" {
        ($content -match 'absent despite|not found despite') | Should -Be $true
    }

    It "includes error handling guidance for cg-index not on PATH" {
        ($content -match 'not on PATH|cg-index --version') | Should -Be $true
    }

    It "includes /cg-setup recommendation in Step 3 error handling" {
        ($content -match '/cg-setup') | Should -Be $true
    }

    It "includes error handling guidance for missing .cg-docs/ (wrong working directory)" {
        ($content -match '\.cg-docs|project root') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Batch B â€” copilot-instructions.md must include /cg-brain-rebuild
# ---------------------------------------------------------------------------

Describe "copilot-instructions.md - /cg-brain-rebuild in Workflow Entry Points" {
    $instructionsFile = Join-Path $repoRoot ".github\copilot-instructions.md"
    $rawContent = Get-Content $instructionsFile -Raw -Encoding UTF8
    $section = if ($rawContent -match '(?s)(## Workflow Entry Points.*?)(\r?\n## |\z)') { $Matches[1] } else { "" }

    It "references /cg-brain-rebuild in Workflow Entry Points" {
        ($section -match '/cg-brain-rebuild') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Token audit prompt registration and root handling
# ---------------------------------------------------------------------------

Describe "cg-token-audit.prompt.md - command contract" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-token-audit.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }

    It "inherits the selected model without model frontmatter" {
        ($frontmatter -notmatch '(?m)^\s*model:') | Should -Be $true
    }

    It "runs cg-token-audit with explicit project root" {
        ($content -match 'cg-token-audit --root \. --output-dir \.cg-docs/cost --format both --recommendations') | Should -Be $true
    }

    It "explains explicit --root . protects consumer-project audits" {
        ($content -match 'current project|user.?s current') | Should -Be $true
        ($content -match 'not the installed plugin repository') | Should -Be $true
    }

    It "is advisory and does not auto-fix" {
        ($content -match 'advisory') | Should -Be $true
        ($content -match 'Do not auto-fix anything|does not modify') | Should -Be $true
    }

    It "loads the context-loading contract instead of broad context artifacts" {
        ($content -match 'context-loading\.contract\.md') | Should -Be $true
        ($content -match 'Do not read `\.cg-docs/`, `BRAIN\*\.md`, `brain-index\.json`') | Should -Be $true
    }

    It "allows audit-generated reports under cost and token output directories" {
        ($content -match '\.cg-docs/cost/') | Should -Be $true
        ($content -match '\.cg-docs/token/') | Should -Be $true
        ($content -match 'report files under\s+`\.cg-docs/cost/`\s+and `\.cg-docs/token/`') | Should -Be $true
    }
}

Describe "copilot-instructions.md - /cg-token-audit in Workflow Entry Points" {
    $instructionsFile = Join-Path $repoRoot ".github\copilot-instructions.md"
    $rawContent = Get-Content $instructionsFile -Raw -Encoding UTF8
    $section = if ($rawContent -match '(?s)(## Workflow Entry Points.*?)(\r?\n## |\z)') { $Matches[1] } else { "" }

    It "references /cg-token-audit in Workflow Entry Points" {
        ($section -match '/cg-token-audit') | Should -Be $true
    }
}

Describe "docs/reference.md - /cg-token-audit registration" {
    $refFile = Join-Path $repoRoot "docs\reference.md"
    $content = Get-Content $refFile -Raw -Encoding UTF8

    It "docs/reference.md lists /cg-token-audit" {
        ($content -match '/cg-token-audit') | Should -Be $true
    }

    It "docs/reference.md documents --recommendations output" {
        ($content -match '--recommendations') | Should -Be $true
        ($content -match 'token-advice\.md') | Should -Be $true
    }

    It "docs/reference.md documents workflow token baseline artifacts" {
        ($content -match '\.cg-docs/token/TOKEN-BUDGET\.md') | Should -Be $true
        ($content -match '\.cg-docs/token/token-audit\.json') | Should -Be $true
        ($content -match '\.cg-docs/token/context-map\.json') | Should -Be $true
        ($content -match '\.cg-docs/token/workflow-costs\.csv') | Should -Be $true
        ($content -match '\.cg-docs/token/large-context-warnings\.md') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Batch B â€” cg-compound.prompt.md uses --brain not --digest
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - uses cg-index --brain (Batch B)" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 3b references cg-index --brain" {
        ($content -match 'cg-index --brain') | Should -Be $true
    }

    It "Step 3b title references Brain not Digest" {
        ($content -match 'Rebuild Knowledge Brain') | Should -Be $true
    }

    It "does not reference cg-index --digest (legacy flag removed)" {
        ($content -match 'cg-index --digest') | Should -Be $false
    }

    It "File Permissions references cg-index --brain not --digest" {
        ($content -match '--digest') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# Batch B â€” docs/reference.md lists /cg-brain-rebuild; model guide documents governance categories
# ---------------------------------------------------------------------------

Describe "docs/reference.md - /cg-brain-rebuild registration" {
    $refFile = Join-Path $repoRoot "docs\reference.md"
    $content = Get-Content $refFile -Raw -Encoding UTF8

    It "docs/reference.md lists /cg-brain-rebuild" {
        ($content -match '/cg-brain-rebuild') | Should -Be $true
    }
}

Describe "docs/model-guide.md - advisory stage guidance" {
    $guideFile = Join-Path $repoRoot "docs\model-guide.md"
    $content = Get-Content $guideFile -Raw -Encoding UTF8

    It "documents stage guidance and user-controlled inheritance" {
        ($content -match 'Planning') | Should -Be $true
        ($content -match 'Implementation') | Should -Be $true
        ($content -match 'Review') | Should -Be $true
        ($content -match 'Fix triage') | Should -Be $true
        ($content -match 'user decides') | Should -Be $true
        ($content -match 'availability can differ by platform and date') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Batch C â€” Brain integration: --no-brain flag and Consult Brain steps
# ---------------------------------------------------------------------------

Describe "Brain integration - cg-skill-brain-query skill exists" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-brain-query\SKILL.md"

    It "SKILL.md file exists" {
        Test-Path $skillFile | Should -Be $true
    }

    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "has valid name: frontmatter field" {
        ($content -match '(?m)^\s*name:\s*cg-skill-brain-query') | Should -Be $true
    }

    It "has valid description: frontmatter field" {
        ($content -match '(?m)^\s*description:') | Should -Be $true
    }

    It "covers contradiction resolution" {
        ($content -match '(?i)contradiction') | Should -Be $true
    }

    It "covers staleness detection" {
        ($content -match '(?i)stale') | Should -Be $true
    }

    It "does not contain write/modify instructions (read-only)" {
        # Verify the skill explicitly declares itself read-only
        ($content -match '(?i)this skill is read-only') | Should -Be $true
    }

    It "warns against using brain-index.json for navigation" {
        ($content -match 'brain-index\.json') | Should -Be $true
    }

    It "includes deduplication rule for matched sub-files" {
        ($content -match '(?i)dedup') | Should -Be $true
    }
}

Describe "Brain integration - --no-brain flag in all 6 target prompts" {
    $targetPrompts = @(
        "cg-brainstorm.prompt.md",
        "cg-plan.prompt.md",
        "cg-work.prompt.md",
        "cg-review.prompt.md",
        "cg-fix-triage.prompt.md",
        "cg-compound.prompt.md"
    )

    foreach ($promptName in $targetPrompts) {
        $promptFile = Join-Path $repoRoot ".github\prompts\$promptName"
        $content = Get-Content $promptFile -Raw -Encoding UTF8

        It "$promptName contains --no-brain flag" {
            ($content -match '--no-brain') | Should -Be $true
        }

        It "$promptName sets brain-enabled variable" {
            ($content -match 'brain-enabled') | Should -Be $true
        }
    }
}

Describe "Brain integration - Consult Brain step in all 6 target prompts" {
    $targetPrompts = @(
        "cg-brainstorm.prompt.md",
        "cg-plan.prompt.md",
        "cg-work.prompt.md",
        "cg-review.prompt.md",
        "cg-fix-triage.prompt.md",
        "cg-compound.prompt.md"
    )

    foreach ($promptName in $targetPrompts) {
        $promptFile = Join-Path $repoRoot ".github\prompts\$promptName"
        $content = Get-Content $promptFile -Raw -Encoding UTF8

        # Use pattern robust to renumbering â€” does not hardcode step numbers
        It "$promptName has a Consult Brain step" {
            ($content -match '(?i)Consult Brain') | Should -Be $true
        }

        It "$promptName references cg-skill-brain-query in its Consult Brain step" {
            ($content -match 'cg-skill-brain-query') | Should -Be $true
        }

        It "$promptName has brain-enabled = false guard in Consult Brain step" {
            ($content -match 'brain-enabled\s*=\s*false') | Should -Be $true
        }
    }
}

Describe "Brain integration - recognized-argument strings updated" {
    $reviewFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $reviewContent = Get-Content $reviewFile -Raw -Encoding UTF8

    It "cg-review.prompt.md Recognized string includes --no-brain" {
        ($reviewContent -match 'Recognized:.*--no-brain') | Should -Be $true
    }

    $triageFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    $triageContent = Get-Content $triageFile -Raw -Encoding UTF8

    It "cg-fix-triage.prompt.md Recognized string includes --no-brain" {
        ($triageContent -match 'Recognized:.*--no-brain') | Should -Be $true
    }
}

Describe "Brain integration - copilot-instructions.md mentions cg-skill-brain-query" {
    $instructionsFile = Join-Path $repoRoot ".github\copilot-instructions.md"
    $content = Get-Content $instructionsFile -Raw -Encoding UTF8

    It "copilot-instructions.md references cg-skill-brain-query" {
        ($content -match 'cg-skill-brain-query') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P3.4 â€” --no-brain flag parsed in all 4 remaining prompts
# ---------------------------------------------------------------------------

Describe "Brain integration - remaining prompts parse --no-brain flag" {
    It "cg-brainstorm.prompt.md parses --no-brain" {
        $c = Get-Content (Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md") -Raw -Encoding UTF8
        ($c -match '--no-brain') | Should -Be $true
    }

    It "cg-compound.prompt.md parses --no-brain" {
        $c = Get-Content (Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md") -Raw -Encoding UTF8
        ($c -match '--no-brain') | Should -Be $true
    }

    It "cg-plan.prompt.md parses --no-brain" {
        $c = Get-Content (Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md") -Raw -Encoding UTF8
        ($c -match '--no-brain') | Should -Be $true
    }

    It "cg-work.prompt.md parses --no-brain" {
        $c = Get-Content (Join-Path $repoRoot ".github\prompts\cg-work.prompt.md") -Raw -Encoding UTF8
        ($c -match '--no-brain') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Batch D â€” Team Brain push step in cg-compound + Team Brain pull in brain-query
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - Team Brain push step (Step 3d)" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "contains Step 3d: Push to Team Brain" {
        ($content -match '(?im)^###\s+Step 3d') | Should -Be $true
    }

    It "Step 3d comes after Step 3c (wiki update)" {
        $idx3c = $content.IndexOf("Step 3c")
        $idx3d = $content.IndexOf("Step 3d")
        $idx3c | Should -BeGreaterThan -1
        $idx3d | Should -BeGreaterThan $idx3c
    }

    It "Step 3d skips silently when team-brain not configured" {
        ($content -match '(?i)skip.*silently|silently.*skip') | Should -Be $true
    }

    It "Step 3d invokes cg-index --push-entry" {
        ($content -match 'cg-index.*--push-entry|--push-entry') | Should -Be $true
    }
}

Describe "cg-skill-brain-query - Team Brain pull step (Step 2b)" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-brain-query\SKILL.md"
    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "contains Step 2b section for team brain pull" {
        ($content -match '(?im)^###\s+Step 2b') | Should -Be $true
    }

    It "Step 2b comes after Step 2 and before Step 3" {
        $idx2  = $content.IndexOf("### Step 2 ")
        $idx2b = $content.IndexOf("### Step 2b")
        $idx3  = $content.IndexOf("### Step 3 ")
        $idx2  | Should -BeGreaterThan -1
        $idx2b | Should -BeGreaterThan -1
        $idx3  | Should -BeGreaterThan -1
        $idx2b | Should -BeGreaterThan $idx2
        $idx3  | Should -BeGreaterThan $idx2b
    }

    It "Step 2b mentions team-brain configuration" {
        ($content -match 'team-brain') | Should -Be $true
    }

    It "Step 2b includes source attribution" {
        ($content -match 'source-project|source_project|source attribution|from team brain') | Should -Be $true
    }

    It "Step 2b has security note about untrusted pattern_text and block-quote embedding" {
        ($content -match '(?i)security note') | Should -Be $true
        ($content -match '(?i)untrusted|prompt injection') | Should -Be $true
        ($content -match '(?i)block.quote') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Plan: test-correctness-assessment â€” cg-fixbug three-layer protocol
# Steps 1+2: Layer 1 (expected behavior source), Layer 2 (test gap classification),
#             Layer 3 (red-green proof), diagnostic fork, schema fields/sections
# ---------------------------------------------------------------------------

Describe "cg-fixbug.prompt.md - Layer 1: Expected Behavior Source" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes a step requiring expected behavior source before Step 2" {
        ($content -match 'Expected Behavior Source') | Should -Be $true
    }

    It "lists user requirement as a valid source type" {
        ($content -match 'User requirement|user requirement|user-requirement') | Should -Be $true
    }

    It "lists mathematical or statistical definition as a valid source type" {
        ($content -match '[Mm]athematical|[Ss]tatistical definition') | Should -Be $true
    }

    It "lists hand-computed example as a valid source type" {
        ($content -match '[Hh]and.computed') | Should -Be $true
    }

    It "requires agent to ask user when expected behavior cannot be determined" {
        ($content -match 'cannot determine the expected behavior|no source can be identified') | Should -Be $true
    }

    It "blocks proceeding to Step 2 before expected behavior source is declared" {
        ($content -match 'Do NOT proceed to Step 2 until') | Should -Be $true
    }
}

Describe "cg-fixbug.prompt.md - diagnostic fork: existing test evaluation" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "searches for existing tests before writing new ones in Step 2" {
        ($content -match '[Ee]xisting test.*before|[Ee]valuate existing tests|[Pp]re.check.*existing') | Should -Be $true
    }

    It "describes 'codifies bug' scenario (existing test passes on buggy code with same input)" {
        ($content -match 'codifies.*bug|asserts buggy behavior|passes on broken code') | Should -Be $true
    }

    It "distinguishes incomplete test from wrong test" {
        ($content -match '[Ii]ncomplete|different aspect|doesn.t exercise the buggy') | Should -Be $true
    }

    It "defers flawed test repair to Step 4 (not Step 2)" {
        ($content -match '[Rr]epair.*Step 4|[Ss]tep 4.*repair|[Aa]fter fix.*repair') | Should -Be $true
    }

    It "preserves the Step 2 hard stop (confirmed failing)" {
        ($content -match 'confirmed failing') | Should -Be $true
    }
}

Describe "cg-fixbug.prompt.md - Layer 2: Test Gap Classification" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes a Test Gap Classification step" {
        ($content -match 'Test Gap Classification|test gap classification') | Should -Be $true
    }

    It "includes 'missing-test' as a gap category" {
        ($content -match 'missing.test') | Should -Be $true
    }

    It "includes 'circular-test' as a gap category" {
        ($content -match 'circular.test') | Should -Be $true
    }

    It "includes 'wrong-test' as a gap category" {
        ($content -match 'wrong.test') | Should -Be $true
    }

    It "includes 'weak-test' as a gap category" {
        ($content -match 'weak.test') | Should -Be $true
    }

    It "includes 'edge-case-gap' as a gap category" {
        ($content -match 'edge.case.gap') | Should -Be $true
    }

    It "requires the agent to state the classification explicitly" {
        ($content -match 'State explicitly|[Ss]tate.*classification') | Should -Be $true
    }
}

Describe "cg-fixbug.prompt.md - Layer 3: Red-Green Proof" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes a red-green proof sequence in Step 4" {
        ($content -match '[Rr]ed.green proof') | Should -Be $true
    }

    It "requires red phase confirmation (test was failing before fix)" {
        ($content -match '[Rr]ed phase.*confirm|[Rr]ed phase: confirmed') | Should -Be $true
    }

    It "requires green phase confirmation (test passes after fix)" {
        ($content -match '[Gg]reen phase|now passes') | Should -Be $true
    }

    It "requires existing tests to still pass (no regressions)" {
        ($content -match 'existing tests.*pass|0 regressions') | Should -Be $true
    }

    It "requires verifying failure matches reported symptom" {
        ($content -match '[Ff]ailure match|[Ff]ailure correspond') | Should -Be $true
    }

    It "requires repair of wrong/circular/weak tests in Step 4" {
        ($content -match 'wrong.test.*repair|circular.test.*repair|weak.test.*repair|repair.*wrong.test|repair.*circular|repair.*weak') | Should -Be $true
    }

    It "preserves the Step 4 hard stop ('confirmed fixed')" {
        ($content -match 'confirmed fixed') | Should -Be $true
    }
}

Describe "cg-fixbug.prompt.md - Step 5 schema fields and document sections" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "schema template includes red-phase-confirmed field" {
        ($content -match 'red-phase-confirmed') | Should -Be $true
    }

    It "schema template includes expected-behavior-source field" {
        ($content -match 'expected-behavior-source') | Should -Be $true
    }

    It "schema template includes test-gap field" {
        ($content -match 'test-gap') | Should -Be $true
    }

    It "document body template includes Expected Behavior Source section" {
        ($content -match '## Expected Behavior Source') | Should -Be $true
    }

    It "document body template includes Test Gap section" {
        ($content -match '## Test Gap') | Should -Be $true
    }

    It "Schema Rules section documents red-phase-confirmed invariant" {
        ($content -match 'red-phase-confirmed.*must') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Plan: test-correctness-assessment â€” cg-work red-phase gate (Step 3)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Red-phase verification gate" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Red-phase verification in Step 2" {
        ($content -match 'Red-phase verification|Red.phase verification') | Should -Be $true
    }

    It "specifies conditional skip for structural steps" {
        ($content -match 'config files.*skip|skip.*structural|purely structural') | Should -Be $true
    }

    It "requires test to fail before implementation (red phase)" {
        ($content -match 'fail.*before.*implement|test.*before.*touching|before touching the implementation') | Should -Be $true
    }

    It "includes the escape hatch for undetermined baseline" {
        ($content -match 'Could not establish failing baseline') | Should -Be $true
    }

    It "specifies this is NOT a hard stop" {
        ($content -match 'NOT a hard stop|not.*hard stop') | Should -Be $true
    }

    It "preserves the existing Step 2.5 Phase Boundary section heading" {
        ($content -match '### Step 2\.5: Phase Boundary') | Should -Be $true
    }

    It "red-phase gate uses bold inline text (not a ### heading)" {
        # Should NOT have a '### ' heading containing "Red-phase"
        ($content -match '### .*[Rr]ed.phase') | Should -Be $false
    }

    It "skip qualifier applies to all structural categories via a single clause" {
        # The qualifier 'no Pester test file asserting against the modified content' should
        # precede or bracket the category list, not trail only the last item
        ($content -match 'no Pester test file asserting against the modified content') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Phase 2: cg-skill-r-testing reference file (test-integrity.md)
# ---------------------------------------------------------------------------

Describe "cg-skill-r-testing - references/test-integrity.md exists" {
    $refPath = "$PSScriptRoot\..\.github\skills\cg-skill-r-testing\references\test-integrity.md"
    $content  = if (Test-Path $refPath) { Get-Content $refPath -Raw } else { "" }

    It "file exists" {
        Test-Path $refPath | Should -Be $true
    }

    It "contains Expected Behavior Sources section" {
        ($content -match '## Expected Behavior Sources?') | Should -Be $true
    }

    It "contains Red-Green Verification Protocol section" {
        ($content -match '## Red-Green Verification Protocol') | Should -Be $true
    }

    It "contains Test Gap Taxonomy section" {
        ($content -match '## Test Gap Taxonomy') | Should -Be $true
    }

    It "contains Detection Signals section" {
        ($content -match '## Detection Signals') | Should -Be $true
    }

    It "contains When to Apply section" {
        ($content -match '## When to Apply') | Should -Be $true
    }

    It "names all 8 gap categories" {
        $cats = @('missing-test','weak-test','circular-test','wrong-test',
                  'ambiguous-spec','fixture-gap','edge-case-gap','integration-gap')
        foreach ($cat in $cats) {
            ($content -match [regex]::Escape($cat)) | Should -Be $true
        }
    }

    It "describes the 4-step mutation verification sequence" {
        # Must mention writing test before implementation / red phase / green phase
        ($content -match 'red phase|red-phase|write.*test.*before|before.*implement') | Should -Be $true
        ($content -match 'green phase|green-phase|test.*pass.*after') | Should -Be $true
    }
}

Describe "cg-skill-r-testing SKILL.md - references test-integrity.md" {
    $skillPath = "$PSScriptRoot\..\.github\skills\cg-skill-r-testing\SKILL.md"
    $content   = if (Test-Path $skillPath) { Get-Content $skillPath -Raw } else { "" }

    It "SKILL.md cross-references test-integrity.md" {
        ($content -match 'test-integrity\.md') | Should -Be $true
    }
}



# ---------------------------------------------------------------------------
# P2.3 — Layer 2 Pester: 3 missing gap categories in cg-fixbug.prompt.md
# (ambiguous-spec, fixture-gap, integration-gap have no individual assertion
#  in the Layer 2 block that guards the *prompt*; the test-integrity.md loop
#  guards the reference file only)
# ---------------------------------------------------------------------------

Describe "cg-fixbug.prompt.md - Layer 2: additional gap categories" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes 'ambiguous-spec' as a gap category" {
        ($content -match 'ambiguous.spec') | Should -Be $true
    }
    It "includes 'fixture-gap' as a gap category" {
        ($content -match 'fixture.gap') | Should -Be $true
    }
    It "includes 'integration-gap' as a gap category" {
        ($content -match 'integration.gap') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.4 — Layer 1 Pester: 4 source types uncovered in cg-fixbug.prompt.md
# ---------------------------------------------------------------------------

Describe "cg-fixbug.prompt.md - Layer 1: additional source types" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "lists documentation as a valid source type" {
        ($content -match 'Documentation.*roxygen|docstring.*source|roxygen.*source') | Should -Be $true
    }
    It "lists backward-compatibility contract as a valid source type" {
        ($content -match 'backward.compat') | Should -Be $true
    }
    It "lists package convention as a valid source type" {
        ($content -match '[Pp]ackage convention|package-convention') | Should -Be $true
    }
    It "lists external reference as a valid source type" {
        ($content -match '[Ee]xternal reference|external-reference') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.5 — Schema Rules invariants for expected-behavior-source and test-gap
# ---------------------------------------------------------------------------

Describe "cg-fixbug.prompt.md - Schema Rules: expected-behavior-source and test-gap invariants" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Schema Rules section documents expected-behavior-source invariant (must)" {
        ($content -match 'expected-behavior-source.*must') | Should -Be $true
    }
    It "Schema Rules section documents test-gap invariant (must)" {
        ($content -match 'test-gap.*must') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.6 — IndexOf ordering: Step 1.5 must appear before Step 2 (Reproduce)
# ---------------------------------------------------------------------------

Describe "cg-fixbug.prompt.md - Step 1.5 ordering before Step 2" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 1.5 Expected Behavior Source appears before Step 2 Reproduce in document order" {
        $idx15 = $content.IndexOf("### Step 1.5:")
        $idx2  = $content.IndexOf("### Step 2: Reproduce")
        $idx15 | Should -BeGreaterThan -1
        $idx2  | Should -BeGreaterThan -1
        $idx15 | Should -BeLessThan $idx2
    }
}

# ---------------------------------------------------------------------------
# P2.7 — IndexOf ordering: red-phase gate must appear before Step 2.5 Phase Boundary
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Red-phase gate ordering before Phase Boundary" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Red-phase verification appears before Step 2.5 Phase Boundary" {
        $gatePos  = $content.IndexOf("Red-phase verification")
        $boundPos = $content.IndexOf("Step 2.5: Phase Boundary")
        $gatePos  | Should -BeGreaterThan -1
        $boundPos | Should -BeGreaterThan -1
        $gatePos  | Should -BeLessThan $boundPos
    }
}

# ---------------------------------------------------------------------------
# P2.8 — IndexOf ordering: Test Gap Classification must appear after "confirmed failing"
# ---------------------------------------------------------------------------

Describe "cg-fixbug.prompt.md - Test Gap Classification ordering after confirmed failing" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Test Gap Classification appears after 'confirmed failing' hard stop phrase" {
        $hardStopPos = $content.IndexOf("confirmed failing")
        $gapPos      = $content.IndexOf("Test Gap Classification")
        $hardStopPos | Should -BeGreaterThan -1
        $gapPos      | Should -BeGreaterThan -1
        $hardStopPos | Should -BeLessThan $gapPos
    }
}

# ---------------------------------------------------------------------------
# P3.2 — SKILL.md cross-reference: load cg-skill-r-testing/test-integrity.md when...
# ---------------------------------------------------------------------------

Describe "cg-skill-r-testing SKILL.md - test-integrity cross-reference has when-to-load guidance" {
    $skillPath = "$PSScriptRoot\..\.github\skills\cg-skill-r-testing\SKILL.md"
    $content   = if (Test-Path $skillPath) { Get-Content $skillPath -Raw } else { "" }

    It "test-integrity cross-reference mentions 'when' trigger condition" {
        ($content -match '(?i)(Load when|when fixing bugs|when reviewing tests|when.*tautolog)') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# P3.3 — Layer 3: six-point proof gate language tested
# ---------------------------------------------------------------------------

Describe "cg-fixbug.prompt.md - Layer 3: six-point proof gate language" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 4 requires all six proof points before confirmation" {
        ($content -match 'Only after all six|six sub-points') | Should -Be $true
    }
}


# ---------------------------------------------------------------------------
# /cg-fix-triage findings - P1.1-P1.4, P2.16-P2.18, P3.4, P3.6, P3.7
# ---------------------------------------------------------------------------

Describe "cg-fixbug.prompt.md - P1.2 escape hatch for 'test is not failing' response" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has handler for 'test is NOT failing' response at Step 2 HARD STOP" {
        ($content -match 'test is NOT failing|NOT failing') | Should -Be $true
    }

    It "instructs to return to pre-check and revise the test" {
        ($content -match 'Return to the pre-check|revise the test.*new input') | Should -Be $true
    }
}

Describe "cg-fixbug.prompt.md - P1.3 cross-reference pointer in Step 2.5 table" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 2.5 table footer references test-integrity.md for Typical Signal column" {
        ($content -match 'test-integrity\.md.*Test Gap Taxonomy') | Should -Be $true
    }
}

Describe "cg-fixbug.prompt.md - P2.17 source priority order (external-reference before hand-computed)" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "External reference ranks above Hand-computed example in priority order" {
        $extRefIdx      = $content.IndexOf("**External reference**")
        $handComputeIdx = $content.IndexOf("**Hand-computed example**")
        $extRefIdx      | Should -BeGreaterThan -1
        $handComputeIdx | Should -BeGreaterThan -1
        $extRefIdx      | Should -BeLessThan $handComputeIdx
    }
}

Describe "cg-fixbug.prompt.md - P2.18 escape hatch for unavailable test runner in Step 2 pre-check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has escape hatch for CLM restriction or missing test runner" {
        ($content -match 'CLM restriction|missing test runner') | Should -Be $true
    }

    It "escape hatch log message opens with 'Test runner unavailable' phrase" {
        ($content -match 'Test runner unavailable.*skipping.*pre-check') | Should -Be $true
    }

    It "escape hatch directs agent to use Step 1.5 source" {
        ($content -match 'behavior source declared in Step 1\.5') | Should -Be $true
    }
}

Describe "cg-fixbug.prompt.md - P3.4 MANDATORY vs HARD STOP comment" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has a comment distinguishing MANDATORY (agent-enforced) from HARD STOP (user-confirmed)" {
        ($content -match 'MANDATORY.*agent-enforced.*HARD STOP.*user-confirmed') | Should -Be $true
    }
}

Describe "cg-fixbug.prompt.md - P3.7 circular-test subcategory note" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fixbug.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "notes that circular-test is a subcategory of wrong-test" {
        ($content -match 'circular.test.*subcategory.*wrong.test') | Should -Be $true
    }
}

Describe "cg-work.prompt.md - P1.2 narrowed red-phase skip condition" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "skip condition requires no Pester test file asserting against the modified content" {
        ($content -match 'no Pester test file asserting against the modified content|no colocated Pester assertions') | Should -Be $true
    }

    It "skip condition no longer lists bare 'prompt text' as structural" {
        # 'prompt text' followed by comma or space in the structural skip list - must be gone
        ($content -match 'prompt text, documentation') | Should -Be $false
    }
}

Describe "docs/reference.md - P3.6 updated /cg-fixbug entry" {
    $refFile = Join-Path $repoRoot "docs\reference.md"
    $content = Get-Content $refFile -Raw -Encoding UTF8

    It "/cg-fixbug entry references Step 1.5 Expected Behavior Source" {
        ($content -match 'expected-behavior source.*Step 1\.5') | Should -Be $true
    }

    It "/cg-fixbug entry references test-gap classification Step 2.5" {
        ($content -match 'test-gap classification.*Step 2\.5') | Should -Be $true
    }

    It "/cg-fixbug entry references red-green proof" {
        ($content -match 'red-green proof') | Should -Be $true
    }
}

Describe "cg-skill-r-testing/references/test-integrity.md - P2.16 renamed protocol section" {
    $refPath = "$PSScriptRoot\..\.github\skills\cg-skill-r-testing\references\test-integrity.md"
    $content = if (Test-Path $refPath) { Get-Content $refPath -Raw } else { "" }

    It "section is renamed to Red-Green Verification Protocol" {
        ($content -match '## Red-Green Verification Protocol') | Should -Be $true
    }

    It "old 'Mutation Verification Protocol' is NOT a standalone heading" {
        ($content -match '(?m)^## Mutation Verification Protocol') | Should -Be $false
    }

    It "notes the renaming from Mutation Verification Protocol" {
        ($content -match 'Formerly.*Mutation Verification Protocol') | Should -Be $true
    }

    It "six-step protocol: includes symptom-match step (step 3)" {
        ($content -match 'Confirm failure matches symptom') | Should -Be $true
    }

    It "six-step protocol: includes no-regressions step (step 6)" {
        ($content -match 'Confirm no regressions') | Should -Be $true
    }

    It "cross-references /cg-fixbug Step 4 sub-points" {
        ($content -match 'cg-fixbug.*Step 4|Step 4 sub-points') | Should -Be $true
    }

    It "mapping clarifies that step 1 (write test) maps to cg-fixbug Step 2 not Step 4" {
        ($content -match 'step 1.*cg-fixbug Step 2|write the test.*cg-fixbug Step 2') | Should -Be $true
    }
}

Describe "cg-skill-r-testing/references/test-integrity.md - P2.17 source priority order" {
    $refPath = "$PSScriptRoot\..\.github\skills\cg-skill-r-testing\references\test-integrity.md"
    $content = if (Test-Path $refPath) { Get-Content $refPath -Raw } else { "" }

    It "External reference ranks above Hand-computed example in priority table" {
        $extRefIdx      = $content.IndexOf("**External reference**")
        $handComputeIdx = $content.IndexOf("**Hand-computed example**")
        $extRefIdx      | Should -BeGreaterThan -1
        $handComputeIdx | Should -BeGreaterThan -1
        $extRefIdx      | Should -BeLessThan $handComputeIdx
    }
}

Describe "cg-commit-push-pr.prompt.md - remaining push and classification safeguards" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-commit-push-pr.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "classifies only .cg-docs/plans as Plans/Knowledge" {
        ($content -match 'Path starts with `\.cg-docs/plans/`') | Should -Be $true
        ($content -match 'Path starts with `\.cg-docs/brainstorms/`, `\.cg-docs/solutions/`, or `\.cg-docs/reviews/`') | Should -Be $true
    }

    It "requires rejected and non-fast-forward evidence before offering rebase or force-with-lease" {
        ($content -match 'contains both `rejected` and `non-fast-forward`') | Should -Be $true
        ($content -match 'authentication, network, permission, protected-branch, or hook failures') | Should -Be $true
    }

    It "maps recognized branch prefixes to conventional PR title types" {
        ($content -match 'derive from the branch name by mapping prefixes: `feat/`, `fix/`, `docs/`, `test/`, `refactor/`, `chore/`, `data/`, `analysis/`') | Should -Be $true
    }

    It "uses a safe conventional fallback title when validation still fails" {
        ($content -match 'force safe fallback: `chore\(<scope>\): update branch changes`') | Should -Be $true
    }
}

Describe "cg-verify-pr.prompt.md - remaining summary and shell safeguards" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-verify-pr.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "requires the CI summary table columns" {
        ($content -match 'Check Name \| Prior Status \| New Status \| Action Taken') | Should -Be $true
    }

    It "scopes PowerShell-only syntax alternatives for bash/zsh" {
        ($content -match '\$null.*PowerShell syntax') | Should -Be $true
        ($content -match '/dev/null') | Should -Be $true
        ($content -match 'head -n 1') | Should -Be $true
    }
}

Describe "docs/reference.md and team-brain schema - remaining docs coverage" {
    $reference = Get-Content (Join-Path $repoRoot "docs\reference.md") -Raw -Encoding UTF8
    $schema = Get-Content (Join-Path $repoRoot "docs\team-brain-schema.md") -Raw -Encoding UTF8

    It "documents cg-brain-init in shell commands" {
        ($reference -match '\| `cg-brain-init` \| Project root \|') | Should -Be $true
    }

    It "documents private and private-sections fields" {
        ($schema -match '`private`') | Should -Be $true
        ($schema -match '`private-sections`') | Should -Be $true
    }
}

# ===========================================================================
# GitHub Issues integration -- /cg-issues prompt and workflow guards
# (Phase 2 Steps 3-4; Phase 3 Steps 5-8; Phase 4 Step 10)
# ===========================================================================

# ---------------------------------------------------------------------------
# /cg-issues prompt -- structural guards
# ---------------------------------------------------------------------------

Describe "/cg-issues.prompt.md - structural guards" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-issues.prompt.md"

    Context "file must exist" {
        It "cg-issues.prompt.md exists in .github/prompts/" {
            Test-Path $promptFile | Should -Be $true
        }
    }

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (a tools: whitelist strips write access from the orchestrating agent)" {
            ($frontmatter -notmatch 'tools:') | Should -Be $true
        }
    }

    Context "mode: default must be read-only status check" {
        $content = Get-Content $promptFile -Raw -Encoding UTF8

        It "defaults to status mode when no argument is given" {
            ($content -match 'status.*default|default.*status|no argument.*status|argument.*omitted.*status') | Should -Be $true
        }

        It "documents backfill, link, adopt, and setup modes" {
            ($content -match '\bbackfill\b') | Should -Be $true
            ($content -match '\blink\b') | Should -Be $true
            ($content -match '\badopt\b') | Should -Be $true
            ($content -match '\bsetup\b') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# /cg-issues -- pre-flight checks
# ---------------------------------------------------------------------------

Describe "/cg-issues.prompt.md - pre-flight checks" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-issues.prompt.md") -Raw -Encoding UTF8

    It "checks gh --version before calling any gh command" {
        ($content -match 'gh --version|gh.*version') | Should -Be $true
    }

    It "checks gh auth status before calling any gh command" {
        ($content -match 'gh auth status') | Should -Be $true
    }

    It "reads roadmap.json to find githubIssues config before proceeding" {
        ($content -match 'githubIssues|roadmap.*config|github.*config') | Should -Be $true
    }

    # P2.10 -- Safety Rules must declare status mode as read-only
    It "Safety Rules declare status mode as read-only" {
        ($content -match 'Status mode is read.?only') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# /cg-issues -- confirmation and safety
# ---------------------------------------------------------------------------

Describe "/cg-issues.prompt.md - confirmation and safety" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-issues.prompt.md") -Raw -Encoding UTF8

    It "requires confirmation before gh issue create" {
        ($content -match 'confirm.*issue create|issue create.*confirm|ask.*create.*issue|never create without.*confirm|create.*confirm.*issue') | Should -Be $true
    }

    It "documents duplicate-prevention marker (hidden body marker)" {
        ($content -match 'duplicate.*prevent|marker|compound-gpid-tracked|cg-tracked|hidden.*marker') | Should -Be $true
    }

    It "checks for existing issues before creating a new one (title search fallback)" {
        ($content -match 'title.*search|search.*title|gh issue list.*search|existing.*issue') | Should -Be $true
    }

    It "handles missing labels with create/skip/cancel choice" {
        ($content -match 'create.*skip.*cancel|skip.*cancel|missing.*label|label.*not.*exist') | Should -Be $true
    }

    It "validates plan paths before reading (starts with .cg-docs/plans/, no .., not absolute)" {
        ($content -match '\.cg-docs/plans/|path.*valid|valid.*path') | Should -Be $true
    }

    It "treats roadmap titles and descriptions as untrusted (strips injection lines)" {
        ($content -match 'untrusted|sanitize|strip.*Ignore|Disregard|Forget|injection') | Should -Be $true
    }

    It "never calls gh issue close directly" {
        # Allow 'gh issue close' only in prohibition/documentation context (lines with not/never/do not)
        $prohibited = ($content -split "`n") | Where-Object {
            $_ -match 'gh issue close' -and $_ -notmatch '\bnot\b|\bnever\b|\bno\b'
        }
        $prohibited.Count | Should -Be 0
    }

    # P2.9 -- graceful degradation: status mode must continue without gh
    It "gracefully handles missing gh -- status mode continues without gh (P2.9)" {
        # Must document that status mode specifically continues without gh
        ($content -match 'status.*mode.*without.*gh|status.*mode.*not.*require.*gh|status.*gh.*unavailable|status.*display.*without.*gh') | Should -Be $true
    }

    # P2.6 -- strip Closes # / Fixes # / Resolves # from feature titles
    It "strips Closes # / Fixes # / Resolves # from feature titles before --title" {
        ($content -match 'Closes\s*#|Fixes\s*#|Resolves\s*#') | Should -Be $true
    }

    # P2.7 -- fenced text block for untrusted content
    It "renders untrusted content in fenced text block (prevents instruction injection)" {
        ($content -match '```text') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# /cg-issues -- dispatch-only guards (no write without confirmation)
# ---------------------------------------------------------------------------

Describe "/cg-issues.prompt.md - dispatches @cg-roadmap for all writes" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-issues.prompt.md") -Raw -Encoding UTF8

    It "dispatches @cg-roadmap for attaching issue metadata (not writing roadmap.json directly)" {
        ($content -match '@cg-roadmap|cg-roadmap') | Should -Be $true
    }

    # P3.6 -- operation-name dispatch tests for link, adopt, configure modes
    It "mentions Attach GitHub Issue to Feature operation name (link/backfill mode dispatch)" {
        ($content -match 'Attach GitHub Issue to Feature') | Should -Be $true
    }

    It "mentions Adopt GitHub Issue as Work Item operation name (adopt mode dispatch)" {
        ($content -match 'Adopt GitHub Issue as Work Item') | Should -Be $true
    }

    It "mentions Configure GitHub Issues operation name (setup mode dispatch)" {
        ($content -match 'Configure GitHub Issues') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-roadmap.agent.md -- Configure GitHub Issues operation
# ---------------------------------------------------------------------------

Describe "cg-roadmap.agent.md - Configure GitHub Issues labelPrefix validation" {
    $agentContent = Get-Content (Join-Path $repoRoot ".github\agents\cg-roadmap.agent.md") -Raw -Encoding UTF8

    # P3.1 fix -- regex must use valid character class (- at start or end, not mid-range)
    It "labelPrefix validation regex uses a valid character class (no mid-range /-)" {
        # The character class must NOT contain the invalid range /-  (ASCII 47 > 45)
        # Valid forms: [-A-Za-z0-9...] or [...-] but never [...:/-...] mid-class
        ($agentContent -match '\[-A-Za-z0-9|A-Za-z0-9[^]]*-\]') | Should -Be $true
    }

    It "rejects labelPrefix values containing shell-unsafe characters" {
        ($agentContent -match 'shell-unsafe') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# /cg-resume must remain non-mutating (Phase 3 Step 5)
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - non-mutating with github issues" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md") -Raw -Encoding UTF8

    It "does not call gh issue create in cg-resume" {
        ($content -notmatch 'gh issue create') | Should -Be $true
    }

    It "does not dispatch @cg-issues adopt or backfill in cg-resume" {
        ($content -notmatch '@cg-issues.*adopt|@cg-issues.*backfill|cg-issues.*adopt|cg-issues.*backfill') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# /cg-strategy -- GitHub issue handoff after roadmap changes (Phase 3 Step 6)
# ---------------------------------------------------------------------------

Describe "cg-strategy.prompt.md - github issues handoff" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-strategy.prompt.md") -Raw -Encoding UTF8

    It "mentions cg-issues or GitHub Issues handoff after approved roadmap changes" {
        ($content -match 'cg-issues|github.*issues.*handoff|backfill.*issues') | Should -Be $true
    }

    It "does not call gh issue create implicitly during strategy execution" {
        ($content -notmatch 'gh issue create') | Should -Be $true
    }

    It "keeps roadmap writes through @cg-roadmap not direct gh calls" {
        # gh.* must be word-bounded to avoid matching 'through @cg-roadmap'
        ($content -notmatch '\bgh\b.*roadmap|directly.*\bgh\b.*milestone') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# /cg-plan -- asks about issue link for new work items (Phase 3 Step 7)
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - github issues awareness" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md") -Raw -Encoding UTF8

    It "does not call gh issue create without user confirmation" {
        ($content -notmatch 'gh issue create') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# /cg-work -- shows issue context, does not block on missing issue (Phase 3 Step 7)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - github issues awareness" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-work.prompt.md") -Raw -Encoding UTF8

    It "does not call gh issue create without user confirmation" {
        ($content -notmatch 'gh issue create') | Should -Be $true
    }

    It "does not block work when github issues are unavailable or user declines" {
        ($content -match 'decline|skip.*issue|issue.*skip|does not block|gh.*unavailable') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# /cg-commit-push-pr -- Refs/Closes in PR body, no direct issue close (Phase 3 Step 8)
# ---------------------------------------------------------------------------

Describe "cg-commit-push-pr.prompt.md - github issues references" {
    $content = Get-Content (Join-Path $repoRoot ".github\prompts\cg-commit-push-pr.prompt.md") -Raw -Encoding UTF8

    It "uses Refs # for partial or uncertain completion" {
        ($content -match 'Refs #|Refs \#') | Should -Be $true
    }

    It "uses Closes # only with explicit user confirmation" {
        ($content -match 'Closes #|Closes \#') | Should -Be $true
    }

    It "does not call gh issue close directly" {
        # Allow 'gh issue close' only in prohibition/documentation context (lines with not/never/no)
        $prohibited = ($content -split "`n") | Where-Object {
            $_ -match 'gh issue close' -and $_ -notmatch '\bnot\b|\bnever\b|\bno\b'
        }
        $prohibited.Count | Should -Be 0
    }

    It "does not claim full bidirectional sync (out of scope for v1)" {
        # Allow 'bidirectional sync' only in prohibition/documentation context
        $prohibited = ($content -split "`n") | Where-Object {
            $_ -match 'bidirectional.*sync|full.*sync.*issue|auto.*sync' -and $_ -notmatch '\bNo\b|\bnot\b|\bnever\b|\bdo not\b'
        }
        $prohibited.Count | Should -Be 0
    }
}

# ---------------------------------------------------------------------------
# goal-execution.contract.md - shared goal-execution contract (Phase 1)
# ---------------------------------------------------------------------------

Describe "goal-execution.contract.md - shared goal-execution contract" {
    $contractFile = Join-Path $repoRoot ".github\shared\goal-execution.contract.md"
    $contract = if (Test-Path $contractFile) { Get-Content $contractFile -Raw -Encoding UTF8 } else { "" }

    It "shared goal-execution contract exists" {
        Test-Path $contractFile | Should -Be $true
    }

    It "defines Completion Contract section" {
        ($contract -match 'Completion Contract') | Should -Be $true
    }

    It "defines Verification Surface section" {
        ($contract -match 'Verification Surface') | Should -Be $true
    }

    It "defines deviate:ask policy" {
        ($contract -match 'deviate:ask') | Should -Be $true
    }

    It "defines deviate:auto policy" {
        ($contract -match 'deviate:auto') | Should -Be $true
    }

    It "defines deviate:strict policy" {
        ($contract -match 'deviate:strict') | Should -Be $true
    }

    It "defines deviate:autonomous alias" {
        ($contract -match 'deviate:autonomous') | Should -Be $true
    }

    It "defines deviation-policy stored value" {
        ($contract -match 'deviation-policy') | Should -Be $true
    }

    It "defines autonomous stored value (auto -> autonomous mapping)" {
        ($contract -match '\bautonomous\b') | Should -Be $true
    }

    It "defines Execution Report section" {
        ($contract -match 'Execution Report') | Should -Be $true
    }

    It "defines work-reports path" {
        ($contract -match '\.cg-docs[/\\]work-reports') | Should -Be $true
    }

    It "defines strict evidence gate" {
        ($contract -match 'strict evidence gate') | Should -Be $true
    }

    It "requires header-driven table parsing" {
        ($contract -match 'header-driven') | Should -Be $true
    }

    It "documents optional Phase column in verification tables" {
        ($contract -match '\bPhase\b') | Should -Be $true
    }

    It "defines Authority Precedence section" {
        ($contract -match 'Authority Precedence') | Should -Be $true
    }

    It "defines Legacy Plan Compatibility section or term" {
        ($contract -match 'Legacy Plan Compatibility|legacy plan') | Should -Be $true
    }

    It "defines Report Resume behavior" {
        ($contract -match 'Report Resume|resume section|blocked.*resume') | Should -Be $true
    }

    It "documents both non-phased and phased table variants" {
        # Non-phased: ID | Evidence Required | Command/Artifact | Required
        ($contract -match 'Evidence Required.*Command/Artifact.*Required') | Should -Be $true
        # Phased: ID | Phase | Evidence Required | Command/Artifact | Required
        ($contract -match 'Phase.*Evidence Required') | Should -Be $true
    }

    It "documents same-day collision suffix behavior" {
        ($contract -match '-2|-3|suffix|collision') | Should -Be $true
    }

    It "defines Blocked-Stop Conditions section" {
        ($contract -match 'Blocked.Stop Condition') | Should -Be $true
    }
}

Describe "goal-execution.contract.md - prompt hooks" {
    $planFile  = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $workFile  = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $planContent = if (Test-Path $planFile) { Get-Content $planFile -Raw -Encoding UTF8 } else { "" }
    $workContent = if (Test-Path $workFile) { Get-Content $workFile -Raw -Encoding UTF8 } else { "" }

    It "cg-plan references goal-execution.contract.md" {
        ($planContent -match 'goal-execution\.contract\.md') | Should -Be $true
    }

    It "cg-work references goal-execution.contract.md" {
        ($workContent -match 'goal-execution\.contract\.md') | Should -Be $true
    }

    It "cg-plan documents deviate:ask argument" {
        ($planContent -match 'deviate:ask') | Should -Be $true
    }

    It "cg-plan documents deviate:auto argument" {
        ($planContent -match 'deviate:auto') | Should -Be $true
    }

    It "cg-plan documents deviate:strict argument" {
        ($planContent -match 'deviate:strict') | Should -Be $true
    }

    It "cg-plan stores autonomous for deviate:auto" {
        ($planContent -match 'autonomous') | Should -Be $true
    }

    It "cg-plan documents deviation-policy frontmatter field" {
        ($planContent -match 'deviation-policy') | Should -Be $true
    }

    It "cg-plan previews contract before saving plan (approval gate)" {
        ($planContent -match 'preview.*contract|contract.*preview|approval.*contract|before.*sav') | Should -Be $true
    }

    It "cg-work documents deviate: override parsing" {
        ($workContent -match 'deviate:') | Should -Be $true
    }

    It "cg-work references plan deviation-policy fallback" {
        ($workContent -match 'deviation-policy') | Should -Be $true
    }

    It "cg-work documents legacy plan compatibility halt" {
        ($workContent -match 'legacy|Legacy|## Completion Contract') | Should -Be $true
    }

    It "cg-work documents execution report creation" {
        ($workContent -match 'execution.report|work-reports') | Should -Be $true
    }

    It "cg-work documents evidence gate before completed-phases write" {
        ($workContent -match 'evidence.*gate|evidence.*complet|verification.*phase') | Should -Be $true
    }

    It "cg-work documents same-day collision suffix" {
        ($workContent -match 'collision|append.*-2|-2.*-3') | Should -Be $true
    }

    It "cg-work documents report identity via execution-report pointer" {
        ($workContent -match 'execution-report.*pointer|pointer.*execution.report') | Should -Be $true
    }
}

Describe "goal-execution.contract.md - journey and compatibility fixtures" {
    $planFile  = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $workFile  = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $planContent = if (Test-Path $planFile) { Get-Content $planFile -Raw -Encoding UTF8 } else { "" }
    $workContent = if (Test-Path $workFile) { Get-Content $workFile -Raw -Encoding UTF8 } else { "" }

    It "cg-plan invalid deviate: value warns and falls back to ask" {
        ($planContent -match 'warn.*fall back|invalid.*deviate|fall back.*ask') | Should -Be $true
    }

    It "cg-plan duplicate deviate: value warns and last valid wins" {
        ($planContent -match 'duplicate.*deviate|last valid|last.*wins') | Should -Be $true
    }

    It "cg-work invalid deviate: override warns and uses plan policy" {
        ($workContent -match 'warn.*plan policy|invalid.*deviate.*warn|falls back.*plan') | Should -Be $true
    }

    It "cg-work duplicate deviate: override warns and last valid wins" {
        ($workContent -match 'duplicate.*deviate|last valid') | Should -Be $true
    }

    It "cg-work accepted exception requires explicit rationale" {
        ($workContent -match 'accepted.exception|exception.*rationale') | Should -Be $true
    }

    It "cg-work missing evidence blocks phase/plan/roadmap completion" {
        ($workContent -match 'missing.*evidence|evidence.*block|block.*complet') | Should -Be $true
    }

    It "cg-work contract text cannot override file permissions or safety rules" {
        ($workContent -match 'Authority Precedence|authority precedence|contract.*subordinate|plan contract.*data|under file permissions') | Should -Be $true
    }

    It "cg-work blocked plan appends resume section rather than overwriting" {
        ($workContent -match 'resume section|append.*section|blocked.*resume') | Should -Be $true
    }
}

Describe "active-state handoff contract - compact resume records" {
    $contractFile = Join-Path $repoRoot ".github\shared\active-state.contract.md"
    $workFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $resumeFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $diagnoseFile = Join-Path $repoRoot ".github\prompts\cg-diagnose.prompt.md"
    $templateFile = Join-Path $repoRoot ".github\prompts\resume-templates.md"
    $docsReference = Join-Path $repoRoot "docs\reference.md"
    $docsWorkflow = Join-Path $repoRoot "docs\workflow.md"

    $contract = if (Test-Path $contractFile) { Get-Content $contractFile -Raw -Encoding UTF8 } else { "" }
    $workContent = if (Test-Path $workFile) { Get-Content $workFile -Raw -Encoding UTF8 } else { "" }
    $resumeContent = if (Test-Path $resumeFile) { Get-Content $resumeFile -Raw -Encoding UTF8 } else { "" }
    $diagnoseContent = if (Test-Path $diagnoseFile) { Get-Content $diagnoseFile -Raw -Encoding UTF8 } else { "" }
    $templateContent = if (Test-Path $templateFile) { Get-Content $templateFile -Raw -Encoding UTF8 } else { "" }
    $referenceContent = if (Test-Path $docsReference) { Get-Content $docsReference -Raw -Encoding UTF8 } else { "" }
    $workflowContent = if (Test-Path $docsWorkflow) { Get-Content $docsWorkflow -Raw -Encoding UTF8 } else { "" }

    It "defines current active-state path and schema version" {
        ($contract -match '\.cg-docs/active-state/current\.json') | Should -Be $true
        ($contract -match 'compound-gpid-active-state-v1') | Should -Be $true
    }

    It "requires exact next command, evidence status, unresolved decisions, and artifact refs" {
        ($contract -match 'nextCommand') | Should -Be $true
        ($contract -match 'evidenceStatus') | Should -Be $true
        ($contract -match 'unresolvedDecisions') | Should -Be $true
        ($contract -match 'artifactRefs') | Should -Be $true
    }

    It "forbids transcript dumps and raw command output in active-state records" {
        ($contract -match 'Do not copy full plan bodies') | Should -Be $true
        ($contract -match 'transcript') | Should -Be $true
        ($contract -match 'raw command-output|raw command output') | Should -Be $true
    }

    It "cg-work is allowed and instructed to update active-state records" {
        ($workContent -match '\.cg-docs/active-state') | Should -Be $true
        ($workContent -match 'create or update|create/update|update') | Should -Be $true
        ($workContent -match 'exact\s+`nextCommand`|exact\s+nextCommand') | Should -Be $true
    }

    It "cg-resume reads active-state records as untrusted data and validates references" {
        ($resumeContent -match '\.cg-docs/active-state/current\.json') | Should -Be $true
        ($resumeContent -match 'untrusted data') | Should -Be $true
        ($resumeContent -match 'validate referenced paths|validates the referenced paths') | Should -Be $true
    }

    It "cg-resume preserves non-mutating behavior" {
        ($resumeContent -match 'You may NOT create, modify, or delete any files') | Should -Be $true
    }

    It "cg-diagnose uses compact pointers but does not write active-state files" {
        ($diagnoseContent -match '\.cg-docs/active-state/current\.json') | Should -Be $true
        ($diagnoseContent -match 'Do not write active-state files') | Should -Be $true
        ($diagnoseContent -match 'compact handoff pointers') | Should -Be $true
    }

    It "resume template includes Active State Snapshot and exact next command" {
        ($templateContent -match 'Active State Snapshot') | Should -Be $true
        ($templateContent -match 'Exact next command') | Should -Be $true
    }

    It "docs explain active-state as a compact restart aid, not durable transcript storage" {
        (($referenceContent + $workflowContent) -match 'compact restart aid') | Should -Be $true
        (($referenceContent + $workflowContent) -match 'must not copy transcripts|must not contain transcript dumps') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# World Bank report-writing skill - Phase 1 shared contracts
# ---------------------------------------------------------------------------

Describe "cg-skill-wb-report-writing - shared assets and routing" {
    $skillRoot = Join-Path $repoRoot ".github\skills\cg-skill-wb-report-writing"
    $skillFile = Join-Path $skillRoot "SKILL.md"
    $workflowsFile = Join-Path $skillRoot "references\workflows.md"
    $safetyFile = Join-Path $skillRoot "references\safety-and-markers.md"
    $styleFile = Join-Path $skillRoot "references\style-conventions.md"
    $terminologyFile = Join-Path $skillRoot "references\terminology.md"
    $qualityFile = Join-Path $skillRoot "references\quality-review-checklist.md"

    $skillContent = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }
    $workflowsContent = if (Test-Path $workflowsFile) { Get-Content $workflowsFile -Raw -Encoding UTF8 } else { "" }

    It "includes the canonical skill root and shared reference files" {
        (Test-Path $skillRoot) | Should -Be $true
        (Test-Path $skillFile) | Should -Be $true
        (Test-Path $workflowsFile) | Should -Be $true
        (Test-Path $safetyFile) | Should -Be $true
        (Test-Path $styleFile) | Should -Be $true
        (Test-Path $terminologyFile) | Should -Be $true
        (Test-Path $qualityFile) | Should -Be $true
    }

    It "keeps SKILL.md as a thin router (<=120 lines when practical)" {
        if (Test-Path $skillFile) {
            (Get-Content $skillFile -Encoding UTF8).Count | Should -BeLessOrEqual 120
        } else {
            $false | Should -Be $true
        }
    }

    It "covers all seven operations in trigger/routing language" {
        ($skillContent -match '(?i)draft') | Should -Be $true
        ($skillContent -match '(?i)expand') | Should -Be $true
        ($skillContent -match '(?i)revise') | Should -Be $true
        ($skillContent -match '(?i)summar') | Should -Be $true
        ($skillContent -match '(?i)adapt') | Should -Be $true
        ($skillContent -match '(?i)quality review') | Should -Be $true
        ($skillContent -match '(?i)end-to-end|end to end') | Should -Be $true
    }

    It "includes all eight document types" {
        ($skillContent -match '(?i)policy-research-working-paper') | Should -Be $true
        ($skillContent -match '(?i)\(PRWP\)') | Should -Be $true
        ($skillContent -match '(?i)policy brief') | Should -Be $true
        ($skillContent -match '(?i)executive summary') | Should -Be $true
        ($skillContent -match '(?i)flagship report section') | Should -Be $true
        ($skillContent -match '(?i)country or regional narrative') | Should -Be $true
        ($skillContent -match '(?i)technical methodology') | Should -Be $true
        ($skillContent -match '(?i)internal memo') | Should -Be $true
        ($skillContent -match '(?i)data blog') | Should -Be $true
    }

    It "requires source-pack preflight and missing-input blocking for unready types" {
        ($skillContent -match '(?i)source pack') | Should -Be $true
        ($skillContent -match '(?i)2-3 approved exemplars') | Should -Be $true
        ($skillContent -match '(?i)missing-input list') | Should -Be $true
        ($workflowsContent -match '(?i)intended audience') | Should -Be $true
        ($workflowsContent -match '(?i)required terminology') | Should -Be $true
        ($workflowsContent -match '(?i)required disclaimers') | Should -Be $true
    }

    It "makes phase-appropriate routing explicit when type-specific references are not yet present" {
        ($skillContent -match '(?i)continue using shared references in this phase') | Should -Be $true
        ($skillContent -match '(?i)type-specific.*child plans') | Should -Be $true
        ($workflowsContent -match '(?i)Validator-enforced checks in this phase') | Should -Be $true
        ($workflowsContent -match '(?i)Manual or child-plan checks') | Should -Be $true
    }

    It "states English/basic qmd scope and explicit near-miss boundaries" {
        ($skillContent -match '(?i)English') | Should -Be $true
        ($skillContent -match '(?i)basic \.qmd structure or prose only') | Should -Be $true
        ($skillContent -match '(?i)non-English output requests') | Should -Be $true
        ($skillContent -match '(?i)unsupported full Quarto code execution or data binding workflows') | Should -Be $true
    }
}

Describe "cg-skill-wb-report-writing - guardrails and marker grammar" {
    $safetyFile = Join-Path $repoRoot ".github\skills\cg-skill-wb-report-writing\references\safety-and-markers.md"
    $styleFile = Join-Path $repoRoot ".github\skills\cg-skill-wb-report-writing\references\style-conventions.md"
    $terminologyFile = Join-Path $repoRoot ".github\skills\cg-skill-wb-report-writing\references\terminology.md"

    $safetyContent = if (Test-Path $safetyFile) { Get-Content $safetyFile -Raw -Encoding UTF8 } else { "" }
    $styleContent = if (Test-Path $styleFile) { Get-Content $styleFile -Raw -Encoding UTF8 } else { "" }
    $terminologyContent = if (Test-Path $terminologyFile) { Get-Content $terminologyFile -Raw -Encoding UTF8 } else { "" }

    It "defines exact visible and hidden marker forms" {
        ($safetyContent -match '\[VERIFY:') | Should -Be $true
        ($safetyContent -match '\[SOURCE NEEDED:') | Should -Be $true
        ($safetyContent -match '\[INSTITUTIONAL POSITION:') | Should -Be $true
        ($safetyContent -match '\[PRELIMINARY:') | Should -Be $true
        ($safetyContent -match '\[UNPUBLISHED: DO NOT CIRCULATE\]') | Should -Be $true
        ($safetyContent -match '<!-- AUTHOR NOTE:') | Should -Be $true
    }

    It "covers institutional-position, unpublished-data, country-sensitivity, and fabrication guardrails" {
        ($safetyContent -match '(?i)institutional position') | Should -Be $true
        ($safetyContent -match '(?i)unpublished') | Should -Be $true
        ($safetyContent -match '(?i)country-sensitive guardrail') | Should -Be $true
        ($safetyContent -match '(?i)fabrication guardrail') | Should -Be $true
        ($safetyContent -match '(?i)never invent') | Should -Be $true
    }

    It "requires marker carry-forward behavior for summarization and conversion" {
        ($safetyContent -match '(?i)summar') | Should -Be $true
        ($safetyContent -match '(?i)document conversion') | Should -Be $true
        ($safetyContent -match '(?i)carry forward') | Should -Be $true
    }

    It "documents style authority source and retrieval/version note" {
        ($styleContent -match '(?i)WBG Publications Editorial Style Guide') | Should -Be $true
        ($styleContent -match '(?i)worldbank\.org') | Should -Be $true
        ($styleContent -match '(?i)retrieved|version') | Should -Be $true
    }

    It "keeps terminology explicitly approved or unresolved (no inferred approvals)" {
        ($terminologyContent -match '(?i)approved') | Should -Be $true
        ($terminologyContent -match '(?i)unresolved') | Should -Be $true
        ($terminologyContent -match '(?i)do not infer|do not guess') | Should -Be $true
        ($terminologyContent -match '(?i)not-required') | Should -Be $false
    }
}
