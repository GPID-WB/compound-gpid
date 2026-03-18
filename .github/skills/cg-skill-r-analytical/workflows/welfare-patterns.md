# Welfare and Poverty Patterns

This is the highest-risk area for AI-assisted code in GPID. Copilot frequently generates poverty and inequality code that looks correct but silently produces wrong numbers — wrong weights, wrong units, wrong formula. Every pattern here exists because the mistake has been made before, or because Copilot is known to get it wrong.

## PPP Adjustment Pipeline

Poverty measurement requires tracking monetary units through every transformation. The pipeline is:

```
LCU nominal → LCU real → PPP USD
```

Each step has a specific deflator or conversion factor. Losing track of which unit a variable is in is the single most common source of wrong poverty numbers.

### The Unit Tracking Rule

Every welfare variable name should encode its unit. This is not optional style — it is a safety mechanism.

```r
# WRONG — what unit is "welfare" in? Nobody knows.
dt[, welfare := consumption / hhsize]

# RIGHT — unit is explicit in the variable name
dt[, welfare_lcu_nominal := consumption_lcu_nominal / hhsize]
dt[, welfare_lcu_real := welfare_lcu_nominal / cpi_deflator]
dt[, welfare_ppp := welfare_lcu_real / ppp_factor]
```

### Full PPP Conversion

```r
# Step 1: Per capita (if not already)
dt[, welf_pc_lcu_nom := total_consumption / hhsize]

# Step 2: Deflate to base year prices (real LCU)
# cpi_deflator = CPI_current_year / CPI_base_year
dt[, welf_pc_lcu_real := welf_pc_lcu_nom / cpi_deflator]

# Step 3: Convert to PPP dollars
# ppp_factor = PPP conversion factor (LCU per international dollar)
dt[, welf_pc_ppp := welf_pc_lcu_real / ppp_factor]

# Step 4: Convert to daily (if annual)
dt[, welf_pc_ppp_day := welf_pc_ppp / 365]
```

### Common PPP Mistakes

**Applying PPP before deflating:**
```r
# WRONG — PPP factors are for a specific base year
dt[, welfare_ppp := welfare_lcu_nominal / ppp_factor]

# RIGHT — deflate to the PPP base year first
dt[, welfare_lcu_real := welfare_lcu_nominal / cpi_deflator]
dt[, welfare_ppp := welfare_lcu_real / ppp_factor]
```

**Mixing PPP vintages:**
```r
# WRONG — 2011 PPP factor applied to 2017 PPP poverty line
dt[, poor := welfare_2011ppp < 2.15]  # $2.15 is a 2017 PPP line

# RIGHT — same PPP vintage throughout
dt[, poor := welfare_2017ppp < 2.15]
```

**Dividing when you should multiply (or vice versa):**
```r
# The PPP factor converts FROM local currency TO PPP dollars
# So you DIVIDE by the PPP factor
dt[, welfare_ppp := welfare_lcu_real / ppp_factor]

# Copilot sometimes generates multiplication — always verify direction
```

## FGT Poverty Indices

The Foster-Greer-Thorbecke (FGT) family of poverty measures. All three must be computed with survey weights.

### FGT(0) — Headcount Ratio

The share of the population below the poverty line.

```r
# Using srvyr (preferred — correct standard errors)
headcount <- svy |>
  summarise(
    fgt0 = survey_mean(welf_pc_ppp_day < poverty_line, vartype = "ci")
  )

# Manual computation with data.table (point estimate only — no correct SEs)
# Use only for quick checks, never for published numbers
dt[, weighted.mean(welf_pc_ppp_day < poverty_line, w = weight)]
```

### FGT(1) — Poverty Gap

The average depth of poverty across the population (how far below the line, on average).

```r
# Compute the normalized gap for each household
svy <- svy |>
  mutate(
    gap = ifelse(welf_pc_ppp_day < poverty_line,
                 (poverty_line - welf_pc_ppp_day) / poverty_line,
                 0)
  )

# FGT(1)
poverty_gap <- svy |>
  summarise(
    fgt1 = survey_mean(gap, vartype = "ci")
  )
```

**Critical:** The gap is `(z - y) / z` for the poor and `0` for the non-poor, then averaged over the ENTIRE population (not just the poor). Copilot frequently averages only over the poor, which gives the wrong number.

```r
# WRONG — averages gap only among the poor
wrong_fgt1 <- svy |>
  filter(welf_pc_ppp_day < poverty_line) |>
  summarise(fgt1 = survey_mean(gap))

# RIGHT — averages gap over entire population (non-poor contribute 0)
right_fgt1 <- svy |>
  summarise(fgt1 = survey_mean(gap))
```

### FGT(2) — Poverty Severity

The squared poverty gap — gives more weight to those further below the line.

```r
svy <- svy |>
  mutate(
    gap_sq = ifelse(welf_pc_ppp_day < poverty_line,
                    ((poverty_line - welf_pc_ppp_day) / poverty_line)^2,
                    0)
  )

severity <- svy |>
  summarise(
    fgt2 = survey_mean(gap_sq, vartype = "ci")
  )
```

### Complete FGT Computation

```r
# All three FGT indices in one block
poverty_line <- 2.15  # $2.15/day, 2017 PPP

svy <- svy |>
  mutate(
    poor     = welf_pc_ppp_day < poverty_line,
    gap      = ifelse(poor, (poverty_line - welf_pc_ppp_day) / poverty_line, 0),
    gap_sq   = gap^2
  )

fgt_results <- svy |>
  summarise(
    fgt0 = survey_mean(poor, vartype = c("se", "ci")),
    fgt1 = survey_mean(gap, vartype = c("se", "ci")),
    fgt2 = survey_mean(gap_sq, vartype = c("se", "ci"))
  )

# FGT by region
fgt_by_region <- svy |>
  group_by(region) |>
  summarise(
    fgt0 = survey_mean(poor, vartype = "ci"),
    fgt1 = survey_mean(gap, vartype = "ci"),
    fgt2 = survey_mean(gap_sq, vartype = "ci"),
    n    = unweighted(n())
  ) |>
  as.data.table()
```

## Weighted vs Unweighted: When Each Is Appropriate

| Statistic | Weighted? | Why |
|-----------|-----------|-----|
| National poverty rate | Yes | Represents the population |
| Regional poverty rate | Yes | Represents regional population |
| Mean welfare | Yes | Population-representative estimate |
| Regression coefficient | Depends | Yes for descriptive; debatable for causal |
| Sample size | No | Count of observations, not people |
| Data quality checks | No | Checking the survey data itself |
| Correlation for EDA | Usually no | Exploring data structure |

**The default for GPID published statistics is always weighted.** Unweighted analysis is for diagnostics and data exploration, not for numbers that appear in reports.

```r
# Population-representative mean (for reports)
svy |> summarise(mean_welfare = survey_mean(welf_pc_ppp_day))

# Unweighted mean (for data quality checks only)
dt[, mean(welf_pc_ppp_day, na.rm = TRUE)]

# Sample size (always unweighted)
dt[, .N]
dt[, .N, by = region]
```

## Gini Coefficient

The Gini coefficient measures inequality on a 0-1 scale (0 = perfect equality, 1 = perfect inequality).

```r
# Weighted Gini using the survey design
# The acid package or manual computation is needed — srvyr doesn't have a built-in Gini

# Manual weighted Gini computation
compute_gini <- function(welfare, weight) {
  # Sort by welfare
  ord <- order(welfare)
  w <- weight[ord]
  y <- welfare[ord]

  # Cumulative weight shares
  cum_w <- cumsum(w) / sum(w)
  # Cumulative welfare shares
  cum_wy <- cumsum(w * y) / sum(w * y)

  # Gini = 1 - 2 * area under Lorenz curve
  # Trapezoidal approximation
  n <- length(y)
  gini <- 1 - sum((cum_w[2:n] - cum_w[1:(n-1)]) *
                   (cum_wy[2:n] + cum_wy[1:(n-1)]))

  return(gini)
}

# Apply to data
gini_national <- dt[, compute_gini(welf_pc_ppp_day, weight)]

# Gini by region
gini_by_region <- dt[, .(gini = compute_gini(welf_pc_ppp_day, weight)),
                     by = region]
```

## Welfare Shares by Decile

```r
# Compute weighted decile assignments
dt[, decile := {
  cum_wt <- cumsum(weight[order(welf_pc_ppp_day)]) / sum(weight)
  # Assign deciles based on cumulative weight
  cuts <- findInterval(cum_wt, seq(0, 1, 0.1)) + 1L
  cuts[cuts > 10L] <- 10L
  # Map back to original order
  result <- integer(.N)
  result[order(welf_pc_ppp_day)] <- cuts
  result
}]

# Compute welfare share by decile
decile_shares <- dt[, .(
  total_welfare = sum(welf_pc_ppp_day * weight),
  pop_share     = sum(weight)
), by = decile]

decile_shares[, welfare_share := total_welfare / sum(total_welfare)]
decile_shares[, pop_pct := pop_share / sum(pop_share)]
setorder(decile_shares, decile)
```

## Multiple Poverty Lines

GPID typically reports at three international poverty lines. Compute all three in one pass:

```r
poverty_lines <- c(
  extreme = 2.15,   # International Poverty Line
  lower   = 3.65,   # Lower-middle income class
  upper   = 6.85    # Upper-middle income class
)

svy <- svy |>
  mutate(
    poor_215 = welf_pc_ppp_day < 2.15,
    poor_365 = welf_pc_ppp_day < 3.65,
    poor_685 = welf_pc_ppp_day < 6.85,
    gap_215  = ifelse(poor_215, (2.15 - welf_pc_ppp_day) / 2.15, 0),
    gap_365  = ifelse(poor_365, (3.65 - welf_pc_ppp_day) / 3.65, 0),
    gap_685  = ifelse(poor_685, (6.85 - welf_pc_ppp_day) / 6.85, 0)
  )

multi_line <- svy |>
  summarise(
    fgt0_215 = survey_mean(poor_215, vartype = "ci"),
    fgt0_365 = survey_mean(poor_365, vartype = "ci"),
    fgt0_685 = survey_mean(poor_685, vartype = "ci"),
    fgt1_215 = survey_mean(gap_215, vartype = "ci"),
    fgt1_365 = survey_mean(gap_365, vartype = "ci"),
    fgt1_685 = survey_mean(gap_685, vartype = "ci")
  )
```

## Verification Checklist

Before publishing any poverty or inequality number:

1. **Unit check:** What unit is the welfare variable in? Is it daily PPP? Annual LCU? Document it.
2. **Weight check:** Is the statistic weighted? Should it be? Are you using the correct weight variable (household weight vs individual weight)?
3. **Population check:** Are FGT indices averaged over the ENTIRE population (including non-poor)?
4. **PPP vintage check:** Is the poverty line in the same PPP vintage as the welfare variable?
5. **Design check:** Is the survey design declared and propagated through all computations?
6. **Reasonableness check:** Does the number make sense? Is the poverty rate between 0 and 1? Is the Gini between 0 and 1? Is the headcount at $2.15 lower than at $6.85?
7. **Cross-check:** Can you reproduce the number with a different method or in Stata?
