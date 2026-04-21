---
plan: .cg-docs/plans/2026-04-20-prompt-prose-compression.md
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
  P3.5: fixed
---

## Review Report

**Review depth**: light
**Files reviewed**: 9
**Findings**: 8 (P0: 0, P1: 0, P2: 3, P3: 5)

> Note: This is a verification review of the P1+P2+P3 fix-triage pass on `2026-04-20-prompt-prose-compression-review-3.md`. Three prior reviews cover the same changeset.

---

### P0 — BLOCKING

None.

---

### P1 — CRITICAL

None.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `tests/prompt-tools.Tests.ps1:~1841` — Step 3.5 block-scoped test missing `IndexOf` guard assertions
  **Why**: `$content.Substring($step35Start, $step37Start - $step35Start)` is called without verifying either index is ≥ 0. If either section header is renamed or removed, .NET throws `ArgumentOutOfRangeException`, obscuring the assertion failure. Every analogous `IndexOf`-scoped test in this file uses preceding guard assertions.
  **Fix**: Add guard assertions before the `Substring` call:
  ```powershell
  $step35Start | Should BeGreaterThan -1
  $step37Start | Should BeGreaterThan $step35Start
  ```

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the `Test-Path` guard in the `cg-fix-triage` full-suite regression gate
  **Why**: The gate was updated to include `if (-not (Test-Path tests\last-run.json)) { Write-Output 'last-run.json not found — run tests first' }`. The existing test only checks `'last-run\.json'`, which passes even if the guard is removed. The guard protects against silent failure on first run.
  **Fix**: Add to the Pester-crash-prevention describe block:
  ```powershell
  It "full-suite gate includes Test-Path guard for missing last-run.json" {
      ($cgFixTriageContent -match 'Test-Path tests\\last-run\.json') | Should Be $true
  }
  It "full-suite gate emits 'last-run.json not found' message when missing" {
      ($cgFixTriageContent -match 'last-run\.json not found') | Should Be $true
  }
  ```

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `<id>` placeholder in `cg-skill-fix-triage-migrate/SKILL.md` template not tested
  **Why**: The template changed from hardcoded `P1.1: open` / `P2.1: open` to `<id>: open`. No test guards this. If reverted, a model following the template would unconditionally emit `P1.1: open` regardless of what was parsed.
  **Fix**: Add to the SKILL.md behavioral-rules describe block:
  ```powershell
  It "uses generic <id> placeholder in frontmatter template (not hardcoded P1.1)" {
      ($content -match '<id>:') | Should Be $true
  }
  It "documents that <id> should be replaced with actual parsed IDs" {
      ($content -match 'replace <id> with actual IDs|actual IDs.*e\.g\.') | Should Be $true
  }
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `tests/helpers.Tests.ps1` — `Get-ToolsList` fixtures include `---` delimiters; inconsistent with function's input contract
  **Why**: `Get-ToolsList` expects extracted frontmatter body (inner content between `---` delimiters), not a full YAML block. Tests pass by coincidence but mislead future maintainers.
  **Fix**: Strip `---` delimiters from fixture strings so they represent the extracted body.

- **[P3.2]** [cg-code-quality] `tests/prompt-tools.Tests.ps1:~1279` — Redundant second `(?s)` in the statistical-functions alternation pattern
  **Why**: In .NET regex, `(?s)` at any position applies dotall to the full pattern. The second `(?s)` in `'(?s)Never.*safe_auto.*statistical|(?s)statistical.*escalate.*manual'` is inert but misleads readers.
  **Fix**: Change to `'(?s)Never.*safe_auto.*statistical|statistical.*escalate.*manual'`

- **[P3.3]** [cg-testing] `tests/helpers.Tests.ps1` — No test for the multiple `tools:` key dedup guard
  **Why**: The `| Select-Object -First 1` guard was added specifically to handle duplicate `tools:` keys; no test exercises the dedup behavior directly.
  **Fix**: Add a fifth test with two `tools:` lines; assert only the first is used.

- **[P3.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — `cg-review` Step 3.5 mtime fallback not tested
  **Why**: Step 3.5 was updated to add mtime fallback for absent `date:` field. No test guards the new tiebreaker text from accidental removal.
  **Fix**: Add to the `cg-review` Step 3.5 describe block:
  ```powershell
  It "Step 3.5 falls back to last-write time when date: is absent" {
      ($content -match 'last.write|absent.*fall back') | Should Be $true
  }
  ```

- **[P3.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Step 0.5 "deferred" ordering clause in `cg-fix-triage` not independently tested
  **Why**: The `(Deferred: execute after Step 1.3 completes.)` sentence could be deleted with no test failure. The skip-for-`--migrate` is tested, but not the ordering constraint.
  **Fix**: Add:
  ```powershell
  It "Step 0.5 instructs skipping skill load when invoked as --migrate" {
      ($content -match 'Skip this step if invoked as.*--migrate') | Should Be $true
  }
  ```

---

### ✅ Passed — No issues found

- **cg-code-quality**: `cg-fix-triage.prompt.md` deferred comment placement, `--migrate` skill-as-mode comment, regression-gate `Test-Path` guard text, `cg-review.prompt.md` Step 4 `mode:autofix` note and Step 3.5 sort rule, `cg-skill-fix-triage-migrate/SKILL.md` `<id>` placeholder with inline comment, `.gitignore` comment placement, `compound-gpid.context.md` single-convention entry, `roadmap.json` plan link to existing file, `tests/helpers.ps1` `Select-Object -First 1` guard, `tests/helpers.Tests.ps1` Pester 3.4 syntax, `tests/prompt-tools.Tests.ps1` gitignore filter test and `--migrate` unrecognized-arg extension.
- **cg-testing**: `Get-ToolsList` 4 new edge-case tests (correct patterns), gitignore non-comment filter test, `status is.*planned` tightening, `--migrate` unrecognized-arg extension. `compound-gpid.context.md` convention is indirectly enforced via prompt file tests.
