---
date: 2026-08-15
depth: light
parent-review: .cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase3-review.md
type: verification
findings:
  P1.6: fixed
  P1.7: fixed
  P2.6: fixed
  P2.7: fixed
  P2.8: fixed
  P3.11: fixed
  P3.12: fixed
  P3.13: fixed
  P3.14: fixed
  P3.15: fixed
  P3.16: fixed
---

## Verify Review Report

**Review mode**: verify (light)
**Parent review**: `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase3-review.md`
**Files reviewed**: 24 changed files (projection module, generator, helpers, link/update/unlink ps+sh, target-mapping, regenerated trees, Pester tests, docs)
**Findings**: 11 (P1: 2, P2: 3, P3: 6)

Verification pass after fix-triage of Phase 3. The 21 prior findings were
confirmed genuinely implemented and coherent (P0.1/P1.1-P1.5 journal validation,
per-platform stale scoping, freshness guard, absent-file verify, symlinked
`.compound-gpid` rejection, null-`generatedTreePath` exclusion, `$args` rename,
tautology removal). Two real functional blockers in the new integration were
found, plus partial-application gaps and test-coverage holes.

### P1 — CRITICAL (must fix before merge)

- **[P1.6]** [cg-code-quality] `scripts/link.ps1:745-778` + `scripts/link.sh:661-689` + `scripts/update.ps1:631-645` — manifest-driven link/update hard-fails for the link-directory native platforms (codex, claude-code, opencode), i.e. the default `--platforms all` profile, on all OSes.
  **Why**: link.ps1 creates junctions for `.agents/*`, `.claude/*`, `.opencode/*` installUnits before the projection `--sync` block. `cg_project_projection._reject_unsafe_destination` → `secure_fs.revalidate_destination_ancestors` rejects any destination whose ancestor is a link/reparse point, so the same-run projection of junctioned roots aborts publication ("Linking is blocked by manifest projection failure", exit 1). Affects fresh links too. Kilo (copy-directory) and copilot escape it, which is why the content-match Pester suite misses it.
  **Fix**: For manifest-driven consumers (local config + manifest present), gate the legacy link-directory install of native roots so the projection materializes them (matching the Phase-6 migration intent), or have the projection adopt/replace verified junctioned roots. Add an integration test driving link logic against the real `target-mapping.json` with a junctioned consumer.
  **Tag**: [manual]

- **[P1.7]** [cg-code-quality] `scripts/cg_project_projection.py:452-471` (`_stage_tree`) + `scripts/secure_fs.py:695,1082-1092` — Windows publish of the default closure fails with `WinError 3` creating the atomic-replace temp file for deep skill files (e.g. `cg-skill-wb-report-writing/evals/benchmarks/*.benchmark.json`).
  **Why**: Staging nests under `<project>/.compound-gpid/staging/<32-hex-tx>/<root>/...`; the Windows writer writes a temp sibling with a `.`+32-hex+`.tmp` suffix via `CreateFileW` without a `\\?\` long-path prefix. Deep canonical paths exceed MAX_PATH 260 once staged. Blocks every manifest-driven link/update on Windows (`ERROR_PATH_NOT_FOUND`). Pytest fixtures use short trees, so this is untested.
  **Fix**: Enable long paths in the Windows writer (`\\?\` prefix after absolute normalization) or reduce staging nesting depth. Add a Windows staging test with a deep nested destination.
  **Tag**: [manual]

### P2 — IMPORTANT (should fix)

- **[P2.6]** [cg-code-quality] `scripts/cg_project_projection.py:1139-1180` — prior P2.1 fix only partially applied: `unlink_consumer_projection` still does not require the leading component to be a declared managed root.
  **Why**: Unlink validates entries with `_is_safe_relative` + checksum only; there is no allowlist against declared `projectRoots`/recorded `activeAdapters`. A forged `projection-ownership.json` can authorize deletion of any readable file whose bytes match a recorded sha. The stale-removal half (per-platform root scoping) and the verify `activeAdapters` check are present, but unlink itself is not bounded.
  **Fix**: Bound unlink deletion to the leading components of the declared managed roots (thread the validated mapping or recorded platform roots into the call), and add a forged-entry-preserved regression test.
  **Tag**: [manual]

- **[P2.7]** [cg-testing] `scripts/cg_project_projection.py:299-337` — `_validate_manifest_freshness` (P1.4) has no regression test covering its three failure branches (registry digest, schema version, desired-plan digest).
  **Why**: `test_unknown_platform_fails_closed` sets an invalid digest but the unknown-platform check fires first, so the freshness guard is never reached. The R4/R5 "no stale selection can publish" boundary could silently regress.
  **Fix**: Add tests mutating the live registry / `registryDigest` / `desiredPlanDigest` and asserting `ProjectionError` matching "stale".
  **Tag**: [safe_auto]

- **[P2.8]** [cg-testing] `scripts/tests/test_project_projection.py:516-529` — `test_journal_root_escape_fails_closed` contains a tautological final assertion and does not exercise the P0.1 containment check it claims.
  **Why**: `assert (root/"compound-gpid.md").exists() or not ...` is always true (the exact P3.5 anti-pattern). With a valid hex txId the test always falls through to the rollback branch, never reaching the containment check.
  **Fix**: Point the "escape" test at a real escape setup (e.g. symlinked `.compound-gpid/generations`) or rename it to reflect rollback coverage and drop the tautology.
  **Tag**: [safe_auto]

### P3 — MINOR (nice to have)

- **[P3.11]** `scripts/link.ps1:818,827` — P3.10 not applied: redundant double assignment of `$compProjectionStateDir` still present (above `if` and inside `try`). Remove the inner assignment. [safe_auto]
- **[P3.12]** `scripts/cg_project_projection.py:318-323` + `update.ps1:631-645` — staleness remediation UX: error says "re-run cg-project-manifest" but no `cg-project-manifest` bin exists and update never re-resolves. Point the error at `cg-link`, or wire re-resolution, so "no separate resolution command" holds. [advisory]
- **[P3.13]** `_validate_manifest_freshness` has no direct unit test (see P2.7). Duplicate note for tracking. [safe_auto]
- **[P3.14]** `verify_projection(project_root, plan)` immediately does `del plan`; drop the unused parameter or use it. Cosmetic. [safe_auto]
- **[P3.15]** `_prune_managed_dirs_no_follow` only removes the leading root directory; nested empty dirs remain. Docstring overstates behavior. Minor. [advisory]
- **[P3.16]** `scripts/tests/fixtures/cg_characterization_manifest.json` re-authored to CRLF, so git reports all lines changed though only 4 sha256 values differ. Commit-time LF normalization resolves; have the generator emit LF. [advisory]

### ✅ Passed (prior fixes verified)
- P0.1 journal `transactionId` validation — implemented + regression-tested (`test_invalid_transaction_id_fails_closed`).
- P1.1 recovery planned-destination validation — implemented + tested (`test_journal_planned_destination_escape_fails_closed`).
- P1.2 rejected publish leaves rolled-back journal — implemented + tested.
- P1.3 stale removal scoped per-platform root — implemented + tested.
- P1.5 verify reports absent/non-regular owned files — implemented + tested.
- P2.2 hard-block on resolution failure, P2.4 root-collision validation — implemented + tested.
- P3.1-P3.9 dead-code/`$args`/tautology cleanups — implemented.

**Next**: `/cg-fix-triage` to apply the open findings (P1.6, P1.7, P2.6, P2.7, P2.8, P3.11, P3.13, P3.14).
