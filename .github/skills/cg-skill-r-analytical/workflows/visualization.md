# Visualization

`ggplot2` with the World Bank's official `wbplot` package for GPID publications. All charts for reports, briefs, and presentations must use `wbplot` theming to meet institutional standards.

## wbplot Setup

```r
# Install wbplot from the World Bank's GitHub repository (one-time)
# Requires GitHub credentials (PAT with public repo access)
# pak::pkg_install("worldbank/wbplot")
# If using remotes: remotes::install_github("worldbank/wbplot")

library(ggplot2)
library(wbplot)
library(data.table)
```

> **Note:** `wbplot` is not on CRAN. If `pak::pkg_install("worldbank/wbplot")` fails with a 401 or rate-limit error, set a GitHub PAT: `Sys.setenv(GITHUB_PAT = "your_token")` or store it in `.Renviron` as `GITHUB_PAT=your_token`.

## theme_wb() — The World Bank Theme

`theme_wb()` replaces `theme_minimal()` for all GPID output. It accepts a `chartType` argument that adjusts spacing and grid lines for different chart types.

```r
# Line chart theme
ggplot(dt, aes(x = year, y = headcount, color = region)) +
  geom_line(lineend = "round") +
  theme_wb(chartType = "line")

# Bar chart theme
ggplot(dt, aes(x = country, y = headcount)) +
  geom_bar(stat = "identity", width = 0.66) +
  theme_wb(chartType = "bar")

# Beeswarm / scatter theme
ggplot(dt, aes(x = gini, y = headcount)) +
  geom_point() +
  theme_wb(chartType = "beeswarm")
```

## World Bank Colors

### Named Colors

Access individual colors from the WB palette:

```r
# Access named colors
WBCOLORS$colorName

# Common examples (check wbplot documentation for full list)
WBCOLORS$blue
WBCOLORS$red
WBCOLORS$orange
```

### Discrete Color Scales

```r
# Categorical color scale for line/point charts
ggplot(dt, aes(x = year, y = headcount, color = region)) +
  geom_line(lineend = "round") +
  scale_color_wb_d() +
  theme_wb(chartType = "line")

# Categorical fill scale for bar charts
ggplot(dt, aes(x = country, y = headcount, fill = income_group)) +
  geom_bar(stat = "identity", width = 0.66) +
  scale_fill_wb_d() +
  theme_wb(chartType = "bar")
```

### Continuous Color Scales

```r
# Sequential palette (light to dark for magnitude)
ggplot(dt, aes(x = lon, y = lat, fill = poverty_rate)) +
  geom_tile() +
  scale_fill_wb_c(palette = "seq") +
  theme_wb()

# Diverging palette (positive/negative from center)
ggplot(dt, aes(x = country, y = change, fill = change)) +
  geom_bar(stat = "identity", width = 0.66) +
  scale_fill_wb_c(palette = "divPosNeg") +
  theme_wb(chartType = "bar")
```

### Binned Color Scales

```r
# Binned continuous scale (for choropleth-style maps)
ggplot(dt, aes(x = lon, y = lat, fill = poverty_rate)) +
  geom_tile() +
  scale_fill_wb_b() +
  theme_wb()
```

## GPID Chart Types

### Poverty Trend Line Chart (Cross-Country)

The most common GPID chart: poverty headcount over time for multiple countries or regions.

```r
# Data: poverty headcount by region and year
poverty_trends <- data.table(
  year = rep(2000:2023, each = 3),
  region = rep(c("East Asia & Pacific", "South Asia",
                 "Sub-Saharan Africa"), times = 24),
  headcount = c(
    # EAP: declining from ~35% to ~1%
    seq(35, 1, length.out = 24),
    # SA: declining from ~40% to ~10%
    seq(40, 10, length.out = 24),
    # SSA: declining from ~55% to ~35%
    seq(55, 35, length.out = 24)
  )
)

p_trend <- ggplot(poverty_trends, aes(x = year, y = headcount, color = region)) +
  geom_line(linewidth = 1, lineend = "round") +
  scale_color_wb_d() +
  scale_y_continuous(limits = c(0, 60), labels = function(x) paste0(x, "%")) +
  labs(
    title = "Poverty Headcount Ratio at $2.15/day (2017 PPP)",
    subtitle = "Percentage of population",
    x = NULL,
    y = NULL,
    color = NULL,
    caption = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "line")

ggsave("output/figures/poverty_trends.png", p_trend,
       width = 10, height = 6, dpi = 300)
```

**Key conventions:**
- `lineend = "round"` must be set manually on `geom_line()` — wbplot does not set this
- Remove axis titles with `x = NULL, y = NULL` when labels are self-explanatory
- Put the source in `caption`
- Use `scale_y_continuous(labels = ...)` to add "%" suffix, not in the data

### Cross-Country Bar Chart (Rankings)

Country comparisons ranked by value, common in Poverty & Equity Briefs.

```r
# Data: poverty headcount by country (latest available)
country_poverty <- data.table(
  country = c("Nigeria", "India", "DRC", "Tanzania", "Ethiopia",
              "Madagascar", "Mozambique", "Uganda", "Kenya", "Bangladesh"),
  headcount = c(30.9, 12.4, 62.4, 44.9, 27.0,
                77.2, 63.0, 42.2, 29.4, 5.0)
)

p_bar <- ggplot(country_poverty,
                aes(x = reorder(country, headcount), y = headcount)) +
  geom_bar(stat = "identity", width = 0.66, fill = WBCOLORS$blue) +
  geom_text(aes(label = sprintf("%.1f%%", headcount)),
            hjust = -0.1, size = 3) +
  coord_flip() +
  scale_y_continuous(expand = expansion(mult = c(0, 0.15))) +
  labs(
    title = "Poverty Headcount Ratio at $2.15/day (2017 PPP)",
    subtitle = "Latest available year",
    x = NULL,
    y = "Percent of population",
    caption = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "bar")

ggsave("output/figures/country_poverty_ranking.png", p_bar,
       width = 9, height = 6, dpi = 300)
```

**Key conventions:**
- Bar width is `0.66`, not the ggplot2 default of `0.9`
- Use `reorder()` to sort bars by value
- `coord_flip()` for horizontal bars (easier to read country names)
- Add value labels with `geom_text()` for reports

### Faceted Regional Comparison

Poverty trends by country, faceted by region.

```r
p_facet <- ggplot(dt_trends,
                  aes(x = year, y = headcount, color = country)) +
  geom_line(linewidth = 0.8, lineend = "round") +
  facet_wrap(~ region, ncol = 3, scales = "free_y") +
  scale_color_wb_d() +
  scale_y_continuous(labels = function(x) paste0(x, "%")) +
  labs(
    title = "Poverty Trends by Region and Country",
    subtitle = "$2.15/day poverty line (2017 PPP)",
    x = NULL,
    y = NULL,
    color = NULL,
    caption = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "line") +
  theme(legend.position = "bottom")

ggsave("output/figures/poverty_trends_faceted.png", p_facet,
       width = 14, height = 8, dpi = 300)
```

### Inequality Chart (Welfare Shares by Decile)

```r
# Data: welfare share by decile
decile_shares <- data.table(
  decile = factor(1:10, labels = paste0("D", 1:10)),
  share  = c(2.1, 3.4, 4.2, 5.1, 6.0, 7.2, 8.8, 11.0, 15.5, 36.7)
)

p_decile <- ggplot(decile_shares, aes(x = decile, y = share)) +
  geom_bar(stat = "identity", width = 0.66, fill = WBCOLORS$blue) +
  geom_text(aes(label = sprintf("%.1f%%", share)),
            vjust = -0.5, size = 3) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.1)),
                     labels = function(x) paste0(x, "%")) +
  labs(
    title = "Welfare Shares by Consumption Decile",
    subtitle = "Per capita consumption, 2017 PPP",
    x = "Decile",
    y = "Share of total consumption",
    caption = "Source: World Bank, Poverty and Inequality Platform"
  ) +
  theme_wb(chartType = "bar")

ggsave("output/figures/welfare_shares.png", p_decile,
       width = 9, height = 6, dpi = 300)
```

## General Conventions

### Saving

Always use `ggsave()` with explicit dimensions:

```r
ggsave(
  filename = "output/figures/plot_name.png",
  plot     = p,
  width    = 10,
  height   = 6,
  dpi      = 300
)
```

- **Reports and briefs:** `width = 10, height = 6` (landscape)
- **Presentations:** `width = 12, height = 7`
- **Square charts:** `width = 8, height = 8`

### data.table + ggplot2

data.table objects work directly in ggplot2 without conversion:

```r
# Summarize with data.table, plot with ggplot2
summary_dt <- dt[, .(mean_welfare = mean(welfare, na.rm = TRUE),
                      se_welfare = sd(welfare, na.rm = TRUE) / sqrt(.N)),
                 by = .(region, year)]

ggplot(summary_dt, aes(x = year, y = mean_welfare, color = region)) +
  geom_line(linewidth = 1, lineend = "round") +
  geom_ribbon(aes(ymin = mean_welfare - 1.96 * se_welfare,
                  ymax = mean_welfare + 1.96 * se_welfare,
                  fill = region),
              alpha = 0.2, color = NA) +
  scale_color_wb_d() +
  scale_fill_wb_d() +
  theme_wb(chartType = "line")
```

### Things to Remember

- `lineend = "round"` on every `geom_line()` — wbplot does not enforce this
- Bar width `0.66` on every `geom_bar()` or `geom_col()` — narrower than ggplot2 default
- Always `theme_wb()` — never `theme_minimal()` for GPID output
- Source line in `caption`, not `subtitle`
- Use `WBCOLORS$colorName` for single-color fills, `scale_*_wb_d()` for mapped aesthetics

*For detailed Problem/Wrong/Right explanations and rationale behind each rule, see [Visualization Anti-Patterns](../references/r-analytical-anti-patterns.md#visualization-anti-patterns).*
