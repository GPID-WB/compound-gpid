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
result <- Y[X, on = "key"]          # X left join Y
result <- X[Y, on = "key", nomatch = 0]  # inner join

# Multi-column join
X[Y, on = .(id, year)]

# Non-equi join
X[Y, on = .(id, date >= start_date, date <= end_date)]

# Rolling join
X[Y, on = "date", roll = TRUE]      # LOCF
X[Y, on = "date", roll = -Inf]      # NOCB

# Anti join (rows in X not in Y)
X[!Y, on = "key"]

# Semi join (rows in X that have a match in Y, but keep X columns only)
X[unique(Y[, .(key)]), on = "key", nomatch = 0]

# Update join (add columns from Y to X in place)
X[Y, on = "key", new_col := i.value]
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

# Select columns by pattern
dt[, lapply(.SD, as.character), .SDcols = patterns("^income_")]
```

## Special Symbols

| Symbol | Meaning | Example |
|--------|---------|---------|
| `.N` | Number of rows (in group) | `dt[, .N, by = group]` |
| `.SD` | Subset of Data (all columns) | `dt[, lapply(.SD, mean)]` |
| `.SDcols` | Columns for .SD | `dt[, lapply(.SD, mean), .SDcols = cols]` |
| `.GRP` | Group number | `dt[, grp_id := .GRP, by = group]` |
| `.BY` | Current group value | `dt[, f(.BY), by = group]` |
| `.I` | Row indices | `dt[, .I[1], by = group]` |
| `:=` | Assign by reference | `dt[, new := x * 2]` |

## Performance Patterns

```r
# Set key for fast lookups
setkey(dt, id)
dt[.(target_id)]            # Binary search

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

# Multiple measure patterns (e.g., income_2020, income_2021, exp_2020, exp_2021)
melt(dt, id.vars = "id",
     measure.vars = patterns("^income_", "^exp_"),
     variable.name = "year",
     value.name = c("income", "expenditure"))
```

## Chaining

```r
# Chain operations
dt[age > 30
  ][, .(mean_income = mean(income)), by = region
  ][order(-mean_income)]
```

## Environment Variables and Scope

```r
# Using variables programmatically with get() and environment variables
col_name <- "income"
dt[, mean(get(col_name))]

# Multiple columns programmatically
cols <- c("income", "expenditure")
dt[, lapply(.SD, mean), .SDcols = cols]

# Dynamic column creation
new_name <- "log_income"
dt[, (new_name) := log(income)]

# Multiple dynamic columns
new_names <- paste0("log_", cols)
dt[, (new_names) := lapply(.SD, log), .SDcols = cols]
```

## I/O

```r
# Read CSV (fast)
dt <- fread("file.csv")

# Read with column selection
dt <- fread("file.csv", select = c("id", "income", "region"))

# Read with type specification
dt <- fread("file.csv", colClasses = c(id = "character", year = "integer"))

# Write CSV
fwrite(dt, "output.csv")

# Write with options
fwrite(dt, "output.csv", na = "", bom = TRUE)  # bom for Excel compatibility
```
