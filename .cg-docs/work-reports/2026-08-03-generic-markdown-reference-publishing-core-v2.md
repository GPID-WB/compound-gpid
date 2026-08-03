---
date: 2026-08-03
plan: ".cg-docs/plans/2026-08-03-generic-markdown-reference-publishing-core-v2.md"
status: completed
---

# Execution Report: Generic Markdown and Reference Publishing Core (Revised)

## Plan Reference

`.cg-docs/plans/2026-08-03-generic-markdown-reference-publishing-core-v2.md`

## Active Deviation Policy

- Stored policy: `ask`
- Runtime override: `deviate:auto`
- Active policy: `autonomous`

## Run 1 - 2026-08-03

- Scope: all phases, explicitly requested by the user
- Review mode: `review:auto`
- Branch: `feat/curated-artifact-themes`
- Status: completed

## Completed Steps and Phases

- Step 1 - Separate generic parsing from strict artifact validation (completed
  2026-08-03).
- Step 2 - Repair non-clobbering publication and bounded reads (completed
  2026-08-03).
- Step 3 - Implement paths, ownership, provenance v2, and mode resolution
  (completed 2026-08-03).
- Phase 1 - Secure Contracts And Generic Identity (completed 2026-08-03).
- Step 4 - Extract the reference theme and shared semantic renderer (completed
  2026-08-03).
- Step 5 - Implement safe links, bounded images, CSP, and HTML validation
  (completed 2026-08-03).
- Step 6 - Publish and freshness-check strict and generic views (completed
  2026-08-03).
- Phase 2 - Reference Rendering And Generic Publication (completed
  2026-08-03).
- Step 7 - Add cross-platform launchers and installation (completed
  2026-08-03).
- Step 8 - Verify exclusions and document the core (completed 2026-08-03).
- Phase 3 - Launchers, Installation, And Context Boundaries (completed
  2026-08-03).
- Step 9 - Run focused and full core verification (completed 2026-08-03).
- Phase 4 - Independent Core Release Gate (completed 2026-08-03).

## Deviations

- The explicit `ALL phases` argument authorizes continuation across successful
  phase boundaries without the normal continue-or-stop prompt. Scope and
  evidence gates remain unchanged.
- A parallel filtered/full Pester attempt raced on shared `tests/last-run.json`.
  Under the autonomous policy, the ambiguous records were discarded and both
  gates were rerun sequentially. Only the isolated sequential records count as
  evidence.
- Windows release gates exposed checkout-dependent CRLF bytes in nested
  Markdown skill resources plus a 60-second drift timeout. The generator now
  normalizes Markdown bundle resources to UTF-8 LF before hashing/emission,
  opaque resources remain byte-exact, and the nested drift timeout is 360
  seconds based on a measured 247-second passing run.

## Accepted Exceptions

None.

## Evidence

| ID | Phase | Evidence | Status | Artifact |
|----|-------|----------|--------|----------|
| V1 | 1 | Strict schemas and generic parser/source ownership. | passed - 145 tests | Focused strict/generic contract, parser, validator, model, coverage, path, theme, provenance, and mode tests. |
| V2 | 1 | Non-clobbering publication and bounded secure reads. | passed - 45 tests, 9 platform skips | Focused secure filesystem, writer, publishing-security, target path, and determinism tests. |
| V3 | 2 | Typed-root rejection, ownership, provenance v2, and modes. | passed - 78 tests, 8 platform skips | Focused path, theme, provenance, mode, strict/generic CLI, integration, and writer tests. |
| V4 | 2 | Reference semantics and safe generic rendering. | passed - 138 tests | Focused strict/generic renderer, security, bitmap, accessibility, design, coverage, contract, and validator tests. |
| V5 | 3 | Generic launcher and installer parity. | passed - exact filtered Pester plus 11 Python tests | `filteredFiles: [install, bash-scripts]`; both file records pass with zero failures. |
| V6 | 3 | Documentation and model-context exclusions. | passed - 184 Python tests and 33-page site check | Generic view sentinels excluded from Brain, audit, duplicate, summary, and integration inputs. |
| V7 | final | Complete Python suite. | passed - 1336 tests, 38 platform skips, 5 subtests | Final `pytest -q` run. |
| V8 | final | Canonical unfiltered Pester suite. | passed - 2343/2343 | `tests/last-run.json`: `filteredFiles: null`, zero failures. |
| V9 | final | Diagnostics and current Plan view. | passed | Workspace diagnostics clear; Plan view rechecked and reports `current`. |

## Constraints Check

| ID | Phase | Constraint | Status |
|----|-------|------------|--------|
| C1 | 1 | Generic publishing cannot accept typed artifact roots or claim strict validation. | passed - independent parser/resolver rejection and strict regressions |
| C2 | 2 | Reference semantics and exact source ownership cannot regress. | passed - strict byte hashes unchanged and exact-once generic ownership verified |
| C3 | 1 | Every destination has one source owner in a registered views namespace. | passed - portable path, output identity, ownership, and case tests |
| C4 | 1 | Publish and rollback preserve competing bytes with no-replace semantics. | passed - Windows handle tests and POSIX no-replace/race contracts |
| C5 | final | Runtime remains dependency-, model-, network-, browser-, and Open Design-free. | passed - static integration scan covers every generic publisher runtime module |

## Brain Findings Applied

The bounded Brain query returned the superseded core Plan and this revised
Plan only. The revised Plan remains authoritative; no stale predecessor detail
was carried forward independently.

## Remaining Uncertainty

- POSIX native no-replace runtime branches are skipped on Windows; their
  source contract and native implementation are present, and the final suite
  must also run on a POSIX CI host before release.
- All review findings, including P1.8, were fixed and re-verified during
  closure. The feature branch was fast-forwarded to `origin/main` at `09a494c`,
  and `git rev-list --left-right --count HEAD...origin/main` is `0 0`.

## Phase Boundary Evidence

- Phase 1 V1: passed, 145 focused Python tests.
- Phase 1 V2: passed, 45 focused Python tests with 9 platform-specific skips.
- Full canonical Pester gate: `passed: true`, `failedCount: 0`,
  `filteredFiles: null`.
- Phase 2 V3: passed, 78 focused Python tests with 8 platform-specific skips.
- Phase 2 V4: passed, 138 focused Python tests; both strict renderer SHA-256
  baselines remained unchanged.
- Phase 2 full canonical Pester gate: `passed: true`, `failedCount: 0`,
  `filteredFiles: null`.
- Phase 3 V5: exact filtered Pester passed for `install` and `bash-scripts`;
  both durable per-file records passed with zero failures.
- Phase 3 V6: passed, 184 focused Python tests with 3 platform-specific skips;
  documentation site check passed 33 navigable pages and 6 groups.
- Phase 3 full canonical Pester gate: `passed: true`, `failedCount: 0`,
  `filteredFiles: null`.
- Final V7 Python gate: 1336 passed, 38 platform-specific skips, 21 expected
  warnings, and 5 subtests passed.
- Final documentation gate: 33 navigable pages, 6 groups, complete skills
  catalog.
- Final V8 Pester gate: 2343/2343 passed, zero failures,
  `filteredFiles: null`.
- Final V9: workspace diagnostics clear and the canonical Plan view current.

## Mechanical Self-Review

- No debug calls, TODO/FIXME/HACK/XXX markers, or secret-like literals were
  added to the runtime surface.
- Every new public Python function has the required docstring sections and
  focused tests.
- No package/lockfile changes, model/network/browser/Open Design runtime
  imports, generated platform-tree edits, or premature editorial assets were
  introduced by implementation.
- Existing user-authored brainstorm, superseded Plan, editorial follow-up Plan,
  and derived views in the dirty worktree were preserved and not claimed as
  implementation output.

## Closure Verification - 2026-08-03

- Complete Python suite: `1336 passed, 38 skipped, 21 warnings, 5 subtests
  passed`.
- Documentation site: passed with 33 navigable pages, 6 groups, and a complete
  skills catalog.
- Canonical unfiltered Pester: `passed: true`, `2343/2343`,
  `failedCount: 0`, `filteredFiles: null`.
- Workspace diagnostics: no errors.
- Canonical Plan view: current after regenerating only the stale Plan view.
- `git diff --check`: passed.
- Package and lockfile changes: none.
- Unintended `.github`, `.claude`, `.agents`, and `.opencode` changes: none.
- `bin/cg-publish-markdown`: Git mode `100755`.
- Generated HTML bodies were not loaded into context.
- Branch ancestry after `git fetch origin` and fast-forward reconciliation:
  `HEAD...origin/main = 0 0`.

## Final Status

Completed. All implementation gates pass, all review findings are fixed, and
the branch is aligned with `origin/main`.