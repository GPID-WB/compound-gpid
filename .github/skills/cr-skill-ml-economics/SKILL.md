---
name: cr-skill-ml-economics
module: research
description: "Machine learning methods for economics research. Covers
  LASSO/ridge/elastic-net for high-dimensional economics, random forests
  and boosting for prediction, cross-validation done right (panel CV,
  time-series CV, stratified CV by group), out-of-sample assessment,
  post-selection inference (debiased LASSO), Chernozhukov-style cross-fitting,
  variable importance with economic interpretation, dimension reduction and
  feature selection, survey-weighted ML for complex-design survey data,
  missing value handling in ML pipelines, class imbalance and rare events,
  data leakage detection, hyperparameter search transparency, and when ML is
  appropriate vs when it is not. Loaded by @cr-ml-methodology for ML/Prediction
  and Implementation tasks."
---

# ML in Economics

Reference skill for machine learning methods applied to economics research.
Covers method selection, correct evaluation, and economic interpretation.

---

## 1. When ML Is (and Isn't) Appropriate in Economics

**When to use**: Prediction tasks where the goal is minimizing out-of-sample
forecast error, not estimating a causal parameter. Also useful for: variable
selection before structural estimation, heterogeneous treatment effect
estimation (causal forest), forming ML-based first stages in double ML / IV.

**Key distinction**: ML optimizes prediction accuracy; econometrics targets
causal identification. They serve different goals. A model with high R² is
not evidence of causality.

| Goal | Appropriate tool |
|------|-----------------|
| Predict future outcomes | ML (LASSO, random forest, gradient boosting) |
| Estimate causal effect of X on Y | IV, RDD, DiD, structural model |
| Select controls before causal analysis | LASSO (double selection, Belloni et al.) |
| Heterogeneous treatment effects | Causal forest (Athey, Tibshirani, Wager) |
| High-p first stage (ML IV) | LASSO first stage + double ML cross-fitting |

**Athey & Imbens (2019)** guidance: ML is valuable in economics when used
(a) for prediction sub-tasks within a causal framework, or (b) for
heterogeneity analysis after identification is established.

**Anti-patterns**:
- Reporting ML model R² as evidence for a theory
- Using LASSO coefficients as causal estimates without double selection
- Claiming "ML predicts well, therefore the mechanism is X"

---

## 2. Penalized Regression (LASSO / Ridge / Elastic Net)

**When to use**: p > n settings, variable selection, multicollinearity,
regularized prediction.

**Key patterns**:

```r
# R — glmnet (canonical)
library(glmnet)
x <- model.matrix(y ~ ., data = df)[, -1]
cv_fit <- cv.glmnet(x, df$y, alpha = 1)          # alpha=1: LASSO
best_lambda <- cv_fit$lambda.min                  # or lambda.1se for sparsity
coef(cv_fit, s = "lambda.min")

# Post-LASSO OLS (Belloni et al. double selection)
library(hdm)
rlasso_fit <- rlasso(y ~ ., data = df)            # rigorous LASSO
# coef() includes intercept — drop with [-1] before selecting variables
selected_vars <- names(which(coef(rlasso_fit)[-1] != 0))
ols_fit <- lm(y ~ ., data = df[, c("y", selected_vars)])
```

```python
# Python — scikit-learn
from sklearn.linear_model import LassoCV, ElasticNetCV, RidgeCV
from sklearn.preprocessing import StandardScaler

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)  # fit only on train
lasso = LassoCV(cv=5, random_state=42).fit(X_scaled, y_train)
```

```stata
* Stata — lasso2 / cvlasso (SSC)
ssc install lasso2
cvlasso y x1 x2 x3, lopt nfolds(10) seed(42)
```

**Penalty selection**: Always use CV (`cv.glmnet`, `LassoCV`), never
hand-tune lambda without CV evidence.

**Economic interpretation**: LASSO coefficients are shrunk — do not interpret
magnitude as OLS coefficients. Use post-LASSO OLS or `hdm::rlasso` for inference.

**Double selection (Belloni, Chernozhukov, Hansen 2014)**: When estimating
effect of D on Y controlling for X (high-dimensional), run LASSO of Y on X
*and* LASSO of D on X; use the union of selected variables as controls in OLS.
This yields valid inference even after selection.

**Anti-patterns**:
- Interpreting regularized coefficients as causal effects
- Using `lambda.min` when sparsity matters (prefer `lambda.1se`)
- Not standardizing predictors before penalized regression
- Running `cv.glmnet` without setting a seed (`set.seed()` before every call)

**References**: Tibshirani (1996); Belloni, Chernozhukov, Hansen (2014, ReStud);
Bühlmann & van de Geer (2011).

---

## 2a. Survey-Weighted ML (GPID requirement)

**Critical for GPID**: All GPID input data are complex-design household surveys
(stratified, clustered, probability-weighted). Fitting any ML model without
survey weights minimises a sample-convenience loss, not a population-level
loss. On surveys that oversample urban households, an unweighted LASSO learns
urban income-poverty relationships — national poverty predictions are silently
biased. For official WB poverty statistics this constitutes silent data
corruption.

**R patterns**:

```r
# glmnet / cv.glmnet with survey weights
library(glmnet)
x      <- model.matrix(y ~ ., data = df)[, -1]
cv_fit <- cv.glmnet(x, df$y, alpha = 1,
                    weights = df$survey_weight)   # <-- required

# ranger (random forest) with case weights
library(ranger)
set.seed(42)
rf <- ranger(y ~ ., data = df,
             case.weights = df$survey_weight,     # <-- required
             seed = 42)

# xgboost: pass weights via DMatrix
dtrain <- xgb.DMatrix(data = x_train, label = y_train,
                       weight = df_train$survey_weight)  # <-- required
```

```python
# scikit-learn: pass sample_weight to fit()
from sklearn.linear_model import LassoCV
lasso = LassoCV(cv=5, random_state=42)
lasso.fit(X_train, y_train,
          sample_weight=df_train['survey_weight'])   # <-- required

# RandomForestRegressor
from sklearn.ensemble import RandomForestRegressor
rf = RandomForestRegressor(n_estimators=500, random_state=42)
rf.fit(X_train, y_train,
       sample_weight=df_train['survey_weight'])       # <-- required
```

**Common GPID weight variable names**: `survey_weight`, `wgt`, `hhweight`,
`pw`, `popweight`, `weight_ind`. Verify the column name in the microdata
before use.

**Anti-patterns**:
- Fitting any ML model on survey microdata without `weights=` / `case.weights=`
  / `sample_weight=` argument → population-level bias (P0)
- Normalising weights (`weights / sum(weights)`) changes the lambda scale in
  `cv.glmnet` — the CV-selected `lambda.min` is not comparable across model
  runs with different weight normalisations; prefer raw probability weights
  throughout a pipeline

---

## 2b. Missing Data in ML Pipelines

**Why it matters for GPID**: In poverty surveys, item non-response on
consumption/income is almost never MCAR — poorer households have
systematically higher non-response. Mean/median single imputation silently
pulls imputed values toward the observed (non-poor) mean, underestimating
poverty incidence.

**Step 1 — document missingness pattern** before any modelling:

```r
# R
library(naniar)
vis_miss(df)              # visual missingness map
miss_var_summary(df)      # % missing per variable
```

```python
import missingno as msno
msno.matrix(df)
print(df.isnull().mean().sort_values(ascending=False))
```

**Step 2 — choose strategy based on mechanism**:

| Mechanism | Strategy |
|-----------|----------|
| MCAR (document assumption) | Listwise deletion acceptable — document explicitly |
| MAR | Single imputation per CV fold — use m ≥5 with Rubin's rules for inference (see below) |
| MNAR | Flag; requires sensitivity analysis |

**Single imputation per CV fold (R)** (`m=1` is sufficient for ML prediction;
use `m ≥5` with Rubin's rules pooling for econometric inference):

```r
# mice-based imputation fitted only on train fold — prevents leakage
library(mice)
# m=1: single imputation — sufficient for ML prediction
train_imputed  <- mice(train_df, m = 1, method = "pmm", seed = 42)
train_complete <- complete(train_imputed)
# Apply the FITTED mice object to the test fold (prevents leakage)
# Option A: mice.reuse() (mice >= 3.16)
test_imputed  <- mice.reuse(train_imputed, test_df, seed = 42)
test_complete <- complete(test_imputed)
# Option B: tidymodels — step_impute_bag() inside a recipe;
# prep() fits on train fold, bake() applies fitted imputer to test fold
```

**NA indicator features** (add `is.na(x)` as a predictor):

```r
df$x_missing <- as.integer(is.na(df$x))
df$x[is.na(df$x)] <- median(df$x, na.rm = TRUE)  # median fill for the value
```

**Anti-patterns**:
- `drop_na(df)` / `na.omit(df)` on the full dataset before train/test split
  without documenting MCAR assumption
- `SimpleImputer().fit(X)` on full data (data leakage — see Check 1 in cr-ml-methodology.agent.md)
- Single mean/median imputation on poverty-related variables
- Imputing the outcome variable `y`

---

## 3. Tree-Based Methods

> **GPID cross-cutting requirements** (survey weights and missing data) apply
> to all ML methods — see Sections 2a and 2b before implementing any estimator.

**When to use**: Non-linear relationships, interactions, heterogeneous
treatment effects, robust prediction. Not for causal inference directly.

**Key patterns**:

```r
# R — random forest (ranger, faster than randomForest)
library(ranger)
set.seed(42)
rf <- ranger(y ~ ., data = train_df, num.trees = 500,
             importance = "permutation", seed = 42)

# Gradient boosting — xgboost
library(xgboost)
set.seed(42)
dtrain <- xgb.DMatrix(data = x_train, label = y_train)
params  <- list(eta = 0.1, max_depth = 6, subsample = 0.8)
cv_res  <- xgb.cv(params, dtrain, nrounds = 500, nfold = 5,
                  early_stopping_rounds = 20, seed = 42)

# Causal forest — heterogeneous treatment effects
library(grf)
set.seed(42)
cf <- causal_forest(X, Y, W, seed = 42)
tau_hat <- predict(cf)$predictions
```

```python
# Python
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import xgboost as xgb
import numpy as np

rng = np.random.default_rng(42)
rf = RandomForestRegressor(n_estimators=500, random_state=42)
rf.fit(X_train, y_train)

xgb_model = xgb.XGBRegressor(n_estimators=500, learning_rate=0.1,
                               random_state=42)
xgb_model.fit(X_train, y_train, eval_set=[(X_val, y_val)],
              early_stopping_rounds=20, verbose=False)
```

**Interpretation**:
- Permutation importance and SHAP values explain feature contributions but
  do NOT establish causality
- Partial dependence plots show marginal effect of one feature averaging over
  others — still predictive, not causal
- For causal HTE: use `grf::causal_forest` (honest estimation)

**Honest estimation**: Splits the sample for tree structure (training) and
leaf estimates (estimation) to avoid overfitting. Required for valid inference
on treatment effects.

**Anti-patterns**:
- Reporting tree-based importance as causal effect size
- Using standard random forest for HTE (not honest — biased)
- Not setting random seeds (results are non-reproducible)
- Using in-sample fit to select between forest models

**References**: Breiman (2001); Friedman (2001, GBM); Athey, Tibshirani, Wager
(2019, AoS); Lundberg & Lee (2017, SHAP).

---

## 4. Cross-Validation Done Right

**When to use**: Any ML model selection or hyperparameter tuning.

**The core rule**: Never let information from the validation fold influence
the model trained on the training folds. This includes preprocessing.

**i.i.d. data — standard k-fold**:

```r
# R — caret or tidymodels
library(tidymodels)
set.seed(42)
folds <- vfold_cv(train_df, v = 10)
```

**Panel / clustered data — leave-one-group-out CV**:

```r
# R — manual leave-one-group-out
groups <- unique(df$firm_id)
preds  <- numeric(nrow(df))
for (g in groups) {
  train_idx <- df$firm_id != g
  fit <- lm(y ~ x, data = df[train_idx, ])
  preds[!train_idx] <- predict(fit, df[!train_idx, ])
}
```

```python
# Python — GroupKFold
from sklearn.model_selection import GroupKFold
gkf = GroupKFold(n_splits=10)
for train_idx, val_idx in gkf.split(X, y, groups=firm_ids):
    ...
```

**Time-series data — rolling origin / expanding window**:

```r
# R — rsample
library(rsample)
set.seed(42)
ts_splits <- rolling_origin(df, initial = 100, assess = 20, cumulative = TRUE)
```

**Stratified CV** (by treatment status, rare outcome):

```r
set.seed(42)
folds <- vfold_cv(train_df, v = 10, strata = treatment)
```

**Class imbalance and rare events** (common in GPID ML tasks: program
take-up, firm bankruptcy, poverty targeting):

- With a 2–5% positive rate, a classifier predicting "never positive" achieves
  95–98% accuracy — accuracy is uninformative.
- Default to **precision-recall AUC** as primary metric; supplement with
  **AUROC** as a secondary check. At prevalence below 5%, AUROC remains high
  even for near-useless classifiers — PR-AUC evaluates performance at the
  operating region relevant for targeting (Davis & Goadrich 2006).
- Use class-weighted loss:

```r
# cv.glmnet: pass weights inversely proportional to class frequency
pos_rate   <- mean(df$y)
class_wts  <- ifelse(df$y == 1, 1 / pos_rate, 1 / (1 - pos_rate))
cv_fit     <- cv.glmnet(x, df$y, alpha = 1,
                        family = "binomial",
                        weights = class_wts)
```

```python
# sklearn: class_weight='balanced' adjusts loss automatically
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegressionCV
rf  = RandomForestClassifier(class_weight='balanced', random_state=42)
lr  = LogisticRegressionCV(class_weight='balanced', cv=5, random_state=42)
```

- SMOTE oversampling: only apply **inside** the CV fold training set —
  never before the split (inflates OOS performance — see Check 1 in cr-ml-methodology.agent.md).

**Why naive k-fold fails with panel data**: If observations from the same
unit appear in both training and validation folds, the model leaks
unit-specific information — CV error is optimistically biased.

**Anti-patterns**:
- Using standard k-fold on panel data with unit fixed effects
- Fitting preprocessing (scalers, PCA) on the full dataset before CV
- Using CV error from one model as the final reported performance (need a
  separate holdout)
- Setting seed once globally and not resetting before each CV call

**References**: Arlot & Celisse (2010); Bergmeir & Benítez (2012, panel CV).

---

## 5. Out-of-Sample Assessment

**When to use**: Final evaluation of any predictive model on held-out data.

**Key patterns**:

```r
# R
preds <- predict(final_model, newdata = test_df)
rmse  <- sqrt(mean((test_df$y - preds)^2))
mae   <- mean(abs(test_df$y - preds))
r2_oos <- 1 - sum((test_df$y - preds)^2) / sum((test_df$y - mean(train_df$y))^2)

# Diebold-Mariano test for comparing two forecasts
library(forecast)
dm.test(e1 = residuals_model1, e2 = residuals_model2, h = 1)
```

```python
from sklearn.metrics import mean_squared_error, mean_absolute_error, r2_score
import numpy as np

rmse = np.sqrt(mean_squared_error(y_test, preds))
mae  = mean_absolute_error(y_test, preds)
r2   = r2_score(y_test, preds)
```

**R² out-of-sample**: Denominator uses training mean, not test mean.
A negative OOS R² means the model is worse than the unconditional mean.

**Test-set contamination**: The test set must never be used for any decision
(feature selection, hyperparameter tuning, normalization parameter estimation)
before final evaluation.

**Anti-patterns**:
- Using validation error as final reported performance (need a third split)
- Selecting models based on test-set performance (test-set contamination)
- Reporting only in-sample R²
- Using the same test set for multiple model comparisons without correction

**References**: Diebold & Mariano (1995); Arlot & Celisse (2010).

---

## 6. Post-Selection Inference: Debiased / Double ML

**When to use**: Estimating the causal effect of a treatment D on outcome Y
when X is high-dimensional (p > n, or many controls). Naive LASSO then OLS
on selected variables gives invalid inference due to selection bias.

**Double/Debiased ML (DML) — Chernozhukov et al. (2018)**:

Cross-fitting procedure for the partially linear model Y = θD + g(X) + ε:

```r
# R — DoubleML package
library(DoubleML)
library(mlr3)
library(mlr3learners)

set.seed(42)
data_dml <- DoubleMLData$new(df, y_col = "y", d_cols = "d",
                              x_cols = setdiff(names(df), c("y", "d")))

# Choose learners for g(X) and m(X)
learner_g <- lrn("regr.cv_glmnet")
learner_m <- lrn("regr.cv_glmnet")

dml_plr <- DoubleMLPLR$new(data_dml, ml_g = learner_g, ml_m = learner_m,
                            n_folds = 5)
dml_plr$fit()
dml_plr$summary()
```

```python
from doubleml import DoubleMLPLR, DoubleMLData
from sklearn.linear_model import LassoCV
from sklearn.base import clone
import numpy as np

np.random.seed(42)
dml_data = DoubleMLData(df, y_col='y', d_cols='d',
                         x_cols=[c for c in df.columns if c not in ['y','d']])
learner = LassoCV()
dml_plr = DoubleMLPLR(dml_data, ml_l=clone(learner), ml_m=clone(learner),
                       n_folds=5)
dml_plr.fit()
print(dml_plr.summary)
```

**Neyman orthogonality**: DML uses moment conditions that are locally
insensitive to the nuisance parameter estimates — this is what makes
cross-fitting give √n-consistent, asymptotically normal θ̂ estimates even
when the ML estimators converge at slower rates.

**Cross-fitting**: Split data into K folds. For each fold k, estimate
nuisance functions (g, m) on the other K-1 folds, then compute residuals
on fold k. This avoids overfitting bias in the Neyman orthogonal score.

**Anti-patterns**:
- Running OLS on LASSO-selected variables without double selection
- Not using cross-fitting (fitting nuisance functions on the full sample)
- Using DML for non-partially-linear models without adapting the moment
  condition

**References**: Chernozhukov et al. (2018, Econometrica); Belloni,
Chernozhukov, Hansen (2014, ReStud).

---

## 7. Variable Importance and Economic Interpretation

**When to use**: Understanding which features drive predictions, connecting
ML results to economic theory.

**Key patterns**:

```r
# R — permutation importance (ranger)
library(ranger)
set.seed(42)
rf <- ranger(y ~ ., data = df, importance = "permutation", seed = 42)
importance(rf)           # named vector

# SHAP values — shapviz / kernelshap
library(shapviz)
shap <- shapviz(rf, X_pred = as.matrix(df[, -1]))
sv_importance(shap)
sv_dependence(shap, v = "x1")
```

```python
import shap
explainer = shap.TreeExplainer(xgb_model)
shap_values = explainer.shap_values(X_test)
shap.summary_plot(shap_values, X_test)
shap.dependence_plot("x1", shap_values, X_test)
```

**Economic interpretation rules**:
- Importance ranks variables by predictive contribution — NOT causal effect
- SHAP shows the direction of the predictive relationship, not causality
- Connect importance findings to theory: "Education is the top predictor,
  consistent with Mincer (1974), but this does not imply a causal return"
- For causal statements, pair with an identification strategy

**Anti-patterns**:
- "Feature X has high importance → X causes Y"
- Reporting Gini impurity importance (biased toward high-cardinality variables
  — always use permutation importance)
- Interpreting SHAP values as marginal effects or treatment effects

**References**: Strobl et al. (2007, permutation importance); Lundberg &
Lee (2017, SHAP); Shapley (1953).

---

## 8. Dimension Reduction and Feature Selection

**When to use**: p >> n; many correlated predictors; latent factor structure.

**Key patterns**:

```r
# R — PCA
pca <- prcomp(x_matrix, center = TRUE, scale. = TRUE)
summary(pca)                    # variance explained
loadings <- pca$rotation[, 1:5] # first 5 PCs

# Factor analysis
fa <- factanal(x_matrix, factors = 3, rotation = "varimax")

# LASSO for feature selection (hdm rigorous LASSO)
library(hdm)
rl <- rlasso(y ~ ., data = df)
selected <- names(which(coef(rl)[-1] != 0))
```

```python
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectFromModel
from sklearn.linear_model import LassoCV

# PCA — full SVD (n_components as float) is deterministic; random_state unused
pca = PCA(n_components=0.95)   # retain 95% variance; random_state not needed
X_pca = pca.fit_transform(X_train)             # fit only on train

# For large p: use randomized SVD (requires seeding)
# pca = PCA(n_components=50, svd_solver='randomized', random_state=42)

# LASSO selection
selector = SelectFromModel(LassoCV(cv=5, random_state=42))
selector.fit(X_train, y_train)
X_selected = selector.transform(X_train)
```

**Economic interpretation**: PCA components are linear combinations of
variables — label them using loadings only if the pattern matches a known
economic concept. Arbitrary labeling ("Factor 1 = Human Capital") without
grounding in the loadings is a P2 methodological concern.

**Anti-patterns**:
- Fitting PCA on the full dataset before train/test split (data leakage)
- Discarding PCs based on eigenvalue < 1 (Kaiser rule is arbitrary — use
  scree plot + domain knowledge)
- Interpreting PCA components as structural factors without theory

---

## 9. Reproducibility Requirements for ML

**When to use**: All ML workflows. Reproducibility is P0 in this framework.

**Seed checklist** (every random component needs an explicit seed):

| Component | R | Python |
|-----------|---|--------|
| Train/test split | `set.seed(42)` before split | `random_state=42` in `train_test_split` |
| CV folds | `set.seed(42)` before fold creation | `random_state=42` in `KFold`/`StratifiedKFold` |
| Random forest | `set.seed(42)` + `seed=42` in `ranger()` | `random_state=42` in `RandomForestRegressor` |
| XGBoost | `set.seed(42)` + `seed=42` in `xgb.cv` | `random_state=42` in `XGBRegressor` |
| Stochastic GD | N/A | `random_state=42` + `np.random.seed(42)` |
| Bootstrapping | `set.seed(42)` before each call | `rng = np.random.default_rng(42)` |
| PyTorch (CPU) | N/A | `torch.manual_seed(42)` |
| PyTorch (GPU) | N/A | `torch.manual_seed(42)` + `torch.cuda.manual_seed_all(42)` + `torch.backends.cudnn.deterministic = True` |
| TensorFlow / Keras | N/A | `tf.random.set_seed(42)` (TF2) or `keras.utils.set_random_seed(42)` (Keras 3) + env var `TF_DETERMINISTIC_OPS=1` for GPU determinism |

**Version pinning**: ML library versions must be locked:
- R: `renv::snapshot()` after installing glmnet, ranger, xgboost, grf, hdm
- Python: `uv lock` (generates `uv.lock` — preferred); for requirements.txt
  compatibility: `uv export --format requirements-txt > requirements.txt`

**Hardware reproducibility**: GPU computations (neural networks, some XGBoost
configurations) may not be perfectly reproducible across machines even with
seeds. Document this explicitly if applicable.

**Anti-patterns**:
- `set.seed(as.numeric(Sys.time()))` — non-reproducible
- Setting seed once globally without resetting before each stochastic call
- Not pinning library versions (`glmnet 4.1` vs `glmnet 4.0` give different
  CV results)

---

## 10. Anti-Patterns Catalog

| Anti-Pattern | Why it fails | Correct approach |
|---|---|---|
| ML R² as evidence for theory | Predictive accuracy ≠ causal validity | Use identification strategy for causal claims |
| Penalized coefficients interpreted as OLS | Regularization biases coefficients toward zero | Post-LASSO OLS or `hdm::rlasso` for inference |
| Naive k-fold on panel data | Unit-level leakage inflates CV accuracy | GroupKFold / leave-one-group-out |
| Preprocessing on full data before CV | Information leakage — test performance is optimistic | Fit preprocessor inside each fold |
| Unreported hyperparameter search | Specification searching — P0 if main result depends on tuned model | Log all trials; use nested CV |
| Single test-set used for model selection | Test-set contamination | Use separate validation and test sets |
| Gini importance for variable ranking | Biased toward high-cardinality variables | Use permutation importance or SHAP |
| Unseeded random operations | Non-reproducible results — P0 | Explicit numeric seeds everywhere |
| Causal claims from predictive model | ML optimization ≠ causal identification | Pair with IV/RDD/DiD or double ML |
| DML without cross-fitting | Overfitting bias in nuisance estimates | Always use K-fold cross-fitting in DML |
| ML on survey data without weights | Population-level silent bias — P0 | Pass `weights=`/`case.weights=`/`sample_weight=` to every estimator |
| Listwise deletion without MCAR documentation | Poverty incidence underestimated if non-response is MNAR/MAR | Document mechanism; use fold-internal imputation for MAR |
| Accuracy reported on rare outcome | Trivially gamed — P1 | Use AUROC or precision-recall AUC when prevalence < 10% |
