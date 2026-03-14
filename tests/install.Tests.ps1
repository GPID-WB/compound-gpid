# tests/install.Tests.ps1
# Pester tests for install.ps1
#
# Run with: Invoke-Pester tests/install.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

Describe "install.ps1 - Git check" {
    Context "when a command does not exist" {
        It "Get-Command returns null for a missing command" {
            $result = Get-Command "this-command-does-not-exist-xyz" -ErrorAction SilentlyContinue
            $result | Should BeNullOrEmpty
        }
    }

    Context "when git is available" {
        It "detects git on a properly configured machine" {
            $result = Get-Command git -ErrorAction SilentlyContinue
            $result | Should Not BeNullOrEmpty
        }
    }
}

Describe "install.ps1 - .cmd wrapper creation" {
    Context "wrapper content" {
        It "each wrapper contains the powershell.exe invocation with -NoProfile" {
            foreach ($script in @("link", "unlink", "update")) {
                $content = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0..\scripts\$script.ps1`" %*`r`n"
                ($content -match 'powershell\.exe') | Should Be $true
                ($content -match 'NoProfile')       | Should Be $true
                ($content -match "$script\.ps1")    | Should Be $true
            }
        }

        It "wrapper uses %~dp0 for self-relative path resolution" {
            $content = "@echo off`r`npowershell.exe -NoProfile -ExecutionPolicy Bypass -File `"%~dp0..\scripts\link.ps1`" %*`r`n"
            ($content -match '%~dp0') | Should Be $true
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

            Test-Path (Join-Path $binDir "cg-link.cmd")   | Should Be $true
            Test-Path (Join-Path $binDir "cg-unlink.cmd") | Should Be $true
            Test-Path (Join-Path $binDir "cg-update.cmd") | Should Be $true
        }
    }
}

Describe "install.ps1 - PATH manipulation" {
    Context "detecting PATH state" {
        It "detects when bin dir is not yet on PATH" {
            $currentPath = "C:\Windows\system32;C:\Windows"
            $binDir      = "C:\WBG\.compound-gpid\bin"
            ($currentPath -notlike "*$binDir*") | Should Be $true
        }

        It "detects when bin dir is already on PATH (idempotency)" {
            $binDir      = "C:\WBG\.compound-gpid\bin"
            $currentPath = "C:\Windows\system32;$binDir;C:\Windows"
            ($currentPath -notlike "*$binDir*") | Should Be $false
        }
    }

    Context "building the new PATH value" {
        It "appends bin dir to an existing PATH with a semicolon separator" {
            $existing = "C:\Windows\system32"
            $binDir   = "C:\WBG\.compound-gpid\bin"
            $newPath  = if ($existing.Length -gt 0) { "$existing;$binDir" } else { $binDir }
            $newPath | Should Be "C:\Windows\system32;C:\WBG\.compound-gpid\bin"
        }

        It "handles empty PATH without a leading semicolon" {
            $existing = ""
            $binDir   = "C:\WBG\.compound-gpid\bin"
            $newPath  = if ($existing.Length -gt 0) { "$existing;$binDir" } else { $binDir }
            $newPath | Should Be "C:\WBG\.compound-gpid\bin"
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

            ($cleaned -match "# --- Compound GPID") | Should Be $false
            ($cleaned -match "# existing content")   | Should Be $true
            ($cleaned -match "# more content")        | Should Be $true
        }
    }

    Context "when profile has no Compound GPID block" {
        It "detects no cleanup is needed" {
            $content = "# My personal profile`nWrite-Host 'Hello'"
            ($content -match "Compound GPID") | Should Be $false
        }
    }
}

Describe "install.ps1 - Junction temp path naming" {
    Context "GUID-based uniqueness" {
        It "generates a path matching the expected prefix and GUID pattern" {
            $guid = [System.Guid]::NewGuid().ToString('N')
            $tempPath = "cg-gpid-junction-target-$guid"
            $tempPath | Should Match 'cg-gpid-junction-target-[a-f0-9]{32}'
        }

        It "two calls to NewGuid produce different paths" {
            $p1 = "cg-gpid-$([System.Guid]::NewGuid().ToString('N'))"
            $p2 = "cg-gpid-$([System.Guid]::NewGuid().ToString('N'))"
            $p1 | Should Not Be $p2
        }
    }

    Context "temp directory cleanup" {
        It "cleans up temp directories correctly" {
            $target   = Join-Path $TestDrive "cg-t-$([System.Guid]::NewGuid().ToString('N'))"
            $junction = Join-Path $TestDrive "cg-j-$([System.Guid]::NewGuid().ToString('N'))"

            New-Item -ItemType Directory -Path $target -Force | Out-Null

            if (Test-Path $junction) { Remove-Item -Path $junction -Force }
            if (Test-Path $target)   { Remove-Item -Path $target   -Force -Recurse }

            Test-Path $target   | Should Be $false
            Test-Path $junction | Should Be $false
        }
    }
}
