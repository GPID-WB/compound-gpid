---
name: cg-skill-r-visualization
description: "ggplot2 and wbplot visualization patterns for World Bank GPID charts. Load when creating or reviewing R visualizations. Covers theme_wb(), WBCOLORS, scale_color_wb_d/scale_fill_wb_d, chart type conventions (line, bar, facet, scatter), ggsave standards, and World Bank style rules. Dialect-neutral: works with both data.table-collapse and tidyverse workflows."
user-invocable: false
---

# R Visualization

`ggplot2` with the World Bank's official `wbplot` package. Dialect-neutral — aggregate data with your project's preferred syntax before plotting, then use `ggplot2` + `wbplot` for all charts.

## Key Rules

- Always use `theme_wb(chartType = ...)` — never `theme_minimal()` for GPID output
- Always source in `caption`, never `subtitle`
- Bar width `0.66` on every `geom_bar()`/`geom_col()`
- `lineend = "round"` on every `geom_line()`
- `WBCOLORS$colorName` for single-color fills, `scale_*_wb_d()` for mapped aesthetics
- Aggregate data **before** passing to ggplot — never compute inside ggplot pipelines
- Save with `dpi = 300`

## References

- [ggplot2 + wbplot Reference](references/ggplot2-reference.md) — theme_wb(), WBCOLORS, scale functions, chart type patterns, ggsave conventions

---

> This skill is dialect-neutral. Use `cg-skill-r-collapse` or `cg-skill-r-datatable` (data.table-collapse) or `cg-skill-r-tidyverse` to prepare data before plotting.
