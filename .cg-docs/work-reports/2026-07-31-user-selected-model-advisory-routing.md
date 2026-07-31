---
date: 2026-07-31
plan: ".cg-docs/plans/2026-07-30-user-selected-model-advisory-routing.md"
status: completed
---

# Work Report: User-Selected Models With Advisory Stage Routing

## Run: 2026-07-31 All Phases

- Plan reference: `.cg-docs/plans/2026-07-30-user-selected-model-advisory-routing.md`
- Active deviation policy: `ask` (stored plan policy; no runtime override)
- Review mode: `auto`
- Scope: all four phases, starting at Phase 1

## Completed Steps And Phases

- Phase 1 steps 1-2 implemented: migrated the old assignment checks, added the
  shared advisory contract/examples, and added advisory-schema and provenance
  validation.
- Phase 2 steps 3-4 implemented: removed canonical and generated execution
  model assignments, model-mapping outputs, catalog consumers, and related
  ownership/install enforcement.
- Phase 3 steps 5-6 implemented: added advisory-only guidance to the four
  handoffs and rewrote model documentation around process stages and user
  choice.
- Phase 4 steps 7-8 implemented: regenerated all native targets, updated audit
  outputs, and completed the final static, Python, Pester, and committed-`HEAD`
  drift/release checks.

## Deviations

- None.

## Accepted Exceptions

- None.

## Evidence

| ID | Status | Artifact |
|----|--------|----------|
| V1 | passed | Generator/target Python checks; regenerated targets contain no executable model assignments or mapping artifacts. |
| V2 | passed | `python3 -m pytest scripts/tests/test_model_advisory.py scripts/tests/test_audit_context.py -q`: 80 passed. |
| V3 | passed | Full canonical Pester run: 2,261 passed, 0 failed, unfiltered. |
| V4 | passed | Generated-target documentation tests and Pester prompt/documentation assertions passed. |
| V5 | passed | `python3 -m pytest scripts/tests/test_target_drift.py scripts/tests/test_release_gate_targets.py -q`: 21 passed after commit. |
| V6 | passed | `python3 -m pytest scripts/tests -q`: 429 passed. |
| V7 | passed | `tests/last-run.json` at `2026-07-31T15:03:07Z`: `passed: true`, 2,261/2,261, `failedCount: 0`, `filteredFiles: null`. |
| V8 | passed | `.cg-docs/cost/context-audit.json`: 0 failures, 0 advisory errors, 0 forbidden execution metadata, 5 stages, 5 examples. |

## Constraints Check

| ID | Status | Result |
|----|--------|--------|
| C1 | passed | Static contract, advisory tests, and generated scans preserve advisory-only behavior. |
| C2 | passed | Examples carry capability-first rationale, platform/date provenance, and verification status. |
| C3 | passed | Contract and handoff tests require conditional guidance for unknown vendors/Auto. |
| C4 | passed | Planning, implementation, review, fix triage, and compounding/documentation stages are covered. |
| C5 | passed | `.github/` remains the source; all three native trees were regenerated from it. |
| C6 | passed | Pester ran through `. tests\\Run-Tests.ps1`; `tests/last-run.json` is unfiltered and passing. |

## Remaining Uncertainty

- Runtime model inheritance, picker availability, and platform-specific effort support require observation on the actual supported platforms; static checks must not claim those behaviors.
- The generated trees, committed-`HEAD` drift checks, and release wrapper checks
  now agree. Runtime model inheritance and picker availability remain platform
  observations rather than static claims.

## Blocking Condition

- None. The committed-`HEAD` generated drift and release gates pass.

## Final Status

`completed`
