# tests/Run-Tests.ps1
# Canonical safe test runner for Compound GPID.
#
# This is the ONLY approved way to run the full test suite. It enforces all
# three Pester safety rules at the script level — no one needs to remember them:
#
#   Rule 1:  Never Invoke-Pester tests/ (directory form)
#             → This script calls each file individually.
#   Rule 2:  Never pipeline -PassThru through ExpandProperty TestResult
#             → This script assigns $r first, accesses only scalar properties.
#   Rule 3:  PassThru output must be assigned before use
#             → $r = Invoke-Pester ... is the only form used here.
#
# REGISTRATION REQUIREMENT: Every .Tests.ps1 file in tests/ MUST be listed in
# the $testNames array below. Files not listed will not run and produce only a
# non-fatal warning — a silent coverage gap. When adding a new test file,
# always add its name to $testNames.
#
# Usage:
#   . tests\Run-Tests.ps1                        Run all tests, quiet per-file output
#   . tests\Run-Tests.ps1 -FailFast              Stop after the first file with failures
#   . tests\Run-Tests.ps1 -File charter          Run only the charter test file
#   . tests\Run-Tests.ps1 -File charter,roadmap  Run charter and roadmap test files
#
# Output artifact: tests/last-run.json — bounded JSON with pass/fail counts,
# per-file breakdown, and failure details. Written atomically after every run.
# Agents should read this artifact via execution_subagent rather than composing
# Invoke-Pester commands directly.
#
# VS Code task: Ctrl+Shift+P → Tasks: Run Task → "Run all Pester tests (safe)"

param(
    [switch]$FailFast,
    [string[]]$File
)

$repoRoot = Split-Path $PSScriptRoot -Parent

# Artifact paths — written atomically after every run.
$artifactPath = Join-Path (Join-Path $repoRoot "tests") "last-run.json"
$artifactTmp  = Join-Path (Join-Path $repoRoot "tests") ".last-run.tmp"

# Capture git SHA for audit trail. Allows /cg-diagnose to verify which commit was tested.
$gitSha = (git -C $repoRoot rev-parse --short HEAD 2>$null)
if (-not $gitSha) { $gitSha = "unknown" }

# Ordered list — non-junction-creating tests first, junction-creating tests last.
# IMPORTANT: link and unlink create directory junctions with timing-sensitive
# cleanup. Running them last prevents cleanup races with other test files.
$testNames = @(
    'charter',
    'helpers',
    'roadmap',
    'prompt-tools',
    'model-assignments',
    'pester-safety',
    'ps51-compat',
    'create-release',
    'bash-scripts',   # macOS bash script tests (platform-guarded, safe on Windows)
    'install',
    'cg-index',       # Python indexer tests (Python-availability-guarded, safe on Windows)
    'run-tests-runner',
    'update',
    'link',     # creates junctions — must be last
    'unlink'    # creates junctions — must be last
)

# -File filtering: run only the specified subset of test files.
# Junction-ordering is preserved: link/unlink are always kept last.
if ($File -and $File.Count -gt 0) {
    $junctionLast = @('link', 'unlink')
    $requested    = $File | ForEach-Object { $_.Trim() }

    # Warn about names not registered in $testNames.
    foreach ($reqName in $requested) {
        if ($testNames -notcontains $reqName) {
            Write-Warning "WARNING: '$reqName' is not a registered test name. Skipping."
        }
    }

    # Build filtered list preserving original order, then push junction tests to end.
    $nonJunction = $testNames | Where-Object { $requested -contains $_ -and $junctionLast -notcontains $_ }
    $junction    = $testNames | Where-Object { $requested -contains $_ -and $junctionLast -contains $_ }
    $testNames   = @($nonJunction) + @($junction)
}

# Guard: if all -File names were unregistered, $testNames is now empty.
# Write an error artifact and fail rather than producing a misleading passed: true, totalCount: 0 result.
if ($File -and $File.Count -gt 0 -and $testNames.Count -eq 0) {
    Write-Host "  ERROR: No registered test names matched the -File filter." -ForegroundColor Red
    $errorArtifact = [pscustomobject]@{
        gitSha        = $gitSha
        ranAt         = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        passed        = $false
        totalCount    = 0
        passedCount   = 0
        failedCount   = 0
        failFast      = $false
        filteredFiles = @($File)
        files         = @()
        failures      = @()
        error         = "No registered test names matched the -File filter"
    }
    try {
        [System.IO.File]::WriteAllText($artifactTmp, ($errorArtifact | ConvertTo-Json -Depth 4))
        Move-Item $artifactTmp $artifactPath -Force
    } catch {
        Write-Warning "WARNING: Failed to write error artifact: $_"
    }
    exit 1
}

$totalPassed = 0
$totalFailed = 0
$failedNames = @()
$skippedNames = @()
$earlyExit   = $false  # set to $true only when -FailFast breaks the loop early

# Detect Pester major version once. Pester 5+ requires the PesterConfiguration
# API; the legacy positional-argument invocation (used for Pester 3/4) triggers
# a deprecated-parameter-set warning in Pester 5 and may misreport PassedCount.
$pesterMod   = Get-Module Pester -ErrorAction SilentlyContinue
if (-not $pesterMod) { Import-Module Pester -ErrorAction SilentlyContinue; $pesterMod = Get-Module Pester }
$pesterMajor = if ($pesterMod) { [int]$pesterMod.Version.Major } else { 3 }

# Artifact data — initialized before the loop.
# Use ArrayList instead of @() + += to prevent single-element array coercion in PS 5.1
# ConvertTo-Json (PS 5.1) serialises a single-element @() as an object, not an array.
$filesArray    = [System.Collections.ArrayList]::new()
$failuresArray = [System.Collections.ArrayList]::new()

Write-Host ""
Write-Host "Compound GPID - Pester test suite" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

foreach ($name in $testNames) {
    $filePath = Join-Path (Join-Path $repoRoot "tests") "$name.Tests.ps1"

    if (-not (Test-Path $filePath)) {
        Write-Host "  [SKIP] $name (file not found)" -ForegroundColor Yellow
        $skippedNames += $name
        continue
    }

    # SAFE PATTERN: assign to $r first — never pipeline Invoke-Pester output directly.
    # Pester 5+: use PesterConfiguration to avoid the deprecated legacy parameter set
    # that misreports PassedCount. Pester 3/4: use the classic positional invocation.
    if ($pesterMajor -ge 5) {
        $cfg = New-PesterConfiguration
        $cfg.Run.Path     = $filePath
        $cfg.Run.PassThru = $true
        $cfg.Output.Verbosity = 'None'
        $r = Invoke-Pester -Configuration $cfg
    } else {
        $r = Invoke-Pester $filePath -PassThru -Quiet
    }

    # Guard: Invoke-Pester can return $null on a fatal load error (missing module at
    # global scope). Without this check, $r.FailedCount throws and exits the loop,
    # leaving the artifact stale from a previous run.
    if ($null -eq $r) {
        Write-Host "  [ERROR] $name - Invoke-Pester returned null" -ForegroundColor Red
        $totalFailed += 1
        $failedNames += $name
        continue
    }

    $status = if ($r.FailedCount -eq 0) { "[PASS]" } else { "[FAIL]" }
    $color  = if ($r.FailedCount -eq 0) { "Green" } else { "Red" }
    Write-Host ("  {0} {1,-28} passed: {2,3}  failed: {3,3}" -f $status, $name, $r.PassedCount, $r.FailedCount) -ForegroundColor $color

    $totalPassed += $r.PassedCount
    $totalFailed += $r.FailedCount

    # Append per-file summary to artifact data.
    $filesArray.Add([pscustomobject]@{
        name   = $name
        total  = $r.TotalCount
        passed = $r.PassedCount
        failed = $r.FailedCount
    }) | Out-Null

    if ($r.FailedCount -gt 0) {
        # $r.TestResult pipeline is safe — this script runs in a terminal subprocess,
        # NOT in the VS Code extension host. Neither Pester 3/4 ($r.TestResult) nor
        # Pester 5 ($r.Tests) paths pipeline through ExpandProperty TestResult.
        if ($pesterMajor -ge 5) {
            # Pester 5: each item in $r.Tests has .Name, .Result, .Path[], .ErrorRecord
            $r.Tests | Where-Object { $_.Result -eq 'Failed' } | ForEach-Object {
                $t = $_
                $describe = if ($t.Path -and $t.Path.Count -gt 0) { $t.Path[0] } else { '' }
                $context  = if ($t.Path -and $t.Path.Count -gt 1) { $t.Path[1] } else { '' }
                $message  = if ($t.ErrorRecord) { $t.ErrorRecord.Exception.Message } else { '' }
                $failuresArray.Add([pscustomobject]@{
                    file     = $name
                    describe = $describe
                    context  = $context
                    name     = $t.Name
                    message  = $message
                }) | Out-Null
            }
        } else {
            # Pester 3/4: each item in $r.TestResult has .Describe, .Context, .Name, .FailureMessage
            $r.TestResult | Where-Object { -not $_.Passed } | ForEach-Object {
                $failuresArray.Add([pscustomobject]@{
                    file     = $name
                    describe = $_.Describe
                    context  = if ($_.Context) { $_.Context } else { '' }
                    name     = $_.Name
                    message  = $_.FailureMessage
                }) | Out-Null
            }
        }

        $failedNames += $name
        if ($FailFast) {
            Write-Host ""
            Write-Host "  FailFast: stopping after first failure." -ForegroundColor Red
            $earlyExit = $true
            break
        }
    }
}

Write-Host ""
$summaryColor = if ($totalFailed -eq 0) { "Green" } else { "Red" }
Write-Host "==================================" -ForegroundColor $summaryColor
Write-Host ("  Total  passed: {0}  failed: {1}" -f $totalPassed, $totalFailed) -ForegroundColor $summaryColor

if ($failedNames.Count -gt 0) {
    Write-Host ""
    Write-Host "  Failed files:" -ForegroundColor Red
    foreach ($name in $failedNames) {
        Write-Host "    Invoke-Pester tests\$name.Tests.ps1" -ForegroundColor Red
    }
    Write-Host "  Run the command above to see the full failure details." -ForegroundColor DarkGray

    # Inline failure summary — visible in CI logs without downloading the artifact.
    if ($failuresArray.Count -gt 0) {
        Write-Host ""
        Write-Host "  Failure details:" -ForegroundColor Red
        foreach ($f in $failuresArray) {
            $loc = "$($f.file) > $($f.describe)"
            if ($f.context) { $loc += " > $($f.context)" }
            $loc += " > $($f.name)"
            Write-Host "    FAIL: $loc" -ForegroundColor Red
            if ($f.message) {
                $msg = ($f.message -split '\r?\n')[0]   # first line only
                Write-Host "         $msg" -ForegroundColor DarkGray
            }
        }
    }
}

# Warn about test files not in $testNames -- prevents silent coverage gaps when
# a new .Tests.ps1 file is added without registering it.
$allTestFiles = Get-ChildItem -Path (Join-Path $repoRoot "tests") -Filter "*.Tests.ps1" -File
$undeclared = $allTestFiles | Where-Object { $testNames -notcontains ($_.BaseName -replace '\.Tests$', '') }
if ($undeclared.Count -gt 0) {
    Write-Host ""
    Write-Host "  WARNING: undeclared test files (not in `$testNames):" -ForegroundColor Yellow
    foreach ($f in $undeclared) {
        Write-Host "    $($f.Name) - add to `$testNames in Run-Tests.ps1 to include in suite" -ForegroundColor Yellow
    }
}

Write-Host "==================================" -ForegroundColor $summaryColor
Write-Host ""

# Build and atomically write the test result artifact.
# failFast is true only when -FailFast was set AND the loop exited early due to failures.
$artifact = [pscustomobject]@{
    gitSha        = $gitSha
    ranAt         = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
    passed        = ($totalFailed -eq 0)
    totalCount    = $totalPassed + $totalFailed
    passedCount   = $totalPassed
    failedCount   = $totalFailed
    failFast      = [bool]$earlyExit
    filteredFiles = if ($File) { @($File) } else { $null }
    skipped       = $skippedNames
    files         = $filesArray
    failures      = $failuresArray
}
# Write to tmp first, then rename -- prevents agents from reading a partial artifact mid-write.
try {
    [System.IO.File]::WriteAllText($artifactTmp, ($artifact | ConvertTo-Json -Depth 4))
    Move-Item $artifactTmp $artifactPath -Force
} catch {
    Write-Warning "WARNING: Failed to write test artifact: $_"
}

if ($totalFailed -gt 0) { $global:LASTEXITCODE = 1; return }
