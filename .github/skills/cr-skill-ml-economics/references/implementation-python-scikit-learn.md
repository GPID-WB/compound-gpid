# Python Implementation with scikit-learn

<!-- Created 2026-09-03. -->

This reference translates the statistical-learning and econometric logic into a
Python workflow. `scikit-learn` is the default general-purpose implementation
ecosystem because its `Pipeline`, `ColumnTransformer`, splitters, estimators,
scorers, and model-selection tools make preprocessing boundaries explicit.
Specialized packages are appropriate when a method or variance estimator is
outside the scikit-learn interface.

## 1. Workflow order

Use this order for a predictive task:

1. define the target, loss, target population, and information set;
2. create a final training/test split matched to the independent unit and time;
3. put all learned preprocessing inside a `Pipeline`;
4. choose an explicit splitter and metrics;
5. tune a small, documented candidate set on training data only;
6. freeze the model, preprocessing, and threshold;
7. fit the finalized pipeline on training data;
8. score the untouched test data once;
9. report baselines, calibration, subgroup errors, stability, and limitations.

`scikit-learn` implements prediction procedures. It does not establish causal
identification. For DML, causal forests, IV, or structural models, use the
causal reference and verify the specialized estimator separately.

## 2. Split before learning transformations

For iid classification observations, a stratified split can preserve class
support. Use `stratify` only when `y` is categorical:

```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    stratify=y,
    random_state=20260903,
)
```

For continuous regression outcomes such as income or welfare, omit stratification:

```python
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    stratify=None,
    random_state=20260903,
)
```

`train_test_split` cannot account for groups. For new-unit prediction, use
indices from `GroupShuffleSplit` and keep every row from a unit on one side:

```python
from sklearn.model_selection import GroupShuffleSplit

splitter = GroupShuffleSplit(
    n_splits=1,
    test_size=0.20,
    random_state=20260903,
)
train_index, test_index = next(splitter.split(X, y, groups=unit_id))
X_train, X_test = X.iloc[train_index], X.iloc[test_index]
y_train, y_test = y.iloc[train_index], y.iloc[test_index]
```

For time-dependent data, sort by time and use `TimeSeriesSplit` or a custom
forward-chaining split. State the initial window, horizon, gap, and whether the
training window expands. Never shuffle future observations into training data.

## 3. Pipeline and ColumnTransformer

A pipeline makes preprocessing part of the estimator. The following pattern
fits imputation, scaling, and encoding within each training fold:

```python
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

numeric_pipeline = Pipeline(
    steps=[
        ("impute", SimpleImputer(strategy="median")),
        ("scale", StandardScaler()),
    ]
)
categorical_pipeline = Pipeline(
    steps=[
        ("impute", SimpleImputer(strategy="most_frequent")),
        ("encode", OneHotEncoder(handle_unknown="ignore")),
    ]
)
preprocessor = ColumnTransformer(
    transformers=[
        ("numeric", numeric_pipeline, numeric_columns),
        ("categorical", categorical_pipeline, categorical_columns),
    ]
)
model = Pipeline(
    steps=[
        ("preprocess", preprocessor),
        ("model", LogisticRegression(max_iter=2000, random_state=20260903)),
    ]
)
```

Fit the `Pipeline` on training data or pass it to a resampling search. Never
create a globally scaled, imputed, target-encoded, PCA-transformed, or screened
matrix before the split. This remains leakage even if the final estimator is
cross-validated.

The project uses polars for new tabular manipulation. Convert to pandas only at
a library boundary when an estimator or helper requires it, and keep that
conversion explicit. A data-library conversion does not change the split or
preprocessing contract.

## 4. Group, temporal, and stratified resampling

Choose the splitter from the target:

```python
from sklearn.model_selection import (
    GroupKFold,
    StratifiedGroupKFold,
    TimeSeriesSplit,
)

group_folds = GroupKFold(n_splits=5)
stratified_group_folds = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=20260903)
time_folds = TimeSeriesSplit(n_splits=5, test_size=12, gap=1)
```

Use `GroupKFold` when every group must be held out together. Use
`StratifiedGroupKFold` only when class support also matters and the resulting
folds remain substantively appropriate. Use `TimeSeriesSplit` for regularly
indexed forward prediction; a custom splitter may be needed for irregular time,
rolling windows, multiple panels, or blocked group-time evaluation.

Stratification preserves class proportions. It does not make dependent rows iid
and does not repair temporal leakage. If a rare class or treatment arm is absent
from a valid group/time fold, report that limitation rather than silently
changing the split.

## 5. Cross-validated metrics and tuning

Use `cross_validate` when several metrics or fit-time diagnostics matter:

```python
from sklearn.model_selection import cross_validate

scoring = {
    "rmse": "neg_root_mean_squared_error",
    "mae": "neg_mean_absolute_error",
    "r2": "r2",
}
cv_results = cross_validate(
    model,
    X_train,
    y_train,
    cv=group_folds,
    groups=unit_id_train,
    scoring=scoring,
    return_train_score=False,
)
```

Record the fact that scikit-learn's negative loss scores must be sign-reversed
for presentation. For classification, define the positive class and probability
column explicitly. For example:

```python
from sklearn.metrics import average_precision_score, recall_score, roc_auc_score

positive_class = "yes"
positive_index = list(final_model.classes_).index(positive_class)
positive_probability = final_model.predict_proba(X_test)[:, positive_index]
roc_auc = roc_auc_score(y_test, positive_probability)
pr_auc = average_precision_score(y_test == positive_class, positive_probability)
recall = recall_score(y_test, final_model.predict(X_test), pos_label=positive_class)
```

Consider `roc_auc`, `average_precision` (PR-AUC), `neg_log_loss`, Brier score,
recall with `pos_label`, and calibration alongside any threshold-dependent
metric. Average precision and trapezoidal PR-AUC are related but not identical;
name the chosen definition.

For hyperparameter tuning:

```python
from sklearn.model_selection import GridSearchCV

search = GridSearchCV(
    estimator=model,
    param_grid={
        "model__C": [0.01, 0.1, 1.0, 10.0],
        "model__penalty": ["l2"],
    },
    cv=group_folds,
    scoring="neg_log_loss",
    refit=True,
    return_train_score=False,
)
search.fit(X_train, y_train, groups=unit_id_train)
final_model = search.best_estimator_
```

For a large or irregular space, `RandomizedSearchCV` can be more economical,
but record the distributions, number of trials, seed, and selection metric. If
tuning and evaluation use the same observations, use nested cross-validation or
preserve a final test set. A search over models, features, transformations, or
metrics is part of the specification and must be reported.

## 6. Final held-out assessment

After freezing the pipeline, parameters, and threshold:

```python
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import numpy as np

predictions = final_model.predict(X_test)
rmse = np.sqrt(mean_squared_error(y_test, predictions))
mae = mean_absolute_error(y_test, predictions)
oos_r2 = 1 - (
    np.sum((y_test - predictions) ** 2)
    / np.sum((y_test - np.mean(y_train)) ** 2)
)
```

The out-of-sample $R^2$ benchmark uses the training mean, not the test mean.
For classification, obtain probabilities, evaluate calibration and ranking,
and choose a threshold using training or validation information only. Never
inspect test performance and then change the model or threshold while retaining
the same test score as final evidence.

Compare with a meaningful baseline: training mean, prevalence rule, linear
model, AR/persistence forecast, or simple policy score. Report metric
uncertainty, subgroup/tail performance, class counts, and error examples.

## 7. Sample weights and survey data

Some estimators accept `sample_weight` in `fit()`, and some scorers accept
weights. When the target is a weighted empirical loss, pass weights at every
supported stage and verify that cross-validation, tuning, calibration, and
scoring use the intended convention. For a pipeline, an estimator-specific
parameter such as `model__sample_weight` may be required; verify the current
scikit-learn metadata-routing behavior for the installed version.

`sample_weight` does not automatically implement a complex survey design. It
does not by itself handle PSUs, stratification, replicate weights, nonresponse,
finite-population corrections, or design-based variance. For population claims,
combine a weighted prediction objective with separately justified survey or
cluster uncertainty. See `survey-panel-and-target-population.md` in this skill
directory.

## 8. Missingness and feature engineering

Fit `SimpleImputer`, encoders, scalers, feature selectors, PCA, target encoders,
and learned aggregates inside the pipeline and resampling loop. If missingness
is outcome- or weight-related, document the mechanism and assess sensitivity.
Do not compute group means, target encodings, or future rolling features using
all rows before the split.

Oversampling and SMOTE must be applied only to the training portion of each
fold. Class weighting changes the loss and is not equivalent to survey weighting.
Keep the two decisions separate.

## 9. Specialized packages

- `doubleml` implements selected DML estimators; verify score, learner, folds,
  cluster/weight, and variance interfaces.
- Established causal-ML libraries can provide causal forests or heterogeneous
  effects; verify honesty, overlap, treatment coding, and inference.
- XGBoost and LightGBM provide boosted trees; document objective, early stopping,
  validation data, seed, and extrapolation behavior.
- `statsmodels` and survey-specific tooling may be needed for design-based or
  econometric estimation outside scikit-learn.

Use specialized packages only where the method's assumptions and output target
are stated. A scikit-learn-compatible API does not turn a predictive learner
into a causal or survey estimator.

## 10. Reproducibility checklist

Record:

- `random_state` values for splits, cross-validation, randomized search, and
  stochastic estimators;
- any explicit NumPy RNG and parallel settings;
- Python and package versions, preferably in `uv.lock` or the project's lockfile;
- feature columns, pipeline steps, estimator, search space, trials, and metric;
- groups, time windows, weights, missingness, and final test boundary;
- baseline, calibration, subgroup errors, and any sensitivity runs.

For GPU or parallel specialized libraries, document hardware and determinism
limits. Re-running code with one seed is not evidence that an invalid split or
leaky feature pipeline is correct.

## References

- Official scikit-learn cross-validation guide:
    https://scikit-learn.org/stable/modules/cross_validation.html
- Official scikit-learn model-selection guide:
    https://scikit-learn.org/stable/model_selection.html
- Official scikit-learn common-pitfalls guide:
    https://scikit-learn.org/stable/common_pitfalls.html
- Hastie, Tibshirani, and Friedman (2009), *The Elements of Statistical
    Learning: Data Mining, Inference, and Prediction*, 2nd ed., Springer. DOI:
    https://doi.org/10.1007/978-0-387-84858-7.
- `doubleml` documentation: https://docs.doubleml.org/
- XGBoost Python API documentation: https://xgboost.readthedocs.io/en/stable/python/
- LightGBM Python API documentation: https://lightgbm.readthedocs.io/en/latest/Python-API.html
