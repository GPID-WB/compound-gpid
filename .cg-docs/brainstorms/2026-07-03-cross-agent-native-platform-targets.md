---
date: 2026-07-03
title: "Cross-Agent Native Platform Targets"
status: decided
scope: "Deep"
chosen-approach: "Hybrid canonical .github source with generated native targets"
tags: [cross-agent, adapters, claude-code, codex, opencode, model-governance, distribution]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# Cross-Agent Native Platform Targets

## Context

Compound GPID currently uses `.github/` as the canonical Copilot-oriented asset
tree for prompts, agents, skills, shared contracts, and instructions. The repo
also ships optional root-level compatibility adapters for Codex and Claude Code,
but those adapters are not native platform trees and are not distributed through
the normal `cg-link`/junction mechanism.

The new goal is to support Claude Code, Codex, and OpenCode alongside GitHub
Copilot so users can install Compound GPID in any supported platform and use
native commands, skills, and agents without needing to know the assets originated
in `.github/`.

The main strategic constraints are:

- Preserve a single maintainable source of truth.
- Keep release validation strong by testing generated platform outputs before
  shipping.
- Avoid making consumer projects generate platform trees locally during install.
- Handle platform-specific model behavior, especially vendor-specific runtimes
  such as Codex and Claude Code versus multi-vendor runtimes such as GitHub
  Copilot and OpenCode.

## Requirements

- Keep `.github/` as the primary human-authored source for current Compound GPID
  workflow assets unless a future migration proves a neutral schema is worth the
  cost.
- Generate native platform trees for Claude Code, Codex, and OpenCode from the
  canonical assets and mapping metadata.
- Commit generated platform trees in the source repository and validate them in
  CI/release gates.
- Extend the existing global clone plus junction/symlink distribution mechanism
  so consumer projects receive generated native trees rather than generating
  them locally.
- Use role-to-tier model policy as the canonical abstraction, with
  platform-specific catalogs generated only where exact model names are useful
  and testable.
- Generate Codex review agents as native subagent TOML configs where supported,
  with a fallback skill/instruction path for runtimes without native subagents.
- Design `target-mapping.json` as a generic target schema with capability flags
  so OpenCode and future platforms can be added without structural schema
  changes.

## Approaches Considered

### Approach 1: Keep Current Adapter Model

Keep `.github/` canonical and ship only root-level compatibility adapters such
as `AGENTS.md` and `CLAUDE.md`.

**Pros**: Smallest change; builds on the current adapter package; preserves the
existing Copilot behavior boundary.

**Cons**: Does not provide native commands, skills, or agents; users still rely
on adapter interpretation; drift risk grows as more platforms are supported.

### Approach 2: Full Neutral Schema Rewrite

Move commands, prompts, skills, agents, model policy, and platform behavior into
a new platform-neutral schema, then generate `.github/` and every other platform
tree from that schema.

**Pros**: Clean long-term architecture; every platform is a generated target;
the canonical format is not tied to GitHub Copilot.

**Cons**: High migration risk; large rewrite; likely to disrupt existing
Copilot-first behavior; difficult to validate in one iteration.

### Approach 3: Hybrid Canonical `.github/` with Generated Native Targets

Keep `.github/` as the canonical human-authored asset tree, add a small target
mapping layer, and generate committed native target trees for Claude Code,
Codex, and OpenCode.

**Pros**: Maintainers edit once; current Copilot assets remain stable; users get
native platform UX; generated outputs can be tested before release; OpenCode can
be modeled as another capability-defined target.

**Cons**: Requires generator tooling, drift tests, release gates, and careful
platform-specific validation; model catalogs can become stale if exact model
names are overasserted.

## Decision

Choose **Approach 3: Hybrid Canonical `.github/` with Generated Native
Targets**.

`.github/` remains the canonical authoring surface for prompts, agents, skills,
instructions, and shared contracts. A small target-mapping schema will define how
canonical assets are emitted for each supported runtime. The generated native
trees are committed in the source repo and validated before release, then
distributed through the same global clone plus junction/symlink mechanism rather
than generated inside user projects.

Model governance should remain role-first. Canonical policy assigns assets to
roles such as `coding`, `review`, `reasoning`, `mechanical`, and `inherited`.
Platform-specific catalogs can be generated where useful, but exact model names
should only be asserted where the platform behavior is actionable and release
validation can confirm it. Multi-vendor platforms should prefer role/tier intent
plus local override hooks over brittle exact defaults.

Codex review agents should be generated as native subagent TOML configs when
Codex supports them. The generator should also emit a fallback skill/instruction
path for runtimes or versions that cannot use native subagents.

`target-mapping.json` should be platform-generic, with capability flags such as
native command support, native skill support, native subagent support,
multi-vendor model support, root-adapter requirements, generated-tree path, and
model-mapping mode. OpenCode should fit this schema as another target, not as a
special-case fork.

## Next Steps

1. Draft a plan for the hybrid generator architecture and release gate.
2. Define the first version of `target-mapping.json` with generic platform
   capability flags.
3. Decide target output paths for Claude Code, Codex, and OpenCode, including
   whether `.agents/` and `.opencode/` are separate outputs or one nested
   OpenCode/agents convention.
4. Extend model governance from the current model catalog into role-first
   platform mapping and generated target catalogs.
5. Prototype Codex review-agent TOML generation with fallback skill/instruction
   output.
6. Add generator drift tests that fail when `.github/` changes without refreshed
   generated platform trees.
7. Add release validation that verifies generated native trees are current before
   publishing a release.
8. Update distribution docs and linker behavior once the generated outputs are
   validated.
