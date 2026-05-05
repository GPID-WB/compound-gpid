---
date: 2026-05-04
title: "Stata Testing & Reproducibility Skill (cg-skill-stata-testing)"
status: superseded
superseded-by: ".cg-docs/plans/2026-05-04-stata-testing-skill-revised.md"
scope: "Standard"
brainstorm: ".cg-docs/brainstorms/2026-05-01-stata-testing-skill.md"
language: "Stata"
estimated-effort: "large"
tags: [skills, stata, testing, reproducibility, reprun, repkit, assert, data-validation]
---

# Plan: Stata Testing & Reproducibility Skill

## Objective

Create a new skill `cg-skill-stata-testing` that teaches Stata developers
reproducible testing workflows — from inline assertions through `reprun`
verification — so Copilot can guide both economists maintaining legacy `.do`
files and developers transitioning to R/Python. The skill is core-loaded
alongside `cg-skill-stata-best-practices` on all `.do`/`.ado` files.

## Context

- `cg-skill-stata-best-practices` already covers coding principles (11 anti-patterns),
  `repkit` documentation (repado, reprun, reproot, repscan, lint), and 21 community
  packages. It does NOT have a dedicated testing section — only scattered mentions
  of `assert` in workflow-best-practices.md.
- `cg-skill-r-testing` provides the structural template: SKILL.md with routing
  table + 5 reference files. This is the proven pattern.
- The brainstorm decided: reproducibility is #1 priority; `reprun`/`reproot` are
  CORE (not optional); all 6 topic areas included; anti-patterns section references
  existing coding-principles and adds 8 testing-specific ones; examples are mixed
  across poverty, survey, harmonization, and causal inference — focused on testing
  the analysis, not performing the analysis.
- `stata.instructions.md` currently routes only to `cg-skill-stata-best-practices`.
  It needs to also mention the new testing skill.

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
| R8  | Workflow examples (end-to-end, domain-specific)          | brainstorm  |
| R9  | Cross-references to cg-skill-stata-best-practices and cg-skill-r-testing | brainstorm |
| R10 | Update `stata.instructions.md` to mention new skill     | convention  |
| R11 | Pester tests: file existence, description length, cross-links | convention |
| R12 | Update `copilot-instructions.md` skill listing           | convention  |
| R13 | Examples focused on TESTING (not calculating)            | brainstorm  |

## Implementation Steps

### 1. Create SKILL.md with Routing Table

- **Requirements**: R1, R9
- **Files**: Create `.github/skills/cg-skill-stata-testing/SKILL.md`
- **Details**:
  Frontmatter:
  ```yaml
  ---
  name: cg-skill-stata-testing
  description: "Testing and reproducibility best practices for Stata. Covers
    inline assertions (assert, capture, exit codes), data validation patterns,
    econometric result verification, reprun/repkit reproducibility workflows,
    test scaffolding, and testing anti-patterns. Load when writing, reviewing,
    or debugging test blocks in .do/.ado files. Use alongside
    cg-skill-stata-best-practices for coding principles and package reference."
  ---
  ```
  Body: routing table pointing to 5 reference files:
  - `references/assertions-and-error-handling.md` (R2)
  - `references/data-validation.md` (R3)
  - `references/result-verification.md` (R4)
  - `references/reproducibility-reprun.md` (R5)
  - `references/test-scaffolding.md` (R6)
  - `references/anti-patterns.md` (R7)
  - `references/workflow-examples.md` (R8)

  Brief intro paragraph explaining the skill's purpose, when to load it, and
  cross-references to `cg-skill-stata-best-practices` (coding-principles) and
  `cg-skill-r-testing` (for Stata→R migration context).
- **Test Scenarios**:
  - ✅ SKILL.md exists and has valid frontmatter
  - ✅ All 7 reference files listed in routing table exist on disk
  - 🛑 Description under 500 characters (skill description length convention)
- **Tests**: Pester test asserting file exists, description is present, all
  reference paths resolve.
- **Acceptance criteria**: SKILL.md loads cleanly, routing table references resolve.

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
    assert `neg_count' == 0, ///
        rc(9) // "Found `neg_count' negative welfare values after PPP conversion"
    ```
  - Pattern: soft assertion (warn but continue)
    ```stata
    capture assert income > 0
    if _rc {
        display as error "WARNING: `=r(N)' observations with non-positive income"
        // Log but don't halt — downstream code handles this
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
  assert inrange(ppp_2017, 0.01, 10000) // no implausible conversion factors
  
  * Verify welfare variable completeness
  count if missing(welfare_lcu) & !missing(weight)
  assert r(N) == 0 // no weighted observations should lack welfare
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
  * --- Test: Pre-treatment trends are parallel (coefficient near zero) ---
  regress outcome i.treated##i.period controls, vce(cluster district)
  
  * Pre-period interaction should be insignificant
  test 1.treated#1.pre_period = 0
  assert r(p) > 0.05 // fail if pre-trend is significant at 5%
  
  * Treatment effect should be positive and bounded
  local beta = _b[1.treated#1.post_period]
  assert `beta' > 0            // expected direction
  assert `beta' < 2.0          // sanity bound — not implausibly large
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
  - **Common failure patterns and fixes** (from existing repkit.md — distill into testing context):
    - Missing `set seed` before random processes
    - Non-unique sort keys (`sort mpg` → `sort mpg make`)
    - `bysort` without secondary sort
  - **reproot for portable test paths**: test assertions using `${root_code}` not hard-coded paths
  - **repscan as pre-flight check**: scan before running full `reprun`
  - **Result caching pattern**:
    ```stata
    * --- Save expected results for future comparison ---
    regress y x1 x2, vce(robust)
    local expected_b1 = _b[x1]
    local expected_N  = e(N)
    
    * Write to a comparison file
    file open fh using "${root}/tests/expected/regression_results.txt", write replace
    file write fh "b_x1=`expected_b1'" _n
    file write fh "N=`expected_N'" _n
    file close fh
    ```
  - **Comparing against cached results**:
    ```stata
    * --- Verify current results match expected ---
    regress y x1 x2, vce(robust)
    
    * Load expected values
    file open fh using "${root}/tests/expected/regression_results.txt", read
    file read fh line
    local expected_b1 = substr("`line'", strpos("`line'", "=") + 1, .)
    file close fh
    
    * Compare with tolerance
    assert reldif(_b[x1], `expected_b1') < 1e-6
    ```

  Note: Cross-reference `cg-skill-stata-best-practices/packages/repkit.md` for
  full `reprun` documentation. This file focuses on **testing patterns using reprun**,
  not the tool's full API.
- **Test Scenarios**:
  - ✅ File exists
  - ✅ Contains `reprun`, `reproot`, `repscan`, `set seed`
  - ✅ Contains cross-reference to repkit.md
- **Tests**: Pester file-existence + cross-link resolution.
- **Acceptance criteria**: Users can set up a reproducibility testing workflow from this file alone.

### 6. Write `references/test-scaffolding.md` and `references/anti-patterns.md`

- **Requirements**: R6, R7, R13
- **Files**: 
  - Create `.github/skills/cg-skill-stata-testing/references/test-scaffolding.md`
  - Create `.github/skills/cg-skill-stata-testing/references/anti-patterns.md`
- **Details**:

  **test-scaffolding.md** — Test loop patterns and isolation:
  - `foreach` loops for batch variable testing
  - `preserve`/`restore` for test isolation (test doesn't corrupt original data)
  - `tempfile` for intermediate test state
  - Test reporting: accumulate pass/fail counts and display summary
  - Pattern: test harness do-file structure
    ```stata
    * --- test_poverty_indices.do ---
    * Tests FGT poverty indices across multiple thresholds
    
    local tests_passed = 0
    local tests_failed = 0
    
    preserve
    
    foreach z in 1.90 3.20 5.50 {
        quietly poverty welfare [aw=weight], line(`z')
        
        * FGT0 must be between 0 and 1
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

  **anti-patterns.md** — Testing-specific anti-patterns:
  - Cross-reference header pointing to `cg-skill-stata-best-practices/references/coding-principles.md`
    (11 universal anti-patterns)
  - 8 testing-specific anti-patterns:
    1. **Silent-passing assertions**: `assert` after `capture` without checking `_rc`
    2. **Not preserving data**: modifying master data in tests without `preserve`/`restore`
    3. **Hard-coded thresholds without documentation**: magic numbers in bounds
    4. **Floating-point precision**: `assert x == 0.1` instead of `reldif()` or `float()`
    5. **Breaking reprun with hard-coded paths**: using `"C:/Users/me/..."` instead of `reproot`
    6. **Order-dependent tests**: test B fails unless test A runs first
    7. **Undocumented test purpose**: no comment explaining what the assertion checks
    8. **Testing inside data-modifying code**: mixing assert blocks with `generate`/`replace`
- **Test Scenarios**:
  - ✅ Both files exist
  - ✅ anti-patterns.md contains cross-reference to coding-principles.md
  - ✅ anti-patterns.md mentions `reldif`, `preserve`, `reproot`
- **Tests**: Pester file-existence + content assertions.
- **Acceptance criteria**: Anti-patterns are actionable and include fix examples.

### 7. Write `references/workflow-examples.md`

- **Requirements**: R8, R13
- **Files**: Create `.github/skills/cg-skill-stata-testing/references/workflow-examples.md`
- **Details**:
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

### 8. Update `stata.instructions.md` and Register Skill

- **Requirements**: R10, R12
- **Files**: 
  - Modify `.github/instructions/stata.instructions.md`
  - Modify `.github/copilot-instructions.md` (skill listing)
- **Details**:
  - Add routing line to `stata.instructions.md`:
    > Load `cg-skill-stata-testing` when writing, reviewing, or debugging
    > test blocks, assertion patterns, or reproducibility checks in `.do`/`.ado` files.
  - Add skill entry to the `<skills>` list in `copilot-instructions.md` with appropriate description.
- **Test Scenarios**:
  - ✅ `stata.instructions.md` mentions `cg-skill-stata-testing`
  - ✅ `copilot-instructions.md` lists the new skill
- **Tests**: Pester content assertions.
- **Acceptance criteria**: Copilot loads the skill automatically on `.do`/`.ado` files when testing context is detected.

### 9. Add Pester Tests

- **Requirements**: R11
- **Files**: Modify `tests/prompt-tools.Tests.ps1`
- **Details**:
  Add a `Describe "cg-skill-stata-testing - skill file structure"` block:
  - Assert SKILL.md exists
  - Assert all 7 reference files exist (file loop, same pattern as `cg-skill-r-testing`)
  - Assert description length ≤ 500 characters
  - Assert SKILL.md mentions `cg-skill-stata-best-practices` (cross-reference)
  - Assert `anti-patterns.md` mentions `coding-principles` (cross-reference link)

  Cross-link validation is already handled by the existing
  `"skill file cross-links resolve"` block — new files will be picked up automatically
  as long as markdown links use relative paths.
- **Test Scenarios**:
  - ✅ All new tests pass on first run
  - 🛑 Tests fail if a reference file is missing
- **Tests**: Self-validating (tests test themselves).
- **Acceptance criteria**: Full suite passes (1300+ assertions, 0 failures).

## Testing Strategy

- **Structural tests** (Pester): file existence, description quality, cross-link resolution
- **Content tests** (Pester): key terms present in each reference file (assert, reprun, preserve, etc.)
- **Manual validation**: read through each example and verify Stata syntax is correct
- **Cross-reference validation**: existing cross-link test block covers all new markdown links automatically

## Documentation Checklist

- [x] SKILL.md routing table with descriptions (serves as documentation)
- [ ] Each reference file has a clear heading structure
- [ ] Examples include comments explaining the testing methodology
- [ ] Cross-references to related skills are bidirectional where useful
- [ ] README.md — not applicable (skill files are self-documenting via SKILL.md)

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Overlap with existing repkit.md content | High | Low | Focus new file on testing PATTERNS with reprun, not reprun API. Cross-reference existing repkit.md for full API docs. |
| Skill description exceeds length cap | Medium | Low | Keep under 500 chars; test enforces this. |
| Examples contain incorrect Stata syntax | Medium | High | Manual review pass; load cg-skill-stata-best-practices during writing. |
| New skill bloats context when loaded alongside existing skill | Low | Medium | Routing table keeps only SKILL.md in context; reference files loaded on-demand. |

## Out of Scope

- Full `repkit` API documentation (already in `cg-skill-stata-best-practices/packages/repkit.md`)
- General coding principles / anti-patterns not related to testing (already in coding-principles.md)
- Automated test runners (Stata has no built-in test framework — patterns are manual)
- CI/CD integration for Stata tests (no standard tool exists)
- `.ado` file unit testing patterns (future enhancement — this plan covers `.do` file testing)
