---
date: 2026-08-07
plan: ".cg-docs/plans/2026-08-07-modular-compound-gpid.md"
status: active
---

# Work Report: Modular Compound GPID Architecture

## Run: 2026-08-07 (ALL phases)

- Plan reference: `.cg-docs/plans/2026-08-07-modular-compound-gpid.md`
- Active deviation policy: `ask` (plan stored; no runtime override)
- Review mode: `auto`
- Scope: all phases 1-5, steps 1-14

## Completed Steps And Phases

- 2026-08-07: Step 1, module-registry schema + validator + unit tests (18 tests).
- 2026-08-07: Step 2, full canonical asset inventory + classification (117 assets (84 CG + 33 CR); 0 unowned; 0 multi-owned) + ownership report mode.
- 2026-08-07: Step 3, namespace-agnostic generator discovery + adapter template + audit SKILL_REF_RE/brain-query paths + test updates (82 generator tests, ns tests).
- 2026-08-07: Step 4, dependency-closure + cross-suite reference checker + CI gate (V4/V9).
- 2026-08-07: Step 5, CG characterization manifest fixture + CR forward baseline from research branch (V5/V6).
- 2026-08-07: Step 6, CG/CR 5-platform parity with synthetic fixtures (V7).
- 2026-08-07: Phase 1 complete; Phase 2 complete. Checkpoint commit authorized.
- 2026-08-07: Step 7, main assets migrated to declared ownership — 0 ambiguous, drift green, characterization unchanged (V8).
- 2026-08-07: Step 8, CR content imported capability-by-capability (5 prompts, 11 agents, 15 skills, 2 instructions); model: stripped per authorization; registry gains suite-cr, cap-research-output, cap-language-research; cross-suite gate green (V9).
- 2026-08-07: Step 11, context-budget enforcement: cg_context_budget.py + generator --active-suites filter + instruction-level contract rule (V12, C5). CG-only generation = 1071 files (unchanged from pre-CR baseline).
- 2026-08-07: Step 12, cg_migrate_config.py idempotent config migration; compound-gpid.local.md now suites: [cg, cr] (V13).
- 2026-08-07: Step 9, mixed /cr-work path proof — dependency resolution through kernel + capability packs only (V10 artifact).
- 2026-08-07: Step 10, compatibility matrix documented (V11 artifact).
- 2026-08-07: Step 13, task-oriented modular guide published + cross-linked (V14).
- 2026-08-07: Step 14, charter updated after Phases 1-4 verified (approved).
- 2026-08-07: Phase 3, Phase 4, Phase 5 complete.
- 2026-08-07: review:auto architecture route dispatched (8 agents). Findings
  addressed: P1 cross-suite name-form coupling (review agents/roadmap/compound-docs
  moved to capability/kernel), capability-id suffix race, YAML comment handling,
  validator perf (cross-suite ~4.9s -> ~0.36s), schema missing-field checks,
  docs/config-table parity. Final gates: 551 Python tests passed; 2488 Pester
  tests passed (full run).

## Deviations

- Authorized checkpoint commits at Phase 1/2 and Phase 3/4 boundaries (drift gate needs regenerated platform trees in HEAD). Commits: `feat(registry)`, `test(drift)`, `feat(cr)`.
- Authorized: strip `model:` frontmatter from all imported CR prompts/agents/skills so the model-governance audit stays green.
- Authorized: align imported CR prompts from `modules: research` to `suites:` includes `cr` (Step 11/12 schema).
- Authorized: updated the protected charter compound-gpid.md (Step 14) after Phases 1-4 verified.
- Recorded: release-gate drift subprocess timeout bumped 360s -> 600s because the verified generated tree legitimately grew (1214 files with CR import; full drift run measured ~381s). This is test infrastructure, not an assertion change.

## Accepted Exceptions

- (none yet)

## Evidence

| ID | Status | Artifact |
|----|--------|----------|
| V1 | passed | `pytest scripts/tests/test_module_registry.py` — 22 passed |
| V2 | passed | `python scripts/cg_validate_modules.py --check-ownership` — exit 0, 117 assets owned |
| V3 | passed | `pytest scripts/tests/test_cg_generate_targets.py -k namespace` — 4 passed |
| V4 | passed | `python scripts/cg_validate_modules.py --check-dependencies` — exit 0 |
| V5 | passed | `pytest scripts/tests/test_cg_characterization.py` — 3 passed |
| V6 | passed | `pytest scripts/tests/test_cr_baseline.py` — 7 passed |
| V7 | passed | `pytest scripts/tests/test_target_drift.py` + release gate `test_drift_test_would_pass` — 336s pass after checkpoint commit |
| V8 | passed | main assets migrated to declared ownership; 0 ambiguous; drift + characterization green |
| V9 | passed | `python scripts/cg_validate_modules.py --check-cross-suite` — exit 0 after CR import |
| V10 | passed | `.cg-docs/work-reports/2026-08-07-mixed-cr-work-path-proof.md` |
| V11 | passed | `.cg-docs/compatibility-matrix.md` |
| V12 | passed | `pytest scripts/tests/test_context_budget.py` — 9 passed; generator CG-only excludes CR |
| V13 | passed | `pytest scripts/tests/test_config_migration.py` — 5 passed |
| V14 | passed | `docs/modular-guide.md` exists, covers 5 topics, cross-linked; `test_target_documentation.py` green |

## Constraints Check

| ID | Status | Result |
|----|--------|--------|
| C1 | passed | Full Pester suite via safe runner — 2488 passed, 0 failed (includes prompt-tools) |
| C2 | passed | registry validator: no `packages/` source tree (check_no_physical_relocation) |
| C3 | passed | `pytest scripts/tests/test_target_drift.py` — 16 passed (368s) |
| C4 | passed | `git diff --stat` confirmed selective CR import (no wholesale merge) |
| C5 | passed | context-budget: CG-only generation = 1071 files, unchanged from pre-CR |
| C6 | passed | instruction-level context-budget limitation documented in contract |
| C7 | passed | Full Pester suite — install.Tests.ps1 green |

## Remaining Uncertainty

- Real-repo context audit flags always-on instruction tokens > 6000 after the
  CR import (both suites' instructions are now canonical in this mixed repo).
  This is mitigated by generator-level suite filtering; instruction-level
  enforcement is a documented AI-compliance rule, not programmatically checked.
- Real-platform CLI smoke remains environment-dependent (deterministic isolated
  closure is the supported proof and passes).

## Final Status

`completed`