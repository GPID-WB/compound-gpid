---
date: 2026-07-24
depth: full
type: standard
plan: .cg-docs/plans/2026-07-23-wb-report-writing-technical-methodology.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: skipped
  P1.4: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
---

## Review Report

**Review mode**: full
**Files reviewed**: 57
**Findings**: 9 (P0: 0, P1: 4, P2: 5, P3: 0)

> Auto-routing applied: schema/write-path/generated-tree risk. Resolved review mode: full. Mandatory emphasis: generator drift, cross-file contracts, and machine-readable completion state.

### P1 - CRITICAL (must fix before merge)

- **[P1.1]** [cg-testing / cg-version-control / cg-reproducibility / cg-adversarial / cg-performance / cg-architecture] `scripts/tests/test_target_drift.py:66` - The stale-tree gate now trusts uncommitted generated files present on disk, so a dirty worktree can pass while a clean checkout still ships incomplete generated outputs. [manual]
  **Why**: `test_generated_trees_are_not_stale()` now unions `git ls-files` with files merely present under `.claude/`, `.agents/`, and `.opencode/`. That weakens the committed product-surface contract described in the generated-tree docs and Brain guidance. The risk is real in this branch because generated WB skill trees are still untracked locally.
  **Fix**: Restore a committed-only merge gate for stale-tree enforcement, or split the behavior into two checks: one strict committed-parity gate and one optional local-presence diagnostic. Do not let local filesystem state satisfy the repository parity contract. Resolve the `.agents/*` tracking policy at the same time so the gate matches the intended product-surface model.

- **[P1.2]** [cg-data-quality / cg-reproducibility / cg-adversarial] `.github/skills/cg-skill-wb-report-writing/references/source-packs/policy-brief.json:21` - Approved source packs still use placeholder exemplar URLs, and the validator accepts any syntactically valid `http(s)` URL as evidence. [manual]
  **Why**: The new source packs are marked `approved`, but exemplar URLs use `example.org` placeholders. `_validate_url_or_repo_path()` in `scripts/validate_wb_writing_skill.py` treats any `http` or `https` URL as valid, so deterministic validation can report success without real reviewable source evidence.
  **Fix**: Replace placeholder URLs with real reviewed sources before merge, or keep those records out of `approved` status. Then tighten the validator to reject placeholder hosts or require repo-local archived evidence or an allowlisted stable source set.

- **[P1.3]** [cg-code-quality / cg-documentation / cg-architecture] `.cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md:73` - The parent plan's documented source-pack schema still disagrees with the validator and tests. [manual]
  **Why**: The plan still documents `terminology_status` as `approved|not-required` and omits fields the validator now requires, while `scripts/validate_wb_writing_skill.py` and `scripts/tests/test_validate_wb_writing_skill.py` enforce `approved|unresolved` plus additional required fields. That recreates the exact cross-file state-drift class already documented in the project brain.
  **Fix**: Choose one canonical contract owner and align the parent plan, validator, fixtures, and behavioral tests in the same change. If the validator is canonical, update the plan schema block; if the plan is canonical, relax the validator and tests accordingly.

- **[P1.4]** [cg-version-control / cg-reproducibility] `.cg-docs/active-state/current.json:29` - Machine-readable completion state and execution evidence reference artifacts that are still only local untracked files. [manual]
  **Why**: `current.json` and the completed work report record V4-V7 as passed and point to WB eval/source-pack/generated-output artifacts, but many of those files are still untracked in the current worktree, including `.cg-docs/cost/wb-writing-final/`, the new WB eval/source-pack JSON files, and generated skill trees under `.claude/` and `.opencode/`. That makes the recorded completed state non-reproducible from the commit alone.
  **Fix**: Before merge, either track the referenced evidence artifacts in the same commit or stop marking the related gates completed/passed until the repository state matches the machine-readable handoff.

### P2 - IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality / cg-adversarial / cg-architecture] `roadmap.json:165` - Roadmap feature lifecycle state diverged from the completed plan/work-report/active-state handoff. [safe_auto]
  **Why**: The WB report-writing feature still showed `active` after the parent plan and work report were completed.
  **Fix**: Mark the roadmap feature `done` and keep the active-state artifact in sync.
  **Status**: Fixed in this review pass.

- **[P2.2]** [cg-testing] `scripts/tests/test_validate_wb_writing_skill.py:176` - The validator test suite lacked a negative invariant proving legacy `not-required` terminology status is rejected. [safe_auto]
  **Why**: Positive checks for `unresolved` existed, but nothing prevented the old enum from silently re-entering the validator contract.
  **Fix**: Add a focused pytest case that sets `terminology_status` to `not-required` and expects validation to fail.
  **Status**: Fixed in this review pass.

- **[P2.3]** [cg-testing] `tests/prompt-tools.Tests.ps1:6869` - Behavioral coverage did not assert that the legacy terminology state stays out of the prose contract. [safe_auto]
  **Why**: The docs/tests required `approved` and `unresolved`, but there was no explicit negative assertion against `not-required`.
  **Fix**: Add a Pester assertion that the terminology reference text does not contain `not-required`.
  **Status**: Fixed in this review pass.

- **[P2.4]** [cg-documentation / cg-reproducibility] `.cg-docs/work-reports/2026-07-23-wb-institutional-report-writing-skill.md:45` - The final execution report still showed the top-level constraint table as `pending` after the work was marked completed. [safe_auto]
  **Why**: The report's evidence and final-status sections said completed, but the constraint table still read as a blocked Phase 2 snapshot.
  **Fix**: Update the final constraint table so it reflects the completed state instead of stale pending placeholders.
  **Status**: Fixed in this review pass.

- **[P2.5]** [cg-data-quality] `scripts/validate_wb_writing_skill.py:357` - Eval-result validation checks expected companion file paths exist, but it does not validate the internal payloads of the referenced type, benchmark, grading, and feedback JSON files. [manual]
  **Why**: A result record can pass while its companion artifacts are empty or semantically inconsistent. The current tests also create `{}` placeholders for those files, which masks the gap.
  **Fix**: Extend `validate_eval_result()` to load and validate the referenced payloads for `schema_version`, `document_type`, and required structure, then update tests so malformed companion artifacts fail deterministically.

### ✅ Passed

- `cg-performance`: No issues found.

### Triage

Autofix complete: applied 4 safe fixes (files: `roadmap.json`, `.cg-docs/active-state/current.json`, `scripts/tests/test_validate_wb_writing_skill.py`, `tests/prompt-tools.Tests.ps1`, `.cg-docs/work-reports/2026-07-23-wb-institutional-report-writing-skill.md`), 5 manual fixes need your review, 0 advisory notes filed.

Validation after autofix:

- `.venv\Scripts\python.exe -m pytest scripts/tests/test_validate_wb_writing_skill.py -q` -> 19 passed
- `. tests\Run-Tests.ps1 -File prompt-tools` -> `passed: true`, `failedCount: 0`, `filteredFiles: "prompt-tools"`
- `Invoke-Pester tests/roadmap.Tests.ps1 -Quiet` -> passed

> Review report saved to `.cg-docs/reviews/2026-07-23-wb-report-writing-technical-methodology-review.md`. Use `/cg-fix-triage` in a future session to apply findings by ID (for example `/cg-fix-triage P1.1 P2.5`) or by priority level (for example `/cg-fix-triage P1`).

## Review Summary

- **Fixed**: 4 findings
- **Skipped**: 0 findings
- **Remaining**: 5 findings

**What would you like to do next?**
1. **`/cg-review mode:verify`** - Verify fixes converged (suppresses fix-consequence P2/P3 findings) *(ensure fixes are committed or staged first)*
2. **`/cg-fix-triage`** - Apply remaining findings in a future session
3. **`/cg-compound`** - Capture learnings from this review
4. **`/cg-fixbug`** - Document a bug that was found and fixed
5. **Ready to merge** - All issues resolved, no further action needed
