"""Created 2026-08-12. Tests for explicit local OCR capability behavior."""
from __future__ import annotations

from pathlib import Path

import pytest

from research_evidence.parsers.ocr import (
    OCRCapabilityError,
    OCRProfile,
    OCRResult,
    run_ocr,
)


def _profile(**overrides: object) -> OCRProfile:
    """Build a complete local OCR profile for tests."""
    values: dict[str, object] = {
        "id": "tesseract-local",
        "engine": "tesseract",
        "exact_version_or_revision": "5.3.4",
        "executable": "tesseract",
        "distribution_source": "https://github.com/tesseract-ocr/tesseract",
        "license_or_access_terms": "Apache-2.0",
        "restriction": "",
        "setup_network_required": True,
        "runtime_network_required": False,
        "telemetry_notes": "No telemetry known.",
        "platform_support": ["macos", "windows", "linux"],
        "caveat_disclaimer": "OCR text requires original-page verification.",
        "enterprise_review_status": "unreviewed",
        "activation_status": "enabled-local",
        "activation_acknowledged": False,
    }
    values.update(overrides)
    return OCRProfile.model_validate(values)


def test_runtime_network_or_remote_service_is_rejected() -> None:
    """Reject OCR profiles that require runtime network or a remote endpoint."""
    with pytest.raises(ValueError, match="runtime network"):
        _profile(runtime_network_required=True)
    with pytest.raises(ValueError, match="remote"):
        _profile(service_url="https://ocr.example.org")


def test_missing_ocr_engine_fails_loudly(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail explicitly when the selected local OCR executable is unavailable."""
    image = tmp_path / "page.png"
    image.write_bytes(b"image")
    monkeypatch.setattr("research_evidence.parsers.ocr.shutil.which", lambda _: None)

    with pytest.raises(OCRCapabilityError, match="unavailable"):
        run_ocr(_profile(), image, page=4, source_version_id="source-version:scan")


def test_ocr_result_is_page_located_low_confidence_and_unapproved(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Record OCR text as review-required evidence that cannot receive high confidence."""
    image = tmp_path / "page.png"
    image.write_bytes(b"image")
    monkeypatch.setattr("research_evidence.parsers.ocr.shutil.which", lambda _: "/usr/bin/tesseract")

    class Completed:
        """Minimal subprocess result fixture."""

        stdout = "OCR text"
        stderr = ""
        returncode = 0

    calls: list[dict[str, object]] = []

    def fake_run(*args: object, **kwargs: object) -> Completed:
        """Capture subprocess arguments without executing a child process."""
        calls.append({"args": args, "kwargs": kwargs})
        return Completed()

    monkeypatch.setattr("research_evidence.parsers.ocr.subprocess.run", fake_run)
    result = run_ocr(_profile(), image, page=4, source_version_id="source-version:scan")

    assert isinstance(result, OCRResult)
    assert result.source_unit.locator.kind.value == "pdf_image"
    assert result.source_unit.locator.page == 4
    assert result.source_unit.review_required is True
    assert result.confidence < 1.0
    assert result.original_authority_verified is False
    assert calls[0]["kwargs"]["shell"] is False


def test_unapproved_profile_cannot_run(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Keep candidate and blocked OCR profiles inactive."""
    image = tmp_path / "page.png"
    image.write_bytes(b"image")
    monkeypatch.setattr("research_evidence.parsers.ocr.shutil.which", lambda _: "/usr/bin/tesseract")
    profile = _profile(activation_status="candidate")

    with pytest.raises(OCRCapabilityError, match="not active"):
        run_ocr(profile, image, page=1, source_version_id="source-version:scan")
