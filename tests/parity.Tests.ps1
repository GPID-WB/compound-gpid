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
    $matches = [regex]::Matches($Content, "'([^|'`r`n]+)\|([^|'`r`n]+)(?:\|[^'`r`n]*)?'")
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

    It "both scripts localize compatibility skill links when Kilo is installed" {
        foreach ($content in @($linkPs1, $linkSh)) {
            $content | Should -Match 'kilo-compat-skills'
            $content | Should -Match 'claude-code'
            $content | Should -Match 'codex'
            $content | Should -Match 'opencode'
            $content | Should -Match 'localized for Kilo compatibility discovery'
        }
    }

    It "both scripts enforce exact ownership and project-contained copy targets" {
        $linkPs1 | Should -Match 'Assert-CgManagedCopyTargetSafe'
        $linkSh | Should -Match 'os\.path\.commonpath'
        $linkSh | Should -Match 'same_realpath'
        $linkSh | Should -Not -Match '\[\[\s+"\$existing_target"\s+==\s+\*compound-gpid\*\s+\]\]'
    }

    It "both scripts stage compatibility links before replacing working links" {
        $linkPs1 | Should -Match 'Set-CgJunctionTargetSafely'
        $linkPs1 | Should -Match 'Temporary junction did not resolve'
        $linkSh | Should -Match 'replace_symlink_safely'
        $linkSh | Should -Match 'os\.replace\(sys\.argv\[1\], sys\.argv\[2\]\)'
    }

    It "POSIX managed-copy failures are explicitly propagated" {
        $linkSh | Should -Match 'managed-copy synchronization failed'
        $linkSh | Should -Match 'copy-directory installation failed'
        $linkSh | Should -Match 'migrated legacy managed file'
    }
}

# ---------------------------------------------------------------------------
# cg-link singular platform flag
# ---------------------------------------------------------------------------
Describe "cg-link - singular --platform flag" {
    $linkPs1 = Get-Content (Join-Path $repoRoot "scripts/link.ps1") -Raw -Encoding UTF8
    $linkSh  = Get-Content (Join-Path $repoRoot "scripts/link.sh")  -Raw -Encoding UTF8

    It "recognizes singular --platform in the PowerShell argument parser" {
        # The singular alias must be a parser token in its own right; matching
        # only the prefix of --platforms is insufficient.
        $linkPs1 | Should -Match '(?m)^\s*}\s*elseif\s*\(\$arg\s+-like\s+"--platform=\*"\)'
    }

    It "recognizes singular --platform in the bash argument parser" {
        # The macOS launcher must select only the requested platform instead of
        # warning on --platform and falling back to the all-platform default.
        $linkSh | Should -Match '(?m)^\s*--platform(?!s)(?:=|\|)'
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

    It "both PowerShell scripts manage Kilo compatibility mirrors" {
        $linkPs1 | Should -Match 'kilo-compat-skills'
        $unlinkPs1 | Should -Match 'kilo-compat-skills'
    }

    It "unlink requires exact junction targets and rejects reparse traversal" {
        $unlinkPs1 | Should -Match 'ExpectedTarget'
        $unlinkPs1 | Should -Match 'Test-CgManagedCopyPathSafe'
        $unlinkPs1 | Should -Not -Match '\*compound-gpid\*'
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

    It "both bash scripts manage Kilo compatibility mirrors" {
        $linkSh | Should -Match 'kilo-compat-skills'
        $unlinkSh | Should -Match 'kilo-compat-skills'
    }

    It "unlink.sh requires exact realpaths and project-contained targets" {
        $unlinkSh | Should -Match 'same_realpath'
        $unlinkSh | Should -Match 'os\.path\.commonpath'
        $unlinkSh | Should -Not -Match '\[\[\s+"\$link_target"\s+==\s+\*compound-gpid\*\s+\]\]'
    }
}

# ---------------------------------------------------------------------------
# link.ps1 <-> link.sh copy-directory semantics parity note
# ---------------------------------------------------------------------------
Describe "link copy-directory semantics parity note" {
    $linkPs1 = Get-Content (Join-Path $repoRoot "scripts/link.ps1") -Raw -Encoding UTF8
    $linkSh  = Get-Content (Join-Path $repoRoot "scripts/link.sh")  -Raw -Encoding UTF8

    It "both scripts preserve user edits through checksum-managed copies" {
        $linkPs1 | Should -Match 'both Windows and POSIX preserve user edits'
        $linkSh  | Should -Match 'preserve user edits, remove only unchanged stale managed files'
        $linkPs1 | Should -Match '\.compound-gpid-managed-copy\.json'
        $linkSh  | Should -Match '\.compound-gpid-managed-copy\.json'
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

Describe "Kilo coexistence launcher parity" {
    It "registers the certified launcher on Windows and POSIX" {
        $installPs1 = Get-Content (Join-Path $repoRoot "install.ps1") -Raw -Encoding UTF8
        $installSh = Get-Content (Join-Path $repoRoot "scripts/install.sh") -Raw -Encoding UTF8
        $linkPs1 = Get-Content (Join-Path $repoRoot "scripts/link.ps1") -Raw -Encoding UTF8
        $linkSh = Get-Content (Join-Path $repoRoot "scripts/link.sh") -Raw -Encoding UTF8
        $updatePs1 = Get-Content (Join-Path $repoRoot "scripts/update.ps1") -Raw -Encoding UTF8
        $updateSh = Get-Content (Join-Path $repoRoot "scripts/update.sh") -Raw -Encoding UTF8

        $installPs1 | Should -Match 'cg-kilo'
        $installSh | Should -Match 'cg-kilo'
        $linkPs1 | Should -Match 'Invoke-CgKiloPreflight'
        $linkSh | Should -Match 'run_kilo_preflight'
        $updatePs1 | Should -Match 'Invoke-CgKiloPreflight'
        $updateSh | Should -Match 'cg_kilo_preflight\.py'
    }

    It "uses the same process-scoped containment control" {
        $worker = Get-Content (Join-Path $repoRoot "scripts/cg_kilo_preflight.py") -Raw -Encoding UTF8
        $worker | Should -Match 'KILO_DISABLE_EXTERNAL_SKILLS'
        $worker | Should -Match 'os\.environ\.copy\(\)'
        $worker | Should -Match 'subprocess\.run'
    }
}

Describe "hybrid Copilot skill projection parity" {
    $mapping = Get-Content (Join-Path $repoRoot ".github/shared/target-mapping.json") -Raw -Encoding UTF8 | ConvertFrom-Json
    $copilot = @($mapping.targets | Where-Object { $_.id -eq "copilot" })[0]
    $linkPs1 = Get-Content (Join-Path $repoRoot "scripts/link.ps1") -Raw -Encoding UTF8
    $linkSh = Get-Content (Join-Path $repoRoot "scripts/link.sh") -Raw -Encoding UTF8
    $unlinkPs1 = Get-Content (Join-Path $repoRoot "scripts/unlink.ps1") -Raw -Encoding UTF8
    $unlinkSh = Get-Content (Join-Path $repoRoot "scripts/unlink.sh") -Raw -Encoding UTF8

    It "reserves the same Copilot skill root on Windows and POSIX" {
        @($copilot.projectedCategories)[0] | Should -Be "skills"
        @($copilot.projectRoots.managed)[0] | Should -Be ".github/skills"
        @($copilot.installUnits | Where-Object { $_.target -eq ".github/skills" }).Count | Should -Be 0
        $linkPs1 | Should -Match 'projectedCategories'
        $linkSh | Should -Match 'COPILOT_PROJECTED_CATEGORIES="skills"'
    }

    It "delegates checksum-owned unlink on both platforms" {
        $unlinkPs1 | Should -Match 'Invoke-CgProjection'
        $unlinkPs1 | Should -Match 'Mode unlink'
        $unlinkSh | Should -Match 'cg_project_projection\.py'
        $unlinkSh | Should -Match '\-\-unlink'
    }
}
