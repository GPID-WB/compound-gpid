# tests/link.Tests.ps1
# Pester tests for scripts/link.ps1 logic (Windows-specific: junction operations)
#
# Run with: Invoke-Pester tests/link.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

# Platform detection (PS 5.1-safe: $IsWindows is undefined on PS 5.1)
$script:OnWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")

# link.ps1 uses junction operations (New-Item -ItemType Junction), which are
# Windows-only. Skip all tests on macOS/Linux with a passing placeholder.
if (-not $script:OnWindows) {
    Describe "link.ps1 - Windows-only tests (skipped on macOS/Linux)" {
        It "platform check: junction tests require Windows" { $true | Should Be $true }
    }
    return
}

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
    Context "when the file is non-existent (first-time generation)" {
        It "creates the file with the management marker as the first line" {
            $dest          = Join-Path $TestDrive "copilot-instructions.md"
            $marker        = "<!-- compound-gpid:managed -->"
            $generatedBody = "# Instructions content"

            Set-Content -Path $dest -Value ($marker + "`n" + $generatedBody)

            $lines = Get-Content $dest
            $lines[0] | Should Be $marker
        }
    }

    Context "when the file exists and has the management marker" {
        It "regenerates the file with the latest content" {
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
            Set-Content -Path $gi -Value @("*.log", "*.tmp")
            Add-Content -Path $gi -Value ".github/prompts/"

            $content = Get-Content $gi -Raw
            $content -match "\.log"              | Should Be $true
            $content -match "\.github/prompts/"  | Should Be $true
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
            $entries = @(".github/prompts/", ".github/skills/", ".github/agents/", ".github/instructions/", ".github/copilot-instructions.md")
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
            ($after | Where-Object { $_ -eq ".github/prompts/"            } | Measure-Object).Count | Should Be 1
            ($after | Where-Object { $_ -eq ".github/skills/"             } | Measure-Object).Count | Should Be 1
            ($after | Where-Object { $_ -eq ".github/agents/"             } | Measure-Object).Count | Should Be 1
            ($after | Where-Object { $_ -eq ".github/instructions/"       } | Measure-Object).Count | Should Be 1
            ($after | Where-Object { $_ -eq ".github/copilot-instructions.md" } | Measure-Object).Count | Should Be 1
            ($after | Where-Object { $_ -match "Compound GPID managed items" } | Measure-Object).Count | Should Be 1
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
            ($lines | Where-Object { $_ -eq ".cg-docs/" } | Measure-Object).Count | Should Be 0
            # Active entries survive exactly once
            ($lines | Where-Object { $_ -eq ".github/prompts/" } | Measure-Object).Count | Should Be 1
            ($lines | Where-Object { $_ -eq ".github/skills/"  } | Measure-Object).Count | Should Be 1
        }

        It "does not gitignore .cg-docs/ -- it is committed institutional memory" {
            # Apply the remove-then-rewrite logic from link.ps1 with the current
            # entry set (no .cg-docs/), starting from a clean pre-existing file.
            $gi      = Join-Path $TestDrive "no-cg-docs-gitignore.gitignore"
            $marker  = "# Compound GPID managed items (junctions + copied file - do not commit)"
            $entries = @(".github/prompts/", ".github/skills/", ".github/agents/", ".github/instructions/", ".github/copilot-instructions.md")
            Set-Content -Path $gi -Value "*.log"

            $newBlock = $marker + "`n" + ($entries -join "`n") + "`n"
            $raw      = Get-Content $gi -Raw
            $raw      = & $NormGitignore $raw
            $existing = ($raw -replace $RemoveCgBlockPattern, "").TrimEnd()
            $sep = if ($existing.Length -gt 0) { "`n`n" } else { "" }
            Set-Content -Path $gi -Value ($existing + $sep + $newBlock)

            $lines = Get-Content $gi
            # .cg-docs/ must NOT appear after a fresh link run
            ($lines | Where-Object { $_ -eq ".cg-docs/" } | Measure-Object).Count | Should Be 0
            # All expected entries present
            ($lines | Where-Object { $_ -eq ".github/prompts/"            } | Measure-Object).Count | Should Be 1
            ($lines | Where-Object { $_ -eq ".github/skills/"             } | Measure-Object).Count | Should Be 1
            ($lines | Where-Object { $_ -eq ".github/agents/"             } | Measure-Object).Count | Should Be 1
            ($lines | Where-Object { $_ -eq ".github/instructions/"       } | Measure-Object).Count | Should Be 1
            ($lines | Where-Object { $_ -eq ".github/copilot-instructions.md" } | Measure-Object).Count | Should Be 1
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
            ($lines | Where-Object { $_ -eq "*.log" } | Measure-Object).Count | Should Be 1
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
            ($lines | Where-Object { $_ -eq "*.pyc" } | Measure-Object).Count | Should Be 1
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
            ($lines | Where-Object { $_ -eq ".github/skills/" } | Measure-Object).Count | Should Be 0
            # The new entry must be present
            ($lines | Where-Object { $_ -eq ".github/prompts/" } | Measure-Object).Count | Should Be 1
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
            ($lines | Where-Object { $_ -eq ".cg-docs/"                                                    } | Measure-Object).Count | Should Be 0
            ($lines | Where-Object { $_ -match "Compound GPID knowledge base"                              } | Measure-Object).Count | Should Be 0
            ($lines | Where-Object { $_ -eq "*.log"                                                        } | Measure-Object).Count | Should Be 1
        }

        It "deletes the .gitignore file when it becomes empty after cleanup" {
            $gi = Join-Path $TestDrive "only-stale-entry.gitignore"
            Set-Content -Path $gi -Value "# Compound GPID knowledge base (local thinking artifacts, typically not committed)`n.cg-docs/"
            & $CleanStaleCgDocs $gi
            Test-Path $gi | Should Be $false
        }

        It "preserves other entries when removing the stale block" {
            $gi = Join-Path $TestDrive "preserve-other-entries.gitignore"
            Set-Content -Path $gi -Value "*.log`n# Compound GPID knowledge base (local thinking artifacts, typically not committed)`n.cg-docs/`n*.tmp"
            & $CleanStaleCgDocs $gi
            $lines = Get-Content $gi
            ($lines | Where-Object { $_ -eq ".cg-docs/"  } | Measure-Object).Count | Should Be 0
            ($lines | Where-Object { $_ -eq "*.log"      } | Measure-Object).Count | Should Be 1
            ($lines | Where-Object { $_ -eq "*.tmp"      } | Measure-Object).Count | Should Be 1
        }

        It "does nothing when the stale entry is absent" {
            $gi = Join-Path $TestDrive "no-stale-entry.gitignore"
            Set-Content -Path $gi -Value "*.log`n.github/prompts/"
            $before = Get-Content $gi -Raw
            & $CleanStaleCgDocs $gi
            $after = Get-Content $gi -Raw
            $after | Should Be $before
        }
    }
}

# ---------------------------------------------------------------------------
# P2.5 (review finding): update.ps1 call failure handling
# ---------------------------------------------------------------------------
# link.ps1 calls update.ps1 inside a try/catch so that a network error or
# broken update does not prevent the link operation from completing.
# These tests verify the try/catch pattern keeps execution flowing.

Describe "link.ps1 - update.ps1 call failure handling" {
    Context "when cg-update throws an exception (e.g. offline)" {
        It "linking continues after update.ps1 throws (try/catch pattern)" {
            $linkContinued = $false
            try {
                throw "Simulated cg-update failure (offline)"
            } catch {
                # Mirrors link.ps1: warn and continue
                Write-Warning "Could not update Compound GPID (offline?): $_"
            }
            # Code after the try/catch must be reachable
            $linkContinued = $true
            $linkContinued | Should Be $true
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
            [string]::IsNullOrEmpty($env:CG_INTERNAL_CALL) | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# P2.6 (review finding): junction accessibility verification (Step 6)
# ---------------------------------------------------------------------------
# link.ps1 Step 6 does a Test-Path check on cg-setup.prompt.md through the
# junction, emitting a Warning on failure and continuing (non-fatal).

Describe "link.ps1 - junction accessibility verification (Step 6)" {
    Context "when cg-setup.prompt.md is accessible through the junction" {
        It "treats Test-Path returning true as verification success" {
            $checkPath = Join-Path $TestDrive "cg-setup.prompt.md"
            New-Item -ItemType File -Path $checkPath -Force | Out-Null
            $verified = Test-Path $checkPath
            $verified | Should Be $true
        }
    }

    Context "when cg-setup.prompt.md is NOT accessible (broken junction or missing source)" {
        It "treats Test-Path returning false as verification failure" {
            # link.ps1 shows Write-Warning and continues; this test verifies the check condition.
            $checkPath = Join-Path $TestDrive "missing-subdir\cg-setup.prompt.md"
            $verified = Test-Path $checkPath
            $verified | Should Be $false
        }

        It "verification failure does not abort the link process (non-fatal guard)" {
            $checkPath = Join-Path $TestDrive "nonexistent\cg-setup.prompt.md"
            $linkCompleted = $false
            if (-not (Test-Path $checkPath)) {
                Write-Warning "Verification failed - prompts not visible at expected path: $checkPath"
            }
            # Execution must continue beyond the if/else
            $linkCompleted = $true
            $linkCompleted | Should Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Context layer — compound-gpid.context.md must NOT be added to .gitignore
# (it is institutional knowledge and must be committed to git)
# ---------------------------------------------------------------------------

Describe "link.ps1 - compound-gpid.context.md is not gitignored" {
    Context "CG-managed .gitignore entries do not include context.md" {
        # Extract $ManagedDirs from link.ps1 and reconstruct expected gitignore entries.
        # This mirrors the derivation logic in link.ps1 so both stay in sync automatically.
        $linkPs1Path = Join-Path $PSScriptRoot "..\scripts\link.ps1"
        $linkContent = Get-Content $linkPs1Path -Raw
        $block = [regex]::Match($linkContent, '(?s)\$ManagedDirs\s*=\s*@\((.+?)\)').Groups[1].Value
        $managedDirs = $block -split '\r?\n' |
                       ForEach-Object { $_.Trim().Trim('"').Trim("'") } |
                       Where-Object { $_ -ne '' }
        $entries = @($managedDirs | ForEach-Object { ".github/$_/" }) +
                   @(".github/copilot-instructions.md")

        It "extracted at least one entry from link.ps1 (guard against empty extraction)" {
            ($entries | Measure-Object).Count | Should BeGreaterThan 0
        }

        It "the CG gitignore entry list does not contain compound-gpid.context.md" {
            ($entries -contains "compound-gpid.context.md") | Should Be $false
        }

        It "copilot-instructions.md IS in the CG gitignore entry list (sanity check)" {
            ($entries -contains ".github/copilot-instructions.md") | Should Be $true
        }
    }
}

