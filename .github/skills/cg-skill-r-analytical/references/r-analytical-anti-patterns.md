# Analytical R Anti-Patterns

Common mistakes in analytical R code. The team hierarchy is collapse > data.table > tidyverse. Each entry: what the mistake is, why it matters, wrong example, right example.

---

## Tool Hierarchy Anti-Patterns

### Using base R or tidyverse for weighted statistics when collapse is available

**Problem:** Computing weighted means with `weighted.mean()`, `dplyr::summarise()`, or manual formulas instead of collapse. These are slower and don't support grouping natively.

**Wrong:**
```r
dt[, weighted.mean(welfare, weight), by = region]  # base R, no SE support
dt %>% group_by(region) %>% summarise(m = weighted.mean(welfare, weight))  # slow
```

**Right:**
```r
fmean(dt$welfare, g = dt$region, w = dt$weight)  # collapse: fastest, explicit
```

**Why it matters:** collapse functions are 10-100x faster and have consistent `f*(x, g, w)` signatures that make code readable and auditable.

---

### Using srvyr for simple weighted statistics

**Problem:** Declaring a full survey design object just to compute a weighted mean. `srvyr` adds overhead (design declaration, method dispatch) that's unnecessary for point estimates.

**Wrong:**
```r
svy <- dt |> as_survey_design(ids = psu, strata = stratum, weights = weight)
svy |> group_by(region) |> summarise(mean_welfare = survey_mean(welfare))
```

**Right (point estimates):**
```r
fmean(dt$welfare, g = dt$region, w = dt$weight)
```

**Right (when you need design-based SEs):**
```r
survey_mean_se(dt$welfare, w = dt$weight, psu = dt$psu, stratum = dt$stratum)
```

**Why it matters:** `srvyr` is a fallback for complex SE estimation, not the default tool. Use collapse for everything you can, fall back to srvyr only when needed.

---

## Welfare Measurement Anti-Patterns

### Computing FGT or Gini without validating welfare and weights first

**Problem:** Running poverty/inequality calculations without pre-checking for NA, zero, or negative welfare values. collapse's default `na.rm = TRUE` silently drops NA rows and computes statistics over fewer observations without warning.

**Wrong:**
```r
# No validation — NA welfare silently excluded; negative welfare inflates FGT(1)
dt[, gap := fifelse(welf_pc_ppp_day < 2.15, (2.15 - welf_pc_ppp_day) / 2.15, 0)]
fgt1 <- fmean(dt$gap, w = dt$weight)
```

**Right:**
```r
# Always validate before FGT/Gini
stopifnot(
  !anyNA(dt$welf_pc_ppp_day), !anyNA(dt$weight),
  all(dt$weight > 0),
  all(dt$welf_pc_ppp_day > 0)  # negative welfare inflates FGT(1) beyond 1
)
dt[, gap := fifelse(welf_pc_ppp_day < 2.15, (2.15 - welf_pc_ppp_day) / 2.15, 0)]
fgt1 <- fmean(dt$gap, w = dt$weight)
```

**Why it matters:** A survey with 5% missing welfare silently computes poverty over 95% of the population as if it were 100%. Negative welfare is physically impossible and produces FGT gap values above 1. Both are P1 data corruption risks. See the [collapse na.rm solution](.cg-docs/solutions/data-quality/2026-03-18-collapse-na-rm-global-option-welfare-risk.md) for the full failure modes.

---

### Averaging the poverty gap only among the poor

**Problem:** Computing FGT(1) as the average gap among poor households instead of the entire population.

**Wrong:**
```r
fmean(dt[poor == TRUE]$gap, w = dt[poor == TRUE]$weight)
```

**Right:**
```r
fmean(dt$gap, w = dt$weight)  # gap is 0 for non-poor
```

**Why it matters:** The wrong number can be 4x larger. This is the most common FGT error.

---

### Losing track of PPP units

**Problem:** Applying a poverty line in one PPP vintage to welfare data in a different vintage.

**Wrong:**
```r
dt[, poor := welfare_2011ppp < 2.15]  # $2.15 is 2017 PPP
```

**Right:**
```r
dt[, poor := welfare_2017ppp < 2.15]
```

**Why it matters:** PPP unit mismatches produce poverty rates that are silently wrong. See [Welfare Patterns](../workflows/welfare-patterns.md) for the full unit-tracking naming convention — every welfare variable name must encode its unit (e.g., `welf_pc_ppp_day`).

---

### Aggregate-then-merge instead of using TRA

> See also the same pattern in [r-technical-anti-patterns.md](../../cg-skill-r-technical/references/r-technical-anti-patterns.md) for non-welfare contexts.

**Problem:** Computing group statistics and merging back instead of using the `TRA` argument.

**Wrong:**
```r
# Two passes + merge to demean within groups
group_means <- dt[, .(mean_w = fmean(welfare, w = weight)), by = region]
dt <- group_means[dt, on = "region"]
dt[, welfare_centered := welfare - mean_w]
```

**Right:**
```r
# One call with TRA
dt[, welfare_centered := fmean(welfare, g = region, w = weight, TRA = "-")]
# Or equivalently:
dt[, welfare_centered := fwithin(welfare, region, weight)]
```

**Why it matters:** The one-call version avoids a full merge and is 2-3x faster on large surveys. The `TRA` argument is available on all Fast Statistical Functions.

---

### Using unweighted means for published statistics

**Wrong:**
```r
dt[, .(mean_welfare = mean(welfare)), by = region]  # unweighted
```

**Right:**
```r
fmean(dt$welfare, g = dt$region, w = dt$weight)  # collapse, weighted
```

---

## collapse Anti-Patterns

### Using set_collapse(mask = ...) to hide function names

> See also the same pattern in [r-technical-anti-patterns.md](../../cg-skill-r-technical/references/r-technical-anti-patterns.md).

**Problem:** Masking base R functions with collapse equivalents makes code unreadable for team members who don't know about the masking.

**Wrong:**
```r
set_collapse(mask = "manip")  # Now subset() is fsubset(), transform() is ftransform()
dt |> subset(year > 2010) |> transform(log_y = log(y))
```

**Right:**
```r
dt |> fsubset(year > 2010) |> ftransform(log_y = log(y))
```

**Why it matters:** Explicit `f`-prefixed names tell every reader exactly which function is running.

---

### Forgetting qDT() after fgroup_by pipe

**Problem:** `fgroup_by() |> fmean()` on a data.table returns a non-overallocated data.table. Using `:=` on it triggers a warning.

**Wrong:**
```r
result <- dt |> fgroup_by(region) |> fmean(w = weight)
result[, new_col := 1]  # Warning about overallocation
```

**Right:**
```r
result <- dt |> fgroup_by(region) |> fmean(w = weight) |> qDT()
result[, new_col := 1]  # Works cleanly
```

---

### Not pre-computing GRP objects for repeated grouped operations

**Problem:** Passing raw grouping vectors to multiple collapse functions. Each call recomputes the grouping.

**Wrong:**
```r
fmean(dt$welfare, g = dt$region, w = dt$weight)
fsd(dt$welfare, g = dt$region, w = dt$weight)
fnobs(dt$welfare, g = dt$region)
# Grouping computed 3 times
```

**Right:**
```r
g <- GRP(dt, ~ region)
fmean(dt$welfare, g = g, w = dt$weight)
fsd(dt$welfare, g = g, w = dt$weight)
fnobs(dt$welfare, g = g)
# Grouping computed once, reused 3 times
```

---

## haven / Stata Migration Anti-Patterns

### Using as_factor() on numeric variables

**Wrong:**
```r
dt[, urban := as_factor(urban)]
fmean(dt$urban)  # Error — can't average a factor
```

**Right:**
```r
dt[, urban := zap_labels(urban)]  # For calculations
dt[, urban_label := as_factor(urban)]  # For tabulation
```

---

## Visualization Anti-Patterns

### Using theme_minimal() instead of theme_wb()

**Wrong:**
```r
ggplot(dt, aes(x = year, y = headcount)) + geom_line() + theme_minimal()
```

**Right:**
```r
ggplot(dt, aes(x = year, y = headcount)) +
  geom_line(lineend = "round") + theme_wb(chartType = "line")
```

---

### Forgetting lineend = "round" and width = 0.66

**Wrong:**
```r
geom_line()                    # butt lineend
geom_bar(stat = "identity")   # width = 0.9
```

**Right:**
```r
geom_line(lineend = "round")
geom_bar(stat = "identity", width = 0.66)
```

---

## Econometrics Anti-Patterns

### Forgetting to cluster standard errors

**Wrong:**
```r
m <- feols(log_welfare ~ education + age | region + year, data = dt)
```

**Right:**
```r
m <- feols(log_welfare ~ education + age | region + year, vcov = ~psu, data = dt)
```

---

### Using standard TWFE for staggered treatment

**Wrong:**
```r
m <- feols(outcome ~ treated | unit + year, data = dt)
```

**Right:**
```r
m <- feols(outcome ~ sunab(first_treated, year) | unit + year, data = dt)
```
