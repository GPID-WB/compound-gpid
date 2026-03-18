# Visualization — ggplot2 + wbplot

## Standard Plot Template

```r
library(ggplot2)
library(wbplot)  # World Bank visual identity

ggplot(dt, aes(x = x_var, y = y_var)) +
  geom_point() +
  labs(
    title = "Descriptive Title",
    subtitle = "Additional context",
    x = "X-axis Label",
    y = "Y-axis Label",
    caption = "Source: World Bank GPID"
  ) +
  theme_wb()
```

## World Bank Theme and Colors

```r
# Apply WB corporate theme
theme_wb()                  # default WB theme
theme_wb(base_size = 14)    # larger text for presentations

# WB color palette
scale_color_wb_d()          # discrete (categorical) colors
scale_fill_wb_d()
scale_color_wb_c()          # continuous
scale_fill_wb_c()

# Access WB colors directly
WBCOLORS                    # named vector of hex codes
WBCOLORS["blue"]            # #009FDA
WBCOLORS["red"]

# Manual WB colors
scale_color_manual(values = c("low" = WBCOLORS["blue"],
                               "high" = WBCOLORS["red"]))
```

## Common Analytical Geoms

```r
# Poverty incidence curve
ggplot(dt, aes(x = consumption_ppp, y = cum_share)) +
  geom_line() +
  geom_vline(xintercept = 2.15, linetype = "dashed", color = WBCOLORS["red"]) +
  scale_x_continuous(labels = scales::dollar_format(prefix = "$")) +
  labs(x = "Daily Consumption (2017 PPP)", y = "Cumulative Population Share") +
  theme_wb()

# Grouped bar chart (country comparison)
ggplot(summary_dt, aes(x = reorder(country, poverty_rate), y = poverty_rate,
                        fill = region)) +
  geom_col() +
  scale_fill_wb_d() +
  coord_flip() +
  scale_y_continuous(labels = scales::percent_format()) +
  theme_wb()

# Time series
ggplot(dt, aes(x = year, y = headcount, color = country)) +
  geom_line(linewidth = 0.8) +
  geom_point(size = 2) +
  scale_color_wb_d() +
  scale_y_continuous(labels = scales::percent_format()) +
  theme_wb() +
  theme(legend.position = "bottom")
```

## Faceting

```r
# Facet by region
ggplot(dt, aes(x = year, y = headcount)) +
  geom_line() +
  facet_wrap(~ region, ncol = 3, scales = "free_y") +
  theme_wb()
```

## data.table + ggplot2

```r
# Summarize with data.table, plot with ggplot2
summary_dt <- dt[, .(poverty_rate = weighted.mean(poor, wgt, na.rm = TRUE)),
                 by = .(region, year)]

ggplot(summary_dt, aes(x = year, y = poverty_rate, color = region)) +
  geom_line() +
  scale_color_wb_d() +
  scale_y_continuous(labels = scales::percent_format()) +
  theme_wb()
```

## Saving Publication-Quality Figures

```r
# Standard export settings for WB reports
ggsave(
  filename = "output/figures/poverty_trends.png",
  plot = p,
  width = 10,
  height = 6,
  dpi = 300,
  bg = "white"
)

# For two-column layout
ggsave("output/figures/narrow.png", p, width = 5, height = 4, dpi = 300)
```

## Color Scale Reference

```r
# Colorblind-friendly alternatives when not using wbplot
scale_color_viridis_d()     # discrete
scale_color_viridis_c()     # continuous
scale_fill_brewer(palette = "Set2")
```

> **Core ggplot2 mechanics (layers, scales, `geom_*`)**: see `cg-skill-r-technical`.
