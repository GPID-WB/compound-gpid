# Snapshot Testing

Snapshot tests record expected output in human-readable files rather than inline code. They are ideal for:

- Complex output that's difficult to verify programmatically
- User-facing messages, warnings, and errors
- Mixed output types (printed text + messages + warnings)
- Printed `data.table` or collapse-summary output
- Text with complex formatting or variable-width columns

## Basic Usage

```r
test_that("error message is informative", {
  expect_snapshot(error = TRUE, {
    validate_input(NULL)
  })
})

test_that("summary output is stable", {
  result <- compute_summary(new_survey_dt())
  expect_snapshot(result)
})
```

The first run creates `tests/testthat/_snaps/{test-file}.md` containing the captured output.

## Snapshot Workflow

```r
devtools::test()                    # Creates new snapshots on first run

testthat::snapshot_review("foofy")  # Review changes interactively
testthat::snapshot_accept("foofy")  # Accept reviewed changes
testthat::snapshot_reject("foofy")  # Reject and revert

testthat::snapshot_download_gh()    # Download snapshots from GitHub CI
```

**CI behavior (testthat 3.3.0+):** New snapshots that don't exist yet fail the test in CI. Always create and commit snapshots locally first.

## Snapshot Types

### Output Snapshots

Capture printed output, messages, warnings, and errors:

```r
test_that("aggregation prints summary correctly", {
  dt <- data.table(
    group = c("a", "a", "b"),
    value = c(10, 20, 30),
    w     = c(1, 1, 1)
  )
  expect_snapshot({
    print(collap(dt, ~ group, fmean, w = ~ w, cols = "value"))
    message("Aggregation complete: 2 groups")
  })
})
```

### Value Snapshots

Capture the structure of R objects:

```r
test_that("column structure is correct after join", {
  result <- merge(dt_a, dt_b, by = "id", all.x = TRUE)
  expect_snapshot(str(result))
})
```

### Error Snapshots

Capture error messages including call information:

```r
test_that("validation errors are clear", {
  expect_snapshot(error = TRUE, {
    validate_welfare(NULL)
    validate_welfare(data.table(welfare = c(1, -5, 3)))  # negative values
    validate_welfare(data.table(welfare = numeric()))    # empty
  })
})
```

## Transform Function

Use `transform` to remove variable elements before comparison:

```r
test_that("output is stable across runs", {
  expect_snapshot(
    run_pipeline(),
    transform = function(lines) {
      # Remove timestamps like "2026-04-06 12:34:56"
      gsub("\\d{4}-\\d{2}-\\d{2} \\d{2}:\\d{2}:\\d{2}", "[TIMESTAMP]", lines)
    }
  )
})
```

Common uses:
- Remove timestamps or run IDs
- Normalize file paths (Windows vs Unix separators)
- Strip API keys or tokens from error messages
- Remove stochastic elements (random seeds, memory addresses)

## Variants

Use `variant` for platform-specific or R-version-specific snapshots:

```r
test_that("floating-point output is platform-stable", {
  expect_snapshot(
    print_precision_summary(dt),
    variant = tolower(Sys.info()[["sysname"]])  # "windows", "linux", "darwin"
  )
})
```

Variants save to `_snaps/{variant}/{test-file}.md` instead of `_snaps/{test-file}.md`.

## Snapshot Files

```
tests/testthat/
├── test-welfare.R
└── _snaps/
    ├── test-welfare.md        # default snapshots
    └── windows/               # variant snapshots
        └── test-welfare.md
```

Each snapshot file is human-readable markdown with the test name as heading, the code that generated the output, and the captured output.

**Always commit `_snaps/` to git** — snapshots are part of the test suite.

## Common Patterns

### Testing Error Messages

```r
test_that("validation errors are user-friendly", {
  expect_snapshot(error = TRUE, {
    validate_weights(c(-1, 0, 1))
    validate_weights(NULL)
    validate_weights(c(NA, 1, 2))
  })
})
```

### Testing data.table Print Output

```r
test_that("aggregation result prints correctly", {
  withr::local_options(datatable.print.nrows = 5L)
  dt <- data.table(
    country  = c("NGA", "ETH", "KEN"),
    headcount = c(0.40, 0.35, 0.25),
    gap       = c(0.15, 0.12, 0.09)
  )
  expect_snapshot(print(dt))
})
```

### Testing Messages and Warnings Together

```r
test_that("pipeline provides correct feedback", {
  expect_snapshot({
    result <- run_with_logging(survey_dt, verbose = TRUE)
    print(summary(result))
  })
})
```

## Best Practices

- **Commit snapshots to git** — they document expected behavior
- **Review snapshot diffs carefully** — ensure changes are intentional before accepting
- **Keep snapshots focused** — one concept per snapshot, not an entire pipeline output
- **Use `transform` for stability** — remove timestamps, addresses, paths before comparison
- **Never auto-accept in CI** — always review locally first
- **Use `withr::local_options()` to fix output width** — prevents snapshot diffs from line-length changes

```r
test_that("wide output is stable", {
  withr::local_options(width = 80L)
  expect_snapshot(print(wide_result_dt))
})
```
