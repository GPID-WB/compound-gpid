# Quarto for Research

## Project Setup

```bash
# Create new Quarto project
quarto create project default my-report

# Install R Quarto package
install.packages("quarto")
```

## Standard YAML Header (WB Report Style)

```yaml
---
title: "Poverty Trends in Sub-Saharan Africa"
subtitle: "Evidence from GPID Microdata, 2000–2022"
author:
  - name: "First Last"
    affiliation: "World Bank, DECDG"
date: today
date-format: "MMMM D, YYYY"
format:
  html:
    toc: true
    toc-depth: 3
    code-fold: true
  docx:
    reference-doc: "template/wb-template.docx"
  pdf:
    documentclass: article
execute:
  echo: false
  warning: false
  cache: true
---
```

## Parametrized Reports

```yaml
# In YAML header
params:
  country: "BRA"
  year: 2022
  poverty_line: 2.15
```

```r
# In code chunks — access via params$
dt_country <- dt[country == params$country & year == params$year]
poverty_rate <- weighted.mean(dt_country$poor, dt_country$wgt)
```

```r
# Render for multiple countries
countries <- c("BRA", "IND", "NGA")
purrr::walk(countries, function(cty) {
  quarto::quarto_render(
    "report.qmd",
    output_file = paste0("output/report_", cty, ".html"),
    execute_params = list(country = cty)
  )
})
```

## Cross-References

```markdown
See @fig-poverty-trend for the time series and @tbl-summary for summary statistics.

![Poverty headcount ratio, 2000–2022](){#fig-poverty-trend}

: Summary Statistics {#tbl-summary}
```

```r
# R chunks — label with fig- or tbl- prefix for cross-ref
#| label: fig-poverty-trend
#| fig-cap: "Poverty headcount ratio, 2000–2022"
plot_poverty_trend(dt)
```

## Tables

```r
# Publication tables with modelsummary (model results)
msummary(models, output = "kableExtra")

# Summary statistics with datasummary
library(modelsummary)
datasummary_skim(dt[, .(consumption_ppp, poor, hh_size, educ)],
                 output = "kableExtra")

# Custom kableExtra tables
library(kableExtra)
kbl(summary_dt, digits = 3, booktabs = TRUE) |>
  kable_styling(latex_options = "hold_position") |>
  add_header_above(c(" " = 1, "Poverty Measures" = 3))
```

## Caching Strategy

```yaml
execute:
  cache: true      # Cache computation by default
```

```r
# Force re-run expensive chunk
#| cache: false
load_data()        # Always re-read data

# Cache a specific chunk
#| cache: true
#| cache-vars: model_results   # only invalidate on these vars
model_results <- run_model(dt)
```

## Inline Code

```markdown
The poverty rate in `r params$country` is `r scales::percent(poverty_rate, 0.1)`.
```

## Project Structure

```
my-report/
├── report.qmd          # Main document
├── _quarto.yml         # Project config
├── params/
│   └── countries.yml   # Parameter sets for batch rendering
├── R/
│   ├── load_data.R
│   └── analysis.R
├── template/
│   └── wb-template.docx
└── output/             # Rendered reports
```
