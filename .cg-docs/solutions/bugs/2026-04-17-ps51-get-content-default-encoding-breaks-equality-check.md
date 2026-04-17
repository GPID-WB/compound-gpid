---
date: 2026-04-17
title: "PS5.1 Get-Content default encoding (Windows-1252) breaks equality check when file was written with UTF-8"
category: "bugs"
language: "both"
tags: [powershell, ps51, encoding, utf8, windows-1252, get-content, set-content, equality-check, idempotency, copilot-instructions, link]
root-cause: "Get-Content without -Encoding UTF8 on PS5.1 uses Windows-1252 (system ANSI), so reading a UTF-8 file and comparing to a string written with Set-Content -Encoding UTF8 always fails the equality check even when content is identical"
severity: "P2"
---

# PS5.1 `Get-Content` Default Encoding Breaks Equality Check When File Was Written with UTF-8

## Problem

`link.ps1` reads the existing `copilot-instructions.md` to compare it with
freshly generated content — skipping the write if nothing changed (idempotency):

```powershell
$existingContent = Get-Content $CopilotInstructionsDest -Raw -ErrorAction SilentlyContinue
...
if ($generated -ne $existingContent) {
    Set-Content -Path $CopilotInstructionsDest -Value $generated -Encoding UTF8
    Write-Host "  copilot-instructions.md - generated"
} else {
    Write-Host "  copilot-instructions.md - up to date"
}
```

**Symptom**: `cg-link` always reported "generated" and rewrote the file on every
run, even when the template and config had not changed. The "up to date" branch
was never reached.

## Root Cause

PowerShell 5.1 `Get-Content` uses the **system ANSI code page** (Windows-1252
on English-locale Windows) when no `-Encoding` parameter is specified.

`Set-Content -Encoding UTF8` writes BOM-less UTF-8.

When the file is then read back without `-Encoding UTF8`, PS5.1 decodes the bytes
as Windows-1252. For any file containing ASCII-only content, the two encodings
produce identical byte sequences and the comparison succeeds. However, the
generated template often includes non-ASCII characters (smart quotes, arrows,
or em-dashes from the skill documentation it embeds), causing the decoded
strings to differ from the in-memory `$generated` value — so `$generated -ne
$existingContent` is always `$true`.

Even on pure-ASCII files, this is a latent risk: if anyone ever adds a non-ASCII
character to the template, the equality check silently breaks without any error.

This is a different manifestation of the same PS5.1 encoding hazard documented
in `2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md` — that one was
about *reading script files*, this one is about *reading data files for comparison*.

## Solution

Always pair `-Encoding UTF8` on both the read and the write:

```powershell
# Read with explicit encoding to match the write encoding
$existingContent = Get-Content $CopilotInstructionsDest -Raw -Encoding UTF8 -ErrorAction SilentlyContinue
...
Set-Content -Path $CopilotInstructionsDest -Value $generated -Encoding UTF8
```

`Update-ManagedInstructionsFile` in `helpers.ps1` was already using `-Encoding UTF8`
on both sides — only the inline Step 4 block in `link.ps1` was missing it.

## Prevention

**PS5.1 encoding rule**: every `Get-Content` and `Set-Content` call that handles
text files must specify `-Encoding UTF8` explicitly. Never rely on the default.

Apply this rule in code review whenever `Get-Content ... -Raw` appears without an
explicit `-Encoding` argument.

**Idempotency test pattern**: any equality-check-before-write pattern should be
covered by a test that:
1. Writes the file once
2. Calls the function again with identical inputs
3. Asserts the return value is `"up-to-date"` (not `"refreshed"`)
4. Asserts the file's `LastWriteTime` is unchanged

Without this test, the encoding mismatch bug is invisible until runtime.

## Related

- [2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md](2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md) — PS5.1 reads script files as Windows-1252, corrupting AST (related PS5.1 encoding family)
- `scripts/link.ps1` Step 4 block — where the fix was applied
- `scripts/helpers.ps1` `Update-ManagedInstructionsFile` — correctly uses `-Encoding UTF8` on both sides
