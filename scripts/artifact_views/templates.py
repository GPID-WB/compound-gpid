"""Self-contained semantic HTML shell for artifact views."""
from __future__ import annotations

from copy import deepcopy
from html import escape

from artifact_views.provenance import ArtifactProvenance

_DESIGN_CONTRACT = {
  "schemaVersion": 1,
  "tokens": {
    "paper": "#f6f5f0",
    "surface": "#ffffff",
    "ink": "#17212b",
    "muted": "#59636d",
    "line": "#c8cdd1",
    "accent": "#006b5f",
    "accentStrong": "#004d45",
    "signal": "#a63d21",
    "code": "#eef1f3",
    "focus": "#d43f00"
  },
  "typography": {
    "display": ["Iowan Old Style", "Palatino Linotype", "serif"],
    "interface": ["Avenir Next", "Segoe UI", "sans-serif"],
    "code": ["SFMono-Regular", "Consolas", "monospace"],
    "baseSize": "16px",
    "letterSpacing": "0"
  },
  "layout": {
    "measure": "78rem",
    "desktopColumns": "minmax(12rem, 18rem) minmax(0, 1fr)",
    "readingFlow": "unframed",
    "mobileColumns": "1fr"
  },
  "breakpoints": ["48rem"],
  "focus": {
    "outlineWidth": "3px",
    "outlineOffset": "3px",
    "colorToken": "focus"
  },
  "motion": {
    "smoothScroll": True,
    "reduced": True
  },
  "print": {
    "margin": "15mm",
    "preservesCanonicalContent": True,
    "repeatsTableHeaders": True,
    "printsLinkTargets": True
  },
  "components": {
    "persistentNavigation": True,
    "overflowTables": True,
    "visibleRawSource": True,
    "nestedCards": False
  }
}


def design_contract() -> dict:
    """Return a defensive copy of the frozen presentation contract.

    Args:
        None.

    Returns:
        Versioned design tokens and semantic component rules used by templates.

    Example:
        >>> design_contract()["schemaVersion"]
        1
    """
    return deepcopy(_DESIGN_CONTRACT)

_BASE_CSS = """
:root {
  color-scheme: light;
  --paper: #f6f5f0;
  --surface: #ffffff;
  --ink: #17212b;
  --muted: #59636d;
  --line: #c8cdd1;
  --accent: #006b5f;
  --accent-strong: #004d45;
  --signal: #a63d21;
  --code: #eef1f3;
  --focus: #d43f00;
  --measure: 78rem;
  font-family: "Avenir Next", "Segoe UI", sans-serif;
  font-size: 16px;
  line-height: 1.55;
}
* { box-sizing: border-box; }
html { background: var(--paper); color: var(--ink); scroll-behavior: smooth; }
body { margin: 0; min-width: 20rem; }
a { color: var(--accent-strong); text-underline-offset: .18em; }
a:focus-visible, summary:focus-visible { outline: 3px solid var(--focus); outline-offset: 3px; }
.skip-link { position: absolute; left: .75rem; top: -5rem; z-index: 10; background: var(--ink); color: white; padding: .6rem .8rem; }
.skip-link:focus { top: .75rem; }
.masthead { border-bottom: 1px solid var(--line); background: var(--surface); }
.masthead-inner { max-width: var(--measure); margin: 0 auto; padding: 1.6rem clamp(1rem, 4vw, 3rem); }
.eyebrow { margin: 0 0 .45rem; color: var(--accent-strong); font-size: .78rem; font-weight: 750; text-transform: uppercase; }
h1, h2, h3, h4, h5, h6 { font-family: "Iowan Old Style", "Palatino Linotype", serif; line-height: 1.16; margin: 1.5em 0 .55em; overflow-wrap: anywhere; }
h1 { margin: 0; font-size: 3.4rem; }
.deck { max-width: 58rem; margin: .75rem 0 0; color: var(--muted); }
.layout { max-width: var(--measure); margin: 0 auto; display: grid; grid-template-columns: minmax(12rem, 18rem) minmax(0, 1fr); gap: clamp(1.5rem, 4vw, 4rem); padding: 2rem clamp(1rem, 4vw, 3rem) 4rem; }
.sidebar { align-self: start; position: sticky; top: 1rem; max-height: calc(100vh - 2rem); overflow: auto; border-left: 4px solid var(--accent); padding-left: 1rem; }
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
pre { max-width: 100%; overflow: auto; padding: 1rem; background: var(--code); border-left: 4px solid var(--accent); white-space: pre; }
code { font-family: "SFMono-Regular", Consolas, monospace; font-size: .88em; }
:not(pre) > code { background: var(--code); padding: .08em .3em; }
table { width: 100%; border-collapse: collapse; display: block; overflow-x: auto; margin: 1rem 0 1.5rem; }
th, td { border: 1px solid var(--line); padding: .55rem .7rem; text-align: left; vertical-align: top; min-width: 8rem; }
th { background: #e6ece9; }
blockquote { margin: 1rem 0; padding: .2rem 0 .2rem 1rem; border-left: 4px solid var(--signal); color: var(--muted); }
.raw-source { border: 1px solid var(--line); margin: 1rem 0; }
.raw-source figcaption { padding: .45rem .7rem; background: #f0e9e5; font-weight: 700; }
.raw-source pre { margin: 0; border: 0; }
.provenance { border-top: 1px solid var(--line); background: var(--surface); }
.provenance-inner { max-width: var(--measure); margin: 0 auto; padding: 1.5rem clamp(1rem, 4vw, 3rem); }
.provenance dl { display: grid; grid-template-columns: max-content minmax(0, 1fr); gap: .35rem 1rem; }
.provenance dt { font-weight: 700; }
.provenance dd { margin: 0; overflow-wrap: anywhere; }
@media (max-width: 48rem) {
  .layout { grid-template-columns: 1fr; }
  .sidebar { position: static; max-height: none; border-left: 0; border-bottom: 1px solid var(--line); padding: 0 0 1rem; }
  h1 { font-size: 2.15rem; }
  .provenance dl { grid-template-columns: 1fr; }
  .provenance dd + dt { margin-top: .5rem; }
}
@media (prefers-reduced-motion: reduce) {
  html { scroll-behavior: auto; }
}
@media print {
  :root { --paper: #fff; --surface: #fff; --ink: #000; --muted: #222; }
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


def render_html_shell(
    *,
    artifact_kind: str,
    title: str,
    eyebrow: str,
    deck: str,
    canonical_href: str,
    navigation_html: str,
    derived_html: str,
    body_html: str,
    provenance: ArtifactProvenance,
) -> bytes:
    """Serialize a complete deterministic self-contained HTML document.

    Args:
        artifact_kind: Brainstorm or Plan identity for the body dataset.
        title: Visible document title.
        eyebrow: Short artifact-type label.
        deck: Supporting authority description.
        canonical_href: Relative link to canonical Markdown.
        navigation_html: Trusted renderer-produced navigation markup.
        derived_html: Trusted renderer-produced derived maps.
        body_html: Trusted escaped source-block markup.
        provenance: Complete source and generation identity.

    Returns:
        Complete UTF-8 encoded HTML bytes.

    Example:
        The semantic renderer supplies escaped fragments and receives one
        self-contained byte string from this function.
    """
    provenance_json = provenance.to_json().replace("<", "\\u003c")
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; object-src 'none'; frame-src 'none'; media-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="artifact-source" content="{escape(provenance.source_path, quote=True)}">
<meta name="artifact-source-sha256" content="{escape(provenance.source_sha256, quote=True)}">
<meta name="artifact-schema-version" content="{escape(str(provenance.artifact_schema_version), quote=True)}">
<meta name="artifact-renderer-version" content="{escape(provenance.renderer_version, quote=True)}">
<title>{escape(title)} · Compound GPID</title>
<style>{_BASE_CSS}</style>
<script id="artifact-provenance" type="application/json">{provenance_json}</script>
</head>
<body data-artifact-kind="{escape(artifact_kind, quote=True)}">
<a class="skip-link" href="#main-content">Skip to artifact content</a>
<header class="masthead">
  <div class="masthead-inner">
    <p class="eyebrow">{escape(eyebrow)}</p>
    <h1>{escape(title)}</h1>
    <p class="deck">{escape(deck)} <a href="{escape(canonical_href, quote=True)}">Open canonical Markdown</a>.</p>
  </div>
</header>
<div class="layout">
  <nav class="sidebar" aria-label="Artifact sections" data-derived="navigation">
    <h2>On this page</h2>
    {navigation_html}
  </nav>
  <main id="main-content" tabindex="-1">
    {derived_html}
    <article aria-label="Canonical artifact content">
      {body_html}
    </article>
  </main>
</div>
<footer class="provenance" aria-labelledby="provenance-heading">
  <div class="provenance-inner">
    <h2 id="provenance-heading">Derived view provenance</h2>
    <p>This HTML is regenerable. Canonical Markdown remains authoritative.</p>
    <dl>
      <dt>Source</dt><dd>{escape(provenance.source_path)}</dd>
      <dt>Source SHA-256</dt><dd><code>{escape(provenance.source_sha256)}</code></dd>
      <dt>Artifact schema</dt><dd>{escape(str(provenance.artifact_schema_version))}</dd>
      <dt>Renderer</dt><dd>{escape(provenance.renderer_version)}</dd>
      <dt>Generated UTC</dt><dd>{escape(provenance.generated_at)}</dd>
    </dl>
  </div>
</footer>
</body>
</html>
"""
    return document.encode("utf-8")
