---
date: 2026-05-22
title: "Test that reimplements logic with correct code masks bugs in the actual code"
category: "testing-patterns"
language: "Python"
tags: [testing, false-positive, reimplementation, integration-test, bash, pester, python, regex]
root-cause: "Test creates a standalone reimplementation of the function under test using correct code, so it passes even when the actual implementation is broken"
severity: "P1"
---

# Test that reimplements logic with correct code masks bugs in the actual code

## Problem

`bash-scripts.Tests.ps1` had a test for the modules-substitution logic in `update.sh`
that consistently passed — even though `update.sh`'s Python regex was broken and silently
returned empty string for any config value containing the letters `r` or `n` (including
`research`, `r-syntax`, `standard`, `project-name`).

The P0 regex bug in `update.sh` survived a complete Phase 1–8 development and review cycle
undetected because the test gave a green signal for the very code path that was broken.

## Root Cause

The test created a **standalone Python script** with the CORRECT regex pattern and tested
that. The actual `update.sh` code had the BROKEN pattern. The two implementations were
independent — the test never called the actual code.

```powershell
# ❌ BUGGY TEST PATTERN: tests a hand-written reimplementation, not the actual code
$tmpPy = Join-Path $tmpDir "extractor.py"
@(
    'def extract(path, key):',
    '    pat = "(?m)^\\s*" + re.escape(key) + ":\\s*[\"\\x27]?([^\"\\x27\\r\\n]+)[\"\\x27]?\\s*$"',
    # ↑ This standalone version used \x27/\r\n — CORRECT — while update.sh had \\r\\n — BROKEN
    ...
) | Set-Content $tmpPy
$result = & python3 $tmpPy $localMd 'modules'
$result | Should -Be 'research'  # passes! but tests the wrong code
```

Meanwhile `update.sh` (via the inline `generate_copilot_instructions` function) contained:

```python
# BROKEN: \\r excludes the letter r; \\n excludes the letter n
pattern = r'(?m)^\s*' + re.escape(key) + r':\s*["\']?([^"\'\\r\\n]+)["\']?\s*$'
```

The test passed because it was correct about what its own standalone implementation would
do — but it proved nothing about `update.sh`'s behavior.

## Solution

Replace the reimplementation test with an **integration test** that calls the ACTUAL
function via the production entry point:

```powershell
# ✓ CORRECT PATTERN: sources the actual helpers.sh and calls the real function
$bashRunner = Join-Path $tmpDir "runner.sh"
@(
    '#!/usr/bin/env bash',
    'print_error() { echo "ERROR: $1" >&2; }',
    ". `"$helpersSh`"",
    "generate_copilot_instructions `"$templateFile`" `"$tmpDir`" `"MARKER`""
) | Set-Content $bashRunner -Encoding UTF8
$output = & bash $bashRunner 2>&1
$outputStr = $output -join "`n"
$outputStr | Should -Match 'Active Modules: research'
```

The integration test:
1. Sources `helpers.sh` (the actual production code)
2. Calls `generate_copilot_instructions` (the actual function)
3. Checks the OUTPUT — not intermediate extraction state
4. Would have caught P0.1 immediately on introduction

## Prevention

**Rule: integration tests must call the actual code path, not a hand-written
reimplementation.**

Symptoms of a reimplementation test:
- The test creates its own Python/shell/SQL/regex logic instead of calling the function under test
- The test passes trivially because the reimplementation happens to be correct
- Changing the actual code does NOT change the test result — the test is decoupled from production behavior

Pattern to apply: test at the function boundary or higher — pass real input, call the real
function, assert the real output.

**Secondary rule: if the production function is too difficult to call directly from tests,
that is an architecture smell.** The underlying fix was to extract `generate_copilot_instructions`
to `scripts/helpers.sh` so it could be sourced and called directly from a Pester bash
runner. The extraction (DRY refactor) was justified by testability, not just code reuse.

**Pester 4 note**: `$array | Should -Match 'pattern'` tests ALL elements — if any element
does not match, the assertion fails. When testing that an array of output lines contains
a match, join first: `$outputStr = $output -join "\`n"`, then `$outputStr | Should -Match`.

## Related

- `.cg-docs/solutions/bugs/2026-05-14-python-regex-raw-string-double-backslash-excludes-letters.md` — the P0 regex bug this test was supposed to catch
- `.cg-docs/solutions/bugs/2026-05-22-bash-heredoc-multiline-compound-command-invalid-syntax.md` — co-discovered during the same fix session
- Fix commit: `57dad18` — "fix(update): extract shared helpers.sh; fix extract_fm_value regex"
