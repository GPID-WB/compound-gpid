# tests/ps51-compat.Tests.ps1
# Pester tests to prevent PS 5.1 compatibility regressions
#
# Run with: Invoke-Pester tests/ps51-compat.Tests.ps1
# Compatible with Pester 3.4+ (ships built-in on Windows)
#
# Background: PS 5.1 reads BOM-less UTF-8 files as Windows-1252 (ANSI).
# Multi-byte UTF-8 characters like em-dash (U+2014, bytes E2 80 94) are
# decoded as three ANSI characters -- byte 0x94 maps to RIGHT DOUBLE
# QUOTATION MARK, which PowerShell treats as a string delimiter. This
# silently corrupts the AST, mis-pairing if/else blocks.
#
# PS 5.1 also lacks $var = if() { } else { } (ternary-style assignment),
# which is a PS 7+ feature.

$repoRoot = if ($env:CG_TEST_ROOT) { $env:CG_TEST_ROOT } else { Split-Path $PSScriptRoot -Parent }
# Production scripts that must parse cleanly on PS 5.1
$productionScripts = @(
    "install.ps1",
    "create-release.ps1",
    "scripts\update.ps1",
    "scripts\link.ps1",
    "scripts\unlink.ps1",
    "scripts\helpers.ps1"
)

# ---------------------------------------------------------------------------
# Non-ASCII character detection
# ---------------------------------------------------------------------------

Describe "PS 5.1 compat - no non-ASCII characters in production scripts" {
    foreach ($rel in $productionScripts) {
        $filePath = Join-Path $repoRoot $rel
        Context $rel {
            It "contains only ASCII characters (0x00-0x7F)" {
                if (-not (Test-Path $filePath)) {
                    
                    return
                }
                $lines = Get-Content -Path $filePath
                $violations = @()
                for ($i = 0; $i -lt $lines.Count; $i++) {
                    if ($lines[$i] -match '[^\x00-\x7F]') {
                        $violations += "L$($i+1): $($lines[$i].Trim())"
                    }
                }
                $violations.Count | Should -Be 0
            }
        }
    }
}

# ---------------------------------------------------------------------------
# $var = if() pattern detection (PS 7+ only)
# ---------------------------------------------------------------------------

Describe 'PS 5.1 compat - no $var = if() patterns in production scripts' {
    foreach ($rel in $productionScripts) {
        $filePath = Join-Path $repoRoot $rel
        Context $rel {
            It 'does not use $var = if (...) { } else { } assignment' {
                if (-not (Test-Path $filePath)) {
                    
                    return
                }
                $lines = Get-Content -Path $filePath
                $violations = @()
                for ($i = 0; $i -lt $lines.Count; $i++) {
                    # Match lines like:  $foo = if (...) {
                    # Exclude comments
                    $line = $lines[$i]
                    if ($line -match '^\s*\$\w+\s*=\s*if\s*\(' -and $line -notmatch '^\s*#') {
                        $violations += "L$($i+1): $($line.Trim())"
                    }
                }
                $violations.Count | Should -Be 0
            }
        }
    }
}
