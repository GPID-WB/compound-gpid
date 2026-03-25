---
date: 2026-03-23
title: "Case-insensitive regex silently accepts invalid git tag names"
category: "bugs"
language: "both"
tags: [powershell, regex, git, validation, case-sensitivity, tags, cg-update]
root-cause: "PowerShell's -notmatch operator is case-insensitive by default; git tag names are case-sensitive, so 'V0.2.0' passes validation but fails at git checkout."
severity: "P2"
---

# Case-Insensitive Regex Silently Accepts Invalid Git Tag Names

## Problem

`cg-update V0.2.0` would pass the version validation check and then fail later
at `git checkout V0.2.0` with a confusing "pathspec did not match any file(s)
known to git" error. The user sees no helpful message pointing them back to the
bad input.

## Root Cause

PowerShell's `-notmatch` operator is **case-insensitive by default**. A pattern
like `^v\d+\.\d+\.\d+$` matches both `v0.2.0` and `V0.2.0` when used with
`-notmatch`. Git tag names, however, are case-sensitive: `v0.2.0` and `V0.2.0`
are different refs. The tag `V0.2.0` would not exist on the remote, so the
checkout fails.

The same issue applies to any downstream system that treats identifiers
case-sensitively (git refs, Docker image tags, npm package names).

```powershell
# BUG: case-insensitive -- accepts 'V0.2.0'
if ($Version -notmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') { ... }

# FIX: case-sensitive -- rejects 'V0.2.0' at validation time
if ($Version -cnotmatch '^(latest|v\d+\.\d+\.\d+(\.\d+)?)$') { ... }
```

## Solution

Replace `-notmatch` with `-cnotmatch` (case-sensitive not-match) at every
validation site that guards git tag names. Similarly, use `-cmatch` instead of
`-match` when the match must be case-sensitive.

In `scripts/update.ps1`, both the CLI validation guard and the `.cg-version`
file reader were updated:

```powershell
# CLI argument
if ($Version -and $Version -cnotmatch $VersionAcceptPattern) {
    Write-Error "Invalid version '$Version'. Expected a tag like 'v0.2.0' ..."
    exit 1
}

# .cg-version file content
if (-not $Version -and $versionMode -cnotmatch $VersionAcceptPattern) {
    Write-Error "Malformed .cg-version: '$versionMode' ..."
    exit 1
}
```

## Prevention

**Rule**: Whenever a regex validates a string that will be passed to git (tag,
branch name, commit ref) or any other case-sensitive system, always use the
case-sensitive operator variants:

| Operator | Case variant | Use when |
|----------|------------|----------|
| `-match` | `-cmatch` | Matching git refs, file paths on case-sensitive FS |
| `-notmatch` | `-cnotmatch` | Rejecting invalid git refs |
| `-eq` | `-ceq` | Comparing git tag strings directly |
| `-like` | `-clike` | Glob matching against git ref names |

**Test coverage**: Add an explicit test that a version string with an uppercase
prefix (e.g. `V0.2.0`) is rejected by the validator:

```powershell
It "rejects a version with uppercase V (case-sensitive validation)" {
    ("V0.2.0" -cnotmatch $VersionAcceptPattern) | Should Be $true
}
```

Without this test, `-notmatch` vs `-cnotmatch` is an easy regression to
introduce silently.

## Related

- `bugs/2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md` -- another
  PS 5.1 gotcha where silent failures led to wrong-branch execution
- `tests/update.Tests.ps1` -- "rejects a version with uppercase V" test added
  in round 7 of thorough review
