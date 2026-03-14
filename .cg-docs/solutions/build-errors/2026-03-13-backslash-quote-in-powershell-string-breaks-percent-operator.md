---
date: 2026-03-13
title: "Backslash-escaped quotes in PowerShell double-quoted strings break % operator parsing"
category: "build-errors"
language: "both"
tags: [powershell, string-escaping, backtick, backslash, cmd-wrapper, percent-operator, parse-error]
root-cause: "PowerShell does not recognise \\\" as an escaped quote inside double-quoted strings — the backslash ends the string prematurely, leaving bare % characters that are parsed as the modulus operator"
severity: "P1"
---

# Backslash-Escaped Quotes in PowerShell Double-Quoted Strings Break `%` Operator Parsing

## Problem

`install.ps1` failed at parse time with:

```
At install.ps1:107 char:90
+ ... -ExecutionPolicy Bypass -File \"%~dp0..\scripts\$script.ps1\" %*`r`n"
+                                      ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
You must provide a value expression following the '%' operator.
ParseException: ExpectedValueExpression
```

The script was building `.cmd` wrapper content inside a PowerShell double-quoted string and used
`\"` (backslash-escaped double quotes) to embed literal `"` characters, with `%~dp0` and `%*`
as CMD batch tokens.

## Root Cause

PowerShell does **not** use `\"` as an escape sequence inside double-quoted strings. The backslash
is treated as a literal backslash character, not an escape. This means the `"` after `\"` closes
the string — leaving `%~dp0...` as bare unquoted text that PowerShell attempts to parse as an
expression. When it encounters `%`, it interprets it as the modulus arithmetic operator and expects
a value on both sides, triggering:

```
You must provide a value expression following the '%' operator.
```

PowerShell's escape character inside double-quoted strings is the **backtick** (`` ` ``), not the
backslash.

## Solution

Replace `\"` with `` `" `` (backtick-escaped double quote):

```powershell
# WRONG — backslash does not escape quotes in PowerShell
$content = "@echo off`r`npowershell.exe -File \"%~dp0..\scripts\$script.ps1\" %*`r`n"

# CORRECT — use backtick to escape the embedded double quotes
$content = "@echo off`r`npowershell.exe -File `"%~dp0..\scripts\$script.ps1`" %*`r`n"
```

The `%~dp0` and `%*` tokens are CMD batch syntax and do not need escaping — PowerShell does not
interpret `%` as an operator in the middle of a string value; the error only occurs when the
premature string termination exposes them as bare tokens in expression context.

## Prevention

- **In PowerShell double-quoted strings**: always use `` ` `` (backtick) to escape embedded `"`, never `\"`
- **Backslash** in PowerShell strings is a literal path separator, not an escape character
- **Quick check**: if a string contains `%~dp0`, `%*`, or other CMD tokens and the script throws
  `ExpectedValueExpression`, look for `\"` pairs — replace with `` `" ``

| Context | Escape for `"` |
|---------|---------------|
| PowerShell double-quoted string | `` `" `` |
| PowerShell single-quoted string | `''` (double the single quote) |
| CMD / batch file | `\"` or `""` |

## Related

- [`.cg-docs/solutions/build-errors/2026-03-04-powershell-dollar-dollar-is-not-pid.md`](./2026-03-04-powershell-dollar-dollar-is-not-pid.md) — another PowerShell string/operator gotcha
- [PowerShell about_Quoting_Rules](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/about/about_quoting_rules)
