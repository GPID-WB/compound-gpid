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

### Forgetting qDT() after fgroup_by pipe operations

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
