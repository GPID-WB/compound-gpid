# ggplot2 + wbplot Reference

`ggplot2` with the World Bank's `wbplot` package for official GPID charts.

## Setup

```r
library(ggplot2)
library(wbplot)
```

## theme_wb()

```r
# Line chart
ggplot(dt, aes(x = year, y = headcount, color = region)) +
  geom_line(lineend = "round") +
  theme_wb(chartType = "line")

# Bar chart
ggplot(dt, aes(x = country, y = headcount)) +
  geom_bar(stat = "identity", width = 0.66) +
  theme_wb(chartType = "bar")

# Scatter
ggplot(dt, aes(x = income, y = welfare)) +
  geom_point() +
  theme_wb(chartType = "scatter")
```

## World Bank Colors

```r
WBCOLORS$blue       # Primary WB blue
WBCOLORS$red        # WB red
WBCOLORS$orange     # WB orange
# (see ?WBCOLORS for full palette)

# Discrete color/fill scales
scale_color_wb_d()
scale_fill_wb_d()

# Continuous (sequential / diverging)
scale_fill_wb_c(palette = "seq")
scale_fill_wb_c(palette = "divPosNeg")
```

## Chart Type Patterns

### Poverty Trend Line Chart

```r
# Aggregate data before plotting (use your project's dialect)
# Example with collapse:
poverty_trends <- dt |>
  fgroup_by(region, year) |>
  fsummarise(headcount = fmean(poor, w = weight)) |>
  qDT()

# Plot
p_trend <- ggplot(poverty_trends, aes(x = year, y = headcount, color = region)) +
  geom_line(linewidth = 1, lineend = "round") +
  scale_color_wb_d() +
  scale_y_continuous(
    limits = c(0, NA),
    labels = function(x) paste0(x * 100, "%")
  ) +
  labs(
    title    = "Poverty Headcount Ratio at $2.15/day (2017 PPP)",
    subtitle = "Percentage of population",
    x        = NULL, y = NULL, color = NULL,
    caption  = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "line")
```

### Cross-Country Bar Chart

```r
# Aggregate
country_poverty <- collap(dt, ~ country, fmean, w = ~ weight, cols = "poor")

p_bar <- ggplot(country_poverty, aes(x = reorder(country, poor), y = poor)) +
  geom_bar(stat = "identity", width = 0.66, fill = WBCOLORS$blue) +
  geom_text(
    aes(label = sprintf("%.1f%%", poor * 100)),
    hjust = -0.1, size = 3
  ) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
  labs(
    title   = "Poverty Headcount Ratio at $2.15/day (2017 PPP)",
    x       = NULL, y = "Share of population",
    caption = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "bar")
```

### Faceted Regional Comparison

```r
p_facet <- ggplot(dt_trends, aes(x = year, y = headcount, color = country)) +
  geom_line(linewidth = 0.8, lineend = "round") +
  facet_wrap(~ region, ncol = 3, scales = "free_y") +
  scale_color_wb_d() +
  labs(
    title   = "Poverty Trends by Region",
    x       = NULL, y = NULL, color = NULL,
    caption = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "line") +
  theme(legend.position = "bottom")
```

### Inequality Chart (Welfare Shares by Decile)

```r
p_decile <- ggplot(decile_shares, aes(x = factor(decile), y = welfare_share)) +
  geom_bar(stat = "identity", width = 0.66, fill = WBCOLORS$blue) +
  geom_text(
    aes(label = sprintf("%.1f%%", welfare_share * 100)),
    vjust = -0.5, size = 3
  ) +
  scale_y_continuous(
    expand = expansion(mult = c(0, 0.1)),
    labels = function(x) paste0(x * 100, "%")
  ) +
  labs(
    title   = "Welfare Shares by Consumption Decile",
    x       = "Decile", y = "Share of total consumption",
    caption = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "bar")
```

## Style Conventions

| Rule | Value |
|------|-------|
| Line width | `linewidth = 1` (main lines), `0.8` (secondary) |
| Line end | `lineend = "round"` — always on `geom_line()` |
| Bar width | `0.66` — always on `geom_bar()`/`geom_col()` |
| Theme | `theme_wb(chartType = ...)` — never `theme_minimal()` |
| Attribution | `caption =` — never `subtitle =` for source |
| Single color | `fill = WBCOLORS$blue` |
| Mapped aesthetics | `scale_color_wb_d()` / `scale_fill_wb_d()` |

## Saving

```r
ggsave("output/figures/poverty_trends.png", p_trend,
       width = 10, height = 6, dpi = 300)

# For reports (higher resolution)
ggsave("output/figures/country_ranking.png", p_bar,
       width = 9, height = 6, dpi = 300)
```
