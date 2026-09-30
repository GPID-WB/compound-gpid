# Econometric Causal Machine Learning

<!-- Created 2026-09-03. -->

This reference covers ML used inside an identified causal or structural
procedure. The central distinction is that ML estimates flexible nuisance
functions or treatment heterogeneity, while the econometric design supplies the
estimand and identification assumptions. Predictive success alone is not a
causal result.

## 1. Start with the estimand and design

Before choosing a learner, state:

- treatment $D$, outcome $Y$, covariates $X$, units, timing, and clusters;
- the estimand: ATE, ATT, a partially linear coefficient, a policy value,
  heterogeneous effect, structural parameter, or a first-stage component;
- the identification strategy and the variation that identifies the target;
- treatment assignment, unconfoundedness or instrument assumptions, overlap,
  interference, and treatment/outcome timing;
- target population, weights, missingness, and dependence;
- how uncertainty and nuisance-function estimation will be handled.

A model that predicts $Y$ well can still omit a confounder, use a post-treatment
variable, violate overlap, or target the wrong population. A model with lower
predictive error can be worse for the causal estimand if it estimates the wrong
nuisance component or amplifies design violations.

## 2. Partially linear model

A common starting point is

$$
Y = \theta_0 D + g_0(X) + \varepsilon,
\qquad
D = m_0(X) + v,
$$

where $\theta_0$ is the target effect, $g_0(X)$ is the structural baseline,
and $m_0(X)=E[D\mid X]$. The directly learned outcome nuisance is instead

$$
\ell_0(X) = E[Y\mid X] = \theta_0 m_0(X) + g_0(X).
$$

The residual-on-residual score uses the learnable nuisance $\ell_0$, not the
structural baseline $g_0$ directly:

$$
\psi(W;\theta,\eta)
= (D-m(X))\{Y-\ell(X)-\theta(D-m(X))\},
$$

with nuisance collection $\eta=(\ell,m)$. The exact score changes with the
estimand, treatment type, outcome, instruments, censoring, or structural model.
Do not use a partially linear recipe simply because a package accepts the data.

## 3. Double/debiased machine learning

Double/debiased machine learning (DML) uses ML learners for nuisance functions
and an orthogonal score for the target parameter. In the partially linear case,
fit estimates of $\ell(X)$ and $m(X)$ on training observations, predict them on
held-out observations, form residuals, and estimate $\theta$ from the pooled
held-out scores.

The two crucial ideas are:

- **Neyman orthogonality:** the score's first-order sensitivity to small nuisance
  estimation errors is zero at the truth, reducing the impact of regularization
  bias when nuisance rates satisfy the required conditions.
- **Cross-fitting:** partition observations into folds; estimate nuisance
  functions without fold $k$, predict them on fold $k$, and rotate through all
  folds. This reduces overfitting and allows the final target estimator to use
  cross-fitted residuals.

Cross-fitting is a bias-control and efficiency device, not a substitute for
identification. It does not repair a bad instrument, a post-treatment control,
poor overlap, invalid moments, wrong target population, or dependence ignored by
the folds.

## 4. Fold construction for causal ML

Use folds that match the independent unit and timing:

| Data structure | Fold rule |
|---|---|
| iid cross-section | Random K-fold with a recorded seed |
| Clustered or panel | Keep each cluster/unit in one fold |
| Time-dependent treatment/outcome | Respect time order and prediction horizon |
| Rare treatment or outcome | Consider stratification only after unit/time separation |
| Survey sample | Define target population and weight strategy before folds |
| Multiple treatment arms | Preserve valid treatment support in each fold |

The nuisance learners must not see the held-out fold through preprocessing,
feature selection, imputation, target encoding, group summaries, or outcome
revisions. The fold assignment should be stored with the results. Repeating
cross-fitting over prespecified splits can assess sensitivity, but choosing the
most favorable split after inspection is specification searching.

## 5. Double selection and DML are related but distinct

Double selection targets a low-dimensional coefficient after selecting controls
predicting both the outcome and treatment. DML estimates nuisance functions and
uses an orthogonal score, often with cross-fitting. Neither is a universal
replacement for a carefully defined identification strategy.

Use double selection when the economic model and target regression support its
assumptions. Use DML when the score, nuisance functions, rates, overlap, and
sample structure support the procedure. Explain why a learner is used for each
nuisance function; do not select a learner only because it wins a generic
prediction contest.

## 6. Heterogeneous treatment effects

For heterogeneous effects, distinguish:

- a descriptive partition of conditional associations;
- a conditional average treatment effect (CATE);
- a policy value or treatment rule;
- a structural response function.

Honest causal forests or generalized random forests can estimate heterogeneity
when treatment assignment, overlap, nuisance adjustment, honesty, and inference
are appropriate. Honesty separates data used to discover partitions from data
used to estimate effects in leaves. An ordinary random forest with treatment as
a feature is not a causal forest.

Before interpreting CATE patterns, check:

- treatment support and overlap in the relevant subgroup;
- effective sample size and number of treated/control units;
- cluster or panel dependence;
- pre-treatment status of all covariates;
- whether subgroup discovery and effect estimation used independent information;
- calibration or policy value under held-out observations;
- multiplicity and instability across folds or seeds.

A statistically significant average effect does not guarantee useful treatment
heterogeneity, and a heterogeneous prediction pattern does not establish a
heterogeneous causal effect.

## 7. Instruments and structural models

ML can estimate high-dimensional first stages, control functions, or nuisance
parts of an IV or structural model. It cannot create instrument relevance,
exclusion, monotonicity, rank conditions, or a valid structural restriction.
State the moment conditions and ensure that the learner's inputs and outputs
match the derived model.

When using ML in IV, check first-stage relevance, effective support, weak-
identification sensitivity, cross-fitting design, treatment effect target, and
standard errors. When using ML inside a structural estimator, verify that the
simulation, integration, optimization, and nuisance predictions preserve the
model's parameter mapping.

## 8. Inference and uncertainty

Report the source of uncertainty:

- sampling uncertainty in the target estimator;
- nuisance estimation and fold variation;
- clustering or serial dependence;
- treatment-effect heterogeneity;
- tuning and learner selection;
- weights and target-population transport;
- finite-sample or weak-overlap sensitivity.

Use the variance estimator justified by the score and dependence structure. A
small nuisance prediction error does not guarantee a precise or unbiased causal
estimate. Conversely, a nuisance learner with mediocre prediction can still be
useful if the orthogonal score and identification conditions are valid.

Do not report a regularized coefficient, SHAP value, feature importance, or
out-of-sample $R^2$ as the causal effect. If post-selection inference is not
implemented, say so rather than relabeling predictive uncertainty as causal
uncertainty.

## 9. Package boundaries

- `DoubleML` and equivalent libraries implement selected DML estimators; verify
  the score, fold, learner, weight, cluster, and variance interfaces against the
  package version.
- `grf` implements causal and generalized random forests in R; verify honesty,
  treatment coding, sample weights, clusters, and inference options.
- Python `doubleml` and established causal-ML libraries provide analogous
  estimators; keep the same estimand and fold checks at the API boundary.
- Generic `scikit-learn`, `tidymodels`, XGBoost, or LightGBM learners provide
  prediction functions but do not supply causal identification.

Package output is evidence about the specified procedure, not a proof that the
procedure's assumptions hold for the study.

## 10. Causal-ML reporting checklist

Record:

- estimand, potential-outcome or structural notation, and target population;
- identification assumptions and supporting diagnostics;
- nuisance functions, learners, loss, tuning, and candidate search;
- cross-fitting folds, independent unit, timing, and seed;
- overlap, treatment support, missingness, and weights;
- orthogonal score or forest honesty construction;
- variance, clustering, finite-sample, and sensitivity procedures;
- held-out nuisance predictions and policy/HTE evaluation where relevant;
- negative evidence: conditions DML or causal forests do not repair;
- the boundary between causal claims, predictive explanations, and hypotheses.

## References

- Chernozhukov et al. (2018), "Double/Debiased Machine Learning for Treatment
  and Structural Parameters," *The Econometrics Journal*, 21(1), C1-C68. DOI:
  https://doi.org/10.3982/ECTA12674.
- Belloni, Chernozhukov, and Hansen (2014), "Inference on Treatment Effects
  after Selection among High-Dimensional Controls," *Review of Economic
  Studies*, 81(2), 608-650. DOI: https://doi.org/10.1093/restud/rdt044.
- Athey, Tibshirani, and Wager (2019), "Generalized Random Forests," *The
  Annals of Statistics*, 47(2), 1148-1178. DOI:
  https://doi.org/10.1214/17-AOS1709.
- Athey and Imbens (2019), "Machine Learning Methods That Economists Should
  Know About," *Annual Review of Economics*, 11, 685-725. DOI:
  https://doi.org/10.1146/annurev-economics-080217-053433.
- Chernozhukov et al. (2022), "Automatic Debiased Machine Learning of Causal
  and Structural Effects," *Econometrica*, 90(3), 967-1028. DOI:
  https://doi.org/10.3982/ECTA18594.
- DoubleML documentation and API reference: https://docs.doubleml.org/
- grf documentation and API reference: https://grf-labs.github.io/grf/
