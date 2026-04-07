---
date: 2026-04-06
title: "Standalone R testing skill modeled on Posit's testing-r-packages"
status: decided
chosen-approach: "Full Posit Mirror — Adapted for collapse/data.table"
tags: [testing, r, skill, testthat, quality-loop]
---

# Standalone R Testing Skill

## Context

The Quality Loop milestone includes a `testing-skill-r` feature (testthat/mockery). The existing testing content lives in `cg-skill-r-technical/references/testing-testthat.md` (~240 lines) — a single file covering basics, collapse/data.table testing, plumber endpoints, and httr2 mocking. Posit published a dedicated `testing-r-packages` skill (https://github.com/posit-dev/skills/tree/main/r-lib/testing-r-packages) with a proven structure: SKILL.md + 5 reference files (bdd, mocking, fixtures, snapshots, advanced). The goal is to create a dedicated testing skill optimized for AI consumption.

## Requirements

1. **Standalone skill** — `cg-skill-r-testing/` in its own folder, not embedded in `cg-skill-r-technical`
2. **Absorb and replace** — the existing `testing-testthat.md` content moves into the new skill; `cg-skill-r-technical` gets a one-line redirect
3. **All 5 reference files** — bdd.md, mocking.md, fixtures.md, snapshots.md, advanced.md — demand-loaded, zero cost when not needed
4. **collapse/data.table first** — all examples prefer collapse and data.table; tidyverse only as fallback. Cross-reference `cg-skill-r-technical` and `cg-skill-r-analytical` for package-specific depth
5. **General, not GPID-specific** — content is portable to any R project; team-specific context comes from the cross-referenced skills
6. **Optimized for AI consumption** — dense, pattern-heavy, no tutorial prose; the SKILL.md description is the trigger mechanism
7. **Plumber/httr2 testing patterns** — move to a new `cg-skill-r-technical/references/testing-apis.md` file (they belong with the technology, not with testthat)
8. **Skill collision prevention** — `cg-skill-r-technical` must defer to `cg-skill-r-testing` for all testing content; no duplication

## Approaches Considered

### Approach 1: Full Posit Mirror — Adapted for collapse/data.table (CHOSEN)

Mirror Posit's `testing-r-packages` structure: SKILL.md (~300 lines) + 5 reference files. Content rewritten with collapse/data.table examples and cross-references to existing skills. Existing `testing-testthat.md` replaced with redirect; plumber/httr2 patterns moved to `testing-apis.md`.

**Pros**: Proven structure, demand-loaded references, single source of truth, easy to maintain.
**Cons**: Largest upfront effort; must tune description for correct triggering; collateral updates to `cg-skill-r-technical` and `copilot-instructions.md`.
**Effort**: Medium.

### Approach 2: Compact Single-File Skill + 2 References

One SKILL.md (~400 lines) with only mocking.md and fixtures.md as references. BDD, snapshots, and advanced topics folded into the main file.

**Pros**: Fewer files, more immediate context for AI.
**Cons**: Larger base token cost, mixes essential and occasional content, diverges from proven structure.
**Effort**: Small-medium.

### Approach 3: Fork Posit's Skill Directly + Overlay

Copy Posit's files verbatim, add collapse/data.table overlays in marked sections.

**Pros**: Fastest to build, easy upstream sync.
**Cons**: Tidyverse-first base fights our overlays, dual voice confuses AI, maintenance burden on re-merge.
**Effort**: Small.

## Decision

**Approach 1** — Full Posit Mirror adapted for collapse/data.table. The proven structure keeps reference files demand-loaded (zero token cost when not needed), gives the `cg-testing` agent a focused skill to load, and avoids content duplication across skills. Writing our own content ensures collapse/data.table primacy without fighting a tidyverse-oriented base.

## Next Steps

1. Create `cg-skill-r-testing/SKILL.md` with frontmatter description optimized for skill triggering
2. Create 5 reference files: `bdd.md`, `mocking.md`, `fixtures.md`, `snapshots.md`, `advanced.md`
3. Replace `cg-skill-r-technical/references/testing-testthat.md` with a redirect to the new skill
4. Create `cg-skill-r-technical/references/testing-apis.md` with plumber/httr2 testing patterns
5. Update `copilot-instructions.md` skill listing to include `cg-skill-r-testing`
6. Update `cg-testing` agent description to reference the new skill
7. Register in `copilot-instructions.md` under the skills block with correct `applyTo` pattern
