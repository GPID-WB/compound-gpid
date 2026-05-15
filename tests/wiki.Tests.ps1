# tests/wiki.Tests.ps1
# Pester tests for the auto-generated project wiki feature:
# - cg-skill-wiki/SKILL.md (skill file)
# - cg-wiki.agent.md (agent)
# - cg-wiki.prompt.md (prompt)
# - cg-setup.prompt.md integration (Step A5.8, Mode B B1.1.6)
# - setup-templates.md (Wiki Configuration section)
# - cg-compound.prompt.md integration (Step 0.5, Step 3c, File Permissions)
#
# Run with: Invoke-Pester tests/wiki.Tests.ps1 -Quiet

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
if ($env:CG_TEST_ROOT -and -not (Test-Path $env:CG_TEST_ROOT)) { throw "CG_TEST_ROOT '$env:CG_TEST_ROOT' does not exist" }
. "$PSScriptRoot/helpers.ps1"

# ---------------------------------------------------------------------------
# cg-skill-wiki/SKILL.md — skill file existence and required sections
# ---------------------------------------------------------------------------

Describe "cg-skill-wiki/SKILL.md - file existence" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"

    It "exists in the repository" {
        Test-Path $skillFile | Should -Be $true
    }
}

Describe "cg-skill-wiki/SKILL.md - schema section" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"
    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "documents the _wiki.yml schemaVersion field" {
        ($content -match 'schemaVersion') | Should -Be $true
    }

    It "documents the compound-gpid-wiki-v1 schema version value" {
        ($content -match 'compound-gpid-wiki-v1') | Should -Be $true
    }

    It "documents the ownership field with auto and manual values" {
        ($content -match 'ownership') | Should -Be $true
        ($content -match '"auto"') | Should -Be $true
        ($content -match '"manual"') | Should -Be $true
    }

    It "documents lastUpdated field and its update rule" {
        ($content -match 'lastUpdated') | Should -Be $true
    }
}

Describe "cg-skill-wiki/SKILL.md - section markers" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"
    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "documents the cg:auto section marker syntax" {
        ($content -match 'cg:auto') | Should -Be $true
    }

    # P2.7 — cg:auto:end closing marker
    It "documents the cg:auto:end closing marker syntax (P2.7)" {
        ($content -match 'cg:auto:end') | Should -Be $true
    }

    It "documents that nested markers are forbidden" {
        ($content -match '[Nn]ested') | Should -Be $true
    }

    # P2.16 — fake cg:auto:end inside code blocks is ignored
    It "specifies that cg:auto:end inside fenced code blocks is ignored (P2.16)" {
        ($content -match 'code block|fenced code|inline code') | Should -Be $true
    }
}

Describe "cg-skill-wiki/SKILL.md - ownership rules" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"
    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "documents page-level ownership rules" {
        ($content -match 'Page-level ownership') | Should -Be $true
    }

    It "documents section-level ownership rules" {
        ($content -match 'Section-level ownership') | Should -Be $true
    }

    It "documents the conflict resolution algorithm" {
        ($content -match 'Conflict Resolution') | Should -Be $true
    }
}

Describe "cg-skill-wiki/SKILL.md - update trigger criteria" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"
    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "documents the wiki update trigger criteria section" {
        ($content -match 'Update Trigger Criteria') | Should -Be $true
    }

    # P3.3 — split 4 criteria into separate It blocks for clearer failure messages
    It "documents the public function signature trigger criterion" {
        ($content -match 'public function signature') | Should -Be $true
    }

    It "documents the CLI command trigger criterion" {
        ($content -match 'CLI command') | Should -Be $true
    }

    It "documents the user-visible output trigger criterion" {
        ($content -match 'user-visible output') | Should -Be $true
    }

    It "documents the dependency trigger criterion" {
        ($content -match 'dependency') | Should -Be $true
    }
}

Describe "cg-skill-wiki/SKILL.md - project-type templates" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"
    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "documents the Package project type template" {
        ($content -match '### Package') | Should -Be $true
    }

    It "documents the Analysis project type template" {
        ($content -match '### Analysis') | Should -Be $true
    }

    It "documents the Tool project type template" {
        ($content -match '### Tool') | Should -Be $true
    }

    It "documents the Dashboard project type template" {
        ($content -match '### Dashboard') | Should -Be $true
    }

    It "documents the API project type template" {
        ($content -match '### API') | Should -Be $true
    }

    It "documents the Other project type template" {
        ($content -match '### Other') | Should -Be $true
    }
}

Describe "cg-skill-wiki/SKILL.md - wiki configuration schema" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"
    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "documents the Wiki Configuration section for compound-gpid.context.md" {
        ($content -match 'Wiki Configuration') | Should -Be $true
    }

    It "documents the folder configuration key" {
        ($content -match '<!-- folder:') | Should -Be $true
    }

    It "documents the audience configuration key" {
        ($content -match '<!-- audience:') | Should -Be $true
    }

    It "documents the tone configuration key" {
        ($content -match '<!-- tone:') | Should -Be $true
    }
}

Describe "cg-skill-wiki/SKILL.md - GitHub Wiki conversion guide" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"
    $content = Get-Content $skillFile -Raw -Encoding UTF8

    It "documents the GitHub Wiki conversion guide" {
        ($content -match 'GitHub Wiki Conversion') | Should -Be $true
    }

    It "documents README.md to Home.md rename" {
        ($content -match 'Home\.md') | Should -Be $true
    }

    It "documents _Sidebar.md generation" {
        ($content -match '_Sidebar') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-wiki.agent.md — agent file structure
# ---------------------------------------------------------------------------

Describe "cg-wiki.agent.md - file existence" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-wiki.agent.md"

    It "exists in the repository" {
        Test-Path $agentFile | Should -Be $true
    }
}

Describe "cg-wiki.agent.md - frontmatter" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-wiki.agent.md"
    $fm = Get-Frontmatter -FilePath $agentFile
    $tools = Get-ToolsList -Frontmatter $fm

    It "has a description field" {
        ($fm -match 'description:') | Should -Be $true
    }

    It "has tools: ['read', 'write', 'search']" {
        ($tools -contains 'read') | Should -Be $true
        ($tools -contains 'write') | Should -Be $true
        ($tools -contains 'search') | Should -Be $true
    }

    It "is not user-invocable" {
        ($fm -match 'user-invocable:\s*false') | Should -Be $true
    }
}

Describe "cg-wiki.agent.md - mode documentation" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-wiki.agent.md"
    $content = Get-Content $agentFile -Raw -Encoding UTF8

    It "documents init mode" {
        ($content -match 'Mode: `init`') | Should -Be $true
    }

    It "documents update mode" {
        ($content -match 'Mode: `update`') | Should -Be $true
    }

    It "documents rebuild mode" {
        ($content -match 'Mode: `rebuild`') | Should -Be $true
    }

    It "documents convert mode" {
        ($content -match 'Mode: `convert`') | Should -Be $true
    }
}

Describe "cg-wiki.agent.md - dispatch contract" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-wiki.agent.md"
    $content = Get-Content $agentFile -Raw -Encoding UTF8

    It "documents the propose boolean parameter" {
        ($content -match 'propose') | Should -Be $true
    }

    It "documents the solution-path parameter" {
        ($content -match 'solution-path') | Should -Be $true
    }

    It "documents the wiki-manifest parameter" {
        ($content -match 'wiki-manifest') | Should -Be $true
    }

    It "documents lastUpdated update rule in a write mode" {
        ($content -match 'lastUpdated') | Should -Be $true
    }
}

Describe "cg-wiki.agent.md - security rules" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-wiki.agent.md"
    $content = Get-Content $agentFile -Raw -Encoding UTF8

    It "declares untrusted content rule for wiki file contents" {
        ($content -match '[Uu]ntrusted') | Should -Be $true
    }

    It "loads cg-skill-wiki" {
        ($content -match 'cg-skill-wiki') | Should -Be $true
    }

    It "validates solution-path prefix to prevent path traversal" {
        ($content -match '\.cg-docs/solutions/') | Should -Be $true
    }

    # P1.4 — injection scan before using solution content
    It "scans solution file for AI-redirect phrases before using content (P1.4)" {
        ($content -match 'Injection scan|injection scan') | Should -Be $true
    }

    It "flags SYSTEM: and Ignore/Override/Forget AI-redirect phrases (P1.4)" {
        ($content -match 'SYSTEM:|Ignore|Override|Forget') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-wiki.prompt.md — prompt file structure
# ---------------------------------------------------------------------------

Describe "cg-wiki.prompt.md - file existence" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-wiki.prompt.md"

    It "exists in the repository" {
        Test-Path $promptFile | Should -Be $true
    }
}

Describe "cg-wiki.prompt.md - frontmatter" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-wiki.prompt.md"
    $fm = Get-Frontmatter -FilePath $promptFile

    It "has a description field" {
        ($fm -match 'description:') | Should -Be $true
    }

    It "does not have a tools: restriction (orchestrating prompts must be unrestricted)" {
        ($fm -notmatch 'tools:') | Should -Be $true
    }
}

Describe "cg-wiki.prompt.md - Step 0 pattern" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-wiki.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has a Step 0: Get Bearings section" {
        ($content -match 'Step 0') | Should -Be $true
    }

    It "reads compound-gpid.md in Step 0" {
        ($content -match 'compound-gpid\.md') | Should -Be $true
    }

    It "parses --propose flag in Step 0 before Step 1 dispatch" {
        $flagPos  = $content.IndexOf('Step 0 flag parse')
        $step1Pos = $content.IndexOf('### Step 1:')
        $flagPos  | Should -BeGreaterThan -1
        $step1Pos | Should -BeGreaterThan -1
        $flagPos  | Should -BeLessThan $step1Pos
    }
}

Describe "cg-wiki.prompt.md - file permissions" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-wiki.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "declares must-NOT-write-directly clause" {
        ($content -match 'must NOT') | Should -Be $true
    }

    It "states all page writes are delegated to @cg-wiki" {
        ($content -match 'delegated to') | Should -Be $true
    }

    # P1.1 — restructure-mode carve-out for direct _wiki.yml writes
    It "permits direct _wiki.yml modification in restructure mode only (P1.1)" {
        ($content -match 'restructure.*mode only') | Should -Be $true
    }
}

Describe "cg-wiki.prompt.md - subcommand documentation" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-wiki.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents the rebuild subcommand" {
        ($content -match 'rebuild') | Should -Be $true
    }

    It "documents the restructure subcommand" {
        ($content -match 'restructure') | Should -Be $true
    }

    It "documents the convert subcommand" {
        ($content -match 'convert') | Should -Be $true
    }

    It "documents the status subcommand" {
        ($content -match 'status') | Should -Be $true
    }

    It "documents the help subcommand" {
        ($content -match 'help') | Should -Be $true
    }

    It "documents the --propose flag" {
        ($content -match '\-\-propose') | Should -Be $true
    }
}

Describe "cg-wiki.prompt.md - wiki existence guard" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-wiki.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "validates _wiki.yml exists before dispatching" {
        ($content -match '_wiki\.yml') | Should -Be $true
    }

    It "directs user to /cg-setup when wiki not initialized" {
        ($content -match '/cg-setup') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-setup.prompt.md integration — Step A5.8 and Mode B wiki offer
# ---------------------------------------------------------------------------

Describe "cg-setup.prompt.md - wiki scaffold integration" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "contains Step A5.8 wiki scaffold" {
        ($content -match 'A5\.8') | Should -Be $true
    }

    It "dispatches @cg-wiki in Step A5.8" {
        ($content -match 'cg-wiki') | Should -Be $true
    }

    It "handles @cg-wiki dispatch failure gracefully" {
        ($content -match '/cg-wiki rebuild') | Should -Be $true
    }

    It "contains Mode B wiki offer (B1.1.6)" {
        ($content -match 'B1\.1\.6') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# setup-templates.md — Wiki Configuration section in context template
# ---------------------------------------------------------------------------

Describe "setup-templates.md - Wiki Configuration in context.md template" {
    $templatesFile = Join-Path $repoRoot ".github\prompts\setup-templates.md"
    $content = Get-Content $templatesFile -Raw -Encoding UTF8

    It "contains Wiki Configuration section" {
        ($content -match 'Wiki Configuration') | Should -Be $true
    }

    It "contains folder configuration comment" {
        ($content -match '<!-- folder: wiki -->') | Should -Be $true
    }

    It "contains audience configuration comment" {
        ($content -match '<!-- audience:') | Should -Be $true
    }

    It "contains tone configuration comment" {
        ($content -match '<!-- tone:') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-compound.prompt.md integration — Step 0.5, Step 3c, File Permissions
# ---------------------------------------------------------------------------

Describe "cg-compound.prompt.md - wiki integration" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "has Step 0.5 for flag parsing" {
        ($content -match 'Step 0\.5') | Should -Be $true
    }

    It "parses --propose flag in Step 0.5 (not in Step 3c)" {
        ($content -match 'Step 0\.5.*Parse Flags|Parse Flags.*Step 0\.5') | Should -Be $true
    }

    It "has Step 3c Update Project Wiki" {
        ($content -match 'Step 3c') | Should -Be $true
        ($content -match 'Update Project Wiki') | Should -Be $true
    }

    It "File Permissions allows delegated wiki writes via @cg-wiki" {
        ($content -match '@cg-wiki') | Should -Be $true
        ($content -match 'delegated write') | Should -Be $true
    }

    It "Step 3c uses wiki-propose variable from Step 0.5" {
        ($content -match 'wiki-propose') | Should -Be $true
    }

    It "Step 3c evaluates trigger criteria (not vague user-facing assessment)" {
        ($content -match 'binary trigger criteria') | Should -Be $true
    }

    It "Step 3c dispatches @cg-wiki with mode update" {
        ($content -match 'mode: update') | Should -Be $true
    }

    It "Step 3c gracefully skips when _wiki.yml missing" {
        ($content -match '_wiki\.yml') | Should -Be $true
    }
}
