# Files and Artifacts

This map distinguishes user settings, shared project sources, generated runtime
targets, and durable workflow artifacts.

## Project root

| Path | Ownership | Purpose |
|---|---|---|
| `compound-gpid.local.md` | Team; committed | Shared language, dialect, project-type, and review settings (plus shared `## Notes`); must stay out of `.gitignore`
| `compound-gpid.md` | Team; committed | Optional short project charter |
| `compound-gpid.context.md` | Team; committed | Optional tactical project context |
| `roadmap.json` | Team; committed | Milestones, features, plan links, and optional issue metadata |
| `.compound-gpid/managed-files.json` | Tool-managed | Checksums and sources for managed copied files |

## Runtime targets

| Path | Role |
|---|---|
| `.github/` | Canonical Copilot-oriented prompts, skills, agents, instructions, and shared contracts |
| `.claude/` | Generated Claude Code target |
| `.agents/` | Generated Codex target |
| `.opencode/` | Generated OpenCode target |
| `.kilo/` | Generated Kilo target |

Directory units are linked into consumer projects. Some strict root or JSON
files are copied and tracked by the sidecar manifest. Project-owned roots and
conflicting files are preserved.

## `.cg-docs/` knowledge base

| Path | Produced or used by |
|---|---|
| `active-state/` | Compact cross-session restart records |
| `archive/` | Charter history and deliberately archived content |
| `brainstorms/` | `/cg-brainstorm` decisions |
| `competitive-reviews/` | Maintainer external-repository reviews and registry |
| `cost/` | Context/model audit reports and release-readiness records |
| `inbox/` | Unapproved strategy ideas awaiting promotion |
| `plans/` | `/cg-plan` implementation plans |
| `reviews/` | Review and verification reports with finding status |
| `solutions/` | Verified reusable lessons from `/cg-compound` |
| `strategy/` | `/cg-strategy` records |
| `token/` | Token dashboard, context map, regression checks, and short-lived output evidence |
| `views/brainstorms/` | Self-contained HTML derived from canonical Brainstorm Markdown |
| `views/plans/` | Self-contained HTML derived from canonical Plan Markdown |
| `views/documents/` | Self-contained HTML published from generic Markdown sources |
| `work-reports/` | Delivery evidence and implementation summaries |

Generated `BRAIN.md`, topic files, logs, and `brain-index.json` index these source
artifacts. Preserve the source artifacts as the authority.

Files under `.cg-docs/views/` are committed, regenerable outputs rather than a
second source of truth. They contain visible and JSON provenance: source path,
exact pinned-byte source SHA-256, schema version, renderer version, and UTC timestamp.
Do not edit them directly or load generated HTML bodies into model context.

## Related pages

- [Configuration](../configuration/index.md)
- [Knowledge and Coordination](../workflows/knowledge.md)
- [Complete Reference](../reference.md)
