# Reference

Quick reference for all Compound GPID commands, agents, skills, configuration, and file structure.

> See [Workflow](workflow.md) for a full explanation of each prompt step. See [Installation](installation.md) for setup instructions. See [Troubleshooting](troubleshooting.md) for known issues.

---

## PowerShell Commands

| Command | Where to run | Purpose |
|---------|-------------|---------|
| `cg-link` | Project root | Create per-subdirectory junctions in `.github/` - enables all Copilot prompts in this project |
| `cg-unlink` | Project root | Remove CG-managed junctions (existing `.github/` content is preserved) |
| `cg-update` | Anywhere | Update to latest (or stay on pinned version). Accepts optional version argument — see Version Management below. |
| `cg-update <version>` | Anywhere | Pin to a specific release tag, e.g. `cg-update v0.2.0` |
| `cg-update latest` | Anywhere | Unpin and return to tracking main |
| `cg-update --list` | Anywhere | Browse available GitHub Releases |

---

## Version Management

Compound GPID supports pinning to specific [GitHub Releases](https://github.com/GPID-WB/compound-gpid/releases) so you can choose between stability and bleeding-edge.

| Command | Effect | Persists? |
|---------|--------|-----------|
| `cg-update` | Use current preference (default: latest) | — |
| `cg-update v0.2.0` | Pin to release `v0.2.0` | Yes — writes to `.cg-version` |
| `cg-update latest` | Unpin and track `main` | Yes — writes to `.cg-version` |
| `cg-update --list` | Browse available releases | No |

**How it works:** the version preference is stored per-machine in `.cg-version` inside your global install directory. This file is gitignored. Pinned users see a yellow hint when a newer release is available at the end of every `cg-update` run.

> **Full details**: see the [Version Management](versioning.md) page.

---

## Copilot Chat Prompts

| Prompt | Model | Purpose |
|--------|-------|---------|
| `/cg-setup` | Claude Sonnet 4.6 | Configure project or load context for returning projects |
| `/cg-brainstorm` | Claude Opus 4.6 | Clarify fuzzy requirements through guided questions |
| `/cg-plan` | Claude Opus 4.6 | Research + structured implementation plan |
| `/cg-work` | Claude Sonnet 4.6 | Step-by-step implementation from plan |
| `/cg-fixbug` | Claude Sonnet 4.6 | Structured bug-fix: reproduce, diagnose, fix, verify, document |
| `/cg-review` | Mixed | Multi-agent code review with P1/P2/P3 findings |
| `/cg-compound` | Claude Sonnet 4.6 | Capture solutions as reusable knowledge |
| `/cg-resume` | Claude Sonnet 4.6 | Load context and pick up interrupted work |
| `/cg-release` | Claude Sonnet 4.6 | Create a GitHub Release. Detects next semver tag, drafts release notes, checks `SCHEMA_VERSION`, and publishes. **Developer-only** — lives at repo root, not junctioned to user projects. |

> **Project Charter**: All /cg-* prompts automatically read compound-gpid.md at session start (if it exists). If missing, prompts remind you to run /cg-setup to optionally create one. Prompts work without a charter -- the reminder is advisory.

---

## Review Agents

| Agent | Focus | Model |
|-------|-------|-------|
| `cg-code-quality` | Style, linting, DRY, naming | Haiku 4.5 |
| `cg-testing` | Coverage, edge cases, test quality | Haiku 4.5 |
| `cg-documentation` | roxygen2/docstrings/do-file headers, README, comments | Haiku 4.5 |
| `cg-version-control` | Commit hygiene, branching, secrets | Haiku 4.5 |
| `cg-reproducibility` | Lockfiles, relative paths, seeds, repkit | Haiku 4.5 |
| `cg-performance` | Vectorization, memory, algorithm complexity | Sonnet 4.6 |
| `cg-architecture` | Project structure, modularity, dependencies | Sonnet 4.6 |
| `cg-data-quality` | Input validation, types, missing values | Sonnet 4.6 |
| `cg-learnings-researcher` | Cross-reference past solutions (thorough only) | Sonnet 4.6 |

> All review agents are dispatched exclusively by `/cg-review`. They are NOT user-invokable and do not appear in the Copilot Chat agent dropdown.

## Roadmap Agent

| Agent | Focus | Model | User-invokable |
|-------|-------|-------|----------------|
| `@cg-roadmap` | Manages `roadmap.json`: add/remove milestones and features, link plans, update statuses | Sonnet 4.6 | **Yes** |

> `@cg-roadmap` is the **only** agent users interact with directly. Invoke it in Copilot Chat to manage your project roadmap. Other prompts (`/cg-plan`, `/cg-work`, `/cg-brainstorm`) dispatch it automatically for roadmap updates.

---

## Skills

| Skill | Contents |
|-------|---------|
| `cg-skill-setup` | Project configuration wizard |
| `cg-skill-r-technical` | **Infrastructure & packages**: `collapse`, `data.table`, `testthat`, roxygen2, `renv`/`pak`, package dev, `plumber`, `shiny`, `targets`, `httr2`. Preference hierarchy: collapse > data.table > tidyverse. |
| `cg-skill-r-analytical` | **Analysis patterns**: `collapse`, `data.table`, `haven`, `fixest`, `modelsummary`, `ggplot2`+`wbplot`, welfare/poverty measurement. Preference hierarchy: collapse > data.table > tidyverse. |
| `cg-skill-r-shared` | Shared R references (collapse anti-patterns) used by both analytical and technical skills |
| `cg-skill-python-best-practices` | polars, numpy, pytest, type hints, `uv`/`poetry` |
| `cg-skill-stata-best-practices` | Comprehensive Stata reference: universal coding principles (compound quotes, macro expansion traps, stored results, `subpop()` vs `if`, clustering), data management, econometrics, causal inference, graphics, Mata, reproducibility (`repkit`: `repado`, `reproot`, `reprun`, `repscan`, `lint`), and 21 community packages (`reghdfe`, `estout`, `did`, `rdrobust`, etc.). ALWAYS load when writing or reviewing `.do` or `.ado` files. |
| `cg-skill-git-workflow` | Branching, commits, PR templates, `.gitignore` |
| `cg-skill-brainstorming` | Requirement elicitation and decision capture |
| `cg-skill-compound-docs` | Knowledge capture and categorization system |

---

## Configuration

Run `/cg-setup` in Copilot Chat after running `cg-link`. The prompt asks:
- **Language**: R, Python, Stata, or any combination
- **Project type**: Package, analysis, dashboard, API, tool
- **Review depth**: Light, standard, or thorough
- **Project charter** (optional): project name, objective, deliverables, constraints

This creates `compound-gpid.local.md` (gitignored, user-specific config) and optionally
`compound-gpid.md` (committed, shared project charter) in your project root, and scaffolds
the `.cg-docs/` directory.

---

## Directory Structure

After linking and configuring, your project will contain:

```
your-project/
├── .github/
│   ├── prompts/              → junction to C:\WBG\.compound-gpid\.github\prompts\
│   ├── skills/               → junction to C:\WBG\.compound-gpid\.github\skills\
│   ├── agents/               → junction to C:\WBG\.compound-gpid\.github\agents\
│   ├── instructions/         → junction to C:\WBG\.compound-gpid\.github\instructions\
│   ├── copilot-instructions.md  # copied from global clone (managed marker)
│   └── workflows/            # your own GitHub Actions (untouched by cg-link)
├── compound-gpid.md          # Project charter (committed -- shared context)
├── compound-gpid.local.md    # Your user config (gitignored)
├── roadmap.json              # Milestone & feature tracker (committed)
└── .cg-docs/                 # Compound GPID knowledge base (committed -- institutional memory)
    ├── brainstorms/          # /cg-brainstorm outputs
    ├── plans/                # /cg-plan outputs
    └── solutions/            # /cg-compound outputs
        ├── build-errors/
        ├── bugs/
        ├── performance-issues/
        ├── testing-patterns/
        ├── data-quality/
        ├── environment-issues/
        └── git-workflows/
```

---

> **Something not working?** See [Troubleshooting](troubleshooting.md).

