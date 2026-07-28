---
date: 2026-07-27
title: "Canonical-to-Native Packaging Foundation"
status: decided
scope: "Deep"
chosen-approach: "Atomic Mirrors With Owned Manifests"
tags: [packaging, generator, native-targets, skills, dependency-closure, manifests, path-safety, drift, ci]
---

# Canonical-to-Native Packaging Foundation

## Context

Compound GPID treats `.github/` as canonical and generates committed native
trees for Claude Code, Codex, and OpenCode through
`scripts/cg_generate_targets.py` and `.github/shared/target-mapping.json`.
The generator currently scans and emits only each skill's `SKILL.md`, so
progressive-disclosure resources under `references/`, `workflows/`, `scripts/`,
`packages/`, source packs, evaluation directories, and other supporting paths
are absent from generated targets.

The defect is broader than skills. Isolated native-platform installations can
also omit prompt support files, shared contracts, and language instructions,
while generated commands and agents retain references to canonical `.github/`
paths. The current drift check validates the generator's incomplete manifest,
not runtime dependency closure. Generator and Git failures can become skipped
drift tests, and the Python target tests are not normal CI gates.

The pilot `cg-skill-brainstorming` proves the immediate defect. Its canonical
`SKILL.md` references two workflow files and one decision template, but each of
the three generated skill directories contains only `SKILL.md`.

Phase 0 must make packaging complete, deterministic, confined, owned, and
testable before any external skill is imported or adapted. The design must
preserve current managed-copy, checksum, symlink/junction, platform-selection,
and user-owned conflict behavior.

## Requirements

1. Treat each `.github/skills/<skill>/` directory as an atomic bundle.
2. Include every regular file in the bundle by default, including evaluation
   files, benchmarks, grades, fixtures, source packs, scripts, assets,
   templates, workflows, references, and packages.
3. Reject unsafe filesystem entries rather than silently excluding them.
4. Preserve each included file's relative path in every native skill root.
5. Validate relative Markdown references before writing outputs.
6. Copy skill-local executable resources without importing, sourcing, or
   executing them during generation.
7. Give native commands, agents, and skills a complete runtime asset closure
   when `.github/` is absent.
8. Copy required `.github/shared/` resources into a configured target-local
   shared root and rewrite runtime references to the native path.
9. Prove target-local shared resources work through isolated-install tests;
   do not label a target supported based only on inferred path compatibility.
10. Derive adapters and references from each target's `outputPaths`, including
    Codex agents at `.agents/subagents/`.
11. Reject absolute paths, traversal, symlink escapes, canonical `.github/`
    destinations, destinations outside a generated tree, duplicate outputs,
    file/directory conflicts, overlapping target trees, and case-insensitive or
    cross-platform-normalized collisions.
12. Remove stale output only when the prior generated manifest owns the path
    and the current bytes still match the recorded checksum.
13. Preserve and fail if a stale manifest-owned path has been modified.
14. Never remove an untracked, unowned, or user-owned file.
15. Fail closed when generation, mapping validation, dependency validation, or
    required Git inspection fails.
16. Add CI and release gates for generation, mapping, drift, path safety,
    dependency closure, deterministic output, and isolated native installs.
17. Prove exact recursive parity for `cg-skill-brainstorming` across Claude
    Code, Codex, and OpenCode before applying the model to all skills.
18. Keep the implementation stdlib-only and avoid a general dependency DSL,
    plugin marketplace, or external-asset intake system.

## Approaches Considered

### Approach 1: Atomic Mirrors With Owned Manifests

Recursively inventory complete skill directories, package target-local runtime
support roots, validate the full output graph before writing, and record one
deterministic checksum manifest per generated target.

**Pros**:
- Makes directory structure the default packaging contract.
- Includes future resource types without allowlist changes.
- Supports exact ownership, safe stale cleanup, and reproducibility checks.
- Avoids a new dependency language.
- Allows isolated native installations to be proved rather than assumed.

**Cons**:
- Generated trees grow because evaluation assets are included.
- Strict validation will expose existing ambiguous or broken references.
- Native path rewriting requires platform-specific integration tests.
- The dependency-closure work extends beyond skill copying.

**Effort**: Large.

### Approach 2: Reference-Driven Closure

Package only `SKILL.md` and files recursively reachable through Markdown
references.

**Pros**:
- Produces smaller target trees.
- Gives each included file an apparent runtime reason.

**Cons**:
- Misses dynamic selection, prose load instructions, scripts, and unlinked but
  intentionally bundled resources.
- Requires a complex parser while still risking silent omissions.
- Conflicts with atomic, include-by-default packaging.

**Effort**: Medium to large.

### Approach 3: Explicit Per-Asset Package Manifests

Require every skill or asset family to list packaged files and dependencies.

**Pros**:
- Provides precise release-content control.
- Could later carry provenance or external-intake metadata.

**Cons**:
- Creates high maintenance cost across existing and future skills.
- A missed manifest update recreates the current incompleteness defect.
- Introduces an unnecessary packaging and dependency language.

**Effort**: Large.

## Decision

Use **Approach 1: Atomic Mirrors With Owned Manifests**.

### Inclusion Policy

Use convention-based, include-by-default packaging:

- Every regular file beneath a canonical skill directory is part of the bundle.
- Evaluation files and source packs are included by default.
- Directory-relative paths are preserved exactly.
- Symlinks, junctions, sockets, devices, and other non-regular entries are
  rejected. They are not followed or silently skipped.
- Unsafe or non-portable paths are rejected before any output is written.
- Phase 0 does not add per-skill allowlists or a general ignore language.
- A later external-intake phase may add optional metadata without changing the
  atomic default, but provenance policy is not part of Phase 0.

This is neither a semantic allowlist nor a broad content denylist. The only
exclusions are hard safety constraints on entry type and path validity.

### Dependency Representation

Do not introduce explicit per-asset dependency declarations in Phase 0.
Represent dependencies using existing structure and references:

- Skill-local resources remain inside the atomic skill bundle.
- Relative Markdown links and images are validated against the packaged bundle.
- A relative skill reference must resolve to an included regular file inside
  that skill's packaged directory. Escaping links fail validation.
- Cross-skill behavior should use a named skill dependency rather than a
  relative file escape. Existing violations may receive narrowly scoped path or
  wording corrections when required for closure; broad skill redesign remains
  out of scope.
- Prompt support files such as `setup-templates.md` and `resume-templates.md`
  are packaged under the target's configured command/support root.
- Canonical language instructions are packaged under a configured native
  instructions root.
- Required shared resources are copied once per target under a configured
  `outputPaths.shared` root. Generated Markdown references are rewritten from
  canonical asset roots to the applicable native output root.
- Rewriting covers known canonical runtime asset roots: prompts, skills,
  agents, instructions, and shared resources. Emitted runtime Markdown must not
  retain an unresolved canonical-runtime dependency.
- References to consumer-project content are not recursively packaged merely
  because a prompt mentions them.

Target-local shared copies are supported only after deterministic resolution
checks and isolated native-platform tests with `.github/` physically absent.
Where a real platform CLI can load or invoke representative assets, the test
must do so. Otherwise, a deterministic resolver must prove exact target paths,
file presence, and reference closure. Unproved behavior is not described as
supported.

### Executable Resources

Executable resources are files under a bundle's `scripts/` subtree or files
whose source mode marks them executable. The generator will:

- Treat them as opaque bytes.
- Require a regular, confined source path.
- Hash and copy them atomically.
- Preserve an executable/non-executable mode bit where the target filesystem
  supports it.
- Record executable status in the target manifest.
- Never import, source, evaluate, or invoke them.

Generator tests must include a script that would create a sentinel if executed;
the script must be packaged while the sentinel remains absent. Syntax or
behavior tests for a known script may run only as separately named, explicitly
approved CI tests, not as implicit generation behavior.

### Path Safety And Collisions

Build and validate the complete source and destination inventory before the
first write. Validation must:

- Normalize repository-relative paths with POSIX separators.
- Reject empty, absolute, drive-qualified, UNC, NUL-containing, or `..` paths.
- Resolve source and existing destination ancestors and reject symlink or
  junction escapes.
- Require every non-Copilot destination to remain beneath that target's
  `generatedTreePath`.
- Reject any non-Copilot destination under canonical `.github/`.
- Validate `outputPaths` and `installUnits`, not only generated asset paths.
- Reject exact duplicates, Unicode-normalized case-fold collisions, Windows
  trailing-dot/space collisions, reserved Windows names, and file/directory
  prefix conflicts.
- Reject overlapping generated tree roots across targets.
- Check the combined namespace, including Codex fallback-agent files sharing
  `.agents/skills/` with skill directories.

The mapping's JSON Schema and runtime validator must enforce the same path and
type/strategy invariants. Link/update entry points that consume the mapping must
fail closed on an invalid mapping; this is path-safety hardening, not a redesign
of installation behavior.

### Generated Ownership Manifest

Create one manifest at a fixed path inside each generated target tree, for
example:

```text
.claude/.compound-gpid-generated.json
.agents/.compound-gpid-generated.json
.opencode/.compound-gpid-generated.json
```

The minimal schema is:

```json
{
  "schemaVersion": 1,
  "target": "opencode",
  "policyVersion": 1,
  "files": [
    {
      "path": ".opencode/skills/cg-skill-brainstorming/workflows/approach-comparison.md",
      "source": ".github/skills/cg-skill-brainstorming/workflows/approach-comparison.md",
      "kind": "skill-support",
      "sha256": "...",
      "executable": false
    }
  ]
}
```

Rules:

- Sort entries by normalized destination path.
- Hash emitted bytes, not only source bytes.
- Omit timestamps, absolute paths, usernames, host metadata, and the manifest's
  own recursive hash.
- Cover commands, command support, agents, fallback agents, skills and all
  support files, instructions, shared resources, adapters, configs, and model
  mappings.
- Keep this source-repository generated-output manifest separate from consumer
  `.compound-gpid/managed-files.json`, whose checksum contract and user-override
  behavior remain unchanged.

The manifest supplies the minimum data needed for ownership, stale cleanup,
drift detection, and reproducibility. File size and aggregate input digests are
optional diagnostics, not required ownership fields.

### Stale Cleanup

Generation follows this order:

1. Scan canonical inputs and the prior target manifest.
2. Build all output bytes and the new manifest in memory.
3. Validate source paths, destinations, references, collisions, prior ownership,
   and all stale candidates.
4. If any check fails, write and delete nothing.
5. Atomically write expected files.
6. Delete stale files only when the prior manifest lists the path and the
   current checksum equals the prior recorded checksum.
7. Remove empty generated directories only up to, but not including, the target
   root.
8. Atomically write the new manifest last.

If a stale owned file's current checksum differs, preserve it and fail. If an
expected destination is not prior-manifest-owned, adopt it only when its bytes
already equal the intended generated bytes; otherwise preserve it and fail.
Never infer deletion ownership from a filename, directory name, glob, or Git
tracking alone.

Per-file atomic writes plus a manifest-last commit do not create a fully atomic
directory transaction, but they preserve recoverability without replacing a
target root that may contain user-owned files. A failure remains nonzero and
drift detection reports any partial state.

### Backward Compatibility

Preserve these existing contracts:

- Directory install units remain symlinks on macOS and junctions on Windows.
- Consumer managed copies continue using their current checksum manifest.
- User-owned conflicts are preserved rather than overwritten.
- Existing `--platforms` selection behavior remains unchanged.
- Existing generated command, agent, and skill destination conventions remain
  unchanged unless corrected through configured `outputPaths`.
- No native target is generated into `.github/`.

Expected compatibility risks:

- Generated trees and releases become larger.
- Previously broken progressive-disclosure paths begin working and may change
  agent behavior or token consumption when explicitly loaded.
- Strict cross-platform path checks may reject filenames accepted on one host.
- Existing modified generated files or unowned legacy orphans will block safe
  cleanup and require explicit maintainer resolution.
- Adding target manifests changes committed generated-tree contents and drift
  expectations.
- Native reference rewriting may expose platform assumptions; isolated tests
  must catch them before support is claimed.

## Closely Related Phase 0 Defects

Include the following because they directly affect packaging safety,
completeness, or proof:

1. The generator scans only `.github/skills/cg-skill-*/SKILL.md` and emits only
   that file.
2. Prompt support files `setup-templates.md` and `resume-templates.md` are not
   generated.
3. Instructions are scanned but never emitted.
4. Shared contracts required by core commands are not present in isolated
   native installations.
5. Generated commands and agents retain hardcoded canonical runtime paths,
   including skill paths.
6. The root adapter hardcodes `<generatedTreePath>/agents/` instead of using
   `outputPaths.agents`, producing the wrong Codex path.
7. Generation has no stale cleanup or persistent generated-output ownership
   record.
8. Output path strings are not confined; absolute paths, traversal, and symlink
   ancestors can escape target trees.
9. Duplicate destinations, output overlaps, case-fold collisions, and
   file/directory conflicts are not rejected globally.
10. Generator writes can leave a partially updated tree, while update/link flows
    may downgrade generation failure and continue.
11. Drift tests skip when generation or Git inspection fails and parse
    human-readable dry-run output.
12. Python generator, target, drift, and release-gate tests are not normal CI
    gates, and release publication does not operationally enforce the gate.
13. Runtime mapping validation is weaker than the checked-in JSON Schema and
    does not enforce type/strategy or path invariants.
14. Generated YAML/TOML interpolation is not safely serialized or comprehensively
    parsed in tests, so otherwise valid canonical metadata can produce invalid
    native files.
15. Current target tests define completeness as one generated `SKILL.md` per
    canonical skill, creating false confidence.

The following findings are related but deferred because they redesign linker or
consumer ownership behavior rather than the canonical packaging foundation:

- Link ownership inferred from a `compound-gpid` substring.
- Existing-link verification not checking the exact expected source.
- Marker occurrence accepted anywhere in a managed file.
- Empty managed instruction files and dangling destination symlinks.
- Consumer managed-manifest atomicity, schema migration, and stale records.
- Broad frontmatter policy redesign beyond safe serialization.
- `cg-skill-brainstorming` workflow/template content drift and its lack of an
  explicit load from `/cg-brainstorm`.
- Orphaned canonical skill content that is not a packaging defect.

## Testable Acceptance Criteria

### Pilot Parity

1. The canonical `cg-skill-brainstorming` inventory contains exactly
   `SKILL.md`, two `workflows/*.md` files, and one `references/*.md` file.
2. Each relative path exists under `.claude/skills/`, `.agents/skills/`, and
   `.opencode/skills/` for the pilot.
3. SHA-256 hashes and executable flags match canonical files exactly for all
   four pilot files on all three targets.
4. Every relative Markdown link in canonical and generated pilot files resolves
   within the corresponding skill directory.

### Bundle And Executable Safety

5. Every regular canonical skill file appears at the same bundle-relative path
   in all targets, including evaluation and source-pack files.
6. A symlink, path escape, special file, case-fold collision, Windows-normalized
   collision, or file/directory collision causes a nonzero preflight failure and
   no output changes.
7. A sentinel-producing skill script is copied with its bytes and executable
   status preserved but is never executed during generation.

### Dependency Closure

8. Generated commands include required support templates, shared contracts, and
   language instructions at configured native paths.
9. All generated runtime references to canonical asset roots are either
   rewritten to valid native paths or rejected.
10. Recursive relative references in packaged Markdown resolve to included
    regular files.
11. Isolated fixtures containing only one native target plus ordinary consumer
    project files, with `.github/` absent, pass dependency-resolution checks.
12. Representative command/agent/skill loading succeeds through each available
    real platform CLI; unsupported or unavailable runtime checks are reported as
    such and are not replaced by a claim of runtime proof.

### Ownership, Cleanup, And Reproducibility

13. Every generated target has a deterministic manifest whose entries match
    existing files and current hashes.
14. Two consecutive generations produce byte-identical outputs and manifests.
15. Deleting or renaming a canonical support file removes the unchanged stale
    target copies and records the new state.
16. Modifying a stale manifest-owned file preserves it and causes generation to
    fail.
17. An untracked or unowned file beneath a target tree is never deleted; a
    conflicting destination blocks generation unless its bytes already match.
18. The generator uses each configured `outputPaths` value, and the Codex adapter
    names `.agents/subagents/` exactly.

### Drift, CI, And Failure Behavior

19. Drift checks consume the structured generated manifest or generator API,
    not human-readable CLI output.
20. Generator, Git, mapping, or ignore-state inspection failure fails tests
    rather than skipping them.
21. CI runs mapping, generator, platform, path-safety, closure, drift, and
    isolated-install Python tests as required checks.
22. Release preflight blocks publication when generation or drift checks fail.
23. Update/link entry points do not continue into a newly generated or installed
    state after target generation fails; previously usable installed content is
    left intact where possible.
24. Existing link/unlink/update tests for managed copies, checksums,
    symlink/junction behavior, platform selection, and user-owned conflicts
    continue to pass unchanged or with equivalent assertions.
25. Maintainer and user documentation accurately describes atomic bundles,
    target-local dependencies, generated ownership, safe cleanup, and isolated
    platform support.

## Phased Implementation Sequence

### Phase 0.1: Safety And Inventory Primitives

1. Align runtime mapping validation with the JSON Schema.
2. Add normalized path, target-root, source-root, symlink-ancestor, portability,
   overlap, and collision validation.
3. Build a deterministic in-memory output inventory before emission.
4. Add structured serialization for native YAML/TOML metadata.
5. Make all preflight failures occur before writes.

### Phase 0.2: Pilot Atomic Bundle

1. Recursively inventory `cg-skill-brainstorming`.
2. Emit all four pilot files unchanged to all three targets.
3. Validate recursive relative references.
4. Add exact path, hash, and mode parity tests.
5. Add a non-executed script fixture even if the pilot itself has no script.

### Phase 0.3: Generated Ownership And Cleanup

1. Add the deterministic per-target manifest.
2. Seed manifests from expected generated files whose bytes match.
3. Add checksum-guarded stale cleanup and empty-directory pruning.
4. Fail on modified stale files, conflicting unowned destinations, malformed
   manifests, or unsafe manifest paths.
5. Add repeatability, rename/delete, and interrupted-failure recovery tests.

### Phase 0.4: Full Skill Expansion

1. Apply atomic inclusion to every canonical skill.
2. Package evaluations, source packs, scripts, packages, assets, templates,
   workflows, and references without semantic exclusions.
3. Resolve or narrowly correct existing relative-reference violations.
4. Regenerate and verify exact bundle-relative parity across all targets.

### Phase 0.5: Native Dependency Closure

1. Add configured output roots for instructions and shared resources.
2. Package prompt support files and language instructions.
3. Copy shared resources target-locally and rewrite canonical runtime asset
   references through `outputPaths`.
4. Fix adapters to use `outputPaths`, including Codex subagents.
5. Validate no unresolved canonical-runtime dependency remains.
6. Build isolated per-target installation fixtures with `.github/` absent.

### Phase 0.6: Fail-Closed Integration And CI

1. Make generator/update/link/drift/release failure propagation explicit and
   nonzero without redesigning existing install semantics.
2. Replace drift-test skips and human-output parsing with structured checks.
3. Run the Python target suite in normal CI.
4. Add path-adversarial, stale-cleanup, closure, and isolated-install jobs.
5. Add real platform CLI smoke checks where available.
6. Enforce the same checks before release publication.

### Phase 0.7: Documentation And Final Proof

1. Update maintainer generation and release instructions.
2. Update user installation and ownership documentation.
3. Remove statements that generated trees contain only `SKILL.md` support.
4. Document manifest ownership separately from consumer managed-copy ownership.
5. Run full cross-platform regression checks and record evidence before any
   external skill intake begins.

## Scope Boundaries

### In Scope

- Canonical bundle inventory and native target generation.
- Required mapping/schema extensions and validation.
- Skill, prompt-support, instruction, and shared-resource packaging.
- Static native-path rewriting required for dependency closure.
- Generated-tree ownership manifests and safe stale cleanup.
- Fail-closed generator, drift, update/link generation handoff, and release
  checks.
- Python and cross-platform CI needed to prove the packaging contract.
- Narrow canonical reference fixes required to make existing assets packageable.
- Maintainer and user documentation for changed packaging and ownership rules.

### Out Of Scope

- Importing or adapting Awesome Copilot or any other external skill.
- External asset provenance, licensing, trust, or intake policy beyond keeping
  an optional future metadata interface possible.
- Native marketplaces, plugins, registries, or publication formats.
- Redesigning `/cg-*` workflows or broad skill content.
- A general dependency language or per-skill package allowlist.
- Generating native trees from a neutral source format.
- Unrelated linker/installer ownership redesign.
- Fixing all consumer managed-manifest or link-identity defects discovered
  during research.
- Runtime model-selection redesign.

## Roadmap Recommendation

Track this as one Deep feature named **Canonical-to-Native Packaging
Foundation** under the existing cross-agent or architecture-research milestone
if that milestone remains active. If the completed cross-agent target feature
cannot accept follow-up hardening, create a small milestone named **Native
Packaging Reliability** with Phase 0 as its first blocking feature.

This feature should block any later external-skill intake feature. The roadmap
record should link this brainstorm and the subsequent `/cg-plan`, and should not
combine external provenance or marketplace work into the same feature.

## Next Steps

1. Register the feature in the roadmap under the selected milestone.
2. Run `/cg-plan` from this brainstorm, preserving the seven implementation
   phases and acceptance criteria.
3. Review the plan with `/cg-plan-review` because path safety, ownership, and
   cross-platform cleanup are high-risk.
4. Implement and prove the pilot before expanding to all canonical skills.
5. Do not begin external skill intake until Phase 0 acceptance criteria pass.
