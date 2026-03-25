# Shared collapse Anti-Patterns

These patterns apply to **all** R code using `collapse`, regardless of whether the work is analytical or technical. Referenced by both `cg-skill-r-analytical` and `cg-skill-r-technical`.

---

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
