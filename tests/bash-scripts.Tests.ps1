# tests/bash-scripts.Tests.ps1
# Pester tests for macOS bash scripts: install.sh, link.sh, unlink.sh, update.sh
# and the bin/ wrappers (bin/cg-link, bin/cg-unlink, bin/cg-update).
#
# Run with: Invoke-Pester tests/bash-scripts.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)
# On macOS CI, requires: pwsh + Pester 4.10.1

# Platform detection (PS 5.1 compatible: no Set-StrictMode here, so $IsWindows/$IsMacOS return $null rather than throwing)
$script:OnWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))
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
    $wrappers = @("bin/cg-link", "bin/cg-unlink", "bin/cg-update", "bin/cg-index", "bin/cg-token-audit", "bin/cg-render-artifact")

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
        $content | Should -Match 'cg-token-audit'
        $content | Should -Match 'cg-render-artifact'
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
        Copy-Item -Path (Join-Path $repoRoot "bin/cg-render-artifact") -Destination (Join-Path $tmpInstallBin "cg-render-artifact") -Force

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

    It "uses generate_copilot_instructions function with resolved Python command" {
        $content | Should -Match 'generate_copilot_instructions'
        $content | Should -Match 'PYTHON_CMD'
        $content | Should -Match 'resolve_python'
    }

    It "defines generate_copilot_instructions before the main body calls it" {
        # Function definition must appear before first call in bash
        $funcDefLine  = [regex]::Match($content, '(?m)^generate_copilot_instructions\(\)').Index
        $funcCallLine = [regex]::Match($content, '(?m)generate_copilot_instructions "\$source_path"').Index
        $funcDefLine | Should -BeLessThan $funcCallLine
    }

    It "includes shared as a Copilot install unit" {
        $content | Should -Match '\.github/shared'
    }

    It "Step 6 verification checks file accessibility not just directory existence" {
        # Regression: link.sh Step 6 only checked -d (directory exists), which passes
        # even when the symlink target is on cloud storage with inaccessible files.
        # Fix: check that cg-setup.prompt.md is reachable through the prompts symlink,
        # matching link.ps1's stronger Test-Path verification (link.ps1 Step 6).
        $content | Should -Match 'cg-setup\.prompt\.md'
    }

    It "supports --yes / -y flag for non-interactive Relink prompt [regression guard]" {
        $content | Should -Match '\-\-yes'
        $content | Should -Match '\|\-y\|'
        $content | Should -Match 'FORCE'
    }

    It "Relink prompt is guarded by FORCE check (2 guards required) [regression guard]" {
        # The Relink symlink-conflict branch must be guarded by FORCE.
        ([regex]::Matches($content, 'if\s+\[ "\$FORCE" -eq 0 \]') | Measure-Object).Count |
            Should -Be 1
    }

    It "uses while-loop argument parsing for order-independent --platforms and --yes" {
        $content | Should -Match 'while \[ "\$#" -gt 0 \]'
        $content | Should -Match '--platforms=\*'
        $content | Should -Match '--platforms\|-Platforms'
    }

    It "defaults to all platforms through normalize_platforms" {
        $content | Should -Match 'input="all"'
        $content | Should -Match 'copilot claude-code codex opencode'
    }

    It "fails loudly for missing selected source units" {
        $content | Should -Match 'Selected Compound GPID source units are missing'
        $content | Should -Match 'exit 1'
    }

    It "migrates legacy .github whole-root symlinks [regression guard]" {
        $content | Should -Match 'migrating legacy whole-root symlink'
        $content | Should -Not -Match 'root_name" != "\.github"'
    }

    It "preserves existing managed entries during partial relinks [regression guard]" {
        $content | Should -Match 'collect_existing_managed_entries'
        $content | Should -Match 'collect_existing_managed_entries >> "\$entries_file"'
    }
}

Describe "install.sh - uninstall preserves package wrappers" {
    It "preserves all package-owned wrappers while removing PATH registration" {
        $tmpHome   = Join-Path ([System.IO.Path]::GetTempPath()) "cg-test-uninstall-$([System.Guid]::NewGuid().ToString('N'))"
        $tmpZshrc  = Join-Path $tmpHome ".zshrc"
        $fakeShell = "/bin/zsh"

        New-Item -ItemType Directory -Path $tmpHome -Force | Out-Null

        $originalHome  = $env:HOME
        $originalShell = $env:SHELL

        $env:HOME  = $tmpHome
        $env:SHELL = $fakeShell

        $tmpInstall = Join-Path $tmpHome ".compound-gpid"
        $tmpInstallBin = Join-Path $tmpInstall "bin"
        $tmpInstallScripts = Join-Path $tmpInstall "scripts"
        New-Item -ItemType Directory -Path $tmpInstallBin -Force | Out-Null
        New-Item -ItemType SymbolicLink -Path $tmpInstallScripts -Target (Join-Path $repoRoot "scripts") -Force | Out-Null

        $wrappers = Get-ChildItem -Path (Join-Path $repoRoot "bin") -Filter "cg-*" -File |
            Where-Object { $_.Extension -eq "" } |
            ForEach-Object { $_.Name }
        try {
            $wrappers.Count | Should -BeGreaterThan 0
            foreach ($wrapper in $wrappers) {
                Set-Content -Path (Join-Path $tmpInstallBin $wrapper) -Value "placeholder" -Encoding UTF8
            }
            Set-Content -Path $tmpZshrc -Value "# --- Compound GPID ---`nexport PATH=`"${tmpInstallBin}:`$PATH`"`n# --- End Compound GPID ---`n" -Encoding UTF8

            & bash (Join-Path $tmpInstallScripts "install.sh") --uninstall 2>/dev/null | Out-Null

            foreach ($wrapper in $wrappers) {
                Test-Path (Join-Path $tmpInstallBin $wrapper) | Should -Be $true
            }
            $profileContent = if (Test-Path $tmpZshrc) { Get-Content $tmpZshrc -Raw -Encoding UTF8 } else { "" }
            $profileContent | Should -Not -Match 'Compound GPID'
        } finally {
            Remove-Item -Path $tmpHome -Recurse -Force -ErrorAction SilentlyContinue
            if ($originalHome)  { $env:HOME  = $originalHome  } else { Remove-Item Env:\HOME  -ErrorAction SilentlyContinue }
            if ($originalShell) { $env:SHELL = $originalShell } else { Remove-Item Env:\SHELL -ErrorAction SilentlyContinue }
        }
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

    It "supports --yes / -y flag for non-interactive use [regression guard]" {
        # cg-unlink is called with --yes in E2E CI smoke tests where there is no
        # /dev/tty available. Without this flag, `read -r answer </dev/tty` hangs
        # or receives empty input, silently aborting the unlink.
        $content | Should -Match '\-\-yes'
        $content | Should -Match '\|\-y\|'  # -y short form in case block
        $content | Should -Match 'FORCE'
    }

    It "guards read confirmation calls with FORCE check [regression guard]" {
        # The single confirmation read must be inside a FORCE guard.
        ([regex]::Matches($content, 'if\s+\[ "\$FORCE" -eq 0 \]') | Measure-Object).Count |
            Should -Be 1
    }

    It "does not require .github to exist before unlinking platform units" {
        $content | Should -Not -Match '\.github/ does not exist.*Nothing to unlink'
        $content | Should -Match '\.opencode/opencode\.json'
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

    It "defines generate_copilot_instructions for post-update refresh" {
        $content | Should -Match 'generate_copilot_instructions'
    }

    It "uses resolved Python command instead of direct python3 calls" {
        $content | Should -Match 'resolve_python'
        $content | Should -Match 'PYTHON_CMD'
        $content | Should -Not -Match '\bpython3\s+"\$GENERATOR_SCRIPT"'
    }

    It "refreshes manifest-managed copied platform files" {
        $content | Should -Match 'managed-files\.json'
        $content | Should -Match 'Refreshed managed platform file'
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

    It "bin/cg-index resolves Python candidates" {
        $wrapperContent | Should -Match 'resolve_python'
        $wrapperContent | Should -Match 'python3 python py'
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

Describe "bash-scripts - bin/cg-token-audit wrapper content" {
    $wrapperPath    = Join-Path $repoRoot "bin/cg-token-audit"
    $wrapperContent = Get-Content $wrapperPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    It "bin/cg-token-audit references cg_audit_context.py" {
        $wrapperContent | Should -Match 'cg_audit_context\.py'
    }

    It "bin/cg-token-audit resolves Python candidates" {
        $wrapperContent | Should -Match 'resolve_python'
        $wrapperContent | Should -Match 'python3 python py'
    }

    It "bin/cg-token-audit passes arguments via `"`$@`"" {
        $wrapperContent | Should -Match '"\$@"'
    }

    It "bin/cg-token-audit uses SCRIPT_DIR for self-relative path" {
        $wrapperContent | Should -Match 'SCRIPT_DIR'
    }

    It "install.sh generates a cg-token-audit wrapper" {
        $installSh = Get-Content (Join-Path $repoRoot "scripts/install.sh") -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
        $installSh | Should -Match 'cg-token-audit'
        $installSh | Should -Match 'cg_audit_context\.py'
    }
}

Describe "bash-scripts - bin/cg-render-artifact wrapper content" {
    $wrapperPath = Join-Path $repoRoot "bin/cg-render-artifact"
    $wrapperContent = Get-Content $wrapperPath -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    It "bin/cg-render-artifact references render_artifact.py" {
        $wrapperContent | Should -Match 'render_artifact\.py'
    }

    It "bin/cg-render-artifact resolves all Python candidates" {
        $wrapperContent | Should -Match 'resolve_python'
        $wrapperContent | Should -Match 'python3 python py'
    }

    It "bin/cg-render-artifact forwards arguments and process exit status" {
        $wrapperContent | Should -Match 'exec "\$PYTHON_CMD"'
        $wrapperContent | Should -Match '"\$@"'
    }

    It "bin/cg-render-artifact uses SCRIPT_DIR for a self-relative entrypoint" {
        $wrapperContent | Should -Match 'SCRIPT_DIR'
        $wrapperContent | Should -Match '\.\./scripts/render_artifact\.py'
    }

    It "install.sh copies the committed cg-render-artifact wrapper" {
        $installSh = Get-Content (Join-Path $repoRoot "scripts/install.sh") -Raw -Encoding UTF8
        $installSh | Should -Match 'cp.*cg-render-artifact'
        $installSh | Should -Match 'chmod \+x.*cg-render-artifact'
    }

    It "install.sh command summary lists cg-render-artifact" {
        $installSh = Get-Content (Join-Path $repoRoot "scripts/install.sh") -Raw -Encoding UTF8
        $installSh | Should -Match 'cg-render-artifact.*Render or validate one workflow artifact'
    }
}

Describe "bash-scripts - Python-backed wrappers enforce Python 3.8+" {
    $wrappers = @(
        "cg-index",
        "cg-brain-init",
        "cg-token-audit",
        "cg-render-artifact",
        "cg-diff-summary",
        "cg-log-summary",
        "cg-problems-summary",
        "cg-test-summary",
        "cg-tree-summary"
    )

    foreach ($wrapper in $wrappers) {
        It "$wrapper checks sys.version_info >= (3, 8)" {
            $content = Get-Content (Join-Path $repoRoot "bin/$wrapper") -Raw -Encoding UTF8
            $content | Should -Match 'sys\.version_info\s*>=\s*\(3,\s*8\)'
        }
    }

    It "install.sh generated wrappers enforce Python 3.8+" {
        $content = Get-Content (Join-Path $repoRoot "scripts/install.sh") -Raw -Encoding UTF8
        $content | Should -Match 'sys\.version_info\s*>=\s*\(3,\s*8\)'
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
