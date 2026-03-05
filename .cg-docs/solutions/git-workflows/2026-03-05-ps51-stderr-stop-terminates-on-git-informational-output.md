---
date: 2026-03-05
title: "PS5.1 ErrorActionPreference=Stop promotes git informational stderr into terminating errors"
category: "git-workflows"
language: "both"
tags: [powershell, powershell-5.1, git, stderr, ErrorActionPreference, 2>null, git-checkout]
root-cause: "PowerShell 5.1 with ErrorActionPreference=Stop treats any stderr output from a native command as a terminating error, even when the command succeeds"
severity: "P1"
---

# PS5.1 `ErrorActionPreference=Stop` Terminates on Git Informational stderr

## Problem

After removing `2>$null` from `git checkout .` (following the general rule "don't suppress stderr"),
the script started failing with:

```
Update failed: Updated 0 paths from the index
```

`git checkout .` was succeeding — "Updated N paths from the index" is its normal
stdout/stderr output — but the script was catching it as a fatal error. Running
`cg-update` from any project directory would immediately abort.

## Root Cause

PowerShell 5.1 with `$ErrorActionPreference = "Stop"` promotes **any** stderr
output from a native (non-PowerShell) command into a terminating `ErrorRecord`.
This is caught by surrounding `try/catch` blocks, which are then reported as
script failures.

`git checkout .` writes "Updated N paths from the index" to stderr by design —
it is purely informational, not an error. But PS5.1 cannot distinguish
informational stderr from error stderr. With `$ErrorActionPreference = "Stop"`,
any native stderr becomes fatal.

This does **not** affect PowerShell 7+, which handles native command stderr
differently.

## Solution

`2>$null` alone is **not sufficient** in all PS5.1 host configurations — some
hosts still promote native stderr to a terminating error even with the redirect.
The bullet-proof fix is to combine `2>$null` with a `try/catch`:

```powershell
# CORRECT — immune to PS5.1 stderr-to-error promotion in all host configurations
try { git checkout . 2>$null } catch { <# informational stderr — ignore #> }
if ($LASTEXITCODE -ne 0) {
    Write-Warning "git checkout . returned exit code $LASTEXITCODE - continuing anyway"
}
```

The `try/catch` ensures that even if PS5.1 promotes the stderr to a terminating
error, it is caught and discarded at the local level rather than propagating to
the outer `catch` block. `$LASTEXITCODE` is still checked immediately after for
real failures (non-zero exit code).

## Prevention

The rule "don't swallow stderr" has an important exception in PS5.1 scripts:

| Situation | Correct approach |
|-----------|-----------------|
| Command succeeds silently (no informational stderr) | No redirect needed |
| Command writes informational stderr on success + you only care about exit code | `try { cmd 2>$null } catch {}` + `$LASTEXITCODE` check |
| Command failure diagnostics matter to the user | No redirect — let git speak |
| Capturing output for processing | `$x = cmd 2>&1` — but always display or use `$x` |

**Checklist for native commands under `$ErrorActionPreference = "Stop"`:**
1. Does this command write to stderr on success? (Check the git man page or test manually)
2. If yes: add `2>$null` AND a `$LASTEXITCODE` check immediately after.
3. If no: leave unredirected; rely on `$LASTEXITCODE` or the terminating error itself.

## Bootstrapping caveat

If the broken version (without `2>$null`) is already deployed in the global clone,
the script will fail before `git pull` can retrieve the fix. Recovery requires
manually updating the global clone once:

```powershell
git -C "$env:USERPROFILE\.compound-gpid" checkout . 2>$null
git -C "$env:USERPROFILE\.compound-gpid" pull --ff-only
```

After that, `cg-update` works normally from all projects.

## Related

- [git stderr swallowed by 2>&1 redirect](./2026-03-04-git-pull-stderr-swallowed-by-redirect.md) — the complementary rule: don't suppress stderr for commands where diagnostics matter
