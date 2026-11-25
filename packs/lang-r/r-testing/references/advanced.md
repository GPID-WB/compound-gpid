# Advanced Testing Topics

Advanced patterns for production-quality test suites. All data construction uses **data.table** and **collapse**.

## Version Compatibility

Key version-gated functions in the cg-skill-r-testing reference files:

| Function | Minimum testthat | Notes |
|---|---|---|
| `local_mocked_bindings()` | 3.0.0 | Replaces `with_mock()` |
| `with_mocked_bindings()` | 3.0.0 | Block-scoped variant |
| `set_state_inspector()` | 3.0.0 | Detects global state drift |
| `snapshot_review()` | 3.0.0 | Interactive review of snapshot changes |
| `snapshot_accept()` / `snapshot_reject()` | 3.0.0 | Accept or revert snapshots |
| `local_mocked_s3_method()` | 3.2.2 | Replaces method dispatch during test |
| `snapshot_download_gh()` | 3.3.0 | Download snapshots from GitHub CI |
| `expect_no_condition()` | 3.2.0 | Assert no condition is signalled |

> **Check your version**: `packageVersion("testthat")`. Team standard is testthat ≥ 3.2.0 (ships with R 4.2+). Install the latest with `pak::pak("testthat")` if needed.



## Skipping Tests

### Built-in Skip Functions

```r
test_that("API integration works end-to-end", {
  skip_if_offline()
  skip_if_not_installed("httr2")
  skip_on_cran()
  skip_on_ci()                     # skip on GitHub Actions, etc.
  skip_on_os("windows")            # skip on specific OS

  result <- call_external_api("NGA", 2023)
  expect_s3_class(result, "data.table")
})
```

| Function | When to use |
|---|---|
| `skip()` | Unconditional skip with message |
| `skip_if(cond)` | Skip if condition is `TRUE` |
| `skip_if_not(cond)` | Skip if condition is `FALSE` |
| `skip_if_offline()` | No internet access |
| `skip_if_not_installed("pkg")` | Package not installed |
| `skip_on_cran()` | Running under `R CMD check` on CRAN |
| `skip_on_ci()` | Running in CI environment |
| `skip_on_os("windows")` | Specific OS |
| `skip_if(getRversion() < "4.2.0")` | R version requirement (all testthat 3.x) |

### Custom Skip Conditions

```r
skip_if_no_api_key <- function(key = "POVERTY_API_KEY") {
  if (Sys.getenv(key) == "") skip(paste(key, "not set"))
}

skip_if_slow_tests_disabled <- function() {
  if (!identical(Sys.getenv("RUN_SLOW_TESTS"), "true")) {
    skip("Set RUN_SLOW_TESTS=true to run slow tests")
  }
}

test_that("full pipeline runs correctly", {
  skip_if_no_api_key()
  skip_if_slow_tests_disabled()

  result <- run_full_pipeline("NGA", year = 2023)
  expect_s3_class(result, "data.table")
})
```

## Managing Secrets in Tests

### Environment Variables

```r
test_that("authenticated endpoint works", {
  api_key <- Sys.getenv("POVERTY_API_KEY")
  skip_if(api_key == "", "POVERTY_API_KEY not set")

  result <- call_authenticated_api(api_key, "NGA")
  expect_true(result$authenticated)
})
```

### Testing Without Secrets — Conditional Mocking

```r
test_that("API client returns correct structure", {
  api_key <- Sys.getenv("POVERTY_API_KEY")

  if (api_key == "") {
    # CI/local without credentials: mock the response
    local_mocked_bindings(
      perform_request = function(...) {
        list(status = 200L, data = data.table(country = "NGA", headcount = 0.40))
      }
    )
  }

  result <- call_api("NGA", 2023)
  expect_named(result, c("country", "headcount"))
})
```

**Never commit secrets:**
- Add credential files to `.gitignore`
- Provide example config: `test_config.yml.example`
- Use environment variables in CI/CD pipelines

## Custom Expectations

### Simple Custom Expectations

```r
# tests/testthat/helper-expectations.R

expect_valid_survey <- function(dt) {
  expect_s3_class(dt, "data.table")
  expect_true(all(dt$welfare > 0),  info = "welfare must be positive")
  expect_false(anyNA(dt$weight),    info = "weights must not contain NAs")
  expect_true(all(dt$weight > 0),   info = "weights must be positive")
}

expect_valid_fgt <- function(result, alpha = 0L) {
  expect_s3_class(result, "data.table")
  col <- paste0("fgt", alpha)
  expect_true(col %in% names(result), info = paste(col, "column missing"))
  expect_true(all(result[[col]] >= 0 & result[[col]] <= 1),
              info = paste(col, "must be in [0, 1]"))
}

expect_no_missing_values <- function(dt, cols = names(dt)) {
  for (col in cols) {
    expect_false(anyNA(dt[[col]]),
                 info = paste("NA values found in column:", col))
  }
}
```

### Complex Custom Expectations (`quasi_label`)

```r
expect_sorted_by <- function(dt, col, decreasing = FALSE) {
  act <- quasi_label(rlang::enquo(dt))
  sorted_vals <- sort(dt[[col]], decreasing = decreasing)
  expect(
    isTRUE(all.equal(dt[[col]], sorted_vals)),
    sprintf("%s is not sorted by '%s' (decreasing = %s)",
            act$lab, col, decreasing)
  )
  invisible(act$val)
}
```

## State Inspection

Detect unintended global state changes between tests:

```r
# tests/testthat/setup-state.R
set_state_inspector(function() {
  list(
    options     = options(),
    env_vars    = Sys.getenv(),
    search_path = search()
  )
})
```

testthat will warn if any state changes between tests, surfacing hidden side effects.

## Testing Edge Cases

### Boundary Conditions

```r
test_that("handles boundary welfare values", {
  expect_no_error(compute_fgt(data.table(welfare = 0,   weight = 1), line = 1))
  expect_no_error(compute_fgt(data.table(welfare = Inf, weight = 1), line = 1))
  expect_true(is.nan(compute_fgt(data.table(welfare = NaN, weight = 1), line = 1)$fgt0))
})
```

### Empty Inputs

```r
test_that("handles empty inputs gracefully", {
  empty_dt <- data.table(welfare = numeric(), weight = numeric())
  result <- compute_fgt(empty_dt, line = 1.90, alpha = 0)
  expect_equal(nrow(result), 0L)
})
```

### Type Validation

```r
test_that("validates input types", {
  expect_error(compute_fgt("not a data.table"), class = "type_error")
  expect_error(compute_fgt(list(welfare = 1)),  class = "type_error")
  expect_no_error(compute_fgt(new_survey_dt()))
})
```

## Parallel Testing

Enable parallel test execution:

```
# In DESCRIPTION:
Config/testthat/parallel: true
```

**Requirements for parallel-safe tests:**
- Tests must be independent — no shared mutable state
- Use `local_*()` functions for all side effects (options, env vars, files)
- Snapshot tests work correctly in parallel (testthat 3.2.0+)

## Test Performance

```r
# Find slow tests
devtools::test(reporter = "slow")

# Detect test ordering dependencies
devtools::test(shuffle = TRUE)
```

If tests fail when shuffled, they have unintended dependencies on execution order — fix by making each test fully self-contained.

## CRAN-Specific Requirements

### Time Limits

Tests must complete in under 1 minute on CRAN:

```r
test_that("expensive computation works", {
  skip_on_cran()  # takes ~2 minutes

  result <- full_bootstrap(new_survey_dt(n = 10000L), reps = 1000L)
  expect_s3_class(result, "data.table")
})
```

### File System Discipline

> See [fixtures.md — File System Discipline](fixtures.md#file-system-discipline) for the correct temp-dir pattern using `withr::local_tempfile()`.

### No External Dependencies

```r
test_that("network-dependent test", {
  skip_on_cran()
  skip_if_offline()
  # network/system calls here
})
```

### Numeric Precision Across Platforms

```r
# Good: tolerant to floating-point differences
expect_equal(result$headcount, 0.3456, tolerance = 1e-4)

# Bad: fails on platforms with different floating-point behavior
expect_identical(result$headcount, 0.3456)
```

## Debugging Failed Tests

### Interactive Debugging

```r
test_that("problematic calculation", {
  browser()  # pauses execution here
  dt <- new_survey_dt()
  result <- compute_fgt(dt, line = 1.90)
  expect_equal(result$fgt0, expected_value)
})
```

### Print Debugging

```r
test_that("inspect intermediate values", {
  dt <- prepare_welfare_data(raw_dt)
  print(str(dt))          # visible when test fails
  print(head(dt))

  result <- compute_fgt(dt, line = 1.90)
  print(result)

  expect_valid_fgt(result)
})
```

### Capture Output for Inspection

```r
test_that("inspect all messages", {
  msgs <- capture_messages({
    result <- run_pipeline(dt)
  })
  print(msgs)  # see all messages when test fails
  expect_match(msgs, "Processing complete")
})
```

## Testing Flaky Code

```r
test_that("network call succeeds eventually", {
  result <- try_again(
    times = 3,
    {
      response <- make_network_request()
      expect_equal(response$status, 200L)
      response
    }
  )
  expect_type(result, "list")
})
```

For timing-sensitive tests, use `skip_on_cran()` and mark them explicitly in the test name.
