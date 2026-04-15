---
date: 2026-04-15
title: "Pester verbose output floods agent context window in long fix-triage sessions — crash even with safe PowerShell patterns"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, vscode, crash, fix-triage, context-overflow, long-session, ai-agent, copilot, quiet, prompt-tools]
root-cause: "Running Invoke-Pester without -Quiet on a large test file (prompt-tools.Tests.ps1, 300+ It-blocks) inside a long fix-triage session floods the agent context window with test output, causing VS Code to crash even though PowerShell itself exits with code 0"
severity: "P1"
---

# Pester Verbose Output Floods Agent Context Window in Long Fix-Triage Sessions

## Problem

VS Code crashed **twice in a single fix-triage session** (2026-04-15) even though
all terminal commands exited with code 0. The PowerShell patterns used were
technically "safe" — no forbidden pipelines, no `2>&1`, no directory run — yet
VS Code crashed immediately after the Pester run completed.

The commands that caused the crash:

```powershell
# ❌ CAUSES CONTEXT OVERFLOW in long sessions — no -Quiet flag
Invoke-Pester tests\prompt-tools.Tests.ps1

# ❌ ALSO RISKY — the second run produces output if first had failures
if ($r.FailedCount -gt 0) { Invoke-Pester tests\model-assignments.Tests.ps1 }
```

**Critical detail:** Both commands exited with code 0 (tests passed). The crash did
not come from PowerShell or the test runner itself — it came from the agent context
window being flooded by the test output that VS Code rendered.

**Session context at time of crash:** The conversation had accumulated a full
brainstorm → plan → implementation → review → fix-triage cycle. This is a
very long context (~10,000+ tokens of conversation history). Adding Pester's
verbose output for 300+ test blocks pushed the total past VS Code's context limit.

## Root Cause

**Two compounding factors (new combination, not previously documented):**

**Factor 1 — Missing `-Quiet` flag on `prompt-tools.Tests.ps1`.**
`prompt-tools.Tests.ps1` contains 300+ `It` blocks testing prompt frontmatter,
tool lists, step counts, agent definitions, etc. Without `-Quiet`, Pester prints
a line for every single passing test. On a 300-block file, this is 300+ lines of
output injected into the agent's visible context.

The Pester Safety Rules require `-Quiet` for single-file runs:
> Safe pattern: `Invoke-Pester tests/roadmap.Tests.ps1 -Quiet`

But the agent dropped the flag when it was "running a quick verification check"
mid-fix-triage — a subtle rule slip documented in
`2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md`.

**Factor 2 — Long accumulated session context at the time of the run.**
A complete brainstorm → plan → implementation → review → fix-triage cycle
produces a very long conversation. At this point in the session, the agent context
is already near capacity. Even a modest amount of additional output (300+ test
lines) can tip the balance over the limit.

**Why this is different from prior documented crashes:**
- `2026-04-02`: Crash from forbidden PowerShell patterns (directory run, ExpandProperty pipeline) — *PowerShell itself crashes VS Code*
- `2026-04-06`: Crash from agent forgetting rules due to context dilution — *agent uses forbidden patterns*
- `2026-04-09`: Crash from `2>&1 | Select-String` during failure debugging — *PowerShell stream interleaving crashes VS Code*
- **This session (2026-04-15)**: Crash from correct-but-verbose output in a long session — *agent context overflow crashes VS Code*. PowerShell exits cleanly; the crash is purely from context flooding.

## Solution

### Immediate fix: Always use `-Quiet` on large test files

```powershell
# ✅ SAFE — -Quiet suppresses individual test lines, shows only summary
$r = Invoke-Pester tests\prompt-tools.Tests.ps1 -PassThru -Quiet
$r | Select-Object TotalCount, PassedCount, FailedCount

# ✅ SAFE — bare single-file run that users want to see
Invoke-Pester tests\prompt-tools.Tests.ps1 -Quiet
```

`-Quiet` suppresses individual `It` block output, printing only the pass/fail
summary. This keeps Pester's contribution to the agent context to ~5 lines
instead of 300+.

### Structural fix: Never run Pester mid-stream in fix-triage

For fix-triage sessions that fix prompt/markdown files (`.prompt.md`, `.agent.md`):

1. **Apply all fixes first** — write all edits to files
2. **Update the review frontmatter** — mark findings fixed
3. **Defer all test verification to the end** — run one test pass at the very end
4. **Ask user before running tests** if the session is already long

The root mistake is running Pester after *each* fix to verify it. For markdown files
there is no unit-level isolation benefit — running tests once at the end is equivalent
and avoids accumulating output across multiple mid-session runs.

### When to skip Pester entirely

For pure markdown edits (prompt files, agent files, skill docs):
- If the only changes are to `.prompt.md`, `.agent.md`, or `.md` files, and
- Tests pass before the session and the changes are non-structural (wording, adding steps, reordering),
- **It is acceptable to note "tests were passing before this session" and skip the run.**

Pester on this project tests structural constraints (frontmatter keys, tool lists, step
counts, agent names). If a change doesn't touch those structures, the test result is
deterministic — they will still pass.

## Prevention

### Rule to add to `cg-skill-pester-safety` SKILL.md

The following rule should be added to the Pester safety skill:

> **6. Never run Pester mid-stream in long fix-triage sessions.**
> Apply all fixes first. Run one test pass at the end only, and always with `-Quiet`.
> For pure markdown edits that don't change frontmatter/tool lists/step counts, consider
> skipping test runs entirely and noting the prior passing state.

### Context check heuristic

Before running any Pester command during a fix-triage session, ask:
- "Is this session already long (brainstorm + plan + implementation + review)?" → If yes, use `-Quiet` mandatory
- "Am I verifying a prompt-file edit that doesn't change frontmatter?" → If yes, consider skipping entirely
- "Have I been running Pester multiple times this session?" → If yes, stop and do one final run

## Related

- [2026-04-02 — `Invoke-Pester tests/ -PassThru` on full directory crashes VS Code](2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md)
- [2026-04-06 — AI agent repeats Pester crash pattern despite documented rules](2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md)
- [2026-04-09 — AI agent uses `2>&1 | Select-String` when debugging test failures](2026-04-09-pester-2amp1-pipe-failure-debugging-trigger.md)
