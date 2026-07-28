---
name: cg-skill-r-testing
user-invokable: false
description: "Best practices for testing R code with testthat 3+. Use when writing, reviewing, debugging, or improving tests in .R or .Rmd files — including test_that(), describe()/it(), expect_*() calls, test fixtures, mocking, and snapshot tests. Covers test structure, core expectations, design principles, test data construction (data.table for data.table-collapse projects, tibble for tidyverse projects), collapse for statistical assertions in both dialects, fixtures, mocking with local_mocked_bindings(), snapshots, and BDD-style testing. Load alongside cg-skill-r-technical for plumber/httr2 API testing and cg-skill-r-analytical for welfare/survey testing patterns."
---

# Testing R Code with testthat

Modern best practices for R testing using testthat 3+. Default examples use **data.table** for test data construction and **collapse** for statistical assertions. For projects with `r-syntax: "tidyverse"` in `compound-gpid.local.md`, use `tibble()` and dplyr for test data construction — statistical assertions still use collapse functions since they work identically on tibbles.

## Initial Setup

Initialize testthat 3rd edition:

```r
usethis::use_testthat(3)
```

Creates `tests/testthat/`, adds testthat to `DESCRIPTION` Suggests with `Config/testthat/edition: 3`, and creates `tests/testthat.R`.

## File Organization

**Mirror package structure:**
- Code in `R/foofy.R` → tests in `tests/testthat/test-foofy.R`
- `usethis::use_test("foofy")` creates paired test file

**Special files:**
- `helper-*.R` — helper functions and custom expectations, sourced before all tests
- `setup-*.R` — run during `R CMD check` and `devtools::test()`, not `load_all()`
- `fixtures/` — static test data files accessed via `test_path()`

```
tests/testthat/
├── fixtures/
│   ├── sample.rds
│   └── edge-case.csv
├── helper-constructors.R    # data.table constructors, custom expectations
├── setup-options.R          # suite-wide options
└── test-*.R                 # test files
```

## Test Structure

### Standard Syntax

```r
test_that("foofy() returns expected result", {
  dt <- data.table(id = 1:3, value = c(10, 20, 30))
  result <- foofy(dt)
  expect_equal(nrow(result), 3)
  expect_equal(result$computed, c(100, 200, 300))
})
```

Test descriptions read naturally and describe behavior, not implementation.

### BDD Syntax (describe/it)

Use when documenting component behavior or writing test-first:

```r
describe("foofy()", {
  it("processes numeric values correctly", {
    dt <- data.table(x = 1:3)
    expect_equal(foofy(dt)$x, c(1, 4, 9))
  })

  it("returns empty data.table for empty input", {
    empty <- data.table(x = integer())
    expect_equal(nrow(foofy(empty)), 0L)
  })

  it("rejects non-data.table input")  # pending specification
})
```

**Key insight:** "Use `describe()` to verify you implement the right things; use `test_that()` to ensure you do things right."

Read `references/bdd.md` in this directory for nesting, test-first workflow, and mixing both styles.

## Running Tests

```r
# Micro: interactive development
devtools::load_all()
expect_equal(foofy(dt), expected)

# Mezzo: single file
testthat::test_file("tests/testthat/test-foofy.R")

# Macro: full suite
devtools::test()                          # Ctrl+Shift+T
devtools::test(reporter = "slow")         # identify slow tests
devtools::test(shuffle = TRUE)            # detect ordering dependencies
devtools::check()                         # full R CMD check
```

## Core Expectations

### Equality

```r
expect_equal(result, expected)              # allows numeric tolerance
expect_identical(result, expected)          # exact match, no tolerance
expect_equal(x, 0.42, tolerance = 1e-10)   # explicit tolerance
expect_equal(result, expected, ignore_attr = TRUE)  # ignore attributes
```

### Errors, Warnings, Messages

```r
expect_error(bad_call(), "message pattern")
expect_error(bad_call(), class = "specific_error_class")  # preferred
expect_no_error(valid_call())

expect_warning(deprecated_func())
expect_no_warning(safe_func())

expect_message(informative_func())
expect_no_message(quiet_func())
```

### Pattern Matching

```r
expect_match(string, "pattern")
expect_match(string, "pattern", ignore.case = TRUE)
```

### Structure and Type

```r
expect_length(vec, 10)
expect_type(obj, "list")
expect_s3_class(dt, "data.table")
expect_null(result)
expect_named(dt, c("id", "value", "weight"))
expect_named(dt, c("id", "value"), ignore.order = TRUE)
```

### Sets and Collections

```r
expect_setequal(x, y)              # same elements, any order
expect_in("a", c("a", "b", "c"))   # element membership
expect_contains(result_cols, required_cols)  # superset check (requires testthat >= 3.2.0)
```

### Logical

```r
expect_true(all(dt$value > 0))
expect_false(anyNA(dt$weight))
```

## Design Principles

### 1. Self-Sufficient Tests

Each test contains all its own setup — no ambient state:

```r
# Good: self-contained
test_that("fmean() respects weights", {
  dt <- data.table(y = c(1, 2, 3), w = c(1, 2, 1))
  expect_equal(fmean(dt$y, w = dt$w), 2.0, tolerance = 1e-10)
})

# Bad: relies on dt defined outside
dt <- data.table(y = c(1, 2, 3), w = c(1, 2, 1))
test_that("fmean() respects weights", {
  expect_equal(fmean(dt$y, w = dt$w), 2.0)  # where did dt come from?
})
```

### 2. Self-Contained — Use withr for Side Effects

```r
test_that("fwrite() produces correct CSV output", {
  dt <- data.table(id = 1:3, value = c(10.1, 20.2, 30.3))
  path <- withr::local_tempfile(fileext = ".csv")
  fwrite(dt, path)
  result <- fread(path)
  expect_equal(result, dt)
})
```

Common `withr` functions: `local_tempfile()`, `local_tempdir()`, `local_options()`, `local_envvar()`, `local_package()`.

### 3. Repetition Is Acceptable

Repeat setup code across tests rather than factoring it out. Test clarity beats DRY.

### 4. Use `devtools::load_all()` Workflow

During development use `load_all()` instead of `library()`. Makes all functions available (including unexported) and automatically attaches testthat — no `library()` calls needed in test files.

### 5. Plan for Test Failure

Write tests assuming they will fail and need debugging. Make test logic explicit and obvious. Avoid hidden dependencies on earlier tests.

## Common Patterns

### Testing collapse Output

```r
test_that("fmean() computes weighted mean correctly", {
  dt <- data.table(y = c(1, 2, 3), w = c(1, 2, 1))
  # (1*1 + 2*2 + 3*1) / (1+2+1) = 8/4 = 2.0
  expect_equal(fmean(dt$y, w = dt$w), 2.0, tolerance = 1e-10)
})

test_that("collap() aggregates by group with weighted means", {
  dt <- data.table(g = c("a", "a", "b"), y = c(10, 20, 30), w = c(1, 1, 1))
  result <- collap(dt, ~ g, fmean, w = ~ w, cols = "y")
  expect_equal(nrow(result), 2)
  expect_equal(result[g == "a"]$y, 15, tolerance = 1e-10)
  expect_equal(result[g == "b"]$y, 30, tolerance = 1e-10)
})

test_that("fwithin() centers values to zero within groups", {
  dt <- data.table(g = c("a", "a", "b", "b"), y = c(10, 20, 100, 200))
  centered <- fwithin(dt$y, g = dt$g)
  # fmean(g=) returns a named vector; use ignore_attr=TRUE to compare numerics only
  expect_equal(fmean(centered, g = dt$g), c(0, 0), tolerance = 1e-10, ignore_attr = TRUE)
})

test_that("TRA='replace' fills each row with its group mean", {
  dt <- data.table(g = c("a", "a", "b"), y = c(10, 20, 30))
  result <- fmean(dt$y, g = dt$g, TRA = "replace")
  expect_equal(result, c(15, 15, 30))
})

test_that("GRP object produces same result as raw grouping", {
  dt <- data.table(g = c("a", "a", "b"), y = c(10, 20, 30))
  grp <- GRP(dt, ~ g)
  expect_equal(fmean(dt$y, g = dt$g), fmean(dt$y, g = grp))
})

test_that("collapse na.rm default silently removes NAs", {
  dt <- data.table(id = 1:3, value = c(1, NA, 3))
  expect_equal(fmean(dt$value), 2)
  expect_equal(fnobs(dt$value), 2L)
})

test_that("panel lag flag() returns NA for first obs per unit", {
  dt <- data.table(id = c(1, 1, 2, 2), year = c(2020, 2021, 2020, 2021),
                   y = c(10, 12, 20, 25))
  pdt <- findex_by(dt, id, year)
  lagged <- flag(pdt$y, 1)
  expect_true(is.na(lagged[1]))
  expect_true(is.na(lagged[3]))
  expect_equal(lagged[2], 10)
  expect_equal(lagged[4], 20)
})
```

### Testing data.table

```r
test_that("right join produces expected row count and NAs", {
  dt_a <- data.table(id = 1:3, val = c("x", "y", "z"))
  dt_b <- data.table(id = 2:4, num = c(10, 20, 30))
  result <- dt_b[dt_a, on = "id"]
  expect_equal(nrow(result), 3)
  expect_true(is.na(result[id == 1, num]))
  expect_equal(result[id == 2, num], 10)
})

test_that(":= modifies data.table in place by reference", {
  dt <- data.table(x = 1:3)
  obj_before <- .Internal(inspect(dt))
  dt[, y := x * 2]
  expect_true("y" %in% names(dt))
  expect_equal(dt$y, c(2L, 4L, 6L))
})

test_that("fread/fwrite round-trip preserves data exactly", {
  dt <- data.table(id = 1:5, label = letters[1:5], value = c(1.1, 2.2, 3.3, 4.4, 5.5))
  path <- withr::local_tempfile(fileext = ".csv")
  fwrite(dt, path)
  result <- fread(path)
  expect_equal(result, dt)
})
```

### Edge Cases

```r
test_that("handles empty data.table gracefully", {
  empty <- data.table(id = integer(), value = numeric())
  result <- my_function(empty)
  expect_equal(nrow(result), 0L)
  expect_s3_class(result, "data.table")
})

test_that("handles single-row input", {
  dt <- data.table(id = 1L, value = 42)
  expect_no_error(my_function(dt))
})

test_that("rejects non-data.table input with informative error", {
  expect_error(my_function(list(x = 1)), class = "my_error_class")
  expect_error(my_function("string"), class = "my_error_class")
})

test_that("handles all-NA column", {
  dt <- data.table(id = 1:3, value = NA_real_)
  expect_true(is.na(fmean(dt$value)))
  expect_equal(fnobs(dt$value), 0L)
})
```

### Custom Expectations in Helper Files

```r
# tests/testthat/helper-expectations.R
expect_valid_dt <- function(x, min_rows = 1L, required_cols = character()) {
  expect_s3_class(x, "data.table")
  expect_gte(nrow(x), min_rows)
  if (length(required_cols)) {
    expect_contains(names(x), required_cols)  # requires testthat >= 3.2.0
  }
}

expect_no_missing <- function(x) {
  expect_false(anyNA(x), info = "Unexpected NAs found")
}
```

## Snapshot Testing

For complex output that's hard to verify programmatically, use `expect_snapshot()`.
Read `references/snapshots.md` in this directory for examples, transforms, variants, and full workflow.

## Mocking

Replace external dependencies during testing with `local_mocked_bindings()`.
Read `references/mocking.md` in this directory for S3/S4/R6 method mocking, webfakes, httptest2, and best practices.

Three approaches: constructor functions (preferred), static fixture files, and local functions with cleanup.
Read `references/fixtures.md` in this directory for helper files, setup files, database fixtures, and organization.

## testthat 3 Modernizations

| Deprecated | Modern |
|---|---|
| `context()` | Remove — filename already provides context |
| `expect_equivalent()` | `expect_equal(ignore_attr = TRUE)` |
| `with_mock()` | `local_mocked_bindings()` |
| `is_null()`, `is_true()`, `is_false()` | `expect_null()`, `expect_true()`, `expect_false()` |

**Edition 3 required:** `Config/testthat/edition: 3` in `DESCRIPTION`.

## Quick Reference

| Task | Code |
|------|------|
| Initialize | `usethis::use_testthat(3)` |
| Run full suite | `devtools::test()` |
| Run single file | `testthat::test_file("tests/testthat/test-x.R")` |
| Review snapshots | `testthat::snapshot_review()` |

## Cross-References

- **`cg-skill-r-technical`** — Load for plumber endpoint and httr2 mock testing, including its `references/testing-apis.md` resource
- **`cg-skill-r-analytical`** — Load for welfare/survey testing patterns (FGT indices, weighted stats, PPP units)
- **[references/bdd.md](references/bdd.md)** — BDD-style testing: describe/it, nesting, test-first workflows
- **[references/mocking.md](references/mocking.md)** — Mocking strategies, webfakes, httptest2
- **[references/fixtures.md](references/fixtures.md)** — Fixture patterns, database fixtures, helper/setup files
- **[references/snapshots.md](references/snapshots.md)** — Snapshot testing, transforms, variants
- **[references/advanced.md](references/advanced.md)** — Skipping tests, parallel testing, custom expectations, CRAN requirements
- **[references/test-integrity.md](references/test-integrity.md)** — Load when fixing bugs or reviewing tests for tautology. Covers expected behavior sources, mutation verification protocol, test gap taxonomy, and tautological test detection.
