---
date: 2026-04-02
title: "Invoke-Pester on full test directory with -PassThru pipeline crashes VS Code"
category: "testing-patterns"
language: "both"
tags: [powershell, pester, vscode, crash, passthru, pipeline, junctions, agent, copilot]
root-cause: "Running Invoke-Pester on the entire tests/ directory with -PassThru and a complex pipeline triggers junction-cleanup hang (all junction-creating tests fire at once) and/or exhausts the PowerShell extension memory with a large result object"
severity: "P1"
---

# `Invoke-Pester tests/ -PassThru` on Full Directory Crashes VS Code

## Problem

VS Code crashes and requires a manual restart when the agent (or user) runs Pester
against the entire `tests/` directory with the `-PassThru` flag followed by a
multi-stage pipeline:

```powershell
# CRASHES VS CODE — do not use
Invoke-Pester tests/ -PassThru |
  Select-Object -ExpandProperty TestResult |
  Where-Object { $_.Result -ne "Passed" } |
  Format-Table Result, Name -AutoSize
```

This crash happened **four confirmed times** in the `strategy` branch fix-triage
session (2026-04-02). Each occurrence required a VS Code restart.

**Recurrence (2026-04-06):** Crashed again during the `vision1` branch fix-triage
session — four additional times. The agent used both `Invoke-Pester tests/ -PassThru`
(directory form) and `Invoke-Pester ..., ... -PassThru | Select-Object -ExpandProperty
TestResult | Where-Object ...` (multi-file + ExpandProperty pipeline). Recurrence
confirms the pattern as reliably dangerous, not edge-case behaviour.

Symptoms:
- VS Code becomes unresponsive during or immediately after the Pester run
- Terminal hangs with no output, or output is produced but VS Code then freezes
- No error message — silent crash requiring force-quit or restart
- Restart immediately re-enables normal operation (no persistent state damage)

## Root Cause

Two compounding factors:

**Factor 1 — Running `tests/` (directory) fires all test files including junction-creating tests.**
This project's `tests/` directory contains `link.Tests.ps1` and `unlink.Tests.ps1`,
which create directory junctions as part of testing the `cg-link` / `cg-unlink`
scripts. Even with `AfterAll` cleanup blocks added as a fix for the known
junction-freeze issue (see Related), running the full suite at once increases the
likelihood that junction cleanup is still in flight when Pester's own `$TestDrive`
cleanup fires — or that multiple junction-creating test files interact unexpectedly.

**Factor 2 — `-PassThru` materialises all test results as .NET objects in memory.**
With 9 test files, each containing multiple `Describe` / `It` blocks, `-PassThru`
returns a large `[Pester.Run]` object. Piping it through `Select-Object -ExpandProperty
TestResult` then `Where-Object` then `Format-Table` keeps the entire result graph
alive in the PowerShell extension process. On large suites this can exhaust the
Language Server's working set, causing the extension host to crash VS Code.

Either factor alone may be sufficient to crash; together they are reliably
problematic.

## Solution

**Never run `Invoke-Pester <directory>` on this workspace. Run individual test files.**

```powershell
# SAFE — single file, quiet output
Invoke-Pester tests/charter.Tests.ps1 -Quiet
Invoke-Pester tests/roadmap.Tests.ps1 -Quiet
Invoke-Pester tests/prompt-tools.Tests.ps1 -Quiet
```

If you need to check for failures across multiple files, run them sequentially
with separate invocations — never as a batch with `-PassThru` pipelines:

```powershell
# SAFE — sequential single-file runs
foreach ($f in @('charter', 'roadmap', 'prompt-tools', 'link', 'unlink')) {
    Write-Host "`n=== $f ==="
    Invoke-Pester "tests/$f.Tests.ps1" -Quiet
}
```

Avoid `-PassThru` with multi-stage pipelines entirely unless you are running a
single, small, non-junction-creating test file.

## Prevention

**For agents (Copilot) invoking Pester in this workspace:**
- Always run individual `*.Tests.ps1` files, never `Invoke-Pester tests/`
- Use `-Output Minimal` or `-Output Normal` — never `-PassThru | pipeline`
- When verifying a fix, only run the test file that covers the changed code

**For project contributors:**
- ✅ **Implemented 2026-04-06**: A **Pester Safety Rules** section was added to
  `.github/copilot-instructions.md` with the three forbidden patterns and three
  safe replacements. This file is auto-loaded into every Copilot session, so the
  agent will see the rules before writing any Pester command.
- ✅ **Implemented 2026-04-06 (Update 2)**: The same Pester safety rules were also
  added to `compound-gpid.local.md` under a `## Notes` section. This file is loaded
  into every session's user context, providing a second enforcement point independent
  of the project instructions. Dual-location documentation increases the chance that
  at least one copy is in the model's active context window at the time a Pester
  command is composed.
- If a full suite run is needed for CI, use GitHub Actions (not local agent terminal)

## Related

- [2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md](./2026-03-04-pester-testdrive-follows-junctions-freezes-vscode.md)
  — Root fix for the junction-cleanup freeze that this issue can re-trigger when
  the full test suite fires all junction-creating tests at once. Apply both fixes
  in tandem.
- [2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md](./2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md)
  — Why documenting the rule in a single file is insufficient; how dual-location
  documentation (copilot-instructions.md + compound-gpid.local.md) reduces recurrence.
- [2026-04-09-pester-2amp1-pipe-failure-debugging-trigger.md](./2026-04-09-pester-2amp1-pipe-failure-debugging-trigger.md)
  — Third recurrence: `2>&1 | Select-String` specifically triggered by failure-debugging
  mode, even when agent knows the rules. Rule #5 added to copilot-instructions.md.
