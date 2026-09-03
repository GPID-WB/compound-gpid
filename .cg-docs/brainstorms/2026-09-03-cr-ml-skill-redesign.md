---
date: 2026-09-03
title: "CR ML Skill Redesign for Econometricians"
status: decided
scope: "Deep"
artifact-schema-version: 1
chosen-approach: "Layered ML skill with the full progressive-disclosure reference set"
tags: [research, machine-learning, econometrics, statistical-learning, high-dimensional, model-selection, cross-validation, context-budget]
---
<!-- Valid status values: decided, in-progress, abandoned -->

# CR ML Skill Redesign for Econometricians

## Context

The existing `cr-skill-ml-economics` skill is a single broad `SKILL.md` that mixes
statistical-learning theory, econometric inference, data-structure safeguards,
implementation examples, and review rules. It contains useful material but does
not provide enough separation between concepts that every ML task needs and
details that should be loaded only for a particular method or data setting.

The redesign serves senior applied econometricians and PhD students equally. It
must support interactive methodological reasoning, `/cr-work` implementation,
and `/cr-review` audits. The skill should be method-first and theory-led, with
implementation guidance available on demand.

The conceptual spine is Hastie, Tibshirani, and Friedman's *The Elements of
Statistical Learning*, second edition: define the prediction target and loss,
reason about complexity and the bias-variance trade-off, distinguish estimation
from assessment, and compare flexible methods with meaningful baselines. The
skill then adds the econometric distinctions and safeguards needed for causal
interpretation, high-dimensional inference, dependent observations, survey
target populations, and reproducible research.

External research informed the design:

- The [Agent Skills specification](https://agentskills.io/specification) describes
  metadata, an activated `SKILL.md`, and on-demand resources as progressive
  disclosure. It recommends focused reference files and keeping the main file
  under 500 lines; this project has the stricter local precedent of a compact
  routing file of about 120 lines.
- [Anthropic's Agent Skills guidance](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)
  recommends evaluation-first development, separating rarely co-used contexts,
  and iterating from observed agent trajectories.
- The official [scikit-learn cross-validation guidance](https://scikit-learn.org/stable/modules/cross_validation.html)
  emphasizes that splits must reflect groups, time, and dependence; pipelines
  must contain preprocessing; nested evaluation protects the final assessment;
  and stratification is an engineering aid, not a substitute for a statistical
  design.
- The official [tidymodels resampling](https://www.tidymodels.org/start/resampling/),
  [tuning](https://www.tidymodels.org/start/tuning/), and
  [recipes](https://www.tidymodels.org/start/recipes/) guidance separates
  training, resampling, and final testing, bundles preprocessing with models,
  and fits transformations using only the analysis data.
- The [ESL reference site](https://hastie.su.domains/ElemStatLearn/) establishes
  the canonical second-edition reference for data mining, inference, and
  prediction.

## Requirements

### Audience and use

- Optimize equally for senior applied econometricians and PhD students.
- Support interactive research assistance, `/cr-work` implementation, and
  `/cr-review` methodology audits.
- Produce method-selection guidance, review checklists, literature-backed
  research notes, and implementation references.

### Methodological foundation

- Use the ESL statistical-learning framework as the organizing vocabulary and
  conceptual sequence.
- Begin with the research goal: prediction, descriptive learning, variable
  selection, causal estimation, heterogeneous treatment effects, or a nuisance
  function inside an econometric estimator.
- Explain the target population, data-generating structure, loss or estimand,
  assumptions, and decision rule before recommending an algorithm.
- Keep predictive performance separate from causal interpretation and from
  structural or reduced-form economic claims.

### Methods and econometric relevance

- Cover linear prediction and regularization: OLS as a benchmark, ridge, LASSO,
  elastic net, screening, sparsity, approximate sparsity, standardization,
  penalty selection, post-LASSO, rigorous LASSO, and debiased/desparsified LASSO.
- Cover econometric high-dimensional inference: double selection, double/debiased
  machine learning, Neyman orthogonality, cross-fitting, nuisance estimation,
  and honest heterogeneous-treatment-effect methods.
- Cover trees and ensembles: bagging, random forests, boosting, gradient-boosted
  trees, honest forests, variable importance, partial dependence, and SHAP with
  explicit predictive-not-causal caveats.
- Cover dimension reduction and feature construction: PCA, factor methods,
  supervised feature selection, and the economic interpretation limits of latent
  components.
- Include a bounded neural-network/deep-learning overview where it helps
  method selection, but exclude computer vision, NLP, reinforcement learning,
  production MLOps, and deployment infrastructure.

### Splitting, selection, and evaluation

- Explain train, validation, and test roles and when cross-validation replaces a
  fixed validation set.
- Cover iid, grouped or clustered, panel, stratified, temporal, rolling-origin,
  nested, repeated, and cross-fitting designs.
- Make high-dimensional and survey-weighted settings first-class cases.
- Cover leakage through preprocessing, feature engineering, target encoding,
  imputation, resampling, and group statistics.
- Cover hyperparameter search, search-space documentation, tuning uncertainty,
  model-selection uncertainty, baselines, and specification-search risks.
- Cover out-of-sample metrics for regression and classification, weighted metrics,
  calibration, rare-outcome metrics, subgroup performance, error analysis, and
  final held-out assessment.

### Implementation and reproducibility

- Use R `tidymodels` as the default implementation ecosystem.
- Use Python `scikit-learn` pipelines as the default implementation ecosystem.
- Use other established packages for specialized methods when their scope,
  assumptions, and interfaces are documented, including packages for boosting,
  causal forests, and Double ML.
- Require explicit seeds, version records, data-split records, and transparent
  reporting of tuning and evaluation decisions.
- Treat survey weights with methodological nuance: distinguish target-population
  loss, estimator support for observation weights, complex-design variance, and
  the limits of treating `sample_weight` as a complete survey design solution.

### Context and maintenance

- Keep the main `SKILL.md` as a compact router and workflow, targeting the
  repository convention of no more than about 120 lines.
- Keep references one level below the skill and make each file focused enough to
  load independently.
- Instruct agents to read only the one or two references needed for the current
  task rather than the complete reference directory.
- Add representative-task evaluations and context-budget checks so new detail
  improves behavior without silently increasing default context.

## Approaches Considered

### Approach 1: Expand the current file

Add the missing theory and methods directly to `SKILL.md`.

- Pros: Fast to begin and easy to locate.
- Cons: Mixes foundations, safeguards, review rules, and code; conflicts with
  the project's context-budget direction; becomes difficult to retrieve from.
- Effort: Medium.
- Decision: Rejected.

### Approach 2: Layered ML skill with full progressive disclosure

Keep one canonical `cr-skill-ml-economics` trigger with a compact router and a
full set of focused references. The initial reference map is:

1. `foundations-and-esl.md`
2. `high-dimensional-and-regularized-methods.md`
3. `splitting-resampling-and-evaluation.md`
4. `trees-ensembles-and-interpretation.md`
5. `econometric-causal-ml.md`
6. `survey-panel-and-target-population.md`
7. `implementation-r-tidymodels.md`
8. `implementation-python-scikit-learn.md`

- Pros: Preserves one canonical trigger; supports both audiences; keeps theory
  central; makes method-specific depth available on demand; matches the Agent
  Skills specification and local Python/R skill patterns.
- Cons: Requires precise routing instructions, reference inventory tests, and
  representative-task evaluations; a full first release has meaningful writing
  and review cost.
- Effort: Large.
- Decision: Chosen.

### Approach 3: CR ML skill family

Replace the single skill with independently triggered skills for foundations,
high-dimensional ML, evaluation, causal ML, and implementation.

- Pros: Maximum per-task granularity and potentially smaller activated context.
- Cons: More competing triggers, duplicated boundaries, prompt and agent routing
  changes, and a risk that only part of the necessary methodology is activated.
- Effort: Large.
- Decision: Deferred. Reconsider only if evaluation shows that one canonical
  trigger cannot route reliably.

## Decision

Implement Approach 2 with the full eight-reference map. The first release will
not ask agents to load all eight files. The compact `SKILL.md` will provide a
short modeling triage and a task-to-reference routing table, then enforce the
non-negotiable boundaries around leakage, prediction versus causal claims,
sample structure, reproducibility, and final assessment.

The reference files will carry the detailed ESL-led theory, econometric methods,
data-structure-specific splitting rules, evaluation logic, and language-specific
implementation recipes. The full map is justified because the requested users
need both a deep methodological foundation and practical support across
interactive reasoning, implementation, and review; progressive disclosure keeps
those needs from becoming one default context payload.

The design will preserve the useful existing material but revise claims that are
too absolute. In particular, survey-weight guidance must distinguish weighted
prediction targets and package-level observation weights from full complex-survey
inference. The skill should not imply that passing `sample_weight` automatically
solves clustering, stratification, variance estimation, or representativeness.

## Devil's Advocate

- Problem validation: The current file's mixed responsibilities and broad scope
  are a credible design problem, but the implementation should begin with a
  representative-task benchmark to identify actual agent misses and retrieval
  failures.
- Simplicity: One canonical skill plus focused references is likely sufficient;
  a family of independently triggered skills would add routing complexity before
  there is evidence that it is needed.
- Effort-value: Eight references create substantial writing and maintenance cost.
  Each file therefore needs a distinct retrieval role, and the core must remain
  small. Evaluation should determine whether any reference can later be merged
  or retired.
- Charter alignment: The decision supports statistical correctness,
  reproducibility, research integrity, the CR suite, and context-budget work.
  The survey-weight qualification above is required to avoid encoding a blanket
  rule that exceeds what individual ML libraries or survey designs support.

## Next Steps

1. Turn this decision into an implementation plan with the eight-file taxonomy,
   core routing contract, and ownership of each method area.
2. Rewrite `cr-skill-ml-economics/SKILL.md` as a compact ESL-led triage and
   routing file, keeping it within the repository's local size target.
3. Create the eight focused references, with the high-dimensional,
   splitting/resampling/evaluation, and econometric causal ML references given
   the deepest treatment.
4. Update `@cr-ml-methodology` and any CR routing or documentation surfaces that
   need to know the new reference paths.
5. Build a representative evaluation matrix covering iid prediction,
   high-dimensional selection, panel or clustered data, survey-weighted
   prediction, DML, and methodology review tasks.
6. Add tests for frontmatter, reference inventory, routing coverage, broken paths,
   and context-budget regressions; regenerate native platform skill bundles when
   implementation begins.
7. Review methodological claims against the cited literature and package
   documentation, especially survey weighting, debiased LASSO, cross-fitting,
   nested evaluation, and interpretation of importance measures.
