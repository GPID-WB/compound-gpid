---
plan: .cg-docs/plans/2026-04-07-r-dialect-skills-architecture.md
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P3.1: fixed
---

## Review Report

**Review depth**: light (override; config is `thorough`)
**Branch**: `feat/r-dialect-skills`
**Files reviewed**: 32 (all changed files between `main` and `feat/r-dialect-skills`)
**Agents dispatched**: cg-code-quality, cg-testing
**Findings**: P1 × 0, P2 × 4, P3 × 1

---

### P1 — CRITICAL (must fix before merge)

None.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No `SCHEMA_VERSION` validation test.
  **Why**: `SCHEMA_VERSION` was bumped to `2026-04-07-r-syntax-dialect` but nothing tests it exists or contains the expected value. A version control regression (e.g. accidental revert) would slip through undetected.
  **Fix**: Add a test inside the `SCHEMA_VERSION` or dialect skills describe block:
  ```powershell
  It "SCHEMA_VERSION contains expected dialect marker" {
      $schemaFile = Join-Path $repoRoot "SCHEMA_VERSION"
      $content = Get-Content $schemaFile -Raw -Encoding UTF8 | ForEach-Object { $_.Trim() }
      ($content -match 'r-syntax-dialect') | Should Be $true
  }
  ```

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1:454-490` — Router test covers only the 4 dialect-specific skills; the 4 unconditional skills (`cg-skill-r-analytical`, `cg-skill-r-technical`, `cg-skill-r-testing`, `cg-skill-r-shared`) are not validated.
  **Why**: Accidental deletion or rename of any unconditional routing line in `r.instructions.md` would not be caught. The router currently has 8 skill references; tests only exercise 4 of them.
  **Fix**: Add 4 more `It` blocks inside the existing "r.instructions.md - dialect router" describe block:
  ```powershell
  It "routes to cg-skill-r-analytical (unconditional)" {
      ($content -match 'cg-skill-r-analytical') | Should Be $true
  }
  It "routes to cg-skill-r-technical (unconditional)" {
      ($content -match 'cg-skill-r-technical') | Should Be $true
  }
  It "routes to cg-skill-r-testing (unconditional)" {
      ($content -match 'cg-skill-r-testing') | Should Be $true
  }
  It "routes to cg-skill-r-shared (unconditional)" {
      ($content -match 'cg-skill-r-shared') | Should Be $true
  }
  ```

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test validates `docs/reference.md` lists all 8 R skills or documents the `r-syntax` config field.
  **Why**: The skills table in `docs/reference.md` was updated as part of this feature (P2.6 fix in the thorough review). If any entry is accidentally dropped or the config field table is removed, nothing catches it.
  **Fix**: Add a new describe block:
  ```powershell
  Describe "docs/reference.md - R skills and r-syntax config" {
      $refFile = Join-Path $repoRoot "docs\reference.md"
      $content = Get-Content $refFile -Raw -Encoding UTF8
      
      It "lists all 8 R skills" {
          $skills = @('cg-skill-r-collapse','cg-skill-r-datatable','cg-skill-r-tidyverse',
                      'cg-skill-r-visualization','cg-skill-r-analytical','cg-skill-r-technical',
                      'cg-skill-r-shared','cg-skill-r-testing')
          foreach ($skill in $skills) {
              ($content -match [regex]::Escape($skill)) | Should Be $true
          }
      }
      
      It "documents r-syntax configuration field" {
          ($content -match 'r-syntax') | Should Be $true
      }
  }
  ```

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No tests validate the 3 dialect-aware agents (`cg-code-quality`, `cg-data-quality`, `cg-performance`) mention `compound-gpid.local.md` for `r-syntax` lookup and document both dialects.
  **Why**: These agents were updated with dialect-conditional logic (P1.1–P1.3 fixes in the thorough review). A revert or incorrect rebase could silently remove the fixes.
  **Fix**: Add a describe block:
  ```powershell
  Describe "R-dialect-aware agents - r-syntax handling" {
      $dialectAwareAgents = @('cg-code-quality', 'cg-data-quality', 'cg-performance')
      
      foreach ($agent in $dialectAwareAgents) {
          $agentFile = Join-Path $repoRoot ".github\agents\$agent.agent.md"
          $content = Get-Content $agentFile -Raw -Encoding UTF8
          
          It "$agent mentions r-syntax in compound-gpid.local.md" {
              ($content -match 'r-syntax') | Should Be $true
          }
          It "$agent documents data.table-collapse dialect" {
              ($content -match 'data\.table-collapse') | Should Be $true
          }
          It "$agent documents tidyverse dialect" {
              ($content -match 'tidyverse') | Should Be $true
          }
      }
  }
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Reference file existence is implicitly tested via `SKILL.md` cross-link resolution but not explicitly enumerated by filename.
  **Why**: A reference file (e.g. `tidyverse-anti-patterns.md`) could be deleted and the only test that catches it is the indirect cross-link check. Explicit enumeration is easier to debug.
  **Fix**: Add a describe block enumerating expected reference files per skill (see full list in the testing agent's output). Low priority since indirect coverage exists.

---

### ✅ Passed

- **cg-code-quality**: No new issues found. All DRY, naming, cross-reference, code example correctness, and style consistency checks passed. All 32 changed documentation files are internally consistent and ready for merge.
