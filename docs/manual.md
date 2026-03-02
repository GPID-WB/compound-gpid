# Compound GPID — User Manual

This manual explains how the Compound GPID system works and how to use it effectively.

## What Is Compound GPID?

Compound GPID is a structured AI-assisted workflow for data science projects. It uses GitHub Copilot's prompt, agent, and skill system to enforce a repeatable loop:

```
Brainstorm → Plan → Work → Review → Compound
```

Each step builds on the previous one. Over time, the knowledge captured in `docs/solutions/` makes future work faster and more consistent.

## Key Concepts

### Prompts

Prompts are **top-level workflow commands** you invoke in Copilot Chat. They orchestrate multi-step processes and produce outputs (documents, code, reviews).

| Prompt | Purpose |
|--------|---------|
| `/cg-brainstorm` | Clarify fuzzy requirements through guided Q&A |
| `/cg-plan` | Research the codebase and create a structured implementation plan |
| `/cg-work` | Implement a plan step by step, with tests and documentation |
| `/cg-review` | Run multi-agent code review with prioritized findings |
| `/cg-compound` | Capture a solved problem as reusable knowledge |

**Prompts are NOT meant to be used interactively.** You invoke a prompt, answer its questions when asked, and let it run to completion. Do not try to steer or micromanage the process — the prompt has a defined workflow it follows.

### Agents

Agents are **specialized reviewers** invoked by the `/cg-review` prompt. Each agent focuses on one aspect of code quality.

| Agent | Focus |
|-------|-------|
| `cg-code-quality` | Style, linting, DRY, naming |
| `cg-testing` | Test coverage, edge cases, quality |
| `cg-documentation` | roxygen2/docstrings, README, comments |
| `cg-version-control` | Commit hygiene, branching, secrets |
| `cg-reproducibility` | Lockfiles, relative paths, seeds |
| `cg-performance` | Vectorization, memory, algorithm complexity |
| `cg-architecture` | Project structure, modularity, dependencies |
| `cg-data-quality` | Input validation, types, missing values |
| `cg-learnings-researcher` | Cross-reference past solutions and brainstorms |

**Agents are NOT meant to be used interactively.** They are dispatched by the `/cg-review` prompt based on your configured review depth. You do not invoke agents directly in normal use.

### Skills

Skills are **reference knowledge** that prompts and agents draw on. They contain best practices, patterns, templates, and workflows for specific topics.

| Skill | Contents |
|-------|----------|
| `cg-skill-setup` | Project configuration wizard |
| `cg-skill-r-best-practices` | `data.table`, `ggplot2`, `testthat`, roxygen2, `renv` |
| `cg-skill-python-best-practices` | polars, numpy, pytest, type hints, `uv`/`poetry` |
| `cg-skill-git-workflow` | Branching strategy, commit conventions, PR templates |
| `cg-skill-brainstorming` | Requirement elicitation and decision capture workflows |
| `cg-skill-compound-docs` | Knowledge capture schema and categorization |

**Skills are NOT intended for interactive use**, although they technically can be referenced. They exist to provide structured knowledge to prompts and agents — think of them as documentation that the AI reads, not commands you run.

## Prompts vs. Skills vs. Agents

| Aspect | Prompts | Agents | Skills |
|--------|---------|--------|--------|
| **What they are** | Workflow commands | Specialized reviewers | Reference knowledge |
| **How you use them** | Type `/cg-brainstorm` in chat | Dispatched by `/cg-review` | Referenced by prompts/agents |
| **Interactive?** | No — follow the workflow | No — automated | No — passive reference |
| **Prefix** | `cg-` | `cg-` | `cg-skill-` |
| **Location** | `.github/prompts/` | `.github/agents/` | `.github/skills/` |
| **Produce output?** | Yes (docs, code, reviews) | Yes (review findings) | No (consumed by others) |

## The Workflow Loop

### 1. Brainstorm (`/cg-brainstorm`)

**When**: Requirements are fuzzy, you're not sure what to build, or multiple approaches are possible.

**What happens**: The prompt scans your project, then asks you clarifying questions one at a time. After gathering context, it proposes 2–3 approaches with pros/cons. Once you pick one, it saves a decision document to `docs/brainstorms/`.

**Output**: `docs/brainstorms/YYYY-MM-DD-<title>.md`

### 2. Plan (`/cg-plan`)

**When**: After brainstorming (or when you already know what to build).

**What happens**: The prompt reads any relevant brainstorm, researches your codebase, and creates a step-by-step implementation plan with files to create/modify, tests to write, and acceptance criteria.

**Output**: `docs/plans/YYYY-MM-DD-<title>.md`

### 3. Work (`/cg-work`)

**When**: After a plan exists.

**What happens**: The prompt loads the most recent plan and implements it step by step — writing code, tests, and documentation. It checks against acceptance criteria and suggests commit messages.

**Output**: Code, tests, documentation changes.

### 4. Review (`/cg-review`)

**When**: After implementing changes.

**What happens**: The prompt determines which agents to dispatch based on your review depth (light/standard/thorough), runs them against changed files, collects findings, and presents them prioritized as P1 (critical), P2 (important), P3 (minor).

**Output**: Prioritized review report with suggested fixes.

### 5. Compound (`/cg-compound`)

**When**: After solving a non-trivial problem.

**What happens**: The prompt captures the problem, root cause, solution, and prevention strategy as a structured document. This feeds the `cg-learnings-researcher` agent in future thorough reviews.

**Output**: `docs/solutions/<category>/YYYY-MM-DD-<title>.md`

## Configuration

### Initial Setup

Run `/cg-setup` in Copilot Chat. This creates `compound-gpid.local.md` with your preferences:

- **Language**: R, Python, or both
- **Project type**: Package, analysis, dashboard, API, tool
- **Review depth**: Light, standard, or thorough

### Review Depth Tiers

| Tier | Agents Run | Use When |
|------|-----------|----------|
| **Light** | `cg-code-quality` + `cg-testing` | Quick fixes, small changes |
| **Standard** | All 8 agents | Most work (default) |
| **Thorough** | All 8 + `cg-learnings-researcher` | Major features, refactors |

## Naming Conventions

All components use a `cg-` prefix to distinguish them from other Copilot prompts, agents, or skills you may have in your project:

- **Prompts**: `cg-<name>.prompt.md` (e.g., `cg-brainstorm.prompt.md`)
- **Agents**: `cg-<name>.agent.md` (e.g., `cg-code-quality.agent.md`)
- **Skills**: `cg-skill-<name>/` (e.g., `cg-skill-r-best-practices/`)

## File Locations

```
.github/
├── prompts/              # Workflow commands
│   ├── cg-brainstorm.prompt.md
│   ├── cg-plan.prompt.md
│   ├── cg-work.prompt.md
│   ├── cg-review.prompt.md
│   └── cg-compound.prompt.md
├── agents/               # Specialized reviewers
│   ├── cg-architecture.agent.md
│   ├── cg-code-quality.agent.md
│   ├── cg-data-quality.agent.md
│   ├── cg-documentation.agent.md
│   ├── cg-learnings-researcher.agent.md
│   ├── cg-performance.agent.md
│   ├── cg-reproducibility.agent.md
│   ├── cg-testing.agent.md
│   └── cg-version-control.agent.md
├── skills/               # Reference knowledge
│   ├── cg-skill-brainstorming/
│   ├── cg-skill-compound-docs/
│   ├── cg-skill-git-workflow/
│   ├── cg-skill-python-best-practices/
│   ├── cg-skill-r-best-practices/
│   └── cg-skill-setup/
├── instructions/         # Language-specific coding standards
│   ├── python.instructions.md
│   └── r.instructions.md
└── copilot-instructions.md  # Global project instructions
```

## Output Locations

```
docs/
├── brainstorms/          # /cg-brainstorm outputs
├── plans/                # /cg-plan outputs
└── solutions/            # /cg-compound outputs
    ├── build-errors/
    ├── data-quality/
    ├── environment-issues/
    ├── git-workflows/
    ├── performance-issues/
    └── testing-patterns/
```
