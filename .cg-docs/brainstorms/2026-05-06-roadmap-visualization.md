---
date: 2026-05-06
title: "Roadmap Visualization — Agent + Prompt Wrapper"
status: decided
scope: "Standard"
chosen-approach: "Hybrid: hidden agent + user-facing prompt wrapper"
tags: [roadmap, visualization, agent, prompt, ux, workflow-maturity]
---

# Roadmap Visualization

## Context

The project roadmap lives in `roadmap.json` — a ~500-line JSON file with 9
milestones and ~57 features. It's too difficult to read raw. Users need a fast,
friendly way to see:
- Overall progress (milestone summary with completion stats)
- What's left in a specific milestone
- Details of a specific feature (description, linked plan)
- Filtered views (by status, in-progress only)

The user wants this invokable quickly without external dependencies, and
reusable across the plugin's internal prompts/agents for consistency.

## Requirements

1. **Chat-based output** — Markdown tables + emoji badges rendered in Copilot chat
2. **Fuzzy matching** — Users don't need to remember exact milestone/feature IDs
3. **Multiple view modes** via flags:
   - *(none)*: Summary table (all milestones, status, done/total)
   - `--milestone <name>`: Single milestone detail (objective, progress, features)
   - `--tasks`: All milestones with feature lists
   - `--tasks <name>`: Features in one milestone
   - `--detail <name>`: Feature description, status, linked plan path
   - `--detail <name> --plan`: Feature detail + plan file summary
   - `--status <status>`: All features matching a status across milestones
   - `--wip`: Shortcut for in-progress milestones with features
4. **No external dependencies** — pure prompt/agent, no Python or Node required
5. **Fast** — Haiku-class model on the agent
6. **Internal reuse** — agent dispatchable by `/cg-resume`, `/cg-plan`,
   `/cg-brainstorm`, `/cg-strategy` for contextual roadmap display
7. **Hidden agent** — not user-invocable directly; users go through `/cg-roadmap-view`

## Approaches Considered

### Approach 1: Pure Prompt

Single `.prompt.md` with formatting templates. LLM reads JSON, interprets flags,
renders output.

- Pros: Zero code, zero dependencies, easy to maintain
- Cons: No reuse by other agents, all logic in one file

### Approach 2: Prompt + PowerShell Script

PowerShell handles parsing/matching, prompt presents output.

- Pros: Deterministic matching, testable, dual-use
- Cons: More code, terminal loses Markdown formatting, two-step flow

### Approach 3: Agent only

Read-only agent with natural language arguments.

- Pros: Reusable, read-only safety, natural language
- Cons: No structured flag syntax, less discoverable

### Approach 4 (Chosen): Hybrid — Hidden Agent + Prompt Wrapper

Two components:
- `cg-roadmap-view.agent.md` — hidden (`user-invocable: false`), `tools: ['read']`,
  Haiku model. Handles all rendering logic, fuzzy matching, view modes.
- `cg-roadmap-view.prompt.md` — thin user-facing wrapper that parses flags and
  dispatches the agent.

Other prompts dispatch the agent directly as a subagent for contextual display.

- Pros: Reusable, structured flags for users, natural language for internal dispatch,
  read-only safety, separation of concerns (UX vs logic)
- Cons: Two files to maintain (but both are small)

## Decision

**Approach 4** — Hybrid architecture. The agent is the source of truth for
roadmap rendering; the prompt is a thin UX layer.

## Integration Points (design for from the start)

| Dispatching prompt/agent | Use case | What to request from agent |
|---|---|---|
| `/cg-roadmap-view` | User wants to see roadmap | Pass flags directly |
| `/cg-resume` | Show "here's where you left off" | `--wip` view |
| `/cg-plan` Step 5 | Show milestone context when linking plan | `--milestone <name>` |
| `/cg-brainstorm` Step 5b | Show milestones for idea placement | Summary table (no flags) |
| `/cg-strategy` | Strategic overview of project state | `--tasks` or summary |

## Additional Decisions

- **ROADMAP.md drift**: Current `ROADMAP.md` is manually maintained and diverged
  from `roadmap.json`. Consider deprecating it or auto-generating it as a separate
  follow-up task. Not in scope for this brainstorm.
- **Fuzzy matching**: LLM-based (not algorithmic). Acceptable because the agent
  is already reading the full JSON and can match intent naturally.
- **Plan summary**: Off by default. Enabled with `--plan` flag (adds latency since
  it reads external files).

## Next Steps

1. Create `cg-roadmap-view.agent.md` with rendering logic and formatting templates
2. Create `cg-roadmap-view.prompt.md` as user-facing wrapper with flag documentation
3. Add integration dispatch instructions to `/cg-resume`, `/cg-plan`, `/cg-brainstorm`, `/cg-strategy`
4. Add Pester tests for the prompt structure
5. Register feature in `roadmap.json` under Workflow Maturity
6. Clean up `_examples/` demo files
