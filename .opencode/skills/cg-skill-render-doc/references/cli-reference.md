# CLI Reference

Deterministic command-line tools for the curated HTML publishing pipeline.

## cg-render-artifact

Validate, render, or check one typed workflow artifact (brainstorm or plan).

```bash
cg-render-artifact [--theme <name>] [--check|--validate-only|--automatic] <source.md>
```

**Source**: Must be under `.cg-docs/brainstorms/` or `.cg-docs/plans/`.
**Output**: `.cg-docs/views/<category>/<name>.html`

### Flags

| Flag | Description |
|------|-------------|
| `--theme reference|editorial` | Explicit theme selection. |
| `--check` | Report current, stale, or missing without writing. |
| `--validate-only` | Validate source, resources, paths, and theme without output I/O. |
| `--automatic` | Validate, then publish only when `artifact-html` is enabled in config. |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success or current |
| 1 | Failure, stale, or missing |
| 2 | Invalid input, source, resource, path, or theme |

## cg-publish-markdown

Validate, render, or check one generic Markdown document.

```bash
cg-publish-markdown [--theme <name>] [--check|--validate-only|--automatic] [--output <path>] <source.md>
```

**Source**: Any project-contained `.md` file outside `.cg-docs/brainstorms/`, `.cg-docs/plans/`, and `.cg-docs/views/`.
**Output**: `.cg-docs/views/documents/<path>.html` (default mirrors source structure).

### Flags

| Flag | Description |
|------|-------------|
| `--theme reference|editorial` | Explicit theme selection. |
| `--check` | Report current, stale, or missing without writing. |
| `--validate-only` | Validate source, resources, paths, and theme without output I/O. |
| `--automatic` | Validate, then publish only when `artifact-html` is enabled in config. |
| `--output <path>` | Portable relative `.html` path under `.cg-docs/views/documents/`. |

### Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success or current |
| 1 | Failure, stale, or missing |
| 2 | Invalid input, source, resource, path, or theme |

## Platform Support

Both tools are available on all supported platforms via committed launchers:

| Platform | Launcher |
|----------|----------|
| Unix (bash) | `bin/cg-render-artifact`, `bin/cg-publish-markdown` |
| Windows (cmd) | `bin/cg-render-artifact.cmd`, `bin/cg-publish-markdown.cmd` |