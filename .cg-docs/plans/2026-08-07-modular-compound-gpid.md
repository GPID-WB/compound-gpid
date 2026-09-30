---
date: 2026-08-07
title: "Modular Compound GPID architecture for technical and research suites"
status: completed
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-07-31-modular-compound-gpid-architecture.md"
language: "both"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
tags: [architecture, modularity, compound-research, technical-suite, capability-packs, registry, packaging, migration, dependency-validation]
phases: 5
completed-date: 2026-08-07
completed-phases: [1, 2, 3, 4, 5]
execution-report: ".cg-docs/work-reports/2026-08-07-modular-compound-gpid.md"
---

# Plan: Modular Compound GPID Architecture for Technical and Research Suites

## Objective

Introduce a validated three-layer module registry (kernel, capability packs,
suites) over the existing canonical `.github/` tree so that every canonical
asset has one declared owner, the dependency graph is acyclic and
cross-suite-safe, and the research suite (`cr-*`) is imported by capability
without direct technical-suite coupling — all while preserving generated-target
parity across Copilot, Claude Code, Codex, OpenCode, and Kilo and the stable
`/cg-*` user surface.

## Context

This plan implements the decision in
`.cg-docs/brainstorms/2026-07-31-modular-compound-gpid-architecture.md`:
**Approach 1 — Layered Registry Over the Canonical Tree**.

Compound GPID currently combines product infrastructure, reusable technical
knowledge, and user-facing technical workflows under the `cg-*` namespace. The
`origin/feat/compound-research-v2` branch adds a research suite under `cr-*`
(5 prompts, 11 agents, 15 skills, 2 new instruction domains — 305 files changed
vs main). The branch demonstrates valuable research behavior but exposes
incomplete architectural boundaries: the canonical target generator
discovers skills through a hard-coded `.github/skills/cg-skill-*` glob
(`scripts/cg_generate_targets.py:64`, `:542`) even though the branch contains
generated `cr-skill-*` trees.

The revamp's primary goal is **maintainability**: core maintainers must be able
to improve a shared capability or one suite without silently breaking another.
The three failure modes to prevent most aggressively are (1) a shared change
silently breaks a suite, (2) additional modules inflate routine context load,
and (3) users cannot tell which suite should own a task.

The plan extends the recently hardened canonical-native packaging foundation
(generator + per-target ownership manifests + drift tests) rather than
replacing it.

**Deliberate prioritization change**: The charter's Current Focus is "Token
Efficiency Core System." The 2026-07-31 brainstorm (Next Step #10) decided to
pursue the modular architecture first because (a) the research branch
(`feat/compound-research-v2`) has 305 unmerged files that create mounting merge
debt, (b) the hard-coded `cg-skill-*` glob blocks any multi-namespace work, and
(c) token efficiency optimizations would need rework if applied before namespace
boundaries are established. This plan represents a deliberate, documented pivot
from the charter's stated priority. The charter update (Step 14) is deferred to
Phase 5 so the modular foundation is verified before the charter reflects it.
The Token Efficiency roadmap milestone is unaffected and can resume after Phase
4 is verified.

### Brain findings incorporated

1. Canonical-native packaging foundation established the generator, ownership
   manifests, and drift tests — the registry extends this, not replaces it.
   — source: `.cg-docs/plans/2026-07-27-canonical-native-packaging-foundation.md`
2. "Capability flags, not schema forks": new platforms/modules fit as data in
   `target-mapping.json`, not code branches. The registry follows this
   data-driven principle.
   — source: `.cg-docs/solutions/environment-issues/2026-07-03-cross-agent-native-platform-trees-require-generator-drift-tests-consistent-python.md`
3. Mock-target drift gotcha: refactoring the generator API breaks mock drift
   tests — update mocks alongside the refactor.
   — source: `.cg-docs/solutions/testing-patterns/2026-05-26-mock-target-drift-after-api-refactoring.md`
4. Skill-consolidation checklist: established safe pattern for
   migrating/consolidating skills.
   — source: `.cg-docs/solutions/git-workflows/2026-03-22-skill-consolidation-checklist.md`

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Three-layer module model (kernel, capability packs, suites); one declared owner per canonical asset | Brainstorm: Architecture & Safety; Target Dependency Rules 5 |
| R2 | Central module-registry plus per-asset frontmatter ownership, validated for consistency | Open Q1; Approach 1 (validated registry) |
| R3 | Namespace-agnostic canonical discovery (no hard-coded `cg-skill-*` prefix branch) | Brainstorm; `cg_generate_targets.py:64,542` |
| R4 | Acyclic dependency graph; suites never depend on suites; capabilities never depend on suites | Target Dependency Rules 1-4 |
| R5 | Generated-target parity across all 5 platforms for both CG and CR | Brainstorm Next Step 5 |
| R6 | Characterization tests baseline CG workflows + selected CR behavior before refactoring | Brainstorm Next Step 4 |
| R7 | CR assets imported by suite/capability, not wholesale merge; direct CG deps → capability-pack deps | Brainstorm Next Step 6; Compatibility Position |
| R8 | One mixed `/cr-work` path proves no direct technical-suite dependency | Brainstorm Next Step 7 |
| R9 | Compatibility matrix covering CG-only, CR-only, mixed, legacy config, drift, context budget | Brainstorm Next Step 8 |
| R10 | Context-budget enforcement: inactive suites' instructions/skills not loaded into routine sessions by default | Brainstorm: Architecture & Safety |
| R11 | Task-oriented manual: suite selection, composition, preferences, extension rules, migration | Brainstorm Next Step 9 |
| R12 | Automated, idempotent, backward-compatible project config migration | Brainstorm: Product & Governance |
| R13 | Charter updated only after modular work is approved | Brainstorm Next Step 10 |

## Implementation Steps

## Phase 1: Registry foundation & asset inventory

### 1. Define module-registry schema and validator

- **Requirements**: R1, R2, R4
- **Files**: `.github/shared/module-registry.json` (new), `scripts/cg_validate_modules.py` (new), `scripts/tests/test_module_registry.py` (new), `.github/shared/target-mapping.json` (reference only)
- **Details**: Define a central registry that declares modules across three
  layers. A **module** is one of: `kernel`, a `capability` pack, or a `suite`.
  Each module declares: `id`, `layer`, `displayName`, `description`, optional
  `dependsOn` (module ids in lower layers only), and `ownedAssets` (glob
  patterns under `.github/`). The registry schema version is `1`. Build a
  stdlib-only validator (`cg_validate_modules.py`) that checks: schema
  conformance, unique module ids, every declared asset exists, every canonical
  asset has exactly one owning module, dependency edges respect layer rules
  (kernel depends on nothing; capabilities depend on kernel or capabilities;
  suites depend on kernel or capabilities; never suite→suite or
  capability→suite), and the dependency graph is acyclic (topological sort).
  Resolve the open question "centralized vs distributed vs combination" by
  choosing a **central registry with per-asset frontmatter cross-validation**:
  the registry is the source of truth for ownership and dependencies, and each
  canonical asset's frontmatter may optionally carry an `owner:` field the
  validator confirms against the registry. This combination catches drift in
  both directions without requiring maintainers to edit every file.
- **Test Scenarios**:
  - happy path: valid registry with kernel + 1 capability + 1 suite passes
  - edge case: asset owned by two modules → validation error
  - edge case: unowned canonical asset → validation error
  - edge case: suite→suite dependency → validation error
  - edge case: cycle in capability dependencies → validation error
  - error path: malformed JSON → clear error, nonzero exit
- **Tests**: `pytest scripts/tests/test_module_registry.py`
- **Acceptance criteria**: `cg_validate_modules.py` exits 0 on a valid seed
  registry and nonzero with a precise message on each violation class; unit
  tests cover all five edge cases.

### 2. Inventory and classify all canonical assets

- **Requirements**: R1
- **Files**: `.github/shared/module-registry.json` (extend from Step 1), `scripts/cg_validate_modules.py` (ownership-report mode)
- **Details**: Produce the initial real registry by classifying every canonical
  asset under `.github/prompts/`, `.github/agents/`, `.github/skills/`,
  `.github/instructions/`, and `.github/shared/` into one of: kernel,
  capability pack, technical suite (`cg-*`), or research suite (`cr-*`). Kernel
  owns lifecycle contracts, context loading, active state, Brain/roadmap
  integration, model/review routing, canonical generation, installation,
  release, and architecture validation. Capability packs own reusable
  implementation knowledge: language support (r, python, stata, powershell),
  testing, reproducibility, data quality, visualization, publication-output
  primitives, git workflow, pester safety. The technical suite owns `cg-*`
  command orchestration; the research suite owns `cr-*` and its domain-specific
  integrity/identification/measurement/econometric/academic-writing behavior.
  **Record ambiguous ownership explicitly** in the registry as
  `"ownership": "ambiguous"` with a resolution note rather than defaulting to a
  shared bucket. Emit an ownership report (`cg_validate_modules.py --report`)
  listing every asset and its assigned module for review. Resolve the open
  question "which `cg-*` skills are genuinely technical-suite assets vs neutral
  capabilities" here: e.g., `cg-skill-r-*`, `cg-skill-python-*`,
  `cg-skill-stata-*`, `cg-skill-pester-safety`, `cg-skill-git-workflow`,
  `cg-skill-reproducibility`, `cg-skill-render-doc` are neutral capabilities;
  `cg-skill-wb-report-writing` is a capability shared by both suites; workflow
  prompts (`cg-work`, `cg-plan`, `cg-brainstorm`, etc.) are technical-suite
  orchestration.
- **Test Scenarios**:
  - happy path: every `.github/` asset appears in exactly one module
  - edge case: ambiguous asset is flagged, not silently bucketed
  - edge case: empty module (no owned assets) → warning
- **Tests**: `python scripts/cg_validate_modules.py --report` (human review) + ownership-closure assertion in `test_module_registry.py`
- **Acceptance criteria**: ownership report shows 0 unowned assets and 0
  double-owned assets; every ambiguous entry has a resolution note.

### 3. Make canonical generation namespace-agnostic

- **Requirements**: R3
- **Files**: `scripts/cg_generate_targets.py` (modify glob logic at lines 64, 542,
  1377), `scripts/cg_audit_context.py` (update `SKILL_REF_RE` at line 115 and
  hard-coded `cg-skill-brain-query` paths at lines 1306, 1318, 1426, 1553,
  1563), `scripts/tests/test_cg_generate_targets.py` (extend),
  `scripts/tests/test_target_drift.py` (update `cg-skill-*` glob at line 166),
  `scripts/tests/test_target_claude.py` (update glob at line 51),
  `scripts/tests/test_target_kilo.py` (update glob at line 84),
  `scripts/tests/test_target_opencode.py` (update glob at line 85),
  `scripts/tests/test_target_packaging.py` (update glob at line 103),
  `scripts/tests/test_agent_adapters.py` (update `REQUIRED_CONTRACT_PHRASES`
  at line 25), `scripts/tests/test_audit_context.py` (update test fixtures),
  `scripts/validate_wb_writing_skill.py` (update `SKILL_ROOT` at line 25),
  `scripts/tests/test_target_closure.py` (update test fixtures),
  `scripts/tests/test_target_ownership.py` (update test fixtures),
  `scripts/tests/test_validate_wb_writing_skill.py` (update test paths),
  `.github/shared/target-mapping.json` (reference)
- **Details**: Replace all hard-coded `cg-skill-*` references with
  namespace-agnostic discovery. The primary changes are:
  1. Replace `CANONICAL_SKILLS_GLOB = ".github/skills/cg-skill-*/SKILL.md"`
     (line 64) with `.github/skills/*/SKILL.md` filtered by registry ownership.
  2. Replace the `cg-skill-*` glob at line 542 with registry-driven discovery:
     iterate every skill directory under `.github/skills/` whose owning module
     is declared in the registry, regardless of prefix.
  3. Update the adapter template at line 1377 to emit a namespace-agnostic
     skill path pattern (e.g., `{paths['skills']}/*/SKILL.md`).
  4. Update `cg_audit_context.py`'s `SKILL_REF_RE` regex to match any
     registered skill prefix, not just `cg-skill-`.
  5. Update all test files listed above: replace `cg-skill-*` globs with
     namespace-agnostic patterns and update fixture paths from
     `cg-skill-*` to generic registered-skill patterns.
  6. Update mock drift tests in lockstep (Brain finding 3).
  **Registry fallback**: If `module-registry.json` does not exist (e.g., in a
  downstream project that hasn't adopted the modular model), fall back to the
  current `cg-skill-*` glob-based discovery. This preserves backward
  compatibility for standalone generator use. Log a deprecation warning when
  falling back. Do NOT change the generated output format or paths — this step
  is purely about discovery.
- **Test Scenarios**:
  - happy path: with only `cg-skill-*` present and registry, generator output is byte-identical to pre-change
  - happy path: without registry, generator falls back to `cg-skill-*` glob with deprecation warning
  - edge case: add a synthetic `cr-skill-test/SKILL.md` (using `tmp_path`, not committed) → discovered and emitted to all 5 platform trees
  - edge case: skill directory with no registry owner → skipped with warning (or error, per registry strictness)
  - edge case: `test_target_drift.py` bundle check covers both `cg-skill-*` and `cr-skill-*` after glob update
  - error path: symlink in skills tree → existing ValueError preserved
- **Tests**: `pytest scripts/tests/test_cg_generate_targets.py -k namespace`, `pytest scripts/tests/test_target_drift.py`, `pytest scripts/tests/test_target_claude.py`, `pytest scripts/tests/test_target_kilo.py`, `pytest scripts/tests/test_target_opencode.py`, `pytest scripts/tests/test_target_packaging.py`, `pytest scripts/tests/test_agent_adapters.py`
- **Acceptance criteria**: generator discovers skills by registry ownership not
  prefix; generator falls back gracefully without registry; drift tests stay
  green for CG; drift test bundle check covers both `cg-skill-*` and
  `cr-skill-*` patterns; a synthetic cr-skill (in `tmp_path`) is emitted to all
  generated trees; all 15+ test files with hard-coded `cg-skill-*` references
  are updated.

## Phase 2: Dependency validation & characterization

### 4. Add dependency-closure and cross-suite validation CI gates

- **Requirements**: R4
- **Files**: `scripts/cg_validate_modules.py` (extend), `.github/workflows/tests.yml` (add gate), `scripts/tests/test_module_registry.py` (extend)
- **Details**: Wire `cg_validate_modules.py --check-dependencies` into the CI
  test workflow as a release gate alongside the existing
  `test_target_drift.py` and `test_release_gate_targets.py`. The gate fails on:
  any unresolved runtime dependency (a canonical path referenced by an asset
  not in the referencing module's transitive dependency closure), any
  cross-suite reference (a `cr-*` asset referencing a `cg-*` asset owned by the
  technical suite, or vice versa, except through a shared capability pack), and
  any cycle. **New infrastructure required** (this is not a simple reuse of
  existing code):
  1. **Reference scanner**: Reuse the generator's `CANONICAL_RUNTIME_PATH_PATTERN`
     (line 68-71) to find all `.github/...` path references in every canonical
     asset body. The regex finds references but does not resolve ownership.
  2. **Asset→module resolver**: New function that maps a canonical path
     (e.g., `.github/skills/cg-skill-r-analytical/SKILL.md`) to its owning
     module by scanning the registry's `ownedAssets` globs.
  3. **Transitive closure algorithm**: New function that computes the full
     dependency closure for a module (its `dependsOn` plus their `dependsOn`,
     recursively) and detects cycles via topological sort.
  4. **Cross-suite checker**: New function that verifies no asset in one suite
     references an asset owned by another suite (except through shared
     capability packs).
  The existing `CANONICAL_RUNTIME_PATH_PATTERN` is the input to step 1; steps
  2-4 are entirely new.
- **Test Scenarios**:
  - happy path: valid closure passes
  - edge case: cr-agent references a cg-skill owned by technical suite → gate fails
  - edge case: cr-agent references a capability pack it depends on → passes
  - edge case: capability references a suite → gate fails
  - error path: broken reference path → clear error
- **Tests**: `pytest scripts/tests/test_module_registry.py -k dependency`, CI gate run
- **Acceptance criteria**: CI gate runs on every PR touching `.github/` and
  fails on the three violation classes above; no false positives on the real
  registry.

### 5. Add characterization tests for CG workflows and CR baseline

- **Requirements**: R6
- **Files**: `scripts/tests/test_cg_characterization.py` (new), `scripts/tests/test_cr_baseline.py` (new)
- **Details**: Before refactoring orchestration or importing CR content,
  capture behavioral baselines. For CG: snapshot the current generated-target
  manifest (per-platform file list + sha256) as the CG characterization baseline
  and assert the generator reproduces it exactly; snapshot key `/cg-work`,
  `/cg-plan`, `/cg-brainstorm` prompt bodies' structural elements (required
  section headings). For CR: extract content from the remote research branch
  using `git show origin/feat/compound-research-v2:<path>` for each asset
  (do NOT checkout or cherry-pick the branch into the worktree). Extract a
  minimal behavioral baseline — the 5 cr-prompts' required sections, the 11
  cr-agents' frontmatter schema, and the 14 cr-skills' SKILL.md frontmatter +
   bundle closure — as fixtures and assert ported versions preserve them. Verify
   the actual asset counts on the branch before committing fixtures. These are
   **characterization tests** (pin current behavior), not specification tests;
  they are allowed to change only when a step explicitly updates behavior.
- **Test Scenarios**:
  - happy path: CG baseline matches current generator output
  - edge case: generator output changes → characterization fails loudly (intended)
  - edge case: CR baseline fixture ported with structural drift → fails
- **Tests**: `pytest scripts/tests/test_cg_characterization.py`, `pytest scripts/tests/test_cr_baseline.py`
- **Acceptance criteria**: both suites green against current main (CG) and
  extracted CR fixtures; baselines committed as fixtures for regression
  detection.

### 6. Prove CG/CR generated-target parity across all platforms

- **Requirements**: R5
- **Files**: `scripts/tests/test_target_drift.py` (extend), `scripts/tests/test_release_gate_targets.py` (reference)
- **Details**: Extend the drift test to assert that, once `cr-*` assets are
  discovered by the generator (Step 3), all 5 platform trees (copilot,
  claude-code, codex, opencode, kilo) receive complete and parity-correct CR
  output alongside CG output. Assert: every cr-prompt, cr-agent, cr-skill, and
  cr-instruction appears in every generated tree; ownership manifests list
  them; runtime dependency rewriting resolves cr-* references correctly; no
  orphaned or stale files. This is the "prove complete CG/CR parity" gate from
  brainstorm Next Step 5. Run before importing real CR content (synthetic
  fixtures suffice) to prove the pipeline; re-run after real import in Phase 3.
- **Test Scenarios**:
  - happy path: 5-platform parity for CG+CR with synthetic fixtures
  - edge case: one platform missing a cr-skill → drift fails
  - edge case: cr-agent runtime reference unresolved → fails
- **Tests**: `pytest scripts/tests/test_target_drift.py`
- **Acceptance criteria**: drift test green across the full 5-platform matrix
  for both namespaces.

## Phase 3: Research suite migration

### 7. Migrate main's assets to declared module ownership

- **Requirements**: R1, R2
- **Files**: `.github/shared/module-registry.json` (finalize from Step 2), all `.github/` canonical assets (frontmatter `owner:` optional cross-validation)
- **Details**: Finalize the registry so that every existing main asset is owned
  by exactly one module. This is mostly completing Step 2's classification, but
  this step commits the registry as the enforced source of truth and removes
  all `"ownership": "ambiguous"` entries by resolving them. If neutral
  capability identifiers are introduced (e.g., a capability pack id that is not
  a `cg-*` prefix), add **compatibility aliases** so existing `cg-skill-*`
  identifiers keep resolving (Brainstorm Compatibility Position: "Existing
  shared `cg-skill-*` identifiers may require compatibility aliases"). Keep all
  user-facing `cg-*` command names stable — aliases are registry-internal.
  Run the generator and confirm main's generated trees are unchanged (the
  ownership layer is metadata; output bytes should not drift unless a real
  content change is made).
- **Test Scenarios**:
  - happy path: registry validates, generator drift green, no ambiguous entries remain
  - edge case: an asset's `owner:` frontmatter disagrees with registry → validator catches
  - edge case: alias points to a renamed capability → resolves correctly
- **Tests**: `python scripts/cg_validate_modules.py`, `pytest scripts/tests/test_target_drift.py`, `pytest scripts/tests/test_cg_characterization.py`
- **Acceptance criteria**: 0 ambiguous ownership entries; CG characterization
  baseline unchanged; drift green.

### 8. Import CR intellectual content by suite and capability

- **Requirements**: R7
- **Files**: `.github/prompts/cr-*.prompt.md` (new, from research branch), `.github/agents/cr-*.agent.md` (new), `.github/skills/cr-skill-*/` (new), `.github/instructions/latex.instructions.md`, `.github/instructions/math.instructions.md` (new), `.github/shared/module-registry.json` (add research suite + its capability deps), `scripts/cg_validate_modules.py`
- **Details**: Import the research branch's intellectual content
  capability-by-capability and suite-by-suite, **never as a wholesale merge**
  (Brainstorm NS6; Constraint C4). Classify each CR asset before import using
  the preliminary mapping below (verify against actual branch content in Step 5
  before execution):

  | CR Asset Type | Examples (preliminary) | Target Module | Rationale |
  |---|---|---|---|
  | cr-prompts (5) | cr-brainstorm, cr-plan, cr-work, cr-review, cr-compound | Research suite | Command orchestration is suite-specific |
  | cr-agents: domain-specific (est.) | identification, measurement, econometric reasoning | Research suite | Domain-specific reasoning |
  | cr-agents: generic (est.) | code-quality, testing, reproducibility (if duplicated) | Capability packs | Reusable across suites |
  | cr-skills: domain-specific (est.) | academic-writing, identification, measurement, econometric-reasoning | Research suite | Domain knowledge |
  | cr-skills: generic (est.) | publication-output, replication, research-eda | Capability packs | Reusable implementation knowledge |
  | cr-instructions (2) | latex, math | Capability packs | Language support, not suite-specific |

  Replace any direct CG-owned dependency with a capability-pack dependency
  (Brainstorm Compatibility Position: "CR behavior is preserved while its direct
  dependencies on CG-owned behavior are replaced with capability-pack
  dependencies"). Add each imported asset to the registry with correct ownership
  and dependencies, then run the cross-suite validation gate (Step 4) after each
  batch to catch coupling early. Use the skill-consolidation checklist (Brain
  finding 4) for the skill imports. **Resolve all `"ownership": "ambiguous"`
  entries** from the classification table before completing this step.
- **Test Scenarios**:
  - happy path: a cr-skill imports cleanly, validates, generates to 5 platforms
  - edge case: cr-agent references a cg-skill directly → cross-suite gate fails (fix by routing through capability)
  - edge case: cr-skill bundle reference unresolved → generator fails loudly
  - error path: wholesale merge attempted → rejected by process (git diff --stat shows selective files only)
- **Tests**: `python scripts/cg_validate_modules.py --check-cross-suite`, `pytest scripts/tests/test_target_drift.py`, `pytest scripts/tests/test_cr_baseline.py`
- **Acceptance criteria**: all CR assets imported and owned; cross-suite gate
  green (no direct technical-suite dependency); CR baseline tests pass; 5
  platform drift green.

## Phase 4: Integration proof & compatibility

### 9. Prove one mixed `/cr-work` end-to-end path

- **Requirements**: R8
- **Files**: integration test artifact in `.cg-docs/work-reports/`, `.github/prompts/cr-work.prompt.md` (reference), `.github/agents/cr-*.agent.md` (reference)
- **Details**: Demonstrate one complete mixed `/cr-work` path that uses
  research reasoning (a cr-agent), R or Python implementation (a capability
  pack skill), testing (a capability pack), reproducibility (a capability
  pack), and publication output (a capability pack) — with **no direct
  dependency on the technical suite** (Brainstorm NS7). Document the path's
  dependency resolution through the registry to prove every reference resolves
  via kernel or a capability pack, never the technical suite. This is the
  architectural proof that the modular boundaries hold under real use. Record
  the run as a work-report artifact serving as V10 evidence.
- **Test Scenarios**:
  - happy path: mixed cr-work path completes using only kernel + capabilities
  - edge case: path touches a technical-suite asset → flagged as boundary violation
- **Tests**: integration-test work-report artifact + `python scripts/cg_validate_modules.py --check-cross-suite` on the path's resolved dependencies
- **Acceptance criteria**: documented end-to-end path resolves entirely
  through kernel and capability packs; cross-suite gate confirms no
  technical-suite dependency.

### 10. Document compatibility matrix

- **Requirements**: R9
- **Files**: `.cg-docs/compatibility-matrix.md` (new)
- **Details**: Document and verify the six compatibility combinations:
  CG-only projects, CR-only projects, mixed projects, legacy (pre-modular)
  configuration, generated-target drift scenarios, and context-budget limits.
  For each, specify expected installed assets, loaded context, and any migration
  steps. This is the documentation counterpart to the automated tests in Steps
  11 and 12.
- **Test Scenarios**:
  - happy path: matrix covers all six combinations with expected outcomes
  - edge case: legacy config without `suites:` maps to CG-only behavior
- **Tests**: documentation completeness check (all six combinations present)
- **Acceptance criteria**: compatibility matrix documented and covers all six
  combinations.

### 11. Design and implement context-budget enforcement

- **Requirements**: R10
- **Files**: `scripts/tests/test_context_budget.py` (new),
  `scripts/cg_context_budget.py` (new),
  `.kilo/shared/context-loading.contract.md` (extend),
  `compound-gpid.local.md` (schema extension)
- **Details**: Context-budget enforcement operates at **two levels**:
  1. **Generator-level (code-enforced)**: The generator filters which
     platform-tree files are emitted based on the active suites declared in
     `compound-gpid.local.md`. A CG-only project's generated trees omit CR
     instructions and CR skill adapters entirely. This is verifiable by
     automated tests.
  2. **Instruction-level (AI-agent compliance)**: The context-loading contract
     (`.kilo/shared/context-loading.contract.md`) is extended with a new stage
     rule: "Before loading a skill or instruction file, check whether its
     owning module's suite is declared active in `compound-gpid.local.md`'s
     `suites:` field. If not active, skip it." This is a Markdown instruction
     for AI agents — it is **not programmatically enforceable** and cannot be
     verified by automated tests. Document this limitation explicitly.
  **Schema extension**: Add `suites:` field to `compound-gpid.local.md`
  frontmatter schema. Allowed values: list of suite ids (e.g., `[cg]`,
  `[cg, cr]`). Default when absent: `[cg]` (backward-compatible with existing
  configs). Example:
  ```yaml
  suites: [cg, cr]
  ```
  **Implementation**: `cg_context_budget.py` reads the registry and the active
  suites list, computes the set of loadable modules (active suites + their
  transitive dependencies + kernel), and produces a filtered asset manifest.
  The generator uses this manifest to emit only loadable assets to platform
  trees. Measure baseline context size for CG-only and assert it does not
  increase post-modularization (Constraint C5).
- **Test Scenarios**:
  - happy path: CG-only session loads only cg + kernel + shared capabilities (context budget unchanged)
  - edge case: mixed project loads both suites' assets
  - edge case: CR-only project loads cr + kernel + shared capabilities
  - edge case: asset owned by a capability pack used by both suites → loaded regardless of suite selection
  - edge case: asset owned by inactive suite → excluded from generated tree
- **Tests**: `pytest scripts/tests/test_context_budget.py`
- **Acceptance criteria**: context-budget test confirms CG-only load is
  unchanged or smaller; generator-level filtering is automated and verified;
  instruction-level limitation is documented.

### 12. Implement config migration

- **Requirements**: R12
- **Files**: `scripts/tests/test_config_migration.py` (new),
  `scripts/cg_migrate_config.py` (new), `compound-gpid.local.md` (reference)
- **Details**: Provide `cg_migrate_config.py` that upgrades a project's
  `compound-gpid.local.md` to the modular schema (adds `suites:` field with
  `[cg]` default) idempotently and backward-compatibly: an old config without
  `suites:` is read as `cg`-only and migrated non-destructively. Re-running
  the migration is a no-op. The script must be stdlib-only and must not
  overwrite existing frontmatter fields.
- **Test Scenarios**:
  - happy path: legacy config without `suites:` → migrated to `[cg]`, backward compatible
  - edge case: re-running migration → no-op
  - edge case: config already has `suites:` → no change
  - edge case: config has other frontmatter fields → preserved
- **Tests**: `pytest scripts/tests/test_config_migration.py`
- **Acceptance criteria**: migration is idempotent and backward-compatible
  across all matrix combinations.

## Phase 5: Documentation & charter

### 13. Write task-oriented modular manual

- **Requirements**: R11
- **Files**: `docs/modular-guide.md` (new), `docs/reference.md` (cross-link), `docs/skills/index.md` (cross-link)
- **Details**: Write a task-oriented manual (Brainstorm NS9) explaining: how to
  choose between the technical (`/cg-*`) and research (`/cr-*`) suites with
  concise help and examples; how suites compose reusable capabilities
  automatically (users should not need dependency names); module preferences
  (technical-only, technical-plus-research) and how they shape setup, help,
  and defaults; extension rules for maintainers (how to add a capability pack
  or a future suite via the registry); and migration from the current
  single-suite package. Keep it task-oriented (start from "I want to do X"),
  not architecture-internal. Cross-link from the existing `docs/reference.md`
  and `docs/skills/index.md`. This addresses failure mode #3 (users cannot tell
  which suite should own a task).
- **Test Scenarios**:
  - happy path: a new user follows the guide to run a research task via `/cr-work`
  - edge case: a maintainer follows extension rules to add a capability and it validates
- **Tests**: documentation presence + cross-link check in `test_target_documentation.py` (extend)
- **Acceptance criteria**: `docs/modular-guide.md` exists, covers all five
  topics, and is linked from the reference docs.

### 14. Update project charter (deferred, post-approval)

- **Requirements**: R13
- **Files**: `compound-gpid.md` (modify, deferred until Phases 1-4 approved)
- **Details**: Only after the modular foundation is approved and verified
  (Brainstorm NS10), update `compound-gpid.md` Key Deliverables to include the
  modular layer model, capability packs, and the research suite, and update
  Current Focus to reflect the modular architecture as an active workstream
  alongside or succeeding token efficiency. This is deliberately the last step:
  the charter reflects approved, verified direction, not in-flight
  experiments. Because this modifies an existing protected file, it requires
  explicit user approval at execution time under deviation-policy `ask`.
- **Test Scenarios**:
  - happy path: charter Key Deliverables + Current Focus updated and consistent with verified registry
  - edge case: attempted before Phase 1-4 verification → blocked-stop
- **Tests**: charter consistency check (manual + `Invoke-Pester tests/local-config.Tests.ps1 -Quiet` if schema-relevant)
- **Acceptance criteria**: charter reflects the modular architecture and is
  consistent with the verified registry and compatibility matrix.

## Testing Strategy

- **Unit tests**: module-registry validator, config migration, context-budget
  loader — all stdlib-only Python (`pytest`).
- **Characterization tests**: CG generator-output baseline + CR structural
  baseline, committed as fixtures, run before and after refactoring.
- **Drift tests**: extend `test_target_drift.py` to cover CG+CR across 5
  platforms; release gate wraps it.
- **Cross-suite gate**: `cg_validate_modules.py --check-cross-suite` as a CI
  gate on every `.github/` change.
- **Integration proof**: one documented mixed `/cr-work` path as a work-report
  artifact with dependency-resolution evidence.
- **Pester parity**: `tests/prompt-tools.Tests.ps1`, `tests/install.Tests.ps1`
  (single-file, `-Quiet`, per Pester safety skill) to confirm `/cg-*` dispatch
  and install behavior unchanged.
- **No new third-party dependencies**: all new scripts are stdlib-only,
  consistent with the existing generator.

## Documentation Checklist

- [x] `docs/modular-guide.md` — task-oriented suite selection, composition, preferences, extension, migration (Step 13)
- [x] `.cg-docs/compatibility-matrix.md` — CG-only/CR-only/mixed/legacy/drift/context-budget matrix (Step 10)
- [x] `docs/reference.md` — cross-link to modular guide
- [x] `docs/skills/index.md` — cross-link to modular guide
- [x] `.github/shared/module-registry.json` — documented schema (in-file description)
- [x] `compound-gpid.md` — Key Deliverables + Current Focus (Step 14, completed)

## Risks & Mitigations

| ID | Risk | Likelihood | Impact | Mitigation |
|----|------|-----------|--------|------------|
| RK1 | Registry granularity too fine → dependency graph harder to maintain than current shared layer | Medium | High | Start coarse (few capability packs); split only when a real cross-suite dependency demands it (Iteration Policy 4) |
| RK2 | Namespace-agnostic generator change breaks existing target parity | Medium | High | Characterization tests (Step 5) pin CG output; drift tests gate every step; update mocks in lockstep (Brain finding 3) |
| RK3 | CR import introduces unresolvable cross-suite coupling | Medium | High | Import capability-by-capability; run cross-suite gate (Step 4) after each batch; route through capability packs, not direct refs |
| RK4 | Context inflation for CG-only sessions | Medium | High | Context-budget test (Step 11) asserts CG-only load unchanged/smaller; registry drives loading, not eager import |
| RK5 | Ambiguous asset ownership defaulted to shared, recreating Approach 3's weak bucket | Medium | Medium | Registry requires explicit resolution; `"ambiguous"` is a flagged state with a note, never silent (Step 2) |
| RK6 | Config migration breaks existing projects | Low | High | Migration is idempotent, backward-compatible, non-destructive; legacy config reads as `[cg]` (Step 12) |
| RK7 | Wholesale research-branch merge slips in | Low | High | Process constraint C4 + git diff review; import is selective file-by-file per Brain finding 4 checklist |
| RK8 | Charter updated prematurely before verification | Low | Medium | Step 14 is last and blocked until Phases 1-4 verified; deviation-policy `ask` requires explicit approval |
| RK9 | Instruction-level context-budget enforcement is not programmatically verifiable | Medium | Medium | Generator-level filtering is code-enforced and testable; instruction-level rules are documented as AI-agent compliance (not automated); test coverage focuses on generator-level enforcement (Step 11) |
| RK10 | Registry fallback allows drift in downstream projects without registry | Low | Medium | Fallback logs deprecation warning; CI gate requires registry; fallback is for standalone generator use only (Step 3) |

## Out of Scope

- Physical package relocation to `packages/kernel/`, `packages/suites/`, etc.
  (Approach 2) — `.github/` remains the canonical runtime source.
- Public third-party plugin API or marketplace.
- Future suites beyond technical and research (writing, presentation,
  dashboard, application) — designed for in the registry, not implemented.
- Wholesale merge of the `feat/compound-research-v2` branch — import is
  selective, capability-by-capability.
- Renaming existing user-facing `cg-*` command or skill identifiers — registry
  aliases preserve stability.
- Runtime model-selection changes — the registry is ownership/dependency
  metadata, not a model-routing layer.

## Completion Contract

### Outcome

Compound GPID runs on a validated three-layer module registry (kernel /
capability packs / suites) where every canonical asset has one declared owner,
the dependency graph is acyclic and cross-suite-safe, the research suite
(`cr-*`) is imported by capability without direct technical-suite coupling, and
a mixed `/cr-work` path is proven end-to-end — all with generated-target parity
across Copilot, Claude Code, Codex, OpenCode, and Kilo.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Module-registry schema validates; validator unit tests pass | `pytest scripts/tests/test_module_registry.py` | yes |
| V2 | 1 | Every canonical asset has a valid declared owner | `python scripts/cg_validate_modules.py --check-ownership` | yes |
| V3 | 1 | Generator discovers all skills namespace-agnostically | `pytest scripts/tests/test_cg_generate_targets.py -k namespace` | yes |
| V4 | 2 | Dependency graph acyclic; no cross-suite dependencies | `python scripts/cg_validate_modules.py --check-dependencies` | yes |
| V5 | 2 | CG characterization tests pass (no behavior regression) | `pytest scripts/tests/test_cg_characterization.py` | yes |
| V6 | 2 | CR baseline tests pass (selected behavior preserved) | `pytest scripts/tests/test_cr_baseline.py` | yes |
| V7 | 2 | Generated-target parity across 5 platforms for CG+CR | `pytest scripts/tests/test_target_drift.py` | yes |
| V8 | 3 | Main assets migrated to declared ownership; drift green | `pytest scripts/tests/test_target_drift.py` | yes |
| V9 | 3 | CR assets imported by capability; no direct CG dependency | `python scripts/cg_validate_modules.py --check-cross-suite` | yes |
| V10 | 4 | Mixed `/cr-work` path runs without technical-suite dependency | integration-test artifact in `.cg-docs/work-reports/` | yes |
| V11 | 4 | Compatibility matrix documented and verified | `.cg-docs/compatibility-matrix.md` | yes |
| V12 | 4 | Context-budget enforcement: generator-level filtering verified; instruction-level limitation documented | `pytest scripts/tests/test_context_budget.py` | yes |
| V13 | 4 | Config migration idempotent + backward-compatible | `pytest scripts/tests/test_config_migration.py` | yes |
| V14 | final | Task-oriented modular manual published | `docs/modular-guide.md` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Existing `/cg-*` commands remain usable | `Invoke-Pester tests/prompt-tools.Tests.ps1 -Quiet` |
| C2 | 1 | `.github/` remains canonical runtime source (no physical relocation) | registry validator: no `packages/` source tree |
| C3 | 2 | Generated-target drift tests remain green | `pytest scripts/tests/test_target_drift.py` |
| C4 | 3 | No wholesale research-branch merge | `git diff --stat` confirms selective import |
| C5 | 4 | Context size does not increase for CG-only sessions | context-budget test baseline comparison |
| C6 | 4 | Instruction-level context-budget limitation documented | Step 11 acceptance criteria |
| C7 | final | Single repo, single install path, one release train | `Invoke-Pester tests/install.Tests.ps1 -Quiet` |

### Boundaries

- Allowed: logical module registry over the existing `.github/` tree; per-asset
  frontmatter ownership cross-validation; compatibility aliases for `cg-*`
  identifiers; data-driven suite/capability declarations; incremental CR import
  capability-by-capability.
- Out of scope: physical package relocation (Approach 2); public third-party
  plugin API/marketplace; future suites (writing/presentation/dashboard/
  application — designed for, not implemented); wholesale research-branch
  merge; renaming existing `cg-*` user-facing identifiers.

### Iteration Policy

1. **deviation-policy: ask** — pause before any deviation; record the decision
   in the execution report.
2. Import CR content capability-by-capability; run characterization tests after
   each import to catch coupling early.
3. Keep `cg-*` user-facing identifiers stable; use registry aliases, not
   renames.
4. Registry granularity starts coarse; split a capability only when a real
   cross-suite dependency demands it.
5. Defer the charter update (Step 14) until the modular foundation is approved
   and verified.

### Blocked-Stop Conditions

- The registry validator cannot be made to pass for the real asset inventory.
- The generator namespace change breaks target parity and cannot be resolved
  without physical relocation.
- CR import introduces an unresolvable cross-suite dependency.
- Context-budget regression for CG-only sessions cannot be reversed.
- Config migration cannot be made backward-compatible.
- Defaults from `.kilo/shared/goal-execution.contract.md` also apply (required
  verification cannot run through the safe runner; required evidence fails
  after allowed recovery; a required deviation under `ask` without user
  approval; a required deviation under `strict`; a protected boundary must be
  crossed; execution report cannot be created; plan lacks a completion
  contract; completion claimed from static inspection alone).
