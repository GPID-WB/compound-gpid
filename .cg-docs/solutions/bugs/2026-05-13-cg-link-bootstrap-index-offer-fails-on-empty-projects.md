---
date: 2026-05-13
title: "cg-link bootstrap index offer always fails on empty projects"
category: "bugs"
type: "bug"
language: "both"
tags: [link, cg-index, bootstrap, empty-project, link.ps1, link.sh, ux]
root-cause: "cg-link offered to run cg-index unconditionally, but cg-index requires .cg-docs/solutions/ which never exists on a freshly-linked project"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# cg-link bootstrap index offer always fails on empty projects

## Symptom

Running `cg-link` on a new empty project completed the symlink/junction setup but then
prompted to build the knowledge index. When the user answered `y`, the command failed:

```
Would you like to build the initial knowledge index now? (y/N) y
Building knowledge index...
[cg-index] ERROR: /Users/.../temp/testing-cg/.cg-docs/solutions does not exist.
Run cg-index from a project root containing a .cg-docs/solutions/ directory.
WARNING: cg-index failed (non-fatal).
```

The offer itself was confusing: a user running `cg-link` for the first time on a new
project has no `.cg-docs/solutions/` directory by definition — `cg-link` is the step
that sets up the plugin before `/cg-setup` creates any project structure.

## Root Cause

Both `scripts/link.ps1` and `scripts/link.sh` contained a "bootstrap offer" block at
the end of a successful link that prompted the user to run `cg-index --all`. The check
only gated on whether `cg-index` was installed — it did not check whether the current
project had a `.cg-docs/solutions/` directory that `cg-index` requires to run.

The primary use case for `cg-link` is linking to a brand-new project. In that scenario
`.cg-docs/solutions/` will never exist, so the offer always produces a confusing error.
The right place for indexing is `/cg-setup`, after the project has been configured and
`.cg-docs/` is populated.

## Reproduction Test

Added to `tests/link.Tests.ps1`:

```powershell
Describe "link.ps1 - no bootstrap index offer at link time" {
    It "link.ps1 does not prompt to run cg-index during cg-link [regression guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw
        ($content -match 'Would you like to build the initial knowledge index') | Should -Be $false
    }

    It "link.ps1 does not call cg-index in the bootstrap block [regression guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.ps1") -Raw
        ($content -match '& cg-index') | Should -Be $false
    }
}

Describe "link.sh - no bootstrap index offer at link time" {
    It "link.sh does not prompt to run cg-index during cg-link [regression guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.sh") -Raw
        ($content -match 'Would you like to build the initial knowledge index') | Should -Be $false
    }

    It "link.sh does not call cg-index in the bootstrap block [regression guard]" {
        $content = Get-Content (Join-Path $PSScriptRoot "..\scripts\link.sh") -Raw
        ($content -match 'cg-index --all') | Should -Be $false
    }
}
```

All 4 tests failed on the pre-fix code and pass after the fix.

## Fix

Removed the entire bootstrap index offer block from both scripts.

**`scripts/link.ps1`** — deleted:
```powershell
# --- Bootstrap offer: build initial knowledge index ---
if ([Environment]::UserInteractive) {
    $cgIndexCmd = Get-Command cg-index -ErrorAction SilentlyContinue
    if ($cgIndexCmd) {
        Write-Host "Would you like to build the initial knowledge index now? (y/N)" -ForegroundColor Cyan
        $indexAnswer = (Read-Host).Trim().ToLower()
        if ($indexAnswer -eq 'y' -or $indexAnswer -eq 'yes') {
            Write-Host "Building knowledge index..." -ForegroundColor DarkGray
            try {
                & cg-index --all
                Write-Host "  Knowledge index built." -ForegroundColor DarkGray
            } catch {
                Write-Warning "  cg-index failed: $_"
            }
        }
    }
}
```

**`scripts/link.sh`** — deleted:
```bash
# Bootstrap offer: build initial knowledge index
if [ -t 0 ] && command -v cg-index > /dev/null 2>&1; then
    printf '\033[0;36mWould you like to build the initial knowledge index now? (y/N)\033[0m '
    read -r index_answer
    case "$index_answer" in
        y|Y|yes|Yes)
            printf 'Building knowledge index...\n'
            cg-index --all || printf 'WARNING: cg-index failed (non-fatal).\n' >&2
            ;;
    esac
fi
```

Both scripts now end cleanly after printing `Run in VS Code / Positron Copilot Chat: /cg-setup`.

## Lessons Learned

- **`cg-link` is a pre-setup step** — it runs before `/cg-setup`, before any project
  structure exists. Any action offered at link time must be valid on a completely empty
  project directory. `cg-index` is not.
- **Never offer a command at install/link time without checking its preconditions** —
  gating only on "is the command installed?" is insufficient. The command's own
  requirements (here: `.cg-docs/solutions/` must exist) must also be satisfied.
- **Indexing belongs in `/cg-setup`** — by the time `/cg-setup` runs, the project is
  configured and `.cg-docs/` may already contain content worth indexing.

## Related

- `.cg-docs/solutions/bugs/2026-05-12-link-read-host-empty-string-throws-psargumentexception.md`
  — earlier bug in the same bootstrap block (`Read-Host ""` crash). That fix kept the
  block; this fix removes it entirely.
- `.cg-docs/solutions/testing-patterns/2026-05-12-source-scanning-regression-guard-for-scripting-anti-patterns.md`
  — the source-scanning regression-guard pattern used for the reproduction tests here.
