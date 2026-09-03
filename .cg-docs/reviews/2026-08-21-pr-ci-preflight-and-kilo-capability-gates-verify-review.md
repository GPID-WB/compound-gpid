---
date: 2026-08-21
depth: light
parent-review: ".cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase5-review.md"
type: verification
plan: ".cg-docs/plans/2026-08-21-pr-ci-preflight-and-kilo-capability-gates.md"
findings:
  P1.1: fixed
  P1.2: fixed
  P1.3: fixed
  P1.4: fixed
  P1.5: fixed
  P1.6: fixed
  P1.7: fixed
  P1.8: fixed
  P1.9: fixed
  P1.10: fixed
  P1.11: fixed
  P2.1: fixed
  P2.2: fixed
  P2.3: fixed
  P2.4: fixed
---

# Verification Review: PR CI Preflight And Kilo Capability Gates

## Review Context

- **Review mode**: verify (light-only)
- **Parent review**: `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-phase5-review.md`
- **Files reviewed**: canonical preflight/generator/projection scripts, tests, workflow, prompts, docs, and generated-tree parity paths
- **Suppression context**: P0.1, P0.2, P0.3, P1.3, and P1.4 were fixed in the parent review. P0/P1 findings remain reportable; no P2/P3 finding in this pass was within an explicitly fixed parent scope.
- **Protected artifacts**: no finding recommends deleting, replacing, renaming, or moving `.cg-docs/`, `compound-gpid.md`, `compound-gpid.local.md`, `roadmap.json`, `SCHEMA_VERSION`, or `.github/`.

## Findings

### P1 - CRITICAL

- **[P1.1]** [cg-code-quality/cg-testing] `scripts/cg_pr_preflight.py:335` -- Kilo capability results are not wired into the preflight gate.
  **Why**: `PreflightResult.kilo` is never populated, the CLI never consumes bounded `cg_kilo_preflight.py` evidence, and blocking Kilo outcomes cannot affect the exit code even though prompts and docs claim they do.
  **Fix**: Add bounded Kilo-result input, populate `kilo`, validate status-specific evidence, and make blocking or malformed outcomes nonzero while preserving neutral host absence.

- **[P1.2]** [cg-code-quality/cg-testing] `scripts/cg_pr_preflight.py:548` -- Git tracking failures fail open during cache validation.
  **Why**: A failed `git ls-files` call is converted to an empty set, so tracked cache artifacts can be classified as local-only and pass the release gate.
  **Fix**: Propagate Git inspection errors and fail closed whenever tracked-versus-local cache provenance cannot be established.

- **[P1.3]** [cg-code-quality/cg-testing] `.github/prompts/cg-commit-push-pr.prompt.md:128` -- Selector-reported Pester groups are ignored.
  **Why**: The prompt promises to run `pester_files` returned by the preflight but hardcodes only `prompt-tools,model-assignments`, allowing link, unlink, or parity changes to bypass their focused tests.
  **Fix**: Build and validate the safe-runner `-File` list from `pester_files`, retaining only registered groups and adding prompt/model groups only when selected.

- **[P1.4]** [cg-code-quality] `.github/prompts/cg-verify-pr.prompt.md:75` -- Malformed or unknown CI check statuses are not fail-closed.
  **Why**: The prompt handles null or empty rollups but does not require well-shaped check objects or recognized status/conclusion values before classification.
  **Fix**: Validate the rollup array, required fields, and closed status/conclusion vocabulary; route malformed or unknown entries to manual diagnosis.

- **[P1.5]** [cg-testing] `scripts/cg_pr_preflight.py:398` -- Project suite/config changes can be classified as no-impact.
  **Why**: Changes to `compound-gpid.local.md` can alter suite, language, and capability closure without selecting native, module, or projection gates.
  **Fix**: Classify active project configuration and manifest changes as native/projection-impacting and add CG-only and CG+CR coverage.

- **[P1.6]** [cg-testing] `scripts/cg_pr_preflight.py:34` -- The authoritative native list omits the projection parity suite.
  **Why**: `scripts/tests/test_project_projection.py` is not in `NATIVE_PYTEST_FILES`, so generator/projection closure checks do not run through the CI-owned preflight.
  **Fix**: Add `scripts/tests/test_project_projection.py` to the canonical native command and assert its presence in the workflow contract.

- **[P1.7]** [cg-code-quality/cg-testing] `scripts/tests/test_project_projection.py:273-287` -- Generator/projection parity bypasses projection's own asset-loading path.
  **Why**: The test passes one prefiltered `assets` object into both generator and projection, so projection-specific manifest scanning can diverge without detection.
  **Fix**: Load generator and projection assets independently from the same committed closure, then compare memberships and add an unowned-asset failure fixture.

- **[P1.8]** [cg-testing] `scripts/tests/test_target_drift.py:219` -- Drift tests reject local cache noise despite the nonfatal cache contract.
  **Why**: Current filesystem scans can fail on untracked `__pycache__` or `.pyc` files even though preflight correctly reports excluded local cache as nonfatal.
  **Fix**: Base committed drift checks on Git blobs and manifest references, ignore untracked local cache, and retain canonical-skill/generated-tree fixtures.

- **[P1.9]** [cg-testing] `.github/prompts/cg-verify-pr.prompt.md:154` -- Base history is inspected before fetching and validating the actual PR base.
  **Why**: Trailer history can use stale or missing local history before `git fetch`; fetch, merge-base, and rebase failures are not explicitly required to halt.
  **Fix**: Fetch the resolved PR base first, require successful commands and a valid merge-base, then count trailers; recompute after rebase.

- **[P1.10]** [cg-testing] `.github/prompts/cg-verify-pr.prompt.md:147` -- Dirty-worktree protection does not check `git status` success.
  **Why**: Empty output from a failed `git status --porcelain` could be treated as clean before rebase, edits, staging, and commit.
  **Fix**: Require exit code zero and empty output for both pre-fix and baseline status checks.

- **[P1.11]** [cg-testing] `.github/workflows/tests.yml:201` -- Certified-host integration can pass while the integration test is skipped.
  **Why**: Preflight can select a Kilo executable from `PATH`, while `test_kilo_coexistence.py` searches only extension directories and skips when none are found.
  **Fix**: Align integration-test discovery with the preflight-selected executable and fail the certified job when real integration coverage is skipped.

### P2 - IMPORTANT

- **[P2.1]** [cg-code-quality] `scripts/cg_pr_preflight.py:194-203` -- Cache reporting is unbounded.
  **Why**: Every discovered cache path is serialized and printed, allowing large local cache trees to overwhelm CI logs or the agent context.
  **Fix**: Emit bounded counts and path samples while retaining all fatal paths needed for remediation.

- **[P2.2]** [cg-testing] `tests/prompt-tools.Tests.ps1:5075` -- Exact-job/manual-route assertions retain stale or vacuous checks.
  **Why**: The old no-run assertion checks only for the phrase `No run found`, and alternation-based checks do not independently prove URL parsing, ordering, and no-latest-run behavior.
  **Fix**: Split assertions for `detailsUrl`, anchored run/job parsing, exact `gh run view --job` syntax, manual routing, and absence of every run-list fallback.

- **[P2.3]** [cg-testing] `docs/reference.md:217` -- Certified-host configuration and protection requirements are undocumented.
  **Why**: The documentation covers neutral Kilo outcomes but omits certified runner/version/SHA variables, protected-environment approval, trusted-event/ref constraints, and evidence artifacts.
  **Fix**: Document the certified-host operator prerequisites, protected event boundary, trusted checkout, hash verification, and evidence outputs.

- **[P2.4]** [cg-testing] `scripts/tests/test_cg_pr_preflight.py:44` -- Full-gate coverage stops at pure change derivation.
  **Why**: Tests do not exercise CLI full-gate selection, committed drift inclusion, all module commands, or native-run suppression after ordinary history failure.
  **Fix**: Add command-selection and `main()` coverage for zero-before/full-gate, missing-history blocking, and prepare-versus-committed execution.

## Passed

- `@cg-code-quality`: reviewed canonical Python, prompt, workflow, docs, and generated parity surfaces; findings are listed above.
- `@cg-testing`: reviewed focused tests, deterministic Kilo coverage, prompt assertions, workflow contracts, and phase-aware preflight behavior; findings are listed above.

## Outcome

Verification found 15 open findings: P0: 0, P1: 11, P2: 4, P3: 0. `mode:verify` applied no fixes.
