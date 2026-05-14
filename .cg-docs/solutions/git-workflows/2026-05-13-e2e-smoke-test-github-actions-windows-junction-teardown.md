---
date: 2026-05-13
title: "E2E smoke test in GitHub Actions with safe Windows junction teardown"
category: "git-workflows"
language: "both"
tags: [ci, github-actions, windows, junction, teardown, e2e, macos, symlink, smoke-test]
root-cause: "Remove-Item -Recurse follows junction links into the source repository tree, deleting source files on GitHub Actions Windows runners when junction removal fails silently."
severity: "P1"
---

# E2E Smoke Test in GitHub Actions with Safe Windows Junction Teardown

## Problem

After adding an E2E smoke test step to CI, the Windows runner occasionally
deleted source files from `$GITHUB_WORKSPACE/.github/prompts/*` during teardown.
The step used `Remove-Item -Recurse -Force` to clean up the E2E working
directory. On GitHub Actions Windows 2022 runners, Windows Defender can lock
files accessed through junctions, causing `Remove-Item -Force` on the junction
itself to fail silently (exit code 0). The subsequent `-Recurse` then traverses
the surviving junction link and removes the source files.

## Root Cause

`Remove-Item -Recurse` on a directory tree that contains directory junctions
**follows the junctions** and deletes files inside the junction targets. This is
the correct NTFS behaviour (Windows Defender treats junction traversal as a
normal directory walk), but it is catastrophic when the junction target is the
repository's own `.github/` folder. The test step was designed for teardown —
it ended up destroying the workspace being tested.

This is a known VS Code freeze risk in Pester tests and affects any PowerShell
script that needs to clean up a directory tree containing junctions.

## Solution

### Teardown: use `cmd /c rmdir /s /q`

Windows `cmd.exe`'s `rmdir /s /q` treats directory junctions as **atomic
entries** — it removes the junction link without following it. It never descends
into junction targets.

```yaml
- name: E2E smoke test teardown (Windows)
  if: always() && runner.os == 'Windows'
  shell: pwsh
  run: |
    $e2eDir = "$env:RUNNER_TEMP\e2e-project"
    if (Test-Path $e2eDir) {
        cmd /c rmdir /s /q "$e2eDir" 2>&1 | Out-Null
    }
```

> **Never use** `Remove-Item -Recurse` on a directory that may contain
> junction links. Always use `cmd /c rmdir /s /q` for Windows teardown.

### Pre-clean: prevent stale state from prior runs

On self-hosted runners `$RUNNER_TEMP` persists between jobs. Pre-clean at the
start of the E2E step to guarantee a fresh state:

```powershell
$e2eDir = "$env:RUNNER_TEMP\e2e-project"
if (Test-Path $e2eDir) { cmd /c rmdir /s /q "$e2eDir" 2>&1 | Out-Null }
New-Item -ItemType Directory -Path $e2eDir | Out-Null
Set-Location $e2eDir
```

### Full E2E step structure (Windows)

```yaml
- name: E2E smoke test (Windows)
  if: success() && runner.os == 'Windows'
  shell: pwsh
  run: |
    $e2eDir = "$env:RUNNER_TEMP\e2e-project"
    if (Test-Path $e2eDir) { cmd /c rmdir /s /q "$e2eDir" 2>&1 | Out-Null }
    New-Item -ItemType Directory -Path $e2eDir | Out-Null
    Set-Location $e2eDir

    # 1. Link (use & to dot-source, not pwsh -File which spawns a child process)
    & "$env:GITHUB_WORKSPACE\scripts\link.ps1"

    # 2. Assert junction created and file accessible through it
    $junction = Get-Item ".github\prompts" -ErrorAction Stop
    if ($junction.LinkType -ne 'Junction') {
        throw "Expected .github\prompts to be a Junction, got: $($junction.LinkType)"
    }
    if (-not (Test-Path ".github\prompts\cg-setup.prompt.md")) {
        throw "cg-setup.prompt.md not accessible through junction"
    }

    # 3. Idempotency: link a second time - must not error
    & "$env:GITHUB_WORKSPACE\scripts\link.ps1"

    # 4. Unlink (-Force skips interactive confirmation in CI)
    & "$env:GITHUB_WORKSPACE\scripts\unlink.ps1" -Force

    # 5. Assert junction removed
    if (Test-Path ".github\prompts") {
        throw "Expected .github\prompts removed after unlink"
    }

    # 6. Assert .gitignore cleaned up
    if (Test-Path ".gitignore") {
        if ((Get-Content ".gitignore" -Raw) -match '\.github/prompts/') {
            throw ".gitignore not cleaned up after unlink"
        }
    }
    Write-Host "E2E smoke test passed." -ForegroundColor Green

- name: E2E smoke test teardown (Windows)
  if: always() && runner.os == 'Windows'
  shell: pwsh
  run: |
    $e2eDir = "$env:RUNNER_TEMP\e2e-project"
    if (Test-Path $e2eDir) { cmd /c rmdir /s /q "$e2eDir" 2>&1 | Out-Null }
```

### Full E2E step structure (macOS)

```yaml
- name: E2E smoke test (macOS)
  if: success() && runner.os == 'macOS'
  shell: bash
  run: |
    E2E_DIR="$RUNNER_TEMP/e2e-project"
    rm -rf "$E2E_DIR"
    mkdir -p "$E2E_DIR"
    cd "$E2E_DIR"

    # 1. Link
    bash "$GITHUB_WORKSPACE/scripts/link.sh"

    # 2. Assert symlink and file accessibility
    [ -L ".github/prompts" ] || { echo "ERROR: .github/prompts is not a symlink"; exit 1; }
    [ -f ".github/prompts/cg-setup.prompt.md" ] || { echo "ERROR: cg-setup.prompt.md not accessible"; exit 1; }

    # 3. Idempotency
    bash "$GITHUB_WORKSPACE/scripts/link.sh"

    # 4. Unlink (--yes skips interactive confirmation in CI)
    bash "$GITHUB_WORKSPACE/scripts/unlink.sh" --yes

    # 5. Assert symlink removed
    [ ! -e ".github/prompts" ] || { echo "ERROR: .github/prompts still exists"; exit 1; }

    # 6. Assert .gitignore cleaned up
    if [ -f ".gitignore" ]; then
        grep -q '\.github/prompts/' .gitignore && { echo "ERROR: .gitignore not cleaned"; exit 1; } || true
    fi
    echo "E2E smoke test passed."

- name: E2E smoke test teardown (macOS)
  if: always() && runner.os == 'macOS'
  shell: bash
  run: |
    rm -rf "$RUNNER_TEMP/e2e-project" || true
```

### Key rules

| Rule | Why |
|------|-----|
| Use `& "script.ps1"` not `pwsh -File "script.ps1"` | `pwsh -File` spawns a child process within a `shell: pwsh` step — redundant and harder to debug |
| `if: always()` on teardown | Teardown must run even when the smoke test step fails |
| `if: success() && runner.os == '...'` on the test step | Prevents the E2E step from running (and hanging) when prior Pester failures have already failed the job |
| Expression injection: use `env:` for `github.base_ref` | `DEFAULT_BRANCH="${{ github.base_ref }}"` is flagged by CodeQL; use `env: DEFAULT_BRANCH: ${{ github.base_ref }}` and reference `${DEFAULT_BRANCH}` in shell |

## Prevention

- **Two-level scan rule**: When writing any cleanup code that might touch
  directories with junctions, use the safe 2-level scan pattern instead of
  `Remove-Item -Recurse`:
  ```powershell
  $level1 = Get-ChildItem -Path $dir -Force -ErrorAction SilentlyContinue
  $level2 = $level1 | Where-Object { $_.PSIsContainer -and $_.LinkType -ne 'Junction' } |
            ForEach-Object { Get-ChildItem -Path $_.FullName -Force -ErrorAction SilentlyContinue }
  @($level1) + @($level2) |
      Where-Object { $_ -and $_.LinkType -eq 'Junction' } |
      ForEach-Object { Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue }
  ```
  Then use `cmd /c rmdir /s /q` for the remaining non-junction content.
- Add this to the PR template Security reviewed checklist: "Junction/symlink
  cleanup uses the safe 2-level scan pattern — no `Remove-Item -Recurse` on
  trees that may contain junctions."

## Related

- [`2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md`](../testing-patterns/2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md) — same
  root cause in Pester `$TestDrive` cleanup
- [`2026-05-13-ci-bypass-flag-force-yes-interactive-scripts.md`](../testing-patterns/2026-05-13-ci-bypass-flag-force-yes-interactive-scripts.md) — `-Force`/`--yes`
  flags used in this E2E test
- [`2026-05-13-cross-script-parity-tests-ps1-sh.md`](../testing-patterns/2026-05-13-cross-script-parity-tests-ps1-sh.md) — parity tests that verify
  link/unlink stay in sync across platforms
