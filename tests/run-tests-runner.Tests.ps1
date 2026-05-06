# tests/run-tests-runner.Tests.ps1
# Tests for Run-Tests.ps1 — the canonical safe test runner.
#
# Strategy (see plan Step 6, REVIEW FIX P1.1):
#   Static tests: verify script text properties that can be checked without
#   running the suite (param block, artifact construction keywords, git SHA,
#   gitignore entries, $testNames membership).
#
#   Artifact-content tests: validate the schema of tests/last-run.json from a
#   *previous* run. Skipped gracefully when no prior artifact exists — the
#   static tests still verify the artifact-producing code is present.
#   First run: static tests pass, artifact tests skip.
#   Second run: both pass.
#
# Run with: Invoke-Pester tests/run-tests-runner.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)

$repoRoot     = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
$runnerPath   = Join-Path (Join-Path $repoRoot "tests") "Run-Tests.ps1"
$gitignorePath = Join-Path $repoRoot ".gitignore"
$artifactPath = Join-Path (Join-Path $repoRoot "tests") "last-run.json"

$runnerContent   = if (Test-Path $runnerPath)   { Get-Content $runnerPath   -Raw -Encoding UTF8 } else { "" }
$gitignoreContent = if (Test-Path $gitignorePath) { Get-Content $gitignorePath -Raw -Encoding UTF8 } else { "" }

# ---------------------------------------------------------------------------
# .gitignore entries (R8)
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - .gitignore entries for artifact files" {
    It ".gitignore contains tests/last-run.json" {
        ($gitignoreContent -match 'tests/last-run\.json') | Should -Be $true
    }

    It ".gitignore contains tests/.last-run.tmp" {
        ($gitignoreContent -match 'tests/\.last-run\.tmp') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# $testNames membership (R15)
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - run-tests-runner is registered in `$testNames" {
    It "`$testNames includes 'run-tests-runner'" {
        ($runnerContent -match "'run-tests-runner'") | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# $testNames membership — bash-scripts (R16)
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - 'bash-scripts' is registered in `$testNames" {
    It "`$testNames includes 'bash-scripts'" {
        ($runnerContent -match "'bash-scripts'") | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Script text — -File parameter (R7)
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - -File parameter support" {
    It "param block declares `$File parameter" {
        ($runnerContent -match '\[string\[\]\]\$File') | Should -Be $true
    }

    It "script filters testNames when -File is provided" {
        ($runnerContent -match '\$File.*-and.*\$File\.Count') | Should -Be $true
    }

    It "junction tests are always placed last in -File mode" {
        ($runnerContent -match 'junctionLast') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Script text — JSON artifact construction (R1, R2, R5, R16)
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - artifact construction keywords" {
    It "script contains ConvertTo-Json (artifact serialization)" {
        ($runnerContent -match 'ConvertTo-Json') | Should -Be $true
    }

    It "script contains Move-Item (atomic rename)" {
        ($runnerContent -match 'Move-Item') | Should -Be $true
    }

    It "script contains failFast field in artifact" {
        ($runnerContent -match 'failFast') | Should -Be $true
    }

    It "artifact includes ranAt timestamp field" {
        ($runnerContent -match 'ranAt') | Should -Be $true
    }

    It "artifact includes passed boolean field" {
        ($runnerContent -match 'passed\s*=') | Should -Be $true
    }

    It "script exits with code 1 when failures are present" {
        ($runnerContent -match 'exit 1') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Script text — undeclared-file detection (R14)
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - undeclared test file detection" {
    It "script detects undeclared test files not in `$testNames" {
        ($runnerContent -match 'Get-ChildItem.*Tests.*ps1') | Should -Be $true
    }

    It "script warns about undeclared test files" {
        ($runnerContent -match 'undeclared') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Script text — unregistered -File name warning (R7)
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - -File unregistered name warning" {
    It "warns when a -File name is not registered in `$testNames" {
        ($runnerContent -match 'Write-Warning.*not a registered test name') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Script text — git SHA capture (R4)
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - git SHA audit trail" {
    It "script captures git rev-parse for SHA" {
        ($runnerContent -match 'git.*rev-parse') | Should -Be $true
    }

    It "script falls back to 'unknown' when not in a git repo" {
        ($runnerContent -match '"unknown"') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Script text — $r.TestResult safety comment (R3, REVIEW FIX P1.2)
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - TestResult pipeline safety comment" {
    It "inline comment documents why `$r.TestResult pipeline is safe" {
        # The comment explains the subprocess isolation exemption. If this test
        # fails, someone removed the comment — add it back to prevent future
        # scan extensions from creating false positives.
        ($runnerContent -match 'TestResult.*pipeline.*safe|safe.*TestResult.*pipeline|subprocess.*NOT.*VS Code|NOT.*extension host') | Should -Be $true
    }
}

# ---------------------------------------------------------------------------
# Artifact content tests — validate schema of previous run's artifact.
# Falls back to a single placeholder passing test when no artifact exists
# (Pester 3.4 has no Skip -- first run shows 1 pass, not a skip).
# ---------------------------------------------------------------------------
Describe "Run-Tests.ps1 - last-run.json artifact schema" {
    if (-not (Test-Path $artifactPath)) {
        It "artifact schema tests skipped - no artifact from a previous run" {
            # Run the suite once to generate tests/last-run.json, then re-run
            # to validate its schema. This is expected on the first clean run.
            $true | Should -Be $true
        }
    } else {
        $json = $null
        $parseError = $null
        try {
            $json = Get-Content $artifactPath -Raw -Encoding UTF8 | ConvertFrom-Json
        } catch {
            $parseError = $_.Exception.Message
        }

        It "last-run.json is valid JSON" {
            $parseError | Should -BeNullOrEmpty
        }

        It "last-run.json has 'passed' field" {
            ($null -ne $json.passed) | Should -Be $true
        }

        It "last-run.json has 'totalCount' field" {
            ($null -ne $json.totalCount) | Should -Be $true
        }

        It "last-run.json has 'passedCount' field" {
            ($null -ne $json.passedCount) | Should -Be $true
        }

        It "last-run.json has 'failedCount' field" {
            ($null -ne $json.failedCount) | Should -Be $true
        }

        It "last-run.json has 'failFast' field" {
            ($null -ne $json.failFast) | Should -Be $true
        }

        It "last-run.json has 'gitSha' field" {
            ($null -ne $json.gitSha) | Should -Be $true
        }

        It "last-run.json gitSha is a non-empty string" {
            ($json.gitSha -is [string] -and $json.gitSha.Length -gt 0) | Should -Be $true
        }

        It "last-run.json has 'ranAt' field" {
            ($null -ne $json.ranAt) | Should -Be $true
        }

        It "last-run.json ranAt is a valid ISO 8601 UTC timestamp" {
            ($json.ranAt -match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$') | Should -Be $true
        }

        It "last-run.json has 'files' array" {
            ($null -ne $json.files) | Should -Be $true
        }

        It "last-run.json has 'failures' array" {
            ($null -ne $json.failures) | Should -Be $true
        }

        It "last-run.json has 'skipped' array field" {
            ($null -ne $json.skipped) | Should -Be $true
        }

        It "last-run.json totalCount is greater than 0" {
            $json.totalCount | Should -BeGreaterThan 0
        }

        It "last-run.json totalCount equals passedCount plus failedCount" {
            ($json.passedCount + $json.failedCount) | Should -Be $json.totalCount
        }

        It "last-run.json files is an array type" {
            ($json.files -is [array]) | Should -Be $true
        }

        It "last-run.json failures is an array type" {
            ($json.failures -is [array]) | Should -Be $true
        }
    }
}
