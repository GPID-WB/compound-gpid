# tests/parity.Tests.ps1
# Cross-script parity checks: verifies that the PowerShell and bash
# equivalents of link/unlink stay in sync on critical configuration values.
#
# These tests catch the class of bug where a developer updates one script
# (e.g. adds a new managed directory to link.ps1) but forgets to update
# the other (link.sh). They run on both Windows and macOS CI because
# the test itself is pure text-matching with no platform-specific code.
#
# Run with: Invoke-Pester tests/parity.Tests.ps1

$repoRoot = Split-Path $PSScriptRoot -Parent

# ---------------------------------------------------------------------------
# Helper: extract the managed-dirs array from a script's source text.
# Works for both PowerShell and bash formats:
#   $ManagedDirs = @("prompts", "skills", ...)   # link.ps1 / unlink.ps1
#   MANAGED_DIRS=("prompts" "skills" ...)          # link.sh / unlink.sh
# Returns a sorted string[] for order-independent comparison.
# ---------------------------------------------------------------------------
function Get-ManagedDirsFromSource {
    param([string]$Content)
    # Match either PS or bash array declaration:
    #   $ManagedDirs = @("prompts", "skills", ...)   # PowerShell (note the @)
    #   MANAGED_DIRS=("prompts" "skills" ...)          # bash
    $m = [regex]::Match($Content, '(?:MANAGED_DIRS|\$ManagedDirs)\s*=\s*@?\(([^)]+)\)')
    if (-not $m.Success) { return @() }
    $inner = $m.Groups[1].Value
    # Extract each "quoted" token
    $items = [regex]::Matches($inner, '"([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
    return ($items | Sort-Object)
}

# ---------------------------------------------------------------------------
# link.ps1 <-> link.sh parity
# ---------------------------------------------------------------------------
Describe "link.ps1 <-> link.sh parity" {
    $linkPs1 = Get-Content (Join-Path $repoRoot "scripts/link.ps1") -Raw -Encoding UTF8
    $linkSh  = Get-Content (Join-Path $repoRoot "scripts/link.sh")  -Raw -Encoding UTF8

    It "both scripts define the same managed directories" {
        $ps1Dirs = Get-ManagedDirsFromSource $linkPs1
        $shDirs  = Get-ManagedDirsFromSource $linkSh

        # Parse guards: if either returns @() the comparison is vacuously true.
        $ps1Dirs.Count | Should -BeGreaterThan 0
        $shDirs.Count  | Should -BeGreaterThan 0
        $missing  = $ps1Dirs | Where-Object { $_ -notin $shDirs }
        $extra    = $shDirs  | Where-Object { $_ -notin $ps1Dirs }
        $missing  | Should -BeNullOrEmpty  # dirs in link.ps1 but not link.sh
        $extra    | Should -BeNullOrEmpty  # dirs in link.sh but not link.ps1
    }

    It "both scripts reference the same verification file (cg-setup.prompt.md)" {
        $linkPs1 | Should -Match 'cg-setup\.prompt\.md'
        $linkSh  | Should -Match 'cg-setup\.prompt\.md'
    }

    It "both scripts use the same .gitignore block marker" {
        $marker = 'Compound GPID managed items'
        $linkPs1 | Should -Match ([regex]::Escape($marker))
        $linkSh  | Should -Match ([regex]::Escape($marker))
    }

    It "link.ps1 ManagedDirs extraction regex finds the array [sanity check]" {
        $dirs = Get-ManagedDirsFromSource $linkPs1
        $dirs | Should -Not -BeNullOrEmpty
        $dirs | Should -Contain 'prompts'
    }

    It "link.sh MANAGED_DIRS extraction regex finds the array [sanity check]" {
        $dirs = Get-ManagedDirsFromSource $linkSh
        $dirs | Should -Not -BeNullOrEmpty
        $dirs | Should -Contain 'prompts'
    }

    It "both scripts support a non-interactive bypass flag [regression guard]" {
        # link.ps1 uses -Force, link.sh uses --yes / -y
        $linkPs1 | Should -Match '\[switch\]\$Force'
        $linkSh  | Should -Match '\-\-yes'
        $linkSh  | Should -Match '(?<![\w])-y[)\s]'
    }
}

# ---------------------------------------------------------------------------
# unlink.ps1 <-> unlink.sh parity
# ---------------------------------------------------------------------------
Describe "unlink.ps1 <-> unlink.sh parity" {
    $unlinkPs1 = Get-Content (Join-Path $repoRoot "scripts/unlink.ps1") -Raw -Encoding UTF8
    $unlinkSh  = Get-Content (Join-Path $repoRoot "scripts/unlink.sh")  -Raw -Encoding UTF8

    It "both scripts define the same managed directories" {
        $ps1Dirs = Get-ManagedDirsFromSource $unlinkPs1
        $shDirs  = Get-ManagedDirsFromSource $unlinkSh

        # Parse guards: if either returns @() the comparison is vacuously true.
        $ps1Dirs.Count | Should -BeGreaterThan 0
        $shDirs.Count  | Should -BeGreaterThan 0

        $missing = $ps1Dirs | Where-Object { $_ -notin $shDirs }
        $extra   = $shDirs  | Where-Object { $_ -notin $ps1Dirs }
        $missing | Should -BeNullOrEmpty
        $extra   | Should -BeNullOrEmpty
    }

    It "unlink.ps1 ManagedDirs extraction regex finds the array [sanity check]" {
        $dirs = Get-ManagedDirsFromSource $unlinkPs1
        $dirs | Should -Not -BeNullOrEmpty
        $dirs | Should -Contain 'prompts'
    }

    It "unlink.sh MANAGED_DIRS extraction regex finds the array [sanity check]" {
        $dirs = Get-ManagedDirsFromSource $unlinkSh
        $dirs | Should -Not -BeNullOrEmpty
        $dirs | Should -Contain 'prompts'
    }

    It "both scripts support a non-interactive bypass flag [regression guard]" {
        # unlink.ps1 uses -Force, unlink.sh uses --yes / -y
        $unlinkPs1 | Should -Match '\[switch\]\$Force'
        $unlinkSh  | Should -Match '\-\-yes'
        $unlinkSh  | Should -Match '(?<![\w])-y[)\s]'
    }

    It "both scripts check for the compound-gpid management marker before removing" {
        $marker = 'compound-gpid'
        $unlinkPs1 | Should -Match $marker
        $unlinkSh  | Should -Match $marker
    }
}

# ---------------------------------------------------------------------------
# link.ps1 <-> unlink.ps1 parity (PowerShell pair)
# ---------------------------------------------------------------------------
Describe "link.ps1 <-> unlink.ps1 parity (PowerShell pair)" {
    $linkPs1   = Get-Content (Join-Path $repoRoot "scripts/link.ps1")   -Raw -Encoding UTF8
    $unlinkPs1 = Get-Content (Join-Path $repoRoot "scripts/unlink.ps1") -Raw -Encoding UTF8

    It "both PowerShell scripts define the same managed directories" {
        $linkDirs   = Get-ManagedDirsFromSource $linkPs1
        $unlinkDirs = Get-ManagedDirsFromSource $unlinkPs1

        # Parse guards: if either returns @() the comparison is vacuously true.
        $linkDirs.Count   | Should -BeGreaterThan 0
        $unlinkDirs.Count | Should -BeGreaterThan 0

        $missing = $linkDirs   | Where-Object { $_ -notin $unlinkDirs }
        $extra   = $unlinkDirs | Where-Object { $_ -notin $linkDirs }
        $missing | Should -BeNullOrEmpty
        $extra   | Should -BeNullOrEmpty
    }
}

# ---------------------------------------------------------------------------
# link.sh <-> unlink.sh parity (bash pair)
# ---------------------------------------------------------------------------
Describe "link.sh <-> unlink.sh parity (bash pair)" {
    $linkSh   = Get-Content (Join-Path $repoRoot "scripts/link.sh")   -Raw -Encoding UTF8
    $unlinkSh = Get-Content (Join-Path $repoRoot "scripts/unlink.sh") -Raw -Encoding UTF8

    It "both bash scripts define the same managed directories" {
        $linkDirs   = Get-ManagedDirsFromSource $linkSh
        $unlinkDirs = Get-ManagedDirsFromSource $unlinkSh

        # Parse guards: if either returns @() the comparison is vacuously true.
        $linkDirs.Count   | Should -BeGreaterThan 0
        $unlinkDirs.Count | Should -BeGreaterThan 0

        $missing = $linkDirs   | Where-Object { $_ -notin $unlinkDirs }
        $extra   = $unlinkDirs | Where-Object { $_ -notin $linkDirs }
        $missing | Should -BeNullOrEmpty
        $extra   | Should -BeNullOrEmpty
    }
}
