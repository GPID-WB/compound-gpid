---
date: 2026-07-28
plan: ".cg-docs/plans/2026-07-27-canonical-native-packaging-foundation.md"
status: active
---

# Work Report: Canonical-to-Native Packaging Foundation

## Resume Run: 2026-07-28 Phases 2-7

- Active deviation policy: `autonomous` (runtime override of stored `ask`)
- Review mode: `auto`
- Scope: all remaining phases, continuing automatically across passed phase gates

## Run: 2026-07-28 Phase 1

- Plan reference: `.cg-docs/plans/2026-07-27-canonical-native-packaging-foundation.md`
- Active deviation policy: `autonomous` (runtime override of stored `ask`)
- Scope: Phase 1, steps 1-2

## Completed Steps And Phases

- 2026-07-28: Step 1, mapping schema and runtime path validation.
- 2026-07-28: Step 2, deterministic pre-write output graph.
- 2026-07-28: Phase 1, Safety And Inventory Primitives.
- 2026-07-28: Steps 3-4 and Phase 2, Pilot Atomic Bundle.
- 2026-07-28: Steps 5-6 and Phase 3, Generated Ownership And Cleanup.
- 2026-07-28: Steps 7-8 and Phase 4, Full Skill Expansion.
- 2026-07-28: Steps 9-10 and Phase 5, Native Dependency Closure.

## Deviations

- Under runtime policy `autonomous`, deferred `instructions` and `shared`
  install units after the full-suite parity gate showed that adding them before
  their assets are emitted would require later-phase linker changes. Their
  `outputPaths` remain configured; install integration stays in its planned
  dependency-closure phase.

## Accepted Exceptions

- None.

## Evidence

| ID | Status | Artifact |
|----|--------|----------|
| V1 | passed | 52 passed: `python3 -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_target_path_safety.py -q` |
| V2 | passed | 10 focused packaging tests; 100 combined Python tests; canonical Pester gate passed. |
| V3 | passed | 17 ownership tests; 163 combined Python tests; canonical Pester gate passed. |
| V4 | passed | 21 recursive packaging and committed-HEAD drift tests passed after the authorized intermediate checkpoint. |
| V5 | passed | 63 exact closure/platform tests; 149 combined Python tests; canonical Pester gate passed. |

## Constraints Check

| ID | Status | Result |
|----|--------|--------|
| C1 | passed | Adversarial containment and no-mutation tests passed. |
| C2 | passed | Schema/runtime parity tests and stdlib import inspection passed; `py_compile` succeeded. |
| C3 | passed | Sentinel, opaque-byte, hash, and executable-mode tests passed. |
| C4 | passed | Modified, unowned, and checksum-mismatched conflict tests preserve content and fail safely. |
| C5 | passed | Recursive all-skill parity and arbitrary regular-file inclusion tests passed. |
| C6 | passed | Existing platform/link behavior passed the canonical Pester gate; Codex subagents remain under `.agents/subagents/`. |

## Remaining Uncertainty

- Later phases must emit and install the configured instruction/shared roots.
- Phase 4's temporary HEAD-evidence block was resolved by the user-authorized
  intermediate checkpoint; V4 subsequently passed.

## Final Status

`active`
