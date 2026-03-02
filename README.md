> [!CAUTION]
> **⚠️ WORK IN PROGRESS — DO NOT USE IN PRODUCTION**
>
> This project is under active development and is not yet ready for use.
> APIs, prompts, and conventions may change without notice.
> This banner will be removed when the system is stable.

# Compound GPID

A compound engineering plugin for data science teams using VS Code/Positron with GitHub Copilot. Inspired by the [Compound Engineering Philosophy](https://every.to/guides/compound-engineering).

## Philosophy

> Each unit of work should make subsequent units easier — not harder.

This plugin implements the **Brainstorm → Plan → Work → Review → Compound** loop, focused on coding best practices, testing, documentation, and version control for R (`data.table` + `ggplot2`) and Python.

## Installation

Each team member clones this repo independently, then creates a **directory junction** in their project to link it.

### Step 1: Clone the repo

```powershell
git clone https://github.com/your-org/compound-gpid.git "C:\tools\compound-gpid"
```

### Step 2: Link to your project

From your project root (run as Administrator or with Developer Mode enabled):

```powershell
# Remove existing .github if present (back up first!)
mklink /J ".github" "C:\tools\compound-gpid\.github"
```

This creates a **junction** (no elevated privileges required on most Windows 10/11 systems with Developer Mode) that makes `compound-gpid/.github/` appear as your project's `.github/` directory.

### Step 3: Run setup

In Copilot Chat, type:

```
/cg-setup
```

This will ask you about your preferred language, project type, and review depth, then write a `compound-gpid.local.md` config file in your project root.

### Step 4: Add to `.gitignore`

```gitignore
# Compound GPID local config (user-specific)
compound-gpid.local.md
```

## Workflow

### The Loop

```
Brainstorm → Plan → Work → Review → Compound
```

| Step | Prompt | Model | Purpose |
|------|--------|-------|---------|
| **Brainstorm** | `/cg-brainstorm` | Claude Opus 4.6 | Clarify fuzzy requirements through guided questions |
| **Plan** | `/cg-plan` | Claude Opus 4.6 | Research + structured implementation plan |
| **Work** | `/cg-work` | Claude Sonnet 4.6 | Step-by-step implementation from plan |
| **Review** | `/cg-review` | Mixed (see below) | Multi-agent code review with P1/P2/P3 findings |
| **Compound** | `/cg-compound` | Claude Sonnet 4.6 | Capture solutions as reusable knowledge |

### Review Agents

| Agent | Focus | Model |
|-------|-------|-------|
| `cg-code-quality` | Style, linting, DRY, naming | Haiku 4.5 |
| `cg-testing` | Coverage, edge cases, test quality | Haiku 4.5 |
| `cg-documentation` | roxygen2/docstrings, README | Haiku 4.5 |
| `cg-version-control` | Commit hygiene, branching, secrets | Haiku 4.5 |
| `cg-reproducibility` | Lockfiles, paths, seeds | Haiku 4.5 |
| `cg-performance` | Vectorization, memory, algorithms | Sonnet 4.6 |
| `cg-architecture` | Structure, modularity, dependencies | Sonnet 4.6 |
| `cg-data-quality` | Validation, types, missing values | Sonnet 4.6 |

### Review Depth Tiers

| Tier | Agents | When to use |
|------|--------|-------------|
| **Light** | `cg-code-quality` + `cg-testing` | Quick fixes, small changes |
| **Standard** | All 8 review agents | Default for most work |
| **Thorough** | All 8 + `cg-learnings-researcher` | Major features, refactors |

## Skills

| Skill | Description |
|-------|-------------|
| `cg-skill-setup` | Configure language, project type, review depth |
| `cg-skill-r-best-practices` | `data.table`, `ggplot2`, `testthat`, roxygen2, `renv` |
| `cg-skill-python-best-practices` | PEP 8, pytest, type hints, polars, `uv`/`poetry` |
| `cg-skill-git-workflow` | Branching, commits, PR templates, `.gitignore` |
| `cg-skill-brainstorming` | Requirement elicitation and decision capture |
| `cg-skill-compound-docs` | Knowledge capture and categorization system |

## Directory Structure (in your project)

After using the plugin, your project will accumulate:

```
your-project/
├── .github/                  → junction to compound-gpid/.github/
├── compound-gpid.local.md    # Your project config (gitignored)
└── docs/
    ├── brainstorms/          # /cg-brainstorm outputs
    ├── plans/                # /cg-plan outputs
    └── solutions/            # /cg-compound outputs
        ├── build-errors/
        ├── performance-issues/
        ├── testing-patterns/
        ├── data-quality/
        ├── environment-issues/
        └── git-workflows/
```

## Phase 2 Roadmap

See [ROADMAP.md](ROADMAP.md) for planned future capabilities.

## Documentation

See the [User Manual](docs/manual.md) for detailed usage instructions, including the differences between prompts, agents, and skills.

## License

MIT
