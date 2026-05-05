---
date: 2026-05-04
depth: light
parent-review: .cg-docs/reviews/2026-05-04-stata-testing-skill-revised-review.md
type: verification
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: fixed
---

## Review Report

**Review depth**: light (verify pass)
**Parent review**: `.cg-docs/reviews/2026-05-04-stata-testing-skill-revised-review.md` (35/35 findings fixed)
**Files reviewed**: 16
**Findings**: 5 (P0: 0, P1: 0, P2: 4, P3: 1)
**Agents**: cg-code-quality, cg-testing

---

### P0 — BLOCKING

_None._

### P1 — CRITICAL

_None._

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/skills/cg-skill-stata-testing/SKILL.md:42` — Routing table entry for `anti-patterns.md` still says "8 testing-specific anti-patterns" but Anti-Pattern 9 (Survey Subgroup `if` vs `subpop()`) was added in P1.6.
  **Why**: Stale count in the routing table misleads agents about file scope.
  **Fix**: Change `8 testing-specific anti-patterns` → `9 testing-specific anti-patterns`.

- **[P2.2]** [cg-code-quality] `docs/reference.md` — Same stale count: "8 testing-specific anti-patterns" in the `cg-skill-stata-testing` skill row.
  **Why**: Same wording was copied to both files when the skill was registered; both missed the P1.6 increment.
  **Fix**: Change `8 testing-specific anti-patterns` → `9 testing-specific anti-patterns`.

- **[P2.3]** [cg-code-quality] `.github/skills/cg-skill-stata-testing/references/data-validation.md:~14` — `duplicates tag` clears `r()` (only sets `r(unique_tag)`), so `if r(N) > 0` immediately after evaluates to `false` — the diagnostic `display as error` line never fires even when duplicates exist. The hard `assert dup_flag == 0` still catches the error, but the informative message is silently suppressed.
  **Why**: `duplicates tag` does not set `r(N)`. Any agent copying this pattern will produce silent diagnostics.
  **Fix**: Insert `count if dup_flag > 0` between `duplicates tag` and the conditional display:
  ```stata
  duplicates tag country_code year, gen(dup_flag)
  count if dup_flag > 0
  if r(N) > 0 display as error "FAIL: `r(N)' observations have duplicates on country_code + year"
  assert dup_flag == 0
  ```

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No regression guard tests exist for the three P0 content fixes. A future edit could silently reintroduce `e(balanced)` after `xtset` (P0.2), `assert expr, "message"` syntax (P0.1), or a `reldif(x, x)` self-comparison (P0.3).
  **Why**: P0 bugs are by definition the most dangerous. The reference files are hand-edited `.md` files with no structural validation beyond the new tests — content-level regressions are realistic.
  **Fix**: Add three `It` regression-guard blocks to the existing `Describe "cg-skill-stata-testing - skill file structure"` block:
  ```powershell
  It "data-validation.md uses r(balanced) not e(balanced) (P0.2 guard)" {
      $dv = Get-Content (Join-Path $skillRoot "references\data-validation.md") -Raw -Encoding UTF8
      ($dv -match 'e\(balanced\)') | Should Be $false
      ($dv -match 'r\(balanced\)') | Should Be $true
  }
  It "data-validation.md has no assert with inline string message (P0.1 guard)" {
      $dv = Get-Content (Join-Path $skillRoot "references\data-validation.md") -Raw -Encoding UTF8
      ($dv -match 'assert\b[^`\r\n]+,\s*"') | Should Be $false
  }
  It "result-verification.md stores spec coefficient before reldif (P0.3 guard)" {
      $rv = Get-Content (Join-Path $skillRoot "references\result-verification.md") -Raw -Encoding UTF8
      ($rv -match 'local\s+b\d\s*=\s*_b\[') | Should Be $true
  }
  ```

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1:~3372` — `It "SKILL.md description trigger mentions assertion blocks (P2.4)"` matches against `$skillContent` (entire file) instead of `$skillFm` (frontmatter only). The phrase "assertion blocks" could move to the routing table body and the test would still pass.
  **Why**: Test name says "description trigger" but checks the whole file — weaker than intended.
  **Fix**: Change `$skillContent -match 'assertion blocks'` → `$skillFm -match 'assertion blocks'` (frontmatter already contains the full multi-line `description:` block).

### ✅ Passed

- **cg-testing**: All 35 prior findings confirmed converged. No regressions detected. New `$skillFm` hoisting is correct Pester 3.4 scope. Tightened `when writing` regex matches actual `stata.instructions.md` content. All new test assertions are non-vacuous and can genuinely fail.
- **cg-code-quality**: No real usernames found. Cross-file consistency between `copilot-instructions.md` and `stata.instructions.md` is correct. No broken Markdown links. No invalid Stata syntax errors in modified blocks.
