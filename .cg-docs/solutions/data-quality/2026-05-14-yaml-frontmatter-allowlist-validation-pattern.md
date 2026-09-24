---
date: 2026-05-14
title: "YAML frontmatter allowlist validation pattern for module/config fields"
category: "data-quality"
language: "both"
tags: [yaml, frontmatter, validation, allowlist, modules, configuration, powershell, python]
root-cause: "Config fields parsed from YAML frontmatter accepted any string silently, including invalid values and YAML list notation, masking misconfiguration"
severity: "P2"
---

# YAML frontmatter allowlist validation pattern for module/config fields

## Problem

`scripts/helpers.ps1` and `scripts/link.sh` both extracted `modules:` from
`compound-gpid.local.md` and passed any string silently downstream. An invalid value
like `modules: banana` would fall through to template substitution, producing
`**Modules**: banana` in the generated `copilot-instructions.md` with no error.

Similarly, YAML list notation (`modules: [engineering, research]` or block sequence) would
either parse to a bracketed string `[engineering, research]` or fall through to the default
`engineering`, with no indication that the format was wrong.

## Root Cause

The parsers only validated that a value existed (falling back to default if empty). They
did not validate that the value was from the allowed vocabulary.

This class of bug is common in frontmatter-driven configuration: the parser silently accepts
garbage, the garbage propagates to downstream artifacts, and the failure surface is distant
from the root cause.

## Solution

After extracting any constrained config field, validate immediately with an allowlist and
throw/exit with a descriptive error.

### PowerShell (scripts/helpers.ps1)

```powershell
# After extraction:
$modules = 'engineering'  # default
if ($fm -match '(?m)^\s*modules:\s*["\x27]?([^"\x27\r\n]+)["\x27]?\s*$') {
    $modules = $Matches[1].Trim()
}

# Reject YAML list notation (e.g. modules: [engineering, research])
if ($modules -match '^\[') {
    throw "Invalid modules format in compound-gpid.local.md: YAML list notation is not " +
          'supported. Use a quoted string: modules: "engineering, research"'
}

# Allowlist validation
$validModules = @('engineering', 'research', 'engineering, research', 'research, engineering')
if ($validModules -notcontains $modules) {
    throw "Invalid modules value '$modules' in compound-gpid.local.md. " +
          "Valid values: $($validModules -join ', ')"
}
```

### Python (scripts/link.sh heredoc)

```python
modules = extract_fm_value(local_path, 'modules') or 'engineering'

# Reject YAML list notation
if modules.startswith('['):
    print('ERROR: Invalid modules format in compound-gpid.local.md: YAML list notation '
          'is not supported. Use a quoted string: modules: "engineering, research"',
          file=sys.stderr)
    sys.exit(1)

# Allowlist validation
VALID_MODULES = {'engineering', 'research', 'engineering, research', 'research, engineering'}
if modules not in VALID_MODULES:
    print(f'ERROR: Invalid modules value "{modules}" in compound-gpid.local.md. '
          f'Valid values: {", ".join(sorted(VALID_MODULES))}', file=sys.stderr)
    sys.exit(1)
```

## Prevention

**Pattern: validate config fields at the boundary, not at the point of use.**

For any YAML frontmatter field that drives downstream behavior:

1. **List notation guard first**: YAML users may naturally write `[a, b]` or block `- a`. These
   parse to unexpected strings — check for `[` prefix and reject early with guidance.

2. **Allowlist over passthrough**: enumerate valid values explicitly. Use a set/array literal
   rather than a regex so the valid set is readable and easily extended.

3. **Error message must name the file and suggest the fix**: the user is editing
   `compound-gpid.local.md`, not the script — show the file name, the bad value, and the
   canonical valid values.

4. **Validate in both language implementations**: this project maintains parallel
   PowerShell (link.ps1/helpers.ps1) and Python (link.sh heredoc) config parsers. Both
   must enforce the same constraints. Add a cross-language parity test if practical.

5. **Test the allowlist with edge cases**: test `research only`, `engineering only`,
   `both (comma-separated)`, `invalid`, and `YAML list notation` as separate Context blocks.
   A test that only covers the happy path will not catch the empty/invalid/format-error cases.

## Related

- `scripts/helpers.ps1` and `scripts/link.sh` — updated in commit `77af4ac`
- `tests/helpers.Tests.ps1` — added edge-case Context blocks for `research only`,
  `invalid value (throws)`, and `YAML list notation (throws)`
- `tests/bash-scripts.Tests.ps1` — added modules substitution functional test
- See also: `data-quality/` for YAML type-safety patterns
