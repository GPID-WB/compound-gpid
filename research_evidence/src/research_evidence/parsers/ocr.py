"""Created 2026-08-12. Explicit local OCR capability and uncertainty contract."""
from __future__ import annotations

from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
from typing import Optional
from urllib.parse import urlsplit

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ..identity import make_source_unit_id, text_fingerprint
from ..inventory import ActivationStatus, EnterpriseReviewStatus
from ..schemas import LocatorKind, SourceUnit, TypedLocator, VerificationStatus
from ..security import validate_offline_environment, validate_subprocess_command


class OCRCapabilityError(RuntimeError):
    """Signal an unavailable, inactive, remote, or unsafe OCR capability.

    Args:
        message: Human-readable OCR capability failure.

    Returns:
        An exception suitable for explicit local capability handling.

    Example:
        ``raise OCRCapabilityError("OCR executable is unavailable")``.
    """


class OCRProfile(BaseModel):
    """Describe one inventory-controlled local OCR executable.

    Args:
        id: Stable OCR profile identifier.
        engine: OCR engine name.
        exact_version_or_revision: Exact installed or selected engine version.
        executable: Local executable name or path.
        distribution_source: Setup-time source for the engine.
        license_or_access_terms: License or access terms.
        restriction: Human-readable restriction, if any.
        setup_network_required: Whether explicit setup may need a network.
        runtime_network_required: Whether normal OCR needs a network.
        telemetry_notes: Declared or unverified telemetry behavior.
        platform_support: Supported operating-system labels.
        caveat_disclaimer: Visible OCR uncertainty disclaimer.
        enterprise_review_status: Organization review state.
        activation_status: Candidate, enabled, or blocked state.
        activation_acknowledged: Local acknowledgement for caveated use.
        service_url: Optional remote service endpoint, always forbidden in v1.

    Returns:
        A validated local OCR profile.

    Example:
        ``OCRProfile.model_validate({"id": "tesseract", ...})``.
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    engine: str = Field(min_length=1)
    exact_version_or_revision: str = Field(min_length=1)
    executable: str = Field(min_length=1)
    distribution_source: str = Field(min_length=1)
    license_or_access_terms: str = Field(min_length=1)
    restriction: str = ""
    setup_network_required: bool
    runtime_network_required: bool
    telemetry_notes: str = Field(min_length=1)
    platform_support: list[str] = Field(min_length=1)
    caveat_disclaimer: str = Field(min_length=1)
    enterprise_review_status: EnterpriseReviewStatus
    activation_status: ActivationStatus = ActivationStatus.CANDIDATE
    activation_acknowledged: bool = False
    service_url: Optional[str] = None

    @model_validator(mode="after")
    def validate_local_only(self) -> "OCRProfile":
        """Reject network-dependent or remote OCR configurations.

        Args:
            self: OCR profile being validated.

        Returns:
            The validated local-only profile.

        Raises:
            ValueError: If runtime network, remote service, or unsafe activation is set.

        Example:
            ``profile.validate_local_only()`` returns a safe profile.
        """
        if self.runtime_network_required:
            raise ValueError("OCR profile cannot require runtime network access")
        if self.service_url:
            parsed = urlsplit(self.service_url)
            if parsed.scheme or parsed.netloc:
                raise ValueError("remote OCR service configurations are forbidden")
        restricted = bool(self.restriction.strip()) or self.enterprise_review_status in {
            EnterpriseReviewStatus.RESTRICTED,
            EnterpriseReviewStatus.BLOCKED,
        }
        if self.activation_status == ActivationStatus.ENABLED_LOCAL and restricted:
            raise ValueError("Restricted OCR profiles cannot use enabled-local status")
        if self.activation_status == ActivationStatus.ENABLED_WITH_CAVEAT and not self.activation_acknowledged:
            raise ValueError("Enabled-with-caveat OCR profiles require acknowledgement")
        if self.enterprise_review_status == EnterpriseReviewStatus.BLOCKED:
            raise ValueError("Blocked OCR profiles cannot be activated")
        return self


class OCRResult(BaseModel):
    """Store one OCR output with explicit uncertainty and page provenance.

    Args:
        source_unit: Image-located OCR source unit.
        engine_id: Inventory profile that generated the text.
        generated_text_sha256: Hash of generated OCR text.
        confidence: Conservative OCR confidence score.
        verification_status: Review status, never high from OCR alone.
        original_authority_verified: Whether the original page was checked.

    Returns:
        A validated OCR result.

    Example:
        ``result.source_unit.locator.page`` identifies the original page.
    """

    model_config = ConfigDict(extra="forbid")

    source_unit: SourceUnit
    engine_id: str = Field(min_length=1)
    generated_text_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    confidence: float = Field(ge=0.0, le=1.0)
    verification_status: VerificationStatus
    original_authority_verified: bool = False


def _validate_image_path(image_path: Path) -> Path:
    """Validate one local non-link image path before subprocess execution."""
    raw = str(image_path)
    parsed = urlsplit(raw)
    if parsed.scheme or parsed.netloc or raw.startswith("//"):
        raise OCRCapabilityError("Remote OCR image paths are forbidden")
    path = Path(image_path)
    if path.is_symlink() or not path.is_file():
        raise OCRCapabilityError(f"OCR image is unavailable or unsafe: {path}")
    return path.resolve()


def run_ocr(
    profile: OCRProfile,
    image_path: Path,
    *,
    page: int,
    source_version_id: str,
) -> OCRResult:
    """Run one explicitly selected local OCR executable on a page image.

    Args:
        profile: Inventory-controlled OCR profile.
        image_path: Local page image; URLs and links are rejected.
        page: One-based original PDF page number.
        source_version_id: Immutable source-version identifier.

    Returns:
        Low-confidence, image-located OCR result requiring original-page review.

    Raises:
        OCRCapabilityError: If the profile is inactive, executable is unavailable,
            network/proxy policy fails, or the subprocess fails.

    Example:
        ``run_ocr(profile, Path("page-004.png"), page=4, source_version_id="v1")``.
    """
    if page <= 0:
        raise OCRCapabilityError("OCR page number must be positive")
    if profile.activation_status not in {
        ActivationStatus.ENABLED_LOCAL,
        ActivationStatus.ENABLED_WITH_CAVEAT,
    }:
        raise OCRCapabilityError(
            f"OCR profile {profile.id!r} is not active: {profile.activation_status.value}"
        )
    validate_offline_environment()
    image = _validate_image_path(image_path)
    executable = shutil.which(profile.executable)
    if executable is None:
        raise OCRCapabilityError(f"OCR executable is unavailable: {profile.executable}")
    command = [executable, str(image), "stdout"]
    try:
        validate_subprocess_command(command, {Path(executable).name})
        environment = {
            key: value
            for key, value in os.environ.items()
            if key.upper() not in {"HTTP_PROXY", "HTTPS_PROXY", "ALL_PROXY"}
        }
        completed = subprocess.run(
            command,
            capture_output=True,
            check=True,
            env=environment,
            shell=False,
            text=True,
            timeout=120,
        )
    except (OSError, subprocess.SubprocessError, ValueError) as error:
        raise OCRCapabilityError(f"Local OCR execution failed: {error}") from error
    text = completed.stdout.strip()
    fingerprint = text_fingerprint(text or "[empty OCR output]")
    locator = TypedLocator(
        kind=LocatorKind.PDF_IMAGE,
        page=page,
        unit_fingerprint=fingerprint,
    )
    source_unit = SourceUnit(
        source_unit_id=make_source_unit_id(source_version_id, locator, fingerprint),
        source_version_id=source_version_id,
        locator=locator,
        text=text or "[empty OCR output]",
        unit_type="image",
        review_required=True,
        parser_metadata={
            "parser": "ocr",
            "engine": profile.engine,
            "engine_version": profile.exact_version_or_revision,
            "confidence_source": "not-provided-by-runner",
        },
    )
    return OCRResult(
        source_unit=source_unit,
        engine_id=profile.id,
        generated_text_sha256=sha256(text.encode("utf-8")).hexdigest(),
        confidence=0.0,
        verification_status=VerificationStatus.FLAGGED_LOW,
        original_authority_verified=False,
    )
