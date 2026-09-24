---
date: 2026-05-14
title: "Compound Research — Phase 4: Structural Econometrics Skills"
status: completed
completed-date: 2026-05-15
scope: "Deep"
brainstorm: ".cg-docs/brainstorms/2026-05-13-compound-research-extension.md"
language: "Markdown, PowerShell"
estimated-effort: "large"
tags: [compound-research, skills, structural-econometrics, mathematical-derivation,
  symbolic-verification, identification-strategies, theory-data-dialogue,
  research-eda, latex, instructions]
---

# Plan: Compound Research — Phase 4: Structural Econometrics Skills

## Objective

Create the six domain-knowledge skills and two instruction files that give the
research module its econometric depth. After this phase, `/cr-brainstorm` and
`/cr-work` can load concrete skill content for Theory/Modeling, Specification
Analysis, EDA, and Implementation (structural) task types — replacing the
current "Phase 4, not yet available" placeholders in the `/cr-*` prompts.

## Context

Phase 3 (completed 2026-05-14, `.cg-docs/plans/2026-05-14-compound-research-phase3-agents.md`)
created the four core CR agents. Phase 4 provides the domain knowledge those
agents draw on. The agents reference skills like `cr-skill-structural-econometrics`
and `cr-skill-identification-strategies`; the skills must exist for the agents
to produce useful output. Currently the agents only load `cr-skill-research-integrity`
and `cr-skill-research-workflow` — Phase 4 must also update the agents to load
their corresponding new skills.

**Current state:**
- 2 CR skills exist: `cr-skill-research-workflow`, `cr-skill-research-integrity`
- 4 CR agents completed in Phase 3: `@cr-research-integrity`,
  `@cr-mathematical-verification`, `@cr-identification-audit`,
  `@cr-econometric-reasoning` — each currently loads only
  `cr-skill-research-integrity` (or `cr-skill-research-workflow`)
- Prompts have "Phase 4, not yet available" markers in `cr-brainstorm.prompt.md`
  (lines 46–47) and `cr-review.prompt.md` (lines 75, 92)
- 3 instruction files exist: `r.instructions.md`, `python.instructions.md`,
  `stata.instructions.md` — all have `module:` frontmatter
- Existing test: `prompt-tools.Tests.ps1` validates `module:` frontmatter on
  all SKILL.md and instruction files
- Existing test: `cr-prompts.Tests.ps1` validates CR skill content

**Skill structure convention** (from existing skills):
- Each skill lives in `.github/skills/<skill-name>/SKILL.md`
- Frontmatter: `name:`, `module:`, `description:` (mandatory)
- Some skills have subdirectories (`workflows/`, `references/`) for linked
  reference documents; most Phase 2 CR skills are flat (SKILL.md only)
- Skills are referenced by name from prompts, agents, and `copilot-instructions.md`

**Instruction file convention** (from existing):
- Lives in `.github/instructions/<name>.instructions.md`
- Frontmatter: `applyTo:`, `module:` (mandatory)
- Triggered automatically when matching files are open

## Requirements

| ID  | Requirement | Source |
|-----|-------------|--------|
| R1  | `cr-skill-structural-econometrics` skill covers discrete choice, DP, simulation-based estimation (MSM, SMM, indirect inference), MLE, GMM, moment selection, SE variants, identification | Brainstorm: Phase 4 |
| R2  | `cr-skill-mathematical-derivation` skill covers LaTeX conventions, notation discipline, FOC derivation patterns, code-to-math variable mapping | Brainstorm: Phase 4 |
| R3  | `cr-skill-symbolic-verification` skill covers SymPy patterns, gradient/Hessian verification, code-against-derivation audit | Brainstorm: Phase 4 |
| R4  | `cr-skill-identification-strategies` skill covers IV, RDD, DiD, event studies, synthetic control, matching/IPW with required diagnostics per strategy | Brainstorm: Phase 4 |
| R5  | `cr-skill-theory-data-dialogue` skill covers translating theoretical assumptions into empirical checks, documentation trail | Brainstorm: Phase 4 |
| R6  | `cr-skill-research-eda` skill covers research-question-framed EDA, distinct from generic engineering EDA | Brainstorm: Phase 4 |
| R7  | `latex.instructions.md` applies to `**/*.tex,**/*.Rnw` with LaTeX/math conventions | Brainstorm: File layout |
| R8  | `math.instructions.md` applies to math derivation files in `.cg-docs/research/derivations/` | Brainstorm: File layout |
| R9  | All skills have `module: research` and valid `name:`, `description:` frontmatter | Phase 1 convention |
| R10 | All instruction files have `module: research` and valid `applyTo:` frontmatter | Phase 1 convention |
| R11 | "Phase 4, not yet available" placeholders removed from `cr-brainstorm.prompt.md` and `cr-review.prompt.md` | Phase 2 scaffolding cleanup |
| R12 | `cr-prompts.Tests.ps1` extended with content tests for all 6 new skills | Testing convention |
| R13 | `prompt-tools.Tests.ps1` module frontmatter validation passes for all new files (automatic — existing test covers new files) | Backward compatibility |
| R14 | `copilot-instructions.md` in this repo updated if needed (skills are auto-discovered, so likely no change) | Template convention |
| R15 | All existing 1941 tests continue to pass | Backward compatibility |
| R16 | CR agents updated to load their corresponding Phase 4 skills (`@cr-mathematical-verification` → `cr-skill-symbolic-verification` + `cr-skill-mathematical-derivation`; `@cr-identification-audit` → `cr-skill-identification-strategies`; `@cr-econometric-reasoning` → `cr-skill-structural-econometrics`) | Plan review P1.1 |
| R17 | `cr-skill-specification-analysis` reference removed from `cr-brainstorm.prompt.md` (stale name — never created) | Plan review P1.3 |
| R18 | `@cr-specification-analysis` marker in `cr-review.prompt.md` relabeled from "Phase 4" to "Phase 5" | Plan review P1.2 |

## Implementation Steps

### 1. Create `cr-skill-structural-econometrics/SKILL.md`
- **Requirements**: R1, R9
- **Files**: `.github/skills/cr-skill-structural-econometrics/SKILL.md`
- **Details**:
  The most substantial skill in this phase. Covers the full spectrum of
  structural econometric methods used in economics research.

  **Frontmatter**:
  ```yaml
  ---
  name: cr-skill-structural-econometrics
  module: research
  description: "Structural econometric methods for economics research. Covers
    discrete choice (logit, probit, nested logit, mixed logit, BLP), dynamic
    programming (Rust, Hotz-Miller CCP), simulation-based estimation (MSM, SMM,
    indirect inference), MLE for structural models, GMM (moment selection,
    overidentification, Hansen J-test), standard error variants (sandwich, bootstrap,
    delta method), identification at infinity, exclusion restrictions, and parametric
    vs semi-parametric trade-offs. Loaded by @cr-econometric-reasoning and /cr-work
    for Theory/Modeling and Implementation tasks."
  ---
  ```

  **Sections to include**:
  1. Discrete Choice Models — logit, probit, nested logit, mixed logit/BLP,
     conditional logit, multinomial; IIA tests; random coefficients
  2. Dynamic Programming — Bellman equation setup, Rust (1987) NFXP,
     Hotz-Miller CCP, forward simulation, discount factor identification
  3. Simulation-Based Estimation — MSM, SMM, indirect inference; simulator
     requirements (differentiability, number of simulations); bias-correction
  4. Maximum Likelihood — likelihood construction, score function, information
     matrix, numerical optimization (Newton-Raphson, BFGS); starting values;
     convergence diagnostics
  5. GMM — moment conditions, optimal weighting matrix, two-step GMM,
     overidentification test (Hansen J), moment selection criteria, continuous
     updating
  6. Standard Errors — analytical (sandwich/Huber-White), bootstrap (parametric,
     nonparametric, wild), delta method, cluster-robust; when each is appropriate
  7. Identification — formal identification analysis, identification at infinity,
     exclusion restrictions, order/rank conditions for IV, local vs. global
  8. Anti-Patterns — common mistakes in structural estimation

  Each section follows the pattern:
  ```
  ## Section Title
  **When to use**: ...
  **Key patterns** (R/Python/Stata):
  - Pattern with code example
  **Anti-patterns**:
  - What NOT to do and why
  **References**: key papers/textbooks
  ```

- **Test Scenarios**:
  - ✅ SKILL.md exists with valid frontmatter
  - ✅ Has `module: research`, `name: cr-skill-structural-econometrics`
  - ✅ Contains sections for discrete choice, dynamic programming, GMM, MLE
  - ✅ Contains anti-patterns section
  - 🛑 Description fits within description convention length
  - ❌ Missing `module:` or `name:` — caught by existing test
- **Acceptance criteria**: Skill file created with all 8 sections, trilingual
  code patterns (R/Python/Stata where applicable), and anti-patterns.

### 2. Create `cr-skill-mathematical-derivation/SKILL.md`
- **Requirements**: R2, R9
- **Files**: `.github/skills/cr-skill-mathematical-derivation/SKILL.md`
- **Details**:
  Conventions and patterns for mathematical derivations in research.

  **Frontmatter**:
  ```yaml
  ---
  name: cr-skill-mathematical-derivation
  module: research
  description: "LaTeX and mathematical derivation conventions for economics research.
    Covers notation discipline, numbered equation conventions, FOC derivation patterns,
    envelope theorem applications, integration by parts in expectation, change of
    variables, asymptotic expansions, and cross-referencing code variables to math
    symbols. Loaded for Theory/Modeling and Implementation tasks."
  ---
  ```

  **Sections**:
  1. Notation Discipline — introduce every symbol before use, consistent subscript
     conventions, distinguish random variables from realizations
  2. Equation Conventions — LaTeX `align` environment, equation numbering,
     cross-references; when to use `\label{eq:...}`
  3. FOC Derivation Patterns — standard steps for utility/profit maximization,
     Lagrangian setup, complementary slackness
  4. Common Derivation Techniques — envelope theorem, Leibniz rule, integration
     by parts in expectation, change of variables, implicit function theorem
  5. Asymptotic Expansions — Taylor expansions for delta method, asymptotic
     normality proofs, convergence rate documentation
  6. Code-Math Variable Mapping — table format linking math symbols to code
     variable names; naming conventions that make mapping transparent
  7. Derivation File Organization — `.cg-docs/research/derivations/` layout,
     section conventions (setup → assumptions → derivation → result)
  8. Anti-Patterns — skipping steps, inconsistent notation, undocumented
     simplifications

- **Test Scenarios**:
  - ✅ SKILL.md exists with valid frontmatter
  - ✅ Has `module: research`
  - ✅ Contains notation discipline section
  - ✅ Contains code-math variable mapping section
  - ✅ References `.cg-docs/research/derivations/`
- **Acceptance criteria**: Skill provides complete derivation conventions
  usable by `@cr-mathematical-verification`.

### 3. Create `cr-skill-symbolic-verification/SKILL.md`
- **Requirements**: R3, R9
- **Files**: `.github/skills/cr-skill-symbolic-verification/SKILL.md`
- **Details**:
  Patterns for automated and semi-automated symbolic verification.

  **Frontmatter**:
  ```yaml
  ---
  name: cr-skill-symbolic-verification
  module: research
  description: "Symbolic verification patterns for code-against-derivation audits.
    Covers SymPy gradient and Hessian verification, analytical-vs-empirical moment
    comparison, second-order condition checks, variable-name-to-symbol mapping, and
    operation matching between LaTeX derivations and implementation code. Loaded by
    @cr-mathematical-verification."
  ---
  ```

  **Sections**:
  1. SymPy Gradient Verification — define symbolic model, compute symbolic
     gradient, compare against code gradient function; numerical gradient check
     as fallback
  2. Hessian Verification — same pattern for second derivatives; check
     negative-definiteness for concavity
  3. Moment Condition Verification — define analytical moments symbolically,
     compare against empirical moment functions in code
  4. Second-Order Conditions — symbolic verification of SOCs for optimization
     problems; saddle-point detection
  5. Code-Derivation Mapping Audit — systematic procedure: extract equations
     from `.tex`/`.md` derivation, extract operations from code, build
     correspondence table, flag mismatches
  6. Numerical Verification Harness — when symbolic verification is infeasible,
     use numerical perturbation tests (finite differences, Monte Carlo draws)
  7. Anti-Patterns — trusting numerical gradients without analytical comparison,
     verifying at a single point only

- **Test Scenarios**:
  - ✅ SKILL.md exists with valid frontmatter
  - ✅ Has `module: research`
  - ✅ Contains SymPy gradient verification section
  - ✅ Contains code-derivation mapping audit section
  - ✅ References `@cr-mathematical-verification`
- **Acceptance criteria**: Skill provides actionable SymPy patterns and
  a systematic code-against-derivation audit procedure.

### 4. Create `cr-skill-identification-strategies/SKILL.md`
- **Requirements**: R4, R9
- **Files**: `.github/skills/cr-skill-identification-strategies/SKILL.md`
- **Details**:
  Comprehensive reference for identification strategies with their required
  diagnostics. This skill is the primary reference for `@cr-identification-audit`.

  **Frontmatter**:
  ```yaml
  ---
  name: cr-skill-identification-strategies
  module: research
  description: "Identification strategies for causal inference in economics with
    required diagnostic tests. Covers IV (first-stage F, weak-IV-robust inference,
    AR confidence sets), RDD (McCrary density, optimal bandwidth, robust SE), DiD
    (parallel trends, event study, Goodman-Bacon decomposition), event studies,
    synthetic control, and matching/IPW. Each strategy includes required diagnostics
    — missing diagnostics trigger P0 identification-theater flags. Loaded by
    @cr-identification-audit and /cr-review."
  ---
  ```

  **Sections** (one per strategy):
  1. Instrumental Variables (IV) — first-stage F (>10 rule of thumb),
     Kleibergen-Paap for multiple endogenous, weak-IV-robust inference
     (Anderson-Rubin, conditional likelihood ratio), Stock-Yogo critical values,
     overidentification (Sargan/Hansen J), exclusion restriction discussion
     **Required diagnostics**: first-stage F-stat, Sargan/Hansen J (if overidentified)
  2. Regression Discontinuity (RDD) — McCrary density test, optimal bandwidth
     selection (Imbens-Kalyanaraman, Calonico-Cattaneo-Titiunik), local
     polynomial estimation, robust bias-corrected SE, placebo cutoffs, covariate
     smoothness
     **Required diagnostics**: McCrary test, bandwidth sensitivity, covariate balance
  3. Difference-in-Differences (DiD) — parallel trends test, event study plot,
     staggered treatment (Callaway-Sant'Anna, Sun-Abraham, de Chaisemartin-D'Haultfoeuille),
     Goodman-Bacon decomposition, Athey-Imbens
     **Required diagnostics**: parallel trends test, event study, Bacon decomposition
     (if staggered)
  4. Event Studies — Abraham-Sun vs. TWFE, pre-trends test, dynamic treatment
     effects, binning endpoints, reference period selection
     **Required diagnostics**: pre-trends test, binned endpoint specification
  5. Synthetic Control — pre-treatment fit (RMSPE), permutation inference
     (placebo-in-space), donor pool selection, outcome gap visualization
     **Required diagnostics**: pre-treatment RMSPE, permutation p-value
  6. Matching and IPW — propensity score estimation, balance diagnostics
     (standardized differences < 0.1), common support, sensitivity analysis
     (Rosenbaum bounds)
     **Required diagnostics**: balance table, common support, Rosenbaum bounds
  7. Strategy Selection Guide — decision tree for choosing strategy based on
     data structure, treatment assignment mechanism, and available variation
  8. Anti-Patterns — "identification theater" catalog (claiming IV without
     first-stage, parallel trends on 2 pre-periods, etc.)

  Each strategy section has:
  ```
  ## Strategy: <Name>
  **When applicable**: ...
  **Required diagnostics** (P0 if missing):
  1. ...
  **Code patterns** (R with fixest / Python / Stata):
  **Anti-patterns**:
  **Key references**:
  ```

- **Test Scenarios**:
  - ✅ SKILL.md exists with valid frontmatter
  - ✅ Has `module: research`
  - ✅ Contains sections for IV, RDD, DiD, event study, synthetic control, matching
  - ✅ Each strategy has "Required diagnostics" subsection
  - ✅ References `@cr-identification-audit`
  - 🛑 Anti-patterns section references "identification theater"
- **Acceptance criteria**: All 6 strategies documented with required diagnostics
  and code patterns.

### 5. Create `cr-skill-theory-data-dialogue/SKILL.md`
- **Requirements**: R5, R9
- **Files**: `.github/skills/cr-skill-theory-data-dialogue/SKILL.md`
- **Details**:
  Patterns for systematically translating theoretical assumptions into
  empirical checks.

  **Frontmatter**:
  ```yaml
  ---
  name: cr-skill-theory-data-dialogue
  module: research
  description: "Patterns for translating theoretical assumptions into empirical
    checks. Covers distributional tests, conditional moment checks, support analysis,
    reduced-form regressions to inform structural priors, exclusion-restriction sniff
    tests, monotonicity checks, and balance tests. Documents the dialogue trail in
    .cg-docs/research/specifications/. Loaded for Specification Analysis tasks."
  ---
  ```

  **Sections**:
  1. The Theory-Data Dialogue Pattern — overview of the iterative cycle:
     state assumption → formulate testable implication → run check → interpret
     → revise or proceed
  2. Distributional Tests — Kolmogorov-Smirnov, Anderson-Darling, Shapiro-Wilk,
     Q-Q plots; when each is appropriate; power considerations
  3. Conditional Moment Checks — testing conditional mean/variance restrictions
     implied by theory; Bierens-type tests
  4. Support Analysis — checking that the support of observed variables matches
     theory assumptions (e.g., non-negative wages, bounded probabilities)
  5. Reduced-Form Regressions — using OLS/IV reduced forms to check whether
     structural relationships appear in the data before estimating the full model
  6. Exclusion Restriction Checks — indirect tests for instrument validity:
     balance tests, falsification tests, overidentification
  7. Monotonicity Checks — verifying monotonicity assumptions (e.g., first-stage
     monotonicity in LATE, single-crossing in sorting models)
  8. Balance Tests — covariate balance across treatment groups; standardized
     differences; randomization inference
  9. Documentation Trail — how to record each check in
     `.cg-docs/research/specifications/`: filename convention, YAML frontmatter
     (assumption tested, result, decision), linking back to derivation file
  10. Anti-Patterns — running checks without documenting results, testing
      on the estimation sample only, ignoring failed checks

- **Test Scenarios**:
  - ✅ SKILL.md exists with valid frontmatter
  - ✅ Has `module: research`
  - ✅ Contains distributional tests section
  - ✅ Contains documentation trail section referencing `.cg-docs/research/specifications/`
  - ✅ Contains theory-data dialogue pattern description
- **Acceptance criteria**: Skill provides systematic procedure for theory-data
  checks with documentation conventions.

### 6. Create `cr-skill-research-eda/SKILL.md`
- **Requirements**: R6, R9
- **Files**: `.github/skills/cr-skill-research-eda/SKILL.md`
- **Details**:
  Research-framed EDA that goes beyond generic "plot everything" approaches.

  **Frontmatter**:
  ```yaml
  ---
  name: cr-skill-research-eda
  module: research
  description: "Exploratory data analysis framed by research questions. Covers
    targeted distributional checks, conditional moment plots, weighted descriptive
    statistics, missingness patterns with implications, outlier analysis tied to
    theory, and sample restriction documentation. Distinct from generic engineering
    EDA — every analysis step is motivated by a research question or theoretical
    prediction. Loaded for EDA and Specification Analysis tasks."
  ---
  ```

  **Sections**:
  1. Research-Framed EDA Philosophy — every plot and summary must answer a
     question; state the question before the code; interpret the result
  2. Targeted Distributional Checks — distributions that matter for the model
     (e.g., log-normality for wage regressions, exponential for duration models);
     density plots with theoretical overlays
  3. Conditional Moment Plots — E[Y|X] binscatters, conditional variance plots,
     conditional quantile plots; detecting nonlinearity and heteroscedasticity
  4. Weighted Descriptive Statistics — always weight by survey/sampling weights;
     collapse-based patterns (`fmean`, `fsd`, `fmedian` with `w` argument);
     unweighted-vs-weighted comparison table
  5. Missingness Patterns — missing-at-random vs. not; Little's MCAR test;
     missingness correlations with observables; implications for estimation
  6. Outlier Analysis — theory-motivated bounds (negative income is impossible,
     consumption > GDP is suspect); winsorization vs. trimming vs. robust methods;
     documenting the decision
  7. Sample Restriction Documentation — every `filter()` / `keep if` must have
     a documented rationale; sample size at each restriction step; flow chart
  8. Subgroup Analysis — splits motivated by theory (not data mining); comparing
     moments across subgroups; pre-specifying subgroups in the plan
  9. Anti-Patterns — "exploring blindly" without a question, p-hacking via
     subgroup analysis, undocumented sample restrictions

- **Test Scenarios**:
  - ✅ SKILL.md exists with valid frontmatter
  - ✅ Has `module: research`
  - ✅ Contains weighted descriptive statistics section
  - ✅ Contains missingness patterns section
  - ✅ Contains sample restriction documentation section
  - ✅ Distinguishes itself from generic EDA
- **Acceptance criteria**: Skill provides research-specific EDA patterns
  distinct from generic data exploration.

### 7. Create `latex.instructions.md`
- **Requirements**: R7, R10
- **Files**: `.github/instructions/latex.instructions.md`
- **Details**:
  Auto-applied when any `.tex` or `.Rnw` file is open.

  **Frontmatter**:
  ```yaml
  ---
  applyTo: "**/*.tex,**/*.Rnw"
  module: research
  ---
  ```

  **Content**:
  - Load `cr-skill-mathematical-derivation` when working on derivation files
  - Load `cr-skill-academic-writing` (Phase 6 — note as planned) when working
    on manuscript sections
  - LaTeX conventions: prefer `\begin{align}` over `\begin{eqnarray}`,
    use `\label{eq:name}` for every numbered equation, use `\text{}` for
    text inside math mode
  - BibTeX/BibLaTeX citation conventions
  - Cross-reference conventions (`\ref{}`, `\eqref{}`, `\cref{}`)
  - Common packages expected: `amsmath`, `amssymb`, `mathtools`, `booktabs`,
    `natbib` or `biblatex`

- **Test Scenarios**:
  - ✅ File exists with valid frontmatter
  - ✅ Has `module: research`, `applyTo:` includes `*.tex`
  - ✅ References `cr-skill-mathematical-derivation`
  - 🛑 Does not reference skills from Phase 6 without "(planned)" marker
- **Acceptance criteria**: LaTeX files auto-load relevant research skills.

### 8. Create `math.instructions.md`
- **Requirements**: R8, R10
- **Files**: `.github/instructions/math.instructions.md`
- **Details**:
  Auto-applied to derivation files in the research directory.

  **Frontmatter**:
  ```yaml
  ---
  applyTo: "**/.cg-docs/research/derivations/**/*.md,**/.cg-docs/research/derivations/**/*.tex"
  module: research
  ---
  ```

  **Content**:
  - Always load `cr-skill-mathematical-derivation`
  - Always load `cr-skill-symbolic-verification`
  - Derivation file structure conventions: YAML frontmatter (`title`,
    `model`, `date`, `status`), then sections (Setup, Assumptions,
    Derivation, Result, Variable Mapping Table)
  - Notation discipline rules from `cr-skill-mathematical-derivation`
  - Warn about code-math mismatch risk: every variable in the derivation
    should have a code counterpart documented in the mapping table

- **Test Scenarios**:
  - ✅ File exists with valid frontmatter
  - ✅ Has `module: research`, `applyTo:` includes derivations path
  - ✅ References `cr-skill-mathematical-derivation`
  - ✅ References `cr-skill-symbolic-verification`
- **Acceptance criteria**: Math derivation files auto-load appropriate skills.

### 9. Update `/cr-*` prompts — remove "Phase 4" placeholders
- **Requirements**: R11, R17, R18
- **Files**: `.github/prompts/cr-brainstorm.prompt.md`, `.github/prompts/cr-review.prompt.md`
- **Details**:
  Replace "Phase 4, not yet available" markers with live skill references.
  Remove stale skill names. Relabel misattributed phase markers.

  **In `cr-brainstorm.prompt.md`** (around lines 46–48):
  - Replace `Theory/Modeling → cr-skill-structural-econometrics *(Phase 4, not yet available)*`
    with `Theory/Modeling → cr-skill-structural-econometrics, cr-skill-mathematical-derivation, cr-skill-symbolic-verification`
  - Remove `Specification Analysis → cr-skill-specification-analysis *(Phase 4, not yet available)*`
    and replace with `Specification Analysis → cr-skill-theory-data-dialogue, cr-skill-research-eda`
    (the skill name `cr-skill-specification-analysis` was never created — the correct skills are
    `cr-skill-theory-data-dialogue` and `cr-skill-research-eda`)
  - Replace `EDA → standard analysis skills` with `EDA → cr-skill-research-eda`
  - Add: `Implementation → cr-skill-structural-econometrics, cr-skill-mathematical-derivation`
    (for structural implementation)

  **In `cr-review.prompt.md`** (around lines 75, 92):
  - Relabel `@cr-specification-analysis *(Phase 4 — not yet available)*` to
    `@cr-specification-analysis *(Phase 5 — not yet available)*`
    (the agent belongs to Phase 5, not Phase 4; the agent file does not exist yet)
  - Leave Phase 5/6/7 markers on other agents unchanged

- **Test Scenarios**:
  - ✅ `cr-brainstorm.prompt.md` no longer contains "Phase 4, not yet available"
  - ✅ `cr-brainstorm.prompt.md` does NOT contain `cr-skill-specification-analysis`
  - ✅ `cr-brainstorm.prompt.md` references `cr-skill-structural-econometrics` without placeholder
  - ✅ `cr-brainstorm.prompt.md` references `cr-skill-theory-data-dialogue`
  - ✅ `cr-review.prompt.md` `@cr-specification-analysis` is labeled "Phase 5"
  - ✅ `cr-review.prompt.md` Phase 5/6/7 markers remain for future agents
  - 🛑 All references to skills point to skill names that now exist as directories
- **Tests**: Covered by existing `cr-prompts.Tests.ps1` plus new assertions
  in Step 11.
- **Acceptance criteria**: No remaining "Phase 4" placeholders in any prompt;
  no stale `cr-skill-specification-analysis` reference.

### 10. Update CR agents to load Phase 4 skills
- **Requirements**: R16
- **Files**: `.github/agents/cr-mathematical-verification.agent.md`,
  `.github/agents/cr-identification-audit.agent.md`,
  `.github/agents/cr-econometric-reasoning.agent.md`
- **Details**:
  Each agent currently loads only `cr-skill-research-integrity` (or
  `cr-skill-research-workflow`). Add instructions to load the corresponding
  Phase 4 skills so the domain knowledge is actually available at review time.

  **Updates**:
  - `@cr-mathematical-verification`: add "Also load `cr-skill-symbolic-verification`
    and `cr-skill-mathematical-derivation` for derivation conventions and
    verification patterns."
  - `@cr-identification-audit`: add "Also load `cr-skill-identification-strategies`
    for the full diagnostic protocol per strategy." Add cross-reference note:
    "`cr-skill-research-integrity` (Error Class 3) defines the P0 detection
    triggers; `cr-skill-identification-strategies` provides the full diagnostic
    protocols."
  - `@cr-econometric-reasoning`: add "Also load `cr-skill-structural-econometrics`
    for structural estimation patterns and anti-patterns."

- **Test Scenarios**:
  - ✅ Each agent file references its corresponding Phase 4 skill by name
  - ✅ `@cr-identification-audit` contains cross-reference between the two skills
  - 🛑 No `tools: ['write']` added — agents remain read-only
- **Acceptance criteria**: All 3 agents load their Phase 4 skills.

### 11. Extend `cr-prompts.Tests.ps1` with skill content tests
- **Requirements**: R12, R15
- **Files**: `tests/cr-prompts.Tests.ps1`
- **Details**:
  Add Describe blocks for each new skill, following the existing pattern
  for `cr-skill-research-workflow` and `cr-skill-research-integrity`.

  **New Describe blocks** (6 total — one per skill):

  1. `cr-skill-structural-econometrics/SKILL.md - content`:
     - Exists, has `module: research`
     - Contains "Discrete Choice" section
     - Contains "Dynamic Programming" section
     - Contains "GMM" section
     - Contains "Maximum Likelihood" or "MLE" section
     - Contains "Standard Errors" section
     - Contains "Anti-Patterns" section

  2. `cr-skill-mathematical-derivation/SKILL.md - content`:
     - Exists, has `module: research`
     - Contains "Notation Discipline" section
     - Contains "Code-Math Variable Mapping" or "Variable Mapping" section
     - References `.cg-docs/research/derivations/`

  3. `cr-skill-symbolic-verification/SKILL.md - content`:
     - Exists, has `module: research`
     - Contains "SymPy" reference
     - Contains "Gradient" section
     - Contains "Hessian" section
     - References `@cr-mathematical-verification`

  4. `cr-skill-identification-strategies/SKILL.md - content`:
     - Exists, has `module: research`
     - Contains IV section
     - Contains RDD section
     - Contains DiD section
     - Contains "Required diagnostics" subsection pattern
     - References `@cr-identification-audit`

  5. `cr-skill-theory-data-dialogue/SKILL.md - content`:
     - Exists, has `module: research`
     - Contains "Distributional Tests" section
     - Contains documentation trail section
     - References `.cg-docs/research/specifications/`

  6. `cr-skill-research-eda/SKILL.md - content`:
     - Exists, has `module: research`
     - Contains "Weighted Descriptive Statistics" section
     - Contains "Missingness" section
     - Contains "Sample Restriction" section

  **Additional assertions** for prompt updates (Step 9):
  - `cr-brainstorm.prompt.md` does NOT contain "Phase 4, not yet available"
  - `cr-brainstorm.prompt.md` does NOT contain `cr-skill-specification-analysis`
  - `cr-brainstorm.prompt.md` references `cr-skill-theory-data-dialogue`
  - `cr-review.prompt.md` `@cr-specification-analysis` entry is labeled "Phase 5" (not "Phase 4")

  **Agent skill-load assertions** (Step 10):
  - `cr-mathematical-verification.agent.md` references `cr-skill-symbolic-verification`
  - `cr-mathematical-verification.agent.md` references `cr-skill-mathematical-derivation`
  - `cr-identification-audit.agent.md` references `cr-skill-identification-strategies`
  - `cr-econometric-reasoning.agent.md` references `cr-skill-structural-econometrics`

  **Instruction file tests**:
  - `latex.instructions.md` exists, has `module: research`, `applyTo` matches `*.tex`
  - `math.instructions.md` exists, has `module: research`, `applyTo` matches `derivations`
  - Both reference `cr-skill-mathematical-derivation`

- **Test Scenarios**:
  - ✅ All new Describe blocks pass
  - ✅ Existing tests remain unchanged and pass
  - 🛑 Test names follow existing naming convention
  - ❌ Missing skill file → test fails with clear name
- **Acceptance criteria**: All new skills and instruction files have
  structural regression tests; total test count increases appropriately.

## Testing Strategy

- **Structural tests** (primary): Each skill gets a Describe block in
  `cr-prompts.Tests.ps1` validating existence, frontmatter, and key content
  sections. Pattern matches `cr-skill-research-workflow` and
  `cr-skill-research-integrity` test blocks.
- **Module frontmatter** (automatic): Existing `prompt-tools.Tests.ps1`
  test `"All managed files have valid module: frontmatter"` automatically
  picks up new files — no manual update needed.
- **Full suite**: Run `. tests\Run-Tests.ps1` to confirm all 1941+ tests pass.

## Documentation Checklist

- [ ] Each SKILL.md has clear section headers and actionable content
- [ ] Anti-patterns sections included in all 6 skills
- [ ] Code examples provided in R, Python, and Stata where applicable
- [ ] Cross-references between related skills (e.g., `cr-skill-identification-strategies`
      → `cr-skill-theory-data-dialogue` for pre-estimation checks)
- [ ] Instruction files document which skills they load and when
- [ ] Inline comments for complex LaTeX patterns in `cr-skill-mathematical-derivation`

## Risks & Mitigations

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Skills too long for model context window | Medium | P2 — model truncates skill content | Keep each SKILL.md under 500 lines; use workflows/references subdirectories for deep dives if needed |
| LaTeX instruction `applyTo` too broad | Low | P3 — loads research skills on non-research LaTeX files | `applyTo` pattern is precise; skill content has guard: "Load only for research-project LaTeX files" |
| `cr-review.prompt.md` placeholder removal breaks existing tests | Low | P1 — test failures | Review existing test assertions before modifying prompts; run tests after each prompt edit |
| Skill content accuracy — wrong econometric advice | Medium | P0 — incorrect research guidance | Ground all patterns in established textbook references (Cameron & Trivedi, Wooldridge, Train); include "Key references" in each section |
| `math.instructions.md` `applyTo` pattern mismatch | Medium | P2 — doesn't trigger on derivation files | No precedent for path-scoped `applyTo` globs in this codebase (existing instructions use `**/*.ext` only). VS Code's glob behavior on dot-prefixed directories is untested. Test with an actual file before committing. Fallback: if the glob doesn't trigger, document that users should manually load `cr-skill-mathematical-derivation` and `cr-skill-symbolic-verification` when editing derivation files, and consider a filename convention (`*.derivation.md`) in a future iteration |

## Out of Scope

- **Skill content for ML in economics** — that's Phase 5 (`cr-skill-ml-economics`)
- **Skill content for academic writing** — that's Phase 6 (`cr-skill-academic-writing`)
- **Skill content for replication standards** — that's Phase 7 (`cr-skill-replication-standards`)
- **New agent creation** — Phase 3 handles agent file creation; this phase updates existing agents to load new skills but does not create new agents
- **`@cr-specification-analysis` agent** — Phase 5 scope, not Phase 4; only the skill knowledge (`cr-skill-theory-data-dialogue`) is created here
- **Workflow/reference subdirectories** — SKILL.md is the primary deliverable; subdirectories can be added later if skills exceed the 500-line guideline
- **Updating `copilot-instructions.template.md`** — skills are auto-discovered by Copilot via `.github/skills/`; the template doesn't list individual skills
