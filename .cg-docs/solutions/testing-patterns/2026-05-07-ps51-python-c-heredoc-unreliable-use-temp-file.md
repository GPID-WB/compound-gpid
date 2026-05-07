---
date: 2026-05-07
title: "PS 5.1 `python -c` here-string unreliable — write temp .py file for Pester Python tests"
category: "testing-patterns"
language: "both"
tags: [pester, powershell, ps51, python, here-string, temp-file, testing]
root-cause: "PowerShell here-strings interpolate $ and backtick; CRLF injection breaks Python's -c argument parser on PS 5.1 Windows; the string is shell-quoted before reaching python"
severity: "P2"
fix-confirmed: "yes"
reviewed-in: ".cg-docs/reviews/2026-05-07-python-utility-layer-cg-index-review.md"
---

# PS 5.1 `python -c` Here-String Unreliable — Use Temp `.py` File for Pester Python Tests

## Problem

Passing multi-line Python code to `python -c` via a PowerShell here-string
(`@"..."@`) in Pester tests produces unreliable behaviour on PS 5.1 / Windows:

```powershell
# BROKEN — do not use this pattern
$result = python -c @"
import json, sys
data = json.load(sys.stdin)
print(data['title'])
"@
```

Symptoms:
- Python receives garbled indentation (CRLF injected mid-string)
- Variable expansion: `$data` becomes an empty PS variable before Python sees it
- Backtick escapes (`\`n`) interact with PS escape rules
- `SyntaxError` or silent wrong output, exit code 0

The failure mode is especially insidious: the test may pass on the CI machine
and fail locally (or vice versa) depending on the PS version and locale.

## Root Cause

1. **Interpolation**: PS here-strings are interpolated by default. Any `$name`
   inside `@"..."@` is expanded to the PowerShell variable value (usually empty
   string) before the content reaches Python. Backtick-escape sequences
   (`\`n`, `\`t`) are also consumed by PowerShell.

2. **CRLF on Windows**: PS 5.1 on Windows injects `\r\n` line endings into
   here-strings. Python's `-c` argument parser is sensitive to `\r` in
   multi-line strings, producing `SyntaxError: unexpected character after line
   continuation character` on some statements.

3. **Shell quoting**: The entire here-string is passed as a single shell
   argument. Complex Python (parentheses, quotes, brackets) interacts with
   PowerShell's argument-binder in non-obvious ways.

## Solution

Write the Python code to a temp file, invoke Python against the file, and
clean up. Use a helper function so the pattern is consistent across all tests:

```powershell
function Invoke-PyHelper {
    param([string[]]$Lines)
    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    # LF-only — Python import machinery is more reliable with LF on Windows
    ($Lines -join "`n") | Set-Content $tmp -Encoding UTF8 -NoNewline
    try   { & python $tmp 2>&1 }
    finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
}

# Usage:
$result = Invoke-PyHelper @(
    'import json, sys',
    'with open(sys.argv[1]) as f: data = json.load(f)',
    'print(data["title"])'
)
```

For tests that need to pass arguments or a second script, add an `Invoke-PyHelper2`:

```powershell
function Invoke-PyHelper2 {
    param([string[]]$Lines, [string[]]$Args = @())
    $tmp = [System.IO.Path]::GetTempFileName() + ".py"
    ($Lines -join "`n") | Set-Content $tmp -Encoding UTF8 -NoNewline
    try   { & python $tmp @Args 2>&1 }
    finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
}
```

Key details:
- Use `` `n `` (LF) not `` `r`n `` (CRLF) for the join — Python is more reliable
  with LF-only temp files on Windows.
- `Set-Content -NoNewline` prevents PS adding an extra trailing newline.
- `-Encoding UTF8` avoids Windows-1252 encoding issues with non-ASCII strings.

## Prevention

Never use `python -c @"..."@` in Pester test files. Always define `Invoke-PyHelper`
(and `Invoke-PyHelper2` if needed) at the top of the test script and route all
Python invocations through it.

The same rule applies to `python -c "..."` with escaped single-line strings —
these break even more easily on PS 5.1 due to quoting rules.

## Related

- `.cg-docs/solutions/bugs/2026-03-23-ps51-utf8-bom-em-dash-corrupts-ast-silently.md` — PS 5.1 encoding traps with non-ASCII content
- `.cg-docs/solutions/bugs/2026-04-17-ps51-get-content-default-encoding-breaks-equality-check.md` — `Get-Content` default encoding on PS 5.1
- `.cg-docs/solutions/testing-patterns/2026-03-19-testing-powershell-switch-parameters.md` — PS 5.1 Pester patterns
