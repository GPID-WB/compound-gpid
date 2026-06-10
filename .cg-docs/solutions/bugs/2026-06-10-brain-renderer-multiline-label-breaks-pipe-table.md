---
date: 2026-06-10
title: "Brain renderer inserts multi-line topic labels into pipe table cells, breaking Markdown"
category: "bugs"
language: "Python"
tags: [brain, renderer, markdown, pipe-table, cluster-label, sanitize, BRAIN.md]
root-cause: "scripts/brain/renderer.py wrote topic.label directly into a Markdown pipe table without collapsing embedded newlines, so multi-word cluster labels spanning multiple physical lines broke the table row"
severity: "P3"
plan: null
reviewed-in: ".cg-docs/reviews/2026-06-09-token-optimization-phase7-release-validation-review-2.md"
related: []
---

# Brain Renderer Inserts Multi-Line Topic Labels Into Pipe Table Cells

## Problem

After a `cg-index --brain` rebuild, the `BRAIN.md` Topic Index table contained
broken rows for topics whose cluster labels spanned multiple lines. GitHub and
VS Code Preview rendered the trailing lines as stray text or additional broken
rows, not as part of the table.

Example of the broken output in `BRAIN.md`:

```markdown
| 2 | [Architecture Research
Objective / Knowledge Brain
Objective / Quality Loop
Objective](BRAIN-01.md#...) | 108 | BRAIN-01.md |
```

The table became unparseable for Topic 2 because Markdown pipe tables require
each row to be a single physical line.

## Root Cause

In `scripts/brain/renderer.py`, the Topic Index table was built by interpolating
`topic.label` directly into the table row string:

```python
lines.append(
    f"| {i} | [{topic.label}]({file_name}#{anchor}) "
    f"| {len(topic.entity_paths)} | {file_name} |"
)
```

`topic.label` is the raw cluster label produced by the topic clusterer. When
the clusterer generates a multi-word label across several entity titles
(separated by newlines), the label carries those embedded `\n` characters into
the rendered table row.

The renderer already had a `_sanitize_inline()` function that strips newlines
and escapes characters unsafe in Markdown link syntax, but it was applied only
to entity titles (`_entity_line()`), not to topic labels in the BRAIN.md index.

## Solution

Apply `_sanitize_inline()` to the topic label before inserting it into the
pipe table:

```python
# Before (broken)
lines.append(
    f"| {i} | [{topic.label}]({file_name}#{anchor}) "
    f"| {len(topic.entity_paths)} | {file_name} |"
)

# After (fixed)
label = _sanitize_inline(topic.label)
lines.append(
    f"| {i} | [{label}]({file_name}#{anchor}) "
    f"| {len(topic.entity_paths)} | {file_name} |"
)
```

`_sanitize_inline()` replaces `\n` with a space and escapes `]`, `(`, `)`, and
`[` characters. The resulting label is safe for inline Markdown link text and
always fits on a single line.

## Prevention

1. **Apply `_sanitize_inline()` to all user-facing string interpolations in
   the renderer**: not just entity titles. Before inserting any field that
   originates from external data (cluster labels, entity summaries, frontmatter
   values) into a Markdown structure, sanitize it.

2. **Add a regression test**: the test suite should include a brain rebuild
   with a topic whose cluster label contains embedded newlines and assert that
   the rendered BRAIN.md table row is a single line. This prevents silent
   re-introduction of the bug after future clusterer changes.

3. **Keep `_sanitize_inline()` as the single gateway**: all renderer output
   paths that produce inline Markdown content (link text, table cells, list
   item titles) should route through `_sanitize_inline()`. Do not add ad hoc
   `str.replace("\n", " ")` calls at individual call sites.

## Related

- `scripts/brain/renderer.py` — the fixed file
- `scripts/brain/tests/test_renderer.py` — existing renderer tests (regression test should be added here)
