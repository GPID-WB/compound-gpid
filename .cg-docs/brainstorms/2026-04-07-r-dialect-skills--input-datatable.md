# Information of SKILL of  `data.table` R package

## 1. Package Purpose and Core Mental Model

`data.table` is a high-performance extension of R's `data.frame`. It provides fast aggregation of large data (100GB+ in RAM), fast ordered joins, and fast add/modify/delete of columns by group — all by reference (no copies).  

The central abstraction is the **`data.table` object** — an enhanced `data.frame` with class `c("data.table", "data.frame")`. All operations flow through one unified syntax:

```r
DT[i, j, by]
#   |  |  |
#   |  |  └── GROUP BY what?
#   |  └───── SELECT/compute what?
#   └──────── WHERE (filter rows) / JOIN (when i is a data.table)
```

Key mental model rules:
- **Reference semantics**: `:=` and all `set*()` functions modify in-place. No copy is made.
- **No rownames**: Use keys instead. Keys are multi-column, multi-type, and enable binary search.
- `.()` is an alias for `list()` inside `DT[...]`.
- Special symbols: `.SD` (Subset of Data), `.N` (row count), `.I` (row indices), `.GRP` (group number), `.BY` (group values), `.NGRP` (number of groups).  

## 2. Installation

```r
# CRAN (stable)
install.packages("data.table")

# GitHub dev version
data.table::update_dev_pkg()
# or
remotes::install_github("Rdatatable/data.table")
```

**System dependencies**: None required. OpenMP is used for parallelism if available (auto-detected at compile time). On macOS, the default clang may lack OpenMP; install `libomp` via Homebrew for multithreading.

**R version**: Requires R >= 3.3.0. Only `methods` is imported; `Suggests` include `bit64`, `R.utils`, `yaml`, `knitr`.  

## 3. Main Functions and Their Signatures

### Data Ingestion

| Function | Signature | Returns |
|----------|-----------|---------|
| `fread` | `fread(input="", file=NULL, text=NULL, cmd=NULL, sep="auto", header="auto", na.strings="NA", select=NULL, drop=NULL, colClasses=NULL, key=NULL, index=NULL, nThread=getDTthreads(), data.table=TRUE, ...)` | `data.table` (or `data.frame` if `data.table=FALSE`) |  

Key `fread` arguments:
- `input`: file path, URL, shell command (if contains a space), or raw data string (if contains `\n`)
- `select`/`drop`: character or integer vector of columns to keep/exclude. Cannot use both.
- `colClasses`: named list like `list(character=c("col1","col2"))` or vector
- `key`/`index`: set key or secondary index on read
- `nThread`: number of threads (default: `getDTthreads()`)

### Data Output

| Function | Signature | Returns |
|----------|-----------|---------|
| `fwrite` | `fwrite(x, file="", append=FALSE, sep=",", na="", col.names=TRUE, row.names=FALSE, compress="auto", nThread=getDTthreads(), ...)` | `NULL` (invisible); writes file |  

Key `fwrite` arguments:
- `compress`: `"auto"`, `"none"`, `"gzip"`. Auto-detects from `.gz` extension.
- `dateTimeAs`: `"ISO"` (default), `"squash"`, `"epoch"`, `"write.csv"`

### Construction & Conversion

```r
data.table(..., keep.rownames=FALSE, check.names=FALSE, key=NULL, stringsAsFactors=FALSE)
as.data.table(x, keep.rownames=FALSE, ..., key=NULL)
setDT(x, keep.rownames=FALSE, key=NULL, check.names=FALSE)  # converts list/data.frame IN PLACE
setDF(x, rownames=NULL)                                       # converts back to data.frame IN PLACE
copy(x)                                                        # deep copy
```  

### Keys, Indices, and Ordering

```r
setkey(x, ..., physical=TRUE)          # sort by cols, mark as key (unquoted col names)
setkeyv(x, cols, physical=TRUE)        # same, but cols is character vector
setindex(x, ...)                       # secondary index (no physical reorder)
setindexv(x, cols)                     # cols can be list of char vectors for multiple indices
key(x)                                 # returns key cols or NULL
indices(x, vectors=FALSE)             # returns index names
haskey(x)                              # TRUE/FALSE
setorder(x, ...)                       # reorder rows by reference (allows -col for descending)
setorderv(x, cols, order=1L)           # programmatic version
```  

### Column Manipulation (by reference)

```r
setnames(x, old, new, skip_absent=FALSE)  # rename columns
setcolorder(x, neworder)                   # reorder columns
set(x, i=NULL, j, value)                  # low-overhead loopable assign
setattr(x, name, value)                   # set any attribute
```   

### Binding & Joining

```r
rbindlist(l, use.names="check", fill=FALSE, idcol=NULL, ignore.attr=FALSE)
merge(x, y, by=NULL, by.x=NULL, by.y=NULL, all=FALSE, all.x=all, all.y=all,
      sort=TRUE, suffixes=c(".x",".y"), no.dups=TRUE, allow.cartesian=FALSE)
```   

### Reshaping

```r
melt(data, id.vars, measure.vars, variable.name="variable", value.name="value",
     na.rm=FALSE, variable.factor=TRUE, value.factor=FALSE)
dcast(data, formula, fun.aggregate=NULL, sep="_", ..., fill=NULL, drop=TRUE,
      value.var=guess(data))
```   

### Conditional & Coalesce

```r
fifelse(test, yes, no, na=NA)       # fast vectorized if-else; type-stable
fcase(..., default=NA)              # fast CASE WHEN (pairs of condition, value)
fcoalesce(...)                      # replace NAs from prioritized candidates
```   

### Overlap Joins

```r
foverlaps(x, y, by.x=key(x), by.y=key(y), type=c("any","within","start","end","equal"),
          mult=c("all","first","last"), nomatch=NA, which=FALSE)
```  

### Rolling & NA Functions

```r
frollmean(x, n, fill=NA, algo="fast", align="right", na.rm=FALSE, hasNA=NA, adaptive=FALSE)
frollsum(x, n, ...)
frollapply(x, n, FUN, ...)
nafill(x, type=c("const","locf","nocb"), fill=NA, nan.is.na=FALSE)
setnafill(x, type, fill, nan.is.na=FALSE, cols=seq_along(x))  # in-place
shift(x, n=1L, fill=NA, type=c("lag","lead","shift","cyclic"), give.names=FALSE)
```

### Utility

```r
uniqueN(x, by=NULL, na.rm=FALSE)    # fast count of unique values
frank(x, ..., ties.method="average") # fast rank
rleid(...)                           # run-length encoding id
rowid(...)                           # row id within each group
between(x, lower, upper, incbounds=TRUE)
x %chin% table                      # fast character %in%
CJ(...)                             # Cross Join — all combinations (sorted, unique)
SJ(...)                             # Sorted Join helper
tables()                            # list all data.tables in memory
setDTthreads(threads)               # control thread count
getDTthreads()                      # query thread count
```  

## 4. Canonical Workflows

### Workflow 1: Read, filter, aggregate, write

```r
library(data.table)

# Read CSV (auto-detects sep, types, header)
DT = fread("sales.csv", key = "region")

# Filter rows, compute by group
result = DT[year >= 2020, .(total_rev = sum(revenue), n = .N), by = region]

# Order result
setorder(result, -total_rev)

# Write out
fwrite(result, "summary.csv")
```

### Workflow 2: Add/update columns by reference, chained operations

```r
DT = fread("flights.csv")

# Add columns by reference (no copy, no reassignment needed)
DT[, `:=`(speed = distance / (air_time / 60),
          delay = arr_delay + dep_delay)]

# Conditional update
DT[hour == 24L, hour := 0L]

# Delete column
DT[, speed := NULL]

# Chained: filter + summarize + order
DT[carrier == "AA", .N, by = .(origin, dest)][order(-N)]
```

### Workflow 3: Joins using `DT[i, on=]` syntax

```r
orders  = data.table(id = 1:5, cust_id = c(10,20,10,30,20), amount = c(100,200,150,300,250))
custs   = data.table(cust_id = c(10,20,30), name = c("Alice","Bob","Carol"))

# Inner join
orders[custs, on = "cust_id", nomatch = NULL]

# Left join (all rows from orders)
custs[orders, on = "cust_id"]

# Anti-join (orders with no matching customer)
orders[!custs, on = "cust_id"]

# Update join: add customer name to orders by reference
orders[custs, on = "cust_id", name := i.name]

# Non-equi join
DT1[DT2, on = .(start <= date, end >= date)]
```

### Workflow 4: Reshape (wide <-> long)

```r
# Wide to long
DT_long = melt(DT, id.vars = c("id", "group"),
               measure.vars = patterns("^val_"),
               variable.name = "metric", value.name = "score")

# Long to wide
DT_wide = dcast(DT_long, id + group ~ metric, value.var = "score", fun.aggregate = mean)
```

### Workflow 5: `.SD` for multi-column operations

```r
DT = data.table(g = rep(letters[1:3], each = 4), x = rnorm(12), y = rnorm(12), z = rnorm(12))

# Apply function to all numeric columns by group
DT[, lapply(.SD, mean), by = g]

# Apply to subset of columns
DT[, lapply(.SD, mean), by = g, .SDcols = c("x", "y")]

# .SDcols with patterns
DT[, lapply(.SD, mean), by = g, .SDcols = patterns("^[xy]")]

# First row per group
DT[, .SD[1], by = g]
```

## 5. Key Design Patterns and Idioms

### The `DT[i, j, by]` idiom
Everything goes inside `[...]`. Do NOT use `dplyr`-style pipes for core operations. Chaining is done with `][`:
```r
DT[year > 2020][, .N, by = region][order(-N)]
```

### Reference semantics (`:=` and `set*`)
- `:=` modifies columns in place. **Never assign the result back**: `DT[, x := 1]` not `DT <- DT[, x := 1]`.
- Use the functional form for multiple columns: `DT[, `:=`(a = 1, b = 2)]` or `DT[, let(a = 1, b = 2)]`.
- To print after `:=`, append `[]`: `DT[, x := 1][]`.  

### `on=` for ad-hoc joins (preferred over `setkey` for one-off joins)
```r
X[Y, on = .(a = b)]           # join X to Y where X$a == Y$b
X[Y, on = .(a >= b)]          # non-equi join
X[Y, on = "id", mult = "first"]
```

### `.()` is `list()` inside `DT[...]`
```r
DT[.(val), on = "col"]        # key lookup
DT[, .(mean_x = mean(x)), by = .(g1, g2)]
```  

### Programming with `data.table` (variable column names)
```r
cols = c("x", "y")
DT[, (cols) := lapply(.SD, as.numeric), .SDcols = cols]  # parentheses on LHS
DT[, ..cols]                                               # .. prefix to look up in parent scope

# For complex expressions, use substitute2() or env= argument
expr = substitute2(list(mean_col = mean(col)), env = list(col = "x", mean_col = "avg_x"))
DT[, eval(expr), by = g]
```

### `copy()` when you need independence
```r
DT2 = copy(DT)   # deep copy; DT2 is independent
# NOT: DT2 = DT  (this just creates another name for the same object)
```

### GForce optimization
`sum`, `mean`, `min`, `max`, `first`, `last`, `head`, `tail`, `.N`, `median`, `var`, `sd`, `prod` are automatically optimized in `j` when used with `by`. `DT[, lapply(.SD, sum), by = g]` is as fast as `DT[, .(x = sum(x), y = sum(y)), by = g]`.

## 6. Common Errors and How to Fix Them

### Error: `:=` used in `i` (forgot comma)
```r
DT[x := 5]
# Error: Operator := detected in i ... Most often, this happens when forgetting the first comma
# Fix:
DT[, x := 5]
```  

### Error: "Column not found" / object not found in `j`
```r
col = "x"
DT[, col]          # returns the string "x", not the column
# Fix: use .. prefix or .SDcols
DT[, ..col]        # returns column x as a data.table
DT[, get(col)]     # returns column x as a vector
DT[, (col) := val] # assign to variable column name
```

### Error: "This data.table has been loaded from disk..."
```r
DT = readRDS("my_dt.rds")
DT[, new_col := 1]  # Warning/error about truelength
# Fix: run setDT() or setalloccol() after loading
DT = readRDS("my_dt.rds")
setDT(DT)
DT[, new_col := 1]  # works
```  

### Error: "Supplied N items to be assigned to M items of column"
```r
DT[, x := c(1, 2, 3)]  # if nrow(DT) != 3
# Fix: RHS must be length 1 (recycled) or exactly nrow(DT). Use rep() explicitly.
```

### Warning: "Column names are duplicated in the result" from `merge`
Happens when `suffixes = c("", "")`. Use distinct suffixes: `suffixes = c(".x", ".y")`.

### Error: "Item N has M columns, inconsistent with item 1 which has K columns"
```r
rbindlist(list(DT1, DT2))  # different number of columns
# Fix:
rbindlist(list(DT1, DT2), fill = TRUE)  # fills missing cols with NA
```  

### `DT[, .SD, .SDcols = c(T, T, F)]` treats `T`/`F` as column names
Always use `TRUE`/`FALSE`, never `T`/`F` in data.table expressions.  

### `fifelse` / `fcase` type mismatch
```r
fifelse(x > 0, 1, 0L)
# Error: 'no' is of type integer but 'yes' is double
# Fix: ensure same types
fifelse(x > 0, 1, 0)     # both double
fifelse(x > 0, 1L, 0L)   # both integer
```  

## 7. Performance and Scaling Notes

- **Threading**: data.table uses OpenMP internally. Control with `setDTthreads(n)`. Default is 50% of logical CPUs. Check with `getDTthreads()`.
- **`fread`/`fwrite`**: Multi-threaded. `fread` memory-maps files. For very large files, use `select=` to read only needed columns.
- **Keys vs indices**: `setkey()` physically reorders (one key only). `setindex()` stores an order vector as an attribute (multiple allowed, no reorder). Use `on=` for ad-hoc joins — it auto-creates/reuses indices.  
- **GForce**: Aggregation functions (`sum`, `mean`, `min`, `max`, `median`, `var`, `sd`, `prod`, `.N`, `first`, `last`, `head`, `tail`) are optimized in C when used in `j` with `by`. Disable with `options(datatable.optimize = 0)`.
- **Avoid copies**: Use `:=` and `set()` instead of `<-` assignment. `set()` is a low-overhead, loopable version of `:=` for use in `for` loops.
- **`rbindlist`** is much faster than `do.call(rbind, list_of_dts)`.
- **Column types matter**: Integer is faster and smaller than double. Use `IDate` (4 bytes) instead of `Date` (8 bytes double) when possible.
- **`CJ()`** (Cross Join) is parallelized in C. Factor inputs are much faster than character.
- **Memory**: `data.table` over-allocates column pointer slots (default 1024 extra via `options(datatable.alloccol)`). This allows adding columns by reference without reallocation.
- **Large groups**: For millions of groups, `keyby=` is faster than `by=` followed by `setkey()`.

## 8. Integration with Other Packages

### Works well with:
- **`bit64`**: `integer64` type is natively supported in keys, joins, `fread`, `fwrite`, `fifelse`, `fcase`, `fcoalesce`, `between`, `shift`, `frank`, `CJ`.
- **`ggplot2`**: `data.table` inherits from `data.frame`, so it works directly with `ggplot()`.
- **`knitr`**: Custom `knit_print.data.table` method registered.
- **`xts`/`zoo`**: `as.data.table.xts` and `as.xts.data.table` converters provided.  

### Known conflicts / compatibility notes:
- **`dplyr`**: Both define `first()`, `last()`, `between()`. If both are loaded, use `data.table::first()` etc. to disambiguate. `data.table` does NOT use the pipe `|>` or `%>%` idiom internally.
- **`reshape2`**: `dcast` and `melt` generics are now owned by `data.table`. If you still use `reshape2`, you must namespace-qualify: `reshape2::dcast()`.  
- **`plyr`**: `plyr` also defines `summarize` etc. Load `data.table` after `plyr` or use explicit namespacing.
- **Packages should `Import` not `Depend` on `data.table`**. Use `data.table::` or `@importFrom` in package code.

## 9. Function Reference Quick-Lookup Table

| Function | Purpose | Key Args | Returns |
|---|---|---|---|
| `fread` | Fast CSV/text reader | `input`, `select`, `key`, `nThread` | `data.table` |
| `fwrite` | Fast CSV writer | `x`, `file`, `sep`, `compress`, `nThread` | `NULL` (writes file) |
| `data.table` | Constructor | `...`, `key` | `data.table` |
| `setDT` | Convert list/df in-place | `x`, `key` | `x` (invisible) |
| `as.data.table` | Convert (copies) | `x`, `keep.rownames`, `key` | `data.table` |
| `copy` | Deep copy | `x` | `data.table` |
| `setkey` / `setkeyv` | Set physical key | `x`, `cols` | `x` (invisible) |
| `setindex` / `setindexv` | Set secondary index | `x`, `cols` | `x` (invisible) |
| `key` / `haskey` / `indices` | Query key/index | `x` | `character` / `logical` |
| `setorder` / `setorderv` | Reorder rows by ref | `x`, `cols`, `order` | `x` (invisible) |
| `setnames` | Rename columns by ref | `x`, `old`, `new` | `x` (invisible) |
| `setcolorder` | Reorder columns by ref | `x`, `neworder` | `x` (invisible) |
| `set` | Low-overhead `:=` | `x`, `i`, `j`, `value` | `x` (invisible) |
| `rbindlist` | Fast row-bind list of DTs | `l`, `use.names`, `fill`, `idcol` | `data.table` |
| `merge` | Join two DTs | `x`, `y`, `by`, `all`, `all.x`, `all.y` | `data.table` |
| `melt` | Wide to long | `data`, `id.vars`, `measure.vars` | `data.table` |
| `dcast` | Long to wide | `data`, `formula`, `fun.aggregate`, `value.var` | `data.table` |
| `foverlaps` | Interval/overlap join | `x`, `y`, `type`, `mult`, `nomatch` | `data.table` |
| `fifelse` | Fast vectorized if-else | `test`, `yes`, `no`, `na` | vector (same type as `yes`) |
| `fcase` | Fast CASE WHEN | `...` (condition, value pairs), `default` | vector |
| `fcoalesce` | Replace NAs from candidates | `...` (vectors or list) | vector |
| `shift` | Lead/lag | `x`, `n`, `type`, `fill` | vector or list |
| `frollmean` / `frollsum` | Rolling mean/sum | `x`, `n`, `fill`, `align`, `na.rm` | list of numeric |
| `frollapply` | Rolling arbitrary function | `x`, `n`, `FUN` | list of numeric |
| `nafill` / `setnafill` | Fill NAs (LOCF/NOCB/const) | `x`, `type`, `fill` | list / `x` (invisible) |
| `frank` / `frankv` | Fast rank | `x`, `ties.method` | integer vector |
| `rleid` / `rleidv` | Run-length group id | `...` | integer vector |
| `rowid` / `rowidv` | Row id within group | `...` | integer vector |
| `uniqueN` | Count unique values | `x`, `by`, `na.rm` | integer scalar |
| `CJ` | Cross join (all combos) | `...`, `sorted`, `unique` | `data.table` |
| `between` / `%between%` | Range check | `x`, `lower`, `upper` | logical vector |
| `%chin%` | Fast character `%in%` | `x`, `table` | logical vector |
| `%like%` / `%ilike%` / `%flike%` | Pattern matching | `x`, `pattern` | logical vector |
| `transpose` | Transpose DT | `l`, `keep.names`, `make.names` | `data.table` |
| `tstrsplit` | Transpose of `strsplit` | `x`, `split`, `keep` | list |
| `setDTthreads` | Set thread count | `threads` | `NULL` (invisible) |
| `getDTthreads` | Get thread count | — | integer |
| `tables` | List all DTs in memory | `mb`, `order.col` | `data.table` |
| `substitute2` | Enhanced `substitute` for programming | `expr`, `env` | language object |
| `patterns` | Regex column selector (for `melt`, `.SDcols`) | `...`, `cols` | integer vector |
| `fintersect` / `fsetdiff` / `funion` / `fsetequal` | Set operations | `x`, `y`, `all` | `data.table` |
| `groupingsets` / `cube` / `rollup` | OLAP-style grouping | `x`, `j`, `by`, `sets` | `data.table` |

