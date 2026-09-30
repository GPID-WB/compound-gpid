---
date: 2026-07-31
name: cr-skill-measurement
module: research
description: "Measurement and classification methodology for economics research.
  Load for composite indicators, ranking/classification thresholds, clustering,
  weighting sensitivity, and comparability checks across units and over time.
  Grounded in OECD/JRC, Alkire-Foster, and cluster-validity standards."
---

# CR Measurement And Classification

Reference skill for Measurement/Classification research tasks in `/cr-*`
workflows.

## 1. Composite Indicators (OECD/JRC)

Use OECD/JRC Handbook guidance for composite indicator construction:
- Define the concept and indicator set before computation.
- Document normalization choice and why it is appropriate.
- Document weighting scheme: equal, expert/budget-allocation, or data-driven.
- Document aggregation choice: linear vs geometric, including compensability.
- Run sensitivity analysis on weighting, normalization, and aggregation.

Required disclosure:
- Indicator inclusion and exclusions.
- Weight source and rationale.
- Aggregation and normalization rationale.

## 2. Multidimensional Measurement (Alkire-Foster)

For deprivation-style classification:
- Define deprivation cutoffs per indicator.
- Define poverty cutoff `k`.
- Report censored headcount and decomposability outputs.
- Treat indicator and weight choices as normative decisions that must be logged.

## 3. Clustering And Cluster Validity

Cluster assignments are claims and require validation evidence.

Named validity sources:
- Silhouette width (Rousseeuw, 1987).
- Gap statistic (Tibshirani, Walther, and Hastie, 2001).
- Bootstrap/resampling stability (Hennig, 2007).

Minimum checks:
- Report chosen `k` and candidate alternatives.
- Report at least one internal index (silhouette or gap).
- Report stability under resampling.

## 4. Thresholding And Classification

- Justify cutoff values explicitly.
- Check boundary sensitivity near thresholds.
- Flag units whose class changes under plausible threshold variation.

## 5. Comparability Rules (P0)

Comparability is blocking when claims depend on cross-unit or over-time ranking.

Over-time comparability:
- Stable definition across vintages.
- Stable coverage or explicit adjustment.
- Stable method or explicit method-change attribution.

Across-unit comparability:
- Harmonized definitions and coverage before ranking.
- Unit-specific methodology deviations must be disclosed.

## 6. Artifact Contracts (Produced By /cr-work, Audited By Agent)

`/cr-work` produces artifacts; `@cr-measurement-integrity` audits them.
The agent never recomputes statistics.

Path: `c-research/measurement/weighting-sensitivity.yaml`
Schema contract:
```yaml
baseline:
  weighting: "equal"
  normalization: "zscore"
  aggregation: "linear"
scenarios:
  - id: "scenario-1"
    weighting: "expert"
    normalization: "minmax"
    aggregation: "geometric"
    rank_correlation_vs_baseline: 0.91
    max_rank_shift: 6
```

Path: `c-research/measurement/cluster-validity.yaml`
Schema contract:
```yaml
selected_k: 4
candidates: [3, 4, 5]
indices:
  silhouette: 0.42
  gap_statistic: 0.31
stability:
  method: "bootstrap"
  cluster_jaccard:
    c1: 0.78
    c2: 0.74
    c3: 0.69
    c4: 0.72
```

Path: `c-research/vintages/<study-slug>-vintage-manifest.yaml`
Schema contract:
```yaml
study: "example-study"
vintage: "2026Q3"
coverage_changes:
  added_units: []
  removed_units: []
harmonization:
  definition_changes: []
  imputation_changes: []
method_changes: []
change_attribution:
  real_change_claim_supported: true
  notes: "Ranking shift primarily due to coverage expansion"
```

## 7. Verification Depth By Review Tier (Audit-Only)

Light:
- Disclosure presence and schema well-formedness.

Standard:
- Required artifacts present and summaries consistent with reported claims.

Thorough:
- Cross-check artifact summary values against asserted ranking/cluster claims.

No tier recomputes statistics. All checks consume `/cr-work` artifacts.

## 8. Anti-Patterns

- Claiming ranking robustness without a weighting sensitivity artifact.
- Reporting cluster labels without validity/stability evidence.
- Comparing vintages without coverage/method attribution.
- Treating threshold choice as purely technical and undocumented.