# Render a Document

Route one project-contained Markdown source to the correct deterministic CLI
tool and render it as curated HTML with an explicit theme.

## Routing

1. If the source is under `.cg-docs/brainstorms/` or `.cg-docs/plans/`:
   use `cg-render-artifact`.
2. If the source is any other `.md` file in the project:
   use `cg-publish-markdown`.
3. Generic routing still rejects typed roots — never use `cg-publish-markdown`
   on `.cg-docs/brainstorms/` or `.cg-docs/plans/` sources.

## Theme Selection

- `--theme reference` selects the reference theme (default for all document types).
- `--theme editorial` selects the editorial theme.
- When `--theme` is omitted, the CLI uses the document-type default (`reference`).
- Agents may **recommend** a theme but must **never silently select** one.
  Always ask the user before passing `--theme editorial`.

## Modes

| Mode | Flag | Behavior |
|------|------|----------|
| Render | (default) | Validate, render, and write the HTML view. |
| Check | `--check` | Report `current`, `stale`, or `missing` without writing. |
| Validate-only | `--validate-only` | Validate source, resources, paths, and theme without output I/O. |
| Automatic | `--automatic` | Validate, then publish only when `artifact-html` is enabled in config. |

## Output

- Typed artifacts: `.cg-docs/views/<category>/<name>.html`
- Generic documents: `.cg-docs/views/documents/<path>.html`
- Output paths are deterministic and mirror the source structure.

## Recovery

If a render fails, the CLI prints the exact recovery command. Re-run it
verbatim after fixing the reported error.