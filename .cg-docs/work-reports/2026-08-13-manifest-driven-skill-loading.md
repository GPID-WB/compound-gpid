---
date: 2026-08-13
title: "Work Report: Manifest-driven skill loading and project-local platform projections"
plan: ".cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md"
status: active
scope: "Deep"
---

# Work Report: Manifest-driven skill loading and project-local platform projections

## Run: 2026-08-13 (Phase 1)

- Plan reference: `.cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md`
- Active deviation policy: `ask` (plan stored; no runtime override)
- Review mode: `auto`
- Scope: Phase 1 requested; implementation completed after correcting an invalid preflight interpretation

## Preflight

- Project charter and local configuration were read; both suites are active and review depth is `thorough`.
- The selected plan contains seven phases and a valid `## Completion Contract`.
- `python scripts/render_artifact.py --validate-only .cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md` passed with exit code 0.
- Targeted Brain query completed; it returned relevant manifest/projection and token-baseline artifacts. Brain warnings about unknown generated subdirectories were non-blocking.
- Targeted roadmap fields were read. The plan-linked features are not currently linked to this plan; no roadmap mutation was attempted because execution did not reach a completion gate.
- The supported Kilo hosts are installed inside the editor extensions: VS Code Kilo CLI `7.4.22` (with prior `7.4.21`) and Positron Kilo CLI `7.4.20`; embedded `kilo.exe --version` commands returned successfully.
- The earlier PATH-only lookup was invalid evidence: the embedded Kilo binaries are not on PATH, and `cg-kilo` is a Phase 1, Step 2 deliverable, not a Phase 1 prerequisite.
- The proposed `KILO_DISABLE_EXTERNAL_SKILLS` control is verified by the embedded Kilo 7.4.20/7.4.21 `debug skill` inventory: local `.kilo/skills` remains present while Codex/Claude compatibility roots are absent under the child-process environment.
- A Kilo diagnostic command encountered a local credential-database error and emitted credential material in its local diagnostic output. No repository file was modified. Post-logout verification with the current VS Code Kilo `7.4.21` binary found the local `kilo` integration row present with `active=0`; no credential values were read or displayed. The local database also contains `openai`, `openrouter`, and `github-copilot` rows, all reporting `active=0`. This confirms local logout metadata only, not provider-side revocation.

## Completed Steps And Phases

- Phase 1, Step 1: characterized embedded Kilo discovery with local/Codex/Claude sentinels and recorded the supported-host fixture.
- Phase 1, Step 2: implemented `cg_kilo_preflight.py`, certified `cg-kilo` launchers, installer registration, link/update blocking gates, and regression coverage.
- Phase 1 completed on 2026-08-13 after the required Python, shell, preflight, and safe Pester checks passed.
- Auto-review completed. Applied fixes for Windows launcher exit propagation,
  Python-version fallback parity, duplicate POSIX preflight execution, typed
  host inventory handling, managed-marker validation, and the POSIX no-follow
  checksum-owned Kilo copy worker.
- Remaining review findings are recorded for later phases: staged publication
  before mutation (Phase 3 secure synchronizer), durable active-manifest launch
  state (Phase 2 manifest), and roadmap reconciliation through `@cg-roadmap`
  (Phase 5/7 contract work). They are not silently marked fixed in Phase 1.
- Review report: `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-review.md`.
- Review result: Phase 1 implementation checks passed, with P0/P1 findings
  intentionally left open for their owning later phases.
- P0/P1 triage batch: fixed bounded host output, executable SHA-256 evidence,
  typed POSIX early-gate exit propagation, and Claude/mixed-root coverage;
  deferred staged rollback, synchronizer parity/publication atomicity, update
  directory synchronization, Codex-side evidence, and roadmap attribution.
- P2/P3 triage batches: fixed deterministic explicit-host selection, bounded
  preservation warnings, command-reference coverage, and direct inventory JSON
  construction. Deferred module decomposition, compatibility-policy extraction,
  global permission policy, and durable evidence packaging.

## Deviations

- None.

## Accepted Exceptions

- None. The plan's `ask` policy still applies to any change from the proposed containment mechanism.

## Evidence

| ID | Status | Artifact / Result |
|----|--------|-------------------|
| V1 | passed | `scripts/tests/fixtures/kilo_coexistence_host.json`; `python -m pytest scripts/tests/test_kilo_coexistence.py` (12 passed); embedded Kilo 7.4.20/7.4.21/7.4.22 inventory proof; repository preflight exit 0. Negative ineffective-containment path returns typed exit 4. |
| V2 | passed | `bin/cg-kilo`, `bin/cg-kilo.cmd`, shared no-follow `cg_kilo_copy.py`, link/update integration; safe Pester `install` 90/90, `update` 138 passed/2 skipped, `bash-scripts` 1/1, `link` 79/79; caller environment preservation and child exit relay covered by Python tests. Codex-side preservation remains explicitly unavailable in the fixture. |
| V3 | pending | Phase 2 not reached. |
| V4 | pending | Phase 2 not reached. |
| V5 | pending | Phase 2 not reached. |
| V6 | pending | Phase 3 not reached. |
| V7 | pending | Phase 3 not reached. |
| V8 | pending | Phase 3 not reached. |
| V9 | pending | Phase 4 not reached. |
| V10 | pending | Phase 4 not reached. |
| V11 | pending | Phase 5 not reached. |
| V12 | pending | Phase 5 not reached. |
| V13 | pending | Phase 6 not reached. |
| V14 | pending | Phase 7 not reached. |
| V15 | pending | Phase 5 not reached; no `@cg-roadmap` reconciliation was attempted. |
| V16 | pending | Whole-plan completion not reached. |

## Constraints Check

| ID | Status | Result |
|----|--------|--------|
| C1 | passed | Kilo/Codex/Claude coexistence is supported only through `cg-kilo`; direct launches are explicitly unsupported and preflight verified contained inventory on Kilo 7.4.20/7.4.21. |
| C2 | pending | Later phases not reached. |
| C3 | pending | Later phases not reached. |
| C4 | pending | Later phases not reached. |
| C5 | pending | Later phases not reached. |
| C6 | pending | Later phases not reached. |
| C7 | pending | Later phases not reached. |
| C8 | pending | Later phases not reached. |
| C9 | pending | Later phases not reached. |

## Remaining Uncertainty

- The containment variable is a tested control for Kilo 7.4.20/7.4.21, not a permanent upstream Kilo contract.
- Kilo's upstream schema-validation behavior remains a separate diagnostic from local content and external-root discovery.
- Local Kilo logout is confirmed by non-secret metadata. Server-side Kilo session revocation cannot be independently confirmed from this machine.
- Phase 2 may begin; its own baseline and strict-manifest evidence gates remain pending.

## Final Status

`active`

Next: `/cg-work phase2 review:auto .cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md`
