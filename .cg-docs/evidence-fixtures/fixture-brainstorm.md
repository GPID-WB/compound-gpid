---
title: "Editorial Theme Brainstorm — Design Token Exploration"
date: 2026-08-03
status: draft
tags: [editorial, design-system, themes, publishing]
---

# Editorial Theme Brainstorm

## Context

The GPID curated HTML publishing pipeline currently ships a single `reference`
theme. Stakeholders have requested a second visual presentation — an
**editorial** theme — suitable for institutional reports, policy briefs, and
long-form narrative documents.

## Design Goals

1. **Warm, authoritative tone**: The editorial theme should feel like a
   well-designed institutional publication — not a developer dashboard.
2. **Typography-first**: Georgia for display headings, Trebuchet MS for body
   text, Consolas for code. The type scale should be generous and readable.
3. **Restrained palette**: Warm paper background (`#fbfbf8`), dark ink text
   (`#181816`), muted secondary (`#5d625f`), with coral (`#e94f2d`), teal
   (`#087c70`), and blue (`#2856c7`) accents.
4. **Accessible by default**: All color pairs must meet WCAG AA contrast
   ratios. Focus indicators must be visible. The layout must work at 200% zoom
   without horizontal scroll.

## Open Questions

- Should the editorial theme use a serif or sans-serif body font?
  - **Decision**: Trebuchet MS (sans-serif) for body — it pairs well with
    Georgia headings and is widely available.
- Should the sidebar be on the left or right?
  - **Decision**: Right sidebar, matching the reference theme layout for
    semantic consistency.
- How should code blocks be styled?
  - **Decision**: Consolas on a slightly tinted background, with a subtle
    left border accent.

## Risks

- The editorial CSS must target the same HTML shell class names as the
  reference theme (`.masthead`, `.sidebar`, `.layout`, `.provenance`).
  Divergent class names would require template changes.
- Print styles must be self-contained within the theme CSS — no separate
  print stylesheet.
- The warm paper background must not reduce readability in high-brightness
  environments.

## Next Steps

1. Extract design tokens from the editorial template blob.
2. Adapt CSS to target shared shell class names.
3. Register the editorial theme in `themes.py`.
4. Add cross-theme semantic comparison tests.
5. Produce browser evidence for both themes.
