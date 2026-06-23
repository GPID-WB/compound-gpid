---
date: 2026-06-23
title: "Cross-agent adapters should be opt-in source packages"
category: "environment-issues"
language: "Markdown/Python"
tags: [codex, claude-code, adapters, packaging, copilot-compatibility]
root-cause: "GitHub Copilot prompt libraries can be reused by other coding agents only when the dispatch adapter is explicit and outside Copilot-managed assets"
severity: "P2"
plan: ".cg-docs/plans/2026-06-23-cross-agent-packaging-adapters.md"
---

# Cross-Agent Adapters Should Be Opt-In Source Packages

## Problem

The root `AGENTS.md` adapter made this repository usable from Codex and Claude
Code-compatible agents, but consumer projects had no packaged adapter source to
copy. Putting compatibility rules into `.github/` files would alter the
Copilot-oriented runtime surface and risk confusing normal Copilot users.

## Root Cause

Compound GPID's prompt, skill, and agent files are designed for GitHub Copilot.
Other agent runtimes can read those files, but they need explicit dispatch,
skill-loading, agent-emulation, and tool-mapping instructions at the repository
root.

## Solution

Ship optional source adapters under `adapters/`:

- `adapters/codex/AGENTS.md` for Codex-compatible agents.
- `adapters/claude/CLAUDE.md` for Claude Code-compatible agents.
- `adapters/manifest.json` to describe target filenames and opt-in behavior.

Document that users copy these files into a consumer repo root only when that
repo is intentionally maintained with the matching agent family. `cg-link` does
not install them automatically.

## Prevention

Keep adapter drift tests focused on the core contract: `/cg-*` prompt dispatch,
`cg-skill-*` skill loading, `@cg-*` agent-spec emulation, tool mapping, and
Copilot non-interference language.

## Related

- `AGENTS.md`
- `adapters/README.md`
- `adapters/codex/AGENTS.md`
- `adapters/claude/CLAUDE.md`
- `.cg-docs/solutions/environment-issues/2026-06-06-codex-claude-code-cg-prompt-dispatch-adapter.md`
