# Targets Pipelines

`targets` is a pipeline tool for R that tracks dependencies between steps and only re-runs what has changed. For any multi-step pipeline (load → clean → analyze → report), `targets` replaces fragile numbered scripts with a dependency graph that guarantees reproducibility.

## Why targets Instead of Numbered Scripts

The technical team builds pipelines that the analytical team depends on. When those pipelines are a series of scripts (`01_load.R`, `02_clean.R`, `03_analyze.R`), problems accumulate:

- Someone changes `02_clean.R` but forgets to re-run `03_analyze.R`
- A pipeline takes 45 minutes and you re-run everything after a one-line fix
- Nobody knows which outputs are stale
- The pipeline works on your machine but not on Connect

`targets` solves all of these: it tracks what depends on what, skips steps that haven't changed, and provides a visual map of the entire pipeline.

## Basic Setup

```r
# Install
pak::pkg_install("targets")

# Initialize in project root
targets::use_targets()
```

This creates `_targets.R` — the pipeline definition file.

## Defining a Pipeline

### _targets.R

```r
# _targets.R
library(targets)
library(tarchetypes)  # for tar_render, tar_quarto, etc.

# Source your functions
tar_source("R/")  # loads all .R files in R/

# Define the pipeline
list(
  # Step 1: Load raw data
  tar_target(
    raw_data,
    load_survey_data("data/raw/survey_2023.dta")
  ),

  # Step 2: Clean
  tar_target(
    clean_data,
    clean_survey(raw_data)
  ),

  # Step 3: Declare survey design
  tar_target(
    survey_design,
    create_survey_design(clean_data)
  ),

  # Step 4: Compute poverty indicators
  tar_target(
    poverty_results,
    compute_poverty(survey_design, poverty_lines = c(2.15, 3.65, 6.85))
  ),

  # Step 5: Generate charts
  tar_target(
    poverty_chart,
    make_poverty_chart(poverty_results),
    format = "file"  # track the output file
  ),

  # Step 6: Render report
  tarchetypes::tar_quarto(
    report,
    path = "report.qmd"
  )
)
```

### R/ Functions

Each target calls a function defined in `R/`. Keep functions pure — no side effects, no global state.

```r
# R/load.R
load_survey_data <- function(path) {
  dt <- as.data.table(haven::read_dta(path))
  dt[, welfare := haven::zap_labels(welfare)]
  dt[, weight := haven::zap_labels(weight)]
  dt
}

# R/clean.R
clean_survey <- function(dt) {
  dt <- dt[!is.na(welfare) & welfare > 0]
  dt[, log_welfare := log(welfare)]
  dt
}

# R/design.R
create_survey_design <- function(dt) {
  dt |>
    srvyr::as_survey_design(
      ids = psu, strata = stratum, weights = weight, nest = TRUE
    )
}

# R/poverty.R
compute_poverty <- function(svy, poverty_lines) {
  results <- lapply(poverty_lines, function(pl) {
    svy |>
      srvyr::summarise(
        fgt0 = srvyr::survey_mean(welfare < pl, vartype = "ci"),
        poverty_line = pl
      )
  })
  data.table::rbindlist(results)
}

# R/charts.R
make_poverty_chart <- function(results) {
  p <- ggplot2::ggplot(results, ggplot2::aes(x = factor(poverty_line), y = fgt0)) +
    ggplot2::geom_col(width = 0.66, fill = wbplot::WBCOLORS$blue) +
    wbplot::theme_wb(chartType = "bar") +
    ggplot2::labs(title = "Poverty Headcount by Poverty Line",
                  x = "Poverty line ($/day)", y = "Headcount ratio")
  path <- "output/figures/poverty_by_line.png"
  ggplot2::ggsave(path, p, width = 9, height = 6, dpi = 300)
  path  # return the file path for tracking
}
```

## Running the Pipeline

```r
# Run the full pipeline (only executes what's changed)
tar_make()

# Check what's up to date vs outdated
tar_outdated()

# Visualize the pipeline as a dependency graph
tar_visnetwork()

# Read a completed target into the session
poverty <- tar_read(poverty_results)

# Load a target into the global environment
tar_load(clean_data)
```

## Pipeline Visualization

`tar_visnetwork()` renders an interactive graph showing:
- **Green nodes:** up to date (will be skipped)
- **Blue nodes:** outdated (will be re-run)
- **Arrows:** dependency direction

This is invaluable for debugging: if you change `clean_survey()`, the graph shows exactly which downstream targets need to re-run.

```r
# Static visualization (for reports/documentation)
tar_mermaid()

# Interactive visualization (in RStudio/Positron viewer)
tar_visnetwork()
```

## Dynamic Branching

When you need to run the same analysis for multiple countries or years, use dynamic branching instead of hardcoding targets.

### tar_map() — Static Branching

When you know the branches at pipeline definition time:

```r
# _targets.R
library(targets)
library(tarchetypes)

countries <- c("NGA", "IND", "ETH", "TZA", "BGD")

list(
  # One target per country
  tarchetypes::tar_map(
    values = list(country = countries),
    tar_target(
      raw_data,
      load_survey_data(country)
    ),
    tar_target(
      poverty,
      compute_poverty(raw_data)
    )
  ),

  # Combine all country results
  tar_target(
    all_poverty,
    dplyr::bind_rows(poverty)
  )
)
```

### Dynamic Branching with pattern

When branches depend on a previous target's output:

```r
list(
  tar_target(
    country_list,
    get_available_countries()  # returns c("NGA", "IND", "ETH", ...)
  ),

  # One branch per country, determined at runtime
  tar_target(
    country_data,
    load_survey_data(country_list),
    pattern = map(country_list)
  ),

  tar_target(
    country_poverty,
    compute_poverty(country_data),
    pattern = map(country_data)
  ),

  tar_target(
    combined,
    rbindlist(country_poverty)
  )
)
```

## File Tracking

When a target produces a file (chart, table, report), use `format = "file"` so targets knows to check whether the file has changed:

```r
tar_target(
  poverty_chart,
  {
    p <- make_chart(results)
    path <- "output/figures/chart.png"
    ggsave(path, p, width = 10, height = 6, dpi = 300)
    path
  },
  format = "file"
)
```

## Rendering Quarto Reports as Targets

```r
# Render a Quarto report as part of the pipeline
tarchetypes::tar_quarto(
  report,
  path = "report.qmd",
  extra_files = c("output/figures/chart.png")  # re-render if chart changes
)

# Parametrized Quarto report
tarchetypes::tar_quarto(
  country_brief,
  path = "brief.qmd",
  execute_params = list(country = "NGA", year = 2023)
)
```

## Project Structure

```
pipeline-project/
├── _targets.R            # Pipeline definition
├── R/
│   ├── load.R            # Data loading functions
│   ├── clean.R           # Cleaning functions
│   ├── analysis.R        # Analysis functions
│   └── charts.R          # Visualization functions
├── data/
│   └── raw/              # Input data (never modified by pipeline)
├── output/
│   ├── figures/          # Generated charts
│   └── tables/           # Generated tables
├── report.qmd            # Quarto report (rendered by pipeline)
├── _targets/             # Pipeline cache (add to .gitignore)
├── renv.lock
├── .gitignore
└── README.md
```

### .gitignore additions

```gitignore
_targets/
```

The `_targets/` directory is the pipeline cache. Do not commit it — it contains serialized R objects and will be rebuilt by `tar_make()`.

## Common Commands Reference

| Command | Purpose |
|---------|---------|
| `tar_make()` | Run the pipeline (skip up-to-date targets) |
| `tar_read(name)` | Load a completed target into R |
| `tar_load(name)` | Load target into global environment |
| `tar_outdated()` | List targets that need re-running |
| `tar_visnetwork()` | Interactive dependency graph |
| `tar_manifest()` | Table of all targets and their commands |
| `tar_progress()` | Status of each target (built, skipped, errored) |
| `tar_invalidate(name)` | Force a target to re-run next time |
| `tar_destroy()` | Delete the entire cache and start fresh |
