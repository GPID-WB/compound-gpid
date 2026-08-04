---
name: cg-skill-render-doc
description: "Publishing workflow for rendering workflow artifacts and generic Markdown documents to curated HTML. Routes typed artifacts to cg-render-artifact and generic documents to cg-publish-markdown. Supports --theme selection (reference or editorial), check, validation, and constrained output modes. Agents may recommend but never silently select themes."
---

# Render Doc

Publishing skill for the two-theme curated HTML rendering pipeline. Routes
typed workflow artifacts and generic Markdown documents to the correct
deterministic CLI tool with explicit theme selection.

## Quick Reference

| Task | Tool | Key Flag |
|------|------|----------|
| Render typed artifact | `cg-render-artifact` | `--theme reference|editorial` |
| Render generic document | `cg-publish-markdown` | `--theme reference|editorial` |
| Check freshness | `cg-render-artifact --check` | `--theme` optional |
| Validate only | `cg-render-artifact --validate-only` | `--theme` optional |
| Automatic (config-gated) | `cg-render-artifact --automatic` | `--theme` optional |

## Workflows

- [Render a Document](workflows/render-document.md)
- [Check Freshness](workflows/check-freshness.md)

## References

- [Theme Reference](references/theme-reference.md)
- [CLI Reference](references/cli-reference.md)