# Welfare Measurement Patterns (GPID)

## FGT Poverty Indices

```r
# Foster-Greer-Thorbecke (1984)
# FGT(0) = headcount ratio
# FGT(1) = poverty gap
# FGT(2) = poverty severity (squared gap)

fgt <- function(income, line, weights = NULL, alpha = 0) {
  if (is.null(weights)) weights <- rep(1, length(income))
  poor <- income < line
  gap <- pmax(0, (line - income) / line)
  weighted.mean(gap^alpha * poor, weights, na.rm = TRUE)
}

# Usage
dt[, .(
  headcount = fgt(consumption_ppp, line = 2.15, weights = wgt, alpha = 0),
  gap       = fgt(consumption_ppp, line = 2.15, weights = wgt, alpha = 1),
  severity  = fgt(consumption_ppp, line = 2.15, weights = wgt, alpha = 2)
), by = .(country, year)]
```

## Gini Coefficient

```r
gini <- function(income, weights = NULL) {
  if (is.null(weights)) weights <- rep(1, length(income))
  n <- length(income)
  ord <- order(income)
  income_sorted <- income[ord]
  wgt_sorted    <- weights[ord]
  wgt_cum       <- cumsum(wgt_sorted) / sum(wgt_sorted)
  income_cum    <- cumsum(income_sorted * wgt_sorted) / sum(income_sorted * wgt_sorted)
  # Trapezoidal integration
  2 * sum(diff(wgt_cum) * (income_cum[-n] + income_cum[-1]) / 2) - 1
}

# By group
dt[, .(gini = gini(consumption_ppp, weights = wgt)), by = .(country, year)]
```

## PPP Conversion

```r
# PPP unit tracking — always know what your monetary variables represent
# Convention: suffix _ppp means 2017 PPP USD, _lcu means local currency

dt[, consumption_ppp := consumption_lcu / cpi_deflator / ppp_2017]

# Check: global poverty line is $2.15/day in 2017 PPP
POVERTY_LINE_2017PPP <- 2.15

# Convert local poverty line to 2017 PPP
dt[, national_line_ppp := national_line_lcu / cpi_2017 / ppp_2017]
```

## Lorenz Curve

```r
lorenz <- function(income, weights = NULL, n_points = 100) {
  if (is.null(weights)) weights <- rep(1, length(income))
  ord <- order(income)
  income_sorted <- income[ord]
  wgt_sorted    <- weights[ord]
  wgt_cum       <- cumsum(wgt_sorted) / sum(wgt_sorted)
  income_cum    <- cumsum(income_sorted * wgt_sorted) / sum(income_sorted * wgt_sorted)
  data.table(cum_pop = c(0, wgt_cum), cum_income = c(0, income_cum))
}

# Plot
lorenz_dt <- dt[country == "BRA" & year == 2022, lorenz(consumption_ppp, wgt)]
ggplot(lorenz_dt, aes(cum_pop, cum_income)) +
  geom_line(color = WBCOLORS["blue"]) +
  geom_abline(slope = 1, linetype = "dashed") +
  labs(x = "Cumulative Population Share", y = "Cumulative Income Share") +
  theme_wb()
```

## Survey-Weighted Poverty Rates

```r
library(srvyr)

svy <- dt |> as_survey_design(weights = wgt, strata = stratum, ids = psu)

# Poverty rate with design-based SE
svy |>
  mutate(poor = consumption_ppp < 2.15) |>
  group_by(country, year) |>
  summarise(
    headcount = survey_mean(poor, vartype = "ci"),
    gap       = survey_mean(pmax(0, (2.15 - consumption_ppp) / 2.15) * poor,
                            vartype = "se")
  )
```

## Decomposition (Shapley / Datt-Ravallion)

```r
# Poverty change decomposition: growth vs. redistribution
# Growth component: change in mean holding distribution fixed
# Redistribution component: change in distribution holding mean fixed

decompose_poverty <- function(y0, y1, w0, w1, line) {
  mu0 <- weighted.mean(y0, w0)
  mu1 <- weighted.mean(y1, w1)

  # Scale y0 to have mean mu1 (pure growth)
  y0_scaled <- y0 * (mu1 / mu0)

  growth_component <- fgt(y0_scaled, line, w0, 0) - fgt(y0, line, w0, 0)
  redist_component <- fgt(y1, line, w1, 0) - fgt(y0_scaled, line, w0, 0)

  list(growth = growth_component, redistribution = redist_component)
}
```

## Naming Conventions

| Convention | Meaning |
|------------|---------|
| `_ppp` suffix | 2017 PPP USD |
| `_lcu` suffix | Local currency units |
| `_pc` suffix | Per capita |
| `wgt` | Survey weight |
| `hh_wgt` | Household weight |
| `ind_wgt` | Individual weight (usually `hh_wgt × hh_size`) |
| `poor` | Binary: 1 if consumption_ppp < poverty line |
