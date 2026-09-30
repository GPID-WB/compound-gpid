# Research Skills

<!-- Created 2026-09-03. -->

Research-suite skills provide method-first guidance for economics and
econometrics research. They support interactive reasoning, implementation, and
review under the lifecycle `Scope -> Evidence -> Theory -> Method -> Execute ->
Verify -> Communicate -> Maintain`.

## Machine learning in economics

| Skill | Purpose | When to use | Availability | Source |
|---|---|---|---|---|
| `cr-skill-ml-economics` | ESL-led statistical learning, high-dimensional methods, sample splitting, model selection, out-of-sample evaluation, causal ML, panel/survey data, economic interpretation, and implementation routing | ML/Prediction tasks, ML implementation, or methodology review | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-ml-economics/SKILL.md) |

## Other research-suite skills

| Skill | Purpose | When to use | Availability | Source |
|---|---|---|---|---|
| `cr-skill-academic-writing` | Economics research writing, journal style, structure, notation, and citations | Drafting or reviewing academic research prose | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-academic-writing/SKILL.md) |
| `cr-skill-evidence-provenance` | Claim-evidence linkage, source identity, locators, and provenance controls | Ingesting evidence or justifying substantive research claims | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-evidence-provenance/SKILL.md) |
| `cr-skill-identification-strategies` | IV, RDD, DiD, event studies, synthetic control, matching, and required diagnostics | Choosing or auditing a causal identification strategy | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-identification-strategies/SKILL.md) |
| `cr-skill-mathematical-derivation` | Mathematical derivation, notation discipline, FOCs, likelihoods, moments, and code mapping | Deriving or translating an economics model | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-mathematical-derivation/SKILL.md) |
| `cr-skill-measurement` | Composite indicators, thresholds, clustering, weighting sensitivity, and comparability | Measuring, ranking, or classifying economic units | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-measurement/SKILL.md) |
| `cr-skill-publication-output` | Publication-quality tables, figures, captions, notes, and deterministic output | Producing research tables or figures | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-publication-output/SKILL.md) |
| `cr-skill-replication-standards` | Replication archives, lockfiles, seeds, data documentation, paths, and sensitive-data controls | Preparing or auditing a replication package | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-replication-standards/SKILL.md) |
| `cr-skill-research-eda` | Research-question-driven EDA, weighted summaries, missingness, outliers, and subgroup checks | Exploring data before specification or estimation | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-research-eda/SKILL.md) |
| `cr-skill-research-integrity` | P0 silent-error detection for code-math mismatch, search, identification, seeds, and assumptions | Any CR task requiring research-integrity checks | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-research-integrity/SKILL.md) |
| `cr-skill-research-scoping` | Scoping, stakeholder impact, and explicit normative choices before research work | Framing a new research question or policy analysis | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-research-scoping/SKILL.md) |
| `cr-skill-research-workflow` | CR task taxonomy, lifecycle, P0-P3 priorities, verification chain, and research layout | Any `/cr-*` workflow | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-research-workflow/SKILL.md) |
| `cr-skill-structural-econometrics` | Discrete choice, dynamic programming, simulation, MLE, GMM, and structural inference | Theory, structural modeling, or estimator implementation | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-structural-econometrics/SKILL.md) |
| `cr-skill-symbolic-verification` | Symbolic and numerical checks of gradients, Hessians, moments, and code-math mappings | Verifying mathematical derivations against implementation | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-symbolic-verification/SKILL.md) |
| `cr-skill-theory-data-dialogue` | Translating theory into empirical checks and documenting specification iteration | Connecting theoretical assumptions to observed data | Research-suite conditional skill | [Canonical source](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-theory-data-dialogue/SKILL.md) |

This is one canonical ML skill, not nine separate ML skills. Its activated `SKILL.md`
is a compact router implementing progressive disclosure. Detailed material is stored in eight focused references and
should be loaded only when the task needs it. Agents should normally read one or
two references, not the complete directory.

## ML reference map

| Reference | Focus |
|---|---|
| [`foundations-and-esl.md`](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-ml-economics/references/foundations-and-esl.md) | Prediction targets, loss, risk, generalization error, bias-variance, complexity, baselines, and prediction versus causal interpretation |
| [`high-dimensional-and-regularized-methods.md`](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-ml-economics/references/high-dimensional-and-regularized-methods.md) | Ridge, LASSO, elastic net, sparsity, approximate sparsity, selection, post-LASSO, double selection, and debiased inference |
| [`splitting-resampling-and-evaluation.md`](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-ml-economics/references/splitting-resampling-and-evaluation.md) | iid, group, panel, temporal, stratified, nested, and cross-fitting splits; data leakage; metrics and final assessment |
| [`trees-ensembles-and-interpretation.md`](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-ml-economics/references/trees-ensembles-and-interpretation.md) | Trees, bagging, random forest, boosting, permutation importance, SHAP, partial dependence, and honest forests |
| [`econometric-causal-ml.md`](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-ml-economics/references/econometric-causal-ml.md) | Double/debiased ML, Neyman orthogonality, cross-fitting, overlap, heterogeneous treatment effects, and identification boundaries |
| [`survey-panel-and-target-population.md`](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-ml-economics/references/survey-panel-and-target-population.md) | Target population, probability weights, clustering, stratification, panel dependence, and design-based variance limits |
| [`implementation-r-tidymodels.md`](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-ml-economics/references/implementation-r-tidymodels.md) | R workflows using rsample, recipes, parsnip, workflows, tune, yardstick, and last_fit |
| [`implementation-python-scikit-learn.md`](https://github.com/GPID-WB/compound-gpid/blob/main/.github/skills/cr-skill-ml-economics/references/implementation-python-scikit-learn.md) | Python pipelines using scikit-learn, ColumnTransformer, explicit splitters, cross_validate, GridSearchCV, and reproducible scoring |

## Methodological orientation

The ML skill uses Hastie, Tibshirani, and Friedman's *The Elements of
Statistical Learning* as its statistical-learning spine. It asks researchers to
state the target, loss, complexity, data-generating structure, and assessment
before naming an algorithm.

Predictive performance, feature importance, regularized coefficients, and
`sample_weight` are not automatically causal or survey-inferential results.
Causal claims require an estimand, identification strategy, overlap and timing
conditions, and appropriate uncertainty. Population claims require a documented
target population, weight and design treatment, and a defensible variance
procedure.

## Canonical source and generated targets

Edit `.github/skills/cr-skill-ml-economics/` only. The `.claude/skills/`,
`.agents/skills/`, `.opencode/skills/`, and `.kilo/skills/` copies are generated
atomic bundles that include the `SKILL.md` and its regular reference files.
Regenerate them with the repository's target generator and run target drift
checks after changing the canonical skill.

## Related pages

- [Research Handbook](../research/index.md)
- [Skills Catalog](index.md)
- [Research Agents](../reference/agents.md)
- [Complete Reference](../reference.md)
- [Modular Guide](../modular-guide.md)
