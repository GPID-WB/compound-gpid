# polars Patterns

## Core Operations

### Reading Data

```python
import polars as pl

# Eager (loads into memory)
df = pl.read_csv("data.csv")
df = pl.read_parquet("data.parquet")

# Lazy (deferred execution — preferred for large data)
lf = pl.scan_csv("data.csv")
lf = pl.scan_parquet("data.parquet")
result = lf.filter(...).select(...).collect()
```

### Selecting Columns

```python
df.select("col1", "col2")
df.select(pl.col("col1"), pl.col("col2"))
df.select(pl.col("^income_.*$"))  # regex
df.select(pl.exclude("temp_col"))
```

### Filtering Rows

```python
df.filter(pl.col("age") > 30)
df.filter((pl.col("age") > 30) & (pl.col("region") == "SSA"))
df.filter(pl.col("country").is_in(["USA", "GBR", "FRA"]))
```

### Adding/Modifying Columns

```python
df.with_columns(
    pl.col("income").log().alias("log_income"),
    (pl.col("income") / pl.col("household_size")).alias("income_per_capita"),
)
```

### Aggregation

```python
df.group_by("region").agg(
    pl.col("income").mean().alias("mean_income"),
    pl.col("income").std().alias("sd_income"),
    pl.len().alias("n"),
)
```

### Sorting

```python
df.sort("income", descending=True)
df.sort("region", "year")
```

## Joins

```python
# Left join
df_a.join(df_b, on="id", how="left")

# Inner join
df_a.join(df_b, on="id", how="inner")

# Multi-column join
df_a.join(df_b, on=["id", "year"], how="left")

# Anti join (rows in A not in B)
df_a.join(df_b, on="id", how="anti")

# Cross join
df_a.join(df_b, how="cross")
```

## Reshaping

```python
# Wide to long (unpivot/melt)
df.unpivot(
    index="id",
    on=["year_2020", "year_2021"],
    variable_name="year",
    value_name="value",
)

# Long to wide (pivot)
df.pivot(on="year", index="id", values="income")
```

## Window Functions

```python
df.with_columns(
    pl.col("income").rank().over("region").alias("income_rank"),
    pl.col("income").mean().over("region").alias("region_mean"),
    pl.col("value").shift(1).over("id").alias("prev_value"),
)
```

## Conditional Logic

```python
df.with_columns(
    pl.when(pl.col("income") > 50000)
    .then(pl.lit("high"))
    .when(pl.col("income") > 25000)
    .then(pl.lit("medium"))
    .otherwise(pl.lit("low"))
    .alias("income_category")
)
```

## Missing Values

```python
df.with_columns(pl.col("income").fill_null(0))
df.with_columns(pl.col("income").fill_null(strategy="forward"))
df.drop_nulls(subset=["income"])
df.filter(pl.col("income").is_not_null())
```

## Performance Tips

1. Use lazy mode (`scan_*` + `.collect()`) for large datasets
2. Use expressions instead of `.map_elements()` / `.apply()`
3. Filter early to reduce data size
4. Select only needed columns early
5. Use `sink_parquet()` for streaming large results
6. Use `pl.concat()` instead of iterative appends
