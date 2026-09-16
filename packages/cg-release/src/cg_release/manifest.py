"""Strict validation of existing preview or prior release manifests."""

from typing import Annotated

from pydantic import Field

from cg_release.events import ControllerError
from cg_release.models import Commit, Digest, Name, VersionedRecord, load_record
from cg_release.policy import safe_path, safe_ref
from cg_release.versions import parse_version


class Manifest(VersionedRecord):
    """Supported manifest fields only; request identity is data, not admission proof."""

    version: Name
    tag: Name
    request_id: Annotated[str, Field(min_length=1, max_length=4096)]
    source_sha: Commit
    policy_digest: Digest
    line: Name
    projections: dict[str, str]
    outputs: list[str]


def validate_manifest(raw: bytes) -> Manifest:
    """Validate existing or generated manifest bytes, e.g. validate_manifest(blob).

    Args:
        raw: Supported bounded UTF-8 manifest bytes; absence is handled by caller.
    Returns:
        Strict schema-v1 data, without inferring any Phase 3 request authority.
    Raises:
        ControllerError: Unknown/duplicate fields, invalid shapes or unsafe values.
    """
    from cg_release.metadata import project_version

    try:
        manifest = load_record(Manifest, raw)
        parse_version(manifest.version)
        safe_ref(manifest.tag)
        if not manifest.tag.endswith(manifest.version):
            raise ValueError
        if len({path.casefold() for path in manifest.outputs}) != len(manifest.outputs):
            raise ValueError
        if len({path.casefold() for path in manifest.projections}) != len(
            manifest.projections
        ):
            raise ValueError
        for path in [*manifest.outputs, *manifest.projections]:
            safe_path(path)
        for projection in manifest.projections.values():
            if projection != manifest.version and projection != project_version(
                manifest.version, []
            ):
                raise ValueError
        return manifest
    except (ValueError, ControllerError):
        raise ControllerError(
            "E_MANIFEST", "Release manifest is invalid or unsupported."
        ) from None
