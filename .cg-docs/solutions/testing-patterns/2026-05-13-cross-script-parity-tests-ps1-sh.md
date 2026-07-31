---
date: 2026-05-13
title: "Cross-script parity tests: keeping ps1 and sh scripts in sync"
category: "testing-patterns"
language: "both"
tags: [parity, powershell, bash, cross-platform, regression, managed-dirs, pester]
root-cause: "ps1 and sh scripts that implement the same operation can drift silently — managed directories, verification paths, gitignore markers, and bypass flags may diverge without any failing test."
severity: "P2"
---

# Cross-Script Parity Tests: Keeping `.ps1` and `.sh` Scripts in Sync

## Problem

`link.ps1` and `link.sh` (and `unlink.ps1` / `unlink.sh`) must produce
equivalent behaviour on Windows and macOS. When a managed directory is added to
one but not the other, or when a bypass flag is added to one script but
forgotten on its counterpart, the divergence is invisible. Individual unit tests
for each script pass; only the combined behaviour breaks.

Examples of silent divergence that occurred before parity tests existed:

- `link.ps1` had `shared/` in `$ManagedDirs`; `link.sh` was missing it
- `unlink.ps1` had `[switch]$Force`; `unlink.sh` had no `--yes` equivalent
- Verification file path differed: `cg-setup.prompt.md` vs `cg-start.prompt.md`

## Root Cause

Scripts are maintained independently. Without a cross-script test, reviewers
catch divergence only by manual comparison during code review — which is
unreliable on diffs that touch many files.

## Solution

Create `tests/parity.Tests.ps1` with `Describe` blocks that read **both** the
ps1 and sh source files as text and assert structural equivalence.

### Helper: extract managed directories

```powershell
function Get-ManagedDirsFromSource {
    param([string]$Content)
    # Match either PS or bash array declaration:
    #   $ManagedDirs = @("prompts", "skills", ...)   # PowerShell
    #   MANAGED_DIRS=("prompts" "skills" ...)          # bash
    $m = [regex]::Match($Content, '(?:MANAGED_DIRS|\$ManagedDirs)\s*=\s*@?\(([^)]+)\)')
    if (-not $m.Success) { return @() }
    $inner = $m.Groups[1].Value
    $items = [regex]::Matches($inner, '"([^"]+)"') | ForEach-Object { $_.Groups[1].Value }
    return ($items | Sort-Object)
}
```

### Describe: link.ps1 ↔ link.sh parity

```powershell
Describe "link.ps1 <-> link.sh parity" {
    $linkPs1 = Get-Content (Join-Path $repoRoot "scripts/link.ps1") -Raw -Encoding UTF8
    $linkSh  = Get-Content (Join-Path $repoRoot "scripts/link.sh")  -Raw -Encoding UTF8

    It "both scripts define the same managed directories" {
        $ps1Dirs = Get-ManagedDirsFromSource $linkPs1
        $shDirs  = Get-ManagedDirsFromSource $linkSh

        # Parse guards: if either returns @() the comparison is vacuously true.
        $ps1Dirs.Count | Should -BeGreaterThan 0
        $shDirs.Count  | Should -BeGreaterThan 0

        ($ps1Dirs | Where-Object { $_ -notin $shDirs }) | Should -BeNullOrEmpty
        ($shDirs  | Where-Object { $_ -notin $ps1Dirs }) | Should -BeNullOrEmpty
    }

    It "both scripts reference the same verification file" {
        $linkPs1 | Should -Match 'cg-setup\.prompt\.md'
        $linkSh  | Should -Match 'cg-setup\.prompt\.md'
    }

    It "both scripts use the same .gitignore block marker" {
        $marker = 'Compound GPID managed items'
        $linkPs1 | Should -Match ([regex]::Escape($marker))
        $linkSh  | Should -Match ([regex]::Escape($marker))
    }

    It "link.ps1 extraction regex finds the array [sanity check]" {
        $dirs = Get-ManagedDirsFromSource $linkPs1
        $dirs | Should -Not -BeNullOrEmpty
        $dirs | Should -Contain 'prompts'
    }

    It "link.sh extraction regex finds the array [sanity check]" {
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
```

### Describe: unlink.ps1 ↔ unlink.sh parity (same structure)

Use the same pattern for unlink. Add a `[regression guard]` It block asserting
that `[switch]$Force` (ps1) / `--yes -y` (sh) are both present.

### Describe: ps1 ↔ ps1 and sh ↔ sh PowerShell/bash pairs

Useful for verifying `link.ps1` and `unlink.ps1` define the same `$ManagedDirs`
(the unlink pass must remove exactly what link created).

### Parse guard rule

> **Critical**: Without parse guards, if `Get-ManagedDirsFromSource` returns
> `@()` for both scripts (e.g., the regex fails after a refactor), `$missing`
> and `$extra` are both empty and the parity assertion passes vacuously.
> **Always** add `$dirs.Count | Should -BeGreaterThan 0` and sanity checks
> like `$dirs | Should -Contain 'prompts'` to every parity Describe block.

## Registration

Add the parity test file to the `$testNames` allowlist in `tests/Run-Tests.ps1`:

```powershell
$testNames = @(
    'charter', 'helpers', 'roadmap', 'prompt-tools', 'model-assignments',
    'pester-safety', 'ps51-compat', 'create-release', 'bash-scripts',
    'install', 'cg-index', 'run-tests-runner', 'update',
    'parity',     # <-- add before link and unlink
    'link', 'unlink'
)
```

## Prevention

- Whenever a managed directory is added to any `link.*` or `unlink.*` script,
  the parity test will catch the missing counterpart on the next test run.
- Whenever a new bypass flag or config value is added to one script, add a
  corresponding parity assertion in the same commit.
- Add a CI PR check comment: "parity CI check passes" to the PR template
  checklist.

## Related

- [`2026-05-13-ci-bypass-flag-force-yes-interactive-scripts.md`](2026-05-13-ci-bypass-flag-force-yes-interactive-scripts.md) — the `-Force`/`--yes`
  bypass flag pattern that parity tests verify stays in sync
- [`2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md`](2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md) — exact
  count assertions for guard-count parity
- [`2026-05-12-source-scanning-regression-guard-for-scripting-anti-patterns.md`](2026-05-12-source-scanning-regression-guard-for-scripting-anti-patterns.md) — source-scan
  regression guards for scripting patterns
- [`2026-07-31-advisory-inheritance-audit-and-legacy-cleanup.md`](2026-07-31-advisory-inheritance-audit-and-legacy-cleanup.md) — checksum-guarded cleanup for removed cross-platform install units
