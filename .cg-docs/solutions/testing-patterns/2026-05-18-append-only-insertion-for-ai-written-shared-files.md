---
date: 2026-05-18
title: "Append-only insertion prevents silent corruption in AI-written shared files"
category: "testing-patterns"
language: "both"
tags: [prompt-design, context-md, markdown, corruption, append-only, structured-content]
root-cause: "Instruction to insert content 'logically within the existing structure' causes the model to insert mid-table, inside code fences, or between YAML key-value pairs"
severity: "P1"
---

# Append-only insertion prevents silent corruption in AI-written shared files

## Problem

`/cg-compound` Step 5 was instructed to enrich `compound-gpid.context.md` by inserting "directly into the correct section — place it logically within the existing structure, not appended at the end."

This is semantically correct for a human editor but dangerous for an AI model: the model must identify a target location inside existing text, and it may insert mid-table, inside a fenced code block, or between YAML key-value pairs — all of which are syntactically valid text positions that are semantically destructive.

### Concrete corruption scenario

`compound-gpid.context.md` contains:

```markdown
| Variable | Source | Notes |
|----------|--------|-------|
| welfare  | GPID   | PCE   |
```

The model determines this table is the correct section for a new domain fact. It inserts a new line *before* the `| welfare |` row:

```markdown
| Variable | Source | Notes |
|----------|--------|-------|
| income   | Survey | 2024  |
| welfare  | GPID   | PCE   |
```

This particular case is harmless. But an insertion *between* the header row and the separator row, or inside a fenced code block, breaks the structure — and since markdown is rendered, the breakage is invisible until a human notices degraded output quality.

### Why this matters

`compound-gpid.context.md` is read at Step 0 by every prompt. Corrupted content is silently injected into every future session's context window. Unlike a file that throws an error, a malformed markdown table just renders as garbled text. The corruption is hard to detect and hard to trace.

## Root Cause

The instruction "insert logically within the existing structure" required the model to make a judgment call about the insertion point inside existing content. Models are unreliable at this — they may choose a position that breaks structural markup.

## Solution

Change the instruction from "insert within the structure" to **append-only**:

> "Append to the bottom of the matching section. Add a new `###` subsection if needed — never insert within existing lines."

This is safe because:
- Appending to the bottom of a section never disrupts existing content
- Adding a new `###` subsection is a structural unit that self-delimits
- The model does not need to identify a specific insertion point

### Implementation in `cg-compound.prompt.md` Step 5

```
3. If yes, append to the bottom of the matching section. Add a new `###`
   subsection if needed — never insert within existing lines. Report:
   "Context enriched: added [brief description] to the [section] section of
   `compound-gpid.context.md`."
```

## Prevention

**Rule**: Any prompt step that instructs an AI to write into an existing file with structured content (tables, code fences, YAML, HTML) must use append-only semantics:
- ✅ "Append a new item to the bottom of section X"
- ✅ "Add a new `###` subsection at the end of section X"
- ❌ "Insert into the correct position within section X"
- ❌ "Place it logically within the existing structure"

**Exception**: Plain prose sections (bullet lists of short items with no nested structure) are lower risk for mid-insertion, but the append-to-bottom rule still applies to avoid structural ambiguity.

**Testing**: Add a test asserting the prompt contains `never insert within existing lines` to catch regressions. See `tests/prompt-tools.Tests.ps1`: `It "Step 5 uses append-only insertion (never inserts within existing lines)"`.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-14-write-permission-flags-must-be-parsed-before-tool-dispatch.md`
- `.cg-docs/solutions/testing-patterns/2026-05-06-html-comment-as-fix-never-executed.md`
