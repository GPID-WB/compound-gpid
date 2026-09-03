"""Created 2026-08-13. Same-origin responsive HTML review route."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import HTMLResponse

from ..api.service import EvidenceAPIService


_REVIEW_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'self'; connect-src 'self'; script-src 'unsafe-inline'; style-src 'unsafe-inline';">
<title>Evidence Workbench</title>
<style>
:root { color-scheme: light; --ink: #19242b; --muted: #5e6c73; --paper: #f6f3ed; --panel: #fffdf8; --line: #d8d4ca; --accent: #0b6e69; --warn: #a65b24; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--paper); color: var(--ink); font: 15px/1.5 Georgia, serif; }
header { padding: 2rem clamp(1rem, 5vw, 5rem) 1.25rem; border-bottom: 1px solid var(--line); }
h1 { margin: 0; font-size: clamp(1.8rem, 4vw, 3rem); letter-spacing: 0; }
main { display: grid; grid-template-columns: minmax(0, 1.4fr) minmax(18rem, .8fr); gap: 1rem; max-width: 1440px; margin: 0 auto; padding: 1rem clamp(1rem, 5vw, 5rem) 4rem; }
section { background: var(--panel); border: 1px solid var(--line); padding: 1rem; min-width: 0; }
section.primary { grid-row: span 2; }
h2 { margin: 0 0 .75rem; font: 700 1rem/1.2 ui-sans-serif, system-ui, sans-serif; letter-spacing: .04em; text-transform: uppercase; }
label { display: block; color: var(--muted); font: .8rem ui-sans-serif, system-ui, sans-serif; margin-bottom: .25rem; }
input, textarea, button { width: 100%; border: 1px solid var(--line); padding: .65rem .75rem; font: inherit; background: #fff; color: var(--ink); }
textarea { min-height: 7rem; resize: vertical; }
button { cursor: pointer; background: var(--accent); color: white; border-color: var(--accent); font: 700 .82rem ui-sans-serif, system-ui, sans-serif; margin-top: .5rem; }
button.secondary { background: transparent; color: var(--accent); }
.grid { display: grid; gap: .75rem; }
.row { display: grid; grid-template-columns: 1fr 1fr; gap: .75rem; }
.result, .event { border-top: 1px solid var(--line); padding: .75rem 0; }
.result:first-child, .event:first-child { border-top: 0; }
small, .meta { color: var(--muted); font: .78rem/1.4 ui-sans-serif, system-ui, sans-serif; }
.caveat { border-left: 3px solid var(--warn); padding-left: .75rem; color: #69401f; }
pre { white-space: pre-wrap; overflow-wrap: anywhere; margin: .5rem 0 0; }
@media (max-width: 760px) { main { display: block; padding: .75rem 1rem 3rem; } section { margin-bottom: .75rem; } .row { grid-template-columns: 1fr; } header { padding: 1.5rem 1rem 1rem; } }
</style>
</head>
<body>
<header><h1>Evidence Workbench</h1><div class="meta">Local review state · original files remain authoritative</div></header>
<main>
<section class="primary"><h2>Source search</h2><div class="grid"><div><label for="query">Query</label><input id="query" name="query" autocomplete="off"></div><button id="search">Search local source units</button><div id="results" aria-live="polite"></div></div></section>
<section><h2>Resource inventory</h2><div class="grid"><div><label for="resource">Project-relative Markdown path</label><input id="resource" value="findings.md"></div><button id="scan">Scan resource</button><div id="scan-status" class="meta"></div></div></section>
<section><h2>Candidate evidence</h2><div class="grid"><div><label for="source-unit">Selected source unit</label><input id="source-unit"></div><div><label for="statement">Atomic claim</label><textarea id="statement"></textarea></div><div><label for="quote">Verbatim quote</label><textarea id="quote"></textarea></div><button id="candidate">Create candidate</button><div id="candidate-status" class="meta"></div></div></section>
<section><h2>Review queue</h2><div id="queue" class="meta">Candidate records stay unapproved until independently verified.</div></section>
<section><h2>Review history</h2><div id="history" class="meta"></div></section>
<section><h2>Run status</h2><div id="status" class="meta"></div></section>
<section><h2>Dependency caveats</h2><p class="caveat">Local-only runtime. Candidate retrieval/OCR profiles require inventory, cache, licensing, performance, and explicit activation checks. Browser state is derived; canonical YAML and journal history are authoritative.</p></section>
</main>
<script>
const json = async (response) => { const body = await response.json(); if (!response.ok) throw body; return body; };
const el = (id) => document.getElementById(id);
const showResults = (payload) => { const results = el('results'); results.replaceChildren(); for (const item of payload.results || []) { const node = document.createElement('article'); node.className = 'result'; const strong = document.createElement('strong'); strong.textContent = item.text; const meta = document.createElement('div'); meta.className = 'meta'; meta.textContent = `${item.source_unit_id} · ${item.locator.kind} · ${item.source_version_id}`; node.append(strong, meta); node.addEventListener('click', () => { el('source-unit').value = item.source_unit_id; el('statement').value = item.text; el('quote').value = item.text; }); results.appendChild(node); } };
el('search').addEventListener('click', async () => { try { showResults(await json(await fetch(`/sources/search?q=${encodeURIComponent(el('query').value)}`))); } catch (error) { el('results').textContent = error.error || 'Search failed'; } });
el('scan').addEventListener('click', async () => { try { const data = await json(await fetch('/resources/scan', { method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({path: el('resource').value}) })); el('scan-status').textContent = `Scanned at revision ${data.revision}`; } catch (error) { el('scan-status').textContent = error.error || 'Scan failed'; } });
el('candidate').addEventListener('click', async () => { try { const data = await json(await fetch('/evidence/candidates', { method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify({source_unit_id: el('source-unit').value, statement: el('statement').value, quote: el('quote').value, relation: 'supports'}) })); el('candidate-status').textContent = `Candidate ${data.evidence.evidence_id} created at revision ${data.revision}`; } catch (error) { el('candidate-status').textContent = error.error || 'Candidate creation failed'; } });
const refresh = async () => { try { const status = await json(await fetch('/run/status')); el('status').textContent = `Canonical revision ${status.revision}`; const history = await json(await fetch('/review/history')); const historyNode = el('history'); historyNode.replaceChildren(); for (const event of history.events || []) { const node = document.createElement('div'); node.className = 'event'; node.textContent = `${event.action} · ${event.target_id} · revision ${event.revision}`; historyNode.appendChild(node); } } catch (error) { el('status').textContent = error.error || 'Status unavailable'; } };
refresh();
</script>
</body>
</html>"""


def register_ui_routes(app: FastAPI, service: EvidenceAPIService) -> None:
    """Register same-origin responsive review routes on a local API app.

    Args:
        app: FastAPI application receiving the routes.
        service: Local API service whose state the view reads.

    Returns:
        ``None`` after root and ``/ui`` routes are registered.

    Example:
        ``register_ui_routes(app, service)`` adds the derived browser surface.
    """

    @app.get("/", response_class=HTMLResponse)
    @app.get("/ui", response_class=HTMLResponse)
    def review_page() -> HTMLResponse:
        """Return the derived local browser review page.

        Args:
            None.

        Returns:
            Responsive HTML that uses same-origin API paths only.

        Example:
            ``GET /`` opens the local evidence review flow.
        """
        return HTMLResponse(_REVIEW_PAGE)
