---
date: 2026-03-02
title: "Constraining file writes in output-producing prompts without agent: plan mode"
category: "testing-patterns"
language: "both"
tags: [prompts, guardrails, file-permissions, agent-mode, copilot]
root-cause: "agent: plan mode prevents all file writes, but brainstorm/plan prompts need to write their output documents — requiring a different approach to scope control"
severity: "P2"
---

# Constraining File Writes in Output-Producing Prompts

## Problem

When designing prompts that should not modify source code (e.g., `cg-brainstorm`,
`cg-plan`), the natural instinct is to use `agent: plan` mode in the YAML
frontmatter. However, `agent: plan` mode prevents **all** file writes — including
writing the output documents these prompts are specifically designed to produce
(`docs/brainstorms/`, `docs/plans/`).

The symptoms:
- Prompt runs correctly through Q&A
- At the capture step, fails silently or errors when trying to write the output file
- Or: switching to `agent: plan` means the output is only shown inline in chat,
  never persisted to disk

## Root Cause

`agent: plan` mode is designed for read-only analysis. It trades off the ability
to write any files in exchange for safety. For prompts whose sole purpose is to
produce a bounded output document, this is too restrictive — the safety guarantee
prevents the core function.

The underlying tension: you want **scope-limited writes** (only to a specific
directory), not **zero writes**.

## Solution

Use default agent mode (no `agent:` frontmatter key, or `agent: default`) and
add an explicit `## File Permissions` section to the prompt body with
self-contained sentences for each rule:

```markdown
## File Permissions

- You may read any file in the workspace.
- You may create new files under `docs/brainstorms/`.
- You must not modify any existing files.
- You must not create files outside `docs/brainstorms/`.
```

Key design choices:
- Each rule is a **self-contained sentence** (not a header + fragments) so the
  instruction is unambiguous when read by the model.
- Use "You may" / "You must not" rather than emoji markers or section headers
  like "ALLOWED:" / "NOT ALLOWED:" — these are more explicit and less prone to
  misinterpretation.
- Place the section **before** the `## Process` section so it is read before any
  action is taken.

## Prevention

When designing a new prompt that needs bounded file output:

1. Do not use `agent: plan` if the prompt needs to write any files.
2. Add a `## File Permissions` section immediately after the opening role
   description, before `## Process`.
3. Write one sentence per permission, using "You may" or "You must not".
4. Be explicit about both the allowed directory **and** the prohibition on writing
   outside it — do not assume the model will infer the boundary.

Anti-pattern to avoid:

```markdown
## File Permissions
ALLOWED:
- Read files
- Create files in docs/

NOT ALLOWED:
- Modify files
```

This pattern uses fragments under headers, which is less explicit than full
sentences and more likely to be interpreted loosely.

## Related

- `docs/plans/2026-03-02-rename-prefix-and-documentation.md` — the plan that
  introduced this pattern
- `docs/brainstorms/2026-03-02-rename-prefix-and-documentation.md` — the
  brainstorm where the agent: plan vs. default mode tension was first identified
- [2026-03-30 Test prompt frontmatter tools: list](./2026-03-30-test-prompt-frontmatter-tools-list.md)
  — Complementary pattern: when prompts use `tools:` frontmatter instead of
  `agent: plan`, guard the list with Pester tests to prevent silent write failures.
