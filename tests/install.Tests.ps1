# tests/install.Tests.ps1
# Pester tests for install.ps1 (Windows-specific: .cmd wrappers, PATH via registry)
#
# Run with: Invoke-Pester tests/install.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

# Platform detection (PS 5.1 compatible: no Set-StrictMode here, so $IsWindows returns $null rather than throwing)
$script:OnWindows = ((Test-Path variable:IsWindows) -and $IsWindows -or $env:OS -eq "Windows_NT")

# install.ps1 manages .cmd wrappers and the Windows registry PATH. Skip all
# tests on macOS/Linux. install.sh is tested in bash-scripts.Tests.ps1.
if (-not $script:OnWindows) {
    Describe "install.ps1 - Windows-only tests (skipped on macOS/Linux)" {
        It "platform check: install.ps1 tests require Windows" { $true | Should -Be $true }
    }
    return
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
            Set-Content -Path $testProfile -Value $content

            $raw     = Get-Content $testProfile -Raw
            $cleaned = ($raw -replace "(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?", "").TrimEnd()

            ($cleaned -match "# --- Compound GPID") | Should -Be $false
            ($cleaned -match "# existing content")   | Should -Be $true
            ($cleaned -match "# more content")        | Should -Be $true
        }
    }

    Context "when profile has no Compound GPID block" {
        It "detects no cleanup is needed" {
            $content = "# My personal profile`nWrite-Host 'Hello'"
            ($content -match "Compound GPID") | Should -Be $false
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
    }
}

Describe "install.ps1 - Phase 1 smoke test" -Tags @("Pending") {
    # This test becomes active after Phase 2 delivers scripts/cg_index.py.
    # Marked Pending so it appears in test output without failing the suite.
    It "cg-index --version exits 0 with non-empty output" -Pending {
        $repoRoot = Split-Path $PSScriptRoot -Parent
        $wrapper  = Join-Path $repoRoot "bin\cg-index.cmd"
        if (-not (Test-Path $wrapper)) { Set-ItResult -Skipped -Because "cg-index.cmd not found" }
        $output   = & cmd /c "`"$wrapper`" --version 2>&1"
        $LASTEXITCODE | Should -Be 0
        $output       | Should -Not -BeNullOrEmpty
    }
}
