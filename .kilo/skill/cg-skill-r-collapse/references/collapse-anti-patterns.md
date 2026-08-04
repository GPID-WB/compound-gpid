# collapse Anti-Patterns

Common mistakes in R code using `collapse`. These apply regardless of whether the project uses `data.table` or tidyverse for manipulation.

---

### Using set_collapse(mask = ...) to hide function names

**Problem:** Masking base R functions makes code unreadable for team members and external readers who don't know about the masking.

**Wrong:**
```r
set_collapse(mask = "manip")  # Now subset() means fsubset(), transform() means ftransform()
dt |> subset(year > 2010) |> transform(log_y = log(y))
```

**Right:**
```r
dt |> fsubset(year > 2010) |> ftransform(log_y = log(y))
```

**Why it matters:** Explicit `f`-prefixed names tell every reader exactly which function is running.

---

### Forgetting qDT() after fgroup_by pipe

**Problem:** `fgroup_by() |> fmean()` on a data.table returns a non-over-allocated data.table. Using `:=` on it triggers a warning.

**Wrong:**
```r
result <- dt |> fgroup_by(region) |> fmean(w = weight)
result[, new_col := 1]  # Warning about over-allocation
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

### Changing na.rm globally in welfare/statistics scripts

**Problem:** `set_collapse(na.rm = FALSE)` changes the global default. All subsequent calls to `fmean`, `fsum`, etc. will return `NA` if any input has missing values — including welfare calculations that assume NA is skipped.

**Wrong:**
```r
set_collapse(na.rm = FALSE)
# ... later in the same script ...
fmean(dt$welfare, g = dt$region, w = dt$weight)  # Returns NA silently
```

**Right:**
```r
# Override per call if you need non-default behavior
fmean(dt$welfare, g = dt$region, w = dt$weight, na.rm = FALSE)
# Or restore afterward
set_collapse(na.rm = FALSE)
# ... non-welfare calculations ...
set_collapse(na.rm = TRUE)  # Restore before welfare work
```

---

### Using base R aggregation when collapse is available

**Problem:** `mean()`, `weighted.mean()` lack the `g` grouping argument and are slower. They require split-apply-combine patterns.

**Wrong:**
```r
dt[, weighted.mean(welfare, weight), by = region]   # base R, no SE support
dt |> group_by(region) |> summarise(m = weighted.mean(welfare, weight))  # slow
```

**Right:**
```r
fmean(dt$welfare, g = dt$region, w = dt$weight)
```

---

### Using ftransform() when you need sequential column references

**Problem:** `ftransform()` evaluates all RHS expressions simultaneously. You cannot reference a newly created column in the same call.

**Wrong:**
```r
ftransform(dt,
  welf_log  = log(welfare),
  welf_log2 = welf_log^2   # Error: welf_log doesn't exist yet at evaluation
)
```

**Right:**
```r
fmutate(dt,
  welf_log  = log(welfare),
  welf_log2 = welf_log^2   # Works: fmutate evaluates sequentially
)
```

---

### Applying srvyr for simple weighted statistics

**Problem:** Creating a full survey design object just to compute a weighted mean adds unnecessary overhead. `srvyr` is for complex survey SE estimation, not point estimates.

**Wrong:**
```r
svy <- dt |> as_survey_design(ids = psu, strata = stratum, weights = weight)
svy |> group_by(region) |> summarise(mean_welfare = survey_mean(welfare))
```

**Right (point estimates):**
```r
fmean(dt$welfare, g = dt$region, w = dt$weight)
```

**Right (design-based SEs required):**
```r
# Use srvyr only when you specifically need design-based standard errors
```
