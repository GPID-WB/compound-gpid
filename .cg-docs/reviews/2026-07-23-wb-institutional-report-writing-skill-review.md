---
date: 2026-07-24
depth: standard
type: standard
plan: .cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md
findings:
  P1.1: fixed
  P1.2: skipped
  P1.3: fixed
  P1.4: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
  P2.5: fixed
  P2.6: fixed
---

## Review Report

**Review mode**: standard
**Files reviewed**: 112
**Findings**: 10 (P0: 0, P1: 4, P2: 6, P3: 0)

### P1 — CRITICAL (must fix before merge)

- **[P1.1]** [cg-data-quality] `scripts/validate_wb_writing_skill.py:481` — Required grading guardrails could be downgraded to optional and still pass the deterministic validator.
  **Why**: The grading-companion check verified that each required guardrail id existed and that `required` was boolean, but it did not enforce `required: true` for those mandatory criteria. A malformed grading artifact could therefore preserve all expected ids while silently weakening the contract.
  **Fix**: Require `required: true` for every id in `REQUIRED_GUARDRAILS` and add a negative pytest that flips one mandatory criterion to `false`.
  **Tag**: [safe_auto]

- **[P1.2]** [cg-architecture / cg-documentation / cg-data-quality] `.cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md:68` — The parent shared-contract artifact still documents a stale source-pack schema.
  **Why**: The parent plan still publishes `terminology_status: approved|not-required` and omits enforced fields such as `intended_audience`, `disclaimer_requirement`, and `required_disclaimers`, while the executable validator requires the current `approved|unresolved` enum and those additional fields. That lets future child-plan work follow the parent plan and still fail the validator.
  **Fix**: Update the parent plan’s Evidence Artifact Schemas and validation prose so the human-owned contract matches the current machine-enforced validator exactly.
  **Tag**: [manual]

- **[P1.3]** [cg-documentation] `docs/reference.md:405` — The user-facing skills reference still omits `cg-skill-wb-report-writing`.
  **Why**: The branch delivers the World Bank report-writing skill as a committed public capability, but the canonical Skills table still has no entry for it. That leaves the repo’s primary reference surface out of sync with the shipped feature set.
  **Fix**: Add a `cg-skill-wb-report-writing` row to the Skills table with a concise description consistent with the shipped skill router.
  **Tag**: [manual]

- **[P1.4]** [cg-version-control] `.gitignore:78` — `.agents/*` still ignores newly generated mirror files in a tree that is treated as committed product surface elsewhere in the branch.
  **Why**: The branch treats `.github` as canonical source and committed native-platform trees as required mirrors, but the ignore rule can silently suppress newly generated `.agents` artifacts from source control. That makes parity drift possible even when generator and drift-test flows succeed locally.
  **Fix**: Narrow the ignore rule so committed mirror outputs remain trackable, or document and enforce a different ownership model consistently across generator, drift tests, and review expectations.
  **Tag**: [manual]

### P2 — IMPORTANT (should fix)

- **[P2.1]** [cg-code-quality] `scripts/validate_wb_writing_skill.py:143` — Repo-relative evidence validation accepted directories where file artifacts were required.
  **Why**: The validator resolved repo-relative paths and required them to exist, but it did not require them to be files. Directory paths could therefore satisfy a contract intended for concrete evidence artifacts.
  **Fix**: Require existing repo-relative evidence paths to resolve to files and add a negative pytest for directory inputs.
  **Tag**: [safe_auto]

- **[P2.2]** [cg-reproducibility] `scripts/tests/test_target_drift.py:112` — The new drift test relied on locale-dependent text decoding.
  **Why**: `read_text()` without an explicit codec made the parity check depend on the runner’s default encoding. That weakens a deterministic cross-platform test, especially on Windows.
  **Fix**: Read both files with `encoding="utf-8"`.
  **Tag**: [safe_auto]

- **[P2.3]** [cg-code-quality / cg-testing] `scripts/brain/utils.py:352` — The Windows retry path falls back to in-place overwrite, which breaks the helper’s atomic-write contract and is not regression-tested.
  **Why**: The helper now advertises an atomic write path but, after repeated `PermissionError`s, writes directly to the destination file. That means the exact platform-specific path added to improve resilience no longer preserves atomic replace semantics, and there is no focused test proving the fallback behavior is acceptable.
  **Fix**: Either preserve atomic semantics by surfacing the error after bounded retries, or explicitly narrow the helper’s contract and add a regression test for the Windows fallback path.
  **Tag**: [manual]

- **[P2.4]** [cg-reproducibility] `.cg-docs/cost/wb-writing-final/context-audit.json:2116` — Committed audit artifacts still embed wall-clock generation timestamps.
  **Why**: Both `.cg-docs/cost/wb-writing-final/context-audit.json` and `.cg-docs/token/regression-check.json` include volatile `generated` timestamps. Re-running the same checks on another machine or later time changes committed evidence even when the substantive audit result is identical.
  **Fix**: Omit volatile timestamps from committed audit artifacts, or normalize/ignore them in the artifact writer and regression comparison path.
  **Tag**: [manual]

- **[P2.5]** [cg-data-quality] `.cg-docs/plans/2026-07-23-wb-institutional-report-writing-skill.md:13` — The parent work-report evidence link is still outside the deterministic validator contract.
  **Why**: The branch treats the parent execution report as completion evidence through `execution-report` frontmatter and reciprocal work-report linkage, but the validator only checks source packs, eval results, and child-plan frontmatter. A stale or broken parent evidence link could therefore survive the final validation gate.
  **Fix**: Extend deterministic validation to resolve the parent `execution-report` path, require the work-report file to exist, and verify reciprocal linkage plus completed status.
  **Tag**: [advisory]

- **[P2.6]** [cg-testing] `scripts/tests/test_target_drift.py:100` — Generated-tree drift coverage is still path-based enough to miss stale committed mirror content.
  **Why**: The current drift checks guard against missing or extra files and protect `.github/` immutability, but they do not comprehensively assert content parity across committed mirror trees. A stale generated file can therefore survive if the expected path set stays unchanged.
  **Fix**: Add content-parity checks for the committed mirror outputs, or expand the drift suite with hash/content assertions for the generated files that are treated as product surface.
  **Tag**: [advisory]

### ✅ Passed

- `cg-performance`: No issues found.

### Triage

Autofix complete: applied 3 safe fixes (files: `scripts/validate_wb_writing_skill.py`, `scripts/tests/test_validate_wb_writing_skill.py`, `scripts/tests/test_target_drift.py`), 5 manual fixes need your review, 2 advisory notes filed.

Validation after autofix:

- `python -m pytest scripts/tests/test_validate_wb_writing_skill.py -q` → 23 passed
- `python -m pytest scripts/tests/test_target_drift.py -q` → 3 passed

> Review report saved to `.cg-docs/reviews/2026-07-23-wb-institutional-report-writing-skill-review.md`. Use `/cg-fix-triage` in a future session to apply findings by ID (e.g., `/cg-fix-triage P1.2 P2.3`) or by priority level (e.g., `/cg-fix-triage P1`).

## Review Summary

- **Fixed**: 3 findings
- **Skipped**: 0 findings
- **Remaining**: 7 findings

**What would you like to do next?**
1. **`/cg-review mode:verify`** — Verify the three safe fixes converged after you commit or stage them.
2. **`/cg-fix-triage`** — Apply the remaining manual findings in a follow-up pass.
3. **`/cg-compound`** — Capture any durable lesson from the validator and parity fixes.