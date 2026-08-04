# Testing APIs — Plumber and httr2

Patterns for testing plumber REST endpoints and httr2 HTTP client code. This reference belongs in `cg-skill-r-technical` because the testing patterns are tightly coupled to the technologies (plumber, httr2). For general R testing patterns (testthat, fixtures, mocking, snapshots), load `cg-skill-r-testing`.

## Testing Plumber Endpoints

Define the `make_req()` helper in `tests/testthat/helper.R` — loaded automatically before all tests.

```r
# tests/testthat/helper.R
make_req <- function(method, path, query = list(), body = NULL) {
  query_string <- if (length(query) > 0) {
    paste(names(query), query, sep = "=", collapse = "&")
  } else {
    ""
  }

  body_str <- if (!is.null(body)) {
    jsonlite::toJSON(body, auto_unbox = TRUE)
  } else {
    ""
  }

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

> **Why `rook.input`?** Plumber reads POST bodies via the rook interface. Omitting `rook.input` or hardcoding `QUERY_STRING = ""` causes body parameters to be silently ignored, producing false-passing tests.

### GET Endpoint Tests

```r
test_that("GET /health returns 200 with ok status", {
  pr  <- plumber::pr("plumber.R")
  res <- pr$call(make_req("GET", "/health"))
  expect_equal(res$status, 200L)
  body <- jsonlite::fromJSON(res$body)
  expect_equal(body$status, "ok")
})

test_that("GET /poverty returns 400 for invalid country code", {
  pr  <- plumber::pr("plumber.R")
  res <- pr$call(make_req("GET", "/poverty/INVALID/2023"))
  expect_equal(res$status, 400L)
})

test_that("GET /stats accepts valid query parameters", {
  pr  <- plumber::pr("plumber.R")
  res <- pr$call(make_req("GET", "/stats",
                           query = list(country = "NGA", year = "2023")))
  expect_equal(res$status, 200L)
  body <- jsonlite::fromJSON(res$body)
  expect_type(body, "list")
})
```

### POST Endpoint Tests

```r
test_that("POST /estimates accepts JSON body and returns result", {
  pr  <- plumber::pr("plumber.R")
  res <- pr$call(make_req("POST", "/estimates",
                           body = list(country = "NGA", year = 2023)))
  expect_equal(res$status, 200L)
  body <- jsonlite::fromJSON(res$body)
  expect_true("headcount" %in% names(body))
})

test_that("POST /estimates returns 422 for missing required fields", {
  pr  <- plumber::pr("plumber.R")
  res <- pr$call(make_req("POST", "/estimates",
                           body = list(country = "NGA")))  # missing year
  expect_equal(res$status, 422L)
})
```

### Testing Response Bodies

```r
test_that("GET /survey returns data.table-compatible JSON structure", {
  pr   <- plumber::pr("plumber.R")
  res  <- pr$call(make_req("GET", "/survey", query = list(country = "NGA")))
  expect_equal(res$status, 200L)

  body <- jsonlite::fromJSON(res$body, simplifyDataFrame = FALSE)
  expect_type(body$data, "list")
  expect_gt(length(body$data), 0L)
})
```

### Reusing the Router Across Tests

Constructing `plumber::pr()` in every test is slow. For test files covering many endpoints, build the router once in a helper:

```r
# tests/testthat/helper.R (extend the existing helper)
build_router <- function() {
  plumber::pr("plumber.R")
}
```

Then in tests:

```r
test_that("multiple endpoint tests share one router", {
  pr <- build_router()

  res_health  <- pr$call(make_req("GET", "/health"))
  res_version <- pr$call(make_req("GET", "/version"))

  expect_equal(res_health$status, 200L)
  expect_equal(res_version$status, 200L)
})
```

## Testing httr2 HTTP Clients

### Mocking with `with_mocked_responses()`

```r
test_that("API client handles successful 200 response", {
  mock <- function(req) {
    httr2::response(
      status_code = 200L,
      headers     = list("Content-Type" = "application/json"),
      body        = charToRaw('{"data": [{"id": 1, "value": 42.0}]}')
    )
  }
  result <- httr2::with_mocked_responses(mock, {
    fetch_data("NGA", 2023)
  })
  expect_equal(result$data[[1]]$value, 42.0)
})

test_that("API client retries on 503", {
  attempt <- 0L
  mock <- function(req) {
    attempt <<- attempt + 1L
    if (attempt < 3L) {
      httr2::response(status_code = 503L, headers = list(), body = raw(0))
    } else {
      httr2::response(
        status_code = 200L,
        headers     = list("Content-Type" = "application/json"),
        body        = charToRaw('{"status": "ok"}')
      )
    }
  }
  result <- httr2::with_mocked_responses(mock, {
    fetch_with_retry("NGA", max_tries = 3L)
  })
  expect_equal(attempt, 3L)
  expect_equal(result$status, "ok")
})

test_that("API client errors loudly on 404", {
  mock <- function(req) {
    httr2::response(status_code = 404L, headers = list(), body = raw(0))
  }
  expect_error(
    httr2::with_mocked_responses(mock, { fetch_data("INVALID", 2023) }),
    class = "httr2_http_404"
  )
})
```

### Testing Pagination

```r
test_that("paginated client collects all pages", {
  page <- 0L
  mock <- function(req) {
    page <<- page + 1L
    if (page == 1L) {
      httr2::response(200L,
        headers = list("Content-Type" = "application/json"),
        body    = charToRaw('{"data": [1, 2], "next_page": 2}'))
    } else {
      httr2::response(200L,
        headers = list("Content-Type" = "application/json"),
        body    = charToRaw('{"data": [3, 4], "next_page": null}'))
    }
  }
  result <- httr2::with_mocked_responses(mock, {
    fetch_all_pages(base_url = "https://api.example.com/data")
  })
  expect_equal(result, c(1, 2, 3, 4))
})
```
