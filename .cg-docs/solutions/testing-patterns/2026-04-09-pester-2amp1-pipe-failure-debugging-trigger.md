---
date: 2026-04-09
title: "AI agent uses 2>&1 | Select-String when debugging test failures — crash trigger during failure investigation"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, vscode, crash, ai-agent, copilot, 2>&1, debugging, failure-inspection]
root-cause: "When an agent is in 'failure-debugging mode' (tests failing, trying to see error messages), it reaches for 2>&1 | Select-String as a natural grep-style filter — a pattern that crashes VS Code even on single-file runs"
severity: "P1"
---

# AI Agent Uses `2>&1 | Select-String` When Debugging Test Failures — Crashes VS Code

## Problem

VS Code crashed **multiple times in a single session** during a fix-triage cycle. The
agent had been told tests were failing and attempted to inspect error messages using:

```powershell
# ❌ CRASHES VS CODE — appeared 4+ times in the April 2026 crash session
Invoke-Pester tests\prompt-tools.Tests.ps1 2>&1 | Select-String -Pattern "FAIL|Expected|Should" | Select-Object -First 30 | ForEach-Object { $_.Line }
Invoke-Pester tests\prompt-tools.Tests.ps1 2>&1 | Select-String -Pattern 'FAIL|fail|\[-\]|Should' | Select-Object -First 15
Invoke-Pester tests\prompt-tools.Tests.ps1 2>&1 | Select-String -Pattern "FAIL|fail|Error|error|Should|Expected" | Select-Object -First 20 | Format-List
Invoke-Pester tests\prompt-tools.Tests.ps1 2>&1 | Select-String -Pattern "FAIL|Failed|Should|assert" | Select-Object -First 20 | Format-List Line
```

**What makes this session distinct from previous crashes:** The agent was actively
investigating the Pester crash problem itself — it knew the dangerous patterns —
yet still used the `2>&1 |` forbidden pattern when reasoning about how to see what
was wrong with specific failing tests. The rules were documented, the skill was loaded,
yet the pattern occurred anyway.

**The cognitive trigger:** "I have a failing test. How do I see the error message?"
→ The agent reaches for `2>&1 | Select-String` as the natural grep-equivalent for
filtering Pester output. This pull is strong enough to override documented safety
rules when the agent is focused on a debugging objective.

Cumulative crash count: **8+ confirmed VS Code crashes** across four sessions
(2026-04-02 × 4, 2026-04-06 × 4, 2026-04-09 × multiple).

## Root Cause

**Two compounding factors:**

**Factor 1 — The `2>&1` redirect pattern.** Redirecting stderr into stdout (`2>&1`)
and then piping through `Select-String` forces PowerShell to interleave the error
and output streams before filtering. On large test files (300+ It-blocks, like
`prompt-tools.Tests.ps1`), this interleaving overwhelms the VS Code extension host
even for single-file runs. The extension host crashes silently — no error message,
no warning.

**Factor 2 — "Failure debugging" as a cognitive override.** When the agent's goal
shifts from "run tests" to "understand why tests are failing," it reasons: "I need
to filter Pester output for the relevant error messages." The most direct translation
of that thought to PowerShell is `2>&1 | Select-String`. This pattern *feels*
correct and efficient — it is how you would grep log output in any shell. The
fact that it crashes VS Code is a non-obvious side effect that must be explicitly
overridden by a rule. Under goal-focus pressure, weakly-reinforced rules lose.

**Why this is different from prior sessions:**
- The physical mechanism was already documented (2026-04-02)
- Context-window dilution was already documented (2026-04-06)
- The dual-location documentation was already in place
- The `cg-skill-pester-safety` required-loading rule was already in copilot-instructions.md
- Yet the pattern still occurred because the **specific trigger** ("I need to see error details")
  was not addressed with an equally prominent **specific safe alternative**

## Solution

### Safe pattern for inspecting test failures

Do **not** use `2>&1 | Select-String`. Instead, use the two-phase approach:

```powershell
# Phase 1: Count failures (safe)
$r = Invoke-Pester tests/prompt-tools.Tests.ps1 -PassThru -Quiet
$r | Select-Object TotalCount, PassedCount, FailedCount

# Phase 2: If failures exist, re-run WITHOUT -Quiet to see each It block
if ($r.FailedCount -gt 0) {
    Invoke-Pester tests/prompt-tools.Tests.ps1
}
```

Phase 2 (bare single-file without `-Quiet`) prints each test name with PASSED/FAILED
inline, which is exactly the error context needed — without the `2>&1` redirect that
crashes VS Code.

### Why the two-phase approach works

The bare `Invoke-Pester tests/file.Tests.ps1` (no redirect, no pipeline, no `-PassThru`)
uses Pester's own output formatter, which writes directly to the terminal host. There
is no interleaved stream merging. The extension host receives structured terminal
output, not a mixed .NET object stream. This is safe even for large test files.

### Canonical full-suite runner

When running the full suite, always use the safe runner script:

```powershell
. tests\Run-Tests.ps1
```

This script enforces all three safety rules by construction and shows per-file
pass/fail counts with re-run commands for failures.

## Prevention

### New rule added to copilot-instructions.md

```
5. **NEVER use `2>&1 | ...` pipelines from Invoke-Pester**:
   To inspect failures, re-run without `-Quiet`: `if ($r.FailedCount -gt 0) { Invoke-Pester tests/foo.Tests.ps1 }`
```

(See `.github/copilot-instructions.md` — Pester Safety Rules, rule #5.)

### Why this specific prevention works

The existing rule in `cg-skill-pester-safety` covered `2>&1 |` as a forbidden
pattern, but it was buried in a checklist. The new rule in `copilot-instructions.md`
is **numbered, prominent, and paired with the safe alternative** in the same line.
The pairing matters: the agent needs to know not just "don't do X" but "when you
want X, do Y instead."

### For future sessions

When you need to see WHY a test is failing:

| What you want | Safe command |
|--------------|-------------|
| Count failures | `$r = Invoke-Pester tests/foo.Tests.ps1 -PassThru -Quiet; $r \| Select-Object TotalCount, PassedCount, FailedCount` |
| See failure details | `if ($r.FailedCount -gt 0) { Invoke-Pester tests/foo.Tests.ps1 }` |
| Run full suite | `. tests\Run-Tests.ps1` |

**Never**: `Invoke-Pester ... 2>&1 | Select-String ...`
**Never**: `Invoke-Pester ... -PassThru | Select-Object -ExpandProperty TestResult | ...`
**Never**: `Invoke-Pester tests/` (directory form)

## Related

- [2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md](./2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md)
  — Physical crash mechanism (PassThru + full-suite pipeline + junction-creating tests)
- [2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md](./2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md)
  — Context window dilution as root cause of recurrence; dual-location documentation fix
- [2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md](./2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md)
  — Original junction-freeze bug that this pattern can re-trigger
