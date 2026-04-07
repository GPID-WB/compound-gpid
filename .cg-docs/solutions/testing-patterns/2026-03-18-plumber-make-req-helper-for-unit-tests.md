---
date: 2026-03-18
title: "Plumber endpoint testing: make_req() helper pattern"
category: "testing-patterns"
language: "R"
tags: [plumber, testing, testthat, http, make_req, api, unit-test]
root-cause: "plumber's PlumberRequest$new() requires a raw rook env list; no built-in test helper exists"
severity: "P1"
---

# Plumber Endpoint Testing: make_req() Helper Pattern

## Problem

When writing unit tests for plumber API endpoints using `pr$call()`, there is no built-in
`make_req()` function in plumber. Skill documentation (and many blog posts) reference this helper
without defining it, causing immediate `Error: could not find function "make_req"` when tests run.

A secondary issue: naively implemented helpers accept `query` and `body` parameters but hardcode
`QUERY_STRING = ""` and ignore `body`, so tests that exercise query parameters or POST bodies
silently pass with wrong behaviour.

## Root Cause

Plumber's internal request object (`PlumberRequest`) wraps a Rack/rook-compatible environment
list. Unit tests must construct this env list manually — plumber provides no `test_request()`
convenience function. The correct constructor is `plumber::PlumberRequest$new(req = list(...))`.

## Solution

Add `make_req()` to `tests/testthat/helper.R` (loaded automatically by testthat before all tests):

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

Then in test files:

```r
test_that("GET /health returns 200 ok", {
  pr  <- plumber::pr("plumber.R")
  res <- pr$call(make_req("GET", "/health"))

  expect_equal(res$status, 200L)
  expect_equal(jsonlite::fromJSON(res$body)$status, "ok")
})

test_that("GET /poverty returns 400 for invalid country code", {
  pr  <- plumber::pr("plumber.R")
  res <- pr$call(make_req("GET", "/poverty/INVALID/2023"))

  expect_equal(res$status, 400L)
})

test_that("POST /estimates accepts JSON body", {
  pr   <- plumber::pr("plumber.R")
  res  <- pr$call(make_req("POST", "/estimates", body = list(country = "NGA", year = 2023)))

  expect_equal(res$status, 200L)
})
```

## Prevention

- Always define `make_req()` in `tests/testthat/helper.R`, never inline.
- The `cg-skill-r-technical` reference file ([references/testing-apis.md](../../../.github/skills/cg-skill-r-technical/references/testing-apis.md)) now includes
  this definition in the "Testing Plumber Endpoints" section.
- Never leave `QUERY_STRING = ""` hardcoded when the helper signature accepts a `query` argument —
  silent parameter ignoring is a test anti-pattern.

## Related

- [httpx async ASGI transport pattern](2026-03-17-httpx-async-client-asgi-transport.md) — same
  concept for Python FastAPI: no built-in test client, must construct transport manually
- [`testing-apis.md`](../../../.github/skills/cg-skill-r-technical/references/testing-apis.md) — Plumber endpoint and httr2 mock testing patterns
