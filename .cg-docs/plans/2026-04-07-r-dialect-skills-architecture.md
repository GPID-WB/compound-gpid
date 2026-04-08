---
date: 2026-04-07
title: "R Dialect Skills Architecture"
status: completed
completed-date: 2026-04-07
brainstorm: ".cg-docs/brainstorms/2026-04-07-r-syntax-dialect-skills.md"
language: "R"
estimated-effort: "large"
tags: [skills, r, architecture, tidyverse, data.table, collapse, refactoring]
---

# Plan: R Dialect Skills Architecture

## Objective

Refactor the R skill ecosystem so that users can select a per-project R syntax
dialect (`data.table-collapse` or `tidyverse`) via `compound-gpid.local.md`,
and the model receives only dialect-consistent instructions — no conflicting
signals. This involves splitting dialect-specific content out of the existing
skills and `r.instructions.md` into three new standalone dialect skills
(`cg-skill-r-collapse`, `cg-skill-r-datatable`, `cg-skill-r-tidyverse`),
extracting ggplot2/visualization into its own skill, and making
`r.instructions.md` a thin routing layer.

## Context

**Today's state:**
- `r.instructions.md` (always loaded on `.R` files): 50 lines of collapse +
  data.table rules plus ggplot2 rules. Explicitly says "tidyverse only as
  fallback."
- `copilot-instructions.md` (always loaded): line 36 says
  "Preference hierarchy: collapse > data.table > tidyverse." Line 37 describes
  three R skills with collapse/data.table baked into their descriptions.
- `cg-skill-r-analytical/SKILL.md`: Decision rule table and quick reference
  both enforce collapse > data.table > tidyverse.
- `cg-skill-r-technical/SKILL.md`: Same hierarchy in header.
- `cg-skill-r-analytical/references/collapse-reference.md`: Pure collapse
  content (300+ lines) — will move to `cg-skill-r-collapse`.
- `cg-skill-r-technical/workflows/data-table-patterns.md`: Mixed data.table +
  collapse content (200 lines) — data.table portions move to
  `cg-skill-r-datatable`, collapse portions to `cg-skill-r-collapse`.
- `cg-skill-r-shared/references/collapse-anti-patterns.md`: Pure collapse
  anti-patterns — will move to `cg-skill-r-collapse`.
- `cg-skill-r-analytical/workflows/visualization.md`: ggplot2 + wbplot
  (syntax-neutral) mixed with collapse data prep examples.

**Brainstorm decision:** Approach 1 — Dialect Skills with Instruction-Level
Routing. Default `data.table-collapse` when `r-syntax` absent. No `"all"`
option in v1.

## Implementation Steps

### Phase 1: Create the Three Dialect Skills

#### 1.1 Create `cg-skill-r-collapse`

- **Files to create**:
  - `.github/skills/cg-skill-r-collapse/SKILL.md`
  - `.github/skills/cg-skill-r-collapse/references/collapse-reference.md`
    (moved from `cg-skill-r-analytical/references/collapse-reference.md`)
  - `.github/skills/cg-skill-r-collapse/references/collapse-anti-patterns.md`
    (moved from `cg-skill-r-shared/references/collapse-anti-patterns.md`)
- **Content source**: User will provide detailed reference material in
  `.cg-docs/brainstorms/2026-04-07-r-dialect-skills--input-collapse.md`.
  Merge with existing `collapse-reference.md` and `collapse-anti-patterns.md`.
- **SKILL.md structure**:
  - Frontmatter: `name: cg-skill-r-collapse`,
    `user-invocable: false`, description focused on when to load
    (grouped/weighted statistics, aggregation, transformations, panel data).
  - Body: Quick reference table, canonical function signatures, decision
    rules for when to use collapse vs alternatives, links to reference files.
- **Tests**: Manual — load the skill in a chat session, ask it to compute a
  weighted mean grouped by region. Verify it uses `fmean(x, g, w)`.
- **Acceptance criteria**: Skill loads when model encounters statistical
  computing tasks; contains all current collapse knowledge; no data.table
  or tidyverse preferences mentioned.

#### 1.2 Create `cg-skill-r-datatable`

- **Files to create**:
  - `.github/skills/cg-skill-r-datatable/SKILL.md`
  - `.github/skills/cg-skill-r-datatable/references/datatable-reference.md`
    (extracted from `cg-skill-r-technical/workflows/data-table-patterns.md`,
    data.table portions only)
  - `.github/skills/cg-skill-r-datatable/references/datatable-anti-patterns.md`
    (extracted from `cg-skill-r-technical/references/r-technical-anti-patterns.md`,
    data.table portions only)
- **Content source**: User will provide detailed reference material in
  `.cg-docs/brainstorms/2026-04-07-r-dialect-skills--input-datatable.md`.
  Merge with existing data.table content.
- **SKILL.md structure**:
  - Frontmatter: `name: cg-skill-r-datatable`,
    `user-invocable: false`, description focused on when to load (data
    manipulation, filtering, joins, reshaping, `:=` assignment, I/O).
  - Body: Quick reference table, `DT[i, j, by]` paradigm, `.SD`/`.SDcols`,
    joins, reshaping, performance patterns, links to reference files.
- **Tests**: Manual — ask model to filter rows, create columns, and do a
  join. Verify it uses `dt[cond]`, `:=`, `X[Y, on=]`.
- **Acceptance criteria**: Skill loads for data manipulation tasks; contains
  all current data.table knowledge; no tidyverse or collapse preferences.

#### 1.3 Create `cg-skill-r-tidyverse`

- **Files to create**:
  - `.github/skills/cg-skill-r-tidyverse/SKILL.md`
  - `.github/skills/cg-skill-r-tidyverse/references/tidyverse-reference.md`
  - `.github/skills/cg-skill-r-tidyverse/references/tidyverse-style.md`
  - `.github/skills/cg-skill-r-tidyverse/references/tidyverse-anti-patterns.md`
  - `.github/skills/cg-skill-r-tidyverse/references/tidyverse-migration.md`
    (migrating from data.table/collapse to tidyverse or vice versa)
- **Content source**: New content. Draw from:
  - posit-dev/skills PR #43 patterns (modern tidyverse: `.by`, `join_by()`,
    native pipe, `pick()`/`across()`, `case_when()`)
  - Current dplyr 1.2+ / tidyr 1.3+ / stringr 1.5+ best practices
  - Specific GPID patterns translated to tidyverse (welfare measurement,
    weighted stats via `weighted.mean()` or `collapse` — note: even in
    tidyverse mode, `collapse` functions can still be used for statistical
    computing since they're syntax-agnostic)
- **SKILL.md structure**:
  - Frontmatter: `name: cg-skill-r-tidyverse`,
    `user-invocable: false`, description focused on when to load (dplyr for
    manipulation, tidyr for reshaping, readr for I/O, stringr for strings,
    purrr for iteration).
  - Body: Quick reference table, modern patterns (`.by` over
    `group_by()/ungroup()`), native pipe, `join_by()`, style conventions,
    links to reference files.
- **Key design choice**: For weighted statistics in tidyverse mode, the skill
  should still recommend `collapse` functions (`fmean`, `fsum`) since
  they work on tibbles and there's no good tidyverse native alternative for
  weighted grouped stats. The key is the *manipulation* layer uses tidyverse,
  not that collapse is banned.
- **Tests**: Manual — ask model to filter, join, reshape using tidyverse.
  Verify it uses `dplyr::filter()`, `left_join()`, `pivot_longer()`.
- **Acceptance criteria**: Skill loads for tidyverse-flavored projects;
  produces idiomatic modern tidyverse code; no "data.table is preferred"
  messaging.

### Phase 2: Extract Visualization Skill

#### 2.1 Create `cg-skill-r-visualization`

- **Files to create**:
  - `.github/skills/cg-skill-r-visualization/SKILL.md`
  - `.github/skills/cg-skill-r-visualization/references/ggplot2-reference.md`
  - `.github/skills/cg-skill-r-visualization/references/wbplot-reference.md`
- **Content source**: Extract from:
  - `r.instructions.md` — ggplot2 section
  - `cg-skill-r-analytical/workflows/visualization.md` — full visualization
    workflow (but replace collapse-specific data prep examples with
    dialect-neutral language like "aggregate your data before plotting")
- **SKILL.md structure**:
  - Frontmatter: `name: cg-skill-r-visualization`,
    `user-invocable: false`, description: ggplot2 + wbplot patterns for
    World Bank visualizations.
  - Body: `theme_wb()`, `WBCOLORS`, scale functions, chart type patterns,
    `ggsave()` conventions.
- **Tests**: Manual — ask for a poverty trend line chart. Verify it uses
  `ggplot2` + `wbplot` patterns.
- **Acceptance criteria**: Skill is dialect-neutral — no collapse or
  data.table references in the manipulation layer. Data prep examples show
  comments like "# aggregate data (use your project's preferred syntax)"
  or show both options briefly.

### Phase 3: Refactor Existing Skills

#### 3.1 Refactor `cg-skill-r-analytical`

- **Files to modify**:
  - `cg-skill-r-analytical/SKILL.md` — remove hierarchy, remove
    decision rule table, remove collapse/data.table quick reference rows.
    Keep: econometrics (fixest), output tables (modelsummary), Quarto,
    welfare measurement, survey analysis, Stata migration content. Update
    description.
  - `cg-skill-r-analytical/references/collapse-reference.md` — **delete**
    (moved to `cg-skill-r-collapse`)
  - `cg-skill-r-analytical/references/r-analytical-anti-patterns.md` —
    remove "Tool Hierarchy Anti-Patterns" section (dialect-specific). Keep
    any analytical anti-patterns that aren't about tool choice (e.g., wrong
    FGT formula, PPP mistakes).
  - `cg-skill-r-analytical/workflows/visualization.md` — **delete**
    (moved to `cg-skill-r-visualization`)
  - `cg-skill-r-analytical/workflows/welfare-patterns.md` — keep but
    review: it uses `data.table` `:=` for examples. Add a note that these
    examples follow the default `data.table-collapse` dialect; in tidyverse
    mode the manipulation syntax changes but the statistical functions
    (`fmean`, `fsum`, etc.) remain the same.
  - `cg-skill-r-analytical/workflows/survey-analysis.md` — similar review
  - `cg-skill-r-analytical/workflows/econometrics.md` — syntax-neutral, keep
  - `cg-skill-r-analytical/workflows/stata-migration.md` — syntax-neutral,
    keep
- **Updated description**: "R patterns for analytical work: fixest for
  econometrics, modelsummary for tables, welfare/poverty measurement patterns,
  survey analysis, and Stata migration. Dialect-neutral — load alongside
  the appropriate syntax skill (collapse, data.table, or tidyverse)."
- **Acceptance criteria**: No "collapse > data.table > tidyverse" language
  remains. Skill focuses on *domain* knowledge, not *syntax* preferences.

#### 3.2 Refactor `cg-skill-r-technical`

- **Files to modify**:
  - `cg-skill-r-technical/SKILL.md` — remove hierarchy, remove
    collapse/data.table quick reference rows. Keep: roxygen2, package
    development, plumber, Shiny, targets, httr2, renv/pak, error handling
    (rlang + cli). Update description.
  - `cg-skill-r-technical/workflows/data-table-patterns.md` — **delete**
    (content moved to `cg-skill-r-datatable` and `cg-skill-r-collapse`)
  - `cg-skill-r-technical/references/r-technical-anti-patterns.md` —
    remove dialect-specific anti-patterns (tool hierarchy section, data.table
    section). Keep: roxygen2 anti-patterns, error handling anti-patterns,
    package development anti-patterns, anything not about data manipulation
    syntax choice.
  - Other workflow/reference files — keep as-is (plumber, shiny, targets,
    http-clients, renv, testing-apis are already syntax-neutral)
- **Updated description**: "R patterns for technical work: roxygen2, package
  development, plumber APIs, Shiny apps, targets pipelines, httr2 HTTP
  clients, renv/pak environment management, and error handling with rlang/cli.
  Dialect-neutral — load alongside the appropriate syntax skill."
- **Acceptance criteria**: No dialect preference language remains. Skill
  focuses on *infrastructure* knowledge.

#### 3.3 Refactor `cg-skill-r-shared`

- **Files to modify**:
  - `cg-skill-r-shared/SKILL.md` — update description and references
  - `cg-skill-r-shared/references/collapse-anti-patterns.md` — **delete**
    (moved to `cg-skill-r-collapse/references/collapse-anti-patterns.md`)
- **Note**: If `cg-skill-r-shared` becomes empty after this, consider
  whether to keep it (for future shared content) or delete it.
- **Acceptance criteria**: No orphaned references. Cross-skill links updated.

### Phase 4: Update Routing Layer

#### 4.1 Rewrite `r.instructions.md`

- **File**: `.github/instructions/r.instructions.md`
- **Current state**: ~50 lines of collapse + data.table rules + ggplot2 rules
- **New content** (thin router, ~20-25 lines):
  ```markdown
  ---
  applyTo: "**/*.R,**/*.r,**/*.Rmd"
  ---

  # R Coding Standards

  ## Syntax Dialect

  Read `compound-gpid.local.md` in the project root for the `r-syntax` field.

  - If `r-syntax: "tidyverse"` → load `cg-skill-r-tidyverse` for data
    manipulation, I/O, and reshaping patterns.
  - If `r-syntax: "data.table-collapse"` (or field is absent) → load
    `cg-skill-r-datatable` for data manipulation and `cg-skill-r-collapse`
    for statistical computing.

  Follow the loaded dialect consistently throughout the project. Do not mix
  dialects within a project.

  ## Universal R Standards (all dialects)

  - Use `ggplot2` for visualization. Load `cg-skill-r-visualization` for
    World Bank chart patterns.
  - Document functions with `roxygen2` (`@param`, `@return`, `@export`,
    `@examples`).
  - Use `testthat` edition 3 for testing.
  - Handle errors with `rlang::try_fetch()` and `cli::cli_abort()`.
  - Use `haven::read_dta()` for Stata files, `as_factor()` for labels.
  ```
- **Acceptance criteria**: No dialect-specific rules in the file. Routing
  directive is clear. Token cost is low (~200 tokens vs current ~500+).

#### 4.2 Update `copilot-instructions.md`

- **File**: `.github/copilot-instructions.md`
- **Changes**:
  - Line 36: Replace "R style: `collapse` for statistics/aggregation,
    `data.table` for data manipulation, `ggplot2` for visualization.
    Preference hierarchy: collapse > data.table > tidyverse." with:
    "R style: Check `compound-gpid.local.md` for the `r-syntax` field.
    Default is `data.table-collapse`. Load the matching dialect skill(s)
    before writing R code."
  - Line 37: Replace the "Three R skills" paragraph with an updated
    description of the new skill ecosystem (6 R skills: collapse,
    data.table, tidyverse, analytical, technical, testing + visualization).
- **Acceptance criteria**: No hardcoded hierarchy. Model reads `r-syntax`
  from config.

### Phase 5: Update Setup and Config

#### 5.1 Update `/cg-setup` skill

- **File**: `.github/skills/cg-skill-setup/SKILL.md`
- **Changes**: Add a new question after Question 1 (Language Preference),
  shown only when language includes R:

  > **Question 1b: R Syntax Dialect** *(shown only if language includes R)*
  >
  > What R syntax dialect do you prefer for this project?
  > 1. **data.table + collapse** — data.table for manipulation, collapse for
  >    statistics. Fast, explicit, used by the GPID team internally.
  >    *(default)*
  > 2. **tidyverse** — dplyr for manipulation, tidyr for reshaping, readr
  >    for I/O. Readable, widely known, good for collaboration with external
  >    coauthors.

- **Config output**: Add `r-syntax: "data.table-collapse"` or
  `r-syntax: "tidyverse"` to the frontmatter of `compound-gpid.local.md`.
- **Acceptance criteria**: New projects get asked about R syntax. Answer
  flows into `compound-gpid.local.md`.

#### 5.2 Bump schema version

- **File**: `SCHEMA_VERSION`
- **Change**: Update from `2026-03-25-project-charter` to new version
  (e.g., `2026-04-07-r-syntax-dialect`).
- **Note**: This is a backward-compatible addition — missing `r-syntax` just
  defaults to `data.table-collapse`.

### Phase 6: Update Cross-References

#### 6.1 Fix all cross-skill links

- Search all `.md` files under `.github/skills/` for references to moved
  files (e.g., `../../cg-skill-r-analytical/references/collapse-reference.md`)
  and update them to point to new locations.
- Update the footer cross-references in each SKILL.md that says "For
  collapse, see cg-skill-r-analytical" → now "For collapse, see
  cg-skill-r-collapse."
- **Acceptance criteria**: No broken internal links.

#### 6.2 Update skill descriptions in `copilot-instructions.md`

- If `copilot-instructions.md` has a skills inventory section that lists all
  available skills, update it to include the three new dialect skills and the
  visualization skill.

## Testing Strategy

- **Pester tests**: Run existing tests (`.tests/` files) to ensure no
  regressions in PowerShell scripts. The skill changes are markdown-only
  so existing tests should pass unchanged.
- **Manual validation — data.table-collapse dialect**:
  1. Set `r-syntax: "data.table-collapse"` in `compound-gpid.local.md`
  2. Open a `.R` file, ask "compute the weighted mean of welfare by region"
  3. Verify: model uses `fmean(dt$welfare, g = dt$region, w = dt$weight)`
  4. Ask "filter rows where income > 50000 and add a log column"
  5. Verify: model uses `dt[income > 50000]` and `:=`
- **Manual validation — tidyverse dialect**:
  1. Set `r-syntax: "tidyverse"` in `compound-gpid.local.md`
  2. Open a `.R` file, ask "compute the weighted mean of welfare by region"
  3. Verify: model uses `dplyr` patterns (or `fmean()` — acceptable since
     collapse is used for weighted stats even in tidyverse mode)
  4. Ask "filter rows where income > 50000 and add a log column"
  5. Verify: model uses `filter(income > 50000)` and `mutate(log_inc = log(income))`
  6. Verify: model does NOT use `:=` or `dt[` syntax
- **Manual validation — no r-syntax field**:
  1. Remove `r-syntax` from `compound-gpid.local.md`
  2. Verify: model defaults to data.table-collapse behavior
- **Cross-reference audit**: grep for broken links (`../../cg-skill-r-`) in
  all skill markdown files.

## Documentation Checklist

- [ ] Each new SKILL.md has complete frontmatter (name, description, user-invocable)
- [ ] Each SKILL.md body has a quick reference table and links to reference files
- [ ] Updated `r.instructions.md` explains the routing logic
- [ ] `copilot-instructions.md` updated skill descriptions
- [ ] `/cg-setup` skill documents the new `r-syntax` question
- [ ] Brainstorm file links to this plan

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|-----------|
| Model ignores `r-syntax` field in config | Writes wrong dialect | Routing directive is in `r.instructions.md` (always loaded), not just skills. Also reinforced in `copilot-instructions.md`. Two always-on files provide redundancy. |
| Tidyverse skill has no good weighted stats pattern | Falls back to base R `weighted.mean()` | Design choice: tidyverse skill explicitly recommends `collapse` functions for weighted stats. Collapse works on tibbles — it's syntax-agnostic. |
| Existing projects break after update | Skills load wrong content | Backward compatible: missing `r-syntax` defaults to `data.table-collapse`. No existing file is required to have the field. |
| Token overhead from more skills | Slower responses | Skills use `user-invocable: false` and load on demand. Only the relevant dialect loads, not all three. Net token cost should be similar or lower than today (today's `r.instructions.md` loads everything always). |
| Cross-references break after file moves | Model can't find reference material | Phase 6 explicitly audits and fixes all internal links. |
| User provides long reference material | Skills become bloated | Follow posit-dev/skills pattern: SKILL.md is compact (~200 lines), reference files are loaded lazily on demand. |

## Out of Scope

- **`"all"` option** for `r-syntax` (mixing dialects) — deferred to v2 if
  needed.
- **tidymodels skill** — separate roadmap feature, not part of this refactoring.
- **Python or Stata dialect choices** — this plan only covers R.
- **Automated evals** — manual validation only for v1. Automated testing of
  skill behavior is in the Evals milestone.
- **Changing the GPID team's default preference** — `data.table-collapse`
  remains the default. This plan adds an alternative, not a replacement.
