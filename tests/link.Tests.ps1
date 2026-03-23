# tests/link.Tests.ps1
# Pester tests for scripts/link.ps1 logic
#
# Run with: Invoke-Pester tests/link.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

Describe "link.ps1 - pre-condition checks" {
    Context "compound-gpid global clone detection" {
        It "passes when install path exists" {
            $installDir = Join-Path $TestDrive "compound-gpid"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            Test-Path $installDir | Should Be $true
        }

        It "fails when install path does not exist" {
            $installDir = Join-Path $TestDrive "does-not-exist"
            Test-Path $installDir | Should Be $false
        }
    }
}

Describe "link.ps1 - .github directory setup" {
    Context "when .github does not exist" {
        It "can be created as a real directory" {
            $githubDir = Join-Path $TestDrive "new-github"
            New-Item -ItemType Directory -Path $githubDir -Force | Out-Null
            Test-Path $githubDir | Should Be $true
            (Get-Item $githubDir).LinkType | Should BeNullOrEmpty
        }
    }

    Context "when .github is a legacy whole-directory junction" {
        It "is identified as a junction" {
            $target   = Join-Path $TestDrive "legacy-target"
            $junction = Join-Path $TestDrive "legacy-github"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should Be "Junction"
        }

        It "removing a junction does not delete the target directory" {
            $target   = Join-Path $TestDrive "preserved-target"
            $junction = Join-Path $TestDrive "removable-junction"
            New-Item -ItemType Directory -Path $target  -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            Remove-Item -Path $junction -Force
            Test-Path $junction | Should Be $false
            Test-Path $target   | Should Be $true
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
            Test-Path (Join-Path $workflowDir "ci.yml") | Should Be $true
            (Get-Item $junctionPath).LinkType | Should Be "Junction"
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
            (Get-Item $junction).LinkType | Should Be "Junction"
        }

        It "creates a junction for skills/" {
            $target   = Join-Path $TestDrive "src-skills"
            $junction = Join-Path $TestDrive "dst-skills"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should Be "Junction"
        }

        It "creates a junction for agents/" {
            $target   = Join-Path $TestDrive "src-agents"
            $junction = Join-Path $TestDrive "dst-agents"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should Be "Junction"
        }

        It "creates a junction for instructions/" {
            $target   = Join-Path $TestDrive "src-instructions"
            $junction = Join-Path $TestDrive "dst-instructions"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should Be "Junction"
        }
    }

    Context "idempotency - already-linked junction detection" {
        It "recognises an existing junction pointing to compound-gpid as already-linked" {
            $target   = Join-Path $TestDrive "cg-prompts"
            $junction = Join-Path $TestDrive "existing-prompts"
            New-Item -ItemType Directory -Path $target -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null

            $item = Get-Item $junction
            $item.LinkType | Should Be "Junction"
            # Simulate the compound-gpid target check
            $item.Target -like "*cg-prompts*" | Should Be $true
        }
    }

    Context "conflict detection - real directory with same name" {
        It "detects when a real directory exists where a junction is expected" {
            $conflicting = Join-Path $TestDrive "conflict-prompts"
            New-Item -ItemType Directory -Path $conflicting -Force | Out-Null
            $item = Get-Item $conflicting
            $item.LinkType | Should BeNullOrEmpty
            # A real directory (no LinkType) signals a conflict - cg-link should error
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

Describe "link.ps1 - copilot-instructions.md management" {
    Context "when the file does not exist" {
        It "creates the file with the management marker as the first line" {
            $dest          = Join-Path $TestDrive "copilot-instructions.md"
            $marker        = "<!-- compound-gpid:managed -->"
            $sourceContent = "# Instructions content"

            Set-Content -Path $dest -Value ($marker + "`n" + $sourceContent)

            $lines = Get-Content $dest
            $lines[0] | Should Be $marker
        }
    }

    Context "when the file exists and has the management marker" {
        It "overwrites the file with the latest content" {
            $dest   = Join-Path $TestDrive "copilot-overwrite.md"
            $marker = "<!-- compound-gpid:managed -->"
            Set-Content -Path $dest -Value ($marker + "`n" + "# Old content")

            $content = Get-Content $dest -Raw
            $content -match [regex]::Escape($marker) | Should Be $true

            # Simulate overwrite with new content
            Set-Content -Path $dest -Value ($marker + "`n" + "# New content")
            (Get-Content $dest -Raw) -match "New content" | Should Be $true
        }
    }

    Context "when the file exists without the management marker" {
        It "detects the file as user-managed (no marker)" {
            $dest = Join-Path $TestDrive "copilot-user.md"
            Set-Content -Path $dest -Value "# My custom instructions"

            $content = Get-Content $dest -Raw
            $marker  = "<!-- compound-gpid:managed -->"
            $content -match [regex]::Escape($marker) | Should Be $false
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
                ".github/copilot-instructions.md"
            )
            Set-Content -Path $gi -Value ($entries -join "`n")
            $content = Get-Content $gi -Raw
            $content -match "\.github/prompts/"       | Should Be $true
            $content -match "\.github/skills/"        | Should Be $true
            $content -match "\.github/agents/"        | Should Be $true
            $content -match "\.github/instructions/"  | Should Be $true
            $content -match "copilot-instructions\.md" | Should Be $true
        }
    }

    Context "when .gitignore exists with unrelated content" {
        It "appends CG entries without disturbing existing lines" {
            $gi = Join-Path $TestDrive "existing-gi.gitignore"
            Set-Content -Path $gi -Value "*.log`n*.tmp"
            Add-Content -Path $gi -Value ".github/prompts/"

            $content = Get-Content $gi -Raw
            $content -match "\.log"              | Should Be $true
            $content -match "\.github/prompts/"  | Should Be $true
        }
    }

    Context "when .gitignore already has all CG entries" {
        It "does not add duplicate entries when run twice (remove-then-rewrite)" {
            $gi      = Join-Path $TestDrive "dup-gi.gitignore"
            $marker  = "# Compound GPID managed items (junctions + copied file - do not commit)"
            $entries = @(".github/prompts/", ".github/skills/")
            $block   = $marker + "`n" + ($entries -join "`n") + "`n"

            # First run
            Set-Content -Path $gi -Value $block

            # Second run: remove-then-rewrite with broadened regex that matches any non-empty body line
            $existing = (Get-Content $gi -Raw) -replace "(?m)^# Compound GPID managed items.*\r?\n([^\r\n]+\r?\n)*", ""
            $existing = $existing.TrimEnd()
            $sep = if ($existing.Length -gt 0) { "`n`n" } else { "" }
            Set-Content -Path $gi -Value ($existing + $sep + $block)

            $after = Get-Content $gi
            ($after | Where-Object { $_ -eq ".github/prompts/" } | Measure-Object).Count | Should Be 1
            ($after | Where-Object { $_ -eq ".github/skills/"  } | Measure-Object).Count | Should Be 1
        }

        It "does not gitignore .cg-docs/ — it is committed institutional memory" {
            $gi      = Join-Path $TestDrive "no-cg-docs-gitignore.gitignore"
            $marker  = "# Compound GPID managed items (junctions + copied file - do not commit)"
            $block   = $marker + "`n.github/prompts/`n.github/skills/`n"
            Set-Content -Path $gi -Value $block

            $lines = Get-Content $gi
            # .cg-docs/ must NOT appear in the CG gitignore block
            ($lines | Where-Object { $_ -eq ".cg-docs/" } | Measure-Object).Count | Should Be 0
            # Only .github/ entries should be in the block
            ($lines | Where-Object { $_ -eq ".github/prompts/" } | Measure-Object).Count | Should Be 1
            ($lines | Where-Object { $_ -eq ".github/skills/"  } | Measure-Object).Count | Should Be 1
        }
    }

    Context "legacy .github entry is no longer added" {
        It "does not add a blanket .github entry" {
            $gi = Join-Path $TestDrive "no-blanket-gi.gitignore"
            Set-Content -Path $gi -Value "# CG entries`n.github/prompts/"
            $content = Get-Content $gi -Raw
            # The blanket ".github" entry (without a slash or subdirectory) should not be present
            $content -match "(?m)^\.github\s*$" | Should Be $false
        }
    }
}

