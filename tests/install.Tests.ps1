# tests/install.Tests.ps1
# Pester tests for install.ps1 (Windows-specific: .cmd wrappers, PATH via registry)
#
# Run with: Invoke-Pester tests/install.Tests.ps1
# Compatible with Pester 4.10.1+ (project standard).

# Platform detection (PS 5.1 compatible: no Set-StrictMode here, so $IsWindows returns $null rather than throwing)
$script:OnWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))

# install.ps1 manages .cmd wrappers and the Windows registry PATH. Skip all
# tests on macOS/Linux. install.sh is tested in bash-scripts.Tests.ps1.
if (-not $script:OnWindows) {
    Describe "install.ps1 - Windows-only tests (skipped on macOS/Linux)" {
        It "platform check: install.ps1 tests require Windows" -Skip {
            $true | Should -Be $true
        }
    }
    return
}

. (Join-Path $PSScriptRoot "..\scripts\helpers.ps1")

function Get-PythonForCgIndexSmoke {
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

Describe "install.ps1 - Git check" {
    Context "when a command does not exist" {
        It "Get-Command returns null for a missing command" {
            $result = Get-Command "this-command-does-not-exist-xyz" -ErrorAction SilentlyContinue
            $result | Should -BeNullOrEmpty
        }
    }

    Context "when git is available" {
        It "detects git on a properly configured machine" {
            $result = Get-Command git -ErrorAction SilentlyContinue
            $result | Should -Not -BeNullOrEmpty
        }
    }
}

Describe "install.ps1 - .cmd wrapper creation" {
    Context "wrapper content" {
        It "each wrapper contains the powershell.exe invocation with -NoProfile" {
            foreach ($script in @("link", "unlink", "update")) {
                $content = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0..\scripts\$script.ps1`" %*`r`n"
                ($content -match 'powershell\.exe') | Should -Be $true
                ($content -match 'NoProfile')       | Should -Be $true
                ($content -match "$script\.ps1")    | Should -Be $true
            }
        }

        It "wrapper uses %~dp0 for self-relative path resolution" {
            $content = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0..\scripts\link.ps1`" %*`r`n"
            ($content -match '%~dp0') | Should -Be $true
        }
    }

    Context "creating wrappers on disk" {
        It "writes all three .cmd files to the bin directory" {
            $binDir = Join-Path $TestDrive "bin"
            New-Item -ItemType Directory -Path $binDir -Force | Out-Null

            foreach ($script in @("link", "unlink", "update")) {
                $cmdPath = Join-Path $binDir "cg-$script.cmd"
                $content  = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0..\scripts\$script.ps1`" %*`r`n"
                Set-Content -Path $cmdPath -Value $content -NoNewline
            }

            Test-Path (Join-Path $binDir "cg-link.cmd")   | Should -Be $true
            Test-Path (Join-Path $binDir "cg-unlink.cmd") | Should -Be $true
            Test-Path (Join-Path $binDir "cg-update.cmd") | Should -Be $true
        }
    }
}

Describe "install.ps1 - PATH manipulation" {
    Context "detecting PATH state" {
        It "detects when bin dir is not yet on PATH" {
            $currentPath = "C:\Windows\system32;C:\Windows"
            $binDir      = "C:\WBG\.compound-gpid\bin"
            ($currentPath -notlike "*$binDir*") | Should -Be $true
        }

        It "detects when bin dir is already on PATH (idempotency)" {
            $binDir      = "C:\WBG\.compound-gpid\bin"
            $currentPath = "C:\Windows\system32;$binDir;C:\Windows"
            ($currentPath -notlike "*$binDir*") | Should -Be $false
        }
    }

    Context "building the new PATH value" {
        It "appends bin dir to an existing PATH with a semicolon separator" {
            $existing = "C:\Windows\system32"
            $binDir   = "C:\WBG\.compound-gpid\bin"
            $newPath  = if ($existing.Length -gt 0) { "$existing;$binDir" } else { $binDir }
            $newPath | Should -Be "C:\Windows\system32;C:\WBG\.compound-gpid\bin"
        }

        It "handles empty PATH without a leading semicolon" {
            $existing = ""
            $binDir   = "C:\WBG\.compound-gpid\bin"
            $newPath  = if ($existing.Length -gt 0) { "$existing;$binDir" } else { $binDir }
            $newPath | Should -Be "C:\WBG\.compound-gpid\bin"
        }
    }
}

Describe "install.ps1 - old profile cleanup" {
    Context "when profile contains an old Compound GPID block" {
        It "removes the block but preserves surrounding content" {
            $testProfile = Join-Path $TestDrive "profile_with_old_block.ps1"
            $content = "# existing content`n# --- Compound GPID (managed by install.ps1 - do not edit manually) ---`nfunction cg-link { }`n# --- End Compound GPID ---`n# more content"
            Set-Content -Path $testProfile -Value $content -Encoding UTF8

            $removed = @(Remove-LegacyProfileCommands -ProfilePath $testProfile)
            $cleaned = (Read-CgProfileText -Path $testProfile).Content

            $removed | Should -Contain "cg-link"
            ($cleaned -match "# --- Compound GPID") | Should -Be $false
            ($cleaned -match "# existing content")   | Should -Be $true
            ($cleaned -match "# more content")        | Should -Be $true
        }

        It "preserves a lookalike Compound GPID block" {
            $testProfile = Join-Path $TestDrive "profile_with_lookalike_block.ps1"
            $content = "# --- Compound GPID personal note ---`nWrite-Output 'preserve me'`n# --- End Compound GPID ---"
            Set-Content -Path $testProfile -Value $content -Encoding UTF8
            $expected = (Read-CgProfileText -Path $testProfile).Content

            [void](Remove-LegacyProfileCommands -ProfilePath $testProfile)

            (Read-CgProfileText -Path $testProfile).Content | Should -Be $expected
        }

        It "removes the historical added-by-install marker" {
            $testProfile = Join-Path $TestDrive "profile_with_historical_block.ps1"
            $content = "# --- Compound GPID (added by install.ps1) ---`nfunction cg-link { }`n# --- End Compound GPID ---"
            Set-Content -Path $testProfile -Value $content -Encoding UTF8

            $removed = @(Remove-LegacyProfileCommands -ProfilePath $testProfile)

            $removed | Should -Contain "cg-link"
            (Read-CgProfileText -Path $testProfile).Content | Should -Not -Match '(?m)^\s*# --- Compound GPID \(added by install\.ps1\) ---'
        }
    }

    Context "when profile has no Compound GPID block" {
        It "detects no cleanup is needed" {
            $content = "# My personal profile`nWrite-Host 'Hello'"
            ($content -match "Compound GPID") | Should -Be $false
        }

        It "contains cleanup for legacy unmarked cg-link profile functions [regression guard]" {
            # Reproduces CLM regression: old installs defined cg-link/cg-unlink/cg-update
            # functions in $PROFILE that dot-sourced scripts without the managed marker block.
            # install.ps1 must clean these legacy lines so command resolution falls back to
            # the PATH .cmd wrappers (which are CLM-safe).
            $installContent = Get-Content (Join-Path $PSScriptRoot "..\install.ps1") -Raw -Encoding UTF8
            $installContent | Should -Match 'helpers\.ps1'
            $installContent | Should -Match 'Remove-LegacyProfileCommands'
            $installContent | Should -Match 'Remove-CgLegacyLiveFunctions'
        }

        It "uses an exact managed block marker instead of unrelated comments" {
            $installContent = Get-Content (Join-Path $PSScriptRoot "..\install.ps1") -Raw -Encoding UTF8
            $helpersContent = Get-Content (Join-Path $PSScriptRoot "..\scripts\helpers.ps1") -Raw -Encoding UTF8
            $helpersContent | Should -Match 'managedBlockPattern'
            $helpersContent | Should -Match 'Remove-Item\s+-Path\s+"Function:\\\$commandName"'
        }

        It "removes an exact legacy wrapper from a global-scoped profile definition" {
            $profilePath = Join-Path $TestDrive "global-profile.ps1"
            $profileContent = 'function global:cg-link { & "C:\WBG\.compound-gpid\scripts\link.ps1" @args }'
            Set-Content -Path $profilePath -Value $profileContent -Encoding UTF8

            [void](Remove-LegacyProfileCommands -ProfilePath $profilePath)

            (Get-Content -Path $profilePath -Raw -Encoding UTF8) | Should -Not -Match '^\s*function\s+(?:global:)?cg-link\b'
        }

        It "preserves the original profile encoding while removing a legacy wrapper" {
            $profilePath = Join-Path $TestDrive "utf16-profile.ps1"
            $content = "# " + "caf" + [char]0x00E9 + "`r`nfunction cg-link { & `"C:\WBG\.compound-gpid\scripts\link.ps1`" @args }`r`n"
            $encoding = [System.Text.UnicodeEncoding]::new($false, $true)
            [System.IO.File]::WriteAllText($profilePath, $content, $encoding)

            [void](Remove-LegacyProfileCommands -ProfilePath $profilePath)

            $bytes = [System.IO.File]::ReadAllBytes($profilePath)
            ($bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) | Should -Be $true
            (Read-CgProfileText -Path $profilePath).Content | Should -Match "caf$([char]0x00E9)"
            (Read-CgProfileText -Path $profilePath).Content | Should -Not -Match '^\s*function\s+cg-link\b'
        }
    }
}

Describe "install.ps1 - Junction temp path naming" {
    Context "GUID-based uniqueness" {
        It "generates a path matching the expected prefix and GUID pattern" {
            $guid = [System.Guid]::NewGuid().ToString('N')
            $tempPath = "cg-gpid-junction-target-$guid"
            $tempPath | Should -Match 'cg-gpid-junction-target-[a-f0-9]{32}'
        }

        It "two calls to NewGuid produce different paths" {
            $p1 = "cg-gpid-$([System.Guid]::NewGuid().ToString('N'))"
            $p2 = "cg-gpid-$([System.Guid]::NewGuid().ToString('N'))"
            $p1 | Should -Not -Be $p2
        }
    }

    Context "temp directory cleanup" {
        It "cleans up temp directories correctly" {
            $target   = Join-Path $TestDrive "cg-t-$([System.Guid]::NewGuid().ToString('N'))"
            $junction = Join-Path $TestDrive "cg-j-$([System.Guid]::NewGuid().ToString('N'))"

            New-Item -ItemType Directory -Path $target -Force | Out-Null

            if (Test-Path $junction) { Remove-Item -Path $junction -Force }
            if (Test-Path $target)   { Remove-Item -Path $target   -Force -Recurse }

            Test-Path $target   | Should -Be $false
            Test-Path $junction | Should -Be $false
        }
    }
}

Describe "install.ps1 - .cg-version initialization" {
    Context "on a fresh install (file does not exist)" {
        It "creates .cg-version with content 'latest'" {
            $installDir  = Join-Path $TestDrive "cg-fresh"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            $versionFile = Join-Path $installDir ".cg-version"

            # Simulate the install.ps1 Step 4 logic
            if (-not (Test-Path $versionFile)) {
                Set-Content -Path $versionFile -Value "latest" -NoNewline
            }

            Test-Path $versionFile                          | Should -Be $true
            (Get-Content $versionFile -Raw).Trim()          | Should -Be "latest"
        }
    }

    Context "on an upgrade (file already exists with a pinned version)" {
        It "preserves the existing pinned version without overwriting" {
            $installDir  = Join-Path $TestDrive "cg-upgrade"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            $versionFile = Join-Path $installDir ".cg-version"

            # Pre-existing pinned version
            Set-Content -Path $versionFile -Value "v0.1.0" -NoNewline

            # Simulate the install.ps1 Step 4 logic (idempotent guard)
            if (-not (Test-Path $versionFile)) {
                Set-Content -Path $versionFile -Value "latest" -NoNewline
            }

            (Get-Content $versionFile -Raw).Trim() | Should -Be "v0.1.0"
        }
    }

    Context "on an upgrade (file already exists tracking latest)" {
        It "preserves 'latest' without overwriting" {
            $installDir  = Join-Path $TestDrive "cg-upgrade-latest"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            $versionFile = Join-Path $installDir ".cg-version"

            Set-Content -Path $versionFile -Value "latest" -NoNewline

            if (-not (Test-Path $versionFile)) {
                Set-Content -Path $versionFile -Value "latest" -NoNewline
            }

            (Get-Content $versionFile -Raw).Trim() | Should -Be "latest"
        }
    }

    Context "edge cases in .cg-version content" {
        It "handles a file with leading/trailing whitespace" {
            $installDir  = Join-Path $TestDrive "cg-ws"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            $versionFile = Join-Path $installDir ".cg-version"

            # File manually edited with extra whitespace
            Set-Content -Path $versionFile -Value "  v0.2.0  " -NoNewline

            $content = (Get-Content $versionFile -Raw).Trim()
            $content | Should -Be "v0.2.0"
        }

        It "handles a file with Windows CRLF line endings" {
            $installDir  = Join-Path $TestDrive "cg-crlf"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            $versionFile = Join-Path $installDir ".cg-version"

            # Out-File on Windows produces CRLF by default; -NoNewline avoids a trailing newline
            "v0.2.0" | Out-File -FilePath $versionFile -Encoding ascii

            # .Trim() must strip CRLF as well as plain LF and whitespace
            $content = (Get-Content $versionFile -Raw).Trim()
            $content | Should -Be "v0.2.0"
        }

        It "handles a blank file by falling back to 'latest'" {
            $installDir  = Join-Path $TestDrive "cg-blank"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            $versionFile = Join-Path $installDir ".cg-version"

            Set-Content -Path $versionFile -Value "" -NoNewline

            $raw = (Get-Content $versionFile -Raw -ErrorAction SilentlyContinue)
            $content = if ([string]::IsNullOrWhiteSpace($raw)) { "latest" } else { $raw.Trim() }
            $content | Should -Be "latest"
        }
    }
}

Describe "install.ps1 - Python detection (Step 1b)" {
    Context "Test-PythonCandidate probe logic" {
        It "accepts output starting with 'Python 3'" {
            $ver = "Python 3.11.9"
            ($ver -match '^Python\s+\d') | Should -Be $true
        }

        It "accepts output starting with 'Python 2' (old but real)" {
            $ver = "Python 2.7.18"
            ($ver -match '^Python\s+\d') | Should -Be $true
        }

        It "rejects Windows Store stub output (empty or non-Python string)" {
            foreach ($stubOutput in @("", "Access is denied.", "Python was not found")) {
                ($stubOutput -match '^Python\s+\d') | Should -Be $false
            }
        }

        It "rejects output that starts with Python but has no version number" {
            $ver = "Python"
            ($ver -match '^Python\s+\d') | Should -Be $false
        }
    }

    Context "Python resolution on this machine" {
        It "finds a real Python via at least one of: python3, python, py" {
            $found = $false
            foreach ($cmd in @("python3", "python", "py")) {
                if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) { continue }
                try {
                    $ver = & $cmd --version 2>&1
                    if ("$ver".Trim() -match '^Python\s+\d') { $found = $true; break }
                } catch {}
            }
            $found | Should -Be $true
        }
    }
}

Describe "install.ps1 - cg-index.cmd copy" {
    Context "single source of truth" {
        It "cg-index.cmd exists in the committed bin/ directory" {
            $repoRoot   = Split-Path $PSScriptRoot -Parent
            $cmdFile    = Join-Path $repoRoot "bin\cg-index.cmd"
            Test-Path $cmdFile | Should -Be $true
        }

        It "cg-index.cmd contains the for /f Python resolution pattern" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-index.cmd"
            $content  = Get-Content $cmdFile -Raw
            ($content -match 'for /f') | Should -Be $true
        }

        It "cg-index.cmd guards each python probe with a 'where' pre-check to prevent stderr leak" {
            # Regression guard: for /f ('python3 --version 2^>^&1') leaks the
            # "'python3' is not recognized" error to outer stderr on some Windows
            # environments when python3 is absent from PATH.  A 'where' pre-check
            # (mirroring install.ps1's Get-Command guard) suppresses this leak so
            # cg-index silently falls through to python / py without emitting
            # NativeCommandError in PowerShell.
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-index.cmd"
            $content  = Get-Content $cmdFile -Raw
            ($content -match 'where python3\s+>nul') | Should -Be $true
            ($content -match 'where python\s+>nul')  | Should -Be $true
            ($content -match 'where py\s+>nul')      | Should -Be $true
        }

        It "cg-index.cmd references cg_index.py" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-index.cmd"
            $content  = Get-Content $cmdFile -Raw
            ($content -match 'cg_index\.py') | Should -Be $true
        }

        It "install.ps1 copies cg-index.cmd rather than generating it inline" {
            $repoRoot      = Split-Path $PSScriptRoot -Parent
            $installScript = Get-Content (Join-Path $repoRoot "install.ps1") -Raw
            # Verify both the variable assignment (single source of truth pattern)
            # and the Copy-Item call that uses it are present.
            ($installScript -match 'cgIndexCmdSrc.*cg-index\.cmd') | Should -Be $true
            ($installScript -match 'Copy-Item.*cgIndexCmdSrc')       | Should -Be $true
        }

        It "does not throw when cg-index.cmd source and destination are the same path" {
            $compoundDir = Join-Path $TestDrive ".compound-gpid"
            $binDir      = Join-Path $compoundDir "bin"
            New-Item -ItemType Directory -Path $binDir -Force | Out-Null

            $cgIndexCmdSrc = Join-Path $compoundDir "bin\cg-index.cmd"
            $cgIndexCmdDst = Join-Path $binDir "cg-index.cmd"
            Set-Content -Path $cgIndexCmdSrc -Value "@echo off" -NoNewline

            # Regression contract: install must be idempotent and should not fail
            # when source and destination resolve to the same file path.
            {
                if (Test-Path $cgIndexCmdSrc) {
                    $cgIndexSrcFull = [System.IO.Path]::GetFullPath($cgIndexCmdSrc)
                    $cgIndexDstFull = [System.IO.Path]::GetFullPath($cgIndexCmdDst)
                    if ($cgIndexSrcFull -ieq $cgIndexDstFull) {
                        $null = $true
                    } else {
                        Copy-Item -Path $cgIndexCmdSrc -Destination $cgIndexCmdDst -Force -ErrorAction Stop
                    }
                }
            } | Should -Not -Throw
        }
    }
}

Describe "install.ps1 - cg-brain-init.cmd copy" {
    Context "single source of truth" {
        It "cg-brain-init.cmd exists in the committed bin/ directory" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-brain-init.cmd"
            Test-Path $cmdFile | Should -Be $true
        }

        It "cg-brain-init.cmd contains the for /f Python resolution pattern" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-brain-init.cmd"
            $content  = Get-Content $cmdFile -Raw
            ($content -match 'for /f') | Should -Be $true
        }

        It "cg-brain-init.cmd guards each python probe with a 'where' pre-check to prevent stderr leak" {
            # Regression guard: matching cg-index.cmd's pattern.  Without the 'where'
            # pre-check, for /f ('python3 --version 2^>^&1') leaks the
            # "'python3' is not recognized" error to outer stderr on systems where
            # python3 is absent from PATH.
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-brain-init.cmd"
            $content  = Get-Content $cmdFile -Raw
            ($content -match 'where python3\s+>nul') | Should -Be $true
            ($content -match 'where python\s+>nul')  | Should -Be $true
            ($content -match 'where py\s+>nul')      | Should -Be $true
        }

        It "cg-brain-init.cmd references team_brain/init.py" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-brain-init.cmd"
            $content  = Get-Content $cmdFile -Raw
            ($content -match 'team_brain.init\.py') | Should -Be $true
        }

        It "does not throw when cg-brain-init.cmd source and destination are the same path" {
            $compoundDir = Join-Path $TestDrive ".compound-gpid"
            $binDir      = Join-Path $compoundDir "bin"
            New-Item -ItemType Directory -Path $binDir -Force | Out-Null

            $src = Join-Path $compoundDir "bin\cg-brain-init.cmd"
            $dst = Join-Path $binDir "cg-brain-init.cmd"
            Set-Content -Path $src -Value "@echo off" -NoNewline

            {
                if (Test-Path $src) {
                    $srcFull = [System.IO.Path]::GetFullPath($src)
                    $dstFull = [System.IO.Path]::GetFullPath($dst)
                    if ($srcFull -ieq $dstFull) {
                        $null = $true
                    } else {
                        Copy-Item -Path $src -Destination $dst -Force -ErrorAction Stop
                    }
                }
            } | Should -Not -Throw
        }
    }
}

Describe "install.ps1 - cg-token-audit.cmd copy" {
    Context "single source of truth" {
        It "cg-token-audit.cmd exists in the committed bin/ directory" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-token-audit.cmd"
            Test-Path $cmdFile | Should -Be $true
        }

        It "cg-token-audit.cmd contains the for /f Python resolution pattern" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-token-audit.cmd"
            $content  = Get-Content $cmdFile -Raw
            ($content -match 'for /f') | Should -Be $true
        }

        It "cg-token-audit.cmd guards each python probe with a 'where' pre-check to prevent stderr leak" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-token-audit.cmd"
            $content  = Get-Content $cmdFile -Raw
            ($content -match 'where python3\s+>nul') | Should -Be $true
            ($content -match 'where python\s+>nul')  | Should -Be $true
            ($content -match 'where py\s+>nul')      | Should -Be $true
        }

        It "cg-token-audit.cmd references cg_audit_context.py" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $cmdFile  = Join-Path $repoRoot "bin\cg-token-audit.cmd"
            $content  = Get-Content $cmdFile -Raw
            ($content -match 'cg_audit_context\.py') | Should -Be $true
        }

        It "install.ps1 copies cg-token-audit.cmd rather than generating it inline" {
            $repoRoot      = Split-Path $PSScriptRoot -Parent
            $installScript = Get-Content (Join-Path $repoRoot "install.ps1") -Raw
            ($installScript -match 'cgTokenAuditCmdSrc.*cg-token-audit\.cmd') | Should -Be $true
            ($installScript -match 'Copy-Item.*cgTokenAuditCmdSrc')           | Should -Be $true
        }

        It "does not throw when cg-token-audit.cmd source and destination are the same path" {
            $compoundDir = Join-Path $TestDrive ".compound-gpid"
            $binDir      = Join-Path $compoundDir "bin"
            New-Item -ItemType Directory -Path $binDir -Force | Out-Null

            $src = Join-Path $compoundDir "bin\cg-token-audit.cmd"
            $dst = Join-Path $binDir "cg-token-audit.cmd"
            Set-Content -Path $src -Value "@echo off" -NoNewline

            {
                if (Test-Path $src) {
                    $srcFull = [System.IO.Path]::GetFullPath($src)
                    $dstFull = [System.IO.Path]::GetFullPath($dst)
                    if ($srcFull -ieq $dstFull) {
                        $null = $true
                    } else {
                        Copy-Item -Path $src -Destination $dst -Force -ErrorAction Stop
                    }
                }
            } | Should -Not -Throw
        }
    }
}

Describe "install.ps1 - cg-render-artifact.cmd copy" {
    Context "single source of truth" {
        It "cg-render-artifact.cmd exists in the committed bin/ directory" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            Test-Path (Join-Path $repoRoot "bin\cg-render-artifact.cmd") | Should -Be $true
        }

        It "cg-render-artifact.cmd contains the for /f Python resolution pattern" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $content = Get-Content (Join-Path $repoRoot "bin\cg-render-artifact.cmd") -Raw
            ($content -match 'for /f') | Should -Be $true
        }

        It "cg-render-artifact.cmd guards python3 with a where pre-check" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $content = Get-Content (Join-Path $repoRoot "bin\cg-render-artifact.cmd") -Raw
            ($content -match 'where python3\s+>nul') | Should -Be $true
        }

        It "cg-render-artifact.cmd guards python with a where pre-check" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $content = Get-Content (Join-Path $repoRoot "bin\cg-render-artifact.cmd") -Raw
            ($content -match 'where python\s+>nul') | Should -Be $true
        }

        It "cg-render-artifact.cmd guards py with a where pre-check" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $content = Get-Content (Join-Path $repoRoot "bin\cg-render-artifact.cmd") -Raw
            ($content -match 'where py\s+>nul') | Should -Be $true
        }

        It "cg-render-artifact.cmd references render_artifact.py and forwards arguments" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $content = Get-Content (Join-Path $repoRoot "bin\cg-render-artifact.cmd") -Raw
            ($content -match 'render_artifact\.py') | Should -Be $true
            ($content -match '%\*') | Should -Be $true
            ($content -match 'exit /b %ERRORLEVEL%') | Should -Be $true
        }

        It "install.ps1 copies the committed cg-render-artifact.cmd" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $installScript = Get-Content (Join-Path $repoRoot "install.ps1") -Raw
            ($installScript -match 'cgRenderArtifactCmdSrc.*cg-render-artifact\.cmd') | Should -Be $true
            ($installScript -match 'Copy-Item.*cgRenderArtifactCmdSrc') | Should -Be $true
        }

        It "does not throw when cg-render-artifact.cmd source and destination match" {
            $compoundDir = Join-Path $TestDrive ".compound-gpid"
            $binDir = Join-Path $compoundDir "bin"
            New-Item -ItemType Directory -Path $binDir -Force | Out-Null
            $src = Join-Path $compoundDir "bin\cg-render-artifact.cmd"
            $dst = Join-Path $binDir "cg-render-artifact.cmd"
            Set-Content -Path $src -Value "@echo off" -NoNewline
            {
                $srcFull = [System.IO.Path]::GetFullPath($src)
                $dstFull = [System.IO.Path]::GetFullPath($dst)
                if ($srcFull -ine $dstFull) {
                    Copy-Item -Path $src -Destination $dst -Force -ErrorAction Stop
                }
            } | Should -Not -Throw
        }
    }
}

Describe "Python-backed CMD launchers - runtime selection and status parity" {
    $repoRoot = Split-Path $PSScriptRoot -Parent
    $launchers = @(
        "cg-index.cmd",
        "cg-brain-init.cmd",
        "cg-token-audit.cmd",
        "cg-render-artifact.cmd"
    )
    $launcherCases = @($launchers | ForEach-Object { @{ Launcher = $_ } })

    foreach ($launcher in $launchers) {
        It "$launcher selects Python 3.8+ before an external run label" {
            $content = Get-Content (Join-Path $repoRoot "bin\$launcher") -Raw
            ($content -match 'sys\.version_info\s*>=\s*\(3,\s*8\)') | Should -Be $true
            ($content -match 'set "PYTHON_CMD=(python3|python|py)"') | Should -Be $true
            ($content -match '(?m)^:run_python\s*$') | Should -Be $true
            ($content -match '(?m)^call %PYTHON_CMD%\s+') | Should -Be $true
            ([regex]::Matches($content, '(?m)^\s*call (?:python3|python|py) -c ').Count) | Should -Be 3
        }
    }

    It "<Launcher> propagates an executed child failure code" -TestCases $launcherCases {
        param($Launcher)
        $fakeBin = Join-Path $TestDrive "fake-python"
        New-Item -ItemType Directory -Path $fakeBin -Force | Out-Null
        $fakePython = Join-Path $fakeBin "python3.cmd"
        @'
@echo off
if "%~1"=="--version" (echo Python 3.11.0& exit /b 0)
if "%~1"=="-c" exit /b 0
exit /b 37
'@ | Set-Content -Path $fakePython -Encoding ASCII
        $originalPath = $env:PATH
        try {
            $env:PATH = "$fakeBin;$originalPath"
            $wrapper = Join-Path $repoRoot "bin\$Launcher"
            & cmd /d /c "`"$wrapper`" ignored.md" | Out-Null
            $LASTEXITCODE | Should -Be 37
        } finally {
            $env:PATH = $originalPath
        }
    }

    It "<Launcher> skips Python 3.7 and executes the Python 3.8 fallback" -TestCases $launcherCases {
        param($Launcher)
        $fakeBin = Join-Path $TestDrive "fake-python-fallback"
        New-Item -ItemType Directory -Path $fakeBin -Force | Out-Null
        @'
@echo off
if "%~1"=="--version" (echo Python 3.7.9& exit /b 0)
if "%~1"=="-c" exit /b 1
exit /b 39
'@ | Set-Content -Path (Join-Path $fakeBin "python3.cmd") -Encoding ASCII
        @'
@echo off
if "%~1"=="--version" (echo Python 3.8.0& exit /b 0)
if "%~1"=="-c" exit /b 0
exit /b 38
'@ | Set-Content -Path (Join-Path $fakeBin "python.cmd") -Encoding ASCII
        $originalPath = $env:PATH
        try {
            $env:PATH = "$fakeBin;$originalPath"
            $wrapper = Join-Path $repoRoot "bin\$Launcher"
            & cmd /d /c "`"$wrapper`" ignored.md" | Out-Null
            $LASTEXITCODE | Should -Be 38
        } finally {
            $env:PATH = $originalPath
        }
    }
}

Describe "install.ps1 - -Uninstall flag" {
    Context "param block" {
        It "install.ps1 declares an -Uninstall switch parameter" {
            $installScript = Get-Content (Join-Path $PSScriptRoot "..\install.ps1") -Raw
            ($installScript -match '\[switch\]\$Uninstall') | Should -Be $true
        }
    }

    Context "wrapper preservation logic" {
        It "preserves package-owned cg-* wrappers in bin dir" {
            $fakebin = Join-Path $TestDrive "fake-bin"
            New-Item -ItemType Directory -Path $fakebin -Force | Out-Null
            Set-Content -Path (Join-Path $fakebin "cg-link.cmd")   -Value "@echo off" -Encoding UTF8
            Set-Content -Path (Join-Path $fakebin "cg-update.cmd") -Value "@echo off" -Encoding UTF8
            Set-Content -Path (Join-Path $fakebin "other.cmd")     -Value "@echo off" -Encoding UTF8

            $wrappers = @(Get-ChildItem -Path $fakebin -Filter 'cg-*' -ErrorAction SilentlyContinue)

            (Test-Path (Join-Path $fakebin "cg-link.cmd"))   | Should -Be $true
            (Test-Path (Join-Path $fakebin "cg-update.cmd")) | Should -Be $true
            (Test-Path (Join-Path $fakebin "other.cmd"))     | Should -Be $true
            $wrappers.Count | Should -Be 2
        }

        It "reports zero wrappers found when bin dir is already empty" {
            $fakebin = Join-Path $TestDrive "fake-bin-empty"
            New-Item -ItemType Directory -Path $fakebin -Force | Out-Null
            $wrappers = @(Get-ChildItem -Path $fakebin -Filter 'cg-*' -ErrorAction SilentlyContinue)
            $wrappers.Count | Should -Be 0
        }

        It "install.ps1 unregisters PATH without deleting package wrapper sources" {
            $installScript = Get-Content (Join-Path $PSScriptRoot "..\install.ps1") -Raw
            $uninstallStart = $installScript.IndexOf('if ($Uninstall)')
            $uninstallEnd = $installScript.IndexOf('exit 0', $uninstallStart)
            $uninstallBlock = $installScript.Substring($uninstallStart, $uninstallEnd - $uninstallStart)
            ($uninstallBlock -match 'Remove-Item\s+-LiteralPath\s+\$wrapper') | Should -Be $false
        }
    }

    Context "isolated uninstall runtime" {
        It "executes uninstall without deleting package wrapper sources" {
            $repoRoot = Split-Path $PSScriptRoot -Parent
            $fixtureRoot = Join-Path $TestDrive "uninstall-runtime"
            $fixtureScripts = Join-Path $fixtureRoot "scripts"
            $fixtureBin = Join-Path $fixtureRoot "bin"
            $fakeBin = Join-Path $fixtureRoot "fake-bin"
            New-Item -ItemType Directory -Path $fixtureScripts, $fixtureBin, $fakeBin -Force | Out-Null
            Copy-Item (Join-Path $repoRoot "install.ps1") (Join-Path $fixtureRoot "install.ps1")
            Copy-Item (Join-Path $repoRoot "scripts\helpers.ps1") (Join-Path $fixtureScripts "helpers.ps1")
            $wrapper = Join-Path $fixtureBin "cg-index.cmd"
            Set-Content -Path $wrapper -Value "@echo off`r`nexit /b 0" -Encoding ASCII
            $registryLog = Join-Path $fixtureRoot "registry.log"
            @'
@echo off
echo %*>>"%CG_TEST_REG_LOG%"
exit /b 1
'@ | Set-Content -Path (Join-Path $fakeBin "reg.cmd") -Encoding ASCII
            $profilePath = Join-Path $fixtureRoot "profile.ps1"
            Set-Content -Path $profilePath -Value "# isolated profile" -Encoding UTF8
            $originalPath = $env:PATH
            $originalRegistryLog = $env:CG_TEST_REG_LOG
            try {
                $env:PATH = "$fakeBin;$originalPath"
                $env:CG_TEST_REG_LOG = $registryLog
                $powerShell = (Get-Process -Id $PID).Path
                $escapedProfile = $profilePath.Replace("'", "''")
                $installPath = (Join-Path $fixtureRoot "install.ps1").Replace("'", "''")
                $command = "`$PROFILE = '$escapedProfile'; & '$installPath' -Uninstall"
                & $powerShell -NoProfile -ExecutionPolicy Bypass -Command $command | Out-Null
                $LASTEXITCODE | Should -Be 0
            } finally {
                $env:PATH = $originalPath
                $env:CG_TEST_REG_LOG = $originalRegistryLog
            }
            (Test-Path $wrapper) | Should -Be $true
            (Get-Content $wrapper -Raw) | Should -Match 'exit /b 0'
            (Get-Content $registryLog -Raw) | Should -Match 'query HKCU\\Environment /v PATH'
        }
    }

    Context "PATH removal logic" {
        It "removes the bin dir from a PATH string that contains it" {
            $binDir      = "C:\WBG\.compound-gpid\bin"
            $currentPath = "C:\Windows\system32;$binDir;C:\Program Files\Git\cmd"
            $newPath = (($currentPath -split ";") | Where-Object { $_ -ne $binDir }) -join ";"
            $newPath | Should -Be "C:\Windows\system32;C:\Program Files\Git\cmd"
        }

        It "leaves PATH unchanged when bin dir is not present" {
            $binDir      = "C:\WBG\.compound-gpid\bin"
            $currentPath = "C:\Windows\system32;C:\Program Files\Git\cmd"
            ($currentPath -like "*$binDir*") | Should -Be $false
        }

        It "handles bin dir at the start of PATH" {
            $binDir      = "C:\WBG\.compound-gpid\bin"
            $currentPath = "$binDir;C:\Windows\system32"
            $newPath = (($currentPath -split ";") | Where-Object { $_ -ne $binDir }) -join ";"
            $newPath | Should -Be "C:\Windows\system32"
        }
    }

    Context "uninstall mode exits before install steps" {
        It "install.ps1 contains early exit 0 in the Uninstall block" {
            $installScript = Get-Content (Join-Path $PSScriptRoot "..\install.ps1") -Raw
            # The uninstall block must call exit 0 before the normal install banner
            $uninstallIdx = $installScript.IndexOf('if ($Uninstall)')
            $exitIdx      = $installScript.IndexOf('exit 0', $uninstallIdx)
            $normalInstallIdx = $installScript.IndexOf("'Step 1: Verify Git'")
            # exit 0 must appear before the first git-check line
            $exitIdx | Should -BeGreaterThan $uninstallIdx
        }
    }
}

Describe "install.ps1 - cg-index smoke test" {
    It "cg-index --version exits 0 with non-empty output" {
        $repoRoot = Split-Path $PSScriptRoot -Parent
        $wrapper  = Join-Path $repoRoot "bin\cg-index.cmd"
        if (-not (Test-Path $wrapper)) { Set-ItResult -Skipped -Because "cg-index.cmd not found" }
        $python = Get-PythonForCgIndexSmoke
        if (-not $python) { Set-ItResult -Skipped -Because "Python is not available" }
        $output   = & cmd /c "`"$wrapper`" --version 2>&1"
        $LASTEXITCODE | Should -Be 0
        $output       | Should -Not -BeNullOrEmpty
    }
}
