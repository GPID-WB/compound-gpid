---
plan: .cg-docs/plans/2026-04-15-per-step-test-failure-handling.md
findings:
  P1.1: fixed
  P2.1: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
---

## Review Report

**Review depth**: light (explicit override — ≥50 non-test lines changed would auto-escalate to standard)
**Files reviewed**: 6
- `.github/prompts/cg-work.prompt.md` (+41/-18 from main)
- `tests/prompt-tools.Tests.ps1` (+49)
- `tests/roadmap.Tests.ps1` (+6)
- `.gitignore` (+1)
- `compound-gpid.md` (+4/-2)
- `roadmap.json` (+32/-32)

**Agents dispatched**: cg-code-quality, cg-testing

**Findings**: 0 P0 · 1 P1 · 1 P2 · 3 P3 = 5 total

---

### P0 — BLOCKING

None.

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-code-quality + cg-testing] `tests/roadmap.Tests.ps1`:219–224 — Cross-milestone duplicate feature ID check has no `It` block coverage
  **Why**: The `$allFeatureIds` cross-milestone check was added (P3.9 fix from standard review) but no test exercises the `"appears in multiple milestones"` error path. The existing intra-milestone duplicate test uses a single-milestone fixture and never reaches the cross-milestone branch. The new validation code is dead from a test coverage perspective.
  **Fix**: Add alongside the existing duplicate-ID test:
  ```powershell
  It "rejects duplicate feature IDs across milestones" {
      $roadmap = @{
          schemaVersion = "compound-gpid-roadmap-v1"
          milestones    = @(
              @{ id = "m1"; title = "M1"; objective = "x"; status = "planned"
                 features = @(@{ id = "shared-feat"; title = "F1"; status = "idea"; plan = $null }) }
              @{ id = "m2"; title = "M2"; objective = "x"; status = "planned"
                 features = @(@{ id = "shared-feat"; title = "F2"; status = "idea"; plan = $null }) }
          )
      }
      $errors = Test-RoadmapSchema $roadmap
      ($errors -join " ") | Should Match "multiple milestones"
  }
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Test 8 does not cover the else-branch behavior (sub-step 3 regression handling)
  **Why**: Test 8 verifies `regressions introduced by the fix` appears, but nothing tests that the prompt instructs emitting the step-4 format notification and continuing to Auto-Fix Diagnostics when regressions occur. If someone rewrote the else clause to "log and retry", Test 8 would still pass.
  **Fix**:
  ```powershell
  It "on new regressions emits step-4 format notification and continues to Auto-Fix Diagnostics" {
      ($content -match 'emit the standard failure notification.*sub-step 4|format from sub-step 4') | Should Be $true
  }
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality + cg-testing] `tests/prompt-tools.Tests.ps1`:1676 — Test 2 subsumed by Test 1 (no independent coverage)
  **Why**: `'still failing after 2 fix attempts'` is a strict substring of Test 1's pattern `'\d+\.\s+If tests are still failing after 2 fix attempts'`. Any change that kills Test 1 also kills Test 2. No independent signal.
  **Fix**: Replace Test 2 with a blockquote-format check:
  ```powershell
  It "notification is rendered as a blockquote" {
      ($content -match '>\s+"\*\*N test\(s\)|>\s+\*\*N test\(s\)') | Should Be $true
  }
  ```

- **[P3.2]** [cg-code-quality] `tests/prompt-tools.Tests.ps1`:1703 — It description references old "Step 4.1" label
  **Why**: The label was renamed from "Step 4.1" to "Auto-Fix Diagnostics" (P2.4 fix in standard review). The `It` description still says "for Step 4.1 sub-item 5".
  **Fix**: Rename to `"includes double-notification skip-guard in Auto-Fix Diagnostics sub-item 5"`.

- **[P3.3]** [cg-code-quality + cg-testing] `tests/prompt-tools.Tests.ps1`:1709 — Dead second alternative in Test 10
  **Why**: `'functional tests only.*not.*get_errors'` never matches because "not" does not appear between those tokens in the current prompt. Test passes only via the first alternative.
  **Fix**: Replace with: `($content -match 'Test Failure Recovery.*functional tests only|get_errors.*handled separately') | Should Be $true`

---

### ✅ Passed

- **cg-code-quality**: TFR block prose reads coherently; no trailing whitespace; no broken markdown; no DRY violations in any changed file; `.gitignore` comment is accurate; `compound-gpid.md` current-focus update is correct.
- **cg-testing**: `(?s)Test Failure Recovery step 4.*skip this surface` confirmed matching against actual prompt text; all `(?s)` flags correct on multi-line patterns.
