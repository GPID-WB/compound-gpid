# Targets Pipelines

## Core Concepts

- A **target** is a named, cached computation: a function call + its result.
- `tar_make()` runs only outdated targets (detected by content hash — not time).
- This makes pipelines reproducible, restartable, and efficient.

## Minimal Pipeline

```r
# _targets.R (at project root)
library(targets)

# Source all functions
tar_source("R/")

list(
  tar_target(raw_data,    load_raw("data/raw/survey.dta")),
  tar_target(clean_data,  clean_survey(raw_data)),
  tar_target(model,       fit_model(clean_data)),
  tar_target(results,     extract_results(model)),
  tar_target(report,      render_report(results),
             format = "file")
)
```

## Running Pipelines

```r
tar_make()           # Run all outdated targets
tar_make("results")  # Run up to a specific target

tar_visnetwork()     # Visualize the dependency graph

tar_read("results")  # Read a target's value
tar_load("results")  # Load into current environment

tar_invalidate("clean_data")  # Force a target to re-run
tar_destroy()                  # Delete all cached targets
```

## Dynamic Branching

```r
# Branch over a list of country codes
list(
  tar_target(countries,    c("BRA", "IND", "NGA")),
  tar_target(country_data, fetch_country(countries),
             pattern = map(countries)),  # one branch per country
  tar_target(all_results,  combine_results(country_data),
             pattern = map(country_data))
)
```

## File Targets

```r
# Track a file as a target (hash its content)
tar_target(
  raw_file,
  "data/raw/survey.dta",
  format = "file"
)

# Use the file path downstream
tar_target(
  data,
  read_dta(raw_file)
)
```

## Parallel Execution

```r
# _targets.R
library(targets)
library(future)
plan(multisession, workers = 4)

tar_option_set(
  controller = crew::crew_controller_local(workers = 4)
)
```

## Project Structure

```
project/
├── _targets.R          # Pipeline definition
├── R/
│   ├── loading.R       # Data loading functions
│   ├── cleaning.R      # Cleaning functions
│   ├── analysis.R      # Modelling functions
│   └── reporting.R     # Output functions
├── _targets/           # Cache (gitignore this)
├── data/
│   └── raw/
└── output/
```

Add `_targets/` to `.gitignore`. Commit `_targets.R` and all `R/` functions.

## Testing with targets

```r
# Test the individual functions, not the pipeline
test_that("clean_survey handles missing income", {
  raw <- data.table(id = 1:3, income = c(1000, NA, 2000))
  result <- clean_survey(raw)
  expect_false(any(is.na(result$income)))
})

# Use tar_test() for pipeline-level snapshot tests
tar_test("pipeline produces expected results", {
  tar_make()
  result <- tar_read("results")
  expect_equal(nrow(result), expected_rows)
})
```
