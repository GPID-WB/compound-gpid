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
