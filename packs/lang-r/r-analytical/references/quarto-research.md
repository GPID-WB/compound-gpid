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

Embed computed values directly in text so they update automatically:

```markdown
The poverty headcount in 2023 was `r sprintf("%.1f%%", headcount_2023 * 100)`,
down from `r sprintf("%.1f%%", headcount_2020 * 100)` in 2020.
```

## Figure Cross-References

Label figures with `#fig-` prefix, reference with `@fig-`:

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

As shown in @fig-poverty-trends, poverty has declined across all regions.
````

## Table Cross-References

Label tables with `#tbl-` prefix:

````markdown
```{r}
#| label: tbl-summary-stats
#| tbl-cap: "Summary statistics by region"

datasummary(welfare + income + hhsize ~ region * (Mean + SD + N),
            data = dt, output = "default")
```

@tbl-summary-stats presents the descriptive statistics.
````

## Parametrized Reports

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

### Rendering Programmatically

```r
# Single country
quarto::quarto_render(
  input = "brief.qmd",
  execute_params = list(country = "Nigeria", year = 2023),
  output_file = "output/briefs/brief_NGA_2023.docx"
)

# Batch
for (ctry in c("Nigeria", "India", "Ethiopia")) {
  quarto::quarto_render(
    input = "brief.qmd",
    execute_params = list(country = ctry, year = 2023),
    output_file = sprintf("output/briefs/brief_%s_2023.docx", ctry)
  )
}
```

## Output Formats

```yaml
# HTML
format:
  html: { toc: true, code-fold: true, self-contained: true }

# Word
format:
  docx: { toc: true, reference-doc: templates/wb_template.docx }

# PDF
format:
  pdf: { documentclass: article, geometry: "margin=1in" }
```

## Setup Chunk

````markdown
```{r}
#| label: setup
#| include: false

library(data.table)
library(collapse)
library(fixest)
library(ggplot2)
library(wbplot)
library(modelsummary)
set.seed(42)
```
````
