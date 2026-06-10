---
date: 2026-06-06
title: "Codex and Claude Code need an AGENTS.md adapter to execute GitHub Copilot /cg-* prompts"
category: "environment-issues"
language: "both"
tags: [codex, claude-code, copilot, prompts, agents, skills, slash-commands]
root-cause: "The repository's .github prompt, skill, and agent assets were designed for GitHub Copilot, while Codex and Claude Code do not automatically register those files as native commands or skills."
severity: "P2"
---

# Codex and Claude Code Need an AGENTS.md Adapter to Execute GitHub Copilot /cg-* Prompts

## Problem

Compound GPID's workflow assets live under `.github/` and were originally
designed for GitHub Copilot:

- `.github/prompts/cg-*.prompt.md` for slash-command workflows
- `.github/skills/cg-skill-*/SKILL.md` for reference knowledge
- `.github/agents/cg-*.agent.md` for specialized review and workflow agents
- `.github/copilot-instructions.md` for project-wide Copilot behavior

When the repository is opened by Codex or Claude Code, those assets are visible
as ordinary files but are not automatically registered as native Codex skills,
slash commands, or callable subagents. A user invoking `/cg-compound` or
`/cg-work phase1` needs the agent to know how to translate that request into a
local file read and execution protocol.

## Root Cause

GitHub Copilot, Codex, and Claude Code use different instruction discovery and
tool models. Copilot-oriented `.github/` assets encode useful behavior, but
Codex does not automatically treat `.github/prompts/*.prompt.md` as executable
slash commands or `.github/skills/*/SKILL.md` as native skills.

Without an explicit adapter, Codex may either ignore `/cg-*` invocations or treat
them as ordinary prose instead of loading the corresponding prompt file.

## Solution

Add a repository-level `AGENTS.md` that applies only to Codex, Claude Code, or
Claude Code-compatible agents. The file must state that it is a compatibility
adapter and does not change the intended GitHub Copilot behavior of the
repository.

The key dispatch convention:

```text
/cg-<name> [args...] -> .github/prompts/cg-<name>.prompt.md
```

For example:

```text
/cg-compound -> read and follow .github/prompts/cg-compound.prompt.md
/cg-work phase1 -> read .github/prompts/cg-work.prompt.md and preserve phase1
```

The adapter also defines local mappings for non-native Copilot/Claude concepts:

- `cg-skill-*` references load `.github/skills/<skill-name>/SKILL.md`
- `@cg-*` dispatch is emulated by reading `.github/agents/cg-*.agent.md`
- unavailable Claude/Copilot tools map to Codex equivalents such as `rg`,
  `sed`, `apply_patch`, `exec_command`, and `update_plan`

## Prevention

When reusing GitHub Copilot prompt libraries in Codex or Claude Code:

- Keep the original `.github/` assets Copilot-oriented.
- Put compatibility behavior in `AGENTS.md`, not in generated Copilot files.
- Make the agent scope explicit: Codex / Claude Code only.
- Preserve command arguments exactly when mapping slash commands to prompt files.
- Treat skills as reference files, not directly invocable commands.
- Treat agent specs as instructions to emulate unless a native subagent tool is
  available.

Test the adapter with a low-risk command such as `/cg-compound` and verify that
the agent first reads `.github/prompts/cg-compound.prompt.md`, then loads the
referenced project instructions and skills.

## Related

- [Skills are not slash-command prompts](2026-03-02-skill-vs-prompt-slash-command.md)
  — establishes the distinction between invocable prompt files and reference
  skill files.
- `AGENTS.md` — the Codex / Claude Code compatibility adapter.
- `.github/prompts/cg-compound.prompt.md` — first prompt used to validate the
  adapter.
