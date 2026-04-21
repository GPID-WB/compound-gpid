---
date: 2026-04-21
title: "Prompt step with forward dependency needs explicit deferred-execution marker"
category: "testing-patterns"
language: "both"
tags: [prompt-design, step-ordering, forward-dependency, deferred-execution, skill-loading, cg-fix-triage, sequential-model]
root-cause: "A prompt step that appears before the step it depends on (forward dependency) is executed out of order by sequential-reading models unless an explicit deferral instruction is present"
severity: "P1"
---

# Prompt Step With Forward Dependency Needs Explicit Deferred-Execution Marker

## Problem

`cg-fix-triage.prompt.md` had a `### Step 0.5: Load Language Skills` section
that appeared *before* `### Step 1` in document order, but whose body said:

> "After Step 1.3 identifies which file types appear in findings, load
> applicable skills only for those types"

This is a **forward dependency**: Step 0.5 depends on information (which file
types appear in findings) that isn't available until Step 1.3 completes.

Sequential-reading models follow document order. Encountering Step 0.5 first,
they attempted to load language skills immediately — before findings were
parsed — producing session-to-session variance in skill selection.

## Root Cause

Prompt files are read top-to-bottom. A step's *position* in the document
determines when it executes, not its number. Placing a numbered step out of
execution order creates a silent forward dependency that only shows up as
non-deterministic behavior.

The `--migrate` guard (`Skip this step if invoked as --migrate`) was evaluated
correctly because the flag is visible at invocation time. But the general case
(non-migrate invocations) had no instruction to defer.

## Solution

Add an HTML comment immediately before the step header, plus inline text in
the opening line:

```markdown
<!-- Execute AFTER Step 1.3 — do not load skills before findings are parsed. -->
### Step 0.5: Load Language Skills

**Skip this step if invoked as `--migrate`.** (Deferred: execute after Step 1.3
completes. The `--migrate` flag is visible at invocation time — no need to
wait for Step 2.)
```

The HTML comment is invisible to the user but read by the model. The inline
parenthetical reinforces the constraint in natural language where it will be
read just before the step body.

## Prevention

- **Rule**: Any numbered step that appears out of execution order in a prompt
  file needs an explicit deferred-execution marker: an HTML comment + inline
  parenthetical explaining when to execute and why.
- **Design preference**: Prefer placing steps in execution order. If a step
  must appear early (e.g., as a navigation aid), use the comment + inline note
  pattern.
- **Test coverage**: Add a position-ordering test using `IndexOf`:
  ```powershell
  It "Step 0.5 appears before Step 1 in document order" {
      $step05Pos = $content.IndexOf("### Step 0.5:")
      $step1Pos  = $content.IndexOf("### Step 1:")
      $step05Pos | Should BeLessThan $step1Pos
  }
  It "Step 0.5 instructs executing after Step 1.3" {
      ($content -match 'execute after Step 1\.3|Deferred.*Step 1\.3') | Should Be $true
  }
  ```

## Related

- [2026-04-13-prompt-step-ordering-indexof-tests.md](./2026-04-13-prompt-step-ordering-indexof-tests.md) — IndexOf-based ordering tests for prompt steps
- [2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md](./2026-04-15-prompt-step-silent-skip-antipattern-fallback-required.md) — related silent-skip anti-pattern
- [2026-04-13-dead-step-after-wait-prompt-session-terminator.md](./2026-04-13-dead-step-after-wait-prompt-session-terminator.md) — dead steps after user-wait pauses (related positioning failure mode)
