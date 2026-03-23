---
date: 2026-03-02
title: "Rename prompts, agents, and skills with cg- prefix; add WIP banner and manual"
status: completed
language: both
estimated-effort: medium
tags: [dx, naming, documentation, guardrails]
---

# Plan: Rename Prefixes & Documentation Overhaul

## Objective

Rename all prompts, agents, and skill folders with a `cg-` / `cg-skill-` prefix for clarity. Add a WIP banner to the README, create a user manual, and add file-permission guardrails to brainstorm/plan prompts.

## Context

All prompts, agents, and skills currently lack a project prefix. The README has no WIP warning. There is no manual explaining the system. The brainstorm decided on Approach 1 (all-at-once).

## Implementation Steps

### 1. Rename prompt files

**Files**: `.github/prompts/`

| Current | New |
|---|---|
| `brainstorm.prompt.md` | `cg-brainstorm.prompt.md` |
| `compound.prompt.md` | `cg-compound.prompt.md` |
| `plan.prompt.md` | `cg-plan.prompt.md` |
| `review.prompt.md` | `cg-review.prompt.md` |
| `work.prompt.md` | `cg-work.prompt.md` |

**Acceptance criteria**: Old files gone, new files exist with identical content (before cross-ref updates).

### 2. Rename agent files

**Files**: `.github/agents/`

| Current | New |
|---|---|
| `architecture.agent.md` | `cg-architecture.agent.md` |
| `code-quality.agent.md` | `cg-code-quality.agent.md` |
| `data-quality.agent.md` | `cg-data-quality.agent.md` |
| `documentation.agent.md` | `cg-documentation.agent.md` |
| `learnings-researcher.agent.md` | `cg-learnings-researcher.agent.md` |
| `performance.agent.md` | `cg-performance.agent.md` |
| `reproducibility.agent.md` | `cg-reproducibility.agent.md` |
| `testing.agent.md` | `cg-testing.agent.md` |
| `version-control.agent.md` | `cg-version-control.agent.md` |

**Acceptance criteria**: Old files gone, new files exist with identical content.

### 3. Rename skill folders

**Files**: `.github/skills/`

| Current | New |
|---|---|
| `brainstorming/` | `cg-skill-brainstorming/` |
| `compound-docs/` | `cg-skill-compound-docs/` |
| `git-workflow/` | `cg-skill-git-workflow/` |
| `python-best-practices/` | `cg-skill-python-best-practices/` |
| `r-best-practices/` | `cg-skill-r-best-practices/` |
| `setup/` | `cg-skill-setup/` |

**Acceptance criteria**: Old folders gone, new folders exist with all contents preserved.

### 4. Update cross-references

Files that reference old names need updating:

#### 4a. `README.md`
- Update prompt references: `/brainstorm` → `/cg-brainstorm`, etc.
- Update `/setup` → `/cg-setup`
- Update skill table names
- Update agent table names (no prefix in agent names referenced via `@`, but agent references like `@code-quality` become `@cg-code-quality`)
- Update directory structure diagram comments

#### 4b. `.github/copilot-instructions.md`
- `/review` → `/cg-review`
- `/compound` → `/cg-compound`
- `r-best-practices` → `cg-skill-r-best-practices`
- `python-best-practices` → `cg-skill-python-best-practices`

#### 4c. `.github/prompts/cg-brainstorm.prompt.md`
- Handoff: `/plan` → `/cg-plan`

#### 4d. `.github/prompts/cg-plan.prompt.md`
- Handoff: `/work` → `/cg-work`

#### 4e. `.github/prompts/cg-work.prompt.md`
- `/plan` references → `/cg-plan`
- `/review` reference → `/cg-review`
- `r-best-practices` → `cg-skill-r-best-practices`
- `python-best-practices` → `cg-skill-python-best-practices`

#### 4f. `.github/prompts/cg-review.prompt.md`
- Agent `@` references: `@code-quality` → `@cg-code-quality`, etc.
- `/review light` → `/cg-review light`
- `/compound` → `/cg-compound`

#### 4g. `.github/prompts/cg-compound.prompt.md`
- `copilot-instructions.md` reference stays (it's a filename, not a command)

#### 4h. `.github/skills/cg-skill-setup/SKILL.md`
- All `/brainstorm`, `/plan`, `/work`, `/review`, `/compound` references → `/cg-brainstorm`, etc.
- `name: setup` → `name: cg-skill-setup`

#### 4i. Other SKILL.md files
- Update `name:` field in frontmatter to include prefix

**Acceptance criteria**: No references to old unprefixed names remain (except in brainstorm/plan docs which are historical records).

### 5. Add file-permission guardrails to brainstorm and plan prompts

**Files**: `cg-brainstorm.prompt.md`, `cg-plan.prompt.md`

Add a `## File Permissions` section to each:

For `cg-brainstorm`:
```markdown
## File Permissions
- ✅ READ any file in the workspace
- ✅ CREATE new files ONLY under `docs/brainstorms/`
- ❌ NEVER modify existing files
- ❌ NEVER create files outside `docs/brainstorms/`
```

For `cg-plan`:
```markdown
## File Permissions
- ✅ READ any file in the workspace
- ✅ CREATE new files ONLY under `docs/plans/`
- ❌ NEVER modify existing files
- ❌ NEVER create files outside `docs/plans/`
```

**Acceptance criteria**: Both prompts have explicit guardrails. Neither uses `agent: plan` mode.

### 6. Add WIP banner to README.md

Add a prominent banner at the very top:

```markdown
> [!CAUTION]
> **⚠️ WORK IN PROGRESS — DO NOT USE IN PRODUCTION**
>
> This project is under active development and is not yet ready for use.
> APIs, prompts, and conventions may change without notice.
> This banner will be removed when the system is stable.
```

**Acceptance criteria**: Banner is the first thing visible in README.

### 7. Create `docs/manual.md`

Single-file manual covering:

1. **Overview**: What Compound GPID is
2. **Key Concepts**: Prompts vs. Skills vs. Agents — what each is, differences
3. **Non-interactive design**: Prompts and agents are NOT meant to be used interactively; they are invoked through the workflow loop
4. **Skills**: Also not intended for interactive use (though they can be); they provide reference knowledge to prompts/agents
5. **The Workflow Loop**: Brainstorm → Plan → Work → Review → Compound
6. **How to invoke**: Using `/cg-brainstorm`, `/cg-plan`, etc. in Copilot Chat
7. **Configuration**: `compound-gpid.local.md` setup
8. **Naming conventions**: `cg-` prefix for prompts/agents, `cg-skill-` for skills

**Acceptance criteria**: Manual exists, is clear and complete for team use.

### 8. Update ROADMAP.md references

- Update prompt/skill/agent name references to use new prefixed names.

**Acceptance criteria**: ROADMAP uses new naming.

## Risks & Mitigations

| Risk | Mitigation |
|---|---|
| Missed cross-references | Grep for old names after all changes |
| Git history disruption from renames | Use `git mv` for renames to preserve history |
| Skills may have internal relative paths | Skill internal paths (e.g., `workflows/project-setup.md`) are relative within the folder — these don't change |

## Out of Scope

- Changing agent behavior or prompt logic (beyond guardrails)
- Adding new prompts, agents, or skills
- Updating `.github/instructions/` files (these reference skills by concept, not filename)
