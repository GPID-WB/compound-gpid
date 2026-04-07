# tests/pester-safety.Tests.ps1
# Meta-tests: scan every test file and the safe runner for forbidden Pester
# invocation patterns. These patterns have crashed VS Code 8+ confirmed times.
#
# Run with: Invoke-Pester tests/pester-safety.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)
#
# This file scans OTHER test files — it deliberately excludes itself to avoid
# self-referential false positives.
#
# Reference: .cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
. "$PSScriptRoot/helpers.ps1"

# Scan all *.Tests.ps1 files EXCEPT this one (self-exclusion avoids false positives
# from the regex patterns stored as strings inside this file).
$testFiles = @(Get-ChildItem (Join-Path $repoRoot "tests") -Filter "*.Tests.ps1" -File |
    Where-Object { $_.Name -ne "pester-safety.Tests.ps1" })

# Also scan the safe runner script itself.
$runnerFile = Get-Item (Join-Path $repoRoot "tests\Run-Tests.ps1") -ErrorAction SilentlyContinue
if ($runnerFile) { $testFiles += $runnerFile }

# ---------------------------------------------------------------------------
# Forbidden pattern 1: Invoke-Pester in directory form
#
# Dangerous:    Invoke-Pester tests/
# Safe:         Invoke-Pester tests/foo.Tests.ps1
#
# The directory form runs ALL test files simultaneously. When junction-creating
# tests (link, unlink) fire in parallel, VS Code's extension host exhausts
# memory and freezes — silently, requiring a force-quit.
# ---------------------------------------------------------------------------

Describe "Pester safety - no directory-form Invoke-Pester" {
    foreach ($file in $testFiles) {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        $relPath = $file.Name

        It "$relPath does not invoke Pester on the tests/ directory" {
            # Check non-comment lines only, so documentation comments are allowed.
            $violations = ($content -split '\r?\n') |
                Where-Object { $_ -notmatch '^\s*#' } |
                Where-Object { $_ -match 'Invoke-Pester\s+"?tests[/\\]"?\s*(?:#|$)' }
            $violations.Count | Should Be 0
        }
    }
}

# ---------------------------------------------------------------------------
# Forbidden pattern 2: -PassThru piped through ExpandProperty TestResult
#
# Dangerous:    Invoke-Pester ... -PassThru | Select-Object -ExpandProperty TestResult | ...
# Safe:         $r = Invoke-Pester ...; $r | Select-Object TotalCount, ...
#
# ExpandProperty TestResult materialises the full Pester result graph as .NET
# objects in the PowerShell extension host, exhausting its memory and freezing
# VS Code. Assigning to $r avoids the pipeline materialisation.
# ---------------------------------------------------------------------------

Describe "Pester safety - no ExpandProperty TestResult pipeline" {
    foreach ($file in $testFiles) {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        $relPath = $file.Name

        It "$relPath does not use the ExpandProperty TestResult crash pattern" {
            # Check non-comment lines only, so documentation comments are allowed.
            $violations = ($content -split '\r?\n') |
                Where-Object { $_ -notmatch '^\s*#' } |
                Where-Object { $_ -match 'ExpandProperty\s+TestResult' }
            $violations.Count | Should Be 0
        }
    }
}

# ---------------------------------------------------------------------------
# Forbidden pattern 3: unassigned -PassThru pipeline
#
# Dangerous:    Invoke-Pester ... -PassThru | Select-Object ...
# Safe:         $r = Invoke-Pester ...; $r | Select-Object ...
#
# Piping -PassThru output without first assigning to a variable is the root
# step that enables the ExpandProperty crash. Even without ExpandProperty,
# a large suite produces a heavy pipeline that can overwhelm the extension host.
# ---------------------------------------------------------------------------

Describe "Pester safety - PassThru output must be assigned before use" {
    foreach ($file in $testFiles) {
        $content = Get-Content $file.FullName -Raw -Encoding UTF8
        $relPath = $file.Name

        It "$relPath does not pipeline Invoke-Pester -PassThru output without assigning first" {
            # Check non-comment lines only.
            # Dangerous:  Invoke-Pester ... -PassThru ... |
            # Safe:       $r = Invoke-Pester ... -PassThru
            $violations = ($content -split '\r?\n') |
                Where-Object { $_ -notmatch '^\s*#' } |
                Where-Object { $_ -match 'Invoke-Pester\b[^\r\n]*-PassThru[^\r\n]*\|' } |
                Where-Object { $_ -notmatch '\$\w+\s*=\s*Invoke-Pester' }
            $violations.Count | Should Be 0
        }
    }
}
