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

    # R-2026-05-18-013: folder field must be documented as informational (not agent-readable)
    It "documents folder field as informational mirror of context.md directive (R-013)" {
        ($content -match 'informational.*context\.md|context\.md.*informational') | Should -Be $true
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

    # R-2026-05-18-012: anchor to rule phrase, not common word [Nn]ested
    It "documents that nested markers are forbidden" {
        ($content -match 'Nested markers are forbidden') | Should -Be $true
    }

    # P2.16 / R-2026-05-18-012: anchor to rule phrase, not common words
    It "specifies that cg:auto:end inside fenced code blocks is ignored (P2.16, R-012)" {
        ($content -match 'Fake markers in code blocks are ignored') | Should -Be $true
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

    It "has read tool" {
        ($tools -contains 'read') | Should -Be $true
    }

    It "has write tool" {
        ($tools -contains 'write') | Should -Be $true
    }

    It "has search tool" {
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

    It "init Step 6 emits the Post-init Checklist after the report line" {
        # P2.7: The Post-init Checklist must be explicitly emitted by the agent
        # after init completes, not left to the model to discover.
        ($content -match '(?is)init Step 6.*Post-.*init.*Checklist|init Step 6.*Post-.*Checklist') | Should -Be $true
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

    # R-2026-05-18-011: anchor to injection-scan context to avoid common-word false positive
    It "flags SYSTEM: and Ignore/Override/Forget in injection-scan context (P1.4, R-011)" {
        ($content -match 'Injection scan[\s\S]{0,400}SYSTEM:') | Should -Be $true
    }

    It "pre-flight discards _wiki.yml folder field in favor of context.md value" {
        ($content -match 'discard its.*folder') | Should -Be $true
    }

    # R-2026-05-18-013: conflict-detection — agent emits note when _wiki.yml folder differs
    It "notifies user when _wiki.yml folder field differs from context.md resolved folder (R-013)" {
        # spans lines: 'folder' + 'informational only' within 300 chars
        ($content -match 'folder[\s\S]{0,300}informational only') | Should -Be $true
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
        ($content -match '/cg-wiki init') | Should -Be $true
        ($content -match '/cg-wiki rebuild') | Should -Be $false
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

    It "Step 3c no-manifest message directs user to /cg-wiki init (not rebuild)" {
        ($content -match '/cg-wiki\s+init') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# /cg-wiki init subcommand — user-facing bootstrap path for existing projects
# ---------------------------------------------------------------------------

Describe "cg-wiki.prompt.md - init subcommand" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-wiki.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "documents the init subcommand in the Usage section" {
        ($content -match '/cg-wiki\s+init') | Should -Be $true
    }

    It "includes init in the Step 1 parse table" {
        ($content -match '\|\s*`?init`?\s*\|') | Should -Be $true
    }

    It "dispatches @cg-wiki with mode: init" {
        ($content -match 'mode:\s*init') | Should -Be $true
    }

    It "allows init subcommand to bypass the missing-manifest guard" {
        ($content -match '(?i)(exception|bypass|skip).*init|init.*(exception|bypass|skip)') | Should -Be $true
    }
}

Describe "cg-setup.prompt.md - B1.1.6 references /cg-wiki init" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-setup.prompt.md"
    $content = Get-Content $promptFile -Raw -Encoding UTF8

    It "B1.1.6 no-wiki message directs user to /cg-wiki init (not /cg-setup)" {
        ($content -match '/cg-wiki\s+init') | Should -Be $true
    }
}

Describe "docs/reference.md - /cg-wiki entry includes init subcommand" {
    $refFile = Join-Path $repoRoot "docs\reference.md"
    $content = Get-Content $refFile -Raw -Encoding UTF8

    It "documents init subcommand in /cg-wiki reference entry" {
        ($content -match 'cg-wiki.*init|init.*cg-wiki') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# cg-wiki.agent.md — Pre-Flight halt message must not be circular (P2.1)
# ---------------------------------------------------------------------------

Describe "cg-wiki.agent.md - Pre-Flight halt message is non-circular" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-wiki.agent.md"
    $content = Get-Content $agentFile -Raw -Encoding UTF8

    It "manifest-not-found halt message does not suggest /cg-wiki rebuild (circular)" {
        # 'rebuild' in the halt message would send the user into an infinite loop
        # because rebuild itself requires _wiki.yml to exist
        ($content -match 'manifest not found[.\s\S]{0,500}/cg-wiki rebuild') | Should -Be $false
    }

    It "manifest-not-found halt message suggests /cg-wiki init" {
        ($content -match 'manifest not found[\.\s\S]{0,120}/cg-wiki init') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# compound-gpid repo self-configuration — docs/ folder as wiki target
# ---------------------------------------------------------------------------

Describe "compound-gpid.context.md - wiki configuration for this repo" {
    $contextFile = Join-Path $repoRoot "compound-gpid.context.md"
    $content = Get-Content $contextFile -Raw -Encoding UTF8

    It "has a ## Wiki Configuration section" {
        ($content -match '(?m)^## Wiki Configuration') | Should -Be $true
    }

    It "declares docs/ as the wiki folder" {
        ($content -match '<!--\s*folder:\s*docs\s*-->') | Should -Be $true
    }

    # R-2026-05-18-014: path-traversal guard on folder directive
    It "folder directive does not contain path traversal (..) (R-014)" {
        ($content -match '<!--\s*folder:\s*[^-]*\.\.[^-]*-->') | Should -Be $false
    }
}

# R-2026-05-18-001: path traversal guard — file: entries must be plain filenames
Describe "docs/_wiki.yml - page file paths are traversal-free (R-001)" {
    $manifestFile = Join-Path $repoRoot "docs\_wiki.yml"
    $ymlContent = if (Test-Path $manifestFile) { Get-Content $manifestFile -Raw -Encoding UTF8 } else { "" }

    It "no file: entry contains .. (path traversal prevention)" {
        ($ymlContent -match '(?m)^\s*file:\s*[''"\s]*[^''"\s]*\.\.[^''"\s]*') | Should -Be $false
    }

    It "no file: entry contains forward slash (path traversal prevention)" {
        ($ymlContent -match '(?m)^\s*file:\s*[''"\s]*[^''"\s]*/') | Should -Be $false
    }

    It "no file: entry contains backslash (path traversal prevention)" {
        ($ymlContent -match '(?m)^\s*file:\s*[''"\s]*[^''"\s]*\\') | Should -Be $false
    }
}

Describe "docs/_wiki.yml - manifest exists for docs/ folder" {
    $manifestFile = Join-Path $repoRoot "docs\_wiki.yml"
    $ymlContent = if (Test-Path $manifestFile) { Get-Content $manifestFile -Raw -Encoding UTF8 } else { "" }

    It "docs/_wiki.yml exists (wiki initialized against docs/)" {
        Test-Path $manifestFile | Should -Be $true
    }

    It "docs/_wiki.yml declares schemaVersion compound-gpid-wiki-v1" {
        ($ymlContent -match 'schemaVersion:\s*[''"]+compound-gpid-wiki-v1[''"]+') | Should -Be $true
    }

    It "docs/_wiki.yml declares folder as docs" {
        ($ymlContent -match 'folder:\s*[''"]+docs[''"]+') | Should -Be $true
    }

    It "docs/_wiki.yml has a pages section" {
        ($ymlContent -match 'pages:') | Should -Be $true
    }
}

Describe "docs/_wiki.yml - folder matches compound-gpid.context.md declaration" {
    $ctxFile   = Join-Path $repoRoot "compound-gpid.context.md"
    $ymlFile   = Join-Path $repoRoot "docs\_wiki.yml"
    $ctx       = if (Test-Path $ctxFile) { Get-Content $ctxFile -Raw -Encoding UTF8 } else { "" }
    $yml       = if (Test-Path $ymlFile) { Get-Content $ymlFile -Raw -Encoding UTF8 } else { "" }
    $ctxFolder = [regex]::Match($ctx, '<!--\s*folder:\s*(\S+?)\s*-->').Groups[1].Value
    $ymlFolder = [regex]::Match($yml, '(?m)^folder:\s*"?([^"\s]+)"?').Groups[1].Value

    It "folder in _wiki.yml matches folder declared in compound-gpid.context.md" {
        $ctxFolder | Should -Not -BeNullOrEmpty   # guard: regex must have matched
        $ymlFolder | Should -Not -BeNullOrEmpty   # guard: regex must have matched
        $ymlFolder | Should -Be $ctxFolder
    }
}

Describe "docs/workflow.md - /cg-wiki is documented in the workflow loop" {
    $workflowFile = Join-Path $repoRoot "docs\workflow.md"
    $content = Get-Content $workflowFile -Raw -Encoding UTF8

    It "mentions /cg-wiki in the workflow" {
        ($content -match '/cg-wiki') | Should -Be $true
    }

    # R-2026-05-18-015: anchor to the section heading, not just any occurrence
    It "has a dedicated ### 6b. Wiki section in the workflow loop (R-015)" {
        ($content -match '(?m)^###\s+6b\.\s+Wiki') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Bug: docs/_wiki.yml all-manual prevents auto-updates from /cg-compound
# Root cause: all 9 pages have ownership: "manual" so @cg-wiki can never
# write to any page, even when /cg-compound trigger criteria fire.
# Fix: reference.md should be ownership: "auto" with cg:auto section markers
# so command-flag/behavior changes captured by /cg-compound can be reflected
# automatically. Also: cg-compound.prompt.md Step 3c must surface the
# "Update manually" notifications from @cg-wiki back to the user.
# ---------------------------------------------------------------------------

Describe "docs/_wiki.yml - reference.md is auto-ownership for command-reference updates" {
    $manifestFile = Join-Path $repoRoot "docs\_wiki.yml"
    $ymlContent = if (Test-Path $manifestFile) { Get-Content $manifestFile -Raw -Encoding UTF8 } else { "" }

    It "docs/_wiki.yml has at least one auto-ownership page" {
        # All pages being 'manual' means @cg-wiki can never write to any page.
        # At minimum reference.md must be 'auto' so command-flag changes get auto-updated.
        ($ymlContent -match "ownership:\s*['""]?auto['""]?") | Should -Be $true
    }

    It "reference.md entry has ownership: auto" {
        # The reference page tracks command flags and defaults — exactly what
        # /cg-compound updates when new flags are added. Must be auto-owned.
        # Negative lookahead prevents crossing into the next YAML entry.
        ($ymlContent -match '(?s)id:\s*[''"]{0,1}reference[''"]{0,1}(?:(?!-\s+id:).)*?ownership:\s*[''"]{0,1}auto[''"]{0,1}') | Should -Be $true
    }

    It "reference.md entry has a managed sections entry" {
        # @cg-wiki needs sections: to know which part of the page to write.
        # Without it, auto-writes silently fail even when ownership is auto.
        # Anchor sections: inside reference entry; managed: true just needs to exist (only auto pages have it).
        ($ymlContent -match '(?s)id:\s*[''"]{0,1}reference[''"]{0,1}(?:(?!-\s+id:).)*?sections:') | Should -Be $true
        ($ymlContent -match 'managed:\s*true') | Should -Be $true
    }

    It "reference.md entry registers isolated technical and research command sections" {
        ($ymlContent -match '(?ms)^\s*-\s+id:\s*[''"]{0,1}reference[''"]{0,1}(?:(?!^\s{2}-\s+id:).)*?^\s{6}-\s+id:\s*[''"]{0,1}commands[''"]{0,1}(?:(?!^\s{2}-\s+id:).)*?managed:\s*true') | Should -Be $true
        ($ymlContent -match '(?ms)^\s*-\s+id:\s*[''"]{0,1}reference[''"]{0,1}(?:(?!^\s{2}-\s+id:).)*?^\s{6}-\s+id:\s*[''"]{0,1}research-commands[''"]{0,1}(?:(?!^\s{2}-\s+id:).)*?managed:\s*true') | Should -Be $true
        ($ymlContent -match 'shell-commands') | Should -Be $false
    }
}

Describe "docs/reference.md - contains cg:auto section markers for plugin-managed content" {
    $refFile = Join-Path $repoRoot "docs\reference.md"
    $content = if (Test-Path $refFile) { Get-Content $refFile -Raw -Encoding UTF8 } else { "" }

    It "docs/reference.md contains at least one cg:auto opening marker" {
        # cg:auto markers delimit plugin-managed sections so @cg-wiki can update
        # them without overwriting hand-authored prose around them.
        ($content -match '<!--\s*cg:auto:') | Should -Be $true
    }

    It "docs/reference.md contains cg:auto:end closing marker" {
        ($content -match '<!--\s*cg:auto:end\s*-->') | Should -Be $true
    }

    It "docs/reference.md has non-overlapping technical and research command markers" {
        ($content -match '<!--\s*cg:auto:commands\s*-->') | Should -Be $true
        ($content -match '<!--\s*cg:auto:research-commands\s*-->') | Should -Be $true
        ($content -match 'cg:auto:shell-commands') | Should -Be $false
    }
}

Describe "docs/whats-new.md - generated release ownership" {
    $manifestFile = Join-Path $repoRoot "docs\_wiki.yml"
    $pageFile = Join-Path $repoRoot "docs\whats-new.md"
    $manifest = if (Test-Path $manifestFile) { Get-Content $manifestFile -Raw -Encoding UTF8 } else { "" }
    $page = if (Test-Path $pageFile) { Get-Content $pageFile -Raw -Encoding UTF8 } else { "" }

    It "registers What's New as an auto-owned release-notes page" {
        ($manifest -match '(?s)id:\s*[''"]{0,1}whats-new[''"]{0,1}.*?ownership:\s*[''"]{0,1}auto[''"]{0,1}.*?release-notes') | Should -Be $true
    }

    It "contains the generated release marker pair and deterministic empty state" {
        ($page -match '<!--\s*cg:auto:release-notes\s*-->') | Should -Be $true
        ($page -match '<!--\s*cg:auto:end\s*-->') | Should -Be $true
        ($page -match 'No releases published yet') | Should -Be $true
    }
}

Describe "cg-skill-wiki/SKILL.md - conflict detection avoids generic token false positives" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"
    $content = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }

    It "conflict detection is based on high-signal topic keys" {
        ($content -match 'high-signal topic keys') | Should -Be $true
        ($content -match 'exact command names') | Should -Be $true
    }

    It "generic workflow/token/audit words do not block by themselves" {
        ($content -match 'Do not block on generic component words') | Should -Be $true
        ($content -match '`workflow`.*`token`.*`audit`.*`telemetry`') | Should -Be $true
    }
}

Describe "cg-compound.prompt.md - Step 3c surfaces manual-page notifications to user" {
    $compoundFile = Join-Path $repoRoot ".github\prompts\cg-compound.prompt.md"
    $content = if (Test-Path $compoundFile) { Get-Content $compoundFile -Raw -Encoding UTF8 } else { "" }

    It "Step 3c instructs agent to notify user when relevant pages are manual-ownership" {
        # Without this, 'Update it manually' notifications from @cg-wiki are
        # silently swallowed — the user never learns what docs to update.
        ($content -match '(?is)step 3c.*manual.*notif|step 3c.*notif.*manual|manual.*ownership.*echo|echo.*manual.*notif') | Should -Be $true
    }

    It "Step 3c contains the verbatim notification template text" {
        # Ensures the quoted template is present so @cg-wiki notifications
        # surface with the correct message, not a paraphrase.
        ($content -match 'Relevant update for.*manual.*ownership[.]\s*Update it manually') | Should -Be $true
    }

    It "Step 3c surfaces any notifications from @cg-wiki, not just manual-ownership" {
        # P3.9: conflict detections and other @cg-wiki messages must also be
        # surfaced — not only manual-ownership notifications.
        ($content -match '(?is)any notifications.*@cg-wiki|any.*notif.*cg-wiki') | Should -Be $true
    }
}

Describe "cg-skill-wiki/SKILL.md - Post-init Checklist is present" {
    $skillFile = Join-Path $repoRoot ".github\skills\cg-skill-wiki\SKILL.md"
    $content = if (Test-Path $skillFile) { Get-Content $skillFile -Raw -Encoding UTF8 } else { "" }

    It "SKILL.md contains a Post-init Checklist section heading" {
        # The checklist is the primary prevention mechanism for the all-manual
        # pages bug. Guards against silent deletion.
        # Heading may be '## Post-`init` Checklist' (with backticks) — use flexible pattern.
        ($content -match '(?m)^##\s+Post-.*Checklist') | Should -Be $true
    }

    It "Post-init Checklist mentions promoting ownership to auto" {
        # The checklist must remind users to upgrade the reference page to
        # auto-ownership after /cg-wiki init.
        ($content -match '(?is)Post-.*Checklist.*ownership.*auto|Post-.*Checklist.*auto.*ownership') | Should -Be $true
    }

    It "Post-init Checklist mentions cg:auto section markers" {
        # cg:auto markers are required for @cg-wiki to write to auto pages.
        # Checklist must mention them so the setup step is not skipped.
        ($content -match '(?is)Post-.*Checklist.*cg:auto:|cg:auto:.*Post-.*Checklist') | Should -Be $true
    }
}

Describe "cg-wiki.agent.md - pages order validation" {
    $agentFile = Join-Path $repoRoot ".github\agents\cg-wiki.agent.md"
    $content = Get-Content $agentFile -Raw -Encoding UTF8

    It "validates pages[].order uniqueness in Pre-Flight" {
        ($content -match 'pages\[\]\.order') | Should -Be $true
        ($content -match 'Duplicate page order') | Should -Be $true
        ($content -match 'must be unique') | Should -Be $true
    }
}
