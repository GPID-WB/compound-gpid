# tests/bash-scripts.Tests.ps1
# Pester tests for macOS bash scripts: install.sh, link.sh, unlink.sh, update.sh
# and the bin/ wrappers (bin/cg-link, bin/cg-unlink, bin/cg-update).
#
# Run with: Invoke-Pester tests/bash-scripts.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)
# On macOS CI, requires: pwsh + Pester 5.6.1

# Platform detection (PS 5.1-safe: $IsWindows is undefined on PS 5.1)
$script:OnWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")
$script:OnMacOS   = ($IsMacOS -eq $true)

# Bash integration tests only run on macOS (the platform that ships bash and the
# scripts target). On Windows, emit a single passing placeholder and return.
if (-not $script:OnMacOS) {
    Describe "bash-scripts (macOS-only tests, skipped on Windows)" {
        It "platform check: bash-scripts tests require macOS" { $true | Should -Be $true }
    }
    return
}

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }

# ---------------------------------------------------------------------------
# Helper: assert a file is executable
# ---------------------------------------------------------------------------
function Test-Executable {
    param([string]$Path)
    (& bash -c "[ -x '$Path' ] && echo yes || echo no" 2>/dev/null).Trim() -eq "yes"
}

# ---------------------------------------------------------------------------
# Bash script file existence and +x bit
# ---------------------------------------------------------------------------
Describe "bash-scripts - scripts exist with executable bit" {
    $bashScripts = @(
        "scripts/install.sh",
        "scripts/link.sh",
        "scripts/unlink.sh",
        "scripts/update.sh"
    )

    foreach ($script in $bashScripts) {
        $scriptPath = Join-Path $repoRoot $script
        It "$script exists" {
            Test-Path $scriptPath | Should -Be $true
        }
        It "$script is executable" {
            Test-Executable $scriptPath | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# bin/ wrappers exist with executable bit
# ---------------------------------------------------------------------------
Describe "bash-scripts - bin/ wrappers exist with executable bit" {
    $wrappers = @("bin/cg-link", "bin/cg-unlink", "bin/cg-update", "bin/cg-index")

    foreach ($wrapper in $wrappers) {
        $wrapperPath = Join-Path $repoRoot $wrapper
        It "$wrapper exists" {
            Test-Path $wrapperPath | Should -Be $true
        }
        It "$wrapper is executable" {
            Test-Executable $wrapperPath | Should -Be $true
        }
        It "$wrapper has shebang line" {
            $firstLine = & bash -c "head -1 '$wrapperPath' 2>/dev/null"
            $firstLine | Should -Match "^#!/"
        }
    }
}

# ---------------------------------------------------------------------------
# install.sh - shebang and structure
# ---------------------------------------------------------------------------
Describe "install.sh - script structure" {
    $installSh = Join-Path $repoRoot "scripts/install.sh"
    $content   = Get-Content $installSh -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    It "starts with #!/usr/bin/env bash shebang" {
        $content | Should -Match "^#!/usr/bin/env bash"
    }

    It "uses set -euo pipefail" {
        $content | Should -Match "set -euo pipefail"
    }

    It "resolves SCRIPT_DIR from script location (not pwd)" {
        $content | Should -Match 'SCRIPT_DIR=.*dirname'
    }

    It "defines COMPOUND_GPID_DIR as parent of scripts/" {
        $content | Should -Match 'COMPOUND_GPID_DIR=.*dirname.*SCRIPT_DIR'
    }

    It "verifies git is available" {
        $content | Should -Match 'command -v git'
    }

    It "tests symlink capability" {
        $content | Should -Match 'ln -s'
    }

    It "creates bin/ directory wrappers" {
        $content | Should -Match 'BIN_DIR'
        $content | Should -Match 'cg-link'
        $content | Should -Match 'cg-unlink'
        $content | Should -Match 'cg-update'
        $content | Should -Match 'cg-index'
    }

    It "initializes .cg-version" {
        $content | Should -Match '\.cg-version'
    }

    It "supports --uninstall flag" {
        $content | Should -Match '\-\-uninstall'
    }

    It "adds PATH block with CG markers" {
        $content | Should -Match 'Compound GPID'
        $content | Should -Match 'PROFILE_FILE'
    }
}

# ---------------------------------------------------------------------------
# install.sh - idempotent PATH block (live smoke test)
# ---------------------------------------------------------------------------
Describe "install.sh - PATH block is idempotent" {
    It "running install.sh twice does not duplicate the PATH block" {
        $tmpHome   = Join-Path ([System.IO.Path]::GetTempPath()) "cg-test-install-$([System.Guid]::NewGuid().ToString('N'))"
        $tmpZshrc  = Join-Path $tmpHome ".zshrc"
        $fakeShell = "/bin/zsh"

        New-Item -ItemType Directory -Path $tmpHome -Force | Out-Null

        $originalHome  = $env:HOME
        $originalShell = $env:SHELL

        $env:HOME  = $tmpHome
        $env:SHELL = $fakeShell

        # Redirect install targets so bin/ and .cg-version writes go to temp dir.
        # install.sh resolves COMPOUND_GPID_DIR from its own path, so we create
        # a minimal temp install dir that points back to the real scripts/.
        $tmpInstall = Join-Path $tmpHome ".compound-gpid"
        $tmpInstallBin     = Join-Path $tmpInstall "bin"
        $tmpInstallScripts = Join-Path $tmpInstall "scripts"
        New-Item -ItemType Directory -Path $tmpInstallBin     -Force | Out-Null
        New-Item -ItemType SymbolicLink -Path $tmpInstallScripts -Target (Join-Path $repoRoot "scripts") -Force | Out-Null

        try {
            # First run — use temp install dir
            & bash (Join-Path $tmpInstallScripts "install.sh") 2>/dev/null | Out-Null
            # Second run (idempotent)
            & bash (Join-Path $tmpInstallScripts "install.sh") 2>/dev/null | Out-Null

            $profileContent = if (Test-Path $tmpZshrc) { Get-Content $tmpZshrc -Raw } else { "" }

            # Count occurrences of the start marker
            $markerCount = ([regex]::Matches($profileContent, [regex]::Escape("# --- Compound GPID ---"))).Count
            $markerCount | Should -Be 1

            # Verify PATH entry uses $HOME-relative form, not absolute path (P3.15)
            $profileContent | Should -Match 'export PATH=.*\$HOME/'
        } finally {
            Remove-Item -Path $tmpHome    -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $tmpInstall -Recurse -Force -ErrorAction SilentlyContinue
            if ($originalHome)  { $env:HOME  = $originalHome  } else { Remove-Item Env:\HOME  -ErrorAction SilentlyContinue }
            if ($originalShell) { $env:SHELL = $originalShell } else { Remove-Item Env:\SHELL -ErrorAction SilentlyContinue }
        }
    }
}

# ---------------------------------------------------------------------------
# install.sh - migration: removes stale function-based install artifacts
# Shell functions have higher precedence than PATH entries; stale cg-*() defs
# shadow the bin/ wrappers. install.sh must remove them on every upgrade.
# Patterns mirror the 'stale' list in install.sh Step 4a — keep in sync.
# ---------------------------------------------------------------------------
Describe "install.sh - removes stale cg-* function definitions on upgrade" {
    It "strips single-line and multiline stale function defs (including cg-index), exports, and preserves non-CG content" {
        $tmpHome   = Join-Path ([System.IO.Path]::GetTempPath()) "cg-test-migrate-$([System.Guid]::NewGuid().ToString('N'))"
        $tmpZshrc  = Join-Path $tmpHome ".zshrc"
        $testShell = "/bin/zsh"

        New-Item -ItemType Directory -Path $tmpHome -Force | Out-Null

        # Seed: non-CG user content + stale artifacts (single-line, multiline cg-index, COMPOUND_GPID_DIR)
        $staleContent = @"
# My shell config
export MY_VAR="important-value"
my_func() { echo "hello"; }

# Compound GPID
export COMPOUND_GPID_DIR="`$HOME/.compound-gpid"
cg-link()   { pwsh "`$COMPOUND_GPID_DIR/scripts/link.ps1"   "`$@"; }
cg-unlink() { pwsh "`$COMPOUND_GPID_DIR/scripts/unlink.ps1" "`$@"; }
cg-update() { pwsh "`$COMPOUND_GPID_DIR/scripts/update.ps1" "`$@"; }
cg-index() {
    python3 "`$COMPOUND_GPID_DIR/scripts/cg_index.py" "`$@"
}


# Compound GPID
export COMPOUND_GPID_DIR="`$HOME/.compound-gpid"
cg-update() { git -C "`$COMPOUND_GPID_DIR" pull; }
"@
        Set-Content -Path $tmpZshrc -Value $staleContent -Encoding UTF8

        $originalHome  = $env:HOME
        $originalShell = $env:SHELL
        # Capture real profile mtime to verify test isolation (P1.7)
        $realProfile     = Join-Path $originalHome ".zshrc"
        $realMtimeBefore = if (Test-Path $realProfile) { (Get-Item $realProfile).LastWriteTime } else { $null }

        $env:HOME  = $tmpHome
        $env:SHELL = $testShell

        $tmpInstall        = Join-Path $tmpHome ".compound-gpid"
        $tmpInstallBin     = Join-Path $tmpInstall "bin"
        $tmpInstallScripts = Join-Path $tmpInstall "scripts"
        New-Item -ItemType Directory -Path $tmpInstallBin     -Force | Out-Null
        New-Item -ItemType SymbolicLink -Path $tmpInstallScripts -Target (Join-Path $repoRoot "scripts") -Force | Out-Null
        (Test-Path $tmpInstallScripts) | Should -Be $true

        try {
            & bash (Join-Path $tmpInstallScripts "install.sh") 2>/dev/null | Out-Null

            $profileContent = if (Test-Path $tmpZshrc) { Get-Content $tmpZshrc -Raw } else { "" }

            # Stale function declarations must be gone (P1.6: includes cg-index)
            ($profileContent -match 'cg-link\s*\(\)')    | Should -Be $false
            ($profileContent -match 'cg-unlink\s*\(\)')  | Should -Be $false
            ($profileContent -match 'cg-update\s*\(\)')  | Should -Be $false
            ($profileContent -match 'cg-index\s*\(\)')   | Should -Be $false
            ($profileContent -match 'COMPOUND_GPID_DIR') | Should -Be $false

            # Multiline function body lines must be gone, not just the declaration (P1.5)
            ($profileContent -match 'cg_index\.py')      | Should -Be $false

            # Non-CG user content must be preserved (P2.5)
            ($profileContent -match 'MY_VAR')            | Should -Be $true
            ($profileContent -match 'my_func')           | Should -Be $true
            ($profileContent -match 'My shell config')   | Should -Be $true

            # No triple+ blank lines left behind (P2.6)
            ($profileContent -match '\n\n\n')            | Should -Be $false

            # New fenced PATH block must be present exactly once
            $markerCount = ([regex]::Matches($profileContent, [regex]::Escape("# --- Compound GPID ---"))).Count
            $markerCount | Should -Be 1

            # Real user profile must be untouched — test isolation (P1.7)
            $realMtimeAfter = if (Test-Path $realProfile) { (Get-Item $realProfile).LastWriteTime } else { $null }
            ($realMtimeBefore -eq $realMtimeAfter) | Should -Be $true
        } finally {
            Remove-Item -Path $tmpHome    -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $tmpInstall -Recurse -Force -ErrorAction SilentlyContinue
            if ($originalHome)  { $env:HOME  = $originalHome  } else { Remove-Item Env:\HOME  -ErrorAction SilentlyContinue }
            if ($originalShell) { $env:SHELL = $originalShell } else { Remove-Item Env:\SHELL -ErrorAction SilentlyContinue }
        }
    }

    It "is a no-op on a fresh profile with no stale content" {
        $tmpHome   = Join-Path ([System.IO.Path]::GetTempPath()) "cg-test-migrate-fresh-$([System.Guid]::NewGuid().ToString('N'))"
        $tmpZshrc  = Join-Path $tmpHome ".zshrc"
        $testShell = "/bin/zsh"

        New-Item -ItemType Directory -Path $tmpHome -Force | Out-Null

        $cleanContent = @"
# User shell config
export PATH="/usr/local/bin:`$PATH"
alias ll="ls -la"
"@
        Set-Content -Path $tmpZshrc -Value $cleanContent -Encoding UTF8

        $originalHome  = $env:HOME
        $originalShell = $env:SHELL
        $env:HOME  = $tmpHome
        $env:SHELL = $testShell

        $tmpInstall        = Join-Path $tmpHome ".compound-gpid"
        $tmpInstallBin     = Join-Path $tmpInstall "bin"
        $tmpInstallScripts = Join-Path $tmpInstall "scripts"
        New-Item -ItemType Directory -Path $tmpInstallBin     -Force | Out-Null
        New-Item -ItemType SymbolicLink -Path $tmpInstallScripts -Target (Join-Path $repoRoot "scripts") -Force | Out-Null

        try {
            & bash (Join-Path $tmpInstallScripts "install.sh") 2>/dev/null | Out-Null

            $profileContent = if (Test-Path $tmpZshrc) { Get-Content $tmpZshrc -Raw } else { "" }

            # User content preserved
            ($profileContent -match 'alias ll') | Should -Be $true
            # CG block appended exactly once
            $markerCount = ([regex]::Matches($profileContent, [regex]::Escape("# --- Compound GPID ---"))).Count
            $markerCount | Should -Be 1
        } finally {
            Remove-Item -Path $tmpHome    -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $tmpInstall -Recurse -Force -ErrorAction SilentlyContinue
            if ($originalHome)  { $env:HOME  = $originalHome  } else { Remove-Item Env:\HOME  -ErrorAction SilentlyContinue }
            if ($originalShell) { $env:SHELL = $originalShell } else { Remove-Item Env:\SHELL -ErrorAction SilentlyContinue }
        }
    }

    It "migration is idempotent: running install.sh twice produces the same profile" {
        $tmpHome   = Join-Path ([System.IO.Path]::GetTempPath()) "cg-test-migrate-idem-$([System.Guid]::NewGuid().ToString('N'))"
        $tmpZshrc  = Join-Path $tmpHome ".zshrc"
        $testShell = "/bin/zsh"

        New-Item -ItemType Directory -Path $tmpHome -Force | Out-Null

        $staleContent = @"
# Compound GPID
export COMPOUND_GPID_DIR="`$HOME/.compound-gpid"
cg-link() { pwsh "`$COMPOUND_GPID_DIR/scripts/link.ps1" "`$@"; }
"@
        Set-Content -Path $tmpZshrc -Value $staleContent -Encoding UTF8

        $originalHome  = $env:HOME
        $originalShell = $env:SHELL
        $env:HOME  = $tmpHome
        $env:SHELL = $testShell

        $tmpInstall        = Join-Path $tmpHome ".compound-gpid"
        $tmpInstallBin     = Join-Path $tmpInstall "bin"
        $tmpInstallScripts = Join-Path $tmpInstall "scripts"
        New-Item -ItemType Directory -Path $tmpInstallBin     -Force | Out-Null
        New-Item -ItemType SymbolicLink -Path $tmpInstallScripts -Target (Join-Path $repoRoot "scripts") -Force | Out-Null

        try {
            & bash (Join-Path $tmpInstallScripts "install.sh") 2>/dev/null | Out-Null
            $profileAfterFirst = if (Test-Path $tmpZshrc) { Get-Content $tmpZshrc -Raw } else { "" }

            & bash (Join-Path $tmpInstallScripts "install.sh") 2>/dev/null | Out-Null
            $profileAfterSecond = if (Test-Path $tmpZshrc) { Get-Content $tmpZshrc -Raw } else { "" }

            $profileAfterFirst | Should -Be $profileAfterSecond
        } finally {
            Remove-Item -Path $tmpHome    -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $tmpInstall -Recurse -Force -ErrorAction SilentlyContinue
            if ($originalHome)  { $env:HOME  = $originalHome  } else { Remove-Item Env:\HOME  -ErrorAction SilentlyContinue }
            if ($originalShell) { $env:SHELL = $originalShell } else { Remove-Item Env:\SHELL -ErrorAction SilentlyContinue }
        }
    }

    It "profile remains valid shell syntax after migration" {
        $tmpHome   = Join-Path ([System.IO.Path]::GetTempPath()) "cg-test-migrate-syntax-$([System.Guid]::NewGuid().ToString('N'))"
        $tmpZshrc  = Join-Path $tmpHome ".zshrc"
        $testShell = "/bin/zsh"

        New-Item -ItemType Directory -Path $tmpHome -Force | Out-Null

        $staleContent = @"
export MY_CLEAN_VAR="still-here"
# Compound GPID
export COMPOUND_GPID_DIR="`$HOME/.compound-gpid"
cg-link()   { pwsh "`$COMPOUND_GPID_DIR/scripts/link.ps1"   "`$@"; }
cg-unlink() { pwsh "`$COMPOUND_GPID_DIR/scripts/unlink.ps1" "`$@"; }
"@
        Set-Content -Path $tmpZshrc -Value $staleContent -Encoding UTF8

        $originalHome  = $env:HOME
        $originalShell = $env:SHELL
        $env:HOME  = $tmpHome
        $env:SHELL = $testShell

        $tmpInstall        = Join-Path $tmpHome ".compound-gpid"
        $tmpInstallBin     = Join-Path $tmpInstall "bin"
        $tmpInstallScripts = Join-Path $tmpInstall "scripts"
        New-Item -ItemType Directory -Path $tmpInstallBin     -Force | Out-Null
        New-Item -ItemType SymbolicLink -Path $tmpInstallScripts -Target (Join-Path $repoRoot "scripts") -Force | Out-Null

        try {
            & bash (Join-Path $tmpInstallScripts "install.sh") 2>/dev/null | Out-Null

            $escapedPath = $tmpZshrc.Replace("'", "'\\''")
            $syntaxCheck = & bash -c ". '$escapedPath' && echo valid" 2>&1
            $syntaxCheck | Should -Match 'valid'
        } finally {
            Remove-Item -Path $tmpHome    -Recurse -Force -ErrorAction SilentlyContinue
            Remove-Item -Path $tmpInstall -Recurse -Force -ErrorAction SilentlyContinue
            if ($originalHome)  { $env:HOME  = $originalHome  } else { Remove-Item Env:\HOME  -ErrorAction SilentlyContinue }
            if ($originalShell) { $env:SHELL = $originalShell } else { Remove-Item Env:\SHELL -ErrorAction SilentlyContinue }
        }
    }
}

# ---------------------------------------------------------------------------
# link.sh - shebang and structure
# ---------------------------------------------------------------------------
Describe "link.sh - script structure" {
    $linkSh  = Join-Path $repoRoot "scripts/link.sh"
    $content = Get-Content $linkSh -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    It "starts with #!/usr/bin/env bash shebang" {
        $content | Should -Match "^#!/usr/bin/env bash"
    }

    It "uses set -euo pipefail" {
        $content | Should -Match "set -euo pipefail"
    }

    It "invokes update.sh with CG_INTERNAL_CALL=1" {
        $content | Should -Match "CG_INTERNAL_CALL=1.*update\.sh"
    }

    It "creates symlinks for managed directories" {
        $content | Should -Match 'ln -s'
    }

    It "manages copilot-instructions.md" {
        $content | Should -Match 'copilot-instructions'
    }

    It "updates .gitignore" {
        $content | Should -Match '\.gitignore'
    }

    It "calls generate_copilot_instructions (sourced from helpers.sh) and requires python3" {
        $content | Should -Match 'generate_copilot_instructions'
        $content | Should -Match 'helpers\.sh'
    }

    It "sources helpers.sh before the main body calls generate_copilot_instructions" {
        # helpers.sh source line must appear before first call in bash
        $sourceDefLine = [regex]::Match($content, 'helpers\.sh').Index
        $funcCallLine  = [regex]::Match($content, '(?m)GENERATED="\$\(generate_copilot_instructions').Index
        $sourceDefLine | Should -BeLessThan $funcCallLine
    }

    It "includes 'shared' in MANAGED_DIRS" {
        $content | Should -Match '"shared"'
    }

    It "Step 6 verification checks file accessibility not just directory existence" {
        # Regression: link.sh Step 6 only checked -d (directory exists), which passes
        # even when the symlink target is on cloud storage with inaccessible files.
        # Fix: check that cg-setup.prompt.md is reachable through the prompts symlink,
        # matching link.ps1's stronger Test-Path verification (link.ps1 Step 6).
        $content | Should -Match 'cg-setup\.prompt\.md'
    }
}

# ---------------------------------------------------------------------------
# unlink.sh - shebang and structure
# ---------------------------------------------------------------------------
Describe "unlink.sh - script structure" {
    $unlinkSh = Join-Path $repoRoot "scripts/unlink.sh"
    $content  = Get-Content $unlinkSh -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    It "starts with #!/usr/bin/env bash shebang" {
        $content | Should -Match "^#!/usr/bin/env bash"
    }

    It "uses set -euo pipefail" {
        $content | Should -Match "set -euo pipefail"
    }

    It "uses [ -L ] to test for symlinks" {
        $content | Should -Match '\-L '
    }

    It "uses readlink without -f flag (BSD-safe)" {
        # Ensure readlink is used but NOT readlink -f
        $content | Should -Match 'readlink '
        ($content -match 'readlink -f') | Should -Be $false
    }

    It "matches symlinks against compound-gpid" {
        $content | Should -Match 'compound-gpid'
    }

    It "removes copilot-instructions.md only when marker is present" {
        $content | Should -Match 'copilot-instructions'
        $content | Should -Match 'compound-gpid:managed'
    }

    It "removes .gitignore CG entries" {
        $content | Should -Match '\.gitignore'
    }
}

# ---------------------------------------------------------------------------
# update.sh - shebang and structure
# ---------------------------------------------------------------------------
Describe "update.sh - script structure" {
    $updateSh = Join-Path $repoRoot "scripts/update.sh"
    $content  = Get-Content $updateSh -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    It "starts with #!/usr/bin/env bash shebang" {
        $content | Should -Match "^#!/usr/bin/env bash"
    }

    It "uses set -euo pipefail" {
        $content | Should -Match "set -euo pipefail"
    }

    It "supports --list flag" {
        $content | Should -Match '\-\-list'
    }

    It "supports --fix flag" {
        $content | Should -Match '\-\-fix'
    }

    It "checks CG_INTERNAL_CALL before refreshing copilot-instructions.md" {
        $content | Should -Match 'CG_INTERNAL_CALL'
    }

    It "reads .cg-version for version mode" {
        $content | Should -Match '\.cg-version'
    }

    It "supports 'latest' mode (git pull)" {
        $content | Should -Match 'git pull'
    }

    It "supports pinned mode (git checkout tag)" {
        $content | Should -Match 'git checkout'
    }

    It "validates version format before pinning" {
        $content | Should -Match 'VERSION_ACCEPT_PATTERN'
    }

    It "uses generate_copilot_instructions (sourced from helpers.sh) for post-update refresh" {
        $content | Should -Match 'generate_copilot_instructions'
        $content | Should -Match 'helpers\.sh'
    }

    It "handles structural migration docs/ -> .cg-docs/" {
        $content | Should -Match '\.cg-docs'
    }
}

# ---------------------------------------------------------------------------
# bin/ wrappers - correct target scripts
# ---------------------------------------------------------------------------
Describe "bash-scripts - bin/ wrappers delegate to correct scripts" {
    $cases = @(
        @{ Wrapper = "bin/cg-link";   Script = "scripts/link.sh"   }
        @{ Wrapper = "bin/cg-unlink"; Script = "scripts/unlink.sh" }
        @{ Wrapper = "bin/cg-update"; Script = "scripts/update.sh" }
    )

    foreach ($case in $cases) {
        $wrapperContent = Get-Content (Join-Path $repoRoot $case.Wrapper) -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        $scriptName = $case.Script.Split("/")[-1]
        It "$($case.Wrapper) references $($case.Script)" {
            $wrapperContent | Should -Match ([regex]::Escape($scriptName))
        }
    }
}

Describe "bash-scripts - bin/cg-index wrapper content" {
    $wrapperPath    = Join-Path $repoRoot "bin/cg-index"
    $wrapperContent = Get-Content $wrapperPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    It "bin/cg-index references cg_index.py" {
        $wrapperContent | Should -Match 'cg_index\.py'
    }

    It "bin/cg-index invokes python3" {
        $wrapperContent | Should -Match '\bpython3\b'
    }

    It "bin/cg-index passes arguments via `"`$@`"" {
        $wrapperContent | Should -Match '"\$@"'
    }

    It "bin/cg-index uses SCRIPT_DIR for self-relative path" {
        $wrapperContent | Should -Match 'SCRIPT_DIR'
    }

    It "install.sh generates a cg-index wrapper" {
        $installSh = Get-Content (Join-Path $repoRoot "scripts/install.sh") -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        $installSh | Should -Match 'cg-index'
    }
}

# ---------------------------------------------------------------------------
# .gitattributes - LF line endings for bash scripts
# ---------------------------------------------------------------------------
Describe "bash-scripts - .gitattributes enforces LF for bash files" {
    $gitattributes = Join-Path $repoRoot ".gitattributes"
    $content       = if (Test-Path $gitattributes) { Get-Content $gitattributes -Raw -Encoding UTF8 } else { "" }

    It ".gitattributes exists" {
        Test-Path $gitattributes | Should -Be $true
    }

    It ".gitattributes sets eol=lf for scripts/*.sh" {
        $content | Should -Match "scripts/\*\.sh.*eol=lf"
    }

    It ".gitattributes sets eol=lf for bin/cg-* wrappers" {
        $content | Should -Match "bin/cg-\*.*eol=lf"
    }

    It ".gitattributes sets eol=lf for *.yml files" {
        $content | Should -Match "\*\.yml.*eol=lf"
    }

    It ".gitattributes sets eol=lf for *.yaml files" {
        $content | Should -Match "\*\.yaml.*eol=lf"
    }
}

# ---------------------------------------------------------------------------
# P2.7 — helpers.sh generate_copilot_instructions integration test
# Calls the ACTUAL function from helpers.sh with fixtures to verify that
# modules values containing 'r' or 'n' are extracted correctly (regression
# guard for the extract_fm_value raw-string double-backslash regex bug).
# ---------------------------------------------------------------------------

Describe "bash-scripts - helpers.sh generate_copilot_instructions" {
    $helpersSh     = Join-Path $repoRoot "scripts/helpers.sh"
    $bashAvailable = (Get-Command bash -ErrorAction SilentlyContinue) -ne $null

    if (-not $bashAvailable) {
        It "bash is available (pre-requisite for helpers.sh test)" {
            $true | Should -Be $true  # soft skip
        }
    } else {
        $tmpDir = Join-Path ([System.IO.Path]::GetTempPath()) "cg-helpers-test-$([System.IO.Path]::GetRandomFileName())"
        New-Item -ItemType Directory -Path $tmpDir -Force | Out-Null

        # Minimal charter
        $charterMd = Join-Path $tmpDir "compound-gpid.md"
        @('---', 'project-name: "Test Project"', '---', '') | Set-Content $charterMd -Encoding UTF8

        # compound-gpid.local.md with modules: research
        # 'research' contains 'r' and 'n' — the chars the broken regex excluded
        $localMd = Join-Path $tmpDir "compound-gpid.local.md"
        @(
            '---',
            'language: "R"',
            'project-type: "analysis"',
            'review-depth: "standard"',
            'modules: "research"',
            '---',
            '# Local config'
        ) | Set-Content $localMd -Encoding UTF8

        # Minimal template with the {{modules}} placeholder
        $templateFile = Join-Path $tmpDir "template.md"
        @('Active Modules: {{modules}}') | Set-Content $templateFile -Encoding UTF8

        # Bash runner: define print_error, source helpers.sh, call the function
        $bashRunner = Join-Path $tmpDir "runner.sh"
        @(
            '#!/usr/bin/env bash',
            'print_error() { echo "ERROR: $1" >&2; }',
            ". `"$helpersSh`"",
            "generate_copilot_instructions `"$templateFile`" `"$tmpDir`" `"MARKER`""
        ) | Set-Content $bashRunner -Encoding UTF8

        $output = & bash $bashRunner 2>&1
        $outputStr = $output -join "`n"

        Remove-Item $tmpDir -Recurse -ErrorAction SilentlyContinue

        It "substitutes modules: research correctly (regex must not exclude letters r/n)" {
            $outputStr | Should -Match 'Active Modules: research'
        }

        It "does not leave an unsubstituted placeholder in output" {
            $outputStr | Should -Not -Match '\{\{modules\}\}'
        }

        It "does not silently fall back to engineering for modules: research" {
            $outputStr | Should -Not -Match 'Active Modules: engineering'
        }
    }
}
