---
date: 2026-03-23
title: "PS 5.1: BOM-less UTF-8 em-dash silently corrupts AST, causing wrong if/else pairing"
category: "bugs"
language: "both"
tags: [powershell, ps51, encoding, utf8, bom, em-dash, ast, if-else, windows-1252, control-flow]
root-cause: "PS 5.1 reads BOM-less UTF-8 files as Windows-1252; the em-dash (U+2014, UTF-8 bytes E2 80 94) byte 0x94 maps to RIGHT DOUBLE QUOTATION MARK, which PowerShell treats as a string delimiter -- silently closing block-comments and strings prematurely, causing if/else blocks to pair with the wrong braces"
severity: "P1"
---

# PS 5.1: BOM-less UTF-8 Em-Dash Silently Corrupts AST, Causing Wrong if/else Pairing

## Problem

`cg-update` was always entering the pinned-mode branch even when `.cg-version`
contained `"latest"`. No error was thrown. The output was coherent (e.g. "Checking
out latest..." followed by `Release 'latest' not found`) -- it looked like a logic
error, not a parse error.

The relevant code:

```powershell
# scripts/update.ps1 (simplified)
if ($versionMode -eq "latest") {
    # latest mode: git pull --ff-only
    ...
} else {
    # pinned mode: git checkout <tag>
    ...
}
```

Despite `$versionMode` being `"latest"`, execution always entered the `else` branch.

## Root Cause

PowerShell 5.1 (the Windows built-in `powershell.exe`) reads script files using the
**system ANSI code page** when no BOM is present. On all English-locale Windows
machines this is **Windows-1252**.

The em-dash character (U+2014) is encoded in UTF-8 as three bytes: `E2 80 94`.
When read as Windows-1252, byte `0x94` maps to the **RIGHT DOUBLE QUOTATION MARK**
(`\u201D`). PowerShell recognises curly/smart quotes as string delimiters:

```
UTF-8 bytes:  E2  80  94
Win-1252:     â   €   "   ← 0x94 = RIGHT DOUBLE QUOTATION MARK
```

In update.ps1, every `try { ... } catch { <# informational stderr -- ignore #> }`
block contained an em-dash inside the block-comment. When PS 5.1 re-read the byte
`0x94` as `"`, it **terminated the comment string prematurely**, then saw the
remaining text as code. This corrupted the brace-matching in the AST.

### Observed AST misparse (before fix)

```
IF L105-L260 cond=[$List.IsPresent] ELSE L215-L260   # should end at L139
IF L109-L171 cond=[$LASTEXITCODE -ne 0] no-else       # should end at L111
```

The `if ($List.IsPresent)` block swallowed the entire rest of the try-block. The
`if ($versionMode -eq "latest") { ... } else { ... }` at L148 was consumed as
part of the `--list` handler's body, so it never executed as a top-level branch.
The parser paired the `else` keyword at L215 with `$List.IsPresent`'s if-block,
not with the `$versionMode` if-block.

**No parse error was reported.** PS 5.1 silently accepted the corrupted AST.

### Why this is especially dangerous

- The bug produces no error output -- the script runs cleanly but takes the
  wrong path.
- `Write-Host` output looks plausible ("Checking out latest..."), masking the
  wrong branch.
- The trigger is any em-dash **anywhere in a comment or string** in a BOM-less
  UTF-8 file. One character corrupts the entire file's control flow.
- AST analysis confirmed the misparse:
  ```powershell
  # Run from a CLM-trusted path (e.g. C:\WBG\)
  $ast = [System.Management.Automation.Language.Parser]::ParseFile('path\to\update.ps1', [ref]$null, [ref]$null)
  $ifs = $ast.FindAll({ $args[0] -is [System.Management.Automation.Language.IfStatementAst] }, $true)
  foreach ($i in $ifs) {
      Write-Output "IF L$($i.Extent.StartLineNumber)-L$($i.Extent.EndLineNumber)"
  }
  ```

## Solution

Replace all non-ASCII characters in every production `.ps1` file with ASCII
equivalents:

| Replace | With |
|---------|------|
| `—` (U+2014 em-dash) | `--` |
| `–` (U+2013 en-dash) | `-` |
| `→` (U+2192 right arrow) | `->` |
| `"` `"` (curly quotes) | `"` |
| `'` `'` (curly apostrophes) | `'` |

After replacement, verify with:

```powershell
Get-ChildItem -Recurse -Filter "*.ps1" | Select-String -Pattern "[^\x00-\x7F]"
# Should return no matches
```

Confirm the AST is now correct:

```powershell
$ast = [System.Management.Automation.Language.Parser]::ParseFile('scripts\update.ps1', [ref]$null, [ref]$null)
$ifs = $ast.FindAll({ $args[0] -is [System.Management.Automation.Language.IfStatementAst] }, $true)
foreach ($i in $ifs) {
    $cond = $i.Clauses[0].Item1.Extent.Text
    Write-Output "IF L$($i.Extent.StartLineNumber)-L$($i.Extent.EndLineNumber) [$cond]"
}
```

## Prevention

1. **Keep all `.ps1` files pure ASCII.** Use `--` for em-dash, `->` for arrows.
   Never use smart/curly quotes or typographic punctuation.

2. **Run the PS 5.1 compat Pester tests** before committing:
   ```powershell
   # From a CLM-trusted path (C:\WBG\ on this machine)
   $env:CG_TEST_ROOT = '<repo-root>'
   Invoke-Pester '<trusted-path>\ps51-compat.Tests.ps1'
   ```
   The test file `tests/ps51-compat.Tests.ps1` scans all production scripts for:
   - Non-ASCII characters
   - `$var = if()` patterns (PS 7+ only)

3. **When in doubt, add a UTF-8 BOM.** A BOM (bytes `EF BB BF` at file start)
   forces PS 5.1 to read the file as UTF-8 correctly. However, ASCII-only files
   are simpler and more portable.

4. **Use AST analysis to detect silent misparses** for any complex PS 5.1 script.
   The parser never reports an error -- you must inspect the AST directly.

5. **Note on CLM**: `[System.Management.Automation.Language.Parser]` calls are
   blocked in Constrained Language Mode. Run AST analysis from a CLM-trusted path
   (e.g. `C:\WBG\`) via a script file, not inline via `-Command`.

## Related

- [PS 5.1 stderr with ErrorActionPreference=Stop terminates on git output](../git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md) -- another PS 5.1 silent failure mode
- [Get-Item .Target is string[] in PowerShell 5.1](../build-errors/2026-03-04-get-item-target-is-string-array.md) -- another PS 5.1 surprise vs PS 7+
- [Pester 3.4 vs Pester 5 compatibility](../testing-patterns/2026-03-04-pester-3-vs-5-windows-compatibility.md) -- notes em-dash causes lexer errors; this document covers the silent AST corruption variant
- [PS 5.1 ConvertFrom-Json single-element array coercion](./2026-03-30-ps51-convertfrom-json-single-element-array-coercion.md) -- another PS 5.1 silent behaviour difference: single-element JSON arrays deserialise to a bare PSCustomObject
- Commits: `da17d82` (replace non-ASCII chars), `1fe5017` (add Pester guard tests)
