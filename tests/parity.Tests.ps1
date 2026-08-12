# tests/parity.Tests.ps1
# Cross-script parity checks: verifies that the PowerShell and bash
# equivalents of link/unlink stay in sync on critical configuration values.
#
# These tests catch the class of bug where a developer updates one script
# (e.g. adds a new install unit to target-mapping.json) but forgets to update
# the bash fallback lists. They run on both Windows and macOS CI because
# the test itself is pure text-matching with no platform-specific code.
#
# Run with: Invoke-Pester tests/parity.Tests.ps1

$repoRoot = Split-Path $PSScriptRoot -Parent

# ---------------------------------------------------------------------------
# Helpers: extract install-unit keys from target-mapping.json and bash fallback
# lists. PowerShell scripts read target-mapping.json directly, while bash keeps
# literal fallback lists to avoid requiring jq.
# ---------------------------------------------------------------------------
function Get-InstallUnitKeysFromMapping {
    param([string]$MappingPath)

    $mapping = Get-Content $MappingPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $keys = @()
    foreach ($target in @($mapping.targets)) {
        foreach ($unit in @($target.installUnits)) {
            $keys += "$($target.id)|$($unit.type)|$($unit.source)|$($unit.target)|$($unit.strategy)"
        }
    }
    return ($keys | Sort-Object)
}

function Get-UnlinkUnitKeysFromMapping {
    param([string]$MappingPath)

    $mapping = Get-Content $MappingPath -Raw -Encoding UTF8 | ConvertFrom-Json
    $keys = @()
    foreach ($target in @($mapping.targets)) {
        foreach ($unit in @($target.installUnits)) {
            $keys += "$($unit.target)|$($unit.type)"
        }
    }
    return ($keys | Sort-Object -Unique)
}

function Get-LinkShInstallUnitKeysFromSource {
    param([string]$Content)

    $keys = @()
    $matches = [regex]::Matches($Content, "'([^|'`r`n]+)\|([^|'`r`n]+)\|([^|'`r`n]+)\|([^|'`r`n]+)\|([^|'`r`n]+)\|[^']*'")
    foreach ($match in $matches) {
        $keys += "$($match.Groups[1].Value)|$($match.Groups[2].Value)|$($match.Groups[3].Value)|$($match.Groups[4].Value)|$($match.Groups[5].Value)"
    }
    return ($keys | Sort-Object)
}

function Get-UnlinkShUnitKeysFromSource {
    param([string]$Content)

    $keys = @()
    $matches = [regex]::Matches($Content, "'([^|'`r`n]+)\|([^|'`r`n]+)'")
    foreach ($match in $matches) {
        $keys += "$($match.Groups[1].Value)|$($match.Groups[2].Value)"
    }
    return ($keys | Sort-Object -Unique)
}

# ---------------------------------------------------------------------------
# link.ps1 <-> link.sh parity
# ---------------------------------------------------------------------------
Describe "link.ps1 <-> link.sh parity" {
    $linkPs1 = Get-Content (Join-Path $repoRoot "scripts/link.ps1") -Raw -Encoding UTF8
    $linkSh  = Get-Content (Join-Path $repoRoot "scripts/link.sh")  -Raw -Encoding UTF8
    $mappingPath = Join-Path $repoRoot ".github/shared/target-mapping.json"

    It "link.ps1 reads install units from target-mapping.json" {
        $linkPs1 | Should -Match 'TargetMappingPath'
        $linkPs1 | Should -Match 'ConvertFrom-Json'
        $linkPs1 | Should -Match 'target\.installUnits'
        $linkPs1 | Should -Match 'unit\.source'
        $linkPs1 | Should -Match 'unit\.target'
        $linkPs1 | Should -Match 'unit\.type'
    }

    It "link.sh hardcoded install units match target-mapping.json" {
        $expected = Get-InstallUnitKeysFromMapping -MappingPath $mappingPath
        $actual = Get-LinkShInstallUnitKeysFromSource -Content $linkSh

        $expected.Count | Should -BeGreaterThan 0
        $actual.Count | Should -BeGreaterThan 0
        $missing = $expected | Where-Object { $_ -notin $actual }
        $extra = $actual | Where-Object { $_ -notin $expected }
        $missing | Should -BeNullOrEmpty
        $extra | Should -BeNullOrEmpty
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

    It "link.sh install-unit extraction finds representative units [sanity check]" {
        $units = Get-LinkShInstallUnitKeysFromSource -Content $linkSh
        $units | Should -Not -BeNullOrEmpty
        $units | Should -Contain 'copilot|directory|.github/prompts|.github/prompts|link-directory'
        $units | Should -Contain 'opencode|file|.opencode/opencode.json|.opencode/opencode.json|config-copy-or-snippet'
    }

    It "both scripts support a non-interactive bypass flag [regression guard]" {
        # link.ps1 parses raw args; link.sh uses --yes / -y.
        $linkPs1 | Should -Match ([regex]::Escape('"--yes", "-y", "-Force", "--force"'))
        $linkSh  | Should -Match '\-\-yes'
        $linkSh  | Should -Match ([regex]::Escape('|-y|'))
    }

    It "both scripts checksum-clean legacy model mappings" {
        $legacyTargets = @(
            '.claude/model-mapping.claude.json',
            '.agents/model-mapping.codex.json',
            '.opencode/model-mapping.opencode.json',
            '.kilo/model-mapping.kilo.json'
        )
        foreach ($target in $legacyTargets) {
            $escaped = [regex]::Escape($target)
            $linkPs1 | Should -Match $escaped
            $linkSh  | Should -Match $escaped
        }
        $linkPs1 | Should -Match 'checksum'
        $linkSh  | Should -Match 'sha256'
    }
}

# ---------------------------------------------------------------------------
# unlink.ps1 <-> unlink.sh parity
# ---------------------------------------------------------------------------
Describe "unlink.ps1 <-> unlink.sh parity" {
    $unlinkPs1 = Get-Content (Join-Path $repoRoot "scripts/unlink.ps1") -Raw -Encoding UTF8
    $unlinkSh  = Get-Content (Join-Path $repoRoot "scripts/unlink.sh")  -Raw -Encoding UTF8
    $mappingPath = Join-Path $repoRoot ".github/shared/target-mapping.json"

    It "unlink.ps1 reads install units from target-mapping.json" {
        $unlinkPs1 | Should -Match 'TargetMappingPath'
        $unlinkPs1 | Should -Match 'ConvertFrom-Json'
        $unlinkPs1 | Should -Match 'target\.installUnits'
        $unlinkPs1 | Should -Match 'unit\.target'
        $unlinkPs1 | Should -Match 'unit\.type'
    }

    It "unlink.sh hardcoded install-unit targets match target-mapping.json" {
        $expected = Get-UnlinkUnitKeysFromMapping -MappingPath $mappingPath
        $actual = Get-UnlinkShUnitKeysFromSource -Content $unlinkSh

        $expected.Count | Should -BeGreaterThan 0
        $actual.Count | Should -BeGreaterThan 0
        $missing = $expected | Where-Object { $_ -notin $actual }
        $extra = $actual | Where-Object { $_ -notin $expected }
        $missing | Should -BeNullOrEmpty
        $extra | Should -BeNullOrEmpty
    }

    It "both scripts support a non-interactive bypass flag [regression guard]" {
        # unlink.ps1 parses raw args; unlink.sh uses --yes / -y.
        $unlinkPs1 | Should -Match ([regex]::Escape('"--yes", "-y", "-Force", "--force"'))
        $unlinkSh  | Should -Match '\-\-yes'
        $unlinkSh  | Should -Match ([regex]::Escape('|-y|'))
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

    It "both PowerShell scripts use target-mapping install units" {
        $linkPs1 | Should -Match 'target\.installUnits'
        $unlinkPs1 | Should -Match 'target\.installUnits'
    }
}

# ---------------------------------------------------------------------------
# link.sh <-> unlink.sh parity (bash pair)
# ---------------------------------------------------------------------------
Describe "link.sh <-> unlink.sh parity (bash pair)" {
    $linkSh   = Get-Content (Join-Path $repoRoot "scripts/link.sh")   -Raw -Encoding UTF8
    $unlinkSh = Get-Content (Join-Path $repoRoot "scripts/unlink.sh") -Raw -Encoding UTF8
    $mappingPath = Join-Path $repoRoot ".github/shared/target-mapping.json"

    It "both bash scripts cover every mapped install-unit target" {
        $linkTargets = Get-LinkShInstallUnitKeysFromSource -Content $linkSh |
            ForEach-Object { ($_ -split '\|')[3] } |
            Sort-Object -Unique
        $unlinkTargets = Get-UnlinkShUnitKeysFromSource -Content $unlinkSh |
            ForEach-Object { ($_ -split '\|')[0] } |
            Sort-Object -Unique
        $mappingTargets = Get-UnlinkUnitKeysFromMapping -MappingPath $mappingPath |
            ForEach-Object { ($_ -split '\|')[0] } |
            Sort-Object -Unique

        $linkTargets.Count | Should -BeGreaterThan 0
        $unlinkTargets.Count | Should -BeGreaterThan 0
        $missingFromLink = $mappingTargets | Where-Object { $_ -notin $linkTargets }
        $missingFromUnlink = $mappingTargets | Where-Object { $_ -notin $unlinkTargets }
        $missingFromLink | Should -BeNullOrEmpty
        $missingFromUnlink | Should -BeNullOrEmpty
    }
}

# ---------------------------------------------------------------------------
# link.ps1 <-> link.sh copy-directory semantics divergence note
# ---------------------------------------------------------------------------
Describe "link copy-directory semantics parity note" {
    $linkPs1 = Get-Content (Join-Path $repoRoot "scripts/link.ps1") -Raw -Encoding UTF8
    $linkSh  = Get-Content (Join-Path $repoRoot "scripts/link.sh")  -Raw -Encoding UTF8

    It "both scripts document the copy-directory semantic divergence" {
        # Windows link.ps1 preserves user edits + removes stale managed files;
        # POSIX link.sh uses a wholesale overwrite. Each script must carry the
        # matching side of the divergence note so the contract stays visible.
        $linkPs1 | Should -Match 'copy-directory semantics: Windows preserves user edits'
        $linkSh  | Should -Match 'copy-directory semantics: POSIX uses a wholesale overwrite'
    }
}

# ---------------------------------------------------------------------------
# cg-brain-init and cg-token-audit registration parity
# ---------------------------------------------------------------------------
Describe "cg-brain-init registration parity" {
    $linkPs1 = Get-Content (Join-Path $repoRoot "scripts/link.ps1") -Raw -Encoding UTF8
    $linkSh  = Get-Content (Join-Path $repoRoot "scripts/link.sh")  -Raw -Encoding UTF8

    It "link.ps1 points users to generic AI tool reload guidance" {
        $linkPs1 | Should -Match 'Restart your AI coding tool'
    }

    It "link.sh points users to generic AI tool reload guidance" {
        $linkSh | Should -Match 'Restart your AI coding tool'
    }

    It "bin/cg-brain-init exists in the repo" {
        $binPath = Join-Path $repoRoot "bin/cg-brain-init"
        Test-Path $binPath | Should -Be $true
    }

    It "bin/cg-brain-init.cmd exists in the repo" {
        $binPath = Join-Path $repoRoot "bin/cg-brain-init.cmd"
        Test-Path $binPath | Should -Be $true
    }

    It "install.ps1 copies cg-brain-init.cmd to bin/" {
        $installPs1 = Get-Content (Join-Path $repoRoot "install.ps1") -Raw -Encoding UTF8
        $installPs1 | Should -Match 'cg-brain-init\.cmd'
    }

    It "install.sh creates cg-brain-init wrapper in bin/" {
        $installSh = Get-Content (Join-Path $repoRoot "scripts/install.sh") -Raw -Encoding UTF8
        $installSh | Should -Match 'cg-brain-init'
    }

    It "bin/cg-token-audit exists in the repo" {
        $binPath = Join-Path $repoRoot "bin/cg-token-audit"
        Test-Path $binPath | Should -Be $true
    }

    It "bin/cg-token-audit.cmd exists in the repo" {
        $binPath = Join-Path $repoRoot "bin/cg-token-audit.cmd"
        Test-Path $binPath | Should -Be $true
    }

    It "install.ps1 copies cg-token-audit.cmd to bin/" {
        $installPs1 = Get-Content (Join-Path $repoRoot "install.ps1") -Raw -Encoding UTF8
        $installPs1 | Should -Match 'cg-token-audit\.cmd'
    }

    It "install.sh creates cg-token-audit wrapper in bin/" {
        $installSh = Get-Content (Join-Path $repoRoot "scripts/install.sh") -Raw -Encoding UTF8
        $installSh | Should -Match 'cg-token-audit'
        $installSh | Should -Match 'cg_audit_context\.py'
    }
}
