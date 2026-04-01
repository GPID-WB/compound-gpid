## Review Report

**Review depth**: light
**Date**: 2026-03-30
**Plan**: `.cg-docs/plans/2026-03-30-fix-triage-prompt.md`
**Branch**: `triage` vs `main` (26 files changed)
**Findings**: 1 P1, 3 P2, 1 P3

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No regression test for the "Do NOT delegate" instruction in `cg-review.prompt.md` Step 3.5
  **Why**: This instruction was added specifically to fix the root-cause bug where delegating file writing mid-session silently corrupted output. Without a test, the instruction can be softened or removed without detection and the bug returns.
  **Fix**: Add inside the `"cg-review.prompt.md - review file output step"` Describe block:
  ```powershell
  It "explicitly instructs DO NOT delegate the Step 3.5 file write" {
      ($content -match 'Do NOT delegate') | Should Be $true
  }
  ```

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/prompts/cg-fix-triage.prompt.md:Step 3` — Validation failure path is undefined
  **Why**: Step 3 says "Verify the fix compiles/parses correctly" but only handles the ambiguous/risky case. If validation fails (compile/parse error), there is no fallback — the agent is left without guidance.
  **Fix**: After the ambiguous/risky block in Step 3, add: "If a fix fails validation, display the error and ask the user to (a) skip and continue, or (b) stop for manual review. Track failed fixes in the summary under 'Failed'."

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No `tools:` absence test for `cg-fix-triage.prompt.md`
  **Why**: The test file already asserts that `cg-review.prompt.md` (an orchestrator) must not have a `tools:` restriction. `cg-fix-triage.prompt.md` is also an orchestrator and needs the same guard. An accidental `tools:` addition would silently strip write access.
  **Fix**: Add a new Describe block:
  ```powershell
  Describe "cg-fix-triage.prompt.md - no tool restriction" {
      $promptFile = Join-Path $repoRoot ".github\prompts\cg-fix-triage.prompt.md"
      Context "orchestrator must have unrestricted tools" {
          $frontmatter = Get-Frontmatter -FilePath $promptFile
          It "does not have a tools: key" {
              ($frontmatter -notmatch 'tools:') | Should Be $true
          }
      }
  }
  ```

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test that `cg-resume.prompt.md` references `.cg-docs/reviews/`
  **Why**: The test file verifies the review/fix-triage pipeline contract, but not the resume side. Step 2e of `cg-resume.prompt.md` (which scans `.cg-docs/reviews/` to surface pending findings) has no regression guard.
  **Fix**: Add a new Describe block:
  ```powershell
  Describe "cg-resume.prompt.md - pending review findings scan" {
      $promptFile = Join-Path $repoRoot ".github\prompts\cg-resume.prompt.md"
      $content = Get-Content $promptFile -Raw -Encoding UTF8
      It "references .cg-docs/reviews/ directory in Step 2e to scan for pending findings" {
          ($content -match '\.cg-docs[/\\]reviews') | Should Be $true
      }
  }
  ```

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `.github/prompts/cg-fix-triage.prompt.md:Step 2` — Terminology inconsistency between "skipping" and "Out of scope"
  **Why**: Step 2 says "skipping M others" but Step 4's summary distinguishes "Skipped" (user declined) vs "Out of scope" (not selected). The ambiguity could confuse the agent when counting.
  **Fix**: In Step 2, change "skipping M others" to "M out of scope."

### ✅ Passed

- cg-code-quality: `cg-fix-triage.prompt.md` frontmatter is valid (`description:`, `model:` present, no `tools:` restriction)
- cg-code-quality: `cg-review.prompt.md` Step 3.5 correctly instructs saving to `.cg-docs/reviews/`
- cg-code-quality: `docs/workflow.md` Fix Triage section is clear with invocation table
- cg-code-quality: `docs/reference.md` updated consistently (prompts table, directory structure)
- cg-testing: Existing test helpers (`Get-Frontmatter`, `Get-ToolsList`) correctly reused
- cg-testing: All 4 new `cg-fix-triage` test blocks cover file existence, frontmatter, and `.cg-docs/reviews/` reference
- cg-testing: Compound finding ID format test (`\*\*\[P[123]\.\d+\]\*\*`) correctly guards the parser contract
**Plan**: `.cg-docs/plans/2026-03-30-fix-triage-prompt.md`
**Files reviewed**: 8
**Findings**: 1 P1, 6 P2, 2 P3

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for `cg-fix-triage.prompt.md` existence
  **Why**: New prompt file added with no structural test; a rename or deletion would go undetected.
  **Fix**: Add a `Describe` block checking `Test-Path` for `.github\prompts\cg-fix-triage.prompt.md`.

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `.github/prompts/cg-review.prompt.md` — Step 5 Summary "Next Steps" does not mention `/cg-fix-triage`
  **Why**: Users skipping findings have no in-prompt guidance for the follow-up workflow.
  **Fix**: Add `- If findings were skipped: Run /cg-fix-triage in a future session to apply them.`

- **[P2.2]** [cg-code-quality] `.github/prompts/cg-resume.prompt.md` — Does not scan `.cg-docs/reviews/` for pending reports
  **Why**: Users resuming a session after a review get no reminder to run `/cg-fix-triage`.
  **Fix**: Add Step 2e scanning `.cg-docs/reviews/`, surface counts in Step 3, suggest `/cg-fix-triage` in Step 4.

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for compound finding IDs (`P1.1`) in `cg-review.prompt.md`
  **Why**: `cg-fix-triage` depends on this format; a revert would silently break the triage pipeline.
  **Fix**: Add `It` block: `($content -match '\*\*\[P[123]\.\d+\]\*\*') | Should Be $true`.

- **[P2.4]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test verifying `.cg-docs/reviews/` reference in `cg-fix-triage.prompt.md`
  **Why**: The core contract of the file is reading from `.cg-docs/reviews/`.
  **Fix**: Add `It` block: `($content -match '\.cg-docs[/\\]reviews') | Should Be $true`.

- **[P2.5]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test verifying `/cg-fix-triage P1.2 P2.1` usage instruction in `cg-review.prompt.md`
  **Why**: This onboarding text in Step 3.5 could be accidentally removed without a test.
  **Fix**: Add `It` block: `($content -match '/cg-fix-triage.*P\d\.\d') | Should Be $true`.

- **[P2.6]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No frontmatter test for `cg-fix-triage.prompt.md`
  **Why**: Missing `description:`/`model:` frontmatter silently prevents the prompt from loading in VS Code.
  **Fix**: Add a `Context` block using `Get-Frontmatter` checking `description:` and `model:`.

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` — Test name "contains a step that writes the review report" is vague
  **Fix**: Rename to `"writes the review report to .cg-docs/reviews/ directory in Step 3.5"`.

- **[P3.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No cross-reference test that `cg-review.prompt.md` mentions `/cg-fix-triage`
  **Fix**: Add `($content -match '/cg-fix-triage') | Should Be $true` in the cg-review Describe block.

### ✅ Passed

- cg-code-quality: No stale `/cg-fix` references (only `/cg-fixbug` and `/cg-fix-triage`)
- cg-code-quality: `docs/workflow.md` is ASCII-safe -- `->` arrows, no em-dashes
- cg-code-quality: `docs/reference.md`, `cg-setup.prompt.md`, `compound-gpid.md` all updated consistently
- cg-code-quality: `cg-fix-triage.prompt.md` Step 1 correctly references `.cg-docs/reviews/`
- cg-testing: Existing test helpers (`Get-Frontmatter`, `Get-ToolsList`) reusable; encoding safe

---

## Resolution

**Status**: resolved
**Resolved date**: 2026-04-01
**Merged**: PR #12 (commit dce0b5f) -- all findings fixed and merged to main
**Verification**: all 13 tests in `tests/prompt-tools.Tests.ps1` pass
