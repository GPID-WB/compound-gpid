---
date: 2026-06-11
title: "LLM 'resolve canonical path' instruction without tool call is unenforceable — symlink traversal remains exploitable"
category: "bugs"
language: "both"
tags: [security, symlink-traversal, path-validation, llm-limitations, prompt-authoring, realpath, cg-issues]
root-cause: "An LLM instructed to 'resolve the canonical real path' performs string-based reasoning, not an OS syscall — a symlink pointing outside the allowed directory passes all string-level checks and is only caught by actually executing readlink -f or Resolve-Path"
severity: "P1"
---

# LLM "Resolve Canonical Path" Instruction Without Tool Call Is Unenforceable

## Problem

A prompt included this path-validation step as a defense against symlink traversal:

> "Resolve the path to its canonical real path (following symlinks) and verify
> the canonical path still starts with the project root's `.cg-docs/plans/`
> directory (guards against symlink traversal to sensitive files)"

A plan file path that passes all preceding string-level checks:
- Starts with `.cg-docs/plans/` ✓
- Ends with `.md` ✓
- Contains no `..` ✓
- Is not absolute ✓

But is actually a symlink: `.cg-docs/plans/legit.md → ../../../../.ssh/id_rsa`

The LLM reads this instruction and reasons: "the path looks like `.cg-docs/plans/legit.md`,
which starts with `.cg-docs/plans/` — canonical path check passed." The agent
cannot follow the symlink by reasoning alone; it does not call `readlink -f` or
`Resolve-Path` unless explicitly instructed to do so via a tool call.

**The symlink guard existed in the prompt but was completely ineffective.**

## Root Cause

LLMs are language models. They simulate reasoning about file paths by applying
string operations to path strings. They cannot:
- Execute `readlink -f` (Linux/macOS) to resolve symlinks
- Execute `Resolve-Path` (PowerShell) to return the canonical path
- Call any OS-level filesystem API

An instruction like "resolve the canonical path" is read by the LLM as a *reasoning
instruction*, not an *execution instruction*. The LLM applies its knowledge of
what `readlink` does and concludes the path is safe based on its string representation.

This is distinct from Python/PowerShell code that actually invokes `Path.resolve()`
or `Resolve-Path` — that code runs at the OS level and follows symlinks physically.

## Solution

Change the prose from reasoning-only to tool-call-required:

**Before (ineffective)**:
```
Resolve the path to its canonical real path (following symlinks) and verify
the canonical path still starts with the project root's .cg-docs/plans/ directory.
```

**After (enforceable)**:
```
Execute Resolve-Path (PowerShell) or readlink -f (bash/Linux) via a tool call to
obtain the canonical real path; compare the returned string against the expected
.cg-docs/plans/ prefix. String-only reasoning is insufficient — the tool call is
required to defeat symlink traversal.
```

The key phrases are: "**via a tool call**" and "**String-only reasoning is insufficient**".
These signal to the LLM that it must execute a command, not reason about the path.

Applied in `.github/prompts/cg-issues.prompt.md` step 5 as part of the
2026-06-11 review cycle.

## Prevention

**General rule**: Any security check in a prompt that requires OS-level behavior
(reading the real inode path, checking file permissions, verifying HMAC/hash,
resolving DNS) must include explicit tool-call language:
- "Execute `<command>` via a tool call"
- "Use `Resolve-Path` / `readlink -f` — string reasoning is insufficient"
- "Run `<command>` and compare the output"

**Never write**: "verify the canonical path", "resolve symlinks", "check file
permissions" — without a corresponding explicit tool invocation instruction.

**Detection**: Review all prompt steps that reference security-sensitive filesystem
operations (`realpath`, `canonical`, `symlink`, `permissions`, `hash`, `signature`).
If the step contains no tool-call language, it is prose-only and ineffective.

**Depth of defense**: Even with a tool-call instruction, the LLM may be in a
context where the tool is not available. Add a fallback: "If the tool call fails
or is unavailable, skip this plan file entirely and use a stub body."

## Related

- `.cg-docs/solutions/bugs/2026-05-20-python-path-startswith-bypass-use-relative-to.md` — Python-code analog: `str.startswith()` on paths is bypassable by sibling-directory names; same root cause at the code level. `Path.relative_to()` is the fix there; tool-call `Resolve-Path` is the fix here.
- `.cg-docs/solutions/testing-patterns/2026-05-14-prompt-injection-via-plan-content-in-ai-generated-output.md` — plan file injection; complements this by addressing what happens after the file is read
- `.cg-docs/solutions/bugs/2026-06-11-cli-injection-in-llm-driven-gh-prompts.md` — broader CLI injection context; realpath fix was P1.2 finding
- `.github/prompts/cg-issues.prompt.md` — fixed prompt (backfill step 5)
