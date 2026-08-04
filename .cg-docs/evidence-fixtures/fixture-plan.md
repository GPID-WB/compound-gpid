---
title: "Editorial Theme Implementation Plan"
date: 2026-08-03
status: draft
tags: [editorial, implementation, themes, publishing]
---

# Editorial Theme Implementation Plan

## Overview

Port the editorial visual system as a second HTML presentation theme alongside
the existing `reference` theme in the GPID curated HTML publishing pipeline.

## Architecture

The theme system uses a `_THEMES` registry in `themes.py`. Each theme provides:
- A **design contract** (frozen dict of design tokens)
- A **stylesheet** (CSS string targeting shared HTML shell class names)

The HTML shell is rendered by `templates.py` `render_html_shell()`, which
injects `{theme.stylesheet}` into a `<style>` tag. Both themes must target the
same shell class names: `.skip-link`, `.masthead`, `.masthead-inner`, `.eyebrow`,
`.deck`, `.layout`, `.sidebar`, `.derived-panel`, `.source-block`,
`.source-heading`, `.raw-source`, `.provenance`, `.provenance-inner`.

## Implementation Steps

### Phase 1: Theme Module

1. Create `scripts/artifact_views/editorial_theme.py` with:
   - `_DESIGN_CONTRACT` dict (frozen design tokens)
   - `_EDITORIAL_CSS` string (adapted to shared shell class names)
   - `editorial_design_contract()` function
   - `editorial_css()` function

2. Register `"editorial"` in `themes.py` `_THEMES` dict.

3. Update tests in `test_themes.py`:
   - Verify both themes are registered
   - Cross-theme semantic comparison tests
   - Design token validation
   - CSS self-containment checks

### Phase 2: Publishing Skill

1. Create `.github/skills/cg-skill-render-doc/` with:
   - `SKILL.md` — skill definition
   - `workflows/render-document.md` — routing logic
   - `workflows/check-freshness.md` — freshness check
   - `references/theme-reference.md` — theme design contracts
   - `references/cli-reference.md` — CLI tools reference

2. Create `.github/prompts/cg-render-doc.prompt.md` with theme resolution rules.

3. Generate platform targets for Claude Code, Codex, and OpenCode.

### Phase 3: Browser Evidence

1. Add `package.json` with Playwright and axe-core dependencies.
2. Create evidence capture script using Playwright.
3. Add Node.js tests for the capture script.
4. Add Python evidence validation tests for schema 2.

### Phase 4: Documentation

1. Document the curated publishing workflow.
2. Verify all gates pass (Python tests, Pester tests, Node tests).
3. Produce final browser evidence for both themes.

## Design Tokens (Editorial)

| Token | Value |
|-------|-------|
| Background | `#fbfbf8` (warm paper) |
| Text | `#181816` (ink) |
| Muted | `#5d625f` |
| Accent Coral | `#e94f2d` |
| Accent Teal | `#087c70` |
| Accent Blue | `#2856c7` |
| Accent Yellow | `#f2c84b` |
| Success | `#18734c` |
| Danger | `#b8322a` |
| Display Font | Georgia |
| Body Font | Trebuchet MS |
| Code Font | Consolas |
| Max Width | 1180px |
| Breakpoints | 980px, 720px |
| Border Radius | ≤ 6px |

## Constraints

- The editorial CSS must target the same HTML shell class names as reference.
- Print styles must be self-contained within the theme CSS.
- All color pairs must meet WCAG AA contrast ratios.
- The theme must not require any template changes.
