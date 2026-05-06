---
date: 2026-05-05
depth: light
parent-review: .cg-docs/reviews/2026-05-05-branch-creation-from-plan-review.md
type: verification
findings:
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P3.1: fixed
---

## Review Report

**Review depth**: light (verify pass)
**Files reviewed**: 5 (`.github/prompts/cg-plan.prompt.md`, `tests/prompt-tools.Tests.ps1`, `docs/reference.md`, `roadmap.json`, `.cg-docs/plans/2026-05-05-branch-creation-from-plan.md`)
**Findings**: 4 (P0: 0, P1: 0, P2: 3, P3: 1)

---

### ✅ All Prior Findings Verified Converged

All 19 fixed findings from the prior review (`2026-05-05-branch-creation-from-plan-review.md`) were confirmed present and correct:

| Finding | Description | Status |
|---------|-------------|--------|
| P1.1 | `Derive the branch name` precedes `Suggested name:` in prompt | ✓ converged |
| P1.2 | `uncommitted changes` check precedes `Suggested name:` in prompt | ✓ converged |
| P1.3 | Branch-already-exists error handler present | ✓ converged |
| P1.4 | `git branch -d` orphaned-branch cleanup note present | ✓ converged |
| P1.5 | Extended type taxonomy (test, docs, chore, data, analysis) present | ✓ converged |
| P2.1 | `$step07Idx | Should BeGreaterThan -1` guard added | ✓ converged |
| P2.2 | `$step1Idx | Should BeGreaterThan -1` guard added | ✓ converged |
| P2.3 | `git symbolic-ref refs/remotes/origin/HEAD` dynamic detection | ✓ converged |
| P2.4 | Non-git workspace guard (fails or returns empty → skip silently) | ✓ converged |
| P2.5 | `Normalize the branch name` + `truncate to 60` present | ✓ converged |
| P2.6 | Refine-path skip present | ✓ converged |
| P2.7–P2.8 | Side-effect fixes of P1.1/P1.2 | ✓ converged |
| P2.9 | `**Branch offer at Step 0.7**` note in `docs/reference.md` | ✓ converged |
| P3.1 | `short-description-from-your-request` placeholder | ✓ converged |
| P3.2 | `If the user accepts` / `If the user declines` phrasing | ✓ converged |
| P3.3 | Test description renamed | ✓ converged |
| P3.4 | Variable alignment padded to double-space | ✓ converged |
| P3.6 | `(?s)feat/.*fix/.*refactor/` + `git checkout -b` tests added | ✓ converged |

No cross-file breakage detected.

---

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-testing] `tests/prompt-tools.Tests.ps1` line ~3524 — Test name claims `docs` and `data` coverage but neither is asserted
  **Why**: `It "Branch type taxonomy includes extended types (test, docs, chore, data, analysis)"` only asserts `test/`, `analysis/`, and `chore/`. `docs/` and `data/` are named in the test description and are real entries in the prompt taxonomy, but have no assertions. Deleting them from the prompt would not be caught.
  **Fix**: Add inside the existing `It` block:
  ```powershell
  ($content -match 'docs/.*documentation') | Should Be $true
  ($content -match 'data/.*data work')      | Should Be $true
  ```

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the "other errors → report verbatim" branch of the `git checkout -b` error handler
  **Why**: The prompt specifies two distinct error paths: (1) branch already exists (covered by existing test); (2) other errors → report git error verbatim and skip. Path 2 has no assertion. A model removing that instruction would not be caught.
  **Fix**: Add:
  ```powershell
  It "Reports git error verbatim and skips branching on other checkout failures" {
      ($content -match 'other errors.*verbatim|report the git error verbatim') | Should Be $true
  }
  ```

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1` — No test for the "empty after normalization → ask user" fallback in the branch name normalization rule
  **Why**: The prompt specifies: "If empty after normalization, ask the user for a branch name." The existing P2.5 test verifies `Normalize the branch name` and `truncate to 60` but not this fallback. Removing the fallback instruction would not be caught.
  **Fix**: Add:
  ```powershell
  It "Asks user for branch name when normalization yields empty string" {
      ($content -match 'empty after normalization.*ask the user') | Should Be $true
  }
  ```

---

### P3 — MINOR (nice to have)

- **[P3.1]** [cg-code-quality] `tests/prompt-tools.Tests.ps1` line ~3499 — Dead regex alternation in the "Branch Offer skips silently" test
  **Why**: The test uses:
  ```powershell
  ($content -match 'not.*main.*master.*skip silently|already on a.*branch.*skip silently')
  ```
  The first alternation (`not.*main.*master.*skip silently`) was written for pre-P2.3 prompt text. After P2.3 the prompt no longer mentions `main`/`master` in this clause. The test passes only via the second alternation. The dead first branch will never match and could mask a future dual regression.
  **Fix**: Drop the stale first alternation:
  ```powershell
  ($content -match 'already on a.*branch.*skip silently') | Should Be $true
  ```

---

### ✅ Passed (no new issues)

- **cg-code-quality**: All 19 prior findings confirmed converged. No new P0/P1 issues. One dead regex branch flagged (P3.1 above).
- **cg-testing**: All prior findings confirmed converged. Three test coverage gaps found (P2.1–P2.3 above).
