# Compound GPID Codex / Claude Code Instructions

These instructions apply only when this repository is being operated by Codex,
Claude Code, or a Claude Code-compatible agent.

This repository's `.github/` prompt, skill, agent, and instruction files were
originally designed for GitHub Copilot. Do not treat `AGENTS.md` as changing the
intended behavior of GitHub Copilot. It is only a compatibility adapter that
tells Codex / Claude Code how to read and execute the existing GitHub
Copilot-oriented assets.

## `/cg-*` Prompt Dispatch

When the user invokes a command matching `/cg-*`, treat it as a request to run
the matching local prompt in `.github/prompts/`.

Dispatch rules:

- `/cg-work` -> read and follow `.github/prompts/cg-work.prompt.md`
- `/cg-work phase1` -> read `.github/prompts/cg-work.prompt.md` and pass
  `phase1` as the command argument
- `/cg-plan-review` -> read and follow `.github/prompts/cg-plan-review.prompt.md`
- In general, `/cg-<name> [args...]` -> `.github/prompts/cg-<name>.prompt.md`
  with `[args...]` preserved as command arguments

If no matching prompt file exists, say so and list the closest available
`.github/prompts/cg-*.prompt.md` files.

Prompt files are executable instructions for the agent. Read the selected
prompt first, then follow its steps, loading referenced local skills, agent
specs, shared contracts, and instruction files from `.github/` as needed.

## Local Skills

When a `.github/prompts/*.prompt.md`, `.github/agents/*.agent.md`, or project
instruction references a skill named `cg-skill-*`, load it from:

```text
.github/skills/<skill-name>/SKILL.md
```

When a skill references relative files such as `workflows/*.md`,
`references/*.md`, or `packages/*.md`, resolve them relative to that skill
directory and read only the files relevant to the task.

## Local Agent Specs

When a prompt asks to dispatch `@cg-*`, emulate the agent in the main thread by
reading the matching spec:

```text
.github/agents/cg-*.agent.md
```

Treat agent output formats, priority systems, and review scope in those files as
instructions. If multiple agents are requested, run their analyses
sequentially in the main thread unless a native subagent tool is explicitly
available.

## Compound Codex Tool Mapping

This repository contains prompts originally designed for GitHub
Copilot. Map unavailable tool names to Codex behavior:

- Read: use shell reads such as `sed`, `cat`, or `rg`
- Write: create files with `apply_patch`
- Edit/MultiEdit: use `apply_patch`
- Bash: use `exec_command`
- Grep: use `rg`; fall back to `grep` if needed
- Glob: use `rg --files` or `find`
- LS: use `ls`
- WebFetch/WebSearch: use the available web tool, `curl`, or Context7 for
  library documentation
- AskUserQuestion/Question: ask a concise question in chat and wait for the
  user's response
- Task/Subagent/Parallel: run sequentially in the main thread unless a native
  subagent tool is available; use `multi_tool_use.parallel` only for independent
  tool calls
- TaskCreate/TaskUpdate/TaskList/TaskGet/TaskStop/TaskOutput and
  TodoWrite/TodoRead: use `update_plan`
- Skill: open the referenced `SKILL.md` and follow it
- ExitPlanMode: ignore

## Project Instructions

Always read `.github/copilot-instructions.md` when starting meaningful project
work, then apply the relevant language instruction files from
`.github/instructions/` and skills from `.github/skills/`.

Use `open-brain` as the project memory system. At the start of meaningful work,
search or inspect relevant recent `open-brain` context for `compound-gpid`; save
only durable decisions, solved problems, conventions, and final outcomes.
