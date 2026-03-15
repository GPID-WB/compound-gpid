# Workflow

This page explains the Compound GPID workflow loop and how to use each step.

> **Not installed yet?** See [Installation](installation.md) first. For all commands and shortcuts, see [Reference](reference.md).

---

## The Loop

```
Brainstorm → Plan → Work → Review → Compound
          ↑
       Resume  (re-enter an interrupted session at any step)
```

All steps are invoked as `/cg-*` prompts in GitHub Copilot Chat. **Prompts are not interactive commands** - invoke a prompt, answer its questions when asked, and let it run to completion.

---

## Steps

### 1. Brainstorm (`/cg-brainstorm`)

**When**: Requirements are fuzzy, you're not sure what to build, or multiple approaches are possible.

**What happens**: The prompt scans your project, asks clarifying questions one at a time, and proposes 2–3 approaches with pros/cons. Once you pick one, it saves a decision document to `.cg-docs/brainstorms/`.

**Output**: `.cg-docs/brainstorms/YYYY-MM-DD-<title>.md`

---

### 2. Plan (`/cg-plan`)

**When**: After brainstorming (or when you already know what to build).

**What happens**: The prompt reads any relevant brainstorm, researches your codebase, and creates a step-by-step implementation plan with files to create/modify, tests to write, and acceptance criteria.

**Output**: `.cg-docs/plans/YYYY-MM-DD-<title>.md`

---

### 3. Work (`/cg-work`)

**When**: After a plan exists.

**What happens**: The prompt loads the most recent plan and implements it step by step - writing code, tests, and documentation. It checks against acceptance criteria and suggests commit messages.

**Output**: Code, tests, documentation changes.

---

### 4. Review (`/cg-review`)

**When**: After implementing changes.

**What happens**: The prompt dispatches specialized agents based on your configured review depth, collects their findings, and presents them prioritized as P1 (critical), P2 (important), P3 (minor).

| Tier | Agents run | Use when |
|------|-----------|---------|
| **Light** | `cg-code-quality` + `cg-testing` | Quick fixes, small changes |
| **Standard** | All 8 agents | Default for most work |
| **Thorough** | All 8 + `cg-learnings-researcher` | Major features, refactors |

**Output**: Prioritized review report with suggested fixes.

---

### 5. Compound (`/cg-compound`)

**When**: After solving a non-trivial problem.

**What happens**: Captures the problem, root cause, solution, and prevention strategy as a structured document. This feeds the `cg-learnings-researcher` agent in future thorough reviews.

**Output**: `.cg-docs/solutions/<category>/YYYY-MM-DD-<title>.md`

---

### 6. Resume (`/cg-resume`)

**When**: At the start of a session when you have interrupted work.

**What happens**: Scans `.cg-docs/plans/` for active plans, `.cg-docs/brainstorms/` for decided-but-unplanned brainstorms, and inspects `git status`/`git log` for in-progress code changes. Presents a structured summary and suggests the most logical next action.

**Output**: A structured context summary and a suggested continuation path.

---

## Prompts vs. Agents vs. Skills

| Aspect | Prompts | Agents | Skills |
|--------|---------|--------|--------|
| **What they are** | Workflow commands | Specialized reviewers | Reference knowledge |
| **How you use them** | Type `/cg-setup`, `/cg-brainstorm`, etc. | Dispatched by `/cg-review` | Referenced by prompts/agents |
| **Interactive?** | No - follow the workflow | No - automated | No (passive by design) |
| **Prefix** | `cg-` | `cg-` | `cg-skill-` |
| **Location** | `.github/prompts/` | `.github/agents/` | `.github/skills/` |
| **Produce output?** | Yes (docs, code, reviews) | Yes (review findings) | No (consumed by others) |

---

> **All commands in one place**: see [Reference](reference.md).
> **Something broken?** See [Troubleshooting](troubleshooting.md).

