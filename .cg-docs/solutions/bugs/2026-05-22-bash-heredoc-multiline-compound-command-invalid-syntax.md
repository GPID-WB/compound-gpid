---
date: 2026-05-22
title: "Bash heredoc with multi-line || { } compound command body is invalid syntax"
category: "bugs"
language: "both"
tags: [bash, heredoc, compound-command, syntax-error, error-trap, bash-3.2, macos]
root-cause: "In bash, a heredoc (<<'EOF') combined with a multi-line || { ... } compound command body is invalid; the closing } must appear on the same line as <<'EOF'"
severity: "P1"
---

# Bash heredoc with multi-line `|| {` compound command body is invalid syntax

## Problem

`scripts/link.sh` (and later `scripts/helpers.sh`) contained an error-trap pattern that
appeared reasonable but was syntactically broken:

```bash
generate_copilot_instructions() {
    ...
    python3 - "$args" <<'PYEOF' || {
        print_error "Failed to generate copilot instructions."
        exit 1
    }
# Python heredoc content...
PYEOF
}
```

**Symptom at runtime**: `bash: syntax error near unexpected token '}'` — the closing `}`
of the outer function is unexpected. Or the error-trap body is silently treated as
heredoc content, meaning `python3` exits non-zero with no handler.

**Critical masking**: The tests for these scripts only checked file content (regex pattern
matching against the source text), never executed the function. Additionally, `bash -n`
(syntax-check mode) did NOT report this as a syntax error in bash 3.2.57 (macOS default
shell as of Ventura/Sonoma) — `bash -n scripts/link.sh` exited 0 with no output.

## Root Cause

When bash processes `cmd <<'PYEOF'`, it queues the heredoc to be read from the lines
immediately following. The `|| {` opens a compound command group — bash expects to read
the group body lines until it finds `}`. These two mechanisms conflict: bash cannot
simultaneously read the compound command body (lines between `|| {` and `}`) AND defer
the heredoc to the lines that follow `}`.

The result:
- The lines `print_error "..."` and `exit 1` are read as heredoc content (passed to stdin
  of `python3`), not as the error handler
- The `}` that was meant to close the error handler is treated as a stray token
- `bash -n` in 3.2.57 does NOT reliably catch this — it reports success even though the
  construct is malformed

## Solution

Place the entire `|| { }` body on a single line:

```bash
# ✓ CORRECT: single-line trap — valid in all bash versions
python3 - "$args" <<'PYEOF' || { print_error "Failed to generate copilot instructions."; exit 1; }
# Python heredoc content
...
PYEOF
```

Alternatively, use `set -euo pipefail` in the calling script and rely on automatic abort
on non-zero exit, with a separate diagnostic message before the call.

## Prevention

**Rule: when combining `<<'EOF'` with `|| { }` error handling, the entire `{ }` body
must fit on a single line.**

Detection — grep for the broken pattern:
```bash
grep -n "<<'[A-Z]*' || {$" scripts/*.sh
```
Any line that ends with `|| {` (nothing after the opening brace) is likely broken.

**Rule: `bash -n` does not reliably catch heredoc + compound-command interaction errors
in bash 3.2 (macOS default).** Always run an actual execution test (call the function
with a fixture input) to verify heredoc-containing functions work end-to-end. Add a
`bash -c 'source helpers.sh; function_under_test args'` call in CI rather than relying
on `bash -n` alone.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-22-test-reimplements-logic-with-correct-code-masks-bug.md` — the test masking pattern that prevented this from being caught earlier
- `.cg-docs/solutions/bugs/2026-05-14-python-regex-raw-string-double-backslash-excludes-letters.md` — the co-discovered regex bug in the same heredoc function
- Fix commit: `57dad18` — "fix(update): extract shared helpers.sh; fix extract_fm_value regex"
- Production fix location: `scripts/helpers.sh` — `generate_copilot_instructions`, Python heredoc call line
