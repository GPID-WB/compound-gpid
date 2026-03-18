# data.table Patterns

## Core Syntax: `DT[i, j, by]`

```r
# Filter rows (i)
dt[age > 30]
dt[country == "USA"]

# Select/compute columns (j)
dt[, .(mean_income = mean(income), n = .N)]
dt[, .(col1, col2)]

# Group by
dt[, .(mean_income = mean(income)), by = region]
dt[, .(mean_income = mean(income)), by = .(region, year)]
```

## Assignment by Reference (`:=`)

```r
# Add/modify columns in place
dt[, log_income := log(income)]
dt[, c("col_a", "col_b") := .(fun_a(x), fun_b(y))]

# Conditional assignment
dt[age > 65, elderly := TRUE]

# Remove columns
dt[, temp_col := NULL]
```

## Joins

```r
# Left join
result <- Y[X, on = "key"]                       # X left join Y
result <- X[Y, on = "key", nomatch = 0]          # inner join

# Multi-column join
X[Y, on = .(id, year)]

# Non-equi join
X[Y, on = .(id, date >= start_date, date <= end_date)]

# Anti join
X[!Y, on = "key"]

# Rolling join
X[Y, on = "date", roll = TRUE]                   # LOCF
X[Y, on = "date", roll = -Inf]                   # NOCB
```

## .SD and .SDcols

```r
# Apply function to multiple columns
dt[, lapply(.SD, mean), .SDcols = c("col1", "col2", "col3")]

# Apply function by group
dt[, lapply(.SD, mean), by = region, .SDcols = is.numeric]

# First/last row per group
dt[, .SD[1], by = group]
dt[, .SD[.N], by = group]
```

## Performance Patterns

```r
# Set key for fast lookups
setkey(dt, id)
dt[.(target_id)]                # Binary search

# Set index for secondary lookups
setindex(dt, region)

# Use fifelse/fcase instead of ifelse
dt[, category := fifelse(income > 50000, "high", "low")]
dt[, category := fcase(
  income > 100000, "high",
  income > 50000,  "medium",
  default = "low"
)]

# Use set() in loops
for (j in cols) {
  set(dt, j = j, value = normalize(dt[[j]]))
}

# Read only needed columns
dt <- fread("file.csv", select = c("id", "income", "region"))
```

## Reshaping

```r
# Wide to long
melt(dt, id.vars = "id", measure.vars = c("year_2020", "year_2021"),
     variable.name = "year", value.name = "value")

# Long to wide
dcast(dt, id ~ year, value.var = "income")

# Multiple value columns
dcast(dt, id ~ year, value.var = c("income", "expenditure"))
```

## Chaining

```r
# Chain operations with [][]
dt[age > 30
  ][, .(mean_income = mean(income)), by = region
  ][order(-mean_income)]
```

## Quick Reference: Special Symbols

| Symbol | Meaning | Example |
|--------|---------|---------|
| `.N` | Number of rows (in group) | `dt[, .N, by = group]` |
| `.SD` | Subset of Data | `dt[, lapply(.SD, mean)]` |
| `.SDcols` | Columns for `.SD` | `dt[, lapply(.SD, mean), .SDcols = cols]` |
| `.GRP` | Group number | `dt[, grp_id := .GRP, by = group]` |
| `.BY` | Current group value | `dt[, f(.BY), by = group]` |
| `.I` | Row indices | `dt[, .I[1], by = group]` |
| `:=` | Assign by reference | `dt[, new := x * 2]` |
