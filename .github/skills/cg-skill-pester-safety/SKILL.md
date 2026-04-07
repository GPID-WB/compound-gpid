---
name: cg-skill-pester-safety
description: "Pre-flight safety rules for Pester (PowerShell test runner) in this workspace. ALWAYS load before writing any Invoke-Pester terminal command. Running Pester incorrectly crashes VS Code — this has happened 8+ times. Covers: forbidden patterns (directory runs, ExpandProperty TestResult pipelines), safe single-file patterns, safe PassThru patterns, and the sequential foreach loop for multi-file verification."
---

# Pester Safety Rules for This Workspace

> **Load this skill before composing any `Invoke-Pester` command.**  
> Violations have crashed VS Code 8+ confirmed times. The crashes are silent — no error, just a frozen window requiring force-quit.

## Forbidden Patterns — NEVER USE

```powershell
# ❌ CRASHES VS CODE — directory run
Invoke-Pester tests/

# ❌ CRASHES VS CODE — ExpandProperty TestResult pipeline
Invoke-Pester tests/foo.Tests.ps1 -PassThru | Select-Object -ExpandProperty TestResult | Where-Object ...

# ❌ CRASHES VS CODE — multi-file + ExpandProperty pipeline
Invoke-Pester tests/a.Tests.ps1, tests/b.Tests.ps1 -PassThru |
  Select-Object -ExpandProperty TestResult |
  Where-Object { $_.Result -ne 'Passed' } |
  Format-Table -AutoSize Name, Result, ErrorRecord
```

**Why these crash:** `-ExpandProperty TestResult` materialises the full Pester result graph as .NET objects in the PowerShell extension host. On suites with junction-creating tests (`link.Tests.ps1`, `unlink.Tests.ps1`), this combines with junction-cleanup timing to exhaust the extension host and freeze VS Code.

## Safe Patterns — ALWAYS USE THESE

### Single file (preferred)

```powershell
Invoke-Pester tests/roadmap.Tests.ps1 -Output Minimal
```

### Single file with PassThru (when you need counts)

```powershell
$r = Invoke-Pester tests/roadmap.Tests.ps1 -PassThru -Output None
$r | Select-Object TotalCount, PassedCount, FailedCount
```

**Critical**: Assign to `$r` first. **Never** pipeline `Invoke-Pester` output directly into `Select-Object` or `Where-Object`.

### Multiple files — run sequentially, one at a time

```powershell
foreach ($f in @('charter', 'roadmap', 'prompt-tools', 'install', 'link', 'unlink', 'update', 'ps51-compat', 'create-release')) {
    Write-Host "`n=== $f ===" -ForegroundColor Cyan
    Invoke-Pester "tests/$f.Tests.ps1" -Output Minimal
}
```

## Pre-Flight Checklist

Before submitting any `Invoke-Pester` command, verify:

- [ ] Not `Invoke-Pester tests/` (directory form)
- [ ] Not `-PassThru | Select-Object -ExpandProperty TestResult`
- [ ] Not `-PassThru | Where-Object`
- [ ] Single file OR sequential `foreach` loop
- [ ] If using `-PassThru`, result is stored in `$r` first

## Test Files in This Workspace

| File | Creates junctions? | Notes |
|------|-------------------|-------|
| `charter.Tests.ps1` | No | Safe, fast |
| `roadmap.Tests.ps1` | No | Safe, fast |
| `prompt-tools.Tests.ps1` | No | Safe, fast |
| `install.Tests.ps1` | No | Safe |
| `ps51-compat.Tests.ps1` | No | Safe |
| `create-release.Tests.ps1` | No | Safe |
| `link.Tests.ps1` | **Yes** | Run last; has `AfterAll` cleanup |
| `unlink.Tests.ps1` | **Yes** | Run last; has `AfterAll` cleanup |
| `update.Tests.ps1` | No | Safe |

Run junction-creating tests (`link`, `unlink`) last and in isolation.

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md` — Full diagnosis and root cause
- `.cg-docs/solutions/testing-patterns/2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md` — Why single-location documentation is insufficient; dual-location strategy
