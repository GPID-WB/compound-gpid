# ggplot2 Conventions

## Standard Plot Template

```r
ggplot(dt, aes(x = x_var, y = y_var)) +
  geom_point() +
  labs(
    title = "Descriptive Title",
    subtitle = "Additional context",
    x = "X-axis Label",
    y = "Y-axis Label",
    caption = "Source: Data Source"
  ) +
  theme_minimal()
```

## Common Geoms

```r
# Scatter
ggplot(dt, aes(x, y, color = group)) + geom_point(alpha = 0.7)

# Line
ggplot(dt, aes(x = year, y = value, color = country)) + geom_line()

# Bar
ggplot(dt, aes(x = category, y = count)) + geom_col()  # pre-computed
ggplot(dt, aes(x = category)) + geom_bar()              # counts rows

# Histogram
ggplot(dt, aes(x = income)) + geom_histogram(bins = 30)

# Box plot
ggplot(dt, aes(x = region, y = income)) + geom_boxplot()

# Density
ggplot(dt, aes(x = income, fill = group)) + geom_density(alpha = 0.5)
```

## Color Scales

```r
# Colorblind-friendly
scale_color_viridis_d()    # discrete
scale_color_viridis_c()    # continuous
scale_fill_brewer(palette = "Set2")

# Manual colors
scale_color_manual(values = c("group1" = "#1b9e77", "group2" = "#d95f02"))
```

## Faceting

```r
# Wrap
facet_wrap(~ region, ncol = 3, scales = "free_y")

# Grid
facet_grid(region ~ year)
```

## Saving

```r
ggsave(
  filename = "output/figures/plot_name.png",
  plot = p,
  width = 10,
  height = 6,
  dpi = 300
)
```

## data.table + ggplot2

```r
# data.table works directly with ggplot2
ggplot(dt[year == 2023], aes(x = income, y = expenditure)) +
  geom_point()

# Summarize with data.table, plot with ggplot2
summary_dt <- dt[, .(mean_income = mean(income)), by = region]
ggplot(summary_dt, aes(x = reorder(region, mean_income), y = mean_income)) +
  geom_col() +
  coord_flip()
```

## Theme Consistency

Use `theme_minimal()` as the default across the project. For custom themes:

```r
theme_project <- function(base_size = 12) {
  theme_minimal(base_size = base_size) +
    theme(
      plot.title = element_text(face = "bold"),
      panel.grid.minor = element_blank(),
      legend.position = "bottom"
    )
}
```
