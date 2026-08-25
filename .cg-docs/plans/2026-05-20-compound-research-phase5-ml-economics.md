---
date: 2026-05-20
title: "Compound Research — Phase 5: ML in Economics"
status: complete
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-05-13-compound-research-extension.md"
language: "Markdown, PowerShell"
estimated-effort: "large"
tags: [compound-research, skills, ml-economics, machine-learning, agents,
  specification-analysis, cr-ml-methodology, phase5]
phases: 2
---

# Plan: Compound Research — Phase 5: ML in Economics

## Objective

Create the ML domain-knowledge skill and two new research agents that give the
research module ML/Prediction and Specification Analysis capabilities. After
this phase, `/cr-brainstorm` and `/cr-work` can load concrete skill content
for ML/Prediction and Implementation (ML) task types, and `/cr-review` can
dispatch `@cr-ml-methodology` and `@cr-specification-analysis` — replacing
the current "Phase 5, not yet available" placeholders.

## Context

Phase 4 (completed 2026-05-15) created six domain-knowledge skills and two
instruction files for structural econometrics. Phase 5 adds the ML complement:
one skill (`cr-skill-ml-economics`) plus two agents (`@cr-ml-methodology`,
`@cr-specification-analysis`). The agents are already referenced with "Phase 5"
placeholders in `cr-review.prompt.md` (lines 77, 81, 94–95, 99) and
`cr-brainstorm.prompt.md` (line 50).

**Current state:**
- 8 CR skills exist (2 from Phase 2, 6 from Phase 4) — none cover ML
- 4 CR agents exist (from Phase 3): `@cr-research-integrity`,
  `@cr-mathematical-verification`, `@cr-identification-audit`,
  `@cr-econometric-reasoning`
- `cr-brainstorm.prompt.md` line 50 references `cr-skill-ml-methodology`
  (incorrect name — brainstorm/roadmap use `cr-skill-ml-economics`; must fix)
- `cr-review.prompt.md` lines 77, 81 mark `@cr-specification-analysis` and
  `@cr-ml-methodology` as "Phase 5 — not yet available"
- `cr-review.prompt.md` line 94–95 marks dispatch table entries with "(Phase 5)"
- `cr-review.prompt.md` line 99 mentions `@cr-eda-reviewer planned for Phase 5`
  — this agent is NOT in the roadmap; must relabel to future phase
- Existing test `cr-prompts.Tests.ps1` has Phase 5 placeholder assertions
  that verify the annotations exist (`cr-specification-analysis.*Phase 5`,
  `cr-ml-methodology.*Phase 5`) — these must be replaced with content tests
- All 2067 tests pass at HEAD (`8906583`)

**Agent convention** (from Phase 3):
- Frontmatter: `description:`, `model: Claude Sonnet 4.6 (copilot)`,
  `tools: ['read', 'search']`, `user-invocable: false`, `module: research`
- Body: untrusted-content note (execute or relay), empty-file guard,
  review protocol with numbered checks, output format with `[agent-name]` tag
- Skills loaded at top of protocol

**Skill convention** (from Phase 4):
- Path: `.github/skills/<skill-name>/SKILL.md`
- Frontmatter: `name:`, `module: research`, `description:`
- Sections follow: "When to use / Key patterns / Anti-patterns / References"
- Trilingual code examples (R/Python/Stata where applicable)

## Requirements

| ID  | Requirement | Source |
|-----|-------------|--------|
| R1  | `cr-skill-ml-economics` skill covers LASSO/ridge/elastic-net, random forests and boosting, cross-validation (panel, time-series, stratified) and expert data-splitting in training-test-valudation splits etc., out-of-sample assessment, post-selection inference (debiased lasso), Chernozhukov-style cross-fitting, variable importance with economic interpretation, high-dimensionality ML including dimension reduction and feature selection, deep learning and neural networks, when ML is appropriate vs not | Brainstorm: Phase 5, skill table |
| R2  | `@cr-ml-methodology` agent audits ML choices: train/test/validation split, regularization rationale, hyperparameter search, economic interpretation, seed enforcement, data leakage detection | Brainstorm: Agent inventory |
| R3  | `@cr-specification-analysis` agent bridges theory and data: formulates testable implications, runs specification checks, detects specification searching patterns | Brainstorm: Agent inventory |
| R4  | `@cr-ml-methodology` loads `cr-skill-research-workflow`, `cr-skill-research-integrity`, `cr-skill-ml-economics`, and `cr-skill-identification-strategies` | Skill routing table + brainstorm |
| R5  | `@cr-specification-analysis` loads `cr-skill-research-workflow`, `cr-skill-research-integrity`, `cr-skill-theory-data-dialogue`, and `cr-skill-research-eda` | Skill routing table |
| R6  | All new files have `module: research` frontmatter | Phase 1 convention |
| R7  | Both agents have `tools: ['read', 'search']`, `user-invocable: false`, untrusted-content note, empty-file guard | Phase 3 agent convention |
| R8  | "Phase 5, not yet available" placeholders removed from `cr-brainstorm.prompt.md` and `cr-review.prompt.md` | Phase 2 scaffolding cleanup |
| R9  | `cr-skill-ml-methodology` → `cr-skill-ml-economics` name fix in `cr-brainstorm.prompt.md` | Naming discrepancy |
| R10 | `@cr-eda-reviewer planned for Phase 5` relabeled to future phase in `cr-review.prompt.md` | Roadmap alignment |
| R11 | `cr-prompts.Tests.ps1` extended with content tests for skill and both agents | Testing convention |
| R12 | Phase 5 placeholder assertions in tests replaced with content assertions | Test maintenance |
| R13 | `prompt-tools.Tests.ps1` module frontmatter validation passes for all new files (automatic — existing test) | Backward compatibility |
| R14 | All existing tests continue to pass | Backward compatibility |
| R15 | `docs/reference.md` updated with entries for `cr-skill-ml-economics`, `@cr-ml-methodology`, `@cr-specification-analysis` | Phase 4 convention (plan review P2.2) |
| R16 | `copilot-instructions.md` updated with `<skill>` entry for `cr-skill-ml-economics` | Plan review P2.3 |

## Implementation Steps

## Phase 1: Core skill and agents

### 1. Create `cr-skill-ml-economics/SKILL.md`

- **Requirements**: R1, R6
- **Files**: `.github/skills/cr-skill-ml-economics/SKILL.md`
- **Details**:
  The ML domain knowledge skill. Covers ML methods as applied in economics
  research — distinct from generic ML tutorials. Emphasis on when ML is the
  right tool, what diagnostics are required, and how to interpret results
  economically.

  **Frontmatter**:
  ```yaml
  ---
  name: cr-skill-ml-economics
  module: research
  description: "Machine learning methods for economics research. Covers
    LASSO/ridge/elastic-net for high-dimensional economics, random forests
    and boosting for prediction, cross-validation done right (panel CV,
    time-series CV, stratified CV by group), out-of-sample assessment,
    post-selection inference (debiased lasso), Chernozhukov-style
    cross-fitting, variable importance with economic interpretation, and
    when ML is appropriate vs when it is not. Loaded by @cr-ml-methodology
    for ML/Prediction and Implementation (ML) tasks."
  ---
  ```

  **Sections to include**:
  1. When ML Is (and Isn't) Appropriate in Economics — prediction vs causal
     inference boundary; ML for prediction ≠ ML for causal estimation;
     Athey & Imbens (2019) guidance; supervised ML for heterogeneous treatment
     effects vs prediction tasks
  2. Penalized Regression (LASSO/Ridge/Elastic Net) — objective functions,
     penalty selection via CV, interpretation in economics (variable selection
     vs shrinkage), post-LASSO OLS, rigorous LASSO (Belloni, Chernozhukov,
     Hansen), double selection for inference
  3. Tree-Based Methods — random forests, gradient boosting (XGBoost,
     LightGBM), bagging; when useful in economics (prediction, heterogeneity
     detection); partial dependence plots; Shapley values for interpretation;
     honest estimation (causal forests — Athey, Tibshirani, Wager)
  4. Cross-Validation Done Right — k-fold CV for i.i.d. data; panel/clustered
     CV (leave-one-group-out, rolling-origin for time series); stratified CV
     by treatment status; why naive k-fold fails with panel data; information
     leakage through cross-validation
  5. Out-of-Sample Assessment — RMSE, MAE, R² out-of-sample; proper holdout
     procedures; test-set contamination detection; Diebold-Mariano test for
     model comparison
  6. Post-Selection Inference — debiased/desparsified LASSO (van de Geer,
     Bühlmann, Ritov, Dezeure); double/debiased ML (Chernozhukov et al. 2018);
     cross-fitting procedure; Neyman orthogonality; inference after model
     selection (selective inference)
  7. Variable Importance and Economic Interpretation — permutation importance,
     SHAP, partial dependence; why coefficient interpretation differs from
     importance; economic meaning of feature selection; connecting ML features
     to economic theory
  8. Hyperparameter Tuning — grid search, random search, Bayesian optimization;
     nested cross-validation (inner for tuning, outer for assessment); tuning
     as a source of specification searching (P0 if unreported)
  9. Reproducibility Requirements — seed lists for all random components
     (train/test split, CV folds, bootstrap, random forests, stochastic
     gradient descent); version pinning for ML libraries; hardware
     reproducibility issues (GPU vs CPU)
  10. Anti-Patterns — treating ML as causal without adjustment, unreported
      hyperparameter search, data leakage through preprocessing, using
      in-sample fit for model selection, interpreting penalized coefficients
      as OLS coefficients, ignoring clustering in CV

  Each section follows the pattern:
  ```
  ## Section Title
  **When to use**: ...
  **Key patterns** (R/Python):
  - Pattern with code example
  **Anti-patterns**:
  - What NOT to do and why
  **References**: key papers
  ```

  Trilingual where applicable — R (glmnet, ranger, tidymodels) and Python
  (scikit-learn, xgboost, lightgbm). Stata has limited ML support; note
  `lasso2`, `cvlasso`, and community packages where available but flag
  R/Python as preferred for serious ML work.

- **Test Scenarios**:
  - ✅ SKILL.md exists with valid frontmatter
  - ✅ Has `module: research`, `name: cr-skill-ml-economics`
  - ✅ Contains LASSO/penalized regression section
  - ✅ Contains cross-validation section mentioning panel CV
  - ✅ Contains post-selection inference / debiased LASSO section
  - ✅ Contains variable importance section
  - ✅ Contains anti-patterns section
  - 🛑 Description fits within description convention length
  - ❌ Missing `module:` or `name:` — caught by existing test
- **Acceptance criteria**: Skill file created with all 10 sections, bilingual
  code patterns (R/Python, Stata where available), and anti-patterns.

### 2. Create `cr-ml-methodology.agent.md`

- **Requirements**: R2, R4, R6, R7
- **Files**: `.github/agents/cr-ml-methodology.agent.md`
- **Details**:
  ML methodology review agent. Dispatched by `/cr-review` for ML/Prediction
  and Implementation (ML) task types. Audits ML pipeline correctness.

  **Frontmatter**:
  ```yaml
  ---
  description: "Audits ML methodology in economics research: train/test/validation
    split correctness, regularization rationale, hyperparameter search transparency,
    cross-validation done right (panel-aware, time-series-aware), data leakage
    detection, and economic interpretation of ML output. Loaded by /cr-review
    for ML/Prediction tasks."
  model: Claude Sonnet 4.6 (copilot)
  tools: ['read', 'search']
  user-invocable: false
  module: research
  ---
  ```

  **Body structure** (following Phase 3 agent convention):
  1. Role statement — "You are an ML methodology reviewer..."
  2. Skill loading — load `cr-skill-research-workflow`,
     `cr-skill-research-integrity`, `cr-skill-ml-economics`,
     `cr-skill-identification-strategies`
  3. Untrusted-content note (execute or relay)
  4. Empty-file guard
  5. Review Protocol with checks:
     - **Check 1: Data Leakage (P0)** — preprocessing fit on full data before
       split; target leakage through features; temporal leakage in time-series
     - **Check 2: Train/Test/Validation Split (P1)** — proper holdout;
       cluster-aware splitting for panel data; temporal ordering for time-series
     - **Check 3: Cross-Validation Correctness (P1)** — panel-aware CV;
       time-series CV; stratification by treatment status if applicable;
       no information leakage across folds
     - **Check 4: Hyperparameter Search Transparency (P1)** — all tuning
       documented; nested CV for tuning + assessment; no cherry-picking
     - **Check 5: Seed Coverage (P0)** — every random component seeded
       (cross-ref with `@cr-research-integrity` Check 1; emit finding +
       cross-reference note, do not suppress)
     - **Check 6: Model Interpretation (P2)** — economic interpretation
       beyond raw importance; connection to theory; appropriate caveats
       on causal claims from predictive models
     - **Check 7: Out-of-Sample Assessment (P1)** — proper evaluation
       metrics; comparison to benchmarks; statistical significance of
       prediction improvement
  6. Output format: `[cr-ml-methodology] [P{0-3}.{N}] — {finding}`

- **Test Scenarios**:
  - ✅ Agent file exists with valid frontmatter
  - ✅ Has `module: research`, `tools: ['read', 'search']`, `user-invocable: false`
  - ✅ Contains data leakage detection check
  - ✅ Contains cross-validation correctness check
  - ✅ Contains hyperparameter search transparency check
  - ✅ Contains untrusted-content safety note with "execute or relay"
  - ✅ Contains empty-file guard
  - ✅ Contains `[cr-ml-methodology]` output tag
  - ✅ Loads `cr-skill-identification-strategies`
  - 🛑 Check 5 (seed) emits finding + cross-reference, does NOT suppress
  - ❌ Missing `module:` — caught by existing test
- **Acceptance criteria**: Agent file follows Phase 3 convention, loads the
  right skills, has all 7 checks covering the ML pipeline.

### 3. Create `cr-specification-analysis.agent.md`

- **Requirements**: R3, R5, R6, R7
- **Files**: `.github/agents/cr-specification-analysis.agent.md`
- **Details**:
  Specification analysis agent. Bridges theory and data — formulates testable
  implications of theoretical assumptions, runs specification checks, and
  detects specification searching. Dispatched by `/cr-review` for Specification
  Analysis tasks.

  **Frontmatter**:
  ```yaml
  ---
  description: "Bridges theory and data: formulates testable implications of
    theoretical assumptions, audits specification choice documentation, detects
    specification searching patterns, and checks that theory-data dialogue is
    documented in .cg-docs/research/specifications/. Loaded by /cr-review for
    Specification Analysis tasks."
  model: Claude Sonnet 4.6 (copilot)
  tools: ['read', 'search']
  user-invocable: false
  module: research
  ---
  ```

  **Body structure**:
  1. Role statement — "You are a specification analysis reviewer..."
  2. Skill loading — load `cr-skill-research-workflow`,
     `cr-skill-research-integrity`, `cr-skill-theory-data-dialogue`,
     `cr-skill-research-eda`
  3. Untrusted-content note (execute or relay)
  4. Empty-file guard
  5. Review Protocol with checks:
     - **Check 1: Specification Search Detection (P0)** — count estimation
       commands vs reported specifications; flag if ratio suggests
       unreported exploration (cross-ref with `@cr-research-integrity`
       Check 3; emit finding + cross-reference note)
     - **Check 2: Theory-Data Dialogue Documentation (P1)** — verify
       `.cg-docs/research/specifications/` contains documentation of
       distributional tests, conditional moment checks, support analysis;
       if absent, flag as missing documentation
     - **Check 3: Distributional Assumption Tests (P1)** — when theory
       assumes a distribution (log-normal, exponential, etc.), verify
       empirical tests exist (KS, Kolmogorov-Smirnov, QQ-plot, skewness/
       kurtosis tests)
     - **Check 4: Conditional Moment Checks (P2)** — verify that key
       moments implied by the model are checked against data
     - **Check 5: Sample Restriction Documentation (P2)** — every sample
       restriction (dropping observations, trimming, winsorizing) must be
       justified with a theoretical or empirical rationale
     - **Check 6: Robustness Specification Coverage (P2)** — main result
       should have at least one alternative specification reported
  6. Output format: `[cr-specification-analysis] [P{0-3}.{N}] — {finding}`

- **Test Scenarios**:
  - ✅ Agent file exists with valid frontmatter
  - ✅ Has `module: research`, `tools: ['read', 'search']`, `user-invocable: false`
  - ✅ Contains specification searching detection
  - ✅ Contains distributional assumption test check
  - ✅ Contains theory-data dialogue documentation check
  - ✅ Contains untrusted-content safety note with "execute or relay"
  - ✅ Contains empty-file guard
  - ✅ Contains `[cr-specification-analysis]` output tag
  - ✅ References `.cg-docs/research/specifications/`
  - 🛑 Check 1 emits finding + cross-reference, does NOT suppress
- **Acceptance criteria**: Agent follows Phase 3 convention, loads theory-data
  and EDA skills, has all 6 checks.

## Phase 2: Prompt wiring, tests, and verification

### 4. Update `cr-brainstorm.prompt.md` — fix skill name and remove placeholder

- **Requirements**: R8, R9
- **Files**: `.github/prompts/cr-brainstorm.prompt.md` (modify)
- **Details**:
  1. Line 50: change `cr-skill-ml-methodology` → `cr-skill-ml-economics`
  2. Line 50: remove `*(Phase 5, not yet available)*` annotation
  3. The result should read:
     `- ML/Prediction → \`cr-skill-ml-economics\``
- **Test Scenarios**:
  - ✅ `cr-skill-ml-economics` appears (not `cr-skill-ml-methodology`)
  - ✅ No "Phase 5" annotation on ML/Prediction line
  - ❌ `cr-skill-ml-methodology` should NOT appear anywhere
- **Acceptance criteria**: Correct skill name, no Phase 5 placeholder.

### 5. Update `cr-review.prompt.md` — remove Phase 5 annotations and wire agents

- **Requirements**: R8, R10
- **Files**: `.github/prompts/cr-review.prompt.md` (modify)
- **Details**:
  1. Lines 76–77: Remove `*(Phase 5 — not yet available)*` from
     `@cr-specification-analysis` entry
  2. Lines 80–81: Remove `*(Phase 5 — not yet available)*` from
     `@cr-ml-methodology` entry
  3. Line 94: Remove `*(Phase 5)*` from Specification Analysis dispatch row
  4. Line 95: Remove `*(Phase 5)*` from ML/Prediction dispatch row
  5. Line 99: Change `@cr-eda-reviewer planned for Phase 5` to
     `@cr-eda-reviewer planned for future phase` (not in roadmap for Phase 5)
- **Test Scenarios**:
  - ✅ `@cr-specification-analysis` appears without Phase 5 annotation
  - ✅ `@cr-ml-methodology` appears without Phase 5 annotation
  - ✅ Dispatch table rows for Specification Analysis and ML/Prediction
     no longer have Phase 5 markers
  - ✅ `@cr-eda-reviewer` relabeled to future phase
  - 🛑 Phase 6 and Phase 7 annotations still present for other agents
- **Acceptance criteria**: All Phase 5 placeholders removed; Phase 6/7
  markers untouched.

### 6. Extend `cr-prompts.Tests.ps1`

- **Requirements**: R11, R12, R14
- **Files**: `tests/cr-prompts.Tests.ps1` (modify)
- **Details**:
  Add test blocks for:
  1. **Phase 5 skill — existence and frontmatter** (same pattern as Phase 4
     skills block): `cr-skill-ml-economics` existence, `module: research`,
     `name:`, `description:`
  2. **cr-skill-ml-economics content tests**: LASSO/penalized regression,
     cross-validation, post-selection inference, debiased LASSO, variable
     importance, anti-patterns
  3. **CR agent structural checks** — extend the existing `$crAgents` array
     to include `cr-ml-methodology.agent.md` and
     `cr-specification-analysis.agent.md`
  4. **cr-ml-methodology.agent.md content tests**: data leakage, cross-
     validation correctness, hyperparameter search, untrusted-content note,
     empty-file guard, `[cr-ml-methodology]` output tag
  5. **cr-specification-analysis.agent.md content tests**: specification
     searching, distributional assumption, theory-data dialogue, untrusted-
     content note, empty-file guard, `[cr-specification-analysis]` output tag,
     `.cg-docs/research/specifications/` reference
  6. **Phase 5 wiring tests** — replace existing Phase 5 placeholder
     assertions:
     - REMOVE: `"still contains Phase 5 annotation for @cr-specification-analysis"` →
       REPLACE with `"does NOT contain Phase 5 annotation on @cr-specification-analysis"`
     - REMOVE: `"still contains Phase 5 annotation for @cr-ml-methodology"` →
       REPLACE with `"does NOT contain Phase 5 annotation on @cr-ml-methodology"`
     - ADD: `@cr-ml-methodology` appears in ML/Prediction dispatch row
       without Phase marker
     - ADD: `@cr-specification-analysis` appears in Specification Analysis
       dispatch row without Phase marker
  7. **cr-brainstorm.prompt.md naming and annotation tests**:
     - `cr-skill-ml-economics` appears (not `cr-skill-ml-methodology`)
     - `*(Phase 5, not yet available)*` does NOT appear:
       `($content -match '(?i)phase 5.*not yet available') | Should -Be $false`
  8. **@cr-eda-reviewer relabeling test**: `@cr-eda-reviewer` does not appear
     alongside "Phase 5" in `cr-review.prompt.md`:
     `($content -match 'cr-eda-reviewer.*Phase 5') | Should -Be $false`

  Follow existing Pester patterns: hoist `Get-Content` and `Get-Frontmatter`
  calls to `Context`/`Describe` scope (not per-`It`).

- **Test Scenarios**:
  - ✅ New tests pass against newly created files
  - ✅ Existing tests not broken
  - 🛑 Phase 5 placeholder tests correctly replaced (not just added)
  - ❌ Duplicate test names — verify uniqueness
- **Acceptance criteria**: All new content has regression tests; Phase 5
  placeholder assertions removed and replaced with content assertions.

### 7. Run full test suite and verify

- **Requirements**: R13, R14
- **Files**: none (verification only)
- **Details**:
  Run `. tests/Run-Tests.ps1` via `execution_subagent` and verify all tests
  pass, including the new ones and the existing 2067.
- **Acceptance criteria**: All tests pass. Zero failures.

## Testing Strategy

- **Structural tests** (existing `prompt-tools.Tests.ps1`): automatically
  validates `module: research` frontmatter on all new files
- **Content tests** (extended `cr-prompts.Tests.ps1`): validates key sections
  exist in skill, agent checks are present, output tags correct
- **Wiring tests**: Phase 5 placeholders removed, dispatch table correct
- **Backward compatibility**: all existing 2067 tests continue to pass

### 8. Update `docs/reference.md` with new entries

- **Requirements**: R15
- **Files**: `docs/reference.md` (modify)
- **Details**:
  Add entries to the Skills table and Agents table in `docs/reference.md`:
  - `cr-skill-ml-economics` — with description and "Loaded by @cr-ml-methodology"
  - `@cr-ml-methodology` — with description and "Loaded by /cr-review for ML/Prediction tasks"
  - `@cr-specification-analysis` — with description and "Loaded by /cr-review for Specification Analysis tasks"
- **Acceptance criteria**: All three artifacts discoverable in reference docs.

### 9. Update `copilot-instructions.md` with skill entry

- **Requirements**: R16
- **Files**: `.github/copilot-instructions.md` (modify)
- **Details**:
  Add a `<skill>` entry for `cr-skill-ml-economics` in the `<skills>` section,
  following the same pattern as the Phase 4 entries.
- **Acceptance criteria**: `cr-skill-ml-economics` appears in the skills catalog.

## Documentation Checklist

- [ ] Skill SKILL.md has complete section structure with code patterns
- [ ] Agent files have review protocol documentation
- [ ] `docs/reference.md` updated with all new artifacts
- [ ] `copilot-instructions.md` updated with skill entry

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Phase 5 placeholder test assertions still pass after removal (stale alternation) | Medium | P1 — false green | Replace assertions entirely (not just add new ones); use negative assertions (`Should -Be $false`) for both `cr-review.prompt.md` and `cr-brainstorm.prompt.md` |
| `cr-skill-ml-methodology` name survives in untested locations | Low | P2 — broken skill loading at runtime | Grep for `cr-skill-ml-methodology` across all `.md` files after step 4; fix any remaining references |
| `@cr-eda-reviewer` relabeling confuses future planning | Low | P3 — cosmetic | Use "future phase" (not a specific number) to avoid premature commitment; add negative test for "Phase 5" |
| Agent Check 5 (seed enforcement) in `@cr-ml-methodology` contradicts global deferral policy | Medium | P0 — suppressed finding | Follow context convention: emit finding + cross-reference note to `@cr-research-integrity`, never suppress |

## Out of Scope

- `@cr-eda-reviewer` agent — mentioned in `cr-review.prompt.md` but not in the
  Phase 5 roadmap feature; deferred to a future phase
- Causal ML methods (double ML, causal forests, DR-Learner) — explicitly out of
  scope per brainstorm ("its own future module")
- ML-specific instruction files (no `ml.instructions.md` — ML code uses existing
  `python.instructions.md` and `r.instructions.md`)
