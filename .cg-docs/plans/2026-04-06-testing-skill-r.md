---
date: 2026-04-06
title: "Testing skill for R (cg-skill-r-testing)"
status: completed
completed-date: 2026-04-06
brainstorm: ".cg-docs/brainstorms/2026-04-06-testing-skill-r.md"
language: "R"
estimated-effort: "medium"
tags: [testing, r, skill, testthat, quality-loop]
---

# Plan: Testing Skill for R (cg-skill-r-testing)

## Objective

Create a standalone `cg-skill-r-testing` skill that gives the AI comprehensive, demand-loaded testthat 3+ reference material — modeled on Posit's `testing-r-packages` skill structure — with examples that prefer collapse and data.table over tidyverse. The skill replaces the existing `cg-skill-r-technical/references/testing-testthat.md` as the single authoritative source of R testing knowledge in the plugin.

## Context

- **Brainstorm decision**: Approach 1 — Full Posit Mirror adapted for collapse/data.table ([brainstorm](.cg-docs/brainstorms/2026-04-06-testing-skill-r.md))
- **Existing content**: `cg-skill-r-technical/references/testing-testthat.md` (~240 lines) covers basics, collapse/data.table testing, plumber/httr2 mocking — to be absorbed and replaced
- **Posit model**: `testing-r-packages` skill = SKILL.md + 5 reference files (bdd.md, mocking.md, fixtures.md, snapshots.md, advanced.md)
- **Consumers**: `cg-testing` agent, `/cg-work` prompt, `/cg-review` prompt — all auto-load when `.R`/`.Rmd` files are in scope
- **Constraint**: collapse/data.table first in all examples; cross-reference `cg-skill-r-technical` and `cg-skill-r-analytical` for package-specific depth

## Implementation Steps

### 1. Create `cg-skill-r-testing/SKILL.md`

- **Files**: `.github/skills/cg-skill-r-testing/SKILL.md`
- **Details**:
  - Frontmatter with `name`, `description` fields matching the conventions of existing skills
  - Description must trigger on: writing R tests, reviewing R test files, debugging failing R tests, improving R test coverage, any `.R` file containing `test_that`, `describe`, `expect_*`, `testthat`
  - Description must NOT trigger on: general R coding, Python/Stata testing, non-test work
  - Candidate description: `"Best practices for testing R code with testthat 3+. Covers test structure, expectations, design principles, fixtures, mocking, snapshots, and BDD patterns. Use when writing, reviewing, debugging, or improving tests in .R files. Prefer collapse for statistical assertions and data.table for test data construction; see cg-skill-r-technical and cg-skill-r-analytical for package-specific depth."`
  - Body sections (mirroring Posit structure, ~300 lines):
    1. Initial Setup — `usethis::use_testthat(3)`
    2. File Organization — mirror package structure, helper/setup/fixtures files
    3. Test Structure — `test_that()` + BDD `describe()`/`it()` (brief, with ref to `references/bdd.md`)
    4. Running Tests — micro/mezzo/macro
    5. Core Expectations — equality, errors/warnings/messages, pattern matching, structure/type, sets/collections, logical
    6. Design Principles — self-sufficient, self-contained (withr cleanup), plan for failure, repetition ok, `load_all()` workflow
    7. Common Patterns — testing collapse output (weighted means, collap, fwithin, GRP, TRA), testing data.table (joins, `:=`, fread/fwrite), testing with temp resources (withr), edge cases (empty DT, NA, invalid input)
    8. Snapshot Testing — brief, with ref to `references/snapshots.md`
    9. Mocking — brief `local_mocked_bindings()` pattern, with ref to `references/mocking.md`
    10. Test Fixtures — brief three approaches, with ref to `references/fixtures.md`
    11. testthat 3 Modernizations — deprecated→modern patterns
    12. Quick Reference — one-liner cheat sheet
    13. Cross-references — links to `cg-skill-r-technical` (plumber/httr2 API testing, renv), `cg-skill-r-analytical` (welfare measurement testing patterns)
- **Tests**: N/A (documentation file)
- **Acceptance criteria**: SKILL.md exists, loads cleanly, contains all 13 sections, all examples use collapse/data.table, no tidyverse examples unless annotated as fallback

### 2. Create `references/mocking.md`

- **Files**: `.github/skills/cg-skill-r-testing/references/mocking.md`
- **Details**:
  - `local_mocked_bindings()` — basic pattern, package-scoped mocking (`.package` arg)
  - `with_mocked_bindings()` — block-scoped alternative
  - S3/S4/R6 method mocking — `local_mocked_s3_method()`, `local_mocked_s4_method()`, `local_mocked_r6_class()`
  - Common patterns: database connections (DBI/RSQLite mock), API calls (httr2 mock), file system ops, random number generation
  - Advanced packages: webfakes (fake HTTP servers), httptest2 (record/replay)
  - Best practices: mock at the right level, verify mock behavior, prefer real fixtures, document what's mocked
  - Migration: `with_mock()` → `local_mocked_bindings()`
  - All examples use data.table for any data construction
- **Tests**: N/A
- **Acceptance criteria**: Covers all mocking approaches in testthat 3+, no deprecated patterns without migration note

### 3. Create `references/fixtures.md`

- **Files**: `.github/skills/cg-skill-r-testing/references/fixtures.md`
- **Details**:
  - Three fixture approaches: constructor functions (data.table based), local functions with withr cleanup, static fixture files
  - Helper files (`helper-*.R`) — custom expectations, test data constructors
  - Setup files (`setup-*.R`) — suite-wide config
  - File system discipline — always use `withr::local_tempdir()`, always `test_path()` for fixtures
  - Database fixtures — in-memory SQLite pattern
  - Complex object fixtures — saveRDS/readRDS pattern
  - Fixture organization — directory structure recommendation
  - Best practices: keep small, document origins, deterministic
  - All constructor examples use `data.table()` not `data.frame()` or `tibble()`
- **Tests**: N/A
- **Acceptance criteria**: All three approaches documented with working examples, all data construction uses data.table

### 4. Create `references/snapshots.md`

- **Files**: `.github/skills/cg-skill-r-testing/references/snapshots.md`
- **Details**:
  - Basic usage, snapshot workflow (create/review/accept/reject)
  - Snapshot types: output, value, error
  - Transform function — removing timestamps, normalizing paths
  - Variants — platform/R-version-specific snapshots
  - Best practices: commit to git, review diffs, focused snapshots, fail on new in CI
  - Snapshot file structure (`_snaps/`)
  - Common patterns: error messages, side-by-side comparisons, printed output
- **Tests**: N/A
- **Acceptance criteria**: Full snapshot lifecycle documented, transform and variant patterns included

### 5. Create `references/bdd.md`

- **Files**: `.github/skills/cg-skill-r-testing/references/bdd.md`
- **Details**:
  - When to use BDD vs standard syntax (the key insight: `describe` for behavior specs, `test_that` for implementation correctness)
  - Basic syntax: `describe()` + `it()`
  - Nested specifications — component→function→behavior hierarchy
  - Pending specifications — `it()` without code body
  - Mixing BDD and standard syntax in the same file
  - BDD with fixtures, snapshots, mocking
  - Test-first workflow with BDD
  - File organization patterns
  - All data examples use data.table
- **Tests**: N/A
- **Acceptance criteria**: Clear guidance on when to choose BDD vs test_that, complete examples with nesting

### 6. Create `references/advanced.md`

- **Files**: `.github/skills/cg-skill-r-testing/references/advanced.md`
- **Details**:
  - Skipping tests — built-in skip functions, custom skip conditions
  - Testing flaky code — `try_again()`
  - Managing secrets — environment variables, local config, testing without secrets
  - Custom expectations — simple (one-liner) and complex (`quasi_label`/`expect()`)
  - State inspection — `set_state_inspector()`
  - CRAN considerations — time limits, file system discipline, no external deps, platform differences
  - Test performance — `reporter = "slow"`, shuffling
  - Parallel testing — `Config/testthat/parallel: true`
  - Edge case patterns — boundary conditions, empty inputs, type validation
  - Debugging — interactive (`browser()`), print debugging, capture output
  - Testing R6 and S4 classes
- **Tests**: N/A
- **Acceptance criteria**: All advanced topics covered, skip patterns and custom expectations are actionable

### 7. Replace `cg-skill-r-technical/references/testing-testthat.md` with redirect

- **Files**: `.github/skills/cg-skill-r-technical/references/testing-testthat.md` (modify)
- **Details**:
  - Replace entire content with a short redirect:
    ```markdown
    # Testing with testthat

    > **This reference has moved.** For comprehensive R testing patterns, load `cg-skill-r-testing`.
    >
    > For plumber endpoint and httr2 mock testing specifically, see [testing-apis.md](testing-apis.md).
    ```
- **Tests**: N/A
- **Acceptance criteria**: File is a redirect, no duplicate testing content remains

### 8. Create `cg-skill-r-technical/references/testing-apis.md`

- **Files**: `.github/skills/cg-skill-r-technical/references/testing-apis.md` (new)
- **Details**:
  - Move plumber endpoint testing section from old `testing-testthat.md` (the `make_req()` helper, GET/POST examples)
  - Move httr2 mocking section from old `testing-testthat.md` (`with_mocked_responses()` pattern)
  - Keep these under `cg-skill-r-technical` because they are about plumber/httr2 technology, not about testthat itself
- **Tests**: N/A
- **Acceptance criteria**: All plumber and httr2 testing content preserved, no content lost in the migration

### 9. Update `copilot-instructions.md` R skills section

- **Files**: `.github/copilot-instructions.md` (modify)
- **Details**:
  - Update the "Two R skills" bullet to mention three R skills:
    - `cg-skill-r-technical` — package/infrastructure work
    - `cg-skill-r-analytical` — statistical/econometric work
    - `cg-skill-r-testing` — testing R code with testthat
  - Add trigger guidance: "Load `cg-skill-r-testing` when writing, reviewing, or debugging R tests."
- **Tests**: N/A
- **Acceptance criteria**: All three R skills documented with clear load conditions

### 10. Update `cg-testing` agent to reference new skill

- **Files**: `.github/agents/cg-testing.agent.md` (modify)
- **Details**:
  - Change the R expertise line from "Load `cg-skill-r-technical` (testthat patterns, plumber testing)" to "Load `cg-skill-r-testing` for testthat patterns; load `cg-skill-r-technical` for plumber/httr2 API testing"
  - Keep the conditional load of `cg-skill-r-analytical` for welfare/survey code as-is
- **Tests**: N/A
- **Acceptance criteria**: Agent references `cg-skill-r-testing` as primary testing skill

### 11. Update `cg-skill-r-technical/SKILL.md` references section

- **Files**: `.github/skills/cg-skill-r-technical/SKILL.md` (modify)
- **Details**:
  - Change the references table entry from `[Testing with testthat](references/testing-testthat.md) — Test structure, assertions, fixtures` to `[Testing APIs](references/testing-apis.md) — Plumber endpoint and httr2 mock testing`
  - Add a note: "For comprehensive R testing patterns (testthat, fixtures, mocking, snapshots, BDD), load `cg-skill-r-testing`."
- **Tests**: N/A
- **Acceptance criteria**: No broken cross-references, clear pointer to new skill

## Testing Strategy

This is a documentation/skill feature — no executable tests. Quality is validated by:

1. **Structural check**: All 6 files exist in the correct paths
2. **Cross-reference check**: All markdown links between files resolve
3. **No duplication check**: `cg-skill-r-technical` contains zero testthat testing patterns (only API testing patterns)
4. **Content check**: All code examples use collapse/data.table; tidyverse appears only as annotated fallback
5. **Trigger check**: Skill description fires on `.R` test files, not on general R work — verify by reading the description against the skill selection logic

## Documentation Checklist

- [x] SKILL.md with frontmatter (name, description) — Step 1
- [ ] 5 reference files with full content — Steps 2–6
- [ ] Redirect in old location — Step 7
- [ ] Cross-references updated in cg-skill-r-technical — Steps 8, 11
- [ ] copilot-instructions.md updated — Step 9
- [ ] cg-testing agent updated — Step 10

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Skill description too broad — fires on general R code | Test description wording against other R skills; include "test" and "testthat" as primary triggers |
| Skill description too narrow — misses script testing (non-package) | Include "testing R code" not just "testing R packages" in description |
| Existing `testing-testthat.md` users hit broken reference | Redirect file preserves the path and points to the new location |
| Plumber/httr2 testing patterns lost in migration | Dedicated `testing-apis.md` preserves all content; verify line-by-line |
| collapse/data.table examples incorrect | Cross-reference `cg-skill-r-technical` and `cg-skill-r-analytical` for authoritative patterns |

## Out of Scope

- Python testing skill (`testing-skill-python` is a separate roadmap feature)
- Stata testing skill (`testing-skill-stata` is a separate roadmap feature)
- Skill description consistency audit across all skills (separate roadmap feature: `skill-description-consistency-audit`)
- Expanding collapse or data.table reference content (separate roadmap features)
- Workflow files inside the skill (Posit doesn't have them for testing; we don't need them either)
