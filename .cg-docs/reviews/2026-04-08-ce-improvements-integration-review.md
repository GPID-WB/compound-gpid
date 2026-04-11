---
plan: .cg-docs/plans/2026-04-08-ce-improvements-integration.md
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P3.1: fixed
---

## Review Report

**Review depth**: light  
**Branch**: feat/ce-improvements  
**Files reviewed**: 22  
**Agents dispatched**: cg-code-quality, cg-testing  
**Findings**: 0 P0, 0 P1, 3 P2, 1 P3

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/skills/cg-skill-compound-docs/references/solution-schema.md` — `bugs` category missing from required fields table  
  **Why**: The category values column lists `build-errors`, `performance-issues`, `testing-patterns`, `data-quality`, `environment-issues`, `git-workflows` — omitting `bugs`. Both `cg-compound.prompt.md` (also changed in this commit) and `copilot-instructions.md` explicitly list `bugs` as the first valid category. The file was edited in this commit for the P2.4 severity fix but this inconsistency was not addressed.  
  **Fix**: Add `bugs` as the first entry: `` `bugs`, `build-errors`, `performance-issues`, `testing-patterns`, `data-quality`, `environment-issues`, `git-workflows` ``

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test verifying `cg-fix-triage.prompt.md` Step 3 apply-order includes P0  
  **Why**: The P1.2 fix changed Step 3 to read "in order (P0 first, then P1, then P2, then P3)". This behaviour change is untested. A future edit could silently revert P0 from the ordering with no test failure to catch it.  
  **Fix**:
  ```powershell
  It "Step 3 apply order lists P0 first before P1" {
      ($content -match 'P0 first') | Should Be $true
  }
  ```

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test verifying `cg-compound.prompt.md` severity template includes P0  
  **Why**: The P1.3 fix updated the severity field template to `"<P0|P1|P2|P3>"`. All existing `cg-compound` tests are structural only (exists, frontmatter, no-tools). A regression could drop P0 from the severity field with no detection.  
  **Fix**:
  ```powershell
  It "severity field template includes P0 option" {
      ($content -match '<P0\|P1\|P2\|P3>') | Should Be $true
  }
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for Priority Levels table in `docs/reference.md`  
  **Why**: The previous P3.1 fix added a standalone Priority Levels table to `docs/reference.md`. The existing `docs/reference.md` describe block covers R skills and r-syntax config but not the priority table — `P0 BLOCKING` could be dropped silently in a future edit.  
  **Fix**: Add to the existing `"docs/reference.md - R skills and r-syntax config"` describe:
  ```powershell
  It "contains Priority Levels table with P0 BLOCKING entry" {
      ($content -match 'P0.*BLOCKING') | Should Be $true
  }
  ```

---

### ✅ Passed

- cg-code-quality: No style violations, naming issues, or DRY problems in new content; `Run-Tests.ps1` correctly follows all three Pester safety rules; P0 additions are consistently phrased across `copilot-instructions.md`, all 8 agent files, both changed prompts (`cg-review`, `cg-fix-triage`, `cg-compound`), and `compound-gpid.md`
- cg-testing: 305/305 `prompt-tools` tests pass; 19/19 `charter` tests pass after `compound-gpid.md` update; new tests in this commit follow Pester 3.4-safe patterns (no em dashes in `It` descriptions, no `-ExpandProperty TestResult` pipelines)

