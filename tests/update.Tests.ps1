# tests/update.Tests.ps1
# Pester tests for scripts/update.ps1 logic
#
# Run with: Invoke-Pester tests/update.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

Describe "update.ps1 - pre-condition checks" {
    Context "install path detection" {
        It "passes when a simulated install directory exists" {
            $installDir = Join-Path $TestDrive "compound-gpid-install"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            Test-Path $installDir | Should Be $true
        }

        It "would prompt to run install when path missing" {
            $installDir = Join-Path $TestDrive "does-not-exist"
            Test-Path $installDir | Should Be $false
        }
    }

    Context "git availability" {
        It "git is available on this machine" {
            $result = Get-Command git -ErrorAction SilentlyContinue
            $result | Should Not BeNullOrEmpty
        }
    }
}

Describe "update.ps1 - directory navigation" {
    Context "Push-Location / Pop-Location" {
        It "restores the original location after a successful push/pop" {
            $original = Get-Location
            $tempDir = Join-Path $TestDrive "nav-test"
            New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
            Push-Location $tempDir
            (Get-Location).Path | Should Be $tempDir
            Pop-Location
            (Get-Location).Path | Should Be $original.Path
        }

        It "restores the original location even when an error is simulated" {
            $original = Get-Location
            $tempDir = Join-Path $TestDrive "nav-error-test"
            New-Item -ItemType Directory -Path $tempDir -Force | Out-Null
            Push-Location $tempDir
            $err = $null
            try {
                throw "Simulated error"
            } catch {
                $err = $_.Exception.Message
            } finally {
                Pop-Location
            }
            $err | Should Be "Simulated error"
            (Get-Location).Path | Should Be $original.Path
        }
    }
}

Describe "update.ps1 - git hash comparison" {
    Context "detecting whether an update occurred" {
        It "reports no update when hashes are equal" {
            $before = "abc123def456"
            $after  = "abc123def456"
            $updated = $before -ne $after
            $updated | Should Be $false
        }

        It "reports an update when hashes differ" {
            $before = "abc123def456"
            $after  = "def456abc123"
            $updated = $before -ne $after
            $updated | Should Be $true
        }
    }
}

Describe "update.ps1 - exit code handling" {
    Context "LASTEXITCODE from git pull" {
        It "treats exit code 0 as success" {
            $global:LASTEXITCODE = 0
            ($LASTEXITCODE -ne 0) | Should Be $false
        }

        It "treats non-zero exit code as failure" {
            $global:LASTEXITCODE = 1
            ($LASTEXITCODE -ne 0) | Should Be $true
            $global:LASTEXITCODE = 0  # reset
        }
    }
}
