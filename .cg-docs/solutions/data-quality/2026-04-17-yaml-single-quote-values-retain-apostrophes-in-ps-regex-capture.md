---
date: 2026-04-17
title: "YAML single-quoted values retain literal apostrophes when regex only strips double-quote delimiters"
category: "data-quality"
language: "both"
tags: [powershell, yaml, frontmatter, regex, single-quote, parsing, helpers, r-syntax, copilot-instructions]
root-cause: "Field extraction regexes using '\"?([^\"\r\n]+)\"?' only strip double-quote delimiters; a YAML value quoted with single quotes (e.g. r-syntax: 'data.table-collapse') is captured with the apostrophes intact, producing malformed output"
severity: "P2"
---

# YAML Single-Quoted Values Retain Literal Apostrophes When Regex Only Strips Double-Quote Delimiters

## Problem

`compound-gpid.local.md` uses YAML frontmatter to store configuration. The field
extraction regex in `helpers.ps1` was:

```powershell
if ($fm -match '(?m)^\s*r-syntax:\s*"?([^"\r\n]+)"?\s*$') {
    $rSyntax = $Matches[1].Trim()
}
```

A user who wrote their config with single-quoted values (valid YAML):

```yaml
---
r-syntax: 'data.table-collapse'
---
```

Would get `$rSyntax = "'data.table-collapse'"` — with the apostrophes included.
The generated `copilot-instructions.md` would then contain:

```
R (R dialect: 'data.table-collapse')
```

Copilot receives an unknown dialect string and silently falls back to defaults,
ignoring the user's configured dialect. No error is thrown.

The same issue applies to `language`, `project-type`, `review-depth`, and
`project-name` — all five fields used the double-quote-only regex.

## Root Cause

The regex `"?([^"\r\n]+)"?` uses:
- `"?` — optional double quote at the start
- `[^"\r\n]+` — any chars except double quote or newline
- `"?` — optional double quote at the end

This correctly strips `"data.table-collapse"` → `data.table-collapse`.
It does **not** strip `'data.table-collapse'` → captures `'data.table-collapse'`
(the apostrophes are not `"` characters, so they pass the character class filter
and are included in the capture group).

YAML allows both `"double-quoted"` and `'single-quoted'` scalar values. A user
following YAML conventions could reasonably use either form.

## Solution

Extend the regex to handle both quote styles. In PS5.1, use `\x27` for the hex
escape of a single quote inside a double-quoted string, and `''` to escape a
literal apostrophe inside a single-quoted regex literal:

```powershell
# Five-field extraction — all five fields updated the same way:
if ($fm -match '(?m)^\s*project-name:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$') { ... }
if ($fm -match '(?m)^\s*language:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')     { ... }
if ($fm -match '(?m)^\s*project-type:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$') { ... }
if ($fm -match '(?m)^\s*review-depth:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$') { ... }
if ($fm -match '(?m)^\s*r-syntax:\s*["\x27]?([^"''\r\n]+)["\x27]?\s*$')     { ... }
```

The character class `["\x27]?` matches an optional double or single quote.
The negated class `[^"''\r\n]` excludes both quote types from the captured value
(preventing capture of the closing quote into the value).

Note: `''` inside a single-quoted PS string is a literal apostrophe; `\x27` is the
hex escape for `'` (0x27 in ASCII/Unicode). The mix is required because PS5.1
double-quoted strings interpret `\'` as a literal backslash-apostrophe, not as an
escape sequence.

Alternatively, post-capture stripping is simpler but noisier:

```powershell
$val = $Matches[1].Trim().Trim('"', "'")
```

## Prevention

**YAML regex rule**: when extracting YAML scalar values by regex in PowerShell,
always account for both `"` and `'` quoting styles. The minimal safe pattern for a
single-line scalar is:

```
^\s*<key>:\s*["\x27]?([^"'\r\n]+)["\x27]?\s*$
```

**Alternative**: use a proper YAML parser. `ConvertFrom-Yaml` (requires PS7+) or
the `powershell-yaml` module handle both quote styles correctly. For PS5.1
compatibility, a regex-based approach is necessary, but the regex must handle both
delimiters.

**Test coverage**: add a test that configures each field with single-quoted YAML
values and asserts the captured value does not contain apostrophes.

## Related

- `scripts/helpers.ps1` — `New-CopilotInstructions` function, field extraction block
- `compound-gpid.local.md` — the config file being parsed
- [2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md](../bugs/2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md) — another PS5.1 parsing edge case
