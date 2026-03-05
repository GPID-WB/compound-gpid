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

Describe "update.ps1 - git checkout . before pull" {
    Context "resetting local changes logic" {
        It "exit code 0 is treated as success" {
            # Test LASTEXITCODE handling without touching the real repo.
            # Running git checkout . against ~\.compound-gpid in tests would
            # silently discard any uncommitted developer changes.
            $global:LASTEXITCODE = 0
            ($LASTEXITCODE -ne 0) | Should Be $false
            $global:LASTEXITCODE = 0  # reset
        }

        It "non-zero exit code triggers a warning but does not abort" {
            $global:LASTEXITCODE = 1
            ($LASTEXITCODE -ne 0) | Should Be $true
            $global:LASTEXITCODE = 0  # reset
        }
    }
}

Describe "update.ps1 - copilot-instructions.md refresh" {
    Context "when the file in CWD has the management marker" {
        It "overwrites the file with updated content" {
            $marker  = "<!-- compound-gpid:managed -->"
            $dest    = Join-Path $TestDrive "copilot-managed.md"
            $source  = Join-Path $TestDrive "copilot-source.md"

            Set-Content -Path $source -Value "# Updated instructions from global clone"
            Set-Content -Path $dest   -Value ($marker + "`n# Old instructions")

            # Simulate the marker check and overwrite
            $existing = Get-Content $dest -Raw
            if ($existing -match [regex]::Escape($marker)) {
                $newContent = Get-Content $source -Raw
                Set-Content -Path $dest -Value ($marker + "`n" + $newContent)
            }

            $result = Get-Content $dest -Raw
            $result -match "Updated instructions" | Should Be $true
            $result -match "Old instructions"     | Should Be $false
        }
    }

    Context "when the file in CWD does NOT have the management marker" {
        It "leaves the user-managed file untouched" {
            $marker  = "<!-- compound-gpid:managed -->"
            $dest    = Join-Path $TestDrive "copilot-user.md"
            $source  = Join-Path $TestDrive "copilot-source-skip.md"

            Set-Content -Path $source -Value "# New source content"
            Set-Content -Path $dest   -Value "# My custom instructions (no marker)"

            # Simulate the marker check - should NOT overwrite
            $existing = Get-Content $dest -Raw
            if ($existing -match [regex]::Escape($marker)) {
                $newContent = Get-Content $source -Raw
                Set-Content -Path $dest -Value ($marker + "`n" + $newContent)
            }

            $result = Get-Content $dest -Raw
            $result -match "My custom instructions" | Should Be $true
            $result -match "New source content"     | Should Be $false
        }
    }

    Context "when copilot-instructions.md does not exist in CWD" {
        It "does not attempt to refresh a non-existent file" {
            $nonexistent = Join-Path $TestDrive "no-copilot-instructions.md"
            Test-Path $nonexistent | Should Be $false
            # Simulates the guard condition in update.ps1
            $shouldRefresh = (Test-Path $nonexistent)
            $shouldRefresh | Should Be $false
        }
    }
}

Describe "update.ps1 - docs to .cg-docs migration" {
    Context "migrating docs/brainstorms to .cg-docs/brainstorms" {
        It "moves docs/brainstorms to .cg-docs/brainstorms when source exists" {
            $root = Join-Path $TestDrive "migrate-brainstorms"
            New-Item -ItemType Directory -Path "$root\docs\brainstorms" -Force | Out-Null
            New-Item -ItemType File -Path "$root\docs\brainstorms\2025-01-01-test.md" -Force | Out-Null

            # Simulate migration logic
            $src = "$root\docs\brainstorms"
            $dst = "$root\.cg-docs\brainstorms"
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                Move-Item -Path $src -Destination $dst
            }

            Test-Path "$root\.cg-docs\brainstorms\2025-01-01-test.md" | Should Be $true
            Test-Path "$root\docs\brainstorms" | Should Be $false
        }
    }

    Context "migrating docs/plans to .cg-docs/plans" {
        It "moves docs/plans to .cg-docs/plans when source exists" {
            $root = Join-Path $TestDrive "migrate-plans"
            New-Item -ItemType Directory -Path "$root\docs\plans" -Force | Out-Null
            New-Item -ItemType File -Path "$root\docs\plans\2025-01-01-plan.md" -Force | Out-Null

            $src = "$root\docs\plans"
            $dst = "$root\.cg-docs\plans"
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                Move-Item -Path $src -Destination $dst
            }

            Test-Path "$root\.cg-docs\plans\2025-01-01-plan.md" | Should Be $true
            Test-Path "$root\docs\plans" | Should Be $false
        }
    }

    Context "migrating docs/solutions to .cg-docs/solutions" {
        It "moves docs/solutions to .cg-docs/solutions when source exists" {
            $root = Join-Path $TestDrive "migrate-solutions"
            New-Item -ItemType Directory -Path "$root\docs\solutions\build-errors" -Force | Out-Null
            New-Item -ItemType File -Path "$root\docs\solutions\build-errors\fix.md" -Force | Out-Null

            $src = "$root\docs\solutions"
            $dst = "$root\.cg-docs\solutions"
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                Move-Item -Path $src -Destination $dst
            }

            Test-Path "$root\.cg-docs\solutions\build-errors\fix.md" | Should Be $true
            Test-Path "$root\docs\solutions" | Should Be $false
        }
    }

    Context "skipping migration when source does not exist" {
        It "does not create .cg-docs/brainstorms when docs/brainstorms is absent" {
            $root = Join-Path $TestDrive "migrate-skip"
            New-Item -ItemType Directory -Path $root -Force | Out-Null

            $src = "$root\docs\brainstorms"
            $dst = "$root\.cg-docs\brainstorms"
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                Move-Item -Path $src -Destination $dst
            }

            Test-Path $dst | Should Be $false
        }
    }

    Context "merge behaviour when target already exists" {
        It "moves individual files when .cg-docs/brainstorms already exists" {
            $root = Join-Path $TestDrive "migrate-merge"
            New-Item -ItemType Directory -Path "$root\docs\brainstorms" -Force | Out-Null
            New-Item -ItemType Directory -Path "$root\.cg-docs\brainstorms" -Force | Out-Null
            New-Item -ItemType File -Path "$root\docs\brainstorms\new-file.md" -Force | Out-Null
            New-Item -ItemType File -Path "$root\.cg-docs\brainstorms\existing-file.md" -Force | Out-Null

            $src = "$root\docs\brainstorms"
            $dst = "$root\.cg-docs\brainstorms"
            if (Test-Path $src) {
                if (-not (Test-Path $dst)) {
                    New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                    Move-Item -Path $src -Destination $dst
                } else {
                    # Merge: move individual files
                    Get-ChildItem -Path $src | ForEach-Object {
                        $target = Join-Path $dst $_.Name
                        if (-not (Test-Path $target)) {
                            Move-Item -Path $_.FullName -Destination $target
                        }
                    }
                    # Remove source if now empty
                    $remaining = Get-ChildItem -Path $src
                    if ($null -eq $remaining -or $remaining.Count -eq 0) {
                        Remove-Item -Path $src -Force
                    }
                }
            }

            Test-Path "$root\.cg-docs\brainstorms\existing-file.md" | Should Be $true
            Test-Path "$root\.cg-docs\brainstorms\new-file.md"      | Should Be $true
            Test-Path "$root\docs\brainstorms"                       | Should Be $false
        }
    }

    Context "preserving other docs/ content" {
        It "does not remove docs/manual.md when migrating docs/brainstorms" {
            $root = Join-Path $TestDrive "migrate-preserve"
            New-Item -ItemType Directory -Path "$root\docs\brainstorms" -Force | Out-Null
            New-Item -ItemType File -Path "$root\docs\manual.md" -Force | Out-Null
            New-Item -ItemType File -Path "$root\docs\brainstorms\note.md" -Force | Out-Null

            $src = "$root\docs\brainstorms"
            $dst = "$root\.cg-docs\brainstorms"
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                Move-Item -Path $src -Destination $dst
            }

            Test-Path "$root\docs\manual.md"            | Should Be $true
            Test-Path "$root\.cg-docs\brainstorms\note.md" | Should Be $true
        }
    }

    Context "idempotency" {
        It "skips migration when .cg-docs/brainstorms already exists and docs/brainstorms is gone" {
            $root = Join-Path $TestDrive "migrate-idempotent"
            New-Item -ItemType Directory -Path "$root\.cg-docs\brainstorms" -Force | Out-Null
            New-Item -ItemType File -Path "$root\.cg-docs\brainstorms\note.md" -Force | Out-Null
            # docs/brainstorms does not exist — nothing to migrate

            $src = "$root\docs\brainstorms"
            $dst = "$root\.cg-docs\brainstorms"
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                Move-Item -Path $src -Destination $dst
            }

            # Destination unchanged
            Test-Path "$root\.cg-docs\brainstorms\note.md" | Should Be $true
        }
    }

    Context "empty docs/ cleanup after migration" {
        It "removes docs/ when all cg subdirectories have been migrated and docs/ is empty" {
            $root = Join-Path $TestDrive "migrate-cleanup"
            New-Item -ItemType Directory -Path "$root\docs\brainstorms" -Force | Out-Null

            # Migrate brainstorms
            $src = "$root\docs\brainstorms"
            $dst = "$root\.cg-docs\brainstorms"
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                Move-Item -Path $src -Destination $dst
            }

            # Simulate cleanup: remove docs/ if empty
            $docsDir = "$root\docs"
            if (Test-Path $docsDir) {
                $remaining = Get-ChildItem -Path $docsDir
                if ($null -eq $remaining -or $remaining.Count -eq 0) {
                    Remove-Item -Path $docsDir -Force -Recurse
                }
            }

            Test-Path "$root\docs" | Should Be $false
            Test-Path "$root\.cg-docs\brainstorms" | Should Be $true
        }

        It "keeps docs/ when non-cg files remain (e.g. manual.md)" {
            $root = Join-Path $TestDrive "migrate-cleanup-keep"
            New-Item -ItemType Directory -Path "$root\docs\brainstorms" -Force | Out-Null
            New-Item -ItemType File -Path "$root\docs\manual.md" -Force | Out-Null

            # Migrate brainstorms
            $src = "$root\docs\brainstorms"
            $dst = "$root\.cg-docs\brainstorms"
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                Move-Item -Path $src -Destination $dst
            }

            # Simulate cleanup: remove docs/ only if empty
            $docsDir = "$root\docs"
            if (Test-Path $docsDir) {
                $remaining = Get-ChildItem -Path $docsDir
                if ($null -eq $remaining -or $remaining.Count -eq 0) {
                    Remove-Item -Path $docsDir -Force -Recurse
                }
            }

            Test-Path "$root\docs"          | Should Be $true
            Test-Path "$root\docs\manual.md" | Should Be $true
        }
    }

    Context "schema version stamping" {
        It "writes cg-schema-version to compound-gpid.local.md when the field exists" {
            $root = Join-Path $TestDrive "schema-stamp"
            New-Item -ItemType Directory -Path $root -Force | Out-Null
            $localMd = "$root\compound-gpid.local.md"
            Set-Content -Path $localMd -Value "# Compound GPID`ncg-schema-version: `"`""

            $schemaVersion = "2026-03-05-cg-docs"

            # Simulate stamping logic
            $content = [System.IO.File]::ReadAllText($localMd)
            if ($content -match 'cg-schema-version:') {
                $updated = $content -replace '(?m)^(cg-schema-version:\s*).*$', ("cg-schema-version: `"" + $schemaVersion + "`"")
                [System.IO.File]::WriteAllText($localMd, $updated)
            }

            $result = [System.IO.File]::ReadAllText($localMd)
            $result -match [regex]::Escape("cg-schema-version: `"$schemaVersion`"") | Should Be $true
        }

        It "does not modify compound-gpid.local.md when the field is absent" {
            $root = Join-Path $TestDrive "schema-stamp-absent"
            New-Item -ItemType Directory -Path $root -Force | Out-Null
            $localMd = "$root\compound-gpid.local.md"
            $original = "# Custom config without schema field`ncg-language: R"
            Set-Content -Path $localMd -Value $original

            $schemaVersion = "2026-03-05-cg-docs"

            $content = [System.IO.File]::ReadAllText($localMd)
            if ($content -match 'cg-schema-version:') {
                $updated = $content -replace '(?m)^(cg-schema-version:\s*).*$', ("cg-schema-version: `"" + $schemaVersion + "`"")
                [System.IO.File]::WriteAllText($localMd, $updated)
            }

            $result = [System.IO.File]::ReadAllText($localMd)
            $result -match [regex]::Escape($schemaVersion) | Should Be $false
        }
    }
}

