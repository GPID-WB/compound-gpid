"""Frozen editorial presentation contract, version 1.

Pinned from the editorial-brief design system (blob 8176439ea8ea60cdb6c541a8fdd6baced3dbc6cf)
and template (blob aefb61c65acecc2ec07878191d9a28191fc8aed2) on the
refactor/modular-compound-gpid branch at commit 52fc749ed484af2246dd7152b032f4dd01e86621.
"""
from __future__ import annotations

from copy import deepcopy

EDITORIAL_CONTRACT_VERSION = 1

_DESIGN_CONTRACT = {
    "schemaVersion": 1,
    "tokens": {
        "ink": "#181816",
        "muted": "#5d625f",
        "paper": "#fbfbf8",
        "white": "#ffffff",
        "line": "#d8dcd8",
        "softLine": "#e9ebe8",
        "coral": "#e94f2d",
        "coralSoft": "#fff0eb",
        "teal": "#087c70",
        "tealSoft": "#e8f5f2",
        "blue": "#2856c7",
        "blueSoft": "#edf1ff",
        "yellow": "#f2c84b",
        "yellowSoft": "#fff8dc",
        "success": "#18734c",
        "danger": "#b8322a",
    },
    "typography": {
        "display": ["Georgia", "Times New Roman", "serif"],
        "interface": ["Trebuchet MS", "Gill Sans", "sans-serif"],
        "code": ["Consolas", "Courier New", "monospace"],
        "baseSize": "17px",
        "letterSpacing": "0",
    },
    "layout": {
        "measure": "1180px",
        "desktopColumns": "minmax(0, 1.45fr) minmax(320px, 0.75fr)",
        "readingFlow": "unframed",
        "mobileColumns": "1fr",
    },
    "breakpoints": ["980px", "720px"],
    "focus": {
        "outlineWidth": "3px",
        "outlineOffset": "3px",
        "colorToken": "blue",
    },
    "motion": {
        "smoothScroll": True,
        "reduced": True,
    },
    "print": {
        "margin": "auto",
        "preservesCanonicalContent": True,
        "repeatsTableHeaders": True,
        "printsLinkTargets": False,
    },
    "components": {
        "persistentNavigation": True,
        "overflowTables": True,
        "visibleRawSource": True,
        "nestedCards": False,
    },
}

_EDITORIAL_CSS = """
:root {
  color-scheme: light;
  --ink: #181816;
  --muted: #5d625f;
  --paper: #fbfbf8;
  --white: #ffffff;
  --line: #d8dcd8;
  --soft-line: #e9ebe8;
  --coral: #e94f2d;
  --coral-soft: #fff0eb;
  --teal: #087c70;
  --teal-soft: #e8f5f2;
  --blue: #2856c7;
  --blue-soft: #edf1ff;
  --yellow: #f2c84b;
  --yellow-soft: #fff8dc;
  --success: #18734c;
  --danger: #b8322a;
  --content: 1180px;
  --radius: 6px;
  --header-height: 64px;
  --measure: 1180px;
  font-family: "Trebuchet MS", "Gill Sans", sans-serif;
  font-size: 17px;
  line-height: 1.65;
  letter-spacing: 0;
}
* { box-sizing: border-box; }
html { background: var(--paper); color: var(--ink); scroll-behavior: smooth; }
body { margin: 0; min-width: 20rem; }
a { color: var(--blue); text-underline-offset: .18em; }
a:focus-visible, summary:focus-visible { outline: 3px solid var(--blue); outline-offset: 3px; }
.skip-link { position: absolute; left: .75rem; top: -5rem; z-index: 10; background: var(--ink); color: var(--white); padding: .6rem .8rem; border-radius: 4px; }
.skip-link:focus { top: .75rem; }
.masthead { border-bottom: 1px solid var(--line); background: var(--white); }
.masthead-inner { max-width: var(--measure); margin: 0 auto; padding: 1.6rem clamp(1rem, 4vw, 3rem); }
.eyebrow { margin: 0 0 .45rem; color: var(--coral); font-size: .78rem; font-weight: 750; text-transform: uppercase; }
h1, h2, h3, h4, h5, h6 { font-family: Georgia, "Times New Roman", serif; line-height: 1.08; margin: 1.5em 0 .55em; overflow-wrap: anywhere; letter-spacing: 0; }
h1 { margin: 0; font-size: 3rem; }
.deck { max-width: 58rem; margin: .75rem 0 0; color: var(--muted); }
.layout { max-width: var(--measure); margin: 0 auto; display: grid; grid-template-columns: minmax(12rem, 18rem) minmax(0, 1fr); gap: clamp(1.5rem, 4vw, 4rem); padding: 2rem clamp(1rem, 4vw, 3rem) 4rem; }
.sidebar { align-self: start; position: sticky; top: 1rem; max-height: calc(100vh - 2rem); overflow: auto; border-left: 4px solid var(--coral); padding-left: 1rem; }
.sidebar h2 { font-family: inherit; font-size: .82rem; text-transform: uppercase; margin: 0 0 .7rem; }
.sidebar ul { list-style: none; margin: 0; padding: 0; }
.sidebar li + li { margin-top: .45rem; }
main { min-width: 0; }
.derived-panel { border-top: 1px solid var(--line); border-bottom: 1px solid var(--line); padding: 1rem 0; margin: 0 0 1.5rem; }
.derived-panel h2 { font-size: 1.3rem; margin: 0 0 .65rem; }
.phase-list, .coverage-list { display: grid; gap: .55rem; padding-left: 1.25rem; }
.source-block { min-width: 0; }
.source-block > :first-child { margin-top: 0; }
.source-heading { scroll-margin-top: 1rem; }
p, li, td, th, code { overflow-wrap: anywhere; }
pre { max-width: 100%; overflow: auto; padding: 1rem; background: #f1f1ed; border-left: 4px solid var(--coral); white-space: pre; border-radius: 3px; }
code { font-family: Consolas, "Courier New", monospace; font-size: .88em; }
:not(pre) > code { background: #f1f1ed; padding: .08em .3em; border: 1px solid #d9d9d3; border-radius: 3px; }
table { width: 100%; border-collapse: collapse; display: block; overflow-x: auto; margin: 1rem 0 1.5rem; }
th, td { border: 1px solid var(--line); padding: .55rem .7rem; text-align: left; vertical-align: top; min-width: 8rem; }
th { background: #e8f5f2; }
blockquote { margin: 1rem 0; padding: .2rem 0 .2rem 1rem; border-left: 4px solid var(--coral); color: var(--muted); }
.raw-source { border: 1px solid var(--line); margin: 1rem 0; border-radius: var(--radius); }
.raw-source figcaption { padding: .45rem .7rem; background: var(--coral-soft); font-weight: 700; }
.raw-source pre { margin: 0; border: 0; }
.provenance { border-top: 1px solid var(--line); background: var(--white); }
.provenance-inner { max-width: var(--measure); margin: 0 auto; padding: 1.5rem clamp(1rem, 4vw, 3rem); }
.provenance dl { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: .35rem 1rem; }
.provenance dt { font-weight: 700; }
.provenance dd { margin: 0; overflow-wrap: anywhere; }
@media (max-width: 980px) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; max-height: none; border-left: 0; border-bottom: 1px solid var(--line); padding: 0 0 1rem; }
  h1 { font-size: 2.15rem; }
  .provenance dl { grid-template-columns: 1fr; }
  .provenance dd + dt { margin-top: .5rem; }
}
@media (max-width: 720px) {
  body { font-size: 16px; }
  h1 { font-size: 1.8rem; }
  h2 { font-size: 1.5rem; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
}
@media print {
  :root { --paper: #fff; --white: #fff; --ink: #000; --muted: #222; }
  @page { margin: 15mm; }
  .skip-link, .sidebar { display: none; }
  .layout { display: block; max-width: none; padding: 0; }
  .masthead-inner, .provenance-inner { max-width: none; padding: 0; }
  .masthead { border: 0; margin-bottom: 1rem; }
  a { color: #000; text-decoration: underline; }
  a[href]::after { content: " (" attr(href) ")"; font-size: .8em; }
  pre, table, blockquote, .raw-source { break-inside: avoid; }
  thead { display: table-header-group; }
  h1, h2, h3, h4 { break-after: avoid; }
  .provenance { margin-top: 1rem; }
}
""".strip()


def editorial_design_contract() -> dict:
    """Return a defensive copy of the version-1 editorial design contract.

    Args:
        None.

    Returns:
        Frozen token and semantic component mapping for the editorial theme.

    Example:
        ``editorial_design_contract()['schemaVersion']`` returns 1.
    """
    return deepcopy(_DESIGN_CONTRACT)


def editorial_css() -> str:
    """Return the immutable version-1 editorial stylesheet.

    Pinned from the editorial-brief template at blob
    aefb61c65acecc2ec07878191d9a28191fc8aed2.

    Args:
        None.

    Returns:
        Complete self-contained editorial stylesheet.

    Example:
        ``'@media print' in editorial_css()`` is true.
    """
    return _EDITORIAL_CSS