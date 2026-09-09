# Splitting, Resampling, and Evaluation

<!-- Created 2026-09-03. -->

This reference answers a question that must come before algorithm selection:
what observations should a fitted procedure be expected to generalize to? The
answer determines the split, resampling scheme, preprocessing boundary, metric,
and final assessment. A technically correct estimator evaluated against the
wrong target can still produce a misleading research result.

## 1. Name the generalization target

Write the target in one sentence:

> Predict [outcome] for [new rows, new units, future periods, or target
> population] using information available at [prediction time], minimizing
> [loss or decision cost].

Then record:

- observation and splitting unit;
- whether repeated observations share a person, household, firm, location,
  survey PSU, experiment, or time block;
- the prediction horizon and allowed information set;
- whether the goal is interpolation, extrapolation, transport, or ranking;
- the target population and evaluation weights;
- the primary metric, benchmark, and decision threshold;
- the random seed and exact split or fold construction.

The iid assumption means observations are independent and identically
distributed for the purpose at hand. It should not be inferred from a rectangular
data frame. Panel, clustered, spatial, survey, and time-series observations
usually require a design that keeps their dependence visible.

## 2. Roles of training, resampling, and test data

Use the following vocabulary consistently:

| Partition | Permitted use | Forbidden use |
|---|---|---|
| Training/analysis | Fit parameters, preprocessing, features, and nuisance functions | Treat as unbiased performance evidence |
| Resampling assessment | Tune hyperparameters, compare prespecified candidates, estimate training-sample risk | Reuse as an untouched final score |
| Final test/holdout | One or a small number of frozen final assessments | Tune, screen features, choose the metric, or revise the model after inspection |
| External or later-period data | Transport or temporal robustness check | Quietly relabel as an iid test if the DGP differs |

For a small dataset, k-fold cross-validation can replace a fixed validation set
inside the training partition. It does not eliminate the need for a final test
set when a performance claim has been tuned against the same observations.
Nested cross-validation uses an inner loop for tuning and an outer loop for
performance assessment when an unbiased estimate of the full selection procedure
is needed.

A three-way split is not mandatory in every workflow. It is often wasteful when
cross-validation is used correctly inside a fixed training set. It is mandatory
to preserve a separate final assessment whenever tuning or model comparison has
used the candidate evaluation data.

## 3. iid data

For iid observations, ordinary k-fold cross-validation is a defensible starting
point. Use 5 or 10 folds when the sample supports it, set a numeric seed when
fold assignment is random, and report fold-level variation rather than only the
mean. Repeated k-fold can characterize sensitivity to fold assignment but is not
independent evidence if the same data and search process are repeatedly inspected.

For small samples, leave-one-out can have high variance as an estimate of test
error and can be computationally expensive. It is not a default replacement for
5- or 10-fold CV. Bootstrap resampling estimates a different object from
cross-validation and should be chosen for a stated purpose.

## 4. Group, clustered, and panel data

If a model should generalize to new groups, every observation from a group must
remain in one fold. In Python, `GroupKFold`, `GroupShuffleSplit`,
`LeaveOneGroupOut`, or `StratifiedGroupKFold` can construct such splits. In R,
use a grouped resampling design or construct group-held-out indices explicitly.
The group identifier is supplied to the splitter; it is not necessarily a
predictor.

Distinguish two targets:

- **New rows within known units:** past observations from a unit may be in the
  analysis data if that information will be available at prediction time. The
  evaluation must still avoid using the outcome or future covariates from the
  assessment row.
- **New units:** no row from an assessment unit may appear in the analysis fold.
  Random row k-fold is invalid because unit-specific information leaks across
  folds and produces optimistic error.

For panel data, decide whether time is also ordered. A group split alone does
not prevent future information from entering a training fold, and a temporal
split alone does not prevent the same unit from appearing on both sides if the
target is new-unit prediction. Use a blocked group-time design when both
constraints apply.

## 5. Temporal and forecasting data

For time-dependent data, training observations must precede the assessment
horizon. `TimeSeriesSplit` in scikit-learn implements expanding training windows
for regularly indexed data; rolling-origin or rolling-window resampling provides
the analogous R design. State the initial window, assessment horizon, gap,
window size, and whether the window expands.

Do not shuffle time series before splitting. Features must use only information
available at their timestamp. Rolling means, lags, aggregates, revisions,
prices, and labels must be checked for look-ahead. A gap may be needed when
outcomes or features overlap across the boundary. Compare forecast models over
the same horizons and use a time-series forecast-comparison procedure such as a
Diebold-Mariano test when its assumptions fit the comparison.

## 6. Stratification and rare outcomes

Stratification preserves approximate class proportions across folds. It can
prevent a rare class from disappearing from an assessment fold, but it is not a
substitute for group separation, temporal ordering, or an identification design.
It can also reduce the observed variation across folds, so report the class
counts and do not overinterpret a small standard deviation.

When the positive class is rare, accuracy may be close to the majority-class
baseline. Consider:

- precision, recall, F1, and precision-recall AUC (PR-AUC);
- ROC-AUC as a complementary ranking measure;
- log loss and Brier score for probabilities;
- calibration at the operating threshold;
- cost-weighted loss or expected policy utility;
- subgroup performance and the number of positive cases per fold.

Class weights and oversampling change the fitted objective. If SMOTE or another
synthetic method is used, it must run only on the analysis portion of each fold.
Applying it before splitting leaks information and can duplicate or interpolate
across assessment observations.

## 7. Preprocessing and data leakage

A preprocessing operation is part of the fitted procedure. Fit it separately in
each analysis fold and apply the learned transformation to that fold's
assessment observations. This includes:

- centering, scaling, normalization, and winsorization;
- imputation and missingness indicators;
- dummy or ordinal encoding and rare-level pooling;
- PCA, factor extraction, feature screening, and variable transformations;
- target encoding, group aggregates, and outcome-derived features;
- class balancing, SMOTE, and synthetic data generation;
- feature selection based on correlations, p-values, or model importance.

A scikit-learn `Pipeline`/`ColumnTransformer` or a tidymodels `recipe` inside a
`workflow` keeps preprocessing inside resampling. A global transformed matrix
can still leak information even when the final estimator is cross-validated.
Document the information set and check whether a feature is available at the
actual prediction time. Target leakage and temporal leakage are often more
serious than a forgotten scaler.

## 8. Hyperparameter and model search

For every search, record:

- model classes and parameter search space;
- grid size or number of random/Bayesian trials;
- resampling scheme, seed, metric, and tie-breaking rule;
- preprocessing and feature-engineering choices searched;
- whether the test set was untouched;
- selected parameters and the uncertainty or near-ties around them.

A broad undocumented search over model classes, outcomes, transformations,
features, split rules, and metrics is specification searching. A small parameter
grid is still a research decision. Nested cross-validation is appropriate when
the evaluation estimate must include the tuning process, but it does not repair
an invalid target, leakage, or poor data structure.

## 9. Metrics and out-of-sample assessment

For regression predictions $\widehat y_i$ and outcomes $y_i$, common metrics are

$$
RMSE = \sqrt{\frac{1}{n}\sum_i (y_i-\widehat y_i)^2},
\qquad
MAE = \frac{1}{n}\sum_i |y_i-\widehat y_i|.
$$

An out-of-sample $R^2$ should compare the model with a benchmark defined without
using test outcomes. For a test set, the unconditional training mean gives

$$
R^2_{OOS} = 1 -
\frac{\sum_{i\in test}(y_i-\widehat y_i)^2}
{\sum_{i\in test}(y_i-\overline y_{train})^2}.
$$

A negative value means the model loses to that benchmark under the stated loss.
Do not silently use the test mean in the denominator, since that gives the
benchmark information from the test outcomes.

For unequal-probability samples, a weighted metric may target population risk:

$$
\widehat R_w(f) =
\frac{\sum_{i\in A} w_i L(y_i, f(x_i))}
{\sum_{i\in A} w_i}.
$$

The meaning of $w_i$, its normalization, and any design-based variance must be
stated. See the survey reference before treating weighted scores as population
performance.

Always compare against a meaningful baseline: a training mean, linear OLS,
logistic regression, persistence or AR model, prevalence rule, or a simple
policy score. Inspect calibration, subgroup/error slices, tails, and the number
of assessment observations. One aggregate metric can hide failure for the
population or subgroup that matters economically.

## 10. Cross-fitting versus performance CV

Cross-fitting is a sample-splitting device for estimating nuisance functions in
an orthogonal causal score. It is not the same as reporting cross-validated
prediction error, although both use held-out predictions. The causal reference
specifies when cross-fitting is appropriate. In either case, held-out
predictions must be produced without fitting the relevant transformation or
nuisance model on the observation being scored.

## 11. Evaluation checklist

Before accepting an evaluation result, verify:

- target population, prediction horizon, and information set are explicit;
- split unit matches the intended generalization target;
- iid, group, panel, temporal, survey, and overlap assumptions are considered;
- preprocessing and feature creation occur inside analysis folds;
- tuning and model selection do not inspect the final test set;
- all random operations have numeric seeds and split records;
- primary and secondary metrics match the decision and outcome prevalence;
- a baseline and held-out out-of-sample result are reported;
- subgroup, calibration, error, and stability checks are included;
- any forecast comparison or uncertainty statement has the right dependence
  structure.

## References

- Hastie, Tibshirani, and Friedman (2009), *The Elements of Statistical
  Learning: Data Mining, Inference, and Prediction*, 2nd ed., Springer,
  Chapters 7 and 18. DOI: https://doi.org/10.1007/978-0-387-84858-7.
- Arlot and Celisse (2010), "A survey of cross-validation procedures for model
  selection," *Statistics Surveys*, 4, 40-79. DOI:
  https://doi.org/10.1214/09-SS054.
- Varma and Simon (2006), "Bias in error estimation when using cross-validation
  for model selection," *BMC Bioinformatics*, 7, 91. DOI:
  https://doi.org/10.1186/1471-2105-7-91.
- Bergmeir, Hyndman, and Koo (2018), "A note on the validity of cross-validation
  for evaluating autoregressive time series prediction," *Computational
  Statistics & Data Analysis*, 120, 70-83. DOI:
  https://doi.org/10.1016/j.csda.2017.11.003.
- Diebold and Mariano (1995), "Comparing predictive accuracy," *Journal of
  Business & Economic Statistics*, 13(3), 253-263. DOI:
  https://doi.org/10.2307/1392185.
- Official scikit-learn model-selection guide:
  https://scikit-learn.org/stable/model_selection.html
- Official tidymodels resampling guide:
  https://www.tidymodels.org/start/resampling/
