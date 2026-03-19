---
date: 2026-03-18
title: "Unclosed code fence in Markdown skill files silently corrupts downstream rendering"
category: "bugs"
language: "both"
tags: [markdown, documentation, code-fence, rendering, skill-files, copy-paste]
root-cause: "A backtick code fence opened inside a Verification Tests section was never closed; a subsequent orphaned test_that() block consumed the closing fence of the next section"
severity: "P2"
---

# Unclosed Code Fence in Markdown Skill Files Silently Corrupts Downstream Rendering

## Problem

In `welfare-patterns.md`, a ` ```r ` fence opened at the start of the Verification Tests section
was never closed. An incomplete duplicate `test_that(...)` block was accidentally appended after
the last test case, which consumed the opening fence of the *next* section. The result:

- Everything after the last valid test case rendered as raw R code inside the fenced block
- The `## Multiple Poverty Lines` section heading disappeared from navigation
- Blockquote callouts (` > Run the pre-checks...`) rendered as literal text inside a code block
- No parse error, no linter warning — visually looks fine in a source editor

## Root Cause

Copy-paste during editing: an incomplete `test_that("weighted_gini() returns 0 for perfect equality", {`
was pasted after the last test case, but the body and closing `})` were never added. This left an
unclosed R expression inside what looked like prose. The fence that *should* have closed the test
block instead appeared to open the next code example, breaking the fence pairing for the rest of
the document.

## Solution

**Before (broken)**:
```markdown
test_that("FGT is 0 when none are poor", {
  ...
})

test_that("weighted_gini() returns 0 for perfect equality", {

> Run the pre-checks from the FGT section above...

## Multiple Poverty Lines
```

**After (fixed)**:
```markdown
test_that("FGT is 0 when none are poor", {
  ...
})
```

> Run the pre-checks from the FGT section above...

## Multiple Poverty Lines
```

Steps:
1. Identify the last complete test case (`})` on its own line)
2. Close the code fence immediately after it (` ``` ` on its own line)
3. Remove the orphaned/incomplete `test_that(...)` line
4. Restore any section headings or prose that were consumed into the broken block

## Prevention

- After editing any code block in a Markdown skill file, visually verify the fence pair balance:
  every ` ```r ` or ` ``` ` opening must have a matching ` ``` ` close before the next prose heading
- Use a Markdown preview (`Ctrl+Shift+V` in VS Code) to catch rendering corruption immediately
- When adding test cases, always include the full `test_that("...", { ... })` block — never paste
  a partial skeleton and leave the file
- Prefer reviewing skill files in the VS Code Markdown preview rather than raw source when doing
  content additions

## Related

- [`testing-testthat.md`](../../../.github/skills/cg-skill-r-technical/references/testing-testthat.md) — canonical testthat patterns for skill docs
- [`welfare-patterns.md`](../../../.github/skills/cg-skill-r-analytical/workflows/welfare-patterns.md) — file where this bug was found and fixed
