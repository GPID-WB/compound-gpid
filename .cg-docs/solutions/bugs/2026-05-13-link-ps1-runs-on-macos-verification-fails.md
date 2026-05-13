---
date: 2026-05-13
title: "link.ps1 runs on macOS via pwsh, Step 6 verification fails due to backslash path separator"
category: "bugs"
type: "bug"
language: "both"
tags: [cg-link, link.ps1, link.sh, macos, symlinks, junctions, platform-guard, path-separator, verification]
root-cause: "link.ps1 had no Windows platform guard; Step 6 used a backslash path separator ('prompts\\cg-setup.prompt.md') that is invalid on macOS, causing Test-Path to return false and emit a spurious verification warning even though symlinks were created correctly"
severity: "P2"
test-written: "yes"
fix-confirmed: "yes"
---

# link.ps1 runs on macOS via pwsh, Step 6 verification fails due to backslash path separator

## Symptom

After running `cg-link` on macOS the terminal shows:

```
WARNING: Verification failed - prompts not visible at expected path:
  /Users/.../compound-research/.github/prompts/cg-setup.prompt.md
```

Despite this warning, the output also says `prompts/ - linked`, `skills/ - linked`, etc.
Inspecting `.github/` afterwards shows only `copilot-instructions.md` — no symlinks — when
`link.ps1` was the script that ran, because junction creation on macOS via `pwsh` silently
fails or leaves no usable directory.

## Root Cause

Two compounding issues:

1. **No platform guard in `link.ps1`**: `link.ps1` is a Windows-only script (it uses
   `New-Item -ItemType Junction`). If a user has `pwsh` installed and invokes `link.ps1`
   directly (or via a stale wrapper), it runs on macOS without any error. Junctions are
   a Windows NTFS feature; the behaviour on macOS is undefined and typically silently
   wrong.

2. **Backslash path separator in Step 6**: `link.ps1` Step 6 contained:
   ```powershell
   $checkPath = Join-Path $TargetGithubDir "prompts\cg-setup.prompt.md"
   ```
   On macOS, `\` is not a path separator — it is a valid filename character. So
   `Join-Path` resolves this to a path ending in `prompts\cg-setup.prompt.md` (a single
   path component with a backslash in the name), which never exists. `Test-Path` returns
   `$false` and the warning fires even when the symlinks are perfectly healthy.

`link.sh` Step 6 also had a weaker check — it only tested `-d $dir` (directory exists)
rather than checking a specific file through the symlink, so it could not catch the case
where the symlink target was mounted but individual files were inaccessible.

## Reproduction Test

Two tests were written:

**`tests/bash-scripts.Tests.ps1`** — inside `Describe "link.sh - script structure"`:
```powershell
It "Step 6 verification checks file accessibility not just directory existence" {
    # Regression: link.sh Step 6 only checked -d (directory exists), which passes
    # even when the symlink target is on cloud storage with inaccessible files.
    # Fix: check that cg-setup.prompt.md is reachable through the prompts symlink.
    $content | Should -Match 'cg-setup\.prompt\.md'
}
```

**`tests/link.Tests.ps1`** — new `Describe "link.ps1 - Windows platform guard"` block:
```powershell
It "contains a Windows platform check to prevent accidental use on macOS/Linux" {
    $linkPs1Content | Should -Match 'IsWindows|Windows_NT'
}
It "directs non-Windows users to link.sh" {
    $linkPs1Content | Should -Match 'link\.sh'
}
```

Both tests failed on the unfixed code.

## Fix

### `scripts/link.ps1` — add platform guard at top

```powershell
# --- Platform guard: Windows only ---
$onWindows = ($IsWindows -eq $true -or $env:OS -eq "Windows_NT")
if (-not $onWindows) {
    Write-Error @"
link.ps1 is Windows-only (it uses directory junctions).
On macOS/Linux, use link.sh instead:
  cg-link
(which calls scripts/link.sh automatically via the bash wrapper in bin/)
"@
    exit 1
}
```

### `scripts/link.ps1` — fix Step 6 path separator

```powershell
# Before (broken on macOS):
$checkPath = Join-Path $TargetGithubDir "prompts\cg-setup.prompt.md"

# After (two-argument form, platform-safe):
$checkPath = Join-Path $TargetGithubDir "prompts" "cg-setup.prompt.md"
```

### `scripts/link.sh` — strengthen Step 6 to check file, not just directory

```bash
# Before: checked -d for each managed dir (directory existence only)
# After: checks a specific known file through the prompts symlink
VERIFY_CHECK="$TARGET_GITHUB_DIR/prompts/cg-setup.prompt.md"
if [[ ! -f "$VERIFY_CHECK" ]]; then
    print_warn "Verification failed - prompts not visible at expected path: $VERIFY_CHECK"
else
    print_gray "Symlinks verified."
fi
```

## Lessons Learned

- **`Join-Path` with embedded backslashes is not cross-platform.** Use the multi-argument
  form `Join-Path $a "dir" "file.ext"` rather than `Join-Path $a "dir\file.ext"` — the
  two-argument form with a backslash literal is Windows-only even inside PowerShell.
- **Scripts that use Windows-only filesystem features (`Junction`, `mklink`) must have
  a platform guard at the very top.** Without one, the script silently produces wrong
  results on macOS/Linux, which is harder to debug than an upfront error message.
- **Verification steps should check a specific file, not just a directory.** A directory
  check passes even when the symlink target is present but the contents are inaccessible
  (e.g. cloud-mounted volumes). File-level checks are more reliable sentinels.

## Related

- `.cg-docs/solutions/environment-issues/2026-05-13-join-path-backslash-not-cross-platform.md` — general pattern: why `Join-Path $base "dir\file"` is Windows-only and the cross-platform fix
