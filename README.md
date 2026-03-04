> [!CAUTION]
> **⚠️ WORK IN PROGRESS — DO NOT USE IN PRODUCTION**
>
> This project is under active development and is not yet ready for use.
> Prompts, agents, skills, and conventions may change without notice.
> This banner will be removed when the system is stable.

# Compound GPID

A compound engineering plugin for data science teams using VS Code/Positron with GitHub Copilot. Inspired by the [Compound Engineering Philosophy](https://every.to/guides/compound-engineering).

## Philosophy

> Each unit of work should make subsequent units easier — not harder.

This plugin implements the **Brainstorm → Plan → Work → Review → Compound** loop, focused on coding best practices, testing, documentation, and version control for R (`data.table` + `ggplot2`) and Python.

## Installation

### Step 1: Clone (one-time per machine)

```powershell
git clone https://github.com/GPID-WB/compound-gpid.git "$env:USERPROFILE\.compound-gpid"
```

### Step 2: Install (one-time per machine)

```powershell
& "$env:USERPROFILE\.compound-gpid\install.ps1"
```

This registers the `cg-link`, `cg-unlink`, and `cg-update` commands in your PowerShell profile.

> **After install**: restart your terminal or run `. $PROFILE` for the commands to take effect.

> **Execution policy**: if PowerShell blocks the script, run:
> `powershell -ExecutionPolicy Bypass -File "$env:USERPROFILE\.compound-gpid\install.ps1"`

### Step 3: Link your project (once per project)

From your project root:

```powershell
cg-link
```

This creates a **directory junction** from `.github/` in your project to the shared `%USERPROFILE%\.compound-gpid\.github\`, making all prompts, agents, and skills visible to VS Code. It also adds `.github` to your `.gitignore` automatically.

> **Developer Mode**: if `cg-link` fails, enable Developer Mode in Windows Settings:
> Settings → System → For developers → Developer Mode (On)

### Step 4: Configure your project

Open your project in VS Code and run in Copilot Chat:

```
/cg-setup
```

This configures language preferences, project type, and review depth, and scaffolds the `docs/` directory.

## Updating

From any terminal:

```powershell
cg-update
```

This runs `git pull` in the global clone. Because all projects share the same `.github/` folder via junctions, updates are instantly visible in every linked project — no per-project update step needed.

## Workflow

### The Loop

```
Brainstorm → Plan → Work → Review → Compound
```

| Step | Prompt | Model | Purpose |
|------|--------|-------|---------|| **Setup** | `/cg-setup` | Claude Sonnet 4.6 | Configure project or load context for returning projects || **Brainstorm** | `/cg-brainstorm` | Claude Opus 4.6 | Clarify fuzzy requirements through guided questions |
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

## PowerShell Commands

| Command | Where to run | Purpose |
|---------|-------------|--------|
| `cg-link` | Project root | Create `.github` junction — enables all Copilot prompts in this project |
| `cg-unlink` | Project root | Remove `.github` junction (restores backup if one was made) |
| `cg-update` | Anywhere | Pull latest Compound GPID updates (applies to all linked projects) |

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
├── .github               → junction to %USERPROFILE%\.compound-gpid\.github\
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
