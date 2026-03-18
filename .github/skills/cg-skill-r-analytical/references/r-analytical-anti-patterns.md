# Analytical R Anti-Patterns

Common mistakes in analytical R code. Each entry: what the mistake is, why it matters, what goes wrong, and what to do instead.

---

## Survey Analysis Anti-Patterns

### Bypassing the survey design for "quick" calculations

**Problem:** Computing weighted statistics directly on the data.table instead of through the survey design object. The point estimate may be correct, but standard errors, confidence intervals, and p-values will be wrong because clustering and stratification are ignored.

**Wrong:**
```r
# "I'll just use weighted.mean, it's faster"
dt[, weighted.mean(welfare, weight), by = region]
```

**Right:**
```r
svy |>
  group_by(region) |>
  summarise(mean_welfare = survey_mean(welfare, vartype = "ci"))
```

**Why it matters:** A poverty headcount of 25.3% ± 0.8pp vs 25.3% ± 2.1pp changes whether a trend is statistically significant. Published numbers with wrong standard errors undermine the credibility of all GPID statistics.

---

### Redeclaring the survey design in different places

**Problem:** Creating multiple survey design objects with slightly different specifications (different weights, strata, or PSU variables) at different points in the analysis. Results become internally inconsistent.

**Wrong:**
```r
# In one script:
svy1 <- dt |> as_survey_design(ids = psu, strata = strat, weights = wt)

# In another script, slightly different:
svy2 <- dt |> as_survey_design(ids = cluster, strata = stratum, weights = weight)
```

**Right:**
```r
# Declare ONCE, at the top of the analysis, and pass svy to all functions
svy <- dt |>
  as_survey_design(ids = psu, strata = stratum, weights = weight, nest = TRUE)

# Everything downstream uses this single object
```

**Why it matters:** If `svy1` and `svy2` use different variable names (which might even be the same column), you cannot tell whether differences in results are real or due to design mismatch.

---

### Subsetting data instead of filtering the design

**Problem:** Filtering the raw data and re-creating a survey design for a subpopulation. This changes the variance estimation because it treats the subset as the full sample.

**Wrong:**
```r
dt_urban <- dt[urban == 1]
svy_urban <- dt_urban |>
  as_survey_design(ids = psu, strata = stratum, weights = weight)
```

**Right:**
```r
svy_urban <- svy |> filter(urban == 1)
```

**Why it matters:** Variance estimation in complex surveys depends on the full sample structure. Subsetting the data and re-declaring the design produces overconfident standard errors for subpopulations.

---

## Welfare Measurement Anti-Patterns

### Averaging the poverty gap only among the poor

**Problem:** Computing FGT(1) as the average gap among poor households instead of averaging over the entire population. This gives the "income gap ratio" (a different statistic), not the FGT poverty gap.

**Wrong:**
```r
svy |>
  filter(welfare < poverty_line) |>
  summarise(fgt1 = survey_mean((poverty_line - welfare) / poverty_line))
```

**Right:**
```r
svy |>
  mutate(gap = ifelse(welfare < poverty_line,
                      (poverty_line - welfare) / poverty_line, 0)) |>
  summarise(fgt1 = survey_mean(gap))
```

**Why it matters:** The FGT poverty gap for a country might be 0.05 (correct) vs 0.20 (wrong). The wrong number is 4x larger and tells a completely different story about poverty depth.

---

### Losing track of PPP units

**Problem:** Applying a poverty line denominated in one PPP vintage to welfare data in a different vintage, or comparing welfare in local currency to a PPP poverty line.

**Wrong:**
```r
# welfare is in 2011 PPP, but $2.15 is a 2017 PPP line
dt[, poor := welfare_2011ppp < 2.15]
```

**Right:**
```r
# Ensure both are in the same PPP vintage
dt[, poor := welfare_2017ppp < 2.15]
```

**Why it matters:** PPP conversion factors differ substantially between vintages. 2011 and 2017 PPP factors can differ by 20-30% for some countries. Using the wrong vintage produces poverty rates that are off by double-digit percentage points.

---

### Using unweighted means for published statistics

**Problem:** Reporting `mean()` instead of survey-weighted means in tables or charts that will appear in publications.

**Wrong:**
```r
# For a table in a report
dt[, .(mean_welfare = mean(welfare)), by = region]
```

**Right:**
```r
svy |>
  group_by(region) |>
  summarise(mean_welfare = survey_mean(welfare, vartype = "ci")) |>
  as.data.table()
```

**Why it matters:** Unweighted means do not represent the population. A region with oversampled rural areas will show lower mean welfare than the true population mean. This is not a minor issue — it can reverse regional rankings.

---

## haven / Stata Migration Anti-Patterns

### Using as_factor() on numeric variables

**Problem:** Converting a labelled numeric variable (like an urban/rural dummy) to a factor, then trying to use it in calculations.

**Wrong:**
```r
dt[, urban := as_factor(urban)]
dt[, mean(urban)]  # NA — can't average a factor
```

**Right:**
```r
# For calculations: strip labels
dt[, urban := zap_labels(urban)]

# For tabulation: convert to factor
dt[, urban_label := as_factor(urban)]
```

**Why it matters:** Silently converts a numeric dummy to a character factor. Downstream calculations fail or produce NA without warning in some contexts.

---

### Ignoring Stata label metadata entirely

**Problem:** Using `zap_labels()` on everything and losing the documentation that Stata labels provide. Two months later, nobody knows what `educ == 3` means.

**Wrong:**
```r
dt <- as.data.table(zap_labels(read_dta("survey.dta")))
# What is education level 3? Who knows.
```

**Right:**
```r
dt <- as.data.table(read_dta("survey.dta"))
# Keep a reference of what the codes mean
educ_labels <- val_labels(dt$education)
# Then zap for computation
dt[, education := zap_labels(education)]
```

**Why it matters:** Label metadata is the data dictionary. Discarding it forces everyone to look up variable definitions in the original survey documentation every time.

---

## Visualization Anti-Patterns

### Using theme_minimal() instead of theme_wb()

**Problem:** Producing charts with default ggplot2 or theme_minimal() styling for GPID publications.

**Wrong:**
```r
ggplot(dt, aes(x = year, y = headcount)) +
  geom_line() +
  theme_minimal()
```

**Right:**
```r
ggplot(dt, aes(x = year, y = headcount)) +
  geom_line(lineend = "round") +
  theme_wb(chartType = "line")
```

**Why it matters:** Institutional publications require consistent branding. Charts that don't match the World Bank style stand out in reports and presentations, and signal a lack of attention to quality.

---

### Forgetting lineend = "round" and width = 0.66

**Problem:** Using ggplot2 defaults for line endings and bar widths instead of wbplot conventions.

**Wrong:**
```r
geom_line()                    # butt lineend (default)
geom_bar(stat = "identity")   # width = 0.9 (default)
```

**Right:**
```r
geom_line(lineend = "round")
geom_bar(stat = "identity", width = 0.66)
```

**Why it matters:** wbplot does not override these defaults. You must set them manually on every chart.

---

## Econometrics Anti-Patterns

### Forgetting to cluster standard errors

**Problem:** Running fixed effects regressions without clustering, producing standard errors that are too small.

**Wrong:**
```r
m <- feols(log_welfare ~ education + age | region + year, data = dt)
# Default: iid standard errors
```

**Right:**
```r
m <- feols(log_welfare ~ education + age | region + year,
           vcov = ~psu, data = dt)
```

**Why it matters:** Unclustered standard errors with panel or grouped data are biased downward, often dramatically. Coefficients appear significant when they are not.

---

### Using standard TWFE for staggered treatment

**Problem:** Estimating a two-way fixed effects model when treatment rolls out at different times across units. The standard TWFE estimator is biased under treatment effect heterogeneity.

**Wrong:**
```r
m <- feols(outcome ~ treated | unit + year, data = dt)
```

**Right:**
```r
m <- feols(outcome ~ sunab(first_treated, year) | unit + year, data = dt)
```

**Why it matters:** The TWFE estimate can be wrong in sign when treatment effects vary across cohorts. This has been demonstrated in econometrics literature (Goodman-Bacon 2021, Sun & Abraham 2021) and is not a theoretical curiosity — it affects real estimates.
