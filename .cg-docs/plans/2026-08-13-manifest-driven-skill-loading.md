---
date: 2026-08-13
title: "Manifest-driven skill loading and project-local platform projections"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-08-13-skill-loading-architecture-context-efficiency.md"
language: "Python/PowerShell/Bash/Markdown/JSON"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
execution-report: ".cg-docs/work-reports/2026-08-13-manifest-driven-skill-loading.md"
tags: [architecture, manifests, capabilities, platform-projections, kilo, context-efficiency, security, vendoring]
phases: 7
current-phase: 2
completed-phases: [1]
roadmap-features: [token-audit-context-model, context-budget-enforcement-design, shrink-always-on-context, prompt-skill-split, stage-context-contracts, token-benchmark-before-after, attribution-documentation, quarantined-external-skill-vendoring, github-actions-supply-chain-hardening-pilot]
---

# Plan: Manifest-Driven Skill Loading and Project-Local Platform Projections

## Objective

Replace all-skill, shared-install runtime exposure with a strict, committed
per-project manifest and an atomically published project-local projection for
each selected platform. The implementation must reduce routine skill metadata
exposure while fail-closing invalid selection, stale state, unsafe filesystem
conditions, and Kilo/Codex coexistence failures.

## Context

The completed modular architecture introduced the canonical `.github/` source,
the three-layer module registry, namespace-agnostic target generation, and
suite-only context filtering. It intentionally did not make a consumer
project's configuration an enforceable installation boundary. Consequently,
`suite-cg` and `suite-cr` still depend on every language capability; the
current config parser silently treats malformed `suites:` values as `[cg]`; and
`cg-link`/`cg-update` install full shared trees rather than a chosen profile.

Kilo's project-local `.kilo` files are already copied on Windows, but Kilo may
also auto-discover the Codex-compatible external `.agents/skills` root. Its
additive `skills.paths` setting cannot prevent this leakage. The Phase 0
release gate therefore blocks all later release gates until a supported process-scoped containment
path is proven to keep `.kilo/skills` available while excluding external
`.agents/skills` and `.claude/skills`.

The plan extends existing, data-driven mechanisms rather than creating
target-specific module implementations:

- `scripts/cg_context_budget.py` currently resolves suites and loadable module
  globs, but its parser defaults malformed values and its closure cannot select
  capabilities independently.
- `scripts/cg_generate_targets.py` already separates a rendered generation plan
  from publication and uses `scripts/secure_fs.py` for generated-tree writes.
- `scripts/link.ps1` has checksum-managed, project-local Kilo copies, but the
  POSIX linker deliberately has divergent overwrite semantics and neither
  linker applies a filtered project manifest.

### Brain Findings Incorporated

1. The module registry, generated ownership manifests, and five-platform drift
   tests are the canonical extensibility foundation. Extend their data model and
   characterization coverage instead of creating parallel target-specific
   generation. Source: `.cg-docs/plans/2026-08-07-modular-compound-gpid.md`.
2. Kilo rejects external linked Markdown sources; copied project-local runtime
   assets and checksum-gated stale deletion are required. A parser/schema defect
   must remain separately diagnosable from a source-path failure. Sources:
   `.cg-docs/solutions/bugs/2026-08-11-windows-link-kilo-copy-directory-parse-failure.md`
   and `.cg-docs/solutions/bugs/2026-08-06-kilo-agent-skill-parsing-failures.md`.
3. The older global-link installation model conflicts with a per-project,
   manifest-filtered projection. Treat it only as migration input, not as a
   pattern to preserve. Source:
   `.cg-docs/plans/2026-03-03-global-install-and-project-setup-v2.md`.

### Plan Review Revisions Incorporated

The 2026-08-13 `/cg-plan-review` requires a certified Kilo launch path rather
than an optional environment-variable probe; separates immutable manifest
selection from mutable projection ownership; persists selected platform ids;
uses durable per-root swaps and recovery instead of claiming impossible
project-wide atomicity; and restricts canonical vendoring to a verified
maintainer source checkout. It also specifies an executable profile oracle, a
restricted strict-config grammar, registered safe-runner Pester names, and the
required roadmap-contract reconciliation for `/cg-import-skill`.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Kilo plus Codex coexistence is a verified Phase 0 release gate available only through a supported contained Kilo launch path: Kilo sees selected local skills only, Codex retains `.agents/skills`, and an uncertified direct launch or failed verification blocks the combined configuration with exact remediation. | Brainstorm: Platform Projections |
| R2 | Preserve a reproducible before-state inventory, advertised-metadata, ordinary-session context, and task-success baseline for CG-only, CR-only, mixed, and representative capability profiles. | Brainstorm: Validation and Measurement |
| R3 | Version the registry and strict project-config schemas; distinguish mandatory dependencies, capability eligibility, and activation metadata under one restricted, deterministic configuration grammar. | Brainstorm: Configuration and Registry |
| R4 | Resolve configuration-derived and explicit additive capabilities plus canonical selected platform ids into one committed, stale-detecting `.compound-gpid/active-manifest.json`; malformed or unknown inputs fail closed while mutable projection drift is reconciled separately. | Brainstorm: Configuration and Registry |
| R5 | Materialize a manifest-filtered, project-local runtime projection for every selected platform without filtering or linking a global shared profile. | Brainstorm: Platform Projections |
| R6 | Use one cross-platform, root-anchored, no-follow synchronization implementation with staged validation, durable per-root atomic swaps, journaled recovery, checksum ownership, and safe stale deletion. | Brainstorm: Platform Projections |
| R7 | Make `cg-link` and `cg-update` resolve, publish, synchronize, and verify the projection automatically, while migrating legacy global links/copies without deleting user-owned content. | Brainstorm: Platform Projections; Migration |
| R8 | Generate an on-demand static `/cg-find-skill` catalog from manifest, registry, and skill frontmatter metadata only, with compact default results and complete filtered records on demand. | Brainstorm: Skill Discovery and Routing |
| R9 | Add a compact manifest-aware router that hard-stops explicitly requested inactive capabilities and gives the authoritative config change plus regeneration remedy. | Brainstorm: Skill Discovery and Routing |
| R10 | Implement `/cg-import-skill` as default-deny, immutable, quarantined vendoring with safe source acquisition, deterministic review evidence, two-stage approval, and canonical managed ownership only from a verified maintainer source checkout. | Brainstorm: Controlled External Vendoring |
| R11 | Keep managed and optional user roots distinct; reject normalized identifier/path collisions before writes and enable secondary roots only after discovery behavior is verified. | Brainstorm: Controlled External Vendoring |
| R12 | Provide idempotent migrations for strict config, active manifest, existing links/copies, and managed markers, retaining only the documented absent-`suites` legacy default during the compatibility window. | Brainstorm: Validation, Migration, and Measurement |
| R13 | Validate capability closure, manifests, projections, catalogs, routes, ownership inventories, platform parity, interrupted publication, and no inactive-reference leaks across all supported profile/platform combinations. | Brainstorm: Validation, Migration, and Measurement |
| R14 | Publish only measured context reduction and verified platform behavior; preserve stable `/cg-*` and `/cr-*` namespaces and link existing roadmap work rather than duplicating it. | Brainstorm: Outcomes and Boundaries |
| R15 | Reconcile the existing quarantined-vendoring roadmap command contract with the decided `/cg-import-skill` namespace through `@cg-roadmap` before vendoring implementation begins. | Plan review P2.4; Brainstorm: Outcomes and Boundaries |

## Implementation Steps

## Phase 1: Kilo Isolation (Phase 0 Release Gate)

### 1. Characterize external skill discovery and define the supported Kilo launch boundary

- **Requirements**: R1, R13
- **Files**: `scripts/tests/test_kilo_coexistence.py` (new),
  `tests/link.Tests.ps1`, `tests/bash-scripts.Tests.ps1`,
  `docs/installation.md` (update), `.github/shared/target-mapping.json` (update
  only if a platform-specific launch declaration is needed).
- **Details**: Build Windows-junction and POSIX-symlink sentinel fixtures that
  model a project containing local `.kilo/skills` plus external
  `.agents/skills` and `.claude/skills`. Establish a minimal reproducible Kilo
  launch test against the supported editor and CLI release. Test the
  process-scoped `KILO_DISABLE_EXTERNAL_SKILLS=1` control without mutating a
  user's global environment. Record the exact supported launch invocation,
  version evidence, local-skill discovery result, excluded-root result, and
  Codex discovery result in a machine-readable fixture. If Kilo does not honor
  the control, the health check must stop combined installation, name the
  incompatible Kilo version/control, and give remediation; it must not silently
  continue or describe an unverified control as supported. Keep a separate
  expected outcome for known upstream schema validation failures so that a
  source-path failure cannot be misclassified as a YAML defect.
- **Test Scenarios**: local Kilo skill remains discoverable; external Codex and
  Claude sentinel skills are absent from Kilo inventory; Codex sees its external
  sentinel; unset or ineffective containment produces a blocking diagnostic;
  malformed local skill is reported as content validation rather than external
  discovery.
- **Tests**: `python -m pytest scripts/tests/test_kilo_coexistence.py`; focused
  safe Pester runs through `tests/Run-Tests.ps1 -File link` and
  `tests/Run-Tests.ps1 -File bash-scripts`.
- **Acceptance criteria**: supported Kilo+Codex combinations have reproducible
  evidence for local-only Kilo discovery and preserved Codex discovery; every
  unsupported or unverifiable combination is blocked before projection publish.

### 2. Implement Kilo/Codex preflight and process-scoped launcher integration

- **Requirements**: R1, R7, R12
- **Files**: `scripts/cg_kilo_preflight.py` (new), `bin/cg-kilo` (new),
  `bin/cg-kilo.cmd` (new), `scripts/link.ps1`, `scripts/link.sh`,
  `scripts/update.ps1`, `scripts/update.sh`, `scripts/tests/test_kilo_coexistence.py`,
  `tests/install.Tests.ps1`, `tests/update.Tests.ps1`.
- **Details**: Encapsulate the verified Phase 0 check in a stdlib-only Python
  preflight that returns typed, actionable statuses rather than probing by
  error-message heuristics. Define `cg-kilo` as the only certified Kilo launch
  path for a project that also has Codex roots: it must set
  `KILO_DISABLE_EXTERNAL_SKILLS=1` for the Kilo process, preserve the inherited
  environment, avoid writing global Kilo configuration or permanent environment
  variables, and fail before launching if local projection validation or the
  containment capability is absent. `cg-link`/`cg-update` must record the
  certified launch requirement in the active manifest and refuse a combined
  Kilo+Codex success outcome unless the preflight and the `cg-kilo` host smoke
  test pass. Their final status must explicitly state that direct editor/CLI
  launches are unsupported for that combined configuration and show the
  certified command; they must not treat an optional launcher test as
  containment. A project without Codex roots may use its normal Kilo launch,
  but must re-run preflight before adding Codex. Use the established CMD
  Python-detection pattern for the Windows wrapper and test Windows/POSIX
  argument and exit-code parity.
- **Test Scenarios**: the certified `cg-kilo` launch discovers local skills and
  excludes external roots; direct Kilo launch is reported unsupported when Codex
  is present; unsupported version blocks without spawning Kilo; absent Codex
  root does not require coexistence mode; caller environment survives; wrapper
  relays failed preflight status; no global config/environment mutation occurs.
- **Tests**: `python -m pytest scripts/tests/test_kilo_coexistence.py`; focused
  safe Pester runs through `tests/Run-Tests.ps1 -File install` and
  `tests/Run-Tests.ps1 -File update`.
- **Acceptance criteria**: a Kilo+Codex project cannot claim a supported
  configuration until the certified launch path passes its scoped containment
  test; normal direct Kilo launches are explicitly unsupported and documented
  solely from executed supported-version evidence.

## Phase 2: Baseline, Strict Schemas, and Manifest Resolution

### 3. Preserve the pre-projection baseline and profile matrix

- **Requirements**: R2, R14
- **Files**: `scripts/cg_audit_context.py` (extend),
  `scripts/cg_context_budget.py` (extend), `scripts/cg_projection_benchmark.py`
  (new), `scripts/tests/test_projection_benchmark.py` (new),
  `.cg-docs/cost/skill-loading-baseline.json` (new generated evidence),
  `.cg-docs/cost/skill-loading-baseline.md` (new generated evidence).
- **Details**: Define deterministic profile fixtures for CG-only, CR-only,
  mixed, and capability-specific projects. For each fixture, commit a minimal
  requested command/capability, expected selected route, expected hard-stop or
  catalog result, expected emitted inventory digest, and a supported host
  procedure. Capture source inventory, generated inventory, advertised skill
  metadata, context-audit measures, and one executable routed-task assertion per
  profile before any selection change. Store raw measures, collection commands,
  source revision, platform versions, timestamps, and an explicit statement
  that token estimates are heuristic. Treat unavailable required host evidence
  as a blocking `unavailable` verification result, not a successful zero or an
  accepted baseline. Separate inventory/context reduction measurements from
  workflow success so smaller output cannot be reported as success if a selected
  workflow breaks. Extend existing audit tooling rather than creating a second
  unconnected token metric.
- **Test Scenarios**: same input produces byte-stable normalized metrics and
  task assertions; unavailable required host integration blocks baseline
  completion; an unselected capability changes inventory but not selected-task
  success; an incomplete profile record or unexpected route fails benchmark
  validation.
- **Tests**: `python -m pytest scripts/tests/test_audit_context.py
  scripts/tests/test_projection_benchmark.py`.
- **Acceptance criteria**: every target profile has a committed, reproducible,
  executable task oracle and comparable before/after fields; unavailable required
  host evidence blocks release evidence, and no unsupported token-saving claim
  is possible.

### 4. Version the registry and implement strict project-configuration parsing

- **Requirements**: R3, R4, R12, R13
- **Files**: `.github/shared/module-registry.json`,
  `scripts/cg_validate_modules.py`, `scripts/cg_context_budget.py`,
  `scripts/cg_migrate_config.py`, `scripts/parsing_utils.py`,
  `scripts/tests/test_module_registry.py`, `scripts/tests/test_context_budget.py`,
  `scripts/tests/test_config_migration.py`.
- **Details**: Introduce a versioned registry schema that retains structural
  `dependsOn` only for mandatory lower-layer runtime prerequisites and adds
  separate capability eligibility/activation records. Each capability record
  must declare stable id, owning module, supported suites/platforms, source
  provenance, expected activation cost, task triggers, and allowed configuration
  selectors. Remove blanket language/research/Pester/Brain/Git dependencies
  from suite declarations; suites select workflow namespaces, while documented
  configuration selectors derive baseline capabilities. Replace the permissive
  frontmatter scan with a strict parser for `compound-gpid.local.md` that accepts
  only UTF-8 without BOM, a top-level delimited frontmatter block, ASCII
  identifier keys, quoted/simple scalar values, and inline lists of quoted or
  ASCII identifier values. Reject duplicate keys, anchors, aliases, tags, block
  scalars, nested mappings/sequences, tabs, non-ASCII control characters, and
  any unrecognized key with line/field remediation. Use this parser, not
  `brain.utils.parse_frontmatter`, for resolver and migration inputs. Only a
  genuinely absent `suites` field in a supported legacy schema defaults to
  `[cg]`; empty, scalar, duplicate, malformed, and unknown values fail. Validate
  `capabilities:` as additive, unique, known ids and reject any attempt to use
  it to subtract a settings-derived capability. Version migration input and
  output so compatibility expiry can turn into an explicit migration error
  rather than an implicit fallback.
- **Test Scenarios**: CG-only, CR-only, and mixed suites resolve namespace
  closure only; language/r-syntax/tooling selectors derive expected packs;
  explicit capability augments but cannot remove derived capability; absent
  legacy suite defaults once; each malformed present form fails; duplicate keys,
  anchors, tags, block scalars, nested values, invalid UTF-8, and tabs fail with
  exact lines; duplicate and unknown capabilities fail; registry dependency
  cycle and eligibility metadata mismatch fail.
- **Tests**: `python -m pytest scripts/tests/test_module_registry.py
  scripts/tests/test_context_budget.py scripts/tests/test_config_migration.py`;
  `python scripts/cg_validate_modules.py --check-dependencies`.
- **Acceptance criteria**: a valid config deterministically produces selected
  suites plus mandatory closure and selected capabilities; every invalid named
  input fails before any generation or projection write.

### 5. Resolve and validate the committed active project manifest

- **Requirements**: R3, R4, R12, R13
- **Files**: `scripts/cg_project_manifest.py` (new),
  `scripts/cg_context_budget.py`, `scripts/cg_validate_modules.py`,
  `scripts/tests/test_project_manifest.py` (new), `.gitignore`,
  `docs/configuration.md` (new or update), `.compound-gpid/active-manifest.json`
  (generated project artifact schema/documented example only),
  `.compound-gpid/projection-ownership.json` (generated mutable ownership state),
  `.compound-gpid/projection-transaction.json` (generated transaction journal).
- **Details**: Implement a side-effect-free resolver that consumes strict
  project configuration plus the versioned registry and produces one canonical
  `active-manifest.json`. Include config/registry hashes and schema versions,
  source revision, selected suites, derived and explicit capabilities, resolved
  module closure, selected platform ids in canonical order, platform eligibility,
  certified Kilo launch requirement, catalog records, and the desired projection
  plan digest. Define the CLI policy: `cg-link --platforms` selects the initial
  platform set; a later `cg-link --platforms` is an explicit replacement after
  confirmation; `cg-update` uses only the persisted selected platform ids and
  never defaults to all platforms. Define canonical JSON ordering and hashing so
  independent runs are comparable. Separate immutable selection validity from
  mutable projection ownership: reject the active manifest only if config hash,
  registry hash/schema, source revision, selected closure, selected platform
  ids, or desired-plan digest differs. Store per-file expected/current ownership
  checksums, preservation state, and stale-deletion authorization only in
  `projection-ownership.json`; a user-modified projected file is a reconciliation
  outcome, not active-manifest staleness. Use the transaction journal solely to
  recover interrupted publication. Change ignore rules so active manifest is a
  generated, reviewable team artifact while mutable ownership, staging,
  quarantine, and transient recovery files remain ignored. Migration must
  create/update these records idempotently without overwriting user-owned
  `.compound-gpid` content.
- **Test Scenarios**: same source/config/platform selection produces identical
  active-manifest bytes; changed config, registry, source revision, closure,
  platform set, or desired plan causes stale rejection; user-modified projected
  file leaves the active manifest valid and enters preservation state; invalid
  manifest/ownership/journal shape fails with the correct recovery path; project
  marker collision preserves user file; migration rerun is a no-op; only managed
  records are updated.
- **Tests**: `python -m pytest scripts/tests/test_project_manifest.py
  scripts/tests/test_context_budget.py`; `python scripts/cg_project_manifest.py
  --root <fixture> --validate`.
- **Acceptance criteria**: the active manifest is the single validated immutable
  selection input for downstream projection, catalog, routing, and selected
  platform scope; no stale selection can publish runtime files, while modified
  projected files reach checksum-governed reconciliation without invalidating
  selection state.

## Phase 3: Secure Materialized Projection

### 6. Refactor target generation into canonical rendering and project projection plans

- **Requirements**: R4, R5, R13
- **Files**: `scripts/cg_generate_targets.py`,
  `scripts/cg_project_projection.py` (new), `scripts/cg_context_budget.py`,
  `.github/shared/target-mapping.json`, `scripts/tests/test_cg_generate_targets.py`,
  `scripts/tests/test_target_closure.py`, `scripts/tests/test_target_determinism.py`,
  `scripts/tests/test_project_projection.py` (new).
- **Details**: Preserve the existing canonical `.github/` renderer while adding
  an explicit source-root/project-output-root projection plan. The plan must
  read only the validated active manifest, render all selected platform assets
  (commands, skills, agents, instructions, shared files, root adapters, and
  configs) from canonical source, and enumerate exact destination paths and
  SHA-256 hashes before any write. Do not derive selection from raw config at
  publish time, regenerate a filtered profile inside the global install, or
  introduce a shared profile cache. Selected platform ids must come exclusively
  from the active manifest's canonical ordered set, with target mapping used only
  to validate eligibility and output layout. Update target mapping with declared managed
  and optional user roots, and validate every root/path as a portable, normalized
  descendant. Generate namespace-specific adapters/configuration from selected
  command and capability records, never wildcard all-skill prose. Retain
  byte-identical full-source generation when the manifest selects all assets.
- **Test Scenarios**: CG-only, CR-only, mixed, and capability-specific manifests
  render distinct inventories for their persisted platform ids; a Kilo-only
  manifest cannot emit another target; full profile preserves current target output;
  every output exists under the selected project root; inactive command, skill,
  agent, instruction, shared reference, adapter, and config paths are absent;
  unknown platform/capability and output collision fail during planning.
- **Tests**: `python -m pytest scripts/tests/test_cg_generate_targets.py
  scripts/tests/test_target_closure.py scripts/tests/test_target_determinism.py
  scripts/tests/test_project_projection.py`.
- **Acceptance criteria**: rendering has a pure, deterministic plan/apply
  boundary, and manifests precisely determine every projected platform file.

### 7. Implement one root-anchored cross-platform projection synchronizer

- **Requirements**: R5, R6, R7, R11, R13
- **Files**: `scripts/cg_project_projection.py`, `scripts/secure_fs.py`,
  `scripts/tests/test_project_projection.py`, `scripts/tests/test_secure_fs.py`,
  `tests/link.Tests.ps1`, `tests/unlink.Tests.ps1`, `tests/parity.Tests.ps1`.
- **Details**: Move filtered runtime synchronization out of divergent PowerShell
  and shell directory-copy paths into a single stdlib Python worker backed by
  `secure_fs`. Resolve and validate all source and destination identities first;
  stage the complete projection in a project-local safe sibling; validate the
  staged inventory, frontmatter, UTF-8, ownership marker, manifest output hashes,
  and root adapters; then publish through a durable transaction rather than
  claiming unsupported whole-project atomicity. Define the transaction boundary
  as every selected platform root plus `.compound-gpid/projection-ownership.json`:
  write an fsynced journal with transaction id, old/new root identities, planned
  hashes, and state; atomically rename each staged root into a same-volume
  versioned project-local generation directory; atomically switch one small
  project-local active-root pointer/adapter per platform; commit the ownership
  state only after every pointer is switched; then remove verified old
  generations. On startup/link/update, recovery reads the journal and either
  completes the remaining pointer switches when every staged root validates or
  rolls all switched pointers back to the prior generation. No command may claim
  success until the journal is committed or recovery finishes. Use root-anchored
  no-follow operations for creates, swaps, markers, stale deletion, and rollback.
  Delete stale assets only when current bytes match the ownership-state checksum;
  preserve modified assets in the old generation or user root and record a
  reconciliation warning. Reject symlinks/junctions/reparse points, hard links,
  portable path collisions, and unsafe marker paths before mutation. Replace the
  documented Windows/POSIX semantic divergence with the same preservation and
  ownership contract on both hosts.
- **Test Scenarios**: normal first publish; modified managed file is preserved;
  unchanged stale managed file is removed; stale modified file is preserved;
  source/destination symlink or reparse swap is rejected; hard link is rejected;
  crash before the first pointer switch, between platform pointer switches, and
  after the last switch but before journal commit each recover to a coherent old
  or new generation; collision with a user root is rejected; Windows/POSIX
  fixtures produce identical inventory and preservation decisions.
- **Tests**: `python -m pytest scripts/tests/test_project_projection.py
  scripts/tests/test_secure_fs.py scripts/tests/test_target_path_safety.py`;
  focused safe Pester runs through `tests/Run-Tests.ps1 -File link`,
  `tests/Run-Tests.ps1 -File unlink`, and
  `tests/Run-Tests.ps1 -File parity`.
- **Acceptance criteria**: no project projection mutation follows an external
  link or destroys unverified user content; after a crash, recovery leaves every
  selected platform on one validated old or new generation, with no mixed active
  root set or uncommitted success claim.

### 8. Integrate projection, migration, and health verification into link/update flows

- **Requirements**: R1, R5, R6, R7, R12, R13
- **Files**: `scripts/link.ps1`, `scripts/link.sh`, `scripts/update.ps1`,
  `scripts/update.sh`, `scripts/unlink.ps1`, `scripts/unlink.sh`,
  `scripts/cg_migrate_config.py`, `scripts/cg_project_projection.py`,
  `tests/link.Tests.ps1`, `tests/update.Tests.ps1`, `tests/unlink.Tests.ps1`,
  `tests/bash-scripts.Tests.ps1`, `tests/parity.Tests.ps1`,
  `scripts/tests/test_update_generates_targets.py`.
- **Details**: Make `cg-link` and `cg-update` invoke strict config migration,
  manifest resolution, journal recovery, staged projection, Kilo coexistence
  preflight, certified Kilo-launch validation where required, and post-publish
  ownership verification in that order. `cg-link --platforms` creates or, after
  explicit confirmation, replaces the active manifest's selected platform set;
  `cg-update` uses that stored set only and never defaults to all targets. On
  update, validate immutable selection fields before using them, reconcile
  mutable projection ownership separately, and regenerate only through the
  source revision that was validated. Safely migrate legacy global links, copied Kilo
  directories, managed-copy markers, and ignored-state assumptions to the new
  project-local layout; remove a link/reparse point only after ownership
  verification and never traverse it. Make unlink remove only checksum-owned
  projection files and leave user files/roots intact. Keep user-visible
  platform-selection flags, preserve exact nonzero child exits, and retire
  obsolete global markdown permission workarounds only when project-local
  containment evidence proves they are unnecessary.
- **Test Scenarios**: fresh link, legacy linked project, partially migrated
  project, stale manifest update, invalid config update, interrupted update,
  Kilo+Codex preflight failure, user-owned root collision, unlink after user
  edits, and repeat link/update/unlink cycles all have deterministic outcomes.
- **Tests**: `python -m pytest scripts/tests/test_update_generates_targets.py
  scripts/tests/test_project_manifest.py scripts/tests/test_project_projection.py`;
  focused safe Pester runs through `tests/Run-Tests.ps1 -File link`,
  `tests/Run-Tests.ps1 -File update`, `tests/Run-Tests.ps1 -File unlink`, and
  `tests/Run-Tests.ps1 -File parity`.
- **Acceptance criteria**: normal link/update requires no separate resolution
  command, all failures occur before unsafe publish, and migration/unlink never
  remove user-owned bytes.

## Phase 4: Catalog, Routing, and Projection Observability

### 9. Generate and expose a static manifest-backed skill catalog

- **Requirements**: R4, R8, R13, R14
- **Files**: `scripts/cg_skill_catalog.py` (new),
  `.github/prompts/cg-find-skill.prompt.md` (new),
  `.kilo/commands/cg-find-skill.md` (generated), `bin/cg-find-skill` (new),
  `bin/cg-find-skill.cmd` (new), `scripts/tests/test_skill_catalog.py` (new),
  `tests/prompt-tools.Tests.ps1`, `tests/install.Tests.ps1`,
  `docs/reference.md`, `docs/skills/index.md`.
- **Details**: Generate catalog rows exclusively from the active manifest,
  registry activation metadata, and parsed skill frontmatter. Never load full
  skill bodies merely to build or query the catalog. Support compact default
  output containing id, purpose, capability, current availability, and
  activation cost. Add `--full` and composable filters for id/query,
  capability, suite, platform, availability, cost, owner, and provenance. Full
  rows must include source path, source/content provenance, eligibility, inactive
  reason, and import status. The command must hard-fail on stale/invalid manifest
  rather than querying global all-skill source. Add static tests proving compact
  output cannot spill full records or all catalog entries into ordinary command
  text.
- **Test Scenarios**: compact query finds active and inactive records; each
  filter constrains results; `--full` adds only requested metadata; stale
  manifest blocks query; generated catalog excludes inactive skill body content;
  output is deterministic across runs.
- **Tests**: `python -m pytest scripts/tests/test_skill_catalog.py` and focused
  safe Pester runs through `tests/Run-Tests.ps1 -File prompt-tools`
  and `tests/Run-Tests.ps1 -File install`.
- **Acceptance criteria**: users can discover activation requirements on demand
  without ordinary sessions receiving the full catalog or any inactive skill
  body.

### 10. Add manifest-aware hard-stop routing and inventory leak checks

- **Requirements**: R8, R9, R13, R14
- **Files**: `.github/shared/context-loading.contract.md`,
  `.github/shared/module-registry.json`, `.github/prompts/cg-*.prompt.md`
  (targeted router call points), `scripts/cg_skill_catalog.py`,
  `scripts/cg_validate_modules.py`, `scripts/tests/test_skill_catalog.py`,
  `scripts/tests/test_target_closure.py`, `scripts/tests/test_context_budget.py`,
  `tests/prompt-tools.Tests.ps1`.
- **Details**: Define one compact router interface that a command invokes only
  when an explicitly requested capability is absent. It must identify the
  missing capability, authoritative selector/configuration field, current
  inactive reason, and exact `cg-link` or `cg-update` regeneration action; then
  stop before work. It must not silently fall back to all-skill global source,
  write a transient session projection, alter configuration, or imply that
  instructions alone enforce selection. Extend closure and generated-target
  tests to inspect all emitted commands, agents, skills, instructions, shared
  assets, root adapters, configs, and catalog rows for inactive asset paths or
  references. Preserve stable `/cg-*` and `/cr-*` workflow namespaces; only add
  the action-first discovery namespace `/cg-find-skill`.
- **Test Scenarios**: active requested capability proceeds; inactive explicit
  request stops with correct config/rebuild remedy; unknown id stops distinctly;
  inactive reference in adapter/config/catalog fails validation; suite-only
  project does not gain language pack by routing; router cannot alter manifest.
- **Tests**: `python -m pytest scripts/tests/test_skill_catalog.py
  scripts/tests/test_target_closure.py scripts/tests/test_context_budget.py`;
  focused safe Pester run through `tests/Run-Tests.ps1 -File prompt-tools`.
- **Acceptance criteria**: every inactive-reference leak is a test failure, and
  missing capabilities produce actionable hard stops rather than degraded work.

## Phase 5: Controlled External Skill Vendoring

### 11. Reconcile vendoring roadmap contract and build quarantined intake modes

- **Requirements**: R10, R11, R13, R15
- **Files**: `scripts/cg_import_skill.py` (new),
  `scripts/cg_vendor_policy.py` (new), `.github/shared/vendor-policy.json`
  (new), `.github/prompts/cg-import-skill.prompt.md` (new),
  `scripts/tests/test_import_skill.py` (new), `tests/prompt-tools.Tests.ps1`,
  `docs/skills/importing.md` (new).
- **Details**: Before implementation, dispatch `@cg-roadmap` to update the
  existing `quarantined-external-skill-vendoring` feature description from the
  superseded `/cg-skill-import` spelling to the brainstorm-decided
  `/cg-import-skill` contract, and add this existing feature to the plan link;
  do not create a duplicate feature. Implement two explicit importer modes.
  `review` mode, available from a consumer project, accepts exactly
  `/cg-import-skill <repo>@<full-sha> <path>` from an allowlisted HTTPS
  repository identity and may create quarantined review evidence only under that
  consumer's non-runtime state. `vendor` mode is rejected unless its working
  directory is a verified Compound GPID canonical source checkout on an approved
  feature branch with an expected origin and clean/policy-allowed state; consumer
  projections and disposable global installs cannot receive canonical writes.
  Both modes require a full immutable SHA,
  normalized approved upstream skill-root descendant, no redirects, no shell
  interpolation, no interactive credentials, disabled hooks/submodules/LFS
  smudging, and a network-free runtime result. Acquire into a non-runtime
  quarantined directory with bounded resource limits. Reject links/reparse
  points, hard links, executables and scripts regardless of mode/extension,
  binary/archive/LFS content, hidden files, unsafe or Unicode-confusable paths,
  oversized bundles, secrets, remote-fetch/network-execution instructions,
  invalid frontmatter, broken relative references, unsupported licenses, and
  managed/user identifier collisions. Implement deterministic scanner reports
  that redact detected secret values.
- **Test Scenarios**: valid pinned Markdown-only fixture reaches consumer
  quarantine; consumer `vendor` mode and non-source checkout each fail before
  canonical mutation; source checkout on an unapproved branch fails; valid
  maintainer source checkout may proceed only to quarantine pending approval;
  short SHA, non-HTTPS URL, redirect, unapproved repo/root, traversal path,
  symlink, executable, archive, binary, LFS pointer, secret, unsafe Markdown
  instruction, license failure, and oversized bundle each fail before runtime
  mutation.
- **Tests**: `python -m pytest scripts/tests/test_import_skill.py`; focused safe
  Pester run through `tests/Run-Tests.ps1 -File prompt-tools`.
- **Acceptance criteria**: no external byte reaches a runtime or canonical
  managed root unless all default-deny admission checks pass in quarantine.

### 12. Add deterministic review, approval, and canonical vendor registration

- **Requirements**: R4, R10, R11, R12, R13
- **Files**: `scripts/cg_import_skill.py`, `scripts/cg_vendor_policy.py`,
  `.github/shared/module-registry.json`, `.github/shared/vendor-policy.json`,
  `scripts/tests/test_import_skill.py`, `scripts/tests/test_module_registry.py`,
  `docs/skills/importing.md`, `docs/reference.md`.
- **Details**: Generate a deterministic full-file, secret-redacted review diff
  and provenance record for a quarantined candidate. Require local maintainer
  approval of that exact diff before mechanical namespace/path rewrites and a
  normal pull-request review after the vendor commit; semantic rewrites always
  require maintainer changes. Only `vendor` mode in the verified canonical source
  checkout may, after approval, copy a non-executable bundle into managed
  `.github/skills/`, register source repository/full SHA, upstream path, license
  evidence, local approval reference, local adaptation record, owner, capability
  eligibility, and import status, and leave the resulting change for normal git
  commit/PR review. It must never commit, push, or modify a consumer projection
  itself. A consumer review artifact can be transferred to the maintainer mode
  only when its candidate digest, source SHA, and policy digest match exactly.
  Re-resolve the active manifest and require a normal projection publish for
  availability. Rejected imports must leave user roots, canonical roots,
  manifests, and runtime projections unchanged.
- **Test Scenarios**: deterministic review report repeatability; approval bound
  to changed bytes expires on modification; mechanical rewrite is recorded;
  semantic change requires explicit maintainer marker; registration becomes
  discoverable only after manifest refresh; rejected candidate leaves no managed
  collision or stale catalog record.
- **Tests**: `python -m pytest scripts/tests/test_import_skill.py
  scripts/tests/test_module_registry.py scripts/tests/test_skill_catalog.py`.
- **Acceptance criteria**: approved imports have verifiable provenance and
  review evidence, while unapproved/rejected imports cannot affect source,
  projection, or user content.

## Phase 6: Migration and Full Regression Matrix

### 13. Complete migration compatibility and managed/user-root safety coverage

- **Requirements**: R1, R6, R7, R11, R12, R13
- **Files**: `scripts/cg_migrate_config.py`, `scripts/cg_project_manifest.py`,
  `scripts/cg_project_projection.py`, `scripts/cg_import_skill.py`,
  `scripts/tests/test_config_migration.py`, `scripts/tests/test_project_manifest.py`,
  `scripts/tests/test_project_projection.py`, `scripts/tests/test_import_skill.py`,
  `tests/link.Tests.ps1`, `tests/unlink.Tests.ps1`, `tests/parity.Tests.ps1`.
- **Details**: Add an explicit compatibility matrix fixture for suite-only,
  CR-only, mixed, capability-specific, legacy absent-suite, malformed config,
  stale-manifest, legacy global-link/copy, user-root collision, Kilo+Codex, and
  interrupted-publication cases. Test all normalizations used for identifiers
  and paths: exact, case-folded, Unicode-normalized, reserved device names,
  trailing dots/spaces, and file/directory prefix conflicts. Verify idempotent
  migration from the defined legacy state and failure after its configured
  compatibility window. Preserve user bytes on every rejected import, migration,
  update, stale deletion, and unlink path.
- **Test Scenarios**: every matrix row asserts selected inventory and expected
  failure/remediation; duplicate normalized identifier is rejected before write;
  legacy migration is repeatable; expired legacy config fails; interrupted
  publish retains last valid manifest/projection; user files survive all failed
  mutations.
- **Tests**: `python -m pytest scripts/tests/test_config_migration.py
  scripts/tests/test_project_manifest.py scripts/tests/test_project_projection.py
  scripts/tests/test_import_skill.py scripts/tests/test_kilo_coexistence.py`;
  focused safe Pester runs through `tests/Run-Tests.ps1 -File link`,
  `tests/Run-Tests.ps1 -File unlink`, and
  `tests/Run-Tests.ps1 -File parity`.
- **Acceptance criteria**: the documented migration matrix has executable
  coverage and every mutation path preserves user-owned content and the last
  valid runtime projection.

### 14. Run end-to-end projection, platform, and release-gate regression tests

- **Requirements**: R1, R5, R6, R7, R8, R9, R10, R11, R13
- **Files**: `.github/workflows/tests.yml`, `scripts/tests/test_target_drift.py`,
  `scripts/tests/test_release_gate_targets.py`, `scripts/tests/test_target_ownership.py`,
  `scripts/tests/test_target_kilo.py`, `scripts/tests/test_target_claude.py`,
  `scripts/tests/test_target_codex.py`, `scripts/tests/test_target_opencode.py`,
  `scripts/tests/test_target_packaging.py`, `tests/Run-Tests.ps1` (reference
  only), `tests/last-run.json` (generated evidence).
- **Details**: Make the profile/platform matrix a CI release gate. Test the
  selected runtime inventory and ownership hashes for every platform persisted
  in each profile's active manifest, along with the full canonical all-assets
  release build. Include Windows and POSIX runners where filesystem semantics differ.
  Require manifest validation, no inactive-reference leaks, generator/project
  projection determinism, Kilo containment evidence, catalog/router checks,
  vendor quarantine checks, and source-to-projection ownership verification
  before target drift and release publication gates can pass. Keep Pester
  execution through the repository safe runner and use `tests/last-run.json` as
  evidence rather than parsing Pester output in pipelines.
- **Test Scenarios**: one platform/profile omission fails CI; inventory hash
  drift fails; inactive adapter reference fails; Kilo gate evidence missing
  fails; a Pester partial run cannot satisfy release evidence; all selected
  profiles pass on both filesystem families.
- **Tests**: targeted Python regression suite for the listed test modules;
  canonical safe Pester runner `. tests\Run-Tests.ps1`, with results read from
  `tests/last-run.json`; `git diff --check`.
- **Acceptance criteria**: CI blocks any manifest, containment, projection,
  ownership, catalog, routing, or platform-parity regression and retains clear
  failure artifacts.

## Phase 7: Measurement, Documentation, and Roadmap Closure

### 15. Measure before/after outcomes and document only verified operation

- **Requirements**: R2, R8, R9, R13, R14
- **Files**: `scripts/cg_projection_benchmark.py`,
  `scripts/tests/test_projection_benchmark.py`, `.cg-docs/cost/` benchmark
  artifacts, `docs/configuration.md`, `docs/installation.md`,
  `docs/modular-guide.md`, `docs/skills/index.md`, `docs/skills/importing.md`,
  `docs/reference.md`, `.cg-docs/compatibility-matrix.md`.
- **Details**: Re-run the Phase 1 benchmark against the unchanged profile
  definitions. Publish normalized before/after active inventory, advertised
  metadata, ordinary-session context, activation cost, and representative task
  success results. Flag regressions by profile rather than averaging them away.
  Document strict config/capability selection, manifest freshness recovery,
  project-local projection lifecycle, managed/user-root behavior, Kilo launch
  containment, catalog querying, inactive-capability hard stops, and vendor
  review/approval. State platform behavior only when supported by executed
  evidence; document upstream Kilo compatibility-root allow/deny request and
  its current status without treating it as an implemented contract.
- **Test Scenarios**: benchmark compares equivalent profile inputs; a context
  reduction with a failed task is reported as failure; stale manifest recovery
  guidance is executable; documentation links reach all new commands and
  recovery instructions; unsupported platform claim is rejected by doc fixture.
- **Tests**: `python -m pytest scripts/tests/test_projection_benchmark.py
  scripts/tests/test_target_documentation.py`; benchmark command against the
  committed profile fixtures; `git diff --check`.
- **Acceptance criteria**: release evidence demonstrates a documented reduction
  in active inventory and routine context exposure without selected-workflow
  regressions, and documentation makes every failure/recovery route explicit.

### 16. Link verified outcomes to existing roadmap work without duplicating features

- **Requirements**: R2, R13, R14, R15
- **Files**: `roadmap.json` (read-only verification), `.cg-docs/cost/` closure
  evidence, `.cg-docs/work-reports/` execution evidence.
- **Details**: Confirm the Step 11 `@cg-roadmap` reconciliation changed the
  existing `quarantined-external-skill-vendoring` feature from `/cg-skill-import`
  to `/cg-import-skill`, linked this plan, and retained its prerequisite on
  `attribution-documentation`; do not create a duplicate feature. After all
  required evidence succeeds, assemble traceable closure evidence for the
  existing context-budget, prompt-skill split, stage-context, token benchmark,
  attribution, quarantined-vendoring, and supply-chain hardening roadmap features
  listed in this plan's frontmatter. Do not edit `roadmap.json` directly. Use
  `@cg-roadmap` to attach the current plan and evidence to matching existing
  features, update status only where evidence satisfies its feature contract,
  and leave incomplete features active with explicit residual work. Verify the
  resulting targeted fields after the roadmap dispatch.
- **Test Scenarios**: every linked feature has evidence path; the vendoring
  feature has the reconciled command contract and remains blocked by incomplete
  attribution evidence; incomplete vendor pilot cannot be marked done; no new
  duplicate feature is created; direct JSON modification is rejected by workflow
  discipline.
- **Tests**: targeted post-dispatch `roadmap.json` feature read and execution
  report evidence audit.
- **Acceptance criteria**: existing roadmap items receive only verified evidence
  links/statuses, with no duplicate roadmap feature and no direct roadmap edit.

## Testing Strategy

- Use stdlib-only Python unit and integration fixtures for manifest parsing,
  registry validation, projection rendering/publication, catalog/router behavior,
  vendor quarantine, and deterministic metrics.
- Use Windows and POSIX filesystem fixtures for no-follow behavior, hard-link and
  reparse/symlink rejection, journaled per-root interruption recovery, output
  ownership, and parity.
- Preserve and extend target characterization, ownership, closure, drift, and
  release-gate tests rather than replacing their coverage.
- Run Pester only through `. tests\Run-Tests.ps1` or its single-file `-File`
  form, then consume `tests/last-run.json`; do not invoke Pester through unsafe
  directory or pipeline patterns.
- Treat real Kilo host discovery as an integration gate with versioned evidence;
  synthetic sentinels test the contract but cannot replace supported-host proof.
  A Kilo+Codex project passes only through `cg-kilo`; unavailable host proof is
  blocking evidence.

## Documentation Checklist

- [ ] Document strict `compound-gpid.local.md` schema, capability derivation,
  restricted grammar, migration window, selected-platform replacement policy,
  and stale-manifest recovery.
- [ ] Document project-local projection, managed/user roots, preservation, and
  link/update/unlink lifecycle.
- [ ] Document verified Kilo process-scoped containment and unsupported-version
  remediation, separately from upstream parser defects.
- [ ] Add `/cg-find-skill` and `/cg-import-skill` to command references and
  skill documentation, and record the approved roadmap migration from the
  superseded `/cg-skill-import` spelling.
- [ ] Document catalog filters, inactive-capability hard-stop diagnostics, and
  activation costs without advertising inactive skill bodies.
- [ ] Document vendor allowlisting, consumer review versus maintainer vendor
  mode, source-checkout/branch guard, quarantine, approval, provenance,
  licensing, semantic adaptation, and PR-review requirements.
- [ ] Update the compatibility matrix and token/context benchmark evidence.

## Risks & Mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|------------|--------|------------|
| RK1 | `KILO_DISABLE_EXTERNAL_SKILLS` is unavailable or not propagated by the certified Kilo launch path. | Medium | Blocking | Phase 0 requires versioned `cg-kilo` host evidence and blocks combined installation; direct Kilo launches are explicitly unsupported. |
| RK2 | A strict config parser breaks legacy projects. | Medium | High | Accept only a genuinely absent legacy `suites` field during the documented compatibility window; ship idempotent migration and fixture coverage. |
| RK3 | Registry eligibility metadata diverges from actual references. | Medium | High | Validate dependency closure, emitted inventory, root adapters, configs, catalog rows, and generated references in CI. |
| RK4 | Staged publication follows a link, exposes a mixed active-root set, or loses user files during a race. | Medium | Critical | Use `secure_fs` root-anchored no-follow operations, durable transaction journal, per-root activation pointers, checksum-gated deletion, interruption tests, and rollback. |
| RK5 | Refactoring link scripts retains Windows/POSIX divergence. | Medium | High | Centralize synchronization in one Python worker and run parity tests on both host families. |
| RK6 | Catalog/routing reintroduces all-skill metadata or a silent fallback. | Medium | High | Build catalog from manifest metadata only, assert compact output, and hard-stop missing capabilities before work. |
| RK7 | Imported Markdown contains supply-chain or prompt-injection behavior. | Medium | Critical | Default-deny quarantine, immutable source verification, no runtime network execution, static scanning, secret-redacted deterministic diff, and two-stage approval. |
| RK8 | Managed and user roots collide under Windows/macOS normalization. | Medium | High | Normalize/case-fold/confusable-check identifiers before writes; preserve user bytes and keep roots distinct. |
| RK9 | Measured inventory reduction degrades selected task success. | Medium | High | Baseline and compare immutable fixture route/output assertions separately for every profile; unavailable host evidence or reductions without working routes fail the release gate. |
| RK10 | Canonical vendoring writes to a consumer projection or disposable installation. | Medium | Critical | Split consumer review and maintainer vendor modes; require verified canonical source checkout, branch, origin, and matching quarantine digests before canonical mutation. |

## Out of Scope

- A public marketplace, arbitrary automatic installation, remote runtime skill
  fetching, shared filtered-profile cache, temporary session-only capability
  overrides, or semantic rewrites of imported skills.
- Changing the stable `/cg-*` or `/cr-*` namespaces, or adding `/cg-skill*`
  commands; `/cg-import-skill` supersedes the existing roadmap's
  `/cg-skill-import` text only after the planned `@cg-roadmap` contract update.
- Filtering the global canonical `.github/`, `.claude`, `.agents`, `.opencode`,
  or `.kilo` source trees for one consumer project.
- Treating `skills.paths` as an exclusion mechanism, suppressing Kilo failures,
  or claiming an unverified environment variable as a permanent Kilo contract.
- Direct edits to `roadmap.json` or duplicate roadmap features.
- Starting the GitHub Actions external-skill hardening pilot before the controlled
  vendoring intake and approval evidence independently pass.

## Completion Contract

### Outcome

Every supported project resolves a strict, reviewable active manifest containing
its selected platform ids and uses a journaled, recoverable per-root activation
transaction to materialize only selected project-local runtime assets. Kilo and
Codex coexist only through the certified contained launch path; inactive
capabilities hard-stop with remediation; and approved external skills follow a
quarantined, auditable maintainer-vendor path.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Kilo/Codex sentinels prove local-only Kilo discovery through `cg-kilo`, or block with exact remediation. | `python -m pytest scripts/tests/test_kilo_coexistence.py` plus supported-host evidence fixture | yes |
| V2 | 1 | Certified launcher/preflight preserves Codex behavior, marks direct launches unsupported, and does not mutate global environment/config. | wrapper and link/update test results | yes |
| V3 | 2 | Before-state profile baseline contains comparable inventory, metadata, context, and executable task-oracle measures. | `.cg-docs/cost/skill-loading-baseline.json` and `.md` | yes |
| V4 | 2 | Strict config, registry eligibility, and mandatory closure reject invalid values and resolve valid profiles. | `python -m pytest scripts/tests/test_module_registry.py scripts/tests/test_context_budget.py scripts/tests/test_config_migration.py` | yes |
| V5 | 2 | Active manifest is deterministic and detects immutable config/registry/source/closure/platform-plan staleness while ownership drift reconciles separately. | `python -m pytest scripts/tests/test_project_manifest.py` | yes |
| V6 | 3 | Project projection plan renders distinct selected inventories and no inactive-reference leaks. | `python -m pytest scripts/tests/test_project_projection.py scripts/tests/test_target_closure.py` | yes |
| V7 | 3 | Publication is no-follow, checksum-owned, journal-recoverable across per-root activation, interruption-safe, and Windows/POSIX equivalent. | projection/secure-fs tests plus link/unlink/parity safe-runner results | yes |
| V8 | 3 | `cg-link` and `cg-update` resolve, publish, migrate, and verify without deleting user bytes. | link/update/unlink test evidence | yes |
| V9 | 4 | `/cg-find-skill` yields compact manifest-backed results and full filtered records only on request. | `python -m pytest scripts/tests/test_skill_catalog.py` | yes |
| V10 | 4 | Explicit inactive capability requests hard-stop with config and regeneration remedy. | catalog/router/closure test evidence | yes |
| V11 | 5 | Importer rejects all prohibited content before canonical/runtime mutation. | `python -m pytest scripts/tests/test_import_skill.py` | yes |
| V12 | 5 | Approved vendor bundle has immutable provenance, review evidence, verified maintainer-source registration, and post-refresh availability. | import fixture/provenance evidence plus catalog test | yes |
| V13 | 6 | Profile/platform/migration/collision/regression matrix passes on supported hosts. | CI artifacts and `tests/last-run.json` from `. tests\Run-Tests.ps1` | yes |
| V14 | 7 | Before/after measurements show active-inventory and routine-context reduction without selected-workflow regressions. | projection benchmark artifacts | yes |
| V15 | 5 | Existing vendoring feature records the approved `/cg-import-skill` contract reconciliation before implementation. | targeted post-`@cg-roadmap` read | yes |
| V16 | final | Existing roadmap features are linked only to verified evidence; no duplicates are created. | targeted post-`@cg-roadmap` read and execution report | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Kilo and Codex may coexist only through the certified `cg-kilo` path with verified external-root containment. | V1 and V2 evidence |
| C2 | 2 | `.github/` remains complete canonical source; no consumer profile filters global source/output trees. | projection tests inspect distinct source/project roots |
| C3 | 2 | Only absent legacy `suites` defaults to `[cg]`; malformed present values fail closed. | strict config fixtures |
| C4 | 3 | Publication never follows a link/reparse point, claims project-wide atomicity without a transaction, or deletes unverified user-owned content. | secure filesystem, journal recovery, and interruption tests |
| C5 | 3 | Windows and POSIX use equivalent ownership and preservation semantics. | parity fixtures on both hosts |
| C6 | 4 | Catalog/router never load inactive skill bodies or silently fall back. | compact-output and hard-stop tests |
| C7 | 5 | Imported content is non-executable, immutable, quarantined, reviewed, provenance-registered, and canonically written only by verified maintainer mode. | importer/admission/provenance tests |
| C8 | 6 | All required Pester evidence uses the safe runner and records `tests/last-run.json`. | runner artifact fields and CI workflow |
| C9 | 7 | Context savings are not reported without per-profile selected-task success. | benchmark schema validation |

### Boundaries

- Allowed: versioned registry/config/manifest schemas; project-local selected
  projections; cross-platform secure synchronization; Kilo containment gate;
  static discovery/routing; controlled vendoring; migrations; measured docs and
  roadmap evidence links.
- Out of scope: marketplace, remote runtime fetching, global filtered caches,
  automatic arbitrary installs, semantic vendor rewrites, temporary capability
  overrides, renamed workflow namespaces, direct roadmap edits, and unverified
  Kilo behavior claims.

### Iteration Policy

1. **deviation-policy: ask** -- pause and record a decision before changing this
   plan's scope, platform support, public command behavior, schema compatibility
   window, or security admission policy.
2. Do not begin Phase 2 until the Phase 0 release gate recorded in Phase 1 has
   successful supported-host `cg-kilo` containment evidence; a blocking
   preflight outcome or unsupported direct launch is not a pass.
3. Preserve existing canonical generation/ownership tests while extracting pure
   projection planning; update test doubles and characterization fixtures in the
   same change as an API refactor.
4. Keep configuration-derived capabilities authoritative. Additive explicit
   capabilities may extend but never subtract the derived baseline.
5. Prefer one shared secure projection worker over platform-specific copy logic.
   Publish through durable per-root activation pointers and recovery journal, not
   an unsupported claim of one atomic multi-root filesystem rename. A platform
   exception requires a documented, tested reason and user approval.
6. Treat vendor quarantine and admission as a security boundary. No roadmap
   hardening pilot, canonical source write, or runtime exposure proceeds before
   consumer-review versus maintainer-vendor mode evidence passes.
7. Treat immutable selection manifest staleness separately from mutable
   projection ownership reconciliation; user modifications must be preserved,
   reported, and never silently change profile selection.
8. Publish final documentation and roadmap statuses only after all required
   profile, platform, security, and benchmark evidence succeeds.

### Blocked-Stop Conditions

- The deployed supported Kilo version cannot prove `cg-kilo` process-scoped
  exclusion of external `.agents/skills` and `.claude/skills` while retaining
  local `.kilo/skills` and Codex behavior.
- A strict manifest/config/registry validation error has no actionable migration
  or correction path.
- Projection synchronization cannot guarantee no-follow containment, journaled
  per-root recovery to a coherent active generation, checksum-gated stale
  deletion, and user-byte preservation on a supported host.
- Any selected platform projection contains an inactive asset/reference or fails
  its target ownership/drift gate.
- An import admission control, consumer/maintainer mode boundary, provenance
  record, deterministic review, or required approval cannot be completed.
- Required before/after benchmark evidence shows selected-workflow regression or
  cannot be collected comparably.
- Defaults from `.kilo/shared/goal-execution.contract.md` also apply, including
  unavailable safe verification, failed required evidence, an unapproved
  `ask`-policy deviation, protected-boundary crossing, or inability to persist
  the execution report.
