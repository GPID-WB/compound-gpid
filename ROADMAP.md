# Compound GPID — Roadmap

## Phase 1: Code Quality Foundation (In Progress)

Focus: Coding best practices, testing, documentation, version control, system stability.

- [x] Core workflow prompts (cg-brainstorm, cg-plan, cg-work, cg-review, cg-compound)
- [x] 8 review agents + learnings researcher (all prefixed `cg-`)
- [x] R technical skill (`cg-skill-r-technical`) — collapse, data.table, testthat, roxygen2, package dev, plumber, shiny, targets
- [x] R analytical skill (`cg-skill-r-analytical`) — collapse, data.table, haven, fixest, modelsummary, ggplot2+wbplot, welfare measurement
- [x] Python best practices skill (`cg-skill-python-best-practices`)
- [x] Git workflow skill (`cg-skill-git-workflow`)
- [x] Brainstorming skill (`cg-skill-brainstorming`)
- [x] Compound docs skill (`cg-skill-compound-docs`)
- [x] Setup skill (`cg-skill-setup`) with review depth tiers
- [x] Team-wide coding standards via `copilot-instructions.md`
- [x] Stata core skill (`cg-skill-stata-core`) with macro system, program scoping, data management, and reproducibility
- [x] Stata research skill (`cg-skill-stata-research`) — phased research workflow, survey design, poverty measurement, causal inference, publication output
- [x] Trilingual R/Python/Stata support across all agents and prompts
- [x] Migrate knowledge folder from `docs/` → `.cg-docs/` to avoid project namespace collisions
- [x] `/cg-resume` prompt — pick up interrupted work by scanning in-progress plans and recent git history
- [x] Structural schema versioning — track `cg-schema-version` per project so `cg-update` knows which migrations to apply

## Phase 2: Analytical Quality

Focus: Statistical and analytical rigor, data analysis workflows, and results communication.

- [ ] Statistical validity review agent (p-hacking, multiple comparisons, sample size)
- [ ] Methodology review agent (identification strategy, robustness checks)
- [ ] Visualization best practices agent (`ggplot2` conventions, accessibility, clarity)
- [ ] Data exploration skill (summary statistics, distributions, outliers)
- [ ] Econometrics patterns skill (common model specifications, diagnostics)
- [ ] Data analysis workflow prompt — guided EDA, hypothesis articulation, iterative analysis loop
- [ ] Insights generation agent — extract key findings from analysis output, draft interpretation
- [ ] Writing support skill — structure results sections, executive summaries, policy briefs
- [ ] `/cg-confidence` check — at any point in the loop, honestly assess what the analysis knows vs. doesn't know (inspired by [Compound Knowledge](https://github.com/EveryInc/compound-knowledge-plugin))

## Phase 3: Research Workflow

Focus: End-to-end research support, writing, and dissemination.

- [ ] Literature scout agent (search papers, summarize findings)
- [ ] Data catalog researcher agent (find relevant datasets)
- [ ] Quarto/RMarkdown writing support skill
- [ ] Paper/report structure skill (World Bank style)
- [ ] Reproducibility audit agent (end-to-end pipeline verification)
- [ ] Research design skill (causal inference, identification strategies, power calculations)
- [ ] Results narration prompt — translate tables and charts into plain-language findings
- [ ] Revision workflow — track reviewer comments, map them to document sections, implement changes

## Phase 4: Domain Knowledge

Focus: Development economics domain expertise.

- [ ] Survey methodology skill (sampling, weights, design effects)
- [ ] Poverty measurement skill (poverty lines, PPP, inequality indices)
- [x] Stata research skill (`cg-skill-stata-research`) — survey econometrics, welfare aggregates, poverty measurement, PPP conversion
- [ ] Spatial analysis skill (geographic data, mapping, spatial joins)
- [ ] Microdata handling skill (anonymization, harmonization)
- [ ] World Bank data API skill (WDI, microdata catalog)

## Phase 5: Team Scaling

Focus: Multi-project and team-wide compounding.

- [ ] Integrate legacy GPID analytical prompts — port existing prompts from GPID projects into the `cg-` system, adapting to the new structure and formats
- [ ] Compound Knowledge integration — adapt `/kw:confidence`, `/kw:review` (strategic alignment + data accuracy) concepts from [EveryInc/compound-knowledge-plugin](https://github.com/EveryInc/compound-knowledge-plugin) for the VS Code Copilot environment
- [ ] Team onboarding agent (new member orientation)
- [ ] Project template generator (scaffold new projects from patterns)
- [ ] Dashboard/API deployment skill
- [ ] Package publishing skill (CRAN, PyPI)

---

## Archived / Deferred

Ideas that were considered and intentionally deferred or removed from scope.

- ~~Cross-project knowledge sharing (shared `docs/solutions/` across repos)~~ — *Archived 2026-03-05*. Each project's knowledge base is intentionally local. Sharing across repos adds synchronization complexity without clear benefit for the current team structure. Revisit if the team scales significantly.
