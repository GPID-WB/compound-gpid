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

# NULL and length
expect_null(result)
expect_length(vec, 5)

# Pattern matching
expect_match(string, "pattern")
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
```

## Snapshot Testing

```r
test_that("summary output is stable", {
  result <- generate_summary(test_data)
  expect_snapshot(result)
})
```

## Running Tests

```r
devtools::test()              # Run all tests
devtools::test_active_file()  # Run tests in current file
testthat::test_file("tests/testthat/test-cleaning.R")  # Run specific file
```
