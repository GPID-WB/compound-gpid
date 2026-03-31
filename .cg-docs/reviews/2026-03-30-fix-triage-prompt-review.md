## Review Report

**Review depth**: light
**Date**: 2026-03-30
**Status**: all findings resolved (2026-03-30 via /cg-fix-triage)
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
