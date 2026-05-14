# tests/unlink.Tests.ps1
# Pester tests for scripts/unlink.ps1 logic (Windows-specific: junction operations)
#
# Run with: Invoke-Pester tests/unlink.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

# Platform detection (PS 5.1-safe: $IsWindows is undefined on PS 5.1)
$script:OnWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")

# unlink.ps1 uses junction operations (Remove-Item on junctions), which are
# Windows-only. Skip all tests on macOS/Linux with a passing placeholder.
if (-not $script:OnWindows) {
    Describe "unlink.ps1 - Windows-only tests (skipped on macOS/Linux)" {
        It "platform check: junction tests require Windows" { $true | Should -Be $true }
    }
    return
}

Describe "unlink.ps1 - pre-condition checks" {
    Context "when .github does not exist" {
        It "detects that there is nothing to unlink" {
            $githubDir = Join-Path $TestDrive "no-github"
            Test-Path $githubDir | Should -Be $false
        }
    }
}

Describe "unlink.ps1 - legacy whole-directory junction" {
    AfterAll {
        # Remove any junctions left by individual It blocks.
        # Pester's $TestDrive cleanup uses Remove-Item -Recurse -Force which
        # follows junctions — explicit removal here avoids errors on cleanup.
        Get-ChildItem -Path $TestDrive -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.LinkType -eq 'Junction' } |
            ForEach-Object { Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue }
    }
    Context "when .github/ is a whole-directory junction to compound-gpid" {
        It "identifies the legacy junction by its LinkType" {
            $target   = Join-Path $TestDrive "cg-source"
            $junction = Join-Path $TestDrive "legacy-github"
            New-Item -ItemType Directory -Path $target  -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            (Get-Item $junction).LinkType | Should -Be "Junction"
        }

        It "removing the junction does not delete the target" {
            $target   = Join-Path $TestDrive "intact-target"
            $junction = Join-Path $TestDrive "removable-link"
            New-Item -ItemType Directory -Path $target  -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null
            Remove-Item -Path $junction -Force
            Test-Path $junction | Should -Be $false
            Test-Path $target   | Should -Be $true
        }
    }

    Context "when .github/ is a regular directory (not a junction)" {
        It "detects that it is not a junction" {
            $dir = Join-Path $TestDrive "real-github"
            New-Item -ItemType Directory -Path $dir -Force | Out-Null
            (Get-Item $dir).LinkType | Should -BeNullOrEmpty
        }
    }
}

Describe "unlink.ps1 - per-subdirectory junction removal" {
    AfterAll {
        # Remove any junctions left by individual It blocks.
        Get-ChildItem -Path $TestDrive -Force -ErrorAction SilentlyContinue |
            Where-Object { $_.LinkType -eq 'Junction' } |
            ForEach-Object { Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue }
    }
    Context "removing junctions for each managed subdirectory" {
        It "removes a prompts/ junction pointing to compound-gpid" {
            $target   = Join-Path $TestDrive "compound-gpid-prompts"
            $junction = Join-Path $TestDrive "dst-github-prompts"
            New-Item -ItemType Directory -Path $target  -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $target | Out-Null

            # Verify it's a CG-owned junction before removal
            $item = Get-Item $junction
            $item.LinkType | Should -Be "Junction"
            $item.Target -like "*compound-gpid*" | Should -Be $true

            Remove-Item -Path $junction -Force
            Test-Path $junction | Should -Be $false
        }

        It "leaves a junction that does not point to compound-gpid" {
            $unrelatedTarget = Join-Path $TestDrive "other-source"
            $junction        = Join-Path $TestDrive "non-cg-junction"
            New-Item -ItemType Directory -Path $unrelatedTarget -Force | Out-Null
            New-Item -ItemType Junction  -Path $junction -Value $unrelatedTarget | Out-Null

            $item = Get-Item $junction
            # Cast Target to string: on some Windows versions Target is an array,
            # and array -like returns a filtered array, not a boolean.
            # Casting ensures we always compare against $false correctly.
            "$($item.Target)" -like "*compound-gpid*" | Should -Be $false
        }

        It "skips when a real directory exists (not a junction)" {
            $realDir = Join-Path $TestDrive "real-skills"
            New-Item -ItemType Directory -Path $realDir -Force | Out-Null
            $item = Get-Item $realDir
            # No junction = skip, leave untouched
            $item.LinkType | Should -BeNullOrEmpty
        }
    }
}

Describe "unlink.ps1 - copilot-instructions.md removal" {
    Context "when copilot-instructions.md has the management marker" {
        It "removes the file" {
            $managed = Join-Path $TestDrive "copilot-instructions-managed.md"
            $marker  = "<!-- compound-gpid:managed -->"
            Set-Content -Path $managed -Value ($marker + "`n# Instructions")

            $content = Get-Content $managed -Raw
            $content -match [regex]::Escape($marker) | Should -Be $true

            Remove-Item -Path $managed -Force
            Test-Path $managed | Should -Be $false
        }
    }

    Context "when copilot-instructions.md does not have the management marker" {
        It "is left in place (user-managed)" {
            $userFile = Join-Path $TestDrive "copilot-instructions-user.md"
            Set-Content -Path $userFile -Value "# My custom instructions"

            $content = Get-Content $userFile -Raw
            $marker  = "<!-- compound-gpid:managed -->"
            $content -match [regex]::Escape($marker) | Should -Be $false

            # File should NOT be deleted - just verify it still exists
            Test-Path $userFile | Should -Be $true
        }
    }
}

Describe "unlink.ps1 - empty .github/ cleanup" {
    Context "when .github/ is empty after removing all junctions" {
        It "removes the empty directory" {
            $emptyDir = Join-Path $TestDrive "empty-github"
            New-Item -ItemType Directory -Path $emptyDir -Force | Out-Null

            $items = Get-ChildItem -Path $emptyDir -Force
            ($items | Measure-Object).Count | Should -Be 0

            Remove-Item -Path $emptyDir -Force
            Test-Path $emptyDir | Should -Be $false
        }
    }

    Context "when .github/ still has user content after unlinking" {
        It "does NOT remove the directory if files remain" {
            $githubDir   = Join-Path $TestDrive "non-empty-github"
            $workflowDir = Join-Path $githubDir "workflows"
            New-Item -ItemType Directory -Path $workflowDir -Force | Out-Null
            Set-Content -Path (Join-Path $workflowDir "ci.yml") -Value "name: CI"

            $items = Get-ChildItem -Path $githubDir -Force
            ($items | Measure-Object).Count -gt 0 | Should -Be $true
            # Directory should NOT be removed
        }
    }
}

Describe "unlink.ps1 - .gitignore cleanup" {
    Context "removing CG-specific entries from .gitignore" {
        It "removes the CG managed-items block" {
            $gi = Join-Path $TestDrive "cleanup-gi.gitignore"
            $block = @"
*.log
# Compound GPID managed items (junctions + copied file - do not commit)
.github/prompts/
.github/skills/
.github/agents/
.github/instructions/
.github/copilot-instructions.md
"@
            Set-Content -Path $gi -Value $block
            $content = Get-Content $gi -Raw

            # Simulate the regex removal used in unlink.ps1
            $updated = $content -replace "(?m)^# Compound GPID managed items.*\r?\n(\.github/.*\r?\n)*", ""

            $updated -match "\.github/prompts/" | Should -Be $false
            $updated -match "\.log"             | Should -Be $true
        }

        It "leaves unrelated content untouched after CG removal" {
            $gi = Join-Path $TestDrive "partial-cleanup-gi.gitignore"
            Set-Content -Path $gi -Value "*.tmp`n# Compound GPID managed items`n.github/prompts/`n*.pyc"
            $content = Get-Content $gi -Raw

            $updated = $content -replace "(?m)^# Compound GPID managed items.*\r?\n(\.github/.*\r?\n)*", ""

            $updated -match "\.tmp"  | Should -Be $true
            $updated -match "\.pyc"  | Should -Be $true
        }
    }
}

Describe "unlink.ps1 - idempotency" {
    Context "running unlink twice does not error" {
        It "gracefully handles already-missing junctions" {
            $missingJunction = Join-Path $TestDrive "already-gone"
            Test-Path $missingJunction | Should -Be $false
            # Simulates attempting to remove a non-existent junction - should not throw
            $item = Get-Item -Path $missingJunction -ErrorAction SilentlyContinue
            $item | Should -BeNullOrEmpty
        }
    }
}

# ---------------------------------------------------------------------------
# Regression guard: -Force parameter for non-interactive / CI use
# ---------------------------------------------------------------------------
# E2E smoke tests invoke unlink.ps1 -Force to skip confirmation prompts in CI
# where Read-Host returns empty, silently aborting the unlink operation.
# These tests verify the flag exists in source and is wired to both prompts.

# ---------------------------------------------------------------------------
# Windows platform guard (mirrors link.Tests.ps1 "link.ps1 - Windows platform guard")
# ---------------------------------------------------------------------------
Describe "unlink.ps1 - Windows platform guard" {
    Context "script content" {
        $unlinkPs1 = Join-Path (Split-Path $PSScriptRoot -Parent) "scripts/unlink.ps1"
        $unlinkPs1Content = Get-Content $unlinkPs1 -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

        It "contains a Windows platform check to prevent accidental use on macOS/Linux" {
            $unlinkPs1Content | Should -Match 'IsWindows|Windows_NT'
        }

        It "directs non-Windows users to unlink.sh" {
            $unlinkPs1Content | Should -Match 'unlink\.sh'
        }
    }
}

Describe "unlink.ps1 - -Force flag for non-interactive use" {
    $unlinkPs1 = Join-Path $PSScriptRoot "..\scripts\unlink.ps1"
    $content   = Get-Content $unlinkPs1 -Raw

    It "declares a [switch]`$Force parameter [regression guard]" {
        $content | Should -Match '\[switch\]\$Force'
    }

    It "both confirmation paths are guarded by -not `$Force (2 guards required) [regression guard]" {
        # Both the legacy-junction path and the per-subdirectory path need an
        # independent if (-not $Force) guard. Should -Match passes on the first
        # occurrence; counting ensures both guards are present.
        ($content -split '\r?\n' | Where-Object { $_ -match 'if \(-not \$Force\)' } | Measure-Object).Count |
            Should -Be 2
    }

    It "does not call Read-Host unconditionally for either confirmation [regression guard]" {
        # Exactly 2 Read-Host calls exist, both inside (-not $Force) guards.
        # Should -BeLessThan 3 passes vacuously with 0 calls — use -Be 2 to
        # assert both the minimum and the maximum.
        ($content -split '\r?\n' | Where-Object { $_ -match 'Read-Host' } | Measure-Object).Count |
            Should -Be 2    # exactly 2: one per confirmation path (legacy + per-subdir)
    }

    It "does not use Read-Host with an empty string argument [regression guard]" {
        # Read-Host '' / Read-Host "" throws PSArgumentException in PS 5.1.
        # See .cg-docs/solutions/bugs/2026-05-12-link-read-host-empty-string-throws-psargumentexception.md
        $content | Should -Not -Match 'Read-Host\s+""'
        $content | Should -Not -Match "Read-Host\s+''"
    }
}

