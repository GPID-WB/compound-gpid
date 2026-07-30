---
project-name: "Compound GPID"
created: "2026-03-26"
last-reviewed: "2026-07-30"
---

# Compound GPID

## Objective

Compound GPID is a GitHub Copilot plugin that gives the World Bank's poverty statistics team a structured workflow for AI-assisted development — brainstorm, plan, code, review, extract lessons — so that every coding session produces both working code and reusable institutional knowledge. It's built for a mixed team of senior economists migrating from Stata to R and junior developers building data infrastructure, all of whom produce high-stakes official statistics where errors carry real institutional consequences.

## Key Deliverables

- The plugin itself — a set of files in `.github/` (prompts, agents, skills, instructions) distributed via directory junctions, plus PowerShell scripts (cg-link, cg-unlink, cg-update, install.ps1, create-release.ps1)
- Workflow prompts: /cg-setup, /cg-brainstorm, /cg-plan, /cg-work, /cg-review, /cg-fix-triage, /cg-compound, /cg-release, /cg-resume, /cg-fixbug
- Knowledge artifacts in `.cg-docs/` — brainstorms, implementation plans, and captured lessons organized by category (bugs, build-errors, performance-issues, testing-patterns, data-quality, environment-issues, git-workflows)
- Review reports from specialized agents (code quality, testing, architecture, etc.) at light/standard/thorough tiers
- R skills reference files (cg-skill-r-analytical for economists, cg-skill-r-technical for developers)
- GitHub Releases with automatic release notes generated from `.cg-docs/` entries

## Constraints

- Statistical correctness over speed — poverty statistics must be accurate; FGT indices must average over the entire population, welfare must be weighted, PPP vintages must match, negative welfare is impossible
- Never commit secrets or large data — API keys, tokens, credentials, `.Renviron`/`.env` files, and data files stay out of git
- Always commit lockfiles and institutional knowledge — `renv.lock`, `poetry.lock`, `uv.lock`, Stata's `code/ado/`, and the entire `.cg-docs/` directory must be version-controlled
- Document before confirmation is forbidden — verify fixes before capturing lessons in `.cg-docs/solutions/`; hard stops at test-failure and test-pass confirmation
- Fail loudly, never silently — explicit errors or warnings for missing data, null weights, missing artifacts; no silent fallbacks
- Conventional commits and feature branches — `type(scope): description` format required; work on branches, not main
- Every function gets documentation — roxygen2 for R, docstrings for Python, header blocks for Stata `.ado` files; parameters, return values, at least one example
- Respect review priority system — P0 blocks everything (security, PII, data corruption, incorrect published output); P1 blocks merge (correctness, validation); P2 should be fixed (performance, tests, docs); P3 is advisory

## Current Focus

Compound Research module ported to v1.0 and integrated with Brain, review routing, model catalog, context-loading contracts, active-state, and multi-target generation. Engineering milestones continue in parallel.
