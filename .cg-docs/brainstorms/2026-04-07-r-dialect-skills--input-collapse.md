# Information for SKILL of collapse (R package)

## 1. Package Purpose and Core Mental Model

`collapse` is a high-performance C/C++-based R package for advanced data transformation and statistical computing. It replaces and accelerates common operations from base R, `dplyr`, and `data.table` with 2–100x speedups.  

**Core mental model:** Everything revolves around the **GRP object** — a grouping structure created by `GRP()` or `fgroup_by()`. All fast statistical functions (`fmean`, `fsum`, `fsd`, etc.) accept a `g` argument for grouped computation, and a `TRA` argument for grouped transformations (replacing, centering, scaling, etc.) in a single pass. The package is **class-agnostic**: functions work identically on base R vectors/data.frames, `data.table`, `tibble`, `sf`, `plm`, and `xts` objects, preserving their attributes.  

**Key abstractions:**
- **GRP object**: A list with `N.groups`, `group.id`, `group.sizes`, `groups`, `group.vars`, `ordered`, `order`, `group.starts`. Created via `GRP()`, `fgroup_by()`, or automatically from factors/lists passed to `g`.  
- **TRA (Transformation) framework**: 10 operations (`"-"`, `"+"`, `"*"`, `"/"`, `"%"`, `"%%"`, `"-+"`, `"+-"`, `"replace"`, `"replace_fill"`) applicable to all fast statistical functions via the `TRA` argument. Example: `fmean(x, g, TRA = "-")` centers `x` by group means in one pass.  

## 2. Installation

```r
# CRAN (stable)
install.packages("collapse")

# GitHub (development)
remotes::install_github("fastverse/collapse")
```

**System dependencies:** A C/C++ compiler. OpenMP support is optional but recommended for multithreading. No other system libraries required. `Depends: R (>= 3.5.0)`, `Imports: Rcpp (>= 1.0.1)`.  

**Configuration on load:**
```r
library(collapse)

# Set global options
set_collapse(
  nthreads = 4L,    # OpenMP threads (default: 1)
  na.rm = TRUE,     # Skip NA by default (default: TRUE)
  sort = TRUE,      # Sort groups (default: TRUE)
  mask = NULL,      # Namespace masking: "all", "fast-fun", "manip", etc.
  verbose = 1L      # Verbosity for joins etc.
)

# Query current options
get_collapse()
``` 

## 3. Main Functions and Their Signatures

### 3.1 Fast Statistical Functions

All follow the pattern: `f<name>(x, g = NULL, w = NULL, TRA = NULL, na.rm = .op[["na.rm"]], use.g.names = TRUE, ...)`. S3 methods exist for `default`, `matrix`, `data.frame`, `grouped_df`, `zoo`, `units`, `pdata.frame`, `pseries`.  

```r
# Aggregation
fmean(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE, nthreads = 1L)
fsum(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE, fill = FALSE, nthreads = 1L)
fmedian(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE, nthreads = 1L)
fvar(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE)
fsd(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE)
fmin(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE, nthreads = 1L)
fmax(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE, nthreads = 1L)
fmode(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE, nthreads = 1L)
fnth(x, n = 0.5, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE, nthreads = 1L)
fprod(x, g = NULL, w = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE, fill = FALSE)
fnobs(x, g = NULL, TRA = NULL, use.g.names = TRUE)
fndistinct(x, g = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE, nthreads = 1L)
ffirst(x, g = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE)
flast(x, g = NULL, TRA = NULL, na.rm = TRUE, use.g.names = TRUE)
```   

### 3.2 Grouping and Ordering

```r
GRP(X, by = NULL, sort = TRUE, decreasing = FALSE, na.last = TRUE,
    return.groups = TRUE, return.order = sort, method = "auto", call = TRUE)
# Returns: GRP object (list with class "GRP")

fgroup_by(.X, ..., sort = TRUE, decreasing = FALSE, na.last = TRUE,
          return.groups = TRUE, return.order = sort, method = "auto")
# Returns: grouped data frame (class "GRP_df", "grouped_df")
# Alias: gby()

fungroup(X)  # Remove grouping

qF(x, ordered = FALSE, na.exclude = TRUE, sort = TRUE, drop = FALSE,
   keep.attr = TRUE, method = "auto")
# Returns: factor

qG(x, ordered = FALSE, na.exclude = TRUE, sort = TRUE,
   return.groups = FALSE, method = "auto")
# Returns: integer vector with class "qG" and "N.groups" attribute

finteraction(..., factor = TRUE, ordered = FALSE, sort = TRUE, method = "auto", sep = ".")
# Alias: itn()
```    

### 3.3 Data Manipulation Verbs

```r
fsubset(.x, subset, ...)          # Alias: sbt(). Fast subset rows + select cols
ss(x, i, j, check = TRUE)        # Non-lazy row/col subset (no NSE)

fselect(.x, ..., return = "data") # Alias: slt(). Select columns by name/index
get_vars(x, vars, return = "data", regex = FALSE)  # Alias: gv()
num_vars(x)  # Alias: nv(). Select numeric columns

ftransform(.data, ...)            # Alias: tfm(). Add/modify/delete columns
settransform(.data, ...)          # Alias: settfm(). In-place ftransform
ftransformv(.data, vars, FUN, ..., apply = TRUE)  # Alias: tfmv()

fmutate(.data, ..., .keep = "all", .cols = NULL)  # Alias: mtt()
# Like dplyr::mutate but auto-detects collapse fast functions and adds grouping

fcompute(.data, ..., keep = NULL) # Like fmutate but only returns computed columns

fsummarise(.data, ..., keep.group_vars = TRUE, .cols = NULL)  # Alias: smr()
# Like dplyr::summarise

collap(X, by, FUN = fmean, catFUN = fmode, cols = NULL, w = NULL,
       wFUN = fsum, custom = NULL, ..., keep.by = TRUE, keep.w = TRUE,
       keep.col.order = TRUE, sort = TRUE)
# Advanced aggregation: auto-splits numeric/categorical, applies different functions

across(.cols = NULL, .fns, ..., .names = NULL, .apply = "auto", .transpose = "auto")
# Only inside fmutate() and fsummarise()
```      

### 3.4 Joins, Pivoting, Binding

```r
join(x, y, on = NULL, how = "left", suffix = NULL, validate = "m:m",
     multiple = FALSE, sort = FALSE, keep.col.order = TRUE,
     drop.dup.cols = FALSE, verbose = 1L, column = NULL, attr = NULL)
# how: "left", "right", "inner", "full", "semi", "anti"

pivot(data, ids = NULL, values = NULL, names = NULL, labels = NULL,
      how = "longer", na.rm = FALSE, factor = c("names", "labels"),
      FUN = "last", nthreads = 1L, fill = NULL, drop = TRUE, sort = FALSE)
# how: "longer", "wider", "recast"

rowbind(...)  # Fast row-binding (uses data.table's rbindlist internally)
roworder(X, ..., na.last = TRUE)  # Reorder rows
colorder(X, ..., pos = "front")   # Reorder columns
frename(X, ..., cols = NULL)      # Alias: rnm(). Rename columns
```   

### 3.5 Time Series / Panel Data

```r
flag(x, n = 1, g = NULL, t = NULL, fill = NA, stubs = TRUE)  # Lag/lead
L(x, n = 1, ...)   # Lag operator (positive n = lag, negative = lead)
F(x, n = 1, ...)   # Lead operator (calls L with -n)

fdiff(x, n = 1, diff = 1, g = NULL, t = NULL, fill = NA, stubs = TRUE)  # Differences
D(x, n = 1, ...)   # Difference operator

fgrowth(x, n = 1, diff = 1, g = NULL, t = NULL, fill = NA, stubs = TRUE)  # Growth rates
G(x, n = 1, ...)   # Growth operator

fwithin(x, g = NULL, w = NULL, na.rm = TRUE, mean = 0, theta = 1)  # Within-transform (demean)
W(x, ...)           # Within operator

fbetween(x, g = NULL, w = NULL, na.rm = TRUE, fill = FALSE)  # Between-transform (group means)
B(x, ...)           # Between operator

fscale(x, g = NULL, w = NULL, na.rm = TRUE, mean = 0, sd = 1)  # Standardize
STD(x, ...)         # Standardize operator

fhdwithin(x, fl, w = NULL, na.rm = TRUE, fill = FALSE)   # High-dimensional within (FE)
HDW(x, ...)
fhdbetween(x, fl, w = NULL, na.rm = TRUE, fill = FALSE)  # High-dimensional between
HDB(x, ...)

fcumsum(x, g = NULL, na.rm = TRUE, fill = FALSE)  # Grouped cumulative sum

findex_by(.X, ..., single = "auto")  # Alias: iby(). Index panel data
# Creates indexed_frame / indexed_series for automatic lag/diff by panel structure
```   

### 3.6 Quick Conversion and Summary

```r
qDF(X, row.names.col = FALSE, keep.attr = FALSE, class = "data.frame")
qDT(X, row.names.col = FALSE, keep.attr = FALSE, class = c("data.table", "data.frame"))
qTBL(X, row.names.col = FALSE, keep.attr = FALSE, class = c("tbl_df", "tbl", "data.frame"))
qM(X, row.names.col = NULL, keep.attr = FALSE)  # Convert to matrix

qsu(x, g = NULL, w = NULL, pid = NULL, cols = NULL, higher = FALSE)  # Quick summary stats
descr(X, ...)  # Detailed column descriptions
pwcor(X, ..., w = NULL, N = FALSE, P = FALSE, use = "pairwise.complete.obs")  # Pairwise correlations
qtab(...)      # Fast cross-tabulation (alias: qtable)
```   

## 4. Canonical Workflows

### 4.1 Grouped Aggregation (dplyr-style)

```r
library(collapse)
data(wlddev)  # World Bank panel data bundled with collapse

# Pipe-based grouped summarization
wlddev |>
  fsubset(year >= 2000 & !is.na(PCGDP)) |>
  fgroup_by(region, income) |>
  fsummarise(
    mean_gdp = fmean(PCGDP),
    median_life = fmedian(LIFEEX),
    n = fnobs(PCGDP)
  )

# Equivalent using collap() — auto-splits numeric/categorical
collap(wlddev, ~ region + income, fmean, fmode, w = ~ POP,
       cols = c("PCGDP", "LIFEEX", "GINI"))
```   

### 4.2 Grouped Transformation (mutate with fast functions)

```r
# fmutate auto-detects collapse fast functions and injects grouping
wlddev |>
  fgroup_by(country) |>
  fmutate(
    gdp_lag1 = flag(PCGDP, 1),           # Lag by 1 within country
    gdp_growth = fgrowth(PCGDP, 1),      # Growth rate
    gdp_centered = fwithin(PCGDP),        # Demean within country
    gdp_scaled = fscale(PCGDP)            # Standardize within country
  ) |>
  fungroup()

# Same using TRA argument (single-pass, no pipe needed)
fmean(wlddev$PCGDP, g = wlddev$country, TRA = "-")  # Center by group mean
```  

### 4.3 Panel Data with Indexing

```r
# Index panel data for automatic lag/diff handling
pwld <- wlddev |>
  findex_by(country, year)

# Now flag/fdiff/fgrowth automatically use the panel structure
L(pwld$PCGDP, 1)          # Lag GDP by 1 year within country
D(pwld$PCGDP)             # First difference
G(pwld$PCGDP)             # Growth rate
W(pwld, cols = "PCGDP")   # Within-transform (country fixed effects)

# Panel summary statistics (between/within decomposition)
qsu(pwld, pid = ~ country, cols = c("PCGDP", "LIFEEX"), higher = TRUE)
```  

### 4.4 Reshaping with pivot()

```r
# Long to wide
long_df <- data.frame(id = rep(1:3, each = 2),
                      variable = rep(c("a", "b"), 3),
                      value = rnorm(6))
pivot(long_df, ids = "id", names = "variable", values = "value", how = "wider")

# Wide to long
wide_df <- data.frame(id = 1:3, a = rnorm(3), b = rnorm(3))
pivot(wide_df, ids = "id", how = "longer")
```  

### 4.5 Fast Joins

```r
x <- data.frame(id = 1:5, val_x = rnorm(5))
y <- data.frame(id = 3:7, val_y = rnorm(5))

join(x, y, on = "id", how = "left", verbose = TRUE)
# left join: x[id] 3/5 (60%) <m:1> y[id] 3/5 (60%)

join(x, y, on = "id", how = "inner", validate = "1:1",
     column = ".join")  # Adds a join indicator column
```  

## 5. Key Design Patterns and Idioms

### 5.1 The `g` + `TRA` Pattern (Most Important)

Every fast statistical function supports `g` (grouping) and `TRA` (transformation) arguments. This enables grouped aggregation AND grouped transformation in a single C-level pass:

```r
# Grouped aggregation
fmean(mtcars$mpg, g = mtcars$cyl)

# Grouped transformation: center by group mean (TRA = "-")
fmean(mtcars$mpg, g = mtcars$cyl, TRA = "-")

# Grouped transformation: replace with group mean (TRA = "replace_fill")
fmean(mtcars$mpg, g = mtcars$cyl, TRA = "replace_fill")

# Weighted grouped mean
fmean(mtcars$mpg, g = mtcars$cyl, w = mtcars$wt)
```  

### 5.2 Pipe-Friendly with `fgroup_by` / `fmutate` / `fsummarise`

```r
# collapse's fgroup_by stores a GRP object, not dplyr's row-index list
mtcars |>
  fgroup_by(cyl, vs) |>
  fmutate(mpg_centered = fwithin(mpg)) |>  # auto-grouped
  fsummarise(across(mpg:drat, fmean)) |>   # across() works inside
  fungroup()
```  

### 5.3 Reuse GRP Objects for Repeated Grouping

```r
g <- GRP(mtcars, ~ cyl + vs)  # Compute once
fmean(mtcars$mpg, g)
fsd(mtcars$mpg, g)
fmin(mtcars$mpg, g)
# Much faster than re-grouping each time
```  

### 5.4 Formula Interface in Operator Functions

```r
# W, B, D, G, L, STD, HDB, HDW support formula interface for by and cols
W(wlddev, ~ PCGDP + LIFEEX | country)  # Within-transform PCGDP, LIFEEX by country
L(wlddev, 1, by = ~ country, t = ~ year, cols = c("PCGDP", "LIFEEX"))
```  

### 5.5 In-Place Modification

```r
settransform(mtcars, new_col = mpg * 2)  # Modifies mtcars in place
setv(x, 1:5, NA)                          # Set elements 1:5 to NA in place
setop(x, "+", 1)                           # x += 1 in place
```  

### 5.6 Short Aliases

Most functions have short aliases for interactive use:  

| Full name | Alias |
|-----------|-------|
| `fselect` | `slt` |
| `fsubset` | `sbt` |
| `fgroup_by` | `gby` |
| `findex_by` | `iby` |
| `fmutate` | `mtt` |
| `fsummarise` | `smr` |
| `ftransform` | `tfm` |
| `frename` | `rnm` |
| `get_vars` | `gv` |
| `add_vars` | `av` |
| `num_vars` | `nv` |
| `finteraction` | `itn` |

## 6. Common Errors and How to Fix Them

### Error: `"fsubset() does not support grouped data"`
```r
# WRONG
mtcars |> fgroup_by(cyl) |> fsubset(mpg > 20)
# FIX: subset BEFORE grouping
mtcars |> fsubset(mpg > 20) |> fgroup_by(cyl)
```  

### Error: `"All replacement expressions have to be uniquely named"`
```r
# WRONG: unnamed expression in ftransform
ftransform(mtcars, mpg * 2)
# FIX: name it
ftransform(mtcars, mpg2 = mpg * 2)
```  

### Error: `"here na.last needs to be TRUE or FALSE"`
```r
# WRONG
GRP(x, na.last = NA)
# FIX: GRP requires na.last = TRUE or FALSE (NA would make dimensions mismatch)
GRP(x, na.last = TRUE)
```  

### Error: `"Lengths of replacements must be equal to nrow(.data) or 1"`
```r
# WRONG: computed column has wrong length
ftransform(mtcars, x = 1:5)
# FIX: length must be nrow(mtcars) or 1. Use NULL to delete columns.
ftransform(mtcars, x = 1)  # scalar recycled
```  

### Error: `"across() can only work inside fmutate() and fsummarise()"`
```r
# WRONG: using across() standalone
across(1:3, fmean)
# FIX: must be inside fmutate() or fsummarise()
mtcars |> fgroup_by(cyl) |> fsummarise(across(mpg:drat, fmean))
```  

### Unused argument warnings
By default, collapse issues warnings for unused arguments. Control with:
```r
options(collapse_unused_arg_action = "none")  # or "warning", "error", "message"
```  

## 7. Performance and Scaling Notes

- **OpenMP multithreading**: Set `set_collapse(nthreads = 4L)` or pass `nthreads` to individual functions (`fsum`, `fmean`, `fmode`, `fndistinct`, `fmin`, `fmax`, `pivot`). Default is 1 thread.  

- **Reuse GRP objects**: For repeated grouped operations on the same grouping, compute `g <- GRP(data, ~ cols)` once and pass it to all functions.  

- **In-place modification**: Use `settransform()`, `setv()`, `setop()`, `%+=%`, `%-=%` for zero-copy modifications.  

- **Quick conversions**: `qDF()`, `qDT()`, `qM()` are much faster than `as.data.frame()`, `as.data.table()`, `as.matrix()` because they avoid deep attribute copying.  

- **`ss()` vs `fsubset()`**: Use `ss(x, i, j)` for programmatic row/column subsetting without non-standard evaluation. It's faster than `[.data.frame` and does not evaluate expressions lazily.  

- **`collap()` vs `fgroup_by |> fsummarise`**: `collap()` is optimized for aggregating entire data frames with different functions for numeric vs. categorical columns. It auto-detects column types.  

- **Hash vs radix grouping**: `method = "auto"` uses radix sort when `sort = TRUE` (stable, ordered groups) and hash-based grouping when `sort = FALSE` (faster for many groups).  

## 8. Integration with Other Packages

### Works natively with:
- **data.table**: All functions preserve `data.table` class and handle over-allocation. `fgroup_by()` on a `data.table` returns a `data.table`. `qDT()` for fast conversion.  
- **dplyr/tibble**: `fgroup_by()` creates objects compatible with `dplyr::grouped_df`. `qTBL()` for fast tibble conversion. `fmutate`/`fsummarise` are drop-in replacements.
- **sf**: Geometry columns are automatically preserved in all operations.
- **plm**: `findex_by()` / `to_plm()` for panel data. `pdata.frame`/`pseries` methods on all fast functions.  

### Namespace masking:
```r
# Replace base/dplyr functions with collapse equivalents
set_collapse(mask = "all")  # unique -> funique, mean -> fmean, subset -> fsubset, etc.
set_collapse(mask = "fast-stat-fun")  # Only mask statistical functions
set_collapse(mask = "manip")  # Only mask manipulation functions
```  

### Suggested packages (optional):
`data.table`, `magrittr`, `kit`, `xts`, `zoo`, `plm`, `fixest`, `tibble`, `dplyr`, `ggplot2`, `bit64`.  

### Known considerations:
- `collapse::D()` conflicts with `stats::D()` (symbolic differentiation). collapse provides S3 methods for `expression`, `call`, `name` to handle this.  
- `.datatable.aware <- TRUE` is set so data.table recognizes collapse as a compatible package.  

## 9. Function Reference Quick-Lookup Table

### Statistical Functions

| Function | Purpose | Key args | Returns |
|----------|---------|----------|---------|
| `fmean` | Grouped/weighted mean | `x, g, w, TRA, na.rm, nthreads` | vector, matrix, or data.frame |
| `fsum` | Grouped/weighted sum | `x, g, w, TRA, na.rm, fill, nthreads` | vector, matrix, or data.frame |
| `fmedian` | Grouped/weighted median | `x, g, w, TRA, na.rm, nthreads` | vector, matrix, or data.frame |
| `fvar` | Grouped/weighted variance | `x, g, w, TRA, na.rm` | vector, matrix, or data.frame |
| `fsd` | Grouped/weighted std dev | `x, g, w, TRA, na.rm` | vector, matrix, or data.frame |
| `fmin` | Grouped minimum | `x, g, TRA, na.rm, nthreads` | vector, matrix, or data.frame |
| `fmax` | Grouped maximum | `x, g, TRA, na.rm, nthreads` | vector, matrix, or data.frame |
| `fmode` | Grouped/weighted mode | `x, g, w, TRA, na.rm, nthreads` | vector, matrix, or data.frame |
| `fnth` | Grouped/weighted nth element/quantile | `x, n, g, w, TRA, na.rm, nthreads` | vector, matrix, or data.frame |
| `fprod` | Grouped/weighted product | `x, g, w, TRA, na.rm, fill` | vector, matrix, or data.frame |
| `fnobs` | Count non-NA observations | `x, g, TRA, use.g.names` | vector, matrix, or data.frame |
| `fndistinct` | Count distinct values | `x, g, TRA, na.rm, nthreads` | vector, matrix, or data.frame |
| `ffirst` | First value per group | `x, g, TRA, na.rm` | vector, matrix, or data.frame |
| `flast` | Last value per group | `x, g, TRA, na.rm` | vector, matrix, or data.frame |
| `fcumsum` | Grouped cumulative sum | `x, g, na.rm, fill` | vector, matrix, or data.frame |   

### Transformation / Time Series Functions

| Function | Purpose | Key args | Returns |
|----------|---------|----------|---------|
| `flag` / `L` / `F` | Lag / lead | `x, n, g, t, fill, stubs` | same class as input |
| `fdiff` / `D` | Differences / log-differences | `x, n, diff, g, t, fill, log` | same class as input |
| `fgrowth` / `G` | Growth rates | `x, n, diff, g, t, fill` | same class as input |
| `fwithin` / `W` | Demean (within-transform) | `x, g, w, na.rm, mean, theta` | same class as input |
| `fbetween` / `B` | Group means (between-transform) | `x, g, w, na.rm, fill` | same class as input |
| `fscale` / `STD` | Standardize (z-score) | `x, g, w, na.rm, mean, sd` | same class as input |
| `fhdwithin` / `HDW` | High-dim within (absorb FE) | `x, fl, w, na.rm, fill` | same class as input |
| `fhdbetween` / `HDB` | High-dim between (predict FE) | `x, fl, w, na.rm, fill` | same class as input |   

### Grouping and Ordering

| Function | Purpose | Key args | Returns |
|----------|---------|----------|---------|
| `GRP` | Create grouping object | `X, by, sort, method` | GRP object (list) |
| `fgroup_by` / `gby` | Group a data frame | `.X, ..., sort, method` | grouped_df |
| `fungroup` | Remove grouping | `X` | ungrouped data frame |
| `findex_by` / `iby` | Index panel data | `.X, ..., single` | indexed_frame |
| `qF` | Quick factor creation | `x, ordered, sort, method` | factor |
| `qG` | Quick grouping vector | `x, ordered, sort` | integer vector (class "qG") |
| `finteraction` / `itn` | Combine factors | `..., factor, sort, sep` | factor or qG |
| `radixorder` | Fast radix-based ordering | `..., na.last, decreasing` | integer index vector |
| `roworder` | Reorder rows | `X, ..., na.last` | reordered data frame |
| `colorder` | Reorder columns | `X, ..., pos` | reordered data frame |    

### Data Manipulation

| Function | Purpose | Key args | Returns |
|----------|---------|----------|---------|
| `fsubset` / `sbt` | Fast subset rows + select cols | `.x, subset, ...` | data.frame |
| `ss` | Programmatic row/col subset | `x, i, j, check` | data.frame |
| `fselect` / `slt` | Select columns | `.x, ..., return` | data.frame |
| `get_vars` / `gv` | Get columns by name/index | `x, vars, return, regex` | data.frame or list |
| `num_vars` / `nv` | Select numeric columns | `x` | data.frame |
| `ftransform` / `tfm` | Add/modify/delete columns | `.data, ...` | data.frame |
| `settransform` / `settfm` | In-place ftransform | `.data, ...` | invisible (modifies in place) |
| `fmutate` / `mtt` | dplyr-style mutate | `.data, ..., .keep, .cols` | data.frame |
| `fcompute` | Compute new cols only | `.data, ..., keep` | data.frame |
| `fsummarise` / `smr` | Grouped summary | `.data, ..., .cols` | data.frame |
| `collap` | Advanced aggregation | `X, by, FUN, catFUN, w, custom` | data.frame |
| `across` | Multi-column operations | `.cols, .fns, ..., .names` | (inside fmutate/fsummarise) |
| `frename` / `rnm` | Rename columns | `X, ..., cols` | data.frame |     

### Joins, Pivoting, Binding

| Function | Purpose | Key args | Returns |
|----------|---------|----------|---------|
| `join` | Join two data frames | `x, y, on, how, validate, multiple, column` | data.frame |
| `pivot` | Reshape longer/wider/recast | `data, ids, values, names, how, FUN, fill` | data.frame |
| `rowbind` | Fast row-binding | `..., idcol, fill` | data.frame |   

### Conversion and Summary

| Function | Purpose | Key args | Returns |
|----------|---------|----------|---------|
| `qDF` | Quick convert to data.frame | `X, row.names.col, keep.attr` | data.frame |
| `qDT` | Quick convert to data.table | `X, row.names.col, keep.attr` | data.table |
| `qTBL` | Quick convert to tibble | `X, row.names.col, keep.attr` | tibble |
| `qM` | Quick convert to matrix | `X, row.names.col, keep.attr` | matrix |
| `qsu` | Quick summary statistics | `x, g, w, pid, cols, higher` | qsu object (matrix) |
| `descr` | Detailed column descriptions | `X, ...` | descr object |
| `pwcor` | Pairwise correlations | `X, w, N, P, use` | matrix |
| `qtab` / `qtable` | Fast cross-tabulation | `...` | table |
| `fquantile` | Fast quantiles | `x, probs, w, na.rm` | numeric vector |
| `frange` | Fast range | `x, na.rm` | numeric(2) |
| `fnunique` | Count unique values | `x` | integer |
| `funique` | Unique values/rows | `x, sort, method` | same class as input |
| `fduplicated` | Duplicated values/rows | `x, all` | logical vector |
| `fcount` / `fcountv` | Fast value counts | `x, ...` | data.frame |   

### Configuration

| Function | Purpose | Key args | Returns |
|----------|---------|----------|---------|
| `set_collapse` | Set global options | `nthreads, na.rm, sort, mask, verbose, digits` | invisible (previous options) |
| `get_collapse` | Get current options | (none) | named list |  

### Memory-Efficient Helpers

| Function | Purpose | Key args | Returns |
|----------|---------|----------|---------|
| `setv` | Set values in place | `x, i, value` | invisible (modifies x) |
| `setop` | Arithmetic in place | `x, op, value` | invisible (modifies x) |
| `copyv` | Copy values between vectors | `x, i, value` | invisible (modifies x) |
| `alloc` | Allocate vector | `value, n` | vector of length n |
| `cinv` | Cheap inverse (1/x) | `x` | numeric vector |
| `setattrib` / `setattr` | Set attributes in place | `x, a` | invisible (modifies x) | 

