---
date: 2026-07-23
depth: standard
type: standard
plan: .cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
---

## Review Report

**Review mode**: standard
**Files reviewed**: 9
**Findings**: 9 (P0: 0, P1: 4, P2: 5, P3: 0)

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-data-quality / cg-architecture] `scripts/validate_wb_writing_skill.py:193` — Source-pack validation does not enforce the documented completeness fields for intended audience and required disclaimers.
  **Why**: The Phase 1 router and shared workflow contract say preflight must block unless the source pack covers approved exemplars, intended audience, required terminology, required disclaimers, and verifiable links. The validator currently enforces approval metadata, terminology metadata, and exemplar structure only, so incomplete source packs can pass the deterministic gate.
  **Fix**: Extend the source-pack schema and validator to require explicit audience and disclaimer fields, or narrow the prose contract until those fields are part of the enforced artifact schema.
  **Tag**: [manual]

- **[P1.2]** [cg-data-quality / cg-architecture] `scripts/validate_wb_writing_skill.py:264` — Eval-result validation does not anchor `benchmark`, `grading`, and `feedback` to canonical skill-local artifact paths for the selected slug.
  **Why**: Only `eval_definition` is pinned to an exact canonical path. The other eval artifacts merely need to exist somewhere inside the repo, so an accepted result can validate against the wrong in-repo artifacts for another type.
  **Fix**: Require canonical slug-specific paths, or at minimum canonical skill-local directory prefixes, for `benchmark`, `grading`, and `feedback`, then keep the existence check as a second gate.
  **Tag**: [manual]

- **[P1.3]** [cg-code-quality] `.github/skills/cg-skill-wb-report-writing/SKILL.md:38` — The router claims that successful preflight loads `references/<type>.md`, but those per-type references do not exist in this Phase 1 slice.
  **Why**: That leaves a dead success branch in the router. The file currently advertises executable continuation that is not actually present yet.
  **Fix**: Either change the router text to explicitly defer the per-type step until child-plan assets exist, or add the referenced per-type files before claiming the branch is available.
  **Tag**: [manual]

- **[P1.4]** [cg-documentation] `.github/skills/cg-skill-wb-report-writing/references/workflows.md:11` — The preflight workflow prose overstates what the current deterministic validator proves.
  **Why**: The workflow reads as if intended audience and disclaimer checks are already part of the fixed artifact contract, but the implementation shipped in this slice does not validate those fields. That mismatch makes the evidence boundary unclear.
  **Fix**: Either implement those shared-preflight fields in the validator or narrow the workflow wording so it distinguishes validator-enforced checks from manual review expectations.
  **Tag**: [manual]

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `scripts/validate_wb_writing_skill.py:67` — Date validation accepted impossible calendar dates.
  **Why**: Regex-only checks allowed invalid values like `2026-02-31`, weakening the deterministic artifact gate.
  **Fix**: Parse dates semantically with `date.fromisoformat()` after the format check.
  **Tag**: [safe_auto]

- **[P2.2]** [cg-testing] `scripts/tests/test_validate_wb_writing_skill.py` — Negative coverage missed invalid child-plan linkage, non-completed status, invalid eval fields, assertion mismatches, and CLI default-root behavior.
  **Why**: Several explicit validator failure branches were untested, leaving deterministic command behavior under-guarded.
  **Fix**: Add focused tests for each missing failure mode and CLI behavior.
  **Tag**: [safe_auto]

- **[P2.3]** [cg-testing / cg-code-quality] `tests/prompt-tools.Tests.ps1:6795` — New behavioral assertions used soft alternation that could pass through dead arms.
  **Why**: Broad regex alternation allows real contract regressions to survive when only one term remains.
  **Fix**: Split compound expectations into exact independent checks.
  **Tag**: [safe_auto]

- **[P2.4]** [cg-documentation] `.github/skills/cg-skill-wb-report-writing/references/terminology.md:11` and `tests/prompt-tools.Tests.ps1:1` — Documentation wording was inconsistent and the Pester header claimed outdated version compatibility.
  **Why**: `pending` contradicted the documented `approved`/`unresolved` terminology state, and the prompt-tools header conflicted with the repo’s Pester 4.10.1 requirement.
  **Fix**: Normalize the terminology state to `unresolved` and update the Pester header guidance.
  **Tag**: [safe_auto]

- **[P2.5]** [cg-version-control / cg-reproducibility] `scripts/validate_wb_writing_skill.py:353` and `.github/skills/cg-skill-wb-report-writing/evals/` — The validator defaulted to the caller’s current directory and the canonical eval artifact tree was only partially scaffolded.
  **Why**: Ambient working-directory dependence made CLI behavior non-deterministic, and missing placeholder directories left part of the artifact contract implicit.
  **Fix**: Default the CLI root from the script-derived repository root and add tracked placeholder directories for canonical eval artifact locations.
  **Tag**: [safe_auto]

### ✅ Passed

- `cg-performance`: No issues found.

### Triage

Autofix complete: applied 5 safe fixes (files: `scripts/validate_wb_writing_skill.py`, `scripts/tests/test_validate_wb_writing_skill.py`, `tests/prompt-tools.Tests.ps1`, `.github/skills/cg-skill-wb-report-writing/references/terminology.md`, `.github/skills/cg-skill-wb-report-writing/evals/benchmarks/.gitkeep`, `.github/skills/cg-skill-wb-report-writing/evals/grades/.gitkeep`, `.github/skills/cg-skill-wb-report-writing/evals/feedback/.gitkeep`), 4 manual fixes need your review, 0 advisory notes filed.

Validation after autofix:

- `python -m pytest scripts/tests/test_validate_wb_writing_skill.py -q` → 15 passed
- `. tests\Run-Tests.ps1 -File prompt-tools` → `passed: true`, `failedCount: 0`

> Review report saved to `.cg-docs/reviews/2026-07-23-wb-institutional-report-writing-skill-review.md`. Use `/cg-fix-triage` in a future session to apply findings by ID (for example `/cg-fix-triage P1.2 P1.4`) or by priority level (for example `/cg-fix-triage P1`).

## Review Summary

- **Fixed**: 5 findings
- **Skipped**: 0 findings
- **Remaining**: 4 findings

**What would you like to do next?**
1. **`/cg-review mode:verify`** — Verify fixes converged (suppresses fix-consequence P2/P3 findings) *(ensure fixes are committed or staged first)*
2. **`/cg-fix-triage`** — Apply skipped findings in a future session
3. **`/cg-compound`** — Capture learnings from this review
4. **`/cg-fixbug`** — Document a bug that was found and fixed
5. **Ready to merge** — All issues resolved, no further action needed