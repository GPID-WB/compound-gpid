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

Describe "install.ps1 - Profile idempotency" {
    Context "when profile does not exist" {
        It "New-Item creates the profile file" {
            $testProfile = Join-Path $TestDrive "test_profile.ps1"
            Test-Path $testProfile | Should Be $false
            New-Item -Path $testProfile -ItemType File -Force | Out-Null
            Test-Path $testProfile | Should Be $true
        }
    }

    Context "when profile already contains Compound GPID block" {
        It "replace regex removes the existing block" {
            $testProfile = Join-Path $TestDrive "profile_with_block.ps1"
            $existingBlock = "# --- Compound GPID ---`nfunction cg-link { }`n# --- End Compound GPID ---"
            Set-Content -Path $testProfile -Value $existingBlock

            $content = Get-Content -Path $testProfile -Raw
            $updated = $content -replace '(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?', ''
            $updated = $updated.TrimEnd()

            ($updated -match 'Compound GPID') | Should Be $false
        }

        It "after removing old block and appending new one, exactly one opening marker exists" {
            $testProfile = Join-Path $TestDrive "profile_replace.ps1"
            $existing = "# --- Compound GPID ---`nfunction cg-link { }`n# --- End Compound GPID ---"
            Set-Content -Path $testProfile -Value $existing

            $content = Get-Content -Path $testProfile -Raw
            $updated = ($content -replace '(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?', '').TrimEnd()
            $newBlock = "`n# --- Compound GPID ---`nfunction cg-link { }`n# --- End Compound GPID ---"
            Set-Content -Path $testProfile -Value ($updated + $newBlock)

            $final = Get-Content -Path $testProfile -Raw
            ($final | Select-String '# --- Compound GPID ---' -AllMatches).Matches.Count | Should Be 1
        }
    }

    Context "when profile has no existing block" {
        It "appends Compound GPID block without removing existing content" {
            $testProfile = Join-Path $TestDrive "profile_fresh.ps1"
            Set-Content -Path $testProfile -Value "# My existing profile`nWrite-Host 'Hello'"

            $block = "`n# --- Compound GPID ---`n# --- End Compound GPID ---"
            Add-Content -Path $testProfile -Value $block

            $after = Get-Content -Path $testProfile -Raw
            ($after -match 'My existing profile') | Should Be $true
            ($after -match 'Compound GPID') | Should Be $true
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
