# Compound GPID — Claude Code Adapter

This file is generated from the target mapping.
It maps Compound GPID `/cg-*` commands to native Claude Code paths.

## Command Dispatch

`/cg-<name> [args...]` -> `.claude/commands/cg-<name>.md`

## Skills

Load skill files from `.claude/skills/*/SKILL.md`.

## Agents

Agent specs are under `.claude/agents/`.

## Instructions And Contracts

Language instructions are under `.claude/instructions/`; shared contracts are under `.claude/shared/`.
