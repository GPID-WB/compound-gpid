---
plan: .cg-docs/plans/2026-04-17-structural-pester-crash-prevention-v2.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
  P1.9: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P2.9: fixed
  P2.10: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
  P3.6: fixed
  P3.7: fixed
  P3.8: fixed
  P3.9: fixed
---

## Review Report

**Review depth**: thorough
**Files reviewed**: 9 (current session changes; context-layer work covered separately)
**Findings**: 9 P1, 10 P2, 9 P3

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-data-quality + cg-code-quality] `tests/Run-Tests.ps1` lines 90–92 / `tests/run-tests-runner.Tests.ps1` line 154 — PS 5.1 `ConvertTo-Json` serializes single-element `@()` arrays as JSON objects, not arrays
  **Why**: `$filesArray` and `$failuresArray` are built with `@()` + `+=`. When either contains exactly one entry (a single-file `-File` run, or exactly one failure), `ConvertTo-Json` produces `"files": {...}` instead of `"files": [{...}]`. Agents calling `.Count` on the deserialized `files` or `failures` get `$null` instead of `1`. The schema test `$null -ne $json.failures` also passes silently for a `$null` result from an empty array.
  **Fix**: Replace `$filesArray = @()` / `$failuresArray = @()` with `[System.Collections.ArrayList]::new()` and use `.Add(...) | Out-Null` instead of `+=`. For the schema tests, wrap deserialized values: `@($json.files).Count` and use `($json.failures -is [array])` assertions.

- **[P1.2]** [cg-testing] `tests/run-tests-runner.Tests.ps1` — No regression test for `exit 1` on failure
  **Why**: `exit 1` is the single behavioral property CI depends on. If accidentally removed, every CI run reports success even when tests fail — silently. No static test verifies its presence.
  **Fix**: Add to the "artifact construction keywords" Describe block:
  ```powershell
  It "script exits with code 1 when failures are present" {
      ($runnerContent -match 'exit 1') | Should Be $true
  }
  ```

- **[P1.3]** [cg-version-control] `tests/run-tests-runner.Tests.ps1` — untracked, not staged
  **Why**: Primary new test file for this feature. It is `??` in `git status` and will not be included in any commit or PR.
  **Fix**: `git add tests/run-tests-runner.Tests.ps1`

- **[P1.4]** [cg-version-control] `.cg-docs/plans/2026-04-17-*` and `.cg-docs/brainstorms/2026-04-17-*` — untracked
  **Why**: Three design-rationale files are untracked: the brainstorm, v1 plan (superseded), and v2 plan. `.cg-docs/` is tracked and these files contain the feature's design rationale. They will not appear in the PR.
  **Fix**: `git add .cg-docs/plans/2026-04-17-* .cg-docs/brainstorms/2026-04-17-*`

- **[P1.5]** [cg-adversarial] `tests/Run-Tests.ps1` lines 70–88 — `-File` with all-unregistered names produces `passed: true`, `totalCount: 0`
  **Why**: If `-File bogus-name` is passed, the warning goes to stderr and `$testNames` becomes an empty array. The loop runs zero iterations. Artifact is written with `passed: true`, `totalCount: 0`. An agent reads `passed: true` and proceeds to commit with zero tests executed.
  **Proof**: `. tests\Run-Tests.ps1 -File nonexistent` → `Get-Content tests\last-run.json | ConvertFrom-Json | Select-Object passed, totalCount` → `True, 0`
  **Fix**: After filtering, if `$testNames.Count -eq 0`, write an error artifact with `passed: false` and `error: "No registered test names matched the -File filter"` and exit 1.

- **[P1.6]** [cg-adversarial] `tests/Run-Tests.ps1` — `-File` partial run silently overwrites full-suite artifact
  **Why**: A `-File roadmap` run (80 passing tests) atomically overwrites the full-suite artifact. An agent at the commit gate reads `passed: true` — but 3 pre-existing failures still exist in the full suite. No `filteredFiles` field distinguishes a partial run from a full run.
  **Fix**: Add `filteredFiles` to the artifact: `filteredFiles = if ($File) { @($File) } else { $null }`. In SKILL.md and `cg-work.prompt.md` canonical pattern, add: "If `filteredFiles` is non-null, this is a partial run — do NOT use as the commit gate."

- **[P1.7]** [cg-adversarial] `.github/skills/cg-skill-pester-safety/SKILL.md` — `foreach` loop in "Safe Patterns — Interactive Debugging Only" section is accessible to agents
  **Why**: The "Interactive Debugging Only" label is a prose heading, not machine-enforced. An agent scanning the skill for "how to run multiple files" lands on the `foreach ($f in @(...)) { $r = Invoke-Pester ... }` block — a clean, well-formatted template it would copy. This is the exact failure mode this feature was built to prevent. `pester-safety.Tests.ps1` wouldn't catch it because the pattern passes the existing scanner.
  **Fix**: Remove the `foreach` loop example from the skill entirely. The skill's Safe Patterns section should contain only the single-file and single-`$r =` PassThru forms. Zero multi-file `Invoke-Pester` templates.

- **[P1.8]** [cg-data-quality] `tests/Run-Tests.ps1` lines 188–191 — No error handling on the artifact write path
  **Why**: `Set-Content $artifactTmp` and `Move-Item ... -Force` have no `try/catch`. On disk-full or permissions error, they fail silently. Agents reading `last-run.json` consume stale results from a previous run with no warning.
  **Fix**:
  ```powershell
  try {
      $artifact | ConvertTo-Json -Depth 4 | Set-Content $artifactTmp -Encoding UTF8
      Move-Item $artifactTmp $artifactPath -Force
  } catch {
      Write-Warning "WARNING: Failed to write test artifact: $_"
  }
  ```

- **[P1.9]** [cg-adversarial] `tests/Run-Tests.ps1` — No null-check on `$r` after `Invoke-Pester`; loop abort leaves artifact stale
  **Why**: If a test file causes `Invoke-Pester` to return `$null` (fatal load error — e.g., missing module at global scope), `$r.FailedCount` throws a "property on null" exception. The exception exits the `foreach` loop. The `ConvertTo-Json`/`Move-Item` block never executes. Agents read the previous run's (potentially stale or clean) artifact.
  **Fix**:
  ```powershell
  if ($null -eq $r) {
      Write-Host "  [ERROR] $name - Invoke-Pester returned null" -ForegroundColor Red
      $totalFailed += 1; $failedNames += $name; continue
  }
  ```
  Also wrap the artifact write in `try/catch` (see P1.8).

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing + cg-adversarial] `tests/run-tests-runner.Tests.ps1` — Schema tests don't validate `totalCount > 0` or array types
  **Why**: `($null -ne $json.files)` passes when `files` is a bare object (P1.1 coercion) or `$null` (P1.5 zero-test run). `$null -ne $json.totalCount` passes for `0`. No assertions catch a meaningless artifact.
  **Fix**: Add assertions:
  ```powershell
  It "last-run.json totalCount is greater than 0" { $json.totalCount | Should BeGreaterThan 0 }
  It "last-run.json totalCount equals passedCount plus failedCount" {
      ($json.passedCount + $json.failedCount) | Should Be $json.totalCount
  }
  It "last-run.json files is an array type" { ($json.files -is [array]) | Should Be $true }
  It "last-run.json failures is an array type" { ($json.failures -is [array]) | Should Be $true }
  ```

- **[P2.2]** [cg-testing] `tests/run-tests-runner.Tests.ps1` — No test for undeclared-file detection logic
  **Why**: `Run-Tests.ps1` lines ~167–174 scan `tests/` for `.Tests.ps1` files not in `$testNames` and emit a warning. If this guard is removed, new test files silently stop running.
  **Fix**:
  ```powershell
  It "script detects undeclared test files not in `$testNames" {
      ($runnerContent -match 'Get-ChildItem.*Tests.*ps1') | Should Be $true
  }
  It "script warns about undeclared test files" {
      ($runnerContent -match 'undeclared') | Should Be $true
  }
  ```

- **[P2.3]** [cg-testing] `tests/run-tests-runner.Tests.ps1` — No test for unregistered `-File` name warning
  **Why**: R7 requires a warning when a `-File` name is not in `$testNames`. If removed, callers silently get zero results with no feedback.
  **Fix**:
  ```powershell
  It "warns when a -File name is not registered in `$testNames" {
      ($runnerContent -match 'Write-Warning.*not a registered test name') | Should Be $true
  }
  ```

- **[P2.4]** [cg-testing] `tests/Run-Tests.ps1` / `tests/run-tests-runner.Tests.ps1` — `$skippedNames` absent from artifact
  **Why**: Files not found on disk are tracked in `$skippedNames` and shown in console as `[SKIP]`, but not in the artifact. Agents reading `last-run.json` can't detect that a file-not-found skip occurred.
  **Fix**: Add `skipped = $skippedNames` to the artifact object. Add a schema test.

- **[P2.5]** [cg-architecture] `tests/prompt-tools.Tests.ps1` — No regression tests for SKILL.md Agent Workflow section or `copilot-instructions.md` Rule 9
  **Why**: The three prompts (`cg-work`, `cg-fix-triage`, `cg-diagnose`) have regression tests, but the two documentation-authority components have none. If `cg-skill-pester-safety/SKILL.md` loses its "Agent Workflow" section or `copilot-instructions.md` loses Rule 9, no test fails — while the prompts stay protected.
  **Fix**: Add two Describe blocks to `prompt-tools.Tests.ps1` checking co-presence of `execution_subagent` + `Run-Tests.ps1` + `last-run.json` in the skill file, and `Agent test workflow` + `execution_subagent` + `last-run.json` in `copilot-instructions.md`.

- **[P2.6]** [cg-code-quality] `tests/Run-Tests.ps1` — `exit 1` terminates interactive dot-source session
  **Why**: When dot-sourced interactively (`. tests\Run-Tests.ps1`), `exit 1` on failure closes the user's PowerShell terminal. The `execution_subagent` and VS Code task both use subprocesses so `exit 1` is correct for them, but interactive use (the documented pattern) loses the session.
  **Fix**: Replace `exit 1` with `$global:LASTEXITCODE = 1; return`. Subagents and CI detect failure via `$LASTEXITCODE`; interactive sessions are not terminated.

- **[P2.7]** [cg-documentation + cg-code-quality] `.github/skills/cg-skill-pester-safety/SKILL.md` — `foreach` loop stale (missing `helpers` and `run-tests-runner`)
  **Why**: The interactive `foreach` loop in Safe Patterns hardcodes the test names array but omits both `helpers` (pre-existing) and `run-tests-runner` (added this session). A developer copying this loop silently skips both files. (P1.7 recommends removing the loop entirely — fix P1.7 first; P2.7 is resolved automatically if the loop is removed.)
  **Fix**: If P1.7 is applied (remove the loop), P2.7 is automatically resolved. If the loop is kept, add `'helpers'` after `'charter'` and `'run-tests-runner'` after `'create-release'`.

- **[P2.8]** [cg-version-control] `roadmap.json`, `scripts/helpers.ps1`, `scripts/update.ps1` — unstaged local changes
  **Why**: These three files show in both `git diff main` (committed on the branch) and `git status` (additional uncommitted delta). The uncommitted changes are invisible to reviewers and won't be in the PR. `scripts/helpers.ps1` and `scripts/update.ps1` have known non-ASCII characters causing pre-existing ps51-compat test failures.
  **Fix**: `git diff -- roadmap.json scripts/helpers.ps1 scripts/update.ps1`. If changes belong to this session, stage them. If unrelated, stash or commit separately.

- **[P2.9]** [cg-adversarial] `tests/pester-safety.Tests.ps1` — Pattern 3 misses backtick-continued `Invoke-Pester -PassThru |` pipelines
  **Why**: Pattern 3 splits on `\r?\n` and checks each line. A backtick-continued line `Invoke-Pester tests/foo.Tests.ps1 \`` / `-PassThru | Select-Object ...` spans two lines. Neither line individually matches the pattern.
  **Fix**: Before running Pattern 3, normalize backtick continuations: `$normalized = ($content -replace '`\r?\n\s*', ' ')`, then split and scan `$normalized`.

- **[P2.10]** [cg-adversarial] `.github/skills/cg-skill-pester-safety/SKILL.md` — Frontmatter description names `foreach` loop as a "feature"
  **Why**: The `description` field in the skill's YAML frontmatter includes "the sequential foreach loop for multi-file verification". This text is surfaced in the Copilot skills index before the full file is loaded. It primes agents to look for and apply that pattern — undermining the "execution_subagent only" message.
  **Fix**: Remove the foreach reference from the description field. Replace with "long-session context-overflow protection rules" to describe what that section covers.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-data-quality] `tests/Run-Tests.ps1` line 187 — `failFast` proxy semantics incorrect when the last file fails
  **Why**: `failFast = [bool]($FailFast -and $totalFailed -gt 0)` is true even when the last file is the failing one (no early `break` happened). A proper `earlyExit` flag would track the `break`.
  **Fix**: Add `$earlyExit = $false` before the loop; set `$earlyExit = $true` inside the `if ($FailFast) { break }` block. Use `failFast = [bool]$earlyExit` in the artifact.

- **[P3.2]** [cg-code-quality] `.github/skills/cg-skill-pester-safety/SKILL.md` — Crash count stale
  **Why**: The banner says "crashes VS Code 12+ confirmed times". `copilot-instructions.md` and user memory say 17+.
  **Fix**: Update banner to "16+".

- **[P3.3]** [cg-code-quality] `.github/prompts/cg-diagnose.prompt.md` — Category A recovery block has doubled label
  **Why**: "Verify the test suite (do NOT use `Invoke-Pester` directly):" appears as inline prose and then again as a bold heading on the next line.
  **Fix**: Remove the inline prose occurrence; keep only the bold heading.

- **[P3.4]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` lines 2038+ — `$content` variable shadowing
  **Why**: The three new Describe blocks all use `$content`, a name used throughout the 2000+ line file. Functionally correct in Pester 3.4 but fragile to reorganization.
  **Fix**: Rename to `$cgWorkContent`, `$cgFixTriageContent`, `$cgDiagnoseContent`.

- **[P3.5]** [cg-documentation] `tests/Run-Tests.ps1` — Stale review-finding reference `(P2.5: prevents silent omissions)`
  **Why**: The undeclared-file warning comment references an internal review finding ID meaningless without the original review document.
  **Fix**: Replace with: `# Prevents silent coverage gaps when a new .Tests.ps1 file is added without registering it.`

- **[P3.6]** [cg-documentation] `tests/Run-Tests.ps1` — Atomic write pattern lacks inline rationale
  **Why**: The `Set-Content $artifactTmp` → `Move-Item` site has no inline comment explaining why atomic.
  **Fix**: Add: `# Write to tmp first, then rename -- prevents agents from reading a partial artifact mid-write.`

- **[P3.7]** [cg-documentation] `tests/run-tests-runner.Tests.ps1` — "Skipped gracefully" is misleading in Pester 3.4
  **Why**: Pester 3.4 has no native Skip. The placeholder It block shows as a pass, not a skip.
  **Fix**: Update the comment: "Falls back to a single placeholder passing test when no artifact exists (Pester 3.4 has no Skip -- first run shows 1 pass, not a skip)."

- **[P3.8]** [cg-reproducibility] `tests/Run-Tests.ps1` — `Set-Content -Encoding UTF8` writes BOM in PS 5.1
  **Why**: PS 5.1's `Set-Content -Encoding UTF8` prepends a UTF-8 BOM. PowerShell consumers auto-strip it, but any out-of-PowerShell consumer (Python, `jq`, VS Code extension) sees a corrupted first character.
  **Fix**: Use `[System.IO.File]::WriteAllText($artifactTmp, ($artifact | ConvertTo-Json -Depth 4))` for BOM-less UTF-8.

- **[P3.9]** [cg-adversarial] `tests/run-tests-runner.Tests.ps1` — `ranAt` not validated for ISO format
  **Why**: `$null -ne $json.ranAt` passes for any non-null value, including a malformed timestamp.
  **Fix**:
  ```powershell
  It "last-run.json ranAt is a valid ISO 8601 UTC timestamp" {
      ($json.ranAt -match '^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$') | Should Be $true
  }
  ```

---

### ✅ Passed

- `@cg-performance`: No performance issues. Array `+=` is O(n²) but bounded to ~13 iterations — not worth changing.
- `@cg-reproducibility`: `ranAt` UTC format is timezone-safe. All paths use `$PSScriptRoot`/`$repoRoot` — no hardcoded absolute paths. git fallback to `"unknown"` is correct.
- `@cg-code-quality`: `cg-work.prompt.md`, `cg-fix-triage.prompt.md`, `copilot-instructions.md`, and `.gitignore` have no issues.
- `@cg-learnings-researcher`: PS 5.1 array coercion is a known issue (documented in `.cg-docs/solutions/bugs/`). The dotall-flag lesson is already handled correctly. The Pester 3.4 em-dash constraint is handled. The subprocess-isolation exemption is correctly documented and tested.
