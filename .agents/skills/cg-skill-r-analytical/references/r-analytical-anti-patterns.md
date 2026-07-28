# Analytical R Anti-Patterns

Common mistakes in analytical R code. Each entry: what the mistake is, why it matters, wrong example, right example.

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

**Why it matters:** A survey with 5% missing welfare silently computes poverty over 95% of the population as if it were 100%. Negative welfare is physically impossible and produces FGT gap values above 1. Both are P1 data corruption risks. See `.cg-docs/solutions/data-quality/2026-03-18-collapse-na-rm-global-option-welfare-risk.md` in the Compound GPID repository for the full failure modes.

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

> Load `cg-skill-r-technical` for the same pattern in non-welfare contexts.

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

> **Collapse anti-patterns** (masking, `qDT()`, `GRP()` pre-computation)
> are in the `cg-skill-r-collapse` skill.
> The patterns below are specific to analytical work.

*No analytical-specific collapse anti-patterns at this time. General collapse anti-patterns are in the shared file above.*

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
