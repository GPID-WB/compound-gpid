---
date: 2026-05-13
title: "Compound Research — extension of compound-gpid for economics & econometrics research"
status: decided
scope: "Deep"
chosen-approach: "Modular plugin system (Approach 3) — same repo, lazy-loaded research module"
tags: [architecture, research, econometrics, ml, structural-modeling, academic-writing, modular-skills, framework-extension]
---

# Compound Research — extension of compound-gpid

## Context

The existing `compound-gpid` plugin gives data science teams a structured AI-assisted workflow (Brainstorm → Plan → Work → Review → Compound) for engineering tasks: code, tests, data pipelines, infrastructure. It enforces statistical correctness, reproducibility, and knowledge capture for poverty-statistics work at the World Bank.

We now want to extend the same framework to support **economics and econometrics research** — the kind of work that produces peer-reviewed journal papers, not just internal data products. The same compound philosophy applies: every unit of work should make the next easier; every solved problem should become reusable knowledge. But the artifacts, the reasoning patterns, and the failure modes are different.

Two initial research types motivate the design:

1. **Structural econometrics** — work where economic theory, the data-generating process (DGP), and empirical features of the data are combined to inform the modeling approach. Requires deep reasoning about functional form, identification, and the bridge between mathematics and code.
2. **Machine learning research in economics** — large-p problems, auxiliary data sources, feature selection, dimension reduction, model selection and assessment, estimation, bootstrapping, and economic interpretation of ML output.

The framework must support diverse task types within these research types — theory derivation, specification analysis, EDA, implementation, writing, table/figure production, reproducibility packaging — all under a unified compound loop that mirrors the engineering side.

User-facing surface: engineering tasks use `/cg-*` commands; research tasks use `/cr-*` commands. Internally, `/cr-*` prompts dispatch a mix of new `cr-*` agents and existing `cg-*` agents to avoid duplication and keep knowledge compounding across both sides.

**Primary personas:**

1. **Researcher-author (senior)** — knows the theory, needs the framework to enforce rigor and reproducibility across the full pipeline from idea to journal submission.
2. **PhD student** — needs scaffolding on methodology selection, derivation steps, and documentation of *why* each modeling choice was made. Learning while producing.

## Requirements

### Functional

- Mirror the compound-gpid workflow loop exactly: `/cr-brainstorm` → `/cr-plan` → `/cr-work` → `/cr-review` → `/cr-fix-triage` → `/cr-compound`, plus the supporting prompts (`/cr-resume`, `/cr-ideate`, `/cr-strategy`, `/cr-plan-review`, `/cr-roadmap-view`).
- Support a research task taxonomy — the same prompt handles many task types, classified at intake time:

  | Task Type | Description | Example |
  |---|---|---|
  | **Theory/Modeling** | Derive the model: setup, FOCs, estimating equations, likelihood, moment conditions | "Derive the likelihood for a Roy model with sorting" |
  | **Specification Analysis** | Theory-data dialogue — test theoretical assumptions against data and iterate on the specification | "Check whether log-normal wage assumption survives by sector" |
  | **EDA** | Open-ended, research-aware data exploration | "Explore wage distributions by education to check for bimodality" |
  | **Implementation** | Translate a derived model into code, accurately and rigorously | "Code the GMM estimator from Section 3" |
  | **ML/Prediction** | Feature selection, dimension reduction, model assessment, economic interpretation | "Select features for LASSO wage prediction with 200 covariates" |
  | **Writing** | Manuscript sections in journal-appropriate style | "Write the identification strategy section" |
  | **Tables/Figures** | Publication-ready output | "Create Table 2: descriptive statistics by treatment arm" |
  | **Reproducibility** | Replication archive for journal submission | "Package replication archive for AER" |

- Active enforcement of **research integrity** — silent research errors are P0 blockers, not advisory notes. The framework detects and halts on:
  - **Code-math mismatch** — implementation diverges from the derived equations
  - **Specification searching** — undocumented runs of alternative specifications
  - **Identification theater** — strategy claimed without corresponding empirical diagnostic
  - **Unseeded randomness** — bootstrap, simulation, MCMC, or train/test splits without explicit seeds
- Verification chain for v1:
  - **Always**: documented derivation trail — every modeling choice traceable to theory and data evidence
  - **Always in review**: symbolic checks — gradient verification, analytical-vs-empirical moment comparison, second-order condition checks where applicable
  - **Offered after review**: "Symbolic checks passed. Run Monte Carlo simulation to verify parameter recovery?" — researcher opts in
- Reuse existing `cg-*` agents (code-quality, testing, reproducibility, data-quality, performance, architecture, adversarial, version-control) — `/cr-review` orchestrates both engineering and research findings into a single unified report.

### Non-functional

- **Modular activation** — projects declare which modules they use (`engineering`, `research`, or both) in `compound-gpid.local.md`. `cg-link`/`cg-setup` generates a filtered `copilot-instructions.md` so a pure data-engineering project never sees CR instructions and vice versa. Prevents bloated instructions and scales to future modules (Bayesian, causal ML, survey design).
- **Single repository, single install** — CR lives alongside CG in `.github/`. One `cg-link`, one `cg-update`, one `roadmap.json`, one `.cg-docs/`. Knowledge compounds across engineering and research.
- **Documentation of reasoning, not just decisions** — every research artifact records the *why* (theory, data evidence, alternatives considered) so PhD students learn from the trail and reviewers can audit it.
- **Reproducibility is non-negotiable** — lockfiles, seeds, relative paths, data dictionaries, and replication instructions are enforced for every task that produces results.
- Must not break any existing `cg-*` workflow, prompt, agent, skill, or test.

### Out of scope for v1

- Automated literature review (search and summarize prior work)
- Real-time multi-user collaboration (teams coordinate via git)
- Journal-specific `.cls`/`.sty` templates (v1 produces clean generic LaTeX)
- Bayesian workflow (Stan, JAGS, brms) — frequentist structural + ML only
- Data collection / survey / sampling-frame design
- Causal ML (double ML, causal forests, DR-Learner) — its own future module

## Approaches Considered

### Approach 1: Unified Extension — same repo, parallel namespace
CR prompts/agents/skills live alongside CG ones; everything is always loaded. Direct integration, full knowledge sharing, simple install. **Con**: `copilot-instructions.md` grows large; projects that only need one side carry the weight of both.

### Approach 2: Separate Package, shared core
CR is its own repo that imports CG agents via cross-repo references. Clean separation, independent release cycles. **Con**: two repos to maintain; merging two `.github/` directories is fragile; knowledge fragmentation across separate `.cg-docs/` directories violates the compound philosophy.

### Approach 3: Plugin Module System — same repo, lazy loading **(CHOSEN)**
Single repo with module-tagged prompts/agents/skills. Projects declare active modules; `cg-link` generates a filtered `copilot-instructions.md`. Combines Approach 1's knowledge sharing with clean activation boundaries. Future-proof for additional modules.

## Decision

**Approach 3 — Plugin Module System.** Build compound-research as a `research` module within the existing repository, activated per-project via `compound-gpid.local.md`. Engineering content stays in the `engineering` module; shared infrastructure (code-quality, testing, reproducibility, R/Python/Stata skills, version control, roadmap, brainstorming) is tagged `shared` and loaded for both.

This gives us:
- Unified `.cg-docs/` so research and engineering lessons compound together
- Direct reuse of existing agents — `/cr-review` dispatches `@cg-code-quality`, `@cg-testing`, `@cg-reproducibility` for code-level checks and new `@cr-*` agents for research-level checks
- Clean activation boundary — researchers using R for econometrics aren't asked about FastAPI conventions; data engineers aren't asked about identification strategy
- Single install/update path via existing `cg-link`/`cg-update`

## Architecture

### Module-tagging convention

Every prompt, agent, skill, and instruction file gains a `module:` field in its frontmatter:

```yaml
---
description: ...
module: research              # one of: shared | engineering | research
applyTo: ...
---
```

Permitted values:
- `shared` — loaded for all projects (e.g., `cg-skill-git-workflow`, `cg-skill-pester-safety`, `cg-skill-compound-docs`, `@cg-reproducibility`, `@cg-version-control`, `cg-skill-r-shared`)
- `engineering` — loaded only when `engineering` module is active
- `research` — loaded only when `research` module is active

`cg-link` reads `compound-gpid.local.md`, determines active modules, and generates `copilot-instructions.md` that includes only the relevant entries. Default = `engineering` (backward compatible). A project enabling research adds `research` to its module list. A project doing both gets both.

### File layout

```
.github/
├── prompts/
│   ├── cg-brainstorm.prompt.md          # tagged: shared (works for both)
│   ├── cg-plan.prompt.md                # tagged: shared
│   ├── cg-work.prompt.md                # tagged: engineering
│   ├── cg-review.prompt.md              # tagged: engineering
│   ├── cg-compound.prompt.md            # tagged: shared
│   ├── ... existing cg-* prompts ...
│   ├── cr-brainstorm.prompt.md          # NEW — research-aware brainstorm
│   ├── cr-plan.prompt.md                # NEW
│   ├── cr-work.prompt.md                # NEW — task-type-aware execution
│   ├── cr-review.prompt.md              # NEW — orchestrates cg-* + cr-* agents
│   ├── cr-fix-triage.prompt.md          # NEW
│   ├── cr-compound.prompt.md            # NEW — research lesson capture
│   ├── cr-resume.prompt.md              # NEW
│   ├── cr-ideate.prompt.md              # NEW — research idea exploration
│   ├── cr-strategy.prompt.md            # NEW — research agenda planning
│   ├── cr-plan-review.prompt.md         # NEW
│   ├── cr-roadmap-view.prompt.md        # NEW
│   └── cr-derive.prompt.md              # NEW — guided mathematical derivation session
├── agents/
│   ├── cg-code-quality.agent.md         # tagged: shared
│   ├── cg-testing.agent.md              # tagged: shared
│   ├── cg-reproducibility.agent.md      # tagged: shared
│   ├── cg-data-quality.agent.md         # tagged: shared
│   ├── cg-performance.agent.md          # tagged: shared
│   ├── cg-architecture.agent.md         # tagged: shared
│   ├── cg-adversarial.agent.md          # tagged: shared
│   ├── cg-documentation.agent.md        # tagged: shared
│   ├── cg-version-control.agent.md      # tagged: shared
│   ├── cg-learnings-researcher.agent.md # tagged: shared (searches both eng + research lessons)
│   ├── cg-plan-critic.agent.md          # tagged: shared
│   ├── cg-roadmap.agent.md              # tagged: shared
│   ├── cg-roadmap-view.agent.md         # tagged: shared
│   ├── cg-fix-problems.agent.md         # tagged: engineering
│   ├── cg-project-scanner.agent.md      # tagged: shared (extended to detect research signals)
│   ├── cg-release-scanner.agent.md      # tagged: shared
│   ├── cr-mathematical-verification.agent.md   # NEW
│   ├── cr-econometric-reasoning.agent.md       # NEW
│   ├── cr-specification-analysis.agent.md      # NEW
│   ├── cr-identification-audit.agent.md        # NEW
│   ├── cr-academic-writing.agent.md            # NEW
│   ├── cr-ml-methodology.agent.md              # NEW
│   ├── cr-research-integrity.agent.md          # NEW — detects P0 silent errors
│   └── cr-replication-package.agent.md         # NEW
├── skills/
│   ├── cg-skill-brainstorming/          # tagged: shared
│   ├── cg-skill-compound-docs/          # tagged: shared
│   ├── cg-skill-git-workflow/           # tagged: shared
│   ├── cg-skill-pester-safety/          # tagged: shared
│   ├── cg-skill-setup/                  # tagged: shared
│   ├── cg-skill-project-scanner/        # tagged: shared
│   ├── cg-skill-fix-triage-migrate/     # tagged: engineering
│   ├── cg-skill-r-shared/               # tagged: shared
│   ├── cg-skill-r-collapse/             # tagged: shared
│   ├── cg-skill-r-datatable/            # tagged: shared
│   ├── cg-skill-r-tidyverse/            # tagged: shared
│   ├── cg-skill-r-visualization/        # tagged: shared
│   ├── cg-skill-r-testing/              # tagged: shared
│   ├── cg-skill-r-technical/            # tagged: engineering
│   ├── cg-skill-r-analytical/           # tagged: shared (research uses many of these patterns)
│   ├── cg-skill-python-best-practices/  # tagged: shared
│   ├── cg-skill-stata-best-practices/   # tagged: shared
│   ├── cg-skill-stata-testing/          # tagged: shared
│   ├── cr-skill-research-workflow/             # NEW — overarching CR loop conventions
│   ├── cr-skill-research-integrity/            # NEW — P0 silent-error catalog
│   ├── cr-skill-structural-econometrics/       # NEW
│   ├── cr-skill-ml-economics/                  # NEW
│   ├── cr-skill-theory-data-dialogue/          # NEW
│   ├── cr-skill-mathematical-derivation/       # NEW
│   ├── cr-skill-symbolic-verification/         # NEW
│   ├── cr-skill-identification-strategies/     # NEW
│   ├── cr-skill-academic-writing/              # NEW
│   ├── cr-skill-publication-output/            # NEW
│   ├── cr-skill-replication-standards/         # NEW
│   └── cr-skill-research-eda/                  # NEW
└── instructions/
    ├── r.instructions.md                # extended with CR task-type routing
    ├── python.instructions.md           # extended
    ├── stata.instructions.md            # extended
    ├── latex.instructions.md            # NEW — applyTo: **/*.tex, **/*.Rnw
    └── math.instructions.md             # NEW — applyTo: math derivation files
```

### Task taxonomy and skill routing in `/cr-brainstorm`

A Step 1.1 classifier in `/cr-brainstorm` routes the request to the right skill bundle. Classification is explicit — the prompt asks the user to confirm the task type so the routing is auditable.

| Task Type | Primary skills loaded | Reused CG skills |
|---|---|---|
| **Theory/Modeling** | `cr-skill-structural-econometrics`, `cr-skill-mathematical-derivation`, `cr-skill-symbolic-verification` | (LaTeX I/O via `latex.instructions.md`) |
| **Specification Analysis** | `cr-skill-theory-data-dialogue`, `cr-skill-research-eda` | `cg-skill-r-analytical`, `cg-skill-r-collapse`, `cg-skill-r-visualization` |
| **EDA** | `cr-skill-research-eda` | `cg-skill-r-analytical`, `cg-skill-r-visualization`, `cg-skill-r-collapse` |
| **Implementation (structural)** | `cr-skill-structural-econometrics`, `cr-skill-mathematical-derivation` | `cg-skill-r-analytical`, `cg-skill-r-testing`, `cg-skill-python-best-practices` |
| **Implementation (ML)** | `cr-skill-ml-economics` | `cg-skill-python-best-practices`, `cg-skill-r-analytical`, `cg-skill-r-testing` |
| **ML/Prediction** | `cr-skill-ml-economics`, `cr-skill-identification-strategies` | `cg-skill-r-analytical`, `cg-skill-python-best-practices` |
| **Writing** | `cr-skill-academic-writing` | (LaTeX I/O) |
| **Tables/Figures** | `cr-skill-publication-output` | `cg-skill-r-visualization`, `cg-skill-r-analytical`, `cg-skill-python-best-practices` |
| **Reproducibility** | `cr-skill-replication-standards` | `cg-skill-git-workflow`, `cg-skill-r-technical`, `cg-skill-python-best-practices` |

Every research task additionally loads `cr-skill-research-workflow` (the loop conventions) and `cr-skill-research-integrity` (the silent-error catalog).

### Agent inventory — new CR agents

| Agent | Purpose | Dispatched by | Reuses |
|---|---|---|---|
| `@cr-econometric-reasoning` | Reason about DGP, functional form, identification strategy at brainstorm/plan time | `/cr-brainstorm`, `/cr-plan` | — |
| `@cr-specification-analysis` | Bridge theory and data — formulate testable implications of theoretical assumptions, run checks, report what they mean for model specification | `/cr-work` (Specification Analysis task), `/cr-review` | `@cg-data-quality` |
| `@cr-mathematical-verification` | Symbolic checks during review — verify gradients, compare analytical vs empirical moments, check second-order conditions, audit code against derivation | `/cr-review`, `/cr-work` (Implementation task) | — |
| `@cr-identification-audit` | When researcher claims IV/RDD/DiD/RD, check for matching diagnostic (first-stage F, McCrary, parallel trends, etc.) — P0 if missing | `/cr-review`, `/cr-plan-review` | — |
| `@cr-research-integrity` | Detect P0 silent errors — code-math mismatch, specification searching, unseeded randomness | `/cr-review`, automatically during `/cr-work` | `@cg-reproducibility` |
| `@cr-academic-writing` | Review prose for journal style, exposition quality, notation consistency, citation completeness | `/cr-review` (Writing task) | `@cg-documentation` |
| `@cr-ml-methodology` | Audit ML choices — train/test/validation split, regularization rationale, hyperparameter search, economic interpretation of coefficients/feature importance | `/cr-review` (ML task) | `@cg-performance`, `@cg-data-quality` |
| `@cr-replication-package` | Audit replication archive — file inventory, data dictionary, run instructions, dependency lockfile, expected runtime, seed list | `/cr-review` (Reproducibility task), `/cr-work` | `@cg-reproducibility`, `@cg-version-control` |

### Agent reuse — existing CG agents called from CR workflows

| CG Agent | When used in CR |
|---|---|
| `@cg-code-quality` | Implementation, ML, Tables/Figures tasks — code standards apply equally |
| `@cg-testing` | Implementation tasks — estimator unit tests, simulation tests |
| `@cg-reproducibility` | All CR tasks producing results — lockfiles, seeds, paths |
| `@cg-data-quality` | EDA, Specification Analysis, Implementation — data validation |
| `@cg-performance` | ML, large-p tasks, simulation-heavy structural work |
| `@cg-architecture` | Implementation tasks — code organization |
| `@cg-adversarial` | Theory/Modeling — "try to break the identification, find a counter-example DGP" |
| `@cg-version-control` | All tasks — same git workflow |
| `@cg-learnings-researcher` | All tasks — searches `.cg-docs/solutions/` for prior research lessons |
| `@cg-plan-critic` | `/cr-plan-review` — checks plan for over-engineering, missing edge cases |
| `@cg-documentation` | Writing tasks — paired with `@cr-academic-writing` |
| `@cg-roadmap`, `@cg-roadmap-view` | Same roadmap.json, milestones can mix engineering and research features |

### New skills — purpose and scope

| Skill | Scope |
|---|---|
| `cr-skill-research-workflow` | Overarching conventions: brainstorm/plan/work/review/compound for research; `.cg-docs/research/` layout (derivations, specifications, results, manuscripts); research integrity priority system (P0–P3); reasoning-trail documentation requirement |
| `cr-skill-research-integrity` | Catalog of P0 silent errors with detection patterns and remediation: code-math mismatch, specification searching, identification theater, unseeded randomness, asymptotic-assumption violations, wrong SE clustering, distributional-assumption-untested |
| `cr-skill-structural-econometrics` | Discrete choice, dynamic programming, simulation-based estimation (MSM, SMM, indirect inference), maximum likelihood for structural models, GMM, moment selection, sandwich SE, bootstrap variants, identification at infinity, exclusion restrictions, parametric vs semi-parametric trade-offs |
| `cr-skill-ml-economics` | LASSO/ridge/elastic-net for high-dim economics, random forests and boosting for prediction, cross-validation done right (panel CV, time-series CV, stratified CV by group), out-of-sample assessment, post-selection inference (debiased lasso), Chernozhukov-style cross-fitting, variable importance with economic interpretation, when ML is appropriate vs when it isn't |
| `cr-skill-theory-data-dialogue` | Patterns for translating theoretical assumptions into empirical checks: distributional tests, conditional moment checks, support analysis, reduced-form regressions to inform structural priors, exclusion-restriction sniff tests, monotonicity checks, balance tests; how to document the dialogue trail in `.cg-docs/research/specifications/` |
| `cr-skill-mathematical-derivation` | LaTeX conventions for derivations, notation discipline, numbered equation conventions, FOC derivation patterns, envelope theorem applications, integration by parts in expectation, change of variables, asymptotic expansions, cross-referencing code variables to math symbols |
| `cr-skill-symbolic-verification` | SymPy patterns for gradient/Hessian verification, analytical-vs-empirical moment comparison harness, second-order condition checks, code-against-derivation audit (variable name and operation matching) |
| `cr-skill-identification-strategies` | IV (first-stage F, weak-IV-robust inference, AR confidence sets), RDD (McCrary density, optimal bandwidth, robust SE), DiD (parallel trends test, event study, Goodman-Bacon decomposition), event studies, synthetic control, matching/IPW; required diagnostics per strategy |
| `cr-skill-academic-writing` | Journal style (AER, JPE, QJE, Econometrica conventions), section structure, abstract writing, equation exposition (explain, don't decorate), notation introduction discipline, citation style, response-to-referee patterns |
| `cr-skill-publication-output` | `modelsummary`/`fixest::etable` for regression tables, `kableExtra` for LaTeX tables, ggplot2 + wbplot for paper figures, font/size conventions for journal submission, figure-caption discipline (self-contained), table-note discipline (variable definitions in notes) |
| `cr-skill-replication-standards` | AEA/AER replication standards, READMEs that survive 5 years, dependency lockfiles, seed lists, expected runtimes, data documentation (codebook + data dictionary), absolute-path forbidden patterns, sensitive-data handling |
| `cr-skill-research-eda` | EDA framed by research question: targeted distributional checks, conditional moment plots, weighted descriptive statistics, missingness patterns with implications, outlier analysis tied to theory, sample restriction documentation; how this differs from generic engineering EDA |

### New `.cg-docs/research/` directory layout

Research artifacts live in a structured subtree so they're findable and the compound loop captures research-specific lessons:

```
.cg-docs/
├── brainstorms/              # existing — research brainstorms go here too
├── plans/                    # existing — research plans go here too
├── reviews/                  # existing — research reviews go here too
├── solutions/                # existing — research lessons go here too (new categories)
│   ├── bugs/
│   ├── ...
│   ├── identification/       # NEW — identification-strategy lessons
│   ├── specification/        # NEW — theory-data dialogue lessons
│   ├── derivation/           # NEW — math derivation patterns
│   ├── ml-methodology/       # NEW — ML pitfalls and patterns
│   └── reproducibility/      # NEW — replication-archive lessons
└── research/                 # NEW — research-specific persistent artifacts
    ├── derivations/          # LaTeX files: setup, FOCs, estimating equations
    ├── specifications/       # specification-analysis trails (theory → check → finding → decision)
    ├── results/              # estimation runs, log files, regression output
    ├── manuscript/           # paper sections, abstract, response letters
    └── replication/          # replication-package staging area
```

### Research Integrity Priority System (P0–P3)

Mirrors compound-gpid's P0–P3 priority system, applied to research-specific failure modes. Detected by `@cr-research-integrity` and `@cr-identification-audit`; surfaced in `/cr-review`.

| Priority | Category | Examples | Enforcement |
|---|---|---|---|
| **P0 — BLOCKING** | Silent research errors | Code-math mismatch; unreported specification search; identification claimed without first-stage evidence; unseeded randomness; PII exposed in replication archive | `/cr-review` halts; must resolve before proceeding |
| **P1 — CRITICAL** | Methodological gaps | Missing robustness check; asymptotic assumptions violated by sample size; wrong SE clustering; distributional assumption untested; missing standard error for derived quantity | Must address before task marked `done` |
| **P2 — IMPORTANT** | Rigor improvements | Alternative estimator comparison missing; sensitivity analysis incomplete; notation inconsistency between derivation and code; missing summary statistics for key subsamples | Should address |
| **P3 — ADVISORY** | Polish | Citation format, table alignment, variable naming consistency between code and paper, figure-caption verbosity | Nice to have |

### Active P0 detection mechanisms

These run **during `/cr-work`**, not only at review time, so errors are caught at write-time:

1. **Code-math mismatch detector** — when implementation follows a derivation in `.cg-docs/research/derivations/`, `@cr-mathematical-verification` cross-references variable names, functional forms, and operations between the LaTeX/math artifact and the code. Discrepancies flagged immediately.
2. **Specification search tracker** — every estimation run is logged to `.cg-docs/research/results/manifest.json`. `/cr-review` cross-checks the paper text against the manifest; if 15 specifications were run but only 2 appear in the paper, flagged P0.
3. **Identification audit** — when a researcher declares an identification strategy in the plan or brainstorm (IV, RDD, DiD, event study, RD), `@cr-identification-audit` checks for the corresponding diagnostic. Missing = P0.
4. **Seed enforcement** — any code path involving randomness (bootstrap, simulation, MCMC, train/test split, k-fold CV) without an explicit seed call → P0 raised during `/cr-work`.

### `/cr-review` orchestration

`/cr-review` is the choreographer. It dispatches both shared and CR-specific agents and merges findings into a single prioritized report:

```
Step 1: Dispatch shared agents (always)
  - @cg-code-quality, @cg-testing, @cg-reproducibility, @cg-data-quality,
    @cg-version-control, @cg-documentation

Step 2: Dispatch CR-specific agents (always)
  - @cr-research-integrity      # P0 silent-error detection
  - @cr-mathematical-verification # symbolic checks (if derivation exists)
  - @cr-identification-audit     # if identification strategy claimed

Step 3: Dispatch task-type-specific agents (conditional)
  - Theory/Modeling task     → @cr-econometric-reasoning, @cg-adversarial
  - Specification Analysis   → @cr-specification-analysis
  - ML/Prediction task       → @cr-ml-methodology, @cg-performance
  - Writing task             → @cr-academic-writing
  - Reproducibility task     → @cr-replication-package

Step 4: Merge findings, sort by priority (P0 → P3), present unified report

Step 5: After review, offer Monte Carlo simulation verification (if symbolic
        checks passed and an estimator was implemented)
```

### Backward compatibility & migration

- **Default module = `engineering`**. Existing projects continue working unchanged after the migration.
- Adding `research` to `compound-gpid.local.md` is opt-in.
- Existing `copilot-instructions.md` templates updated to read modules and filter. `cg-link` regenerates on relink; no manual edits needed.
- All existing tests must continue to pass. New tests added for: module-tagging frontmatter presence, filtered-instructions generation correctness, `cr-*` prompt structure, agent dispatch matrices.

### Charter implications

The current `compound-gpid.md` charter scopes the project to "AI-assisted development" for "poverty statistics." Adding research is a scope expansion. The charter should be updated (with user approval) before this lands to add:

- An additional deliverable for research workflow support
- A second user profile (researcher-author and PhD student)
- A new constraint family for research integrity (P0 silent-error prevention)

The core values transfer cleanly: "statistical correctness over speed" → "research integrity over speed"; "fail loudly, never silently" applies even more strongly to research.

## Phased Implementation Plan

This is a Deep-scope effort. Suggested phases for `/cr-plan` (each phase ends with passing tests and a working artifact):

### Phase 1 — Module system (foundation)
- Add `module:` frontmatter convention to all existing prompts, agents, skills, instructions
- Extend `compound-gpid.local.md` schema with `modules: [engineering|research|...]`
- Update `cg-link` to read modules and filter `copilot-instructions.md` generation
- Update `cg-skill-setup` to ask about modules at first install
- Tests: module frontmatter required and valid; filtered generation correct; default = `engineering` backward-compatible

### Phase 2 — Research workflow scaffolding
- Create `cr-skill-research-workflow` and `cr-skill-research-integrity`
- Build `/cr-brainstorm`, `/cr-plan`, `/cr-work`, `/cr-review`, `/cr-compound` as research-aware copies of their CG counterparts with task-type classifier
- Create `.cg-docs/research/` directory layout and tests for it
- Tests: each `/cr-*` prompt has the canonical Step 0, branch offer, pushback, handoff structure; task-type classifier present

### Phase 3 — Core research agents
- Build `@cr-research-integrity`, `@cr-mathematical-verification`, `@cr-identification-audit`, `@cr-econometric-reasoning`
- Wire `/cr-review` orchestration (shared + CR-specific + conditional task-type dispatch)
- Tests: agent dispatch matrices, P0 detection on synthetic violations, schemaVersion guards

### Phase 4 — Structural econometrics skills
- `cr-skill-structural-econometrics`, `cr-skill-mathematical-derivation`, `cr-skill-symbolic-verification`, `cr-skill-identification-strategies`, `cr-skill-theory-data-dialogue`, `cr-skill-research-eda`
- `latex.instructions.md`, `math.instructions.md`
- Tests: skill descriptions within length cap, applyTo patterns valid, references resolvable

### Phase 5 — ML in economics
- `cr-skill-ml-economics`, `@cr-ml-methodology`
- `@cr-specification-analysis` agent
- Tests: agent dispatch, skill content sanity

### Phase 6 — Writing & publication output
- `cr-skill-academic-writing`, `cr-skill-publication-output`, `@cr-academic-writing`
- Tests

### Phase 7 — Reproducibility & replication package
- `cr-skill-replication-standards`, `@cr-replication-package`
- Integration with `@cg-reproducibility`
- Tests

### Phase 8 — Integration polish & docs
- Update `compound-gpid.md` charter (with user approval) for new scope
- Update `README.md`, `docs/manual.md`, `docs/reference.md`, `docs/workflow.md`
- Add a `cr-` section to `.github/copilot-instructions.template.md`
- Roadmap milestone for `compound-research` with all phase features registered
- Full test pass including cross-prompt journey tests for `/cr-*` flows

## Devil's Advocate — Resolved Points

- **Problem validation**: Acknowledged the reasoning-side gap is real for the team's research output; documented as motivation, not anticipatory.
- **Simplicity check**: Considered "just write a few skills and use existing `/cg-brainstorm`." Rejected because the P0 research-integrity requirements (active detection of silent errors during work, not only at review) require new prompt-level logic and dedicated agents, not skill content alone.
- **Effort-value**: Module system adds engineering overhead but pays back via clean activation boundaries and future modules (Bayesian, causal ML, survey design are on the horizon). Building it now is cheaper than retrofitting it after `cr-*` content already exists.
- **Charter alignment**: Scope expansion acknowledged; charter update step added to Phase 8.

## Next Steps

1. **Update the charter** (`compound-gpid.md`) to reflect the new scope — researcher-author and PhD student personas, research workflow deliverable, research-integrity constraint family. Requires explicit user approval (per the project's body-edit rule).
2. **Run `/cg-plan`** with this brainstorm as input. The plan will inherit the Deep scope and break the work into the eight phases above with concrete tasks and acceptance criteria per phase.
3. **Run `/cg-plan-review`** on the resulting plan before implementation, because the module-system phase has cross-cutting impact on every existing file.
4. **Register a new milestone** in `roadmap.json` titled `compound-research` with each phase as a feature. Status: `planned`.
5. **Stay on the `compound-research` branch** through implementation. Merge to `main` only after Phase 8 is complete and the full test suite is green.

## Side Ideas Captured

The following adjacent ideas surfaced during the brainstorm but are explicitly deferred to later modules or future work:

- **Bayesian workflow module** (Stan/JAGS/brms support) — separate future module
- **Causal ML module** (double ML, causal forests, DR-Learner) — separate future module
- **Automated literature review** — distinct enough to be its own future feature, possibly its own module
- **Journal-specific style packages** — additive to `cr-skill-publication-output` once core works
- **Real-time multi-user collaboration** — out of scope; teams use git
- **Survey/sampling design module** — separate future module
