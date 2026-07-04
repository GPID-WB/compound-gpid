---
name: cg-skill-pester-safety
description: "Pre-flight safety rules for Pester (PowerShell test runner) in this workspace. ALWAYS load before writing any Invoke-Pester terminal command. Running Pester incorrectly crashes VS Code — this has happened 16+ times. Covers: forbidden patterns (directory runs, ExpandProperty TestResult pipelines, 2>&1 redirects), safe single-file patterns, safe PassThru patterns, long-session context-overflow protection rules (never run Pester mid-stream in fix-triage; always -Quiet on large test files), and the execution_subagent rule (use execution_subagent instead of run_in_terminal for Pester in long sessions — even -Quiet -PassThru via run_in_terminal crashes)."
---

# Pester Safety Rules for This Workspace

> **Load this skill before composing any `Invoke-Pester` command.**  
> Violations have crashed VS Code 16+ confirmed times. The crashes are silent — no error, just a frozen window requiring force-quit.

## Agent Workflow — Canonical Pattern

**Agents must use this pattern. Never compose `Invoke-Pester` commands directly.**

```
execution_subagent query:
  "In the repo root, run . tests\Run-Tests.ps1 (no flags, no pipeline).
   Then run: Get-Content tests\last-run.json | ConvertFrom-Json |
   Select-Object passed, failedCount, failures
   Return only those three fields."
```

Read `tests/last-run.json` for results:
- `passed: true` → all tests passed; continue
- `passed: false` → check `failures` array for `file`, `describe`, `name`, `message`
- `filteredFiles: non-null` → this is a partial run — do NOT use as the commit gate; run the full suite first

For single-file runs (testing one module during a step):
```
execution_subagent query:
  "In the repo root, run . tests\Run-Tests.ps1 -File <test-name>
   (no other flags, no pipeline).
   Then run: Get-Content tests\last-run.json | ConvertFrom-Json |
   Select-Object passed, failedCount, failures
   Return only those three fields."
```

The artifact `tests/last-run.json` is written atomically after every run and contains:
`gitSha`, `ranAt`, `passed`, `totalCount`, `passedCount`, `failedCount`, `failFast`, `filteredFiles`, `files[]`, `failures[]`

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

# ❌ CRASHES VS CODE — pipelining Invoke-Pester output through 2>&1
Invoke-Pester tests/foo.Tests.ps1 2>&1 | Select-String -Pattern 'FAIL|fail' | ...
```

**Why these crash:** `-ExpandProperty TestResult` materialises the full Pester result graph as .NET objects in the PowerShell extension host. On suites with junction-creating tests (`link.Tests.ps1`, `unlink.Tests.ps1`), this combines with junction-cleanup timing to exhaust the extension host and freeze VS Code. Pipelining through `2>&1` redirects the error stream into the same pipeline, causing interleaved object serialization that overwhelms the extension host — even on single-file runs of large test files (300+ tests).

## Safe Patterns — Interactive Debugging Only

> **These patterns are for interactive debugging only — never for agent workflows.**
> Agents must use the canonical `execution_subagent` pattern above.

### Canonical full-suite runner (interactive use)

```powershell
. tests\Run-Tests.ps1
```

`tests/Run-Tests.ps1` runs every file in safe order, shows per-file pass/fail counts, and lists the re-run command for any failed file. It enforces all three safety rules by construction — no one needs to remember them.

VS Code shortcut: `Ctrl+Shift+P` → **Tasks: Run Task** → **Run all Pester tests (safe)**

### Single file

```powershell
# Full output (shows each It block result)
Invoke-Pester tests/roadmap.Tests.ps1

# Quiet (shows only pass/fail counts)
Invoke-Pester tests/roadmap.Tests.ps1 -Quiet
```

> ⚠️ **Pester 3.4 note**: `-Output Minimal` and `-Output None` are **Pester 5 flags** and fail on Pester 3.4 (Windows built-in) with "ambiguous parameter". Use `-Quiet` instead.

### Single file with PassThru (when you need counts)

```powershell
$r = Invoke-Pester tests/roadmap.Tests.ps1 -PassThru -Quiet
$r | Select-Object TotalCount, PassedCount, FailedCount
```

**Critical**: Assign to `$r` first. **Never** pipeline `Invoke-Pester` output directly into `Select-Object` or `Where-Object`.

## Pre-Flight Checklist

Before submitting any `Invoke-Pester` command, verify:

- [ ] Not `Invoke-Pester tests/` (directory form)
- [ ] Not `-PassThru | Select-Object -ExpandProperty TestResult`
- [ ] Not `-PassThru | Where-Object`
- [ ] Not `Invoke-Pester ... 2>&1 | ...` (2>&1 redirect piped to anything)
- [ ] Single file OR sequential `foreach` loop
- [ ] If using `-PassThru`, result is stored in `$r` first
- [ ] Large test files (`prompt-tools.Tests.ps1`, 300+ blocks) always use `-Quiet` (no bare verbose run mid-session)
- [ ] Not running Pester mid-stream in a long fix-triage session (apply all fixes first, run once at the end)

### Safe pattern for finding failing test details

Do NOT use `2>&1 | Select-String` to grep for failures. Instead:
```powershell
$r = Invoke-Pester tests/foo.Tests.ps1 -PassThru -Quiet
$r | Select-Object TotalCount, PassedCount, FailedCount
# If failures: re-run without -Quiet to see each It block result
if ($r.FailedCount -gt 0) { Invoke-Pester tests/foo.Tests.ps1 }
```

## Test Files in This Workspace

| File | Creates junctions? | Notes |
|------|-------------------|-------|
| `charter.Tests.ps1` | No | Safe, fast |
| `roadmap.Tests.ps1` | No | Safe, fast |
| `prompt-tools.Tests.ps1` | No | Safe, fast |
| `model-assignments.Tests.ps1` | No | Safe, fast |
| `pester-safety.Tests.ps1` | No | Meta-test — scans other test files for forbidden patterns |
| `install.Tests.ps1` | No | Safe |
| `ps51-compat.Tests.ps1` | No | Safe |
| `create-release.Tests.ps1` | No | Safe |
| `run-tests-runner.Tests.ps1` | No | Tests Run-Tests.ps1 static properties and last-run.json schema |
| `update.Tests.ps1` | No | Safe |
| `link.Tests.ps1` | **Yes** | Run last; has `AfterAll` cleanup |
| `unlink.Tests.ps1` | **Yes** | Run last; has `AfterAll` cleanup |

Run junction-creating tests (`link`, `unlink`) last and in isolation.

## Long Sessions — Extra Caution

In a long fix-triage session (accumulated brainstorm + plan + implementation + review context), Pester output can flood the agent context window even when the PowerShell command exits cleanly. VS Code crashes from context overflow, not from PowerShell itself.

**Rules for long sessions:**
1. Always use `-Quiet` — never run large test files (`prompt-tools.Tests.ps1`) without it
2. Apply all fixes first, then run ONE test pass at the very end
3. For pure markdown edits (`.prompt.md`, `.agent.md`) that don't change frontmatter/tool lists/step counts, consider skipping the test run and noting "tests were passing before this session"
4. **Use `execution_subagent` instead of `run_in_terminal` for Pester in long sessions** — even `-Quiet -PassThru` via `run_in_terminal` injects terminal output into the agent context; `execution_subagent` returns only a summary and never floods context (crashes #15+16, 2026-04-15)

**Decision tree for choosing how to run Pester:**
- **Agent workflow (always)** → use `execution_subagent` + `Run-Tests.ps1` + read `last-run.json` (see Canonical Pattern above)
- Short interactive session + small test file (< 100 tests) → `run_in_terminal` with `-Quiet -PassThru` is OK
- Long interactive session OR large test file (300+ tests) → **use `execution_subagent`**
- Any session + `prompt-tools.Tests.ps1` → **always use `execution_subagent`**

## `prompt-tools.Tests.ps1` — Regex Test Quality Anti-Patterns

When writing or reviewing `-match` assertions in `prompt-tools.Tests.ps1`, watch for these three failure modes. Each produces a permanently-green test that covers less than it claims.

### 1. Dead arm from typo (born broken)

A misspelled alternation arm never matches — the test passes via a sibling arm. Invisible at code review because the spelling looks plausible.

```powershell
# ❌ 'fall back' never matches 'falls back to plan policy'
($content -match 'warn.*plan policy|fall back.*plan') | Should -Be $true

# ✅ Derived directly from the prompt text
($content -match 'warn.*plan policy|falls back.*plan') | Should -Be $true
```

**Prevention**: Before writing an arm, read the actual prompt line and copy the exact wording. Then verify each arm in isolation. See `.cg-docs/solutions/testing-patterns/2026-06-12-regex-arm-dead-from-inception-typo-passes-via-sibling.md`.

### 2. Always-true first arm (first branch swallows everything)

The first arm matches all inputs that satisfy the test intent, so later arms are never evaluated. `Forget` can be deleted from the prompt and the test still passes.

```powershell
# ❌ Ignore.*Override always matches; Override.*Forget is never required
($content -match 'Ignore.*Override|Override.*Forget') | Should -Be $true

# ✅ Each word asserted independently
($content -match 'Ignore') | Should -Be $true
($content -match 'Override') | Should -Be $true
($content -match 'Forget') | Should -Be $true
```

See `.cg-docs/solutions/testing-patterns/2026-05-01-regex-alternation-masks-coverage-split-into-independent-assertions.md`.

### 3. Stale arm after prompt refactoring (was correct, now dead)

An arm was valid at creation time. After the prompt text changed, the arm no longer matches — but the test passes via a surviving sibling arm. The dead arm may accidentally rescue the test if the surviving arm is later removed.

**Prevention**: After any prompt refactor, re-derive all related regex patterns from the new text rather than minimally editing old ones. See `.cg-docs/solutions/testing-patterns/2026-05-05-stale-alternation-after-prompt-refactoring.md`.

### General rule

For all three variants: **test each alternation arm independently before committing**. A passing combined test does not prove all arms match.

---

## Related

- `.cg-docs/solutions/testing-patterns/2026-04-02-invoke-pester-full-suite-passthru-crashes-vscode.md` — Full diagnosis and root cause
- `.cg-docs/solutions/testing-patterns/2026-04-06-ai-agent-ignores-pester-rules-despite-documentation.md` — Why single-location documentation is insufficient; dual-location strategy
- `.cg-docs/solutions/testing-patterns/2026-04-15-pester-verbose-output-floods-context-long-session.md` — Context overflow crash even with safe PowerShell patterns; fix-triage long-session guidance
- `.cg-docs/solutions/testing-patterns/2026-06-12-regex-arm-dead-from-inception-typo-passes-via-sibling.md` — Typo variant: dead-from-inception arm; prevention checklist

## PowerShell Helper Anti-Patterns

### `Where-Object` returns `PSObject[]` — never pass directly to .NET string methods

`Where-Object` always returns a collection (`PSObject[]`), even when only one element matches. Passing the result directly to a .NET method expecting `[string]` triggers implicit `.ToString()` which joins elements with spaces — producing garbled output with no error:

```powershell
# ❌ WRONG — $line is PSObject[]; [regex]::Matches() coerces to space-joined string
$line = ($text -split '\r?\n' | Where-Object { $_ -match '^\s*tools:' })
$tokens = [regex]::Matches($line, "['\"](\w+)['\"]")   # silently merges duplicate lines

# ✅ CORRECT — Select-Object -First 1 forces scalar, deduplicates duplicate keys
$line = ($text -split '\r?\n' | Where-Object { $_ -match '^\s*tools:' } | Select-Object -First 1)
$tokens = [regex]::Matches($line, "['\"](\w+)['\"]")
```

**Rule**: Always add `| Select-Object -First 1` after `Where-Object` before passing to any .NET method that expects a `[string]`.
