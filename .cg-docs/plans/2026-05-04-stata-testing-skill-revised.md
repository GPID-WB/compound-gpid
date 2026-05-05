---
date: 2026-05-04
title: "Stata Testing & Reproducibility Skill (cg-skill-stata-testing) — revised"
status: completed
completed-date: 2026-05-04
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-01-stata-testing-skill.md"
language: "Stata"
estimated-effort: "large"
tags: [skills, stata, testing, reproducibility, reprun, repkit, assert, data-validation, revised]
---

# Plan: Stata Testing & Reproducibility Skill (revised)

> **Revision note**: Supersedes `2026-05-04-stata-testing-skill.md`. Addresses
> findings from two `/cg-plan-review` rounds:
> **Round 1** — P1.1 (template reference corrected to stata-best-practices routing pattern),
> P1.2 (500-char description cap removed — test asserts presence only),
> P2.1 (Step 6 split into 6a scaffolding + 6b anti-patterns),
> P2.2 (workflow-examples.md acknowledged as scope addition with rationale),
> P2.3 (dual-skill loading validation step added),
> P3.1 (reference count mismatch fixed).
> **Round 2** — P2.1 (phantom Step 8 removed, merged as pre-condition into Step 8),
> P2.2 (stata.instructions.md format specified, Pester tests expanded),
> P2.3 (docs/reference.md added to registration step),
> P3.1 (r.instructions.md description corrected — it IS the pattern template for Step 8),
> P3.2 (stata-best-practices SKILL.md line count corrected to ~120 lines).

## Objective

Create a new skill `cg-skill-stata-testing` that teaches Stata developers
reproducible testing workflows — from inline assertions through `reprun`
verification — so Copilot can guide both economists maintaining legacy `.do`
files and developers transitioning to R/Python. The skill follows the
**routing-table pattern** of `cg-skill-stata-best-practices` (thin SKILL.md
with on-demand reference files) and is conditionally loaded from
`stata.instructions.md` when testing context is detected.

## Context

- `cg-skill-stata-best-practices` already covers coding principles (11 anti-patterns),
  `repkit` documentation (repado, reprun, reproot, repscan, lint), and 21 community
  packages. It does NOT have a dedicated testing section — only scattered mentions
  of `assert` in workflow-best-practices.md. **Its SKILL.md uses the routing-table
  pattern** (thin shell that directs the model to load specific reference files
  on demand, ~120 lines for 35+ references). This is the structural template for
  the new skill. The new skill's much shorter routing table (7 files) easily fits
  under the 100-line budget.
- `cg-skill-r-testing` is a **cross-reference destination** for Stata→R migration
  context. It uses an inline-content pattern (not a routing table) — do NOT mirror
  its structure.
- The brainstorm decided: reproducibility is #1 priority; `reprun`/`reproot` are
  CORE (not optional); all 6 topic areas included; anti-patterns section references
  existing coding-principles and adds 8 testing-specific ones; examples are mixed
  across poverty, survey, harmonization, and causal inference — focused on testing
  the analysis, not performing the analysis.
- **Scope addition (beyond brainstorm)**: A standalone `workflow-examples.md` file
  is added as Step 7. Rationale: the brainstorm's "Workflow Examples" section (§7
  in proposed structure) intended domain examples; splitting them into a standalone
  file keeps reference files focused on one topic each and makes examples
  copy-pasteable. This is the most expensive deliverable — budget accordingly.
- `stata.instructions.md` currently routes only to `cg-skill-stata-best-practices`.
  The new skill will be loaded **conditionally** (when testing context is detected),
  not unconditionally on every `.do`/`.ado` file.
- `r.instructions.md` is the **direct pattern template for the conditional routing
  line** — it conditionally loads `cg-skill-r-testing` with the phrase "when writing,
  reviewing, or debugging R tests". Use matching syntax for `stata.instructions.md`.

## Requirements

| ID  | Requirement                                              | Source      |
|-----|----------------------------------------------------------|-------------|
| R1  | SKILL.md with routing table pointing to reference files  | pattern     |
| R2  | Quick reference: assert syntax, capture, error handling  | brainstorm  |
| R3  | Data validation patterns (pre-analysis checks)           | brainstorm  |
| R4  | Result verification (coefficient bounds, sign, stability)| brainstorm  |
| R5  | Reproducibility & reprun workflow (run → capture → compare) | brainstorm |
| R6  | Test scaffolding & loops (batch testing, isolation)      | brainstorm  |
| R7  | Anti-patterns: cross-reference existing + 8 testing-specific | brainstorm |
| R8  | Workflow examples (end-to-end, domain-specific)          | brainstorm+ |
| R9  | Cross-references to cg-skill-stata-best-practices and cg-skill-r-testing | brainstorm |
| R10 | Update `stata.instructions.md` with conditional routing  | convention  |
| R11 | Pester tests: file existence, description presence, cross-links | convention |
| R12 | Update `copilot-instructions.md` skill listing           | convention  |
| R13 | Examples focused on TESTING (not calculating)            | brainstorm  |
| R14 | SKILL.md stays under 100 lines (thin routing table)      | P2.3 fix    |

## Implementation Steps

### 1. Create SKILL.md with Routing Table

- **Requirements**: R1, R9, R14
- **Files**: Create `.github/skills/cg-skill-stata-testing/SKILL.md`
- **Details**:
  Frontmatter:
  ```yaml
  ---
  name: cg-skill-stata-testing
  description: "Testing and reproducibility best practices for Stata. Covers inline assertions (assert, capture, exit codes), data validation patterns, econometric result verification, reprun/repkit reproducibility workflows, test scaffolding, and testing anti-patterns. Load when writing, reviewing, or debugging test blocks in .do/.ado files. Use alongside cg-skill-stata-best-practices for coding principles and package reference."
  ---
  ```
  Body: **routing table** (following `cg-skill-stata-best-practices` pattern — NOT
  the inline-content pattern of `cg-skill-r-testing`):
  
  | File | Topics |
  |------|--------|
  | `references/assertions-and-error-handling.md` | `assert`, `capture`, `_rc`, exit codes, soft assertions |
  | `references/data-validation.md` | `isid`, `duplicates`, `misstable`, `inrange`, panel/survey validation |
  | `references/result-verification.md` | `_b[]`, `reldif`, `test`, coefficient bounds, stability |
  | `references/reproducibility-reprun.md` | `reprun`, `reproot`, `repscan`, result caching |
  | `references/test-scaffolding.md` | `foreach` loops, `preserve`/`restore`, test harness patterns |
  | `references/anti-patterns.md` | 8 testing-specific anti-patterns + cross-ref to coding-principles |
  | `references/workflow-examples.md` | End-to-end examples: poverty, PPP, survey, DiD |

  Brief intro paragraph (3–5 lines) explaining:
  - Purpose: testing & reproducibility patterns for Stata
  - When to load: test blocks, assertions, reprun workflows
  - Cross-references: `cg-skill-stata-best-practices` (coding-principles, repkit API),
    `cg-skill-r-testing` (for Stata→R migration mindset)

  **Constraint**: Total SKILL.md must stay under 100 lines. The routing table +
  intro + frontmatter should be ~50–70 lines.
- **Test Scenarios**:
  - ✅ SKILL.md exists and has valid frontmatter
  - ✅ All 7 reference files listed in routing table exist on disk
  - ✅ `description:` field is present and non-empty
  - ✅ Total line count ≤ 100
- **Tests**: Pester test asserting file exists, description is present, all
  reference paths resolve, line count ≤ 100.
- **Acceptance criteria**: SKILL.md loads cleanly, routing table references resolve,
  stays under 100-line budget.

### 2. Write `references/assertions-and-error-handling.md`

- **Requirements**: R2, R13
- **Files**: Create `.github/skills/cg-skill-stata-testing/references/assertions-and-error-handling.md`
- **Details**:
  Cover:
  - `assert` syntax: `assert condition`, `assert condition if qualifier`
  - Return codes and `_rc` inspection after `capture`
  - `capture noisily` vs `capture` (when to surface errors)
  - `exit` codes for custom error signaling
  - Structured assertion blocks (group related assertions with comments)
  - Messaging patterns: `display as error`, `display as result`
  - Pattern: assertion with context message
    ```stata
    * Verify no negative welfare values after PPP conversion
    count if welfare_ppp < 0
    local neg_count = r(N)
    assert `neg_count' == 0
    ```
  - Pattern: soft assertion (warn but continue)
    ```stata
    capture assert income > 0
    if _rc {
        display as error "WARNING: observations with non-positive income found"
    }
    ```
- **Test Scenarios**:
  - ✅ File exists and is non-empty
  - ✅ Contains `assert`, `capture`, `_rc`, `exit`
- **Tests**: Pester file-existence test.
- **Acceptance criteria**: Covers all assertion patterns a Stata user would need.

### 3. Write `references/data-validation.md`

- **Requirements**: R3, R13
- **Files**: Create `.github/skills/cg-skill-stata-testing/references/data-validation.md`
- **Details**:
  Cover pre-analysis validation patterns:
  - **Uniqueness checks**: `isid`, `duplicates report`, `duplicates tag`
  - **Missingness validation**: `misstable summarize`, custom missing-count assertions
  - **Value range checks**: `assert inrange(var, lo, hi)`, `assert inlist(var, ...)`
  - **Panel structure validation**: `xtset` + assert balanced panel
  - **Survey design checks**: validate PSU/strata structure, non-zero weights
  - **Cross-dataset consistency**: post-merge `_merge` validation, row-count checks
  - **Type safety**: `confirm numeric variable`, `confirm string variable`

  Example (testing data harmonization — PPP alignment):
  ```stata
  * --- Test: PPP conversion factors are aligned to correct vintage ---
  assert !missing(ppp_2017) if !missing(welfare_lcu)
  assert ppp_2017 > 0
  assert inrange(ppp_2017, 0.01, 10000)
  
  * Verify welfare variable completeness
  count if missing(welfare_lcu) & !missing(weight)
  assert r(N) == 0
  ```
- **Test Scenarios**:
  - ✅ File exists
  - ✅ Contains `isid`, `duplicates`, `assert`, `misstable`
- **Tests**: Pester file-existence test.
- **Acceptance criteria**: Covers data validation patterns for all 4 analysis domains.

### 4. Write `references/result-verification.md`

- **Requirements**: R4, R13
- **Files**: Create `.github/skills/cg-skill-stata-testing/references/result-verification.md`
- **Details**:
  Cover post-estimation testing patterns:
  - **Coefficient sign checks**: `assert _b[treatment] > 0`
  - **Magnitude bounds**: `assert abs(_b[var]) < threshold`
  - **Precision-aware comparison**: `assert reldif(estimate, expected) < tolerance`
  - **Statistical significance checks**: `test var = 0` + inspect `r(p)`
  - **Model diagnostic assertions**: R-squared bounds, F-stat, observation counts
  - **Cross-specification stability**: run multiple specs, assert coefficient stability
  - **FGT poverty index checks**: assert between 0 and 1, monotonicity by threshold

  Example (testing DiD parallel trends):
  ```stata
  * --- Test: Pre-treatment trends are parallel ---
  regress outcome i.treated##i.period controls, vce(cluster district)
  
  * Pre-period interaction should be insignificant
  test 1.treated#1.pre_period = 0
  assert r(p) > 0.05
  
  * Treatment effect should be positive and bounded
  local beta = _b[1.treated#1.post_period]
  assert `beta' > 0
  assert `beta' < 2.0
  ```
- **Test Scenarios**:
  - ✅ File exists
  - ✅ Contains `_b[`, `reldif`, `test`, `assert`
- **Tests**: Pester file-existence test.
- **Acceptance criteria**: Covers coefficient, precision, and diagnostic testing.

### 5. Write `references/reproducibility-reprun.md`

- **Requirements**: R5, R13
- **Files**: Create `.github/skills/cg-skill-stata-testing/references/reproducibility-reprun.md`
- **Details**:
  Core reproducibility testing patterns with `reprun`:
  - **Basic workflow**: `reprun "analysis.do"` — run twice, compare state
  - **Reading reprun output**: Seed RNG, Sort Order RNG, Data Checksum columns
  - **Common failure patterns and fixes** (distilled from existing repkit.md):
    - Missing `set seed` before random processes
    - Non-unique sort keys (`sort mpg` → `sort mpg make`)
    - `bysort` without secondary sort
  - **reproot for portable test paths**: test assertions using `${root_code}` not hard-coded paths
  - **repscan as pre-flight check**: scan before running full `reprun`
  - **Result caching pattern**: save expected results to file, compare on re-run
  - **Comparing against cached results**: load file, parse, `assert reldif() < tol`

  Note: Cross-reference `cg-skill-stata-best-practices/packages/repkit.md` for
  full `reprun` API documentation. This file focuses on **testing patterns using
  reprun**, not the tool's full API.
- **Test Scenarios**:
  - ✅ File exists
  - ✅ Contains `reprun`, `reproot`, `repscan`, `set seed`
  - ✅ Contains cross-reference link to `../../cg-skill-stata-best-practices/packages/repkit.md`
- **Tests**: Pester file-existence + cross-link resolution (existing block handles this).
- **Acceptance criteria**: Users can set up a reproducibility testing workflow from this file alone.

### 6a. Write `references/test-scaffolding.md`

- **Requirements**: R6, R13
- **Files**: Create `.github/skills/cg-skill-stata-testing/references/test-scaffolding.md`
- **Details**:
  Test loop patterns and isolation:
  - `foreach` loops for batch variable testing
  - `preserve`/`restore` for test isolation (test doesn't corrupt original data)
  - `tempfile` for intermediate test state
  - Test reporting: accumulate pass/fail counts and display summary
  - Pattern: test harness do-file structure
    ```stata
    * --- test_poverty_indices.do ---
    local tests_passed = 0
    local tests_failed = 0
    
    preserve
    
    foreach z in 1.90 3.20 5.50 {
        quietly poverty welfare [aw=weight], line(`z')
        
        capture assert inrange(r(head_count), 0, 1)
        if _rc {
            local ++tests_failed
            display as error "FAIL: FGT0 out of range for z=`z'"
        }
        else {
            local ++tests_passed
        }
    }
    
    restore
    
    display as result _n "Tests passed: `tests_passed'  Failed: `tests_failed'"
    assert `tests_failed' == 0
    ```
  - Pattern: multi-file test runner (master test do-file that runs sub-tests)
- **Test Scenarios**:
  - ✅ File exists
  - ✅ Contains `preserve`, `restore`, `foreach`, `tempfile`
- **Tests**: Pester file-existence test.
- **Acceptance criteria**: Users can build batch test harnesses from these patterns.

### 6b. Write `references/anti-patterns.md`

- **Requirements**: R7, R13
- **Files**: Create `.github/skills/cg-skill-stata-testing/references/anti-patterns.md`
- **Details**:
  Testing-specific anti-patterns catalog:
  - **Cross-reference header**: link to
    `../../cg-skill-stata-best-practices/references/coding-principles.md`
    (11 universal anti-patterns that also affect tests — don't repeat, just link)
  - **8 testing-specific anti-patterns** (each with: pattern, why it's wrong, fix):
    1. **Silent-passing assertions**: `capture assert ...` without checking `_rc` afterward
    2. **Not preserving data**: modifying master data in tests without `preserve`/`restore`
    3. **Hard-coded thresholds without documentation**: magic numbers in bounds with no comment
    4. **Floating-point precision**: `assert x == 0.1` instead of `assert reldif(x, 0.1) < 1e-10` or `assert float(x) == float(0.1)`
    5. **Breaking reprun with hard-coded paths**: using `"C:/Users/me/..."` instead of `reproot`
    6. **Order-dependent tests**: test B fails unless test A runs first
    7. **Undocumented test purpose**: no comment explaining what the assertion checks
    8. **Testing inside data-modifying code**: mixing assert blocks with `generate`/`replace`
  
  Each anti-pattern has:
  - ❌ Wrong pattern (code block)
  - ✅ Correct pattern (code block)
  - Brief explanation of why the wrong pattern fails
- **Test Scenarios**:
  - ✅ File exists
  - ✅ Contains cross-reference link to `coding-principles.md`
  - ✅ Contains `reldif`, `preserve`, `reproot`
- **Tests**: Pester file-existence + content assertions + cross-link resolution.
- **Acceptance criteria**: All 8 anti-patterns are actionable and include working fix examples.

### 7. Write `references/workflow-examples.md` (scope addition)

- **Requirements**: R8, R13
- **Files**: Create `.github/skills/cg-skill-stata-testing/references/workflow-examples.md`
- **Details**:
  > **Scope addition**: This file is beyond the brainstorm's locked 6-section
  > structure. Rationale: standalone examples file keeps reference files focused
  > on single topics and makes domain examples copy-pasteable for users.

  End-to-end testing workflows, one per domain:

  **Example 1: Testing poverty measurement (FGT indices)**
  - Load survey data → validate weights → compute FGT → assert bounds → reprun

  **Example 2: Testing data harmonization (PPP conversion)**
  - Load raw + PPP factors → validate alignment → convert → assert no negatives → compare with prior run

  **Example 3: Testing survey estimates (weighted means)**
  - Validate survey design → compute subpopulation means → assert SE magnitude → check reproducibility

  **Example 4: Testing causal inference (DiD)**
  - Load panel → validate balance → run DiD → assert pre-trends → bound treatment effect

  Each example follows the same structure:
  1. Setup (load data, validate inputs)
  2. Execute (run the analysis)
  3. Verify (assertions on results)
  4. Reproduce (reprun check)
  
  All examples are self-contained (include minimal synthetic data or describe the
  data shape expected) and focused on the testing methodology, not the calculation.
- **Test Scenarios**:
  - ✅ File exists
  - ✅ Contains all 4 domain keywords: poverty, PPP, survey, DiD
- **Tests**: Pester file-existence + content check.
- **Acceptance criteria**: A new user can copy any example and adapt it to their project.

### 8. Update `stata.instructions.md`, Register Skill, and Update Docs

- **Requirements**: R10, R12, R14
- **Pre-condition**: Verify SKILL.md is ≤ 100 lines before proceeding (ensures
  dual loading won't bloat context). If over budget, trim before registering.
- **Files**: 
  - Modify `.github/instructions/stata.instructions.md`
  - Modify `.github/copilot-instructions.md` (skill listing)
  - Modify `docs/reference.md` (skill catalog)
- **Details**:
  - **`stata.instructions.md`** — Add conditional routing line using the exact
    format from `r.instructions.md` (which uses: `- cg-skill-r-testing when writing,
    reviewing, or debugging R tests`):
    ```markdown
    - Load `cg-skill-stata-testing` when writing, reviewing, or debugging test
      blocks, assertion patterns, or reproducibility checks.
    ```
    This means it loads alongside `cg-skill-stata-best-practices` only when
    testing context is detected — NOT unconditionally on every `.do` file.
  - **`copilot-instructions.md`** — Add skill entry to the skill listing section
    with description matching SKILL.md frontmatter.
  - **`docs/reference.md`** — Add skill entry to the skill catalog table (matching
    format of existing `cg-skill-stata-best-practices` row).
- **Test Scenarios**:
  - ✅ `stata.instructions.md` mentions `cg-skill-stata-testing`
  - ✅ `stata.instructions.md` contains conditional language ("when writing...test blocks")
  - ✅ `copilot-instructions.md` lists the new skill
  - ✅ `docs/reference.md` lists the new skill
  - ✅ SKILL.md line count ≤ 100 (pre-condition check)
- **Tests**: Pester content assertions.
- **Acceptance criteria**: Copilot loads the skill conditionally on `.do`/`.ado`
  files when testing context is detected. All three registration locations are updated.

### 9. Add Pester Tests

- **Requirements**: R11, R14
- **Files**: Modify `tests/prompt-tools.Tests.ps1`
- **Details**:
  Add a `Describe "cg-skill-stata-testing - skill file structure"` block:
  - Assert SKILL.md exists
  - Assert all 7 reference files exist (file loop, same pattern as `cg-skill-r-testing` test block)
  - Assert `description:` field is present and non-empty (match existing pattern — NO length cap)
  - Assert SKILL.md mentions `cg-skill-stata-best-practices` (cross-reference)
  - Assert SKILL.md line count ≤ 100 (R14 — thin routing table enforcement)
  - Assert `anti-patterns.md` mentions `coding-principles` (cross-reference link)

  Add a `Describe "stata.instructions.md - skill routing"` block:
  - Assert `applyTo` field is present and covers `.do` and `.ado`
  - Assert file mentions `cg-skill-stata-best-practices` (existing routing)
  - Assert file mentions `cg-skill-stata-testing` (new conditional routing)
  - Assert conditional trigger language is present ("when writing", "test blocks")

  Add one assertion in existing `docs/reference.md` block (if present):
  - Assert `docs/reference.md` contains `cg-skill-stata-testing`

  Cross-link validation is already handled by the existing
  `"skill file cross-links resolve"` block — new files will be picked up automatically
  as long as markdown links use relative paths.
- **Test Scenarios**:
  - ✅ All new tests pass on first run
  - 🛑 Tests fail if a reference file is missing
  - 🛑 Tests fail if SKILL.md exceeds 100 lines
  - 🛑 Tests fail if `stata.instructions.md` is missing conditional routing
- **Tests**: Self-validating (tests test themselves).
- **Acceptance criteria**: Full suite passes (1300+ assertions, 0 failures).

## Testing Strategy

- **Structural tests** (Pester): file existence, description presence, cross-link resolution, line count
- **Content tests** (Pester): key terms present in each reference file (assert, reprun, preserve, etc.)
- **Manual validation**: read through each example and verify Stata syntax is correct
- **Cross-reference validation**: existing cross-link test block covers all new markdown links automatically
- **No description length cap test**: only assert presence/non-empty (existing pattern)

## Documentation Checklist

- [x] SKILL.md routing table with descriptions (serves as documentation)
- [ ] Each reference file has a clear heading structure
- [ ] Examples include comments explaining the testing methodology
- [ ] Cross-references to related skills use relative markdown links
- [ ] README.md — not applicable (skill files are self-documenting via SKILL.md)

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Overlap with existing repkit.md content | High | Low | Focus on testing PATTERNS, not API. Cross-reference existing repkit.md for full docs. |
| Examples contain incorrect Stata syntax | Medium | High | Manual review pass; load cg-skill-stata-best-practices during writing. |
| New skill bloats context when loaded alongside existing skill | Low | Medium | Routing table keeps SKILL.md thin (≤100 lines); conditional loading in instructions. |
| workflow-examples.md is expensive (scope addition) | Medium | Medium | Budget this as the longest step; defer to last content step so core files aren't shortchanged. |
| Cross-reference links break if skill directories are renamed | Low | Low | Existing cross-link Pester test catches this automatically. |

## Out of Scope

- Full `repkit` API documentation (already in `cg-skill-stata-best-practices/packages/repkit.md`)
- General coding principles / anti-patterns not related to testing (already in coding-principles.md)
- Automated test runners (Stata has no built-in test framework — patterns are manual)
- CI/CD integration for Stata tests (no standard tool exists)
- `.ado` file unit testing patterns (future enhancement — this plan covers `.do` file testing)
- Description length cap enforcement (no existing precedent; existing skills exceed any proposed cap)
