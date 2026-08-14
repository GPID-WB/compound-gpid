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

---

## Run: 2026-08-14 (Phase 2)

- Plan reference: `.cg-docs/plans/2026-08-13-manifest-driven-skill-loading.md`
- Active deviation policy: `ask` (plan stored; no runtime override)
- Review mode: `auto`
- Scope: Phase 2 requested (`phase2`); steps 3, 4, 5 in scope.
- Preflight: plan artifact validation `cg-render-artifact --validate-only` passed (exit 0); Phase 1 V1/V2 evidence confirmed in the 2026-08-13 run (cg-kilo containment evidence present), satisfying Iteration Policy #2 before Phase 2.
- Brain: budgeted `cg-index query` (intent work) returned 3 artifacts; no actionable new constraints beyond plan-incorporated findings.
- Roadmap: no feature currently links to this plan; Step 1.5 roadmap dispatch not applicable (no matching `plan` path).

### Completed Steps And Phases
- Phase 2, Step 3: added `cg_projection_benchmark.py`, extended `cg_audit_context.py`
  (advertised-skill-metadata scan) and `cg_context_budget.py` (loadable ids,
  inventory digest); committed `.cg-docs/cost/skill-loading-baseline.json` and
  `.md` with four profile oracles all passing; host evidence marked available
  only when registry inventory was executed.
- Phase 2, Step 4: versioned the module registry to v2 with capability
  eligibility/activation records; pruned blanket language dependencies from
  suite declarations; added strict config grammar in `parsing_utils.py`
  (`parse_strict_config`) with line/field remediation; versioned
  `cg_migrate_config.py`; extended `cg_validate_modules.py` with v2 capability
  schema validation; capability-aware resolution with config selectors and
  additive explicit capabilities; closure checks use the full-config derived
  capability closure (per-project selection enforced by the manifest).
- Phase 2, Step 5: added `cg_project_manifest.py` resolving the committed
  active manifest with immutable selection fields, platform eligibility,
  compact catalog records, and desired-plan digest; separated mutable
  projection ownership state; added `.gitignore` rules and `docs/configuration.md`.
- Phase 2 completed on 2026-08-14 after the canonical V3/V4/V5 gates and the
  full-suite gate passed.

### Review Convergence (review:auto -> full, 2026-08-14)

The `review:auto` routing resolved to `full` (registry schema change = security-risk;
module boundary/dependency changes = architecture-risk; dedup to highest coverage).
Dispatched the full agent set: code-quality, testing, documentation, version-control,
reproducibility, performance, architecture, data-quality, learnings-researcher,
and adversarial. All findings were review-only (no protected artifacts touched).

Consolidated P1/P2 fixes applied and re-verified:
- Capability activation: `_capability_eligible` now resolves suite eligibility on
  user-facing names (empty-selector capabilities no longer dead code) and selector
  capabilities must be suite-eligible; owningModule validation (missing owner or
  undeclared module now fails loudly, no phantom ids).
- Benchmark: `validate_payload` blocks an `unavailable` oracle (R2/R14); the
  "no inactive skill body leak" oracle is a real assertion with a leak test;
  `collect_profile_baseline` catches registry/inventory failures and emits a
  blocking `unavailable` record end-to-end; profile-independent scans are hoisted
  (was O(profiles x full-scan)); unknown profile ids raise.
- Manifest: `source_revision` uses the deterministic `unknown-revision` sentinel;
  `canonical_platform_ids` rejects missing/empty `targets`; unknown suites/
  capabilities wrap into `ManifestResolutionError`; `validate_manifest` guards
  non-dict input and adds field-type checks; `_platform_eligibility` guards
  non-list `supportedPlatforms`; `ensure_managed_state` refuses to follow a
  symlinked/non-directory `.compound-gpid` and never overwrites existing files.
- Strict parser: line-anchored closing delimiter (no `---`-in-value truncation),
  lowercase-only list identifiers, quoted scalars exempt from the anchor/tag
  rejection, and migration rejects no-frontmatter/invalid-UTF-8 with clean errors.
- Validator: selector fields cross-checked against the config allowlist and the
  structural closure is computed per-module (suite-scoped) so cr-only research
  packs remain blocked for suite-cg.
- Docs: `claude` -> `claude-code`, review-depth values, migration wording, and
  complete manifest field list updated.

Re-verified after fixes: Phase 2 test batch 139 passed; full Python suite 935 passed /
20 skipped / 1 failed (the same pre-existing D4 active-state test); V4 gate 74 passed;
baseline regenerated with all four profiles passing; real-repo manifest validates.

Carried P3/advisory (documented, non-blocking): `KNOWN_CONFIG_FIELDS` is a frozen
allowlist decoupled from `docs/configuration.md` (single source migration is
future work); remediation line numbers assume `---` on physical line 1; the
audit `generated` stamp falls back to wall-clock only as an evidence marker.

### Verify Pass + Fix-Triage Closure (2026-08-14)

- `/cg-review mode:verify` found the prior review's fixed findings and forced a
  light pass (`@cg-code-quality` + `@cg-testing`) with a suppression policy.
  Result: 1xP1 + 4xP2 + 6xP3 new verification findings, zero P0; no cross-file
  breakage. Saved as
  `.cg-docs/reviews/2026-08-13-manifest-driven-skill-loading-verify-review-2.md`
  (the Phase 1 verify review with the same base name was preserved; the Phase 2
  verify pass uses the workflow's `-2` counter naming).
- `/cg-fix-triage` applied all 11 findings and marked them `fixed`:
  - P1.1: registry `supportedPlatforms` `claude` -> `claude-code` (all 12
    records) so `platformEligibility.allEligible` is true on the default manifest.
  - P2.1: `str.removeprefix("suite-")` -> 3.8-safe slicing in
    `cg_validate_modules._derived_capability_ids_for`.
  - P2.2: guarded config read (OSError/UnicodeDecodeError -> clean exit) in
    `cg_context_budget.main`.
  - P2.3: `resolve_active_manifest` rejects a non-supported `config-schema-version`.
  - P2.4: leak test now asserts presence-of-failure (not absence-of-success).
  - P3.1-P3.6: dead branch removed, shared comment-strip import, dropped unused
    `config` param, docstring alignment, `filtered_manifest` v2 contract note,
    and physical-line offset computation in the strict parser.
- Re-verified: Phase 2 test batch 139 passed; real-repo registry/manifest
  validate; baseline regenerated (all four profiles passed/available); canonical
  safe Pester full-suite gate 2520 passed / 0 failed (full run).

### Knowledge Capture (`/cg-compound`, 2026-08-14)

- Captured `.cg-docs/solutions/bugs/2026-08-14-capability-eligibility-namespace-mismatch.md`
  (category bugs, severity P1) — the dead suite-eligibility branch caused by
  comparing module ids against user-facing names, plus the canonical
  `claude-code` platform-id fix and the fail-closed validation discipline.
- Knowledge brain rebuilt via `cg-index --brain` (exit 0; 724 entities, 6 topics,
  310 edges).
- Wiki updated by `@cg-wiki`: `docs/reference.md` gained `cg-project-manifest` and
  `cg-projection-benchmark` rows; `docs/_wiki.yml` lastUpdated bumped. No manual
  ownership or conflict notifications.
- Cross-referenced with existing related solutions (back-links added).
- `compound-gpid.context.md` enriched with the strict-config/selection facts.

### Deviations
- None. The plan's `ask` policy did not require any documented deviation; the
  full-config derived capability closure in structural reference checks is a
  direct implementation of the plan's selector-derivation requirement.

### Accepted Exceptions
- None.

### Evidence
| ID | Status | Artifact / Result |
|----|--------|-------------------|
| V1 | passed | Phase 1 (carried). |
| V2 | passed | Phase 1 (carried). |
| V3 | passed | `.cg-docs/cost/skill-loading-baseline.json` + `.md`; `python -m pytest scripts/tests/test_projection_benchmark.py` (14 passed); all four profiles `passed`/`available`. |
| V4 | passed | `python -m pytest scripts/tests/test_module_registry.py scripts/tests/test_context_budget.py scripts/tests/test_config_migration.py` (71 passed) plus `test_strict_config.py` (24 passed). |
| V5 | passed | `python -m pytest scripts/tests/test_project_manifest.py` (18 passed); real-repo manifest resolves and validates. |
| V6 | pending | Phase 3 not reached. |
| V7 | pending | Phase 3 not reached. |
| V8 | pending | Phase 3 not reached. |
| V9 | pending | Phase 4 not reached. |
| V10 | pending | Phase 4 not reached. |
| V11 | pending | Phase 5 not reached. |
| V12 | pending | Phase 5 not reached. |
| V13 | pending | Phase 6 not reached. |
| V14 | pending | Phase 7 not reached. |
| V15 | pending | Phase 5 not reached. |
| V16 | pending | Whole-plan completion not reached. |

### Constraints Check
| ID | Status | Result |
|----|--------|--------|
| C1 | passed | Phase 1 (carried). |
| C2 | passed | `.github/` remains the complete canonical source; manifest resolution is side-effect-free and projection tests inspect distinct source/project roots. |
| C3 | passed | Only a genuinely absent `suites` field in a supported legacy schema defaults to `[cg]`; empty/scalar/duplicate/malformed values fail closed with exact lines (migration + strict-parser tests). |
| C4 | pending | Phase 3 not reached. |
| C5 | pending | Phase 3 not reached. |
| C6 | pending | Phase 4 not reached. |
| C7 | pending | Phase 5 not reached. |
| C8 | pending | Phase 6 not reached. |
| C9 | pending | Phase 7 not reached. |

### Full-Suite Gate (2026-08-14)
- Python: `python -m pytest scripts/tests` — 925 passed, 20 skipped, 1 failed.
- Pester (safe runner `. tests\Run-Tests.ps1`): 2520 passed, 0 failed, 2 skipped,
  full run (`filteredFiles` null), 2522 total.
- The single pytest failure is `test_issue_dispatch.py::TestActiveStateIntegrity::test_current_json_preserves_blocking_decisions`, which asserts an `unresolvedDecisions` entry `D4` in `.cg-docs/active-state/current.json`. The committed `current.json` at HEAD contains only `D1`/`D2` (Phase 1 handoff), so this failure pre-dates Phase 2 and is unrelated to Phase 2 files. Recorded as a deferred pre-existing item for `/cg-fix-triage`.

### Remaining Uncertainty
- Capability eligibility and config-selector derivation are documented in
  `docs/configuration.md`; the generator's no-`--active-suites` path remains
  byte-identical, while explicit config restriction is enforced through the
  active manifest and its staleness checks.
- Projection ownership/journal records are schema-validated but their
  publication lifecycle is implemented in Phase 3 (secure synchronizer).

### Final Status

`active` — Phase 2 complete; next `/cg-work phase3`.
