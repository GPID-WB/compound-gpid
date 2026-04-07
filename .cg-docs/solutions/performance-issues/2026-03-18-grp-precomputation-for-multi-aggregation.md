---
date: 2026-03-18
title: "Pre-compute GRP once for blocks with multiple aggregations over the same grouping"
category: "performance-issues"
language: "R"
tags: [collapse, GRP, fmean, fsum, grouped-aggregation, performance, welfare-measurement, regional-analysis]
root-cause: "Each collapse f*() call with g = dt$region independently computes the group structure; 4 consecutive calls on the same grouping variable do 4x redundant work"
severity: "P2"
---

# Pre-compute GRP Once for Blocks with Multiple Aggregations over the Same Grouping

## Problem

A common pattern in GPID welfare code computes several statistics by region in consecutive calls:

```r
fgt_region <- data.table(
  region = unique(dt$region),
  fgt0   = fmean(dt$poor,   g = dt$region, w = dt$weight),
  fgt1   = fmean(dt$gap,    g = dt$region, w = dt$weight),
  fgt2   = fmean(dt$gap_sq, g = dt$region, w = dt$weight),
  n      = fnobs(dt$poor,   g = dt$region)
)
```

Each call passes `g = dt$region` (a raw vector). Internally, collapse must sort and hash that vector
to build a `GRP` object for grouping every single time. With 4 calls on the same grouping variable,
the group structure is built **4 times redundantly**.

On surveys with 50k+ households and 20+ regions this is noticeable; on the full GPID microdata
(millions of rows) it becomes a meaningful bottleneck.

## Root Cause

collapse's Fast Statistical Functions accept `g` as a raw vector **or** a pre-built `GRP` object.
When given a vector they silently construct the `GRP` internally on every call — convenient but
wasteful when the same grouping is reused. Authors writing one aggregation at a time miss this
because the cost is invisible per-call.

## Solution

Pre-compute the `GRP` object once and pass it to all subsequent aggregation calls:

```r
# ✅ Compute group structure once
g_region <- GRP(dt, ~ region)   # or GRP(dt$region) for a single vector

fgt_region <- data.table(
  region = g_region$groups$region,   # group labels from the GRP object
  fgt0   = fmean(dt$poor,   g = g_region, w = dt$weight),
  fgt1   = fmean(dt$gap,    g = g_region, w = dt$weight),
  fgt2   = fmean(dt$gap_sq, g = g_region, w = dt$weight),
  n      = fnobs(dt$poor,   g = g_region)
)
```

### When to apply

Apply this pattern whenever **3 or more** collapse aggregation calls share the same grouping
variable(s) in the same block. For one or two calls the overhead is negligible and the simpler
`g = dt$region` syntax is fine.

### GRP structure

A `GRP` object contains 9 elements (see `collapse-reference.md`):

| Element | Description |
|---------|-------------|
| `$ngroups` | Number of unique groups |
| `$groups` | data.frame of group-label columns |
| `$group.id` | Integer vector: which group each row belongs to |
| `$group.sizes` | Integer: how many rows per group |
| `$order` | Integer permutation vector for sorting |
| `$ordered` | Logical flags (is sorted + is sorted call) |
| `$call` | The call used to create it |
| `$sort` | Whether rows were sorted during construction |
| `$gsorted` | Whether data is already grouped-sorted |

Extract group labels from `g_region$groups` (a data.frame), not `unique(dt$region)` — the GRP
group order may differ from the order of first appearance in the data.

## Prevention

- In any block that aggregates over the same variable more than twice, always pre-compute `GRP` first
- Add a comment `# pre-compute GRP to avoid N redundant grouping passes` at the GRP line
- See `welfare-patterns.md` FGT Regional section for the canonical example of this pattern

## Related

- [`collapse-reference.md`](../../../../.github/skills/cg-skill-r-collapse/references/collapse-reference.md) — GRP object structure, all 9 elements
- [`welfare-patterns.md`](../../../../.github/skills/cg-skill-r-analytical/workflows/welfare-patterns.md) — FGT regional block using this pattern
- [`survey-analysis.md`](../../../../.github/skills/cg-skill-r-analytical/workflows/survey-analysis.md) — similar pattern for by-region survey estimates
