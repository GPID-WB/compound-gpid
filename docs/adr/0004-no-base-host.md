# ADR 0004: No coding agent is the base

Date: 2026-11-24. Status: accepted (maintainer's direction).

## Context

Version 1 was written for one coding agent, GitHub Copilot. Its files lived in `.github/`, and every other coding agent was served by a generated copy of that tree with its names translated. Each new host added a copy, a translation and a class of bugs.

The maintainer has confirmed that analysts may now choose among several coding agents, including Copilot, Claude Code, Codex and Kilo. The plugin should work in whichever one a person prefers and should not lean on any one of them.

## Decision

Compound GPID 2.0 has no base host.

1. **One source, in the open format.** Everything is written once as Agent Skills folders (`SKILL.md` plus files beside it). Every supported host reads that format directly. Nothing is generated per host.
2. **Core uses only what every host has:** skills, an always-loaded instructions file, a shell, and Python. The loop, the two hard stops and the verifiers must work with those four things alone.
3. **A host-specific piece is an adapter.** When one host needs something of its own, it goes in a small file that only that host reads, and the loop still works without it. Known adapters so far:
   - `CLAUDE.md` containing `@AGENTS.md`, because Claude Code reads only `CLAUDE.md`;
   - a per-skill policy file for Codex, because Codex ignores the frontmatter flag that keeps a skill user-invoked;
   - later, optionally, a Kilo mode that pins the guide, and session hooks where a host offers them.
4. **A feature only some hosts have is used when present and never required.** A todo tool shows the checklist where it exists; the state stays in files. A subagent tool gives independent review where it exists; without one the review runs in the main thread and is recorded as self-review.
5. **Supported means tested.** A host is supported when its rows in ADR 0001 are live results, and they are re-run before each release. A host with only documentation-based rows is listed as untested.
6. **Adding a host** means adding its rows to ADR 0001 and, if needed, one adapter. It never means changing a principle, a playbook or the tooling.

## Consequences

- Hosts that can be run from a script (Claude Code, Codex, the Kilo command line) are tested first and most often, because the check is one command. Copilot and the editor panels are tested by the maintainer with the checklist.
- The plugin gives up host features that cannot be had everywhere, such as an agent picker. The guide gets the same effect from files and a script.
- When a host changes how it finds skills, one adapter or one row changes.
- The words "base", "canonical tree" and "generated tree" from version 1 have no meaning in version 2.

## What would reopen this

A host that most analysts use and that cannot read Agent Skills folders at all.
