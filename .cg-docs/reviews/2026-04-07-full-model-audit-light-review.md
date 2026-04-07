---
plan: ".cg-docs/plans/2026-04-07-full-model-audit.md"
findings:
  P1.1: fixed
  P2.1: fixed
  P3.1: fixed
  P3.2: fixed
  P3.3: fixed
  P3.4: fixed
---

## Review Report

**Review depth**: light  
**Branch**: `audit_models`  
**Files reviewed**: 12  
**Agents**: cg-code-quality, cg-testing  
**Findings**: 1 P1 · 1 P2 · 4 P3

---

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Step 2.5 operationalized criteria names not tested  
  **Why**: The updated Step 2.5 in `cg-review.prompt.md` defines three explicit quality criteria: **Presence**, **Context**, **Volume**. The existing test block checks for the section header, "Incomplete Reviews", "NOT retry", `empty.*garbled`, and `@<agent-name>` — but does not assert that the three named criteria appear in the prompt. If someone edits the prompt and removes or renames these criteria, no test will catch it.  
  **Fix**: Add three `It` blocks to the "cg-review.prompt.md - subagent output quality check" Describe block:
  ```powershell
  It "documents the Presence criterion by name" {
      ($content -match '\bPresence\b') | Should Be $true
  }
  It "documents the Context criterion by name" {
      ($content -match '\bContext\b') | Should Be $true
  }
  It "documents the Volume criterion by name" {
      ($content -match '\bVolume\b') | Should Be $true
  }
  ```

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `tests/model-assignments.Tests.ps1:18-24` and `tests/prompt-tools.Tests.ps1:22-28` — `Get-Frontmatter` helper duplicated across both test files  
  **Why**: Both test files define an identical 7-line `Get-Frontmatter` function. Future changes to frontmatter parsing (e.g., supporting different delimiter styles) must be applied in both places.  
  **Fix**: Extract to `tests/helpers.ps1`:
  ```powershell
  # tests/helpers.ps1
  function Get-Frontmatter {
      param([string]$FilePath)
      $raw = Get-Content $FilePath -Raw -Encoding UTF8
      if ($raw -match '(?s)^---\s*\r?\n(.+?)\r?\n---') {
          return $Matches[1]
      }
      return ''
  }
  ```
  Then dot-source at the top of each test file: `. "$PSScriptRoot/helpers.ps1"`  
  Note: The P2.3 comment in `model-assignments.Tests.ps1` explicitly flagged this as a conscious decision ("can be duplicated or moved to a shared helpers.ps1"); extracting it is the cleaner path forward.

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Two `Describe` blocks test the same `cg-skill-r-testing` files  
  **Why**: `Describe "cg-skill-r-testing - skill file structure"` (hardcoded `@()` array) and `Describe "cg-skill-r-testing - file structure validation"` (individual `It` blocks) test identical files with identical assertions. Pre-existing duplication not introduced in this branch, but worth removing.  
  **Fix**: Remove the second block (`cg-skill-r-testing - file structure validation`); the first already covers all 6 files.

- **[P3.2]** [cg-testing] `tests/model-assignments.Tests.ps1` — Model guide stem search matches anywhere in prose  
  **Why**: `($content -match [regex]::Escape($stem))` passes if the stem appears anywhere in the guide — including inside prose sentences or URLs. A stem like `cg-review` would match "use cg-review to inspect" even if the reference table was deleted.  
  **Fix** (optional): Anchor patterns to file-extension context: `($content -match [regex]::Escape($stem) + '\.(prompt|agent)\.md')` for stronger table validation.

- **[P3.3]** [cg-testing] `tests/model-assignments.Tests.ps1` — `model:` key presence validated but value not checked  
  **Why**: Tests confirm each file has a `model:` frontmatter key but not that the value is non-empty or non-placeholder. A file with `model: ` (empty) or `model: TODO` would pass.  
  **Fix** (optional): Add a value check: `($frontmatter -cmatch '(?m)^\s*model:\s+\S+') | Should Be $true`

- **[P3.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Missing test for "no issues found" as a valid agent output signal  
  **Why**: Step 2.5 in `cg-review.prompt.md` states a usable output contains findings "OR an explicit 'no issues found' statement" — but no test validates this alternative is documented in the prompt.  
  **Fix**: Add to the "review file output step" Describe block:
  ```powershell
  It "documents 'no issues found' as valid output when an agent finds nothing" {
      ($content -match 'no issues found') | Should Be $true
  }
  ```

---

### ✅ Passed

- **cg-code-quality**: PowerShell style, naming, JSON formatting, YAML frontmatter, and Markdown all pass. Count sentinels well-documented. `-cmatch` usage for case-sensitive matching is correct.
- **cg-code-quality**: No hardcoded magic values; all file paths constructed via `Join-Path`; `Get-Content -Raw -Encoding UTF8` used consistently.
- **cg-testing**: Both test files are Pester 3.4-safe: no `-Because` clauses, no directory-form `Invoke-Pester`, no `-PassThru | ExpandProperty` pipelines.
- **cg-testing**: Dynamic `Get-ChildItem` discovery with count sentinels is robust; `Test-Path` guards prevent opaque scope-level exceptions; regex anchored to `model:` key with case-sensitive `-cmatch`.

---

> Review report saved to `.cg-docs/reviews/2026-04-07-full-model-audit-light-review.md`. Use `/cg-fix-triage` to apply findings by ID (e.g., `/cg-fix-triage P1.1 P2.1`) or by priority level (e.g., `/cg-fix-triage P1`).
