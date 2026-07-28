# polars Patterns

## Core Operations

### Reading Data

```python
import polars as pl

# Eager (loads into memory — use for small/medium data)
df = pl.read_csv("data.csv")
df = pl.read_parquet("data.parquet")

# Lazy (deferred execution — preferred for large data and pipelines)
lf = pl.scan_csv("data.csv")
lf = pl.scan_parquet("data.parquet")
result = lf.filter(...).select(...).collect()

# Read only needed columns (faster I/O)
df = pl.read_parquet("data.parquet", columns=["id", "welfare", "year"])
lf = pl.scan_csv("data.csv").select(["id", "welfare", "year"])
```

### Selecting Columns

```python
df.select("col1", "col2")
df.select(pl.col("col1"), pl.col("col2"))
df.select(pl.col("^income_.*$"))  # regex pattern
df.select(pl.exclude("temp_col"))
df.select(pl.col(pl.Float64))     # select all float columns by dtype
```

### Filtering Rows

```python
df.filter(pl.col("age") > 30)
df.filter((pl.col("age") > 30) & (pl.col("region") == "SSA"))
df.filter(pl.col("country").is_in(["USA", "GBR", "FRA"]))
df.filter(pl.col("welfare").is_not_null())
df.filter(pl.col("welfare").is_between(0, 99_999))
```

### Adding and Modifying Columns

```python
df.with_columns(
    pl.col("income").log().alias("log_income"),
    (pl.col("income") / pl.col("household_size")).alias("income_pc"),
    pl.col("year").cast(pl.Int32),
)

# Multiple transforms in one pass — always prefer this over chaining with_columns
df.with_columns(
    log_income  = pl.col("income").log(),
    income_pc   = pl.col("income") / pl.col("household_size"),
    is_poor     = pl.col("income") < 2.15,
)
```

### Aggregation

```python
df.group_by("region").agg(
    pl.col("income").mean().alias("mean_income"),
    pl.col("income").std().alias("sd_income"),
    pl.col("income").median().alias("median_income"),
    pl.col("income").quantile(0.1).alias("p10_income"),
    pl.len().alias("n"),
)

# Multiple group-by keys
df.group_by("region", "year").agg(
    pl.col("welfare").mean(),
    pl.col("weight").sum().alias("total_weight"),
)
```

### Sorting

```python
df.sort("income", descending=True)
df.sort(["region", "year"], descending=[False, True])
df.sort("income", nulls_last=True)
```

---

## Joins

```python
# Left join — preserve all rows from left
df_a.join(df_b, on="id", how="left")

# Inner join — only matched rows
df_a.join(df_b, on="id", how="inner")

# Full outer join
df_a.join(df_b, on="id", how="full")

# Multi-column join key
df_a.join(df_b, on=["country", "year"], how="left")

# Anti join — rows in A not in B (useful for unmatched diagnostics)
df_a.join(df_b, on="id", how="anti")

# Validate join cardinality (catches accidental row multiplication)
df_a.join(df_b, on="id", how="left", validate="m:1")
# Options: "1:1", "1:m", "m:1", "m:m"
```

---

## Reshaping

```python
# Wide to long (melt/unpivot)
df.unpivot(
    index="id",
    on=["year_2020", "year_2021", "year_2022"],
    variable_name="year",
    value_name="value",
)

# Long to wide (pivot)
df.pivot(on="year", index="id", values="welfare", aggregate_function="mean")
```

---

## Window Functions

```python
df.with_columns(
    pl.col("income").rank().over("region").alias("income_rank_in_region"),
    pl.col("income").mean().over("region").alias("region_mean_income"),
    pl.col("income").shift(1).over("id").alias("income_lag1"),
    pl.col("income").pct_change().over("id").alias("income_growth"),
    pl.col("income").cum_sum().over("region").alias("cumulative_income"),
)
```

---

## Conditional Logic

```python
# Simple binary condition
df.with_columns(
    pl.when(pl.col("income") < 2.15)
    .then(pl.lit(True))
    .otherwise(pl.lit(False))
    .alias("is_poor")
)

# Multi-branch (equivalent to case_when in R / dplyr)
df.with_columns(
    pl.when(pl.col("income") < 2.15)
    .then(pl.lit("extreme_poor"))
    .when(pl.col("income") < 3.65)
    .then(pl.lit("poor"))
    .when(pl.col("income") < 6.85)
    .then(pl.lit("near_poor"))
    .otherwise(pl.lit("non_poor"))
    .alias("poverty_category")
)
```

---

## Missing Values

```python
df.with_columns(pl.col("income").fill_null(0))
df.with_columns(pl.col("income").fill_null(strategy="forward"))
df.with_columns(pl.col("income").fill_null(pl.col("income").mean()))
df.drop_nulls(subset=["income", "weight"])
df.filter(pl.col("income").is_not_null())

# Null counts for QA
null_report = df.select(pl.all().null_count())
```

> **WARNING — never use `fill_null(0)` on welfare or income columns.**
> Null welfare means *data is missing*, not zero consumption. Filling with `0`
> creates spurious extreme-poor households and directly inflates poverty rates.
> Instead, drop nulls explicitly before poverty computation and log the weight share lost:
>
> ```python
> n_null = df["welfare"].null_count()
> if n_null > 0:
>     lost_weight_share = (
>         df.filter(pl.col("welfare").is_null())["weight"].sum()
>         / df["weight"].sum()
>     )
>     logger.warning("Dropping null welfare", n=n_null, weight_share=round(lost_weight_share, 4))
> df = df.drop_nulls(subset=["welfare"])
> ```

---

## Schema Validation

Always validate column presence and dtypes before processing. A `year` column
read as `String` instead of `Int32` silently produces empty filter results
or broken joins — no error is raised.

```python
# Define expected schema as a module-level constant
SURVEY_SCHEMA: dict[str, pl.DataType] = {
    "welfare": pl.Float64,
    "weight":  pl.Float64,
    "year":    pl.Int32,
    "country": pl.String,
}


def validate_schema(df: pl.DataFrame, expected: dict[str, pl.DataType]) -> None:
    """Validate DataFrame columns and dtypes. Raise on any mismatch."""
    missing = [col for col in expected if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    mismatches = {
        col: {"expected": str(expected[col]), "got": str(df[col].dtype)}
        for col in expected
        if col in df.columns and df[col].dtype != expected[col]
    }
    if mismatches:
        raise TypeError(f"Schema dtype mismatch: {mismatches}")


# Enforce dtype consistency at read time — prevents cross-dataset join failures
SCHEMA_OVERRIDES: dict[str, pl.DataType] = {
    "year":    pl.Int32,
    "welfare": pl.Float64,
    "weight":  pl.Float64,
    "country": pl.String,
}

df = pl.read_parquet("data.parquet", schema_overrides=SCHEMA_OVERRIDES)
lf = pl.scan_csv("data.csv", schema_overrides=SCHEMA_OVERRIDES)
```

---

## Lazy Evaluation — When and How

Use lazy mode for any pipeline operating on more than ~100k rows or multiple files.

```python
# Pattern: scan → transform chain → collect once
result = (
    pl.scan_parquet("data/surveys/*.parquet")   # reads nothing yet
    .filter(pl.col("year") >= 2010)             # pushed to scan — reads less
    .select(["id", "welfare", "weight", "year"])
    .with_columns(
        log_welfare = pl.col("welfare").log(),
        is_poor     = pl.col("welfare") < 2.15,
    )
    .group_by("year")
    .agg(
        pl.col("welfare").mean().alias("mean_welfare"),
        pl.col("is_poor").mean().alias("poverty_rate"),
    )
    .sort("year")
    .collect()   # executes entire pipeline here, once
)

# For very large output: stream to disk without loading into memory
(
    pl.scan_parquet("data/raw/*.parquet")
    .filter(pl.col("year") == 2022)
    .sink_parquet("data/processed/2022.parquet")  # never fully in RAM
    # ⚠️  sink_parquet uses the streaming engine — not all ops are supported.
    # If you get errors, use .collect(streaming=True) as a fallback:
    # .collect(streaming=True)   # chunk-based processing, returns a DataFrame
)

# ⚠️  Glob scan assumes all matched files share the same schema.
# GPID survey files often differ across years (new columns, renames).
# For heterogeneous schemas, use diagonal concat:
import glob
frames = [pl.scan_parquet(f) for f in glob.glob("data/*.parquet")]
combined = pl.concat(frames, how="diagonal_relaxed").collect()
# "diagonal_relaxed" fills missing columns with nulls and casts mismatched types gracefully.

# Decision guide:
# .collect()                — results fit in RAM; fully supported; simplest
# .collect(streaming=True)  — large data, need a DataFrame result; chunk-based
# .sink_parquet()           — output goes directly to disk; zero peak RAM overhead
```

---

## Performance Profiling

**Profile before optimizing.** Intuition is wrong; measurement is right.
Run `memray` or `cProfile` before making any performance change.
Only then look at expressions vs .map_elements().

```python
import time
import polars as pl

# Quick timing
start = time.perf_counter()
result = expensive_operation(df)
elapsed = time.perf_counter() - start
print(f"Elapsed: {elapsed:.3f}s  Rows: {result.height:,}")

# Lazy plan inspection — see what polars will execute
lf = pl.scan_parquet("data/*.parquet").filter(...).select(...)
print(lf.explain(optimized=False))  # unoptimized plan — what you wrote
print(lf.explain(optimized=True))   # optimized plan — what polars will execute
# Note: optimized=True is the default since polars ≥ 0.19
```

```bash
# Memory profiling — install memray
uv add --dev memray

# Profile a script
python -m memray run -o output.bin my_script.py
python -m memray flamegraph output.bin   # generates HTML flamegraph

# CPU profiling — built-in cProfile
python -m cProfile -o output.prof my_script.py
python -m pstats output.prof  # interactive browser
# Or:
uv add --dev snakeviz
snakeviz output.prof          # visual browser
```

**Common polars performance mistakes:**

```python
# WRONG — Python loop, defeats vectorization entirely
results = []
for row in df.iter_rows(named=True):
    results.append(row["income"] * 1.1)
df = df.with_columns(pl.Series("income_adj", results))

# RIGHT — expression, runs in Rust
df = df.with_columns(
    (pl.col("income") * 1.1).alias("income_adj")
)

# WRONG — .map_elements() is a Python loop with overhead
df = df.with_columns(
    pl.col("income").map_elements(lambda x: x * 1.1).alias("income_adj")
)

# RIGHT — use native expression
df = df.with_columns(
    (pl.col("income") * 1.1).alias("income_adj")
)

# WRONG — unnecessary .to_pandas() round-trip
pd_df = df.to_pandas()
pd_df["income_adj"] = pd_df["income"] * 1.1
df = pl.from_pandas(pd_df)

# RIGHT — stay in polars
df = df.with_columns(
    (pl.col("income") * 1.1).alias("income_adj")
)

# WRONG — collecting in a loop
frames = []
for year in years:
    frames.append(pl.scan_parquet(f"data/{year}.parquet").collect())
combined = pl.concat(frames)

# RIGHT — scan all at once, let polars parallelize
combined = pl.scan_parquet("data/*.parquet").collect()
# Or with explicit paths:
combined = pl.concat([
    pl.scan_parquet(f"data/{year}.parquet") for year in years
]).collect()
```
