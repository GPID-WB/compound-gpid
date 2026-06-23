# Compound GPID Claude Code Instructions

These instructions apply only when this repository is being operated by Claude
Code or a Claude Code-compatible agent.

The repository's `.github/` prompt, skill, agent, and instruction files were
designed for GitHub Copilot. Do not treat this adapter as changing the intended
behavior of GitHub Copilot. It only tells Claude Code-compatible agents how to
read and execute the existing GitHub Copilot-oriented assets.

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

Treat agent output formats, priority systems, and review scope in those files
as instructions. If multiple agents are requested, run their analyses
sequentially in the main thread unless a native subagent tool is explicitly
available.

## Compound Claude Code Tool Mapping

This repository contains prompts originally designed for GitHub Copilot. Map
unavailable Copilot-style tool names to Claude Code behavior:

- Read: use Claude Code file-read tools or shell reads such as `sed`, `cat`, or
  `rg`
- Write: use Claude Code edit/write tools
- Edit/MultiEdit: use Claude Code edit tools
- Bash: use the shell tool
- Grep: use `rg`; fall back to `grep` if needed
- Glob: use file-glob tools, `rg --files`, or `find`
- LS: use directory-listing tools or `ls`
- WebFetch/WebSearch: use available web tools only when the workflow permits
  external research
- AskUserQuestion/Question: ask a concise question in chat and wait for the
  user's response
- Task/Subagent/Parallel: run sequentially in the main thread unless native
  subagent tools are explicitly available
- TaskCreate/TaskUpdate/TaskList/TaskGet/TaskStop/TaskOutput and
  TodoWrite/TodoRead: use the available task tracking tool
- Skill: open the referenced `SKILL.md` and follow it
- ExitPlanMode: ignore

## Project Instructions

Always read `.github/copilot-instructions.md` when starting meaningful project
work, then apply the relevant language instruction files from
`.github/instructions/` and skills from `.github/skills/`.

Use the repository's declared project memory system if one exists. When no
project-specific memory system is declared, rely on local `.cg-docs/` plans,
reviews, solutions, and Brain artifacts.
