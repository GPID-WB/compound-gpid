---
date: 2026-03-19
title: "Review and integrate cg-skill-stata-research + update references across the project"
status: superseded
language: "both"
estimated-effort: "medium"
tags: [skills, stata, documentation, integration, review]
---

# Plan: Review and Integrate cg-skill-stata-research

## Objective

The new `cg-skill-stata-research` skill has been created with six sub-files covering research methodology, survey/poverty measurement, causal inference, publication outputs, research anti-patterns, and community package references. The existing `cg-skill-stata-core` SKILL.md already cross-references it. This plan ensures: (1) the new skill's content is technically correct and complete, (2) all project-level references are updated to mention both Stata skills where appropriate (mirroring the R skill split pattern), and (3) the ROADMAP is updated to mark the item as done.

## Context

**What exists today:**
- `cg-skill-stata-core` — 7 files (SKILL.md + 4 workflows + 2 references). Covers language fundamentals: macros, scoping, data management, reproducibility. Already includes a forward reference to `cg-skill-stata-research` in its SKILL.md ("when available").
- `cg-skill-stata-research` — 7 files (SKILL.md + 4 workflows + 2 references). New skill covering research methodology: phased research workflow, survey design & poverty measurement, causal inference, output/tables, research anti-patterns, community packages.

**What needs updating:**
Several project-level files currently reference only `cg-skill-stata-core` for Stata work. After the R skill split (plan `2026-03-17`), the pattern is to reference both skills where appropriate and explain when to load which. The same pattern must be applied for the two Stata skills.

**Key reference — the R skill split pattern (from `copilot-instructions.md`):**
> Two R skills: `cg-skill-r-technical` covers package/infrastructure work... `cg-skill-r-analytical` covers statistical/econometric work... Load the appropriate skill based on work type; load both for mixed work.

The Stata equivalent:
> Two Stata skills: `cg-skill-stata-core` covers language fundamentals (macros, scoping, data management, repkit). `cg-skill-stata-research` covers analytical methodology (survey design, poverty measurement, causal inference, publication output). Always load `cg-skill-stata-core` for any Stata work. Additionally load `cg-skill-stata-research` when writing or reviewing analytical do-files.

## Implementation Steps

### 1. Content review — cg-skill-stata-research SKILL.md

- **Files**: `.github/skills/cg-skill-stata-research/SKILL.md`
- **Details**: Verify the SKILL.md structure, routing table, "When to Load" section, and YAML frontmatter are correct and consistent with the core skill's structure.
- **Checks**:
  - YAML `name` matches directory name
  - Description is accurate and mentions pairing with `cg-skill-stata-core`
  - Routing table links are correct relative paths
  - "When to Load" section is comprehensive
  - Critical Analytical Gotchas section aligns with the full anti-patterns reference
- **Acceptance criteria**: SKILL.md is self-consistent and properly cross-references the core skill.

### 2. Content review — research-phases.md

- **Files**: `.github/skills/cg-skill-stata-research/workflows/research-phases.md`
- **Details**: Verify the six-phase workflow. Check that code examples follow `cg-skill-stata-core` conventions (compound quotes on tempfiles, `//` not `*` for inline comments, `quietly` in loops, units comments on `replace`, `_merge` checks).
- **Checks**:
  - All code examples use `//` for inline comments (not mid-line `*`)
  - `tempfile` paths use compound quotes
  - Each phase has a clear PAUSE point
  - Phase 5 correctly defers to `output-tables.md`
- **Acceptance criteria**: All code examples pass the 11 anti-patterns from `cg-skill-stata-core`.

### 3. Content review — survey-poverty.md

- **Files**: `.github/skills/cg-skill-stata-research/workflows/survey-poverty.md`
- **Details**: Verify survey design patterns, FGT implementation, welfare aggregation steps, inequality measures, and replicate weights. This is the highest-risk file — incorrect poverty measurement patterns could propagate to official statistics.
- **Checks**:
  - `svyset` patterns are correct (PSU, strata, weights)
  - `svy:` is used consistently (never bare `summarize` on survey data)
  - `subpop()` is recommended over `if` for subgroup analysis
  - PPP conversion order is correct (spatial → temporal → PPP, with PPP last)
  - FGT formula implementation is mathematically correct
  - Welfare aggregation step sequence documents units before/after each transform
  - Multiple poverty lines section uses correct GPID standard ($2.15, $3.65, $6.85)
  - Shared prosperity calculation is correct
  - Gini/Theil/GE patterns use weights
- **Acceptance criteria**: A Stata user following these patterns verbatim would produce correct poverty statistics.

### 4. Content review — causal-inference.md

- **Files**: `.github/skills/cg-skill-stata-research/workflows/causal-inference.md`
- **Details**: Verify DiD (classic + staggered), RD, matching, IV, and panel FE patterns. Focus on whether modern DiD estimators are correctly recommended for staggered timing.
- **Checks**:
  - Classic 2x2 DiD is correctly shown
  - Staggered DiD explicitly warns against TWFE and shows `csdid`, `did_multiplegt`, `did_imputation`
  - RD patterns use `rdrobust` with diagnostics (McCrary, covariate balance)
  - Matching includes overlap check and balance tests
  - IV includes first-stage diagnostics and weak-instrument warnings
  - Method selection guide at the bottom is accurate
- **Acceptance criteria**: Patterns match current methodological best practices (post-2020 DiD revolution).

### 5. Content review — output-tables.md

- **Files**: `.github/skills/cg-skill-stata-research/workflows/output-tables.md`
- **Details**: Verify `esttab`, `coefplot`, `putexcel` patterns and the replication package checklist.
- **Checks**:
  - `esttab` examples produce valid LaTeX, RTF, and CSV
  - Multi-panel table pattern is syntactically correct
  - `coefplot` syntax matches current package version
  - Replication package checklist is comprehensive
- **Acceptance criteria**: A user following these patterns produces publication-ready outputs.

### 6. Content review — stata-research-anti-patterns.md

- **Files**: `.github/skills/cg-skill-stata-research/references/stata-research-anti-patterns.md`
- **Details**: Verify the 11 research-level anti-patterns. These complement (not duplicate) the 11 core anti-patterns in `cg-skill-stata-core`.
- **Checks**:
  - No overlap with core anti-patterns (core covers syntax; research covers methodology)
  - Each anti-pattern has: problem statement, wrong example, right example, rule/explanation
  - Quick diagnostic checklist at the bottom covers all critical checks
  - Cross-references to core skill are correct
- **Acceptance criteria**: The research anti-patterns file is complete and non-overlapping with the core anti-patterns.

### 7. Content review — community-packages.md

- **Files**: `.github/skills/cg-skill-stata-research/references/community-packages.md`
- **Details**: Verify package syntax references are accurate and the package list is complete for GPID needs.
- **Checks**:
  - All syntax examples are correct for current package versions
  - `repado` reference is included for version pinning
  - No packages are missing that are used in the workflow files (reghdfe, estout, csdid, rdrobust, psmatch2, coefplot, ineqdeco, ivreg2, xtabond2)
- **Acceptance criteria**: Quick reference is accurate and sufficient.

### 8. Content review — cg-skill-stata-core updates

- **Files**: `.github/skills/cg-skill-stata-core/SKILL.md`
- **Details**: Verify the core SKILL.md's forward reference to `cg-skill-stata-research` is now correct (no longer "when available" — the skill exists). Check if any other core skill files were recently modified.
- **Checks**:
  - The "(when available)" parenthetical should be removed
  - The cross-reference text is accurate
  - No other issues with the core skill files
- **Acceptance criteria**: Core skill cleanly references the research skill without conditional language.

### 9. Update copilot-instructions.md — Stata section

- **Files**: `.github/copilot-instructions.md`
- **Details**: Add a "Two Stata skills" block under "Stata style" (mirroring the "Two R skills" block). Update the Code Organization section to list `cg-skill-stata-research`.
- **Changes**:
  - After the existing Stata line, add a sub-bullet explaining the two-skill structure
  - In Code Organization, add `cg-skill-stata-research` to the skills list
- **Acceptance criteria**: The Stata skill documentation mirrors the R skill split pattern.

### 10. Update cg-work.prompt.md — Stata skill loading

- **Files**: `.github/prompts/cg-work.prompt.md` (line ~20)
- **Details**: Expand the Stata skill loading instruction to load both skills for analytical work.
- **Change**: From `Stata: load the cg-skill-stata-core skill.` to a pattern that mentions loading `cg-skill-stata-research` for analytical do-files, mirroring the R dual-skill loading pattern already in the file.
- **Acceptance criteria**: `cg-work` knows to load the research skill for analytical Stata work.

### 11. Update cg-review.prompt.md — Stata skill check

- **Files**: `.github/prompts/cg-review.prompt.md` (line ~55)
- **Details**: Expand the "Stata skill check" block to also mention `cg-skill-stata-research` for analytical `.do` files.
- **Acceptance criteria**: Review agents load both skills when reviewing analytical Stata code.

### 12. Update cg-fixbug.prompt.md — Stata skill reference

- **Files**: `.github/prompts/cg-fixbug.prompt.md` (line ~74)
- **Details**: Add `cg-skill-stata-research` alongside `cg-skill-stata-core` for analytical bug fixes.
- **Acceptance criteria**: Bug-fix workflow loads both skills when appropriate.

### 13. Update docs/reference.md — Skills table

- **Files**: `docs/reference.md`
- **Details**: Add `cg-skill-stata-research` to the Skills table.
- **Change**: New row: `cg-skill-stata-research` | Research methodology, phased workflow, survey design, poverty measurement, causal inference, publication output, research anti-patterns |
- **Acceptance criteria**: Skills table lists both Stata skills.

### 14. Update ROADMAP.md — Mark items complete

- **Files**: `ROADMAP.md`
- **Details**: Mark the Stata research skill item in Phase 4 as done. Also consider moving it to Phase 1 (where the core skill is listed) since both skills are now foundational.
- **Changes**:
  - Phase 4 line: `- [ ] Stata research skill (cg-skill-stata-research)...` → `- [x] Stata research skill (cg-skill-stata-research)...`
  - Optionally add a `[x]` entry under Phase 1 as well to show both Stata skills are complete
- **Acceptance criteria**: ROADMAP accurately reflects current state.

### 15. Update cg-code-quality agent — dual Stata skill awareness

- **Files**: `.github/agents/cg-code-quality.agent.md`
- **Details**: The agent currently references only `cg-skill-stata-core` for `.do`/`.ado` files (line ~46). For analytical code, it should also reference `cg-skill-stata-research` anti-patterns.
- **Acceptance criteria**: Code quality agent is aware of both sets of anti-patterns.

## Testing Strategy

This is a documentation/skill review — no automated tests. Verification is via:

1. **Manual content review**: Each workflow and reference file is read and checked against Stata documentation and GPID practices.
2. **Cross-reference validation**: All internal links between files are verified to be correct relative paths.
3. **Anti-pattern overlap check**: Confirm the 11 research anti-patterns do not duplicate the 11 core anti-patterns.
4. **Grep verification**: After all reference updates, grep for `cg-skill-stata` across the project to confirm no stale references remain.

## Documentation Checklist

- [ ] SKILL.md YAML frontmatter complete and accurate
- [ ] All workflow files have clear headers and purpose statements
- [ ] All code examples follow core skill conventions
- [ ] Cross-references between skills are bidirectional
- [ ] docs/reference.md updated
- [ ] copilot-instructions.md updated
- [ ] All prompts updated

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Code examples in research skill violate core skill conventions | Steps 2-5 explicitly check every code example against the 11 core anti-patterns |
| Research anti-patterns duplicate core anti-patterns | Step 6 specifically checks for overlap |
| Stale "when available" references in core skill | Step 8 specifically removes conditional language |
| Missed reference in a prompt/agent file | Step 15 + final grep verification covers this |

## Out of Scope

- **New analytical code**: This plan reviews existing skill content, not writing new analysis do-files.
- **Stata research skill testing with real data**: Skills are documentation-only — they are validated by human review, not automated tests.
- **Phase 2/3 roadmap items**: Statistical validity agents and methodology agents are separate roadmap items not addressed here.
- **Instructions file update**: `.github/instructions/stata.instructions.md` is already comprehensive and doesn't need research-specific additions (the skill handles that layer).
