---
date: 2026-05-14
depth: light
parent-review: .cg-docs/reviews/2026-05-14-commit-push-pr-and-verify-pr-review.md
type: verification
findings:
  P1.1: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
  P2.7: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
---

# Verify Review: cg-commit-push-pr and cg-verify-pr

**Mode**: verification (following fix-triage on prior review)
**Parent review**: `.cg-docs/reviews/2026-05-14-commit-push-pr-and-verify-pr-review.md`
**Prior fixes confirmed**: 22 of 22 fixed findings correctly converged ✓
**New findings**: 12 (P1: 1, P2: 7, P3: 4)

---

## Review Report

**Review depth**: light (mode:verify)
**Files reviewed**: 8
**Findings**: 12 (P0: 0, P1: 1, P2: 7, P3: 4)

---

### P1 — CRITICAL (must fix before merge)

**[P1.1]** [cg-code-quality] `cg-verify-pr.prompt.md:Step 4 ("Commit and push fixes")` — `git add <fixed-files>` has no exit-code check
  **Why**: P1.1 in the prior review added the exit-code guard to `cg-commit-push-pr` Step 4 but the symmetrical fix was not applied to the equivalent block in `cg-verify-pr` Step 4. If staging fails (locked file, permissions, merge conflict), the commit runs silently on previously-staged content with no error reported.
  **Fix**: After `git add <fixed-files>` in Step 4, add: "Verify exit code. If non-zero: report the exact git error and halt — do not attempt `git commit`."

---

### P2 — IMPORTANT (should fix)

**[P2.1]** [cg-code-quality] `cg-verify-pr.prompt.md:Step 2` — All-CANCELLED edge case has no terminal action
  **Why**: The CANCELLED rule says "treat as non-blocking; note in classification" but does not halt. The Failing bullet only fires for `FAILURE`/`TIMED_OUT`. If every check is CANCELLED, no bullet exits cleanly and Step 3 is entered with zero failing checks.
  **Fix**: Add an explicit case: "If all remaining checks are `CANCELLED`, `SKIPPED`, `NEUTRAL`, or `SUCCESS`: output '✅ No failing checks. Nothing to fix.' and halt."

**[P2.2]** [cg-code-quality] `cg-commit-push-pr.prompt.md:Step 1.2` and `cg-verify-pr.prompt.md:Step 2` — Sub-bullets fused onto parent line
  **Why**: `cg-commit-push-pr` Step 1.2 has the detached HEAD sub-bullet fused onto the same line as the parent item. `cg-verify-pr` Step 2 has `Halt.   - **Manual action required**...` and `classification).   - **Failing**...` fused similarly. LLM parsers depend on newlines to delineate list items.
  **Fix**: Insert a line break before each fused sub-bullet so the conditional handling appears on its own indented line.

**[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1:cg-verify-pr structure Describe` — No test for P1.3 null/empty `statusCheckRollup` guard
  **Why**: The "No CI checks have run yet" halt (P1.3 fix) has no test assertion. A regression removing this guard would not be caught.
  **Fix**: Add:
  ```powershell
  It "halts with 'No CI checks have run yet' when statusCheckRollup is null or empty (P1.3)" {
      ($content -match 'No CI checks have run yet') | Should -Be $true
  }
  ```

**[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1:both structure Describes` — No test for P1.4 detached HEAD guard in either prompt
  **Why**: Both prompts have the detached HEAD guard. Neither test Describe asserts "detached HEAD state" appears in the prompt text.
  **Fix**: Add to each structure Describe block:
  ```powershell
  It "halts with 'detached HEAD state' when git branch returns empty (P1.4)" {
      ($content -match 'detached HEAD state') | Should -Be $true
  }
  ```

**[P2.5]** [cg-testing] `tests/prompt-tools.Tests.ps1:cg-verify-pr structure Describe` — No test for P1.6 empty `gh run list` guard
  **Why**: The "No run found for workflow" skip path (P1.6 fix) has no test assertion.
  **Fix**: Add:
  ```powershell
  It "skips log fetching with 'No run found' message when gh run list returns empty (P1.6)" {
      ($content -match 'No run found for workflow') | Should -Be $true
  }
  ```

**[P2.6]** [cg-testing] `tests/prompt-tools.Tests.ps1:cg-verify-pr structure Describe` — No tests for P1.7 SKIPPED/CANCELLED/ACTION_REQUIRED/STALE classification rules
  **Why**: All four P1.7 conclusion values lack test assertions. A regression misclassifying any of them would be undetected.
  **Fix**: Add four `It` blocks:
  ```powershell
  It "treats SKIPPED conclusion as passing (P1.7)" {
      ($content -match 'SKIPPED') | Should -Be $true
  }
  It "treats CANCELLED as non-blocking (P1.7)" {
      ($content -match 'CANCELLED') | Should -Be $true
  }
  It "halts on ACTION_REQUIRED conclusion (P1.7)" {
      ($content -match 'ACTION_REQUIRED') | Should -Be $true
  }
  It "halts on STALE conclusion (P1.7)" {
      ($content -match 'STALE') | Should -Be $true
  }
  ```

**[P2.7]** [cg-testing] `tests/prompt-tools.Tests.ps1:cg-commit-push-pr structure Describe` — No test for P1.1 `git add` exit-code check
  **Why**: The exit-code guard after `git add` in cg-commit-push-pr Step 4 (P1.1 fix) has no test assertion.
  **Fix**: Add:
  ```powershell
  It "halts after git add failure without attempting git commit (P1.1)" {
      ($content -match 'Verify exit code after.*git add|exit code.*git add') | Should -Be $true
  }
  ```

---

### P3 — MINOR (nice to have)

**[P3.1]** [cg-code-quality] `tests/prompt-tools.Tests.ps1:~line 1989` — Banner comment says "14 prompts" but Describe block correctly says "17 prompts"
  **Fix**: Change `# Context Layer — compound-gpid.context.md referenced in all 14 prompts` → `# Context Layer — compound-gpid.context.md referenced in all 17 prompts`.

**[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1:cg-commit-push-pr structure Describe` — No test for P2.10 untracked file bifurcation
  **Fix**: Add:
  ```powershell
  It "reads untracked files via Get-Content when git diff returns empty (P2.10)" {
      ($content -match 'Get-Content.*untracked|untracked.*Get-Content|\?\?.*Get-Content') | Should -Be $true
  }
  ```

**[P3.3]** [cg-testing] `tests/prompt-tools.Tests.ps1:cg-verify-pr structure Describe` — Test name claims all four failure categories but assertion only checks `Lint`
  **Fix**: Rename `It "classifies failures by type: lint, test, build, platform-specific (R7)"` → `It "classifies lint/type errors as a failure category (R7)"`.

**[P3.4]** [cg-testing] `tests/prompt-tools.Tests.ps1:cg-verify-pr structure Describe` — Trivially-broad `|block` arm in `--watch` prohibition test
  **Fix**: Remove the `|block` alternative from `($content -match 'Do NOT use.*--watch|NOT.*--watch|block')`. The first two arms are sufficient and specific.

---

### ✅ Passed — All 22 prior fixes confirmed

- P1.1 (git add exit-code, cg-commit-push-pr) ✓
- P1.2 (force-with-lease rejection) ✓
- P1.3 (statusCheckRollup null/empty guard) ✓
- P1.4 (detached HEAD, both prompts) ✓
- P1.6 (empty gh run list guard) ✓
- P1.7 (SKIPPED/CANCELLED/ACTION_REQUIRED/STALE classification) ✓
- P2.2 (--first-parent in git log) ✓
- P2.3 (Select-Object -First 1 on git merge-base) ✓
- P2.5 (docs/reference.md Review Agents note) ✓
- P2.6 (default branch detection, cg-verify-pr) ✓
- P2.7 (@cg-code-quality description updated) ✓
- P2.8 ([--propose] in reference.md) ✓
- P2.9 (35→37 file count in reference.md) ✓
- P2.10 (untracked file bifurcation) ✓
- P2.11 (redundant git status removed) ✓
- P2.12 (copilot-instructions Describe merged) ✓
- P2.17 (No open PR test) ✓
- P2.18 (context layer 17 prompts) ✓
- P2.19 (Nothing to commit test) ✓
- P2.20 (SKIPPED/CANCELLED, covered by P1.7) ✓
- P3.1 (stale comment 19→21) ✓
- P3.2 (split --watch It block) ✓
- docs/model-guide.md, roadmap.json, copilot-instructions.md, tests/model-assignments.Tests.ps1 — no new issues.
