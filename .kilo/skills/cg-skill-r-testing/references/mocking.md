# Mocking in testthat

Mocking temporarily replaces function implementations during testing, enabling tests when dependencies are unavailable or impractical (databases, APIs, file systems, expensive computations). All data construction uses **data.table**.

## Core Mocking Functions

### `local_mocked_bindings()`

Replace function implementations within a test scope — automatically restored after the test:

```r
test_that("processes result correctly", {
  local_mocked_bindings(
    get_records = function(id) data.table(id = id, value = 42, group = "a")
  )
  result <- process_records(123)
  expect_equal(result$value, 42)
})
```

**Package-scoped mocking** — mock a function from another package:

```r
test_that("handles external package function", {
  local_mocked_bindings(
    read_dta = function(path, ...) data.table(id = 1L, welfare = 100),
    .package = "haven"
  )
  result <- load_survey("dummy.dta")
  expect_s3_class(result, "data.table")
})
```

### `with_mocked_bindings()`

Mock for a specific code block (not the full test):

```r
test_that("falls back gracefully on API failure", {
  result <- with_mocked_bindings(
    fetch_api = function(...) stop("Network error"),
    {
      tryCatch(
        get_data(),
        error = function(e) data.table(id = integer(), value = numeric())
      )
    }
  )
  expect_equal(nrow(result), 0L)
})
```

## S3 Method Mocking

> Requires **testthat ≥ 3.2.2**. On older versions, use `local_mocked_bindings()` targeting the method dispatch.

```r
test_that("custom print method is used", {
  local_mocked_s3_method(
    print, "myclass",
    function(x, ...) cat("Mocked output\n")
  )
  obj <- structure(list(), class = "myclass")
  expect_output(print(obj), "Mocked output")
})
```

## R6 Class Mocking

testthat has no built-in R6 mock helper. Use **dependency injection** instead — pass the mock instance directly to the function under test:

```r
# Preferred: dependency injection
test_that("processes query result correctly", {
  MockDB <- R6::R6Class("MockDB",
    public = list(
      query = function(sql) data.table(id = 1:3, result = letters[1:3])
    )
  )
  db <- MockDB$new()
  result <- process_records(db)  # function accepts db as parameter
  expect_equal(nrow(result), 3L)
})
```

If you need to intercept `ClassName$new()` itself, use `local_mocked_bindings()` on the constructor in its package:

```r
test_that("constructor is replaced during test", {
  MockDB <- R6::R6Class("MockDB",
    public = list(query = function(sql) data.table(id = 1L, val = 99))
  )
  local_mocked_bindings(
    Database = MockDB,
    .package = "yourpkg"
  )
  result <- create_and_query()  # internally calls Database$new()
  expect_equal(result$val, 99)
})
```

## Common Mocking Patterns

### Database Connections (DBI)

```r
test_that("database query returns expected structure", {
  local_mocked_bindings(
    dbConnect  = function(...) list(connected = TRUE),
    dbGetQuery = function(conn, sql) {
      data.table(id = 1:3, country = c("NGA", "ETH", "KEN"), welfare = c(100, 200, 300))
    }
  )
  result <- fetch_from_db("SELECT * FROM welfare")
  expect_equal(nrow(result), 3)
  expect_named(result, c("id", "country", "welfare"))
})
```

### API Calls (httr2)

Use `httr2::with_mocked_responses()` (httr2 ≥ 1.0.0) — the purpose-built mock mechanism, more stable than low-level binding patches:

```r
test_that("API client handles 200 response", {
  httr2::with_mocked_responses(
    function(req) httr2::response_json(body = list(data = list(list(id = 1, value = 42)))),
    {
      result <- call_api("NGA", 2023)
      expect_equal(result$data[[1]]$value, 42)
    }
  )
})
```

### File System Operations

```r
test_that("file processing handles content correctly", {
  local_mocked_bindings(
    file.exists = function(path) TRUE,
    readLines   = function(path, ...) c("header", "row1", "row2")
  )
  result <- process_file("dummy.csv")
  expect_equal(length(result), 3L)
})
```

### Random Number Generation (Deterministic Mocks)

```r
test_that("sampling function produces expected output when mocked", {
  local_mocked_bindings(
    runif = function(n, ...) rep(0.5, n),
    rnorm = function(n, ...) rep(0.0, n)
  )
  result <- bootstrap_estimate(n = 10)
  expect_equal(result$se, 0)
})
```

### Verify Mock Was Called

```r
test_that("fetch is called exactly once", {
  calls <- list()
  local_mocked_bindings(
    fetch_records = function(...) {
      calls <<- append(calls, list(list(...)))
      data.table(id = 1L, value = 100)
    }
  )
  process_data("NGA")
  expect_length(calls, 1L)
  expect_equal(calls[[1]]$country, "NGA")
})
```

## Advanced Mocking Packages

### webfakes — Fake HTTP Servers

Run a real in-memory HTTP server for integration testing:

```r
test_that("API client handles paginated response", {
  app <- webfakes::new_app()
  app$get("/records", function(req, res) {
    res$send_json(list(
      data = list(list(id = 1, value = 100), list(id = 2, value = 200)),
      next_page = NULL
    ))
  })
  web <- webfakes::local_app_process(app)

  result <- fetch_all_records(web$url("/records"))
  expect_equal(nrow(result), 2L)
})
```

### httptest2 — Record and Replay

Record real HTTP interactions for later replay:

```r
test_that("API returns expected structure", {
  # First run records real response; subsequent runs replay it
  httptest2::with_mock_dir("fixtures/api-responses", {
    result <- call_real_api("NGA", 2023)
    expect_named(result, c("country", "year", "headcount"))
  })
})
```

## Mocking Best Practices

**Mock at the right level:**
- Mock external dependencies (APIs, databases, file I/O) — not internal package functions
- Prefer real fixtures (static `.rds`/`.csv` files) when the data is stable
- Use webfakes or httptest2 for full HTTP integration testing rather than mocking individual httr2 functions

**Prefer real fixtures when possible:**
```r
# Better: use a static fixture
result <- fread(test_path("fixtures", "api-response.csv"))

# Use mocking when: fixture creation requires live credentials or is expensive
local_mocked_bindings(...)
```

**Document what's being mocked and why:**
```r
test_that("handles unavailable authentication service", {
  # Mock the external auth service — unavailable in test environment
  local_mocked_bindings(
    auth_check = function(token) list(valid = TRUE, user = "test")
  )
  result <- protected_endpoint("fake-token")
  expect_equal(result$status, "ok")
})
```

## Migration from Deprecated Functions

| Deprecated | Modern |
|---|---|
| `with_mock(pkg::func = function(...) "x")` | `local_mocked_bindings(func = function(...) "x", .package = "pkg")` |
| `mockr::local_mock()` | `local_mocked_bindings()` |

`local_mocked_bindings()` works with byte-compiled code and is reliable across platforms; `with_mock()` does not.
