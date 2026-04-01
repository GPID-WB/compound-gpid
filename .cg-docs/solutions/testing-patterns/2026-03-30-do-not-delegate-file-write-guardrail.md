---
date: 2026-03-30
title: "Do NOT delegate file-writing steps in AI workflow prompts"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, prompt-authoring, subagent, delegation, file-write, silent-failure, cg-review, guardrails, agent-mode]
root-cause: "An AI agent delegated a file-writing step to a subagent; file writes in the subagent's context are silently discarded when the subagent returns, leaving no artifact"
severity: "P1"
---

# Do NOT Delegate File-Writing Steps in AI Workflow Prompts

## Problem

A multi-step AI workflow prompt (`cg-review.prompt.md`) contained a step
(Step 3.5) that was supposed to write the review report to disk:

```
3. Write the full prioritized report to .cg-docs/reviews/<stem>-review.md.
```

At runtime, the agent chose to delegate this step to a subagent. The write
succeeded — inside the subagent's execution context — but when the subagent
returned control to the calling agent, the file was gone. No error was raised.
The review report was silently lost.

**Observable symptom**: User runs `/cg-review`, sees the report summary in
the chat, then runs `/cg-fix-triage` in a new session and is told _"No review
reports found in `.cg-docs/reviews/`."_ No file was ever written to disk.

**Why delegation causes silent loss**: Subagents are ephemeral. File writes
executed inside a subagent are visible only within that subagent's tool calls
and are not reflected in the outer workspace. When the subagent finishes and
returns a text response, those tool effects vanish.

## Root Cause

The step instruction was written in passive voice without specifying the
execution context: _"Write the full report to ..."_.  This left it open to
the agent's discretion whether to execute the write itself or hand it off.
Because writing a large file is a non-trivial operation, the agent chose to
delegate it.

## Solution

### 1. Add explicit "Do NOT delegate" to any file-writing step

For every prompt step that persists something to disk, add an explicit
prohibition immediately after the write instruction:

```markdown
3. Write the full prioritized report (the markdown block from Step 3) to
   `.cg-docs/reviews/<stem>-review.md`. **Write this file directly using
   your own file creation tool. Do NOT delegate this step to a subagent.**
```

Key phrasing elements:
- **"directly"** — emphasises the calling agent must act, not hand off
- **"your own file creation tool"** — makes it concrete which capability to use
- **"Do NOT delegate this step to a subagent"** — unambiguous prohibition

### 2. Add a Pester regression test that the instruction survives

Without a test, a future refactor could soften or remove the "Do NOT delegate"
clause, and the silent-loss bug would return undetected:

```powershell
Describe "cg-review.prompt.md - review file output step" {
    $promptFile = Join-Path $repoRoot ".github\prompts\cg-review.prompt.md"
    $content    = Get-Content $promptFile -Raw -Encoding UTF8

    # ... other contract tests ...

    It "explicitly instructs DO NOT delegate the Step 3.5 file write" {
        ($content -match 'Do NOT delegate') | Should Be $true
    }
}
```

This test guards against the most common recurrence vector: a prompt that is
paraphrased during a refactor, dropping the explicit prohibition.

## Prevention

Apply this pattern to **every** prompt step that creates, modifies, or deletes
files outside the subagent pattern:

| Step type | Guard needed? |
|-----------|--------------|
| Write a report/artifact to `.cg-docs/` | ✅ Yes |
| Apply a code fix (edit a source file) | ✅ Yes |
| Delete a file | ✅ Yes |
| Read a file for context | ❌ No (read-only, no persistence) |
| Ask a subagent to review code | ❌ No (intentional delegation) |

**Checklist for prompt authors**:

1. Scan every step in the process for file-system mutations.
2. For each mutation step, add "Do NOT delegate this to a subagent."
3. Add a Pester test that the phrase survives refactoring.

## Related

- [2026-03-30-prompt-pipeline-contract-testing.md](./2026-03-30-prompt-pipeline-contract-testing.md)
  — How to test the interface contract between chained prompts (cg-review → cg-fix-triage).
- [2026-03-30-test-prompt-frontmatter-tools-list.md](./2026-03-30-test-prompt-frontmatter-tools-list.md)
  — How to test that the `tools:` frontmatter grants write permission so the
  agent can write at all (a separate but complementary guard).
- [git-workflows/2026-04-01-charter-drift-prevention.md](../git-workflows/2026-04-01-charter-drift-prevention.md)
  — Structural rule + `last-reviewed` frontmatter + archive-on-removal pattern
  applied to a shared committed document; tests enforce the invariants.
