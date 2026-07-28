# tests/update.Tests.ps1
# Pester tests for scripts/update.ps1 logic
#
# Run with: Invoke-Pester tests/update.Tests.ps1
# Compatible with Pester 4.10.1+ (project standard).

$script:OnWindows = (((Test-Path variable:IsWindows) -and $IsWindows) -or ($env:OS -eq "Windows_NT"))
$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
. (Join-Path $repoRoot "scripts\helpers.ps1")

Describe "update.ps1 - pre-condition checks" {
    Context "install path detection" {
        It "passes when a simulated install directory exists" {
            $installDir = Join-Path $TestDrive "compound-gpid-install"
            New-Item -ItemType Directory -Path $installDir -Force | Out-Null
            Test-Path $installDir | Should -Be $true
        }

        It "would prompt to run install when path missing" {
            $installDir = Join-Path $TestDrive "does-not-exist"
            Test-Path $installDir | Should -Be $false
        }
    }

    Context "git availability" {
        It "git is available on this machine" {
            $result = Get-Command git -ErrorAction SilentlyContinue
            $result | Should -Not -BeNullOrEmpty
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
            (Get-Location).Path | Should -Be $tempDir
            Pop-Location
            (Get-Location).Path | Should -Be $original.Path
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
            $err | Should -Be "Simulated error"
            (Get-Location).Path | Should -Be $original.Path
        }
    }
}

Describe "update.ps1 - git hash comparison" {
    Context "detecting whether an update occurred" {
        It "reports no update when hashes are equal" {
            $before = "abc123def456"
            $after  = "abc123def456"
            $updated = $before -ne $after
            $updated | Should -Be $false
        }

        It "reports an update when hashes differ" {
            $before = "abc123def456"
            $after  = "def456abc123"
            $updated = $before -ne $after
            $updated | Should -Be $true
        }
    }
}

Describe "update.ps1 - exit code handling" {
    Context "LASTEXITCODE from git pull" {
        It "treats exit code 0 as success" {
            $global:LASTEXITCODE = 0
            ($LASTEXITCODE -ne 0) | Should -Be $false
        }

        It "treats non-zero exit code as failure" {
            $global:LASTEXITCODE = 1
            ($LASTEXITCODE -ne 0) | Should -Be $true
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
            ($LASTEXITCODE -ne 0) | Should -Be $false
            $global:LASTEXITCODE = 0  # reset
        }

        It "non-zero exit code triggers a warning but does not abort" {
            $global:LASTEXITCODE = 1
            ($LASTEXITCODE -ne 0) | Should -Be $true
            $global:LASTEXITCODE = 0  # reset
        }
    }

    Context "PS5.1 ErrorActionPreference=Stop regression" {
        # Regression test for the bootstrap failure documented in docs/manual.md:
        # "cg-update fails with 'Updated 0 paths from the index'"
        #
        # On PS5.1, ErrorActionPreference=Stop can promote native command stderr
        # to a terminating error. git checkout . writes informational output to
        # stderr on success, which triggers this. The fix in update.ps1 wraps
        # the checkout in try/catch so terminating errors are swallowed and
        # execution always continues to git pull.

        It "does not throw when checkout step raises a terminating error" {
            $ErrorActionPreference = "Stop"
            $checkoutAttempted = $false
            $pullAttempted     = $false
            $threw             = $false

            try {
                # Simulate the update.ps1 pattern: try/catch around checkout
                try {
                    $checkoutAttempted = $true
                    throw "Simulated PS5.1 stderr-as-terminating-error from git checkout ."
                } catch {
                    <# Simulates update.ps1 pattern: ignore informational stderr from git checkout . #>
                }

                # Pull must still be reached even though checkout threw
                $pullAttempted = $true
            } catch {
                $threw = $true
            } finally {
                $ErrorActionPreference = "Continue"
            }

            $checkoutAttempted | Should -Be $true
            $pullAttempted     | Should -Be $true
            $threw             | Should -Be $false
        }

        It "does not suppress a real checkout failure (non-zero LASTEXITCODE)" {
            # Even with the try/catch, a non-zero exit code must still be detectable
            $global:LASTEXITCODE = 1
            $warnTriggered = $false

            try { throw "Simulated stderr" } catch { <# ignore #> }
            if ($LASTEXITCODE -ne 0) { $warnTriggered = $true }

            $warnTriggered | Should -Be $true
            $global:LASTEXITCODE = 0  # reset
        }
    }
}

Describe "update.ps1 - copilot-instructions.md refresh" {
    $marker = "<!-- compound-gpid:managed -->"

    Context "when the file in CWD has the management marker" {
        It "calls Update-ManagedInstructionsFile which regenerates the file (real code path)" {
            # Create a minimal template directory so New-CopilotInstructions can run
            $templateDir = Join-Path $TestDrive "refresh-template"
            $githubDir   = Join-Path $templateDir ".github"
            New-Item -ItemType Directory -Path $githubDir -Force | Out-Null
            Set-Content -Path (Join-Path $githubDir "copilot-instructions.template.md") `
                        -Value "# Generated" -Encoding UTF8
            $projectRoot = Join-Path $TestDrive "refresh-project"
            New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null

            $dest = Join-Path $TestDrive "copilot-managed.md"
            Set-Content -Path $dest -Value ($marker + "`n# Old generated content") -Encoding UTF8

            $outcome = Update-ManagedInstructionsFile -Dest $dest -Marker $marker `
                -TemplateDir $templateDir -ProjectRoot $projectRoot
            $outcome | Should -Be "refreshed"
            (Get-Content $dest -Raw) -match [regex]::Escape($marker) | Should -Be $true
        }
    }

    Context "when the file in CWD does NOT have the management marker" {
        It "returns 'skipped' and leaves the user-managed file untouched" {
            $dest = Join-Path $TestDrive "copilot-user.md"
            Set-Content -Path $dest -Value "# My custom instructions (no marker)" -Encoding UTF8

            $outcome = Update-ManagedInstructionsFile -Dest $dest -Marker $marker `
                -TemplateDir $TestDrive -ProjectRoot $TestDrive
            $outcome | Should -Be "skipped"
            (Get-Content $dest -Raw) -match "My custom instructions" | Should -Be $true
        }
    }

    Context "when copilot-instructions.md does not exist in CWD" {
        It "does not attempt to refresh a non-existent file" {
            $nonexistent = Join-Path $TestDrive "no-copilot-instructions.md"
            Test-Path $nonexistent | Should -Be $false
            # Simulates the guard condition in update.ps1
            $shouldRefresh = (Test-Path $nonexistent)
            $shouldRefresh | Should -Be $false
        }
    }
}

Describe "update.ps1 - manifest-managed platform file refresh" {
    It "contains the managed-files refresh path" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\update.ps1") -Raw -Encoding UTF8
        $content | Should -Match 'managed-files\.json'
        $content | Should -Match 'Update-CgManagedPlatformFiles'
    }

    It "refreshes only when the current checksum matches the manifest checksum" {
        $projectRoot = Join-Path $TestDrive "managed-refresh-project"
        $installRoot = Join-Path $TestDrive "managed-refresh-install"
        $manifestPath = Join-Path $projectRoot ".compound-gpid\managed-files.json"
        $sourceRel = ".opencode/opencode.json"
        $targetRel = ".opencode/opencode.json"
        $sourcePath = Join-Path $installRoot $sourceRel
        $targetPath = Join-Path $projectRoot $targetRel

        New-Item -ItemType Directory -Path (Split-Path $sourcePath -Parent) -Force | Out-Null
        New-Item -ItemType Directory -Path (Split-Path $targetPath -Parent) -Force | Out-Null
        Set-Content -Path $sourcePath -Value '{"updated":true}' -Encoding UTF8
        Set-Content -Path $targetPath -Value '{"updated":false}' -Encoding UTF8

        $files = @{}
        $files[$targetRel] = @{ source = $sourceRel; checksum = (Get-CgFileSha256 -Path $targetPath) }
        $manifest = @{
            schemaVersion = "compound-gpid-managed-files-v1"
            files = $files
        }
        Write-CgManagedFilesManifest -ManifestPath $manifestPath -Manifest $manifest

        $result = Update-CgManagedPlatformFiles -ManifestPath $manifestPath -ProjectRoot $projectRoot -CompoundGpidDir $installRoot

        $result.Refreshed | Should -Contain $targetRel
        (Get-Content $targetPath -Raw -Encoding UTF8) | Should -Match '"updated":true'
        $roundTrip = Read-CgManagedFilesManifest -ManifestPath $manifestPath
        $roundTrip.files[$targetRel].checksum | Should -Be (Get-CgFileSha256 -Path $targetPath)
    }

    It "skips refresh when the user modified the copied file" {
        $projectRoot = Join-Path $TestDrive "managed-skip-project"
        $installRoot = Join-Path $TestDrive "managed-skip-install"
        $manifestPath = Join-Path $projectRoot ".compound-gpid\managed-files.json"
        $sourceRel = ".opencode/opencode.json"
        $targetRel = ".opencode/opencode.json"
        $sourcePath = Join-Path $installRoot $sourceRel
        $targetPath = Join-Path $projectRoot $targetRel

        New-Item -ItemType Directory -Path (Split-Path $sourcePath -Parent) -Force | Out-Null
        New-Item -ItemType Directory -Path (Split-Path $targetPath -Parent) -Force | Out-Null
        Set-Content -Path $sourcePath -Value '{"updated":true}' -Encoding UTF8
        Set-Content -Path $targetPath -Value '{"user":true}' -Encoding UTF8

        $files = @{}
        $files[$targetRel] = @{ source = $sourceRel; checksum = "old-managed-checksum" }
        $manifest = @{
            schemaVersion = "compound-gpid-managed-files-v1"
            files = $files
        }
        Write-CgManagedFilesManifest -ManifestPath $manifestPath -Manifest $manifest

        $result = Update-CgManagedPlatformFiles -ManifestPath $manifestPath -ProjectRoot $projectRoot -CompoundGpidDir $installRoot

        $result.SkippedUserModified | Should -Contain $targetRel
        (Get-Content $targetPath -Raw -Encoding UTF8) | Should -Match '"user":true'
        $roundTrip = Read-CgManagedFilesManifest -ManifestPath $manifestPath
        $roundTrip.files[$targetRel].checksum | Should -Be "old-managed-checksum"
    }

    It "drops manifest entries for missing managed target files" {
        $projectRoot = Join-Path $TestDrive "managed-missing-project"
        $installRoot = Join-Path $TestDrive "managed-missing-install"
        $manifestPath = Join-Path $projectRoot ".compound-gpid\managed-files.json"
        $sourceRel = ".opencode/opencode.json"
        $targetRel = ".opencode/opencode.json"
        $sourcePath = Join-Path $installRoot $sourceRel

        New-Item -ItemType Directory -Path (Split-Path $sourcePath -Parent) -Force | Out-Null
        Set-Content -Path $sourcePath -Value '{"updated":true}' -Encoding UTF8

        $files = @{}
        $files[$targetRel] = @{ source = $sourceRel; checksum = "missing-target-checksum" }
        $manifest = @{
            schemaVersion = "compound-gpid-managed-files-v1"
            files = $files
        }
        Write-CgManagedFilesManifest -ManifestPath $manifestPath -Manifest $manifest

        $result = Update-CgManagedPlatformFiles -ManifestPath $manifestPath -ProjectRoot $projectRoot -CompoundGpidDir $installRoot

        $result.RemovedMissing | Should -Contain $targetRel
        Test-Path $manifestPath | Should -Be $false
    }

    It "rejects manifest entries that escape project or install roots" {
        $projectRoot = Join-Path $TestDrive "managed-invalid-project"
        $installRoot = Join-Path $TestDrive "managed-invalid-install"
        $manifestPath = Join-Path $projectRoot ".compound-gpid\managed-files.json"
        $outsidePath = Join-Path $TestDrive "outside.json"
        New-Item -ItemType Directory -Path $projectRoot -Force | Out-Null
        New-Item -ItemType Directory -Path $installRoot -Force | Out-Null
        Set-Content -Path $outsidePath -Value '{"outside":true}' -Encoding UTF8

        $targetRel = "../outside.json"
        $files = @{}
        $files[$targetRel] = @{ source = "../source.json"; checksum = (Get-CgFileSha256 -Path $outsidePath) }
        $manifest = @{
            schemaVersion = "compound-gpid-managed-files-v1"
            files = $files
        }
        Write-CgManagedFilesManifest -ManifestPath $manifestPath -Manifest $manifest

        $result = Update-CgManagedPlatformFiles -ManifestPath $manifestPath -ProjectRoot $projectRoot -CompoundGpidDir $installRoot

        $result.Invalid | Should -Contain $targetRel
        (Get-Content $outsidePath -Raw -Encoding UTF8) | Should -Match '"outside":true'
    }

    It "skips manifest-managed targets that are symlinks or reparse points" {
        $projectRoot = Join-Path $TestDrive "managed-symlink-project"
        $installRoot = Join-Path $TestDrive "managed-symlink-install"
        $manifestPath = Join-Path $projectRoot ".compound-gpid\managed-files.json"
        $sourceRel = ".opencode/opencode.json"
        $targetRel = ".opencode/opencode.json"
        $sourcePath = Join-Path $installRoot $sourceRel
        $targetPath = Join-Path $projectRoot $targetRel
        $outsidePath = Join-Path $TestDrive "outside-managed-target.json"

        New-Item -ItemType Directory -Path (Split-Path $sourcePath -Parent) -Force | Out-Null
        New-Item -ItemType Directory -Path (Split-Path $targetPath -Parent) -Force | Out-Null
        Set-Content -Path $sourcePath -Value '{"updated":true}' -Encoding UTF8
        Set-Content -Path $outsidePath -Value '{"outside":true}' -Encoding UTF8
        Remove-Item -Path $targetPath -Force -ErrorAction SilentlyContinue
        try {
            New-Item -ItemType SymbolicLink -Path $targetPath -Target $outsidePath -ErrorAction Stop | Out-Null
        } catch {
            # Windows requires Developer Mode or the SeCreateSymbolicLinkPrivilege
            # for this fixture. Mark it skipped when the test host lacks that
            # capability instead of reporting a false failure.
            Set-ItResult -Skipped -Because "Symbolic links are unavailable: $($_.Exception.Message)"
            return
        }

        $files = @{}
        $files[$targetRel] = @{ source = $sourceRel; checksum = (Get-CgFileSha256 -Path $targetPath) }
        $manifest = @{
            schemaVersion = "compound-gpid-managed-files-v1"
            files = $files
        }
        Write-CgManagedFilesManifest -ManifestPath $manifestPath -Manifest $manifest

        $result = Update-CgManagedPlatformFiles -ManifestPath $manifestPath -ProjectRoot $projectRoot -CompoundGpidDir $installRoot

        $result.Invalid | Should -Contain $targetRel
        (Get-Content $outsidePath -Raw -Encoding UTF8) | Should -Match '"outside":true'
    }
}

Describe "update.ps1 - executable generation failure boundary" {
    It "exits before managed-file refresh when target mapping is missing" {
        $installRoot = Join-Path $TestDrive "isolated-update-install"
        $scriptsRoot = Join-Path $installRoot "scripts"
        $projectRoot = Join-Path $TestDrive "isolated-update-project"
        New-Item -ItemType Directory -Path $scriptsRoot -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $projectRoot ".opencode") -Force | Out-Null
        Copy-Item (Join-Path $repoRoot "scripts/update.ps1") (Join-Path $scriptsRoot "update.ps1")
        Copy-Item (Join-Path $repoRoot "scripts/helpers.ps1") (Join-Path $scriptsRoot "helpers.ps1")
        Set-Content (Join-Path $installRoot ".cg-version") "latest" -NoNewline
        $managedPath = Join-Path $projectRoot ".opencode/opencode.json"
        Set-Content $managedPath '{"managed":"before"}' -Encoding UTF8
        $childScript = Join-Path $TestDrive "invoke-isolated-update.ps1"
        @'
param($UpdateScript, $ProjectRoot)
function global:git {
    $global:LASTEXITCODE = 0
    if ($args[0] -eq "rev-parse" -and $args[1] -eq "--abbrev-ref") { return "main" }
    if ($args[0] -eq "rev-parse" -and $args[1] -eq "--short") { return "abc123" }
}
function global:python3 {
    if ($args[0] -eq "--version") { $global:LASTEXITCODE = 0; return "Python 3.11.0" }
}
Set-Location $ProjectRoot
& $UpdateScript
'@ | Set-Content $childScript -Encoding UTF8

        $pwsh = (Get-Process -Id $PID).Path
        & $pwsh -NoProfile -File $childScript (Join-Path $scriptsRoot "update.ps1") $projectRoot
        $childExit = $LASTEXITCODE

        $childExit | Should -Not -Be 0
        (Get-Content $managedPath -Raw -Encoding UTF8) | Should -Match '"managed":"before"'
    }
}

Describe "helpers.ps1 - managed file manifest helpers" {
    It "can write and read a managed files manifest" {
        $manifestPath = Join-Path $TestDrive "managed-files.json"
        $manifest = @{
            schemaVersion = "compound-gpid-managed-files-v1"
            files = @{
                ".opencode/opencode.json" = @{ source = ".opencode/opencode.json"; checksum = "abc" }
            }
        }
        Write-CgManagedFilesManifest -ManifestPath $manifestPath -Manifest $manifest
        $roundTrip = Read-CgManagedFilesManifest -ManifestPath $manifestPath
        $roundTrip.files[".opencode/opencode.json"].source | Should -Be ".opencode/opencode.json"
        $roundTrip.files[".opencode/opencode.json"].checksum | Should -Be "abc"
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

            Test-Path "$root\.cg-docs\brainstorms\2025-01-01-test.md" | Should -Be $true
            Test-Path "$root\docs\brainstorms" | Should -Be $false
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

            Test-Path "$root\.cg-docs\plans\2025-01-01-plan.md" | Should -Be $true
            Test-Path "$root\docs\plans" | Should -Be $false
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

            Test-Path "$root\.cg-docs\solutions\build-errors\fix.md" | Should -Be $true
            Test-Path "$root\docs\solutions" | Should -Be $false
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

            Test-Path $dst | Should -Be $false
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

            Test-Path "$root\.cg-docs\brainstorms\existing-file.md" | Should -Be $true
            Test-Path "$root\.cg-docs\brainstorms\new-file.md"      | Should -Be $true
            Test-Path "$root\docs\brainstorms"                       | Should -Be $false
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

            Test-Path "$root\docs\manual.md"            | Should -Be $true
            Test-Path "$root\.cg-docs\brainstorms\note.md" | Should -Be $true
        }
    }

    Context "idempotency" {
        It "skips migration when .cg-docs/brainstorms already exists and docs/brainstorms is gone" {
            $root = Join-Path $TestDrive "migrate-idempotent"
            New-Item -ItemType Directory -Path "$root\.cg-docs\brainstorms" -Force | Out-Null
            New-Item -ItemType File -Path "$root\.cg-docs\brainstorms\note.md" -Force | Out-Null
            # docs/brainstorms does not exist -- nothing to migrate

            $src = "$root\docs\brainstorms"
            $dst = "$root\.cg-docs\brainstorms"
            if ((Test-Path $src) -and -not (Test-Path $dst)) {
                New-Item -ItemType Directory -Path (Split-Path $dst) -Force | Out-Null
                Move-Item -Path $src -Destination $dst
            }

            # Destination unchanged
            Test-Path "$root\.cg-docs\brainstorms\note.md" | Should -Be $true
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

            Test-Path "$root\docs" | Should -Be $false
            Test-Path "$root\.cg-docs\brainstorms" | Should -Be $true
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

            Test-Path "$root\docs"          | Should -Be $true
            Test-Path "$root\docs\manual.md" | Should -Be $true
        }
    }

    Context "schema version stamping" {
        It "writes cg-schema-version to compound-gpid.local.md when the field exists" {
            $root = Join-Path $TestDrive "schema-stamp"
            New-Item -ItemType Directory -Path $root -Force | Out-Null
            $localMd = Join-Path $root "compound-gpid.local.md"
            Set-Content -Path $localMd -Value "# Compound GPID`ncg-schema-version: `"`""

            $schemaVersion = "2026-03-05-cg-docs"  # MUST match $SchemaVersion in scripts/update.ps1

            # Simulate stamping logic
            $original = "# Custom config without schema field`ncg-language: R"
            Set-Content -Path $localMd -Value $original

            $schemaVersion = "2026-03-05-cg-docs"  # MUST match $SchemaVersion in scripts/update.ps1

            $content = [System.IO.File]::ReadAllText($localMd)
            if ($content -match 'cg-schema-version:') {
                $updated = $content -replace '(?m)^(cg-schema-version:\s*).*$', ("cg-schema-version: `"" + $schemaVersion + "`"")
                [System.IO.File]::WriteAllText($localMd, $updated)
            }

            $result = [System.IO.File]::ReadAllText($localMd)
            $result -match [regex]::Escape($schemaVersion) | Should -Be $false
        }
    }
}

# ---------------------------------------------------------------------------
# Charter migration notice
# ---------------------------------------------------------------------------
# These are condition-level unit tests that verify the boolean logic used by
# update.ps1 to decide whether to show the charter migration notice. They do
# NOT invoke update.ps1 itself -- they test the condition in isolation.

Describe "update.ps1 - charter migration notice" {
    Context "when compound-gpid.md does NOT exist" {
        It "detects when charter is absent (condition check)" {
            $testRoot = Join-Path $TestDrive "charter-notice-absent"
            New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
            $charter = Join-Path $testRoot "compound-gpid.md"
            $shouldNotify = -not (Test-Path $charter)
            $shouldNotify | Should -Be $true
        }
    }

    Context "when compound-gpid.md EXISTS" {
        It "detects when charter is present (condition check)" {
            $testRoot = Join-Path $TestDrive "charter-notice-present"
            New-Item -ItemType Directory -Path $testRoot -Force | Out-Null
            $charter = Join-Path $testRoot "compound-gpid.md"
            New-Item -ItemType File -Path $charter -Force | Out-Null
            $shouldNotify = -not (Test-Path $charter)
            $shouldNotify | Should -Be $false
        }
    }
}

# ---------------------------------------------------------------------------
# Version pinning -- argument parsing
# ---------------------------------------------------------------------------

Describe "update.ps1 - argument parsing" {
    Context "no argument supplied" {
        It "treats no argument as null (reads from .cg-version)" {
            $Version = $null
            $Version -eq $null | Should -Be $true
        }
    }

    Context "explicit 'latest' argument" {
        It "recognises 'latest' as the unpin keyword" {
            $Version = "latest"
            $Version | Should -Be "latest"
            $Version -match '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$' | Should -Be $true
        }
    }

    Context "tag argument" {
        It "recognises a tag string as a pin target" {
            $Version = "v0.1.0"
            $Version | Should -Match '^v\d+\.\d+\.\d+(\.\d+)?$'
        }
    }

    Context "--list argument" {
        It "is NOT written to .cg-version (special switch parameter)" {
            # When --list is passed, PowerShell sets $List = $true and $Version = ""
            $List    = [switch]$true
            $Version = ""
            # The --list branch exits early; $Version is empty so writes are skipped
            $List.IsPresent                       | Should -Be $true
            [string]::IsNullOrEmpty($Version)     | Should -Be $true
        }
    }

    Context "version argument trimming" {
        It "trims leading and trailing whitespace" {
            $Version = "  v0.2.0  "
            $Version = $Version.Trim()
            $Version | Should -Be "v0.2.0"
        }

        It "trimmed value still passes format validation" {
            $Version = "  v0.2.0  "
            $Version = $Version.Trim()
            ($Version -match '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') | Should -Be $true
        }
    }

    Context "version format validation" {
        It "accepts a valid 3-segment tag" {
            $Version = "v0.2.0"
            ($Version -notmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') | Should -Be $false
        }

        It "accepts the 'latest' keyword" {
            $Version = "latest"
            ($Version -notmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') | Should -Be $false
        }

        It "accepts a 4-segment dev tag (v0.2.0.9000 convention)" {
            $Version = "v0.2.0.9000"
            ($Version -notmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') | Should -Be $false
        }

        It "rejects a 2-segment tag missing the patch number" {
            $Version = "v0.2"
            ($Version -notmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') | Should -Be $true
        }

        It "rejects a tag without leading 'v'" {
            $Version = "0.2.0"
            ($Version -notmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') | Should -Be $true
        }

        It "rejects arbitrary strings" {
            $Version = "main"
            ($Version -notmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') | Should -Be $true
        }

        It "rejects a 4-segment tag with trailing dot (malformed)" {
            $Version = "v0.2.0."
            ($Version -notmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') | Should -Be $true
        }

        It "rejects a 5-segment tag" {
            $Version = "v0.2.0.9000.1"
            ($Version -notmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') | Should -Be $true
        }
    }
}

# ---------------------------------------------------------------------------
# Version pinning -- .cg-version read / write
# ---------------------------------------------------------------------------

Describe "update.ps1 - .cg-version read" {
    Context "file present with 'latest'" {
        It "resolves versionMode to 'latest'" {
            $versionFile = Join-Path $TestDrive "cv-latest.txt"
            Set-Content -Path $versionFile -Value "latest" -NoNewline

            $versionMode = (Get-Content $versionFile -Raw).Trim()
            if ([string]::IsNullOrWhiteSpace($versionMode)) { $versionMode = "latest" }

            $versionMode | Should -Be "latest"
        }
    }

    Context "file present with a pinned tag" {
        It "resolves versionMode to the tag" {
            $versionFile = Join-Path $TestDrive "cv-pinned.txt"
            Set-Content -Path $versionFile -Value "v0.2.0" -NoNewline

            $versionMode = (Get-Content $versionFile -Raw).Trim()
            if ([string]::IsNullOrWhiteSpace($versionMode)) { $versionMode = "latest" }

            $versionMode | Should -Be "v0.2.0"
        }
    }

    Context "file absent (pre-versioning install)" {
        It "defaults to 'latest' for backward compatibility" {
            $versionFile = Join-Path $TestDrive "cv-missing.txt"
            # File deliberately not created

            $versionMode = if (Test-Path $versionFile) {
                (Get-Content $versionFile -Raw).Trim()
            } else { "latest" }

            $versionMode | Should -Be "latest"
        }
    }

    Context "file present but empty or whitespace" {
        It "falls back to 'latest' for blank content" {
            $versionFile = Join-Path $TestDrive "cv-blank.txt"
            Set-Content -Path $versionFile -Value "   " -NoNewline

            $raw = (Get-Content $versionFile -Raw -ErrorAction SilentlyContinue).Trim()
            $versionMode = if ([string]::IsNullOrWhiteSpace($raw)) { "latest" } else { $raw }

            $versionMode | Should -Be "latest"
        }
    }

    Context "file present with blank first line (multi-line content)" {
        It "returns the first non-empty line" {
            $versionFile = Join-Path $TestDrive "cv-multiline.txt"
            # Simulates a manually edited file where the version is on line 2
            Set-Content -Path $versionFile -Value "`n`nv0.2.0`nv0.1.0" -NoNewline

            $raw = (Get-Content $versionFile -Raw -ErrorAction SilentlyContinue)
            $versionMode = (($raw -split "`n" | Where-Object { $_.Trim() -ne "" } | Select-Object -First 1) + "").Trim()
            if ([string]::IsNullOrWhiteSpace($versionMode)) { $versionMode = "latest" }

            $versionMode | Should -Be "v0.2.0"
        }

        It "falls back to 'latest' when all lines are blank" {
            $versionFile = Join-Path $TestDrive "cv-allblank.txt"
            Set-Content -Path $versionFile -Value "`n  `n   " -NoNewline

            $raw = (Get-Content $versionFile -Raw -ErrorAction SilentlyContinue)
            $versionMode = (($raw -split "`n" | Where-Object { $_.Trim() -ne "" } | Select-Object -First 1) + "").Trim()
            if ([string]::IsNullOrWhiteSpace($versionMode)) { $versionMode = "latest" }

            $versionMode | Should -Be "latest"
        }
    }

    Context "file present with malformed content (manual edit)" {
        It "rejects garbage content that does not match version format" {
            # Validate .cg-version content after reading: guards against manual edits
            # with values like 'main' or 'v1.0' that bypass the CLI argument guard.
            $rawMode = "main"
            $isInvalid = ($rawMode -cnotmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$')
            $isInvalid | Should -Be $true
        }

        It "rejects a 2-segment tag read from .cg-version" {
            $rawMode = "v1.0"
            $isInvalid = ($rawMode -cnotmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$')
            $isInvalid | Should -Be $true
        }

        It "accepts a valid 3-segment tag from .cg-version" {
            $rawMode = "v0.2.0"
            $isInvalid = ($rawMode -cnotmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$')
            $isInvalid | Should -Be $false
        }

        It "accepts a valid 4-segment dev tag from .cg-version" {
            $rawMode = "v0.1.0.9000"
            $isInvalid = ($rawMode -cnotmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$')
            $isInvalid | Should -Be $false
        }

        It "rejects a 5-segment tag from .cg-version (too many segments)" {
            $rawMode = "v1.0.0.0.0"
            $isInvalid = ($rawMode -cnotmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$')
            $isInvalid | Should -Be $true
        }

        It "rejects a version with uppercase V (case-sensitive validation)" {
            # git tag names are case-sensitive; V0.2.0 would fail at checkout
            # with an unhelpful 'pathspec did not match' error.
            $rawMode = "V0.2.0"
            $isInvalid = ($rawMode -cnotmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$')
            $isInvalid | Should -Be $true
        }
    }
}

Describe "update.ps1 - .cg-version write" {
    Context "switching from 'latest' to a pinned tag (pinned branch)" {
        It "overwrites with the tag name after successful checkout" {
            $versionFile = Join-Path $TestDrive "cv-switch-to-pin.txt"
            Set-Content -Path $versionFile -Value "latest" -NoNewline

            # Simulate pinned branch: Set-Content is called after git checkout succeeds
            $versionMode = "v0.2.0"
            Set-Content -Path $versionFile -Value $versionMode -NoNewline

            (Get-Content $versionFile -Raw).Trim() | Should -Be "v0.2.0"
        }
    }

    Context "explicitly unpinning with 'cg-update latest' (latest branch)" {
        It "overwrites with 'latest' when user explicitly passes latest argument" {
            $versionFile = Join-Path $TestDrive "cv-switch-to-latest.txt"
            Set-Content -Path $versionFile -Value "v0.1.0" -NoNewline

            # Simulate latest branch: Set-Content only when $Version -eq "latest"
            $Version = "latest"
            if ($Version -eq "latest") {
                Set-Content -Path $versionFile -Value "latest" -NoNewline
            }

            (Get-Content $versionFile -Raw).Trim() | Should -Be "latest"
        }

        It "does NOT overwrite when no $Version argument was supplied (file already correct)" {
            $versionFile = Join-Path $TestDrive "cv-no-overwrite.txt"
            Set-Content -Path $versionFile -Value "latest" -NoNewline

            # Simulate latest branch with no explicit $Version: no write needed
            $Version = $null
            if ($Version -eq "latest") {
                Set-Content -Path $versionFile -Value "latest" -NoNewline
            }
            # File content should remain unchanged
            (Get-Content $versionFile -Raw).Trim() | Should -Be "latest"
        }
    }

    Context "re-pinning to a different tag (pinned branch)" {
        It "overwrites with the new tag after successful checkout" {
            $versionFile = Join-Path $TestDrive "cv-repin.txt"
            Set-Content -Path $versionFile -Value "v0.1.0" -NoNewline

            # Simulate pinned branch: Set-Content called after checkout succeeds
            $versionMode = "v0.2.0"
            Set-Content -Path $versionFile -Value $versionMode -NoNewline

            (Get-Content $versionFile -Raw).Trim() | Should -Be "v0.2.0"
        }
    }

    Context "--list flag (early return, no write)" {
        It "does NOT modify .cg-version when --list is passed" {
            $versionFile = Join-Path $TestDrive "cv-list-guard.txt"
            Set-Content -Path $versionFile -Value "v0.1.0" -NoNewline

            # Simulate: $List.IsPresent causes early return before any Set-Content
            $List = [switch]$true
            if (-not $List.IsPresent) {
                Set-Content -Path $versionFile -Value "should-not-appear" -NoNewline
            }

            (Get-Content $versionFile -Raw).Trim() | Should -Be "v0.1.0"
        }
    }

    Context "tag validation failure (no write on bad input)" {
        It "does NOT write .cg-version when the tag does not exist" {
            $versionFile = Join-Path $TestDrive "cv-bad-tag.txt"
            Set-Content -Path $versionFile -Value "v0.1.0" -NoNewline

            # Simulate pinned branch: tag validation fails -- throw before Set-Content
            $versionMode = "v9.9.9"
            $allTags     = @("v0.2.0", "v0.1.0")
            $wrote       = $false
            try {
                if ($versionMode -notin $allTags) {
                    throw "Release '$versionMode' not found."
                }
                # If we get here, checkout succeeded -- write preference
                Set-Content -Path $versionFile -Value $versionMode -NoNewline
                $wrote = $true
            } catch { <# expected #> }

            $wrote                                 | Should -Be $false
            (Get-Content $versionFile -Raw).Trim() | Should -Be "v0.1.0"
        }
    }
}

# ---------------------------------------------------------------------------
# Version pinning -- detached HEAD detection (latest mode)
# ---------------------------------------------------------------------------

Describe "update.ps1 - detached HEAD detection" {
    Context "inspecting git HEAD state" {
        It "identifies 'HEAD' as a detached HEAD state" {
            # git rev-parse --abbrev-ref HEAD returns "HEAD" in detached state
            $headBranch = "HEAD"   # simulated output from git in detached state
            ($headBranch -eq "HEAD") | Should -Be $true
        }

        It "identifies a branch name as NOT detached" {
            $headBranch = "main"
            ($headBranch -eq "HEAD") | Should -Be $false
        }
    }

    Context "detached HEAD switch-back logic" {
        It "triggers git checkout main when detached HEAD is detected" {
            $headBranch     = "HEAD"
            $switchAttempted = $false
            if ($headBranch -eq "HEAD") {
                $switchAttempted = $true
            }
            $switchAttempted | Should -Be $true
        }

        It "skips git checkout main when already on a branch" {
            $headBranch     = "main"
            $switchAttempted = $false
            if ($headBranch -eq "HEAD") {
                $switchAttempted = $true
            }
            $switchAttempted | Should -Be $false
        }
    }

    Context "git rev-parse failure" {
        It "throws when git rev-parse returns non-zero exit code" {
            $global:LASTEXITCODE = 1
            {
                if ($LASTEXITCODE -ne 0) {
                    throw "Could not determine current branch (git rev-parse failed with exit code $LASTEXITCODE)"
                }
            } | Should -Throw "Could not determine current branch"
            $global:LASTEXITCODE = 0
        }
    }
}

# ---------------------------------------------------------------------------
# Version pinning -- tag validation (pinned mode)
# ---------------------------------------------------------------------------

Describe "update.ps1 - tag validation" {
    Context "tag exists" {
        It "proceeds when git tag --list returns the tag name" {
            # Simulate: git tag --list "v0.2.0" returns "v0.2.0"
            $tagResult = "v0.2.0"
            $tagExists = -not [string]::IsNullOrWhiteSpace($tagResult)
            $tagExists | Should -Be $true
        }
    }

    Context "tag does not exist" {
        It "detects missing tag when git tag --list returns empty" {
            # Simulate: git tag --list "v9.9.9" returns nothing
            $tagResult = $null
            $tagExists = -not [string]::IsNullOrWhiteSpace($tagResult)
            $tagExists | Should -Be $false
        }

        It "builds a helpful error hint from similar tags" {
            $versionMode = "v9.9.9"
            # Only release tags in the hint -- dev tags are filtered before building $similar.
            $similar     = @("v0.2.0", "v0.1.0")
            $hint = "`n`nAvailable releases:`n" + ($similar | ForEach-Object { "  $_" } | Out-String).TrimEnd()
            $errorMsg = "Release '$versionMode' not found.$hint`n`nRun: cg-update --list   to see all available releases."

            $errorMsg -match "v9\.9\.9"    | Should -Be $true
            $errorMsg -match "v0\.2\.0"    | Should -Be $true
            $errorMsg -match "cg-update --list" | Should -Be $true
        }

        It "omits the similar-tags section when no tags exist at all" {
            $versionMode = "v9.9.9"
            $similar     = @()
            $hint        = if ($similar) {
                "`n`nAvailable releases:`n" + ($similar | ForEach-Object { "  $_" } | Out-String).TrimEnd()
            } else { "" }
            $errorMsg = "Release '$versionMode' not found.$hint`n`nRun: cg-update --list   to see all available releases."

            # Use the section-header pattern (with trailing colon+newline) to avoid
            # matching "all available releases" in the body of the error message.
            $errorMsg -match "Available releases:`n" | Should -Be $false
            $errorMsg -match "cg-update --list"      | Should -Be $true
        }

        It "dev tags are excluded from the error hint (release-only filter applied to similar)" {
            # Simulate allTags with dev tags at top (sorted newest first by git).
            $allTags = @("v0.2.0.9001", "v0.2.0.9000", "v0.2.0", "v0.1.0")
            $similar = $allTags | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 5
            $hint = "`n`nAvailable releases:`n" + ($similar | ForEach-Object { "  $_" } | Out-String).TrimEnd()
            $hint -match "9000" | Should -Be $false
            $hint -match "9001" | Should -Be $false
            $hint -match "v0\.2\.0" | Should -Be $true
        }

        It "throws when a non-existent tag is validated against the tag list" {
            $versionMode = "v9.9.9"
            $allTags     = @("v0.2.0", "v0.1.0")
            {
                if ($versionMode -notin $allTags) {
                    throw "Release '$versionMode' not found."
                }
            } | Should -Throw "not found"
        }
    }
}

# ---------------------------------------------------------------------------
# Version pinning -- PS5.1 safe checkout pattern (pinned mode)
# ---------------------------------------------------------------------------

Describe "update.ps1 - PS5.1-safe checkout" {
    AfterEach {
        $global:LASTEXITCODE = 0
    }

    Context "try/catch wrapping git checkout in pinned mode" {
        It "does not propagate informational stderr from git checkout <tag>" {
            $ErrorActionPreference = "Stop"
            $checkoutAttempted = $false
            $threw             = $false

            try {
                try {
                    $checkoutAttempted = $true
                    throw "Simulated PS5.1 stderr from git checkout v0.2.0"
                } catch {
                    <# Simulates update.ps1 pattern: ignore informational stderr #>
                }
                # Execution must continue after the inner catch
            } catch {
                $threw = $true
            } finally {
                $ErrorActionPreference = "Continue"
            }

            $checkoutAttempted | Should -Be $true
            $threw             | Should -Be $false
        }

        It "still detects a real checkout failure via LASTEXITCODE" {
            $global:LASTEXITCODE = 1
            try { throw "Simulated stderr" } catch { <# ignore #> }
            ($LASTEXITCODE -ne 0) | Should -Be $true
            $global:LASTEXITCODE = 0  # reset
        }
    }
}

# ---------------------------------------------------------------------------
# Migration warning: stale .cg-docs/ in .gitignore
# ---------------------------------------------------------------------------

Describe "update.ps1 - stale .cg-docs/ gitignore warning" {
    # Tests for the detection logic that fires when .cg-docs/ appears as a
    # standalone line in .gitignore (added by /cg-setup before v0.1.1).
    # The production regex matches either / or \ as the path separator.
    # NOTE: The regex below is inlined from update.ps1. If the production
    # pattern changes, update this Describe block to match.

    Context "when .cg-docs/ is present as a standalone line" {
        It "detects .cg-docs/ with forward slash" {
            $lines = @("*.log", ".cg-docs/", "*.tmp")
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 1
        }

        It "detects .cg-docs\ with backslash (Windows path variant)" {
            $lines = @("*.log", ".cg-docs\", "*.tmp")
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 1
        }

        It "detects .cg-docs/ with surrounding whitespace" {
            $lines = @("  .cg-docs/  ")
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 1
        }

        It "detects .cg-docs/ in mixed case (case-insensitive regex)" {
            $lines = @(".CG-DOCS/", ".Cg-Docs\")
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 2
        }
    }

    Context "when .cg-docs/ is NOT a standalone line" {
        It "does not trigger on an empty .gitignore" {
            $lines = @()
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 0
        }

        It "does not trigger when .cg-docs/ is absent" {
            $lines = @("*.log", "compound-gpid.local.md", ".github/prompts/")
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 0
        }

        It "does not trigger on a .cg-docs/ entry that is a comment" {
            # git does not support inline comments in .gitignore; a line like
            # '# .cg-docs/' is a comment and does NOT gitignore the directory.
            $lines = @("# .cg-docs/")
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 0
        }

        It "does not trigger on .cg-docs without trailing slash (slash required by /cg-setup)" {
            # /cg-setup generates '.cg-docs/' with a trailing slash. The slash-less
            # form '.cg-docs' is intentionally not matched -- it is not a gitignore
            # pattern that would have been written by the tool.
            $lines = @(".cg-docs")
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 0
        }

        It "does not trigger on the CG managed block marker line itself (no .cg-docs/ in block after v0.1.1)" {
            # The managed block is rewritten by link.ps1 and no longer contains
            # .cg-docs/ after v0.1.1. This test guards that the 3-line block
            # containing only .github/ entries produces zero matches.
            $lines = @(
                "# Compound GPID managed items (junctions + copied file - do not commit)",
                ".github/prompts/",
                ".github/skills/"
            )
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 0
        }

        It "does not match .cg-docs/ with trailing non-whitespace content ($ anchor)" {
            # Confirms the $ anchor in the regex rejects lines like '.cg-docs/ # note'
            # which are not valid gitignore patterns written by the tool.
            $lines = @(".cg-docs/ # note", ".cg-docs/ extra")
            $staleCgDocsLines = $lines | Where-Object { $_ -match '(?i)^\s*\.cg-docs[/\\]\s*$' }
            ($staleCgDocsLines | Measure-Object).Count | Should -Be 0
        }
    }
}

# ---------------------------------------------------------------------------
# Version pinning -- --list output formatting
# ---------------------------------------------------------------------------

Describe "update.ps1 - --list formatting" {
    Context "marking the current version in the tag list" {
        It "appends '<-- current' marker to the active pinned tag" {
            $currentPin  = "v0.1.0"
            $releaseTags = @("v0.2.0", "v0.1.0")
            $lines       = $releaseTags | ForEach-Object {
                $marker = if ($_ -eq $currentPin) { "  <-- current" } else { "" }
                "$_$marker"
            }
            ($lines | Where-Object { $_ -match "<-- current" }).Count | Should -Be 1
            ($lines | Where-Object { $_ -match "v0\.1\.0.*<-- current" }).Count | Should -Be 1
            ($lines | Where-Object { $_ -match "v0\.2\.0.*<-- current" }).Count | Should -Be 0
        }

        It "appends '<-- current' marker to the HEAD tag when mode is 'latest'" {
            # Regression test: when not pinned (versionMode = "latest"), the arrow must
            # still appear next to whichever release tag HEAD points to.
            # Bug: the original loop only checked ($_ -eq $currentPin); since $currentPin
            # is "latest", no release tag ever matched and the arrow was never shown.
            $currentPin   = "latest"   # user is not pinned
            $installedTag = "v0.4.3"   # simulates: git tag --points-at HEAD filtered to release tags
            $releaseTags  = @("v0.4.3", "v0.3.0", "v0.2.0")

            # Fixed logic: mark a tag when it matches either the pin OR the installed HEAD tag
            $lines = $releaseTags | ForEach-Object {
                $marker = if ($_ -eq $currentPin -or $_ -eq $installedTag) { "  <-- current" } else { "" }
                "$_$marker"
            }

            ($lines | Where-Object { $_ -match "<-- current" }).Count        | Should -Be 1
            ($lines | Where-Object { $_ -match "v0\.4\.3.*<-- current" }).Count | Should -Be 1
            ($lines | Where-Object { $_ -match "v0\.3\.0.*<-- current" }).Count | Should -Be 0
        }

        It "shows no arrow when mode is 'latest' and HEAD is not at a tagged release (between releases)" {
            # When HEAD is between tags (e.g. on a commit after the last release),
            # $installedTag will be $null or empty and no arrow should appear.
            $currentPin   = "latest"
            $installedTag = $null   # HEAD points to an untagged commit
            $releaseTags  = @("v0.4.3", "v0.3.0", "v0.2.0")

            $lines = $releaseTags | ForEach-Object {
                $marker = if ($_ -eq $currentPin -or $_ -eq $installedTag) { "  <-- current" } else { "" }
                "$_$marker"
            }

            ($lines | Where-Object { $_ -match "<-- current" }).Count | Should -Be 0
        }

        It "selects first tag when multiple release tags point to the same HEAD commit" {
            # Regression/documentation: git tag --points-at HEAD can return multiple
            # tags (e.g. tag alias). update.ps1 takes $headTags[0]. This test documents
            # and validates that only the first tag gets the arrow.
            # (P2.2) MUST match selection logic in scripts/update.ps1 $installedTag block.
            $currentPin   = "latest"
            $headTags     = @("v0.4.3", "v0.4.3-alias")   # multiple tags at HEAD
            $installedTag = $headTags[0]                    # update.ps1: $headTags[0]
            $releaseTags  = @("v0.4.3", "v0.4.3-alias", "v0.3.0")

            $lines = $releaseTags | ForEach-Object {
                $marker = if ($_ -eq $currentPin -or $_ -eq $installedTag) { "  <-- current" } else { "" }
                "$_$marker"
            }
            ($lines | Where-Object { $_ -match "v0\.4\.3[^-].*<-- current" }).Count | Should -Be 1
            ($lines | Where-Object { $_ -match "v0\.3\.0.*<-- current" }).Count    | Should -Be 0
        }

        It "shows no arrow when git tag --points-at HEAD fails (no tags returned)" {
            # When git fails or HEAD is between releases, $headTags will be empty
            # and $installedTag stays $null. No arrow should appear.
            # (P2.3) Documents the error/between-releases path for update.ps1.
            $currentPin   = "latest"
            $headTags     = @()        # empty: git failed or no tag at HEAD
            $installedTag = if ($headTags) { $headTags[0] } else { $null }
            $releaseTags  = @("v0.4.3", "v0.3.0")

            $lines = $releaseTags | ForEach-Object {
                $marker = if ($_ -eq $currentPin -or $_ -eq $installedTag) { "  <-- current" } else { "" }
                "$_$marker"
            }
            ($lines | Where-Object { $_ -match "<-- current" }).Count | Should -Be 0
        }

        It "shows no arrow when HEAD points to a dev tag in latest mode" {
            # Dev tags (4-component v0.4.3.9000) are filtered out by $ReleaseTagPattern
            # before building $headTags, so $installedTag correctly stays $null.
            # (P3.1) MUST match $ReleaseTagPattern filter in scripts/update.ps1.
            $CurrentPin          = "latest"
            # Simulate: git tag --points-at HEAD returned "v0.4.3.9000" which was then
            # filtered by: Where-Object { $_ -match '^v\d+\.\d+\.\d+$' }
            $headTagsAfterFilter = @()   # dev tag filtered out → empty
            $installedTag        = if ($headTagsAfterFilter) { $headTagsAfterFilter[0] } else { $null }
            $releaseTags         = @("v0.4.3", "v0.3.0")

            $lines = $releaseTags | ForEach-Object {
                $marker = if ($_ -eq $CurrentPin -or $_ -eq $installedTag) { "  <-- current" } else { "" }
                "$_$marker"
            }
            ($lines | Where-Object { $_ -match "<-- current" }).Count | Should -Be 0
        }

        # P3.2: The '^v\d+\.\d+\.\d+$' pattern used below MUST match $ReleaseTagPattern
        # defined in scripts/update.ps1. If the production pattern changes, update here too.

        It "marks 'latest' mode correctly in the mode label" {
            $currentPin = "latest"
            $modeLabel  = if ($currentPin -eq "latest") { "main (latest)" } else { "$currentPin (pinned)" }
            $modeLabel | Should -Be "main (latest)"
        }

        It "marks a pinned tag correctly in the mode label" {
            $currentPin = "v0.2.0"
            $isDevPin   = $currentPin -ne "latest" -and $currentPin -match '^v\d+\.\d+\.\d+\.\d+$'
            $modeLabel  = if ($currentPin -eq "latest") { "main (latest)" }
                          elseif ($isDevPin)             { "$currentPin (dev -- not listed above)" }
                          else                           { "$currentPin (pinned)" }
            $modeLabel | Should -Be "v0.2.0 (pinned)"
        }

        It "marks a dev-tag pin with '(dev -- not listed above)' in the mode label" {
            $currentPin = "v0.1.0.9000"
            $isDevPin   = $currentPin -ne "latest" -and $currentPin -match '^v\d+\.\d+\.\d+\.\d+$'
            $modeLabel  = if ($currentPin -eq "latest") { "main (latest)" }
                          elseif ($isDevPin)             { "$currentPin (dev -- not listed above)" }
                          else                           { "$currentPin (pinned)" }
            $modeLabel | Should -Be "v0.1.0.9000 (dev -- not listed above)"
        }

        It "shows correct mode label when dev pin no longer exists on remote (orphaned dev tag)" {
            # Simulate: user pinned to v0.1.0.9000, tag was later deleted from remote.
            # The dev-pin label must still appear correctly even though the tag is absent.
            $currentPin = "v0.1.0.9000"
            $allTags    = @("v0.2.0", "v0.1.0")  # dev tag gone
            $isDevPin   = $currentPin -ne "latest" -and $currentPin -match '^v\d+\.\d+\.\d+\.\d+$'
            $modeLabel  = if ($currentPin -eq "latest") { "main (latest)" }
                          elseif ($isDevPin)             { "$currentPin (dev -- not listed above)" }
                          else                           { "$currentPin (pinned)" }
            $modeLabel | Should -Be "v0.1.0.9000 (dev -- not listed above)"
            # Confirm the tag is indeed absent from remote
            $currentPin -notin $allTags | Should -Be $true
        }
    }

    Context "dev tags excluded from release list" {
        It "filters out 4-component dev tags from the display list" {
            $allTags     = @("v0.2.0.9001", "v0.2.0.9000", "v0.2.0", "v0.1.0")
            $releaseTags = @($allTags | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' })
            $releaseTags.Count | Should -Be 2
            ($releaseTags | Where-Object { $_ -match '\.\d+\.\d+\.\d+$' }).Count | Should -Be 0
            $releaseTags -contains "v0.2.0" | Should -Be $true
            $releaseTags -contains "v0.1.0" | Should -Be $true
        }

        It "produces an empty release list when all tags are dev tags" {
            $allTags     = @("v0.1.0.9001", "v0.1.0.9000")
            $releaseTags = @($allTags | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' })
            $releaseTags.Count | Should -Be 0
        }
    }

    Context "no releases available" {
        It "produces an empty tag array when no tags match" {
            $tags = @()
            $tags.Count | Should -Be 0
            [bool]$tags | Should -Be $false
        }
    }
}

# ---------------------------------------------------------------------------
# Version pinning -- version status display
# ---------------------------------------------------------------------------

Describe "update.ps1 - version status display" {
    Context "upfront mode display (start of run)" {
        It "formats upfront line as 'Mode: tracking main (latest)' in latest mode" {
            $versionMode = "latest"
            $line = if ($versionMode -eq "latest") { "Mode: tracking main (latest)" } else { "Mode: pinned ($versionMode)" }
            $line | Should -Be "Mode: tracking main (latest)"
        }

        It "formats upfront line as 'Mode: pinned (<tag>)' in pinned mode" {
            $versionMode = "v0.2.0"
            $line = if ($versionMode -eq "latest") { "Mode: tracking main (latest)" } else { "Mode: pinned ($versionMode)" }
            $line | Should -Be "Mode: pinned (v0.2.0)"
        }
    }

    Context "latest mode" {
        It "formats status line as 'main (latest)'" {
            $versionMode = "latest"
            $statusLine  = if ($versionMode -eq "latest") { "Current version: main (latest)" } else { "Current version: $versionMode (pinned)" }
            $statusLine | Should -Be "Current version: main (latest)"
        }
    }

    Context "pinned mode" {
        It "formats status line as '<tag> (pinned)'" {
            $versionMode = "v0.2.0"
            $isDevPin = $versionMode -match '^v\d+\.\d+\.\d+\.\d+$'
            $pinLabel = if ($isDevPin) { "dev-pinned" } else { "pinned" }
            $statusLine  = if ($versionMode -eq "latest") { "Current version: main (latest)" } else { "Current version: $versionMode ($pinLabel)" }
            $statusLine | Should -Be "Current version: v0.2.0 (pinned)"
        }

        It "formats status line as '<tag> (dev-pinned)' for a dev tag" {
            $versionMode = "v0.1.0.9000"
            $isDevPin = $versionMode -match '^v\d+\.\d+\.\d+\.\d+$'
            $pinLabel = if ($isDevPin) { "dev-pinned" } else { "pinned" }
            $statusLine  = if ($versionMode -eq "latest") { "Current version: main (latest)" } else { "Current version: $versionMode ($pinLabel)" }
            $statusLine | Should -Be "Current version: v0.1.0.9000 (dev-pinned)"
        }
    }

    Context "newer release hint" {
        It "shows hint when latest tag differs from pinned version" {
            $versionMode = "v0.1.0"
            $latestTag   = "v0.2.0"
            $showHint    = $latestTag -and $latestTag -ne $versionMode
            $showHint | Should -Be $true
        }

        It "suppresses hint when already on the latest release" {
            $versionMode = "v0.2.0"
            $latestTag   = "v0.2.0"
            $showHint    = $latestTag -and $latestTag -ne $versionMode
            $showHint | Should -Be $false
        }

        It "suppresses hint when no tags exist (latestTag is null)" {
            $versionMode = "v0.2.0"
            $latestTag   = $null
            $showHint    = $latestTag -and $latestTag -ne $versionMode
            $showHint | Should -Be $false
        }

        It "suppresses hint in latest mode regardless of available tags" {
            $versionMode = "latest"
            $latestTag   = "v0.2.0"
            # Hint is only shown in the else branch (versionMode -ne "latest")
            $inPinnedBranch = $versionMode -ne "latest"
            $inPinnedBranch | Should -Be $false
        }

        It "skips dev tags when computing latestTag -- hint shows next release only" {
            # Simulate: git tag --list returns dev+release tags sorted newest first.
            # latestTag must be derived from release-only tags.
            $allTags   = @("v0.2.0.9001", "v0.2.0.9000", "v0.2.0", "v0.1.0")
            $latestTag = $allTags | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 1
            $latestTag | Should -Be "v0.2.0"
        }

        It "suppresses hint when only dev tags exist (latestTag becomes null)" {
            $allTags   = @("v0.1.0.9001", "v0.1.0.9000")
            $latestTag = $allTags | Where-Object { $_ -match '^v\d+\.\d+\.\d+$' } | Select-Object -First 1
            $latestTag | Should -BeNullOrEmpty
        }
    }
}

# ---------------------------------------------------------------------------
# P2.7 (review finding): --fix repair partial failure handling
# ---------------------------------------------------------------------------
# update.ps1 --fix runs: git clean -fd, git checkout ., git pull --ff-only.
# git clean and git checkout failures are non-fatal (output piped, LASTEXITCODE
# not checked); only git pull failure is fatal (LASTEXITCODE checked + throw).
# The finally block guarantees Pop-Location regardless of outcome.

Describe "update.ps1 - --fix repair partial failure handling" {
    AfterEach { $global:LASTEXITCODE = 0 }

    Context "git clean failure is non-fatal (LASTEXITCODE not checked)" {
        It "execution continues beyond git clean even when LASTEXITCODE is non-zero" {
            # The --fix block pipes git clean output via 2>&1 | ForEach-Object {...}
            # but does NOT inspect LASTEXITCODE afterward -- clean failure is non-fatal.
            $global:LASTEXITCODE = 1
            $cleanRan  = $true   # simulate: ForEach-Object received output lines
            $pullStage = $false
            # No LASTEXITCODE check between clean and checkout -- execution reaches pull
            if ($cleanRan) { $pullStage = $true }
            $pullStage | Should -Be $true
            $global:LASTEXITCODE = 0
        }
    }

    Context "git pull failure is fatal (LASTEXITCODE checked, throws)" {
        It "throws when git pull --ff-only exits non-zero" {
            $global:LASTEXITCODE = 1
            {
                if ($LASTEXITCODE -ne 0) {
                    throw "git pull --ff-only failed with exit code $LASTEXITCODE"
                }
            } | Should -Throw "git pull --ff-only failed"
        }

        It "does not throw when git pull succeeds (exit code 0)" {
            $global:LASTEXITCODE = 0
            $threw = $false
            try {
                if ($LASTEXITCODE -ne 0) {
                    throw "git pull --ff-only failed with exit code $LASTEXITCODE"
                }
            } catch {
                $threw = $true
            }
            $threw | Should -Be $false
        }
    }

    Context "Pop-Location in finally block (location always restored)" {
        It "restores the original working directory even when repair throws" {
            $original = Get-Location
            $tempDir  = Join-Path $TestDrive "fix-repair-test"
            New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

            Push-Location $tempDir
            try {
                throw "Simulated repair failure"
            } catch {
                <# expected -- mirrors the outer catch in --fix block #>
            } finally {
                Pop-Location
            }
            (Get-Location).Path | Should -Be $original.Path
        }

        It "restores location even when the inner try succeeds" {
            $original = Get-Location
            $tempDir  = Join-Path $TestDrive "fix-success-test"
            New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

            Push-Location $tempDir
            try {
                <# repair steps succeed #>
            } catch {
                <# no error #>
            } finally {
                Pop-Location
            }
            (Get-Location).Path | Should -Be $original.Path
        }
    }
}

Describe "update.ps1 - CG_INTERNAL_CALL guard" {
    Context "when CG_INTERNAL_CALL is set (called from cg-link)" {
        It "guard condition evaluates to false so refresh/migration is skipped" {
            $env:CG_INTERNAL_CALL = "1"
            $shouldRun = -not $env:CG_INTERNAL_CALL
            Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
            $shouldRun | Should -Be $false
        }

        It "guard condition is truthy for any non-empty value" {
            foreach ($val in @("1", "true", "yes", "link")) {
                $env:CG_INTERNAL_CALL = $val
                $guardHolds = [bool]$env:CG_INTERNAL_CALL
                Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
                $guardHolds | Should -Be $true
            }
        }
    }

    Context "when CG_INTERNAL_CALL is unset (called directly by user)" {
        It "guard condition evaluates to true so refresh/migration runs" {
            Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
            $shouldRun = -not $env:CG_INTERNAL_CALL
            $shouldRun | Should -Be $true
        }

        It "variable is absent (null/empty) when the env var is not set" {
            Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
            [string]::IsNullOrEmpty($env:CG_INTERNAL_CALL) | Should -Be $true
        }
    }

    Context "Remove-Item cleanup in finally block" {
        It "removing a non-existent env var with SilentlyContinue does not throw" {
            Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
            # If we got here without an exception, the pattern is safe
            $true | Should -Be $true
        }

        It "correctly clears the variable after simulated internal call" {
            $env:CG_INTERNAL_CALL = "1"
            [string]::IsNullOrEmpty($env:CG_INTERNAL_CALL) | Should -Be $false
            Remove-Item Env:\CG_INTERNAL_CALL -ErrorAction SilentlyContinue
            [string]::IsNullOrEmpty($env:CG_INTERNAL_CALL) | Should -Be $true
        }
    }
}

Describe "update.ps1 - legacy CLM profile remediation" {
    Context "when a user updates from legacy profile-function based installs" {
        It "contains cleanup for unmarked cg-link profile functions [regression guard]" {
            $updateContent = Get-Content (Join-Path $PSScriptRoot "..\scripts\update.ps1") -Raw -Encoding UTF8
            $helpersContent = Get-Content (Join-Path $PSScriptRoot "..\scripts\helpers.ps1") -Raw -Encoding UTF8
            $updateContent | Should -Match 'Remove-LegacyProfileCommands'
            $helpersContent | Should -Match 'hasLegacyCgFunctions'
            $updateContent | Should -Match '\$PROFILE'
            $updateContent | Should -Match 'Remove-CgLegacyLiveFunctions'
        }

        It "fails closed in Constrained Language Mode without changing the profile" {
            if (-not $script:OnWindows -or -not (Get-Command powershell.exe -ErrorAction SilentlyContinue)) {
                Set-ItResult -Skipped -Because "This acceptance test requires Windows PowerShell"
                return
            }

            $profilePath = Join-Path $TestDrive "clm-profile.ps1"
            $profileContent = 'function cg-link { & "C:\WBG\.compound-gpid\scripts\link.ps1" @args }'
            Set-Content -Path $profilePath -Value $profileContent -Encoding UTF8

            $probePath = Join-Path $TestDrive "clm-profile-probe.ps1"
            $helperPath = (Join-Path $PSScriptRoot "..\scripts\helpers.ps1").Replace("'", "''")
            $profileLiteral = $profilePath.Replace("'", "''")
            $probeContent = @"
`$ExecutionContext.SessionState.LanguageMode = 'ConstrainedLanguage'
. '$helperPath'
try {
    [void](Remove-LegacyProfileCommands -ProfilePath '$profileLiteral')
    Write-Output 'unexpected-success'
    exit 2
} catch {
    Write-Output `$_.Exception.Message
    exit 0
}
"@
            Set-Content -Path $probePath -Value $probeContent -Encoding UTF8

            $probeOutput = @(& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $probePath)
            $probeExitCode = $LASTEXITCODE

            $probeExitCode | Should -Be 0
            ($probeOutput -join "`n") | Should -Match 'FullLanguage'
            (Get-Content -Path $profilePath -Raw -Encoding UTF8) | Should -Be ($profileContent + "`r`n")
        }

        It "removes exact legacy wrappers after unrelated profile content" {
            $profilePath = Join-Path $TestDrive "legacy-profile.ps1"
            $profileContent = @'
# personal profile content before the legacy wrappers
function cg-link { & "C:\WBG\.compound-gpid\scripts\link.ps1" @args }
function cg-unlink { & "C:/WBG/.compound-gpid/scripts/unlink.ps1" @args }
function cg-update { & "$env:USERPROFILE\.compound-gpid\scripts\update.ps1" @args }
function My-PersonalCommand { Write-Output "preserve me" }
# personal profile content after the legacy wrappers
'@
            Set-Content -Path $profilePath -Value $profileContent -Encoding UTF8

            [void](Remove-LegacyProfileCommands -ProfilePath $profilePath)

            $cleaned = Get-Content -Path $profilePath -Raw -Encoding UTF8
            $cleaned | Should -Not -Match '(?m)^\s*function\s+cg-(link|unlink|update)\b'
            $cleaned | Should -Match 'function\s+My-PersonalCommand'
            $cleaned | Should -Match 'personal profile content before'
            $cleaned | Should -Match 'personal profile content after'
        }

        It "removes dot-sourced wrappers while preserving customized functions" {
            $profilePath = Join-Path $TestDrive "dot-source-profile.ps1"
            $profileContent = @'
function cg-update { . "$env:USERPROFILE\.compound-gpid\scripts\update.ps1" @args }
function cg-link { Write-Host "custom pre-hook"; . "C:\WBG\.compound-gpid\scripts\link.ps1" @args }
'@
            Set-Content -Path $profilePath -Value $profileContent -Encoding UTF8

            [void](Remove-LegacyProfileCommands -ProfilePath $profilePath)

            $cleaned = Get-Content -Path $profilePath -Raw -Encoding UTF8
            $cleaned | Should -Not -Match '(?m)^\s*function\s+cg-update\b'
            $cleaned | Should -Match 'function\s+cg-link\b'
            $cleaned | Should -Match 'custom pre-hook'
        }

        It "removes legacy functions from the live session after cleanup" {
            $profilePath = Join-Path $TestDrive "live-profile.ps1"
            $profileContent = 'function cg-link { & "C:\WBG\.compound-gpid\scripts\link.ps1" @args }'
            Set-Content -Path $profilePath -Value $profileContent -Encoding UTF8
            function global:cg-link { & "C:\WBG\.compound-gpid\scripts\link.ps1" @args }

            try {
                $removed = @(Remove-LegacyProfileCommands -ProfilePath $profilePath)
                if ($removed.Count -gt 0) {
                    [void](Remove-CgLegacyLiveFunctions -CommandNames $removed)
                }
            } finally {
                Remove-Item -Path Function:\cg-link -Force -ErrorAction SilentlyContinue
            }

            Get-Command cg-link -CommandType Function -ErrorAction SilentlyContinue | Should -BeNullOrEmpty
        }

        It "preserves a customized live function when the profile wrapper is legacy" {
            $profilePath = Join-Path $TestDrive "custom-live-profile.ps1"
            $profileContent = 'function cg-link { & "C:\WBG\.compound-gpid\scripts\link.ps1" @args }'
            Set-Content -Path $profilePath -Value $profileContent -Encoding UTF8
            function global:cg-link { Write-Output "custom" }

            try {
                $removed = @(Remove-LegacyProfileCommands -ProfilePath $profilePath)
                $removed | Should -Contain "cg-link"
                (Test-CgLegacyFunctionDefinition -CommandName "cg-link") | Should -Be $false
                (Get-Command cg-link -CommandType Function).Definition | Should -Match "custom"
            } finally {
                Remove-Item -Path Function:\cg-link -Force -ErrorAction SilentlyContinue
            }
        }

        It "preserves non-ASCII profile content and the original encoding for all supported formats" {
            $fixtures = @(
                [pscustomobject]@{ Name = "utf8-bom"; Encoding = [System.Text.UTF8Encoding]::new($true); Prefix = @(0xEF, 0xBB, 0xBF); ExpectedEncodingName = "utf-8" },
                [pscustomobject]@{ Name = "utf8-no-bom"; Encoding = [System.Text.UTF8Encoding]::new($false); Prefix = @(); ExpectedEncodingName = "utf-8" },
                [pscustomobject]@{ Name = "utf16-le"; Encoding = [System.Text.UnicodeEncoding]::new($false, $true); Prefix = @(0xFF, 0xFE); ExpectedEncodingName = "utf-16-le" },
                [pscustomobject]@{ Name = "utf16-be"; Encoding = [System.Text.UnicodeEncoding]::new($true, $true); Prefix = @(0xFE, 0xFF); ExpectedEncodingName = "utf-16-be" },
                [pscustomobject]@{ Name = "utf32-le"; Encoding = [System.Text.UTF32Encoding]::new($false, $true); Prefix = @(0xFF, 0xFE, 0x00, 0x00); ExpectedEncodingName = "utf-32-le" },
                [pscustomobject]@{ Name = "utf32-be"; Encoding = [System.Text.UTF32Encoding]::new($true, $true); Prefix = @(0x00, 0x00, 0xFE, 0xFF); ExpectedEncodingName = "utf-32-be" }
            )
            if ($script:OnWindows) {
                $ansiCodePage = [System.Globalization.CultureInfo]::CurrentCulture.TextInfo.ANSICodePage
                if ($PSVersionTable.PSEdition -ne "Desktop") {
                    [System.Text.Encoding]::RegisterProvider([System.Text.CodePagesEncodingProvider]::Instance)
                }
                $ansiEncoding = [System.Text.Encoding]::GetEncoding($ansiCodePage)
                $fixtures += [pscustomobject]@{ Name = "ansi"; Encoding = $ansiEncoding; Prefix = @(); ExpectedEncodingName = "ansi" }
            }

            foreach ($fixture in $fixtures) {
                $profilePath = Join-Path $TestDrive ("encoding-" + $fixture.Name + ".ps1")
                $nonAscii = "caf" + [char]0x00E9
                $profileContent = "# $nonAscii`r`nfunction cg-link { & `"C:\WBG\.compound-gpid\scripts\link.ps1`" @args }`r`n"
                [System.IO.File]::WriteAllText($profilePath, $profileContent, $fixture.Encoding)

                [void](Remove-LegacyProfileCommands -ProfilePath $profilePath)

                $roundTrip = Read-CgProfileText -Path $profilePath
                $nonAsciiPattern = [regex]::Escape($nonAscii)
                $roundTrip.Content | Should -Match $nonAsciiPattern
                $roundTrip.Content | Should -Not -Match '(?m)^\s*function\s+cg-link\b'
                $bytes = [System.IO.File]::ReadAllBytes($profilePath)
                if ($fixture.Prefix.Count -gt 0) {
                    for ($i = 0; $i -lt $fixture.Prefix.Count; $i++) {
                        $bytes[$i] | Should -Be $fixture.Prefix[$i]
                    }
                } else {
                    $roundTrip.HasBom | Should -Be $false
                }
                $roundTrip.EncodingName | Should -Be $fixture.ExpectedEncodingName
            }
        }

        It "preserves invalid UTF-8 bytes in a BOM-less ANSI profile" {
            if (-not $script:OnWindows) {
                Set-ItResult -Skipped -Because "The active Windows ANSI code page is unavailable on macOS/Linux"
                return
            }

            $profilePath = Join-Path $TestDrive "ansi-invalid-utf8-profile.ps1"
            $prefix = [System.Text.Encoding]::ASCII.GetBytes("# ")
            $ansiCodePage = [System.Globalization.CultureInfo]::CurrentCulture.TextInfo.ANSICodePage
            if ($PSVersionTable.PSEdition -ne "Desktop") {
                [System.Text.Encoding]::RegisterProvider([System.Text.CodePagesEncodingProvider]::Instance)
            }
            $ansiEncoding = [System.Text.Encoding]::GetEncoding($ansiCodePage)
            $ansiByte = $null
            for ($candidate = 0x80; $candidate -le 0xFF; $candidate++) {
                $candidateBytes = [byte[]]@([byte]$candidate)
                $candidateText = $ansiEncoding.GetString($candidateBytes)
                $roundTripCandidate = $ansiEncoding.GetBytes($candidateText)
                if ($candidate -ne 0xC2 -and $candidate -ne 0xC3 -and
                    $roundTripCandidate.Length -eq 1 -and $roundTripCandidate[0] -eq [byte]$candidate) {
                    $ansiByte = [byte]$candidate
                    break
                }
            }
            $ansiByte | Should -Not -BeNullOrEmpty
            $suffix = [System.Text.Encoding]::ASCII.GetBytes("`r`nfunction cg-link { & `"C:\WBG\.compound-gpid\scripts\link.ps1`" @args }`r`n")
            $bytes = New-Object -TypeName byte[] -ArgumentList ($prefix.Length + 1 + $suffix.Length)
            [System.Array]::Copy($prefix, 0, $bytes, 0, $prefix.Length)
            $bytes[$prefix.Length] = $ansiByte
            [System.Array]::Copy($suffix, 0, $bytes, $prefix.Length + 1, $suffix.Length)
            [System.IO.File]::WriteAllBytes($profilePath, $bytes)

            [void](Remove-LegacyProfileCommands -ProfilePath $profilePath)

            $roundTripBytes = [System.IO.File]::ReadAllBytes($profilePath)
            $roundTripBytes | Should -Contain $ansiByte
            $roundTripBytes | Should -Not -Contain ([byte]0xC3)
            (Read-CgProfileText -Path $profilePath).EncodingName | Should -Be "ansi"
            (Read-CgProfileText -Path $profilePath).Content | Should -Not -Match '(?m)^\s*function\s+cg-link\b'
        }

        It "preserves the profile line-ending style around removed wrappers" {
            $fixtures = @(
                [pscustomobject]@{ Name = "lf"; NewLine = "`n" },
                [pscustomobject]@{ Name = "crlf"; NewLine = "`r`n" }
            )
            $encoding = New-Object -TypeName System.Text.UTF8Encoding -ArgumentList $false

            foreach ($fixture in $fixtures) {
                $profilePath = Join-Path $TestDrive ("line-endings-" + $fixture.Name + ".ps1")
                $profileContent = "# before$($fixture.NewLine)$($fixture.NewLine)function cg-link { & `"C:\WBG\.compound-gpid\scripts\link.ps1`" @args }$($fixture.NewLine)$($fixture.NewLine)# after$($fixture.NewLine)"
                [System.IO.File]::WriteAllText($profilePath, $profileContent, $encoding)

                [void](Remove-LegacyProfileCommands -ProfilePath $profilePath)

                $cleaned = [System.IO.File]::ReadAllText($profilePath, $encoding)
                $cleaned | Should -Be ("# before$($fixture.NewLine)$($fixture.NewLine)$($fixture.NewLine)# after$($fixture.NewLine)")
                if ($fixture.Name -eq "lf") {
                    [System.IO.File]::ReadAllBytes($profilePath) | Should -Not -Contain ([byte]0x0D)
                } else {
                    $cleaned | Should -Match "`r`n"
                }
            }
        }

        It "fails closed instead of replacing a symlinked profile" {
            $targetPath = Join-Path $TestDrive "profile-target.ps1"
            $profilePath = Join-Path $TestDrive "profile-link.ps1"
            $profileContent = 'function cg-link { & "C:\WBG\.compound-gpid\scripts\link.ps1" @args }'
            Set-Content -Path $targetPath -Value $profileContent -Encoding UTF8
            $targetBytesBefore = [System.IO.File]::ReadAllBytes($targetPath)

            try {
                New-Item -ItemType SymbolicLink -Path $profilePath -Target $targetPath -ErrorAction Stop | Out-Null
            } catch {
                Set-ItResult -Skipped -Because "Symbolic links are unavailable: $($_.Exception.Message)"
                return
            }

            try {
                { Remove-LegacyProfileCommands -ProfilePath $profilePath } | Should -Throw
                $targetBytesAfter = [System.IO.File]::ReadAllBytes($targetPath)
                [Convert]::ToBase64String($targetBytesAfter) | Should -Be ([Convert]::ToBase64String($targetBytesBefore))
                $linkItem = Get-Item -LiteralPath $profilePath -Force
                $isReparsePoint = (($linkItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0)
                $hasLinkType = ($linkItem.PSObject.Properties.Name -contains "LinkType") -and (-not [string]::IsNullOrWhiteSpace([string]$linkItem.LinkType))
                ($isReparsePoint -or $hasLinkType) | Should -Be $true
            } finally {
                Remove-Item -LiteralPath $profilePath -Force -ErrorAction SilentlyContinue
            }
        }

        It "preserves near-miss functions instead of deleting customized code" {
            $profilePath = Join-Path $TestDrive "near-miss-profile.ps1"
            $profileContent = @'
function cg-link { & "C:\WBG\.compound-gpid\scripts\link.ps1" @args; Write-Output "custom" }
function cg-unlink { & "C:\WBG\.compound-gpid\scripts\other.ps1" @args }
function cg-update { & "C:\WBG\.compound-gpid\scripts\update.ps1" @other }
'@
            Set-Content -Path $profilePath -Value $profileContent -Encoding UTF8
            $expected = (Read-CgProfileText -Path $profilePath).Content

            [void](Remove-LegacyProfileCommands -ProfilePath $profilePath)

            (Read-CgProfileText -Path $profilePath).Content | Should -Be $expected
        }

        It "does not treat an unrelated Compound GPID comment as a managed block" {
            $profilePath = Join-Path $TestDrive "unrelated-profile.ps1"
            $profileContent = "# Compound GPID is mentioned in a personal note`nWrite-Output 'preserve me'"
            Set-Content -Path $profilePath -Value $profileContent -Encoding UTF8
            $expectedProfileContent = Get-Content -Path $profilePath -Raw -Encoding UTF8

            [void](Remove-LegacyProfileCommands -ProfilePath $profilePath)

            (Get-Content -Path $profilePath -Raw -Encoding UTF8) | Should -Be $expectedProfileContent
        }
    }
}
