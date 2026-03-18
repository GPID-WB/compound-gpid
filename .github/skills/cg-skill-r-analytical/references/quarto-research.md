# Quarto for Research

Quarto for analytical output: parametrized reports, cross-referencing figures and tables, and rendering to multiple formats (HTML, Word, PDF).

## Basic Document Structure

```yaml
---
title: "Poverty Trends in Sub-Saharan Africa"
author: "GPID Team"
date: today
format:
  html:
    toc: true
    code-fold: true
  docx:
    reference-doc: template.docx
  pdf:
    documentclass: article
---
```

## Inline R Code

Embed computed values directly in text so they update automatically when data changes:

```markdown
The poverty headcount in 2023 was `r sprintf("%.1f%%", headcount_2023 * 100)`,
down from `r sprintf("%.1f%%", headcount_2020 * 100)` in 2020. This represents
a decline of `r sprintf("%.1f", (headcount_2020 - headcount_2023) * 100)`
percentage points over three years.
```

This renders as: "The poverty headcount in 2023 was 24.3%, down from 27.1% in 2020..."

**Why this matters:** Hardcoded numbers in text get out of sync with tables and figures when data is updated. Inline R eliminates this class of error.

## Figure Cross-References

Label figures and reference them in text. Labels must start with `#fig-`.

````markdown
```{r}
#| label: fig-poverty-trends
#| fig-cap: "Poverty headcount at $2.15/day (2017 PPP), by region"
#| fig-width: 10
#| fig-height: 6

ggplot(poverty_dt, aes(x = year, y = headcount, color = region)) +
  geom_line(linewidth = 1, lineend = "round") +
  scale_color_wb_d() +
  theme_wb(chartType = "line")
```

As shown in @fig-poverty-trends, poverty has declined across all regions
since 2000, with the fastest progress in East Asia.
````

The `@fig-poverty-trends` reference automatically becomes "Figure 1" (or whatever the number is) in the rendered output.

## Table Cross-References

Label tables with `#tbl-` prefix:

````markdown
```{r}
#| label: tbl-summary-stats
#| tbl-cap: "Summary statistics by region"

library(modelsummary)
datasummary(
  welfare + income + hhsize ~ region * (Mean + SD + N),
  data = dt,
  output = "default"
)
```

@tbl-summary-stats presents the descriptive statistics for our sample.
````

## Parametrized Reports

Run the same analysis for different countries, years, or poverty lines by passing parameters.

### YAML Header with Parameters

```yaml
---
title: "Poverty Brief: `r params$country`"
format: docx
params:
  country: "Nigeria"
  year: 2023
  poverty_line: 2.15
---
```

### Using Parameters in Code

````markdown
```{r}
dt <- load_survey(params$country, params$year)
svy <- dt |>
  as_survey_design(ids = psu, strata = stratum, weights = weight, nest = TRUE)

headcount <- svy |>
  summarise(fgt0 = survey_mean(welfare < params$poverty_line, vartype = "ci"))
```

In `r params$year`, `r params$country` had a poverty headcount of
`r sprintf("%.1f%%", headcount$fgt0 * 100)` at the
$`r params$poverty_line`/day poverty line.
````

### Rendering Programmatically

```r
# Render a single country brief
quarto::quarto_render(
  input       = "poverty_brief.qmd",
  execute_params = list(country = "Nigeria", year = 2023, poverty_line = 2.15),
  output_file = "output/briefs/poverty_brief_NGA_2023.docx"
)

# Batch render for multiple countries
countries <- c("Nigeria", "India", "Ethiopia", "Tanzania")

for (ctry in countries) {
  quarto::quarto_render(
    input       = "poverty_brief.qmd",
    execute_params = list(country = ctry, year = 2023, poverty_line = 2.15),
    output_file = sprintf("output/briefs/poverty_brief_%s_2023.docx", ctry)
  )
}
```

## Output Formats

### HTML (for sharing and exploration)

```yaml
format:
  html:
    toc: true
    toc-depth: 3
    code-fold: true       # Collapse code blocks
    code-summary: "Show code"
    self-contained: true  # Single HTML file, no dependencies
```

### Word (for institutional review)

```yaml
format:
  docx:
    toc: true
    reference-doc: templates/wb_template.docx  # WB branding
```

### PDF (for final publication)

```yaml
format:
  pdf:
    documentclass: article
    papersize: letter
    geometry:
      - margin=1in
    fontsize: 11pt
```

### Multiple Formats at Once

```yaml
format:
  html:
    toc: true
  docx:
    toc: true
  pdf:
    documentclass: article
```

Render a specific format: `quarto::quarto_render("report.qmd", output_format = "docx")`

## Code Chunk Options

Common chunk options for GPID reports:

````markdown
```{r}
#| label: fig-my-plot
#| fig-cap: "Caption text"
#| fig-width: 10
#| fig-height: 6
#| echo: false        # Hide code in output
#| warning: false     # Suppress warnings
#| message: false     # Suppress messages
```
````

For reproducibility, set a seed in the setup chunk:

````markdown
```{r}
#| label: setup
#| include: false

library(data.table)
library(srvyr)
library(fixest)
library(ggplot2)
library(wbplot)
library(modelsummary)

set.seed(42)
```
````

## Project Organization for Quarto Reports

```
project/
├── report.qmd              # Main report
├── appendix.qmd            # Supplementary analysis
├── _quarto.yml             # Project-level config (optional)
├── R/
│   ├── 01_load_data.R      # Data loading functions
│   ├── 02_clean_data.R     # Cleaning functions
│   └── 03_analysis.R       # Analysis functions
├── data/
│   └── raw/
├── output/
│   ├── figures/
│   └── tables/
└── templates/
    └── wb_template.docx
```

Source analysis functions from R scripts:

````markdown
```{r}
#| label: setup
#| include: false

source("R/01_load_data.R")
source("R/02_clean_data.R")
source("R/03_analysis.R")
```
````
