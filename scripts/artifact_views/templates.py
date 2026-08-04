"""Self-contained semantic HTML shell for artifact views."""
from __future__ import annotations

from html import escape
from typing import Union

from artifact_views.provenance import ArtifactProvenance, PublicationProvenance
from artifact_views.reference_theme import reference_design_contract
from artifact_views.themes import ThemeContract

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
    return reference_design_contract()


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
    provenance: Union[ArtifactProvenance, PublicationProvenance],
    theme: ThemeContract,
    navigation_label: str = "Artifact sections",
    article_label: str = "Canonical artifact content",
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
        theme: Resolved theme contract owning the serialized stylesheet.

    Returns:
        Complete UTF-8 encoded HTML bytes.

    Example:
        The semantic renderer supplies escaped fragments and receives one
        self-contained byte string from this function.
    """
    provenance_json = provenance.to_json().replace("<", "\\u003c")
    if isinstance(provenance, ArtifactProvenance):
        schema_meta = (
        '<meta name="artifact-schema-version" content="'
        f'{escape(str(provenance.artifact_schema_version), quote=True)}">'
        )
        provenance_rows = (
        f"      <dt>Artifact schema</dt><dd>{escape(str(provenance.artifact_schema_version))}</dd>\n"
        f"      <dt>Renderer</dt><dd>{escape(provenance.renderer_version)}</dd>\n"
        f"      <dt>Generated UTC</dt><dd>{escape(provenance.generated_at)}</dd>"
        )
    else:
        schema_meta = (
        '<meta name="publication-provenance-schema" content="2">\n'
        f'<meta name="publication-output" content="{escape(provenance.output_path, quote=True)}">\n'
        f'<meta name="publication-theme" content="{escape(provenance.theme_name, quote=True)}">'
        )
        provenance_rows = (
        f"      <dt>Output</dt><dd>{escape(provenance.output_path)}</dd>\n"
        f"      <dt>Document type</dt><dd>{escape(provenance.document_type)}</dd>\n"
        f"      <dt>Renderer</dt><dd>{escape(provenance.renderer_version)}</dd>\n"
        f"      <dt>Theme</dt><dd>{escape(provenance.theme_name)} v{provenance.theme_version}</dd>\n"
        f"      <dt>Generated UTC</dt><dd>{escape(provenance.generated_at)}</dd>"
        )
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; img-src data:; connect-src 'none'; object-src 'none'; frame-src 'none'; media-src 'none'; base-uri 'none'; form-action 'none'">
<meta name="artifact-source" content="{escape(provenance.source_path, quote=True)}">
<meta name="artifact-source-sha256" content="{escape(provenance.source_sha256, quote=True)}">
{schema_meta}
<meta name="artifact-renderer-version" content="{escape(provenance.renderer_version, quote=True)}">
<title>{escape(title)} · Compound GPID</title>
<style>{theme.stylesheet}</style>
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
  <nav class="sidebar" aria-label="{escape(navigation_label, quote=True)}" data-derived="navigation">
    <h2>On this page</h2>
    {navigation_html}
  </nav>
  <main id="main-content" tabindex="-1">
    {derived_html}
    <article aria-label="{escape(article_label, quote=True)}">
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
{provenance_rows}
    </dl>
  </div>
</footer>
</body>
</html>
"""
    return document.encode("utf-8")
