# Artifact View Contract

This contract governs versioned Brainstorm and Plan Markdown plus their optional
self-contained HTML views.

## Authority

- Canonical Markdown is the sole decision and execution authority.
- HTML is derived, regenerable, and may orient human or agent readers, but it
  never supplies execution semantics, roadmap state, approvals, or edits.
- New Brainstorms and Plans emit `artifact-schema-version: 1`.
- Missing version is compatible legacy input only when deterministic parsing is
  unambiguous. Unknown future versions fail with recovery guidance.

## Validation And Generation

After canonical Markdown is saved and its path is verified:

- Normal emitter flow runs `cg-render-artifact --automatic <source>`.
- A one-run `--no-html` flag runs
  `cg-render-artifact --validate-only <source>` instead.
- `artifact-html: false` suppresses automatic HTML writes only. It never
  suppresses validation, explicit rendering, validation-only, or stale checks.
- Explicit rendering uses `cg-render-artifact <source>`.
- Freshness uses `cg-render-artifact --check <source>`.

Any validation or rendering failure preserves the canonical Markdown and any
prior valid view. Report the exact failure, expected missing/stale/current view
path, and the one-file recovery command.

## Paths And Provenance

- Brainstorm: `.cg-docs/brainstorms/<slug>.md` maps to
  `.cg-docs/views/brainstorms/<slug>.html`.
- Plan: `.cg-docs/plans/<slug>.md` maps to
  `.cg-docs/views/plans/<slug>.html`.
- Views embed source path, normalized source SHA-256, artifact schema version,
  renderer version, and UTC generation timestamp.

## Model Context

Generated `.cg-docs/views/**` files are derived outputs:

- Never load their bodies, full content, or diffs into model context.
- Review, commit/PR, release, Brain, context, and audit workflows may list,
  count, stage, or freshness-check view paths only.
- Review and PR prose comes from canonical Markdown, renderer code, tests, and
  stale-check results.

## Runtime Independence

Rendering is local, deterministic, dependency-free Python. It performs no model,
agent, network, subprocess-agent, or Open Design call. Open Design is used only
for implementation-time design evidence; users need no daemon, MCP server,
account, connector, plugin, or runtime.
