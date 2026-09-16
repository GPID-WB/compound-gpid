"""Created 2026-08-13. Browser review-flow smoke tests over the local API app."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from research_evidence.api.service import create_app
from research_evidence.config import RuntimeSettings


def _client(tmp_path: Path, source_text: str = "Weighted poverty fell by four points.") -> TestClient:
    """Create an isolated local app client for browser smoke tests."""
    resources = tmp_path / "resources"
    resources.mkdir()
    (resources / "findings.md").write_text(f"# Findings\n\n{source_text}", encoding="utf-8")
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    return TestClient(create_app(settings))


def test_review_page_is_derived_local_html_with_expected_workbench_surfaces(tmp_path: Path) -> None:
    """Expose the actual review workflow as a local responsive HTML view."""
    client = _client(tmp_path)
    response = client.get("/")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/html")
    html = response.text
    for label in (
        "Resource inventory",
        "Source search",
        "Candidate evidence",
        "Review queue",
        "Review history",
        "Run status",
        "Dependency caveats",
    ):
        assert label in html
    assert "@media" in html
    assert "/sources/search" in html
    assert "/review/history" in html
    assert "http://" not in html
    assert "https://" not in html
    assert "Content-Security-Policy" in html


def test_review_page_shows_local_caveat_and_canonical_state_boundary(tmp_path: Path) -> None:
    """Make confidence/caveat language visible without making browser state canonical."""
    client = _client(tmp_path)
    html = client.get("/ui").text

    assert "original files remain authoritative" in html.lower()
    assert "candidate" in html.lower()
    assert "local-only" in html.lower()
    assert "fetch(" in html
    assert "window.location" not in html


def test_malicious_source_text_is_not_server_rendered_into_review_page(tmp_path: Path) -> None:
    """Keep untrusted source markup in the API data boundary, not page HTML."""
    payload = '<img src=x onerror="alert(1)">'
    client = _client(tmp_path, payload)
    scanned = client.post("/resources/scan", json={"path": "findings.md"})
    assert scanned.status_code == 200
    results = client.get("/sources/search", params={"q": "alert"}).json()
    assert results["results"][0]["text"] == payload
    page = client.get("/")
    assert payload not in page.text
    assert "default-src 'self'" in page.text
