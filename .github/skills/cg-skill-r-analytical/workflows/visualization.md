# Visualization

`ggplot2` with the World Bank's official `wbplot` package. Data aggregation before plotting uses `collapse` for speed. All charts for reports must use `wbplot` theming.

## wbplot Setup

```r
library(ggplot2)
library(wbplot)
library(collapse)
library(data.table)
```

## theme_wb()

```r
ggplot(dt, aes(x = year, y = headcount, color = region)) +
  geom_line(lineend = "round") +
  theme_wb(chartType = "line")

ggplot(dt, aes(x = country, y = headcount)) +
  geom_bar(stat = "identity", width = 0.66) +
  theme_wb(chartType = "bar")
```

## World Bank Colors

```r
WBCOLORS$blue                # Named colors
scale_color_wb_d()           # Discrete color scale
scale_fill_wb_d()            # Discrete fill scale
scale_fill_wb_c(palette = "seq")       # Sequential continuous
scale_fill_wb_c(palette = "divPosNeg") # Diverging continuous
```

## Data Preparation with collapse

Aggregate data with collapse before passing to ggplot2:

```r
# Poverty trends: weighted headcount by region and year
poverty_trends <- dt |>
  fgroup_by(region, year) |>
  fsummarise(headcount = fmean(poor, w = weight))

# Convert to data.table for ggplot compatibility
poverty_trends <- qDT(poverty_trends)
```

## GPID Chart Types

### Poverty Trend Line Chart

```r
p_trend <- ggplot(poverty_trends, aes(x = year, y = headcount, color = region)) +
  geom_line(linewidth = 1, lineend = "round") +
  scale_color_wb_d() +
  scale_y_continuous(limits = c(0, NA), labels = function(x) paste0(x * 100, "%")) +
  labs(
    title = "Poverty Headcount Ratio at $2.15/day (2017 PPP)",
    subtitle = "Percentage of population",
    x = NULL, y = NULL, color = NULL,
    caption = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "line")

ggsave("output/figures/poverty_trends.png", p_trend, width = 10, height = 6, dpi = 300)
```

### Cross-Country Bar Chart

```r
# Aggregate with collapse
country_poverty <- collap(dt, ~ country, fmean, w = ~ weight, cols = "poor")
setnames(country_poverty, "poor", "headcount")

p_bar <- ggplot(country_poverty, aes(x = reorder(country, headcount), y = headcount)) +
  geom_bar(stat = "identity", width = 0.66, fill = WBCOLORS$blue) +
  geom_text(aes(label = sprintf("%.1f%%", headcount * 100)), hjust = -0.1, size = 3) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
  labs(
    title = "Poverty Headcount Ratio at $2.15/day (2017 PPP)",
    x = NULL, y = "Share of population",
    caption = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "bar")

ggsave("output/figures/country_ranking.png", p_bar, width = 9, height = 6, dpi = 300)
```

### Faceted Regional Comparison

```r
p_facet <- ggplot(dt_trends, aes(x = year, y = headcount, color = country)) +
  geom_line(linewidth = 0.8, lineend = "round") +
  facet_wrap(~ region, ncol = 3, scales = "free_y") +
  scale_color_wb_d() +
  labs(title = "Poverty Trends by Region", x = NULL, y = NULL, color = NULL,
       caption = "Source: World Bank, Poverty and Inequality Platform") +
  theme_wb(chartType = "line") +
  theme(legend.position = "bottom")
```

### Inequality Chart (Welfare Shares)

```r
p_decile <- ggplot(decile_shares, aes(x = factor(decile), y = welfare_share)) +
  geom_bar(stat = "identity", width = 0.66, fill = WBCOLORS$blue) +
  geom_text(aes(label = sprintf("%.1f%%", welfare_share * 100)), vjust = -0.5, size = 3) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.1)),
                     labels = function(x) paste0(x * 100, "%")) +
  labs(title = "Welfare Shares by Consumption Decile", x = "Decile",
       y = "Share of total consumption",
       caption = "Source: World Bank, Poverty and Inequality Platform") +
  theme_wb(chartType = "bar")
```

## Key Conventions

- `lineend = "round"` on every `geom_line()` — wbplot does not set this
- Bar width `0.66` on every `geom_bar()`/`geom_col()` — narrower than default
- Always `theme_wb()` — never `theme_minimal()` for GPID output
- Source in `caption`, not `subtitle`
- `WBCOLORS$colorName` for single-color fills, `scale_*_wb_d()` for mapped aesthetics
- Aggregate data with `collapse` before plotting — never inside ggplot pipelines

### Saving

```r
ggsave("output/figures/plot.png", p, width = 10, height = 6, dpi = 300)
```
