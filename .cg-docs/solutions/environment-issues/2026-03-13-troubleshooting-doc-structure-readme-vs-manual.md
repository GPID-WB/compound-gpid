---
date: 2026-03-13
title: "Troubleshooting documentation belongs in manual, not README"
category: "environment-issues"
language: "both"
tags: [documentation, readme, manual, troubleshooting, structure, architecture]
root-cause: "Troubleshooting entries landed in README.md by default (first entry established the pattern there), conflicting with the established convention that README is a brief intro and docs/manual.md owns operational reference content"
severity: "P2"
---

# Troubleshooting Documentation Belongs in Manual, Not README

## Problem

A troubleshooting section was added to `README.md` during a hotfix (documenting a `cg-update`
bootstrap failure). Because it was the first such entry and README was the most visible file,
it landed there. A second entry followed. With more issues inevitable, this created a divergence:
`docs/manual.md` exists as the operational reference but troubleshooting content was accumulating
in `README.md` instead.

## Root Cause

No explicit convention existed for where troubleshooting entries go. The first entry established
a de-facto pattern in the wrong file. Without a clear rule, each new entry defaulted to README
(most visible, easiest to find).

The existing convention — README = brief intro, `docs/manual.md` = operational reference — was
documented in `.cg-docs/brainstorms/2026-03-02-rename-prefix-and-documentation.md` but not
enforced.

## Solution

Move all troubleshooting content to `docs/manual.md#troubleshooting`. In `README.md`, replace
the section with a single pointer:

```markdown
> For troubleshooting and known issues, see the [User Manual](docs/manual.md#troubleshooting).
```

**Exception**: bootstrap failures that prevent users from reaching the manual (e.g., `cg-update`
failing before it can pull the fix) are defensible in README — the user literally cannot get to
the manual if the tool is broken. In these cases, keep a minimal entry in README and duplicate
the full detail in `docs/manual.md`.

### Troubleshooting entry structure (Symptom/Cause/Fix)

Each entry in `docs/manual.md` should follow this pattern:

```markdown
### `<command>` fails with "<error message>"

**Symptom**:
```
<exact terminal output>
```

**Cause**: <one-sentence root cause>

**Fix — <action summary>**:
```powershell
<commands>
```

<follow-up prose if needed>

> **If <fix> fails** with `<error>`, <fallback explanation>:
> ```powershell
> <fallback command>
> ```
```

**Include**:
- Exact terminal output in the Symptom block (users can search for it)
- One-sentence root cause
- Specific fix commands with inline comments explaining non-obvious flags (e.g., `2>$null  # suppress stderr (PS5.1 stderr-to-error promotion)`)
- Fallback if the primary fix can fail in edge cases
- GitHub Issues link for persistent problems: `If the issue persists, open a [GitHub Issue](<url>).`

## Prevention

- All new troubleshooting entries go in `docs/manual.md` under `## Troubleshooting`
- `README.md` only gets a pointer, not the content
- Exception: bootstrap failures where the tool itself is broken — keep a minimal entry in README and full detail in manual
- During `/cg-review`, flag any troubleshooting content added to README as a P2 architecture finding

## Related

- [`.cg-docs/brainstorms/2026-03-02-rename-prefix-and-documentation.md`](../../brainstorms/2026-03-02-rename-prefix-and-documentation.md) — Original convention establishing README vs manual split
- [`.cg-docs/solutions/git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md`](../git-workflows/2026-03-05-ps51-stderr-stop-terminates-on-git-informational-output.md) — The entry that triggered this finding
