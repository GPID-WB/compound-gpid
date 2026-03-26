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
- [x] Stata best-practices skill (`cg-skill-stata-best-practices`) — unified reference covering universal coding principles, data management, econometrics, causal inference, reproducibility tools (repkit), survey design, and 21+ community packages; replaces former `cg-skill-stata-core` and `cg-skill-stata-research`
- [x] Trilingual R/Python/Stata support across all agents and prompts
- [x] Migrate knowledge folder from `docs/` → `.cg-docs/` to avoid project namespace collisions
- [x] `/cg-resume` prompt — pick up interrupted work by scanning in-progress plans and recent git history
- [x] Structural schema versioning — track `cg-schema-version` per project so `cg-update` knows which migrations to apply
- [x] Project charter file (`compound-gpid.md`) -- shared project context
      read by all prompts at session start

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

End-to-end research support: literature search, data exploration, reproducibility audits, writing support, and revision tracking. Specific features will be scoped after Phase 2 tools are in active use by the analytical team.

## Phase 4: Domain Knowledge

Deep development economics domain expertise: survey methodology, poverty measurement, PPP conversion, spatial analysis, and World Bank data API integration. Specific features will be scoped based on gaps identified during Phase 2 analytical work.

## Phase 5: Team Scaling

Multi-project and team-wide compounding: legacy prompt integration, team onboarding, project templates, and publishing workflows. Specific features will be scoped when adoption from earlier phases provides signal on what the team actually needs.

---

## Archived / Deferred

Ideas that were considered and intentionally deferred or removed from scope.

- ~~Cross-project knowledge sharing (shared `docs/solutions/` across repos)~~ — *Archived 2026-03-05*. Each project's knowledge base is intentionally local. Sharing across repos adds synchronization complexity without clear benefit for the current team structure. Revisit if the team scales significantly.
