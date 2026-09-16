# Trees, Ensembles, and Interpretation

<!-- Created 2026-09-03. -->

Tree methods are flexible prediction procedures that represent nonlinearities
and interactions without requiring them to be specified in advance. Their
usefulness in economics depends on the prediction target, sample structure,
loss, extrapolation problem, and the interpretation required. They are not
causal estimators by default.

## 1. Decision trees

A regression tree partitions predictor space into regions and predicts a
constant or simple value within each region. Classification trees partition the
space using a criterion such as impurity reduction or log loss. Tree depth,
minimum leaf size, pruning/complexity penalty, and split criterion regulate
complexity.

Trees can be useful when thresholds and interactions are substantively
plausible, but a single tree is often unstable: small changes in data can change
an early split and the entire downstream partition. Use a linear or regularized
model as a benchmark. Do not infer a structural threshold merely because a tree
placed a split there.

## 2. Bagging and random forests

Bagging averages predictions from trees fitted to bootstrap samples. Averaging
reduces variance when individual trees are noisy and not perfectly correlated.
A random forest adds random feature subsampling to decorrelate trees. The main
parameters include number of trees, candidate features per split, minimum node
size, maximum depth, sampling fraction, and the loss or split rule.

Random forests are often strong low-maintenance predictors and can discover
nonlinear interactions. They generally interpolate rather than extrapolate well:
predictions outside the observed support may remain near leaf averages. Record
support and extrapolation limits when forecasting prices, incomes, or trends.

Out-of-bag error is useful as an internal diagnostic, but it is not automatically
the final unbiased score after repeated tuning, feature engineering, or model
comparison. Use a held-out assessment matched to the target population.

## 3. Boosting and gradient-boosted trees

Boosting builds an additive model sequentially, fitting later learners to
residual structure left by earlier learners. Gradient boosting generalizes this
idea to a differentiable loss. Important complexity controls include the number
of boosting rounds, learning rate, tree depth, minimum leaf size, row and
feature subsampling, regularization, and early stopping.

A small learning rate with more rounds can trade computation for smoother
fitting. Early stopping requires a validation design that is separate from the
final test set. XGBoost and LightGBM are specialized implementations, not
methodological substitutes for stating the loss, split, tuning budget, and
baseline. Hyperparameter search must be recorded like any other specification
search.

## 4. Choosing an ensemble

| Situation | Candidate | Main check |
|---|---|---|
| Nonlinear iid prediction | Random forest or boosting | Held-out loss and calibration |
| Sparse linear signal | LASSO, ridge, or elastic net | Scaling, support stability, and baseline |
| Strong interactions and moderate sample | Boosted trees | Tuning burden and extrapolation |
| New-unit prediction | Any ensemble with group splits | Group leakage and group-level metrics |
| Time-dependent prediction | A tree ensemble with temporal resampling | Look-ahead, drift, and horizon |
| Causal heterogeneity | Honest causal forest or DML | Identification, overlap, honesty, and inference |

Do not choose the most flexible model based on in-sample fit. If predictive
performance is similar, prefer the simpler or more stable model and document the
trade-off. Compare candidates on the same folds, metric, target population, and
information set.

## 5. Importance is not an effect

Feature importance answers a predictive question: how much does the fitted
procedure rely on a feature under a specified perturbation or decomposition? It
does not answer whether changing that feature changes the outcome.

**Gini or split-gain importance** can favor continuous or high-cardinality
variables and can be distorted by correlated predictors. Prefer a method whose
limitations are understood, usually permutation importance or a model-specific
explanation, and report stability across resamples.

**Permutation importance** measures the loss increase after a feature is
permuted. It is conditional on the fitted model, the reference sample, the
permutation scheme, and correlations among predictors. Permuting one member of
a correlated group may make the group appear unimportant even when the group is
predictive. Consider grouped permutations or domain-level feature blocks.

**SHAP values** decompose a prediction relative to a background distribution
under a chosen cooperative-game approximation. They can show local contribution
and direction in a predictive model, but they are not marginal effects,
structural derivatives, treatment effects, or evidence of causality. State the
background data, model, link scale, and dependence caveats.

**Partial dependence** averages predictions over a feature grid. It can evaluate
feature values that are rare or impossible in the joint data, especially with
correlated predictors. Accumulated local effects can reduce some extrapolation
from impossible combinations but still describe the fitted prediction function.
Use conditional plots and support diagnostics where correlations matter.

## 6. Economic interpretation workflow

For each important feature or interaction:

1. define the prediction target and information set;
2. check support, missingness, and correlation with other predictors;
3. compare importance across resamples, folds, groups, and plausible model
   classes;
4. connect the pattern to economic theory or prior literature as a hypothesis;
5. test the hypothesis with an appropriate descriptive or causal design;
6. state explicitly that predictive importance is not a causal effect.

A feature may be important because it is a proxy, a measurement artifact, a
location marker, a post-treatment variable, or a member of a correlated feature
group. A stable importance ranking is still not identification.

## 7. Honest forests and causal forests

Ordinary random forests use the same observations to choose splits and estimate
leaf predictions. For causal heterogeneity, this can overfit treatment effects.
Honest methods separate observations used to construct the tree from observations
used to estimate leaf effects. Causal forests additionally require a causal
estimand, treatment assignment assumptions, overlap/positivity, nuisance
adjustment, and an inference procedure appropriate to the design.

A causal forest is not a license to interpret an ordinary random forest as a
causal forest. Check treatment coding, outcome timing, covariate availability,
cluster or panel dependence, sample weights, and whether the software's variance
estimator matches the data. If identification or overlap fails, honesty cannot
repair it.

## 8. Stability and diagnostics

Report more than a single importance chart or best score:

- held-out loss versus OLS, regularized, and simple policy baselines;
- fold, seed, group, and time-window variation;
- calibration and threshold behavior;
- subgroup and tail error rates;
- feature support and correlated-feature diagnostics;
- sensitivity to reasonable hyperparameter choices;
- training size and computational budget;
- extrapolation or covariate-shift checks.

If importance is central to the economic narrative, pre-specify the importance
method, reference sample, feature grouping, and stability criterion. Do not rank
models or features using the final test set and then report the same test set as
an unbiased assessment.

## 9. Reporting checklist

A tree or ensemble result should state:

- the target, loss, and generalization population;
- baseline models and candidate model classes;
- split and resampling design, including groups or time;
- tuning space, number of trials, early-stopping rule, and seed;
- preprocessing, weights, and missing-data handling;
- held-out metrics and calibration;
- importance or explanation method and its limitations;
- support, extrapolation, stability, and subgroup diagnostics;
- whether any causal interpretation uses a separate identification strategy.

## References

- Breiman (1996), "Bagging Predictors," *Machine Learning*, 24, 123-140. DOI:
   https://doi.org/10.1007/BF00058655.
- Breiman (2001), "Random Forests," *Machine Learning*, 45, 5-32. DOI:
   https://doi.org/10.1023/A:1010933404324.
- Friedman (2001), "Greedy Function Approximation: A Gradient Boosting
   Machine," *The Annals of Statistics*, 29(5), 1189-1232. DOI:
   https://doi.org/10.1214/AOS/1013203451.
- Hastie, Tibshirani, and Friedman (2009), *The Elements of Statistical
   Learning: Data Mining, Inference, and Prediction*, 2nd ed., Springer,
   Chapters 9 and 10. DOI: https://doi.org/10.1007/978-0-387-84858-7.
- Athey, Tibshirani, and Wager (2019), "Generalized Random Forests," *The
   Annals of Statistics*, 47(2), 1148-1178. DOI:
   https://doi.org/10.1214/17-AOS1709.
- Strobl et al. (2007), "Bias in random forest variable importance measures:
   Illustrations, sources and a solution," *BMC Bioinformatics*, 8, 25. DOI:
   https://doi.org/10.1186/1471-2105-8-25.
- Lundberg and Lee (2017), "A Unified Approach to Interpreting Model
   Predictions," *Advances in Neural Information Processing Systems*, 30.
   Proceedings: https://proceedings.neurips.cc/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html.
