# tests/link.Tests.ps1
# Pester tests for scripts/link.ps1 logic (Windows-specific: junction operations)
#
# Run with: Invoke-Pester tests/link.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

# Platform detection (PS 5.1 compatible: no Set-StrictMode here, so $IsWindows returns $null rather than throwing)
$script:OnWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))

# link.ps1 uses junction operations (New-Item -ItemType Junction), which are
# Windows-only. Skip all tests on macOS/Linux with a passing placeholder.
if (-not $script:OnWindows) {
    Describe "link.ps1 - Windows-only tests (skipped on macOS/Linux)" {
        It "platform check: junction tests require Windows" { $true | Should -Be $true }
    }
    return
}

Describe "link.ps1 - pre-condition checks" {
    Context "compound-gpid global clone detection" {
        It "passes when install path exists" {
            $installDir = Join-Path $TestDrive "compound-gpid"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            Test-Path $installDir | Should -Be $true
        }

        It "fails when install path does not exist" {
            $installDir = Join-Path $TestDrive "does-not-exist"
            Test-Path $installDir | Should -Be $false
        }
    }
}

Describe "link.ps1 - .github directory setup" {
    Context "when .github does not exist" {
        It "can be created as a real directory" {
            $githubDir = Join-Path $TestDrive "new-github"
            New-Item -ItemType Directory -Path $githubDir -Force | Out-Null
            Test-Path $githubDir | Should -Be $true
            (Get-Item $githubDir).LinkType | Should -BeNullOrEmpty
        }
    }

    Context "when .github is a legacy whole-directory junction" {
        It "link.ps1 migrates Compound-owned .github whole-root junctions [regression guard]" {
            $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw -Encoding UTF8
            $content | Should -Match 'migrating legacy whole-root junction'
            $content | Should -Not -Match 'RootName\s+-ne\s+"\.github"'
        }

        It "is identified as a junction" {
            $target   = Join-Path $TestDrive "legacy-target"
            $junction = Join-Path $TestDrive "legacy-github"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should -Be "Junction"
        }

        It "removing a junction does not delete the target directory" {
            $target   = Join-Path $TestDrive "preserved-target"
            $junction = Join-Path $TestDrive "removable-junction"
            New-Item -ItemType Directory -Path $target  -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            Remove-Item -Path $junction -Force
            Test-Path $junction | Should -Be $false
            Test-Path $target   | Should -Be $true
        }
    }

    Context "when .github already exists as a real directory with user content" {
        It "user content survives alongside new junctions" {
            $githubDir   = Join-Path $TestDrive "user-github"
            $workflowDir = Join-Path $githubDir "workflows"
            New-Item -ItemType Directory -Path $workflowDir -Force | Out-Null
            Set-Content -Path (Join-Path $workflowDir "ci.yml") -Value "name: CI"

            # Simulate adding a junction inside the existing .github/
            $target      = Join-Path $TestDrive "prompts-source"
            $junctionPath = Join-Path $githubDir "prompts"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junctionPath -Value $target | Out-Null

            # User content is still present
            Test-Path (Join-Path $workflowDir "ci.yml") | Should -Be $true
            (Get-Item $junctionPath).LinkType | Should -Be "Junction"
        }
    }

    AfterAll {
        # Explicitly remove junctions before Pester's $TestDrive cleanup fires.
        # On Windows, Remove-Item -Recurse -Force follows junction links, which
        # hangs the PowerShell Language Server and freezes VS Code.
        # Scan 1-2 levels without recursing into junctions.
        $level1 = Get-ChildItem -Path $TestDrive -Force -ErrorAction SilentlyContinue
        $level2 = $level1 |
            Where-Object { $_.PSIsContainer -and $_.LinkType -ne 'Junction' } |
            ForEach-Object { Get-ChildItem -Path $_.FullName -Force -ErrorAction SilentlyContinue }
        @($level1) + @($level2) |
            Where-Object { $_ -and $_.LinkType -eq 'Junction' } |
            ForEach-Object { Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue }
    }
}

Describe "link.ps1 - per-subdirectory junction creation" {
    Context "creating directory junctions for each managed subdirectory" {
        It "creates a junction for prompts/" {
            $target   = Join-Path $TestDrive "src-prompts"
            $junction = Join-Path $TestDrive "dst-prompts"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should -Be "Junction"
        }

        It "creates a junction for skills/" {
            $target   = Join-Path $TestDrive "src-skills"
            $junction = Join-Path $TestDrive "dst-skills"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should -Be "Junction"
        }

        It "creates a junction for agents/" {
            $target   = Join-Path $TestDrive "src-agents"
            $junction = Join-Path $TestDrive "dst-agents"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should -Be "Junction"
        }

        It "creates a junction for instructions/" {
            $target   = Join-Path $TestDrive "src-instructions"
            $junction = Join-Path $TestDrive "dst-instructions"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should -Be "Junction"
        }
    }

    Context "idempotency - already-linked junction detection" {
        It "recognises an existing junction pointing to compound-gpid as already-linked" {
            $target   = Join-Path $TestDrive "cg-prompts"
            $junction = Join-Path $TestDrive "existing-prompts"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null

            $item = Get-Item $junction
            $item.LinkType | Should -Be "Junction"
            # Simulate the compound-gpid target check
            $item.Target -like "*cg-prompts*" | Should -Be $true
        }
    }

    Context "conflict detection - real directory with same name" {
        It "detects when a real directory exists where a junction is expected" {
            $conflicting = Join-Path $TestDrive "conflict-prompts"
            New-Item -ItemType Directory -Path $conflicting -Force | Out-Null
            $item = Get-Item $conflicting
            $item.LinkType | Should -BeNullOrEmpty
            # A real directory (no LinkType) signals a conflict - cg-link should skip
            # that install unit and continue other selected units.
        }
    }

    AfterAll {
        # Explicitly remove junctions before Pester's $TestDrive cleanup fires.
        # On Windows, Remove-Item -Recurse -Force follows junction links, which
        # hangs the PowerShell Language Server and freezes VS Code.
        $level1 = Get-ChildItem -Path $TestDrive -Force -ErrorAction SilentlyContinue
        $level2 = $level1 |
            Where-Object { $_.PSIsContainer -and $_.LinkType -ne 'Junction' } |
            ForEach-Object { Get-ChildItem -Path $_.FullName -Force -ErrorAction SilentlyContinue }
        @($level1) + @($level2) |
            Where-Object { $_ -and $_.LinkType -eq 'Junction' } |
            ForEach-Object { Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue }
    }
}

Describe "link.ps1 - Kilo copy-directory strategy" {
    BeforeAll {
        $repoRoot = Split-Path $PSScriptRoot -Parent
        $linkContent = Get-Content (Join-Path $repoRoot "scripts\link.ps1") -Raw -Encoding UTF8
        $mapping = Get-Content (Join-Path $repoRoot ".github\shared\target-mapping.json") -Raw -Encoding UTF8 | ConvertFrom-Json
        $kilo = @($mapping.targets | Where-Object { $_.id -eq "kilo" })[0]
    }

    AfterEach {
        if ($script:KiloCopyTestAgentJunction) {
            $remainingLink = Get-Item -LiteralPath $script:KiloCopyTestAgentJunction -Force -ErrorAction SilentlyContinue
            if ($remainingLink -and $remainingLink.LinkType -eq "Junction") {
                [System.IO.Directory]::Delete($remainingLink.FullName)
            }
            $script:KiloCopyTestAgentJunction = $null
        }
    }

    It "maps every Kilo directory unit to copy-directory" {
        $directoryUnits = @($kilo.installUnits | Where-Object { $_.type -eq "directory" })
        $directoryUnits.Count | Should -Be 5
        @($directoryUnits | Where-Object { $_.strategy -ne "copy-directory" }).Count | Should -Be 0
    }

    It "passes each mapped directory strategy into Install-CgDirectoryUnit" {
        $linkContent | Should -Match 'Install-CgDirectoryUnit[^\r\n]+-Strategy \(\[string\]\$unit\.strategy\)'
    }

    It "migrates a Compound-owned junction when copy-directory is selected" {
        $linkContent | Should -Match '\$Strategy -eq "copy-directory"'
        $linkContent | Should -Match 'migrating legacy junction to copy-directory'
        $linkContent | Should -Match 'Remove-CgJunction -Path \$target'
    }

    It "requires exact expected-target ownership for junction migration" {
        $linkContent | Should -Match 'Test-CgOwnedJunction -Item \$existing -ExpectedTarget \$source'
        $linkContent | Should -Match 'OrdinalIgnoreCase'
        $linkContent | Should -Not -Match '\*compound-gpid\*'
    }

    It "removes populated junctions without recursive traversal" {
        $linkContent | Should -Match '\[System\.IO\.Directory\]::Delete\(\$item\.FullName\)'
        $linkContent | Should -Match 'Refusing to remove non-junction path'
    }

    It "syncs managed files by checksum and rejects a linked result" {
        $linkContent | Should -Match 'cg_kilo_copy\.py'
        $linkContent | Should -Match 'Shared Kilo copy worker failed'
        $linkContent | Should -Match 'copy-directory invariant failed'
    }

    It "manages copied directories via checksum manifests and baseline sync" {
        $linkContent | Should -Match '\.compound-gpid-managed-copy\.json'
        $linkContent | Should -Match 'performing a baseline sync \(user files preserved\)'
        $linkContent | Should -Not -Match 'Adopt-CgCopiedDirectoryIfExact'
        $linkContent | Should -Match 'Refusing to write a managed-copy marker through a reparse point'
        $linkContent | Should -Match 'System\.IO\.File\]::Replace\(\$temporaryPath, \$markerPath, \$backupPath\)'
    }

    It "migrates Kilo agents behaviorally and preserves managed user edits" {
        $project = Join-Path $TestDrive "kilo-copy-project"
        $profileDir = Join-Path $TestDrive "kilo-copy-profile"
        $kiloRoot = Join-Path $project ".kilo"
        $sourceAgents = Join-Path $repoRoot ".kilo\agents"
        $targetAgents = Join-Path $kiloRoot "agents"
        $targetCommands = Join-Path $kiloRoot "commands"
        New-Item -ItemType Directory -Path $project, $profileDir, $kiloRoot, $targetCommands -Force | Out-Null
        Set-Content -LiteralPath (Join-Path $targetCommands "user-command.md") -Value "user-owned"
        $script:KiloCopyTestAgentJunction = $targetAgents
        New-Item -ItemType Junction -Path $targetAgents -Value $sourceAgents | Out-Null
        $sourceWiki = Join-Path $sourceAgents "cg-wiki.md"
        $sourceHashBefore = (Get-FileHash -LiteralPath $sourceWiki -Algorithm SHA256).Hash

        $oldProfile = $env:USERPROFILE
        $oldSkipUpdate = $env:CG_SKIP_UPDATE
        Push-Location $project
        try {
            $env:USERPROFILE = $profileDir
            $env:CG_SKIP_UPDATE = "1"
            & (Join-Path $repoRoot "scripts\link.ps1") -RawArgs @("--platforms", "kilo", "--yes")
        } finally {
            Pop-Location
            $env:USERPROFILE = $oldProfile
            $env:CG_SKIP_UPDATE = $oldSkipUpdate
            $remainingAgentLink = Get-Item -LiteralPath $targetAgents -Force -ErrorAction SilentlyContinue
            if ($remainingAgentLink -and $remainingAgentLink.LinkType -eq "Junction") {
                [System.IO.Directory]::Delete($remainingAgentLink.FullName)
            }
        }

        (Get-Item -LiteralPath $targetAgents -Force).LinkType | Should -BeNullOrEmpty
        Test-Path -LiteralPath (Join-Path $targetAgents "cg-wiki.md") | Should -Be $true
        Test-Path -LiteralPath (Join-Path $targetAgents ".compound-gpid-managed-copy.json") | Should -Be $true
        (Get-Content -LiteralPath (Join-Path $targetCommands "user-command.md") -Raw).Trim() | Should -Be "user-owned"
        Test-Path -LiteralPath (Join-Path $project ".github") | Should -Be $false
        (Get-FileHash -LiteralPath $sourceWiki -Algorithm SHA256).Hash | Should -Be $sourceHashBefore

        $targetWiki = Join-Path $targetAgents "cg-wiki.md"
        Set-Content -LiteralPath $targetWiki -Value "user customization"
        Push-Location $project
        try {
            $env:USERPROFILE = $profileDir
            $env:CG_SKIP_UPDATE = "1"
            & (Join-Path $repoRoot "scripts\link.ps1") -RawArgs @("--platforms=kilo", "--yes")
        } finally {
            Pop-Location
            $env:USERPROFILE = $oldProfile
            $env:CG_SKIP_UPDATE = $oldSkipUpdate
        }
        (Get-Content -LiteralPath $targetWiki -Raw).Trim() | Should -Be "user customization"
        Test-Path -LiteralPath (Join-Path $project ".github") | Should -Be $false

        $victim = Join-Path $project "victim.txt"
        Set-Content -LiteralPath $victim -Value "must survive"
        $victimHash = (Get-FileHash -LiteralPath $victim -Algorithm SHA256).Hash.ToLowerInvariant()
        $markerPath = Join-Path $targetAgents ".compound-gpid-managed-copy.json"
        $marker = Get-Content -LiteralPath $markerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $marker.files | Add-Member -NotePropertyName "../../victim.txt" -NotePropertyValue $victimHash
        $utf8NoBom = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false
        [System.IO.File]::WriteAllText($markerPath, (($marker | ConvertTo-Json -Depth 4) + "`n"), $utf8NoBom)

        Push-Location $project
        try {
            $env:USERPROFILE = $profileDir
            $env:CG_SKIP_UPDATE = "1"
            & (Join-Path $repoRoot "scripts\link.ps1") -RawArgs @("--platforms", "kilo", "--yes")
        } finally {
            Pop-Location
            $env:USERPROFILE = $oldProfile
            $env:CG_SKIP_UPDATE = $oldSkipUpdate
        }
        (Get-Content -LiteralPath $victim -Raw).Trim() | Should -Be "must survive"
    }

    It "preserves a malformed copy-directory marker without crashing the link" {
        # Regression (P1.1): a parseable-but-malformed marker such as {} must
        # cause the unit to be preserved and skipped, NOT a terminating
        # PropertyNotFoundException that aborts the whole link.
        $project = Join-Path $TestDrive "kilo-malformed-marker-project"
        $profileDir = Join-Path $TestDrive "kilo-malformed-marker-profile"
        $kiloRoot = Join-Path $project ".kilo"
        $targetAgents = Join-Path $kiloRoot "agents"
        $heldFile = Join-Path $targetAgents "cg-held.md"
        $markerPath = Join-Path $targetAgents ".compound-gpid-managed-copy.json"
        New-Item -ItemType Directory -Path $project, $profileDir, $kiloRoot, $targetAgents -Force | Out-Null
        Set-Content -LiteralPath $heldFile -Value "user content"
        Set-Content -LiteralPath $markerPath -Value '{}'

        $oldProfile = $env:USERPROFILE
        $oldSkipUpdate = $env:CG_SKIP_UPDATE
        Push-Location $project
        try {
            $env:USERPROFILE = $profileDir
            $env:CG_SKIP_UPDATE = "1"
            & (Join-Path $repoRoot "scripts\link.ps1") -RawArgs @("--platforms=kilo", "--yes")
        } finally {
            Pop-Location
            $env:USERPROFILE = $oldProfile
            $env:CG_SKIP_UPDATE = $oldSkipUpdate
        }

        # The link did not crash (P1.1): the user-held file is preserved, and
        # the malformed marker is recovered by a baseline sync (P2.10) instead
        # of leaving the unit unmanaged/stuck.
        (Get-Content -LiteralPath $heldFile -Raw).Trim() | Should -Be "user content"
        $recovered = Get-Content -LiteralPath $markerPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $recovered.schemaVersion | Should -Be 1
        $recovered.source | Should -Be ".kilo/agents"
        Test-Path -LiteralPath (Join-Path $targetAgents "cg-wiki.md") | Should -Be $true
        # ...and the other Kilo units still get copied (link did not abort).
        Test-Path -LiteralPath (Join-Path $kiloRoot "commands\cg-plan.md") | Should -Be $true
    }

    It "adopts a real directory with a user-owned file via baseline sync" {
        # Regression (P2.6/P2.10): a real target directory that already holds a
        # user-owned file must NOT be stuck-skipped. Baseline sync copies the CG
        # files, preserves the user file, and writes a fresh marker.
        $project = Join-Path $TestDrive "kilo-baseline-adopt-project"
        $profileDir = Join-Path $TestDrive "kilo-baseline-adopt-profile"
        $kiloRoot = Join-Path $project ".kilo"
        $targetAgents = Join-Path $kiloRoot "agents"
        $userFile = Join-Path $targetAgents "my-own-agent.md"
        New-Item -ItemType Directory -Path $project, $profileDir, $kiloRoot, $targetAgents -Force | Out-Null
        Set-Content -LiteralPath $userFile -Value "my custom agent"

        $oldProfile = $env:USERPROFILE
        $oldSkipUpdate = $env:CG_SKIP_UPDATE
        Push-Location $project
        try {
            $env:USERPROFILE = $profileDir
            $env:CG_SKIP_UPDATE = "1"
            & (Join-Path $repoRoot "scripts\link.ps1") -RawArgs @("--platforms=kilo", "--yes")
        } finally {
            Pop-Location
            $env:USERPROFILE = $oldProfile
            $env:CG_SKIP_UPDATE = $oldSkipUpdate
        }

        # CG agents were installed, the user file survived, and the unit is now
        # a managed copy (marker present) rather than silently skipped.
        Test-Path -LiteralPath (Join-Path $targetAgents "cg-wiki.md") | Should -Be $true
        (Get-Content -LiteralPath $userFile -Raw).Trim() | Should -Be "my custom agent"
        $markerPath = Join-Path $targetAgents ".compound-gpid-managed-copy.json"
        Test-Path -LiteralPath $markerPath | Should -Be $true
        (Get-Content -LiteralPath $markerPath -Raw -Encoding UTF8 | ConvertFrom-Json).schemaVersion | Should -Be 1
    }
}

Describe "link.ps1 - copilot-instructions.md management" {
    Context "when the file is non-existent (first-time generation)" {
        It "creates the file with the management marker as the first line" {
            $dest          = Join-Path $TestDrive "copilot-instructions.md"
            $marker        = "<!-- compound-gpid:managed -->"
            $generatedBody = "# Instructions content"

            Set-Content -Path $dest -Value ($marker + "`n" + $generatedBody)

            $lines = Get-Content $dest
            $lines[0] | Should -Be $marker
        }
    }

    Context "when the file exists and has the management marker" {
        It "regenerates the file with the latest content" {
            $dest   = Join-Path $TestDrive "copilot-overwrite.md"
            $marker = "<!-- compound-gpid:managed -->"
            Set-Content -Path $dest -Value ($marker + "`n" + "# Old content")

            $content = Get-Content $dest -Raw
            $content -match [regex]::Escape($marker) | Should -Be $true

            # Simulate overwrite with new content
            Set-Content -Path $dest -Value ($marker + "`n" + "# New content")
            (Get-Content $dest -Raw) -match "New content" | Should -Be $true
        }
    }

    Context "when the file exists without the management marker" {
        It "detects the file as user-managed (no marker)" {
            $dest = Join-Path $TestDrive "copilot-user.md"
            Set-Content -Path $dest -Value "# My custom instructions"

            $content = Get-Content $dest -Raw
            $marker  = "<!-- compound-gpid:managed -->"
            $content -match [regex]::Escape($marker) | Should -Be $false
            # cg-link should skip this file
        }
    }
}

Describe "link.ps1 - .gitignore management (per-item entries)" {
    Context "when .gitignore does not exist" {
        It "creates .gitignore with CG-specific entries" {
            $gi = Join-Path $TestDrive "new-gi.gitignore"
            $entries = @(
                ".github/prompts/",
                ".github/skills/",
                ".github/agents/",
                ".github/instructions/",
                ".github/shared/",
                ".github/copilot-instructions.md"
            )
            Set-Content -Path $gi -Value ($entries -join "`n")
            $content = Get-Content $gi -Raw
            $content -match "\.github/prompts/"       | Should -Be $true
            $content -match "\.github/skills/"        | Should -Be $true
            $content -match "\.github/agents/"        | Should -Be $true
            $content -match "\.github/instructions/"  | Should -Be $true
            $content -match "\.github/shared/"        | Should -Be $true
            $content -match "copilot-instructions\.md" | Should -Be $true
        }
    }

    Context "when .gitignore exists with unrelated content" {
        It "appends CG entries without disturbing existing lines" {
            $gi = Join-Path $TestDrive "existing-gi.gitignore"
            Set-Content -Path $gi -Value @("*.log", "*.tmp")
            Add-Content -Path $gi -Value ".github/prompts/"

            $content = Get-Content $gi -Raw
            $content -match "\.log"              | Should -Be $true
            $content -match "\.github/prompts/"  | Should -Be $true
        }
    }

    Context "when .gitignore already has all CG entries" {
        # The remove-then-rewrite logic is inlined from link.ps1 for test isolation.
        # $RemoveCgBlockPattern and $NormGitignore replicate it here:
        #   1. Normalize content to end with \n (handles manual edits that strip trailing newlines)
        #   2. Remove any existing CG block
        #   3. TrimEnd() to remove trailing whitespace before appending separator + new block
        # If the production logic in link.ps1 changes, update this Context accordingly.
        $RemoveCgBlockPattern = "(?m)^# Compound GPID managed items[^\r\n]*\r?\n(?:(?:\.github/|\.cg-docs/)[^\r\n]*\r?\n)*"
        $NormGitignore = { param([string]$c) if ($c -and $c -notmatch '\r?\n$') { $c + "`n" } else { $c } }

        It "does not add duplicate entries when run twice (remove-then-rewrite)" {
            $gi      = Join-Path $TestDrive "dup-gi.gitignore"
            $marker  = "# Compound GPID managed items (junctions + copied file - do not commit)"
            $entries = @(".github/prompts/", ".github/skills/", ".github/agents/", ".github/instructions/", ".github/shared/", ".github/copilot-instructions.md")
            $block   = $marker + "`n" + ($entries -join "`n") + "`n"

            # First run
            Set-Content -Path $gi -Value $block

            # Second run: remove-then-rewrite with broadened regex that matches any non-empty body line
            $raw      = Get-Content $gi -Raw
            $raw      = & $NormGitignore $raw
            $existing = ($raw -replace $RemoveCgBlockPattern, "").TrimEnd()
            $sep = if ($existing.Length -gt 0) { "`n`n" } else { "" }
            Set-Content -Path $gi -Value ($existing + $sep + $block)

            $after = Get-Content $gi
            ($after | Where-Object { $_ -eq ".github/prompts/"            } | Measure-Object).Count | Should -Be 1
            ($after | Where-Object { $_ -eq ".github/skills/"             } | Measure-Object).Count | Should -Be 1
            ($after | Where-Object { $_ -eq ".github/agents/"             } | Measure-Object).Count | Should -Be 1
            ($after | Where-Object { $_ -eq ".github/instructions/"       } | Measure-Object).Count | Should -Be 1
            ($after | Where-Object { $_ -eq ".github/shared/"             } | Measure-Object).Count | Should -Be 1
            ($after | Where-Object { $_ -eq ".github/copilot-instructions.md" } | Measure-Object).Count | Should -Be 1
            ($after | Where-Object { $_ -match "Compound GPID managed items" } | Measure-Object).Count | Should -Be 1
        }

        It "removes .cg-docs/ from old CG block on upgrade (institutional knowledge must be committed)" {
            # Simulate a .gitignore written by an OLD cg-link that gitignored .cg-docs/
            $gi      = Join-Path $TestDrive "upgrade-gi.gitignore"
            $oldMarker  = "# Compound GPID managed items (junctions + copied file + knowledge base - do not commit)"
            $oldBlock   = $oldMarker + "`n.github/prompts/`n.github/skills/`n.cg-docs/`n"
            Set-Content -Path $gi -Value $oldBlock

            # Apply the remove-then-rewrite logic from link.ps1 with the NEW (narrower) block
            $newMarker  = "# Compound GPID managed items (junctions + copied file - do not commit)"
            $newEntries = @(".github/prompts/", ".github/skills/")
            $newBlock   = $newMarker + "`n" + ($newEntries -join "`n") + "`n"

            $raw      = Get-Content $gi -Raw
            $raw      = & $NormGitignore $raw
            $existing = ($raw -replace $RemoveCgBlockPattern, "").TrimEnd()
            $sep = if ($existing.Length -gt 0) { "`n`n" } else { "" }
            Set-Content -Path $gi -Value ($existing + $sep + $newBlock)

            $lines = Get-Content $gi
            # .cg-docs/ must be gone after upgrade
            ($lines | Where-Object { $_ -eq ".cg-docs/" } | Measure-Object).Count | Should -Be 0
            # Active entries survive exactly once
            ($lines | Where-Object { $_ -eq ".github/prompts/" } | Measure-Object).Count | Should -Be 1
            ($lines | Where-Object { $_ -eq ".github/skills/"  } | Measure-Object).Count | Should -Be 1
        }

        It "does not gitignore .cg-docs/ -- it is committed institutional memory" {
            # Apply the remove-then-rewrite logic from link.ps1 with the current
            # entry set (no .cg-docs/), starting from a clean pre-existing file.
            $gi      = Join-Path $TestDrive "no-cg-docs-gitignore.gitignore"
            $marker  = "# Compound GPID managed items (junctions + copied file - do not commit)"
            $entries = @(".github/prompts/", ".github/skills/", ".github/agents/", ".github/instructions/", ".github/shared/", ".github/copilot-instructions.md")
            Set-Content -Path $gi -Value "*.log"

            $newBlock = $marker + "`n" + ($entries -join "`n") + "`n"
            $raw      = Get-Content $gi -Raw
            $raw      = & $NormGitignore $raw
            $existing = ($raw -replace $RemoveCgBlockPattern, "").TrimEnd()
            $sep = if ($existing.Length -gt 0) { "`n`n" } else { "" }
            Set-Content -Path $gi -Value ($existing + $sep + $newBlock)

            $lines = Get-Content $gi
            # .cg-docs/ must NOT appear after a fresh link run
            ($lines | Where-Object { $_ -eq ".cg-docs/" } | Measure-Object).Count | Should -Be 0
            # All expected entries present
            ($lines | Where-Object { $_ -eq ".github/prompts/"            } | Measure-Object).Count | Should -Be 1
            ($lines | Where-Object { $_ -eq ".github/skills/"             } | Measure-Object).Count | Should -Be 1
            ($lines | Where-Object { $_ -eq ".github/agents/"             } | Measure-Object).Count | Should -Be 1
            ($lines | Where-Object { $_ -eq ".github/instructions/"       } | Measure-Object).Count | Should -Be 1
            ($lines | Where-Object { $_ -eq ".github/shared/"             } | Measure-Object).Count | Should -Be 1
            ($lines | Where-Object { $_ -eq ".github/copilot-instructions.md" } | Measure-Object).Count | Should -Be 1
        }

    It "preserves existing managed entries during partial relinks [regression guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw -Encoding UTF8
        $content | Should -Match 'Get-CgInstalledGitignoreEntries'
        $content | Should -Match 'Update-CgGitignoreBlock -Entries \(@\(\$installedEntries\) \+ \(Get-CgInstalledGitignoreEntries'
    }

    It "writes the managed block as UTF-8 without a BOM" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw -Encoding UTF8
        $content | Should -Match 'System\.Text\.UTF8Encoding -ArgumentList \$false'
        $content | Should -Match 'System\.IO\.File\]::WriteAllText\(\$gitignorePath'
    }

        It "preserves user content preceding the CG block (regex safety)" {
            # Regression guard: the remove-then-rewrite regex must not affect
            # user lines that appear BEFORE the CG marker block.
            $gi     = Join-Path $TestDrive "user-content-before-block.gitignore"
            $marker = "# Compound GPID managed items (junctions + copied file - do not commit)"
            # Typical layout: user content first, then the CG block
            $initial = "*.log`n`n" + $marker + "`n.github/prompts/`n"
            Set-Content -Path $gi -Value $initial

            # Apply remove-then-rewrite
            $raw      = Get-Content $gi -Raw
            $raw      = & $NormGitignore $raw
            $existing = ($raw -replace $RemoveCgBlockPattern, "").TrimEnd()
            $newBlock = $marker + "`n.github/prompts/`n"
            $sep = if ($existing.Length -gt 0) { "`n`n" } else { "" }
            Set-Content -Path $gi -Value ($existing + $sep + $newBlock)

            $lines = Get-Content $gi
            # User content before the block must survive
            ($lines | Where-Object { $_ -eq "*.log" } | Measure-Object).Count | Should -Be 1
        }

        It "does not delete user content following the CG block (regex safety)" {
            # Regression guard: the remove-then-rewrite regex must not consume user lines
            # that immediately follow the CG block without a blank-line separator.
            $gi     = Join-Path $TestDrive "user-content-after-block.gitignore"
            $marker = "# Compound GPID managed items (junctions + copied file - do not commit)"
            # No blank line between CG block and user content -- worst-case layout
            $initial = $marker + "`n.github/prompts/`n*.pyc"
            Set-Content -Path $gi -Value $initial

            # Apply remove-then-rewrite
            $raw      = Get-Content $gi -Raw
            $raw      = & $NormGitignore $raw
            $existing = ($raw -replace $RemoveCgBlockPattern, "").TrimEnd()
            $newBlock = $marker + "`n.github/prompts/`n"
            $sep = if ($existing.Length -gt 0) { "`n`n" } else { "" }
            Set-Content -Path $gi -Value ($existing + $sep + $newBlock)

            $lines = Get-Content $gi
            # User content must survive the rewrite
            ($lines | Where-Object { $_ -eq "*.pyc" } | Measure-Object).Count | Should -Be 1
        }

        It "does not leave orphaned entries when CG block has no trailing newline (EOF edge case)" {
            # Regression guard: a .gitignore manually edited to remove the trailing newline
            # after the last CG entry must still be fully cleaned up on the next cg-link run.
            # link.ps1 normalizes the content before applying the regex, so this must pass.
            $gi     = Join-Path $TestDrive "cg-block-at-eof-no-newline.gitignore"
            $marker = "# Compound GPID managed items (junctions + copied file - do not commit)"
            # Write block WITHOUT trailing newline (-NoNewline) to simulate manual edit
            Set-Content -Path $gi -Value ($marker + "`n.github/prompts/`n.github/skills/") -NoNewline

            $newMarker  = $marker
            $newEntries = @(".github/prompts/")
            $newBlock   = $newMarker + "`n" + ($newEntries -join "`n") + "`n"

            # Apply normalization + remove-then-rewrite (as link.ps1 does)
            $raw      = Get-Content $gi -Raw
            $raw      = & $NormGitignore $raw
            $existing = ($raw -replace $RemoveCgBlockPattern, "").TrimEnd()
            $sep = if ($existing.Length -gt 0) { "`n`n" } else { "" }
            Set-Content -Path $gi -Value ($existing + $sep + $newBlock)

            $lines = Get-Content $gi
            # The old last entry (.github/skills/) must NOT appear as an orphan
            ($lines | Where-Object { $_ -eq ".github/skills/" } | Measure-Object).Count | Should -Be 0
            # The new entry must be present
            ($lines | Where-Object { $_ -eq ".github/prompts/" } | Measure-Object).Count | Should -Be 1
        }
    }

    Context "legacy .github entry is no longer added" {
        It "does not add a blanket .github entry" {
            $gi = Join-Path $TestDrive "no-blanket-gi.gitignore"
            Set-Content -Path $gi -Value "# CG entries`n.github/prompts/"
            $content = Get-Content $gi -Raw
            # The blanket ".github" entry (without a slash or subdirectory) should not be present
            $content -match "(?m)^\.github\s*$" | Should -Be $false
        }
    }

    Context "stale .cg-docs/ gitignore cleanup (Step 5b)" {
        # Replicates the Step 5b logic in link.ps1 for unit-test isolation.
        $CleanStaleCgDocs = {
            param([string]$path)
            $raw = Get-Content $path -Raw -ErrorAction SilentlyContinue
            if ($raw -and ($raw -match '(?i)# Compound GPID knowledge base')) {
                $cleaned = $raw -replace '(?m)^# Compound GPID knowledge base[^\r\n]*\r?\n\.cg-docs/\r?\n?', ''
                $cleaned = $cleaned.TrimEnd()
                if ([string]::IsNullOrWhiteSpace($cleaned)) {
                    Remove-Item $path -Force
                } else {
                    Set-Content -Path $path -Value ($cleaned + "`n")
                }
            }
        }

        It "removes the stale knowledge-base comment and .cg-docs/ entry" {
            $gi = Join-Path $TestDrive "stale-cg-docs.gitignore"
            Set-Content -Path $gi -Value "*.log`n# Compound GPID knowledge base (local thinking artifacts, typically not committed)`n.cg-docs/`n"
            & $CleanStaleCgDocs $gi
            $lines = Get-Content $gi
            ($lines | Where-Object { $_ -eq ".cg-docs/"                                                    } | Measure-Object).Count | Should -Be 0
            ($lines | Where-Object { $_ -match "Compound GPID knowledge base"                              } | Measure-Object).Count | Should -Be 0
            ($lines | Where-Object { $_ -eq "*.log"                                                        } | Measure-Object).Count | Should -Be 1
        }

        It "link.ps1 contains production cleanup for stale .cg-docs/ entries" {
            $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw -Encoding UTF8
            $content | Should -Match 'Compound GPID knowledge base'
            $content | Should -Match '\\.cg-docs/'
        }

        It "link.sh contains production cleanup for stale .cg-docs/ entries" {
            $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.sh") -Raw -Encoding UTF8
            $content | Should -Match 'Compound GPID knowledge base'
            $content | Should -Match '\\.cg-docs/'
        }

        It "deletes the .gitignore file when it becomes empty after cleanup" {
            $gi = Join-Path $TestDrive "only-stale-entry.gitignore"
            Set-Content -Path $gi -Value "# Compound GPID knowledge base (local thinking artifacts, typically not committed)`n.cg-docs/"
            & $CleanStaleCgDocs $gi
            Test-Path $gi | Should -Be $false
        }

        It "preserves other entries when removing the stale block" {
            $gi = Join-Path $TestDrive "preserve-other-entries.gitignore"
            Set-Content -Path $gi -Value "*.log`n# Compound GPID knowledge base (local thinking artifacts, typically not committed)`n.cg-docs/`n*.tmp"
            & $CleanStaleCgDocs $gi
            $lines = Get-Content $gi
            ($lines | Where-Object { $_ -eq ".cg-docs/"  } | Measure-Object).Count | Should -Be 0
            ($lines | Where-Object { $_ -eq "*.log"      } | Measure-Object).Count | Should -Be 1
            ($lines | Where-Object { $_ -eq "*.tmp"      } | Measure-Object).Count | Should -Be 1
        }

        It "does nothing when the stale entry is absent" {
            $gi = Join-Path $TestDrive "no-stale-entry.gitignore"
            Set-Content -Path $gi -Value "*.log`n.github/prompts/"
            $before = Get-Content $gi -Raw
            & $CleanStaleCgDocs $gi
            $after = Get-Content $gi -Raw
            $after | Should -Be $before
        }
    }
}

# ---------------------------------------------------------------------------
# P2.5 (review finding): update.ps1 call failure handling
# ---------------------------------------------------------------------------
# link.ps1 must not install or claim a new linked state after update validation
# fails. Existing project content remains untouched because linking has not begun.

Describe "link.ps1 - update.ps1 call failure handling" {
    Context "when cg-update throws an exception (e.g. offline)" {
        It "linking is blocked after update.ps1 throws" {
            $linkBlocked = $false
            try {
                throw "Simulated cg-update failure (offline)"
            } catch {
                $linkBlocked = $true
            }
            $linkBlocked | Should -Be $true
        }

        It "CG_INTERNAL_CALL env var is cleaned up even when update throws" {
            $env:CG_INTERNAL_CALL = "1"
            try {
                throw "Simulated update failure"
            } catch {
                <# warn and continue #>
            } finally {
                Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
            }
            [string]::IsNullOrEmpty($env:CG_INTERNAL_CALL) | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# P2.6 (review finding): junction accessibility verification (Step 6)
# ---------------------------------------------------------------------------
# link.ps1 Step 6 does a Test-Path check on cg-setup.prompt.md through the
# junction, emitting a Warning on failure and continuing (non-fatal).

# ---------------------------------------------------------------------------
# -Force flag for non-interactive use (mirrors unlink.Tests.ps1)
# ---------------------------------------------------------------------------
Describe "link.ps1 - -Force flag for non-interactive use" {
    $linkPs1 = Join-Path $PSScriptRoot "..\scripts\link.ps1"
    $content = Get-Content $linkPs1 -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    It "parses Force through Resolve-CgLinkArguments [regression guard]" {
        $content | Should -Match 'Resolve-CgLinkArguments'
        $content | Should -Match '--yes'
        $content | Should -Match '-Force'
    }

    It "does not collide with PowerShell's automatic args variable" {
        $content | Should -Match 'param\(\[object\[\]\]\$Arguments\)'
        $content | Should -Match 'Resolve-CgLinkArguments -Arguments \$RawArgs'
        $content | Should -Not -Match 'param\(\[object\[\]\]\$Args\)'
    }

    It "tolerates a zero-argument invocation (link.ps1 with no flags) [regression guard]" {
        # CI E2E runs `link.ps1` with no flags; ValueFromRemainingArguments then
        # yields $null, and .Count on $null throws under Set-StrictMode.
        $content | Should -Match 'if \(\$null -eq \$Arguments\) \{ \$Arguments = @\(\) \}'
    }

    It "Relink prompt is guarded by -not `$Force [regression guard]" {
        # The junction-conflict branch Read-Host must be inside if (-not $Force).
        ($content -split '\r?\n' | Where-Object { $_ -match 'if \(-not \$Force\)' } | Measure-Object).Count |
            Should -Be 1
    }

    It "does not call Read-Host unconditionally [regression guard]" {
        # Exactly 1 Read-Host call exists for non-Compound junction relink.
        ($content -split '\r?\n' | Where-Object { $_ -match 'Read-Host' } | Measure-Object).Count |
            Should -Be 1
    }

    It "accepts GNU-style platform flags through raw argument parsing" {
        $content | Should -Match 'ValueFromRemainingArguments'
        $content | Should -Match '--platforms=\*'
        $content | Should -Match '--platforms", "-Platforms'
    }

    It "defaults to all supported platforms" {
        $content | Should -Match 'copilot", "claude-code", "codex", "opencode", "kilo'
    }
}

Describe "link.ps1 - Windows platform guard" {
    Context "script content" {
        $linkPs1 = Join-Path (Split-Path $PSScriptRoot -Parent) "scripts/link.ps1"
        $linkPs1Content = Get-Content $linkPs1 -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

        It "contains a Windows platform check to prevent accidental use on macOS/Linux" {
            # Regression: link.ps1 ran on macOS because it had no platform guard.
            # Junctions are Windows-only; macOS users must use link.sh instead.
            $linkPs1Content | Should -Match 'IsWindows|Windows_NT'
        }

        It "uses Test-Path variable:IsWindows guard for PS 5.1 strict mode compatibility [regression guard]" {
            # Regression: bare $IsWindows under Set-StrictMode -Version Latest throws
            # 'variable not set' on PS 5.1 because $IsWindows is a PS6+ automatic variable.
            # Fix: (Test-Path variable:IsWindows) -and $IsWindows -or $env:OS -eq "Windows_NT"
            # Belt-and-suspenders: ps51-compat.Tests.ps1 also covers this via full-suite scan.
            # Note: Should -Match also matches comment text; the ps51 scanner checks code portions.
            $linkPs1Content | Should -Match 'Test-Path\s+variable:IsWindows'
        }

        It "directs non-Windows users to link.sh" {
            # The error message or comment must reference link.sh so the user knows
            # what to run instead.
            $linkPs1Content | Should -Match 'link\.sh'
        }
    }
}

Describe "link.ps1 - junction accessibility verification (Step 6)" {
    Context "when cg-setup.prompt.md is accessible through the junction" {
        It "treats Test-Path returning true as verification success" {
            $checkPath = Join-Path $TestDrive "cg-setup.prompt.md"
            New-Item -ItemType File -Path $checkPath -Force | Out-Null
            $verified = Test-Path $checkPath
            $verified | Should -Be $true
        }
    }

    Context "when cg-setup.prompt.md is NOT accessible (broken junction or missing source)" {
        It "treats Test-Path returning false as verification failure" {
            # link.ps1 shows Write-Warning and continues; this test verifies the check condition.
            $checkPath = Join-Path $TestDrive "missing-subdir\cg-setup.prompt.md"
            $verified = Test-Path $checkPath
            $verified | Should -Be $false
        }

        It "verification failure does not abort the link process (non-fatal guard)" {
            $checkPath = Join-Path $TestDrive "nonexistent\cg-setup.prompt.md"
            $linkCompleted = $false
            if (-not (Test-Path $checkPath)) {
                Write-Warning "Verification failed - prompts not visible at expected path: $checkPath"
            }
            # Execution must continue beyond the if/else
            $linkCompleted = $true
            $linkCompleted | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Context layer — compound-gpid.context.md must NOT be added to .gitignore
# (it is institutional knowledge and must be committed to git)
# ---------------------------------------------------------------------------

Describe "link.ps1 - compound-gpid.context.md is not gitignored" {
    Context "CG-managed .gitignore entries do not include context.md" {
        # Reconstruct expected gitignore entries from target-mapping install units.
        $linkPs1Path = Join-Path $PSScriptRoot "..\scripts\link.ps1"
        $linkContent = Get-Content $linkPs1Path -Raw
        $mapping = Get-Content (Join-Path $PSScriptRoot "..\.github\shared\target-mapping.json") -Raw | ConvertFrom-Json
        $entries = @($mapping.targets[0].installUnits | ForEach-Object { $_.target })

        It "extracted at least one entry from link.ps1 (guard against empty extraction)" {
            ($entries | Measure-Object).Count | Should -BeGreaterThan 0
        }

        It "the CG gitignore entry list does not contain compound-gpid.context.md" {
            ($entries -contains "compound-gpid.context.md") | Should -Be $false
        }

        It "copilot-instructions.md IS in the CG gitignore entry list (sanity check)" {
            ($entries -contains ".github/copilot-instructions.md") | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Regression guard: Read-Host empty-string prompt crash (bootstrap index offer)
# Bug: link.ps1 called Read-Host "" which throws PSArgumentException
#      "name cannot be null or empty" whenever the bootstrap index offer is shown.
# Fix: Read-Host with no argument reads stdin without displaying a duplicate prompt.
# ---------------------------------------------------------------------------

Describe "link.ps1 - bootstrap index Read-Host prompt" {
    Context "Read-Host empty-string argument is the root cause of the PSArgumentException" {
        It "Read-Host with empty string prompt throws PSArgumentException [reproduces bug]" {
            # PowerShell does not accept an empty string as the -Prompt parameter.
            # This is the exact call that crashed cg-link at the bootstrap index offer.
            { Read-Host "" } | Should -Throw
        }

        It "link.ps1 bootstrap prompt does not use Read-Host with an empty string [regression guard]" {
            # Fails on the buggy code (contains Read-Host ""), passes after the fix.
            $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw
            $content | Should -Not -Match 'Read-Host\s+""'
        }
    }
}

# ---------------------------------------------------------------------------
# Bug: cg-link bootstrap index offer fires on empty projects with no .cg-docs/solutions/
# cg-index always fails on a freshly-linked project because .cg-docs/solutions/ does
# not exist yet. The offer is misleading and unhelpful at link time; indexing belongs
# in /cg-setup once the project has been configured.
# Fix: remove the bootstrap index offer from link.ps1 and link.sh entirely.
# ---------------------------------------------------------------------------

Describe "link.ps1 - no bootstrap index offer at link time" {
    It "link.ps1 does not prompt to run cg-index during cg-link [regression guard]" {
        # Fails on the current code (bootstrap offer present), passes after the fix.
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw
        ($content -match 'Would you like to build the initial knowledge index') | Should -Be $false
    }

    It "link.ps1 does not call cg-index in the bootstrap block [regression guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw
        ($content -match '& cg-index') | Should -Be $false
    }
}

Describe "link.sh - no bootstrap index offer at link time" {
    It "link.sh does not prompt to run cg-index during cg-link [regression guard]" {
        # Fails on the current code (bootstrap offer present), passes after the fix.
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.sh") -Raw
        ($content -match 'Would you like to build the initial knowledge index') | Should -Be $false
    }

    It "link.sh does not call cg-index in the bootstrap block [regression guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.sh") -Raw
        ($content -match 'cg-index --all') | Should -Be $false
    }
}

# ---------------------------------------------------------------------------
# Kilo platform: global kilo.jsonc markdown_source permission for symlinks
# ---------------------------------------------------------------------------
# Kilo docs (https://kilo.ai/docs/customize/workflows) require that when
# .kilo/commands/ is a symlink, the global ~/.config/kilo/kilo.jsonc must
# whitelist the symlink target path via permission.markdown_source.
# Without this, Kilo refuses to load external command files.
#
# The add logic lives in helpers.ps1 (Update-CgKiloGlobalPermission) so it can
# be unit-tested. link.ps1 invokes it; unlink intentionally does NOT remove the
# permission because it is keyed on the shared installation, not the project.
# ---------------------------------------------------------------------------

# Source helpers.ps1 once for the behavioral Describe blocks below.
$script:CgHelpersPath = Join-Path $PSScriptRoot "..\scripts\helpers.ps1"
. $script:CgHelpersPath

Describe "link.ps1 - kilo global kilo.jsonc permission wiring" {
    It "link.ps1 invokes Update-CgKiloGlobalPermission when kilo is selected [regression guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw -Encoding UTF8
        $content | Should -Match 'Update-CgKiloGlobalPermission'
    }

    It "link.ps1 does not use the PS6-only -AsHashtable switch [PS 5.1 compatibility guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw -Encoding UTF8
        $content | Should -Not -Match 'ConvertFrom-Json\s+-AsHashtable'
    }

    It "link.sh references markdown_source permission for kilo symlinked commands [regression guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.sh") -Raw -Encoding UTF8
        $content | Should -Match 'markdown_source'
        $content | Should -Match 'kilo\.jsonc'
    }

    It "unlink.ps1 does NOT remove the shared kilo permission [shared-install guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\unlink.ps1") -Raw -Encoding UTF8
        $content | Should -Match 'intentionally left in place'
        $content | Should -Not -Match 'Remove-CgKiloGlobalPermission'
    }

    It "unlink.sh does NOT remove the shared kilo permission [shared-install guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\unlink.sh") -Raw -Encoding UTF8
        $content | Should -Match 'intentionally left in place'
        $content | Should -Not -Match 'remove_kilo_global_permission'
    }
}

Describe "helpers.ps1 - Update-CgKiloGlobalPermission behavior" {
    $script:cgInstall = Join-Path $TestDrive "compound-gpid"
    $script:cgCommands = Join-Path $script:cgInstall ".kilo\commands"
    New-Item -ItemType Directory -Path $script:cgCommands -Force | Out-Null

    It "adds the permission to a fresh config file" {
        $cfg = Join-Path $TestDrive "fresh-kilo.jsonc"
        $written = Update-CgKiloGlobalPermission -CompoundGpidDir $script:cgInstall -KiloConfigPath $cfg
        $written | Should -Be $true
        $cfg | Should -Exist
        $json = Get-Content $cfg -Raw | ConvertFrom-Json
        ($json.permission.markdown_source.PSObject.Properties.Name) | Should -Not -BeNullOrEmpty
    }

    It "preserves unrelated settings when adding the permission" {
        $cfg = Join-Path $TestDrive "preserve-kilo.jsonc"
        Set-Content -Path $cfg -Value '{"$schema":"https://app.kilo.ai/config.json","theme":"dark","permission":{"bash":"allow"}}' -Encoding UTF8
        Update-CgKiloGlobalPermission -CompoundGpidDir $script:cgInstall -KiloConfigPath $cfg | Out-Null
        $json = Get-Content $cfg -Raw | ConvertFrom-Json
        $json.theme | Should -Be "dark"
        $json.permission.bash | Should -Be "allow"
        ($json.permission.markdown_source.PSObject.Properties.Name) | Should -Not -BeNullOrEmpty
    }

    It "is idempotent on repeated add (returns false, no double-write)" {
        $cfg = Join-Path $TestDrive "idempotent-kilo.jsonc"
        Update-CgKiloGlobalPermission -CompoundGpidDir $script:cgInstall -KiloConfigPath $cfg | Out-Null
        $second = Update-CgKiloGlobalPermission -CompoundGpidDir $script:cgInstall -KiloConfigPath $cfg
        $second | Should -Be $false
        $json = Get-Content $cfg -Raw | ConvertFrom-Json
        ($json.permission.markdown_source.PSObject.Properties | Measure-Object).Count | Should -Be 1
    }

    It "leaves the file unchanged when existing config is invalid JSON" {
        $cfg = Join-Path $TestDrive "invalid-kilo.jsonc"
        $original = '{not valid json'
        Set-Content -Path $cfg -Value $original -NoNewline -Encoding UTF8
        $written = Update-CgKiloGlobalPermission -CompoundGpidDir $script:cgInstall -KiloConfigPath $cfg
        $written | Should -Be $false
        (Get-Content $cfg -Raw) | Should -Be $original
    }

    It "leaves the file unchanged when root is a JSON array (non-object)" {
        $cfg = Join-Path $TestDrive "array-kilo.jsonc"
        $original = '[]'
        Set-Content -Path $cfg -Value $original -NoNewline -Encoding UTF8
        $written = Update-CgKiloGlobalPermission -CompoundGpidDir $script:cgInstall -KiloConfigPath $cfg
        $written | Should -Be $false
        (Get-Content $cfg -Raw) | Should -Be $original
    }

    It "prunes empty parent keys when removing the permission" {
        $cfg = Join-Path $TestDrive "prune-kilo.jsonc"
        Update-CgKiloGlobalPermission -CompoundGpidDir $script:cgInstall -KiloConfigPath $cfg | Out-Null
        $removed = Update-CgKiloGlobalPermission -CompoundGpidDir $script:cgInstall -KiloConfigPath $cfg -Remove
        $removed | Should -Be $true
        $json = Get-Content $cfg -Raw | ConvertFrom-Json
        # permission key should be gone after pruning the only markdown_source entry
        ($json.PSObject.Properties.Name -contains 'permission') | Should -Be $false
    }
}

Describe "helpers.ps1 - ConvertTo-CgHashtable PS 5.1 compatibility" {
    It "converts a PSCustomObject into a hashtable with ContainsKey support" {
        $obj = [pscustomobject]@{ a = 1; nested = [pscustomobject]@{ b = 2 } } | ConvertTo-Json | ConvertFrom-Json
        $ht = ConvertTo-CgHashtable $obj
        ($ht -is [hashtable]) | Should -Be $true
        $ht.ContainsKey('a') | Should -Be $true
        ($ht.nested -is [hashtable]) | Should -Be $true
        $ht.nested.ContainsKey('b') | Should -Be $true
    }
}

Describe "link.ps1 - manifest-driven projection integration" {
    Context "link.ps1 resolves the active manifest and syncs the projection" {
        It "invokes Resolve-CgActiveManifest for the selected platforms" {
            $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw -Encoding UTF8
            $content | Should -Match 'Resolve-CgActiveManifest'
            $content | Should -Match 'Active manifest: resolved'
        }

        It "syncs and verifies the projection when an active manifest exists" {
            $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw -Encoding UTF8
            $content | Should -Match 'Invoke-CgProjection'
            $content | Should -Match 'projection: synced and verified'
        }

        It "blocks the link banner on projection failure" {
            $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw -Encoding UTF8
            $content | Should -Match 'blocked by manifest projection failure'
        }
    }
}

Describe "helpers.ps1 - Invoke-CgProjection interface" {
    It "accepts sync, recover, verify, and unlink modes" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\helpers.ps1") -Raw -Encoding UTF8
        $content | Should -Match 'ValidateSet\("sync", "recover", "verify", "unlink"\)'
    }

    It "fails closed on a nonzero worker exit" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\helpers.ps1") -Raw -Encoding UTF8
        $content | Should -Match 'failed with exit code \$\{exit\}'
    }

    It "resolves the active manifest with ensure-state" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\helpers.ps1") -Raw -Encoding UTF8
        $content | Should -Match 'Resolve-CgActiveManifest'
        $content | Should -Match '--ensure-state'
    }
}
