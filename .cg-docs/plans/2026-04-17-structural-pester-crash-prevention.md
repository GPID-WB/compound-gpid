---
date: 2026-04-17
title: "Structural prevention of agent-caused Pester crashes"
status: superseded
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-04-17-structural-pester-crash-prevention.md"
language: "both"
estimated-effort: "medium"
tags: [pester, crash-prevention, agent-safety, testing, powershell, run-tests, json-artifact]
---

# Plan: Structural Prevention of Agent-Caused Pester Crashes

## Objective

Eliminate the two failure modes that have caused 18+ VS Code crashes from
agent-composed Pester commands. Category A (72%): agents compose forbidden
`Invoke-Pester` patterns after context compaction. Category B (28%): even safe
patterns flood the agent context window in long sessions with 300+ lines of test
output. The solution makes it architecturally unnecessary for agents to compose
`Invoke-Pester` commands and decouples test results from agent context via a
bounded JSON artifact.

## Context

**What exists today:**
- `tests/Run-Tests.ps1` — safe sequential runner that loops over individual test
  files using `-PassThru -Quiet` and reports per-file pass/fail counts. It outputs
  to the terminal only — no structured artifact.
- `cg-skill-pester-safety/SKILL.md` — comprehensive safety documentation with
  forbidden patterns, safe patterns, pre-flight checklist, and decision tree.
- `copilot-instructions.md` — 8-rule Pester Safety section at the top of file.
- `compound-gpid.local.md` — notes section with safety rules.
- `/memories/pester-safety-critical.md` — persistent user memory note.
- `pester-safety.Tests.ps1` — meta-tests scanning test files for forbidden patterns.

**What's missing:**
- No structured output from `Run-Tests.ps1` — agents must parse terminal output.
- No literal copy-paste blocks in prompts — `/cg-work`, `/cg-fix-triage`, and
  `/cg-diagnose` give indirect instructions ("run tests") that let agents compose
  their own `Invoke-Pester` commands.
- No staleness detection — no way to verify test results correspond to current code.
- No single-file mode — agents run the full suite even for one-file changes.

**Brainstorm decision:** Approach 1 — Full Stack — JSON Artifact + Prompt Hardening.
Two-phase implementation: Phase 1 (script changes), Phase 2 (prompt hardening).

## Requirements

| ID  | Requirement                                                          | Source           |
|-----|----------------------------------------------------------------------|------------------|
| R1  | `Run-Tests.ps1` emits `tests/last-run.json` with bounded schema     | brainstorm       |
| R2  | Artifact includes `passed`, `totalCount`, `passedCount`, `failedCount`, per-file breakdown, and failures array | brainstorm |
| R3  | Failures array includes `file`, `describe`, `context`, `name`, `message` from Pester 3.4 `-PassThru` | brainstorm |
| R4  | Artifact includes `gitSha` (from `git rev-parse --short HEAD`) for staleness detection | brainstorm |
| R5  | Artifact includes `ranAt` timestamp for crash diagnosis              | brainstorm       |
| R6  | Atomic write-then-rename pattern (`.last-run.tmp` → `last-run.json`) | brainstorm      |
| R7  | `-File` parameter for single-file mode with junction-ordering enforcement | brainstorm    |
| R8  | `tests/last-run.json` and `tests/.last-run.tmp` added to `.gitignore` | brainstorm     |
| R9  | Prompts `/cg-work`, `/cg-fix-triage`, `/cg-diagnose` contain literal `execution_subagent` blocks | brainstorm |
| R10 | Literal blocks include `Invoke-Pester` prohibition adjacent to the safe command | brainstorm |
| R11 | Literal blocks include if-passed/if-failed decision logic inline     | brainstorm       |
| R12 | `cg-skill-pester-safety/SKILL.md` updated: artifact workflow is THE pattern; old `$r = Invoke-Pester` demoted to debugging-only | brainstorm |
| R13 | `copilot-instructions.md` Pester Safety section updated to reference `last-run.json` | brainstorm |
| R14 | `prompt-tools.Tests.ps1` gains tests verifying literal `execution_subagent` blocks exist in each hardened prompt | brainstorm |
| R15 | Tests for `-File` parameter behavior in Run-Tests.ps1                | brainstorm       |

## Implementation Steps

### Phase 1: Run-Tests.ps1 Upgrades (one session — commit before Phase 2)

#### 1. Add `-File` parameter to Run-Tests.ps1
- **Requirements**: R7
- **Files**: `tests/Run-Tests.ps1`
- **Details**:
  - Add `[string[]]$File` parameter to `param()` block alongside existing `[switch]$FailFast`.
  - When `-File` is provided, filter `$testNames` to only include the specified names.
  - Preserve junction-ordering: if the filtered list includes `link` or `unlink`,
    ensure they sort to the end regardless of the order provided.
  - If `-File` specifies a name not in `$testNames`, emit a warning:
    `"WARNING: '$name' is not a registered test name. Skipping."` and continue.
  - When `-File` is not provided, behavior is unchanged (run all tests).
- **Test Scenarios**:
  - ✅ Happy path: `-File prompt-tools` runs only prompt-tools
  - ✅ Happy path: `-File charter,roadmap` runs both in order
  - 🛑 Edge case: `-File link,charter` reorders to charter first, link last
  - ❌ Error path: `-File nonexistent` warns and skips
  - ✅ No `-File` → runs all tests (existing behavior unchanged)
- **Tests**: Add to a new test file `tests/run-tests-runner.Tests.ps1` or extend
  existing coverage in `prompt-tools.Tests.ps1` (prefer a new file since
  `prompt-tools.Tests.ps1` is already 2000+ lines).
  - **Decision**: Create `tests/run-tests-runner.Tests.ps1` — a dedicated file for
    testing `Run-Tests.ps1` functionality. Register it in `Run-Tests.ps1`'s
    `$testNames` array. This file tests the runner's parameters and artifact output,
    not prompts.
- **Acceptance criteria**: `Run-Tests.ps1 -File prompt-tools` runs only prompt-tools
  and produces correct output. `Run-Tests.ps1` with no args runs all tests as before.

#### 2. Build JSON artifact from Pester results
- **Requirements**: R1, R2, R3, R5
- **Files**: `tests/Run-Tests.ps1`
- **Details**:
  - After the test loop completes, build the artifact object:
    ```powershell
    $filesArray = @()  # built incrementally inside the foreach loop
    $failuresArray = @()  # built incrementally inside the foreach loop
    ```
  - Inside the existing `foreach ($name in $testNames)` loop, after each
    `$r = Invoke-Pester ...`, append to `$filesArray`:
    ```powershell
    $filesArray += [pscustomobject]@{
        name   = $name
        total  = $r.TotalCount
        passed = $r.PassedCount
        failed = $r.FailedCount
    }
    ```
  - For failed tests, extract failure details:
    ```powershell
    if ($r.FailedCount -gt 0) {
        $r.TestResult | Where-Object { -not $_.Passed } | ForEach-Object {
            $failuresArray += [pscustomobject]@{
                file     = $name
                describe = $_.Describe
                context  = $_.Context
                name     = $_.Name
                message  = $_.FailureMessage
            }
        }
    }
    ```
  - After the loop, build the top-level object:
    ```powershell
    $artifact = [pscustomobject]@{
        ranAt       = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
        passed      = ($totalFailed -eq 0)
        totalCount  = $totalPassed + $totalFailed
        passedCount = $totalPassed
        failedCount = $totalFailed
        files       = $filesArray
        failures    = $failuresArray
    }
    ```
  - Note: `gitSha` is added in Step 3 — keep artifact construction modular.
- **Test Scenarios**:
  - ✅ Happy path: all tests pass → `passed: true`, empty `failures` array
  - ✅ Happy path: some failures → `passed: false`, `failures` array populated with
    `describe`, `context`, `name`, `message`
  - 🛑 Edge case: `context` is empty string when test has no `Context` block
  - 🛑 Edge case: `-FailFast` stops early → artifact reflects only the files run
- **Tests**: In `run-tests-runner.Tests.ps1`, verify artifact schema fields exist
  and types are correct after a full run. Run a known-passing subset with `-File`
  to check artifact content.
- **Acceptance criteria**: `tests/last-run.json` is written after every run with
  the agreed schema.

#### 3. Add git SHA for staleness detection
- **Requirements**: R4
- **Files**: `tests/Run-Tests.ps1`
- **Details**:
  - Before the test loop, capture the git SHA:
    ```powershell
    $gitSha = (git -C $repoRoot rev-parse --short HEAD 2>$null)
    if (-not $gitSha) { $gitSha = "unknown" }
    ```
  - Add `gitSha = $gitSha` to the `$artifact` object.
  - The fallback to `"unknown"` handles the edge case where tests run outside a
    git repo (unlikely but defensive).
- **Test Scenarios**:
  - ✅ Happy path: `gitSha` matches `git rev-parse --short HEAD`
  - 🛑 Edge case: not in a git repo → `gitSha` is `"unknown"`
- **Tests**: In `run-tests-runner.Tests.ps1`, verify `gitSha` field exists and
  is a non-empty string.
- **Acceptance criteria**: `last-run.json` contains a `gitSha` field that matches
  the current HEAD.

#### 4. Implement atomic write-then-rename
- **Requirements**: R6
- **Files**: `tests/Run-Tests.ps1`
- **Details**:
  - Define paths at the top of the script (after `$repoRoot`):
    ```powershell
    $artifactPath = Join-Path $repoRoot "tests\last-run.json"
    $artifactTmp  = Join-Path $repoRoot "tests\.last-run.tmp"
    ```
  - After building `$artifact`, write atomically:
    ```powershell
    $artifact | ConvertTo-Json -Depth 4 | Set-Content $artifactTmp -Encoding UTF8
    Move-Item $artifactTmp $artifactPath -Force
    ```
  - `Move-Item` on the same volume is atomic (rename, not copy).
  - If the runner crashes before `Move-Item`, the agent gets either the previous
    valid artifact or no artifact — never a partial file.
- **Test Scenarios**:
  - ✅ Happy path: `last-run.json` is valid JSON after a run
  - ✅ Happy path: `.last-run.tmp` does not exist after a successful run
  - 🛑 Edge case: `last-run.json` from a previous run is overwritten cleanly
- **Tests**: In `run-tests-runner.Tests.ps1`, verify `last-run.json` exists after
  run, is valid JSON (`ConvertFrom-Json` succeeds), and `.last-run.tmp` does not
  exist.
- **Acceptance criteria**: After a successful run, only `last-run.json` exists (no
  `.tmp` file left behind). JSON is valid and parseable.

#### 5. Add .gitignore entries
- **Requirements**: R8
- **Files**: `.gitignore`
- **Details**:
  - Add under the existing "Testing & profiling" section:
    ```
    # Pester test runner artifact (session-local, not committed)
    tests/last-run.json
    tests/.last-run.tmp
    ```
- **Test Scenarios**:
  - ✅ `git status` does not show `tests/last-run.json` as untracked after a test run
- **Tests**: Can verify in `run-tests-runner.Tests.ps1` that the `.gitignore`
  contains the entries (regex match on file content).
- **Acceptance criteria**: Both files are in `.gitignore`.

#### 6. Register new test file and run full suite
- **Requirements**: R15
- **Files**: `tests/Run-Tests.ps1` (add `'run-tests-runner'` to `$testNames`),
  `tests/run-tests-runner.Tests.ps1` (new file)
- **Details**:
  - Create `tests/run-tests-runner.Tests.ps1` with all tests from Steps 1–5.
  - Add `'run-tests-runner'` to the `$testNames` array in `Run-Tests.ps1`,
    positioned before the junction-creating tests.
  - Run `. tests\Run-Tests.ps1` to verify everything passes.
- **Test Scenarios**:
  - ✅ `run-tests-runner` appears in `$testNames`
  - ✅ Full suite passes with the new test file included
- **Acceptance criteria**: `. tests\Run-Tests.ps1` reports all tests passing
  including the new `run-tests-runner` file.

**Phase 1 gate**: Commit and push all Phase 1 changes before starting Phase 2.

---

### Phase 2: Prompt Hardening (second session)

#### 7. Add literal `execution_subagent` block to `/cg-work`
- **Requirements**: R9, R10, R11
- **Files**: `.github/prompts/cg-work.prompt.md`
- **Details**:
  - In Step 2 item 4 ("Test"), replace the indirect "Run both the discovered
    existing tests AND the new tests" instruction with a literal block.
  - The block must contain:
    1. The exact `execution_subagent` query string
    2. An explicit `Invoke-Pester` prohibition adjacent to the command
    3. If-passed/if-failed decision logic inline
  - Template (adapted to cg-work's single-file-during-work / full-suite-before-commit pattern):

    ````markdown
    **Running tests** (do NOT use `Invoke-Pester` directly — always use `execution_subagent`):

    For the test file(s) covering this step:
    > **execution_subagent query**: "In the repo root, run
    > `. tests\Run-Tests.ps1 -File <test-name>` (no other flags, no pipeline).
    > Then run `Get-Content tests\last-run.json | ConvertFrom-Json |
    > Select-Object passed, failedCount, failures`. Return only those three fields."

    If `passed` is `true`: continue to the next step.
    If `passed` is `false`: read `failures` array and apply Test Failure Recovery below.
    ````

  - The existing Test Failure Recovery block stays — it handles the fix loop
    after failures are identified. Only the *invocation* changes.
  - At the full-suite gate (Step 3.6 or equivalent "run full suite before commit"
    point), add a second literal block using `Run-Tests.ps1` without `-File`.
- **Test Scenarios**:
  - ✅ Prompt contains `execution_subagent` instruction
  - ✅ Prompt contains `Invoke-Pester` prohibition adjacent to the block
  - ✅ Prompt contains `last-run.json` reference
  - ✅ Prompt contains `Run-Tests.ps1` reference
- **Tests**: Add to `prompt-tools.Tests.ps1` — see Step 11.
- **Acceptance criteria**: `/cg-work` contains a literal `execution_subagent` block
  with prohibition and decision logic.

#### 8. Add literal `execution_subagent` block to `/cg-fix-triage`
- **Requirements**: R9, R10, R11
- **Files**: `.github/prompts/cg-fix-triage.prompt.md`
- **Details**:
  - In Step 3 item 3 ("Verify the fix compiles/parses correctly"), replace the
    generic "run any available linter or test" with a literal block:

    ````markdown
    **Running tests** (do NOT use `Invoke-Pester` directly — always use `execution_subagent`):

    > **execution_subagent query**: "In the repo root, run `. tests\Run-Tests.ps1`
    > (no flags, no pipeline). Then run `Get-Content tests\last-run.json |
    > ConvertFrom-Json | Select-Object passed, failedCount, failures`.
    > Return only those three fields."

    If `passed` is `true`: mark the finding as fixed and continue.
    If `passed` is `false`: review `failures` — if the failure is unrelated to
    this finding, note it and continue; if related, the fix needs revision.
    ````

  - `/cg-fix-triage` always runs the full suite (it fixes across files), so no
    `-File` variant needed.
- **Test Scenarios**:
  - ✅ Prompt contains `execution_subagent` instruction
  - ✅ Prompt contains `Invoke-Pester` prohibition
  - ✅ Prompt contains `last-run.json` reference
- **Tests**: Add to `prompt-tools.Tests.ps1` — see Step 11.
- **Acceptance criteria**: `/cg-fix-triage` contains a literal `execution_subagent`
  block with prohibition and decision logic.

#### 9. Add literal `execution_subagent` block to `/cg-diagnose`
- **Requirements**: R9, R10, R11
- **Files**: `.github/prompts/cg-diagnose.prompt.md`
- **Details**:
  - In the recovery section (Category A and Category E), replace the
    `. tests\Run-Tests.ps1` references with a literal block:

    ````markdown
    **Verify test suite** (do NOT use `Invoke-Pester` directly):

    > **execution_subagent query**: "In the repo root, run `. tests\Run-Tests.ps1`
    > (no flags, no pipeline). Then run `Get-Content tests\last-run.json |
    > ConvertFrom-Json | Select-Object passed, failedCount, failures`.
    > Return only those three fields."

    If `passed` is `true`: codebase integrity confirmed.
    If `passed` is `false`: report failures to the user — these may be pre-existing
    or caused by the crash interrupting a mid-session edit.
    ````

  - Keep the existing safe pattern documentation in the "Known Crash Patterns
    Reference" section — that's educational reference, not an execution instruction.
- **Test Scenarios**:
  - ✅ Recovery sections contain `execution_subagent` instruction
  - ✅ Recovery sections contain `last-run.json` reference
- **Tests**: Add to `prompt-tools.Tests.ps1` — see Step 11.
- **Acceptance criteria**: `/cg-diagnose` recovery sections use literal blocks.

#### 10. Update safety documentation
- **Requirements**: R12, R13
- **Files**: `.github/skills/cg-skill-pester-safety/SKILL.md`,
  `.github/copilot-instructions.md`
- **Details**:
  - **`cg-skill-pester-safety/SKILL.md`**:
    - Add a new top-level section "Agent Workflow — Canonical Pattern" above the
      existing "Safe Patterns" section.
    - Document the new workflow: `execution_subagent` → `Run-Tests.ps1` →
      read `last-run.json` → act on `passed`/`failures`.
    - Demote the existing "Safe Patterns" section with a note:
      > "The patterns below are for **interactive debugging only** — never for
      > agent workflows. Agents must use the canonical pattern above."
    - Update the decision tree to remove `run_in_terminal` options for agents.
  - **`copilot-instructions.md`**:
    - In the Pester Safety Rules section, add a new rule 9:
      > "**Agent test workflow**: Agents must use `execution_subagent` to run
      > `. tests\Run-Tests.ps1` and read `tests/last-run.json` for results.
      > Never compose `Invoke-Pester` commands directly."
    - Reference `last-run.json` in the canonical full-suite runner section (rule 8).
- **Test Scenarios**:
  - ✅ Skill file contains "Agent Workflow" section
  - ✅ Skill file contains "last-run.json" reference
  - ✅ copilot-instructions.md contains "last-run.json" reference
- **Tests**: Regex checks in `prompt-tools.Tests.ps1` or `pester-safety.Tests.ps1`.
- **Acceptance criteria**: Both files updated with artifact-based workflow as
  the primary agent pattern.

#### 11. Add regression tests for literal blocks
- **Requirements**: R14
- **Files**: `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Add a new `Describe` block:
    `"Pester crash prevention — literal execution_subagent blocks in test-running prompts"`
  - For each of the three prompts (`cg-work`, `cg-fix-triage`, `cg-diagnose`),
    add tests using the established `Get-Content ... -Raw -Encoding UTF8` +
    regex pattern:
    1. Contains `execution_subagent` (the subagent instruction)
    2. Contains `Run-Tests.ps1` (the safe runner reference)
    3. Contains `last-run.json` (the artifact reference)
    4. Contains `Invoke-Pester` prohibition text (the adjacent warning)
  - Pattern for each test:
    ```powershell
    It "cg-work.prompt.md contains execution_subagent test block" {
        $content = Get-Content $cgWorkFile -Raw -Encoding UTF8
        ($content -match 'execution_subagent') | Should Be $true
    }
    It "cg-work.prompt.md references Run-Tests.ps1 in test block" {
        ($content -match 'Run-Tests\.ps1') | Should Be $true
    }
    It "cg-work.prompt.md references last-run.json artifact" {
        ($content -match 'last-run\.json') | Should Be $true
    }
    It "cg-work.prompt.md prohibits direct Invoke-Pester" {
        ($content -match 'do NOT use.*Invoke-Pester') | Should Be $true
    }
    ```
  - Repeat for `cg-fix-triage.prompt.md` and `cg-diagnose.prompt.md`.
  - This is ~12 `It` blocks (4 checks × 3 prompts).
- **Test Scenarios**:
  - ✅ All 12 tests pass after prompt hardening
  - 🛑 Edge case: if someone removes a literal block from a prompt, the test fails
  - ❌ Error path: if a prompt file doesn't exist, the test fails clearly
- **Tests**: Self-contained — this IS the test step.
- **Acceptance criteria**: All 12 regression tests pass. Removing a literal block
  from any of the three prompts causes a test failure.

#### 12. Run full suite and commit
- **Requirements**: All
- **Files**: All modified files
- **Details**:
  - Run `. tests\Run-Tests.ps1` via `execution_subagent`.
  - Verify all tests pass including the new regression tests.
  - Commit all Phase 2 changes.
- **Acceptance criteria**: Full suite green. All changes committed.

## Testing Strategy

**Two test files cover this feature:**

1. **`tests/run-tests-runner.Tests.ps1`** (new, Phase 1):
   - Tests `Run-Tests.ps1` `-File` parameter behavior
   - Tests `last-run.json` artifact schema, valid JSON, atomic write
   - Tests `gitSha` field presence
   - Tests `.gitignore` entries

2. **`tests/prompt-tools.Tests.ps1`** (extended, Phase 2):
   - Tests literal `execution_subagent` blocks exist in `/cg-work`,
     `/cg-fix-triage`, `/cg-diagnose`
   - Tests `Invoke-Pester` prohibition is adjacent in each prompt
   - Tests `last-run.json` reference in each prompt

**Existing tests that must still pass:**
- `pester-safety.Tests.ps1` — meta-tests scanning for forbidden patterns (no
  changes expected; the new `run-tests-runner.Tests.ps1` must also pass its scan)
- All other test files — no regressions expected

## Documentation Checklist

- [ ] `Run-Tests.ps1` header comment updated with `-File` parameter docs
- [ ] `cg-skill-pester-safety/SKILL.md` updated with artifact workflow
- [ ] `copilot-instructions.md` updated with rule 9
- [ ] Inline comments in `Run-Tests.ps1` for the artifact construction

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Pester 3.4 `.TestResult` doesn't expose `.Describe` as expected | Low (confirmed in brainstorm) | High — artifact schema broken | Test in Phase 1 Step 2; fall back to `.Name` only if `.Describe` is null |
| `ConvertTo-Json -Depth 4` serialization fails on complex Pester objects | Low | Medium — no artifact written | Only serialize simple `[pscustomobject]` values, never raw Pester result objects |
| Agent still composes `Invoke-Pester` despite literal blocks (context compaction) | Low (reduced from current high) | Medium — crash | Multiple reinforcement layers: literal block + prohibition + `copilot-instructions.md` + safety skill + memory note |
| `Move-Item` not truly atomic on some Windows configurations | Very low | Low — partial file | PS 5.1 `Move-Item` on same volume is a rename; only cross-volume moves are non-atomic |
| New `run-tests-runner.Tests.ps1` interferes with test ordering | Low | Low | Register before junction tests in `$testNames` |

## Out of Scope

- **Changing the test framework** — Pester 3.4 is the Windows built-in; no migration.
- **CI/CD integration** — `last-run.json` is a local session artifact, not a CI output.
- **`cg-fix-problems` agent changes** — the agent loads `cg-skill-pester-safety`
  but does not directly invoke Pester. If it starts doing so, a separate update
  is needed. Monitor during Phase 2.
- **User-facing test commands** — users never run tests; this is agent-only.
- **Pester 5 migration** — out of scope entirely.
