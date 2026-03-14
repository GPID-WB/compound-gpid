# Compound GPID — User Manual

This manual explains how the Compound GPID system works and how to use it effectively.

## What Is Compound GPID?

Compound GPID is a structured AI-assisted workflow for data science projects. It uses GitHub Copilot's prompt, agent, and skill system to enforce a repeatable loop:

```
Brainstorm → Plan → Work → Review → Compound
```

Each step builds on the previous one. Over time, the knowledge captured in `.cg-docs/solutions/` makes future work faster and more consistent.

## Getting Started

1. **Install** (once per machine): Clone the repo to `C:\WBG\.compound-gpid` and run `install.ps1` — see [README.md](../README.md) for the exact commands. This creates `cg-link`, `cg-update`, and `cg-unlink` as batch wrappers on your PATH.
2. **Link** (once per project): From your project root in a terminal, run `cg-link`. This creates the `.github` junction that makes all Copilot prompts available.
3. **Configure** (once per project): Open your project in VS Code and run `/cg-setup` in Copilot Chat. This creates your `compound-gpid.local.md` config file and scaffolds the `docs/` structure.
4. **Start working**: Use `/cg-brainstorm` if requirements are fuzzy, `/cg-plan` if you know what to build, or `/cg-work` if a plan already exists.

## Key Concepts

### Prompts

Prompts are **top-level workflow commands** you invoke in Copilot Chat. They orchestrate multi-step processes and produce outputs (documents, code, reviews).

| Prompt | Purpose |
|--------|---------|
| `/cg-setup` | Configure project (new) or load context (returning) |
| `/cg-brainstorm` | Clarify fuzzy requirements through guided Q&A |
| `/cg-plan` | Research the codebase and create a structured implementation plan |
| `/cg-work` | Implement a plan step by step, with tests and documentation |
| `/cg-review` | Run multi-agent code review with prioritized findings |
| `/cg-compound` | Capture a solved problem as reusable knowledge |
| `/cg-resume` | Load context from an interrupted session and continue work |

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
| **How you use them** | Type `/cg-setup`, `/cg-brainstorm`, etc. in chat | Dispatched by `/cg-review` | Referenced by prompts/agents |
| **Interactive?** | No — follow the workflow | No — automated | No (passive by design; can be referenced directly) |
| **Prefix** | `cg-` | `cg-` | `cg-skill-` |
| **Location** | `.github/prompts/` | `.github/agents/` | `.github/skills/` |
| **Produce output?** | Yes (docs, code, reviews) | Yes (review findings) | No (consumed by others) |

## The Workflow Loop

### 1. Brainstorm (`/cg-brainstorm`)

**When**: Requirements are fuzzy, you're not sure what to build, or multiple approaches are possible.

**What happens**: The prompt scans your project, then asks you clarifying questions one at a time. After gathering context, it proposes 2–3 approaches with pros/cons. Once you pick one, it saves a decision document to `.cg-docs/brainstorms/`.

**Output**: `.cg-docs/brainstorms/YYYY-MM-DD-<title>.md`

### 2. Plan (`/cg-plan`)

**When**: After brainstorming (or when you already know what to build).

**What happens**: The prompt reads any relevant brainstorm, researches your codebase, and creates a step-by-step implementation plan with files to create/modify, tests to write, and acceptance criteria.

**Output**: `.cg-docs/plans/YYYY-MM-DD-<title>.md`

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

**Output**: `.cg-docs/solutions/<category>/YYYY-MM-DD-<title>.md`

### 6. Resume (`/cg-resume`)

**When**: At the start of a session when you have interrupted work — an active plan, a decided-but-unplanned brainstorm, or staged/unstaged git changes.

**What happens**: The prompt first checks that your schema version is up to date (if not, it instructs you to run `cg-update`). It then scans `.cg-docs/plans/` for active plans, `.cg-docs/brainstorms/` for decided brainstorms without a plan, and inspects `git status`/`git log` for in-progress code changes. It presents a structured summary and suggests the most logical next action with numbered options.

**Output**: A structured context summary and a suggested continuation path.

## Configuration

### Initial Setup

Run `/cg-setup` in Copilot Chat (after running `cg-link` in your terminal to create the junction). The prompt will ask you three questions:

- **Language**: R, Python, or both
- **Project type**: Package, analysis, dashboard, API, tool
- **Review depth**: Light, standard, or thorough

It then creates `compound-gpid.local.md` and scaffolds the `.cg-docs/` directory.

### Review Depth Tiers

| Tier | Agents Run | Use When |
|------|-----------|----------|
| **Light** | `cg-code-quality` + `cg-testing` | Quick fixes, small changes |
| **Standard** | All 8 agents | Most work (default) |
| **Thorough** | All 8 + `cg-learnings-researcher` | Major features, refactors |

## PowerShell Commands

These commands are registered in your PowerShell profile by `install.ps1` and are available from any terminal after installation.

| Command | Where to run | Purpose |
|---------|-------------|--------|
| `cg-link` | Project root | Create `.github` junction — enables all Copilot prompts |
| `cg-unlink` | Project root | Remove `.github` junction (restores backup if one was made) |
| `cg-update` | Anywhere | Pull latest Compound GPID updates |

`cg-link` also automatically adds `.github` to the project's `.gitignore`, since the junction points to an external repo and should not be committed.

## Updating Compound GPID

Run `cg-update` from any terminal. This does a `git pull` in the global clone at `C:\WBG\.compound-gpid`. Because all linked projects share the same `.github/` directory via junctions, the update is instantly visible in every project — no per-project update step is needed.

To check what changed: `cg-update` shows the commit log of new commits when an update is available.

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
│   ├── cg-compound.prompt.md
│   └── cg-resume.prompt.md
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

## Troubleshooting

### `cg-update` fails with "Updated 0 paths from the index"

**Symptom**:
```
cg-update
Checking for updates...
update.ps1 : Update failed: Updated 0 paths from the index
```

**Cause**: The global clone at `C:\WBG\.compound-gpid` has an old version of `update.ps1` that crashes on PowerShell 5.1 before it can pull the fix.

**Fix — run these two commands once in any terminal**:
```powershell
git -C "C:\WBG\.compound-gpid" checkout . 2>$null  # suppress stderr (PS5.1 stderr-to-error promotion)
git -C "C:\WBG\.compound-gpid" pull --ff-only
```

This manually updates the global clone. After that, `cg-update` works normally from all projects — no further action needed.

> **If `pull --ff-only` fails** with `fatal: Not possible to fast-forward`, the global clone has an unexpected local commit. Fix it with:
> ```powershell
> git -C "C:\WBG\.compound-gpid" reset --hard origin/main
> ```

**Then run `cg-update` from each linked project** to apply the structural migration (consolidates knowledge docs from `docs/` to `.cg-docs/`, required for `/cg-compound` and solution lookups to work correctly):
```powershell
cg-update  # run from your project root
```

If the issue persists, open a [GitHub Issue](https://github.com/GPID-WB/compound-gpid/issues).

### `. $PROFILE` fails with "Cannot dot-source" error (Constrained Language Mode)

**Symptom**:
```
. $PROFILE
Microsoft.PowerShell_profile.ps1 : Cannot dot-source this command because it was defined in a different language mode.
```

**Cause**: Your organization enforces Constrained Language Mode (CLM) via AppLocker or Windows Defender Application Control. OneDrive has redirected your Documents folder to a path CLM treats as untrusted, blocking profile dot-sourcing.

**Fix**: Re-install using the current approach (batch wrappers on PATH — no profile manipulation):
```powershell
# Clone to C:\WBG (if not already there)
git clone https://github.com/GPID-WB/compound-gpid.git "C:\WBG\.compound-gpid"

# Run the installer
& "C:\WBG\.compound-gpid\install.ps1"

# Restart your terminal
```
The installer automatically removes any old `$PROFILE` block from previous installs.

### Removing an old installation from `$env:USERPROFILE\.compound-gpid`

If you previously cloned to `$env:USERPROFILE\.compound-gpid` (the old default path), clean it up after migrating to `C:\WBG\.compound-gpid`:

**Step 1 — Remove the old `$PROFILE` block** (if `install.ps1` hasn't already done this automatically):
```powershell
$p = Get-Content $PROFILE -Raw
$p = $p -replace "(?s)# --- Compound GPID.*?# --- End Compound GPID ---\r?\n?", ""
Set-Content $PROFILE $p.TrimEnd()
```

**Step 2 — Remove the old `bin\` directory from PATH** (if it was added):

> **Note**: `[Environment]::GetEnvironmentVariable` is blocked by Constrained Language Mode. Use `reg.exe` instead — it works in all language modes.

```powershell
$oldBin = "$env:USERPROFILE\.compound-gpid\bin"
$currentPath = (reg query "HKCU\Environment" /v PATH 2>$null |
    Where-Object { $_ -match 'PATH' }) -replace '.*REG_[A-Z_]+\s+', ''
$newPath = ($currentPath.Trim() -split ';' |
    Where-Object { $_ -and $_ -ne $oldBin }) -join ';'
reg add "HKCU\Environment" /v PATH /t REG_EXPAND_SZ /d $newPath /f
```

**Step 3 — Delete the old clone**:
```powershell
Remove-Item -Path "$env:USERPROFILE\.compound-gpid" -Recurse -Force
```

**Step 4 — Restart your terminal** to pick up the PATH change.

> If you already ran `install.ps1` from `C:\WBG\.compound-gpid`, Step 1 was done automatically. You only need Steps 2–4.

## Output Locations

```
.cg-docs/
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
