---
date: 2026-04-17
title: "Canonical Run-Tests.ps1 + last-run.json artifact decouples test results from agent context window"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, vscode, crash, context-overflow, run-tests, json-artifact, execution-subagent, agent-safety, long-session, canonical-runner]
root-cause: "Agents composing Invoke-Pester commands directly — even with safe flags — risk context overflow in long sessions; a canonical runner that writes structured JSON lets agents read only counts and failures without injecting raw Pester output into their context"
severity: "P1"
---

# Canonical `Run-Tests.ps1` + `last-run.json` Artifact Decouples Test Results from Agent Context Window

## Problem

Despite 18+ documented VS Code crashes and a comprehensive `cg-skill-pester-safety`
skill, agents continued to compose `Invoke-Pester` commands directly. The failure
modes were:

**Category A (72% of crashes):** Agent composes a forbidden pattern after context
compaction (the safety rules are no longer in the active context window):
```powershell
# ❌ Crashes VS Code — forbidden patterns the agent "forgot"
Invoke-Pester tests/
Invoke-Pester ... | Select-Object -ExpandProperty TestResult
Invoke-Pester ... 2>&1 | Select-String ...
```

**Category B (28% of crashes):** Agent uses a technically-safe pattern but the
full Pester output floods the agent context window in a long session:
```powershell
# ❌ Still crashes in long sessions — raw output injected into context
$r = Invoke-Pester tests\prompt-tools.Tests.ps1 -PassThru -Quiet
$r | Select-Object TotalCount, PassedCount, FailedCount
```

The root problem is that any `Invoke-Pester` call returns or prints information
that goes through the agent's context window. For a 300-test file in a long
session, even the `-Quiet` summary is enough to tip over the limit.

## Root Cause

**Architectural gap**: agents had to *compose* `Invoke-Pester` commands from memory
to get test results. There was no safe, bounded mechanism for an agent to ask
"did the tests pass?" without knowing and correctly applying all the Pester safety
rules. Safety depended entirely on the agent remembering the rules, which failed
under context compaction.

**Output coupling**: test results were only available as terminal output injected
directly into the agent context. There was no artifact the agent could read
selectively.

## Solution

### Canonical runner: `tests/Run-Tests.ps1`

`Run-Tests.ps1` was upgraded to write a bounded JSON artifact after every run:

```powershell
# Writes: tests/last-run.json
# Format:
# {
#   "passed": 1057,
#   "failedCount": 1,
#   "failures": [
#     { "file": "prompt-tools", "describe": "...", "name": "...", "message": "..." }
#   ],
#   "timestamp": "2026-04-17T10:30:00"
# }
```

Agents read the artifact (not the runner output) to get bounded, structured results:

```powershell
Get-Content tests\last-run.json | ConvertFrom-Json |
    Select-Object passed, failedCount, failures
```

This returns ~5 lines even if 1,000 tests ran. The raw Pester output stays inside
the `execution_subagent` subprocess and never reaches the parent agent's context.

### Agent workflow (canonical pattern)

```
1. Use execution_subagent to run `. tests\Run-Tests.ps1`
2. Have the subagent read tests\last-run.json and return counts + failure names
3. Parent agent receives only the structured summary — never raw Pester output
```

This pattern is now hardcoded in `/cg-work`, `/cg-fix-triage`, and `/cg-diagnose`
prompts as literal copy-paste blocks with exact command strings — no agent
composition required.

### Why `execution_subagent` + JSON is better than `run_in_terminal` + `-Quiet`

| Method | Context injection | Safe in long session | Bounded output |
|--------|-------------------|----------------------|----------------|
| `run_in_terminal` (no flags) | All Pester output | No | No |
| `run_in_terminal -Quiet -PassThru` | Summary + PS status | Sometimes | No |
| `execution_subagent` (reads JSON) | Structured summary only | Yes | Yes (~5 lines) |

## Prevention

**Rule**: agents must never compose `Invoke-Pester` commands directly in any
session. The only allowed patterns are:

1. **Full suite**: `execution_subagent` → `. tests\Run-Tests.ps1` → read `tests\last-run.json`
2. **Single file** (exceptional): `execution_subagent` with the safe PassThru pattern
3. **Never**: `run_in_terminal` for Pester in any session with prior edits

The prompts (`/cg-work`, `/cg-fix-triage`, `/cg-diagnose`) now enforce this by
providing the exact command strings. The `cg-skill-pester-safety` SKILL.md includes
the canonical runner rule as Rule 8 and the `execution_subagent` rule as Rule 9.

## Related

- [2026-04-15 — Pester verbose output floods context in long sessions](2026-04-15-pester-verbose-output-floods-context-long-session.md) — the context overflow crash that motivated this fix
- [2026-04-06 — AI agent ignores Pester rules despite documentation](2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md) — why documentation alone is insufficient
- [2026-04-02 — Invoke-Pester full suite PassThru crashes VS Code](2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md) — the original crash doc
- `.cg-docs/plans/2026-04-17-structural-pester-crash-prevention-v2.md` — the design plan
- `.cg-docs/reviews/2026-04-17-structural-pester-crash-prevention-v2-review.md` — implementation review
- `tests/Run-Tests.ps1` — canonical runner implementation
- `tests/run-tests-runner.Tests.ps1` — tests for the runner itself
- `.cg-docs/solutions/testing-patterns/2026-07-31-review-artifacts-must-use-machine-readable-finding-maps-and-stable-validation-evidence.md` — follow-on rule: `tests/last-run.json` is safe as a bounded latest-run summary, not as immutable historical evidence in committed reports
