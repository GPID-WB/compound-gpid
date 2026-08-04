# data.table Anti-Patterns

Common mistakes in R code using `data.table`.

---

### Assigning back after `:=`

**Problem:** `:=` modifies by reference. Assigning back creates a second, unnecessary reference and confuses readers.

**Wrong:**
```r
dt <- dt[, log_income := log(income)]  # Extra <- is redundant and misleading
```

**Right:**
```r
dt[, log_income := log(income)]  # Works in place; no reassignment needed
```

---

### Using `ifelse()` instead of `fifelse()`/`fcase()`

**Problem:** `ifelse()` is slow and coerces types unpredictably (drops Date class, converts integers to doubles).

**Wrong:**
```r
dt[, category := ifelse(income > 50000, "high", "low")]
dt[, flag := ifelse(is.na(x), 0, x)]
```

**Right:**
```r
dt[, category := fifelse(income > 50000, "high", "low")]
dt[, value    := fcoalesce(x, 0)]  # Better pattern for NA replacement

# For multi-condition logic:
dt[, category := fcase(
  income > 100000, "high",
  income >  50000, "medium",
  default          = "low"
)]
```

---

### Using `DT[, col]` to retrieve a variable column name

**Problem:** `dt[, col]` where `col` is a variable returns the string `"col"`, not the column.

**Wrong:**
```r
col_name <- "welfare"
dt[, col_name]   # Returns the string "welfare"
```

**Right:**
```r
col_name <- "welfare"
dt[, ..col_name]          # .. prefix: looks up in parent scope
dt[, get(col_name)]       # get(): returns column as vector
dt[, .SD, .SDcols = col_name]  # As data.table (one column)

# Assigning to a variable column name:
dt[, (col_name) := value] # Parentheses on LHS
```

---

### Not calling `setDT()` after loading from RDS/RDA

**Problem:** `readRDS()` / `load()` does not restore the over-allocation slots of a `data.table`. Using `:=` immediately after produces a warning about `truelength`.

**Wrong:**
```r
dt <- readRDS("my_dt.rds")
dt[, new_col := 1]  # Warning: This data.table has been loaded from disk...
```

**Right:**
```r
dt <- readRDS("my_dt.rds")
setDT(dt)
dt[, new_col := 1]  # Works cleanly
```

---

### Using `dt[, col]` instead of `dt$col` or `dt[["col"]]` for a vector

**Problem:** `dt[, col]` without `.()` returns a single column as a **vector**, which can be confusing and is inconsistent with how `[]` works on data frames.

**Clarification (not strictly wrong — just be aware):**
```r
dt[, welfare]           # Returns welfare column as vector
dt[, .(welfare)]        # Returns welfare column as 1-column data.table
dt[, c("welfare")]      # Returns welfare column as 1-column data.table
dt$welfare              # Returns welfare column as vector (explicit, readable)
dt[["welfare"]]         # Returns welfare column as vector (programmatic)
```

**Prefer the explicit forms** when intent matters.

---

### Type mismatch in `fifelse`

**Problem:** `fifelse` requires `yes` and `no` branches to be the same type. A mismatch produces an error.

**Wrong:**
```r
fifelse(x > 0, 1, 0L)   # Error: 'no' is integer but 'yes' is double
```

**Right:**
```r
fifelse(x > 0, 1,  0)   # Both double
fifelse(x > 0, 1L, 0L)  # Both integer
```

---

### Using `T`/`F` in data.table expressions

**Problem:** Inside `DT[...]`, `T` and `F` are treated as column name lookups, not `TRUE`/`FALSE`.

**Wrong:**
```r
dt[, .SD, .SDcols = c(T, T, F)]  # Treats T/F as column names
```

**Right:**
```r
dt[, .SD, .SDcols = c(TRUE, TRUE, FALSE)]
```

---

### Row-filtering inside `j` instead of `i`

**Problem:** Filtering rows in the `j` expression (`dt[, x[x > 0]]`) is less efficient and harder to read than filtering in `i`.

**Wrong:**
```r
dt[, .(welfare = welfare[welfare > 0]), by = region]  # Filtering in j
```

**Right:**
```r
dt[welfare > 0, .(n = .N, mean = fmean(welfare, w = weight)), by = region]
```

---

### Using `lapply(.SD, collapse_function)` when `collap()` is available

**Problem:** `lapply(.SD, fmean, w = weight)` applies `fmean` column-by-column, without properly passing the weight across groups.

**Wrong:**
```r
dt[, lapply(.SD, fmean, w = weight), .SDcols = c("welfare", "income"), by = region]
```

**Right:**
```r
collap(dt, ~ region, fmean, w = ~ weight, cols = c("welfare", "income"))
```

**Why:** `collap()` is purpose-built for multi-column aggregation with weights. Use `.SD` patterns for quick EDA or when there's no weighted alternative.
