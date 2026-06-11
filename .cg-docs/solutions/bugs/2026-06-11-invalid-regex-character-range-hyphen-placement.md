---
date: 2026-06-11
title: "Invalid regex character class range: hyphen placement between non-ascending code points"
category: "bugs"
language: "both"
tags: [regex, character-class, validation, shell-safety, agent-spec, prose]
root-cause: "Hyphen placed between two characters whose ASCII values are descending (e.g., '/-' where '/' is 47 and '-' is 45) creates an invalid character range that raises an error in POSIX, Python re, and JavaScript regex engines"
severity: "P3"
---

# Invalid Regex Character Class Range: Hyphen Placement Between Non-Ascending Code Points

## Problem

An agent spec (`cg-roadmap.agent.md`) included this validation regex as prose guidance:

```
^[A-Za-z0-9_. :/-]*$
```

The sequence `/-` inside the character class `[...]` is interpreted by strict regex engines
as the range "from `/` to `-`". Since `/` is ASCII 47 and `-` is ASCII 45, and 47 > 45,
this is an invalid (descending) range. Engines that enforce strict range ordering raise an error:

```python
>>> import re
>>> re.compile(r'^[A-Za-z0-9_. :/-]*$')
# raises: re.error: bad character range /-  at position 13
```

JavaScript (strict mode), POSIX `grep -E`, and most compiled regex engines similarly reject it.

The bug was present as prose in an LLM agent spec — **not in running code** — so it
caused no runtime failure in the project. However, the regex would fail immediately if
copy-pasted into a Python validator, shell script, or any strict-engine environment.

Found in: `.github/agents/cg-roadmap.agent.md` Configure GitHub Issues step 3, during
the `mode:verify` pass of the 2026-06-11 GitHub Issues integration review cycle.

## Root Cause

When authoring a character class to allow "letters, digits, and the special chars
`_`, `.`, ` `, `:`, `/`, `-`", the natural human ordering places `-` after `/`:

```
[A-Za-z0-9_. :/-]   # WRONG: /-  is interpreted as range '/' to '-'
```

This is a classic off-by-one style mistake: the author intends `-` as a literal
character, but its placement between `/` and `]` (or between any two other characters)
makes it a range operator.

The issue is subtle because:
1. Many regex engines (including .NET / PowerShell's `-match`) are permissive and treat
   the invalid range as two literal characters rather than raising an error. The regex
   "works" in PowerShell but silently fails elsewhere.
2. In a markdown document or LLM prompt, no linter scans for invalid regex character classes.
3. The `-` is not misplaced "obviously" — it's next to `/` which looks like part of
   the intended set rather than a range boundary.

## Solution

Place `-` at the **start** or **end** of the character class — never between two other characters:

```
# SAFE: - at start
^[-A-Za-z0-9_. :/]*$

# SAFE: - at end
^[A-Za-z0-9_. :/-]*$   -- WRONG (see above)
^[A-Za-z0-9_. :/\-]*$  -- SAFE: escaped with backslash
^[A-Za-z0-9_. :/]*-?   -- alternative: make - optional outside the class

# CANONICAL SAFE form for "letters, digits, and _.:/ -":
^[-A-Za-z0-9_. :/]*$
```

Applied fix in `cg-roadmap.agent.md`:
```
# Before (invalid range):
^[A-Za-z0-9_. :/-]*$

# After (- moved to front):
^[-A-Za-z0-9_. :/]*$
```

## Prevention

**Rule**: In any character class `[...]`, the literal `-` must be at the very start
(`[-...]`) or very end (`...-]`), or escaped (`\-`). If `-` is placed between two
characters, it is a range — verify the range is valid (left char ASCII < right char ASCII).

**LLM-specific gotcha**: When LLMs author regex patterns as prose (in `.prompt.md`,
`.agent.md`, or `SKILL.md` files), they often list characters in "natural" order
(`a-z`, `0-9`, then special chars), which places `-` mid-class. Add a source-scanning
test to catch invalid mid-class hyphens in agent/prompt spec files.

**Detection**: In Python, `re.compile()` raises on invalid ranges. In JavaScript,
`new RegExp()` raises `SyntaxError: Invalid regular expression`. In POSIX grep:
`echo '' | grep -E '^[A-Za-z0-9_. :/-]*$'` exits non-zero with error.

**Quick audit**: Search for regex patterns in `.agent.md` and `.prompt.md` files:
```powershell
Select-String -Path .github/agents/*.agent.md -Pattern '\[.+[^\\]-[^]].+\]' |
  Where-Object { $_.Line -notmatch '(A-Z|a-z|0-9)' }
```

## Related

- `.cg-docs/solutions/bugs/2026-03-23-case-insensitive-regex-fails-git-tag-validation.md` — related regex authoring gotcha (case sensitivity in PowerShell)
- `.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md` — alternation masking in Pester assertions
- `.cg-docs/solutions/testing-patterns/2026-05-06-pester-caret-anchor-requires-multiline-flag.md` — anchor flag gotcha
- `.cg-docs/solutions/bugs/2026-06-11-cli-injection-in-llm-driven-gh-prompts.md` — broader CLI injection context in which this regex was introduced
