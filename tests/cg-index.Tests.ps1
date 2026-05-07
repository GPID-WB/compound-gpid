# tests/cg-index.Tests.ps1
# Pester tests for scripts/cg-index.py
#
# Tests invoke cg-index.py as a subprocess (python <script> ...) against
# temporary fixture data so the test suite remains self-contained and does
# not depend on the real .cg-docs/ directory.
#
# Compatible with Pester 4.10.1 (project standard).
# Run with: Invoke-Pester tests/cg-index.Tests.ps1 -Quiet

$repoRoot  = Split-Path $PSScriptRoot -Parent
$cgIndex   = Join-Path $repoRoot "scripts\cg_index.py"

# Expose scripts dir as env var so helper functions can access it regardless of
# PowerShell scope resolution rules (env vars are process-wide, always visible).
$env:_CG_TEST_PYDIR = ((Join-Path $repoRoot "scripts").Replace('\', '/')).Trim()

# ---------------------------------------------------------------------------
# Resolve a real Python interpreter (same probe order as bin/cg-index.cmd)
# ---------------------------------------------------------------------------
function Get-Python {
    foreach ($cmd in @("python3", "python", "py")) {
        $found = Get-Command $cmd -ErrorAction SilentlyContinue
        if (-not $found) { continue }
        try {
            $ver = & $cmd --version 2>&1
            if ("$ver".Trim() -match '^Python\s+\d') { return $cmd }
        } catch {}
    }
    return $null
}

$script:Python = Get-Python

if (-not $script:Python) {
    Describe "cg-index.py (Python not available - tests skipped)" {
        It "Python is required to run cg-index tests" { $true | Should -Be $true }
    }
    return
}

# ---------------------------------------------------------------------------
# Helper: create a minimal fixture .cg-docs/solutions/ tree under $TestDrive
# ---------------------------------------------------------------------------
function New-FixtureRoot {
    param([string]$Base)
    $solutionsDir = Join-Path $Base ".cg-docs\solutions\bugs"
    New-Item -ItemType Directory -Path $solutionsDir -Force | Out-Null
    return $Base
}

function Write-FixtureMd {
    param(
        [string]$Dir,
        [string]$Filename,
        [string]$Content
    )
    $path = Join-Path $Dir $Filename
    # PowerShell here-strings add a leading \r\n before the first content line.
    # Trim so the file starts with "---" for proper frontmatter detection.
    Set-Content -Path $path -Value $Content.TrimStart("`r`n") -Encoding UTF8 -NoNewline
    return $path
}

$script:GoodFrontmatter = @"
---
title: "Test Bug Fix"
date: 2024-03-15
status: active
tags: [pester, testing]
category: bugs
---

## Problem

This is the problem description text. It explains what went wrong and why
the fix was necessary.

## Solution

Some code fix was applied.
"@

$script:NoFrontmatter = @"
# Just a heading

No frontmatter here at all.
"@

$script:ActiveEntry = @"
---
title: "Active Entry"
date: 2024-06-01
status: active
tags: [active]
---

Active problem description text.
"@

$script:ArchivedEntry = @"
---
title: "Archived Entry"
date: 2023-01-01
status: archived
tags: [old]
---

Old problem that is no longer relevant.
"@

$script:NoStatusEntry = @"
---
title: "No Status Entry"
date: 2024-01-15
tags: [test]
---

Entry with no status field should be treated as active in DIGEST.
"@

# ---------------------------------------------------------------------------
# --version flag
# ---------------------------------------------------------------------------
Describe "cg-index.py --version" {
    It "exits 0" {
        & $script:Python $cgIndex --version 2>&1 | Out-Null
        $LASTEXITCODE | Should -Be 0
    }

    It "prints a version string" {
        $output = & $script:Python $cgIndex --version 2>&1
        "$output" | Should -Match '\d+\.\d+\.\d+'
    }
}

# ---------------------------------------------------------------------------
# Missing .cg-docs/solutions/ directory
# ---------------------------------------------------------------------------
Describe "cg-index.py - missing solutions directory" {
    It "exits 1 when .cg-docs/solutions/ does not exist" {
        $emptyRoot = Join-Path $TestDrive "empty-root"
        New-Item -ItemType Directory -Path $emptyRoot -Force | Out-Null
        & $script:Python $cgIndex --root $emptyRoot 2>&1 | Out-Null
        $LASTEXITCODE | Should -Be 1
    }

    It "prints an error to stderr when .cg-docs/solutions/ does not exist" {
        $emptyRoot = Join-Path $TestDrive "empty-root2"
        New-Item -ItemType Directory -Path $emptyRoot -Force | Out-Null
        $stderr = & $script:Python $cgIndex --root $emptyRoot 2>&1
        "$stderr" | Should -Match 'ERROR'
    }
}

# ---------------------------------------------------------------------------
# --index mode
# ---------------------------------------------------------------------------
Describe "cg-index.py --index" {
    $indexRoot = Join-Path $TestDrive "index-root"
    New-FixtureRoot $indexRoot | Out-Null
    $bugsDir = Join-Path $indexRoot ".cg-docs\solutions\bugs"
    Write-FixtureMd $bugsDir "2024-03-15-test-bug.md" $script:GoodFrontmatter | Out-Null

    $output = & $script:Python $cgIndex --index --root $indexRoot 2>&1
    $indexFile = Join-Path $indexRoot ".cg-docs\search-index.json"

    It "exits 0" {
        $LASTEXITCODE | Should -Be 0
    }

    It "creates search-index.json" {
        Test-Path $indexFile | Should -Be $true
    }

    It "search-index.json is valid JSON" {
        { Get-Content $indexFile -Raw | ConvertFrom-Json } | Should -Not -Throw
    }

    It "search-index.json contains a 'generated' field" {
        $json = Get-Content $indexFile -Raw | ConvertFrom-Json
        $json.generated | Should -Not -BeNullOrEmpty
    }

    It "search-index.json contains a 'count' field" {
        $json = Get-Content $indexFile -Raw | ConvertFrom-Json
        $json.count | Should -Be 1
    }

    It "search-index.json contains one entry with correct title" {
        $json = Get-Content $indexFile -Raw | ConvertFrom-Json
        $json.entries[0].title | Should -Be "Test Bug Fix"
    }

    It "search-index.json entry has a 'path' field" {
        $json = Get-Content $indexFile -Raw | ConvertFrom-Json
        $json.entries[0].path | Should -Not -BeNullOrEmpty
    }

    It "search-index.json entry has correct category from directory name" {
        $json = Get-Content $indexFile -Raw | ConvertFrom-Json
        $json.entries[0].category | Should -Be "bugs"
    }

    It "search-index.json entry has correct status" {
        $json = Get-Content $indexFile -Raw | ConvertFrom-Json
        $json.entries[0].status | Should -Be "active"
    }

    It "search-index.json entry does NOT contain a 'summary' field" {
        $json = Get-Content $indexFile -Raw | ConvertFrom-Json
        # search-index is metadata-only -- no full summaries
        ($json.entries[0] | Get-Member -Name summary -ErrorAction SilentlyContinue) | Should -BeNullOrEmpty
    }

    It "prints a status line to stdout" {
        "$output" | Should -Match '\[cg-index\]'
    }
}

# ---------------------------------------------------------------------------
# --index includes all statuses (active, archived, and any other)
# ---------------------------------------------------------------------------
Describe "cg-index.py --index includes all statuses" {
    $allStatusRoot = Join-Path $TestDrive "all-status-root"
    New-FixtureRoot $allStatusRoot | Out-Null
    $bugsDir = Join-Path $allStatusRoot ".cg-docs\solutions\bugs"
    Write-FixtureMd $bugsDir "2024-03-15-active.md"   $script:GoodFrontmatter | Out-Null
    Write-FixtureMd $bugsDir "2023-01-01-archived.md" $script:ArchivedEntry   | Out-Null

    & $script:Python $cgIndex --index --root $allStatusRoot 2>&1 | Out-Null
    $allStatusIndexFile = Join-Path $allStatusRoot ".cg-docs\search-index.json"

    It "includes both active and archived entries" {
        $json = Get-Content $allStatusIndexFile -Raw | ConvertFrom-Json
        $json.count | Should -Be 2
    }

    It "includes the archived entry in the index" {
        $json = Get-Content $allStatusIndexFile -Raw | ConvertFrom-Json
        $json.entries.title | Should -Contain "Archived Entry"
    }

    It "includes the active entry in the index" {
        # P3.2: verify active entry title explicitly, not just via count
        $json = Get-Content $allStatusIndexFile -Raw | ConvertFrom-Json
        $json.entries.title | Should -Contain "Test Bug Fix"
    }
}

# ---------------------------------------------------------------------------
# --digest mode
# ---------------------------------------------------------------------------
Describe "cg-index.py --digest" {
    $digestRoot = Join-Path $TestDrive "digest-root"
    New-FixtureRoot $digestRoot | Out-Null
    $bugsDir = Join-Path $digestRoot ".cg-docs\solutions\bugs"
    Write-FixtureMd $bugsDir "2024-03-15-test-bug.md"   $script:GoodFrontmatter | Out-Null
    Write-FixtureMd $bugsDir "2024-06-01-active.md"     $script:ActiveEntry      | Out-Null
    Write-FixtureMd $bugsDir "2023-01-01-archived.md"   $script:ArchivedEntry    | Out-Null
    Write-FixtureMd $bugsDir "2024-01-15-no-status.md"  $script:NoStatusEntry    | Out-Null

    $output = & $script:Python $cgIndex --digest --root $digestRoot 2>&1
    $digestFile = Join-Path $digestRoot ".cg-docs\DIGEST.md"

    It "exits 0" {
        $LASTEXITCODE | Should -Be 0
    }

    It "creates DIGEST.md" {
        Test-Path $digestFile | Should -Be $true
    }

    It "DIGEST.md contains active entries" {
        $content = Get-Content $digestFile -Raw
        $content | Should -Match "Test Bug Fix"
        $content | Should -Match "Active Entry"
    }

    It "DIGEST.md omits archived entries" {
        $content = Get-Content $digestFile -Raw
        $content | Should -Not -Match "Archived Entry"
    }

    It "DIGEST.md uses one-field-per-line format for metadata" {
        $content = Get-Content $digestFile -Raw
        $content | Should -Match "date:"
        $content | Should -Match "category:"
        $content | Should -Match "status:"
    }

    It "DIGEST.md contains a prose summary for the test bug entry" {
        $content = Get-Content $digestFile -Raw
        # Summary should come from the ## Problem section
        $content | Should -Match "problem description"
    }

    It "DIGEST.md has a header line" {
        $content = Get-Content $digestFile -Raw
        $content | Should -Match "Compound GPID"
    }

    It "DIGEST.md includes entries with no status field (treated as active)" {
        $content = Get-Content $digestFile -Raw
        $content | Should -Match "No Status Entry"
    }
}

# ---------------------------------------------------------------------------
# --all mode
# ---------------------------------------------------------------------------
Describe "cg-index.py --all" {
    $allRoot = Join-Path $TestDrive "all-root"
    New-FixtureRoot $allRoot | Out-Null
    $bugsDir = Join-Path $allRoot ".cg-docs\solutions\bugs"
    Write-FixtureMd $bugsDir "2024-03-15-test-bug.md" $script:GoodFrontmatter | Out-Null

    & $script:Python $cgIndex --all --root $allRoot 2>&1 | Out-Null

    It "creates search-index.json" {
        Test-Path (Join-Path $allRoot ".cg-docs\search-index.json") | Should -Be $true
    }

    It "creates DIGEST.md" {
        Test-Path (Join-Path $allRoot ".cg-docs\DIGEST.md") | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Default mode (no flags) == --index
# ---------------------------------------------------------------------------
Describe "cg-index.py - default mode (no flags)" {
    $defaultRoot = Join-Path $TestDrive "default-root"
    New-FixtureRoot $defaultRoot | Out-Null
    $bugsDir = Join-Path $defaultRoot ".cg-docs\solutions\bugs"
    Write-FixtureMd $bugsDir "2024-03-15-test-bug.md" $script:GoodFrontmatter | Out-Null

    & $script:Python $cgIndex --root $defaultRoot 2>&1 | Out-Null

    It "creates search-index.json by default" {
        Test-Path (Join-Path $defaultRoot ".cg-docs\search-index.json") | Should -Be $true
    }

    It "does not create DIGEST.md by default" {
        Test-Path (Join-Path $defaultRoot ".cg-docs\DIGEST.md") | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# Skipping files without frontmatter
# ---------------------------------------------------------------------------
Describe "cg-index.py - files without frontmatter" {
    $skipRoot = Join-Path $TestDrive "skip-root"
    New-FixtureRoot $skipRoot | Out-Null
    $bugsDir = Join-Path $skipRoot ".cg-docs\solutions\bugs"
    Write-FixtureMd $bugsDir "no-fm.md"              $script:NoFrontmatter   | Out-Null
    Write-FixtureMd $bugsDir "2024-03-15-good.md"    $script:GoodFrontmatter | Out-Null

    & $script:Python $cgIndex --index --root $skipRoot 2>&1 | Out-Null

    It "exits 0 even when some files have no frontmatter" {
        $LASTEXITCODE | Should -Be 0
    }

    It "index contains only the valid entry" {
        $json = Get-Content (Join-Path $skipRoot ".cg-docs\search-index.json") -Raw | ConvertFrom-Json
        $json.count | Should -Be 1
    }
}

# ---------------------------------------------------------------------------
# Idempotency: running twice produces the same output
# ---------------------------------------------------------------------------
Describe "cg-index.py - idempotency" {
    $idemRoot = Join-Path $TestDrive "idem-root"
    New-FixtureRoot $idemRoot | Out-Null
    $bugsDir = Join-Path $idemRoot ".cg-docs\solutions\bugs"
    Write-FixtureMd $bugsDir "2024-03-15-test-bug.md" $script:GoodFrontmatter | Out-Null

    & $script:Python $cgIndex --all --root $idemRoot 2>&1 | Out-Null
    $index1  = Get-Content (Join-Path $idemRoot ".cg-docs\search-index.json") -Raw
    $digest1 = Get-Content (Join-Path $idemRoot ".cg-docs\DIGEST.md") -Raw

    # Second run (same date, so generated field matches)
    & $script:Python $cgIndex --all --root $idemRoot 2>&1 | Out-Null
    $index2  = Get-Content (Join-Path $idemRoot ".cg-docs\search-index.json") -Raw
    $digest2 = Get-Content (Join-Path $idemRoot ".cg-docs\DIGEST.md") -Raw

    It "search-index.json is identical on second run" {
        $index1 | Should -Be $index2
    }

    It "DIGEST.md is identical on second run" {
        $digest1 | Should -Be $digest2
    }
}

# ---------------------------------------------------------------------------
# Frontmatter parser unit tests (via temp Python script files to avoid
# PowerShell here-string + python -c multiline/encoding issues)
# ---------------------------------------------------------------------------
Describe "cg-index.py - frontmatter parser" {
    # Helper: write lines as a Python file and run it; return trimmed stdout+stderr
    function Invoke-PyHelper {
        param([string[]]$Lines)
        $pyDir   = ($env:_CG_TEST_PYDIR).Trim()
        $pathLine = "sys.path.insert(0, '" + $pyDir + "')"
        $allLines = @("import sys", $pathLine) + $Lines
        $pyFile = Join-Path $env:TEMP ("pyfm-" + [System.Guid]::NewGuid().ToString('N') + ".py")
        Set-Content -Path $pyFile -Value ($allLines -join "`n") -Encoding UTF8 -NoNewline
        return ("$(& $script:Python $pyFile 2>&1)").Trim()
    }

    It "parses a simple title field" {
        $out = Invoke-PyHelper @(
            "from cg_index import parse_frontmatter",
            "fm = parse_frontmatter('---\ntitle: Hello World\n---\nBody')",
            "assert fm.get('title') == 'Hello World', 'Got: ' + str(fm)",
            "print('ok')"
        )
        $out | Should -Be "ok"
    }

    It "parses an inline tag list" {
        $out = Invoke-PyHelper @(
            "from cg_index import parse_frontmatter",
            "fm = parse_frontmatter('---\ntags: [pester, testing]\n---')",
            "assert fm.get('tags') == ['pester', 'testing'], 'Got: ' + str(fm)",
            "print('ok')"
        )
        $out | Should -Be "ok"
    }

    It "returns empty dict when no frontmatter block exists" {
        $out = Invoke-PyHelper @(
            "from cg_index import parse_frontmatter",
            "fm = parse_frontmatter('# Just a heading\nNo frontmatter.')",
            "assert fm == dict(), 'Got: ' + str(fm)",
            "print('ok')"
        )
        $out | Should -Be "ok"
    }
}

# ---------------------------------------------------------------------------
# Summary extractor unit tests (via temp Python script files)
# ---------------------------------------------------------------------------
Describe "cg-index.py - extract_summary" {
    function Invoke-PyHelper2 {
        param([string[]]$Lines)
        $pyDir   = ($env:_CG_TEST_PYDIR).Trim()
        $pathLine = "sys.path.insert(0, '" + $pyDir + "')"
        $allLines = @("import sys", $pathLine) + $Lines
        $pyFile = Join-Path $env:TEMP ("pysum-" + [System.Guid]::NewGuid().ToString('N') + ".py")
        Set-Content -Path $pyFile -Value ($allLines -join "`n") -Encoding UTF8 -NoNewline
        return ("$(& $script:Python $pyFile 2>&1)").Trim()
    }

    It "extracts content from ## Problem section" {
        $out = Invoke-PyHelper2 @(
            "from cg_index import extract_summary",
            "text = '---\ntitle: X\n---\n## Problem\nThis is the problem.\n## Solution\nFix.'",
            "s = extract_summary(text)",
            "assert 'problem' in s.lower(), 'Got: ' + str(s)",
            "print('ok')"
        )
        $out | Should -Be "ok"
    }

    It "falls back to first prose paragraph when no ## Problem section" {
        $out = Invoke-PyHelper2 @(
            "from cg_index import extract_summary",
            "text = '---\ntitle: X\n---\n# Title\n\nFirst prose paragraph here.\n\n## Section\nOther.'",
            "s = extract_summary(text)",
            "assert 'prose' in s.lower(), 'Got: ' + str(s)",
            "print('ok')"
        )
        $out | Should -Be "ok"
    }

    It "skips heading lines when extracting summary" {
        $out = Invoke-PyHelper2 @(
            "from cg_index import extract_summary",
            "text = '---\ntitle: X\n---\n# Title heading\nProse content only.'",
            "s = extract_summary(text)",
            "assert '# Title heading' not in s, 'Heading leaked: ' + str(s)",
            "assert 'Prose content' in s, 'Missing prose: ' + str(s)",
            "print('ok')"
        )
        $out | Should -Be "ok"
    }

    It "truncates to ~100 words with ellipsis" {
        $out = Invoke-PyHelper2 @(
            "from cg_index import extract_summary",
            "words = 'word ' * 150",
            "text = '---\ntitle: X\n---\n' + words.strip()",
            "s = extract_summary(text, max_words=100)",
            "assert s.endswith('...'), 'No ellipsis: ' + repr(s)",
            "assert len(s.split()) <= 101, 'Too long: ' + str(len(s.split()))",
            "print('ok')"
        )
        $out | Should -Be "ok"
    }

    It "excludes fenced code block content from summary" {
        $out = Invoke-PyHelper2 @(
            "from cg_index import extract_summary",
            "fence = chr(96)*3",
            "text = '---\ntitle: X\n---\n## Problem\n' + fence + '\nSHOULD_NOT_APPEAR\n' + fence + '\nProse after fence.'",
            "s = extract_summary(text)",
            "assert 'SHOULD_NOT_APPEAR' not in s, 'Fence leaked: ' + repr(s)",
            "assert 'Prose after fence' in s, 'Prose missing: ' + repr(s)",
            "print('ok')"
        )
        $out | Should -Be "ok"
    }
}
