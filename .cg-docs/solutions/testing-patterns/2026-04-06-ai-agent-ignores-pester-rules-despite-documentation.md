---
date: 2026-04-06
title: "AI agent repeats Pester crash pattern despite documented rules — documentation alone is insufficient"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, vscode, crash, ai-agent, copilot, enforcement, context-window, safety-rules]
root-cause: "Rules documented only in copilot-instructions.md are not reliably retained in the model's active context window during long sessions, causing the agent to re-use forbidden Pester patterns"
severity: "P1"
---

# AI Agent Repeats Pester Crash Pattern Despite Documented Rules

## Problem

VS Code was crashed **multiple times in a single session** by the AI agent running
forbidden Pester patterns — even though the dangerous patterns were explicitly
documented in:

- `.github/copilot-instructions.md` (Pester Safety Rules section)
- `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md`

The agent used this pattern on each crash:

```powershell
# CRASHED VS CODE — appeared 4+ times across two fix-triage sessions
Invoke-Pester tests/charter.Tests.ps1, tests/link.Tests.ps1, tests/update.Tests.ps1 `
  -PassThru | Select-Object -ExpandProperty TestResult |
  Where-Object { $_.Result -ne 'Passed' } |
  Format-Table -AutoSize Name, Result, ErrorRecord
```

The rules had been written. The agent had processed them at session start. Yet the
same pattern recurred under "test verification" pressure — when the agent was focused
on confirming pass/fail results, the constraint in a non-prominent section of a large
instructions file was no longer in the active context window.

## Root Cause

**Context window dilution.** `copilot-instructions.md` is auto-loaded at session
start, but in a long session the instructions scroll out of close context as the
conversation grows. By the time the agent reaches the "run tests to verify" step
of a fix-triage cycle, the Pester rules may be far outside the effective token
window. The agent reasons from recent context (task: "verify tests pass") and
regenerates the most natural-looking Pester pattern — which is the dangerous one.

Two contributing factors:
1. The rule is buried mid-document among many other rules (not visually salient)
2. The agent has strong prior training to use `-ExpandProperty TestResult` when
   inspecting failures — that prior overrides a weakly-reinforced rule

## Solution

**Dual-location documentation with one location that is always near the top of context.**

Added the identical Pester safety rules to `compound-gpid.local.md`. This file is
structured to load near the beginning of every session and contains a dedicated
`## Notes` section. Because it is short (< 50 lines) and purpose-specific, the full
file is more reliably in the model's active context when Pester commands are generated.

```markdown
# In compound-gpid.local.md → ## Notes

### ⚠️ Pester Safety Rules (CRITICAL — violating these crashes VS Code)

1. Never run the full test suite as a directory: `Invoke-Pester tests/`
2. Never pipeline `-PassThru` output through `Select-Object -ExpandProperty TestResult`
3. Safe pattern (single file): `Invoke-Pester tests/roadmap.Tests.ps1 -Output Minimal`
4. Safe pattern (PassThru if needed): assign first, then inspect:
   $r = Invoke-Pester tests/roadmap.Tests.ps1 -PassThru -Output None
   $r | Select-Object TotalCount, PassedCount, FailedCount
```

The dual-location approach (instructions file + local config file) increases the
probability that at least one copy of the rule is in the model's active context
when it composes a Pester invocation.

## Prevention

**Enforce rules at multiple context layers, not just one.**

| Layer | File | When loaded |
|-------|------|-------------|
| System instructions | `.github/copilot-instructions.md` | Session start |
| User config | `compound-gpid.local.md` | Always visible in user context |
| Solution library | `.cg-docs/solutions/testing-patterns/` | On demand via cg-learnings-researcher |

**For agents (Copilot):** Before composing any `Invoke-Pester` command, mentally
verify:
- ❌ Not `Invoke-Pester tests/` (directory)
- ❌ Not `-PassThru | Select-Object -ExpandProperty TestResult`
- ✅ Individual file: `Invoke-Pester tests/FILE.Tests.ps1 -Output Minimal`
- ✅ PassThru summary: `$r = Invoke-Pester ...; $r | Select-Object TotalCount, PassedCount, FailedCount`

**General principle (any safety rule prone to recurrence):**
> If a rule appears in the system instructions but keeps being violated, add it to
> the shortest, most specific file that is always loaded near the top of context.
> `compound-gpid.local.md` is ideal for this project.

## Related

- [2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md](./2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md)
  — Primary crash diagnosis with root cause, safe patterns, and full prevention history
- [2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md](./2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md)
  — Original junction-freeze bug that interacts with this pattern
