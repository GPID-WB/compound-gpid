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
| `/cg-setup` | Claude Haiku 4.5 | Configure project or load context for returning projects |
| `/cg-strategy` | Claude Opus 4.6 | Full project visioning and direction-setting. Structures ideas into milestones, or rethinks the roadmap mid-project. Dispatches `@cg-roadmap` for all writes. **Requires `compound-gpid.md`** — run `/cg-setup` first. |
| `/cg-brainstorm` | Claude Opus 4.6 | Clarify fuzzy requirements through guided questions |
| `/cg-plan` | Claude Opus 4.6 | Research + structured implementation plan |
| `/cg-work` | Claude Sonnet 4.6 | Step-by-step implementation from plan |
| `/cg-fixbug` | Claude Sonnet 4.6 | Structured bug-fix: reproduce, diagnose, fix, verify, document |
| `/cg-review` | Mixed | Multi-agent code review with P0/P1/P2/P3 findings |
| `/cg-fix-triage [IDs\|PRIORITY\|--migrate]` | Claude Sonnet 4.6 | Apply review findings by ID or priority level. Use `--migrate` to backfill per-finding status tracking on legacy review files. |
| `/cg-compound` | Claude Sonnet 4.6 | Capture solutions as reusable knowledge |
| `/cg-resume` | Claude Haiku 4.5 | Load context, check schema version, scan pending work, and resume interrupted sessions |

> **Model selection**: See [Model Guide](model-guide.md) for tier assignments, decision criteria, and override guidance for all 22 prompt and agent files.

> **Project Charter**: All /cg-* prompts automatically read compound-gpid.md at session start (if it exists). If missing, prompts remind you to run /cg-setup to optionally create one. Prompts work without a charter -- the reminder is advisory.

### Plugin Development (developer-only)

> These prompts are **not distributed** to user projects via junctions. They live at the `compound-gpid` repo root and are only available when working inside the compound-gpid repository itself.

| Prompt | Model | Purpose |
|--------|-------|---------|
| `/cg-release` | Claude Sonnet 4.6 | Create a GitHub Release for compound-gpid. Detects next semver tag, drafts release notes from `.cg-docs/`, checks `SCHEMA_VERSION`, and publishes to GitHub Releases. |

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
| `cg-learnings-researcher` | Cross-reference past solutions (thorough only) | Haiku 4.5 |

> All review agents are dispatched exclusively by `/cg-review`. They are NOT user-invokable and do not appear in the Copilot Chat agent dropdown.

> ℹ️ For model assignment rationale, tier criteria, and override guidance, see [Model Guide](model-guide.md).

## Roadmap Agent

| Agent | Focus | Model | User-invokable |
|-------|-------|-------|----------------|
| `@cg-roadmap` | Manages `roadmap.json`: add/remove milestones and features, link plans, update statuses | Haiku 4.5 | **Yes** |

> `@cg-roadmap` is the **only** agent users interact with directly. Invoke it in Copilot Chat to manage your project roadmap. Other prompts (`/cg-plan`, `/cg-work`, `/cg-brainstorm`) dispatch it automatically for roadmap updates (when `roadmap.json` exists).

### `roadmap.json` Schema

| Field | Type | Values |
|-------|------|--------|
| `milestones[].status` | derived | `planned`, `in-progress`, `done` |
| `features[].status` | set | `idea`, `planned`, `active`, `done` |

Milestone status is always derived from features (never set directly). Feature `active` maps to milestone `in-progress`. IDs are kebab-case and immutable after creation. `features[].plan` is a nullable path to a `.cg-docs/plans/` file.

---

## Skills

| Skill | Contents |
|-------|---------|
| `cg-skill-setup` | Project configuration wizard |
| `cg-skill-r-collapse` | **collapse statistical computing**: `fmean`/`fsum`/`fmedian`/`fnth` and all Fast Statistical Functions, GRP objects, TRA transformation types, `fwithin`/`fbetween`/`fscale`, `flag`/`fdiff`/`fgrowth`, `collap()`, `fsummarise`/`fmutate`. Dialect-neutral: works on data.table, tibble, and data.frame. |
| `cg-skill-r-datatable` | **data.table manipulation**: `DT[i,j,by]` syntax, `:=` in-place mutation, `fread`/`fwrite`, joins, `melt`/`dcast` reshaping, `.SD`/`.SDcols`, `fifelse`/`fcase`/`fcoalesce`, keys and indices. |
| `cg-skill-r-tidyverse` | **tidyverse patterns**: dplyr 1.2+ (`.by`, `join_by`, `across`/`pick`/`reframe`), native pipe `\|>`, `pivot_longer`/`pivot_wider`, `readr` I/O, `stringr`, `purrr`. Load for `r-syntax: "tidyverse"` projects. |
| `cg-skill-r-visualization` | **ggplot2 + wbplot**: World Bank visualization conventions, `theme_wb()`, `WBCOLORS`, `scale_color_wb_d()`, `scale_fill_wb_c()`, GPID chart types. |
| `cg-skill-r-analytical` | **Analytical domain patterns**: `haven` (Stata migration), `fixest` (econometrics), `modelsummary` (tables), welfare/poverty measurement, FGT indices, survey analysis. Syntax-neutral — works with any dialect. |
| `cg-skill-r-technical` | **Infrastructure & packages**: roxygen2, package dev, `plumber` APIs, `shiny`, `targets` pipelines, `httr2` clients, `renv`/`pak`. Syntax-neutral. |
| `cg-skill-r-shared` | Base R style rules universal to all dialects: `<-` assignment, `snake_case`, `TRUE`/`FALSE`, `rlang`/`cli` error handling. |
| `cg-skill-r-testing` | testthat 3+ patterns: `test_that()`, `describe()`/`it()`, fixtures, mocking (`local_mocked_bindings()`), snapshots, BDD-style testing. Dialect-aware: data.table examples for collapse/data.table projects, tibble examples for tidyverse projects. |
| `cg-skill-python-best-practices` | polars, numpy, pytest, type hints, `uv`/`poetry` |
| `cg-skill-stata-best-practices` | Comprehensive Stata reference: universal coding principles (compound quotes, macro expansion traps, stored results, `subpop()` vs `if`, clustering), data management, econometrics, causal inference, graphics, Mata, reproducibility (`repkit`: `repado`, `reproot`, `reprun`, `repscan`, `lint`), and 21 community packages (`reghdfe`, `estout`, `did`, `rdrobust`, etc.). ALWAYS load when writing or reviewing `.do` or `.ado` files. |
| `cg-skill-git-workflow` | Branching, commits, PR templates, `.gitignore` |
| `cg-skill-brainstorming` | Requirement elicitation and decision capture |
| `cg-skill-compound-docs` | Knowledge capture and categorization system |

---

## Configuration

Run `/cg-setup` in Copilot Chat after running `cg-link`. The prompt asks:
- **Language**: R, Python, Stata, or any combination
- **R syntax dialect** (if R is selected): `data.table-collapse` (default) or `tidyverse`
- **Project type**: Package, analysis, dashboard, API, tool
- **Review depth**: Light, standard, or thorough
- **Project charter** (optional): project name, objective, deliverables, constraints

This creates `compound-gpid.local.md` (gitignored, user-specific config) and optionally
`compound-gpid.md` (committed, shared project charter) in your project root, and scaffolds
the `.cg-docs/` directory.

### Configuration Fields

All fields are stored as YAML frontmatter in `compound-gpid.local.md`:

| Field | Values | Description |
|-------|--------|-------------|
| `language` | `"r"`, `"python"`, `"stata"`, `"both"`, or combination | Language(s) used in the project |
| `r-syntax` | `"data.table-collapse"` (default), `"tidyverse"` | R dialect for skill routing. Determines which R syntax skills are loaded for `.R` files. Use `"tidyverse"` for projects with external coauthors who only know dplyr. |
| `project-type` | `"package"`, `"analysis"`, `"dashboard"`, `"api"`, `"tool"` | Project type |
| `review-depth` | `"light"`, `"standard"`, `"thorough"` | Depth of `/cg-review` (see Review Depth Tiers in `copilot-instructions.md`) |
| `cg-schema-version` | date string | Auto-managed by `cg-update`. Do not edit manually. |

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
├── compound-gpid.md          # Project charter (4 sections: Objective, Key Deliverables, Constraints, Current Focus). YAML: project-name, team, created, last-reviewed. Committed -- shared.
├── compound-gpid.local.md    # Your user config (gitignored)
├── roadmap.json              # Milestone & feature tracker (committed)
└── .cg-docs/                 # Compound GPID knowledge base (committed -- institutional memory)
    ├── archive/              # Archived charter sections removed by the user (not loaded at session start)
    ├── brainstorms/          # /cg-brainstorm outputs
    ├── plans/                # /cg-plan outputs
    ├── reviews/              # /cg-review outputs (review reports for /cg-fix-triage)
    ├── strategy/             # /cg-strategy session records
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

**Archive file format** (`.cg-docs/archive/charter-history.md`): Content removed from
the charter is appended with a date heading and source section label:

````markdown
## Archived YYYY-MM-DD
**Removed from**: <section name>
<removed content>
````

> **Something not working?** See [Troubleshooting](troubleshooting.md).

---

## `.cg-docs/` Document Frontmatter Schema

Each document type in `.cg-docs/` uses a defined set of `status` enum values. These are enforced
by convention now and will be validated automatically in a future `evals` milestone.

| Document type | Path | Valid `status` values |
|---------------|------|-----------------------|
| Brainstorm | `.cg-docs/brainstorms/` | `open`, `decided`, `abandoned` |
| Plan | `.cg-docs/plans/` | `draft`, `active`, `completed`, `abandoned` |
| Solution | `.cg-docs/solutions/` | `draft`, `applied` |
| Review | `.cg-docs/reviews/` | Per-finding status in `findings:` frontmatter key: `open`, `fixed`, `skipped` |

