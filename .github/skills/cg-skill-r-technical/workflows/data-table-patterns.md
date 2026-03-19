# data.table + collapse Patterns

`data.table` for manipulation (filtering, joins, reshaping, `:=`). `collapse` for statistical computing (grouped/weighted stats, transformations, aggregation). They work seamlessly together — collapse functions operate directly on data.table objects.

> **Full collapse API**: For global options (`set_collapse`), the complete Fast Statistical Function signatures, all 10 TRA types, GRP object structure, and attribute preservation rules, see [`cg-skill-r-analytical/references/collapse-reference.md`](../../cg-skill-r-analytical/references/collapse-reference.md).

## When to Use Which

| Operation | Tool | Example |
|-----------|------|---------|
| Row filtering | data.table | `dt[age > 30]` |
| Column creation | data.table | `dt[, new := expr]` |
| Joins | data.table | `Y[X, on = "key"]` |
| Reshaping | data.table / collapse | `melt()` / `pivot()` |
| Conditional logic | data.table | `fifelse()`, `fcase()` |
| I/O | data.table | `fread()`, `fwrite()` |
| Weighted mean/sum/sd | collapse | `fmean(x, g, w)` |
| Aggregation | collapse | `collap(dt, ~ g, fmean, w = ~ w)` |
| Group centering/scaling | collapse | `fwithin()`, `fscale()` |
| Lags/diffs/growth | collapse | `flag()`, `fdiff()`, `fgrowth()` |
| Summary stats | collapse | `qsu()`, `descr()` |

## data.table Core: DT[i, j, by]

```r
dt[age > 30]                                                    # Filter
dt[, .(mean_inc = mean(income)), by = region]                   # Aggregate (base R mean — EDA only; use fmean() for GPID work)
dt[, log_income := log(income)]                                 # Add column
dt[age > 65, elderly := TRUE]                     # Conditional assignment
dt[, temp_col := NULL]                            # Remove column
```

## collapse Inside data.table

collapse functions work directly in `dt[, j, by]`:

```r
# collapse for statistical computing in j
dt[, .(mean_welf = fmean(welfare, w = weight),
       sd_welf   = fsd(welfare, w = weight),
       med_welf  = fmedian(welfare, w = weight),
       n         = fnobs(welfare)),
   by = region]

# collapse for column creation
dt[, welfare_centered := fwithin(welfare, region, weight)]
dt[, welfare_scaled := fscale(welfare, region, weight)]
dt[, welfare_pct := fsum(welfare, region, TRA = "%")]
dt[, welfare_lag := flag(welfare, 1, country)]  # lag within country

# collapse for row-level operations
dt[, region_mean := fmean(welfare, region, weight, TRA = "replace")]
```

## Aggregation: collap() vs dt[, j, by]

```r
# data.table aggregation (base R mean — unweighted, for EDA/diagnostics only)
# For GPID published work: use fmean(x, g, w = weight) instead
dt[, .(mean_w = mean(welfare), n = .N), by = region]

# collapse aggregation (faster, native weight support)
collap(dt, ~ region, fmean, w = ~ weight, cols = c("welfare", "income"))

# collapse multi-function aggregation
collap(dt, ~ region, list(fmean, fsd, fnobs), w = ~ weight, cols = "welfare")

# collapse custom aggregation
collap(dt, ~ region,
       custom = list(fmean = "welfare", fsum_uw = "hhsize"),
       w = ~ weight)
```

## Joins

```r
# data.table joins (primary tool for joins)
result <- Y[X, on = "key"]              # Left join
result <- X[Y, on = "key", nomatch = 0] # Inner join
X[Y, on = .(id, year)]                  # Multi-column
X[!Y, on = "key"]                       # Anti join
X[Y, on = "date", roll = TRUE]          # Rolling join

# collapse join (simpler syntax, verbose output)
join(X, Y, on = "key", how = "left")
join(X, Y, on = c("id" = "key"), how = "inner", verbose = TRUE)
```

## Reshaping

```r
# data.table reshape
melt(dt, id.vars = "id", measure.vars = c("y2020", "y2021"),
     variable.name = "year", value.name = "value")
dcast(dt, id ~ year, value.var = "income")

# collapse pivot (simpler for common cases)
pivot(dt, ids = "id", values = c("y2020", "y2021"), how = "longer",
      names = list(variable = "year", value = "value"))
pivot(dt, ids = "id", values = "income", names = "year", how = "wider")
```

## Performance Patterns

```r
# data.table: setkey for fast lookups
setkey(dt, id)
dt[.(target_id)]

# data.table: fast conditional
dt[, category := fcase(
  income > 100000, "high",
  income > 50000,  "medium",
  default = "low"
)]

# collapse: pre-compute grouping for repeated use
g <- GRP(dt, ~ region + year)
fmean(dt$welfare, g = g, w = dt$weight)
fsd(dt$welfare, g = g, w = dt$weight)

# data.table: read only needed columns
dt <- fread("file.csv", select = c("id", "income", "region"))
```

## Assignment by Reference

```r
dt[, log_income := log(income)]                   # data.table :=
dt[, c("a", "b") := .(fun_a(x), fun_b(y))]      # Multiple columns

# collapse settransform (also modifies in place)
settransform(dt, log_income = log(income))
settransformv(dt, c("welfare", "income"), log)    # Apply to multiple columns
```

## .SD and .SDcols

```r
# Apply function to multiple columns — use collap() for weighted multi-column aggregation (preferred)
# Prefer: collap(dt, ~ region, fmean, w = ~ weight, cols = c("welfare", "income"))
dt[, lapply(.SD, fmean, w = weight), .SDcols = c("welfare", "income"), by = region]

# First/last row per group
dt[, .SD[1], by = group]
```

## Quick Conversion

```r
qDT(x)    # Anything to data.table (fast, minimal checks)
qDF(x)    # To data.frame
qM(x)     # To matrix
```
