---
date: 2026-05-14
title: "Write-permission mode flags must be parsed before any tool dispatch, not deferred to a later step"
category: "testing-patterns"
language: "both"
tags: [prompt-design, file-permissions, mode-flags, propose, read-only, step-ordering, cg-verify-pr]
root-cause: "A --propose READ-only flag was documented in File Permissions but not parsed until Step 0.6, allowing tool-using steps (Step 0.1–0.5) to run in write mode before the flag was evaluated"
severity: "P2"
---

# Write-permission mode flags must be parsed before any tool dispatch, not deferred to a later step

## Problem

A prompt's File Permissions block declared:

> `--propose` mode: READ-only — no file creation, modification, git commits,
> or pushes of any kind.

But the flag parsing was placed in **Step 0.6** — after bearings (Step 0.1–0.3)
and other pre-flight work. An agent executing linearly could call `read_file`
and other tool-dispatching steps (Steps 0.1–0.5) before it evaluated the
`--propose` flag. If the agent's future steps included write operations, the
READ-only constraint had not yet been established when those steps were entered.

Discovered as P2.1 in the `cg-commit-push-pr`/`cg-verify-pr` thorough review.

## Root Cause

Mode flags that restrict what the agent is permitted to do must be evaluated
**before any step that could dispatch a tool**. Placing flag parsing after Step 0
bearings creates a window where the agent has already started executing without
knowing it is in READ-only mode.

This is the same class of bug as "within-step pre-flight ordering" (guards before
the offer) but at the macro level: **the permission mode is a global guard that
must precede all action steps**.

## Solution

Move flag parsing to **Step 0 itself**, immediately after reading the charter
(Step 0.1), before any tool dispatch or conditional logic:

```markdown
### Step 0: Get Bearings

1. Read `compound-gpid.md` ...
2. Read `compound-gpid.local.md` ...
3. Read `compound-gpid.context.md` ...

4. **Parse invocation flags** (do this before any further step):
   - If `--propose` is present: set mode = `observe-only`. No file creation,
     modification, git commits, or pushes for the remainder of this session.
   - Default: mode = `auto-fix`.
   Announce: "Running in **[auto-fix / observe-only (--propose)]** mode."
```

For prompts where Step 0 is a fixed boilerplate (e.g., "Get Bearings"), use
**Step 0.5** rather than 0.6:

```markdown
### Step 0.5: Parse Invocation Flags

*(Execute before Step 1 — do not defer to Step 0.6 or later.)*
```

The key invariant: **no step that might write a file, run git, or call a tool
may execute before the write-permission mode is resolved**.

## Prevention

- In any prompt that has a flag controlling write permissions (`--propose`,
  `--dry-run`, `--read-only`, etc.): the flag parsing step must appear before
  Step 1, ideally as part of Step 0 or Step 0.5.
- Test signal — assert the flag parsing step comes before Step 1:
  ```powershell
  It "parses --propose flag before Step 1 (not deferred to Step 0.6 or later)" {
      # Verify Step 0.6 or flag parse section appears before Step 1
      $step06Idx = $content.IndexOf("Step 0.6")
      $step1Idx  = $content.IndexOf("### Step 1")
      $step06Idx | Should -BeGreaterThan -1
      $step06Idx | Should -BeLessThan $step1Idx
  }
  ```
- Cross-reference the "within-step pre-flight ordering" convention in
  `compound-gpid.context.md` — this is its macro-level equivalent.

## Related

- `.cg-docs/solutions/testing-patterns/2026-05-05-within-step-preflight-must-precede-offer-template.md`
- `.cg-docs/solutions/testing-patterns/2026-04-21-prompt-step-forward-dependency-deferred-marker.md`
- `.cg-docs/solutions/testing-patterns/2026-04-13-dead-step-after-wait-prompt-session-terminator.md`
