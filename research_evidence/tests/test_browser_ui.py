"""Created 2026-08-13. Browser review-flow smoke tests over the local API app."""
from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from research_evidence.api.service import create_app
from research_evidence.config import RuntimeSettings


def _client(tmp_path: Path) -> TestClient:
    """Create an isolated local app client for browser smoke tests."""
    resources = tmp_path / "resources"
    resources.mkdir()
    (resources / "findings.md").write_text(
        "# Findings\n\nWeighted poverty fell by four points.",
        encoding="utf-8",
    )
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


def test_review_page_shows_local_caveat_and_canonical_state_boundary(tmp_path: Path) -> None:
    """Make confidence/caveat language visible without making browser state canonical."""
    client = _client(tmp_path)
    html = client.get("/ui").text

    assert "original files remain authoritative" in html.lower()
    assert "candidate" in html.lower()
    assert "local-only" in html.lower()
    assert "fetch(" in html
    assert "window.location" not in html
