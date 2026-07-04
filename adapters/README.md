# Compound GPID Cross-Agent Adapters

> **Note**: As of the cross-agent native platform targets implementation,
> these adapters are superseded by generated native trees (`.claude/`,
> `.agents/`, `.opencode/`). The new mechanism uses
> `cg_generate_targets.py` and `.github/shared/target-mapping.json` to
> generate committed, release-validated platform trees distributed via
> the same junction/symlink mechanism. These source adapter files remain
> for backward compatibility but new users should use
> `cg-link --platforms copilot,claude-code,codex,opencode` instead.

These files are optional compatibility adapters for teams that use Compound
GPID from coding agents that do not natively load GitHub Copilot prompt,
skill, and agent assets.

GitHub Copilot does not read these files. Normal Copilot-only projects do not
need them.

## Available Adapters

| Adapter | Copy to consumer repo root | Purpose |
|---------|----------------------------|---------|
| Codex | `AGENTS.md` | Maps `/cg-*` commands, `cg-skill-*` skills, `@cg-*` agents, and Copilot-style tool names to Codex behavior. |
| Claude Code | `CLAUDE.md` | Maps the same Compound GPID assets to Claude Code-compatible behavior. |

## Usage

1. Link the project normally with `cg-link`.
2. Copy the adapter file for your agent into the consumer repository root.
3. Commit the adapter only if that repository is intentionally maintained with
   that agent family.

Keep project-specific rules in the closest project adapter file. Keep reusable
Compound GPID workflow behavior in the packaged adapter source so future
updates can be reviewed and copied intentionally.

## Boundaries

- These adapters are source packages, not `cg-link` managed outputs.
- They do not install retrieval backends, external services, or snapshot
  tooling.
- They should not change `.github/` prompt, skill, agent, instruction, or
  shared-contract behavior for GitHub Copilot.
