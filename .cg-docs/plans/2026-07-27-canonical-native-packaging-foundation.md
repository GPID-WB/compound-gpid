---
date: 2026-07-27
title: "Canonical-to-Native Packaging Foundation"
status: active
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-07-27-canonical-native-packaging-foundation.md"
language: "Python"
estimated-effort: "large"
deviation-policy: "ask"
tags: [packaging, generator, native-targets, skills, dependency-closure, manifests, path-safety, drift, ci]
phases: 7
execution-report: ".cg-docs/work-reports/2026-07-28-canonical-native-packaging-foundation.md"
completed-phases: [1, 2, 3]
current-phase: 4
failing-steps: [8]
---

# Plan: Canonical-to-Native Packaging Foundation

## Objective

Make native target generation complete, deterministic, confined, owned, and
independently usable before any external skill intake begins. Compound GPID
will package canonical skills as atomic directory bundles, provide target-local
runtime dependency closure for commands, agents, skills, instructions, prompt
support, and shared contracts, and enforce safe generation through checksummed
ownership manifests, fail-closed validation, CI, and release gates.

## Context

The approved brainstorm chose **Atomic Mirrors With Owned Manifests**. The
existing `scripts/cg_generate_targets.py` scans only each canonical skill's
`SKILL.md`; it does not package progressive-disclosure resources, prompt
support files, instructions, or target-local shared contracts. Its dry-run
manifest describes paths rather than emitted bytes and ownership, validation
does not confine all configured paths, writes occur incrementally, and there is
no safe stale cleanup.

The current native-target foundation remains authoritative:

- `.github/` is the canonical source; `.claude/`, `.agents/`, and `.opencode/`
  are committed generated product surfaces.
- `.github/shared/target-mapping.json` is the platform-generic mapping, and
  capability flags and configured `outputPaths` remain the extension model.
- Directory install units remain junctions on Windows and symlinks on macOS;
  strict copied files retain consumer-side checksum ownership behavior.
- `/cg-commit-push-pr` and `cg-update` regenerate targets, while drift and
  release checks are intended to prevent stale publication.
- Role-first model policy and current platform-selection behavior are not being
  redesigned.

Relevant prior knowledge:

- Native targets must remain generated, committed, drift-tested, and
  distributed through existing install semantics. Source:
  `.cg-docs/solutions/environment-issues/2026-07-03-cross-agent-native-platform-trees-require-generator-drift-tests-consistent-python.md`.
- The completed native-target plan established the generator, mapping,
  platform emitters, update/link integration, and release gates that this plan
  hardens rather than replaces. Source:
  `.cg-docs/plans/2026-07-03-cross-agent-native-platform-targets.md`.
- Tactical context confirms per-unit installation, consumer managed-copy
  checksums, and committed generated trees as current conventions. Source:
  `compound-gpid.context.md` (native platform tree and linking entries).

No `compound-gpid.local.md` is present. The implementation is Python-led and
must remain Python 3.8+ stdlib-only; existing PowerShell, shell, Markdown, JSON,
and YAML integration surfaces are changed only where this packaging contract
requires them.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Treat every `.github/skills/<skill>/` directory as an atomic bundle and include every regular file by default at the same bundle-relative path. | brainstorm requirements 1, 2, 4 |
| R2 | Reject non-regular entries, unsafe/non-portable paths, traversal, absolute/drive/UNC paths, symlink or junction escapes, destinations outside target roots, and destinations under canonical `.github/`. | brainstorm requirements 3, 11 |
| R3 | Reject duplicate destinations, overlapping generated trees, file/directory conflicts, and case-insensitive, Unicode-normalized, or Windows-normalized collisions across the complete output namespace. | brainstorm requirement 11 |
| R4 | Validate recursive relative Markdown links and images against included regular files before writing; reject escaping or missing references. | brainstorm requirements 5, 7 |
| R5 | Copy executable resources as opaque bytes, preserve executable status where supported, record it, and never import, source, evaluate, or execute them during generation. | brainstorm requirement 6 |
| R6 | Give generated commands, agents, skills, prompt support, language instructions, and shared contracts complete target-local runtime asset closure when `.github/` is absent. | brainstorm requirements 7-9 |
| R7 | Extend configured `outputPaths` for all emitted runtime roots and derive adapters, references, and install units from those values, including Codex agents at `.agents/subagents/`. | brainstorm requirements 8, 10 |
| R8 | Rewrite known canonical runtime asset-root references to target-native paths and reject unresolved canonical runtime dependencies without recursively packaging consumer-project content. | brainstorm dependency representation decision |
| R9 | Build and validate a deterministic in-memory source/output inventory, emitted bytes, references, collisions, ownership state, and stale candidates before the first write or delete. | brainstorm path safety and stale cleanup decisions |
| R10 | Emit one deterministic checksummed ownership manifest per generated target, covering all generated files and executable status without host-specific metadata or a recursive self-hash. | brainstorm requirement 12 and manifest decision |
| R11 | Delete stale output only when the prior manifest owns it and current bytes match the recorded checksum; preserve and fail on modified owned files, malformed manifests, or conflicting unowned destinations. | brainstorm requirements 12-14 |
| R12 | Preserve existing junction/symlink, consumer managed-copy checksum, user-owned conflict, platform-selection, and native destination behavior. | brainstorm backward compatibility decision |
| R13 | Align runtime mapping validation with the checked-in JSON Schema, including type/strategy, path, output-root, overlap, and collision invariants. | brainstorm closely related defects 8, 9, 13 |
| R14 | Serialize generated YAML/TOML/frontmatter safely and prove generated native metadata parses for adversarial but valid canonical values. | brainstorm closely related defect 14 |
| R15 | Fail closed when generation, mapping, dependency, Git/ignore-state inspection, update/link generation handoff, drift, or release preflight fails. | brainstorm requirement 15 and defects 10, 11 |
| R16 | Enforce mapping, generation, path safety, dependency closure, deterministic output, drift, isolated install, and platform checks in normal CI and before release publication. | brainstorm requirement 16 |
| R17 | Prove exact recursive four-file parity for `cg-skill-brainstorming` across Claude Code, Codex, and OpenCode before expanding atomic packaging to every skill. | brainstorm requirement 17 |
| R18 | Keep the design Python 3.8+ stdlib-only and avoid a general dependency DSL, per-skill package allowlists, plugin marketplace, or external-asset intake system. | brainstorm requirement 18 |
| R19 | Document atomic bundles, target-local dependency closure, generated-tree ownership, safe cleanup, isolated support claims, and the distinction from consumer managed-copy ownership. | brainstorm acceptance criterion 25 |

## Implementation Steps

## Phase 1: Safety And Inventory Primitives

### 1. Align mapping schema and runtime validation

- **Requirements**: R2, R3, R7, R13, R18
- **Files**:
  - `.github/shared/target-mapping.json`
  - `scripts/schemas/target_mapping_schema.json`
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_target_mapping.py`
  - `scripts/tests/test_target_path_safety.py` (new)
- **Details**:
  - Add native `outputPaths` entries needed for instructions and shared
    resources while preserving the existing platform-generic target shape.
  - Define one reusable normalization and containment contract for canonical
    sources, generated destinations, `outputPaths`, and `installUnits`.
  - Reject empty, absolute, drive-qualified, UNC, NUL-containing, traversal,
    canonical-destination, and target-escaping paths. Resolve existing source
    and destination ancestors without following escapes into the inventory.
  - Compare the combined output graph using POSIX repository-relative paths,
    Unicode normalization plus case-folding, Windows trailing-dot/space and
    reserved-name normalization, and file/directory prefix detection.
  - Reject overlapping non-Copilot generated roots and include Codex fallback
    files and skill directories in one collision namespace.
  - Keep the JSON Schema and stdlib runtime validator behaviorally equivalent;
    do not add `jsonschema` or another dependency.
- **Test Scenarios**: valid current mapping; missing/type-invalid fields;
  absolute/traversal paths; symlink ancestor escape; overlapping target roots;
  duplicate output; case-fold/Unicode/Windows-normalized collision;
  file/directory conflict; invalid install-unit source/target/strategy.
- **Tests**: `python3 -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_target_path_safety.py -q`
- **Acceptance criteria**: Every configured and derived path is validated by
  matching schema/runtime invariants before generation can construct a write
  plan, and adversarial mappings fail nonzero without changing output.

### 2. Build the deterministic pre-write output graph

- **Requirements**: R3, R9, R13, R14, R18
- **Files**:
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_cg_generate_targets.py`
  - `scripts/tests/test_target_path_safety.py` (new)
- **Details**:
  - Replace path-only manifest construction with typed source assets and output
    entries that carry normalized source/destination paths, kind, emitted bytes,
    SHA-256, and executable status before filesystem mutation.
  - Separate scanning, validation, rendering, and committing so all target
    outputs and stale candidates are validated before the first write/delete.
  - Expose a structured inventory/result API for tests, drift checks, and
    release gates instead of requiring stdout parsing.
  - Serialize YAML/TOML/frontmatter fields with deterministic escaping and add
    parser-based tests for descriptions, tool names, quotes, slashes, Unicode,
    and multiline-like values supported by canonical metadata.
  - Keep CLI output human-readable, but make it a presentation of structured
    results rather than an integration interface.
- **Test Scenarios**: stable sorted inventory; identical inputs produce
  identical bytes/hashes; one invalid late entry prevents all writes; generated
  TOML/frontmatter parses; dry-run performs no mutation.
- **Tests**: `python3 -m pytest scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_path_safety.py -q`
- **Acceptance criteria**: Generation has a deterministic, testable output graph
  containing final emitted bytes and no write/delete occurs until the complete
  graph passes validation.

## Phase 2: Pilot Atomic Bundle

### 3. Recursively inventory and emit the brainstorming pilot

- **Requirements**: R1, R4, R9, R17, R18
- **Files**:
  - `scripts/cg_generate_targets.py`
  - `.github/skills/cg-skill-brainstorming/SKILL.md`
  - `.github/skills/cg-skill-brainstorming/workflows/approach-comparison.md`
  - `.github/skills/cg-skill-brainstorming/workflows/requirement-elicitation.md`
  - `.github/skills/cg-skill-brainstorming/references/decision-template.md`
  - `scripts/tests/test_target_packaging.py` (new)
  - `.claude/skills/cg-skill-brainstorming/` (generated)
  - `.agents/skills/cg-skill-brainstorming/` (generated)
  - `.opencode/skills/cg-skill-brainstorming/` (generated)
- **Details**:
  - Recursively scan the pilot directory with `os.scandir`/`Path` primitives
    that distinguish regular files from symlinks and special entries without
    following them.
  - Include exactly the current four regular files and preserve each path below
    the skill root in every target.
  - Validate every relative Markdown link/image recursively against the pilot
    bundle and reject escapes or missing resources before emission.
  - Compare emitted bytes and executable flags against canonical sources.
- **Test Scenarios**: exact four-file inventory; nested relative paths; valid
  links; missing link; escaping link; unexpected symlink/special entry; exact
  path/hash parity for all three targets.
- **Tests**: `python3 -m pytest scripts/tests/test_target_packaging.py -q -k pilot`
- **Acceptance criteria**: All four pilot files exist at matching relative paths
  with matching SHA-256 and executable flags in Claude Code, Codex, and OpenCode,
  and all canonical/generated relative references resolve.

### 4. Prove executable resources are copied but never run

- **Requirements**: R2, R5, R9, R17
- **Files**:
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_target_packaging.py` (new)
- **Details**:
  - Add a fixture skill containing a script whose execution would create a
    sentinel file. Mark it executable where the fixture filesystem supports it.
  - Assert generation reads, hashes, and writes the file as opaque bytes,
    preserves executable/non-executable mode status where supported, records the
    status in structured output, and never creates the sentinel.
  - Keep any script syntax/behavior execution outside generation and outside
    this implicit packaging test.
- **Test Scenarios**: executable script; non-executable script under `scripts/`;
  binary bytes; unsupported mode-bit filesystem; sentinel remains absent.
- **Tests**: `python3 -m pytest scripts/tests/test_target_packaging.py -q -k executable`
- **Acceptance criteria**: Executable resources package without execution and
  parity tests distinguish preserved executable status from content equality.

## Phase 3: Generated Ownership And Cleanup

### 5. Add deterministic per-target ownership manifests

- **Requirements**: R9, R10, R12, R18
- **Files**:
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_target_ownership.py` (new)
  - `.claude/.compound-gpid-generated.json` (generated)
  - `.agents/.compound-gpid-generated.json` (generated)
  - `.opencode/.compound-gpid-generated.json` (generated)
- **Details**:
  - Implement schema version 1 with target ID, policy version, and sorted file
    entries containing repository-relative destination, canonical source or
    generator source identity, kind, emitted-byte SHA-256, and executable flag.
  - Cover commands, support files, agents, fallback agents, skill bundles,
    instructions, shared resources, adapters, configs, and model mappings.
  - Exclude timestamps, absolute paths, usernames, host metadata, and the
    manifest's own recursive hash.
  - Read prior manifests defensively and reject malformed schemas, duplicate
    entries, target mismatches, unsafe paths, and hashes with invalid shape.
  - Keep generated-tree ownership distinct from consumer
    `.compound-gpid/managed-files.json` semantics.
- **Test Scenarios**: deterministic sorting/bytes; complete file coverage;
  emitted-byte hashes; executable status; malformed/unsafe/foreign manifest;
  second generation byte identity.
- **Tests**: `python3 -m pytest scripts/tests/test_target_ownership.py -q -k manifest`
- **Acceptance criteria**: Each target has one deterministic manifest whose
  entries exactly describe existing generated files and current emitted bytes.

### 6. Implement checksum-guarded stale cleanup and recovery

- **Requirements**: R9, R11, R12, R15
- **Files**:
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_target_ownership.py` (new)
- **Details**:
  - Compute all stale candidates from the prior ownership manifest during
    preflight and validate every candidate before mutating the tree.
  - Delete only paths listed by the prior manifest whose current bytes match the
    recorded checksum; remove empty generated directories only up to, but not
    including, the target root.
  - Preserve and fail on a modified stale file, malformed manifest, unsafe
    manifest path, file/directory replacement, or conflicting unowned path.
  - Adopt an existing unowned expected destination only when its bytes already
    equal the intended output; otherwise preserve and fail.
  - Atomically write expected files, then safely delete validated stale paths,
    and atomically write the new manifest last. Test recovery/drift behavior for
    failures after partial per-file commits without replacing whole target roots.
- **Test Scenarios**: unchanged delete/rename; modified stale file; untracked
  file; equal unowned destination; conflicting destination; malformed manifest;
  interrupted write; empty-directory pruning boundary.
- **Tests**: `python3 -m pytest scripts/tests/test_target_ownership.py -q -k cleanup`
- **Acceptance criteria**: Stale unchanged generated content is removed and
  recorded, while every modified or unowned path is preserved and causes a
  clear nonzero failure before unsafe cleanup.

## Phase 4: Full Skill Expansion

### 7. Apply atomic packaging to every canonical skill

- **Requirements**: R1, R2, R4, R5, R9, R18
- **Files**:
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_target_packaging.py` (new)
  - `.claude/skills/` (generated)
  - `.agents/skills/` (generated)
  - `.opencode/skills/` (generated)
- **Details**:
  - Generalize pilot scanning to every canonical skill directory and include all
    regular files, including workflows, references, packages, scripts, assets,
    templates, evaluations, benchmarks, grades, fixtures, and source packs.
  - Preserve bundle-relative paths and mode status with no semantic allowlist,
    content denylist, or new ignore language.
  - Validate every skill entry and recursive relative Markdown reference before
    allowing any target write.
  - Ensure Codex fallback-agent files sharing `.agents/skills/` participate in
    global file/directory collision checks.
- **Test Scenarios**: nested resources of every representative kind; future
  unknown regular-file extension; binary asset; special entry; fallback/skill
  namespace conflict; all-target recursive parity.
- **Tests**: `python3 -m pytest scripts/tests/test_target_packaging.py -q`
- **Acceptance criteria**: Every canonical regular skill file exists at the
  same bundle-relative path in all three generated targets with matching hash
  and executable status.

### 8. Resolve existing reference violations and regenerate exact mirrors

- **Requirements**: R4, R12, R17, R19
- **Files**:
  - `.github/skills/` (only narrowly required reference/path corrections)
  - `scripts/tests/test_target_packaging.py` (new)
  - `scripts/tests/test_target_drift.py`
  - `.claude/skills/` (generated)
  - `.agents/skills/` (generated)
  - `.opencode/skills/` (generated)
- **Details**:
  - Inventory existing broken or escaping relative references surfaced by strict
    validation. Correct only the path or wording necessary for package closure;
    represent true cross-skill behavior as a named skill dependency rather than
    a relative escape.
  - Regenerate all skill trees and compare canonical/target path sets, emitted
    hashes, references, and modes recursively.
  - Update drift expectations to include support files and manifests rather than
    defining completeness as one `SKILL.md` per skill.
- **Test Scenarios**: current repository reference closure; narrowly corrected
  links; all-target inventory equality; stale legacy single-file mirrors;
  unchanged existing skill behavior.
- **Tests**: `python3 -m pytest scripts/tests/test_target_packaging.py scripts/tests/test_target_drift.py -q`
- **Acceptance criteria**: The repository has no unresolved skill-local relative
  references and generated skill inventories exactly mirror canonical bundles.

## Phase 5: Native Dependency Closure

### 9. Package target-local runtime support and rewrite references

- **Requirements**: R6, R7, R8, R9, R12, R14
- **Files**:
  - `.github/shared/target-mapping.json`
  - `scripts/schemas/target_mapping_schema.json`
  - `scripts/cg_generate_targets.py`
  - `.github/prompts/setup-templates.md`
  - `.github/prompts/resume-templates.md`
  - `.github/instructions/*.instructions.md`
  - `.github/shared/` (required runtime resources)
  - `scripts/tests/test_target_closure.py` (new)
  - generated target command, agent, instruction, shared, and adapter paths
- **Details**:
  - Emit prompt support files beneath the configured command/support root,
    language instructions beneath a configured instructions root, and required
    shared contracts once beneath each configured target-local shared root.
  - Rewrite known canonical runtime roots for prompts, skills, agents,
    instructions, and shared resources to target-local configured roots in
    emitted Markdown. Do not rewrite consumer-project paths or recursively
    package files merely because prose mentions them.
  - Derive root adapters, generated config, model mappings, and references from
    `outputPaths`; remove hardcoded `<generatedTreePath>/agents/` assumptions and
    assert Codex uses `.agents/subagents/`.
  - Reject emitted runtime Markdown that retains an unresolved canonical asset
    dependency required at execution time.
- **Test Scenarios**: setup/resume support resolution; shared completion/context
  contracts; language instructions; each canonical root rewrite; consumer path
  untouched; custom fixture `outputPaths`; Codex subagent path; unsafe rewrite.
- **Tests**: `python3 -m pytest scripts/tests/test_target_closure.py scripts/tests/test_target_mapping.py -q`
- **Acceptance criteria**: Every generated runtime dependency either resolves to
  a present target-local file through configured paths or generation rejects it.

### 10. Prove isolated native installations

- **Requirements**: R6, R7, R8, R15, R16
- **Files**:
  - `scripts/tests/test_target_closure.py` (new)
  - `scripts/tests/test_target_claude.py`
  - `scripts/tests/test_target_codex.py`
  - `scripts/tests/test_target_opencode.py`
  - optional CI fixture/support scripts under `scripts/tests/fixtures/`
- **Details**:
  - Build one isolated fixture per native target containing only that generated
    tree plus ordinary consumer-project files, with `.github/` physically absent.
  - Use a deterministic resolver to verify exact target paths, file presence,
    relative-reference closure, generated config/adapter paths, and absence of
    canonical runtime dependencies.
  - Where an available real platform CLI can load a representative command,
    agent, and skill safely and non-interactively, add a smoke test. Report an
    unavailable CLI as unproved/unsupported test coverage, not runtime proof.
  - Keep real-CLI checks separate from deterministic resolution so local absence
    does not turn required static closure checks into skips.
- **Test Scenarios**: each target without `.github/`; representative command,
  agent, skill, instruction, and shared contract; missing packaged dependency;
  available/unavailable CLI reporting.
- **Tests**: `python3 -m pytest scripts/tests/test_target_closure.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py -q`
- **Acceptance criteria**: Deterministic isolated closure passes for every
  supported target, and support claims distinguish real CLI proof from static
  resolution where a platform CLI is unavailable.

## Phase 6: Fail-Closed Integration And CI

### 11. Make generation handoffs fail closed

- **Requirements**: R12, R15, R16
- **Files**:
  - `scripts/update.ps1`
  - `scripts/update.sh`
  - `scripts/link.ps1`
  - `scripts/link.sh`
  - `scripts/helpers.ps1`
  - `.github/prompts/cg-commit-push-pr.prompt.md`
  - `scripts/tests/test_update_generates_targets.py`
  - related link/update Pester tests under `tests/`
- **Details**:
  - Propagate generator, mapping, and dependency validation failures as nonzero
    blocking outcomes rather than warnings followed by linking, updating,
    staging, or claiming a newly generated state.
  - Preserve previously usable installed content where possible and avoid
    redesigning per-unit linking or consumer managed-copy ownership.
  - Retain cross-platform Python resolution (`python3`, `python`, `py` with
    Windows Store stub rejection) in all generator entry points.
  - Update static wiring tests that currently require warning-and-continue
    behavior so they instead assert no downstream state transition after failure.
- **Test Scenarios**: generator unavailable; invalid mapping; generation
  validation failure; Python unavailable; previous target tree remains usable;
  no link/update/stage continuation; successful current workflows unchanged.
- **Tests**: `python3 -m pytest scripts/tests/test_update_generates_targets.py -q`; focused link/update Pester files through the canonical safe runner workflow
- **Acceptance criteria**: Every generation entry point stops before claiming or
  installing a new state after a required generation check fails, while existing
  successful install semantics remain unchanged.

### 12. Replace skip-prone drift checks and enforce CI/release gates

- **Requirements**: R10, R15, R16
- **Files**:
  - `scripts/tests/test_target_drift.py`
  - `scripts/tests/test_release_gate_targets.py`
  - `.github/workflows/tests.yml`
  - `cg-release.prompt.md`
  - `create-release.ps1`
  - `tests/create-release.Tests.ps1`
- **Details**:
  - Make drift tests consume the structured generator inventory/ownership
    manifests instead of parsing human-readable dry-run output.
  - Replace skips on generator, Git blob/listing, or ignore-state inspection
    failures with explicit failures. Compare committed HEAD bytes and ownership
    entries so dirty working-tree files cannot mask incomplete committed output.
  - Add required Python CI jobs for mapping, generation, path safety, packaging,
    ownership, closure, determinism, drift, and isolated target tests on supported
    operating systems without replacing existing Pester/E2E jobs.
  - Run real platform smoke checks only where the corresponding CLI is installed
    and label unavailable coverage honestly.
  - Add an operational release preflight before publication and make
    `create-release.ps1` reject release creation when required native packaging
    checks fail; do not rely only on a test that is not invoked by release flow.
- **Test Scenarios**: generator/Git/ignore command failure; dirty generated tree;
  missing/extra/hash-mismatched committed file; malformed manifest; CI job
  presence; release check failure blocks API call; all checks pass.
- **Tests**: `python3 -m pytest scripts/tests/test_target_drift.py scripts/tests/test_release_gate_targets.py -q`; `tests/create-release.Tests.ps1` through the canonical safe Pester runner
- **Acceptance criteria**: Required CI and release flows fail on every packaging,
  ownership, closure, or drift failure and cannot silently skip the gate.

## Phase 7: Documentation And Final Proof

### 13. Document packaging, ownership, and support guarantees

- **Requirements**: R6, R10, R11, R12, R19
- **Files**:
  - `README.md`
  - `docs/context-files.md`
  - `docs/installation.md`
  - `docs/reference.md`
  - `docs/troubleshooting.md`
  - maintainer/release documentation identified during implementation
- **Details**:
  - Describe canonical atomic bundles, include-by-default regular files,
    executable-resource handling, target-local support roots, and isolated
    dependency closure.
  - Document generated ownership manifests, manifest-last recovery, and
    checksum-guarded stale cleanup separately from consumer
    `.compound-gpid/managed-files.json` ownership.
  - Explain conflicts requiring maintainer resolution, including modified stale
    generated files, malformed manifests, unsafe paths, and unowned destination
    conflicts.
  - Update content tables that currently imply target skills contain only
    `SKILL.md`, and state precisely which support claims have real CLI evidence.
- **Test Scenarios**: documentation links resolve; described commands/paths match
  mapping; no obsolete single-file skill statements; generated vs consumer
  ownership is unambiguous.
- **Tests**: existing documentation/link checks plus targeted content assertions
  added where a stable contract needs regression coverage.
- **Acceptance criteria**: Maintainers and users can identify canonical inputs,
  generated outputs, ownership boundaries, recovery actions, and verified native
  support without reading generator internals.

### 14. Regenerate, prove determinism, and run final regressions

- **Requirements**: R1-R19
- **Files**:
  - `.claude/` (generated)
  - `.agents/` (generated)
  - `.opencode/` (generated)
  - all focused test and documentation files changed by prior phases
- **Details**:
  - Run generation twice from the same canonical inputs and prove byte-identical
    outputs and ownership manifests with no second-run changes.
  - Verify committed generated file sets and hashes against the structured
    manifests and canonical inventories.
  - Run all focused Python target suites, isolated closure checks, release gates,
    and existing link/update regressions on supported operating systems.
  - Run the canonical Pester suite only through the project safe runner and
    execution-subagent workflow; inspect `tests/last-run.json` rather than
    injecting full Pester output into the implementation session.
  - Record unavailable real-platform CLI coverage as remaining uncertainty and
    do not convert it into a support claim.
- **Test Scenarios**: clean repeat generation; cross-platform path behavior;
  committed parity; all focused suites; existing installation behavior;
  release preflight; unavailable optional CLI.
- **Tests**:
  - `python3 scripts/cg_generate_targets.py --all`
  - repeat generation plus repository hash/diff comparison
  - `python3 -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_path_safety.py scripts/tests/test_target_packaging.py scripts/tests/test_target_ownership.py scripts/tests/test_target_closure.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py scripts/tests/test_target_drift.py scripts/tests/test_release_gate_targets.py scripts/tests/test_update_generates_targets.py -q`
  - canonical Pester runner via execution subagent
- **Acceptance criteria**: All required evidence passes, generated trees are
  committed and deterministic, existing install regressions pass, and external
  skill intake remains blocked until this plan is completed.

## Testing Strategy

- Use `pytest` fixtures and `tmp_path` repositories for deterministic source,
  target, symlink, collision, stale-file, malformed-manifest, and interruption
  scenarios. Keep test data minimal and inline unless a reusable isolated target
  fixture materially reduces duplication.
- Test pure normalization, validation, inventory, reference-resolution,
  serialization, manifest, and ownership functions before end-to-end CLI tests.
- Assert both outcomes and absence of mutation for every preflight failure.
  Snapshot relevant source/output bytes and directory inventories before the
  failing invocation.
- Compare hashes of emitted bytes, not only source bytes or path sets. Verify
  executable status independently from content.
- Parameterize target-specific cases across Claude Code, Codex, and OpenCode;
  keep capability/output-path behavior mapping-driven.
- Test cross-platform-normalized collisions on every host through pure path
  normalization fixtures; supplement with Windows/macOS filesystem E2E checks.
- Keep deterministic isolated-resolution tests required. Treat real CLI smoke
  checks as additional runtime evidence and report unavailable CLIs explicitly.
- Do not use `pytest.skip` for generator, mapping, Git, ignore-state, dependency,
  ownership, or required deterministic closure failures.
- Run Pester only through the canonical safe runner workflow described by
  `cg-skill-pester-safety`, after implementation changes are complete.

## Documentation Checklist

- [ ] Update generated-tree content tables for atomic skill bundles and runtime support roots.
- [ ] Document target `outputPaths` for commands, skills, agents, instructions, and shared resources.
- [ ] Document ownership manifest schema, deterministic fields, and fixed locations.
- [ ] Explain checksum-safe stale cleanup, conflict failures, and recovery steps.
- [ ] Distinguish generated-tree ownership from consumer `.compound-gpid/managed-files.json` ownership.
- [ ] Document executable-resource packaging and the no-execution guarantee.
- [ ] Document CI, drift, deterministic generation, isolated-install, and release gates.
- [ ] State which native platform behaviors have real CLI proof versus deterministic resolution only.
- [ ] Remove or correct statements implying generated skills contain only `SKILL.md`.
- [ ] Confirm README, installation, reference, context-files, and troubleshooting links remain valid.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Path validation is incomplete or differs across hosts. | Generator can escape target roots, overwrite canonical/user content, or ship colliding paths. | Validate normalized source and destination graphs before writes; use `Path.relative_to`, resolved-ancestor checks, portable-name normalization, adversarial fixtures, and Windows/macOS CI. |
| Cleanup mistakes ownership for location or naming. | User or maintainer modifications are deleted. | Delete only prior-manifest-owned paths with matching current checksums; preserve/fail on every mismatch or unowned path; never infer ownership from globs or Git tracking. |
| Per-file atomic writes fail after partial output changes. | Target tree and manifest temporarily disagree. | Validate everything before mutation, write files atomically, write manifest last, fail nonzero, and make drift/recovery tests detect and repair only safely owned state. |
| Broad reference rewriting alters consumer-project paths or prose. | Generated commands resolve incorrectly or package unrelated project files. | Rewrite only known canonical runtime asset roots, test consumer paths as negative cases, and reject unresolved required runtime references. |
| Atomic packaging substantially increases generated/release size. | Slower generation, CI, cloning, or noisy diffs. | Keep deterministic hashing/inventory linear, measure generated counts/sizes, avoid duplicate target-local shared files, and accept size growth as the chosen correctness tradeoff. |
| Strict validation exposes existing broken references or non-portable names. | Initial implementation blocks generation. | Surface all violations from preflight, make only narrow canonical corrections required for closure, and do not weaken the safety contract to preserve invalid content. |
| Runtime mapping validation drifts from JSON Schema. | A mapping passes one entry point and fails or escapes through another. | Share explicit invariants, add parity fixtures that evaluate both representations, and fail all mapping consumers closed. |
| CI exists but release publication bypasses it. | A stale or incomplete native package can still ship. | Invoke release preflight operationally before the GitHub API call and test that a failed gate prevents release creation. |
| Real platform CLIs are unavailable in CI. | Static closure is mistaken for runtime support. | Keep deterministic isolated resolution required, add CLI smoke checks where available, and label missing runtime proof as uncertainty rather than support. |
| Fail-closed integration accidentally breaks current install/update behavior. | Existing users cannot link or refresh otherwise valid targets. | Preserve per-unit and managed-copy contracts, add failure injection around only generation handoffs, and run existing platform/link/update regressions unchanged or with equivalent assertions. |

## Out of Scope

- Importing, adapting, licensing, or evaluating Awesome Copilot or any external skill.
- External asset provenance, trust, intake, or optional metadata policy.
- Native marketplaces, plugins, registries, or publication formats.
- A general dependency language, semantic content allowlist, or per-skill package manifest.
- Generating native trees from a neutral source format.
- Broad redesign of `/cg-*` workflows, skill content, or model selection.
- Unrelated consumer linker identity, marker, dangling-link, or managed-manifest redesign.
- Fixing every consumer ownership issue discovered during implementation unless it blocks this packaging contract.
- Claiming platform runtime support without deterministic isolated closure or recording unavailable CLI proof.

## Completion Contract

### Outcome

Compound GPID deterministically packages every canonical skill as an atomic
native bundle and supplies commands, agents, instructions, prompt support, and
shared contracts with target-local runtime dependency closure for Claude Code,
Codex, and OpenCode. Generation validates the complete output graph before
writing, tracks ownership with checksummed per-target manifests, removes only
unchanged owned stale files, fails closed on unsafe or unverifiable states, and
is enforced by CI and release gates.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Mapping/schema parity and adversarial path, overlap, collision, entry-type, and pre-write validation pass with no output mutation on failure. | `python3 -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_target_path_safety.py -q` | yes |
| V2 | 2 | `cg-skill-brainstorming` has exact four-file path, byte-hash, Markdown-reference, and executable-mode parity in all three native targets; a sentinel script is copied but never executed. | `python3 -m pytest scripts/tests/test_target_packaging.py -q -k "pilot or executable"` | yes |
| V3 | 3 | Per-target ownership manifests are deterministic and complete; unchanged owned stale files are removed, while modified owned, unowned, malformed-manifest, and conflicting paths are preserved and fail safely. | `python3 -m pytest scripts/tests/test_target_ownership.py -q` | yes |
| V4 | 4 | Every regular file in every canonical skill appears at the same bundle-relative path in all targets, and all relative Markdown references resolve. | `python3 -m pytest scripts/tests/test_target_packaging.py scripts/tests/test_target_drift.py -q` | yes |
| V5 | 5 | Commands, agents, skills, prompt support, instructions, and shared contracts resolve without `.github/`; configured `outputPaths` are honored, including `.agents/subagents/`. | `python3 -m pytest scripts/tests/test_target_closure.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py -q` | yes |
| V6 | 6 | Generator, mapping, Git inspection, update/link handoff, drift, and release failures are nonzero and blocking; required Python gates run in CI on supported operating systems. | `python3 -m pytest scripts/tests/test_target_drift.py scripts/tests/test_release_gate_targets.py scripts/tests/test_update_generates_targets.py -q`; `.github/workflows/tests.yml` | yes |
| V7 | 7 | Two consecutive generations are byte-identical; generated trees and manifests match committed output; maintained docs describe bundle closure and ownership accurately; existing install behavior regresses nowhere. | `python3 scripts/cg_generate_targets.py --all`; repeat generation and hash comparison; focused pytest suite; canonical Pester runner via execution subagent | yes |
| V8 | final | Full required verification passes and release publication cannot proceed when native packaging or drift evidence fails. | CI artifacts, release preflight artifact, and final `/cg-work` execution report | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Generation never writes into canonical `.github/` or outside a configured native generated tree. | Snapshot canonical bytes and adversarial containment tests. |
| C2 | 1 | Implementation remains Python 3.8+ stdlib-only and mapping runtime validation matches the checked-in JSON Schema. | Import/dependency inspection and schema/runtime parity tests. |
| C3 | 2 | Executable resources are treated as opaque bytes and never imported, sourced, or run during generation. | Sentinel fixture and mode/hash assertions. |
| C4 | 3 | No untracked, unowned, user-owned, modified stale, or checksum-mismatched file is deleted or overwritten. | Ownership conflict and stale-cleanup tests. |
| C5 | 4 | Inclusion is atomic and include-by-default for regular skill files; no per-skill allowlist or general ignore DSL is introduced. | Recursive canonical-to-target inventory comparison. |
| C6 | 5 | Existing directory junction/symlink, managed-copy checksum, `--platforms`, and user-conflict behavior remains intact. | Existing link/update tests and platform E2E checks. |
| C7 | 6 | Generation, mapping, Git, dependency, drift, and release checks fail closed rather than skip or downgrade to warnings. | Failure-injection tests and CI/release assertions. |
| C8 | final | External skill intake and consumer ownership redesign do not enter this implementation. | Changed-file and requirements review against boundaries. |

### Boundaries

- Allowed: generator refactoring; mapping/schema extensions; atomic skill
  packaging; target-local prompt support, instructions, and shared resources;
  static runtime-reference rewriting; ownership manifests; checksum-safe stale
  cleanup; focused Python tests; CI/release enforcement; generated-tree
  regeneration; narrow canonical reference corrections; maintainer/user
  documentation.
- Out of scope: external skill import or provenance policy;
  marketplace/plugin/registry work; neutral source formats; general dependency
  DSLs or per-skill allowlists; broad `/cg-*` redesign; unrelated linker
  identity or consumer managed-manifest redesign; runtime model-selection
  redesign.

### Iteration Policy

1. Implement and verify each phase in order; do not expand all skills before the pilot parity gate passes.
2. Within a phase, fix failing required evidence and rerun only the focused verification surface before broader regression checks.
3. Under `deviation-policy: ask`, pause before changing requirements, phase boundaries, ownership semantics, supported target claims, or listed files materially.
4. Record justified approved deviations and their evidence impact in the execution report.
5. Mark a phase complete only after all required rows for that phase pass; mark the plan complete only after V8 and all final constraints pass.

### Blocked-Stop Conditions

- Preflight cannot prove source/destination confinement, collision freedom, or complete dependency closure before writes.
- A stale manifest-owned path is modified, a destination conflicts with user-owned content, or a manifest is malformed/unsafe and resolution requires destructive action.
- Required isolated-install behavior cannot be tested or deterministically resolved; the affected target must not be claimed supported.
- Any required generator, mapping, Git, CI, drift, update/link, release, or regression check remains failed after focused recovery.
- Safe cross-platform verification cannot be run, or continuing would require crossing the defined boundaries.
- A required deviation is discovered and user approval is unavailable.
