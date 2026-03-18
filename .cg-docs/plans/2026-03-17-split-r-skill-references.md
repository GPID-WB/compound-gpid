---
date: 2026-03-17
title: "Update all references from cg-skill-r-best-practices to cg-skill-r-technical + cg-skill-r-analytical"
status: active
brainstorm: ~
language: "both"
estimated-effort: "small"
tags: [documentation, skills, refactor]
---

# Plan: Update References for R Skill Split

## Objective

The `cg-skill-r-best-practices` skill has been split into two focused skills:

- **`cg-skill-r-technical`** — data.table, ggplot2, testthat, roxygen2, package development, plumber APIs, Shiny apps, targets pipelines, httr2, renv/pak.
- **`cg-skill-r-analytical`** — haven for Stata migration, srvyr/survey for complex surveys, fixest for econometrics, modelsummary for tables, ggplot2+wbplot for World Bank visualizations, welfare/poverty measurement patterns.

All references to the old skill (`cg-skill-r-best-practices`) must be updated across the project.

## Context

The old skill directory no longer exists. The two new skill directories are already created at:
- `.github/skills/cg-skill-r-analytical/`
- `.github/skills/cg-skill-r-technical/`

Historical `.cg-docs/` files (brainstorms, old plans) will **not** be modified — they are historical records.

## Implementation Steps

### 1. Update `cg-work.prompt.md`

- **File**: `.github/prompts/cg-work.prompt.md` (line 18)
- **Details**: Replace the single R skill reference with both new skills.
- **Change**:
  - Old: `R: load the \`cg-skill-r-best-practices\` skill.`
  - New: `R: load the \`cg-skill-r-technical\` skill and the \`cg-skill-r-analytical\` skill.`
- **Acceptance criteria**: The prompt references both new skills.

### 2. Update `copilot-instructions.md`

- **File**: `.github/copilot-instructions.md` (line 27)
- **Details**: Replace the old skill name in the "Code Organization" section.
- **Change**:
  - Old: `see \`cg-skill-r-best-practices\`, \`cg-skill-python-best-practices\`, or \`cg-skill-stata-core\` skills`
  - New: `see \`cg-skill-r-technical\`, \`cg-skill-r-analytical\`, \`cg-skill-python-best-practices\`, or \`cg-skill-stata-core\` skills`
- **Acceptance criteria**: Both new R skills are listed alongside Python and Stata.

### 3. Update `docs/reference.md`

- **File**: `docs/reference.md` (line 55)
- **Details**: Replace the single R row in the Skills table with two rows describing each new skill.
- **Change**: Replace the `cg-skill-r-best-practices` row with:
  - `cg-skill-r-technical` — `data.table`, `ggplot2`, `testthat`, roxygen2, `renv`, package dev, `plumber`, `shiny`, `targets`
  - `cg-skill-r-analytical` — `haven`, `srvyr`/`survey`, `fixest`, `modelsummary`, `ggplot2`+`wbplot`, welfare measurement
- **Acceptance criteria**: Both skills appear in the Skills table with accurate descriptions.

### 4. Update `ROADMAP.md`

- **File**: `ROADMAP.md` (line 9)
- **Details**: Replace the single checklist item with two items for each new skill.
- **Change**:
  - Old: `- [x] R best practices skill (\`cg-skill-r-best-practices\`)`
  - New: Two items — `cg-skill-r-technical` and `cg-skill-r-analytical`
- **Acceptance criteria**: Roadmap reflects both new skills as completed.

### 5. Verify — grep for stale references

- **Details**: Run a final grep for `cg-skill-r-best-practices` to confirm only historical `.cg-docs/` files remain.
- **Acceptance criteria**: Zero matches outside `.cg-docs/brainstorms/` and `.cg-docs/plans/`.

## Testing Strategy

No code tests needed — these are documentation-only changes. Verification is the final grep in Step 5.

## Documentation Checklist

- [x] Skills table in `docs/reference.md` updated
- [x] copilot-instructions.md updated
- [x] Workflow prompt updated
- [x] ROADMAP updated

## Risks & Mitigations

- **Risk**: Other projects already linked may still cache the old `copilot-instructions.md`.
  - **Mitigation**: Running `cg-update` in those projects will pull the updated file.

## Out of Scope

- Modifying historical `.cg-docs/brainstorms/` or `.cg-docs/plans/` documents (they are records-of-fact).
- Restructuring the nested directory layout of the new skills (assumed intentional).
