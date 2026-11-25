# Targets Pipelines

`targets` tracks dependencies between pipeline steps and only re-runs what changed. Use `collapse` for fast aggregation and `data.table` for manipulation inside target functions.

## Why targets

Numbered scripts (`01_load.R`, `02_clean.R`) have no dependency tracking. `targets` knows the graph, skips unchanged steps, and provides visual pipeline maps.

## Pipeline Definition

```r
# _targets.R
library(targets)
library(tarchetypes)
tar_source("R/")

# Always run tar_make() from the project root (where _targets.R lives).
# Use here::here() inside target functions for portable paths across machines:
#   load_survey <- function(path) as.data.table(haven::read_dta(here::here(path)))

list(
  tar_target(raw_data, load_survey("data/raw/survey.dta")),
  tar_target(clean_data, clean_survey(raw_data)),
  tar_target(poverty, compute_poverty(clean_data, lines = c(2.15, 3.65, 6.85))),
  tar_target(chart, make_chart(poverty), format = "file"),
  tarchetypes::tar_quarto(report, path = "report.qmd")
)
```

## Functions Use collapse + data.table

```r
# R/poverty.R
compute_poverty <- function(dt, lines) {
  results <- lapply(lines, function(pl) {
    data.table(
      poverty_line = pl,
      headcount    = fmean(dt$welfare < pl, w = dt$weight),
      gap          = fmean(fifelse(dt$welfare < pl, (pl - dt$welfare) / pl, 0), w = dt$weight)
    )
  })
  rbindlist(results)
}
```

## Running

```r
tar_make()          # Run (skip up-to-date)
tar_read(poverty)   # Load result
tar_visnetwork()    # Dependency graph
tar_outdated()      # What needs re-running
```

## Dynamic Branching

```r
tar_target(country_data, load_survey(country_list), pattern = map(country_list))
tar_target(country_poverty, compute_poverty(country_data), pattern = map(country_data))
```

## .gitignore

```gitignore
_targets/
```

## Reproducibility: renv + targets

Commit both `renv.lock` and the `_targets/` store (or at minimum its metadata) to ensure the full pipeline is reproducible across machines:

```r
# After adding/removing packages:
renv::snapshot()

# targets respects the active renv environment automatically.
# Run tar_make() from a session where renv is active (renv::restore() first if needed).
renv::restore()  # ensure locked environment
tar_make()       # pipeline runs with pinned package versions
```

Always commit `renv.lock` together with any change to `_targets.R`.
