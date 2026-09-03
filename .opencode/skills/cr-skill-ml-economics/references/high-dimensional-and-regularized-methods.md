# High-Dimensional and Regularized Methods

<!-- Created 2026-09-03. -->

This reference covers prediction and inference when the number of candidate
predictors $p$ is large relative to observations $n$, including $p > n$.
The organizing ideas are regularization, sparsity or approximate sparsity,
explicit loss functions, and a strict separation between prediction and
post-selection inference.

## 1. Diagnose the high-dimensional problem

Record:

- $n$, $p$, the effective sample size, and the number of independent groups;
- the outcome, treatment, target controls, and candidate nuisance variables;
- missingness, rare categories, collinearity, and deterministic or near-zero
  variance predictors;
- whether the target is prediction, variable screening, causal inference, or
  a structural/econometric parameter;
- the sampling unit and whether weights, clusters, panels, or time ordering
  alter the effective sample size.

The phrase "high-dimensional" covers several distinct cases:

| Case | Main problem | Typical response |
|---|---|---|
| $p$ close to $n$ | OLS variance and model-selection instability | Regularization and validation |
| $p > n$ | OLS is not identified uniquely | Penalized or dimension-reduced prediction |
| Many correlated predictors | Coefficients and selections are unstable | Group/domain features, elastic net, stability checks |
| Many controls for a target effect | Selection can omit outcome or treatment predictors | Double selection or DML |
| Approximate sparsity | Small effects remain outside a sparse approximation | Tune complexity; assess omitted approximation error |

## 2. OLS as a benchmark, not a universal default

For a linear prediction model $Y = X\beta + \varepsilon$, OLS minimizes
squared error when the design has sufficient rank. It is an important baseline
because it is transparent, often well-calibrated under correct specification,
and gives a reference for how regularization changes prediction.

OLS is not automatically the correct inferential benchmark. With many candidate
controls, a data-dependent selection step changes the distribution of the
reported coefficient. With $p > n$, OLS cannot select a unique coefficient
vector without additional restrictions. If the target is causal, identification,
not predictive fit, determines whether OLS is appropriate.

## 3. Ridge, LASSO, and elastic net

For centered and scaled predictors, ridge solves

$$
\widehat\beta^{ridge}(\lambda)
= \arg\min_\beta
\left\{
\frac{1}{2n}\|Y-X\beta\|_2^2 + \lambda\|\beta\|_2^2
\right\}.
$$

Ridge shrinks correlated coefficients together and generally keeps all
predictors. It is often a strong prediction method when signal is dense or
collinearity is substantial.

LASSO solves

$$
\widehat\beta^{lasso}(\lambda)
= \arg\min_\beta
\left\{
\frac{1}{2n}\|Y-X\beta\|_2^2 + \lambda\|\beta\|_1
\right\}.
$$

The $L_1$ penalty can set coefficients exactly to zero, providing a sparse
representation. Selection is useful for prediction or as one component of an
inference procedure, but a zero coefficient does not prove that the economic
variable is irrelevant. Selection depends on scaling, correlations, the loss,
penalty, sample, and tuning design.

Elastic net combines both penalties:

$$
\widehat\beta^{EN}(\lambda,\alpha)
= \arg\min_\beta
\left\{
\frac{1}{2n}\|Y-X\beta\|_2^2
+ \lambda\left[\alpha\|\beta\|_1
+ (1-\alpha)\|\beta\|_2^2\right]
\right\},
\qquad 0\leq\alpha\leq 1.
$$

The exact scaling convention differs across software. Document the objective,
standardization, observation weights, and how the intercept is handled.

For generalized outcomes, replace squared error with the appropriate negative
log-likelihood or task loss. The penalty changes the fitted function; it does
not by itself create a valid causal estimand.

## 4. Standardization and penalty scale

Standardization is part of the specification. Without it, a common penalty
shrinks variables measured in large units differently from variables measured
in small units. Fit centering and scaling only on the analysis data within each
resampling fold, then apply those fitted transformations to assessment data.

Do not silently mix:

- raw and standardized predictors;
- different weight normalizations;
- different outcome scaling;
- penalty values from different software conventions;
- a full-data transform with a fold-specific model.

When observation weights represent a target-population loss, document whether
the library uses raw weights, normalized weights, or weights only in fitting and
not in scoring. A case-weight interface is not a complete complex-survey design.

## 5. Sparsity and approximate sparsity

A sparse approximation assumes that a relatively small support $S$ captures the
important components of the regression function. Approximate sparsity allows a
remainder:

$$
Y = X\beta_0 + r(X) + \varepsilon,
$$

where $\beta_0$ has a small effective support and $r(X)$ is controlled relative
to the target rate. The practical implications are:

- sparsity is an assumption about approximation and signal, not a fact implied
  by LASSO selecting few variables;
- the relevant sparsity level depends on the target, loss, sample structure,
  and nuisance function;
- weak signals and correlated features can make support recovery impossible
  even when prediction is good;
- a selected support should be examined for stability and theory, not counted as
  a definitive list of causes.

Compatibility or restricted-eigenvalue-type conditions support theoretical rates
for some high-dimensional estimators. They are not proven by a high test score.
Check support overlap, design collinearity, signal strength, and effective sample
size before invoking sparse asymptotics.

## 6. Choosing the penalty and model complexity

Use a documented tuning rule. Cross-validation is common for prediction; a
one-standard-error rule can favor a simpler model when the loss difference is
small. The minimum-CV-error rule may improve predictive performance but can
select a more complex and less stable model. Neither rule is universally best.

For high-dimensional inference, theoretically calibrated penalty choices or
specialized rigorous-LASSO procedures may be preferable to a prediction-only
CV rule. Do not mix a prediction-tuned LASSO with inferential claims without
explaining the resulting assumptions and correction.

Record:

- candidate penalty grid or search range;
- standardization and weight conventions;
- fold construction and seed;
- primary loss and tie-breaking rule;
- number of candidates and whether model class choices were also searched;
- selected penalty, support size, and stability across resamples.

A large unreported search over penalties, transformations, outcomes, or feature
sets is specification searching. Report the search, not only the winning row.

## 7. Post-LASSO and selection for prediction

A post-LASSO refit typically uses LASSO to select variables and then fits an
unpenalized model on the selected support. It can reduce shrinkage bias for
prediction or descriptive fits, but ordinary post-selection standard errors are
not automatically valid. The selected variables were chosen using the outcome,
so a naive second-stage p-value ignores selection uncertainty.

Use post-LASSO OLS only with a clearly stated purpose and caveat. Do not label
its coefficients causal merely because the second-stage model is unpenalized.
For a causal target, use a method designed for the selection problem, such as
double selection or DML when its assumptions fit the design.

## 8. Double selection for a target treatment effect

Suppose the target is the coefficient on treatment $D$ in a partially linear
model:

$$
Y = \theta D + g(X) + \varepsilon,
$$

where $X$ is a high-dimensional control vector. Double selection runs a
selection procedure for the outcome equation $Y$ on $X$ and another for the
treatment equation $D$ on $X$. The union of selected controls is included in a
final target regression.

The intuition is to protect against controls that predict the outcome and
controls that predict treatment. The method still relies on identification,
approximation, overlap, and error conditions. It does not make an invalid
instrument valid, create random assignment, or repair a post-treatment control.

A double-selection report should state:

- the treatment, outcome, and target estimand;
- the candidate control universe and any variables forced into the model;
- the outcome and treatment selection procedures;
- penalty and fold choices;
- the final union support;
- standard-error and clustering choices;
- sensitivity to plausible control universes and tuning rules.

## 9. Debiased or desparsified LASSO

The ordinary LASSO estimator is biased toward zero because of the penalty. A
debiased (or desparsified) LASSO adds a correction based on an estimate of the
precision structure of the design. Schematically, for a target coefficient:

$$
\widetilde\beta_j
= \widehat\beta_j
+ \frac{1}{n}\widehat\Theta_j^T X^T(Y-X\widehat\beta),
$$

where $\widehat\Theta_j$ approximates the relevant inverse Gram direction.
Under sparsity, design, tail, and regularity conditions, the corrected statistic
can support asymptotic inference for selected coordinates.

The correction does not remove the need to verify:

- a defensible target parameter;
- approximate sparsity of both regression and precision components;
- design regularity and effective sample size;
- appropriate dependence and variance estimation;
- tuning and implementation details;
- whether the package's reported interval corresponds to the intended target.

Do not describe a debiased interval as automatically valid in a small, highly
correlated, clustered, or survey sample.

## 10. Selective inference and stability

If the scientific question concerns the selected support, account for the fact
that selection was data-dependent. Selective-inference methods target a
conditional or selection-adjusted statement and can be conservative or require
strong assumptions. They are different from simply reporting post-LASSO OLS
standard errors.

Use stability diagnostics even when formal selective inference is not feasible:

- repeat the analysis across prespecified resamples or seeds;
- record selection frequencies and sign changes;
- compare grouped or domain-level alternatives for correlated features;
- assess out-of-sample loss and subgroup performance;
- explain whether instability reflects weak signal, collinearity, or changing
  target populations.

Stability is evidence about the procedure, not proof that a feature is causal.

## 11. Dimension reduction and feature construction

Dimension reduction changes the predictor representation and may be useful when
predictors are strongly correlated, $p$ is very large, or a latent-factor
structure is plausible. It does not automatically preserve the target of the
original regression or create an economic structural factor.

**PCA and factor methods** construct components from predictor covariance. Fit
centering, scaling, rotations, the number of components, and any factor
selection using analysis folds only. Assess the resulting components against
held-out loss and compare with ridge, LASSO, or a domain-based feature set.

Choose the number of components using a prespecified combination of validation
performance, scree/loadings, cumulative variance, and economic theory. The
largest-variance component need not be the most predictive. Label a component
as human capital, wealth, or another economic construct only when its loadings,
measurement design, and theory support that interpretation.

**Feature selection and construction** can use domain grouping, supervised
screening, regularization, sparse PCA, or learned transformations. All outcome-
or sample-dependent choices belong inside the resampling loop. Record the
candidate feature universe, selection rule, number of alternatives, and
stability across folds. A selected feature or latent component is predictive
evidence, not a causal effect.

## 12. Method-selection map

| Research objective | Starting point | Main caution |
|---|---|---|
| Dense linear prediction | Ridge or elastic net | Shrunk coefficients are predictive parameters |
| Sparse prediction | LASSO or elastic net | Support can be unstable and loss-dependent |
| Many controls, causal target | Double selection or DML | Identification, overlap, and dependence remain central |
| Coordinate-wise high-dimensional inference | Debiased LASSO | Requires design and sparsity conditions |
| Latent correlated structure | PCA/factors plus validation | Components need not be structural factors |
| Screening candidates for theory | LASSO plus stability and domain review | Screening is not causal proof |

## 13. Reporting checklist

Before reporting a regularized result, state:

- whether the goal is prediction, selection, or inference;
- $n$, $p$, group structure, and effective sample size;
- preprocessing and standardization;
- penalty objective and tuning rule;
- candidate grid, folds, seed, and search count;
- selected support and its stability;
- baseline and held-out performance;
- whether weights define a target-population loss and what design features remain
  untreated;
- whether inference is post-LASSO, double selection, debiased LASSO, DML, or
  not attempted;
- which economic interpretation is justified and which is not.

## References

- Hastie, Tibshirani, and Friedman (2009), *The Elements of Statistical
  Learning: Data Mining, Inference, and Prediction*, 2nd ed., Springer,
  Chapters 3, 5, 7, and 18. DOI: https://doi.org/10.1007/978-0-387-84858-7.
- Tibshirani (1996), "Regression Shrinkage and Selection via the Lasso,"
  *Journal of the Royal Statistical Society: Series B*, 58(1), 267-288. DOI:
  https://doi.org/10.1111/j.2517-6161.1996.tb02080.x.
- Zou and Hastie (2005), "Regularization and Variable Selection via the Elastic
  Net," *Journal of the Royal Statistical Society: Series B*, 67(2), 301-320.
  DOI: https://doi.org/10.1111/j.1467-9868.2005.00503.x.
- Belloni, Chernozhukov, and Hansen (2014), "Inference on Treatment Effects
  after Selection among High-Dimensional Controls," *Review of Economic
  Studies*, 81(2), 608-650. DOI: https://doi.org/10.1093/restud/rdt044.
- van de Geer et al. (2014), "On Asymptotically Optimal Confidence Regions and
  Tests for High-Dimensional Models," *The Annals of Statistics*, 42(3),
  1166-1202. DOI: https://doi.org/10.1214/14-AOS1203.
- Bühlmann and van de Geer (2011), *Statistics for High-Dimensional Data:
  Methods, Theory and Applications*, Springer. DOI:
  https://doi.org/10.1007/978-3-642-20192-9.
