---
name: cr-skill-ml-economics
module: research
description: "Theory-first machine learning for economics research. Use for statistical-learning foundations, high-dimensional methods, sample splitting, model selection, out-of-sample evaluation, causal ML, panel and survey data, economic interpretation, or R/Python implementation."
---

# Machine Learning in Economics

Use this skill for ML/Prediction work, ML implementation, or methodology review.
It serves senior econometricians and PhD students: explain the reasoning first,
then provide code only when the task requires it.

## Core workflow

1. Define the goal: prediction, descriptive learning, variable selection, causal
   estimation, heterogeneous treatment effects, or a nuisance function.
2. State the estimand or prediction target, target population, loss, available
   information at prediction time, and data structure (iid, panel, group,
   cluster, temporal, or survey).
3. Select the smallest useful set of references below. Read only one or two references
  needed for the task; do not load all eight by default.
4. Check leakage, sample splitting, preprocessing, weights, seeds, tuning,
  baselines, validation, uncertainty, and final out-of-sample assessment.
5. Separate predictive interpretation from causal or structural claims.

## Reference routing

| Need | Read |
|---|---|
| ESL foundations, loss, risk, complexity, bias-variance | `references/foundations-and-esl.md` |
| High-dimensional prediction, regularization, selection, inference | `references/high-dimensional-and-regularized-methods.md` |
| iid, group, panel, temporal splitting, CV, tuning, evaluation | `references/splitting-resampling-and-evaluation.md` |
| Leakage, preprocessing, and review safeguards | `references/splitting-resampling-and-evaluation.md` |
| Trees, ensembles, importance, SHAP, partial dependence | `references/trees-ensembles-and-interpretation.md` |
| DML, cross-fitting, orthogonality, causal ML | `references/econometric-causal-ml.md` |
| Survey weights, target population, clustering, design limits | `references/survey-panel-and-target-population.md` |
| R implementation with tidymodels | `references/implementation-r-tidymodels.md` |
| Python implementation with scikit-learn | `references/implementation-python-scikit-learn.md` |
| Neural-network method selection | `references/foundations-and-esl.md` |

## Non-negotiable boundaries

- Predictive fit, feature importance, regularized coefficients, and DML do not
  establish causality without an estimand, identification strategy, and stated
  assumptions.
- Never fit preprocessing, feature engineering, imputation, target encoding,
  or group statistics using held-out data. Prevent data leakage inside CV.
- Match the split to the dependence structure. Do not use iid shuffling for
  panel, group, cluster, or temporal data without a defensible target.
- Use explicit numeric seeds and record split, tuning, metric, and package
  decisions. Keep a final test set out of model selection.
- For survey data, identify the target population and justify weights. A
  `sample_weight` argument does not by itself implement clustering,
  stratification, design-based variance, or representativeness.

## Scope

Include a bounded neural-network overview for method selection. This skill does
not cover computer vision, NLP, reinforcement learning, or production MLOps.
