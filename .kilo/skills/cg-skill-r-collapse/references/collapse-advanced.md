# collapse Advanced Reference

Extended collapse reference for data manipulation, summary statistics, joins/pivoting, type system, and short aliases. Load when you need lookup beyond the core statistical functions in [`collapse-reference.md`](collapse-reference.md).

## Data Manipulation Verbs

```r
# Column selection (NSE)
fselect(dt, region, welfare, weight)
fselect(dt, 1:5)
num_vars(dt)   # All numeric columns
cat_vars(dt)   # All categorical/character columns

# Row subsetting
fsubset(dt, region == "EAP" & year > 2010)
fsubset(dt, welfare > 0, region, welfare, weight)  # Subset rows + select cols

# Column transformation (simultaneous evaluation)
ftransform(dt, log_welfare = log(welfare), poor = welfare < 2.15)

# Sequential mutation (can reference new columns)
fmutate(dt,
  welf_log  = log(welfare),
  welf_log2 = welf_log^2
)

# In-place transformation
settransform(dt, log_welfare = log(welfare))

# Renaming
frename(dt, welf = welfare, wt = weight)
setrename(dt, welf = welfare)  # In-place
```

### ftransform vs fmutate

| | `ftransform()` | `fmutate()` |
|--|--|--|
| Evaluation | All RHS simultaneously | Sequential |
| Reference new cols | Cannot | Can (each expr can use the previous) |

## Summary Statistics

```r
# Fast summary (one-pass, with weights)
qsu(dt, w = ~ weight)                              # Overall
qsu(dt, ~ region, w = ~ weight)                    # By region
qsu(dt, ~ region, w = ~ weight, higher = TRUE)     # + skewness, kurtosis

# Panel decomposition (between/within)
qsu(pdt, pid = ~ country, cols = c("welfare", "income"), higher = TRUE)

# Detailed description
descr(dt)

# Fast cross-tabulation (weighted)
qtab(dt$region, dt$year, w = dt$weight)

# Pairwise correlations
pwcor(num_vars(dt), w = dt$weight, N = TRUE, P = TRUE)
```

## Quick Conversion

```r
qDT(x)   # Anything to data.table (fast, minimal checks)
qDF(x)   # To data.frame
qTBL(x)  # To tibble
qM(x)    # To matrix
```

## Row/Column Sweeping

```r
X %c-% fmean(X)     # Subtract column means from each row
X %c/% fsd(X)       # Divide each column by its SD
X %r-% rowSums(X)   # Subtract row sums from each column
X %r/% rowMeans(X)  # Divide each row by its mean
```

## Joins, Pivoting, Binding

```r
# Fast join (all types supported)
join(x, y, on = "id", how = "left")             # Left join
join(x, y, on = "id", how = "inner")            # Inner join
join(x, y, on = c("id" = "key"), how = "anti")  # Anti join with renamed key
join(x, y, on = "id", validate = "1:1", column = ".join")  # Add join indicator

# Reshape
pivot(dt, ids = "id", values = c("y2020", "y2021"), how = "longer",
      names = list(variable = "year", value = "value"))
pivot(dt, ids = "id", values = "income", names = "year", how = "wider")

# Row binding
rowbind(dt1, dt2)        # Fast rbind
rowbind(dt1, dt2, fill = TRUE)  # Fill missing columns with NA
```

## Using collapse Inside data.table

collapse functions work directly inside `dt[, j, by]`:

```r
dt[, .(mean_welf = fmean(welfare, w = weight),
       sd_welf   = fsd(welfare, w = weight),
       n         = fnobs(welfare)),
   by = region]

# Column creation
dt[, welfare_centered := fwithin(welfare, region, weight)]
dt[, welfare_scaled   := fscale(welfare, region, weight)]
dt[, welfare_pct      := fsum(welfare, region, TRA = "%")]
dt[, region_mean      := fmean(welfare, region, weight, TRA = "replace")]
```

## Object Type System

collapse operates on 3 principal types: atomic vectors, matrices, and lists (assumed to be data frames). Fast Statistical Functions dispatch via S3:

| Method | Used for |
|--------|----------|
| `.default` | Atomic vectors |
| `.matrix` | Matrices |
| `.data.frame` | Data frames, data.tables, tibbles |
| `.grouped_df` | `dplyr::group_by()` output |

## Short Aliases

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
| `num_vars` | `nv` |
| `finteraction` | `itn` |

## Common Errors

```r
# Error: result of fgroup_by pipe cannot use :=
result <- dt |> fgroup_by(region) |> fmean(w = weight)
result[, new_col := 1]  # Warning about over-allocation
# Fix: add qDT()
result <- dt |> fgroup_by(region) |> fmean(w = weight) |> qDT()

# Error: na.rm global option changed, welfare returns NA
set_collapse(na.rm = FALSE)
fmean(dt$welfare, g = dt$region, w = dt$weight)  # Returns NA silently
# Fix: restore default
set_collapse(na.rm = TRUE)
# OR override per call:
fmean(dt$welfare, g = dt$region, w = dt$weight, na.rm = TRUE)
```
