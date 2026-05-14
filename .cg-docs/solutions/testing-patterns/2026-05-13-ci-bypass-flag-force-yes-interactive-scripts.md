---
date: 2026-05-13
title: "CI bypass flag pattern: [switch]$Force / --yes for interactive scripts"
category: "testing-patterns"
language: "both"
tags: [ci, powershell, bash, interactive, Read-Host, force-flag, non-interactive, e2e]
root-cause: "Scripts with interactive confirmation prompts hang indefinitely in CI because there is no stdin to satisfy Read-Host / read -r."
severity: "P1"
---

# CI Bypass Flag Pattern: `[switch]$Force` / `--yes` for Interactive Scripts

## Problem

PowerShell scripts (`link.ps1`, `unlink.ps1`) and bash scripts (`link.sh`,
`unlink.sh`) contain interactive confirmation prompts (`Read-Host`, `read -r`).
When these scripts are invoked from GitHub Actions E2E smoke tests or any
non-interactive automation, the runner hangs indefinitely waiting for keyboard
input that never arrives. The job eventually times out with a cryptic timeout
error rather than a meaningful failure message.

Secondary issue: even if the CI job is configured with a short timeout, the
hanging step can freeze VS Code's terminal if the test runner is invoked
interactively (e.g., Pester calling the script).

## Root Cause

Scripts designed for interactive developer use assume a human is present at the
terminal. CI runners have no attached TTY. `Read-Host` in PowerShell 5.1 blocks
forever; `read -r </dev/tty` in bash fails with "device not configured" on
macOS GitHub Actions runners and hangs on Linux.

## Solution

Add a bypass flag to every script that has interactive prompts. The flag is
optional (defaults to `$false` / `0`) so the developer experience is unchanged.

### PowerShell pattern (`scripts/unlink.ps1`, `scripts/link.ps1`)

```powershell
param(
    # Skip all interactive confirmation prompts. Used by CI and any
    # automation that cannot supply keyboard input.
    [switch]$Force
)

# ... later, wherever a confirmation prompt would appear:
if (-not $Force) {
    $answer = Read-Host "Remove .github junction? [y/N]"
    if ($answer -notmatch "^[Yy]$") {
        Write-Host "Aborted." -ForegroundColor Yellow
        exit 0
    }
}
# (proceed with the operation)
```

Invoke from CI:
```yaml
- name: E2E smoke test
  shell: pwsh
  run: |
    & "$env:GITHUB_WORKSPACE\scripts\unlink.ps1" -Force
```

### Bash pattern (`scripts/unlink.sh`, `scripts/link.sh`)

```bash
FORCE=0
for arg in "$@"; do
    case "$arg" in
        --yes|-y) FORCE=1 ;;
    esac
done

# ... later, wherever a confirmation prompt would appear:
if [[ "$FORCE" -eq 0 ]]; then
    printf 'Remove .github symlinks? [y/N] '
    read -r answer </dev/tty
    if [[ ! "$answer" =~ ^[Yy]$ ]]; then
        print_yellow "Aborted."; exit 0
    fi
fi
# (proceed with the operation)
```

Invoke from CI:
```yaml
- name: E2E smoke test
  run: bash scripts/unlink.sh --yes
```

### Key details

- **Both short and long forms**: Always support both `--yes` and `-y` in bash.
  Tests must assert both forms are present.
- **`printf` inside the FORCE guard**: Move the prompt text *inside* the
  `if [[ "$FORCE" -eq 0 ]]` block so CI logs are not polluted with
  "Proceed? [y/N]" lines when `--yes` is used.
- **No change to normal operation**: When invoked interactively (no `-Force` /
  `--yes`), both confirmation steps still appear exactly as before.

## Regression Tests

Add a dedicated `Describe` block asserting the flag is wired correctly:

### PowerShell (Pester 4)

```powershell
Describe "unlink.ps1 - -Force flag for non-interactive use" {
    $unlinkPs1 = Join-Path $PSScriptRoot "..\scripts\unlink.ps1"
    $content   = Get-Content $unlinkPs1 -Raw -Encoding UTF8 -ErrorAction SilentlyContinue

    It "declares a [switch]`$Force parameter [regression guard]" {
        $content | Should -Match '\[switch\]\$Force'
    }

    It "all confirmation paths are guarded by -not `$Force (N guards required) [regression guard]" {
        # Count separately — Should -Match short-circuits on first hit and
        # misses a missing second guard entirely.
        ($content -split '\r?\n' | Where-Object { $_ -match 'if \(-not \$Force\)' } | Measure-Object).Count |
            Should -Be 2    # adjust N to match the actual number of prompts
    }

    It "does not call Read-Host unconditionally [regression guard]" {
        ($content -split '\r?\n' | Where-Object { $_ -match 'Read-Host' } | Measure-Object).Count |
            Should -Be 2    # adjust N to match the actual number of prompts
    }
}
```

> **Anti-pattern**: `$content | Should -Match 'if \(-not \$Force\)'` passes on
> the first match — if one of two required guards is deleted the test still
> passes. Always count with `Measure-Object`.

### Bash (tested from PowerShell via file content checks)

```powershell
Describe "unlink.sh - script structure" {
    $content = Get-Content (Join-Path $repoRoot "scripts/unlink.sh") -Raw -Encoding UTF8

    It "supports --yes / -y flag for non-interactive use [regression guard]" {
        $content | Should -Match '\-\-yes'
        $content | Should -Match '(?<![\w])-y[)\s]'   # short form, not inside a word
    }

    It "prompt strings are inside the FORCE guard (N guards required) [regression guard]" {
        ([regex]::Matches($content, 'if\s+\[\[.*FORCE') | Measure-Object).Count |
            Should -Be 2    # adjust N to match the actual number of prompts
    }
}
```

## Prevention

- Before adding any `Read-Host` or `read -r` call to a script, ask: "will this
  script ever be called from CI or automation?" If yes, add `[switch]$Force` /
  `--yes -y` from the start.
- The E2E smoke test step must always pass `-Force` / `--yes` to any CG script
  that has interactive prompts. Make this explicit in CI YAML comments.
- Parity: if `link.ps1` has `-Force`, `link.sh` must have `--yes / -y`. Assert
  this in `tests/parity.Tests.ps1`.

## Related

- [`2026-05-13-cross-script-parity-tests-ps1-sh.md`](2026-05-13-cross-script-parity-tests-ps1-sh.md) — parity test approach
  ensuring ps1↔sh always stay in sync
- [`2026-05-13-e2e-smoke-test-github-actions-windows-junction-teardown.md`](../git-workflows/2026-05-13-e2e-smoke-test-github-actions-windows-junction-teardown.md) — E2E
  test that invokes scripts with `-Force`/`--yes` in CI
- [`2026-03-19-testing-powershell-switch-parameters.md`](2026-03-19-testing-powershell-switch-parameters.md) — general PS switch
  parameter testing patterns
- [`2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md`](2026-04-17-exact-count-assertion-prevents-silent-regression-when-test-name-states-count.md) — counting
  assertions prevent silent regressions
