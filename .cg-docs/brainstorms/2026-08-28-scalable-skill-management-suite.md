---
date: 2026-08-28
title: "Scalable Skill Management Suite"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Explicit operation modules behind one role-gated command"
tags: [skills, architecture, lifecycle, security, registry, manifests, projections, cross-platform, documentation, testing]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Scalable Skill Management Suite

## Context

Compound GPID has separate `/cg-find-skill` and `/cg-import-skill` commands,
manifest-backed discovery, quarantined external import, module ownership, active
manifest generation, and project-local platform projections. It does not have
one complete skill lifecycle. Creation is only suggested by `/cg-compound`,
imports do not fully assign ownership and capability metadata, discovery stops
when the active manifest is absent, and safe update, deprecation, removal, and
audit workflows do not exist.

The suite must support two distinct asset scopes:

- Permanent plugin skills maintained in the canonical Compound GPID source.
- Project-specific skills imported and approved by a consumer project.

Both scopes must produce valid atomic skill bundles for Copilot, Claude Code,
Codex, OpenCode, and Kilo. External or global skill locations must never become
implicit runtime sources.

This decision extends, but does not replace, prior decisions:

- `.github/` remains the canonical source for permanent plugin assets.
- Skills and their nested resources are atomic bundles.
- `module-registry.json` is the ownership and capability source of truth for
  permanent plugin assets.
- `.compound-gpid/active-manifest.json` is the committed project selection
  record.
- Project-local projections are checksum-owned, atomically published, and
  fail closed on unsafe or stale state.
- Imported content is pinned to a full commit SHA, quarantined, statically
  reviewed, and never executed during admission.

## Requirements

### Purpose and Success

The public interface will be one `/cg-skill` command. The command is a small
dispatcher, not a workflow implementation. Each operation has its own workflow,
machine-readable descriptor and contract, Python implementation module, tests,
and focused documentation page.

The first public release must contain the complete decided lifecycle. Internal
delivery remains phased, but no partial `/cg-skill` command will be released as
the production replacement.

Success means that a user or automation process can discover, inspect, create,
import, update, validate, activate, deactivate, audit, deprecate, and safely
remove a skill through deterministic contracts without bypassing ownership,
provenance, manifest, projection, or approval controls.

### Users and Authority

| Role | Main use cases | Allowed writes |
| --- | --- | --- |
| Consumer project user | Discover skills, inspect metadata, import a project-specific skill, update an approved project import, activate or deactivate an explicit capability, validate and audit project state | Approved project skill store, project skill registry, strict local configuration, active manifest, checksum-owned projections |
| Compound GPID maintainer | Create permanent skills, vendor approved external skills, update imported plugin skills, register ownership and capabilities, deprecate and remove permanent skills, run release audits | Canonical `.github/` sources, module registry, provenance records, generated targets, release documentation |
| CI and automation | Validate contracts, registries, manifests, bundles, references, documentation, and target parity; consume stable JSON | None unless a separately approved apply operation is invoked |
| Coding agent host | Load only approved projected bundles for its selected platform | None; hosts consume projections and do not resolve external sources |

The tool detects the role from the checkout. Consumer is the safe default.
Maintainer authority requires code-enforced proof of a canonical source checkout;
an agent assertion or command-line role flag is not sufficient. An invalid or
ambiguous role fails closed.

### Command Grammar

```text
/cg-skill find [filters]
/cg-skill info <id>
/cg-skill create <id> --scope plugin --module <module-id> --capability <capability-id>
/cg-skill import <repo>@<full-sha> <path> --scope project|plugin
/cg-skill update <id> --to <full-sha>
/cg-skill validate [<id>|--all] [--format human|json]
/cg-skill deprecate <id> --successor <id>
/cg-skill remove <id> [--migration <path>]
/cg-skill activate <capability>
/cg-skill deactivate <capability>
/cg-skill audit [--provenance|--references|--updates]
/cg-skill help [operation]
```

Common rules:

- `find`, `info`, `validate`, `audit`, and `help` are read-only.
- A mutating operation produces a plan by default.
- Apply requires `--apply <plan-digest>` and revalidates all plan inputs.
- `--format json` uses one stable result envelope for all operations.
- Paths in output are repository-relative and use `/` separators.
- Records and findings use deterministic ordering.
- `create` is plugin-only in the first release. Project users can import
  project-specific skills but cannot create unprovenanced project bundles.
- `update` applies only to skills with pinned upstream provenance. A new full
  SHA is mandatory; a branch, tag, or short SHA is not accepted.
- `deprecate` is explicit because immutable IDs replace in-place rename.
- `remove` never performs an in-place rename and never deletes a modified or
  user-owned projected file.

### Missing or Stale Manifest Behavior

Discovery must become useful without weakening runtime safety:

- `find`, `info`, and `help` may build a read-only prospective catalog from
  validated registry, frontmatter, project registry, and strict configuration
  inputs when the active manifest is missing or stale.
- Prospective output must report manifest health and must not claim that a
  skill is active or projected.
- Capability routing, activation state claims, apply operations, and projection
  verification require a fresh valid manifest or must generate and verify one
  as part of the approved transaction.
- Invalid configuration, ownership, provenance, or registry input remains a
  hard error. There is no global all-skill fallback.

### Project-Specific Skill Store

Approved consumer imports use a dedicated committed source store:

```text
.compound-gpid/skills/<id>/
.compound-gpid/project-skill-registry.json
.compound-gpid/skill-provenance/<id>.json
```

This store is authoritative for project-specific skills. It is not a generated
platform tree. The project registry uses a reserved project namespace and must
record an explicit owner module, capability, source path, supported platforms,
selectors, lifecycle status, and provenance identity for every project skill.
It cannot replace, weaken, or shadow a canonical module or capability record.

Manifest resolution combines the validated canonical registry with the
validated project registry. Projection code then publishes selected atomic
bundles to each eligible platform. Portable case-folded path and identifier
collisions fail before any write. A project import is inactive after admission;
activation is a separate approved operation.

### Creation and Import Metadata

Every newly created or imported skill must receive, before admission:

- A valid immutable identifier and normalized bundle path.
- A quoted, ASCII-safe frontmatter description and valid `SKILL.md`.
- One explicit owner module.
- One explicit capability record or an explicit assignment to an existing
  compatible capability.
- Supported suite and platform eligibility.
- Activation cost, task triggers, and any strict configuration selectors.
- Origin scope: `plugin-canonical` or `project-imported`.
- Source provenance and approval identity.
- A deterministic bundle inventory and content digest.

The tool does not infer ownership from a filename prefix. It does not add a
skill to a broad suite glob and assume that capability registration is complete.
Catalog data is derived from validated source metadata and registries; there is
no second hand-edited catalog source.

Creation supports focused templates for `SKILL.md`, references, workflows,
examples, and opaque resources. It creates only requested files and never
executes generated or imported resources. Identifier, portable path, module,
capability, and destination collisions are plan errors.

### Inputs and Outputs

The common request envelope is `cg-skill-request-v1`. Each operation descriptor
points to an operation-specific argument schema.

```json
{
  "schema": "cg-skill-request-v1",
  "operation": "remove",
  "phase": "plan",
  "root": ".",
  "arguments": {"id": "cg-skill-example"}
}
```

The common result envelope is `cg-skill-result-v1` and contains:

- `ok`, `operation`, `phase`, `role`, and `changed`.
- `planDigest` and ordered `actions` for mutation plans.
- `findings` with stable code, severity, path, message, and remediation.
- Operation-specific `data` validated by that operation's result contract.
- Redacted provenance and review evidence paths where applicable.

The apply digest binds at least the operation, normalized arguments, role,
source revision, configuration digest, canonical registry digest, project
registry digest, manifest selection fields, provenance state, reference scan,
and bundle inventory. Apply rejects stale or changed inputs instead of silently
replanning.

### Explicitly Out of Scope

- A public marketplace or search over arbitrary remote repositories.
- Runtime loading from a global, external, or network skill location.
- Mutable Git references, short SHAs, submodules, redirects, or LFS content.
- Execution of imported bundle content during admission or generation.
- Automatic approval, activation, vendoring, registry mutation, or deletion.
- In-place skill identifier rename.
- Deletion of modified or user-owned projected content.
- A generic declarative workflow language for arbitrary operations.
- Project-authored skills without pinned import provenance in the first release.

## Architecture

### Canonical Workflow and Contract Layout

```text
.github/prompts/cg-skill.prompt.md
.github/skills/cg-skill-management/SKILL.md
.github/skills/cg-skill-management/workflows/find.md
.github/skills/cg-skill-management/workflows/info.md
.github/skills/cg-skill-management/workflows/create.md
.github/skills/cg-skill-management/workflows/import.md
.github/skills/cg-skill-management/workflows/update.md
.github/skills/cg-skill-management/workflows/validate.md
.github/skills/cg-skill-management/workflows/deprecate.md
.github/skills/cg-skill-management/workflows/remove.md
.github/skills/cg-skill-management/workflows/activate.md
.github/skills/cg-skill-management/workflows/deactivate.md
.github/skills/cg-skill-management/workflows/audit.md
.github/skills/cg-skill-management/workflows/help.md
.github/shared/skill-management/operations/<operation>.json
.github/shared/skill-management/contracts/request-v1.schema.json
.github/shared/skill-management/contracts/result-v1.schema.json
.github/shared/skill-management/contracts/plan-v1.schema.json
.github/shared/skill-management/contracts/<operation>-v1.schema.json
```

There is one descriptor per operation rather than one central operation list.
The dispatcher normalizes the first argument, rejects path separators and
unknown names, loads the matching descriptor and workflow, and invokes the
declared handler. `help` discovers validated descriptors in lexical order.
Adding an operation does not require edits to existing operation files or
business logic in the dispatcher.

The command prompt remains owned by `suite-cg`. A new focused skill-management
capability pack owns the management skill bundle and shared contracts. The
module registry must give every new canonical asset exactly one owner and add
the capability as a declared dependency of `suite-cg`.

### Python Layout

```text
scripts/cg_skill.py
scripts/skill_management/__init__.py
scripts/skill_management/contracts.py
scripts/skill_management/context.py
scripts/skill_management/planning.py
scripts/skill_management/operations/<operation>.py
scripts/skill_management/services/catalog.py
scripts/skill_management/services/bundles.py
scripts/skill_management/services/admission.py
scripts/skill_management/services/registry.py
scripts/skill_management/services/references.py
scripts/skill_management/services/runtime.py
scripts/skill_management/services/provenance.py
```

`scripts/cg_skill.py` parses only common arguments, validates the operation
descriptor, lazy-loads the handler, and renders the common result envelope.
It contains no operation workflow or registry mutation logic.

Each operation module validates operation-specific arguments and coordinates
domain services. An operation module does not write files directly and does not
implement its own output shape, role detection, approval logic, or transaction
engine.

Existing `cg_skill_catalog.py`, `cg_import_skill.py`, `cg_vendor_policy.py`,
`cg_project_manifest.py`, `cg_project_projection.py`,
`cg_generate_targets.py`, and `cg_validate_modules.py` remain authoritative for
their current rules. Implementation must expose or move focused APIs from them;
it must not duplicate their parsing, security, ownership, manifest, projection,
or generation logic.

### Responsibility Boundaries

| Component | Owns | Must not own |
| --- | --- | --- |
| Prompt dispatcher | Operation lookup, workflow loading, common invocation | Lifecycle policy, filesystem writes, registry logic |
| CLI dispatcher | Common parsing, descriptor validation, handler dispatch, output rendering | Operation-specific mutation logic |
| Operation module | One use case and its service coordination | Duplicated security, projection, or result-format code |
| Catalog service | Discovery, prospective catalog, availability explanation | Activation writes or manifest publication |
| Bundle service | Bundle inventory, scaffold, path and content validation | External fetch or module registration |
| Admission service | Quarantine, static checks, redacted diff, approval evidence | Activation, projection, or arbitrary execution |
| Registry service | Canonical and project ownership/capability validation and planned edits | Manifest or target generation |
| Reference service | Exact command, agent, instruction, documentation, registry, and skill references | Automatic broad text replacement |
| Runtime service | Manifest resolution, target generation, project projection, parity verification | Admission policy or lifecycle decisions |
| Provenance service | Immutable source identity, append-only update history, tombstones | Network fetch or bundle mutation |
| Planner/apply engine | Preconditions, ordered actions, digest, secure transaction, rollback | Operation-specific policy decisions |

### Mutation Transaction

Planning does not write canonical assets, registries, configuration, manifests,
or projections. Import planning may write only isolated quarantine content and
redacted review evidence because static admission requires acquisition. That
content is never loadable.

Apply performs these stages:

1. Revalidate role, request contract, plan digest, source state, and approvals.
2. Stage all source, registry, provenance, configuration, manifest, and generated
   outputs under transaction-owned paths.
3. Validate module ownership, capability closure, bundle contents, references,
   manifest freshness, target parity, and projection containment against the
   complete staged state.
4. Publish with pinned parents, no-follow checks, checksum ownership, and
   compare-before-replace behavior.
5. Verify every selected platform projection and generated target.
6. Remove only transaction-owned staging data and write the final result.

Failure leaves the prior valid state active. Rollback must not overwrite bytes
that another process created or changed after planning.

## Lifecycle State Model

Origin, lifecycle, and availability are separate dimensions.

| Dimension | Values | Meaning |
| --- | --- | --- |
| Origin | `plugin-canonical`, `project-imported` | Where the approved source bundle and ownership record live |
| Admission | `quarantined`, `approved`, `rejected` | Whether external content passed policy and approval |
| Lifecycle | `current`, `deprecated`, `removed` | Whether the identifier accepts normal use, points to a successor, or is a tombstone |
| Availability | `inactive`, `active` | Whether the capability is selected and verified in eligible projections |

Allowed transitions:

```text
create plan -> approved/current/inactive plugin skill
import plan -> quarantined
approved import apply -> approved/current/inactive project or plugin skill
current/inactive -> current/active
current/active -> current/inactive
current/* -> deprecated/* with required successor
deprecated/active -> deprecated/inactive
deprecated/inactive -> removed after reference and grace checks
approved imported current/* -> approved imported current/* at a new full SHA
```

New activation of a deprecated skill is blocked. An already active deprecated
skill may remain active during an approved migration but always emits a warning.
A removed identifier cannot be reused or restored; its tombstone and provenance
history remain. Replacement requires a new identifier.

Removal requires all of these conditions:

- The skill is deprecated and inactive.
- A valid successor exists unless an approved no-successor exception is part of
  the plan.
- The reference scanner reports no live references, or every reference is
  covered by an explicit reviewed migration file.
- No active manifest or selected projection requires the skill or capability.
- The configured deprecation grace policy is complete.
- Only checksum-owned generated copies are scheduled for deletion.

## Security and Approval Boundaries

- Consumer is the default role. Maintainer role requires a verified canonical
  registry, expected repository identity, and approved source checkout state.
- Every mutation uses plan then apply. `--yes`, agent prose, or an environment
  variable cannot bypass the plan digest.
- Import accepts only HTTPS, a normalized approved path, and a full 40-character
  commit SHA.
- Fetch does not follow redirects and does not load submodules or LFS objects.
- Archive members are validated before extraction. Symlinks, junctions,
  reparse-point escapes, portable path collisions, devices, and executable
  content are rejected.
- Limits are enforced from metadata and bounded streams before full content is
  read into memory.
- Admission scans paths, frontmatter, links, secrets, prompt-injection markers,
  licenses, binary content, and bundle limits without executing content.
- Review diffs are deterministic and secret-redacted.
- Permanent vendoring requires canonical maintainer role and plugin-scope
  approval. Project import approval cannot grant plugin authority.
- Registry changes, activation, deactivation, deprecation, and removal each
  require a fresh apply approval.
- Projection writes are confined to declared roots and checksum-owned files.
- Invalid configuration, manifests, provenance, ownership, references, or
  projection state blocks apply with exact remediation.

## Compatibility and Migration

`/cg-find-skill` and `/cg-import-skill` will not remain as aliases. The first
public `/cg-skill` release removes their prompt files, generated command files,
and dedicated wrappers in the same breaking change.

Migration mapping:

```text
/cg-find-skill [filters] -> /cg-skill find [filters]
/cg-import-skill <source> [options] -> /cg-skill import <source> [options]
```

There is no runtime deprecation period. Migration documentation, release notes,
updated examples, and repository-wide reference checks are mandatory before
release. Tests permit old names only in the migration page and historical
artifacts. Internal Python modules may keep stable APIs during refactoring, but
they are not user-facing compatibility commands.

## Documentation Information Architecture

```text
docs/skills/management/index.md
docs/skills/management/lifecycle.md
docs/skills/management/commands/<operation>.md
docs/skills/management/maintainers/creation.md
docs/skills/management/maintainers/vendoring.md
docs/skills/management/maintainers/registry-and-capabilities.md
docs/skills/management/maintainers/release-checks.md
docs/skills/management/consumers/discovery.md
docs/skills/management/consumers/project-skills.md
docs/skills/management/consumers/activation.md
docs/skills/management/consumers/remediation.md
docs/skills/management/security.md
docs/skills/management/migration.md
```

The overview explains the model and links to focused pages. It does not repeat
all operation details. Each operation descriptor names its command page, and a
documentation completeness test checks that grammar, options, roles, result
codes, examples, and lifecycle effects agree with executable behavior.

The main command reference, skill catalog, configuration guide, installation
guide, troubleshooting guide, navigation, and generated platform command lists
must link to the focused pages. Maintainer and consumer guidance remain separate.
Security controls are documented once and linked from import, update, and
removal pages.

## Test Strategy and Release Gates

### Unit and Contract Tests

- One unit test module for every operation module.
- Focused tests for each domain service.
- Descriptor and JSON Schema validation tests.
- Dispatcher tests that prove unknown operations fail without importing an
  unrelated operation module.
- Stable JSON snapshots, deterministic ordering, path normalization, finding
  severities, remediation, and exit-code tests.
- Plan digest, changed-input, replay, wrong-role, expired-plan, and concurrent
  modification tests.

### Security Tests

- Full SHA, HTTPS, redirect, submodule, LFS, license, secret redaction, and
  prompt-injection cases.
- Tar and archive traversal, absolute paths, case collisions, symlinks,
  junctions, reparse points, devices, executable bits, and decompression limits.
- Metadata-first and bounded-read tests that prevent memory exhaustion.
- Canonical role spoofing and project-to-plugin privilege escalation tests.
- Destructive operation tests that prove modified and user-owned projected
  content is never removed.

### Integration Tests

- Canonical registry and project registry ownership and capability closure.
- Missing, malformed, and stale active manifests.
- Prospective discovery without false active-state claims.
- Create and import through catalog, manifest, target generation, projection,
  and verification.
- Activation and deactivation through strict config, manifest regeneration, and
  every selected platform.
- Update with redacted deterministic diff and append-only provenance history.
- Reference-safe deprecation and removal with migration files and tombstones.
- Generated-target parity for Copilot, Claude Code, Codex, OpenCode, and Kilo.
- Windows, macOS, and Linux path and transaction behavior.

### Documentation and Release Gates

A release is blocked when any of these conditions exists:

- A descriptor, workflow, implementation module, contract, test, or command
  page is missing for a registered operation.
- An example does not match executable help or contract behavior.
- A canonical or project asset has zero or multiple owners.
- A capability, selector, provenance record, or platform eligibility record is
  invalid.
- A manifest is stale or a selected projection is missing, stale, escaped, or
  not checksum-owned.
- Generated native targets differ from canonical `.github/` sources.
- Security, reference, migration, deterministic-output, or cross-platform tests
  fail.
- Old command names remain outside the migration page or historical artifacts.

## Approaches Considered

### Approach 1: Explicit Operation Modules

Use a thin prompt router and CLI router, one machine-readable descriptor and
workflow per operation, explicit Python operation modules, and focused shared
domain services. Reuse current catalog, admission, registry, manifest,
projection, target-generation, and validation rules through tested APIs.

Pros:

- Clear responsibility and security boundaries.
- Stable contracts and one plan/apply implementation.
- New operations do not change existing operation files.
- Project and plugin skill scopes share protocol without sharing authority.
- Direct fit with the module registry and atomic bundle architecture.

Cons:

- Requires a controlled refactor of existing script APIs.
- Adds a validated project registry overlay.
- Full first release has a large integration and security surface.

Effort: Large, estimated at 6-10 engineering weeks plus security review.

Recommended: Yes. This is the smallest design that meets the complete lifecycle
and extension requirements without a large script or a generic interpreter.

### Approach 2: Thin Facade Over Separate Scripts

Keep current scripts intact and add one standalone script for every missing
operation. Let the command router invoke each script directly.

Pros:

- Lower initial refactor cost.
- Existing discovery and import tests change less.
- Individual scripts remain easy to invoke.

Cons:

- Role detection, JSON results, plan/apply, error codes, and registry loading
  become duplicated infrastructure.
- Cross-operation transactions and lifecycle invariants can drift.
- The design can become a set of large scripts with inconsistent contracts.

Effort: Large, estimated at 4-7 engineering weeks.

Recommended: No. The lower initial cost creates the maintenance problem that
the suite is intended to prevent.

### Approach 3: Declarative Lifecycle Engine

Define operations as declarative step graphs interpreted by one generic engine.

Pros:

- Uniform plan/apply and output behavior.
- Strong introspection for generated help and documentation.
- Many future operations could be mostly declarative.

Cons:

- The engine becomes a new workflow language and central complexity point.
- Security behavior becomes indirect and harder to audit.
- Import, projection, registry, and removal need special steps that weaken the
  abstraction.
- Effort is not proportional to the current operation count.

Effort: Very large, estimated at 10-14 engineering weeks.

Recommended: No. It over-engineers the extension mechanism.

## Devil's Advocate Review

The problem is pre-validated by fragmented commands, missing creation and
lifecycle paths, incomplete imported-skill ownership, missing-manifest discovery
failure, and prior importer security findings.

A command alias over existing scripts would solve discoverability but not the
project skill store, stable contracts, role enforcement, plan/apply, reference
safety, or projection verification. A real domain boundary is justified.

The full lifecycle in one public release delays user value and combines several
high-risk systems. A staged public release would reduce risk, but the user chose
one complete first public release. Internal phases and release gates are
therefore mandatory; partial code must not be presented as production-ready.

The chosen approach aligns with the charter's modular ownership, fail-loudly
rule, canonical sources, atomic bundles, deterministic generation, and
cross-platform parity. Immediate alias removal is a breaking choice but does not
conflict with the current work-in-progress charter.

## Decision

Choose Approach 1: explicit operation modules behind one role-gated
`/cg-skill` command. Complete all internal phases before the first public
release.

Use a dedicated committed project skill store and project registry overlay so
consumer-approved skills can be projected to every selected coding agent without
becoming permanent Compound GPID assets. Use code-enforced consumer and
maintainer roles, deterministic plan-then-apply for every mutation, immutable
skill IDs, explicit deprecation, reference-safe removal, and append-only
provenance.

Remove `/cg-find-skill` and `/cg-import-skill` immediately when the complete new
command ships. Do not maintain compatibility aliases.

## Phased Implementation

### Phase 1: Contracts and Read-Only Spine

Implement the common schemas, per-operation descriptors, thin prompt and CLI
dispatchers, role detection, common findings, and `find`, `info`, `validate`,
and `help`. Adapt discovery to support prospective output when the manifest is
missing or stale.

This is the recommended minimum viable implementation phase because it proves
the extension contract, routing, deterministic output, and manifest safety
before any lifecycle writer exists. It is an internal foundation, not the first
public replacement release.

### Phase 2: Project Skill Admission and Runtime

Implement the project store and registry schema, project-scoped import,
project provenance, activation, deactivation, combined manifest resolution,
multi-platform projection, and containment verification.

### Phase 3: Maintainer Creation and Vendoring

Implement permanent creation, focused scaffolds, plugin-scoped vendoring,
explicit module and capability registration, catalog derivation, generated
target updates, and maintainer documentation.

### Phase 4: Update, Audit, Deprecation, and Removal

Implement pinned upstream comparison, deterministic redacted update diffs,
append-only provenance, complete reference scanning, immutable-ID successor
migration, deprecation, tombstones, and safe removal.

### Phase 5: Migration, Security Review, and Release

Complete all command pages, consumer and maintainer guides, migration updates,
old-reference cleanup, platform parity, cross-platform integration, adversarial
security review, and release gates. Remove old command surfaces only in this
phase after the new command passes every gate.

## Unresolved Decisions Requiring Human Approval

1. Select the reserved project module and capability identifier grammar and
   confirm whether each project skill gets one capability or related project
   skills may share a capability.
2. Decide whether project imports may approve any exact HTTPS repository per
   plan or must first add the repository to a constrained project policy overlay.
   The project policy must never weaken canonical security ceilings.
3. Set the deprecation grace policy for skill removal, such as one major release,
   a fixed number of days, or both.
4. Define the exact canonical-checkout proof for maintainer role, including
   repository origin, registry identity, source revision, and allowed branch
   state.
5. Decide where signed or reviewable plan records live, how long they remain
   valid, and whether approval identity must use a local user name, a commit, a
   pull request, or another external review reference.
6. Confirm whether project-authored, non-imported skills remain out of scope or
   should later use `create --scope project` with a distinct provenance model.
7. Define the release version that carries the immediate command removal and
   confirm that the breaking migration is acceptable without compatibility
   aliases.

## Next Steps

1. Turn this brainstorm into a Deep implementation plan with a requirement
   traceability matrix and explicit file-level phases.
2. Resolve the seven human approval decisions before Phase 2 or any destructive
   operation implementation begins.
3. Prototype and review the request, result, plan, operation descriptor, project
   registry, and provenance schemas before writing operation modules.
4. Map each existing catalog, import, policy, registry, manifest, projection,
   generation, and validation function to its future service boundary. Mark
   reuse, move, or refactor; do not duplicate behavior.
5. Define per-phase verification commands and the final release gate matrix,
   including safe Pester execution rules for any PowerShell tests.
