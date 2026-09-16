# Statistical Learning Foundations

<!-- Created 2026-09-03. -->

This reference is the conceptual starting point for ML work in economics. It
uses the vocabulary and progression of Hastie, Tibshirani, and Friedman (HTF),
*The Elements of Statistical Learning* (ESL), second edition, without
reproducing the book's prose. Read it before selecting an algorithm when the
research goal, loss, estimand, or generalization target is unclear.

## 1. Start with the target

Separate five questions that are often collapsed into "build a model":

1. **What is the goal?** Prediction, description, variable selection, causal
   estimation, heterogeneous treatment effects, or a nuisance function inside
   an econometric estimator.
2. **What is the prediction target?** For regression this may be a conditional
   mean, a conditional quantile, or an individual outcome. For classification
   it may be a conditional probability, a class label, or a ranking.
3. **What is the estimand?** A causal effect, structural parameter, treatment
   response, forecast, or population risk is not interchangeable with a fitted
   prediction function.
4. **What population and information set matter?** State the target population,
   observation unit, prediction horizon, and which variables are available when
   the prediction is made.
5. **What loss or decision rule matters?** Choose a loss function or utility
   criterion before comparing models. A metric chosen after seeing results is
   a specification decision and must be recorded.

Let $X$ denote predictors, $Y$ an outcome, and $f(X)$ a prediction. A common
regression target is the conditional mean

$$
m(x) = E[Y \mid X=x].
$$

A classification target may be the conditional class probability

$$
\eta(x) = P(Y=1 \mid X=x).
$$

Neither target is automatically a causal response. If $D$ is treatment, a
causal target usually compares potential outcomes or an identified structural
parameter, not $E[Y \mid X=x]$ alone.

## 2. Risk, loss, and generalization

For a loss function $L(Y, f(X))$, define population risk and empirical risk as

$$
R(f) = E[L(Y, f(X))], \qquad
\widehat R(f) = \frac{1}{n}\sum_{i=1}^n L(Y_i, f(X_i)).
$$

The population risk is the object that describes expected performance on new
data from the target process. The related **generalization error** is the
expected loss on observations outside the fitting sample. Training error
estimates neither generalization error nor causal validity without additional
assumptions. Out-of-sample assessment approximates risk under a specified
sampling and deployment design.

Useful losses include:

| Task | Common loss or metric | What it emphasizes |
|---|---|---|
| Continuous prediction | Squared error, RMSE | Large errors; conditional mean under squared loss |
| Continuous prediction | Absolute error, MAE | Robustness to large errors; conditional median under ideal conditions |
| Quantile prediction | Pinball loss | A specified conditional quantile |
| Binary probability prediction | Log loss, Brier score | Probabilistic accuracy and calibration |
| Binary ranking | ROC-AUC, PR-AUC | Ranking; PR-AUC is more informative for rare positives |
| Policy targeting | Cost-weighted loss, expected utility | Decision-specific consequences of errors |

Choose metrics that match the decision. For example, a poverty-targeting rule
may care about weighted false negatives and calibration at a threshold, not only
RMSE or accuracy.

## 3. The ESL model-complexity view

ESL organizes supervised learning around the tension between approximation and
estimation. The **bias-variance trade-off** is the central reminder that a more
flexible function class can reduce approximation bias but increase variance,
sensitivity to noise, and computational cost. Regularization,
constrained fitting, early stopping, aggregation, and validation are ways to
control effective complexity.

For a fitted prediction at a fixed $x$, the squared-error decomposition is a
useful diagnostic idea:

$$
E[(Y - \widehat f(x))^2]
= \operatorname{Var}(Y \mid X=x)
+ \operatorname{Bias}(\widehat f(x))^2
+ \operatorname{Var}(\widehat f(x)).
$$

The irreducible conditional variance cannot be removed by changing algorithms.
A lower training error can coexist with a higher test error when model variance
and overfitting dominate. The useful question is not whether a method is
"flexible" but whether its complexity is appropriate for the DGP, sample size,
noise level, target population, and loss.

Use the following sequence:

1. Establish an interpretable baseline, such as the training mean, linear OLS,
   logistic regression, an AR model for forecasting, or a simple weighted rule.
2. Fit a small set of theoretically motivated candidates.
3. Tune only on the training data through a pre-specified resampling design.
4. Assess the finalized candidate on untouched data.
5. Inspect errors, calibration, subgroup behavior, and stability, not only one
   aggregate score.

## 4. Estimation is not assessment

A model-fitting procedure estimates parameters or a function using an analysis
sample. An assessment procedure estimates how that procedure behaves on data
not used to choose it. Keep these roles separate:

- **Training data** estimate model parameters and preprocessing quantities.
- **Resampling data** compare hyperparameters and model classes within the
  training portion.
- **Test data** provide the final assessment after decisions are frozen.

Cross-validation is a way to reuse training data for model comparison. It is
not a license to repeatedly inspect the final test set. If the same data are
used for tuning and performance claims, use nested cross-validation or preserve
a final holdout. The split unit must follow the DGP: rows are not independent
when they share a household, firm, person, location, survey PSU, or time block.

Preprocessing is part of the estimator. Centering, scaling, imputation,
encoding, feature screening, PCA, and target encoding must be fitted within the
analysis portion of each resample. A pipeline or workflow should carry those
operations with the model.

## 5. Prediction versus economics

A high $R^2$, low RMSE, important feature, or selected variable is evidence about
a predictive procedure under a stated evaluation design. It is not evidence
that a predictor causes the outcome or that a structural mechanism is true.

For an economic interpretation, state:

- the economic object being predicted or estimated;
- the sampling and target population;
- the information set available at prediction time;
- whether a variable is a treatment, control, proxy, mediator, post-outcome
  variable, or merely a predictive feature;
- the assumptions needed for any causal or structural interpretation;
- whether the result is stable across samples, subgroups, specifications, and
  plausible split designs.

Prediction can still be economically useful. Examples include forecasting
income, ranking households for a program, imputing a nuisance function for DML,
selecting candidate controls, or finding heterogeneity to investigate with a
causal design. In each case, prediction is a component of the research design,
not a replacement for identification.

## 6. Classification and decisions

A classifier can output a score, probability, ranking, or hard label. These are
different products:

- A probability requires calibration and an appropriate loss.
- A ranking requires a ranking metric and a decision threshold chosen using only
  training or validation information.
- A hard label requires an explicit cost or utility trade-off.

Accuracy can be misleading when the positive class is rare. Compare against a
majority or prevalence baseline, report class-conditional metrics, and inspect
precision-recall behavior in the operating region that matters. Calibration
curves and Brier or log loss are useful when predicted probabilities drive
resource allocation.

## 7. Data structure and target population

The iid assumption is a modeling choice, not a default fact. Before resampling,
ask whether the intended generalization is:

- new rows from the same units;
- new units such as firms, people, or households;
- a future period;
- a new survey wave or population;
- a target population represented through unequal-probability sampling.

Use group, blocked, temporal, or survey-aware designs when they match the target.
A random row split can produce excellent scores while estimating the wrong
quantity because the same unit or near-future information appears on both sides.

For survey data, define whether the objective is sample prediction, finite-
population prediction, or superpopulation prediction. Observation weights may
alter the empirical loss, but they do not automatically solve clustering,
stratification, nonresponse, calibration, or design-based variance estimation.

## 8. Dimension and flexible methods

When $p$ is large relative to $n$, ordinary least squares may be unstable or
undefined. Regularization, screening, dimension reduction, and tree or boosting
methods can improve prediction, but each changes the estimand or interpretation.
Read the high-dimensional reference before interpreting selected variables.

Tree ensembles and neural networks can approximate nonlinearities and
interactions. They remain prediction procedures unless embedded in an identified
causal method. A bounded neural-network overview is useful for method selection,
but a deep model should not be chosen merely because the dataset is large.

## 9. Bounded neural-network method selection

Neural networks can be useful for large tabular samples with nonlinearities and
interactions, but they are not a default for high-dimensional economic data.
Choose them only after a linear/regularized and tree-based baseline, with a
clear target, loss, sample structure, and computational budget.

For tabular economic prediction, review:

- feature scaling and categorical representation inside the training pipeline;
- architecture size relative to effective sample size and signal complexity;
- weight decay, dropout, early stopping, and other regularization;
- validation or nested-CV design, including group/time separation;
- random seeds, initialization, batch order, hardware, and deterministic limits;
- calibration, subgroup/tail error, extrapolation, and sensitivity to tuning;
- predictive interpretation limits: learned weights are not causal effects.

Deep learning does not repair leakage, poor overlap, weak identification,
survey-design mismatch, or a wrong target population. This skill gives only
bounded method-selection guidance; computer vision, NLP, reinforcement
learning, and production MLOps are out of scope.

## 10. Practical decision checklist

Before recommending or fitting a model, record:

- goal and prediction/causal/structural status;
- outcome, predictors, treatment, controls, and availability timing;
- target population and observation unit;
- loss, primary metric, secondary metrics, and baseline;
- iid, group, panel, temporal, clustered, or survey dependence;
- preprocessing and feature-engineering operations;
- split unit, resampling design, tuning budget, and seed;
- final test or external validation plan;
- uncertainty, subgroup stability, calibration, and error analysis;
- economic interpretation and claims that are explicitly out of scope.

## References

- Hastie, Tibshirani, and Friedman (2009), *The Elements of Statistical
   Learning: Data Mining, Inference, and Prediction*, 2nd ed., Springer. DOI:
   https://doi.org/10.1007/978-0-387-84858-7. Canonical book site:
   https://hastie.su.domains/ElemStatLearn/
- Arlot and Celisse (2010), "A survey of cross-validation procedures for model
   selection," *Statistics Surveys*, 4, 40-79. DOI:
   https://doi.org/10.1214/09-SS054.
- Athey and Imbens (2019), "Machine Learning Methods That Economists Should
   Know About," *Annual Review of Economics*, 11, 685-725. DOI:
   https://doi.org/10.1146/annurev-economics-080217-053433.
- Davis and Goadrich (2006), "The relationship between Precision-Recall and ROC
   curves," *Proceedings of the 23rd International Conference on Machine
   Learning*, 233-240. DOI: https://doi.org/10.1145/1143844.1143874.
- Official scikit-learn model-selection guide:
   https://scikit-learn.org/stable/model_selection.html
- Official tidymodels resampling guide:
   https://www.tidymodels.org/start/resampling/
