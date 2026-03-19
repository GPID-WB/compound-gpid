---
date: 2026-03-19
title: "PowerShell null interpolation silently corrupts pipe-delimited output contracts"
category: "data-quality"
language: "both"
tags: [powershell, null, interpolation, output-contract, api-response, invoke-restmethod, github-api, pipe-delimited]
root-cause: "PowerShell silently interpolates $null as an empty string in double-quoted strings, so missing API response fields produce structurally valid but semantically corrupt output"
severity: "P1"
---

# PowerShell `$null` Interpolation Silently Corrupts Pipe-Delimited Output Contracts

## Problem

A script writes release metadata to `release-result.txt` in the format `CREATED|<id>|<url>`:

```powershell
$response = Invoke-RestMethod ...
"CREATED|$($response.id)|$($response.html_url)" | Set-Content $resultFile
```

If the GitHub API response is missing `id` or `html_url` (schema change, partial error body, unexpected API version), PowerShell silently interpolates `$null` as `""`, producing:

```
CREATED||
CREATED|123|
```

The downstream consumer (a Copilot prompt parsing the file by splitting on `|`) reads these as structurally valid and reports "success" with a blank URL. No error is ever raised.

## Root Cause

PowerShell's string interpolation expands `$null` to an empty string inside double-quoted strings:

```powershell
$x = $null
"value is: $x"    # → "value is: "   (no error, no warning)
"$($x.field)"     # → ""             (property access on $null also returns $null silently)
```

This is by design in PowerShell, but it means accessing a missing property on a `PSCustomObject` (like a deserialized JSON response) produces an empty string rather than an error — even with `$ErrorActionPreference = "Stop"`.

The same pattern applies to any pipe-delimited, CSV, or structured text output where positional fields are derived from object properties.

## Solution

Always guard API response fields before writing to the output contract:

```powershell
if (-not $response.id -or -not $response.html_url) {
    Write-Error "GitHub API response missing expected fields (id, html_url). Raw: $($response | ConvertTo-Json)"
    exit 1
}
"CREATED|$($response.id)|$($response.html_url)" | Set-Content $resultFile
```

Apply the same guard on every path that writes to the output file:

```powershell
# EXISTS path
if ($null -ne $existingRelease) {
    if (-not $existingRelease.id -or -not $existingRelease.html_url) {
        Write-Error "GitHub API response missing expected fields. Raw: $($existingRelease | ConvertTo-Json)"
        exit 1
    }
    "EXISTS|$($existingRelease.id)|$($existingRelease.html_url)" | Set-Content $resultFile
    exit 0
}

# CREATED path
if (-not $response.id -or -not $response.html_url) {
    Write-Error "GitHub API response missing expected fields. Raw: $($response | ConvertTo-Json)"
    exit 1
}
"CREATED|$($response.id)|$($response.html_url)" | Set-Content $resultFile
```

## Prevention

- **At every API response boundary**: verify expected fields exist before interpolating them into structured output.
- **General rule**: `$null` interpolation is not a bug PowerShell will catch for you. Treat it as an explicit validation responsibility.
- **Defensive pattern** — prefer explicit null checks over relying on `$ErrorActionPreference = "Stop"` (which does *not* protect against missing properties):

```powershell
# Instead of:
"$($obj.field)"    # silently empty if $obj.field is $null

# Write:
if (-not $obj.field) { Write-Error "Missing field 'field'"; exit 1 }
"$($obj.field)"
```

- For structured output formats (pipe-delimited, CSV, JSON), validate the full set of required fields in a single guard before writing.

## Related

- [2026-03-19-invoke-restmethod-bare-catch-swallows-non-404-errors.md](../build-errors/2026-03-19-invoke-restmethod-bare-catch-swallows-non-404-errors.md) — Companion fix: narrowing `catch {}` to 404-only so non-404 errors surface immediately rather than falling through to this output path.
