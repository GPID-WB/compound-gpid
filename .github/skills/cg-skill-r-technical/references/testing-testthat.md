# Testing with testthat

## Setup

```r
usethis::use_testthat()
usethis::use_test("module_name")
```

## Test Structure

```r
test_that("function does expected thing", {
  input_dt <- data.table(id = 1:3, value = c(10, 20, 30))
  result <- my_function(input_dt)
  expect_equal(nrow(result), 3)
  expect_equal(result$computed, c(100, 200, 300))
})
```

## Assertions

```r
expect_equal(actual, expected)       # tolerance for numerics
expect_identical(actual, expected)   # exact
expect_true(condition)
expect_false(condition)
expect_error(f(), "message")
expect_warning(f(), "warning")
expect_s3_class(obj, "data.table")
expect_type(x, "double")
expect_null(result)
expect_length(vec, 5)
expect_match(string, "pattern")
expect_equal(x, 0.42, tolerance = 1e-4)
```

## Testing collapse Output

```r
test_that("weighted mean matches expected value", {
  dt <- data.table(y = c(1, 2, 3), w = c(1, 2, 1))
  result <- fmean(dt$y, w = dt$w)
  # (1*1 + 2*2 + 3*1) / (1+2+1) = 8/4 = 2
  expect_equal(result, 2.0)
})

test_that("collap aggregation produces correct groups", {
  dt <- data.table(g = c("a", "a", "b"), y = c(10, 20, 30), w = c(1, 1, 1))
  result <- collap(dt, ~ g, fmean, w = ~ w, cols = "y")
  expect_equal(nrow(result), 2)
  expect_equal(result[g == "a"]$y, 15)
  expect_equal(result[g == "b"]$y, 30)
})

test_that("fwithin centers to zero within groups", {
  dt <- data.table(g = c("a", "a", "b", "b"), y = c(10, 20, 100, 200))
  centered <- fwithin(dt$y, g = dt$g)
  # Within-group means should be 0
  expect_equal(fmean(centered, g = dt$g), c(0, 0), tolerance = 1e-10)
})

test_that("GRP object produces same result as raw grouping", {
  dt <- data.table(g = c("a", "a", "b"), y = c(10, 20, 30))
  grp <- GRP(dt, ~ g)
  expect_equal(
    fmean(dt$y, g = dt$g),
    fmean(dt$y, g = grp)
  )
})

test_that("TRA replace fills group statistics correctly", {
  dt <- data.table(g = c("a", "a", "b"), y = c(10, 20, 30))
  replaced <- fmean(dt$y, g = dt$g, TRA = "replace")
  expect_equal(replaced, c(15, 15, 30))
})

test_that("panel operations with findex_by work", {
  dt <- data.table(id = c(1, 1, 2, 2), year = c(2020, 2021, 2020, 2021),
                   y = c(10, 12, 20, 25))
  pdt <- findex_by(dt, id, year)
  lagged <- flag(pdt$y, 1)
  # First obs per id should be NA (no lag available)
  expect_true(is.na(lagged[1]))
  expect_true(is.na(lagged[3]))
  expect_equal(lagged[2], 10)
  expect_equal(lagged[4], 20)
})
```

## Testing data.table

```r
test_that("join produces expected result", {
  dt_a <- data.table(id = 1:3, val = c("x", "y", "z"))
  dt_b <- data.table(id = 2:4, num = c(10, 20, 30))
  result <- dt_b[dt_a, on = "id"]
  expect_equal(nrow(result), 3)
  expect_true(is.na(result[id == 1, num]))
  expect_equal(result[id == 2, num], 10)
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
test_that("writes file correctly", {
  temp_dir <- withr::local_tempdir()
  path <- file.path(temp_dir, "out.csv")
  fwrite(data, path)
  expect_true(file.exists(path))
  result <- fread(path)
  expect_equal(nrow(result), expected_rows)
})
```

## Edge Cases

```r
test_that("handles empty data.table", {
  empty <- data.table(id = integer(), value = numeric())
  result <- my_function(empty)
  expect_equal(nrow(result), 0)
})

test_that("handles NA values with collapse", {
  dt <- data.table(id = 1:3, value = c(1, NA, 3))
  # collapse default na.rm = TRUE
  expect_equal(fmean(dt$value), 2)
  expect_equal(fnobs(dt$value), 2L)
})

test_that("errors on invalid input", {
  expect_error(my_function("not a data.table"), "must be")
})
```

## Testing Plumber Endpoints

```r
test_that("GET /health returns ok", {
  pr <- plumber::pr("plumber.R")
  res <- pr$call(make_req("GET", "/health"))
  expect_equal(res$status, 200L)
  body <- jsonlite::fromJSON(res$body)
  expect_equal(body$status, "ok")
})

test_that("GET /poverty returns 400 for bad country code", {
  pr <- plumber::pr("plumber.R")
  res <- pr$call(make_req("GET", "/poverty/INVALID/2023"))
  expect_equal(res$status, 400L)
})
```

## Testing httr2 with Mocks

```r
test_that("API client handles success", {
  mock <- function(req) {
    httr2::response(status_code = 200,
      headers = list("Content-Type" = "application/json"),
      body = charToRaw('{"data": [1, 2, 3]}'))
  }
  result <- httr2::with_mocked_responses(mock, { fetch_data("NGA", 2023) })
  expect_length(result$data, 3)
})
```

## Test Fixtures

```r
# tests/testthat/helper.R (loaded automatically)
make_test_survey <- function(n = 100) {
  data.table(
    id = seq_len(n), welfare = rlnorm(n, 2, 1),
    weight = runif(n, 0.5, 2), region = sample(c("A", "B"), n, TRUE),
    psu = sample(1:10, n, TRUE), stratum = sample(1:5, n, TRUE)
  )
}
```

## Snapshot Testing

```r
test_that("summary output is stable", {
  result <- generate_summary(test_data)
  expect_snapshot(result)
})
```

## Running

```r
devtools::test()
devtools::test_active_file()
testthat::test_file("tests/testthat/test-cleaning.R")
```
