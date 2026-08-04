# data.table Reference

`data.table` is a high-performance extension of R's `data.frame` for fast aggregation, ordered joins, and in-place column manipulation.

## I/O

```r
# Read (auto-detects sep, types, header)
dt <- fread("file.csv")
dt <- fread("file.csv", select = c("id", "income", "region"))  # Read only needed cols
dt <- fread("file.csv", key = "id")                            # Set key on read
dt <- fread("file.csv", nThread = 4)                           # Parallel read

# Write
fwrite(dt, "output.csv")
fwrite(dt, "output.csv.gz")  # Auto-compresses from extension
fwrite(dt, "output.csv", nThread = 4)
```

## Construction and Conversion

```r
# Create
dt <- data.table(id = 1:5, x = rnorm(5), group = c("A","A","B","B","C"))

# Convert in-place (no copy)
setDT(df)                   # data.frame to data.table, in-place
setDT(list_of_vectors)      # List to data.table

# Convert with copy
dt <- as.data.table(df)

# Convert back
setDF(dt)                   # data.table to data.frame, in-place

# Deep copy (when you need independence)
dt2 <- copy(dt)             # NOT: dt2 <- dt (just another reference)
```

## Core DT[i, j, by] Operations

```r
# Filter rows
dt[income > 50000]
dt[region == "EAP" & year > 2010]
dt[region %chin% c("EAP", "SAR")]  # Fast character %in%

# Aggregate (use collapse for weighted/fast stats)
dt[, .(count = .N, mean_inc = fmean(income, w = weight)), by = region]

# Add/modify columns by reference
dt[, log_income := log(income)]
dt[, ':='(log_income = log(income), poor = income < 2.15)]  # Multiple cols
dt[, let(log_income = log(income), poor = income < 2.15)]   # Alternative syntax

# Conditional assignment
dt[age > 65, elderly := TRUE]
dt[is.na(income), income := 0]

# Delete column
dt[, log_income := NULL]

# Chain operations
dt[income > 0][, .(n = .N, mean_inc = mean(income)), by = region][order(-mean_inc)]
```

## Conditional Logic

```r
# Fast vectorized if-else (type-stable — both branches must be same type)
dt[, category := fifelse(income > 50000, "high", "low")]
# Note: both "high" and "low" are character — types must match

# Fast CASE WHEN (shortcut for nested fifelse)
dt[, category := fcase(
  income > 100000, "high",
  income >  50000, "medium",
  income >  20000, "low",
  default          = "very_low"
)]

# Coalesce (replace NAs from prioritized candidates)
dt[, filled := fcoalesce(primary, secondary, 0L)]
```

## Keys, Indices, and Fast Lookup

```r
# Physical key (sorts rows, used for binary search)
setkey(dt, id)
dt[.(target_id)]         # Key-based lookup — very fast
dt[.(c(1L, 5L, 10L))]   # Multiple values

# Secondary index (no physical reorder, multiple allowed)
setindex(dt, region)
setindexv(dt, c("region", "year"))  # Multiple columns

# Query key/index
key(dt)
haskey(dt)
indices(dt)
```

## Joins

```r
# Left join (all rows from X)
custs[orders, on = "cust_id"]

# Inner join
orders[custs, on = "cust_id", nomatch = NULL]

# Anti-join (rows in X with no match in Y)
orders[!custs, on = "cust_id"]

# Multi-column join
X[Y, on = .(id, year)]
X[Y, on = c("id_x" = "id_y")]  # Different column names

# Non-equi join
DT1[DT2, on = .(start <= date, end >= date)]

# Rolling join (last observation carried forward)
X[Y, on = "date", roll = TRUE]

# Update join (add column from Y to X by reference)
orders[custs, on = "cust_id", name := i.name]
```

### Join type summary

| Join | Syntax | Notes |
|------|--------|-------|
| Left | `Y[X, on=]` | All rows of X |
| Right | `X[Y, on=]` | All rows of Y |
| Inner | `X[Y, on=, nomatch=NULL]` | Only matching rows |
| Anti | `X[!Y, on=]` | X rows with no match |
| Cross | `CJ(x_vals, y_vals)` | All combinations |

## Reshaping

```r
# Wide to long
melt(dt,
     id.vars      = c("id", "group"),
     measure.vars = c("y2020", "y2021"),
     variable.name = "year",
     value.name    = "value")

# Multiple measure variables simultaneously
melt(dt, id.vars = "id",
     measure.vars = patterns("^income_", "^welfare_"),
     variable.name = "year",
     value.name = c("income", "welfare"))

# Long to wide
dcast(dt, id + group ~ year, value.var = "value")
dcast(dt, id ~ year, value.var = "income", fun.aggregate = mean)
```

## .SD and .SDcols

```r
# Apply function to all numeric columns by group
dt[, lapply(.SD, mean), by = group]

# Apply to subset of columns
dt[, lapply(.SD, fmean, w = weight), by = group,
   .SDcols = c("welfare", "income")]

# .SDcols with patterns
dt[, lapply(.SD, sum), by = group, .SDcols = patterns("^val_")]

# First row per group
dt[, .SD[1], by = group]

# Last N rows per group
dt[, tail(.SD, 2), by = group]
```

**Prefer `collap()` for weighted multi-column aggregation** — it's faster than `.SD` patterns:

```r
# Preferred for GPID work with weights
collap(dt, ~ region, fmean, w = ~ weight, cols = c("welfare", "income"))
```

## Rolling Functions

```r
# Rolling mean/sum
dt[, roll_mean := frollmean(value, n = 3, align = "right", na.rm = TRUE), by = id]
dt[, roll_sum  := frollsum(value, n = 7), by = id]

# Lead/lag (for non-panel or when findex_by is not set up)
dt[, value_lag1 := shift(value, n = 1, type = "lag"), by = id]
dt[, value_lead := shift(value, n = 1, type = "lead"), by = id]
```

## NA Functions

```r
# Fill NAs
nafill(dt$x, type = "locf")  # Last observation carried forward
nafill(dt$x, type = "nocb")  # Next observation carried backward
nafill(dt$x, type = "const", fill = 0)  # Replace with constant

# In-place NA fill
setnafill(dt, type = "locf", cols = c("welfare", "income"))
```

## Column Manipulation

```r
# Rename
setnames(dt, "old_name", "new_name")
setnames(dt, c("old1", "old2"), c("new1", "new2"))
setnames(dt, old = ~ gsub("_lcu", "", .))  # Pattern rename

# Reorder columns
setcolorder(dt, c("id", "year", "welfare"))

# Low-overhead loop assignment (use set() in for loops, not :=)
for (j in c("a", "b", "c")) {
  set(dt, j = j, value = log(dt[[j]]))
}
```

## Row Binding

```r
# Fast row binding of a list of data.tables
rbindlist(list_of_dts)
rbindlist(list_of_dts, use.names = TRUE, fill = TRUE)  # Fill missing cols
rbindlist(list_of_dts, idcol = "source")              # Add source column
```

## Performance Patterns

```r
# setkey for repeated lookups
setkey(dt, id)
dt[.(target_ids)]  # Fast binary search

# Parallel reads
dt <- fread("large.csv", nThread = getDTthreads())

# Use integer types where possible (faster, smaller)
dt[, id := as.integer(id)]

# Avoid copies — always use := not <-
dt[, x := x * 2]  # CORRECT
dt <- dt[, x := x * 2]  # WRONG — creates unnecessary ref

# Column lookup with variable names
cols <- c("welfare", "income")
dt[, (cols) := lapply(.SD, as.numeric), .SDcols = cols]  # Parentheses on LHS
dt[, ..cols]  # .. prefix to look up in parent scope

# GForce optimization (automatic for: sum, mean, min, max, .N, var, sd, etc.)
dt[, .(total = sum(x), avg = mean(y)), by = g]  # Runs in optimized C
```

## Full Function Reference

| Function | Purpose | Key Args |
|---|---|---|
| `fread` | Fast CSV reader | `input`, `select`, `key`, `nThread` |
| `fwrite` | Fast CSV writer | `x`, `file`, `sep`, `compress`, `nThread` |
| `data.table` | Constructor | `...`, `key` |
| `setDT` | Convert in-place | `x`, `key` |
| `as.data.table` | Convert (copy) | `x`, `keep.rownames`, `key` |
| `copy` | Deep copy | `x` |
| `setkey`/`setkeyv` | Set physical key | `x`, `cols` |
| `setindex`/`setindexv` | Set secondary index | `x`, `cols` |
| `setorder`/`setorderv` | Reorder rows | `x`, `cols`, `order` |
| `setnames` | Rename columns | `x`, `old`, `new` |
| `setcolorder` | Reorder columns | `x`, `neworder` |
| `set` | Low-overhead `:=` | `x`, `i`, `j`, `value` |
| `rbindlist` | Fast row-bind | `l`, `use.names`, `fill`, `idcol` |
| `merge` | Join (base R style) | `x`, `y`, `by`, `all.x`, `all.y` |
| `melt` | Wide to long | `data`, `id.vars`, `measure.vars` |
| `dcast` | Long to wide | `data`, `formula`, `fun.aggregate` |
| `foverlaps` | Interval overlap join | `x`, `y`, `type`, `mult` |
| `fifelse` | Fast vectorized if-else | `test`, `yes`, `no`, `na` |
| `fcase` | Fast CASE WHEN | `...` (cond, val pairs), `default` |
| `fcoalesce` | Replace NAs | `...` (vectors) |
| `shift` | Lead/lag | `x`, `n`, `type`, `fill` |
| `frollmean`/`frollsum` | Rolling mean/sum | `x`, `n`, `fill`, `align` |
| `frollapply` | Rolling function | `x`, `n`, `FUN` |
| `nafill`/`setnafill` | Fill NAs | `x`, `type`, `fill` |
| `frank` | Fast rank | `x`, `ties.method` |
| `rleid` | Run-length group id | `...` |
| `rowid` | Row id within group | `...` |
| `uniqueN` | Count unique values | `x`, `by`, `na.rm` |
| `CJ` | Cross join (all combos) | `...`, `sorted`, `unique` |
| `between`/`%between%` | Range check | `x`, `lower`, `upper` |
| `%chin%` | Fast character `%in%` | `x`, `table` |
| `%like%`/`%ilike%` | Pattern matching | `x`, `pattern` |
| `patterns` | Regex column selector | `...`, `cols` |
| `fintersect`/`fsetdiff`/`funion` | Set operations | `x`, `y`, `all` |
| `setDTthreads`/`getDTthreads` | Thread control | `threads` |
| `tables` | List all DTs | `mb`, `order.col` |
