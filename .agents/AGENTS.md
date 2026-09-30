# Compound GPID — Codex Adapter

This file is generated from the target mapping.
It maps Compound GPID `/cg-*` commands to native Codex paths.

## Command Dispatch

`/cg-<name> [args...]` -> `.agents/commands/cg-<name>.md`

## Skills

Load skill files from `.agents/skills/*-skill-*/SKILL.md`.

## Agents

Agent specs are under `.agents/subagents/`.

## Instructions And Contracts

Language instructions are under `.agents/instructions/`; shared contracts are under `.agents/shared/`.
