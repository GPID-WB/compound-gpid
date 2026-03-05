---
date: 2026-03-04
title: "git stderr swallowed by 2>&1 redirect into an unused variable"
category: "git-workflows"
language: "both"
tags: [powershell, git, stderr, redirection, exit-code, error-handling]
root-cause: "Assigning `git pull 2>&1` to a variable silences both stdout and stderr; git errors are lost and the script appears to succeed"
severity: "P1"
---

# `git pull 2>&1` Swallows Errors When Assigned to a Variable

## Problem

A script captured git output like this:

```powershell
# WRONG — stderr never reaches the console
$pullOutput = git pull --ff-only 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Error "git pull failed"
}
```

The intent was to capture output so it could be formatted. In practice:

- `2>&1` merges stderr into stdout.
- Assigning the merged stream to `$pullOutput` swallows **both** stdout and stderr
  — nothing is printed to the terminal, not even git's progress/error messages.
- The `$LASTEXITCODE` check fires on failure, but the user sees only the generic
  error message, not git's actual diagnostic (e.g., "Your local changes would be
  overwritten", "refusing to merge unrelated histories").
- When `$pullOutput` is never used again in the script, it is dead code — the
  capture was pointless and the information is discarded.

## Root Cause

In PowerShell, assigning an external command's output to a variable captures
**all output streams that are redirected into the variable's stream**. `2>&1`
redirects stderr to stdout, and the whole merged stream becomes the variable
value, silently removing it from the terminal. If the variable is then discarded,
both streams are lost entirely.

## Solution

Let git write directly to the terminal. Check success with `$LASTEXITCODE`:

```powershell
# CORRECT — git messages appear in the terminal; exit code is still inspectable
git pull --ff-only
if ($LASTEXITCODE -ne 0) {
    Write-Error "git pull failed. See git output above for details."
    return
}
```

If you need both to display output **and** inspect it:

```powershell
# Capture stdout only; stderr still flows to the terminal
$pullOutput = git pull --ff-only
if ($LASTEXITCODE -ne 0) {
    Write-Error "git pull failed"
    return
}
# Now $pullOutput has stdout lines (e.g. to parse the summary)
```

If you need to capture both streams for logging:

```powershell
$pullOutput = git pull --ff-only 2>&1
$pullOutput | Tee-Object -Variable captured   # still prints AND captures
if ($LASTEXITCODE -ne 0) { ... }
```

## Prevention

- **Default rule**: let git (and other CLI tools) write to the terminal unimpeded.
  Only capture output when you have a concrete reason to process it.
- If you assign `cmd 2>&1` to a variable, ensure you **display or log it**;
  otherwise remove the capture.
- Code review checklist: flag `$x = <external-cmd> 2>&1` where `$x` is never
  used — it is always a bug.
- Strongly prefer `$LASTEXITCODE` over parsing output to detect failures.

## Related

- [PowerShell `$$` is not PID](../build-errors/2026-03-04-powershell-dollar-dollar-is-not-pid.md) — sibling P1 fix from the same review session
- [PS5.1 ErrorActionPreference=Stop terminates on git informational stderr](./2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md) — the complementary exception: `2>$null` IS correct for commands that write informational messages to stderr on success
