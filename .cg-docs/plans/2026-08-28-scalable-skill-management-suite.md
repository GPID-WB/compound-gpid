---
date: 2026-08-28
title: "Scalable Skill Management Suite"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-08-28-scalable-skill-management-suite.md"
language: "both"
estimated-effort: "large"
deviation-policy: "ask"
execution-report: ".cg-docs/work-reports/2026-08-28-scalable-skill-management-suite.md"
artifact-schema-version: 1
phases: 7
completed-phases: [1]
current-phase: 2
tags: [skills, architecture, lifecycle, security, registry, manifests, projections, cross-platform, documentation, testing]
---

# Plan: Scalable Skill Management Suite

## Objective

Build one role-gated `/cg-skill` command that manages the complete skill
lifecycle without becoming one large prompt or Python script. Use explicit
operation descriptors, workflows, contracts, and modules; reuse focused domain
services; support permanent and project-specific skills; and verify every
selected platform through deterministic, fail-closed plan/apply transactions.

The first public release is complete only when discovery, inspection, creation,
import, update, validation, activation, deactivation, audit, deprecation,
removal, help, documentation, migration, and release gates all pass. The old
`/cg-find-skill` and `/cg-import-skill` surfaces remain until that final gate and
are then removed without compatibility aliases.

## Context

The approved brainstorm selected explicit operation modules behind one thin
command. It also selected strict consumer and maintainer roles, deterministic
plan then apply for all mutations, immutable identifiers, a dedicated committed
project skill store, immediate old-command replacement at release, and one
complete first public release.

Existing implementation provides useful but disconnected foundations:

- `scripts/cg_skill_catalog.py` builds and filters a manifest-backed catalog,
  routes capabilities, and formats output.
- `scripts/cg_import_skill.py` fetches pinned bundles to quarantine, runs
  admission, writes review evidence, and vendors to canonical source.
- `scripts/cg_vendor_policy.py` owns current source, path, scan, limit,
  checkout, and collision rules.
- `scripts/cg_project_manifest.py` resolves strict configuration and the
  canonical module registry into the active manifest.
- `scripts/cg_project_projection.py` plans, publishes, recovers, and verifies
  checksum-owned project projections.
- `scripts/cg_generate_targets.py` inventories atomic skill bundles and renders
  committed native targets.
- `scripts/cg_validate_modules.py` validates module ownership, dependencies,
  capabilities, and cross-suite references.
- `scripts/link.ps1` and `scripts/update.ps1` orchestrate installation,
  manifest, and projection flows but are not suitable lifecycle engines.

Research found these implementation blockers:

- Import registration appends provenance but does not assign module ownership,
  capability metadata, or owned assets.
- Catalog construction is duplicated between the catalog and manifest code and
  produces inconsistent capability fields.
- Missing or stale manifests hard-stop discovery instead of permitting clearly
  labeled prospective results.
- Nested shared operation descriptors and contracts are not recursively
  inventoried and are flattened by target generation.
- The module validator does not recursively enumerate nested shared assets.
- Project registry and project provenance schemas do not exist.
- Current project projection excludes Copilot because `.github/skills` is a
  canonical linked unit.
- Generator, manifest, projection, and import use separate write boundaries;
  there is no complete lifecycle transaction.
- Existing import and catalog tests are not included in the authoritative native
  preflight list.

The user approved managed Copilot bundle projection: `.github/skills/` becomes
a real project parent, and selected bundles are published as checksum-owned
files while unrelated user-owned bundles remain untouched.

No new runtime dependency is planned. Python implementations must remain
compatible with Python 3.8. Contract files use the closed
`compound-gpid-schema-subset-v1` dialect and a standard-library validator rather
than claiming full JSON Schema support. The validator rejects every keyword
outside the declared subset.

The reviewed plan also makes these distinctions explicit:

- Project capabilities use `activationMode: "explicit-only"`. Eligibility
  selectors may block eligibility but cannot activate a project skill. The
  manifest records `selectedProjectSkills` as a one-to-one capability-to-bundle
  map and does not select all assets through the shared `project-local` owner.
- Project imports may approve one normalized credential-free public GitHub HTTPS
  origin in an exact plan even when that repository is not on the plugin vendor
  allowlist. Plugin vendoring remains allowlist-only. Both scopes keep the same
  canonical admission ceilings. Unsupported hosts or providers are rejected in
  the first release because bounded acquisition cannot be proven for them.
- Lifecycle publication is crash-consistent and convergent, not atomically
  visible across independent host roots. No operation reports success before
  every selected root reaches and verifies the desired state.
- Approval fields are audit metadata. Repository branch protection and reviewed
  change integration remain the human authorization boundary.

## Requirements

| ID | Requirement | Source |
| --- | --- | --- |
| R1 | Provide one public `/cg-skill <operation>` grammar with a thin prompt dispatcher and thin Python dispatcher. | Brainstorm: Purpose and Command Grammar |
| R2 | Give every operation one descriptor, focused workflow, Python module, request/result contract, test surface, and documentation page. Adding an operation must not change existing operation files. | Brainstorm: Architecture |
| R3 | Enforce consumer and maintainer write contexts in code. Consumer is the default. Maintainer mutation requires invocation root, project root, and canonical source root to be the same approved development checkout on a nonprotected feature branch; a role flag, linked global source, origin string, or free-text approver cannot elevate authority. | Brainstorm: Users and Authority; plan review P1.4 |
| R4 | Use stable `cg-skill-request-v1`, `cg-skill-result-v1`, and `cg-skill-plan-v1` envelopes with operation-specific contracts in the closed `compound-gpid-schema-subset-v1` dialect, stable exit codes, finding codes, severities, remediation, and deterministic ordering. | Brainstorm: Inputs and Outputs; plan review P2.1 |
| R5 | Make every lifecycle mutation plan by default and require `--apply <digest>`. Bind the digest to normalized arguments, role, source, registries, config, manifest, provenance, references, and bundle inventory. | Brainstorm: Approval Contract |
| R6 | Support permanent plugin skills in canonical `.github/` and project-specific imported skills under `.compound-gpid/skills/` with a committed project registry and provenance store. | Brainstorm: Project-Specific Skill Store |
| R7 | Use reserved owner `project-local`, one `activationMode: "explicit-only"` capability `project-skill-<id>` per project skill, and a manifest `selectedProjectSkills` one-to-one map. Select project bundles from that map rather than the shared owner glob. Project records cannot shadow or weaken canonical records. | Approved contract C6/C8; plan review P1.1 |
| R8 | Treat `SKILL.md` and all nested regular resources as one atomic bundle. Validate frontmatter, paths, links, contents, declared non-data resource class, inventory, and portable collisions. Reject tabular, statistical, database, archive, environment, credential, and other data-bearing formats before commit. | Brainstorm: Creation Metadata; charter; plan review P1.5 |
| R9 | Let `find`, `info`, and `help` produce clearly labeled prospective catalog output when the manifest is missing or stale, but never claim active or projected state. Invalid input still fails closed. | Brainstorm: Missing or Stale Manifest Behavior |
| R10 | Scaffold permanent skills with valid quoted ASCII-safe frontmatter and optional focused references, workflows, examples, and resources. Require explicit owner and capability metadata and block identifier/path collisions. | Brainstorm: Creation Workflow |
| R11 | Quarantine imports pinned to one normalized credential-free public GitHub HTTPS repository, normalized source path, and full SHA. Use bounded provider API traversal: enumerate the selected tree and declared blob sizes before content reads, then stream each blob under metadata/per-file/total limits and verify Git object identity. Reject unsupported providers. Project exact-origin approval and plugin allowlist approval are separate policy paths. | Brainstorm: Security; plan review final P2.1 |
| R12 | Distinguish project import from plugin vendoring. Project approval cannot grant plugin authority. Canonical mutations require maintainer write context plus approver and immutable review reference as audit metadata; branch protection remains the authorization boundary. | Brainstorm: Security and Role Matrix; plan review P1.4 |
| R13 | Update only imported skills with pinned provenance and an explicit new full SHA. Produce a deterministic redacted diff and preserve append-only provenance history. | Brainstorm: Update Workflow |
| R14 | Activate and deactivate only explicit capabilities through a byte-preserving strict config plan. Do not subtract selector-derived or dependency-required capabilities. Project capabilities are explicit-only and select one bundle through `selectedProjectSkills`. Regenerate and exactly verify manifest and desired projections in the same apply. | Brainstorm: Activation; plan review P1.1/P2.4 |
| R15 | Keep skill IDs immutable. Deprecation requires a valid acyclic same-origin successor. Plugin removal requires a versioned release attestation bound to tag-ref object SHA, peeled commit SHA, payload digest, and deprecation-record digest plus a later attested release; project removal requires a later descendant project revision. A versioned migration must stage exact digest-bound edits and rescan to zero live references before owned-only deletion and tombstone publication. | Brainstorm: Identity Lifecycle; final plan review P1.1 |
| R16 | Validate and audit frontmatter, non-data bundle policy, links, source paths, ownership, capabilities, provenance, selectors, platform eligibility, references, generated parity, manifest freshness, exact desired projections, and containment with error/warning/info findings and exact remediation. Generic mutable update discovery is excluded; candidate comparison occurs only in `update --to <full-sha>`. | Brainstorm: Validation and Audit; plan review P1.6/P1.8 |
| R17 | Extract reusable APIs from existing catalog, import, policy, registry, manifest, projection, generator, and validator code. Do not duplicate their domain rules in operation modules. | Brainstorm: Responsibility Boundaries; research |
| R18 | Recursively inventory and path-preserve nested shared contracts and descriptors in module ownership and all generated targets. | Research: generator and validator blocker |
| R19 | Combine validated canonical and project registry snapshots with separate digests for catalog, closure, manifest, generation, projection, validation, and reference scanning. | Research: project overlay blocker |
| R20 | Materialize approved canonical and project skill bundles for Copilot, Claude Code, Codex, OpenCode, and Kilo. Target mapping declares Copilot skill-only projection to a real `.github/skills/` managed root while all other Copilot categories keep their current linked topology. | User approval; plan review P1.3 |
| R21 | Serialize lifecycle writers with a project lock. Stage and validate all outputs, journal expected bytes and progress durably, publish with compare-before-replace semantics, and recover deterministically to one validated desired state. Do not claim atomic host visibility across roots or overwrite concurrent non-lifecycle changes. | Brain findings; plan review P1.2/P1.8 |
| R22 | Keep old commands active through a full pre-removal replacement gate. Then stage new public registration and old-surface removal together, run a full final-tree gate, and publish only if both gates pass. Keep old names only in migration documentation and immutable historical artifacts. | User decision; plan review P1.9 |
| R23 | Add focused overview, lifecycle, operation, maintainer, consumer, security, migration, configuration, installation, and troubleshooting documentation. Derive completeness from operation descriptors. | Brainstorm: Documentation Information Architecture |
| R24 | Add unit, contract, security, registry, manifest, projection, target parity, reference safety, documentation, wrapper, installer, cross-platform, and release-gate tests. Include all skill-management tests in authoritative preflight. | Brainstorm: Test Strategy; research |
| R25 | Preserve Python 3.8 and current Python behavior, Windows/macOS/Linux support, Pester safe-runner rules, deterministic bytes, canonical `.github/` authority, and generated-tree ownership. Require Linux and Python 3.8 CI evidence, not local inference. | Charter; project instructions; plan review P2.5 |
| R26 | Keep project-authored non-imported skills, project policy overlays, marketplace search, remote runtime fetch, mutable Git references as imported source identity, runtime execution, and in-place rename out of scope. Read-only validation of immutable release tags remains allowed for lifecycle grace. | Brainstorm: Out of Scope; plan review follow-up |
| R27 | Do not release a partial production replacement. Internal phases can coexist with old commands until every final gate passes. | User decision: Full Release |

## Plan Review Resolution

| Finding | Resolution in this revision |
| --- | --- |
| P1.1 | Added explicit-only project capabilities, `selectedProjectSkills`, two-skill isolation, and canonical initial-availability rules. |
| P1.2 | Replaced cross-root atomicity with an exclusive lifecycle lock, durable commit point, serialized publication, exact convergence, and deterministic forward recovery. |
| P1.3 | Made the hybrid Copilot target-mapping mode mandatory and added Windows/POSIX link, update, and unlink scope and tests. |
| P1.4 | Required equal invocation/project/source roots and a nonprotected feature branch; treated approver fields as audit metadata rather than authorization proof. |
| P1.5 | Added a committed non-data resource policy and negative import, vendor, and create tests. |
| P1.6 | Removed generic mutable update discovery from first-release audit grammar. |
| P1.7 | Added executable plugin tag/release grace, project revision grace, digest-bound staged migrations, zero-reference rescan, and successor graph checks. |
| P1.8 | Replaced ownership-only projection checks with exact desired path, digest, ownership, and managed-bundle inventory verification. |
| P1.9 | Kept the CLI private until a full pre-removal gate, staged public registration/removal together, and required a second final-tree gate. |
| P2.1 | Defined a closed standard-library schema subset, rejected unsupported keywords, and reserved stable exit codes. |
| P2.2 | Deferred each runtime operation descriptor until its workflow, handler, contract, focused page, and tests exist. |
| P2.3 | Separated exact-origin project approval from allowlist-only plugin vendoring. |
| P2.4 | Selected a byte-preserving source-span config editor with exact prior-digest publication. |
| P2.5 | Added required Linux and Python 3.8 CI jobs, CI artifact evidence, and an execution-report pointer. |
| P2.6 | Expanded active reference scanning to roadmap, project context, adapters, installers, docs, and generated trees with explicit historical exemptions. |
| P2.7 | Replaced broad completion evidence with exact commands or named CI artifacts and required registration completeness checks. |
| P2.8 | Kept Phase 2 read tests canonical-only and moved project-origin behavior to the project overlay phase. |
| P3.1 | Moved dispatcher verification V4 to Phase 1. |
| Follow-up P1.1 | Removed mutable grace-anchor finalization. Removal planning derives immutable plugin tag/release and project commit evidence from the exact committed deprecation-record digest while audit remains read-only. |
| Follow-up P2.1 | Defined held-handle POSIX/Windows advisory locking, no-follow validation, diagnostic-only metadata, crash release, timeout, and concurrent recovery tests. |
| Follow-up P2.2 | Added target ownership to V2 and exact safe-runner link/unlink/bash/parity evidence to V10. |
| Final P1.1 | Added a separate future-release attestation that pins tag-ref object SHA, peeled commit SHA, release payload SHA-256, and deprecation-record digests; moved-tag validation blocks removal. |
| Final P2.1 | Replaced unbounded Git clone/archive acquisition with bounded public GitHub tree/blob API traversal and rejection of unsupported providers. |

## Dependency Graph

```text
Phase 1 contracts and packaging substrate
  -> Phase 2 read-only command spine
  -> Phase 3 project registry and all-platform runtime
  -> Phase 4 transaction and secure project lifecycle
  -> Phase 5 maintainer creation, vendoring, and update
  -> Phase 6 audit, deprecation, and removal
  -> Phase 7 migration, documentation, and release
```

Phase 3 must solve managed Copilot bundle projection before project import can
be considered usable. Phase 4 must prove the shared transaction and hardened
admission before any plugin writer is added. Phase 7 must not remove old command
surfaces until all earlier evidence is green.

## Phase 1: Contracts and Packaging Substrate

### 1. Define Versioned Common Contracts and the Closed Schema Dialect

- **Requirements**: R1, R2, R4, R5, R6, R7, R12, R15, R19, R25
- **Files**: `.github/shared/skill-management/contracts/schema-subset-v1.schema.json`, `.github/shared/skill-management/contracts/operation-descriptor-v1.schema.json`, `.github/shared/skill-management/contracts/request-v1.schema.json`, `.github/shared/skill-management/contracts/result-v1.schema.json`, `.github/shared/skill-management/contracts/plan-v1.schema.json`, `.github/shared/skill-management/contracts/project-registry-v1.schema.json`, `.github/shared/skill-management/contracts/provenance-v1.schema.json`, `.github/shared/skill-management/contracts/release-attestation-v1.schema.json`, `scripts/skill_management/contracts.py`, `scripts/tests/test_skill_management_contracts.py`
- **Details**: Define strict common envelopes, operation argument/data schemas,
  stable findings, roles, manifest health, lifecycle states, action kinds,
  project registry records, explicit-only activation, selected project bundles,
  provenance history, migration records, and tombstones. Step 1 defines only the
  descriptor meta-contract and common envelopes. Each operation adds its own
  descriptor and operation contract with its implementation; runtime help and
  dispatch never advertise a planned or absent operation.
- **Details**: Define `compound-gpid-schema-subset-v1` as a closed dialect with
  only `$schema`, `$id`, local `$ref`, `$defs`, `type`, `properties`, `required`,
  `additionalProperties`, `items`, `enum`, `const`, `pattern`, `minLength`,
  `maxLength`, `minimum`, `maximum`, `minItems`, `maxItems`, and `uniqueItems`.
  Reject unsupported keywords and nonlocal references. Use JSON-pointer path then
  finding code for deterministic error order. Add a meta-validator that proves
  contract files and runtime validation reject the same invalid objects.
- **Details**: Reserve exit codes: `0` success, `2` usage/unknown operation, `3`
  contract/config/registry/manifest invalid, `4` role/approval context invalid,
  `5` admission policy/security failure, `6` lifecycle/reference conflict, `7`
  stale plan/concurrent state, and `8` generation/projection verification fail.
  Unexpected internal failures use `1` with redacted diagnostics.
- **Test Scenarios**: Valid meta-contract and each envelope; unsupported schema
  keyword; remote `$ref`; unknown keys; missing fields; invalid exit/finding/
  lifecycle values; duplicate IDs; shadowing; explicit-only selection;
  deterministic canonical serialization and error order.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_contracts.py -q`
- **Acceptance criteria**: Contracts are versioned, deterministic, strict, and
  sufficient for every decided operation without operation-specific fields in
  the common router.

### 2. Support Recursive Shared Resources and Internal Ownership

- **Requirements**: R2, R18, R20, R25
- **Files**: `scripts/cg_generate_targets.py`, `scripts/cg_validate_modules.py`, `.github/shared/module-registry.json`, `.github/skills/cg-skill-management/SKILL.md`, `scripts/tests/test_cg_generate_targets.py`, `scripts/tests/test_target_packaging.py`, `scripts/tests/test_target_ownership.py`, `scripts/tests/test_target_drift.py`, `scripts/tests/test_module_registry.py`
- **Details**: Replace immediate-child `.github/shared/*` scanning with recursive
  regular-file inventory. Preserve paths relative to `.github/shared/` instead
  of flattening to basenames. Apply portable path collision, no-follow, regular
  file, ownership, and deterministic ordering checks to nested resources.
- **Details**: Add internal module `cap-skill-management` to own
  `.github/skills/cg-skill-management/` and
  `.github/shared/skill-management/`. Do not add a public capability record or
  `suite-cg` dependency until the Phase 7 public-registration changeset. Use
  synthetic registry fixtures to prove recursive target output before public
  selection is possible.
- **Details**: Promote stable public path and ownership helpers rather than
  continuing private cross-module calls such as `_glob_match()`. Replace Python
  3.9-only `removeprefix()` use in module validation.
- **Test Scenarios**: Nested contracts under a synthetic selected module on all
  native targets;
  same basenames in different directories; unsafe nested path; nested directory
  symlink; multiple owner; unowned file; exact byte parity; stale nested output.
- **Tests**: `python -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_packaging.py scripts/tests/test_target_ownership.py scripts/tests/test_target_drift.py scripts/tests/test_module_registry.py -q`
- **Acceptance criteria**: Nested management contracts are exactly owned and
  path-preserved when the internal module is selected, but the current public
  suite closure does not expose the incomplete management capability.

### 3. Add the Private CLI Dispatcher and Shared Core Skeleton

- **Requirements**: R1, R2, R3, R4, R17, R25, R27
- **Files**: `scripts/cg_skill.py`, `scripts/skill_management/__init__.py`, `scripts/skill_management/context.py`, `scripts/skill_management/planning.py`, `scripts/skill_management/operations/__init__.py`, `scripts/tests/test_skill_management_dispatch.py`
- **Details**: Keep the internal entry point reachable only through
  `python scripts/cg_skill.py` until Phase 7. Do not add a canonical prompt,
  public wrapper, installer registration, suite dependency, generated command,
  or public help surface in this phase. Make the CLI parse common arguments,
  validate one active descriptor, lazy-import one
  handler, and render one result envelope. It must contain no lifecycle rules.
- **Details**: Add consumer-safe context discovery. Maintainer write context
  requires invocation Git root, `project_root`, and `source_root` to be the same
  validated canonical development checkout on a non-detached, nondefault,
  nonprotected feature branch. A consumer project linked to a valid canonical
  global source remains consumer. Origin and audit metadata do not prove human
  authority; reviewed branch integration remains external enforcement.
- **Test Scenarios**: Unknown operation; path-like operation; malformed
  descriptor; handler outside allowed package; one lazy import; consumer role;
  linked valid global source; detached/default/protected branch; spoofed
  canonical files; wrong origin; mismatched roots; JSON and human error rendering.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_dispatch.py -q`
- **Acceptance criteria**: The private entry point routes safely without any
  public product surface, and adding an active descriptor does not require a
  dispatcher code change.

## Phase 2: Read-Only Command Spine

### 4. Extract Catalog, Registry, and Bundle Service APIs

- **Requirements**: R8, R9, R16, R17, R19, R25
- **Files**: `scripts/skill_management/services/catalog.py`, `scripts/skill_management/services/registry.py`, `scripts/skill_management/services/bundles.py`, `scripts/cg_skill_catalog.py`, `scripts/cg_project_manifest.py`, `scripts/cg_validate_modules.py`, `scripts/cg_generate_targets.py`, `scripts/tests/test_skill_catalog.py`, `scripts/tests/test_project_manifest.py`, `scripts/tests/test_module_registry.py`
- **Details**: Create one canonical `RegistrySnapshot` abstraction that Phase 3
  can extend with a project overlay, and one source-neutral asset inventory API.
  Move catalog construction to one service and make manifest
  catalog records call it. Resolve the current capability-field disagreement.
  Expose public owner matching, path validation, frontmatter parsing, atomic
  bundle inventory, and Markdown-reference APIs.
- **Details**: Separate `project_root` from canonical `source_root` in one
  `SkillManagementContext`. Add manifest health values `fresh`, `missing`,
  `stale`, and `invalid`. Resolve canonical prospective rows in memory without
  writes. Do not implement or simulate project-origin records before Step 7.
- **Details**: Keep old script entry points as internal implementation shims
  during migration, but make them call the new services rather than duplicate
  rules.
- **Test Scenarios**: Canonical-only and prospective catalog; valid fresh
  manifest; stale config/registry/source; malformed manifest; deterministic
  rows; owner/capability consistency; bundle resources; local links; portable
  collisions.
- **Tests**: `python -m pytest scripts/tests/test_skill_catalog.py scripts/tests/test_project_manifest.py scripts/tests/test_module_registry.py -q`
- **Acceptance criteria**: Catalog, manifest, validation, and later operations
  consume the same validated registry, bundle, and metadata models.

### 5. Implement `find`, `info`, and `help`

- **Requirements**: R1, R2, R4, R9, R16, R23
- **Files**: `.github/skills/cg-skill-management/workflows/find.md`, `.github/skills/cg-skill-management/workflows/info.md`, `.github/skills/cg-skill-management/workflows/help.md`, `.github/shared/skill-management/contracts/find-v1.schema.json`, `.github/shared/skill-management/contracts/info-v1.schema.json`, `.github/shared/skill-management/contracts/help-v1.schema.json`, `.github/shared/skill-management/operations/find.json`, `.github/shared/skill-management/operations/info.json`, `.github/shared/skill-management/operations/help.json`, `scripts/skill_management/operations/find.py`, `scripts/skill_management/operations/info.py`, `scripts/skill_management/operations/help.py`, `docs/skills/management/commands/find.md`, `docs/skills/management/commands/info.md`, `docs/skills/management/commands/help.md`, `scripts/tests/test_skill_management_read.py`
- **Details**: Preserve existing useful catalog filters and add exact identifier
  lookup. Compact output includes purpose, capability, availability or manifest
  health, activation cost, and origin. Full output includes owner, source,
  provenance identity, selectors, supported suites/platforms, and inactive or
  prospective reason.
- **Details**: Missing or stale manifest output must say `prospective` and
  provide exact regeneration remediation. Capability routing and active-state
  claims remain hard stops until a fresh manifest exists.
- **Test Scenarios**: Fresh, missing, stale, and invalid manifest; exact and
  partial ID filters; canonical origin; unknown ID; deterministic
  help order; inactive reason; no global fallback.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_read.py scripts/tests/test_skill_catalog.py -q`
- **Acceptance criteria**: Read-only discovery remains useful when runtime state
  is absent but cannot misrepresent availability or bypass invalid inputs.

### 6. Implement Baseline `validate` and Common Findings

- **Requirements**: R2, R4, R8, R16, R24
- **Files**: `.github/skills/cg-skill-management/workflows/validate.md`, `.github/shared/skill-management/contracts/validate-v1.schema.json`, `.github/shared/skill-management/operations/validate.json`, `scripts/skill_management/operations/validate.py`, `docs/skills/management/commands/validate.md`, `scripts/skill_management/contracts.py`, `scripts/tests/test_skill_management_read.py`, `scripts/tests/test_skill_management_completeness.py`
- **Details**: Validate one skill or all known skills through shared services.
  At this phase cover descriptor, frontmatter, bundle inventory, local links,
  ownership, capability record, manifest health, source confinement, and stable
  finding rendering. Later phases extend the same operation with provenance,
  project registry, projection, and lifecycle checks.
- **Details**: Enforce descriptor completeness for every registered operation:
  workflow, handler, contract, test declaration, and documentation path. Permit
  no runtime `planned` descriptor state and no absent required path. Each later
  operation step adds its descriptor only with its handler, workflow, contract,
  focused command page, and tests. Phase 7 expands cross-cutting documentation
  and public navigation rather than repairing incomplete operation descriptors.
- **Test Scenarios**: Error/warning/info sorting; exact remediation; one/all;
  invalid frontmatter; broken local link; missing owner; incomplete descriptor;
  deterministic JSON; human output parity.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_read.py scripts/tests/test_skill_management_completeness.py -q`
- **Acceptance criteria**: All read-only operations share one findings model and
  baseline validation has no operation-local parser or formatter.

## Phase 3: Project Registry and All-Platform Runtime

### 7. Add the Project Skill Store and Registry Overlay

- **Requirements**: R6, R7, R8, R19, R25, R26
- **Files**: `.compound-gpid/skills/` as runtime-created project source, `.compound-gpid/project-skill-registry.json` as runtime-created committed state, `.compound-gpid/skill-provenance/` as runtime-created committed state, `.gitignore`, `SCHEMA_VERSION`, `scripts/skill_management/services/registry.py`, `scripts/skill_management/services/provenance.py`, `scripts/cg_project_manifest.py`, `scripts/cg_context_budget.py`, `scripts/parsing_utils.py` only if strict config support changes, `scripts/tests/test_project_skill_registry.py`, `scripts/tests/test_project_manifest.py`, `scripts/tests/test_context_budget.py`
- **Details**: Define strict project records with identifier, source path,
  `project-local` owner, `project-skill-<id>` capability,
  `activationMode: "explicit-only"`, suite/platform eligibility selectors,
  lifecycle, provenance identity, and bundle digest. Eligibility selectors may
  reject a platform or suite but never activate a project capability. Project
  records cannot edit canonical modules, dependencies, capabilities, or security
  policy.
- **Details**: Extend canonical capability validation with optional
  `activationMode: "explicit-only"` while preserving the existing legacy default
  for current records. New standalone canonical capabilities can use this mode;
  project capabilities must use it.
- **Details**: Build one immutable combined snapshot with separate source
  digests. Resolve closure and active manifest against both stores. Add project
  assets to desired-plan and catalog digests. Add manifest
  `selectedProjectSkills` as a one-to-one capability-to-bundle map. Select project
  assets from this map, never from the broad `project-local` ownership glob. Keep
  active manifest reviewable and
  project skill source/registry/provenance committed; keep plans, quarantine,
  reviews, journals, and runtime ownership state ignored as appropriate.
- **Test Scenarios**: Empty overlay; one project skill; two project skills with
  only one explicitly selected and only one projected; empty selectors remain
  inactive; reserved-namespace
  violation; canonical shadow; source escape; missing bundle; digest mismatch;
  case collision; invalid suite/platform; deterministic combined closure;
  gitignore containment.
- **Tests**: Project registry, manifest, context budget, strict config, and
  gitignore-focused tests.
- **Acceptance criteria**: All consumers use one validated snapshot, and project
  skills are explicit committed inputs rather than global or generated sources.
  Importing one skill does not activate it or expose any sibling project bundle.

### 8. Make Generation and Projection Source-Neutral

- **Requirements**: R8, R18, R19, R20, R21, R25
- **Files**: `scripts/cg_generate_targets.py`, `scripts/cg_project_projection.py`, `.github/shared/target-mapping.json`, `scripts/tests/test_cg_generate_targets.py`, `scripts/tests/test_target_packaging.py`, `scripts/tests/test_target_ownership.py`, `scripts/tests/test_target_path_safety.py`, `scripts/tests/test_project_projection.py`
- **Details**: Accept validated asset inventories that identify origin and
  source root. Render project bundles through the same target renderer as
  canonical bundles. Preserve origin and provenance identity in plan metadata
  without exposing absolute source paths.
- **Details**: Strengthen manifest freshness validation to include configuration,
  canonical registry, project registry, source revision, desired plan, and
  platform selection. Malformed ownership or journal JSON is an error, not an
  empty state.
- **Details**: Preserve current no-follow, path, checksum, drift, and Kilo
  compatibility mirror rules, but replace ownership-only verification with exact
  desired-plan verification. Every planned path and digest must exist, every
  ownership entry must match, each managed bundle must contain exactly its
  planned inventory, and no unexpected file may remain inside it. A modified
  selected destination is preserved but blocks apply. Do not create a second
  platform renderer.
- **Test Scenarios**: Mixed canonical/project inventory; origin collision;
  nested resources; all platforms; malformed ownership; stale source/config;
  path escape; interruption; forward recovery; modified planned file; unexpected
  file in managed bundle; deterministic generation.
- **Tests**: `python -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_packaging.py scripts/tests/test_target_ownership.py scripts/tests/test_target_path_safety.py scripts/tests/test_target_determinism.py scripts/tests/test_target_drift.py scripts/tests/test_project_projection.py -q`
- **Acceptance criteria**: One generation plan and one projection plan can
  safely represent all approved skill origins for all selected platforms.

### 9. Migrate Copilot to Managed Per-Bundle Projection

- **Requirements**: R20, R21, R25
- **Files**: `.github/shared/target-mapping.json`, `scripts/cg_project_projection.py`, `scripts/link.ps1`, `scripts/link.sh`, `scripts/update.ps1`, `scripts/update.sh`, `scripts/unlink.ps1`, `scripts/unlink.sh`, `scripts/helpers.ps1`, `scripts/tests/test_target_mapping.py`, `scripts/tests/test_copilot_skill_projection.py`, `scripts/tests/test_project_projection.py`, `scripts/tests/test_link_projection_order.py`, `tests/link.Tests.ps1`, `tests/unlink.Tests.ps1`, `tests/bash-scripts.Tests.ps1`, `tests/parity.Tests.ps1`, relevant update tests`
- **Details**: Make target-mapping change mandatory. Add a declarative Copilot
  skill-only projection mode such as `projectedCategories: ["skills"]`, with
  `.github/skills` as its managed project root. Keep Copilot prompts, agents,
  instructions, and shared units on their existing install topology and exclude
  them from the skill projection plan.
- **Details**: Replace the whole `.github/skills` canonical link with a real
  project parent. Publish each selected canonical or project bundle as
  checksum-owned files. Preserve unrelated user-owned skill directories and
  reject destination collisions without partial migration.
- **Details**: Add an idempotent migration path for existing linked Copilot
  skill roots. Verify ownership before unlinking a managed junction. Do not
  remove a real directory or user-owned link. Recover interruption without
  losing the prior valid linked or projected state.
- **Details**: Keep prompts, agents, and other Copilot install units unchanged
  and prove that none enter the bundle projection. Link, update, and unlink on
  Windows and POSIX remain wrappers around focused Python runtime APIs rather
  than lifecycle engines. Cover `source_root == project_root` explicitly.
- **Test Scenarios**: Existing managed junction; real user directory; mixed
  user and managed bundles; collision; modified managed file; Copilot-only
  selection; all-platform selection; interrupted migration; repeated link;
  update after source revision; unlink owned-only behavior; no projected prompt,
  agent, instruction, or shared file; Windows/POSIX parity.
- **Tests**: `python -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_copilot_skill_projection.py scripts/tests/test_project_projection.py scripts/tests/test_link_projection_order.py -q`; focused `link`, `unlink`, `bash-scripts`, and `parity` Pester files through the execution subagent.
- **Acceptance criteria**: Copilot loads the same approved project skills as
  other hosts, and migration cannot overwrite or delete unrelated user content.

## Phase 4: Transaction and Secure Project Lifecycle

### 10. Implement the Common Plan/Apply Transaction

- **Requirements**: R3, R4, R5, R21, R25
- **Files**: `scripts/skill_management/planning.py`, `scripts/skill_management/locking.py`, `scripts/skill_management/context.py`, `scripts/secure_fs.py`, `scripts/skill_management/contracts.py`, `scripts/tests/test_skill_management_planning.py`, `scripts/tests/test_skill_management_locking.py`
- **Details**: Store ignored plan records at
  `.compound-gpid/skill-plans/<digest>.json`. Recompute and compare all bound
  inputs at apply. Plan record age is not trusted as a substitute for state
  validation. Reject replay after successful apply.
- **Details**: Acquire an exclusive project lifecycle lock at
  `.compound-gpid/skill-transaction.lock` before apply revalidation and hold it
  through final verification. Use a held-handle advisory lock: POSIX uses
  `fcntl.flock` and Windows uses `msvcrt.locking` or the equivalent Win32
  byte-range primitive. Validate the lock path and ancestors with no-follow and
  reparse-point checks before opening, require a regular file, and hold the file
  handle for the full critical section. Lock-file metadata is diagnostic only;
  process death releases the OS lock, and a stale file without a held lock does
  not block acquisition. Use an injectable monotonic acquisition timeout and do
  not delete/recreate the lock file as an ownership signal. Recovery acquires
  the same lock before reading a journal, so only one writer or recovery process
  can proceed. Store durable journals under
  `.compound-gpid/skill-transactions/<transaction-id>.json`. The journal records
  schema, request/plan digest, expected old/new bytes for each action, ordered
  action status, roots, and recovery state.
- **Details**: Stage and validate the complete desired state. Fsync or otherwise
  durably publish a `prepared` journal before changing live paths. The commit
  point is the durable transition to `publishing` immediately before the first
  live write. Publish in this order: source bundles and provenance, registries,
  strict config, active manifest, canonical generated targets, then each host
  projection and ownership record. Verify exact desired state, mark `committed`,
  then clean staging. Hosts may observe mixed state while `publishing`; no
  success is reported until convergence.
- **Details**: Failure before `publishing` discards staging and leaves live state
  unchanged. After `publishing`, recovery proceeds forward under the lock from
  journaled expected bytes. If a non-lifecycle writer changed any pending or
  applied path, recovery preserves those bytes, remains blocked with the journal,
  and gives exact remediation. Do not claim cross-root atomic visibility or use
  broad rollback after publication.
- **Details**: Require explicit approver and immutable review reference as audit
  metadata for plugin vendoring, canonical registry mutation, deprecation,
  removal, and emergency grace exceptions. Record user apply for project import
  and activation. Do not describe these fields as proof of human identity.
- **Test Scenarios**: Happy plan/apply; no-op; changed argument; changed file;
  wrong role; wrong digest; replay; concurrent writer; staged validation fail;
  crash before/after commit point and at every publish boundary; serialized
  lifecycle writer; subprocess crash and automatic OS-lock release; stale lock
  file; acquisition timeout; symlink/junction/reparse substitution; concurrent
  recovery; forward recovery; concurrent non-lifecycle writer before and after a
  planned path; invalid journal; redacted stored plan.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_locking.py scripts/tests/test_skill_management_planning.py -q`
- **Acceptance criteria**: No operation implements direct writes. Apply is
  serialized, crash-consistent, never reports partial success, converges forward
  to one verified desired state when expected bytes still match, and blocks
  without clobbering concurrent non-lifecycle changes otherwise.

### 11. Harden Admission and Implement Project Import

- **Requirements**: R8, R11, R12, R17, R21, R25
- **Files**: `scripts/skill_management/services/admission.py`, `scripts/skill_management/services/bundles.py`, `scripts/skill_management/providers/github.py`, `scripts/cg_import_skill.py`, `scripts/cg_vendor_policy.py`, `.github/shared/vendor-policy.json`, `.github/skills/cg-skill-management/workflows/import.md`, `.github/shared/skill-management/contracts/import-v1.schema.json`, `.github/shared/skill-management/operations/import.json`, `scripts/skill_management/operations/import_skill.py`, `docs/skills/management/commands/import.md`, `scripts/tests/test_import_skill.py`, `scripts/tests/test_skill_management_github_provider.py`, `scripts/tests/test_skill_management_security.py`, `scripts/tests/test_skill_management_project_lifecycle.py`
- **Details**: Separate source-spec parsing, fetch, extraction, admission,
  redacted evidence, and lifecycle registration. Confine quarantine under the
  project; create it without cleanup/mkdir race windows; validate archive members
  before extraction. In the first release, accept only normalized public
  `https://github.com/<owner>/<repo>` origins. Resolve the supplied full commit
  SHA through bounded GitHub HTTPS API calls without clone, checkout, archive,
  submodules, redirects, hooks, or LFS.
- **Details**: Traverse the selected path through nonrecursive Git tree objects.
  Cap response metadata bytes, tree depth, entry count, and total declared blob
  size before requesting any blob. Reject truncated trees, missing size metadata,
  type changes, submodules, or unsupported API behavior. Fetch only selected
  blobs as bounded streams, enforce HTTP and decoded per-file/total limits, and
  verify each byte stream against the expected Git blob object ID. Reject a
  provider when bounded tree and blob behavior cannot be established. Use local
  HTTP fixtures; tests do not depend on live GitHub.
- **Details**: Reject symlinks, junctions, reparse escapes, hard links, devices,
  executable mode bits, unsafe extensions, invalid YAML/frontmatter, broken
  bundle references, license failures, secrets, and injection findings according
  to strict policy. Reject tabular/statistical/database/archive/environment and
  credential-bearing formats, including `.csv`, `.dta`, `.sav`, `.rds`,
  `.parquet`, `.feather`, `.db`, and `.sqlite`. Opaque resources require a
  declared approved non-data class. Never execute imported content.
- **Details**: Project import may approve one normalized credential-free public
  GitHub HTTPS origin outside the plugin repository allowlist. Plugin scope remains
  allowlist-only. Both scopes use the same non-overridable canonical security
  ceilings. Bind project plan to exact origin, path,
  full SHA, candidate digest, policy digest, and review evidence. Apply writes an
  inactive project bundle, project record, and append-only provenance, then
  regenerates and verifies runtime state through the common transaction.
- **Test Scenarios**: All documented attacks and limits; invalid policy schema;
  deterministic redacted evidence; exact source mismatch; quarantine escape;
  project/plugin authority confusion; unsupported provider; oversized metadata,
  tree, entry set, declared total, HTTP body, decoded blob, and total stream;
  truncated tree; Git object mismatch; outside-repository path; outside-allowlist
  project success and plugin rejection; prohibited data file; undeclared opaque
  resource; collision; modified planned destination; extra managed-bundle file;
  failed exact runtime verification; successful inactive project import.
- **Tests**: `python -m pytest scripts/tests/test_import_skill.py scripts/tests/test_skill_management_github_provider.py scripts/tests/test_skill_management_security.py scripts/tests/test_skill_management_project_lifecycle.py -q`
- **Acceptance criteria**: Project import cannot alter canonical assets and does
  not make content active before separate approval.

### 12. Implement Activation and Deactivation

- **Requirements**: R5, R7, R14, R19, R20, R21
- **Files**: `.github/skills/cg-skill-management/workflows/activate.md`, `.github/skills/cg-skill-management/workflows/deactivate.md`, `.github/shared/skill-management/contracts/activate-v1.schema.json`, `.github/shared/skill-management/contracts/deactivate-v1.schema.json`, `.github/shared/skill-management/operations/activate.json`, `.github/shared/skill-management/operations/deactivate.json`, `scripts/skill_management/operations/activate.py`, `scripts/skill_management/operations/deactivate.py`, `scripts/skill_management/services/runtime.py`, `scripts/skill_management/services/config_editor.py`, `docs/skills/management/commands/activate.md`, `docs/skills/management/commands/deactivate.md`, `scripts/tests/test_strict_config.py`, `scripts/tests/test_skill_management_config_editor.py`, `scripts/tests/test_skill_management_project_lifecycle.py`, `scripts/tests/test_project_manifest.py`, `scripts/tests/test_project_projection.py`
- **Details**: Implement a source-span config edit planner that changes only the
  top-level frontmatter `capabilities:` inline-list value or inserts that field
  before the closing frontmatter delimiter. Preserve every other byte, comments,
  quoting, field order, body content, and original CRLF/LF style. Duplicate or
  block-style capability fields are hard errors. Bind the exact prior file digest
  and publish through `secure_fs.ExpectedFileState`. Activation adds one
  explicit capability only when valid. Deactivation removes only explicit
  selection and blocks when a selector or dependency still requires it.
- **Details**: Apply config, active manifest, generated targets if applicable,
  and project projections through the common transaction. Verify every selected
  platform before success. A deprecated skill cannot be newly activated.
- **Test Scenarios**: Activate inactive project skill; already active no-op;
  deactivate explicit; selector-derived block; dependency-required block;
  malformed/duplicate config; absent field; inline comments; advisory blocks;
  quoted values; CRLF/LF; byte-identical no-op; concurrent config modification;
  stale plan; projection collision; deprecated activation; only one of two
  project bundles selected; all-platform exact parity.
- **Tests**: `python -m pytest scripts/tests/test_strict_config.py scripts/tests/test_skill_management_config_editor.py scripts/tests/test_skill_management_project_lifecycle.py scripts/tests/test_project_manifest.py scripts/tests/test_project_projection.py -q`
- **Acceptance criteria**: Capability selection changes are explicit,
  reviewable, reversible, and cannot bypass strict resolver semantics.

## Phase 5: Maintainer Creation, Vendoring, and Update

### 13. Implement Permanent Skill Creation

- **Requirements**: R3, R5, R8, R10, R12, R17, R18, R21
- **Files**: `.github/skills/cg-skill-management/workflows/create.md`, `.github/shared/skill-management/contracts/create-v1.schema.json`, `.github/shared/skill-management/operations/create.json`, `scripts/skill_management/operations/create.py`, `scripts/skill_management/services/bundles.py`, `scripts/skill_management/services/registry.py`, focused template resources under `.github/skills/cg-skill-management/`, `docs/skills/management/commands/create.md`, `scripts/tests/test_skill_management_create.py`
- **Details**: Require permanent scope, maintainer role, identifier, quoted
  ASCII-safe description, owner module, capability assignment or complete new
  capability metadata, suites, platforms, activation cost, triggers, selectors,
  approver, and immutable review reference as audit metadata. Do not infer owner
  from prefix. Existing capability assignment is accepted as initially inactive
  only when that capability is `explicit-only` and unselected in the current
  active manifest; otherwise reject it and require a new inactive explicit-only
  capability. Do not claim global inactivity for a skill added to an already
  active capability.
- **Details**: Scaffold only requested focused files. Validate frontmatter with
  the same parser used at runtime, inventory the complete bundle, check local
  links, detect portable collisions, enforce the non-data committed-resource
  policy, plan registry changes, derive catalog metadata, generate all targets,
  and verify parity before publication.
- **Test Scenarios**: Minimal skill; each optional resource type; invalid name;
  unquoted/non-ASCII description; prohibited data file; declared/undeclared
  opaque non-data resource; owner mismatch; new explicit-only capability;
  unselected/active existing capability; missing approver/review reference;
  collision; broken reference; target failure; successful inactive canonical
  skill.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_create.py -q`
- **Acceptance criteria**: One approved apply creates a complete, owned,
  discoverable, inactive, and cross-platform permanent skill without manual
  registry repair.

### 14. Implement Plugin Vendoring

- **Requirements**: R3, R5, R8, R11, R12, R17, R21
- **Files**: `.github/skills/cg-skill-management/workflows/import.md`, `.github/shared/skill-management/contracts/import-v1.schema.json`, `scripts/skill_management/operations/import_skill.py`, `scripts/skill_management/services/admission.py`, `scripts/skill_management/services/registry.py`, `scripts/skill_management/services/provenance.py`, `scripts/cg_import_skill.py`, `docs/skills/management/commands/import.md`, `scripts/tests/test_skill_management_vendor.py`, `scripts/tests/test_import_skill.py`
- **Details**: Reuse the exact project admission pipeline. Plugin scope adds
  canonical maintainer write context, approver and immutable review reference as
  audit metadata, plugin repository allowlist, explicit owner and
  capability registration, canonical provenance, target generation, and release
  checks. Project approval evidence cannot be reused as plugin authority unless
  a new plugin plan binds it.
- **Details**: Replace direct `register_vendor_skill()` copy/JSON mutation with
  common planned actions. Keep legacy function entry only as an internal shim
  until final migration, then remove or make private if no callers remain.
- **Test Scenarios**: Consumer attempts plugin scope; spoofed checkout; dirty
  unrelated files; changed touched files; missing approval; project review reused
  without plugin plan; owner/capability failure; target failure; successful
  vendoring with full provenance.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_vendor.py scripts/tests/test_import_skill.py -q`
- **Acceptance criteria**: Vendoring cannot produce an unowned canonical skill
  and cannot publish partial canonical or generated state.

### 15. Implement Imported-Skill Update and Provenance History

- **Requirements**: R5, R11, R13, R17, R21
- **Files**: `.github/skills/cg-skill-management/workflows/update.md`, `.github/shared/skill-management/contracts/update-v1.schema.json`, `.github/shared/skill-management/operations/update.json`, `scripts/skill_management/operations/update.py`, `scripts/skill_management/services/admission.py`, `scripts/skill_management/services/provenance.py`, `docs/skills/management/commands/update.md`, `scripts/tests/test_skill_management_update.py`
- **Details**: Permit update only for project or plugin skills with valid pinned
  upstream provenance. Require explicit `--to <full-sha>`. Fetch and admit the
  candidate through quarantine, compare normalized atomic inventories, produce a
  deterministic redacted diff, and bind approval to old/new digests and policy.
- **Details**: Preserve append-only source, reviewer, approval, policy, diff, and
  content history. Keep origin scope and immutable identifier. Re-run ownership,
  capability, reference, manifest, target, and projection verification.
- **Test Scenarios**: Local-created/no upstream; same SHA no-op; short SHA;
  changed path; policy change; secret in new version; removed resource; active
  project update; active plugin update; failed projection; complete history.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_update.py -q`
- **Acceptance criteria**: Every updated byte is attributable to one approved
  immutable source transition. Apply acknowledges possible mixed host visibility
  during publication, reports no success before exact convergence, and leaves a
  recoverable journal after interruption.

## Phase 6: Audit, Deprecation, and Removal

### 16. Build Complete Validation, Audit, and Reference Services

- **Requirements**: R4, R8, R13, R15, R16, R17, R19, R24
- **Files**: `scripts/skill_management/services/references.py`, `scripts/skill_management/services/provenance.py`, `scripts/skill_management/operations/validate.py`, `.github/skills/cg-skill-management/workflows/audit.md`, `.github/shared/skill-management/contracts/audit-v1.schema.json`, `.github/shared/skill-management/operations/audit.json`, `scripts/skill_management/operations/audit.py`, `docs/skills/management/commands/audit.md`, `scripts/cg_validate_modules.py`, `scripts/cg_skill_catalog.py`, `roadmap.json` as read-only input, `compound-gpid.context.md`, active root adapters and installer text, `docs/skills/importing.md`, `scripts/tests/test_skill_management_audit.py`, `scripts/tests/test_module_registry.py`
- **Details**: Scan command, agent, instruction, documentation, registry,
  config, manifest, project registry, operation workflow, contract, and all skill
  bundle resources. Strip fenced examples only where the existing reference
  contract requires it; distinguish live, migration, and historical references.
- **Details**: Extend validation to provenance history, selectors, lifecycle,
  project overlay, generated target parity, active manifest freshness, projection
  containment, and operation completeness. First-release audit filters are
  `--provenance` and `--references`. Remove generic `--updates` and any mutable
  remote lookup. Exact immutable candidate comparison exists only in
  `/cg-skill update <id> --to <full-sha>`.
- **Details**: Include active roadmap fields, `compound-gpid.context.md`, root
  adapters, installers, existing skill-management pages, generated active
  targets, and runtime config in old-name/reference classes. Roadmap changes are
  dispatched through `@cg-roadmap`, never written directly by an operation.
- **Details**: Make leak detection effective and source-neutral. Findings use
  stable codes, severity, paths, messages, and exact remediation in human and
  JSON output.
- **Test Scenarios**: Each reference class; fenced example; historical
  exemption; stale target; missing provenance; invalid selector; generic update
  flag rejection; immutable candidate handled by update; roadmap/context/adapter
  references; deterministic finding order; one/all validation.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_audit.py scripts/tests/test_module_registry.py scripts/tests/test_skill_catalog.py scripts/tests/test_skill_management_completeness.py -q`
- **Acceptance criteria**: Destructive lifecycle operations consume one complete
  reference and validity report, and automation can rely on stable JSON codes.

### 17. Implement Deprecation and Reference-Safe Removal

- **Requirements**: R3, R5, R15, R16, R21, R25
- **Files**: `.github/skills/cg-skill-management/workflows/deprecate.md`, `.github/skills/cg-skill-management/workflows/remove.md`, `.github/shared/skill-management/contracts/deprecate-v1.schema.json`, `.github/shared/skill-management/contracts/remove-v1.schema.json`, `.github/shared/skill-management/contracts/migration-v1.schema.json`, `.github/shared/skill-management/contracts/release-attestation-v1.schema.json`, `.github/shared/skill-management/release-attestations/`, `.github/shared/skill-management/operations/deprecate.json`, `.github/shared/skill-management/operations/remove.json`, `scripts/skill_management/operations/deprecate.py`, `scripts/skill_management/operations/remove.py`, `scripts/skill_management/services/references.py`, `scripts/skill_management/services/provenance.py`, `scripts/skill_management/services/release_attestation.py`, `docs/skills/management/commands/deprecate.md`, `docs/skills/management/commands/remove.md`, `scripts/tests/test_skill_management_release_attestation.py`, `scripts/tests/test_skill_management_removal.py`
- **Details**: Deprecation requires a valid nondeprecated successor, records the
  scope-specific grace anchor, updates discovery metadata, blocks new activation,
  and warns for active migration. Reject self-successors, successor cycles,
  cross-origin successors, removed successors, and identifier reuse.
- **Details**: Deprecation writes an immutable `deprecatedRecordDigest`; audit
  remains read-only and never finalizes state. During removal planning, derive
  the earliest future release attestation that names the skill's exact
  deprecation-record digest. The separate attestation records schema version,
  release version, full tag-ref object SHA, peeled commit SHA, release payload
  SHA-256, and covered deprecation-record digests. Verify the current local and
  remote tag object/peeled commit, tagged tree record, and immutable payload bytes
  against the attestation. A moved, replaced, deleted, lightweight-versus-
  annotated changed, or mismatched tag blocks removal. Require a later attested
  published descendant release that still contains the record and skill. Keep
  historical release payload schemas unchanged.
  For project skills, derive the earliest project commit containing the exact
  record and require a later descendant project revision. If no immutable anchor
  can be derived, removal is blocked. A non-Git project requires an explicit
  project-specific grace exception. The ban on mutable branches/tags applies to
  imported source identity, not read-only validation of immutable release tags.
- **Details**: Define versioned migration records with exact source path,
  expected digest, replacement, reviewer, and immutable approval reference.
  Stage migration edits in the same lifecycle transaction and rescan the staged
  final state. Removal requires zero live references after edits, no manifest or
  projection requirement, and owned-only deletion. Emergency grace exceptions
  cannot bypass inactive state, zero references, ownership, modified-file,
  successor, or tombstone checks.
- **Details**: Apply removes source and checksum-owned generated/projection bytes,
  updates registries/manifests/catalog, preserves provenance/tombstone, and
  converges all targets through the lifecycle journal. A modified destination
  blocks removal rather than being deleted.
- **Test Scenarios**: Active skill; missing successor; successor deprecated;
  self-successor; successor cycle; cross-origin successor; exact record digest;
  plugin tag-object/commit/payload attestation, moved/replaced tag, tag ancestry,
  and later-release grace without release-payload mutation; project containing/
  descendant revision and non-Git
  exception; each live reference class; valid and stale migration digest;
  staged migration rescan; modified projection; user-owned bundle; emergency
  exception limits; successful plugin/project removal; attempted ID reuse.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_release_attestation.py scripts/tests/test_skill_management_removal.py -q`
- **Acceptance criteria**: No identifier or byte can disappear without complete
  reviewed evidence, and removed IDs remain reserved tombstones.

## Phase 7: Migration, Documentation, and Release

### 18. Complete Unlinked Documentation Candidates and Executable Examples

- **Requirements**: R2, R23, R24
- **Files**: `docs/skills/management/index.md`, `docs/skills/management/lifecycle.md`, `docs/skills/management/commands/<operation>.md`, `docs/skills/management/maintainers/*.md`, `docs/skills/management/consumers/*.md`, `docs/skills/management/security.md`, `docs/skills/management/migration.md`, `scripts/tests/test_skill_management_completeness.py`, documentation candidate tests`
- **Details**: Keep overview, lifecycle, operation, consumer, maintainer,
  security, and migration concerns separate. Each operation descriptor is the
  source of required page identity and executable grammar. Test help, examples,
  roles, result codes, lifecycle effects, and links against implementation.
- **Details**: Keep these candidate pages unlinked from public navigation and do
  not replace active old-command documentation before the pre-removal gate.
  Validate their internal links, executable examples, and descriptor parity in
  isolation. Step 19 publishes navigation and updates active reference,
  configuration, installation, catalog, and troubleshooting pages in the staged
  public changeset.
- **Test Scenarios**: Missing page; wrong option; stale example; orphan page;
  duplicate navigation ID; broken internal link; missing H1/title/description;
  catalog count; active/historical old-name handling.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_completeness.py -q` plus candidate-page link/example tests that do not require public navigation.
- **Acceptance criteria**: Each audience can follow one focused lifecycle path,
  and docs cannot pass with an undocumented or mismatched operation.

### 19. Pass the Pre-Removal Gate and Stage the Public Migration

- **Requirements**: R1, R22, R27
- **Files**: `scripts/cg_pr_preflight.py`, `.github/workflows/tests.yml`, `.github/prompts/cg-release.prompt.md`, add `.github/prompts/cg-skill.prompt.md`, add `bin/cg-skill`, add `bin/cg-skill.cmd`, update `install.ps1` and `scripts/install.sh`, add public capability record and `suite-cg` dependency in `.github/shared/module-registry.json`, remove `.github/prompts/cg-find-skill.prompt.md`, remove `.github/prompts/cg-import-skill.prompt.md`, remove `bin/cg-find-skill`, remove `bin/cg-find-skill.cmd`, update `.github/shared/context-loading.contract.md`, `scripts/cg_projection_benchmark.py`, `compound-gpid.context.md`, active root adapters, installer text, `docs/navigation.json`, `docs/reference.md`, `docs/reference/commands.md`, `docs/skills/index.md`, skill category pages, `docs/skills/importing.md`, `docs/configuration.md`, `docs/configuration/index.md`, `docs/installation.md`, `docs/troubleshooting.md`, `docs/context-files.md`, `docs/modular-guide.md`, `docs/development/index.md`, roadmap fields through `@cg-roadmap`, generated `.claude/`, `.agents/`, `.opencode/`, `.kilo/` trees through generator only, prompt-count/wrapper/parity tests, `.cg-docs/cost/skill-loading-baseline.*` through its generator`
- **Details**: Before the pre-removal run, add every current and new
  skill-management test to `NATIVE_PYTEST_FILES`, keep module validation after
  pytest, replace the release prompt's duplicate test list with authoritative
  preflight, add Linux to the native matrix, and add the Python 3.8 compatibility
  job. A completeness test compares active descriptors, phase evidence commands,
  `NATIVE_PYTEST_FILES`, and CI registration.
- **Details**: While old commands remain active, run a full pre-removal
  replacement gate: all Steps 1-18 evidence, full native preflight, full safe
  Pester, docs checks, module checks, and cross-platform CI. Do not start public
  registration or removal until that gate passes and is recorded.
- **Details**: In one staged public changeset, add the public prompt, POSIX/CMD
  wrappers, installer registration, skill-management capability record, and
  `suite-cg` dependency while removing old prompts/wrappers and updating all
  active references. The CMD launcher uses guarded Python detection. Regenerate
  native commands and ownership manifests so old generated commands are removed
  as owned stale files and `cg-skill.md` is present.
- **Details**: Update capability triggers, routing remediation, benchmarks,
  installation, configuration, and migration text. Permit old names only in the
  migration page and immutable historical `.cg-docs` and release payloads. The
  old-reference test reports scanned roots and exemption classes. Dispatch
  roadmap text changes through `@cg-roadmap`; do not rewrite historical knowledge
  artifacts.
- **Test Scenarios**: Active old prompt; orphan generated old command; stale
  ownership manifest; old trigger; old wrapper; migration page exemption;
  historical artifact exemption; public launcher installation; skill-management
  suite closure; prompt count; regenerated baseline.
- **Tests**: `python -m pytest scripts/tests/test_skill_management_migration.py scripts/tests/test_target_drift.py scripts/tests/test_target_closure.py -q`; focused `model-assignments`, `install`, `bash-scripts`, and `parity` Pester runs through the execution subagent.
- **Acceptance criteria**: The pre-removal gate passed with old commands intact,
  and one staged changeset now exposes only `/cg-skill` in the candidate tree
  while preserving migration and historical evidence.

### 20. Pass the Final-Tree Gate and Integrate Release Evidence

- **Requirements**: R20, R23, R24, R25, R27
- **Files**: `create-release.ps1`, `scripts/cg_release_attestation.py`, `.github/shared/skill-management/contracts/release-attestation-v1.schema.json`, `.github/shared/skill-management/release-attestations/`, `scripts/tests/test_skill_management_release_attestation.py`, `tests/Run-Tests.ps1` only if registration changes, release documentation, generated targets, `.cg-docs/work-reports/2026-08-28-scalable-skill-management-suite.md` as execution evidence`
- **Details**: Run focused Python, Node, and Pester gates after their steps. At
  final-tree verification after Step 19 changes, rerun committed full native
  preflight, canonical Pester
  runner through the execution subagent, docs checks, module checks, target
  dry-run/drift, and cross-platform CI. Do not publish if this second full gate
  fails; the prior released tree retains the old commands. Record both
  pre-removal and final-tree evidence in the execution report.
- **Details**: Add Linux to the native CI matrix and add a Python 3.8
  compatibility job for contracts, planning, registry, admission, generation,
  and projection tests. Require the successful CI run URL and per-matrix result
  as final evidence. Local Windows results do not satisfy cross-platform support.
- **Details**: Add a post-release attestation command for future releases. After
  the remote tag and immutable release payload exist, it writes a deterministic
  versioned attestation containing tag type, tag-ref object SHA, peeled commit
  SHA, release payload SHA-256, and covered deprecation-record digests. Releases
  that cover deprecations require an annotated tag. The attestation is committed
  through the normal reviewed workflow after release; removal remains blocked
  until it exists. The command verifies the remote and local tag identities and
  never rewrites historical release payloads.
- **Details**: Update structural schema version and migration checks if project
  store or Copilot topology requires consumer migration. Do not read release
  credentials before isolated preflight succeeds.
- **Test Scenarios**: Unified test omitted from preflight; release prompt drift;
  filtered Pester run presented as full; generated target stale; docs gate fail;
  Linux/Python 3.8 matrix absence or failure; platform-specific failure;
  structural migration absent; lightweight deprecation tag; moved tag;
  payload/record digest mismatch; pre-removal pass followed by final-tree failure.
- **Tests**: Commands in Testing Strategy and Completion Contract.
- **Acceptance criteria**: Separate recorded pre-removal and final-tree gates plus
  successful Windows/macOS/Linux and Python 3.8 CI prove the complete command,
  security controls, docs, ownership, manifests, and projections before release.

## Requirement Traceability

| Requirement | Steps |
| --- | --- |
| R1 | 3, 5, 19 |
| R2 | 1, 3, 5, 6, 11-18 |
| R3 | 3, 10, 13, 14, 17 |
| R4 | 1, 3, 5, 6, 10, 16 |
| R5 | 1, 10-15, 17 |
| R6 | 1, 7, 11 |
| R7 | 1, 7, 12 |
| R8 | 4, 7, 8, 11, 13, 14, 16 |
| R9 | 4, 5 |
| R10 | 13 |
| R11 | 11, 14, 15 |
| R12 | 1, 11, 13, 14 |
| R13 | 15, 16 |
| R14 | 12 |
| R15 | 1, 16, 17 |
| R16 | 4, 6, 16, 17 |
| R17 | 4, 11, 13-16 |
| R18 | 2, 8, 13 |
| R19 | 1, 4, 7, 8, 12, 16 |
| R20 | 8, 9, 12, 19, 20 |
| R21 | 8-15, 17 |
| R22 | 19, 20 |
| R23 | 5, 18, 20 |
| R24 | 6, 16, 18, 20 |
| R25 | 2-3, 7-11, 17, 20 |
| R26 | 7 and plan boundaries |
| R27 | 3, 19, 20 |

## Testing Strategy

### Test Layers

- Contract tests validate schemas, operation descriptors, deterministic
  serialization, findings, and plan digests.
- Unit tests isolate every operation and service with minimal source/project
  fixtures and resolver-built manifests.
- Security tests use malicious archives, paths, modes, links, policy values,
  content limits, role spoofing, plan replay, and concurrent writes.
- Integration tests exercise source -> registry -> manifest -> generation ->
  projection -> verification for canonical and project skills.
- Migration tests cover existing Copilot links, old command removal, generated
  ownership cleanup, schema changes, and historical exemptions.
- Documentation tests compare descriptor grammar and executable help with every
  operation page and public navigation.
- Release tests prove that authoritative preflight includes all relevant Python,
  Node, module, target, and Pester gates.

### Focused Python and Node Commands

```powershell
python -m pytest scripts/tests/test_skill_management_contracts.py -q
python -m pytest scripts/tests/test_skill_management_dispatch.py -q
python -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_packaging.py scripts/tests/test_target_drift.py -q
python -m pytest scripts/tests/test_skill_management_read.py scripts/tests/test_skill_catalog.py -q
python -m pytest scripts/tests/test_project_skill_registry.py scripts/tests/test_project_manifest.py -q
python -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_copilot_skill_projection.py scripts/tests/test_project_projection.py scripts/tests/test_link_projection_order.py -q
python -m pytest scripts/tests/test_skill_management_planning.py -q
python -m pytest scripts/tests/test_import_skill.py scripts/tests/test_skill_management_github_provider.py scripts/tests/test_skill_management_security.py -q
python -m pytest scripts/tests/test_skill_management_config_editor.py scripts/tests/test_skill_management_project_lifecycle.py -q
python -m pytest scripts/tests/test_skill_management_create.py scripts/tests/test_skill_management_vendor.py -q
python -m pytest scripts/tests/test_skill_management_update.py -q
python -m pytest scripts/tests/test_skill_management_audit.py scripts/tests/test_skill_management_removal.py -q
python -m pytest scripts/tests/test_skill_management_completeness.py -q
python -m pytest scripts/tests/test_skill_management_migration.py scripts/tests/test_target_closure.py -q
python scripts/cg_validate_modules.py --check-ownership --check-dependencies --check-cross-suite
python scripts/cg_generate_targets.py --all --dry-run
node scripts/rebuild-docs.js --check
node scripts/check-docs-site.js
```

### Pester Safety

Load `cg-skill-pester-safety` before any Pester execution. Run Pester only
through an execution subagent and the repository safe runner. Focused runs use
the safe runner's supported file selector. The final run is:

```text
In the repository root, run:
. tests\Run-Tests.ps1
Do not add flags or a pipeline.
Then read tests\last-run.json and return passed, failedCount, failures, and filteredFiles.
```

Final evidence is valid only when `filteredFiles` is `null`.

Focused phase evidence also uses the execution subagent and safe runner. The
expected `filteredFiles` value must equal the requested file for `link`,
`unlink`, `bash-scripts`, `parity`, `model-assignments`, `install`,
`docs-automation`, and `create-release`; a different or additional filter is not
accepted as that phase's evidence.

### Final Native Gate

```powershell
python scripts/cg_pr_preflight.py --phase committed --full-gate --run-native-target
```

The implementation must add current catalog/import and all new skill-management
tests to this authoritative preflight before using it as completion evidence.

## Documentation Checklist

- [ ] Add management overview and lifecycle model.
- [ ] Add one command page per operation.
- [ ] Add consumer discovery, project import, activation, availability, and remediation guides.
- [ ] Add maintainer creation, vendoring, registry/capability, update, deprecation/removal, and release guides.
- [ ] Add one security page for quarantine, approval, provenance, supply chain, and destructive controls.
- [ ] Add immediate-replacement migration mapping for both old commands.
- [ ] Update public navigation and command reference generation.
- [ ] Update skill catalog/category text and remove stale bundle-packaging claims.
- [ ] Update configuration, installation, context, modular, development, and troubleshooting pages.
- [ ] Verify examples against descriptors and executable help.
- [ ] Keep historical `.cg-docs` and release payloads unchanged.
- [ ] Add documentation completeness and active-old-reference gates.

## Risks & Mitigations

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Independent host roots cannot be atomically visible as one transaction. | Hosts can observe mixed state during publication or a crash. | Serialize lifecycle writers, stage all outputs, use a durable prepared/publishing/committed journal, recover forward from expected bytes, block concurrent non-lifecycle conflicts, and never report success before exact convergence. |
| Copilot migration overwrites a real user `.github/skills` directory or loses a managed junction. | User content loss and P0 trust failure. | Detect ownership and topology first, migrate per bundle into a real parent, preserve unrelated content, block collisions, and add interruption/recovery fixtures. |
| Project overlay shadows canonical ownership or capability records. | Privilege escalation or incorrect runtime closure. | Reserved namespaces, separate digests, strict no-shadow validation, one `RegistrySnapshot`, and portable collision gates. |
| A shared project owner causes one selected capability to expose every project bundle. | Silent over-activation and context leakage. | Require explicit-only project capabilities and select bundles from the manifest's one-to-one `selectedProjectSkills` map, with two-skill isolation tests. |
| A linked global canonical source is mistaken for maintainer authority. | Consumer-triggered canonical mutation. | Require invocation/project/source roots to be the same development checkout, reject default/protected branches, test linked-source consumers, and treat approver fields only as audit metadata. |
| Refactoring catalog and manifest code changes existing active-state behavior. | Discovery or routing regression. | Characterize existing behavior first, use resolver-built fixtures, unify duplicated row logic, and keep route hard stops stricter than prospective discovery. |
| Source acquisition exhausts disk/network before bundle admission or keeps link, LFS, license, or memory gaps. | Supply-chain compromise or denial of service. | Use bounded public GitHub tree/blob API traversal, reject unsupported providers, enforce metadata and stream limits before reads, convert every rule into a negative fixture, and run adversarial security review. |
| Imported or scaffolded resources commit prohibited data files. | Charter violation and possible sensitive-data exposure. | Reject declared data-bearing formats, require an approved non-data class for opaque resources, and test project import, plugin vendor, and create paths. |
| Nested shared recursion causes output collisions or target drift. | Broken generated hosts. | Preserve relative paths, apply portable collision rules, validate ownership recursively, and require exact drift parity on every target. |
| Project skill plans or evidence leak secrets. | Credential exposure. | Store ignored redacted plan/evidence records, never embed secret values, and test serialized artifacts for redaction. |
| Full first release creates a long implementation path. | Integration drift and delayed value. | Keep seven hard internal phases, retain old public commands, keep the new CLI private, and run phase evidence continuously without exposing an incomplete product. |
| Immediate alias removal breaks active documentation or automation. | User disruption. | Complete scoped reference inventory, executable migration docs, release notes, wrapper/install updates, and active-versus-historical reference tests before removal. |
| New tests are omitted from authoritative preflight. | False release confidence. | Add an explicit completeness test for preflight registration and remove duplicate release-prompt test lists. |
| Python 3.8 or Windows path behavior regresses during refactor. | Consumer installation failure. | Remove unsupported APIs, use existing secure path helpers, add Windows reparse/long-path fixtures, and require cross-platform CI. |
| Destructive reference scan misses nested skill resources or generated active references. | Unsafe removal. | Scan all source categories and bundle resources, classify live/migration/historical references, and require migration coverage plus manifest/projection checks. |
| Release grace trusts a movable tag or is undefined for projects. | Removal occurs too early or remains blocked forever. | Pin tag-ref object SHA, peeled commit SHA, payload digest, and record digests in a reviewed attestation; verify moved tags; use descendant project revisions, digest-bound migrations, and zero-reference rescans. |
| Strict config edits damage comments or derived capability semantics. | Invalid project configuration or unexpected activation. | Use one deterministic config edit planner, show exact patch, block derived/dependency removal, and re-resolve before apply. |
| A required selected file is modified or an extra file exists in a managed bundle. | Apply can falsely report a complete projection. | Preserve user bytes but block lifecycle apply; verify every desired path/digest, ownership entry, and exact managed-bundle inventory. |
| Public registration or old-command removal occurs before a complete replacement pass. | Users receive an incomplete or commandless release. | Run a full pre-removal gate with old commands intact, stage registration/removal together, run a second full final-tree gate, and publish only after both pass. |

## Out of Scope

- Public marketplace or remote repository discovery.
- Runtime loading from global, external, or network locations.
- Mutable branches, tags, or short SHAs as imported source identity; redirects,
  submodules, and LFS content. Read-only validation of immutable release tags is
  allowed only for deprecation grace evidence.
- Generic `audit --updates` or any mutable remote update discovery. Exact
  candidate comparison is only `update <id> --to <full-sha>`.
- Execution of imported content during admission, generation, or validation.
- Project-authored skills without pinned import provenance. This is roadmap item
  `project-authored-skills`.
- Private/authenticated repository acquisition and external Git providers other
  than bounded public GitHub HTTPS API traversal in the first release.
- A project-level vendor-policy overlay.
- Shared project capabilities in the first release; each project skill gets one
  reserved capability.
- In-place identifier rename or identifier reuse after removal.
- Automatic approval, activation, vendoring, registry mutation, or deletion.
- Deletion or replacement of user-owned projected content.
- A generic declarative workflow engine.
- Full JSON Schema support or an undeclared schema-validator dependency.
- Rewriting historical knowledge artifacts or release payloads.
- Partial public replacement before the complete final gate.

## Completion Contract

### Outcome

Compound GPID provides one role-gated `/cg-skill` command with explicit operation
modules, stable human and JSON contracts, secure plan/apply mutations, permanent
and project-specific skill scopes, immutable lifecycle controls, and verified
projections for Copilot, Claude Code, Codex, OpenCode, and Kilo. The old skill
commands are removed only after the complete replacement passes security,
documentation, migration, and release gates.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
| --- | --- | --- | --- | --- |
| V1 | 1 | Common request, result, plan, finding, descriptor, project-registry, and provenance contracts pass valid and invalid fixtures | `python -m pytest scripts/tests/test_skill_management_contracts.py -q` | yes |
| V2 | 1 | Nested shared contracts are recursively inventoried, path-preserved, owned, and deterministic under a selected synthetic module | `python -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_packaging.py scripts/tests/test_target_ownership.py scripts/tests/test_target_drift.py -q` | yes |
| V3 | 1 | Internal `cap-skill-management` assets have one owner and remain outside the public suite closure | `python scripts/cg_validate_modules.py --check-ownership --check-dependencies --check-cross-suite` | yes |
| V4 | 1 | The private Python dispatcher loads one validated operation, enforces write context, and contains no lifecycle business logic | `python -m pytest scripts/tests/test_skill_management_dispatch.py -q` | yes |
| V5 | 2 | `find`, `info`, `validate`, and `help` return deterministic human and JSON results | `python -m pytest scripts/tests/test_skill_management_read.py scripts/tests/test_skill_catalog.py -q` | yes |
| V6 | 2 | Missing and stale manifests permit only prospective discovery and never claim active or projected state | `python -m pytest scripts/tests/test_skill_management_read.py scripts/tests/test_skill_catalog.py -q` | yes |
| V7 | 3 | The project registry enforces reserved namespaces, exact ownership, no shadowing, confined source paths, and portable collision rules | `python -m pytest scripts/tests/test_project_skill_registry.py -q` | yes |
| V8 | 3 | Manifest resolution combines canonical and project registries with separate digests and deterministic catalog records | `python -m pytest scripts/tests/test_project_manifest.py -q` | yes |
| V9 | 3 | Exactly selected project bundles reach all five platforms with exact desired-plan verification | `python -m pytest scripts/tests/test_project_skill_registry.py scripts/tests/test_project_manifest.py scripts/tests/test_target_packaging.py scripts/tests/test_project_projection.py -q` | yes |
| V10 | 3 | Hybrid Copilot migration preserves user content, projects skills only, and has Windows/POSIX link-update-unlink parity | `python -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_copilot_skill_projection.py scripts/tests/test_project_projection.py scripts/tests/test_link_projection_order.py -q`; via execution subagent run `. tests\Run-Tests.ps1 -File link`, then `-File unlink`, `-File bash-scripts`, and `-File parity`, each with the matching `filteredFiles` value | yes |
| V11 | 4 | Held-handle locking and plan/apply reject concurrent writers/recovery, replay, changed inputs, wrong role, wrong approval, stale plans, and concurrent modifications | `python -m pytest scripts/tests/test_skill_management_locking.py scripts/tests/test_skill_management_planning.py -q` | yes |
| V12 | 4 | Bounded GitHub acquisition and admission block oversized source metadata/content, unsupported providers, traversal, link races, hard links, executables, data files, LFS, redirects, secrets, injection, and invalid licenses | `python -m pytest scripts/tests/test_import_skill.py scripts/tests/test_skill_management_github_provider.py scripts/tests/test_skill_management_security.py -q` | yes |
| V13 | 4 | Project import, byte-preserving activation/deactivation, explicit-only selection, manifest regeneration, and exact projection converge through the journal | `python -m pytest scripts/tests/test_skill_management_config_editor.py scripts/tests/test_skill_management_project_lifecycle.py -q` | yes |
| V14 | 5 | Permanent creation and plugin vendoring assign explicit ownership, inactive capability semantics, non-data resources, provenance, catalog data, and target parity | `python -m pytest scripts/tests/test_skill_management_create.py scripts/tests/test_skill_management_vendor.py -q` | yes |
| V15 | 5 | Imported-skill update requires a new full SHA, produces a deterministic redacted diff, and appends provenance without losing history | `python -m pytest scripts/tests/test_skill_management_update.py -q` | yes |
| V16 | 6 | Validation and audit cover all decided metadata, references, manifests, targets, and projections with stable severities and remediation | `python -m pytest scripts/tests/test_skill_management_audit.py -q` | yes |
| V17 | 6 | Immutable-ID deprecation and removal enforce successor, inactive state, grace, references, migration coverage, tombstones, and owned-only deletion | `python -m pytest scripts/tests/test_skill_management_removal.py -q` | yes |
| V18 | 7 | Every operation has a descriptor, workflow, handler, contract, tests, and focused documentation page | `python -m pytest scripts/tests/test_skill_management_completeness.py -q` | yes |
| V19 | 7 | Public docs, navigation, examples, command reference, catalog, configuration, installation, and troubleshooting pass site checks | `node scripts/rebuild-docs.js --check` and `node scripts/check-docs-site.js` | yes |
| V20 | 7 | Active old-name roots are clean, historical/migration exemptions are explicit, and staged public registration/removal has exact generated parity | `python -m pytest scripts/tests/test_skill_management_migration.py scripts/tests/test_target_drift.py scripts/tests/test_target_closure.py -q` | yes |
| V21 | 7 | Full pre-removal replacement gate passes while old public commands remain active | `python scripts/cg_pr_preflight.py --phase committed --full-gate --run-native-target`; `. tests\Run-Tests.ps1` via execution subagent with `filteredFiles: null`; `node scripts/rebuild-docs.js --check`; `node scripts/check-docs-site.js`; recorded CI run URL | yes |
| V22 | final | Full final-tree native preflight passes after staged public registration and old-command removal | `python scripts/cg_pr_preflight.py --phase committed --full-gate --run-native-target` | yes |
| V23 | final | Canonical Pester suite passes through the execution subagent with no filter | `. tests\Run-Tests.ps1`, then `tests/last-run.json` with `filteredFiles: null` | yes |
| V24 | final | Windows, macOS, Linux, and Python 3.8 compatibility jobs pass | Successful `.github/workflows/tests.yml` run URL and recorded matrix job results | yes |
| V25 | final | Generated trees are current and both gate results are recorded in the execution report | `python scripts/cg_generate_targets.py --all --dry-run` and `.cg-docs/work-reports/2026-08-28-scalable-skill-management-suite.md` | yes |

### Constraints

| ID | Phase | Constraint | Check |
| --- | --- | --- | --- |
| C1 | 1 | `/cg-skill` prompt and CLI remain dispatchers; operation logic stays in focused modules | Dispatcher import and structure tests |
| C2 | 1 | No new runtime dependency is added without approval; Python 3.8 remains supported | Dependency diff and compatibility tests |
| C3 | 1 | Permanent assets retain exactly one owner; management skill and contracts use `cap-skill-management` | Module validation gates |
| C4 | 2 | No global or external skill location becomes a fallback runtime source | Missing-manifest and route hard-stop tests |
| C5 | 2 | JSON keys, findings, records, paths, and human output remain deterministic | Snapshot and repeated-run byte comparisons |
| C6 | 3 | Project skills use owner `project-local`, explicit-only capability `project-skill-<id>`, and one-to-one `selectedProjectSkills` bundle selection | Two-skill isolation and project registry tests |
| C7 | 3 | Copilot uses a real `.github/skills/` parent with checksum-owned per-bundle publication and preserves unrelated user content | Copilot migration and ownership tests |
| C8 | 3 | Canonical and project records cannot shadow, replace, or weaken each other | Overlay validator tests |
| C9 | 4 | Project imports approve one exact public GitHub HTTPS repository, path, and full SHA per plan under canonical ceilings; plugin scope remains repository-allowlist-only and unsupported providers fail | Provider, admission policy, and plan binding tests |
| C10 | 4 | Planning writes no lifecycle state; import planning may write only confined quarantine and redacted evidence | Filesystem side-effect tests |
| C11 | 4 | Apply is lifecycle-writer serialized, journaled, crash-consistent, and forward-recoverable; it does not claim cross-root atomic visibility or clobber concurrent changes | Commit-point, recovery, and race tests |
| C12 | 4 | Maintainer mutation requires equal invocation/project/source roots and a nondefault nonprotected feature branch; origin and audit text cannot elevate | Linked-source consumer and role-spoofing tests |
| C13 | 5 | Every new/imported skill receives explicit ownership, capability, eligibility, provenance, atomic inventory, and approved non-data resource classification | Creation and vendoring tests |
| C14 | 6 | Skill identifiers never rename in place or become reusable after removal | Lifecycle state tests |
| C15 | 6 | Plugin grace uses cryptographically pinned release attestations and ancestry; project grace uses a later descendant revision; migration edits rescan to zero references | Attestation, moved-tag, grace, migration, and successor tests |
| C16 | 6 | Modified or user-owned projected files are never deleted | Ownership and destructive-operation tests |
| C17 | 7 | The private CLI is not publicly registered until a full pre-removal gate passes; registration/removal is staged once and followed by a second full gate | Phase ordering and migration tests |
| C18 | 7 | Historical `.cg-docs` and release payloads retain old names; active roadmap, context, adapters, installers, docs, generated trees, and code do not | Scanner-root and exemption-report test |
| C19 | final | Pester runs only through the safe runner and execution subagent | Pester safety gate |
| C20 | final | Generated platform trees are changed only by the canonical generator | Drift and ownership manifests |
| C21 | final | Generic mutable update discovery is absent; update comparison requires an exact full SHA | Grammar and audit/update tests |
| C22 | final | Every selected destination and exact managed-bundle inventory matches the desired plan before success | Modified-file and unexpected-file tests |
| C23 | final | Linux and Python 3.8 support are proven by CI artifacts | Required matrix evidence |

### Boundaries

- Allowed: canonical prompts, management skill bundle, shared contracts, module
  registry, Python services and operations, wrappers, strict config, active
  manifest, project registry/store, generated targets, projections, tests, docs,
  release gates, and required schema version updates.
- Allowed: focused refactors of current catalog, importer, vendor policy,
  manifest, projection, generator, and module validator into reusable APIs.
- Out of scope: marketplace, remote runtime fetch, mutable Git references,
  content execution, in-place rename, project-authored unprovenanced skills,
  project policy overlay, automatic approval, and user-owned deletion.
- Out of scope: changes to historical brainstorms, plans, work reports,
  solutions, Brain artifacts, or immutable release payloads.
- Out of scope: partial public replacement; internal phases can coexist with old
  commands until final release.

### Iteration Policy

1. Implement phases in order and do not advance until required phase evidence passes.
2. Fix failures within the current phase; do not weaken tests, ownership, security, or projection checks.
3. Use one reserved project owner, one explicit-only capability per project skill, and one-to-one manifest bundle selection in the first release.
4. Store ignored plan records under `.compound-gpid/skill-plans/<digest>.json`; revalidate state at apply.
5. Require explicit approver and immutable review reference as audit metadata for plugin vendoring, registry mutation, deprecation, removal, and emergency grace exceptions; do not present these strings as authorization proof.
6. Generate native target changes from `.github/`; never patch generated platform trees manually.
7. Preserve security ceilings; any relaxation is a deviation requiring user approval.
8. Keep the CLI private until the pre-removal gate; stage public registration and old-surface removal together, then run the final-tree gate.
9. Under `deviation-policy: ask`, pause before public grammar, schema dialect, storage, Copilot topology, role, approval, security, or release-scope changes.

### Blocked-Stop Conditions

- Managed Copilot projection cannot preserve unrelated user-owned content.
- A project registry record can shadow or weaken a canonical record.
- The lifecycle lock, durable commit point, expected-byte publication, exact desired-state verification, or deterministic forward recovery cannot be proven.
- Imported content requires execution, mutable source identity, an unbounded read, or a security-policy relaxation.
- A destructive operation cannot prove complete references and checksum ownership.
- Manifest, registry, provenance, target, or projection validation fails.
- A required cross-platform or security test cannot run through the approved runner.
- New public registration or old-command removal would occur before the pre-removal gate passes.
- Linux or Python 3.8 required CI evidence is unavailable or failing.
- Implementation needs an unapproved dependency, schema migration, authority expansion, or scope deviation.
- Required evidence fails after allowed recovery, or the execution report cannot be written.
