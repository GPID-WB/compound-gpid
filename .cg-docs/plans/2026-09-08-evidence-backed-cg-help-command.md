---
date: 2026-09-08
title: "Evidence-Backed Cross-Platform /cg-help Command"
status: active
completed-phases: [1, 2]
current-phase: 3
execution-report: ".cg-docs/work-reports/2026-09-09-evidence-backed-cg-help-command.md"
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-09-04-cg-help-command.md"
language: "Python"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
tags: [help, commands, catalog, deterministic-retrieval, cross-platform, documentation]
phases: 6
---

# Plan: Evidence-Backed Cross-Platform /cg-help Command

## Objective

Add `/cg-help` as the single in-chat entry point for discovering and using
Compound GPID slash and shell commands. The command will use a versioned,
generated evidence catalog and a deterministic Python query layer for overview,
exact lookup, typo handling, candidate retrieval, active-suite ranking, and
explicit result states. The model may rerank only returned candidate IDs. A
second deterministic validation and rendering step produces the final answer,
so no model-produced command, URL, activation action, or workflow step can cross
the evidence boundary. Equivalent assets and static contracts are required on
all five platforms; runtime query-mode support is claimed only for platforms
whose support-matrix row has executed host evidence.

## Context

The approved brainstorm selected a **Hybrid Help Engine**. This plan preserves
that decision and resolves the implementation details against the active
integration baseline:

- The current planning worktree is at `c94b6bca` and is 174 commits behind the
  active `dev` integration branch observed at `11ce531`. Implementation must run
  from a feature branch that contains `dev` at or after that observed commit.
  The first `/cg-work` preflight must stop before edits if this ancestry check
  fails; this plan does not authorize an implicit rebase or merge.

- `.github/` is canonical. Copilot consumes it directly; Claude Code, Codex,
  OpenCode, and Kilo use committed generated trees produced by
  `scripts/cg_generate_targets.py`.
- `/cg-help` is a cross-suite capability, not a technical-suite-only command.
  A new `cap-help` capability module owns its prompt, sidecar, shell metadata,
  and generated catalog; both `suite-cg` and `suite-cr` depend on it. The module
  registry uses an explicit ownership exclusion so the existing broad
  `suite-cg` prompt glob does not also own `/cg-help`.
- Every regular top-level `.github/shared/*` file already maps to each native
  target's shared root. A generated `.github/shared/help-catalog.json` therefore
  needs no new target-mapping output path.
- The target generator must not write canonical `.github/` assets. Help-catalog
  generation is a separate deterministic step that runs before native-target
  generation; native generation only validates and distributes its result.
- Canonical prompt frontmatter provides only `description`, and the existing
  general frontmatter parser is permissive and flat. Help metadata therefore
  uses strict per-command `*.help.json` sidecars beside searchable canonical
  prompts. Sidecars keep metadata out of normal prompt context, remain owned by
  the same suite module, and avoid arbitrary nested frontmatter or free-form
  body extraction.
- Shell command metadata is currently split across wrappers, installers, and
  documentation. `.github/shared/shell-commands.json` becomes the canonical
  shell help metadata source, with parity tests against all implementation and
  install inventories.
- The active `dev` branch already contains five `/cr-*` prompts and
  `.github/shared/module-registry.json` schema version 2. That registry owns
  `suite-cg` and `suite-cr`, their canonical assets, dependencies, supported
  platforms, activation selectors, and source provenance. Help ownership,
  availability, and activation evidence extend this registry; no parallel
  command-suite registry is created.
- `scripts/brain/query.py` supplies useful patterns for stable scoring, evidence
  reasons, warnings, and bounded output, but its algorithm is not reused as-is:
  help needs typo distance, absolute thresholds, strict candidate limits,
  availability semantics, and command/workflow-specific result states.
- The existing `/cg-token-audit` command is the closest user-facing pattern: a
  thin prompt invokes deterministic local tooling and stops instead of asking
  the model to inspect broad repository content when the tool is unavailable.
- `docs/reference.md` and `docs/reference/commands.md` already disagree with the
  current command inventory. Their help-managed command sections move to one
  deterministic catalog owner. The wiki manifest, agent, skill, and tests must
  explicitly preserve/delegate those sections so `/cg-wiki rebuild` cannot
  overwrite them.

Relevant prior knowledge:

- Native targets are generated product surfaces and require deterministic
  generation, ownership manifests, and drift/release gates. Source:
  `.cg-docs/solutions/environment-issues/2026-07-03-cross-agent-native-platform-trees-require-generator-drift-tests-consistent-python.md`.
- The canonical-to-native packaging foundation requires target-local shared
  resources, complete closure, fail-closed validation, and no canonical writes
  from the native generator. Source:
  `.cg-docs/plans/2026-07-27-canonical-native-packaging-foundation.md`.
- Thin user prompts should consume deterministic, compact tooling output and
  must not replace a missing backend with broad model inspection. Source:
  `.cg-docs/plans/2026-06-16-token-context-optimization-closure.md`.

## Plan Review Resolution

| Finding | Required Revision | Plan Resolution |
|---------|-------------------|-----------------|
| P1.1 | Use the active integration baseline and existing module registry. | Added an ancestry preflight against `dev` at or after `11ce531`; replaced the parallel suite registry with `module-registry.json` extensions; included current `/cg-*` and `/cr-*` sources and tests. |
| P1.2 | Prevent shell injection when transporting user queries. | Added a CLI-created, confined request-file protocol populated only through a structured file-write tool; no user query is interpolated into a shell command. |
| P1.3 | Give generated documentation one owner and bootstrap missing markers. | Added an explicit wiki ownership migration, one guarded marker-bootstrap operation, wiki preservation rules, and wiki regression tests before strict docs checks. |
| P1.4 | Make the final evidence boundary executable. | Limited the model to candidate-ID reranking; deterministic Python validates the selection and renders all final commands, URLs, activation text, and workflows. |
| P2.1 | Define JSON/error/exit-code behavior. | Added a state-by-state transport contract: every semantic result, including `error`, emits validated JSON on stdout; errors also use documented nonzero codes and stderr diagnostics. |
| P2.2 | Select one runtime catalog source. | Selected the catalog in the installed Compound GPID clone as the only runtime source; native copies are distribution/parity assets and prompts do not pass target-local catalog paths. |
| P2.3 | Define runtime freshness trust. | The CLI recomputes the fixed installed source inventory digest before every query; install/link/update/release also run catalog `--check` before mutation or success claims. |
| P2.4 | Represent Windows/POSIX shell differences. | Added `supportedOS` and per-OS implementation evidence to shell records; runtime availability uses `sys.platform` and tests retain POSIX-only summary wrappers. |
| P2.5 | Keep help metadata out of prompt context. | Replaced prompt-body metadata blocks with owner-module adjacent `*.help.json` sidecars and added prompt token/absence regressions. |
| P2.6 | Enforce Python 3.8 compatibility. | Added `compileall`, CLI startup, catalog generation, and all focused help tests to the Python 3.8 CI job with a compatible pytest pin. |
| P2.7 | Make each phase independently green. | Limited Phase 1 to schema/parser/source validation, moved runtime/query assertions to their implementation phases, and requires catalog regeneration/check in the prompt phase. |
| Pass 2 P1.1 | Keep `/cg-help` available in CR-only projections. | Added a shared `cap-help` module, explicit overlap resolution, both-suite dependencies, and CG-only/CR-only/mixed projection tests on all platforms. |
| Pass 2 P1.2 | Disambiguate slash and shell commands with the same visible name. | Added kind-qualified canonical IDs, preserved leading-slash intent, defined bare-name ambiguity, and required qualified IDs in relations/workflows/selections/follow-ups. |
| Pass 2 P1.3 | Close module-registry changes over every current consumer. | Kept schema version 2 with optional help/ownership-exclusion fields; added all generator, validator, context, manifest, projection, and skill-management consumers/tests; made sidecars canonical owned assets. |
| Pass 2 P1.4 | Include command wrappers for skill management and Kilo while excluding direct assets. | Clarified that `/cg-skill` and shell `cg-skill` are in scope, direct skill assets are not, and explicitly included `cg-kilo`, `cg-brain-init`, and every refreshed shell class. |
| Pass 2 P2.1 | Reuse active suite/config/manifest authority. | Reused strict config parsing and `.compound-gpid/active-manifest.json` validation; activation guidance stays in the registry but no new activation parser is added. |
| Pass 2 P2.2 | Remove impossible post-pull preservation claims. | Kept pre-mutation preservation for install/link, but documents that failed post-pull validation can already affect linked consumers and requires explicit recovery without auto-reset. |
| Pass 2 P2.3 | Keep request files out of consumer version control. | Added consumer managed-ignore updates, prepare-time expired cleanup, interrupted-session/git-status tests, and existing-request ownership checks. |
| Pass 2 P2.4 | Detect semantic sidecar staleness. | Added per-record pinned definition digests over authoritative prompt/parser/help sources; ordinary `--write` cannot refresh them and fails after implementation-only changes. |
| Pass 2 P2.5 | Keep Phase 2 target fixtures green. | Deferred mandatory target-generator integration to Phase 5, where all generator fixtures and ownership/packaging/path/mapping suites are updated and run together. |
| Pass 3 P1.1 | Do not assign ownership before `/cg-help` files exist. | Phase 1 creates `cap-help` with existing shell metadata only; Step 7 atomically creates the prompt/sidecar, adds their exact ownership, pins the digest, regenerates the catalog, and proves cross-suite projection. |
| Pass 3 P1.2 | Apply ownership exclusions in the central registry service and lifecycle callers. | Added `skill_management/services/registry.py`, all owner-resolution paths, and focused read/create/migration/dispatch/audit tests for load, snapshot, mutation, and serialization. |
| Pass 3 P2.1 | Give absent config/manifest states one deterministic activation result. | Explicit suites require a valid active manifest; legacy CG default is allowed only when existing tooling proves non-projected legacy mode and exact expected command paths; unverified commands are never recommended. |
| Pass 3 P2.2 | Version and validate prepare/selection transport responses. | Added a separate operation-discriminated transport envelope with exact UUID/path derivation, limits, expiry, and prompt validation before every file write. |
| Pass 3 P2.3 | Define host-specific argument sources without false byte-exact claims. | Added target-mapping argument-source capabilities, generated adapter assertions, host smoke evidence, safe model-visible fallback semantics, and blocked support when a host cannot expose query text safely. |
| Pass 3 P3.1 | Select one repeated marker-bootstrap behavior. | Repeated bootstrap is an idempotent zero-status no-op with a stable `already-bootstrapped` result and no file mutation. |
| Pass 4 P1.1 | Represent commands shared by more than one suite. | Replaced singular suite ownership in command records with `ownerModule` plus sorted `supportedSuites`; ranking evaluates the active intersection and tests shared help/shell commands in each suite mode. |
| Pass 4 P2.1 | Do not complete with unproved query-mode support. | Added a required support matrix separating asset/static contract from runtime query proof and prohibited runtime claims for unverified rows. |
| Pass 4 P2.2 | Keep target-mapping changes compatible until fixture migration. | Kept schema version 1 with an optional argument-source field for legacy non-help fixtures, made it mandatory whenever `cap-help` is present, and added production completeness tests for all five targets. |
| Pass 5 P1.1 | Give host certification an executable scope. | Made five-platform asset/static proof required, retained required Kilo certification through existing infrastructure, allowed explicit `unverified-no-certified-host` status for other hosts, and blocked runtime claims or concealed probe failures without creating unscheduled credentialed CI. |
| Pass 6 P1.1 | Bind support evidence to the implementation under test. | Added a versioned JSON support artifact with Git/catalog/prompt/mapping hashes, exact trusted-SHA Kilo checkout controls, a strict validator, and documentation/release digest gates; moved all Kilo integration files to Step 7. |
| Pass 7 P1.1 | Remove the committed-evidence Git SHA cycle. | Bound host evidence to a pre-evidence `subjectCommit`; validators require ancestry and byte-identical help-sensitive paths between the subject and current/release checkout, while excluding the committed evidence file itself. |
| Pass 8 P1.1 | Certify only after all bound implementation paths are final. | Moved the actual Kilo host run, combined support JSON, and support-claim rendering to Step 12 after Steps 9-11; Phase 4 builds/tests certification tooling only, and no help-sensitive path may change after the subject commit. |

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Plain `/cg-help` is available in CG-only, CR-only, and mixed-suite projects and returns a concise categorized overview, common workflow entry points, and copyable query examples. | brainstorm requirements 1-3 + plan review pass 2 P1.1 |
| R2 | Exact queries for `/cg-*`, `/cr-*`, and Compound GPID shell commands use kind-qualified canonical identities and return a practical guide with purpose, use cases, syntax, arguments, prerequisites, examples, outputs, constraints, and next commands. | brainstorm requirements 4-5, 11 + plan review pass 2 P1.2 |
| R3 | Free-text queries use deterministic weighted retrieval over curated intents and examples. The model may return only a reranked list of selected candidate IDs; deterministic validation and rendering produce the final response. | brainstorm requirements 6, decision + plan review P1.4 |
| R4 | Supported multi-command workflows are returned only from explicit workflow evidence; every step identifies its command and catalog or approved-document source. | brainstorm requirements 7, decision |
| R5 | When workflow evidence is insufficient, return at most three ranked command candidates with a match reason, availability label, controlled confidence wording, and an exact follow-up query. | brainstorm requirement 8 |
| R6 | When no in-scope evidence supports a request, return an explicit unsupported result without inventing a command, workflow, capability, activation action, or documentation claim. | brainstorm requirements 9, 12, 36 |
| R7 | Represent each command with `ownerModule` and sorted `supportedSuites`; rank commands whose supported-suite set intersects active suites before inactive commands, and show an inactive suite only with module-registry availability and activation evidence. Missing or inconsistent active-suite evidence fails closed. | brainstorm requirements 10, 30 + plan review P1.1 + pass 4 P1.1 |
| R8 | Cover every authoritative `/cg-*` and `/cr-*` prompt plus every refreshed Compound GPID shell command available on the current OS, including `/cg-skill`, shell `cg-skill`, `cg-kilo`, and `cg-brain-init`. Direct agent/skill assets remain outside the searchable surface, but commands that manage them are in scope. | brainstorm requirements 11-12 + plan review pass 2 P1.4 |
| R9 | Store strict slash help metadata in owner-module `*.help.json` sidecars beside canonical prompts and shell metadata in the shared `cap-help` authority; extend the existing module registry and generate the merged catalog without a parallel suite or command registry. | brainstorm requirements 34, 76 + plan review P1.1/P2.5 + pass 2 P1.1/P1.3 |
| R10 | Version and validate kind-qualified command IDs (`slash:<name>` or `shell:<name>`), suite/category metadata, aliases, intents, usage, examples, prerequisites, outputs, constraints, related commands, canonical provenance, supported OS/platforms, availability, activation, and documentation links. | brainstorm decision, catalog fields + plan review pass 2 P1.2/P2.4 |
| R11 | Treat sidecars, shell metadata, module-registry help fields, workflow records, and documentation as untrusted extraction data. Parse only fixed source classes and never execute or obey extracted text. | brainstorm requirement 35 + plan review P2.5 |
| R12 | Fail loudly on missing, malformed, duplicate, ambiguous, stale, unavailable, unsafe, or unverifiable catalog evidence; never fall back to an unbounded repository scan. | brainstorm requirement 36 |
| R13 | Generate and distribute equivalent current help assets and static argument/transport contracts for Copilot, Claude Code, Codex, OpenCode, and Kilo through existing generation, ownership, installation, CI, and release paths; runtime query support follows the verified support matrix only. | brainstorm requirement 34 + plan review pass 4 P2.1/pass 5 P1.1 |
| R14 | Keep command reference tables and user workflow documentation synchronized from the same catalog evidence and detect command additions or removals that leave stale help data. | brainstorm requirements 88-91 |
| R15 | Prove behavior with acceptance fixtures for no-argument overview, exact slash and shell lookup, free-text single-command routing, workflows, inactive suites, typo handling, ambiguity, unsupported tasks, malformed/stale evidence, and injection-like content. | brainstorm next steps 1, 7 |
| R16 | Keep defaults concise, use progressive detail, and always provide copyable follow-up commands; normal documentation links are permitted, but clickable slash execution is not required. | brainstorm requirements 2, 33 |
| R17 | Run implementation only from a feature branch containing the active `dev` integration baseline at or after observed commit `11ce531`; stop before edits if ancestry or refreshed inventories cannot be proved. | plan review P1.1 |
| R18 | Keep module-registry schema version 2 backward-compatible while extending the central ownership service and every registry/config/manifest/projection consumer; use the existing strict config parser and validated active manifest as suite-activation authority. | plan review pass 2 P1.1/P1.3/P2.1 + pass 3 P1.2 |
| R19 | Transport raw queries only through CLI-owned confined request files that are ignored in both source and consumer projects, cleaned on every prepare/consume path, and never interpolated into shell commands. | plan review P1.2 + pass 2 P2.3 |
| R20 | Pin each help record to a digest of its authoritative prompt or shell parser/help sources so implementation-only changes fail catalog checks until metadata is explicitly reviewed and repinned. | plan review pass 2 P2.4 |
| R21 | Use a separate versioned transport-envelope schema for request preparation, query completion, selection preparation, selection rendering, and transport errors; validate UUID/path derivation before every file write. | plan review pass 3 P2.2 |
| R22 | Define and statically test the invocation-argument source for each platform; do not claim byte-exact fidelity for model-visible text; record runtime status as `verified`, `unverified-no-certified-host`, or `failed`; require existing Kilo certified-host proof and prohibit runtime support claims for every unverified row. | plan review pass 3 P2.3 + pass 4 P2.1/P2.2 + pass 5 P1.1 |
| R23 | Record support status in versioned machine-readable evidence bound to a trusted pre-evidence `subjectCommit`, catalog digest/hash, canonical/generated prompt hashes, target-mapping hash, platform host version/hash, probe contract, and outcomes; require subject ancestry plus unchanged help-sensitive paths in the current/release checkout to avoid a self-referential commit hash. | plan review pass 6 P1.1 + pass 7 P1.1 |

## Required Support Matrix

| Platform | Help Asset Required | Static Overview/Query Contract Required | Runtime Status Contract | Allowed Completion Claim |
|----------|---------------------|-----------------------------------------|-------------------------|--------------------------|
| Copilot | canonical: yes | yes | Run a host probe when certified infrastructure/credentials are available; otherwise `unverified-no-certified-host`. | Runtime query support only when `verified`; otherwise canonical asset and static contract only. |
| Claude Code | generated: yes | yes | Run a CLI/host probe when available; otherwise `unverified-no-certified-host`. | Runtime query support only when `verified`; otherwise generated asset and static contract only. |
| Codex | generated: yes | yes | Run a CLI/host probe when available; otherwise `unverified-no-certified-host`. | Runtime query support only when `verified`; otherwise generated asset and static contract only. |
| OpenCode | generated: yes | yes | Run a CLI/host probe when available; otherwise `unverified-no-certified-host`. | Runtime query support only when `verified`; otherwise generated asset and static contract only. |
| Kilo | generated: yes | yes | Existing certified-host infrastructure must produce `verified`. | Generated asset, static contract, and runtime query support after the required probe passes. |

All asset and static-contract cells are required completion evidence. Runtime
probes use existing local or certified-host infrastructure only; this plan does
not create a new credentialed multi-vendor test service. A probe that runs and
fails records `failed` and blocks completion; it cannot be relabeled unverified.
For hosts without certified infrastructure, `unverified-no-certified-host` is an
allowed evidence status but forbids runtime-support wording in docs/releases.
The authoritative matrix evidence is
`.cg-docs/work-reports/2026-09-08-evidence-backed-cg-help-command-support.json`,
validated by `scripts/schemas/help_support_evidence_schema.json` and bound to the
trusted pre-evidence subject commit and generated bytes. Validators prove the
subject is an ancestor and all schema-defined help-sensitive paths remain
unchanged in the current/release checkout. Markdown summaries are not machine
authority.

## Implementation Steps

## Phase 1: Evidence And Source Contracts

### 1. Verify the integration baseline and define the shared schema layer

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R10, R11, R12, R15, R16, R17, R18, R19, R20, R21, R22
- **Files**:
  - `.github/shared/module-registry.json` (baseline input)
  - `scripts/schemas/help_catalog_schema.json` (new)
  - `scripts/schemas/help_transport_schema.json` (new)
  - `scripts/help/catalog.py` (new shared schema/runtime validator)
  - `scripts/tests/fixtures/help/` (new)
  - `scripts/tests/test_help_catalog.py` (new)
- **Details**:
  - Before any implementation edit, fetch current refs and execute an ancestry
    check that proves the feature branch contains `dev` at or after observed
    commit `11ce531`. If it does not, stop and ask the user to rebase or recreate
    the worktree; do not rebase, merge, or silently implement against `main`.
  - Refresh the prompt, module-registry, target, installer, docs, and test
    inventories after that baseline check. Record the actual base commit in the
    execution report so later deviations can distinguish repository drift from
    plan error.
  - Define catalog schema version 1 and one deterministic JSON envelope with
    `schemaVersion`, `generatorVersion`, `sourceDigest`, sorted `suites`, sorted
    `commands`, and sorted `workflows`.
  - Define command records with strict required fields: kind-qualified canonical
    `id` (`slash:<name>` or `shell:<name>`), display name, `kind`,
    `ownerModule`, sorted non-empty `supportedSuites`, `category`, `summary`,
    kind-scoped unique `aliases`,
    curated `intents`, `usage`, `examples`, `prerequisites`, `outputs`,
    `constraints`, typed `relatedCommands`, immutable canonical `sourcePath`,
    optional documentation targets, `supportedPlatforms`, `supportedOS`, and
    availability/activation references. Sidecars also pin a
    `definitionDigest` over the authoritative command source set.
  - Define workflow records with a stable ID, curated intents, prerequisites,
    ordered steps, exact command references, per-step evidence references, and
    an approved source path/section. Reject a workflow whose command, suite, or
    source cannot be resolved.
  - Define the only backend result states: `overview`, `exact`, `workflow`,
    `candidates`, `unsupported`, and `error`. `candidates` contains no more than
    three commands; `error` is never converted to `unsupported` because broken
    evidence is different from a supported no-match result.
  - Define a separate transport-envelope schema version 1 with exact operation
    discriminators: `request-prepared`, `query-completed`,
    `selection-prepared`, `selection-rendered`, and `transport-error`.
    `request-prepared` contains only schema/operation, UUID, the deterministic
    relative query path
    `.compound-gpid/runtime/help-requests/<uuid>.query.txt`, byte/expiry limits,
    and cleanup policy. Selection paths use the same UUID plus a fixed suffix.
    Reject unknown fields, absolute paths, separators inside the UUID, and every
    path that is not derived exactly from the returned UUID.
  - Nest the six semantic result states only inside `query-completed` or
    `selection-rendered`. Those payloads include catalog digest, ordered evidence
    IDs, deterministic display content, warnings, and recovery. A semantic
    `error` payload remains valid JSON on stdout and is paired with a documented
    nonzero exit code and concise stderr diagnostic.
  - Preserve a leading slash as an exact kind signal. A bare name resolves
    exactly only when one kind owns it; when slash and shell variants both
    exist, return both as `candidates`. Require qualified IDs in workflows,
    relations, model selections, and generated follow-up queries; display
    `/cg-help /cg-skill` for slash and `/cg-help shell:cg-skill` for shell.
  - Add minimal golden fixtures for all brainstorm acceptance examples before
    query implementation. Include structural samples for all result states,
    Windows/POSIX availability, inactive suites, unsupported direct agents,
    stale digests, duplicate aliases, broken relations/workflows, and
    instruction-like strings in every extractable field.
  - Implement the minimal stdlib runtime schema validator and result-envelope
    parser in this phase. Keep it behaviorally equivalent to the JSON Schema and
    reject duplicate/unknown keys without adding a runtime package dependency.
- **Test Scenarios**: feature branch missing the required dev ancestor; refreshed
  dev inventory; valid minimal/full catalog shapes; every semantic and transport
  envelope shape; UUID/path mismatch and unsafe prepare path;
  unknown schema version; missing/unknown fields; wrong types; supported OS
  values; unknown owner module; empty/unknown/unsorted supported suites; shared
  command in CG-only/CR-only/mixed states; duplicate slash/shell visible names; leading-slash and bare-name
  behavior; duplicate keys; injection-like values remain inert data.
- **Tests**: `python -m pytest scripts/tests/test_help_catalog.py scripts/tests/test_module_registry.py -q -k "schema or envelope or ownership"`
- **Acceptance criteria**: The implementation baseline contains the active dev
  architecture, and schema/runtime structural tests pass without depending on
  extraction, ranking, CLI, prompt, or future-phase production logic.

### 2. Establish canonical command, suite, and workflow metadata ownership

- **Requirements**: R2, R4, R7, R8, R9, R10, R11, R12, R14, R15, R16, R18, R20
- **Files**:
  - `.github/prompts/cg-*.help.json` (new owner-module sidecars)
  - `.github/prompts/cr-*.help.json` (new owner-module sidecars)
  - `.github/shared/shell-commands.json` (new)
  - `.github/shared/module-registry.json`
  - `scripts/cg_validate_modules.py`
  - `scripts/cg_generate_targets.py`
  - `scripts/skill_management/context.py`
  - `scripts/skill_management/services/registry.py`
  - `scripts/cg_context_budget.py`
  - `scripts/parsing_utils.py`
  - `scripts/cg_project_manifest.py`
  - `scripts/tests/test_module_registry.py`
  - `scripts/tests/test_context_budget.py`
  - `scripts/tests/test_project_manifest.py`
  - `scripts/tests/test_project_projection.py`
  - `scripts/tests/test_skill_management_read.py`
  - `scripts/tests/test_skill_management_create.py`
  - `scripts/tests/test_skill_management_migration.py`
  - `scripts/tests/test_skill_management_dispatch.py`
  - `scripts/tests/test_skill_management_audit.py`
  - `docs/workflow.md` (strict marked workflow-data blocks)
  - `scripts/tests/test_help_catalog.py`
- **Details**:
  - Add one strict `cg-<name>.help.json` or `cr-<name>.help.json` sidecar beside
    each searchable canonical prompt. Match prompt and sidecar by normalized
    basename and module-registry ownership. Sidecars are canonical owned assets
    for registry validation but are not emitted as command bodies; their content
    reaches targets only through the generated catalog. Normal command token
    counts must remain unchanged apart from unrelated baseline changes.
  - Set `ownerModule` from the registry's unique resolved owner and validate each
    sidecar's sorted `supportedSuites` against the suites whose dependency
    closures contain that owner. Suite-owned prompts normally support one suite;
    capability-owned commands can support both. Never infer one singular suite
    from a `cg-` filename.
  - Make `.github/shared/shell-commands.json` the only shell help metadata
    authority. Cover the refreshed installed lifecycle, indexing, rendering,
    publishing, token-audit, skill-management, certified Kilo launch, brain
    initialization, and summary commands. Validate kind-qualified IDs against
    committed `bin/cg-*` wrappers, installer-generated wrappers, CLI parser
    entry points, and both Windows and POSIX install inventories so metadata
    cannot advertise a command that is not installed.
  - Assign shared lifecycle and capability shell commands to their registry
    owner module and list every supported suite explicitly. Test `cg-help`,
    `cg-link`, `cg-update`, `cg-skill`, and other shared commands in both
    CG-only and CR-only closures rather than attaching them to one pseudo-suite.
  - Record `supportedOS` per shell command and cite implementation evidence for
    each OS. Preserve POSIX-only summary wrappers unless a separate approved
    implementation adds Windows equivalents; Windows queries must label those
    entries unavailable rather than reject valid metadata or advertise them as
    runnable.
  - Keep module-registry schema version 2 and add backward-compatible optional
    help and `ownershipExclusions` fields. Add a `cap-help` capability module
    that initially owns only the Phase 1 shell metadata; make both suite modules
    depend on it. Step 3 adds the generated catalog atomically with its first
    emission. Step 7 adds the `/cg-help` prompt/sidecar ownership and exact
    `suite-cg` exclusions atomically when those files first exist.
  - Extend `suite-cg` and `suite-cr` with sidecar globs, allowed command
    prefixes/kinds, evidence-backed activation guidance, and catalog ownership.
    Activation status comes from strict config and active-manifest validation in
    Step 5, not a new registry parser. Do not create `command-suites.json`.
  - Update every schema-version, owned-asset, config, manifest, generation, and
    projection consumer for the optional fields and sidecar inventory:
    `cg_validate_modules.py`, `cg_generate_targets.py`,
    `skill_management/context.py`, the central
    `skill_management/services/registry.py` ownership resolver,
    `cg_context_budget.py`, `parsing_utils.py`, and `cg_project_manifest.py`.
    Preserve exclusions through registry load, owner lookup, snapshots,
    mutations, and serialization. Unknown future schema versions still fail.
  - Populate sidecars for every `/cg-*` and `/cr-*` prompt present on the
    refreshed dev baseline, including `/cg-skill`; `/cg-help` is deliberately
    deferred to Step 7. Missing, extra, cross-owned, or prefix-mismatched
    sidecars are hard failures.
  - Add marked workflow records only to approved sections of `docs/workflow.md`.
    The visible prose remains human-readable, while the marked records provide
    exact command sequences and per-step sources. Related-command links alone
    must not be treated as proof of an ordered workflow.
  - Require every referenced command, workflow, suite, source path, and docs
    anchor to exist and be unique. Preserve source paths as canonical logical
    identities in all target copies; they are provenance, not runtime file
    dependencies and must not be rewritten to native paths.
- **Test Scenarios**: all refreshed cg/cr prompts represented exactly once;
  missing/extra/malformed sidecar; sidecar ownership or basename mismatch;
  prompt body has no help payload; normal prompt token regression; wrapper and
  installer inventory mismatch by OS; `cg-skill`, `cg-kilo`, or
  `cg-brain-init` omitted; ownership-exclusion fixture through load/snapshot/
  mutation/serialization; schema-v2 legacy record; each updated registry
  consumer; unsupported activation guidance;
  broken docs anchor; duplicate command across suites.
- **Tests**: `python -m pytest scripts/tests/test_help_catalog.py scripts/tests/test_module_registry.py scripts/tests/test_context_budget.py scripts/tests/test_project_manifest.py scripts/tests/test_project_projection.py scripts/tests/test_skill_management_read.py scripts/tests/test_skill_management_create.py scripts/tests/test_skill_management_migration.py scripts/tests/test_skill_management_dispatch.py scripts/tests/test_skill_management_audit.py -q -k "metadata or inventory or ownership or exclusion or suite or workflow or schema"`
- **Acceptance criteria**: Every in-scope cg/cr command has one adjacent
  owner-module sidecar, shell and per-OS claims match implementation evidence,
  workflows have explicit step provenance, every registry/ownership consumer
  accepts and preserves the backward-compatible optional fields, and ordinary
  prompt context contains no help data. Cross-suite `/cg-help` projection is a
  Step 7 gate because its files do not exist in this phase.

## Phase 2: Deterministic Catalog Generation

### 3. Implement strict extraction, merge, validation, and catalog emission

- **Requirements**: R4, R7, R8, R9, R10, R11, R12, R14, R15, R18, R20
- **Files**:
  - `scripts/help/catalog.py` (new)
  - `scripts/cg_generate_help_catalog.py` (new)
  - `scripts/schemas/help_catalog_schema.json` (new)
  - `.github/shared/module-registry.json`
  - `.github/shared/help-catalog.json` (generated)
  - `scripts/tests/test_help_catalog.py` (new)
- **Details**:
  - Complete the Python 3.8+ stdlib-only pipeline using the shared validator from
    Phase 1. Read only exact prompt-sidecar pairs, the shell metadata authority,
    `module-registry.json` help fields, and marked workflow records. Do not
    import prompts, wrappers, source scripts, or extracted content.
  - Emit the first valid catalog and add its exact canonical path to `cap-help`
    ownership in the same change. Registry validation must never observe an
    owned missing catalog or an emitted unowned catalog at a phase boundary.
  - Separate extraction, normalization, validation, merge, and serialization so
    the complete input graph is validated before writing the catalog.
  - Reject malformed JSON, duplicate/unknown keys, missing required values,
    unsafe or escaping paths, duplicate normalized IDs or aliases, invalid
    command prefixes, unknown/incorrect owner modules, unsupported-suite entries
    outside owner dependency closures, dangling relations, unavailable commands
    in workflows, invalid documentation anchors, sidecar/module ownership
    mismatches, unsupported OS values, and ambiguous activation evidence.
  - Compute `sourceDigest` from normalized repository-relative source identities
    plus exact source bytes for every accepted sidecar, corresponding prompt,
    module-registry help record, authoritative shell definition source set, and
    workflow record.
    Exclude timestamps, absolute host paths, and output bytes so identical inputs
    emit byte-identical catalog content.
  - Implement `--write`, `--check`, and `--stdout`. `--write` uses atomic replace
    after complete validation; `--check` recomputes expected bytes and fails on
    missing, stale, or unexpected output without mutation; `--stdout` is for
    diagnostics and tests.
  - Recompute each sidecar's `definitionDigest` from its prompt bytes. For shell
    records, hash the declared fixed parser/help/wrapper source set. Ordinary
    `--write` and catalog digest generation fail when a pinned definition digest
    differs; they never auto-repin stale metadata.
  - Provide an explicit maintainer operation to preview and refresh one named
    definition digest only after its help metadata was reviewed. It must not
    edit descriptive fields or refresh all records implicitly.
  - Emit stable UTF-8 JSON with deterministic key order, record order, newline,
    and schema/generator versions. Return distinct nonzero exit codes for source
    validation, stale output, and I/O failures with concise actionable errors.
- **Test Scenarios**: byte-identical repeated generation; shuffled input order;
  late invalid source prevents writes; stale/missing catalog; read-only output;
  interrupted atomic write; canonical path normalization on Windows/POSIX;
  malformed sidecar or module help record; prompt/parser change with unchanged
  pinned digest; explicit one-record repin; source change updates catalog digest.
- **Tests**: `python -m pytest scripts/tests/test_help_catalog.py scripts/tests/test_module_registry.py -q`
- **Acceptance criteria**: One deterministic command generates or checks the
  complete versioned catalog, all invalid source states fail before mutation,
  and no hand-maintained merged command registry exists.

### 4. Add independent catalog freshness to the maintainer workflow

- **Requirements**: R9, R12, R14, R15, R20
- **Files**:
  - `.github/prompts/cg-commit-push-pr.prompt.md`
  - `scripts/tests/test_help_catalog.py`
- **Details**:
  - In the maintainer commit workflow, run catalog `--check` whenever prompt,
    sidecar, module-registry help, shell definition, or workflow evidence changes.
    If a definition digest is stale, stop for explicit metadata review and a
    one-record repin; never auto-repin from a bulk generation path.
  - After all pinned definitions match reviewed metadata, run the help generator
    in `--write` mode before later native-target generation and staging.
    Propagate failure and never stage a partially generated catalog.
  - Keep this phase independent of `scripts/cg_generate_targets.py`; mandatory
    target-generator preflight and all affected fixture migrations occur
    together in Step 9 so Phase 2 leaves existing target tests green.
  - Treat command/sidecar additions or removals, aliases, module-registry help
    changes, shell inventory changes, and marked workflow changes as
    catalog-affecting inputs.
  - Exclude `.cg-docs/views/**` and unrelated documentation bodies from source
    digests and drift inputs.
- **Test Scenarios**: prompt/sidecar changes without catalog regeneration;
  implementation-only change with stale pinned digest; bulk auto-repin attempt;
  reviewed single-record repin; catalog-only change; unrelated prose/view change;
  commit workflow runs check/review/write in order and stops on failure.
- **Tests**: `python -m pytest scripts/tests/test_help_catalog.py -q -k "digest or stale or commit or repin"`
- **Acceptance criteria**: Catalog bytes cannot be regenerated from changed
  command definitions until their metadata is explicitly reviewed and repinned,
  and Phase 2 does not break or weaken existing native-target fixtures.

## Phase 3: Deterministic Query Service

### 5. Implement normalization, exact lookup, workflow matching, and ranking

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R10, R12, R15, R16, R18, R20
- **Files**:
  - `scripts/help/query.py` (new)
  - `scripts/cg_help.py` (new)
  - `scripts/cg_context_budget.py`
  - `scripts/parsing_utils.py`
  - `scripts/cg_project_manifest.py`
  - `scripts/tests/test_help_query.py` (new)
  - `scripts/tests/test_cg_help.py` (new)
  - `scripts/tests/test_context_budget.py`
  - `scripts/tests/test_project_manifest.py`
- **Details**:
  - Load and fully validate one catalog before answering. Runtime validation
    checks schema/generator compatibility, record invariants, internal
    references, and availability data. Recompute `sourceDigest` from the fixed
    source inventory in the installed Compound GPID clone before every query;
    a stored digest is not freshness proof. Invalid or stale evidence returns
    `error`, never a partial answer or broad-scan fallback.
  - Normalize user input with NFKC, case-folding, surrounding whitespace trim,
    shell basename handling, and whitespace/punctuation tokenization. Preserve a
    leading slash as a slash-kind selector and accept explicit `slash:` or
    `shell:` qualification. Reject NUL/control characters and enforce a
    documented query-length limit before scoring.
  - Resolve a unique kind-qualified command ID or kind-scoped alias before fuzzy
    retrieval. A bare visible name shared by slash and shell records returns an
    ambiguous candidate set; it never merges records or silently prefers a kind.
    Typo lookup uses bounded Damerau-Levenshtein distance: at most one edit for
    identifiers of 3-5 characters and at most two for identifiers of 6 or more;
    inputs shorter than three characters do not receive typo correction. A tied
    best typo never becomes `exact`.
  - Derive expected active suites and module closure through the existing strict
    config parser. When `.compound-gpid/active-manifest.json` is present, call
    the existing manifest validator and require matching config/registry digests,
    platform, suite set, module closure, and projected command evidence before
    reporting active status. A stale/incomplete/contradictory manifest returns
    `error`.
  - If strict config explicitly selects any suite or existing tooling identifies
    projection mode, require a valid active manifest; missing evidence returns
    `error`. If suites are omitted and no active manifest exists, allow the
    existing documented legacy CG default only when project-manifest/link
    tooling proves a recognized non-projected legacy installation and a bounded
    exact-path check finds every expected `suite-cg` plus `cap-help` command for
    the current platform. This check derives paths from target mapping and the
    catalog; it does not scan directories. If proof is incomplete, return
    `error`. No `unverified` command can appear in overview, exact, workflow, or
    candidate results.
  - Use named, test-visible weights over curated evidence: full ID/alias phrase,
    ID/alias tokens, intent phrases/tokens, example/usage tokens, and category.
    Require both a positive semantic field match and an absolute minimum score.
    Availability cannot lift an irrelevant command above the threshold. A
    command is active when `supportedSuites` intersects the validated active
    suite set; shared commands stay active in CG-only and CR-only projects. Use
    active status only as a tie-breaker after relevance. Resolve shell
    availability from normalized `sys.platform` and `supportedOS`, then score
    and qualified command ID provide stable ordering.
  - Match only explicit workflow records using kind-qualified command IDs.
    Return `workflow` only when its intent
    clears the workflow threshold and every step is available with complete
    evidence. Otherwise return `candidates` or `unsupported`; never synthesize a
    workflow by traversing related-command links.
  - Return at most three candidates after deduplication. Include deterministic
    match reasons, `high`/`medium`/`possible` wording from fixed score bands,
    suite/OS availability, and exact disambiguated follow-ups. Do not
    expose confidence percentages that imply calibrated probability.
  - For candidate results, issue an opaque request-bound `selectionToken` and a
    closed list of allowed candidate IDs. The model can rerank/select only those
    IDs. The backend rejects unknown, duplicate, over-limit, expired, or
    cross-request selections before deterministic rendering.
  - Build `overview` entirely from catalog categories and approved common
    workflow records. Keep output order stable and cap each category/default
    section to a configured, tested size.
- **Test Scenarios**: `/cg-skill`, `shell:cg-skill`, and ambiguous bare
  `cg-skill`; `/cg-token-audit` versus shell variant; alias collision;
  typo distance boundaries and ties; empty/long/control input; stable ranking;
  shared owner module/support set in CG-only, CR-only, and mixed modes; active
  intersection tie-break without relevance inflation; strict config reuse; valid,
  stale, missing, and contradictory active manifests; changed explicit config;
  incomplete projection; recognized complete legacy CG install; absent config
  without legacy markers; missing expected legacy command path; no unverified
  recommendation; OS-specific shell availability; inactive
  labels; missing suite evidence; workflow threshold and unavailable
  step; exactly three candidates; selection-token replay/expiry/unknown ID;
  deterministic unsupported and error states.
- **Tests**: `python -m pytest scripts/tests/test_help_query.py scripts/tests/test_cg_help.py -q`
- **Acceptance criteria**: Identical catalog/query/project evidence produces
  byte-equivalent structured results, every result state is deterministic, and
  no branch calls a model or scans beyond declared evidence paths.

### 6. Expose safe request transport, deterministic rendering, and wrappers

- **Requirements**: R1, R2, R3, R5, R6, R7, R8, R12, R13, R15, R16, R18, R19, R20, R21
- **Files**:
  - `scripts/cg_help.py` (new)
  - `bin/cg-help` (new)
  - `bin/cg-help.cmd` (new)
  - `install.ps1`
  - `scripts/install.sh`
  - `scripts/link.ps1`
  - `scripts/link.sh`
  - `tests/install.Tests.ps1`
  - `tests/bash-scripts.Tests.ps1`
  - `tests/parity.Tests.ps1`
  - `.gitignore`
  - `scripts/tests/test_cg_help.py` (new)
- **Details**:
  - Make the prompt integration a three-operation protocol with no user text in
    shell arguments: `--prepare-request --root .`, `--consume-request <uuid>`,
    and, only for candidates, `--render-selection <uuid>`. UUIDs use a strict
    lowercase hexadecimal/hyphen grammar generated by the CLI and are safe to
    pass as one validated argument.
  - `--prepare-request` exclusively creates a request and optional selection
    file under `<root>/.compound-gpid/runtime/help-requests/`, then returns only
    a schema-valid `request-prepared` transport envelope. It refuses
    symlinks, reparse-point escapes, existing files, or a root outside the
    canonical project path. Add `.compound-gpid/runtime/` to this repository's
    `.gitignore` and to the consumer managed-ignore entries maintained by both
    link implementations; parity tests must keep those entries equivalent.
  - Before any file-write call, the prompt validates the transport schema and
    `request-prepared` operation, checks the UUID grammar, derives the one
    allowed relative query path from that UUID, requires an exact match with the
    returned path, and resolves it under the canonical project root. Unknown or
    extra fields, operation mismatch, path mismatch, absolute paths, or failed
    confinement produce `transport-error` and no write.
  - The prompt writes only the invocation text supplied through the target's
    mapped argument source to the returned query path through a structured
    file-write tool, never shell redirection, interpolation, an environment
    variable, or model-generated escaping. Byte-exact fidelity is claimed only
    for a host source whose runtime probe proves it. `--consume-request`
    canonicalizes the path again, requires a regular CLI-created file, enforces
    byte/UTF-8/control/length limits, consumes it once, and cleans it up on
    success or failure. Concurrent request UUIDs remain isolated. Every prepare
    operation removes only expired files whose CLI ownership and confinement are
    proved, so interrupted sessions do not accumulate raw queries.
  - `--consume-request` returns `query-completed` with deterministic Markdown
    for `overview`, `exact`, `workflow`, `unsupported`, and semantic `error`.
    For `candidates`, it returns `selection-prepared` with bounded evidence and
    the exact UUID-derived selection path. The prompt applies the same transport
    validation before writing only an ordered JSON list of returned IDs through
    the structured file tool. `--render-selection` validates the token/list and
    returns `selection-rendered` with deterministic Markdown.
  - Resolve the only runtime catalog from the installed Compound GPID clone
    relative to the wrapper/script, not from native target-local copies or the
    consumer project. Recompute catalog and pinned definition freshness against
    the clone's fixed source inventory before processing. Use `--root` only for
    existing strict config/manifest validation, registry-declared guidance, and
    request confinement; never scan the project tree or parse suite config again.
  - Add test-only `--catalog <path> --source-root <path>` overrides as a required
    pair so fixture freshness can be recomputed. Do not permit remote URLs,
    implicit discovery, target-local overrides in prompts, or multiple
    unregistered catalog merges at query time.
  - For every operation, emit one schema-valid transport JSON envelope on
    stdout. Semantic states appear only in the allowed nested payloads. Success
    operations exit zero. Semantic `error` emits its transport envelope on
    stdout, a concise diagnostic on stderr, and a documented nonzero category
    code. A failure that cannot construct valid transport JSON uses
    stderr/nonzero only. Prompts parse a present envelope before classifying the
    exit status.
  - Follow existing wrapper and Python detection conventions. The Windows `.cmd`
    launcher must use the established `where` pre-check and version-verification
    pattern with Windows Store stub rejection. Both wrappers propagate exact
    exit status; they never receive raw user queries.
  - Add the wrapper to Windows/POSIX install, uninstall, displayed inventory,
    parity, and consumer-root tests. Prove `--root .` refers to the invoking
    project while the catalog still resolves from the installed plugin.
  - Keep stdout machine-clean in JSON mode; diagnostics and actionable failures
    go to stderr with nonzero status.
- **Test Scenarios**: every transport operation/envelope; extra field, unknown
  operation, malformed UUID, UUID/path mismatch, and absolute/escaping prepare
  path cause no file write; exact prompt-to-CLI operation strings on PowerShell/CMD and
  POSIX; quotes, semicolons, pipes, backticks, `$()`, newlines, and Unicode in the
  request file; concurrent UUIDs; symlink/reparse escape; request replacement,
  replay, expiry, prepare-time stale cleanup, and interrupted-session
  `git status` remains clean/ignored; consumer managed-ignore parity; installed
  wrapper from unrelated working directory; Python absent/Store stub;
  missing/stale catalog; malformed
  activation selector; structured error with nonzero status; transport error;
  JSON/Markdown parity and exit propagation.
- **Tests**: `python -m pytest scripts/tests/test_cg_help.py -q`; focused install,
  bash, and parity Pester files through the canonical safe runner workflow.
- **Acceptance criteria**: `cg-help` behaves identically through Windows and
  POSIX installs, transports no user text through a shell command, renders final
  output deterministically, reads only its fresh installed catalog plus existing
  strict config/active-manifest evidence, and fails without model fallback.

## Phase 4: Bounded `/cg-help` Prompt

### 7. Add the canonical prompt and enforce the answer contract

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R11, R12, R13, R15, R16, R18, R19, R20, R21, R22, R23
- **Files**:
  - `.github/prompts/cg-help.prompt.md` (new)
  - `.github/prompts/cg-help.help.json` (new)
  - `.github/shared/help-catalog.json` (regenerated)
  - `.github/shared/module-registry.json`
  - `.github/shared/target-mapping.json`
  - `scripts/schemas/target_mapping_schema.json`
  - `scripts/cg_generate_targets.py`
  - `scripts/schemas/help_support_evidence_schema.json` (new)
  - `scripts/help/support.py` (new)
  - `scripts/cg_verify_help_support.py` (new)
  - `.github/copilot-instructions.md`
  - `.github/workflows/tests.yml`
  - `scripts/cg_kilo_preflight.py`
  - `scripts/tests/test_kilo_coexistence.py`
  - `scripts/tests/test_help_support.py` (new)
  - `tests/prompt-tools.Tests.ps1`
  - `scripts/tests/test_cg_help.py`
  - `scripts/tests/test_project_projection.py`
  - `scripts/tests/test_target_mapping.py`
  - `scripts/tests/test_target_claude.py`
  - `scripts/tests/test_target_codex.py`
  - `scripts/tests/test_target_opencode.py`
  - `scripts/tests/test_target_kilo.py`
- **Details**:
  - Create `/cg-help` and its sidecar, then atomically add their exact `cap-help`
    ownership and the matching `suite-cg` broad-glob exclusions. Pin the prompt
    definition digest in the same change. Prove the prompt is present in
    CG-only, CR-only, and mixed module projections with no unmatched ownership
    pattern or double owner before testing its answer flow.
  - Keep target-mapping schema version 1 and add a backward-compatible optional
    help argument-source object. Legacy fixtures/targets without `cap-help` keep
    existing behavior when the field is absent. The production mapping and any
    fixture whose selected closure contains `cap-help` or whose source inventory
    contains `/cg-help` must provide the object; missing values then fail before
    generation. Add production completeness tests for all five targets.
  - In that object, Copilot uses the model-visible invocation tail from the current
    user request. Claude Code and Codex use their verified native `$ARGUMENTS`
    placeholder. OpenCode and Kilo use the generator-emitted `$ARGUMENTS` input
    block already established for those targets. Record the exact emitted token
    and whether fidelity is `native-placeholder` or `model-visible` per target.
  - Generate platform-specific input instructions from that mapping. Assert the
    canonical Copilot prompt does not claim placeholder substitution; assert
    Claude/Codex prompts contain the verified native placeholder; assert
    OpenCode/Kilo retain their explicit generated argument block. If current
    platform documentation or a runtime probe contradicts a mapping entry, stop
    and correct the mapping/test evidence before claiming query-mode support.
  - Add a thin `/cg-help` prompt that calls `--prepare-request --root .`, writes
    the target's mapped invocation text only through the returned structured
    file path and a non-shell file-write tool, then calls
    `--consume-request <uuid>`. No query character is interpolated into a
    command, flag, environment assignment, or redirection. For
    `model-visible` sources, describe the value as the query text received by the
    host and do not claim byte-exact fidelity to the user's original keystrokes.
  - Relay the backend's deterministic final Markdown unchanged for `overview`,
    `exact`, `workflow`, and `unsupported`. For a structured `error`, relay only
    its deterministic recovery text after validating the envelope and nonzero
    category; do not convert it to unsupported.
  - For `candidates`, use model reasoning only to choose and order IDs from the
    returned closed candidate set. Write those IDs to the prepared selection
    file through the structured file-write tool, call
    `--render-selection <uuid>`, and relay its deterministic Markdown unchanged.
    Do not compose, paraphrase, or append commands, URLs, workflow steps,
    activation guidance, or prose outside that renderer output.
  - If the wrapper is missing, no valid envelope is available, the schema/state
    is unknown, the envelope exceeds limits, or selection validation fails, stop
    with the fixed transport/evidence recovery. Never perform model-only
    retrieval, manual rendering, or a repository scan.
  - Regenerate `help-catalog.json` and all target command outputs, then pass
    catalog, mapping, generated-content, projection, and focused target checks
    before Phase 4 is complete. Do not put help metadata in the prompt body.
  - Define runtime probes for existing local or certified-host infrastructure.
    Each available probe runs overview, exact, and metacharacter-bearing
    free-text request/selection/render flows and verifies the backend's received
    query fingerprint. Build and fixture-test all probe/status logic here, but
    do not create authoritative runtime evidence in Phase 4 because later
    help-sensitive phases would invalidate it. Static mapping/generated-content
    checks remain required for every platform.
  - Extend the existing `cg-kilo-certified` workflow job and pinned
    `CG_KILO_CERTIFIED_VERSION`/`CG_KILO_CERTIFIED_SHA256` checks to run the Kilo
    `/cg-help` overview, exact, and metacharacter free-text flows through
    `test_kilo_coexistence.py`.
  - Change certified checkout behavior from the default branch to the exact
    trusted pre-evidence `subjectCommit`. On a protected `dev` push, use
    `github.sha` as that subject. For `workflow_dispatch`, require a full 40-hex
    `subject_commit`, protected
    `cg-kilo-certified` environment approval, same-repository commit validation,
    and detached checkout of that subject. Reject fork pull requests, mutable
    branch names, missing commits, SHA mismatch after checkout, and every unapproved
    path to the self-hosted runner. Reuse existing runner/version/hash variables;
    add no token, credential, or secret.
  - Define support-evidence schema version 1. The root records `subjectCommit`,
    probe commit/tree identity, and a schema-defined sorted help-sensitive path
    inventory/digest that includes catalog sources, help/query/support code,
    wrappers/install/link integration, target mapping/generator, canonical and
    generated prompts/catalogs, and host-test workflow code, but excludes the
    support JSON and Markdown execution/docs claims. Each platform row records
    catalog `sourceDigest` and file SHA-256, canonical prompt SHA-256, target
    mapping SHA-256, generated prompt SHA-256 or canonical identity, static
    results, runtime status, pinned/observed host version and executable hash
    when probed, probe-contract version, exact non-secret probe names/arguments,
    UTC run date, outcomes, and absence/failure reason.
  - Implement `cg_verify_help_support.py` to validate schema/status rules and
    recompute subject catalog/prompt/mapping/generated hashes from Git objects.
    It requires `subjectCommit` ancestry and proves every help-sensitive path is
    unchanged between subject and current. Use synthetic Git-history fixtures in
    this phase for missing/foreign/non-ancestor subjects, evidence-only follow-up
    commits, stale digests, and changed bound paths. Step 12 performs the real
    certification and creates the canonical combined JSON after all bound paths
    are frozen.
  - Store no token, credential, raw query, or secret in support evidence.
    Documentation/release prose may claim runtime support only for rows whose
    source-bound status is `verified`.
- **Test Scenarios**: prompt/sidecar ownership added only after file creation;
  unmatched exclusion; CG-only, CR-only, and mixed canonical projections;
  Copilot model-visible source; Claude/Codex native placeholders; OpenCode/Kilo
  generated argument blocks; literal/unsubstituted placeholder; host omits or
  normalizes text; synthetic default-branch checkout differs from subject commit;
  mutable dispatch ref; fork/unapproved runner input; evidence Git SHA, catalog
  digest, prompt hash, mapping hash, or generated prompt hash mismatch;
  subject is not ancestor; evidence-only follow-up commit; help-sensitive path
  changed after subject; verified,
  unverified-no-certified-host, and failed matrix fixtures; failed probes block;
  exact prompt operation
  sequence on PowerShell/CMD and POSIX; all result states; raw query never appears in shell command text;
  unknown state/schema; backend absent; valid error envelope with nonzero code;
  nonzero transport failure; invalid JSON; four candidates; selected unknown or
  injected ID; evidence tries to instruct the model; unavailable suite;
  unsupported direct-agent task; catalog regenerated after adding `/cg-help`.
- **Tests**: `python -m pytest scripts/tests/test_cg_help.py scripts/tests/test_help_support.py scripts/tests/test_project_projection.py scripts/tests/test_target_mapping.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py scripts/tests/test_target_kilo.py -q`; focused
  `tests/prompt-tools.Tests.ps1` through the canonical safe runner workflow.
- **Acceptance criteria**: Static and fixture-driven tests prove raw queries use
  only the validated transport/request path, `cap-help` keeps the command
  available in every suite projection, all five asset/static matrix rows pass,
  exact-subject certification/evidence tooling passes synthetic histories, and
  model output is limited to validated
  candidate IDs, all final user-visible content comes from deterministic Python,
  the Phase 4 catalog is fresh, and no broad/model-only fallback exists.

### 8. Add adversarial extraction and answer-boundary regression coverage

- **Requirements**: R4, R5, R6, R11, R12, R15, R19
- **Files**:
  - `scripts/tests/fixtures/help/` (new)
  - `scripts/tests/test_help_catalog.py`
  - `scripts/tests/test_help_query.py`
  - `scripts/tests/test_cg_help.py`
  - `tests/prompt-tools.Tests.ps1`
- **Details**:
  - Add fixture values that contain fake instructions, extra commands, Markdown
    links, shell metacharacters, marker-like strings, path traversal, duplicate
    keys, encoded control characters, and text asking the extractor/model to
    ignore its contract. Assert they are rejected where structurally invalid or
    preserved only as inert bounded display data.
  - Prove free-form prompt and docs prose outside exact sidecars/workflow markers
    cannot alter command fields, availability, activation, workflow order, or
    source provenance.
  - Test that the deterministic renderer rejects a selection containing a
    command ID, workflow step, activation command, or URL absent from the
    request-bound evidence envelope.
  - Test evidence truncation and oversized fields before prompt consumption.
    Reject a record or apply schema field limits deterministically; never rely on
    model context limits as validation.
  - Add false-positive queries for agents, skills, ordinary programming tasks,
    and adjacent tools so a weak token overlap does not suppress abstention.
- **Test Scenarios**: injection in every field/source class; sidecar/workflow
  marker confusion; escaping source/doc link; overlong catalog/query/field; unsupported
  tasks sharing common words such as `review`, `plan`, or `data`; attempted
  fourth recommendation; fabricated activation guidance.
- **Tests**: `python -m pytest scripts/tests/test_help_catalog.py scripts/tests/test_help_query.py scripts/tests/test_cg_help.py -q -k "adversarial or injection or unsupported or limit"`; focused prompt-contract Pester checks through the safe runner.
- **Acceptance criteria**: Untrusted source text cannot expand authority or
  output scope, and representative false positives reliably abstain.

## Phase 5: Native Targets, Install, CI, And Release

### 9. Generate equivalent native command and catalog assets

- **Requirements**: R1, R9, R10, R11, R12, R13, R15, R18, R20, R22
- **Files**:
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_cg_generate_targets.py`
  - `scripts/tests/test_target_closure.py`
  - `scripts/tests/test_target_claude.py`
  - `scripts/tests/test_target_codex.py`
  - `scripts/tests/test_target_opencode.py`
  - `scripts/tests/test_target_kilo.py`
  - `scripts/tests/test_target_drift.py`
  - `scripts/tests/test_target_ownership.py`
  - `scripts/tests/test_target_packaging.py`
  - `scripts/tests/test_target_path_safety.py`
  - `scripts/tests/test_target_mapping.py`
  - `scripts/tests/test_project_projection.py`
  - `.claude/commands/cg-help.md` (generated)
  - `.agents/commands/cg-help.md` (generated)
  - `.opencode/commands/cg-help.md` (generated)
  - `.kilo/commands/cg-help.md` (generated)
  - native `shared/help-catalog.json` files and ownership manifests (generated)
- **Details**:
  - Use the existing prompt and top-level shared-file generation paths; do not
    add target-specific help emitters or a new `outputPaths` field unless current
    mapping behavior is proven insufficient.
  - At this phase boundary, make native generation require a current catalog
    `--check` before any target write. Update every temporary generator fixture
    and helper to provide a minimal valid module registry, command sidecars,
    pinned definition digests, shell/workflow sources, and generated catalog.
    Do not add a test-only production bypass for missing help evidence.
  - Treat native `shared/help-catalog.json` files as required distribution and
    isolated-package parity assets, not the runtime source used by the PATH
    wrapper. Generated prompts call `cg-help` without `--catalog`; the wrapper
    resolves and freshness-checks the canonical catalog in its installed clone.
  - Preserve catalog-internal canonical `sourcePath` values byte-for-byte in all
    native copies. No prompt runtime catalog path exists to rewrite.
  - Include `/cg-help` in root adapters and command inventories through existing
    generic generation, not hard-coded platform lists. Prove `cap-help` produces
    the command and catalog for CG-only, CR-only, and mixed projections on each
    platform.
  - Extend exact byte/hash, target closure, determinism, ownership, packaging,
    path-safety, mapping, and stale-output tests for the new prompt and catalog
    in Claude Code, Codex, OpenCode, and Kilo. Copilot is validated against
    canonical source/catalog and projection checks.
  - Regenerate all four committed native trees and manifests only after the
    canonical catalog passes `--check`.
- **Test Scenarios**: all five platforms; custom target shared root; missing
  catalog; legacy generator fixture lacks help evidence; cap-help missing from a
  CG-only/CR-only/mixed projection; generated prompt passes forbidden `--catalog`; accidental rewrite
  of provenance; native catalog differs from canonical bytes; stale/orphaned
  help asset; second generation no-op.
- **Tests**: `python -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_closure.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py scripts/tests/test_target_kilo.py scripts/tests/test_target_drift.py scripts/tests/test_target_determinism.py scripts/tests/test_target_ownership.py scripts/tests/test_target_packaging.py scripts/tests/test_target_path_safety.py scripts/tests/test_target_mapping.py scripts/tests/test_project_projection.py -q`
- **Acceptance criteria**: Every supported platform receives the same current
  help contract and catalog through generic owned generation, all prompts use
  the one installed-clone runtime source through `cg-help`, provenance remains
  canonical, and repeat generation is byte-identical.

### 10. Enforce help gates in install, update, CI, and release workflows

- **Requirements**: R12, R13, R14, R15, R18, R19, R20, R22, R23
- **Files**:
  - `install.ps1`
  - `scripts/install.sh`
  - `scripts/link.ps1`
  - `scripts/link.sh`
  - `scripts/update.ps1`
  - `scripts/update.sh`
  - `.github/workflows/tests.yml`
  - `create-release.ps1`
  - `scripts/tests/test_update_generates_targets.py`
  - `scripts/tests/test_release_gate_targets.py`
  - `scripts/cg_verify_help_support.py`
  - `scripts/tests/test_help_support.py`
  - `.cg-docs/work-reports/2026-09-08-evidence-backed-cg-help-command-support.json`
  - `tests/install.Tests.ps1`
  - `tests/bash-scripts.Tests.ps1`
  - `tests/parity.Tests.ps1`
  - `tests/create-release.Tests.ps1`
- **Details**:
  - Install and uninstall `cg-help` with the same ownership/conflict behavior as
    existing shell commands. Never overwrite a conflicting user-owned wrapper.
  - Run catalog `--check` before install/link mutation and after update/pull
    before native generation. Consumer install/link/update must not repair or
    write canonical metadata; a stale committed catalog is a release defect.
    Pre-install/link failure makes no mutation and preserves prior content.
  - Do not claim post-pull preservation for linked platforms: current update
    performs an in-place pull, and linked consumers can observe the changed clone
    before validation completes. On post-pull failure, stop generation, report
    that linked content may be inconsistent, record the pulled commit, and give
    explicit non-destructive diagnosis/recovery guidance. Never auto-reset or
    silently roll back the clone.
  - Add focused Python help tests and catalog `--check` to Windows/macOS CI
    before native target drift. Extend the existing Python 3.8 job with a pinned
    compatible test dependency (`pytest==8.3.5` or the current verified
    Python-3.8-compatible project pin), `compileall` for every new help module,
    CLI startup/catalog generation checks, and the full focused help tests. Keep
    existing Pester/E2E jobs and safe execution rules intact.
  - Extend operational release preflight to run help catalog/query checks,
    documentation parity, all four native-target tests, and drift before the
    release API call. Add the currently omitted Kilo target test rather than
    claiming five-platform release coverage without it.
  - Make documentation/release claim checks consume the versioned support JSON,
    not the Markdown execution report. Require `subjectCommit` ancestry and
    prove the schema-defined help-sensitive path inventory, catalog digest/hash,
    prompt hashes, target-mapping hash, and generated prompt hashes are unchanged
    at the release checkout; require all asset/static rows, require Kilo
    `verified`, reject any
    `failed` row, and reject runtime-support wording for
    `unverified-no-certified-host` rows. Do not require new vendor credentials or
    create hidden network-dependent CI for unverified hosts.
  - Prove every failure prevents downstream install/update/release success
    claims. Assert no mutation only for checks that run before install/link;
    assert honest changed-state reporting for failures after an in-place pull.
- **Test Scenarios**: wrapper conflict; missing Python; stale catalog before
  install/link and after pull; failed preflight makes no install/link mutation;
  failed post-pull check reports changed clone/linked-consumer risk without reset;
  Python 3.8 import, compile, catalog, or CLI failure; support evidence from the
  default/foreign/stale SHA or mismatched digest; incompatible pytest pin;
  help tests fail in CI; release preflight omits Kilo; failed gate blocks release
  API call; successful existing install/update behavior remains unchanged.
- **Tests**: `python -m pytest scripts/tests/test_update_generates_targets.py scripts/tests/test_release_gate_targets.py scripts/tests/test_help_support.py -q`; focused install/update/release Pester files through the canonical safe runner.
- **Acceptance criteria**: Stale, invalid, or untested help assets cannot be
  newly installed, linked, reported current, or released; post-pull failures are
  reported without false preservation claims; and all five platform claims have
  matching required gates.

## Phase 6: Documentation And Final Proof

### 11. Generate command references and document the help contract

- **Requirements**: R1, R2, R5, R6, R7, R8, R14, R16, R18, R20, R23
- **Files**:
  - `scripts/help/catalog.py`
  - `docs/reference.md`
  - `docs/reference/commands.md`
  - `docs/workflow.md`
  - `docs/_wiki.yml`
  - `.github/agents/cg-wiki.agent.md`
  - `.github/skills/cg-skill-wiki/SKILL.md`
  - `scripts/check-docs-site.js`
  - `scripts/tests/test_target_documentation.py`
  - `scripts/tests/test_help_catalog.py`
  - `scripts/cg_verify_help_support.py`
  - `tests/wiki.Tests.ps1`
- **Details**:
  - Assign the catalog generator as the sole owner of help command tables. Add
    explicit help-managed section IDs for shell, `/cg-*`, and `/cr-*` tables in
    `docs/reference.md` and `docs/reference/commands.md`; preserve surrounding
    hand-written documentation.
  - Provide one explicit `--bootstrap-docs-markers` migration operation. It may
    replace only the uniquely recognized legacy command-table ranges when a
    target file has no help markers. It must preview/check expected old bounds,
    refuse missing/ambiguous/duplicate content, and write atomically. After
    markers exist, it returns zero, emits the stable structured result
    `already-bootstrapped`, and makes no file change. Normal `--write-docs` and
    `--check-docs` never bootstrap missing markers.
  - Update `docs/_wiki.yml`, the wiki agent, and `cg-skill-wiki` to mark these
    section IDs as externally generated by the help catalog. Wiki init/rebuild/
    update must preserve them byte-for-byte and must not synthesize command-table
    facts. Add wiki tests that run the rebuild path and compare the sections.
  - Render the delegated sections from the validated catalog. Do not create a
    third maintained command inventory or ask the wiki agent/model to synthesize
    catalog facts.
  - Add strict `--write-docs` and `--check-docs` operations that compare expected
    managed-section bytes. Keep writes atomic and fail on missing, duplicate, or
    malformed markers after the controlled bootstrap migration.
  - Document no-argument, exact, natural-language, workflow, inactive-suite,
    typo/ambiguity, unsupported, and evidence-error behavior with copyable
    examples.
  - Implement and fixture-test platform support rendering, but do not emit final
    runtime claims in this phase. With validated fixture evidence, render runtime
    claims only for `verified` rows and explicit static-only status for
    `unverified-no-certified-host`; reject `failed` or stale evidence. Step 12
    renders the final support section after real certification; support-doc paths
    are explicitly excluded from the help-sensitive subject inventory.
  - Explain canonical metadata ownership, generated-catalog freshness,
    module-registry suite ownership, activation-evidence requirements, inert data
    extraction, candidate limits, and recovery commands.
  - Correct existing command-table drift, including current canonical prompts
    and installed shell commands, as output of the catalog rather than isolated
    manual edits.
- **Test Scenarios**: marker bootstrap on exact legacy tables; absent/ambiguous
  legacy range; repeated bootstrap returns zero and `already-bootstrapped`
  without mutation; wiki rebuild preserves delegated
  bytes; wiki attempts to own a help section; command added/removed without docs
  update; shell inventory mismatch; broken/duplicate marker or table row; docs
  link/anchor missing; verified/unverified/failed support fixtures; attempted
  runtime claim without evidence; deferred feature advertised; second docs
  render no-op.
- **Tests**: `python -m pytest scripts/tests/test_help_catalog.py scripts/tests/test_help_support.py scripts/tests/test_target_documentation.py -q`; support-evidence validator; `node --check scripts/check-docs-site.js`; `node scripts/check-docs-site.js`
- **Acceptance criteria**: Marker migration is explicit and fail-closed, the
  catalog generator is the only help-table writer, every wiki workflow preserves
  those sections, base docs match catalog evidence exactly, support-claim
  rendering is fixture-proved but waits for Step 12 evidence, and deferred
  surfaces are not advertised as implemented.

### 12. Regenerate all assets and execute final acceptance evidence

- **Requirements**: R1, R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R16, R17, R18, R19, R20, R21, R22, R23
- **Files**:
  - `.github/shared/help-catalog.json` (generated)
  - `.claude/`, `.agents/`, `.opencode/`, `.kilo/` (generated help assets)
  - `.cg-docs/work-reports/2026-09-08-evidence-backed-cg-help-command-support.json` (generated evidence)
  - final support sections in `docs/reference.md` and `docs/reference/commands.md`
  - all source, test, install, workflow, and documentation files changed above
- **Details**:
  - Generate the canonical catalog, check it, generate all native targets twice,
    and prove the second pass changes no catalog, docs, target file, or ownership
    manifest bytes.
  - Run focused catalog, query, CLI, target, update, release, and documentation
    Python/Node suites before the broader safe project regression.
  - Run required Pester coverage only through the canonical safe runner and an
    execution subagent; inspect `tests/last-run.json` rather than injecting full
    Pester output into the implementation session.
  - After every help-sensitive implementation path and generated asset is final
    and all pre-certification tests pass, freeze the schema-defined path
    inventory. Stop for explicit user approval to create/push the pre-evidence
    `subjectCommit` through the normal git workflow; `/cg-work` must not commit or
    push implicitly. Record its full SHA and prove the remote contains that exact
    same-repository commit.
  - Trigger the protected Kilo certified-host workflow for `subjectCommit` (or
    consume its protected `dev` push run), verify detached checkout SHA, and
    download the source-bound host artifact. Run any other available host probes
    against the same subject. A failed probe blocks; unavailable non-Kilo hosts
    receive `unverified-no-certified-host`.
  - Build and validate the combined support JSON from subject Git objects and
    host artifacts. Then render final support documentation from that JSON. Only
    the support JSON, Markdown execution report, and explicitly excluded rendered
    support-doc sections may change after certification. Commit these evidence/
    docs-only changes through normal user-approved git workflow.
  - Re-run the support validator at the final checkout. If any help-sensitive
    path differs from `subjectCommit`, discard the stale certification, finish
    the change, create a new approved subject commit, and repeat certification;
    never patch the path allowlist to preserve stale evidence.
  - Execute a fixture matrix for all six result states and all brainstorm
    acceptance examples across current `/cg-*`, `/cr-*`, and per-OS shell
    inventories. Require every support row to pass asset/static checks and carry
    one explicit runtime status. Kilo must be `verified`; an executed failed
    probe on any platform blocks completion; `unverified-no-certified-host` is
    allowed for another host only with runtime claims removed from docs/releases.
  - Review the final diff for no hand-edited generated targets, no catalog/docs
    drift, no direct agent/skill entries, no more than three candidates, no
    unbounded fallback, and no direct `roadmap.json` mutation.
- **Test Scenarios**: clean repeated generation; exact acceptance matrix;
  all-target committed drift; inactive or contradictory suite selectors; fresh consumer install;
  upgrade from an install without `cg-help`; user approval unavailable for
  subject commit; remote subject SHA mismatch; Kilo artifact tests default or
  foreign commit; evidence/docs-only follow-up; bound implementation path changes
  after subject; required recertification; release preflight; existing command regressions.
- **Tests**:
  - `python scripts/cg_generate_help_catalog.py --write`
  - `python scripts/cg_generate_help_catalog.py --check`
  - `python -m compileall -q scripts/help scripts/cg_help.py scripts/cg_generate_help_catalog.py scripts/cg_verify_help_support.py`
  - `python scripts/cg_generate_targets.py --all`
  - repeat generation and repository diff/hash comparison
  - `python -m pytest scripts/tests/test_module_registry.py scripts/tests/test_context_budget.py scripts/tests/test_project_manifest.py scripts/tests/test_project_projection.py scripts/tests/test_skill_management_read.py scripts/tests/test_skill_management_create.py scripts/tests/test_skill_management_migration.py scripts/tests/test_skill_management_dispatch.py scripts/tests/test_skill_management_audit.py scripts/tests/test_help_catalog.py scripts/tests/test_help_query.py scripts/tests/test_cg_help.py scripts/tests/test_help_support.py scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_determinism.py scripts/tests/test_target_drift.py scripts/tests/test_target_closure.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py scripts/tests/test_target_kilo.py scripts/tests/test_target_documentation.py scripts/tests/test_target_ownership.py scripts/tests/test_target_packaging.py scripts/tests/test_target_path_safety.py scripts/tests/test_target_mapping.py scripts/tests/test_update_generates_targets.py scripts/tests/test_release_gate_targets.py -q`
  - canonical Pester runner through an execution subagent; inspect `tests/last-run.json`
  - protected exact-subject Kilo certification and support artifact collection
  - `python scripts/cg_verify_help_support.py --source-root . --evidence .cg-docs/work-reports/2026-09-08-evidence-backed-cg-help-command-support.json`
  - final support-doc render followed by `node scripts/check-docs-site.js`
  - `git diff --check`
- **Acceptance criteria**: Every required verification row passes, generated
  content is current and deterministic, the final support JSON validates against
  an ancestor certified subject with unchanged help-sensitive paths, all
  acceptance states have executed evidence, existing command/install behavior
  has not regressed, and unsupported suite/task/runtime claims remain explicit.

## Testing Strategy

- Use Python `pytest` for strict schema/runtime parity, extraction, source
  digests, deterministic generation, ranking, result envelopes, CLI behavior,
  native target closure, and release gates. Keep fixtures minimal and isolated
  under `scripts/tests/fixtures/help/`.
- Test pure normalization, edit distance, scoring, thresholds, availability,
  workflow validation, and rendering separately before end-to-end CLI tests.
- Test kind-qualified slash/shell identity and bare-name ambiguity before fuzzy
  scoring so collision handling cannot depend on ranking weights.
- Reuse strict config and active-manifest fixtures for suite status; do not mock
  a help-only activation parser.
- Assert exact sorted records, output bytes, exit status, stderr/stdout separation,
  match reasons, confidence labels, and absence of filesystem mutation on every
  preflight failure.
- Parameterize platform checks across Copilot canonical paths plus Claude Code,
  Codex, OpenCode, and Kilo generated paths. Test custom mapping roots through
  fixtures instead of hard-coding current target paths in production logic.
- Treat prompt bodies, sidecars, module-registry help fields, shell/workflow
  records, catalog values,
  and user queries as hostile data. Include injection, traversal, control,
  Unicode normalization, overlength, duplicate, malformed, and dangling-reference
  cases.
- Use golden acceptance fixtures for exact, typo, ambiguous, ranked, workflow,
  inactive, unsupported, and error states. Prefer property-style invariant loops
  over adding a new property-testing dependency.
- Require catalog `--check` independently from native target drift so stale
  canonical inputs cannot be hidden by consistently stale target copies.
- Change authoritative prompt/parser bytes without changing sidecar fields and
  prove pinned definition digests fail before ordinary catalog regeneration.
- Interrupt request processing after prepare/write and prove raw query files are
  ignored, ownership-confined, expired-cleaned, and absent after normal consume.
- Limit real model output to request-bound candidate IDs. Backend tests prove
  unknown or altered selections fail, deterministic rendering supplies the
  executable output boundary, and prompt tests prove no model prose is relayed.
- Validate support evidence against an ancestor `subjectCommit` and prove the
  schema-defined help-sensitive paths/hashes are unchanged in the current tree.
  Evidence/docs-only commits may follow; changed implementation bytes require a
  new subject and cannot reuse the prior green host run.
- Run Pester only through the canonical safe runner and execution-subagent
  workflow after implementation changes are complete.

## Documentation Checklist

- [ ] Document `/cg-help` no-argument overview and exact/free-text query syntax.
- [ ] Document slash/shell kind qualification and ambiguous bare-name behavior.
- [ ] Document all six result states and distinguish `unsupported` from evidence `error`.
- [ ] Include copyable examples for slash commands, shell commands, workflows, typos, inactive suites, and unsupported tasks.
- [ ] Explain the three-candidate maximum and controlled confidence wording.
- [ ] Explain that workflow steps must have explicit catalog or approved-document evidence.
- [ ] Document strict per-command sidecars and canonical shell/module-registry ownership.
- [ ] Document module-registry suite selectors, per-OS availability, and activation evidence.
- [ ] Document `cap-help` ownership and CG-only, CR-only, and mixed availability.
- [ ] Document current `/cr-*` coverage and fail-closed handling for missing or contradictory suite evidence.
- [ ] Document catalog generation, `--check`, source digest, freshness, and recovery.
- [ ] Document pinned definition digests and explicit per-record repin review.
- [ ] Generate both command reference tables from catalog evidence and remove existing drift.
- [ ] Document safe request/selection files, cleanup, and the rule that raw queries never enter shell arguments.
- [ ] Document transport envelope operations, UUID/path validation, and error/exit behavior.
- [ ] Document each platform argument source, fidelity limit, and runtime proof status.
- [ ] Publish the support matrix after all five asset/static rows pass, Kilo is runtime-verified, and every other runtime row is honestly `verified` or `unverified-no-certified-host`.
- [ ] Link support claims to versioned JSON evidence, its ancestor `subjectCommit`, and unchanged current Git/catalog/prompt/mapping/generated hashes.
- [ ] Document installed-clone runtime catalog trust, native parity-copy paths, and canonical provenance identities.
- [ ] Document the wiki ownership migration and catalog-owned help section markers.
- [ ] State that direct agents, skills, comparisons, tours, and audience personalization are deferred.
- [ ] Document install/update/CI/release gates and the five-platform support evidence.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Implementation starts from stale `main` instead of active `dev`. | Existing `/cr-*` commands and module ownership are omitted or replaced, causing wrong behavior and merge conflicts. | Require and record a `dev` ancestry preflight before edits; stop for an explicit rebase/recreated worktree when it fails; refresh all inventories after synchronization. |
| `/cg-help` remains owned only by `suite-cg`. | CR-only projections omit the cross-suite help entry point. | Put the command in shared `cap-help`, make both suites depend on it, resolve broad-glob overlap explicitly, and test CG-only/CR-only/mixed projections. |
| Registry ownership is added before the prompt/sidecar exists. | Phase validation rejects unmatched owned-asset patterns. | Create files and add exact cap-help ownership/exclusions atomically in Step 7; keep those claims out of Phase 1 evidence. |
| Optional module-registry fields break a schema-v2 consumer or leave sidecars unowned. | Generation, projection, context budgeting, or skill management fails or silently ignores help assets. | Keep version 2 backward-compatible, update every known consumer/inventory, and run registry/context/manifest/projection tests together. |
| Help metadata increases ordinary prompt context or is interpreted as instructions. | Every command pays a token cost and metadata gains unintended authority. | Use adjacent owner-module sidecars, never embed them in prompt bodies, and add token/absence plus instruction-like data tests. |
| A hand-maintained catalog duplicates command documentation. | Commands and help drift independently. | Co-locate slash sidecars, centralize shell metadata as the implementation authority, generate the merged catalog/docs, and enforce source digests plus parity checks. |
| Slash and shell commands share one visible name. | Exact lookup merges unlike behavior or returns the wrong guide. | Use kind-qualified canonical IDs, preserve slash intent, return candidates for ambiguous bare names, and qualify every relation/workflow/selection/follow-up. |
| Catalog and all native copies are consistently stale. | Native drift passes while help omits current commands. | Recompute the fixed source digest at runtime and run independent `--check` gates before install/link/update, target generation, CI, and release. |
| A changed prompt/parser keeps semantically stale sidecar text while the catalog digest is regenerated. | Freshness checks certify incorrect syntax, outputs, or constraints. | Pin per-record definition digests, block ordinary writes on mismatch, and require explicit one-record repin after metadata review. |
| Retrieval returns plausible but irrelevant commands. | Unsupported tasks receive false recommendations. | Require absolute evidence thresholds and semantic-field overlap, use active suite only as a tie-breaker, cap at three, and maintain false-positive abstention fixtures. |
| Typo tolerance changes an ambiguous query into the wrong exact command. | Users receive confidently incorrect syntax. | Bound edit distance by identifier length, require a unique best match, and return candidates on ties. |
| Related-command links are mistaken for supported workflows. | The model invents an unsafe or invalid sequence. | Return workflows only from explicit ordered workflow records with per-step evidence and available command validation. |
| Raw user queries are interpolated into shell commands. | Quotes or metacharacters split flags or execute unintended commands. | Use CLI-created confined request files populated only through a structured file-write tool; pass only validated UUIDs in shell arguments and test exact prompt operations on Windows/POSIX. |
| A prepare response points the file tool outside the owned request path. | The prompt writes untrusted text to an unrelated or sensitive file. | Validate a separate versioned transport envelope and exact UUID-derived path before every write; unknown/mismatched fields cause no mutation. |
| A host does not substitute the assumed argument placeholder. | Query mode sends a literal token, empty text, or normalized content while tests pass. | Record argument source/fidelity per target, assert generated content, require existing Kilo certification, probe other hosts when infrastructure exists, mark absent infrastructure unverified, and prohibit unsupported runtime claims. |
| Certified Kilo CI checks out the default branch instead of the feature SHA. | Old code certifies new help assets and release/docs consume unrelated evidence. | Checkout an exact protected trusted SHA, bind evidence to Git/catalog/prompt/mapping/generated hashes, validate the JSON artifact, and reject fork/mutable/unapproved dispatch inputs. |
| Host certification runs before later help-sensitive phases. | Required target/install/docs code changes invalidate evidence by design. | Build probe tooling earlier but run authoritative certification only in Step 12 after all bound paths are frozen; any later bound change forces a new subject and recertification. |
| A new required target-mapping field breaks schema-v1 fixtures before migration. | Phase 4 leaves broad target tests red or changes version-1 semantics silently. | Keep the field optional for legacy non-help mappings, require it when `cap-help` or `/cg-help` is present, test production completeness, and migrate all help-enabled fixtures in Step 9. |
| Model rendering exceeds bounded evidence or adds a command/URL. | Model-only capability claims bypass the deterministic contract. | Let the model return only request-bound candidate IDs; validate them and render all final content deterministically in Python. |
| Structured `error` and nonzero exit semantics diverge. | The prompt loses recovery evidence or makes its error branch unreachable. | Emit validated error JSON on stdout plus nonzero category/stderr, parse present envelopes before status classification, and test transport failures separately. |
| Active-suite detection scans or guesses from project content. | Token use grows and availability varies across models/platforms. | Reuse strict config and active-manifest validation under explicit `--root`; reject stale or contradictory evidence and do not add another parser. |
| Help suite status disagrees with strict config or the active manifest. | Commands are labeled active although their projection is stale or incomplete. | Reuse existing config/manifest code and digests, fail on contradictions, and avoid a second activation parser. |
| Global and target-local catalogs become competing runtime sources. | Platforms answer from different evidence or native copies are unused accidentally. | Use only the freshness-checked installed-clone catalog at runtime; treat native copies as required parity/distribution assets and prohibit prompt `--catalog` overrides. |
| Native generation changes canonical provenance. | Evidence becomes inconsistent across platforms or points to generated derivatives as authority. | Preserve catalog `sourcePath` identities and full catalog bytes across targets; no runtime path rewrite exists for catalog contents. |
| Adding a canonical catalog through the native generator violates ownership boundaries. | Target generation mutates source and hides stale inputs. | Keep a separate help generator; native generation runs `--check` and only distributes validated canonical output. |
| Shell wrappers differ by OS or disagree with metadata. | Help advertises unavailable shell commands or rejects valid POSIX-only commands. | Record/test `supportedOS`, derive runtime host availability from `sys.platform`, and compare metadata with each OS installer and wrapper inventory. |
| Wiki rebuild and catalog generation both own command tables. | One workflow overwrites the other and docs drift permanently. | Migrate to explicit catalog-owned markers, delegate them in wiki assets, bootstrap once under strict guards, and test wiki preservation. |
| A request file remains after interruption. | Sensitive query text appears as an untracked consumer-project file. | Manage the runtime ignore entry in both link implementations, clean proven expired files on prepare, consume once, and test interrupted `git status`. |
| Post-pull validation fails after linked content changed. | Consumers observe an inconsistent clone despite a false preservation claim. | Stop further generation, report the pulled commit and linked-content risk, provide explicit recovery, and never auto-reset or claim rollback. |
| New code passes only on Python 3.11. | Wrappers select Python 3.8 but help fails at import or runtime. | Pin a Python-3.8-compatible pytest, run compileall/CLI/catalog/focused tests in the existing Python 3.8 CI job. |
| Release checks omit one generated target. | Five-platform support is claimed without release evidence. | Add Kilo and help-specific checks to operational release preflight and assert failed checks prevent the release API call. |
| Generated catalog, docs, and four native trees create noisy changes. | Review misses semantic source changes among generated diffs. | Keep output deterministic, separate canonical and generated review sections, validate ownership manifests, and require second-run no-op evidence. |

## Out of Scope

- Direct-agent discovery, direct skill-asset discovery, direct invocation, or
  recommendation outside command evidence. `/cg-skill` and shell `cg-skill`
  remain in scope as documented command interfaces.
- Command-to-command comparison answers.
- Guided tours and interactive onboarding walkthroughs.
- Beginner-versus-power-user personalization or stored user profiles.
- Clickable slash-command execution or platform-specific chat UI actions.
- External web search, remote catalog lookup, or a parallel suite registry.
- Model-only semantic search, repository-wide fallback scans, embeddings, vector
  databases, or a new retrieval dependency.
- Replacing the canonical-to-native target architecture or changing generated
  ownership semantics.
- Redesigning `/cg-setup` or creating a general plugin/module marketplace.
- Adding a duplicate roadmap item; the existing `cg-help-interactive` item owns
  this work.

## Completion Contract

### Outcome

Compound GPID provides equivalent `/cg-help` assets and static contracts for
Copilot, Claude Code, Codex, OpenCode, and Kilo. On support-matrix hosts marked
`verified`, it provides evidence-backed overview, exact slash or shell guides,
bounded natural-language routing, supported workflows, and explicit unsupported
results; unverified rows are labeled without runtime claims. A versioned catalog
and deterministic Python layer supply all evidence; the model can only rerank
request-bound candidate IDs, and deterministic validation/rendering prevent
invented commands, URLs, activation actions, or workflows.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | The feature branch contains active `dev`; backward-compatible registry and central ownership consumers, schema/runtime structure, existing-command sidecar inventory, kind-qualified IDs, per-OS availability, and semantic/transport envelopes pass without not-yet-created `/cg-help` assets or future query logic. | ancestry/base record; schemas; `python -m pytest scripts/tests/test_help_catalog.py scripts/tests/test_module_registry.py scripts/tests/test_context_budget.py scripts/tests/test_project_manifest.py scripts/tests/test_project_projection.py scripts/tests/test_skill_management_read.py scripts/tests/test_skill_management_create.py scripts/tests/test_skill_management_migration.py scripts/tests/test_skill_management_dispatch.py scripts/tests/test_skill_management_audit.py -q -k "schema or envelope or ownership or exclusion or metadata or inventory"` | yes |
| V2 | 2 | Catalog generation is deterministic and provenance-complete; pinned definition digests block implementation-only semantic drift; invalid/stale evidence fails before mutation. | `python scripts/cg_generate_help_catalog.py --check`; `python -m pytest scripts/tests/test_help_catalog.py -q` | yes |
| V3 | 3 | Kind-qualified exact lookup, ambiguity, typo tolerance, weighted retrieval, exact legacy/manifest activation states, per-OS ranking, versioned safe ignored request transport, structured error exits, selection validation, and deterministic rendering pass without broad scans. | `python -m pytest scripts/tests/test_help_query.py scripts/tests/test_cg_help.py scripts/tests/test_context_budget.py scripts/tests/test_project_manifest.py -q` | yes |
| V4 | 4 | `/cg-help` files/ownership are added atomically; cross-suite projections and all five asset/static rows pass; exact-subject workflow, support schema/validator, and host probes pass fixture histories; no raw query enters the shell; no authoritative host evidence is created yet. | `cap-help` projections; target mapping/generated prompts; `.github/workflows/tests.yml`; host/support fixture tests; prompt/sidecar; catalog `--check` | yes |
| V5 | 5 | Copilot, Claude Code, Codex, OpenCode, and Kilo receive equivalent current help assets; all target fixtures pass; install/link/update/runtime freshness and per-OS wrapper checks pass; CI/release evidence gates and Python 3.8 pass with fixtures. | Full target/ownership/packaging/path/mapping suite; support-gate fixtures; install/link/update, Python 3.8, and release tests; generated manifests | yes |
| V6 | 6 | Marker bootstrap succeeds once, wiki workflows preserve catalog-owned sections, base command references match the catalog, and support-claim rendering accepts/rejects verified/unverified/failed fixture evidence correctly. | `python -m pytest scripts/tests/test_target_documentation.py scripts/tests/test_help_catalog.py scripts/tests/test_help_support.py -q`; focused `tests/wiki.Tests.ps1`; `node scripts/check-docs-site.js` | yes |
| V7 | final | All help-sensitive paths are frozen in an approved remote `subjectCommit`; Kilo certifies that exact subject; final source-bound support JSON validates unchanged paths; final support docs match allowed claims; all focused/Pester/generation/drift evidence remains green. | Step 12 sequence; certified-host artifact; versioned support JSON/validator; final docs check; `tests/last-run.json`; `/cg-work` execution report | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | all | `.github/` remains canonical; generated catalogs, docs sections, and native trees are not independent hand-maintained authorities. | Source/provenance checks, ownership manifests, and drift tests. |
| C2 | all | No unbounded repository scan, remote lookup, or model-only retrieval fallback is permitted. | Query/prompt negative tests and changed-file review. |
| C3 | all | Prompt bodies, sidecars, module-registry help fields, shell/workflow records, catalog fields, and documentation are untrusted extraction/display data. | Strict parser and adversarial fixture tests. |
| C4 | all | Direct agent/skill assets remain outside the searchable surface, while documented commands that manage them, including `/cg-skill` and shell `cg-skill`, remain covered. | Catalog inventory, exact command, and unsupported direct-asset tests. |
| C5 | all | Candidate responses contain at most three commands; workflows require explicit evidence for every ordered step. | Result-envelope, query, and prompt-contract tests. |
| C6 | all | Missing, stale, unsafe, unavailable, or unverifiable evidence fails loudly and cannot silently become a recommendation. | Failure-path tests and nonzero exit assertions. |
| C7 | all | Existing canonical-to-native generation, generated ownership, consumer install ownership, and Pester safety contracts remain intact. | Existing target/install regressions and safe runner artifact. |
| C8 | all | The installed clone is the only runtime catalog source; native copies remain byte-equivalent distribution assets and canonical provenance paths remain stable. | Cross-target bytes, wrapper resolution, freshness, and forbidden prompt-override tests. |
| C9 | all | Roadmap changes use `@cg-roadmap`; implementation does not edit `roadmap.json` directly. | Final diff review and roadmap agent record. |
| C10 | all | `/cg-help` remains available through `cap-help` in CG-only, CR-only, and mixed projections without unresolved registry ownership overlap. | Registry ownership plus five-platform projection tests. |
| C11 | all | Raw queries never enter shell arguments and request files remain CLI-owned, confined, ignored in source/consumer projects, single-use, and cleanup-bounded. | Prompt operation, path safety, managed-ignore, interruption, and `git status` tests. |
| C12 | all | Catalog generation cannot certify unchanged sidecar metadata after an authoritative prompt/parser source changes. | Pinned definition-digest mismatch and explicit repin tests. |
| C13 | all | Optional help fields remain backward-compatible with module-registry schema version 2 across every existing consumer. | Registry, generator, context, skill-management, manifest, and projection regressions. |
| C14 | all | No file-write occurs until a versioned prepare/selection transport envelope and its exact UUID-derived confined path pass validation. | Transport schema, path mismatch, unknown-field/operation, and no-write tests. |
| C15 | all | Each platform has one explicit argument source; model-visible sources carry no byte-exact claim; Kilo requires certified runtime proof; other unverified rows cannot produce runtime support claims; any executed failed probe blocks. | Target mapping/schema, generated-content, versioned support JSON, and host evidence checks. |
| C16 | all | Runtime evidence must identify a trusted pre-evidence `subjectCommit`, hash its help-sensitive implementation paths, and prove those paths unchanged at current/release checkout; the committed evidence file and Markdown are not self-referential machine authority. | Support-evidence schema/validator, protected exact-subject workflow tests, ancestry/path-diff checks, documentation and release gates. |

### Boundaries

- Allowed: canonical slash-command sidecars; canonical shell metadata and
  backward-compatible module-registry/cap-help extensions; strict config and
  active-manifest reuse; consumer managed-ignore entries;
  source-bound support evidence and validator;
  approved workflow records; catalog schema/generation; deterministic Python
  query and CLI; cross-platform wrappers and native assets; `/cg-help` prompt;
  focused tests; generated outputs; CI/release gates; user and maintainer docs.
- Out of scope: direct-agent or skill help; command comparison; guided tours;
  audience personalization; clickable slash execution; external or unregistered
  search; model-only retrieval; embeddings/vector databases; target architecture
  replacement; module marketplace; duplicate roadmap features.

### Iteration Policy

1. Before edits, prove the feature branch contains active `dev` at or after `11ce531`; stop for an explicit worktree rebase/recreation decision if it does not.
2. Implement and verify phases in order: evidence contract, catalog, query service, bounded prompt, platform/release integration, then documentation/final proof.
3. Do not populate production metadata until schema and malicious/invalid fixtures pass; do not repin definition digests without explicit per-record metadata review; do not generate native assets until canonical catalog `--check` passes.
4. Do not assign `/cg-help` prompt/sidecar ownership before Step 7 creates those files; add files, ownership exclusions, pinned digest, catalog, and projections as one green change.
5. Within a phase, fix required focused evidence and rerun only that phase's verification rows before broader regressions.
6. Under `deviation-policy: ask`, pause before changing the evidence model, scoring thresholds, supported command surface, module-registry activation contract, transport/support-evidence schemas, trusted-SHA controls, platform argument-source/support claims, phase boundaries, or listed files materially.
7. Build/test host certification earlier, but create the approved subject commit and run authoritative probes only after Steps 9-11 and every help-sensitive path are final; any later bound change invalidates evidence and requires recertification.
8. Record approved deviations and evidence impact in the execution report.
9. Mark a phase complete only after all required rows for that phase pass; mark the plan complete only after V7 and all final constraints pass.

### Blocked-Stop Conditions

- Canonical metadata cannot produce a unique, provenance-backed catalog entry
  for every advertised command.
- The implementation branch does not contain the active `dev` baseline at or
  after observed commit `11ce531`, and the user has not approved a rebase or
  replacement worktree.
- A module-registry suite lacks complete owned sidecars, safe activation
  selectors, or evidence-backed activation guidance; affected commands must not
  be advertised until the registry contract is satisfied.
- `cap-help` is absent from any selected suite closure, its exact ownership
  exclusion is unresolved, or a schema-v2 registry consumer rejects/ignores the
  optional help fields.
- `/cg-help` ownership is introduced before its prompt/sidecar exists, or the
  central ownership service and lifecycle snapshots disagree about exclusions.
- An authoritative command source changed without reviewed metadata and an
  explicit matching definition-digest repin.
- Safe request files cannot be confined, ignored in the consumer project,
  consumed once, or cleaned without risking user-owned content.
- A prepare/selection transport envelope or UUID-derived path cannot be
  validated before the corresponding structured file-write operation.
- A platform's mapped argument source is contradicted by generated output or
  runtime evidence; a probe returns `failed`; Kilo certification is unavailable;
  or docs/releases claim runtime support for an `unverified-no-certified-host`
  row. Final completion must stop.
- Certified-host evidence tests another/default/mutable commit, lacks protected
  same-repository dispatch approval, has a non-ancestor subject, or any
  help-sensitive catalog/prompt/mapping/generated/code path differs between the
  subject and current checkout.
- Strict config and active-manifest evidence disagree about selected suites,
  platform, module closure, or projected commands.
- Required behavior would need an unbounded scan, remote lookup, broad model
  inference, or a command/workflow absent from backend evidence.
- A generated target does not receive the same catalog bytes, the runtime
  wrapper does not resolve the installed-clone catalog, or provenance identity
  changes across target copies.
- Required verification cannot run through the safe runner, or required
  evidence remains failed after focused recovery.
- Continuing requires unsafe/destructive generated-tree changes, direct
  `roadmap.json` edits, or work outside the approved boundaries.
- A material deviation is required and user approval is unavailable under
  `deviation-policy: ask`.
