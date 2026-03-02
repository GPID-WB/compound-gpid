---
date: 2026-03-02
title: "Rename prompts, agents, and skills with cg- prefix; add WIP banner and manual"
status: decided
chosen-approach: "All-at-once with explicit file-permission guardrails"
tags: [dx, naming, documentation, guardrails]
---

# Rename Prefixes & Documentation Overhaul

## Context

The project's prompts, agents, and skills lack a consistent naming prefix, making it unclear which files belong to the Compound GPID system. Additionally, the project needs:
- A WIP banner on README.md to prevent premature use
- A manual explaining how the system works
- Clear documentation that prompts/agents are non-interactive
- Explanation of differences between prompts, skills, and agents

## Requirements

1. **Rename prompts** with `cg-` prefix (e.g., `cg-brainstorm.prompt.md`)
2. **Rename agents** with `cg-` prefix (e.g., `cg-architecture.agent.md`)
3. **Rename skill folders** with `cg-skill-` prefix (e.g., `cg-skill-brainstorming/`)
4. **Add WIP banner** to `README.md` — prominent warning that this is a work in progress
5. **Create `docs/manual.md`** — single-file wiki/manual covering:
   - How to use the system
   - That prompts and agents are NOT meant to be used interactively
   - Differences between prompts, skills, and agents
   - Skills are also not intended for interactive use (though they can be)
6. **File-permission guardrails** in brainstorm and plan prompts:
   - Use default agent mode (not `agent: plan`) so they can write output files
   - Add explicit rules: READ any file, CREATE only under allowed `docs/` subdirectory, NEVER modify existing files, NEVER create files outside allowed directory
7. **Update all cross-references** in prompt/agent/skill files that reference old names

## Approaches Considered

### Approach 1: All-at-once (Chosen)

Do all renames, reference updates, WIP banner, and manual in one pass/PR.

**Pros**: Everything consistent immediately; no half-renamed state; easy to review.
**Cons**: Larger diff, but low risk (mostly renames and docs).
**Effort**: Medium.

### Approach 2: Phased (renames first, docs second)

Split into two PRs: renames + reference updates, then docs.

**Pros**: Smaller PRs.
**Cons**: Intermediate state where files are renamed but docs don't explain the new names.
**Effort**: Medium (same total work).

### Approach 3: Docs-first, then renames

Write manual first, then rename to match documented conventions.

**Pros**: Documentation drives naming.
**Cons**: Manual references files that don't exist yet.
**Effort**: Medium.

## Decision

**Approach 1: All-at-once.** The changes are mechanical and self-contained. Low risk, no confusing intermediate state.

### Guardrail Decision

For brainstorm and plan prompts, use **default agent mode** (not `agent: plan`) with explicit file-permission rules in the prompt text:

```
## File Permissions
- ✅ READ any file in the workspace
- ✅ CREATE new files ONLY under `docs/<allowed-subdirectory>/`
- ❌ NEVER modify existing files
- ❌ NEVER create files outside the allowed directory
```

This allows the prompts to write their output files (brainstorm docs, plans) while preventing unwanted modifications to source code.

## Rename Mapping

### Prompts (.github/prompts/)
| Current | New |
|---|---|
| `brainstorm.prompt.md` | `cg-brainstorm.prompt.md` |
| `compound.prompt.md` | `cg-compound.prompt.md` |
| `plan.prompt.md` | `cg-plan.prompt.md` |
| `review.prompt.md` | `cg-review.prompt.md` |
| `work.prompt.md` | `cg-work.prompt.md` |

### Agents (.github/agents/)
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

### Skills (.github/skills/)
| Current | New |
|---|---|
| `brainstorming/` | `cg-skill-brainstorming/` |
| `compound-docs/` | `cg-skill-compound-docs/` |
| `git-workflow/` | `cg-skill-git-workflow/` |
| `python-best-practices/` | `cg-skill-python-best-practices/` |
| `r-best-practices/` | `cg-skill-r-best-practices/` |
| `setup/` | `cg-skill-setup/` |

## Next Steps

1. Use `/plan` (`cg-plan`) to create a detailed implementation plan with file-by-file changes
2. Execute the plan: renames, reference updates, WIP banner, manual creation
3. Review and merge
