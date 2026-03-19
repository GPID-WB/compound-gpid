---
date: 2026-03-19
title: "Bare catch {} on Invoke-RestMethod swallows non-404 HTTP errors"
category: "build-errors"
language: "both"
tags: [powershell, invoke-restmethod, github-api, error-handling, catch, http, 404, bearer-token]
root-cause: "An empty catch block treats all HTTP errors identically — 401, 403, 429, 500, and network failures all silently fall through as if the resource simply didn't exist"
severity: "P1"
---

# Bare `catch {}` on `Invoke-RestMethod` Swallows Non-404 HTTP Errors

## Problem

A script checking for an existing GitHub Release before creating one used an empty `catch {}` around the `GET /releases/tags/<tag>` call:

```powershell
try {
    $existingRelease = Invoke-RestMethod -Uri $checkUrl -Headers $headers
} catch {}
```

The intent was: "if the release doesn't exist (404), proceed to create it." But the bare `catch {}` also swallowed 401 (bad token), 403 (insufficient scope), 429 (rate limit), 500 (server error), and network timeouts — all of which left `$existingRelease` as `$null`. The script would then fall through to the POST (create) path and fail there with a less informative error.

## Root Cause

PowerShell's `Invoke-RestMethod` throws a terminating error for any non-2xx HTTP response when `$ErrorActionPreference = "Stop"`. A bare `catch {}` catches *all* of these uniformly. Only a 404 is semantically "the resource doesn't exist yet" — everything else is an unexpected failure that should surface immediately.

This is the inverse of the issue documented in `2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md`, where stderr from git should be suppressed. For structured HTTP APIs, error codes carry meaning and must be inspected, not silenced.

## Solution

Inspect the HTTP status code inside the catch block and re-throw anything that isn't a 404:

```powershell
$existingRelease = $null
try {
    $existingRelease = Invoke-RestMethod -Uri $checkUrl -Headers $headers
} catch {
    # Only a 404 means "release doesn't exist" — re-throw all other HTTP errors
    $status = $_.Exception.Response?.StatusCode.value__
    if ($null -eq $status -or $status -ne 404) { throw }
}
```

The `?.` null-conditional operator handles cases where `Response` is `$null` (e.g. network timeout, DNS failure) — by treating those as non-404 errors and re-throwing.

### GitHub API authorization header

Related: while fixing this, also updated the `Authorization` header to use `Bearer` instead of `token`:

```powershell
# Correct (current GitHub API docs)
Authorization = "Bearer $token"

# Deprecated (still works but may be removed)
Authorization = "token $token"
```

### Token extraction safety

When parsing `git credential fill` output, use `Select-Object -First 1` to guard against multi-account GCM configurations that could return multiple `password=` lines:

```powershell
$token = ($credLines | Where-Object { $_ -match "^password=" } | Select-Object -First 1) -replace "^password=", ""
```

Without `-First 1`, multiple matches produce an array; string interpolation yields `"Bearer val1 val2"` — an invalid token that passes the `IsNullOrEmpty` guard.

## Prevention

- **Never use bare `catch {}`** for `Invoke-RestMethod` calls. Always inspect `$_.Exception.Response?.StatusCode.value__` and only suppress the specific expected status codes.
- **Use `Bearer` for GitHub API** auth headers, not `token`.
- **Pipe `git credential fill` through `Select-Object -First 1`** before using the token.

```powershell
# Pattern: catch only what you expect
try {
    $result = Invoke-RestMethod -Uri $url -Headers $headers
} catch {
    $status = $_.Exception.Response?.StatusCode.value__
    if ($null -eq $status -or $status -ne 404) { throw }
    # $result remains $null — caller checks for null to detect "not found"
}
```

## Related

- [2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md](../git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md) — Complementary rule: **git native commands** write informational stderr and _should_ use `2>$null` or `2>&1`. HTTP API errors carry semantic meaning and should **not** be suppressed.
- [2026-03-04-git-pull-stderr-swallowed-by-redirect.md](../git-workflows/2026-03-04-git-pull-stderr-swallowed-by-redirect.md) — Pattern: don't capture stderr into an unused variable.
- [2026-03-19-api-response-null-fields-corrupt-output-contract.md](../data-quality/2026-03-19-api-response-null-fields-corrupt-output-contract.md) — Companion fix: guard response fields before writing the output contract.
