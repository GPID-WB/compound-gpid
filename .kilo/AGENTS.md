# Compound GPID — Kilo Adapter

This file is generated from the target mapping.
It maps Compound GPID `/cg-*` commands to native Kilo paths.

## Command Dispatch

`/cg-<name> [args...]` -> `.kilo/commands/cg-<name>.md`

## Skills

Load skill files from `.kilo/skills/*-skill-*/SKILL.md`.

## Agents

Agent specs are under `.kilo/agents/`.

## Instructions And Contracts

Language instructions are under `.kilo/instructions/`; shared contracts are under `.kilo/shared/`.

## Cross-Adapter Skill Discovery

Kilo auto-discovers `.agents/skills` and `.claude/skills` in addition to `skills.paths`. As of the 2026-08-20 Kilo schema, project config has no supported `only`, `exclude`, or auto-discovery switch; the process-level `KILO_DISABLE_EXTERNAL_SKILLS` flag is not portable to VS Code/Positron project installs. When Kilo and another adapter are linked together, `cg-link` therefore keeps the adapter path as a junction/symlink but points it at an adapter-specific managed mirror under `.compound-gpid/kilo-compat-skills/`. This keeps every Kilo-reachable `SKILL.md` inside the project trust boundary while preserving each adapter's generated content. This workaround complements upstream Kilo #12391/PR #12846 and remains necessary for Kilo versions that reject auto-discovered compatibility skills resolving outside the project.
