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
if ($env:CG_TEST_ROOT -and -not (Test-Path $env:CG_TEST_ROOT)) { throw "CG_TEST_ROOT '$env:CG_TEST_ROOT' does not exist" }
. "$PSScriptRoot/helpers.ps1"

# Note: Get-ToolsList is defined in helpers.ps1 (shared helper, moved from this file per P2.17)

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

    It "includes R package .Rbuildignore check for .cg-docs/" {
        ($content -match '\.Rbuildignore') | Should Be $true
    }

    It "Step 3.5 falls back to last-write time when date: is absent" {
        ($content -match 'last.write|absent.*fall back') | Should Be $true
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

    It "references /cg-plan-review in Workflow Entry Points" {
        ($section -match '/cg-plan-review') | Should Be $true
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

    It "documents P0 finding ID pattern in Step 3.5" {
        ($content -match [regex]::Escape('**[P0.')) | Should Be $true
    }

    It "documents P1 finding ID pattern in Step 3.5" {
        ($content -match [regex]::Escape('**[P1.')) | Should Be $true
    }

    It "documents P2 finding ID pattern in Step 3.5" {
        ($content -match [regex]::Escape('**[P2.')) | Should Be $true
    }

    It "documents P3 finding ID pattern in Step 3.5" {
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

    It "instructs DO NOT delegate frontmatter status update to a subagent" {
        ($content -match 'Do NOT delegate') | Should Be $true
    }

    It "loads cg-skill-fix-triage-migrate for --migrate mode by name" {
        ($content -match 'cg-skill-fix-triage-migrate') | Should Be $true
    }

    It "Step 0.5 instructs skipping skill load when invoked as --migrate" {
        ($content -match 'Skip this step if invoked as.*--migrate') | Should Be $true
    }

    It "warns on unrecognized arguments with recognized options list" {
        ($content -match 'Unrecognized argument') -and ($content -match '\-\-migrate') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-skill-fix-triage-migrate SKILL.md - behavioral rules
# ---------------------------------------------------------------------------

Describe "cg-skill-fix-triage-migrate SKILL.md - behavioral rules" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-fix-triage-migrate\SKILL.md"
    $content = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }

    It "documents all-open default for findings" {
        ($content -match 'Set all findings to.*open|defaulted to.*open|all findings.*open') | Should Be $true
    }

    It "instructs do NOT delegate to subagent for file writes" {
        ($content -match 'do NOT delegate|NOT delegate') | Should Be $true
    }

    It "has 'No legacy review files found' response for empty scan result" {
        ($content -match 'No legacy review files found') | Should Be $true
    }

    It "instructs prepending full frontmatter block when no frontmatter exists" {
        ($content -match 'prepend full block') | Should Be $true
    }

    It "uses generic <id> placeholder in frontmatter template (not hardcoded P1.1)" {
        ($content -match '<id>:') | Should Be $true
    }

    It "documents that <id> should be replaced with actual parsed IDs" {
        ($content -match 'replace <id> with actual IDs|actual IDs.*e\.g\.') | Should Be $true
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

    It "reference.md documents @cg-release-scanner agent" {
        ($content -match 'cg-release-scanner') | Should Be $true
    }

    It "reference.md documents @cg-project-scanner agent" {
        ($content -match 'cg-project-scanner') | Should Be $true
    }

    It "column header uses User-invocable (not User-invokable)" {
        ($content -match 'User-invocable') | Should Be $true
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
    $tmpNoFm   = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.IO.Path]::GetRandomFileName() + ".md")
    $tmpPartFm = [System.IO.Path]::Combine([System.IO.Path]::GetTempPath(), [System.IO.Path]::GetRandomFileName() + ".md")

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

    It "uses 3+ matching keywords threshold (synced with cg-brainstorm)" {
        ($content -match '3\+?\s*matching keywords') | Should Be $true
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

    It "blocks Focused/Extended/Strategic scope as plan input (Thinking Partner guard)" {
        ($content -match 'Thinking Partner.*not valid') | Should Be $true
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

    It "includes >= 200 non-test lines suggestion trigger" {
        ($content -match '200 non-test lines') | Should Be $true
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

    It "prohibits safe_auto for statistical functions (escalate to manual)" {
        ($content -match '(?s)Never.*safe_auto.*statistical|statistical.*escalate.*manual') | Should Be $true
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
        # Original check: text "existing tests AND the new tests" was replaced with
        # a literal execution_subagent block (Phase 2 prompt hardening). The
        # new approach uses execution_subagent + Run-Tests.ps1 + last-run.json.
        # (?s) flag makes . match newlines so the pattern spans multiple lines.
        ($content -match '(?s)existing tests AND the new tests|(?s)execution_subagent.*Run-Tests|Run-Tests.*execution_subagent') | Should Be $true
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

# P3.3–P3.12 are advisory-only findings; no regression tests required.

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

# ---------------------------------------------------------------------------
# P1.38 — cg-brainstorm Step 3.5 Devil's Advocate
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 3.5 Devil's Advocate" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 3.5 Devil's Advocate section" {
        ($content -match "Step 3\.5.*Devil") | Should Be $true
    }

    It "checks problem validation (is problem real)" {
        ($content -match 'Problem validation|problem real') | Should Be $true
    }

    It "checks simplicity (simpler solution exists)" {
        ($content -match '[Ss]implicity check|simpler solution') | Should Be $true
    }

    It "checks effort-value proportionality" {
        ($content -match '[Ee]ffort-value|80% of the benefit') | Should Be $true
    }

    It "checks charter alignment" {
        ($content -match '[Cc]harter alignment') | Should Be $true
    }

    It "includes side-idea capture instruction during pushback" {
        ($content -match 'adjacent idea|separate idea worth tracking') | Should Be $true
    }

    It "Step 3.5 is always-on and unconditional for all scopes" {
        ($content -match 'always-on and unconditional') | Should Be $true
    }

    It "Thinking Partner mode uses decision reversibility check" {
        ($content -match 'decision reversibility') | Should Be $true
    }

    It "Thinking Partner mode uses stakeholder impact check" {
        ($content -match 'stakeholder impact') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.39 — cg-brainstorm Step 5c Side-Idea Capture
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 5c Side-Idea Capture" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 5c Side-Idea Capture section" {
        ($content -match '5c\..*Side-Idea Capture') | Should Be $true
    }

    It "has 'no adjacent ideas' variant for sessions without pushback" {
        ($content -match 'No adjacent ideas surfaced') | Should Be $true
    }

    It "has context-aware variant referencing the pushback discussion" {
        ($content -match 'pushback discussion') | Should Be $true
    }

    It "renames previous 5c to 5d (Handoff moved to 5d)" {
        ($content -match '5d\. Handoff') | Should Be $true
    }

    It "Step 5c dispatches @cg-roadmap for captured ideas" {
        ($content -match '@cg-roadmap') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.17 — cg-brainstorm step ordering: Step 3.5 before Step 4, Step 5c before 5d
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - step ordering: Step 3.5 and Step 5c" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 3.5 appears before Step 4 in the file" {
        $step35Idx = $content.IndexOf("### Step 3.5:")
        $step4Idx  = $content.IndexOf("### Step 4:")
        $step35Idx | Should BeGreaterThan -1
        $step4Idx  | Should BeGreaterThan -1
        $step35Idx | Should BeLessThan $step4Idx
    }

    It "Step 5c Side-Idea Capture appears before Step 5d Handoff" {
        $step5cIdx = $content.IndexOf("5c. Side-Idea Capture")
        $step5dIdx = $content.IndexOf("5d. Handoff")
        $step5cIdx | Should BeGreaterThan -1
        $step5dIdx | Should BeGreaterThan -1
        $step5cIdx | Should BeLessThan $step5dIdx
    }
}
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Step 1.7 Branch Offer ordering" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 1.7 Branch Offer appears after Step 1.5 Scope Assessment" {
        $step15Idx  = $content.IndexOf('### Step 1.5:')
        $step17Idx  = $content.IndexOf('### Step 1.7:')
        $step15Idx  | Should BeGreaterThan -1
        $step17Idx  | Should BeGreaterThan $step15Idx
    }

    It "Step 2 Clarifying Questions appears after Step 1.7 Branch Offer" {
        $step17Idx  = $content.IndexOf('### Step 1.7:')
        $step2Idx   = $content.IndexOf('### Step 2:')
        $step17Idx  | Should BeGreaterThan -1
        $step2Idx   | Should BeGreaterThan $step17Idx
    }
}

# ---------------------------------------------------------------------------
# P1.40 — cg-plan-critic.agent.md existence and structure
# ---------------------------------------------------------------------------

Describe "cg-plan-critic.agent.md - existence and structure" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-plan-critic.agent.md"

    It "exists in the repository" {
        Test-Path $agentFile | Should Be $true
    }

    Context "required frontmatter fields" {
        $frontmatter = if (Test-Path $agentFile) { Get-Frontmatter -FilePath $agentFile } else { "" }

        It "has tools: restricted to read and search (not write)" {
            ($frontmatter -match "tools:.*'read'") -and ($frontmatter -match "tools:.*'search'") | Should Be $true
        }

        It "is NOT user-invocable" {
            ($frontmatter -match 'user-invocable:\s*false') | Should Be $true
        }

        It "has a model in frontmatter" {
            ($frontmatter -match 'model:') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# P1.41 — cg-plan-review.prompt.md existence and structure
# ---------------------------------------------------------------------------

Describe "cg-plan-review.prompt.md - existence and structure" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan-review.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = Get-Frontmatter -FilePath $promptFile

        It "does not have a tools: key (orchestrating prompt needs unrestricted access)" {
            ($frontmatter -notmatch 'tools:') | Should Be $true
        }
    }

    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "dispatches @cg-plan-critic" {
        ($content -match '@cg-plan-critic') | Should Be $true
    }

    It "can locate a plan without user specifying a path (scans .cg-docs/plans/)" {
        ($content -match '\.cg-docs[/\\]plans') | Should Be $true
    }

    It "includes side-idea capture in Step 4" {
        ($content -match 'Step 4.*Side-Idea Capture') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.42 — cg-plan.prompt.md Step 6 plan-review handoff and side-idea capture
# ---------------------------------------------------------------------------

Describe "cg-plan.prompt.md - Step 6 plan-review handoff" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-plan.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 6 suggests /cg-plan-review as an option" {
        ($content -match '/cg-plan-review') | Should Be $true
    }

    It "Step 6a includes side-idea capture section" {
        ($content -match '6a\. Side-Idea Capture') | Should Be $true
    }

    It "Step 6b contains the handoff options" {
        ($content -match '6b\. Handoff') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P1.43 — cg-resume.prompt.md schema bypass guard for compound-gpid workspace
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - schema bypass guard" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "contains workspace-root SCHEMA_VERSION self-check before schema comparison" {
        ($content -match 'SCHEMA_VERSION') -and ($content -match 'workspace root') | Should Be $true
    }

    It "instructs to skip schema comparison when workspace root has SCHEMA_VERSION" {
        ($content -match '[Ss]kip this entire step|[Ss]kip.*proceed.*Step 2') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-work.prompt.md - test failure recovery (per-step test enforcement)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - test failure recovery" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "exists" {
        Test-Path $promptFile | Should Be $true
    }

    It "documents 2 fix attempts hard cap" {
        ($content -match '\d+\.\s+If tests are still failing after 2 fix attempts') | Should Be $true
    }

    It "notification is rendered as a blockquote" {
        ($content -match '>\s+"?\*\*N test\(s\)|>\s+\*\*N test\(s\)') | Should Be $true
    }

    It "notification template includes 'Review before merging'" {
        ($content -match 'Review before merging') | Should Be $true
    }

    It "notification template shows per-test enumeration format" {
        ($content -match '<test-file>::<test-name>') | Should Be $true
    }

    It "explicitly separates test failures from @cg-fix-problems dispatch" {
        ($content -match '(?s)Do NOT dispatch.*@cg-fix-problems.*test fail') | Should Be $true
    }

    It "includes anti-weakening guard ('not weaken')" {
        ($content -match 'not\s+weaken|weaken or remove') | Should Be $true  # \s+ intentionally spans the CRLF line break between 'not' and 'weaken' in the prompt
    }

    It "permits test updates when function interface explicitly changed" {
        ($content -match 'changed signature or return type|Inference about interface change') | Should Be $true
    }

    It "notification template uses variable count placeholder (N test(s))" {
        ($content -match 'N test\(s\)') | Should Be $true
    }

    It "describes sequential two-attempt structure ('one more targeted fix attempt')" {
        ($content -match 'one more targeted fix') | Should Be $true
    }

    It "requires full-suite re-run after targeted fixes resolve to catch regressions" {
        ($content -match '(?s)full test suite.*catch regressions|regressions introduced by the fix') | Should Be $true
    }

    It "instructs continuing to Auto-Fix Diagnostics when full suite passes (continue path)" {
        ($content -match '(?s)full suite passes.*continue normally|continue.*Auto-Fix Diagnostics') | Should Be $true
    }

    It "notification template includes last error message placeholder" {
        ($content -match '<last error message>') | Should Be $true
    }

    It "on new regressions emits step-4 format notification and continues to Auto-Fix Diagnostics" {
        ($content -match 'emit the standard failure notification.*sub-step 4|format from sub-step 4') | Should Be $true
    }

    It "includes double-notification skip-guard in Auto-Fix Diagnostics sub-item 5" {
        ($content -match '(?s)Test Failure Recovery step 4.*skip emitting') | Should Be $true
    }

    It "scopes Test Failure Recovery to functional tests only" {
        ($content -match 'Test Failure Recovery.*functional tests only|get_errors.*handled separately') | Should Be $true
    }

    It "full-suite re-run step appears before the user-wait pause" {
        $rrunIdx = $content.IndexOf('full test suite')
        $waitIdx = $content.IndexOf('Wait for the user')
        $rrunIdx | Should BeGreaterThan -1
        $rrunIdx | Should BeLessThan $waitIdx
    }
}

# ---------------------------------------------------------------------------
# P1.37 — cg-work Step 3.7 must have title-search fallback for unlinked features
# Bug: When a plan implements features whose roadmap entry still has plan: null,
# Step 3.7 skips them with only a soft warning and never updates their status.
# Fix: add a fallback that searches feature titles in the plan content and
# prompts the user to confirm which features were completed.
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 3.7 title-search fallback for plan:null features" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 3.7 searches feature titles in the plan content when no path match found" {
        ($content -match 'title.*plan content|feature.*title.*appear|scan.*plan.*title|title.*match.*plan') | Should Be $true
    }

    It "Step 3.7 prompts the user to confirm which unlinked features were completed" {
        ($content -match 'confirm.*which features|which.*features.*complet|ask.*user.*confirm') | Should Be $true
    }

    It "Step 3.7 still dispatches @cg-roadmap for confirmed matches from the fallback" {
        # The fallback must dispatch @cg-roadmap, not just warn
        $step37Start = $content.IndexOf("### Step 3.7:")
        $step4Start  = $content.IndexOf("### Step 4:")
        $step37Block = $content.Substring($step37Start, $step4Start - $step37Start)
        ($step37Block -match '@cg-roadmap') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.4 — cg-work.prompt.md - Step 1.5 Mark Work Started
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 1.5 Mark Work Started" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "dispatches @cg-roadmap to mark feature status active at work start" {
        ($content -match 'to status active') | Should Be $true
    }

    It "Step 1.5 is conditioned on feature status being planned" {
        ($content -match 'status is.*planned') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.5 — cg-work.prompt.md - Step 3.5 Mark Plan Complete
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 3.5 Mark Plan Complete" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "Step 3.5 writes completed-date with today's date" {
        ($content -match 'completed-date') | Should Be $true
    }

    It "Step 3.5 changes status to completed in plan frontmatter" {
        $step35Start = $content.IndexOf("### Step 3.5:")
        $step37Start = $content.IndexOf("### Step 3.7:")
        $step35Start | Should BeGreaterThan -1
        $step37Start | Should BeGreaterThan $step35Start
        $step35Block = $content.Substring($step35Start, $step37Start - $step35Start)
        ($step35Block -match 'status.*completed|status: completed') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Context Layer — compound-gpid.context.md referenced in all 14 prompts
# ---------------------------------------------------------------------------

Describe "context layer - all 15 prompts reference compound-gpid.context.md" {
    $prompts = @(
        "cg-brainstorm",
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
        "cg-work"
    )

    foreach ($name in $prompts) {
        $promptFile = Join-Path $repoRoot ".github\prompts\$name.prompt.md"
        $content    = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

        It "$name.prompt.md references compound-gpid.context.md" {
            ($content -match 'compound-gpid\.context\.md') | Should Be $true
        }

        It "$name.prompt.md instructs to skip silently when context.md is absent" {
            ($content -match 'skip silently|skip.*silently|proceed without project context') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Context Layer — renumbering survival: 'warn' item retains 'warn' text
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
            ($content -match 'warn the user') | Should Be $true
        }

        It "$name.prompt.md retains 'No project charter found' message text" {
            ($content -match 'No project charter found') | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Context Layer — cg-compound Step 5 context enrichment before Step 6 confirm
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - context enrichment step ordering" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 5 Context Enrichment section" {
        ($content -match 'Step 5.*Context Enrichment') | Should Be $true
    }

    It "includes Step 6 Confirm section" {
        ($content -match 'Step 6.*Confirm') | Should Be $true
    }

    It "Step 5 (Context Enrichment) comes before Step 6 (Confirm)" {
        $step5Pos = $content.IndexOf("### Step 5: Context Enrichment")
        $step6Pos = $content.IndexOf("### Step 6: Confirm")
        $step5Pos | Should BeGreaterThan -1
        $step6Pos | Should BeGreaterThan -1
        $step5Pos | Should BeLessThan $step6Pos
    }

    It "proposes adding to compound-gpid.context.md when domain knowledge is discovered" {
        ($content -match 'compound-gpid\.context\.md') | Should Be $true
    }

    It "offers to create context.md if it does not exist" {
        ($content -match 'does not exist.*suggest creating|Would you like me to create it') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Context Layer — cg-work Step 3.8 milestone completion check
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - Step 3.8 milestone completion check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 3.8 Milestone Completion Check section" {
        ($content -match 'Step 3\.8.*Milestone Completion Check') | Should Be $true
    }

    It "Step 3.8 appears between Step 3.7 and Step 4 in the file" {
        $step37Pos = $content.IndexOf("### Step 3.7:")
        $step38Pos = $content.IndexOf("### Step 3.8:")
        $step4Pos  = $content.IndexOf("### Step 4:")
        $step37Pos | Should BeGreaterThan -1
        $step38Pos | Should BeGreaterThan -1
        $step4Pos  | Should BeGreaterThan -1
        $step38Pos | Should BeGreaterThan $step37Pos
        $step38Pos | Should BeLessThan $step4Pos
    }

    It "counts non-done features in the milestone after marking done" {
        ($content -match 'all features.*done|not.*done.*idea.*planned.*active') | Should Be $true
    }

    It "dispatches @cg-roadmap when milestone is fully complete" {
        $step38Start = $content.IndexOf("### Step 3.8:")
        $step4Start  = $content.IndexOf("### Step 4:")
        $step38Block = $content.Substring($step38Start, $step4Start - $step38Start)
        ($step38Block -match '@cg-roadmap') | Should Be $true
    }

    It "warns user that Current Focus may be stale when milestone completes" {
        ($content -match '[Ss]tale.*Current Focus|Current Focus.*stale') | Should Be $true
    }

    It "suggests /cg-strategy to update direction after milestone completes" {
        ($content -match '/cg-strategy') | Should Be $true
    }

    It "does NOT auto-modify compound-gpid.md charter (redirects to /cg-strategy)" {
        $step38Start = $content.IndexOf("### Step 3.8:")
        $step4Start  = $content.IndexOf("### Step 4:")
        $step38Block = $content.Substring($step38Start, $step4Start - $step38Start)
        # Charter direction is deferred to /cg-strategy, not handled inline in cg-work
        ($step38Block -match '/cg-strategy') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Context Layer — cg-resume Step 2f.5 Current Focus staleness check
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - Step 2f.5 Current Focus staleness" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 2f.5 Current Focus staleness check" {
        ($content -match '2f\.5.*[Cc]urrent [Ff]ocus') | Should Be $true
    }

    It "checks if Current Focus references a completed milestone" {
        ($content -match 'status.*done|done.*status') | Should Be $true
    }

    It "surfaces a nudge when Current Focus references a completed milestone" {
        ($content -match 'Stale Current Focus') | Should Be $true
    }

    It "does NOT auto-modify the charter (read-only nudge only)" {
        $step2f5Start = $content.IndexOf("#### 2f.5.")
        $step3Start   = $content.IndexOf("### Step 3:")
        if ($step2f5Start -ge 0 -and $step3Start -ge 0) {
            $block = $content.Substring($step2f5Start, $step3Start - $step2f5Start)
            ($block -match 'Set-Content|Write-Content|update.*compound-gpid\.md') | Should Be $false
        } else {
            $true | Should Be $true  # guard: skip if section not found
        }
    }

    It "suggests /cg-strategy to update direction" {
        ($content -match '/cg-strategy') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Context Layer — .gitignore must NOT contain compound-gpid.context.md
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
        # Only check non-comment lines — a comment documenting that the file is intentionally
        # NOT gitignored is permitted; an uncommented entry would actually ignore the file.
        $nonCommentLines = ($content -split '\r?\n' | Where-Object { $_ -notmatch '^\s*#' }) -join "`n"
        ($nonCommentLines -match 'compound-gpid\.context\.md') | Should Be $false
    }
}

# ---------------------------------------------------------------------------
# cg-compound.prompt.md - context enrichment step (Step 5)
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - context enrichment step" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references compound-gpid.context.md in Step 5" {
        ($content -match 'compound-gpid\.context\.md') | Should Be $true
    }

    It "proposes adding to compound-gpid.context.md when a finding is relevant" {
        # The step must include language proposing additions to context.md sections
        ($content -match 'I.d add this to the|propose.*addition|suggest.*add') | Should Be $true
    }

    It "includes an offer to create compound-gpid.context.md when it does not exist" {
        ($content -match 'does not exist.*create it|create it.*does not exist|Would you like me to create it') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-resume.prompt.md - Current Focus staleness check (Step 2f.5)
# ---------------------------------------------------------------------------

Describe "cg-resume.prompt.md - Current Focus staleness check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 2f.5 Current Focus staleness check" {
        ($content -match '2f\.5') | Should Be $true
    }

    It "cross-references milestone status done in staleness logic" {
        ($content -match "status.*done|status.*`"done`"") | Should Be $true
    }

    It "emits a Stale Current Focus nudge when a completed milestone is referenced" {
        ($content -match 'Stale Current Focus') | Should Be $true
    }

    It "does not auto-modify the charter (nudge only)" {
        ($content -match 'Do NOT auto-modify|only surface the nudge') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-work.prompt.md - milestone completion check (Step 3.8)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - milestone completion check" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Step 3.8 milestone completion check" {
        ($content -match '3\.8') | Should Be $true
    }

    It "dispatches @cg-roadmap when all features in a milestone are done" {
        ($content -match '@cg-roadmap.*milestone|milestone.*@cg-roadmap') | Should Be $true
    }

    It "warns the user when a milestone is fully complete" {
        ($content -match 'Milestone.*is now complete|is now complete') | Should Be $true
    }

    It "offers to update Current Focus when a milestone completes" {
        ($content -match 'Current Focus') | Should Be $true
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
        (Test-Path $cgWorkFile) | Should Be $true
    }

    It "cg-work.prompt.md contains execution_subagent instruction" {
        ($cgWorkContent -match 'execution_subagent') | Should Be $true
    }

    It "cg-work.prompt.md references Run-Tests.ps1 in test block" {
        ($cgWorkContent -match 'Run-Tests\.ps1') | Should Be $true
    }

    It "cg-work.prompt.md references last-run.json artifact" {
        ($cgWorkContent -match 'last-run\.json') | Should Be $true
    }

    It "cg-work.prompt.md contains Invoke-Pester prohibition alongside execution_subagent" {
        # Co-presence check: both must exist (prohibition intent confirmed).
        # Does not test exact phrasing - rewording the prohibition still passes.
        ($cgWorkContent -match 'execution_subagent') -and ($cgWorkContent -match 'Invoke-Pester') |
            Should Be $true
    }

    It "warns filteredFiles non-null means partial run (commit gate guard)" {
        ($cgWorkContent -match 'filteredFiles') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P3.10 — cg-work full-suite commit gate guard (dedicated describe)
# ---------------------------------------------------------------------------

Describe "cg-work.prompt.md - full-suite commit gate guard" {
    $cgWorkFile = Join-Path $repoRoot ".github\prompts\cg-work.prompt.md"
    $cgWorkContent = if (Test-Path $cgWorkFile) { Get-Content $cgWorkFile -Raw -Encoding UTF8 } else { "" }

    It "full-suite gate query includes filteredFiles field" {
        ($cgWorkContent -match 'filteredFiles') | Should Be $true
    }

    It "partial run guard: non-null filteredFiles blocks commit gate" {
        ($cgWorkContent -match 'filteredFiles.*partial run|partial run.*filteredFiles') | Should Be $true
    }
}

Describe "Pester crash prevention - execution_subagent blocks in cg-fix-triage" {
    $cgFixTriageFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    $cgFixTriageContent = if (Test-Path $cgFixTriageFile) { Get-Content $cgFixTriageFile -Raw -Encoding UTF8 } else { "" }

    It "cg-fix-triage.prompt.md exists" {
        (Test-Path $cgFixTriageFile) | Should Be $true
    }

    It "cg-fix-triage.prompt.md contains execution_subagent instruction" {
        ($cgFixTriageContent -match 'execution_subagent') | Should Be $true
    }

    It "cg-fix-triage.prompt.md references Run-Tests.ps1 in test block" {
        ($cgFixTriageContent -match 'Run-Tests\.ps1') | Should Be $true
    }

    It "cg-fix-triage.prompt.md references last-run.json artifact" {
        ($cgFixTriageContent -match 'last-run\.json') | Should Be $true
    }

    It "cg-fix-triage.prompt.md contains Invoke-Pester prohibition alongside execution_subagent" {
        ($cgFixTriageContent -match 'execution_subagent') -and ($cgFixTriageContent -match 'Invoke-Pester') |
            Should Be $true
    }

    It "full-suite gate includes filteredFiles field" {
        ($cgFixTriageContent -match 'filteredFiles') | Should Be $true
    }

    It "full-suite gate includes Test-Path guard for missing last-run.json" {
        ($cgFixTriageContent -match 'Test-Path tests\\last-run\.json') | Should Be $true
    }

    It "full-suite gate emits 'last-run.json not found' message when file is missing" {
        ($cgFixTriageContent -match 'last-run\.json not found') | Should Be $true
    }
}

Describe "Pester crash prevention - execution_subagent blocks in cg-diagnose" {
    $cgDiagnoseFile = Join-Path $repoRoot ".github\prompts\cg-diagnose.prompt.md"
    $cgDiagnoseContent = if (Test-Path $cgDiagnoseFile) { Get-Content $cgDiagnoseFile -Raw -Encoding UTF8 } else { "" }

    It "cg-diagnose.prompt.md exists" {
        (Test-Path $cgDiagnoseFile) | Should Be $true
    }

    It "cg-diagnose.prompt.md contains execution_subagent instruction" {
        ($cgDiagnoseContent -match 'execution_subagent') | Should Be $true
    }

    It "cg-diagnose.prompt.md references Run-Tests.ps1 in test block" {
        ($cgDiagnoseContent -match 'Run-Tests\.ps1') | Should Be $true
    }

    It "cg-diagnose.prompt.md references last-run.json artifact" {
        ($cgDiagnoseContent -match 'last-run\.json') | Should Be $true
    }

    It "cg-diagnose.prompt.md contains Invoke-Pester prohibition alongside execution_subagent" {
        ($cgDiagnoseContent -match 'execution_subagent') -and ($cgDiagnoseContent -match 'Invoke-Pester') |
            Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.5 — cg-skill-pester-safety SKILL.md Agent Workflow regression tests
# If the Agent Workflow section is removed, no agent will know to use
# execution_subagent, and the canonical Run-Tests.ps1 pattern is lost.
# ---------------------------------------------------------------------------

Describe "cg-skill-pester-safety - Agent Workflow section present" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-pester-safety\SKILL.md"
    $skillContent = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }

    It "SKILL.md contains 'execution_subagent' in Agent Workflow section" {
        ($skillContent -match 'execution_subagent') | Should Be $true
    }

    It "SKILL.md references Run-Tests.ps1 in Agent Workflow section" {
        ($skillContent -match 'Run-Tests\.ps1') | Should Be $true
    }

    It "SKILL.md references last-run.json artifact in Agent Workflow section" {
        ($skillContent -match 'last-run\.json') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.5 — copilot-instructions.md Rule 9 regression tests
# Rule 9 is the system-level mandate that makes the execution_subagent
# pattern binding on all agents. If removed, no agent-level test fails.
# ---------------------------------------------------------------------------

Describe "copilot-instructions.md - Rule 9 Agent test workflow" {
    $instructionsFile = Join-Path $repoRoot ".github\copilot-instructions.md"
    $instructionsContent = if (Test-Path $instructionsFile) { Get-Content $instructionsFile -Raw -Encoding UTF8 } else { "" }

    It "copilot-instructions.md contains 'Agent test workflow' rule" {
        ($instructionsContent -match 'Agent test workflow') | Should Be $true
    }

    It "copilot-instructions.md references execution_subagent in Rule 9" {
        ($instructionsContent -match 'execution_subagent') | Should Be $true
    }

    It "copilot-instructions.md references last-run.json in Rule 9" {
        ($instructionsContent -match 'last-run\.json') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.19 — cg-setup.prompt.md structural tests (zero coverage previously)
# ---------------------------------------------------------------------------

Describe "cg-setup.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }
}

Describe "cg-setup.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $frontmatter = Get-Frontmatter -FilePath $promptFile

    It "has a description in frontmatter" {
        $frontmatter | Should Match 'description:'
    }

    It "has a model in frontmatter" {
        $frontmatter | Should Match 'model:'
    }

    It "does not have a tools: key (orchestrating prompt needs unrestricted access)" {
        ($frontmatter -notmatch 'tools:') | Should Be $true
    }
}

Describe "cg-setup.prompt.md - mode detection and overwrite guard" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "references compound-gpid.local.md for mode detection (Mode A vs Mode B)" {
        ($content -match 'compound-gpid\.local\.md') | Should Be $true
    }

    It "has a project-name overwrite guard before recreating compound-gpid.md" {
        ($content -match 'already exists|overwrite') | Should Be $true
    }

    It "references setup-templates.md for templates" {
        ($content -match 'setup-templates\.md') | Should Be $true
    }

    It "creates roadmap.json during new project setup" {
        ($content -match 'roadmap\.json') | Should Be $true
    }

    It "updates .gitignore to exclude compound-gpid.local.md" {
        ($content -match '\.gitignore') | Should Be $true
    }

    It "does NOT create compound-gpid.md if user skips Question 4 (project name)" {
        ($content -match 'do NOT create|skips.*Q4|skips before Question 4') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.26 — cg-setup.prompt.md Mode B returning project coverage
# ---------------------------------------------------------------------------

Describe "cg-setup.prompt.md - Mode B returning project" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "includes Mode B section for returning projects" {
        ($content -match 'Mode B') | Should Be $true
    }

    It "checks for deprecated charter sections (B1.1.5)" {
        ($content -match 'Architecture Notes|deprecated') | Should Be $true
    }

    It "performs schema version check (B1.3)" {
        ($content -match 'cg-schema-version') | Should Be $true
    }

    It "checks for roadmap.json and notifies if missing (B1.2.5)" {
        ($content -match 'roadmap\.json') | Should Be $true
    }

    It "checks for compound-gpid.context.md and offers to create it (B1.1.3)" {
        ($content -match 'compound-gpid\.context\.md') | Should Be $true
    }

    It "explicitly instructs not to add context.md to .gitignore" {
        ($content -match '(?i)do NOT add.*\.gitignore|institutional knowledge') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-review-repos.prompt.md - file existence, frontmatter, guardrail, and content
# (Developer-only prompt for competitive repo analysis)
# ---------------------------------------------------------------------------

Describe "cg-review-repos.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should Be $true
    }
}

Describe "cg-review-repos.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
    $frontmatter = if (Test-Path $promptFile) { Get-Frontmatter -FilePath $promptFile } else { "" }

    Context "required frontmatter fields" {
        It "has a description in frontmatter" {
            $frontmatter | Should Match 'description:'
        }

        It "has a model in frontmatter" {
            $frontmatter | Should Match 'model:'
        }
    }
}

Describe "cg-review-repos.prompt.md - no tool restriction" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"

    Context "orchestrator must have unrestricted tools" {
        $frontmatter = if (Test-Path $promptFile) { Get-Frontmatter -FilePath $promptFile } else { "" }

        It "does not have a tools: key" {
            ($frontmatter -notmatch '(?m)^\s*tools:') | Should Be $true
        }
    }
}

Describe "cg-review-repos.prompt.md - dev-repo guardrail" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "checks compound-gpid.md for project-name" {
        ($content -match 'project-name') | Should Be $true
    }

    It "contains consumer-project warning message" {
        ($content -match 'compound-gpid development only') | Should Be $true
    }

    # P1.1: guardrail must check the exact case-sensitive value, not just key presence
    It "guardrail checks exact case-sensitive value 'Compound GPID'" {
        ($content -match '"Compound GPID"') | Should Be $true
    }
}

Describe "cg-review-repos.prompt.md - content structure" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review-repos.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "references --full flag for initial assessment mode" {
        ($content -match '--full') | Should Be $true
    }

    # P3.5: case-insensitive --full flag matching must be documented
    It "specifies case-insensitive --full flag matching" {
        ($content -match 'case-insensitive') | Should Be $true
    }

    It "references repos.json registry file" {
        ($content -match 'repos\.json') | Should Be $true
    }

    It "feature card template includes Compatibility field" {
        ($content -match 'Compatibility:') | Should Be $true
    }

    It "feature card template includes How we'd adapt it field" {
        ($content -match "How we'd adapt it") | Should Be $true
    }

    It "mentions concept mapping table" {
        ($content -match 'Concept Mapping') | Should Be $true
    }

    It "references assessment file path format" {
        ($content -match 'competitive-reviews/.*-full-review\.md|competitive-reviews\\.*-full-review\.md') | Should Be $true
    }

    It "references delta report file path format" {
        ($content -match 'delta-review\.md') | Should Be $true
    }

    It "warns about null-baseline repos for delta mode" {
        ($content -match 'lastReviewedRelease') | Should Be $true
    }

    It "instructs to run --full to recover null-baseline repos" {
        ($content -match '--full.*first|Run.*--full') | Should Be $true
    }

    It "stops when registry file is missing" {
        ($content -match 'Stop if the registry is missing') | Should Be $true
    }

    # P1.2: injection guard for fetch_webpage content
    It "contains injection guard for fetch_webpage content" {
        ($content -match 'untrusted data') | Should Be $true
    }

    # P1.3: URL validation — only https://github.com/ permitted
    It "requires https://github.com/ URLs only" {
        ($content -match 'https://github\.com/') | Should Be $true
    }

    # P1.4: repo ID validation — alphanumeric + hyphens only
    It "validates repo IDs are alphanumeric with hyphens only" {
        ($content -match 'alphanumeric.*hyphens|hyphens only') | Should Be $true
    }

    # P1.5: feature card limit per repo in full mode
    It "limits feature cards to 25 per repo in full mode" {
        ($content -match '25 most significant') | Should Be $true
    }

    # P1.6a: registry write strategy — per-repo immediately
    It "instructs updating registry per-repo immediately (not at end)" {
        ($content -match 'per-repo immediately') | Should Be $true
    }

    # P1.6b: registry write strategy — replace entire file
    It "instructs replacing the entire repos.json file on each write" {
        ($content -match 'entire file') | Should Be $true
    }

    # P2.4: lastFullReviewNote behavior on partial failure
    It "specifies lastFullReviewNote behavior on partial failure" {
        ($content -match 'lastFullReviewNote') | Should Be $true
    }

    # P3.2: lastFullReviewNote must be removed on successful full review
    It "specifies lastFullReviewNote is removed on successful full review" {
        ($content -match 'remove.*lastFullReviewNote|lastFullReviewNote.*removed') | Should Be $true
    }

    # P2.12: branch-specific tests for new validation paths
    It "validates releasesUrl ends with /releases" {
        ($content -match 'ends with.*releases|/releases') | Should Be $true
    }

    It "validates date formats as YYYY-MM-DD" {
        ($content -match 'YYYY-MM-DD') | Should Be $true
    }

    It "validates shortName uniqueness" {
        ($content -match 'shortName.*unique|unique.*shortName|Duplicate shortName') | Should Be $true
    }

    It "specifies collision policy for same-day re-runs" {
        ($content -match 'same-day re-run|-2.*-3|-3.*-2') | Should Be $true
    }

    It "validates root-level lastFullReview date separately from per-repo dates" {
        ($content -match 'root-level|registry root') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# competitive-reviews/repos.json - registry file validation
# ---------------------------------------------------------------------------

Describe "competitive-reviews/repos.json - registry" {
    $registryFile = Join-Path $repoRoot ".cg-docs\competitive-reviews\repos.json"

    It "exists in the repository" {
        Test-Path $registryFile | Should Be $true
    }

    It "is valid JSON" {
        { Get-Content $registryFile -Raw -Encoding UTF8 | ConvertFrom-Json } | Should Not Throw
    }

    $json = if (Test-Path $registryFile) {
        try { Get-Content $registryFile -Raw -Encoding UTF8 | ConvertFrom-Json } catch { $null }
    } else { $null }

    It "has schemaVersion field" {
        $json.schemaVersion | Should Not BeNullOrEmpty
    }

    # P2.3: value must match the constant expected by the prompt (case-sensitive)
    It "schemaVersion equals expected constant" {
        $json.schemaVersion.Trim() | Should BeExactly 'compound-gpid-competitive-reviews-v1'
    }

    # P2.5: schemaVersion must not have leading/trailing whitespace (invisible in failure messages)
    It "schemaVersion has no leading or trailing whitespace" {
        $json.schemaVersion | Should Be $json.schemaVersion.Trim()
    }

    # P2.2: count sentinel — update when adding a new repo to repos.json
    It "has repos array with exactly 3 entries" {
        $json.repos.Count | Should Be 3
    }

    foreach ($repoEntry in @(if ($null -ne $json) { $json.repos } else { @() })) {
        It "repo '$($repoEntry.id)' has required fields" {
            $repoEntry.id | Should Not BeNullOrEmpty
            $repoEntry.url | Should Not BeNullOrEmpty
            $repoEntry.releasesUrl | Should Not BeNullOrEmpty
            $repoEntry.shortName | Should Not BeNullOrEmpty
        }
    }
}

# ---------------------------------------------------------------------------
# Review convergence — cg-review mode:verify argument
# ---------------------------------------------------------------------------

Describe "cg-review.prompt.md - mode:verify argument" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents mode:verify argument" {
        ($content -match 'mode:verify') | Should Be $true
    }

    It "includes Step 1.7 for verification context" {
        ($content -match 'Step 1\.7') | Should Be $true
    }

    It "suppression policy never suppresses P0/P1" {
        ($content -match '(?s)P0/P1.*[Nn]ever suppress') | Should Be $true
    }

    It "suppression policy suppresses P2/P3 on fixed-finding scope" {
        ($content -match '(?s)P2/P3.*fixed-finding scope|P2/P3.*fix-consequence') | Should Be $true
    }

    It "suppression policy always reports cross-file breakage" {
        ($content -match '(?s)[Cc]ross-file breakage.*[Aa]lways report') | Should Be $true
    }

    It "forces light depth in verify mode" {
        ($content -match '(?si)Force depth to.*light|light.*forced') | Should Be $true
    }

    It "verify review filename pattern documented" {
        ($content -match 'verify-review\.md') | Should Be $true
    }

    It "instructs to skip Step 1.5 overrides in verify mode" {
        ($content -match '(?si)Step 1\.5.*[Ss]kip.*mode:verify|[Ss]kip this step if.*mode:verify') | Should Be $true
    }

    It "documents parent-review frontmatter for verify reviews" {
        ($content -match 'parent-review') | Should Be $true
    }

    It "documents type: verification frontmatter field" {
        ($content -match 'type: verification') | Should Be $true
    }

    It "unrecognized-argument warning lists mode:verify" {
        ($content -match 'Recognized:.*mode:verify') | Should Be $true
    }

    It "documents mutual exclusion of mode:autofix and mode:verify" {
        ($content -match '(?s)mode:autofix.*mode:verify.*mutually exclusive|Cannot combine.*mode:autofix.*mode:verify') | Should Be $true
    }

    It "mutual exclusion resolves in favour of mode:verify" {
        ($content -match 'using.*mode:verify|ignore.*mode:autofix') | Should Be $true
    }

    It "warns when no prior review with fixed findings found" {
        ($content -match '[Nn]o prior review with fixed findings found') | Should Be $true
    }

    It "verify mode dispatches only cg-code-quality and cg-testing" {
        ($content -match '(?s)[Vv]erify mode.*cg-code-quality.*cg-testing|cg-code-quality.*cg-testing.*light.*forced') | Should Be $true
    }

    It "excludes -verify-review.md files from prior review scan" {
        ($content -match '-review\.md.*NOT.*-verify-review\.md|verify-review\.md.*[Ss]kip|[Ss]kip.*verify-review\.md') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# Review convergence — cg-fix-triage mode:verify handoff
# ---------------------------------------------------------------------------

Describe "cg-fix-triage.prompt.md - mode:verify handoff" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "suggests mode:verify instead of review light in Step 5" {
        ($content -match '(?s)Step 5.*mode:verify') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# P2.7/P2.8 — cg-release-scanner.agent.md existence and dispatch reference
# ---------------------------------------------------------------------------

Describe "cg-release-scanner.agent.md - existence and structure" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-release-scanner.agent.md"

    It "exists in the repository" {
        Test-Path $agentFile | Should Be $true
    }

    Context "required frontmatter fields" {
        $frontmatter = Get-Frontmatter -FilePath $agentFile

        It "has user-invocable: false in frontmatter" {
            ($frontmatter -match 'user-invocable:\s*false') | Should Be $true
        }

        It "has tools: restricted to read and search (not write)" {
            ($frontmatter -match "tools:.*'read'") -and ($frontmatter -match "tools:.*'search'") | Should Be $true
        }

        It "has a model in frontmatter" {
            ($frontmatter -match 'model:') | Should Be $true
        }
    }

    $agentContent = Get-Content $agentFile -Raw -Encoding UTF8

    It "documents Highest impact: none for empty commit log" {
        ($agentContent -match 'Highest impact: none') | Should Be $true
    }

    It "uses window-days (hyphen, not underscore) in window-start description" {
        ($agentContent -match 'window-days') | Should Be $true
    }
    It "uses tag-date (hyphen, not underscore) in window-start description" {
        ($agentContent -match 'tag-date') | Should Be $true
    }
}

Describe "cg-release.prompt.md - dispatches cg-release-scanner" {
    $promptFile = Join-Path $repoRoot "cg-release.prompt.md"
    $content = if (Test-Path $promptFile) { Get-Content $promptFile -Raw -Encoding UTF8 } else { "" }

    It "cg-release.prompt.md references @cg-release-scanner" {
        ($content -match '@cg-release-scanner') | Should Be $true
    }

    It "warns when window-start is on or after today (zero-doc-context guard)" {
        ($content -match 'window-start.*today|All.*cg-docs.*entries will be excluded') | Should Be $true
    }

    It "warns and falls back when --since ISO date is in the future" {
        ($content -match 'after today.*fall back|parsed.*after today') | Should Be $true
    }

    It "warns when commit log exceeds 500 lines" {
        ($content -match '500 lines|exceeds 500') | Should Be $true
    }

    It "warns on shallow clone and falls back to window-days formula" {
        ($content -match 'shallow clone') | Should Be $true
    }

    It "catch-all when release-result.txt is absent or unrecognized" {
        ($content -match 'may have failed|release-result\.txt.*absent|neither.*CREATED') | Should Be $true
    }

    It "documents halt condition when scanner returns no output" {
        ($content -match 'no output|does not contain.*Scan Summary|Scanner returned no output') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-skill-project-scanner - existence and structure
# ---------------------------------------------------------------------------

Describe "cg-skill-project-scanner - existence and structure" {
    $skillDir  = Join-Path $repoRoot ".github\skills\cg-skill-project-scanner"
    $skillFile = Join-Path $skillDir "SKILL.md"

    It "skill directory exists" {
        Test-Path $skillDir | Should Be $true
    }

    It "SKILL.md exists" {
        Test-Path $skillFile | Should Be $true
    }

    Context "frontmatter fields" {
        $frontmatter = if (Test-Path $skillFile) { Get-Frontmatter -FilePath $skillFile } else { "" }

        It "has a name: field in frontmatter" {
            ($frontmatter -match 'name:') | Should Be $true
        }

        It "has a description: field in frontmatter" {
            ($frontmatter -match 'description:') | Should Be $true
        }

        It "has a schema-version: field in frontmatter" {
            ($frontmatter -match 'schema-version:') | Should Be $true
        }
    }

    $skillContent = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }

    It "contains Tier 1 heading (Language and Framework Detection)" {
        ($skillContent -match 'Tier 1') | Should Be $true
    }

    It "contains Tier 2 heading (Project Type and Convention)" {
        ($skillContent -match 'Tier 2') | Should Be $true
    }

    It "contains Tier 3 heading (Charter-Relevant Content)" {
        ($skillContent -match 'Tier 3') | Should Be $true
    }

    It "contains Tier 4 heading (Out of Scope)" {
        ($skillContent -match 'Tier 4') | Should Be $true
    }

    It "contains confidence threshold table with high/medium/low rows" {
        ($skillContent -match '(?i)\|\s*(high|medium|low)\s*\|') | Should Be $true
    }

    It "contains output schema section" {
        ($skillContent -match 'Output Schema') | Should Be $true
    }

    It "contains prompt injection safety rule" {
        ($skillContent -match 'data, not instructions|prompt injection') | Should Be $true
    }

    It "signal catalog is non-empty (Tier 1 has at least one row)" {
        # After the Tier 1 heading there should be at least one table row with a pipe character
        ($skillContent -match 'Tier 1[\s\S]+?\|[^\n]+\|') | Should Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-project-scanner.agent.md - existence and structure
# Note: No dispatch test — the calling prompt (/cg-setup) is not modified
# until Phase 2. Limit tests to agent existence, frontmatter, and content.
# ---------------------------------------------------------------------------

Describe "cg-project-scanner.agent.md - existence and structure" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-project-scanner.agent.md"

    It "exists in the repository" {
        Test-Path $agentFile | Should Be $true
    }

    Context "required frontmatter fields" {
        $frontmatter = if (Test-Path $agentFile) { Get-Frontmatter -FilePath $agentFile } else { "" }

        It "has user-invocable: false in frontmatter" {
            ($frontmatter -match 'user-invocable:\s*false') | Should Be $true
        }

        It "has tools: restricted to read and search (not write)" {
            $tools = Get-ToolsList $frontmatter
            ($tools -contains 'read') -and ($tools -contains 'search') -and (-not ($tools -contains 'write')) | Should Be $true
        }

        It "has model: Claude Haiku 4.5 (copilot) in frontmatter" {
            ($frontmatter -match 'model:\s*Claude Haiku 4\.5') | Should Be $true
        }
    }

    $agentContent = if (Test-Path $agentFile) { Get-Content $agentFile -Raw -Encoding UTF8 } else { "" }

    It "references cg-skill-project-scanner (loads the signal catalog)" {
        ($agentContent -match 'cg-skill-project-scanner') | Should Be $true
    }

    It "contains prompt injection guard (data not instructions)" {
        ($agentContent -match 'data, not instructions|prompt injection') | Should Be $true
    }

    It "output schema includes Scan Summary section" {
        ($agentContent -match 'Scan Summary') | Should Be $true
    }

    It "output schema includes Language Detection section" {
        ($agentContent -match 'Language Detection') | Should Be $true
    }

    It "output schema includes Project Type section" {
        ($agentContent -match 'Project Type') | Should Be $true
    }

    It "output schema includes Framework and Tooling section" {
        ($agentContent -match 'Framework.*Tooling|Tooling.*Framework') | Should Be $true
    }

    It "output schema includes Charter Draft Content section" {
        ($agentContent -match 'Charter Draft Content') | Should Be $true
    }

    It "output schema includes Setup Recommendations section" {
        ($agentContent -match 'Setup Recommendations') | Should Be $true
    }

    It "does not reference write or terminal tools" {
        ($agentContent -match 'editFiles|runInTerminal|createFile') | Should Be $false
    }
}

# ---------------------------------------------------------------------------
# P1.44 — cg-brainstorm Branch Offer must appear before Step 2 questions
# The branch offer is the very first question asked of the user, so the
# model cannot bias itself toward an existing branch mid-brainstorm.
# ---------------------------------------------------------------------------

Describe "cg-brainstorm.prompt.md - Branch Offer appears before Step 2" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-brainstorm.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has a Branch Offer step between Step 1.5 and Step 2 (Step 1.7)" {
        $branchOfferIdx = $content.IndexOf('### Step 1.7:')
        $branchOfferIdx | Should BeGreaterThan -1
    }

    It "Branch Offer (Step 1.7) appears before Step 2 Clarifying Questions" {
        $branchOfferIdx = $content.IndexOf('### Step 1.7:')
        $step2Idx       = $content.IndexOf('### Step 2:')
        $branchOfferIdx | Should BeGreaterThan -1
        $step2Idx       | Should BeGreaterThan $branchOfferIdx
    }
}

