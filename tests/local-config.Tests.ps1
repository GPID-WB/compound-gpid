# tests/local-config.Tests.ps1
# Regression guard: compound-gpid.local.md must be version-controlled so every
# checkout, worktree, and team member receives the team-shared config without
# manually copying files between machines.
#
# Expected behavior source: user-requirement — "the file should be present and
# accessible across machines and team members without manual copying".
#
# Previously the file was gitignored (".gitignore:2"), so fresh worktrees and
# clones simply had no config. These assertions fail on that state.
#
# Run with: Invoke-Pester tests/local-config.Tests.ps1 -Quiet
# Compatible with Pester 3.4+ (ships built-in on Windows)

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
$localMd  = Join-Path $repoRoot "compound-gpid.local.md"
$gitignorePath = Join-Path $repoRoot ".gitignore"
$gitignoreContent = if (Test-Path $gitignorePath) { Get-Content $gitignorePath -Raw -Encoding UTF8 } else { "" }

Describe "compound-gpid.local.md - version-controlled team config" {
    It "is NOT excluded by an uncommented .gitignore rule" {
        ($gitignoreContent -notmatch '(?m)^compound-gpid\.local\.md\s*$') | Should -Be $true
    }

    It "exists at the repository root" {
        Test-Path $localMd | Should -Be $true
    }

    It "is tracked by git (not a per-machine untracked file)" {
        # NOT a directory run / PassThru pipeline — git ls-files exits 0 only
        # when the path is tracked.
        & git -C $repoRoot ls-files --error-unmatch -- "compound-gpid.local.md" 2>$null | Out-Null
        $LASTEXITCODE | Should -Be 0
    }
}
