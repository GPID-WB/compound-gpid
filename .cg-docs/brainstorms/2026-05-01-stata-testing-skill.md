---
date: 2026-05-01
title: "Stata Testing Skill — Best Practices for Reproducible & Validated Analysis"
status: decided
scope: "Standard"
tags: [skills, stata, testing, data-validation, reproducibility, assert, reprun]
---

<!-- Valid status values: decided, in-progress, abandoned -->

# Stata Testing Skill — Best Practices for Reproducible & Validated Analysis

## Context

The **Skills Enhancement** milestone aims to deepen language skills so analytical team members get idiomatic patterns, anti-patterns, testing best practices, and workflow support without leaving Copilot. The Stata ecosystem currently has `cg-skill-stata-best-practices` covering 21 community packages, syntax, and gotchas — but **testing patterns are sparse**.

This brainstorm covers one feature: `testing-skill-stata` — a dedicated skill file that teaches Stata developers reproducible testing workflows using:
- **Inline assertions** (`assert`, `capture`, error handling)
- **Data validation** (missingness checks, panel structure, value ranges)
- **Result verification** (coefficient stability, sign checks, reproducibility)
- **Test scaffolding** (loops, control flow, `repkit` integration if in scope)

## Goals

1. **Make testing first-class in Stata workflows** — Users can ask Copilot "how do I test that X?" and get patterns, not generic suggestions.
2. **Bridge Stata→R migration** — Economists moving from Stata should see how testing patterns transfer (assertions in Stata ↔ testthat in R).
3. **Support reproducibility best practices** — Skill should reference `reprun` / `repkit` where relevant (but not require it).
4. **Reduce silent failures** — Teach "fail loudly" principle through assertion patterns.

## Key Questions — RESOLVED ✅

### Q1: Audience & Pain Points ✅

**Audience**: Mixed — both economists maintaining legacy `.do` files AND developers transitioning from Stata to R/Python.

**Pain point ranking** (highest to lowest priority):
1. **Reproducibility** — Verifying results match prior runs (hard to debug diffs)
2. **Scattered asserts** — Unclear semantics, no standard pattern
3. **Econometric result checking** — Coefficient bounds, sign, stability
4. **Data validation** — Lowest priority (secondary to reproducibility)

### Q2: Scope — Core Topics ✅

**All six areas included**, with reprun as CORE (not optional):
- ✅ **Inline assertions & error handling** — `assert`, `capture`, messaging, `exit` codes
- ✅ **Data validation** — checking assumptions before analysis (missingness, structure, ranges, duplicates)
- ✅ **Test loops & scaffolding** — `foreach`, `while`, control flow for running multiple tests
- ✅ **Econometric result checking** — coefficient bounds, sign checks, stability across subgroups
- ✅ **Reproducibility verification** — comparing results to prior runs (using `stored results`, diffing output)
- ✅ **`reprun` / `repkit` integration** — test patterns when using the reproducibility package

### Q3: `repkit` Scope ✅

**CORE, not optional.** Since reproducibility is your #1 pain point, `reprun`, `reproot`, and result caching should be front-and-center.

**Skill becomes**: "Testing & Reproducibility in Stata (with reprun/repkit)"

Key patterns:
- ✅ `reprun` — re-running prior scripts and diffing outputs
- ✅ `reproot` — managing working directory for portability
- ✅ Result caching — storing expected results and checking new runs

### Q4: Anti-Patterns ✅

**Yes, include an "Anti-Patterns & Gotchas" section.**

**Strategy**: 
- **Reference** the existing `cg-skill-stata-best-practices / references/coding-principles.md` (11 universal anti-patterns)
- **Add testing-specific anti-patterns** unique to this skill:
  - Silent-passing assertions (test doesn't fail when it should)
  - Not preserving/validating original data before tests
  - Hard-coded thresholds/tolerances without explanation
  - Result verification ignoring floating-point precision
  - Breaking `reprun` reproducibility with hard-coded paths (must use `reproot`)
  - Not isolating test blocks (tests affecting each other, order-dependent)
  - Not documenting what each test is checking for
  - Comparing results without understanding expected precision (e.g., integer vs double)

### Q5: Real-World Examples ✅

**Mixed examples across all domains**, aimed at TESTING (not calculating):
- ✅ **Poverty/welfare measurement** — Testing FGT indices, inequality measures
- ✅ **Data harmonization** — Testing PPP conversions, variable alignment validation
- ✅ **Survey analysis** — Testing design-aware weighted estimates, subpop assertions
- ✅ **Causal inference** — Testing DiD parallel trends, coefficient sign/magnitude checks
 ✅

**FINAL STRUCTURE:**

```
SKILL.md Header
- Name: cg-skill-stata-testing
- Description: Testing & reproducibility best practices in Stata (assert, reprun, repkit)
- When to Load: .do/.ado files; /cg-work on Stata code; any session writing test blocks

---

## 1. Quick Reference
   - assert syntax & error handling
   - capture for error trapping
   - exit codes & messaging
   - Cheat sheet table

## 2. Data Validation Patterns
   - Pre-analysis checks (missingness, structure, ranges)
   - Survey design validation
   - Example: Testing PPP conversion alignment (data harmonization domain)

## 3. Result Verification Patterns
   - Coefficient bounds & sign checks
   - Precision thresholds for floating-point comparisons
   - Stored result validation
   - Example: Testing DiD parallel trends (causal inference domain)

## 4. Reproducibility & reprun
   - reprun workflow: run → capture → compare
   - reproot for portable paths
   - Result caching strategies
   - Example: Testing FGT poverty indices (poverty/welfare domain)

## 5. Test Scaffolding & Loops
   - Loop patterns for batch testing
   - Test isolation & order independence
   - Example: Testing survey-weighted estimates (survey analysis domain)

## 6. Anti-Patterns & Gotchas
   - Cross-reference to cg-skill-stata-best-practices/coding-principles.md (11 universal patterns)
   - Testing-specific anti-patterns (8 patterns unique to testing)
   - Floating-point precision gotchas
   - reprun portability traps
BRAINSTORM COMPLETE ✅

**Status**: DECIDED — all key questions answered, scope locked, examples scoped to testing across 4 domains.

**Next Steps**: → Ready for `/cg-plan` to create implementation plan with:
- SKILL.md file structure and content outline
- 20–30 code examples (5–7 per section, domain-mixed)
- Test coverage plan (Pester assertions on description length, completeness)
- Integration points with cg-skill-stata-best-practices (cross-references)
- Estimated effort: Large (~15–20 hours development + review
   - Links to:
     - cg-skill-stata-best-practices (coding-principles)
     - cg-skill-r-testing (migration mindset for Stata→R users)
     - repkit documentation (reprun, reproot)
```
**Anti-patterns**: Yes, include a section.

**Examples**: Mix of survey/poverty measurement (World Bank context) + generic patterns.

## Next Steps

→ Ready for `/cg-plan` to create implementation plan with:
- SKILL.md file structure
- Detailed content outline
- Code examples to write
- Test coverage plan (Pester assertions on description length, completeness)
- Integration with cg-skill-stata-best-practices (cross-references)
