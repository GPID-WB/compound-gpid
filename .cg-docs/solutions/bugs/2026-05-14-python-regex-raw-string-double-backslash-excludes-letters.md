---
date: 2026-05-14
title: "Python regex raw-string double-backslash silently excludes literal letters"
category: "bugs"
language: "Python"
tags: [python, regex, raw-string, backslash, character-class, frontmatter-parser]
root-cause: "Double-backslash in a Python raw string passes \\\\r/\\\\n to the regex engine, which treats them as literal \\ + r/n — not carriage-return/newline — so letters r and n are excluded from the character class"
severity: "P1"
---

# Python regex raw-string double-backslash silently excludes literal letters

## Problem

`extract_fm_value` in `scripts/link.sh` silently returned `''` (empty string) for any
YAML frontmatter value containing the letters `r` or `n` — including `research`, `r-syntax`,
`project-name`, etc.

The symptom was `modules: research` being read back as the default value `engineering`
instead of `research`. The test:

```
Expected: 'research'
But was:  'engineering'
```

The function appeared to work for simple values like `"r"`, `"standard"`, `"analysis"` —
none of which happen to contain `r` or `n` in positions that trigger the exclusion clearly —
masking the bug through the entire Phase 1+2 development cycle.

## Root Cause

The character class in the frontmatter extraction regex was written as:

```python
# BUGGY: double-backslash in raw string
pattern = r'(?m)^\s*' + re.escape(key) + r':\s*["\']?([^"\'\\r\\n]+)["\']?\s*$'
```

In a Python raw string `r'...'`, `\\r` is two chars: `\` and `r` (not carriage-return).
The regex engine receives the literal character sequence `\\r`, which it parses inside
`[...]` as:
- `\\` = escaped backslash → matches literal `\`
- `r`  = literal `r` → matches the letter r

So `[^"\'\\r\\n]` expands to: **"not any of: `"`, `'`, `\`, `r`, `\`, `n`"**

The letters `r` and `n` are silently excluded from the match. Any value containing those
letters is truncated at the first `r` or `n`, returning an empty capture group.

The intent was to exclude carriage-return (`\r`) and newline (`\n`), but the double-backslash
escaping defeats that — `\\r` in regex = escaped backslash + letter, not carriage-return.

## Solution

Replace `\\r`/`\\n` with unambiguous alternatives:
- Use `\x27` hex-escape for single-quote (avoids the backslash-letter confusion entirely)
- Use single-backslash `\r`/`\n` for line terminators (raw strings pass `\r`/`\n` to the
  regex engine which correctly interprets them as CR/LF)

```python
# FIXED: \x27 for apostrophe, single-backslash \r\n for line terminators
pattern = r'(?m)^\s*' + re.escape(key) + r':\s*["\x27]?([^"\x27\r\n]+)["\x27]?\s*$'
```

Why this works:
- `\x27` = hex-literal apostrophe — no backslash + letter ambiguity
- `\r` in a raw string = `\r` (two chars) → regex sees `\r` = carriage-return ✓
- `\n` in a raw string = `\n` (two chars) → regex sees `\n` = newline ✓

The frontmatter also matches the pattern: only one `---...---` block, so no value
should span a newline — `[^"\x27\r\n]+` correctly stops at line boundaries.

## Prevention

**Rule: never use `\\r` or `\\n` inside a Python raw-string regex character class.**

| Intent | Raw string form | What regex sees | Result |
|--------|----------------|-----------------|--------|
| Exclude carriage-return | `r'[^\r]'` | `[^\r]` = not CR | ✓ correct |
| Exclude carriage-return | `r'[^\\r]'` | `[^\\r]` = not `\` and not `r` | ✗ WRONG |
| Exclude newline | `r'[^\n]'` | `[^\n]` = not LF | ✓ correct |
| Exclude newline | `r'[^\\n]'` | `[^\\n]` = not `\` and not `n` | ✗ WRONG |

When the regex is being assembled via string concatenation in a **bash heredoc** (as in
`link.sh`), the escaping layers interact and `\\r` is especially tempting since bash
itself processes backslashes. Prefer `\x{NN}` hex-escapes for non-alphanumeric characters
and single-backslash `\r`/`\n` for standard escape sequences.

**Detection**: if a frontmatter parser returns `''` or falls back to a default for known
keys that should have values, suspect a character-class exclusion bug — add a print-debug
line to log the raw matched group before the `.strip()` call.

## Related

- Initial fix in `scripts/link.sh` at commit `77af4ac` (fix(research): apply all 40 Phase 1/2
  review findings)
- **Bug propagated** to `scripts/update.sh` via copy-paste (not sourced from a shared file).
  Fixed in commit `57dad18` by extracting both copies to `scripts/helpers.sh` (DRY refactor,
  mirrors the Windows `scripts/helpers.ps1` pattern).
- The PowerShell equivalent in `scripts/helpers.ps1` uses `[^"''\r\n]` directly in a
  non-raw regex literal and is not affected
- `.cg-docs/solutions/testing-patterns/2026-05-22-test-reimplements-logic-with-correct-code-masks-bug.md` — the test that masked the propagated bug in `update.sh`
- `.cg-docs/solutions/bugs/2026-05-22-bash-heredoc-multiline-compound-command-invalid-syntax.md` — co-discovered during the same fix session
