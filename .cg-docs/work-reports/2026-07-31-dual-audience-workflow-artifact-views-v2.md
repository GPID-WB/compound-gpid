---
date: 2026-07-31
plan: ".cg-docs/plans/2026-07-31-dual-audience-workflow-artifact-views-v2.md"
status: blocked
---

# Execution Report: Dual-Audience Workflow Artifact Views (Revised)

## Plan Reference

`.cg-docs/plans/2026-07-31-dual-audience-workflow-artifact-views-v2.md`

## Active Deviation Policy

- Stored policy: `ask`
- Runtime override: `deviate:auto`
- Active policy: `autonomous`

## Run 1 — 2026-07-31

- Scope: Phase 1 — Executable Contract and Mandatory Validation
- Review mode: `review:auto`
- Branch: `feat/human-readable-workflow-artifacts`
- Status: active

## Run 2 — 2026-07-31

- Scope: all remaining phases (2–5), explicitly requested by the user
- Review mode: `review:auto`
- Stored deviation policy: `ask`
- Runtime override: `deviate:auto` (`autonomous`)
- Branch: `feat/human-readable-workflow-artifacts`
- Resume point: Phase 2, Step 4
- Status: active

## Completed Steps and Phases

- Step 1 — Define the executable schema and closed Markdown grammar (completed
	2026-07-31).
- Step 2 — Implement the typed document and source ledger (completed
	2026-07-31).
- Step 3 — Implement fence-aware parsers, validators, and validation-only API
	(completed 2026-07-31).
- Phase 1 — Executable Contract and Mandatory Validation (completed
	2026-07-31).
- Step 4 — Implement normalized identity, provenance, and secure output
  mutation (completed 2026-07-31).
- Step 5 — Build type-specific templates and source-coverage enforcement
	(completed 2026-07-31).
- Step 6 — Harden content security, offline behavior, print, and accessibility
	(completed 2026-07-31).
- Phase 2 — Secure Deterministic Rendering (completed 2026-07-31).
- Step 7 — Produce and validate the Open Design evidence matrix (completed
	2026-07-31).
- Step 8 — Freeze accepted tokens, components, responsive rules, and print
	rules (completed 2026-07-31).
- Phase 3 — Open Design Evidence and Frozen Presentation (completed
	2026-07-31).
- Step 9 — Implement explicit and automatic one-file CLI modes (completed
	2026-07-31).
- Step 10 — Add cross-platform launchers and installer lifecycle support
	(completed 2026-07-31).
- Step 11 — Add mandatory workflow validation and model-context exclusions
	(completed 2026-07-31).
- Step 12 — Exclude views from scanners, audits, summaries, and duplicate
	content paths (completed 2026-07-31).
- Step 13 — Regenerate all native targets and prove parity (completed
	2026-07-31).
- Phase 4 — CLI, Workflow Integration, Isolation, and Target Parity (completed
	2026-07-31).
- Step 14 — Document authority, lifecycle, commands, and recovery (completed
	2026-07-31).
- Step 15 — Run end-to-end, audit, documentation, and full-suite gates
	(completed 2026-07-31).
- Phase 5 — Documentation and Release Evidence (completed 2026-07-31).

## Deviations

- Run 2 treats the explicit `ALL phases` argument as advance authorization to
	continue across successful phase boundaries without pausing for the usual
	continue/stop question. This changes workflow pacing only, not scope or gates.
- V6's existing drift tests compare generated files to committed Git blobs in
	`HEAD`, so they necessarily fail for legitimate uncommitted canonical and
	generated changes. Under `autonomous`, the exact generator and V6 pytest
	command ran in an ephemeral committed mirror of the current worktree instead.
	This preserved the clean-HEAD invariant without modifying tests or committing
	the user's repository; all 152 tests passed there. In the live worktree, the
	other 149 V6 tests passed and only the three documented HEAD-comparison tests
	failed before the mirror check.

## Accepted Exceptions

None.

## Evidence

| ID | Phase | Evidence | Status | Artifact |
|----|-------|----------|--------|----------|
| V1 | 1 | Executable schema, typed model, parser, and validator tests pass. | passed — 48 tests | `pytest -q scripts/artifact_views/tests/test_contract.py scripts/artifact_views/tests/test_model.py scripts/artifact_views/tests/test_parser.py scripts/artifact_views/tests/test_validator.py` |
| V2 | 2 | Secure path mutation, provenance, coverage, renderer, security, and accessibility tests pass. | passed — 90 tests | `pytest -q scripts/artifact_views/tests/test_paths.py scripts/artifact_views/tests/test_writer.py scripts/artifact_views/tests/test_provenance.py scripts/artifact_views/tests/test_renderer.py scripts/artifact_views/tests/test_coverage.py scripts/artifact_views/tests/test_security.py scripts/artifact_views/tests/test_accessibility.py scripts/tests/test_target_path_safety.py` |
| V3 | 3 | Open Design evidence matrix is complete and all-pass. | passed — 2 artifacts, 6 viewport rows | `.cg-docs/work-reports/2026-07-31-dual-audience-workflow-artifact-views.design-evidence.json` |
| V4 | 4 | CLI, integration, failure-preservation, scanner, and audit tests pass. | passed — 152 tests including discovered diff-summary path | `pytest -q scripts/artifact_views/tests/test_cli.py scripts/artifact_views/tests/test_integration.py scripts/brain/tests/test_scanner.py scripts/tests/test_audit_context.py scripts/tests/test_cg_summary.py` |
| V5 | 4 | Installer, launcher, and prompt workflow contracts pass. | passed — bash and prompt-tools Pester gates; CMD static contract | `tests/last-run.json` plus independent CMD contract check |
| V6 | 4 | Native targets regenerate and parity checks pass. | passed — 780 generated files; 152/152 tests in ephemeral committed mirror | exact V6 generator/pytest command in committed mirror |
| V7 | 4 | Model-facing consumers exclude generated HTML bodies. | passed — path-only prompt assertions and sentinel tests across Brain, audit, duplicates, and diff summaries | `tests/prompt-tools.Tests.ps1` and Python sentinel suites |
| V8 | final | Context audit passes without view ingestion or unsupported claims. | passed — zero guardrail failures, view source records, sentinels, duplicates, or savings claims | `.cg-docs/cost/artifact-views-final/context-audit.json` |
| V9 | final | Documentation checks pass. | passed — 33-page site and 19 lifecycle contracts | `node scripts/check-docs-site.js && pytest -q scripts/tests/test_target_documentation.py` |
| V10 | final | Complete Python suite passes. | passed — 1131 tests and 5 subtests | `pytest -q` in ephemeral committed mirror |
| V11 | final | Canonical unfiltered Pester suite passes. | passed — 2283/2283 | `tests/last-run.json` |

## Constraints Check

| ID | Phase | Constraint | Status |
|----|-------|------------|--------|
| C1 | 1 | Markdown remains the sole semantic authority. | passed — typed models retain canonical source identity and byte coverage |
| C2 | 1 | Validation cannot be bypassed by HTML opt-outs or execution paths. | passed — renderer-independent API, CLI opt-out tests, emitter hooks, and versioned Plan preflight |
| C3 | 2 | Every substantive source block renders exactly once. | passed — pre-serialization bijection tests cover missing, duplicate, unknown, and derived owners |
| C4 | 2 | Source HTML, scripts, styles, and instructions never execute. | passed — structured escaping, URL allowlist, final HTML validation, and adversarial payload tests |
| C5 | 2 | Output is self-contained and offline. | passed — embedded CSS, restrictive CSP, and zero runtime resource dependencies |
| C6 | 2 | Output mutation remains securely contained and race-resistant. | passed — root-pinned and fallback identity checks; real POSIX ancestor-swap tests passed |
| C7 | 3 | Open Design is design-time only. | passed — runtime HTML has no Open Design dependency; CLI/desktop used only for evidence ingestion and native exports |
| C8 | 4 | Markdown saves before rendering and survives every failure. | passed — byte-preservation injection tests and prompt ordering assertions |
| C9 | 4 | Canonical and generated targets remain in parity. | passed — ownership, closure, determinism, path safety, and clean-HEAD drift all verified |
| C10 | 4 | Generated HTML bodies add no model context. | passed — component-scoped exclusions and path-only workflow contracts |
| C11 | final | Version 1 boundaries remain intact. | passed — one-file Brainstorm/Plan views only; no bulk, editing, hosted export, runtime Open Design, or AI summaries |

## Brain Findings Applied

Contract vocabulary must remain aligned across executable schema constants,
validator behavior, fixtures, and tests. Source:
`.cg-docs/solutions/testing-patterns/2026-07-24-cross-file-contract-state-must-align-docs-validator-tests.md`.

## Remaining Uncertainty

- Windows CMD runtime execution is unavailable on macOS; mandatory probe,
	forwarding, and exit-propagation structure is statically verified and covered
	by Windows-only Pester assertions.
- The automatic full review found 4 P0 and 11 P1 findings. Implementation phases
	executed, but the change is not merge-ready until those findings are fixed and
	re-verified. See
	`.cg-docs/reviews/2026-07-31-dual-audience-workflow-artifact-views-v2-review.md`.

## Accepted Design Changes

- Editorial, unframed reading surface with serif display headings and compact
	sans-serif navigation/provenance.
- Restrained neutral paper/surface palette with teal navigation and rust focus
	accents rather than a one-hue treatment.
- Persistent desktop navigation, linear mobile flow, overflow-contained tables,
	and full-content print output.
- No runtime script, remote font, CDN, network request, or Open Design dependency.

## Phase Boundary Evidence

- V1: passed, 48/48 focused Python tests.
- Real-artifact check: the selected compatible-legacy Brainstorm and Plan both
	validate through `validate_path()`.
- Full Pester gate: passed, 2261/2261 tests, `failedCount: 0`,
	`filteredFiles: null` in `tests/last-run.json`.
- Phase 2 V2: passed, 90/90 focused Python tests.
- Phase 2 full Pester gate: passed, `failedCount: 0`,
  `filteredFiles: null` in `tests/last-run.json`.
- Phase 3 V3: passed, 2 artifacts and 6 required viewport rows.
- Frozen design contract: passed, 9 design/accessibility tests.
- Phase 3 full Pester gate: passed, `failedCount: 0`,
  `filteredFiles: null` in `tests/last-run.json`.
- Phase 4 V4/V7 isolation gate: passed, 152 Python tests.
- Phase 4 V5: bash-scripts and prompt-tools Pester gates passed; Windows CMD
	structure independently verified on macOS.
- Phase 4 V6: passed, 152/152 tests in an ephemeral committed mirror.
- Phase 4 full Pester gate: passed, `failedCount: 0`,
	`filteredFiles: null` in `tests/last-run.json`.
- Final V8 context audit: passed with zero guardrail failures, zero generated
	view source records, zero sentinel/duplicate findings, and no savings claim.
- Final V9 documentation gate: passed, 33 navigable pages and 19 contracts.
- Final V10 Python gate: passed, 1131 tests and 5 subtests in an ephemeral
	committed mirror.
- Final target drift gate: passed, 11/11 tests in an ephemeral committed mirror.
- Final V11 Pester gate: passed, 2283/2283 tests, `failedCount: 0`,
	`filteredFiles: null`.

## Final Status

Blocked after implementation — all five phases and V1-V11 evidence gates ran,
but the automatic full review found open P0/P1 security and correctness issues.
