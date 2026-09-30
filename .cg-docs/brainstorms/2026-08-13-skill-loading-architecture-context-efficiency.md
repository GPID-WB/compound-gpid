---
date: 2026-08-13
title: "Manifest-driven skill loading for context efficiency"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Per-project materialized projection"
tags: [architecture, skills, context-efficiency, capabilities, manifests, platform-adapters, kilo, copilot, security, vendoring]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Manifest-Driven Skill Loading for Context Efficiency

## Context

Compound GPID currently makes every generated skill visible to Kilo through
`.kilo/skills/*/SKILL.md`. Although full skill bodies are demand-loaded, skill
names and descriptions enter ordinary session context. The completed modular
registry and `cg_context_budget.py` already calculate suite closures, but normal
`cg-link` and `cg-update` do not apply that selection to their installed runtime
trees. Further, both `suite-cg` and `suite-cr` currently declare every language
capability as a dependency, so suite filtering still ships irrelevant skills.

The installation model creates a more urgent platform problem. The current
Codex `.agents/skills` directory is linked to the global installation. Kilo
auto-discovers that compatible location in addition to `.kilo/skills`, resolves
the external Windows junction or POSIX symlink, and can fail to parse every
discovered skill. Kilo's configured `skills.paths` is additive, not an exclusion
of compatibility roots. This is a concrete correctness and context-isolation
failure, not only a token-optimization opportunity.

This design extends, rather than duplicates, the existing roadmap work:
`token-audit-context-model`, `context-budget-enforcement-design`,
`shrink-always-on-context`, `prompt-skill-split`, `stage-context-contracts`,
`token-benchmark-before-after`, `attribution-documentation`, and
`github-actions-supply-chain-hardening-pilot`.

### Prior Knowledge Applied

1. The completed modular architecture established a validated, registry-driven
   canonical source and five-platform ownership/drift guarantees. This work
   extends that data-driven generator; it does not create target-specific module
   implementations. Source: `.cg-docs/plans/2026-08-07-modular-compound-gpid.md`.
2. Kilo requires project-local Markdown sources. An external junction/symlink
   causes cascading, misleading parse errors even when agent and skill YAML is
   valid. Source: `.cg-docs/solutions/bugs/2026-08-11-windows-link-kilo-copy-directory-parse-failure.md`.
3. Kilo's historical schema-validator failure is distinct from source-path
   failures. Projection validation must preserve frontmatter, UTF-8, and
   YAML-hardening checks, while surfacing upstream parser defects separately.
   Source: `.cg-docs/solutions/bugs/2026-08-06-kilo-agent-skill-parsing-failures.md`.

## Requirements

### Outcomes and Boundaries

- Context reduction and fail-closed platform isolation are equal release gates.
- Keep `.github/` as the full, canonical, release-validated source owned by the
  modular registry. Do not apply one project's profile to global generated trees.
- Preserve the stable `/cg-*` and `/cr-*` workflow namespaces. Add action-first
  discovery and import commands named `/cg-find-skill` and `/cg-import-skill`;
  do not create commands beginning with `/cg-skill` because that namespace is
  reserved in practice for skill identifiers.
- No public marketplace, arbitrary automatic installation, remote runtime
  fetching, semantic rewrites of imported skills, shared filtered profile cache,
  or temporary session-only capability override is in scope.
- The kernel's mandatory scope stays narrow: manifest/runtime resolver, compact
  hard-stop router, and only their direct runtime assets. Language, research,
  Pester, Brain, and Git guidance are task-triggered capabilities, never an
  unconditional base closure.

### Configuration and Registry

- Suites select workflow namespaces only (`cg`, `cr`). They must not pull every
  language or domain capability by dependency declaration.
- Project configuration selects capabilities by a hybrid model:
  - `language`, `r-syntax`, `project-type`, and explicit tooling/domain settings
    derive documented baseline capabilities.
  - `capabilities:` supplies additive, validated capability ids.
  - Explicit capabilities may not remove settings-derived capabilities. To remove
    R support, for example, change the authoritative language setting.
- Move the registry to a versioned schema that separates:
  - **Mandatory dependency**: a hard lower-layer runtime prerequisite of a module;
    it participates in transitive closure and cannot be omitted.
  - **Capability eligibility**: a profile-selectable pack that may be activated
    by configuration or task routing, but is not automatically selected merely
    because a suite exists.
  - **Activation metadata**: task triggers, supported suites/platforms, source
    provenance, expected cost, and configuration selectors. Metadata describes
    eligibility; it never bypasses manifest selection.
- Define a strict versioned parser for `compound-gpid.local.md`. The legacy
  default `[cg]` applies only when `suites` is genuinely absent in a supported
  legacy schema. Empty, scalar, duplicate, malformed, or unknown values fail
  closed with an actionable correction. Missing/malformed registry or invalid
  named module/capability also fails closed.
- Resolve one active project manifest containing the validated config and
  registry versions/hashes, source revision, selected suites, derived and
  explicit capabilities, selected module closure, platform eligibility,
  generated catalog records, and expected output hashes.
- Commit `.compound-gpid/active-manifest.json`. It is a generated, reviewable
  team artifact rather than ignored local state. Reject it as stale when its
  config hash, registry hash/schema, source revision, or owned output hashes no
  longer match; direct users to `cg-link` or `cg-update` to regenerate it.

### Platform Projections

- Materialize a manifest-filtered, project-local runtime projection for every
  selected platform. The global install remains the complete source; a project
  never links a filtered profile to the shared global `.claude`, `.agents`,
  `.opencode`, or `.kilo` tree.
- Refactor the generator into a plan/apply model with distinct canonical source
  and project output roots. Resolve and validate first, generate to a secure
  staging area, validate the complete projection, then atomically publish only
  the active project. Interrupted runs preserve the last valid projection.
- `cg-link` and `cg-update` automatically resolve the manifest, produce the
  selected projection, synchronize it, and verify its ownership. They do not
  require a separate manual resolution command.
- Replace divergent PowerShell and shell copy behavior with one secure,
  cross-platform projection/synchronization implementation. It must use
  no-follow/root-anchored mutation, checksum ownership, atomic marker updates,
  checksum-gated stale deletion, and identical Windows/POSIX semantics.
- Kilo must receive real, project-local regular files for its commands, skills,
  agents, instructions, and shared files. It must not receive external junctions
  or symlinks under its runtime roots.
- Phase 0 must make Kilo+Codex coexistence safe before broader manifest work.
  Kilo auto-discovery of external `.agents/skills` and `.claude/skills` must be
  disabled through a verified process-scoped launch path using
  `KILO_DISABLE_EXTERNAL_SKILLS=1`, while `.kilo/skills` remains available and
  Codex still uses `.agents/skills`. If this cannot be applied and verified on
  the deployed Kilo version, the combined install blocks with exact remediation;
  it never silently proceeds with parser failures or inventory leakage.
- Treat `KILO_DISABLE_EXTERNAL_SKILLS` as a tested containment control, not a
  permanent platform contract. Track an upstream request for a documented,
  project-configurable compatibility-root allow/deny list.

### Skill Discovery and Routing

- Generate a static, manifest-backed `/cg-find-skill` catalog. It is queried on
  demand and never injected wholesale into normal sessions.
- Default output is compact matching records: id, purpose, capability, current
  availability, and activation cost. Support `--full` for complete records and
  filters for id/query, capability, suite, platform, availability, cost, owner,
  and provenance.
- Full catalog records contain id, purpose, owner/module, capability and suite
  eligibility, platform eligibility, activation cost, active/inactive reason,
  source path, content/source provenance, and import status. The catalog indexes
  frontmatter and registry metadata only; it does not load all skill bodies.
- The compact kernel router detects an explicitly requested but absent
  capability and stops before work. Diagnostics name the missing capability,
  the authoritative configuration field to change, and the required
  `cg-link`/`cg-update` regeneration action. It never silently falls back,
  emits a transient projection, or proceeds without the needed capability.

### Controlled External Vendoring

- `/cg-import-skill <repo>@<full-sha> <path>` accepts only an approved HTTPS
  repository identity, a verified full immutable commit SHA, and a normalized
  descendant of an approved upstream skill root. It must disable hooks,
  submodules, LFS smudging, interactive credentials, shell interpolation, and
  redirects.
- Import first stages content in quarantined, non-runtime state. Admission is
  default-deny: reject links/reparse points, hard links, executables, scripts
  regardless of mode, binaries, archives, hidden files, oversized bundles,
  Unicode-confusable or unsafe paths, LFS pointers, secrets, and instructions
  that require remote runtime fetching or network execution.
- The importer runs static security, path, license, frontmatter, reference,
  provenance, and collision checks and produces a deterministic full-file review
  diff without exposing secret contents. Only mechanical namespace/path rewrites
  may be automatic; semantic rewrites require maintainers.
- Approval is two-stage: a maintainer explicitly approves the quarantined diff
  locally, then normal pull-request review approves the trusted vendor commit.
  Approved non-executable bundles are vendored into canonical managed
  `.github/skills/` ownership and registered with source SHA, license, upstream
  path, review evidence, and local adaptation record.
- Separate managed and user skill roots. A platform mapping declares each
  managed root and verified optional user root; a normalized combined identifier
  index rejects exact, case-folded, Unicode-normalized, reserved-name,
  trailing-dot/space, and file/directory collisions before any write. User bytes
  survive rejected imports and updates. A secondary root is not enabled on a
  platform until its discovery semantics are verified.

### Validation, Migration, and Measurement

- Add idempotent migrations for the strict project-config schema, active
  manifest, existing global links/copies, and managed-directory markers. Legacy
  projects retain the documented `[cg]` suite default only through the defined
  compatibility window, then receive actionable migration errors.
- Validate named skill references, registry ownership, capability closure,
  active manifest closure, emitted catalog rows, platform routing, and generated
  ownership inventories. No inactive skill, agent, instruction, command, or
  root-adapter reference may leak into a project projection.
- Test suite-only, CR-only, mixed, capability-specific, legacy, invalid-config,
  stale-manifest, external-collision, Kilo+Codex coexistence, Windows/POSIX
  parity, emitted inventory/routing leaks, and secure interrupted publication.
- Establish and preserve the existing token/context audit as baseline. Compare
  before/after inventory, advertised metadata, ordinary-session context, and
  task success for CG-only, CR-only, mixed, and representative capability
  profiles. Do not claim success solely from heuristic token estimates.

## Approaches Considered

### Approach 1: Per-Project Materialized Projection

Keep a complete global canonical source, resolve one committed manifest per
consumer project, and materialize only its selected runtime assets under local
platform roots.

**Pros:** Enforces manifest isolation rather than adapter prose; prevents one
project's profile from changing another's; permits local regular Kilo files;
keeps configuration and emitted inventory reviewable; fits the existing
registry-driven generator model.

**Cons:** Requires a secure shared projection worker, link/update migration,
managed-copy ownership controls, and a larger cross-platform test matrix.

**Effort:** Large.

### Approach 2: Global Profile Cache With Per-Project Links

Generate profiles keyed by manifest hash in the global install and link each
project to its selected shared profile.

**Pros:** Avoids duplicating files across consumer projects and retains more
link-style update behavior.

**Cons:** Adds shared-cache lifecycle, concurrent update, cleanup, and
cross-project contamination risk; Kilo still requires local copies; makes
provenance and failure recovery more complex.

**Effort:** Very large.

### Approach 3: Keep Global Assets and Filter Through Adapters

Leave all global platform assets installed and ask platform adapters to advertise
only selected suites and skills.

**Pros:** Smallest implementation delta.

**Cons:** Does not stop host discovery, skill metadata context leakage, Kilo
external-path parsing, vendored-skill exposure, or cross-project inventory
bleed. It violates fail-closed enforcement.

**Effort:** Small.

## Decision

Choose **Approach 1: Per-Project Materialized Projection**.

The global install remains canonical and complete for maintainers, release
validation, and source provenance. Each consumer project resolves a strict,
committed manifest from selected workflow suites, settings-derived capabilities,
and additive explicit capabilities. The manifest is then the sole source for
local platform projections, root adapters, Kilo configuration, emitted ownership
inventory, and the on-demand skill catalog.

Kilo coexistence with Codex is a hard Phase 0 release gate. Its compatibility
scanner must be demonstrably prevented from reading linked external `.agents`
or `.claude` skill roots before project manifest filtering proceeds. Kilo's own
runtime assets remain verified project-local copies. A documented upstream
allowlist/exclusion facility is still desirable, but its absence must not cause
silent fallback to unsafe discovery.

The registry must distinguish structural dependencies from optional capability
eligibility. A suite selects commands, not all implementation guidance. The
resolver chooses only mandatory runtime closure plus configuration-selected
capabilities; task routing either uses an active capability or hard-stops with a
specific config-and-regenerate remedy.

## Phased Delivery

### Phase 0: Kilo Multi-Platform Isolation

1. Reproduce Kilo discovery with Kilo and Codex installed together using Windows
   junction and macOS symlink sentinel fixtures.
2. Verify the deployed Kilo version recognizes a process-scoped
   `KILO_DISABLE_EXTERNAL_SKILLS=1` launch path and that it retains
   `.kilo/skills` while excluding `.agents/skills` and `.claude/skills`.
3. Add link/install health checks that block combined Kilo+Codex use when the
   control cannot be confirmed. Preserve Codex behavior.
4. Retain project-local copied Kilo assets and add UTF-8/frontmatter validation
   plus an explicit separate outcome for known upstream Kilo schema defects.
5. File and track the upstream request for a documented compatibility-root
   discovery allowlist.

### Phase 1: Baseline and Strict Resolution

1. Run and preserve the baseline context/token audit for the current all-skill
   install, including platform inventory and session metadata measures.
2. Version the registry/configuration schemas and implement strict parsing,
   capability eligibility, mandatory dependency closure, and active-manifest
   validation.
3. Define derivation rules for language, R dialect, tooling, and domain
   capabilities; implement explicit additive `capabilities:` selection and
   actionable fail-closed diagnostics.
4. Add idempotent migration and compatibility tests for legacy projects.

### Phase 2: Secure Project-Local Projection

1. Refactor generation to separate source and project output roots, then stage,
   validate, and atomically publish manifest-filtered platform assets.
2. Replace divergent Windows/Posix copied-directory implementations with one
   no-follow, checksum-owned synchronization path.
3. Migrate existing global links/copies safely without deleting user-owned
   content; commit `active-manifest.json` and keep regenerable runtime output
   managed.
4. Generate exact namespace-specific root adapters and configurations without
   wildcard all-skill messaging.

### Phase 3: Catalog, Router, and Observability

1. Generate `/cg-find-skill` and its static catalog from registry and skill
   frontmatter; implement compact default results and `--full`/filter behavior.
2. Implement the manifest-aware hard-stop router and missing-capability
   diagnostics.
3. Emit and validate platform inventories, adapter routes, active/inactive
   catalog reasons, and provenance without loading whole skill bodies.

### Phase 4: Controlled Vendoring

1. Implement `/cg-import-skill` quarantine, immutable-source verification,
   static admission checks, review diff, and two-stage approval.
2. Define managed/user roots and normalized collision prevention across all
   supported platforms.
3. Vendor the approved non-executable bundle into canonical managed source with
   complete provenance, licensing, and adaptation records.
4. Use the GitHub Actions hardening pilot only after the intake system is
   independently verified.

### Phase 5: Verification and Benchmark Closure

1. Run the full profile/platform/security regression matrix.
2. Benchmark against the Phase 1 baseline and publish before/after inventory,
   context, and task-success results.
3. Update public configuration, modular, skills, installation, and recovery
   documentation with only verified platform behavior.
4. Capture the final attribution and operational lessons in the existing
   roadmap/workflow artifacts.

## Acceptance Criteria

- A CG-only project, CR-only project, mixed project, and capability-specific
  project materialize different verified inventories without affecting one
  another or the global canonical source.
- Invalid or stale registry/configuration/manifest state fails before publish,
  names the defective field or dependency, and preserves the prior valid
  project projection.
- No inactive asset or reference appears in a selected platform's commands,
  agents, skills, instructions, shared assets, root adapter, configuration, or
  generated catalog.
- Kilo plus Codex succeeds on Windows and macOS sentinel tests: Codex uses
  `.agents/skills`; Kilo sees selected local `.kilo/skills` only; Kilo reports
  no external skill parse errors after a full host restart.
- Windows and POSIX synchronization produce equivalent ownership, collision,
  stale-file preservation, reparse/symlink rejection, and unlink semantics.
- Quarantine rejects prohibited external content before it reaches runtime or
  canonical skills; approved imports have pinned provenance, license evidence,
  local approval, and PR review evidence.
- `/cg-find-skill` defaults to compact manifest-backed matches and exposes
  complete records only on request; it never injects the all-skill catalog into
  normal session context.
- Before/after measurement shows a documented reduction in active inventory and
  routine context exposure without regressions in the selected workflow paths.

## Risks and Mitigations

- **Kilo environment propagation is not a documented project setting.** Prove
  the process-scoped launch path on supported editor/CLI versions, make it an
  install gate, and pursue upstream configuration support.
- **Profile bleed from shared output trees.** Never generate filtered output into
  the global install; bind every install unit to a project-scoped projection.
- **TOCTOU through junctions, symlinks, or reparse points.** Use handle/root
  anchored no-follow operations through staging, publish, rollback, marker
  writes, and stale deletion; test swap attacks with external sentinels.
- **Imported non-executable data can still be dangerous.** Default-deny the
  bundle format and scan Markdown instructions as well as file modes/extensions.
- **Configuration fallback masks errors.** Permit the legacy `[cg]` default only
  for a truly absent legacy field; all malformed present values are errors.
- **Managed/user collisions shadow trusted content.** Keep roots distinct,
  reject normalized collisions before write, and preserve user-owned bytes.
- **Broad scope delays value.** Phase 0 and baseline audit are release gates;
  defer caching, marketplace features, semantic rewriting, and transient
  overrides.

## Next Steps

1. Use `/cg-plan` to produce a Deep-scope implementation plan with Phase 0 as
   an explicit blocking prerequisite and with the listed roadmap features as
   linked work rather than duplicate features.
2. Start the plan with reproducible Kilo discovery evidence against the deployed
   release and an audited Kilo launch-path mechanism.
3. Treat registry/config schema, secure projection synchronization, and the
   capability matrix as shared cross-platform contracts with test-first
   characterization coverage.
4. Defer the GitHub Actions external-skill pilot until controlled vendoring and
   its approval/provenance path pass independently.
