# Survey, Panel, and Target-Population ML

<!-- Created 2026-09-03. -->

This reference qualifies ML for unequal-probability samples, complex surveys,
and dependent observations. The central question is not simply whether a
library accepts a `sample_weight` argument. It is which population risk or
estimand is being targeted, which dependence features affect fitting and
assessment, and which design information is needed for uncertainty.

## 1. Define the target population

Distinguish three targets:

- **Sample prediction:** performance for the observed sample-generating process;
- **finite-population prediction:** weighted performance over a defined finite
  population represented by the sample;
- **superpopulation prediction:** expected performance under a model for future
  units or populations.

Write the target population, inclusion mechanism, observation unit, prediction
unit, and time horizon. A household survey may contain people nested in
households, households in PSUs, strata, regions, and waves. The independent unit
for splitting and the unit for a population estimate may differ.

A model can be accurate for sampled observations but poor for the target
population if high-weight units, small domains, or systematically nonresponding
units are misrepresented. An unweighted model may be appropriate for a
conditional sample target, but it should not be presented as a population
predictor without justification.

## 2. What probability weights do

Let $\pi_i$ be the inclusion probability and $w_i \propto 1/\pi_i$ the base
weight. For a weighted empirical loss, a common objective is

$$
\widehat R_w(f) =
\frac{\sum_{i\in A} w_i L(y_i, f(x_i))}
{\sum_{i\in A} w_i}.
$$

Weights can also include nonresponse adjustment, calibration, trimming, or
post-stratification. Their meaning must be documented. Weighting the loss changes
the population emphasis; it does not automatically make covariates, outcomes,
missingness, or future observations available at prediction time.

Raw versus normalized weights can affect software-specific penalty scales,
regularization paths, sampling behavior, and reported loss. Record the exact
weight vector or transformation, the normalization convention, and whether
weights are used in fitting, tuning, scoring, or all three. Do not compare
penalties across runs with different conventions without checking the objective.

## 3. What weights do not solve

An observation-weight argument generally does not by itself implement:

- stratified sample selection or finite-population corrections;
- cluster or PSU dependence;
- replicate weights or design-based variance;
- nonresponse or coverage correction beyond the supplied adjustment;
- calibration constraints or domain estimation;
- transport to an unrepresented population;
- dependence across panel waves or repeated units.

In Python, `sample_weight` in an estimator or scorer changes what that interface
can weight; it is not a complete complex-survey design. In R, `case_weights` or an
engine's weight argument has the same limitation unless the estimator explicitly
implements the required design and variance. Survey inference may require a
survey-specific estimator, replicate-weight procedure, bootstrap, linearization,
or a design-aware variance calculation outside the ML learner.

If a package does not support the needed weight, cluster, or replicate interface,
state the limitation and choose a defensible alternative. Never silently drop
weights or claim design-based inference from an unweighted learner.

## 4. Panel and clustered prediction

Decide whether the model should generalize to:

- new observations within known households, firms, or people;
- new households, firms, people, PSUs, or regions;
- a new survey wave or time period;
- the target population represented by the weighted sample.

For new-unit prediction, split by the unit: all rows from a unit remain in one
fold. A random row split leaks unit-specific patterns. For future-wave
prediction, split by time and ensure that revised weights, outcomes, and feature
aggregates were available at the forecast date. If both units and time matter,
use blocked group-time folds.

Report metrics at both row and independent-unit level when the decision concerns
units. Large units can dominate unweighted row metrics; high-weight units can
dominate weighted metrics. Show the number and weight share of groups in each
fold, and check whether small domains disappear from assessment sets.

## 5. Survey-aware workflow

1. Describe the sample design, weights, strata, clusters, waves, and target
   population.
2. Separate outcome, predictors, identifiers, design variables, and information
   unavailable at prediction time.
3. Decide whether weights define the learning target, the evaluation target, or
   both.
4. Choose a splitting unit that respects panel/cluster dependence and time.
5. Fit imputation, encoding, scaling, feature engineering, and selection inside
   analysis folds. Document whether missingness is related to welfare, treatment,
   or inclusion.
6. Tune against a prespecified weighted or unweighted loss and report the
   rationale.
7. Assess on untouched data with weighted and unweighted diagnostics when both
   are informative.
8. Use survey or cluster-aware uncertainty methods for population claims.
9. Compare against a simple weighted baseline and inspect domains, tails, and
   high-weight units.

A weighted loss can be useful even when the learner lacks design-based variance.
The output should then be described as weighted prediction with separately
qualified uncertainty, not as a complete survey estimator.

## 6. Weight and design diagnostics

Before fitting, check:

- weights are present, positive where required, and not accidentally missing;
- the weight sum and weight distribution by domain;
- extreme weights and any prespecified trimming or stabilization;
- representation of strata, PSUs, waves, and domains in each split;
- whether all observations from a cluster remain together when required;
- whether the outcome and predictors have different missingness by weight/domain;
- whether design variables are predictors, split identifiers, or restricted from
  the model for substantive reasons;
- whether population totals, calibration constraints, or replicate weights must
  be preserved outside the learner.

Do not infer that a column named `weight`, `wt`, `pw`, or `survey_weight` is
sufficiently specified. Verify its definition in the codebook and data
provenance. Conversely, do not ignore a documented weight because a generic ML
example omitted it.

## 7. Evaluation for population prediction

Use metrics that answer the population question. Weighted RMSE, MAE, log loss,
Brier score, calibration, PR-AUC, and cost-sensitive metrics may be appropriate,
but the choice depends on the decision and target. Report the denominator and
whether weights are normalized.

For a population estimate, include:

- weighted and, when useful, unweighted performance;
- a baseline using the relevant weighted mean, prevalence, or simple model;
- domain and subgroup performance with weight shares and effective sample size;
- calibration and tail behavior for poverty, targeting, or risk scores;
- sensitivity to reasonable weight handling and trimming;
- design-aware or cluster-aware uncertainty where a population claim is made.

A weighted test score is not automatically unbiased if the test split excludes
important domains, reuses tuned decisions, or fails to represent the deployment
population. An external validation wave may be more informative than a random
within-wave split.

## 8. Missingness and nonresponse

Survey missingness often reflects item nonresponse, attrition, coverage, or
welfare-related reporting. Mean imputation can alter both the predictive loss
and the population distribution. Treat imputation as a fold-specific fitted
operation and record the missingness mechanism considered (MCAR, MAR, or MNAR).

For prediction, a single fold-internal imputation may be an operational choice;
for econometric inference, multiple imputation and variance combination may be
needed. Sensitivity analysis should consider differential missingness by weight,
domain, and outcome. Do not impute the outcome merely to make an ML interface
accept the row without documenting the estimand change.

## 9. Causal or policy uses

Weights and survey design do not turn prediction into causal inference. For a
policy or treatment-effect application, also state treatment assignment,
identification, overlap, interference, timing, and an appropriate causal
estimator. DML or causal forests require folds and variance methods compatible
with clusters, panels, and target populations.

A targeting score may be evaluated by population-weighted utility, but a high
score or important feature does not prove a program effect. Keep the policy
objective, prediction target, and causal estimand distinct.

## 10. Implementation boundaries

R `tidymodels` can carry case weights through supported models and metrics, while
survey-specific packages such as `survey` or `srvyr` handle design-based
operations outside the generic learner. Python scikit-learn supports
`sample_weight` for selected estimators and scorers; custom splitters and
external survey tooling may be needed for design features.

Check each engine's documentation for whether it supports weights during:

- fitting;
- cross-validation and hyperparameter tuning;
- probability calibration;
- prediction scoring;
- bootstrap, cluster, or replicate-weight inference.

If only fitting is weighted but selection or final scoring is not, say so. A
package boundary is a methodological boundary, not a cosmetic implementation
detail.

## 11. Reporting checklist

Record:

- study, wave, sample design, target population, and observation unit;
- weight definition, normalization, trimming, and use in each pipeline stage;
- strata, clusters, panels, domains, and splitting unit;
- prediction horizon and information set;
- preprocessing, imputation, feature engineering, and leakage controls;
- weighted/unweighted metrics, baseline, calibration, and subgroup results;
- effective sample sizes, weight shares, and high-weight sensitivity;
- design-based, cluster-robust, replicate, or model-based uncertainty;
- package support limits and any unimplemented design feature;
- whether conclusions are predictive, population-descriptive, policy-targeting,
  causal, or structural.

## References

- Särndal, Swensson, and Wretman (1992), *Model Assisted Survey Sampling*,
   Springer. DOI: https://doi.org/10.1007/978-1-4612-0939-2.
- Lohr (2021), *Sampling: Design and Analysis*, 3rd ed., Chapman and Hall/CRC.
   DOI: https://doi.org/10.1201/9780429296284.
- Lumley (2010), *Complex Surveys: A Guide to Analysis Using R*, Wiley. DOI:
   https://doi.org/10.1002/9780470580066.
- Binder (1983), "On the Variances of Asymptotically Normal Estimators from
   Complex Surveys," *International Statistical Review*, 51(3), 279-292. DOI:
   https://doi.org/10.2307/1402588.
- Little (1993), "Pattern-mixture models for multivariate incomplete data,"
   *Journal of the American Statistical Association*, 88(423), 125-134. DOI:
   https://doi.org/10.1080/01621459.1993.10476326.
- Official scikit-learn sample-weight and model-selection documentation:
   https://scikit-learn.org/stable/
- R `survey` package documentation: https://r-survey.r-forge.r-project.org/survey/
