---
date: 2026-03-05
title: "Migrate docs/ to .cg-docs/ and add /cg-resume prompt"
status: decided
chosen-approach: "Clean Auto-Migration"
tags: [migration, docs, cg-resume, rbuildignore, update-script]
---

# Migrate docs/ to .cg-docs/ and Add /cg-resume Prompt

## Context

Several projects already use `docs/` for their own purposes (pkgdown sites, Sphinx/MkDocs output, plain documentation). Compound GPID currently stores brainstorms, plans, and solutions under `docs/`, which risks colliding with existing project structure. Additionally, there is no way to resume interrupted work — users must manually remember where they left off.

## Requirements

1. **Rename `docs/{brainstorms,plans,solutions}` → `.cg-docs/{brainstorms,plans,solutions}`** across all prompts, skills, agents, and documentation.
2. **Keep `docs/manual.md` in `docs/`** — it's user-facing documentation for the compound-gpid repo itself.
3. **Auto-migrate existing users**: `update.ps1` should detect if the current project has `docs/brainstorms/`, `docs/plans/`, or `docs/solutions/` and move them to `.cg-docs/`.
4. **Migrate compound-gpid's own repo**: move `docs/brainstorms/`, `docs/plans/`, `docs/solutions/` to `.cg-docs/` in this repo.
5. **R package `.Rbuildignore` support**:
   - `/cg-setup` adds `.cg-docs/` to `.Rbuildignore` when user selects "R package" project type.
   - `/cg-review` (code quality agent) defensively checks: if R package signals exist (`DESCRIPTION`, `NAMESPACE`, `R/`) and `.cg-docs/` is present but not in `.Rbuildignore`, flag as P2.
6. **New `/cg-resume` prompt**: scans `.cg-docs/plans/` for `status: in-progress`, `.cg-docs/brainstorms/` for `status: decided` without a corresponding plan, checks recent git history, and summarizes what to pick up next.

## Approaches Considered

### Approach 1: Clean Auto-Migration (Chosen)

All references update to `.cg-docs/` in one release. `update.ps1` auto-migrates folders in linked projects. No dual-path complexity.

**Pros**:
- Clean mental model — one path, no ambiguity
- Small user base makes a clean cut safe
- Junction-based architecture means prompt/skill changes propagate instantly on `cg-update`

**Cons**:
- Users who don't run `cg-update` from their project directory won't get the folder migration (but will get updated prompts via junctions)
- ~130+ path references to update across ~22 files

**Effort**: Medium

### Approach 2: Dual-Path Transition

Prompts check both `.cg-docs/` and `docs/` during a transition period.

**Pros**: Zero risk of breaking anyone
**Cons**: Doubles complexity, hard to clean up later, unnecessary for small user base
**Effort**: Large

### Approach 3: Manual Migration with Guidance

Change references but don't auto-migrate. Print instructions instead.

**Pros**: Simplest code
**Cons**: Poor UX, users will forget
**Effort**: Small

## Decision

**Approach 1: Clean Auto-Migration** — chosen because the user base is small (early adopters only), the junction architecture means prompt changes propagate automatically, and dual-path complexity is not justified.

## Next Steps

1. **Update all prompt files** (6 files): replace `docs/brainstorms`, `docs/plans`, `docs/solutions` → `.cg-docs/brainstorms`, `.cg-docs/plans`, `.cg-docs/solutions`
2. **Update all agent files** (1 file): `cg-learnings-researcher.agent.md`
3. **Update all skill files** (6 files): setup, compound-docs, brainstorming, git-workflow
4. **Update `copilot-instructions.md`**: `docs/solutions/` → `.cg-docs/solutions/`
5. **Update `README.md`** and **`ROADMAP.md`**: path references
6. **Update `docs/manual.md`**: all path references to brainstorms/plans/solutions
7. **Add migration logic to `update.ps1`**: detect and move `docs/{brainstorms,plans,solutions}` → `.cg-docs/`
8. **Update `cg-setup` prompt**: scaffold `.cg-docs/` instead of `docs/`, add `.Rbuildignore` logic for R packages
9. **Add `.Rbuildignore` check to review agent**: P2 finding if R package + `.cg-docs/` without `.Rbuildignore` entry
10. **Create `/cg-resume` prompt**: scan `.cg-docs/plans/` and `.cg-docs/brainstorms/`, check git log, summarize pending work
11. **Migrate compound-gpid's own folders**: move `docs/{brainstorms,plans,solutions}` → `.cg-docs/`
12. **Update existing docs in `.cg-docs/`**: fix self-references in brainstorms/plans/solutions files
13. **Add `.cg-docs/` to `.gitignore` entries in `link.ps1`**: ensure it's gitignored in linked projects
