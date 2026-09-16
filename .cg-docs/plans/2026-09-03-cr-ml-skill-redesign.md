---
date: 2026-09-03
title: "CR ML Skill Redesign for Econometricians"
status: completed
completed-date: 2026-09-03
scope: "Deep"
task-type: "ML/Prediction"
brainstorm: ".cg-docs/brainstorms/2026-09-03-cr-ml-skill-redesign.md"
language: "R/Python/Markdown"
estimated-effort: "large"
deviation-policy: "ask"
artifact-schema-version: 1
phases: 4
completed-phases: [1, 2, 3, 4]
roadmap-features: [skills-enhancement/cr-ml-skill-redesign-for-econometricians]
execution-report: ".cg-docs/work-reports/2026-09-03-cr-ml-skill-redesign.md"
tags: [research, machine-learning, econometrics, statistical-learning, high-dimensional, model-selection, evaluation, context-budget]
---

# Plan: CR ML Skill Redesign for Econometricians

## Objective

Replace the monolithic `cr-skill-ml-economics/SKILL.md` with a compact,
Hastie-Tibshirani-Friedman-led router and eight focused progressive-disclosure
references. Give senior econometricians and PhD students one coherent
methodological foundation for interactive assistance, implementation, and
review, while preserving context budgets and canonical-to-native packaging
parity.

## Context

The current CR ML skill combines statistical-learning theory, econometric
inference, data-structure safeguards, implementation examples, and review rules
in one large file. Its content is useful but difficult to retrieve selectively,
and `/cr-work` does not explicitly route the ML skill for ML implementation
plans. The current `@cr-ml-methodology` agent also encodes survey-weight and
validation rules that need methodological qualification.

The approved design keeps one canonical trigger and adds this full reference
map under `.github/skills/cr-skill-ml-economics/references/`:

1. `foundations-and-esl.md`
2. `high-dimensional-and-regularized-methods.md`
3. `splitting-resampling-and-evaluation.md`
4. `trees-ensembles-and-interpretation.md`
5. `econometric-causal-ml.md`
6. `survey-panel-and-target-population.md`
7. `implementation-r-tidymodels.md`
8. `implementation-python-scikit-learn.md`

Detailed theory and method logic are primary. R `tidymodels` and Python
`scikit-learn` are default implementation ecosystems, with established
specialized packages documented only where their assumptions and interfaces are
clear. The implementation excludes computer vision, NLP, reinforcement
learning, and production MLOps/deployment; deep learning receives only a bounded
method-selection overview.

The design follows the Agent Skills progressive-disclosure specification and
this repository's local thin-router convention. The generator already packages
skill directories recursively as atomic bundles and validates skill-local
Markdown references, so native mirrors must be regenerated rather than edited.

## Requirements

| ID | Requirement | Source |
|----|-------------|--------|
| R1 | Keep one canonical `cr-skill-ml-economics` skill trigger with a compact router and explicit demand-loading instructions. | Brainstorm decision |
| R2 | Keep the canonical `SKILL.md` at or below the local approximately 120-line routing target and below the skill review threshold where practical. | Context/skill consolidation convention |
| R3 | Organize the full eight-reference map with one-level relative paths and distinct retrieval roles. | Brainstorm decision |
| R4 | Use ESL as the conceptual spine: prediction target, loss, estimand, complexity, bias-variance trade-off, estimation versus assessment, and benchmark comparison. | User request and brainstorm |
| R5 | Cover linear prediction and regularization: OLS benchmark, ridge, LASSO, elastic net, scaling, sparsity, approximate sparsity, screening, penalty selection, post-LASSO, rigorous LASSO, and debiased/desparsified LASSO. | User request and brainstorm |
| R6 | Cover econometric high-dimensional inference: double selection, DML, Neyman orthogonality, cross-fitting, nuisance functions, and honest heterogeneous-treatment-effect methods. | User request and brainstorm |
| R7 | Cover trees and ensembles: bagging, random forests, boosting, gradient-boosted trees, honest forests, importance, partial dependence, and SHAP with predictive-not-causal caveats. | Brainstorm decision |
| R8 | Cover dimension reduction, factor methods, feature construction, and economic interpretation limits. | Brainstorm decision |
| R9 | Cover iid, grouped/clustered, panel, stratified, temporal, rolling-origin, repeated, nested, and cross-fitting sample-splitting designs. | User request and brainstorm |
| R10 | Explain preprocessing, feature engineering, target encoding, imputation, resampling, and group-statistic leakage controls. | Brainstorm decision |
| R11 | Cover hyperparameter search, search-space and trial reporting, tuning/model-selection uncertainty, specification-search risks, meaningful baselines, and held-out assessment. | User request and brainstorm |
| R12 | Cover regression/classification metrics, weighted metrics, calibration, rare-outcome metrics, subgroup performance, error analysis, forecast comparison, and final test assessment. | Brainstorm decision |
| R13 | Make panel/clustered and survey-weighted settings first-class, distinguishing target-population loss, estimator support for weights, complex-design variance, clustering, stratification, and representativeness. | User request and devil's advocate |
| R14 | Use R `tidymodels` and Python `scikit-learn` as default implementation stacks; document specialized packages such as DoubleML, `grf`, XGBoost, and LightGBM only with scope and assumptions. | User clarification |
| R15 | Require explicit seeds, split records, version records, and transparent tuning/evaluation decisions. | Charter and brainstorm |
| R16 | Update `/cr-work` so ML/Prediction plans and ML implementation tasks load `cr-skill-ml-economics` conditionally without loading all references. | Local routing inspection |
| R17 | Update `@cr-ml-methodology` to route its checks to relevant references and correct overbroad survey-weight assertions while preserving P0/P1 research-integrity behavior. | Local agent inspection |
| R18 | Add representative-task evaluations for iid prediction, high-dimensional selection, panel/clustered data, survey-weighted prediction, DML, and review/leakage tasks. | Brainstorm decision and external skill guidance |
| R19 | Add tests for frontmatter, reference inventory, local-link closure, routing coverage, content contracts, evaluation fixtures, context budget, generated parity, and documentation. | Brainstorm decision and local test conventions |
| R20 | Update public CR skill documentation and retain module ownership under `suite-cr`; no module-registry change is required. | Charter and local registry |
| R21 | Regenerate `.claude`, `.agents`, `.opencode`, and `.kilo` skill bundles from canonical `.github` sources. | Generator contract |
| R22 | Preserve existing useful ML content unless it is superseded by a more precise theory, package, or survey-design qualification. | Brainstorm decision |

## Implementation Steps

## Phase 1: Core Router and Statistical-Learning Foundation

### 1. Establish the content taxonomy and baseline inventory

- **Requirements**: R1, R3, R4, R22
- **Files**:
  - `.github/skills/cr-skill-ml-economics/SKILL.md`
  - `.github/skills/cr-skill-ml-economics/references/` (new directory)
  - `scripts/tests/fixtures/cr_ml_skill_evaluation.json` (new fixture)
  - `scripts/tests/test_cr_ml_skill.py` (new test file)
- **Details**:
  - Record the existing skill's useful concepts and map each to one of the
    eight references before moving content.
  - Define the routing labels used by the core: foundations, regularization,
    splitting/evaluation, ensembles, econometric causal ML, survey/panel data,
    R implementation, and Python implementation.
  - Define representative task records with task type, data structure, goal,
    expected references, and required safeguards. Keep fixture text inert data,
    not executable instructions.
  - Do not add an independently triggered skill family.
- **Test Scenarios**:
  - Happy path: every eight reference labels has one unique fixture route.
  - Edge case: a task requiring both high-dimensional methods and panel-aware
    evaluation routes to both relevant references without routing the full set.
  - Error path: an unknown task label produces a clear uncovered-route failure.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
- **Acceptance criteria**:
  - The taxonomy and evaluation fixture define the intended ownership of every
    method area before substantive content is redistributed.
  - No reference has an ambiguous or duplicate primary retrieval role.

### 2. Rewrite the compact ML skill router

- **Requirements**: R1, R2, R3, R4, R9, R10, R15, R22
- **Files**:
  - `.github/skills/cr-skill-ml-economics/SKILL.md`
- **Details**:
  - Preserve valid frontmatter: `name`, `module`, and a trigger-rich
    `description` that mentions econometric ML, high-dimensional methods,
    splitting/evaluation, causal ML, survey/panel data, and implementation.
  - Replace inline tutorials with a short workflow:
    1. identify goal/estimand, target population, data structure, loss, and
       prediction availability;
    2. choose the appropriate reference(s);
    3. check leakage, split design, weights, seeds, tuning, and final assessment;
    4. distinguish predictive from causal/structural interpretation;
    5. report assumptions, baselines, uncertainty, and limitations.
  - Add a compact task-to-reference routing table and instruct agents to load
    only the one or two references needed for the current task. State that the
    complete reference directory must not be loaded by default.
  - Keep non-negotiable research-integrity rules inline: no causal claims from
    predictive fit, no test-set tuning, no preprocessing leakage, no unseeded
    randomness, and no silent treatment of unsupported weights or dependence.
  - Include bounded deep-learning scope and explicit out-of-scope domains.
- **Test Scenarios**:
  - Happy path: all eight reference filenames and all six representative task
    categories appear in routing language.
  - Edge case: the core remains below 120 lines without losing the integrity
    rules or survey/panel routing pointer.
  - Error path: a removed reference filename or a request to load all references
    fails the content contract.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
- **Acceptance criteria**:
  - `SKILL.md` is a router rather than a second technical textbook.
  - The file is ASCII/UTF-8 clean, valid frontmatter, locally linked, and no
    longer contains duplicated implementation blocks that belong in references.

### 3. Create the ESL-led theory and high-dimensional references

- **Requirements**: R4, R5, R6, R8, R11, R15, R22
- **Files**:
  - `.github/skills/cr-skill-ml-economics/references/foundations-and-esl.md`
  - `.github/skills/cr-skill-ml-economics/references/high-dimensional-and-regularized-methods.md`
- **Details**:
  - `foundations-and-esl.md`: define supervised learning notation, prediction
    target versus estimand, conditional mean/probability targets, loss
    functions, risk/generalization error, training error, bias-variance and
    complexity, regularization, baseline models, calibration, and the
    prediction/causal/structural boundary. Organize references to relevant ESL
    chapters without reproducing copyrighted text.
  - `high-dimensional-and-regularized-methods.md`: explain OLS as benchmark,
    ridge/LASSO/elastic net objectives, standardization, tuning, sparsity and
    approximate sparsity, correlated predictors, screening, post-LASSO,
    rigorous LASSO, double selection, debiased/desparsified LASSO, selective
    inference limits, and the distinction between prediction and inference.
  - Include econometric notation, assumptions, failure modes, method-selection
    guidance, and literature pointers rather than package-first tutorials.
  - Mark all uncertain or package-specific claims for later verification.
- **Test Scenarios**:
  - Happy path: required equations/concepts, ESL terminology, and econometric
    method names are present.
  - Edge case: references explicitly warn against treating selected/shrunk
    coefficients as ordinary causal estimates.
  - Error path: a reference contains unsupported claims or copied source prose;
    content review blocks completion until corrected.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
- **Acceptance criteria**:
  - A senior researcher can use the references to choose and explain a method;
    a PhD student can follow the reasoning from target to estimator and
    assessment without relying on a code snippet as the explanation.

## Phase 2: Data Structure, Evaluation, and Econometric Methods

### 4. Create splitting, resampling, and evaluation references

- **Requirements**: R9, R10, R11, R12, R15, R22
- **Files**:
  - `.github/skills/cr-skill-ml-economics/references/splitting-resampling-and-evaluation.md`
  - `.github/skills/cr-skill-ml-economics/references/survey-panel-and-target-population.md`
- **Details**:
  - Explain train/validation/test roles, when k-fold CV replaces a fixed
    validation set, nested CV, repeated CV, cross-fitting, and why evaluation
    must be separated from tuning.
  - Cover iid, group/cluster, panel, stratified, temporal, rolling-origin,
    blocked, and leave-group-out designs. Explain the deployment/generalization
    target each design estimates and when stratification is only an engineering
    aid.
  - Cover leakage through transformations, feature engineering, target
    encoding, imputation, resampling, group aggregates, and future information.
  - Define regression and classification metrics, OOS R2 with the training
    benchmark, weighted metrics, calibration, PR-AUC/AUROC for rare outcomes,
    subgroup/error analysis, forecast comparison, and test-set contamination.
  - In `survey-panel-and-target-population.md`, distinguish a finite or
    superpopulation target, weighted empirical loss, probability weights,
    clustering, stratification, replicate/design-based variance, and package
    limitations. Explain that `sample_weight` is not automatically a complete
    complex-survey solution.
  - Include a checklist for recording sample structure, target population,
    splitting unit, weights, metrics, and evaluation horizon.
- **Test Scenarios**:
  - Happy path: panel task routes to group-aware splitting and survey task
    routes to target-population/weight qualification.
  - Edge case: stratified rare-outcome CV is not presented as a replacement for
    group or temporal separation.
  - Error path: random row splitting on repeated units or temporal data is
    identified as invalid for the stated generalization target.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
- **Acceptance criteria**:
  - The reference gives a defensible split/evaluation design before naming an
    algorithm and does not overclaim what observation weights accomplish.

### 5. Create ensemble and interpretation references

- **Requirements**: R7, R8, R11, R12, R15, R22
- **Files**:
  - `.github/skills/cr-skill-ml-economics/references/trees-ensembles-and-interpretation.md`
- **Details**:
  - Cover trees, bagging, random forests, boosting, gradient-boosted trees,
    early stopping, tuning, extrapolation limits, and when flexible methods
    are useful for economic prediction or heterogeneity discovery.
  - Explain permutation importance, SHAP, partial dependence, accumulated
    local effects where relevant, correlated-feature interpretation, subgroup
    stability, and why these are predictive explanations rather than causal
    effects or marginal treatment effects.
  - Cover honest forests and causal forests only in the causal context, including
    sample honesty, treatment assignment, overlap, nuisance adjustment, and
    inference caveats.
  - Require meaningful linear/regularized baselines and held-out comparison.
- **Test Scenarios**:
  - Happy path: feature importance routes with explicit predictive-not-causal
    language and a stability/error-analysis requirement.
  - Edge case: correlated predictors prevent a simplistic single-variable
    importance interpretation.
  - Error path: Gini importance or SHAP is used as a causal effect without an
    identification strategy; the content contract must catch the omission.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
- **Acceptance criteria**:
  - Flexible models are explained through their statistical behavior and
    economic use case, not a catalog of package calls.

### 6. Create econometric causal-ML reference

- **Requirements**: R5, R6, R9, R11, R12, R15, R22
- **Files**:
  - `.github/skills/cr-skill-ml-economics/references/econometric-causal-ml.md`
- **Details**:
  - Explain when ML is a nuisance-function tool inside an identified causal
    design rather than an estimator of causality by itself.
  - Cover partially linear and partially separable models, DML, double
    selection, Neyman orthogonality, cross-fitting, nuisance learner choice,
    overlap/positivity, treatment and outcome types, clustered/panel dependence,
    honest heterogeneous treatment effects, and inference.
  - State the conditions under which cross-fitting helps and the conditions it
    does not repair, including poor identification, lack of overlap, invalid
    moments, dependence ignored by folds, or target-population mismatch.
  - Include method-selection and reporting checklists plus canonical literature
    pointers for Chernozhukov et al., Belloni et al., and causal forests.
- **Test Scenarios**:
  - Happy path: a DML request routes here plus the split/evaluation reference.
  - Edge case: a causal forest request is separated from ordinary random-forest
    prediction and requires honesty/identification language.
  - Error path: a predictive LASSO is proposed as a causal estimate without a
    causal design; the reference requires a correction.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
- **Acceptance criteria**:
  - The reference provides a defensible bridge from econometric estimand and
    identification assumptions to ML nuisance estimation and inference.

## Phase 3: Language-Specific Implementation References

### 7. Create R `tidymodels` implementation reference

- **Requirements**: R12, R13, R14, R15, R19, R22
- **Files**:
  - `.github/skills/cr-skill-ml-economics/references/implementation-r-tidymodels.md`
- **Details**:
  - Use `rsample`, `recipes`, `parsnip`, `workflows`, `tune`, `yardstick`, and
    `last_fit` as the default workflow vocabulary.
  - Show split-first, recipe-inside-workflow, resampling, tuning, finalization,
    and held-out assessment patterns for regression and classification.
  - Show grouped, temporal, and stratified resampling where supported, and
    identify when a custom split is required.
  - Include preprocessing, imputation, dummy encoding, scaling, class
    imbalance, metrics, case weights where the engine supports them, and an
    explicit warning that case weights do not automatically implement a full
    complex survey design.
  - Add specialized-package adapters only for clearly bounded uses such as
    `grf`, `DoubleML`, `glmnet`, `ranger`, or XGBoost; state when an engine falls
    outside the default `tidymodels` abstraction.
  - Do not use stale `caret` patterns as the default.
- **Test Scenarios**:
  - Happy path: an R implementation task can identify the workflow order and
    where preprocessing is fitted.
  - Edge case: grouped or temporal resampling is not silently replaced by
    ordinary `vfold_cv()`.
  - Error path: a code example implies that `case_weights` solves survey
    clustering/variance; content tests require the qualification.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
- **Acceptance criteria**:
  - The R reference is implementation-ready while keeping method logic in the
    theory references and using current tidymodels idioms.

### 8. Create Python `scikit-learn` implementation reference

- **Requirements**: R10, R12, R13, R14, R15, R19, R22
- **Files**:
  - `.github/skills/cr-skill-ml-economics/references/implementation-python-scikit-learn.md`
- **Details**:
  - Use `Pipeline`, `ColumnTransformer`, estimator APIs, explicit splitters,
    `cross_validate`, `GridSearchCV`/`RandomizedSearchCV`, and held-out scoring
    as the default vocabulary.
  - Show preprocessing inside pipelines, group-aware and temporal splitters,
    stratification only where appropriate, sample weights at fit/evaluation
    boundaries, metrics, calibration, and final test assessment.
  - Explain that `train_test_split` cannot account for groups and that ordinary
    shuffled CV is inappropriate for time-dependent or grouped observations.
  - Include specialized adapters for `doubleml`, causal forests, XGBoost, or
    LightGBM only where scikit-learn's general interface is insufficient; keep
    package-specific API details bounded and version-sensitive claims explicit.
  - Use reproducible `random_state`/RNG patterns and avoid introducing pandas
    as the project's general data-manipulation convention; conversions at a
    library boundary may be documented when required by the estimator.
  - Do not present `sample_weight` as a complete complex-survey design or
    variance estimator.
- **Test Scenarios**:
  - Happy path: an implementation request routes here and gets a pipeline-first
    answer with the correct splitter and metric.
  - Edge case: a group split is used to create the final holdout rather than
    calling `train_test_split` with no group handling.
  - Error path: preprocessing is fit before the split or CV helper is used with
    a contaminated transformed matrix; content tests require a pipeline fix.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
- **Acceptance criteria**:
  - The Python reference is practical for current scikit-learn workflows and
    clearly marks where specialized econometric packages are needed.

## Phase 4: Routing, Documentation, Tests, and Generated Targets

### 9. Update CR workflow and methodology-agent routing

- **Requirements**: R1, R3, R9, R10, R13, R16, R17, R22
- **Files**:
  - `.github/prompts/cr-work.prompt.md`
  - `.github/agents/cr-ml-methodology.agent.md`
  - `.github/prompts/cr-brainstorm.prompt.md` (only if routing wording needs
    synchronization)
  - `.github/prompts/cr-plan.prompt.md` (only if routing wording needs
    synchronization)
- **Details**:
  - In `/cr-work`, add a conditional ML/Prediction route that loads
    `cr-skill-ml-economics` and directs the agent to select the relevant
    references. For ML implementation, retain mathematical-derivation loading
    only when the plan genuinely contains derived mathematics; do not load all
    ML references automatically.
  - In `@cr-ml-methodology`, add a reference-routing table by check: leakage
    and splits, tuning/evaluation, high-dimensional inference, causal ML,
    ensembles/interpretation, and survey/panel target population.
  - Preserve the eight-check review protocol and output format, but revise
    Check 8 so it asks whether the stated target population and estimator
    support require weights, and whether weights are paired with an appropriate
    variance/dependence treatment. Do not turn unsupported `sample_weight` use
    into a false completeness claim; still flag unweighted official-population
    prediction when weighting is substantively required.
  - Preserve cross-references to research-integrity and identification agents.
- **Test Scenarios**:
  - Happy path: ML/Prediction and ML implementation routes load the core skill;
    non-ML tasks do not load it merely because `/cr-work` is running.
  - Edge case: an ML review routes to one or two references per check rather
    than the full directory.
  - Error path: the agent reverts to the old universal-weight assertion or a
    prompt loses the skill name; routing tests fail.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
  - `python -m pytest scripts/tests/test_cr_baseline.py -q`
- **Acceptance criteria**:
  - Interactive, implementation, and review paths all have explicit, bounded
    ML routing and retain existing CR lifecycle/integrity behavior.

### 10. Add content, routing, and representative-task tests

- **Requirements**: R2, R3, R4, R5, R6, R7, R8, R9, R10, R11, R12, R13, R14, R15, R18, R19, R20, R22
- **Files**:
  - `scripts/tests/test_cr_ml_skill.py`
  - `scripts/tests/fixtures/cr_ml_skill_evaluation.json`
  - `tests/prompt-tools.Tests.ps1` (only if a canonical frontmatter or skill
    inventory assertion belongs in the existing Pester contract)
- **Details**:
  - Test the core file exists, parses frontmatter, stays within the line/token
    target, names all eight references, instructs selective loading, and
    contains the integrity boundary terms.
  - Test each reference exists, is non-empty, has a distinct purpose, and
    contains required method/theory/routing terms. Assertions must be
    independent rather than relying on a single broad alternation.
  - Implement fixture-driven routing checks: expected references are a set, no
    unexpected references are selected, and core-only tasks do not load detail.
  - Add checks for the revised survey-weight nuance, DML/cross-fitting, group and
    temporal splitting, nested tuning/final testing, predictive interpretation,
    and implementation-stack defaults.
  - Keep tests structural/content-focused; they must not execute code examples
    or require R/Python ML packages.
- **Test Scenarios**:
  - Happy path: all representative task records resolve to expected references
    and safeguards.
  - Edge case: one task legitimately resolves to two references; a task with
    no specialized setting resolves only to foundations plus evaluation.
  - Error path: deleting or renaming a reference, removing a route, or deleting
    a survey qualification causes a targeted failure.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py -q`
  - `python -m pytest scripts/tests/test_cr_baseline.py -q`
  - Safe Pester validation through `tests/Run-Tests.ps1` at the final gate.
- **Acceptance criteria**:
  - Future edits cannot silently remove a reference, route, or high-risk
    methodological qualification.

### 11. Update documentation and regenerate native bundles

- **Requirements**: R3, R19, R20, R21
- **Files**:
  - `docs/skills/index.md`
  - `docs/skills/analysis.md` or a new CR-focused catalog page if the existing
    information architecture requires it
  - `docs/reference.md`
  - `.claude/skills/cr-skill-ml-economics/**` (generated)
  - `.agents/skills/cr-skill-ml-economics/**` (generated)
  - `.opencode/skills/cr-skill-ml-economics/**` (generated)
  - `.kilo/skills/cr-skill-ml-economics/**` (generated)
- **Details**:
  - Document the CR ML skill's audience, goals, availability, compact-router
    behavior, eight references, and canonical-source rule in the public catalog.
  - Preserve the existing general reference entry and make the progressive
    disclosure structure discoverable without treating references as separate
    skills.
  - Run the canonical generator from `.github` and verify every reference is
    present in every generated native skill bundle with matching bytes except
    expected runtime-path rewrites.
  - Never hand-edit generated platform files.
- **Test Scenarios**:
  - Happy path: all native platforms contain the same recursive reference set.
  - Edge case: Markdown links from nested references resolve within the bundle;
    external literature links remain external.
  - Error path: stale or orphaned generated files are detected by drift tests.
- **Tests**:
  - `python scripts/cg_generate_targets.py --all`
  - `python -m pytest scripts/tests/test_target_packaging.py scripts/tests/test_target_closure.py scripts/tests/test_target_determinism.py scripts/tests/test_target_drift.py -q`
  - `python -m pytest scripts/tests/test_target_documentation.py -q`
- **Acceptance criteria**:
  - Canonical and generated bundles have exact recursive inventory parity,
    deterministic content, valid local links, and no orphaned outputs.

### 12. Run context-budget, methodological, and full regression gates

- **Requirements**: R2, R15, R18, R19, R20, R21, R22
- **Files**:
  - `scripts/cg_audit_context.py` (only if a narrowly scoped audit assertion
    is required; no analyzer rewrite by default)
  - `.cg-docs/cost/` generated audit artifacts if the repository workflow
    requires refreshed evidence
  - `.cg-docs/work-reports/` execution evidence created by `/cg-work`
- **Details**:
  - Run the context audit with recommendations and inspect the before/after
    ML-skill rows. Confirm the activated core is below the local skill threshold,
    references are not counted as default activated skill content, and no
    unintended always-on burden or broad routing was introduced.
  - Run the representative evaluation fixture and review every failure as a
    content/routing defect, not as a reason to weaken the test.
  - Validate frontmatter and local references, then run the complete canonical
    test runner once at the end using the repository's Pester safety rules.
  - Record commands, dates, results, remaining uncertainty, and any accepted
    exception in the execution report; do not mark completion from static
    inspection alone.
- **Test Scenarios**:
  - Happy path: audit has no new failure and reviewed warnings are understood;
    all Python and Pester tests pass.
  - Edge case: audit warnings remain for intentional reference count or generated
    bundle size; classify and document them rather than hiding them.
  - Error path: a required test or audit fails; stop completion and repair the
    same slice before widening scope.
- **Tests**:
  - `python -m pytest scripts/tests/test_cr_ml_skill.py scripts/tests/test_cr_baseline.py scripts/tests/test_yaml_frontmatter_lint.py -q`
  - `python scripts/cg_audit_context.py --root . --format both --recommendations`
  - Full safe runner: `tests/Run-Tests.ps1`, with results read from
    `tests/last-run.json`.
- **Acceptance criteria**:
  - All required evidence rows pass, the context impact is understood, and the
    repository regression gate is green.

## Testing Strategy

### Content and structure

- Use stdlib-only Python tests for frontmatter, reference inventory, local link
  closure, route coverage, distinct reference roles, and required methodological
  terms.
- Keep fixture-driven assertions independent and targeted. Do not validate the
  skill by checking only that a large keyword blob exists.
- Use existing generic frontmatter, baseline, target-packaging, target-closure,
  target-determinism, target-drift, and documentation contracts as regression
  gates.

### Methodological review

- Verify ESL terminology and claims against the canonical second-edition source
  and cited econometric literature without reproducing copyrighted prose.
- Review high-dimensional inference, DML, cross-fitting, honest forests,
  selection/inference distinctions, metrics, and split designs for unstated
  assumptions.
- Specifically audit survey language for the difference between weighted loss,
  target population, estimator support, clustering/stratification, and design
  variance.
- Confirm predictive importance, regularized coefficients, and OOS performance
  are not presented as causal evidence without an identification strategy.

### Context and packaging

- Compare pre/post `cg_audit_context.py` output for the core skill, reference
  counts, high-frequency prompt/agent rows, and reviewed warnings.
- Generate all native trees from canonical sources and run recursive parity,
  closure, determinism, and drift tests.
- Do not execute bundled examples or install R/Python ML packages solely to test
  Markdown guidance.

### Final regression

- Run focused Python tests after each implementation phase.
- Run the canonical full Pester runner once after all content, routing,
  documentation, and generated-target changes are complete; inspect
  `tests/last-run.json` rather than flooding the session with raw output.

## Documentation Checklist

- [ ] Core skill description states what it does and when it activates.
- [ ] Public skills catalog describes CR ML as one skill with eight references,
      not nine separate skills.
- [ ] `docs/reference.md` retains the ML method-pack entry and points users to
      the public catalog.
- [ ] Each reference identifies its intended audience/task and literature scope.
- [ ] Specialized package examples state version-sensitive or engine-specific
      boundaries.
- [ ] Survey-weight language distinguishes observation weights from full survey
      design and variance handling.
- [ ] Generated platform trees are regenerated from canonical `.github` sources.

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Core router remains too large | Context burden and poor retrieval | Enforce the line/token test; move explanation to references; retain only triage and non-negotiable safeguards inline. |
| Eight references become an unmaintainable textbook | Stale or contradictory guidance | Give each file a narrow retrieval role, use literature pointers, and add representative-task evaluations. |
| Routing loads too little context | Incomplete or unsafe answers | Fixture-driven expected-reference sets cover combined tasks; make high-risk safeguards explicit in the core. |
| Routing loads too much context | Token waste and lower signal | Require one/two-reference default routing and compare context-audit output before and after. |
| ESL theory is flattened into package recipes | Weak econometric reasoning | Put notation, loss, risk, assumptions, and method comparison before implementation examples. |
| Survey weights are overclaimed | Incorrect population inference or false assurance | Distinguish target-population loss, estimator support, complex-design variance, clustering, and stratification. |
| DML/cross-fitting is treated as magic identification | Invalid causal inference | Require estimand, identification, overlap, nuisance, fold, and dependence checks. |
| Native targets drift | Platform users receive stale or incomplete references | Regenerate atomically and run recursive packaging, closure, determinism, and drift tests. |
| Documentation and test contracts are incomplete | Future changes silently regress | Update public catalog and add fixture/content/inventory tests tied to each requirement. |
| Package APIs become stale | Misleading implementation guidance | Keep specialized adapters bounded, version-conscious, and subordinate to method logic. |

## Out of Scope

- Computer vision, NLP, reinforcement learning, and production MLOps/deployment.
- A new family of independently triggered CR ML skills.
- Changes to `.github/shared/module-registry.json` or suite ownership.
- New runtime dependencies for this repository.
- Rewriting unrelated CR skills, prompts, or review agents.
- Executing R/Python ML examples as part of Markdown-content tests.
- Full deep-learning, Bayesian deep-learning, or neural-network implementation
  guidance; only bounded method-selection coverage is included.
- Treating this skill as a substitute for study-specific identification,
  survey-design, or research-integrity review.

## Completion Contract

### Outcome

The CR ML capability is a compact, ESL-led routing skill with eight focused,
demand-loaded references covering statistical-learning foundations,
high-dimensional methods, splitting/resampling/evaluation, ensembles,
econometric causal ML, survey/panel data, and R/Python implementation.
`/cr-work` and `@cr-ml-methodology` load relevant material conditionally,
documentation describes the structure, and all generated platform bundles match
the canonical skill recursively.

### Verification Surface

| ID | Phase | Evidence Required | Command/Artifact | Required |
|----|-------|-------------------|------------------|----------|
| V1 | 1 | Core router contains modeling triage, prediction/causal boundary, reference map, and selective-loading rule; core remains within local size target. | `python -m pytest scripts/tests/test_cr_ml_skill.py -q` | yes |
| V2 | 1 | ESL foundations and high-dimensional references contain required theory, notation, method comparisons, econometric cautions, and literature pointers. | `scripts/tests/test_cr_ml_skill.py` content assertions | yes |
| V3 | 2 | Splitting/evaluation, tree/ensemble, causal-ML, and survey/panel references cover required structures, diagnostics, and interpretation limits. | `scripts/tests/test_cr_ml_skill.py` content assertions | yes |
| V4 | 3 | R and Python implementation references use agreed default stacks and document specialized-package boundaries, preprocessing, weights, seeds, and evaluation. | `scripts/tests/test_cr_ml_skill.py` content assertions | yes |
| V5 | 4 | `/cr-work` conditionally loads ML material for ML/Prediction and ML implementation; the review agent routes to relevant references and applies revised survey-weight logic. | `scripts/tests/test_cr_ml_skill.py` and CR baseline tests | yes |
| V6 | 4 | Representative routing matrix covers iid prediction, high-dimensional selection, panel/clustered data, survey-weighted prediction, DML, and review/leakage tasks. | `scripts/tests/fixtures/cr_ml_skill_evaluation.json` plus executable fixture test | yes |
| V7 | 4 | Every canonical ML reference is present in all generated skill bundles with exact recursive file parity and valid local Markdown closure. | `python scripts/cg_generate_targets.py --all`; target packaging/closure/determinism/drift tests | yes |
| V8 | 4 | Frontmatter and documentation contracts pass, including the public CR skill catalog and generated-target documentation. | `python -m pytest scripts/tests/test_yaml_frontmatter_lint.py scripts/tests/test_target_documentation.py -q` | yes |
| V9 | final | Before/after context audit shows the activated `SKILL.md` is below the local skill threshold and no unintended always-on or high-frequency burden was introduced; recommendations are recorded in the execution report. | `python scripts/cg_audit_context.py --root . --format both --recommendations` | yes |
| V10 | final | Full repository regression passes through the canonical safe runner. | `tests/Run-Tests.ps1` and `tests/last-run.json` with `passed: true` | yes |

### Constraints

| ID | Phase | Constraint | Check |
|----|-------|------------|-------|
| C1 | 1 | Keep `SKILL.md` as a thin router, targeting no more than 120 lines and below the skill review token threshold. | Focused skill test and context audit |
| C2 | 1-4 | Do not ask agents to load all eight references by default; route one or two by task and data structure. | Core routing assertions, fixture test, and audit review |
| C3 | 1-4 | Do not present predictive accuracy, feature importance, regularized coefficients, or DML output as causal without estimand and identification conditions. | Content tests and ML-agent review |
| C4 | 2-4 | Treat survey weights as a target-population/estimator-capability issue; do not imply `sample_weight` alone handles clustering, stratification, variance estimation, or representativeness. | Survey reference and agent assertions |
| C5 | 3 | Use R `tidymodels` and Python `scikit-learn` as defaults; do not add runtime dependencies merely to document specialized packages. | Reference content and dependency diff check |
| C6 | 4 | Edit canonical `.github` sources only; generate native mirrors with the existing generator. | Target packaging, closure, determinism, and drift tests |
| C7 | 1-4 | Preserve CR frontmatter, lifecycle/integrity behavior, module ownership, and unrelated user changes. | Baseline, module, and full-suite tests |

### Boundaries

- Allowed: the canonical ML skill, its eight references, the ML review agent,
  the ML conditional route in `/cr-work`, focused CR documentation, focused
  tests/fixtures, generated native ML bundles, and context-audit evidence.
- Out of scope: excluded application domains, independently triggered ML skill
  families, module-registry changes, unrelated CR assets, runtime dependency
  installation, and execution of bundled ML examples.

### Iteration Policy

1. Preserve useful current coverage while moving detailed material to the
   reference with the clearest retrieval role.
2. Write and review theory before implementation recipes; distinguish target,
   loss, estimand, assumptions, and assessment throughout.
3. Keep reference routing to one or two files for ordinary tasks; add a second
   file only when the task's data structure or inferential goal requires it.
4. If an API is uncertain, state the conceptual contract and verify against
   official package documentation before adding syntax.
5. If a test or generated parity check fails, repair the canonical source or
   routing contract and rerun the same focused check before widening scope.
6. Under `deviation-policy: ask`, pause before changing scope, dependencies,
   module ownership, reference taxonomy, or test evidence requirements; record
   the decision in the execution report.

### Blocked-Stop Conditions

- A required methodological claim cannot be verified against cited literature
  or official package documentation.
- The core cannot meet the context target without removing a research-integrity
  or safety rule.
- A reference path, Markdown link, generated bundle, native target closure, or
  documentation contract fails.
- The revised survey-weight policy cannot be expressed without contradicting the
  charter or actual package capabilities.
- Required Python tests, the canonical safe Pester runner, or the context audit
  cannot run.
- A required test fails after local repair attempts.
- Completion would require a module-registry change, new runtime dependency,
  generated-tree hand edit, or out-of-scope domain without approval.
- Completion evidence would rely only on static inspection rather than an
  executed check or approved exception.
