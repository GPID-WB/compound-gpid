# BDD-Style Testing with describe() and it()

Behavior-Driven Development testing uses `describe()` and `it()` to create specification-style tests that read like natural language descriptions of behavior. All data construction uses **data.table**.

## When to Use BDD vs Standard Syntax

**Use BDD (`describe`/`it`) when:**
- Documenting intended behavior of new components before implementation
- Testing complex components with multiple related facets (e.g., a calculation pipeline)
- Following test-first development workflows
- A group of tests rely on shared fixture setup in the `describe()` block
- Tests serve as living specification documentation

**Use `test_that()` when:**
- Writing straightforward unit tests for individual functions
- Testing implementation details or internal helpers
- Converting existing tests (no need to change working code)

**Key insight:** "Use `describe()` to verify you implement the right things; use `test_that()` to ensure you do things right."

## Basic BDD Syntax

```r
describe("compute_fgt()", {
  it("computes headcount ratio at given poverty line", {
    dt <- data.table(welfare = c(0.5, 1.0, 1.5, 2.0), weight = rep(1, 4))
    result <- compute_fgt(dt, line = 1.0, alpha = 0)
    expect_equal(result$fgt0, 0.25, tolerance = 1e-10)  # 1 of 4 below line
  })

  it("returns zero FGT when all welfare above line", {
    dt <- data.table(welfare = c(5, 10, 15), weight = rep(1, 3))
    result <- compute_fgt(dt, line = 1.0, alpha = 0)
    expect_equal(result$fgt0, 0)
  })

  it("handles empty data.table")  # pending specification
})
```

Each `it()` block runs in its own environment and supports all testthat expectations.

## Nested Specifications

```r
describe("welfare_pipeline()", {

  describe("input validation", {
    it("rejects NULL welfare column", {
      dt <- data.table(id = 1:3, weight = rep(1, 3))
      expect_error(welfare_pipeline(dt), class = "missing_welfare_error")
    })

    it("rejects negative welfare values", {
      dt <- data.table(welfare = c(1, -5, 3), weight = rep(1, 3))
      expect_error(welfare_pipeline(dt), class = "negative_welfare_error")
    })

    it("rejects zero weights", {
      dt <- data.table(welfare = c(1, 2, 3), weight = c(1, 0, 1))
      expect_error(welfare_pipeline(dt), class = "invalid_weight_error")
    })
  })

  describe("with valid data", {
    it("returns a data.table", {
      dt <- new_survey_dt()
      expect_s3_class(welfare_pipeline(dt), "data.table")
    })

    it("preserves row count", {
      dt <- new_survey_dt(n = 50L)
      result <- welfare_pipeline(dt)
      expect_equal(nrow(result), 50L)
    })

    it("produces non-negative adjusted welfare", {
      dt <- new_survey_dt()
      result <- welfare_pipeline(dt)
      expect_true(all(result$welfare_adj >= 0))
    })
  })

  describe("PPP conversion", {
    it("applies PPP factor correctly", {
      dt <- data.table(welfare = c(100, 200), weight = c(1, 1))
      result <- welfare_pipeline(dt, ppp_factor = 2.0)
      expect_equal(result$welfare_ppp, c(50, 100), tolerance = 1e-10)
    })

    it("errors on missing PPP factor when currency requires it")  # pending
  })
})
```

## Pending Specifications

Mark unimplemented behaviors by omitting the code block:

```r
describe("fgt_decomposition()", {
  it("computes Shapley decomposition", {
    dt <- new_survey_dt()
    result <- fgt_decomposition(dt)
    expect_named(result, c("growth", "redistribution", "total"))
  })

  it("handles unequal group sizes")        # pending
  it("handles single-group data")          # pending
  it("is consistent with fgt2 directly")   # pending
})
```

Pending `it()` blocks appear as SKIPPED in test output, document planned work, and don't cause failures.

## Test-First Workflow with BDD

1. **Write specifications (pending):**

```r
describe("collap_weighted()", {
  it("aggregates by group with weights")
  it("handles missing weights")
  it("preserves non-aggregated columns")
  it("returns data.table with correct key")
})
```

2. **Implement one specification at a time:**

```r
describe("collap_weighted()", {
  it("aggregates by group with weights", {
    dt <- data.table(g = c("a", "a", "b"), y = c(10, 20, 30), w = c(1, 1, 1))
    result <- collap_weighted(dt, group_col = "g", value_col = "y", weight_col = "w")
    expect_equal(result[g == "a"]$y, 15, tolerance = 1e-10)
    expect_equal(result[g == "b"]$y, 30, tolerance = 1e-10)
  })

  it("handles missing weights")              # still pending
  it("preserves non-aggregated columns")     # still pending
  it("returns data.table with correct key") # still pending
})
```

## BDD with Fixtures

Use the same fixture patterns as standard tests — define shared data in the `describe()` scope:

```r
describe("fmean_by_region()", {
  # Shared fixture accessible by all it() blocks in this describe()
  dt <- data.table(
    region = c("Urban", "Urban", "Rural", "Rural"),
    welfare = c(200, 300, 100, 150),
    weight  = c(1, 1, 1, 1)
  )

  it("computes unweighted means by region", {
    result <- fmean_by_region(dt, weighted = FALSE)
    expect_equal(result[region == "Urban"]$mean, 250)
    expect_equal(result[region == "Rural"]$mean, 125)
  })

  it("computes weighted means by region", {
    dt_w <- copy(dt)
    dt_w[region == "Urban", weight := c(1, 3)]
    result <- fmean_by_region(dt_w, weighted = TRUE)
    # Urban: (200*1 + 300*3)/4 = 275
    expect_equal(result[region == "Urban"]$mean, 275, tolerance = 1e-10)
  })
})
```

## BDD with Mocking

```r
describe("fetch_api_data()", {
  describe("on success", {
    it("returns a data.table with expected columns", {
      local_mocked_bindings(
        perform_request = function(...) list(status = 200L,
          body = '{"data": [{"id": 1, "value": 100}]}')
      )
      result <- fetch_api_data("NGA", 2023)
      expect_s3_class(result, "data.table")
      expect_named(result, c("id", "value"))
    })
  })

  describe("on failure", {
    it("returns empty data.table on 404", {
      local_mocked_bindings(
        perform_request = function(...) list(status = 404L, body = "{}")
      )
      result <- fetch_api_data("INVALID", 2023)
      expect_equal(nrow(result), 0L)
    })

    it("errors loudly on 500", {
      local_mocked_bindings(
        perform_request = function(...) list(status = 500L, body = "{}")
      )
      expect_error(fetch_api_data("NGA", 2023), class = "api_server_error")
    })
  })
})
```

## Mixing BDD and Standard Syntax

Both styles can coexist in the same file:

```r
# tests/testthat/test-welfare.R

# BDD for behavioral specifications of the pipeline
describe("welfare_pipeline()", {
  describe("validation", { ... })
  describe("processing", { ... })
})

# Standard syntax for internal utility functions
test_that("ppp_convert() applies factor correctly", {
  expect_equal(ppp_convert(100, factor = 2), 50)
})

test_that("winsorize() clips at specified percentile", {
  dt <- data.table(x = c(1, 2, 3, 4, 100))
  result <- winsorize(dt$x, p = 0.95)
  expect_lt(max(result), 100)
})
```

**Guidelines:** use BDD for behavioral specs, `test_that()` for implementation details, keep related tests in the same style within a section, don't nest `test_that()` inside `describe()`.

## File Organization with BDD

```r
# tests/testthat/test-pipeline.R
describe("Pipeline", {
  describe("load_data()", { ... })
  describe("clean_data()", { ... })
  describe("compute_poverty()", { ... })
  describe("export_results()", { ... })
})
```
