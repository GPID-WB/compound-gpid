# Test Fixtures and Data Management

Test fixtures arrange the environment into a known state. testthat provides several approaches for managing test data and state. All data construction examples use **data.table** and **collapse**; use `fwrite`/`fread` instead of `write.csv`/`read.csv`.

## Fixture Approaches

### 1. Constructor Helper Functions (Preferred)

Create reusable test objects on demand. Define in `helper-constructors.R` or inside the test file:

```r
# tests/testthat/helper-constructors.R
new_survey_dt <- function(n = 100L, seed = 42L) {
  set.seed(seed)
  data.table(
    id      = seq_len(n),
    welfare = rlnorm(n, meanlog = 2, sdlog = 1),
    weight  = runif(n, 0.5, 2),
    region  = sample(c("Urban", "Rural"), n, replace = TRUE),
    psu     = sample(seq_len(10), n, replace = TRUE),
    stratum = sample(seq_len(5), n, replace = TRUE)
  )
}

new_group_dt <- function(groups = c("a", "b", "c"), n_per_group = 10L, seed = 42L) {
  set.seed(seed)
  data.table(
    group = rep(groups, each = n_per_group),
    value = rnorm(length(groups) * n_per_group),
    w     = runif(length(groups) * n_per_group, 0.5, 2)
  )
}
```

**Use when:** data is cheap to create, multiple tests need similar but not identical data, data should vary between tests.

```r
test_that("fmean() computes correct weighted group means", {
  dt <- new_group_dt()
  result <- collap(dt, ~ group, fmean, w = ~ w, cols = "value")
  expect_equal(nrow(result), 3L)
  expect_s3_class(result, "data.table")
})
```

### 2. Local Functions with Cleanup

Handle side effects using `withr::defer()` — automatic cleanup after the test:

```r
local_temp_csv <- function(dt, pattern = "test", env = parent.frame()) {
  path <- withr::local_tempfile(pattern = pattern, fileext = ".csv",
                                .local_envir = env)
  fwrite(dt, path)
  path
}

local_temp_rds <- function(obj, env = parent.frame()) {
  path <- withr::local_tempfile(fileext = ".rds", .local_envir = env)
  saveRDS(obj, path)
  path
}

test_that("fread() round-trips CSV correctly", {
  dt   <- new_survey_dt(n = 20L)
  path <- local_temp_csv(dt)
  result <- fread(path)
  expect_equal(result, dt)
})
```

**Use when:** tests create temporary files or connections, setup requires multiple steps, cleanup logic is non-trivial.

### 3. Static Fixture Files

Store pre-created data in `tests/testthat/fixtures/`. Access with `test_path()` — always portable, never relative paths:

```r
test_that("poverty calculation matches reference output", {
  dt       <- readRDS(test_path("fixtures", "survey-sample.rds"))
  expected <- readRDS(test_path("fixtures", "expected-poverty-rates.rds"))
  result   <- compute_fgt(dt, line = 1.90)
  expect_equal(result, expected, tolerance = 1e-6)
})
```

**Create fixtures interactively (run once):**

```r
dt <- new_survey_dt(n = 500L)
saveRDS(dt, "tests/testthat/fixtures/survey-sample.rds")

expected <- compute_fgt(dt, line = 1.90)
saveRDS(expected, "tests/testthat/fixtures/expected-poverty-rates.rds")
```

**Use when:** data is expensive to create, represents real-world edge cases, or multiple tests need identical data.

## Helper Files

Files starting with `helper-` are automatically sourced before all tests run:

```r
# tests/testthat/helper-constructors.R

# ---- Data constructors ----

new_survey_dt <- function(n = 100L, seed = 42L) { ... }

new_panel_dt <- function(n_units = 10L, n_years = 5L, seed = 42L) {
  set.seed(seed)
  CJ(unit = seq_len(n_units), year = 2015L + seq_len(n_years))[,
    value := rnorm(.N)]
}
```

## Setup Files

Files starting with `setup-` run during `R CMD check` and `devtools::test()`, but not during `devtools::load_all()`:

```r
# tests/testthat/setup-options.R

# Set package-wide test options — restored after suite completes
withr::local_options(
  list(
    datatable.verbose = FALSE,
    warn             = 1L   # warn immediately, not at end
  ),
  .local_envir = teardown_env()
)
```

**Use setup files for:** package-wide test options, environment variable configuration, one-time expensive setup, suite initialization.

## File System Discipline

**Always write to temp directories — never to the working directory or package folder:**

```r
test_that("export function writes correct output", {
  dt   <- new_survey_dt(n = 20L)
  dir  <- withr::local_tempdir()
  path <- file.path(dir, "output.csv")

  export_survey(dt, path)

  expect_true(file.exists(path))
  result <- fread(path)
  expect_equal(nrow(result), 20L)
})
```

**Always use `test_path()` for fixture access — never relative paths:**

```r
# Good — works in all contexts (interactive, R CMD check, CI)
dt <- readRDS(test_path("fixtures", "survey-sample.rds"))

# Bad — breaks under R CMD check
dt <- readRDS("fixtures/survey-sample.rds")
```

## Database Fixtures

### In-Memory SQLite

```r
test_that("welfare query returns correct aggregation", {
  con <- DBI::dbConnect(RSQLite::SQLite(), ":memory:")
  withr::defer(DBI::dbDisconnect(con))

  DBI::dbExecute(con, "CREATE TABLE welfare (id INTEGER, country TEXT, value REAL, weight REAL)")
  DBI::dbExecute(con, "INSERT INTO welfare VALUES
    (1, 'NGA', 100.0, 1.5),
    (2, 'NGA', 200.0, 2.0),
    (3, 'ETH', 150.0, 1.0)")

  result <- query_welfare_mean(con, "NGA")
  expect_equal(result$mean_welfare, fmean(c(100, 200), w = c(1.5, 2.0)),
               tolerance = 1e-10)
})
```

### Fixture SQL Scripts

```r
test_that("complex aggregation query works", {
  con <- DBI::dbConnect(RSQLite::SQLite(), ":memory:")
  withr::defer(DBI::dbDisconnect(con))

  schema <- readLines(test_path("fixtures", "sql", "schema.sql"))
  DBI::dbExecute(con, paste(schema, collapse = "\n"))

  result <- run_aggregation(con)
  expect_s3_class(result, "data.frame")
  expect_gt(nrow(result), 0L)
})
```

## Fixture Organization

```
tests/testthat/
├── fixtures/
│   ├── data/                  # Input survey and reference data
│   │   ├── survey-sample.rds
│   │   └── edge-case-zeros.rds
│   ├── expected/              # Pre-computed expected outputs
│   │   ├── poverty-rates.rds
│   │   └── gini-coefficients.rds
│   ├── sql/                   # Database schemas
│   │   └── schema.sql
│   └── README.md              # Document fixture origins
├── helper-constructors.R      # data.table constructors
├── helper-expectations.R      # Custom expect_* functions
├── setup-options.R            # Suite-wide options
└── test-*.R                   # Test files
```

**Document fixture origins in `fixtures/README.md`:**

```markdown
# Fixtures

## survey-sample.rds
Created 2026-04-06 from synthetic data (new_survey_dt(n=500, seed=42)).
Contains 500 rows with welfare, weight, region, psu, stratum.

## poverty-rates.rds
Pre-computed FGT indices at $1.90/day for survey-sample.rds.
Created with: compute_fgt(survey_sample, line = 1.90)
```

## Best Practices

**Keep fixtures small and deterministic:**
```r
# Good: no randomness
dt <- data.table(
  group = c("a", "a", "b"),
  value = c(10, 20, 30),
  w     = c(1, 1, 1)
)

# Acceptable: seeded randomness
set.seed(42)
dt <- data.table(value = rnorm(100))
```

**Use constructors for data variation across tests; static files for fixed reference data.**

**Commit fixture files to version control** — they are part of your test suite.
