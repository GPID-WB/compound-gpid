---
date: 2026-07-03
title: "Cross-Agent Native Platform Targets"
status: completed
completed-date: 2026-07-03
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-07-03-cross-agent-native-platform-targets.md"
language: "Python/PowerShell/Markdown"
estimated-effort: "large"
deviation-policy: "ask"
tags: [cross-agent, adapters, claude-code, codex, opencode, model-governance, distribution, generator, target-mapping]
phases: 6
completed-phases: [1, 2, 3, 4, 5, 6]
execution-report: ".cg-docs/work-reports/2026-07-03-cross-agent-native-platform-targets.md"
roadmap-features:
  - architecture-research/study-codex-plugin
  - architecture-research/copilot-instructions-restructuring
---

# Plan: Cross-Agent Native Platform Targets

## Objective

Compound GPID generates committed native platform trees (`.claude/`, `.agents/`,
`.opencode/`) from the canonical `.github/` source via a `target-mapping.json`
schema, distributes them through the existing junction/symlink mechanism, and
blocks release if generated trees are stale — so users on Claude Code, Codex,
and OpenCode get native commands, skills, and agents without knowing about
`.github/`.

## Context

The approved brainstorm (`.cg-docs/brainstorms/2026-07-03-cross-agent-native-platform-targets.md`)
chose Approach 3: keep `.github/` as the canonical authoring surface, add a
platform-generic target-mapping schema with capability flags, generate committed
native trees for Claude Code, Codex, and OpenCode, and distribute them via the
existing global clone + junction/symlink mechanism.

Prior work:
- `adapters/manifest.json` + `adapters/codex/AGENTS.md` + `adapters/claude/CLAUDE.md`
  are opt-in source packages, not `cg-link` managed outputs.
- `.github/shared/model-catalog.json` is the canonical role assignment source.
- `scripts/cg_audit_context.py` validates model governance against the catalog.
- `scripts/link.ps1` / `scripts/link.sh` create per-subdirectory junctions for
  `.github/{prompts,skills,agents,instructions,shared}`.
- Existing rule: Codex/Claude compatibility belongs outside `.github/` assets.
  This plan supersedes that rule for generated native trees, which become a
  first-class product surface — but `.github/` itself remains Copilot-canonical
  and is never modified by the generator.

Brain findings:
- Codex and Claude Code need a root adapter to execute Copilot-oriented `/cg-*`
  prompts — source: `.cg-docs/solutions/environment-issues/2026-06-06-codex-claude-code-cg-prompt-dispatch-adapter.md`.
- Cross-agent adapters should be opt-in source packages — source:
  `.cg-docs/solutions/environment-issues/2026-06-23-cross-agent-adapters-are-opt-in-source-packages.md`.
- The OpenAI-first model-governance pass added a durable model catalog — source:
  `.cg-docs/BRAIN-01.md` (solution, 2026-06-16).

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Define a platform-generic `target-mapping.json` schema with capability flags so OpenCode and future platforms fit without structural change. | brainstorm decision |
| R2 | Build a generator (`scripts/cg_generate_targets.py`) that reads `.github/` canonical assets + `target-mapping.json` and emits native platform trees. | brainstorm next step 1 |
| R3 | Generate `.claude/` tree: commands from prompts, skills from skills, agents from agents, with role-to-tier Claude model mapping. | brainstorm requirement |
| R4 | Generate `.agents/` tree: Codex commands, review-agent TOML configs where supported, fallback skill/instruction path. | brainstorm decision (open problem 2) |
| R5 | Generate `.opencode/` tree: commands, skills, agents with multi-vendor model intent (role/tier, not exact names). | brainstorm requirement |
| R6 | Commit generated trees in the source repo; do not generate on user machines. | brainstorm decision |
| R7 | Extend `cg-link`/`cg-unlink` to link generated platform trees into consumer projects, gated behind an opt-in flag to preserve existing Copilot-only behavior. | brainstorm next step 8 |
| R8 | Add drift tests that fail when `.github/` changes but generated trees are stale. | brainstorm next step 6 |
| R9 | Add release validation that verifies generated native trees are current before publishing. | brainstorm next step 7 |
| R10 | Update docs: installation, reference, context-files, model-guide. | brainstorm next step 8 |
| R11 | Role-first model policy: canonical roles drive platform catalogs; exact model names asserted only where platform supports deterministic validation. | brainstorm decision (open problem 1) |
| R12 | Do not modify `.github/` canonical assets during generation. | brainstorm constraint |

## Implementation Steps

## Phase 1: Target-Mapping Schema and Generator Core

### 1. Define `target-mapping.json` schema and seed initial targets
- **Requirements**: R1, R11
- **Files**:
  - `.github/shared/target-mapping.json`
  - `scripts/schemas/target_mapping_schema.json` (JSON Schema for validation)
- **Details**:
  - Define platform-generic schema with capability flags: `supportsNativeCommands`,
    `supportsNativeSkills`, `supportsNativeSubagents`, `supportsMultiVendorModels`,
    `requiresRootAdapter`, `generatedTreePath`, `modelMappingMode` (`exact` |
    `tier` | `role-only`), `commandFormat`, `skillFormat`, `agentFormat`.
  - Seed four targets: `copilot` (passthrough — no generation, validates schema),
    `claude-code`, `codex`, `opencode`.
  - Each target declares its output root (`.claude/`, `.agents/`, `.opencode/`),
    native command path convention, native skill format, native agent/subagent
    format, and model mapping mode.
  - Copilot target has `generatedTreePath: null` and `modelMappingMode: role-only`
    (the `.github/` tree IS the Copilot output; no generation needed).
- **Test Scenarios**: schema validates with all four targets; missing required
  field fails validation; unknown platform rejected.
- **Tests**: `python3 -m pytest scripts/tests/test_target_mapping.py -q`
- **Acceptance criteria**: `target-mapping.json` validates against the JSON
  Schema and all four targets are representable without special-case fields.

### 2. Build `scripts/cg_generate_targets.py` generator core
- **Requirements**: R2, R12
- **Files**:
  - `scripts/cg_generate_targets.py`
  - `scripts/tests/test_cg_generate_targets.py`
- **Details**:
  - Python 3.8+, stdlib only (consistent with `cg_audit_context.py` and `cg_index.py`).
  - CLI: `python3 scripts/cg_generate_targets.py --root . --target <platform> [--all] [--dry-run]`
  - Reads `.github/prompts/*.prompt.md`, `.github/agents/*.agent.md`,
    `.github/skills/cg-skill-*/SKILL.md`, `.github/instructions/*.instructions.md`,
    `.github/shared/model-catalog.json`, and `.github/shared/target-mapping.json`.
  - Parses frontmatter (reuse `scripts/brain/utils.py:parse_frontmatter`).
  - For each enabled target, emit native files to the target's `generatedTreePath`.
  - Never write to `.github/`. Never modify source assets.
  - `--dry-run` reports what would be written without writing.
  - Exit 0 on success, 1 on error, 2 on invalid root.
  - Atomic writes (reuse `brain.utils.write_atomic`).
- **Test Scenarios**: fixture `.github/` with 2 prompts, 1 agent, 1 skill;
  generator produces expected file counts; dry-run produces no files; missing
  target-mapping fails cleanly; generator does not modify `.github/`.
- **Tests**: `python3 -m pytest scripts/tests/test_cg_generate_targets.py -q`
- **Acceptance criteria**: generator runs against the real repo without error
  and produces files in `.claude/`, `.agents/`, `.opencode/` (Phase 2-4 populate
  the platform-specific emitters; Phase 1 proves the core pipeline).

## Phase 2: Claude Code Target

### 3. Implement Claude Code emitter
- **Requirements**: R3, R11
- **Files**:
  - `scripts/generate/target_claude.py` (emitter module)
  - `.claude/` (generated output tree)
  - `scripts/tests/test_target_claude.py`
- **Details**:
  - Map `.github/prompts/cg-*.prompt.md` → `.claude/commands/cg-*.md` (Claude
    Code command format: frontmatter `description` + body).
  - Map `.github/skills/cg-skill-*/SKILL.md` → `.claude/skills/cg-skill-*/SKILL.md`
    (Claude Code skill format).
  - Map `.github/agents/cg-*.agent.md` → `.claude/agents/cg-*.md` (Claude Code
    subagent format: frontmatter `description` + body; tool list mapped to
    Claude Code tool names).
  - Model mapping: `modelMappingMode: tier` — map canonical role to Claude tier:
    `coding` → `sonnet`, `review` → `sonnet`, `reasoning` → `opus`, `mechanical`
    → `haiku`, `inherited` → omit (let Claude Code pick).
  - Exact model names marked `not-tested` unless validated; emit a
    `model-mapping.claude.json` artifact documenting the mapping and validation
    status.
  - Root adapter: emit `.claude/CLAUDE.md` from the existing
    `adapters/claude/CLAUDE.md` source, updated to reference native `.claude/`
    paths instead of `.github/` paths.
- **Test Scenarios**: every prompt produces a command file; every agent produces
  a subagent file; every skill produces a skill file; model tier mapping is
  correct per role; `CLAUDE.md` references `.claude/` paths.
- **Tests**: `python3 -m pytest scripts/tests/test_target_claude.py -q`
- **Acceptance criteria**: `.claude/` tree is complete, valid, and
  role-to-tier model mapping matches the canonical catalog assignments.

## Phase 3: Codex Target

### 4. Implement Codex emitter with subagent TOML
- **Requirements**: R4, R11
- **Files**:
  - `scripts/generate/target_codex.py` (emitter module)
  - `.agents/` (generated output tree)
  - `scripts/tests/test_target_codex.py`
- **Details**:
  - Map `.github/prompts/cg-*.prompt.md` → `.agents/commands/cg-*.md` (Codex
    command format).
  - Map `.github/agents/cg-*.agent.md` → `.agents/subagents/cg-*.toml` (native
    Codex subagent TOML config: `name`, `description`, `model`, `tools`).
  - Review agents (`cg-code-quality`, `cg-testing`, `cg-architecture`, etc.)
    get native TOML subagent configs.
  - Fallback: also emit `.agents/skills/cg-*.md` (skill/instruction format) for
    each agent, so runtimes without native subagent support can load the agent
    spec as a reference file. The fallback path is documented in
    `.agents/README.md`.
  - Model mapping: `modelMappingMode: exact` — map canonical role to OpenAI
    model: `coding` → `GPT-5.3-Codex`, `review` → `GPT-5.4`, `reasoning` →
    `GPT-5.4`, `mechanical` → `GPT-5.4 mini`, `inherited` → omit.
  - Emit `model-mapping.codex.json` artifact with validation status.
  - Root adapter: emit `.agents/AGENTS.md` from the existing
    `adapters/codex/AGENTS.md` source, updated to reference native `.agents/`
    paths.
- **Test Scenarios**: every prompt produces a command; every review agent
  produces a TOML subagent config; every agent also produces a fallback skill
  file; TOML config has required fields; model mapping is correct per role;
  `AGENTS.md` references `.agents/` paths.
- **Tests**: `python3 -m pytest scripts/tests/test_target_codex.py -q`
- **Acceptance criteria**: `.agents/` tree has native TOML subagents for review
  agents, fallback skill files for all agents, and correct OpenAI model mapping.

## Phase 4: OpenCode Target

### 5. Implement OpenCode emitter
- **Requirements**: R5, R11
- **Files**:
  - `scripts/generate/target_opencode.py` (emitter module)
  - `.opencode/` (generated output tree)
  - `scripts/tests/test_target_opencode.py`
- **Details**:
  - Map `.github/prompts/cg-*.prompt.md` → `.opencode/commands/cg-*.md` (OpenCode
    command format).
  - Map `.github/skills/cg-skill-*/SKILL.md` → `.opencode/skills/cg-skill-*/SKILL.md`.
  - Map `.github/agents/cg-*.agent.md` → `.opencode/agents/cg-*.md` (OpenCode
    agent format).
  - Model mapping: `modelMappingMode: role-only` — OpenCode is multi-vendor, so
    emit role/tier intent in agent frontmatter (e.g. `role: coding`, `tier:
    standard`) without hard-coding exact model names. Include a
    `model-mapping.opencode.json` artifact that documents the role-to-capability
    mapping and lets the user/local config resolve exact models.
  - Emit `.opencode/AGENTS.md` root adapter referencing `.opencode/` paths.
  - Emit `.opencode/opencode.json` or `.opencode/opencode.jsonc` config that
    registers the commands, skills, and agents directories if OpenCode supports
    declarative config.
- **Test Scenarios**: every prompt produces a command; every skill produces a
  skill file; every agent produces an agent file; model mapping is role-only
  (no exact vendor names); config file registers the trees.
- **Tests**: `python3 -m pytest scripts/tests/test_target_opencode.py -q`
- **Acceptance criteria**: `.opencode/` tree is complete and uses role/tier
  model intent without vendor-specific exact names.

## Phase 5: Distribution and Linker Extension

### 6. Extend `cg-link` and `cg-unlink` for platform trees
- **Requirements**: R6, R7
- **Files**:
  - `scripts/link.ps1`
  - `scripts/link.sh`
  - `scripts/unlink.ps1`
  - `scripts/unlink.sh`
  - `scripts/helpers.ps1`
  - `bin/cg-link`, `bin/cg-link.cmd` (if new flags needed)
  - `tests/link.Tests.ps1`
  - `tests/unlink.Tests.ps1`
  - `tests/bash-scripts.Tests.ps1`
- **Details**:
  - Add `--platforms <comma-separate-list>` flag to `cg-link` (default: `copilot`
    only, preserving existing behavior). Example: `cg-link --platforms copilot,claude-code,codex`.
  - When a platform is requested, create junctions/symlinks for the platform's
    `generatedTreePath` subdirectories into the consumer project root (e.g.
    `.claude/commands/` → global `.claude/commands/`).
  - `cg-unlink` removes platform junctions/symlinks it created.
  - Gitignore entries extended to cover platform-managed directories.
  - Verification step checks a known file in each linked platform tree.
  - Existing Copilot-only `cg-link` (no `--platforms` flag) must produce
    identical behavior to today.
- **Test Scenarios**: default `cg-link` links only `.github/` (existing
  behavior); `--platforms copilot,claude-code` links `.github/` + `.claude/`;
  `cg-unlink` removes all platform links; idempotent re-link; conflict with
  user-owned `.claude/` directory.
- **Tests**: `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File link"` +
  `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File unlink"` +
  `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File bash-scripts"`
- **Acceptance criteria**: existing Copilot-only link/unlink tests pass
  unchanged; new platform-link tests pass on Windows + macOS.

### 7. Update `cg-update` to refresh generated trees
- **Requirements**: R6, R9
- **Files**:
  - `scripts/update.ps1`
  - `scripts/update.sh`
  - `tests/update.Tests.ps1`
- **Details**:
  - `cg-update` runs `cg_generate_targets.py --all` after pulling the latest
    source, so the global clone's generated trees are always current.
  - If generation fails, warn but do not block (user may be offline); existing
    generated trees remain linked.
  - Consumer projects that linked platform trees see updates immediately via
    junctions/symlinks (same propagation model as `.github/`).
- **Test Scenarios**: `cg-update` regenerates trees; generation failure warns
    but does not break existing links.
- **Tests**: `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File update"`
- **Acceptance criteria**: `cg-update` refreshes generated trees after pull.

## Phase 6: Drift Tests, Release Gate, and Documentation

### 8. Add generator drift tests
- **Requirements**: R8
- **Files**:
  - `scripts/tests/test_target_drift.py`
- **Details**:
  - Test runs `cg_generate_targets.py --all --dry-run` against the current
    `.github/` source and compares the dry-run output manifest against the
    committed generated trees.
  - If any file would change, the test fails with a diff showing which files
    are stale.
  - If any committed generated file is not in the dry-run manifest, the test
    fails (orphaned file).
  - Test also verifies `.github/` was not modified by the generator.
- **Test Scenarios**: clean repo passes; modify a `.github/prompts/` file
  without regenerating → test fails; orphaned file in `.claude/` → test fails.
- **Tests**: `python3 -m pytest scripts/tests/test_target_drift.py -q`
- **Acceptance criteria**: drift test detects stale and orphaned generated files.

### 9. Add release gate validation
- **Requirements**: R9
- **Files**:
  - `cg-release.prompt.md` (update Step 2 or add a pre-release check)
  - `scripts/tests/test_release_gate_targets.py`
- **Details**:
  - Release gate runs the drift test before allowing a release.
  - If generated trees are stale, the release is blocked with a message:
    "Generated platform trees are stale. Run
    `python3 scripts/cg_generate_targets.py --all` and commit before releasing."
  - Also verify `adapters/manifest.json` is consistent with `target-mapping.json`
    (or document that `adapters/` is superseded by generated trees).
- **Test Scenarios**: stale trees block release; fresh trees pass.
- **Tests**: `python3 -m pytest scripts/tests/test_release_gate_targets.py -q`
- **Acceptance criteria**: release gate blocks on stale generated trees.

### 10. Update documentation
- **Requirements**: R10
- **Files**:
  - `docs/installation.md`
  - `docs/reference.md`
  - `docs/context-files.md`
  - `docs/model-guide.md`
  - `README.md`
  - `adapters/README.md` (update or mark as superseded)
- **Details**:
  - Document `--platforms` flag in installation and reference docs.
  - Explain that generated trees are committed, release-validated, and
    distributed via junctions/symlinks.
  - Update model-guide to describe role-to-tier platform mapping.
  - Update context-files.md to describe `.claude/`, `.agents/`, `.opencode/`
    as generated native trees (not user-edited).
  - Mark `adapters/` as superseded by generated trees (keep for backward compat
    reference but point to the new mechanism).
  - Add a "Platform Support" section to README.
- **Test Scenarios**: prompt-tools tests pass (docs structure validation).
- **Tests**: `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"`
- **Acceptance criteria**: docs reflect the new architecture and pass doc
  structure tests.

### 11. Final validation and evidence
- **Requirements**: R8, R9, R12
- **Files**:
  - `.cg-docs/work-reports/2026-07-03-cross-agent-native-platform-targets.md`
  - `.cg-docs/reviews/*cross-agent-native-platform-targets*`
  - `roadmap.json` (via `@cg-roadmap`)
- **Details**:
  - Run all generator tests, drift tests, link/unlink tests, model-assignment
    tests, prompt-tools tests, and the full safe runner.
  - Record evidence in the execution report.
  - Mark roadmap features done via `@cg-roadmap`.
- **Tests**:
  - `python3 -m pytest scripts/tests/test_target_mapping.py scripts/tests/test_cg_generate_targets.py scripts/tests/test_target_claude.py scripts/tests/test_target_codex.py scripts/tests/test_target_opencode.py scripts/tests/test_target_drift.py scripts/tests/test_release_gate_targets.py -q`
  - `python3 -m pytest scripts/tests/test_agent_adapters.py -q`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"`
  - `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"`
  - `git diff --check`
- **Acceptance criteria**: all tests pass; generated trees are current; docs
  are updated; roadmap features marked done.

## Testing Strategy

- **Generator unit tests**: fixture-based tests with a minimal `.github/` tree,
  validating output file structure, frontmatter, model mapping, and no-source-
  modification invariant.
- **Platform emitter tests**: per-platform tests validating native format
  compliance, model mapping mode, and completeness (every canonical asset has
  a native counterpart).
- **Drift tests**: dry-run comparison against committed generated trees.
- **Linker tests**: extend existing `link.Tests.ps1` / `unlink.Tests.ps1` /
  `bash-scripts.Tests.ps1` with `--platforms` scenarios; existing Copilot-only
  tests must pass unchanged.
- **Safe runner**: full Pester suite via `. ./tests/Run-Tests.ps1`.
- **Python tests**: `python3 -m pytest scripts/tests/ -q` integrated via the
  platform-guarded Pester wrapper in `Run-Tests.ps1`.

## Documentation Checklist

- [ ] `docs/installation.md` documents `--platforms` flag and per-platform setup.
- [ ] `docs/reference.md` lists generated trees and their contents.
- [ ] `docs/context-files.md` describes `.claude/`, `.agents/`, `.opencode/` as
      generated, release-validated, non-user-edited.
- [ ] `docs/model-guide.md` documents role-to-tier platform model mapping.
- [ ] `README.md` has a "Platform Support" section.
- [ ] `adapters/README.md` marked as superseded by generated trees.

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Generated trees go stale silently | Drift test (Phase 6) + release gate (Phase 6) |
| `cg-link --platforms` breaks existing Copilot-only users | Default is `copilot` only; new behavior is opt-in via flag |
| Platform native format changes | Generator emits closest stable equivalent; documents gaps in per-platform README |
| Exact model names become stale | Role-first policy; exact names only where validated; `not-tested` status documented |
| Generator modifies `.github/` | Invariant test + `--dry-run` mode; generator only reads `.github/` |
| `adapters/` and generated trees diverge | Drift test checks consistency; `adapters/README.md` marks superseded |
| OpenCode format is unfamiliar/undocumented | Emit role/tier intent without exact names; document as best-effort |
| Large generated tree bloats repo | Generated files are small (Markdown + TOML + JSON); junction-based distribution means consumers don't duplicate |
| macOS symlink vs Windows junction differences | Reuse existing cross-platform linker pattern from `link.ps1`/`link.sh` |

## Out of Scope

- Full neutral-schema rewrite of `.github/` into a platform-independent source.
- Generating platform trees on user machines during install.
- External retrieval backends, vector search, MCP integrations.
- Cursor adapter generation.
- Live runtime model validation in Claude Code, Codex, or OpenCode sessions.
- Migrating `adapters/manifest.json` consumers to the new mechanism (backward
  compat — old adapters remain valid source packages).

## Completion Contract

### Outcome

Compound GPID generates committed native platform trees (`.claude/`, `.agents/`,
`.opencode/`) from the canonical `.github/` source via a `target-mapping.json`
schema, distributes them through the existing junction/symlink mechanism, and
blocks release if generated trees are stale — so users on Claude Code, Codex,
and OpenCode get native commands, skills, and agents without knowing about
`.github/`.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | `target-mapping.json` schema validates; generator runs without error | `python3 -m pytest scripts/tests/test_target_mapping.py -q` | yes |
| V2 | 1 | Generator produces expected file counts from a fixture `.github/` | `python3 -m pytest scripts/tests/test_cg_generate_targets.py -q` | yes |
| V3 | 2 | `.claude/` tree contains commands, skills, agents with role-to-tier model mapping | `python3 -m pytest scripts/tests/test_target_claude.py -q` | yes |
| V4 | 3 | `.agents/` tree contains Codex commands + review-agent TOML configs + fallback skills | `python3 -m pytest scripts/tests/test_target_codex.py -q` | yes |
| V5 | 4 | `.opencode/` tree contains commands, skills, agents with multi-vendor model intent | `python3 -m pytest scripts/tests/test_target_opencode.py -q` | yes |
| V6 | 5 | `cg-link` links platform trees into a test project; `cg-unlink` removes them | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File link"` | yes |
| V7 | 6 | Drift test fails when `.github/` changes but generated trees are stale | `python3 -m pytest scripts/tests/test_target_drift.py -q` | yes |
| V8 | final | Full safe runner passes | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1"` | yes |
| V9 | final | Docs updated: installation, reference, context-files, model-guide | `pwsh -NoProfile -Command ". ./tests/Run-Tests.ps1 -File prompt-tools"` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | `.github/` canonical assets are not modified by the generator | diff review — no `.github/` files changed |
| C2 | 1 | `target-mapping.json` is platform-generic; no platform-specific schema forks | schema validation test |
| C3 | 2-4 | Exact model names asserted only where platform supports deterministic validation | model-mapping test per platform |
| C4 | 3 | Codex review agents have fallback skill/instruction path when TOML subagents unsupported | fallback path test |
| C5 | 5 | Existing Copilot-only `cg-link` behavior does not break | link tests pass on Windows + macOS |
| C6 | 6 | Existing `adapters/manifest.json` tests still pass or are explicitly superseded | `python3 -m pytest scripts/tests/test_agent_adapters.py -q` |
| C7 | all | Safe Pester runner only; no direct `Invoke-Pester` pipeline | command evidence |

### Boundaries

- **Allowed**: New `scripts/cg_generate_targets.py`, `target-mapping.json`, generated `.claude/`, `.agents/`, `.opencode/` trees, new tests, linker extensions, docs updates
- **Out of scope**: Full neutral-schema rewrite of `.github/`; generating platform trees on user machines; external retrieval backends; MCP integrations; Cursor adapter; model-name runtime validation in live sessions

### Iteration Policy

1. Build generator + schema first (Phase 1); validate with fixtures before touching real assets.
2. Generate one platform at a time (Claude → Codex → OpenCode); test each before next.
3. If a platform's native format is undocumented or unstable, emit the closest stable equivalent and document the gap — do not block the release.
4. Model catalogs: prefer role/tier intent; add exact names only when testable. Mark unvalidated names as `not-tested`.
5. If `cg-link` extension would break existing Copilot-only users, gate platform-tree linking behind an opt-in flag rather than changing default behavior.

### Blocked-Stop Conditions

- Generator cannot parse existing `.github/` canonical assets without modifying them.
- `target-mapping.json` schema cannot represent a platform without a structural fork.
- `cg-link` extension breaks existing Copilot-only link tests on Windows or macOS.
- Drift test framework cannot reliably detect stale generated trees.
- Full safe runner fails after scoped fixes.
