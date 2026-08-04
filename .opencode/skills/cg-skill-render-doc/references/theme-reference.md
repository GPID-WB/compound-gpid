# Theme Reference

The curated HTML pipeline supports two presentation-only themes. Both themes
render the same semantic HTML structure — only CSS presentation differs.

## Registered Themes

| Theme | Contract Version | Default For | Description |
|-------|-----------------|-------------|-------------|
| `reference` | 1 | All document types | Clean, minimal reference style with Iowan Old Style display, Avenir Next body, single accent color. |
| `editorial` | 1 | None (explicit only) | Warm paper editorial style with Georgia display, Trebuchet body, multi-accent palette (coral, teal, blue, yellow). |

## Design Contracts

Both themes are frozen at contract version 1. The design tokens are immutable
and verified at test time. Runtime has no Git dependency — all tokens are
embedded in the theme module.

### Reference Theme

- **Palette**: neutral background, single accent color
- **Typography**: Iowan Old Style (display), Avenir Next (body), SF Mono (code)
- **Layout**: 78rem max width, 48rem single breakpoint
- **Radius**: ≤ 6px

### Editorial Theme

- **Palette**: warm paper `#fbfbf8`, ink `#181816`, muted `#5d625f`, coral `#e94f2d`, teal `#087c70`, blue `#2856c7`, yellow `#f2c84b`
- **Typography**: Georgia (display), Trebuchet MS (body/control), Consolas (code)
- **Layout**: 1180px max width, 980px/720px breakpoints
- **Radius**: ≤ 6px

## Theme Resolution

1. Explicit `--theme` always wins.
2. Without `--theme`, the document-type default is used (`reference` for all types).
3. On re-render of an existing view, the recorded theme is reused unless `--theme` is explicit.
4. Unknown recorded themes block mutation until an explicit registered theme is supplied.

## Semantic Equivalence

Both themes target the same shared HTML shell class names:
`.skip-link`, `.masthead`, `.masthead-inner`, `.eyebrow`, `.deck`, `.layout`,
`.sidebar`, `.derived-panel`, `.source-block`, `.source-heading`, `.raw-source`,
`.provenance`, `.provenance-inner`.

Cross-theme semantic summaries must be identical — only CSS and presentation
metadata may differ between themes.