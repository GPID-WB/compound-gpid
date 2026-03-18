# Testing with testthat

## Project Setup

```r
# Initialize testing infrastructure
usethis::use_testthat()

# Create a test file for a source file
usethis::use_test("module_name")
```

## File Structure

```
tests/
├── testthat/
│   ├── test-cleaning.R       # Tests for R/cleaning.R
│   ├── test-analysis.R       # Tests for R/analysis.R
│   ├── test-utils.R          # Tests for R/utils.R
│   └── fixtures/
│       └── sample_data.csv   # Small test data files
└── testthat.R                # Test runner
```

## Test Structure

```r
test_that("function does expected thing with normal input", {
  # Arrange
  input_dt <- data.table(id = 1:3, value = c(10, 20, 30))

  # Act
  result <- my_function(input_dt)

  # Assert
  expect_equal(nrow(result), 3)
  expect_equal(result$computed, c(100, 200, 300))
})
```

## Assertion Functions

```r
# Equality
expect_equal(actual, expected)            # uses tolerance for numerics
expect_identical(actual, expected)        # exact match

# Logical
expect_true(condition)
expect_false(condition)

# Errors and warnings
expect_error(bad_function(), "expected message")
expect_warning(warn_function(), "expected warning")
expect_message(msg_function(), "expected message")

# Class and type
expect_s3_class(obj, "data.table")
expect_type(x, "double")

# NULL
expect_null(result)

# Length
expect_length(vec, 5)

# Pattern matching
expect_match(string, "pattern")

# Numeric tolerance
expect_equal(computed_gini, 0.42, tolerance = 1e-4)
```

## Testing data.table

```r
test_that("join produces expected result", {
  dt_a <- data.table(id = 1:3, value_a = c("x", "y", "z"))
  dt_b <- data.table(id = 2:4, value_b = c(10, 20, 30))

  result <- dt_b[dt_a, on = "id"]

  expect_equal(nrow(result), 3)
  expect_true(is.na(result[id == 1, value_b]))
  expect_equal(result[id == 2, value_b], 10)
})

test_that("assignment by reference modifies in place", {
  dt <- data.table(x = 1:3)
  dt[, y := x * 2]

  expect_true("y" %in% names(dt))
  expect_equal(dt$y, c(2, 4, 6))
})
```

## Temporary Resources with withr

```r
test_that("function writes output file correctly", {
  temp_dir <- withr::local_tempdir()
  output_path <- file.path(temp_dir, "output.csv")

  write_results(data, path = output_path)

  expect_true(file.exists(output_path))
  result <- fread(output_path)
  expect_equal(nrow(result), expected_rows)
})

test_that("function reads from a temporary file", {
  temp_file <- withr::local_tempfile(fileext = ".csv")
  fwrite(data.table(id = 1:3, val = c(10, 20, 30)), temp_file)

  result <- my_read_function(temp_file)
  expect_equal(nrow(result), 3)
})
```

## Edge Case Patterns

```r
test_that("function handles empty data.table", {
  empty_dt <- data.table(id = integer(), value = numeric())
  result <- my_function(empty_dt)
  expect_equal(nrow(result), 0)
})

test_that("function handles NA values", {
  dt_with_na <- data.table(id = 1:3, value = c(1, NA, 3))
  result <- my_function(dt_with_na)
  expect_false(any(is.na(result$computed)))
})

test_that("function errors on invalid input", {
  expect_error(
    my_function("not a data.table"),
    "must be a data.table"
  )
})

test_that("function handles single-row input", {
  dt <- data.table(id = 1, value = 42)
  result <- my_function(dt)
  expect_equal(nrow(result), 1)
})
```

## Snapshot Testing

For complex output that's hard to assert value-by-value:

```r
test_that("summary output is stable", {
  result <- generate_summary(test_data)
  expect_snapshot(result)
})

test_that("error message format is stable", {
  expect_snapshot_error(bad_function(NULL))
})
```

Snapshots are stored in `tests/testthat/_snaps/`. Review changes with `testthat::snapshot_review()`.

## Testing Plumber Endpoints

Add a `make_req()` helper to `tests/testthat/helper.R` (loaded automatically by testthat):

```r
# tests/testthat/helper.R
make_req <- function(method, path, query = list(), body = NULL) {
  query_string <- if (length(query) > 0) {
    paste(names(query), query, sep = "=", collapse = "&")
  } else {
    ""
  }

  body_str <- if (!is.null(body)) jsonlite::toJSON(body, auto_unbox = TRUE) else ""

  plumber::PlumberRequest$new(
    req = list(
      REQUEST_METHOD = method,
      PATH_INFO      = path,
      QUERY_STRING   = query_string,
      HTTP_HOST      = "localhost",
      CONTENT_TYPE   = "application/json",
      rook.input     = list(read_lines = function(...) body_str)
    )
  )
}
```

Then use it in tests:

```r
test_that("GET /health returns status ok", {
  pr <- plumber::pr("plumber.R")

  res <- pr$call(make_req("GET", "/health"))

  expect_equal(res$status, 200L)
  body <- jsonlite::fromJSON(res$body)
  expect_equal(body$status, "ok")
})

test_that("GET /poverty returns 400 for invalid country code", {
  pr <- plumber::pr("plumber.R")

  res <- pr$call(make_req("GET", "/poverty/INVALID/2023"))

  expect_equal(res$status, 400L)
})
```

## Testing httr2 Requests

Use `httr2::with_mocked_responses()` to test HTTP client code without hitting real servers:

```r
test_that("API client handles successful response", {
  mock_response <- function(req) {
    httr2::response(
      status_code = 200,
      headers = list("Content-Type" = "application/json"),
      body = charToRaw('{"data": [1, 2, 3]}')
    )
  }

  result <- httr2::with_mocked_responses(mock_response, {
    fetch_data("NGA", 2023)
  })

  expect_length(result$data, 3)
})

test_that("API client handles 404 gracefully", {
  mock_404 <- function(req) {
    httr2::response(status_code = 404)
  }

  expect_error(
    httr2::with_mocked_responses(mock_404, {
      fetch_data("XXX", 2023)
    }),
    "not found"
  )
})
```

## Test Fixtures

For test data used across multiple test files:

```r
# tests/testthat/helper.R (loaded automatically by testthat)
make_test_survey <- function(n = 100) {
  data.table(
    id      = seq_len(n),
    welfare = rlnorm(n, meanlog = 2, sdlog = 1),
    weight  = runif(n, 0.5, 2.0),
    region  = sample(c("A", "B", "C"), n, replace = TRUE),
    psu     = sample(1:10, n, replace = TRUE),
    stratum = sample(1:5, n, replace = TRUE)
  )
}
```

Use in tests:

```r
test_that("poverty computation returns valid results", {
  dt <- make_test_survey(1000)
  svy <- dt |>
    srvyr::as_survey_design(ids = psu, strata = stratum, weights = weight)

  result <- compute_poverty(svy, poverty_line = 2.15)

  expect_true(result$fgt0 >= 0 && result$fgt0 <= 1)
  expect_true(result$fgt1 >= 0 && result$fgt1 <= result$fgt0)
})
```

## Testing Anti-Patterns

### Test with no assertions

**Wrong:**
```r
test_that("function runs", {
  result <- my_function(data)  # No check — this test ALWAYS passes, even if my_function() errors or returns garbage
})
```

**Right:**
```r
test_that("function returns non-empty data.table", {
  result <- my_function(data)
  expect_s3_class(result, "data.table")
  expect_gt(nrow(result), 0)
})
```

### Test that checks implementation detail, not behaviour

**Wrong:**
```r
test_that("function calls fread internally", {
  # Testing that an internal function is called — fragile
  mockery::expect_called(fread, 1)
})
```

**Right:** Test observable outputs (return value, file written, error raised), not which internal function was used.

### Order-dependent tests

**Wrong:**
```r
# test-analysis.R expects test-cleaning.R to have run first and set dt_global
test_that("step 2 works", {
  result <- step2(dt_global)  # dt_global set by a previous test
  ...
})
```

**Right:** Each test creates its own data in the Arrange phase. Use `helper.R` fixtures for shared setup.

---

## Running Tests

```r
devtools::test()              # Run all tests
devtools::test_active_file()  # Run tests in current file
testthat::test_file("tests/testthat/test-cleaning.R")  # Specific file
```
