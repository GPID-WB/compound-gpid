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
# Usage:
#   . tests\Run-Tests.ps1                Run all tests, quiet per-file output
#   . tests\Run-Tests.ps1 -FailFast      Stop after the first file with failures
#
# VS Code task: Ctrl+Shift+P → Tasks: Run Task → "Run all Pester tests (safe)"

param([switch]$FailFast)

$repoRoot = Split-Path $PSScriptRoot -Parent

# Ordered list — non-junction-creating tests first, junction-creating tests last.
# IMPORTANT: link and unlink create directory junctions with timing-sensitive
# cleanup. Running them last prevents cleanup races with other test files.
$testNames = @(
    'charter',
    'roadmap',
    'prompt-tools',
    'model-assignments',
    'pester-safety',
    'ps51-compat',
    'create-release',
    'install',
    'update',
    'link',     # creates junctions — must be last
    'unlink'    # creates junctions — must be last
)

$totalPassed = 0
$totalFailed = 0
$failedNames = @()
$skippedNames = @()

Write-Host ""
Write-Host "Compound GPID - Pester test suite" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

foreach ($name in $testNames) {
    $filePath = Join-Path $repoRoot "tests\$name.Tests.ps1"

    if (-not (Test-Path $filePath)) {
        Write-Host "  [SKIP] $name (file not found)" -ForegroundColor Yellow
        $skippedNames += $name
        continue
    }

    # SAFE PATTERN: assign to $r first — never pipeline Invoke-Pester output directly.
    $r = Invoke-Pester $filePath -PassThru -Quiet

    $status = if ($r.FailedCount -eq 0) { "[PASS]" } else { "[FAIL]" }
    $color  = if ($r.FailedCount -eq 0) { "Green" } else { "Red" }
    Write-Host ("  {0} {1,-28} passed: {2,3}  failed: {3,3}" -f $status, $name, $r.PassedCount, $r.FailedCount) -ForegroundColor $color

    $totalPassed += $r.PassedCount
    $totalFailed += $r.FailedCount

    if ($r.FailedCount -gt 0) {
        $failedNames += $name
        if ($FailFast) {
            Write-Host ""
            Write-Host "  FailFast: stopping after first failure." -ForegroundColor Red
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
}

# Warn about test files not in $testNames (P2.5: prevents silent omissions)
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

if ($totalFailed -gt 0) { exit 1 }
