"""Created 2026-08-13. Tests for the loopback-only FastAPI service."""
from __future__ import annotations

from pathlib import Path
import socket

import pytest

from research_evidence.api.service import create_app
from research_evidence.config import RuntimeSettings
from research_evidence.errors import NetworkAccessDenied


def _client(tmp_path: Path):
    """Create a local service client over one isolated Markdown resource."""
    from fastapi.testclient import TestClient

    resources = tmp_path / "resources"
    resources.mkdir()
    (resources / "findings.md").write_text(
        "# Findings\n\nWeighted poverty fell by four points.",
        encoding="utf-8",
    )
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    return TestClient(create_app(settings))


def test_non_loopback_app_creation_is_rejected(tmp_path: Path) -> None:
    """Reject a service configuration that could expose the workbench remotely."""
    resources = tmp_path / "resources"
    resources.mkdir()
    settings = RuntimeSettings.from_paths(tmp_path, resources)
    with pytest.raises(ValueError, match="loopback"):
        create_app(settings, bind_host="0.0.0.0")


def test_health_scan_search_and_source_context_are_local(tmp_path: Path) -> None:
    """Expose provenance-rich local scan, search, and source-context views."""
    client = _client(tmp_path)
    assert client.get("/health").json()["status"] == "active"

    scanned = client.post("/resources/scan", json={"path": "findings.md"})
    assert scanned.status_code == 200
    source_unit_id = scanned.json()["units"][1]["source_unit_id"]

    search = client.get("/sources/search", params={"q": "weighted poverty"})
    assert search.status_code == 200
    assert search.json()["results"][0]["source_unit_id"] == source_unit_id

    context = client.get(f"/sources/{source_unit_id}")
    assert context.status_code == 200
    assert context.json()["source_version_id"]
    assert context.json()["locator"]["kind"] == "markdown_block"
    assert context.json()["original_authority"] is True


def test_candidate_review_mutations_persist_and_approve_exact_quote(tmp_path: Path) -> None:
    """Create a candidate, approve it through verification, and expose history."""
    client = _client(tmp_path)
    scanned = client.post("/resources/scan", json={"path": "findings.md"}).json()
    source_unit_id = scanned["units"][1]["source_unit_id"]
    quote = "Weighted poverty fell by four points."

    candidate = client.post(
        "/evidence/candidates",
        json={
            "source_unit_id": source_unit_id,
            "statement": "Weighted poverty fell by four points.",
            "quote": quote,
            "relation": "supports",
        },
    )
    assert candidate.status_code == 200
    evidence_id = candidate.json()["evidence"]["evidence_id"]
    assert candidate.json()["evidence"]["review_state"] == "candidate"

    approved = client.post(
        f"/review/evidence/{evidence_id}",
        json={"action": "approve", "expected_revision": candidate.json()["revision"]},
    )
    assert approved.status_code == 200
    assert approved.json()["evidence"]["review_state"] == "approved"
    assert approved.json()["evidence"]["verification_status"] == "verified-high"

    history = client.get("/review/history")
    assert history.status_code == 200
    assert history.json()["events"][-1]["action"] == "approve"


def test_conflict_and_invalid_paths_fail_closed(tmp_path: Path) -> None:
    """Return deterministic revision conflicts and reject URL/path escapes."""
    client = _client(tmp_path)
    scanned = client.post("/resources/scan", json={"path": "findings.md"})
    revision = scanned.json()["revision"]

    conflict = client.post(
        "/resources/scan",
        json={"path": "findings.md", "expected_revision": revision - 1},
    )
    assert conflict.status_code == 409
    assert conflict.json()["error"] == "revision-conflict"

    traversal = client.post("/resources/scan", json={"path": "../outside.md"})
    assert traversal.status_code == 400
    remote = client.post("/resources/scan", json={"path": "https://example.org/paper.pdf"})
    assert remote.status_code == 400


def test_recovery_endpoint_is_explicit(tmp_path: Path) -> None:
    """Expose journal recovery as a local typed operation."""
    client = _client(tmp_path)
    recovered = client.post("/recovery")
    assert recovered.status_code == 200
    assert recovered.json()["recovered"] == []


def test_api_middleware_enforces_offline_socket_boundary(tmp_path: Path) -> None:
    """Exercise the production request boundary with a remote socket probe."""
    client = _client(tmp_path)

    @client.app.get("/security-probe")
    def security_probe() -> dict[str, bool]:
        """Attempt a remote connection inside the application middleware."""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
                probe.connect(("203.0.113.1", 9))
        except NetworkAccessDenied:
            return {"blocked": True}
        return {"blocked": False}

    assert client.get("/security-probe").json() == {"blocked": True}
