---
date: 2026-03-20
title: "Merge Stata skills into cg-skill-stata-best-practices"
status: completed
brainstorm: null
language: "Stata"
estimated-effort: "medium"
tags: [skills, stata, refactor, cleanup]
---

# Plan: Merge Stata Skills into `cg-skill-stata-best-practices`

## Objective

Consolidate the three Stata skills (`stata`, `cg-skill-stata-core`, `cg-skill-stata-research`) into a single unified skill called `cg-skill-stata-best-practices`. Enrich the new skill with universal coding principles from the old skills. Remove all GPID-specific content. Delete the old skills and update all references project-wide.

## Context

The project currently has three Stata skills:
- **`stata`** — new, comprehensive general reference (37 reference files, 20 package files)
- **`cg-skill-stata-core`** — GPID-specific but contains universal principles (4 workflow files, 2 reference files)
- **`cg-skill-stata-research`** — GPID-specific with some universal principles (4 workflow files, 2 reference files)

Per brainstorm decision, the new `stata` skill becomes the base. Universal coding principles from the old skills are added. GPID-specific content is dropped.

### What's IN (universal principles to carry forward):
- Compound double quotes deep dive
- Eager macro expansion trap
- Stored results disappearance pattern
- `subpop()` vs `if` with `svy:` commands
- Clustering at the correct level
- Anti-patterns (universal ones from both old skills)
- `repkit` for reproducibility (as a package reference file)

### What's OUT (GPID-specific, dropped):
- GPID headers and do-file template
- `gpid_` naming conventions
- 6-phase research workflow
- PPP/FGT/welfare/shared prosperity content
- Weak instruments warning
- Staggered DiD warning

## Implementation Steps

### 1. Rename `stata/` → `cg-skill-stata-best-practices/`
- **Files**: Rename folder `.github/skills/stata/` → `.github/skills/cg-skill-stata-best-practices/`
- **Details**:
  - Use `git mv` to rename the folder (preserves history)
  - Update `SKILL.md` YAML frontmatter: `name: cg-skill-stata-best-practices`
  - Update SKILL.md description to reflect best-practices focus
  - Add `references/coding-principles.md` and `packages/repkit.md` to the routing table
- **Tests**: Verify folder exists, old folder does not
- **Acceptance criteria**: Skill folder renamed, SKILL.md updated

### 2. Create `references/coding-principles.md`
- **Files**: `.github/skills/cg-skill-stata-best-practices/references/coding-principles.md`
- **Details**: New file with universal Stata coding principles extracted from old skills:
  1. **Compound Double Quotes** — when and why to use them; opening/closing delimiter syntax; rule of thumb for when to apply (from `stata-core/workflows/macro-system.md` §2)
  2. **Eager Macro Expansion** — macros store strings not formulas; inner references resolved at assignment; must rebuild inside loops (from `stata-core/workflows/macro-system.md` §3)
  3. **Stored Results Disappear** — `r()` and `e()` overwritten by next command; save to locals immediately (from `stata-core/workflows/program-scoping.md` §2)
  4. **`subpop()` vs `if` with `svy:`** — `if` corrupts variance estimation; `subpop()` preserves full design (from `stata-research/workflows/survey-poverty.md` §2)
  5. **Clustering at the Correct Level** — cluster at level of treatment assignment or higher; few-cluster considerations (from `stata-research/references/stata-research-anti-patterns.md` #6)
  6. **Anti-Patterns Checklist** — universal items from both old skills:
     - `=` vs `==` in `if` conditions
     - String vs numeric type confusion
     - `replace` without units comment
     - Missing `quietly` in loops/programs
     - `merge` without checking `_merge`
     - `append` losing variable labels
     - Globals in production do-files
     - Missing `set more off` and `version`
     - `log using` without `replace`/`append`
     - `forvalues` vs `foreach` confusion
     - Unweighted statistics on survey data
     - `if` instead of `subpop()` (cross-ref to §4)
     - Missing overlap check before matching
     - P-hacking via specification search
     - Missing values in inequality measures
  - All examples must be generic (no `gpid_`, no poverty lines, no welfare variables)
- **Tests**: File exists, no GPID-specific references
- **Acceptance criteria**: Complete principles file with WRONG/RIGHT code examples

### 3. Create `packages/repkit.md`
- **Files**: `.github/skills/cg-skill-stata-best-practices/packages/repkit.md`
- **Details**: Comprehensive reference for the `repkit` Stata package, sourced from:
  - GitHub README (https://github.com/worldbank/repkit) — overview, installation, command table
  - Vignette: `ado-management-with-repado.md` — principle, setup, usage, nostrict mode, self-install limitation
  - Vignette: `reprun-examples.md` — usage, output interpretation, examples
  - Vignette: `reproot-files.md` — root files, env settings, multi-root projects
  - Vignette: `lint-examples.md` + `linting-rules.md` — detection, correction, rules list
  - Vignette: `schemes-with-repado.md` — custom schemes in strict mode
  - Content organized into sections: Overview, Installation, Commands (repado, repadolog, reproot, reproot_setup, reprun, repscan, lint), Common Workflows
- **Tests**: File exists, content covers all 7 commands
- **Acceptance criteria**: Comprehensive repkit reference usable without visiting the GitHub repo

### 4. Update `SKILL.md` routing table
- **Files**: `.github/skills/cg-skill-stata-best-practices/SKILL.md`
- **Details**:
  - Add `references/coding-principles.md` to routing table under new "Best Practices" section
  - Add `packages/repkit.md` to the Community Packages section in routing table
  - Update skill name and description in YAML frontmatter
  - Keep the "Critical Gotchas" section as-is (already universal)
  - Keep the "Running Stata from the Command Line" section as-is
  - Keep "Common Patterns" section as-is
- **Tests**: All routing table links resolve to actual files
- **Acceptance criteria**: Routing table complete, YAML frontmatter correct

### 5. Delete old skill folders
- **Files**: Delete entire folders:
  - `.github/skills/cg-skill-stata-core/`
  - `.github/skills/cg-skill-stata-research/`
- **Details**: Use `git rm -r` to remove tracked files
- **Tests**: Folders no longer exist
- **Acceptance criteria**: Old skill folders completely removed

### 6. Update `copilot-instructions.md`
- **Files**: `.github/copilot-instructions.md`
- **Details**:
  - Lines 12-13: Replace the "Two Stata skills" block. Change to single skill reference: `cg-skill-stata-best-practices`
  - Line 29: Replace `cg-skill-stata-core` and `cg-skill-stata-research` with `cg-skill-stata-best-practices`
- **Tests**: `grep` for `stata-core` and `stata-research` returns zero matches
- **Acceptance criteria**: All references point to `cg-skill-stata-best-practices`

### 7. Update `stata.instructions.md`
- **Files**: `.github/instructions/stata.instructions.md`
- **Details**:
  - Lines 7-9: Replace the "Full guidance" block that references both old skills with a single reference to `cg-skill-stata-best-practices`
- **Tests**: `grep` for `stata-core` and `stata-research` returns zero matches
- **Acceptance criteria**: Instructions file references single skill

### 8. Update agent files (7 files)
- **Files**:
  - `.github/agents/cg-architecture.agent.md` (line 12)
  - `.github/agents/cg-code-quality.agent.md` (line 46)
  - `.github/agents/cg-data-quality.agent.md` (line 12)
  - `.github/agents/cg-documentation.agent.md` (line 12)
  - `.github/agents/cg-performance.agent.md` (line 12)
  - `.github/agents/cg-reproducibility.agent.md` (line 11)
  - `.github/agents/cg-testing.agent.md` (line 12)
  - `.github/agents/cg-version-control.agent.md` (line 12)
- **Details**: In each file, replace all occurrences of `cg-skill-stata-core` and `cg-skill-stata-research` with `cg-skill-stata-best-practices`. Simplify the "additionally load" pattern to just "load `cg-skill-stata-best-practices`".
- **Tests**: `grep` for `stata-core` and `stata-research` across all `.agent.md` files returns zero matches
- **Acceptance criteria**: All 8 agent files reference single skill

### 9. Update prompt files (3 files)
- **Files**:
  - `.github/prompts/cg-work.prompt.md` (line 20)
  - `.github/prompts/cg-fixbug.prompt.md` (line 74)
  - `.github/prompts/cg-review.prompt.md` (line 55)
- **Details**: Replace all `cg-skill-stata-core` / `cg-skill-stata-research` references with `cg-skill-stata-best-practices`. Simplify the two-skill loading pattern.
- **Tests**: `grep` for `stata-core` and `stata-research` across all `.prompt.md` files returns zero matches
- **Acceptance criteria**: All 3 prompt files reference single skill

### 10. Final verification
- **Details**:
  - Run `grep -r "stata-core\|stata-research\|cg-skill-stata-core\|cg-skill-stata-research"` across the entire `.github/` folder
  - Verify zero matches
  - Verify `cg-skill-stata-best-practices` folder contains: `SKILL.md`, `references/` (38 files), `packages/` (21 files)
- **Acceptance criteria**: No stale references remain anywhere in the project

## Testing Strategy

- **Reference integrity**: All file paths in SKILL.md routing table resolve to actual files
- **No stale references**: Grep across `.github/` for old skill names returns zero matches
- **Content completeness**: `coding-principles.md` covers all 6 principle categories
- **repkit completeness**: `repkit.md` covers all 7 commands (repado, repadolog, repkit, reproot, reproot_setup, reprun, repscan, lint — 8 total including lint)

## Documentation Checklist
- [x] SKILL.md frontmatter updated
- [ ] Routing table entries for new files
- [ ] `coding-principles.md` has correct WRONG/RIGHT examples
- [ ] `repkit.md` is self-contained reference

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Missed reference to old skill names | Final grep verification (Step 10) |
| Principles file too long | Keep focused on principles, not full tutorials — link to existing reference files for details |
| repkit.md content stale | Source directly from GitHub repo; note version (v4.0) |

## Out of Scope

- Modifying the content of existing reference files in the `stata` skill (they're already correct)
- Creating new workflow files (the old workflow structure is dropped)
- Updating `.cg-docs/plans/` or `.cg-docs/brainstorms/` that mention old skills (historical records)
- Updating memory files (repo memory note references old skills — will be updated separately)
