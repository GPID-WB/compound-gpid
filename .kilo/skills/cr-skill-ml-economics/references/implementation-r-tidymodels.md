# R Implementation with tidymodels

<!-- Created 2026-09-03. -->

This reference translates the statistical-learning and econometric logic into
an R workflow. `tidymodels` is the default implementation ecosystem for ML
prediction in this skill: `rsample` defines splits, `recipes` defines
preprocessing, `parsnip` defines models, `workflows` bundles preprocessing and
models, `tune` performs resampled search, and `yardstick` evaluates predictions.
The code patterns are templates; the data structure and estimand still control
the design.

## 1. Workflow order

Use this order for a predictive task:

1. define the target, loss, target population, and information set;
2. create the final training/test split before inspecting test performance;
3. make a recipe using the training data and put it inside a workflow;
4. choose resamples from the independent unit and time structure;
5. tune a small, documented candidate set on training resamples;
6. select and finalize the workflow using a prespecified metric and rule;
7. fit the finalized workflow on the full training partition;
8. use `last_fit()` once on the untouched test partition;
9. report metrics, baselines, calibration, subgroup errors, and limitations.

This is a prediction workflow. For causal ML, load the econometric causal
reference and verify the estimator, score, folds, overlap, and inference
separately.

## 2. Split before preprocessing

For iid data:

```r
library(tidymodels)

set.seed(20260903)
data_split <- initial_split(data, prop = 0.80, strata = outcome)
train_data <- training(data_split)
test_data  <- testing(data_split)
```

`strata` can preserve class proportions, but it does not handle panel, cluster,
or temporal dependence. For grouped data, construct a group-held-out final
split and grouped resamples:

```r
set.seed(20260903)
data_split <- group_initial_split(data, group = unit_id, prop = 0.80)
train_data <- training(data_split)
test_data  <- testing(data_split)
folds <- group_vfold_cv(train_data, group = unit_id, v = 5)
```

For temporal data, sort by time and use a rolling-origin or rolling-window
design. Do not replace a temporal split with `vfold_cv()` merely because it is
convenient. If both group and time constraints matter, construct a custom
`rsample` split that holds out the intended group-time blocks.

## 3. Recipes are fitted estimators

A recipe defines preprocessing, but its statistics are learned when it is
prepped. Put the recipe in a `workflow` and pass that workflow to resampling so
means, scales, imputation values, factor levels, PCA rotations, feature
selection, and target encodings are learned only from each analysis fold.

```r
ml_rec <-
  recipe(outcome ~ ., data = train_data) |>
  update_role(unit_id, new_role = "id") |>
  step_impute_median(all_numeric_predictors()) |>
  step_unknown(all_nominal_predictors()) |>
  step_dummy(all_nominal_predictors()) |>
  step_zv(all_predictors()) |>
  step_normalize(all_numeric_predictors())
```

The imputation step is only an example. Choose it after examining missingness
and the estimand. For MAR prediction, fit the imputer inside each fold. For
inference, multiple imputation and variance combination may be needed. Do not
impute the outcome without stating how that changes the target.

Keep identifiers with a non-predictor role when they help error analysis. Do not
leave identifiers in the predictor set unless their use is substantively and
predictively justified. A unit ID can let a flexible model memorize the panel.

## 4. Model specifications and workflows

For a regularized linear model:

```r
linear_spec <-
  linear_reg(penalty = tune(), mixture = tune()) |>
  set_engine("glmnet") |>
  set_mode("regression")

linear_wf <-
  workflow() |>
  add_recipe(ml_rec) |>
  add_model(linear_spec)
```

Here `mixture = 0` is ridge-like and `mixture = 1` is LASSO-like for engines
that expose the usual elastic-net parameterization. Document the engine's
objective and scaling convention. For a random forest or boosted tree, use a
`parsnip` specification with a named engine and tune only a prespecified set of
complexity controls.

```r
forest_spec <-
  rand_forest(trees = 300, mtry = tune(), min_n = tune()) |>
  set_engine("ranger", importance = "permutation", seed = 20260903) |>
  set_mode("regression")

forest_wf <-
  workflow() |>
  add_recipe(ml_rec) |>
  add_model(forest_spec)
```

Do not add a recipe only because a model is available. Tree models may not need
scaling, but missing values, factor levels, identifiers, and zero-variance
predictors still require an explicit decision.

## 5. Resampling and tuning

For iid training data:

```r
set.seed(20260903)
folds <- vfold_cv(train_data, v = 5)

metrics <- metric_set(rmse, mae)

set.seed(20260903)
tuned <-
  linear_wf |>
  tune_grid(
    resamples = folds,
    grid = 8,
    metrics = metrics,
    control = control_grid(save_pred = FALSE)
  )

best <- select_best(tuned, metric = "rmse")
final_wf <- finalize_workflow(linear_wf, best)
```

For classification, use metrics that match the decision:

```r
# Put the intended positive class first, or pass event_level = "second"
# explicitly when calling the binary metric function.
outcome <- factor(outcome, levels = c("yes", "no"))
classification_metrics <-
  metric_set(roc_auc, pr_auc, accuracy, sens, spec, mn_log_loss)
```

When scoring predictions directly, make the event choice visible:

```r
classification_metrics(
  predictions,
  truth = outcome,
  estimate = .pred_yes,
  event_level = "first"
)
```

Use `group_vfold_cv()` for new-unit prediction and a rolling-origin design for
forecasting. A `vfold_cv()` call is not valid merely because the data have one
row per record. The independent unit controls the resample.

Record the model grid, grid size, metric, fold construction, seed, and selected
configuration. If model classes, recipes, feature sets, or outcomes were also
searched, report those choices. A large unreported `tune_grid()` search is
specification searching.

The starter values above are deliberately modest: five folds, eight candidate
configurations, 300 trees, and no saved resample predictions. For larger survey
or panel data, benchmark fit time and memory first; enable `save_pred = TRUE`,
more trees, or more folds only when the analysis budget and reporting need
justify them.

## 6. Final test assessment

After selecting the workflow on training resamples, use `last_fit()` with the
original split:

```r
final_fit <- last_fit(final_wf, split = data_split, metrics = metrics)
collect_metrics(final_fit)
collect_predictions(final_fit)
```

`yardstick::rsq` is not the training-mean out-of-sample $R^2$ defined in the
statistical reference. Calculate the training-mean OOS R2 explicitly from the
held-out predictions:

```r
test_predictions <- collect_predictions(final_fit)
training_mean <- mean(train_data$outcome, na.rm = TRUE)
training_mean_oos_r2 <- 1 -
  sum((test_predictions$outcome - test_predictions$.pred)^2, na.rm = TRUE) /
  sum((test_predictions$outcome - training_mean)^2, na.rm = TRUE)
```

If `rsq` is also reported, label it as a test-centered or yardstick-specific
metric rather than the training-mean OOS R2.

`last_fit()` fits on the complete training partition and assesses on the test
partition. Do not use test metrics to choose a new recipe, model, threshold,
or feature set and then report the same test metrics as final evidence. If you
must iterate after seeing test results, create a new frozen test set or label
the result exploratory.

Calculate or collect a meaningful baseline: weighted mean, prevalence rule,
linear OLS/logistic model, persistence forecast, or a simple policy score.
Report the training-test split, the primary metric, confidence or variability
information, calibration, and subgroup/tail errors.

## 7. Case weights and survey data

Some tidymodels engines accept `case_weights`, often represented by hardhat
weight classes such as importance or frequency weights. Use the engine's
supported interface when the target is a weighted empirical loss, and verify
whether the weight reaches fitting, tuning, calibration, and yardstick scoring.

Do not imply that `case_weights` implements a complete complex survey design.
It does not automatically handle PSUs, stratification, replicate weights,
nonresponse, finite-population corrections, or design-based variance. Use
survey-specific tools for design operations and document the boundary between a
weighted ML prediction and a survey population estimator. See
`survey-panel-and-target-population.md` in this skill directory.

## 8. Group, temporal, and rare-outcome safeguards

- Use group-held-out resamples when the model must generalize to new units.
- Use rolling-origin resamples when the model must predict future periods.
- Combine group and time restrictions when both sources of dependence matter.
- Use stratification for class support only after honoring group/time separation.
- Apply SMOTE or class balancing within analysis folds, not before splitting.
- Use PR-AUC, recall, calibration, and policy loss for rare outcomes rather than
  relying on accuracy.
- Check whether the yardstick metric uses the same weights and event-level
  definition as the scientific decision.

## 9. Specialized engines

- `glmnet` is useful for ridge, LASSO, and elastic net; verify family, weights,
  standardization, and lambda selection.
- `ranger` is a fast random-forest engine; verify permutation importance,
  case-weight, probability, and sampling options. Its ordinary interface does
  not provide cluster-robust or design-based variance; use cluster-aware splits
  and external uncertainty procedures where required.
- XGBoost and LightGBM provide boosted trees; document early stopping, metric,
  validation data, seed, and extrapolation limits.
- `grf` provides causal/generalized forests; use it only with an identified
  causal target and its required honesty, overlap, and inference checks.
- `DoubleML` or `mlr3` ecosystems can implement DML; verify the score, learner,
  folds, clustering, weights, and variance against the package version.

The starter examples are intentionally bounded: use a smaller tree count,
fold count, grid, and no saved predictions while developing. Increase trees or
save predictions only after setting an explicit fit, thread, and memory budget
for the data size.

A specialized engine may sit outside the full tidymodels abstraction. Keep the
methodological contract explicit instead of presenting package syntax as proof
of correctness.

## 10. Reproducibility checklist

Record:

- `set.seed()` values for initial splits, resamples, tuning, and stochastic
  engines;
- exact package versions and the lockfile used;
- formula, recipe, roles, model engine, metric, and tuning grid;
- group, time, strata, weight, and missingness decisions;
- selected configuration, final test result, baseline, and error slices;
- any engine options that affect parallelism or numerical reproducibility.

Never use a time-derived seed. If parallel execution changes random-number
streams, document the parallel plan and verify repeated output where practical.

## References

- Official tidymodels start guides: https://www.tidymodels.org/start/
- Official resampling guide: https://www.tidymodels.org/start/resampling/
- Official tuning guide: https://www.tidymodels.org/start/tuning/
- Official recipes and workflows guide: https://www.tidymodels.org/start/recipes/
- Kuhn and Johnson (2019), *Feature Engineering and Selection: A Practical
  Approach for Predictive Models*, Chapman and Hall/CRC. DOI:
  https://doi.org/10.1201/9781315108230.
- `ranger` reference manual: https://cran.r-project.org/package=ranger.
- `glmnet` reference manual: https://cran.r-project.org/package=glmnet.
